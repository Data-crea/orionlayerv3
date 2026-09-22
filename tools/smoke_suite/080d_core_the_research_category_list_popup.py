# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 080d_core_the_research_category_list_popup.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (97 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# This one did NOT stand inside main(): it is work order 165 part C,
# the category list popup, which is one behaviour of BOTH research
# modes and therefore lives in core/ and in this group.
#
# The 3 check(s) it holds:
#   - the category list is Get_Group_List_, padding and all, and it
#     pages the way Init_List_Data_ pages
#   - the list popup opens on the right category, in the right column,
#     81 px apart between the modes
#   - the list popup's input table is the original's, and it sends
#     nothing at all
from core import researchtechlist as _tl

# ── 1. THE CONTENT IS `Get_Group_List_` (tech.cpp:1105-1168) ──
#
# Walk the category's chain; skip a researched field; promote a field
# with a researched application to status 1; keep it only if at least
# one application is at status >= 1; and the field being researched is
# status 4, which the original assigns rather than reads.
_tl_tf = [0] * _rl_res.FIELD_COUNT
_tl_chain = []
_tl_f = _rl.FIRST_FIELD_IN_GROUP[4]
while _tl_f != 0:
    _tl_chain.append(_tl_f)
    _tl_f = _rl.NEXT_FIELD[_tl_f]
assert len(_tl_chain) >= 6, _tl_chain
for _tl_f in _tl_chain:
    _tl_tf[_tl_f] = _rl.FIELD_STATUS_OFFERABLE
_tl_ta = [0] * player_mod.TECH_APPLICATIONS_COUNT
_tl_slots = _rl.field_applications()
for _tl_f in _tl_chain:
    for _tl_a in _tl_slots.get(_tl_f, ()):
        _tl_ta[_tl_a] = _rl.APP_STATUS_AVAILABLE

_tl_items = _tl.group_list(_tl_tf, _tl_ta, 0, 4)
assert [i.field for i in _tl_items] == _tl_chain, (
    [i.field for i in _tl_items], _tl_chain)
for _tl_i in _tl_items:
    assert _tl_i.status == _rl.FIELD_STATUS_OFFERABLE
    assert _tl_i.apps == _tl_slots.get(_tl_i.field, ()), _tl_i.field
    assert set(_tl_i.statuses) == {_rl.FIELD_STATUS_OFFERABLE}

# A RESEARCHED FIELD IS SKIPPED, and the field being researched is not
# — it is the one the popup marks.
_tl_done = dict(enumerate(_tl_tf))
_tl_tf2 = list(_tl_tf)
_tl_tf2[_tl_chain[1]] = 3                       # researched
_tl_cur = _tl_chain[2]
_tl_marked = _tl.group_list(_tl_tf2, _tl_ta, _tl_cur, 4)
assert [i.field for i in _tl_marked] == \
    [f for f in _tl_chain if f != _tl_chain[1]], \
    [i.field for i in _tl_marked]
_tl_one = next(i for i in _tl_marked if i.field == _tl_cur)
assert _tl_one.status == _tl.STATUS_CURRENT
assert set(_tl_one.statuses) == {_tl.STATUS_CURRENT}, _tl_one.statuses
# …and status 4 is drawn in the colour the panel marks the current
# research with, which in the original is `group_colors[4]` reading one
# past a four-entry array onto `disabled_color`. Transcribed as what it
# lands on, and asserted so a later reader cannot "correct" it.
assert _tl.STATUS_COLOUR[_tl.STATUS_CURRENT][0] == "row_current"
assert _tl.STATUS_COLOUR[_rl.FIELD_STATUS_OFFERABLE][0] == "row"

# A FIELD AT STATUS 0 WITH A RESEARCHED APPLICATION is promoted to 1
# and still listed (tech.cpp:1127-1136).
_tl_tf3 = [0] * _rl_res.FIELD_COUNT
_tl_promo = _tl_chain[0]
_tl_ta3 = [0] * player_mod.TECH_APPLICATIONS_COUNT
_tl_ta3[_tl_slots[_tl_promo][0]] = 3            # RESEARCHED
_tl_p = _tl.group_list(_tl_tf3, _tl_ta3, 0, 4)
assert [i.field for i in _tl_p] == [_tl_promo], [i.field for i in _tl_p]
assert _tl_p[0].status == 1 and _tl_p[0].apps == \
    (_tl_slots[_tl_promo][0],)

# THE `tech[4]` PADDING IS READ, and the player's own data decides what
# that means. `Get_Group_List_` walks all four slots and reads
# `tech_applications[tech[i]]` for the empty ones, which is
# `tech_applications[0]`. Dropping the padding would answer that
# question silently instead of transcribing it.
_tl_short = next(f for f in _tl_chain if len(_tl_slots.get(f, ())) < 4)
assert len(_tl.field_slots(_tl_short, _tl_slots)) == _rl.MAX_ROWS
_tl_pad_ta = list(_tl_ta)
_tl_pad_ta[0] = _rl.APP_STATUS_AVAILABLE
_tl_padded = _tl.group_list(_tl_tf, _tl_pad_ta, 0, 4)
_tl_pad_item = next(i for i in _tl_padded if i.field == _tl_short)
assert 0 in _tl_pad_item.apps, (
    "the empty tech[] slots are not being read; Get_Group_List_ reads "
    "them and the player's own tech_applications[0] is what decides")
_tl_plain = next(i for i in _tl_items if i.field == _tl_short)
assert 0 not in _tl_plain.apps

# ── PAGING IS `Init_List_Data_` (list.cpp:143-186) ──
#
# The step is `_app_name_y[app_count] + 8` — the table read ONE PAST
# the last label — and an item whose bottom would pass 424 starts the
# next page at the top instead.
_tl_pages = _tl.paginate(_tl_items)
assert sum(len(p) for p in _tl_pages) == len(_tl_items)
for _tl_page in _tl_pages:
    _tl_y = _tl.LIST_Y
    for _tl_i in _tl_page:
        assert _tl_i.y == _tl_y, (_tl_i.field, _tl_i.y, _tl_y)
        _tl_y += _tl.APP_NAME_Y[len(_tl_i.apps)] + _tl.ITEM_SPACING
    assert _tl_y <= _tl.Y_MAX + _tl.APP_NAME_Y[len(_tl_page[-1].apps)] \
        + _tl.ITEM_SPACING
assert len(_tl_pages) > 1, (
    f"{len(_tl_items)} items fitted on one page — this fixture cannot "
    f"tell paging from not paging")
# The rows are the original's rectangles, and they are the SAME table
# the panel's rows use (tech.cpp:30-32 / list.cpp:100-108).
_tl_row = _tl_pages[0][0].row_rect(0, 500)
assert _tl_row == (500, _rl.ROW_Y1[0] + _tl.LIST_Y, 500 + 213,
                   _rl.ROW_Y2[0] + _tl.LIST_Y), _tl_row
ok("the category list is Get_Group_List_, padding and all, and it "
   "pages the way Init_List_Data_ pages")

# ── 2. THE WINDOW FOLLOWS THE MODE AND THE COLUMN ──
#
# `_list_window_x_offsets[i] + _g_scrn_x` (tech.cpp:33, :421): a
# LEFT-column entry opens its window on the RIGHT and the other way
# round, and the whole thing moves with the panel origin.
_tl_pop = _tl.TechListPopup()
for _tl_mode, _tl_origin in (("select", 161), ("change", 80)):
    _tl_geo = _dx_geo.Geometry(_tl_mode)
    assert _tl_geo.origin == _tl_origin
for _tl_idx in range(8):
    _tl_pop.open(type("E", (), {"index": _tl_idx, "group": 4})(), [])
    _tl_sel, _tl_chg = (_tl_pop.window_x(161), _tl_pop.window_x(80))
    assert _tl_sel - _tl_chg == 81, (_tl_idx, _tl_sel, _tl_chg)
    assert _tl_pop.window_x(80) - 80 == (205 if _tl_idx % 2 == 0 else 6)
_tl_pop.close()
assert not _tl_pop.visible
ok("the list popup opens on the right category, in the right column, "
   "81 px apart between the modes")

# ── 3. THE INPUT TABLE, AND NOTHING ON THE WIRE ──
#
# tech.cpp:979-1029: the page buttons page; a row click returns an id
# NOTHING branches on; everything else is the whole-screen field and
# closes; a right click on a row opens that application's description;
# a right click anywhere else only redraws. And the whole popup is
# display-only, so not one byte goes out for any of it.
# THE SEND-COUNTING CLIENT, installed here rather than assumed: a
# module between 080 and this one leaves the app holding a
# different one, and a zero send count off somebody else's client
# would be a number about nothing.
_dx_scr.app.client, _dx_scr.app.connected = _rs_client, True
_rs_client.state = _dx_state
_rs_client.log.clear()
_dx_scr.update(_dx_state)
assert _dx_scr.state == _dx_core.READY, _dx_scr.problems
_tl_entry = next(e for e in _dx_scr._entries if e.offered)
_tl_field = _dx_scr.radio_field(_tl_entry.index)
assert _tl_field is not None, (
    f"no type-{_rl.TYPE_RADIO} field at the category button's own "
    f"origin for entry {_tl_entry.index}")
_tl_px, _tl_py = _dx_geo.window_point(
    ((_tl_field.x + _tl_field.x_end) // 2,
     (_tl_field.y + _tl_field.y_end) // 2), _dx_scr.layout)
_dx_scr.handle_click(_tl_px, _tl_py)
assert _dx_scr._techlist.visible
# Q11: the category is the BUTTON'S OWN, not `entries[index - first]`.
assert _dx_scr._techlist.entry.group == _tl_entry.group

_tl_win = _dx_scr._techlist.window_rect(_dx_scr.geom.origin)
_tl_items_now = _dx_scr._techlist.items()


def _tl_click(native_xy, button=1):
    _p = _dx_geo.window_point(native_xy, _dx_scr.layout)
    if button == 1:
        _dx_scr.handle_click(*_p)
    else:
        _dx_scr.handle_right_button(True, *_p)


if _tl_items_now:
    _tl_it = _tl_items_now[0]
    _tl_r = _tl_it.row_rect(0, _dx_scr._techlist.list_x(_dx_scr.geom.origin))
    _tl_mid = ((_tl_r[0] + _tl_r[2]) // 2, (_tl_r[1] + _tl_r[3]) // 2)
    # A ROW CLICK DOES NOTHING AND THE LIST STAYS.
    _tl_click(_tl_mid)
    assert _dx_scr._techlist.visible, (
        "a row click closed the list; the original's loop compares that "
        "id against nothing (tech.cpp:1014-1017)")
    # A RIGHT CLICK ON A ROW describes that application.
    _dx_scr.help.close()
    _tl_click(_tl_mid, button=3)
    assert _dx_scr.help.visible and _dx_scr.help.help_id == _tl_it.apps[0]
    _dx_scr.help.close()
# ANYTHING ELSE CLOSES: the whole-screen field is what the click lands
# on, and `match_val == hidden_field_1` returns (tech.cpp:1015-1028).
_tl_click((_tl_win[0] + 4, _tl_win[3] - 4))
assert not _dx_scr._techlist.visible

# ESC CLOSES THE LIST AND DOES NOT LEAVE THE SCREEN, in change mode
# where there IS something to leave: the popup's own whole-screen field
# carries the ESC hotkey (tech.cpp:968).
_dx_scr.handle_click(_tl_px, _tl_py)
assert _dx_scr._techlist.visible
_dx_scr.handle_key(pygame.K_ESCAPE)
assert not _dx_scr._techlist.visible
assert not _dx_scr._left, (
    "ESC under an open list reached the exit button; it must close the "
    "list and stop there")

# PAGING, and it is the popup's own state and not a send.
_dx_scr._techlist.open(_tl_entry, _tl_items)
assert len(_dx_scr._techlist.pages) > 1
_tl_up, _tl_down = _dx_scr._techlist.button_rects(_dx_scr.geom.origin)
assert _tl_up is None and _tl_down is not None, (
    "page one offers an UP button or no DOWN button; "
    "Set_List_Up_Down_Field_Drawing_ enables each only where it acts")
_tl_click(((_tl_down[0] + _tl_down[2]) // 2,
           (_tl_down[1] + _tl_down[3]) // 2))
assert _dx_scr._techlist.page == 1 and _dx_scr._techlist.visible
_tl_up, _tl_down = _dx_scr._techlist.button_rects(_dx_scr.geom.origin)
assert _tl_up is not None
_tl_click(((_tl_up[0] + _tl_up[2]) // 2, (_tl_up[1] + _tl_up[3]) // 2))
assert _dx_scr._techlist.page == 0
_dx_scr._techlist.close()

assert _rs_client.log == [], (
    f"the list popup sent {_rs_client.log} — it is display-only in the "
    f"original and HD sends nothing for it")
ok("the list popup's input table is the original's, and it sends "
   "nothing at all")
