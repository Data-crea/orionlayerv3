# Work order 134 — what was done

| part | commit | what |
|---|---|---|
| A | `a47650f` | the frame: the Planets ring as a variant, one opening |
| B | `0f0e488` | the screen, its sixteen region boxes, its own scroll bar |
| C | `b6b1f6f` | the wire, the refusal, and the two engine patches |
| D | this one | the checks on a real snapshot, the renders, the marking |

Smoke **215 → 217**. Two new checks: the Fleets markings (C) and the
Fleets screen on a real snapshot (D).

## The numbers this order settled

- Work order **134**; next free **135**.
- Next free fundament decision **70** — and **none was filed**. Every
  rule this screen follows was already there: 3 (does not apply, and the
  screen says so), 5 (one geometry, `fltgeom`), 12 (the frame variant),
  20 (fields by hotkey and type in the live list), 22 and 61 (the loud
  fallback and its marking), 25 (reconstruct first, then read WITH a
  validation), 33 (refuse what the game refuses), 34 (thin_border
  throughout, and why), 42 (derived artwork), 46 (the list window is the
  game's), 55 and 69 (one fixed frame image, plain-scaled). The order
  says to file one only for a decision that is actually new; there was
  none.
- Open fixes **27** and **28** filed and applied; next free **29**.

## What the reading report got right

`doc/fleet_screen_reading.md` was written by a read-only sub-session and
says so, so every number it gives was re-read against the tree before
anything was built on it. **All of them held** — the inset box, the grid
origin, step and cell, the scroll track, the ship panel clip, the twelve
button origins, the twelve static help rectangles. Recorded because it
is what makes the rest of that document usable.

Two things it left open that the build had to settle itself:

- **The captain portrait's extent is not a constant.** `flt2.cpp:848-866`
  reads `animate::Get_Width_/Get_Height_` of the LBX art. That is why no
  box claims `inner_panel` on this screen.
- **RETURN's help rectangle is not RETURN's button.** Help 374 is
  `(456, 430)-(628, 456)`, a strip reaching left across the two filter
  radios; the button is at `(556, 430)`. `fltgeom` derives the box from
  both and says which edge came from where.

## What is not built

`doc/briefs/134-parked-for-data.md` — the live acceptance (parked: the
display server is unreachable), the four OMISSIONs, relocation, move
orders, the detailed ship view, and the six still-open questions from
the reading's §9.
