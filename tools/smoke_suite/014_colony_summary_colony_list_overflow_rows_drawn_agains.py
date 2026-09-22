# smoke-suite area: colony_summary
#
# Part of the OrionLayer smoke suite — 014_colony_summary_colony_list_overflow_rows_drawn_agains.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (93 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 1 check(s) it holds:
#   - colony list overflow (rows drawn against rows present, the count is named, nothing drawn when no


# ── DRAWN AGAINST PRESENT: the list says what it dropped ──
# render() stops at the first row that would cross the bottom of
# list_area. At 1920x1080 the panel holds nine rows, so a
# twelve-colony empire lost three IN SILENCE — every drawn row
# correct, every check in this suite green, and the fault found
# by somebody noticing a colony they owned was missing from a
# screenshot. The check is therefore on the two numbers being
# reconciled, not on the drawing being pretty.
d.switch_to("colony_summary")
_ov_area = pygame.Rect(*app.layout.rect(
    d.active.box_rect("list_area")))
from screens.colony_summary import colonyheader as _ch
from screens.colony_summary import colonytrack as _ct0
_ov_cfg = _sjson.load(open(os.path.join(
    SCREENS_DIR, "colony_summary", "layout.json"),
    encoding="utf-8"))["list"]
# THE FIXTURE CARRIES THE COLUMN BOXES, because the screen's cfg
# does — `colonyheader.install_columns` binds them on load. A
# fixture without them gets NO row at all now (`row_boxes`), which
# is the honest answer to a caller that has no columns.
_ov_cfg = _column_cfg(_ov_cfg, app.layout)
_ov_fits = _cl.rows_drawn(_ov_area, _ov_cfg, app.layout.scale, 99)
assert _ov_fits > 0, "no row fits list_area at all"
# TEN, because that is the original's window: COLSUM::_list_col
# holds ten and Update_Col_List_ (colsum.cpp:348) fills exactly
# that many. At row_height 62 the panel held nine and nothing
# said so until a --live --native side-by-side put the two lists
# next to each other. Asserted at every shipped resolution, and
# with room left for the overflow line: at row_height 60 ten rows
# fit and the line does not, which is the interaction a change to
# either number alone gets wrong.
_ORIGINAL_WINDOW = 10
for _W, _H in _SIZES:
    _lay2 = Layout(_W, _H)
    _la2 = pygame.Rect(*_lay2.rect(d.active.box_rect("list_area")))
    _fits2 = _cl.rows_drawn(_la2, _ov_cfg, _lay2.scale, 99)
    assert _fits2 >= _ORIGINAL_WINDOW, (
        f"{_W}x{_H}: the list draws {_fits2} rows and the original "
        f"windows {_ORIGINAL_WINDOW} (_list_col[10], "
        f"colsum.cpp:348)")
    # EXACTLY TEN, and it is `list.row_count` that says so — not
    # a `row_height` that happens to divide. It was exactly that
    # until 8 September 2026: 58 and a 14 px pad yielded ten at
    # all three shipped resolutions by arithmetic coincidence,
    # and nothing in the tree said which of the three numbers was
    # load-bearing. A check that only asked ">= 10" could not see
    # eleven either.
    assert _fits2 == _ORIGINAL_WINDOW, (
        f"{_W}x{_H}: the list draws {_fits2} rows, not "
        f"{_ORIGINAL_WINDOW}. `list.row_count` is "
        f"{_ov_cfg['row_count']} and the band is the window "
        f"divided by it — a different count is a JSON change, "
        f"never a side effect")
    # AND THE BANDS TILE THE WINDOW EXACTLY, the last taking the
    # remainder. A strip below the last row belongs to nobody:
    # the hit test would answer None over rows that look drawn.
    _bands2 = _cl.row_bands(_la2, _ov_cfg, _lay2.scale, _fits2)
    assert _bands2[0][0] == _la2.y, (_W, _H, _bands2[0])
    assert _bands2[-1][0] + _bands2[-1][1] == _la2.bottom, (
        f"{_W}x{_H}: the bands end at "
        f"{_bands2[-1][0] + _bands2[-1][1]} and list_area at "
        f"{_la2.bottom} — the last band takes the remainder")
    for _b0, _b1 in zip(_bands2, _bands2[1:]):
        assert _b0[0] + _b0[1] == _b1[0], (_W, _H, _b0, _b1)
    # AND THE STEP IS DERIVED FROM THAT BAND, not declared. The
    # per-resolution table is gone: the figure's INK has to fit
    # the band with the origin where the original puts it.
    #
    # THE NEED IS BUILT FROM THE MODULE'S OWN CONSTANTS, never
    # spelled out here — `FIGURE_TOP_NATIVE` is a transcription
    # (colsum.cpp:683 against :311) and `INK_BOTTOM_MIN` is a
    # measurement over all 54 masters, and a checker that
    # rewrites either as a literal is the second copy decision 5
    # is about. Until 9 September 2026 this said `28 * step +
    # PLATE_LINE`, which was the whole rule then and is one of
    # its two halves now.
    _need2 = _ctk.FIGURE_TOP_NATIVE + 28 - _ctk.INK_BOTTOM_MIN
    _st2 = _ctk.figure_step(_la2, _ov_cfg)
    _bh2 = _ctk.band_height(_la2, _ov_cfg)
    assert _need2 * _st2 <= _bh2, (
        f"{_W}x{_H}: step {_st2} needs {_need2 * _st2} px and the "
        f"band is {_bh2}")
    assert _st2 == max(_ctk.zoomtables.FIGURE_STEPS) or \
        _need2 * (_st2 + 1) > _bh2, (
        f"{_W}x{_H}: step {_st2} was chosen and {_st2 + 1} also "
        f"fits — the rule is the LARGEST that fits")
    # AND THE ORIGIN CLEARS THE PLATE'S LINE, which is the other
    # fact and the one that no longer binds. Kept because the two
    # are different claims: if the transcription is ever revised,
    # this is the floor underneath it.
    assert _ctk.FIGURE_TOP_NATIVE * _st2 >= _ctk.PLATE_LINE, (
        f"{_W}x{_H}: the figure starts "
        f"{_ctk.FIGURE_TOP_NATIVE * _st2} px into the band and the "
        f"plate's line is {_ctk.PLATE_LINE} px — 46 of the 54 "
        f"masters carry ink on canvas row 0")
_ov_rows = [{"index": _i, "name": f"Over {_i}", "pops": 2,
             "jobs": [1, 1, 0], "no_farming": False, "climate": 8,
             "max_pop": 9, "producing": "", "producing_turns": 0,
             "can_buy": False, "production": [1, 1, 1, 1],
             "size": 2, "gravity": 1, "mineral": 2, "growth": 0,
             "morale": 0, "morale_applies": True}
            for _i in range(_ov_fits + 3)]
assert _cl.rows_drawn(_ov_area, _ov_cfg, app.layout.scale,
                      len(_ov_rows)) == _ov_fits, (
    "rows_drawn does not agree with itself about how many fit")
# The wording is in layout.json (decision 15) and {count} is
# substituted by replace (decision 37), so the check reads the
# template rather than hardcoding the sentence.
# ── THE ARROWS SAY IT NOW, NOT A SENTENCE ──
#
# "{count} more not shown" was text where the original has two
# buttons (`_x_fields[1]` and `[2]`, colsum.cpp:263-264), and it
# said what was off screen without offering any way to reach it.
# The statement is the DOWN ARROW being live, so this check moved
# from "ink appears under the last row" to "the arrow that can
# move is drawn differently from the one that cannot" — which is
# the same fault being watched, in the control that replaced the
# sentence.
from screens.colony_summary import colonyscroll as _cscr
_ov_surf = pygame.Surface((_ov_area.right + 8, _ov_area.bottom + 8))

def _arrow_ink(_rows, _first):
    """(up ink, down ink) for a list of `_rows` at `_first`."""
    _ov_surf.fill((0, 0, 0))
    _cl.render(_ov_surf, _rows, _ov_area, _ov_cfg, app.layout,
               app.style, _first)
    _up, _down = _cscr.arrows(_ov_area, _ov_cfg, app.layout.scale)
    assert _up is not None, (
        "the list has no scroll arrows; the column table is what "
        "places them and it is missing")
    return tuple(int(pygame.surfarray.array3d(
        _ov_surf.subsurface(_r)).sum()) for _r in (_up, _down))

# AT THE TOP OF AN OVERFLOWING LIST: down is live, up is not.
_ov_up0, _ov_dn0 = _arrow_ink(_ov_rows, 0)
assert _ov_dn0 > _ov_up0, (
    f"{len(_ov_rows) - _ov_fits} rows are below the window and the "
    f"down arrow is not drawn any brighter than the up one "
    f"({_ov_dn0} against {_ov_up0}) — nothing on screen says there "
    f"is more, which is the fault this check exists for and was "
    f"live until 3 September 2026")
# SCROLLED TO THE BOTTOM: it is the other way round.
_ov_upN, _ov_dnN = _arrow_ink(_ov_rows, len(_ov_rows) - _ov_fits)
assert _ov_upN > _ov_dnN, (
    f"at the bottom of the list the up arrow is not the live one "
    f"({_ov_upN} against {_ov_dnN})")
# A LIST THAT FITS: neither is live, and both are still drawn —
# the original's buttons do not disappear, they stop responding.
_ov_upF, _ov_dnF = _arrow_ink(_ov_rows[:_ov_fits], 0)
assert _ov_upF == _ov_dnF and _ov_upF > 0, (
    f"a list that fits draws its arrows {_ov_upF} and {_ov_dnF}; "
    f"both should be dim and both should be there")
assert _ov_dnF < _ov_dn0, (
    "the dim down arrow is not dimmer than the live one")
# AND THE OLD SENTENCE IS GONE. A renderer that drew both would
# pass everything above.
_ov_surf.fill((0, 0, 0))
_cl.render(_ov_surf, _ov_rows, _ov_area, _ov_cfg, app.layout,
           app.style)
_ov_bands = _cl.row_bands(_ov_area, _ov_cfg, app.layout.scale,
                          len(_ov_rows))
_ov_top = _ov_bands[-1][0] + _ov_bands[-1][1]
_ov_up1, _ = _cscr.arrows(_ov_area, _ov_cfg, app.layout.scale)
# SINCE 8 September 2026 THERE IS NO STRIP TO INK. The bands are
# the window divided by `row_count` with the last taking the
# remainder, so they reach `list_area`'s own bottom and a
# sentence under the last row has nowhere to go. That is the
# stronger form of the same claim, so it is what is asserted —
# a zero-height strip cannot carry the old one.
assert _ov_top == _ov_area.bottom, (
    f"the bands end at {_ov_top} and list_area at "
    f"{_ov_area.bottom} — a strip below the last row is where "
    f"the overflow sentence used to live, and the arrows replaced "
    f"it")
# THE ARROW RECTS COME FROM THE LIST'S OWN GEOMETRY, which is what
# keeps them over the scroll column at every resolution — the same
# `colonytrack.columns` the rows' hit-test uses (decision 5).
_ov_cols = _ct0.columns(_ov_area, _ov_cfg)
assert _ov_up1.x == _ov_cols["scroll"][0], (
    f"the up arrow is at x={_ov_up1.x} and the scroll column "
    f"starts at {_ov_cols['scroll'][0]} — the arrows must come "
    f"from the column table, not from a second position")
assert _ov_up1.width == _ov_cols["scroll"][1]
# ── AN ARROW IS ONE BAND'S WORTH OF CONTROL ─────────────────
# Its height comes from the ROW BAND and never from the column
# width. It was `int(width * HEIGHT_RATIO)` at ratio 1.0 — a
# square whose side was the leftover of the other five columns —
# so at F9 4K, with `col_scroll` swollen to 1837 px, the arrows
# were 1837 px tall: a control the height of the whole list, in
# Data's screenshot of 8 September 2026.
#
# Asserted at several window sizes AND at row counts the shipped
# geometry does not use, because "fits in a band" is a claim
# about the ratio and the clamp, not about ten rows at 1080p —
# and a wide window with few rows is exactly where a
# width-derived height would reappear.
_ov_down1 = _cscr.arrows(_ov_area, _ov_cfg, app.layout.scale)[1]
for _aw, _ah in ((1920, 1080), (2560, 1440), (3440, 1440),
                 (3840, 2160)):
    _alay = Layout(_aw, _ah)
    _abx = {b.name: b for b in _seated(_boxes_path, _aw, _ah)}
    _aarea = _abx["list_area"].screen_rect
    _acfg = dict(_ov_cfg)
    _acfg[_ct0.COLUMNS_KEY] = [
        (_n[4:], _abx[_n]) for _n in
        ("col_name", "col_farmers", "col_workers", "col_scientists",
         "col_building", "col_scroll")]
    _acfg[_ct0.COLUMNS_SPAN_KEY] = (_abx["list_area"].ref_rect[0],
                                    _abx["list_area"].ref_rect[2])
    for _rows_n in (4, 10, 25):
        _acfg["row_count"] = _rows_n
        _aband = _ct0.band_height(_aarea, _acfg)
        _aup, _adown = _cscr.arrows(_aarea, _acfg, _alay.scale)
        for _which, _ar in (("up", _aup), ("down", _adown)):
            assert _ar.height <= _aband, (
                f"{_aw}x{_ah} rows={_rows_n}: the {_which} arrow "
                f"is {_ar.height} px tall in a {_aband} px band — "
                f"an arrow is sized from the band, never from the "
                f"column width")
            assert _aarea.top <= _ar.top and \
                _ar.bottom <= _aarea.bottom, (
                    f"{_aw}x{_ah} rows={_rows_n}: the {_which} "
                    f"arrow {tuple(_ar)} leaves list_area "
                    f"{tuple(_aarea)}")
_ov_cfg.pop("row_count", None)
# AND THE COLUMN IT SITS IN IS THE TRANSCRIBED WIDTH, not the
# leftover of the other five. Native x 619..627 — the arrows'
# field x (colsum.cpp:263-264) and the anim's measured extent —
# is 27 reference px, and `col_scroll` carries exactly that.
_sc_ref = colony_rects()["col_scroll"]
assert _sc_ref[2] == 27, (
    f"col_scroll is {_sc_ref[2]} reference px; the original's "
    f"scroll column is native 619..627 = 9 px = 27 reference "
    f"(colsum.cpp:263-264 for the x, colsum.cpp:278 and :759 for "
    f"the track it holds). A width that is not this one is the "
    f"leftover of the other five columns again")
_lr_scroll = _sjson.load(open(os.path.join(
    SCREENS_DIR, "colony_summary", "layout_reference.json"),
    encoding="utf-8"))
assert _lr_scroll["list_columns"]["scroll"] == 27, (
    "layout_reference.list_columns disagrees with boxes.json "
    "about the scroll column")
assert "621" in _lr_scroll["_list_columns_note"] and \
    "619" in _lr_scroll["_list_columns_note"], (
    "the scroll column's width no longer names the source it is "
    "transcribed from — an unsourced number here is what it was")
assert _cscr.arrow_at(_ov_area, _ov_cfg, app.layout.scale,
                      _ov_up1.center) == "up"
assert _cscr.arrow_at(_ov_area, _ov_cfg, app.layout.scale,
                      (_ov_area.x + 4, _ov_area.centery)) is None

# Nothing below the last drawn band can be selected, because
# row_at only knows the bands render laid out. That held when
# there was no scrolling and it still holds with it: row_at
# answers in BAND numbers over the window it was given, and the
# offset is added by the screen (screen._row_at), so a hidden row
# is unreachable here by construction rather than by luck.
assert _cl.row_at(_ov_area, _ov_cfg, app.layout.scale,
                  len(_ov_rows),
                  (_ov_area.x + 4, _ov_top + 2)) is None, (
    "a point below the last drawn row hit-tests to a row; the "
    "hidden ones are not selectable and must not become so by "
    "accident")
ok("colony list overflow (rows drawn against rows present, the "
   "count is named, nothing drawn when nothing is dropped)")
