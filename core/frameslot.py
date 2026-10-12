"""A screen's painted frame — HD EXTENSION, work order 197 E (195's Q3).

THE SLOT. `screens/<screen>/assets/frame.png`, 3840x2160 with alpha, laid
over the whole window after the screen has drawn. OrionLayer ships no
frame (decision 71: every screen frameless); a mod fills the slot — the
player's `frames/<screen>.png` (`core.usermod`) or a developer mod's file
at the tree path. Without a frame nothing new is drawn.

DRAWN ONLY WHERE IT FITS (195 §3.4-3.5, decided as Q3 (c): one full-screen
frame now, per-panel pieces later):
  - the window is 16:9 (within 1 %): a painted picture scales uniformly,
    the boxes do not at other aspects (anchors, stretching rows);
  - the frame was painted for the screen's CURRENT layout: its layout hash
    (`layout_hash`, generated from the boxes the screen places at
    3840x2160 — never a counter somebody bumps) is in the PNG's text chunk
    `orionlayer-layout`, written there by `tools/frame_template.py`, or in
    the mod's `mod.json` `{"frames": {"<screen>": "<hash>"}}`. A frame
    without one, or for another layout, is not drawn: a crooked frame is
    worse than none.
Every refusal is logged once and kept in `REFUSED` for the settings row.
"""
import hashlib
import json
import logging
import os

import pygame

log = logging.getLogger("frameslot")

SIZE = (3840, 2160)
ASPECT, TOLERANCE = 16 / 9, 0.01
CHUNK = "orionlayer-layout"
TREE = "screens/{screen}/assets/frame.png"

#: screen -> why its frame is not drawn (the last refusal).
REFUSED = {}
_cache = {}


def layout_hash(res, screen):
    """12 hex digits of the screen's box rectangles at 3840x2160, as
    `Box.update_layout` places them (anchors included), or None for a
    screen without boxes.json (its geometry is code — no frame slot)."""
    from core.box import load_boxes
    from core.layout import Layout
    path = res.screen_file(screen, "boxes.json")
    if not path:
        return None
    layout = Layout(*SIZE)
    rows = []
    for box in load_boxes(path, *SIZE):
        box.update_layout(layout)
        r = box.screen_rect
        rows.append([box.name, list(r) if r is not None else None])
    rows.sort(key=lambda row: str(row[0]))
    blob = json.dumps(rows, separators=(",", ":")).encode()
    return hashlib.sha1(blob).hexdigest()[:12]


def painted_for(path):
    """The layout hash a frame PNG carries in its text chunk, or None."""
    try:
        from PIL import Image
        with Image.open(path) as img:
            return (img.text or {}).get(CHUNK) if hasattr(img, "text") \
                else img.info.get(CHUNK)
    except (OSError, ValueError, ImportError):
        return None


def _refuse(screen, why):
    if REFUSED.get(screen) != why:
        log.info("frame of %s not drawn: %s", screen, why)
    REFUSED[screen] = why
    return None


def frame_for(res, screen, win_w, win_h):
    """The frame scaled to the window, or None (with `REFUSED[screen]`
    saying why, unless there simply is no frame)."""
    path = res.resolve(TREE.format(screen=screen)) if screen else None
    if not path:
        REFUSED.pop(screen, None)
        return None
    if win_h <= 0 or abs(win_w / win_h - ASPECT) > ASPECT * TOLERANCE:
        return _refuse(screen, f"the window is {win_w}x{win_h}, not 16:9")
    try:
        stamp = os.path.getmtime(path)
    except OSError:
        return None
    key = (screen, path, stamp, win_w, win_h)
    if key in _cache:
        return _cache[key]
    from core import usermod
    want = layout_hash(res, screen)
    have = painted_for(path) or usermod.frame_layouts().get(screen)
    if want is None:
        return _refuse(screen, "the screen has no boxes to paint a frame for")
    if have is None:
        return _refuse(screen, "no layout hash (paint over the template "
                               "from tools/frame_template.py, or name it in "
                               "mod.json)")
    if have != want:
        return _refuse(screen, f"painted for layout {have}, the screen's is "
                               f"{want} — repaint over a new template")
    try:
        img = pygame.image.load(path)
    except (pygame.error, OSError) as err:
        return _refuse(screen, f"cannot be read ({err})")
    if img.get_size() != SIZE:
        return _refuse(screen, f"{img.get_width()}x{img.get_height()}, "
                               f"not 3840x2160")
    surf = img.convert_alpha() if pygame.display.get_surface() else img
    scaled = pygame.transform.smoothscale(surf, (win_w, win_h))
    _cache.clear()
    _cache[key] = scaled
    REFUSED.pop(screen, None)
    return scaled


def draw(surface, res, screen):
    """Lay the screen's frame over `surface` where it fits."""
    img = frame_for(res, screen, *surface.get_size())
    if img is not None:
        surface.blit(img, (0, 0))
    return img is not None
