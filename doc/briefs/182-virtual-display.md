# Work order 182, part 1 — live tests on a virtual display

27 September 2026, this machine (CachyOS, GNOME/mutter 50.4 on Wayland,
NVIDIA + AMD). Nothing was installed: only what is on the machine was
measured (Data's system configuration is not ours to change).

## What is on the machine

| candidate | present | measured |
|---|---|---|
| `kwin_wayland --virtual` | no (KDE's window-system library only) | — |
| `weston` headless backend | no | — |
| `cage`, `sway` (wlroots headless) | no | — |
| **Xvfb** (`xorg-server-xvfb` 21.1.24) | yes | **A** |
| **`mutter --headless --virtual-monitor`** (mutter 50.4) with its own Xwayland | yes | **B** |
| Xwayland `-rootless` on its own display | yes, but rootless Xwayland needs a compositor — Data's gnome-shell (its windows then appear on his desktop) or B's; on its own it is not a candidate | — |

## The two candidates, measured

| question | A: Xvfb `:91` (1920x1080x24, llvmpipe GL) | B: `mutter --headless` in its own D-Bus session (Xwayland `:2`, NVIDIA via gbm) |
|---|---|---|
| engine (SDL x11) starts and renders | yes — `ext: server started`; the main menu in the window (`import`) | yes — the same |
| HD client (pygame) | yes — x11 driver, a 1920x1080 window drawn and read back; live tools use SDL's dummy driver anyway | yes — the same |
| VSync / frame pacing (fix 31) | no hang in 7 starts; main menu 6.0-6.1 snapshots/s, gap median 165.0-165.2 ms, p95 166.5, max 166.7 | no hang; 6.0/s, 165.2 / 166.4 / 166.7 ms |
| the real desktop, for reference | — | 6.0/s, 165.1 / 166.4 / 166.9 ms (`--real-desktop`, one start) |
| screenshot | `import -window root` / `-window <id>` | `import -window <id>` (a rootless root is black) |
| input | `xdotool key --window <id>` reaches the engine | the same |
| intro skip (`tools/intro_skip.py`) | yes — `engine_start` prints INTRO SKIPPED and READY | yes (by hand) |
| anything in Data's session | nothing: `xdotool search --pid` on `:0` (with the auth file that opens `:0`, 3440 px wide) finds no engine window | nothing |
| side effects | none; its own MIT cookie (`xauth`), no TCP | needs `dbus-run-session`; tries gvfs (`fusermount3` refused); **writes a `.mutter-Xwaylandauth.*` in `/run/user/1000`** — the file `engine_start`'s "newest auth file" rule picked for `:0` until 182 |

**Chosen: A, Xvfb** — no GPU, no D-Bus, no GNOME, no auth file in the
session's directory; it is started and stopped by `tools/vdisplay.py`
with a private cookie. B works and is not needed. The auth-file trap B
exposed is closed anyway: the real desktop now takes the auth file that
actually opens `:0` (`vdisplay.session_auth`), not merely the newest.

## Proof of equivalence (step 2)

The same live steps, on Xvfb (`V_*`) and on Data's desktop (`R_*`,
`--real-desktop "equivalence proof, work order 182 Part 1.2"`), each on a
fresh engine, SAVE4 loaded as scratch, nothing saved; evidence
`~/orionlayer-fixtures/evidence/work_order_182/`:

- `tools/flash_walk.py` — pre-game (main menu, New Game, Select Race,
  Empire Identity, Custom Race), the save load, every in-game nav
  transition, the system window: 29 transitions — at 1920x1080 and
  2576x1432;
- `tools/colony_accept.py --orders` — 181's colony screen and build popup
  (every way in and out, `<`/`>`, a pop move and back, the queue under
  edit, Cancel, one real order and back): 23 transitions — at both sizes.

| | 1920 flash | 1920 colony | 2576 flash | 2576 colony |
|---|---|---|---|---|
| native frames, V / R | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| transition table (name, settled, native, pixel verdict) | identical | identical | identical | identical |
| wire per capture (screen, fields, stardate, HD screen, net) | identical (29) | identical (34) | identical (29) | identical (34) |
| orders and their results (pop move, lists, queue, OK, record) | — | identical | — | identical |
| colony frames agreeing with the engine's handle, V / R | — | 407 / 406 | — | 395 / 399 |
| every guard | MOX.SET's load byte (offset 21, 10 → 3), restored — both | | | |

**Pixels.** Every HD capture of the colony screen and the popup is
identical between V and R. What differs, each explained:

- **HD**: the galaxy map's fleet route line (its dashes march — two
  captures of the SAME run differ there too), the main menu's animation
  (two captures of one run differ in the same box), and a 2 px text cursor
  blinking in Empire Identity's name field.
- **native** (the game's own framebuffer, from the wire): the same route
  line and the orbiting planets of the system window (animation phase; the
  map's box differs between two captures of one run), the shown colony's
  orbit marker (`Global_Cycler_(50, 6)`, colsysdi.cpp:78), Empire
  Identity's default ruler name — "Saguaro Ty" on V, "Tak Tochno" on R:
  the game draws a random one per visit, not a display effect — and on the
  Colonies screen one pop icon blinking dark on R: the original blinks the
  icon under its POINTER (coldraw.cpp:342-343), and on the real desktop
  that is wherever Data's mouse was. That last one is the interference this
  part removes.

**Result: equivalent. Switched over.**
