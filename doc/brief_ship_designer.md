# Brief — the Ship Designer in HD (work order 185, parts 6-8)

Written before building, from `doc/ship_designer_reading.md` (the reading,
with every source reference) and the blocks open fixes 44 and 45 add.
**No line numbers here**: the reading owns every detail; this owns the
layout, the graphics, the input path and the markings.

## What the screen is, and when it may draw

- `screens/ship_design/`, claiming wire id **3** (SCREEN_DESIGN) and, as
  pickers drawn over it, **54** (shield or computer), **55** (weapon) and
  **56** (special system) — the ids open fix 45 reports.
- It draws ONLY from the "DSGN" block (open fix 44) and, for a picker, the
  "DSBX" block (open fix 45). **Both are applied since work order 186**
  (orion2re `70d31b10`, `4af9fefa`). Without DSGN — an older engine — the
  screen DECLINES its id (`ScreenBase.claims`, the colony screen's pattern
  from open fix 35): id 3 is then an id no HD screen claims and the player
  gets the game's own picture through the safety net — exactly today's
  behaviour, no hold, no failure, no flash. Nothing is ever drawn from an
  invented value.
- Under DSGN without DSBX (fix 44 applied, 45 not), a picker reports 3 like
  the page; the screen then sees a field list that is not the page's (no
  Cancel button at its origin) and hands over to the game's picture for as
  long as the picker is up (`wants_original`, the research panel's
  pattern) — the gate holds it, so no native frame is shown by mistake:
  the picture is shown because HD has no view for that picker, which is
  decision 22's case.
- The one way in is the build popup (Design, then a design row; Refit,
  then the custom row), and the way out is Cancel or Build back to it —
  both screens are HD already, so every transition is HD-to-HD through the
  hand-over gate, and the flash check gets their recorded transitions.

## Layout — the current HUD style (decision 71)

One full-window screen on the universal background (mod-overridable),
panels in glass with the transparency setting, the global frame colour,
title plate on top. Boxes in `boxes.json` (1920 reference, F5), wording in
`layout.json`, each position a box so a mod can move it. Arranged as the
original arranges its page, top to bottom, so the eye finds things where a
MOO2 player expects them:

| area | contents | source |
|---|---|---|
| title plate | the screen's name | HD EXTENSION — the original's headline is painted into DESIGN.LBX's background; the word is the game's own help title for this screen |
| ship panel (top left) | the ship picture, left / right arrows, the design name (editable), "Space" and the hull space | picture: SHIPS.LBX (the Fleets screen's extraction and loader); name, space: DSGN |
| hull column | six buttons, Frigate .. Doom Star, the current one lit, the unavailable ones dimmed | names: TECHNAME hull names (`core/shipparts.py`); state: DSGN `size` and the field list (a hull without a button field is not offered) |
| drive / armour panel | name, parsecs per turn, combat speed; name, structure points, armour points | names: TECHNAME; numbers: DSGN |
| shield / computer panel | name, strength, damage points blocked; name, beam attack; beam defence, missile evasion | as above; a click opens the picker |
| weapons table | eight rows: count, name (plural above one, "(ammo)" for racks), damage, arc, space, cost, modifications; minus / plus per row | names, plurals: TECHNAME; damage and modification strings: DSGN as the engine formats them; arc words: KENTEXT (`core/kentext.py`); space and cost: DSGN divided as the original divides |
| specials table | eight rows: name, description | names: TECHNAME; descriptions: TECHDESC |
| bottom line | Cost, Space Available; Clear, Cancel, Build | DSGN; the labels HESTRNGS; the three buttons at the fields the wire reports |

**The pickers** are HUD popups over the page, one layout per kind:
generic (name, cost, space — or for computers name, bonus, cost), weapon
(name "(n)", damage, cost, space, note; the four filters; the arc picture
or the rack list; the modification list; Cancel, Accept), special (name,
space, cost, description). Their rows and numbers come from DSBX, row for
row, never recomputed.

## Original graphics adopted

- **The ship pictures** — SHIPS.LBX, entry `picture + colour * 50`, through
  the Fleets screen's extraction (`tools/fleet_art_extract.py`) and loader
  (`screens/fleets/fltart.py`): the same pictures, not a second copy.
- **The firing-arc pictures** of the weapon picker — DESIGN.LBX's five arc
  images — through a new extraction of that one group, raw blobs decoded at
  load time (decision 38's rule, the Fleets extractor's pattern).
- **Not adopted, and why**: DESIGN.LBX's background, button, box and scroll
  art. Decision 71 replaced every screen's frame and chrome with the HUD
  blocks; the designer follows it. Marked DEVIATION `hud_frameless`, as
  every screen since 169 is.

## Input — decision 20, one field at a time, found in the live list

| control | what HD sends | why |
|---|---|---|
| Cancel, Clear, Build, a row, the shield / computer panel, a picker row, Accept, a filter, an arc, a rack, a modification, the icon arrows, plus / minus | `ACTIVATE_FIELD` on the field found in the list read NOW, by type and rectangle — never a remembered index | the handlers compare field ids |
| a hull button | `INJECT_CLICK` at its field's centre (open fix 3 applied) | a multi-button (field type 3) writes `_design_size` in the mouse path, which an activation skips — the radio button's fact in fundament part 09 |
| the design name | the key path of the continuous string field: **UNVERIFIED** until the live test shows what a client's keys do there | decision 61: an UNVERIFIED behaviour is not built; until measured, the name is shown, not edited |
| a right click on a row | the game's help (HELP.LBX), drawn in the shared help panel | the original opens `Text_Box_` with the item's help |

**Refuse before sending** (decision 33): Build only while the wire offers
its button (the original removes it when the design does not fit); plus
only where the plus field exists; a hull button only where its button
field exists. A "may not upgrade" answer is a warning box under id 3 —
the screen sees the box's list, hands over for it, and the game's picture
answers it (the reading, section 10).

## Markers (decision 61), each in the module, the status document and a smoke check

| marker | what |
|---|---|
| DEVIATION `hud_frameless` | the page and the pickers wear the HUD blocks, not DESIGN.LBX's art; positions follow the original's page |
| HD EXTENSION `title` | the title plate; the word is the game's own |
| DEVIATION `picker_as_popup` | the pickers are HUD popups; the original draws them from DESIGN.LBX's box sprites |
| OMISSION `flashing_hover` | the original flashes the hovered row and the shield / computer name in a cycling palette index; an RGB surface has none — HD fills the row as the research panel does (INVENTION `hover_fill`) |
| UNVERIFIED `name_entry` | typing the name: the text being typed is the engine's `_continuous_string`, on no block (work order 186) |
| ~~UNVERIFIED `fix44`, `fix45`~~ | removed by work order 186: the fixes are applied and the data path was seen live on that engine |

## Texts

Every visible word is extracted from the player's files, none typed:
HESTRNGS (labels, headers, messages — `core/hestrings.py`), TECHNAME
(component, hull and modification names and plurals — `core/shipparts.py`,
extended by the missing tables), TECHDESC (special descriptions, weapon
notes — a new extractor), KENTEXT (arc words), HELP.LBX (right-click help).
The engine-formatted strings in DSGN / DSBX (damage, modifications) are
drawn as they come, decision 60's rule. Words of OrionLayer's own (the
title's source note, the hand-over sentence) are registered in the screen's
text table and replaceable from the mod folder (decision 73).

## Checks, offline

The claim rule both ways (DSGN present / absent), the picker ids, every
input's message and its refusals on a stand-in list, the recorded DSGN /
DSBX parsed and drawn at 1920, 2576, 3840 (090t's double-scaling rule, the
research panel's pixel pattern), the markings, the extraction's loaders
with and without the player's files, the transitions in the flash check's
replay set.
