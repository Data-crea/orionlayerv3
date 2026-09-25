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
