"""TOOL — mouse and key events from outside, into the ordinary loop.

**This is a TOOL and not a feature.** It exists because a live
acceptance has to follow a CLICK PATH, and a session driving this
project cannot move the pointer: under Wayland an X client's
`warp_pointer` is constrained and synthetic button events do not reach
the window (work orders 140 and 141, both of which had to fall back to
`livesend` and say so). Without it the next acceptance steps — select
a cell, toggle a filter, RETURN — cannot be run at all.

WHAT IT IS NOT. It is not a second input path. It calls
`pygame.event.post` and stops; from there a click is the ordinary
`MOUSEBUTTONDOWN` the window would have produced, and it goes through
`App._handle_events`, `App._handle_click`, `_showing_original` and the
screen's own handler exactly as a real one does. That is decision 5
stated for input: one path, or the thing that proves the layout proves
it against a copy of the layout. Nothing here knows what a screen is.

OFF UNLESS ASKED. The socket exists only when `ORIONLAYER_DEBUG_INPUT`
is in the environment. Not a setting in `settings.json` and not one in
`user_settings.json`: a setting can be saved by accident and then lives
on a disk somebody forgets about, and `core/usersettings.py` writes
back keys it does not know (fundament 63). An environment variable is
gone when the shell is.

AND IT SAYS SO. One line at startup, the same shape as the build line
(work order 139 C), because a channel that can drive the game must not
be quiet about being open.

WHY A UNIX SOCKET. No port, so nothing is reachable from anywhere but
this machine's filesystem, and the mode is 0600 — checked here rather
than assumed, because `os.chmod` after `bind` leaves a window and the
umask is not ours to trust.

WHAT IT ACCEPTS, one JSON object per line:

    {"type": "click", "x": 960, "y": 540}     left button, down + up
    {"type": "down",  "x": 960, "y": 540}     press only
    {"type": "up",    "x": 960, "y": 540}     release only
    {"type": "motion", "x": 960, "y": 540}
    {"type": "key", "key": "f"}               key down + up
    {"type": "wheel", "y": 1}

Coordinates are WINDOW coordinates, the same ones SDL reports, so a
caller computes them from `boxes.json` exactly as the screen does.
Anything else is ignored with one log line: a tool that cannot say what
it was asked for has nothing to post.
"""
import json
import logging
import os
import socket
import stat

import pygame

log = logging.getLogger("debuginput")

#: The one switch. Present in the environment or the socket is not
#: created at all — see the module docstring for why not a setting.
ENV_VAR = "ORIONLAYER_DEBUG_INPUT"

#: Socket name inside `$XDG_RUNTIME_DIR`.
SOCKET_NAME = "orionlayer-debug-input.sock"

#: Every event kind this accepts, so an unknown one is a refusal and
#: not a silent no-op.
KINDS = ("click", "down", "up", "motion", "key", "wheel")


def socket_path():
    """Where the socket lives, or None when there is no runtime dir."""
    base = os.environ.get("XDG_RUNTIME_DIR")
    return os.path.join(base, SOCKET_NAME) if base else None


def enabled():
    return bool(os.environ.get(ENV_VAR))


class DebugInput:
    """The listener. `None` in `App` when the switch is not set."""

    def __init__(self, path):
        self.path = path
        self._sock = None
        self._conns = []
        self._buf = {}

    @classmethod
    def open(cls):
        """The listener, or None — and None is the normal case.

        Returns None without a word when the switch is not set; says
        why in one line when it is set and the socket cannot be made,
        because a tool that was asked for and did not appear must not
        be silent about it.
        """
        if not enabled():
            return None
        path = socket_path()
        if path is None:
            log.warning("%s is set but XDG_RUNTIME_DIR is not; no debug "
                        "input socket", ENV_VAR)
            return None
        try:
            if os.path.exists(path):
                os.unlink(path)
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            # BEFORE the bind, so there is no window in which the
            # socket exists with the umask's mode.
            old = os.umask(0o177)
            try:
                sock.bind(path)
            finally:
                os.umask(old)
            os.chmod(path, 0o600)
            sock.setblocking(False)
            sock.listen(4)
        except OSError as exc:
            log.warning("%s is set but the socket could not be opened: %s",
                        ENV_VAR, exc)
            return None
        mode = stat.S_IMODE(os.stat(path).st_mode)
        if mode != 0o600:
            log.warning("debug input socket has mode %o, not 600; closing",
                        mode)
            sock.close()
            os.unlink(path)
            return None
        self = cls(path)
        self._sock = sock
        log.info("TOOL: debug input socket open at %s (mode %o) — %s is "
                 "set. Events posted here take the ordinary input path.",
                 path, mode, ENV_VAR)
        return self

    # ── Per frame ─────────────────────────────────────────

    def pump(self):
        """Accept, read and post. Returns how many events were posted."""
        if self._sock is None:
            return 0
        while True:
            try:
                conn, _ = self._sock.accept()
            except (BlockingIOError, OSError):
                break
            conn.setblocking(False)
            self._conns.append(conn)
            self._buf[conn] = b""
        posted = 0
        for conn in list(self._conns):
            try:
                chunk = conn.recv(4096)
            except BlockingIOError:
                continue
            except OSError:
                chunk = b""
            if not chunk:
                self._drop(conn)
                continue
            self._buf[conn] += chunk
            while b"\n" in self._buf[conn]:
                line, _, rest = self._buf[conn].partition(b"\n")
                self._buf[conn] = rest
                posted += self._post(line)
        return posted

    def _drop(self, conn):
        self._conns.remove(conn)
        self._buf.pop(conn, None)
        try:
            conn.close()
        except OSError:
            pass

    def _post(self, line):
        """One line -> pygame events. Returns how many were posted."""
        try:
            msg = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            log.warning("debug input: not JSON (%s)", exc)
            return 0
        kind = msg.get("type")
        if kind not in KINDS:
            log.warning("debug input: unknown type %r (known: %s)",
                        kind, ", ".join(KINDS))
            return 0
        events = self._events(kind, msg)
        for event in events:
            pygame.event.post(event)
        log.info("debug input: %s %s -> %d event(s)", kind,
                 {k: v for k, v in msg.items() if k != "type"}, len(events))
        return len(events)

    @staticmethod
    def _events(kind, msg):
        pos = (int(msg.get("x", 0)), int(msg.get("y", 0)))
        button = int(msg.get("button", 1))
        if kind == "motion":
            return [pygame.event.Event(pygame.MOUSEMOTION, pos=pos,
                                       rel=(0, 0), buttons=(0, 0, 0))]
        if kind in ("click", "down", "up"):
            down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos,
                                      button=button)
            up = pygame.event.Event(pygame.MOUSEBUTTONUP, pos=pos,
                                    button=button)
            return {"click": [down, up], "down": [down], "up": [up]}[kind]
        if kind == "wheel":
            return [pygame.event.Event(pygame.MOUSEWHEEL,
                                       x=int(msg.get("x", 0)),
                                       y=int(msg.get("y", 0)))]
        key = msg.get("key", "")
        code = pygame.key.key_code(key) if isinstance(key, str) and key \
            else int(key or 0)
        return [pygame.event.Event(pygame.KEYDOWN, key=code, mod=0,
                                   unicode=key if isinstance(key, str)
                                   and len(key) == 1 else ""),
                pygame.event.Event(pygame.KEYUP, key=code, mod=0)]

    def close(self):
        for conn in list(self._conns):
            self._drop(conn)
        if self._sock is not None:
            try:
                self._sock.close()
            finally:
                self._sock = None
            try:
                os.unlink(self.path)
            except OSError:
                pass
