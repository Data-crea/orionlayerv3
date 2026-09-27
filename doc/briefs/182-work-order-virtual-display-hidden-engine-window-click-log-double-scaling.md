# Work Order — OrionLayer v3

**Number:** next free (expected 182)
**Base:** main = origin/main = 5c5d670, suite green (375 checks). orion2re `orionlayer-local` = 2097b0c6 (Fixes 34–40 applied).
**Mode:** Unattended run with no questions to Data. Anything that needs his decision goes into `<n>-parked-for-data.md` together with the default you chose, and the run continues on that default. Record progress in `<n>-progress.md` after every part. Make one commit per part.

This order has four parts. Part 1 comes first, because every live step after it runs on the virtual display.

1. Live tests move to a virtual display, so that Data's desktop no longer shows the game during runs.
2. A new open fix that keeps the engine's own window hidden. It is written and proven here, not applied.
3. A click log and a stress test for the lost Cancel click from 181.
4. The remaining double-scaling faults, together with a check that catches the fault in general.

## Standing rules

**Before you start**
- Read `doc/v3_fundament.md` first, then the parts this order touches, and always all of the `principles-` parts.

**Live tests**
- Run `tools/liveguard.py` before every live step and check with it afterwards.
- Only the scratch slots SAVE4 and SAVE5 may be written. Never write to SAVE8.
- Exactly one client may be connected to the server at a time.

**Foreign engines and clients**
- Data is not playing. You may close engines and clients you did not start: run liveguard first, send SIGTERM, and use SIGKILL only if needed.
- Engines and clients running inside Data's real session are his. Once Part 1 is done, you never need to touch his session. Leave anything running there alone and note it in progress.

**Engine patches**
- orion2re stays local and is never pushed.
- No engine patch may be applied in this order.
- A new engine change is written as follows:
  - an entry in `doc/orion2re_open_fixes.md` (next free number, expected 41) with the structure of entries 34–40
  - a patch file under `doc/`
  - proof that it applies with no offset or fuzz and compiles with the engine's flags
  - a misspelt-constant control that is refused
- Every changed place carries a comment `OrionLayer, open fix <N>.` on a single line, so that grep finds it.
- Then park it for Data's approval.

**Colony screen**
- CRUNCH, TOGGLE and the full-screen field [0] are never activated.

**Originals**
- MOO2 original files are never copied anywhere.

**Push**
- Push only when the suite, a fresh clone, liveguard and the flash check are all green, and no live step is broken by this order. No force push.
- If a condition fails, commit locally without pushing, and record the reason.

## Part 1 — Live tests on a virtual display

**Why:** Data works at the same desktop while live runs happen. Today the game opens in front of him, and he has to push it away. That disturbs his work, and his clicks and focus changes can land between the test's inputs, so the results can no longer be trusted. After this part, a live run must be invisible in his session.

**1. Measure the options on this machine (CachyOS)**

Candidates include:
- a headless Wayland compositor (for example `kwin_wayland --virtual`, or `weston` with its headless backend)
- a virtual X display (Xvfb or Xwayland rootless on its own display)

For each candidate, determine:
- whether the engine (SDL) and the HD client (pygame) both start and render in it
- whether VSync and the frame pacing behave. Remember Fix 31, the VSync startup hang.
- whether the existing screenshot and input tools work in it. If they do not, find what does.
- whether the intro skip reaches the engine window there

Record the results in a table in `doc/briefs/<n>-virtual-display.md`.

**2. Proof of equivalence**

Pick the best working option and run the same live steps on it and on the real desktop:
- the recorded flash transitions, a sample of them at 1920 and at 2576
- the colony screen and the build popup from 181
- one save load

The results must match:
- the same native-frame count (zero)
- the same wire values
- the same HD frames, pixel-identical or with any difference explained

If they do not match, do not switch over. Record why, and go to step 4.

**3. Switch over**

- Every tool that starts an engine or client for a live step starts it on the virtual display by default. That includes liveguard-wrapped runs, engine_start in test mode, and the replay and comparison tools.
- Running on the real desktop remains possible only through an explicit flag, and progress must name the reason whenever it is used.
- A smoke check fails if a live tool would open a window in the user's session without that flag.
- Update the live-test protocol in the fundament.

**4. Fallback, only if no option passes step 2**

- Windows open without taking focus.
- Live runs wait until the desktop has been idle for five minutes.
- Park the reasons why no virtual display worked.

## Part 2 — Keep the engine's own window hidden (new open fix)

**Why:** OrionLayer draws everything, so the engine's window should never be seen. The decisions record that it is shown anyway, because `SDL_ShowWindow` runs before `g_hide_window` is set. Every player would see this after the release.

**1. Read the source**

- Find exactly where the window is created, shown and hidden.
- Record every other place that depends on the window being visible. Among these:
  - VSync and frame pacing (Fix 31)
  - input
  - the intro skip, which today sends a space key to this window

**2. Write the fix**

The smallest change that keeps the window hidden from the start, for example setting the flag before showing the window, or creating it hidden. Write it as the next open fix, following the standing rule, and park it.

**3. Prove it in a scratch build**

Never on `orionlayer-local`. In the scratch build:
- The engine window never appears. Check this on a real session and on the virtual display.
- The engine starts without the VSync hang, and frame pacing is unchanged.
- The HD client works as before: flash check, a save load, the colony screen.
- The intro can still be skipped.

If the space key cannot reach a hidden window, find another route, such as a key through the existing input path or an API command. If that route needs its own engine change, it goes into the same open fix. Prepare the client side of that route, but keep it inactive until the fix is applied. Without the fix, today's behaviour stays.

Record the results in the entry.

## Part 3 — Click log and stress test

**Background:** In 181, one Cancel click in the build popup at 3840 was lost, in a frame where the engine had sent an empty field list. Data was using the desktop at that time and may have clicked himself. So the likeliest cause is outside interference. The other candidate is the input drop during a handover hold from 180.

**1. Click log**

For every mouse click and key press the HD client receives, record:
- time and screen ID
- whether HD sent it to the engine, or dropped it, and if dropped, why: handover hold, no field under the cursor, a modal, and so on
- the frame's field count

Keep the log behind a debug flag, so it costs nothing in normal play.

**2. Stress test on the virtual display**

For each resolution — 1920, 2576 and 3840 — and on SAVE4 or SAVE5:
- 200 cycles of: open the build popup, then Cancel
- 100 cycles of: open the colony screen, then `<`, `>`, then back to the galaxy
- 100 cycles of: open Fleets, then back

After every cycle, check that the expected screen was reached. Evaluate the log.

**3. Evaluation**

For every lost input, give its cause from the log.

**If inputs are dropped during a hold that was not needed** — for example, a single empty field list on an already-open screen:
- Fix the handover gate, so that a screen that is already shown does not re-enter the hold because of one empty frame.
- Keep the 180 rule intact: no native frame, and no input to a screen the player cannot see.

**If nothing is lost**, record that. The 181 case then counts as external interference, and the log stays as a debug tool.

Add a smoke check that holds whatever rule you arrive at.

## Part 4 — Remaining double scaling

**Background:** In 179, the star names and Select Race had the resolution factor applied twice (4× instead of 2× at 2160p). The same fault is known in Custom Race and Empire Identity. Earlier briefs also list boxes on further screens with doubled scaling at 2160p.

**1. Find all of them**

Search the code for every place where the resolution factor can be applied twice. Do not limit the search to the known screens. Record the list with screen, element and cause.

**2. Fix them**

- Each element scales exactly once, following the same pattern as the 179 fix.
- 1080p renders must stay pixel-identical. Prove it with a before-and-after comparison for every affected screen.

**3. General check**

Add a check that detects double scaling in general, not screen by screen. Two possible approaches:
- render every registered screen at 1920 and 3840, and compare element sizes against the expected factor
- a static check on the scaling calls

Choose whichever catches the fault reliably, and explain the choice.

**4. Evidence**

Put native and HD side by side at 1920, 2576 and 3840 for every changed screen.

Note for Data: at his 2576×1432 window, the affected elements become smaller, exactly as in 179. That is the correct proportional size. List the screens where he will notice it.

## Finish

- Run the full suite, a fresh clone, the flash check and a final liveguard check. Push if all conditions are met.

**The progress file ends with a summary covering:**
- which virtual display is now in use, and the equivalence result
- the open fix for the engine window: number, what it changes, the scratch results, and how the intro skip works with it
- the stress-test result per resolution, with the cause of every lost input
- the double-scaling list, and what was fixed
- the new check count

**Parked-for-data, ordered by importance:**
1. the new open fix for approval
2. anything about the virtual display that Data must know or decide
3. everything else

**List the live steps Data should look at himself.** At minimum:
- that a live run no longer shows anything on his desktop
- the smaller elements at 2576
