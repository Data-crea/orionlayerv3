"""
TCP client for the orion2re Extension API.

Connects to the game process, receives state snapshots,
field lists and framebuffer data, sends input commands.
"""
import socket
import struct
import time
import logging
from core.game_state import (
    GameState, parse_state, parse_fields, parse_visual,
)
from core.wire_protocol import (
    MAGIC, PROTO_VERSION,
    MSG_HELLO, MSG_HELLO_REPLY, MSG_STATE, MSG_FIELDS,
    MSG_VISUAL, MSG_EVENT,
    MSG_ACTIVATE, MSG_INJECT_KEY, MSG_INJECT_CLICK, MSG_CANCEL_FIELD,
    MSG_SET_JOBS, MSG_SELECT_SHIP, MSG_SAVE_SLOTS, MSG_SHOW_WINDOW,
    MSG_INJECT_RIGHT_CLICK, MSG_COMBAT_COMMAND, MSG_SET_SPIES,
    SUB_STATE, SUB_FIELDS, SUB_VISUAL, SUB_EVENTS,
    parse_save_slots,
)

log = logging.getLogger("game_client")

# Wire protocol constants (must match ext_server.h) now live in
# core/wire_protocol.py — single source, also used by the
# standalone tools/ext_diag*.py.

# Connection health
RECV_BUF_SIZE = 4 * 1024 * 1024   # 4 MB OS receive buffer

# Seconds without data before the connection is treated as dead.
#
# SILENCE IS NOT DEATH. `ext::Tick()` runs from `fields::Get_Input_()`,
# so the server only talks while the game is inside an input loop.
# Galaxy generation, turn processing and savegame loading all run
# with no input loop at all and can be silent for many seconds — in a
# debug build, tens of them. A watchdog that fires there does real
# damage: it drops a healthy connection and the fresh one misses
# every FIELD_LIST published while it was gone, because `ext_api.cpp`
# resends the list only on a field-count change or a screen change.
#
# Anything that knows the game is about to go quiet calls
# `hold_watchdog()` and the timeout is suspended for that long.
STALE_TIMEOUT = 10.0


#: How long a tool waits for the first STATE_SNAPSHOT before giving
#: up. The server only talks inside an input loop — `ext::Tick()` runs
#: from `fields::Get_Input_()` — so a game generating a galaxy or
#: processing a turn is silent for as long as that takes, and silence
#: is not death. Ten seconds is long enough for a game sitting on a
#: screen and short enough that a tool run against nothing says so
#: rather than hanging.
SNAPSHOT_TIMEOUT = 10.0


def fetch_snapshot(host="localhost", port=17362,
                   timeout=SNAPSHOT_TIMEOUT):
    """Connect, wait for one STATE_SNAPSHOT, disconnect, return it.

    (state, error) — exactly one of them is None. The error is a
    sentence a tool can print, because the two failures are different
    things a user has to fix differently: nothing listening on the
    port, and a connection that never produced a snapshot.

    **One home for this, not two.** `dev:tools/struct_probe.py` had this loop
    and `dev:tools/colony_list_preview.py` needed the same one; a second copy
    of a wait whose contract is "poll until `current_screen` is set,
    and treat silence as busy rather than dead" is the kind that
    drifts by a condition and is then wrong in only one of the tools.
    The rule is that the third copy is the signal to extract — this
    is the second, and it is extracted anyway because the thing being
    copied is a protocol contract rather than four lines of shape.

    The caller gets a DISCONNECTED state object: everything the
    snapshot carried is in it, and nothing will arrive afterwards.
    That suits a tool that wants one reading. Anything that has to
    keep watching wants a `GameClient` of its own.
    """
    client = GameClient()
    if not client.connect(host=host, port=port):
        return None, (f"Cannot reach orion2re at {host}:{port} — is the "
                      f"game running with -DORION2RE_EXT=ON?")
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        client.poll()
        state = client.state
        if state and state.current_screen >= 0:
            client.disconnect()
            return state, None
        time.sleep(0.05)
    client.disconnect()
    return None, (f"No STATE_SNAPSHOT within {timeout:.0f} s — is a game "
                  f"loaded? The server only talks inside an input loop, "
                  f"so a game busy generating or processing is silent.")


def count_connections(port=17362):
    """How many established TCP connections exist on `port`.

    OrionLayer holds exactly one. Anything above two entries (our
    end plus the server's end of the same connection) means orion2re
    is still holding clients from earlier sessions — and a server
    that serializes a full snapshot for every dead connection on
    every tick is a candidate for the load gaps that only a restart
    clears.

    Reads /proc/net/tcp directly rather than shelling out to `ss`,
    so it costs nothing and works with no tools installed. Returns
    None where /proc is not available.
    """
    hexport = f"{port:04X}"
    total = 0
    found = False
    for path in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            with open(path) as f:
                lines = f.readlines()[1:]
        except OSError:
            continue
        found = True
        for line in lines:
            parts = line.split()
            if len(parts) < 4 or parts[3] != "01":   # ESTABLISHED
                continue
            local = parts[1].rsplit(":", 1)[-1]
            remote = parts[2].rsplit(":", 1)[-1]
            if hexport in (local, remote):
                total += 1
    return total if found else None


class GameClient:
    """Connects to the orion2re Extension API."""

    def __init__(self):
        self.host = 'localhost'
        self.port = 17362
        self.sock = None
        self.connected = False
        self.state = GameState()
        self._recv_buf = bytearray()
        self._last_recv_time = 0.0
        self._hold_until = 0.0
        self._subs = 0
        # Traffic counters. The only way to tell "the game is busy"
        # apart from "we are not asking it to do anything" is to look
        # at what arrived while we waited; both look like a frozen
        # screen. Monotonic, never reset — callers take deltas.
        self.stats = {"state": 0, "fields": 0, "visual": 0,
                      "bytes": 0}
        # A REQUESTED END IS NOT A LOST CONNECTION (decision 62).
        # `expect_shutdown` is called before the GAME menu's QUIT is
        # confirmed; after it, the socket closing ends the client
        # instead of starting a reconnect.
        self.shutdown_expected = False
        self.game_ended = False

    def connect(self, host='localhost', port=17362,
                subscribe_state=True, subscribe_fields=True,
                subscribe_visual=True, subscribe_events=True):
        """Open connection and send subscription request."""
        self.host = host
        self.port = port
        self._subs = 0
        if subscribe_state:  self._subs |= SUB_STATE
        if subscribe_fields: self._subs |= SUB_FIELDS
        if subscribe_visual: self._subs |= SUB_VISUAL
        if subscribe_events: self._subs |= SUB_EVENTS

        return self._open()

    def _open(self):
        """Open socket, set buffer size, send HELLO."""
        self.disconnect()
        try:
            self.sock = socket.socket(socket.AF_INET,
                                      socket.SOCK_STREAM)
            self.sock.settimeout(5.0)
            self.sock.connect((self.host, self.port))
            self.sock.setsockopt(socket.SOL_SOCKET,
                                socket.SO_RCVBUF, RECV_BUF_SIZE)
            self.sock.setblocking(False)
            self.connected = True
            self._recv_buf.clear()
            self._last_recv_time = time.monotonic()

            payload = struct.pack('<HH', PROTO_VERSION, self._subs)
            self._send_message(MSG_HELLO, payload)
            log.info(f"Connected to orion2re at "
                     f"{self.host}:{self.port}")
            return True

        except (ConnectionRefusedError, TimeoutError, OSError) as e:
            log.warning(f"Cannot connect to orion2re: {e}")
            self.connected = False
            return False

    def disconnect(self):
        """Close connection."""
        if self.sock:
            try:
                self.sock.close()
            except OSError:
                pass
        self.sock = None
        self.connected = False

    def poll(self):
        """Read all available messages. Non-blocking.

        Returns True if at least one message was processed.
        Auto-reconnects if no data received for STALE_TIMEOUT.
        """
        if not self.connected:
            return False

        got_message = False
        # THE BATTLE'S EVENTS OF EVERY SNAPSHOT THIS POLL READS (work order
        # 197 C): a screen sees only the state the poll leaves, and the
        # engine sends several between two frames while the battle runs —
        # CMEV carries each snapshot's events once, so they are gathered
        # here onto the last state (`_carry_combat_events`), numbered as
        # sent; a screen skips what it has seen by number.
        self._cmev_batch = []

        try:
            # Read all available data
            while True:
                try:
                    chunk = self.sock.recv(65536)
                    if not chunk:
                        self._lost("orion2re disconnected")
                        return False
                    self._recv_buf.extend(chunk)
                    self._last_recv_time = time.monotonic()
                except BlockingIOError:
                    break

            # Check for stale connection, unless somebody has told us
            # the game is legitimately busy (see STALE_TIMEOUT).
            now = time.monotonic()
            silent = now - self._last_recv_time
            if silent > STALE_TIMEOUT and now >= self._hold_until:
                self._lost(f"No data for {silent:.1f}s — reconnecting")
                return False

            # Parse messages from buffer. Collected first: A STATE SNAPSHOT
            # ANOTHER ONE FOLLOWS IN THIS POLL IS NOT PARSED (work order
            # 226 C) — screens see only the last (`_carry_combat_events`),
            # and on a screen whose loop has no wait the engine sends a
            # dozen a frame, each a full parse (Planets: half the frame).
            # One carrying the battle's events (CMEV) is parsed still, so
            # they are gathered as before; fields, pictures and slots go
            # onto the state in their order and are carried, as before.
            batch = []
            while len(self._recv_buf) >= 16:
                magic, length = struct.unpack_from(
                    '<II', self._recv_buf, 0
                )
                if magic != MAGIC:
                    log.error(f"Bad magic: 0x{magic:08X}")
                    self._recv_buf.clear()
                    self._reconnect()
                    return False

                total = 8 + length
                if len(self._recv_buf) < total:
                    break

                msg_type, flags, seq = struct.unpack_from(
                    '<HHI', self._recv_buf, 8
                )
                payload = bytes(self._recv_buf[16:total])
                del self._recv_buf[:total]
                batch.append((msg_type, flags, payload))

            last_state = max((i for i, m in enumerate(batch)
                              if m[0] == MSG_STATE), default=-1)
            for i, (msg_type, flags, payload) in enumerate(batch):
                if msg_type == MSG_STATE and i < last_state and \
                        b"CMEV" not in payload:
                    self.stats["state"] += 1
                    self.stats["bytes"] += len(payload) + 16
                    self.stats["state_skipped"] = \
                        self.stats.get("state_skipped", 0) + 1
                else:
                    self._handle_message(msg_type, flags, payload)
                got_message = True

        except (ConnectionResetError, BrokenPipeError, OSError) as e:
            self._lost(f"Connection lost: {e}")
            return False

        return got_message

    def hold_watchdog(self, seconds):
        """Suspend the stale-connection timeout for `seconds`.

        For callers that know the game is about to stop talking —
        an injection chain waiting for a dialog that only appears
        after galaxy generation, for instance. Repeated calls extend;
        they never shorten an existing hold.
        """
        self._hold_until = max(self._hold_until,
                               time.monotonic() + seconds)

    def expect_shutdown(self):
        """The next silence or close is the game ending on request.

        Called by the GAME menu BEFORE it confirms QUIT
        (`Do_Main_Game_Popup_`, loadsave.cpp:1257-1273: YES saves
        SAVE10.GAM and returns SCREEN_EXIT). From here on no reconnect
        is attempted: the watchdog is disarmed, and a closed socket
        sets `game_ended` for the app to leave on.
        """
        self.shutdown_expected = True
        self._hold_until = float("inf")
        log.info("shutdown expected: the watchdog is disarmed")

    def _lost(self, reason):
        """The connection is gone or silent: end, or reconnect."""
        if self.shutdown_expected:
            log.info("orion2re went away after QUIT was confirmed "
                     "(%s); not reconnecting", reason)
            self.disconnect()
            self.game_ended = True
            return
        log.warning(reason)
        self._reconnect()

    def _reconnect(self):
        """Close and reopen the connection.

        The field list is dropped. It describes whatever dialog was
        open on the old connection, and the game may have moved on
        several times while we were not listening — acting on it
        after a reconnect means clicking a field that no longer
        exists. An empty list means "unknown", which callers can
        handle; a stale one is a lie they cannot detect.
        """
        log.info("Reconnecting...")
        self.state.fields = []
        self._open()

    def activate_field(self, field_id):
        """Activate a field (simulates mouse click on a button).

        OPEN FIX 62 (work order 197 A4): the field's rectangle as THIS
        client's list shows it goes along, and the engine drops the
        activation if, when its next `Get_Input_` would take it, that index
        names another field — a list that ended by itself in between (the
        reports phase's whole-screen field) had handed its index to SELECT
        NEW RESEARCH, which committed row 1 after its input delay (open fix
        26). An engine without the fix reads the first two bytes and nothing
        else (`ext_server.cpp`, `payload_len >= 2`), exactly as before; an
        index this list does not carry goes alone, unchecked, as before."""
        f = next((f for f in (getattr(self.state, "fields", None) or [])
                  if getattr(f, "index", None) == field_id), None)
        payload = struct.pack('<h', field_id)
        if f is not None:
            payload += struct.pack('<4h', f.x, f.y, f.x_end, f.y_end)
        self._send_message(MSG_ACTIVATE, payload)

    def inject_key(self, keysym):
        """Send a keypress to the game.

        Ignores keysyms outside int16 range (pygame special keys
        like F-keys use large values that have no SDL equivalent).
        """
        if -32768 <= keysym <= 32767:
            self._send_message(MSG_INJECT_KEY,
                               struct.pack('<h', keysym))

    def inject_click(self, x, y):
        """Send a mouse click at (x,y) in 640x480 space."""
        self._send_message(MSG_INJECT_CLICK,
                           struct.pack('<hh', x, y))

    def inject_right_click(self, x, y):
        """A RIGHT click at (x, y) in 640x480 space — open fix 61
        (`MSG_INJECT_RIGHT_CLICK`); an engine without it drops it."""
        self._send_message(MSG_INJECT_RIGHT_CLICK,
                           struct.pack('<hh', x, y))

    def combat_command(self, serial, unit, op, a=0, b=0, c=0):
        """One battle action — open fix 58 (`MSG_COMBAT_COMMAND`). `serial`
        and `unit` are the CMBT block's battle and acting unit: the engine
        drops a command meant for another. What happened comes back as CMEV
        events, never from here."""
        self._send_message(MSG_COMBAT_COMMAND,
                           struct.pack('<HhBhhh', serial, unit, op, a, b, c))

    def set_spies(self, races, agents):
        """The Races screen's spies and missions — open fix 64
        (`MSG_SET_SPIES`). `races` is [(player, spies, mission), …] for
        EVERY race the screen shows, mission 1-3 or 0 to keep it; `agents`
        the pool. The engine takes the whole list or nothing (the total
        kept, no group above 63); the player record on the wire says which."""
        payload = struct.pack('<B', len(races)) + b"".join(
            struct.pack('<BBB', p, s, m) for p, s, m in races) + \
            struct.pack('<B', agents)
        self._send_message(MSG_SET_SPIES, payload)

    def set_jobs(self, colony_index, pairs):
        """Set the job of one or more pops in ONE colony.

        `pairs` is [(pop_index, job), …]. The engine applies the
        whole list or none of it (fundament 52), so a caller gets
        one outcome and never a half-applied move. Nothing is
        returned here: the result is read off the next snapshot, by
        diffing the pop words `colonymove.predict_pops` predicted —
        which is the same check the click chain used and the reason
        that tooling still applies.
        """
        payload = struct.pack('<hB', colony_index, len(pairs))
        for pop_index, job in pairs:
            payload += struct.pack('<BB', pop_index, job)
        self._send_message(MSG_SET_JOBS, payload)

    def select_ship(self, ship_index, selected):
        """Select or deselect ONE ship in the open fleet box.

        `MSG_SELECT_SHIP`, open fix 21 (`doc/ext_fleet_select_ship.patch`,
        reported, not applied). The engine applies it only when the box is
        open, the ship is the player's, in that box's stack and may be
        ordered; otherwise it writes nothing. Nothing is returned here:
        what happened is the FSEL block of a later snapshot (open fix 20).
        """
        payload = struct.pack('<hB', ship_index, 1 if selected else 0)
        self._send_message(MSG_SELECT_SHIP, payload)

    def show_window(self, show):
        """Show or hide the ENGINE'S OWN window — `MSG_SHOW_WINDOW`, open
        fix 43 (`doc/ext_engine_window_on_request.patch`, applied by work
        order 186): one byte, 1 show, 0 hide, applied by the engine's main
        thread. F12 sends it (`main.App._cycle_render_mode`). An engine
        without the fix drops it; nothing comes back, and nothing waits."""
        self._send_message(MSG_SHOW_WINDOW, struct.pack('<B', 1 if show else 0))

    def cancel_field(self, field_id):
        """Right-click on a field."""
        self._send_message(MSG_CANCEL_FIELD,
                           struct.pack('<h', field_id))

    def _send_message(self, msg_type, payload=b''):
        """Send a framed message."""
        if not self.connected or not self.sock:
            return
        msg_header = struct.pack('<HHI', msg_type, 0, 0)
        frame_header = struct.pack('<II', MAGIC,
                                   len(msg_header) + len(payload))
        try:
            self.sock.sendall(frame_header + msg_header + payload)
        except (BrokenPipeError, OSError) as e:
            log.warning(f"Send failed: {e}")
            self._reconnect()

    def _carry_combat_events(self):
        """This poll's CMEV events so far onto the state just parsed."""
        batch = getattr(self, "_cmev_batch", None)
        if batch is None:
            batch = self._cmev_batch = []
        ev = getattr(self.state, "combat_events", None)
        if ev:
            batch.extend(ev["events"])
        if batch:
            self.state.combat_events = {"first": batch[0]["seq"],
                                        "events": list(batch)}

    def _handle_message(self, msg_type, flags, payload):
        """Process a received message."""
        self.stats["bytes"] += len(payload) + 16
        if msg_type == MSG_HELLO_REPLY:
            log.info("HELLO_REPLY received")

        elif msg_type == MSG_STATE:
            self.stats["state"] += 1
            try:
                old_fb = self.state.framebuffer
                old_pal = self.state.palette
                old_fields = self.state.fields
                old_slots = self.state.save_slots
                self.state = parse_state(payload)
                self.state.framebuffer = old_fb
                self.state.palette = old_pal
                self.state.fields = old_fields
                self.state.save_slots = old_slots
                self._carry_combat_events()
            except Exception as e:
                log.error(f"State parse error: {e}")

        elif msg_type == MSG_FIELDS:
            self.stats["fields"] += 1
            try:
                self.state.fields = parse_fields(payload)
                # The engine sends MSG_SAVE_SLOTS right AFTER the list
                # it belongs to, so a list with none has no slots.
                self.state.save_slots = None
            except Exception as e:
                log.error(f"Fields parse error: {e}")

        elif msg_type == MSG_VISUAL:
            self.stats["visual"] += 1
            try:
                fb, pal = parse_visual(payload)
                self.state.framebuffer = fb
                self.state.palette = pal
            except Exception as e:
                log.error(f"Visual parse error: {e}")

        elif msg_type == MSG_SAVE_SLOTS:
            try:
                self.state.save_slots = parse_save_slots(payload)
            except Exception as e:
                log.error(f"Save slot parse error: {e}")

        elif msg_type == MSG_EVENT:
            if len(payload) >= 4:
                evt_flags, screen = struct.unpack_from(
                    '<Hh', payload, 0
                )
                log.debug(f"Event: flags=0x{evt_flags:04X} "
                          f"screen={screen}")
