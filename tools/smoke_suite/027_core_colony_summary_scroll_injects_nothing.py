# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 027_core_colony_summary_scroll_injects_nothing.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (91 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 1 check(s) it holds:
#   - colony summary scroll injects nothing and moves no selection; a sort resets the window and keeps


# ── A SCROLL SENDS NOTHING TO THE GAME (fundament 46) ──
# This is what lets the package ship without the synchronisation.
# The original's rows are ten SLOTS over the sorted array
# (_list_col[i] = _g_colony_list_ptr[_first + i],
# colsum.cpp:348-351) and every clickable field is built per slot
# (Add_Fields_Pop_For_, colsum.cpp:312-346), so an injected click
# names a position in the GAME's window and _first decides which
# colony it reaches. Ours is a viewing offset the game has never
# heard of. Scrolling is therefore safe precisely as long as it
# injects NOTHING, and the day somebody adds an injection to this
# path it must fail here rather than send a click to the wrong
# colony — which is invisible, because every value on both
# screens stays correct.
class _CapAll(_Cap):
    def __init__(self):
        super().__init__(); self.fields = []
    def activate_field(self, f): self.fields.append(f)
_sc_cap = _CapAll()
_sc_client, _sc_conn = app.client, app.connected
app.client, app.connected = _sc_cap, True
_sc_pt = (_la.x + 4, _la.y + 4)
_sc_before = _scr_op._selected
for _ in range(_sc_n + 5):
    _scr_op.handle_mousewheel(-1, *_sc_pt)      # down, past the end
assert _scr_op._first == _sc_hidden, (
    f"scrolling to the end left first at {_scr_op._first}, not "
    f"{_sc_hidden}")
for _ in range(_sc_n + 5):
    _scr_op.handle_mousewheel(1, *_sc_pt)       # and back up
assert _scr_op._first == 0, _scr_op._first
assert _sc_cap.calls == [] and _sc_cap.keys == [] \
    and _sc_cap.fields == [], (
    f"a scroll reached the game: clicks {_sc_cap.calls}, keys "
    f"{_sc_cap.keys}, fields {_sc_cap.fields}. The HD list scrolls "
    f"for VIEWING ONLY — the game's _first is not synchronised "
    f"yet (fundament 46), so an injection now names a row in the "
    f"game's window and reaches the wrong colony")
# A wheel outside list_area is not ours either.
_scr_op.handle_mousewheel(-1, _la.x - 40, _la.y - 40)
assert _scr_op._first == 0, (
    "a wheel event outside list_area scrolled the list")

# SCROLLING DOES NOT MOVE THE SELECTION. It holds a COLONY, not a
# row index (colsum.cpp:830-837, colonyselect), so the window may
# travel past it and the scan box goes on showing the same colony.
assert _scr_op._selected == _sc_before, (
    f"a scroll moved the selection from {_sc_before} to "
    f"{_scr_op._selected}")

# A SORT RESETS THE WINDOW AND KEEPS THE SELECTION — one handler,
# two opposite rules. colsum.cpp:832 sets _first = 0; the same
# block (colsum.cpp:830-837) never assigns _g_colony_n.
for _ in range(3):
    _scr_op.handle_mousewheel(-1, *_sc_pt)
assert _scr_op._first == 3, _scr_op._first
_sc_sel_before = _scr_op._selected
_sc_btn = next(_b for _b in _scr_op._sort_buttons()
               if _b.key == "population")
_scr_op.handle_click(_sc_btn.hit.centerx, _sc_btn.hit.centery)
assert _scr_op._first == 0, (
    f"the sort left the window at {_scr_op._first}; the original "
    f"puts it back at the top (_first = 0, colsum.cpp:832)")
assert _scr_op._selected == _sc_sel_before, (
    f"the sort moved the selection from {_sc_sel_before} to "
    f"{_scr_op._selected}; colsum.cpp:830-837 never touches "
    f"_g_colony_n, so the colony keeps its identity and only its "
    f"ROW moves")
app.client, app.connected = _sc_client, _sc_conn
_scr_op._sort_key = "name"
_scr_op.update(_sel_snap)
ok("colony summary scroll injects nothing and moves no selection; "
   "a sort resets the window and keeps the colony")
