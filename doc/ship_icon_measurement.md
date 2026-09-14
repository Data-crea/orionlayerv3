# Ship icon footprint — how the numbers in zoomtables were obtained

`core/zoomtables.py` carries `SHIP_ICON_DIM` and
`MONSTER_ICON_DIM_ZOOM0`. Unlike `STAR_FIELDS_DIM`, which is a
straight transcription of `MOX::_star_fields_dim`, these are
**derived**. This file is the evidence, so the next person does not
have to redo it — or worse, treat the numbers as transcribed.

## Why there is nothing to transcribe

Ship icon sizes are not a table in the orion2re source. They live in
`BUFFER0.LBX` and are read back at runtime:

```cpp
// ships.cpp:328
void Get_Ship_Icon_Dimensions_(int16_t zoom_level, uint8_t* w, uint8_t* h) {
    anim = buffer::Buffer_Reload_("BUFFER0.LBX", zoom_level + 0xCD, ...);
    *w = animate::Get_Width_(anim);
    *h = animate::Get_Height_(anim);
}
```

The results land in `MOX::_ship_icon_width[4]` / `_ship_icon_height[4]`
(mox.h:625). Reading them out would mean either an LBX extractor or
two more int16 arrays in the Extension API. Neither is worth it for
eight numbers.

## Three sources, one answer

**1. Overlap thresholds.** `MAINSCR::Do_Fleet_Popup_` (mainscr.cpp:1797)
decides whether the click hit a stack of icons:

```cpp
SHIPS::Overlapped_Ship_Icon_Button_(&ship_icon_id, 13 - zoom_level, 9 - zoom_level)
```

The two arguments are compared against `|dx|` and `|dy|` between icon
top-left corners, so they are the icon's own extent — and the width
shrinks by exactly one pixel per zoom step.

**2. Stack spacing.** `SHIPS::Get_XYs_For_Orbiting_Ships_` (ships.cpp:289)
places orbit slots 2, 3 and 4 in a column:

```cpp
int16_t diff_11_minus_zoom = 11 - zoom_level;
out_arr_y[0] = y_ref + diff_11_minus_zoom;
out_arr_y[1] = y_ref + 2 * diff_11_minus_zoom;
out_arr_y[2] = y_ref + 3 * diff_11_minus_zoom;
```

A stack that does not overlap requires icon height < 11 - zoom.

**3. Measurement.** A native galaxy map screenshot, small galaxy, one
fleet in orbit. The capture was at 1.5x (960x720 window), identifiable
from the run-length pattern of duplicated rows and columns (2,1,2,1);
reduced back to 1:1 by keeping one row/column per run.

| Type | Owner value | Native px at zoom 0 |
|---|---|---|
| player ship | 0..7 | 11 x 10 |
| guardian | 9 | 12 x 11 |
| crystal | 11 | 13 x 13 |
| dragon | 12 | 13 x 10 |
| hydra | 14 | 11 x 12 |
| eel (`worm.png`) | 13 | 9 x 9 |

`worm.png` was an assumption when this table was first written — red,
serpent shaped, and the only remaining unmatched red monster.
**Confirmed as the eel in the live game on 29 August** via
`tools/ship_icon_check.py`.

Note that the height stays one pixel below the stack step
`11 - zoom`, which is what keeps four fleets at one star from
touching. Sources 2 and 3 therefore agree rather than merely coexist.

### The guardian was wrong for a day, and how

The first version of this table had the guardian at **17 x 16** — half
again the size of everything else, and visibly wrong on screen before
anyone questioned the number.

The cause: the sprites sit on a star field, and the measurement took
the largest connected blob above a low brightness threshold. At that
threshold a faint pixel bridged the guardian into two background stars
two pixels away, and the bounding box swallowed them. A threshold
sweep shows it immediately:

```
guardian   t25 = 17x16   t40 = 16x14   t60 = 11x11   t80 = 11x11
ship       t25 = 11x10   t40 = 11x10   t60 = 10x10   t80 =  9x10
```

Every other sprite is stable across the sweep; only the guardian moves
by 45 %. Reading the pixel map settles it — the creature spans columns
5..16 and rows 7..17, and the specks at columns 1..3 are stars.

**Two rules came out of this.** A measurement that is not stable under
its own threshold is not a measurement. And a size that is an outlier
against its siblings has to be justified before it is used: the smoke
test now asserts that no monster exceeds 1.4x the player ship on
either axis, which would have caught it in seconds.

## Still missing

- **Zoom levels 1, 2 and 3 have not been measured.** All screenshots so
  far are from one zoom level. The per-step shrink is an extrapolation
  from source 1. A capture of the same system after pressing `-` three
  times in a Huge galaxy would settle it.
- **Antaran (8)** has no reference and borrows the player footprint,
  marked UNVERIFIED. Neither it nor the Amoeba has HD artwork; both draw
  as the grey player-ship stand-in on the map (a marked DEVIATION,
  fundament 64). The **Amoeba (10)** is measured now — see below.

## The sprites disagree with the screenshot table — 14 September 2026

The Amoeba had no screenshot, so it was measured off its own sprite:
BUFFER0.LBX entry `241 + (owner - 9) * 4 + zoom`
(`SHIPS::Get_Ship_Icon_Pict_Seg_`, ships.cpp:383-397 — the monster
entries run FORWARDS by zoom, the player entries backwards), all eight
frames decoded through the main screen's palette as the game sent it,
bounding box of the pixels above a brightness threshold:

```
             t0      t25     t40     t60     t80     table (screenshot)
guardian  e241 13x11   13x11   13x11   13x11   13x11   12 x 11
amoeba    e245 13x14   13x13   13x13   13x13   11x12   (copy of eel, 9 x 9)
crystal   e249 15x12   15x12   15x12   15x12   15x12   13 x 13
dragon    e253 13x15   13x15   13x13   13x13   12x13   13 x 10
eel       e257 15x5    15x5    15x5    14x5    14x3     9 x  9
hydra     e261 13x13   13x13   13x12   13x12   13x12   11 x 12
player    e208 12x8    -       12x8    -       11x8    11 x 10
```

**The entries ARE what the game draws.** At zoom 3, on the `natives`
fixture, every live monster icon in the framebuffer matched its own
entry pixel for pixel (Amoeba 29/29 twice, Eel 17/17, Hydra 24/24,
Guardian 24/24) and none of the other types' entries.

So the Amoeba went in at **13 x 13**, stable from t25 to t60. But the
same method does not reproduce the five screenshot numbers above — the
eel most plainly, 15 x 5 against 9 x 9 — and the player ship neither.
Either the 1.5x screenshot was reduced wrongly, or it was not zoom 0,
or "the central blob" measured something narrower than the sprite.
**Not repaired**: the five values size every monster on the map, and
changing them is outside the brief that found this. Reported to Data
as an open question, with the numbers.
- **A second player colour.** The original indexes a separate LBX entry
  per colour, so a palette swap is likely but unproven. If any colour
  turns out to be a different drawing, runtime tinting is the wrong
  model and eight sprites are needed.

## How to redo it properly

The Extension API already ships a pixel-exact 640x480 framebuffer
(`VISUAL_FRAME`), which removes the 1.5x reconstruction step entirely.
Dumping one frame per zoom level from `tools/ext_diag.py` and measuring
the sprites there would promote this whole table from derived to
measured.
