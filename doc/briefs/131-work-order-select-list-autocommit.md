DEFERRED — not executed. Taken up again when the HD research screens are built (Data, 19 Sep 2026).

Work order <next free number> — Why the select list chooses by itself, and the rest of 130's acceptance (19 Sep 2026)

Assign the next free number. No reporting stop; park what is Data's to decide. Separate commits, no push. Rules as in 130: the block headed "RULES FOR THE WHOLE RUN — re-read this block at the start of every part" in doc/briefs/126-work-order-unattended-run.md, plus the three additions at the top of work order 129. Multi-turn live runs use a NEW GAME, as 129 and 130 did; the scratch saves are reloaded, never continued.

NO change to orion2re is authorised in this order. If part A can only be solved on the engine side, describe it per rule 2 and park it.


WHAT DATA ESTABLISHED THIS MORNING (19 Sep), by hand

The binary built from e9d07528 (Open Fix 25 in), NO client connected, real mouse in the orion2re window, new game: after the presentation dialog the select list WAITS. He took his hand off the mouse, nothing was chosen, the pointer's hover highlight worked, he chose normally. So the patch on its own does not cause the behaviour recorded as Open Fix 26 ("the select list commits a row by itself about a second and a half after the hand-over").

He also saw three presentation screens after one completed field, having picked one application. That is the original's behaviour, not a fault: tech.cpp treats six field ids as "everyone gets every application" in two places — where the current field's rows are coloured, and where the completed applications are handed out. It matters for part C.


PART A — Open Fix 26: find the mechanism, then fix it on the client side

Two variables are left: a client being connected at all, and the presentation dialog being dismissed by INJECTED clicks. Separate them before theorising (the fundament's "Read the source before theorising." and "Establish which side of the boundary a problem is on before designing for it."):

- Connected and silent: a client that connects, reads, and sends nothing from before the turn ends until ten seconds after the list is up. The dialog has to be dismissed without the client — if there is no way to do that from a tool, say so, and leave that one run to Data (write him the exact steps in the parked file).
- Injected dismissal, as 130 did it. Then vary it: a key instead of a click if the dialog takes one; a longer gap between the last click's DOWN and UP; a pause between the last click and the hand-over.
- Read, on the engine side, the function that DELIVERS an injected click (how DOWN and UP are spread over ticks — the fundament already records that DOWN alone hangs the game) and the function that BUILDS the select list's input loop (what it does with mouse state, pending input and any buffered click when it starts). The delay of about one and a half seconds is a clue; find what in that path has a timer, a repeat or a queue of that length.
- 130 measured "zero sends" after the hand-over. Widen the counter: every send since the turn ended, with its time, next to the time the field changed.

Then fix it in OrionLayer if it can be fixed there — the fallback's click forwarding (part A of 130) and the HD screen both have to come out of this without the list ever choosing for the player. Acceptance: five hand-overs in a row, in OrionLayer's window only, where the list stays untouched for ten seconds with the send log empty, and the player's click then chooses the row clicked. File what was learnt under Open Fix 26's entry, quoting its first line.


PART B — Finish 130 part F

The third selection in a third category, and HD beside the native frame at the two resolutions still missing. Every capture with its colour count, as 130 introduced.


PART C — The six "everyone gets everything" fields, Creative and Uncreative

The two places in tech.cpp named above decide what a choice MEANS. Check the HD screen against them and against the native frame: what is highlighted on hover for such a field (one row or all), what a click on any of its rows sends, and what the screen does for a Creative and for an Uncreative player. A new game's first list consists largely of these fields, so this is cheap to see live. Where HD differs from the original, fix it; where the first build deliberately leaves something out, mark it (module, status document, check). If doc/newtech_reading.md does not already say that one completed field can produce several presentation screens, add it with the source.


PART D — A fallback must be loud

130's screen fell back on every real state and nobody could tell, because falling back looks like working. From now on: every fallback from an HD screen that exists writes one log line with the reason, and the live driver's record names the HD screen that was actually drawing, beside the colour count. The live acceptance in parts A and B asserts that research_select was the active screen while the wire said 53 — from the record AND from the picture, not from a flag.


PART E — Test doubles written next to the code

130's check passed because it built its own state object with the same invented attribute name the code used. Go through tools/smoke_test.py for checks that build a stand-in for GameState, the dispatcher or the client by hand. List them all. Convert the ones where the real class can be used at little cost; for the rest say why not. Do not sweep beyond that.


PART F — Two lessons for the fundament

Worded from what happened, checked against the tree so nothing is filed twice:
- 129 reported "HD shows the original picture" from a flag named use_original, while six single-colour screenshots lay in the evidence folder unopened. A flag's name is not an observation, and evidence nobody looked at is not evidence. It belongs beside "A field dump is not documentation."
- A test double written by the same hand as the code shares its mistakes.


PART G — The display server, report only

On 18 Sep at about 18:25 SDL could no longer open a display ("The video driver did not add any displays") while the desktop kept running. Data found no leftover orion2re or python processes the next morning. Look at the journal around that time and at how the live driver and the headless renderers open and close their windows. Report what you find; change nothing unless a tool of ours plainly leaks.


THEN

Fresh clone, setup, full smoke, as before a push — and report the result. The push itself stays Data's decision; 129, 130 and this order are all still local.


REPORT

Deviations first. Per part: seen live (evidence path, colour count, active HD screen), committed (hash), smoke before and after. Open Fix 26: mechanism, with the source lines, and what the fix is. A parked file only if something is Data's to decide; if it stays empty, say so.
