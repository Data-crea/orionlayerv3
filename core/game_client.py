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
    SUB_STATE, SUB_FIELDS, SUB_VISUAL, SUB_EVENTS,
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

    **One home for this, not two.** `struct_probe.py` had this loop
    and `colony_list_preview.py` needed the same one; a second copy
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

        try:
            # Read all available data
            while True:
                try:
                    chunk = self.sock.recv(65536)
                    if not chunk:
                        log.warning("orion2re disconnected")
                        self._reconnect()
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
                log.warning("No data for %.1fs — reconnecting", silent)
                self._reconnect()
                return False

            # Parse messages from buffer
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

                self._handle_message(msg_type, flags, payload)
                got_message = True

        except (ConnectionResetError, BrokenPipeError, OSError) as e:
            log.warning(f"Connection lost: {e}")
            self._reconnect()
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
        """Activate a field (simulates mouse click on a button)."""
        self._send_message(MSG_ACTIVATE,
                           struct.pack('<h', field_id))

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
                self.state = parse_state(payload)
                self.state.framebuffer = old_fb
                self.state.palette = old_pal
                self.state.fields = old_fields
            except Exception as e:
                log.error(f"State parse error: {e}")

        elif msg_type == MSG_FIELDS:
            self.stats["fields"] += 1
            try:
                self.state.fields = parse_fields(payload)
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

        elif msg_type == MSG_EVENT:
            if len(payload) >= 4:
                evt_flags, screen = struct.unpack_from(
                    '<Hh', payload, 0
                )
                log.debug(f"Event: flags=0x{evt_flags:04X} "
                          f"screen={screen}")
