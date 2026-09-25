Work order <n> — Darker frame colours, and the title plate centred on the map

Number: next free work-order number from the tree; rename before filing under doc/briefs/.

Mode

Unattended single run, no reporting stops. Choices go to doc/briefs/<n>-parked-for-data.md with the default taken, progress to doc/briefs/<n>-progress.md. Builds on 169 and 170 (decision 71).

Start

Clone per CLAUDE.md. Read the fundament index, all principles- parts, part 04 with decision 71, and the progress and parked files of 169 and 170.

Data's verdict on 170

The hue slider is accepted — Data likes the result (he tested a violet). Two things change now.

1. Frame colour: also grey, silver and black

Today the setting only turns the hue, so every choice is a saturated colour. Data wants darker and neutral settings too: grey, silver, and black for those who like it.

Add what the hue alone cannot reach — e.g. a saturation and a brightness control next to the hue, or neutral presets; your choice, park it with the reason. Keep it simple enough for a settings row.
The same recolour rule as 170 for code-drawn and cut pieces, so they never disagree. The never-recolour list from 170 holds unchanged.
Black and dark grey must stay usable. A black frame on a dark background still needs visible edges and a visible active/hover state — define a minimum edge brightness (or a light edge on dark fills) and name it. Measure contrast of every text on HUD blocks over the whole range of the new controls, as 170 did for the hue; clamp only where it fails and say where.
P5 from 170 becomes pressing: blue labels under a grey or black frame. Default now: accent-coloured labels (STARDATE, TREASURY, column heads and similar) follow the frame colour, values and white text stay as they are — within the contrast rule above. Park it with renders.
Stored through the same settings file, applied immediately, reset returns to the measured blue — as in 170. Old hud_hue-only settings files keep working.
2. Title plate centred on the galaxy map

The GAME plate is centred on the window, not on the map. Since 170 the map area ends at the right panel, so the plate sits visibly off-centre over the map. Centre it on the map area's horizontal extent at every window size, including non-16:9 windows like Data's 2576x1432. The overlap check from 170 must still pass. If other screens have a title plate over a content area that is not window-centred, apply the same rule and list them.

Tests
Full suite green, fresh clone green. Checks for: neutral settings reachable (grey, silver, black), minimum edge brightness, contrast over the full control range, plate centre equals map-area centre.
Renders under ~/orionlayer-fixtures/evidence/work_order_<n>/: galaxy and colony in measured blue, silver, mid grey, dark grey, black, and one saturated colour; galaxy at 1920x1080 and 2576x1432 for the plate. Listed as things for Data to look at.
Live test only if orion2re starts cleanly; the start hang is not part of this order — if it recurs, park it and run offline. Do not connect to an engine Data started.
Done when

Both parts built, checks in, progress file ends with what was built, what was parked, and what Data should look at first. Commits local. No push.
