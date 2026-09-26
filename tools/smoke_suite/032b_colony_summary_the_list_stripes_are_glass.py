# smoke-suite area: colony_summary
#
# Part of the OrionLayer smoke suite — 032b_colony_summary_the_list_stripes_are_glass.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/, in file-name order and in ONE
# namespace. Do not import this file; it is not a module.
#
# Split out of 032 by work order 174 (the suite's 40 KB rule), which made
# the colony list's stripes glass: it reads names 032 binds (_plv, _lp_cl,
# _lp_ct, _np), and runs after it by its file name.
#
# The 1 check(s) it holds:
#   - the list stripes A/B by list index (holds under a one-row scroll) and fills the scanned colony's


# ── …AND THE STRIPE IS THE LIST'S, THE FILL IS THE SCANNED ROW'S ──
# Rendered, twice: from the top and scrolled by one. Every band's
# background (the MODE over the band, which the fill dominates) is
# row_selected where the band's colony is the scanned one and
# otherwise A or B by LIST index — so scrolling by one swaps the
# colours on screen and keeps each colony's own.
from screens.colony_summary import colonyfigures as _lp_fig
from screens.colony_summary import colonyscroll as _lp_scroll
_lp_app, _lp_scr = _plv.build_screen(1920, 1080)
_lp_app.dispatcher.switch_to("colony_summary")
_lp_scr.enter(None)
_lp_scr.update(_plv._Snapshot(_plv.COLONIES))
_lp_area, _lp_cfg, _lp_scale, _lp_n = _lp_scr._list_view()
_lp_rows = _lp_scr._rows
assert len(_lp_rows) >= 3, "the synthetic empire has too few rows"
_lp_scanned = _lp_rows[2]["index"]
_lp_cols = [(_x, _w) for _k, (_x, _w)
            in _lp_ct.columns(_lp_area, _lp_cfg).items()
            if _k != _lp_scroll.COLUMN]
_lp_x0 = min(_x for _x, _w in _lp_cols)
_lp_x1 = max(_x + _w for _x, _w in _lp_cols)
for _lp_first in (0, 1):
    _lp_s = pygame.Surface((1920, 1080))
    _lp_s.fill((255, 0, 255))
    _lp_cl.render(_lp_s, _lp_rows, _lp_area, _lp_cfg, _lp_scr.layout,
                  _lp_scr.style, _lp_first, _lp_scr._frame_inset(),
                  _lp_fig.set_for(_lp_scr, _lp_area, _lp_cfg),
                  _lp_scanned, None)
    _lp_px = _np.array(pygame.surfarray.array3d(_lp_s)).transpose(1, 0, 2)
    for _lp_b, (_lp_by, _lp_bh) in enumerate(
            _lp_ct.all_bands(_lp_area, _lp_cfg)):
        _lp_li = _lp_first + _lp_b
        _lp_sel = (_lp_li < len(_lp_rows)
                   and _lp_rows[_lp_li]["index"] == _lp_scanned)
        _lp_exp = (_lp_cl.ROW_SELECTED if _lp_sel else
                   (_lp_cl.ROW_A if _lp_li % 2 == 0 else _lp_cl.ROW_B))
        # SINCE WORK ORDER 174 a band is GLASS with its colour laid over
        # (`core.hud.glass.draw`), so there is no single colour to take
        # the mode of. The same rule by the successor method: the band
        # on screen is, pixel for pixel in its majority, the glass its
        # expected colour draws at that rect.
        _lp_rect = pygame.Rect(_lp_x0, _lp_by, _lp_x1 - _lp_x0, _lp_bh)
        _lp_ref = pygame.Surface((1920, 1080))
        from core.hud import glass as _lp_gl
        from core.hud import style as _lp_hs
        _lp_gl.draw(_lp_ref, _lp_rect, dense=True, shade=tuple(_lp_exp[:3]),
                    shade_alpha=float(_lp_hs.get().get(
                        "glass.selected_shade" if _lp_sel else "glass.row_shade")))
        _lp_band = _lp_px[_lp_by + 2:_lp_by + _lp_bh - 2,
                          _lp_x0 + 2:_lp_x1 - 2].reshape(-1, 3)
        _lp_want = _np.array(pygame.surfarray.array3d(_lp_ref)).transpose(
            1, 0, 2)[_lp_by + 2:_lp_by + _lp_bh - 2,
                     _lp_x0 + 2:_lp_x1 - 2].reshape(-1, 3)
        _lp_same = float((_lp_band == _lp_want).all(axis=1).mean())
        assert _lp_same > 0.5, (
            f"first={_lp_first} band {_lp_b} (list index {_lp_li}"
            f"{', scanned' if _lp_sel else ''}): only {_lp_same:.0%} of it "
            f"is the glass under {tuple(_lp_exp[:3])}")
# AND THE THREE STAY TOLD APART on the glass: A, B and the selected
# colour, each over the same background, differ by their mean.
_lp_means = []
for _lp_c in (_lp_cl.ROW_A, _lp_cl.ROW_B, _lp_cl.ROW_SELECTED):
    _lp_ref = pygame.Surface((1920, 1080))
    _lp_gl.draw(_lp_ref, pygame.Rect(_lp_x0, 400, _lp_x1 - _lp_x0, 40),
                dense=True, shade=tuple(_lp_c[:3]),
                shade_alpha=float(_lp_hs.get().get(
                    "glass.selected_shade" if _lp_c is _lp_cl.ROW_SELECTED
                    else "glass.row_shade")))
    _lp_means.append(_np.array(pygame.surfarray.array3d(_lp_ref.subsurface(
        (_lp_x0, 400, _lp_x1 - _lp_x0, 40)))).reshape(-1, 3).mean(axis=0))
assert _np.abs(_lp_means[0] - _lp_means[1]).max() >= 1.0 and \
    _np.abs(_lp_means[2] - _lp_means[0]).max() >= 10.0, _lp_means
ok("the list stripes A/B by list index (holds under a one-row "
   "scroll) and fills the scanned colony's band row_selected — each "
   "band the glass its colour draws (work order 174), the three told "
   "apart")
