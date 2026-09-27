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
  DEVIATION      `ship_row_dim` — a ship row is never dimmed: the original
                 dims by `Colony_Can_Build_Product_` and the design's size
                 against the colony's bases (:625-653), a rule this screen
                 does not copy
  DEVIATION      `button_words`, `hd_font` — the Leaders and Races rules
  OMISSION       `description`, `product_picture`, `design_stats`,
                 `delete_hint` — the HELP.LBX description, the product's
                 picture, a design's nine stat lines, and the "delete %s"
                 the original prints over its own pointer's queue row
"""
from core.hestrings import printf
from core.hud import blocks as hud
from core.hud import text as hudtext
from screens.colony.coldraw import text
from screens.leaders import ldrdraw as nd

from . import bqwire as w

E_TITLE, E_COST, E_MAINT, E_TIME, E_TURNS = 210, 242, 367, 211, 544


def draw(surface, screen, view, state, names, hover):
    for box in (w.BUILDINGS_BOX, w.PICTURE_BOX, w.SUMMARY_BOX, w.OTHERS_BOX,
                w.DESCRIPTION_BOX, w.QUEUE_BOX):
        nd.draw_box(surface, screen, box)
    _title(surface, screen, view, names)
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


def _lists(surface, screen, view, state, names):
    dim = hudtext.colour("sub")
    for entries, rows, x, width, building in (
            (view.buildings, view.building_rows, 13, 171, True),
            (view.others, view.other_rows, 485, 138, False)):
        for e, f in zip(entries, rows):
            if e["id"] == w.SEPARATOR:
                continue
            bright = view.queued(e["id"]) if building else True
            name, _st = names.product(e["id"], state)
            text(surface, screen, name, x, f.y + 1, width, "value",
                 "value", colour=None if bright else dim)


def _queue(surface, screen, view, state, names):
    active = view.active_queue_row()
    for i, product in enumerate(view.items[:7]):
        name, _st = names.product(product, state) if product != w.NONE \
            else ("", "ok")
        y = w.QUEUE_TEXT_Y + i * w.QUEUE_PITCH
        text(surface, screen, name, w.QUEUE_TEXT_X, y, w.QUEUE_W, "value",
             "value", align="center")
        if i == active and i < len(view.queue):
            f = view.queue[i]
            hud.outline(surface, nd.rect(screen.layout,
                                         (f.x, f.y, f.x_end, f.y_end)),
                        screen.layout.scale)


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
        lit = key == "auto" and view.auto_building != 0
        hud.slant_button(surface, r, screen.layout.scale,
                         "active" if lit else "normal", screen.word(key),
                         style_renderer=screen.style)
