Work order 125 — the GAME menu inside the map opening (16 Sep 2026)

Data's decision: the game-menu frame must sit INSIDE the galaxy map's own opening, clear of the GAME field above and the nav bar below, instead of overlapping both as it does today. Measure, then build in one run — Data does not want a reporting stop.

This replaces the anchor decision 122/Run 1b made from loadsave.cpp (the four dialogs fixed at 0x90, 0x19, that share transferred to HD). Defensible because the original has no frame at all: its anchor was written for a frameless popup. It is still a deliberate deviation and gets the full marking — module docstring, amendment to decision 69, status document, and a smoke check that fails if the frame reaches outside the map cutout.

Measure first, and put the numbers in the report

For 1080p, 1440p and 2160p, with the frame fitted to the map cutout (height = the cutout's height, aspect preserved, centred on the cutout; decide whether a small inset looks better and say why):

the frame's rect and how much smaller it is than today;
the resulting opening, and the scale factor the menu content now takes;
the font size of the menu buttons, SETTINGS/RETURN, and the slider labels at that factor — measured by rendering (Style.render_text), not by the nominal point size;
the confirmation and warning after BOTH factors (they already carry 0.900 / 0.843): their rect, and whether the question gains a line;
the sliders: block count and block width in device pixels — the original's ten blocks must stay countable, and the HD preview must still land on the same value as before the change.
Then build
Frame fitted to the map cutout at every resolution, nothing outside it. The map cutout comes from boxes.json as the regenerator wrote it, never a literal.
Menu content scaled by one factor, as in 123 — geometry is the original's, smaller.
If something does not survive the shrink — the confirmation gains a line, a label becomes unreadable at 1080p, the slider blocks fall below a legible width — do NOT silently compensate with a hand-tuned exception. Build it, and report the number with a one-line recommendation. Data decides afterwards.
The press feedback from 124 and the help regions must still land on the moved rects; the smoke check for both is expected to catch a miss, so say whether it did.
Also in this run

Frame bottom edge (124/F): with the new anchor the overlap into the nav bar disappears by construction. Confirm it, and drop or retarget the measurement note from 124 accordingly.

Acceptance

Screenshots at all three resolutions beside the native image, for the menu, settings (with sliders), load, save, confirmation and warning. Smoke green, count before and after. Decision 69 amended. Report the measurement table even where the build went through — the numbers are what Data reviews.

Same protocol as before: Data's own OrionLayer closed before a live run, one picture per injected click, SAVE1–9 hashed.
