# smoke-suite area: research_select
#
# Part of the OrionLayer smoke suite — 080_research_select_52_falls_back_to_the_original.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (92 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 5 check(s) it holds:
#   - 52 falls back to the original picture; 53 is the HD screen and hands back to it, and neither sen
#   - research select: the layout is the original's rectangles, every row's drawn centre picks that ro
#   - research select: four omissions, one HD extension and three deviations are marked where they hap
#   - open fix 26 is OPEN, and the player's workaround stands in all three places it has to (module, o
#   - open fix 26's marking is tied to its status, and its status no longer requires it


# THE TWO TURN-START RESEARCH DIALOGS (work order 129 B, open fix 24):
# while the state reports 52 (the science room) or 53 (SELECT NEW
# RESEARCH), no HD screen may send anything. Nothing claims those ids,
# so decision 22 takes over and the original picture is what the player
# answers in — and 128 C showed what one field into that list does.
# Driven through the dispatcher, with the galaxy map (which is the
# screen that was left up before the patch) entered first.
_rs_app, _ = _pv.build_screen(1920, 1080)
_rs_d = _rs_app.dispatcher

class _RsClient:
    def __init__(self):
        self.log = []
        self.state = None

    def activate_field(self, i):
        self.log.append(("act", i))

    def inject_click(self, x, y):
        self.log.append(("click", x, y))

    def inject_key(self, k):
        self.log.append(("key", k))

    def cancel_field(self, i):
        self.log.append(("cancel", i))
_rs_client = _RsClient()
_rs_app.client, _rs_app.connected = _rs_client, True
_rs_d.switch_to("galaxy_map")
_rs_gs = _GmState()
_rs_gs.current_screen = 0
_rs_gs.map_scale = 10          # zoomed in: the map would want to park
import json as _rs_json
from core.game_state import FieldInfo as _RsField

def _rs_fields(rows):
    out = []
    for _r in rows:
        _f = _RsField()
        (_f.index, _f.x, _f.y, _f.x_end, _f.y_end, _f.field_type,
         _f.hotkey) = _r
        out.append(_f)
    return out
_rs_gs.fields = _rs_fields(_rs_json.load(open(os.path.join(
    os.path.dirname(SCREENS_DIR), "tools",
    "galaxy_box_fields.json")))["closed"])
_rs_map = _rs_d.screens["galaxy_map"]
_rs_map._viewctl.active = True      # decoupled: the map wants to park
_rs_map._viewctl._park_sent = 0.0
_rs_d.update_from_game(_rs_gs)
_rs_d.update_screens(_rs_gs)
assert _rs_client.log, ("the map sends nothing even at screen 0 in this "
                        "fixture — the control below proves nothing")
# 52 STILL HAS NO HD SCREEN and falls back (decision 22). 53 is
# screens/research_select/ since work order 130 E — but with no
# player record on the wire it cannot vouch for a list, so it must
# ALSO show the game's picture and send nothing. Both cases, and
# the difference between them, are the point of this check now.
_rs_client.log.clear()
_rs_gs.current_screen = 52
assert _rs_d.update_from_game(_rs_gs) is False, (
    "screen 52 routed to an HD screen; nothing may claim it")
assert _rs_d.use_original and _rs_d.active is None, _rs_d.active_name
for _ in range(3):
    _rs_map._viewctl._park_sent = 0.0
    _rs_d.update_screens(_rs_gs)
    _rs_d.route_click(960, 540)
    _rs_d.route_motion(960, 540)
assert _rs_client.log == [], (52, _rs_client.log)

_rs_client.log.clear()
_rs_gs.current_screen = 53
assert _rs_d.update_from_game(_rs_gs) is True, (
    "screen 53 no longer routes to research_select")
assert _rs_d.active_name == "research_select", _rs_d.active_name
for _ in range(3):
    _rs_d.update_screens(_rs_gs)
    _rs_d.route_click(960, 540)
    _rs_d.route_motion(960, 540)
assert _rs_client.log == [], (53, _rs_client.log)
assert _rs_d.active.wants_original(), (
    "the research screen has no player record and still claims it "
    "can draw the list")
from core import screen_names as _rs_names
assert _rs_names.SCREENS[52] == ("(synthetic)", None), \
    _rs_names.SCREENS[52]
assert _rs_names.SCREENS[53] == ("(synthetic)", "research_select"), \
    _rs_names.SCREENS[53]
ok("52 falls back to the original picture; 53 is the HD screen and "
   "hands back to it, and neither sends anything")

# ── THE RESEARCH SELECT SCREEN (work order 130 E and F) ────────
#
# Wire id 53, structure only — frame and artwork come later. Three
# things must not rot: the layout IS the original's rectangles, the
# rows are one rectangle for drawing and clicking, and the screen
# refuses rather than guesses.
from screens.research_select import native as _rsn
from screens.research_select import screen as _rss

# 1. THE LAYOUT IS TRANSCRIBED, AND THE PROVENANCE IS NOT ON A BOX.
#    `Box.to_dict` serializes a fixed key set, so a `native` key on
#    a box is dropped the first time the F5 editor saves — the trap
#    decision 38 names for `help_id`. boxes.json therefore names the
#    boxes and native.py holds every rectangle, and the two lists
#    must be exactly each other.
_rs_scr = _rs_d.screens["research_select"]
_rs_boxfile = _sjson.load(open(os.path.join(
    SCREENS_DIR, "research_select", "boxes.json"), encoding="utf-8"))
for _res, _bl in _rs_boxfile.items():
    assert {_b["name"] for _b in _bl} == set(_rsn.BOX_NATIVE), (
        _res, sorted({_b["name"] for _b in _bl}
                     ^ set(_rsn.BOX_NATIVE)))
    for _b in _bl:
        assert "rect" not in _b, (
            f"{_b['name']} carries a rect in boxes.json — it would be "
            f"a second copy of a number native.py owns, and the copy "
            f"is the one that goes stale")
# Seated, every box is DERIVED, so `to_dict` omits the rect and the
# editor cannot write that second copy back.
_rs_d.switch_to("research_select")
assert all(_b.derived and _b.ref_rect for _b in _rs_scr.boxes), \
    [(_b.name, _b.derived, _b.ref_rect) for _b in _rs_scr.boxes]
assert all("rect" not in _b.to_dict() for _b in _rs_scr.boxes)
# And the eight entry boxes ARE the game's own entry-block fields —
# the same rectangles researchlist validates the wire against, not
# a second transcription of them.
_rs_tf = [0] * _rl_res.FIELD_COUNT
for _rs_g in (4, 7):
    _rs_tf[_rl.FIRST_FIELD_IN_GROUP[_rs_g]] = _rl.FIELD_STATUS_OFFERABLE
from core.structs import player as _rs_plsp
_rs_ta = [_rl.APP_STATUS_AVAILABLE] * _rs_plsp.TECH_APPLICATIONS_COUNT
_rs_entries = _rl.reconstruct(_rs_tf, _rs_ta, select_mode=True)
_rs_blocks = {_k: _r for _k, _t, _r in _rl.expected_fields(_rs_entries)
              if _k.startswith("block ")}
for _i in range(8):
    assert _rsn.BOX_NATIVE[f"entry_{_i}"] == _rs_blocks[f"block {_i}"], (
        _i, _rsn.BOX_NATIVE[f"entry_{_i}"], _rs_blocks[f"block {_i}"])

# 2. NATIVE <-> HD ROUND-TRIPS AT ALL FOUR RESOLUTIONS, and the
#    conversion is the SAME placement the fallback view uses, which
#    is what makes an HD screenshot line up with the native one
#    beside it.
from core.original_view import OriginalView as _RsOV
_rs_view = _RsOV()
for _W, _H in ((1920, 1080), (2560, 1440), (3440, 1440), (3840, 2160)):
    _rs_lay = Layout(_W, _H)
    for _nx, _ny in ((0, 0), (161, 30), (320, 240), (639, 479)):
        # The CENTRE of the native pixel's own HD cell, which is
        # what a click means — the top-left corner is a boundary
        # and rounds either way. The cell comes from the module's
        # own conversion, never recomputed here.
        _cx, _cy, _cw, _ch = _rsn.to_hd((_nx, _ny, _nx, _ny), _rs_lay)
        _rs_back = _rsn.from_hd_point(
            (_cx + _cw // 2, _cy + _ch // 2), _rs_lay)
        assert _rs_back == (_nx, _ny), (_W, _H, (_nx, _ny), _rs_back)
    # the reference-space picture is the same 4:3 box the fallback
    # places the framebuffer in, at reference size
    _rs_vx, _rs_vy, _rs_vw, _rs_vh, _ = _rs_view.placement(
        _rs_lay.ref_w, _rs_lay.ref_h)
    _rs_full = _rsn.to_hd((0, 0, 639, 479), _rs_lay)
    assert abs(_rs_full[0] - _rs_vx) <= 1 and \
        abs(_rs_full[2] - _rs_vw) <= 1, (_W, _H, _rs_full,
                                         (_rs_vx, _rs_vy, _rs_vw, _rs_vh))

# 3. ONE RECTANGLE FOR DRAWING AND FOR CLICKING — ASSERTED AGAINST
#    THE DRAWN PIXELS, not only against the arithmetic (work order
#    128 D's method for the Planets list). A shared function
#    guarantees agreement, not correctness: the stacked colony
#    figures shared one and missed 165 of 210 clicks (decision 5).
# THE REAL GameState, never a hand-made object with the attribute
# names the screen happens to ask for. The first version of this
# check built its own class with a `players` list; the screen read
# `players`; `core/game_state.py` has only ever had `player_raw`,
# so the check passed and the screen fell back on every real state.
# Found by driving it live (work order 130's live run) — which is
# the one thing that could. A fake that answers the question the
# code asks proves the code and the fake agree, and nothing else.
from core.game_state import GameState as _RsGameState
assert hasattr(_RsGameState(), "player_raw"), \
    "GameState has no player_raw — the screen reads a name that is gone"
assert not hasattr(_RsGameState(), "players"), \
    "GameState grew a `players` attribute; the screen must read one home"

def _RsPlayerState(fields, players):
    _st = _RsGameState()
    _st.current_screen = 53
    _st.fields = fields
    _st.player_raw = list(players)
    _st.player_num = 0
    return _st

from core.structs import player as player_mod

def _rs_record(tech_fields, tech_apps):
    """A raw s_player whose two tech arrays say this."""
    _raw = bytearray(player_mod.SPEC.size)
    _off = next(_o for _n, _o, _k in player_mod.SPEC.fields
                if _n == "tech_fields")
    _raw[_off:_off + len(tech_fields)] = bytes(tech_fields)
    _ao = player_mod.TECH_APPLICATIONS_OFFSET
    _raw[_ao:_ao + len(tech_apps)] = bytes(tech_apps)
    return bytes(_raw)

from core.structs import player as player_mod
_rs_live = _rl_list(_rs_entries)
for _i, _f in enumerate(_rs_live):
    _f.index = _i
_rs_gs2 = _RsPlayerState(_rs_live, [_rs_record(_rs_tf, _rs_ta)])
_rs_scr.enter(_rs_gs2)
_rs_scr.update(_rs_gs2)
if _rs_scr.state == _rss.READY:
    _rs_surface = pygame.Surface((1920, 1080))
    _rs_surface.fill((0, 0, 0))
    _rs_scr.render(_rs_surface)
    _rs_hits = 0
    for _e in _rs_scr._entries:
        for _row in range(len(_e.apps)):
            _wx, _wy, _ww, _wh = _rsn.window_rect(_e.row_rect(_row),
                                                  _rs_scr.layout)
            # The row's own visible centre, the point a player aims
            # at — not a corner, and not a native pixel converted a
            # second way.
            _cx, _cy = _wx + _ww // 2, _wy + _wh // 2
            assert _rs_scr.row_at(_cx, _cy) == (_e.index, _row), (
                _e.index, _row, (_cx, _cy), _rs_scr.row_at(_cx, _cy))
            # And the hover the screen would show is that row, and
            # it is drawn INSIDE that rectangle: render with the
            # hover set and require the fill to be there and only
            # there.
            _rs_scr.handle_mouse_motion(_cx, _cy)
            assert _rs_scr._hover == (_e.index, _row)
            _rs_hover_surf = pygame.Surface((1920, 1080))
            _rs_hover_surf.fill((0, 0, 0))
            _rs_scr.render(_rs_hover_surf)
            assert _rs_hover_surf.get_at((_cx, _cy))[:3] != (0, 0, 0), (
                "the hovered row drew nothing at its own centre",
                _e.index, _row)
            # Two pixels above the row's top edge is the row above
            # or nothing — never this row.
            assert _rs_scr.row_at(_cx, _wy - 2) != (_e.index, _row)
            _rs_hits += 1
    assert _rs_hits >= 4, _rs_hits
    report(f"research select: {_rs_hits} rows, every visible centre "
           f"picks its own row")
else:
    report(f"research select could not be driven with a record "
           f"({_rs_scr.state}) — the refusals below are what ran")

# 4. THE REFUSALS (decision 33), each one on its own.
#    Its own client, because the screen resolves the row against
#    `client.state.fields` in the same step it sends — which is the
#    rule being checked, not a detail of the fixture.
class _RsScrClient:
    def __init__(self, state):
        self.log = []
        self.state = state

    def activate_field(self, i):
        self.log.append(("ACTIVATE_FIELD", i))

    def inject_click(self, x, y):
        self.log.append(("INJECT_CLICK", x, y))

    def inject_key(self, k):
        self.log.append(("INJECT_KEY", k))

_rs_prev = (_rs_scr.app.client, _rs_scr.app.connected)
_rs_client = _RsScrClient(_rs_gs2)
_rs_scr.app.client, _rs_scr.app.connected = _rs_client, True
_rs_client.log.clear()
if _rs_scr.state == _rss.READY:
    # a click beside every row sends nothing
    _rs_scr.handle_click(2, 2)
    assert _rs_client.log == [], _rs_client.log
    # a click ON a row sends exactly one ACTIVATE_FIELD, for the
    # field that row has IN THIS LIST — found by shape, so a list
    # whose indices have all moved still resolves to the same rect.
    _e0 = next(_e for _e in _rs_scr._entries if _e.offered)
    _wx, _wy, _ww, _wh = _rsn.window_rect(_e0.row_rect(0),
                                          _rs_scr.layout)
    _rs_scr.handle_click(_wx + _ww // 2, _wy + _wh // 2)
    assert len(_rs_client.log) == 1, _rs_client.log
    _rs_want = _rl.row_field(_rs_live, _e0, 0)
    assert _rs_client.log[0] == ("ACTIVATE_FIELD", _rs_want.index), \
        (_rs_client.log, _rs_want.index)
    # and a SECOND click sends nothing: one commit per visit, the
    # game leaves 53 by itself (decision 21)
    _rs_client.log.clear()
    _rs_scr.handle_click(_wx + _ww // 2, _wy + _wh // 2)
    assert _rs_client.log == [], _rs_client.log

# THE REFUSALS, AND THE ORDER THEY ARE TESTED IN.
#
# `_rebuild` decides in one order: names -> wording -> player
# record -> validation, and the FIRST thing missing is the answer.
# So the state a situation produces depends on what the machine has
# extracted, and asserting one state per situation made this block
# pass where the files happened to exist and fail on a fresh clone —
# found by the clone run before the push, 18 September 2026, twice
# in a row, on this and on the NO_PLAYER case below.
#
# `_rs_expect` is `_rebuild`'s own order, once. What every case
# then asserts is the RULE, which holds whatever is extracted: the
# screen hands over, it says why, and it sends nothing.
def _rs_expect(want_when_ready):
    if _rs_scr._names.state != "ok":
        return _rss.NAMES_MISSING
    if _rs_scr._wording.state != "ok":
        return _rss.WORDING_MISSING
    return want_when_ready

def _rs_refuses(label, want_when_ready):
    assert _rs_scr.state == _rs_expect(want_when_ready), (
        label, _rs_scr.state, _rs_scr._names.state,
        _rs_scr._wording.state)
    assert _rs_scr.wants_original(), label
    assert _rs_scr.problems, (
        f"{label}: the screen fell back and said nothing about why")
    assert _rs_scr.fallback_reason(), (
        f"{label}: no sentence for state {_rs_scr.state}")
    _rs_client.log.clear()
    _rs_scr.handle_click(960, 540)
    _rs_scr.handle_mouse_motion(960, 540)
    assert _rs_client.log == [], (label, _rs_client.log)
    assert _rs_scr.row_at(960, 540) is None, (
        f"{label}: a row was hit-tested on a list the screen "
        f"refused to draw")

# a field list of the wrong shape
_rs_scr.enter(_RsPlayerState(_rs_live[:-1], [_rs_record(_rs_tf, _rs_ta)]))
_rs_refuses("wrong-shape field list", _rss.UNVALIDATED)
# no player record on the wire
_rs_scr.enter(None)
_rs_refuses("no player record", _rss.NO_PLAYER)
# an absent extractor file, forced regardless of what this machine
# has: these two do not depend on the tree, so they are exact.
_rs_real_names = _rs_scr._names
_rs_scr._names = _tn.TechNames("zz")
_rs_scr.update(_rs_gs2)
assert _rs_scr.state == _rss.NAMES_MISSING and _rs_scr.wants_original()
assert _rs_scr.fallback_reason()
_rs_scr._names = _rs_real_names
_rs_real_wording = _rs_scr._wording
_rs_scr._wording = _bt.BillText("zz")
_rs_scr.update(_rs_gs2)
assert _rs_scr.state == _rs_expect(_rss.WORDING_MISSING)
assert _rs_scr.wants_original() and _rs_scr.fallback_reason()
_rs_scr._wording = _rs_real_wording
# ESC, and every other key, sends NOTHING: select mode has no way
# out but a commit (tech.cpp:131, fields.cpp:983-988).
_rs_client.log.clear()
for _k in (27, 13, 32, ord("a")):
    _rs_scr.handle_key(_k)
assert _rs_client.log == [], (
    "a key was forwarded into a dialog whose cancel is disabled",
    _rs_client.log)
_rs_scr.app.client, _rs_scr.app.connected = _rs_prev
ok("research select: the layout is the original's rectangles, every "
   "row's drawn centre picks that row, and it refuses five ways")

# 5. EVERY OMISSION AND DEVIATION IS MARKED, AND THE MARKING IS
#    HELD HERE (decision 61, and the markings inventory above).
#    Each key must appear with its own label in the module that
#    owns it, so a marking cannot be dropped from the docstring and
#    left in the code, or the other way round.
_rs_src = {
    "screen": open(os.path.join(SCREENS_DIR, "research_select",
                                "screen.py"), encoding="utf-8").read(),
    "panel": open(os.path.join(SCREENS_DIR, "research_select",
                               "panel.py"), encoding="utf-8").read(),
    "native": open(os.path.join(SCREENS_DIR, "research_select",
                                "native.py"), encoding="utf-8").read(),
    "layout": open(os.path.join(SCREENS_DIR, "research_select",
                                "layout.json"), encoding="utf-8").read(),
}
# THE RP/FP/PR DEVIATION IS GONE — work order 165 part A. It was
# there because `MOX::_settings.language` had no verified offset, so
# HD printed " RP" whatever the game was running in. The byte is in
# the settings spec now (@210, both sources beside the field), the
# suffix follows the game, and the marking went with the cause. Its
# replacement is the assertion three blocks down: the TABLE has to be
# the original's four cases.
assert set(_rss.MARKED) == {
    "science_room_animation", "category_list_popup", "description_box",
    "little_arrow", "title", "category_label_as_text",
    "shrink_instead_of_squeeze"}, \
    sorted(_rss.MARKED)
for _kind in ("OMISSION", "HD EXTENSION", "DEVIATION"):
    assert _kind in _rs_src["screen"], _kind
assert sum(1 for _v in _rss.MARKED.values() if _v == "OMISSION") == 4
# The four omissions are things the screen must NOT have built.
for _absent in ("SR_R", "_Tech_List_", "Draw_Application_Description_",
                "Draw_Little_Arrow_"):
    assert _absent in _rs_src["screen"], (
        f"{_absent} is no longer named in the omission list — either "
        f"it was built and the marking must go, or the marking was "
        f"dropped and the omission is now invisible")
# The three deviations each live where they are done.
assert "DEVIATION" in _rs_src["panel"], "the squeeze/shrink deviation"
# …AND THE SUFFIX NOW FOLLOWS THE GAME. `tech.cpp:631-639` has three
# cases and an else; the table must carry exactly that, and the
# resolver must fall to " RP" for anything the original does not name
# — which is what its own `else` does.
assert _rss.COST_SUFFIX == {0: " RP", 1: " FP", 3: " RP", 4: " PR"}, (
    f"the cost-unit table is {_rss.COST_SUFFIX}; tech.cpp:631-639 "
    f"prints FP for language 1, PR for language 4 and RP otherwise")
assert _rss.cost_suffix(1) == " FP" and _rss.cost_suffix(4) == " PR", (
    "the resolver does not reproduce the original's two named cases")
assert _rss.cost_suffix(0) == " RP" and _rss.cost_suffix(9) == " RP", (
    "a language the original has no case for must fall to RP, which "
    "is what its own else does — not to a blank or an error")
assert "cost_suffix" not in _rs_src["layout"], (
    "layout.json still carries a cost suffix. It is the GAME'S word "
    "now and comes off the wire; a second copy in OrionLayer's own "
    "wording file is the stale copy this project keeps paying for")
# The chosen title rect. It is computed in `core/researchnative.py`
# since work order 165 part B — one geometry for both modes — so the
# marking is asserted THERE, where the number is, as well as in the
# screen's own binding of it.
assert "HD EXTENSION" in _rs_src["native"], "the chosen title rect"
_rs_geo_src = open(os.path.join(os.path.dirname(SCREENS_DIR), "core",
                                "researchnative.py"),
                   encoding="utf-8").read()
assert "HD EXTENSION" in _rs_geo_src and "title" in _rs_geo_src, (
    "core/researchnative.py no longer marks the title rect as the one "
    "chosen rectangle on the research screens")
# And the screen has a help list of its own: three rectangles, ONE
# id, all of them OUTSIDE the panel (billhelp.cpp:42-46).
_rs_help = _sjson.load(open(os.path.join(
    SCREENS_DIR, "research_select", "help.json"), encoding="utf-8"))
_rs_regions = _rs_help["regions"]
assert len(_rs_regions) == 3 and {_r["help_id"] for _r in _rs_regions} \
    == {254}, _rs_regions
# NOT "outside the panel" — the bands lie over the fill's own top
# and bottom edges, and doc/tech_change_reading.md §7 derives the
# panel's VISIBLE edge from these very rectangles. The rule that
# matters is narrower and is the one §6 states: a right click is
# help only where it is not something else. Inside an entry block
# or on a radio it is the description box or the category list
# (tech.cpp:323-337, :377-391), so no help region may cover one.
_rs_touch = [(f"entry_{_i}", _rsn.BOX_NATIVE[f"entry_{_i}"])
             for _i in range(8)]
_rs_touch += [(f"radio {_i}",
               (_rl.RADIO_POS[_i][0] + _rl.PANEL_ORIGIN_SELECT,
                _rl.RADIO_POS[_i][1],
                _rl.RADIO_POS[_i][0] + _rl.PANEL_ORIGIN_SELECT,
                _rl.RADIO_POS[_i][1]))
              for _i in range(8)]
for _r in _rs_regions:
    _hx1, _hy1, _hx2, _hy2 = _r["native"]
    for _tn_name, (_tx1, _ty1, _tx2, _ty2) in _rs_touch:
        assert (_hx2 < _tx1 or _hx1 > _tx2
                or _hy2 < _ty1 or _hy1 > _ty2), (
            f"help region {_r['box']} covers {_tn_name}; a right "
            f"click there is the description box or the category "
            f"list, not help (tech.cpp:323-337, :377-391)")
    assert _r["box"] in _rsn.BOX_NATIVE, _r["box"]
# And the HD title sits in a band, where the original's art carries
# its headline — not over an entry.
for _tn_name, (_tx1, _ty1, _tx2, _ty2) in _rs_touch:
    _ttx1, _tty1, _ttx2, _tty2 = _rsn.TITLE_RECT
    assert (_ttx2 < _tx1 or _ttx1 > _tx2
            or _tty2 < _ty1 or _tty1 > _ty2), (
        f"the HD title overlaps {_tn_name}")
ok("research select: four omissions, one HD extension and three "
   "deviations are marked where they happen, and help 254's three "
   "rectangles all lie outside the panel")

# ── THE WORKAROUND LIVES EXACTLY AS LONG AS THE FAULT ──────────
#
# Open fix 26: SELECT NEW RESEARCH commits a row by itself about a
# second and a half after the science room hands over. Measured 18
# September 2026 with a send counter at zero; Data's counter-test of
# 19 September (same binary, no client connected, the completion
# dialog clicked away with the REAL MOUSE) shows the list waits, so
# open fix 25 is not the cause. OPEN, deferred by Data.
#
# While it is open the player has a way round it, and a way round a
# fault is worth nothing where nobody finds it. So the SAME sentence
# stands in three places — the module that has the fault, the only
# list of what is asked of Joes, and the status document — and this
# check holds it in all three FOR AS LONG AS entry 26 says OPEN.
# When the entry stops saying OPEN the marking may go, and this
# check says so instead of failing: a check that outlives its
# subject is the reason decision 61 exists.
_wa = ("click the completion dialog away in the orion2re window "
       "with the real mouse")

def _wa_flat(path):
    return _lre.sub(r"\s+", " ", io.open(
        path, encoding="utf-8").read()).lower()

_wa_root = os.path.dirname(SCREENS_DIR)
_wa_fixes = os.path.join(_wa_root, "doc", "orion2re_open_fixes.md")
_wa_files = {
    "doc/orion2re_open_fixes.md": _wa_fixes,
    "v3_projektstatus.md": os.path.join(_wa_root, "v3_projektstatus.md"),
    "screens/research_select/screen.py": os.path.join(
        SCREENS_DIR, "research_select", "screen.py"),
}
# The entry's own status, read from its row in the table at the top —
# one place, so the fix's state and this check cannot disagree.
_wa_rows = [_l for _l in io.open(_wa_fixes, encoding="utf-8")
            if _l.startswith("| 26 |")]
assert len(_wa_rows) == 1, (
    f"doc/orion2re_open_fixes.md has {len(_wa_rows)} rows for item 26 "
    f"— this check reads its status from exactly one")
_wa_open = "OPEN" in _wa_rows[0]
if _wa_open:
    for _name, _path in sorted(_wa_files.items()):
        assert _wa in _wa_flat(_path), (
            f"open fix 26 still says OPEN and {_name} no longer "
            f"carries the workaround. Either the fix was closed — in "
            f"which case its row says so and this check stands down — "
            f"or the sentence was dropped from a place a player or a "
            f"future session would look")
    # And the fault itself is named where it is suffered, not only
    # where it is filed.
    assert "open fix 26" in _wa_flat(
        _wa_files["screens/research_select/screen.py"]), (
        "screens/research_select/screen.py no longer names open fix "
        "26; the workaround without the fault it works round is a "
        "sentence nobody can act on")
    ok("open fix 26 is OPEN, and the player's workaround stands in "
       "all three places it has to (module, open fixes, status)")
else:
    report("open fix 26 no longer says OPEN — the workaround may "
           "leave the module, the open fixes and the status document")
    ok("open fix 26's marking is tied to its status, and its status "
       "no longer requires it")
