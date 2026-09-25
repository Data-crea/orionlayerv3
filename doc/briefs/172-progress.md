# Work order 172 — progress

Unattended run, 25 September 2026. The frame colour must never touch
pictures. Builds on 169-171 (decision 71).

Evidence root: `~/orionlayer-fixtures/evidence/work_order_172/`.

## Part 1 — the cause, established before anything was changed

**It was 169, not the tint.** The same New Game state (difficulty Easy,
galaxy Medium, age Average, five players, tech Average; Tactical Combat
and Antarans on) rendered at 2576x1432 — Data's window — from three
trees (`ng_diag.py` in the session scratch, renders in the evidence
folder):

| tree | pictures |
|---|---|
| `ac5ed00` (before 169) | all five present |
| `0c7b832` (169's New Game commit), default blue | all five BLACK |
| HEAD before this order, blue / grey | all five black, at both |

So the loss predates every tint, and the tint did not cause it. **The
mechanism:** a window of that size takes the 2560x1440 box list
(decision 1's closest-by-area fallback), and that list carries an
`inner_panel` box on each picture slot. Until 169 that skin was a
9-slice with a TRANSPARENT centre, framing the picture. 169 made
`draw_inner_panel` a FILLED HUD panel, and New Game draws its boxes
after its pictures — so five opaque panels covered the five pictures,
at every frame colour. At 1920x1080 the box list has no such boxes,
which is why no 169-171 render showed it (they also had no New Game
state, so the slots were empty anyway — a render without data proved
nothing).

**The other 169 screens, checked:** only `screens/new_game/boxes.json`
has `inner_panel` boxes; the boxes that default to the filled `panel`
skin (galaxy sidebar icons, Planets' windows, Empire Identity's busy
panel) belong to screens that never draw their box list through that
path. Select Race's portraits, Empire Identity's banners and preview,
the colony surface picture and Main Menu's art were present in 169's own
renders. No other loss.

**The title plate's smear** had its own cause, in 170/171's rule: pixels
were selected by an accent hue band and a saturation threshold, so the
glossy centre's near-cyan and unsaturated pixels stayed blue while their
neighbours went grey; and the edge floors, applied per pixel, lifted the
brighter half of the painted glow and let the darker half fall.

**The checkboxes** drew their state as the small button's lit fill
alone — too faint to read in blue and invisible on a dark tone.

## Part 2 — the fix — **DONE**

- **Pictures:** New Game draws its box list FIRST and its pictures
  last, each inside its HUD panel; `setting_picture` is the one function
  for the drawing and the check.
- **By component, never by colour:** `core/hud/tint.py` no longer
  selects by hue at all. It turns what a HUD component hands it, whole:
  the style values of `core/hud`'s blocks, the accent words, and the cut
  pieces that are frame (plate, nav glyphs, TURN). Nothing else passes
  through it, whatever its hue. The one named exemption inside a
  component is the plate's two lamps (`lamp_mask`, grown into their pale
  core).
- **The plate (parked P1):** painted pieces are scaled by one smooth
  curve with no edge floors (`rotate_pixels(..., floors=False)`), so the
  glow stays a gradient; lines stay visible because edges darken only
  with the square root. Renders: `title_plate_tones_after.png`.
- **Checkboxes:** a new block, `core.hud.blocks.checkbox`: the small
  button's square and a tick in the lit edge colour (follows the frame
  colour; at the floors on dark tones). New Game's three toggles and the
  GAME menu's thirteen settings squares use it. **Other toggles,
  checked:** Custom Race draws its own tick and radio dot over its
  images (unchanged, fine); Planets' restrictions and Fleets' filters
  show state as the small button's active EDGE, which the floors keep at
  2:1 over a normal edge even on black (171's check).
- `core/hud/tables.py` split out of `blocks.py` for the line guideline.

## Checks

305 -> **307**, none deleted.
- **"hud never touches pictures"** (006c, push-only tier, ~35 s,
  declared in `SLOW_TIER`): New Game's five pictures equal their source
  pixel for pixel at six tints (blue, silver, grey, dark grey, black,
  violet) and at both box lists — 60 comparisons; and on all 13 screens,
  the GAME menu and its Settings dialog, a tint changes only pixels
  inside a region a HUD component drew (every block records its rect).
- **"checkboxes draw both states at every tint"** (006c, commit tier).
- 170's "every accent lies in the hue band" is replaced by its successor
  ("the rule selects nothing by hue; a red pixel of a component turns").

## Evidence — for Data to look at

`~/orionlayer-fixtures/evidence/work_order_172/`:
- `before_new_game_at_ac5ed00.png`, `before_new_game_at_0c7b832.png`,
  `before_new_game_HEAD_{blue,grey,silver,black}.png` — the cause.
- `after_new_game_{blue,silver,grey,dark_grey,black}.png` — pictures
  back, ticks visible.
- `title_plate_tones_after.png` — the plate in every tone.

## Live — PARKED

Data's engine (PID 287200) still holds port 17362; not connected to, and
no engine of this run could take the port.

## What Data should look at first

1. `after_new_game_grey.png` against your screenshot.
2. `title_plate_tones_after.png` — clean enough in grey and black?
3. The tick (P2).
