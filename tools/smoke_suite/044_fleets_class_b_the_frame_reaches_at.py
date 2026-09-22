# smoke-suite area: fleets
#
# Part of the OrionLayer smoke suite — 044_fleets_class_b_the_frame_reaches_at.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (92 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 1 check(s) it holds:
#   - class B: the frame reaches at most px into any of cutouts


# ── CLASS B: how far the ARTWORK reaches into each cutout ──
# Content clipped to a cutout — the galaxy map's stars and star
# names — cannot be kept off the rim by an inset without cropping
# the content, so what is budgeted here is the FRAME, not the
# residue. If a redrawn frame grows a fatter rim, this fails and
# the clipped content stops silently losing more of itself.
#
# MEASURED ON THE SOURCE IMAGE, which is the artwork. At display
# sizes the bilinear rescale widens the rim's alpha ramp by one
# to three reference px, and that is a property of the resampler
# rather than of the drawing.
#
# CORNERS EXCLUDED, and `title` excluded outright: it is not a
# rectangle. Its hole is angled, so the bounding box find_holes
# returns contains real frame at both ends — 14 px on the colony
# summary, 29 on the galaxy map — and measuring a straight-edge
# intrusion there measures the shape, not the rim.
# Today's worst is 2, on the top edge of `list_area` and
# `galaxy_inset`; every other straight edge is 0 or 1. The
# budget IS the measurement, so any thickening fails.
_CLASS_B_BUDGET = 2
_CORNER_TRIM = 0.18
import frame_holes as _fhB

def _intrusion(alpha, rect):
    _x, _y, _w, _h = rect
    _x0, _y0 = max(0, _x), max(0, _y)
    _x1 = min(alpha.shape[1], _x + _w)
    _y1 = min(alpha.shape[0], _y + _h)
    if _x1 - _x0 < 8 or _y1 - _y0 < 8:
        return None
    _iy = int((_y1 - _y0) * _CORNER_TRIM)
    _ix = int((_x1 - _x0) * _CORNER_TRIM)
    _out = []
    # EVERY ROW AND EVERY COLUMN. It used to step `edge // 40`,
    # which on the Fleets opening is a column every 44 px — wide
    # enough to walk straight over a 27 px strut stub, and it did:
    # work order 136 C measured T2 B1 with the stride against T4 B4
    # without it. "A check with a scope has a blind spot exactly
    # the size of that scope", the scope here being a sampling
    # rate. Measured 19 September 2026 before the stride went:
    # colony_summary and galaxy_map read the same either way (worst
    # 1 and 0), so nothing was loosened to pay for it.
    for _cs, _horiz in ((range(_y0 + _iy, _y1 - _iy), True),
                        (range(_x0 + _ix, _x1 - _ix), False)):
        _lo = _hi = 0
        for _c in _cs:
            _line = (alpha[_c, _x0:_x1] if _horiz
                     else alpha[_y0:_y1, _c])
            _n = 0
            while _n < len(_line) and _line[_n] >= 16:
                _n += 1
            _lo = max(_lo, _n)
            _n = 0
            while _n < len(_line) and _line[len(_line) - 1 - _n] >= 16:
                _n += 1
            _hi = max(_hi, _n)
        _out += [_lo, _hi]
    return _out

_b_worst = {}
for _name in _FRAME_SCREENS_B:
    # ONE FILE PER SCREEN since Phase B — every screen wears its
    # own `assets/frame.png` and none of them has a switch. This
    # was the 1080p colony PLATE by path, hardcoded, and measured
    # glyphs against artwork nobody blitted.
    _fpng = res.screen_file(_name, "assets", "frame.png")
    if not _fpng or not os.path.exists(_fpng):
        continue
    _iw, _ih, _holes = _fhB.find_holes(_fpng)
    # A SCREEN WITH NO NAMING RULE HAS ONE HOLE, and that is a
    # state rather than a gap: decision 3 derives cutout boxes from
    # a frame's holes and `fleets` has none to derive — one
    # opening, hand-placed regions inside it
    # (screens/fleets/layout.json `_no_cutouts_note`). Naming it
    # here rather than adding a `frame_holes` rule keeps `--write`
    # unable to touch that screen, which is what the note promises.
    if _name in _fhB.RULES:
        _named = _fhB.name_holes(_holes, _name, (_iw, _ih))
    else:
        assert len(_holes) == 1, (
            f"{_name} has no frame_holes rule and cuts "
            f"{len(_holes)} holes; a multi-hole frame needs a rule "
            f"before it can be measured hole by hole")
        _named = {"opening": _holes[0]}
    _al = _np.array(Image.open(_fpng).convert("RGBA"))[:, :, 3]
    for _cn, _r in _named.items():
        if _cn == "title":
            continue
        _v = _intrusion(_al, _r)
        assert _v is not None, (_name, _cn)
        _b_worst[(_name, _cn)] = max(_v)
        # **A FRAME MAY DECLARE ITS CHAMFER INSTEAD.** The budget
        # of 2 is the measurement of frames whose holes are square:
        # any thickening of their rim fails. The Fleets v4 frame's
        # holes are chamfered on purpose and the chamfer is LONG —
        # 30 of the ship panel's 142 rows, so `_CORNER_TRIM`'s 18 %
        # does not clear it and this reads 8 at what it takes for a
        # straight edge. That is the artwork, not a rim.
        #
        # So a screen that has MEASURED its chamfer and insets its
        # content by it is held to that number instead, which is a
        # stronger statement than the flat budget: the intrusion
        # must fit inside the inset the screen actually uses. The
        # inset itself is checked against the artwork separately
        # (the Fleets v4 frame block), so neither number can drift.
        _b_allow = _CLASS_B_BUDGET
        if _name == "fleets":
            from screens.fleets import fltgeom as _b_flg
            _b_allow = _b_flg.CONTENT_INSET_SRC.get(_cn, _CLASS_B_BUDGET)
            assert _b_allow >= max(_v), (
                f"fleets/{_cn}: the frame reaches {max(_v)} px into "
                f"this hole at a straight edge but CONTENT_INSET_SRC "
                f"says {_b_allow}; content inset by the declared "
                f"number would still be covered")
        assert max(_v) <= _b_allow, (
            f"{_name}/{_cn}: the frame's opaque alpha reaches "
            f"{max(_v)} source px into this cutout at a straight "
            f"edge (L{_v[0]} R{_v[1]} T{_v[2]} B{_v[3]}), over the "
            f"budget of {_CLASS_B_BUDGET}. Content clipped to this "
            f"hole — the galaxy map's stars and names — loses that "
            f"much of itself with no inset able to help. Either the "
            f"artwork grew a rim or find_holes' bounding box is no "
            f"longer the hole's shape")
# DERIVED FROM THE SCREENS ACTUALLY MEASURED, not a literal. It
# was 17 — the galaxy map's ten less `title` plus the Stage A3
# plate's eight — and a literal was wrong twice in one day. A
# floor exists so a frame that stops cutting holes cannot pass by
# measuring nothing, which is a rule about EACH screen present
# and not about a total.
# A WINDOW WITH NO HOLE IS NOT A CUTOUT TO MEASURE. The colony
# header is a strip of the list's hole (`_windows_without_a_hole`)
# and never appears in the namer's answer, so counting it would
# ask this block for a rectangle that does not exist.
# THROUGH `BOX_NAME`, because `RULE_NAMES` is in the BOX's
# spelling and the reference is in its own: `return_button` there
# is `return` here, and subtracting the reference's word left
# RETURN in the floor with no hole to measure — one short, every
# run, the day it stopped having one.
_b_nohole = {_cpl.BOX_NAME.get(_n, _n)
             for _n in _lr.get("_windows_without_a_hole", ())}
_b_floor = sum(len(_fh_mod.RULE_NAMES[_n] - {"title"} - _b_nohole)
               if _n in _fh_mod.RULES else 1
               for _n in _FRAME_SCREENS_B)
assert len(_b_worst) >= _b_floor, (
    f"{len(_b_worst)} cutouts measured, {_b_floor} expected from "
    f"{list(_FRAME_SCREENS_B)}")
ok(f"class B: the frame reaches at most {_CLASS_B_BUDGET} px into "
   f"any of {len(_b_worst)} cutouts")
