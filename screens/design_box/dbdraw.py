"""Drawing the Ship Designer's three pickers in the HUD style (decision 71).

Every anchor is the original's offset from the box's base, which the wire
gives (`dbgeom`, `dbwire`); every word the game's own by its id; every
number open fix 45's "DSBX" row as the engine computed it. What is drawn
and where it comes from:

  TRANSCRIPTION  the positions; the headers (HESTRNGS by the original's
                 ids); "No Shield" / "No Computer" / "No Weapon" / "No
                 Special" for row 0; the computer bonus as "+%d" and row
                 0's "0" (`Print_Computer_Data_`); a weapon's name with
                 "(n)" where n is `0 / space`, raised to 1 for a row that
                 fits — the original's kept bug (desbox.cpp:2256-2266), so
                 it reads (1) or (0) and never a real count; the damage
                 string as the engine formatted it; the weapon note
                 (TECHDESC); a row that does not fit dimmed; the lit arc
                 as `Draw_Weapons_Arc_Box_` finds it (the first of
                 Forward Extended, Back Extended, Rear, 360 in its bits,
                 else Forward); the rack words' three frames (chosen,
                 offered, neither)
  ORIGINAL ART   the arc pictures, the arc and rack words and the four
                 filter buttons, DESIGN.LBX's own (`sdart`) — their words
                 exist in no string table (DEVIATION `filter_art`: the
                 filters keep the original's button art among HUD blocks)
  DEVIATION      `hud_frameless` — the boxes are HUD panels, not DESIGN.LBX's
                 box sprites; `button_words` — Cancel / Accept and the
                 scroll arrows in code
  HD EXTENSION   `box_titles` — the title plate; the original paints the
                 headline into its box art, and the shield / computer box
                 wears the special box's ("Select Special System")
  INVENTION      `chosen_fill` — the chosen weapon row lit by a HUD fill
                 where the original draws an arrow sprite, and a
                 modification that is on, where it draws the lit frame
  OMISSION       `no_weapon_damage` — "No Weapon"'s damage "0" is
                 `_weapons[0]`'s, which DSBX does not carry (the writer
                 formats a damage string only for a weapon); `fit_colour`
                 — a special that does not fit is dimmed by the original
                 (desbox.cpp:2825-2846) from its slot's space and the
                 exclusions, neither on the wire: HD draws every special
                 row alike; `flashing_hover`. The right clicks are
                 `dbright` (work order 200)
"""
from core.hud import blocks as hud
from core.hud import text as hudtext
from screens.colony import coldraw
from screens.leaders import ldrdraw as nd
from screens.ship_design import sdart

from . import dbgeom as geom


def _t(surface, screen, words, x, y, w, key="value", role="value",
       align="left"):
    """`x` is the anchor the original prints at; right / centre alignment
    are anchored there (`ldrdraw.blit_text`), as its `Print_Right_` /
    `Print_Centered_` are; `w` is the width a word is fitted to."""
    return coldraw.text(surface, screen, words, x, y, w, key, role,
                        align=align)


def _rect(f):
    return (f.x, f.y, f.x_end, f.y_end)


def draw(surface, screen, box, names):
    layout = screen.layout
    r = nd.draw_box(surface, screen, _rect(box.base))
    hud.title_plate(surface, r.centerx, r.top, layout.scale,
                    screen.word(f"box_{box.kind}"),
                    style_renderer=screen.style)
    {"generic": _generic, "weapon": _weapon,
     "special": _special}[box.kind](surface, screen, box, names)
    _buttons(surface, screen, box)


def _generic(surface, screen, box, names):
    bx, by = box.origin
    x0 = bx + geom.GENERIC_X
    shield = box.box["replacement_type"] == geom.REPLACEMENT_SHIELD
    cols = geom.SHIELD_COLS if shield else geom.COMPUTER_COLS
    heads = [_t(surface, screen, names.h(sid), x0 + dx,
                by + geom.GENERIC_HEAD_Y, 0xC0, "value", "label")
             for sid, dx in cols]
    size = coldraw.font(screen.layout, "value")
    for y, row, _field in box.rows():
        item = row["item"]
        if shield:
            name = names.part("shields", item) if item else \
                names.h(geom.NO_SHIELD)
            values = (str(row["cost"]), str(row["space"]))
        else:
            name = names.part("computers", item) if item else \
                names.h(geom.NO_COMPUTER)
            values = (f"+{row['extra']}" if item else "0", str(row["cost"]))
        _t(surface, screen, name, x0 + cols[0][1], y, 0xD0)
        # Centred under the column's header, as `Print_Integer_Centered_`
        # centres on the header's width (less the shield table's swapped
        # widths, desbox.cpp:2387/2398 — DEVIATION `centring_swap`).
        wy = nd.point(screen.layout, 0, y)[1]
        for head, value in zip(heads[1:], values):
            if head is not None:
                nd.blit_text(surface, screen.style, value, head.centerx, wy,
                             head.w * 2, size, hudtext.colour("value"),
                             align="center")


def _weapon(surface, screen, box, names):
    bx, by = box.origin
    x0 = bx + geom.WEAPON_X
    rows = box.rows()
    art = sdart.load()
    if rows:
        head_y = rows[0][0] - geom.WEAPON_ROW_DY + geom.WEAPON_HEAD_DY
        for sid, dx, align in geom.WEAPON_HEADS:
            w = 0x50
            _t(surface, screen, names.h(sid), x0 + dx, head_y, w, "value",
               "label", align)
    chosen = box.box["chosen"]
    first = max(0, box.box["first_row"])
    cols = geom.WEAPON_COLS
    for k, (y, row, field) in enumerate(rows):
        weapon = row["extra"]
        role = "value" if row["unlocked"] or weapon <= 0 else "sub"
        if first + k == chosen and chosen > 0:
            hud.panel(surface, nd.rect(screen.layout, _rect(field)),
                      screen.layout.scale, lit=True, dense=True)
        if weapon <= 0:
            name = names.h(geom.NO_WEAPON)
        else:
            n = 1 if row["space"] > 0 and row["unlocked"] else 0
            name = f"{names.part('weapons', weapon) or ''} ({n})"
        _t(surface, screen, name, x0 + cols["name"], y, 0xA8, role=role)
        _t(surface, screen, row["text"], x0 + cols["damage"], y, 0x30,
           role=role, align="right")
        for col in ("cost", "space"):
            _t(surface, screen, str(row[col]), x0 + cols[col], y, 0x20,
               role=role, align="right")
        if weapon > 0:
            _t(surface, screen, names.weapon_note(weapon),
               x0 + cols["note"], y, 0x120, "line", "sub")
    _arc_box(surface, screen, box, art)
    _mods(surface, screen, box, names)
    for i, (f, status) in enumerate(zip(box.filter_fields(),
                                        box.box["filters"])):
        if f is not None:
            _sprite(surface, screen, art.label("filter", i, status),
                    (f.x, f.y))


def _sprite(surface, screen, sprite, native_xy):
    if sprite is None:
        return
    x, y = nd.point(screen.layout, *native_xy)
    surface.blit(nd.magnified(sprite, screen.layout), (x, y))


def _arc_box(surface, screen, box, art):
    field = box.arc_box_field()
    if field is None:
        return
    bx = box.base.x
    b = field.y - geom.ARC_BOX_DY
    nd.draw_box(surface, screen, _rect(field))
    racks = box.rack_fields()
    if racks:
        _sprite(surface, screen, art.arc(4),
                (bx + geom.ARC_PICT[0], b + geom.ARC_PICT[1]))
        for i in range(5):
            frame = 2 if box.box["rack"] == i else 1 if i < len(racks) else 0
            _sprite(surface, screen, art.label("rack", i, frame),
                    (bx + geom.RACK_TEXT[0],
                     b + geom.RACK_TEXT[1] + i * geom.RACK_STEP))
        return
    lit = lit_arc(box.box["arcs"])
    _sprite(surface, screen, art.arc(lit),
            (bx + geom.ARC_PICT[0], b + geom.ARC_PICT[1]))
    for i in range(5):
        _sprite(surface, screen, art.label("arc", i, 1 if i == lit else 0),
                (bx + geom.ARC_TEXT[0],
                 b + geom.ARC_TEXT[1] + i * geom.ARC_STEP))


def lit_arc(arcs):
    """`Draw_Weapons_Arc_Box_`'s choice (desbox.cpp:1140-1152)."""
    for i in (1, 2, 3, 4):
        if arcs & geom.ARC_BITS[i]:
            return i
    return 0


def _mods(surface, screen, box, names):
    field = box.arc_box_field()
    if field is None:
        return
    bx = box.base.x
    b = field.y - geom.ARC_BOX_DY
    x1, y1, x2, y2 = geom.MOD_BOX
    nd.draw_box(surface, screen, (bx + x1, b + y1, bx + x2, b + y2))
    for i, f, on in box.mods():
        if on:
            # A modification switched on: lit like the chosen row (the
            # original draws its word in the lit frame, frame 2).
            hud.panel(surface, nd.rect(screen.layout, _rect(f)),
                      screen.layout.scale, lit=True, dense=True)
        _t(surface, screen, names.part("weapon_mods", i), f.x, f.y,
           f.x_end - f.x, "value", "title" if on else "value")


def _special(surface, screen, box, names):
    bx, by = box.origin
    for sid, dx in geom.SPECIAL_HEADS:
        _t(surface, screen, names.h(sid), bx + dx, by + geom.SPECIAL_HEAD_DY,
           0x70, "value", "label")
    cols = geom.SPECIAL_COLS
    for y, row, _field in box.rows():
        item = row["item"]
        name = names.part("specials", item) if item else \
            names.h(geom.NO_SPECIAL)
        _t(surface, screen, name, bx + cols["name"], y, 0xA0)
        for col in ("space", "cost"):
            _t(surface, screen, str(row[col]), bx + cols[col], y, 0x28,
               align="right")
        if item:
            _t(surface, screen, names.description(item),
               bx + cols["description"], y, 0x130, "line", "sub")


def _buttons(surface, screen, box):
    for key, f in (("cancel", box.cancel), ("accept", box.accept())):
        if f is None:
            continue
        r = nd.rect(screen.layout, _rect(f))
        state = "disabled" if f.field_type != geom.TYPE_BUTTON else \
            screen.button_state(key, r)
        hud.slant_button(surface, r, screen.layout.scale, state,
                         screen.word(key), style_renderer=screen.style)
    for f in box.scroll_buttons():
        r = nd.rect(screen.layout, _rect(f))
        word = chr(f.hotkey) if 32 < f.hotkey < 127 else ""
        hud.small_button(surface, r, screen.layout.scale,
                         screen.button_state(f"scroll{f.index}", r), word,
                         style_renderer=screen.style)
