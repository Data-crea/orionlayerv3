# smoke-suite area: colony_summary
#
# Part of the OrionLayer smoke suite — 013_colony_summary_colony_summary_sort_keys_seven_five.py.
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
#   - colony summary sort keys (seven, five descending, case-insensitive name, no toggle, ties in inpu


# ── The colony list ──
# Built against a synthetic snapshot, so the check runs headless
# and does not depend on somebody's savegame — a test that reads
# the user's disk answers differently for the user.
#
# The rules, not the instance: a row shows "No Farming" exactly
# when its colony's max_farms is 0; the three job counts add up
# to the population; and the bar never draws a square past its
# own end, which is what keeps "counting squares counts pops"
# true when a deviation makes the computed maximum too small.
from screens.colony_summary import colonylist as _cl
from screens.colony_summary import colonyrows as _cr
from core.structs import colony as _colsp, star as _starsp

def _mk_colony(owner, planet, pops, jobs, max_farms, climate):
    b = bytearray(361)
    b[0] = owner & 0xFF
    b[2:4] = _s.pack("<h", planet)
    b[10] = pops
    i = 0
    for prof, n in enumerate(jobs):
        for _ in range(n):
            b[12 + 4 * i:16 + 4 * i] = _s.pack("<I", (prof & 3) << 7)
            i += 1
    b[224] = max_farms
    b[226] = climate
    return bytes(b)

def _mk_planet(colony_index, star_index, orbit, size, climate):
    b = bytearray(18)
    b[0:2] = _s.pack("<h", colony_index)
    b[2:4] = _s.pack("<h", star_index)
    b[4] = orbit
    b[6] = size
    b[9] = climate
    return bytes(b)

def _mk_star(name, slots):
    b = bytearray(_starsp.SIZE)
    b[0:len(name)] = name.encode("latin-1")
    for i, v in enumerate(slots):
        off = _starsp.PLANET_INDEX_OFFSET + 2 * i
        b[off:off + 2] = _s.pack("<h", v)
    return bytes(b)

class _GS:
    player_num = 0
_gs = _GS()
# Two planets in one system, the first slot EMPTY, so the numeral
# of the first real planet is I and not II — HAROLD::Planet_Number_
# counts occupied slots, and getting that wrong renamed five of
# seven rows the first time it was tried.
_gs.planets_raw = [_mk_planet(0, 0, 1, 1, 5),
                   _mk_planet(1, 0, 2, 3, 8)]
_gs.stars = _starsp.parse_all([_mk_star("Sol", [-1, 0, 1, -1, -1])])
_gs.colonies_raw = [
    _mk_colony(0, 0, 3, (0, 3, 0), 0, 5),      # No Farming
    _mk_colony(0, 1, 6, (2, 3, 1), 255, 8),    # farms
    _mk_colony(1, 1, 4, (0, 4, 0), 255, 8),    # another player
]
_pl_raw = bytearray(pl.SIZE)
_pl_raw[pl.TRAITS_OFFSET + _cr.TRAIT_ENVIRONMENT_IMMUNE] = 1
_gs.player_raw = [bytes(_pl_raw)]

_rows = _cr.build_rows(_gs, "name")
assert len(_rows) == 2, [r["name"] for r in _rows]
assert [r["name"] for r in _rows] == ["Sol I", "Sol II"], \
    [r["name"] for r in _rows]
for _r in _rows:
    assert sum(_r["jobs"]) == _r["pops"], _r
assert _rows[0]["no_farming"] and not _rows[1]["no_farming"], _rows
# The worked example from the fundament, section 3: Small(1)
# Ocean(5) with an environment-immune owner is 5, where the size
# table alone would say 10.
assert _rows[0]["max_pop"] == 5, _rows[0]["max_pop"]

# Nothing is drawn past the bar. Rendered onto a known background
# and measured, rather than asserted about the code: a clip that
# stops working is invisible in the source and obvious in pixels.
_surf = pygame.Surface((1920, 1080))
_surf.fill((0, 0, 0))
_area = pygame.Rect(100, 100, 1200, 400)
import json as _cjson
with open(os.path.join(SCREENS_DIR, "colony_summary", "layout.json"),
          encoding="utf-8") as _fh:
    _cfg = _cjson.load(_fh)["list"]
_cl.render(_surf, _rows, _area, _cfg, app.layout, app.style)
_px = pygame.surfarray.array3d(_surf)
for _x in range(_area.right, 1920):
    assert not _px[_x].any(), f"the list drew at x={_x}, past its area"

# A row whose population EXCEEDS its computed maximum. The two
# documented deviations in max_population() both make the number
# too small, so this is a state the real screen can reach. Those
# squares now spill into the unreachable region rather than being
# clipped at max_pop — a pop is a fact, max_pop is a computation
# — so what has to hold is that the TRACK still ends inside the
# panel. The rows above cannot catch it: both fit comfortably.
_surf.fill((0, 0, 0))
_cl.render(_surf, [{"name": "Overflow", "pops": 8,
                    "jobs": [0, 8, 0], "no_farming": False,
                    "max_pop": 3}],
           _area, _cfg, app.layout, app.style)
_px = pygame.surfarray.array3d(_surf)
for _x in range(_area.right, 1920):
    assert not _px[_x].any(), (
        f"a row with more pops than its maximum drew at x={_x} — "
        f"the bar no longer clips at its own end")

# The bar is an INVENTION and the marking has to survive. Checked
# in both homes the project requires: the module that draws it and
# the JSON a mod would edit.
_cl_src = open(os.path.join(SCREENS_DIR, "colony_summary",
                            "colonylist.py"), encoding="utf-8").read()
assert "INVENTION" in _cl_src, \
    "colonylist.py no longer marks the bar as an INVENTION"
assert "INVENTION" in _cfg.get("_invention", ""), \
    "layout.json list._invention no longer carries the marking"
# The per-row detail line is an HD EXTENSION and carries its own
# marker: the original prints climate and n/max for the SELECTED
# colony only, into the scan box at native (13, 354, 80, 88)
# (COLSUM::Draw_Colony_Scan_Info_, colsum.cpp:1155). A marking
# two documents claim exists is not a marking — this one is
# asserted in both homes, and refused if it does not name what
# the original does instead.
assert "HD EXTENSION" in _cl_src, \
    "colonylist.py no longer marks the per-row detail line"
_hd = _cfg.get("_hd_extension", "")
assert "HD EXTENSION" in _hd, \
    "layout.json list._hd_extension no longer carries the marking"
assert "colsum.cpp:1155" in _hd, \
    ("list._hd_extension no longer names what the original does "
     "instead — a label without the deviation it records is a "
     "label, not a marking")
# THE VERTICAL ANCHOR IS A DEVIATION — 12 September 2026. The
# original hangs its sprites from the row's TOP; ours sit on the
# band's FLOOR, because our band is `list_area` divided by ten
# and the slack it leaves went under the figures. Same rule as
# above: the marking is asserted in every home it claims, and it
# has to name the transcription it departs from.
_fa = _cfg.get("_figure_anchor_deviation", "")
assert "DEVIATION" in _fa and "colsum.cpp:685" in _fa, (
    "layout.json list._figure_anchor_deviation no longer marks "
    "the top-to-bottom anchor with the original's own icon row")
for _fa_home, _fa_src in (
        ("colonylist.py", _cl_src),
        ("colonytrack.py", open(os.path.join(
            SCREENS_DIR, "colony_summary", "colonytrack.py"),
            encoding="utf-8").read()),
        ("v3_projektstatus.md", open(os.path.join(
            os.path.dirname(SCREENS_DIR), "v3_projektstatus.md"),
            encoding="utf-8").read())):
    assert "DEVIATION" in _fa_src and "figure_origin_y" in _fa_src, (
        f"{_fa_home} no longer marks the figure anchor as a "
        f"DEVIATION, or no longer names the one function that "
        f"owns it")

# AND THE SPRITE'S HEIGHT IS ONE NUMBER. `colonytrack` declares
# it because `colonyfigures` imports that module and not the
# reverse; a second copy that disagreed would put the row's
# figures and the held ones on different floors (decision 36).
from screens.colony_summary import colonyfigures as _fa_fig
from screens.colony_summary import colonytrack as _fa_ctk
assert _fa_ctk.MASTER_ROWS == _fa_fig.MASTER_SIZE == 28, (
    f"colonytrack.MASTER_ROWS is {_fa_ctk.MASTER_ROWS} and "
    f"colonyfigures.MASTER_SIZE is {_fa_fig.MASTER_SIZE}; the "
    f"masters are 28 x 28 (decision 50) and the anchor is "
    f"measured off that number")
# ── "No Farming": centred in the farmers column ──
# TRANSCRIBED, 8 September 2026, and the check moved with the
# drawing. It used to sit below the bar at the left edge of the
# first job marker, and these checks asserted that placement's
# own risk — that a later draw would paint over it, which had
# happened once with every number right and nothing on screen.
# The source settles the placement instead: coldraw.cpp:315-321
# prints it with `Squeeze_Print_Paragraph_(left_x, top_y + 5,
# right_x - left_x, 28, …, 2)` and the 2 selects
# `Print_Centered_(x + width/2, y, str)`.
#
# THE COLUMN TABLE IS INSTALLED HERE, because "centred in the
# column" has no meaning in the single-track fallback that the
# synthetic rows above use — that geometry has no columns, and
# `colonyheader.install_columns` is what the real screen puts in
# `list` at startup. So this renders the SHIPPED geometry.
from screens.colony_summary import colonyheader as _chd
from screens.colony_summary import colonytrack as _ctk
from core.box import Box as _Box
with open(os.path.join(SCREENS_DIR, "colony_summary",
                       "boxes.json"), encoding="utf-8") as _bh:
    _boxes_json = _cjson.load(_bh)

def _column_cfg(base, layout, area=None):
    """`base` plus the six column BOXES and `list_area`'s span.

        The columns are boxes now, so a fixture that wants the
        shipped row geometry has to hand over box OBJECTS — the same
        thing `colonyheader.install_columns` binds.

        **THE `area` BRANCH IS GONE — 9 September 2026, and losing it
        is the point.** This used to have two arms: reference rects
        when the caller had no area, and a hand-tiled set of
        `screen_rect`s laid across the caller's synthetic area when
        it had one. That second arm was a second copy of the tiling
        arithmetic living in the checker — decision 5's "a tool is a
        reader too", one file over from where it was last paid for.
        It agreed with `colonytrack.columns` by construction and
        would have gone on agreeing with a broken one.

        Now there is nothing to lay out: a column is a fraction of
        the cutout, so the fixture hands over the reference rects and
        the span, and `columns` maps them into whatever area it is
        given — the same call the screen makes. `area` is kept only
        so the ten call sites read the same; it is not used.
        """
    del area                      # see above; kept for the callers
    out = dict(base)
    raw = colony_rects()
    boxes = []
    for name in _chd.COLUMN_BOXES:
        b = _Box({"name": name, "rect": raw[name]})
        b.update_layout(layout)
        boxes.append((name[4:], b))
    out[_ctk.COLUMNS_KEY] = boxes
    out[_ctk.COLUMNS_SPAN_KEY] = (raw["list_area"][0],
                                  raw["list_area"][2])
    return out

_cfg_cols = _column_cfg(_cfg, app.layout, _area)
assert _cfg_cols[_ctk.COLUMNS_KEY], (
    "the six column boxes are missing from boxes.json, so the "
    "shipped row geometry cannot be exercised at all")
_surf.fill((0, 0, 0))
_cl.render(_surf, [{"name": "Full", "pops": _cl.POP_LIMIT_CAP,
                    "jobs": [0, 30, 12], "no_farming": True,
                    "max_pop": _cl.POP_LIMIT_CAP}],
           _area, _cfg_cols, app.layout, app.style)
_px = pygame.surfarray.array3d(_surf)
_label_ink = [(x, y) for x in range(_area.x, _area.right)
              for y in range(_area.y, _area.bottom)
              if tuple(_px[x, y]) == tuple(_cl.NO_FARM_COLOR[:3])]
assert _label_ink, (
    "'No Farming' is not on the surface for a full 42-slot row — "
    "the squares are painted over it again")
_cols_now = _ctk.columns(_area, _cfg_cols)
_fx, _fw = _cols_now["farmers"]
_lx0 = min(x for x, _y in _label_ink)
_lx1 = max(x for x, _y in _label_ink)
assert _fx <= _lx0 and _lx1 < _fx + _fw, (
    f"'No Farming' inks x {_lx0}..{_lx1} and the farmers column is "
    f"{_fx}..{_fx + _fw} — the label has left its own column")
# CENTRED, which is the whole of what the 2 in that call means.
# Two px of slack for the odd-width case; anything more is a
# placement, not a rounding.
_want_c = _fx + _fw / 2.0
_got_c = (_lx0 + _lx1 + 1) / 2.0
assert abs(_got_c - _want_c) <= 2, (
    f"'No Farming' is centred on {_got_c:.1f} and the farmers "
    f"column's centre is {_want_c:.1f} — Print_Centered_ puts it "
    f"at left_x + width/2 (bill.cpp, mode 2)")
# AND AT top_y + 5, as a proportion of the row (5 of 31, the
# original's own row pitch at colsum.cpp:311). The original's ink
# top sits ON that y — measured at 136 against top_y + 5 = 136 on
# colony_summary_native_split.png — so this is the ink and not a
# surface edge.
_bands = _cl.row_bands(_area, _cfg_cols, app.layout.scale, 1)
_btop, _bh = _bands[0]
# THE SHIPPED BAND, not this check's synthetic area. The label's
# size is a REFERENCE value scaled by the layout, so the cap-vs-
# band relation only holds where the band is the real one — the
# `_area` above is 1200x400 to exercise the clip, and measuring
# the derivation against it asks the wrong question.
_ship_area = pygame.Rect(*app.layout.rect(
    colony_rects()["list_area"]))
_ship_band = _ctk.band_height(_ship_area, _cfg_cols)
_want_y = _btop + round(_cl.NATIVE_LABEL_Y_OFFSET * _bh
                        / _cl.NATIVE_ROW_PITCH)
_got_y = min(y for _x, y in _label_ink)
assert abs(_got_y - _want_y) <= 1, (
    f"'No Farming' inks from y={_got_y}; top_y + 5 is {_want_y} at "
    f"a band of {_bh}")
# ── ...and the SIZE is the measurement, re-measured ──
# The only source for it is a picture: font style 3's height is in
# the player's FONTS.LBX. The capital N measures 10 px of cap on
# colony_summary_native_split.png, in a 31 px row, so the drawn
# cap must be 10/31 of the band. Measured by RENDERING
# (decision 30), because a nominal font size is not a cap height
# and the substitution path can mix two fonts inside one string.
_cap_surf = app.style.render_text(
    "N", app.layout.font_size(_cfg_cols["no_farming_font"]),
    (255, 255, 255))
_cap_box = _cap_surf.get_bounding_rect()
_want_cap = _cl.NATIVE_LABEL_CAP * _ship_band / _cl.NATIVE_ROW_PITCH
assert abs(_cap_box.height - _want_cap) <= 1.5, (
    f"the 'No Farming' cap renders {_cap_box.height} px where the "
    f"measurement wants {_want_cap:.1f} — no_farming_font "
    f"{_cfg_cols['no_farming_font']} no longer carries the 10 px "
    f"cap measured off the native screenshot")
# ── The label cannot be painted over, and now by construction ──
# The old placement had to PROVE this with a full track, because
# the label shared a band with the squares. It cannot happen any
# more and the reason is the data, not the drawing: the label is
# drawn only when `max_farms == 0`, which is exactly the state in
# which the food column has no farmer to draw. Asserted rather
# than argued — a farmers column with cells in it and the label
# asked for at the same time must not exist, so the row that
# would produce it is checked to draw no farmer cell.
_surf.fill((0, 0, 0))
_cl.render(_surf, [{"name": "Hatched I", "pops": 3,
                    "jobs": [0, 2, 1], "no_farming": True,
                    "climate": 1, "max_pop": 20}],
           _area, _cfg_cols, app.layout, app.style)
_px = pygame.surfarray.array3d(_surf)
_nf_rgb = tuple(_cl.NO_FARM_COLOR[:3])
_food_rgb = tuple(_cl.ZONE_COLORS[0][:3])
_label = [(x, y) for x in range(_area.x, _area.right)
          for y in range(_area.y, _area.bottom)
          if tuple(_px[x, y]) == _nf_rgb]
_food = [(x, y) for x in range(_area.x, _area.right)
         for y in range(_area.y, _area.bottom)
         if tuple(_px[x, y]) == _food_rgb]
assert _label, "'No Farming' did not draw on a row that has free slots"
assert not _food, (
    "a No Farming row drew farmer cells — the label and the "
    "figures would then share the column, which is the collision "
    "the old placement existed to avoid")

# ── The budget, checked where it can actually fail ──
# The column sum — name + tail + building + pad + 42*unit +
# 41*gap == list_area — is no longer asserted. `track_metrics`
# hands the floor division's remainder to the name column's drawn
# width, so that sum balances BY CONSTRUCTION at every
# resolution, and a thing that cannot fail is not a check.
#
# The previous version asserted it with `1920`, `1080` and `1.0`
# as literals: it covered one of the two keys in boxes.json and
# none of the sizes reached through the fallback chain. It
# balanced at scale 1.0 and 2.0 — where every int() truncates
# cleanly — and was 11 to 30 px short at every fractional scale,
# which it never looked at.
#
# So: twelve window sizes, and the two things the construction
# can still get wrong.
#
#   1. the row ends flush     slot42_right + building + pad_x
#                             == list_area.right
#   2. the ellipsis threshold is the same everywhere — the
#      remainder is GUTTER, never text budget
#
# (2) is what guards the design decision. Letting the remainder
# into the text budget ALSO closes (1), and silently makes the
# threshold range 244..288 reference px: the same colony name
# cuts on one monitor and not on another.
#
# Both are read off the SURFACE, not recomputed. An earlier draft
# of this check derived bar_x and the clip from layout.json the
# same way the renderer does, which made it agree with the
# renderer by construction — it passed unchanged when the gutter
# was moved a pixel and when the clip was tied to the drawn
# width, the two failures it exists for.
_SIZES = [(1280, 720), (1366, 768), (1440, 900), (1600, 900),
          (1680, 1050), (1920, 1080), (1920, 1200), (2048, 1152),
          (2560, 1080), (2560, 1440), (3440, 1440), (3840, 2160)]
_boxes_path = os.path.join(SCREENS_DIR, "colony_summary", "boxes.json")

# ── THE SIX COLUMNS TILE list_area EXACTLY ──────────────────
# This replaced "the row ends flush", which was the same property
# under the old shared budget: a slot width was a floor division,
# the six columns almost never spent `list_area` exactly, and the
# remainder was handed to the name column's drawn width so the
# row could not stop short of the panel. The columns are BOXES
# now — there is no budget and no remainder — so the property is
# a rule about the boxes and it is asserted directly.
#
# It has to hold at every window because a box rect is REFERENCE
# space and `Box.update_layout` truncates independently per box:
# six `int()` calls at a fractional scale are exactly where a
# one-pixel seam between two columns would open.
_COLS = ("col_name", "col_farmers", "col_workers", "col_scientists",
         "col_building", "col_scroll")
for _W, _H in _SIZES:
    _lay = Layout(_W, _H)
    _bx = {b.name: b for b in _seated(_boxes_path, _W, _H)}
    assert "list_area" in _bx, f"no list_area box at {_W}x{_H}"
    _ar = _bx["list_area"].screen_rect
    _cc = dict(_cfg)
    _cc[_ctk.COLUMNS_KEY] = [(n[4:], _bx[n]) for n in _COLS]
    _cc[_ctk.COLUMNS_SPAN_KEY] = (_bx["list_area"].ref_rect[0],
                                  _bx["list_area"].ref_rect[2])
    _got = _ctk.columns(_ar, _cc)
    assert set(_got) == {n[4:] for n in _COLS}, sorted(_got)
    _prev = _ar.x
    for _name in _COLS:
        _x, _w = _got[_name[4:]]
        assert _x == _prev, (
            f"{_W}x{_H}: {_name} starts at {_x} and the column "
            f"before it ends at {_prev} — the six must tile "
            f"list_area with no seam and no overlap")
        _prev = _x + _w
    assert _prev == _ar.right, (
        f"{_W}x{_H}: the columns end at {_prev}, list_area at "
        f"{_ar.right} — the row stops short of its panel")

# ── AND THE COLUMN BOXES ARE RESOLUTION-INDEPENDENT ─────────
# **THE SUBJECT MOVED, THE RULE DID NOT — 12 September 2026.**
# This compared the six rects between `boxes.json`'s resolution
# keys, because `core.box.save_boxes` writes only the key the
# editor is running at and one dragged at 1080p would leave 1440p
# behind with every picture still looking right. That file holds
# no rect for this screen now, so the keys cannot disagree — and
# the rule is still worth asserting one step earlier: a box rect
# lives in REFERENCE space, so seating the same boxes at four
# window sizes has to give one answer, and a `seat` that scaled
# would be caught here rather than in a screenshot.
_by_size = {}
for _W, _H in _SIZES:
    _by_size[(_W, _H)] = {b.name: tuple(b.ref_rect)
                          for b in _seated(_boxes_path, _W, _H)}
_first_size = _SIZES[0]
for _sz, _got in _by_size.items():
    assert _got == _by_size[_first_size], (
        f"seating at {_sz} gives different reference rects from "
        f"{_first_size}: "
        f"{ {k: (_by_size[_first_size].get(k), _got.get(k)) for k in _got if _by_size[_first_size].get(k) != _got.get(k)} }")

# ── THE NAME FITS ITS CELL, AND THE BOUND IS THE GAME'S ─────
# The widest name the game can produce is `WWWWWWW IV`: the
# buffer is `char[15]` (namestar.cpp:262) AND the input field is
# capped at the pixel width of seven W's
# (`Get_String_Width_("WWWWWWW")`, namestar.cpp:246-256). It must
# not be ellipsised at any window; something past the bound must
# be. Ellipsis is the fallback for a column narrowed past what
# the editor reports, not the mechanism it used to be.
_cfg_names = _column_cfg(_cfg, app.layout)
for _W, _H in _SIZES:
    _lay = Layout(_W, _H)
    _bx = {b.name: b for b in _seated(_boxes_path, _W, _H)}
    _cw = _bx["col_name"].screen_rect.width
    _px = _lay.font_size(_cfg["name_font"])
    _bound = app.style.render_text(
        _cl.NAME_BOUND_STAR, _px, _cl.ROW_NAME).get_width()
    assert _bound <= _cw, (
        f"{_W}x{_H}: the widest name the game can make is "
        f"{_bound} px and col_name is {_cw} — narrow the column "
        f"and the editor is supposed to SAY so, not clamp")
    _det = app.style.render_text(
        _cl.NAME_BOUND_DETAIL, _lay.font_size(_cfg["small_font"]),
        _cl.DETAIL_COLOR).get_width()
    assert _det <= _cw, (
        f"{_W}x{_H}: the widest second line is {_det} px against "
        f"a {_cw} px column")
    assert _cl._fit(_cl.NAME_BOUND_STAR, app.style, _px, _cw,
                    _cfg) == _cl.NAME_BOUND_STAR, (
        f"{_W}x{_H}: the widest producible name was ellipsised")
    _over = "M" * 40
    assert _cl._fit(_over, app.style, _px, _cw, _cfg) != _over, (
        f"{_W}x{_H}: a name far past the bound was not cut, so "
        f"the fallback is not there at all")

# ── NAMES ARE LEFT-ALIGNED, which is the original's ─────────
# `Squeeze_Formatted_Paragraph_Centered_(0x0C, y, …, 0)` passes
# JUSTIFY_LEFT (colsum.cpp:582, bill.cpp:210); `Centered_` is the
# vertical axis only. Read off the surface: the name's ink starts
# at the column's own left edge, not against its right.
_lay = Layout(1920, 1080)
_bx = {b.name: b for b in _seated(_boxes_path, 1920, 1080)}
_ar = _bx["list_area"].screen_rect
_sf = pygame.Surface((1920, 1080))
_sf.fill((0, 0, 0))
# `scanned` IS SET, because the original always has one: `_g_colony_n`
# is assigned before the input loop and its later assignment has no
# else branch (colsum.cpp:880-890), and `Selection.reseat` mirrors
# that — nothing is scanned only when the list is empty. A fixture
# with no scanned colony would draw every name dimmed, which is a
# state the screen cannot be in.
_cl.render(_sf, [{"name": "Sol I", "index": 4, "pops": 2,
                  "jobs": [1, 1, 0], "no_farming": False,
                  "climate": 8, "max_pop": 6}],
           _ar, _column_cfg(_cfg, _lay), _lay, app.style, scanned=4)
_a3 = pygame.surfarray.array3d(_sf)
_ncol = _bx["col_name"].screen_rect
_hit = [x for x in range(_ncol.x, _ncol.right)
        if (_a3[x] == list(_cl.ROW_NAME[:3])).all(axis=1).any()]
assert _hit, "the colony name drew no ink at all"
assert _hit[0] - _ncol.x < _ncol.width // 3, (
    f"the name's ink starts {_hit[0] - _ncol.x} px into a "
    f"{_ncol.width} px column — that is not left-aligned, and the "
    f"original left-aligns (colsum.cpp:582 passes JUSTIFY_LEFT)")

import importlib.util as _plu
_pv_spec = _plu.spec_from_file_location(
    "_probe_colony_preview",
    os.path.join(os.path.dirname(SCREENS_DIR), "tools",
                 "colony_list_preview.py"))
_pv = _plu.module_from_spec(_pv_spec)
_pv_spec.loader.exec_module(_pv)
_pv_rows = _cr.build_rows(_pv._Snapshot(_pv.COLONIES), "name")
assert len(_pv_rows) == len(_pv.COLONIES), (
    f"the preview's snapshot yields {len(_pv_rows)} rows from "
    f"{len(_pv.COLONIES)} colonies — build_rows drops some")
assert set(_pv_rows[0]) == set(_rows[0]), (
    f"preview rows {sorted(_pv_rows[0])} against build_rows' "
    f"{sorted(_rows[0])}")
# THE PROVENANCE BAND IS A MARKING, so it gets a check. The tool
# wrote a side-by-side of a synthetic empire against a real
# screenshot and nothing in the image said so — two different
# worlds presented as a comparison. A marking without a check is
# an intention (see the fundament on the help panel's).
d.switch_to("colony_summary")
_pv_screen = d.active
_pv_screen.update(_pv._Snapshot(_pv.COLONIES))
_syn_head, _syn_detail, _syn_col = _pv.provenance(
    _pv._Snapshot(_pv.COLONIES), _pv_screen, False, "name")
assert "SYNTHETIC" in _syn_head, (
    f"the preview's band no longer says the rows are invented: "
    f"{_syn_head!r}. A tool whose output looks like a measurement "
    f"must not draw made-up data unmarked")
assert _syn_detail and "colony_list_preview" in _syn_detail, _syn_detail
assert _syn_col != _pv.BAND_LIVE, "synthetic and live share a colour"
# And the band actually reaches the image: taller surface, ink in
# the strip the render does not occupy.
_pv_flat = pygame.Surface((400, 120))
_pv_flat.fill((0, 0, 0))
_pv_banded = _pv.with_band(_pv_flat, app, _syn_head, _syn_detail,
                           _syn_col)
assert _pv_banded.get_height() > _pv_flat.get_height(), (
    "with_band returned a surface no taller than its input, so the "
    "band is drawn over the picture or not at all")
_pv_strip = pygame.Rect(
    0, 0, _pv_banded.get_width(),
    _pv_banded.get_height() - _pv_flat.get_height())
assert pygame.surfarray.array3d(
    _pv_banded.subsurface(_pv_strip)).sum() > 0, "the band is blank"
assert any(r["no_farming"] for r in _pv_rows), (
    "no preview colony shows No Farming — the max_farms == 0 "
    "case is not being drawn")
_pv_full = max(_pv_rows, key=lambda r: r["pops"])
assert (_pv_full["pops"] >= 20
        and _pv_full["max_pop"] - _pv_full["pops"] <= 4), (
    f"the stress colony is {_pv_full['pops']}/"
    f"{_pv_full['max_pop']} — it exists to show a nearly full "
    f"track and no longer does")
_pv_sparse = min(_pv_rows,
                 key=lambda r: r["pops"] / max(1, r["max_pop"]))
assert _pv_sparse["max_pop"] - _pv_sparse["pops"] >= 5, (
    f"the sparse colony is {_pv_sparse['pops']}/"
    f"{_pv_sparse['max_pop']} — it exists to show a long "
    f"unreachable tail")
assert any(len(r["name"]) >= 15 for r in _pv_rows), (
    "no preview colony has a str15 name, so the ellipsis case is "
    "not drawn")
# Numerals are earned by OCCUPIED slots, not by the orbit
# (HAROLD::Planet_Number_). Every star reading "I" is how the
# first version of the synthetic snapshot was wrong.
assert any(not r["name"].endswith(" I") for r in _pv_rows), (
    "every preview colony is numeral I — the filler planets that "
    "earn a numeral are missing from the snapshot")
# The sidebar numbers exist to be FALSIFIABLE, not plausible.
assert _pv.PLAYER["surplus_bc"] < 0, (
    "the preview's income is not negative, so red-if-negative "
    "never renders and the picture cannot show it")
assert _pv.PLAYER["surplus_food"] > 0, (
    "the preview's food is not positive, so the explicit plus "
    "never appears beside the negative income")
assert len(str(_pv.PLAYER["bc"])) >= 5, (
    "the preview's widest sidebar value is under five digits, so "
    "right alignment is not visible AS alignment")
assert len(str(_pv.PLAYER["surplus_freighters"])) == 1, (
    "the preview has no one-digit sidebar value to contrast with "
    "the widest one")

# ── An OUTPOST is not a row ──
# Both of the original's conditions, from
# Build_Global_Colony_List_ (colxport.cpp:91-99): the colony's
# owner is the local player AND its outpost_flag is zero.
# Verified live on 3 September 2026 — 12 records carried the
# local player and the Colonies screen listed 11, the difference
# being the planet the game itself calls "Yian I (Elerian
# Outpost)". See core/structs/colony.py.
#
# The flag is set here through the SPEC's own offset, not a
# literal, so a spec change breaks this loudly instead of
# flipping some other byte and passing.
from core.structs import colony as _col_spec
_out_snap = _pv._Snapshot(_pv.COLONIES)
_with_all = _cr.build_rows(_out_snap, "name")
_op_off = dict((_n, _o) for _n, _o, _k
               in _col_spec.SPEC.fields)["outpost_flag"]
_victim = 1
_op_name = _with_all[0]["name"]
_op_raw = bytearray(_out_snap.colonies_raw[_victim])
assert _op_raw[_op_off] == 0, "the preview already ships an outpost"
_op_raw[_op_off] = 1
_out_snap.colonies_raw[_victim] = bytes(_op_raw)
_without = _cr.build_rows(_out_snap, "name")
assert len(_without) == len(_with_all) - 1, (
    f"a colony with outpost_flag set is still in the rows: "
    f"{len(_without)} of {len(_with_all)}. The original's list "
    f"does not carry it (colxport.cpp:91-99)")
_gone = set(_r["index"] for _r in _with_all) - set(
    _r["index"] for _r in _without)
assert _gone == {_victim}, (
    f"the outpost filter dropped {_gone}, not the colony whose "
    f"flag was set ({_victim})")
del _op_name
# And it is the FLAG that drops it, not the owner: everything
# else about that record is untouched and it was in the list a
# moment ago.
assert any(_r["index"] == _victim for _r in _with_all), _victim

# ── The seven sort keys, and their DIRECTIONS ──
# COLSUM::Switched_cmp_ (colsum.cpp:378-401, orion2re 1.60) is a
# switch on _g_sort_index with the sign as a literal per case.
# Five descending, Name and Producing ascending, and NO direction
# toggle anywhere — clicking the active header re-sorts
# identically. Asserted on the ORDER a sort produces rather than
# on the comparator functions, so a rewrite of how sorting is
# implemented still has to come out the same way round.
import json as _sjson
_sort_cfg = _sjson.load(open(os.path.join(
    SCREENS_DIR, "colony_summary", "layout.json"),
    encoding="utf-8"))["sort"]
_sorters = _cr.SORT_KEYS
assert set(_sorters) == {b["key"] for b in _sort_cfg["buttons"]}, (
    f"the sort keys {sorted(_sorters)} do not match the buttons "
    f"{sorted(b['key'] for b in _sort_cfg['buttons'])}")

def _order(_key, _rowset):
    return [r["name"] for r in sorted(_rowset, key=_sorters[_key])]

# "beta" is deliberately lower-case and sorts BETWEEN two
# capitals only under casefold: by ASCII it lands after both.
_a = {"name": "Alpha", "pops": 3, "jobs": [1, 1, 1], "no_farming": False,
      "climate": 8, "max_pop": 9, "producing": "", "producing_turns": 0,
      "can_buy": False, "production": [1, 9, 5, 2]}
_b = {**_a, "name": "beta", "pops": 7, "production": [8, 2, 1, 9]}
_c = {**_a, "name": "Gamma", "pops": 5, "production": [4, 5, 9, 4]}
_set = [_a, _b, _c]

# Name: ascending, and CASE-INSENSITIVE — cmp_Alpha_ calls
# strcasecmp (colsum.cpp:1053). Plain str sort would put the
# lower-case "gamma" after both capitals.
assert _order("name", _set) == ["Alpha", "beta", "Gamma"], \
    _order("name", _set)
assert _order("name", _set) != sorted(r["name"] for r in _set), (
    "the name sort is matching a case-SENSITIVE order, so this "
    "check is not exercising strcasecmp")
# The five descending keys.
assert _order("population", _set) == ["beta", "Gamma", "Alpha"], \
    _order("population", _set)
assert _order("food", _set) == ["beta", "Gamma", "Alpha"], \
    _order("food", _set)
assert _order("industry", _set) == ["Alpha", "Gamma", "beta"], \
    _order("industry", _set)
assert _order("science", _set) == ["Gamma", "Alpha", "beta"], \
    _order("science", _set)
assert _order("bc", _set) == ["beta", "Gamma", "Alpha"], \
    _order("bc", _set)
# Producing cannot be honoured — Prod_To_Sort_Type_ needs
# _buildings[].cost and Selection_Name_, both loaded from the
# player's techname.lbx and not shipped. It must be declared
# unavailable AND fall back visibly, not silently.
assert "producing" in _cr.SORT_UNAVAILABLE, (
    "producing is no longer declared unavailable — if the cost "
    "and name tables have arrived, implement cmp_Prod_ "
    "(colsum.cpp:1091) rather than dropping the marking")
assert _order("producing", _set) == _order("name", _set), (
    "the producing key does something other than fall back to "
    "the name, but the tables it needs are still not shipped")
# Sorting twice by the same key changes nothing: no toggle.
_once = _order("bc", _set)
assert _order("bc", [dict(r) for r in _set]) == _once, (
    "sorting twice by the same key gave a different order — "
    "Switched_cmp_ has no direction toggle (colsum.cpp:378-401)")
# ── Ties keep the INPUT order, and that is transcribed ──
# The name fallback that used to be here was ours, and it ordered
# ties the original does not order. Four links carry the array
# order all the way through: ext_api.cpp:94 writes the colonies
# in `MOX::_colony[i]` order, colxport.cpp:91 filters them into
# `_g_colony_list_ptr` in that same order, colsum.cpp:363 swaps
# only on a STRICTLY positive comparison so equal elements never
# move, and colsum.cpp:1056 returns 0 on equality so the sign
# that would move them cannot arise.
#
# Driven through `build_rows` rather than through `_sorters`
# directly, because "input order" is a property of the whole
# path: the sort key alone cannot express it, and a key that
# LOOKS stable in isolation would still reshuffle if build_rows
# ever stopped walking `colonies_raw` in order or started using a
# sort that is not stable.
_tie_pv = [dict(_pv.COLONIES[3]), dict(_pv.COLONIES[3])]
_tie_pv[0]["star"] = "Zeta"
_tie_pv[1]["star"] = "Aeta"
# Same pops, same production: every key below is a tie.
for _k in ("population", "food", "industry", "science", "bc"):
    _fwd = [r["name"] for r in
            _cr.build_rows(_pv._Snapshot(_tie_pv), _k)]
    _rev = [r["name"] for r in
            _cr.build_rows(_pv._Snapshot(_tie_pv[::-1]), _k)]
    assert _fwd == ["Zeta I", "Aeta I"], (_k, _fwd)
    assert _rev == ["Aeta I", "Zeta I"], (_k, _rev)
    assert _fwd == _rev[::-1], (_k, _fwd, _rev)
# The negative form, so the check cannot pass by accident on a
# key that happens to be alphabetical anyway: a name tie-break
# would put "Aeta I" first BOTH times.
assert _fwd[0] != _rev[0], (
    "ties come out in the same order whichever way the snapshot "
    "is packed, so something is ordering them — the original "
    "orders them by nothing (colsum.cpp:363, colsum.cpp:1056)")
# And a redraw is still stable: same snapshot, same list. That is
# what the name fallback was bought for, and it was already true.
_snap = _pv._Snapshot(_tie_pv)
assert ([r["name"] for r in _cr.build_rows(_snap, "population")]
        == [r["name"] for r in _cr.build_rows(_snap, "population")]), (
    "two build_rows calls over one snapshot disagree — the list "
    "reshuffles between redraws")
# The tuple form is what a tie-break looks like; the absence has
# to be visible in the key itself, not only in the order.
assert not isinstance(_cr.SORT_KEYS["population"]({
    **_a, "name": "x", "pops": 1}), tuple), (
    "a descending sort key returns a tuple again, which is a "
    "tie-break by another name")
# ── THE HIGHLIGHT CONTAINS THE WORD IT LIGHTS ──────────────
#
# `layout` measured `label` and `render` drew `label.upper()`, so
# the lit box was sized for a string nobody sees: at 1080p "Name"
# measures 52 px and "NAME" draws 56, "Industry" 76 against 96,
# "Producing" 92 against 113. The active key sat behind its own
# text instead of around it, worst on the longest words — which
# is what made a dimmed PRODUCING read as a second selection
# rather than as an unavailable one. Both calls go through
# `colonysort.display` now, and this asserts the property that
# names, rather than the identity of the two call sites.
from screens.colony_summary import colonysort as _csort
_sb_data = app.res.load_json(
    "screens/colony_summary/layout.json", {}) or {}
_sb_keys = [(b["key"], b["label"])
            for b in _sb_data.get("sort", {}).get("buttons", [])]
assert _sb_keys, "the sort bar has no buttons to lay out"
for _sw, _sh in ((1920, 1080), (2560, 1440), (3440, 1440),
                 (3840, 2160)):
    _slay = Layout(_sw, _sh)
    _sbox = {b.name: b for b in _seated(
        os.path.join(SCREENS_DIR, "colony_summary", "boxes.json"),
        _sw, _sh)}
    # ONE BOX PER KEY since 12 September 2026. The row's font
    # size is the first slot's, the way `colonysort.font_size`
    # reads it — asserted here at four resolutions including one
    # that is not 16:9, because the highlight has to contain its
    # word at every one of them and 3440x1440 is where a letterbox
    # offset would show up.
    _slot_boxes = {}
    for _k, _lbl in _sb_keys:
        _bx = _sbox.get(_csort.box_name(_k))
        assert _bx is not None, (
            f"{_sw}x{_sh}: no {_csort.box_name(_k)} box")
        _slot_boxes[_k] = _bx.screen_rect
    _sfs = _slay.font_size(
        _sbox[_csort.box_name(_sb_keys[0][0])]
        .style.get("font_size", 18))
    _btns = _csort.layout(_slot_boxes, _sb_keys, app.style, _sfs)
    assert len(_btns) == len(_sb_keys), (
        f"{_sw}x{_sh}: {len(_btns)} buttons for "
        f"{len(_sb_keys)} keys — a key lost its box")
    for _bt in _btns:
        _drawn = app.style.render_text(
            _csort.display(_bt.label), _sfs, (255,) * 3).get_width()
        assert _drawn <= _bt.highlight.width, (
            f"{_sw}x{_sh}: {_bt.label!r} draws {_drawn} px and its "
            f"highlight is {_bt.highlight.width} — the lit box has "
            f"to contain the word it lights, or the active key "
            f"reads as a smudge and a dimmed key reads as a "
            f"second selection")
        assert _bt.highlight.width <= _bt.hit.width, (
            f"{_sw}x{_sh}: {_bt.label!r}'s highlight is wider than "
            f"its hit rect")
# AND THE PAD IS THE ORIGINAL'S, measured off its own framebuffer:
# the lit box is native 92..138 around ink at 94..136, two native
# px per side, which is six reference.
# ── THE TYPOGRAPHY DEVIATION IS A RENDERING, NOT AN EDIT ────
# Capitals and no colon are Data's decision (9 September 2026) and
# are marked. What the check defends is the thing that makes a
# deviation checkable at all: the STORED labels must still be the
# original's own spelling, so what is deviated from stays on
# record. The day somebody "tidies" layout.json to match the
# screen, the deviation becomes invisible and unfalsifiable.
for _k, _lbl in _sb_keys:
    assert _lbl != _lbl.upper() or len(_lbl) <= 2, (
        f"the stored sort label {_lbl!r} is already capitals — the "
        f"original prints these in mixed case and the capitals are "
        f"the RENDERING's deviation, not the data's")
_emp_rows = _sb_data.get("empire", {}).get("rows", [])
assert _emp_rows, "the sidebar has no rows"
for _r in _emp_rows:
    _l = _r.get("label", "")
    assert _l and _l != _l.upper(), (
        f"the stored sidebar label {_l!r} is already capitals")
    assert ":" not in _l, (
        f"the stored sidebar label {_l!r} carries the colon; the "
        f"original's string has it and ours drops it in the "
        f"RENDERING — putting it in the data hides the deviation")
assert "%sReserve: " in _sb_data["empire"].get("_estrings_note", ""), (
    "empire._estrings_note no longer records the original's own "
    "string, which is what the colon deviation is measured against")
for _home, _txt in (
        ("colonysort.py", open(os.path.join(
            SCREENS_DIR, "colony_summary", "colonysort.py"),
            encoding="utf-8").read()),
        ("colonyempire.py", open(os.path.join(
            SCREENS_DIR, "colony_summary", "colonyempire.py"),
            encoding="utf-8").read()),
        ("layout.json", _sb_data["sort"].get(
            "_typography_deviation", "")),
        ("v3_projektstatus.md", open(os.path.join(
            os.path.dirname(SCREENS_DIR), "v3_projektstatus.md"),
            encoding="utf-8").read())):
    assert "typography" in _txt.lower() and "DEVIATION" in _txt, (
        f"{_home} does not carry the typography deviation")

# ── ALL SEVEN LABELS ARE ONE COLOUR ─────────────────────────
#
# **THIS REPLACES THE MARKING CHECK — 12 September 2026, Data's
# decision.** PRODUCING was drawn DIMMED to say that this build
# sorts by name where the original sorts by cost, and that was a
# marked DEVIATION with a note in four places, this check being
# one of them. Data read the dim word as a wrong colour twice, so
# the marker had failed as a marker: on the screen there is no
# note, only a word in a different grey. The dimming is gone and
# the four markings with it; what is asserted now is the property
# that replaced them, which is stronger than a note about a colour
# — the seven words are drawn in the SAME colour, and that colour
# is the original's own.
#
# All seven of the original's buttons are one field
# (`Add_Multi_Button_Field_`, colsum.cpp:267-273) and it draws
# them alike: every inactive label measures (196, 196, 196) on its
# framebuffer, PRODUCING included, and only the active one differs
# at (196, 208, 252) — here the lit box is the whole difference.
#
# MEASURED OFF THE RENDER, not read out of a constant: a screen
# that passed the colour and then dimmed the word in the blit
# would satisfy any check that only looked at `SORT_TEXT`.
from screens.colony_summary import screen as _sortscr
assert tuple(_sortscr.SORT_TEXT[:3]) == (196, 196, 196), (
    f"the sort row's colour is {tuple(_sortscr.SORT_TEXT[:3])} "
    f"and the original's inactive label is (196, 196, 196)")
import importlib.util as _sk_u
import numpy as _sk_np
_sk_spec = _sk_u.spec_from_file_location(
    "_sort_preview", os.path.join(os.path.dirname(SCREENS_DIR),
                                  "tools", "colony_list_preview.py"))
_plv_for_sort = _sk_u.module_from_spec(_sk_spec)
_sk_spec.loader.exec_module(_plv_for_sort)
_sk_data_sort = _sb_data["sort"]
_sk_app, _sk_screen = _plv_for_sort.build_screen(1920, 1080)
_sk_app.dispatcher.switch_to("colony_summary")
_sk_screen.enter(None)
_sk_screen.update(_plv_for_sort._Snapshot(_plv_for_sort.COLONIES))
_sk_inks = {}
for _sk_key in [_b["key"] for _b in _sk_data_sort["buttons"]]:
    _sk_surf = pygame.Surface((1920, 1080))
    _sk_surf.fill((0, 0, 0))
    _sk_screen._sort_key = "name"
    _sk_screen.render(_sk_surf)
    _sk_box = _sk_screen.box_rect(f"sort_{_sk_key}")
    assert _sk_box, f"no box for sort_{_sk_key}"
    # INSIDE THE SLOT'S BLEED. The box is the hole grown by
    # `colonyplates.BLEED`, so its outermost ring is the frame's
    # own lit rim — bright metal, which read as 204/209/210 for
    # FOOD and 200/201/202 for INDUSTRY and made three colours out
    # of one.
    _sk_r = pygame.Rect(*_sk_screen.layout.rect(_sk_box)).inflate(
        -6 * _sk_screen.layout.scale, -6 * _sk_screen.layout.scale)
    _sk_a = pygame.surfarray.array3d(
        _sk_surf.subsurface(_sk_r)).transpose(1, 0, 2).astype(int)
    # The word's own ink: the MOST COMMON bright pixel. The fills
    # under it are dark (the panel base 8/14/23, the active
    # 30/48/88) and the anti-aliased edges of the glyphs are every
    # shade between, so the mode is the colour the text was
    # rendered in and a max would be whatever one edge pixel did.
    _sk_bright = _sk_a.reshape(-1, 3)
    _sk_bright = _sk_bright[_sk_bright.sum(axis=1) > 400]
    assert len(_sk_bright) >= 20, (
        f"sort_{_sk_key} drew no word bright enough to measure")
    _sk_vals, _sk_counts = _sk_np.unique(
        _sk_bright, axis=0, return_counts=True)
    _sk_inks[_sk_key] = tuple(
        int(v) for v in _sk_vals[_sk_counts.argmax()])
assert len(set(_sk_inks.values())) == 1, (
    f"the seven sort labels are drawn in {len(set(_sk_inks.values()))} "
    f"different colours: {_sk_inks} — PRODUCING was dimmed until "
    f"12 September 2026 and nothing may dim a key again without "
    f"saying so on the screen rather than in a note")
assert set(_sk_inks.values()) == {(196, 196, 196)}, (
    f"the sort labels ink at {set(_sk_inks.values())} against the "
    f"original's (196, 196, 196)")
# AND THE STATE THE DIMMING USED TO DRAW IS STILL THERE. It is
# what refuses a move made under an unavailable sort
# (`colonypick`) and what falls the key back to a name sort; only
# the DRAWING of it went.
assert _cr.SORT_UNAVAILABLE and "cost" in "".join(
    _cr.SORT_UNAVAILABLE.values()), (
    "SORT_UNAVAILABLE no longer says the cost table is what is "
    "missing — the key still sorts by name and something has to "
    "carry why")
assert "colsum.cpp:1091" in open(os.path.join(
    os.path.dirname(SCREENS_DIR), "v3_projektstatus.md"),
    encoding="utf-8").read(), (
    "v3_projektstatus.md no longer carries the open item that "
    "replaced the marking: Producing sorts by name until "
    "TECHDATA::_buildings cost is extracted (colsum.cpp:1091)")

assert _csort.HIGHLIGHT_PAD == 6, (
    f"HIGHLIGHT_PAD is {_csort.HIGHLIGHT_PAD}; the original leaves "
    f"2 native px each side of the word (lit box 92..138, ink "
    f"94..136, measured at 1080p) = 6 reference")

ok("colony summary sort keys (seven, five descending, "
   "case-insensitive name, no toggle, ties in input order, "
   "producing declared unavailable)")
