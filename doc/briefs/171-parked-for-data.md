# Work order 171 — parked for Data

Every choice this unattended run made that is Data's to confirm, with
the default taken.

---

## P1 — Saturation and brightness bars, not presets

**Default:** two bars in one "Frame tone" row. They reach every
neutral and every dark colour — dark violet, pale blue — in one row, and
grey/silver/black are each two clicks. **Alternative:** a row of neutral
swatches (Silver, Grey, Dark grey, Black) like the player-colour row —
one click each, but nothing in between. The named values are in
`core/hud/tint.NAMED` if swatches are wanted.

## P2 — Accent labels follow the frame colour

**Default (the order's):** STARDATE, TREASURY and the other panel
labels, the title word, button words and the table's column heads turn
with the frame (hue and saturation, at their own luminance); values,
white text, sub-values, colony names in rows and red negatives do not.
Renders: `tone_samples_sheet.png`.

## P3 — Black and dark grey look alike at the edges

Both hold their edges at the floors (EDGE_FLOOR 0.15, LIT_FLOOR 0.36),
so the difference between them is the fills (near-black vs black). A
"black" frame therefore has mid-grey edges. **Default:** kept — the
floors are what keep the HUD usable. If Data wants darker edges on
black, the floors are two named numbers; below them the check that
edges stay 3:1 (or as visible as the blue) fails, which is the point.

## P4 — The live part

Not run: Data's engine holds the port and may not be connected to.
