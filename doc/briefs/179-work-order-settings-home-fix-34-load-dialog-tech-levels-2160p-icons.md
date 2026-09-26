Work Order — OrionLayer v3

Number: next free (expected 179) Base: main = origin/main = d2b30a6, suite green (344 checks) Mode: unattended run, no questions to Data. Anything that needs his decision goes into <n>-parked-for-data.md together with the default you chose, and the run continues with that default. Tracking: progress in <n>-progress.md, updated after every part. One commit per part.

Standing rules
Live tests: always run tools/liveguard.py before any live step, and check with it afterwards. Only the scratch slots SAVE4 and SAVE5 may be written. Never touch SAVE8.
Engines: Data is not playing right now. You may terminate foreign engine processes. Run liveguard first, then send SIGTERM, and use SIGKILL only if needed.
orion2re: stays local and is never pushed. Fix 34 is approved by Data (see Part 2). No other engine patch may be applied. If you find a new engine problem, add an entry to doc/orion2re_open_fixes.md and a patch file, but do not apply it.
No MOO2 originals: original MOO2 files are never copied into the repo, the mod folder or the assets.
HUD: recoloring applies to HUD parts only, never to images. Style values live in assets/shared/hud/style.json.
Push: only when the suite, a fresh clone and liveguard are all green, and no live step is broken by this order. No force push. If a condition fails, commit locally, do not push, and record the reason in progress.
Part 1 — Move user_settings.json to ~/.config/orionlayer/

This part comes first, so that every later live test already runs under the updated liveguard.

Settings location

The new location is ~/.config/orionlayer/user_settings.json, the same base as the mod folder (Decision 72). Respect XDG_CONFIG_HOME if it is set.

One-time migration at startup

If the new file is missing and the old file in the program folder exists, copy the old file to the new location.
Never delete or modify the old file.
If both files exist, the new one wins, and a single log line notes that the old one is being ignored.

Writes

All writes go only to the new location.
Create the directory if it is missing.

liveguard

Protect the new path.
Keep protecting the old path as long as that file exists.
Add a check that both are backed up and verified.

Tests

Cover the migration: new file missing, both files present, neither file present.
Cover the XDG override.
Cover the liveguard coverage.
Part 2 — Apply Open Fix 34 (approved)

Apply and verify

Apply doc/ext_main_menu_save_slots.patch (Fix 34) to the orionlayer-local branch.
Rebuild the engine.
Live-check with liveguard:
The main menu Load dialog opens, and the slot data now arrives on the wire.
SAVE4 loads correctly.
The GAME-menu Load and Save dialogs from Fix 14 still behave as before.
While the dialog is open, log the wire message once, and store the excerpt next to the progress file as evidence.

Documentation of the engine change

Data requires this. It is part of the definition of done for this part, not optional.

Comment in the engine source. At the changed condition in src/ext/ext_api.cpp, add a short comment marking it as an OrionLayer change. It must name "Open Fix 34" and give a one-line reason, so anyone reading Joes' tree can see the change without our docs.
Engine commit. Make exactly one commit on orionlayer-local for this fix. Its message starts with OrionLayer Open Fix 34: and states what changed and why.
Fix 34 entry in doc/orion2re_open_fixes.md. Change the status to APPLIED and add:
the date of application
the orionlayer-local commit hash
the OrionLayer repo commit that records it
the exact change: file, function, and line numbers before and after, plus the diff itself (it is one condition, so include it in full)
the live-check result, with a pointer to the wire excerpt
how to revert it (git revert <hash> on orionlayer-local, then rebuild)
any side effect you observed or ruled out. In particular, check whether _screen_data can be 2 on the main menu anywhere other than the Load dialog, and write down what you found.
Applied-fixes list. Update every place in the repo that lists which fixes a fresh clone must apply to orion2re. That includes the overview line of applied fixes and any setup or rebuild instructions. After this part, a fresh clone on another machine must know it needs Fix 34.
Check that the docs match the code. The diff documented in step 3 must match the committed engine change byte for byte. Record in progress that you verified this.

If the patch no longer applies cleanly or the live check fails:

Do not improvise a different engine change.
Revert, and leave the entry at NOT APPLIED with the failure documented.
Park it for Data.
Skip Part 3, keeping the safety-net fallback, and continue with Part 4.
Part 3 — Load dialog in HD
Use the save-game data exposed by Fix 34 to draw the load dialog in the frameless HUD style (core/hud/), consistent with the other galaxy modals.
Keep the safety net for unknown modals as a fallback, so the original image is shown if the data is missing.
Live test: open the dialog, check the slot list against the actual save files, load SAVE4, and cancel back out.
If this grows beyond a clean part: ship what works behind the fallback, and park the rest with a description.
Part 4 — Remove the fourth tech level in New Game
The original offers three tech-level choices, and our HD New Game screen shows a fourth. Remove it.
Make sure the remaining choices map to the correct engine values.
Live-check that each selection starts a game with the matching level.
Part 5 — 2160p scaling fixes

Star names

At 2160p, star names on the galaxy map are drawn at twice their current size.
Scale them through the resolution factor rather than a hardcoded 2160p branch.

Select Race

Fix the overlapping text at 2160p.

Verification

Take screenshot comparisons at 1080p and 2160p for both screens, and store them next to the progress file.
1080p must not change visibly.
Part 6 — Missing icons (list from order 169)
Work through the list of missing icons from 169.
Use our own sources or generated HUD-style icons only, never MOO2 originals.
Any icon with no clean source gets a visible placeholder and a line in parked-for-data.
Icons must stay moddable through the mod folder.
Finish
Run the full suite, a fresh clone and a final liveguard check.
Push if every push condition is met.
The progress file ends with a short summary covering:
what was done per part
the new check count
the parked items
which live steps Data should look at himself
