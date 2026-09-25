# 168 — Which outer frame becomes the one shared outer ring: the evaluation

Work order 168, 25 September 2026. **Analysis only**: no frame, screen,
layout or check was changed. The only additions to the tree are this
report, the filed order, its README row and the measuring script
(`tools/frame_ring_measure.py`, with its picture half in
`tools/frame_ring_evidence.py`). Data decides.

**The short answer.** None of the existing frames is sharp at 2160p in
the sense decision 70 means. The Fleets frame is the only one that
is not upscaled at 2160p. Its edges measure as sharp as any source
edge in the tree (1.60 px). But its 3840x2160 pixels hold the detail of
the 1672x940 AI draft Data upscaled it from. Per pixel, its fine
texture is about a fifth of the Planets frame's at 1:1. The Planets
frame has the cleanest ring and the most detail at 1080p. It is
upscaled 2x at 2160p (edge 2.90 px). The two rings are the same design
at the same depth (profile below). So the recommended base is **the
Fleets frame's outer ~80 reference px, checked against the Planets ring**.
A 2160p ring that is sharp in texture as well as in edges needs a
source painted or rendered at 3840x2160. Resampling any of these
images will not produce that.

---

## Material

### The frame images

| candidate | path | px | alpha | origin, as the tree records it | governing decisions |
|---|---|---|---|---|---|
| galaxy_map | `screens/galaxy_map/assets/frame.png` | 1707x921 | yes | built in work order 133 from a ChatGPT render ("ChatGPT Image Sep 18, 2026, 10_29_27 PM.png"), master `galaxy_map_frame_v3.png`; holes cut from measured geometry (2306f3d) | 12, 70 (keeps its size until replaced) |
| colony_summary | `screens/colony_summary/assets/frame.png` | 1672x941 | yes | Data's image, "generated at 1672x941 and upscaled at every resolution" (cc8f4b4, 9a0a66e, ec325dc) | **55** (one fixed image, boxes measured off its holes), 12, 70 |
| planets | `screens/planets/assets/frame.png` | 1920x1080 | yes | brief 101's `frame3.png` from Data's Downloads, byte-identical to `doc/briefs/101-frame3.png`; how it was made is not recorded | 12, 70 |
| fleets | `screens/fleets/assets/frame.png` | 3840x2160 | yes | AI draft 1672x940, left column edited, **upscaled by Data to 3840x2160**, ship grid edited (`151-new-fleets-frame-findings.md`); reshaped by 153 A; source `_src/fleets_frame_4k_map165.png`, RGB, no alpha. Its first version (a47650f, 134 A) was the Planets ring with the struts removed | **70** (the only frame on the canvas), 12 |
| game_menu | `screens/game_menu/assets/frame.png` | 1108x1419 | yes | Data's frame, work order 122 Run 1b (975ea44) | **69** (fixed popup frame, plain-scaled), 12, 70 |
| in:frame_plain | `~/orionlayer-fixtures/incoming/frames_18sep/frame_plain.png` | 1920x1080 | yes | the set of 18 September (work order 132), **built and rejected by Data, reverted** (`v3_projektstatus.md`); outside the tree | — |
| in:frame_map_sidebar | `…/frames_18sep/frame_map_sidebar.png` | 1920x1080 | yes | same set | — |
| in:frame_map_4panels | `…/frames_18sep/frame_map_4panels_7buttons.png` | 1920x1080 | yes | same set | — |

Other frame images found and **not measured as candidates**:

- `assets/shared/skins/default/frame/*.png`: the skin nine-slice
  (`core/frame.FrameRenderer`) of the pre-game screens (custom race,
  select race via its variant folder, empire identity). Its tiles add
  up to 368+936+368 x 122+650+169 = **1672x941**, the colony frame's
  size, so at 2160p it is upscaled by the same factor class (about
  2.3x). It is nine tiles, not one ring image, and it is not a
  full-screen HD frame.
- `screens/fleets/assets/_src/fleets_frame_4k_map165.png`: the Fleets
  frame's own source, 3840x2160 RGB. It adds nothing to the frame
  itself.
- `core/researchframe.py` nine-slices the Fleets frame's inner map
  frame for the research panel (166 B). That is an inner frame, not an
  outer ring.
- `…/frames_18sep/panel.png`, 2144x704: a panel, not a ring.
- `assets/shared/banner/*frame*.png`: banner and stand frames, not
  screen frames.

**A licence point, a question rather than a finding.** `LICENSE` lists
"cockpit frames" under *artwork derived from Master of Orion 2*. Its
AI-generated section names only the planet surfaces and the output
icons. The provenance above records the galaxy map frame as a ChatGPT
render and the Fleets frame as an AI draft. If the shared ring comes
from either, the licence text probably needs a line.

### Data's screenshots (`/home/data/Bilder/Bildschirmfotos/`)

| file | screen | size | scale of the frame image in it |
|---|---|---|---|
| GALAXY.png | galaxy map | 2442x1365 | ~1.43x (1707 → ~2440) |
| COLONY.png | colony summary | 2442x1365 | ~1.46x |
| PLANETS.png | planets | 2442x1365 | ~1.27x |
| FLEETS.png | fleets | 2442x1365 | ~0.64x (downscaled) |

All four were taken on 25 September 2026 at 11:26, from one window of
2442x1365 (about 1.27 times the reference, between 1080p and 1440p).
**How the frames look in use:** the four screens already wear one
style family, the dark cockpit ring with orange diamond lamps in the
corners and lamp groups along the top. Seen whole, they read as the
same frame. They differ in the details. The galaxy map has a title
plate ("GAME") in the top edge and lamp pairs in the bottom edge. The
top lamp groups sit in slightly different places. The inner rim
differs where each screen's own panels meet the ring. At this window
size Fleets and Planets look crisp. The galaxy map is visibly the
softest.

---

## A. Sharpness

### A1. Native size and scale factors

The factor is image px → window px, x/y. Full-screen frames are
smoothscaled once onto the 16:9 area (`ScreenBase._scale_frame`). The
GAME menu is seated by ONE factor, the galaxy map's `map_area` height
(844 ref px) over the image height (`gmframe.placement`).

| frame | px | aspect | 1080p | 1440p | 2160p | upscaled at 2160p? |
|---|---|---|---|---|---|---|
| galaxy_map | 1707x921 | 1.853 | 1.125 / 1.173 | 1.500 / 1.564 | **2.250 / 2.345** | yes, and **non-uniformly** (4 % taller than wide: 1.853 → 1.778) |
| colony_summary | 1672x941 | 1.777 | 1.148 | 1.531 | **2.297** | yes, 2.3x |
| planets | 1920x1080 | 1.778 | 1.000 | 1.333 | **2.000** | yes, 2x |
| fleets | 3840x2160 | 1.778 | 0.500 | 0.667 | **1.000** | **no** |
| game_menu | 1108x1419 | 0.781 | 0.595 | 0.793 | **1.190** | slightly, 1.19x |
| in:frame_* (3) | 1920x1080 | 1.778 | 1.000 | 1.333 | **2.000** | yes, 2x |

**A correction, not applied (analysis-only order).** Decision 70's
text, and the table in `151-new-fleets-frame-findings.md`, give the
GAME menu as 1.733x at the reference and 3.466x at 2160p. That is
1920/1108, as if the popup were stretched to the window width, and it
is not. `gmframe.placement` scales it by 844/1419 = 0.595 at the
reference, so it is **downscaled** up to 1440p and upscaled 1.19x at
2160p. The rest of decision 70 is untouched: the GAME menu is still
upscaled at 4K. Whether to correct the decision's text is Data's call.

### A2. Measured sharpness of the ring

The ring is the band 60 reference px deep from each edge, the same on
every frame, opaque pixels only (method below). **Edge** is the
10–90 % rise of the 400 strongest edges, median, in px of the image
measured. About 1.6 px is a crisp edge, and a k-times upscale makes it
about k times wider. **lapnorm** is Laplacian variance over luma
variance: fine detail per pixel with the contrast divided out. Higher
means more detail. **Detail ratio** is lapnorm at 2160p over lapnorm at
1080p: how much new detail the extra 2160p pixels carry. A plain 2x
upscale gives about 0.11.

| frame | edge src | 1080p | 1440p | **2160p** | lapnorm src | 1080p | 1440p | **2160p** | detail ratio | block8 |
|---|---|---|---|---|---|---|---|---|---|---|
| **fleets** | 1.60 | 1.59 | **1.65** | **1.60** | 0.494 | 1.597 | 0.827 | **0.494** | **0.31** | 0.89 |
| game_menu | 1.61 | 1.68 | 1.70 | 2.05 | 0.844 | 1.705 | 0.958 | 0.316 | 0.19 | 1.01 |
| **planets** | 1.60 | **1.60** | 2.07 | 2.90 | 2.612 | **2.612** | 0.776 | 0.299 | 0.11 | 1.02 |
| colony_summary | 1.58 | 2.03 | 2.44 | 3.38 | **2.782** | 1.199 | 0.539 | 0.154 | 0.13 | 1.17 |
| in:frame_map_4panels | 1.75 | 1.75 | 2.54 | 3.62 | 0.487 | 0.487 | 0.137 | 0.049 | 0.10 | 0.94 |
| in:frame_map_sidebar | 1.75 | 1.75 | 2.69 | 3.77 | 0.503 | 0.503 | 0.142 | 0.051 | 0.10 | 0.95 |
| galaxy_map | 2.09 | 2.79 | 3.01 | 3.88 | 1.124 | 0.487 | 0.214 | 0.059 | 0.12 | 1.13 |
| in:frame_plain | 1.75 | 1.75 | 2.58 | 3.89 | 0.497 | 0.497 | 0.137 | 0.049 | 0.10 | 0.99 |

What the numbers say:

- **At 2160p only Fleets is crisp at the edges** (1.60 px). Every other
  full-screen frame is 2.9–3.9 px, which is 1.8–2.4 times as soft.
- **Fleets' own 4K pixels are not detailed.** Its source lapnorm
  (0.494) is a fifth of Planets' (2.612) and a sixth of the colony
  frame's (2.782). That is the fingerprint of an upscale that
  sharpened the edges but added no texture. It agrees with the recorded
  history, a 1672x940 draft upscaled by Data. Downscaled to 1080p, its
  lapnorm (1.597) lies between the colony frame's and Planets'.
- **At 1080p Planets is the sharpest frame** in both metrics (1.60 px,
  2.612), because it is drawn 1:1 there.
- **Galaxy map is soft even at its source** (2.09 px native, the only
  source above 1.75). It is upscaled 1.17x at 1080p and 2.35x at 2160p
  on top of that, and non-uniformly.
- **The 18 September set** is soft at its source. Its lapnorm, about
  0.5 at 1:1, is the lowest native detail of any 1920 frame, and it
  ends at about 0.05 at 2160p, the lowest there too.
- **GAME menu** is a popup and only 1.19x at 2160p, so it holds up well
  (2.05 px). It is not a full-screen ring (see B).
- **No JPEG-like 8-px grid anywhere**: block8 is 0.89–1.17. The colony
  (1.17) and galaxy (1.13) frames are the highest, which is a hint but
  not a visible grid in the crops.

### A3. Visible artefacts (from the crops, as seen, for Data to confirm)

- **Planted checkerboard, opaque.** `frame_plain` and
  `frame_map_4panels` carry a light grey/white checkerboard in their
  outer corners at **alpha 255**: a transparency pattern painted into
  the image. `frame_map_sidebar`'s corner is opaque grey from x ≥ 16.
  At 2160p it shows as a white-grey chequered wedge in the window
  corner (`crop_bottom_right_corner_2160p_100pct.png`).
- **Lamp cores (cockpit family).** In `view_cockpit_tl_2160p_200pct.png`
  the Fleets corner lamp has a blown-out white core and smeared,
  painterly glow rings. Its rivets and plate bevels are crisp, but
  their highlights are smooth blobs with no texture. This looks like
  AI-upscaler smearing, while the edges stay sharp. The galaxy and
  colony lamps are plainly blurred, with rivets as soft dots. Planets
  sits between the two: soft, but with scratches and grime still
  readable.
- **Top edge.** In `view_cockpit_top_2160p_200pct.png` the colony
  frame's top rail carries embossed glyph-like ornaments (spiral,
  brackets). Planets and Fleets carry plain rails with grime. The galaxy
  map's shows its title plate (green = hole).
- **No halos** (bright or dark fringes along the inner rim) were seen
  on any frame. The inner alpha edges are hard (B3).

---

## B. Suitability as a shared ring

### B1. Ring thickness and content area

The thickness is the median distance from the image edge to the first
hole pixel on 41 scanlines over the middle 60 % of each side, converted
to reference px. The spread is the 10th–90th percentile of those
scanlines, in image px, and shows where plates, rails and struts reach
into the ring.

| frame | left | right | top | bottom | content left (ref px) | spread L / R / T / B (image px) |
|---|---|---|---|---|---|---|
| planets | 74.0 | 75.0 | 75.0 | 88.0 | **1771 x 917** | 74..74 / 75..75 / 75..75 / 88..88 |
| colony_summary | 99.9 | 102.2 | 87.2 | 70.0 | 1718 x 923 | 87..87 / 89..91 / 76..76 / 61..64 |
| galaxy_map | 91.1 | 115.9 | 65.7 | 104.4 | 1713 x 910 | 81..81 / 103..103 / **7..56** / **89..149** |
| in:frame_plain | 96.0 | 95.0 | 91.0 | 87.0 | 1729 x 902 | 95..96 / 95..96 / 81..92 / 87..87 |
| in:frame_map_sidebar | 100.0 | 99.0 | 102.0 | 102.0 | 1721 x 876 | 100..101 / 99..106 / 101..106 / 102..118 |
| in:frame_map_4panels | 101.0 | 101.0 | 91.0 | 160.0 | 1718 x 829 | 101..112 / 101..112 / 91..91 / 160..173 |
| fleets (to first hole) | 116.5 | 228.0 | 112.5 | 116.5 | 1576 x 851 | 228..332 / **456..2126** / **211..1607** / 228..239 |
| game_menu (popup) | 68.4 | 68.4 | 64.8 | 70.2 | opening 522 x 709 | 115..116 / 115..115 / 108..109 / 118..118 |

**Fleets' metal ring is not its "first hole" distance.** A dark chassis
plate lies between the ring and the holes, and the right column and the
ship grid lie beyond it. Luma profiles across the four sides show the
metal ending at about **78 reference px** on the left, top and right,
the same as Planets. The two profiles have their peaks at the same
depths: bright rail at about 54–60 ref px, inner rim at about 72
(numbers in the method section). **The Fleets ring and the Planets ring
are the same design at the same depth**, which is consistent with
Fleets' first version having been the Planets ring (a47650f). Cut at
about 80 ref px, Fleets leaves about 1760 x 920 of content, as Planets
does.

### B2. Symmetry and consistency

The measure is the mean absolute luma difference (0–255) inside the
common 60-ref-px band. 0 would be a mirrored copy.

| frame | TL↔TR | TL↔BL | TL↔BR | left↔right | top↔bottom |
|---|---|---|---|---|---|
| colony_summary | 22.2 | 30.6 | 30.6 | 29.6 | 34.2 |
| fleets | 24.1 | 49.2 | 50.2 | 28.4 | **21.3** |
| galaxy_map | 20.9 | 34.4 | 33.1 | 33.9 | 57.0 |
| planets | 33.7 | 54.6 | 55.0 | **23.6** | 40.0 |
| game_menu | 32.6 | — | — | 4.5 | 74.3 |
| in:frame_plain | 14.3 | 84.0 | 80.5 | 21.2 | 72.3 |
| in:frame_map_sidebar | 39.6 | 68.2 | 65.7 | 26.1 | 85.8 |
| in:frame_map_4panels | 19.0 | 87.6 | 85.3 | 29.6 | 68.5 |

**No frame has mirrored corners or edges.** Every one was painted as a
whole picture, so its four corners are four drawings. In the cockpit
family the top and bottom corners differ more than left and right
(TL↔BL 30–55 against TL↔TR 21–34). The top edges carry lamp groups
that the bottom edges do not. The 18 September set differs most from
top to bottom (68–88): title plate at the top, button plates at the
bottom. A shared ring that must look the same on every screen, and be
checkable as the same (decision 55's gap), would be easiest to hold if
it were **built from one corner and one edge segment per side**.
Otherwise every screen's copy has to be compared against one master
image.

**Screen-specific content baked in, to remove or move to a variant
(decision 12):**

| frame | baked in |
|---|---|
| galaxy_map | title plate in the top edge (top spread 7..56 px: the plate's hole reaches to 7 px from the edge); nav-row plates and lamp pairs in the bottom (89..149) |
| colony_summary | glyph ornaments on the top rail; bottom row plates touching the ring (61..64) |
| planets | interior struts meeting the ring in T-junctions (one vertical on the right, the horizontal above the bottom row), otherwise none: spread 0 on all four sides |
| fleets | dark chassis plate inside the ring on all sides; right column, ship grid and button rails run into it (spread 456..2126 / 211..1607) |
| in:frame_plain | title plate top, two plates bottom left/right |
| in:frame_map_sidebar | title plate top; sidebar struts |
| in:frame_map_4panels | title plate top; seven-button rail in the bottom (160 ref px) |
| game_menu | a portrait popup: its whole shape is specific |

### B3. The inner edge

| frame | soft alpha px L/R/T/B (16 ≤ α < 250) | wobble L/R/T/B (image px) | verdict |
|---|---|---|---|
| planets | 0/0/0/0 | 0/0/0/0 | hard, straight, measurable |
| colony_summary | 0/0/0/0 | 0/2/0/3 | hard, straight |
| game_menu | 0/0/0/0 | 1/0/1/0 | hard, straight |
| galaxy_map | 1/1/1/1 | 0/0/49/60 | hard; top and bottom wander (plate, nav row) |
| in:frame_* | 1–2 | 0–16 | hard, near-straight |
| fleets | 0/0/0/0 | 104/1670/1396/11 | hard, but the "inner edge" is the screen's layout, not a ring |

Every frame has a hard alpha cut (at most 2 px of partial alpha). A
hole can be measured off any of them. Only Planets and colony_summary
have an inner ring edge that is also straight all round.

### B4. Can the ring be cut out cleanly, and what needs repainting

- **Planets:** yes. This has been done once in this tree: a47650f cut
  the Planets ring out by thickness (ring about 74 px against the widest
  strut's 29, an opening with a disc of radius 18) and shipped it as
  the first Fleets frame. What needs repainting: the T-junction stubs
  where the struts met the ring, which becomes plain inner rim.
- **Fleets:** yes, but by a CUT LINE, not by its alpha. Its alpha ends
  at the screen's holes, 116–228 ref px in, so the ring has to be cut
  at about 80 ref px (about 160 source px), where the metal ends. The
  inner rim along that line then needs repainting as a rim, because
  today it runs into the chassis plate. Its source has no alpha, and
  the tracked frame does.
- **Colony:** yes along its straight edges. The top-rail ornaments and
  the bottom plates would have to be repainted as plain rail.
- **Galaxy map:** the title plate and the bottom row would have to be
  repainted, and the 4 % aspect stretch undone. There is little ring
  left that is not either softer than the rest or specific.
- **18 September set:** the corners must be repainted (the painted
  checkerboard), and the title plates and bottom plates removed. It is
  also the other style family, and it was rejected in 132.

---

## C. Recommendation

### Ranking as the base for the shared outer ring

| rank | candidate | why, in numbers | against it |
|---|---|---|---|
| **1** | **fleets, outer ~80 ref px** | only frame not upscaled at 2160p; edge 1.60 / 1.65 / 1.59 px at 2160p / 1440p / 1080p; highest detail ratio (0.31); already on decision 70's canvas; same ring design and depth as Planets | its 4K pixels carry the detail of a 1672 px draft (source lapnorm 0.494); lamp cores smeared; has to be cut by a line and its inner rim repainted |
| **2** | **planets** | sharpest at 1080p (1.60 px, lapnorm 2.612); cleanest ring (spread 0, wobble 0, hard alpha); thinnest ring, most content (1771 x 917); already cut out once (a47650f) | 2.0x upscaled at 2160p: edge 2.90 px, lapnorm 0.299 |
| 3 | colony_summary | most detail per source pixel (lapnorm 2.782), straight inner edge, best corner consistency (TL↔BL 30.6, T↔B 34.2) | 2.3x at 2160p (3.38 px); top-rail ornaments; decision 55 ties it to its own holes |
| 4 | galaxy_map | same family as the other three | soft at its source already (2.09 px), 2.35x at 2160p (3.88 px), non-uniform stretch, title plate and nav row baked in |
| 5–7 | in:frame_map_4panels / _sidebar / _plain | 1:1 at 1080p, hard alpha | least detail of all (lapnorm about 0.5 native, 0.05 at 2160p), 3.6–3.9 px at 2160p, painted checkerboard, other style family, rejected in 132 |
| — | game_menu | 1.19x at 2160p (2.05 px) | a portrait popup, not a full-screen ring; other style family |

Fleets and Planets are close, and the choice between them is the
choice between the two questions. **For sharpness at 1440p and 2160p,
Fleets. For a clean ring and the best 1080p image, Planets.** The two
are one design, so Data does not have to pick against the look.

### What Data would have to do, for rank 1

1. **Cut** the Fleets frame's outer ring at about 160 source px (about
   80 ref px) on all four sides. Check the cut line against the Planets
   ring's inner rim (72–78 ref px), so the two agree where they are
   one design.
2. **Repaint the inner rim** along the cut as a continuous rim. Today
   the chassis plate and, on the right, the column and grid rails run
   into it.
3. **Decide on the corners.** Either keep the four painted corners, or
   make one corner and one edge segment per side and mirror or repeat
   them. Only the second makes "every screen is the same at the edge"
   something a check can hold byte for byte (decision 55's gap).
4. **Repaint the lamp cores** if the smeared glow in
   `view_cockpit_tl_2160p_200pct.png` bothers Data at 4K.
5. **Keep it at 3840x2160** (decision 70). It is already there, so no
   re-export is needed and none should be made. Resampling it again
   would only lose detail.
6. **Anything screen-specific** (a title plate like the galaxy map's,
   a lamp pair) goes into a variant image, per decision 12. The shared
   ring holds none of it.

### Plainly: none of them is truly sharp at 2160p

At 2160p only Fleets passes on edge width. It passes because its
edges were sharpened during an upscale. Its texture is what a
1672-px-wide picture can hold, and that shows at 200 % as smooth
highlights and smeared lamps. A ring that is sharp in texture at 2160p
needs a source that was **painted or rendered at 3840x2160 or more** (a
paint-over of the rank-1 cut at full size, a 3D or vector render, or
an AI generation made at 4K rather than upscaled to it). Measured the
same way, that source should show about 1.6 px at 2160p. It should
also show a detail ratio clearly above the 0.1–0.3 of everything here:
its 2160p pixels should carry more detail than a 2x upscale of its
1080p pixels.

---

## Evidence, for Data to look at (not findings)

In `~/orionlayer-fixtures/evidence/work_order_168/` (37 files):

| file | what to look at |
|---|---|
| `00_contact_sheet.png` | all eight at 2160p, scaled down: are the style families as described, is the popup at its real size? |
| `view_cockpit_tl_2160p_200pct.png` | the four cockpit frames, top-left lamp, 200 %: is Fleets' lamp smeared, are the galaxy and colony rivets as soft as they measure? |
| `view_cockpit_top_2160p_200pct.png` | top-rail middle, 200 %: colony's ornaments, galaxy's title plate |
| `crop_{top_left_corner,top_edge_mid,left_edge_mid,bottom_right_corner}_2160p_{100,200}pct.png` | the same four ring spots on the seven full-screen frames, 1:1 and 200 % (magenta = hole): the checkerboard in the 18 September corners, edge softness side by side |
| `render_<frame>_{1920x1080,2560x1440,3840x2160}.png` | each frame as the app scales it, at the three resolutions |
| `measurements.txt`, `measurements.json` | every number in this report |

---

## Method

**Rerun** (writes only to the given paths):

```bash
python tools/frame_ring_measure.py --json ~/orionlayer-fixtures/evidence/work_order_168/measurements.json --evidence ~/orionlayer-fixtures/evidence/work_order_168 > ~/orionlayer-fixtures/evidence/work_order_168/measurements.txt
```

The full definitions are in the script's docstring. In short:

- **Ring, per image, from its own alpha only.** Opaque is α ≥ 250 and
  hole is α < 16 (`tools/frame_holes`'s threshold). Thickness per side
  is the median of 41 scanlines over the middle 60 % of that side,
  counted from the first opaque pixel (so the popup's transparent
  margin is not a hole) to the first hole pixel.
- **The same regions on every frame.** Sharpness and symmetry use a band
  60 **reference** px deep from each image edge, opaque pixels only,
  kept 3 px off its inner side and eroded by 1. 60 is under the
  thinnest measured ring (65.7, the galaxy map's top), so no hole,
  strut, chassis plate or alpha edge is measured as "metal". For the
  GAME menu the band is all of its opaque art, eroded by 3.
- **Renders** are `pygame.transform.smoothscale` of the whole image,
  exactly as `ScreenBase._scale_frame` does it. For the popup the size
  comes from `gmframe.placement`'s factor. The ring mask is scaled with
  it (nearest).
- **Metrics on luma** (0.299 R + 0.587 G + 0.114 B). *lapnorm* is
  var(3x3 Laplacian) / var(luma). *edge10_90* is the median 10–90 %
  rise over the 400 strongest non-max-suppressed Sobel peaks (≥ 12 px
  apart, range ≥ 20 levels), on a 25-px profile along the dominant
  gradient axis, taking the crossings nearest the centre. *block8* is
  the mean |gradient| on 8-px boundaries over the mean elsewhere, both
  axes. *Symmetry* is the mean |Δluma| between the top-left 60x60-ref
  square and each other corner flipped onto it, and between opposite
  band strips, opaque pixels of both only. *Inner soft / wobble* are the
  partial-alpha pixels before the hole, and the p10–p90 of the
  thickness, per side.
- **Two things measured outside the script, stated so they can be
  checked:**
  - Fleets' metal depth came from mean luma profiles across each side
    (rows 300–800 for left and right, columns 500–1400 for top and
    bottom) of both frames smoothscaled to 1920x1080, sampled every 6
    ref px. Left side, Fleets:
    `2 106 81 33 21 27 21 50 30 56 68 0 104 26 15 14 12 59…`. Left
    side, Planets: `16 65 93 16 22 17 71 32 118 132 1 66 64 1 0 0…`.
    Both have the rim dip at sample 10 (60 ref px) and the last rim
    peak at sample 12 (72). Fleets continues into its chassis plate
    from sample 13 on, and Planets into its hole.
  - The screenshot scales are the image widths over 2442.
- **What the metrics cannot see.** No metric here tells a painted
  detail from an invented one, or a pleasing lamp from a smeared one.
  The A3 observations come from looking at the crops, and they are
  listed as evidence for Data for that reason.
