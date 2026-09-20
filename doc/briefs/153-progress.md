# Work Order 153 — progress

Unattended run, 20 September 2026. One commit per part.
Questions and the one missing input are in `153-parked-for-data.md`.

---

# Part A — the new layout

## What was built

`tools/fleets_frame_reshape.py` (new), called by
`tools/fleets_frame_build.py` between the unlit rebuild of Support and
Combat and the cut of the 32 openings. The source
(`_src/fleets_frame_4k_map165.png`, sha256 `92f89a86…`) is unchanged
and still verified before anything is written; the build is
reproducible byte for byte (two runs, `c8a2ec75…` both times).

Order of the three steps, and why:

1. **unlit** first, on the pristine source — every constant in
   `_unlit` is a measurement of the art as painted, and reshaping
   first would leave all of them pointing at something else.
2. **reshape**.
3. **cut**, then `_check_targets`, which refuses the build if a hole
   did not come out at the figure the order gives.

## The transform

A piecewise-linear remap of each axis. A segment is either an ANCHOR,
copied pixel for pixel, or an ELASTIC run, resampled (LANCZOS). Every
corner, chamfer, rivet, bracket and V-notch is in an anchor.

**Rows 153..1987 only.** Outside them is the outer ring and the two
full-width bars just inside it, which the order leaves alone. Measured:
across x 500..3615 the largest one-pixel horizontal step is 8.3 grey
levels at row 152 and ≤3.3 at rows 153..169, and ≤3.3 at 1975..1987
against 9.3 at 1988. The band ends where the ring's own edge begins.

**Vertical**, on columns 175..2080 (the left column and the plain
chassis right of it; the right column does not change height):

| rows | what is there | out |
|---|---|---|
| 153..330 | the map's top border and its two top brackets | 177, anchor |
| 330..1190 | **elastic** — inside the map, between the brackets | 665 (−195) |
| 1190..1658 | the map's bottom brackets, the three small boxes, the chassis, the panel's top brackets | 468, anchor, sliding up 195 |
| 1658..1815 | **elastic** — inside the panel, between ITS brackets (which end at 1652 and begin at 1822 on the left rail) | 352 (+195) |
| 1815..2160 | the panel's bottom brackets and border, the chassis below | 345, anchor |

**Horizontal**, three bands. The left half is shared by all three,
which is what keeps the left column from shearing at a band cut:

| x | out |
|---|---|
| 0..500 | 500, anchor (ring, chassis, map and panel left borders, PREV entire) |
| 500..1770 | **elastic**, 949 (−321) — inside the map (228..2039), the status strip (480..1783) and the ship panel (234..2034) at once, and flat to 5 grey levels over the whole height |
| 1770..2134 | 364, anchor at −321 (NEXT, the right borders, the chassis up to the right column's frame line) |

and then, per band:

* **grid** (rows 153..1560): +80 inside each cell's straight run
  (2250..2420, 2570..2730, 2870..3030, 3180..3330) and **+1** in the
  gap between the last cell and the scroll housing (3400..3440). The
  odd pixel is not in a cell on purpose: `name_holes_fleets` finds the
  grid by looking for twenty holes that share a size, and 321/4 is not
  a whole number.
* **button row 1** (1560..1778): +99/+112/+110, in proportion to the
  plates' present widths 398:451:445.
* **button row 2** (1778..1987): +84/+73/+74/+90, in proportion to
  330:285:288:353.

The two band cuts are the flattest rows available: across x 2200..3560
the largest one-pixel horizontal step is 4.3 at rows 1550..1567 and 3.7
at 1772..1785.

**The scroll bar keeps its width and its place.** Everything from
x 3440 on is an anchor at offset 0, so `fltgeom.SCROLL_SRC_COLUMN`
needed no new measurement and its box is unchanged.

## What came out, against the order's figures

| hole | before | after |
|---|---|---|
| `inset_map` | 228, 211, 1812 x 1101 | **228, 211, 1491 x 906** |
| `ship_panel` | 234, 1545, 1801 x 382 | **234, 1350, 1480 x 577** |
| `status_band` | 480, 1370, 1304 x 119 | 480, 1175, 983 x 119 |
| `prev_fleet` | 233, 1375, 183 x 113 | 233, 1180, 183 x 113 |
| `next_fleet` | 1843, 1374, 191 x 114 | 1522, 1179, 191 x 114 |
| cells | 261 x 219 at x 2213/2518/2823/3124 | **341 x 221** at x 1892/2277/2662/3043 |
| `btn_all` / `relocate` / `scrap` | 398 / 451 / 445 wide | 497 / 563 / 555 |
| `btn_leaders` / `support` / `combat` / `return` | 330 / 285 / 288 / 353 | 414 / 358 / 362 / 443 |

The gutters between cells (44, 44, 40) and between buttons (52, 52 and
47, 48, 46) are unchanged, and both button rows still end at x 3569.

## The three answers the order asks for

**Map aspect.** 1491 / 906 = **1.645695**, against 1812 / 1101 =
1.645777 before. 0.005 % apart.

**Stretch against the galaxy's 1.265.** The hole stretches it
**1.300945x** where it stretched it **1.301009x** — 0.005 %. The
number that actually moves stars is the BOX, because
`colonyrows.galaxy_inset_stars` divides by `box_w` and `box_h`: the
box is 750x457 against 910x554, so **1.29734x against 1.29849x**,
0.089 %. Both are inside the 0.13 % that work order 151 accepted as
"unchanged", and the smoke check now holds the hole figure to 0.1 %.

**Ship panel line capacity**, at the box's own font size, measured by
rendering the real font with the real part names:

| | 1920x1080 | 2560x1440 | 3440x1440 | 3840x2160 |
|---|---|---|---|---|
| text box, window px | 694 x 242 | 925 x 322 | 925 x 322 | 1388 x 484 |
| font / line height | 14 / 14 | 18 / 17 | 18 / 17 | 28 / 27 |
| **lines** | **17** | **18** | **18** | **17** |
| the same before 153 | 10 | 11 | 11 | 10 |
| column widths | 374 / 301 | 498 / 401 | 498 / 401 | 748 / 601 |

**Does the longest realistic panel fit at 1440p without the overflow
line? YES, at the full font size and without shrinking.** The test
case is the four head lines the transcription can produce (name, crew
word + EP, shield, location) plus the weapons column at the struct's
design maximum — `WEAPON_SLOTS = 8` — each entry the longest name in
the catalogue with its firing arc ("9 Black Hole Generator (…)"). It
fits at 18 px at 1440p with **13 specials still fitting beside it**.
Before this work order the same content had to shrink to 15 px and
left room for **none**.

## Everything that had to move with the frame

* `boxes.json` — 32 derived boxes regenerated by
  `tools/frame_holes.py … --write`.
* The six boxes with no hole — **`screens/fleets/fltplaced.py`** is
  new and each is now a rule against a hole. Validated by running it
  against the boxes as they stood at `fb197ac`: five reproduce the
  file exactly and `status_text` comes out one pixel further right,
  which is written down in the module rather than papered over.
  `tools/fleets_place_boxes.py --write` applies them.
* `fltgeom.CONTENT_INSET_SRC` for a cell, 9 -> 10.
* `layout.json`'s `frame._note`, and `_no_cutouts_note`, which said
  decision 3 does not apply to this screen, that the frame has one
  hole and that `frame_holes` has no `fleets` rule. **All three
  stopped being true in work order 146** and the note had not caught
  up; it now records the correction instead of the claim.

## The cells' two extra rows

Not the reshape. `_openings` grows an edge while the next line is 80 %
dark, and at a cell's lower bevel that line is dark everywhere except
under the two corner brackets — so the fraction depends on how WIDE
the cell is. At 261 px the brackets were 24 % of rows 444 and 445 and
the walk stopped at 443; at 341 px they are 19 % and it reaches 445.
**The paint says 445 is right**: a column through the middle of a cell
reads 8.7 at row 445 and 29.0 at 446. The old cut was three rows short
of the interior. Nothing about the threshold was changed; it is
recorded at `fleets_frame_reshape.TARGET_CELL_SIZE`.

## Acceptance

* **Map stretch unchanged from today** — 0.005 % on the hole, 0.089 %
  on the box. Held by a new smoke check at 0.1 %.
* **Panel fits the longest realistic entry at 1440p** — yes, at the
  full 18 px, with 13 specials to spare.
* **No stretched corners anywhere in the rebuilt right column** —
  measured, not asserted. `fleets_frame_reshape.anchor_pairs()` is
  every region the reshape claims to translate; the smoke test
  compares **1 889 951 solid pixels** of the shipped frame against the
  unlit source and requires them byte-identical. It covers the whole
  frame, not only the right column.
* **Smoke test green before the commit** — 235 -> 237, both count
  documents moved with it.

Renders in `~/orionlayer-fixtures/evidence/work_order_153/`:
`acceptance_partA_1440p.png` (new beside current, 2560x1440),
`before_1440p.png`, `new_1440p.png`, `frame_153_built.png`. The third
panel the order asks for is missing because the mockup is not on disk
— `153-parked-for-data.md`.

## Live

**No live run, and none is needed.** Part A is artwork and geometry
and touches nothing the engine holds; the renders are made from the
same fixture snapshot the smoke test drives the screen with. No save
was opened, nothing was written to `~/Master of Orion 2`, and no
client was attached to port 17362.
