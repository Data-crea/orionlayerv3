# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 006a_core_hud_style_blocks_and_cut_pieces.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/, in file-name order and in ONE
# namespace. Do not import this file; it is not a module.
#
# Work order 169, decision 71: the HUD style that replaced the cockpit
# frames on every screen. Core, because every screen draws these blocks
# and none owns them.
#
# The 5 check(s) it holds:
#   - hud style.json's measured block == tools/hud_measure.py
#   - hud cut pieces rebuild byte for byte, and the names agree both ways
#   - hud blocks draw at three sizes, edges at their measured width
#   - hud slanted button: drawn shape and hit shape agree
#   - hud: no screen loads a frame image, and the background slot is filled


import json as _hj
import tempfile as _htmp

import hud_cut as _hcut
import hud_measure as _hmeas
from core.hud import art as _hart
from core.hud import blocks as _hblk
from core.hud import raster as _hras
from core.hud import style as _hsty

# 1 — THE STYLE FILE IS HELD TO THE TOOL. `measured` is a copy of what
#     `tools/hud_measure.py` measures off the two committed images, and a
#     copy is legitimate only with a checker. The colony mockup is not in
#     the tree; its block is REPORTED, never checked (a check that read
#     ~/Downloads would pass on one machine only).
_hs_file = _hj.load(open(os.path.join(os.path.dirname(SCREENS_DIR), "assets",
                                      "shared", "hud", "style.json")))
_hs_got = _hmeas.measure()
_hs_stored = {k: v for k, v in _hs_file["measured"].items()
              if k != "mockup_colony"}
_hs_bad = _hmeas.compare(_hs_got, _hs_stored)
assert not _hs_bad, (
    f"assets/shared/hud/style.json's measured block differs from "
    f"tools/hud_measure.py in {len(_hs_bad)} value(s), first "
    f"{_hs_bad[:3]}. Edit the artwork or the tool, never the copy")
_hs_colony = _hs_file["measured"]["mockup_colony"]
assert _hs_colony["sha256"] == _hmeas.hud_colony.COLONY_SHA256
report(f"hud style: {len(_hs_colony) - 1} table values from Data's colony "
       f"mockup (sha256 {_hs_colony['sha256'][:12]}…), not in the tree — "
       f"re-measure with tools/hud_measure.py --colony <png>")
# Every `*_from` indirection in `chosen` names a value that exists.
_hsty.reset()
_hs = _hsty.get()
for _hs_k, _hs_v in _hs_file["chosen"].items():
    if isinstance(_hs_v, dict):
        for _hs_kk, _hs_vv in _hs_v.items():
            if _hs_kk.endswith("_from"):
                _hs.colour(_hs_vv)
ok(f"hud style.json's measured block == tools/hud_measure.py "
   f"({sum(1 for _ in _hmeas.compare(_hs_got, {})) } values)")


# 2 — THE CUT PIECES ARE DERIVED (decision 40): rebuilt into a scratch
#     folder and compared byte for byte with what setup built. Absent is
#     a state that is REPORTED and named, and the check still counts
#     (decision 49's pattern): the rebuild itself is asserted either way.
_hc_cache = {}


def _hc_pieces():
    """hud_cut.cut(), once per run: name -> (array, box)."""
    if not _hc_cache:
        _hc_cache.update(_hcut.cut())
    return _hc_cache


_hc_dir = _htmp.mkdtemp(prefix="hud_cut_")
_hc_names = _hcut.write(_hc_dir)
_hc_tree = os.path.join(os.path.dirname(SCREENS_DIR), "assets", "shared",
                        "hud", "cut")
_hc_have = [n for n in _hc_names
            if os.path.exists(os.path.join(_hc_tree, n + ".png"))]
for _hc_n in _hc_have:
    assert open(os.path.join(_hc_dir, _hc_n + ".png"), "rb").read() == \
        open(os.path.join(_hc_tree, _hc_n + ".png"), "rb").read(), (
        f"assets/shared/hud/cut/{_hc_n}.png is not what tools/hud_cut.py "
        f"builds — run python tools/setup.py")
if len(_hc_have) < len(_hc_names):
    report(f"hud cut pieces: {len(_hc_names) - len(_hc_have)} of "
           f"{len(_hc_names)} not built here — python tools/setup.py")
assert sorted("icon_" + k for k in _hart.ICONS) + [_hart.TITLE_PLATE] == \
    sorted(_hc_names), ("core.hud.art.ICONS and tools/hud_cut.ICONS name "
                        "different icons", _hc_names)
ok(f"hud cut pieces rebuild byte for byte ({len(_hc_have)} of "
   f"{len(_hc_names)} present), and the names agree both ways")


# 3 — EVERY BLOCK DRAWS, AT THREE SIZES, AND ITS EDGE IS THE MEASURED
#     WIDTH. The edge line is read back off the drawn panel: a horizontal
#     profile through its middle, the run of pixels at least half-way to
#     the edge colour's brightness, in device px, against
#     `panel.edge_width` times the scale (a supersampled edge may spread
#     one px either side).
_hb_font = app.style
for _hb_w, _hb_h in ((1920, 1080), (2560, 1440), (3840, 2160)):
    _hb_s = _hb_w / 1920
    _hb_surf = pygame.Surface((_hb_w, _hb_h))
    _hb_surf.fill((0, 0, 0))
    _hb_r = pygame.Rect(int(100 * _hb_s), int(100 * _hb_s),
                        int(300 * _hb_s), int(400 * _hb_s))
    _hblk.panel(_hb_surf, _hb_r, _hb_s)
    _hb_y = _hb_r.centery
    _hb_row = [sum(_hb_surf.get_at((_x, _hb_y))[1:3])
               for _x in range(_hb_r.x - 6, _hb_r.x + int(30 * _hb_s))]
    _hb_peak = max(_hb_row)
    _hb_run = sum(1 for _v in _hb_row if _v >= _hb_peak * 0.75)
    _hb_want = _hs.get("panel.edge_width") * _hb_s
    assert abs(_hb_run - _hb_want) <= 1.6 + 0.35 * _hb_s, (
        f"{_hb_w}x{_hb_h}: the panel's edge line is {_hb_run} px, the "
        f"style says {_hb_want:.1f}")
    assert _hb_peak >= 0.8 * sum(_hs.colour("panel.edge")[1:3]), _hb_peak
    for _hb_st in _hblk.STATES:
        _hblk.slant_button(_hb_surf, pygame.Rect(0, 0, int(250 * _hb_s),
                           int(62 * _hb_s)), _hb_s, _hb_st, "Colonies",
                           icon="colonies", style_renderer=_hb_font)
    _hblk.action_button(_hb_surf, pygame.Rect(0, 0, int(282 * _hb_s),
                        int(73 * _hb_s)), _hb_s, "normal", "Turn", "turn",
                        _hb_font)
    _hblk.small_button(_hb_surf, pygame.Rect(0, 0, int(120 * _hb_s),
                       int(36 * _hb_s)), _hb_s, "hover", "Close",
                       style_renderer=_hb_font)
    _hblk.popup(_hb_surf, _hb_r, _hb_s)
    _hblk.outline(_hb_surf, _hb_r, _hb_s)
    _hblk.table_header(_hb_surf, _hb_r, _hb_s)
    _hblk.table_row(_hb_surf, _hb_r, _hb_s, 1, selected=True)
    _hblk.scrollbar(_hb_surf, _hb_r, _hb_s, 3, 10, 30)
    _hblk.separator(_hb_surf, 0, 100, 50, _hb_s)
    _hblk.title_plate(_hb_surf, _hb_w // 2, 0, _hb_s, "Game", _hb_font)
# The cache is per size and state, and bounded.
assert 0 < len(_hblk._CACHE) <= _hblk._CACHE_MAX
_hb_key = [k for k in _hblk._CACHE if k[0] == "slant"]
assert len({k[4] for k in _hb_key if k[1] == 250}) == 4, _hb_key
ok("hud blocks draw at three sizes, the panel edge at its measured "
   "width, the button in four cached states")


# 4 — THE HIT SHAPE IS THE DRAWN SHAPE (decision 5). A slanted button is
#     a parallelogram; its box's corners are NOT the button, and a click
#     there must not activate it. Every pixel of a 1080p button is asked:
#     drawn opaque inside the edge <=> hit.
_hh_r = pygame.Rect(40, 40, 250, 62)
_hh_s = pygame.Surface((340, 150), pygame.SRCALPHA)
_hh_s.fill((0, 0, 0, 0))
_hh_built, _hh_pad = _hras.shape(
    lambda w, h: _hras.slanted(w, h, _hs.get("button.slant")),
    _hh_r.w, _hh_r.h, fill=(10, 10, 10), edge=(200, 200, 200), edge_w=1.4)
_hh_s.blit(_hh_built, (_hh_r.x - _hh_pad, _hh_r.y - _hh_pad))
_hh_bad = 0
for _y in range(_hh_r.y, _hh_r.bottom):
    for _x in range(_hh_r.x, _hh_r.right):
        _a = _hh_s.get_at((_x, _y))[3]
        if _a in range(40, 216):
            continue            # the antialiased rim: either answer is fair
        if (_a >= 216) != _hblk.slant_hit(_hh_r, _x, _y):
            _hh_bad += 1
assert _hh_bad == 0, f"{_hh_bad} pixels drawn and hit disagree"
assert not _hblk.slant_hit(_hh_r, _hh_r.x + 2, _hh_r.y + 2), \
    "the top-left corner of a slanted button's box hit the button"
ok("hud slanted button: drawn shape and hit shape agree on every pixel")


# 5 — THE NEW STYLE IS WHAT EVERY SCREEN DRAWS: no screen loads a frame
#     image any more (the images and `_load_frame` stay in the tree, as
#     the order that recorded 71 asks), and a screen without a picture in
#     its background slot draws the placeholder, never the old cockpit
#     texture.
_hf_loaders = []
for _hf_root, _hf_dirs, _hf_files in os.walk(SCREENS_DIR):
    for _hf_f in _hf_files:
        if _hf_f.endswith(".py"):
            _hf_src = open(os.path.join(_hf_root, _hf_f),
                           encoding="utf-8").read()
            if "self._load_frame(" in _hf_src:
                _hf_loaders.append(os.path.join(_hf_root, _hf_f))
# WHILE WORK ORDER 169 CONVERTS THE SCREENS ONE COMMIT AT A TIME, the ones
# not yet converted are named here, and the list may only shrink: a screen
# on it that stops loading its frame fails until it is taken off. The
# order's last commit leaves it empty.
_HF_PENDING = set()
_HF_BG_PENDING = set()
from core.screen_base import ScreenBase
_hf_now = {os.path.basename(os.path.dirname(_p)) for _p in _hf_loaders}
assert _hf_now == _HF_PENDING, (
    f"screens loading a frame image {sorted(_hf_now)}, pending list "
    f"{sorted(_HF_PENDING)}: a converted screen comes off the list, and "
    f"no screen goes back on it")
# THE BACKGROUND SLOT IS FILLED (work order 173): every screen stands on
# the picture `core.backgrounds` gives it — its own where the tree ships
# one (the Main Menu's title art), Data's universal picture everywhere
# else. Asserted by DRAWING each screen's `_render_background` (the
# research panel overrides it) and comparing it with the universal
# picture cover-scaled to the window.
from core import backgrounds as _hf_bgs
_hf_bgs.reset()
_hf_uni = _hf_bgs.cover(pygame.image.load(os.path.join(
    os.path.dirname(SCREENS_DIR), _hf_bgs.UNIVERSAL)), 1920, 1080)
_hf_uni_px = pygame.image.tobytes(_hf_uni, "RGB")
_hf_n, _hf_own = 0, []
for _hf_name in sorted(d.screens):
    _hf_scr = d.screens[_hf_name]
    if _hf_scr.IS_OVERLAY or not hasattr(_hf_scr, "_render_background"):
        continue
    _hf_surf = pygame.Surface((1920, 1080))
    _hf_scr._render_background(_hf_surf)
    _hf_got = pygame.image.tobytes(_hf_surf, "RGB")
    if os.path.exists(os.path.join(os.path.dirname(SCREENS_DIR),
                                   _hf_bgs.DIR, _hf_name + ".png")):
        assert _hf_got != _hf_uni_px, f"{_hf_name} lost its own picture"
        _hf_own.append(_hf_name)
    else:
        assert _hf_got == _hf_uni_px, (
            f"{_hf_name} does not stand on the universal background")
        _hf_n += 1
assert _hf_n >= 9, f"only {_hf_n} screens on the universal background"
assert _hf_own == ["main_menu"], _hf_own
ok(f"hud: no screen loads a frame image; {_hf_n} screens stand on the "
   f"universal background, {len(_hf_own)} on its own picture")
