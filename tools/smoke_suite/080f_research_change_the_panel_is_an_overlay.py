# smoke-suite area: research_change
#
# Part of the OrionLayer smoke suite — 080f_research_change_the_panel_is_an_overlay.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (99 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# This one did NOT stand inside main(): it is work order 165 part F,
# change mode moved onto the GAME menu's overlay pattern.
#
# The 2 check(s) it holds:
#   - change mode is a panel over the HD galaxy map: the dispatcher
#     holds it while the wire says 36, and the map takes no input
#   - the map is BEHIND the panel, not painted out, and the three help
#     bands answer over it

# ── A PANEL OVER THE MAP, NOT A SCREEN INSTEAD OF IT ──
#
# The original draws the map itself before switching
# (`Draw_Mini_Main_Screen_`, mainscr_main.cpp:700-703; `Tech_Change_`,
# tech.cpp:1159-1161) and then fills only (s+4, 4)-(s+471, 472) over it
# (:290-291). Work order 165 built it as a screen of its own with the
# shared cockpit texture, which painted the map out; Data reversed that
# on 23 September 2026 and this check is what holds the reversal.
from core import researchframe as _rf
from screens.research_change import screen as _ov_chg
from screens.research_select import screen as _ov_sel

assert _ov_chg.ResearchChangeScreen.IS_OVERLAY is True
assert _ov_chg.ResearchChangeScreen.OVERLAY_PARENT == "galaxy_map"
# No dimming, for the reason the GAME menu has none: a palette-indexed
# engine cannot darken what is under a panel.
assert _ov_chg.ResearchChangeScreen.OVERLAY_DIM == 0
assert _ov_chg.ResearchChangeScreen.GAME_SCREEN_ID == 36
# SELECT mode is NOT one: behind its panel the original has a black
# fill and the science-room animation, not the map.
assert _ov_sel.ResearchSelectScreen.IS_OVERLAY is False

# 1. THE DISPATCHER HOLDS IT WHILE THE WIRE SAYS 36. `update_from_game`
#    opens it over the parent, keeps it for as long as the id stands,
#    and closes it the moment the game leaves — which is the lock this
#    screen needs and the one the GAME menu already had.
_ov_map_state = _RsGameState()
_ov_map_state.current_screen = 0
_ov_map_state.fields = _rs_fields(_rs_json.load(open(os.path.join(
    os.path.dirname(SCREENS_DIR), "tools",
    "galaxy_box_fields.json")))["closed"])
_ov_map_state.map_scale = 10
_dx_scr.app.client, _dx_scr.app.connected = _rs_client, True

_rs_client.state = _ov_map_state
_rs_d.close_overlay()
_rs_d.switch_to("galaxy_map", _ov_map_state)
_rs_d.update_from_game(_ov_map_state)
assert _rs_d.active_name == "galaxy_map" and _rs_d.overlay is None

_rs_client.state = _dx_state
_rs_d.update_from_game(_dx_state)
# THE STAND-INS AGAIN, because opening the overlay ENTERED the screen
# and `enter` rebuilds its two loaders from the real tree. On a machine
# that has run the extractors they come back `ok` and nothing is
# noticed; in a CLONE they come back missing, the screen is not READY,
# `render_content` returns early and the frame below is never drawn.
# The fresh-clone run caught exactly that — the fault the fundament
# describes under "A CHECK THAT READS THE PLAYER'S OWN FILES PASSES ON
# THE MACHINE THAT WROTE THEM", for the fifth time.
_dx_scr._names = derived(_dx_tn.TechNames)
_dx_scr._wording = derived(_dx_bt.BillText)
_dx_scr.update(_dx_state)
assert _rs_d.active_name == "galaxy_map", (
    f"the map is not the parent any more ({_rs_d.active_name}); change "
    f"mode is supposed to be a panel OVER it")
assert _rs_d.overlay_name == "research_change", _rs_d.overlay_name
assert _rs_d.top is _dx_scr
# It survives a second snapshot at 36 — the dispatcher must not
# re-enter the screen every frame.
_rs_d.update_from_game(_dx_state)
assert _rs_d.overlay_name == "research_change"

# 2. THE MAP TAKES NO INPUT WHILE THE PANEL IS UP, and the control is
#    the click that OPENS change mode: the galaxy map's research window
#    (`mapinput.click`, work order 165 part B). It sends on the map and
#    it must send nothing through the panel.
_ov_box = _rs_map.box_rect("sb_research_text")
assert _ov_box, "the galaxy map has no sb_research_text box to aim at"
_ov_pt = pygame.Rect(*_rs_map.layout.rect(_ov_box)).center

_rs_d.close_overlay()
_rs_client.state = _ov_map_state
_rs_d.update_screens(_ov_map_state)
_rs_client.log.clear()
_rs_d.route_click(*_ov_pt)
assert _rs_client.log, (
    "the research window sends nothing on the bare map either — this "
    "control proves nothing about the overlay")
_ov_would_send = list(_rs_client.log)

_rs_client.state = _dx_state
_rs_d.update_from_game(_dx_state)
assert _rs_d.overlay_name == "research_change"
_rs_client.log.clear()
_rs_d.route_click(*_ov_pt)
assert _rs_client.log == [], (
    f"a click on the map under the panel reached the map and sent "
    f"{_rs_client.log} (bare map: {_ov_would_send}) — the panel is not "
    f"taking the input")
assert _rs_d.overlay_name == "research_change", (
    "the click closed the panel; a click on the map outside it does "
    "nothing at all")
ok("change mode is a panel over the HD galaxy map: the dispatcher "
   "holds it while the wire says 36, and the map takes no input")

# ── THE MAP IS BEHIND IT, AND THAT IS A PIXEL CLAIM ──
#
# Two frames of the same state, one with the overlay and one without.
# In the two side bands — which is where the original has map and this
# screen had a cockpit texture until part F — the two must be IDENTICAL,
# because the panel draws nothing there. Inside the panel they must
# differ, or the comparison is about a frame that drew no panel at all.
#
# THE STAND-INS ONCE MORE. The click control above closed and reopened
# the overlay, and every open ENTERS the screen and rebuilds its two
# loaders from the real tree — which is `ok` here and missing in a
# clone. Setting them after the first open was not enough, and the
# fresh-clone run said so a second time.
_dx_scr._names = derived(_dx_tn.TechNames)
_dx_scr._wording = derived(_dx_bt.BillText)
_dx_scr.update(_dx_state)
assert _dx_scr.state == _dx_core.READY, (
    f"the panel is {_dx_scr.state}, so render_content returns early "
    f"and the frame below is never drawn")
_rs_map.update(_ov_map_state)


def _ov_frame(with_overlay):
    _kept = _rs_d.overlay
    if not with_overlay:
        _rs_d.overlay = None
    _surf = pygame.Surface((1920, 1080))
    _surf.fill((0, 0, 0))
    _rs_d.render(_surf)
    _rs_d.overlay = _kept
    return _surf


_ov_with, _ov_without = _ov_frame(True), _ov_frame(False)
_ov_bands = [_dx_scr.geom.bands[_b] for _b in ("left_band", "right_band")]
# THE OUTER FRAME REACHES OUTSIDE THE PANEL, by its own rail and its
# corner brackets — that is what an outer frame is (work order 166
# part B). So the claim is not "the bands are untouched" any more; it
# is that everything that changed lies inside the FRAME's own rect and
# the rest of the band is still map.
_ov_frame_rect = _rf.for_app(_dx_scr.app).around(
    _dx_geo.window_rect(_dx_scr.geom.panel_rect, _dx_scr.layout),
    _rf.REFERENCE_SCALE * _dx_scr.layout.scale)
_ov_seen = _ov_changed = _ov_outside = 0
for _ov_band in _ov_bands:
    _bx, _by, _bw, _bh = _dx_geo.window_rect(_ov_band, _dx_scr.layout)
    for _oy in range(_by, _by + _bh, 2):
        for _ox in range(_bx, _bx + _bw, 2):
            _ov_seen += 1
            if _ov_with.get_at((_ox, _oy))[:3] == \
                    _ov_without.get_at((_ox, _oy))[:3]:
                continue
            _ov_changed += 1
            if not _ov_frame_rect.collidepoint(_ox, _oy):
                _ov_outside += 1
assert _ov_seen > 500, _ov_seen
assert _ov_outside == 0, (
    f"{_ov_outside} of {_ov_changed} changed band pixels lie OUTSIDE "
    f"the frame's own rect — the panel is painting over the map "
    f"instead of sitting on it")
assert _ov_changed > 0, (
    "the frame changed nothing in the bands; it is not being drawn and "
    "the test above is about an empty set")
# …and the panel IS drawn, or the equality above is about nothing.
_px, _py, _pw, _ph = _dx_geo.window_rect(_dx_scr.geom.panel_rect,
                                         _dx_scr.layout)
_ov_panel_diff = sum(
    1 for _oy in range(_py, _py + _ph, 3)
    for _ox in range(_px, _px + _pw, 3)
    if _ov_with.get_at((_ox, _oy))[:3] != _ov_without.get_at((_ox, _oy))[:3])
assert _ov_panel_diff > 500, (
    f"only {_ov_panel_diff} pixels inside the panel differ; this frame "
    f"drew no panel and the band equality above means nothing")

# AND THE PANEL FILLS ITS OWN AREA. `Fill_(s+4, 4, s+0x1D7, 0x1D8, 0)`
# runs before the panel art is drawn over it (tech.cpp:290-291). The
# first build of this overlay left it out, and the galaxy map shone
# THROUGH the rows — clean in the bands, unreadable where the text is,
# and a band-equality check alone is blind to it. So: render the panel
# alone onto a colour nothing else uses. None of it may survive inside
# the fill rectangle, and all of it must survive in the bands.
_OV_THROUGH = (255, 0, 255)
_ov_m = pygame.Surface((1920, 1080))
_ov_m.fill(_OV_THROUGH)
_dx_scr.render(_ov_m)
_ov_inside = sum(
    1 for _oy in range(_py + 3, _py + _ph - 3, 4)
    for _ox in range(_px + 3, _px + _pw - 3, 4)
    if _ov_m.get_at((_ox, _oy))[:3] == _OV_THROUGH)
assert _ov_inside == 0, (
    f"{_ov_inside} sampled pixels inside the panel are still what was "
    f"under it — the panel is not filling its own rectangle and "
    f"whatever is behind shows through the rows")
# In the side bands the fill must not reach at all — OUTSIDE the outer
# frame's own rect, which legitimately has metal in them since work
# order 166 part B.
_ov_band_kept = _ov_band_seen = 0
for _ov_band in _ov_bands:
    _bx, _by, _bw, _bh = _dx_geo.window_rect(_ov_band, _dx_scr.layout)
    for _oy in range(_by, _by + _bh, 8):
        for _ox in range(_bx, _bx + _bw, 8):
            if _ov_frame_rect.collidepoint(_ox, _oy):
                continue
            _ov_band_seen += 1
            _ov_band_kept += _ov_m.get_at((_ox, _oy))[:3] == _OV_THROUGH
assert _ov_band_seen > 1000, _ov_band_seen
assert _ov_band_kept == _ov_band_seen, (
    f"the fill reached the side bands ({_ov_band_seen - _ov_band_kept} "
    f"of {_ov_band_seen}); the original leaves those as map")

# 3. THE THREE HELP BANDS ANSWER OVER THE MAP. They are hidden boxes —
#    hit areas only, so the map shows through them — and a right click
#    in one opens help 255, this screen's own, not the map's.
_ov_help = _sjson.load(open(os.path.join(
    SCREENS_DIR, "research_change", "help.json"), encoding="utf-8"))
assert {_r["help_id"] for _r in _ov_help["regions"]} == {255}
_ov_hidden = {_b["name"] for _b in _sjson.load(open(os.path.join(
    SCREENS_DIR, "research_change", "boxes.json"),
    encoding="utf-8"))["1920x1080"] if _b.get("hidden")}
assert {"left_band", "right_band", "top_band"} <= _ov_hidden, sorted(
    _ov_hidden)
_dx_scr.app.helptext = HelpText(_DxRes(), "en")
_dx_scr.help.close()
_ov_bx, _ov_by, _ov_bw, _ov_bh = _dx_geo.window_rect(
    _dx_scr.geom.bands["left_band"], _dx_scr.layout)
assert _rs_d.top.handle_right_button(
    True, _ov_bx + _ov_bw // 2, _ov_by + _ov_bh // 2) is True
assert _dx_scr.help.visible and _dx_scr.help.help_id == 255, (
    _dx_scr.help.help_id)
_dx_scr.help.close()
_rs_d.close_overlay()
ok("the map is BEHIND the panel, not painted out, and the three help "
   "bands answer over it")
