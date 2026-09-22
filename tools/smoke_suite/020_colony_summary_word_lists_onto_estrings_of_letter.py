# smoke-suite area: colony_summary
#
# Part of the OrionLayer smoke suite — 020_colony_summary_word_lists_onto_estrings_of_letter.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (92 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 2 check(s) it holds:
#   - word lists onto estrings ( of letter for letter, gravities split by `%sravity`)
#   - word lists onto estrings NOT COMPARED (: no estrings_<lang>.json on this disk — run `python tool


# ── THE OPTION STRINGS ARE A SECOND FILE AND A SECOND WALK ──
#
# `COLBLDG::Selection_Name_` (colbldg.cpp:796) sends a BUILDING id
# to techname.lbx and an OPTION id to estrings.lbx, and the
# reference save takes the OPTION branch on every row —
# producing[0] is -2, TRADE_GOODS. The column was blank for that
# reason, not for want of a wider techname walk.
from core import estrings as _es
assert _es.ESTRINGS_COUNT == 812, (
    "ESTRINGS_COUNT moved. It is estrings.h:4 and Load_E_Strings_ "
    "walks exactly that many strings (estrings.cpp:11-37), so it "
    "is asserted against the file rather than taken from it")
# THE SIXTEEN OPTION IDS ARE Option_String_'s OWN CASES, and the
# table is pinned entry by entry rather than spot-checked: a
# switch transcribed into a dict is exactly the kind of table
# that goes stale one case at a time.
assert len(_es.OPTION_STRINGS) == 17, (
    f"{len(_es.OPTION_STRINGS)} option ids, expected 17 — the "
    f"count is Option_String_'s CASE LABELS, not its distinct "
    f"return values: SEPARATOR, NONE and 0 are three labels "
    f"falling through to one E_Strings_ call (colbldg.cpp:2356)")
assert len(set(_es.OPTION_STRINGS.values())) == 15, (
    "15 distinct E_Strings_ indices behind 17 ids — the "
    "three-way fall-through is the only sharing in the switch")
assert _es.OPTION_STRINGS[-2] == 0x21D and _es.OPTION_STRINGS[-3] == 0x142
assert _es.OPTION_STRINGS[0] == _es.OPTION_STRINGS[-1] == \
    _es.OPTION_STRINGS[-9] == 0x00C, (
        "NONE, SEPARATOR and 0 no longer share E_Strings_(0x00C). "
        "They share it in the source (colbldg.cpp:2356-2359) and "
        "that string is EMPTY, which is why an empty cell in the "
        "BUILDING column is correct and not a missing file")
assert _es.OPTION_STRINGS[-5] == 0x0B2 and _es.OPTION_STRINGS[-6] == 0x0B1, (
    "WORKER/SCIENTIST no longer cross. -5 is WORKER -> 0x0B2 and "
    "-6 is SCIENTIST -> 0x0B1, and the pair is out of numeric "
    "order in the source too — it is the crossing that proves the "
    "table was transcribed from Option_String_ and not sorted "
    "into agreement with itself")
_es_strings = _es.EStrings(settings.get("language", "en"))
assert _es_strings.state in ("ok", "missing", "stale"), _es_strings.state
if _es_strings.state == "ok":
    assert len(_es_strings.strings) == _es.ESTRINGS_COUNT
    # PINNED, AND THIS IS THE CHECK THAT CATCHES THE HEADER.
    # Walking the LBX entry from offset 0 instead of from 4 put
    # every string ONE INDEX LATE and still produced 812 plausible
    # strings — Trade Goods sat at 0x21E, which is Transport Ship.
    # `Farload_Library_Data_` reads total_count and element_size,
    # two uint16s, then seeks past them (farload.cpp:88-92, :107).
    # Three anchors from Option_String_'s own switch; a walk off
    # by one fails all three.
    for _entry, _want in ((0x142, "Housing"), (0x21D, "Trade Goods"),
                          (0x21E, "Transport Ship")):
        _got = _es_strings.string(_entry)
        assert _got == _want, (
            f"E_Strings_({_entry:#05x}) is {_got!r}, expected "
            f"{_want!r} — the walk has slipped, most likely past "
            f"the 4-byte entry header (farload.cpp:107)")
    assert _es_strings.string(0x00C) == "", (
        "E_Strings_(0x00C) is not the empty string any more. It "
        "is what NONE, SEPARATOR and 0 resolve to, and an empty "
        "entry that reads as absent makes 'the original prints "
        "nothing' indistinguishable from 'no such index'")
    assert _es_strings.string(_es.ESTRINGS_COUNT) is None, (
        "an out-of-range index returns something. None must mean "
        "NO SUCH ENTRY and '' must mean a blank entry")
    # THE WORD LISTS ARE NOT SWITCHED, AND THIS IS WHY THEY
    # STAY. 20 of the 23 entries in layout.json's four
    # enum-indexed lists are letter for letter the game's own
    # (estrings.cpp:155-169, :204-213); the three that differ are
    # the gravities, and they differ because the COLONY SUMMARY
    # supplies half the word. E_Strings_(0x4A)'s gravity slot is
    # `%sravity` and the table holds 'Normal G'
    # (colsum.cpp:1194-1200), so 'Normal Gravity' exists only
    # once the two are joined. Pinned because a future reader who
    # sees 'Low G' in the table and 'Low' in layout.json will
    # otherwise "fix" one of them.
    #
    # WRITTEN AS "23 of the 26" UNTIL 10 SEPTEMBER 2026, when the
    # comparison stopped being prose and became the loop below.
    # The four tables hold 5 + 5 + 3 + 10 = 23 entries, of which
    # the three gravities differ, so it is 20 of 23 — and the
    # count nobody could run was wrong in BOTH halves. Decision
    # 36's rule: a number a document carries and no check reads
    # is an intention. This is the same shape as decision 51's
    # "fifty" cell plates, in the same file, four days apart.
    _es_tables = {
        # MOX::_planet_size_string, estrings.cpp:155-159
        ("words", "sizes"): (0x2AB, 0x1E0, 0x173, 0x168, 0x143),
        # MOX::_mineral_class_string, estrings.cpp:161-165
        ("words", "minerals"): (0x2AC, 0x1A7, 0x2AD, 0x1C2, 0x2AE),
        # MOX::_planet_gravity_string, estrings.cpp:167-169
        ("words", "gravities"): (0x2AF, 0x2B0, 0x2B1),
        # MOX::_planet_climate_string, estrings.cpp:204-213.
        # NOT under `words` — climate has one home at
        # list.climates, and it is read from there by the row
        # renderer and the output panel alike (words._note).
        ("list", "climates"): (0x21B, 0x2CF, 0x2D0, 0x2D1, 0x2D2,
                               0x18F, 0x1F5, 0x0B8, 0x2D3, 0x12F),
    }
    _es_lay = _sjson.load(open(os.path.join(
        SCREENS_DIR, "colony_summary", "layout.json"),
        encoding="utf-8"))
    _es_same, _es_split, _es_total = 0, [], 0
    for (_blk, _key), _ids in _es_tables.items():
        _ours = _es_lay[_blk][_key]
        assert len(_ours) == len(_ids), (
            f"{_blk}.{_key} holds {len(_ours)} words against "
            f"{len(_ids)} E_Strings_ calls in the original's "
            f"table. ORDER IS THE ENUM (words._note), so a list "
            f"that has gained or lost an entry is indexed wrong "
            f"from that entry on and draws a neighbour's word")
        for _i, (_id, _word) in enumerate(zip(_ids, _ours)):
            _game = _es_strings.string(_id)
            _es_total += 1
            assert _game, (
                f"E_Strings_({_id:#05x}) is {_game!r} — "
                f"{_blk}.{_key}[{_i}] has no game string behind "
                f"it any more, so nothing here can be compared")
            if _game == _word:
                _es_same += 1
                continue
            # THE ONLY LEGAL DIFFERENCE IS THE SPLIT WORD. The
            # colony summary's format supplies 'ravity' and the
            # table supplies the 'G', so our list holds the bare
            # quality and the game's string carries a suffix we
            # must NOT repeat. Anything else is a wording drift
            # and is what this loop is here to catch.
            assert (_blk, _key) == ("words", "gravities"), (
                f"{_blk}.{_key}[{_i}] is {_word!r} where the "
                f"game's E_Strings_({_id:#05x}) is {_game!r}. "
                f"These lists are our own wording (decision 15) "
                f"and they are allowed to differ — but only "
                f"where a reason is written down, and the "
                f"gravities are the only entry that has one")
            assert _game == _word + " G", (
                f"gravities[{_i}] is {_word!r} and the game's "
                f"string is {_game!r}; the split is exactly the "
                f"' G' that E_Strings_(0x4A)'s `%sravity` slot "
                f"completes (colsum.cpp:1194-1200). A different "
                f"suffix means the split moved and 'Normal "
                f"Gravity' no longer assembles")
            _es_split.append(_word)
    assert _es_total == 23 and _es_same == 20 and \
        len(_es_split) == 3, (
            f"{_es_same} of {_es_total} words identical, "
            f"{len(_es_split)} split — the pinned shape is 20 of "
            f"23 with the three gravities split. Both numbers "
            f"are asserted, because a table that grows and a "
            f"table that drifts are different faults")
    assert "%sravity" in (_es_strings.string(0x4A) or ""), (
        "E_Strings_(0x4A) no longer splits the word 'Gravity'. "
        "The scan box's format supplies 'ravity' and "
        "_planet_gravity_string supplies 'Normal G'; that split "
        "is why words.gravities holds the bare quality")
    assert _es_strings.string(0x2B0) == "Normal G", (
        "_planet_gravity_string[NORMAL_G] is not 'Normal G'. It "
        "looks like an enum name in title case and is in fact the "
        "game's own string — see words._note")
    _es_note = (f"{sum(1 for t in _es_strings.strings if t)} "
                f"non-empty of {_es.ESTRINGS_COUNT}, "
                f"{_es_same}/{_es_total} words identical")
    ok(f"word lists onto estrings ({_es_same} of {_es_total} "
       f"letter for letter, {len(_es_split)} gravities split by "
       f"`%sravity`)")
else:
    _es_note = (f"{_es_strings.state} — run "
                f"`python tools/estrings_extract.py`")
    # AND THE COMPARISON IS NOT SILENTLY SKIPPED. Without the
    # player's estrings.lbx there is nothing to compare against,
    # which is a legal state — but a check that reports nothing
    # in it is indistinguishable from one that passed, and that
    # is the fault the figure clip check carried below.
    ok(f"word lists onto estrings NOT COMPARED "
       f"({_es_strings.state}: no estrings_<lang>.json on this "
       f"disk — run `python tools/estrings_extract.py`)")
