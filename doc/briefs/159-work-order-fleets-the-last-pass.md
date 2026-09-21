# Work Order 159 — Fleets, the last pass: non-combat ship panel, one HStrings, damaged specials if a save allows

First line for references: "Work Order 159 — Fleets, the last pass: non-combat ship panel, one HStrings, damaged specials if a save allows"

Filed as 159: the highest number in `doc/briefs/` was 158 when this was
filed. Read `doc/v3_fundament.md` first, then the Fleets entries under
"What is missing" in `v3_projektstatus.md` and D17 in
`doc/briefs/157-parked-for-data.md`.

## How this run works

Unattended, no reporting stops. Questions for Data go into
`doc/briefs/159-parked-for-data.md`, progress into
`doc/briefs/159-progress.md`, evidence under
`~/orionlayer-fixtures/evidence/work_order_159/`. When in doubt whether
something is still this order or already a new design choice: **park it
and carry on with the next part.**

Commits go through the fast tier; the push goes through the full suite
(decision 31 as refined by 158).

## Why

The Fleets screen is functionally complete. The release goal is every
screen in HD by 22 November, so this order closes Fleets with the items
that need neither C++ nor new ground truth, and then **Fleets is
declared done**. Everything else on the Fleets list stays under "What is
missing", explicitly marked *after release* (Part 4).

## Global constraints

- Do not touch orion2re, research change mode (131), or any screen other
  than Fleets — **except the three other HStrings sites in Part 2**.
- **No live game run in this order.** No client on port 17362, nothing
  written to `~/Master of Orion 2`. Saves may be read as files (Part 3),
  as 154 did for the officer count.
- Every change of behaviour on screen is exactly the one named in its
  part; nothing else moves. Prove the rest unchanged by preview captures
  at four resolutions, byte-identical where the part does not touch the
  drawing.
- Markers move with their code, in module, status document and suite.

## Part 1 — The non-combat ship panel (item 4)

**The original.** `Print_Scanned_Ship_Data_` returns early for
`ship_type` 1, 2 and 4 (flt2.cpp:548-575): HELP.LBX record `0x29` for a
colony ship, `0xBD` for a transport, `0x6D` for an outpost, font style 3
in its own colour, printed with
`ERIC::Print_Paragraph_Centered_Vertically_(0x12, 0x11A, 0x12B, 0xB7)`.
No crew, shield, destination, weapon or special lines at all. HD today
draws the full data panel for these three types — **more than the
original, which is the fault.**

Build it as a second panel mode keyed on `ship_type`. **Read the drawing
function before writing anything**, and transcribe what it does, not
what it looks like:

- **Which types.** Exactly 1, 2 and 4, taken from the source, not from a
  field dump. **If the ship-type constants in HD's specs do not agree
  with the source's numbering, that is a finding**: stop this part, park
  it, carry on with Part 2.
- **Text.** Through the same `helptext` loader the right-click help
  uses — no new extractor, no new file. The decoding is
  `core/helpformat.py`'s (decision 38), so control codes render as the
  help popup renders them.
- **Layout.** Vertically centred in the panel's text hole, as the
  original's name says, wrapped at the hole's width. The original's
  rectangle is 305 px native [CORRECTED: 299 — see 159-progress.md];
  HD's hole is not, so the wrap width is the
  hole's, and **that is a scaled transcription, not a deviation.** Font
  and colour from the original (style 3, its own colour) through the
  screen's existing `colors.json` / layout words — nothing hardcoded in
  the renderer (decision 15).
- **Too long for the hole.** Use the panel's existing overflow behaviour
  (`"+{n} more"`, `fltpanel._log_overflow`) — do not invent a second
  one. If the three texts all fit at every resolution, **say so with the
  measured line counts** and do not build anything for the case.
- **A clone with no extracted help.** Show the short "not extracted yet"
  wording the help popup already uses, from
  `assets/shared/help/labels.json`. **Do not fall back to the data
  panel**: that is the "more than the original" this part removes. Mark
  this fallback where the help popup's is marked.

The rest of the screen does not change for these ships: grid cell,
selection, strip, PREV/NEXT all behave as before.

**Checks** (rules, not instances — fundament, "Assert the rule"):

- every `ship_type` in the original's early-return set draws the
  paragraph mode and never a data line; every other type draws the data
  panel as before;
- the no-help state draws the labels' wording and nothing else;
- the three texts are driven through a **committed stand-in**, never the
  player's extraction (the derived-loader rule from the clone-only
  fault).

**Acceptance.** Captures of all three types at 2560x1440, and at the
other three resolutions for the longest of the three texts, beside the
source rectangle in the progress file. A combat ship captured before and
after, **byte-identical**.

Remove item 4 from "What is missing" and add the section to "What
works".

## Part 2 — One HStrings (D17)

`HStrings` is built at four sites with three lifetimes:
`galaxy_map/boxdraw` (per screen), `game_menu/screen` (per app),
`planets/planetwords` (fresh on every Planets enter), and
`screens/fleets/screen.py` (per screen).

**Decision (Data): one instance, owned by the app, built on first use.**
The table is read-only game data from the player's installation; it does
not change while the game runs. That is decision 18's trade for palettes
applied to text: a re-extraction needs a restart, and the lookup is free
afterwards.

- One accessor, one place, used by all four sites. Language from the
  app's settings with the tolerant default
  `(getattr(app, "settings", {}) or {})` that `boxdraw` and `game_menu`
  already use.
- `colonybuild` (via Planets) crashes today on a missing `settings`
  where the others default. **That changes, deliberately: it defaults.**
  Record it in the progress file as **the one intended behaviour change
  of this part**, with the path that used to raise.
- **Planets loses its re-read on every enter.** Before removing it, read
  why it was written that way: **if the source or a note gives a reason**
  (a language switch, a reload the player can trigger), **stop this part
  and park it with that reason** — the decision above assumed there is
  none.
- A check: exactly one construction site for `HStrings` in the tree, by
  `ast`, the same shape as the check that already holds `HelpText` to
  one.
- Mark D17 resolved in `157-parked-for-data.md` with the hash.

## Part 3 — Damaged specials in red (item 2), only if a save allows

The check is already written (status document, item 2): damaged bits
must be a subset of fitted bits, **and at least one ship must actually
carry damage** or the run says so instead of passing.

- Read every save on this disk **as a file** — nothing loaded, nothing
  written — and find ships with any bit set in
  `special_device_damage_flags` at `@118`.
- **If at least one ship carries damage and every damaged bit is a
  fitted bit:** that is the second source decision 23 asks for beside
  the header route. Promote the field out of `unverified.py`, draw
  damaged specials with the original's `FLT2::_red_colors`
  (flt2.cpp:724-731) — colour through `colors.json` — and add the check.
  Record which save and which ships.
- **If no ship carries damage, or any damaged bit is not fitted:**
  change nothing. Park it with the counts ("n ships across m saves, none
  damaged") and what save would settle it. **154's lesson applies:** a
  check that holds on 60 undamaged ships proves nothing.

## Part 4 — Fleets is done

- `v3_projektstatus.md`: a session paragraph saying Fleets is complete
  for the release, and what that means.
- The remaining Fleets items under "What is missing" — plural weapon
  names (1), Beam OCV/DCV (3), the strip's move preview (5), arrows for
  PREV/NEXT (6), and item 2 if Part 3 parked it — get **one line each
  marking them after release**, with nothing else changed. Item 5 keeps
  its note that it is one piece of work with the galaxy map's move
  preview.
- Any Fleets entry in older parked files that is now answered: mark it
  resolved with the hash. Anything still open stays where it is.

## Finish

- Fast tier and full suite green; fresh-clone verification with
  `setup.py`, both input states.
- **Push** — Data explicitly asks for it with this file, through the
  pre-push hook.
- Final report **in German**, short:
  - Part 1: done or parked; the three types' captures; how many lines
    the longest text needs at each resolution; the no-help state
  - Part 2: done or parked; the intended behaviour change in one
    sentence; whether Planets' re-read had a reason
  - Part 3: which way, and the counts
  - what the status document now says about Fleets
  - suite count, push confirmation
  - anything parked, with the path
