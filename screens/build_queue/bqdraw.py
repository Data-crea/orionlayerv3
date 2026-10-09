"""Drawing the build popup in the HUD style (decision 71).

Every text at the HD image of the position the original prints it at
(`bqwire`), the windows as the HUD's glass panels, the buttons as HUD
buttons. Marks — each in `layout.json` `marks`, the status document and
check 090q:

  TRANSCRIPTION  the lists in the game's order, a building row bright
                 while queued and dim otherwise (colbldg.cpp:665-692), the
                 seven queue rows, the title, the summary's lines and their
                 numbers (BLDL: the engine's own `Draw_Cost_And_Time_Info_`
                 values)
  DEVIATION      `ship_row_dim` — narrowed by work order 208 B8: a design
                 LARGE or bigger is dimmed without a star base, star
                 fortress or battlestation, as the original does
                 (:625-633); what `Colony_Can_Build_Product_` and
                 `Auto_Design_Type_` dim (:637-652) is not copied
  TRANSCRIPTION  the selected product's picture in the grid room and its
                 information in the large box (work order 226 D, Data's
                 decision 3; `bqproduct`, `screens/colony/colroom`)
  DEVIATION      `button_words`, `hd_font` — the Leaders and Races rules
  DEVIATION      `one_edge` (work order 226 D): a list column is its shell
                 panel — the original's inner box round the list is not
                 drawn again inside it — and the picture, summary and
                 description boxes are cells of the middle panel (the
                 shell's field), not panels in a panel; the lists' words
                 stand at the shell's inset from the panel's inner line
  OMISSION       `delete_hint` — the "delete %s" the original prints over
                 its own pointer's queue row
  TRANSCRIPTION  the two modes (work order 228, Data's decision 3): while
                 DESIGN's mode is on every design row is bright and the
                 design under the pointer blinks (colbldg.cpp:632-640), and
                 the button that set a mode (DESIGN, REPEAT BUILD) is
                 "selected" (decision 92) until the mode ends
  OMISSION       `mode_pointer` — the original's mode shows as its pointer
                 picture (17 for DESIGN, 16 for REPEAT, colbldg.cpp:21-22);
                 HD has one pointer drawing (`core/cursor.py`)
"""
from core import prodname
from core.hestrings import printf
from core.hud import blocks as hud
from core.hud import hover as hud_hover
from core.hud import text as hudtext
from screens.colony.coldraw import font, text
from screens.leaders import ldrdraw as nd

from . import bqwire as w

E_TITLE, E_COST, E_MAINT, E_TIME, E_TURNS = 210, 242, 367, 211, 544


def draw(surface, screen, view, state, names, hover):
    # The shell's three panels (work order 225), then the original's boxes
    # inside them. The title stands on the plate now (`screen._title`).
    for name in ("left_panel", "middle_panel", "right_panel"):
        r = screen.box_screen_rect(name)
        if r is not None:
            hud.panel(surface, r, screen.ref_layout.scale)
    # ONE EDGE PER GROUP (DEVIATION `one_edge`): the two lists are their
    # panels; the middle panel's boxes are its cells. The queue's rows are
    # fields of their own (`_queue`).
    for box in (w.PICTURE_BOX, w.SUMMARY_BOX, w.DESCRIPTION_BOX):
        hud.field(surface, nd.rect(screen.layout, box), screen.layout.scale)
    product = hover if hover is not None else view.items[0]
    _picture(surface, screen, view, state, names, product)
    _lists(surface, screen, view, state, names, hover)
    _queue(surface, screen, view, state, names)
    _summary(surface, screen, view, state, names, hover)
    _description(surface, screen, view, state, product)
    _buttons(surface, screen, state, view)


def _title(surface, screen, view, names):
    fmt = screen.e(E_TITLE)
    name = names.planet_name(view.colony)
    if fmt:
        x, y, width, h = w.TITLE
        # `printf`, never `%`: a template without the `%s` (a mod's, a
        # language's) must not raise in a render (decision 37; work order
        # 182 found it with the committed stand-in strings).
        text(surface, screen, printf(fmt, name), x + width // 2, y, width,
             "value", "title", align="center")


#: `BUILDING_STAR_BASE`, `_STAR_FORTRESS`, `_BATTLESTATION`
#: (orion2_consts.h:21, :53-54) and `SHIP_SIZE_LARGE` (:512).
BASES, SHIP_SIZE_LARGE = (40, 41, 8), 2


def design_needs_base(view, state, product):
    """TRANSCRIBED (work order 208 B8): a design row is dimmed when the
    colony has no star base, star fortress or battlestation and the design
    is LARGE or bigger (colbldg.cpp:625-633). Not transcribed:
    `Colony_Can_Build_Product_` (:637-640) and the special ships' dimming by
    `Auto_Design_Type_` (:642-652) — DEVIATION `ship_row_dim`, narrowed."""
    from core import prodname
    from core.structs import player as player_struct
    if prodname.kind(product) != prodname.KIND_SHIP_DESIGN or \
            getattr(view, "colony", None) is None:
        return False
    raws = getattr(state, "player_raw", None) or []
    me = getattr(state, "player_num", 0) or 0
    if not 0 <= me < len(raws):
        return False
    size = player_struct.design_size(player_struct.parse(raws[me]),
                                     prodname.SHIP_DESIGN_BASE - product)
    built = list(view.colony.buildings)
    has_base = any(0 <= b < len(built) and built[b] for b in BASES)
    return size is not None and size >= SHIP_SIZE_LARGE and not has_base


def design_blinks_dim(ticks):
    """`ERIC::Global_Cycler_(30, 2)` (eric.cpp:98-102): the half of the
    blink in which DESIGN's mode draws the design under the pointer dim
    (colbldg.cpp:634-636) — every other 30 ms of the clock."""
    return (int(ticks) // 30) % 2 != 0


def row_bright(view, state, product, building, hover, ticks):
    """Whether a list row is drawn bright. A building row while queued
    (colbldg.cpp:675-680). A ship row unless a design needs a base
    (`design_needs_base`); while DESIGN's mode is on (`_field_mode` 1)
    nothing is dimmed by that rule, and the design under the pointer
    blinks (colbldg.cpp:625-640)."""
    if building:
        return view.queued(product)
    if getattr(view, "field_mode", w.MODE_NONE) == w.MODE_DESIGN:
        return not (product == hover and
                    prodname.kind(product) == prodname.KIND_SHIP_DESIGN and
                    design_blinks_dim(ticks))
    return not design_needs_base(view, state, product)


def _lists(surface, screen, view, state, names, hover=None):
    """The two lists, each word at the shell's inset from its panel's inner
    line (DEVIATION `one_edge`: the original's x 13 and 485 are its boxes'
    own edges, which in the shell ARE the panel's inner line)."""
    import pygame
    from core.hud import shell
    dim = hudtext.colour("sub")
    ticks = pygame.time.get_ticks()
    pad = shell.inset(screen.ref_layout)
    for entries, rows, x, width, building, panel in (
            (view.buildings, view.building_rows, 13, 171, True, "left_panel"),
            (view.others, view.other_rows, 485, 138, False, "right_panel")):
        r = screen.box_screen_rect(panel)
        inner = shell.inner(r, screen.ref_layout) if r is not None else None
        for e, f in zip(entries, rows):
            if e["id"] == w.SEPARATOR:
                continue
            bright = row_bright(view, state, e["id"], building, hover,
                                ticks)
            name, _st = names.product(e["id"], state)
            px, py = nd.point(screen.layout, x, f.y + 1)
            pw = nd.rect(screen.layout, (0, 0, width, 1)).w
            if inner is not None:
                px = max(px, inner.x + pad)
                pw = min(pw, inner.right - pad - px)
            nd.blit_text(surface, screen.style, name, px, py, pw,
                         font(screen.layout, "value"),
                         hudtext.colour("value") if bright else dim)


def _world(view, state):
    """(climate, ground type, race) the popup's pictures are drawn in."""
    from core.structs import planet as planet_struct
    from core.structs import player as player_struct
    col = view.colony
    pls = getattr(state, "planets_raw", None) or []
    bg = planet_struct.parse(pls[col.planet]).climate_bg_type \
        if 0 <= col.planet < len(pls) else 0
    raws = getattr(state, "player_raw", None) or []
    me = getattr(state, "player_num", 0) or 0
    race = player_struct.parse(raws[me]).race if 0 <= me < len(raws) else 0
    return int(col.climate), int(bg), int(race)


def _ship_parts(view, state, product):
    """(design picture, queued ship view) for a ship product, else Nones."""
    from core.structs import player as player_struct
    from core.structs import ship as ship_struct
    from screens.refit import refwords
    kind = prodname.kind(product)
    raws = getattr(state, "player_raw", None) or []
    me = getattr(state, "player_num", 0) or 0
    if kind == prodname.KIND_SHIP_DESIGN and 0 <= me < len(raws):
        d = refwords.design_view(player_struct.parse(raws[me]),
                                 prodname.SHIP_DESIGN_BASE - product)
        return d.picture_num, d
    if kind == prodname.KIND_QUEUED_SHIP:
        ships = getattr(state, "ships_raw", None) or []
        i = prodname.QUEUED_SHIP_BASE - product
        if 0 <= i < len(ships):
            return None, ship_struct.parse(ships[i])
    return None, None


def _picture(surface, screen, view, state, names, product):
    """The picture box: the grid room with the product in it, at a whole
    step (`colroom`), or the word the original centres there."""
    from screens.colony import colroom
    from . import bqproduct
    if product in (w.NONE, w.SEPARATOR, None):
        return
    box = nd.rect(screen.layout, w.PICTURE_BOX)
    inner = box.inflate(-2, -2)
    climate, bg, race = _world(view, state)
    pic, ship = _ship_parts(view, state, product)
    spec = bqproduct.picture(product, race, pic, ship)
    colroom.draw(surface, inner, spec or ("room",), climate, bg)
    if spec is None:
        word = (screen.e(bqproduct.WORD_IN_BOX[product])
                if product in bqproduct.WORD_IN_BOX
                else names.product(product, state)[0])
        cx, cy = nd.point(screen.layout, *colroom.CENTRE)
        nd.blit_text(surface, screen.style, word, cx, cy, inner.w,
                     font(screen.layout, "value"), hudtext.colour("value"),
                     align="center")


def _description(surface, screen, view, state, product):
    """The large box: the product's help record or setting description,
    or a design's paragraph, wrapped to the box in the shell's text."""
    from core import helpformat
    from core.hud import shell
    from core.textfit import wrap_text
    from . import bqproduct
    if product in (w.NONE, w.SEPARATOR, None):
        return
    box = nd.rect(screen.layout, w.DESCRIPTION_BOX)
    inner = box.inflate(-2 * shell.inset(screen.ref_layout),
                        -2 * shell.inset(screen.ref_layout))
    size = font(screen.layout, "value")
    pitch = int(size * 1.25)
    lines = []
    _pic, ship = _ship_parts(view, state, product)
    if ship is not None:
        from screens.refit import refwords
        for row in refwords.design_lines(ship, screen.e, screen.parts()):
            lines.append("  ".join(str(v) for v in row if v))
    else:
        got = bqproduct.text(product, getattr(screen, "helptext", None),
                             screen.maintext())
        if got is not None:
            for ln in helpformat.parse(got[1] or ""):
                lines.extend(wrap_text(screen.style, ln.plain(), size,
                                       inner.w) or [""])
    y = inner.y
    for ln in lines:
        if y + pitch > inner.bottom:
            break
        nd.blit_text(surface, screen.style, ln, inner.x, y, inner.w, size,
                     hudtext.colour("value"))
        y += pitch


#: The queue's rows as the game lays its fields out (colbldg.cpp, the
#: seven type-7 fields at 207, 329 + 20 i — (458, 350 + 20 i), read off the
#: live list in work order 223): one row's field where the list has none.
QUEUE_ROW = (207, 329, 458, 350)


def queue_row(view, i):
    """Row i's native rect: the live field's, else the game's pattern;
    one px short at top and bottom, so the rows stand apart (the fields
    overlap by a px)."""
    if i < len(view.queue):
        f = view.queue[i]
        x0, y0, x1, y1 = f.x, f.y, f.x_end, f.y_end
    else:
        x0, y0, x1, y1 = QUEUE_ROW
        y0, y1 = y0 + i * w.QUEUE_PITCH, y1 + i * w.QUEUE_PITCH
    return (x0, y0 + 1, x1, y1 - 1)


def _queue(surface, screen, view, state, names):
    """The seven queue rows — the original's striped rows — as the shared
    field (work order 223), the row being edited 'on'."""
    active = view.active_queue_row()
    items = list(view.items[:7]) + [w.NONE] * (7 - len(view.items[:7]))
    for i, product in enumerate(items):
        hud.field(surface, nd.rect(screen.layout, queue_row(view, i)),
                  screen.layout.scale,
                  on=(i == active and i < len(view.queue)))
        name, _st = names.product(product, state) if product != w.NONE \
            else ("", "ok")
        y = w.QUEUE_TEXT_Y + i * w.QUEUE_PITCH
        text(surface, screen, name, w.QUEUE_TEXT_X, y, w.QUEUE_W, "value",
             "value", align="center")


def _summary(surface, screen, view, state, names, hover):
    """`Draw_Current_Selection_` (colbldg.cpp:822-986): the item under HD's
    pointer, else the queue's first; its name, then the numbers."""
    product = hover if hover is not None else view.items[0]
    if product in (w.NONE, w.SEPARATOR, None):
        return
    name, _st = names.product(product, state)
    text(surface, screen, name, w.SUMMARY_X, w.SUMMARY_Y, w.SUMMARY_W,
         "value", "title")
    e = view.entry(product)
    if e is None:
        return
    lines = [(E_COST, e["cost"])]
    if e["maintenance"] >= 0:
        lines.append((E_MAINT, e["maintenance"]))
    lines.append((E_TIME, e["time"]))
    turns = screen.turns_left(state, view, product)
    if turns is not None:
        lines.append((E_TURNS, turns))
    for n, (eid, value) in enumerate(lines, start=2):
        fmt = screen.e(eid)
        if fmt:
            text(surface, screen, printf(fmt, value), w.SUMMARY_X,
                 w.SUMMARY_Y + n * w.SUMMARY_PITCH, w.SUMMARY_W, "line",
                 "label")


#: The buttons that set a mode, and the `field_mode` each sets.
MODE_BUTTONS = {"design": w.MODE_DESIGN, "repeat": w.MODE_REPEAT}


def _buttons(surface, screen, state, view):
    fields = getattr(state, "fields", None)
    for key, ident in (("cancel", w.CANCEL), ("ok", w.OK),
                       ("refit", w.REFIT), ("design", w.DESIGN),
                       ("repeat", w.REPEAT), ("auto", w.AUTO_BUILD)):
        f = w.live_field(fields, ident)
        if f is None:
            continue
        r = nd.rect(screen.layout, (f.x, f.y, f.x_end, f.y_end))
        if key == "auto":
            # A TOGGLE inside a panel: rectangular, "selected" while on
            # (work order 225, decisions 88 and 92).
            lit = view.auto_building != 0
            hud.small_button(surface, r, screen.layout.scale,
                             hud_hover.pointer_state(
                                 r, "active" if lit else "normal"),
                             screen.word(key).upper(),
                             style_renderer=screen.style)
            continue
        # A mode's button is "selected" while its mode is on (work order
        # 228, Data's decision 3; decision 92) — the original shows the
        # mode by its pointer picture only (OMISSION `mode_pointer`).
        on = key in MODE_BUTTONS and \
            MODE_BUTTONS[key] == getattr(view, "field_mode", w.MODE_NONE)
        hud.slant_button(surface, r, screen.layout.scale,
                         hud_hover.pointer_state(r,
                                                 "active" if on else "normal"),
                         screen.word(key), style_renderer=screen.style)
