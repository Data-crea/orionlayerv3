# smoke-suite area: fleets
#
# Part of the OrionLayer smoke suite — 046_fleets_the_fleets_v4_frame_32_holes.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (92 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 3 check(s) it holds:
#   - the Fleets v4 frame: 32 holes, every one named by the rule the tool uses, every box equal to its
#   - the Fleets reshape (work order 153): the segments tile both axes and move neither, every hole ca
#   - the six Fleets boxes with no hole are all present at both resolutions, each inside the hole it b


# ── THE FLEETS OPENING IS THE ARTWORK'S, NOT A TYPED NUMBER ─────
#
# Work order 146. **THE FRAME NOW CUTS THIRTY-TWO HOLES** and the
# boxes are derived from them (decision 3), where v3 had ONE
# opening with hand-seated regions inside it. What the old check
# held — one hole, `frame.opening` equal to that hole plus BLEED,
# the image 1920x1080, the Planets master's strut stubs — was all
# about that frame and none of it survives v4. This is the
# replacement, and it holds the thing decision 3 cares about: the
# holes and the boxes still agree, as they do for `map_area`.
import numpy as _fo_np
from PIL import Image as _fo_Image
from screens.fleets import fltgeom as _flg
_fo_png = res.screen_file("fleets", "assets", "frame.png")
assert _fo_png and os.path.exists(_fo_png), "the Fleets frame is gone"
_fo_iw, _fo_ih, _fo_holes = _fhB.find_holes(_fo_png)
_fo_lay = _sjson.load(io.open(os.path.join(
    SCREENS_DIR, "fleets", "layout.json"), encoding="utf-8"))
assert [_fo_iw, _fo_ih] == list(_fo_lay["frame"]["image_size"]), (
    f"the Fleets frame is {_fo_iw}x{_fo_ih} and layout.json says "
    f"{_fo_lay['frame']['image_size']}; `to_ref` scales from that "
    f"number, so the two cannot differ")
assert len(_fo_holes) == 32, (
    f"the Fleets frame cuts {len(_fo_holes)} holes, 32 expected "
    "(1 minimap + 3 arrow bar + 1 text panel + 20 cells + 7 "
    "controls). The naming rule refuses anything else, so this "
    "says the artwork changed")

# 1. EVERY HOLE IS NAMED, and the namer is the one the tool uses.
_fo_named = _fhB.name_holes(_fo_holes, "fleets", (_fo_iw, _fo_ih))
assert len(_fo_named) == 32, sorted(_fo_named)
assert set(_fo_named) == _fhB.RULE_NAMES["fleets"], (
    sorted(set(_fo_named) ^ _fhB.RULE_NAMES["fleets"]))

# 2. HOLES AND BOXES AGREE — the `map_area` rule, for all 32.
_fo_boxes = _sjson.load(io.open(os.path.join(
    SCREENS_DIR, "fleets", "boxes.json"), encoding="utf-8"))
for _fo_res, _fo_list in _fo_boxes.items():
    _fo_by = {b["name"]: b for b in _fo_list}
    for _fo_n, _fo_r in _fo_named.items():
        assert _fo_n in _fo_by, f"{_fo_res}: no box for hole {_fo_n}"
        _fo_want = _fhB.to_ref(_fo_r, _fo_iw, _fo_ih)
        assert _fo_by[_fo_n]["rect"] == _fo_want, (
            f"{_fo_res}: box {_fo_n} is {_fo_by[_fo_n]['rect']} and its "
            f"hole makes {_fo_want}. Run "
            f"`python tools/frame_holes.py screens/fleets/assets/"
            f"frame.png --write` — content would sit off its hole")

# 3. INSIDE A HOLE THE FRAME IS THE BORDER. Not one derived box may
#    wear a skin that draws an outline: the artwork already drew it.
for _fo_res, _fo_list in _fo_boxes.items():
    for _fo_b in _fo_list:
        if _fo_b["name"] not in _fo_named:
            continue
        _fo_skin = (_fo_b.get("style") or {}).get("skin")
        assert _fo_skin == "none", (
            f"{_fo_res}: box {_fo_b['name']} sits in a hole and wears "
            f"skin {_fo_skin!r}; the frame is its border. A MISSING "
            f"style is not enough — core/box.py defaults to 'panel'")

# 4. THE CHAMFER TABLE IS THE ARTWORK'S (decision 36: a hand-copied
#    value needs a checker). Re-derived here from the shipped PNG.
_fo_alpha = _fo_np.array(_fo_Image.open(_fo_png).convert("RGBA"))[:, :, 3]
_fo_T = _fo_alpha < _fhB.ALPHA_LIMIT
for _fo_n, _fo_k in _flg.CONTENT_INSET_SRC.items():
    _fo_x, _fo_y, _fo_w, _fo_h = _fo_named[_fo_n]
    assert _fo_T[_fo_y + _fo_k:_fo_y + _fo_h - _fo_k,
                 _fo_x + _fo_k:_fo_x + _fo_w - _fo_k].all(), (
        f"CONTENT_INSET_SRC[{_fo_n}] = {_fo_k} is not clear of the "
        f"chamfer; content there is covered by the frame, which "
        f"draws last")
    if _fo_k:
        assert not _fo_T[_fo_y + _fo_k - 1:_fo_y + _fo_h - _fo_k + 1,
                         _fo_x + _fo_k - 1:_fo_x + _fo_w - _fo_k + 1] \
            .all(), (
            f"CONTENT_INSET_SRC[{_fo_n}] = {_fo_k} is larger than the "
            f"chamfer needs; it is a measurement, not a margin")
assert tuple(_flg.FRAME_SRC_SIZE) == (_fo_iw, _fo_ih)

# 5. THE FRAME IS AN HD INVENTION and says so where it is used.
_fo_note = _fo_lay["frame"].get("_note", "")
assert "HD INVENTION" in _fo_note, (
    "screens/fleets/layout.json frame._note no longer marks the "
    "frame an HD INVENTION — the native Fleets screen has flat "
    "plates and no such frame (FLEET.LBX 0)")
_fo_geo = io.open(os.path.join(SCREENS_DIR, "fleets", "fltgeom.py"),
                  encoding="utf-8").read()
assert "HD INVENTION" in _fo_geo, (
    "fltgeom lost the HD INVENTION marking for the v4 frame")

ok("the Fleets v4 frame: 32 holes, every one named by the rule the "
   "tool uses, every box equal to its hole plus BLEED at both "
   "resolutions, no box in a hole drawing its own border, the "
   "chamfer table re-derived from the artwork, and the frame "
   "marked an HD INVENTION")

# ── WORK ORDER 153: THE RESHAPE, AND WHAT IT PROMISED NOT TO DO ─
#
# Data accepted a new layout for this screen: the map hole gives
# 195 px of height to the ship panel and 321 px of width to the
# right column. `tools/fleets_frame_reshape.py` is that step, and
# all three of its promises are measurable, so all three are
# measured here rather than described.
import fleets_frame_reshape as _rs

# 1. THE SEGMENTS TILE BOTH AXES AND MOVE NEITHER. `_validate`
#    raises on a gap, an overlap, an empty segment, a band whose
#    lengths do not add up to 3840, or a left column that does not
#    give the right one exactly what it took.
_rs._validate()

# 2. WHAT CAME OUT IS WHAT DATA ASKED FOR — the order's own
#    figures against the SHIPPED frame's alpha, not against the
#    tool that wrote it.
for _rs_n, _rs_want in _rs.TARGET_HOLES.items():
    assert tuple(_fo_named[_rs_n]) == _rs_want, (
        f"{_rs_n} is {tuple(_fo_named[_rs_n])} in the shipped frame "
        f"and fleets_frame_reshape targets {_rs_want}")
_rs_cells = [_fo_named[f"cell_{_i:02d}"] for _i in range(20)]
assert {(_c[2], _c[3]) for _c in _rs_cells} == {_rs.TARGET_CELL_SIZE}, (
    f"the cells are {sorted({(c[2], c[3]) for c in _rs_cells})}, not "
    f"one size {_rs.TARGET_CELL_SIZE} — `name_holes_fleets` finds the "
    f"grid by looking for twenty holes that share a size")
assert tuple(sorted({_c[0] for _c in _rs_cells})) == _rs.TARGET_CELL_X
assert tuple(sorted({_c[1] for _c in _rs_cells})) == _rs.TARGET_CELL_Y
#    and the galaxy is stretched by what it was stretched by
#    before, which is the acceptance criterion in Data's own words
from screens.colony_summary.colonyrows import (
    INSET_SCALE_X as _rs_gx, INSET_SCALE_Y as _rs_gy)
_rs_gal = _rs_gx / _rs_gy
_rs_was = (_rs.SOURCE_MAP_HOLE[0] / _rs.SOURCE_MAP_HOLE[1]) / _rs_gal
_rs_now = (_fo_named["inset_map"][2] / _fo_named["inset_map"][3]) \
    / _rs_gal
assert abs(_rs_now - _rs_was) / _rs_was < 0.001, (
    f"the map hole stretches the galaxy {_rs_now:.5f}x where the hole "
    f"before work order 153 stretched it {_rs_was:.5f}x; Data's "
    f"acceptance is that this does not change")

# 3. NO STRETCHED CORNERS — ANYWHERE, not only in the right
#    column. `anchor_pairs` is every region the reshape claims to
#    TRANSLATE, and every corner, chamfer, rivet, bracket and
#    V-notch of this frame is inside one of them. The comparison
#    is against the unlit source, so it goes past the reshape
#    rather than through it; solid pixels only, because the cut
#    zeroes the RGB under a hole on purpose.
import fleets_frame_build as _rsb
_rs_src = _fo_np.asarray(_rsb._unlit(
    _fo_Image.open(_rsb.SRC).convert("RGB")))
_rs_out = _fo_np.asarray(_fo_Image.open(_fo_png).convert("RGBA"))
_rs_seen = 0
for _sx, _sy, _w, _h, _dx, _dy in _rs.anchor_pairs():
    _a = _rs_src[_sy:_sy + _h, _sx:_sx + _w].astype(int)
    _b = _rs_out[_sy + _dy:_sy + _dy + _h,
                 _sx + _dx:_sx + _dx + _w]
    _solid = _b[:, :, 3] > 200
    _bad = (_fo_np.abs(_a - _b[:, :, :3].astype(int)).max(axis=2) > 0) \
        & _solid
    _rs_seen += int(_solid.sum())
    assert not _bad.any(), (
        f"the anchor at {(_sx, _sy, _w, _h)} moved by {(_dx, _dy)} is "
        f"not a copy: {int(_bad.any(axis=1).sum())} row(s) differ, the "
        f"first at source y {_sy + int(_fo_np.where(_bad.any(axis=1))[0][0])}"
        f". Something resampled a region the reshape calls an anchor")
assert _rs_seen > 1_500_000, (
    f"only {_rs_seen} solid pixels were compared; the anchors used to "
    f"cover 1.89 million and a shrunken set proves less than it says")
del _rs_src, _rs_out

ok("the Fleets reshape (work order 153): the segments tile both "
   "axes and move neither, every hole came out at Data's figure, "
   "the twenty cells share one size, the galaxy stretch is "
   "unchanged, and every anchor — every corner, chamfer and "
   f"bracket, {_rs_seen} solid pixels — is a copy and not a "
   "resample")

# ── THE SIX BOXES WITH NO HOLE FOLLOW THE HOLES ────────────────
#
# Work order 153. Thirty-two boxes are cutouts and are held to
# their holes above. Six are not, and before 153 they were
# remembered rectangles: when the frame changed shape every one of
# them stayed over the old layout. `screens/fleets/fltplaced.py`
# makes each a RULE against a hole; this is the checker that rule
# needs, and it is what makes a future reshape move them.
#
# **WHAT IS HELD IS CONTAINMENT, NOT EQUALITY** — Data,
# 20 September 2026. Until then this demanded that each of the six
# EQUAL what `fltplaced` computes, which turned six F5-editable
# boxes into locked ones behind everybody's back: one nudge of
# `ship_panel_text` in the editor, one pixel at 2560x1440, and the
# suite went red over a box that was never meant to be pinned.
# `fltgeom`'s own docstring and decision 14 say the seat is a
# starting point and not a cage, so the seeder seeds and the check
# holds the 151 lesson and nothing more.
from screens.fleets import fltplaced as _fpl
for _fpl_res, _fpl_list in _fo_boxes.items():
    _fpl_by = {b["name"]: b["rect"] for b in _fpl_list if "rect" in b}
    #  1. all six are there — a placed box that vanishes takes its
    #     content with it and nothing else would notice
    for _fpl_n in _fpl.NAMES:
        assert _fpl_n in _fpl_by, (
            f"{_fpl_res}: no {_fpl_n} box. Run `python "
            f"tools/fleets_place_boxes.py --write`")
    #  2. THE 151 LESSON, against the file's own rects and not
    #     against the seed: a box outside its hole is drawn and
    #     then covered by the frame, which renders last
    _fpl_bad = _fpl.contained(_fpl_by, {_fpl_n: _fpl_by[_fpl_n]
                                        for _fpl_n in _fpl.NAMES})
    assert not _fpl_bad, (
        f"{_fpl_res}: " + "; ".join(_fpl_bad) + ". A box outside "
        f"its hole is painted over by the frame — move it back in "
        f"F5, or re-seed with `python "
        f"tools/fleets_place_boxes.py --write`")
    #  3. and the SEED itself is still sound, so a reshape cannot
    #     leave the tool producing something the editor would have
    #     to repair by hand
    _fpl_seed_bad = _fpl.contained(_fpl_by)
    assert not _fpl_seed_bad, (
        f"{_fpl_res}: the seed `fltplaced.placed` computes would "
        f"not fit: " + "; ".join(_fpl_seed_bad))
    assert set(_fpl.NAMES) & set(_fhB.RULE_NAMES["fleets"]) == set(), (
        "a placed box took a cutout's name; the editor would lock it")

ok("the six Fleets boxes with no hole are all present at both "
   "resolutions, each inside the hole it belongs to or holding "
   "the ones it is the union of — wherever F5 left it — the seed "
   "they came from still fits, and none of them is a cutout name")
