# Work order 174 — parked for Data

Every choice, finding and question this unattended run parked, with the
default taken.

---

## A1 — open fix 31: present without VSync on request

**Default taken: written, not applied** (`doc/ext_present_no_vsync.patch`).
It is the only change that removed the start hang (0 in 50 against 8 in
60). Applying it is Data's (and Joes') call; until then
`tools/engine_start.py` recognises the hang and starts again. A deeper
fix — a timeout on the game thread's wait for the present — was not
attempted.

## A2 — the inhibitor

`tools/engine_start.py` holds `gnome-session-inhibit --inhibit idle` for
the engine's lifetime so the screen does not blank during a live run —
no setting changed, gone with the engine. **Alternative:** `--no-inhibit`.

## A3 — what was running on the desktop

This run started at 06:18; Data launched Borderlands 3 full-screen at
06:21:53, and every engine of this run after that sat behind it. An
engine that came up runs throttled there. Noted because the live part
(C) ran in the same state.
