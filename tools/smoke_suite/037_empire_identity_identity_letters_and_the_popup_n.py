# smoke-suite area: empire_identity
#
# Part of the OrionLayer smoke suite — 037_empire_identity_identity_letters_and_the_popup_n.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (91 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 1 check(s) it holds:
#   - identity letters and the popup (N only on natives, overlay not reflow, flips in the last row, no

# ── The identity letter, and the popup's two rules ───────────
# N on a native cell and nothing on the player's own, because
# over ninety per cent of cells are the second case and have to
# stay quiet. The letters for android and conquered rest on the
# source alone — see the split marking check above.
_idm = _mv_cfg.get("cell_marks", {})
assert _idm.get("native") == "N", _idm
for _kind in ("android", "conquered"):
    assert _idm.get(_kind), f"no letter for {_kind}"
assert len(set(_idm.values())) == len(_idm), (
    f"two identity classes share a letter: {_idm}")
assert not (set(_idm.values())
            & set(_mv_cfg.get("marker_letters", []))), (
    f"an identity letter collides with a job marker: {_idm} "
    f"against {_mv_cfg.get('marker_letters')}. They sit in "
    f"different boxes, but a reader should not have to know that")
_idr = dict(_dt_rows[1])          # Urna I's shape
# `colonyrows.Cell(kind, figure)` — a cell carries its identity
# class AND the figure it draws, both from one `Colony_Pop_Anim_`
# read. The fake carries the same shape as the real row, which is
# what the AST pin on the row dict exists to keep true.
_Cell = _crw.Cell
_idr["cells"] = ((_Cell("", "human_farmer.png"),
                  _Cell("native", "native.png"),
                  _Cell("native", "native.png"),
                  _Cell("native", "native.png")), (), ())
_marks = [_cl._cell_mark(_mv_cfg, _idr["cells"], 0, _k)
          for _k in range(4)]
assert _marks == ["", "N", "N", "N"], _marks
assert _cl._cell_mark(_mv_cfg, _idr["cells"], 1, 0) == "", (
    "a job with no cells produced a mark")

# THE POPUP OVERLAYS AND NEVER REFLOWS, so the rows it is drawn
# over must be exactly where they were without it — the list is
# the click frame (decision 46).
_pop_words = _scr_op._data.get("popup", {})
_pop_px = app.layout.font_size(_pop_words.get("font", 15))
_pop_before = _cl.row_bands(_mv_area, _mv_cfg, _mv_scale,
                            len(_mv_rows))
_pop_ctl = _cmu.MoveController()
_pop_ctl.over = (0, 0)
_pop_surf = pygame.Surface((_mv_area.right + 8, _mv_area.bottom + 8))
_pop_rect = _pop_ctl.draw_popup(_pop_surf, _mv_rows, 0, _mv_area,
                                _mv_cfg, _mv_scale, app.style,
                                app.layout, _scr_op._data)
assert _pop_rect is not None, "the popup drew nothing at all"
assert _cl.row_bands(_mv_area, _mv_cfg, _mv_scale,
                     len(_mv_rows)) == _pop_before, (
    "the rows moved when the popup opened — it must overlay")
# IT STAYS INSIDE list_area, at every row, because the frame
# image is drawn after the content and would cover it otherwise.
for _i in range(len(_pop_before)):
    _pop_ctl.over = (_i, 0)
    _r = _cpop.rect_for(_mv_area, _mv_cfg, _mv_scale, _mv_rows[_i],
                        0, _pop_before[_i], app.style, _pop_px,
                        _pop_words)
    assert _r is not None
    assert _mv_area.contains(_r[0]), (
        f"row {_i}: the popup at {_r[0]} leaves {_mv_area} — "
        f"outside the cutout it is covered by the frame's metal")
# AND A ROW AT THE BOTTOM OF THE PANEL FLIPS IT ABOVE rather
# than off the panel. The fixture list is short, so the case is
# made rather than waited for: a band at the last row position
# `list_area` can hold, which is where a full list puts one.
_pop_h = _pop_before[0][1]
_bottom_band = (_mv_area.bottom - _pop_h, _pop_h)
_r_last = _cpop.rect_for(_mv_area, _mv_cfg, _mv_scale, _mv_rows[0],
                         0, _bottom_band, app.style, _pop_px,
                         _pop_words)[0]
assert _r_last.bottom <= _bottom_band[0], (
    f"a row at the panel's bottom put its popup at {_r_last}, "
    f"not above the row at y={_bottom_band[0]}")
assert _mv_area.contains(_r_last), (
    f"the flipped popup at {_r_last} still leaves {_mv_area}")
# NO POPUP WHILE A SELECTION IS HELD. One rule, and it lives in
# the controller so a reader cannot find a second answer.
_pop_ctl.over = (0, 0)
_pop_ctl.pick = object()
assert _pop_ctl.draw_popup(_pop_surf, _mv_rows, 0, _mv_area,
                           _mv_cfg, _mv_scale, app.style,
                           app.layout, _scr_op._data) is None, (
    "the popup opened while a pick was held — it would flicker "
    "under the aiming gesture and cover the drop targets")
_pop_ctl.pick = None
_pop_ctl.hover(_mv_rows, 0, _mv_area.x + 5, _mv_area, _mv_cfg,
               _mv_scale)
_pop_ctl.pick = object()
_pop_ctl.hover(_mv_rows, 0, _mv_area.x + 5, _mv_area, _mv_cfg,
               _mv_scale)
assert _pop_ctl.over is None, (
    "hovering while a pick is held set a popup target anyway")
ok("identity letters and the popup (N only on natives, overlay "
   "not reflow, flips in the last row, none while a pick is held)")
