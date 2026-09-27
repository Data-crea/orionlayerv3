# Work Order — OrionLayer v3

**Number:** next free (expected 183)
**Base:** main = origin/main = 7d491d9, suite green (379 checks). orion2re `orionlayer-local` = 2097b0c6 (Fixes 34–40 applied).
**Mode:** Unattended run, with no questions to Data. Anything that needs his decision goes into `<n>-parked-for-data.md` together with the default you chose, and the run continues on that default. Record progress in `<n>-progress.md` after every part. Make one commit per part.

## What Data decided

- Data approves **Open Fix 41**, which keeps the engine's own window hidden from the start, exactly as proven in 182.
- He also decided that the original intro is not important. For players, the intro is skipped exactly as it already is in the tests, and the player lands directly in the HD main menu.
- Nothing of the intro may be heard.

## Standing rules

**Before you start**
- Read `doc/v3_fundament.md` first, then the parts this order touches, and always all of the `principles-` parts.

**Live tests**
- Run live tests on the virtual display (Xvfb, from 182).
- Use the real desktop only through `--real-desktop` with a reason, and only where this order asks for it (Part 3).
- Run `tools/liveguard.py` before every live step, and check with it afterwards.
- Only the scratch slots SAVE4 and SAVE5 may be written. Never SAVE8.
- Exactly one client may be connected to the server at a time.

**Foreign engines and clients**
- Engines and clients running in Data's real session are his. Leave them alone and note them in progress.

**Engine patches**
- Only Fix 41 may be applied.
- Any other engine change you find necessary is written as a new open fix (next free number), with a patch file, proof that it applies with no offset or fuzz and compiles, and a misspelt-constant control. It is parked, not applied.
- Every changed place carries `OrionLayer, open fix <N>.` on a single line.
- orion2re stays local and is never pushed.

**Originals**
- MOO2 original files are never copied anywhere.

**Push**
- Push only when all of these are green: the suite, a fresh clone, liveguard, and the flash check. No live step may be broken by this order. No force push.
- If a condition fails, commit locally without pushing, and record the reason.

## Part 1 — Apply Fix 41 and document it

**Apply**
- Apply the Fix 41 patch named in its entry in `doc/orion2re_open_fixes.md` to `orionlayer-local`.
  1. Run `patch -p1 --dry-run`, then `patch -p1`, with no offset and no fuzz.
  2. Rebuild with `ninja -C out/build/Linux/linux-debug`.
- Make one commit on `orionlayer-local`. Its message starts with `OrionLayer Open Fix 41:`.
- The commit must match the 182 scratch proof byte for byte. Record that you checked this.

**Live checks on Xvfb, with liveguard**
- The engine window is never mapped.
- There is no VSync hang at start, and the frame pacing is unchanged against the 182 measurement.
- The flash check, one save load, the colony screen and the build popup all behave as in 182.

**Documentation**

Data requires this for every engine change. It is part of the definition of done, and the model is how Fixes 34–40 were documented.

1. **Entry 41 set to `APPLIED`**, recording:
   - the date
   - the `orionlayer-local` commit hash
   - the OrionLayer commit
   - file, function and line numbers, with the full diff
   - the live result
   - how to revert it
   - the observed side effects, in particular that a hidden window presents without VSync, and what the measured pacing showed
2. **version_check:** move 41 to `LOCAL_PATCHES`. A build without it must be reported by name.
3. **Fresh-clone list:** the README, the `setup.py` output and the overview line in fundament part 09 now name Fixes 34–41.
4. **Docs against commit:** the diff in the entry must match the commit byte for byte. Record that you verified this.
5. **Bundle:** write a new bundle of `orionlayer-local` next to the earlier ones, named to show it holds Fixes 34–41, and verify it with `git bundle verify`.

**If Fix 41 fails**
- Revert it and rebuild.
- Document the failure in the entry and park it.
- Skip Part 3's window check, and continue with Part 2.

## Part 2 — Players skip the intro, silently

**1. Intro skip in the player path**
- Find the path a player uses to start OrionLayer. It may or may not be the same `engine_start` the tools use.
- Make sure that path sends the intro skip exactly as the tools do. The player must land in the HD main menu without any key press of his own.
- Record which path it is, and that the tool path and the player path now behave the same.

**2. Measure whether any intro sound is heard**

Do this without Data hearing it. For example:
- route the engine's audio stream into a PipeWire null sink and record it with `pw-record`, or
- record from the monitor of a sink that is not his output.

Measure on a normal start with the real audio driver, not SDL's dummy driver. Record:
- whether any intro audio is produced between engine start and READY
- how long it lasts
- how loud it is

**3. If intro audio is produced, keep it silent until READY**
- Prefer a client-side solution with no engine change. For example:
  - mute only the engine's own stream through PipeWire (`wpctl` / `pactl`) from start until READY, then unmute it, or
  - start the engine so its audio opens only after READY.
- The game's own music and sounds after READY must be unaffected. Prove it with a recording: they are present after READY at the same level as without the mute.
- The mute must never stay on if something goes wrong. If READY never arrives, or the client crashes, the engine's stream must not remain muted for the next session. Add a check for that.
- Any other audio stream on Data's system, such as his music or a browser, must never be touched. Add a check that the mute addresses only the engine's own stream.
- If this cannot be solved client-side, write it as a new open fix, prove it in a scratch build, and park it. Record exactly what the player would hear until then.

**4. If no intro audio is produced**, record the measurement and build nothing.

## Part 3 — Acceptance on Data's real desktop

This is the one place where `--real-desktop` is required. Use it with the reason "Fix 41 acceptance: the engine window must not appear in a real session".

- Run one normal player start in Data's real session, with liveguard.
- Confirm that no engine window appears at any time, including during startup, the intro skip and the first screen changes.
- Confirm that the HD main menu appears without any key press.
- Confirm that nothing of the intro is audible. Use the recording method from Part 2 on the real output path, not Data's ears.
- Keep it short, then close everything.
- Record the time the run took in progress, so Data knows when his screen was in use.

## Finish

- Run the full suite, a fresh clone (setup must name Fixes 34–41), the flash check, and a final liveguard check.
- Push if every condition is met.

**The progress file ends with a summary covering:**
- Fix 41: applied or not, both commit hashes, documented yes/no
- the player start path, and the intro skip in it
- the audio measurement, and what was done about it
- the new check count

**Parked-for-data:**
- a proposed decision text: "Players skip the original intro; the engine window stays hidden from the start". Leave the number free for Data.
- any new open fix
- everything else

**List the live steps Data should look at himself.** At minimum:
- a normal start of the game on his desktop: no engine window, straight into the HD main menu, no intro sound
