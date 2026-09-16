Work order 124 — GAME menu completion and the open remainders (16 Sep 2026)

Everything in 122 and 123 is pushed; main and origin/main are at 1de9918. This order has three new items Data decided tonight (A–C) and four leftovers (D–G). Separate commits, push stays with Data.

Live runs: Data's own OrionLayer must be closed first, and the scratch game currently holds an in-memory colony on Malus II — reload SAVE4/5, do not continue the running game. Every injected click is followed by a framebuffer read before the next one (the rule filed in 123).

Start with D and E: they are small, and A is the one that may need a patch, so its shape should be known before the evening's work is spent.

A. Savegame names in the load and save dialogs

Today both dialogs show "Slot N" instead of the saved game's own name. That was expected: Open Fix 14 puts the save list on the wire and is described but NOT applied.

Report first, build second. Read loadsave.cpp and the Extension API and answer: where does the original read the slot names from (file header, an in-memory table, both), and is there any path that already reaches a client without a patch? A snapshot field nobody looked at is cheaper than a patch (decision 25 — reconstruct before asking for one).
If a patch is genuinely needed, it is Open Fix 14 and it follows the orion2re rule: one entry in doc/orion2re_open_fixes.md, a patch file under doc/, reported to Data BEFORE it is applied. Stop there and report — do not apply it in this run.
If the names can be read without a patch, build it: the list shows the real name, the save dialog pre-fills the existing name of the slot being overwritten, and an empty slot reads as the original writes it (take the wording from the game, not from us — decision 15, the string goes in JSON).

Acceptance: either a report naming the patch and what it would carry, or the dialogs showing real names beside a native screenshot.

B. Click feedback on GAME and every menu entry

Data wants an orange flash on press, so the user sees the click land. Before building: check what the ORIGINAL does on these buttons — MOO2 draws a pressed state on its own fields, and if it does, this is a transcription and follows it. If the original shows nothing (or something that is not orange), then an orange flash is an HD INVENTION and needs the full marking: in the module, in the status document, and in a smoke test that fails if it silently disappears. Say which of the two it is in the report.

Scope: the GAME button in the galaxy frame, and every button in the menu tree (SAVE, LOAD, NEW, QUIT, SETTINGS, RETURN, YES/NO, the load and save rows). One implementation, shared — the third copy rule. Colour comes from the palette, not a literal; the frame artwork's own orange lamps are the reference for the hue.

The feedback is drawn in HD and must not depend on the game answering: it fires on the press, and it must NOT imply success where the game would refuse the input (decision 33). If an input can be refused, the flash still fires and the refusal is drawn as it already is.

C. Music and Sound FX sliders

Decided on 14 Sep to omit and mark them; Data now wants them built.

Read first: how does the original store and apply the two volumes (loadsave.cpp settings dialog and whatever it calls), what are the value ranges and steps, and how many segments does the bar have (the original draws discrete blocks, not a continuous bar).
Then say plainly whether a client can set them at all: field activation, an injected click on the bar, or nothing without a patch. If it needs a patch, same rule as A — describe, do not apply, report.
Build the HD side to the original's geometry and step count. The drag behaviour is HD's own: name it and mark it if the original only accepts clicks.
Remove the "omitted and marked" note from the status document and the module when they are real.
D. Menu buttons under the confirmation

From 123: HD draws the popup without the menu buttons under the confirmation box; the original shows the menu underneath. Fix so the menu is drawn behind the box as the original has it. Small, visual, confirm with a side-by-side.

E. Fundament: the hidden full-screen field

From 123's eta run: screens that ignore injected clicks and keys respond to ACTIVATE_FIELD on their screen-filling hidden field — that is very likely what the GNN screen was in 122. File it in section 3 (orion2re facts worth memorising), next to the existing field-type entries, with the run as its source. Mark the GNN case as inferred, not confirmed, unless it is re-tested.

F. Frame bottom edge against the nav bar

The 123 fix sends the scale factor's excess downward. Measure how far the game-menu frame now reaches into the nav bar at 1080p, 1440p and 2160p, and whether any nav label is covered. Report numbers; only fix if something is actually covered.

G. Research readout

HD shows "500 RP" where the original shows "~16 turns" (the turn estimate is in the original's sidebar). Pre-existing, found in the 1a comparison. Read where the original computes it and report the expression before changing the readout — this is a number, not a label, and it needs a source.

Report

In this order, per item: what changed (files), decisions or Open Fixes filed, smoke count before/after, what needs Data's hand, what could not be done and why. Items A and C may end in a report rather than code — that is a correct outcome, not a failure.

Untouched and still open: scroll bar for fleets over nine ships (needs Data's big-fleet save), the named scroll deviation (live unconfirmed), Part C of brief 110 (waits on the message-ID patch), Open Fix 15 and 19, right-click outside the help regions in the save dialog (needs Data's own click at the native window), colony_move_hd.py import error, the Empire Identity key burst over ~10 characters, and the whole colony-screen work order.
