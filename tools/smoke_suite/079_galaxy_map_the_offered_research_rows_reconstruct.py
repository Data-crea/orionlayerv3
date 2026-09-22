# smoke-suite area: galaxy_map
#
# Part of the OrionLayer smoke suite — 079_galaxy_map_the_offered_research_rows_reconstruct.py.
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
#   - the offered research rows reconstruct, and the game's own field list is what says so — four ways
#   - sidebar research readout: the original's four cases through core/research, and three lines fit t


# ── THE OFFERED RESEARCH ROWS, RECONSTRUCTED (decision 25) ──────
#
# doc/research_screen_stop1.md §1 found the categories and the offered
# field reconstructible and the choice ROWS not, for two reasons. Work
# order 130 C addressed both: tech[4] is a DERIVATION, not a table
# (techinit.cpp:444-474), and tech_applications @379 now has its header
# source. What must not rot is the rule that the reconstruction is only
# ever used when the game's own field list agrees with it.
from core import researchlist as _rl
from core import research as _rl_res
from core.structs import unverified as _rl_unv

# 1. THE DERIVATION IS THE ORIGINAL'S, INCLUDING ITS LIMIT. The engine
#    exits the game when a fifth application wants one of four slots
#    (techinit.cpp:466-468); here that is an assertion, because a
#    silently dropped fifth row is a list HD would draw one row short
#    and never notice.
_rl_apps = _rl.field_applications()
assert all(len(v) <= _rl.MAX_ROWS for v in _rl_apps.values())
assert all(_rl.APP_FIELD[a] == f
           for f, apps in _rl_apps.items() for a in apps), (
    "an application landed in a field that is not its own")
# Ascending app id, first free slot — so each field's apps come out
# sorted, and every non-sentinel app is placed exactly once.
assert all(list(v) == sorted(v) for v in _rl_apps.values())
_rl_placed = sorted(a for apps in _rl_apps.values() for a in apps)
_rl_want = [a for a, f in enumerate(_rl.APP_FIELD)
            if f not in (_rl.FIELD_INVALID, _rl.FIELD_STARTING_TECH,
                         _rl.FIELD_XENON_TECHNOLOGY)]
assert _rl_placed == _rl_want, (
    len(_rl_placed), len(_rl_want),
    set(_rl_want) ^ set(_rl_placed))
# The hyper-advanced fields have exactly one application each, by the
# switch and not by the table (tech.cpp:1063-1084).
for _rl_f in range(_rl.FIELD_HYPER_FIRST, _rl.FIELD_COUNT_HYPER_LAST + 1):
    assert _rl.hyper_application(_rl_f) == \
        _rl.APP_HYPER_FIRST + _rl_f - _rl.FIELD_HYPER_FIRST

# 2. THE WALK IS THE ORIGINAL'S WALK (tech.cpp:587-600): it tests the
#    chain's first field BEFORE advancing, it stops at the first field
#    at status 2, and it skips the field the player is already
#    researching — which is the whole difference between select mode
#    and change mode's list.
_rl_tf = [0] * _rl_res.FIELD_COUNT
_rl_first = _rl.FIRST_FIELD_IN_GROUP[4]
_rl_tf[_rl_first] = _rl.FIELD_STATUS_OFFERABLE
assert _rl.offered_field(_rl_tf, 4, 0) == _rl_first
assert _rl.offered_field(_rl_tf, 4, _rl_first) == 0, (
    "the field being researched was offered anyway")
_rl_second = _rl.NEXT_FIELD[_rl_first]
_rl_tf[_rl_second] = _rl.FIELD_STATUS_OFFERABLE
assert _rl.offered_field(_rl_tf, 4, _rl_first) == _rl_second
assert _rl.offered_field([0] * _rl_res.FIELD_COUNT, 4, 0) == 0

# 3. A FIELD WITH NOTHING PICKABLE STILL HAS ONE ROW. The original adds
#    a field for billtext message 62 with app id 0 (tech.cpp:624-636),
#    so the wire carries a rectangle there. A reconstruction without it
#    is one row short of the game's list and fails validation — which
#    is the right failure, but it would fail on every such category.
from core.structs import player as _rl_plsp
_rl_ta = [0] * _rl_plsp.TECH_APPLICATIONS_COUNT
_rl_rows, _rl_ph = _rl.offered_rows(_rl_first, _rl_ta, _rl_apps)
assert _rl_rows == (0,) and _rl_ph is True, (_rl_rows, _rl_ph)
for _rl_a in _rl_apps[_rl_first]:
    _rl_ta[_rl_a] = _rl.APP_STATUS_AVAILABLE
_rl_rows, _rl_ph = _rl.offered_rows(_rl_first, _rl_ta, _rl_apps)
assert _rl_rows == _rl_apps[_rl_first] and _rl_ph is False

# 4. THE VALIDATION THE DATA PROVIDES, AND THAT IT CAN SAY NO.
#    Decision 25: a reconstruction without a validation the data
#    itself carries is a guess with extra steps. Build the field list
#    the reconstruction predicts, prove it validates, then break it
#    four ways and require each to be caught.
# Two categories offering, so the field list carries two radios and
# the empty categories' blocks sit between them — the shape the skew
# in §2.4 is about. Group 4 is panel entry 0, group 7 is entry 4.
_rl_other = _rl.FIRST_FIELD_IN_GROUP[7]
_rl_tf[_rl_other] = _rl.FIELD_STATUS_OFFERABLE
for _rl_a in _rl_apps.get(_rl_other, ()):
    _rl_ta[_rl_a] = _rl.APP_STATUS_AVAILABLE
_rl_entries = _rl.reconstruct(_rl_tf, _rl_ta, current_field=0,
                              select_mode=True)
assert [_e.index for _e in _rl_entries if _e.offered] == [0, 4], \
    [(_e.index, _e.field) for _e in _rl_entries]
# Every category still has an entry BLOCK, offered or not
# (tech.cpp:225-231) — eight of them, which is what makes the radio
# indices skew away from the entry indices.
assert sum(1 for _k, _t, _r in _rl.expected_fields(_rl_entries)
           if _k.startswith("block ")) == 8

from core.game_state import FieldInfo as _RlField

def _rl_list(entries, select_mode=True):
    """The FIELD_LIST the game would build for these entries."""
    out = []
    for _kind, _ft, _r in _rl.expected_fields(entries, select_mode):
        _f = _RlField()
        _f.index = len(out)
        _f.field_type = 7 if _ft is None else _ft
        if _r is None:
            _f.x = _f.y = _f.x_end = _f.y_end = 0
        elif _r[2] is None:
            # a radio: origin from the source, end from the art
            _f.x, _f.y = _r[0], _r[1]
            _f.x_end, _f.y_end = _r[0] + 18, _r[1] + 18
        else:
            _f.x, _f.y, _f.x_end, _f.y_end = _r
        _f.hotkey = 0
        out.append(_f)
    return out

_rl_fields = _rl_list(_rl_entries)
assert _rl.validate_against_fields(_rl_entries, _rl_fields) == [], \
    _rl.validate_against_fields(_rl_entries, _rl_fields)
# one row too many
assert _rl.validate_against_fields(_rl_entries,
                                   _rl_fields + _rl_fields[-1:]), \
    "an extra field validated"
# a row in the wrong place — the case a remembered index would hide
_rl_moved = _rl_list(_rl_entries)
_rl_moved[1].y += 1
assert _rl.validate_against_fields(_rl_entries, _rl_moved), \
    "a row one pixel out validated"
# a radio missing: the index skew of doc/tech_change_reading.md §2.4
_rl_skew = [_f for _f in _rl_list(_rl_entries) if _f.field_type != 1]
assert _rl.validate_against_fields(_rl_entries, _rl_skew), \
    "a list with no radio buttons validated"
# and an empty list is not quietly "nothing to disagree with"
assert _rl.validate_against_fields(_rl_entries, [])
assert _rl.validate_against_fields(_rl_entries, None)

# 5. A ROW IS FOUND BY SHAPE, NEVER BY A REMEMBERED INDEX (the rule
#    work order 128 C put into core/livefields.live_field — which this
#    calls rather than carrying a second copy, and mapboxes now imports
#    from the same home).
from core import livefields as _lf
from screens.galaxy_map import mapboxes as _rl_mb
assert _rl_mb.live_field is _lf.live_field and _rl_mb.rect is _lf.rect, \
    "mapboxes has its own copy of live_field again"
_rl_e = next(_e for _e in _rl_entries if _e.offered)
_rl_hit = _rl.row_field(_rl_fields, _rl_e, 0)
assert _rl_hit is not None and _lf.rect(_rl_hit) == _rl_e.row_rect(0)
# The same row, in a list where every index has moved.
_rl_shifted = _rl_list(_rl_entries)[:1] + _rl_list(_rl_entries)
for _i, _f in enumerate(_rl_shifted):
    _f.index = _i
_rl_hit2 = _rl.row_field(_rl_shifted, _rl_e, 0)
assert _rl_hit2 is not None and _lf.rect(_rl_hit2) == _rl_e.row_rect(0)
# And absent from a list that does not hold it: no send, not a guess.
assert _rl.row_field([], _rl_e, 0) is None
ok("the offered research rows reconstruct, and the game's own field "
   "list is what says so — four ways of disagreeing, all caught")

# THE SIDEBAR'S RESEARCH READOUT — the original's four cases (work
# order 129 D), transcribed from Print_Main_Screen_Data_
# (mainscr_main.cpp:186-247) through core/research.py. Until then HD
# printed accumulated over produced, which was a deviation nothing
# marked. The row now carries up to three lines, so it is also
# RENDERED at all four shipped sizes and the label must survive.
if slow("sidebar_research"):
    from screens.galaxy_map import sidebar as _rr_sb
    from core import research as _rr_research

    class _RrPlayer:
        def __init__(self, **kw):
            self.research_breakthrough = 0
            self.current_research_field = 60
            self.research_accumulated = 412
            self.research_produced = 44
            self.tech_fields = [0] * _rr_research.FIELD_COUNT
            self.tech_fields[60] = 2
            for _k, _v in kw.items():
                setattr(self, _k, _v)
    _rr_labels = {"research": "Research", "research_unit": "RP",
                  "breakthrough": "Breakthrough", "no_research": "None"}
    # 1. a running project: the turns the original's own loop gives, and
    #    the points per turn below them. 412 at 44 with cost 900 is the
    #    pair measured beside the native frame on SAVE4 (18), 456 on
    #    SAVE5 (17).
    assert _rr_research.FIELD_COST[60] == 900, _rr_research.FIELD_COST[60]
    for _rr_acc, _rr_want in ((412, "~18 turns"), (456, "~17 turns")):
        _rr_out = _rr_sb.research_readout(
            _RrPlayer(research_accumulated=_rr_acc), _rr_labels)
        assert _rr_out == ("Research", (_rr_want,), "44 RP"), _rr_out
    # 2. the chance line appears only above zero, and then above the turns
    _rr_out = _rr_sb.research_readout(
        _RrPlayer(research_accumulated=1000), _rr_labels)
    assert _rr_out == ("Research", ("11%", "~5 turns"), "44 RP"), _rr_out
    # 3. research standing still: "0 RP", and nothing else
    assert _rr_sb.research_readout(
        _RrPlayer(research_produced=0), _rr_labels) == \
        ("Research", ("0 RP",), ""), "the stalled case"
    # 4. the two words
    assert _rr_sb.research_readout(
        _RrPlayer(research_breakthrough=1), _rr_labels)[1] == \
        ("Breakthrough",)
    assert _rr_sb.research_readout(
        _RrPlayer(current_research_field=0), _rr_labels)[1] == ("None",)
    # 5. IT FITS, at all four shipped sizes, without eating the label:
    #    rendered, and the label's ink must be inside the row's box and
    #    above the first value line.
    for _rr_W, _rr_H in ((1366, 768), (1920, 1080), (2560, 1440),
                         (3840, 2160)):
        _rr_app, _ = _pv.build_screen(_rr_W, _rr_H)
        _rr_app.dispatcher.switch_to("galaxy_map")
        _rr_scr = _rr_app.dispatcher.active
        _rr_box = _rr_scr.box_rect("sb_research_text")
        assert _rr_box, (_rr_W, "no sb_research_text box")
        _rr_rect = pygame.Rect(*_rr_app.layout.rect(_rr_box))
        _rr_surf = pygame.Surface((_rr_W, _rr_H))
        _rr_surf.fill((0, 0, 0))
        _rr_sb.draw_text_block(
            _rr_surf, _rr_app.style, _rr_app.layout, _rr_app.layout.rect(_rr_box),
            "Research", ("11%", "~18 turns"), "44 RP", False, 1.0, "center",
            _rr_sb.DEFAULT_FONTS)
        _rr_px = pygame.surfarray.array3d(_rr_surf).transpose(1, 0, 2)
        _rr_rows = np.where(_rr_px.any(axis=(1, 2)))[0]
        assert len(_rr_rows), (_rr_W, "the research row drew nothing")
        assert _rr_rect.top <= _rr_rows.min() and \
            _rr_rows.max() <= _rr_rect.bottom, (
            f"{_rr_W}x{_rr_H}: the three-line research row inks rows "
            f"{_rr_rows.min()}..{_rr_rows.max()}, its box is "
            f"{_rr_rect.top}..{_rr_rect.bottom}")
    ok("sidebar research readout: the original's four cases through "
       "core/research, and three lines fit the row at four sizes")
