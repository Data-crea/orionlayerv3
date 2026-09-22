# The fundament, part 2 of 9 — The orion2re boundary

Everything that crosses to the engine: field input, struct offsets, injected clicks, what ships and what does not, and the deviations the boundary forced.

**Decisions in this part:** 20, 21, 22, 23, 24, 25, 33, 35, 36, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 52, 59, 60, 62.

The index is [`../v3_fundament.md`](../v3_fundament.md), and it is
what to read first. This file is one part of the fundament and
carries no rule that is not in it; the text below is what stood in
`doc/v3_fundament.md` before work order 164 moved it, unchanged.

<!-- fundament-body -->
### The orion2re boundary

**20. Field IDs for input.** `ACTIVATE_FIELD` for field types 0, 7 and
13. `INJECT_CLICK` only for radio buttons (type 1) and free map
clicks — and only at a 640x480 window, or with the coordinate fix,
because `platform.cpp` maps injected (x, y) as *window* coordinates.

**21. Dialog chains are event-driven, never timed.** A step waits for
the field-list shape of its dialog and moves on only when the list has
changed again. `Get_Input_()` consumes one key per frame, so anything
sent "after a short delay" races with the typing.

**22. Graceful fallback.** An unknown screen ID falls back to the
original framebuffer, so the game is always playable.

**23. Struct offsets only through `core/structs` specs, and only
verified ones.** Verification means numeric agreement with live data
via `tools/struct_probe.py`, or compiling orion2re's own header with
its `#pragma pack(1)` and matching the assert in `sizes.h`.
Unverified specs are quarantined in `structs/unverified.py`.

**The header route carries as far as the byte layout and stops
there.** `offsetof` and a satisfied `sizes.h` assert fix where a
member begins and how wide it is; they say nothing about the meaning
of bits *inside* one. `s_planet_data` is whole members throughout, so
the header carried it end to end and `planet.py` is verified on that
alone; `s_colony` carries the same way up to `pop[42]`, whose five
fields are masks in `pop.h` — orion2re's own reading of what the
original packs into that word, which no size assert can check. (They
are explicit masks on a `uint32_t`, not C bitfields, so the
implementation-defined ordering rule never enters into it; the gap is
that a transcription of *meaning* is not a measurement of *layout*.)
A packed word inside an otherwise verified struct is its own claim
and needs its own second source — `doc/s_colony_offsets.md` is Phase
A of exactly that, and says so in its own last section.

**24. Ship icons are positioned by orion2re, not by us.**
`s_ship_icon.x/y` are finished 640x480 top-left coordinates.
Re-deriving the orbit slot geometry from `Get_XYs_For_Orbiting_Ships_`
would duplicate logic that can only drift. Under a decoupled HD
viewport those coordinates are **re-anchored, never re-derived** (see
35): which ship sits in which slot, and where that slot lies relative
to its star, still comes from `Build_Ship_Icons_`.

**25. Reconstruct derived state before asking for a patch.**
`MOX::_ship_node[]` looked like it had to be serialized; it is a pure
function of `_ship[]`, which already is. Anything reconstructed must
carry a validation the data itself provides — otherwise it is a guess
with extra steps.

**33. Refuse input the game would refuse, before sending it.** An
input orion2re rejects is answered in the framebuffer, which an HD
screen cannot see — so it does not know the click failed, and any
screen switch it made on the strength of that click is already wrong.
Custom Race Accept on a negative pick balance is the first case: the
condition is tested in HD, no `ACTIVATE_FIELD` goes out, and the
message is drawn in HD instead. The cost is a second copy of a rule
the game already owns, so this only applies where the rule is one
comparison and the failure is silent; anything larger belongs on the
C++ side or not at all.

**44. A frame cutout narrower than the original's proportion is a
DEVIATION, and the clamp that absorbs it must be able to expire.**
The colony summary's sidebar draws its six values right-justified
against a column whose width the original states: 104 native px of
640 (`colsum.cpp:418`), which is 312 reference px. The `sidebar`
cutout gives 286, less 8 reference px of `text_inset` on each side,
so 270. The renderer takes the smaller, so **the clamp fires at
every resolution** and the original's proportion is never the one
drawn — 13.5 % of the column, every value 42 reference px left of
where the transcription puts it.

**The inset is not a widening of the deviation; it is the deviation
being measured properly** — corrected 4 September 2026. The 286 was
never a column a reader could see: `frame_holes.to_ref` adds
`BLEED = 2` reference px outward on each side so panel FILLS cover
the anti-aliased rim, and the artwork's rim reaches further in still,
so 7 or 8 reference px of that 286 were always under metal. Every
label on the panel was drawn with part of its first letter beneath
the frame and every value lost its last pixels at the other end, at
every resolution, for as long as the panel existed. It was reported
as a resolution-dependent glitch — clear at one window size, clipping
the R of RESERVE five pixels later — and it was not: what changes
with the window is the font size meeting a constant overlap. Now the
inset is declared, the number above is what is legible, and a check
asserts against the frame's own alpha that no glyph starts or ends
under it.

The alignment is transcribed and the width is not, and those are
marked separately. A deviation that is live in every single frame is
the easiest kind to stop seeing, precisely because nothing ever looks
wrong: 286 is a perfectly reasonable column, and the only evidence
that it is a deviation is a number in a note.

**The shape of the workaround is the decision here.** The clamp is
`min(cutout, native)` and not a hardcoded 286. The cutout comes from
the frame artwork through `frame_holes.py` and can move; 104 is a
transcription and cannot. Written as a `min`, the deviation ends the
day the artwork gives that hole 312 or more, with nobody needing to
remember it — a workaround that cannot expire is a permanent change
wearing a temporary label.

And the frame art is **not** widened to suit it. That would be
deriving artwork from a deviation to make the deviation go away,
which is the tail wagging the dog and would also make the marking
unfalsifiable. If the sidebar hole should be wider, that is an
artwork decision with its own reasons.

The failure this guards against is not the clamp; it is the native
number being deleted once somebody notices it never wins. A smoke
check asserts `native_width` is still read, so removing it as dead
weight fails the suite rather than quietly ending the marking.

**RETIRED — 12 September 2026, and it retired itself the way it was
written to.** Data's new frame removes the right-hand column
altogether and puts the empire readouts in the lower band, where the
box is 451 reference px wide and 435 usable against the
transcription's 312. `min(cutout, native)` therefore selects the
NATIVE width at all twelve shipped window sizes — measured, the clamp
fires at 0 of 12 — so the drawn column IS the original's proportion
and there is nothing left to deviate from. The marking in
`colonyempire.value_column` says RETIRED and carries the measurement;
the smoke check that held the marking now holds its converse, and
asserts the docstring says DEVIATION again the moment the clamp fires
at any size. The entry stays here rather than being deleted: the
decision it records is the SHAPE — a workaround written as a `min`
that expires on its own — and the shape is what was vindicated. That
it took a new frame rather than a widened hole is the second half of
the entry holding too.

**43. WITHDRAWN, 3 September 2026 — it was built on a one-file word
grep, and the grep was wrong.** (Line numbers here are orion2re
1.60.0, `src/version.h`.)

This decision claimed that `colsum.cpp` sorts the colony list by
food, industry and research while never drawing any of the three per
colony, and concluded that `output_panel` — which is to show those
values for the selected colony — is therefore an HD EXTENSION.

**The original draws them.** `COLSUM::Draw_Colony_Scan_Info_`
(colsum.cpp:1155), called from `Draw_Scan_Info_` (:80) at :485, runs
`for (i = 0; i < ECON_COUNT; ++i) Draw_Colony_Wee_Prod_(_g_colony_n,
i, 106, y_pos, 366, 20)` with `y_pos` stepping 18 — four rows of
icons at native x 106, y 349 upward — plus
`Draw_Info_Wee_Morale_(…, 106, 421, 366)`. That path lands in
`COLDRAW::Draw_Colony_Prod_Both_` (coldraw.cpp:36), which reads
`colony->production[prod_type]` (coldraw.cpp:60) and draws it as
tens-and-units sprites. Food, industry, research and BC, per colony,
on this screen, in the bottom-left — exactly where `output_panel`
sits. **`output_panel` is a TRANSCRIPTION**, not an extension.

**Why the grep missed it, which is the part worth keeping.** The
search was `grep -in "food\|industry\|research" colsum.cpp`. The
call site contains none of those words: the value is selected by a
loop index against `ECON_COUNT`, and the drawing lives in a different
file. A word grep finds a concept only where somebody spelled it, and
the engine spells this one as an integer. Searching for the DATA
(`production[`) instead of the LABEL would have found it in one step.

That is decision 44's lesson arriving from the other side: there, one
definition was mistaken for the definition; here, one file was
mistaken for the code path. Both are the same error — a search that
returned something, believed because it returned something.

The rule this entry originally proposed — *the original computing a
value is not permission to display it* — survives, and is worth
keeping. It just has no example here, because on this screen the
original displays them. It kept `output_panel` marked as an extension
for a day and a half, which is exactly how long a wrong marking is
more dangerous than no marking: it was asserted in a smoke check, so
the tree actively defended the error.

**45. Two deviations in the colony row. ONE IS RETIRED, one is kept, both stay written down.**

**The colony NAME was right-aligned; the original left-aligns it — and as of 8 September 2026 so do we.**
`BILL::Squeeze_Formatted_Paragraph_Centered_(0x0C, y_pos,
paragraph_type, 0x17, buffer, 0)` (colsum.cpp:582) forwards to
`_Squeeze_Print_Paragraph_(x, y + height/2, …, center_y=true)`
(bill.cpp:252). `center_y` does nothing but `y = y - height/2`
(bill.cpp:205) — **"Centered_" is the vertical axis only.** The
sixth parameter is `color_or_alignment`, and for a formatted
paragraph it is handed to `Print_Formatted_Paragraph_` as the JUSTIFY
argument (bill.cpp:210). colsum.cpp passes `0` = `JUSTIFY_LEFT`.

It was kept for a real reason: right alignment is what made a 236 px
name column affordable, because overflow grew LEFT into `pad_x` where
nothing was drawn instead of rightward onto the track, and that trade
bought the building column. **The trade ended when the column became
a box.** The NAME cell is 303 reference px of its own now, and the
widest name the game can produce — `WWWWWWW IV`, because
`Do_Change_Star_Name_` caps the input field at the pixel width of
seven W's (namestar.cpp:246-256) on top of the `char[15]` buffer —
measures 174 px. There is nothing to absorb because there is nothing
to overflow, so the alignment goes back to the original's.

What stays is the READING, because it is the expensive half: a
function called `Centered_` is a trap, and a later reader who checks
the call and sees a name that agrees with the word will file the
alignment as transcribed without ever reading `bill.cpp:205`.

**The per-row second line has no per-row counterpart.**
`Draw_Colony_Scan_Info_` draws it ONCE, for `_g_colony_n`, at native
(13, 354, 80, 88), and substitutes seven values into
`E_Strings_(74)`: size, climate, gravity, mineral class, `n_pops`,
computed maximum, growth (colsum.cpp:1196-1205). The HD row shows
three of them on every row. Kept for the same reason as the
allocation bar — it makes comparable what the original could only
show one at a time — and the other four belong in `output_panel`,
which is the HD equivalent of that same box.

The second is marked in `screens/colony_summary/colonylist.py`, here,
and in a smoke check; the first is now a transcription and the check
asserts the ink starts at the column's left edge. Neither ever
changed a pixel of DATA; the point is that the next person reads a
choice as a choice — and that a retired deviation is retired in
writing, not by the marking quietly disappearing.

**46. The list window belongs to the game, and it is re-established
rather than remembered.** The original's colony list has ten SLOTS,
not ten colonies: `_list_col[i] = _g_colony_list_ptr[_first + i]`
(colsum.cpp:348-351), and every clickable field in a row is created
per slot — `Add_Fields_Pop_For_` fills `_list_col_job_fields[slot*3+i]`
at y = `slot * 31 + 34` (colsum.cpp:311-345). So an injected click
names a POSITION IN THE WINDOW; which colony it reaches is `_first`'s
answer and not ours.

The HD list may therefore scroll freely for VIEWING — every colony is
in the snapshot and the game never has to know — but `_first` must
agree with the HD row before anything is injected. Same asymmetry as
decision 35: the view decouples, the click frame does not. And the
failure mode is the same one, which is why it earns its own number:
every value on both screens stays correct and only the click's
destination is wrong, so nothing about the picture reveals it.

**`_first` is re-established, not tracked.** The tempting argument is
the sort key's — a state you establish yourself does not have to be
read — and it does not carry here. `platform.cpp:1379` shows the
game's window is hidden only when `ext::g_hide_window` is set, so a
visible window, which is how this screen was compared against the
original in the first place, lets a human drag the original's own
slider. A remembered `_first` would then be a lie the caller cannot
detect.

Establish with the safe direction, as in 35's corollary:
`Decrement_First_` clamps at 0 (colsum.cpp:211-214), so N activations
of `_x_fields[1]` put the window at the top from wherever it was, and
k of `_x_fields[2]` walk it to the target. Both through
`ACTIVATE_FIELD`, because the handler compares field IDs
(colsum.cpp:790-800) — which also keeps this clear of INJECT_CLICK's
window-coordinate constraint. Sorting is a second way the window
returns to a known place (`_first = 0`, colsum.cpp:832) and not a
substitute for establishing it.

**The refusals are mirrored before sending** (decision 33). With
fewer than ten colonies `_first` never moves at all
(`colonies_count >= num_items`, colsum.cpp:210 and :226), and a step
down is refused unless `_g_colony_list_ptr[_first + 10] != -1`
(colsum.cpp:796). Counting a step the game refused is exactly what
puts the two windows back out of step.

Corollary for the HD side: **HD's visible row count is not the
game's ten.** It is derived from `list_area` and `row_height` and
happens to be ten today. Any future k is computed against the
ORIGINAL's window of ten, never against however many rows HD draws.

**47. A preview does not inject; the commit sends the whole gesture.**
Added 5 September 2026, when the population move became the first HD
interaction that is a GESTURE rather than a button — two clicks, with
a state in between that the player can still change their mind about.

The original's first click is not a preview at all:
`COLMOVE::Get_Cluster_` unassigns the pops there and then
(colsum.cpp:861-870), and the only ways out of a held cluster are
dropping it or leaving the screen, because both `Clear_Cluster_` call
sites on that screen are leave-the-screen paths (colsum.cpp:804 and
:938). An HD preview that mirrored the first click faithfully would
therefore strand any player who changed their mind, on a screen whose
own Cancel does not exist.

So the HD side holds the intermediate state LOCALLY and sends
nothing, and the second click — target known, every rule mirrored and
passed — sends both clicks back to back with each one confirmed
against its effect. The wire sees one atomic gesture or nothing at
all.

Two things follow, and they are the reason this is a decision rather
than a note on one screen:

- **the cancel that the original does not have is bought by the
  first half**, not granted out of kindness. Right-click or a click
  into empty space discards an HD selection precisely because that
  selection is not the game's cluster. The marking has to carry that
  sentence — "we are nicer" is not a reason and would not survive
  the day a preview starts injecting.
- **anything a refusal would have shown must be mirrored** (decision
  33), because the refusal is not silent on the other side: it opens
  a blocking message box over a screen the HD client has left up.
  See section 3.

The shape generalises to every future gesture — a drag on the galaxy
map, a build queue reorder: decide locally, commit once, confirm each
step, and never leave the game in a state only the player can end.

**52. Pop moves go over the wire as one command per colony, and the
command is all-or-nothing.** `MSG_SET_JOBS`: one colony, a list of
(pop_idx, new_job). Run A (brief 91, commit d98a96d) settled the
three facts this rests on. The click chain owned 597 of the 725 ms
per drop (RESORT, ESTABLISH, PICK, DROP) — that is the part a command
removes; the game's own recalculation and one snapshot round trip
stay whatever the transport. The recalculation is per batch, not per
pop: `Send_Cluster_` runs the whole cluster and only then calls
`Col_Calc_Wrapper_` (colmove.cpp:461-464), so a list is the
original's shape, not a convenience. And `Give_Colonist_New_Job_`
answers each of its refusals with a text box that spins waiting for
a human (textbox.cpp:145-149) — a loop that re-enters `ext::Tick`
from inside the refusal, which a command must never reach.

That last fact decides the rest. The handler checks the refusal
conditions itself, before touching a pop, and rejects the whole list
if any entry fails; HD checks the same conditions before sending
(decision 33), so a rejection on the wire is the exception. The
original moves pops until the first refusal and leaves the earlier
ones moved (colmove.cpp:168-173), because a human at the box decides
whether to continue. A command cannot ask, so it does not start.
**This is a marked DEVIATION**: the game behaves differently under
the command than under the click. Data's decision, 10 September
2026.

The command lives in `src/ext/`, our own directory in Joes' tree;
the patch is `doc/ext_move_pop.patch`, its entry is in
`doc/orion2re_open_fixes.md`, and `tools/version_check.py` covers
the new message id. The click chain is deleted in the same session
the command lands — two paths that move pops is the same fault as
two copies of a table.

**59. The GAME popup is one OVERLAY that claims SCREEN_GAME, and its
dialog is read off the field list.** 14 September 2026, Data's decision
on the Stop 1 reading (`doc/game_menu_reading.md`). `LOADSAVE::_Game_Popup_`
runs four dialogs, a confirmation and a warning, and the game reports
screen 8 for all of them; `_screen_data` is not on the wire. So
`screens/game_menu` is `IS_OVERLAY` with `GAME_SCREEN_ID = 8` — the
dispatcher needed no change, `update_from_game` already opens an
overlay bound to an id and closes it when the game leaves — and which
dialog is up is `nodes.classify` over the list: type, hotkey and size,
never index, and **never field 0**, which after a message box carries
whatever geometry the list held before.

**The screen underneath keeps updating, and that is a hazard with a
number in it.** The galaxy map parked the game with `ACTIVATE_FIELD 9`
from `update()`; under the overlay field 9 is the Load dialog's ninth
slot row, which loads at once. It now parks only while the game reports
screen 0. The rule this adds: a screen that sends a field NUMBER from
`update()` must check that the list it was measured against is the one
on the wire.

**60. Save slot names come from the engine, never from a folder of
ours.** Data, 14 September 2026. HD could read the ten SAVEn.GAM headers
itself, and the day HD's folder and the game's differ the names on
screen stop belonging to the slots a click reaches — every name still
plausible, which is decision 35's failure shape. So the list is a patch
(`doc/ext_save_slots.patch`, open fix 14, `MSG_SAVE_SLOTS`) — applied
16 September 2026 and required by `tools/version_check.py`; until then a
row showed its slot number only, marked HD STATE, and without the block it
now shows no invented label at all. The
strings the patch carries are the ones the engine formatted — a year of
126, no month on a first visit — and HD draws them as they come.

**62. A requested end is not a lost connection.** QUIT -> YES makes the
game save SAVE10.GAM and exit (loadsave.cpp:1257-1273). The GAME menu
calls `GameClient.expect_shutdown()` BEFORE the YES goes out: the
watchdog is disarmed, a close or silence then sets `game_ended` instead
of starting a reconnect, and `main.App` ends with the game. No "game
ended" screen. Before, not after, because the silence of the save is
exactly what an armed watchdog reads as a dead link.

**42. Derived artwork ships; unmodified original artwork does not.**
The repository is public, and OrionLayer is a modification that
requires an installed, legally obtained copy of Master of Orion 2 —
the same footing every HD texture pack stands on, and the same one
that has kept them online for decades. The portraits, banners,
nebulae and frames are derived work: upscaled, redrawn, hours of
effort on top of the originals. Those ship, with the copyright in the
underlying work acknowledged in `LICENSE` and in the README.

`nebula_ref/` did not, and the line is exactly there. It held sprites
extracted from STARBG.LBX pixel for pixel, with nothing added — the
one place in the tree where the answer to "what did you contribute to
this file?" was "nothing". It is now extracted at runtime like the
help texts, by the same rule as decision 40.

This is not free. Nothing else in the tree checks a nebula master's
shape or brightness, so a clone without the references cannot make
that comparison. The check states that rather than skipping: present
means every master is measured, absent means the command that fixes
it is named, and the count is the same either way so that "checks
must not go down" stays a rule anybody can follow.

`LICENSE` is MIT for the code and documentation and says, in a
section that is longer than the licence itself, what it does not
cover. A licence that quietly implies ownership of somebody else's
artwork is worse than none.

**41. The display font must be redistributable, and its licence
ships beside it.** The project ran on a DEMO build of Bank Gothic
until 31 August 2026. That was never only an aesthetic debt: a demo
font is not licensed for redistribution, and the moment the tree
became a repository the file would have been published with it. It
also cost real work — the whole per-character substitution path in
`Style.render_text` exists because that font mapped 28 characters,
the digit 4 among them, onto one watermark bitmap.

Replaced by **Aldrich** (Matthew Desmond, SIL Open Font License),
picked by measurement rather than by eye: of six OFL candidates it is
the closest to Bank Gothic in height (38 vs 40 px at nominal 40) and
ascent (29 vs 31), and its advance widths run a consistent 85-93 % of
the old font's. Narrower is the safe direction — text shrinks inside
boxes tuned for the wider face rather than overflowing them. The one
visible change is real and worth naming: Bank Gothic rendered
lowercase as small caps, Aldrich renders true lowercase.

The substitution machinery stays. It costs nothing on a clean font
(the single-font path is taken when nothing is detected), and a mod
may ship any font at all. What changed is the test: it asserted that
`(` and `4` *are* substituted, which tested one font's defect rather
than the mechanism. It now asserts that the shipped font substitutes
nothing, that a stub font with a deliberate collision IS detected,
and that any shipped font has a licence file next to it.

**40. Derived files are generated, never committed — and the licence
to say a file is derived is a byte-for-byte check.** The repository
carries source, documentation and authored artwork; the ship steps,
the cut sidebar icons and the black hole master are rebuilt by
`tools/setup.py`, which then runs the smoke test so a clone can prove
its own completeness. Two reasons, and the second is the one that
matters: artwork extracted from somebody's copy of the game is not
ours to redistribute, and git stores images as whole blobs rather
than diffs, so every regeneration of a set that stayed in the
repository would leave another full copy in the history forever.

The check is not a formality. `stars/` was about to be ignored on the
strength of "there is a `make_star_icons.py`, therefore it is
generated" — and the tool emits uniform 256x256 canvases while the
36 sprites in the tree are trimmed to content, 44 to 206 px. Both
render, the smoke test's star checks are size-agnostic, and nobody
would have noticed that every clone had different artwork from the
one all the zoom and icon measurements were taken against. A
generator that does not reproduce its own output is not a generator
yet, and its output is authored state until it is.

The same rule already governed the help texts (decision 38); this is
it stated once for everything, now that there is a repository to
state it about.

**39. A button whose native rectangle is in the source is clicked by
coordinate, not by field id.** The galaxy map drives its nav buttons
through `ACTIVATE_FIELD` with ids read off the field list, and each
id had to be verified live before it could be trusted. The colony
summary does it the other way round: `layout.json` carries a
`native_click` point inside each of the original's buttons, taken
from the `Add_*_Field_` call with a line number (`colsum.cpp:265`),
and the screen injects a click there. The point is checkable by a
grep against the source, needs no live session, and survives a field
list that shifts — the scroll field is only added when there are ten
or more colonies, which renumbers everything after it.

The trade-off used to be the known one: `INJECT_CLICK` carried
window coordinates (open fix 3), so this only held at a 640x480
window. **That is gone as of 4 September 2026** — the command now
converts with the renderer's own inverse before pushing the event
(`doc/ext_inject_click.patch`), so a `native_click` point is a game
coordinate at any window size. Worth naming the reason the
constraint could not simply be lived with: the window size is on no
wire message and, under Wayland, cannot be measured from outside at
all, so "just run it at 640x480" was a precondition nobody could
check — and an unverifiable precondition is one that goes missing
quietly, taking the click to the wrong row with every number on
screen still correct. It is also the path the population bars will
need anyway — a pop move is two clicks at
computed positions, and there is no field id for "icon 7 of the
farmers".

**Amended 3 September 2026: where the original gives the button a
HOTKEY, the key goes first and the coordinate stays as the
fallback.** Not by field id either way, so the decision is unchanged
in what it refuses; what changed is which of the two id-free paths is
preferred, and why.

A click is not inert. `INJECT_CLICK` arrives as an SDL button event,
and platform.cpp:1171 hands its coordinates to
`Set_Present_Mouse_Position_` while :1172 enqueues them as a mouse
input event — so every injected click leaves the game's own pointer
standing on the button we pressed. The key path (platform.cpp:1131)
touches neither. Both sort the game correctly, and nothing on the HD
screen can show the difference.

**The coordinates are kept, and that is half the decision.** A
`native_click` is checkable by a grep against the `Add_*_Field_` call
with no game running; a hotkey is a letter in a JSON file that has to
be taken on trust until somebody presses it. So the two are not a
replacement but an order, and a smoke check refuses a sort button
that has lost its point. RETURN has no letter at all — its field
reports 0x25 — and takes the click path, which is what makes the
fallback load-bearing rather than decorative.

**And this one had to be verified live before it was switched on,
because its failure mode is invisible.** A dropped key and a working
key produce the same picture on this screen: the original re-sorts by
a key it already holds without moving a pixel, since there is no
direction toggle. "Nothing changed" is both outcomes. Sorting AWAY
from the active key is the only observation that separates them, and
that is what was run — `p` from a name-sorted list moved 15071 of
307200 framebuffer bytes, `n` moved them back, and a frame taken
after the key was byte-identical to one taken after the equivalent
click. The pointer half of the claim was NOT observed and rests on
the source alone: the cursor is composited onto the ARGB present
surface (platform.cpp:794-822) and the Extension API sends the
indexed one (ext_api.cpp:165), so no cursor is on the wire.

**And the second half of that sentence was wrong — corrected
4 September 2026.** It said the game's window is hidden while the API
is on. It is not: `ext::Init()` sets `g_hide_window = true` from
`mox2.cpp:382`, immediately before `Screen_Control_()`, which is long
AFTER the platform layer has already called `SDL_ShowWindow`
(platform.cpp:1394) with the flag still false. So the window is
created 640x480, `SDL_WINDOW_RESIZABLE`, and SHOWN — a human can
focus it, drag it and move the pointer across it, which is precisely
the mechanism behind open fix 3's second half. A flag that is set
after the thing it would have prevented is not a guard, and reading
it as one cost a wrong sentence here.
Saying which half was measured is the point of writing it down.

**A new message is not a new picture — 4 September 2026.**
*(Superseded in force by "A fresh message is not a fresh world" under
Diagnosis, 5 September 2026: waiting on the right channel's own
counter is necessary and NOT sufficient, because the first value that
channel produces after a send is structurally the old one. Read both;
this one is the half that is about which channel, that one is the
half that is about when.)* The
population-move probe stepped the game's list window down, read
`_first` back off the scroll thumb, got the same value it had before,
and stopped with "established 1, wanted 0". The step had in fact
worked. Its `settle()` waited for a new STATE snapshot and then
merely checked that *a* framebuffer existed, so it read the thumb out
of the frame from before the step. The two channels are separate and
the visual one lags: waiting on the wrong counter turns a success
into a reported failure, which is the cheap direction — the same
mistake pointed the other way would have aimed a click at a window
position that had already moved. Anything read out of the
framebuffer waits on the framebuffer's own counter.


**36. A value the API does not report is copied by hand — and gets a
checker, not a reminder.** The engine version is on orion2re's main
menu and nowhere on the wire: `HELLO_REPLY` carries `PROTO_VERSION`,
which is the protocol's number, and the snapshot has no version
field. Appending it would have been four lines of C++, backwards
compatible, and still the wrong trade — a permanent change to
somebody else's tree bought one line of cosmetic text.

So `core/config.ORION2RE_VERSION` holds the string, and
`tools/version_check.py` reads orion2re's own `src/version.h` and
`src/game/consts.h` and fails on a mismatch. That is the part that
makes the copy legitimate: a hand-maintained number without a check
is the nebula sizes again, correct until the day somebody upstream
changes it and nothing here notices. The smoke test adds the other
half — the literal appears in exactly one file in the tree.

The line to hold: this is for values a client *displays*. The moment
a client has to **behave** differently per engine version, a number
a human retypes is no longer good enough and the patch comes back.

**35. The HD viewport may decouple from the game's; the click frame
may not.** The snapshot carries every star's galaxy coordinate, so
zooming and panning the HD map is a client-side act the game never
sees — no Extension API change, no scroll command, nothing to ask
Joes for. But `INJECT_CLICK` lands in the game's own 640x480 slice, so
**every galaxy→native conversion that reaches the wire goes through
the GAME's state, never the HD view's**, and while decoupled the game
is parked at maximum zoom-out so that slice covers the galaxy.

The asymmetry is the whole point: HD pixel → galaxy uses whatever
view is on screen, galaxy → native always uses the game's. Mixing the
two frames produces clicks that select the wrong system while looking
perfectly right on screen — the worst kind of wrong, because nothing
about the picture reveals it.

Corollary: **park with the safe direction only.** Parking uses the
zoom-OUT field exclusively and throttles it. Zoom-in (field 8) puts
the game into a rubber-band selection state a client cannot escape;
a feature that never needs it can never trip it.

**48. `pop[]` HAS NO ORDER, so the one the player sees is the
original's draw order — and inside a job group that is not a
preference.** Read 5 September 2026;
`doc/pop_order_reading.md` is the reading, with every finding marked
for how far it is carried.

The array is a bag with stable indices between events. Everything
that appears is appended at `pop[n_pops]` (growth colcalc.cpp:2387,
androids :3802, settlers settler.cpp:49); everything that disappears
is replaced by the LAST entry (six sites, all
`pop[hole] = pop[--n_pops]`); a job change moves nothing, it rewrites
the profession bits where they are; and
`invasion::Enforce_Population_Limits_At_Colony_` SHUFFLES the whole
array (invasion.cpp:721) on four occasions, one of which is a
building completing — Biospheres, in a game with no war in it.
**It is NOT on the pop-move write path** — established 7 September
2026 when a move looked as though it had touched a second colony and
this function was the first suspect, because it is named here. The
cross-colony writers are `COLCALC::Pass_Out_Imports_`
(colcalc_main.cpp:208), which rewrites `imports[ECON_FOOD]` on every
non-outpost colony of the owner, and `COLCALC::Post_Import_Computing_`
(colcalc.cpp:891), which rewrites `pop_growth`, `pop_roundoff` and
`specialty` on every NEEDY one. See section 3. The
engine does sort `pop[]`, in `aidudes.cpp`, and only for players
whose `objectives != PLAYER_OBJECTIVE_HUMAN`.

So there is nothing to transcribe. What the ORIGINAL shows is
imposed at draw time by `Do_Colony_Info_Pop_Stuff_For_Pop_`
(coldraw.cpp:326-337): state, then the conquered bit, then the low
nibble in the order (9, 0, 1 … 8), and the array only innermost.

**HD keeps that order inside a job group, and the reason is not
fidelity — it is that the selection rule depends on it.**
`Get_Cluster_` takes every identical pop from the clicked one to the
END OF THE ARRAY, and `Pops_Identical_` compares exactly the three
fields the walk groups by. Those two facts together make a cluster
one contiguous run of icons starting at the clicked one. Order the
cells any other way — by array index, by race, by anything — and a
click on one cell moves cells elsewhere in the row, with every count
on screen still correct. That is this project's worst failure shape
and it is one ordering decision away.

Corollary, and it is the part a drawing session will meet first:
**a cell may not be positioned by a property the walk does not sort
by.** The race and android distinction is carried in the CELL —
which is what the original does too, in the sprite rather than in a
colour, and with four classes: a conquered pop is a static race
portrait (colony.cpp:1278), a native and an android are one sprite
each for every race (colony_main.cpp:456, :460), and everyone else is
per race and per job (:445). Carrying it in the position instead
would be re-sorting the group.

