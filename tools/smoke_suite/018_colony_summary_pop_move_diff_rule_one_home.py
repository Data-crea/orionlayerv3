# smoke-suite area: colony_summary
#
# Part of the OrionLayer smoke suite — 018_colony_summary_pop_move_diff_rule_one_home.py.
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
#   - pop-move diff rule (one home, two tools; a second colony's pop or production fails it, and pop_g


# ── THE POP-MOVE DIFF RULE, AND IT MUST BE ABLE TO FAIL ──
#
# "Exactly one colony's bytes changed" was what both acceptance
# tools asserted, and it is not what the game guarantees:
# `Pass_Out_Imports_` (colcalc_main.cpp:208) redistributes the
# whole player's food on every recalculation, so a colony nobody
# touched comes back with a different `imports` — and a NEEDY one
# with a different `pop_growth` too. The rule names those fields
# and refuses everything else, which is stricter than the old one
# about the moved colony, where any byte difference passed.
#
# A rule nobody has seen fail is a tolerance. Three synthetic
# diffs, each the shape the rule exists to catch.
from screens.colony_summary import colonymove as _cmv
from core.structs import colony as _ccs

def _rec(**fields):
    _b = bytearray(_ccs.SIZE)
    for _name, _val in fields.items():
        _off, _fmt = next((_e[1], _e[2]) for _e in _ccs.SPEC.fields
                          if _e[0] == _name)
        _s.pack_into("<h" if _fmt.startswith("i16") else "<b",
                     _b, _off, _val)
    return bytes(_b)

_base = bytes(_ccs.SIZE)
_verdict = lambda _a, _b: _cmv.move_diff_verdict(
    _a, _b, 0, _ccs.SPEC, _ccs.parse)

# (a) a SECOND colony whose pop[] changed — the failure the whole
#     acceptance exists for, and the one thing that may never be
#     allowed on any colony but the moved one.
_pop_off = next(_e[1] for _e in _ccs.SPEC.fields if _e[0] == "pop")
_b2 = bytearray(_base); _s.pack_into("<I", _b2, _pop_off, 0x280)
_ok_a, _lines_a = _verdict([_base, _base], [_base, bytes(_b2)])
assert not _ok_a, (
    "the rule accepted a second colony whose pop[] changed — that "
    "is the wrong-colony failure and it is what the acceptance is "
    "for; a rule that passes it is a tolerance")
assert any("pop changed" in _l for _l in _lines_a), _lines_a

# (b) a second colony whose production changed. Nothing on the
#     pop-move path writes another colony's production:
#     `Recalculate_Colony_` is called for the moved colony only.
_pr_off = next(_e[1] for _e in _ccs.SPEC.fields
               if _e[0] == "production")
_b3 = bytearray(_base); _s.pack_into("<h", _b3, _pr_off, 7)
_ok_b, _lines_b = _verdict([_base, _base], [_base, bytes(_b3)])
assert not _ok_b, (
    "the rule accepted a second colony whose production changed; "
    "Pass_Out_Imports_ writes imports and Post_Import_Computing_ "
    "writes pop_growth/pop_roundoff/specialty, and neither writes "
    "production on a colony that was not moved")
assert any("production changed" in _l for _l in _lines_b), _lines_b

# (c) a NON-NEEDY colony whose pop_growth changed.
#     `Post_Import_Computing_` is called only for entries of
#     `needy_colony_indices` (colcalc_main.cpp:341-352), and
#     neediness IS readable from the record — `production[FOOD] -
#     maintenance[FOOD] < 0`, colcalc_main.cpp:219 — so the rule
#     conditions on it rather than allowing the field everywhere.
_pg_off = next(_e[1] for _e in _ccs.SPEC.fields if _e[0] == "pop_growth")
_b4 = bytearray(_base); _s.pack_into("<h", _b4, _pg_off, 51)
_ok_c, _lines_c = _verdict([_base, _base], [_base, bytes(_b4)])
assert not _ok_c, (
    "the rule accepted pop_growth on a colony that is not needy; "
    "Post_Import_Computing_ runs for needy colonies only, and "
    "allowing the field everywhere is the tolerance this check "
    "exists to refuse")
assert any("NOT needy" in _l for _l in _lines_c), _lines_c

# (c2) THE SAME FIELD ON A NEEDY COLONY IS ALLOWED, or the rule
#      would refuse what the game actually does and the live proof
#      could never go green.
_mt_off = next(_e[1] for _e in _ccs.SPEC.fields if _e[0] == "maintenance")
_b5 = bytearray(_base); _s.pack_into("<h", _b5, _mt_off, 5)
_b6 = bytearray(_b5); _s.pack_into("<h", _b6, _pg_off, 51)
_ok_c2, _lines_c2 = _verdict([_base, bytes(_b5)],
                             [_base, bytes(_b6)])
assert _ok_c2, _lines_c2
assert any("is needy" in _l for _l in _lines_c2), _lines_c2

# (c3) AND `imports` IS ALLOWED ON ANY of the owner's colonies,
#      needy or not — Pass_Out_Imports_ writes it in the first
#      loop, before the needy list exists.
_im_off = next(_e[1] for _e in _ccs.SPEC.fields if _e[0] == "imports")
_b7 = bytearray(_base); _s.pack_into("<h", _b7, _im_off, 1)
_ok_c3, _lines_c3 = _verdict([_base, _base], [_base, bytes(_b7)])
assert _ok_c3, _lines_c3

# AND AN UNREADABLE RECORD IS A FAILURE, not a skip.
_ok_d, _ = _verdict([_base, _base], [_base, b"\x00\x01"])
assert not _ok_d, "a changed record that will not parse must fail"

# Both acceptance tools read the ONE rule, not a copy each.
for _tool in ("colony_move_hd.py", "colony_move_probe.py"):
    _src = open(os.path.join(_proj, "tools", _tool),
                encoding="utf-8").read()
    assert "move_diff_verdict" in _src, (
        f"{_tool} does not call colonymove.move_diff_verdict — the "
        f"rule has to have one home, or the two drift and the "
        f"acceptance means whichever was run last")
ok("pop-move diff rule (one home, two tools; a second colony's "
   "pop or production fails it, and pop_growth only on a "
   "colony the food balance says was needy)")
