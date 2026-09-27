# Work order 182 — parked for Data

Ordered by importance: 1. the new open fix, 2. the virtual display, 3. everything else. Every item names the default this run continued with.

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
