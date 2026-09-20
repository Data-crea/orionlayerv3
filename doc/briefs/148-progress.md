# 148 — Extract the original GUI art, per screen (progress)

**Work Order 148 — Extract the original GUI art, per screen.**

Everything is under `~/orionlayer-fixtures/evidence/work_order_148/`.
**Nothing extracted is in the repo**, and orion2re was read-only —
`git status` there shows no tracked file modified and HEAD is unchanged
at `e6199966`.

## What came out

**19 139 PNGs across 18 screen folders plus `_shared/`, 159 MB.**
One folder per screen, `manifest.md` in each, `_composite.png` in each,
`INDEX.md` at the top.

| folder | files | not extracted | palette id |
|---|---|---|---|
| `antaran_room/` | 56 | 0 | 0 |
| `colony/` | 638 | 5 | 1 |
| `colony_summary/` | 42 | 0 | 1 |
| `council/` | 1259 | 0 | 0 |
| `fleets/` | 293 | 0 | 8 |
| `galaxy_map/` | 3668 | 0 | 0 |
| `info_library/` | 256 | 0 | 0 |
| `load_save/` | 73 | 0 | 0 |
| `main_menu/` | 142 | 0 | 5 |
| `new_game/` | 47 | 4 | 9 |
| `officers/` | 498 | 2 | 8 |
| `planet_summary/` | 144 | 0 | 6 |
| `race_diplomacy/` | 1277 | 0 | 0 |
| `research_select/` | 80 | 0 | 0 |
| `score/` | 17 | 0 | 12 |
| `ship_design/` | 145 | 0 | 4 |
| `tactical_combat/` | 10027 | 32 | 3 |
| `turn_summary/` | 7 | 0 | 0 |

### `_shared/` — drawn by more than one screen

Stored once, referenced from each screen's manifest by path, not copied.

| archive | files | drawn by |
|---|---|---|
| CONFIRM.LBX | 5 | GENDRAW::Confirmation_Box_ |
| WARNING.LBX | 7 | GENDRAW::Warning_Box_ |
| TEXTBOX.LBX | 6 | TEXTBOX::Do_Text_Box_ |
| GSTAR.LBX | 262 | MOVEBOX::Draw_Galaxy_Map_Box_ |
| RACEICON.LBX | 171 | various |

## How the files were made

`extract_gui_art.py` and `write_manifests.py` live **in the evidence
folder, not in `tools/`**, as the order requires. They decode through
the repo's own `core/lbx` — nothing here re-implements a format.

**Transparency is colour index 0**, established from source rather than
assumed: `draw.cpp`'s `Draw_Bitmap_Sprite_` writes a pixel only
`if (pixel != 0)`, and `Color_Stream_Copy_` in the same file carries the
comment "skipping color 0 (transparency)". Index 0 becomes alpha 0.

**Palette, per entry, as the engine resolves it:** the screen's own
palette as the base — `fonts::Load_Palette_(id, 0, 255)` reads FONTS.LBX
entry `id + 1` — and an entry's own embedded palette laid over it where
it has one, which is what `animate::Draw_Palette_` does. Screens that
install no palette are marked `inherits` in their manifest with the id
actually used.

**The shared dialog art is the one case with no single right answer.**
At run time `animate::Remap_Draw_` recolours it to whatever palette the
host screen has, by nearest-colour search (`remap::Find_Closest_Color_`).
It is rendered once in its own authored palette, because every other
rendering would be a choice of host screen. Said so in `INDEX.md`.

Native size, no scaling, no cropping, no cleanup, one PNG per frame,
`<LBX>_<entry>_<frame>.png`. **No frames were cut out of backgrounds.**

## One finding the composites produced

**A button's normal state is already painted into the background, pixel
for pixel.** The Fleets composite — the background plus FLEET.LBX 2..12
placed at the field origins `flt1.cpp` gives them — is byte-identical to
the background alone: **0 of 307 200 pixels differ.** The control is
FLEET.LBX 13, the dimmed ALL button, pasted at the same coordinates:
**2 009 pixels differ.** So the paste works, and the normal sprites are
exact copies of what is underneath.

That extends work order 147's finding. Frames and panels are painted
into the background, and so are the buttons at rest; the separate
entries exist only for the states that differ — hover, pressed (frame 1
of the same entry) and the dimmed duplicates at FLEET.LBX 13..16.
`fields::Draw_Visible_Fields_` redraws every button every frame
regardless, which is why both copies must exist and agree.

For Data's purpose this is the useful part: **the backgrounds in these
folders already contain every button face, in its normal state, at its
final position.**

## What could not be extracted

* **Entries that are not animation records.** COLONY.LBX 0–4 and a
  handful elsewhere fail the 12-byte animation header; they are data,
  not pictures. Listed as NOT EXTRACTED in their manifest with the
  reason. 43 across the whole run.
* **Anything drawn by code rather than loaded** — the Fleets scroll-bar
  thumb gradient is the clearest case, `FLT1::Fill_FltScrn_Scroll_Bar_`
  plotting `line::Line_` from palette 0xA6 downward. Listed per the
  order, not reconstructed.
* **The live comparison.** Data's OrionLayer (pid 327353) was attached
  to the server for the whole run, so by the live-test protocol nothing
  of mine connected. The order allows this explicitly. No save was
  opened, nothing was written, SAVE8 untouched.

## Composites

`_composite.png` places sprites only where the source names both the
entry and its field origin — that is the Fleets screen today. Elsewhere
the composite is the background alone, which given the finding above is
what the original draws before anything dynamic. Extending it to the
other screens is a per-screen read of each `Add_*_Field_` call; it is
mechanical but it is not free, and it is not what this order was for.
