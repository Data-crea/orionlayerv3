# Work Order 152 — Fleets: function and parity pass

First line for references: "Work Order 152 — Fleets: function and parity pass"

Before anything else: check the next free work-order number in the tree,
put it in the title above, and rename this file to match.

## Purpose

The new Fleets frame is in (Work Order 151, first line "Work Order 151 —
New Fleets frame"). Data played the screen side by side with the
original and found eight problems. Some are bugs, some are missing
parity with the original, two are cosmetic.

Everything below that comes from Data's screenshots is an observation
to verify, not a finding. Establish the cause from source and live data
before designing a fix.

## The eight items

**1. Scrap does nothing in HD.** Data's screenshot shows the original
window with the confirmation "Scrapping this ship will yield 131 bcs,
Okay?" and YES/NO open, while the HD screen shows no dialog. Does the
click reach the game, and the HD screen simply not see the dialog? What
does HD need to show it and answer it (decision 33 and the popup
pattern of decision 11)?

**2. Ships and panel text disappear.** In the same screenshot the HD grid
is empty and the text box blank while the game still shows four
Katanas. Data also reports ships vanishing when he selects them. Is this
the same cause as item 1 (the dialog changing the field list or the
screen state), or a separate one? Establish which before fixing either.

**3. Star names on hover in the map.** Data says the original shows a
star's name when the mouse is over it on the Fleets map. Confirm from
source what the original does there. The Extension API has no mouse
motion (established in 151 B), so if the names come, they come from
data HD already holds — say whether it does.

**4. Grey line above the ship icons.** Each occupied cell shows a thin
grey line along the top edge of the blue square behind the ship. Find
where it comes from (the ship artwork, its extraction, or the
renderer) and remove it at its source.

**5. Selection highlight.** Today the selected state is the blue square
directly behind the ship. Data wants it brighter and on the edge of the
cell box, not behind the ship. Report how the original marks a
selected ship (it looks like a light frame around the whole cell in
the original screenshot — verify) and draw the HD state on the cell
edge, following the new cell frame's shape.

**6. Right-click help.** Implement context help on the Fleets screen
exactly as on the galaxy map: regions transcribed from the original's
help table for this screen into `screens/fleets/help.json`, text from
the user's `HELP.LBX`, same popup (decision 38, first line "Context
help: regions transcribed, text derived, neither in boxes.json").

**7. Ship panel content.** The original shows: ship name; crew level and
experience ("Green Crew (1EP)"); shield class; Beam OCV and Beam DCV
with values; a Weapons column with count, name and firing arc
("5 Anti-Missile Rockets (360)", "(Fx)", "(F)"); a Specials column.
HD shows a location line the original does not, no crew, no OCV/DCV,
no arcs, no specials, one column. Transcribe the original's content and
two-column layout (the column positions were documented in 151 B). For
each value say whether it is on the wire; anything that is not goes
into `doc/orion2re_open_fixes.md` as a request, not a guess. The
"Location" line: keep only if Data decides so — report it as an HD
addition.

**8. Moving ships over the map.** In the original, ships can be sent to
another system from the Fleets screen via the map. Establish from
source exactly how that interaction works (which button, which clicks,
what the map accepts), then implement it. Every click that reaches the
game goes through the game's own frame, never the HD view's
(decision 35, first line "The HD viewport may decouple from the
game's; the click frame may not"), and injected clicks follow
decision 20.

## Running

- **Stop 1:** findings for all eight items, from source and live data.
  Items 4 and 5 are cosmetic and may be implemented in the same run as
  their own commits once their cause is clear. Everything else: report
  and stop.
- **Stop 2:** after Data's decisions, one commit per item.

## Live rules — important for this order

- Scrap and relocation change the game state. Test them **only on a
  scratch save (SAVE4/SAVE5)** and never save the game afterwards.
- Hash SAVE1–9 and SAVE11 before and after; they must be identical.
  SAVE10 is the autosave and is only logged.
- Exactly one client at the server — Data's OrionLayer must be closed.
- Every send checks the freshly read field list; an injected click is
  followed by a framebuffer read before the next one.

## Acceptance

- Each item either fixed with a before/after capture at 1440p beside
  the original, or reported with the reason it cannot be done in HD.
- Smoke test green before every commit. Pushing is Data's decision.

End of work order.
