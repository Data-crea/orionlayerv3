# Work Order 166 — Research screen: no glimpse of the original on entry, a frame from the Fleets art, drawn inner boxes, text that fits

First line for references: "Work Order 166 — Research screen: no glimpse of the original on entry, a frame from the Fleets art, drawn inner boxes, text that fits"

Filed as 166 because 165 was the last one. Check that before filing and take the next free number if it is taken.

Read the fundament index, the principles- parts, and of the decision parts only 04-decisions-screen-artwork-and-markings.md and 03-decisions-sizing-sprites-and-fonts.md. Nothing else at startup; read further parts only when a part of this order needs them.

## Why (Data)

Data looked at the change-mode panel live at 3500.3 and saw four things:

1. On opening, the original shows for a moment — the game's own picture, with a description on the left — before the HD panel appears. The player must never see that.
2. The panel has no outer frame. It gets one now, taken from the Fleets artwork.
3. The eight inner boxes use frame art that does not fit. They are to be drawn in code, the way the Planets screen draws its boxes.
4. The text does not sit cleanly in the boxes. Seen in Data's capture: each field name ("Servo Mechanics", "Ion Fission", …) sits on the top edge of its box; the hover band on "Molecular Compression / Atmospheric Renewer" runs past the right edge of its box and does not line up with it.

This supersedes, for the research screens only, the earlier "frame and artwork come later": Data has decided the frame now.

## How this run works

Unattended, no reporting stops. Rules: the block headed "RULES FOR THE WHOLE RUN — re-read this block at the start of every part" in `doc/briefs/126-work-order-unattended-run.md`, plus the three additions at the top of work order 129. Progress in `doc/briefs/166-progress.md`, Data's items in `doc/briefs/166-parked-for-data.md`, evidence under `~/orionlayer-fixtures/evidence/work_order_166/`. Separate commits per part. Push after a fresh-clone check: released by Data for this order. No change to orion2re.

Live runs: `tools/gameload.py`, SAVE4/SAVE5 for anything that changes the game, SAVE8 never. At the end reload SAVE10 and confirm by snapshot (stardate 3500.3, 2 players), as in 165.

**Both modes.** Change mode (36) and select mode (53) share one implementation since 165 B. Every part below applies to both. Select mode is proven offline and in the fixtures; its live acceptance still waits on Data's mouse (open fix 26) and is not part of this order.

Where this order leaves a choice, take the default, record the choice in the parked file (what, why, cost of reversal) — 165 showed what happens when a choice is taken silently.

## PART A — Never show the original on entry

Find out first what Data saw, then fix it. Likely, from `doc/tech_change_reading.md` §4: the first snapshot at 36 carries the one-field list `Clear_Fields_` leaves behind, the validation against the field list fails, and the screen falls back to the framebuffer for one or more frames. Confirm or refute that from a frame-by-frame capture of the entry before changing anything.

Rules for the fix:

- A disagreement that is TRANSIENT on entry (the list not yet built) must not show the framebuffer. HD keeps drawing what it drew last — here the HD galaxy map — until the list validates.
- A disagreement that PERSISTS still falls back, and loudly (the log line from 165 A). The wait has a bound, measured from the captures with margin, not guessed. Falling back must stay possible; the fix must not turn a real failure into a frozen map.
- If the cause sits in the shared dispatcher or in `ScreenBase` rather than in the research screens, fix it there, and list in the report which other screens the same entry glimpse could reach. Do not build those screens' acceptance in this order.

Acceptance: a frame-by-frame capture of five entries into change mode from the map, in which no frame shows the game's framebuffer; the counter-test (the old behaviour restored) shows the glimpse again in the same capture method. A check that holds the rule offline.

## PART B — The outer frame, from the Fleets art

Source: `screens/fleets/assets/frame.png` (3840x2160). Take the upper left inner frame — the one around the Fleets scanner map, with the orange lamps in its four corners. Cut it out of that picture (not copied by hand from a screenshot), record where it came from and at what native rectangle, and use it as a nine-slice: corners at native pixel size, edges stretched, so it fits the research panel at every resolution.

It becomes the research panel's outer frame, in both modes, around the panel's content box (the box `core/researchnative.py` already transcribes). The frame is HD artwork, not a transcription: mark it as the fundament's artwork decisions require. The CANCEL button in change mode stays inside the frame.

Default if the frame's corners collide with the panel content at the smallest resolution: the frame grows outward, never inward over content. Record it if that happens.

Acceptance: HD captures at all four resolutions (1080p to 4K) with the frame, beside the native frame; corner lamps unstretched in every one (measured, not only looked at).

## PART C — Inner boxes drawn in code, like the Planets screen

Remove the frame art the eight category boxes and the two popups use today. Draw their boxes the way `screens/planets/` draws its boxes (the thin outline colour and fill it takes from the palette), through the same helpers if they can be shared, rather than a second copy.

Acceptance: no inner frame asset is loaded by either research screen any more (checked); captures at four resolutions.

## PART D — Text that fits

Every string on both research screens and in both popups — category label, cost, field name, application rows, CANCEL, the description box — lies inside its box with a margin, at every resolution. The hover band covers exactly its row and stays inside its box.

Proof by measurement, not by eye alone:

- An offline check that renders both screens at all four resolutions with the longest real names (field and application names from the extracted tables, the longest per box) and asserts every text bounding box lies inside its box with the margin, and every hover band inside its box. Counter-test: move one text onto the box edge, the check turns red.
- Then look at the captures yourself, every one of them. In 165 the missing panel fill was found by looking, not by the check. Anything the eye finds that the check missed goes into the check.

If a name cannot fit at the size the fundament's font rules set, the existing shrink rule applies (the DEVIATION `research_select` already marks). Do not clip.

## PART E — One counter in the tree

Replace `tools/colony_move_hd.Counter` with the repaired `SendCounter` (165 H). One class for counting sends in the tree afterwards. No record on disk changes.

## Abort rules

- A save hash differs after a live run: stop live work, park with the evidence.
- Part A's cause turns out to be on the engine side: describe it, park it, finish B to E.
- The suite goes red and the cause is not found within two attempts: revert that part's commits, park it, continue with the next part.

## Closing

Suite green, working tree clean, pushed after the fresh-clone check, SAVE10 reloaded and confirmed. Short final report in German: what Data saw in point 1 and why, what each part changed, the captures to look at (paths), and every choice taken with its default or not.
