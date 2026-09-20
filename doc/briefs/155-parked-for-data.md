# Work Order 155 — parked for Data

Two things the order asked to have raised before they were decided,
and the live declaration.

---

## 1. The strip is not a star-name field, and that changes the ask

The order said: *"If the original uses the bar for something else
entirely, say so before overriding it — Data decides whether hover
takes precedence or shares the space."* It does, so here it is.

Help 363 calls the strip **"information as you scan ships and stars
in the galaxy map window"**, and
`FLT2::Print_Fltscrn_Scanned_Star_Name_` (flt2.cpp:338-522) chooses
one of **ten** states:

| when | what the strip says |
|---|---|
| ships selected, reachable this turn | H 0x67 "Orbiting %s" |
| ships selected, N turns, star visited | H 0x69 / 0x6A "%d turn(s) to %s" |
| ships selected, N turns, not visited | H 0x6B / 0x6C "ETA %d turn(s)" |
| a black hole in the way | H 0x21 |
| the ships cannot move | H 0x6E |
| out of range, star visited | H 0x6F / 0x70 "%d parsecs to %s" |
| out of range, not visited | H 0xEB |
| hyperspace flux | H 0x73 |
| **no ships selected** | **the star's own name** (state 7) |
| no ships selected, and the player knows nothing of the star | **H 0x94** (state 8) |

So naming the hovered star IS the original's behaviour — in exactly
one of the ten, the one where nothing is selected. The other eight
are a MOVE PREVIEW driven by `SHIPMOVE::Ships_Try_To_Move_To_` and
`_g_ship_move_info`, which is on no wire and which
`layout.json` has marked an OMISSION since work order 134.

**What was built, and the decision inside it.** HD draws states 7 and
8. **With ships selected it prints nothing at all.** The alternative
was to print the star's name there anyway — but the original is
answering "can these ships get there, and how long" and a name is not
a worse answer to that question, it is an answer to a different one.
Silence is honest; a name would be a quiet invention of exactly the
kind work order 152 caught here before.

**Say if you want it the other way** — name the star in all ten
states — and it is one line. It would be a marked DEVIATION rather
than a transcription.

**And one sub-state is out of reach either way.** State 7 has a
longer form when the player has a colony at the star and an officer
assigned: the star's name, the governor's name and an ETA
(H 0x92 / 0x93, flt2.cpp:478-489). It reads `s_leader_data`, which
`core/structs/unverified.py` refuses — the same struct the Beam
OCV/DCV line is waiting on, already on the open list.

---

## 2. The two small boxes were already built

The order describes them as boxes that "switch". They are PREV FLEET
and NEXT FLEET, and the original's own help says what they do:

* **364** — *"Pressing this button will 'go back' one fleet in the
  list of all fleets in your empire. Note that as the filter buttons
  are selected, a fleet may be skipped."*
* **365** — *"Pressing this button will display the next fleet in
  your empire."*

`FLT1::Next_Ship_Icon_` and `Previous_Ship_Icon_` (flt1.cpp:990-1060)
step `_small_ship_stack_ptr` through the ship stacks, wrapping, and
staying inside the same ownership class — own stacks cycle among own
stacks and foreign among foreign.

**HD has activated both through the game's own field since work order
134.** `FleetsScreen.handle_click` sends `ACTIVATE_FIELD` for any box
whose name is in `fltwire.HOTKEYS`, and `prev_fleet` and `next_fleet`
are in it; the existing check already covers "the filters get a click
and the rest an activation". Nothing was needed here, and nothing was
changed — re-implementing a working path would have been the worse
outcome.

**BUT THEY SHOW NOTHING, AND THE ACCEPTANCE CAPTURE MAKES THAT
PLAIN.** Look at `acceptance_155_strip_1440p.png`: the two boxes
either side of the strip are empty in every one of the four states.
They are clickable and they work, but a player has no way to know
what they are. The original fills them with FLEET.LBX arrow art,
which is MOO2's and not in this tree (decision 42), so HD draws
nothing at all — the same shape of gap the grid cells had before
work order 142 D1 gave them the extracted pictures.

Three ways to close it, none of them done here because the order did
not ask: extract the two arrows the way `fleet_art_extract.py`
already extracts the rest of this screen's art; draw a glyph of our
own and mark it an HD EXTENSION; or put the words PREV and NEXT
there, which is what `layout.json`'s `words` already does for the
seven buttons that have no string either. **The third is the
cheapest and the most consistent with what this screen already
does.** Say which.

---

## 3. The live part — nothing to run

Hover resolves the star from the stars HD already draws and **sends
nothing**, which is the order's own rule; the two buttons were
already built and already covered. There is no state a live run could
show that the fixture does not, and the fixture drives the real
screen object through the real parser.

No save was opened, nothing was written to `~/Master of Orion 2`, and
no client was attached to port 17362.
