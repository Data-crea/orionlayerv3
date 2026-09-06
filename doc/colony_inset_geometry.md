# The colony summary's galaxy inset: what it shows, and at what scale

**An investigation, 6 September 2026.** Parts 1 and 2 only —
**Part 3 is not computed yet**, by the brief's own reporting stop.
Every line number was re-anchored against the working tree at
`~/orion2re` on that date.

The question this answers: `colonyinset.py` draws a small galaxy map
beside the colony list, and what it *should* show was never written
down. Everything below is in **world units** and nothing is derived
from an asset's pixel size (decision 26).

---

## 1. The original

### 1.1 One call, and the whole rectangle is in it

`COLSUM::Draw_Galaxy_Map_` (`colsum.cpp:413-415`) is one line:

```c
MOVEBOX::Draw_Galaxy_Map_Box_(nullptr, 0, 0x17c, 0x15d, 0x80, 0x5b,
                              0, 0, 0, 0, 3, 0);
```

Against the signature at `movebox.cpp:4-9` that is

| argument | value | meaning |
|---|---|---|
| `x_base`, `y_base` | 0x17c = **380**, 0x15d = **349** | the box's top-left in 640x480 |
| `width`, `height` | 0x80 = **128**, 0x5b = **91** | the box |
| `map_x_off`, `map_y_off` | 0, 0 | no offset inside the box |
| `x_adj`, `y_adj` | 0, 0 | no adjustment |
| `view_mode` | **3** | the colony-screen star sprite |
| `exit_flag` | 0 | draw |

So the inset is **native (380, 349, 128, 91)** — x 380..507, y 349..439
inclusive — and it is called from `COLSUM::Draw_Colony_Summary_`
(`colsum.cpp:467`).

### 1.2 It shows the WHOLE galaxy. There is no window.

`movebox.cpp:64-65`, the only positioning arithmetic in the function:

```c
int32_t scale_x = 506000 / width;      // movebox.cpp:20
int32_t scale_y = 400000 / height;     // movebox.cpp:21
...
int32_t sx = x_start + map_x_off + ((MOX::_star[i].x * 1000 / MOX::_max_map_scale) * 10) / scale_x;
int32_t sy = y_start + map_y_off + ((MOX::_star[i].y * 1000 / MOX::_max_map_scale) * 10) / scale_y;
```

**No selected star enters this.** There is no centre, no window size,
no clamp — every star is placed by its own world coordinate alone.
The origin is the box's top-left and world (0, 0) maps there.

**Why "the whole galaxy" is not an approximation.** `506000` and
`400000` are `MAP_MAX_X * 1000` and `MAP_MAX_Y * 1000` of the SMALL
galaxy, and the four original sizes hold the ratio
`MAP_MAX / _max_map_scale` constant (`mapgen.cpp:1078-1110`):

| size | `MAP_MAX_X` x `MAP_MAX_Y` | `_max_map_scale` | X / scale | Y / scale |
|---|---|---:|---:|---:|
| small | 506 x 400 (0x1FA, 0x190) | 10 | 50.6 | 40 |
| medium | 759 x 600 (0x2F7, 0x258) | 15 | 50.6 | 40 |
| large | 1012 x 800 (0x3F4, 0x320) | 20 | 50.6 | 40 |
| huge | 1518 x 1200 (0x5EE, 0x4B0) | 30 | 50.6 | 40 |

Dividing by `_max_map_scale` therefore normalises **any** original
galaxy onto the small galaxy's coordinate space, and the box's
coverage is exactly `50.6 * scale` x `40 * scale` world units — the
whole map, edge to edge, at every size. That is the whole trick, and
it is why the function needs no galaxy-size branch.

**The transform, stated once:**

```
inset_x = 380 + ((star.x * 1000 / M) * 10) / (506000 / 128)
inset_y = 349 + ((star.y * 1000 / M) * 10) / (400000 /  91)
M = MOX::_max_map_scale
```

all divisions integer, truncating toward zero. With `506000/128 =
3953` and `400000/91 = 4395` this is **0.070268 px per world unit in
x and 0.063212 in y** at M = 36 — see 1.7 for why those two differ.

### 1.3 It does not re-centre, and there is no edge case

Because 1.2 has no window, selecting a different colony cannot move
the map. The only thing the selection changes is **which star's
sprite is left animating** (1.5). Measured in Part 2 across ten
different selections.

The one thing that *is* clipped is the drawing:
`graphics::Set_Window_(map_x_off + x_start, map_y_off + y_start,
map_x_off + width + x_start, map_y_off + height + y_start)` followed
by `video::Clip_On_` (`movebox.cpp:58-60`, `Clip_Off_` at `:106`).
So a sprite that would cross the box's edge is cut at the edge, not
moved.

### 1.4 What is drawn inside: stars, and nothing else

The star loop (`movebox.cpp:63-105`) is the entire content. After it
the function does `Do_Fleet_Screen_Stuff_` for `SCREEN_FLEET` and
`Do_Officer_Screen_Stuff_` for `SCREEN_OFFICERS` (`movebox.cpp:108-120`)
and returns. **No nebulae, no wormholes, no ship icons, no grid, no
home ping** on the colony summary.

One thing is drawn *over* it by the caller: while a colonist cluster
is held, `COLSUM::Colsum_Connect_Galaxy_Map_Stars_`
(`colsum.cpp:731-744`, called at `colsum.cpp:497`) draws a marching
multi-coloured line from the cluster's colony star to the currently
scanned one, through
`SHIPS::Draw_Directional_Multi_Colored_Line_`. Guarded by
`COLMOVE::_cluster_colony_n != -1 && COLONY::_g_colony_n != -1`
(`colsum.cpp:487`).

And the scanned star's NAME is printed under the box, centred at
native (444, 431), by `COLSUM::Draw_Scan_Info_` (`colsum.cpp:80-88`)
— inside the inset's own y range, not below it.

### 1.5 The star sprite: a dedicated 3x3 dot, not a zoom-table rung

`view_mode == 3` draws `MOX::_colony_galaxy_star_seg[color_idx]` at
`(sx - 1, sy - 1)` (`movebox.cpp:99-104`), so the computed pixel is
the sprite's **centre**.

That array is loaded by `COLONY::Load_Galaxy_Map_Anims_`
(`colony.cpp:329-339`): ten entries from **`gstar.lbx`, entries
23..32**. Measured through `core/lbx.py` on the player's own file:
each is **3 x 3 pixels with 8 frames**, `flags = 0x04`. Entries 20..22
in the same file are 5x5 with 10 frames — a different, larger dot
the other screens use.

So the inset's star is **not** any rung of `core/zoomtables.py`. It
is a dedicated three-pixel animated dot, and the ten of them are one
per colour index, not one per size.

The colour index (`movebox.cpp:70-83`):

| condition | index |
|---|---|
| `spectral_class == STAR_CLASS_BLACK_HOLE` | 9 on the colony palette, else 10 |
| owner outside 0..MAX_PLAYERS, visited or owner -1/-2 | 8 |
| owner outside 0..MAX_PLAYERS, unvisited | 0 |
| otherwise | `MOX::_player[owner].color` |

**The selected star is the animated one.** `movebox.cpp:101-103`:
every star except `MOX::_galaxy_map_scanned_star` has its animation
frame reset to 0 before drawing, so only the scanned star's 8-frame
cycle advances. `_galaxy_map_scanned_star` is set on entry from
`_g_colony_n` (`colsum.cpp:141`), from a row hover
(`colsum.cpp:879-888`) and from a job-column hit (`colsum.cpp:1001`).

### 1.6 Clickable? No — but right-clickable

No field covers the box. The screen's fields (`colsum.cpp:263-309`)
are the four buttons at x 619/531, the seven sort buttons at y 446,
the scroll field at x 621, the per-row hidden fields at x 12..101 and
512..597, the buy buttons at x 599, and last a full-screen catch-all
`Add_Hidden_Field_(0, 0, 639, 479)` (`colsum.cpp:309`). A left click
in the inset reaches only that catch-all.

A **right** click hits the help list. `_colony_summary_screen_help_list`
(`erichelp.cpp:65-88`) contains `{525, 381, 349, 510, 439}` — the
inset's own rectangle — and `fields::Check_Help_List_`
(`fields.cpp:2916`) draws the entry and swallows the click. Help 525
in the player's own HELP.LBX reads:

> **Galaxy Map Window** — *Shows the galaxy map, the currently
> scanned star, the source and destination stars when moving
> colonists.*

which is a second, independent confirmation of 1.2, 1.5 and the
connect line of 1.4: the original's own words say *the galaxy map*,
not a region of it.

### 1.7 Two asymmetries worth writing down

**The inset is anisotropic, by a constant factor.** x is divided by
3953 and y by 4395, so one world unit is `3953/4395 = 0.89943` as
tall as it is wide on screen. That factor is independent of galaxy
size, because both divisors are constants. The original's small
galaxy map is 506 x 400 world (aspect 1.265) drawn into 128 x 91 px
(aspect 1.4066), and 1.265 / 1.4066 is exactly that 0.8994. **The
original does not preserve the galaxy's aspect in this box.**

**The connect line uses a different divisor from the dots.**
`MOVEBOX::Get_Galaxy_Map_Star_XY_` (`movebox.cpp:355-388`) computes
`506000 / map_width + 1` and `400000 / map_height + 1` — **3954 and
4396** where the draw loop uses 3953 and 4395 — and subtracts a
centre offset of 2 (or 3) rather than 1. Measured over this save's
99 stars, the two disagree by at most **1 px** in x (2 stars of 99)
and 1 px in y (1 star of 99). It is the original's own inconsistency,
not a transcription error, and it only affects the endpoints of the
colonist-move line.

### 1.8 One case the original's arithmetic does not cover

orion2re adds a fifth galaxy size that MOO2 does not have:
`GALAXY_SIZE_MAXIMUM`, chosen for more than 71 stars
(`harold.cpp:1034-1053`, guarded by `#if MAX_STARS > ORIGINAL_MAX_STARS`,
`consts.h:8,17`). Its map is built from a grid rather than a table
(`mapgen.cpp:1112-1120`):

```c
raw_cell_size   = (50 * 30) / 10                    // = 150
_MAP_MAX_X      = Maximum_Galaxy_Grid_X_() * 150
_MAP_MAX_Y      = Maximum_Galaxy_Grid_Y_() * 150
_max_map_scale  = Maximum_Galaxy_Display_Scale_()    // mapgen.cpp:64-71
```

and `Maximum_Galaxy_Display_Scale_` takes the LARGER of the two
ceilings `(map_width * 10 + 505) / 506` and
`(map_height * 10 + 399) / 400`, so `MAP_MAX / scale` is no longer
50.6 and 40. **For this size the galaxy no longer fills the box.**

| size | galaxy, world | box covers, world | fill |
|---|---|---|---|
| small | 506 x 400 | 506.0 x 399.9 | 100 % x 100 % |
| medium | 759 x 600 | 759.0 x 599.9 | 100 % x 100 % |
| large | 1012 x 800 | 1012.0 x 799.9 | 100 % x 100 % |
| huge | 1518 x 1200 | 1518.0 x 1199.8 | 100 % x 100 % |
| **maximum (the reference save)** | **1800 x 1350** | **1821.5 x 1439.8** | **98.8 % x 93.8 %** |

The reference save is a maximum galaxy — 99 stars — so **every
measurement in Part 2 is of the under-filled case**, and it is the
case OrionLayer's own reference material is in.

---

## 2. Measurement

**Save**: `SAVE8.GAM` in the player's install, sha256 `ab70cc9a…70bd6`,
byte-identical to `~/orionlayer-fixtures/fixture_reference_3502.4.GAM`
(11 colonies, **99 stars**). Loaded through the game's own Load
dialog on 6 September 2026 and opened on the colony summary. Frames
are the Extension API's `VISUAL` — the game's own 640x480
framebuffer, palette-indexed, so the comparison is on indices.

Star world coordinates come from the same snapshot's star records
(`core/structs/star.py`, x at offset 15, y at 17), not from the
screen.

### 2.1 Solving for the scale

`_max_map_scale` is not on the wire, so it was solved for rather than
assumed: the transform of 1.2 was evaluated for every M from 10 to
120 and scored by how many of the 99 predicted centres land on a
non-background pixel inside the box.

| M | predicted centres landing exactly on ink |
|---:|---:|
| 10 | 0 / 99 |
| 15 | 1 / 99 |
| 20 | 8 / 99 |
| 34 | 13 / 99 |
| 35 | 21 / 99 |
| **36** | **99 / 99** |
| 37 | 18 / 99 |
| 38 | 11 / 99 |
| 30 | 4 / 99 |

**M = 36, and it is the only value that fits.** It also agrees with
1.8 computed forward: 99 stars needs
`Maximum_Galaxy_Grid_Y_() = 9` (the first y with
`((y*5+3)/4)*y >= 99`, i.e. 12 x 9 = 108), so `MAP_MAX` is
1800 x 1350, and `Maximum_Galaxy_Display_Scale_` gives
`max((18000+505)/506, (13500+399)/400) = max(36, 34) = 36`. Two
independent routes to the same number.

The whole 128 x 91 box is background index 0 in 10 416 of its 11 648
pixels, and carries 1 232 ink pixels — close to 99 x 9 = 891 plus the
scanned star's name text, which `Draw_Scan_Info_` puts inside the box
(1.4).

### 2.2 Ten selections, and the map never moves

The scanned colony was changed by clicking each of the ten list rows
in turn (each click enters that colony's screen; ESC returns, and
`colsum.cpp:141` re-establishes the scanned star from `_g_colony_n`).
The scanned star of each frame was identified by differencing
consecutive frames — only the previous and the new scanned star's
neighbourhood changes — which chains from the known entry default.

| row slot | scanned star identified | world (x, y) | predicted centres on ink |
|---:|---|---|---:|
| 0 | Blucher (entry default, `_list_col[0]`) | 734, 496 | **99 / 99** |
| 1 | Draconis | 387, 109 — near the **top** edge | **99 / 99** |
| 2 | (click did not take) | — | **99 / 99** |
| 3 | Irra | 631, 124 | **99 / 99** |
| 4 | **Ktynga** | **72, 621 — near the LEFT edge** | **99 / 99** |
| 5 | Sadak | 427, 344 | **99 / 99** |
| 6 | Blucher | 734, 496 | **99 / 99** |
| 7 | **Waghi** | **103, 483 — near the left edge** | **99 / 99** |
| 8 | Blucher | 734, 496 | **99 / 99** |
| 9 | (click did not take) | — | **99 / 99** |

**Predicted against measured: 99 of 99 stars, in all ten frames, land
on their predicted pixel exactly.** Not "within a pixel" — the
predicted `(inset_x, inset_y)` is a non-background pixel every time,
for every star, at every selection.

The two colonies the brief asks for, far apart and one at an edge,
are **Ktynga (72, 621)** and **Irra (631, 124)** — 4 % of the map
width from the left edge and 9 % of its height from the top. Neither
moves the map by a pixel.

Two further frames captured with two genuinely different selections
(Blucher and Wolf) differ in **1 478 pixels over the whole screen**
and in **183 inside the inset** — and every one of those 183 is
either the star-name text or within two pixels of Blucher's or Wolf's
own dot. No other star moved or changed.

### 2.3 What the measurement confirms, line by line

| claim | source | measured |
|---|---|---|
| box at (380, 349, 128, 91) | `colsum.cpp:414` | 99 stars fall inside it, none outside |
| `506000 / width`, `400000 / height` | `movebox.cpp:20-21` | 99/99 exact, and only at M = 36 |
| origin is the box corner, world (0,0) | `movebox.cpp:64-65` | 99/99 exact |
| no window, no re-centring | absence in `movebox.cpp:63-105` | 10 selections, identical to the pixel |
| `_max_map_scale` normalises the size | `mapgen.cpp:1078-1120` | M = 36 derived forward and solved backward |
| the scanned star is the animated one | `movebox.cpp:101-103` | only the old and new scanned dots change |
| stars only | `movebox.cpp:63-120` | ink = 99 dots + the name text, nothing else |

**Nothing in Part 1 was misread.** Parts 1 and 2 agree.

---

## 3. Ours — NOT COMPUTED

Deliberately empty. The brief's reporting stop puts Part 3 after
Parts 1 and 2 are confirmed, and Part 3 is arithmetic on those
inputs: the crop in world units, the world→HD scale per resolution,
whether that scale is a rung of `core/zoomtables.py` or between rungs
(and therefore an **HD EXTENSION** to be marked like `hd_zoom_level`),
and the star sprite size at that scale.

Two things Part 1 already settles about it, recorded here so they are
not re-derived:

- **The crop is the whole galaxy**, `MAP_MAX_X` x `MAP_MAX_Y` world
  units — except on orion2re's maximum size, where the box covers
  `128 * (506000/128) * M / 10000` x `91 * (400000/91) * M / 10000`
  and the galaxy is smaller than that (1.8). Which of the two an HD
  inset should reproduce is a question, not a fact.
- **The original's star is a 3x3 dot from `gstar.lbx` 23..32, not a
  zoom-table rung** (1.5), so "which rung" may have no answer and the
  choice may be between a dot and an HD sprite — also a question.
