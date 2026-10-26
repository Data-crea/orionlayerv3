"""Draw only on change — work order 273 (Data's decision of work order 262,
answering 255 P5 a).

The client drew every frame whole: a list screen at 4K with the glass on
costs about 30 ms a frame, at rest as much as in use (work order 255). A
frame that would draw the same picture again is now not drawn, and the
window keeps the last one.

WHAT "THE SAME PICTURE" MEANS, and why each part:

  * the screen says its picture is STILL (a class attribute): it draws
    nothing that moves with time — no animation, no blinking cursor, no
    frame counter. Every other screen is drawn every frame, as before;
  * the player has been quiet for `framerate.IDLE_AFTER` (one second): a
    hover, a press flash (0.3 s, `core/hud/shell.PRESSED_FOR`,
    `screenframe.ACTIVE_FOR`) and anything else input starts are drawn
    while they last;
  * nothing came from the game since the last drawn frame. The engine
    sends the WHOLE snapshot on every tick, changed or not (ext_api.cpp,
    the `SendToSubscribers(SUB_STATE, ...)` at the end of `Tick`), and the
    framebuffer likewise, so an arrival says nothing; `GameClient.changes`
    counts a message of such a kind (`game_client.REPEATED`) only when its
    bytes differ from the previous one of its kind, and every event.
    Measured live (work order 273, `dev:tools/snapshot_idle_probe.py`): at
    rest on the galaxy map, the colony summary and Planets, 73 to 134
    snapshots in four seconds, all byte for byte the same;
  * the window, the screen, its overlay, the mode and the editor are the
    ones of the last drawn frame;
  * the last drawn frame held no turning planet, or the next visible step
    of one is not due (`planetspin.take_touched`, work order 331: a
    fraction of a pixel at the sphere's centre, never faster than 15 a
    second): a planet on screen keeps a STILL screen drawing at that pace
    and no faster, a screen that shows none (or is covered) is gated as
    before;
  * and the last drawn frame is younger than `REDRAW_EVERY`: a change
    nothing above sees (a file loaded in the background) is drawn within
    a second.

`ORIONLAYER_DRAW_ALWAYS=1` draws every frame, as before (diagnostics).
"""
import os
import time

from core import framerate, planetspin

REDRAW_EVERY = 1.0
ENV = "ORIONLAYER_DRAW_ALWAYS"


def still(screen):
    """True for a screen whose picture changes only with input, the game's
    messages, the window or itself being replaced."""
    return screen is None or bool(getattr(type(screen), "STILL", False))


class DrawGate:
    def __init__(self):
        self._key = None
        self._at = 0.0
        self._pending = False
        self._turning = None
        self.drawn = 0
        self.skipped = 0

    @staticmethod
    def key(app):
        d = app.dispatcher
        client = getattr(app, "client", None)
        changes = getattr(client, "changes", None) if app.connected else None
        editor = getattr(app, "editor", None)
        return (changes, id(d.active), id(d.overlay), app.win_w, app.win_h,
                getattr(app, "render_mode", None),
                bool(getattr(editor, "active", False)),
                getattr(app, "_fs_surface", None) is not None)

    def needed(self, app, now=None):
        """True when this frame must be drawn; a frame drawn is counted and
        becomes the one the next compares with."""
        now = time.monotonic() if now is None else now
        key = self.key(app)
        if self._pending:
            # what the frame drawn last held, said by `planetspin.touch`
            self._turning, self._pending = planetspin.take_touched(), False
        d = app.dispatcher
        last_input = getattr(app, "_input_at", None)
        draw = (os.environ.get(ENV, "").lower() in ("1", "on", "yes")
                or not (still(d.active) and still(d.overlay))
                or last_input is None
                or now - last_input < framerate.IDLE_AFTER
                or key != self._key
                or now - self._at >= REDRAW_EVERY
                or (self._turning is not None
                    and now - self._at >= self._turning))
        if draw:
            self._key, self._at, self._pending = key, now, True
            planetspin.take_touched()      # only what THIS frame draws counts
            self.drawn += 1
        else:
            self.skipped += 1
        return draw

    def forget(self):
        """Another picture was drawn (the game's, a held frame, a notice):
        the next HD frame is drawn whatever it compares with."""
        self._key = None
