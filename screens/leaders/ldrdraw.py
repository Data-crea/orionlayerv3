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

from core import palette
from core import researchnative as nat
from core.config import REF_H, REF_W

from . import ldrgeom as geom

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
BOX_FILL = palette.col("colony_summary", "panel_background", (8, 14, 23))
BOX_OUTLINE = palette.col("panel", "thin_border", (55, 65, 85))
#: The galaxy box is black because the original's is: the stars are
#: drawn over the black of OFFICER.LBX 0 in that rectangle.
MAP_FILL = (0, 0, 0)

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


def magnified(sprite, layout):
    """HD EXTENSION `sprite_scale`: the largest integer factor that does
    not exceed the native-to-window scale."""
    step = max(1, int(native_scale(layout)))
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


def draw_frame_boxes(surface, screen, show_view_box_art):
    """The boxes behind everything: four rows, the view box (unless the
    original's own art is drawn there), the galaxy box, two strips."""
    for i in range(geom.ROWS):
        draw_box(surface, screen, row_box(i))
    if not show_view_box_art:
        draw_box(surface, screen, geom.VIEW_BOX)
    r = draw_box(surface, screen, geom.GALAXY_BOX)
    surface.fill(MAP_FILL, r.inflate(-2, -2))
    draw_box(surface, screen, geom.VIEW_STRIP)
    draw_box(surface, screen, geom.MAP_STRIP)


# ── The rows ──────────────────────────────────────────────

def draw_rows(surface, screen, rows, art, lit=()):
    """Every listed leader, as `ldrrows.Row`s. `lit` is the set of leader
    ids drawn in the selected colours — the scanned and the selected one
    (officer.cpp:3608-3622)."""
    for row in rows:
        _draw_row(surface, screen, row, art, row.index in lit)


def _draw_row(surface, screen, row, art, lit):
    layout, style = screen.layout, screen.style
    i = row.slot
    ink = text_colour(art, "selected" if lit else "normal")
    # The portrait, centred in its cell (officer.cpp:640-642).
    sprite = art.portrait(row.rec.pict_num, dark=row.dark) \
        if art is not None and art.available else None
    cell = rect(layout, geom.portrait_cell(i))
    if sprite is not None:
        big = magnified(sprite, layout)
        surface.blit(big, big.get_rect(center=cell.center))
    else:
        screen.style.draw_plate(surface, cell.inflate(-4, -4),
                                layout.scale, BOX_OUTLINE)
    # The name, centred in 160 px from text_x + 22 (:3630-3633).
    ty = geom.text_y(i)
    name_left = point(layout, geom.TEXT_X + geom.NAME_DX, ty)
    name_w = rect(layout, (geom.TEXT_X + geom.NAME_DX, ty,
                           geom.TEXT_X + geom.NAME_DX + geom.NAME_W - 1,
                           ty)).w
    blit_text(surface, style, row.name, name_left[0] + name_w // 2,
              name_left[1], name_w, font_px(layout, "name"), ink, "center")
    _draw_cost(surface, screen, row, ink, ty)
    _draw_status(surface, screen, row, art, ink, i)
    _draw_skills(surface, screen, row, art, ink, i)


def _draw_cost(surface, screen, row, ink, ty):
    """The two cost lines, in the original's two alignments (:3636-3675)."""
    layout, style = screen.layout, screen.style
    size = font_px(layout, "cost")
    right = point(layout, geom.TEXT_X + geom.RIGHT_COLUMN
                  - geom.COST_RIGHT_INSET, ty)
    line_h = style.render_text("0", size, ink).get_height()
    room = rect(layout, (geom.TEXT_X + geom.NAME_DX + geom.NAME_W, ty,
                         geom.TEXT_X + geom.RIGHT_COLUMN, ty)).w
    label = style.render_text(row.cost_label or " ", fit(
        style, row.cost_label or " ", room, size), ink)
    if row.cost_align == "right":
        blit_text(surface, style, row.cost_value, right[0], right[1],
                  room, size, ink, "right")
        if row.cost_label:
            surface.blit(label, (right[0] - label.get_width(),
                                 right[1] + line_h))
        return
    left = right[0] - label.get_width()
    blit_text(surface, style, row.cost_value, left, right[1], room, size, ink)
    if row.cost_label:
        surface.blit(label, (left, right[1] + line_h))


def _draw_status(surface, screen, row, art, ink, i):
    """The line under the portrait and the ETA over it (:3677-3745)."""
    layout, style = screen.layout, screen.style
    cx = point(layout, geom.PORTRAIT_X + geom.PORTRAIT_W // 2, 0)[0]
    y = point(layout, 0, geom.status_y(i))[1]
    fit_w = rect(layout, (0, 0, geom.STATUS_FIT_W - 1, 0)).w
    colour = text_colour(art, "red") if row.status_red else ink
    blit_text(surface, style, row.status, cx, y, fit_w,
              font_px(layout, "status"), colour, "center")
    if row.eta:
        cell = rect(layout, geom.portrait_cell(i))
        drawn = blit_text(surface, style, row.eta, cell.centerx,
                          cell.centery, cell.w, font_px(layout, "status"),
                          text_colour(art, "red"), "center")
        if drawn is not None:
            # Two lines above and two below, in the red pair
            # (officer.cpp:3093-3096).
            red = text_colour(art, "red")
            for dy in (-3, -2):
                pygame.draw.line(surface, red, (drawn.x, drawn.y + dy),
                                 (drawn.right, drawn.y + dy))
            for dy in (0, 1):
                pygame.draw.line(surface, red,
                                 (drawn.x, drawn.bottom + dy),
                                 (drawn.right, drawn.bottom + dy))


def skill_line_rects(screen, row):
    """Each skill line's window rect, top down — the drawing's AND the
    right-click's (decision 5)."""
    layout = screen.layout
    out = []
    for k, y in enumerate(geom.skill_rows(row.slot, len(row.skills))):
        out.append(rect(layout, (geom.TEXT_X, y - 1,
                                 geom.TEXT_X + geom.RIGHT_COLUMN - 1,
                                 y + geom.SKILL_STEP - 2)))
    return out


def _draw_skills(surface, screen, row, art, ink, i):
    """Icon, name, value per displayed skill (:3747-3837)."""
    layout, style = screen.layout, screen.style
    size = font_px(layout, "skill")
    value_right = point(layout, geom.TEXT_X + geom.RIGHT_COLUMN
                        - geom.VALUE_RIGHT_INSET, 0)[0]
    for (sid, name, value), y in zip(row.skills,
                                      geom.skill_rows(i, len(row.skills))):
        icon = art.skill_icon(sid) if art is not None and art.available \
            else None
        icon_at = point(layout, geom.TEXT_X + geom.SKILL_ICON_DX,
                        y + geom.SKILL_ICON_DY)
        if icon is not None:
            surface.blit(magnified(icon, layout), icon_at)
        name_at = point(layout, geom.TEXT_X + geom.SKILL_NAME_DX, y)
        drawn_v = blit_text(surface, style, value, value_right, name_at[1],
                            value_right - name_at[0], size, ink, "right")
        room = (drawn_v.x if drawn_v else value_right) - name_at[0] - 4
        blit_text(surface, style, name, name_at[0], name_at[1], room,
                  size, ink)


# ── Buttons ───────────────────────────────────────────────

#: DEVIATION `button_words`: without the extracted art a button is its
#: rectangle and a word. The words are the art's own, read off
#: OFFICER.LBX 3..13 — the source passes an EMPTY help string to every
#: one (officer.cpp:2858-2908), so there is no string to transcribe.
BUTTON_WORDS = {"tab_colony": "Colony Leaders", "tab_ship": "Ship Officers",
                "hire": "HIRE", "pool": "POOL", "dismiss": "DISMISS",
                "cancel": "CANCEL", "return": "RETURN", "prev": "<",
                "next": ">", "scroll_up": "^", "scroll_down": "v"}


def draw_button(surface, screen, art, name, frame=0, dull=False,
                at=None):
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
    x, y = at or geom.BUTTONS[name][0]
    w, h = geom.BUTTON_SIZE[name]
    r = rect(layout, (x, y, x + w - 1, y + h - 1))
    state = "disabled" if dull else ("active" if frame else "normal")
    hud.small_button(surface, r, layout.scale, state)
    colour = hudtext.colour("button")
    if dull:
        colour = tuple(c // 2 for c in colour)
    blit_text(surface, screen.style, BUTTON_WORDS[name], r.centerx,
              r.y + (r.h - font_px(layout, "button")) // 2, r.w - 4,
              font_px(layout, "button"), colour, "center")
    return r


def draw_strip(surface, screen, native, text, art):
    """A centred one-line strip (`Set_Fitted_Font_Style_` +
    `Print_Centered_`, officer.cpp:725-726, :824-825, :2202)."""
    if not text:
        return
    r = rect(screen.layout, native)
    size = font_px(screen.layout, "strip")
    blit_text(surface, screen.style, text, r.centerx,
              r.y + (r.h - size) // 2, r.w - 6, size,
              text_colour(art, "normal"), "center")
