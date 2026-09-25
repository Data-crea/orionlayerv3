# Work order 170 — progress

Unattended run, 25 September 2026. HUD layout fixes on the galaxy map
(and the same gap on the other screens), and a global HUD colour
setting. Builds on 169 / decision 71.

Evidence root: `~/orionlayer-fixtures/evidence/work_order_170/`.

## Part 0 — filed

170 was free (nothing above 169 in `doc/briefs/`). Filed byte for byte
with its `<n>` placeholders, as 167 and 169 were. Worked in the full
tree, as 169 did (169 P0).

## Part 1A — the cause, measured before anything was changed

Data's window is 2576x1432. `Layout.scale` = min(2576/1920, 1432/1080)
= 1.3259; the 16:9 content area is 2545.9 px wide, so it sits with
**15 px of letterbox on each side** and none above or below.

| what Data saw | cause, in numbers |
|---|---|
| empty band under the bar, ~60 px | the bar's boxes were MEASURED off the HUD artwork (169), and the artwork itself ends early: its lowest visible row is HUD y 3619 of 3756 (ref 1036), and the bar's edge lines sit higher still (nav 1022, TURN 1026 ref). So the bar ended 54 ref px above the bottom — 72 px at 1.3259 — at every 16:9-or-wider window, and more at a taller one (the content area is centred, the rest is letterbox). The HUD's own transparent margin was carried over as if it were layout. |
| dark strip at the left edge | the 15 px letterbox: the galaxy map's floor was drawn only inside `map_area`, which starts at the content area's left edge; outside it the background placeholder showed |
| black above the right panel | the same: `map_area` stopped at the panel's left edge, and the floor with it |
| stars under the GAME plate | 169's choice (169 P7): `map_area` started at y 0 and the title plate hangs over it; the plate is drawn later, so what is under it is hidden and its clicks go to GAME |

Data's suspicion (the bar's position) was right in effect and wrong in
kind: nothing moved the bar, the measurement put it there.

## Part 1B — the fix — **DONE**

| what | how | commit |
|---|---|---|
| bar on the bottom edge | the bar ends the HUD's own screen-edge margin above the bottom — `measured.galaxy.edge_margin`, 20 ref px, the gap between the info panel's opaque right edge and the image's edge, the one place the artwork says how far a block sits from the screen's edge — and hangs from the WINDOW's bottom (`anchor_v: bottom`) | galaxy |
| map in the free space | `map_area` from the title plate's bottom to the bar's top, left of the panel, `MAP_GAP` (6, ours) clear of each; `anchor_v: stretch`, so it follows the window between plate and bar. DEVIATION marked in `screen.py`: not the original's 506:400 — clicks go back through the same `MapView`, so they follow | galaxy |
| no black strips | the floor is drawn over the whole window (`floorlift.render_floor`), stars still clipped to the map box | galaxy |
| title plate | hangs from the window's top edge | galaxy |
| window anchors | `Layout.vertical` / `Box.anchor_v` (top, bottom, stretch) — HD EXTENSION; identical to the old rects at 16:9 and every wider window, different only at a taller one | galaxy |
| the same gap elsewhere | colony: sort row and RETURN on the bottom edge (they sat 70 ref px up, in the old frame's holes). New Game and Empire Identity: frame buttons on the bottom edge. Custom Race: none — its columns reach 22 ref px from the bottom and its buttons are inside them | colony, pre-game |
| checked, not changed | Planets (lowest panel ends 994), Fleets (968), Select Race (850), Leaders and research (native geometry): their bottom rows are CONTENT in panels, not a bar — parked (P2) with the numbers | — |

## Part 2 — the frame colour — **DONE**

- **Where:** the GAME menu's Settings dialog, a sixth OrionLayer row
  ("Frame colour"): a hue bar across the value column and RESET. The
  Settings dialog, not the menu itself, because the menu has no free
  room and the dialog is where the other OrionLayer display settings
  already are (floor lift, player colours, monster values).
- **Form:** continuous hue, 0-359, a click on the bar sets the hue under
  the pointer (parked P3, with the samples).
- **Rule:** `core/hud/tint.py` — a colour in the accent band (170-250°)
  is turned and brought back to its own relative luminance. The same
  function for code-drawn colours and, per pixel, for the title plate and
  the frame glyphs. Constant-HLS rotation was built first and MEASURED:
  hues 25-175° made a table word fall to 3.3:1 on the selected row.
  With luminance kept the worst contrast over 72 hues is 6.20:1, so no
  clamp.
- **Never turned:** all text colours and the background placeholder
  (skipped in `HudStyle.colour`), the five info-panel pictures, the title
  plate's orange lamps; star/player/race colours, sprites and portraits
  are not HUD style values at all.
- **Persistence:** `user_settings.json` key `hud_hue` (the existing
  mechanism, decision 63), None = the measured blue; applied at start by
  `main.App` and at once from the dialog — caches rebuilt, no restart.

## Checks

301 -> **303**, none deleted.
- New: "galaxy map: no star, name, fleet or wormhole pixel under a HUD
  block, and the bar on the bottom edge" (011a) — five window sizes
  (1080p, 1440p, 2160p, Data's 2576x1432, 1920x1200), a worst-case edge
  galaxy always and the reference save's 99 stars when the fixture is on
  the disk (it was, here); the two HUD-colour checks (006b).
- Rewritten because their subject moved (named in each): the colony
  sort-slot namer check -> "two exchanged sort slots keep their own keys";
  "no spare holes" -> "the only unclaimed holes are the old sort row";
  the floor-lift one-point check follows the floor into
  `floorlift.render_floor`; the OrionLayer rows check covers six rows.

## Live — read only, on Data's engine

My own session-launched orion2re hung again after `data space allocated`
(stopped by PID; P1 of 169 unchanged). **Data's engine was running**
(PID 287200, started 19:00, no client attached), so one read-only
snapshot was taken through `core.game_client.fetch_snapshot`: nothing
sent, no save loaded, connections 0 before and after, SAVE1-11 identical
before and after. The game: stardate 3500.0, 54 stars, 28 colonies — not
one of the fixtures (`fixture_name` None). Rendered from it at 2576x1432,
1920x1080 and 3840x2160: **0 pixels of stars, names, fleets or wormholes
under a HUD block**, TURN 27 / 20 / 40 px above the bottom (the 20 ref px
margin). Komi, Bier and Miract — the names Data saw under the plate — are
below it.

## Evidence — for Data to look at

`~/orionlayer-fixtures/evidence/work_order_170/` (offline renders say
`offline`, the live ones `LIVE_snapshot`):
- `galaxy_map_2576x1432_LIVE_snapshot.png` (+ 1080p, 2160p) — your own
  game in your window size.
- `galaxy_map_{1920x1080,2560x1440,3840x2160,2576x1432,1920x1200}_offline.png`.
- every screen at 1080p, `<screen>_1920x1080_offline.png`, and
  `game_menu_settings_1920x1080_offline.png` (the slider row).
- `colour_samples_sheet.png` — galaxy and colony at the measured blue and
  at hues 0, 30, 120, 160, 280 (single files `*_hue<NNN>_offline.png`).

## What Data should look at first

1. `galaxy_map_2576x1432_LIVE_snapshot.png` — the plate, the bar, the
   left edge and the corner above the panel, in your game and window.
2. `colour_samples_sheet.png` — do you want the continuous hue, or a few
   presets? (P3)
3. `colony_summary_1920x1080_offline.png` — the sort row is on the
   bottom now and the band moved ABOVE it (P2).
4. Parked P2: whether Planets, Fleets and Select Race should stretch to
   the bottom too.
