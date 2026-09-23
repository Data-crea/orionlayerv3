# smoke-suite area: research_change
#
# Part of the OrionLayer smoke suite — 080a_research_change_the_change_mode_panel.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (93 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# This one did NOT stand inside main(): it is work order 165 part B,
# the change-mode research panel, and it is the only check that order
# added for it.
#
# The 1 check(s) it holds:
#   - research change (36): the same panel 81 px left, a way out that
#     changes nothing, the remaining cost, and every marking

# ── CHANGE MODE IS SELECT MODE WITH FOUR DIFFERENCES ──
#
# `TECH::_Tech_Select_(changing_tech)` is ONE function (tech.cpp:111-395)
# and work order 165 made the HD side one class. This check is about
# the four places the two modes part company, because a configuration
# that silently collapses into the other mode is the failure this shape
# invites: everything would still draw, and it would draw select mode.
from core import researchnative as _rc_geo
from screens.research_change import screen as _rcs
from screens.research_select import screen as _rss2

_rc_sel = _rc_geo.Geometry("select")
_rc_chg = _rc_geo.Geometry("change")

# 1. THE ORIGIN, AND THE 81 PX. `_g_scrn_x` is 161 and 80
#    (tech.cpp:146-147, :170-171), and every position on the panel is
#    origin + constant, so the whole of change mode sits 81 px left.
assert (_rc_sel.origin, _rc_chg.origin) == (161, 80)
for _i in range(8):
    _rc_s = _rc_sel.entry_block_rect(_i)
    _rc_c = _rc_chg.entry_block_rect(_i)
    assert [_a - _b for _a, _b in zip(_rc_s, _rc_c)] == [81, 0, 81, 0], (
        f"entry {_i} is not 81 px apart in the two modes: "
        f"{_rc_s} against {_rc_c}")
assert _rc_chg.panel_rect == (84, 4, 551, 472), _rc_chg.panel_rect

# 2. THE BANDS ARE NOT THE SAME SHAPE, which is the thing a shared
#    geometry would quietly get wrong. Select mode's first rectangle
#    covers the science room and it has a BOTTOM band; change mode's
#    covers the strip of galaxy map left of the panel and it has a
#    RIGHT one (billhelp.cpp:42-46 against :48-52).
assert (_rc_sel.help_id, _rc_chg.help_id) == (254, 255)
assert set(_rc_sel.bands) == {"science_room", "top_band", "bottom_band"}
assert set(_rc_chg.bands) == {"left_band", "right_band", "top_band"}
assert _rc_chg.science_room_rect is None, (
    "change mode has no science room — that animation is select mode's "
    "left strip (tech.cpp:245-273); here the strip is galaxy map")

# 3. boxes.json NAMES THE BOXES, THE GEOMETRY OWNS THE RECTANGLES,
#    and the two lists are exactly each other — the same rule select
#    mode is held to, for the same reason (decision 38's trap: a
#    `native` key on a box is dropped the first time F5 saves).
_rc_boxfile = _sjson.load(open(os.path.join(
    SCREENS_DIR, "research_change", "boxes.json"), encoding="utf-8"))
_rc_want = set(_rc_chg.box_native())
for _res, _bl in _rc_boxfile.items():
    assert {_b["name"] for _b in _bl} == _rc_want, (
        _res, sorted({_b["name"] for _b in _bl} ^ _rc_want))
    for _b in _bl:
        assert "rect" not in _b, (
            f"{_b['name']} carries a rect in boxes.json — a second copy "
            f"of a number core/researchnative.py owns")
_rc_scr = d.screens["research_change"]
d.switch_to("research_change")
assert all(_b.derived and _b.ref_rect for _b in _rc_scr.boxes), \
    [(_b.name, _b.derived) for _b in _rc_scr.boxes]

# 4. THE ENTRY BOXES ARE THE GAME'S OWN BLOCK FIELDS, in change mode's
#    positions — the same rectangles `researchlist` validates the wire
#    against, not a second transcription of them.
_rc_tf = [0] * _rl_res.FIELD_COUNT
for _rc_g in (4, 7):
    _rc_tf[_rl.FIRST_FIELD_IN_GROUP[_rc_g]] = _rl.FIELD_STATUS_OFFERABLE
_rc_ta = [_rl.APP_STATUS_AVAILABLE] * _rs_plsp.TECH_APPLICATIONS_COUNT
_rc_entries = _rl.reconstruct(_rc_tf, _rc_ta, select_mode=False)
_rc_blocks = {_k: _r for _k, _t, _r in
              _rl.expected_fields(_rc_entries, select_mode=False)
              if _k.startswith("block ")}
_rc_bn = _rc_chg.box_native()
for _i in range(8):
    assert _rc_bn[f"entry_{_i}"] == _rc_blocks[f"block {_i}"], (
        _i, _rc_bn[f"entry_{_i}"], _rc_blocks[f"block {_i}"])

# 5. THE COST IS WHAT IS LEFT, and only in this mode. `_Tech_Select_(1)`
#    passes `research_accumulated` as the offset (tech.cpp:203) where
#    `(0)` passes 0 (:221). The original clamps at 0 (:590-607).
_rc_scr._accumulated = 40
_rc_scr._current = (7, 3)
assert _rc_scr.cost_offset() == 40, _rc_scr.cost_offset()
assert _rc_scr.current_pair() == (7, 3), _rc_scr.current_pair()
_rc_sel_scr = d.screens["research_select"]
_rc_sel_scr._accumulated = 40
_rc_sel_scr._current = (7, 3)
assert _rc_sel_scr.cost_offset() == 0, (
    "select mode subtracted an accumulation it does not have — "
    "`_Tech_Select_(0)` passes 0 (tech.cpp:221)")
assert _rc_sel_scr.current_pair() == (0, 0), (
    "select mode named a current field. `Tech_Select_` zeroes it "
    "before the list is built (tech.cpp:104-105), so the original's "
    "second colour has nothing to mark there")

# 6. THERE IS A WAY OUT, AND IT SENDS NOTHING IT CANNOT FIND. ESC and
#    a click on the exit button are the same act, because the button
#    IS the ESC field (fields.cpp:2608-2613). Its rect is NOT in the
#    source — `Add_Button_Field_` takes it from the art — so the
#    screen looks it up in the live list, and with no such field it
#    must send nothing rather than guess an index.
assert _rcs.ResearchChangeScreen.HAS_EXIT is True
assert _rss2.ResearchSelectScreen.HAS_EXIT is False, (
    "select mode grew a way out. It has no ESC field and cancel is "
    "disabled (tech.cpp:131, :207) — its only exit is a commit")
assert _rc_chg.exit_button_origin == (269, 452), (
    f"the exit button moved: {_rc_chg.exit_button_origin}; "
    f"tech.cpp:198-200 puts it at (s + 189, 452)")
assert _rc_sel.exit_button_origin is None
_rc_sends = []
_rc_scr.app.client.activate_field = lambda _i: _rc_sends.append(_i)
_rc_scr._left = False
_rc_scr._sent = False
_rc_scr.handle_key(__import__("pygame").K_ESCAPE)
assert _rc_sends == [], (
    f"change mode sent {_rc_sends} for ESC with no exit button in the "
    f"field list. A field id it cannot see in the list it was handed "
    f"is the index that crashed the game in work order 128 C")

# 7. EVERY MARKING, AND THE SET IS SELECT MODE'S MINUS THE SCIENCE
#    ROOM — that difference IS the mode difference, so a drift in
#    either direction is caught here (decision 61).
assert set(_rcs.MARKED) == {
    "category_list_popup", "radio_index_skew", "exit_button_as_text",
    "description_box", "little_arrow", "title",
    "category_label_as_text", "shrink_instead_of_squeeze"}, \
    sorted(_rcs.MARKED)
# BOTH DIRECTIONS. Select mode has the science room, which is its own
# strip; change mode has the exit button's label, which select mode has
# no button to print (`accept_btn_id = -1`, tech.cpp:216). Asserting one
# direction only would let a marking appear on one screen unnoticed.
assert set(_rcs.MARKED) - set(_rss2.MARKED) == {"exit_button_as_text"}, (
    sorted(set(_rcs.MARKED) - set(_rss2.MARKED)))
assert set(_rss2.MARKED) - set(_rcs.MARKED) == {"science_room_animation"}, (
    sorted(set(_rss2.MARKED) ^ set(_rcs.MARKED)))
_rc_src = open(os.path.join(SCREENS_DIR, "research_change", "screen.py"),
               encoding="utf-8").read()
for _kind in ("OMISSION", "HD EXTENSION", "DEVIATION"):
    assert _kind in _rc_src, _kind
assert "Draw_Little_Arrow_" in _rc_src, (
    "Draw_Little_Arrow_ is no longer named in the omission list — "
    "either it was built and the marking must go, or the marking was "
    "dropped and the omission is now invisible")
# BOTH POPUPS ARE BUILT (work order 165 part C) and marked DEVIATION,
# so they are named for a different reason: what deviates is the box,
# not the behaviour. Both modes take them from the same class and both
# must say so — which is the whole point of building them once.
for _built in ("description_box", "category_list_popup",
               "radio_index_skew"):
    assert _rcs.MARKED[_built] == "DEVIATION" == _rss2.MARKED[_built], \
        _built
for _named in ("Draw_Application_Description_", "_Tech_List_"):
    assert _named in _rc_src, _named
# …and it must not MARK the science room, while still saying why it
# does not. An omission of something the original does not draw here
# would be a marking with no subject; a file that simply never
# mentions it leaves the next reader to wonder. The set equality above
# is the first half; this is the second.
assert "science_room_animation" not in _rcs.MARKED
assert "no science room" in _rc_src and "SR_R" in _rc_src, (
    "change mode neither marks the science room nor says why it does "
    "not. It is select mode's strip (tech.cpp:245-273); here that "
    "strip is the galaxy map")

# 8. HELP 255, THREE RECTANGLES, EACH RESOLVED FROM ITS BOX
#    (billhelp.cpp:48-52, decision 38).
_rc_help = _sjson.load(open(os.path.join(
    SCREENS_DIR, "research_change", "help.json"), encoding="utf-8"))
_rc_regions = _rc_help["regions"]
assert len(_rc_regions) == 3 and {_r["help_id"] for _r in _rc_regions} \
    == {255}, _rc_regions
for _r in _rc_regions:
    assert tuple(_r["native"]) == _rc_chg.bands[_r["box"]], (
        _r["box"], _r["native"], _rc_chg.bands[_r["box"]])

# 9. AND 36 IS THE ENGINE'S OWN NUMBER, claimed by this screen. It
#    named a folder that never existed until now, so it fell through
#    to the framebuffer.
assert _rs_names.SCREENS[36] == ("TECH_CHANGE", "research_change"), \
    _rs_names.SCREENS[36]
assert _rcs.ResearchChangeScreen.GAME_SCREEN_ID == 36

ok("research change (36): the panel 81 px left of select mode's at "
   "every entry, its own three help bands, the remaining cost where "
   "select mode shows the full one, a way out that sends nothing it "
   "cannot find in the live list, and every marking held")
