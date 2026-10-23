"""The Fleets screen's own text sizes — work order 326 Part B.

Data (WO 326): the screen's words were clearly larger than the other
screens'. Each size here is the `share` this screen passes to the shared
`core.hud.icons.fitted_word` (font px = box height x share, then shrunk
until the word fits the width); the shared default (0.52) and every HUD
role stay as they are, so no other screen moves. A share of the box
height, not a pixel count, so 1920x1080 and 3840x2160 draw the same
proportion (the boxes scale with the window).

HD EXTENSION `fleets_font_sizes`: the original prints these words into
FLEET.LBX art at its own 640x480 size (flt1.cpp:1188-1258); the HD sizes
are chosen against two measured sources each, named per value. Values in
reference px (1920x1080); Aldrich's cap height is 0.706 of the font px
(measured: font 34 -> cap 24, `~/claude/scratch/wo326/research-B.md`).
"""

#: ALL, RELOCATE, SCRAP, SUPPORT, COMBAT (67 ref px boxes) and PREV, NEXT
#: (64): font 27 / 26, cap 19 / 18 (was the shared 0.52: font 34 / 33,
#: cap 24).
#: Sources: (1) Data's mockup (mockup.png, scaled 1.0738 to 1920): caps
#: ALL 21.5, COMBAT 19.3, PREV/NEXT 18.3; (2) the HUD's own measured big
#: button text, `assets/shared/hud/style.json` measured.text.action.cap
#: 0.293 of the box height -> share 0.293 / 0.706 = 0.415.
CONTROL_SHARE = 0.415

#: A ship's name in the band under its cell picture (band = a quarter of
#: the cell, 35 ref px at 1920): font 20, cap 14 (was 0.8: font 28).
#: Sources: (1) the mockup's cell names, "Invincible" cap 14.0 ref;
#: (2) the native-scaled peers' strip text, `core.nativedraw.NATIVE_TEXT`
#: strip 9 x 2.25 = 20 ref px (the Leaders and Races screens).
CELL_NAME_SHARE = 0.58

#: The strip under the map (its content rect, 56 ref px tall): font 20
#: (was 0.62: font 34, cap 24 — the largest text on the screen).
#: Sources: (1) the peers' one-line strips,
#: `core.nativedraw.NATIVE_TEXT` strip 9 x 2.25 = 20 ref px and
#: the Planets screen's `status_line` 22; (2) the mockup draws its long
#: fleet summary at cap ~10 ref, the width of the strip — the same rule
#: `fitted_word` applies (a long line shrinks to fit), so a short line
#: stands at 20 and a long one comes out as the mockup's.
STATUS_SHARE = 0.36
