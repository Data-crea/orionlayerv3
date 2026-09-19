# 143 — Can the Fleets mockup yield inner-frame pieces? (findings only)

**Findings only.** No code, no skin, no `boxes.json`, no assets, no
commit. Everything below is measured; where a number could not be
measured it says so rather than estimating.

Evidence (never in the repo — the source is a download, not an asset):
`~/orionlayer-fixtures/evidence/work_order_143/`.

## The source, verified before anything was read off it

| | |
|---|---|
| Path | `~/Downloads/ChatGPT Image Sep 19, 2026, 03_47_16 PM.png` |
| Size | 1 926 480 bytes |
| Pixels | **1678 x 937**, RGB, no alpha |
| sha256 | `cc6f18c7197e4e852ed9f08dea889268ebdbd05de0960273c4946a95a65f51f1` |

**The path in the work order does not exist as written.** The real
files use spaces and commas; the underscores were substituted
somewhere in transit. Two files sit at that timestamp —
`03_47_05 PM` and `03_47_16 PM` — and they are **byte-identical**
(same sha256), so the choice does not matter. It is recorded because
"the file I measured" and "the file you meant" have to be the same
file, and here that needed checking rather than assuming.

**1678 x 937 is not a screen resolution** (aspect 1.791, where 16:9 is
1.778). Nothing below assumes it is.

## What the skin format actually requires — read first, because it
## changes which objections matter

`core/nineslice.py` loads **nine separate PNGs** (`load_tile_directory`)
and `render()` blits the four corners **unchanged** and **smoothscales**
each edge in one dimension.

Two consequences, both of which cut against the questions as posed:

* **Mirror symmetry is not required.** All four corners are stored
  separately, so corners that differ are simply cut separately. The
  shipped `frame` skin does not even keep top and bottom the same
  height (122 vs 169 px).
* **Edges are stretched, not tiled.** So the failure mode to look for
  is **smearing of unique detail**, not visible repetition. A strip
  that repeats badly is irrelevant; a strip that is not constant along
  its length is the problem.

One constraint the format does impose: `corner = parts["top_left"].get_width()`
is a single scalar used for both axes, so **the corner must be square**.

## Baselines, so the numbers mean something

The same tests run against what the tree already ships:

| | corner mirror diff | edge deviation along its length |
|---|---|---|
| `inner_panel` | mean 8.7, 20.3 % off>16 | **2.0, 0.0 %** |
| `frame` (outer ring) | mean 6.6, 14.9 % off>16 | top 10.5, 43.3 % / left 3.1, 0.0 % |

`inner_panel`'s edge deviation of 2.0 / 0 % is what an edge that
stretches invisibly looks like. That is the bar.

## Per candidate

Thicknesses are per side, in source pixels, measured by metal density
and confirmed at three thresholds (0.35 / 0.50 / 0.65).

### A — mini galaxy map frame — **not usable as 9-slice**

* Thickness **L 13, T 6, R 25, B 7**. The left and right edges are not
  the same element: the left is a two-rail bevel, the right is that
  **plus a third wide rail** (`A_map_left_vs_right_edge_8x.png`). A
  9-slice needs one left piece and one right piece, and these two
  cannot both be that frame's edge.
* Top thickness sampled along the edge: 6,7,7,6,6,6,6,7,7,6,7,**10**,6,7
  — spread 4 px on a 6 px rail.
* Corners: TL vs mirrored TR mean 34.7 (62.3 % off>16). Irrelevant on
  its own — see above — but the corner *sizes* differ with the side
  thicknesses, which is not irrelevant.
* Interior: clean. **0** bright pixels within 4 px inside any rail, so
  no star bleeds into a border. Centre can be transparent.
* Verdict: **not usable as a 9-slice.** Usable only fixed-size, and
  then only by picking one side's profile and discarding the other's.

### B — empty text panel frame — **usable as 9-slice** (the one candidate that is)

* Thickness **L 13, T 13, R 14, B 12** — the only candidate whose four
  sides agree. **Threshold-stable**: identical at 0.35, 0.50 and 0.65.
  Sampled along the top edge: 13,12,13,13,13,13,12,13,12,13,13,13,13,13
  — **spread 1 px**.
* Corners chamfered 45° with an orange lozenge in each
  (`B_text_panel_top_edge_4x.png`). Cut at 48 x 48 they are square and
  contain the whole chamfer.
* Edge deviation along length: top 18.0 (66.8 %), bottom 10.0, left
  9.6, right 9.8. All worse than `inner_panel`'s 2.0 — the top rail
  carries rust/grime streaks that are not constant along its length.
* **Trial cut made and stretched exactly as `render()` would**
  (`TRIAL_B_nineslice_stretch.png`, pieces in `TRIAL_B_pieces/`): holds
  at 635x346, 1400x300, 500x900 and 300x160. `TRIAL_B_edge_smear_4x.png`
  shows where it stops holding: crisp speckle at 1:1, blurred at 1400,
  washed into soft streaks at 2600. The stretchable centre is 539 px,
  so filling a 1920-wide box is ~3.4x and is past the point where the
  grain survives.
* Interior: sd (5.5, 5.2, 5.0), no content. Clean enough for a
  transparent centre; it holds nothing that would have to be kept.
* Verdict: **usable as a 9-slice**, with the stretch limit stated.

### C — ship grid frame incl. scroll bar housing — **not usable**

* Thickness **L 12, T 2, R 2, B 12**. It is **not a closed frame**: the
  left and bottom are thick bevels, the top and right are thin rails
  where the panel runs into the outer ring and the button block. Four
  sides, two different kinds of element.
* The scroll bar housing is **its own chamfered frame with its own
  orange bolts** (`C_D_rect_probe_5x.png`), not part of the grid
  frame — so "incl. the scroll bar housing" describes two objects.
* Interior is not a centre: it holds the cells. sd (26.3, 32.2, 22.6).
* Verdict: **not usable.** The scroll housing alone is a separate,
  fixed-size candidate.

### D — button block frame — **usable only fixed-size**

* Thickness reads **L 14, T 12, R 12, B 12** at threshold 0.65 but
  **L 26, T 21, R 25, B 31** at 0.35 — the boundary is a gradient, so
  the measurement does **not** stay stable under the sweep. This is the
  one candidate where the cut line cannot be pinned.
* Top thickness along the edge: min 12, max 24, **spread 12**.
* Edge deviation: bottom 14.9 (48.3 %), right 13.5 (42.7 %).
* Interior holds the buttons.
* Verdict: **usable only fixed-size**, and only after deciding by hand
  where its edge ends.

### E — individual grid cells and button frames — **not usable as 9-slice**

* Cell interiors are extremely regular: widths 111, 111, 111, 112 at
  pitch ~129. Cell frame T 9, B 9, R 12; the leftmost cell's left
  "frame" is the panel's own 22 px bevel.
* **The borders are shared between neighbours** — a cell is not an
  independent frame, it is a grid. Cutting one yields a piece whose
  edges belong half to the next cell.
* Cell interior sd (0.4, 0.6, 0.7), luma 9.7..12.3 — flat.
* Verdict: **not usable as a 9-slice.** A cell would be a fixed-size
  plate, and at 111 px interior it is close to HD's 128x126 at 1080p.

### F — arrow-button bar — **not usable as 9-slice**

* The bar is **54 px tall**. With corners large enough to hold the
  chamfer there is no straight vertical edge left at all — the
  uniformity test returned empty strips.
* Top edge deviation 20.7 (56.9 % off), **45 orange accent pixels** in
  the top strip alone: the most detail-laden edge measured.
* Verdict: **not usable as a 9-slice.** Fixed-size element only.

## Resolution (question 5)

| target | upscale of this mockup | upscale of the **shipped** outer ring |
|---|---|---|
| 1080p | 1.14x | 1.15x |
| 1440p | 1.53x | 1.53x |
| 2160p | **2.29x** | **2.30x** |

`assets/shared/skins/default/frame/9slice.json` records
`source_size: [1672, 941]`. **The outer ring this project already ships
was cut from a source the same size as this mockup**, and is used at
2160p today. So "would the pieces have to be upscaled at 2160p" is
answered yes — and it is the identical compromise already in the tree,
not a new one.

Piece sizes a cut would give, against what ships:

* mockup B: corner 48x48, rails 12–14 px
* `inner_panel`: corner **24x24**, rails 24 px
* `frame`: corner 368x122 / 368x169

A 48x48 corner from the mockup carries **more** detail than
`inner_panel`'s 24x24 does.

## Colour (question 6) — observations, not judgements

Metal pixels only (luma > 45, saturation < 0.34):

| | metal mean RGB | B−R | median luma |
|---|---|---|---|
| mockup outer ring | (96.8, 96.6, 96.3) | −0.5 | 83.7 |
| **shipped `frame`** | (97.3, 96.2, 95.1) | −2.2 | 78.7 |
| planets frame | (97.2, 98.1, 98.7) | +1.4 | 83.7 |
| galaxy_map frame | (87.4, 88.1, 86.0) | −1.5 | 75.3 |
| mockup B text panel rail | (99.8, 100.5, 101.3) | +1.5 | 93.3 |
| mockup A map panel rail | (67.4, 67.6, 67.2) | −0.2 | 67.7 |
| mockup D button block rail | (107.7, 110.4, 111.1) | +3.4 | 102.7 |
| **shipped `inner_panel`** | (61.1, 53.5, 46.2) | **−14.9** | 50.7 |

Two observations:

1. **The mockup's outer ring is the shipped ring's colour** — (96.8,
   96.6, 96.3) against (97.3, 96.2, 95.1). Whatever produced it had the
   existing frame in front of it.
2. **The mockup's inner panels are neutral-to-cool; `inner_panel` is
   warm bronze.** B−R +1.5 against −14.9. Dropping a mockup cut in
   beside the existing `inner_panel` would put a cool grey panel next to
   a warm brown one. Side by side in `COLOUR_side_by_side.png`.

Against the native original: the orion2re Fleets screen
(`REF_native_fleets_FLEET_LBX_0.png`, FLEET.LBX entry 0) has **no
ornate metal panel frame at all** — flat blue plates with thin bevels.
Any of these frames is an HD invention, not a transcription, and would
be marked as such.

## If B were taken — what decision 34 would have to say (proposal, not a decision)

Decision 34 gives two skins and a meaning each: `inner_panel` is the
9-slice art and **frames pictures**; `thin_border` is the rounded blue
outline and **groups things**.

Candidate B is 9-slice art doing `thin_border`'s job: it groups a text
area. So it fits neither name, and there are three ways out, for Data
to choose between:

1. **Replace `inner_panel`.** Cheapest in names, worst in fact — the
   whole tree's five New Game setting images wear it, and they are
   pictures. It would also swap warm bronze for cool grey everywhere at
   once.
2. **A third skin**, e.g. `panel_frame`, meaning "9-slice art that
   groups". Decision 34 would need a third paragraph and, by its own
   last sentence, **every screen that renders panel skins selectively
   would have to match on three names, not two** — that sentence exists
   because matching on `inner_panel` alone nearly lost Select Race.
3. **Leave the taxonomy alone** and treat B as a screen-local asset for
   Fleets only, which is what the Fleets frame already is.

I would not choose here. What the measurements support is only that B
is the one candidate that *could* be cut; whether it should be is a
question about the tree's vocabulary, not about the pixels.

## Evidence index

`OVERVIEW_candidates.png` (measured rects on the source),
`A_map_corners_4x.png`, `A_map_left_vs_right_edge_8x.png`,
`B_text_panel_top_edge_4x.png`, `C_D_rect_probe_5x.png`,
`TRIAL_B_source_cut.png`, `TRIAL_B_pieces/` (nine files),
`TRIAL_B_nineslice_stretch.png`, `TRIAL_B_edge_smear_4x.png`,
`COLOUR_side_by_side.png`, `REF_native_fleets_FLEET_LBX_0.png`.
