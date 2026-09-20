# Work Order 153 — parked for Data

Questions this session could not answer from the tree, and things it
had to decide without the reference the order names.

---

## 1. `~/Downloads/fleets_mockup_narrow.png` does not exist

The order names it as the accepted 1440p mockup and asks for an
acceptance render "beside the mockup". It is not in `~/Downloads`, not
anywhere under `~` (searched by name and by `*narrow*.png`), and no PNG
written after the tracked source (`fleets_frame_4k_map165.png`,
20 Sep 11:39) looks like it. What IS in `~/Downloads` from that
morning:

| file | size | what it is |
|---|---|---|
| `fleets_frame_4k_map165.png` | 3840x2160 | the tracked source, already in `_src/` |
| `fleets_frame_4k_cells.png` | 3840x2160 | an earlier frame, not narrow |
| `fleets_frame_equal_panels.png` / `(1)` | 1672x940 / 3840x2160 | earlier frames, not narrow |
| `fleets_inner_planets_style.png` | 2562x1440 | a RENDER of the current HD screen, not a mockup |

**Nothing was blocked by it.** The order gives the target in numbers
(195 px, aspect 1.6458, ~1491 wide, the width moving from the left
column to the right) and says the mockup is "not art" and that the real
thing is built from the tracked source. Those numbers are what the
build follows. What is missing is only the third panel of the
acceptance render; it is produced as **new beside current**, and the
mockup column is left out rather than filled with a substitute.

If the file exists somewhere this session cannot see, hand it over and
the third panel takes ten seconds to add.

---

## 2. The live part

Recorded in `153-progress.md` under "Live". No live run is required by
either part: Part A is artwork and geometry, Part B reads data HD
already holds and sends nothing. The acceptance renders are made from
the fixture snapshot the smoke test and work order 152 use.
