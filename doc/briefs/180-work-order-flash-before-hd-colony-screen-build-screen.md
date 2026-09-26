Work Order — OrionLayer v3

Number: next free (expected 180) Base: main = origin/main = 5ecba52, suite green (354 checks) Mode: Unattended run with no questions to Data. Anything that needs his decision goes into <n>-parked-for-data.md, together with the default you chose, and the run continues on that default. Tracking:

Record progress in <n>-progress.md after every part.
Make one commit per part.
Store evidence under ~/orionlayer-fixtures/evidence/work_order_<n>/.

This order has three subjects:

A. The original artwork flashes before HD appears. This is a release blocker.
B. The single-colony screen, complete.
C. The build screen, complete: buildings and ships, wire ID 25.

A comes first, because B and C must be built under the rule A establishes.

Standing rules

Before you start

Read doc/v3_fundament.md first, then the parts this order touches, and always all of the principles- parts.

Live tests

Run tools/liveguard.py before every live step and check with it afterwards.
Only the scratch slots SAVE4 and SAVE5 may be written. Never touch SAVE8.
Exactly one client may be connected to the server at a time.

Engines left running

Data is not playing. You may close engines and clients you did not start: run liveguard first, send SIGTERM, and use SIGKILL only if needed.
If the desktop was in use within the last few minutes, leave them running as in 179, and note that in progress.

Engine patches

orion2re stays local and is never pushed.
No engine patch may be applied in this order.
Any engine change you need is written as follows:
a new entry, numbered next free, in doc/orion2re_open_fixes.md
a patch file under doc/
proof that the patch applies and compiles with the engine's flags
a misspelt-constant control that must be refused
Then park it for Data's approval. The entry uses the same structure as entry 34: what is missing, what the patch does, what it costs us without it.

Original artwork

MOO2 original files are never copied into the repo, the mod folder or the assets.

Markings

Every difference from the original is marked with the existing labels: DEVIATION, HD EXTENSION, OMISSION, HD STATE, UNVERIFIED.
Each label goes in the module, in the status document, and in a smoke check.
An UNVERIFIED behaviour is not built.

Comparison

Every HD screen in this order is put beside a native screenshot of the same state, at 1920, 2576 and 3840.

Push

Push only when the suite, a fresh clone and liveguard are all green, and no live step is broken by this order. No force push.
If a condition fails, commit locally without pushing, and record the reason.
A — The original flashes before HD

The symptom, as Data reports it: on some screens, before HD appears, the old graphic is shown briefly with a description on the left side. A player must never see this.

Part A1 — Measure before fixing

Nothing is fixed in this part. It establishes what flashes, where, and why.

1. Tag every presented frame with its source.

Add client-side instrumentation that records, for every frame the HD window presents:

the screen ID
whether the frame came from an HD screen, from the safety net (native picture), or from a blank or background fill
a timestamp

Keep the instrumentation behind a flag or a debug setting, so it costs nothing in normal play.

2. Walk every transition into every screen HD draws.

Take the list from the screen registry, not from memory.
Include both directions: into the screen, and back to where it came from.
Include the galaxy-map overlays and modals.
Run the walk at 1920 and at 2576.

For every transition, record:

the number of native frames presented before the first HD frame
how long they stayed on screen

3. Check the second possible source: the engine's own window.

The decisions record that the engine window is not hidden: SDL_ShowWindow runs before g_hide_window is set. Since 179, engine_start also sends a space key to that window to skip the intro.

Find out whether the engine window is ever mapped, raised or focused in front of the HD window:

during startup
during the intro skip
during screen changes

If the desktop cannot be observed from outside, for example under Wayland, write down which method you used, what it can and cannot see, and what it excluded.

4. Match the description.

Identify which native screen or screens show a description panel on the left, and confirm those are the ones that flash.

5. Report.

Write a findings document in doc/briefs/<n>-flash-findings.md listing each flashing transition with:

the source (safety net inside the HD window, or the engine window)
the frame count
the cause in the code, meaning which condition lets the native picture through

Commit the instrumentation and the findings.

Part A2 — Fix it

The rule to implement: a screen HD draws never presents a native frame.

While a transition waits for the data the HD screen needs, the HD window keeps showing:

the last HD frame, or
the universal background.

The safety net's native picture is allowed only for screens and modals that HD has no screen for at all.

If a known screen's data does not arrive within a timeout:

Log it.
Fall back to the safety net once.
Count that fallback as a failure in the checks, not as normal behaviour.

If the cause is inside OrionLayer: fix it in the transition path, in one place for all screens, not screen by screen.

If the cause is the engine window:

Fix it on the client side if that is possible. For example, deliver the intro-skip key without the window coming forward, or use the API instead of a window key.
If it needs an engine change, write it as an open fix and park it, following the standing rule.

Checks:

A smoke check replays recorded transitions for every screen in the registry. It fails if any of them presents a native frame before the first HD frame.
It also fails if a screen is added to the registry without being covered by this check.

Live verification:

Walk every transition from A1 again at 1920 and 2576.
Every transition must show zero native frames.
Store the before-and-after table as evidence.

Wording for Data:

Write the rule as a proposed decision text into parked-for-data.
Leave the decision number free. Data files it himself.
B — The single-colony screen, complete

Safety rule, from the reading reports in order 126: On the single-colony screen, CRUNCH, TOGGLE and the full-screen field [0] must never be activated — not live, not in a test, not by any HD control.

A smoke check holds this rule.

Part B1 — Inventory
Find out what already exists in HD for the single-colony screen, including the colony panel, output rows, surface picture and population figures.
Put it beside the original's routines and list every element the original draws and every control it offers.

For each element, mark whether it is:

(a) already in HD
(b) buildable from data already on the wire
(c) blocked because the data is not on the wire

The reading reports from 126 already name two things that are not on the wire: which colony is shown, and the build and ship lists. Check whether that is still true on the current engine tree.

Store the inventory in doc/briefs/<n>-colony-inventory.md.

Part B2 — Build everything in (b)
Build every element and control the original has that can be built from data already on the wire.
Use the frameless HUD style (core/hud/), glass fill, the universal background and the frame colour.
Follow the rule from Part A: no native frame on entry or exit.

Controls

Every control sends what the original's own field does.
Use the hotkey where one exists and the click as fallback, as in the amended decision.
HD sends no order the player has not chosen.

Live test on SAVE4 or SAVE5

Open the screen for several colonies.
Change only what a scratch slot allows.
Check every value against the native screen.
Part B3 — Everything in (c)
Write one open fix per missing piece of data, each with its patch file, and park it.
In the HD screen, each missing piece is drawn as nothing, not as an invented value, and marked HD STATE.

When the missing piece is which colony is shown

HD must not guess the colony.
Keep the screen on the safety net: the full native screen, not a flash.
Record this as the single most important parked item.

HD code for the patched data

It may be written in advance against a recorded fixture of the patched wire format, and covered by checks.
It becomes active only when the data block actually arrives.
Without the block, the screen behaves exactly as it does today.
C — The build screen (wire ID 25), complete
Part C1 — Inventory

Do the same as B1 for the build screen:

building list, ship list, specials, the current build and queue, and all controls
what exists, what is on the wire, what is not

Store it in doc/briefs/<n>-build-inventory.md.

Part C2 — Build
Build everything buildable from wire data, under the same rules as B2.
Selecting an item to build is an order. HD sends it only when the player chooses it.

Live test on SAVE4 or SAVE5 only

Select a building.
Select a ship.
Cancel.
Confirm that the engine's state matches, both on the wire and in the native screen.
Part C3 — Missing data

Same as B3: open fixes, patch files, parked, and HD STATE markings.

Code written against fixtures stays inactive until the block arrives.

Finish
Run the full suite, a fresh clone and a final liveguard check. Push if every push condition is met.

The progress file ends with a summary covering:

per part, what was done
the new check count
the flash table before and after
for B and C, the share of the original's elements now in HD, versus waiting on a patch

Parked-for-data is ordered by importance:

engine patches to approve, with what each one unlocks
the proposed decision text from A2
everything else

List the live steps Data should look at himself:

every former flash transition
the colony screen beside the original
the build screen beside the original
