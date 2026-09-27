# Brief — the diplomacy audience in HD (work order 185, parts 9-11)

Written before building, from `doc/audience_reading.md` (the reading, with
every source reference) and the block open fixes 46 and 47 add. **No line
numbers here**: the reading owns every detail; this owns the layout, the
graphics, the input path and the markings.

## What the screen is, and when it may draw

- `screens/audience/`, claiming the synthetic ids open fix 46 reports:
  **57** (the player opened it — the Races screen's AUDIENCE) and **58**
  (an AI asked for it — at turn start, or on a sneak attack in turn
  processing). One screen answers both (`EXTRA_SCREEN_IDS`, as the Ship
  Designer's pickers do).
- It draws ONLY from the "DIPL" block (open fix 47). **Neither fix is
  applied.** Without 46 the audience runs under its caller's id and no HD
  screen can know it is up: the Races screen's HD view hands a dialog it
  cannot name to the game's picture after its wait, and a turn-start
  audience is the modal net's case — exactly today's behaviour. With 46
  and without 47, the screen declines 57 / 58 (`claims`) and the picture
  is shown at once. Nothing is ever drawn from an invented value.
- A list the audience runs that is not a menu — the system picker, which
  has its own loop and its own stars — is a list HD has no view for: the
  screen hands over (`wants_original`) and the gate treats it as a modal
  net. The same for a DIPL whose menu disagrees with the live fields.
- Ways in: the Races screen's AUDIENCE and a race (57); a turn start with
  a diplomacy message, a sneak attack (58). Ways out: Good Bye, a war or
  surrender confirmed, a refusal clicked away — back to the caller.

## Layout — the current HUD style (decision 71), on the original's stage

The audience is a scene: the ambassador in the race's room. The scene is
the original's own art; everything laid over it is HUD.

| area | contents | source |
|---|---|---|
| the stage (whole window, 4:3 centred, pillarboxed on the universal background) | the race's room, the ambassador — not drawn when the audience is refused | DIPLOMAT.LBX: the room `race*2 + 13`, the ambassador `race*2 + 14` (first frame), in the palette of entry `race` — a new extraction, raw blobs decoded at load (decision 38) |
| the reply panel (the original's text box at the top) | the statement, wrapped | DIPL's text, as the engine rendered it (decision 60: drawn as it comes) |
| the menu panel (the original's list at the left) | the title and the items, a disabled item dimmed | DIPL's list — title, words and the flag `Get_List_Field_` honours |
| a statement waiting for a click | the reply panel alone; a click anywhere answers it | the single full-screen field the list shows |

**Original graphics adopted**: the room and the ambassador. **Not adopted,
and why**: the text box and list chrome — decision 71 draws every panel
with the HUD blocks (DEVIATION `hud_frameless`). **Not drawn**: the
talking loop (the ambassador's animation phase is not on the wire — HD
shows the first frame: OMISSION `talking_loop`), the fade-in, the
diplomat cursor, the header line (JIMTEXT2's "leader of the race" line
needs an extraction this order does not add: OMISSION `header_line`).

## Input — decision 20, one field at a time, found in the live list

| control | what HD sends | why |
|---|---|---|
| a menu item | `ACTIVATE_FIELD` on its field: the live list's type-10 fields in y order, the title first — the item's index is its place after the title | the list returns the chosen field (`Get_List_Field_`); measured live in part 9 (Good Bye by activation left the audience) |
| a statement's click | `ACTIVATE_FIELD` on the one full-screen field | the statement waits for any click |
| a disabled item | refused before sending (decision 33) | `Get_List_Field_` ignores it (flag 0) |
| a right click | nothing (OMISSION `audience_help`) | the audience's help ids (the reading) are not built |

Keys: none sent — the list has no hotkeys (type 10, hotkey 0).

## Markers (decision 61), each in the module, the status document and a smoke check

| marker | what |
|---|---|
| DEVIATION `hud_frameless` | panels in the HUD blocks, not the original's text box and list art |
| OMISSION `talking_loop`, `header_line`, `audience_help` | as above |
| UNVERIFIED `fix46`, `fix47` | the data path: built against blocks recorded on a scratch engine; the screen claims nothing without DIPL |

## Texts

Every word on the screen is the engine's — the reply text and the menu as
DIPL carries them, rendered from the player's JIMTEXT / DIPLOMSx files by
the engine itself. OrionLayer's own words: none, except the hand-over
sentence of the safety net, which already exists.

## Checks, offline

The claim rule both ways (DIPL present / absent), the two ids, the menu's
items against the live fields, every input's message and its refusals on
the recorded lists, the recorded DIPL parsed and drawn at 1920, 2576 and
3840 (090t's double-scaling rule), the markings, the art loader with and
without the player's files.
