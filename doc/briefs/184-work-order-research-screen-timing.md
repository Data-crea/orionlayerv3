# Work Order — OrionLayer v3

**Number:** next free (expected 184)
**Base:** main = origin/main = 5b24070, suite green (381 checks). orion2re `orionlayer-local` = 4bf152e4 (Fixes 34–41 applied).
**Mode:** Unattended run with no questions to Data. Anything that needs his decision goes into `<n>-parked-for-data.md` together with the default you chose, and the run continues on that default. Record progress in `<n>-progress.md` after every part. Make one commit per part.

**Task:** Data finds that opening the research screen takes noticeably long. Find out where the time goes, and make it faster wherever that is possible without changing what the player sees.

This order measures first and optimises second. A speed-up that is not backed by a before-and-after measurement does not count.

## Standing rules

**Before you start**
- Read `doc/v3_fundament.md` first, then the parts this order touches, and always all of the `principles-` parts.

**Live tests**
- Run live tests on the virtual display (Xvfb).
- The real desktop is allowed only through `--real-desktop` with a reason, and only for the short measurement in Part 1.3.
- Run `tools/liveguard.py` before every live step and check with it afterwards.
- Only the scratch slots SAVE4 and SAVE5 may be written. Never write SAVE8.
- Exactly one client may be connected to the server at a time.

**Fix 41 as it stands**
- Data decided to leave Fix 41 as it is for now: the original without OrionLayer, and F12 to the original, do not work.
- Do not change that, and do not count it as a fault of this order.

**Engine patches**
- No engine patch may be applied.
- If the measurement shows that the time is lost in the engine or on the wire, write the change as a new open fix (next free number). It needs:
  - a patch file
  - proof that it applies with no offset or fuzz and compiles
  - a misspelt-constant control
  - `OrionLayer, open fix <N>.` on a single line at every changed place
- Park it for Data's approval.

**What must not change**
- The research screen must look exactly as it does today. Renders at 1920, 2576 and 3840 must be pixel-identical before and after.
- If a difference is unavoidable, name it and explain it.
- The flash rule from 180 stays intact: no native frame, and no input to a screen the player cannot see.

**Originals**
- MOO2 original files are never copied anywhere.

**Push**
- Push only when the suite, a fresh clone, liveguard and the flash check are all green, and no live step is broken by this order. No force push.
- If a condition fails, commit locally without pushing, and record the reason.

## Part 1 — Measure where the time goes

**1. Instrumentation**

Add timing points, behind a debug flag, so they cost nothing in normal play. Measure the path from the player's click or key that opens research to the first HD frame of the research screen, split into:

- (a) the click or key being sent to the engine
- (b) the engine switching screens, up to the first snapshot with the research screen's ID
- (c) the handover hold (180) waiting until every data block the research screen needs has arrived. Record how many snapshots that took, and at what snapshot rate.
- (d) HD-side preparation on first entry and on later entries, separately. This covers asset and font loading, text layout, help and LBX-derived data, surface creation, and caches being built.
- (e) drawing the first frame

**2. Measurements on Xvfb**

Take the measurements at 1920, 2576 and 3840, on SAVE4:
- 20 entries per resolution, reached from the galaxy map
- the first entry after start measured on its own, then the following entries
- where they exist in the scratch save, the other ways into research as well, such as the turn-start research prompt. Use **no** ACTIVATE_FIELD on the research choice rows (open fix 23, SIGSEGV). Only the player's own click on a row, read from the current field list, is allowed.

Record median, maximum, and the share of each phase (a)–(e).

Use `cProfile` or an equivalent for phase (d), and name the ten most expensive calls.

**3. Short control on Data's real desktop**

Xvfb renders without a GPU, so its times can differ from what Data sees.
- Run 10 entries at his window size, with `--real-desktop` and the reason "research-screen timing on the real display".
- Keep it short, and record its time window in progress.
- If the phase shares differ materially from Xvfb, say so. The real desktop is what counts for Data.

**4. Comparison with the original**

Measure how long the engine itself needs to show its native research screen (phase b alone). That is the floor HD cannot go below without an engine change.

**5. Findings**

Write the findings to `doc/briefs/<n>-research-timing.md`:
- a table of the phases
- where the time actually goes
- which part of it OrionLayer can influence, and which part is the engine's

Commit the instrumentation and the findings.

## Part 2 — Make it faster, where the measurement says it pays

Only address phases that carry a relevant share of the time.

**HD side (d, e).** Candidates include the following, and the measurement decides which of them apply:
- preparing the research screen's static parts once, at startup or in idle time, instead of on first entry
- caching rendered text, surfaces and layout between entries
- avoiding repeated file reads or decoding
- avoiding recomputation of anything that does not depend on the current snapshot

A cache must be invalidated correctly on:
- a change of resolution or window size
- F5 layout edits
- mod-folder changes
- frame colour or panel glass changes
- language or text-resolver changes

Each of these needs a check. Startup time must not get noticeably worse. Measure it and record it.

**Handover wait (c).**
- If the hold waits for more snapshots than necessary, find out why. For example, a block arriving one tick later than the screen ID, or a condition requiring data the research screen does not need for its first frame.
- Tighten the condition only if it still guarantees a complete, correct first frame.
- The flash check and the stress test from 182 must stay green.

**Engine side (b), and the snapshot rate.**
- If the time is lost here, for example because the snapshot rate of about 6 per second makes the screen's first block arrive late, then do not change the engine.
- Write the smallest useful change as an open fix and prove it in a scratch build, with the gain measured.
- Park it for Data, together with its cost and its risk.
- Name the risks in particular: a higher snapshot rate touches every screen, the CPU load, and the pacing measured in 182 and 183.

**For every change**
- Measure before and after, with the same method as Part 1.
- Renders at 1920, 2576 and 3840 must be pixel-identical.
- Add a check that holds the gain in a robust form. For example: the research screen's first entry does not rebuild a given static part, or its preparation is served from the cache on the second entry. No fragile timing threshold.

## Finish

- Run the full suite, a fresh clone, the flash check and a final liveguard check.
- Push if every condition is met.

**The progress file ends with a summary covering:**
- time to the first research frame before and after, as median and maximum, per resolution, for the first entry and for later entries, on Xvfb and on the real desktop
- what was changed, and the gain from each change
- what is left, and whose it is: the engine's, the wire's, or ours
- the new check count

**Parked-for-data:**
- any open fix, with its measured gain, cost and risk
- everything else

**Live steps Data should look at himself:**
- open research several times from the galaxy map in his own window
- the first time after start, and again afterwards
