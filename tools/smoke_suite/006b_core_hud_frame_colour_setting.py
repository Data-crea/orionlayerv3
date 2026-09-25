# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 006b_core_hud_frame_colour_setting.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/, in file-name order and in ONE
# namespace. Do not import this file; it is not a module.
#
# Work order 170: the HUD frame colour, an HD EXTENSION set in the GAME
# menu's Settings dialog (`core/hud/tint.py`, `screens/game_menu/gmorion.py`).
#
# The 3 check(s) it holds:
#   - hud frame colour: the default is the measured blue, the never-recolour list holds, code and pieces agree
#   - hud frame colour: persists, applies without a restart, every word readable at every hue
#   - hud frame colour: grey, silver and black reachable and usable (work order 171)


import colorsys as _fc_cs
import tempfile as _fc_tmp

import numpy as _fc_np

from core import usersettings as _fc_us
from core.hud import art as _fc_art
from core.hud import blocks as _fc_blk
from core.hud import style as _fc_hs
from core.hud import tint as _fc_tint

_fc_hs.set_tone(None, None, None)
_fc_st = _fc_hs.get()
_fc_meas = _fc_st.measured

# 1 — THE DEFAULT IS THE MEASURED BLUE. With no setting every colour the
#     blocks read is style.json's own value, and the reference hue is the
#     measured panel edge's, re-derived here rather than trusted.
assert _fc_tint.hue() is None and _fc_us.DEFAULTS["hud_hue"] is None
for _fc_path in ("panel.fill", "panel.edge", "panel.glow", "separator.color",
                 "button.edge", "button.underline", "action.edge",
                 "mockup_colony.selected", "mockup_colony.scroll_thumb"):
    _fc_raw = _fc_st._walk(_fc_meas, _fc_path)
    assert _fc_st.colour(_fc_path) == tuple(_fc_raw), _fc_path
_fc_h = _fc_cs.rgb_to_hls(*[_v / 255 for _v in _fc_meas["panel"]["edge"]])[0]
assert round(_fc_h * 360) == _fc_tint.REFERENCE, (
    f"tint.REFERENCE {_fc_tint.REFERENCE} is not the measured panel "
    f"edge's hue {_fc_h * 360:.1f}")
# Every accent the style measured lies in the band, and nothing that
# must never turn does: the red negative, the orange lamps' hue.
for _fc_path in ("panel.edge", "panel.fill", "action.edge", "button.edge",
                 "separator.color", "mockup_colony.selected"):
    _fc_hh = _fc_cs.rgb_to_hls(*[_v / 255 for _v in
                                 _fc_st._walk(_fc_meas, _fc_path)])[0] * 360
    assert _fc_tint.in_band(_fc_hh), (_fc_path, _fc_hh)
assert not _fc_tint.in_band(_fc_cs.rgb_to_hls(
    *[_v / 255 for _v in _fc_meas["text"]["negative"]["color"]])[0] * 360)

# 2 — THE NEVER-RECOLOUR LIST, at a hue far from blue (20, a red).
# SINCE WORK ORDER 171 the accent labels follow (`WORDS_THAT_FOLLOW`,
# 170 P5 decided); every other word stays.
_fc_before_text = {_k: _fc_st.colour(f"text.{_k}.color")
                   for _k in _fc_meas["text"]
                   if not _fc_hs.follows_as_word(f"text.{_k}.color")}
_fc_follow_lum = {_p: _fc_tint.luminance(_fc_st.colour(_p))
                  for _p in _fc_hs.WORDS_THAT_FOLLOW}
_fc_before_ph = _fc_st.colour("background_placeholder")
_fc_before_pal = palette.col("galaxy_map", "owner_0", (1, 2, 3))
_fc_hs.set_hue(20)
try:
    assert _fc_st.colour("panel.edge") != tuple(_fc_meas["panel"]["edge"])
    for _k, _c in _fc_before_text.items():
        assert _fc_st.colour(f"text.{_k}.color") == _c, (
            f"text.{_k} turned with the frame colour")
    # An accent label turns, at its own luminance.
    for _p, _l in _fc_follow_lum.items():
        assert abs(_fc_tint.luminance(_fc_st.colour(_p)) - _l) < 0.01, _p
    assert _fc_st.colour("text.label.color") != tuple(
        _fc_meas["text"]["label"]["color"]), "the labels did not follow"
    assert _fc_st.colour("background_placeholder") == _fc_before_ph
    assert palette.col("galaxy_map", "owner_0", (1, 2, 3)) == _fc_before_pal
    # The pieces: what is in FOLLOWS turns, the picture icons never, and
    # inside a turned piece every pixel outside the band stays — the
    # title plate's orange lamps.
    assert not ({"icon_treasury", "icon_command", "icon_food",
                 "icon_freighters", "icon_research"} & _fc_tint.FOLLOWS)
    _fc_plate = _hc_pieces()["title_plate"][0][..., :3]
    _fc_turned = _fc_tint.rotate_pixels(_fc_plate)
    _fc_x = _fc_plate.astype(float) / 255
    _fc_mx, _fc_mn = _fc_x.max(axis=2), _fc_x.min(axis=2)
    _fc_c = _fc_mx - _fc_mn
    _fc_safe = _fc_np.where(_fc_c == 0, 1, _fc_c)
    _fc_hue = _fc_np.where(_fc_mx == _fc_x[..., 0],
                           ((_fc_x[..., 1] - _fc_x[..., 2]) / _fc_safe) % 6,
                           _fc_np.where(_fc_mx == _fc_x[..., 1],
                                        (_fc_x[..., 2] - _fc_x[..., 0])
                                        / _fc_safe + 2,
                                        (_fc_x[..., 0] - _fc_x[..., 1])
                                        / _fc_safe + 4)) * 60
    _fc_warm = (_fc_c > 0.3) & (_fc_hue < 60)
    assert _fc_warm.sum() > 100, "the title plate has no orange lamp pixels"
    assert (_fc_turned[_fc_warm] == _fc_plate[_fc_warm]).all(), (
        "the title plate's orange lamps turned with the frame colour")
    # CODE AND PIECES AGREE: the per-pixel rule is the per-colour rule.
    _fc_grid = _fc_np.array([[[r, g, b] for b in range(0, 256, 51)
                              for g in range(0, 256, 51)
                              for r in range(0, 256, 51)]], _fc_np.uint8)
    _fc_px = _fc_tint.rotate_pixels(_fc_grid)[0]
    for _fc_i, _fc_rgb in enumerate(_fc_grid[0]):
        _fc_one = _fc_tint.rotate(tuple(int(_v) for _v in _fc_rgb))
        assert max(abs(int(_a) - _b) for _a, _b in
                   zip(_fc_px[_fc_i], _fc_one)) <= 1, (_fc_rgb, _fc_one)
finally:
    _fc_hs.set_tone(None, None, None)
ok("hud frame colour: the default is the measured blue, the never-recolour "
   "list holds (values and white words, placeholder, player colours, "
   "picture icons, the plate's lamps), accent labels follow at their own "
   "luminance, code and pieces turn by one rule")

# 3 — PERSISTS, APPLIES AT ONCE, STAYS READABLE.
_fc_dir = _fc_tmp.TemporaryDirectory()
_fc_path = os.path.join(_fc_dir.name, "user_settings.json")
_fc_set = _fc_us.UserSettings(path=_fc_path)
_fc_set.set("hud_hue", 120)
assert _fc_us.save(_fc_set) is True
_fc_back = _fc_us.load(_fc_path)
assert _fc_back.get("hud_hue") == 120
# A 170 file (hud_hue alone) reads the other two as measured.
assert _fc_back.get("hud_sat") is None and _fc_back.get("hud_bright") is None
_fc_set.set("hud_sat", 0.0)
_fc_set.set("hud_bright", 0.1)
_fc_us.save(_fc_set)
_fc_back2 = _fc_us.load(_fc_path)
assert (_fc_back2.get("hud_sat"), _fc_back2.get("hud_bright")) == (0.0, 0.1)
assert ("hudstyle.apply_settings(self.user_settings)" in
        open(os.path.join(os.path.dirname(SCREENS_DIR), "main.py"),
             encoding="utf-8").read()), "main.App no longer applies the tone"
_fc_hs.apply_settings(_fc_back2)
assert (_fc_tint._sat, _fc_tint._bright) == (0.0, 0.1)
_fc_hs.set_tone(None, None, None)
_fc_main = open(os.path.join(os.path.dirname(SCREENS_DIR), "main.py"),
                encoding="utf-8").read()
assert "hudstyle.apply_settings(" in _fc_main, (
    "main.App no longer applies the saved frame colour at start")
# Without a restart: the same panel, the same size, drawn before and
# after a change, differs — the caches were rebuilt — and comes back
# byte for byte when the setting does.
_fc_r = pygame.Rect(10, 10, 200, 120)


def _fc_draw():
    _s = pygame.Surface((240, 160))
    _s.fill((0, 0, 0))
    _fc_blk.panel(_s, _fc_r, 1.0)
    return pygame.image.tostring(_s, "RGB")


_fc_a = _fc_draw()
_fc_hs.set_hue(_fc_back.get("hud_hue"))
_fc_b = _fc_draw()
_fc_hs.set_tone(None, None, None)
_fc_c2 = _fc_draw()
assert _fc_a != _fc_b and _fc_a == _fc_c2, (
    "the frame colour did not apply at once, or did not come back")
_fc_dir.cleanup()


def _fc_lum(c):
    def ch(v):
        v = v / 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(v) for v in c[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


# READABLE AT EVERY POSITION: every HUD word against every fill it can
# sit on, at every hue in 5-degree steps — WCAG contrast, 4.5 floor.
_fc_fills = ("panel.fill", "panel.fill_edge", "button.fill",
             "button.hover_fill", "button.active_fill", "action.fill",
             "mockup_colony.selected", "mockup_colony.row_a",
             "mockup_colony.row_b", "mockup_colony.header")
_fc_words = [f"text.{_k}.color" for _k in _fc_meas["text"]
             if _k != "negative"] + ["mockup_colony.text_header",
                                     "mockup_colony.text_row"]
_fc_worst = (99.0, None)
# THE WHOLE CONTROL RANGE (work order 171): hue in 15-degree steps,
# saturation at both ends and the middle, brightness at both ends, the
# middle and the measured value.
_fc_grid = [(_h, _s, _b) for _h in range(0, 360, 15)
            for _s in (0.0, 0.5, 1.0)
            for _b in (_fc_tint.BRIGHT_RANGE[0], 0.5, 1.0,
                       _fc_tint.BRIGHT_RANGE[1])]
try:
    for _fc_deg, _fc_s, _fc_b in _fc_grid:
        _fc_hs.set_tone(_fc_deg, _fc_s, _fc_b)
        for _f in _fc_fills:
            _fl = _fc_lum(_fc_st.colour(_f))
            for _w in _fc_words:
                _wl = _fc_lum(_fc_st.colour(_w))
                _cr = (max(_fl, _wl) + 0.05) / (min(_fl, _wl) + 0.05)
                if _cr < _fc_worst[0]:
                    _fc_worst = (_cr, (_fc_deg, _fc_s, _fc_b, _f, _w))
finally:
    _fc_hs.set_tone(None, None, None)
assert _fc_worst[0] >= 4.5, (
    f"a HUD word falls below 4.5:1 at {_fc_worst[1]} ({_fc_worst[0]:.2f})")
report(f"hud frame colour: worst word contrast over {len(_fc_grid)} settings "
       f"{_fc_worst[0]:.2f}:1 at {_fc_worst[1]}")
ok("hud frame colour: persists through user_settings.json (all three, and "
   "a 170 file still reads), applies without a restart and comes back "
   "byte for byte, every word readable (>= 4.5:1) over the whole control "
   "range")

# 4 — GREY, SILVER AND BLACK ARE REACHABLE, AND STAY USABLE (171).
#     Each named setting is inside the controls' ranges, turns the
#     accent neutral, and keeps the edge floors: every edge 3:1 against
#     every fill (WCAG 1.4.11), the lit edge 2:1 against a normal one.
_fc_fills_all = ("panel.fill", "panel.fill_edge", "button.fill",
                 "action.fill", "mockup_colony.selected",
                 "mockup_colony.row_a", "mockup_colony.row_b",
                 "mockup_colony.header", "mockup_colony.scroll_track")
_fc_edges = ("panel.edge", "panel.edge_dim", "separator.color",
             "button.edge", "action.edge", "mockup_colony.selected_edge",
             "mockup_colony.scroll_thumb")
# THE MEASURED BLUE IS NOT ITSELF AT 3:1 EVERYWHERE — the dim edge
# (panel top/bottom, the cell outlines) sits at 2.2:1 on the panel fill
# by Data's design. So the promise is: at every named setting each edge
# is at 3:1 OR at least as visible as in the measured blue.
def _fc_cr(_a, _b):
    _la, _lb = _fc_tint.luminance(_a), _fc_tint.luminance(_b)
    return (max(_la, _lb) + 0.05) / (min(_la, _lb) + 0.05)


_fc_base_cr = {(_e, _f): _fc_cr(_fc_st.colour(_e), _fc_st.colour(_f))
               for _e in _fc_edges for _f in _fc_fills_all}
# THE WHOLE RANGE FIRST, then the named settings on top of it.
_fc_bgrid = [round(_fc_tint.BRIGHT_RANGE[0] + _i * 0.1, 2)
             for _i in range(int((_fc_tint.BRIGHT_RANGE[1]
                                  - _fc_tint.BRIGHT_RANGE[0]) / 0.1) + 1)]
_fc_range = [(None, _s, _b) for _s in (0.0, 0.5, 1.0) for _b in _fc_bgrid]
try:
    for _fc_h2, _fc_s2, _fc_b2 in _fc_range:
        _fc_hs.set_tone(_fc_h2, _fc_s2, _fc_b2)
        for _e in _fc_edges:
            for _f in _fc_fills_all:
                _now = _fc_cr(_fc_st.colour(_e), _fc_st.colour(_f))
                assert _now >= min(3.0, _fc_base_cr[(_e, _f)]) - 0.05, (
                    f"s {_fc_s2} b {_fc_b2}: {_e} against {_f} is "
                    f"{_now:.2f}:1")
        assert _fc_cr(_fc_st.colour("action.edge"),
                      _fc_st.colour("button.edge")) >= 2.0 or \
            _fc_b2 >= 1.0, (_fc_s2, _fc_b2, "hover/active not visible")
finally:
    _fc_hs.set_tone(None, None, None)
try:
    for _fc_n, (_fc_h2, _fc_s2, _fc_b2) in _fc_tint.NAMED.items():
        assert _fc_tint.SAT_RANGE[0] <= _fc_s2 <= _fc_tint.SAT_RANGE[1]
        assert (_fc_tint.BRIGHT_RANGE[0] <= _fc_b2
                <= _fc_tint.BRIGHT_RANGE[1]), _fc_n
        _fc_hs.set_tone(_fc_h2, _fc_s2, _fc_b2)
        _fc_e = _fc_st.colour("panel.edge")
        assert max(_fc_e) - min(_fc_e) <= 2, (_fc_n, "not neutral", _fc_e)
        for _e in _fc_edges:
            for _f in _fc_fills_all:
                _now = _fc_cr(_fc_st.colour(_e), _fc_st.colour(_f))
                assert _now >= min(3.0, _fc_base_cr[(_e, _f)]) - 0.05, (
                    f"{_fc_n}: {_e} against {_f} is {_now:.2f}:1, under "
                    f"both 3:1 and the measured blue's "
                    f"{_fc_base_cr[(_e, _f)]:.2f}:1")
        _fc_lit = _fc_tint.luminance(_fc_st.colour("action.edge"))
        _fc_norm = _fc_tint.luminance(_fc_st.colour("button.edge"))
        assert (_fc_lit + 0.05) / (_fc_norm + 0.05) >= 2.0, (
            f"{_fc_n}: hover/active not visible against a normal edge")
finally:
    _fc_hs.set_tone(None, None, None)
ok(f"hud frame colour: {', '.join(_fc_tint.NAMED)} reachable from the "
   f"controls; over {len(_fc_range)} tone settings and at each of those "
   f"controls, neutral, every edge at 3:1 or as visible as the measured "
   f"blue on every fill (EDGE_FLOOR "
   f"{_fc_tint.EDGE_FLOOR}), the lit edge >= 2:1 over a normal one "
   f"(LIT_FLOOR {_fc_tint.LIT_FLOOR})")
