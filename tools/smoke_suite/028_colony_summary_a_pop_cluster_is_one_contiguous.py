# smoke-suite area: colony_summary
#
# Part of the OrionLayer smoke suite — 028_colony_summary_a_pop_cluster_is_one_contiguous.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (93 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 1 check(s) it holds:
#   - a pop cluster is one contiguous run of icons (decision 48: only because the column is drawn in t


# ── The icons a column draws, and in whose order ──────────────
# A COLUMN IS NOT pop[] IN ARRAY ORDER. `Do_Colony_Info_Pop_Stuff_
# For_Pop_` (coldraw.cpp:326-337) walks state, then the conquered
# bit, then pop_order (9 first), then the array — so the icon at
# slot m is not the m-th pop of that job, and a click aimed by
# array position would take the wrong cluster with every number on
# both screens still correct.
from screens.colony_summary import colonyicons as _ci

def _icon_pop(nibble=0, job=0, assigned=True, conquered=0):
    return (nibble | (job << 7)
            | (_cst.POP_MASK_ASSIGNED if assigned else 0)
            | (conquered << 10))

# THE LIVE CASE, ENCODED. Measured 5 September 2026 against the
# reference save: Blucher II had twelve farmers and one scientist,
# the scientist at pop 11 and the last farmer at pop 12. A click
# at native x 230 — past every icon — took pop 12, which is slot
# ELEVEN of the column and not pop 11. That is the whole
# distinction this module exists for, so it is the fixture.
_live = ([_icon_pop(0, 0)] * 11 + [_icon_pop(0, 2)]
         + [_icon_pop(0, 0)])
assert _ci.icon_pops(_live, 13, 0) == tuple(list(range(11)) + [12]), (
    "the food column must draw pops 0..10 and 12 — the scientist "
    "at 11 is not in it, and the last farmer is index 12")
assert _ci.slot_at(0, 230, 12) == 11, (
    "a click past every icon selects the LAST slot "
    "(coldraw.cpp:361), which here is slot 11")
assert _ci.slot_pop(_live, 13, 0, 11) == 12, (
    "slot 11 of that column is pop 12; reading it as pop 11 is "
    "the array-order mistake this check is about")

# THE FIVE LOOPS, each asserted where it decides the order.
# state first (normal 2, native 3, android 4 — colony.cpp:1240),
# then the conquered bit, then the low nibble in pop_order's own
# sequence, and only then the array.
_mixed = [_icon_pop(9, 0), _icon_pop(0, 0), _icon_pop(8, 0),
          _icon_pop(1, 0), _icon_pop(0, 0, conquered=1),
          _icon_pop(0, 0)]
assert _ci.icon_pops(_mixed, 6, 0) == (1, 5, 3, 4, 0, 2), (
    f"draw order is {_ci.icon_pops(_mixed, 6, 0)}; expected the "
    f"low nibbles grouped before the array is consulted — 0s "
    f"(1, 5), then the 1 (3), then the conquered 0 (4), then the "
    f"native (0), then the android (2)")
# THE ARRAY IS THE INNERMOST TIE-BREAK AND NOTHING MORE. Pops 1
# and 3 are both unconquered normals and 1 comes first here only
# because its low nibble does — the nibble loop is OUTSIDE the
# array loop (coldraw.cpp:329-331). Written down because the
# first version of this check expected (1, 3, 5), which is what
# "within a group, array order" reads like until you ask what a
# group is.
assert _ci.POP_ORDER[0] == 9 and len(_ci.POP_ORDER) == 10, (
    "pop_order is (9, 0..8) — coldraw.cpp:287-297")

# UNASSIGNED POPS ARE NOT ICONS (coldraw.cpp:336). This is the
# difference between the HD row, which draws a square per pop of a
# job, and the game, which draws one per ASSIGNED pop — and it is
# exactly the state a held cluster produces.
_held = [_icon_pop(0, 0), _icon_pop(0, 0, assigned=False)]
assert _ci.icon_pops(_held, 2, 0) == (0,), (
    "a pop in a held cluster draws no icon")
assert _ci.slot_pop(_held, 2, 0, 1) is None, (
    "a slot past the icons must answer None, not a guess — the "
    "caller refuses the click on it")

# THE SECOND COPY OF pop_state IS DELIBERATE AND MUST AGREE.
for _n in range(16):
    assert _ci._state(_icon_pop(_n)) == _cm.pop_state(_icon_pop(_n)), (
        f"colonyicons._state and colonymove.pop_state disagree at "
        f"nibble {_n}; the two copies exist so one can be "
        f"re-read without the other silently following")
# A CLUSTER IS A CONTIGUOUS RUN OF ICONS, AND ONLY BECAUSE THE
# COLUMN IS DRAWN IN THE ORIGINAL'S ORDER (decision 48).
# `Get_Cluster_` takes every identical pop from the clicked one to
# the END OF THE ARRAY (colmove.cpp:66-71), and `Pops_Identical_`
# compares exactly the three fields the walk groups by — so the
# cluster is "this icon and every icon after it" only while the
# grouping holds. Ordered any other way inside a job, a click on
# one cell would move cells elsewhere in the row, with every count
# on screen still correct. Asserted here rather than trusted,
# because the drawing that would break it is not written yet and
# this is what has to fail when somebody writes it.
#
# `pop[]` itself has no order to lean on: appended on growth,
# replaced by the LAST entry on removal, and shuffled outright by
# invasion.cpp:721 when a colony builds Biospheres. The array
# order below is therefore deliberately hostile — a foreign pop
# between two own ones, which is what the engine actually
# produces (doc/pop_order_reading.md).
_mix_pops = [_icon_pop(0, 0), _icon_pop(3, 0), _icon_pop(0, 0),
             _icon_pop(0, 0, conquered=1), _icon_pop(9, 0),
             _icon_pop(0, 0)]
_mix_icons = _ci.icon_pops(_mix_pops, 6, 0)
for _start in range(6):
    if _ci.pop_slot(_mix_pops, 6, 0, _start) is None:
        continue
    _cl_plan = _cm.plan_pickup(_mix_pops, 6, _start)
    if _cl_plan.refused:
        continue
    _slots = sorted(_mix_icons.index(_p) for _p in _cl_plan.indices)
    assert _slots == list(range(_slots[0], _slots[0] + len(_slots))), (
        f"the cluster from pop {_start} is icons {_slots}, which is "
        f"not one run — decision 48's grouping has been broken")
    assert _slots[0] == _mix_icons.index(_start), (
        f"the cluster starts at icon {_slots[0]}, not at the "
        f"clicked one ({_mix_icons.index(_start)})")
    assert _slots[-1] == _slots[0] + len(_cl_plan.indices) - 1
ok("a pop cluster is one contiguous run of icons (decision 48: "
   "only because the column is drawn in the original's order)")
