# Work order 181 — parked for Data

Every item names the default this run continued with.

## Fix 35's include carries the marker too

Fix 35 changes two places in `src/ext/ext_api.cpp`: its block, whose
comment names the fix, and one added line `#include "game/build_queue.h"`
(for `BUILD_QUEUE::autobuild_settings`), which named nothing. Part 2.1 asks
for "OrionLayer, open fix <N>." at every changed place; Part 1 allowed the
series to differ from 180's proof only by fix 39's marker. The two cannot
both hold for this line.

**Default:** the marker, on the same line (no line added, no hunk moves):
`#include "game/build_queue.h"  // OrionLayer, open fix 35. autobuild_settings, sent in "COLS".`
— made in the patch file before it was applied, so file and commit
`c5d4dacd` match. Undoing it is a comment edit plus the patch file's diff
section; nothing depends on it.

## A popup click lost once at 3840 — observation, cause not established

In the first 3840x2160 walk (`~/orionlayer-fixtures/evidence/
work_order_181/P3_pictures_3840x2160_cancel_lost/`) the build popup's
Cancel, clicked in HD, did nothing. The trace shows the client's field list
empty for exactly that frame (snapshot 1663: 45 fields, then 0, then 45) —
a FIELD_LIST of 0 fields from the engine while the popup rebuilt its
fields; the activation most likely landed in that gap. A fresh engine
repeated the walk with every transition settled. The desktop was in active
use at the time, and the engine's window follows the real pointer
(decision 39's correction), which is a plausible trigger — not measured.
**Default:** nothing changed; the lost click is not silent in the sense of
harm (nothing was sent to a wrong field), but the player would click
again. A fix on our side would be to hold a click that meets an empty
list and send it when the same list is back — a new rule for every HD
screen, so it is Data's call.

## Plague and Pop Boom were not seen live

SAVE4 has neither event on any of the six colonies walked (CEVT 0 / 0), so
the two words are proved only by the smoke check's forced states and the
engine's own function (events.cpp:131-151). **Default:** accepted on that
basis; a save with an active event would show them.
