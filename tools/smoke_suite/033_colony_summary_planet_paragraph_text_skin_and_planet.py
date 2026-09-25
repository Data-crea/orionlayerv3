# smoke-suite area: colony_summary
#
# Part of the OrionLayer smoke suite — 033_colony_summary_planet_paragraph_text_skin_and_planet.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (93 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 4 check(s) it holds:
#   - planet_paragraph (text skin) and planet_disc sit inside planet_info without overlapping, the dis
#   - an F5 save round trip leaves boxes.json and layout_reference.json unchanged, writes no text, col
#   - every climate has a surface tile (), each at the size the tool cuts and rebuilt byte for byte, a
#   - the lower band is three holes matched to planet_info, colony_panel and galaxy_inset with no spar


# ── THE PARAGRAPH AND THE DISC ARE BOXES — brief 95 Part C ────
# At every resolution boxes.json declares planet_info for: both
# boxes exist, the paragraph is a `text`-skin box, both sit inside
# planet_info and do not overlap, the disc drawn is the climate's
# sprite fitted into the disc box, and the paragraph's string and
# colour are the box's runtime `text` / `text_color` — red for
# negative growth, for the whole paragraph.
from screens.colony_summary import colonyplanets as _px_pl
_px_boxes = _sjson.load(open(os.path.join(
    SCREENS_DIR, "colony_summary", "boxes.json"), encoding="utf-8"))
_px_res = sorted(_k for _k, _v in _px_boxes.items()
                 if isinstance(_v, list)
                 and any(_b.get("name") == "planet_info" for _b in _v))
assert _px_res, "no resolution declares planet_info"
for _px_spec in _px_res:
    _px_names = {_b["name"]: _b for _b in _px_boxes[_px_spec]}
    assert "planet_disc" in _px_names and "planet_paragraph" in _px_names, (
        f"{_px_spec}: boxes.json lacks planet_disc or planet_paragraph")
    assert _px_names["planet_paragraph"].get("style", {}).get(
        "skin") == "text", (
        f"{_px_spec}: planet_paragraph is not a text-skin box "
        f"(decision 37)")
    _px_W, _px_H = (int(_v) for _v in _px_spec.split("x"))
    _px_app, _px_scr = _plv.build_screen(_px_W, _px_H)
    _px_app.dispatcher.switch_to("colony_summary")
    _px_scr.enter(None)
    _px_scr.update(_plv._Snapshot(_plv.COLONIES))
    _px_info = pygame.Rect(*_px_scr.layout.rect(
        _px_scr.box_rect("planet_info")))
    _px_t = pygame.Rect(*_px_scr.layout.rect(
        _px_scr.box_rect("planet_paragraph")))
    _px_d = pygame.Rect(*_px_scr.layout.rect(
        _px_scr.box_rect("planet_disc")))
    assert _px_info.contains(_px_t) and _px_info.contains(_px_d), (
        f"{_px_spec}: paragraph {_px_t} or disc {_px_d} is not "
        f"inside planet_info {_px_info}")
    assert not _px_t.colliderect(_px_d), (
        f"{_px_spec}: the paragraph {_px_t} overlaps the disc {_px_d}")
    _px_surf = pygame.Surface((_px_W, _px_H))
    _px_surf.fill((0, 0, 0))
    _px_scr.render(_px_surf)
    _px_row = _px_scr.selected_row()
    _px_tb = next(_b for _b in _px_scr.boxes
                  if _b.name == "planet_paragraph")
    assert _px_tb.text == _co.fill_template(
        _ocfg["info_paragraph"],
        _co.row_values(_px_row, _words, _climates)), (
        f"{_px_spec}: planet_paragraph's Box.text is {_px_tb.text!r}")
    _px_side = min(_px_d.w, _px_d.h)
    _px_spr = _px_pl.set_for(_px_scr, _px_side).get(_px_row["climate"])
    _px_x = _px_d.x + (_px_d.w - _px_spr.get_width()) // 2
    _px_y = _px_d.y + (_px_d.h - _px_spr.get_height()) // 2
    _px_got = _np.array(pygame.surfarray.array3d(_px_surf.subsurface(
        pygame.Rect(_px_x, _px_y, _px_spr.get_width(),
                    _px_spr.get_height()))))
    _px_ref = _np.array(pygame.surfarray.array3d(_px_spr))
    _px_op = _np.array(pygame.surfarray.array_alpha(_px_spr)) == 255
    assert _px_op.sum() > 100 and (
        _px_got[_px_op] == _px_ref[_px_op]).all(), (
        f"{_px_spec}: the disc drawn in planet_disc {_px_d} is not "
        f"the climate's sprite at its shorter side")
    # THE PARAGRAPH'S INK IS INSIDE ITS BOX.
    _px_s2 = pygame.Surface((_px_W, _px_H))
    _px_s2.fill((0, 0, 0))
    _co.render_info(_px_s2, _px_row, _px_t, _ocfg, _words, _climates,
                    _px_scr.layout, _px_scr.style, text_box=_px_tb)
    _px_ink = pygame.surfarray.array3d(_px_s2).sum(axis=2) > 0
    _px_xs, _px_ys = _np.nonzero(_px_ink)
    assert len(_px_xs) and _px_t.collidepoint(int(_px_xs.min()),
                                              int(_px_ys.min())) \
        and _px_xs.max() < _px_t.right and _px_ys.max() < _px_t.bottom, (
        f"{_px_spec}: the paragraph's ink leaves planet_paragraph {_px_t}")
    assert _px_tb.text_color == _co.VALUE_COLOR
    _co.render_info(_px_s2, dict(_px_row, growth=-5), _px_t, _ocfg,
                    _words, _climates, _px_scr.layout, _px_scr.style,
                    text_box=_px_tb)
    assert _px_tb.text_color == _co.SHORTAGE_COLOR, (
        f"{_px_spec}: negative growth did not turn the paragraph box "
        f"red through Box.text_color")
ok(f"planet_paragraph (text skin) and planet_disc sit inside "
   f"planet_info without overlapping, the disc is the climate's "
   f"sprite fitted to its box, and the paragraph is Box.text in "
   f"Box.text_color ({', '.join(_px_res)})")

# ── …AND AN EDITOR ROUND TRIP WRITES NOTHING IT SHOULD NOT ────
# Load, render (which fills Box.text), save exactly as F5's `S`
# does — `save_boxes` plus the screen's `save_geometry` — into a
# scratch copy, and diff. boxes.json must come back equal, with no
# text, colour, rect or image path on either box; the reference
# must come back equal; and a DRAG of the disc must land in
# `planet_info_parts` and nowhere else.
import shutil as _rt_sh
import tempfile as _rt_tf
from core.box import save_boxes as _rt_save
_rt_src = os.path.join(SCREENS_DIR, "colony_summary")
with _rt_tf.TemporaryDirectory() as _rt_tmp:
    for _rt_f in ("boxes.json", "layout_reference.json"):
        _rt_sh.copy(os.path.join(_rt_src, _rt_f), _rt_tmp)
    for _rt_spec in _px_res:
        _rt_W, _rt_H = (int(_v) for _v in _rt_spec.split("x"))
        _rt_app, _rt_scr = _plv.build_screen(_rt_W, _rt_H)
        _rt_app.dispatcher.switch_to("colony_summary")
        _rt_scr.enter(None)
        _rt_scr.update(_plv._Snapshot(_plv.COLONIES))
        _rt_s = pygame.Surface((_rt_W, _rt_H))
        _rt_scr.render(_rt_s)
        assert next(_b for _b in _rt_scr.boxes
                    if _b.name == "planet_paragraph").text, (
            "the render did not fill planet_paragraph's Box.text, so "
            "the round trip would prove nothing")
        _rt_scr._screen_dir = _rt_tmp
        _rt_save(_rt_tmp, _rt_scr.boxes, _rt_W, _rt_H)
        assert _rt_scr.save_geometry() == [], (
            f"{_rt_spec}: an unmoved save rewrote the reference")
    _rt_before = _sjson.load(open(os.path.join(_rt_src, "boxes.json"),
                                  encoding="utf-8"))
    _rt_after = _sjson.load(open(os.path.join(_rt_tmp, "boxes.json"),
                                 encoding="utf-8"))
    assert _rt_after == _rt_before, (
        "an editor save changed boxes.json without a drag")
    for _rt_spec, _rt_list in _rt_after.items():
        for _rt_b in _rt_list:
            if _rt_b["name"] not in ("planet_disc", "planet_paragraph",
                                     "planet_name", "planet_surface"):
                continue
            # KEYS, not substrings: the paragraph's own skin is the
            # VALUE "text", which is exactly what it should carry.
            _rt_keys = set(_rt_b) | set(_rt_b.get("style", {}))
            _rt_bad = _rt_keys & {"text", "text_color", "rect",
                                  "image", "asset", "path"}
            assert not _rt_bad, (
                f"{_rt_spec}/{_rt_b['name']} carries {sorted(_rt_bad)} "
                f"in boxes.json after a save: {_rt_b}")
            assert ".png" not in _sjson.dumps(_rt_b), (
                f"{_rt_spec}/{_rt_b['name']} names an image file in "
                f"boxes.json after a save: {_rt_b}")
    assert _sjson.load(open(os.path.join(
        _rt_tmp, "layout_reference.json"), encoding="utf-8")) == \
        _sjson.load(open(os.path.join(
            _rt_src, "layout_reference.json"), encoding="utf-8")), (
        "an editor save changed layout_reference.json without a drag")
    # THE DRAG: ten reference px right, then save.
    _rt_disc = next(_b for _b in _rt_scr.boxes if _b.name == "planet_disc")
    _rt_x, _rt_y, _rt_w, _rt_h = _rt_disc.ref_rect
    _rt_disc.ref_rect = (_rt_x + 10, _rt_y, _rt_w, _rt_h)
    _rt_wrote = _rt_scr.save_geometry()
    assert _rt_wrote == [("planet_disc", [_rt_x + 10, _rt_y, _rt_w, _rt_h])], (
        f"a dragged disc wrote {_rt_wrote}")
    _rt_ref = _sjson.load(open(os.path.join(
        _rt_tmp, "layout_reference.json"), encoding="utf-8"))
    assert _cpl.all_rects(_rt_ref)["planet_disc"] == [
        _rt_x + 10, _rt_y, _rt_w, _rt_h], (
        "the dragged disc does not come back from the reference")
ok("an F5 save round trip leaves boxes.json and layout_reference.json "
   "unchanged, writes no text, colour, rect or image path for the two "
   "planet_info boxes, and a dragged disc lands in planet_info_parts")

# ── THE PLANET SURFACES — brief 97, decision 58 ───────────────
# Every climate the enum has a tile for, as a RULE over the names
# the disc uses; the ten files exist after setup at the size the
# tool's rule cuts; regenerating reproduces them byte for byte
# (decision 40); a root with no tiles is a state and not a crash
# (decision 38); and the markings — HD EXTENSION for the picture,
# AI-generated artwork with no claim — are at every home.
import importlib.util as _sf_ilu
import subprocess as _sf_sp
import tempfile as _sf_tf
from screens.colony_summary import colonysurfaces as _sf
from screens.colony_summary import colonyplanets as _sf_pl
_sf_root = os.path.dirname(SCREENS_DIR)
_sf_tool = os.path.join(_sf_root, "tools", "make_surface_tiles.py")
_sf_spec = _sf_ilu.spec_from_file_location("_sf_tool_mod", _sf_tool)
_sf_mod = _sf_ilu.module_from_spec(_sf_spec)
_sf_spec.loader.exec_module(_sf_mod)
_sf_rects = _sf_mod.tile_rects()
_sf_ids = [_i for _i in range(64) if _sf_pl.name_for(_i) is not None]
assert _sf_ids == list(range(len(_sf_pl.NAMES))) and \
    set(_sf_rects) == set(_sf_pl.NAMES), (
    f"the climates with a name are {_sf_ids} and the tool cuts "
    f"{sorted(_sf_rects)} — every climate needs exactly one tile")
_sf_dir = os.path.join(SCREENS_DIR, "colony_summary", _sf.SURFACE_DIR)
for _sf_id in _sf_ids:
    _sf_name = _sf_pl.name_for(_sf_id)
    _sf_path = os.path.join(_sf_dir, f"{_sf_name}.png")
    assert os.path.exists(_sf_path), (
        f"no surface tile for climate {_sf_id} ({_sf_name}) at "
        f"{_sf_path} — run `python tools/setup.py`")
    assert _pl_Image.open(_sf_path).size == tuple(_sf_rects[_sf_name][2:]), (
        f"{_sf_name}.png is {_pl_Image.open(_sf_path).size}; the tool "
        f"cuts {_sf_rects[_sf_name][2:]} and scales nothing")
with _sf_tf.TemporaryDirectory() as _sf_tmp:
    _sf_run = _sf_sp.run([sys.executable, _sf_tool, "--out", _sf_tmp],
                         capture_output=True, text=True)
    assert _sf_run.returncode == 0, _sf_run.stderr[-400:]
    for _sf_name in _sf_pl.NAMES:
        with open(os.path.join(_sf_dir, f"{_sf_name}.png"), "rb") as _fh:
            _sf_a = _fh.read()
        with open(os.path.join(_sf_tmp, f"{_sf_name}.png"), "rb") as _fh:
            _sf_b = _fh.read()
        assert _sf_a == _sf_b, (
            f"{_sf_name}.png does not regenerate byte for byte "
            f"(decision 40)")
    _sf_empty = os.path.join(_sf_tmp, "no_tiles_here")
    os.makedirs(_sf_empty)
    _sf_none = _sf.SurfaceSet(app.res, root=_sf_empty)
    assert _sf_none.state == "missing" and _sf_none.get(8) is None, (
        "a root without tiles must be the 'missing' state and draw "
        "nothing, not raise (decision 38)")
assert _sf.SurfaceSet(app.res).state == "ok"
for _sf_home, _sf_path, _sf_words in (
        ("colonysurfaces.py", os.path.join(
            SCREENS_DIR, "colony_summary", "colonysurfaces.py"),
         ("HD EXTENSION, decision 58", "DEVIATION", "AI-GENERATED")),
        ("tools/make_surface_tiles.py", _sf_tool,
         ("AI-GENERATED", "ChatGPT", "LICENCE", "decision 40")),
        ("LICENSE", os.path.join(_sf_root, "LICENSE"),
         ("planet_surfaces.png", "ChatGPT", "No copyright is")),
        ("doc/v3_fundament.md", os.path.join(
            _sf_root, "doc", "v3_fundament.md"),
         ("**58.", "HD EXTENSION")),
        ("v3_projektstatus.md", os.path.join(
            _sf_root, "v3_projektstatus.md"),
         ("decision 58", "HD EXTENSION"))):
    _sf_text = read_doc(_sf_path)
    for _sf_w in _sf_words:
        assert _sf_w in _sf_text, (
            f"{_sf_home} no longer carries {_sf_w!r} — the surface "
            f"picture's marking and the artwork's origin live at "
            f"every home")
ok(f"every climate has a surface tile ({len(_sf_ids)}), each at the "
   f"size the tool cuts and rebuilt byte for byte, a missing set is a "
   f"state, and the HD EXTENSION / AI-artwork marking is at every home")

# ── THREE BOTTOM WINDOWS — brief 97, Stop 3 ───────────────────
# The frame's lower band is three holes and the reference names
# three windows; the match claims every hole (no spare since the
# title cartouche closed); planet_output, planet_surface and
# empire_stats are PARTS inside colony_panel and not cutouts; and
# nothing in frame_holes still explains a spare by the cartouche.
import json as _b3_json
_b3_png = os.path.join(SCREENS_DIR, "colony_summary", "assets",
                       "frame.png")
_b3_w, _b3_h, _b3_holes = fh.find_holes(_b3_png)
_b3_named = fh.name_holes(_b3_holes, "colony_summary", (_b3_w, _b3_h))
# SINCE WORK ORDER 170 THE SORT ROW AND RETURN HAVE LEFT THEIR HOLES: the
# frame is not drawn (decision 71) and the row sits on the bottom edge,
# declared in `_windows_without_a_hole`. So the holes no window claims
# are exactly the old bottom row — one per declared window that is not
# the header — and nothing else in the frame may go unclaimed.
_b3_lr = _b3_json.load(open(os.path.join(
    SCREENS_DIR, "colony_summary", "layout_reference.json")))
_b3_left = [_n for _n in _b3_lr.get("_windows_without_a_hole", ())
            if _n != "header"]
assert len(fh.SPARE_HOLES) == len(_b3_left) and all(
    _h[1] > 0.85 * _b3_h for _h in fh.SPARE_HOLES), (
    f"the frame has holes no window claims outside the old sort row: "
    f"{fh.SPARE_HOLES}, declared hole-less {_b3_left}")
assert len(fh.BAND_KEYS) == 3 and set(fh.BAND_KEYS) <= set(_b3_named), (
    f"the band keys {fh.BAND_KEYS} are not three matched windows")
_b3_band_row = next(_row for _row in fh._rows(_b3_holes)
                    if _b3_named["colony_panel"] in
                    [list(_h) for _h in _row])
assert len(_b3_band_row) == 3, (
    f"the lower band row has {len(_b3_band_row)} holes; Data's frame "
    f"cuts three")
_b3_ref = _b3_json.load(open(os.path.join(
    SCREENS_DIR, "colony_summary", "layout_reference.json"),
    encoding="utf-8"))
_b3_win = pygame.Rect(*_b3_ref["colony_panel"])
for _b3_part in ("planet_output", "planet_surface", "empire_stats"):
    _b3_r = pygame.Rect(*_b3_ref["colony_panel_parts"][_b3_part])
    assert _b3_win.contains(_b3_r), (
        f"{_b3_part} {_b3_r} is not inside colony_panel {_b3_win}")
    assert _b3_part not in fh.RULE_NAMES["colony_summary"], (
        f"{_b3_part} is still a cutout name in frame_holes")
_b3_src = open(fh.__file__, encoding="utf-8").read()
assert "pre-Stage-4 title cartouche" not in _b3_src, (
    "frame_holes.py still explains a spare hole by the title "
    "cartouche Data's frame closed")
ok("the lower band is three holes matched to planet_info, colony_panel "
   "and galaxy_inset with no spare hole, and planet_output, "
   "planet_surface and empire_stats sit inside colony_panel as parts")
