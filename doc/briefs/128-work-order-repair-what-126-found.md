Work order <next free number> — Repair what 126 found: the Screen 6 collision, field 9 in the research dialog, the Planets list, weapons(), and three small safeguards (17 Sep 2026)

Assign the next free number (126 and 127 are taken; 125 is taken too, its file is missing from doc/briefs/ and Data will supply it — note it, do not reconstruct it). Data has decided the points below in chat after reading 126's closing report; where this order says "decided", that is his decision and not a suggestion. Separate commits, no push.

The RULES block of work order 126 applies here unchanged — it is not repeated, one home. Two things differ: this order DOES include live runs, and it DOES authorise exactly one change to orion2re (part B). Nothing else in ~/orion2re is touched.

126 ran without the game ever being up. Everything it found is derived from source, and its one change to productive input handling (mapinput.py) has never been exercised live. That is where this order starts.

PART A — First live step: the galaxy map after 126 part F

Before anything is repaired, show that the input split did not change behaviour. On a reloaded scratch save, against the framebuffer after each step: a click on a star, zoom in and out with the wheel, pan, a fleet selection and its cancel, the GAME menu open and closed. If anything differs from before the split, stop repairing, fix or revert part F first, and say so at the top of the report.

PART B — Screen 6 means two things (decided: the race selection gets its own synthetic ID)

126's finding, from three source files, not seen live: the galaxy map's RACES button sets the screen the game uses for races/diplomacy, and OrionLayer maps that same number to select_race, because our own ext_screen_id.patch makes the race selection report it too.

Reproduce it live first. Click RACES on the HD galaxy map and record what HD shows and what the framebuffer shows. If it does NOT reproduce, stop this part and report — a fix for a fault nobody has seen is a guess.
Change the patch so the race selection reports a synthetic ID of its own, the way Custom Race already does. Pick the next free synthetic number and check it against the engine's own screen enum so it cannot collide again. This is a new commit on the orionlayer-local branch in ~/orion2re, with a message naming the open fix; doc/ext_screen_id.patch, doc/orion2re_open_fixes.md and the REQUIRED_FIXES entry in tools/version_check.py follow in the same OrionLayer commit. The screen-name table has one home — change it there.
126 also noted that taking a stock race leaves that screen number set afterwards. Say whether the new ID changes that, fixes it, or leaves it; do not widen the patch for it without reporting first.
Live again: the New Game flow through race selection and Custom Race still works end to end, and RACES from the galaxy map now falls back to the original screen (decision 22) instead of opening the HD race selection.
A smoke check that asserts the rule, not the instance: no two screens in the tree claim the same GAME_SCREEN_ID, and no synthetic ID lies inside the engine's own range.

PART C — The galaxy map must not park into the research dialog (decided: guard by field-list shape, the pattern of decision 59)

From source, not observed: the map sends the zoom-out field whenever the game reports the main screen and the view is not fully zoomed out; the research choice at turn start reports the same screen number, and the same field number is a research row there.

Park only when the field list has the main screen's shape, never on the screen number alone. Use the shape test that decision 59 already introduced rather than writing a second one — if it is not reusable as it stands, extract it (third-copy rule) and say so.
Smoke check: hand the map a field list shaped like the research dialog with the main screen's number, zoomed in, and assert that nothing is sent.
Try to reproduce the original fault live on a scratch save (zoom the HD view in, end turns until a research choice comes up). If it cannot be reached in reasonable time, say so and leave it at the smoke check — do not spend the evening on it.

PART D — Planets list: hover and draw disagree on single pixel rows (decision 5)

One function produces the row for a y coordinate; drawing and hover both call it. Then the check that makes it stay fixed: sweep EVERY pixel row of the list, at all four resolutions, and assert that the hovered row is the drawn row. And because a shared function guarantees agreement, not correctness (filed today from the stacked-figures case), also assert against what is visible: a pixel inside a drawn row's rect resolves to that row.

126's redundancy audit lists 24 drifted copies. Do not work through them here. But before touching any screen in this order, read its entries in doc/redundancy_audit.md — this part's fault came out of that list, and its neighbours may be the same kind.

PART E — weapons() skips empty slots; the original stops at the first one

126's finding: the original ends the weapon list at the first empty slot, core/structs/ship.py skips empty slots instead, and its docstring misreads the source line.

Evidence before the change, two sources: the function in orion2re that BUILDS or writes the weapon slots (design, refit, capture) — can a gap exist at all? — and a struct probe over a real save: how many ships have a gap. Report both numbers.
Then make weapons() do what the original does and correct the docstring. List every caller and say whether its result can change.
A smoke check with a constructed ship that has a gap.

PART F — Three small safeguards

faulthandler. Enable it at the top of tools/smoke_test.py, so that the next exit 139 prints the Python stack before it dies. On 16 September the real loss was not the crash but that its output vanished. Show once, in a subprocess, that a forced segfault now leaves a stack on stderr, and that the pre-commit hook still blocks on it. Thirty clean runs today proved little — at a true rate of one in thirty, thirty runs stay clean about one time in three. This line makes every ordinary run a probe instead.
The hook in a fresh clone. A hook under tools/githooks/ only fires where core.hooksPath points at it. Make the documented setup do that (setup.py or the step CLAUDE.md names — your choice, one home) and prove it: fresh clone, documented setup, forced-red smoke, commit refused.
The smoke check for decision 28 asserts nothing today — 127's Stop 1 found it is satisfied by words from other entries. Repair it so it reads what it means, and show it red once. If the same weakness is visible in a neighbouring check while you are there, list it; do not sweep.

NOT IN THIS ORDER

Open Fix 22 and any other patch for the colony view — that is the next order, after Data has read the colony reading report in doc/. The smoke-test split (parked; decided: later, after these repairs). Stop 2 of 127 (decided: the ceiling is the 80 KB that Stop 1 proposed; the build comes after the large screens). No new screen. No push.

REPORT

Deviations from this order first. Then per part: what was seen live (with the evidence path), what is committed (hash), and the smoke count before and after. A parked file only if something is Data's to decide; if it stays empty, say so.
