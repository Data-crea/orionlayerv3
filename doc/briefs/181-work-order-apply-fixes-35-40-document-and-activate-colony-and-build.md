Work Order — OrionLayer v3

Number: next free (expected 181) Base: main = origin/main = 7fa43b4, suite green (371 checks). orion2re orionlayer-local = 9ab84230 (Fix 34). Mode: Unattended run, with no questions to Data. Anything that needs his decision goes into <n>-parked-for-data.md together with the default you chose, and the run continues on that default. Record progress in <n>-progress.md, updated after every part. Make one commit per part.

What this order is: Data has approved Open Fixes 35, 36, 37, 38, 39 and 40, as a complete series and in that order (brief 180, doc/briefs/180-parked-for-data.md, item 1). This order applies them, documents every engine change, and activates the colony screen and the build popup that work order 180 built against fixtures.

Standing rules

Before you start

Read doc/v3_fundament.md first, then the parts this order touches, and always all of the principles- parts.

Live tests

Run tools/liveguard.py before every live step, and check with it afterwards.
Only the scratch slots SAVE4 and SAVE5 may be written. Never write SAVE8.
Exactly one client may be connected to the server at a time.
MOX.SET's byte that changes on load is known (fundament), and liveguard restores it.

Engines already running

Data is not playing. You may close engines and clients you did not start: run liveguard first, send SIGTERM, and use SIGKILL only if needed.
If the desktop was in use within the last few minutes, leave them running and note it in progress.

Colony screen safety

CRUNCH, TOGGLE and the full-screen field [0] must never be activated — not live, not in a test, not by any HD control.
The existing smoke check stays.

Engine scope

Only Fixes 35 to 40 may be applied.
Any other engine change you find necessary is written as a new open fix, with its patch file, and parked. It is not applied.
orion2re stays local and is never pushed.

Original artwork

MOO2 original files are never copied anywhere.

Push

Push only when all of these are green: the suite, a fresh clone, liveguard, and the flash check from 180 (zero native frames on every recorded transition). No live step may be broken by this order. No force push.
If a condition fails, commit locally, do not push, and record the reason.
Part 1 — Apply the series 35 to 40

Apply the patches on orionlayer-local, in this order, each on top of the previous one:

Fix    Patch file
35    doc/ext_colony_screen_colony.patch
36    doc/ext_colony_building_placement.patch
37    doc/ext_colony_status_word.patch
38    doc/ext_colony_product_cost.patch
39    doc/ext_build_popup_queue.patch
40    doc/ext_build_popup_lists.patch

For each fix, before moving on to the next

Run patch -p1 --dry-run, then patch -p1. It must apply with no offset and no fuzz. Any offset or fuzz counts as a failure, see "If a fix fails" below.
Rebuild with ninja -C out/build/Linux/linux-debug.
Make one commit on orionlayer-local per fix. The message starts with OrionLayer Open Fix <N>: and states what the block sends and why.
The series must reproduce the scratch commits from 180 byte for byte, apart from the Fix 39 marker correction below. Record that you verified this.

Fix 39 marker correction

Data requires every engine change to be recognisable as ours. In tools/version_check.py, Fixes 35–38 and 40 carry the marker OrionLayer, open fix N., but Fix 39 carries only the symbol name COLBLDG::_colony_auto_building.

Before committing Fix 39, check whether its code change carries an OrionLayer, open fix 39. comment like the others.
If it does not, add the comment and update the patch file, so that patch file and commit match.
Switch its version_check marker to OrionLayer, open fix 39.
Record in the Fix 39 entry that the patch differs from the 180 proof only by this comment, and show the diff of the patch file.

If a fix fails (it does not apply cleanly, does not build, or its live check in Part 2 fails):

Do not improvise a different engine change.
Revert that fix with patch -R -p1 and a rebuild.
Do not apply the fixes after it. The series is stacked, so they depend on it.
Document the failure in the entry, park it, and continue with whatever the applied fixes allow.

If Fix 35 itself fails: both screens stay the safety net exactly as today. Do Part 2 only to confirm that, then go straight to the Finish section.

Part 2 — Document every engine change

Data requires this. It is part of the definition of done, not optional. The model is how Fix 34 was documented in 179.

For each applied fix:

1. Comment in the engine source

At every changed place in src/ext/ext_api.cpp, add a comment naming OrionLayer, open fix <N>. and the reason in one line.
Check with a grep that each of the six markers is present exactly where its block is.

2. Entry in doc/orion2re_open_fixes.md

Change the status to APPLIED, and add:

the date
the orionlayer-local commit hash
the OrionLayer commit that records it
the change: file, function and line numbers, plus the full diff (the blocks are short)
the live result from Part 3, with a pointer to a wire excerpt of that block
how to revert it: patch -R -p1, or git revert <hash> in reverse series order, then a rebuild
the side effects you observed or ruled out

The 36 entry additionally keeps stating that HD does not place buildings yet (UNVERIFIED building_placement), and why.

3. version_check

Move each applied patch from REPORTED_PATCHES to LOCAL_PATCHES.
version_check must then require all applied fixes. Check that a build without one of them is reported.

4. Applied-fixes list

Update every place that tells a fresh clone which fixes it needs:

README
the setup and rebuild instructions
the overview line in the fundament

After this part, a fresh clone on another machine must know it needs Fixes 35 to 40.

5. Docs against the commits

For every fix, the diff in the entry must match the committed engine change byte for byte. Record that you verified this, fix by fix.

6. Bundle

Write a new bundle of orionlayer-local next to the one from 179.
Name it so it is clear it contains Fix 34 through 40.
Verify it with git bundle verify.
Part 3 — Activate and accept both screens live

With the blocks now on the wire, the HD code from 180 has to switch on by itself. No flag is needed.

Wire against the fixtures

Record each new block live: COLS, CBLD, CEVT, CPRD, BLDQ and BLDL.
Compare field layout and sizes against tools/fixtures/colony_blocks_180.json.
If they differ, the live wire is right. Correct the fixture and the parser, and note it in progress.

Colony screen (screen 1), on SAVE4 or SAVE5

Open the screen from every way the game offers that is reachable in the scratch save:

the galaxy map
the colony summary
the Info screen / turn summary
via < and > between colonies

Each time, HD must show the same colony as the native screen, including right after switching. That is the handle/pair agreement from Fix 35.

Check every element against the native screen:

status word (Plague and Pop Boom if the save can show them, otherwise record that they are not reachable)
production bar and turns (Fix 38)
buildings as a list (DEVIATION building_list)

Do one pop move, confirm it on the wire, move it back, and restore the save word for word.

Build popup (screen 25), on SAVE4 or SAVE5

Check both lists against the native popup: order, names, and cost / maintenance / time (Fix 40).
Check that the queue under edit is shown before OK (Fix 39), and that Auto Build's state is correct.
Select a building, then a ship, then Cancel. The production queue must be exactly as before.
Then add one item and confirm with OK. Check it on the wire and in the native screen, and restore the scratch save.

Flash

Walk every transition into and out of screen 1 and screen 25 at 1920 and 2576. Every one must show zero native frames.
Add these transitions to the recorded set that the 180 flash check replays.

Comparison images

Put native and HD side by side at 1920, 2576 and 3840, for the colony screen (at least three different colonies) and for the build popup.
Store them under ~/orionlayer-fixtures/evidence/work_order_<n>/.

Markings

Every remaining HD STATE from 180 that the new blocks fill must disappear: from the module, from the status document, and from its smoke check. A check that is removed this way must be recorded, because the thing it measured is gone.
DEVIATION and UNVERIFIED stay where they still apply.
Finish
Run the full suite, a fresh clone at the head (setup must name Fixes 35–40), the flash check, and a final liveguard check.
Push if every condition is met.

The progress file ends with a summary covering:

per fix: applied or not, both commit hashes, and documented yes/no
the new check count
the share of the colony screen's and the build popup's elements now in HD, with what is still missing and why
the parked items
the live steps Data should look at himself, at minimum:
the colony screen beside the original
the build popup with one real build order
switching colonies with < and >
