# 145 — `inner_frame.png`: usable as inner frame? 9-slice or plain scaling? (findings only)

**Findings only.** No code, no skin, no `boxes.json`, no assets, no
commit of the source. Method, baseline and the `nineslice.py`
constraints are 143's and are reused, not re-derived.

**THE ORDER ARRIVED TRUNCATED.** It ends mid-sentence at

> *"Plain scaling: render the frame into those rects. Report edge
> thickness per side"*

and nothing follows — no rest of that bullet, no 9-slice bullet, no
question 3. I answered question 1 in full and question 2 as far as it
is legible, finishing the cut sentence the only way it can go (the
resulting rail thickness per side, measured). **Anything the order
asked for after that point is not in this brief because it did not
reach me.** The remaining questions are listed at the end.

## The source

Exactly one match on the machine:

| | |
|---|---|
| Path | `~/Downloads/inner_frame.png` (only match; `find ~ -iname "inner_frame*"`) |
| Size | 336 068 bytes |
| Pixels | **1652 x 901**, **RGBA**, PNG |
| sha256 | `573a4274adf3f807387be75986b2e8cee0508944dc51403d208965f9b3e64c0e` |

Copied to `~/orionlayer-fixtures/evidence/work_order_145/inner_frame.png`;
the copy's sha256 is identical, so the evidence no longer depends on
`~/Downloads`.

Aspect 1652/901 = **1.8335**.

## 1. Alpha

**The interior is genuinely transparent.** Over the centre 60 % box
alpha is 0 everywhere (min 0, max 0). Across the whole image:

| alpha | pixels | share |
|---|---|---|
| 0 | 1 315 348 | 88.37 % |
| 255 | 172 650 | 11.60 % |
| 1..254 | 454 | **0.03 %** |

Only nine distinct alpha values exist — it is a near-binary mask, not
a soft one.

**No RGB hides under the transparent pixels.** All 1 315 348 of them
are exactly `(0, 0, 0, 0)`: R, G and B are 0..0. So the fundament's
`BLEND_RGB_ADD` hazard — "RGB hiding under transparent pixels becomes
a visible rectangle" — **does not apply to this file.** It is already
blanked the way that fact asks for.

**Cost of keying: none.** There is no white to key; the question's
premise does not hold for this asset.

**But there IS a halo, and it is measurable.** The 454 partial-alpha
pixels carry RGB **(235.3, 236.0, 236.2)** — near-white — while the
opaque frame body averages **(66.9, 67.4, 67.7)**, dark metal. That is
the signature of an asset keyed off a white background: the
antialiased rim kept its white and only lost opacity. Composited over
a dark panel those pixels blend toward white, so the frame carries a
**thin, sparse light fringe** on its edges.

Scale of it: 454 px out of 1 487 998 non-transparent-or-opaque
decisions, i.e. 0.03 % — a fringe you will find by looking for it, not
a halo that reads across the screen. Removing it is one operation
(premultiply the rim toward the frame's own colour, or discard
alpha < 255 given the mask is near-binary anyway), and losing those
454 pixels costs the only antialiasing the asset has.

Two further alpha facts that matter for question 2:

* The frame **runs to the image edge** — the outer 4 px ring averages
  alpha 209.8, it is not inset. Nothing can be trimmed off the outside
  without cutting metal.
* Measured rails, opaque alpha at the midlines: **left 34, right 34,
  top 33, bottom 30** px. Left and right agree exactly; top and bottom
  differ by 3, and there are 2 fully transparent rows at the bottom.

## 2. Plain scaling vs 9-slice

### Which boxes would carry it

52 box entries wear `inner_panel` or `thin_border` across eight
screens (86 entries counting both resolution tables). Fleets first, as
asked, then the rest.

### Fleets, at all four resolutions

Aspect against the source's 1.8335, and the per-axis scale factor a
plain stretch would need. "anis" is the anisotropy — how many times
more one axis is scaled than the other, i.e. how far from proportional
the stretch is.

| box | 1080p | aspect | anis | 2160p |
|---|---|---|---|---|
| `inset_map` | 676x403 | 1.677 | **1.09** | 1352x806 |
| `ship_panel` | 680x412 | 1.650 | **1.11** | 1360x824 |
| `prev/next_fleet` | ~70x42 | 1.65 | 1.08–1.12 | ~140x84 |
| `icon_area` | 605x658 | 0.919 | **1.99** | 1210x1316 |
| `button_band` | 645x179 | 3.603 | **1.97** | 1290x358 |
| `status_text` | 447x47 | 9.511 | **5.19** | 894x94 |
| `status_band` | 662x55 | 12.036 | **6.56** | 1324x110 |
| `scroll_column` | 33x645 | 0.051 | **35.84** | 66x1290 |

Only two Fleets boxes are within 11 % of the source's proportions.

### Plain scaling: the resulting rail thickness per side

This is the cut sentence, finished. Source rails L34 R34 T33 B30.

| box | res | left | right | top | bottom | L/T |
|---|---|---|---|---|---|---|
| `inset_map` | 1080p | 13.9 | 13.9 | 14.8 | 13.4 | 0.94 |
| `inset_map` | 2160p | 27.8 | 27.8 | 29.5 | 26.8 | 0.94 |
| `ship_panel` | 1080p | 14.0 | 14.0 | 15.1 | 13.7 | 0.93 |
| `icon_area` | 1080p | 12.5 | 12.5 | 24.1 | 21.9 | **0.52** |
| `button_band` | 1080p | 13.3 | 13.3 | 6.6 | 6.0 | **2.02** |
| `status_band` | 1080p | 13.6 | 13.6 | **2.0** | **1.8** | **6.76** |
| `scroll_column` | 1080p | **0.7** | **0.7** | 23.6 | 21.5 | **0.03** |
| `btn_support` | 1080p | 2.8 | 2.8 | **1.5** | **1.4** | 1.81 |

Read it as: plain scaling holds only where the box is already close to
1.83:1. Everywhere else the frame stops being a frame — `status_band`
gets a 2 px hairline over and under a 14 px bar, `scroll_column` gets
a 0.7 px side, and `btn_support` falls under 2 px on three sides at
1080p.

Rendered side by side in `SCALING_plain_vs_nineslice.png`.

### 9-slice: the constraint that decides it

143 established that `core/nineslice.py` takes **nine separate PNGs**,
blits corners **unchanged**, **smoothscales** each edge in one
dimension, and uses **one scalar** for the corner
(`corner = parts["top_left"].get_width()`), so the corner must be
square.

Measured here: the top rail's opaque height settles at its constant 34
px from **x = 115**, so the corner ornament needs **k ≈ 123** to be
contained. `render()` falls back to scaling the whole image when
`width < l+r+2 or height < t+b+2` — so a box needs **≥ 248 x 248 px**
to get the 9-slice path at all.

| screen | skin | boxes | 9-slice path at 1080p | at 2160p |
|---|---|---|---|---|
| fleets | thin_border | 16 | **3** | 4 |
| custom_race | thin_border | 3 | 3 | 3 |
| empire_identity | thin_border | 3 | 3 | 3 |
| galaxy_map | thin_border | 2 | 2 | 2 |
| game_menu | thin_border | 16 | 2 | 3 |
| research_select | inner_panel | 8 | **0** | 8 |
| research_select | thin_border | 2 | 2 | 2 |
| select_race | thin_border | 2 | 2 | 2 |

So at 1080p **17 of 52** boxes would take the 9-slice path and the
other 35 would silently fall back to plain scaling — including every
Fleets button, both status boxes and the scroll column. `research_select`'s
eight `inner_panel` entries take it at 2160p and none at 1080p, i.e.
the same screen would be drawn two different ways at two resolutions.

### What the render shows

In `SCALING_plain_vs_nineslice.png`, 9-slice (right) keeps the corner
ornament and the 34 px rails at every size and looks consistent for
`inset_map`, `ship_panel` and `icon_area`. For `button_band` (179 px
tall) and `status_band` (55 px tall) the 123 px corners meet and
overlap — the frame visibly breaks, which is precisely the case the
engine's own threshold hands back to plain scaling.

## Verdict on the two questions I can answer

* **Alpha: usable as-is.** Transparent interior, no hidden RGB, no
  keying needed. One caveat with a number on it: a 454-pixel
  near-white fringe from a white-background key.
* **9-slice vs plain scaling is not a choice between two options for
  the whole tree — it is decided per box by size**, and the engine
  already makes that decision at 248 px. Plain scaling is only
  defensible where the box is near 1.83:1, which among Fleets boxes is
  `inset_map` and `ship_panel` and nothing else.

## Not answered, because the order was cut off

Whatever followed *"Report edge thickness per side"* — the rest of the
plain-scaling bullet, the 9-slice bullet that presumably mirrored it,
and any question 3 (decision 34's taxonomy, a recommendation, a
deliverable format). Re-send from that point and I will finish it
against the same evidence.

## Evidence

`inner_frame.png` (copy), `SCALING_plain_vs_nineslice.png`.
