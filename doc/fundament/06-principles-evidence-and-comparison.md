# The fundament, part 6 of 9 — Evidence, and comparison against the original

How a claim is established, and how it is checked against the original — the section's own preamble, Evidence, Comparison against the original.

**Decisions in this part:** no decisions.

The index is [`../v3_fundament.md`](../v3_fundament.md), and it is
what to read first. This file is one part of the fundament and
carries no rule that is not in it; the text below is what stood in
`doc/v3_fundament.md` before work order 164 moved it, unchanged.

<!-- fundament-body -->
## 2. Working principles

The same handful of mistakes keeps recurring in new costumes. Grouped
by the mistake, not by the date — a date-ordered list grows forever
and hides the repetition.

### Evidence

**Read the function that BUILDS the thing, not the ones that read
it.** An inferred call chain is not evidence. The `_ship_node`
detour: three functions that consume the table said nothing, one
function that fills it settled the question in a minute and made a
C++ patch unnecessary.

**Two independent sources before any production value.** Header plus
live probe, or header plus static_assert. Anything from a single
source goes to `unverified.py`.

**Numerically verify, never estimate visually.** The oldest rule in
the project and still the most violated.

**When the original states a PROPORTION, the proportion is the
transcription and the pixel count is DERIVED from it.** The colony
summary's producing column is `Squeeze_Print_Formatted_Paragraph_(
0x200, y, 0x55, 0x16)` (colsum.cpp:621): width 85 of a 640 px screen,
which is 13.3 %, which is 190 of 1408. That ratio was rejected once as
"a scaled estimate" in favour of measuring the widest producing string
— 311 px, on one line, at full font — and the measurement came out
nearly twice as large and looked exactly as authoritative.
`BILL::_Squeeze_Print_Paragraph_` (bill.cpp:147) settles it: `width`
goes straight into `get_height(width, text)` and the loop shrinks the
HEIGHT until it fits. **Width never moves, and the function has no
truncation branch at all.** All three constraints in the measurement
— one line, full font, whole string unwrapped — are ones the original
never imposes.

Worth keeping as the SHAPE of the error rather than as one column's
number: it was not a wrong measurement, it was the right measurement
of the wrong question. A requirement the original does not have is
not a measurement of the original. And the direction of the rule is
the useful half — a percentage carries across a resolution change and
a pixel count does not, so the tree stores the one the source states
and computes the other, never the reverse.

**Ring from the artwork, window from the layout, boundary measured.**
Generated artwork and the geometry it has to fit come from two
different places on purpose, and the place where they meet is
asserted in numbers. (`frame_build.py` is deleted — decision 55,
12 September 2026 — and what it did is kept here because the PRINCIPLE
is what the paragraph is about.) `frame_build.py` lifts the device ring out of
the master's own rectangles rather than scaling the reference number
— `round(ring * scale)` put the plate's ring one pixel INSIDE its own
first hole at 1440p, 106 where the table says 107, because the holes
are placed by `Layout.rect`'s truncation and a second rounding rule
disagreed with the first. Taking the ring from the rectangles the
holes are cut from makes the two agree by construction, and the check
compares in DEVICE pixels for the same reason: converting an edge
back to reference asks `round(int(107 * 4/3) / (4/3))` to be 107, and
at 1440p it is 106.

**Artwork that does not fit the ring fails at the checker, not at the
eye.** A window overhanging the metal by a pixel is invisible at every
resolution somebody looks at and wrong at the one they do not, so the
boundary is measured — every window's three edge pixels against the
plate's own metal median, the eight windows agreeing per side to
within 4 — and the check is verified to FAIL, with the bevel pass
removed, before it is trusted. This is the same statement as decision
3 one domain over: the artwork is upstream of the geometry, the
geometry is upstream of the boxes, and every join between them is a
number somebody can check rather than a picture somebody approved.

**A measurement that is not stable under its own threshold is not a
measurement.** The guardian icon was measured at 17x16 and shipped;
the real sprite is 12x11. A low brightness threshold had bridged it
into two background stars. Every other sprite held steady across a
threshold sweep and only that one moved by 45 %, which is the whole
tell — sweep the parameter before trusting the number.

**A measurement anchored on the wrong feature is stable, repeatable
and wrong — and a threshold sweep will not find it.** The sibling of
the rule above, and the reason it is a separate line: there the
parameter was too permissive and moving it exposed the fault, here
the parameter is fine and nothing about it moves. (`frame_master` is
deleted — decision 55.) `frame_master`'s
`--profiles` walks each hole's edge OUTWARD FROM ITS BOUNDING BOX.
For the master's eight rectangular holes that is the same edge. For
its one chamfered hole — the header cartouche — it is not: the bbox
starts at y=21 and the lit lip sits at y=21..22, so the band sampled
above the box is three rows of plain metal and the tool printed
**"a side with no lit edge"** for a hole whose every side carries a
one-pixel lip of 147..222 against metal at 2. Stable at any
threshold, because the band contains no lit pixel to threshold.

**The tell is the SHAPE, not the number**: fill against the bounding
box, 91.4 % for that hole against 94.4-99.9 % for the eight others.
That ratio is now the gate, and `bevel_source` refuses a hole below
it — which was always required and had never been stated, because
the function CROPS A RECTANGLE and a chamfered source would print
its own slanted corners onto every window of the screen. It was
excluded by accident, by scoring 0.00 from a measurement that could
not see it. **An exclusion that happens to hold is not a rule**, and
the day a chamfered hole measures well is the day it silently wins.

**And the first diagnosis of it was wrong, which is the half worth
keeping.** The cause was reported as "the chamfered corners put hole
pixels into the metal band and flatten the average" — plausible,
mechanical, and false: masking every hole pixel out of the band
changes **not one of the forty numbers** the tool prints, because
the bands lie outside the box and contain none. An explanation that
predicts nothing is not a diagnosis, and the cheapest test of one is
to apply the fix it implies and see whether anything moves. A tool
may report that it cannot measure something. It may not report the
thing as absent.

**Establish the ruler's own error before believing an improvement.**
Rotation drift was measured at 0.37 px and the obvious next move was
to chase it lower. The frames at 0, 90, 180 and 270 degrees are exact
rotations and cannot drift at all, so measuring *those* gives the
noise floor: 0.26 px. Almost the entire remaining "error" was the
measurement. Two fixes had already been built and both made things
worse, because they were correcting numbers smaller than the
instrument could resolve.

**An outlier has to be justified before it is used.** 17x16 stood out
against six siblings clustered around 11x10 and nobody asked why. The
smoke test now asserts that no monster exceeds 1.4x the player ship,
which turns that question into a failing test.

**An asset is not a measurement.** A rule that reads a number out of
the artwork — pixel width, canvas size, export scale — is a
convention pretending to be data, and it fails silently the first
time somebody redraws the artwork rather than regenerating it. The
number has to live in a table with a source next to it. The nebula
sizes were in the assets for three weeks and were only wrong once the
masters were replaced.

**A field dump is not documentation.** The Extension API reports
geometry, type and hotkey. Every label in a dump is interpretation
until the source confirms it. Field 14 was labelled "Research" for two
weeks; it is `_races_button`, and the wrong label had already reached
`layout.json`, where the HD button would have opened diplomacy.

**A name table copied into three files is the same failure.** The
screen-ID map lived independently in `dispatcher.py`, `ext_diag.py`
and the index doc. Diffing them found real drift in two of the three.

**And it applies to somebody else's tree, where you cannot fix it —
so grep for the second copy before believing the first.** The colony
summary's sidebar layout was got wrong twice, in opposite directions,
because one definition was read and treated as the definition.
`s_0_0055110c` and `s_1_00551110` — the two format prefixes every
sidebar line carries — are defined **three times in three
namespaces**: COLSUM (`colsum.cpp:36-37`), ESTRINGS
(`estrings.cpp:8-9`) and strings (`strings.cpp:22,24`), and declared
at two different sizes on top of that (`[3]`, `[3]`, `[4]`). The
first two spell the value in octal, where `"\0320"` looks like ESC
and is SUB; the third spells it `"\x1A" "0"` and carries the answer
in a comment — *"switches paragraph justification to left
alignment"*. One grep found one site, and the escape was misread in
one direction and then, correcting it, in the other.

What would have settled it in a minute was not more care with octal.
It was `grep -rn s_0_0055110c` — three hits where one was expected,
which is the signal, before any argument about what the bytes mean.
The octal is the local detail; the transferable rule is that a
symbol found once has not been found, and that the copies disagreeing
about their *type* is a louder warning than the values agreeing is a
reassurance. Filed as a question rather than a fix in
`doc/orion2re_open_fixes.md` item 6, because it is not our tree.

The same thing happened to the list of C++ fixes being asked of Joes,
and there it was worse, because the drift pointed outward. The status
document named three items and named a file as their home; the file
contained three different items, one of which was already applied,
and a third document pointed at a patch file that did not exist. A
list of requests to somebody else must have exactly one home —
`doc/orion2re_open_fixes.md` — and everything else must be a pointer,
never a copy. A copy is a second thing to forget to update.

**A marking that two documents claim exists is not a marking.**
`core/helppopup.py` and this file both stated that the auto-sizing
help panel was marked as an HD EXTENSION in `screens/*/help.json`. It
was marked in none of the three, for as long as both documents said
so. This is not the name-table failure above wearing a new costume:
there the copies existed and drifted, here no copy was ever written,
and nothing noticed because a marking *does* nothing — no code reads
it, no screen shows it, and the two sentences asserting it were the
only evidence anybody ever consulted. A labelling rule without a
check is an intention, and it decays exactly the way the hand-copied
engine version in decision 36 would have without
`tools/version_check.py`: correct on the day it is written, and
unfalsifiable every day after. The check has the same shape as that
one, too — walk the tree rather than a list of screens, refuse a file
that carries no marking, and refuse a marking that does not name what
the original does instead, so the note records a reason rather than
carrying a label.

**A claim in a bug report needs a source like any other number.**
"SendFrame drops the client, and that is the cause of every reconnect
in the log" survived weeks and reached the list Joes gets as fact.
The reconnects were OrionLayer's own watchdog firing during
legitimate silence. Nobody had checked the one thing that separates
the two: a server that dropped a client still answers the next
connection, so the missing `HELLO_REPLY` after every reconnect said
the server was not running at all. The bug may still be real; the
symptom attributed to it was not.

**Read the source before theorising.** When the API behaves
unexpectedly, the answer is usually one function in the orion2re tree.
Four consecutive theories were wrong about the Empire Identity
injection; `racesel.cpp`, `namestar.cpp`, `fields.cpp` and
`ext_api.cpp` settled it in one pass.

**Establish which side of the boundary a problem is on before
designing for it.** The pointer-anchored zoom was first treated as a
question about orion2re — what does a zoom step anchor on, can a
client move the origin at all — and a live probe was built to answer
it. Both questions turned out to be irrelevant: the snapshot already
carries every star's galaxy coordinate, so rendering never needed the
game's view. Reading `renderer.py` and `ships.py` would have shown
that in one pass. Before asking what the other side can do, check
what you already hold.

### Comparison against the original

**Compare side by side before styling.** This method has now found
three separate classes of error that no amount of visual polishing
would have surfaced: the mislabelled field, TURN in the wrong place
with a missing GAME button, and ship icons a size too large.

**Judge new artwork against the original, not against design rules.**
The sidebar icons were criticised for a garish microscope and a
cropped planet — both are in the original exactly like that. The real
deviation was elsewhere and had been missed.

**A defence against a fault the original does not have can BE a
deviation.** Every sort key on the colony summary fell back to the
planet name on a tie, marked as an addition of ours, with a written
reason: the original's bubble sort "leaves equal elements in whatever
order they already had, which for us would mean a list that
reshuffles between frames". Half of that was right and the
conclusion was wrong. The bubble sort swaps only on a strictly
positive comparison (colsum.cpp:363) and `cmp_` returns 0 on
equality (colsum.cpp:1056), so it is stable; the colonies arrive on
the wire in `MOX::_colony[]` order (ext_api.cpp:94), the original's
own list is filtered out of the same array in the same order
(colxport.cpp:91), and Python's sort is stable too. The stability
was already there, along the whole chain, and the fallback was
buying nothing — while ordering ties the original leaves unordered,
so two equal colonies sat alphabetically here and in array order
there.

No value on either screen was wrong, which is why it survived: the
only symptom is two rows in a different sequence, and that is the
kind of difference a side-by-side finds and a table of numbers never
will. **Before adding a guard against somebody else's code, follow
the value through every file it passes** — here four, of which the
one that sorts is only the third. A guard justified by an assumption
about code you have not read is a deviation with a comment on it.

**Sometimes the honest answer is "the original could not do it
either".** Star size steps 3 and 4 differ by 9 %. Chasing legibility
there would mean inventing a deviation and calling it a fix.

**An effect the original is technically incapable of is an invention,
and inventions must be marked.** The black hole faded between alpha
165 and 255 on a 4.8 s sine. Nobody had written down where it came
from, and it came from nowhere — MOO2 draws palette-indexed and has
no alpha blending at all, so `Advance_Black_Hole_Animation_` can only
step sprite frames. The pulse was four times faster than the rotation
it was layered over and read as breathing. Deleted. The test for this
class of thing is cheap: ask what the original would have had to do
to produce the effect, and if the answer is "it couldn't", the
constant needs a source or it needs to go.

The same test decided the message popup's fill: opaque, no dimmed
backdrop, because a palette-indexed engine cannot dim one.

**Game text is not a string.** MOO2's help bodies carry `FMTPARA`
control codes — `\a` function sequences, `\r`, `\t` — and the
Command Points table is not made of spaces but of absolute column
positions (`\aX3.Frigate\aX97.-1`). Printed verbatim they appear on
screen as literal `X97.` runs with the DEMO font's watermark where
the `\a` was, and the table collapses. The extractor's first version
also "cleaned" each line with `rstrip()`, which looks harmless and
silently eats the trailing `\t`, `\v` and `\f` that carry layout.
Two rules came out of it: **a tool that moves game data moves it
byte for byte**, and interpretation belongs where it can be fixed
without re-running the tool. The general form is the one this
project keeps relearning in new costumes — the bytes meant something
that the reading code did not know about, and the symptom was
cosmetic rather than a crash.

**Scaling twice looks correct at the resolution you tested.**
`box_font_scale` multiplies a box's stored value by `win_h / 1080`
and `Layout.font_size` multiplies by the window scale again. For a
box whose value was hand-tuned per resolution that is exactly what
makes the tuning land; for one that has to be right at resolutions
nobody tuned it is a double scale. The help popup rendered at twice
the intended size at 3840x2160 and looked perfectly fine in the 4K
screenshot on its own — the fault only exists in the comparison.
Anything that must work at an untuned resolution reads the stored
scale directly.

**A PATTERN IN THREE OBSERVATIONS IS NOT A RULE UNTIL THE WRITER
SAYS IT IS.** A pop move appeared to change "always the next index" —
colony 10 took 11, colony 11 took 12, three times running, which is
the kind of regularity that invites a theory. There is no index
relationship at all: the player has **five** needy colonies (5, 7,
10, 11, 12), `needy_colony_indices` is filled in index order and the
three distribution passes walk it round-robin, so whichever colony
sits at the margin of the allocation is the one that moves — and it
happened to be one above the moved colony each time.

This is "read the function that BUILDS the thing" applied to a
PATTERN rather than to a value, and it earns its own line because the
failure is a different one: there, an inferred call chain stood in
for evidence; here, a real measurement repeated three times stood in
for a mechanism. Every observation was correct and the rule drawn
from them did not exist.

**A TOOL THAT READS A SAVE IDENTIFIES IT BEFORE IT REPORTS. A proof
that does not say what it is about is not a proof.** Three acceptance
runs of the pop move were produced on 7 September 2026 and every line
of them was true: the clicks landed, the held cluster matched the
prediction, exactly one colony's bytes changed, every pop word agreed.
None of it was evidence about the reference save — the game had a
different galaxy loaded, and nothing in the run said so. The
identification cost three lines of code and the run had gone without
it since it was written.

It is the sibling of the line below and NOT the same fault. That one
is about a result that varies with the reader's disk; this one is
about a result that is perfectly stable and silent about its subject.
A run whose output would be identical on the wrong data is the more
dangerous of the two, because nothing about it looks provisional.

`colony_move_hd.py` now names the fixture — stardate AND star count
AND colony count, since 3502.4 and 3502.5 are one tick apart and any
game reaches them — and stops with what it saw. The status document
had already required that "anything below that reads a save reads it
by its fixture name"; the rule existed and the tool did not obey it,
which is what makes this a line here rather than a note there.

**AND IDENTIFYING THE SAVE IS NOT THE SAME AS THE SAVE BEING
UNCHANGED — 9 September 2026, and the fingerprint above is what made
the gap invisible.** `identify` reads stardate, star count and colony
count. Not one of the three moves when a pop changes job, so a save
that has been written to reports "fixture: reference" on every line,
for as long as it takes somebody to notice.

Something did write to it. The drop sweep's `--scan` tries a round
trip — move, move back — for every (row, source, target) the save
offers, to find one it can sweep from. **Every one of those probes is
a real move**: there is no dry run for an injected click, the game
acts on it. Round trips that did not restore exactly were reported
and the loop CARRIED ON, so each one left the fixture further from
where it started; thirty configurations later Blucher II held eleven
farmers and two scientists where the save has twelve and one.

Three things generalise, and the second is the one that was actually
missing.

**A diagnostic that injects is not a reader, and the two need
different guards.** The rule this project already had — a tool that
reads a save identifies it — is about the INPUT. A tool that drives
the game also has an OUTPUT into the thing it is measuring, and
nothing covered that. `tools/fixtures.verify_colonies` now compares
every colony record against the `.GAM` on disk before a run starts,
and refuses to begin from a drifted one.

**The authority has to be a file, not the first reading.** Comparing
the state at the end of a run against the state at the beginning
would have passed here, because the drift accumulated ACROSS runs.
MOO2 writes the colony array uncompressed and a freshly loaded slot
matches it byte for byte, so the save itself is the reference; the
offset is stored per fixture and **gated on the file's sha256**,
which is what separates a checkable constant from a magic number —
a different file cannot be sliced at 607 and believed.

**And a loop that reports a failure must decide whether to continue.**
This one printed `exact=False` and went on, which reads as diligence
and is the opposite: the first configuration a probe cannot return
from is the last one it may try, because every further probe is
measured on a state the previous failure created. The scan stops
there now and says to reload, and the rows it already printed are
still the answer it was asked for.

The cost was one reload and no data: the `.GAM` on disk is never
touched, because the game only writes it on save. That is luck about
this particular tool, not a property of the class — the same fault in
something that saved would have been permanent.

**And the obvious fix was tried and is only half a fix, which is the
part worth keeping.** Predicting whether a round trip can return —
instead of moving to find out — is cheap: the restore takes the
target column's last icon, `Get_Cluster_` scans to the end of the
array, so it returns the pop that went only when that pop's index is
above every one already there. Measured against the probing run's own
results, **17 of 19 agreed and both misses were in the unsafe
direction**: predicted returnable, measured not, both scientists to
farmers, both leaving bytes changed OUTSIDE `pop[]`.

The leading explanation is already in section 3 — `Send_Cluster_`
always ends in `Pass_Out_Imports_`, which rewrites `imports[
ECON_FOOD]` on every non-outpost colony and three more fields on
every needy one, and an undone move need not land the distribution
passes back on the same numbers. **It is an explanation and not a
measurement**, because separating the two costs a run on a save that
is already drifting, and that was not spent.

So: a predictor that models one cause of a failure is a FILTER and
never a guarantee, and the thing it is a filter for still has to be
checked afterwards. Writing it as `may_return` rather than `returns`
is not pedantry — the first name states what was proven, and a tool
that acts on the second would have drifted the fixture on exactly the
two cases the predictor got wrong.

**A test that reads the user's disk answers differently for the
user.** The check separating "no help file" from "no such entry"
built its two states by loading the real file, which does not exist
in the repo — and would have started failing the moment somebody ran
the extractor. Both states are now forced. A smoke test whose result
depends on optional local data is a test that fails for the person
who followed the instructions.

**A trick that works on one screen is not a rule.** Custom Race's
message box fills itself from its own screen's background, and the
reasoning written down for it — "no sampled RGB constant can go
stale" — reads like a general principle. It is not. It works there
because Custom Race sits on the flat cockpit texture, so cutting the
texture back out reads as bare backdrop with the panels lifted off.
The help popup reused it verbatim and was **invisible** over the Main
Menu artwork and over the star field: blitting the background back at
the same coordinates reproduces exactly what was already there. The
popup now fills from `background_cockpit.png` on every screen. What
caught it was rendering all three screens to PNG and looking — the
code was correct, the assumption underneath it was not, and no test
that checked "the popup drew ink" would have failed either.

**Marked inventions are allowed; unmarked ones are not.** The home
ping, the free HD zoom and the Empire Identity progress box are all
things MOO2 cannot do, and all three are shipped. What separates them
from the deleted pulse is that each says so in its own module, in the
status document, and in a test that fails if it silently disappears.

The progress box is the clearest case of an invention the HD frontend
*owes* the player rather than merely allows itself: MOO2 shows nothing
while it generates the galaxy because the player is looking at the
game's own screen and knows the click landed. An HD screen that stays
up across a wait the original never had to explain has to say what it
is waiting for.

**The original swaps sprites, it does not scale them.**
`Draw_Scaled_Star_Picture_` draws at native size whenever
`scale_percent >= 100`, which is always in a vanilla game. Six
drawings per class exist precisely so nothing has to be shrunk.

**Zoom and star size are the same axis.** Added into one 0..5 index —
which means "large" and "small" are not absolute sizes, and it is why
size becomes unreadable when zoomed out, in the original too.

