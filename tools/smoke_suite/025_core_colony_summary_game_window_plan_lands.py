# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 025_core_colony_summary_game_window_plan_lands.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (93 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 2 check(s) it holds:
#   - colony summary game window (plan lands from every reachable _first, and does nothing below ten c
#   - colony summary _first read back from the scroll thumb ( states, null state distinct from zero)


# ── The game's list window, established not remembered ──
# Decision 46. An injected click names a POSITION IN THE GAME'S
# WINDOW, so `_first` has to agree with the HD row before
# anything is sent, and nothing on the wire reports `_first`.
#
# THE PLAN IS CHECKED BY SIMULATING THE ORIGINAL'S OWN STEPPERS,
# transcribed here from colsum.cpp rather than reasoned about,
# and it is run FROM EVERY REACHABLE STARTING STATE — which is
# the whole claim: "establish, do not remember" is only true if
# the sequence lands on the target from wherever the window was.
from screens.colony_summary.colonyselect import GameWindow as _GW

def _sim_dec(first, n):
    # Decrement_First_, colsum.cpp:207-221. The stepper refuses
    # entirely below the window; the clamp is `< 1`, which for a
    # non-negative _first is max(0, _first - 1).
    if n >= _GW.SLOTS:
        return max(0, first - 1)
    return first

def _sim_inc(first, n):
    # The CALLER's guard first (colsum.cpp:796): the increment is
    # only offered while _g_colony_list_ptr[_first + 10] is a real
    # colony, and that array is padded with -1 past the count.
    if not (first + _GW.SLOTS < n):
        return first
    # Increment_First_, colsum.cpp:223-232.
    if n >= _GW.SLOTS:
        return first + 1
    return first

# SLOTS is the ORIGINAL's ten and is not read from the layout.
# Decision 46's corollary: HD's visible row count is derived from
# list_area and happens to be ten today, and every k is counted
# against the game's window instead.
assert _GW.SLOTS == 10, _GW.SLOTS
for _n in range(0, 40):
    assert _GW.max_first(_n) == max(0, _n - 10), _n

for _n in (0, 1, 5, 9, 10, 11, 12, 25, 37):
    _reachable = list(range(0, _GW.max_first(_n) + 1))
    for _target in range(0, max(2, _GW.max_first(_n) + 3)):
        _plan = _GW.plan(_n, _target)
        if _plan.refused:
            # A refused target is one the game cannot hold, and
            # it is refused rather than silently clamped.
            assert _target > _GW.max_first(_n) or not _GW.scrolls(_n), (
                f"n={_n} target={_target} refused ({_plan.refused}) "
                f"but max_first is {_GW.max_first(_n)}")
            assert _plan.steps == 0, _plan
            continue
        for _start in _reachable:
            _f = _start
            for _ in range(_plan.down):
                _f = _sim_dec(_f, _n)
            assert _f == 0 or not _GW.scrolls(_n), (
                f"n={_n}: {_plan.down} decrements from {_start} "
                f"left the window at {_f}, not at the top — the "
                f"safe direction is what makes this establish "
                f"rather than remember")
            for _ in range(_plan.up):
                _f = _sim_inc(_f, _n)
            assert _f == _target, (
                f"n={_n} start={_start} target={_target}: the plan "
                f"{_plan} lands on {_f}. Counting a step the game "
                f"refuses is how the two windows come apart")

# FEWER COLONIES THAN SLOTS DOES NOTHING, which is the acceptance
# case: both steppers are guarded by colonies_count >= num_items
# (colsum.cpp:210 and :226) and Update_First_ forces _first = 0
# below the window (colsum.cpp:194-197). So the plan is no steps,
# not "some steps that happen to be refused".
for _n in range(0, 10):
    assert not _GW.scrolls(_n), _n
    _p = _GW.plan(_n, 0)
    assert (_p.down, _p.up, _p.refused) == (0, 0, None), (_n, _p)
    assert _GW.plan(_n, 1).refused == _GW.REFUSE_WINDOW_FIXED, _n
    # and every row is already in the window, at its own index
    for _pos in range(_n):
        _p2, _slot = _GW.slot_for(_n, _pos)
        assert (_p2.steps, _slot) == (0, _pos), (_n, _pos, _p2, _slot)

# A ROW MAPS TO A SLOT, and the last page is full rather than
# short: at n = 25 the window stops at 15, so row 24 is slot 9
# and not slot 14 of a half-empty page.
_p3, _slot3 = _GW.slot_for(25, 24)
assert (_p3.first, _slot3) == (15, 9), (_p3, _slot3)
_p4, _slot4 = _GW.slot_for(25, 20)
assert (_p4.first, _slot4) == (15, 5), (_p4, _slot4)
# Exactly ten colonies: the guard passes but the window still
# cannot move, because slot ten would be empty.
assert _GW.max_first(10) == 0 and _GW.scrolls(10)
assert _GW.slot_for(10, 9)[1] == 9
# Off the end is refused, not clamped.
assert _GW.slot_for(11, 11)[0].refused == _GW.REFUSE_PAST_END
assert _GW.slot_for(11, -1)[0].refused == _GW.REFUSE_PAST_END

# The refusals carry OUR wording (decision 15), like the move
# rules — a window that will not go where HD wants it is a reason
# to show, not a silence.
for _r in (_GW.REFUSE_WINDOW_FIXED, _GW.REFUSE_PAST_END):
    assert _out_cfg["move"].get(_r), (
        f"move.{_r} has no wording")
ok("colony summary game window (plan lands from every reachable "
   "_first, and does nothing below ten colonies)")

# ── Reading _first back off the game's own screen ──
# _first is not on the wire, and ACTIVATE_FIELD has a single slot
# (ext::g_pending_field), so a batch of window steps is silently
# collapsed to the last one. The steps therefore have to be sent
# one at a time and CONFIRMED — and the game draws the number:
# Draw_Bar_Indicator_ (colsum.cpp:747-771) fills palette 229 from
# 271*_first/n + 40 to 271*(_first+10)/n + 40 across x 621..626.
#
# ONE MATCH IS A POINT, NOT A CURVE. The formula is transcribed
# and then exercised over EVERY (n, _first) the engine can hold:
# each pair is rendered the way colsum.cpp draws it, borders over
# the fill's edges included, and read back.
from screens.colony_summary import colonyfirst as _cf

def _render_thumb(n, first):
    _fb = [[0] * 640 for _ in range(480)]
    _b = _cf.thumb_bounds(n, first)
    if _b is None:
        return _fb
    _y1, _y2 = _b
    for _y in range(_y1, _y2 + 1):
        for _x in range(_cf.THUMB_X0, _cf.THUMB_X1 + 1):
            _fb[_y][_x] = _cf.THUMB_FILL
    # colsum.cpp:762-765 — the borders overwrite the fill's own
    # first and last row, which is why the run is inset by one.
    for _x in range(_cf.THUMB_X0, _cf.THUMB_X1 + 1):
        _fb[_y1][_x] = _cf.THUMB_BORDER_LIGHT
        _fb[_y2][_x] = _cf.THUMB_BORDER_DARK
    for _y in range(_y1, _y2 + 1):
        _fb[_y][_cf.THUMB_X0] = _cf.THUMB_BORDER_LIGHT
        _fb[_y][_cf.THUMB_X1] = _cf.THUMB_BORDER_DARK
    return _fb

# THE CONSTANTS ARE ANCHORED TO LITERALS FIRST, because the
# sweep below renders and reads through the SAME thumb_bounds and
# is therefore blind to a wrong constant — changing 271 to 270
# moves the drawing and the reader together and the sweep stays
# green. These pairs are worked out from colsum.cpp:752-753 by
# hand: 271*first/n + 40 and 271*(first+10)/n + 40, C integer
# division, so n=11 first=0 gives 2710//11 = 246 for the lower
# edge and n=20 first=5 gives 1355//20 = 67 for the upper.
assert _cf.thumb_bounds(11, 0) == (40, 286), _cf.thumb_bounds(11, 0)
assert _cf.thumb_bounds(11, 1) == (64, 311), _cf.thumb_bounds(11, 1)
assert _cf.thumb_bounds(20, 5) == (107, 243), _cf.thumb_bounds(20, 5)
assert _cf.thumb_bounds(250, 0) == (40, 50), _cf.thumb_bounds(250, 0)
assert (_cf.THUMB_FILL, _cf.THUMB_X0, _cf.THUMB_X1) == (229, 621, 626)

_pairs = 0
for _n in list(range(10, 60)) + [72, 100, 135, 136, 200, 259]:
    for _f in range(0, max(0, _n - _cf.WINDOW) + 1):
        assert _cf.read_first(_render_thumb(_n, _f), _n) == _f, (
            f"n={_n}, _first={_f} read back as "
            f"{_cf.read_first(_render_thumb(_n, _f), _n)!r}")
        _pairs += 1
assert _pairs > 1500, _pairs

# THE TOLERANCE IS TRANSCRIBED, NOT TUNED, and a wider one is not
# safer. The thumb moves 271/n px per step, so at 2 two
# candidates fit one run from n = 136 and the reader must refuse.
assert _cf.read_first(_render_thumb(136, 1), 136, tolerance=2) is None, (
    "at tolerance 2 and 136 colonies the thumb moves 1.993 px per "
    "step, so _first = 1 has two candidates fitting one run — the "
    "reader must return None rather than pick the nearer")
assert _cf.read_first(_render_thumb(136, 1), 136) == 1, (
    "and at the transcribed tolerance of 1 the same state is exact")

# THE NULL STATE IS ITS OWN ANSWER. Below ten colonies the bar is
# not drawn at all (colsum.cpp:751) and Update_First_ has already
# forced _first = 0 — so the reader must say NOT_DRAWN and never
# 0. A channel that idles as a valid reading is the rim survey's
# green-run-in-a-null-state, one domain over.
for _n in range(0, 10):
    assert _cf.thumb_bounds(_n, 0) is None, _n
    assert _cf.read_first(_render_thumb(_n, 0), _n) == _cf.NOT_DRAWN, (
        f"with {_n} colonies the bar is not drawn and the reader "
        f"returned something other than NOT_DRAWN — a reading of 0 "
        f"there is indistinguishable from a real _first of 0")
assert _cf.NOT_DRAWN != 0 and _cf.NOT_DRAWN is not None
# A blank screen with enough colonies is also NOT_DRAWN: the
# colony summary is simply not up.
assert _cf.read_first([[0] * 640 for _ in range(480)], 25) == \
    _cf.NOT_DRAWN

# AND A RUN THAT FITS NOTHING IS NOT A READING EITHER. None and
# NOT_DRAWN are different answers and a caller must stop on both.
_junk = [[0] * 640 for _ in range(480)]
for _y in range(200, 210):
    for _x in range(_cf.THUMB_X0, _cf.THUMB_X1 + 1):
        _junk[_y][_x] = _cf.THUMB_FILL
assert _cf.read_first(_junk, 25) is None, (
    "a 229 run matching no candidate must read as None — the "
    "channel spoke and was not understood")
ok(f"colony summary _first read back from the scroll thumb "
   f"({_pairs} states, null state distinct from zero)")
