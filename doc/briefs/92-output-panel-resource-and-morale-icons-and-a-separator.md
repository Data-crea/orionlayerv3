Output panel — resource and morale icons, and a separator between rows

Brief 92. Screen: colony_summary, box planet_output, module colonyoutput.py, wording and deviations in layout.json under output. Read the module docstring and output._deviation_note first; this brief does not repeat them.

What Data wants

The mockup (Data's, 13 September 2026, ~/Downloads/mockup.png — copy it to doc/briefs/92-mockup.png so the brief and the picture travel together) puts an icon at the left of each of the five rows — FOOD, INDUSTRY, RESEARCH, BC, MORALE — and a thin horizontal line between rows. Two things and only two:

Icons. Four resource icons from one sheet (symbols.png: coin, corn, pickaxe, test tube — that is BC, FOOD, INDUSTRY, RESEARCH, in sheet order) and two morale masks (normal_moral.png, low_moral.png). Data places the three source files at screens/colony_summary/assets/_src/output/ before this run starts; if they are not there, stop and say so.
Separators. A line between consecutive rows, as drawn in the mockup. Nothing under the last row, nothing above the first.

The bars beside the numbers in the mockup are NOT part of this brief. Do not draw them, do not prepare for them.

Run 1 — source questions, reporting stop, no code

Answer each from the function that BUILDS the thing, with file and line, in the status document:

Morale states in the original. Draw_Colony_Scan_Info_ draws morale from native y 421 as sprites (the deviation note says so). Which routine, how many distinct sprites, and what value range selects each? Data has two masks. State whether two states cover what the original distinguishes, or whether the original draws N sprites for +N / −N (in which case say what the two masks would stand for, and leave the choice to Data).
Resource icons in the original. Draw_Colony_Prod_Both_ draws the rows as sprite groups. Is there a single per-resource glyph the original uses anywhere on this screen or the colony screen (a header icon, a legend), or only the counting sprites? This decides the marking: an icon beside a label is either a transcription of an existing glyph or the continuation of the label+number deviation this panel already carries. Say which.
Separators. Confirm the original draws no line between the rows in that box. If so, the separator is an HD EXTENSION and is marked as one — in colonyoutput.py, in layout.json under output, and in a smoke check that fails if it silently disappears (the marked-inventions rule in the fundament).
Icon dimensions. Which table will hold them. core/zoomtables is for orion2re transcriptions; if these sizes are ours, name the table in layout.json or core/ where they live WITH A SOURCE BESIDE THEM ("An asset is not a measurement": the size does not come from the PNG). Propose the table entry; Data confirms.
Next free decision number, checked at this stop and again at Run 2's end.
Run 2 — after Data's decisions

Asset preparation — a tool, tools/make_output_icons.py, modelled on make_sidebar_icons.py:

Splits symbols.png into four masters; loads the two masks.
Keys the black background to alpha WITHOUT leaving a dark fringe (the sources are anti-aliased against black; a straight black→transparent leaves a halo, and BLEND_RGB_ADD would show the rest — pygame facts, section 4). Trim to content.
The two masks come on canvases of different size and aspect (1254x1254 and 1374x1130). Normalise both to ONE footprint so that a state change does not move or resize the icon on screen; the tool refuses to write if the two outputs disagree in size, the same shape of guard as make_black_hole_master.py.
Output to screens/colony_summary/assets/output/, at the sizes from the table decided in Run 1, one file per icon per step if the panel has steps, otherwise one. The tool's docstring states the sources are AI-generated (Data's, ChatGPT) and carry the licence note the other assets carry.
Report the resampling filter used. The sources are upscaled pixel art with soft edges; whichever filter you pick, put the result at 1080p and 1440p beside a native screenshot of the original's box and let Data look.

Rendering in colonyoutput.py:

Icon position and size come from layout.json under output, not from constants in the module. The five rows get their icon by row id; morale picks the mask by the state rule decided in Run 1, in colonyrows (the seam: colonyoutput is handed the answer, it does not read the record).
Separators: y from the row geometry the module already has, x extent, colour and thickness from layout.json / palette. No double scaling — anything that must be right at an untuned resolution reads the stored scale directly (the help-popup lesson).
An empty selection still draws nothing — no icons, no lines.

Marking and checks:

Deviation note in layout.json updated: what the icons are and why, what the separators are and why, and what it would take to undo each.
Smoke test: icon files exist at every declared size; the two morale masks agree in size; separators are declared for every resolution that declares the panel (assert the rule, not the instance).
tools/smoke_test.py green, headless.
Acceptance

Two screenshots per resolution (1080p, 1440p) with Draconis I and one high-morale colony selected, beside the native box. Data judges against the mockup and the original — phrase anything you notice as a question to verify, not a finding. Push is Data's.
