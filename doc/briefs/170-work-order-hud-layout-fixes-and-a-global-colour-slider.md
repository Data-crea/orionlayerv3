Work order <n> — HUD layout fixes and a global colour slider

Number: next free work-order number from the tree; rename before filing under doc/briefs/.

Mode

Unattended single run, no reporting stops. Choices go to doc/briefs/<n>-parked-for-data.md with the default taken, progress to doc/briefs/<n>-progress.md. Builds on 169 (decision 71).

Start

Clone per CLAUDE.md. Read the fundament index, all principles- parts, part 04 with decision 71, and doc/briefs/169-progress.md and 169-parked-for-data.md.

Data's verdict on 169

The galaxy screen in the new style is accepted as it stands. Two things change now.

1. Galaxy screen: map area and bottom bar

Data's live screenshot (2576x1432 window) shows:

The title plate covers stars. Star names at the top of the map (Komi, Bier, Miract in his game) sit under the GAME plate. The plate is on top, so they cannot be read or clicked.
The bottom bar is not at the bottom. There is an empty band below the nav buttons and TURN, about 60 px in that window.
Also visible: a dark strip at the left edge, and the area above the right panel is plain black where the rest of the screen shows the map floor.

Find the cause, do not guess it — Data suspects the bar position, it may also be the map rectangle or the fit of the HUD layout to the window. Then:

The bottom bar sits at the bottom edge (keep a margin only if the style values call for one, and name it).
The map area lies fully inside the free space: below the title plate, above the bar, left of the right panel. No star, star name, fleet or wormhole may be covered by a HUD block at any resolution. Where the map rectangle now differs from the original's, the click mapping follows it, and it is marked DEVIATION.
No black strips or dead corners where the map floor or background should show.
The bar and panel are shared blocks — check every other screen for the same gap and fix it there too.

A check that fails when any star or label of a real save's map overlaps a HUD block, at 1080p, 1440p and 2160p and at a non-16:9 window like Data's.

2. Global colour slider for the frame colour

In the GAME menu (or the settings dialog it opens, if that fits better — say which), a slider sets the colour of the UI frame for all screens at once. HD EXTENSION, marked as such.

What it recolours: the HUD's accent colour — panel edges, glow, separator lines, button edges and underlines, the title plate, hover/active states, the scrollbar, the TURN button. Cut raster pieces (title plate) are recoloured the same way as code-drawn ones, so they never disagree.
What it never recolours: anything that carries game meaning or is artwork — star colours, player/race colours, star-name colours, red negative values, original MOO2 sprites and portraits, the icons with their own colours (coins, food, station, freighter, microscope). Whether the blue nav icons follow the slider is a choice; park it.
Default is the measured blue from 169's style.json; a reset returns to it.
The setting persists across restarts through the tree's existing settings mechanism (find it; do not add a second one) and applies immediately, without restarting — caches built per colour are invalidated.
Slider form (continuous hue, or hue plus a few presets) is your choice; park it with a render of 5–6 sample colours on the galaxy and colony screens.
Text stays readable at every slider position; if some hues fail, clamp the range and say where.
Tests
Full suite green, fresh clone green. New checks for the overlap rule above and for the colour setting (default equals measured value, persistence, never-recolour list untouched).
Renders under ~/orionlayer-fixtures/evidence/work_order_<n>/: galaxy at 1080p, 1440p, 2160p and at 2576x1432; every screen once at 1080p after the bar fix; the colour samples. Listed as things for Data to look at.
Live test per CLAUDE.md only if orion2re starts cleanly; the start hang from 169 is not part of this order — if it recurs, park it and run offline.
Done when

Both parts built, checks in, progress file ends with what was built, what was parked, and what Data should look at first. Commits local. No push.
