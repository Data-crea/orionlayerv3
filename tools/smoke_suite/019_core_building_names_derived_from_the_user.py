# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 019_core_building_names_derived_from_the_user.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (90 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 1 check(s) it holds:
#   - building names, derived from the user's TECHNAME.LBX ()


# ── THE BUILDING NAMES ARE THE USER'S OWN, AND DERIVED ──
#
# The help-text pattern (decision 38): extracted from the
# player's TECHNAME.LBX, never committed, decoded at load time,
# format-versioned, and an absent file is a state the column
# explains rather than an empty cell. **REPORTED, NOT SKIPPED** —
# this check counts either way, so "the count must not go down"
# stays a rule a clone can follow (decision 42).
from core import buildnames as _bn
assert _bn.BUILDING_FIRST_STRING == _bn.TECH_FIELD_COUNT + _bn.TECH_APP_COUNT
assert (_bn.TECH_FIELD_COUNT, _bn.TECH_APP_COUNT, _bn.BUILDING_COUNT) \
    == (83, 212, 49), (
        "the string walk's offsets moved. They are orion2_consts.h "
        "enums with static_asserts beside them (TECH_FIELD_COUNT, "
        "TECH_APP_COUNT, BUILDING_COUNT) and the building block's "
        "position is computed from them, not measured off the file")
# An id outside the building table is NOT a building — it is a
# ship or one of Option_String_'s options, which is the other
# branch of Selection_Name_ (colbldg.cpp:796-802) and a different
# string source. -2 is COLONY_PRODUCTION_TRADE_GOODS.
#
# **ID 0 IS THE BOUND THAT WAS WRONG, and this assertion is why
# it stayed wrong.** It read `is_building(0)` and passed, because
# it had been written from the same range the code had rather
# than from the predicate. `Colony_Production_Is_Building_` is
# `id > BUILDING_NO_BUILDING && id < BUILDING_COUNT`
# (colbldg.h:16) — 1..48 — and `Option_String_` claims 0 with an
# explicit `case 0:` returning the empty string
# (colbldg.cpp:2356-2359). Both bounds are now spelled with the
# named constants, so a check and the code cannot agree with each
# other while both disagree with the source.
assert not _bn.is_building(_bn.BUILDING_NO_BUILDING), (
    "is_building(0) is True again. 0 is BUILDING_NO_BUILDING and "
    "belongs to Option_String_, which returns the empty string "
    "for it; treating it as a building prints _buildings[0], "
    "'No Building', where the original prints nothing")
assert _bn.is_building(1) and _bn.is_building(_bn.BUILDING_COUNT - 1)
assert not _bn.is_building(_bn.BUILDING_COUNT) and not _bn.is_building(-2)
assert not _bn.is_building(None)
_bn_names = _bn.BuildingNames(settings.get("language", "en"))
assert _bn_names.state in ("ok", "missing", "stale"), _bn_names.state
if _bn_names.state == "ok":
    # PINNED AGAINST THE REFERENCE SAVE'S OWN LANGUAGE BLOCK.
    # Three names at known ids, so a walk that slipped by one
    # string fails here rather than showing a plausible wrong
    # word — the failure this kind of table produces.
    for _id, _want in ((1, None), (7, "Automated Factory"),
                       (48, None)):
        _got = _bn_names.building(_id)
        if _want is not None:
            assert _got == _want, (
                f"building {_id} is {_got!r}, expected {_want!r} — "
                f"the string walk has slipped")
        else:
            assert _got, f"building {_id} has no name"
    assert _bn_names.building(-2) is None, (
        "-2 is TRADE_GOODS, an option and not a building; naming "
        "it out of the building table would be the wrong branch "
        "of Selection_Name_")
    _bn_note = f"{len(_bn_names.names)} names"
else:
    _bn_note = (f"{_bn_names.state} — run "
                f"`python tools/techname_extract.py`")
# The column explains an absent file instead of drawing nothing.
_bn_cfg = d.screens["colony_summary"]._data.get("build", {})
assert _bn_cfg.get("names_missing"), (
    "layout.json has no wording for a missing name file, so the "
    "BUILDING column would be indistinguishable from a colony "
    "that builds nothing")
for _cite in ("Calculate_Current_Production_Turn_Count_", "OPEN"):
    assert _cite in _bn_cfg.get("_turns_note", ""), (
        f"build._turns_note no longer carries {_cite!r} — the "
        f"'- 8t' suffix is not drawn and the reason has to travel "
        f"with the omission")
ok(f"building names, derived from the user's TECHNAME.LBX "
   f"({_bn_note})")
