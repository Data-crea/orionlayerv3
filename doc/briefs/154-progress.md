# Work Order 154 — progress

Formatting only, as the order says: no new values and nothing new off
the wire. One commit. Decisions taken without asking are in
`154-parked-for-data.md`.

---

## The transcription

`FLT2::Print_Scanned_Ship_Data_`, flt2.cpp:524-747, read line by line
**and then checked against a native screenshot of the same panel** —
`evidence/work_order_152/panel/001_20_panel_native.png`, the ship
"Rafale", captured live in work order 152. Two independent sources,
which is what this tree asks for before a number is trusted, and they
agree on every one of them.

### The line grid

The drawing window is `Set_Window_(15, 282, 320, 465)` (flt1.cpp:402),
so x is measured from 15 over a width of 305, and y from 287.

| slot | content | x | notes |
|---|---|---|---|
| 1 | ship name | 0x12 | font style 3, larger |
| 2 | `<crew word> (n EP)` | 0x12 | style 2 |
| 3 | shield name | 0x12 | always present; `_shields[0]` is "No Shield" |
| 4 | H 0x99 "Beam OCV:" | 0x12 | value RIGHT-aligned ending at 0x85 |
| 4 | H 0x9A "Beam DCV:" | 0xAD | value at 0x73 + 0xAD = 288, same line |
| 5 | the destination, **or nothing** | 0x12 | shifted colour, normal + 3 per channel |
| 6 | H 0x9D "Weapons:" | 0x12 | style 2 |
| 6 | H 0x9E "Specials:" | 0xAD | same line |
| 7+ | weapon entries | 0x17 | style 1, step FH + 1 |
| 7+ | special entries | 0xBC | style 1, own cursor from the same `base_y` |

**THE HEAD IS FIVE SLOTS AND THE CURSOR ADVANCES THROUGH ALL FIVE.**
The destination block is an `if` that prints or does not print, and
the `y_cursor += FH + 2` after it runs either way (flt2.cpp:643-660).
So a slot the original leaves empty is a BLANK LINE and everything
below keeps its place.

**That blank IS the "empty line between the head block and the
Weapons/Specials block" the order describes** — it is the destination
slot, and it is empty because the ship in the comparison is parked.
There is no separate blank: a ship in transit fills it and the two
blocks are then adjacent.

### The four points in the order

1. **Beam OCV / DCV** — see `154-parked-for-data.md` §1. The answer is
   "absent always, and not because of the layout": the numbers need
   the leader records. **The labels are now drawn at their own stops**
   so the line keeps its place and the gap is visible; the numbers are
   not invented.
2. **Separation** — built, as the five-slot head. Not a hard-coded
   blank: the slot is blank when the original's own condition says
   nothing goes in it.
3. **Indentation** — built. Weapons 0x12 -> 0x17 under their heading,
   specials 0xAD -> 0xBC under theirs. **The two indents differ** (5
   native px and 15) and both are transcribed rather than averaged.
4. **Tab stops** — six of them, as fractions of the panel width, in
   `screens/fleets/fltpanel.py`:

| stop | native x | fraction of 305 | what sits there |
|---|---|---|---|
| `COL_LABEL` | 0x12 = 18 | 0.00984 | every head line, "Weapons:" |
| `COL_ENTRY` | 0x17 = 23 | 0.02623 | weapon entries |
| `COL_OCV_VALUE_END` | 0x85 = 133 | 0.38689 | OCV value, right-aligned |
| `COL_RIGHT_LABEL` | 0xAD = 173 | 0.51803 | "Beam DCV:", "Specials:" |
| `COL_RIGHT_ENTRY` | 0xBC = 188 | 0.56721 | special entries |
| `COL_DCV_VALUE` | 0x73+0xAD = 288 | 0.89508 | DCV value |

`SPECIALS_SPLIT`, which 151 B put in the tree, is `COL_RIGHT_ENTRY`
and is now defined as it rather than as a second copy of 173/305.

The two value stops are transcribed and not yet drawn to. They are
held by a smoke check so they cannot rot before the numbers arrive.

## Two faults found on the way, both fixed

**1. HD printed a destination for a ship that was not going
anywhere.** The original's condition is

    loc >= SHIP_LOCATION_MOVING_OFFSET
        && loc <= _NUM_STARS + SHIP_LOCATION_WORMHOLE_OFFSET

(flt2.cpp:644; the offsets are 10000 and 20000, consts.h:22-24), and a
parked ship's `location` is the bare star index. Work order 152 item 7
established that the line is the original's — correctly — and did not
carry its condition across, so HD printed "Destination, Vega" for a
ship sitting at Vega. H 0x9B is literally "Destination, %s". The slot
is now blank for a parked ship, which is also what makes the empty
line in point 2 appear in the right place.

**2. HD named a star the player had not explored.** The original picks
H 0x9C "Destination, Unexplored star" unless
`Player_Has_Visited_ || TRAIT_OMNISCIENCE ||
One_Leader_With_Galactic_Lore_ || Contact_With_One_Colony_`
(flt2.cpp:657-662). HD printed the name regardless. It now reads the
first two — `star.visited` is a bitmask over players and the racial
pick is in `player.traits`, both already decoded, through the helpers
`colonyrows` and the galaxy map already use — and has neither the
leader skills nor the diplomatic contact. **So it can under-report and
cannot over-report.** Marked `deviation_panel_destination_info`;
showing a name the player should not see was the unsafe half and it
is gone.

The third wording, H 0x68 "Destination: Antares" for
`_NUM_STARS == star_idx`, is built too.

## What is marked

Four new entries in `layout.json`, each citing the lines it describes,
each held by the new smoke check:

* `omission_panel_beam_bonuses` — the line is drawn, the numbers are
  not, and why.
* `deviation_panel_one_font` — the original uses three font styles
  (name, head, entries), 2 px of leading in the head against 1 in the
  columns, and puts two of its lines 2 px below the pitch. HD has one
  font at one size and draws one pitch. Every POSITION is transcribed;
  the faces are not.
* `deviation_panel_destination_info` — above.
* `omission_panel_support_ship_help` — a colony, transport or outpost
  ship gets a centred HELP.LBX paragraph in the original and the data
  panel in HD (`154-parked-for-data.md` §2).

And one existing mark corrected: `deviation_panel_overflow` still said
the original "uses TWO COLUMNS ... where HD stacks both in one", which
stopped being true at work order 152 item 7.

**The known omissions stay, as the order says:** the weapon plural
(visible in the comparison — the original says "3 Nuclear Bombs" and
HD "3 Nuclear Bomb") and the red for a damaged special.

One difference deliberately NOT changed: with no firing-arc bits set
the original prints `%d %s ()` with empty brackets and HD prints no
brackets at all. HD cannot tell "no arc bits" from "no KENTEXT.LBX
extracted", and printing empty brackets after every weapon in a fresh
clone is the worse of the two. No real weapon has an arc of 0.

## Acceptance

`~/orionlayer-fixtures/evidence/work_order_154/acceptance_154_1440p.png`
— the original's own panel (the native 640x480 capture at x3) beside
HD's at 2560x1440, **the same ship**, built from a fixture that
reproduces Rafale exactly: Green Crew (15 EP), No Shield, four Nuclear
Missiles and three Nuclear Bombs at 360 degrees, no specials, parked.

Checked against each other:

| | original | HD |
|---|---|---|
| line order | name, crew, shield, OCV/DCV, blank, headings, entries | the same |
| the blank line | one, the empty destination slot | the same |
| weapons indented under "Weapons:" | yes | yes |
| specials indented under "Specials:" | yes, further | yes, the same fraction |
| right column starts at | 0xAD heading / 0xBC entries | the same fractions |
| the two bonus numbers | +25 / +45 | missing, labels drawn, marked |
| plural weapon name | "3 Nuclear Bombs" | "3 Nuclear Bomb", marked already |
| name in a larger font | yes | no, marked |

Smoke 238 -> 239.

## Live

**No live run, and none is called for.** This order moves text inside
one box; it reads no new field and sends nothing. The comparison is
against a native capture already in the fixtures, taken live in work
order 152 with its save hashes recorded beside it. No save was opened,
nothing was written to `~/Master of Orion 2`, and no client was
attached to port 17362.

---

# After the order — Data's answer on the Beam OCV/DCV line

**20 September 2026, same day: drop the line entirely, no empty labels
on screen.**

So the head is FOUR slots, not five, and HD's grid is one line shorter
than the original's. That is a deliberate difference and it is
recorded in three places rather than one: the mark
`omission_panel_beam_bonuses`, `154-parked-for-data.md` §1 — which
keeps the two rejected alternatives, because the next session faces
the same choice the moment the numbers exist — and
`v3_projektstatus.md`'s **"What is missing"**, as item 3 under the
Fleets ship panel, with what lifting it costs.

The colony / transport / outpost help paragraph (flt2.cpp:548-575) is
item 4 in the same place, on Data's instruction, and is explicitly not
part of any order yet.

`acceptance_154_1440p.png` in the evidence folder is re-cut against
the shipped panel, so the comparison shows what the screen actually
draws: no Beam line, and the blank destination slot still holding its
place above Weapons/Specials.

**One more fault, found by the fresh-clone check before the push.**
The layout check this order added asserted on wording that comes out
of the player's own HESTRNGS and TECHNAME.LBX, so it passed here and
failed in a clone. The line grid is now measured against a panel built
out of literals and the no-catalogue state is asserted rather than
skipped — the same shape as the ship-picture fallback, and for the
same reason.
