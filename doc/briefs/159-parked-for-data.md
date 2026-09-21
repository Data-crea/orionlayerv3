# Work order 159 — parked for Data

Unattended run, 21 September 2026. Nothing here blocked a later part.

---

## 1. The paragraph's COLOUR is not transcribed (part 1)

The layout is a transcription and **the ink is not**, and that is
marked rather than glossed.

`Print_Scanned_Ship_Data_` sets font style 3 from
`MISC::Get_Mox_Font_Colors_(3, 111, 116, …)` with
`_mox_font_colors_offset = 0x72` (flt2.cpp:566-571). That builds a
ramp over **MOO2 palette indices 111..116** — indices, not RGB. The
palette lives in the player's own installation, and turning those
indices into colours needs that file plus a native screenshot of this
panel to check the result against. Work order 159 was forbidden a live
run, so HD draws the paragraph in the panel's existing label colour.

It is `fleets.panel_paragraph` in `colors.json` with the reason beside
it, marked `deviation_panel_paragraph_colour` in `layout.json`, and
**it is a one-value change when the two sources exist** — nothing is
built around the wrong colour.

**Auf Deutsch:** Der Absatz sitzt und bricht wie im Original, aber
seine Farbe ist geraten. Das Original nimmt Palettenindizes 111..116
aus der Spieldatei; die kann diese Sitzung nicht lesen, also steht dort
die vorhandene Label-Farbe, und das ist an drei Stellen als
Abweichung vermerkt statt als Transkription ausgegeben.

---

## 2. Damaged specials — the counts could not be had (part 3)

**Nothing in the tree changed.** Full write-up in
`v3_projektstatus.md` under item 2 and in
`~/orionlayer-fixtures/evidence/work_order_159/part3/`.

**Settled:** the serialised ship record **is** the packed struct.
`Read_Ship_` and `Read_Ship_Design_` read the declaration order with
no padding, so a record is 129 bytes and
`special_device_damage_flags[5]` sits at **@118** — the offset this
project already had.

**Not settled:** where the records start. A save is a serial stream,
so the ship array has no fixed file offset, and 159's scanner could
not locate it reliably. It was cross-checked against work order 154's
own officer count over the same ten saves — 4 of 185 — and reproduced
neither number in either of two attempts.

**So no counts are reported.** The loosened run "found" damaged ships
whose names are single characters and whose fitted-device flags are
all zero: damage on a ship with no devices. Reporting that as "7
damaged ships across 10 saves" would have been worse than 154's check
that proved nothing — a number that is not measuring what it names.

**What would settle it, cheapest first:**

1. **One save where you know a ship has special damage, and which
   one.** That turns the locator from a guess into something
   checkable, and it is the only cheap answer.
2. A reader that walks `Read_Game_State_` as far as the ship array
   (settings, colonies, planets, stars, leaders, players). That is a
   new tool of real size — a decision, not cleanup, which is why 159
   parked rather than started it.
3. A live reading, which this order forbade.

**Auf Deutsch:** Die Felder stehen im Save, und zwar an der bekannten
Stelle innerhalb eines Schiffsatzes — aber wo die Schiffe in der Datei
anfangen, ist nicht fest, und mein Sucher hat es nicht zuverlässig
gefunden. Er widerspricht einer Zahl, die Auftrag 154 über dieselben
zehn Saves aufgeschrieben hat, also melde ich keine Zahlen. Am
billigsten wäre ein Spielstand, bei dem du weißt, welches Schiff
Schaden an einem Special hat.

---

## 3. Still parked, unchanged

- **T3 variant B** (should the two `lift` functions be merged) —
  `doc/briefs/157-parked-for-data.md`.
- **156's D–G**, the four extractions — `doc/briefs/156-parked-for-data.md`.
- **D17 is closed** by this order's part 2 (`8c68edc`).
