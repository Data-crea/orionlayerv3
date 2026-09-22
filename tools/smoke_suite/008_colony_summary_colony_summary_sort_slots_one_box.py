# smoke-suite area: colony_summary
#
# Part of the OrionLayer smoke suite — 008_colony_summary_colony_summary_sort_slots_one_box.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (91 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 8 check(s) it holds:
#   - colony_summary sort slots (one box per key, RETURN right of all seven, hit == the hole, highligh
#   - layout_reference._sort_slots is a pointer to layout.json and to colsum.cpp:267-273, not a second
#   - frame_holes names the frame's holes by overlap (two exchanged sort slots keep their own names)
#   - the seven sort slots are marked a DEVIATION at all five homes (module, namer, geometry, status, 
#   - every window sits inside its own hole in at resolutions ( windows, hole found by the component u
#   - the declared hole fill(s) are the artwork's own holes, re-derived from the alpha, and each cover
#   - the original's map rect is measured against the lower band, and a starmap placed elsewhere is a 
#   - colony_summary (cutouts == boxes.json [], the screen's boxes are the reference and not the file,


# ── Colony Summary (frame, cutouts, native click points) ──
d.switch_to("colony_summary")
cs = d.active
assert cs.GAME_SCREEN_ID == 20
import frame_holes as fh
_fh_no = fh.BOX_NAME
from screens.colony_summary import colonysort as _csort_mod
from screens.colony_summary import colonyheader as _chdr0
#: The original's seven sort fields, native x — the literals of
#: Add_Multi_Button_Field_(x, 446, ...) at colsum.cpp:267-273 in
#: ~/orion2re/src/game/colsum.cpp, so a retyped one fails. ONE
#: COPY: the injection check below and the `_sort_slots` pointer
#: check both read this.
NATIVE_X_SORT = {"name": 89, "population": 140, "food": 219,
                 "industry": 262, "science": 326, "producing": 393,
                 "bc": 480}
# ── THE CHAIN IS TWO LINKS: reference -> boxes.json ─────────
#
# Decision 3 asserted holes == mask == boxes because the artwork
# sat BETWEEN the rectangles and the boxes: a mask was rendered
# from the reference, a plate cut from the mask, and the boxes
# measured back out of the plate. Phase B deleted the middle —
# the frame is a fixed image that was drawn FIRST and the
# rectangles were measured off it — so what is left is that
# `boxes.json` IS the reference plus BLEED.
#
# **THIS IS A REPLACEMENT AND NOT A RELAXATION.** The old check
# compared three things that could disagree; this one compares two
# and is stricter about them — the whole file, byte for byte,
# rather than a rect at a time within the 2 px the round-trip
# through a PNG needed. And what the artwork used to guarantee is
# asserted separately and better: "every window sits inside its
# own hole", below, at three resolutions against the alpha.
# **NARROWED TO THE RECTS — 12 September 2026.** This compared
# `boxes.json` byte for byte against what a tool rebuilt from the
# reference, and that tool READ `boxes.json` for everything except
# the rects: role, style and the six columns were compared against
# themselves. The file carries no rectangle at all now — the
# fourteen cutouts and the six columns are derived at load by
# `colonyplates.reseat` — so what is left to assert is the thing
# that was ever really asserted, against the LIVE boxes.
from screens.colony_summary import colonyplates as _cpl
_boxes_path = os.path.join(SCREENS_DIR, "colony_summary",
                           "boxes.json")
import json as _bxjson
_boxes_raw = _bxjson.load(open(_boxes_path, encoding="utf-8"))
for _res, _blist in _boxes_raw.items():
    for _b in _blist:
        assert "rect" not in _b, (
            f"{_res}/{_b['name']} carries a rect in boxes.json. "
            f"The geometry is layout_reference.json's and is "
            f"seated at load; a rect here is a second copy that "
            f"nothing reads and nothing keeps current")
_derived_names = set(_cpl.box_rects(cs))
# THE PARTS INSIDE A WINDOW ARE VOCABULARY TOO — brief 95 Part C,
# 13 September 2026: `planet_disc` and `planet_paragraph` are typed
# in the reference under `planet_info_parts` and are not holes.
_vocab = (fh.RULE_NAMES["colony_summary"] | set(_chdr0.COLUMN_BOXES)
          | set(_cpl.part_rects(_cpl.reference(cs))))
assert _derived_names == _vocab, (
    f"the reference derives {sorted(_derived_names)} and the "
    f"screen's own vocabulary is {sorted(_vocab)}")
# AND THE SCREEN DOES NOT READ THE FILE IT WAS WRITTEN INTO.
# `colonyplates.reseat` rebuilds these rects at every load, so a
# reference edited without running the tool cannot leave a stale
# fill behind the frame — which it did, on the day that became
# possible. Asserted against the LIVE boxes, not against the file.
_live = {b.name: tuple(b.ref_rect) for b in cs.boxes}
for _bn, _br in _cpl.box_rects(cs).items():
    assert _live.get(_bn) == tuple(_br), (
        f"{_bn} is {_live.get(_bn)} on the screen and {tuple(_br)} "
        f"in layout_reference.json — reseat did not run, or ran "
        f"and something overwrote it")
_cut_note = (f"{len(_derived_names)} boxes from "
             f"layout_reference.json + {_cpl.BLEED} px")

# ── SEVEN SLOTS AGAIN, ONE BOX PER KEY ──────────────────────
#
# **DEVIATION, 12 September 2026, reversing "THE BAR IS ONE HOLE
# NOW" (Stage A3).** Stage A3 cut one `sort_bar` and put the
# division in `colonysort.layout`, on the reading that the
# original has ONE recessed strip with seven words laid along it.
# That reading is unchanged and is still what colsum.cpp says.
# What changed is the artwork: Data's frame cuts a slot per key
# and he places them by hand, so the division is geometry again.
# `layout_reference._sort_slots_note` carries the whole entry.
#
# "sort_bar.x == list_area.x" was settled and dropped on
# 11 September 2026 and does not come back per slot — the
# original's own strip starts 77 native px (231 reference) to the
# RIGHT of its list (Add_Multi_Button_Field_ at native x 89,
# colsum.cpp:267-273, against the first list field's
# Add_Hidden_Field_(12, y1, 101, y_row_end) at colsum.cpp:291),
# and where ours starts is Data's. Reported, not enforced.
#
# THE CITATION IS :267-273 AND NOT :265-271. The work order that
# asked for this said :265-271, and so did the comment that stood
# here; ~/orion2re/src/game/colsum.cpp puts the seven
# Add_Multi_Button_Field_ calls at 267-273 and RETURN's
# Add_Button_Field_(531, 445, ...) at 265, which is where the
# older number came from. doc/v3_orion2re_index.md:517 agrees.
_slots = {}
for _key in fh.SORT_KEYS:
    _name = _csort_mod.box_name(_key)
    assert _name in fh.SORT_BOX_KEYS, (
        f"colonysort.box_name({_key!r}) is {_name!r} and "
        f"frame_holes does not know that box — the two build the "
        f"same string from opposite ends and must not drift")
    _r = cs.box_rect(_name)
    assert _r, f"colony_summary has no {_name} box"
    _slots[_key] = _r
_la = cs.box_rect("list_area")
_ordered = sorted(_slots.items(), key=lambda kv: kv[1][0])
report(f"sort slots x {_ordered[0][1][0]}.."
       f"{_ordered[-1][1][0] + _ordered[-1][1][2]} | list_area x "
       f"{_la[0]} w {_la[2]} | the original's own offset is 231 "
       f"ref px (native 89 against 12)")
report("sort row gaps, ref px (the in_row divider measures 38): "
       + ", ".join(
           f"{_a[0]}->{_b[0]} {_b[1][0] - (_a[1][0] + _a[1][2])}"
           for _a, _b in zip(_ordered, _ordered[1:])))
# KEPT, and this one IS transcribed: the original draws RETURN as
# a separate raised plate to the right of the whole strip, native
# x 531 (Add_Button_Field_(531, 445, ...), colsum.cpp:265) against
# the last sort field ending at x_end 515 (live FIELD_LIST,
# orion2re 1.60, screen 20). It is now asserted against EVERY
# slot rather than against one bar's right edge — a per-box rule
# for a per-box layout, and the thing that catches a slot Data
# drags past RETURN.
#
# **THE RULE IS "NO SLOT OVERLAPS RETURN", NOT "EVERY SLOT ENDS
# LEFT OF IT"** — corrected 12 September 2026. The x-only form
# assumed RETURN is on the sort row, which is where the ORIGINAL
# puts it and where the Stage-A3 plate put it. Data's static frame
# puts RETURN in the right-hand column instead, above the row
# entirely, and the x-only rule called that an overlap when the
# two rectangles do not touch. What the check is for is that a
# click cannot land on two controls, and that is a 2-D question.
#
# The original's own relationship is REPORTED and keeps its
# source, because it is a transcription and losing it is how a
# deviation stops being visible: `Add_Button_Field_(531, 445, …)`
# at colsum.cpp:265, to the right of a strip ending at native
# x 515 (live FIELD_LIST, orion2re 1.60, screen 20).
_rb = cs.box_rect("return")
_rbr = pygame.Rect(*_rb)
for _key, _r in _ordered:
    assert not _rbr.colliderect(pygame.Rect(*_r)), (
        f"the {_key} slot {tuple(_r)} overlaps RETURN "
        f"{tuple(_rb)} — a click there would land on two "
        f"controls. Shrink the slot, never move RETURN")
_last = _ordered[-1]
report(f"RETURN at x {_rb[0]} y {_rb[1]} | the sort row ends at x "
       f"{_last[1][0] + _last[1][2]} y {_last[1][1] + _last[1][3]} | "
       f"the original puts RETURN on the row, to its right "
       f"(native x 531 against a strip ending at 515, "
       f"colsum.cpp:265)"
       + ("" if _last[1][0] + _last[1][2] <= _rb[0]
          else "  <-- NOT on the row's right: the artwork puts it "
               "elsewhere"))
# THE SLOTS DO NOT OVERLAP EACH OTHER EITHER. They are separate
# holes in a plate, so this is a property of the artwork and not
# of any arithmetic here — and two slots that overlap would give
# one key a hit rect it shares, where the FIRST in layout.json's
# order silently wins every click in the shared strip.
for (_ka, _ra), (_kb, _rb2) in zip(_ordered, _ordered[1:]):
    assert _ra[0] + _ra[2] <= _rb2[0], (
        f"the {_ka} and {_kb} slots overlap: {_ra} and {_rb2}")
# The seven keys, and the SAME function answers the renderer and
# the click test (decision 5).
_sb = cs._sort_buttons()
assert [b.key for b in _sb] == fh.SORT_KEYS, [b.key for b in _sb]
# **THE HIT RECT IS THE BOX.** Not a share of a bar: a click
# anywhere in a cut-out sorts by the key drawn in it.
for _b in _sb:
    _want = pygame.Rect(*cs.layout.rect(_slots[_b.key]))
    assert _b.hit == _want, (
        f"{_b.key}'s hit rect is {_b.hit} and its box is {_want} "
        f"— the hole is the button")
# **AND THE HIGHLIGHT IS THE WORD PLUS THE PAD, NOT THE BOX.**
# The transcription that had to survive the rewrite: the original
# lights a rectangle around the WORD (native 92..138 for ink at
# 94..136) inside a field that is wider (89..139), so the lit box
# grows with the word. Filling the slot would be one line shorter
# and would make all seven highlights the same width, which the
# original's never are. The tell is asserted rather than the
# construction: no two DIFFERENT words may light the same width.
_lit = {}
for _b in _sb:
    assert _b.hit.contains(_b.highlight), (
        f"{_b.key}'s highlight is outside the box that hits it")
    # Within a pixel: both edges are placed by integer division,
    # so an odd leftover puts the centres one apart and that is
    # the truncation and not a drift.
    assert abs(_b.highlight.centerx - _b.hit.centerx) <= 1, (
        f"{_b.key}'s highlight is not centred in its box: "
        f"{_b.highlight} in {_b.hit}")
    _lit[_b.label] = _b.highlight.width
_clamped = [b.key for b in _sb if b.highlight.width == b.hit.width]
assert len(set(_lit.values())) > 1, (
    f"all seven highlights are {sorted(set(_lit.values()))} px "
    f"wide — the lit box follows the WORD (colsum.cpp's own is "
    f"native 92..138 for 'Name'), and seven equal ones mean it "
    f"has quietly become the box")
report(f"sort highlights, window px at 1920x1080: "
       + ", ".join(f"{k} {v}" for k, v in sorted(_lit.items()))
       + (f" | clamped to the box: {_clamped}" if _clamped
          else " | none clamped to its box"))
ok("colony_summary sort slots (one box per key, RETURN right of "
   "all seven, hit == the hole, highlight == the word + pad)")

# ── `_sort_slots` IS A POINTER, NOT A SECOND COPY ───────────
#
# `layout_reference.json` types the seven rects, and beside each
# one it names the sort key, the label and the original's own
# field x — so somebody reading the geometry file knows which box
# is which without opening `layout.json`. That is a HAND-COPIED
# NUMBER IN A SECOND FILE, which is decision 36's whole subject
# and this project's most expensive recurring fault, so it gets a
# checker the same day it is written.
#
# The key and the label are held to `layout.json`, which is the
# one home for both; `native_x` is held to the source constants
# the injection check already asserts. And the ORDER is held too:
# the file lists them left to right, which is what makes reading
# it beside the picture possible at all.
_slot_meta = _lr_slots = app.res.load_json(
    "screens/colony_summary/layout_reference.json", {}).get(
        "_sort_slots", {})
assert list(_slot_meta) == fh.SORT_BOX_KEYS, (
    f"layout_reference._sort_slots lists {list(_slot_meta)}, the "
    f"boxes are {fh.SORT_BOX_KEYS} — same seven, same order")
for _bname, _meta in _slot_meta.items():
    _key = _meta["key"]
    assert _csort_mod.box_name(_key) == _bname, (_bname, _key)
    _btn = next(b for b in cs._data["sort"]["buttons"]
                if b["key"] == _key)
    assert _meta["label"] == _btn["label"], (
        f"{_bname}'s label is {_meta['label']!r} here and "
        f"{_btn['label']!r} in layout.json — layout.json is the "
        f"home, this is the pointer")
    assert _meta["native_x"] == NATIVE_X_SORT[_key], (
        f"{_bname}'s native_x is {_meta['native_x']}, the original's "
        f"field is at {NATIVE_X_SORT[_key]} (colsum.cpp:267-273)")
    assert _meta["native_x"] <= _btn["native_click"][0] <= \
        _meta["native_x"] + 12, (
        f"{_bname}'s injection point is outside the field it names")
_slot_x = [cs.box_rect(_n)[0] for _n in _slot_meta]
assert _slot_x == sorted(_slot_x), (
    f"layout_reference lists the slots in the order {list(_slot_meta)} "
    f"and their x are {_slot_x} — the file is read beside the "
    f"picture, so the order is left to right")
ok("layout_reference._sort_slots is a pointer to layout.json and "
   "to colsum.cpp:267-273, not a second copy")

# ── A SWAPPED SLOT KEEPS ITS NAME ───────────────────────────
#
# The reason the namer matches by OVERLAP and not by order. Seven
# hand-placed holes in one row is a lot of chances to drag one
# past its neighbour, and an index-based namer answers that
# silently: PRODUCING would sort by science and every other thing
# on the screen would still be right. This project already paid
# for that once, with the last two bottom panels the wrong way
# round for a fortnight (`layout.json`, `panels._note`).
#
# Asserted by MOVING THE RECTANGLES rather than by reading the
# code: two slots are exchanged in a copy of the reference, a
# plate is rendered from it, and each name has to come back on
# the hole the reference now puts it on.
# Asserted by MOVING THE RECTANGLES rather than by reading the
# code, and against the REAL FRAME — it used to build a plate from
# the galaxy master with a swapped reference, which needed
# `frame_build` and `frame_cut` and is gone with them. The holes
# are the artwork's own; what is swapped is the geometry handed to
# the matcher, which is the actual case: Data moves two slots in
# GIMP and `layout_reference.json` moves with them.
_sw_w, _sw_h, _sw_holes = fh.find_holes(
    res.screen_file("colony_summary", "assets", "frame.png"))
_sw_ref = dict(fh.reference_windows("colony_summary",
                                    (_sw_w, _sw_h)))
_sw_lr = app.res.load_json(
    "screens/colony_summary/layout_reference.json", {}) or {}
_a, _b = fh.SORT_BOX_KEYS[1], fh.SORT_BOX_KEYS[4]
_sw_ref[_a], _sw_ref[_b] = _sw_ref[_b], _sw_ref[_a]
_sw_named = fh.name_holes(_sw_holes, "colony_summary",
                          (_sw_w, _sw_h), _sw_ref)
assert "overlap" in (fh.LAST_MATCH or ""), fh.LAST_MATCH
# AND ORDER WOULD HAVE GOT IT WRONG, which is what makes this a
# test: the second slot from the left is where `sort_population`
# sits, and an index-based namer calls it that because it is
# second. It has to come back as the key the geometry now puts
# there.
# THE BOTTOM ROW IS EIGHT HOLES SINCE 12 September 2026 — the
# seven keys and RETURN, which took the eighth slot the evening
# Data's frame cut one for it. Counted against the rule's own
# names for that row rather than against `SORT_KEYS`, which is
# seven and is not what the row holds.
_sw_row = sorted((tuple(_r) for _r in _sw_holes
                  if _r[1] > 0.85 * _sw_h), key=lambda _r: _r[0])
_sw_want = len(fh.SORT_KEYS) + (
    0 if "return_button" in _sw_lr.get(
        "_windows_without_a_hole", ()) else 1)
assert len(_sw_row) == _sw_want, (
    f"{len(_sw_row)} holes in the artwork's bottom row, "
    f"{len(fh.SORT_KEYS)} sort keys and "
    f"{_sw_want - len(fh.SORT_KEYS)} for RETURN")
_sw_at = {tuple(_r): _n for _n, _r in _sw_named.items()}
assert _sw_at[_sw_row[1]] == _b, (
    f"the second slot from the left came back as "
    f"{_sw_at[_sw_row[1]]!r}; the swapped geometry puts {_b!r} "
    f"there and {_a!r} is the name an INDEX would have given it")
assert _sw_at[_sw_row[4]] == _a, (
    f"the fifth slot came back as {_sw_at[_sw_row[4]]!r}, not "
    f"{_a!r} — the swap has to be followed in both directions")
ok("frame_holes names the frame's holes by overlap (two exchanged "
   "sort slots keep their own names)")


# ── THE SLOTS ARE A MARKED DEVIATION, AT EVERY HOME ─────────
# Reversing a recorded decision is itself a decision, and the
# rule is that a deviation is marked in the source, in the docs
# and in a check. This is the check; it names the homes so one
# that quietly loses its paragraph fails here.
for _home, _txt in (
        ("colonysort.py", open(os.path.join(
            SCREENS_DIR, "colony_summary", "colonysort.py"),
            encoding="utf-8").read()),
        ("tools/frame_holes.py", open(os.path.join(
            os.path.dirname(SCREENS_DIR), "tools", "frame_holes.py"),
            encoding="utf-8").read()),
        ("layout_reference.json", app.res.load_json(
            "screens/colony_summary/layout_reference.json", {}).get(
                "_sort_slots_note", "")),
        ("v3_projektstatus.md", open(os.path.join(
            os.path.dirname(SCREENS_DIR), "v3_projektstatus.md"),
            encoding="utf-8").read()),
        ("doc/v3_fundament.md", open(os.path.join(
            os.path.dirname(SCREENS_DIR), "doc", "v3_fundament.md"),
            encoding="utf-8").read()),
        ):
    assert "DEVIATION" in _txt and "sort_bar" in _txt, (
        f"{_home} does not mark the seven sort slots as a DEVIATION "
        f"naming the sort_bar it reverses")
ok("the seven sort slots are marked a DEVIATION at all five homes "
   "(module, namer, geometry, status, fundament)")

# ── EVERY WINDOW SITS INSIDE ITS OWN HOLE, AT EVERY SIZE ────
#
# **THE CHECK THE STATIC FRAME NEEDS** — 12 September 2026. The
# plate was GENERATED from these rectangles, so "the box is inside
# the hole" was true by construction and nothing had to ask. The
# screen wears a FIXED image now: the holes were drawn by hand
# long before these rectangles were typed, and the only thing
# holding the two together is that somebody measured one from the
# other. This is what re-measures it, off the alpha, at every
# shipped resolution rather than at 1080p alone — the boxes are
# placed by `Layout.rect`'s truncation and the frame by
# `smoothscale`, and the two roundings are not the same one.
#
# THE HOLE IS FOUND, NOT ASSUMED: the transparent component the
# window's own centre falls in, and its bounding box. That is
# immune to the artwork's rounded corners, which are real —
# `tools/colony_frame_check.py` reports all fourteen holes as
# non-rectangular on this file, by 80 to 2172 px each — and which
# a per-pixel test would fail on while nothing was wrong. What is
# asserted is containment of the RECT in the hole's extent, with
# `BLEED` of tolerance, which is the thing the bleed exists for.
_hole_png = res.screen_file("colony_summary", "assets", "frame.png")
assert _hole_png and os.path.exists(_hole_png), (
    "screens/colony_summary/assets/frame.png is gone — it is the "
    "frame this screen wears and the artwork every rectangle in "
    "layout_reference.json was measured off")
if True:
    from scipy import ndimage as _hnd
    import numpy as _hnp
    from PIL import Image as _hPIL
    from screens.colony_summary import colonyplates as _hcpl
    _hlr, _hwins = _hcpl.load_reference(
        _hcpl.reference_path(os.path.dirname(SCREENS_DIR)))
    _halpha = _hnp.array(_hPIL.open(_hole_png).convert(
        "RGBA"))[:, :, 3]
    _hb = _cpl.BLEED
    _worst = {}
    for _hspec in _hlr["_resolutions"]:
        _hw, _hh = (int(v) for v in _hspec.split("x"))
        # NEAREST, so a resample cannot invent an alpha between
        # metal and hole — the same reason `frame_cut` never reads
        # a scaled artwork's own black.
        _hs = _hnp.array(_hPIL.fromarray(_halpha).resize(
            (_hw, _hh), _hPIL.NEAREST))
        _hlab, _hn = _hnd.label(_hs < 16)
        _hobj = _hnd.find_objects(_hlab)
        _hlay = Layout(_hw, _hh)
        _hskip = set(_hlr.get("_windows_without_a_hole", ()))
        for _hname, _hrect in _hwins.items():
            # A DECLARED NO-HOLE WINDOW IS NOT MEASURED HERE, and
            # saying so is not the same as passing it. The header
            # is a band of the list's hole and RETURN has none at
            # all — it is drawn OVER the frame, which is Data's
            # decision of 12 September 2026 and the reason it is
            # the one FREE box in the editor. The rule that
            # applies to it instead is "inside the window", below.
            if _hname in _hskip:
                continue
            _hx, _hy, _hww, _hhh = _hlay.rect(_hrect)
            _hcx, _hcy = _hx + _hww // 2, _hy + _hhh // 2
            _hid = int(_hlab[_hcy, _hcx])
            assert _hid, (
                f"{_hspec}: the centre of {_hname} at "
                f"({_hcx}, {_hcy}) is METAL — the window is not "
                f"over a hole at all")
            _hys, _hxs = _hobj[_hid - 1]
            _htol = max(1, round(_hb * _hlay.scale))
            _hover = (_hxs.start - _hx, (_hx + _hww) - _hxs.stop,
                      _hys.start - _hy, (_hy + _hhh) - _hys.stop)
            assert max(_hover) <= _htol, (
                f"{_hspec}: {_hname} at "
                f"{(_hx, _hy, _hww, _hhh)} leaves its hole "
                f"{(int(_hxs.start), int(_hys.start), int(_hxs.stop - _hxs.start), int(_hys.stop - _hys.start))} "
                f"by l/r/t/b {_hover}, over the {_htol} px of "
                f"bleed the content is allowed to hide behind")
            _worst[_hname] = max(_worst.get(_hname, -99),
                                 max(_hover))
    # AND HOW DEEP THE ARTWORK'S OWN CORNER REACHES, reported:
    # the inset at which a window's rect becomes wholly
    # transparent. It is 7 device px at 1080p and 14 at 2160p on
    # this frame — the rounding of hand-drawn holes — and it is
    # what a content renderer has to keep its corners clear of.
    # ── AND THE ONES WITH NO HOLE ARE INSIDE THE WINDOW ─────
    for _hname in sorted(_hskip):
        _hr = _hwins[_hname]
        assert (_hr[0] >= 0 and _hr[1] >= 0
                and _hr[0] + _hr[2] <= 1920
                and _hr[1] + _hr[3] <= 1080), (
            f"{_hname} at {_hr} leaves the 1920x1080 reference "
            f"area — it has no hole to be inside, so this is the "
            f"only geometry rule it has")
    report("no hole, checked against the window instead: "
           + ", ".join(f"{_n} {_hwins[_n]}" for _n in sorted(_hskip)))
    report("windows inside their holes, worst overhang per box "
           "(ref px, bleed is " + str(_hb) + "): "
           + ", ".join(f"{_k} {_v:+d}" for _k, _v
                       in sorted(_worst.items(), key=lambda kv: -kv[1])
                       [:4]))
    ok(f"every window sits inside its own hole in "
       f"{os.path.basename(_hole_png)} at "
       f"{len(_hlr['_resolutions'])} resolutions "
       f"({len(_hwins)} windows, hole found by the component "
       f"under each window's centre)")

    # ── AND THE ONE HOLE THAT IS BIGGER THAN ITS WINDOW ────
    #
    # `galaxy_inset` keeps the original's coverage aspect
    # (movebox.cpp:20-21) inside a hole Data drew wider, so part
    # of the cutout has no box over it and would show the
    # screen's background through the frame. What goes there is
    # the panel's own black, over `_galaxy_inset_hole`, and that
    # rect is a hand-copied number — so it gets a checker
    # (decision 36). RE-DERIVED HERE FROM THE ALPHA rather than
    # compared to a second literal: the component under the
    # window's centre, its bounding box, scaled by the same
    # factors the frame is blitted with, floored on the near
    # edges and ceiled on the far ones so the fill covers every
    # pixel of the hole.
    _hh_panels = (_json.load(open(os.path.join(
        SCREENS_DIR, "colony_summary", "layout.json"),
        encoding="utf-8")).get("panels", {}))
    _hh_declared = _hcpl.hole_rects(_hlr)
    assert _hh_declared, (
        "layout_reference.json declares no `_hole_<window>` at "
        "all — galaxy_inset's hole is 34 ref px wider than its "
        "box and something has to fill the difference")
    _hh_lab, _ = _hnd.label(_halpha < 16)
    _hh_objs = _hnd.find_objects(_hh_lab)
    _hh_ny, _hh_nx = _halpha.shape
    _hh_seen = []
    for _hh_box, _hh_rect in _hh_declared.items():
        _hh_win = next(_n for _n, _r in _hwins.items()
                       if _hcpl.BOX_NAME.get(_n, _n) == _hh_box)
        _hx, _hy, _hw2, _hh2 = _hwins[_hh_win]
        _hh_cx = int((_hx + _hw2 / 2) * _hh_nx / 1920)
        _hh_cy = int((_hy + _hh2 / 2) * _hh_ny / 1080)
        _hh_id = int(_hh_lab[_hh_cy, _hh_cx])
        assert _hh_id, (
            f"{_hh_win}'s centre is METAL in the artwork — a "
            f"declared hole for a window that has none")
        _hh_ys, _hh_xs = _hh_objs[_hh_id - 1]
        _hh_want = [
            int(_hh_xs.start * 1920 / _hh_nx),
            int(_hh_ys.start * 1080 / _hh_ny),
            -(-int(_hh_xs.stop) * 1920 // _hh_nx)
            - int(_hh_xs.start * 1920 / _hh_nx),
            -(-int(_hh_ys.stop) * 1080 // _hh_ny)
            - int(_hh_ys.start * 1080 / _hh_ny)]
        assert _hh_rect == _hh_want, (
            f"_hole_{_hh_win} says {_hh_rect} and the alpha of "
            f"{os.path.basename(_hole_png)} says {_hh_want} — "
            f"the artwork moved and the black behind the box did "
            f"not follow it")
        # AND IT COVERS THE BOX, which is what makes laying it
        # first legitimate: the panel fill is drawn over it.
        _hh_bl = _hcpl.bled(_hh_rect)
        _hh_bw = _hcpl.bled(_hwins[_hh_win])
        assert (_hh_bl[0] <= _hh_bw[0] and _hh_bl[1] <= _hh_bw[1]
                and _hh_bl[0] + _hh_bl[2] >= _hh_bw[0] + _hh_bw[2]
                and _hh_bl[1] + _hh_bl[3] >= _hh_bw[1] + _hh_bw[3]), (
            f"the hole fill {_hh_bl} does not cover "
            f"{_hh_win} {_hh_bw} — the box would paint outside "
            f"the black instead of on it")
        _hh_seen.append(
            f"{_hh_win} box {_hw2}x{_hh2} in hole "
            f"{_hh_rect[2]}x{_hh_rect[3]}, remainder "
            f"{_hh_rect[2] - _hw2} x {_hh_rect[3] - _hh2} ref px "
            f"painted "
            f"{_hh_panels.get(_hh_box) if isinstance(_hh_panels.get(_hh_box), str) else 'panel_background'}")
    report("holes wider than their window: " + "; ".join(_hh_seen))
    ok(f"the {len(_hh_declared)} declared hole fill(s) are the "
       f"artwork's own holes, re-derived from the alpha, and each "
       f"covers its window")
# WHERE THE ORIGINAL PUTS ITS MAP, AND WHERE DATA PUT OURS ──
#
# This ASSERTED that whichever bottom box lands nearest the
# original's own map rect is the one called `galaxy_inset`, and
# decisively so. It was written because the name was assigned by
# index until 4 September 2026 and was on the wrong hole the whole
# time (the same failure as the field dump that labelled
# _races_button "Research").
#
# **IT IS A REPORTED DEVIATION SINCE 12 September 2026, and that
# is Data's decision about his own frame.** The new frame's lower
# band is four boxes; he mapped box 3 to `empire_stats` and box 4
# to `galaxy_inset`, and box 3 is the one the original's map rect
# falls in. The source is unchanged and is still measured here —
# what changed is that the answer is now a placement somebody
# made rather than a name somebody could get wrong.
#
# The original draws its small galaxy map with
# MOVEBOX::Draw_Galaxy_Map_Box_(nullptr, 0, 0x17c, 0x15d, 0x80,
# 0x5b, ...) at colsum.cpp:415 — x_base 380, y_base 349, width
# 128, height 91 of 640x480 (movebox.cpp:4-9), confirmed by
# Colsum_Connect_Galaxy_Map_Stars_ passing the same four to
# Get_Galaxy_Map_Star_XY_ (colsum.cpp:734-735). The native
# numbers are literals here so a retyped one fails.
_GMAP_NATIVE = (380, 349, 128, 91)          # colsum.cpp:415
from core.config import REF_W as _GREF_W, REF_H as _GREF_H
_gsx, _gsy = _GREF_W / 640.0, _GREF_H / 480.0
_gref = (_GMAP_NATIVE[0] * _gsx, _GMAP_NATIVE[1] * _gsy,
         _GMAP_NATIVE[2] * _gsx, _GMAP_NATIVE[3] * _gsy)
_gref_cx = _gref[0] + _gref[2] / 2.0
_pan = []
for _k in fh.BAND_KEYS:
    _r = cs.box_rect(_k)
    assert _r is not None, f"colony_summary has no {_k} box"
    _pan.append((abs(_r[0] + _r[2] / 2.0 - _gref_cx), _k))
_pan.sort()
report(f"the original's map rect is reference centre x "
       f"{_gref_cx:.0f} (native {_GMAP_NATIVE}, colsum.cpp:415); "
       f"the nearest bottom box is {_pan[0][1]} at "
       f"{_pan[0][0]:.0f} px, galaxy_inset is at "
       f"{next(d for d, k in _pan if k == 'galaxy_inset'):.0f}")
# **AND THE DEVIATION IS MARKED, which is what makes it a decision
# rather than a drift.** If the map is not in the box the original
# puts it in, the reason has to be written where somebody reading
# the geometry will meet it.
if _pan[0][1] != "galaxy_inset":
    _gm_note = app.res.load_json(
        "screens/colony_summary/layout_reference.json", {}).get(
            "_geometry_source", "")
    assert "DEVIATION" in _gm_note and "colsum.cpp:415" in _gm_note, (
        f"the nearest bottom box to the original's map rect is "
        f"{_pan[0][1]!r} and not galaxy_inset, and "
        f"layout_reference._geometry_source does not mark that as "
        f"a DEVIATION citing colsum.cpp:415")
ok("the original's map rect is measured against the lower band, "
   "and a starmap placed elsewhere is a marked deviation")

# Every button injects a click INSIDE the original's button
# (colsum.cpp:265-273): the x is the field's left edge plus a
# margin, the y sits in the 446 row. Asserting the source
# constants rather than "some point", so a retyped number fails.
NATIVE_X = NATIVE_X_SORT
HOTKEY = {"name": "n", "population": "p", "food": "f",
          "industry": "i", "science": "s", "producing": "r",
          "bc": "b"}
btns = {b["key"]: b for b in cs._data["sort"]["buttons"]}
assert list(btns) == fh.SORT_KEYS, list(btns)
for key, b in btns.items():
    nx, ny = b["native_click"]
    assert NATIVE_X[key] <= nx <= NATIVE_X[key] + 12, (key, nx)
    assert 446 <= ny <= 460, (key, ny)
    assert b["hotkey"] == HOTKEY[key], (key, b["hotkey"])
rx, ry = cs._data["return"]["native_click"]
assert 531 <= rx <= 545 and 445 <= ry <= 459, (rx, ry)

# The empire rows name only verified s_player fields, in the
# order Draw_Empire_Info_ prints them.
from core.structs import player as _ps
_fields = [f[0] for f in _ps.SPEC.fields]
rows = [r["field"] for r in cs._data["empire"]["rows"]]
assert rows == ["bc", "surplus_bc", "total_pop", "surplus_freighters",
                "surplus_food", "research_produced"], rows
assert all(f in _fields for f in rows), rows

# Clicking a sort button records the key and sends the ORIGINAL'S
# OWN HOTKEY, not a click. Both paths live in `_inject` and the
# difference between them is invisible on screen — a click sorts
# the game correctly too, and additionally drags its pointer onto
# the button (platform.cpp:1171-1172). So the path is asserted
# here rather than left to a live session to notice.
class _Cap:
    def __init__(self): self.calls = []; self.keys = []
    def inject_click(self, x, y): self.calls.append((x, y))
    def activate_field(self, f): pass
    def inject_key(self, k): self.keys.append(k)
cap = _Cap()
app.client, was = cap, app.connected
app.connected = True
_food = next(b for b in cs._sort_buttons() if b.key == "food")
cs.handle_click(_food.hit.centerx, _food.hit.centery)
assert cs._sort_key == "food"
assert cap.keys == [ord(HOTKEY["food"])], (cap.keys, HOTKEY["food"])
assert cap.calls == [], (
    f"a sort button injected a click at {cap.calls} as well as (or "
    f"instead of) its hotkey — the click path is the FALLBACK now, "
    f"and taking both moves the game's pointer for nothing")
# ── ENTERING THE SCREEN SETS THE GAME'S SORT ──
# _g_sort_index is not on the wire, so the two lists could sit on
# different keys with neither being wrong — the first real
# side-by-side found exactly that. Rather than ask for it to be
# serialised, HD imposes its own key once on entry and every
# later change goes through handle_click, so they agree by
# construction. Idempotent: Switched_cmp_ has no toggle
# (colsum.cpp:378-401), so re-sorting by the key the game already
# holds re-sorts identically.
cap.calls.clear(); cap.keys.clear()
cs.enter(None)
assert cap.keys == [ord(HOTKEY[cs._sort_key])], (
    f"entering the screen sent {cap.keys} — it must push its own "
    f"sort key {cs._sort_key!r} to the game, because nothing on "
    f"the wire reports the game's")
assert cap.calls == [], (
    f"the entry sort used the click path ({cap.calls}); it takes "
    f"the hotkey like every other sort")
# And it is the DEFAULT from layout.json, not a hardcoded key.
assert cs._sort_key == cs._data["sort"]["default"], (
    "the entry sort key is not layout.json's default")
cap.calls.clear(); cap.keys.clear()

# RETURN has no letter to press: its field carries 0x25. It keeps
# the native_click, and this asserts the fallback still works —
# a hotkey path that swallowed every button would look identical
# on the sort bar and break the only way off the screen.
cap.calls.clear(); cap.keys.clear()
rbx, rby, rbw, rbh = cs.layout.rect(cs.box_rect("return"))
cs.handle_click(rbx + rbw // 2, rby + rbh // 2)
assert cap.calls == [tuple(cs._data["return"]["native_click"])], \
    cap.calls
assert cap.keys == [], cap.keys
assert "hotkey" not in cs._data["return"], (
    "RETURN grew a hotkey — field 14 reports 0x25, which is not a "
    "key a player presses; if this is deliberate, verify it live "
    "the way the sort keys were before trusting it")
# The click path is the fallback, so its points must SURVIVE.
# Deleting them once the hotkey works is the failure this guards:
# they are the half that can be checked by a grep against
# colsum.cpp:265-273 with no game running.
for key, b in btns.items():
    assert "native_click" in b, (
        f"sort button {key!r} lost its native_click — the hotkey "
        f"path does not replace it, it precedes it")
app.client, app.connected = FakeClient(), was
cs.render(pygame.display.get_surface())
ok(f"colony_summary (cutouts == boxes.json [{_cut_note}], the "
   f"screen's boxes are the reference and not the file, native "
   f"clicks kept as the fallback, empire rows)")
