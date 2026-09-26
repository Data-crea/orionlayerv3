"""What a click, a right click, the pointer and a key do on the Leaders screen.

DECISION 20: every send resolves its field in the list on the wire at
the moment of the click, by type and rectangle, and does not go at all
when the field is not there. DECISION 65: nothing is sent whose effect
HD could not see — `ldrwire.View.sendable` is the one answer to "may
this go", and nothing here second-guesses it.

Every hit test resolves the pointer to a NATIVE pixel first and asks
`ldrgeom`'s rectangles, the ones the drawing uses (decision 5).

THE RIGHT BUTTON, as the original splits it (officer.cpp:1283-1339,
:1476-1482): on a SKILL line it is that skill's help box — drawn by HD
(DEVIATION `hd_skill_help`, `ldrdialog`); on a PORTRAIT it is
`Find_Selected_Leader_` (:3159-3220), sent as a right click on the
portrait's own field, whose answer is a box the wire shows; anywhere
else it is the help list (`help.json`, the original's two tables). On a
big ship icon, with the block, it is `CMBTDRW1::Detailed_View_Ship_`
(officer.cpp:1041-1047), sent as a right click on the icon's field; the
game's view answers as the fallback picture (OMISSION
`detailed_ship_view`).

THE GALAXY BOX AND THE GRID (work order 175, open fix 30 applied) —
`ldrmap` finds the field, and only in mode -1, as the loop reads them
(officer.cpp:986-1086): a star with one of the player's colonies in the
colony view (it becomes `_officer_star_chosen` and `_displayed`,
:1060-1070 — a star without one is not sent, the game would ignore it);
a stack icon in the ship view (`Scan_Small_Ship_Icons_` makes it the
stack on show, flt1.cpp:851-861 — in the colony view that pointer is
invisible and is not sent); a big icon in the ship view (picks it, or
assigns the selected officer, :1004-1034).
"""
import logging

from core import researchnative as nat
from core import skildesc

from . import ldrdialog, ldrdraw, ldrgeom, ldrmap, ldrrows, ldrwire

log = logging.getLogger("leaders")

#: ESC, the RETURN button's hotkey (officer.cpp:2906), and the one key
#: every native box answers to.
KEY_ESC = 27


def native(screen, screen_x, screen_y):
    """The native 640x480 pixel under a window point, or None."""
    ref = screen.layout.to_ref(screen_x, screen_y)
    return nat.from_hd_point(ref, screen.layout)


def _inside(point, rect):
    x1, y1, x2, y2 = rect
    return x1 <= point[0] <= x2 and y1 <= point[1] <= y2


def _field_at(view, rect):
    """The live field with exactly this rectangle, or None."""
    return next((f for f in view.fields
                 if (f.x, f.y, f.x_end, f.y_end) == tuple(rect)), None)


def send(screen, field, why):
    if field is None or not screen.app.connected:
        return False
    log.info("leaders: %s -> field %d", why, field.index)
    screen.app.client.activate_field(field.index)
    return True


def click(screen, screen_x, screen_y):
    """A left click. Returns None; everything it does is a send."""
    if screen._skill_help is not None:
        screen._skill_help = None            # any click closes it
        return None
    view = screen._view
    if view is None:
        return None
    if view.state == ldrwire.IN_BOX:
        from screens.fleets import fltbox
        for key, field, rect in fltbox.button_rects(screen):
            if rect.collidepoint(screen_x, screen_y):
                send(screen, field, f"box {key}")
        return None
    if view.state == ldrwire.POPUP:
        for key, rect in ldrdialog.popup_rects(screen):
            if rect.collidepoint(screen_x, screen_y):
                send(screen, getattr(view.popup, key, None), f"popup {key}")
        return None
    point = native(screen, screen_x, screen_y)
    if point is None or view.state != ldrwire.READY:
        return None
    for name in ldrgeom.BUTTONS:
        if _inside(point, ldrgeom.button_rect(name)) and name in view.buttons:
            if view.sendable(name):
                send(screen, view.buttons[name], name)
            else:
                log.info("leaders: %s not sent — %s", name, NO_BLOCK)
            return None
    for slot, idx, rec in view.listed():
        if not (_inside(point, ldrgeom.text_field(slot))
                or _inside(point, ldrgeom.portrait_field(slot))):
            continue
        # A leader FOR HIRE opens the hire question in EVERY mode, and
        # hire mode sends any leader to `Do_Hire_Officer_` — both answer
        # with a popup or a message the wire shows (officer.cpp:1409-1414).
        # Anything else selects or acts in a mode HD cannot see.
        for_hire = int(rec.status) == 4
        if view.sendable("leader") or view.mode == 0 or (
                for_hire and view.sendable("hire_leader")):
            send(screen, _field_at(view, ldrgeom.text_field(slot)),
                 f"leader {idx}")
        else:
            log.info("leaders: leader %d not sent — %s", idx, NO_BLOCK)
        return None
    if view.block is not None and view.mode == -1:
        _map_click(screen, view, point)
    return None


#: Why a control needing the view state is not sent: an engine without
#: open fix 30 (applied on orionlayer-local since work order 175;
#: `tools/version_check.py` names an engine that lacks it).
NO_BLOCK = ("the engine sends no OFFS block (open fix 30 is not in this "
            "engine), so its effect could not be seen")


def _map_click(screen, view, point):
    """A click in the galaxy box or the grid — see the module docstring."""
    state = screen._state
    if view.view == ldrgeom.VIEW_SHIP:
        big = ldrmap.big_icon_at(view.block, point)
        if big is not None:
            send(screen, _field_at(view, ldrgeom.grid_cell(big[1])),
                 f"big icon {big[0]}")
            return
        hit = ldrmap.icon_at(state, view.fields, point)
        if hit is not None:
            send(screen, hit[1], f"stack icon {hit[0]}")
        return
    star = ldrmap.star_at(state, point)
    if star is None:
        return
    if view.player not in ldrmap.colony_owners(state, state.stars[star]):
        log.info("leaders: star %d not sent — no colony of the player's "
                 "there, the game would ignore it", star)
        return
    send(screen, ldrmap.star_field(state, view.fields, star), f"star {star}")


def right_button(screen, down, screen_x, screen_y):
    """See the module docstring. True when the press was used."""
    if not down:
        return False
    if screen.help.visible:
        screen.help.close()
        return True
    if screen._skill_help is not None:
        screen._skill_help = None
        return True
    view = screen._view
    if view is not None and view.state == ldrwire.READY:
        for row in screen._rows:
            for k, rect in enumerate(ldrdraw.skill_line_rects(screen, row)):
                if rect.collidepoint(screen_x, screen_y):
                    open_skill_help(screen, row, row.skills[k][0])
                    return True
        point = native(screen, screen_x, screen_y)
        big = (ldrmap.big_icon_at(view.block, point)
               if point is not None and view.view == ldrgeom.VIEW_SHIP
               and view.mode == -1 else None)
        if big is not None:
            field = _field_at(view, ldrgeom.grid_cell(big[1]))
            if field is not None and screen.app.connected:
                log.info("leaders: ship view of big icon %d -> field %d",
                         big[0], field.index)
                screen.app.client.cancel_field(field.index)
                return True
        if point is not None:
            for slot, _idx, _rec in view.listed():
                if _inside(point, ldrgeom.portrait_field(slot)):
                    field = _field_at(view, ldrgeom.portrait_field(slot))
                    if field is not None and screen.app.connected:
                        log.info("leaders: where is leader %d -> field %d",
                                 _idx, field.index)
                        screen.app.client.cancel_field(field.index)
                    return True
    return open_help(screen, screen_x, screen_y)


def open_skill_help(screen, row, skill_id):
    """HD's own skill help box (DEVIATION `hd_skill_help`)."""
    the = ldrrows.the_word(screen._words, row.index)
    text = ldrrows.skill_help_text(row.rec, row.index, skill_id, row.level,
                                   screen._words, screen._skills, the)
    if text is None:
        # The texts are the player's own SKILDESC.LBX; absent, the box
        # says how to get them rather than opening empty.
        text = (f"Skill {skill_id}",
                f"The skill help texts are not extracted. Run: "
                f"{skildesc.HOW}")
    screen._skill_help = text


def open_help(screen, screen_x, screen_y):
    """The original's help list for the view on show, first hit wins
    (`Check_Help_List_`, fields.cpp:2924-2932)."""
    view = screen._view
    if view is None:
        return False
    point = native(screen, screen_x, screen_y)
    if point is None:
        return False
    counts = [0] * ldrgeom.ROWS
    for row in screen._rows:
        counts[row.slot] = len(row.skills)
    entries = ldrgeom.help_list(screen._help_doc.get("regions", []),
                                view.view, counts)
    if view.view == ldrgeom.VIEW_SHIP:
        shown = len((view.block or {}).get("ship_idx") or [])
        entries += [(ldrgeom.HELP_EMPTY_GRID, r) for r in
                    ldrgeom.help_empty_cells(min(ldrgeom.GRID_COLUMNS
                                                 * ldrgeom.GRID_ROWS, shown))]
    for help_id, rect in entries:
        if _inside(point, rect):
            entry = screen.helptext.entry(help_id) or \
                screen.helptext.missing_entry(help_id)
            screen.help.open(help_id, *entry)
            return True
    return False


def hover(screen, screen_x, screen_y):
    """The leader under the pointer is lit and priced — HD's own
    `_officer_scanned` (officer.cpp:1320-1336) — and the star, stack or
    big icon under it named (`ldrmap.scan`). Sends nothing."""
    screen._hover = None
    point = native(screen, screen_x, screen_y)
    if screen._view is not None and screen._view.state == ldrwire.READY:
        ldrmap.scan(screen, point)
    if point is None or screen._view is None:
        return
    for slot, idx, _rec in screen._view.listed():
        if _inside(point, ldrgeom.text_field(slot)) or \
                _inside(point, ldrgeom.portrait_field(slot)):
            screen._hover = idx


def key(screen, keycode):
    """ESC closes HD's help box, answers a native box, or is RETURN."""
    view = screen._view
    if keycode != KEY_ESC or view is None:
        return
    if screen._skill_help is not None:
        screen._skill_help = None
        return
    if view.state == ldrwire.READY and view.sendable("return"):
        send(screen, view.buttons.get("return"), "ESC")
    elif view.state == ldrwire.IN_BOX and view.box is not None:
        send(screen, view.box.fields.get(KEY_ESC), "box ESC")
