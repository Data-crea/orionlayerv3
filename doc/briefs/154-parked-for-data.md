# Work Order 154 — parked for Data

One decision taken without asking, one piece of work found and not
done, and the live declaration.

---

## 1. Beam OCV / Beam DCV: the labels are drawn, the numbers are not

The order asked which of three things this is, and it is the third
one it did not list: **absent always, and absent for a reason that is
not the layout.**

`Print_Scanned_Ship_Data_` prints the line for every combat ship
(flt2.cpp:606-622) and the numbers come from
`INITSHIP::Get_Ship_Combat_Bonuses_` (initship.cpp:638-687), which is:

    Get_Design_Combat_Bonuses_(design)
      + Helmsman_Bonus_(ship->officer_index)        <- leader records
      + Weaponry_Bonus_(ship->officer_index)        <- leader records
      + MOX::_crew_data[crew_quality].attack/.defense
      + player.traits[TRAIT_SHIP_ATTACK / _DEFENSE]
      + (strategic combat) Best_Warp_Drive_ and _hull_data[].strat_def_bonus
      + (trans-dimensional) COMBAT1::_td_combat_speed_bonus * 5

`officer_index` itself is in HD's ship spec, but the two bonuses it
feeds are skills in the LEADER record, and `core/structs/unverified.py`
refuses that struct (decision 23). So the number cannot be computed
for any ship that has a captain, and a panel that printed a number for
some ships and nothing for others would be worse than one that prints
none.

**ANSWERED, 20 September 2026: drop the line entirely — no empty
labels on screen.** So HD's head block is four slots where the
original's is five, the grid is deliberately one line shorter, and the
gap is recorded in the mark and on the open list rather than shown as
a label with nothing after it. What follows is what was proposed and
why Data's answer went the other way; it is kept because the next
session will face the same choice the moment the numbers arrive.

**What work order 154 did, and the two alternatives it chose over.**
HD drew the two LABELS at the original's own tab stops and no values.

* *Draw nothing at all and drop the line.* Rejected: everything below
  it would sit a line higher than the original, which is exactly what
  the order's acceptance measures.
* *Reserve the line as a second blank.* Rejected: for a parked ship
  that is two blank lines in a row, which reads as a layout fault and
  hides the gap instead of showing it.
* *Labels, no values.* Chosen. The line keeps its place, and a label
  with nothing after it says "this value is missing" where a blank
  says nothing at all — the same argument `deviation_panel_overflow`
  already makes for the "+n more" marker.

**Data did say so**, and it was a two-line change. The labels are gone;
`Panel.HEAD_SLOTS` is four, `omission_panel_beam_bonuses` says why, and
`v3_projektstatus.md`'s "What is missing" carries the cost of lifting
it — the leader record first, then four static tables.

Lifting it properly is a content project: verify `s_leader_data`, and
transcribe `_crew_data`, `_hull_data[].strat_def_bonus` and
`Get_Design_Combat_Bonuses_`. It is not formatting and it was not done
here.

---

## 2. A colony, transport or outpost ship has a different panel entirely — **BUILT**

**Done in work order 159 part 1, 21 September 2026, commit `8b679c2`.**
The panel has a second mode keyed on `ship_type`, the text comes
through the same `helptext` the right-click help uses, and all three
records fit their hole at every resolution (measured: colony 3 lines,
outpost and transport 4). The colour is the one thing NOT
transcribed — the original's is a ramp over MOO2 palette indices
111..116 and pinning it needs the player's palette plus a native
screenshot — so it is marked `deviation_panel_paragraph_colour` and
parked in `doc/briefs/159-parked-for-data.md`.

The entry as it was found follows, unchanged.

---

Found while transcribing, not asked for, and NOT built.

`Print_Scanned_Ship_Data_` returns early for `ship_type` 1, 2 and 4
(flt2.cpp:548-575): it loads a HELP.LBX record — 0x29 for a colony
ship, 0xBD for a transport, 0x6D for an outpost — and prints it as a
centred paragraph in a different colour. No crew line, no shield, no
bonuses, no destination, no weapons, no specials. It is prose about
what the ship is for.

HD draws the data panel for these ships, which shows MORE than the
original rather than less, so nothing is hidden by leaving it. Marked
as `omission_panel_support_ship_help`.

**It is buildable.** HD already loads HELP.LBX through
`tools/help_extract.py` and the ids are the same ones the context help
uses. It is a second layout mode for this panel and its own piece of
work; the remit here was the formatting of the data panel.

**ON THE OPEN LIST, 20 September 2026** (Data), as item 4 under "The
Fleets ship panel" in `v3_projektstatus.md`'s "What is missing" —
explicitly not part of this order.

---

## 3. The live part — nothing to run

This order changes where text is drawn inside one box. It reads no new
field, sends nothing, and the acceptance is a picture compared against
a native screenshot that already exists in the fixtures
(`evidence/work_order_152/panel/001_20_panel_native.png`, captured
live on 20 September 2026 with the hashes recorded beside it).

No save was opened, nothing was written to `~/Master of Orion 2`, and
no client was attached to port 17362.

---

## 4. The leader record: tried, and it does not verify. 20 September 2026

Data asked for one attempt with `struct_probe`, "the way crew_quality
was verified: two independent sources, live readings across enough
ships and officers to be non-vacuous", and to put the Beam OCV/DCV
line back if it held.

**It does not hold, and the reason is not the one expected.**

### What ran

One client, the engine already up, no OrionLayer attached (checked:
`ss -tanp` showed 17362 in LISTEN with no established connection).
`python tools/struct_probe.py leaders` plus a decoder over all 67
records. Nothing was loaded, nothing was sent, nothing was saved.
SAVE1-9 and SAVE11 hashed before and after and **identical**; SAVE10
logged, `70f86100…`, unchanged.

### What the reading gives

Six of the fifteen fields corroborate against the header
(orion2.h:1088-1104, `sizes.h:28` asserting 0x3b), and one of them
numerically:

* `type` @35 against the title on all 67 — 0 for "Rebel Pilot" and
  "Pirate Captain", 1 for "Science Leader" and "High Priestess", no
  counter-example;
* `special_skills` @42 against the title — "Weapons Officer" is
  exactly `LEADER_SHIP_SKILL_WEAPONRY`, "Trilarian Navigator" is
  HELMSMAN|WEAPONRY, "Legendary Pilot" is HELMSMAN2;
* **`xp` @36 numerically** — the only values in 67 records are 0, 60,
  150, 300 and 1000, and `Get_Officer_Base_Level_` (officer.cpp:44-61)
  steps at 60, 150, 300, 500, 1000. A wrong offset does not land on
  another function's thresholds.

`level` @52 is 0 in all 67 and `location` @53 is -1 in 65, so neither
is corroborated by anything, and seven fields have no ground truth at
all here.

### Why it is not enough — two blockers, neither of them the struct

**1. The officer path is vacuous.** The panel reaches the leader
record only through `s_ship_data.officer_index`, and the loaded save
has **0 of 21 ships with an officer**. Across all ten saves on this
disk — read from the FILES, nothing loaded — only SAVE1, SAVE3, SAVE4
and SAVE5 have one at all, and each has exactly one: **4 ships of
185**. This is the shape of the damaged-special check that held on 60
ships and proved nothing.

**2. The ground truth cannot be read.** Even with a good save, the
check is "does my number equal the one the game prints". The game
prints that panel only for `_scanned_big_ship`, which it sets from its
OWN cursor (flt1.cpp:616-620) — and the Extension API has no mouse
motion. That is the same gap work order 153 B worked around on HD's
side, and it cannot be worked around on the game's. An INJECT_CLICK
would set it, at the cost of toggling that ship's selection, and would
buy one data point on one ship.

### What is NOT missing

The static tables everyone assumed were the hard part are plain
literals in the source and cost nothing: `_crew_data` (mox.cpp:780),
`_computers[].bonus` and `_hull_data` (techdata.cpp:429 and :77), and
`Get_Officer_Base_Level_` is five lines. `Get_Design_Combat_Bonuses_`
(initship.cpp:1339-1378) is `_computers[].bonus` plus
`combat_speed * 5` plus seven special-device bits. The traits are
already decoded and their indices are now known —
`TRAIT_SHIP_DEFENSE` 6, `TRAIT_SHIP_ATTACK` 7, `TRAIT_WARLORD` 30.

### Stopped, as instructed

The line stays dropped. The findings are recorded at
`core/structs/unverified.py`'s `LEADER` entry — so the next attempt
starts from the layout and the two blockers rather than from
scratch — and on the open list in `v3_projektstatus.md` with the order
the work has to happen in: **a save with several officered ships
first, then a way to read the original's own panel for one of them,
then the transcription.**
