# 146 — Fleets: build in the new frame (progress)

## The source

One match: `~/Downloads/fleets_frame_v4.png`, **950 116 bytes,
1445 x 811, RGBA**, sha256
`4667e86d1405555d1cddce1b5647c3ced43141bf2a2efe5260de29dab6c1b198`.
Copied to `evidence/work_order_146/` and **shipped unmodified** as
`screens/fleets/assets/frame.png` — same sha256. Not resized: the
frame is stretched over the reference area by `_scale_frame` anyway,
so resizing would only resample Data's art, which the order forbids.
(1445/811 = 1.7818 is also not 16:9, so a resize to 1920x1080 would be
very slightly anisotropic.)

## 1. Measured

**Alpha.** Three distinct values; 45.64 % at 0, 54.35 % at 255, **102
partial pixels (0.01 %)**. **No RGB under alpha 0** — every
transparent pixel is exactly (0,0,0,0), so the `BLEND_RGB_ADD` hazard
does not apply. The 102 partial pixels carry RGB (239,239,239) against
a body of (39.6,39.1,38.9): the same white-key fringe 145 found in
`inner_frame.png`, at a thirtieth the size.

**Thirty-two holes — the expected inventory verifies exactly**, and
the count was taken, not trusted:

| what | holes | source px |
|---|---|---|
| minimap | 1 | (117, 80, 646, 392) |
| arrow bar | 3 | (117,507,68,41) (211,507,460,41) (697,507,66,41) |
| text panel | 1 | (117, 574, 646, 142) |
| ship cells | 20 | 86x81, x {850,956,1062,1168}, y {81,180,279,378,477} |
| controls | 7 | two rows, y≈589 and y≈671 |

The grid is **perfectly regular** — column pitch 106, row pitch 99,
every cell 86x81 — which confirms the regularisation from one template
cell. No specks: the smallest hole is 2498 px², above `MIN_AREA`.

**Which hole is which, from source.** Every name is one
`fltwire.CONTROL_ORIGINS` already knows by its `flt1.cpp` line, so the
frame and the wire share one vocabulary.

* **The three arrow-bar fields are PREV | status text | NEXT.**
  `fltgeom.REGIONS["status_band"]` cites evanhelp.cpp:154-157 — help
  363 the status text, 364 PREV, 365 NEXT — and `CONTROL_ORIGINS` puts
  `prev_fleet` at native (19, 249) and `next_fleet` at (283, 249)
  (flt1.cpp:1217-1218). The middle field is where
  `FLT2::Print_Fltscrn_Scanned_Star_Name_` prints (flt2.cpp:521).
  **Confirmed against the native screen**: `LIVE_side_by_side_save4.png`
  shows ◄ | long field | ► in exactly that order.
* Buttons row 1 = All, Relocate, Scrap (flt1.cpp:1195, :1229, :1187);
  row 2 = Leaders, Support, Combat, Return (:1234, :1256, :1257,
  :1201). Confirmed by order AND by width — Support and Combat are the
  two narrow holes (82 and 86 px), as they are the two narrow controls
  natively.

**The scroll bar is painted, not a hole.** Measured on the artwork:
housing x 1275..1308 (rails 1275-1280 and 1302-1308, dark channel
between), **up arrow y 76..123, track y 124..512, down arrow y
513..564**. `fltgeom.SCROLL_V4_COLUMN` and `SCROLL_PARTS` carry those
numbers and a smoke check asserts the whole column is opaque — if the
bar ever became a cutout, the measurement would be stale and the check
says so.

## 2. Integrated

**Through `tools/frame_holes.py`**, which is what the tree already
does for the galaxy map, rather than `fleet_boxes.py`, which seated
native rectangles into the v3 frame's single opening. A new
`name_holes_fleets` rule names the 32 holes **positionally and
refuses anything else** — wrong count, no group of 20 equal cells, a
grid that is not 4x5, the wrong number left of the grid. `--write`
generated the boxes and kept the six non-cutout boxes verbatim
(decision 3).

**Boxes that changed skin — 16, all to `none`:** `inset_map`,
`ship_panel`, `prev_fleet`, `status_band`, `next_fleet`, `btn_all`,
`btn_relocate`, `btn_scrap`, `btn_leaders`, `btn_support`,
`btn_combat`, `btn_return`, plus the four structural leftovers
`icon_area`, `button_band`, `status_text`, `scroll_column`.

**`skin: "none"` is new in `core/box.py`** and had to be: removing
`style` is not enough, because the default is `"panel"` — which is
exactly what appeared inside the holes the first time, a filled panel
with its own chamfered outline along every rail.

**The ship grid.** `fltdraw.icon_slots` now reads `cell_00`..`cell_19`
and computes nothing. Render and hit-test share it as before —
`draw_cells` for the picture, `screen._slot_at` for the click — so
decision 5 holds with the geometry now being the artwork's. A smoke
check asserts every box equals its hole plus BLEED.

**The minimap fit, against the galaxy and not a screenshot.** All four
galaxy sizes normalise to the same extent: `(MAP_MAX * 1000 // scale)
* 10` is **506000 x 400000** for Small 506x400@10, Medium 759x600@15,
Large 1012x800@20 and Huge 1518x1200@30, which is exactly
`INSET_SCALE_X/Y`. So the fit is one answer for every galaxy size:

| | aspect | stretch of the galaxy's own 1.265 |
|---|---|---|
| v4 hole 646x392 | 1.6480 | 1.303x |
| the original's inset box 305x182 | 1.6758 | 1.325x |

**1.66 % apart.** Both stretch — that is the original's doing, not
ours — and HD now stretches it very slightly *less* than the original.

## 3. Content fit, rendered not estimated

| resolution | cell | longest plausible name | worst case |
|---|---|---|---|
| 1080p | 118x112 | "Doom Star Alpha" at size 13 | 15 widest glyphs **clip** |
| 1440p / ultrawide | 157x149 | size 18 | size 10, fits |
| 2160p | 236x224 | size 27 | size 15, fits |

Real names ("Scout", "Katana") draw at full size everywhere. **No
button label overflows at any resolution** after the shrink. The only
clipping is 15 consecutive widest glyphs at 1080p, which no ship name
in the game produces.

**The doubled Support/Combat label was real, and here is why.**
FLEET.LBX entries 9 and 10 are whole BUTTONS — border, lit field and
the words "Support"/"Combat" baked into the pixels
(`Add_Radio_Button_Field_`, flt1.cpp:1255-1256). Work order 142 blitted
the lit face and then drew HD's own label on top: the word twice,
offset, and under v4's narrower hole the baked word overflowed the
blue field as well. Fixed by drawing **only the field** — colour
`radio_on` (8,8,80), measured from that very frame, palette 0xA1 —
with HD's label on top. Under v4 the border is the frame's, so a whole
button blitted into a hole was the wrong shape twice over.

Two more found by rendering: the ship panel's first line was **covered
by the frame's chamfer** (the frame draws last), fixed by
`CONTENT_INSET_SRC` — the chamfer measured per hole, 5..14 source px,
with a smoke check that re-derives it from the artwork and fails both
if it is too small and if it is larger than the chamfer needs. And
`draw_slots` no longer draws a cell edge: the hole has one.

## 4. Marked and checked

The frame is marked an **HD INVENTION** in `fltgeom`, in
`layout.json`'s `frame._note` and in `v3_projektstatus.md`, and a
smoke check fails if either marking disappears. The native screen is
flat plates with a "FLEET OPERATIONS" title bar and no such frame —
visible in `LIVE_side_by_side_save4.png`.

**Two checks were replaced, not deleted** (both were about the v3
one-opening frame and could not survive v4): "the frame cuts exactly
one hole equal to `frame.opening`" became the 32-hole block above, and
"every box lies inside that opening" became "every box lies in the
reference area, every derived box equals its hole, and the scroll
column lands on the painted bar". A third, the class-B intrusion
budget, now accepts a **declared** chamfer instead of the flat 2 px —
and asserts the declaration covers the intrusion, which is stronger
than the budget was.

## Live

Protocol held: **exactly one client** (checked before connecting; none
was attached), engine left running, **SAVE8 untouched**, SAVE1-6, 9
and 11 **byte-identical before and after**, SAVE10 logged only and
unchanged. SAVE4 loaded by clicking through the HD GAME menu.

`btn_return` fired **from its new hole-derived position (1670, 924)**
and the game changed screen — the live proof that the derived geometry
drives the original. Fleets opened with **no `original shown` line
between** the click and `HD draws: fleets`, so the WAITING state still
holds with the new frame.

Screenshots: see parked question 3 — the compositor could not present
a window, so F8 was added and the live pictures come from the surface
itself.

## Evidence

`fleets_frame_v4.png` (the source), `fleets_{art,noart}_*.png` at four
resolutions, `LIVE_hd_fleets_save4.png`,
`LIVE_native_fleets_save4.png`, `LIVE_side_by_side_save4.png`,
`RINGS_side_by_side.png`.
