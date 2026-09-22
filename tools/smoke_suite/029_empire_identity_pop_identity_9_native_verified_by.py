# smoke-suite area: empire_identity
#
# Part of the OrionLayer smoke suite — 029_empire_identity_pop_identity_9_native_verified_by.py.
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
#   - pop identity: 9 = native verified by three sources, 8 and conquered still open, and the split is


# ── The nibble marking is SPLIT, and it has to stay split ────
# 9 = native has three independent sources as of 5 September 2026
# (data, picture, the game's own label); 8 = android and the
# conquered bit have none, because no save this project holds
# contains either. Those are different claims and the difference
# is the whole value of the day's work — "verified" with a
# footnote is how a reader stops reading. A marking with no check
# is an intention (the help panel's lesson), so this is the check.
_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _src(*parts):
    return open(os.path.join(_root_dir, *parts)).read()

_nib_spec = _src("core", "structs", "colony.py")
for _needle in ("9 = NATIVE IS VERIFIED", "8 = ANDROID IS NOT VERIFIED",
                "the DATA", "the PICTURE", "OWN WORDS",
                "fixture_natives_3502.5.GAM", "b1f1aa466716d6c0"):
    assert _needle in _nib_spec, (
        f"core/structs/colony.py no longer records {_needle!r}. The "
        f"nibble claim rests on a named save and three named "
        f"sources; a claim that stops naming them is back to being "
        f"three readings of one tree (decision 23)")
_nib_move = _src("screens", "colony_summary", "colonymove.py")
assert "still UNVERIFIED" in _nib_move, (
    "colonymove's android rule no longer says it is unverified — "
    "no save in this project contains an android, so the rule is "
    "mirrored from the source alone")
_nib_status = _src("v3_projektstatus.md")
for _needle in ("VERIFIED: nibble 9 = native",
                "STILL OPEN: nibble 8 = android"):
    assert _needle in _nib_status, (
        f"v3_projektstatus.md no longer carries {_needle!r}")
# And the behaviour the marking is about still holds both ways.
assert _cm.pop_state(_icon_pop(9)) == _cm.POP_STATE_NATIVE
assert _cm.pop_state(_icon_pop(8)) == _cm.POP_STATE_ANDROID
assert _cst.POP_NATIVE == 9 and _cst.POP_ANDROID == 8
ok("pop identity: 9 = native verified by three sources, 8 and "
   "conquered still open, and the split is asserted")
