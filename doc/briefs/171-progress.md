# Work order 171 — progress

Unattended run, 25 September 2026. Neutral and dark HUD frame colours;
the galaxy title plate centred on the map. Builds on 169/170 (decision 71).

Evidence root: `~/orionlayer-fixtures/evidence/work_order_171/`.

## Part 0 — filed

171 was free. Filed byte for byte with its `<n>` placeholders.

## Part 2 — the title plate centred on the map — **DONE**

`screens/galaxy_map/hudview.plate_centre_x`: the map box's horizontal
centre in window px (anchors included). The plate, its word, its click
area and its help region all read it. At 1080p the plate moved 155 ref
px left (window centre 960, map centre 805); at Data's 2576x1432 by the
same share. **Other screens:** the only other title plates are the
pre-game ones (New Game, Select Race, Custom Race, Empire Identity),
whose content is window-centred — left as they are.
Check: the plate's centre equals the map box's within 1 px at five
window sizes; 170's overlap check still passes at all five.

## Part 1 — grey, silver, black — **DONE**

- **Controls (parked P1):** a "Frame tone" row under the hue row — a
  SATURATION bar (0-1: grey to the chosen colour) and a BRIGHTNESS bar
  (0.1-1.6: black to silver). Two bars reach every neutral and every dark
  colour, not just four presets, in one row. RESET on the hue row resets
  all three.
- **One rule** (`tint.transform_array`) for code and cut pieces: hue
  turned, saturation multiplied, then scaled to a target luminance —
  a word keeps its own; an edge takes √B while darkening, B above 1; a
  fill takes B below 1 and never brightens.
- **Named floors while darkening:** `EDGE_FLOOR` 0.15 — MEASURED as the
  smallest floor at which every edge stays at 3:1 on every fill, or as
  visible as in the measured blue, over the whole range (0.11 failed at
  29 settings, 0.13 at 4); `LIT_FLOOR` 0.36 — hover/active/TURN at least
  2:1 over a normal edge. The measured blue itself has one edge under
  3:1 (the dim edge on the panel fill, 3.06-3.2 depending on the fill;
  the separator on the selected row 3.1), so the promise is "3:1 or as
  visible as the blue".
- **Contrast:** every word on every fill over 288 settings (24 hues x 3
  saturations x 4 brightnesses): worst 6.20:1. Nothing clamped.
- **Labels follow** (170 P5, parked P2 with renders): `text.title`,
  `text.label`, `text.button`, the table's column heads — hue and
  saturation, at their own luminance.
- **Stored** as `hud_hue`, `hud_sat`, `hud_bright`; a 170 file with
  `hud_hue` alone reads the same colour; applied at once.
- Three measured facts that changed the design on the way: constant
  factors took contrast from edges (→ √B for edges), brightening fills
  took it from silver's edges (→ fills never brighten), 0.11 was too
  low a floor (→ 0.15).

## Checks

303 -> **305**, none deleted: the plate centre (011a), and "grey, silver,
dark grey, black reachable from the controls; over 48 tone settings
every edge at 3:1 or as visible as the measured blue, the lit edge 2:1"
(006b). Extended: the contrast sweep covers the whole control range;
persistence of all three keys and of a 170-only file; the words that
follow keep their luminance; the OrionLayer rows check covers seven rows.

## Live — PARKED

Data's own orion2re (PID 287200, started 19:00) is running and holds
port 17362; the order forbids connecting to it, and an engine of this
run could not take the port. Everything offline.

## Evidence — for Data to look at

`~/orionlayer-fixtures/evidence/work_order_171/`:
- `tone_samples_sheet.png` — galaxy and colony in measured blue,
  silver, grey, dark grey, black and violet (single files
  `<screen>_1920x1080_<name>_offline.png`).
- `galaxy_map_1920x1080_offline.png`, `galaxy_map_2576x1432_offline.png`
  — the plate over the map's centre.
- `game_menu_settings_1920x1080_offline.png` — the two rows.

## What Data should look at first

1. `tone_samples_sheet.png` — are silver, grey and black what you meant,
   and should black be darker at the edges (P3)?
2. `galaxy_map_2576x1432_offline.png` — the plate over the map.
3. P2: labels turning grey with the frame — keep?
