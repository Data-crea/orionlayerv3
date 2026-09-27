# Work order 183 — progress

Unattended run, 27 September 2026, base `7d491d9` (= origin/main, 379
checks). orion2re `orionlayer-local` `2097b0c6`, its three untracked files
(`mox.set`, `racesel_custom_screen_id.patch`, `src.zip`) left alone.
Evidence root: `~/orionlayer-fixtures/evidence/work_order_183/`.

## Before part 1

- Read: `doc/v3_fundament.md` (the index), all three `principles-` parts
  (06, 07, 08) in full, and the parts this order touches: 09 (the start
  hang, the live-run file list, the engine line, the virtual display) and
  02 (decision 39's correction — the window shown before `g_hide_window`).
  Also 182's progress, parked file, virtual-display brief and entry 41.
- 17:40: no orion2re and no OrionLayer client running. **In Data's session**
  (left alone, noted): Borderlands 3 (PID 27418) playing sound on his HDMI
  sink, Steam, Firefox and Chromium — his, and the reason every audio step
  below touches only a stream this run started.

## Part 1 — apply fix 41 and document it — **DONE**

1. **Applied.** On `orionlayer-local` at `2097b0c6`:
   `patch -p1 --dry-run`, then `patch -p1` with
   `doc/ext_engine_window_hidden.patch` — both files, no offset, no fuzz;
   `ninja -C out/build/Linux/linux-debug` compiled the two files and linked
   (17:40). One commit, **`4bf152e4`** "OrionLayer Open Fix 41: keep the
   engine's own window hidden from the start" (`git add` of the two files;
   the three untracked files untouched).
   **Against 182's scratch proof, byte for byte:** the scratch clone lived
   in another session's scratchpad and is gone, but the patch file IS its
   `git diff` — and `git diff 4bf152e4~1 4bf152e4` equals the file's diff
   byte for byte, `diff --git` and `index` lines included (sha256
   `a2f8e948…` both); the post-image blobs are `88c157cd` and `3f943781`,
   the scratch commit's own.
2. **Live on Xvfb** (`:91`, every start through `tools/engine_start.py`
   with its own liveguard backup, each verified after):

   | | result |
   |---|---|
   | window (starts 29931, 30052, 30148, 30255) | **never mapped**: `xwatch` on the root from before the engine existed saw 0 maps of the engine's window and 2 of a control window per run; `xwininfo` `IsUnMapped` at READY and 20 s later |
   | start | no hang in 6 starts; READY 1.53-1.54 s, the intro skipped by the key |
   | pacing, main menu, 20 s (first 5 s left out) | 6.06/s, gap median 164.3, p95 166.4, max 166.8-167.1 ms — 182: 6.0-6.1/s, 164.8-165.2 / 166.4-166.5 / 166.7 |
   | the same WITHOUT `ORION2RE_NO_VSYNC` (30255) | 6.06/s, 164.5 / 166.5 / 167.5 ms — the hidden window alone turns VSync off |
   | flash walk, 1920, incl. the SAVE4 load (engine 30375) | 29 transitions, 0 native frames; identical to 182's unpatched and fix-41 runs on 182's comparison columns (only the gate's `held` counts differ, as between 182's own runs) |
   | colony screen + build popup, `--orders`, 1920 (engine 30611) | 23 transitions, 0 native frames, 407 colony frames agreeing, 0 disagreeing; every order's result and the table identical to 182's unpatched run |
   | guards `183_P1_start_{a,b,c,novsyncenv}`, `183_P1_flash`, `183_P1_colony` | starts: identical; the two load runs: MOX.SET's load byte (offset 21, 10 → 3), restored, verified identical |

   The first pacing figure of start a (7.2/s) counted the burst at connect;
   the script then measured the steady window, which is what the table
   gives. One run's name swallowed its flag (a shell quoting slip) and ran
   WITH the variable — kept as start c, its guard verified.
3. **Documented** as 34-40 were:
   - entry 41 **APPLIED**: date, `4bf152e4`, the OrionLayer commit (its
     hash added by Part 2's commit), file / function / lines (ext_api.cpp
     :16; platform.cpp `Present_VSync_Interval_` from :20, added 21-24;
     the show at :1410-1412, every line re-read on the committed tree), the
     full diff, the live table, the revert (`git revert` or `patch -R`,
     dry-run proved clean), and the side effects — a hidden window presents
     without VSync, and the measured pacing did not move;
   - `version_check`: 41 moved to `LOCAL_PATCHES`, `REPORTED_PATCHES`
     empty again. **A build without it is refused by name** — run on the
     whole `src/` of `2097b0c6` (`git archive`, nothing written to the
     repo): exit 1, one line, `doc/ext_engine_window_hidden.patch :
     MISSING` and "… (open fix 41) …";
   - the fresh-clone list: README's table row 14 and its bundle name,
     `setup.py`'s report (from `required_fixes`, now "… 34, 35, 36, 37, 38,
     39, 40, 41"), fundament part 09's engine line; one dated sentence each
     in part 09 (virtual display) and part 02 (decision 39's correction);
   - **the entry's diff against the commit**: the entry's diff is
     `git diff 4bf152e4~1 4bf152e4` with git's `diff --git`/`index` lines
     and the text after `@@` left out — produced from the commit, and held
     by the new check against the patch file, which is held against the
     commit;
   - **bundle** `~/orion2re_bundle_27sep_4bf152e4_fixes34-41.bundle`
     beside the others: `git bundle verify` exit 0, a clone of it has
     `4bf152e4` on top and 1164 commits, as the branch.
4. **Check 090r #4** (new): fix 41 applied and documented — required,
   status and hash in entry, summary row and patch file, two one-line
   markers, the entry's diff the file's; on a disk with the tree the
   commit's diff the file's and each marker once. 090r's old "41 is parked"
   assertions went with the state they described (in the same module).
   **Checks 379 → 380.**

**Commit gate, recorded (the hook asks for both exits):** the first
`git commit` of Part 1 was refused — the pre-commit fast tier exited
**139**, a native segfault inside CPython 3.14.7 while check 059 walked an
`ast` (`evidence/work_order_183/P1_precommit_139.log`), code this order did
not touch; the same tier run by hand at once: **exit 0**, 370 green; the
commit then went through its own hook green. Part 1 = OrionLayer
**`89ce660`**.

## Part 2 — players skip the intro, silently — **DONE: the player's start skips it; no intro audio is produced, nothing built for audio**

1. **The player's path, found.** README's quick start was two terminals:
   the orion2re binary bare in `~/Master of Orion 2`, then `python
   main.py` — **no skip**, so the logos and the 113 s intro played (and
   with fix 41 the player could not even press a key into the hidden
   window). `main.py` starts no engine (176, check 006e). Data's desktop
   launchers (`~/Schreibtisch/OrionLayer_Start.desktop`, the same file in
   `~/.local/share/applications/`, 3 August) run `cd ~/orionlayer &&
   ./launcher.sh edit main_menu` — a folder that no longer exists, so they
   start nothing; they are his files outside the tree and were not touched
   (parked, with the line that would work).
   **Now: `python play.py`** (new, root): the engine through
   `tools/engine_start.start` — THE function every live tool starts it
   with, so the skip is the tools' by construction, not a copy — with
   `real_desktop="player start (play.py)"` (the player's display and audio;
   the tools' virtual display plays no sound), no guard, no idle
   inhibitor; after READY `main.py` in the player's own environment (the
   tools' forced drivers stripped); and the engine stopped when OrionLayer
   ends — since fix 41 a leftover engine would be invisible, hold the port
   and could keep playing music. It stops only the engine its own start
   returned; with somebody else's engine running it refuses, as
   `engine_start` does. README's quick start and CLAUDE.md now open with
   it; the by-hand way stays, saying the intro then plays out.
   **Live, on the virtual display** (only the display redirected by a
   scratch driver: engine on Xvfb, client on dummy drivers; guards
   `183_P2_play_virtual{,_b}` clean): INTRO SKIPPED, READY, `main.py` at
   game screen 10 → HD `main_menu`, "no native frame", no key pressed;
   OrionLayer ended → `orion2re PID 42781 stopped (SIGTERM)`.
   **Found on the way:** the first version reported "did not stop;
   SIGKILL" for an engine that had ended within a second — an exited
   child stays a zombie that `kill(pid, 0)` still finds. It reaps now
   (`play.gone`); timed separately: the engine exits 1.0 s after SIGTERM,
   with and without a client having been connected.
   **Check 090v** (new): `play.py` starts through `engine_start.start`
   with the skip on, `real_desktop` set, no guard, no inhibitor; its client
   env carries none of the tools' forcing; a real stand-in child is stopped
   by SIGTERM and reaped; an already-ended engine is left alone; a refused
   start signals nothing; `play.py` imports no skip and sends no key of its
   own; README's quick start opens with `python play.py`.
2. **Measured, without Data hearing it** (`evidence/work_order_183/
   P2_audio/`): a private null sink (`pactl load-module
   module-null-sink sink_name=ol183_measure`, the default sink checked
   unchanged), the engine on the virtual display with its NORMAL driver
   (`SDL_AUDIODRIVER` unset → `pipewire`, in its log), its stream sent
   there by `PIPEWIRE_NODE`. SDL sets `target.object` to the default sink
   itself (SDL_pipewire.c:1201-1205), so the override was proved first
   with a stream of **pure silence** (linked only to the null sink; Data's
   game stream stayed on HDMI), then a −20 dBFS tone recorded at −23.0
   dBFS RMS (a sine's −3 dB) — the recorder hears what plays there. Every
   engine run had a watchdog that would kill it the moment any of its
   streams linked anywhere else: none did.
   **The trap:** the first control (the intro allowed to play) recorded
   pure digital silence for 126 s, intro and menu music alike — the
   engine's stream was **muted at 0 %**: WirePlumber restores stream
   volume by application name, and Data's state stores `orion2re` muted
   (`~/.local/state/wireplumber/stream-properties` line 88). Not set by
   any session (the only pactl/wpctl calls in any transcript are this
   run's); his setting, **left alone** (parked). So the measurement runs
   the engine as `SDL_APP_NAME=orion2re-183-measure`:

   | run | before READY (engine start → READY) | after READY (1-6 s) |
   |---|---|---|
   | control, intro allowed (PID 39313) | **108.0 s of sound**, from 5.0 s on (the logos are silent), peak −7.8 dBFS, RMS −16.1 dBFS; READY at 113.0 s | music, RMS −26.0 dBFS |
   | skip 1 / 2 / 3 (the tools' key) | **nothing**: 0 windows above −60 dBFS, digital silence (−120 dBFS), before the main menu's music is requested (0.08 s); READY in the log at 0.09 s | music from ≥ 0.25 s after the launch, RMS −18.4 / −18.4 / −18.8 dBFS |

   (50 ms windows; the music track is random per start, `clock() % 3`,
   jim.cpp — hence −26 against −18.) With the key, the logos end at once
   and the intro is never played (jim.cpp:150-152); the key arrives at
   ~0.06 s, and the first intro sound would come at 5.0 s.
3. **Intro audio is produced only without the skip**, and the player's
   start now skips — so, by the order's rule 4, **nothing was built for
   audio**: no mute, no engine change, no new open fix. What a player
   hears: nothing of the intro; the main menu's music, as ever — on THIS
   machine not even that, while `orion2re` is stored muted.
4. **The recording method for Part 3**, validated here in the null sink
   (runs `X_measure`, `X_ownname`): on Data's real output path his game
   plays too, so a sink monitor cannot isolate the engine. A recorder that
   links to nothing by itself (`node.autoconnect = false`,
   `node.dont-fallback = true` — never a microphone) is linked by name to
   the engine stream's own output ports, re-linked every 20 ms. With the
   measurement name it recorded the music at the monitor's level
   (−26/−27 dBFS, the same profile), linked 0.15 s after the launch —
   before any sound; with the engine's own name, silence on both (his
   stored mute acts before the ports). Two tries that failed first, kept
   because they would fail again: links made before the stream starts
   playing are left on ports it replaces (recorded silence under a
   −19 dBFS monitor), and a `pw-record` targeting the stream by name is
   never linked at all.
5. **Left as found**: the null sink unloaded (`pactl list sinks` has no
   `ol183_measure`), the default sink unchanged, Data's game stream at
   61 % unmuted before and after, the `orion2re` row unchanged. WirePlumber
   caches a row for every stream it sees — this run added rows for
   `ol183_measure`, `pw-record` and `orion2re-183-measure`, beside dozens
   of earlier tools' rows; nothing reads them but WirePlumber's own restore.
   Every engine guard clean (`183_A_*`, `183_B_*`, `183_C_skip_{1,2,3}`,
   `183_D1`, `183_V_*`, `183_W_*`, `183_X_*`, `183_P2_*`).
6. **Documented**: fundament part 09 (the intro's sound, the stored-mute
   trap, the capture), entry 41's intro paragraph and its OrionLayer hash
   (`89ce660`, held by 090r), README, CLAUDE.md, the status document.

**Suite, recorded:** two full runs exited **139** — native segfaults in
numpy's `_multiarray_umath` (check 006f in `core/hud/glass.py`, then in
`core/hud/blocks.py`), before 090v runs and in code this order did not
touch (`evidence/work_order_183/P2_suite_139{,b}.log`); the third: **exit
0, 381 green**. Parked with what `coredumpctl` shows.
090v shown red on its own (`python -B`, the suite's namespace stood in):
`play.py` changed to pass `intro=True` → "the player's start must skip the
intro"; restored, caches cleared, green. Full suite after the docs: **exit
0, 381 green**.
**Checks 380 → 381** (090v).

Part 2 = OrionLayer **`6260aae`**.

## Part 3 — acceptance on Data's real desktop — **DONE: no engine window, the HD main menu without a key, nothing of the intro audible**

`--real-desktop` reason, as ordered: **"Fix 41 acceptance: the engine window
must not appear in a real session"**. Before it (18:47): Borderlands 3 had
ended, no audio stream played on the system, no engine or client ran, the
screen was awake (idle 91 ms — Data at the desk). `play.main` exactly as a
player runs it — the only changes, by a scratch driver: this reason, and a
liveguard backup taken first.

**Your screen was in use: 18:48:15-18:48:42 (27 s; OrionLayer's window for
23 s of it) and 18:50:00-18:50:09 (9 s; OrionLayer's window 5 s, and a
1 x 1 pixel control window for 0.3 s at 18:50:01).** Two runs, because the
first left three things unproved (below).

| | run 1, 18:48:15 (engine 55735, client 55852) | run 2, 18:50:00 (engine 58538, client 58671) |
|---|---|---|
| the start | `REAL DESKTOP (engine): <reason>`; INTRO SKIPPED at 1.56 s, logos drawn 1.57, READY (log) 1.58 | skip 2.11 s, logos drawn 2.15, READY (log) 2.17 |
| the engine's window on `:0` (`xwatch` on the root from before the engine existed; only our PIDs' events kept, the raw file deleted — it names Data's windows) | **0 maps**, never in the client lists | **0 maps**, never in the client lists; `xwininfo` **IsUnMapped** in all 25 polls (window `60817467`) |
| the watcher sees a map at all (control) | — not shown (OrionLayer's window is Wayland) | **yes**: a 1 x 1 X window, 2 map events |
| HD main menu without a key | `HD draws: main_menu, game screen 10` 0.5 s after OrionLayer started | the same, 0.6 s after; "no native frame" |
| the first screen changes | — | `n` then ESC to the engine's own (hidden) window, as the skip is sent: HD `new_game` (screen 13) at 5.7 s, back to `main_menu` at 7.2 s — still 0 maps |
| the engine's own stream on the real output path (HDMI), captured from before the music (1.61 s / 2.18 s) | **0 non-zero samples in 24.4 s** | **0 non-zero samples in 6.2 s**; the stream `mute: true`, 0 % — Data's stored setting |
| the end | OrionLayer ended (terminated after its 15 s wait), `orion2re PID 55735 stopped (SIGTERM)` | OrionLayer ended by SIGTERM, exit 0; `stopped (SIGTERM)` |
| after | no engine, no client; guard `183_P3_real` identical | no engine, no client; guard `183_P3_real2` identical |

**What run 1 could not show**, and why there was a run 2: OrionLayer's
window is a native **Wayland** window for a player (`play.py` hands the
client the player's own environment, and pygame picks `wayland` in this
session), so X tools neither see it map nor send it keys — run 1 therefore
had no positive control for the watcher on `:0`, no screen change and no
screenshot. The ENGINE is an X11 client of Xwayland (its SDL uses x11 on
this machine, CLAUDE.md), so any appearance of ITS window is an X map on
`:0` — which run 2's control proves the watcher sees. Screenshots of
OrionLayer's window were not taken: X cannot capture a Wayland window, and
a screenshot of the whole screen would be Data's desktop. The HD evidence
is the client's own log.

**Nothing of the intro is audible, for two independent reasons:** the
engine produces none once the key is sent (Part 2, measured), and on this
machine the engine's whole stream is stored muted — the capture of what it
hands the HDMI sink is exact zeros. Data's settings unchanged after both
runs (his stored `orion2re` row, the default sink).
