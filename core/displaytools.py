"""Display helpers that need none of the App's state.

One job: the two things main.py does to pygame's display that depend only
on pygame and the player's folders — `set_mode` (a window request and the
report of what was granted) and `save_screenshot` (F8). Split out of
main.py (decision 6); the App keeps what touches its own fields.
"""
import logging
import os

import pygame

log = logging.getLogger("orionlayer")


def set_mode(w, h, flags):
    """`pygame.display.set_mode`; the caller adopts the size granted.

    **A REQUESTED SIZE IS NOT A WINDOW SIZE.** The window manager
    may give less than was asked for, and on this project's own
    machine it does: measured 9 September 2026 on a single
    3440x1440 display, a request for 2560x1440 is granted
    2560x1371, 3440x1440 is granted 3440x1371, and 3840x2160 —
    which is one of the four sizes F7 offers — is granted
    3440x1371. **No `VIDEORESIZE` event is delivered for any of
    them**, so nothing downstream can notice on its own, and
    the expectation `core.resizeexpect` keeps for the event a
    deliberate resolution change may provoke was never even met.

    `win_w`/`win_h` used to be the numbers we asked for, and
    `Layout`, every box, the cursor and the frame plate are all
    built from them. At F7 "4K" the whole screen was therefore
    laid out for 3840x2160 inside a 3440x1371 surface: 1.12x too
    wide, 1.58x too tall, everything past the edge simply gone.
    Milder but live at every other size too — 2560x1440 got 69 px
    of height it did not have. That is
    `after_geometry_3840x2160.png` in the fixtures, whose FILE
    NAME is the request and whose pixels are the grant.

    The difference is REPORTED and not merely absorbed, because a
    window that is quietly smaller than the one configured is a
    state somebody has to be able to see in a log rather than
    infer from a screenshot. The formatter carries the timestamp
    (see `basicConfig` in main.py), which is what makes the line
    placeable against a resize the user remembers making.
    """
    surface = pygame.display.set_mode((w, h), flags)
    got_w, got_h = surface.get_size()
    if (got_w, got_h) != (w, h):
        log.warning(
            "window: asked for %dx%d, granted %dx%d — laying out "
            "for what was granted", w, h, got_w, got_h)
    return surface


def save_screenshot():
    """TOOL — the window's own surface to a PNG (F8).

    **It photographs the SURFACE, not the screen**, which is the
    whole point: a live acceptance needs a picture of what HD drew,
    and this session has more than once had a display that renders
    correctly and cannot be captured — work order 146 met a
    compositor that placed the window at (-985, -565) and answered
    a fullscreen request with "granted 1x38", so `import -window`
    had nothing to photograph while the game was running fine.
    Reading `pygame.display.get_surface()` sidesteps every one of
    those, because it is the same surface the renderer just filled.

    Under `$ORIONLAYER_SHOTS` when set (the live tools), else the
    player's own folder (`core.usermod.screenshot_dir`: on Linux
    `~/.config/orionlayer/screenshots/`) — never the working
    directory, which is the program's folder for a player (work order
    219). Named by the clock so a sequence keeps its order.
    """
    import datetime
    from core import usermod
    surface = pygame.display.get_surface()
    if surface is None:
        log.warning("F8: no display surface to save")
        return
    folder = os.environ.get("ORIONLAYER_SHOTS") or usermod.screenshot_dir()
    name = datetime.datetime.now().strftime("orionlayer_%H%M%S_%f.png")
    path = os.path.join(folder, name)
    try:
        os.makedirs(folder, exist_ok=True)
        pygame.image.save(surface, path)
    except (pygame.error, OSError) as exc:
        log.warning("F8: could not save %s (%s)", path, exc)
        return
    log.info("TOOL: screenshot %dx%d -> %s",
             surface.get_width(), surface.get_height(), path)
