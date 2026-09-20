# 151 — New Fleets frame: Stop 2

**Work Order 151, Stop 2**, on Data's three decisions. The old frame is
still what the tree wears: `screens/fleets/assets/frame.png` is
untouched at 1445x811, and `boxes.json`, `fltgeom.py` and
`layout.json` still describe it. **Nothing about the swap is
committed** — it waits for acceptance. What is committed is the
decision, its check, the build tool, and this report.

No live run. Nothing was sent to the engine, no save was touched.

---

## 0. The map, re-measured before anything was cut

Data's decision 1 asked for this first, so it is first.

**The new source.** `screens/fleets/assets/_src/fleets_frame_4k_map165.png`
— 3840x2160, RGB, **no alpha**, 6 719 622 bytes, sha256
`92f89a8650684de237730248a8b3b977674bbe9886a83bc2a961acdbe498a83d`.
It replaces `fleets_frame_4k_cells.png` (sha256 `e2ce1745…`), which is
off disk and out of the index.

**The opening, measured twice by different means.** The detector puts
it at **(228, 211) 1812 x 1101**. A straight luma profile across the
rim agrees: the bright rim ends at x 227 and the dark begins at 228;
on the right the dark ends at 2039 and the rim starts at 2041; top rim
ends 209, dark begins 210 (210 reads 13, 211 reads 3 — one transition
row); bottom dark ends 1311, rim starts 1313. So the opening is
1812 wide and 1101 or 1102 high depending on which side of that single
transition row you stand, and the cut takes 1101.

| box | w x h | aspect | stretch vs the galaxy's 1.265 |
|---|---|---|---|
| the original's inset | 305 x 182 | 1.6758 | **1.3248x** |
| current v4 hole | 646 x 392 | 1.6480 | **1.3027x** |
| **new 4K map hole** | **1812 x 1101** | **1.6458** | **1.3010x** |
| the same at 1102 high | 1812 x 1102 | 1.6443 | 1.2998x |

**It lands where Data said: ~1.65, and within 0.13 % of v4's stretch.**
The old source stretched the galaxy 1.953x; this one stretches it
1.301x against v4's 1.3027x and the original's 1.3248x — that is
0.13 % away from the frame the screen wears today and 1.8 % less
stretch than the original applies. Section 1 of the Stop 1 findings is
answered by the art: no code change, no letterbox, no marked
deviation.

The stars painted inside it are gone, as Data said they would be:
the opening is a hole and they were inside it.

---

## 1. The two lit buttons, rebuilt unlit

Decision 2, option (a): all seven unlit in the art, HD draws the lit
state as today, **rebuilt at their own widths, corners kept**.

**The four bottom plates, measured off their border profiles at mid
height** — outer x range, and all four share one vertical extent
y 1796..1941 with an 11 px top and 10 px bottom border:

| button | plate x | width | interior (the future hole) |
|---|---|---|---|
| Leaders | 2162..2512 | 351 | 2173..2502, 330 x 125 |
| Support | 2539..2844 | **306** | 2550..2834, 285 x 125 |
| Combat | 2872..3180 | **309** | 2883..3170, 288 x 125 |
| Return | 3207..3580 | 374 | 3217..3569, 353 x 126 |

Support's interior measured 280 x 119 in the Stop 1 pass and 285 x 125
here. **Both numbers are right about different things**: the first was
measured on the LIT art, where the bright inner border stops a dark-
region scan three pixels early on each side. It is one of the reasons
the rebuild had to come before the cut.

**How it is rebuilt.** A horizontal 3-slice of the Leaders plate: 60 px
of plate kept at each end, the straight middle resampled from 231 px to
186 (Support) and 189 (Combat). Nothing is scaled vertically.

Three things that had to be measured rather than assumed, each of which
was wrong the first time:

* **The corner size.** 60 px is well clear of the chamfer, which
  measures 22 px off the art. It could not be found by asking where the
  border stops changing: the plate is lit along its length, so no column
  of it matches any other and that test returns nothing. Measured off
  the chamfer instead.
* **The glow does not stop at the plate.** It lifts the whole dark band
  behind the button — blue-minus-green **+10.5** above Support against
  **+4.9** above Leaders, still +4 forty pixels away. So the copied tile
  runs the full height of that band, from the highlight seam above it
  (y 1768) to the one below (y 1962), both continuous horizontal lines.
  A tile that stopped at the plate left a blue haze around two buttons.
* **The band left of the Leaders plate is not plain band.** The button
  panel's own bevel runs there (luma 26..33 against the band's 11) and
  fades out only around x 2180. Copied across, it drew a bright strip
  where nothing stands, so the left margin is mirrored from the clean
  right one.

And one fault worth recording because the result looked right: the word
"Leaders" is flattened out of the source interior so it is not carried
into the other two slots, and the first version did that over the
interior's **bounding rectangle** — which also covers the four chamfer
corners. They are inside that rectangle but they are frame, not
content. The rebuilt buttons came out with square corners while
everything else on the screen had chamfered ones, and the chamfer table
reported an inset of 0 for exactly those two, which is what found it.
Only the bright islands the dark interior **encloses** are flattened
now.

---

## 2. The 32 openings, cut

**Detected, not assumed, and swept.** The detector separates the
interiors by eroding with a 13x13 structure before labelling — without
that every dark area in the image is one connected region through the
chassis shadow, and a plain threshold returns the whole canvas as a
single blob — then grows each edge while the next line is at least 80 %
dark. A majority test rather than a scan line, because the openings
still contained painted content and a star or a letter stops a scan
line dead.

Swept over seed threshold 26/30/34 and edge threshold 22/26/30: **the
same 32 rectangles at every combination.** Two candidates come and go
at the edges of the sweep and neither is an opening — a dark strip in
the top chassis at 34, and a merged blob around the ALL button at 26.
Three more are refused by shape at every setting: the vent slots in the
outer chassis at both canvas edges, the painted scroll trough, and one
seed that grows back out over nearly the whole image.

**The cut follows the interior's shape, not its bounding box.** Every
opening here has chamfered corners; a rectangular cut would erase them
and leave square holes in a frame that has angled ones.
`binary_fill_holes` inside each opening closes every bright island the
interior encloses — which is precisely how the painted content leaves:
the map's stars and the buttons' labels are not retouched off the art,
they are inside a hole.

**What came out**, through the tree's own naming rule
(`tools/frame_holes.name_holes_fleets`, which refuses anything but this
inventory):

| | |
|---|---|
| minimap | (228, 211) 1812 x 1101 |
| arrow bar | PREV (233,1375) 183x113, status (480,1370) 1304x119, NEXT (1843,1374) 191x114 |
| text panel | (234, 1545) 1801 x 382 |
| 20 cells | all **261 x 219**, pitch 305 x 263, a clean 4 x 5 |
| 7 controls | ALL 398x126, RELOCATE 451x126, SCRAP 445x125; LEADERS 330x125, SUPPORT 285x125, COMBAT 288x125, RETURN 353x126 |

**Alpha hygiene.** 4 303 122 fully transparent pixels (51.9 % of the
canvas), **0 partial pixels**, and **0 pixels with colour left under
alpha 0** — the RGB is zeroed under the cut, which is the property work
order 146 measured on the v4 frame and is worth keeping: colour under a
transparent pixel is invisible to a normal blit and appears the moment
anything reaches for `BLEND_RGB_ADD` or a premultiplied copy.

**The scroll bar stays painted**, as in v4 — it has no hole, because the
thumb's position is a value the snapshot does not carry, so HD draws a
bar over painted art. Re-measured off the new frame:

```
housing   x 3447..3553   (rails 3447-3460 and 3543-3553, channel between)
up arrow  y  206..306    (triangle 236..278)
track     x 3480..3522,  y 323..1408
down      y 1425..1519   (triangle 1453..1494)
```

`fltgeom.SCROLL_V4_COLUMN` is renamed **`SCROLL_SRC_COLUMN`** with it:
the name said v4 and the frame no longer is.

---

## 3. The boxes

**32 derived, 6 placed.** `tools/frame_holes.py … --write` regenerates
the 32 cutout boxes and keeps the rest verbatim, which is decision 3
working as intended. The six it keeps had to be moved by hand, and
**five of them were stale before this order** — placed for the v3
one-opening frame and never re-seated when v4 cut 32 holes:
`status_hint` sat 151 px ABOVE the band it belongs to, `status_text`
164 px above it, and `icon_area` did not contain its own cells.

| box | current | new | moves |
|---|---|---|---|
| inset_map | [153, 105, 862, 526] | [112, 104, 910, 554] | 41 |
| ship_panel | [153, 762, 862, 193] | [115, 770, 904, 195] | 38 |
| status_band | [278, 673, 615, 59] | [238, 683, 656, 64] | 40 |
| cell_00 | [1127, 106, 118, 112] | [1104, 110, 134, 114] | 23 |
| btn_support | [1303, 897, 113, 61] | [1273, 902, 146, 66] | 30 |
| btn_return | [1581, 892, 178, 65] | [1606, 901, 180, 67] | 25 |
| **scroll_column** | [1694, 101, 45, 651] | [1724, 103, 54, 657] | re-measured |
| **icon_area** | [1017, 77, 605, 658] | [1104, 103, 674, 657] | 87 — now the union it is documented to be |
| **button_band** | [1002, 797, 645, 179] | [1084, 801, 702, 167] | 82 — the union of the seven |
| **status_text** | [395, 509, 447, 47] | [342, 683, 449, 64] | 174 — into the band it names |
| **inset_hint** | [295, 436, 649, 29] | [130, 600, 874, 40] | 165 — the bottom strip, per `hint_rect` |
| **status_hint** | [304, 522, 627, 20] | [251, 701, 629, 27] | 179 — inside the band, was above it |

**The chamfer table is re-measured too**, as it must be: it is in SOURCE
pixels and the canvas changed. `CONTENT_INSET_SRC` goes from
inset_map 14 / ship_panel 13 / cells 6 to **42 / 39 / 9**, with the
seven buttons at 5-7 and the arrow-bar pair at 14. Every value is the
smallest inset that clears the chamfer, and the smoke test re-derives
all of them from the shipped PNG (decision 36).

---

## 4. The canvas, filed as decision 70

Data's decision 3, filed as a **new entry rather than an amendment to
12**: decision 12 is about frame VARIANTS and runtime tile swapping,
and this says nothing about either — it says what size a frame image is
authored at. Numbered 70 after checking the tree: 69 was the highest
and nothing used 70.

**70. 3840x2160 is the source canvas for a new or replaced frame
image.** Existing frames keep their own size until something replaces
them. 3840x2160 is the only canvas that is an exact integer ratio to
both ends of the pipeline — halved onto the 1920x1080 reference by
`_scale_frame`, 1:1 at 2160p — and every frame in the tree today is
upscaled at 4K.

**With a check, in `tools/smoke_test.py`.** A rule about what is NEW
cannot be read off a tree that only holds what is there now, so the
check holds the replacement half: every `screens/*/assets/frame.png` is
either the size it had when the decision was filed or the canvas, and a
third size fails. Red-proved — resizing the Planets frame to 2400x1350
gives:

```
AssertionError: screens/planets/assets/frame.png is 2400x1350; it was
1920x1080 and a REPLACED frame is 3840x2160 (decision 70), never a
third size
```

**Smoke goes 230 -> 231**, and both count documents move with it.

**The cost is stated in the entry rather than discovered later**: RGBA
at 3840x2160 is about five times the file. `frame.png` is 950 KB at v4
and **5 003 879 bytes** at this build. No PNG optimiser is installed on
this machine (`oxipng`, `optipng`, `pngcrush`, `zopflipng` all absent),
so that number is what Python's own writer produces at `optimize=True`.

---

## 5. What builds it

`tools/fleets_frame_build.py` — the only thing that touches the source
pixels, and it does two things to them: rebuilds the two lit buttons
unlit, and cuts the 32 openings. It verifies the source's sha256 first,
because every constant in it is a measurement of THAT image, and it
refuses to write anything if the openings do not come out at 32.

Its output is byte-identical to the build these renders were made from
(sha256 `258eec69e8704b6a91310379156509c6637d805fabc7f42a1fe26feef51e0fb8`),
which is the licence decision 40 asks for before anything may be called
derived. Its default output path is gitignored.

---

## 6. For acceptance

`~/orionlayer-fixtures/evidence/work_order_151/`:

| file | what |
|---|---|
| `acceptance_1440p.png` | the three side by side, captioned |
| `fleets_new151_1440p.png` | the new frame, full 2560x1440 |
| `fleets_current_1440p.png` | the frame the tree wears today, same fixture |
| `planets_1440p.png` | the Planets screen, for the house style |
| `frame_151_built.png` | the built frame itself, alpha and all |
| `pending_swap.patch` | the rest of the swap, ready to apply |

Both Fleets renders use the same synthetic state — nine ships, three
relocation lines, SUPPORT on and COMBAT off — so the only difference
between them is the frame and what came out of it.

**What to look at.** The HD-drawn lit SUPPORT sits in its hole and the
other six are the art's own unlit plates. The scroll thumb lands on the
painted trough. The map is taller and the text panel shorter, which is
the edit Data made. The ship-panel text still starts at the top-left
inside the chamfer.

**What the clone proves.** The whole swap — frame, 32 derived boxes, six
placed ones, the chamfer table, the scroll column, `layout.json`'s
`image_size` and `_note` — was applied in a throwaway clone and
`python tools/smoke_test.py` is **231 checks green** there, including
the 32-hole rule, the box/hole agreement for all 32, the chamfer table
re-derived from the PNG, and the scroll column landing on opaque paint.

## 7. On acceptance, this is the commit

The frame is a build, and the rest is parked as a patch that
`git apply --check` accepts against the commit this brief arrives in:

```
python tools/fleets_frame_build.py --out screens/fleets/assets/frame.png
git apply ~/orionlayer-fixtures/evidence/work_order_151/pending_swap.patch
python tools/smoke_test.py
```

Expected: `SMOKE TEST PASSED — 231 checks green`. Abort if the build
prints anything but `3840x2160`, or if the patch does not apply — that
would mean one of the four files moved under it, and the answer is to
re-derive rather than to force.

What the patch carries, so it can be read instead of trusted:
`boxes.json` (32 derived + the six re-seated), `fltgeom.py`
(`FRAME_SRC_SIZE`, `CONTENT_INSET_SRC`, `SCROLL_SRC_COLUMN` and
`SCROLL_PARTS`), `layout.json` (`frame.image_size` and the provenance
in `frame._note`), and `smoke_test.py`'s two references to the renamed
constant. `v3_projektstatus.md` is the one thing left to write by hand,
because what it says depends on the decision being made.

Nothing else changes: no screen behaviour, no wire, no deviation.

## 8. Still open, carried forward

* `capture_fields.py` has never run — the port has not been free in any
  session since work order 150.
* The `INJECT_CLICK` deviation (the radios do not respond) is unchanged.
