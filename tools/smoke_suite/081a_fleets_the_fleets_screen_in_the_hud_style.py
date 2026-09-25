# smoke-suite area: fleets
#
# Part of the OrionLayer smoke suite — 081a_fleets_the_fleets_screen_in_the_hud_style.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/, in file-name order and in ONE
# namespace. Do not import this file; it is not a module.
#
# Work order 169, decision 71.
#
# The 1 check(s) it holds:
#   - Fleets in the HUD style: a panel per window, a HUD button behind every control, words in the HUD colour


from core.hud import blocks as _fh_hud
from core.hud import style as _fh_hs
from screens.fleets import fltdraw as _fh_draw
from screens.fleets import flthud as _fh_fh

d.switch_to("fleets")
_fh_scr = d.active
_fh_panels, _fh_buttons = [], []
_fh_real_panel, _fh_real_small = _fh_hud.panel, _fh_hud.small_button
_fh_hud.panel = lambda _s, _r, *_a, **_k: _fh_panels.append(tuple(_r))
_fh_hud.small_button = lambda _s, _r, _sc, _st="normal", *_a, **_k: \
    _fh_buttons.append((tuple(_r), _st))
try:
    _fh_surf = pygame.Surface((1920, 1080))
    _fh_fh.draw_hud(_fh_surf, _fh_scr, enabled={"btn_return"})
finally:
    _fh_hud.panel, _fh_hud.small_button = _fh_real_panel, _fh_real_small
for _fh_n in _fh_fh.HUD_PANELS:
    _fh_r = _fh_draw._rect(_fh_scr, _fh_n)
    assert _fh_r is not None and tuple(_fh_r) in _fh_panels, (
        f"the Fleets window {_fh_n} is not a HUD panel")
_fh_states = {}
for _fh_n, _k in _fh_draw.CONTROL_WORDS:
    _fh_r = tuple(_fh_draw._rect(_fh_scr, _fh_n))
    _fh_states[_fh_n] = next(_st for _r, _st in _fh_buttons if _r == _fh_r)
assert _fh_states["btn_return"] in ("normal", "hover"), _fh_states
assert _fh_states["btn_scrap"] == "disabled", _fh_states
# THE WORDS: a live control's word is the HUD button colour — the
# DEVIATION marked in `draw_labels` (decision 71).
assert "DEVIATION (decision 71" in open(_fh_draw.__file__,
                                         encoding="utf-8").read()
_fh_said = []
_fh_real_rt = _fh_scr.style.render_text
_fh_scr.style.render_text = lambda _t, _sz, _c, *a, **k: (
    _fh_said.append((_t, tuple(_c))), _fh_real_rt(_t, _sz, _c, *a, **k))[1]
try:
    _fh_draw.draw_labels(_fh_surf, _fh_scr, {"return": "Return",
                                              "scrap": "Scrap"},
                         enabled={"btn_return"})
finally:
    _fh_scr.style.render_text = _fh_real_rt
_fh_col = dict(_fh_said)
assert _fh_col["Return"] == _fh_hs.get().colour("text.button.color"), _fh_col
assert _fh_col["Scrap"] != _fh_col["Return"], _fh_col
ok("Fleets in the HUD style: a panel per window, a HUD button behind "
   "every control in its state, live words in the HUD colour")
