# Work order 170 — parked for Data

Every choice this unattended run made that is Data's to confirm, with
the default taken.

---

## P1 — The live part

Session-launched orion2re hung again (169 P1, not this order's). Your own
engine was up, so a READ-ONLY snapshot was used (nothing sent, no save
loaded, saves identical): see the progress file. **Not done live:** a
click through the moved bar and map on a running game. The click path is
unchanged in code (same field ids, `MapView.to_native` on the new box);
a hand test of TURN, one nav button and a star click would close it.

## P2 — The band on screens without a bar

**Done:** the bar-like rows are on the bottom edge — galaxy map, colony
summary (sort row + RETURN), New Game and Empire Identity (frame
buttons). Custom Race had no band (its columns reach 1058).
**Not changed, with the lowest element's bottom at 1080p:** Planets 994
(86 ref px band), Fleets 968 (112), Select Race 850 (230), Leaders and
the research panel (native 640x480 geometry, scaled). Their bottom rows
are panels with content, and closing the band means re-laying out the
screen — Data's layout call. **Default:** left as they are.
**Also:** the colony screen's band moved from under the sort row to
above it (between the lower panels, ending 921, and the row at 1011).

## P3 — The slider's form

**Default:** continuous hue (0-359), click to set, RESET to the measured
blue, in the Game Settings dialog's OrionLayer rows. Samples at 0, 30,
120, 160, 280 in `colour_samples_sheet.png`. Presets instead (or as
well) would be a row of swatches like the player-colour row.

## P4 — The nav glyphs and TURN follow the frame colour

**Default:** they follow (they are frame-coloured glyphs); the five
info-panel pictures never do. One set in `core/hud/tint.FOLLOWS`.

## P5 — Text keeps its colour

Every word keeps its measured colour at every hue — the labels stay
light blue under a red frame. That is what guarantees readability.
**Alternative:** turn the label/title blues with the frame (they are in
the band); readability would then need its own check per hue.

## P6 — Windows taller than 16:9

Title plate and bar hang from the window's edges and the map stretches
between them; the info panel stays in the 16:9 content area, so at
16:10 there is a gap between the panel's bottom and the bar. The floor
fills it. **Default:** kept; stretching the panel would need its rows to
spread.

## P7 — The reference save's star array

Found at offset 24984 of `fixture_reference_3502.4.GAM` (99 records of
234 bytes, the first "Orion"), gated on the file's sha256 in the check.
Not added to `tools/fixtures.py`'s table, because only the check reads
it; if more tools want it, it moves there.
