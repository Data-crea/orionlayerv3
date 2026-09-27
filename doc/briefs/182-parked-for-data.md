# Work order 182 — parked for Data

Ordered by importance: 1. the new open fix, 2. the virtual display, 3. everything else. Every item names the default this run continued with.

## 1. Open fix 41 — the engine's own window hidden from the start (for approval)

`doc/ext_engine_window_hidden.patch`, entry 41 in `doc/orion2re_open_fixes.md`.
Two marked places: `ext::g_hide_window` starts `true`, so the window the
engine creates hidden is never shown (the show at platform.cpp:1406-1408
was conditional on the flag already; it was just set too late, from
`mox2.cpp:382`); and a hidden window presents without VSync, so it can
never meet open fix 31's hang. **Unlocks:** no engine window on any
player's desktop, and no real pointer for the original to follow.
Proved in a scratch build: never mapped on the virtual display and on your
session, pacing unchanged, HD identical (flash walk incl. a load, the
colony acceptance with orders), the tools' intro skip still arrives.
**Default this run continued with: not applied.**

**Decide with it — the intro, for a player.** With the window hidden, the
original's logos and intro still play for about 113 s (with their sound)
before the Extension API is up, and the player sees only OrionLayer's
window waiting. The tools skip it with one key to the window (it still
arrives). Options: (a) leave it; (b) an engine switch to skip the intro
(`ORION2RE_SKIP_INTRO`, in `JIM::Draw_Logos_`, jim.cpp:59/113) — a second
engine change, so a second open fix; (c) OrionLayer says "the game is
starting" while it waits. **Default:** (a), nothing built.

## 2. The virtual display

- **Live runs no longer appear on your desktop** (and play no sound). The
  engine runs on a private Xvfb (`python tools/vdisplay.py status`); it
  stays up between runs, idle and invisible — `python tools/vdisplay.py
  stop` ends it. **Default:** left running between live runs, stopped at
  the end of this order.
- **Your own sessions are unchanged**: `python main.py` and a game you
  start yourself still use your desktop. Only the tools behave differently.
- A tool can still use your desktop with `--real-desktop "reason"` (the
  engine) or `ORIONLAYER_REAL_DESKTOP="reason"` (a client). **Default:**
  used only for the equivalence proof and one pacing reference in this
  order, each named in progress.
