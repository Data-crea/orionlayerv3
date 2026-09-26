# Work order 179 — parked for Data

Every choice and question this unattended run parked, with the default
taken.

---

## 1. Open fix 34's ESC side effect — ask Joes for a reset? (default: no)

Leaving the main menu's Load dialog with ESC keeps `_screen_data` 2
(loadsave.cpp:388-391; CANCEL resets it at :382-383), so with fix 34 the
menu's own field list is followed by a slot message. HD ignores it (it needs
the dialog's fields too), so nothing is wrong on screen. A one-line reset on
the ESC path would be an engine change beyond fix 34; not written as a patch.
Default: leave it, recorded in entry 34.

## 2. Text at 2576x1432 is smaller after part 5 (default: proportional)

The fault fixed in part 5 grew with the square of the window scale at every
size above 1080p, not only at 2160p. At your 2576x1432 the star names and
Select Race's text were 1.78x their 1080p size and are now 1.33x — the
proportional size, a quarter smaller than you have been seeing. The order
asked for 1080p unchanged and 2160p fixed; the same rule gives this. See
`evidence/work_order_179/scaling_2160/compare_*_2576x1432_*.png`. If the old
size at 2576 was right for your eyes, the way to get it back without the
fault is a larger `font_scale` on the boxes (F5) — not the double factor.

## 3. Two more screens with the same double scale (default: not changed)

Custom Race (`box_font_scale` into `Layout.font_size` at screen.py:251, 298,
320, …) and Empire Identity (screen.py:180, 207, 255) have the same shape as
part 5's fault; Custom Race's 2560x1440 boxes also carry a hand value (0.9)
that may have been tuned against it. Not in this order's scope, not changed;
a check like 090m per screen would show it.

## 4. Buttons too narrow for icon AND word (default: the word alone)

Every button of 169's P11 list has a glyph now, but a glyph is drawn only
where it and the whole word fit. With the buttons as they are, these show
the word only (1920x1080 and 2576x1432): colony summary POPULATION,
INDUSTRY, SCIENCE, PRODUCING, RETURN; Planets CLIMATE, MINERALS; Fleets
SUPPORT, COMBAT, PREV, NEXT; GAME menu SAVE GAME, LOAD GAME, NEW GAME, QUIT
GAME, SETTINGS; main menu HALL OF FAME at 2576. To show them: wider boxes
(F5) or a smaller word — your call, it changes the look. The glyphs are in
`evidence/work_order_179/icons/glyph_sheet.png` — the shapes are mine;
`assets/shared/hud/glyphs.json` is the one place to change one, or drop
`hud/icon_<name>.png` into the mod folder.
