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
  HD EXTENSION   `designer_pictures` — the four filter buttons and the arc
                 dial from the mod folder (`dbpics`), the original's art
                 without them (Data, 2 November 2026)
  HD EXTENSION   `picker_words` — the arc and rack words beside the dial in
                 the HUD font (their text in `layout.json`, German in
                 `de.json`), where the original draws DESIGN.LBX's pictures
                 of them (Data, 2 November 2026)
  HD EXTENSION   `picker_rows` — one text size for every word of a table
                 row (the notes were smaller than the names), each centred
                 between its row's edges, the chosen row's frame as wide as
                 the table's words and the two lower boxes ending on one line
                 (Data, 21 November 2026)
  HD EXTENSION   `solid_panel` — the picker's box is opaque: the designer's
                 page under it showed through the glass (Data, 2 November
                 2026)
  HD EXTENSION   `picker_mockup` — the special picker's faint row rules,
                 hover bar and scroll track in the frame colour (`dbmock`,
                 Data's mockup, 25 November 2026)
  INVENTION      `chosen_fill` — the chosen weapon row lit by a HUD fill
                 where the original draws an arrow sprite, and a
                 modification that is on, where it draws the lit frame
  TRANSCRIPTION  `fit_colour` — a special that does not fit the hull, or
                 that a special in the design excludes, is dim as in the
                 original (desbox.cpp:2800-2835; the space of the replaced
                 special read from its own row, UNVERIFIED
                 `fit_replaced_space`; the exclusions from techdata.cpp's
                 table, `dbfit`); the dim colour is 55 % of the row's own,
                 HD EXTENSION `fit_dim`: the original's dull palette index
                 has no RGB value
  OMISSION       `no_weapon_damage` — "No Weapon"'s damage "0" is
                 `_weapons[0]`'s, which DSBX does not carry (the writer
                 formats a damage string only for a weapon);
                 `flashing_hover`: the cycling colour of a hovered row (a
                 still bar stands in for it). The right clicks are
                 `dbright` (work order 200)
"""
from core.hud import blocks as hud
from core.hud import hover as hud_hover
from core.hud import text as hudtext
from screens.colony import coldraw
from core import nativedraw as nd
from screens.ship_design import sdart

from . import dbfit, dbmock, dbpics, dbgeom as geom


def _t(surface, screen, words, x, y, w, key="value", role="value",
       align="left"):
    """`x` is the anchor the original prints at; right / centre alignment
    are anchored there (`nativedraw.blit_text`), as its `Print_Right_` /
    `Print_Centered_` are; `w` is the width a word is fitted to."""
    return coldraw.text(surface, screen, words, x, y, w, key, role,
                        align=align)


def _rect(f):
    return (f.x, f.y, f.x_end, f.y_end)


def _row_h(screen, field):
    """A row's height in window px: its field's, else the original's 14."""
    if field is not None:
        return nd.rect(screen.layout, _rect(field)).h
    return int(round(geom.WEAPON_STEP * nd.native_scale(screen.layout)))


def _row(surface, screen, words, x, y, w, role="value", align="left",
         row_h=0):
    """One line of a table row at a native anchor, ONE SIZE for every row
    word (Data, 21 November 2026: the notes were smaller than the names and
    the words sat on the top edge of their row, under the chosen row's
    frame), centred between the row's top and bottom (HD EXTENSION
    `picker_rows`). `x` is the anchor, `w` the native width the word is
    fitted to, as `_t`'s."""
    if not words:
        return None
    layout = screen.layout
    size = coldraw.font(layout, "value")
    px, py = nd.point(layout, x, y)
    x0 = x - (w if align == "right" else w // 2 if align == "center" else 0)
    wpx = nd.rect(layout, (x0, y, x0 + w - 1, y)).w
    colour = tuple(role) if isinstance(role, tuple) else \
        hudtext.colour(role)
    h = screen.style.render_text("Wg", size, colour[:3]).get_height()
    return nd.blit_text(surface, screen.style, words, px,
                        py + max(0, (row_h - h) // 2), wpx, size, colour,
                        align=align)


def draw(surface, screen, box, names):
    layout = screen.layout
    # HD EXTENSION `solid_panel` (Data, 2 November 2026): the picker's box
    # is opaque — the designer's page under it showed through the glass
    r = nd.rect(layout, _rect(box.base))
    hud.panel(surface, r, layout.scale, solid=True)
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
    # THE CHOSEN ROW'S FRAME ends where the table's words end (the widest
    # note drawn), not at the row field's far edge
    size = coldraw.font(screen.layout, "value")
    note_end = 0
    for y, row, field in rows:
        if row["extra"] > 0:
            note = names.weapon_note(row["extra"])
            if note:
                nx, ny = nd.point(screen.layout, x0 + cols["note"], y)
                wpx = nd.rect(screen.layout, (x0 + cols["note"], y,
                                              x0 + cols["note"] + 0x11F,
                                              y)).w
                fitted = nd.fit(screen.style, note, wpx, size)
                note_end = max(note_end, nx + screen.style.render_text(
                    note, fitted, (255, 255, 255)).get_width())
    for k, (y, row, field) in enumerate(rows):
        weapon = row["extra"]
        role = "value" if row["unlocked"] or weapon <= 0 else "sub"
        rh = _row_h(screen, field)
        if first + k == chosen and chosen > 0 and field is not None:
            fr = nd.rect(screen.layout, _rect(field))
            pad = max(4, fr.h // 4)
            if note_end:
                fr.w = max(8, min(fr.w, note_end + pad - fr.x))
            hud.panel(surface, fr, screen.layout.scale, lit=True, dense=True)
        if weapon <= 0:
            name = names.h(geom.NO_WEAPON)
        else:
            n = 1 if row["space"] > 0 and row["unlocked"] else 0
            name = f"{names.part('weapons', weapon) or ''} ({n})"
        _row(surface, screen, name, x0 + cols["name"], y, 0xA8, role,
             row_h=rh)
        _row(surface, screen, row["text"], x0 + cols["damage"], y, 0x30,
             role, "right", rh)
        for col in ("cost", "space"):
            _row(surface, screen, str(row[col]), x0 + cols[col], y, 0x20,
                 role, "right", rh)
        if weapon > 0:
            _row(surface, screen, names.weapon_note(weapon),
                 x0 + cols["note"], y, 0x120, "sub", row_h=rh)
    _arc_box(surface, screen, box, art)
    _mods(surface, screen, box, names)
    for i, (f, status) in enumerate(zip(box.filter_fields(),
                                        box.box["filters"])):
        if f is None:
            continue
        # HD EXTENSION `designer_pictures`: the mod folder's button where
        # it has one, in the footprint of the original's own sprite
        sprite = art.label("filter", i, status)
        w = sprite.get_width() if sprite is not None else f.x_end - f.x
        if not dbpics.draw_filter(surface, screen.app.res, nd.rect(
                screen.layout, (f.x, f.y, f.x + w, f.y + 24)), i,
                status >= 1):
            _sprite(surface, screen, sprite, (f.x, f.y))


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
    ax, ay = bx + geom.ARC_PICT[0], b + geom.ARC_PICT[1]
    if racks:
        _dial(surface, screen, art, 4, ax, ay)
        for i in range(5):
            frame = 2 if box.box["rack"] == i else 1 if i < len(racks) else 0
            _pick_word(surface, screen, f"rack_{i}", frame,
                       bx + geom.RACK_TEXT[0],
                       b + geom.RACK_TEXT[1] + i * geom.RACK_STEP)
        return
    lit = lit_arc(box.box["arcs"])
    _dial(surface, screen, art, lit, ax, ay)
    for i in range(5):
        _pick_word(surface, screen, f"arc_{i}", 1 if i == lit else 0,
                   bx + geom.ARC_TEXT[0],
                   b + geom.ARC_TEXT[1] + i * geom.ARC_STEP)


def _pick_word(surface, screen, key, frame, native_x, native_y):
    """An arc or rack word in OrionLayer's own font where the original
    prints DESIGN.LBX's picture of it (HD EXTENSION `picker_words`): the
    chosen one lit, an offered one plain, one not offered dim — the
    original's three frames (2, 1, 0)."""
    _t(surface, screen, screen.word(key), native_x, native_y, 0x60, "value",
       {2: "title", 1: "value", 0: "sub"}[frame] if key.startswith("rack_")
       else "title" if frame else "value")


def _dial(surface, screen, art, arc, native_x, native_y):
    """The arc dial: the mod folder's compass lit for `arc` where it has
    one (HD EXTENSION `designer_pictures`), else the original's picture."""
    sprite = art.arc(arc)
    w, h = sprite.get_size() if sprite is not None else (83, 89)
    if not dbpics.draw_compass(surface, screen.app.res, nd.rect(
            screen.layout, (native_x, native_y, native_x + w,
                            native_y + h)), arc):
        _sprite(surface, screen, sprite, (native_x, native_y))


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
    # the two lower boxes end on one line: the arc box's own bottom (the
    # modification box was 3 px longer, `MOD_BOX`'s extent of the sprite)
    y2 = min(y2, field.y_end - b) if field.y_end > b + y1 else y2
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
    rows = box.box["rows"]
    slot = box.box["slot"]
    for y, row, _field in box.rows():
        item = row["item"]
        name = names.part("specials", item) if item else \
            names.h(geom.NO_SPECIAL)
        rh = _row_h(screen, _field)
        # TRANSCRIPTION `fit_colour` (desbox.cpp:2800-2835): a row that does
        # not fit, or that a special in the design excludes, is dim
        fit = dbfit.fits(row, rows, box.design, slot)
        # the original's dull colour (`Font_Colors2(2, 'U', 'W')`) as 55 %
        # of the row's own
        role = "value" if fit else tuple(
            int(c * 0.55) for c in hudtext.colour("value")[:3])
        if _field is not None:
            fr = nd.rect(screen.layout, _rect(_field))
            if fit and dbmock.hovered(fr):
                dbmock.hover_bar(surface, fr.inflate(-2, -2))
            dbmock.row_rule(surface, fr)
        _row(surface, screen, name, bx + cols["name"], y, 0xA0, role,
             row_h=rh)
        for col in ("space", "cost"):
            _row(surface, screen, str(row[col]), bx + cols[col], y, 0x28,
                 role, align="right", row_h=rh)
        if item:
            _row(surface, screen, names.description(item),
                 bx + cols["description"], y, 0x130,
                 "sub" if fit else role, row_h=rh)
    dbmock.track(surface, screen, box.scroll_buttons(),
                 max(0, box.box["first_row"]), 10, len(rows))


def _buttons(surface, screen, box):
    for key, f in (("cancel", box.cancel), ("accept", box.accept())):
        if f is None:
            continue
        r = nd.rect(screen.layout, _rect(f))
        state = "disabled" if f.field_type != geom.TYPE_BUTTON else \
            hud_hover.pointer_state(r)
        hud.slant_button(surface, r, screen.layout.scale, state,
                         screen.word(key), style_renderer=screen.style)
    for f in box.scroll_buttons():
        r = nd.rect(screen.layout, _rect(f))
        word = chr(f.hotkey) if 32 < f.hotkey < 127 else ""
        hud.small_button(surface, r, screen.layout.scale,
                         hud_hover.pointer_state(r), word,
                         style_renderer=screen.style)
