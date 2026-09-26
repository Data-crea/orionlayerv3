# Work order 177 — progress

Unattended run, 26 September 2026. Invisible modals on the galaxy map, the
safety net, Select Race's way back, the main menu's Load dialog, the start
deadline; live tests; push. Evidence root:
`~/orionlayer-fixtures/evidence/work_order_177/`.

## E. The start deadline — **DONE (both: raised AND named)**

`tools/engine_start.py`: the deadline is `START_DEADLINE = 150` s (was
60 s since 174) — the original's logo and intro sequence, which plays
whenever no key or button is down at start (`JIM::Draw_Logos_`,
jim.cpp:18-120), takes 112.9 s every time (11 of 82 starts in 176). While
the log stands at "mox2: data space allocated" WITHOUT the hang's signature
the tool now prints "INTRO: the original's logos and intro are playing" and
keeps waiting, so an intro is neither a timeout nor mistaken for open fix
31's hang. 006e holds the deadline above the intro and the CLI default to
it. (176's parked item 6.)
