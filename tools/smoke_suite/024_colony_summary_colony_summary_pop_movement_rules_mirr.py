# smoke-suite area: colony_summary
#
# Part of the OrionLayer smoke suite — 024_colony_summary_colony_summary_pop_movement_rules_mirr.py.
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
#   - colony summary pop-movement rules mirrored (four rules, the pick-up refusal, and the count a par


# ── The pop-movement rules, mirrored (decision 33) ──
# Four drop rules plus a refusal at the pick-up, each asserted
# separately and each made to BITE — a rule that four others
# cover is a rule nobody is testing.
#
# THE SHAPE IS A COUNT, NOT A BOOLEAN, and that is the check
# worth having. Send_Cluster_ returns mid-cluster on a refusal
# (colmove.cpp:168-173), so a mirror answering yes/no would say
# "this works" and then move seven of twelve — decision 33's own
# failure mode one level finer.
from screens.colony_summary import colonymove as _cm
from core.structs import colony as _cst

def _pop(nibble=0, job=0, assigned=True, conquered=0):
    return (nibble | (job << 7)
            | (_cst.POP_MASK_ASSIGNED if assigned else 0)
            | (conquered << 10))

# RULE 0 — the pick-up refuses a native outright, colmove.cpp:59.
# Not one of the four: it is in a different function, and the
# fundament's count missed it until 4 September 2026.
assert _cm.plan_pickup([_pop(9)], 1, 0).refused == \
    _cm.REFUSE_NATIVE_PICKUP, "a native must not be picked up"
assert _cm.plan_pickup([_pop(0)], 1, 0).refused is None

# RULE 1 — natives take neither research nor industry
# (colmove.cpp:524-529), and the `== 6` arm is transcribed.
for _job, _want in ((_cm.ECON_RESEARCH, _cm.REFUSE_NATIVE_JOB),
                    (_cm.ECON_INDUSTRY, _cm.REFUSE_NATIVE_JOB),
                    (_cm.ECON_FOOD, None)):
    _p = _cm.plan_drop([_pop(9, 0)], 1, 255, _cm.Cluster([0]), _job)
    assert _p.reason == _want, (_job, _p)
# The `|| pop_state == 6` arm is transcribed even though
# Pop_To_Pop_State_ cannot return 6 (colony.cpp:1240). Asserted
# BEHAVIOURALLY by forcing the state, because a text search for
# "state == 6" passes on this module's own docstring, which says
# the words — the first version of this check did exactly that
# and survived the arm being deleted.
_real_state = _cm.pop_state
try:
    _cm.pop_state = lambda _w: 6
    _six = _cm.plan_drop([_pop(0, 0)], 1, 255, _cm.Cluster([0]),
                         _cm.ECON_RESEARCH)
finally:
    _cm.pop_state = _real_state
assert _six.reason == _cm.REFUSE_NATIVE_JOB, (
    f"with pop_state forced to 6 the native rule did not fire "
    f"({_six}) — colonymove no longer transcribes the "
    f"`|| pop_state == 6` arm of colmove.cpp:524. That branch is "
    f"unreachable in orion2re today, which is exactly why it is "
    f"written down rather than reasoned about: the condition "
    f"costs one `or`")

# RULE 2 — androids keep the job they have (colmove.cpp:531-537),
# and the path that never consults the rules lets one back onto
# its own column.
assert _cm.plan_drop([_pop(8, 1)], 1, 255, _cm.Cluster([0]),
                     _cm.ECON_RESEARCH).reason == _cm.REFUSE_ANDROID
assert _cm.plan_drop([_pop(8, 1)], 1, 255, _cm.Cluster([0]),
                     _cm.ECON_INDUSTRY).reason is None, (
    "an android dropped back on its own column takes the "
    "re-flag path at colmove.cpp:165 and never reaches rule 2")

# RULE 3 — at most 42 in a job (colmove.cpp:539-543). Asserted as
# a COUNT: forty already there and a cluster of five gives two
# landed and three carried, which is the whole reason plan_drop
# does not return a boolean.
_full = [_pop(0, 1)] * 40 + [_pop(0, 0)] * 5
_fc = _cm.plan_pickup(_full, 45, 40)
assert len(_fc.indices) == 5, _fc
_fp = _cm.plan_drop(_full, 45, 255, _fc, _cm.ECON_INDUSTRY)
assert (_fp.landed, _fp.carried, _fp.reason) == (
    2, 3, _cm.REFUSE_JOB_FULL), (
    f"forty in industry and a cluster of five must land TWO and "
    f"carry three, stopping on the job limit; got {_fp}")
assert _fp.stopped_at == 42, _fp

# RULE 4 — a farmer needs max_farms > sum (colmove.cpp:546-554).
# The field holds 0 or 255 and nothing between, so the rule is
# binary in practice: a planet that cannot farm refuses its FIRST
# farmer, and one that can never refuses here at all.
_w3 = [_pop(0, 1)] * 3
assert _cm.plan_drop(_w3, 3, 0, _cm.Cluster([0, 1, 2]),
                     _cm.ECON_FOOD).reason == _cm.REFUSE_NO_FARMING
assert _cm.plan_drop(_w3, 3, 0, _cm.Cluster([0, 1, 2]),
                     _cm.ECON_FOOD).landed == 0
assert _cm.plan_drop(_w3, 3, 255, _cm.Cluster([0, 1, 2]),
                     _cm.ECON_FOOD).reason is None
assert _cm.plan_drop(_w3, 3, 0, _cm.Cluster([0, 1, 2]),
                     _cm.ECON_RESEARCH).landed == 3

# A PARTIAL DROP IS THE NORMAL CASE, not an edge one: an android
# in the middle of a cluster lands everyone before it and nobody
# after.
_mix = [_pop(0, 1), _pop(0, 1), _pop(8, 1)]
_mp = _cm.plan_drop(_mix, 3, 255, _cm.Cluster([0, 1, 2]),
                    _cm.ECON_RESEARCH)
assert (_mp.landed, _mp.carried, _mp.stopped_at) == (2, 1, 2), _mp

# THE CLUSTER IS NOT THE RUN UNDER THE CURSOR. Get_Cluster_ scans
# to the END of the array and takes every identical pop
# (colmove.cpp:66-71), so a group split by a different one still
# comes along in full.
_split = [_pop(0, 0), _pop(0, 1), _pop(0, 0)]
assert _cm.plan_pickup(_split, 3, 0).indices == (0, 2), (
    "a group split by a different pop must still be taken whole")

# PLANNING MUST NOT MUTATE. A plan that changed the state it
# planned against would be right exactly once.
_before = list(_full)
_cm.plan_drop(_full, 45, 255, _fc, _cm.ECON_INDUSTRY)
assert _full == _before, "plan_drop mutated the caller's pops"

# OUR OWN WORDING, per decision 15 — every reason has a string
# and the count lines carry their placeholders.
_mv = _out_cfg["move"]
for _r in (_cm.REFUSE_NATIVE_PICKUP, _cm.REFUSE_NATIVE_JOB,
           _cm.REFUSE_ANDROID, _cm.REFUSE_JOB_FULL,
           _cm.REFUSE_NO_FARMING):
    assert _mv.get(_r), (
        f"move.{_r} has no wording. We refuse before injecting, so "
        f"the sentence is ours to own (decision 15) — the "
        f"original's ESTRINGs are not ours to copy, and one of "
        f"the two it uses describes a rule its code does not "
        f"implement (open fix 8)")
for _ph in ("{landed}", "{carried}"):
    assert _ph in _mv["partial"], (
        f"move.partial lost {_ph} — the message is about HOW MANY "
        f"land, because the drop is divisible")
ok("colony summary pop-movement rules mirrored (four rules, the "
   "pick-up refusal, and the count a partial drop lands)")
