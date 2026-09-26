# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 006f_core_panel_glass_and_its_slider.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/, in file-name order and in ONE
# namespace. Do not import this file; it is not a module.
#
# Work order 174 B: glass instead of black on every screen — the
# background under a box, dimmed, under a gradient that follows the
# frame colour — and the Panel glass slider (HD EXTENSION). Core,
# because every screen draws its boxes through the one fill.
#
# The 5 check(s) it holds:
#   - glass on every box: no opaque near-black box left but the named map and picture areas
#   - glass follows the frame colour, and never tints the background
#   - Panel glass slider: persistence, reset, a mod's default, dense stays denser
#   - glass keeps every HUD word at the floor over tints x backgrounds x slider
#   - pictures untouched by the glass at the slider's ends


import json

import numpy as _gl_np

import glass_inventory as _gl_inv
import hud_evidence as _gl_he
from core import backgrounds as _gl_bgs
from core import usersettings as _gl_us
from core.hud import glass as _gl
from core.hud import style as _gl_hs
from core.hud import tint as _gl_tint

assert "HD EXTENSION" in (_gl.__doc__ or ""), "core/hud/glass.py lost its marking"


def _gl_reset():
    _gl.set_value(None)
    _gl_hs.set_tone(None, None, None)
    _gl_bgs.reset()


# 1 — GLASS ON EVERY BOX. `tools/glass_inventory.py` renders every screen,
#     every GAME menu node and the popups over a magenta and over a green
#     background: a box whose pixels do not change with the background
#     does not let it through. What may be left is named here, each for
#     its reason — never a panel, a table, a popup or a text field.
def _gl_excluded(stage, app):
    scr = app.dispatcher.active
    L = app.layout
    rects = []
    if stage == "colony_summary":
        # The original's galaxy map, measured black (transcription).
        rects.append(pygame.Rect(*L.rect(scr.box_rect("galaxy_inset"))).inflate(40, 40))
    if stage == "planets":
        rects.append(scr.box_screen_rect("galaxy_inset"))
    if stage == "fleets":
        # The fleet map window: the engine's picture of the map.
        rects.append(scr.box_screen_rect("inset_map"))
    if stage == "leaders":
        from screens.leaders import ldrdraw, ldrgeom
        rects.append(ldrdraw.rect(L, ldrgeom.GALAXY_BOX).inflate(8, 8))
    if stage == "empire_identity":
        rects.append(scr.box_screen_rect("banner_grid"))   # the banners' art
    if stage == "select_race":
        rects.append(scr.box_screen_rect("race_grid"))     # the portraits
    return [r for r in rects if r is not None]


_gl_stages = _gl_inv.stages()
_gl_left, _gl_seen = [], 0
try:
    for _gl_st in _gl_stages:
        _gl_app = _gl_he.make_app(1920, 1080)
        _gl_he.stage(_gl_app, _gl_st)
        _gl_ex = _gl_excluded(_gl_st, _gl_app)
        for _gl_b in _gl_inv.boxes(_gl_st):
            _gl_r = pygame.Rect(_gl_b["rect"])
            if not any(_e.contains(_gl_r) for _e in _gl_ex):
                _gl_left.append((_gl_st, _gl_b["rect"], _gl_b["colour"],
                                 _gl_b["source"]))
        _gl_seen += 1
finally:
    _gl_reset()
assert _gl_seen >= 20, f"only {_gl_seen} stages examined"
assert not _gl_left, f"boxes that are still opaque and dark: {_gl_left}"
ok(f"glass on every box: {_gl_seen} screens, GAME menu nodes and popups "
   f"rendered over two backgrounds; no opaque near-black box left but the "
   f"named map and picture areas")

# 2 — GLASS FOLLOWS THE FRAME COLOUR, AND NEVER TINTS THE BACKGROUND.
#     Over black the glass IS its gradient: navy under the measured blue,
#     violet under a violet frame, no hue at all under grey and silver,
#     darker under black than under grey. And over any background the
#     difference two frame colours make is the same — the background's
#     share cancels, so the tint never touched it.
_gl_rng = _gl_np.random.default_rng(174)
# Dark enough that the floor never clamps (asserted): a clamp may choose
# another opacity per frame colour, and then the shares would not cancel
# for a reason that is not the tint.
_gl_bg1 = _gl_rng.integers(0, 40, (40, 60, 3)).astype(_gl_np.float32)
_gl_bg2 = _gl_rng.integers(0, 40, (40, 60, 3)).astype(_gl_np.float32)


def _gl_hsv(c):
    import colorsys
    return colorsys.rgb_to_hsv(*(max(0.0, float(v)) / 255.0 for v in c))


try:
    _gl_mean = {}
    for _gl_name, _gl_t in (("blue", (None, None, None)), ("violet", (280, None, None)),
                            ("grey", _gl_tint.NAMED["grey"]),
                            ("silver", _gl_tint.NAMED["silver"]),
                            ("black", _gl_tint.NAMED["black"])):
        _gl_hs.set_tone(*_gl_t)
        _gl_mean[_gl_name] = _gl.fill(None, 60, 40).reshape(-1, 3).mean(axis=0)
    _h = {k: _gl_hsv(v) for k, v in _gl_mean.items()}
    assert 0.5 < _h["blue"][0] < 0.72 and _h["blue"][1] > 0.4, _h["blue"]
    assert 0.72 < _h["violet"][0] < 0.86 and _h["violet"][1] > 0.3, _h["violet"]
    assert _h["grey"][1] < 0.08 and _h["silver"][1] < 0.08, (_h["grey"], _h["silver"])
    assert _h["black"][2] < _h["grey"][2], (_h["black"], _h["grey"])
    _gl_hs.set_tone(None, None, None)
    _gl.clear_clamps()
    _a1, _a2 = _gl.fill(_gl_bg1, 60, 40), _gl.fill(_gl_bg2, 60, 40)
    _gl_hs.set_tone(280, None, None)
    _b1, _b2 = _gl.fill(_gl_bg1, 60, 40), _gl.fill(_gl_bg2, 60, 40)
    assert not _gl.clamps, _gl.clamps
    assert _gl_np.abs((_b1 - _a1) - (_b2 - _a2)).max() < 1e-3, \
        "the frame colour changed the background's share of the glass"
finally:
    _gl_reset()
ok("glass follows the frame colour (navy, violet, no hue under grey and "
   "silver, darkest under black) and never tints the background under it")

# 3 — THE SLIDER: stored as the player's value, back after a restart,
#     RESET to the measured position, a mod may move the default, and the
#     dense variant moves with it and stays denser.
from screens.game_menu import gmorion as _gl_gmo
import tempfile as _gl_tmp
_gl_dir = _gl_tmp.mkdtemp()
try:
    class _GlScreen:
        class app:
            user_settings = _gl_us.UserSettings(
                path=os.path.join(_gl_dir, "user_settings.json"))
    _gl_gmo.set_glass(_GlScreen, 0.8)
    assert abs(_gl.value() - 0.8) < 1e-6
    assert _GlScreen.app.user_settings.get("hud_glass") == 0.8
    _gl_us.save(_GlScreen.app.user_settings)
    _gl.set_value(None)
    _gl_back = _gl_us.load(os.path.join(_gl_dir, "user_settings.json"))
    _gl_hs.apply_settings(_gl_back)
    assert abs(_gl.value() - 0.8) < 1e-6, "the slider did not survive a restart"
    _gl_gmo.set_glass(_GlScreen, None)
    assert _gl._value is None and _gl.value() == _gl.default() == 0.5
    assert _GlScreen.app.user_settings.get("hud_glass") is None
    assert "glass" in _gl_gmo.BANDS
    # A mod's default: a partial style.json (decision 72).
    from core import usermod as _gl_um
    _gl_mod = os.path.join(_gl_dir, "mod")
    os.makedirs(_gl_mod)
    with open(os.path.join(_gl_mod, "style.json"), "w") as _f:
        json.dump({"chosen": {"glass": {"slider_default": 0.7}}}, _f)
    _gl_um.init(True, _gl_mod)
    _gl_hs.reset()
    assert _gl.default() == 0.7 and _gl.value() == 0.7
    _gl_um.shutdown()
    _gl_hs.reset()
    for _v in (0.0, 0.25, 0.5, 0.75, 0.99):
        _n, _d = _gl.transparency(False, _v), _gl.transparency(True, _v)
        assert _d < _n, (_v, _n, _d)
    assert _gl.transparency(False, 1.0) == 0.0 == _gl.transparency(True, 1.0)
    assert _gl.transparency(False, 0.5) == 1.0
finally:
    _gl_reset()
ok("Panel glass slider: stored as the player's value and back after a "
   "restart, RESET to the measured 0.5, a mod's style.json moves the "
   "default, the dense variant stays denser at every position")

# 4 — THE FLOOR over tints x backgrounds x slider (170/171: every HUD word
#     >= 4.5:1). The panels every screen draws are collected once; for
#     each background (the universal picture, a bright procedural nebula
#     like 173's demo mod, and plain white as the worst case), each of
#     five frame colours and five slider positions, the brightest glass
#     pixel under each panel must leave the dimmest HUD word at the floor.
#     Where a position would not, that panel was made denser — counted.
if slow("glass_floor"):
    from core.hud import blocks as _gl_blk
    _gl_rects = set()
    _gl_real = _gl_blk.panel

    def _gl_spy(surface, rect, scale, lit=False, filled=True, dense=False):
        if filled:
            _gl_rects.add((tuple(pygame.Rect(rect)), dense))
        return _gl_real(surface, rect, scale, lit, filled, dense)
    _gl_blk.panel = _gl_spy
    try:
        for _gl_st in _gl_stages:
            _gl_app = _gl_he.make_app(1920, 1080)
            _gl_he.stage(_gl_app, _gl_st)
            _gl_s = pygame.Surface((1920, 1080))
            _gl_app.dispatcher.active.render(_gl_s)
            if _gl_app.dispatcher.overlay_name:
                _gl_app.dispatcher.screens[_gl_app.dispatcher.overlay_name].render(_gl_s)
    finally:
        _gl_blk.panel = _gl_real
    _gl_uni = pygame.surfarray.array3d(_gl_bgs.cover(pygame.image.load(
        os.path.join(os.path.dirname(SCREENS_DIR), _gl_bgs.UNIVERSAL)),
        1920, 1080)).transpose(1, 0, 2).astype(_gl_np.float32)
    _yy, _xx = _gl_np.mgrid[0:1080, 0:1920]
    _neb = (0.5 + 0.5 * _gl_np.sin(_xx / 97.0) * _gl_np.cos(_yy / 61.0))
    _gl_demo = _gl_np.dstack([_neb * 200, _neb * 60, _neb * 180]).astype(_gl_np.float32)
    _gl_white = _gl_np.full((1080, 1920, 3), 255.0, _gl_np.float32)
    _gl_worst, _gl_n, _gl_clamped = 99.0, 0, 0
    try:
        for _gl_bgname, _gl_bg in (("universal", _gl_uni), ("demo", _gl_demo),
                                   ("white", _gl_white)):
            for _gl_t in ((None, None, None), (280, None, None),
                          _gl_tint.NAMED["silver"], _gl_tint.NAMED["grey"],
                          _gl_tint.NAMED["black"]):
                _gl_hs.set_tone(*_gl_t)
                _limit = _gl.word_floor_lum()
                _tmin = (_limit + 0.05) * 4.5 - 0.05
                for _v in (0.0, 0.25, 0.5, 0.75, 1.0):
                    _gl.set_value(_v)
                    _gl.clear_clamps()
                    for (_x, _y, _w, _h2), _dense in sorted(_gl_rects):
                        _r = pygame.Rect(_x, _y, _w, _h2).clip((0, 0, 1920, 1080))
                        if _r.w < 4 or _r.h < 4:
                            continue
                        _under = _gl_bg[_r.y:_r.bottom, _r.x:_r.right]
                        _px = _gl.fill(_under, _r.w, _r.h, _dense, rect=_r)
                        # The glass AS DRAWN, by the floor's own statistic.
                        _top = _gl.peak_lum(_px)
                        _cr = (_tmin + 0.05) / (_top + 0.05)
                        _gl_worst = min(_gl_worst, _cr)
                        _gl_n += 1
                    _gl_clamped += len(_gl.clamps)
    finally:
        _gl_reset()
    assert _gl_n > 2000, f"only {_gl_n} panel measurements"
    assert _gl_worst >= 4.5 - 0.01, f"a HUD word falls to {_gl_worst:.2f}:1 on glass"
    report(f"glass floor: {len(_gl_rects)} panels x 3 backgrounds x 5 frame "
           f"colours x 5 slider positions, worst {_gl_worst:.2f}:1; "
           f"{_gl_clamped} panel builds made denser to keep it")
    ok(f"glass keeps every HUD word at the 4.5:1 floor over tints x "
       f"backgrounds x slider ({_gl_n} panel measurements, worst "
       f"{_gl_worst:.2f}:1)")

# 5 — PICTURES UNTOUCHED at the slider's ends: New Game's five pictures
#     are their source at see-through and at solid (172's rule; 006c holds
#     it over the frame colours).
_gl_pn = 0
try:
    for _v in (0.0, 1.0):
        _gl.set_value(_v)
        _gl_app = _gl_he.make_app(2560, 1440)
        _gl_he.stage(_gl_app, "new_game")
        _gl_ng = _gl_app.dispatcher.active
        _gl_s = pygame.Surface((2560, 1440))
        _gl_ng.render(_gl_s)
        from core.hud import blocks as _gl_blk2
        for _gl_cat, _gl_slot in _gl_ng._cfg["setting_slots"].items():
            _gl_panel = pygame.Rect(*_gl_ng._hd_to_screen(*_gl_slot["rect"]))
            _gl_src = _gl_ng.setting_picture(_gl_cat, _gl_panel)
            _gl_in = _gl_blk2.panel_inner(_gl_panel, _gl_app.layout.scale)
            _a = pygame.surfarray.array3d(_gl_s.subsurface(_gl_in))
            _b = pygame.surfarray.array3d(_gl_src)
            assert (_a == _b).all(), (_v, _gl_cat)
            _gl_pn += 1
finally:
    _gl_reset()
ok(f"pictures untouched by the glass: New Game's pictures are their source "
   f"at the slider's two ends ({_gl_pn} comparisons)")
