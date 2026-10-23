"""The small galaxy map's painted background — work order 326 Part B.

HD EXTENSION `minimap_background` (Data, WO 326: "background minimap.png
is the minimap's background"): with the player's mod folder on and the
picture `files/screens/fleets/assets/pictures/minimap_background.png` in
it, the map's panel is filled with that picture instead of the black the
original fills its box with (`graphics::Fill_(..., 0)`, movebox.cpp:38,
`fltdraw.fill_inset`); the stars, the stacks and the relocation lines are
drawn over it as before. The original has no picture there.

WHERE IT LIVES (Data's decision, WO 326; decision 95): in the player's
mod folder only, never in either tree or the base pack — a `usermod.SLOTS`
name, found through `Resources.resolve` (decision 72), so a modder's file
of the same name is the one drawn.

THE ARRANGEMENT IS THE MOCKUP'S (Data, WO 326, mockup.png): the picture
fills the whole map panel to its frame — not only the star area
(`inset_map`) — covering it at its own proportion, never stretched, the
overflow cut evenly (`core.backgrounds.cover`), clipped to the panel's
outline (`blocks.panel_polygon`) with the edge drawn again over it, the
way the Leaders screen's map box takes its picture (`ldrpics.draw_box`).

UNCHANGED BRIGHTNESS — a choice, not a measurement: the Leaders screen
holds its map picture no brighter than its plain box; this box's plain
ground is black (luminance 0), so the same rule would erase the picture
Data asked for. Parked for Data (the WO 326 report).

WITHOUT IT — the folder off, no file, a file that cannot be read (one log
line) — the panel is drawn as before this order: the black inset.
"""
import logging
import os

import pygame

from core import backgrounds
from core import usermod
from core.hud import blocks as hud

log = logging.getLogger("fleets")

#: The tree path the mod folder fills (`usermod.SLOTS`).
PICTURE = "screens/fleets/assets/pictures/minimap_background.png"
#: The panel the picture fills (`flthud.HUD_PANELS`).
PANEL = "map_panel"

_loaded = {}
_made = {}


def path():
    """The picture's file, or None (folder off, or no file)."""
    if not usermod.active():
        return None
    from core import resources
    p = resources.res.resolve(PICTURE)
    return p if p and os.path.isfile(p) else None


def source():
    """The picture as loaded and the file's stamp, or (None, None)."""
    p = path()
    if p is None:
        return None, None
    try:
        stamp = (p, os.stat(p).st_mtime_ns)
    except OSError:
        return None, None
    if stamp not in _loaded:
        try:
            img = pygame.image.load(p)
            img = img.convert() if pygame.display.get_surface() else img
        except (pygame.error, OSError) as exc:
            log.warning("fleets: minimap picture %s unreadable (%s) — the "
                        "map is drawn black, as without it", p, exc)
            img = None
        _loaded.clear()
        _loaded[stamp] = img
    return _loaded[stamp], stamp


def picture(size, scale):
    """The picture covering `size`, transparent outside the panel's
    outline, or None. Made once per file, size and scale."""
    img, stamp = source()
    if img is None:
        return None
    w, h = int(size[0]), int(size[1])
    key = (stamp, w, h, round(scale, 4))
    if key not in _made:
        pic = backgrounds.cover(img, w, h)
        # headless (the suite, the preview tools) there is no display
        # format to convert to; a 32-bit alpha surface stands in
        pic = pic.convert_alpha() if pygame.display.get_surface() else \
            pic.convert_alpha(pygame.Surface((1, 1), pygame.SRCALPHA))
        mask = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.polygon(mask, (255, 255, 255, 255),
                            hud.panel_polygon(w, h, scale))
        pic.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        _made.clear()
        _made[key] = pic
    return _made[key]


def draw(surface, screen):
    """The picture in the map's panel, its edge again over it; False when
    nothing is drawn (the black inset stands)."""
    box = screen.box_by_name(PANEL)
    rect = box.screen_rect if box is not None else None
    if not rect or rect.w < 4 or rect.h < 4:
        return False
    scale = screen.layout.scale
    pic = picture(rect.size, scale)
    if pic is None:
        return False
    surface.blit(pic, rect.topleft)
    hud.panel(surface, rect, scale, filled=False)
    return True
