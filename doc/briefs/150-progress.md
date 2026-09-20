# 150 — Wireframes of every screen at 1440p (progress)

**Work Order 150 — Wireframes of every screen at 1440p.**

Everything is under `~/orionlayer-fixtures/evidence/work_order_150/`.
**Nothing is in the repo** and orion2re was read-only — no tracked file
modified, HEAD unchanged.

## What came out

**22 wireframes across 18 screens**, 2560x1440, **no artwork of any
kind** in any image. Per screen: `original_1440.png`, `boxes_1440.md`,
and `hd_1440.png` where the tree has one. `INDEX.md` and `_overview.png`
at the top, the latter being all 22 side by side.

| | |
|---|---|
| screens | 18, all with `original_1440.png` and a table |
| HD wireframes | **4** — main_menu, galaxy_map, fleets, new_game |
| exact field rects drawn | **124** |
| traced dark wells | **186** |
| traced transparent cutouts | **59** |
| calls listed but not drawn | **155** |

## The mapping

640x480 scaled by a uniform factor 3 to 1920x1440, centred
horizontally at x offset 320, side bands left empty. Written in the
corner of every image and at the head of every table, exactly as the
order specified it.

## Exact vs traced, and how each number is sourced

**Solid lines are exact.** They come from `Add_*_Field_` calls in the
screen's own source, by two routes, and the table says which per row:

* `Add_Hidden_Field_(x, y, x_end, y_end, …)` — all four literals.
* `Add_Button_Field_(x, y, help, pic, …)` — literal origin, and the
  extent from the sprite, because that is how the engine computes it:
  `field->x_end = x + Get_Width_(pic) - 1` (`fields.cpp`). The `pic`
  variable is followed back to the `Far_Reload_Next_(<LBX>, <entry>)`
  that filled it and the size read off that entry's extracted PNG.

**Dashed lines are interpretation** and every row carries the rule and
a `fill` figure saying how rectangular the region actually was.

## Two findings

**1. The original's backgrounds carry transparent cutouts.** This was
not in the plan. The Fleets minimap never traced as a dark well —
because it is not one. The backgrounds have transparent holes where
live content is drawn: **Fleets 17.2 % transparent, Officers 26.2 %,
Colony Summary 3.6 %**. That is the same construction as OrionLayer's
own HD frames, and it was found by checking why a panel was missing
rather than by looking for it.

Cutouts are traced separately from wells and drawn with a shorter
dash, because they are a different statement: a hole is where the game
draws, a well is where the art says content goes.

**2. The trace agrees with the tree's own geometry where both exist.**
The Fleets minimap cutout comes out at native (16, 52, 303, 182)
against `fltgeom.REGIONS["inset_map"]` = (15, 52, 305, 182) — within
the antialiased rim. The traced ship panel is (15, 280, 305, 185)
against `fltgeom`'s `_r(13, 280, 319, 465)`. Nothing was fitted to
those numbers; the tracer does not know they exist.

## Method notes worth keeping

The trace threshold **is not one number for every screen**. Each
background has its own palette, and 25 % of the luma suits Fleets and
Colony Summary while finding nothing on Design (whose rules are 1–2 px)
or the galaxy map (a starfield, not wells). So the percentile is swept
over eight values and the one yielding the most panel-shaped regions is
used; **the chosen percentile and the whole sweep are printed in each
screen's table**, so the choice is visible rather than tuned out of
sight.

The shape filter is stated too: at least 20x20 px and at least
half-filling its own bounding box. Below that the trace picks up 1–2 px
rules and speckle that happens to be 4-connected — the Planet Summary's
text rows join into one region spanning the whole screen at fill 0.017.
Dropped regions are counted in the table, not hidden.

## What is not drawn, and why

* **Catchers and hotkey staircases** — listed in the tables, kept out
  of the drawings per the order, and **detected rather than listed by
  hand**: the `(0,0,639,479)` catcher by its rect, and the staircase by
  its shape (three or more consecutive fields of equal size stepping by
  a constant offset, which is the main menu's six C/S/L/M/H/Q fields).
* **155 calls whose coordinates are computed at run time** — loops,
  parameters, tables. Listed per screen with call site and reason, not
  guessed at. Ship Design has the most (32), because its rows are built
  in loops.

## Screens with no `hd_1440.png`

Twelve have no HD screen of that name in the tree. Two exist but were
**not** silently down-levelled:

* **research_select** — `boxes.json` has only a 1920x1080 list. Stated
  on the image and in the table; no fallback.
* **colony_summary** — its `boxes.json` carries **names only**; every
  rect is seated from `layout_reference.json` at load (decision 55), so
  there is no 2560x1440 geometry in the file to draw. Reading it off
  the running screen would be a different source, so it was not done.
