# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 051_core_colony_summary_sidebar_six_s_player.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (93 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 6 check(s) it holds:
#   - colony summary sidebar (six s_player scalars kinded and held to the verified spec, sign rule per
#   - colony list (rows, No Farming below a full track and clear of the hatching, horizontal budget ba
#   - a cell plate on every band, FIVE per band, whatever the colony count (the original's are in COLS
#   - colony cells: a plate per cell of every band, the plate rect IS the drop rect, and one home for 
#   - colony list geometry is boxes and a row count (nine tuned values gone, a save writes nothing der
#   - colony columns tile list_area at window sizes, built AND resized into (one coordinate frame: eve


# ── output_panel: decision 43 is WITHDRAWN ──
# It marked output_panel an HD EXTENSION on the strength of a
# word grep of one file. The original draws all four ECON values
# per colony — Draw_Colony_Scan_Info_ (colsum.cpp:1155) loops
# Draw_Colony_Wee_Prod_ into Draw_Colony_Prod_Both_
# (coldraw.cpp:36), which reads colony->production[] at
# coldraw.cpp:60. The panel is a TRANSCRIPTION. This check keeps
# the withdrawal from being quietly reverted.
_scr_src = open(os.path.join(SCREENS_DIR, "colony_summary",
                             "screen.py"), encoding="utf-8").read()
assert "WITHDRAWN" in _fund_src, (
    "fundament 43 no longer records that it was withdrawn — it "
    "claimed the original never draws per-colony food/industry/"
    "research, and coldraw.cpp:60 does")
assert "coldraw.cpp:60" in _fund_src and "coldraw.cpp:60" in _scr_src, (
    "the withdrawal no longer cites where the original actually "
    "draws production[] — a retraction without its evidence is "
    "how the original error got in")
assert "TRANSCRIPTION" in _scr_src, (
    "screen.py no longer records output_panel as a transcription")
ok("colony summary sidebar (six s_player scalars kinded and held "
   "to the verified spec, sign rule per row, ESTR/join/justify "
   "provenance, output_panel marked TRANSCRIPTION)")

ok("colony list (rows, No Farming below a full track and clear of "
   "the hatching, horizontal budget balances to the pixel, name "
   "clipped to its column, INVENTION + HD EXTENSION marked, "
   "preview rows match build_rows and carry a provenance band)")

# ── A PLATE PER CELL OF EVERY BAND, WHATEVER THE COLONY ─────
#    COUNT
#
# The original has no per-row plate decision to make: the cells
# are painted into COLSUM.LBX entry 0, the one bitmap
# `Draw_Colony_Summary_Screen_` blits (`animate::Draw_(0, 0,
# _anims[0])`, colsum.cpp:461), so a plate is part of the picture.
# Counted on its own framebuffer, `colony_summary_native_split.png`
# in the fixtures: eight colonies, TEN plated bands.
#
# HD drew them inside the per-ROW renderer until 9 September 2026,
# so seven colonies gave seven plated bands and 197 reference px
# of bare panel. The claim that every band is plated was in the
# code comment, in decision 51 and in the status document, and
# was true in none of the three — a marking that three documents
# assert is still not the behaviour, which is the fundament's own
# lesson one domain over. Nothing could see it because no check
# counted the rects.
_plate_cfg = _column_cfg(_cfg, app.layout, _area)
_plate_seen = []
_real_plate = app.style.draw_plate

def _spy_plate(_surf, _rect, _scale, _colour, *a, **kw):
    _plate_seen.append(pygame.Rect(_rect))
    return _real_plate(_surf, _rect, _scale, _colour, *a, **kw)

_plate_surf = pygame.Surface((1920, 1080))
try:
    app.style.draw_plate = _spy_plate
    for _n_col in (0, 1, 3, 7, 10, 25):
        _plate_rows = _pv_rows[:_n_col] if _n_col <= len(_pv_rows) else (
            (_pv_rows * 30)[:_n_col])
        if _n_col and not _plate_rows:
            continue
        _plate_seen.clear()
        _plate_surf.fill((0, 0, 0))
        _cl.render(_plate_surf, _plate_rows, _area, _plate_cfg,
                   app.layout, app.style)
        _want_rows = int(_plate_cfg.get("row_count", 10))
        # FIVE COLUMNS, not six — 9 September 2026. The scroll
        # slot stopped being a column of the row when the slider
        # was transcribed: the original has one continuous track
        # there (`Draw_Bar_Indicator_`, colsum.cpp:747-771), not
        # ten stacked cells. The other five are plated because
        # the original's bitmap plates them.
        _want = _want_rows * 5
        # An EMPTY list draws the "no colonies" word and no row
        # geometry at all, which is the original's own blank
        # screen; every other count owes the full grid.
        if _n_col == 0:
            continue
        assert len(_plate_seen) == _want, (
            f"{_n_col} colonies drew {len(_plate_seen)} cell "
            f"plates; the window has {_want_rows} bands and five "
            f"plated columns, so it owes {_want} whatever the "
            f"list holds — the original's are in a bitmap and "
            f"cannot be conditional on anything")
        # AND THEY TILE THE WINDOW: every band's plates share one
        # top and one height, and the bands reach list_area's own
        # bottom. Counting alone would pass on six plates drawn
        # ten times in the same place.
        _by_top = collections.defaultdict(list)
        for _r in _plate_seen:
            _by_top[(_r.top, _r.height)].append(_r)
        assert len(_by_top) == _want_rows, (
            f"{_n_col} colonies: {len(_plate_seen)} plates in "
            f"{len(_by_top)} distinct bands, wanted {_want_rows}")
        _tops = sorted(_by_top)
        assert _tops[0][0] == _area.y, (
            f"the first band starts at {_tops[0][0]}, list_area "
            f"at {_area.y}")
        assert _tops[-1][0] + _tops[-1][1] == _area.bottom, (
            f"the last band ends at {_tops[-1][0] + _tops[-1][1]}, "
            f"list_area at {_area.bottom} — a strip below the "
            f"last band belongs to nobody")
        for _i, _key in enumerate(_tops[:-1]):
            assert _key[0] + _key[1] == _tops[_i + 1][0], (
                f"band {_i} ends at {_key[0] + _key[1]} and the "
                f"next starts at {_tops[_i + 1][0]}")
finally:
    app.style.draw_plate = _real_plate
# AND THE SCROLL COLUMN IS NOT AMONG THEM: it carries one track,
# drawn once, not a plate per band.
_plate_scroll_x = _plate_cfg and _ctk.columns(
    _area, _plate_cfg).get(_cscr.COLUMN)
if _plate_scroll_x:
    _sx, _sw = _plate_scroll_x
    assert not any(_r.x == _sx and _r.width == _sw
                   for _r in _plate_seen), (
        "the scroll column is being plated per band again; the "
        "original has one continuous track there")
ok("a cell plate on every band, FIVE per band, whatever the "
   "colony count (the original's are in COLSUM.LBX entry 0 and "
   "cannot be conditional; the scroll slot carries one track "
   "instead of ten cells)")

# ── The square is a fixed unit, not a ruler that moves ──
# The unit used to be derived from the widest max_pop in the
# current list, so acquiring one better colony resized every
# square on the screen and a square counted last turn was not the
# square counted this turn. It now comes from POP_LIMIT_CAP, the
# engine's own ceiling (colcalc.cpp:930, pop[], colmove.cpp:518).
#
# Asserted in pixels rather than by reading the arithmetic: the
# SAME row, drawn alone and drawn beside a colony twice its size,
# must come out identical pixel for pixel. Reimplementing the
# unit formula here would only check it against itself.
# THE BAND IS DERIVED NOW: `list_area` divided by
# `list.row_count`, so this reads it from the same function the
# renderer does rather than from two tuned values that are gone.
_sq_cfg = _column_cfg(_cfg, app.layout, _area)
_band = pygame.Rect(_area.x, _area.y, _area.w,
                    _ctk.band_height(_area, _sq_cfg))

def _first_row_pixels(_rowset):
    _s = pygame.Surface((1920, 1080))
    _s.fill((0, 0, 0))
    _cl.render(_s, _rowset, _area, _sq_cfg, app.layout, app.style)
    return pygame.surfarray.array3d(_s.subsurface(_band))

_modest = {"name": "Alpha I", "pops": 4, "jobs": [1, 2, 1],
           "no_farming": False, "max_pop": 8}
_grand = {"name": "Beta II", "pops": 30, "jobs": [10, 12, 8],
          "no_farming": False, "max_pop": _cr.POP_LIMIT_CAP}
assert (_first_row_pixels([_modest])
        == _first_row_pixels([_modest, _grand])).all(), (
    "the colony list's square still changes size with the row set "
    "— the unit must come from POP_LIMIT_CAP, not from the widest "
    "max_pop currently on screen")

# ── FIFTY PLATES, AND THE PLATE IS THE DROP RECT ────────────
# Replaces "three regions, three visual states" — the filled /
# free / unreachable run belonged to the single 42-slot track,
# which went with the nine tuned values on 8 September 2026. The
# count does not go down: an obsolete check is replaced, and the
# subject is the same one row drawn correctly.
#
# **A DEVIATION IN KIND, and that is what makes the empty rows
# matter.** The original has NO per-cell drawing call at all:
# `Draw_Colony_Summary_Screen_` blits one bitmap —
# `animate::Draw_(0, 0, _anims[0])`, COLSUM.LBX entry 0
# (colsum.cpp:461, loaded at :404-408) — and the plates are
# painted into it. That is why every cell has one whether or not a
# colony sits there. HD cannot ship that bitmap (decision 42), so
# it draws them, and the plate is `StyleRenderer.draw_plate`
# (decision 51).
_pl_cfg = _column_cfg(_cfg, app.layout, _area)
_surf.fill((0, 0, 0))
_cl.render(_surf, [{"name": "Regions I", "pops": 4,
                    "jobs": [1, 2, 1], "no_farming": False,
                    "max_pop": 9}],
           _area, _pl_cfg, app.layout, app.style)
_px = pygame.surfarray.array3d(_surf)
_plate_rgb = list(_cl.PLATE_COLOR[:3])
_pl_bands = _cl.row_bands(_area, _pl_cfg, app.layout.scale, 1)
_pl_boxes = _ctk.row_boxes(_area, _pl_cfg, app.layout.scale,
                           {"name": "Regions I", "pops": 4,
                            "jobs": [1, 2, 1], "no_farming": False,
                            "max_pop": 9}, _pl_bands[0])
assert len(_pl_boxes.targets) == 3, _pl_boxes.targets
for _job, _rect in _pl_boxes.targets:
    # THE PLATE RECT IS THE DROP RECT. Read off the surface: the
    # plate's own colour on every edge of the target.
    for _side, _pt in (("left", (_rect.x, _rect.centery)),
                       ("right", (_rect.right - 1, _rect.centery)),
                       ("top", (_rect.centerx, _rect.y)),
                       ("bottom", (_rect.centerx, _rect.bottom - 1))):
        _seg = _px[max(0, _pt[0] - 2):_pt[0] + 3,
                   max(0, _pt[1] - 2):_pt[1] + 3]
        assert (_seg == _plate_rgb).all(axis=2).any(), (
            f"job {_job}'s plate has no {_side} edge where its "
            f"drop rect has one — the plate rect IS the drop rect "
            f"(decision 5)")
# AND THE BAND IS THE WHOLE OF IT. The pick round left a marked
# DEVIATION here: the drop target was `bar_h`, 30 reference px of
# a 58 px row, so a click in the outer 14 px of a row discarded
# the selection where the original would have dropped. The target
# is the band now and that deviation is CLOSED.
_pl_top, _pl_h = _pl_bands[0]
for _job, _rect in _pl_boxes.targets:
    assert (_rect.y, _rect.height) == (_pl_top, _pl_h), (
        f"job {_job}'s drop rect is {_rect.y}..{_rect.bottom} and "
        f"the band is {_pl_top}..{_pl_top + _pl_h} — the pick "
        f"round's 52 %-of-the-band deviation is back")
# EVERY BAND, INCLUDING THE EMPTY ONES. Ten bands, three plates
# each, on a list of one colony.
_pl_all = _cl.row_bands(_area, _pl_cfg, app.layout.scale, 99)
assert len(_pl_all) == 10, len(_pl_all)
_pl_rows = [{"name": f"C{i}", "pops": 1, "jobs": [1, 0, 0],
             "no_farming": False, "max_pop": 4} for i in range(10)]
_surf.fill((0, 0, 0))
_cl.render(_surf, _pl_rows, _area, _pl_cfg, app.layout, app.style)
_px = pygame.surfarray.array3d(_surf)
for _i, (_bt, _bh) in enumerate(_pl_all):
    _rows_with = [_y for _y in range(_bt, _bt + _bh)
                  if (_px[_area.x:_area.right, _y]
                      == _plate_rgb).all(axis=1).any()]
    assert len(_rows_with) >= 2, (
        f"band {_i} carries plate ink on {len(_rows_with)} rows; "
        f"every band draws its three plates, empty or not — the "
        f"original's are in the background bitmap and are there "
        f"whatever the row holds")
# ONE HOME FOR THE PLATE. The rounded-rect arithmetic existed in
# `draw_thin_border` AND in `colonyheader.render`; it is
# `draw_plate`'s now and a grep is what keeps it that way.
#
# THE FINGERPRINT IS THE EXPRESSION AND NOT THE LINE — corrected
# 12 September 2026, when `draw_plate` grew a `radius` parameter
# and the default moved off the `border_radius=` keyword onto its
# own line. The grep was for `border_radius=max(6, int(10 *
# scale))` and matched NOTHING, which this check reported as
# "lives in []" rather than passing — the failure mode a
# zero-tolerance list is supposed to have, and it had it.
_plate_hits = []
for _dp, _dn, _fns in os.walk(_proj):
    _dn[:] = [x for x in _dn if x not in ("__pycache__", ".git")]
    for _fn in _fns:
        if not _fn.endswith(".py"):
            continue
        _fp = os.path.join(_dp, _fn)
        if os.path.relpath(_fp, _proj) in SUITE_FILES:
            continue
        # The ASSIGNMENT, not the expression: `colonyheader`
        # quotes the expression in a docstring recording where it
        # used to live, and a grep that matched prose would report
        # the history as a second home.
        if "radius = max(6, int(10 * scale))" in \
                open(_fp, encoding="utf-8").read():
            _plate_hits.append(os.path.relpath(_fp, _proj))
assert _plate_hits == [os.path.join("core", "style.py")], (
    f"the plate's rounded-rect arithmetic lives in {_plate_hits}; "
    f"one home, which is StyleRenderer.draw_plate (decision 51)")
ok("colony cells: a plate per cell of every band, the plate rect "
   "IS the drop rect, and one home for the arithmetic")

# ── NINE VALUES DIED, AND NOTHING READS THEM ────────────────
# `row_height`, `pad_x`, `pad_y`, `name_width`, `name_gap`,
# `bar_height`, `tail_width`, `building_width`, `growth_gap`. Each
# answered a question a column BOX or `list.row_count` now
# answers, and a tuned number that agrees with a derived one is
# the second copy decision 5 is about. Greppped rather than
# asserted on the config, because a `cfg.get("row_height", 58)`
# would keep working off the default and nothing would say so.
_DEAD = ("row_height", "pad_x", "pad_y", "name_width", "name_gap",
         "bar_height", "tail_width", "building_width", "growth_gap")
_dead_hits = {}
for _dp, _dn, _fns in os.walk(_proj):
    _dn[:] = [x for x in _dn if x not in ("__pycache__", ".git")]
    for _fn in _fns:
        if not _fn.endswith(".py"):
            continue
        _fp = os.path.join(_dp, _fn)
        _rel2 = os.path.relpath(_fp, _proj)
        if _rel2 in SUITE_FILES:
            continue
        # SCOPED TO THE LIST CFG'S READERS. `colonyoutput` has
        # its own `pad_x`/`pad_y` under the `output` block, which
        # is a different config and a legitimate one — a
        # tree-wide grep on the bare word would be measuring the
        # wrong object, which is the failure the fundament names
        # twice.
        if os.path.basename(_fp) not in (
                "colonylist.py", "colonytrack.py", "colonybuild.py",
                "colonyscroll.py", "colonypopup.py",
                "colonyheader.py", "colony_list_preview.py",
                "colony_move_hd.py"):
            continue
        _txt = open(_fp, encoding="utf-8").read()
        for _k in _DEAD:
            # A READ, not a mention: the notes that record why
            # each one died name them, which is the point.
            for _form in (f'cfg["{_k}"]', f'cfg.get("{_k}"',
                          f'"{_k}":'):
                if _form in _txt:
                    _dead_hits.setdefault(_k, []).append(_rel2)
assert not _dead_hits, (
    f"the retired list values are still read: {_dead_hits}. They "
    f"are a column box or `list.row_count` now — a default that "
    f"keeps working is exactly how the tuned copy survives")
_lj = _sjson.load(open(os.path.join(
    SCREENS_DIR, "colony_summary", "layout.json"), encoding="utf-8"))
for _k in _DEAD:
    assert _k not in _lj["list"], (
        f"layout.json list.{_k} is back")
assert _lj["list"]["row_count"] == 10, _lj["list"]["row_count"]

# ── AN EDITOR SAVE WRITES NO DERIVED VALUE ──────────────────
# Save, reload, diff. The band, the step, the cell, the drop and
# the plate rects are computed every frame (decision 37's shape,
# applied to geometry), so none of them may appear in boxes.json
# — and the six column boxes must come back exactly as they went
# in, because `sync_columns` writes the derived width and y back
# into them and a save is where that would leak a stray drag.
from core.box import save_boxes as _save_boxes
_sd_screen = d.screens["colony_summary"]
_before_json = _sjson.load(open(os.path.join(
    SCREENS_DIR, "colony_summary", "boxes.json"), encoding="utf-8"))
with _tf.TemporaryDirectory() as _sd_dir:
    _sd_path = os.path.join(_sd_dir, "boxes.json")
    io_shutil = __import__("shutil")
    io_shutil.copy(os.path.join(SCREENS_DIR, "colony_summary",
                                "boxes.json"), _sd_path)
    _chdr.sync_columns(_sd_screen)
    _save_boxes(_sd_dir, _sd_screen.boxes, 1920, 1080)
    _after_json = _sjson.load(open(_sd_path, encoding="utf-8"))
_names_before = {b["name"] for b in _before_json["1920x1080"]}
_names_after = {b["name"] for b in _after_json["1920x1080"]}
assert _names_before == _names_after, (
    f"a save changed which boxes exist: "
    f"{_names_before ^ _names_after}")
_rects_before = {b["name"]: b.get("rect") for b in _before_json["1920x1080"]}
_rects_after = {b["name"]: b.get("rect") for b in _after_json["1920x1080"]}
assert _rects_before == _rects_after, (
    f"a save moved a box: "
    f"{ {k: (_rects_before[k], _rects_after[k]) for k in _rects_before if _rects_before[k] != _rects_after[k]} }")
_DERIVED_KEYS = ("band", "row_count", "step", "figure_step",
                 "cell", "drop", "plate", "pitch")
for _b in _after_json["1920x1080"]:
    for _k in _DERIVED_KEYS:
        assert _k not in _b, (
            f"the editor wrote a derived value {_k!r} into "
            f"{_b['name']} — the band, the step and the three "
            f"rects are computed every frame and belong in no file")

# ── A COLUMN DRAGGED VERTICALLY IS IGNORED, and SAYS SO ─────
_drag_box = next(b for b in _sd_screen.boxes if b.name == "col_workers")
_drag_before = tuple(_drag_box.ref_rect)
_drag_box.ref_rect = (_drag_before[0], _drag_before[1] + 40,
                      _drag_before[2], _drag_before[3] - 40)
_drag_box.update_layout(_sd_screen.layout)
_chdr.sync_columns(_sd_screen)
assert tuple(_drag_box.ref_rect) == _drag_before, (
    f"a vertical drag survived sync_columns: "
    f"{_drag_box.ref_rect} against {_drag_before}. y and height "
    f"are list_area's, and a drag that is merely ignored is one "
    f"the editor then saves")
_note = _sd_screen.editor_note(_drag_box)
assert _note and "band" in _note, (
    f"editor_note for a column box says {_note!r} — it has to "
    f"report the derived band, because that is what the person "
    f"dragging cannot see")
_name_note = _sd_screen.editor_note(
    next(b for b in _sd_screen.boxes if b.name == "col_name"))
assert _name_note and "not clamped" in _name_note, (
    f"col_name's editor line is {_name_note!r} — it must REPORT "
    f"the lower bound and say that it does not clamp")
assert "namestar.cpp" in _name_note, (
    "the name bound's line does not name where the cap comes from")
# AND THE OVERLAY ASKS THE SCREEN, rather than naming one.
_ov_src = open(os.path.join(_proj, "core", "editor", "overlay.py"),
               encoding="utf-8").read()
assert "editor_note(b)" in _ov_src, (
    "core/editor/overlay.py no longer asks the screen what its "
    "box means")
assert "race_grid" not in _ov_src, (
    "the race_grid special case is back in generic editor code; "
    "Select Race implements `editor_note` now")
_sr = d.screens["select_race"]
_sr.enter(None)
assert _sr.editor_note(_Box({"name": "race_grid",
                             "rect": [0, 0, 10, 10]})) is not None, (
    "Select Race lost the line the overlay used to fish out of it")
assert _sr.editor_note(_Box({"name": "info_panel",
                             "rect": [0, 0, 10, 10]})) is None, (
    "Select Race answers for a box that is not the race grid")
ok("colony list geometry is boxes and a row count (nine tuned "
   "values gone, a save writes nothing derived, a vertical drag "
   "snaps back and the info bar reports what it cannot show)")

# ── ONE COORDINATE FRAME, AND THE CHECK GOES THE WAY THE ────
#    FAULT WENT
#
# Every rect on this screen derives from the `list_area` cutout
# through the same `Layout.rect` call the frame image goes
# through, so the six columns tile that cutout at any window size.
#
# **BOTH STATES, AND THE SECOND ONE IS THE POINT.** A screen
# BUILT at 3440x1440 was correct the whole time this was broken;
# what was wrong was a screen built at 1920x1080 and RESIZED into
# it. `ScreenBase.on_resize` calls `_reload_boxes`, which replaces
# every Box object, and the column table bound at `enter()` went
# on pointing at the discarded ones — so `colonytrack.columns`
# answered the START size's device x while `list_area` and the
# frame answered the new one. Measured 8 September 2026 at all
# four F9 sizes: the columns stayed at 105/408/751/1112/1452/1767
# and `col_scroll`, being the remainder, ran to 1837 px at 4K.
# A fixture that constructs at one size cannot see a resize
# fault; this one walks the path.
#
# SIZES: every key `boxes.json` stores, plus the four `main.py`
# offers on F9 — which is where Data's three came from. The rule
# is asserted, never the numbers, so a fifth size next month
# fails the same way rather than needing a new branch.
_geo_sizes = sorted({
    tuple(int(_v) for _v in _k.split("x"))
    for _k in _sjson.load(open(os.path.join(
        SCREENS_DIR, "colony_summary", "boxes.json"),
        encoding="utf-8"))
    if _k.count("x") == 1
} | {(1920, 1080), (2560, 1440), (3440, 1440), (3840, 2160)})
_geo_keys = {"name", "farmers", "workers", "scientists",
             "building", "scroll"}
_geo_snap = _pv._Snapshot(_pv.COLONIES)
_geo_scr = d.screens["colony_summary"]
_geo_w0, _geo_h0 = app.win_w, app.win_h

def _geo_measure(_w, _h, _how):
    """Assert the rule at one size, in one of the two states."""
    _area = pygame.Rect(*_geo_scr.layout.rect(
        _geo_scr.box_rect("list_area")))
    _chdr.sync_columns(_geo_scr)
    _cfg = _geo_scr._data.get("list", {})
    _c = _ctk.columns(_area, _cfg)
    assert set(_c) == _geo_keys, (
        f"{_how} {_w}x{_h}: columns are {sorted(_c)}")
    _ordered = sorted(_c.values())
    # TILE EXACTLY: first edge is the cutout's, every column's
    # right edge IS its neighbour's left, last edge is the
    # cutout's. No gap and no overlap, at any scale.
    assert _ordered[0][0] == _area.x, (
        f"{_how} {_w}x{_h}: the list starts at {_ordered[0][0]} "
        f"and the cutout at {_area.x} — a column is a fraction "
        f"of list_area, not a position in the window")
    for _i, (_cx, _cw) in enumerate(_ordered[:-1]):
        assert _cx + _cw == _ordered[_i + 1][0], (
            f"{_how} {_w}x{_h}: column {_i} ends at {_cx + _cw} "
            f"and the next starts at {_ordered[_i + 1][0]}")
    assert _ordered[-1][0] + _ordered[-1][1] == _area.right, (
        f"{_how} {_w}x{_h}: the columns end at "
        f"{_ordered[-1][0] + _ordered[-1][1]} and the cutout at "
        f"{_area.right} — the last column is not a remainder to "
        f"absorb a mismatch")
    # AND EVERY COLUMN LIES INSIDE IT. Tiling and containment are
    # not the same claim: six columns can tile a span that has
    # itself slid off the cutout, which is exactly what the
    # ultrawide screenshot shows.
    for _k, (_cx, _cw) in _c.items():
        assert _area.x <= _cx and _cx + _cw <= _area.right, (
            f"{_how} {_w}x{_h}: the {_k} column "
            f"({_cx}..{_cx + _cw}) is outside list_area "
            f"({_area.x}..{_area.right})")
    # THE NAME BLOCK LIES INSIDE THE NAME CELL. `name_rect` is
    # the drop target and the cell; the block is drawn into it
    # with the frame inset applied to the left edge only.
    _rows_g = _geo_scr._rows
    assert _rows_g, f"{_how} {_w}x{_h}: no rows to measure"
    _nr = _ctk.name_rect(_area, _cfg, _geo_scr.layout.scale,
                         _rows_g[0])
    _ncx, _ncw = _c["name"]
    assert _nr is not None and _ncx <= _nr.x and \
        _nr.x + _nr.width <= _ncx + _ncw, (
            f"{_how} {_w}x{_h}: the name block {_nr} is not "
            f"inside the NAME cell ({_ncx}..{_ncx + _ncw})")

for _gw, _gh in _geo_sizes:
    # STATE 1 — built at the size.
    _geo_scr.exit()
    app.win_w, app.win_h = _gw, _gh
    app.layout.update(_gw, _gh)
    _geo_scr.enter(_geo_snap)
    _geo_scr.update(_geo_snap)
    _geo_measure(_gw, _gh, "built at")
    # STATE 2 — built at 1920x1080, then resized into the size,
    # which is what the app itself does: `settings.json` starts
    # every session at 1920x1080 and F9 resizes from there.
    _geo_scr.exit()
    app.win_w, app.win_h = 1920, 1080
    app.layout.update(1920, 1080)
    _geo_scr.enter(_geo_snap)
    _geo_scr.update(_geo_snap)
    app.win_w, app.win_h = _gw, _gh
    app.layout.update(_gw, _gh)
    _geo_scr.on_resize()
    _geo_measure(_gw, _gh, "resized into")
# AND THE TABLE IS THE SCREEN'S OWN BOXES, not six objects that
# merely look like them. This is the invariant the symptom came
# from, and it is cheap to state directly.
_geo_tbl = _geo_scr._data.get("list", {}).get(_ctk.COLUMNS_KEY) or ()
assert _geo_tbl and all(
    any(_b is _sb for _sb in _geo_scr.boxes) for _k, _b in _geo_tbl), (
    "the bound column table holds Box objects the screen no "
    "longer has — a device coordinate with a lifetime longer "
    "than the window it was computed for")
_geo_scr.exit()
app.win_w, app.win_h = _geo_w0, _geo_h0
app.layout.update(_geo_w0, _geo_h0)
_geo_scr.enter(_geo_snap)
_geo_scr.update(_geo_snap)
ok(f"colony columns tile list_area at {len(_geo_sizes)} window "
   f"sizes, built AND resized into (one coordinate frame: every "
   f"rect derives from the cutout, not from the window)")
