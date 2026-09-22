# smoke-suite area: colony_summary
#
# Part of the OrionLayer smoke suite — 026_colony_summary_colony_summary_list_scrolls_clamps_tra.py.
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
#   - colony summary list scrolls (clamps transcribed, overflow counts above and below, wheel marked, 


# ── The list SCROLLS, for viewing only (fundament 46) ──
# Fifteen colonies against a panel that holds ten, so the offset
# has somewhere to go. The synthetic empire ships five, which is
# why this builds its own rather than reusing _sel_snap.
from screens.colony_summary import colonyselect as _cs_sel
_sc_cols = [dict(_c, star=f"{_c['star']}{_i}")
            for _i, _c in enumerate(_pv.COLONIES * 3)]
_sc_snap = _pv._Snapshot(_sc_cols)
_scr_op._sort_key = "name"
_scr_op.update(_sc_snap)
_sc_n = len(_scr_op._rows)
_sc_view = _scr_op._list_view()
_sc_vis = _scr_op._window.visible(*_sc_view)
assert _sc_vis == _cl.rows_drawn(_la, _lcfg, app.layout.scale, _sc_n), (
    "the screen and colonylist disagree about how many rows fit")
assert 0 < _sc_vis < _sc_n, (
    f"{_sc_n} rows into a panel that holds {_sc_vis} — this block "
    f"cannot test scrolling if everything fits")

# THE CLAMPS ARE THE ORIGINAL'S, all three of them, and they are
# asserted on the Window rather than through the screen so a
# failure names the rule rather than a pixel.
_w = _cs_sel.Window()
# Lower bound 0: Decrement_First_ floors it (colsum.cpp:211-214).
_w.scroll(-99, _sc_n, _sc_vis)
assert _w.first == 0, _w.first
# Upper bound: Increment_First_ is reached only while
# _g_colony_list_ptr[_first + 10] != -1 (colsum.cpp:796), so the
# original's LAST PAGE IS FULL and first stops at n - visible.
_w.scroll(99, _sc_n, _sc_vis)
assert _w.first == _sc_n - _sc_vis, (
    f"first ran to {_w.first}; the original stops at "
    f"{_sc_n - _sc_vis} because it refuses the step that would "
    f"leave the window's last slot empty (colsum.cpp:796)")
# Fewer rows than fit: neither stepper runs at all
# (colsum.cpp:210 and :226) and Update_First_ forces 0 every draw
# (colsum.cpp:194-197).
_w2 = _cs_sel.Window()
_w2.scroll(5, _sc_vis - 1, _sc_vis)
assert _w2.first == 0, (
    f"a list shorter than the window scrolled to {_w2.first}; the "
    f"original's steppers refuse it outright")
_w2.first = 7
assert _w2.clamp(_sc_vis - 1, _sc_vis) == 0, (
    "a window left pointing past a shrunken list did not "
    "re-establish itself; Update_First_ does that every frame")

# THE ARROWS SAY IT IN BOTH DIRECTIONS. The line this replaced
# counted `n - visible` at every offset, because at the bottom
# nothing is below and a count of the tail alone would say
# nothing is missing. The arrows carry the same both-ways
# property directly: at the top only DOWN is live, at the bottom
# only UP, and in the middle both.
from screens.colony_summary import colonyscroll as _cscr2
_sc_hidden = _sc_n - _sc_vis
_sc_surf = pygame.Surface((_la.right + 8, _la.bottom + 8))
_sc_up_r, _sc_dn_r = _cscr2.arrows(_la, _lcfg, app.layout.scale)
assert _sc_up_r is not None

def _sc_ink_at(_first):
    _sc_surf.fill((0, 0, 0))
    _cl.render(_sc_surf, _scr_op._rows, _la, _lcfg, app.layout,
               app.style, _first)
    return tuple(int(pygame.surfarray.array3d(
        _sc_surf.subsurface(_r)).sum())
        for _r in (_sc_up_r, _sc_dn_r))

_sc_top_up, _sc_top_dn = _sc_ink_at(0)
_sc_mid_up, _sc_mid_dn = _sc_ink_at(_sc_hidden // 2)
_sc_bot_up, _sc_bot_dn = _sc_ink_at(_sc_hidden)
assert _sc_top_dn > _sc_top_up, (
    f"at the top of {_sc_n} rows with {_sc_vis} visible, the down "
    f"arrow is not the live one ({_sc_top_dn} against {_sc_top_up})")
assert _sc_bot_up > _sc_bot_dn, (
    f"at the bottom the up arrow is not the live one "
    f"({_sc_bot_up} against {_sc_bot_dn})")
assert _sc_mid_up == _sc_top_dn and _sc_mid_dn == _sc_top_dn, (
    f"in the middle both arrows should be live and equally lit; "
    f"got up {_sc_mid_up}, down {_sc_mid_dn}, live {_sc_top_dn}")

# And the window really is a different slice: the top row drawn
# at the bottom offset is not the top row drawn at 0.
assert _scr_op._rows[0] is not _scr_op._rows[_sc_hidden], "no slice"

# THE MARKINGS. The wheel is an HD EXTENSION — MOO2 has no wheel
# on this screen — and the original's slider is NOT DRAWN. Both
# are recorded in three places and a marking with no check is an
# intention, which is the failure the help panel's marking taught.
assert "HD EXTENSION" in (_scr_op.handle_mousewheel.__doc__ or ""), (
    "screen.handle_mousewheel no longer marks the wheel as an HD "
    "EXTENSION; MOO2 scrolls this list with two step buttons and "
    "a slider (colsum.cpp:790-800), never a wheel")
assert "HD EXTENSION" in _lcfg.get("_hd_extension_wheel", ""), (
    "layout.json list._hd_extension_wheel no longer marks the "
    "wheel")
# ── THE SLIDER IS DRAWN, AND ITS ARITHMETIC IS THE ORIGINAL'S ─
#
# This block used to assert the OMISSION — that `colonylist` still
# said "NOT DRAWN" about `Draw_Bar_Indicator_`. The slider is
# transcribed since 9 September 2026, so the marker went and this
# asserts the drawing instead, which is the stronger claim.
for _cite in ("Draw_Bar_Indicator_", "colsum.cpp:747-771"):
    assert _cite in (_cl.__doc__ or "") or _cite in (
            _cscr2.slider.__doc__ or "") or _cite in (
            _cscr2.track.__doc__ or ""), (
        f"neither colonylist nor colonyscroll cites {_cite!r}")
# WHAT IS STILL OMITTED stays recorded: the per-row BUY button.
assert "_buy_note" in _lcfg or "buy" in (_cl.__doc__ or "").lower(), (
    "the omitted per-row buy button is no longer recorded")
# THE ARITHMETIC, at several windows. `y1 = h*first/n + top` and
# `y2 = h*(first+WINDOW)/n + top` (colsum.cpp:752-753), with the
# ORIGINAL's window of ten and not HD's row count.
_sl_area = _ov_area
_sl_cfg = _ov_cfg
_tr = _cscr2.track(_sl_area, _sl_cfg, app.layout.scale)
assert _tr is not None and _tr.height > 0, "no slider track"
_up_a, _dn_a = _cscr2.arrows(_sl_area, _sl_cfg, app.layout.scale)
assert _tr.top == _up_a.bottom and _tr.bottom == _dn_a.top, (
    f"the track {tuple(_tr)} does not span the gap between the "
    f"arrows {tuple(_up_a)}..{tuple(_dn_a)}")
for _n in (10, 11, 17, 40):
    for _f in (0, 1, _n - 10):
        _th = _cscr2.slider(_sl_area, _sl_cfg, app.layout.scale, _f, _n)
        assert _th is not None, f"no thumb at first={_f} of {_n}"
        _wy1 = _tr.y + _tr.height * _f // _n
        _wy2 = _tr.y + _tr.height * min(_n, _f + _cf.WINDOW) // _n
        assert _th.top == _wy1 and _th.height == max(1, _wy2 - _wy1), (
            f"first={_f} of {_n}: thumb {tuple(_th)} against the "
            f"original's {_wy1}..{_wy2}")
        assert _tr.contains(_th) or _th.height >= _tr.height, (
            f"the thumb leaves its track at first={_f} of {_n}")
    # AND ITS LENGTH IS THE VISIBLE-TO-TOTAL RATIO, which is the
    # whole reason the original draws a bar and not a marker.
    _t0 = _cscr2.slider(_sl_area, _sl_cfg, app.layout.scale, 0, _n)
    assert abs(_t0.height / _tr.height
               - _cf.WINDOW / _n) < 2.0 / _tr.height, (
        f"at {_n} colonies the thumb covers "
        f"{_t0.height / _tr.height:.3f} of the track and the "
        f"window is {_cf.WINDOW / _n:.3f} of the list")
# NOTHING AT ALL BELOW THE WINDOW, which is the original's own
# `if (num_colonies >= 10)` (colsum.cpp:751) — not even the
# track's corner dots.
for _n in (0, 1, 9):
    assert _cscr2.slider(_sl_area, _sl_cfg, app.layout.scale,
                        0, _n) is None, (
        f"a thumb was drawn for {_n} colonies; the original draws "
        f"nothing below {_cf.WINDOW}")
# THE DRAWING AND THE READING AGREE ABOUT THE COLOUR. `colonyfirst`
# recovers `_first` by looking for palette index 229 in the
# framebuffer; if this screen drew a different blue the two would
# disagree about what the same control looks like.
assert _cf.THUMB_FILL == 229 and _cf.THUMB_X0 == 621, (
    "colonyfirst's transcribed indices moved")
_sl_colors = _sjson.load(open(os.path.join(
    os.path.dirname(SCREENS_DIR), "assets", "shared", "skins",
    "default", "colors.json"), encoding="utf-8"))["colony_summary"]
assert tuple(_sl_colors["slider_fill"]) == tuple(_cscr2.SLIDER_FILL[:3]), (
    "colors.json and colonyscroll disagree about the thumb's fill")
assert "747-771" in _sl_colors.get("_slider_note", ""), (
    "colors.json no longer says where the slider's colours come "
    "from")
ok("colony summary list scrolls (clamps transcribed, overflow "
   "counts above and below, wheel marked, slider TRANSCRIBED: "
   "position from first, length from the visible/total ratio, "
   "nothing below ten colonies)")
