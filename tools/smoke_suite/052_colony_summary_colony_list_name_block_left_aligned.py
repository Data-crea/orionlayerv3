# smoke-suite area: colony_summary
#
# Part of the OrionLayer smoke suite — 052_colony_summary_colony_list_name_block_left_aligned.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (91 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 2 check(s) it holds:
#   - colony list name block (left-aligned like the original, the game's own name bound, marked second
#   - a colony that is building something shows what ( id(s) through the real resolver, ink inside the


# ── The name block: LEFT-aligned in its own cell ────────────
# It was right-aligned, and that was a marked deviation
# (decision 45): a 236 px name column shared a budget with the
# track, so the overflow had to grow LEFT into `pad_x` where
# nothing was drawn instead of rightward onto the first slots.
# **The column is a box now**, the widest name the game can
# produce fits it, and the alignment goes back to the original's
# — `Squeeze_Formatted_Paragraph_Centered_(0x0C, y, …, 0)` passes
# JUSTIFY_LEFT (colsum.cpp:582, bill.cpp:210).
#
# Asserted at the game's own maximum, which is NOT fifteen
# arbitrary characters: `Do_Change_Star_Name_` caps the input
# field at the pixel width of seven W's (namestar.cpp:246-256) on
# top of the `char[15]` buffer.
_nb_cfg = _column_cfg(_cfg, app.layout, _area)
_surf.fill((0, 0, 0))
# SCANNED, like every fixture that measures the name's ink — the
# original always has exactly one scanned colony (colsum.cpp:
# 880-890 has no else branch) and `Selection.reseat` mirrors it.
_cl.render(_surf, [{"name": _cl.NAME_BOUND_STAR, "index": 4,
                    "pops": 3, "jobs": [1, 1, 1],
                    "no_farming": False, "climate": 8,
                    "max_pop": 9}],
           _area, _nb_cfg, app.layout, app.style, scanned=4)
_px = pygame.surfarray.array3d(_surf)
_scale = app.layout.scale
_nb_cols = _ctk.columns(_area, _nb_cfg)
_nx, _nw = _nb_cols["name"]
_rgb = tuple(_cl.ROW_NAME[:3])
_name_cols = [x for x in range(_area.x, _area.right)
              if any(tuple(_px[x, y]) == _rgb
                     for y in range(_area.y, _area.bottom))]
assert _name_cols, "the name did not draw at all"
assert min(_name_cols) >= _nx, (
    f"the name starts at x={min(_name_cols)}, left of its column "
    f"at {_nx}")
assert max(_name_cols) < _nx + _nw, (
    f"the widest producible name reaches x={max(_name_cols)}, past "
    f"its column at {_nx + _nw} — it is on the farmers column")
# LEFT: the ink starts in the first third of the cell. Measured on
# the picture, because "the renderer blits at left" is what the
# right-aligned version could also have claimed about its own
# edge.
assert min(_name_cols) - _nx < _nw // 3, (
    f"the name's ink starts {min(_name_cols) - _nx} px into a "
    f"{_nw} px column — that is not left-aligned")

# ── The detail line ──
# Climate name plus n/max, from the same row dict, under the name.
# The climate is an index into the PLANET_CLIMATE enum
# (orion2_consts.h:362-374) and the wording lives in layout.json,
# so this asserts the wiring, not the words.
assert _cl._detail_text(
    {"climate": 8, "pops": 12, "max_pop": 14}, _cfg) == "Terran 12/14"
assert _cl._detail_text(
    {"climate": 0, "pops": 1, "max_pop": 42}, _cfg) == "Toxic 1/42"
assert len(_cfg["climates"]) == 10, _cfg["climates"]
# An index the enum does not cover must degrade, not raise: the
# climate byte is one unverified value away from being anything.
for _bad in (-1, 10, 255):
    assert "?" in _cl._detail_text(
        {"climate": _bad, "pops": 1, "max_pop": 2}, _cfg), _bad
# Substitution is a REPLACE, not str.format (decision 37): a
# translated string with a stray brace must not raise inside the
# render path, and an unknown placeholder must survive to be seen.
_braced = dict(_cfg)
_braced["detail"] = "{climate} {pops}/{max_pop} {not_a_key} }{"
_out = _cl._detail_text({"climate": 9, "pops": 2, "max_pop": 3}, _braced)
assert _out == "Gaia 2/3 {not_a_key} }{", _out

# Both lines start on the same edge, so the eye drops straight
# down rather than crossing a ragged one per row.
_surf.fill((0, 0, 0))
_cl.render(_surf, [{"name": "Sol", "index": 4, "pops": 12,
                    "jobs": [4, 5, 3], "no_farming": False,
                    "climate": 8, "max_pop": 14}],
           _area, _nb_cfg, app.layout, app.style, scanned=4)
_px = pygame.surfarray.array3d(_surf)
_detail_rgb = tuple(_cl.DETAIL_COLOR[:3])
_left_of = lambda rgb: min(
    x for x in range(_area.x, _area.right)
    if any(tuple(_px[x, y]) == rgb for y in range(_area.y, _area.bottom)))
assert abs(_left_of(_rgb) - _left_of(_detail_rgb)) <= 2, (
    f"name starts at {_left_of(_rgb)}, detail at "
    f"{_left_of(_detail_rgb)} — the two lines are not aligned")
# ── THE BRIGHT NAME AND THE DESCRIPTION READ ONE STATE ──────
#
# The original drives both from `_g_colony_n`:
# `Set_Colony_Font_To_Blue_(2, colony_idx == _g_colony_n)` colours
# the name (colsum.cpp:554) and `Draw_Colony_Scan_Info_` fills the
# scan box for the same index (colsum.cpp:1155). So a separate
# hover for the colour would be two answers to one question, and
# the failure would be the quiet kind — a bright name over one
# row and a description of another, every value on screen correct.
#
# Asserted on the SURFACE and on the panel's own input, at three
# scanned colonies, so it holds for whichever row is scanned and
# not just for row 0.
_sc_rows = [{"name": f"Colony {i}", "index": 10 + i, "pops": 2,
             "jobs": [1, 1, 0], "no_farming": False, "climate": 8,
             "max_pop": 6} for i in range(3)]
from screens.colony_summary import colonyselect as _csel2
_sc_sel = _csel2.Selection()
for _pick in (10, 11, 12):
    _sc_sel.rows = _sc_rows
    _sc_sel.colony = _pick
    assert _sc_sel.row()["index"] == _pick, (
        "the panel's input is not the scanned colony")
    _surf.fill((0, 0, 0))
    _cl.render(_surf, _sc_rows, _area, _nb_cfg, app.layout,
               app.style, scanned=_sc_sel.colony)
    _p2 = pygame.surfarray.array3d(_surf)
    _bands = _ctk.row_bands(_area, _nb_cfg, app.layout.scale,
                            len(_sc_rows))
    _bright = []
    for _i, (_top, _h) in enumerate(_bands):
        _has = any(tuple(_p2[x, y]) == tuple(_cl.ROW_NAME[:3])
                   for x in range(_area.x, _area.x + 300)
                   for y in range(_top, _top + _h))
        if _has:
            _bright.append(_sc_rows[_i]["index"])
    assert _bright == [_pick], (
        f"scanned colony {_pick} but the bright name is on "
        f"{_bright} — the name colour and the description panel "
        f"must read one state")
# AND THE SCREEN HANDS THE SAME VALUE TO BOTH. A grep, because the
# two calls are in different methods and the drift would be a
# second source appearing rather than this value changing.
_cs_screen_src = open(os.path.join(
    SCREENS_DIR, "colony_summary", "screen.py"), encoding="utf-8").read()
# SLICED TO THE METHOD, not grepped over the file. The first
# version of this looked for `self._selected)` anywhere in
# screen.py and passed against a broken tree, because
# `_render_inset` carries `galaxy_inset_label(self._state,
# self._selected),` and that substring contains it. A check
# anchored on the wrong feature is stable, repeatable and wrong.
_rl_body = _cs_screen_src.split("def _render_list(")[1].split(
    "\n    def ")[0]
assert "self._selected" in _rl_body, (
    "`_render_list` no longer hands `_selected` to "
    "`colonylist.render` — the bright name would then have a "
    "source of its own, and a name bright over one row with the "
    "description of another is the quiet kind of wrong")
assert "_row_name_note" in open(
    os.path.join(os.path.dirname(SCREENS_DIR), "assets", "shared",
                 "skins", "default", "colors.json"),
    encoding="utf-8").read(), (
    "colors.json no longer records where the two name colours "
    "come from")

# THE SECOND LINE IS AN HD EXTENSION, marked in three homes.
assert "HD EXTENSION" in (_cl._draw_name_block.__doc__ or ""), (
    "the per-row second line is no longer marked where it is drawn")
assert "HD EXTENSION" in _cfg.get("_hd_extension", ""), (
    "layout.json list._hd_extension no longer carries it")
ok("colony list name block (left-aligned like the original, the "
   "game's own name bound, marked second line)")

# ── The building column squeezes; it never truncates ──
# 190 px is a HARD width, transcribed from
# Squeeze_Print_Formatted_Paragraph_(0x200, y, 0x55, 0x16)
# (colsum.cpp:621). _Squeeze_Print_Paragraph_ (bill.cpp:147) wraps
# into the width and shrinks until the HEIGHT fits; there is no
# truncation branch in it at all. The behaviour is transcribed,
# not the three steps — the first of those narrows the space
# glyph, a bitmap-font trick Aldrich has no equivalent for.
from screens.colony_summary import colonybuild as _cb
# THE COLUMN IS A BOX NOW, so its width comes from the box and
# not from a tuned `building_width` that agreed with it.
_bw = int(_ctk.columns(_area, _nb_cfg)["building"][1]
          / app.layout.scale)
_small = app.layout.font_size(_cfg["small_font"])
_floor = app.layout.font_size(_cfg["build_font_min"])
_sizes = list(range(_small, _floor - 1, -1))
for _text in ("Trade Goods", "Atmosphere Renewer",
              "Alien Control Center", "W" * 15,
              "Refit " + "W" * 15):
    _lines, _size = _cb.squeeze_lines(
        app.style, _text, _bw,
        int(_ctk.band_height(_area, _nb_cfg)
            / app.layout.scale), _sizes, (255,) * 3)
    # Never truncate: every word of the source survives.
    _kept = " ".join(_cb.wrap_text(app.style, _text, _size, _bw)).split()
    assert _kept == _text.split(), (_text, _kept)
    # The hard side is the width.
    assert max(s.get_width() for s in _lines) <= _bw, (
        f"{_text!r} squeezed to {max(s.get_width() for s in _lines)} px "
        f"in a {_bw} px column — the width is the reservation")
    assert _floor <= _size <= _small, (_text, _size)

# A single word wider than the column cannot be broken, so it fits
# the height on one line and never triggers a height-driven
# shrink. That is exactly how a 15-glyph ship design sat at 225 px
# in a 190 px column; the fit test has to be both dimensions.
#
# THE WORD IS GROWN AGAINST THE COLUMN, not written as a literal —
# corrected 9 September 2026. It was `"W" * 15`, which was wider
# than the column on the day it was written and stopped being so
# the moment `col_building` took the nine reference px that
# `col_scroll` gave up when its width became a transcription. The
# check then passed a word that FITS to an assertion about words
# that do not, and reported the squeeze as broken. The premise
# ("wider than the column") is the thing to state; how many W's
# that takes is a fact about a font and a box, and belongs to
# whichever of them changed.
_ww = 2
while (app.style.render_text("W" * _ww, _small, (255,) * 3
                             ).get_width() <= _bw and _ww < 200):
    _ww += 1
assert _ww < 200, (
    f"no unbreakable word overruns the {_bw} px building column, "
    f"so the width-driven shrink cannot be exercised at all")
_wide, _wsize = _cb.squeeze_lines(
    app.style, "W" * _ww, _bw, 999, _sizes, (255,) * 3)
assert _wsize < _small, (
    f"an unbreakable word of {_ww} W's, {app.style.render_text('W' * _ww, _small, (255,) * 3).get_width()} px "
    f"in a {_bw} px column, did not shrink — the squeeze is "
    f"driven by height alone again")

# And when nothing is left to shrink it still draws everything:
# the original prints the paragraph once its loop runs out.
_tiny, _tsize = _cb.squeeze_lines(
    app.style, "W" * 60, 40, 4, _sizes, (255,) * 3)
assert _tiny and _tsize == _sizes[-1], (_tsize, len(_tiny))
# ── A COLONY THAT IS BUILDING SOMETHING SHOWS WHAT ──────────
#
# **THE WHOLE CHAIN, NOT THE SQUEEZE.** Everything above measures
# `squeeze_lines` on a string somebody typed here; nothing asserted
# that a production ID reaching the row builder comes out of
# `colonybuild.draw` as INK. Those are different failures with the
# same look — an empty column — and the second one is the report
# that prompted this check: a live screen whose BUILDING column
# was blank at every row, where every module on the path had in
# fact been untouched for a week.
#
# ID -> NAME -> PIXELS, at 1920x1080 and 2560x1440, through the
# real `prodname.Resolver` and the real renderer. Two ids, because
# `Selection_Name_` reaches two different files for them
# (colbldg.cpp:796-820): -2 is TRADE_GOODS through
# `Option_String_` and the player's ESTRINGS.LBX, and a building
# id goes through `Real_Building_Name_` and TECHNAME.LBX. A tree
# with one extracted and not the other is a real state, and the
# check says which half is absent instead of failing blankly.
#
# THE MEASURE IS A DELTA, not "some ink in the column": the row
# plates draw there too, so a cell that lost its text still has
# thousands of lit pixels. Empty against named, same cell, same
# geometry — that difference IS the text.
from core import prodname as _pn_mod
from screens.colony_summary import colonybuild as _cbuild
_pn = _cbuild.names_for(d.screens["colony_summary"])
_ids = [(-2, "an option (TRADE_GOODS, Option_String_, "
             "ESTRINGS.LBX)"),
        (1, "a building (Real_Building_Name_, TECHNAME.LBX)")]
_named = []
for _pid, _what in _ids:
    _txt, _st = _pn.name(_pid)
    if _st == _pn_mod.STATE_OK and _txt:
        _named.append((_pid, _txt))
    else:
        report(f"building column: id {_pid} is {_what} and resolves "
               f"to {_txt!r}/{_st!r} — not extracted on this disk, "
               f"so it is not measured here")
if not _named:
    # THE SAME TREATMENT AS THE JSON CHECK — 13 September 2026. The
    # two name files are extracted from the player's install and
    # gitignored (decision 40), so a fresh clone has neither and
    # used to fail here before anyone had run an extractor. Absence
    # is allowed ONLY as absence: both files missing AND ignored by
    # git. A file that is present and still resolves nothing is a
    # real fault and still fails. The renderer half is measured
    # either way, with a stand-in name, so the pixels are checked
    # even on a clone.
    from core.buildnames import name_file as _bn_file
    from core.estrings import string_file as _es_file
    _bn_lang = (settings or {}).get("language", "en")
    _bn_root = os.path.dirname(SCREENS_DIR)
    _bn_rel = [_bn_file(_bn_lang), _es_file(_bn_lang)]
    _bn_present = [_f for _f in _bn_rel
                   if os.path.exists(os.path.join(_bn_root, _f))]
    assert not _bn_present, (
        f"neither a building id nor an option id resolves to a name, "
        f"yet {_bn_present} exist on this disk — the files are there "
        f"and the resolver reads nothing from them. Re-run "
        f"`python tools/techname_extract.py` and `python "
        f"tools/estrings_extract.py`")
    if os.path.isdir(os.path.join(_bn_root, ".git")):
        import subprocess as _bn_sp
        _bn_ign = set(_bn_sp.run(
            ["git", "-C", _bn_root, "check-ignore", "--no-index",
             *_bn_rel], capture_output=True, text=True).stdout.split())
        assert set(_bn_rel) <= _bn_ign, (
            f"the name files may be absent only because they are "
            f"generated and gitignored; git does not ignore "
            f"{sorted(set(_bn_rel) - _bn_ign)}")
    report("building column: no name files on this disk (a fresh "
           "clone) — the resolver half is not measured; the renderer "
           "half is, with a stand-in name")
    _named = [(-2, "Trade Goods")]
for _bspec in ("1920x1080", "2560x1440"):
    _bw2, _bh2 = (int(v) for v in _bspec.split("x"))
    _blay = Layout(_bw2, _bh2)
    _bboxes = {b.name: b for b in _seated(
        os.path.join(SCREENS_DIR, "colony_summary", "boxes.json"),
        _bw2, _bh2)}
    _barea = pygame.Rect(*_blay.rect(_bboxes["list_area"].ref_rect))
    _bcfg = dict(_nb_cfg)
    _bcfg[_ctk.COLUMNS_KEY] = [(n[4:], _bboxes[n]) for n in
                               _chdr.COLUMN_BOXES]
    _bcfg[_ctk.COLUMNS_SPAN_KEY] = (_bboxes["list_area"].ref_rect[0],
                                    _bboxes["list_area"].ref_rect[2])
    _bcol = _ctk.columns(_barea, _bcfg)["building"][1]
    _bband = _ctk.band_height(_barea, _bcfg)
    _empty = pygame.Surface((_bcol, _bband))
    _empty.fill((0, 0, 0))
    _cb.draw(_empty, {"producing": "", "producing_state": "ok"},
             0, 0, _bcol, _bband, _bcfg, app.style, _blay)
    _base = int((pygame.surfarray.array3d(_empty).sum(axis=2)
                 > 40).sum())
    for _pid, _txt in _named:
        _cell = pygame.Surface((_bcol, _bband))
        _cell.fill((0, 0, 0))
        _cb.draw(_cell, {"producing": _txt, "producing_state": "ok",
                         "producing_turns": 3, "producing_id": _pid},
                 0, 0, _bcol, _bband, _bcfg, app.style, _blay)
        _arr = pygame.surfarray.array3d(_cell).sum(axis=2) > 40
        _ink = int(_arr.sum())
        assert _ink > _base, (
            f"{_bspec}: a colony producing {_txt!r} (id {_pid}) "
            f"draws {_ink} lit px in its {_bcol}x{_bband} building "
            f"cell and an empty one draws {_base} — the name "
            f"reached the row and no glyph reached the screen")
        # AND THE INK IS INSIDE THE CELL, which is the other way
        # this goes blank: text placed past the column's own edge
        # is drawn and then clipped by the list.
        _xs = np.where(_arr.any(axis=1))[0]
        _ys = np.where(_arr.any(axis=0))[0]
        assert _xs.min() >= 0 and _xs.max() < _bcol, (
            f"{_bspec}: {_txt!r} inks x {_xs.min()}..{_xs.max()} "
            f"in a {_bcol} px column")
        assert _ys.min() >= 0 and _ys.max() < _bband, (
            f"{_bspec}: {_txt!r} inks y {_ys.min()}..{_ys.max()} "
            f"in a {_bband} px band")
ok(f"a colony that is building something shows what "
   f"({len(_named)} id(s) through the real resolver, ink inside "
   f"the cell at 1920x1080 and 2560x1440)")
