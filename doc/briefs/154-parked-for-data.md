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

## 2. A colony, transport or outpost ship has a different panel entirely

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
