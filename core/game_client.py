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
    MSG_INJECT_RAW_KEY, MSG_SETTLE_POPS, MSG_LAYOUT, CAP_LAYOUT,
    MSG_DEMOLISH, CAP_DEMOLISH,
    SUB_STATE, SUB_FIELDS, SUB_VISUAL, SUB_EVENTS,
    parse_save_slots,
)
from core import colony_guard
from core.structs import layout as engine_layout

log = logging.getLogger("game_client")

# Wire protocol constants (must match ext_server.h) now live in
# core/wire_protocol.py — single source, also used by the
# standalone tools/ext_diag*.py.

# Connection health
RECV_BUF_SIZE = 4 * 1024 * 1024   # 4 MB OS receive buffer
#: A frame's length counts the 8 bytes after the first 8 (message type,
#: flags, sequence number): at least that header, and never more than the
#: largest the engine builds — the 640x480 framebuffer and its palette are
#: under 400 KB, a snapshot under a few MB. 64 MB leaves room for every
#: block yet stops a corrupt length from being waited for.
MIN_FRAME = 8
MAX_FRAME = 64 * 1024 * 1024

# Seconds without data after which the client says so in the log — and
# nothing else (work order 322 C).
#
# SILENCE IS NOT DEATH. `ext::Tick()` runs from `fields::Get_Input_()`,
# so the server only talks while the game is inside an input loop.
# Galaxy generation, turn processing and savegame loading all run
# with no input loop at all and can be silent for many seconds — in a
# debug build, tens of them. Until work order 322 a watchdog reconnected
# here, and that did real damage (P811): it dropped a healthy connection, and
# the fresh one waited, without even a HELLO_REPLY, until the busy game came
# back to its input loop (F909). The field list itself is no longer lost by
# a reconnect: HELLO marks it dirty, so a new connection gets the current
# list at once (ext_server.cpp:198-200), and since open fix 84 the list is
# also resent whenever its content changes. And the reconnect could cure
# nothing: every way the server drops a
# client closes its socket (`Server::RemoveDeadClients`, ext_server.cpp:
# 460-471; `Server::Stop`, :75-82), and an engine that dies has its
# sockets closed by the kernel — so a lost engine always arrives as a
# close or a reset, which `poll` reads, and silence on an open socket is
# an engine that is busy (or hung, which no reconnect helps). A peer that
# vanishes without a close (a remote `orion2re.host` whose machine went
# away) is found by TCP keepalive (`KEEPALIVE`), which the far side's
# kernel answers however busy the game is.
#
# Anything that knows the game is about to go quiet may still call
# `hold_watchdog()`: the silence is then not even logged.
STALE_TIMEOUT = 10.0
#: TCP keepalive: idle seconds, interval, probes (Linux names; skipped
#: where the platform lacks them). Answered by the peer's kernel, not the
#: game, so a busy game is never taken for a dead one.
KEEPALIVE = (10, 5, 3)
#: The connect's timeout at the start; a retry after a loss uses
#: `RETRY_TIMEOUT` — a refused connect on this machine returns at once, and
#: a retry must not hold the window (`core/enginelink.py` paces them).
CONNECT_TIMEOUT = 5.0
RETRY_TIMEOUT = 0.5
#: How long a send waits for the engine to take what it already holds.
SEND_TIMEOUT = 2.0


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


def _keepalive(sock):
    """TCP keepalive on `sock` with `KEEPALIVE`'s timing, where the
    platform has the options (see STALE_TIMEOUT for why)."""
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        for name, value in zip(("TCP_KEEPIDLE", "TCP_KEEPINTVL",
                                "TCP_KEEPCNT"), KEEPALIVE):
            opt = getattr(socket, name, None)
            if opt is not None:
                sock.setsockopt(socket.IPPROTO_TCP, opt, value)
    except OSError as e:
        log.info("TCP keepalive not set: %s", e)


#: The kinds the engine sends again unchanged (work order 273): a repeat of
#: one of these is not a change (`GameClient.changes`).
REPEATED = (MSG_STATE, MSG_VISUAL, MSG_FIELDS, MSG_SAVE_SLOTS)


class GameClient:
    """Connects to the orion2re Extension API."""

    #: Also on the class: a stand-in made without `__init__` counts too.
    changes = 0
    _last_state = None
    _last_of = None

    def __init__(self):
        self.host = 'localhost'
        self.port = 17362
        self.sock = None
        self.connected = False
        #: HELLO_REPLY's capability bits of the engine connected now; 0
        #: before the reply and for an engine that sends none.
        self.capabilities = 0
        self.state = GameState()
        self._recv_buf = bytearray()
        self._last_recv_time = 0.0
        self._hold_until = 0.0
        self._subs = 0
        # Traffic counters. The only way to tell "the game is busy"
        # apart from "we are not asking it to do anything" is to look
        # at what arrived while we waited; both look like a frozen
        # screen. Monotonic, never reset — callers take deltas.
        # `state_ok` counts the snapshots that PARSED; `state` counts every
        # one that arrived. The connection is only "reached again" on a
        # parsed one (audit TD-05): a layout this client cannot read used
        # to count as the new connection's first snapshot.
        self.stats = {"state": 0, "state_ok": 0, "fields": 0, "visual": 0,
                      "bytes": 0}
        # A REQUESTED END IS NOT A LOST CONNECTION (decision 62).
        # `expect_shutdown` is called before the GAME menu's QUIT is
        # confirmed; after it, the socket closing ends the client
        # instead of starting a reconnect.
        self.shutdown_expected = False
        self.game_ended = False
        # A LOST ENGINE (work order 322 C, HD EXTENSION `engine_lost`): the
        # reason the last connection ended, while no new one has opened —
        # None when connected, and when none was ever made (the standalone
        # start, which is not a loss). `core/enginelink.py` reads it, paces
        # `retry` and tells the player.
        self.lost = None
        #: How many losses `_lost` has already reconnected at once. The
        #: link counts them: a reconnect that works leaves `connected`
        #: True and `lost` None, so without the count nothing outside
        #: would ever learn that the snapshot it holds is the old one's.
        self.reconnected = 0
        self._silence_logged = False
        # WHAT CAME THAT CAN CHANGE A PICTURE (work order 273,
        # `core/drawgate.py`): the engine sends the whole snapshot — and the
        # framebuffer — on every tick, changed or not, so a message of a
        # kind that repeats counts only when its bytes differ from the
        # previous one of its kind; an event always counts.
        self.changes = 0
        self._last_state = None
        self._last_of = {}

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

    def _open(self, timeout=CONNECT_TIMEOUT):
        """Open socket, set buffer size, send HELLO."""
        self.disconnect()
        try:
            self.sock = socket.socket(socket.AF_INET,
                                      socket.SOCK_STREAM)
            self.sock.settimeout(timeout)
            # BEFORE connect: the TCP window scale is fixed by the SYN, so
            # a buffer asked for afterwards cannot widen the window the
            # engine sees — and the engine drops a client whose buffer
            # stays full for a second (ext_server.cpp, kMaxWaitMs)
            self.sock.setsockopt(socket.SOL_SOCKET,
                                socket.SO_RCVBUF, RECV_BUF_SIZE)
            self.sock.connect((self.host, self.port))
            _keepalive(self.sock)
            # HELLO is sent here, not through `_send_message`, whose failure
            # is a loss and would reconnect from inside the connect; and
            # BEFORE the client counts as connected, so a failed HELLO
            # leaves `lost` as it was and the loss is retried (WO 322 C)
            payload = struct.pack('<HH', PROTO_VERSION, self._subs)
            self.sock.sendall(self._frame(MSG_HELLO, payload))
            self.sock.setblocking(False)
            self.connected = True
            self.lost = None
            self._recv_buf.clear()
            self._last_recv_time = time.monotonic()
            self._silence_logged = False
            log.info(f"Connected to orion2re at "
                     f"{self.host}:{self.port}")
            return True

        except (ConnectionRefusedError, TimeoutError, OSError) as e:
            # a retry's refusal is the loss going on, said once by
            # `core/enginelink.py` — not one warning every retry
            (log.debug if self.lost else log.warning)(
                f"Cannot connect to orion2re: {e}")
            if self.sock:
                try:
                    self.sock.close()
                except OSError:
                    pass
            self.sock = None
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
        # the next engine says its own (open fix 111's CAP_DEMOLISH)
        self.capabilities = 0
        self.changes += 1
        self._last_state = None
        self._last_of = {}

    def poll(self):
        """Read all available messages. Non-blocking.

        Returns True if at least one message was processed. A close or
        a reset is a loss (`_lost`); silence is not (see STALE_TIMEOUT).
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
                    self._silence_logged = False
                except BlockingIOError:
                    break

            # A long silence is said once and acted on never: the socket
            # is open, so the game is busy (see STALE_TIMEOUT, P811).
            now = time.monotonic()
            silent = now - self._last_recv_time
            if silent > STALE_TIMEOUT and now >= self._hold_until and \
                    not self._silence_logged:
                self._silence_logged = True
                log.info("no data for %.1fs on an open socket: the game is "
                         "busy, not gone — waiting, not reconnecting", silent)

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
                    self._lost("a frame with a bad magic: the stream is "
                               "out of step")
                    return False

                # a header out of step must not make the client buffer the
                # stream (framebuffer and state, ~20 MB/s) while it waits
                # for a frame that never completes, nor read the next
                # frame's header as this one's body
                if not MIN_FRAME <= length <= MAX_FRAME:
                    log.error(f"Bad frame length: {length}")
                    self._recv_buf.clear()
                    self._lost("a frame of impossible length: the stream "
                               "is out of step")
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

    def _parse_failed(self, kind, exc):
        """One line for the first message of a kind that does not parse,
        then one in a hundred: the engine sends a snapshot every tick, and
        a layout the client cannot read made the log a line per snapshot —
        many a second — that buried the one that mattered."""
        key = kind + "_errors"
        self.stats[key] = self.stats.get(key, 0) + 1
        if self.stats[key] == 1 or self.stats[key] % 100 == 0:
            log.error("%s parse error: %s (%d so far)", kind, exc,
                      self.stats[key])

    def _lost(self, reason):
        """The connection closed or broke: end, or reconnect once now.

        A refused reconnect leaves `lost` set; `core/enginelink.py` then
        calls `retry` at its own pace and tells the player (work order 322
        C). Silence never comes here (see STALE_TIMEOUT)."""
        if self.shutdown_expected:
            log.info("orion2re went away after QUIT was confirmed "
                     "(%s); not reconnecting", reason)
            self.disconnect()
            self.game_ended = True
            return
        log.warning(reason)
        self.lost = reason
        self._reconnect(timeout=RETRY_TIMEOUT)
        if self.connected:
            self.reconnected += 1

    def retry(self):
        """One more connect after a loss — `_reconnect` with a short
        timeout. True once a connection is open again."""
        if self.lost is None or self.shutdown_expected:
            return self.connected
        self._reconnect(timeout=RETRY_TIMEOUT)
        return self.connected

    def _reconnect(self, timeout=None):
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
        if timeout is None:
            self._open()
        else:
            self._open(timeout)

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
        # The colony screens' safety rule at the one chokepoint, so a screen
        # or mod that sends through the base class cannot bypass the senders'
        # own check (audit TD-13).
        if f is not None:
            why = colony_guard.refusal(
                f, getattr(self.state, "current_screen", -1))
            if why is not None:
                log.warning("activate_field %s refused: %s — nothing sent",
                            field_id, why)
                return
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

    def inject_raw_key(self, code):
        """Send a key the engine's platform layer translates (open fix 89,
        `core/keyfwd.py`): an F key, Alt+F key or Alt+letter code; the
        engine drops anything else."""
        if 0 <= code <= 0xFFFF:
            self._send_message(MSG_INJECT_RAW_KEY, struct.pack('<H', code))

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

    def settle_pops(self, source_index, dest_index, pops, answers=None,
                    job=-1):
        """Settle pops of one colony in another colony of the player
        (`MSG_SETTLE_POPS`). The short form (open fix 92,
        `doc/ext_settle_pops.patch`): the colony screen's colony to a colony
        at its star, the whole list or none of it. With `answers` the long
        form (open fix 103, `doc/ext_settle_anywhere.patch`): any colony,
        from the colony screen or the Colonies list, colonist by colonist up
        to the first that may not go — `answers` the YES bits of the
        original's two questions (`core.settlewire.YES_*`), `job` the job
        each takes first (-1 keeps it); its outcome is STLR. Either result
        is read off a later snapshot, as for `set_jobs`."""
        payload = struct.pack('<hhB', source_index, dest_index, len(pops))
        payload += bytes(int(p) for p in pops)
        if answers is not None:
            payload += struct.pack('<Bb', int(answers) & 0xFF, int(job))
        self._send_message(MSG_SETTLE_POPS, payload)

    @property
    def can_demolish(self):
        """The engine takes MSG_DEMOLISH (open fix 111, CAP_DEMOLISH)."""
        return bool(getattr(self, "capabilities", 0) & CAP_DEMOLISH)

    def demolish(self, colony_index, building):
        """Start the original's demolish of one building of the colony the
        colony screen shows (`MSG_DEMOLISH`, open fix 111,
        `doc/ext_building_demolish.patch`). The engine refuses, writing
        nothing, unless that colony is on screen and has the building; what
        follows — the refusal box, the confirmation, the refund — is the
        game's and comes back as MSGB."""
        self._send_message(MSG_DEMOLISH,
                           struct.pack('<hh', colony_index, building))

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
        # The socket is non-blocking for the reads. `sendall` on it raises
        # BlockingIOError when the engine's receive buffer is full, after
        # part of the frame may be out: a retry cannot resume, and dropping
        # the connection for it is the busy-engine reconnect decision 62's
        # STALE_TIMEOUT forbids. So the send waits, up to SEND_TIMEOUT, for
        # the buffer to drain; only a send that still fails is a loss
        # (audit TD-08).
        try:
            self.sock.settimeout(SEND_TIMEOUT)
            try:
                self.sock.sendall(self._frame(msg_type, payload))
            finally:
                if self.sock is not None:
                    self.sock.setblocking(False)
        except (BrokenPipeError, OSError) as e:
            self._lost(f"Send failed: {e}")

    @staticmethod
    def _frame(msg_type, payload=b''):
        """One framed message's bytes."""
        msg_header = struct.pack('<HHI', msg_type, 0, 0)
        return struct.pack('<II', MAGIC, len(msg_header) + len(payload)) + \
            msg_header + payload

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
        if msg_type not in REPEATED:
            self.changes += 1
        else:
            if self._last_of is None:
                self._last_of = {}
            if payload != self._last_of.get(msg_type):
                self.changes += 1
                self._last_of[msg_type] = payload
            if msg_type == MSG_STATE:
                self._last_state = self._last_of[msg_type]
        if msg_type == MSG_HELLO_REPLY:
            caps = struct.unpack_from("<H", payload, 2)[0] \
                if len(payload) >= 4 else 0
            log.info("HELLO_REPLY received (capabilities 0x%04X)", caps)
            self.capabilities = caps
            # A LAYOUT follows the reply when the engine says so (decision
            # 97); a snapshot read before it would be read at the specs'
            # own offsets, which are another engine's. An engine without
            # the bit is the one the specs were read against.
            self._layout_pending = bool(caps & CAP_LAYOUT)
            engine_layout.install(None)

        elif msg_type == MSG_LAYOUT:
            try:
                engine_layout.install(engine_layout.parse(payload))
            except ValueError as e:
                log.error(f"Layout parse error: {e} — snapshots not read")
                return
            self._layout_pending = False

        elif msg_type == MSG_STATE:
            self.stats["state"] += 1
            if getattr(self, "_layout_pending", False):
                return
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
                self.stats["state_ok"] += 1
            except Exception as e:
                self._parse_failed("state", e)

        elif msg_type == MSG_FIELDS:
            self.stats["fields"] += 1
            try:
                self.state.fields = parse_fields(payload)
                # The engine sends MSG_SAVE_SLOTS right AFTER the list
                # it belongs to, so a list with none has no slots.
                self.state.save_slots = None
            except Exception as e:
                # an old list is a lie nobody can detect; none is "unknown"
                self.state.fields = []
                self._parse_failed("fields", e)

        elif msg_type == MSG_VISUAL:
            self.stats["visual"] += 1
            try:
                fb, pal = parse_visual(payload)
                self.state.framebuffer = fb
                self.state.palette = pal
            except Exception as e:
                self._parse_failed("visual", e)

        elif msg_type == MSG_SAVE_SLOTS:
            try:
                self.state.save_slots = parse_save_slots(payload)
            except Exception as e:
                self._parse_failed("slots", e)

        elif msg_type == MSG_EVENT:
            if len(payload) >= 4:
                evt_flags, screen = struct.unpack_from(
                    '<Hh', payload, 0
                )
                log.debug(f"Event: flags=0x{evt_flags:04X} "
                          f"screen={screen}")
