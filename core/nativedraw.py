"""The native-drawing library every 640x480-transcribed screen shares.

One window rectangle per native rectangle (`rect`, `point`, `field_hit`),
the HD text sizes taken from the original's own pixel heights (`font_px`,
`blit_text`, `fit`), the glass boxes and the sprite scalings. It lived in
`screens/leaders/ldrdraw` until work order 324: audience, build_queue,
colony, combat, design_box, galaxy_map, ground_combat, info, race_report,
races, refit and ship_design drew through it, so a Leaders file was the
shared library. What stayed in `ldrdraw` is what only the Leaders screen
has (its rows, slots, tabs); the bodies below were moved
unchanged, apart from `native_scale` reading the plane's size from
`core/nativeview` instead of from `ldrgeom` (both are 640x480).

Conversion of the plane itself is `core/nativeview`; this module is what
the screens draw WITH it.
"""
import pygame

from core.hud import blocks as hud

from core import nativeview as nat
from core import palette
from core.config import REF_H, REF_W


MIN_FONT = 8

#: The inner boxes: the research screens' two colours, read from the
#: sections that own them (work order 166 C) — not copied here.
BOX_OUTLINE = palette.col("panel", "thin_border", (55, 65, 85))

#: DEVIATION `hd_font`: the text heights in the original's own pixels,
#: chosen from the line pitch each text sits on (the skill lines step
#: 0x11 = 17; the cost column's two lines share one text line's height).
NATIVE_TEXT = {"name": 10, "cost": 7, "status": 8, "skill": 9,
               "strip": 9, "button": 9, "note": 8}


def native_scale(layout):
    """Window pixels per native pixel — `nativeview`'s own scale."""
    return layout.scale * min(REF_W / nat.NATIVE_W, REF_H / nat.NATIVE_H)


def rect(layout, native):
    return pygame.Rect(*nat.window_rect(native, layout))


def field_hit(layout, f, x, y):
    """Is window point (x, y) on live field `f`, drawn where the layout
    maps its native rectangle — the panel map's click test (work order
    225), one home since work order 228 (four screens had a copy)."""
    return rect(layout, (f.x, f.y, f.x_end, f.y_end)).collidepoint(x, y)


def field_slant_hit(layout, f, x, y):
    """`field_hit` for a field drawn as the shell's slanted button: its
    own shape (`core.hud.shell.hit`)."""
    from core.hud import shell
    return shell.hit(rect(layout, (f.x, f.y, f.x_end, f.y_end)), x, y)


def point(layout, x, y):
    return nat.window_point((x, y), layout)


def font_px(layout, key):
    return max(MIN_FONT, int(round(NATIVE_TEXT[key] * native_scale(layout))))

def fit(style, text, max_w, size):
    """The largest size at or below `size` whose RENDER fits `max_w`
    (measured by rendering, `core/textfit`'s rule)."""
    while size > MIN_FONT and style.render_text(text, size,
                                                (255, 255, 255)).get_width() > max_w:
        size -= 1
    return size


def blit_text(surface, style, text, x, y, max_w, size, colour, align="left"):
    """One line, shrunk to fit `max_w`, anchored `left`/`right`/`center`
    at window `x`. Returns the drawn rect or None."""
    if not text:
        return None
    size = fit(style, text, max(1, max_w), size)
    surf = style.render_text(text, size, colour)
    if align == "right":
        x -= surf.get_width()
    elif align == "center":
        x -= surf.get_width() // 2
    surface.blit(surf, (x, y))
    return pygame.Rect(x, y, surf.get_width(), surf.get_height())


def draw_box(surface, screen, native):
    """One inner box: fill and plate. DEVIATION `inner_boxes_drawn`."""
    r = rect(screen.layout, native)
    # A HUD panel since decision 71 (work order 169).
    hud.panel(surface, r, screen.layout.scale)
    return r


#: How far a sprite may overhang the scale it stands at (work order 225):
#: in a shell panel the scale is the panel's (`PanelMap.sprite_scale`),
#: 1.91 for the Leaders rows at 1080p, and a strict floor would halve the
#: portraits there; 5 % keeps the step the island gave (2) while the
#: portrait still ends above its row's status line.
STEP_SLACK = 1.05


def magnified(sprite, layout):
    """HD EXTENSION `sprite_scale`: the largest integer factor that does
    not exceed the native-to-window scale — in a shell panel the panel's
    own (`core.panelmap`), within `STEP_SLACK`."""
    fitted = getattr(layout, "sprite_scale", None)
    step = max(1, int(fitted * STEP_SLACK) if fitted is not None
               else int(native_scale(layout)))
    if step == 1:
        return sprite
    return pygame.transform.scale_by(sprite, step)


def stretched(sprite, window_rect):
    """HD EXTENSION `sprite_scale`: nearest-neighbour to the exact HD
    rectangle of the sprite's native one (`transform.scale` does not
    blend), so an art's painted cells land under the fields they belong
    to."""
    return pygame.transform.scale(sprite, window_rect.size)


def skill_icon(icon, size):
    """A skill icon in its `size` square: the original's drawing at the
    largest integer step that fits (HD EXTENSION `sprite_scale`), a painted
    one larger than the square scaled down smoothly to it (work order 255:
    a redrawn icon from the mod folder, `core.blobart`, is drawn at the
    slot's size, never magnified)."""
    w, h = icon.get_size()
    if w > size or h > size:
        k = min(size / w, size / h)
        return pygame.transform.smoothscale(
            icon, (max(1, round(w * k)), max(1, round(h * k))))
    step = max(1, min(size // max(1, w), size // max(1, h)))
    return pygame.transform.scale_by(icon, step) if step > 1 else icon
