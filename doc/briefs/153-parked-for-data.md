# Work Order 153 — parked for Data

Questions this session could not answer from the tree, and things it
had to decide without the reference the order names.

**NOTHING IS OPEN.** Both entries are closed; they are kept because a
question that vanishes leaves no record that it was ever asked, and
the second one is the live-run declaration the rules require.

---

## 1. `~/Downloads/fleets_mockup_narrow.png` — RESOLVED, 20 September 2026

**Data's answer: the file never existed on this machine.** It only ever
existed outside it and was never put in `~/Downloads`. That is the
whole of it — not a path this session could not reach, and not
something to go looking for again.

**Agreed with it: the acceptance render stays at two panels**, new
beside current. The mockup column is not to be re-cut.

### What was asked, and what the search found

The order names the file as the accepted 1440p mockup and asks for an
acceptance render "beside the mockup". It was not in `~/Downloads`,
not anywhere under `~` (searched by name and by `*narrow*.png`), and
no PNG written after the tracked source
(`fleets_frame_4k_map165.png`, 20 Sep 11:39) was it. What IS in
`~/Downloads` from that morning, none of it the mockup:

| file | size | what it is |
|---|---|---|
| `fleets_frame_4k_map165.png` | 3840x2160 | the tracked source, already in `_src/` |
| `fleets_frame_4k_cells.png` | 3840x2160 | an earlier frame, not narrow |
| `fleets_frame_equal_panels.png` / `(1)` | 1672x940 / 3840x2160 | earlier frames, not narrow |
| `fleets_inner_planets_style.png` | 2562x1440 | a RENDER of the current HD screen, not a mockup |

### Why nothing was blocked

The order gives the target in NUMBERS — 195 px, aspect 1.6458, about
1491 wide, the width moving from the left column to the right — and
says in the same breath that the mockup is "not art" and that the real
thing is built from the tracked source. Those numbers are what the
build followed, and every one of them is asserted against the cut
holes in `fleets_frame_reshape.TARGET_HOLES` and in the smoke test.
The mockup would have changed nothing about the artwork; it was only
ever going to be the third panel of a picture.

**The lesson worth keeping is the general one**, and it is the
delivery agreement's own: a package may name a file that is not there,
and the answer is to say so and carry on from what CAN be verified —
not to substitute the nearest-looking thing and not to stop.

---

## 2. The live part — CLOSED, nothing to run

Recorded in `153-progress.md` under "Live". No live run is required by
either part: Part A is artwork and geometry, Part B reads data HD
already holds and sends nothing — that is the point of it. The
acceptance renders are made from the fixture snapshot the smoke test
and work order 152 use.

No save was opened, nothing was written to `~/Master of Orion 2`, and
no client was attached to port 17362 at any moment of the session.
