# smoke-suite area: research_change
#
# Part of the OrionLayer smoke suite — 080b_research_change_the_change_driver_plans.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (95 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# This one did NOT stand inside main(): it is work order 165 part D,
# the live driver that changes the current research.
#
# The 2 check(s) it holds:
#   - the change driver plans three DIFFERENT categories, never the
#     current field and never a placeholder row
#   - the change driver's scratch slots are the protocol's two, and
#     never the reference save

# ── A PLAN THAT PROVES NOTHING LOOKS EXACTLY LIKE ONE THAT DOES ──
#
# `tools/research_change_hd.py` makes the three changes part D asks for.
# Three ways the run could pass while measuring nothing, and all three
# are decided before anything is sent: the CURRENT field is offered in
# change mode (tech.cpp:201, :204), so committing it reads back as a
# match with nothing changed; a placeholder row is billtext message 62
# with app id 0, a row that cannot be chosen; and two entries of one
# category are two changes, not two categories.
import importlib.util as _cd_ilu

_cd_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "tools", "researchchangephases.py")
_cd_spec = _cd_ilu.spec_from_file_location("_change_phases", _cd_path)
_cd = _cd_ilu.module_from_spec(_cd_spec)
_cd_spec.loader.exec_module(_cd)

from core.researchlist import Entry as _CdEntry


def _cd_entry(index, group, field, apps, placeholder=False):
    return _CdEntry(index, group, field, apps, 0, 0, placeholder)


# The shape of a real list: the current field among the offers (entry
# 4, field 60, which is what SAVE4 was on), one empty category, one
# placeholder, and two entries sharing a category.
_cd_offer = [
    _cd_entry(0, 4, 21, (25, 192)),
    _cd_entry(1, 2, 41, (96, 97, 161)),
    _cd_entry(2, 4, 99, (7,)),            # category 4 again
    _cd_entry(3, 8, 10, (0,), placeholder=True),
    _cd_entry(4, 7, 60, (86, 136, 143)),  # the current field
    _cd_entry(5, 0, 0, ()),               # a category offering nothing
    _cd_entry(6, 6, 2, (106,)),
]
_cd_plan = _cd.plan_changes(_cd_offer, 60)
assert [e.index for e in _cd_plan] == [0, 1, 6], \
    [e.index for e in _cd_plan]
assert len({e.group for e in _cd_plan}) == 3
assert all(e.offered and not e.placeholder and e.field != 60
           for e in _cd_plan)
# Nothing left to take is a SHORT plan, never a repeated category — the
# caller reports a short one and would not notice a repeat.
assert [e.index for e in _cd.plan_changes(_cd_offer, 60, want=9)] == \
    [0, 1, 6]
assert _cd.plan_changes([_cd_offer[4]], 60) == []
ok("the change driver plans three DIFFERENT categories, never the "
   "current field and never a placeholder row")

# ── THE SCRATCH SLOTS ARE THE PROTOCOL'S TWO ──
#
# Work order 126 rule 8: SAVE4/SAVE5 only, and never SAVE8. The load
# driver refuses the reference save on its own (its own check); this
# holds the other half, that the driver which USES it asks for nothing
# else. The two are tied here rather than in one module, because they
# are two tools and the rule is about the pair.
assert _cd.SCRATCH == (4, 5), _cd.SCRATCH
assert _ld.REFERENCE_SLOT not in _cd.SCRATCH
for _cd_slot in _cd.SCRATCH:
    try:
        _ld.load_slot(None, _cd_slot)
    except ValueError as _cd_exc:                      # pragma: no cover
        raise AssertionError(
            f"the load driver refuses SAVE{_cd_slot}, which the change "
            f"driver uses as scratch: {_cd_exc}") from _cd_exc
    except Exception:
        pass          # it got past the guard and reached the world
ok("the change driver's scratch slots are the protocol's two, and "
   "never the reference save")
