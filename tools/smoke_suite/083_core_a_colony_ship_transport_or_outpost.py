# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 083_core_a_colony_ship_transport_or_outpost.py.
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
#   - a colony ship, transport or outpost draws the original's HELP.LBX paragraph and never a data lin


# ── THE NON-COMBAT SHIP GETS A PARAGRAPH, NOT THE DATA PANEL ──
#
# Work order 159, closing item 4. `Print_Scanned_Ship_Data_`
# returns early for ship_type 1, 2 and 4 and prints one HELP.LBX
# record instead (flt2.cpp:548-575); HD drew the full data panel
# for all three, which showed MORE than the original.
#
# ASSERTED AS THE RULE. Not "type 1 draws a paragraph" three
# times, but: every type in the original's early-return set draws
# the paragraph and never a data line, and every OTHER type in the
# enum draws the data panel — walked over the whole enum, so a
# type added to `PARAGRAPH_HELP` without a reading of the source,
# or dropped from it, fails here rather than on somebody's screen.
from screens.fleets import fltpanel as _pp_panel
from core.helptext import HelpText
_pp_all = set(range(_pl_ship_spec.SHIP_TYPE_COUNT))
assert set(_pl.PARAGRAPH_HELP) <= _pp_all, (
    f"PARAGRAPH_HELP has a ship_type outside the enum: "
    f"{sorted(set(_pl.PARAGRAPH_HELP) - _pp_all)}")
assert set(_pl.PARAGRAPH_HELP) == {
    _pl_ship_spec.SHIP_TYPE_COLONY,
    _pl_ship_spec.SHIP_TYPE_TRANSPORT,
    _pl_ship_spec.SHIP_TYPE_OUTPOST}, sorted(_pl.PARAGRAPH_HELP)
for _pp_t in sorted(_pp_all):
    _pp_g = _pl_types.SimpleNamespace()
    _pp_g.ships_raw = [_PlShip(loc=0, ship_type=_pp_t).raw]
    _pp_g.stars, _pp_g.player_raw, _pp_g.player_num = [], [], 0
    _pp_got = _pl.panel_lines(0, _pp_g, _pl_parts, _pl_str, None)
    if _pp_t in _pl.PARAGRAPH_HELP:
        assert isinstance(_pp_got, _pl.Paragraph), (
            f"ship_type {_pp_t} still builds a {type(_pp_got).__name__}; "
            f"the original returns before it prints a single data line")
        assert _pp_got.help_id == _pl.PARAGRAPH_HELP[_pp_t]
        assert not hasattr(_pp_got, "head"), (
            "a Paragraph carries a head block — the whole point is "
            "that none of the data lines exists for these ships")
    else:
        assert isinstance(_pp_got, _pl.Panel), (
            f"ship_type {_pp_t} lost its data panel")
# THE THREE RECORDS ARE THE ORIGINAL'S OWN: 0x29 colony, 0xBD
# transport, 0x6D outpost (flt2.cpp:555-561).
assert _pl.PARAGRAPH_HELP == {
    _pl_ship_spec.SHIP_TYPE_COLONY: 0x29,
    _pl_ship_spec.SHIP_TYPE_TRANSPORT: 0xBD,
    _pl_ship_spec.SHIP_TYPE_OUTPOST: 0x6D}, _pl.PARAGRAPH_HELP

# BOTH TEXT STATES, THROUGH COMMITTED FILES AND NEVER THIS
# MACHINE'S EXTRACTION — the clone-only fault, four times over.
#
# `HelpText` takes a `Resources` rather than a `root=`, so it
# cannot go through `derived()`. This hands it a resolver that
# looks in the stand-in tree FIRST and the real tree second: the
# help file comes from `tools/fixtures/derived/`, the labels from
# the committed `assets/shared/help/labels.json`, and nothing
# comes from whatever this machine has extracted. `HelpText` is on
# `_REAL_DERIVED_OK` for the path check's sake; this is not
# leaning on that.
class _PpRes:
    skin = "default"

    def load_json(self, rel, default=None):
        for _base in (DERIVED_ROOT, os.path.dirname(SCREENS_DIR)):
            _p = os.path.join(_base, *rel.split("/"))
            if os.path.exists(_p):
                return __import__("json").load(
                    io.open(_p, encoding="utf-8"))
        return default

_pp_res = _PpRes()
_pp_have = HelpText(_pp_res, "en")
assert _pp_have.available, (
    "the help stand-in did not load — run "
    "`python tools/make_derived_fixtures.py`")
for _pp_t, _pp_id in sorted(_pl.PARAGRAPH_HELP.items()):
    _pp_lines = _pp_panel.paragraph_text(_pp_have, _pl.Paragraph(_pp_id))
    assert _pp_lines == [f"Help {_pp_id} body"], (_pp_t, _pp_lines)
    assert "title" not in "".join(_pp_lines), (
        "the panel is printing the record's TITLE; the original "
        "passes lbx_data->body and nothing else (flt2.cpp:572)")
# ABSENT: an impossible language, which is how this file forces the
# missing state without a temporary directory.
_pp_none = HelpText(_pp_res, "zz")
assert not _pp_none.available, "the 'zz' help file exists?"
for _pp_id in sorted(_pl.PARAGRAPH_HELP.values()):
    _pp_lines = _pp_panel.paragraph_text(_pp_none, _pl.Paragraph(_pp_id))
    assert _pp_lines == [_pp_none.label("missing_title"),
                         _pp_none.label("missing_body")], _pp_lines
    # and NOT the stand-in's text, which is the whole point:
    # an absent help file must not quietly show content.
    assert not any(_l.endswith(" body") for _l in _pp_lines), (
        _pp_lines)
ok("a colony ship, transport or outpost draws the original's "
   "HELP.LBX paragraph and never a data line, every other "
   f"ship_type in the enum still draws the data panel, the three "
   f"records are 0x29/0xBD/0x6D, and with no extracted help the "
   f"panel shows the help popup's own wording rather than falling "
   f"back to the data it must not show")
