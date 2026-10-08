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
  DEVIATION      `button_words`, `hd_font` — the Leaders and Races rules
  OMISSION       `description`, `product_picture`, `design_stats`,
                 `delete_hint` — the HELP.LBX description, the product's
                 picture, a design's nine stat lines, and the "delete %s"
                 the original prints over its own pointer's queue row
"""
from core.hestrings import printf
from core.hud import blocks as hud
from core.hud import hover as hud_hover
from core.hud import text as hudtext
from screens.colony.coldraw import text
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
    for box in (w.BUILDINGS_BOX, w.PICTURE_BOX, w.SUMMARY_BOX, w.OTHERS_BOX,
                w.DESCRIPTION_BOX, w.QUEUE_BOX):
        nd.draw_box(surface, screen, box)
    _lists(surface, screen, view, state, names)
    _queue(surface, screen, view, state, names)
    _summary(surface, screen, view, state, names, hover)
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


def _lists(surface, screen, view, state, names):
    dim = hudtext.colour("sub")
    for entries, rows, x, width, building in (
            (view.buildings, view.building_rows, 13, 171, True),
            (view.others, view.other_rows, 485, 138, False)):
        for e, f in zip(entries, rows):
            if e["id"] == w.SEPARATOR:
                continue
            bright = view.queued(e["id"]) if building else \
                not design_needs_base(view, state, e["id"])
            name, _st = names.product(e["id"], state)
            text(surface, screen, name, x, f.y + 1, width, "value",
                 "value", colour=None if bright else dim)


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
        hud.slant_button(surface, r, screen.layout.scale,
                         hud_hover.pointer_state(r, "normal"),
                         screen.word(key), style_renderer=screen.style)
