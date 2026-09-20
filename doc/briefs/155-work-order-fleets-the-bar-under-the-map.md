# Work Order 155 — Fleets: the bar under the map

First line for references: "Work Order 155 — Fleets: the bar under the map"

Before anything else: check the next free work-order number in the tree,
put it in the title above, and rename this file to match.

## Purpose

The strip under the galaxy map is still empty in HD. Two things belong
there:

1. **The long bar shows the name of the star the mouse is over.** Data
   wants hovering a star in the map to name it in that bar.
2. **The small box left and right of it switch**, as in the original.

## What to establish first

Read the source for that strip: what the original draws in the bar,
what the two buttons switch between, and what the bar shows when
nothing is hovered. Transcribe that, then add HD's hover behaviour on
top of it. If the original uses the bar for something else entirely,
say so before overriding it — Data decides whether hover takes
precedence or shares the space.

## Rules that apply

- **Hover sends nothing.** The API has no mouse motion; HD resolves the
  star under the pointer from the snapshot it already holds, as 153 B
  does for the ship panel.
- **Do not name a star the player has not explored.** Use the same
  visited/omniscient/lore helpers the ship panel's destination line
  uses since 154, so HD can under-report and never over-report.
- **The two switch buttons act through the game's own fields**
  (`ACTIVATE_FIELD`), against a freshly read field list; the grid and
  the panel follow whatever the game then reports.
- The bar and both small boxes are boxes in `boxes.json`, F5-editable
  like everything else (decisions 14, 15, 37).

## Running

Unattended, no stops. Questions go to
`doc/briefs/<n>-parked-for-data.md`.

Acceptance: a 1440p capture with a star hovered and its name in the
bar, one with nothing hovered, and one after each switch button,
beside the original in the same states.

## Live rules

Exactly one client — Data's OrionLayer must be closed; if it is
attached, skip the live part and say so. Scratch saves only (SAVE4 /
SAVE5), never save; hashes of SAVE1–9 and SAVE11 identical before and
after; SAVE10 only logged.

## Acceptance

- Hovering a star names it in the bar, with no send to the game.
- Unexplored stars are not named.
- Both switch buttons do what the original's do.
- Smoke test green before every commit. Pushing is Data's decision.

End of work order.
