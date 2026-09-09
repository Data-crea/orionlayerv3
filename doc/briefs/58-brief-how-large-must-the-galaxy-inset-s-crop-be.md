Brief: how large must the galaxy inset's crop be

Investigation with one deliverable, doc/colony_inset_geometry.md. No screen code changes until the numbers are on paper and confirmed. Read doc/v3_fundament.md first — the rules that apply are "measure in world units" (nebula lesson, decision 26), "two independent sources", and decision 35 (the HD view may decouple, the click frame may not).

The question

The colony management screen shows a small galaxy map beside the colony list. colonyinset.py draws it today; what it should show is not written down. Answer: what region of the galaxy, in world units, does the original's inset display, at what scale, and what does that make the crop for our HD inset box?

Part 1 — read the original

Find the function in colsum.cpp (or wherever it lives — cite it) that draws the galaxy inset on the colony summary screen. State, each with file:line:

The inset's rectangle in 640x480.
What it draws: the whole galaxy scaled to fit, or a window around the selected colony's star? If a window: its size in world units, and whether it is fixed or depends on galaxy size.
The world→inset transform: origin, scale factor, and where the scale comes from (_max_map_scale, a constant, a division by MAP_MAX_X?). Quote the arithmetic.
What is drawn inside: stars only, or nebulae, wormholes, ship icons, the selected star's marker? Which sprite size for stars — which rung of the zoom table, or a dedicated dot?
Does the inset re-centre when a different colony is selected, and what happens at the galaxy edge (clamp, or let the window run past the edge)?
Is it clickable in the original — does a click in the inset do anything (Check_Help_List_, a field, nothing)?
Part 2 — measure it

Run orion2re with the reference save (99 stars). Capture the native frame of the colony summary screen for at least two colonies far apart (one near the galaxy edge). For each, measure the inset positions of three identifiable stars and solve for the transform. It must agree with Part 1 to the pixel; if not, say which line was misread.

Part 3 — compute ours

Given the HD inset box from screens/colony_summary/boxes.json at each supported resolution, state:

the crop in world units (width x height) that reproduces the original's coverage,
the resulting world→HD scale per resolution,
whether that scale sits on a rung of core/zoomtables.py or between rungs — if between, it is an HD EXTENSION like hd_zoom_level and must be marked as one,
what the star sprite size is at that scale (from the table, or a dot as the original does — say which).

Everything in world units. Nothing derived from an asset's pixel size.

Reporting stop

Parts 1 and 2 first, then stop. Part 3 is arithmetic on agreed inputs; if Parts 1 and 2 disagree, Part 3 is not computed.

Acceptance
The document, every number with source or measurement.
Measurement table: predicted vs measured, two colonies minimum.
No other files changed. No push.