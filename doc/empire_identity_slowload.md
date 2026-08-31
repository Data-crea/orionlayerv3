# Empire Identity — the 23-second gap

An open investigation record, in the same spirit as
`ship_icon_measurement.md`: the full state of a question that is
deliberately not closed, so the volatile status document can carry a
five-line summary instead of the whole case file. If the gap
reappears, start here.

Status: **dormant since the 30 August reboot. Not closed.** A fault
that appears once and then hides has a different cause from one that
always fires, and closing it as "fixed" would be a guess.

---

## The observation

One run spent **23.6 s** between the banner-tile activation and the
home-star FIELD_LIST; every run since has spent **2.7 s** with the
same settings (Huge, 3 opponents, Impossible, 71 stars). The gap sits
in the stretch where orion2re generates the galaxy — a period the
Extension API is legitimately silent in, because `ext::Tick()` runs
from `fields::Get_Input_()` and mapgen has no input loop.

## Ruled out, with the evidence

- **The client is not the slow side.** The chain's own steps cost
  2.8 s of the 26.4, and the heartbeat reported 0 bytes, 0 snapshots
  for the whole gap — OrionLayer was waiting, not working.
- **Nothing was blocking on the socket**, for the same reason.
- **orion2re was not computing.** `top` showed it in state S at
  1–8 % CPU. Whatever it did for 23 seconds, it did it asleep.
- Silence on the ext API proves only that `Get_Input_()` did not
  reach the hook — it does not distinguish "busy" from "stuck".

## What ended it, and what that implies

**A system reboot.** Every run since has been short, including the
first one after the restart — the run that had been slow before. So
the cause was accumulated session state, not the settings, the banner
tile or the build. The two runs that looked like a banner-tile
correlation (slow run picked tile 7, fast runs tile 2) were the same
fluke seen twice; the run order was confounded from the start,
because the slow run was always the second of its session.

**Likeliest candidate:** the reconnect storm the 3-second watchdog
bug produced. If orion2re keeps a dropped client in its list, it
serializes for dead connections on every tick, and the cost grows
with every reconnect of the session. That would mean the watchdog fix
(now 10 s, holdable) removed this too — as a side effect, not by
design. **Unproven.**

## Withdrawn conclusions

"It is the injection" was withdrawn: the 7-second F12 comparison run
differed from the slow run in more than one variable, so it proved
nothing. Untested candidates, in order: the banner tile, and the star
count — 71 sits one star under the 72 threshold where orion2re
switches to extended scaling.

## If it comes back

The instrumentation is already in the tree and costs nothing while
things are fast: `injection.py` logs the New Game settings at chain
start, the elapsed time per step, and a heartbeat every 2 s carrying
state/s, visual/s and KB/s from `GameClient.stats`; `main.py` logs
timestamps.

1. `ss -tnp | grep 17362` — more connections than OrionLayer's one
   and the dead-client mechanism is confirmed in one line.
2. `grep -E "setup:|Banner tile|Fields changed after 'banner'"` on
   the OrionLayer log for the timeline.
3. `gdb -p $(pgrep -x orion2re) -batch -ex "thread apply all bt"`
   inside the gap, to name the function it sleeps in.
