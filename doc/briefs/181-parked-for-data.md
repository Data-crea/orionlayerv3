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
