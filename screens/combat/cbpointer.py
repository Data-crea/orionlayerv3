"""What the battle's pointer and its fields do beyond the orders' gestures —
work order 398 (package 1 of the engine-against-overlay gaps of 397). Split
out of `cbinput` at a named seam: that module holds the gestures' sends, this
one the facts the pointer's picture is chosen from (`cbcursor.pick`), the
fields the original keeps while its OPTIONS panel is up, and the centre
click. Each function takes the combat screen (`scr`) and reads its state.

TRANSCRIPTION `centre_click` (G1): the original's hidden field over the
unit's picture, (15, 379)-(100, 460), hotkey "c" (combat1.cpp:288), snaps
the view to the acting unit (:827-829). It is added with the weapon rows in
both lists, the orders' and the OPTIONS panel's, and cleared with every field
while AUTO plays or another player's unit acts (:168-196 — the
`Add_Tactical_Combat_Fields` early return). HD's window over the
unit's picture is that field; the key C is the same field and takes the
same guard (`centre_on_acting`).

DEVIATION `centre_click_area`: HD's click area is the field's part of the
unit's status box, `cbstatus.field_rect` of `cbstatus.CENTRE_FIELD` (15, 379)
-(100, 460) in the box drawn at (13, 375) — measured from the box's own
rectangle, not the whole status window — so it covers the picture and bars
as the original's does and not HD's name line or margins.

OMISSION `centre_click_net`: the original's list is also cleared by
`game_type != 1 && owner != PLAYER_NUM && take_control_flag == 0`
(combat1.cpp:165-166); HD is single-player, the `[` take-control key has no
handler, so only the owner test (`scr._human_acting`) is kept.

TRANSCRIPTION `options_fields` (G5): with the OPTIONS panel up
(`order_info_flag` 0) the list is the panel's own fields (the five lights,
SELF DESTRUCT, the title/ESC button) plus — added after the if/else, for
both lists — the eight weapon-row fields and the centre field
(combat1.cpp:250-288); the reduced map's grid field is added in the OPTIONS
branch too (:257) and its click re-centres (:814-816). Not in the OPTIONS
list: the map's own grid (`space_field` -100, :256, so no move, fire or face),
the missile fields (-1000, :253), the WEAPONS/SPECIALS tabs (-100, :259-260)
and AUTO, SCAN, BOARD, RETREAT, WAIT, DONE and T (-100). The weapon-row
handler runs whatever the list (:730-745) and only while the weapons view is
shown (`ship_status_display == 0`, HD's rows exist only there); the
original's hit areas do not overlap the panel (rows x 120-255, the panel's
lights 264-407), so HD's panel window (`Options.panel`) is not served.
`served_in_options` answers for those clicks, nothing else.
"""
import logging

from core import combatblocks as cb
from . import cbcursor, cbdraw, cbmap, cbtarget

log = logging.getLogger("combat")


def centre_on_acting(scr):
    """The centre field's effect (`Snap_Center_Combat_Screen` on the acting
    unit's cell, combat1.cpp:827-829): the view moves, nothing is sent.
    Served on the player's own unit's turn (`_human_acting`, the OPTIONS
    panel's list too) and not under AUTO (its list is one field). True when
    the view moved."""
    c = scr._shown()
    unit = cb.acting_unit(c) if c else None
    if unit is None or scr._cam is None or not scr._human_acting() or \
            scr._computer(c):
        return False
    # DEVIATION `centre_snap`: the original puts the unit's cell at the
    # middle of its 32 x 18 view (`Snap_Center_Combat_Screen(x, y)`: the
    # view's corner is x - 16, y - 9, combinit.cpp:2490-2491), the cell's
    # corner at the middle, as the reduced map's click does; HD does the
    # same instead of the footprint's centre (`cbdraw.centre`), which would
    # differ by up to 30 px for a large ship. The original's clamp to the
    # grid is `Camera.clamp`'s.
    scr._cam.centre_on(unit["x"] * cbdraw.CELL, unit["y"] * cbdraw.CELL)
    return True


def served_in_options(scr, x, y):
    """A click with the OPTIONS panel up on a field the original keeps
    (TRANSCRIPTION `options_fields`): the reduced map re-centres, a weapon
    row switches, the unit's picture centres. Not the panel's own window.
    True when it was one of these."""
    panel = scr._opts.panel
    if panel is not None and panel.collidepoint(x, y):
        return False
    c = scr._shown()
    if c is None or not scr._human_acting() or scr._computer(c):
        return False
    at = cbmap.cell_at(scr._panel.map, x, y) \
        if scr._panel.map is not None else None
    if at is not None:
        if scr._cam is not None:
            scr._cam.centre_on(at[0] * cbmap.CELL, at[1] * cbmap.CELL)
        return True
    row = scr._panel.row_at(x, y)
    if row is not None:
        if scr.app.connected:
            scr._panel.switch(row, scr._state, scr.app.client)
        return True
    if scr._panel.picture is not None and \
            scr._panel.picture.collidepoint(x, y):
        return centre_on_acting(scr)
    return False


def pointer_pick(scr, unit, tick):
    """`Assign_Mouse_Images`' picture for the battle as HD shows it:
    (icon, frame) from `cbcursor.pick`, or None for HD's own pointer
    (`cbcursor`'s docstring: the order of the tests, the deviations).
    OMISSION `centre_click_net`: the clock tests the owner alone, the
    original's `game_type != 1` (combat1.cpp:2214) has no HD counterpart."""
    c = scr._shown()
    if unit is None or c is None or scr._art is None or scr._tail or \
            scr._logwin.open or scr.help.visible or \
            scr._pops.showing(scr._state):
        return None
    if unit["owner"] != scr._me():
        return cbcursor.pick(tick=tick)          # the computer's turn
    pt, cam = scr._pointer, scr._cam
    if pt is None or cam is None or not scr._own_turn() or scr._computer(c) \
            or scr._opts.up(scr._state) or not cam.on_field(*pt):
        return None
    cur = cb.acting_index(c)
    cell = cam.cell_at(*pt)
    t = scr._unit_at(cell) if cell is not None else None
    if t is None:
        kind = None
    elif t == cur:
        kind = "self"
    elif c["units"][t]["owner"] == unit["owner"]:
        kind = "own"
    elif cbdraw.unit_ref(c["units"][t], "stasis_source_idx") is not None:
        kind = "held"
    else:
        kind = "enemy"
    move = None
    if not scr._board and not scr._pops.scan_mode:
        cell = scr._frame_cell(pt)
        move = cbcursor.icon(unit, cell) if cell is not None else None
    return cbcursor.pick(
        missile=cbtarget.missile_under(scr._play.ordnance, cam, *pt)
        is not None, scan=scr._pops.scan_mode, board=scr._board,
        move=move, target=kind)

