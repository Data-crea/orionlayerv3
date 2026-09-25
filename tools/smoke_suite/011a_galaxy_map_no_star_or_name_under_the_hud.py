# smoke-suite area: galaxy_map
#
# Part of the OrionLayer smoke suite — 011a_galaxy_map_no_star_or_name_under_the_hud.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/, in file-name order and in ONE
# namespace. Do not import this file; it is not a module.
#
# Work order 170. Data's 2576x1432 screenshot had star names under the
# GAME plate and a band under the bar; this is what fails the day either
# comes back.
#
# The 2 check(s) it holds:
#   - galaxy map: no star, name, fleet or wormhole pixel under a HUD block, at five window sizes
#   - galaxy map: the title plate is centred on the map box (work order 171)


import struct as _ov_struct

import numpy as _ov_np

import hud_evidence as _ov_he
from core.game_state import GameState as _OvGS, PLAYER_SIZE as _OV_PS
from core.game_state import STAR_SIZE as _OV_SS
from core.structs import star as _ov_star
from screens.galaxy_map import hudview as _ov_hv

#: Window sizes: the three shipped 16:9 ones, Data's own window (wider
#: than 16:9, letterboxed left and right) and a 16:10 one (taller,
#: letterboxed above and below — where a bar anchored to the content
#: area would float).
_OV_SIZES = ((1920, 1080), (2560, 1440), (3840, 2160), (2576, 1432),
             (1920, 1200))


def _ov_raw(name, x, y, cls=2, size=1, owner=-1):
    r = bytearray(_OV_SS)
    r[0:len(name)] = name.encode()
    _ov_struct.pack_into("<hh", r, 15, x, y)
    r[19] = size
    _ov_struct.pack_into("<b", r, 20, owner)
    r[22] = cls
    _ov_struct.pack_into("<h", r, 160, -1)
    r[171] = 1
    return bytes(r)


def _ov_state(raws, scale, max_x, max_y):
    gs = _OvGS()
    gs.current_screen = 0
    gs.player_num = 0
    gs.map_scale, gs.map_max_x, gs.map_max_y = scale, max_x, max_y
    gs.stars = _ov_star.parse_all(raws)
    gs.player_raw = [bytes(_OV_PS)] * 8
    gs.stardate = 35000
    return gs


# THE WORST CASE, COMMITTED: a medium galaxy (759 x 600 at scale 15, the
# game's view at its origin, so the native viewport covers it exactly)
# with a star on every corner and every edge, each with a long name —
# the names hang BELOW their stars, so the bottom row is the one a bar
# would cover, and the top row the one the plate would.
_OV_EDGE = [_ov_raw(f"Edgestar {_i} Longname", _x, _y, owner=0 if _i % 3
                    else -1)
            for _i, (_x, _y) in enumerate(
                (_x, _y) for _x in (2, 190, 380, 570, 757)
                for _y in (2, 150, 300, 450, 598))]
_ov_cases = [("edge galaxy", _ov_state(_OV_EDGE, 15, 759, 600))]

# THE REAL SAVE, WHEN IT IS ON THIS DISK: the reference fixture's 99
# stars (a maximum galaxy, 1800 x 1350, display scale 36), read at the
# offset they were found at on 25 September 2026 and gated on the file's
# sha256 like every fixture offset (tools/fixtures.py). A clone has no
# saves (decisions 40, 42), so there the edge galaxy carries the check
# alone — and it is the harder of the two.
_ov_fx = os.path.join(FIXTURE_DIR if "FIXTURE_DIR" in dir() else
                      os.path.expanduser("~/orionlayer-fixtures"),
                      "fixture_reference_3502.4.GAM")
_ov_real = 0
if os.path.exists(_ov_fx):
    _ov_bytes = open(_ov_fx, "rb").read()
    if hashlib.sha256(_ov_bytes).hexdigest().startswith("ab70cc9ad5442335"):
        _ov_raws = [_ov_bytes[24984 + _i * _OV_SS:24984 + (_i + 1) * _OV_SS]
                    for _i in range(99)]
        _ov_cases.append(("reference save",
                          _ov_state(_ov_raws, 36, 1800, 1350)))
        _ov_real = 99


def _ov_mask(surf, other):
    a = pygame.surfarray.array3d(surf).astype(int)
    b = pygame.surfarray.array3d(other).astype(int)
    return (_ov_np.abs(a - b).max(axis=2) > 12).T


_ov_seen = 0
_ov_plates = 0
for _W, _H in _OV_SIZES:
    _ov_app = _ov_he.make_app(_W, _H)
    _ov_app.dispatcher.switch_to("galaxy_map")
    _ov_gm = _ov_app.dispatcher.active
    # The HUD alone, on transparent: every pixel a block draws.
    _ov_hud = pygame.Surface((_W, _H), pygame.SRCALPHA)
    _ov_hud.fill((0, 0, 0, 0))
    _ov_hv.render_sidebar(_ov_gm, _ov_hud)
    _ov_hv.render_nav(_ov_gm, _ov_hud)
    _ov_hv.render_title(_ov_gm, _ov_hud)
    _ov_hudm = (pygame.surfarray.array_alpha(_ov_hud) > 8).T
    # The map box itself clears every HUD block's rect.
    _ov_box = _ov_gm.box_screen_rect("map_area")
    for _ov_blk in ([_ov_gm.title_rect(), _ov_gm.box_screen_rect("sidebar")]
                    + [_ov_gm.nav_rect(_s["key"])
                       for _s in _ov_gm._data["buttons"]]):
        assert not _ov_box.colliderect(_ov_blk), (
            f"{_W}x{_H}: the map box {_ov_box} overlaps the HUD block "
            f"{_ov_blk}")
    # THE PLATE IS CENTRED ON THE MAP (work order 171), not on the window:
    # its text box's centre is the map box's horizontal centre.
    # The PLATE's centre, not its text box's: the artwork's hexagon sits
    # ~3 ref px left of the plate's middle, and the word follows the
    # hexagon (16 September 2026).
    from core.hud import blocks as _ov_blk
    _ov_pc = _ov_blk.title_plate_rect(_ov_hv.plate_centre_x(_ov_gm), 0,
                                      _ov_app.layout.scale)[0].centerx
    _ov_plates += 1
    assert abs(_ov_pc - _ov_box.centerx) <= 1, (
        f"{_W}x{_H}: the title plate is centred at x {_ov_pc}, the map "
        f"box at {_ov_box.centerx}")
    # THE BAR IS ON THE BOTTOM EDGE: TURN's lowest pixel is the HUD's
    # own screen-edge margin above the window's bottom, at every size.
    from core.hud import style as _ov_hs
    _ov_turn = _ov_gm.nav_rect("turn")
    _ov_m = _ov_hs.get().get("galaxy.edge_margin") * _ov_app.layout.scale
    assert abs((_H - _ov_turn.bottom) - _ov_m) <= 2, (
        f"{_W}x{_H}: TURN ends {_H - _ov_turn.bottom} px above the "
        f"bottom, the margin is {_ov_m:.1f}")
    for _ov_name, _ov_gs in _ov_cases:
        _ov_gm.update(_ov_gs)
        _ov_with = pygame.Surface((_W, _H))
        _ov_gm._render_map(_ov_with)
        _ov_empty = _ov_state([], _ov_gs.map_scale, _ov_gs.map_max_x,
                              _ov_gs.map_max_y)
        _ov_gm.update(_ov_empty)
        _ov_none = pygame.Surface((_W, _H))
        _ov_gm._render_map(_ov_none)
        _ov_content = _ov_mask(_ov_with, _ov_none)
        assert _ov_content.sum() > 500, (_W, _ov_name, "drew no stars")
        _ov_under = _ov_content & _ov_hudm
        assert not _ov_under.any(), (
            f"{_W}x{_H}, {_ov_name}: {int(_ov_under.sum())} pixels of "
            f"stars, names, fleets or wormholes lie under a HUD block")
        _ov_seen += 1
# THE MARKING of the window anchors this rests on.
assert "HD EXTENSION, work order 170" in open(
    os.path.join(os.path.dirname(SCREENS_DIR), "core", "layout.py"),
    encoding="utf-8").read()
report(f"galaxy map overlap: the reference save's {_ov_real} stars "
       + ("measured too" if _ov_real else
          "are not on this disk — the edge galaxy carried the check"))
ok(f"galaxy map: no star, name, fleet or wormhole pixel under a HUD "
   f"block, and the bar on the bottom edge ({len(_OV_SIZES)} window "
   f"sizes, {_ov_seen} renders)")
ok(f"galaxy map: the title plate is centred on the map box, not the "
   f"window ({_ov_plates} window sizes, within 1 px)")
