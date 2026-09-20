# Work Order 155 — progress

One commit. The two questions the order told me to raise first are in
`155-parked-for-data.md`; this is what was established and built.

---

## What the original does with that strip

Read before anything was written, and the reading changes the ask.

**Help 363 names it**: *"This window displays information as you scan
ships and stars in the galaxy map window."* Not a star-name field — a
SCAN readout.

`FLT2::Print_Fltscrn_Scanned_Star_Name_` (flt2.cpp:338-522) is called
from one place, under one condition:

```
if (MOX::_galaxy_map_scanned_star > -1)
    FLT2::Print_Fltscrn_Scanned_Star_Name_();        flt1.cpp:397
```

so **with nothing scanned the original does not write the strip at
all** and it is empty. Inside, it picks one of **ten** states. The
first thing it does is ask whether any ships are selected
(`Build_Fltscrn_Ship_List_`), and that decides everything:

| condition | state | text |
|---|---|---|
| ships selected, arrives this turn | 0 | H 0x67 "Orbiting %s" |
| ships selected, N turns, visited | 1 | H 0x69 / 0x6A "%d turn(s) to %s" |
| ships selected, N turns, not visited | 2 | H 0x6B / 0x6C "ETA %d turn(s)" |
| black hole in the way | 3 | H 0x21 |
| ships cannot move | 4 | H 0x6E |
| out of range, visited | 5 | H 0x6F / 0x70 "%d parsecs to %s" |
| out of range, not visited | 6 | H 0xEB |
| hyperspace flux | 9 | H 0x73 |
| **no ships selected** | **7** | **the star's own name** |
| no ships selected, player knows nothing of it | 8 | H 0x94 |

State 7 has a longer form — star name, governor's name, ETA
(H 0x92 / 0x93, flt2.cpp:478-489) — when the player has a colony
there and an officer assigned.

The text is CENTRED: `Print_(169 - width/2, (23 - h)/2 + 248)`
(flt2.cpp:519-521), and the colour is `_neutral_colors` for the
refusals and the unexplored case, or the owner's player colour when
the star has one and no ships are moving.

**The "know it" test is the same four-way one the destination line
uses**: `Player_Has_Visited_ || TRAIT_OMNISCIENCE ||
One_Leader_With_Galactic_Lore_ || Contact_With_One_Colony_`
(flt2.cpp:379-383).

## What was built

**States 7 and 8, and nothing else.** The other eight are the move
preview, driven by `SHIPMOVE::Ships_Try_To_Move_To_` and
`_g_ship_move_info`, which is on no wire and has been marked an
OMISSION since work order 134. So:

* nothing scanned -> the strip is empty, as the original leaves it;
* a star hovered, no ships selected -> its name;
* a star the player knows nothing of -> H 0x94, and **the name is not
  printed**, through `fltrows._player_knows_star` — the helper work
  order 154 built, so HD can under-report and never over-report;
* **ships selected -> nothing.** The original is answering "can these
  ships get there" and HD cannot; a name would be an answer to a
  different question. That decision is in `155-parked-for-data.md` §1
  with the one-line alternative if Data wants it the other way.

**Hover sends nothing**, which is the order's own rule.
`fltmove.star_at` resolves the star from the stars HD already draws —
`galaxy_inset_stars` emits one entry per star in `game_state.stars`
order and skips none, so the drawn index IS the star index. It is
**one copy**: `fltmove.click` was carrying that arithmetic and now
calls the same function (decision 5).

**The three scans are mutually exclusive, as in the original.**
Taking a big icon sets `_scanned_big_ship` and clears
`_galaxy_map_scanned_star` in the same branch (flt1.cpp:616-620), so
the strip goes quiet when the pointer moves onto the grid. Taking a
star clears `_scanned_small_ship` but **not** `_scanned_big_ship`
(:649-652), so the ship panel keeps its ship while the strip names a
star. HD does both.

## What was already there

**The two small boxes are PREV FLEET and NEXT FLEET, and they have
worked since work order 134.** `FLT1::Next_Ship_Icon_` /
`Previous_Ship_Icon_` (flt1.cpp:990-1060) step
`_small_ship_stack_ptr` through the ship stacks, wrapping and staying
inside the same ownership class; HD's `handle_click` sends
`ACTIVATE_FIELD` for any box in `fltwire.HOTKEYS`, which includes
both, against a freshly read field list. Nothing was needed and
nothing was changed.

What IS missing is that they show nothing — see
`155-parked-for-data.md` §2, with the three ways to fix it and a
recommendation.

## What is held

One new check, driven through the real screen on a fixture that now
carries star records:

1. each visited star names itself in the strip, and **nothing is
   sent** — asserted after every hover;
2. an unexplored star is **not** named;
3. an empty patch of map clears the strip;
4. hovering a grid cell clears the scanned star and sets the ship
   panel's — the exclusion;
5. with a ship selected the strip is empty;
6. `fltmove.star_at` is the one answer, and says so outside the box.

The fixture asserts its own stars do not land on top of each other,
or hovering could not tell them apart and the whole check would pass
vacuously.

Smoke 242 -> 243.

## Acceptance

`~/orionlayer-fixtures/evidence/work_order_155/` —
`acceptance_155_strip_1440p.png` is the strip in all four states at
2560x1440, and the four full screens beside it. The order asked for
them "beside the original in the same states"; the original's own
capture of this strip is the one thing not in the fixtures, because
work order 152's native capture was taken with nothing scanned and
the strip empty. What IS beside it is the source, state by state, in
the table above.

## Live

**No live run.** Hover sends nothing — that is the order's rule and
the thing the check asserts — and the two buttons were already built
and already covered. No save was opened, nothing was written to
`~/Master of Orion 2`, and no client was attached to port 17362.
