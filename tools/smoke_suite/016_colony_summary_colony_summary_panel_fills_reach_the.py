# smoke-suite area: colony_summary
#
# Part of the OrionLayer smoke suite — 016_colony_summary_colony_summary_panel_fills_reach_the.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (92 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 4 check(s) it holds:
#   - colony_summary panel fills reach the screen (the inset is black in a rendered frame, not only in
#   - colony_summary galaxy_inset (transform, the four colour branches, uniform-scale geometry, markin
#   - colony layout reference (columns are the list, the figure column fits the original's widest, ins
#   - colony inset dot + figure step (odd by requirement, centred on the computed pixel at all three r


# ── galaxy_inset: the original's small galaxy map ──
# COLSUM::Draw_Galaxy_Map_ (colsum.cpp:415) is one call into
# MOVEBOX::Draw_Galaxy_Map_Box_ at native (380, 349, 128, 91),
# view_mode 3. The transform was verified against the original's
# OWN framebuffer on 4 September 2026 — all 99 stars of the
# reference save within 2 px of ink — and what is asserted here
# is the arithmetic that verification passed, so a retyped
# constant fails without a game running.
from screens.colony_summary import colonyinset as _ci
import struct as _ist
from core.structs import star as _istar

def _fake_star(x, y, owner=-1, spectral=0, visited=0, name=b"S"):
    b = bytearray(_istar.SIZE)
    b[0:len(name)] = name
    _ist.pack_into("<hh", b, 15, x, y)
    _ist.pack_into("<b", b, 20, owner)
    b[22] = spectral
    b[171] = visited
    return _istar.parse(bytes(b))

class _FakeGS:
    # MAP_MAX IS A PAIR, and the default is the reference save's
    # own 1800 x 1350 (99 stars, 12 x 9 cells). A fake that
    # carried x alone is how the y ceiling went untested for as
    # long as the recovery only read x.
    def __init__(self, stars, players=(), num=0,
                 max_x=1800, max_y=1350):
        self.stars = stars; self.player_raw = list(players)
        self.player_num = num
        self.map_max_x = max_x; self.map_max_y = max_y
        self.colonies_raw = []; self.planets_raw = []

# THE POSITION, transcribed: movebox.cpp:19-20 and :62-64.
# max_map_scale 36 comes from MAP_MAX 1800 x 1350 through
# zoomtables.max_map_scale, which is the one home for it.
_iscale = zt.max_map_scale(1800, 1350)
assert _iscale == 36, _iscale
# And the dots move with it: a galaxy where the retired estimate
# and the transcription disagree must place its stars through the
# transcription's answer, not the estimate's. Same star, two
# galaxies, and the 45-vs-44 difference has to show.
_probe_dot = _crw.galaxy_inset_stars(
    _FakeGS([_fake_star(2000, 1600)], max_x=2250, max_y=1800))[0]
_want_45 = (((2000 * 1000 // 45) * 10) // (506000 // 128),
            ((1600 * 1000 // 45) * 10) // (400000 // 91))
assert _probe_dot[:2] == _want_45, (_probe_dot, _want_45)
assert _want_45 != (((2000 * 1000 // 44) * 10) // (506000 // 128),
                    ((1600 * 1000 // 44) * 10) // (400000 // 91)), \
    "pick a star where 44 and 45 actually place differently"
for _sx_in, _sy_in in ((0, 0), (1740, 1285), (900, 600)):
    _want_x = ((_sx_in * 1000 // 36) * 10) // (506000 // 128)
    _want_y = ((_sy_in * 1000 // 36) * 10) // (400000 // 91)
    _got = _crw.galaxy_inset_stars(
        _FakeGS([_fake_star(_sx_in, _sy_in)]))[0]
    assert _got[:2] == (_want_x, _want_y), (_got, _want_x, _want_y)
# Every star of the reference galaxy lands INSIDE the box. Not a
# tautology: the divisors are per-axis and a swapped pair would
# still produce plausible numbers, off the box in one direction.
_ibox = _crw.INSET_NATIVE
for _gx, _gy in ((0, 0), (1740, 1285), (1800, 1350)):
    _px, _py, _ = _crw.galaxy_inset_stars(
        _FakeGS([_fake_star(_gx, _gy)]))[0]
    assert 0 <= _px <= _ibox[2] and 0 <= _py <= _ibox[3], (
        f"galaxy ({_gx}, {_gy}) maps to ({_px}, {_py}), outside "
        f"the original's {_ibox[2]}x{_ibox[3]} box")

# THE COLOUR RULE, movebox.cpp:67-79, all four branches.
_COLOR_OFF = next(f[1] for f in _ps.SPEC.fields if f[0] == "color")

def _player_with_color(c):
    b = bytearray(_ps.SIZE)
    b[_COLOR_OFF] = c
    return bytes(b)

_iplayers = [_player_with_color(5)]
assert _crw.galaxy_inset_stars(_FakeGS(
    [_fake_star(0, 0, spectral=_istar.CLASS_BLACK_HOLE)]))[0][2] == 9, \
    "a black hole must take index 9 on this screen (movebox.cpp:69)"
assert _crw.galaxy_inset_stars(_FakeGS(
    [_fake_star(0, 0, owner=-1)]))[0][2] == 8, \
    "an unowned star with owner -1 takes 8 (movebox.cpp:73)"
assert _crw.galaxy_inset_stars(_FakeGS(
    [_fake_star(0, 0, owner=-3, visited=1)]))[0][2] == 8, \
    "an unowned star the player has visited takes 8"
assert _crw.galaxy_inset_stars(_FakeGS(
    [_fake_star(0, 0, owner=-3, visited=0)]))[0][2] == 0, \
    "unowned, unvisited and not -1/-2 takes 0 (movebox.cpp:75)"
assert _crw.galaxy_inset_stars(_FakeGS(
    [_fake_star(0, 0, owner=0)], _iplayers))[0][2] == 5, \
    "an owned star takes _player[owner].color (movebox.cpp:78)"

# THE GEOMETRY IS A RULE, not a rect: uniform scale, centred,
# letterboxed — the same rule core.mapcoords.MapView applies, and
# the reason the map does not fill this cutout. Asserted at
# several box shapes so a hole that changes shape cannot start
# stretching the galaxy silently.
for _bw, _bh in ((451, 203), (203, 203), (128, 91), (900, 400)):
    _r = _ci.map_rect(pygame.Rect(10, 20, _bw, _bh))
    assert _r.w <= _bw and _r.h <= _bh, (_r, _bw, _bh)
    assert abs(_r.w / _r.h - 128 / 91.0) < 0.02, (
        f"map_rect({_bw}x{_bh}) gave {_r.w}x{_r.h}, aspect "
        f"{_r.w / _r.h:.3f} against the original's "
        f"{128 / 91.0:.3f} — a galaxy is a shape, and the box it "
        f"goes in does not have to be the shape the original's "
        f"box was (mapcoords.MapView applies the same rule)")
    assert abs((_r.x - 10) - (_bw - _r.w) / 2) <= 1, "not centred"
    assert abs((_r.y - 20) - (_bh - _r.h) / 2) <= 1, "not centred"

# THE MARKINGS. Three deviations and three omissions, and a
# marking without a check is an intention.
_icfg = _out_cfg["inset"]
for _cite in ("colsum.cpp:415", "colsum.cpp:86", "view_mode 3",
              "FRAMEBUFFER"):
    assert _cite in _icfg["_note"], (
        f"inset._note no longer carries {_cite!r}")
# And the witness record survives where the table is, not only
# in a session report — the shape drawn_production uses.
for _cite in ("NO WITNESS", "mox.cpp:903", "silver"):
    assert _cite in (_ci.__doc__ or "") or _cite in open(
        os.path.join(SCREENS_DIR, "colony_summary",
                     "colonyinset.py"), encoding="utf-8").read(), (
        f"colonyinset no longer records {_cite!r} at INSET_COLORS "
        f"— which of the ten colour indices has been seen on a "
        f"live frame, and why the main-palette table does not "
        f"recover the three that have not")
for _cite in ("gstar.lbx", "OWNER_COLORS", "3, 4 and 5"):
    assert _cite in _icfg["_deviation_note"], (
        f"inset._deviation_note no longer carries {_cite!r} — the "
        f"sprite is not shipped, the colours are the skin's, and "
        f"three of the ten were never measured")
# THE NOTE'S SUBJECT CHANGED ON 6 SEPTEMBER 2026 AND SO DID THIS
# CHECK. It used to hold the note to the 451 x 203 box and the
# 286 px reading — the original's own 128 x 91 picture scaled
# uniformly, which keeps the original's 0.89943 vertical squash.
# The rebuild's decided reading is 253 x 200, isotropic, scale
# 5/M, no letterbox at any galaxy size, and the two readings
# differ by 11 % of content width from the same data. Keeping the
# old citations would have held the note to the reading that was
# withdrawn, which is worse than not checking it.
for _cite in ("253 x 200", "50.6*M", "NO LETTERBOX AT ANY SIZE",
              "HD EXTENSION", "DEVIATION", "0.89943",
              "decision 44"):
    assert _cite in _icfg["_geometry_note"], (
        f"inset._geometry_note no longer carries {_cite!r}")
# AND THE 286 READING MAY NOT COME BACK. Two readings of one
# inset in one tree is what this note used to be.
assert "286" not in _icfg["_geometry_note"], (
    "the 286 px reading is back in inset._geometry_note — that is "
    "the anisotropy-preserving reading the isotropic decision "
    "replaced, and the tree may hold one of the two")
for _cite in ("movebox.cpp:98-101", "colsum.cpp:69-75",
              "colsum.cpp:731", "_cluster_colony_n"):
    assert _cite in _icfg["_not_drawn_note"], (
        f"inset._not_drawn_note no longer carries {_cite!r} — the "
        f"animation, the star fields and the population-transfer "
        f"connect line are what the original does here and this "
        f"does not")
for _cite in ("NOT DRAWN", "gstar.lbx", "Colsum_Connect"):
    assert _cite in (_ci.__doc__ or ""), (
        f"colonyinset no longer records {_cite!r}")

# IT DRAWS, AND IT SENDS NOTHING. Same guard as the scroll path
# (decision 46): this panel is display only.
class _InsetCap(_Cap):
    def __init__(self):
        super().__init__(); self.fields = []
    def activate_field(self, f): self.fields.append(f)
_icap = _InsetCap()
_icl, _icon = app.client, app.connected
app.client, app.connected = _icap, True
_isnap = _pv._Snapshot(_pv.COLONIES)
_scr_op.update(_isnap)
_isurf = pygame.Surface((1920, 1080))
_iarea = pygame.Rect(*app.layout.rect(_scr_op.box_rect("galaxy_inset")))
_isurf.fill((0, 0, 0))
_scr_op._render_inset(_isurf)
app.client, app.connected = _icl, _icon
assert _icap.calls == [] and _icap.keys == [] and _icap.fields == [], (
    f"the galaxy inset reached the game: {_icap.calls}/"
    f"{_icap.keys}/{_icap.fields}. It is display only — the "
    f"original's stars are fields and ours are not (fundament 46)")
# THE FILL A PANEL NAMES IS THE FILL ON THE SCREEN, read back
# off a rendered frame and not off the value.
#
# For a day the inset's black was in `layout.json`, measured,
# documented and accepted — and the panel on screen was still
# PANEL_BG, because the lookup read `_data[name + "_fill"]` while
# the key sits inside `_data["panels"]`. Nothing raised: a panel
# without a fill is the normal case, so the miss looked exactly
# like the default. That is the help popup's lesson again — the
# background you see is not always the background that is set —
# and the only thing that can tell them apart is a sample.
from screens.colony_summary import screen as _cs_mod
from core import palette as _fl_pal
_fl_panels = _scr_op._data.get("panels", {})
# A PANEL NAMES A SKIN KEY OR IS `true` — 13 September 2026, brief
# 96. A colour typed into `panels` is the second home decision 14
# forbids, and a key the skin lacks is a panel that cannot draw.
for _k, _v in _fl_panels.items():
    if _k.startswith("_"):
        continue
    assert _v is True or isinstance(_v, str), (
        f"panels.{_k} is {_v!r} — a panel is `true` (the panel base) "
        f"or the NAME of a colors.json key, never a colour")
    if isinstance(_v, str):
        _fl_pal.require("colony_summary", _v)
_fl_surf = pygame.Surface((1920, 1080))
_fl_surf.fill((255, 0, 255))
_scr_op.render(_fl_surf)
# Sampled as a MODE over the box and not read at one pixel: the
# frame image is blitted after the panels and its rim bleeds a
# few px inward, and the inset draws stars on top. The background
# is what most of the box is — the same method the (0, 8, 0)
# measurement of the original used.
for _k, _want in (("galaxy_inset",
                   _fl_pal.require("colony_summary",
                                   _fl_panels["galaxy_inset"])),
                  ("header",
                   _fl_pal.require("colony_summary",
                                   _fl_panels["header"])),
                  ("planet_info", None)):
    _fr = pygame.Rect(*app.layout.rect(_scr_op.box_rect(_k)))
    _fa = pygame.surfarray.array3d(_fl_surf.subsurface(_fr))
    _hist = {}
    for _sx in range(4, _fr.w - 4, 3):
        for _sy in range(4, _fr.h - 4, 3):
            _c = tuple(int(_v) for _v in _fa[_sx, _sy])
            _hist[_c] = _hist.get(_c, 0) + 1
    _got, _n = max(_hist.items(), key=lambda _i: _i[1])
    _exp = tuple(_want[:3]) if _want else tuple(_cs_mod.PANEL_BG[:3])
    assert _got == _exp and _n > sum(_hist.values()) // 2, (
        f"{_k} is mostly {_got} ({_n} of {sum(_hist.values())} "
        f"samples) on the rendered frame; layout.json asks for "
        f"{_exp}")
ok("colony_summary panel fills reach the screen (the inset is "
   "black in a rendered frame, not only in layout.json)")

ok("colony_summary galaxy_inset (transform, the four colour "
   "branches, uniform-scale geometry, markings, sends nothing)")

# ── The layout reference, which is the whole chain now ──
#
# layout_reference.json is the ONE place this screen's rectangles
# are typed, and since Phase B it is one link from the boxes:
# `tools/boxes_from_reference.py` writes them and
# `colonyplates.reseat` rebuilds them at every load. What this
# checks is the file's own arithmetic and that every rectangle in
# it resolves to the box the running screen holds.
_proj = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from screens.colony_summary import colonyplates as _cpl2
_lr_path = _cpl2.reference_path(_proj)
_lr, _lr_windows = _cpl2.load_reference(_lr_path)
import numpy as np
from PIL import Image as _PILImage
from core.config import REF_W as _REF_W, REF_H as _REF_H

# THE COLUMNS ARE THE LIST. No slack to distribute, unlike the
# single-track row where six floor divisions dropped pixels that
# had to be given away.
assert sum(_lr["list_columns"].values()) == _lr["list"][2], (
    f"list_columns sum to {sum(_lr['list_columns'].values())}, the "
    f"list is {_lr['list'][2]} wide")

# ── THE RING IS GONE, AND SO IS THE RULE THAT RESTED ON IT ──
#
# `ring` was four values measured off the main-screen master, and
# "every window is inside the ring, per side" was the rule it
# carried: a hole outside the metal is not a layout preference, it
# is a hole in the edge of the screen. Phase B deleted the master,
# the plate machinery and both `layout_reference` entries with
# them (decision 55).
#
# **THE RULE IS NOT DROPPED, IT IS SHARPER.** The ring was an
# approximation of the artwork — one rectangle standing for the
# whole of it. What replaces it is "every window sits inside its
# OWN hole", asserted against `assets/frame.png`'s alpha at all
# three shipped resolutions, in the colony_summary block above.
# A window outside the metal fails there, and so does one inside
# the metal but over the wrong hole, which the ring never caught.

# FIGURE CAPACITY IS ASSERTED, NOT NOTED. A column must fit at
# least as many unsqueezed figures as the original's widest does
# — industry, reach 122 at pitch 30, which is four. The column
# and the pitch both scale with the resolution, so the count is
# the same at all three, and asserting all three is what proves
# that rather than assuming it.
_orig_fit = max((r - l - 10) // 30 for l, r in
                ((101, 226), (236, 368), (378, 502)))
from screens.colony_summary import colonytrack as _ctk_cap
_cap_la = colony_rects()["list_area"]
_cap_cfg = _sjson.load(open(os.path.join(
    SCREENS_DIR, "colony_summary", "layout.json"),
    encoding="utf-8"))["list"]
for _spec in _lr["_resolutions"]:
    _sw, _sh = (int(v) for v in _spec.split("x"))
    _slay = Layout(_sw, _sh)
    _sarea = pygame.Rect(*_slay.rect(_cap_la))
    # THE STEP AND THE COLUMN BOTH COME FROM THE BOXES NOW. The
    # column was `layout_reference.list_columns` and the step a
    # per-resolution table; both are derived, so this is measured
    # rather than read off two files that could disagree.
    _step = _ctk_cap.figure_step(_sarea, _cap_cfg)
    _cbox = colony_rects()["col_farmers"]
    _colw = _cbox[2] * _slay.scale
    _fits = int((_colw - 28 * _step) // (30 * _step) + 1)
    assert _fits >= _orig_fit, (
        f"{_spec}: a figure column of {_colw:.0f} px at step "
        f"{_step} fits {_fits} unsqueezed figures, the original's "
        f"widest column fits {_orig_fit}")

# THE LOWER BAND WAS EVEN AND FLUSH, AND THAT IS NOW DATA'S CALL
# — 11 September 2026. Three enforcements dropped here: the band
# flush with the list on the left, flush on the right, and its
# three gaps equal. Every one of them is CHOSEN: `_lower_band_note`
# traces the gap to "THE MASTER'S OWN SLOT DIVIDER", which is our
# own artwork, and the flushness to nothing but our own eye. MOO2
# has no lower band of four panels at all — the shape is an HD
# EXTENSION, so there is nothing here to transcribe and nothing
# for the suite to defend.
#
# They stay MEASURED. The numbers below still come out on every
# run, so a band that drifts is visible; it just no longer fails.
import frame_holes as _fh_mod
_band_keys = _fh_mod.BAND_KEYS
_band = sorted((_lr[_k] for _k in _band_keys), key=lambda r: r[0])
_gaps = [b[0] - (a[0] + a[2]) for a, b in zip(_band, _band[1:])]
_l0, _l1 = _lr["list"][0], _lr["list"][0] + _lr["list"][2]
report(f"lower band x {_band[0][0]}..{_band[-1][0] + _band[-1][2]} "
       f"against the list's {_l0}..{_l1} "
       f"(left {_band[0][0] - _l0:+d}, "
       f"right {_band[-1][0] + _band[-1][2] - _l1:+d}) | "
       f"panel gaps {_gaps}")
# THE SORT ROW IS EIGHT BOXES since 12 September 2026, and every
# width and gap in it is Data's. Reported per box, because the
# one number this used to print ("bar + gap + return") described a
# layout that no longer exists and a mean gap would hide exactly
# what a hand-placed row goes wrong in: one slot out of line.
_row = sorted(([_k] + list(_lr[_k])
               for _k in _fh_mod.SORT_BOX_KEYS + ["return_button"]),
              key=lambda r: r[1])
report("sort row, left to right: "
       + " | ".join(f"{_r[0]} {_r[1:]}" for _r in _row))
# The `gaps` table went with the rails in Phase B: it held the
# master's seven struts by role, and nothing lays a rail any more.
# The widths are still reported, because a hand-placed row is
# where an uneven gap shows.
report("sort row gaps: "
       + ", ".join(f"{_a[0]}->{_b[0]} {_b[1] - (_a[1] + _a[3])}"
                   for _a, _b in zip(_row, _row[1:])))
report(f"band bottom {max(_lr[_k][1] + _lr[_k][3] for _k in _band_keys)}"
       f" -> sort row top {min(_r[2] for _r in _row)} | sort row "
       f"bottom {max(_r[2] + _r[4] for _r in _row)}")

# THE INSET'S ASPECT IS THE ORIGINAL'S COVERAGE, to a thousandth.
# movebox.cpp:20-21: the crop is 128*(506000//128) by
# 91*(400000//91) world units times M/10000, and M cancels.
_ix, _iy, _iw, _ih = _lr["galaxy_inset"]
_crop = (128 * (506000 // 128)) / (91 * (400000 // 91))
assert abs(_iw / _ih - _crop) < 0.001, (
    f"the inset box is {_iw / _ih:.4f} against the original's "
    f"coverage aspect {_crop:.4f} — a letterbox at every galaxy "
    f"size is the cost, and Part 3 says there is none")
# THE 1:1 PROPERTY IS GONE — 8 September 2026, and it is recorded
# rather than quietly dropped. This asserted `(_iw*2, _ih*2) ==
# (506, 400)`: at 3840x2160 the box was the small galaxy's own
# world extent at one device pixel per world unit. The list grew
# 29 ref px so 1440p could take figure step 3, the 29 came out of
# the lower band's height, and this box is what the band's height
# fixes — so it is 239 x 189 now and the coincidence is over.
#
# It was a CONSEQUENCE of the box's size, never a requirement of
# the drawing: `colonyinset.map_rect` fits 128:91 isotropically
# on `min(w/128, h/91)` and no 1:1 relation enters it. What was
# the rule underneath is the ASPECT, asserted above and still
# inside a thousandth. What replaces the instance is the property
# that actually has to hold — the map still fits its box on the
# axis that binds, and the box never crops it.
from screens.colony_summary import colonyinset as _cinset
_im = _cinset.map_rect(pygame.Rect(_ix, _iy, _iw, _ih))
assert _im.w <= _iw and _im.h <= _ih, (
    f"the inset's map {_im.w}x{_im.h} does not fit its box "
    f"{_iw}x{_ih} — map_rect is supposed to letterbox, not crop")
assert _im.w == _iw, (
    f"the inset's map is {_im.w} of {_iw} px wide: HEIGHT has "
    f"become the binding axis, which puts panel either side of "
    f"the galaxy instead of above and below it. Below a box "
    f"height of {round(_iw * 91 / 128)} that is what happens")

# THE DERIVATION IS REPRODUCIBLE AND ROUNDS LIKE THE SCREEN. This
# rendered the mask twice and compared the pixels, which was the
# licence to gitignore it (decision 40); there is no mask and
# nothing generated left on this screen. What the check was
# actually about survives and is the half that could go wrong: a
# rectangle read out of the reference must resolve to the same
# device rect the running screen resolves it to, at every
# resolution, through `Layout.rect`'s truncation and no second
# rounding rule.
# **TWO ASSERTIONS LEFT HERE ON 12 September 2026, AND BOTH WENT.**
# `assert _a1 == _a2, "Layout.rect is not a function"` called one
# PURE function twice with one argument and compared the results —
# it could not fail, and it replaced the mask double-render, which
# could. And "every rect resolves to the box the screen holds" is
# asserted in the colony_summary block above, through
# `colonyplates.box_rects`; this copy open-coded the bleed
# arithmetic instead, which made it a fourth home for an
# expression that has to agree to the pixel.
ok("colony layout reference (columns are the list, the figure "
   "column fits the original's widest, inset aspect = the "
   "original's coverage and the map never crops)")

# ── The two colony tables in zoomtables ──
#
# THE DOT IS ODD BY REQUIREMENT, not by taste. The original draws
# its 3 px dot at (sx - 1, sy - 1) so the computed pixel IS the
# centre (movebox.cpp:103); an even size has no centre pixel, so
# "the star is drawn where the transform says" would stop being
# checkable. This asserts the property on a RENDER rather than on
# the arithmetic that produced it.
from core import zoomtables as _zt2
assert set(_zt2.INSET_DOT_DIM) == set(_lr["_resolutions"])
# ── THE FIGURE STEP IS DERIVED, so this check derives too ──
# There is no `FIGURE_STEP` table and no `layout_reference.
# figure_scale`: the list holds `row_count` rows, the band is the
# window divided by that, and the step is the largest whose
# `28*step` fits under the plate's 1 px line. What is asserted is
# that the derivation still yields 2 / 3 / 4 at the three shipped
# resolutions — the numbers the tables used to declare — recomputed
# from the BOXES and the masters rather than read from either.
_der_la = d.active.box_rect("list_area")
_der_cfg = _sjson.load(open(os.path.join(
    SCREENS_DIR, "colony_summary", "layout.json"),
    encoding="utf-8"))["list"]
_der = {}
for _rk in _lr["_resolutions"]:
    _rw, _rh = (int(v) for v in _rk.split("x"))
    _der[_rk] = _ctk.figure_step(
        pygame.Rect(*Layout(_rw, _rh).rect(_der_la)), _der_cfg)
# **THE RULE IS ASSERTED, THE TABLE IS REPORTED — 12 September
# 2026.** This asserted `{1080p: 2, 1440p: 3, 2160p: 4}`, which was
# the INSTANCE the 8 September work bought by growing the list 29
# ref px. The static frame's list hole is 615 ref px where the
# Stage-A3 cutout was 649, and 1440p falls back to step 2: the
# band is 82 device px and step 3 needs 85. The list moved, which
# is exactly what the old message said to look for — and it moved
# because Data chose the frame, so it is a cost to report and not
# a fault to fail on.
#
# What survives is the DERIVATION itself, recomputed here from the
# masters' own measurement rather than read from `figure_step`:
# the step is the largest whose `28*step + 1` fits the band. A
# `figure_step` that returned anything else would be the fault
# this block exists for, and it still fails.
_need = (_ctk.FIGURE_TOP_NATIVE + 28 - _ctk.INK_BOTTOM_MIN)
for _rk, _got in _der.items():
    _rw, _rh = (int(v) for v in _rk.split("x"))
    _band = _ctk.band_height(
        pygame.Rect(*Layout(_rw, _rh).rect(_der_la)), _der_cfg)
    _want = max([_s for _s in _zt2.FIGURE_STEPS
                 if _need * _s <= _band] or [min(_zt2.FIGURE_STEPS)])
    assert _got == _want, (
        f"{_rk}: figure_step says {_got} and a band of {_band} "
        f"device px holds {_want} at {_need} master rows per step "
        f"(4 transcribed + 28 - 3 measured) — the derivation and "
        f"its own rule have parted")
report(f"figure steps, derived: {_der} | list {_lr['list'][3]} ref "
       f"px tall"
       + ("" if _der == {"1920x1080": 2, "2560x1440": 3,
                         "3840x2160": 4}
          else "  <-- NOT 2/3/4; the list is shorter than the "
               "638 box px 1440p needs for step 3"))
assert not hasattr(_zt2, "FIGURE_STEP"), (
    "the per-resolution FIGURE_STEP table is back; the step is "
    "derived from the row band (colonytrack.figure_step)")
assert "figure_scale" not in _lr, (
    "layout_reference.figure_scale is back — it was the same "
    "table in the design input and it is derived now")
for _spec, _dim in _zt2.INSET_DOT_DIM.items():
    assert _dim % 2 == 1, (
        f"{_spec}: a {_dim} px dot has no centre pixel, so the "
        f"computed star position cannot be its centre")
    # Rendered, then read back: place the dot by the module's own
    # origin rule and measure where its ink actually is.
    _cx, _cy = 40, 30
    _dot = pygame.Surface((80, 60))
    _dot.fill((0, 0, 0))
    _dot.fill((255, 255, 255), pygame.Rect(
        _zt2.inset_dot_origin(_cx, _dim),
        _zt2.inset_dot_origin(_cy, _dim), _dim, _dim))
    _arr = pygame.surfarray.array3d(_dot).sum(axis=2)
    _xs = [x for x in range(80) if _arr[x].any()]
    _ys = [y for y in range(60) if _arr[:, y].any()]
    assert (min(_xs) + max(_xs)) / 2 == _cx and \
           (min(_ys) + max(_ys)) / 2 == _cy, (
        f"{_spec}: a {_dim} px dot placed for centre "
        f"({_cx}, {_cy}) inks x {min(_xs)}..{max(_xs)} y "
        f"{min(_ys)}..{max(_ys)}, whose centre is "
        f"({(min(_xs) + max(_xs)) / 2}, {(min(_ys) + max(_ys)) / 2})")
    assert len(_xs) == _dim and len(_ys) == _dim
    # And it is the NEAREST odd number to the derivation, so the
    # table cannot drift from what Part 3 computed.
    _target = _zt2.INSET_DOT_TARGET[_spec]
    assert abs(_dim - _target) < 1.5 and \
        abs(_dim - _target) <= abs(_dim + 2 - _target) and \
        abs(_dim - _target) <= abs(_dim - 2 - _target), (
        f"{_spec}: {_dim} is not the nearest odd number to "
        f"{_target}")
# The original's own rule, which the HD one generalises.
assert _zt2.inset_dot_origin(50, 3) == 49, "movebox.cpp:103 is sx - 1"
ok("colony inset dot + figure step (odd by requirement, centred on "
   "the computed pixel at all three resolutions, nearest to the "
   "derivation, and the figure step matches layout_reference)")
