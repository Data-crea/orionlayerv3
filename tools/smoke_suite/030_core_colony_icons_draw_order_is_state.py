# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 030_core_colony_icons_draw_order_is_state.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (91 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 2 check(s) it holds:
#   - colony icons (draw order is state/conquered/pop_order/array, not array; unassigned pops draw not
#   - colony icon geometry (squish transcribed, every slot's click round-trips through the original's 


ok("colony icons (draw order is state/conquered/pop_order/array, "
   "not array; unassigned pops draw nothing)")

# ── The squish, and the x that lands on a slot ────────────────
# Calculate_Squish_Step_ (coldraw.cpp:12-33) divides the column by
# the icon count, so the pitch moves with the population. The aim
# has to round-trip through the original's own walk, or a click
# takes the icon next door — which moves a different cluster and
# looks perfectly right.
for _job, (_lx, _rx) in enumerate(_ci.COLUMNS):
    for _count in range(1, 43):
        _pitch = _ci.column_pitch(_job, _count)
        _want = min(_ci.ICON_SPACING,
                    max(1, int((_rx - _lx - 10) / _count)))
        assert _pitch == _want, (
            f"column {_job} at {_count} icons: pitch {_pitch}, "
            f"the source computes {_want}")
        # Every icon inside the column, with the ten px the
        # `spacing / -3` term reserves still to spare — which is
        # why Find_Bar_Position_'s clamp never bites.
        assert _lx + _pitch * _count <= _rx - 10, (
            f"the last icon of {_count} in column {_job} reaches "
            f"{_lx + _pitch * _count}, past {_rx - 10}")
        for _slot in range(_count):
            _x = _ci.slot_click_x(_job, _slot, _count)
            assert _ci.slot_at(_job, _x, _count) == _slot, (
                f"aiming at slot {_slot} of {_count} in column "
                f"{_job} (x {_x}) selects "
                f"{_ci.slot_at(_job, _x, _count)}")
# The fallback: anything past the last icon is the last icon
# (coldraw.cpp:361), which is what makes a click at the column's
# right edge safe without any squish arithmetic at all.
assert _ci.slot_at(0, _ci.COLUMNS[0][1], 7) == 6
assert _ci.slot_at(0, _ci.COLUMNS[0][0] - 50, 7) == 0, (
    "a value left of the column selects the first icon; "
    "Find_Bar_Position_ clamps it to range_min (fields.cpp:1710)")
assert _ci.slot_at(0, 200, 0) is None, (
    "an empty column selects nothing — Get_Selected_Pop_ returns "
    "-1 and Get_Cluster_ is never called")
# The row a click names is a SLOT in the game's window, never an
# HD row (decision 46), and its y is the field's own middle.
assert _ci.row_click_y(0) == 34 + 15 and _ci.row_click_y(3) == \
    34 + 93 + 15, "row y is slot * 31 + 34, colsum.cpp:311-345"
ok("colony icon geometry (squish transcribed, every slot's click "
   "round-trips through the original's own walk)")
