# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 006c_core_hud_never_touches_pictures.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/, in file-name order and in ONE
# namespace. Do not import this file; it is not a module.
#
# Work order 172: Data saw New Game's five pictures black under a grey
# frame colour. The cause was not the tint — 169 had covered them — but
# the order's rule holds either way: the frame colour touches the HUD's
# components and nothing else, and a picture is always its source.
#
# The 2 check(s) it holds:
#   - hud never touches pictures: New Game's five equal their source at six tints; elsewhere a tint changes only HUD components
#   - checkboxes draw both states at every tint (New Game, the GAME menu's settings)


import numpy as _np_pic

import hud_evidence as _pic_he
from core.hud import blocks as _pic_blk
from core.hud import style as _pic_hs
from core.hud import tint as _pic_tint

#: The six tints the order names: the measured blue, silver, grey, dark
#: grey, black and one saturated colour.
_PIC_TINTS = [(None, None, None)] + [
    _pic_tint.NAMED[_pic_nn] for _pic_nn in ("silver", "grey", "dark_grey", "black")
] + [(280, None, None)]


def _pic_px(surf, rect=None):
    s = surf.subsurface(rect) if rect is not None else surf
    return _np_pic.array(pygame.surfarray.array3d(s)).transpose(1, 0, 2)


class _PicGS:
    pass


def _pic_ng_state(on):
    gs = _PicGS()
    for _pic_aa, _pic_vv in dict(ng_difficulty=1, ng_galaxy_size=1, ng_galaxy_age=1,
                       ng_opponents=3, ng_tech_level=1,
                       ng_tactical_combat=int(on), ng_random_events=int(on),
                       ng_antarans=int(on), current_screen=13).items():
        setattr(gs, _pic_aa, _pic_vv)
    return gs


if slow("tint_pictures"):
    # 1a — NEW GAME'S FIVE PICTURES ARE THEIR SOURCE, at every tint, at the
    #      two box lists (1920x1080 has none, 2560x1440 has the inner_panel
    #      boxes that covered the pictures from 169 to 172).
    _pic_n = 0
    try:
        for _PIC_W, _PIC_H in ((1920, 1080), (2560, 1440)):
            _pic_app = _pic_he.make_app(_PIC_W, _PIC_H)
            _pic_app.dispatcher.switch_to("new_game")
            _pic_ng = _pic_app.dispatcher.active
            _pic_ng.update(_pic_ng_state(True))
            for _pic_t in _PIC_TINTS:
                _pic_hs.set_tone(*_pic_t)
                _pic_s = pygame.Surface((_PIC_W, _PIC_H))
                _pic_ng.render(_pic_s)
                for _pic_cat, _pic_slot in _pic_ng._cfg["setting_slots"].items():
                    _pic_panel = pygame.Rect(*_pic_ng._hd_to_screen(
                        *_pic_slot["rect"]))
                    _pic_src = _pic_ng.setting_picture(_pic_cat, _pic_panel)
                    assert _pic_src is not None, (_pic_cat, "no picture")
                    _pic_in = _pic_blk.panel_inner(_pic_panel, _pic_app.layout.scale)
                    assert (_pic_px(_pic_s, _pic_in) == _pic_px(_pic_src)).all(), (
                        f"{_PIC_W}x{_PIC_H}, tint {_pic_t}: New Game's {_pic_cat} "
                        f"picture is not its source")
                    _pic_n += 1
    finally:
        _pic_hs.set_tone(None, None, None)

    # 1b — EVERYWHERE ELSE, A TINT CHANGES ONLY HUD COMPONENTS. Every block of
    #      core/hud records the rect it draws (plus its glow's pad), and the
    #      two table helpers and the settings row's bars record theirs; a
    #      pixel that differs between the measured blue and a tint must lie
    #      inside one of them. A picture, a sprite, a portrait, a star or a
    #      word that is not an accent label that changed colour lands outside
    #      and fails.
    _pic_regions = []
    _pic_real = {}
    _PIC_BLOCKS = ("panel", "popup", "outline", "small_button", "slant_button",
                   "action_button", "checkbox", "table_header", "table_row",
                   "scrollbar")


    def _pic_spy(_name):
        _fn = getattr(_pic_blk, _name)

        def _wrap(_surface, _rect, _scale, *_pic_aa, **_k):
            # The widest glow of any block (the action button's, 1.6x the
            # panel's), so twice the panel's pad covers every block.
            _pad = 2 * _pic_blk.glow_pad(_scale) + 2
            _pic_regions.append(pygame.Rect(_rect).inflate(2 * _pad, 2 * _pad))
            return _fn(_surface, _rect, _scale, *_pic_aa, **_k)
        return _fn, _wrap


    def _pic_sep(_surface, _x0, _x1, _y, _scale, vertical=False):
        if vertical:
            _pic_regions.append(pygame.Rect(int(_y) - 4, int(_x0), 8,
                                            int(_x1 - _x0)))
        else:
            _pic_regions.append(pygame.Rect(int(_x0), int(_y) - 4,
                                            int(_x1 - _x0), 8))
        return _pic_real["separator"](_surface, _x0, _x1, _y, _scale, vertical)


    def _pic_plate(_surface, _cx, _top, _scale, *_pic_aa, **_k):
        _pic_regions.append(_pic_blk.title_plate_rect(_cx, _top, _scale)[0]
                            .inflate(8, 8))
        return _pic_real["title_plate"](_surface, _cx, _top, _scale, *_pic_aa, **_k)


    from core import listgrid as _pic_lg
    from screens.game_menu import gmorion as _pic_gmo
    _pic_real_fills = _pic_lg.draw_row_fills


    def _pic_fills(_surface, _bands, _cols, _skip, *_pic_aa, **_k):
        _sp = _pic_lg.plated_span(_cols, _skip)
        if _sp is not None:
            for _by, _bh in _bands:
                _pic_regions.append(pygame.Rect(_sp[0], _by, _sp[1], _bh))
        return _pic_real_fills(_surface, _bands, _cols, _skip, *_pic_aa, **_k)


    _pic_real_rows = _pic_gmo._render_frame_row


    def _pic_rows(_screen, _surface, _geo, *_pic_aa, **_k):
        for _pic_kk in ("frame", "tone"):
            _pic_regions.append(_geo[_pic_kk].inflate(0, 12))
        return _pic_real_rows(_screen, _surface, _geo, *_pic_aa, **_k)


    _pic_names = sorted(_pic_nn for _pic_nn in os.listdir(SCREENS_DIR)
                        if os.path.isfile(os.path.join(SCREENS_DIR, _pic_nn,
                                                       "screen.py"))
                        and not _pic_nn.startswith("_")) + ["game_menu_settings"]
    _pic_screens = 0
    for _pic_nn in _PIC_BLOCKS:
        _pic_real[_pic_nn], _pic_ww = _pic_spy(_pic_nn)
        setattr(_pic_blk, _pic_nn, _pic_ww)
    _pic_real["separator"] = _pic_blk.separator
    _pic_real["title_plate"] = _pic_blk.title_plate
    _pic_blk.separator = _pic_sep
    _pic_blk.title_plate = _pic_plate
    _pic_lg.draw_row_fills = _pic_fills
    _pic_gmo._render_frame_row = _pic_rows
    try:
        for _pic_name in _pic_names:
            _pic_app = _pic_he.make_app(1920, 1080)
            _pic_he.stage(_pic_app, _pic_name)
            _pic_d = _pic_app.dispatcher
            if _pic_name == "new_game":
                _pic_d.active.update(_pic_ng_state(True))

            def _pic_draw():
                _pic_sf = pygame.Surface((1920, 1080))
                _pic_d.active.render(_pic_sf)
                if _pic_d.overlay_name:
                    _pic_d.screens[_pic_d.overlay_name].render(_pic_sf)
                return _pic_px(_pic_sf)
            _pic_hs.set_tone(None, None, None)
            _pic_regions.clear()
            _pic_base = _pic_draw()
            for _pic_t in _PIC_TINTS[1:]:
                _pic_hs.set_tone(*_pic_t)
                _pic_regions.clear()
                _pic_now = _pic_draw()
                _pic_ok = _np_pic.zeros(_pic_base.shape[:2], bool)
                for _pic_rr in _pic_regions:
                    _pic_rr = _pic_rr.clip(pygame.Rect(0, 0, 1920, 1080))
                    _pic_ok[_pic_rr.top:_pic_rr.bottom, _pic_rr.left:_pic_rr.right] = True
                _pic_diff = (_pic_now != _pic_base).any(axis=2)
                _pic_out = _pic_diff & ~_pic_ok
                assert not _pic_out.any(), (
                    f"{_pic_name}, tint {_pic_t}: {int(_pic_out.sum())} pixels "
                    f"outside every HUD component changed colour — first at "
                    f"{tuple(int(_pic_vv) for _pic_vv in _np_pic.argwhere(_pic_out)[0][::-1])}")
            _pic_screens += 1
    finally:
        for _pic_nn in _PIC_BLOCKS + ("separator", "title_plate"):
            setattr(_pic_blk, _pic_nn, _pic_real[_pic_nn])
        _pic_lg.draw_row_fills = _pic_real_fills
        _pic_gmo._render_frame_row = _pic_real_rows
        _pic_hs.set_tone(None, None, None)
    ok(f"hud never touches pictures: New Game's five equal their source at "
       f"{len(_PIC_TINTS)} tints and two box lists ({_pic_n} comparisons); on "
       f"{_pic_screens} screens and dialogs a tint changes only HUD components")

# 2 — CHECKBOXES DRAW BOTH STATES, at every tint: New Game's three
#     toggles and the GAME menu's settings squares, rendered checked and
#     unchecked; every box must differ by at least a tenth of its pixels.
_pic_boxes = 0
try:
    _pic_app = _pic_he.make_app(1920, 1080)
    _pic_app.dispatcher.switch_to("new_game")
    _pic_ng = _pic_app.dispatcher.active
    _pic_rects = [pygame.Rect(*_pic_ng._hd_to_screen(
        *_pic_ng._toggle_icon_rect(_i)))
        for _i in range(len(_pic_ng._cfg["toggles"]["order"]))]
    for _pic_t in _PIC_TINTS:
        _pic_hs.set_tone(*_pic_t)
        _pic_shots = []
        for _pic_on in (True, False):
            _pic_ng.update(_pic_ng_state(_pic_on))
            _pic_sf = pygame.Surface((1920, 1080))
            _pic_ng.render(_pic_sf)
            _pic_shots.append(_pic_sf)
        for _pic_rr in _pic_rects:
            _pic_dd = (_pic_px(_pic_shots[0], _pic_rr) != _pic_px(_pic_shots[1], _pic_rr)
                  ).any(axis=2).sum()
            assert _pic_dd >= 0.1 * _pic_rr.w * _pic_rr.h, (
                f"tint {_pic_t}: a New Game checkbox at {tuple(_pic_rr)} looks "
                f"the same checked and unchecked ({_pic_dd} px differ)")
            _pic_boxes += 1
    # The GAME menu's settings squares: through the one block they use.
    from screens.game_menu import gmdraw as _pic_gmd
    assert "hud.checkbox(" in open(_pic_gmd.__file__, encoding="utf-8").read()
    for _pic_t in _PIC_TINTS:
        _pic_hs.set_tone(*_pic_t)
        _pic_r = pygame.Rect(10, 10, 30, 30)
        _pic_aa = pygame.Surface((60, 60))
        _pic_blk.checkbox(_pic_aa, _pic_r, 1.0, True)
        _pic_bb = pygame.Surface((60, 60))
        _pic_blk.checkbox(_pic_bb, _pic_r, 1.0, False)
        assert (_pic_px(_pic_aa, _pic_r) != _pic_px(_pic_bb, _pic_r)).any(axis=2).sum() \
            >= 0.1 * 900, _pic_t
        _pic_boxes += 1
finally:
    _pic_hs.set_tone(None, None, None)
ok(f"checkboxes draw both states at every tint ({_pic_boxes} boxes: New "
   f"Game's three toggles and the GAME menu's settings squares)")
