"""Drawing the Leaders screen: the rows, the buttons, the strips, the boxes.

Everything is placed at the HD image of its native rectangle
(`ldrgeom`, through `core/researchnative`), so the drawing, the hit test
and a native screenshot all speak the original's coordinates.

WHAT IS TRANSCRIPTION AND WHAT IS OURS — each marked where it happens:

  TRANSCRIPTION   every position, every string, which picture, the two
                  alignments of the cost column, the text colours (as
                  PALETTE INDICES — 68 normal, 71 selected, 129 red,
                  officer.cpp:9-11 — resolved through the screen's own
                  palette when the art is extracted)
  DEVIATION       `inner_boxes_drawn` — the original paints its panels
                  into OFFICER.LBX 0, the full-screen art this order
                  leaves out ("no outer frame"); HD draws each inner box
                  as a fill and a plate, the research screens' look
                  (work order 166 C)
  DEVIATION       `hd_font` — the bitmap fonts 0/2/3 become the HD font
                  at a size taken from the native line pitch, shrunk to
                  the original's width where it would overflow (the
                  original squeezes, HD shrinks — `core/researchpanel`)
  HD EXTENSION    `sprite_scale` — portraits and skill icons at an
                  INTEGER magnification, centred on their native cell
                  (fleets' rule, decision 28); buttons and the view box
                  art at their native rectangle's exact HD size,
                  nearest-neighbour, so every pixel is the original's
                  and the art lines up with the fields over it
"""
import pygame

from core.hud import blocks as hud
from core.hud import text as hudtext

from core import leaderportraits
from core import palette
from core import researchnative as nat
from core.config import REF_H, REF_W

from . import ldrgeom as geom
from . import ldrpics

MIN_FONT = 8

#: The row text colours as the ORIGINAL names them — palette indices
#: (`_normal_text_colors` 68, `_selected_text_colors` 71, `_red_colors`
#: 129, the body index of each; officer.cpp:9-11) — and what FONTS.LBX
#: entry 9 holds at each, read on this machine for work order 167 and
#: used only while the player's palette is not extracted. The smoke
#: test holds the two against each other whenever the palette is there.
TEXT_INDEX = {"normal": 68, "selected": 71, "red": 129}
TEXT_FALLBACK = {"normal": (120, 156, 192), "selected": (160, 208, 236),
                 "red": (196, 0, 0)}

#: The inner boxes: the research screens' two colours, read from the
#: sections that own them (work order 166 C) — not copied here.
BOX_OUTLINE = palette.col("panel", "thin_border", (55, 65, 85))
#: The galaxy box is NOT black any more (work order 175): the original
#: draws its stars over the black of OFFICER.LBX 0 there, and Data's
#: screenshot showed that black as a hole in the HUD. It is a glass
#: panel like every other box — DEVIATION `map_glass`.

#: DEVIATION `hd_font`: the text heights in the original's own pixels,
#: chosen from the line pitch each text sits on (the skill lines step
#: 0x11 = 17; the cost column's two lines share one text line's height).
NATIVE_TEXT = {"name": 10, "cost": 7, "status": 8, "skill": 9,
               "strip": 9, "button": 9, "note": 8}


def native_scale(layout):
    """Window pixels per native pixel — `researchnative`'s own scale."""
    return layout.scale * min(REF_W / geom.NATIVE_W, REF_H / geom.NATIVE_H)


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


def text_colour(art, key):
    """A text colour: the palette's at the original's index, else the
    value read off that palette for work order 167."""
    rgb = art.palette_rgb(TEXT_INDEX[key]) if art is not None else None
    return tuple(rgb) if rgb else TEXT_FALLBACK[key]


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


def strip_rect(layout, native):
    """Where a strip under the view box or the map is drawn: its native
    rectangle, centred on the view box. DEVIATION `strips_centred` (work
    order 238): original = the view strip at 364-566 and the map strip at
    364-567 (officer.cpp:756, :2102-2105), 1 and 1.5 native px right of
    the view box's centre (300-629) — 10 window px uneven at 3840x2160 once
    the panel holds the view box edge to edge. HD = the same width, centred;
    nothing is hit there."""
    r = rect(layout, native)
    r.centerx = rect(layout, geom.VIEW_BOX).centerx
    return r


def draw_strip_box(surface, screen, native):
    """A strip's box, where `strip_rect` puts it. DEVIATION
    `inner_boxes_drawn`, as `draw_box`."""
    r = strip_rect(screen.layout, native)
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


# ── The inner boxes ───────────────────────────────────────

#: One box per row: the portrait and the text field together, one
#: native pixel short of the next row so the boxes stand apart.
def row_box(i):
    x1, y1, _x2, _y2 = geom.portrait_field(i)
    _a, _b, x2, y2 = geom.text_field(i)
    return (x1, y1, x2, y2 - 1)


def draw_frame_boxes(surface, screen, slots=None, art=None):
    """The boxes behind everything, each a glass HUD panel (work order
    174's blocks): four rows, the view box, the galaxy box, two strips.

    A row's box and the galaxy box show their picture where the mod
    folder has one (work order 237, `ldrpics`): `slots` {row: Row or
    None} once the view is known — a row with a leader its slot's
    picture, an empty one the empty slot's — else every row as before."""
    layout = screen.layout
    for i in range(geom.ROWS):
        r = rect(layout, row_box(i))
        if slots is None or not ldrpics.draw_box(
                surface, r, layout.scale,
                ldrpics.slot_place(i, slots.get(i) is not None),
                word_zones(screen, i, slots.get(i), art)):
            draw_box(surface, screen, row_box(i))
    draw_box(surface, screen, geom.VIEW_BOX)
    if not ldrpics.draw_box(surface, rect(layout, geom.GALAXY_BOX),
                            layout.scale, "minimap", map_zones(screen)):
        draw_box(surface, screen, geom.GALAXY_BOX)
    draw_strip_box(surface, screen, geom.VIEW_STRIP)
    draw_strip_box(surface, screen, geom.MAP_STRIP)


# ── Where words stand on a picture (work order 237) ──────

def word_zones(screen, slot, row, art):
    """[(window Rect, ceiling)] where a row's words stand — the ground
    `ldrpics.dim` keeps under each word's floor. A row with a leader: the
    name and cost band and every skill line in the rows' ink, the status
    line and the ETA in the red (the strictest ink there); an empty row:
    the caption's two lines."""
    from core.hud import fill
    layout = screen.layout
    box = fill.member("panel")
    if row is None:
        return [(z, ldrpics.ceiling(ink, box))
                for z, ink in caption_lines(screen, slot)[1]]
    from . import ldrslot
    normal = ldrpics.ceiling(text_colour(art, "normal"), box)
    red = ldrpics.ceiling(text_colour(art, "red"), box)
    slot = slot_of(screen, row)
    style, pad = screen.style, slot.px(0.02)
    zones = []
    for surf, at in cost_lines(screen, row, (255, 255, 255), slot):
        zones.append((pygame.Rect(at, surf.get_size()).inflate(2 * pad, 0),
                      normal))
    cost_left = min([z.x for z, _c in zones] + [slot.cost_right])
    room = cost_left - slot.text_x - slot.px(ldrslot.NAME_CAP)
    for text, cap, top, ceil in (
            (row.name, ldrslot.NAME_CAP, slot.name_top, normal),
            (row.status, ldrslot.STATUS_CAP, slot.status_top,
             red if row.status_red else normal)):
        if text:
            surf, c = _render_cap(style, text, slot.px(cap), (255, 255, 255),
                                  room)
            zones.append((pygame.Rect(slot.text_x, top - c, surf.get_width(),
                                      surf.get_height()).inflate(2 * pad, 0),
                          ceil))
    zones += [(r, normal) for r in skill_line_rects(screen, row)]
    if row.eta:
        p = portrait_rect(screen, row, art)
        h = slot.px(ldrslot.STATUS_CAP) * 2
        zones.append((pygame.Rect(p.x, p.centery - h, p.w, 2 * h), red))
    return zones


def map_zones(screen):
    """The galaxy box's picture is never brighter than the plain box it
    replaces: stars, fleets and the chosen star's box are drawn where the
    snapshot puts them, over the whole box, in the original's colours —
    some at 2 : 1 on the plain box already — so every mark keeps at least
    the contrast it has there (measured, work order 237: the nebula's core
    took one star from 4.2 : 1 to 1.7 : 1 before this)."""
    from core.hud import fill
    r = rect(screen.layout, geom.GALAXY_BOX)
    return [(r, ldrpics.ground(fill.member("panel")))]


# ── The empty row's caption (work order 237) ──────────────

#: Placed as the mockup places it (`Mockup.png`, Data, 11 October 2026),
#: measured off its third row, whose frame is 928 x 181 px at (45, 481):
#: both lines start at 41.4 % of the box's width; the title's capitals
#: stand from 42.0 % of its height and are 9.4 % tall, the hint's from
#: 60.8 % and 6.6 %.
CAPTION_X = 0.414
CAPTION = (("title", "label", 0.420, 0.094), ("hint", "sub", 0.608, 0.066))


def caption_lines(screen, slot):
    """([(surface, topleft)], [(Rect, ink)]) of row `slot`'s caption:
    the words from the text table (`ldrtexts`, decision 73), each line
    shrunk where it would pass the box's right edge. None in hire mode,
    where "assign a leader from the pool" is not what the player is doing
    (Data's decision, work order 262 answering 237 P2)."""
    from core import modtexts
    from core.hud import text as hudtext
    view = getattr(screen, "_view", None)
    if view is not None and view.hire_mode:
        return [], []
    layout, style = screen.layout, screen.style
    box = rect(layout, row_box(slot))
    tab = "colony" if view is not None and \
        view.view == geom.VIEW_COLONY else "ship"
    room = box.right - (box.x + int(box.w * CAPTION_X)) - box.h // 6
    drawn, zones = [], []
    for key, role, top, cap in CAPTION:
        words = modtexts.text(f"leaders.empty.{tab}.{key}") or ""
        ink = hudtext.colour(role)
        size = max(MIN_FONT, int(round(
            cap * box.h / hudtext.cap_ratio(style))))
        size = fit(style, words, max(1, room), size)
        surf = style.render_text(words, size, ink)
        ink_top = surf.get_bounding_rect().y
        at = (box.x + int(box.w * CAPTION_X),
              box.y + int(round(box.h * top)) - ink_top)
        drawn.append((surf, at))
        zones.append((pygame.Rect(at, surf.get_size()), ink))
    return drawn, zones


def draw_empty(surface, screen, slots):
    """The caption over every empty row's picture (`slots` as in
    `draw_frame_boxes`); nothing where the row has no picture."""
    if slots is None or ldrpics.source("slot_empty") is None:
        return
    for i in range(geom.ROWS):
        if slots.get(i) is None:
            for surf, at in caption_lines(screen, i)[0]:
                surface.blit(surf, at)


# ── The rows ──────────────────────────────────────────────

def draw_rows(surface, screen, rows, art, lit=()):
    """Every listed leader, as `ldrrows.Row`s. `lit` is the set of leader
    ids drawn in the selected colours — the scanned and the selected one
    (officer.cpp:3608-3622)."""
    for row in rows:
        _draw_row(surface, screen, row, art, row.index in lit)


def _cap_size(style, cap_px):
    """The font size whose capitals are `cap_px` tall (the empty caption's
    rule, `caption_lines`)."""
    return max(MIN_FONT, int(round(cap_px / hudtext.cap_ratio(style))))


def _render_cap(style, text, cap_px, colour, max_w=None):
    """`text` with capitals `cap_px` tall, shrunk to `max_w`; the surface
    and the y of its capitals' top inside it."""
    size = _cap_size(style, cap_px)
    if max_w is not None:
        size = fit(style, text or " ", max(1, max_w), size)
    surf = style.render_text(text or " ", size, colour)
    cap_top = style.render_text("H", size, colour).get_bounding_rect().y
    return surf, cap_top


def blit_cap(surface, style, text, x, cap_top, cap_px, colour, max_w,
             align="left"):
    """One word of a slot: capitals `cap_px` tall standing at `cap_top`,
    shrunk to `max_w` (`fit`, the screen's rule), anchored `left` or `right`
    at `x`. Every word of a slot is drawn here, as every other word of the
    screen is by `blit_text` (the screen's text check watches both).
    Returns the drawn Rect, or None."""
    if not text:
        return None
    surf, cap = _render_cap(style, text, cap_px, colour, max_w)
    if align == "right":
        x -= surf.get_width()
    surface.blit(surf, (x, cap_top - cap))
    return pygame.Rect(x, cap_top - cap, surf.get_width(), surf.get_height())


def _widest_skill_name(screen, size):
    """The widest skill name of the language at `size` — the value column
    is set by it (`ldrslot.value_right`), so it stands still from leader to
    leader and from row to row."""
    words = getattr(screen, "_words", None)
    names = []
    if words is not None:
        from core import leaderskills as ls
        names = [words.estring(n) or "" for n in ls.SKILL_NAME_ESTRINGS]
    names += [name for r in getattr(screen, "_rows", ()) or ()
              for _sid, name, _v in r.skills]
    key = (size, tuple(names))
    hit = getattr(screen, "_widest_skill", None)
    if hit is not None and hit[0] == key:
        return hit[1]
    w = max((screen.style.render_text(n, size, (255, 255, 255)).get_width()
             for n in names if n), default=0)
    screen._widest_skill = (key, w)
    return w


def slot_of(screen, row):
    """Row `row`'s `ldrslot.Slot` — every rectangle the drawing, the dimmed
    ground and both right clicks use (decision 5)."""
    from . import ldrslot
    layout = screen.layout
    box = rect(layout, row_box(row.slot))
    inner = hud.panel_inner(box, layout.scale)
    slot = ldrslot.Slot(box, inner, len(row.skills))
    size = _cap_size(screen.style, slot.px(ldrslot.SKILL_CAP))
    values = [v for r in getattr(screen, "_rows", ()) or () for _s, _n, v
              in r.skills] + [v for _s, _n, v in row.skills]
    widest_v = max((screen.style.render_text(v, size, (255, 255, 255))
                    .get_width() for v in values if v), default=0)
    right = ldrslot.value_right(slot, _widest_skill_name(screen, size),
                                widest_v)
    return ldrslot.Slot(box, inner, len(row.skills), right)


def portrait_picture(screen, row, art, slot):
    """What stands in the slot's portrait column: the HD picture fitted to
    the column (`core.leaderportraits`, work order 255), else the
    original's drawing at the largest integer step that fits (HD EXTENSION
    `sprite_scale`), else None."""
    col = slot.portrait_column
    hd = leaderportraits.picture(row.rec, col.size, dark=row.dark)
    if hd is not None:
        return hd
    sprite = art.portrait(row.rec.pict_num, dark=row.dark) \
        if art is not None and art.available else None
    if sprite is None:
        return None
    w, h = sprite.get_size()
    step = max(1, min(col.w // max(1, w), col.h // max(1, h)))
    return pygame.transform.scale_by(sprite, step) if step > 1 else sprite


def plate_size(slot):
    """Where neither picture is there, the plate stands where the
    original's drawing would: 73 x 88 at the column's whole step."""
    nw, nh = leaderportraits.NATIVE_SIZE
    col = slot.portrait_column
    step = max(1, min(col.w // nw, col.h // nh))
    return (nw * step, nh * step)


def portrait_rect(screen, row, art):
    """Where row `row`'s portrait is drawn — the portrait's right click
    ("where is this leader") answers there, not at the native field's
    83 px (`ldrinput.right_click`)."""
    slot = slot_of(screen, row)
    pic = portrait_picture(screen, row, art, slot)
    if pic is None:
        return slot.portrait_rect(plate_size(slot))
    return slot.portrait_rect(pic.get_size())


def _draw_row(surface, screen, row, art, lit):
    """DEVIATION `mockup_slot` (`ldrslot`): the original's words and rules
    (`ldrrows`, officer.cpp:3578-3838) at the mockup's places."""
    from . import ldrslot
    style = screen.style
    ink = text_colour(art, "selected" if lit else "normal")
    slot = slot_of(screen, row)
    # The portrait standing on the column's floor, in front of the slot's
    # picture: the HD cut-out (work order 255), else the original's drawing.
    pic = portrait_picture(screen, row, art, slot)
    if pic is not None:
        at = slot.portrait_rect(pic.get_size())
        surface.blit(pic, at)
    else:
        at = slot.portrait_rect(plate_size(slot))
        screen.style.draw_plate(surface, at, screen.layout.scale, BOX_OUTLINE)
    cost_left = _draw_cost(surface, screen, row, ink, slot)
    room = cost_left - slot.text_x - slot.px(ldrslot.NAME_CAP)
    # The name at the top of the text column (:3624-3634's words).
    blit_cap(surface, style, row.name, slot.text_x, slot.name_top,
             slot.px(ldrslot.NAME_CAP), ink, room)
    _draw_status(surface, screen, row, art, ink, slot, at, room)
    _draw_skills(surface, screen, row, art, ink, slot)


def cost_room(slot):
    """The cost column's width: from the value column's right edge (and its
    gap) to the slot's — the cost can never run into a skill's value."""
    from . import ldrslot
    return slot.cost_right - slot.values_right - int(round(
        slot.box.w * ldrslot.VALUE_GAP))


def cost_specs(screen, row, slot):
    """[(text, cap px, x, cap top, align)] of the two cost lines at the
    slot's top right, in the original's two alignments (:3636-3675): for
    hire both right-aligned; otherwise the value starts where the label
    starts — never past the slot's right edge (German's "  Nr.", HESTR
    0x10A with two spaces in the file, is wider than its label "Inst.")."""
    from . import ldrslot
    style, right, room = screen.style, slot.cost_right, cost_room(slot)
    vcap, lcap = slot.px(ldrslot.COST_CAP), slot.px(ldrslot.LABEL_CAP)
    out = []
    lab_x = None
    if row.cost_label:
        lab = _render_cap(style, row.cost_label, lcap, (255, 255, 255),
                          room)[0]
        lab_x = right - lab.get_width()
    if row.cost_value:
        val = _render_cap(style, row.cost_value, vcap, (255, 255, 255),
                          room)[0]
        if row.cost_align == "right" or lab_x is None:
            out.append((row.cost_value, vcap, right, slot.y(
                ldrslot.COST_TOP), "right"))
        else:
            out.append((row.cost_value, vcap,
                        min(lab_x, right - val.get_width()),
                        slot.y(ldrslot.COST_TOP), "left"))
    if row.cost_label:
        out.append((row.cost_label, lcap, right, slot.y(ldrslot.LABEL_TOP),
                    "right"))
    return out


def cost_lines(screen, row, ink, slot):
    """[(surface, topleft)] of the cost lines as `cost_specs` places them —
    what the words' dimmed ground and the fit check measure."""
    out = []
    for text, cap_px, x, top, align in cost_specs(screen, row, slot):
        surf, cap = _render_cap(screen.style, text, cap_px, ink,
                                cost_room(slot))
        if align == "right":
            x -= surf.get_width()
        out.append((surf, (x, top - cap)))
    return out


def _draw_cost(surface, screen, row, ink, slot):
    """The cost at the top right; returns the left edge it takes."""
    left = slot.cost_right
    for text, cap_px, x, top, align in cost_specs(screen, row, slot):
        r = blit_cap(surface, screen.style, text, x, top, cap_px, ink,
                     cost_room(slot), align)
        if r is not None:
            left = min(left, r.x)
    return left


def _draw_status(surface, screen, row, art, ink, slot, portrait, room):
    """The status line under the name (INVENTION `status_under_name`; the
    original's words and red, :3677-3738) and the ETA over the portrait
    (:3742-3745)."""
    from . import ldrslot
    style = screen.style
    colour = text_colour(art, "red") if row.status_red else ink
    blit_cap(surface, style, row.status, slot.text_x, slot.status_top,
             slot.px(ldrslot.STATUS_CAP), colour, room)
    if row.eta:
        red = text_colour(art, "red")
        cap_px = slot.px(ldrslot.STATUS_CAP)
        width = _render_cap(style, row.eta, cap_px, red, portrait.w)[0] \
            .get_width()
        drawn = blit_cap(surface, style, row.eta, portrait.centerx
                         - width // 2, portrait.centery - cap_px // 2,
                         cap_px, red, portrait.w)
        # Two lines above and two below, in the red pair
        # (officer.cpp:3093-3096).
        for dy in (-3, -2):
            pygame.draw.line(surface, red, (drawn.x, drawn.y + dy),
                             (drawn.right, drawn.y + dy))
        for dy in (0, 1):
            pygame.draw.line(surface, red, (drawn.x, drawn.bottom + dy),
                             (drawn.right, drawn.bottom + dy))


def skill_line_rects(screen, row):
    """Each skill line's window rect, top down — the drawing's AND the
    right-click's (decision 5)."""
    return [line for line, _icon, _cy in slot_of(screen, row).skill_lines()]


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


def _draw_skills(surface, screen, row, art, ink, slot):
    """Icon, name, value per displayed skill (:3747-3837's words): one line
    each, the value right-aligned in its own column."""
    from . import ldrslot
    style = screen.style
    cap_px = slot.px(ldrslot.SKILL_CAP)
    for (sid, name, value), (line, icon_r, cy) in zip(row.skills,
                                                       slot.skill_lines()):
        icon = art.skill_icon(sid) if art is not None and art.available \
            else None
        if icon is not None:
            pic = skill_icon(icon, icon_r.h)
            surface.blit(pic, pic.get_rect(center=icon_r.center))
        top = cy - cap_px // 2
        drawn = blit_cap(surface, style, value, slot.values_right, top,
                         cap_px, ink, slot.values_right - slot.skill_name_x,
                         "right")
        room = (drawn.x if drawn else slot.values_right) \
            - slot.skill_name_x - int(round(slot.box.w * ldrslot.VALUE_GAP))
        blit_cap(surface, style, name, slot.skill_name_x, top, cap_px, ink,
                 room)


# ── Buttons ───────────────────────────────────────────────

#: DEVIATION `button_words`: without the extracted art a button is its
#: rectangle and a word. The words are the art's own, read off
#: OFFICER.LBX 3..13 — the source passes an EMPTY help string to every
#: one (officer.cpp:2858-2908), so there is no string to transcribe.
BUTTON_WORDS = {"tab_colony": "COLONY LEADERS", "tab_ship": "SHIP OFFICERS",
                "hire": "HIRE", "pool": "POOL", "dismiss": "DISMISS",
                "cancel": "CANCEL", "return": "RETURN", "prev": "<",
                "next": ">", "scroll_up": "^", "scroll_down": "v"}


#: The two tabs left to right; their band is shared in their art's
#: widths (`BUTTON_SIZE`, 150 and 140), the original's proportion.
TAB_ORDER = ("tab_colony", "tab_ship")


def tab_rects(screen):
    """{tab: window Rect} — where the two tabs are drawn AND hit.

    DEVIATION `tab_band` (work order 238): original = the art at
    (7, 10) and (160, 10), 150 and 140 wide (officer.cpp:836, :839), its
    fields at (9, 11) and (156, 11) (:2883-2899) — the pair runs from 1 px
    left of the rows to 3 px right of them, which the panel's scale made
    4 and 11 window px at 1920x1080. HD = the two tabs across the rows'
    own left and right edge, the shell's `element_gap` between them, the
    widths in the art's proportion, the height the art's at its native
    place. Drawn and hit in this one rect (decision 5)."""
    from core.hud import shell
    layout = screen.layout
    band = rect(layout, row_box(0))
    x, y = geom.TAB_DRAW[TAB_ORDER[0]]
    w, h = geom.BUTTON_SIZE[TAB_ORDER[0]]
    tall = rect(layout, (x, y, x + w - 1, y + h - 1))
    gap = shell.element_gap(layout)
    widths = [geom.BUTTON_SIZE[n][0] for n in TAB_ORDER]
    first = round((band.w - gap) * widths[0] / sum(widths))
    return {TAB_ORDER[0]: pygame.Rect(band.x, tall.y, first, tall.h),
            TAB_ORDER[1]: pygame.Rect(band.x + first + gap, tall.y,
                                      band.right - band.x - first - gap,
                                      tall.h)}


def draw_button(surface, screen, art, name, frame=0, dull=False,
                at=None, window=None):
    """One button at its native rectangle, as a HUD small button with
    its word — frame 1 is the "active" state, the dull picture the
    "disabled" one.

    **DEVIATION (decision 71, work order 169): the OFFICER.LBX button
    art is not drawn.** Work order 167 drew the original's own pictures
    here; decision 71 puts every screen in the HUD style, and a button
    is the HUD's block. The art is still extracted and still used for
    the portraits, the skill icons and the map box. Where the button
    sits and what it sends are unchanged — its native rectangle, its
    field."""
    layout = screen.layout
    if window is not None:
        r = pygame.Rect(window)
    else:
        x, y = at or geom.BUTTONS[name][0]
        w, h = geom.BUTTON_SIZE[name]
        r = rect(layout, (x, y, x + w - 1, y + h - 1))
    state = "disabled" if dull else ("active" if frame else "normal")
    hud.small_button(surface, r, layout.scale, state)
    colour = hudtext.colour("button")
    if dull:
        colour = tuple(c // 2 for c in colour)
    word = BUTTON_WORDS[name]
    # NO GLYPH (work order 225, decision 91): the word alone, capitals.
    cx = r.centerx
    blit_text(surface, screen.style, word, cx,
              r.y + (r.h - font_px(layout, "button")) // 2, r.w - 4,
              font_px(layout, "button"), colour, "center")
    return r


def draw_strip(surface, screen, native, text, art):
    """A centred strip (`Set_Fitted_Font_Style_` + `Print_Centered_`,
    officer.cpp:725-726, :824-825; movebox.cpp:289-290). One line where
    it fits at the note size; otherwise two, the way
    `Print_Paragraph_Centered_` fills the fleet strip's 22 px
    (officer.cpp:2186-2201) — never cut: the second line shrinks to fit.
    DEVIATION `strip_ink`: the rows' ink, not the owner's colour ramp."""
    if not text:
        return
    from core import textfit
    r = strip_rect(screen.layout, native)
    size = font_px(screen.layout, "strip")
    ink = text_colour(art, "normal")
    room = r.w - 6
    if screen.style.render_text(text, size, ink).get_width() <= room:
        blit_text(surface, screen.style, text, r.centerx,
                  r.y + (r.h - size) // 2, room, size, ink, "center")
        return
    size = font_px(screen.layout, "note")
    lines = textfit.wrap_text(screen.style, text, size, room)
    lines = lines[:1] + [" ".join(lines[1:])] if len(lines) > 2 else lines
    step = r.h // max(1, len(lines))
    for k, line in enumerate(lines):
        blit_text(surface, screen.style, line, r.centerx,
                  r.y + k * step + (step - size) // 2, room, size, ink,
                  "center")
