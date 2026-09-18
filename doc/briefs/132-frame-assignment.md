# Work order 132 — the 18 September frame set: measured, assigned, mostly unused

Part A of work order 132, 18 September 2026. Everything below is
measured off the files in
`~/orionlayer-fixtures/incoming/frames_18sep/`, which are byte-identical
copies of Chat's originals in `~/Downloads/` (sha256 checked both ways).
Chat's descriptions were treated as claims and re-measured; where they
differ from the files, the files win and the difference is named.

**The short answer: one of four assets is assigned.** `frame_plain.png`
goes to Select Race. The other three fit no screen this project has, for
reasons that are counts and aspect ratios rather than taste, and they
stay unused.

---

## 1. How every screen is framed today

| screen | how it is framed | asset | size | holes |
|---|---|---|---|---|
| `galaxy_map` | fixed image, cutouts derived (decision 3) | `assets/frame.png` | 1706x922 | **10** |
| `colony_summary` | fixed image, rects from `layout_reference.json` (decision 55) | `assets/frame.png` | 1672x941 | 12 |
| `planets` | fixed image, cutouts derived (decision 3) | `assets/frame.png` | 1920x1080 | **5** |
| `game_menu` | fixed image, plain-scaled, one opening (decision 69) | `assets/frame.png` | 1108x1419 | 1 |
| `new_game` | shared 9-slice (`USE_FRAME`) | `core/frame.py` tiles | — | — |
| `select_race` | shared 9-slice, variant `select_race` | `core/frame.py` tiles | — | — |
| `custom_race` | shared 9-slice | `core/frame.py` tiles | — | — |
| `empire_identity` | shared 9-slice | `core/frame.py` tiles | — | — |
| `main_menu` | none (own background image) | — | — | — |
| `research_select` | **none** (work order 130: "frame and artwork come later") | — | — | — |

`ScreenBase._load_frame` / `_render_frame_image` already do the fixed
image: the image is stretched over the reference area and the 9-slice is
the fallback when there is none. Nothing new is needed to hang an image
on a screen.

## 2. The new assets, measured

`frame_holes.find_holes` reads regions of alpha < 16. All three large
frames are stored at exactly 1920x1080.

| asset | size | aspect | openings | other features |
|---|---|---|---|---|
| `frame_map_sidebar.png` | 1920x1080 | 1.7778 | **8** | 1 title plate (752, 8, 415, 61) |
| `frame_map_4panels_7buttons.png` | 1920x1080 | 1.7778 | **5** | 1 title plate + **7 opaque button plates** |
| `frame_plain.png` | 1920x1080 | 1.7778 | **1** | 1 title plate (643, 6, 633, 73), 2 corner plates |
| `panel.png` | 2144x704 | 3.0455 | **1** | brackets at the middle of each edge |

### The openings

    frame_map_sidebar      (100, 100, 1342, 672)  aspect 1.997   big left
                           (1484, 100, 338, 672)  aspect 0.503   right column
                           (100, 801, 396, 177)   aspect 2.237   bottom 1
                           (528, 801, 559, 177)   aspect 3.158   bottom 2
                           (1120, 801, 322, 177)  aspect 1.819   bottom 3
                           (1488, 801, 329, 55)   aspect 5.982   stacked 1
                           (1488, 871, 329, 49)   aspect 6.714   stacked 2
                           (1488, 935, 329, 44)   aspect 7.477   stacked 3

    frame_map_4panels      (101, 91, 1718, 610)   aspect 2.816   one wide opening
                           (112, 736, 406, 185)   aspect 2.195   bottom 1
                           (556, 735, 385, 185)   aspect 2.081   bottom 2
                           (979, 736, 385, 185)   aspect 2.081   bottom 3
                           (1403, 735, 405, 186)  aspect 2.177   bottom 4

    frame_plain            (92, 81, 1734, 912)    aspect 1.901   margins L92 R94 T81 B87

    panel                  (92, 88, 1959, 528)    aspect 3.710

### The seven plates are real, and they are opaque

Chat's claim, confirmed after a first measurement missed them: they are
dark **teal**, `rgba(20, 31, 37, 255)`, not near-black, so a luminance
threshold tuned for black does not see them. Detected as opaque regions
with `b > r + 8`:

    (795, 12, 327, 59)     the title plate
    (127, 966, 204, 61)    (374, 966, 203, 61)   (620, 965, 192, 62)
    (853, 967, 212, 60)    (1105, 967, 193, 60)  (1341, 967, 205, 60)
    (1588, 967, 205, 60)

They carry alpha 255. `frame_holes.find_holes` reports **5** holes for
that file and none of them is a button.

### The irregularities, in numbers

Fields that look alike are not alike. At 1920x1080 image px equal
reference px, so every number below is also a reference-pixel number,
and doubles at 3840x2160.

| asset | group | spread |
|---|---|---|
| `frame_map_sidebar` | three bottom fields | **width 237 px** (322 / 396 / 559); heights and tops exact; gaps 32, 33 |
| `frame_map_sidebar` | three stacked rows | **height 11 px** (55 / 49 / 44) on rows that look identical; widths exact |
| `frame_map_4panels` | four bottom fields | **width 21 px** (385..406); height 1 px; top 1 px; gaps 38, 38, 39 |
| `frame_map_4panels` | seven button plates | **width 20 px** (192..212); height 2 px; top 2 px; gaps 40..43 |

These are the numbers decision 3 would turn into box coordinates.

### The stretch claim: NOT settled

Chat says the three large frames were generated at about 1670–1683 px
wide and scaled to 1920x1080. I cannot confirm or refute that from the
files. Mean |gradient| per axis on the opaque metal, with the committed
frames as controls:

| file | \|dx\| | \|dy\| | dx/dy |
|---|---|---|---|
| NEW `frame_map_sidebar` | 12.9 | 21.5 | 0.601 |
| NEW `frame_map_4panels` | 11.1 | 17.6 | 0.629 |
| NEW `frame_plain` | 13.4 | 16.3 | 0.820 |
| committed `colony_summary` | 11.3 | 18.7 | **0.604** |
| committed `galaxy_map` | 17.7 | 19.0 | 0.936 |
| committed `planets` | 17.1 | 25.3 | 0.676 |
| committed `game_menu` | 18.0 | 15.8 | 1.142 |

The new ratios sit inside the range the committed frames already show —
`colony_summary` has the same 0.604 and is stored at its native
1672x941. So this measurement does not isolate a horizontal stretch.

**What IS a difference, and it is decision-relevant:** every committed
frame is stored at the size it was generated (1672x941, 1706x922,
1108x1419) and scaled by the code at load. These three are stored
already resampled to 1920x1080, so whatever resampling happened is baked
in and the renderer no longer chooses the filter or the target. That is
parked as a question for Data, not decided here.

## 3. The assignment

Fit is by opening COUNT, ASPECT and the boxes the screen needs. A screen
that already has a frame is switched only if the new one fits at least
as well.

| asset | screen | verdict |
|---|---|---|
| `frame_plain.png` | **select_race** | **ASSIGNED** — every box inside the opening at both resolutions the screen defines |
| `frame_plain.png` | empire_identity | near fit, `busy_panel` 3 px over the top — parked |
| `frame_plain.png` | custom_race, main_menu | no — 6 and 7 boxes outside, up to 66 px |
| `frame_map_sidebar.png` | — | **no fit anywhere** |
| `frame_map_4panels_7buttons.png` | — | **no fit anywhere** |
| `panel.png` | — | **no fit anywhere** |

### Content extents against the openings

| screen | content bounding box (ref) | aspect |
|---|---|---|
| `select_race` | (100, 115, 1720, 735) | 2.340 |
| `empire_identity` | (110, 78, 1700, 907) | 1.874 |
| `custom_race` | (75, 107, 1770, 951) | 1.861 |
| `galaxy_map` | (90, 66, 1721, 969) | 1.776 |
| `planets` | (72, 73, 1775, 921) | 1.927 |
| `main_menu` | (1592, 178, 300, 833) | 0.360 |

For a single-opening frame the test is not aspect agreement but
CONTAINMENT: does every box lie inside the opening. Select Race's does,
at 1920x1080 and at 2560x1440 (it defines both, and its rects differ
between them). Aspect matters where an opening must be covered by a
body, which is decision 69's case, not this one.

### The two questions, answered

**Q1. Can `frame_map_sidebar.png` replace the galaxy map's frame, given
how the `nav_*` boxes are derived today?**

**No.** The galaxy map's cutouts are ten names —
`map_area`, `sidebar`, `title` and seven `nav_*` — and
`tools/frame_holes.py --write` derives every one of them from a
transparent hole (decision 3). Its current frame has exactly ten holes.
The asset has **eight**, and they are the wrong eight: there is no title
opening at all, and the six small ones are three wide fields
(aspects 2.237, 3.158, 1.819) plus three narrow stacked rows
(5.982, 6.714, 7.477) where the screen needs **seven** buttons of one
shape (today 213x50, aspect 4.26). `name_holes` could not produce the
name set `RULE_NAMES["galaxy_map"]` requires, so the regenerator would
fail before the smoke assertion ever ran.

**Q2. Can the seven plates of `frame_map_4panels_7buttons.png` carry the
seven nav buttons, given that they are not holes?**

**No, not without a second derivation rule.** The plates are opaque
(alpha 255); `find_holes` reads alpha < 16 and reports five holes for
that file, none of them a button. Deriving boxes from opaque teal
regions would be a mechanism beside decision 3's, keyed on a colour
rather than on transparency — a new rule, and a fragile one, since the
same teal is the title plate and the corner plates. This order does not
authorise inventing it, and the file fails on the large opening anyway:
one wide opening of aspect 2.816 and no right column, where the galaxy
map needs a `sidebar` cutout (today 244x851, aspect 0.287).

### Why the other two are unused

`frame_map_sidebar.png` — eight openings in an arrangement no screen
has. Nearest is Planets (list, side panel, three bottom panels = five):
the top two map cleanly, but the asset splits the bottom left into three
where Planets has two and the bottom right into three stacked rows where
Planets has one. Changing Planets' panel count to suit an asset is a
content change this order does not authorise.

`panel.png` — opening aspect 3.710. The popups it was meant for are
`help_popup` (1.35), `system_box` (1.09), `fleet_box` (0.86) and the
GAME menu body (0.739). Plain-scaling it onto any of them distorts by
2.7x or more; nine-slicing it would stretch the mid-edge brackets, which
decision 12 and the brackets themselves rule out. Using it would mean
changing what decision 34's panel skins mean, which work order 132 says
to park rather than do.

## 4. Consequences of the one assignment

**Select Race ← `frame_plain.png`**

- `boxes.json`: **nothing changes.** Select Race has no cutout boxes —
  it is on the shared 9-slice, which has no holes — so
  `tools/frame_holes.py --write` is not run and decision 3 does not
  apply. There is no "cutouts agree with frame" assertion for this
  screen to make or break; what replaces it is a containment check.
- No F5-placed box ends up outside the opening, at either resolution.
  That is the measurement, not an expectation.
- **One thing IS lost and has to be rebuilt:** the 9-slice draws the
  screen title (`FRAME_TITLE`, "Select Race" / "Select Race Picture")
  in `frame.title_rect`. A fixed image has no title bar, so the title
  would silently disappear. `frame_plain.png` has a title plate at
  (643, 6, 633, 73), measured from its own alpha, and the title is drawn
  there.
- `FRAME_BTN_LEFT` and `FRAME_BTN_RIGHT` are already `None` on this
  screen, so no frame button is lost.

**"At least as well" — the one axis where the 9-slice could have won,
measured.** A 9-slice composes from tiles and could in principle stay
sharper than a fixed raster at 2160p. It does not here: the shared
frame's own `9slice.json` declares `source_size` **1672x941**, smaller
than the 1920x1080 asset replacing it. At 3840x2160 the 9-slice is
scaled by 2.30 and the new image by 2.00, so the new frame is the
sharper of the two at every supported resolution, not merely the more
uniform one. That is why this is an assignment and not a taste call —
and it is also why the "these are soft at 2160p" worry, which is real,
is a worry about BOTH and not a reason to keep the old one.

## 5. Provenance

The committed frames live at `screens/<name>/assets/frame.png`, are
authored artwork, are committed (decision 42: derived artwork ships;
unmodified original artwork does not — these are neither, they are ours),
and are loaded through the resource roots (decision 16). The new asset
follows exactly that: `screens/select_race/assets/frame.png`.

The SOURCES and `key_frames.py` are not build inputs — nothing in the
tree regenerates a frame from them — so they are not tools and they are
not generated files (decision 40's licence, a byte-for-byte rebuild,
does not exist here and is not claimed). They stay outside the tree in
`~/orionlayer-fixtures/incoming/frames_18sep/`, which is the precedent
`~/orionlayer-fixtures/gimp/frame_1920_retouched_2026-09-10.png` already
set for a frame source: the retouched master lives in the fixtures and
only the finished asset is committed. They are named here so the trail
from render to committed asset is written down rather than remembered.
