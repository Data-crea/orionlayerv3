# 151 — New Fleets frame: Stop 1 findings

**Work Order 151 — New Fleets frame.** Stop 1: findings only. **No art
was changed**, no hole was cut, no box was moved. The old frame is
untouched in the tree.

## The source, in the tree

`screens/fleets/assets/_src/fleets_frame_4k_cells.png` — **3840x2160,
RGB, no alpha**, 6 824 378 bytes, sha256
`e2ce1745fbe5c7ff34b075a6af8239074bd55f5f29c86aac06b4d5f12d499cbb`,
byte-identical to the Downloads copy. `_src/` is the tree's existing
convention for source art (`colony_summary/assets/_src`,
`galaxy_map/assets/ships/_src`), and it is tracked, not ignored.

Provenance is recorded as given: AI draft at 1672x940, left column
edited so map and text box match in height, upscaled by Data to
3840x2160, ship grid edited so all 20 cells carry the same frame.

## What I measured, and how

The image has no alpha, so the openings were found from their dark
interiors: luma <= 30, then **eroded by a 13x13 structure before
labelling and dilated back**. Without the erosion every dark area in
the image is one connected region — the interiors join through the
chassis shadows, and a plain threshold returns the whole 3840x2160
canvas as a single blob. The erosion separates them; the dilation
restores each one's true extent.

That yields **33 elements, exactly the inventory the order lists**:
1 map, 3 small boxes, 1 text box, 20 cells, 1 scroll bar, 7 buttons.
The cells come out at a perfectly regular 255x212 on a 305 x 263
pitch, which confirms the grid edit.

---

## 1. Map aspect — the sharpest finding

**How the minimap maps the galaxy** (`colonyrows.galaxy_inset_stars`):

```
div_x = INSET_SCALE_X // box_w      div_y = INSET_SCALE_Y // box_h
sx = ((star.x * 1000 // scale) * 10) // div_x
```

The divisors are **per axis**. The galaxy is therefore **stretched to
fill the box** — it is never letterboxed, and there is no code path
that would letterbox it. Every galaxy size normalises to the same
506000 x 400000 (work order 146), so the galaxy's intrinsic aspect is
always **1.265** and this is one answer for all four sizes.

| box | w x h | aspect | stretch vs 1.265 |
|---|---|---|---|
| the original's inset | 305 x 182 | 1.676 | **1.325x** |
| current v4 hole | 646 x 392 | 1.648 | **1.303x** |
| **new 4K map box** | **1801 x 729** | **2.471** | **1.953x** |

**The new box stretches the galaxy nearly twice as wide as it is tall,
where the original stretches it by a third.** Stars would sit about
1.5 times further apart horizontally, relative to vertically, than in
the original — and the original already stretches.

If it were letterboxed instead, the galaxy would use **922 of the
1801 px** width: **879 px, 49 % of the map box, would stay empty.**

Three ways out, all Data's to choose:

1. **Accept the stretch.** No code changes. The minimap is a locator,
   not a chart, and the original already distorts it — but this is a
   different amount of distortion from every other place the galaxy is
   drawn in HD.
2. **Letterbox it.** Needs a change to `galaxy_inset_stars`: one
   divisor for both axes and a centring offset. That is a deviation
   from the original's own arithmetic and would have to be marked. It
   leaves half the box empty.
3. **Narrow the map opening in the art** to roughly 1801 x 1424 —
   which the layout has no room for — or widen nothing and accept 1.

## 2. Holes vs surfaces

Following exactly how the current frame does it (work order 146):

| element | new frame | why |
|---|---|---|
| map | **hole** | live content: stars, relocation lines, stack markers |
| 3 small boxes | **holes** | PREV, the status text, NEXT — live text and buttons |
| text box | **hole** | the scanned ship's lines |
| 20 cells | **holes** | ship pictures and names, drawn per cell |
| 7 buttons | **holes** | labels and the lit filter state are drawn by HD |
| **scroll bar** | **painted surface** | v4 paints it; the thumb's position is a pointer value the snapshot does not carry, so HD draws a bar over painted art rather than into a hole |

That is 32 holes and one painted surface, the same split as v4. The
scroll bar's rect would have to be re-measured off the new art, as it
was for v4, because it is the one control with no hole to derive from.

## 3. Button states

**What the current screen does.** Work order 146 settled this:
`fltdraw.draw_labels` fills the button's content rect with
`col("radio_on")` when the filter is on and draws HD's own label over
it. `radio_on` is **(8, 8, 80)**, measured from FLEET.LBX entry 9
frame 1 — the frame the original itself draws when the status is 1.
The border comes from the frame's hole. HD does **not** blit the
original's button face, because FLEET.LBX 9 and 10 carry the words
baked into the pixels and that printed each label twice.

**What the new art does.** Support and Combat are lit in the artwork,
in both fill and border — measured interiors (16.7, 45.0, 80.9) and
(16.3, 43.2, 77.2) against the other five at green-dominant values,
and borders (32.2, 59.7, 95.2) and (19.7, 40.9, 67.6) against
neutral greys. **A state is baked into the frame**, which is what the
order says must not stay.

**Restoring the unlit frame is not a straight copy.** The buttons
differ in width: Leaders 319 and Return 341 against Support 274 and
Combat 276. An unlit frame taken from Leaders or Return has to be
rebuilt at the narrower width — corners kept, middle shortened —
rather than pasted.

Options, against the two decisions the order names:

**Decision 12, "Frame variants only — no runtime tile swapping."**
**Decision 34, "Two panel skins, and which one means what."**

* **(a) One artwork, all seven buttons unlit; HD draws the lit state.**
  What the screen already does, and what decision 12 asks for: one
  frame, no swapping, the state drawn by code. Costs the rebuild of
  two button frames at a narrower width.
* **(b) Frame variants — one artwork per filter combination.** Decision
  12 permits variants, but two independent toggles means **four**
  frames, and every future state multiplies them. It also puts a
  game state into an art asset, which is the thing the order objects
  to in the first place.
* **(c) Make the two buttons painted surfaces instead of holes** and
  let a skin draw them entirely. That is decision 34's question —
  which skin means what — and it would need a name for "a button
  that draws its own frame", which the tree does not have.

I have no recommendation; (a) is what the existing code already
expects.

## 4. Canvas — 3840x2160 as the common source

**It fits, and it is better than every frame now in the tree.**

`core/screen_base._load_frame` loads the PNG and `_scale_frame`
smoothscales it **once** to `layout.rect(0, 0, 1920, 1080)`, the
reference area in window pixels; `tools/frame_holes.to_ref` scales
hole coordinates by `1920 / img_w`.

| frame | source | to the 1920 reference | at 2160p |
|---|---|---|---|
| fleets v4 | 1445x811 | 1.329x | 2.657x |
| planets | 1920x1080 | 1.000x | 2.000x |
| galaxy_map | 1707x921 | 1.125x | 2.250x |
| colony_summary | 1672x941 | 1.148x | 2.297x |
| game_menu | 1108x1419 | 1.733x | 3.466x |
| **4K candidate** | **3840x2160** | **0.500x** | **1.000x** |

It is the only canvas that is an exact integer ratio to both targets:
halved for the reference, **1:1 at 2160p — never upscaled**. Every
other frame in the tree is upscaled at 4K.

**The double-scaling rule does not bite here.** The fundament's rule —
*"Scaling twice looks correct at the resolution you tested"* — is about
a stored value multiplied by the window scale twice, the fault that
rendered the help popup at double size at 3840x2160. A frame image is
not a stored value: it is scaled once, by `_scale_frame`, and the hole
coordinates are converted once, by `to_ref`. Neither is multiplied
again. The one thing to watch is that `to_ref` must read the image's
own size and not a constant, which it does.

## 5. Cutouts

**All 33 boxes move. Not one keeps its rect.**

| box | new (ref px) | current | moves by |
|---|---|---|---|
| inset_map | [117, 108, 900, 364] | [153, 105, 862, 526] | 162 px |
| ship_panel | [117, 594, 900, 367] | [153, 762, 862, 193] | 174 px |
| status_band | [243, 504, 646, 57] | [278, 673, 615, 59] | 169 px |
| scroll_column | [1733, 156, 36, 554] | [1694, 101, 45, 651] | 97 px |
| cell_00 | [1108, 114, 127, 106] | [1127, 106, 118, 112] | 19 px |
| btn_support | [1278, 905, 137, 57] | [1303, 897, 113, 61] | 25 px |

The map and text box move furthest, because the new layout makes them
the same height — the edit the provenance describes.

**32 of them are derived from the frame (decision 3, "Cutout boxes
come from the frame; content boxes do not") and are regenerated by
`tools/frame_holes.py screens/fleets/assets/frame.png --write`** with
the `name_holes_fleets` rule written for work order 146. That rule
refuses anything that is not 32 holes in the expected shape, so it
will also serve as the check that the new alpha was cut correctly.

**Six are hand-placed and `--write` keeps them verbatim:**
`icon_area`, `button_band`, `status_text`, `scroll_column`,
`inset_hint`, `status_hint`. Of those, **`scroll_column` must be
re-measured off the new art** — the scroll bar is painted, so it has
no hole to be derived from, exactly as in v4. The other five are
either leftovers or hint text boxes and need only checking that they
still sit inside the new openings.

---

## Stopping here

Nothing was changed. Stop 2 needs Data's decisions on:

1. the map stretch — accept 1.95x, letterbox, or change the art;
2. the button state — (a), (b) or (c) above;
3. whether 3840x2160 becomes the common canvas for all frames or only
   for this one.
