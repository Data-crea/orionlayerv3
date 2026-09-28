# smoke-suite area: galaxy_map
#
# Part of the OrionLayer smoke suite — 090zb_galaxy_map_the_travel_line_on_hover.py.
# `tools/smoke_test.py` executes this file, and every other module in
# tools/smoke_suite/, in file-name order and in ONE namespace. Do not
# import this file; it is not a module.
#
# The 2 check(s) it holds:
#   - open fix 48's FMOV block parses whole or not at all, after DSBX, and the preview's colour is the original's rule with Data's two extensions
#   - the travel line on hover: drawn to the hovered star from the fleet box's head, green where FMOV says reachable, red where not, gone when the pointer leaves or FMOV is absent — at 1920 and 2576


# ── THE TRAVEL LINE ON HOVER (work order 188 Part 3, open fix 48) ──
#
# The original draws the preview on HOVER (`Draw_ETA_Destination_Line_`,
# mainscr.cpp:535-568) from the move verdict `Ships_Try_To_Move_To_` fills
# (shipmove.cpp:776-969). FMOV puts the engine's verdict for every star on
# the wire; HD colours the line from it and never recomputes range or fuel.
import struct as _tl_st
import inspect as _tl_inspect
from core import moveblocks as _tl_mb
from core import game_state as _tl_gsmod
from screens.galaxy_map import maplines as _tl_ml

# 1. THE BLOCK: whole or None, and read LAST (after DSGN / DSBX).
_tl_v = [{"moving": 1, "turns_left": 3}, {"out_of_range": 1, "parsecs": 5},
         {"immobile": 1}, {"moving": 1, "turns_left": 0},
         {"blackhole_blocks": 1}, {"hyperspace_flux": 1}]
_tl_blk = _tl_mb.build(_tl_v)
assert len(_tl_blk) == 8 + 14 * len(_tl_v)
_tl_g = _tl_ns = __import__("types").SimpleNamespace()
assert _tl_mb.parse(_tl_g, _tl_blk + b"xx", 0) == len(_tl_blk)
assert [v["turns_left"] for v in _tl_g.fleet_move["verdicts"]] == \
    [3, 0, 0, 0, 0, 0] and _tl_g.fleet_move["verdicts"][1]["parsecs"] == 5
for _tl_bad in (_tl_blk[:-1], b"FMOX" + _tl_blk[4:],
                _tl_blk[:4] + b"\x02" + _tl_blk[5:],        # a version 2
                _tl_blk[:7] + b"\x0f" + _tl_blk[8:]):       # a struct of 15
    _tl_g2 = __import__("types").SimpleNamespace()
    assert _tl_mb.parse(_tl_g2, _tl_bad, 0) == 0 and \
        _tl_g2.fleet_move is None, _tl_bad[:8]
assert _tl_mb.FORMAT == "<bbbbBbbbbBbbbb" and _tl_mb.SIZE == 14, \
    "s_ship_move_info, orion2.h:2921-2936"
_tl_src = _tl_inspect.getsource(_tl_gsmod.parse_snapshot) if hasattr(
    _tl_gsmod, "parse_snapshot") else io.open(_tl_gsmod.__file__,
                                              encoding="utf-8").read()
assert _tl_src.index("designblocks.parse(gs, data, pos)") < \
    _tl_src.index("moveblocks.parse(gs, data, pos)"), "FMOV is written LAST"
# The colour: mainscr.cpp:558-567, and Data's two extensions (red for an
# immobile fleet and a black hole target, where the original draws none).
assert [_tl_ml.preview_colour(v) for v in _tl_g.fleet_move["verdicts"]] == \
    ["green", "red", "red", None, "red", "red"]
assert _tl_ml.preview_colour(_tl_g.fleet_move["verdicts"][0],
                             black_hole=True) == "red"
assert _tl_ml.preview_colour(None) is None
assert "HD EXTENSION `hover_line`" in (_tl_ml.__doc__ or "") and \
    "Data's decision, 28 Sep" in (_tl_ml.__doc__ or "")
assert "HD EXTENSION `hover_line`" in io.open(os.path.join(
    os.path.dirname(SCREENS_DIR), "v3_projektstatus.md"),
    encoding="utf-8").read()
assert "the order preview line" not in (_tl_ml.__doc__ or ""), \
    "the OMISSION is gone: the preview is drawn"
ok("open fix 48's FMOV block parses whole or not at all, after DSBX, and the "
   "preview's colour is the original's rule with Data's two extensions")

# 2. THE RENDER. The map staged from the tree, a fleet box with its head
# icon at star 3, FMOV saying star 5 is reachable and star 20 is not.
import hud_evidence as _tl_he
from core.structs import ship_icon as _tl_icon
from core import mapcoords as _tl_mc
_tl_counts = {}
for _tl_size in ((1920, 1080), (2576, 1432)):
    _tl_app = _tl_he.make_app(*_tl_size)
    _tl_gs = _tl_he.stage(_tl_app, "galaxy_map")
    _tl_gm = _tl_app.dispatcher.active
    _tl_s3 = _tl_gs.stars[3]
    _tl_nx, _tl_ny = _tl_mc.galaxy_to_native(_tl_s3.x, _tl_s3.y, _tl_gs)
    _tl_gs.ship_icons = _tl_icon.parse_all([_tl_st.pack(
        "<6h", 0, 0, 3, 0, int(_tl_nx) + 6, int(_tl_ny) - 4)])
    _tl_gs.fleet_selection = {"stack": 0, "ships": [0], "selected": [True],
                              "chain": [0]}
    _tl_verd = [{"moving": 0, "out_of_range": 1, "parsecs": 9}
                for _ in _tl_gs.stars]
    _tl_verd[5] = {"moving": 1, "turns_left": 2}
    _tl_verd[3] = {"moving": 1, "turns_left": 0}          # where it stands
    _tl_mb.parse(_tl_gs, _tl_mb.build(_tl_verd), 0)
    _tl_gm.update(_tl_gs)
    _tl_seen = []
    _tl_real = _tl_ml.stroke
    _tl_ml.stroke = lambda surf, colour, a, b: (
        _tl_seen.append(tuple(colour[:3])), _tl_real(surf, colour, a, b))

    def _tl_draw(hover):
        _tl_seen.clear()
        _tl_gm._hover_star = None if hover is None else _tl_gm._stars[hover]
        # THE APP'S SEQUENCE: the pointer moved, THEN a snapshot arrived
        # (which builds `_stars` anew), then the frame — found live in work
        # order 188: an identity lookup of the hovered star drew nothing.
        # new star objects at the same places, as a parsed snapshot has
        _tl_gs.stars = _tl_he.galaxy_state().stars
        _tl_gm.update(_tl_gs)
        assert hover is None or not any(
            _s is _tl_gm._hover_star for _s in _tl_gm._stars), \
            "the snapshot did not rebuild the stars: the live case is missed"
        _tl_surf = pygame.Surface(_tl_size)
        _tl_gm._render_map(_tl_surf)
        return ({c for c in _tl_seen if c in _tl_ml.GREEN},
                {c for c in _tl_seen if c in _tl_ml.RED}, len(_tl_seen))
    try:
        _tl_green = _tl_draw(5)
        _tl_red = _tl_draw(20)
        _tl_none = _tl_draw(None)
        _tl_here = _tl_draw(3)
        _tl_saved = _tl_gs.fleet_move
        _tl_gs.fleet_move = None
        _tl_gm.update(_tl_gs)
        _tl_nofix = _tl_draw(5)
        _tl_gs.fleet_move = _tl_saved
        _tl_gs.fleet_selection = dict(_tl_gs.fleet_selection,
                                      selected=[False])
        _tl_gm.update(_tl_gs)
        _tl_nosel = _tl_draw(5)
    finally:
        _tl_ml.stroke = _tl_real
    assert _tl_green[0] and not _tl_green[1], ("reachable: green", _tl_green)
    assert _tl_red[1] and not _tl_red[0], ("unreachable: red", _tl_red)
    for _tl_n, _tl_r in (("no hover", _tl_none), ("at its own star",
                                                   _tl_here),
                         ("no FMOV", _tl_nofix), ("nothing selected",
                                                  _tl_nosel)):
        assert not _tl_r[0] and not _tl_r[1], (_tl_n, _tl_r)
    _tl_counts[_tl_size] = (_tl_green[2], _tl_red[2])
# the wave follows the window: more pieces at 2576 than at 1920
assert _tl_counts[(2576, 1432)][0] >= _tl_counts[(1920, 1080)][0], \
    _tl_counts
ok(f"the travel line on hover: drawn to the hovered star from the fleet "
   f"box's head, green where FMOV says reachable, red where not, gone when "
   f"the pointer leaves or FMOV is absent — at 1920 and 2576 "
   f"(pieces {_tl_counts})")
