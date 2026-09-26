# Work order 174 — progress

Unattended run, 26 September 2026. Glass instead of black on every
screen, a glass slider, and the live test of 167-173. Builds on 169-173
(decisions 71, 72). Parts in the order's order: A, B, C.

Evidence root: `~/orionlayer-fixtures/evidence/work_order_174/`.

## Precondition — checked at the start

`ps -C orion2re`: no engine running. No OrionLayer client (`main.py`)
running. Port 17362: nobody listening. Data's engine from 173 (PID
287200) is gone. So A and C may start an engine of this run.

The mockup is at `~/Downloads/ChatGPT Image Sep 26, 2026, 06_07_07 AM.png`
(spaces and commas where the order has underscores; 1683 x 935, sha256
`80f7b6e2...`) — the only file of that time stamp.

## Part A — the start hang — **EXPLAINED; the fix is in orion2re (patch, not applied); our side detects and restarts**

Saves hashed before any engine started (`saves_before.sha256`).

**1. Started as the protocol says** (DISPLAY :0, the newest mutter auth
file, `SDL_VIDEODRIVER=x11`, `cd "$HOME/Master of Orion 2"`, `nohup`):
at 06:20 it ran cleanly to `ext: server started` (`engine_start1.log`).
The window "Orion2 Redone" was mapped and viewable. A second start with
the window minimised during the logos: clean too.

**2. It did hang, intermittently.** The new start tool's first run hung
at the old place (`engine_start3_tool.log`); alternating runs showed it
has nothing to do with the tool: 2 of 7 starts hung, with and without an
idle inhibitor, the screen on each time (idle 2-1403 ms).

**3. Where it waits — backtraces** (a start with ptrace allowed by the
child, `prctl(PR_SET_PTRACER)`, gdb attached only after a hang;
`hang_backtrace_6.txt`, `_9.txt`): the main thread in
`SDL_RenderPresent` → the NVIDIA GLX swap (driver 615.71.09) →
`drmSyncobjTimelineWait`; the game thread in `JIM::Draw_Logos_` →
`palstore::Slow_Fade_In_` → `video::Submit_Palette_`, in
`SDL_WaitCondition(..., timeoutNS=-1)`, waiting for that present. VSync
is on (platform.cpp:644, :1390). `SDL_LogInfo` writes unbuffered to
stderr, so "data space allocated" really is the last thing done
(mox2.cpp:299, then `Draw_Logos_` at :302). Under gdb from the start it
never hung (0 of 6): the fault is timing-sensitive. `_8.txt` is NOT a
hang — the intro cinematic playing (`Play_Cinematic_`, jim.cpp:151),
which holds the log at the same line; the tool tells the two apart only
by the threads' waits over several samples.

**4. When — what was running.** At 06:21:53 Data launched Borderlands 3
full-screen (3440x1440, focused, covering the monitor; journal and
`_NET_CLIENT_LIST_STACKING`). The one clean start before that was at
06:20; every later series ran behind the game. On 25 September (169)
the engine was started at 18:39:57, nine and a half minutes after
Data's last input in that session, with GNOME set to blank and lock
after 300 s idle (`idle-delay 300`, `lock-delay 0`) — the journal logs
no lock events, so that one is circumstantial. Data's engine at 19:00
started with him at the screen. An engine that DID come up behind the
game runs, throttled: 19-35 state snapshots in 6 s to a client of this
run.

**5. One change at a time** (`hangstat_r1..r4.json`; a "GPU-HANG" is the
signature, not a timeout):

| change | starts | hangs |
|---|---:|---:|
| none — Data's build, the protocol's command (three series) | 60 | 8 |
| an idle inhibitor / no inhibitor / a new session / nohup | 7 | 2 |
| `__NV_DISABLE_EXPLICIT_SYNC=1` | 40 (+12 with gdb armed) | hangs moved to `xcb_wait_for_special_event` (2 caught) |
| `SDL_RENDER_DRIVER=software` | 20 | 6 |
| `SDL_RENDER_DRIVER=vulkan` | 20 (+20 with gdb armed) | hangs moved to `VULKAN_AcquireNextSwapchainImage` (2 caught) |
| scratch build of e6199966, unpatched | 20 | 1 |
| scratch build with `ORION2RE_NO_VSYNC=1` (the patch) | 50 | **0** |

**The change that did it: not waiting for VSync** — which needs
orion2re. **Cause and fix belong to orion2re** (patch rule): open fix
31 in `doc/orion2re_open_fixes.md`, `doc/ext_present_no_vsync.patch`
(an `ORION2RE_EXT`-gated `ORION2RE_NO_VSYNC=1`; default unchanged),
`patch --dry-run` clean against Data's tree, built and run only in a
scratch copy (`git archive` plus `vendors/`; Data's tree untouched).
**NOT APPLIED — parked A1.**

**Our side** — `tools/engine_start.py`, the one way a live run starts
the engine now: sets `ORION2RE_NO_VSYNC=1` (ignored until the patch is
in), refuses on a locked screen / a taken port / an engine that is not
ours (found by binding, never connecting), runs under an idle
inhibitor, recognises the hang by its signature and starts again,
stopping only its own PID. Shown working: 10 runs, one of which met the
hang twice and came up on the third start (`engine_retry_*.log`). A
check holds its decisions offline (006e). Recorded in fundament part 09
beside the protocol; CLAUDE.md's "cause open" paragraph now says what
was found. Every engine started for A was stopped by its PID; none of
Data's processes was touched.
