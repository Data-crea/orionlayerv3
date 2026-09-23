# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 080h_core_the_research_screen_waits_for_the.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (102 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# This one did NOT stand inside main(): it is work order 166 part A,
# the glimpse of the original on entry.
#
# The 2 check(s) it holds:
#   - an empty field list is WAITING and draws nothing; a list that is
#     there and disagrees hands over on the first frame
#   - while it waits, the window is the galaxy map and not the game's
#     picture

# ── NOT YET, VERSUS WRONG ──
#
# `Clear_Fields_` leaves count 1 (fields.cpp:207) and `parse_fields`
# drops slot 0, so between the switch to 36 and `Init_Entry_Data_` the
# wire carries NO fields. Treating that as a contradiction put the
# game's own picture on screen for 22 frames on every entry — measured
# five times out of five by `tools/entry_glimpse.py`, and what Data saw
# at stardate 3500.3.
#
# The distinction is the whole fix: an ABSENT list is the game not
# having built one; a list that is THERE and disagrees is the fault
# work order 165 part D found, and that one must still hand over at
# once.
from core import researchstate as _wt

assert _wt.EMPTY_LIST_GRACE == 66, _wt.EMPTY_LIST_GRACE
assert "22" in _wt.__doc__ or "22" in io.open(os.path.join(
    os.path.dirname(SCREENS_DIR), "core", "researchstate.py"),
    encoding="utf-8").read(), (
        "the grace no longer says what it was measured from")

_wt_good = _rl_list(_dx_entries, select_mode=False)
_wt_rec = (_dx_tf, _dx_ta)


def _wt_state(fields, empty_frames):
    return _wt.classify(_dx_scr._names, _dx_scr._wording, _wt_rec,
                        fields, False, empty_frames)


# A list that agrees is READY whatever the counter says.
assert _wt_state(_wt_good, 0)[1] == _wt.READY
assert _wt_state(_wt_good, 999)[1] == _wt.READY
# NO list is WAITING, up to and including the bound…
for _wt_n in (0, 1, _wt.EMPTY_LIST_GRACE):
    assert _wt_state([], _wt_n)[1] == _wt.WAITING, _wt_n
    assert _wt_state(None, _wt_n)[1] == _wt.WAITING, _wt_n
# …and past it the silence becomes a failure.
assert _wt_state([], _wt.EMPTY_LIST_GRACE + 1)[1] == _wt.UNVALIDATED
# A LIST THAT IS THERE AND DISAGREES has no grace at all — one field
# too many is exactly the shape of the fault 165 part D found.
_wt_extra = _wt_good + _wt_good[-1:]
for _wt_n in (0, 1, _wt.EMPTY_LIST_GRACE):
    assert _wt_state(_wt_extra, _wt_n)[1] == _wt.UNVALIDATED, _wt_n
# And the states that come before the list is even looked at are
# unchanged: no record, no names, no wording.
assert _wt.classify(_dx_scr._names, _dx_scr._wording, None, [], False,
                    0)[1] == _wt.NO_PLAYER


class _WtAbsent:
    state = "missing"


assert _wt.classify(_WtAbsent(), _dx_scr._wording, _wt_rec, _wt_good,
                    False, 0)[1] == _wt.NAMES_MISSING
assert _wt.classify(_dx_scr._names, _WtAbsent(), _wt_rec, _wt_good,
                    False, 0)[1] == _wt.WORDING_MISSING

# WAITING IS THE ONE STATE THAT DOES NOT HAND OVER.
_wt_empty_state = _RsGameState()
_wt_empty_state.current_screen = 36
_wt_empty_state.fields = []
_wt_empty_state.player_raw = list(_dx_state.player_raw)
_wt_empty_state.player_num = 0
_dx_scr.app.client, _dx_scr.app.connected = _rs_client, True
_rs_client.state = _wt_empty_state
_dx_scr.enter(_wt_empty_state)
_dx_scr._names = derived(_dx_tn.TechNames)
_dx_scr._wording = derived(_dx_bt.BillText)
_dx_scr.update(_wt_empty_state)
assert _dx_scr.state == _wt.WAITING, _dx_scr.state
assert _dx_scr.wants_original() is False, (
    "the screen hands over while the game has not built its list — the "
    "glimpse is back")
# The bound is reached by UPDATING, not by setting a number by hand:
# the counter is the screen's own.
for _ in range(_wt.EMPTY_LIST_GRACE + 1):
    _dx_scr.update(_wt_empty_state)
assert _dx_scr.state == _wt.UNVALIDATED, _dx_scr.state
assert _dx_scr.wants_original() is True, (
    "a list that never arrives never reaches the picture — the fix has "
    "turned a real failure into a frozen map")
# …and the first real list ends it, whatever the counter had reached.
_dx_scr.update(_dx_state)
assert _dx_scr.state == _wt.READY and _dx_scr.wants_original() is False
ok("an empty field list is WAITING and draws nothing; a list that is "
   "there and disagrees hands over on the first frame")

# ── AND WHILE IT WAITS, THE WINDOW IS THE MAP ──
#
# The screen drawing nothing is only half the claim; the other half is
# that what the player sees is the galaxy map. Two frames of the same
# state, one with the overlay and one without: while it waits they must
# be IDENTICAL, because the panel contributes nothing at all.
_rs_client.state = _ov_map_state
_rs_d.close_overlay()
_rs_d.switch_to("galaxy_map", _ov_map_state)
_rs_client.state = _wt_empty_state
_rs_d.update_from_game(_wt_empty_state)
assert _rs_d.overlay_name == "research_change", _rs_d.overlay_name
_dx_scr._names = derived(_dx_tn.TechNames)
_dx_scr._wording = derived(_dx_bt.BillText)
_dx_scr.update(_wt_empty_state)
_rs_map.update(_ov_map_state)
assert _dx_scr.state == _wt.WAITING, _dx_scr.state


def _wt_frame(with_overlay):
    _kept = _rs_d.overlay
    if not with_overlay:
        _rs_d.overlay = None
    _s = pygame.Surface((1920, 1080))
    _s.fill((0, 0, 0))
    _rs_d.render(_s)
    _rs_d.overlay = _kept
    return _s


_wt_with, _wt_without = _wt_frame(True), _wt_frame(False)
_wt_seen = _wt_diff = 0
for _wt_y in range(0, 1080, 7):
    for _wt_x in range(0, 1920, 7):
        _wt_seen += 1
        if _wt_with.get_at((_wt_x, _wt_y))[:3] != \
                _wt_without.get_at((_wt_x, _wt_y))[:3]:
            _wt_diff += 1
assert _wt_seen > 5000, _wt_seen
assert _wt_diff == 0, (
    f"{_wt_diff} of {_wt_seen} pixels differ while the panel is still "
    f"waiting — it is drawing something it cannot vouch for")
# The control: with a list it CAN vouch for, the same comparison finds
# the panel. Without this the equality above would pass on a frame that
# drew no panel under any circumstances.
_rs_client.state = _dx_state
_dx_scr.update(_dx_state)
assert _dx_scr.state == _wt.READY
_wt_ready = _wt_frame(True)
_wt_drawn = sum(1 for _wt_y in range(0, 1080, 7)
                for _wt_x in range(0, 1920, 7)
                if _wt_ready.get_at((_wt_x, _wt_y))[:3] !=
                _wt_without.get_at((_wt_x, _wt_y))[:3])
assert _wt_drawn > 200, _wt_drawn
_rs_d.close_overlay()
ok("while it waits, the window is the galaxy map and not the game's "
   "picture")
