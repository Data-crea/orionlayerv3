# The fundament, part 8 of 9 — Diagnosis and refactoring

How a fault is found when nothing looks wrong — Diagnosis, Refactoring.

**Decisions in this part:** no decisions.

The index is [`../v3_fundament.md`](../v3_fundament.md), and it is
what to read first. This file is one part of the fundament and
carries no rule that is not in it; the text below is what stood in
`doc/v3_fundament.md` before work order 164 moved it, unchanged.

<!-- fundament-body -->
### Diagnosis

**Two failure modes can look identical.** Missing icon files log a
warning; a stale `layout.json` logs nothing at all, because an empty
config means the loop never runs. Any config-driven feature must be
checkable by a grep, not only by looking at the screen.

**A fault that only exists in motion needs a test, not a look.** The
black hole drifted up to 2.9 px over its rotation and every single
frame was correct in isolation, so no screenshot could show it. The
test measures the event horizon's centroid across all 72 frames and
demands they agree — which is only possible because the horizon is a
disc on the axis and therefore cannot legitimately move. Find the
part of the thing that must stay still, then assert that it does.

The anchored zoom is the same shape of test: the galaxy point under
the cursor pixel is what must not move, so that is what the smoke
test pins, to under 0.01 px across six wheel ticks. The star *centre*
is deliberately asserted loosely — it sits a fraction of a native
pixel off the integer cursor position, and that fraction legitimately
magnifies with the zoom. Assert the invariant, not the thing that
merely looks like it.

**A later draw can erase an earlier one, and every number stays
right.** The colony list's "No Farming" label was drawn at the left
edge of the allocation bar and the worker squares were then painted
over it. All seven rows matched the original in name, order, flag,
population and job split — the comparison table was green in every
cell — and the label was nowhere on screen. No test that checks
values can see this, and neither can the pixel check that shipped
with it: that one measures whether the bar stays inside its area,
which it did. The class is the same one the help popup taught (see
"A trick that works on one screen is not a rule"), reached by a
different route: there the drawing reproduced what was already
underneath, here it was covered by what came after.

The consequence is the one that entry already names, stated as a
rule rather than as a story: **render every new renderer to PNG and
look at it before a green table counts as evidence.** A table says
the data is right. Only the picture says it is visible.

**And the third costume: the background you see is not always the
background that is set.** The colony summary's galaxy inset was
measured against the original, given `galaxy_inset_fill` in
`layout.json`, marked, documented and accepted — and stayed panel
blue in the running game for a day. The value sat inside the
`panels` block; the lookup read the TOP level of the same file, found
nothing, and fell back to the default. Nothing raised and nothing
could: a panel without its own fill is the normal case, so a missed
key is indistinguishable from the default it produces.

Two things generalise. **A lookup whose miss returns the common case
cannot report a typo, so something else has to** — the check now
asserts that every `<name>_fill` key names a panel in the same block,
which is the assertion the absent key could not make for itself. And
**a measurement justifies a value, never a result.** The measurement
here was right, the value was right, the document said the inset was
black on the strength of both — and the only thing that could have
told them apart was a sample of the rendered frame, which is now
what the check takes and what the acceptance shows.

**Assert the rule, not the instance.** The New Game panel-skin check
does not list which panels carry which skin; it asserts that every
`inner_panel` box sits inside a `thin_border` box. A renamed or newly
added panel still has to obey it, and nobody has to remember to
update the test.

**A CHECK THAT READS THE PLAYER'S OWN FILES PASSES ON THE MACHINE
THAT WROTE THEM.** Four times — 13 September (`d3d0561`), twice in
one run (`5402b7d`) and 20 September (`58b2808`) — a smoke check
asserted on data that exists only where an extractor has been run.
Each stayed green here and went red in a clone, and each was caught
by the fresh-clone run before a push, never by the suite.

**The finding is that prose does not stop this one.** The third
occurrence walked into a trap described in the paragraph *immediately
above the list it should have edited* — the session read the warning
and added the file to the wrong list anyway. A fifth entry saying
"remember the clone" would be the fourth thing of its kind to fail.

So the shape of the answer is not a reminder, it is that the fault
cannot be written:

* **A check needs content, not the player's content.** Where a check
  only needs a name to render, the suite hands it a committed
  stand-in, identical on every machine. There is then no absence to
  branch on and no machine-dependent version to write.
* **The checks that are about the loader force both states**, present
  and absent, the way the Fleets ship picture's fallback is forced —
  a fallback nobody exercises is where this rots, and the session
  writing the code always has the files.
* **The registry is the gate and must be complete.** One list names
  every file derived from the player's install
  (`tools/setup.py:from_game()`), and it is two-way: every extractor
  is named by it or is excepted with an output that is really
  tracked. It had two holes when that check was first written —
  `kentext_en.json` and the Fleets gamedata — so a clone was never
  told to run either extractor, and anything keyed on the list had a
  hole the same size.
* **The fresh-clone run stays**, and it is the gate rather than the
  design. It has caught every occurrence, which is the argument for
  keeping it and not the argument for relying on it.

**AND IT CAUGHT THE CHECK THAT ENFORCES THIS RULE**, four commits
after the rule was written. `git check-ignore` cannot tell that a
bare path is a directory without looking at the disk, and the
registry names one — `nebula_ref`. The ignore rule for it ends in a
slash, so the query matched here, where the directory exists, and did
not match in a clone, where by definition it does not. Green on the
machine that had extracted it, red everywhere else: the exact shape
described above, written into the checker for it. **Nothing about
knowing the rule prevents this** — which is the whole point of the
entry, and the reason the last bullet is not negotiable.

**A skip condition is part of the assertion, and it has to name the
right thing.** That same check skipped a resolution whose box list
was *empty*, standing in for "1080p has no panel frames yet". Adding
one unrelated box — the help popup's rect — made the list non-empty,
and the test started demanding panels from a resolution that has
none. The guard now keys on the absence of panel-skin boxes, which is
what it always meant, plus an assertion that at least one resolution
does define them, so the skip cannot quietly become universal. A
proxy condition holds only until something else changes the proxy.

**And a proxy can be broken by your own habits, not by an edit.**
The ~300-line guideline was read off `wc -l` for as long as it
existed, on the proxy that a long file does a lot. This project
writes the reason for every value next to the value, so its files
grew long in DOCUMENTATION — and the proxy came apart quietly and in
one direction. Measured on 4 September 2026: of 25 files over 300
total lines, 17 were under 300 lines of code, and the ranking
INVERTED — `custom_race/screen.py` was 558 total against
`colony_summary/screen.py`'s 666, and 400 code against 252. A reader
working the list from the top would split the wrong file first, and
one did: `colony_summary/screen.py` was split for a number that never
applied to it.

Same shape as the entry above and worth stating separately, because
the trigger is different. There, something else moved the proxy;
here, nothing moved at all — the proxy was measuring a quantity that
had slowly stopped meaning what it was chosen to mean. The tell was
available the whole time and nobody asked for it: **the number a
guideline is enforced on has to be the number the guideline is
about**, and if it is a proxy, something has to re-check the proxy
occasionally rather than the values it produces.

**A PREVIEW THAT CONSTRUCTS IN ONE SIZE CANNOT SEE A RESIZE FAULT —
the check has to go the way the fault went.** 9 September 2026, the
colony list's six column boxes.

`colonytrack.columns` read each column's left edge off
`Box.screen_rect`, a DEVICE coordinate that `Box.update_layout` writes
once per layout change. `colonyheader.install_columns` bound those six
Box objects into the screen's `list` block at `enter()`, and
`ScreenBase.on_resize` calls `_reload_boxes`, which REPLACES
`screen.boxes` with freshly parsed objects. So after any resize the
table held six boxes the screen no longer had, laid out for the window
it was entered at, while `list_area` and the frame image — both
resolved through `Layout.rect` every frame — followed the new one.
`settings.json` starts every session at 1920x1080 and F9 resizes from
there, so **every window size except the start one was wrong, and the
start one was right.**

What it looked like: the NAME text clipped on the left (the column
stayed at device x 105 and the frame's left rail was then drawn over
it), the header plates at the 1080p x at every size, the columns
sitting on the letterbox bar OUTSIDE the frame at 3440x1440, and
`col_scroll` — the last column, sized as the remainder — running from
35 px to 635, 1075 and 1837.

**The suite already had a check for exactly this property, at twelve
window sizes, and it passed throughout.** It builds a `Layout`, calls
`load_boxes`, calls `update_layout` on each box and asserts the six
tile `list_area` with no seam — which is true, at every one of the
twelve, of a screen CONSTRUCTED at that size. The fault was not in
what the geometry computes; it was in an object's lifetime. A fixture
that constructs at its target size has no lifetime to get wrong, so it
cannot fail the way the app failed, and twelve of them cannot either:
the blind spot is not made smaller by more sizes, because every one of
them is the same shape.

Two things generalise, and the second is the transferable half.

**A check whose setup differs from the app's own path is testing a
different program.** The app enters at one size and resizes; the check
entered at the size and stopped. That difference was invisible because
both produce a correct screen — the state under test was never
reached. So when the app has a SEQUENCE (start, resize, resize back),
the check walks the sequence, and asserting the rule in the end state
only is not the same claim.

**And a device coordinate is a value with a lifetime, which is the
thing to hunt for.** A reference coordinate is resolution-independent
and cannot go stale; `int(x * scale + offset)` is true of one window
and silently false of the next. The fix was not to refresh the cache
but to stop holding one: a column is now a FRACTION OF THE `list_area`
CUTOUT, mapped through the same rect the frame goes through, so both
edges of every column are recomputed from one source every frame and
the tiling is exact by construction rather than by two roundings
agreeing. **Anything that stores a window coordinate across frames
owes an answer to "what invalidates this?", and "nothing, it is
recomputed" is the only cheap one.**

The sibling failure is one file over and was found in the same pass:
the smoke test's own column fixture carried a hand-tiled copy of the
same arithmetic for the synthetic-area case, agreeing with
`colonytrack` by construction and prepared to go on agreeing with a
broken one. Decision 5's "a tool is a reader too", second instance.

**A diagnostic should degrade, not crash.** `star_icon_check.py` once
died with an AttributeError, which reads like a broken script when it
actually meant "the update never landed".

**A recovery mechanism can be the fault.** OrionLayer kept losing the
Empire Identity chain: the game stood in "Enter home star name" while
HD had fallen back to Custom Race. Nothing in the chain was wrong. The
connection watchdog reconnected after 3 s of silence, and the silence
was the galaxy being generated — `ext::Tick()` runs from
`Get_Input_()`, and mapgen has no input loop. The fresh connection
then missed the FIELD_LIST the last step was waiting for, because
`ext_api.cpp` resends the list only on a field-count or screen change.
Two rules came out of it: **silence is not death**, so anything that
knows the game is about to go quiet holds the watchdog open; and **a
reconnect drops its field list**, because a list from a dead
connection describes a dialog the game may have left several times
over, and a stale list is a lie the caller cannot detect while an
empty one is a state it can handle.

**Log with timestamps.** Violated for months in `main.py`, which is
how a 24-second gap could sit in the Empire Identity chain without
anybody being able to say where it was.

**A fresh message is not a fresh world.** The sharper form of "a new
message is not a new picture", and it is not the same lesson: there,
two channels were mistaken for one and the fix was to wait on the
right counter. Here BOTH counters move and both move too early.
`ext::Tick()` runs `ProcessInput()` before it serializes anything
(ext_api.cpp:341-386), so the message that follows an injected
command was built from the world before the game acted on it — the
command has only been handed over. Measured 5 September 2026: one
increment of the colony list's window read the old `_first` on the
first state/visual pair and the new one on the second, every time.

Waiting for "a fresh snapshot" therefore reports a step that worked
as a step that did not, which is the cheap direction exactly once —
the next step then aims at a state that has since moved. The rule is
to wait for the EFFECT the step must have, with a floor of one
pre-effect message. The floor and the whole argument for why a COUNT
is admissible under decision 21 live in
`core.wire_protocol.EFFECT_PAIRS`; there are two wait SHAPES, a
blocking one in the tools and a frame-driven one in the screens, and
they cannot share code, so the smoke test asserts the rule on both
rather than assuming it travelled.

**THE FINDING IS BIGGER THAN THE SCREEN THAT PAID FOR IT, so every
observe-then-send loop in the tree was audited on 5 September 2026.**
The result is written out because "it was checked" is otherwise
unverifiable, and because three of the four survive for reasons worth
copying rather than by luck:

- `galaxy_map/viewctl.park_game` — SAFE, structurally. It stops on
  an ABSOLUTE target (`map_scale >= fit`), never on a comparison
  with the previous reading, so a pre-effect snapshot costs it one
  redundant zoom-out step and cannot make it stop half way. The
  throttle is wall-clock and only spaces the steps. A smoke check now
  feeds it the same stale state repeatedly and fails if it ever
  concludes "nothing moved".
- `core/injection.py` `InjectionChain` — SAFE, twice over. It waits
  on the FIELD_LIST, which `ext_api.cpp` only sends when the field
  count or the screen changed, i.e. after the game acted; and it
  compares the list's SIGNATURE against the one it fired on, so an
  identical list does not advance it. That is the same shape as the
  new floor-plus-predicate, arrived at from the other direction.
- the fire-and-forget injections — the sort keys, RETURN, the New
  Game toggles, `original_view.forward_click` — are not affected at
  all: nothing observes to decide a next step. What they do assume
  is that the send worked, which is a separate question and is
  answered separately (decision 39's live check for the sort keys).
- `tools/zoom_probe.py` — WRONG, and it was being cited as the
  example to copy. See the entry above under decision 21's rule.

Two things this audit is not. It is not a claim that nothing else
will ever grow such a loop: the rule is the deliverable, and the
smoke checks are what make it survive. And it is not a claim that
the surviving three were designed against this fault — they were
not; they are safe for their own reasons, and writing down WHICH
reason is what lets the next reader tell a safe loop from a lucky
one.

**A wait needs its traffic, not just its duration.** "The game is
busy" and "we are not asking it to do anything" produce the same
frozen screen and the same elapsed seconds. What separates them is
what arrives on the socket meanwhile: snapshots pouring in mean the
game is running its input loop and the client is the slow side.
`InjectionChain` therefore reports state/s, visual/s and KB/s beside
the elapsed time, and `GameClient` keeps monotonic counters for it.

**An injected click on a live game is followed by a picture before the
next one.** Read the framebuffer after every click and decide the next
click from what it shows; two clicks without a picture between them are a
blind sequence, and the game may have moved under the second — a dialog
opened, a confirmation appeared, a turn advanced. Source: work order 122,
16 September 2026, where a loop clicked CLOSE at a fixed native point until
the map came back, a click turned a colony-base choice into "Really trash
your colony base for 100BC?", and the colony base of the loaded scratch game
was scrapped (in memory; no save file changed) before anybody looked.

**A LIVE DRIVER IS A CLIENT, and is bound by the rule the product is:
identify the dialog from the list you just read, or send nothing.** Filed
17 September 2026 (work order 129 A) from two incidents, a month apart in
kind and identical in shape. Work order 122: a loop clicked CLOSE at a
fixed native point until the map came back; one click turned a
colony-base choice into "Really trash your colony base for 100BC?" and the
scratch game's colony base was scrapped (in memory) before anybody looked.
Work order 128 C: a driver saw screen 0 with a message box's field list,
decided from that reading a moment later, and sent `ACTIVATE_FIELD 1` into
the turn-start research prompt — which commits the row under the POINTER
(tech.cpp:354-369) and, with the pointer over none, dereferenced null:
orion2re died with SIGSEGV (open fix 23, "Activating a research choice row
by field id crashes the game — an observation").

Neither tool was careless about reading the screen; both decided from a
reading that was one step old. So the rule is not "read the framebuffer
after every click" — that one already existed and both obeyed it — but
where the DECISION comes from: the field list of the state being sent
into, at the moment of sending. `tools/livesend.py` is the one home for
it, over the shape tests that already exist (`mapboxes.live_field`,
`game_menu.nodes.classify`), and it RAISES rather than returning False: a
tool that cannot say what is on screen has nothing to send, and carrying
on regardless is precisely what both incidents did.

**A COUNTER-TEST THAT RESTORES A FILE CAN BE MEASURING THE MUTATION.**
17 September 2026, work order 128 B. A check was shown red by editing one
character (`GAME_SCREEN_ID = 51` -> `50`) and the file was restored with
`cp` — same size, same second — so Python's mtime-and-size check accepted
the stale `__pycache__`, and the next run, the one meant to prove the tree
green again, quietly ran the mutated bytecode and failed. The rule: clear
the caches (`find . -name __pycache__ -not -path './.git/*' -exec rm -rf
{} +`) or run the mutated suite with `python -B`. It belongs beside "a
measurement that is not stable under its own threshold": there the
instrument was too coarse, here the instrument was measuring a different
program than the one on disk — and a red/green demonstration that silently
measures the wrong code is worse than none, because it is the evidence
everything else rests on.

**On the colony screens a right click is help, not cancel.** Over a help
region the game draws the entry and swallows the click (section 3, "A right
click is not always Cancel"; the colony screen's table is transcribed in
brief 99, which the chat called "Brief 98"). A live run that right-clicks
there to back out opens a help panel instead; it is closed with a LEFT click
beside the rows, and the picture after it confirms the panel is gone before
the next input. Filed by work order 126 from the 16 September 2026
handover, where it was already part of the live protocol.

**A permanent smoke test pays for itself immediately.** Run it after
every step, not only at the end — a change touching six files breaks
screen loading in a way the test catches in seconds.

**A READER WHOSE EXTENT COMES FROM THE SAME TABLE AS ITS CONTENTS
CANNOT REPORT A WRONG EXTENT.** `fixtures.fixture_colonies`
(`tools/fixtures.py:169-196`) slices `colony_count` colony records
out of a savegame and returns them. The count is the input AND the
implicit expectation, so a wrong count returns fewer records and no
error at all — not a warning, not a short read, a clean answer of
the wrong length. `FIXTURE_FILES["natives"]["colony_count"]` said
36 where the file holds 38, and record 37 was **Urna I**, the only
colony in any fixture with native pops and the colony the fixture is
NAMED for. On 10 September 2026 that produced the finding "no
fixture has a native pop, so the native refusal cannot be
live-tested", from a file with three of them, and it was one
sentence away from being filed on the open acceptance list as a
missing savegame. **What caught it was a second source and nothing
else**: the running engine's own `num_colonies`, which reports 38 on
a fresh load. The rule is not "count more carefully". It is that a
number describing a file must be checkable against something that is
not the same table — and where the only honest second source is the
running game, the offline path has to say it is unverified rather
than answer as if it were.

**AND THE GUARD THAT WOULD HAVE CAUGHT IT EXISTED AND HAD NEVER
RUN.** `verify_colonies` (`tools/fixtures.py:210-213`) compares the
engine's record count against the file's and refuses on a mismatch;
pointed at this save it says "the game reports 38 colony records and
the file holds 36" and returns False, which is exactly right and was
true from the day the number was written. It had simply never been
run against a loaded `natives` save — the measuring runs all used
the reference fixture, whose count was correct. **A guard that
exists is not a guard that ran, and a fixture nobody verifies is a
fixture nobody has checked.** The check now runs on every fixture
the smoke test can reach, offline, against the file's own length.

**A FUNCTION THAT FAILS BY RETURNING `None` FAILS INVISIBLY.**
`fixtures.fixture_name` (`tools/fixtures.py:45-57`) fingerprints a
snapshot against the fixture table and returns the name, "or None".
While the count above was wrong it returned `None` for the natives
save — it could not identify a save that was sitting right in front
of it — and **nothing treated that as a fault**. Callers print it,
put it on a provenance band, and carry on; `None` renders as "not a
known fixture", which is a legitimate state a caller has no way to
tell apart from "the table is broken". That is why the wrong count
survived: the one function positioned to notice it reported the
problem in the one way nobody reads. The rule: **where a caller
cannot distinguish "no answer" from "not asked", do not return the
absence.** Raise, or make a check demand the answer. A sentinel is
only honest when the caller is known to branch on it, and "or None"
in a docstring is not evidence that anybody does.

**Revert to a known-good baseline when regressions pile up.**

### Refactoring

**The third copy is the signal to extract.** A palette wrapper had
been pasted into six modules, two of them inside the *same* screen.
Two independent grid-layout implementations were separately written
arithmetic for "N items into a rect". The thin blue border was a
hand-written `draw.rect` inside Custom Race until the popup and New
Game wanted it too.

**Except where redundancy is the point.** `ext_diag.py` re-derives the
FIELD_LIST offsets by hand instead of importing the shared parser.
That is the two-independent-sources rule, deliberately left alone.

**Method renames need a full-project grep.**

**Byte-identical output after a refactor proves only the paths that
were EXERCISED.** It is the strongest evidence this project has and
it is evidence about a sample, not about a function — and the sample
is whatever the fixtures happened to reach. `core/lbx.py` inherited
`read_palette` from `nebula_extract.py` verbatim; it read
`r, g, b, changed` where `s_palette_entry` is `{changed, r, g, b}`
(orion2.h:2131-2136), so every colour it returned was one byte to the
left and COLSUM entry 0's white came back as cyan. Every regeneration
in between was byte-identical, and the reason is the whole lesson:
**not one of STARBG.LBX's 48 nebula entries carries a palette at
all**, so the function had never once run on real data. Nothing was
identical *because* the code was right; it was identical because that
branch was never taken.

So a byte-for-byte check licenses the refactor over the inputs it
saw, and the useful question afterwards is which inputs it did NOT
see. Where the answer is "a whole class of them", the check owes that
class a fixture — the palette byte order is now pinned against the
struct with a non-zero flag byte in the fixture, precisely so a wrong
order cannot pass by being unreachable. A test whose data cannot fail
it is a test the tree defends.

**Data-driven screens are translation-ready for free.**

---

