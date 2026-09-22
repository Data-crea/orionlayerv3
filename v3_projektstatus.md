# OrionLayer v3 — Project Status

Updated: 20 September 2026

**How to read the date above.** The header names the day this file
was last edited; the "This session (…)" paragraphs below it run
newest first, and the top one should carry the same date. Between
5 and 10 September 2026 they did not: five sessions edited sections
deeper in this file and left both the header and the lead paragraph
at 5 September, so the document appeared four days out of date while
carrying entries dated 9 September inside it. **The convention is
right and the header had gone stale** — resolved 10 September 2026
by dating the header to the edit and giving this session its
paragraph, below, so the two agree again.

This session (20 September 2026, work order 155): **the strip under
the Fleets map names the star the pointer is over — and the finding
is what it must NOT say.**

**The strip is not a star-name field.** Help 363 calls it
"information as you scan ships and stars", and
`FLT2::Print_Fltscrn_Scanned_Star_Name_` (flt2.cpp:338-522) picks one
of TEN states. The first thing it asks is whether any ships are
selected; if they are, it runs `SHIPMOVE::Ships_Try_To_Move_To_` and
prints a MOVE PREVIEW — "Orbiting %s", "%d turn(s) to %s", "ETA %d
turn(s)", a black hole in the way, immobile, parsecs out of range,
hyperspace flux. The star's NAME is state 7, reached only when
nothing is selected, and H 0x94 is state 8 for a star the player
knows nothing about. With nothing scanned the original does not write
the strip at all (flt1.cpp:397).

**HD draws states 7 and 8 and stays SILENT for the other eight.**
With ships selected the original is answering "can these ships get
there"; a name is not a worse answer to that, it is an answer to a
different question, and `_g_ship_move_info` is on no wire. The
alternative — name the star in all ten — is one line and is Data's
to call; `doc/briefs/155-parked-for-data.md` §1 has it.

Hover **sends nothing**: `fltmove.star_at` resolves the star out of
the stars HD already draws (`galaxy_inset_stars` emits one per star
in order, so the drawn index IS the star index), and it is ONE copy —
`fltmove.click` was carrying the same arithmetic and now calls it.
The unexplored case uses the helper work order 154 built, so HD can
under-report and never over-report.

**The three scans are mutually exclusive, as in the original**:
taking a grid cell clears the scanned star (flt1.cpp:616-620), taking
a star clears the small ship but NOT the big one (:649-652), so the
ship panel keeps its ship while the strip names a star.

**The two small boxes were already built.** They are PREV/NEXT FLEET
— `Next_Ship_Icon_` / `Previous_Ship_Icon_` step the ship stack — and
`handle_click` has activated them through the game's own field since
work order 134. Nothing was needed. What IS missing is that they show
nothing at all, which the acceptance capture makes plain; three ways
to close it are in the parked file, with a recommendation.

One older check had to state its own precondition: "the panel follows
the SCANNED ship" answered whichever source an EARLIER check had left
set, because since 153 B there are two. It clears HD's hover now and
says which one it is driving.

Smoke 242 -> 243.

This session (20 September 2026, the clone-only fault, piece 4 of 4):
**every registered path is ignored, and the two lists can no longer
drift.**

Each of the twelve paths `setup.from_game()` registers must really be
gitignored — a COMMITTED file on that list could vanish and nothing
would say so, and a player's own data could be committed by
accident. All twelve are.

**And `_JSON_ABSENT_OK` is now held to the registry**, which is the
fault `5402b7d` was: two new files went into `_JSON_OTHER` instead of
the absent-allowed list, the suite stayed green on the machine that
had extracted them, and a clone went red. Every `.json` the registry
names must be on the absent-allowed list, so forgetting one fails
here rather than in a clone.

**It found two the moment it was written.** `kentext_en.json` and the
Fleets `manifest.json` — the two entries piece 1 added to the
registry — had never reached `_JSON_ABSENT_OK`. Two lists maintained
by hand had already drifted within the same session; that is the
argument for tying them together rather than keeping both.

No new check: the assertions join the JSON one, which is the same
concern. Smoke 242, unchanged.

**The four pieces are done.** The rule is in the fundament, the
registry is complete and self-checking, a check gets a stand-in
instead of the player's catalogue, the loader rule is enforced by
`ast` rather than remembered, and the two lists are one.

This session (20 September 2026, the clone-only fault, piece 3 of 4):
**the rule is enforced, not remembered.**

Every construction of a derived-data loader in `tools/smoke_test.py`
must now be one of three things: `derived(Loader)` for the committed
stand-in, an explicit `root=` (a scratch directory, which is how a
forced-absent case is written), or the language `"zz"`, which cannot
exist. Anything else has to be named in `_REAL_DERIVED_OK` with the
reason it needs the player's own extraction.

**Read with `ast`, not with a grep.** A call can span lines, and a
line scan cannot see one. The aliasing import is the other half:
`HelpText as _HelpText` hides every construction from any scan, so
an aliasing import of a loader class is refused outright — the two
that existed are gone.

Fifteen constructions today: two allow-listed, six forced absent by
`"zz"`, five by a scratch `root=`, and the rest through `derived`.
The check refuses to pass if it sees fewer than ten, so a scan that
has stopped recognising them says so instead of going quiet.

Smoke 241 -> 242.

This session (20 September 2026, the clone-only fault, piece 2 of 4):
**a check gets a stand-in, not the player's catalogue.**

`tools/fixtures/derived/` holds a committed stand-in for each of the
eight derived catalogues, in the SAME relative layout the loaders
use, so the suite reaches them through the loader's own `root=` and
nothing else changes. A stand-in that bypassed the loader would test
nothing.

**They are generated from the loaders' own constants**
(`tools/make_derived_fixtures.py`), never copied from an extraction —
`HSTRINGS_COUNT`, `ESTRINGS_COUNT`, `BUILDING_COUNT`, the
`shipparts.TABLES` counts, and each module's `FORMAT_VERSION`. That
is what makes the generator runnable in a clone that has never seen
MOO2. The values are deliberately not plausible ("Weapon 14", not
"Nuclear Missile"): a stand-in that reads like real data invites a
check to pin wording that is the player's and not ours.

**Two checks were vacuous and are not any more**, which is the
argument for the whole piece:

* `TechNames.field_name` — "the hyper-advanced fields are None"
  passed in a clone because EVERY field was None with no file. The
  stand-in carries all 83, so it now tests the loader's own boundary.
* `ArcWords` — ran whichever branch the machine was in, present here
  and absent in a clone, so neither was exercised on both. It now
  runs the stand-in for the words AND an empty directory for the
  absence, every time.

The 154 ship-panel layout block — the fourth occurrence, and the
reason this exists — takes its catalogues from `derived()` too.

Held by a new check: the stand-ins are byte-for-byte what the
generator makes, each carries the `FORMAT_VERSION` its loader
demands (so a bump that forgets them fails at the bump), each loads
through the loader's own path, and three checks are allow-listed to
read the PLAYER's extraction with a reason — `BuildingNames` and
`EStrings` pin real strings that catch a walk off by one, and the
help-file check is about the loader itself.

One stand-in detail worth keeping: every HESTRNGS entry carries a
`%s`, because many of the real ones are format strings (0x9B is
"Destination, %s") and a placeholder-free stand-in silently drops
whatever is substituted into it. That cost one red run to find.

Smoke 240 -> 241.

This session (20 September 2026): **two writers were leaving JSON
without its trailing newline, and now none is.**

The tree's convention ends a JSON file with a newline.
`core.box.save_boxes` — every F5 save — and
`select_race.save_races` did not, so each save left the file one byte
short and the next hand edit appeared in the diff beside
`\ No newline at end of file`. **`tools/frame_holes.py` had already
worked round it on its own side and its comment named `save_boxes` as
the culprit**; a comment is not a fix, and the fleets `boxes.json`
Data saved on 20 September came out without one.

Seven tracked files carried the fingerprint — `custom_race` and
`select_race` `boxes.json`, `races.json`, `traits.json`,
`new_game/layout.json` and two `9slice.json`. Both writers fixed at
the source, all seven normalised, and the JSON formatting check now
also holds that **every tracked `.json` ends with exactly one**
newline — no more, so a double newline is a fault too.

It reads the list from `git ls-files`, which makes it clone-safe by
construction: the extracted catalogues are gitignored, so they are
never named and their absence cannot fail it. That is the piece-1
rule applied the first time it was needed.

No new check — the assertion joins the formatting one, which is the
same concern. Smoke 240, unchanged.

This session (20 September 2026): **the six placed Fleets boxes are
seeded, not pinned — a check of mine had locked the editor out.**

Work order 153 A gave the six boxes with no hole a RULE, and a smoke
check that demanded each one EQUAL what `fltplaced` computes. That
quietly turned six F5-editable boxes into locked ones. It surfaced
the first time anybody used the editor on them: Data nudged
`ship_panel_text` one pixel at 2560x1440, set its `font_scale` to 1.5
and moved `help_popup`, and the suite went red over the pixel.

**`fltgeom`'s own docstring and decision 14 already said the seat is
a starting point and not a cage**, so the check was wrong and not the
edit. What is held now is the 151 lesson and nothing else — every
placed box is INSIDE the hole it belongs to (or holds the cutouts it
is the union of), measured against `boxes.json`'s own rects wherever
F5 left them. Two things go with it: all six must still exist, and
the SEED `fltplaced.placed` computes must itself fit, so a reshape
cannot leave the tool producing something the editor has to repair by
hand.

`tools/fleets_place_boxes.py` stays a seeder, run when the frame
changes shape, and now says before it writes that it overwrites F5's
edits — the same bargain `tools/fleet_boxes.py` carried.

**Data's three edits stand, with two repairs the pre-existing checks
demanded and one check of theirs that was wrong.**

* `help_popup` at 2560x1440 had been dragged to x 954 with a width of
  1080 — right edge 2034, **114 reference px outside the 1920 space**,
  so it would be clipped at every window size. The editor let it go
  there. Pulled back to x 840, which is as far right as it fits; the
  move stands, the overhang does not.
* `font_scale` 1.5 was written into the 2560x1440 block only, because
  `save_boxes` writes the block you are in. That left the panel's text
  at 1.5x on three resolutions and 1.0x at 1080p, which the "same
  share of the window at all four" check caught. The 1080p block now
  carries 1.5 as well.
* And the check that tests "the box's font_size decides the panel"
  compared against `layout.font_size(font_size * 2)` **with
  `font_scale` left out** — right only while the scale is 1.0, which
  it was everywhere, so the check was green and wrong at the same
  time. The first non-unit scale turned it red and the message blamed
  the product. Fixed to use the same product `panel_font_px` uses.

**The editor does not clamp a drag to the reference area.** That is
how the `help_popup` overhang got written, and it is worth its own
look — a box dragged past the edge is saved outside it and only the
smoke test says so.

Smoke 240, unchanged.

This session (20 September 2026, the clone-only fault, piece 1 of 4):
**the rule is in the fundament, and the registry it rests on had two
holes.**

A check that reads the player's own extracted files passes on the
machine that wrote them. It has happened **four** times — 13 September
(`d3d0561`), twice in one run (`5402b7d`) and 20 September
(`58b2808`) — and each was caught by the fresh-clone run before a
push, never by the suite. The finding that decides the shape of the
answer is in `5402b7d`: that session walked into a trap described in
the paragraph *immediately above the list it should have edited*.
**Prose has already been tried and has already failed**, so the
fundament entry (§2, Diagnosis) says what makes the fault unwritable
rather than asking anyone to remember it.

**`tools/setup.py:from_game()` is the registry** — the one list of
files derived from the player's install, and what tells a clone which
extractor to run. Anything keyed on it inherits its holes, and
writing the check found two:

* **`kentext_en.json`**, which `ArcWords` reads for the Fleets
  panel's weapon firing arcs;
* **the Fleets gamedata**, which `fltart` reads for the ship
  pictures.

Neither had ever been reported absent, so a clone was never told to
run `kentext_extract.py` or `fleet_art_extract.py` at all. Both are
registered now, checked by `manifest.json` and the language-aware
path the loader itself uses.

The check is two-way, like the over-300-lines list: every
`tools/*_extract.py` is named by a registry command, or is on the
committed-output exception list AND its output is really tracked by
git. One exception today — `planet_extract.py`, whose ten planet
discs come from Data's own sheet and are committed.

Smoke 239 -> 240.

This session (20 September 2026, the leader record): **tried with
struct_probe, and it does not verify — the blocker is not the struct.**

Data asked for one attempt, two independent sources, live readings
across enough ships and officers to be non-vacuous, and the Beam
OCV/DCV line back if it held.

**The layout is corroborated.** orion2re's header with its `0x3b` size
assert, and a live reading of all 67 records where `name`, `title`,
`type`, `special_skills` and `player_index` agree — the last two
semantically against each leader's own title — and **`xp` agrees
numerically**: the only values present are 0, 60, 150, 300 and 1000,
which are exactly `Get_Officer_Base_Level_`'s thresholds. A wrong
offset does not land on another function's step points.

**It is not enough, for two reasons and neither is the struct.**
First, the officer path is VACUOUS: the panel reaches the leader
record only through `s_ship_data.officer_index`, the loaded save has
0 of 21 ships with an officer, and across all ten saves on this disk
— read from the files, nothing loaded — only four ships of 185 carry
one, never more than one per save. That is the damaged-special check
again. Second, the ground truth cannot be read at all: the game
prints that panel only for `_scanned_big_ship`, which it sets from
its OWN cursor, and the API has no mouse motion. An INJECT_CLICK
would set it at the cost of toggling that ship's selection, for one
data point.

**What is NOT missing, which is worth knowing:** every static table
is a literal in the source — `_crew_data` (mox.cpp:780),
`_computers[].bonus` and `_hull_data` (techdata.cpp:429, :77) — and
`Get_Officer_Base_Level_` is five lines. The trait indices are now
known: SHIP_DEFENSE 6, SHIP_ATTACK 7, WARLORD 30.

Stopped there, as instructed. The line stays dropped and the findings
are at `core/structs/unverified.py`'s `LEADER` entry, in
`doc/briefs/154-parked-for-data.md` §4, and on the open list with the
order the work has to happen in.

**Live rules kept:** one client, nothing sent, nothing loaded, nothing
saved. SAVE1-9 and SAVE11 hashed before and after and identical;
SAVE10 logged at `70f86100…` and unchanged.

Smoke 239, unchanged.

This session (20 September 2026, after work order 154): **the Beam
OCV / DCV line is gone, and two omissions are on the open list.**

Work order 154 drew the two labels with nothing after them so the line
would hold its place in the grid. **Data's answer: no empty labels on
the player's screen, drop the line entirely.** So `Panel.HEAD_SLOTS`
is four where the original's head is five, HD's grid is deliberately
one line shorter than the original's, and
`omission_panel_beam_bonuses` records that as a difference rather than
an oversight.

The reason is kept in three places, which is what makes it findable:
the mark, `doc/briefs/154-parked-for-data.md` (with the two rejected
alternatives, because the next session faces the same choice when the
numbers arrive), and **"What is missing"**, where it is now item 3
under the Fleets ship panel with the cost of lifting it — the leader
record verified first, then four static tables. Item 4 is the
colony / transport / outpost help paragraph (flt2.cpp:548-575), added
on Data's instruction and explicitly not part of any order yet.

Also fixed on the way: the layout check work order 154 added only
passed where the extracted names are. The fresh-clone verification
before the push caught it — the line grid is now measured against a
panel built out of literals, and the no-catalogue state is asserted
instead of skipped.

Smoke 239, unchanged.

This session (20 September 2026, work order 154): **the ship panel
laid out the way the original lays it out.**

Formatting only. `FLT2::Print_Scanned_Ship_Data_` (flt2.cpp:524-747)
read line by line AND checked against a native screenshot of the same
panel (`evidence/work_order_152/panel/001_20_panel_native.png`, the
ship "Rafale"). Two sources, agreeing on every number.

**THE HEAD IS FIVE SLOTS, NOT FOUR, AND AN EMPTY ONE IS A BLANK
LINE.** The destination is an `if` that prints or does not, and the
`y_cursor += FH + 2` after it runs either way (flt2.cpp:643-660). That
blank IS the empty line Data saw between the head and the
Weapons/Specials headings — it is the destination slot, empty because
the ship was parked. A ship in transit fills it and there is no blank
at all.

**Six tab stops, transcribed as fractions of the 305 px window**
(`fltpanel.COL_*`): labels at +3, weapon entries at +8, the OCV value
right-aligned ending at +118, "Beam DCV:" and "Specials:" at +158,
special entries at +173, the DCV value at +273. The two indents
DIFFER — 5 native px on the left, 15 on the right — and both are
transcribed rather than averaged. `SPECIALS_SPLIT` is now defined as
`COL_RIGHT_ENTRY` instead of being a second copy of the same number.

**Beam OCV / DCV: absent always, and not because of the layout.**
`INITSHIP::Get_Ship_Combat_Bonuses_` (initship.cpp:638-687) adds the
HELMSMAN and WEAPONRY skills of `ship->officer_index` to the design's
own bonus, and those live in the leader record, which
`core/structs/unverified.py` refuses (decision 23). So no number can
be computed for a ship with a captain. **The two LABELS are drawn at
their stops** so the line holds its place and the gap is visible
rather than silent — the same argument `deviation_panel_overflow`
makes. The two alternatives and why they lost are in
`doc/briefs/154-parked-for-data.md`.

**Two faults found while transcribing, both fixed.** HD printed
"Destination, Vega" for a ship sitting at Vega: the original prints
that line only for `location >= 10000` (flt2.cpp:644), and work order
152 item 7 established the line without its condition. And HD named a
star the player had not explored: the original picks H 0x9C
"Destination, Unexplored star" unless visited, omniscient, a Galactic
Lore leader or in contact with a colony there (:657-662), and HD now
reads the first two through the helpers `colonyrows` and the galaxy
map already use. It can under-report and cannot over-report, which is
the safe half.

**Found and not built:** a colony, transport or outpost ship gets a
centred HELP.LBX paragraph in the original instead of this panel
entirely (flt2.cpp:548-575). HD shows the data panel, which is more
than the original rather than less. Marked, parked, buildable.

Four new marks, each citing its lines, each held by the new check;
`deviation_panel_overflow` corrected, because it still said HD stacks
the two columns in one, which stopped being true at 152 item 7.

Smoke 238 -> 239.

This session (20 September 2026, work order 153, Part B):
**hovering a ship shows its readout, and sends nothing.**

**WHAT THE ORIGINAL DOES, off the source.** The panel is printed for
`_scanned_big_ship` and for nothing else (flt1.cpp:401-406), and that
value is the HOVER: `Scan_Fltscrn_Big_Icons_` takes `scan_val.full` —
the field under the pointer — as `btn_id1` and sets only its FIRST out
index for it, answering result 4; a click matches `input` and sets
both (flt2.cpp:902-950). **Selection never feeds the panel**:
`selected` is a separate flag with its own sprite (:93-104). **With
neither, the last hovered ship stays** — nothing clears
`_scanned_big_ship` when the pointer leaves the grid; it goes to -1
on entry (:528), on the bar being DRAGGED (:449, not on an arrow
click), after SCRAP (:714) and when the stack pointer moves (:677,
:757, :765). And it is an ICON INDEX, so a scroll keeps the same ship
and takes the box off the grid when that ship leaves the five rows.

**HD BUILDS IT LOCALLY AND THAT IS A REQUIREMENT.** Everything
`panel_lines` needs is in the snapshot the screen already holds —
`ship_idx` from the FLTS block, `ships_raw` from the same message —
so no client call is on the path. It has to be: the API has no mouse
motion to forward (open fixes 3 and 4), and a send per mouse movement
would flood the one input path it does have. **Nothing was asked of
Joes**; `doc/orion2re_open_fixes.md` is unchanged.

`screens/fleets/fltscan.py` is HD's copy of `_scanned_big_ship`, with
the citation for every rule, including the one reset that has no HD
equivalent — HD's bar has no draggable thumb. **The mark and the panel
are one value now**: `fltdraw` asked `_hover_cell`, the raw pointer
slot, and asks `_scan.slot(block)`, which is what the order means by
the two changing together and what the original does with one variable
and two draw calls.

Ten assertions under one check, through the real screen on the real
fixture: the hovered ship is the one in the panel, **nothing is sent**
(after each of nine hovers and again at the end), the marked cell is
the panel's cell, selection does not pull it away, the pointer leaving
changes neither, an empty slot and a foreign stack are refused, a
scroll keeps the SHIP, the four resets fire, and the wire's own
`scanned_big` is still the fallback.

Two corrections on the way: `screens/fleets/screen.py`'s docstring
still said the frame is the Planets art with its struts removed, has
one hole, and that `tools/fleet_boxes.py` seeded `boxes.json` — all
untrue since work order 146, and Part A fixed only `layout.json`'s
copy of the same claim; and `fltwire._rows_from_block` multiplied
`first_row` by a literal 4 where `fltgeom.GRID_COLUMNS` is the tree's
copy of `_big_icon_display_columns`.

Smoke 237 -> 238.

This session (20 September 2026, work order 153, Part A): **the
Fleets frame at new proportions, from the same source, with every
corner still a copy.**

Data accepted a new layout because the ship panel could not hold the
original's readout even after font scaling (152, item 7). In 4K source
pixels: the map hole gives **195 px of height** to the ship panel
(1812x1101 -> **1491x906**) and **321 px of width** to the right
column, so its aspect stays at **1.6458**; the three small boxes and
the panel follow the map's new width; the right column takes the 321
back and its cells, buttons and scroll-bar area are rebuilt at their
new size. The canvas stays 3840x2160 (decision 70) and the outer ring
is not touched.

**THE METHOD IS 151's 3-SLICE, GENERALISED** —
`tools/fleets_frame_reshape.py`, called by `fleets_frame_build`
between the unlit rebuild and the cut. Each axis is a list of
segments: an ANCHOR is copied pixel for pixel, an ELASTIC run is
resampled, and every elastic run was chosen against a measured
flatness profile, never by eye. The left column needs one x profile
(an elastic run in [500, 1770) lies inside the map, the status strip
and the panel at once, so all three lose 321 while PREV and NEXT keep
their size); the right column needs three, cut at rows 1560 and 1778,
because four cells, three buttons and four buttons divide the same
width differently.

**"No stretched corners" is a measurement.** `anchor_pairs()` is every
region the reshape claims to translate; the smoke test compares
**1 889 951 solid pixels** of it against the unlit source and requires
them byte-identical. Every corner, chamfer, rivet, bracket and V-notch
is inside one.

**The galaxy stretch did not move**: 1491/906 = 1.645695 against the
galaxy's own 1.265 is **1.300945x**, where the hole before this work
order gave **1.301009x** — 0.005 %. In the BOX, which is what
`galaxy_inset_stars` actually divides by, it is 1.29734x against
1.29849x, 0.089 %. Both are inside the 0.13 % that 151 accepted.

**The ship panel now fits the longest realistic entry at every
resolution.** Four head lines plus the eight-weapon column at the
struct's own maximum, in the real font with the real names:

| | 1920x1080 | 2560x1440 | 3440x1440 | 3840x2160 |
|---|---|---|---|---|
| text box, window px | 694x242 | 925x322 | 925x322 | 1388x484 |
| lines at the box's own size | 17 | 18 | 18 | 17 |
| 8 weapons + 4 head | fits at 14 px | fits at 18 px | fits at 18 px | fits at 28 px |
| specials still fitting beside them | 12 | 13 | 13 | 12 |
| the same, before this work order | 10 lines, shrunk to 11 px, 0 specials | 11 lines, 15 px, 0 | 11 lines, 15 px, 0 | 10 lines, 23 px, 0 |

**The cells came out 341x221 where they were 261x219**, and that is
the opening detector catching up rather than the reshape: it grows an
edge while the next line is 80 % dark, and at the cell's lower bevel
that fraction depends on how wide the cell is. A column through the
middle of a cell reads 8.7 at row 445 and 29.0 at 446, so the interior
always ended there and the old cut was three rows short of it.
`CONTENT_INSET_SRC` for a cell moves 9 -> 10 with it.

**The six boxes with no hole are a rule now, not a memory.**
`screens/fleets/fltplaced.py` derives `ship_panel_text`, `icon_area`,
`button_band`, `status_text`, `inset_hint` and `status_hint` from the
holes; run against the boxes as they stood at `fb197ac` five come out
identical and `status_text` one pixel right. `tools/fleets_place_boxes.py
--write` applies them and a smoke check recomputes them, so the next
reshape moves them. Before this, a frame change left every one of them
over the old layout — the fault 151 paid for.

The mockup the order names (`~/Downloads/fleets_mockup_narrow.png`) is
not on disk; see `doc/briefs/153-parked-for-data.md`. The acceptance
render is new beside current, at 1440p, in
`~/orionlayer-fixtures/evidence/work_order_153/`.

Smoke 235 -> 237.

This session (20 September 2026, work order 152, item 8): **ships are
sent to a star from the Fleets map, and it needed nothing from Joes.**

**THE ORIGINAL'S FLOW HAS NO BUTTON** (flt1.cpp:628-664): select ships
in the grid, then click a star in the inset. RELOCATE is a different
branch. The send is `ACTIVATE_FIELD` on the star's own hidden field,
which decision 20 names for a type 7, and **decision 35 is satisfied
outright** — the field IS the game's frame, so no HD rectangle is in
the path and the API's missing INJECT_CLICK mapping is not in the way.

**THE POLARITY IS THE TRAP AND IT IS WRITTEN DOWN.** In
`Scan_Galaxy_Map_Fields_` the second argument is `input` and a match
there is the CLICK (result 0); the hover is the first argument and
answers result 4. That is the opposite way round from
`Scan_Fltscrn_Big_Icons_` on the same screen, where a positive index
is the HOVER. Two scanners, one screen, opposite conventions.

**THE STAR-TO-FIELD MAPPING IS DERIVED FROM THE DATA, NOT TYPED.**
HD's inset positions and the game's star fields differ by a constant
offset, and three attempts got it wrong before the live numbers
settled it: comparing in the wrong frame gave scattered offsets, and
demanding that all 54 agree exactly refused a mapping that is right.
Measured: **(-6, -6) on 46 of 54, with five at (-7, -6) and three at
(-6, -7)** — HD's arithmetic and the game's round the same division
differently by a pixel. So `fltmove.match` takes the majority offset
from the data each time and allows `SLACK` of 2 around it, requires a
clean bijection, and **returns {} otherwise, which means send
nothing**. The rule lives on the star pitch (~30 px) exceeding the
offset (12), which the check's fixture is built to respect.

**ONE REFUSAL IS OURS, THE REST ARE THE GAME'S** (decision 33). The
black hole is one comparison — `spectral_class ==
STAR_CLASS_BLACK_HOLE` (flt1.cpp:640) — and refusing it in HD also
keeps the screen out of a `User_Box_` it did not need to enter.
`Player_Can_Order_Ship_` reads data HD does not hold and is left to
the game.

**Live on SAVE4**: one ship selected, an HD click on star 0 resolved to
field 19, and the ship's `location` went from 32 to 20000 — the
in-transit encoding — with `travelling_speed` 2 and `turns_left` 4.
The ships moved. SAVE1-6, 8, 9 and 11 byte-identical, SAVE10 logged and
unchanged, nothing saved.

Smoke 234 -> 235.

This session (20 September 2026, work order 152, item 7): **the ship
panel is the original's content, in the original's own words, in the
original's two columns.**

**`JIM::Get_Text_Message_` READ PROPERLY, which is what unblocked it.**
The call is
`Farload_Data_Static_(file, message_index * 6 + language, …)` (jim.cpp)
— **six LBX entries per message, one per language**. Reading "entry 3"
of KENTEXT.LBX gives `"Pob:"`, which is why the arcs looked
unreachable; message 3 in English is **entry 18**. With that, all five
firing arcs come from source: **F, Fx, Bx, B** out of the player's own
KENTEXT.LBX through `tools/kentext_extract.py` and `core/kentext.py`,
and **"360"**, which is a LITERAL in `Weapon_Arc_String_` and is
transcribed rather than extracted. The order the bits are tested in is
the answer and not a tidy-up: 0x0F has four of them set and the
original prints the FORWARD word for it.

**THE CREW LINE GOES IN, and the spec with it.** `crew_quality` @113,
`crew_experience` @114 and `officer_index` @116 are promoted to the
VERIFIED spec on the two routes decision 23 names — the header
(orion2.h:2847-2868, the same struct run already verified at @109) and
a live reading over 60 ships where the experience bands per quality do
not overlap and rise.

**TWO COLUMNS, at the original's own x.** Weapons at 0x17 and specials
at 0xBC inside a window that starts at x 15 and is 305 wide, so the
split is `(0xBC - 15) / 305` — a FRACTION, because the HD panel is a
hole in Data's artwork and not 305 px wide. Both columns start from one
`base_y` as the original does, and one size is found for the head and
both columns together, measured by rendering.

**THE LOCATION LINE WAS THE ORIGINAL'S ALL ALONG** — the order had it
down as an HD addition and it is not (flt2.cpp:672). What WAS HD's own
was the hardcoded English "Location: " label, and it is gone: the line
now comes from `H_Message_(0x9B)` formatted with the star's name.

Live on SAVE4: *Rafale / Green Crew (15 EP) / No Shield / Destination,
Yoth*, then **Weapons:** with five entries each carrying its arc, and
**Specials:** with the table's own "None" — every string the game's.

**TWO OMISSIONS, both marked.** The weapon PLURAL
(`TECHDATA::_weapons[t].name_plural`) is not in
`tools/techname_extract.py`'s output, so the singular stands rather
than an invented "s". And a damaged special is not shown in red:
`special_device_damage_flags` @118 is unverified, and the obvious live
check — a damaged device must be a fitted one — held on all 60 ships
and **proved nothing, because not one of them had any damage**.

This session (20 September 2026, work order 152, items 1 and 2): **a
native message box is shown by blitting the game's own pixels, and the
screen stays up behind it.**

**THE FAULT, AND A READING THE TREE HAD WRONG.** `fltwire` said a
message box "adds two hidden fields and clears nothing … every field
this screen built is still in place". The second half is wrong.
`GENDRAW::Message_Box_Startup_` calls `FIELDSAV::Save_Field_Stats_`,
which RE-BASES `fields::_fields` past the screen's fields and then calls
`Clear_Fields_` on the new base (fieldsav.cpp), and `SerializeFields`
walks that re-based window. So the wire carries the BOX's fields and
none of the screen's, `has_fleet_list` fails, and the state was
`WAITING` — the one non-READY state that KEEPS HD's picture up, while
`update()` cleared the cells and the panel. An HD frame with an empty
grid and a blank text box, which is exactly what Data photographed.
`FOREIGN_FIELDS`, the state named after this very box, could never be
reached by one.

**MEASURED, NOT ARGUED.** Live on SAVE4: 73 fields READY before SCRAP;
after it exactly two, `(235,302)-(286,323)` hotkey 'Y' and
`(345,302)-(396,323)` hotkey 'N', which is `Confirmation_Box_`'s two
`Add_Hidden_Field_` calls to the pixel. **And the FLTS block never goes
away** — present with `icons`, `ship_idx` and the selection intact
through the whole sequence, which is what makes the fix possible.

**`core/gamebox.py` IS GENERAL AND NOT A SCRAP SPECIAL CASE.** It knows
box KINDS: the confirmation box (CONFIRM.LBX 0, 313x227, drawn at
(161, 117), two fields) and the warning/message box (WARNING.LBX 0,
331x191, at (154, 144), one ESC field). Each rectangle has two
independent sources — the literal in the `animate::Remap_Draw_` call
and the LBX entry's own header. Recognition is an EQUALITY against the
whole live list, because a box replaces the list rather than adding to
it; and the ESC hotkey is what tells the warning box's screen-filling
field from the fleet screen's own catcher at the same rectangle with
hotkey 0.

**CHAINS ARE THE NORMAL CASE.** Answering NO to the scrap confirmation
opens a SECOND box — `Scrap_Ships_` answers a refusal with
`User_Box_(…, 3)` (flt1.cpp:1524-1527) — and the source read missed it
until the live run showed the list going 2 -> 1 instead of back to 74.
Nothing assumes a box is the last one; the detector runs on every
snapshot. Proven end to end: SCRAP -> confirmation in HD -> HD's own NO
-> warning in HD -> HD's own dismiss -> 74 fields, READY.

**THE LIMITATION, MARKED IN THREE PLACES.** HD cannot set the box's
text in its own font: the string is `H_Message_(n)` formatted with
values the engine computed, and for the scrap confirmation that value
is `Get_Scrap_Ship_Value_()`, a cost model a client does not have. So
the crop is the game's own rendering at an integer magnification
(decision 28's reason) inside an HD panel — the one place in an HD
screen where the original's 640x480 type appears. It is marked in
`core/gamebox.py`, here, and in a smoke check, and **open fix 29** is
the replacement.

This session (20 September 2026, work order 151 B): **the Fleets ship
panel is sized and placed by a box, wraps by rendering, and says what
it dropped.**

**WHAT IT WAS.** `fltdraw.draw_panel` sized its text
`max(10, int(content_rect.height * 0.055))` — a constant in the
renderer, tied to the HOLE's height, with a floor that fired at 1080p
and nowhere else. Measured at all four resolutions before the change:
10 / 11 / 11 / 17 window px, which against the window is 0.0093 /
0.0076 / 0.0076 / 0.0079 — **the text was 22 % larger relative to its
window at 1080p than at 1440p**, and the number of lines that fitted
changed with the resolution (15 / 18 / 18 / 17), so a ship whose list
ran to sixteen entries was complete at 1440p and cut at 1080p. There
was no wrapping at all: one entry was one line however long, and the
loop `break`s at the box's bottom edge — a weapon simply not on the
list, with nothing to say so.

**WHAT IT IS.** `ship_panel_text`, a free box in `boxes.json` inside
the `ship_panel` hole — the `picks_popup` / `picks_popup_text` split
Custom Race already uses, and the reason for it is that `ship_panel`
is a CUTOUT: its rect is the artwork's and the F5 editor locks it.
The size is that box's `font_size` times its `font_scale`, through
`Layout.font_size` **once**; 0.01296 / 0.01250 / 0.01250 / 0.01296 of
the window at the four resolutions, and the 3.5 % that is left is
`Layout.font_size`'s `int()`, which costs every box in the tree the
same.

**WRAPPED AND SHRUNK BY RENDERING** (decision 30), through
`core/textfit.squeeze_block` — new, and the colony summary's scan
panel now calls it too: that loop was the second copy of "the largest
size at which every line, wrapped, fits the box together" and
`textfit`'s own docstring says the third is the one that gets
extracted.

**AND IT DOES NOT CLIP IN SILENCE.** Below `PANEL_MIN_FONT` (8
reference px) the panel keeps whole lines and spends its last one on
`words.panel_more` with the count. **HD EXTENSION**, marked in
`layout.json` as `deviation_panel_overflow`: the original prints at a
fixed size and lets `Set_Window_(15, 282, 320, 465)` (flt1.cpp:402)
cut whatever does not fit, with no shrink, no wrap and no marker. It
also uses TWO COLUMNS — weapons at x 0x17, specials at x 0xBC, each
with its own cursor (flt2.cpp:690-740) — where HD stacks both in one,
which is why HD runs out of room sooner than the original does. That
column difference is now written down; it was not before.

`screens/fleets/fltpanel.py` is new: `fltdraw` went over the 300-line
guideline the moment the panel stopped being six lines of blitting,
and it splits at a seam (decision 6) — everything left in `fltdraw`
draws a shape at a rect; this decides a font size and a line break
from data.

**LIVE, ON A REAL SHIP.** The engine came up from this session — which
CLAUDE.md said it would not, and that note is now wrong; it is
recorded below. SAVE2 loaded, one client, the Fleets screen at 96
fields with HD drawing. **The API has no MOUSEMOTION** (`ext_api`
doc's limitations, open fixes 3 and 4), so a client cannot hover; what
works is `ACTIVATE_FIELD` on a cell, because `Scan_Fltscrn_Big_Icons_`
(flt2.cpp:902-935) reads the field index POSITIVELY as the hover and
its negative as the click, and `fields.cpp:172-181` hands it in
positively. That scanned the Sabre at Draconis — 10 lines, three
weapon entries and four specials — and the panel drew all ten. With
`ship_panel_text` dragged to a third of its height, the same ship
shrank to the 8 px floor, kept five lines and printed the marker —
**"+5 more"** in the wording that shipped a few hours later; the
captures in the evidence folder carry the longer first version, which
is what was on screen at the time. Evidence in
`~/orionlayer-fixtures/evidence/work_order_151/`.
SAVE1-6, 8, 9 and 11 byte-identical before and after; SAVE8 never
touched; SAVE10 logged at `07b2dd62…` and unchanged.

**THE LONGEST LIST IN THAT SAVE IS THE ORION GUARDIAN'S, AND IT CANNOT
BE SCANNED.** Sixteen lines — five weapons and eight specials — but
`flt1.cpp:614` only scans while `_PLAYER_NUM == _fltscrn_stack_owner`,
so a monster stack has no panel. The longest the player owns is eleven,
which fits. The overflow path is therefore exercised by the box, above,
and by the smoke test at the struct's own maximum: 8 weapon slots
(`ship.WEAPON_SLOTS`) and 39 specials, 50 lines.

**A CORRECTION TO CLAUDE.md, EARNED BY A RUN.** "AND THAT IS NOT
ENOUGH FROM INSIDE A SANDBOXED SESSION — CAUSE OPEN" described
orion2re stopping after `mox2: data space allocated` when launched
from a session. It did not stop today: with `DISPLAY=:0`, the
determined `XAUTHORITY` and `SDL_VIDEODRIVER=x11`, it ran through to
`ext: server started on port 17362` and served a full live acceptance.
The note stays in CLAUDE.md as history with today's contradiction
beside it, because what changed is not established and "it works now"
is not a cause either.

Smoke **231 -> 233**: the panel's size comes from its box and is the
same share of the window at all four resolutions, and nothing is
dropped without the marker. Both red-proved — putting the old
`rect.height * 0.055` back gives *"panel_font_px is 10, the box asks
for 14.0 reference px"*, and removing the marker gives *"the last line
is not the marker, so 32 lines went missing without a word"*.

**ONE DEAD KEY FOUND — REMOVED THE SAME DAY, ON DATA'S DECISION.**
`inset_hint` and `status_hint` carried `"font_scale": 0.8` and the
`text` skin never reads it — `Box.render` sizes from
`style["font_size"]` alone (default 16), so both had always rendered
at 16 and the 0.8 had never done anything. It is out of both
resolution sets and **nothing moved on screen**, which is what makes
it a deletion rather than a change. `Box.render` is untouched, and the
unification is parked under "What is missing" above, with the reason:
the third box in that state is the colony summary's
`planet_paragraph`, whose `font_scale: 1.6` IS read, in the 1440 set
only, and composing the keys in `Box.render` would apply it twice at
one resolution and not the other.

**AND THE MARKER LOST ITS DEVELOPER HALF.** `words.panel_more` was
"+{n} more — make the panel taller in F5"; Data's decision of the same
day is that the editor is not the player's business, so the player
sees **"+{n} more"** and the rest — which box, how big it is, how many
lines it held, at what size, and what was asked for — goes to the log
from `fltpanel._log_overflow`, once per change rather than once per
frame. A smoke assertion refuses F5, `font_size`, `boxes.json` and
"editor" in the player's string, and a second one refuses a
`font_scale` on any `text` box of this screen, so the dead key cannot
grow back while the unification is parked.

This session (20 September 2026, work order 151, Stop 2): **the
frame canvas is 3840x2160 from now on (decision 70), and the new
Fleets frame is built but NOT worn yet.** Data's three decisions on
151 are answered in `doc/briefs/151-stop2-progress.md`.

**What is in the tree.** Decision 70 in `doc/v3_fundament.md` with its
own check — every `screens/*/assets/frame.png` is either the size it
had when the entry was filed or 3840x2160, and a third size fails, so
the rule cannot quietly become an intention. Smoke **230 -> 231**, both
count documents moved with it. `tools/fleets_frame_build.py` builds the
frame from `screens/fleets/assets/_src/fleets_frame_4k_map165.png`: it
rebuilds Support and Combat unlit at their own widths by a 3-slice of
the Leaders plate (60 px of plate kept at each end, chamfer measured at
22), and cuts the 32 openings to their own shape so the chamfers
survive and the painted stars and labels end up INSIDE a hole rather
than being retouched off the art. The source sha256 is verified before
anything is written, because every constant in that module is a
measurement of that one image.

**ACCEPTED AND SWAPPED IN**, same day, second commit.
`screens/fleets/assets/frame.png` is now the build at 3840x2160
(sha256 258eec69…), `boxes.json` carries the 32 derived boxes and the
six re-seated ones, and `fltgeom.py` and `layout.json` describe the new
canvas. The v4 frame (1445x811, sha256 4667e86d…) is out of the tree
and in the history.

**The map answers Stop 1's sharpest finding by itself.** The new
source's hole is 1812 x 1101, aspect 1.6458, stretching the galaxy's
own 1.265 by **1.301x** — against v4's 1.3027x and the original's
1.3248x. The frame Stop 1 measured stretched it 1.953x; this one is
0.13 % from what the screen already does, so no code changes and
nothing is letterboxed.

**Five boxes were stale before this order, and the swap re-seats all
five.** `status_hint` sat 151 px ABOVE the band it belongs to and
`status_text` 164 px above it — neither was inside its own parent;
`icon_area` did not contain its own twenty cells and `button_band` did
not contain its own seven buttons; `inset_hint` sat 63 % down the map
instead of on the bottom strip `fltgeom.hint_rect` documents. All five
were seated for the v3 one-opening frame and never re-seated when v4
cut 32 holes. The regenerator keeps non-cutout boxes verbatim, which is
decision 3 working correctly and is also how they survived unnoticed
for a frame and a half. After the swap every one of the five is inside
its parent and `inset_hint` is at 0.895 of the map's height, which is
the rule's own 163/182.

This session (19 September 2026, work order 142 A): **the Fleets
screen waits instead of flashing the original.** `Screen_Control_`
ticks at the top of its loop and dispatches after it (mox2.cpp:40), so
the first snapshot that says screen 4 still carries the galaxy map's
field list; 139 A made that visible and 140 measured it — 24 strangers,
then one — and every open showed the game's own picture for about a
second. The new state is **WAITING**, recognised by the field
`Add_Fleet_Screen_Fields_` adds LAST,
`Add_Hidden_Field_(0, 0, 639, 479, "", 0)` (flt1.cpp:1262). It keeps
HD's own picture up, sends nothing (`_inert`, which is a different
question from `wants_original`), and ends when the list arrives and on
nothing else — decision 21, no timer. `FOREIGN_FIELDS` is left for the
case it was built for: our list plus a native box's own fields.

**The marker was checked against recorded live lists, not assumed:**
none of the galaxy map's four in `tools/galaxy_box_fields.json` carries
a full-screen field, and the one list that does is a message box's
catcher with hotkey ESC (textbox.cpp:246) — which is why the hotkey is
part of the test. Smoke **225 -> 226**.

**Work order 142 B: field 0 is dropped once, in
`core.game_state.parse_fields`.** Decision 59 has said "never field 0"
since 14 September, and until now that was an INTENTION sixteen
consumers had to keep on their own — of which two did not: the Planets
screen's `_send_available` asked the whole list for a hotkey, and its
`_return` took the first ESC field and ACTIVATED ITS INDEX, so a stale
hotkey in slot 0 would have sent `ACTIVATE_FIELD 0`. 141 A had already
paid for the same shape on the Fleets screen. Dropping it once makes
the rule a property instead of an intention. **The indices stay the
engine's** — `FieldInfo.index` carries the array index
`ACTIVATE_FIELD` sends, and leaving the entry out renumbers nothing —
and `tools/ext_diag.py`'s raw reader still sees slot 0, deliberately.
The per-consumer filters stay: they cost nothing, they document the
rule where a reader meets it, and `injection._signature` legitimately
wants the whole list. Smoke **226 -> 227**.

**Work order 142 C: a debug input socket, marked TOOL and off unless
asked.** It exists because a live acceptance has to follow a CLICK
PATH and a session driving this project cannot move the pointer —
140 and 141 both had to fall back to `livesend` and said so.
`core/debuginput.py` accepts one JSON object per line on a Unix socket
in `$XDG_RUNTIME_DIR`, calls `pygame.event.post` and stops: from there
a debug click IS a click and takes the same path through
`_handle_events`, `_handle_click` and `_showing_original` that a real
one does (decision 5 stated for input). The switch is the environment
variable `ORIONLAYER_DEBUG_INPUT` and NOT a setting — a setting can be
saved by accident and `core/usersettings.py` writes back keys it does
not know. The socket is 0600, read back off the filesystem rather than
trusted from the umask, and the listener refuses to hand itself over
if the mode is anything else. One log line when it opens, the shape of
the build line. Both states are forced in the check, neither read off
this machine. Smoke **227 -> 228**; `main.py` joins the over-300 list
at 304 code lines.

This session (19 September 2026, work order 146): **the Fleets screen
rebuilt in Data's v4 frame.** `screens/fleets/assets/frame.png` is
`fleets_frame_v4.png` shipped unmodified at its own 1445x811 (sha256
`4667e86d…`), and it cuts **32 holes** where v3 had one opening — so
the boxes are now DERIVED from the artwork (decision 3) by a new
`name_holes_fleets` rule in `tools/frame_holes.py`, and
`tools/fleet_boxes.py` is superseded. `tools/frame_holes.py
screens/fleets/assets/frame.png --write` is the command.

**THE FRAME IS AN HD INVENTION** — the native Fleets screen is flat
blue plates under a "FLEET OPERATIONS" title bar (FLEET.LBX 0,
flt1.cpp:385) and has nothing like it. Marked in `fltgeom`, in
`layout.json`'s `frame._note` and here, with a smoke check on all
three.

Sixteen boxes lost `thin_border` for the new `skin: "none"` in
`core/box.py`: inside a hole the frame is the border. The skin had to
be NAMED — removing a style defaults to `"panel"`, which drew a filled
panel with its own chamfered outline along every rail.

**The doubled Support/Combat label is explained and fixed.** FLEET.LBX
9 and 10 are whole buttons with the words baked into the pixels, so
blitting the lit face and drawing HD's label on top printed each word
twice; HD now draws only the lit FIELD, colour measured from that
frame — (8,8,80), palette 0xA1 — under its own label.

Two v3 checks were REPLACED rather than deleted (both were about the
one-opening frame): the single-hole assertion became a 32-hole block
that names every hole and holds every box to it, and "every box inside
the opening" became "inside the reference area, every derived box on
its hole, and the scroll column on the painted bar". The class-B
intrusion budget now accepts a screen's DECLARED chamfer and asserts
the declaration covers the intrusion.

Live on SAVE4 with one client: `btn_return` fired from its new
hole-derived position and the game changed screen. `main.py` gained
**F8**, a TOOL that saves the pygame surface, because the compositor
placed the window at (-985, -565) and answered a fullscreen request
with "granted 1x38" — the game rendered correctly and could not be
photographed. Smoke stays at **230**.

This session (19 September 2026, work order 142 D): **the Fleets
screen in the original's look.** The grid cell draws the ship's own
picture — `SHIPS.LBX ship_type + colour * 50`
(`KEN::Do_Get_Ship_Picture_Seg`, ken.cpp:466) — on the original's own
grid plate, cut out of FLEET.LBX 0 where the original paints it
(flt1.cpp:1130); the inset is black because `graphics::Fill_(..., 0)`
fills it black (movebox.cpp:38, palette index 0 read as `(0, 0, 0)`)
and carries the original's 5x5 star sprites, FLEET.LBX 34..44 at frame
0, offset `-2, -2` (flt1.cpp:1441-1444, movebox.cpp:84-85), clipped to
the box as the original clips it; the screen's colours are the
original's, from the palette `fonts::Load_Palette_(8, 0, 255)` installs
(flt1.cpp:557), with the index and the engine line for each in
`colors.json`'s `fleets._source` — the fleet screen's text is GREEN
(palette 116, `FLT2::_normal_colors`), which this project had been
drawing blue-white.

**HOW THE ORIGINAL COLOURS A SHIP, read three times before it was
right.** Not a remap table and not tinted artwork: the sprites are
drawn in palette indices 192..239, which the screen palette leaves as
placeholder green, and `KEN::Load_Player_Ship_Palette_` (ken.cpp:71)
loads SHIPS.LBX `colour * 50 + 49` and installs ITS embedded ramp
(`animate::Draw_Palette_`, ken.cpp:106). Slot 49 of every colour set —
the 2x1 entry that looks like a placeholder — is the palette carrier
and is the whole mechanism. The SPRITE is chosen by `previous_owner`
and the RAMP by the current owner, so a captured ship keeps its old
hull in its new colours; both indirections go through
`_player[idx].color`, which this screen was not doing at all.

**Two corrections to things this tree asserted.** `SHIPS.LBX` holds
449 entries, not the 450 the index arithmetic implies, and slot 49 of
every set is a palette carrier rather than a ship — so a picture is
also not one size (52x48, 52x52, 55x55 and 51x49 all occur) and
nothing may assume one. And `_fleet_galaxy_star_seg` is declared
`[11]` (mox.h:110) with all eleven loaded, so the fleet screen's
black-hole index 10 is **not** the out-of-bounds read `fltdraw` and
`colonyrows` both recorded it as; 10 is the colony screen's overrun,
and the fleet screen's own eleventh sprite. Invisible while both drew
the same flat dot.

Extraction follows decision 38: `tools/fleet_art_extract.py` hands the
raw LBX blobs over untouched and `screens/fleets/fltart.py` decodes
them at load time through `core/lbx`, which gained one shared palette
decoder rather than a second transcription of `{changed, r, g, b}`.
**The files are never committed and never shipped** (decisions 40 and
42): gitignored, and the check refuses them tracked under any name.
A fresh clone has none of them, so the cell falls back to the name and
the builder's colour and the screen says how to extract — both states
forced in the check, neither read off this machine. The ship-picture
OMISSION is lifted and the marking records that it was ever there.
The status strip is now EMPTY with nothing hovered, because
`Print_Fltscrn_Scanned_Star_Name_` is called only under
`if (_galaxy_map_scanned_star > -1)` (flt1.cpp:397) — HD had been
inventing a line the game never prints. The two filter radios show
their state from the FLTS block at last. Smoke **228 -> 229**.

This session (19 September 2026, work order 141): **the Fleets screen
is READY, live, for the first time** — and the fixtures now carry the
field the engine always sends.

**A.** `fltwire.foreign_fields` skips field index 0, with the reason
from the source: `fields::Clear_Fields_` sets `_fields_count = 1`, not
0 (fields.cpp:207), so slot 0 is never cleared and no `Add_*_Field_`
ever writes it, while `SerializeFields` sends every field from `i = 0`
(ext_api.cpp:326).

**B. Every fixture list carries a field 0 now, and the split is the
lesson.** The RECORDED fixtures
(`tools/galaxy_box_fields.json`, `tools/game_menu_fields.json`) always
had it — they were captured live, and their first row is
`[0, 0, 0, 0, 0, 0, 0]`. The HAND-BUILT ones did not, and that is
exactly where 137 A's fault hid for two days. `FIELD_ZERO_ROW` is one
constant with junk geometry rather than zeros (zeros are falsy; the
recorded fixtures already cover the all-zero shape), and both halves
are asserted: a re-recording that loses field 0 fails, and a hand-built
Fleets list without one fails.

**Nothing else fell over**, and the reason is worth keeping rather than
counted as luck: the only two consumers that could have been hurt
already knew. `OriginalView.find_field_at` skips `index < 1`
(original_view.py:127) and `game_menu.nodes.real` drops it
(nodes.py:46). The fallback fixture now gives slot 0 a FULL-SCREEN rect
that covers the click point, so that skip is a real test instead of a
comment.

**C. Two residual hazards, read only and NOT changed.** Both are in the
Planets screen and both come from asking the list a question without
excluding slot 0: `_send_available` (screen.py:142-144) answers "is
there a field with this hotkey" over every field, and `_return`
(screen.py:277-279) takes the first field whose hotkey is ESC **and
activates its index** — so a slot 0 carrying a stale ESC would make HD
send `ACTIVATE_FIELD 0`. Decision 59's "never field 0" is exactly this
and neither line obeys it. The full table and a recommendation on
dropping field 0 centrally are in the report.

**D. Live.** `HD draws: fleets, game screen 4` — three Katana in the
player's colour, the inset with real stars, SCRAP correctly dimmed
where nothing is selected, and the whole screen against the original's
own picture in
`~/orionlayer-fixtures/evidence/work_order_141/02_native_left_hd_right.png`.
The Fleets button came back off the live list as field 12 at
`(167, 434)-(230, 471)` type 13 hotkey 0x46 — `mainscr.cpp:1396` to the
pixel. SAVE1-6, 8, 9, 11 and SAVE10 byte-identical; no selection, no
scrap, no move; the engine was left running.

This session (19 September 2026, work order 140): **the Fleets screen
live — and it is ONE FIELD.** Data started orion2re from the desktop
session and this session connected to it as the only client.

The reason 138 could not see and 139 made visible, in the log and in
the window:

```
11:55:24.393 galaxy_map: Action: fleets (field 12)
11:55:24.504 dispatcher: screen: galaxy_map -> fleets (game screen 4)
11:55:24.535 orionlayer: original shown: fleets, game screen 4 — 24 field(s)
             … (0, 0, 0, 0) type 0, (-1, -1, -1, -1) type 8 ×5 and 18 more …
11:55:25.630 orionlayer: original shown: fleets, game screen 4 — 1 field(s)
             in the live list that this screen does not build:
             (0, 0, 0, 0) type 0.
```

The first line at 24 strangers is the transient 139 A predicted and
did not suppress: the snapshot already says screen 4 while the field
list is still the galaxy map's. **The steady state is one stranger,
and it is field index 0.**

**`fields::Clear_Fields_` sets `_fields_count = 1`, not 0**
(fields.cpp:207), so slot 0 is never cleared and no `Add_*_Field_` ever
writes it — while `SerializeFields` sends every field from `i = 0`
(ext_api.cpp:326). The fundament has said so since decision 59 —
*"never field 0, which after a message box carries whatever geometry
the list held before"* — and work order 137 A's field-set rule did not
know it. One dummy field made every Fleets field list foreign, which
is exactly why the screen was never seen. **The fault is 137 A's and
the fix is NOT applied**: it is one `continue` in
`screens/fleets/fltwire.foreign_fields`, and the wording is in the
report.

Everything else validated on the real list: all 92 fields but slot 0
are recognised, the three grid cells, the eleven control origins, the
inset star fields, the small ship icons, the debug field and the
screen-filling catcher. RETURN came back live as `(556, 430)-(628,
456)` — exactly 73 x 27, the extent work order 137 E4 derived from
LEADERS — and RELOCATE as `(441, 380)-(530, 408)`, 90 x 29 against the
help rectangle's 89 x 28, which is why that rule matches on the ORIGIN
and not on the extent. The FLTS block read stack 2, owner 0, 3 icons,
`ship_idx [3, 4, 2]`.

**Part C, named and not changed:** at 4:3 the fallback note does cover
the picture — the bottom 24 native rows, native y 456..479, at 1024x768,
1440x1080, 1600x1200 and 1920x1440 alike. On the Fleets screen that is
RETURN's last row; on the galaxy map it is the lower part of the nav
buttons (434..471). At 16:9 and ultrawide the overlap is zero.

SAVE1-6, 8, 9, 11 byte-identical before and after; SAVE10 unchanged
too. No selection, no scrap, no move. The engine was left running for
Data. Evidence in `~/orionlayer-fixtures/evidence/work_order_140/`.

This session (19 September 2026, work order 139 A-D): **a fallback
says why — in the log and on the screen.** 138 found the Fleets screen
handing over with nothing anywhere saying why, and `fallback_reason()`
with one caller in the whole tree.

- **One log line per change**, at `main.App._verdict` (main.py) and
  nowhere else: every screen that hands over passes through
  `_showing_original`, so none of them needs a rule of its own. The
  reporting itself is `core.fallbacknote.Reporter`, beside the drawing
  of the same sentence, so the line and the note cannot disagree. On
  CHANGE only — the method is asked twice a frame — and the key
  carries the REASON, so a screen that stays down for a new reason
  still writes a line. A screen with no `fallback_reason` is written
  as `no reason given` in as many words.
- **Every screen switch is one line** with the game's own id
  (`core/dispatcher.py`). Until now a switch left no trace at all, and
  138 had to infer it from which screen sent the NEXT click.
- **The first line of every log says which OrionLayer is running** —
  `core.config.build_line`, git asked rather than a number written
  into the tree, and `unknown` rather than an exception when git
  cannot answer. 138 could not say which commit Data's run was on, and
  the answer decided whether a rule that had never run live was even
  in that build.
- **The reason is drawn over the game's picture**, `core/fallbacknote.py`,
  marked **HD EXTENSION**: the original has no second renderer to fall
  back FROM, so it has no such state to explain. It goes in a band the
  picture does not use — the pillarbox at 4:3 in a wide window,
  measured 240 px at 1080p and 760 at ultrawide — takes the picture
  rect from `OriginalView.placement` rather than repeating that
  arithmetic (decision 5), fills from `background_cockpit.png` like
  the help popup, wraps by rendering (decision 30), shortens with its
  own marker rather than cutting, takes its frame wording from
  `assets/shared/fallback/labels.json` (decision 15) and **swallows no
  click**: `_handle_click` is untouched and knows nothing about it.
  No reason means no note, so decision 22's plain fallback and F12's
  mode look exactly as they did.

Shown red three ways: logging per frame instead of per change, the
switch line removed, and the note placed over the picture. Renders at
1080p, 1440p, ultrawide, 2160p and 4:3 in
`~/orionlayer-fixtures/evidence/work_order_139/`. Smoke **224 -> 225**.

**Work order 139 E: the display was reachable all along, and the probe
was the fault.** `xdpyinfo` is not installed on this machine, so
`xdpyinfo -display :0` was answering `command not found` — and work
orders 134 and 138 both read that as "no display" and parked their
live part on it. A tool may report that it cannot measure something;
it may not report the thing as absent, and this is that entry with a
missing binary in the role.

Measured instead, with what is there: Xwayland runs on `:0`,
`XAUTHORITY` already points at mutter's own auth file, and SDL opens a
real window through it — `x11: OK`, while `SDL_VIDEODRIVER=wayland`
fails with "the video driver did not add any displays". The recipe is
in CLAUDE.md under the live-run rules, with the auth file DETERMINED
rather than typed, because mutter renames it at every login.

**F is parked all the same, and WHY IS OPEN.** With all three
variables set, orion2re still stops after `mox2: data space
allocated`: the process sits at 0 % CPU in state `S` at
`rt_sigsuspend` and the launching shell exits 144. This paragraph
first read that as "suspended from outside", and **work order 140 A
withdrew the reading**: `T` is stopped and `S` at `rt_sigsuspend` is a
process waiting on a signal of its own, and 144 is `128 + 16` =
SIGSTKFLT, not SIGUSR1 (10). The observations stand, the conclusion
does not, and the cause is open. What Data would have to do is one
step and is in the report. SAVE1-6, 8, 9, 11
and SAVE10 are byte-identical to the work order 138 run; nothing was
loaded and nothing was sent.

This session (19 September 2026, work order 138): **why the HD Fleets
screen does not appear — diagnosed as far as this machine allows, and
STOPPED at the live part.** Nothing was fixed; nothing but this
paragraph and the brief changed.

**What is NOT the cause.** orion2re is on `orionlayer-local` at
`e6199966`, both patch commits are ancestors of HEAD, `ORION2RE_EXT` is
ON, `cmake --build --preset linux-debug` says "ninja: no work to do",
and the binary carries `ext::Select_Fltscrn_Ship_` — the function open
fix 28 adds and nothing else has. `version_check.py` reports all ten
patches APPLIED and the three version strings agreeing. OrionLayer is
at `origin/main`. The dispatcher maps game screen 4 to `fleets`.
**`ACTIVATE_FIELD 12` is the Fleets button**, which the parked file
left unverified: `mainscr.cpp:1394-1399` adds colonies, planets,
fleets, leaders, races, info consecutively, and Data's own log shows
colonies 10, planets 11, leaders 13 and info 15 all reaching their
screens — there is no room between 11 and 13 for anything but the
Fleets button at 12.

**How "the HD screen does not appear" is produced.** `main._showing_
original` (main.py:245-246) asks the top screen's `wants_original()`,
and `FleetsScreen.wants_original` (screens/fleets/screen.py:138) is
true whenever the View is not READY. So a Fleets screen that cannot
vouch for what it would draw shows orion2re's own picture in
OrionLayer's window — which from the outside is indistinguishable from
the HD screen never arriving. Data's log (10:29:11 and 10:29:41)
carries `galaxy_map: Action: fleets (field 12)` twice and nothing from
`fleets` after either.

**AND THE REASON IS INVISIBLE, which is the finding of its own.**
`fallback_reason()` is never logged and never drawn: its only consumer
in the tree is `tools/researchphases.py:177`, a research-screen tool.
The dispatcher logs no screen switch, and `screens/fleets/` holds one
`log` call in all (screen.py:311, a send with no live field).
`logging.basicConfig` (main.py:16) adds no file handler, so the log is
whatever stderr is redirected to. **Not fixed** — the correction is
proposed in the report and is Data's to release.

**Part B stopped: no reachable display.** `xdpyinfo -display :0` fails
although `DISPLAY=:0` is set (the session is Wayland). The engine was
started once and stopped at `mox2: data space allocated`, the same
point work order 134 recorded, before `ext::Init()` and therefore
before port 17362 ever opens; every later attempt was killed at once.
SAVE1-6, 8, 9, 11 and SAVE10 hash identically before and after
(SAVE7 does not exist). Evidence in
`~/orionlayer-fixtures/evidence/work_order_138/`.

This session (19 September 2026, work order 137): **a field the Fleets
screen did not build hands back to the original, and the map sends nothing while the game
is elsewhere.** 136 D found HD
sitting `READY` over a game waiting in a native modal: SCRAP's
confirmation box adds two hidden fields and clears nothing
(gendraw.cpp:172-173), the screen id stays 4, the FLTS block keeps
arriving, and the validation only asked whether every displayed cell HAS
a field. `fltwire.foreign_fields` now knows the whole set
`Add_Fleet_Screen_Fields_` builds, read out of the builders
(flt1.cpp:1177-1263) in three shapes — exact rectangle where the source
gives four numbers, exact ORIGIN where the extent comes from FLEET.LBX
at runtime, and as a class for the two families that are one per star
and one per ship icon. A field outside it is `FOREIGN_FIELDS`, which
hands over, names the strangers with their rects, sends nothing, and
returns to READY by itself when they go. Smoke **219 -> 220**.

**Which other screens read their field list on presence alone**, as a
reading and not a change: `colony_summary` (`colonysend.field_at`,
colonysend.py:126), `planets` (screen.py:142 and :277) and `new_game`
(screen.py:361) all ask "is there a field with this key / at this
point" and nothing else. Of those, `colony_summary` and `planets` CAN
meet a native box — every pop-move refusal answers with `GENDRAW::Help_`
(colmove.cpp:21, :78, :156, :377, :465) and the Planets send path calls
`Confirmation_Box_`/`Warning_Box_` (plntsum.cpp:235, :268, :287, :299) —
and `new_game` has none in `newgame.cpp`. The galaxy map is a third
shape: `mapboxes.classify` names the boxes it knows and ignores the
rest, and the map can meet a box (`User_Box_` at mainscr.cpp:1456,
:1491, :1507 and mainscr_main.cpp:462, :495, :624, :718). `game_menu`
and `research_select` already classify or validate the WHOLE list —
`nodes.classify` returns None for a list it does not recognise and the
caller draws nothing — which is the shape the Fleets screen has now.
Nothing was changed on any of them.

**And `mapinput.map_click` now refuses outside screen 0** (decision 33).
It was already true and true by accident — the dispatcher routes input
to the top screen — and 136 B's gate made saying it out loud worth
doing: while the id is not 0 the state the click is computed from is the
last screen-0 one, so the click would look perfectly reasonable and
would land in another screen's field space. Smoke **220 -> 221**.

**Fundament entry 70 was NOT filed, and the tree-wide grep is why**
(work order 137 C, which made the entry conditional on there being no
reader of `ship_icons` or `map_scale` outside `screens/galaxy_map/`).
There are six, in three kinds:

| file:line | field | what it is |
|---|---|---|
| `screens/fleets/screen.py:126`, `:248` | `ship_icons` | the Fleets inset's own ship markers — the data is THIS screen's while it is up |
| `screens/fleets/fltwire.py:309` | `ship_icons` | 137 A's field-set rule: a small icon's field top-left IS `_ship_icon[i].x/y` |
| `tools/ship_icon_check.py:99`, `:106-114` | both | a live diagnostic against a running game |
| `tools/zoom_probe.py:68`, `:81`, `:99`, `tools/zoom_check.py:62`, `tools/nebula_check.py:136` | `map_scale` | live probes |
| `tools/ext_diag.py:231` | `map_scale` | a wire dump, re-derived from the bytes rather than from `GameState` |
| `core/mapcoords.py:72` | `map_scale` | `view_triple`, a helper on whatever state its caller hands it |

`core/game_state.py` is the parser and not a reader. **The colony
screen's galaxy inset is clean** and was the one the order named: brief
58's inset does not zoom at all, so `colonyrows.galaxy_inset_stars`
(colonyrows.py:383) recovers `max_map_scale` from `MAP_MAX_X`/`MAP_MAX_Y`
through `zoomtables.max_map_scale` and reads `stars`, never `map_scale`
and never `ship_icons`. The Planets and Fleets insets call the same
function with their own box.

Also measured while it was cheap: widening the "no module reads
`client.state`" assert to the whole tree would FAIL today —
`screens/new_game/screen.py:360-361`, `screens/research_select/screen.py:336`,
`core/original_view.py:149` and the two editor modules all read it, each
for the field list. Whether the gate grows to the Fleets screen, and
whether that assert is worth widening on its own, is Data's.

**The Fleets optics** (work order 137 E, same session). Seven points:

- **The three strut stubs are out of the artwork.** 174 px to
  transparent, nothing painted, the cut line measured off the adjacent
  ring edge rather than typed
  (`~/orionlayer-fixtures/incoming/fleets_frame/cut_strut_stubs.py`).
  The opening now measures **L1 R0 T2 B0** against a budget of 2, where
  it was L1 R0 T4 B4 — better than the L1 R0 T2 B1 the order asked for.
  The master's own two steps stay, and a check holds both halves: the
  three stub rectangles clear, the two steps present.
- **`fleets` is in the class-B measurement** and the stride is gone —
  every row and every column, not `edge // 40`. `colony_summary` and
  `galaxy_map` read the same either way. It is **not** in class A:
  that one builds each screen at twelve sizes with no snapshot, and the
  Fleets screen then draws seven text surfaces, under the floor class A
  refuses to measure below. Class A waits for a fixture that hands this
  screen a snapshot; the lists are split with that reason in the file.
- **No box sits on a `thin_border`'s own 1 px line**, tree-wide: 95
  nested boxes in 71 groups at every resolution. Ten of them were on
  this screen, and the cause is worth keeping — its groups AND its
  controls are help rectangles from the same table
  (evanhelp.cpp:154-165), and the original gives a group and its first
  control the same left edge. It can; it draws no outline there. So
  **the group gave way, not the control** (`fltgeom.GROUP_PAD`, 2 native
  px), which is decision 54's rule one level up. Six named exceptions,
  of which two are REPORTED, NOT FIXED and belong to other screens:
  `custom_race` `picks_header` (L0 T0 R0 inside `race_picks_panel`) and
  `empire_identity` `preview_header` (L0 R0 inside `preview_panel`).
  The other four are boxes that are never drawn together.
- **RETURN's box is its own field.** It always was, and the entry said
  "right and bottom from the help strip" — and 556 + 73 - 1 IS 628, so
  the wrong derivation produced the right rectangle and would have gone
  on doing so until help 374 moved. It now takes LEADERS' extent, the
  same row and the same artwork family, and a check refuses any control
  rect equal to the help strip (decision 38).
- **The two empty areas say what is missing.** A `text` box each
  (decision 37) with the wording in `layout.json` (decision 15), and an
  OMISSION marking beside the four `fltwire` already carries. The inset
  is empty because relocation and move orders are not built
  (flt1.cpp:640, :649) and there is **no screen-level path back to the
  original** to send the click to — `wants_original` is the View's
  state alone and F12 is the application's mode — so it is a hint and a
  marking and nothing more. The status strip was the harder question:
  `Print_Fltscrn_Scanned_Star_Name_` (flt2.cpp:338-522) prints one line
  out of thirteen HESTRINGS, keyed on `MOX::_galaxy_map_scanned_star`,
  which is **on no wire** (FLTS carries `scanned_small`/`scanned_big`,
  which are icons and not the star), and on the move preview that is
  already an OMISSION. So it cannot be filled from the wire and is
  marked; HD keeps drawing the part it can say, the scanned stack's
  star name.
- **Two highlighted cells are the original's own state**, not a fault:
  `Set_Fltscrn_Big_Icons_` (flt1.cpp:1610-1616) is the ALL button and
  selects every icon, and SCRAP exists only while the count is above
  zero (:1185). The panel follows the SCANNED ship and never the
  selection, which is asserted with the two set to different ships.
- Renders at all four resolutions and a before/after crop of every
  changed place: `~/orionlayer-fixtures/evidence/work_order_137/`.

Smoke **221 -> 224**.

This session (19 September 2026, work order 136): **state a screen
rewrites for itself belongs to that screen, and the map takes none of
it.** 135 gated `s_ship_icon` and left `map_scale`, so the map held
screen-0 icons against a screen-4 scale — two reference frames in one
picture, which is the fault decision 35 is about, one layer down. Every
write in `flt.cpp`, `flt1.cpp`, `flt2.cpp` and `officer.cpp` was read
against what `ext_api.cpp` serializes: exactly two snapshot fields are
rewritten and on the wire, `_cur_map_x`/`_cur_map_y` are not written by
either screen at all, and FSEL's stack is written once on EXIT
(flt1.cpp:827). So `ships.IconGate` is now `ships.ScreenStateGate` with
its fields in one dict, `GATED_FIELDS`, each carrying the engine line
that writes it; the smoke check iterates that dict instead of naming a
field. **The rule is "screen 0 only" and not "not screen 4"**, and that
is not tidiness: the Officers screen (id 29) makes both writes too
(officer.cpp:905, :857/:1191), so a list of guilty screens would have
been wrong the day it was written. `viewctl.park_game` is deliberately
outside the gate — it stops on an ABSOLUTE target read off `map_scale`,
so a frozen one is a target it could never reach — and is handed the raw
snapshot, held by a check. No fundament entry was filed; a wording is
proposed in the report and the decision is Data's. Smoke stays **219**:
the 135 check was replaced, not added.

**And the Fleets frame's opening was measured** (136 C, measurement
only, nothing changed). The typed `opening` [72, 73, 1775, 921] IS the
artwork's own hole plus `BLEED`, so the number is right and was simply
unchecked. Four opaque islands sit inside it, 1147 px in all: two are
STUBS OF THE PLANETS STRUTS, at x 1452..1478 and x 594..615, which are
exactly the strut gaps of the Planets master (between holes ending
1450/592 and starting 1480/617) — not ornament of the ring — and two
are the master's own steps, the right holes starting at y 77 where the
left start at 75 and the lower-left at x 75 where the upper starts at
74. Cost: `icon_area` loses 170 x 2 reference px at its top right and
`ship_panel` 22 x 1 at its bottom, the same at all four shipped
resolutions. **The suite's class-B pass would not have seen it**: it
samples `edge // 40` lines, which on this opening is a column every
44 px against 27 px stubs, and reports T2 B1 where every line says
T4 B4; `colony_summary` and `galaxy_map` measure the same either way
(worst 1 and 0), so tightening the stride is safe and is left for the
commit that adds this screen. The finished check is a draft at
`doc/briefs/136-draft-fleets-opening-check.py`; `fleets` is NOT in
`_FRAME_SCREENS` and no red check was committed.

**Two readings for the live acceptance** (136 D, in
`134-parked-for-data.md` as Evidence 9 and 10). A click in the Fleets
inset map sends nothing, changes nothing and does not hand over to the
framebuffer — no box on the screen carries a `field_id` and there is no
star branch — while the original makes it a relocation or a move order
(flt1.cpp:629-649). And SCRAP's native boxes are invisible to HD:
`GENDRAW::Confirmation_Box_` (gendraw.cpp:153) does not clear the field
list, it appends two hidden fields and spins in its own `Get_Input_()`
loop, the screen id stays 4, the FLTS block keeps arriving and every
big-icon field is still there — so `fltwire` stays READY over a game
that is waiting on a modal. The validation only asks whether every
displayed cell HAS a field; it never asks what else appeared.

Work order 134 is on `origin/main` at `14a6db7`.

This session (19 September 2026, work order 135): **the galaxy map
takes `s_ship_icon` from screen 0 and from no other screen id.** The
Fleets screen writes the same wire array it does not own — inset
coordinates into `x/y` (flt.cpp:54-55) and a FIELD ID into `stack_id`
(flt2.cpp:34), both serialized like any other frame — so a map drawn
from a screen-4 snapshot puts every stack in the inset's corner and
resolves a click on one to a field id, with every other number on
screen still correct. One gate, `ships.ScreenStateGate`, at the one point
where a snapshot becomes the map's state; the six readers (the fleet
render, `maplines`, `mapeta`, `mapinput`/`mapclick` and
`boxmodel.remember`) all read that state and needed no rule of their
own. Held by a check on real bytes through `parse_state`, shown red by
removing the gate. **`MOX::_cur_map_scale` is clobbered in the same
window and is NOT gated** — `flt.cpp:14` sets it to `_max_map_scale`
and `flt1.cpp:487`/`:835` restore it around `Fleet_Screen_`; recorded
here and as Evidence 8 in `doc/briefs/134-parked-for-data.md`, not
fixed, because the rule Data set names `s_ship_icon`. Work order 134
is on `origin/main` at `14a6db7`.

**And the briefs index had gone stale, which is why four work orders
were missing.** `doc/briefs/README.md` says it holds every brief this
project has been given; its table stopped at 128 while the folder held
six more files, and the work-order files for 125, 132, 133 and 134 had
never been imported at all. All four were in the paste cache — the
place that page names as the only copy there used to be — and are now
in the tree byte for byte, with the three that arrived as bare pastes
named from their own first line and the fourth from the name Data gave
it, `workorder_fleets_screen.md`. The index is complete in both
directions and a check holds it there, so the next import that is not
indexed fails the suite. Smoke **217 -> 219**.

This session (18 September 2026, work order 133): **the galaxy map
wears frame v3, and its holes are cut from geometry rather than from a
threshold.** The render came with no alpha and its openings painted
solid black, so nothing could be keyed by brightness; every hole is cut
from edges measured on the drawing at the half-way luminance crossing,
with a 1 px anti-aliased edge. The six nav slots now read at exactly
equal height and top edge. Section at the end of "What works". Smoke
**215**.

This session (19 September 2026, work order 134): **the Fleets screen,
built in one run — frame, screen, wire and checks — and NOT ACCEPTED.**
The frame is the Planets ring with its struts removed, one opening, cut
by THICKNESS rather than a threshold. The screen seats the original's
sixteen rectangles into that opening under one factor. Its content
cannot be reconstructed — three routes were followed to the line that
closes each — so two engine patches were written under the protocol
(open fixes 27 and 28), and the screen refuses loudly in four named
states when they are not there. **No live acceptance has run: the
display server is unreachable, the live part is parked in
`doc/briefs/134-parked-for-data.md`.** Smoke **215 -> 217**.

Work order 132 (frame set of 18 Sep) built and rejected by Data,
reverted. Number 132 stays used.

This session (18 September 2026, work order 130): **the research
select screen, and the two things it stands on.** The fallback view is
a view again — it drew a flat colour and swallowed every click, so the
two turn-start dialogs were a dead end inside OrionLayer's window; it
now shows the game's picture and forwards clicks by F12's own path. An
ACTIVATED research row is now the row the game chooses (open fix 25,
orion2re e9d07528) instead of whatever its own pointer rests on, and
the null dereference of open fix 23 is guarded. The offered rows
reconstruct and validate against the game's own field list, the names
come from the player's TECHNAME and BILLTEXT, and
`screens/research_select/` draws them — handing BACK to the fallback
whenever it cannot vouch for what it would draw. Smoke 205 -> **213**.
Sections at the end of "What works", from "The fallback view is a
view" on. **The live acceptance was NOT run** — see "What is missing".

This session (16 September 2026, work order 122): **Data's two new
frames and the three items of 15 September**, one commit per item so
each reverts alone. The sections are at the end of "What works",
from "Galaxy map: frame v2" on. (The lead paragraphs for 14 and
15 September were never written; those sessions' sections are
there too, dated.)

This session (13 September 2026, briefs 95/96), last: **the colony
list wears Data's palette, RETURN is the sort keys' size, and the scan
box's paragraph and disc are boxes.** Rows stripe A/B by list index
and the scanned colony's band is filled — an HD EXTENSION, decision 57,
with no hover key because the hovered row is the scanned row
(colsum.cpp:880-890). Panel base, header background and text, and the
cell outlines come from Data's table; every one of those colours lives
in `colors.json` only (`palette.require`, no code default), and
`panels` in `layout.json` names keys instead of typing the inset's
black. RETURN 24 → 18 in both lists. `planet_paragraph` (text skin)
and `planet_disc` (rect only) sit inside `planet_info` under
`layout_reference.json` `planet_info_parts`, draggable in F5 and
written back there; `planet_disc_gap` and the padding arithmetic are
gone. Smoke 125 -> **129**. See "Brief 95 Run 2" below.

This session (13 September 2026), earlier: **the output panel's rows
wear icons, with a line between them** — brief 92, decision 56. Six
31x31 masters cut from Data's AI-generated sheets by
`tools/make_output_icons.py` (derived, ignored, rebuilt by setup and
byte-checked by the suite): food, industry, research and BC beside
those rows, and a morale mask chosen in `colonyrows.morale_icon` —
negative halved morale low, everything else normal, following the row
under Unification. The icons are a DEVIATION (the original's own
counting shapes used as labels) and the separator an HD EXTENSION (the
original's box has no line, in code or in COLSUM.LBX). Size, gap and
line are data in `layout.json` under `output`. Smoke 122 -> **125**.
See "Brief 92 Run 1" and "Run 2" after the 12 September mockup table.

This session (12 September 2026): **the planets are on the
screen.** Ten discs cut from Data's own sheet by
`tools/planet_extract.py` — 54 x 54 RGBA under `assets/planets/`, one
per `PLANET_CLIMATE` — drawn at the left of every row's name cell and,
large, at the left of `planet_info`. Which disc is `s_colony.climate`,
the same field the "Terran 13/22" line reads, so the picture and the
word are one number read twice. DEVIATION: the original prints that
name at native x 12 and draws no planet; the shift is
`list.planet_icon_gap` in layout.json, data and not code. Scaled like a
figure — nearest neighbour, one cached set per pixel size, no
smoothscale — and 1:1 at 1920x1080, because the master's size was
chosen from the row icon's own height there. Smoke 120 -> **122**. See
"Data's planet discs" below, which also lists the mockup's other five
ideas as candidates.

This session (12 September 2026), last: **Data's frame gained an
eighth slot and RETURN moved into it.** `assets/frame.png` cuts **14**
holes now (sha256 `b95d0651…`, from `~/Downloads/frame.png`): the title
cartouche, the list, four bottom boxes and EIGHT in the sort row.
`return_button` is a cutout like any other again — rect from the alpha,
`[1680, 962, 130, 47]`, drawn UNDER the frame with the seven keys, the
panel fill through `render_fills`, hover over the whole box, and
**LOCKED** in the F5 editor. The plate it painted over the metal for
one day is gone with the hole that was missing, and `_editor_free` is
an empty list — the declaration that no box on this screen may be
dragged, not a missing key. Editor classes: **0 free / 6 bound / 14
locked**. Smoke stays at 120. See "The eighth slot" below.

This session (12 September 2026), last: **die Figur füllt die Zeile —
the figure's SIZE is no longer always an integer step.** DEVIATION from
decision 28, Data's decision after the A/B/C crops. The step still
answers the mod contract (`@2x`/`@3x`/`@4x`, decision 50); the drawn
size is the band less the plate's line, taken only when that buys at
least a quarter of a master row (`FIGURE_SIZE_SNAP`). So 2560x1440
goes 56 -> **76 px** and 3440x1371 56 -> **72 px**, while 1920x1080 and
3840x2160 keep the integer step and are **byte-identical — 0 pixels of
2.2 M and 8.9 M differ** against the previous commit, measured. Nearest
neighbour, so every colour stays the game's own and only the pixel grid
breaks. Smoke 119 -> **120**. See "Die Figur füllt die Zeile" below.

This session (12 September 2026), last: **the row figures sit on the
plate's inner floor, by their INK.** Anchoring the CANVAS to the band's
floor (the entry below) still floated at every size: 51 of the 54
masters ink to row 23 of 28 and the three Bulrathi to row 24, so the
transparent tail — 8 device px at step 2, 16 at step 4 — sat under
every figure. `colonytrack.figure_origin_y` takes that sprite's own
last inked row now (`colonyfigures.FigureSet.ink_bottom`, measured on
the stepped surface at load) and puts it on the row above the cell
plate's bottom border. The check reads the PIXELS: at four sizes, for
every band, the lowest inked pixel of every drawn figure — 52 cells per
size — and of the held cluster. Recorded in the same DEVIATION
marking, not a new one. See "The row figures move to the band's floor"
below, which now carries both halves.

This session (12 September 2026), before that: **the row figures sit on
the band's floor.** DEVIATION in the vertical anchor, top -> bottom,
Data's decision. The original's band is 31 native px around a 28 px
sprite — 3 px above it and **zero** below, measured from the source and
from its own framebuffer — and HD transcribed the TOP anchor into a
band that is `list_area` divided by ten, so every pixel the band had
over 28 rows piled up UNDER the figures: 2 px at 1920x1080, where
nobody saw it, 17 at 3440x1371 and 21 at 2560x1440, where a row's
colonists floated over their own row. `colonytrack.figure_origin_y` is
the one home for the rule, the held cluster reads it through
`held_figure_y`, and the check asserts the canvas's floor against the
band's at four sizes for **every** row. See "The row figures move to
the band's floor" below.

This session (12 September 2026), last: **the PRODUCING sort label is
no longer dimmed.** All seven labels are drawn in one colour, and it is
the original's own (196, 196, 196) — measured on its framebuffer, where
all seven buttons are one field (colsum.cpp:267-273) and only the
active one differs. The dim grey was a marker that had failed as a
marker: Data read it as a wrong colour twice, and the note that
explained it was never on the screen. The four markings go with it —
the comment in `colonysort.render`, `layout.json`'s
`sort._unavailable_deviation`, the DEVIATION bullet here, and the check
that held the three together, which is REPLACED by a stronger one: the
seven words are read back out of the render and must ink in the same
colour, and in the original's. `colonyrows.SORT_UNAVAILABLE`, the
name-sort fallback and `colonypick`'s refusal are untouched — only the
drawing went. What replaces the marking is one line under open items:
Producing sorts by name until `TECHDATA::_buildings` cost is extracted
(colsum.cpp:1091).

This session (12 September 2026), the held figure re-measured at
**3440x1371** after a second report: **it is not reproducible there.**
Live against the running game on the reference save (Slot 8), the held
cluster inks from the row's own figure line at every y of every band —
delta **0 px**, in the arithmetic and in the pixels, at 1920x1080,
2560x1440, 3440x1371 and 3840x2160. The check covers four sizes now
and measures the blit at two. **Data's window is 3440x1371** — not
3440x1440, and not the 1920x1080 in `settings.json`, which is only the
startup request and is never written back. See "The held figure at
3440x1371" below.

This session (12 September 2026), **Data's new frame — the right-hand
column is gone and RETURN has no hole.** `assets/frame.png` cuts
**13** holes where the old one cut 14: the title cartouche, the list,
four boxes in the lower band and the seven sort slots. Twelve windows
claim one each, the cartouche is spare, and the two that do not are
the header (a band of the list's hole, as before) and **RETURN, which
is drawn OVER the frame** on a plate this screen paints itself — the
one FREE box in the F5 editor, written back to
`layout_reference.json` by `colonyplates.write_back` so a drag
survives `reseat`. `galaxy_inset` keeps the original's coverage
aspect inside a hole that is wider than it, and the 34 x 3 reference
px of remainder is painted BLACK (`_hole_galaxy_inset`).
**Decision 44's DEVIATION is RETIRED**: the empire readouts moved
into the lower band, the box is 451 reference px against the
transcription's 312, and the clamp fires at 0 of 12 window sizes.
Smoke 117 -> **119**. See "Data's new frame" below.

This session (12 September 2026), the redundancy audit's follow-up:
**`boxes.json` carries no rectangle for the colony screen any more.**
All twenty — the fourteen cutouts and the six columns — are derived at
load from `layout_reference.json`, the columns from `list_columns`
through `colonyplates.column_rects`. `Box.role` and `Box.locked` are
gone from the data model and from all seven screens' files; neither
was ever read. `tools/boxes_from_reference.py` is deleted, because
with no rects in the file it had nothing to write. **Measured
acceptance: 0 pixels differ** at 1920x1080 and 2560x1440, whole-screen
render before against after. See "One home for every colony rect"
below.

This session (12 September 2026), PHASE B: **the plate machinery is
deleted and the static frame is the only path** (fundament decision
55, superseding 49 for this screen). Six tools, one screen module, the
three generated plates, the rendered masks, both `.gitignore` entries,
`setup.py`'s build step and `layout_reference`'s ring and gap tables
are gone; `frame_preview` and `colony_plateless` are gone from
`settings.json` and from `load_settings`. Stage 5 folded in:
`info_style` removed. **The check count went DOWN, 122 -> 115**, which
it may do only in this shape — seven checks whose subject was deleted,
each with its replacement named. See "Phase B: what was deleted and
what replaced it" below.

This session (12 September 2026), last: **the colony screen wears one
fixed image** — Data's decision, and it is the path that ships.
`screens/colony_summary/assets/frame.png` is Data's retouched copy of
the pre-Stage-4 frame, 1672x941, plain-scaled per resolution: no
master, no `frame_build`, no nine-slice, no bevel, no rails. Its 14
holes were mapped to the 13 windows by the PRE-STAGE-4 naming rule read
out of the history, the title cartouche is left over, and the header —
which had no window at all before Stage 4 — is a strip of the list's
hole. `frame_preview` ships off; the plate and the plateless prototype
are both still here and both still green. 121 -> 122. See "The colony
screen wears one fixed image" below.

This session (12 September 2026), later: **the colony screen can be
drawn with NO frame artwork at all** — Data's decision, PHASE A, a
prototype and nothing is deleted. `settings.colony_plateless` turns
the plate off and every rectangle in `layout_reference.json` is drawn
where it is typed: fill, rim, lit line, all three through
`StyleRenderer.draw_plate`. `boxes.json` is that file plus BLEED and
nothing else, byte for byte identical to what the plate produced, so
no content rect moved. It supersedes decision 49 for this screen when
Phase B makes it the only path; until then the plates, the master and
every check on them are still here and still green. See "The colony
screen without frame artwork" below.

This session (12 September 2026): **the seven sort keys are seven
boxes again** (fundament decision 54) — a marked DEVIATION that
reverses "THE BAR IS ONE HOLE NOW" (Stage A3, 7 September 2026),
because Data's artwork cuts a slot per key and where a hole is, is not
the code's to decide. `layout_reference.json` types seven rects,
`colonysort.layout` reads one per key and distributes nothing, and the
plate has **14 windows** where it had 8. The suite went **115 -> 119**.
Three things that were not asked for and are reported rather than
assumed: the galaxy master has **six** bottom slot holes and not seven,
so the initial rects are measured off the superseded 14-hole colony
frame instead; `sort_bc` overlapped RETURN by 121 ref px and was
shrunk, not RETURN moved; and the row overran the ring by 4 px and lost
4 px of height. See "The seven sort keys take seven boxes" below.

This session (11 September 2026): **the colony screen's top and
bottom band were freed, by splitting the layout rules into the ones
we CHOSE and the ones we TRANSCRIBED** (fundament decision 53). Four
enforcements left `tools/smoke_test.py` and became report lines —
the lower band flush with the list, its three gaps equal, every gap
equal to its role's strut, and the ring pinned to the main-screen
master. Six stayed, each with a source reference. The count went UP,
114 -> 115: `tools/colony_frame_check.py` is new, read-only, and
holds the surviving rules against a PNG, which is where they can
meet artwork the suite will never have. **Verified by perturbation,
not by reading**: the lower band non-flush with unequal gaps is
green, and the sort row at a different width and split is green.
**TWO RULES THAT BLOCK THE REST WERE NOT DROPPED** — see "Two rules
of unknown parentage" below.

This session (10 September 2026), last: **the sort bar's rim was
measured and NOT rounded** — the original turns its corner on ~2
native px, HD's rim is the master's own lit edge nine-sliced with
flat corner tiles, and no radius in the data or the cutter can
change that; it needs master artwork (see "The sort bar's rim
cannot be rounded" below).

This session (10 September 2026), later still: **two lessons from
the fixtures bug went into the fundament's Diagnosis section** — a
reader whose extent comes from the same table as its contents, and
a function that fails by returning `None` — both now with smoke
checks that bite on the exact fault; and **Data decided Claude Code
may load saves and restart the game itself**, on two conditions
(see below).

This session (10 September 2026), later: **the pop move became one
command** — `MSG_SET_JOBS`, applied whole or not at all
(fundament 52), the four click-chain states deleted, 725 ms of drop
down to 55; and **the `natives` fixture turned out to have natives
after all**, hidden by a colony count of 36 where the engine reports
38 (see "The pop move is one command" below).

This session (10 September 2026), in one line each: **three prose
claims became checks** — the word lists are compared onto the
player's own estrings entry by entry (and the comment's "23 of the
26" was wrong twice over: it is 20 of 23), `colonyrows` is held
pygame-free by a walk of its import graph rather than by two
docstrings claiming it, and the figure clip check stopped reporting
a pass it had not performed on any tree without an extracted figure
set; **the sort bar's outer outline was investigated and not
changed** — it is baked into the frame plate, so rounding it is
Part 3b territory and Part 3b is deferred (see its section below);
and **Run A is answered** — the ten-drop table is now in this
document rather than only in a commit message, with what a direct
pop-move command can and cannot remove beside it, the four source
answers and a proposed command shape (see "Run A" below).

This session (5 September 2026), the Colonies screen analysed end to
end — no code, no drawing change, the record is
`doc/colsum_design_analysis.md`, in one line each: **the read side is
already solved** — the Extension API ships every `s_colony` record
WHOLE (ext_api.cpp:126-131) and the spec is verified, so every colony
value is a level-1 capability today and the work is presentation
rather than exposure; **the cost boundary is not where it looks** —
`src/ext/` is our own directory and untracked in Joes' tree, so an
additive read command diverges from nothing and Joes' tree stays at
the one `platform.cpp` hunk; **six leverage points**, the best of
which is five `extern` values (`COLSUM::_first`, `_g_sort_index`,
`_list_col[10]`, `COLONY::_g_colony_n`, `COLMOVE::_cluster_colony_n`)
that would retire the pixel reading of the scroll thumb entirely and
turn the row-to-slot mapping from an inference into a reading;
`COLCALC::Colony_Job_Production_` is const-correct down the whole
chain (colcalc.cpp:1444), so a "what would this move be worth"
evaluation on a scratch copy is safe by the TYPE SYSTEM;
`SETTLER::Pop_Tries_To_Settle_` already separates decision from
action and names eleven refusals with an ETA, which is decision 33's
shape for free; **`s_colony.max_population` is a dead field** —
written only by the savegame reader (savegame.cpp:268, :322), so
mirroring `Planet_Max_Population_For_Player_` was right; **the
42-slot track spends half of every row** — measured, the best colony
in the reference save reaches 22 of 42 and the smallest 4, and the
"same cell size everywhere" property survives deriving the width
from the empire's own maximum; **more screen does not buy more rows**
— `Layout.scale = min(sx, sy)` letterboxes 440 px away on each side
at 3440x1440 and still draws ten; and the recommended design keeps
click-click, because `Get_Cluster_`'s "everything after the clicked
one" already makes the group size selectable and the preview already
teaches it. Overall impact if built: **LOW-MODERATE**, additive and
inside our own directory.

This session (5 September 2026), the order inside a job group — an
investigation, no patch and no drawing change, in one line each:
**`pop[]` has no order at all**, which is the answer to the question
that was asked and it is answered from the WRITING side — everything
that appears is appended at `pop[n_pops]` (growth colcalc.cpp:2387,
androids :3802, settlers settler.cpp:49), everything that disappears
is replaced by the LAST entry (six sites, all
`pop[hole] = pop[--n_pops]`), a job change moves nothing at all, and
`Enforce_Population_Limits_At_Colony_` SHUFFLES the whole array
(invasion.cpp:721) on four occasions of which one is **a building
completing** — Biospheres, in a game with no war in it; the engine
DOES sort `pop[]`, in `aidudes.cpp:742`, androids and natives to the
front, and only for players whose `objectives !=
PLAYER_OBJECTIVE_HUMAN`, so it cannot reach a colony this screen
draws; **the draw order is a different question and is the only
ordering the original imposes on what a player sees** — state, then
the conquered bit, then the low nibble in the order (9, 0, 1 … 8),
and the array only innermost (coldraw.cpp:326-337); **HD keeps that
order inside a job group and the reason is not fidelity** — the
selection takes every identical pop to the END of the array while
`Pops_Identical_` compares exactly the fields the walk groups by, so
a cluster is one contiguous run of icons only while the grouping
holds, and any other order would move cells the player did not click
with every count on screen still correct (**decision 48**, and a
smoke check that fails when the grouping breaks); **the second open
test case is NOT closed and it was not the case it was thought to
be** — a foreign pop between two own ones is normal in the ARRAY and
impossible in the drawn COLUMN, so what still wants a witness is
whether our mirror reproduces the original's column for a two-race
colony; the original carries the race and android distinction in the
SPRITE and in four classes, not two — a conquered pop is a static
race portrait, a native and an android are one sprite each for every
race; and the `race_idx` loop that iterates `MASK_CONQUERED` went to
`doc/orion2re_open_fixes.md` as **item 9, a question**, which is the
only part of this that belongs on Joes' list. The reading is
`doc/pop_order_reading.md`, with every finding marked for how far it
carries — it is ONE source, it may decide a drawing, and it verifies
nothing.

This session (5 September 2026), phase 3b of pop movement — the
connection to the mouse, in one line each: **a real mouse click on
the HD colony summary now moves pops**, verified end to end with
`tools/colony_move_hd.py --commit`, which posts a genuine
`MOUSEBUTTONDOWN` into pygame's queue and lets the app route it, and
which diffs the WHOLE colony array against a prediction made before
the click — exactly the predicted pop word changed, in exactly one
colony; **the gate was the wait, for the third time and for a new
reason**: `ext::Tick()` runs `ProcessInput()` before it serializes
anything (ext_api.cpp:341-386), so the first snapshot after a send is
built from the world BEFORE the game acted, which no counter can fix
— measured, one window increment read the old `_first` at pair 1 and
the new one at pair 2 — and both loops now wait for the EFFECT with a
floor of two pairs, asserted separately in each; **`colonyicons.py`
transcribes the icon walk**, because a column is NOT `pop[]` in array
order — five nested loops (coldraw.cpp:326-337) group by state, then
the conquered bit, then the low nibble in `pop_order`'s sequence, and
only innermost by the array — and the live proof is a colony whose
last farmer icon was pop 12 while pop 11 was a scientist, so a click
past every icon took 12 and array order would have said 11;
**the fundament's pointer sentence was wrong in its mechanism**:
`Get_Selected_Pop_` passes mode 3, whose test reads the SCROLL
FIELD's value (coldraw.cpp:361), and `Find_Bar_Position_`
(fields.cpp:1702-1743) writes that from `mouse::Pointer_X_() +
_pointer_offset` at push-down — same conclusion, one more link, and
the link carries that the value survives between clicks; **every
refusal opens a BLOCKING message box** (`GENDRAW::Help_` ->
`TEXTBOX::Do_Text_Box_`, `do { … } while (Get_Input_() == 0)`,
textbox.cpp:149) over a screen the HD client is still drawing, which
is the strongest form of decision 33 yet and is why a partial move is
REFUSED here — a marked deviation, since the original performs it;
**decision 47** says a preview does not inject and the commit sends
the whole gesture, which is what buys the cancel MOO2 does not have;
**the sort key goes out again after every move**, because HD re-sorts
from every snapshot and the game only when a sort field is activated
(colsum.cpp:829-838), so a move under a production key would leave
the two lists in different orders with every value on both screens
still correct; and `Clear_Cluster_`'s call sites are colsum.cpp:804
and :938, not :802 and :937 as four documents said.

**Three answers from the review, 5 September 2026, each of which
changed something:**

- **The ProcessInput finding was audited across the tree, not only
  repaired here.** Four observe-then-send loops exist.
  `viewctl.park_game` is safe structurally — it stops on an ABSOLUTE
  target and never on a delta, so a stale snapshot costs it one
  redundant step; `core/injection.py` is safe twice over, because the
  FIELD_LIST is only sent after the game acted and the chain compares
  against the signature it fired on; the fire-and-forget injections
  observe nothing. `tools/zoom_probe.py` was WRONG — it drained
  frames for a fixed 0.6 s and compared, a timed wait, while two
  documents cited it as this project's event-driven pattern. It waits
  for the change now, with the duration as a timeout, which also
  repairs its conclusions: "this key does not scroll" is a finding
  that reached the fundament and it has to rest on having waited for
  a movement that never came. The audit and each reason are in the
  fundament, because "it was checked" is otherwise unverifiable, and
  the 4 September entry now points forward to the sharper one.
- **The floor of two pairs is a count, and decision 21 refuses
  counted waits, so the argument now stands beside the number** —
  in `core.wire_protocol.EFFECT_PAIRS`, which is its one home
  because the gap is a property of the API's tick ordering rather
  than of any screen. It is a bolt against a predicate that was
  already true before the send, not a settling time; three would
  start skipping evidence. A smoke check refuses a reader that meets
  the number without the reason, and the behavioural checks pin both
  sides of the two.
- **The sort key moved to the FRONT of the chain, and it is sent
  unconditionally.** `Sort_Col_List_` runs at exactly two places in
  the engine — screen entry (colsum.cpp:110) and the sort handler
  (:830) — and never on its own, so the game's order is frozen for a
  whole visit while HD re-sorts from every snapshot. The handler also
  sets `_first = 0` (colsum.cpp:832), so establishing the window
  first and sorting second would establish a window the sort then
  moves: sort, then establish, then the two clicks. Unconditional
  rather than "only when the key is one this move changes", because
  the question is not what our move did — it is whether both lists
  are still in one order, which nothing on the wire reports, and a
  human can re-sort the game's own visible window at any time. The
  conditional version would also need a table of which keys a pop
  move affects, which is the shape of copy this project keeps being
  bitten by. `_first` is still re-established from scratch afterwards
  even though the sort just zeroed it — shortening it would be
  remembering instead of establishing.

**The three markings this phase adds, in the form the fundament
demands — each says what the original does instead:**

- **HD EXTENSION — the cancel.** Right click, or a left click on
  neither an icon nor a drop band, discards the selection. MOO2 has
  no cancel that stays on this screen: both `Clear_Cluster_` call
  sites are leave-the-screen paths (colsum.cpp:804 and :938). It is
  allowed because the HD selection is not the game's cluster —
  nothing has been injected — and the day a preview does inject it
  has to go. In `colonypick.py`, `colonymoveui.py`, `layout.json`
  under `move._hd_extension_cancel`, and a smoke check.
- **DEVIATION — the drop rect is half the row's height. CLOSED
  8 September 2026**, one round later: the row band is the list
  window divided by `list.row_count` and the cell fills it, so the
  plate rect is the drop rect is the cell rect and the target is the
  whole band. A smoke check reads the plate's own four edges off the
  rendered surface at the drop rect's own bounds. What it was:
  *(Replaces "HD EXTENSION — a drop target per job", withdrawn
  8 September 2026: the target is a TRANSCRIPTION and always was.
  `Add_Scroll_Field_(left_x, top_y, left_x, right_x + 8, left_x,
  right_x, right_x - left_x + 8, 30, …)` (coldraw.cpp:409) is added
  in mode 1 for every row and every job, whether or not the walk
  before it emitted an icon — so an empty column is a drop target in
  the original too, and nothing about it is ours.)* What IS ours is
  its height. The original's field is 30 px of a 31 px row pitch,
  97 % of the band; ours is `bar_h`, 30 reference px of a 58 px
  `row_height`, 52 %. It does not change WHICH ROW a click lands in
  — the bands do not overlap either way and `row_at` has already
  chosen the row — but inside one row a click in the top or bottom
  14 reference px is "outside every target" and discards the
  selection, where the original would have dropped. In
  `colonytrack._column_boxes`, `layout.json` under
  `move._drop_target_note`, and a smoke check. Making the rect the
  full band is one expression and has not been taken.
- **HD EXTENSION — a click on the held pop's own group discards the
  selection and sends nothing.** Only the "sends nothing" half is an
  extension: the original's outcome is the same, because
  `Send_Cluster_` with the job the pops already hold takes the
  re-flag path (colmove.cpp:165) and releases the cluster with the
  array unchanged. Holding the selection instead would be the
  deviation.
- **DEVIATION — a partial move is refused.** The original performs
  it and then opens a blocking box. HD sends only a plan that
  completes and says how many WOULD have moved. In
  `layout.json` under `move._partial_note`, in `colonypick.py`, and
  a smoke check.
- **A MOVE THAT WORKED SAYS NOTHING — 9 September 2026, and a
  message went away rather than an extension arriving.** `move.
  complete` was "{landed} moved", drawn into `planet_info` — which
  is the LEFT HALF OF THE ORIGINAL'S OWN SCAN BOX, the description
  paragraph at native (13, 354, 80, 88)
  (`Draw_Colony_Scan_Info_`, colsum.cpp:1155) — so every successful
  move evicted a transcription to report a thing already on screen.
  The original marks nothing here at all: the only `Fill_`/`Line_`
  calls in `colsum.cpp` are the scroll thumb (:759-765), and what it
  does instead is redraw the row, which IS the feedback. Data's two
  1440p screenshots of 8 September are the pair, one with the
  paragraph and one with "1 moved" in its place. A REFUSAL still
  speaks — decision 33, and the original's own answer to one is a
  blocking text box (textbox.cpp:149) — but it is transient and
  `_render_info` takes the panel back on the next frame.
- **DEVIATION — the HD frontend's typography.** Every label on this
  screen is drawn in CAPITALS, and the sidebar drops the colon the
  original's own string carries. Data's decision, 9 September 2026.
  The original prints its seven sort keys and its six sidebar labels
  in mixed case — `layout.json` stores them that way, and
  `empire._estrings_note` records the sidebar's as `orion2_str.h`
  comments them, `ESTR_SRESERVE_SD '%sReserve: %d'`, colon included.
  **The stored labels stay the original's spelling and a smoke check
  holds them there**: the deviation is in the RENDERING
  (`colonysort.display`, `colonyempire.value_row`) and must not
  become an edit to the data, or what it deviates from stops being on
  record. The column headings are NOT part of it — the original's own
  headings are capitals, so `colonyheader` is a transcription. In
  `colonysort.display`, `colonyempire.value_row`, `layout.json` under
  `sort._typography_deviation`, here, and a check.
- **HD EXTENSION — the stranded notice, on its own strip.**
  `move.stranded` ("The game is holding colonists. Press RETURN to
  put them back.") is the one line that is neither a refusal nor a
  result, and it stands until the player acts, so unlike a refusal it
  would hold the description panel for an unbounded time. It is drawn
  across the TOP BAND of the list instead, over the rows and under
  the frame (`colonymoveui.draw_notice`). MOO2 shows no such strip —
  its answer to a held cluster is the blocking
  `TEXTBOX::Do_Text_Box_` that HD must not reproduce — which is what
  makes it an extension. The top band is the place because while the
  game holds a cluster the list is not actionable: every further drop
  compounds the mismatch. In `colonymoveui.MoveController.__init__`,
  in `layout.json` under `move._hd_extension_notice`, and a smoke
  check.

**What this session did NOT verify, stated rather than left to be
assumed:** no refusal is reachable in the reference save at all. It
has no native and no android pop, every colony's `max_farms` is 255,
and no job is within thirty of the 42 cap — so every plan it can
produce predicts "all", and the live runs are evidence that the click
LANDS, not that `plan_drop`'s branches are right. Those branches are
covered by the smoke test alone, each rule verified to bite on its
own. A save with a native or a no-farming colony would close the gap;
inventing one would not.

This session (4 September 2026), after that, in one line each: **the
exceptions list was measuring the wrong number** — decision 6 was
enforced on `wc -l`, which counts this project's own docstrings, so
of 25 files over 300 TOTAL lines only 8 are over 300 lines of CODE
and **sixteen entries left the list without a line being edited**;
three of those sixteen had been added by the three packages
immediately before and were never exceptions, `colonyrows.py` most
plainly at 141 code of 629; the ranking also INVERTED, which is what
made `colony_summary/screen.py` get split ahead of
`custom_race/screen.py` (241 code against 400) — the split is kept
for the seam it actually has and the retired reason is written down
rather than left standing; `tools/linecount.py` is now the measure
and a smoke check holds the list to it in both directions; and a note
went into `output._deviation_note` about how to read a native
production row, because the groups are separated by an EMPTY SLOT and
a negative-imports group shares the net's sprites, which is how Wolf
II's BC row was read as 18 when it was 10 plus 8.

This session (4 September 2026), phase 2, in one line each:
**`colonyselect.GameWindow` plans the game's ten-slot window** —
`COLSUM::_first` — and it sits beside `Window` on purpose, because
decision 46's corollary is that confusing HD's viewing offset with
the original's window is the available mistake and a reader who meets
only one of them is the person who makes it; the plan **establishes
rather than remembers**, always leading with enough decrements to
reach the top from any state, since nothing on the wire reports
`_first` and a visible game window lets a human move it
(platform.cpp:1379); the window's own refusals are mirrored BEFORE
the steps are counted — below ten colonies neither stepper runs at
all (colsum.cpp:210 and :226) and the increment stops at `n - 10`
because slot ten must hold a real colony (colsum.cpp:796), so the
last page is FULL and a target past it is refused rather than
clamped; **the check simulates the original's steppers and runs the
plan from EVERY reachable `_first`**, which is the only way "establish
rather than remember" is a claim and not a wish, and it verifies the
acceptance case directly: under ten colonies the plan is zero steps,
not steps that happen to be refused; `SLOTS` is pinned to the game's
ten and asserted independent of the layout, since HD's visible count
is ten only by arithmetic; and `COLXPORT::N_Colonies_`
(colxport.cpp:67) was checked to count `owner == player` and
`outpost_flag == 0`, the same pair `build_rows` filters on, so the
two lists bind — with the one caveat that it returns a table entry
instead when `_cheezy_hack_col_count_state` is set, which nothing on
the wire would report.

This session (4 September 2026), phase 1 of pop movement, in one line
each: **the four drop rules and the pick-up refusal are mirrored** in
`screens/colony_summary/colonymove.py`, and decision 33 still carries
because all five decide from `pop[]`, `n_pops` and `max_farms`, every
one in the verified `s_colony`; **the mirror answers a COUNT, not a
boolean**, because `Send_Cluster_` returns mid-cluster on a refusal
(colmove.cpp:168-173) — forty pops already in industry and a cluster
of five lands TWO and carries three, and a yes/no mirror would have
said "this works"; the conditions are transcribed AS WRITTEN
including `|| pop_state == 6`, which cannot fire today, because
transcribing costs one `or` and being right about dead code is a
claim nobody has to make — and the check for it is BEHAVIOURAL, since
the first version searched the file text and passed on this module's
own docstring; `max_farms` turned out to hold only 0 or 255
(colcalc.cpp:691-695), so rule 4 is binary in practice — a planet
that cannot farm refuses its FIRST farmer — which the fundament's
"farmers at most max_farms" reads as a capacity and is not; **the
native rule is unreachable in the original**, since
`Give_Colonist_New_Job_`'s only two callers need a cluster and
`Get_Cluster_` refuses a native before one exists, so ESTR 522
("natives can only farm or mine") cannot be shown while ESTR 382
("natives cannot be moved") can — filed as **open fix 8, a question**,
with no guess about which side is right; our own refusal wording is
in `layout.json` under `move` per decision 15, because we refuse
BEFORE injecting and the sentence is therefore ours to own; and each
of the five rules was verified to bite on its own by deleting it.

This session (4 September 2026), the rim survey closed, in one line
each: the one rule became **two** — **class A**, text this tree places
at a cutout edge, zero pixels under opaque frame alpha at every
shipped size with no tolerance, and **class B**, how far the frame
ARTWORK reaches into each hole, budgeted per cutout at today's
measurement with the corners and the non-rectangular `title` excluded;
the two are separated MECHANICALLY and not by a list — a glyph whose
clip at blit time IS one of that screen's cutouts is class B — so no
screen needs an exception; **the bleed question was measured and the
answer is "mostly"**, `bleed=0` halves the intrusion (map_area L4.2 ->
L2.0 reference px) but does not remove it, because what remains is the
bilinear rescale widening the rim's alpha ramp plus find_holes'
bounding box over a not-quite-rectangular hole — at SOURCE resolution
the intrusion is 0 to 2 px, which is what class B budgets; **class A
found a second instance the sidebar-only check could not**, one pixel
of a fifteen-character colony name at 1600x900 whose right-aligned
overflow was bounded by `list_area`'s own edge rather than by the rim,
so `text_inset` moved out of `empire` and became a screen-level
`frame_inset` that both `colonyempire` and `colonylist` read — one
number, two readers, no helper, because the third copy is the signal
and this is the second; two survey lessons went into the fundament
beside the "wrong object" entry — measure what survives the clip, and
a check's force is a property of the state it runs in (22 blits
against 65, and no star names at all in this save); and
**`doc/plntsum_reading.md`** commits the Planets reading with its
three acceptance points, since the screen waits on frame artwork this
tree cannot produce.

This session (4 September 2026), three from the side-by-side, in one
line each: **the sidebar labels were drawn under the frame at every
resolution** — `value_column` returned the cutout's own edges, and
`frame_holes.to_ref` adds 2 reference px of BLEED outward so panel
FILLS cover the anti-aliased rim, which is right for a fill and wrong
for a glyph, with the artwork's rim reaching further in on top; it was
reported as size-dependent and is not, the overlap being 2 to 4.5
reference px at every size measured from 1280x720 to 3840x2160 and
only the font size meeting it changing, so 18 px keeps the R of
RESERVE and 16 px does not; the right-aligned VALUES were losing their
last pixels to the same rim; fixed with a measured `text_inset` on
both edges, which does not widen decision 44's deviation but states it
honestly — 286 was never a column a reader could see — and a check now
asserts against the frame's OWN ALPHA that no glyph starts or ends
under it; **the shortage marker moved to the right of the value**,
which is the order the original draws its groups in (net, secondary,
imports, shortage LAST, coldraw.cpp:170-177) and also ends the "-1 12"
misreading, the pair right-aligned as a group because the widest
structural marker does not fit in `column_gap` at any shipped size;
and **which of the inset's ten colour indices has been seen is now
recorded at the colour table**, seven read off a live frame and three
— silver, blue, brown — carried by no player in the reference save,
with the obvious recovery route written down as a dead end because
`_main_palette_player_colors` (mox.cpp:903) indexes the MAIN screen's
palette and this screen runs its own.

This session (4 September 2026), the galaxy inset, in one line each:
**the small galaxy map draws** — `COLSUM::Draw_Galaxy_Map_`
(colsum.cpp:415) is one call into `MOVEBOX::Draw_Galaxy_Map_Box_` at
native (380, 349, 128, 91) with view_mode 3, and under that mode it
draws one sprite per star and nothing else, plus the scanned star's
name centred at native (444, 431) (colsum.cpp:86) which names the
SELECTED colony's star; **the transform was verified against the
original's own framebuffer**, all 99 stars of the reference save
within 2 px of ink in the 640x480 frame the Extension API reports,
and the HD render puts 99 of 99 at a worst error of 0.44 native px;
the star SPRITE cannot be shipped — `gstar.lbx` entries 23..32 — so
its shape was measured off that framebuffer instead of guessed, a 3x3
plus with a bright centre and a 3x3 ring for a black hole, which is
why the original's draw call offsets by (-1, -1); **the map does not
fill its hole and that is the visible deviation** — 128:91 uniform
scaled and letterboxed into a 451x203 cutout, the rule
`mapcoords.MapView` already applies, after the fill-the-hole version
was built and rejected on the side-by-side for stretching the galaxy
33 %; three things the original does here are NOT DRAWN and are
recorded — the scanned star's animation, the stars being hoverable
fields, and `Colsum_Connect_Galaxy_Map_Stars_`, which turns out to
fire only while a population transfer is being dragged
(`COLMOVE::_cluster_colony_n != -1`, colsum.cpp:487-498) and so has
no state in this project at all; and the panel sends NOTHING to the
game, asserted, per decision 46.

This session (4 September 2026), last, in one line each: **the
production rows drew the wrong number and now draw the original's** —
`COLDRAW::Draw_Colony_Prod_Both_` computes a net before it draws
anything, in four branches (coldraw.cpp:73-94, labelled A to D in
`colonyrows.drawn_production`) of which only one is `production[t]`,
and on the reference save the two differ on NINE colonies of eleven,
Wolf II's BC reading 18 stored against 10 drawn; **B and C are
confirmed against a running game, and A and D cannot be confirmed by
any game** — they are the same three lines (coldraw.cpp:75-78 against
:89-92), both guarded by the industry row, so only the `(int8_t)`
cast picks between them and the cast cannot change the result; the
suite is GREEN with branch A deleted and the note now says so rather
than letting a check named after A appear to hold it up; what a save
COULD still settle is D against C, and on the industry row even that
collapses, because `COLCALC::Pre_Import_Computing_` writes
`imports[ECON_INDUSTRY] = min(maintenance, production)`
(colcalc.cpp:507-511, the only write to that field in the engine) so
all four paths compute `max(0, production - maintenance)` given a
non-negative production — an assumption recorded where the conclusion
is; the distinction is kept per branch the way
`core/structs/player.py` keeps it per field rather than left to one
word covering all four;
the SHORTAGE is drawn beside it with both of the original's refusals
mirrored (never on the industry row, never with negative imports,
coldraw.cpp:152), Wolf II's single food marker confirmed live;
`production` stays in the row because the four sort keys read it and
the original sorts on the record, so the net is its own key; the
`(int8_t)` cast at coldraw.cpp:73 against the uncast test at :152 is
transcribed AS WRITTEN and filed as open fix **item 7, a question and
not a fix request**; and `screen.py` came down 666 -> 627 by moving
`_row_at` and `_visible_rows` onto `colonyselect.Window`, where the
offset already lives.

This session (4 September 2026), later, in one line each: **the
colony list scrolls**, one row per wheel notch, with all three clamps
transcribed from the original's own steppers and the visible count
derived from `list_area` rather than assumed to be the game's ten;
the wheel is an **HD EXTENSION** and the original's proportional
slider is recorded as **NOT DRAWN**; the overflow line stayed and now
counts rows above the window as well as below; **nothing is sent to
the game**, which is `doc/v3_fundament.md` decision 46 — the
original's rows are ten SLOTS, so an injected click names a position
in the GAME's window — and a smoke check drives the list to its
bottom and back and asserts zero injections, which is what lets this
ship before the synchronisation exists; and the check count stopped
having two homes and one checker, the Snapshot table below having
said 55 against a suite of 63 for four sessions.

This session (4 September 2026), in one line each: a live
side-by-side of the HD colony summary against orion2re 1.60 confirmed
**ten of ten** allocation tracks against the original's three pop
columns, filled and empty cells both, and **six of six** sidebar
values, with nothing in the drawing wrong; the galaxy inset cutout had
been named by its position among the three bottom holes and is now
named from the source — `colsum.cpp:415` draws the small galaxy map at
native (380, 349, 128, 91), which is the RIGHTMOST hole, so
`galaxy_inset` and `spare_panel` swapped and a smoke check now asserts
the rule rather than the list; and four stale statements were brought
back in line — `output_panel`'s withdrawn HD EXTENSION tag in
`screen.py`'s box list, the sidebar justification paragraph that is
settled since 2 September, the rejected `row_height` 60 sitting as a
fallback in `colonylist.py` (removed, along with `pad_y` and
`bar_height`, so a missing key raises instead of silently drawing nine
rows), and the 62/34 row arithmetic in four places, where the
conclusion was right and only the operands were old.

**The gap this document warned about is closed.** The previous
version opened with a warning that the context-help work was
described here but missing from the tree — a package lost to the
mis-copy. Both streams have now been merged into one tree and
measured there. The counts live in the Snapshot table below and
nowhere else in this file: they were restated here as well, and the
copy said 48 while the table said 49.

**The project is now a git repository, not a chain of ZIPs.** See
"Repository layout" below for what is committed, what is generated,
and the one asset set that looks generated and is not.

This session (31 August), last of all, in one line each: `s_colony`
is **verified** and promoted to `core/structs/colony.py` — `owner`,
`planet`, `n_pops` and `max_farms` all agree with the original's
colony summary from an 85-turn savegame, `n_pops` twice over
(39 against the empire sidebar, 3 against a planet description); the
`pop[]` masks came along as a separate, partly open claim, with only
`MASK_PROF` confirmed; `Spec` grew an array kind and
`tools/struct_probe.py` a `--spec` decode mode; and the displayed
maximum population turned out to be a computation rather than the
size table, which the colony list's bar design depends on.

This session (31 August), earlier, in one line each: `s_colony` (361 B)
was transcribed from `orion2.h:487-537` and its size confirmed by
compiling orion2re's own headers — 50 members, contiguous, matching
`ORION2RE_STATIC_SIZE_ASSERT(s_colony, 0x169)`, written up in
`doc/s_colony_offsets.md` as **Phase A only**, with `COLONY` in
`unverified.py` still deliberately empty because the second source
(a live probe) does not exist yet; and **decision 23 was made more
precise, not renumbered**: the header route was worded as if it
verified a struct outright, which held for `s_planet_data` because
every field there is a whole member, but `s_colony` packs race,
original owner, profession, assigned and conquered into each `pop[]`
word, and `offsetof` reaches the word without reaching its contents.
Those masks live in `pop.h` and are orion2re's own reading of the
original — a transcription of meaning, which a size assert cannot
check.

This session (31 August), latest, in one line each: the galaxy map's
sidebar help regions were pulled onto the full row band — they had
covered 87 % of the column against the original's 97 %, leaving five
dead strips where a right click opened nothing; and two deviations
from the original are now marked where they are read, one of which
`helppopup.py` and the fundament had both claimed for weeks was
already marked in `screens/*/help.json` when it was marked in none
of the three.

This session (31 August), later, in one line each: the colony summary
package and the context-help work were merged (they were built in
parallel from a common ancestor and neither knew about the other);
the delivery scaffolding was replaced with `.gitignore`,
`tools/setup.py` and `requirements.txt`; and `make_star_icons.py`
turned out not to reproduce the star sprites in the tree, which is
why they stay committed.

Earlier this session (31 August), in one line each: the colony summary screen
got its cockpit frame, its cutout-derived boxes and a live empire
sidebar; a mis-copied package destroyed part of the working tree and
the repair left two permanent tools behind, `make_manifest.py` and
`verify_tree.py`; and the delivery rules in the fundament gained the
four lessons that cost that afternoon.

Previous session, in one line each: MOO2's right-click context help
works on Main Menu, New Game and the Galaxy Map — 31 regions, the
FMTPARA format codes decoded, verified against the real HELP.LBX; the
tree lost 15 MB of files nothing referenced; and the two documents
that had drifted from `doc/orion2re_open_fixes.md` were brought back
in line with it. Earlier the same day: the decoupled HD viewport on
the galaxy map, the Custom Race Accept guard, the two named panel
skins, the on-demand black hole rotation, and the main menu's engine
version line.

This file is the volatile half: what exists today, what is missing,
and how to run things. Decisions and lessons live in
`doc/v3_fundament.md`; long investigation records live in their own
files under `doc/` and are only summarised here.

---

## Snapshot

| | |
|---|---|
| Python | 32,960 lines across 111 modules — `find . -name '*.py'`, `__pycache__` excluded, the smoke test's 6,400 included. The previous figure here (21,642 across 94) was carried from an unstated method and could not be reproduced |
| Smoke test | `python tools/smoke_test.py` — **248 checks**, headless, in `tools/smoke_suite/` since work order 162 (91 check modules, one group per screen plus a shared core; `tools/smoke_test.py` is the runner). **Two tiers since work order 158**: the bare command runs everything (~72 s here); `--fast` runs the commit gate's 241 (~32 s here). `--screen <name>` prints only that screen's sentences and the core's and is NEVER a gate. See "The gate has two tiers" below |
| Assets | 170 MB (select_race 68, galaxy_map 51, shared 23, new_game 21, colony_summary 1) |
| Screens in HD | 9 of ~20–22 (the GAME menu overlay, work order Stop 2, every dialog of the popup; colony summary draws list, sidebar, scan box and galaxy inset, and MOVES POPS — the first HD gesture that drives the game; planets, brief 101, lists, sorts, restricts and returns) |
| Setup from clone | `python tools/setup.py` (deps via the system package manager) |
| orion2re | required for live data, not for the smoke test |

### The suite is a directory — 22 September 2026, work order 162

`tools/smoke_test.py` was 22 221 lines and 1 172 833 bytes, almost all
of it inside one `main()`: several times any context window, fifteen
times work order 127's 80 KB reading budget, and getting worse with
every screen. It is the **runner** now, 557 lines, and the checks are
**91 modules in `tools/smoke_suite/`** — one group per screen plus a
shared core, executed in file-name order into ONE namespace, which is
what `main()` did with its locals.

**Nothing was lost, and that is a measurement.** The cut was made by a
script (`evidence/work_order_162/smoke_cut.py`), never by reading
blocks into a session and writing them out again. Three proofs:

| | |
|---|---|
| **AST** | the modules' statements, concatenated in order, dump identically to `main()`'s 4 020 top-level statements — asserted before a single file was written |
| **output** | the normalised ordered `ok(...)` list of a full run is identical to the baseline taken before the cut; so are 247 full, 240 fast and the 7 push-only |
| **time** | full 71.7 s before and after; fast 31.9 s before, 31.8 s after |

| | command | checks | on this tree |
|---|---|---:|---:|
| **Full** — the default, and the pre-push gate | `python tools/smoke_test.py` | 248 | ~72 s |
| **Fast** — the pre-commit gate | `python tools/smoke_test.py --fast` | 241 | ~32 s |
| **Screen** — **never a gate** | `python tools/smoke_test.py --screen <name>` | all of them, ~a third printed | the tier's |

**`--screen` narrows what a run PRINTS, not what it runs**, and the
reason is worth keeping: it was meant to skip the other screens'
checks, and the dependency closure says it cannot. The checks share
their fixtures through objects — `d.active`, an app, a laid-out screen
— that earlier checks fill by method calls no name analysis can see.
One screen's closure is **87 %** of the suite under a practical rule
and **96 %** under the only sound one, and a narrowed run died on the
galaxy map's own screen object. 157 had already refused this shape for
its caching idea: *a check that inherits another check's app is a new
class of fault this project has not had yet.* The selector also widens
itself — anything changed against HEAD outside `screens/<name>/` and
that screen's own modules turns the run into the fast tier with its
full output, naming the files.

**The size rule that keeps it from growing back** is decision 6's
shape one level up: no check module may pass 40 KB
(`smoke_test.CHECK_MODULE_LIMIT`), the five exceptions are listed above
with the reason, and the suite holds the list to the files in both
directions — along with every module declaring its group, and none of
them rebinding a name the runner owns.

### The gate has two tiers — 21 September 2026, work order 158

157 measured the suite at ~78 s and found that seven checks were about
half of it, every one expensive for the same reason: it stands screens
up at many sizes or counts. Data chose 157's Option A. **No check was
deleted, weakened or thinned** — the tiers change *when* a check runs,
never what it asserts, and all 247 run before every push.

| | command | checks | on this tree | in a clone |
|---|---|---:|---:|---:|
| **Full** — the default, and the pre-push gate | `python tools/smoke_test.py` | 247 | 79.5–80.4 s | 63.6–64.1 s |
| **Fast** — the pre-commit gate | `python tools/smoke_test.py --fast` | 237 | 38.9–39.2 s | 37.3 s |

Six runs each here, three in the clone. The commit gate falls by
**51 %** on this machine and peak memory with it, 6.7 GB → 4.8 GB. In a
clone the saving is smaller, **42 %**, and the reason is 157 §4: the
biggest push-only item is the figure pick-up's second pass over the
player's own extracted figures, which does not run where they are
absent. **The gate was always cheaper for a forker than for Data, and
the fast tier narrows that gap rather than widening it.**

**The hooks.** `core.hooksPath` names the directory, so `python
tools/setup.py` switches both on at once and a clone gets the pair or
neither.

```
tools/githooks/pre-commit   python tools/smoke_test.py --quiet --fast
tools/githooks/pre-push     python tools/smoke_test.py --quiet
```

The push hook refuses on any exit but 0, on a missing PASSED line, and
on a PASSED line that says FAST TIER — the two hooks differ by one
flag, and a hook that quietly passed `--fast` would leave the project
with two fast gates and no full one.

**The seven push-only checks**, declared in `smoke_test.SLOW_TIER` with
the reason each is expensive, and held to the `slow(...)` guards by a
check in the *fast* tier, in both directions:

| check | why it is there |
|---|---|
| figure pick-up, 1–20 figures × 3 resolutions | 28.2 s, 36 % of the suite; its second pass reads the player's own extracted figures |
| RETURN's cutout at twelve resolutions | 13.7 s; the twelve sizes are the point |
| GAME menu frame: opening, and drawn | 3.0 s + 1.2 s |
| `main._verdict`'s fallback log | 2.3 s |
| sidebar research readout | 2.3 s |
| 49 tools import in fresh processes | 2.0 s; the only expensive check that renders nothing |

**The threshold was not the ranking.** A check went push-only when it
cost at least a second **and** its own block could be skipped without a
later check noticing. The second half did the work: 157 warned that a
segment's time includes shared setup in front of it, and ranks 6, 8 and
10 of that table turned out to have safely-skippable blocks of five to
nine lines, because their cost *is* setup other checks need. They
stayed in the fast tier.

**What it costs, accepted rather than discovered.** A fault only those
seven can see now lands at push time. The drop-marker hit area and the
colony list's plating were both found by checks on that list. Both
gates were therefore proved by walking a real fault through them —
`~/orionlayer-fixtures/evidence/work_order_158/gate_proofs.txt`. **The
fresh-clone run did not move and is not replaced** (157 §6).

Three positioning systems coexist, by design:

- **Reference 1920x1080 with anchors** — main menu, select race,
  custom race, empire identity
- **Background-relative cover-scale** — new game, fully driven by
  `layout.json`
- **Frame-cutout derived** — galaxy map, colony summary and planets,
  boxes generated from the transparent holes in `frame.png`

---

## File tree

Line counts are current. Files over the 300-line guideline are listed
with their count, which is the point of decision 6: the list is meant
to stay uncomfortable to extend.

```
~/orionlayerv3/
├── main.py                       328  Entry point, window, main loop,
│                                      event routing
├── settings.json                      Window, connection, skin,
│                                      active_mods, render_mode,
│                                      language (help texts)
├── LICENSE                            MIT for code and docs; the
│                                      artwork is explicitly out of
│                                      scope, and says why
├── CLAUDE.md                          Working agreement, read by a
│                                      Claude Code session on start
├── .gitignore                         What is generated, and why
├── requirements.txt                   Pinned pygame / numpy / Pillow
├── README.md                          Overview, quickstart, hotkeys
├── MODDING.md                         Complete modding guide
├── v3_projektstatus.md                This file
├── core/
│   ├── resources.py              141  Mod-aware file resolution —
│   │                                  the heart of the mod system
│   ├── palette.py                 64  col(), for_section()
│   ├── wire_protocol.py           81  O2XE frame + FIELD_LIST bytes,
│   │                                  shared with tools/ext_diag*
│   ├── screen_names.py            74  Screen-ID -> name, ONE source
│   ├── gridlayout.py              73  grid_cell_rect, packed_grid
│   ├── screens_loader.py         101  Screen auto-discovery
│   ├── config.py                  53  Constants, paths, defaults
│   ├── mouse.py                   56  Pointer position, ONE source
│   │                                  (fullscreen offset lives here)
│   ├── cursor.py                 122  Sci-fi cursor, sized like the
│   │                                  original's
│   ├── layout.py                  65  1080p reference -> window
│   ├── box.py                    249  UI element (rect, field_id,
│   │                                  anchor, style, panel skins)
│   ├── screen_base.py            390  Base class, frame buttons,
│   │                                  key handling
│   ├── screenhelp.py             265  Right-click help mixin:
│   │                                  regions, region padding,
│   │                                  modal guards, render
│   ├── helppopup.py              346  The help panel (auto-size,
│   │                                  columns, scroll, backdrop)
│   ├── helptext.py               180  Extracted HELP.LBX strings,
│   │                                  format versioning
│   ├── helpformat.py             272  MOO2 FMTPARA control codes
│   ├── lbx.py                    132  The LBX container and the two
│   │                                  sprite formats, shared by the
│   │                                  three extractors. Images
│   │                                  nothing: Pillow stays a tool
│   │                                  dependency
│   ├── style.py                  448  Skins, fonts, buttons, panels,
│   │                                  render_text (glyph fallback),
│   │                                  draw_inner_panel /
│   │                                  draw_thin_border
│   ├── textfit.py                     Wrap, and shrink until it fits
│   │                                  BOTH ways. Extracted from the
│   │                                  help popup and the building
│   │                                  column when the move message
│   │                                  became the third copy
│   ├── banner.py                 233  Runtime-tinted MOO2 banners
│   ├── injection.py              166  InjectionChain by field shape
│   ├── mapcoords.py              183  Galaxy <-> 640x480 <-> HD,
│   │                                  MapView + SmoothMapView
│   ├── zoomtables.py             460  Zoom levels, sprite sizes,
│   │                                  font scales — ONE sizing source
│   ├── nineslice.py              127  NineSlice + tile loading
│   ├── frame.py                  207  Cockpit frame renderer
│   ├── dispatcher.py             216  Screen switching, overlay
│   │                                  layer, sub-screen lock
│   ├── game_client.py            240  TCP client (auto-reconnect)
│   ├── game_state.py             271  Snapshot parser
│   ├── original_view.py          150  Framebuffer view + input
│   ├── monsterhull.py            121  Monster hull points, copied
│   │                                  from initship.cpp (checker:
│   │                                  tools/monster_hull_check.py)
│   ├── shipparts.py              113  Ship part names (TECHNAME.LBX)
│   ├── maintext.py                86  System special descriptions
│   │                                  (MAINTEXT.LBX), not drawn yet
│   ├── structs/                       Declarative struct specs:
│   │                                  star, ship, ship_icon, player,
│   │                                  planet, nebula, unverified
│   ├── widgets/                       ListView (187), TextInput (118)
│   └── editor/                        editor.py (390), overlay.py
│                                      (229), constants.py (74)
├── screens/
│   ├── main_menu/                219  ID 10 (+ help.json)
│   ├── new_game/                 382  ID 13, data-driven (+ help.json)
│   ├── select_race/                   ID 6
│   │   ├── screen.py             322  Grid, picture mode, info panel
│   │   ├── renderer.py           174  Portrait grid
│   │   └── info_panel.py         278  Name, description, traits
│   ├── custom_race/                   Synthetic ID 50
│   │   ├── screen.py             558  Panels, picks, Accept guard
│   │   ├── renderer.py           288  Race picks + specials panels
│   │   ├── description.py        157  Trait text, markup, wrapping
│   │   ├── popup.py              151  Message box (negative picks)
│   │   └── traits.json                Traits, picks, messages
│   ├── empire_identity/               Sub-screen, two entry paths
│   │   ├── screen.py             342  Ruler, banner, home star
│   │   └── renderer.py           235
│   ├── galaxy_map/                    ID 0 (+ help.json)
│   │   ├── screen.py             805  Star field, sidebar, nav,
│   │   │                              input routing, help regions
│   │   ├── renderer.py           746  Stars, nebulas, black holes,
│   │   │                              wormhole layer, star names
│   │   ├── ships.py              529  Ship/monster icons, tinting,
│   │   │                              owner resolution, re-anchoring
│   │   ├── sidebar.py            301  Stardate + five readouts
│   │   ├── starfield.py          274  Decorative background stars
│   │   ├── ping.py               194  Home-system marker (INVENTION)
│   │   ├── viewctl.py            189  Decoupled HD viewport: zoom at
│   │   │                              the pointer, pan, game parking
│   │   ├── layout.json                Buttons, field IDs, rows,
│   │   │                              ship_icons, starfield, ping
│   │   ├── boxes.json                 map_area, sidebar, nav_* (7),
│   │   │                              sb_<row>_text / _icon (11),
│   │   │                              help_popup
│   │   └── assets/                    frame.png, map_background.png,
│   │                                  stars/, nebula/, icons/,
│   │                                  ships/<kind>/0..3.png
│   ├── colony_summary/                ID 20, frame, list, sidebar,
│   │   │                              scan box, galaxy inset, and
│   │   │                              the population move
│   │   ├── screen.py             291  the seam only: boxes, wording,
│   │   │                              client; everything else is a
│   │   │                              module beside it
│   │   ├── colonyrows.py              the numbers per colony
│   │   ├── colonylist.py              the rows: markers, cells,
│   │   │                              growth, the name block
│   │   ├── colonytrack.py             the row's geometry, and
│   │   │                              decision 5's one home
│   │   ├── colonypopup.py             the hover popup
│   │   ├── colonybuild.py             the building column
│   │   ├── colonyoutput.py            the scan box
│   │   ├── colonyinset.py             the small galaxy map
│   │   ├── colonyempire.py            the sidebar
│   │   ├── colonyselect.py            which colony is selected, HD's
│   │   │                              scroll window, and the GAME's
│   │   ├── colonyfirst.py             reading `_first` off the thumb
│   │   ├── colonymove.py              COLMOVE's five rules, mirrored
│   │   ├── colonyicons.py             which pop each icon is, and
│   │   │                              where it sits (coldraw.cpp)
│   │   ├── colonypick.py              what a click would do. Pure,
│   │   │                              and cannot send — decision 47
│   │   ├── colonymoveui.py            the state between two clicks
│   │   ├── colonysend.py              the two clicks on the wire,
│   │   │                              each confirmed by its effect
│   │   ├── colonyplates.py         90  what a window IS: the rule,
│   │   │                              EVERY rect derived at startup
│   │   │                              — cutouts from the reference,
│   │   │                              columns from list_columns —
│   │   │                              and the panel fills
│   │   ├── layout.json                frame, sort/return native
│   │   │                              click points, empire rows,
│   │   │                              the move's own wording
│   │   ├── boxes.json                 20 NAMES and 8 font sizes. No
│   │   │                              rectangle: every one is
│   │   │                              derived at load from
│   │   │                              layout_reference.json
│   │   └── assets/                    frame.png (1672x941) — the
│   │                                  frame, and the artwork every
│   │                                  rect is measured off
│   └── _template/                 50  Copy to create a screen
├── assets/shared/                     fonts, banner, cursor, skins,
│                                      help/ (labels.json + the
│                                      GENERATED help_<lang>.json)
├── mods/example_mod/                  Working example
├── doc/
│   ├── v3_fundament.md                Decisions, principles, rules
│   ├── v3_orion2re_index.md           Source-code reference
│   ├── ext_api_dokumentation_v3.md    Extension API, for Joes
│   ├── orion2re_open_fixes.md         What is asked of Joes — the
│   │                                  ONLY home of that list
│   ├── empire_identity_slowload.md    The 23-second gap: full
│   │                                  investigation record, dormant
│   ├── pop_order_reading.md           Why pop[] has no order, what
│   │                                  the original draws instead,
│   │                                  and what a save would have to
│   │                                  contain to close four open
│   │                                  points at once
│   ├── orion2re_tree_comparison.md    A / B / C: our divergence,
│   │                                  Joes' progress, and the
│   │                                  intersection. The one home
│   │                                  for those facts
│   ├── colsum_design_analysis.md      The Colonies screen end to
│   │                                  end: what the original is,
│   │                                  what OrionLayer may do with
│   │                                  it, the capability map, the
│   │                                  six leverage points, and the
│   │                                  one recommended design
│   ├── UMZUG.md                       Git/GitHub setup and the
│   │                                  day-to-day workflow (German)
│   ├── ext_screen_id.patch            Screen IDs for Select Race
│   │                                  and Custom Race — applied,
│   │                                  and carries the defect in
│   │                                  its own first hunk
│   ├── ext_ship_icon_owner.patch      Optional, not needed
│   ├── ship_icon_measurement.md       Where the icon sizes come from
│   └── starfield_measurement.md       Background star density
└── tools/
    ├── smoke_test.py           11502  Headless verification (117
    │                                  checks; the count lives in
    │                                  CLAUDE.md and the Snapshot
    │                                  table, both asserted against
    │                                  the run)
    ├── help_extract.py           171  HELP.LBX -> help_<lang>.json
    ├── ext_diag.py               473  Extension API diagnostics
    ├── ext_diag_race.py          228  Race screen field diagnostics
    ├── nebula_extract.py         100  Pull nebula sprites from LBX
    ├── raceicon_extract.py       297  RACEICON.LBX -> the population
    │                                  figures per race and one named
    │                                  file per entry, grayscale by
    │                                  index and in the game palette
    ├── nebula_asset_check.py     238  Nebula asset resolution
    ├── make_nebula_icons.py      249  Render the HD nebula shapes
    ├── make_star_icons.py        224  Generate the 36 star sprites
    ├── make_black_hole_master.py 208  Rotatable black hole master
    ├── make_ship_icons.py        207  Generate ship/monster steps
    ├── zoom_probe.py             205  What a zoom step does to the
    │                                  game's view origin (live)
    ├── colony_move_probe.py           One pop move by injected
    │                                  native clicks, predicted
    │                                  before and diffed after (live)
    ├── colony_move_hd.py              The same move through the HD
    │                                  screen: a real MOUSEBUTTONDOWN
    │                                  posted into pygame's queue and
    │                                  routed by the app (live)
    ├── starfield_measure.py      179  Background star density
    ├── nebula_check.py           161  Nebula spec check
    ├── ship_icon_check.py        158  Live owner/kind/sprite per icon
    ├── zoom_check.py             153  Zoom ladder against a live map
    ├── struct_probe.py           144  Live offset verification
    ├── make_sidebar_icons.py     129  Cut the five sidebar icons
    ├── frame_holes.py            197  WHICH hole is which box: the
    │                                  colony rule matches every rect
    │                                  to a hole of assets/frame.png
    │                                  by OVERLAP, never by order;
    │                                  galaxy_map still derives its
    │                                  boxes here
    ├── setup.py                  138  Rebuild generated artwork
    │                                  after a clone, then verify
    ├── star_icon_check.py        109  Which star sprite resolves
    ├── version_check.py               Engine version vs orion2re src
    ├── monster_hull_check.py     176  core/monsterhull.py vs src
    ├── maintext_extract.py       128  MAINTEXT.LBX -> maintext_<lang>
    └── starfield_preview.py       94  Render the field to a PNG
```

## Repository layout

The project is a git repository. `.gitignore` carries the reasoning
per line; this is the summary.

**Committed.** All source, all documentation, `settings.json` (no
secrets, and a clone should start in the last known-good state), and
every piece of authored artwork: the HD masters under `_src/`, the
sidebar `_source_sheet.png`, `_black_hole_src.png`, the nebula
`type_*.png`, the cockpit frames, the portraits and banners.

**Generated, therefore ignored.** Ship and monster steps, the five
cut sidebar icons, the black hole master, contact sheets.
`tools/setup.py` rebuilds all of it after a clone and then runs the
smoke test, so a clone can answer "did this come out complete?"
itself.

The licence to ignore a file is that regenerating it reproduces the
committed one **byte for byte**, which was checked for each of them
rather than assumed. Git stores images as whole blobs rather than
diffs, so every regeneration of a set that stayed in the repository
would leave another full copy in the history permanently — and these
are exactly the sets that get regenerated.

**`stars/` looks generated and is not.** The 36 committed sprites are
trimmed to their content, 44 to 206 px and varying;
`make_star_icons.py` as it stands emits uniform 256x256 canvases.
Some earlier version or invocation produced the tree's set and no
longer exists. The smoke test does not notice — its star checks are
size-agnostic — so ignoring them would have handed every clone
different artwork from the one all the zoom and icon work was
measured against, silently. They stay committed until the tool
reproduces them. See "Loose ends".

**Derived from the user's own MOO2 installation, never committed.**
`assets/shared/help/help_*.json` (from HELP.LBX) and
`nebula_ref/` (from STARBG.LBX). The distinction that decided this:
the HD artwork in `nebula/` is *derived* work — upscaled, redrawn,
hours of somebody's effort — while `nebula_ref/` is the original
sprite, pixel for pixel, with nothing added. That was the one place
in the tree carrying unmodified original artwork, and it left before
the repository went public.

It costs something real. Nothing else in the tree checks a nebula
master's shape or brightness, so a clone that has not run
`nebula_extract.py` cannot make that comparison. The check does not
vanish and does not quietly pass: it asserts that either the
references are present and every master agrees with them, or they are
absent and says which command produces them. The count stays at 48
either way, which is what keeps "the number must not go down" a
usable rule.

**What git replaced.** `make_manifest.py`, `verify_tree.py` and
`tree_manifest.sha256` existed because there was no version control —
a sha256 per file was the only way to find out what a bad `cp -r` had
rolled back. `git status` and `git diff` do that job continuously and
without a manifest to keep fresh. The four delivery lessons in the
fundament stay: they are about verifying a copy, and they are the
reason the repository exists.

---

**Over 300 CODE lines, knowingly** — re-measured 4 September 2026,
and the measure itself changed. Decision 6 counts CODE now: total
minus blank, minus whole-line comments, minus docstrings, each line
in exactly ONE bucket. The numbers below are produced by
`python tools/linecount.py` and transcribed, not typed, and a smoke
check asserts this list still agrees with it — the same trade the
check count makes, for the same reason.

`tools/struct_probe.py` (**478** code, 753 total), `screens/galaxy_map/screen.py` (**456** code, 776 total), `tools/colony_list_preview.py` (**403** code, 772 total), `screens/custom_race/screen.py` (**400** code, 558 total), `tools/colony_move_hd.py` (**385** code, 586 total), `core/editor/editor.py` (**359** code, 430 total), `screens/galaxy_map/renderer.py` (**336** code, 758 total), `tools/ext_diag.py` (**325** code, 473 total), `core/style.py` (**310** code, 479 total), `main.py` (**323** code, 549 total — over since work order 142 C added the debug input switch; 146 added the F8 surface screenshot, a TOOL for live acceptance on a display that renders but cannot be captured).
`smoke_test.py` is exempt by nature, **and since 22 September 2026 so
is `tools/smoke_suite/`** — work order 162 split that one `main()` into
ninety-one check modules, and they are the same file in pieces. They are
held to something stricter in its place, below.

---

**Check modules over 40 KB, knowingly** — work order 162 part 5. No
module in `tools/smoke_suite/` may pass half of work order 127's 80 KB
reading budget, and `tools/smoke_test.CHECK_MODULE_LIMIT` is the
setting. A module over it is always the same thing: **ONE section that
is bigger than the limit on its own**, and a section is one check's
block, so splitting it would split a check. The sizes below come from
the files and a smoke check asserts this list against them in both
directions.

`011_galaxy_map_galaxy_map_stand_in_exactly_amoeba.py` (**51** KB — the galaxy map stand-in: exactly amoeba and antaran reach the player-ship fallback, thirteen `ok()` calls inside one block), `013_colony_summary_colony_summary_sort_keys_seven_five.py` (**45** KB — the seven sort keys at every resolution), `031_core_figures_sit_on_the_plate_s.py` (**44** KB — figures on the plate's inner floor, four resolutions and every band, measured out of the render), `059_core_ship_weapons_end_at_the_first.py` (**43** KB — the monster and ship-part block, nineteen `ok()` calls in one run of statements), `061_core_no_archives_or_backup_copies_anywhere.py` (**40** KB — the tree-sweep block: archives, the briefs index, the decision numbers and the exceptions list).

**TWO TOOLS JOINED THE LIST ON 8 SEPTEMBER 2026 and one thing left
them both.** `colony_list_preview.py` (345 -> 410) gained `--hold`,
`--pointer`, `--native-live` and `--info-style`; `colony_move_hd.py`
(under the guideline before) gained the four drop cases and the
shortened-row verification, and crossed at 397. What was split out
instead of listed is `tools/fixtures.py` — the savegame fingerprint
table, which BOTH tools now read, so the extraction removed a
tool-imports-tool edge as well as 32 lines. What is left in each is
genuinely one thing: drive one gesture and verify it, and render the
screen and say where the rows came from. Splitting either further
would be inventing a seam to satisfy a number, which is the thing
decision 6's own amendment warns about.

**SIXTEEN ENTRIES LEFT THE LIST and none of them was edited**, which
is the finding rather than a side effect. They were never exceptions;
`wc -l` was counting the project's own documentation habit. In
descending total: `colony_summary/colonylist.py` (204 code of 657),
`colony_summary/colonyrows.py` (141/629), `colony_summary/screen.py`
(241/627), `galaxy_map/ships.py` (242/529), `core/zoomtables.py`
(169/515), `core/screen_base.py` (257/390),
`empire_identity/renderer.py` (247/383), `new_game/screen.py`
(277/382), `core/game_client.py` (224/372),
`empire_identity/screen.py` (278/372), `core/helppopup.py` (191/349),
`main.py` (246/328), `select_race/screen.py` (211/322),
`core/structs/colony.py` (86/310), `core/injection.py` (170/307),
`galaxy_map/sidebar.py` (167/301).

**Three of those sixteen were added by the last three packages** —
`colonylist.py`, `colonyrows.py` and `colony_summary/screen.py` — and
none of the three was ever an exception. Each was noted as
"knowingly over" with a justification for why the length was earned;
the justifications were true and the premise was not. `colonyrows.py`
is the plainest case: 629 total, **141** code, and 456 of the rest is
docstring and comment.

**THE RANKING INVERTED, and that cost something.**
`custom_race/screen.py` is 558 total against `colony_summary/
screen.py`'s 627 — so it sat LOWER on the old list — and 400 code
against 241. A reader working the list from the top splits the wrong
file first, and one did: see below.

`colony_summary/screen.py` was split on 4 September (a53a730) BECAUSE
IT READ 666 LINES, and that number never applied to it. Measured
properly the file was **252** code before the split and 241 after —
under the guideline both times. The split bought 39 lines of a file
that was never over.

**It is kept, and the reason recorded for it is corrected rather than
left standing.** The seam is real independently of any line count:
`_row_at` is a band number plus the offset and `visible` is the
number `Window` needs in order to clamp itself, so both are the
offset's business and neither was a new concern — and the screen
kept `_list_view`, which resolves `list_area` to screen pixels, so
taking the input stayed with the screen. That is the reason it has.
The reason it was DONE for has been retired, and this paragraph is
here so nobody reconstructs it from the commit message.

The cost was checked before deciding rather than argued about: the
one property the split gave up is that `colonyselect` imported no
pygame, and nothing in the tree depends on it. Only `screen.py`
imports the module — in the same statement that already imported
`colonylist`, listed before it, so no import order changed — and
`smoke_test.py`, deep inside `main()` long after the display is up.
No check asserts the property; the three "no pygame" notes in the
tree name `core.wire_protocol`, `ext_diag.py` and `zoom_probe.py`.
The module is still importable headless in any case, since importing
pygame needs no display. Had any of that come back positive, the two
methods would have gone back to `screen.py`.

`colony_summary/colonyrows.py` is no longer listed at all, and the
paragraph that defended its length is gone with it: at 141 code lines
there is nothing to defend. What that paragraph said remains true and
is the general rule — splitting a file to separate a value from the
evidence for it is the thing the guideline exists to prevent, not an
instance of it — and it now lives where it belongs, in decision 6.

`screen_base.py` reached 572 lines while the help code sat in it and
was split rather than listed higher: `core/screenhelp.py` is a mixin,
and none of what moved was about being a screen. `helppopup.py`
crossed the line this session (column renderer + backdrop) and is
listed instead of split, because everything in it is one widget.

`struct_probe.py` grew from 243 to 459 with the pop-nibble report and
is listed rather than split: it is one instrument with several views
of the same snapshot — hexdump, int16 columns, spec decode, and now
one named prediction — and a view that lived in its own file would
still need the connection, the spec registry and the array table from
this one.

`colony_list_preview.py` is listed rather than split because a
preview tool IS one thing, and the two halves it appears to have —
four documented scenario rows, and the machinery that renders them —
are useless apart. Most of its length is the rationale for each row:
what that row is meant to settle, and, for the race-group row, what
it cannot.

`colonylist.py` has been on and off this list twice. It crossed at
380 when the track was re-based on the population cap, split into
`colonyrows.py` (the numbers) and `colonylist.py` (the drawing) along
the seam the data flow already had, and is back at 348 now that the
name block is two aligned lines rather than one blit. It is listed
rather than split again: the obvious seam — name block against track
— is one renderer drawing one row, and the earlier split is not the
precedent for it, because that seam already existed in the data flow
and this one would have to be invented. The building column DID go to
its own file (`colonybuild.py`), and the difference is the test: it
carries a transcription with its own source and its own fitting
behaviour, so it is a thing rather than a slice.

It is on the list at 414 with that reasoning stated, which is the
uncomfortable half of the rule working as intended: the next addition
to this file should split it, not extend it.

**Deleted this session, verified unreferenced by grep first:**
`galaxy_map/assets/{map_background1,map_background2,3}.png`,
`galaxy_map/assets/stars.zip`, `galaxy_map/assets/_contact_sheet.png`
(regenerable via `--sheet`), `galaxy_map/assets/nebula/Backup{,.zip}`
(the pre-replacement nebula masters, found by the new hygiene check
on its first run), `main_menu/assets/background1.png` — 15 MB. Later
also `assets/shared/skins/default/frame/9-slice.zip`, a copy of the
frame folder it sat in whose `9slice.json` was ten days older than
the one beside it and had no `button_font_scale`. That one survived
two passes because the check only walked `screens/`; it walks the
whole tree now. The smoke test refuses archives and backup folders
anywhere. Kept: `_black_hole_src.png`, which is the INPUT to
`make_black_hole_master.py`, not a leftover.

---

## What works

### The galaxy map loads its sprites once, not once per entry — work order 161, 21 September 2026

Data, 21 September 2026: returning from Colonies, Planets or Fleets to
the galaxy map is noticeably slower than the original, while entering
is not.

**It was ours, and the wire was measured first to know that.** Over six
live transitions the new field list arrives **0.06–0.17 s** after the
screen id changes, **in both directions** — about two snapshots at the
measured ~18/s. The asymmetry was `enter()`: **galaxy_map 429–439 ms
every time**, against fleets 84, planets 31, colony_summary 27 — and
**every RETURN lands on the galaxy map**, which is why all three
screens felt the same.

**409 of those 432 ms were 81 `pygame.image.load` calls** in
`_load_sprites`, run unconditionally from `enter` although
`SpriteCache` is built in `__init__`, resize clears only the scaled
variants, and **nothing in the tree calls `SpriteCache.clear()`**.
Every reload replaced a surface with an identical one.

**The guard is keyed on the skin, the active mods, `nebula_forms` and
`sidebar_icons` — not on "loaded already".** `asset_path` resolves
through `res.screen_file`, so which file a name reaches depends on the
skin and the mods, and the last two come from `layout.json`, which a
mod can replace. A plain load-once would pin the map to artwork from an
inactive skin. `force=True` reloads regardless and has one caller: the
nebula check, which puts a test surface over the real artwork and has
to restore it.

| | 1st entry | re-entry | loads | render |
|---|---:|---:|---:|---|
| 1920x1080 | 436.5 ms | **45.3 ms** | 81 → **3** | identical |
| 2560x1440 | 436.0 ms | **49.8 ms** | 81 → **3** | identical |
| 3440x1440 | 437.5 ms | **53.4 ms** | 81 → **3** | identical |
| 3840x2160 | 448.7 ms | **63.0 ms** | 81 → **3** | identical |

**~385 ms off every return, 90 %**, and the frame byte-identical at all
four resolutions. The three remaining loads are the frame, the
background and the map background — untouched.

**The check counts loads, not milliseconds, and that is deliberate.**
The first version of the guard stored the sidebar loop's variable
instead of the key, so it never matched: renders identical, timings
unchanged, nothing visibly wrong, and no saving at all. Only a load
counter showed it. A timing assertion would also have been
machine-dependent.

**CONFIRMED IN PLAY, and that is a separate claim from the numbers
above.** Every measurement here is headless, through
`colony_list_preview.build_screen` — it says the loads stopped and the
frame did not move, and it says nothing about how the game feels. Data
played the built tree on 21 September 2026 and reported the return as
**"viel besser"**. That is the half a harness cannot give.

**What this does not explain.** Data reported 1–2 s; this accounts for
~0.43 s on top of ~0.12 s on the wire. The engine's own redraw
(`Build_Ship_Icons_`, and on one branch `Fast_Fade_Out_` before
`Add_Map_Fields_`) was read but not measured. **Whether the remainder
is still worth chasing is now an open question rather than an
assumption**: the complaint that started this is gone, so the next
session should ask Data before measuring the engine side.

### Fleets is done — 21 September 2026, work order 159

**Complete for the 22 November release.** The screen draws the grid,
the selection, the scroll bar, the seven controls and PREV/NEXT, the
inset map with its stars and relocation lines, the strip under it, and
the ship panel in **both** of the original's modes — the data readout
for a combat ship and, since this order, the HELP.LBX paragraph for a
colony ship, transport or outpost.

**What "done" means here, stated so nobody has to guess.** It does not
mean nothing is left: five items stay under "What is missing" and each
now says **AFTER RELEASE** in its own entry. It means that everything
left needs something this project does not have yet — a C++ change, a
field that is not on the wire, ground truth from a save nobody has, or
extracted artwork — and that none of them is a fault a player would
read as broken. The screen shows what it can prove and marks what it
cannot, which is the line this project draws everywhere else.

The five, with why each waits:

| | item | waiting on |
|---|---|---|
| 1 | plural weapon names | the extractor's plural field and a `FORMAT_VERSION` bump, which wants to travel with another change to that file |
| 2 | a damaged special in red | ground truth: a save with a damaged ship. Work order 159 settled the record layout and failed to locate the ship array in a serialised save — see the entry |
| 3 | Beam OCV and Beam DCV | `s_leader_data`, which decision 23 refuses, and a way to read the number the original prints |
| 5 | the strip's move preview | `_g_ship_move_info` on the wire — **one piece of work with the galaxy map's own move preview**, and it stays one |
| 6 | arrow glyphs for PREV/NEXT | the two sprites extracted; the words are decision 15's answer meanwhile, not a stopgap |

**The one thing 159 could not finish is in item 2 and is written up
there in full**, including what it DID establish — the serialised ship
record is the packed struct, 129 bytes, damage flags at @118 — so the
next attempt starts from that rather than from nothing.

### Fleets: a colony ship, transport or outpost gets the original's paragraph — work order 159, 21 September 2026

`Print_Scanned_Ship_Data_` **returns before it prints a single data
line** for `ship_type` 1, 2 and 4 (flt2.cpp:548-575): it loads one
HELP.LBX record — `0x29` colony, `0xBD` transport, `0x6D` outpost —
sets font style 3 in its own colour and prints it with
`ERIC::Print_Paragraph_Centered_Vertically_`. HD drew the full data
panel for all three, which showed **more** than the original rather
than less. It now draws the paragraph.

**THE TYPES COME FROM THE ENUM, not from a field dump.** HD had no
`SHIP_TYPE` constants at all; `orion2_consts.h:519-526` is transcribed
into `core/structs/ship.py` (`COMBAT=0, COLONY=1, TRANSPORT=2,
UNUSED=3, OUTPOST=4`) and `fltrows.PARAGRAPH_HELP` is keyed off them,
so the set cannot drift from the enum it was read out of.

**THE RECTANGLE IS 299 PX, NOT 305 — a correction.** The entry this
replaces said the original's rectangle is "305 px wide", and work
order 159 repeated it. `eric.cpp:171` declares
`Print_Paragraph_Centered_Vertically_(x, y, width, box_height, text,
color)`, so `0x12B` = **299** is the width and the box is
`(18, 282, 299, 183)`. **305 is a different number and is not wrong
where it appears elsewhere**: it is the DRAWING WINDOW,
`Set_Window_(15, 282, 320, 465)`, 320 − 15, which the tab-stop entries
above correctly use. The paragraph box sits inside that window.

**Vertically centred in the box, wrapped at HD's hole.** The primitive
prints at `y + box_height/2 − paragraph_height/2`, so a short
paragraph and a long one share a centre line. HD's hole is a different
shape at every resolution, so the wrap width is the hole's — a scaled
transcription, the same call `panel_block` already makes for the data
panel.

**MEASURED, ALL THREE FIT EVERYWHERE**, so nothing was built for
overflow:

| | 1920x1080 | 2560x1440 | 3440x1440 | 3840x2160 |
|---|---|---|---|---|
| hole | 694x242 | 925x322 | 925x322 | 1388x484 |
| colony `0x29`, 152 chars | 3 lines / 60 px | 3 / 81 | 3 / 81 | 3 / 120 |
| transport `0xBD`, 236 chars | 4 lines / 80 px | 4 / 108 | 4 / 108 | 4 / 160 |
| outpost `0x6D`, 220 chars | 4 lines / 80 px | 4 / 108 | 4 / 108 | 4 / 160 |

The transport is the longest and its block is 160 px of a 484 px hole
at 2160p. If a translation ever overflows, the panel's existing
`"+{n} more"` path takes it; no second mechanism was invented.

**THE COLOUR IS NOT TRANSCRIBED, and is marked rather than claimed.**
The original sets style 3 from `Get_Mox_Font_Colors_(3, 111, 116, …)`
with `_mox_font_colors_offset = 0x72` — a ramp over MOO2 **palette
indices** 111..116. The palette is in the player's own installation
and pinning the RGB needs it plus a native screenshot of this panel;
work order 159 was forbidden a live run. HD draws the paragraph in the
panel's existing label colour, `colors.json` carries it as
`fleets.panel_paragraph` with the reason beside it (decision 15),
`layout.json` marks it `deviation_panel_paragraph_colour`, and it is
parked in `doc/briefs/159-parked-for-data.md`.

**A CLONE WITH NO EXTRACTED HELP SHOWS THE HELP POPUP'S WORDING**, not
the data panel — falling back to the data would restore the very fault
this removes, on the machines least able to notice. Marked
`fallback_panel_help_missing`. The suite drives the three texts through
a committed stand-in under `tools/fixtures/derived/`, never this
machine's extraction.

**Nothing else on the screen moved**: a combat ship's panel renders
byte-identically at all four resolutions, before and after
(`~/orionlayer-fixtures/evidence/work_order_159/part1/`).

### Connection
TCP client parses the binary snapshot with auto-reconnect. F12
toggles HD against the scaled 640x480 framebuffer; original-mode
clicks route through `original_view.forward_click`. Screens switch
automatically from each screen's `GAME_SCREEN_ID`.

### Right-click context help — three screens, verified on real data
A transcription: `fields::Check_Help_List_` (fields.cpp:2916) runs
*before* the right button becomes Cancel, and on a hit draws the
entry and swallows the click. HD does the same. 31 regions on Main
Menu (6), New Game (11) and the Galaxy Map (14 of 15), transcribed
from the C++ tables into `screens/<name>/help.json` with the native
640x480 rectangle recorded beside each — never as box properties,
because `Box.to_dict` would drop a foreign key on the next F5 save.
That is decision 38 in the fundament; it was born as a second "36"
because two same-day sessions each took the next free number, and
was renumbered since the version-line decision had been cited first.
The walk stops at the first hit, so screen-wide fallbacks sit last,
and the smoke test enforces that ordering.

**The regions are derived from the boxes, and may be larger than
them.** A region names its boxes and the rect is their union, so it
follows an F5 nudge instead of drifting from it. That left the galaxy
map's sidebar covering 87 % of its column where the original covers
97 %: the `sb_*` boxes are sized to their content, 93 reference
pixels inside a row pitch of 109/110, so 16–17 pixels between every
pair of readouts answered a right click with nothing. A `pad_y` on
the region closes it — 7 reference pixels, the largest value that
keeps the band inside the `sidebar` cutout — without touching what is
drawn. The pad applies to every region kind rather than to the `box`
branch alone, so it cannot become a silent no-op, and it scales with
the window, because an unscaled pad is correct only at the resolution
it was tuned on.

**Two deviations are marked where they are read**, under an
`hd_extension` key in `help.json`: the stardate region fills its HD
row where the original's fills 17 of a 21-pixel one, and the
auto-sizing panel. The second is the one worth remembering —
`helppopup.py` and the fundament both stated it was marked in
`screens/*/help.json`, and it was marked in none of the three for as
long as both said so. A smoke check now walks the tree, not a list of
screens, and refuses a `help.json` that carries no marking or a
marking that does not name the 339 px wrap it deviates from.

The machinery: `core/screenhelp.py` (mixin on ScreenBase — every
screen has the behaviour, a `help.json` opts in),
`core/helppopup.py` (the panel), `core/helptext.py` (the strings),
`core/helpformat.py` (the decoder). The panel is the `help_popup`
box, F5-movable, auto-sized to its text, wheel-scrolled when too
tall — a marked HD EXTENSION against the original's fixed 339 px
box. On the galaxy map the box is centred on `map_area`, not the
window, and the smoke test asserts containment in the cutout rather
than the exact centre, so an F5 nudge is legal and sliding under the
sidebar is not. Font size reads the box's stored `font_scale`
directly, bypassing `box_font_scale`'s resolution auto-factor, which
double-scales anything not hand-tuned per resolution. Right-drag
panning survives untouched: the original's help list pointedly does
not cover the map area.

**The bodies are not plain strings.** They carry MOO2's FMTPARA
control codes; the Command Points table is four absolute column
positions (`\aX3.Frigate\aX97.-1…`), not spaces.
`core/helpformat.py` transcribes `fmtpara.cpp`: X (column) and T
(tab stops) are honoured, columns scale from the original's 339 px
paragraph space to the panel's text width (so the table lines up at
1080p through 4K), everything else is dropped and recorded per entry
as `dropped_functions`. The extractor hands the bytes over untouched
and decoding happens at load time; the file carries `"format": 2`
and a stale one is refused with the command that fixes it, because a
mangled body renders *almost* right.

**Verified against the real HELP.LBX on 30 August**: 707 records,
every id the three screens use is present, and `dropped_functions`
is empty across the entire file — the claim "nothing in the help
text uses more than X, T and the line breaks" is now a measurement,
not an assumption. Text colour is the original's RGB (72, 144, 56),
measured; title and body share it and differ only in font style,
exactly as in `Draw_Help_Entry_`.

The text itself is derived from the player's installation
(`tools/help_extract.py`, language per `settings.json`) and never
ships; until extracted, the popup says so with the command.

**31 August — the file name had three independent spellings.**
`core.helptext` built the path the loader reads, `help_extract.py`
built the one it writes, and `setup.py` checked a hardcoded
`help_en.json`. The two directions of the resulting lie: a German
install that had extracted `help_de.json` correctly was told the
texts were absent, and an English file under `"language": "de"` was
reported ok while every popup showed a placeholder. `help_file()` in
`core/helptext.py` is now the single source, all three go through it,
and the smoke test asserts they agree for `en`, `de` and `fr` — `en`
alone cannot catch it. `setup.py` also names the consequence and
prints the `--lang` the settings actually call for, because the
report was accurate and still read as optional.
OrionLayer's own wording around it lives in
`assets/shared/help/labels.json`. Not drawn, deliberately: the
per-entry animation (`anim_lbx` is preserved in the JSON so the
omission stays a decision).

### Core UI
NineSlice with per-size cache, **Aldrich** (SIL Open Font License)
with a font cache and per-character fallback for substituted
glyphs, corner glows, anchors,
per-resolution box storage, frame title bars and button bars, the mod
system, skin selection.

**F9** cycles 1080p → 1440p → Ultrawide → 4K. **F11** is fullscreen
with pillarboxing and corrected mouse coordinates. Boxes are stored
for 1920x1080 and 2560x1440.

**F5 editor**: select, drag, resize handles, arrow nudge, content
offset, font scale (Ctrl+Wheel), glow position and rotation, field
assignment, portrait zoom/pan, pannable image boxes, per-resolution
save (Ctrl+S), help overlay (H).

### Main Menu — logo, scrolling credits, engine version
The version line sits bottom right, where the original puts it, in
its own `version_text` box: right-anchored, right-aligned, drawn with
the new `text` box skin, F5-draggable like everything else.

**The number is maintained by hand, and that is a decision** (36).
The Extension API does not report it — `HELLO_REPLY` carries
`PROTO_VERSION`, which is the wire protocol's number, and the
snapshot has no version field. Appending it to the reply would have
been four backwards-compatible lines of C++ in the tree Joes
maintains, for one line of cosmetic text, so the proposal was
written down and withdrawn
(`doc/ext_api_dokumentation_v3.md`, `doc/orion2re_open_fixes.md`).

It lives in `core/config.ORION2RE_VERSION`; the word "Version" is a
template in `boxes.json`, so a translation replaces it without
touching code. `tools/version_check.py` compares the constant against
orion2re's *two* literals — `src/version.h` and `src/game/consts.h`
are separately written and can disagree with each other as well as
with us — and the smoke test asserts the number appears in exactly
one file in this tree.

Position and colour are measured, not styled. The source centres the
string on native x=517 (`Print_Centered_(0x205, …)`,
mainmenu.cpp:295); a native screenshot puts it at 516.4 with a 7 px
ink height, which also pins `font_h` at 10. The same screenshot gives
the glyph colour as RGB (104, 56, 20) against the credits' (164, 100,
40) — **the original draws its version dimmer than its credits**, at
59 % of their luma. The HD default is `credit_role` at that same
ratio rather than the raw colour of a palette OrionLayer does not
use, and lives in `colors.json` as `main_menu.version`.

### Panel skins — two, with a job each
`inner_panel` (the 9-slice art) frames pictures; `thin_border` (a
rounded blue outline) groups things. Both are box skins in
`core/box.py`, selected per box in `boxes.json`, coloured from
`panel.thin_border` in `colors.json`.

New Game pairs them: each setting image keeps its 9-slice frame, the
group box around image, title and label carries the thin border, as
does the toggle group. The smoke test asserts the containment — every
`inner_panel` box must sit inside a `thin_border` box — so the rule
survives a renamed or added panel.

Select Race and Custom Race are border-only, in every mode including
picture-select. `inner_panel` therefore has exactly one job left in
the tree: New Game's five setting pictures.

### New Game — complete, data-driven
All layout, field wiring, value maps and labels in `layout.json`.
Five setting categories via `ACTIVATE_FIELD`, three toggles via
`INJECT_CLICK`, Cancel/Accept through the frame button bars.

### Select Race — complete
5x3 portrait grid (13 stock races plus Custom Race), hover selection,
click sends `INJECT_CLICK` on the race radio. Info panel as three
independently movable boxes. Picture mode for the Custom Race
portrait. A stock portrait click injects the radio and switches to the
HD Empire Identity screen with `lock_ids=(6,)`; click and ENTER share
one code path.

### Custom Race — complete, with a local Accept guard
Three panels (Race Picks, Special Abilities, Description) plus the
combined picks/score bar, all F5-movable with their own font scales.
Exclusive trait groups and the Lithovore/Farming block are honoured
locally and mirrored to the game field by field.

**Message box on an overspent race.** MOO2 refuses a race whose
remaining picks are negative and answers with an error box.
OrionLayer tests the same condition *before* it forwards Accept, so
orion2re never receives the invalid Accept, never draws its own box
into the framebuffer, and the HD screen is never left sitting on
Empire Identity while the game stays on 50.

The box is outlined with `thin_border` and filled with the screen's
own scaled background blitted at the same window coordinates — so it
reads as bare backdrop with the panels lifted off it, and no sampled
RGB constant can go stale when the artwork changes. It is modal:
click, wheel and every key are swallowed, so ESC dismisses the
message instead of cancelling the screen. No dimming layer — MOO2 is
palette-indexed and cannot alpha-blend, so a darkened backdrop would
be an invention.

Two F5 boxes, the same split the picks/score bar uses: `picks_popup`
(panel) and `picks_popup_text` (text area with its own `font_scale`).
The box renders while the editor is open, with the real string,
because an empty panel gives no clue whether a font scale fits. The
wording lives in `traits.json` under `messages`. Word wrap measures
by rendering rather than by `font.size()`, because `render_text`
mixes two fonts wherever the DEMO font substitutes a glyph; rendered
lines are cached per (text, pixel size, width).

### Empire Identity — complete, both paths live-verified
Replaces MOO2's three dialogs (ruler name → banner colour → home star
name) with one HD screen. Custom Race Accept (lock 50+6) and stock
race selection (lock 6) both reach the *same* `Naming_Popup_` and
`Flag_Screen_` in `racesel.cpp`, so one field-shape detector serves
both without a branch.

Accept runs the InjectionChain, event-driven on FIELD_LIST: ruler name
(24 backspaces + name + Enter as one SDL burst) → banner (waits for
eight large hidden fields, then `ACTIVATE_FIELD`) → home star. ESC
returns cleanly to screen 6. The chain is not evenly spaced — the
galaxy is generated between banner and home star, in API silence —
which is why the watchdog is 10 s and holdable, a reconnect drops its
field list, and the home-star step carries its own 90 s timeout. A
failed chain switches to the original view instead of releasing
silently, so the dialog can be finished by hand.

**Progress box while the chain runs** — an INVENTION, marked in
`renderer.py`, `layout.json` and a smoke test that fails if it stops
being drawn. Two F5 boxes (`busy_panel`, `busy_text`), opaque, filled
from the screen's own background, `thin_border` outline; one bar
segment per chain step, the running one sweeping, waits over 3 s
shown in seconds. Wording in `layout.json` under `labels.busy_steps`.

### Colony Summary — frame, sidebar, buttons
The original's "Colonies" list (screen 20, `colsum.cpp`), built the
galaxy-map way: one cockpit frame PNG with 14 transparent cutouts,
generated from a black-and-white mask, boxes derived from the holes
by `frame_holes.py` — which now carries one naming rule per screen,
chosen from the path.

Live: the six empire readouts in the sidebar, transcribed from
`COLSUM::Draw_Empire_Info_` — Reserve, Income, Population, Freighters,
Food, Research, each one verified `s_player` field, with the
original's explicit plus and red-if-negative. They go through
`Style.render_text` — the reason was that `+` and `-` were on the
DEMO Bank Gothic's watermark list, and the habit is worth keeping now
that Aldrich renders them fine, because a mod's font may not. RETURN injects a click at a point inside the original's own button
(`colsum.cpp:265-273`), so no field id is needed. The seven sort
buttons now send the original's own HOTKEY instead and keep that
point as their fallback — decision 39, amended, and see "The sort bar
sends keys" below.

**Everything below was read in orion2re 1.60.0** (`src/version.h`,
`consts.h:43`). Line numbers from a 1.31 archive differ — three were
carried in from one and are corrected here: `Draw_Empire_Info_` is
colsum.cpp:**418** not 408, the justify test is fmtpara.cpp:**1057**
not 1056, and `GAME_VERSION_LABEL` is consts.h:**43** not 47.

**What `s_player`'s `verified=True` actually rests on.** A **static
assert**, not a live probe: `core/structs/player.py`'s own docstring
says the offsets come from compiling orion2re's `orion2.h` with its
`#pragma pack(1)` and reading `offsetof`, with `sizeof` landing on
the `0xf0e` in `sizes.h`. That was reproduced on 2 September 2026 and
every offset is exact — `bc` 50, `surplus_freighters` 56,
`total_pop` 266, `research_produced` 272, `surplus_food` 276,
`surplus_bc` 278, `race` 37, `tech_applications` 379, `traits` 2308.
Git adds nothing: the whole tree arrives in one squashed commit
(`e0ae910`, 31 August), so there is no per-field history to read.

**All six were read against the original's own box on 3 September
2026 and all six agreed.** `tools/struct_probe.py players --sidebar`
prints them beside the labels and signs the original uses, in the
original's order, and the reading closed the one risk that mattered:
the original showed Food **-10** and Income **+30**, opposite signs
and different magnitudes, so a swap of `surplus_food` and
`surplus_bc` would have put -10 on the Income line and been visible
at a glance. Two numbers that happened to be close, or both positive,
would have proved nothing. `race` @37 and `total_pop` @266 already
had incidental corroboration from the pop-nibble work; the other four
have it now.

**A static assert fixes the layout and cannot tell interchangeable
members apart**, which is the risk that actually bites here:
**`surplus_food` (276) and `surplus_bc` (278) are two bytes apart,
both `int16`, both net flows, both printed with an explicit sign.**
Swapped, every value on screen stays plausible and the struct is
exactly as large either way. So `tools/struct_probe.py players
--sidebar` prints the six beside the labels and signs the original
uses, for a human to hold against the game's own screen, with `race`,
`traits` and `tech_applications` along as controls — right anchors
and wrong scalars means the scalars.

A probe spec briefly duplicated the six in
`core/structs/unverified.py`, on the mistaken premise that they were
unverified. **They never were.** It is deleted, the offsets have one
home again, and a smoke check refuses any `Spec` named `s_player`
outside `player.py`.

`player.py`'s docstring now says **which evidence stands per field**
rather than leaving a spec-wide flag to imply it covers everything:
`race` @37 and `total_pop` @266 have incidental live corroboration
from other work, and `bc`, `surplus_freighters`, `research_produced`,
`surplus_food` and `surplus_bc` have none. The flag stays `True` —
flipping it is a decision to take deliberately, not in passing — but
it should not be read as more than the compile it came from.
`--sidebar` now ends with a printed **expected-vs-actual table**, six
blanks to fill from the original's own screen and a tick box each, so
the run that closes this needs eyes and not interpretation.

They are also **not one kind of number**, which is recorded per
field: `bc` is a stock, `surplus_bc` and `surplus_food` are net
flows, `research_produced` is gross, `total_pop` and
`surplus_freighters` are counts. Adding a gross to a net is the
mistake that table exists to prevent.

**What the six actually are, from source.** `Draw_Empire_Info_` is
colsum.cpp:418. The strings are NOT in the source — `Load_E_Strings_`
(estrings.cpp:11) loads them from the player's own `estrings.lbx` at
runtime — but `orion2_str.h` carries each one as a comment on the
enum, which is where these come from: 118 `%sReserve: %s%d`, 106
`%sIncome: %s%s%+d`, 114 `%sPopulation: %s%d`, 103
`%sFreighters: %s%d`, 102 `%sFood: %s%+d`, 117 `%sResearch: %s%d`.
**Only Income and Food carry `%+d`**, which is why `signed` is per
row.

**The two per-line prefixes are NOT colour attributes** — this was
got wrong first time and is worth the space. `s_0_0055110c` and
`s_1_00551110` (estrings.cpp:8-9) are the literals `"\0320"` and
`"\0321"`, and octal `032` is **0x1A, not ESC**: compiled, they are
the bytes `1A 30` and `1A 31`. FMTPARA sends 0x1A to
`Set_Justification_` and 0x1B to `Set_Current_Colors_`
(fmtpara.cpp:364-368). Only the red one is a colour —
`Red_If_Negative_Fmt_String_` (eric.cpp:176) returns `"\0332"` =
`1B 32`, and `Set_Current_Colors_` (fmtpara.cpp:1154) sets
`color_attr = code << 5`.
Red-if-negative is the original's and applies to Income **alone**;
this screen also colours Food and Freighters, and those two are
marked HD EXTENSION.

**Two findings that would have become inventions.** The six lines are
joined by `String_Builder2_` (eric.cpp:425) through `E_Strings_(71)`
= `%s%c%s` with the character `13` — a **carriage return**, not a
newline, and the whole block reaches `Print_Formatted_Paragraph_` as
one string. And that call passes **justify=3**, which is
`JUSTIFY_FULL` and **inert here**: `Complete_Line_` (fmtpara.cpp:1057)
checks the next character and drops to `Justify_Line_(0)` on CR, LF,
FF or a terminating NUL. Every line is followed by that CR, so
justify=3 never applies.

**The conclusion drawn from that was wrong twice, and is now
settled.** The two prefixes are justification codes, and the 1.60
tree says so three separate ways: `colsum.cpp:36-37` and
`estrings.cpp:8-9` spell them `"\0320"` / `"\0321"`, and
`strings.cpp:22,24` spells the same symbols `"\x1A" "0"` /
`"\x1A" "1"` — unambiguous hex, and commented in the source itself
as *"switches paragraph justification to left alignment"* and
*"to right alignment"*. `Set_Justification_` (fmtpara.cpp:999) takes
`mode = next char - '0'`, flushes the pending segment through
`Complete_Line_` when `char_count > 0`, then assigns `justify_mode`
(:1017); `Justify_Line_` (:1699) implements **mode 1 by adding the
whole remaining width to the first character's advance** — right
alignment — against `para.x2 = x + width - 1` = 623 of 640 (:657).

**One row per entry, not two.** `Set_Justification_` never advances
y; y moves only on CR, LF, VT and FF (fmtpara.cpp:322-341, where CR
falls through to `Vertical_Move_Line_Advance_`). The CR that
`String_Builder2_` joins the six with is what ends each row.

**So the invention was the other way round.** Label-left /
value-right is the transcription, and the stacked centred
label-over-value this screen drew until 2 September 2026 was the
invention. The renderer now does label-left / value-right, with the
column's width taken from the original's own 104 px paragraph rather
than a margin somebody liked.

**The width is itself a DEVIATION, and a live one — decision 44.**
104 native px is 312 reference px; the `sidebar` cutout is 286, and
`min` picks the cutout at every resolution, so the original's
proportion is never the one drawn. That is 8.3 % of the column and
26 reference px per value. The alignment is transcribed, the width is
not, and the two are marked apart. The clamp is written as `min` and
not as a hardcoded 286 so it **expires by itself** if the frame art
ever gives that hole 312 or more; the art is not being widened to
suit it, which would be deriving artwork from a deviation. The smoke
check asserts `native_width` is still read and still *larger* than
what is drawn — deleting it as dead weight fails, and the day it
stops being larger the marking should be retired rather than
restored. A smoke
check measures it in **ink at twelve resolutions**: the label's
leftmost inked column flush with the column's left edge, the
rightmost value ink flush with its right, both after subtracting the
glyph's own side bearing — measured through the same compositing the
renderer does, because an antialiased edge blends differently over
the panel fill and a fixed pixel tolerance passed at 1080p and
failed at 4K by exactly the bearing. Reverting to the centred layout
fails it by 56 px.

**`justify=3` is inert for a different reason than first recorded.**
Not because CR terminates each line — that is true and would also do
it — but because the buffer BEGINS with `s_0`, so
`Set_Justification_` assigns `justify_mode = 0` with `char_count`
still 0, before a single character is drawn. Mode 3 never reaches
`Justify_Line_` at all.

**Why this was wrong twice: an octal `032` read as `033`.** `"\0320"`
looks like ESC + `'0'` and is SUB + `'0'` — a C octal escape is
greedy to three digits, so `\032` is 0x1A, not `\033` = 0x1B. Read
as ESC it is a colour code and the six lines are plain left-aligned
text; read correctly it is a justification code and the original
does label-left / value-right.

**The same trap does NOT catch `Red_If_Negative_Fmt_String_`, which
was queried and stands.** Its literal is `"\0332"`, and there the
greedy escape takes `\033` = **0x1B**, leaving `'2'` — bytes
`1B 32`, which FMTPARA routes to `Set_Current_Colors_`
(:364-368, :1154). Three things agree: the bytes, the function's own
comment, and `colsum.cpp` itself, which spells the same effect
`"\x1B" "2"` at :567, :575 and :1189. Red-if-negative is real, is
the original's, and is kept. Two literals one octal digit apart,
opposite meanings, and the trap is on the other one.

**What IS open about those symbols is a declaration, not a value.**
`s_0_0055110c` and `s_1_00551110` exist three times in three
namespaces at two declared sizes — `const char[3]` in `colsum.h` and
`strings.h`, `const char[4]` in `estrings.h` — in two spellings, all
producing the same bytes. Nothing misbehaves; it is item 6 in
`doc/orion2re_open_fixes.md` as a **question** for Joes (which byte
does the original binary emit at `0x0055110c`?), not a fix request.

`E_Strings_(12)` is **OPEN, single source**: it has no entry in
`orion2_str.h` at all, so only its uses can be read. Every use in the
tree is consistent with the empty string — button labels where the
sprite carries the artwork, "no help", "no prefix", the not-negative
branch of `Red_If_Negative_Fmt_String_` — and consistent is not
confirmed.

**Research is absolute and carries no percent — but not for the
reason it is tempting to cite.** ESTR 117 is `%sResearch: %s%d`;
there is no `%%` in it and none in any research label. The only
entries in the whole table with a literal `%%` are 108 (maintenance
penalty), 112 (morale), 120 and 121 (worker penalty) and HESTR
`0x142`. The conclusion stands; the citation had to be the string
table rather than the field.

**`output_panel` is a TRANSCRIPTION — decision 43 is WITHDRAWN,
3 September 2026.** It was marked an HD EXTENSION on the claim that
`colsum.cpp` never draws per-colony food, industry or research. It
draws all four. `COLSUM::Draw_Colony_Scan_Info_` (colsum.cpp:1155),
reached from `Draw_Scan_Info_` at :485, loops `i < ECON_COUNT`
calling `Draw_Colony_Wee_Prod_(_g_colony_n, i, 106, y_pos, 366, 20)`
with `y_pos` stepping 18, and adds morale at (106, 421); that lands
in `COLDRAW::Draw_Colony_Prod_Both_` (coldraw.cpp:36), which reads
`colony->production[prod_type]` (coldraw.cpp:60) and draws it as
tens-and-units sprites at native x 106, y 349 upward — the
bottom-left, which is exactly where `output_panel` sits.

**Why the grep missed it.** The search was for the words
"food|industry|research" in one file. The call site contains none of
them: the value is chosen by a loop index against `ECON_COUNT`, and
the drawing lives in `coldraw.cpp`. Searching for the DATA
(`production[`) rather than the LABEL would have found it in one
step. That is decision 44's lesson from the other side — there one
definition was mistaken for the definition, here one file was
mistaken for the code path — and the marking was defended by a smoke
assertion for a day and a half, which is how a wrong marking becomes
worse than none.

The rule the entry proposed — *the original computing a value is not
permission to display it* — survives; it simply has no example here.

**Native geometry**, for re-deriving HD boxes: the empire paragraph
is x 520, y 354, w 104. A colony row is `slot * 31 + 38`; the name
column is x 12, w 89 — w 87 when the colony has an event — h 23; the
building column x 512, w 85, h 22.

**The preview draws the whole screen now — 3 September 2026.**
`tools/colony_list_preview.py` drove `colonylist.render` alone, so
the sidebar and the sort bar had no picture at all and both of the
row renderer's deviations were found by reading rather than by
looking. It now drives the real `ColonySummaryScreen.render` off a
synthetic snapshot: real `s_star`, `s_planet_data`, `s_colony` and
`s_player` bytes through the real specs, so `build_rows` and
`_render_sidebar` cannot tell the difference. **Fake the state, never
the drawing** — a preview that draws its own version of a screen is a
picture of the preview. The hand-written row dicts are gone with it,
and so is the check that they matched `build_rows`: that drift is now
structurally impossible, and what is asserted instead is that each
synthetic colony still produces the SHAPE its comment claims.

**The invariant checker was measuring the wrong object, and had been
since it was written.** It compared the FIRST ROW BAND across two
renderings, which is the same colony only while the sort leaves it
first: with `--sort population` it reported "NO — the unit moved with
the row set" every time, correctly observing that two different
colonies look different. The slot width is computed by
`track_metrics` from `POP_LIMIT_CAP` and the panel and takes no rows
at all, so it could not have moved.

Asserting `track_metrics` directly would have been worse: it is a
pure function of things the row set does not touch, so the assertion
cannot fail and therefore says nothing. What CAN fail is the render —
an earlier bar derived the unit from the widest `max_pop` in the
list, which is the fault this exists to catch. So it now finds THAT
COLONY in each rendering by its own index and compares the two
TRACKS. Not the whole band: the frame PNG bleeds three or four pixels
of metal edge into `list_area` on both sides, artwork that differs
between one y and another, and comparing bands reported 310 differing
pixels all of them in x 0..3 and 1405..1407. Verified to bite by
making the unit depend on the row count.

One thing the rewrite got wrong first and the picture caught at once:
every colony read numeral **I**. `HAROLD::Planet_Number_` counts
OCCUPIED slots before the planet, not the orbit, so a numeral has to
be earned with real planets in front of it — the snapshot now packs
filler planets carrying `colony_index -1`.

**The sidebar's numbers are chosen to be falsifiable, not
plausible.** Plausible numbers are what hide an alignment bug: six
values of similar width sit in a column whether they are right-
aligned or centred. So `bc` is 18432 and `surplus_freighters` is 7 —
five digits against one, which makes right alignment visible AS
alignment — `surplus_bc` is **negative**, so red-if-negative actually
renders for the first time, `surplus_food` is positive so the
explicit plus shows beside it, and `research_produced` is unsigned so
the sign is visibly a per-row property. All four kinds are
distinguishable in one frame: a stock, two signed net flows, an
unsigned gross, two counts.

**`--live` — 3 September 2026, and without it `--native` was never a
comparison.** The tool rendered its synthetic empire and nothing
else. A run against a game with 55 colonies at stardate 3502.4 wrote
a side-by-side whose HD half listed Vega I, Sol III, Kif II, a name
of ten W's and Nazin I over a sidebar of 18432 / -214 / 39 / 7 /
+12 / 1180, and whose native half showed Blucher II, Wolf II,
Draconis V over 878 / +42 / 78 / 17 / -3 / 27. Two different empires
presented as a comparison, with nothing in the image saying so — and
the API was reachable the whole time, since `struct_probe` read the
same game in the same minute. The tool never asked.

It asks now. `--live` takes one STATE_SNAPSHOT and hands the real
state to the real screen, so `build_rows` runs over the wire's own
colonies. It does NOT fall back to the synthetic empire when the game
is unreachable: that substitution is what the switch exists to
prevent.

**The fetch has ONE home.** `core.game_client.fetch_snapshot` —
connect, wait for `current_screen >= 0`, disconnect, return
`(state, error)`. `struct_probe` had the loop and this tool needed
the same one; the rule is that the third copy is the signal to
extract, and this was extracted at the second anyway, because what
is being copied is a protocol contract ("silence is busy, not dead")
rather than four lines of shape.

**Every image carries a provenance band**, `--live` or not: LIVE with
the stardate, the record count, how many survive the outpost filter
and how many are drawn; SYNTHETIC with "these colonies do not exist".
`--native` without `--live` writes the image and says ON the image
that it is not a comparison. This is the same class as the tenth row
that used to vanish in silence — an absence shaped like a result —
and a marking without a check is an intention, so a smoke check holds
the band.

**THE FIRST REAL SIDE-BY-SIDE, and it found things at once.** Run
against the live game at stardate 3502.4 with a framebuffer captured
off the wire:

- **The sidebar agrees exactly** — 878 / +42 / 78 / 17 / -3 / 27 on
  both halves, which is an independent confirmation of the six-of-six
  reading recorded in `core/structs/player.py`.
All five things it found have since been acted on; what they were,
and what came of each, is below.

**The tenth row — `row_height` 62 to 58.** The original windows ten
(`_list_col[10]`, filled by `Update_Col_List_` at colsum.cpp:348) and
the HD panel drew nine, because `list_area` is 619 reference px and
`pad_y` takes 14: 605 / 62 = 9. Lowering the row was the cheaper of
the two ways — `list_area` comes from the frame artwork through
`frame_holes.py` (decision 3), so growing the panel means redrawing
the frame.

**60 would have fit ten and was still wrong**, which the smoke test
caught: 10 x 60 = 600 leaves 5 px, and the "{count} more not shown"
line is about 15, so it would have been clamped back over the last
row it exists to account for. The two features compete for the same
pixels and the arithmetic has to hold both. 58 leaves 25. `bar_height`
came down 34 to 30 with it, so `row_height` minus `bar_height` stays
28 and the band "No Farming" is drawn in is exactly as wide — at 34
it would have been 12 px for a 14 px label.

**The sort is SET, not read.** `_g_sort_index` is not on the wire, so
the two lists could sit on different keys with neither being wrong.
Rather than ask for it to be serialised, the screen injects its own
key once on entry (`_push_sort_key`), and every later change goes
through `handle_click`, which injects as it goes — so they agree by
construction and there is no second path to drift. Idempotent by the
original's own design: `Switched_cmp_` has no direction toggle
(colsum.cpp:378-401), so re-sorting by the key the game already holds
re-sorts identically. Same trade as parking the galaxy map at maximum
zoom-out (decision 35): **a state you establish yourself does not
have to be read**, and the alternative was four lines of C++ in
somebody else's tree, which is decision 36's line.

**The word rule: a value carries no prefix, because the label carries
it.** The source draws this more finely than "our list is wrong".
MINERALS: colland.cpp:60-62 puts the table value into its own format
string, `E_Strings_(0x176)`, so the word "Mineral" belongs to the
FORMAT — the table holds "Rich", which is what our list held, and it
was right. GRAVITY: colland.cpp:65 prints the table entry with no
format at all, so "Normal Gravity" really is in the table — and
copying it verbatim would have rendered GRAVITY Normal Gravity, the
same fault from the other side. Our "Normal G" was neither: it was
the enum name in title case, which is how a list derived from
identifiers instead of from the screen goes wrong. Both lists now
carry the bare quality; the rule is in `words._note` so it is not
re-decided one list at a time, and a smoke check refuses a value that
repeats its own label.

**Growth: the k is a UNIT.** MOO2 counts population in thousands, and
the original prints "+63k". The panel now signs the value through
`colonyempire.format_value` and carries the "k" in the template.
Nothing divides or scales — the engine's number is printed as the
engine's number, with the unit that was always implied written down.

**Two deviations in the row, both kept, both marked — decision 45.**
The colony NAME is right-aligned and the original left-aligns it:
`Squeeze_Formatted_Paragraph_Centered_` (colsum.cpp:582) is
`center_y` ONLY (bill.cpp:205), and its sixth argument reaches
`Print_Formatted_Paragraph_` as JUSTIFY (bill.cpp:210) with colsum
passing 0 = `JUSTIFY_LEFT`. Kept, because right alignment is what
makes a 236 px column affordable. And the per-row second line has no
per-row counterpart: the original draws it once for the selected
colony. Both marked in `colonylist.py`, in the fundament and in
smoke checks.

**What the second line owes, if it stays.** `E_Strings_(74)` takes
SEVEN values (colsum.cpp:1196-1205): planet size, climate, gravity
class, mineral class, `n_pops`, computed maximum, growth. The row
draws three — climate, `n_pops`, `max_pop` — and omits size, gravity,
mineral class and growth. That omission is **deliberate**: a row is
58 px and the second line is one short string, so seven values there
would be a table rather than a caption, and the row exists to carry
the track. They have a home already and it is the original's own —
`output_panel` is the HD equivalent of that same bottom-left box. If
the hover band from the design lands, the row keeps its three and the
panel answers for the rest, which is what the original does one
colony at a time.

**The sort bar works — 3 September 2026.** Seven keys, and the
DIRECTIONS are transcribed rather than chosen: `Switched_cmp_`
(colsum.cpp:378-401, 1.60) is a switch on `_g_sort_index` with the
sign as a literal in each `case`. Five are descending — population,
food, industry, science, BC — and Name and Producing ascending.

**There is no direction toggle, and its absence is the
transcription.** Clicking the header that is already lit re-sorts
identically; the original has no reversal anywhere. No arrow is drawn
for that reason. Every list control written since 1996 does the
opposite, so this is the kind of fidelity that reads as a missing
feature and needs the note.

Name is CASE-INSENSITIVE, because `cmp_Alpha_` calls `strcasecmp`
(colsum.cpp:1053). Star names generate capitalised, but a player
renames a home star with free text (namestar.cpp:262), and a plain
`str` sort would file that after every capital.

**Six of seven are implemented; `producing` is not, and says so.**
`cmp_Prod_` (colsum.cpp:1091) orders by `Prod_To_Sort_Type_`, which
reads `TECHDATA::_buildings[].cost`, then breaks ties on
`Selection_Name_` — a cost table and a name table both loaded at
runtime from the player's own `techname.lbx` and neither shipped.
That is the same absence that leaves the building column empty. The
button is drawn LIKE THE OTHER SIX since 12 September 2026 — it was
dimmed until then, which is the deviation Data ended — and it still
injects its click, because the original's list behind us sorts fine
and the injection keeps the two screens agreeing; what it cannot do is
reorder our rows. `colonyrows.SORT_UNAVAILABLE` still carries the key
and the reason, and `colonypick` still refuses a move made under it.

**Ties keep the input order — 3 September 2026, and the tie-break
that used to be here is gone.** Every key fell back to the planet
name on a tie, marked as an addition of ours, on the reasoning that
the original's bubble sort leaves equal elements wherever they were
and that for us this would mean a list reshuffling between redraws.
The first half is right and the second does not follow.

Four files carry the array order end to end, and only one of them is
the sort: `ext_api.cpp:94` writes the colonies in `MOX::_colony[i]`
order, so `colonies_raw` arrives in it; `colxport.cpp:91` filters the
original's own list out of the same array in the same order;
`colsum.cpp:363` swaps only when `Switched_cmp_` is STRICTLY
positive, so equal elements never move; and `colsum.cpp:1056` returns
0 on equality, so the sign that would move them cannot arise.
`build_rows` walks `colonies_raw` in order and `list.sort` is stable,
so the list was already stable across redraws — and the fallback was
ordering ties the original leaves unordered. Two colonies of equal
population sat alphabetically on our screen and in array order on
the original's, with every value on both correct. `_by()` now returns
a single negated number, because a tuple IS a tie-break and the
absence has to be visible in the key rather than asserted beside it.

The smoke check was turned around with it: it no longer demands the
name order for equal rows, it drives `build_rows` over two snapshots
packed in opposite orders and demands the output follow the input —
through the whole path, since "input order" is not a property a sort
key can express on its own.

`s_colony.production[4]` (offset 231, ECON order plus BC —
orion2_consts.h:119-123) now reaches the row dicts for the four keys
that need it. **Nothing in the ROW draws it**, and the original does
not put it in its row either — but it does draw all four per colony,
in the bottom-left box `output_panel` occupies (coldraw.cpp:60).
That is the withdrawal of decision 43, recorded above; the comment in
`colonyrows.py` still carried the old claim and has been corrected.

**The sort bar sends keys — 3 September 2026.** `_inject` has two
paths now. A button with a `hotkey` in `layout.json` sends
`INJECT_KEY` and nothing else; a button without one, or with a
malformed one, falls through to its `native_click`. The seven sort
buttons take the first path, RETURN the second — its field carries a
hotkey byte of 0x25, which is not a letter anybody presses.

**Why the key is preferred.** A click is not inert:
`INJECT_CLICK` arrives as an SDL button event, and platform.cpp:1171
feeds its coordinates to `Set_Present_Mouse_Position_` while :1172
enqueues them as a mouse input event, so every injected click leaves
the game's own pointer parked on the button we pressed. The key path
(platform.cpp:1131) touches neither.

**The click points STAY, and the smoke test refuses a sort button
that loses one.** They are the half that can be checked without a
running game — a grep against the `Add_Multi_Button_Field_` call at
colsum.cpp:265-273 — while a hotkey is a letter in a JSON file that
has to be taken on trust until somebody presses it. The two are an
order, not a replacement.

**It was verified live before it was switched on, because a silent
failure looks exactly like a success here.** The original re-sorts by
a key it already holds without moving a pixel — there is no direction
toggle — so "nothing changed" is both the working and the broken
outcome. Sorting AWAY from the active key is what separates them.
Against orion2re 1.60 on the reference save, Colonies screen up:
`p` from a name-sorted list moved 15071 of the 307200 framebuffer
bytes, `n` moved them back, `B` and `S` moved it again, and an idle
capture moved nothing at all. A frame taken after the key was
byte-identical to one taken after the equivalent `native_click`.

**Second source for the hotkeys, from the same session.** The
FIELD_LIST reports fields 16-22 at y 446-469 carrying N P F I S R B —
the same seven letters `layout.json` holds, UPPERCASE on the wire.
The game folds case: both `n` (110) and `N` (78) arrive. Worth
writing down, because the mismatch between the stored lowercase and
the reported uppercase looks like a bug and fixing it would fix
nothing.

**What was NOT observed: the pointer.** The cursor is composited onto
the ARGB present surface (platform.cpp:794-822) and the Extension API
sends the indexed `g_present_surface` (ext_api.cpp:165), so no cursor
of any kind is on the wire; the game's window is hidden while the API
is on (platform.cpp:1379), so there is nothing to photograph either.
That half of the claim rests on platform.cpp:1171-1172 against
:1131-1134 and on nothing else, and it is written down that way
rather than as "verified".

**The outpost filter is ARMED — 3 September 2026, and the gate that
blocked it is closed.** The original's list is built on two
conditions, the colony's `owner` and a zero `outpost_flag`
(`Build_Global_Colony_List_`, colxport.cpp:91-99; `N_Colonies_`
counts with the same pair at colxport.cpp:67). `build_rows` applies
both now.

**The second source is discriminating, which the earlier one was
not.** A save at stardate 3502.4 with 55 colonies: colony 54 sits on
planet 239, the game labels that planet "Yian I (Elerian Outpost)"
and shows 0/4 population, and the Colonies screen does not list it.
Twelve records carry the local player as owner; the screen lists
**eleven**, and the record they differ by is the one with the flag
set. `tools/struct_probe.py colonies --outposts` reports ANSWERABLE
and 12 against 11 — against the previous save it reported
INCONCLUSIVE, because all 21 of its colonies carried 0 and the filter
would have removed nothing either way.

**One write site, which is what makes the flag mean one thing.**
`COLONIZE::Make_New_Colony_Or_Outpost_` sets it in the branch that
runs when the new colony is not a colony — `outpost_flag = 1` with
`n_pops = 0` beside it (colonize.cpp:381-382), which is also where
the observed 0 population comes from. Nothing else assigns it; every
other mention in the tree is a read, except `savegame.cpp:309`, which
restores it from disk.

A smoke check sets the flag on one preview colony through the SPEC's
own offset and demands that exact row leave the list.

**Two states the original's row carries and ours does not.** Found
while reading `Draw_Colony_Summary_For_Colony_` for the sort work,
marked NOT DRAWN in `colonyrows.py`, and deliberately not dressed up
as a task — an omission nobody wrote down cannot be told apart from
one nobody noticed.

- **The star's BLOCKADE** (colsum.cpp:557-569). `star->blockaded` is
  a bitmask over players, shifted by the local player and masked to
  one bit at colsum.cpp:562 — the same shape as `visited`, and read
  the same way by `star.visited_by`. A blockaded system colours the
  row through an inline attribute and appends a marker (ESTR 0x46 and
  0x86); an unblockaded one substitutes the empty string twice, which
  is why the native name column is 89 px wide and not 87.
  **Reachable:** `blockaded` is offset 162 in the verified
  `core/structs/star.py` spec and the stars are in the snapshot. Not
  drawn because nothing has been built for it.
- **A COLONY EVENT** (colsum.cpp:553, `EVENTS::Colony_Has_Event_` at
  events.cpp:635). A colony with an event takes the other branch of
  that function entirely: a different paragraph type, an inline
  colour chosen by `Event_Good_` (colsum.cpp:534), and the event's own
  label appended to the name. **Not reachable:** the function reads
  `EVENTS::_event_data[]`, and the snapshot carries settings,
  players, stars, ships, colonies, planets, nebulas, leaders, antarans
  and ship icons and no events (ext_api.cpp:53-136).

The two are listed apart because they are different kinds of absence,
and collapsing them into one line is how the buildable one would stop
looking buildable. A smoke check holds both markings to their sources
and fails if `GameState` ever grows an events array — at which point
the second entry is wrong and wants revisiting rather than deleting.

**The list has a SELECTION now — 3 September 2026.** Transcribed,
and the two halves have separate sources.

**Entry lands on row 0 of the SORTED list.** `colsum.cpp:139` sets
`COLONY::_g_colony_n = COLSUM::_list_col[0]` in the screen's setup,
before the input loop runs, and `_list_col` is filled from the sorted
`_g_colony_list_ptr` by `Update_Col_List_` (colsum.cpp:348-351) — so
it is the first row as sorted and not the first colony in the array.

**After that it changes on HOVER, not on a click.**
`Evaluate_Colony_Pop_Input_` takes the clicked field and the scanned
one as two separate arguments, and it is the SCANNED one that moves
the selection: over a row's name, producing or buy field it assigns
`COLONY::_g_colony_n` (colsum.cpp:880-890). "Scanned" is this
engine's word for hovered — `fields::Scan_Input_` (fields.cpp:652)
returns the field under the pointer with no button involved, and
`Evaluate_Input_` is handed both values from colsum.cpp:159-162.
Leaving the list does not clear it: the assignment has no else
branch, so the box goes on showing the last colony the pointer
crossed.

**The selection is a COLONY, never a row index**, and that is the
part a row index would get wrong invisibly. The sort handler
(colsum.cpp:830-837) re-sorts, clears the window array and resets
`_first`, and never touches `_g_colony_n` — so the selected colony
keeps its identity and moves to wherever the new order puts it. A row
index would keep the highlight still and change the colony under it,
which is the opposite behaviour and looks identical on entry. The
row dicts therefore carry `index`, the snapshot's own colony index,
which is the same number `_list_col[]` holds. Nothing draws it.

**A click on a row is deliberately inert, and it is commented rather
than left silent.** The original does something substantial there:
clicking the name field sets `MOX::_current_screen = SCREEN_COLONY`
and hands over the star and orbit (colsum.cpp:912-920), and clicking
the producing text goes to `SCREEN_QUEUE_POPUP` instead
(colsum.cpp:922-944). Neither destination has an HD screen, so
injecting the click would move the game to a screen the HD side
cannot draw and hand the player a 640x480 fallback with no way back
that this screen knows about. The click is swallowed here rather than
allowed to fall through — an absence that is written down is a state,
one that happens to work out is a bug waiting for its second cause.
The honest risk is named in the code: the hover has already moved the
selection by the time a click arrives, so a player who clicks a row
does see the panel change, which reads as the click working.

**`output_panel` draws — 3 September 2026, and it is a
TRANSCRIPTION** (decision 43 withdrawn; the marking was the opposite
for a day and a half). `COLSUM::Draw_Colony_Scan_Info_`
(colsum.cpp:1155) fills the native box at (13, 354, 80, 88) for the
selected colony, guarded by `_g_colony_n != -1` (colsum.cpp:1165):
seven values substituted into `ESTRINGS::E_Strings_(74)`
(colsum.cpp:1196-1205) — planet size, climate, gravity class, mineral
class, `n_pops`, the computed maximum and growth — plus a column of
production rows and morale from native x 106 (colsum.cpp:1171-1176).

**Its own module, `colonyoutput.py`, not the end of `screen.py`.**
The screen was already over the guideline and a panel that draws
eleven values from a dict is not "being a screen". It is handed plain
dicts and knows nothing about structs, the same seam `colonyrows` and
`colonylist` already use, so a spec change breaks in one place —
`build_rows`, where the offsets are.

**The selection machinery followed it out, into
`colonyselect.py`** — the state and the two rules that move it, kept
together because they only make sense together. What stayed in
`screen.py` is the geometry, which belongs with whatever owns the
boxes; `_rows` and `_selected` are properties over the `Selection`
object so nothing else in the file has to know where they live.
**It bought less than it looks like it should:** 691 lines to 647,
because sixty lines of state and docstring became twenty-six lines of
delegation.

**The sidebar followed, into `colonyempire.py` — 647 to 528**, and
that was a commit of its own for one reason: two smoke checks reach
into `native_column_width` and `value_column` to hold decision 44's
clamp, and one of them greps a source file for the DEVIATION
marking. Left pointing at `screen.py` they would have gone on passing
against a file that no longer contains what they assert — a check
whose subject has moved out from under it is worse than no check,
because it still reports green. They moved with the code and were
strengthened on the way:

- the marking is now asserted on `value_column.__doc__` rather than
  anywhere in the file. The module docstring also contains the word
  DEVIATION, so a file-wide search passed even with the marking taken
  off the function it is about — verified by taking it off.
- `screen.py` is asserted NOT to mention `native_width` again, so the
  clamp cannot acquire a second home. Verified by giving it one.

`NATIVE_W`/`NATIVE_H` moved with it and `screen.py` imports them:
`_inject`'s bounds check and the sidebar's scaling are statements
about the same 640x480 slice, and two copies of a screen size is how
one of them ends up describing a window.

Behaviour-neutral, and checked by looking: the sidebar renders the
same six values in the same places before and after.

**Eleven rows in two columns, and the split follows the original's
own two halves.** LEFT is the scan paragraph: the seven values
`E_Strings_(74)` carries, in six rows, because the original prints
`n_pops` and the maximum as one pair and so does this. RIGHT is the
production column: all four ECON values with morale under them, which
is the same grouping the original draws at native x 106. Label left,
value right. Three of the seven — climate, `n_pops`,
`max_pop` — are also on every row, and that is not a duplication to
tidy: the per-row line is the HD EXTENSION and this is the original's
own box, which prints all seven for one colony.

**BC is drawn — 3 September 2026, and the deviation that left it out
is retired.** It was omitted on the reading that the panel showed
"food, industry and research". The original draws four: its loop is
`i < ECON_COUNT` and ECON_COUNT is 4 (orion2_consts.h:123), and the
GEOMETRY says so without taking the constant on trust — `y_pos`
starts at 349 and steps 18 (colsum.cpp:1170-1173), giving 349, 367,
385, 403, with morale one step further on at 421 (colsum.cpp:1176),
which leaves room for exactly four rows above it and not three. The
smoke check that asserted BC's absence is gone; what is asserted now
is that there are four production rows and that they sit in one
column, which is how the original draws them at native x 106.

**Two deviations remain, both marked in `layout.json` under
`output._deviation_note`, each one line away from being undone.**
(1) Each production row is one number where the original's is
several — `COLDRAW::Draw_Colony_Prod_Both_` (coldraw.cpp:36) draws
imports (:46), pollution for industry (:56) and a shortage computed
from maintenance minus imports minus production (:61) beside the net
value. This prints `colony->production[i]` (coldraw.cpp:60) and
nothing else, so it is a subset of that row rather than a smaller
drawing of it. (2) Morale is a number here and a row of SPRITES
there: `Draw_Info_Morale_Both_` draws `abs(morale / 2)` of them,
capped at 20, in one of two artworks by sign. The sprites are in the
player's LBX and are not shipped — the same trade the Buy button
already carries and marks. The VALUE is transcribed, including the C
truncation toward zero, and so is the Unification rule: at
`GOVERNMENT_UNIFICATION` or above the original zeroes its own count
and draws nothing, so the row keeps its label and shows no value. A
drawn 0 would claim neutral morale where the original is claiming
that morale does not apply.

**An empty selection draws NOTHING** — no dash, no zero, no label
with a blank beside it — because the original's box is simply not
drawn. A smoke check renders the panel with no selection and asserts
the surface is untouched, which is the one form of this that a table
of values cannot check.

**Growth is printed RAW.** It is the sum of `s_colony.pop_growth[10]`
that colsum.cpp:1179-1182 accumulates, and the format string that
labels it lives in the player's `estrings.lbx` and is not shipped, so
its unit is unknown here: a live colony of 8 pops decoded 73 on
3 September 2026, plainly an accumulator and not a per-turn head
count. Printing the engine's own number under our own label is the
honest form; inventing a division to make it look like people would
not be. The original also sums `pop_roundoff[10]` in the same loop
and then passes it to nothing — there is no transcription to make.

**The word lists are OURS, and the note says so.** The original fills
four tables — `_planet_size_string`, `_mineral_class_string` and
`_planet_gravity_string` at estrings.cpp:155-169,
`_planet_climate_string` at estrings.cpp:204-213 — and every entry is
an `E_Strings_(id)` call, so the strings come from the player's own
`estrings.lbx`, loaded at runtime, one file per language
(`Load_E_Strings_`). They are not in the orion2re source and are not
shipped. So `layout.json` carries English words this project chose to
match what the game prints, in a `words` block, under decision 15.
Three of them have a second source of a sort: the original's own
planet description for Ixion II read "Small Ocean, Normal Gravity,
Mineral Abundant" on 31 August 2026, which also fixes the direction
of all three enums. The rest are the enum names in title case and are
unconfirmed.

**Climate is deliberately NOT in that block.** It already had a home
at `list.climates` with its own provenance note, and a second copy
that agrees on the day it is made is the screen-ID-map failure
waiting. A smoke check asserts the climate words appear in exactly
one of the two blocks, and that none of the three new lists appears
in the other.

**What has NOT been done is the check that would settle the panel.**
Of its ten values, five — size, climate, gravity, mineral class and
`n_pops` — were read live against the original's own planet
description, and `max_pop` is computed from them. Growth and morale
rest on the header's names alone, exactly as `outpost_flag` does. The
thing that settles them is the `--native` side-by-side in
`tools/colony_list_preview.py`, which still has never been run.

**The list says what it dropped — 3 September 2026, and it was
silent until then.** `colonylist.render` stops at the first row that
would cross the bottom of `list_area`. At 1920x1080 that panel holds
NINE rows, so a twelve-colony empire lost three with nothing on
screen saying so — every drawn row correct, every check in the suite
green, and the fault found by somebody noticing a colony they owned
was missing from a screenshot. It is the exact shape of the fundament
entry about a later draw erasing an earlier one, reached from the
other side: there the data was right and invisible, here the data was
right and absent.

A line now reads `{count} more not shown`, in the strip the rows
could not use, in a colour that is not the row name's — the wording
in `layout.json` per decision 15, `{count}` substituted by replace
per decision 37. `colonylist.rows_drawn` exports the number so a
caller can ask the question at all, which is the part that was
missing: nothing could compare drawn against present.

**It was not a scrollbar and not a step towards one; the step was
taken separately on 4 September 2026** — see "The list scrolls, for
viewing only" below. The line stayed and now counts BOTH directions,
rows above the window plus rows below it, which needed no change to
the wording. A smoke check holds the three things that mattered
then and still matter: the count in the line equals present minus
drawn, nothing is drawn when nothing is dropped, and a point below
the last drawn band still hit-tests to no row.

**pop_growth FALLS — 3 September 2026.** The second `--live --native`
run put both halves on the same key and the same ten rows, and the
scan boxes could finally be read against each other for one colony.
For **Sadak I** the original's box reads `Huge Desert / Normal
Gravity / Mineral Rich / Population (4/8) / +63k`, and the HD panel
reads Size Huge, Climate Desert, Gravity Normal, Minerals Rich,
Population 4/8, **Growth +63k**. Six of the seven `E_Strings_(74)`
values agree with the original's own print of the same colony,
including the one that rested on the header's name alone. The maximum
is the seventh and is computed, not read.

**morale does NOT fall, and the reason is worth writing down: it is
blocked by an input capability, not by data.** The comparison needs
the original's box pointed at a colony whose morale is non-zero. In
this save exactly one of the local player's listed colonies has one —
Draconis I, morale -4, which the panel would show as -2 and the
original as two sprites in the negative artwork — and the original's
`_g_colony_n` moves on HOVER (colsum.cpp:880-890), which the
Extension API cannot inject. Every click that lands on that row does
something else instead: the name field leaves for SCREEN_COLONY
(colsum.cpp:912-920), the producing text opens the build popup
(:922-944), and a job column moves population (colmove). And the game
window is hidden while the API is on (platform.cpp:1379), so nobody
can hover it by hand either. A save in which the colony the original
happens to be scanning has non-zero morale would settle it without
any of that.

**Scrolling is built, for VIEWING ONLY — 4 September 2026, and the
half that is missing is written down as decision 46.** The original
windows ten rows over the sorted list — `_list_col[10]`,
`Update_Col_List_` (colsum.cpp:348) filling from
`_g_colony_list_ptr[_first + i]` — and resets `_first = 0` on every
sort click (colsum.cpp:832), which `handle_click` now mirrors.

The HD offset lives in `colonyselect.Window`, beside the selection
because a sort touches both and in opposite directions: the window
goes home, the colony keeps its identity. All three clamps are the
original's (`Decrement_First_` colsum.cpp:211-214, the refusal at
colsum.cpp:796 that keeps the last page full, and the two steppers
declining outright below `num_items` at colsum.cpp:210 and :226,
with `Update_First_` forcing 0 every draw at colsum.cpp:194-197).
The mouse wheel is an **HD EXTENSION** — MOO2 has two step buttons
and a proportional slider (`_x_fields[1]`/`[2]`, colsum.cpp:790-800;
`Draw_Bar_Indicator_`, colsum.cpp:747-753) — and that **slider is
NOT DRAWN**, recorded in `colonylist`'s docstring beside the
blockade and the colony event.

**NOTHING IS SENT TO THE GAME, and that is what makes it safe to
ship.** The original's rows are ten SLOTS, so an injected click names
a position in the game's window and `_first` decides which colony it
reaches — decision 46. A smoke check drives the list to its bottom
and back with a capturing client and asserts `inject_click`,
`activate_field` and `inject_key` were called zero times, so the
first edit that adds an injection to a scroll path fails instead of
reaching the wrong colony. Synchronising `_first` is decision 46's
other half and is not started.

**The list is no longer blocked.** `s_colony` is verified as of
31 August (`core/structs/colony.py`): `owner`, `planet`, `n_pops` and
`max_farms` each agree with the original's own colony summary, and
`MASK_PROF` with its FARMERS column. What is still missing is the
work, not the data. `output_panel` draws now; `galaxy_inset` and
`spare_panel` are still fill only, and one panel per step is
deliberate.

One number the bar design depends on is **not** a struct field:
maximum population is computed by
`COLCALC::Planet_Max_Population_For_Player_` over climate, racial
immunity and Advanced City Planning, and
`MOX::_planet_max_population[size]` is only its base — 10 where the
game shows 5 on a Small Ocean planet. A bar proportional to the
table alone is twice too long on exactly the planets a player looks
at most. See section 3 of the fundament, and the smoke rule that
refuses the base table anywhere it appears without the climate
factors.

**The list renders — first visible step, 31 August.**
`screens/colony_summary/colonyrows.py` (the numbers),
`screens/colony_summary/colonylist.py` (the drawing),
`screens/colony_summary/colonyoutput.py` (the scan box),
`screens/colony_summary/colonyselect.py` (which colony is selected)
and `screens/colony_summary/colonybuild.py` (the building column) —
counts in the over-300 list above, so there is one place to update —
their own modules because `screen.py` was at 258 against a ~300
guideline. One
row per colony of the local player, sorted by name: the planet name,
then one allocation bar, one square per colonist, three zones in ECON
order.
The list now has a SELECTION, and it is what feeds `output_panel`.
Still read-only towards the game: nothing the list does sends an
injection. No hover band is drawn and no divider is draggable; those
belong on a picture somebody already believes.

**The bar is an INVENTION** and is marked as one in `colonylist.py`,
in `layout.json` under `list._invention`, here, and in a smoke check
that fails if either marking disappears. The original draws three
columns of pop sprites per row, squished when a colony outgrows its
column (coldraw.cpp:282).

Verified against the original's own screen for the same savegame
(85 turns, stardate 3508.5): seven rows, same names in the same
order, "No Farming" on exactly Kif II, Malus I, Sol III and Sol IV,
per-row populations and job splits identical, total 39. Bar length is
`Planet_Max_Population_For_Player_` reimplemented, not the size table
— with two stated deviations that both make a bar too short rather
than too long: Advanced City Planning is not applied, because
`tech_applications` has no verified offset, and the limit is taken
for the owner's race rather than the best over races present, because
that walk needs the pop word's low nibble.

Race groups as shades and androids/natives as locked are **not
drawn** — but the mask is no longer the reason. The low nibble has a
second source for 0..7, verified live, and that source refutes the
"race" reading rather than merely agreeing with the player one. What
is still open is the meaning of 8 and 9, the android and native
sentinels, which are exactly the two cases the locking was wanted
for. The zone split is a list of runs so they can be added inside a
run later without moving anything.

One thing only the picture caught: "No Farming" was first drawn at
the bar's left edge and the worker squares painted straight over it.
Every number was right and the screen showed nothing. It now sits
after the track, in a `tail_width` column reserved for it — the
collapsed zone has zero width by construction, and the free tail is
one slot wide on Sol IV.

**The track is the engine's cap, not the empire's best colony.** The
square used to be sized from the widest `max_pop` in the list being
drawn, so the ruler moved with the empire: one new Gaia colony, or a
finished Biosphere, lengthened the longest bar and shrank every
square on screen. A square counted last turn was not the square
counted this turn, and nothing in the picture said the scale had
changed — the same class as the drift and double-scale faults, a
number that is wrong only in comparison with itself.

It now comes from `POP_LIMIT_CAP` in `colonyrows.py`, which is 42 in
one place in the tree and carries all three of its sources: `s_colony.pop[42]`
(orion2.h:497), the clamp closing
`COLCALC::Planet_Max_Population_For_Player_` (colcalc.cpp:930), and
the per-job cap in `COLMOVE::Give_Colonist_New_Job_`
(`Sum_Colonists_ >= 42`, colmove.cpp:518) — that last one is why one
zone may legitimately span the whole track, so it cannot be drawn
shorter. `max_population()` clamps with the same constant, so the two
cannot disagree about how long a full bar is.

Three regions per row, each with its own state: **filled**, one
square per assigned pop in its zone's colour; **free**, from `n_pops`
to `max_pop`, a dashed outline and no fill; **unreachable**, from
`max_pop` to the cap, no square at all and only a faint baseline.
The third is not padding — Advanced City Planning (+5), Biospheres
(+2), Subterranean and terraforming all move `max_pop` up during a
game, so it is room the colony does not have yet, and a square there
would claim it was either filled or free. Squares past `max_pop` are
now drawn rather than clipped: they land in the unreachable region,
where nothing else is, so the two stated deviations stay visible
without losing a colonist off the picture.

Two smoke checks hold it, both measured in pixels rather than by
re-deriving the arithmetic, which would only check the formula
against itself: the same row drawn alone and drawn beside a
42-population colony must come out identical pixel for pixel, and the
three regions must appear in order with the unreachable one thin and
at the foot of the track — so a dimmer square there fails instead of
passing a colour test.

### The horizontal budget of list_area — decided 1 September 2026

`list_area` is 1408 reference px and every column spends from the
same pot. Fixed costs are `pad_x` twice (44) and the 41 inter-slot
gaps (82), so

    unit = (1408 - name_width - tail_width - building - 126) // 42

| variant | no building col | +190 building |
|---|---|---|
| today: tail 150, label in tail | 19 | 14 |
| **1. label moved below the bar, tail 0** | **22** | **18** |
| 1 + name_width 230 | 25 | 20 |
| name_width 336 (the true maximum) instead | 18 | 14 |

The table lives in `layout.json` under `list._horizontal_budget`, so
the next session cannot spend the width without reading what it
costs. **Decided: candidate 1 adopted, candidate 2 rejected.**

**Candidate 1 — the label moved, and it was free.** `row_height` 62
against `bar_height` 34 leaves 28 px, split 14 above and 14 below by
centring the bar, and "No Farming" renders 88x14. So the label fits
in height the row already pays for, and `tail_width` went to 0: 150
px back into the track, unit 19 to 22. `no_farming_placement: "tail"`
restores the old position.

#### It is an identity now, and it was 38 px short — 2 September 2026

The budget was stated as a division and checked as a table, which is
not the same as being balanced. It was not:

    name 240 + tail 0 + building 206 + pad 44
         + 42*unit 798 + 41*gap 82  =  1370      against 1408

`unit` is a FLOOR division and 836/42 is 19.905, so 38 px were
dropped on the floor every frame. They were not slack and they were
not padding — nothing claimed them, so they surfaced as dead air
between the right edge of the building column (1446) and the right
edge of `list_area` (1506), a 60 px gap after the Buy buttons that
read as a misaligned panel rather than as a rounding error.

**`name_width` 240 -> 236, and the division comes out exact:**
(1408 - 236 - 0 - 206 - 44 - 82) / 42 = 840/42 = **20**, remainder 0.
The four pixels are not a measurement of anything; they are what
makes the pot divide, and they came off the name column because it
is the only one of the four with slack against its own stated range
— realistic maximum 230, room 244. `building_width` is a hard
transcription, `pad_x` and `square_gap` are the fixed costs, so
neither could give.

The square went 19 -> 20 as a side effect, which is the trade coming
out the right way round: the slack ended up in the thing the screen
exists to make countable. The row now ends flush — slot 42 at 1278,
building column 1294 to 1484, right `pad_x` to 1506.

**The smoke test asserts the relation, not the number.** It reads
`name_width`, `tail_width`, `building_width`, `building_gap`,
`pad_x`, `square_gap` and `POP_LIMIT_CAP` out of `layout.json` and
the width out of the `list_area` box, and requires the sum to equal
it. A budget checked against the constant 1408 stops being a budget
the first time `frame_holes.py` moves a cutout: the constant goes on
agreeing while the panel no longer does, and the check then reports
success about a screen that is wrong. A second assertion says the
same thing the other way — that the remainder is zero — because that
is the half a later edit to any of those keys breaks first.

#### …and it only balanced at scale 1.0 — 2 September 2026

The assertion above had `1920`, `1080` and `1.0` as literals. It was
scale-blind by construction: it covered one of the two keys in
`boxes.json` and none of the sizes reached through the fallback
chain, and the comment beside it called the truncation at other
scales "a bound and not an identity", which excused the gap instead
of measuring it.

Measured, across twelve window sizes:

| | | | |
|---|---|---|---|
| 1280x720 +30 | 1440x900 +22 | 1680x1050 +11 | 1920x1200 **0** |
| 1366x768 +29 | 1600x900 +15 | 1920x1080 **0** | 2048x1152 +21 |
| 2560x1080 **0** | 2560x1440 +15 | 3440x1440 +15 | 3840x2160 **0** |

It closes at four of twelve, and the pattern is exact: **only at
integer scale.** At 1.0 and 2.0 every term truncates cleanly and
42·unit divides; at every fractional scale the six independent
`int()` calls each drop a fraction, and 11 to 30 px land at the right
edge as the same dead air the reference-space fix had just removed.

**The name column absorbs the remainder — as DRAWN WIDTH, not as
text budget.** `track_metrics` computes `slack`, what `list_area` has
left after the building column, both `pad_x` and the whole track, and
`render` adds it to where the bar starts. Nothing is written back to
`layout.json`; it is a per-frame number. The row then ends flush at
all twelve.

The split matters, and it is the whole point of doing this in two
numbers. Adding the remainder to the column outright also closes the
right edge, and silently makes the ellipsis threshold range **244 to
288 reference px** — 288 at 1280x720 against 244 at 1080p, so the
same colony name cuts on one monitor and not on another. The name
still clips and ellipsises against `name_width * scale`, so the
threshold is 244 everywhere (241.9 to 244.0 measured, and that 2.1 px
is three terms being scaled and truncated independently, not slack).
The remainder becomes **gutter** between the name and the first slot,
which is the one thing that column can absorb without saying anything
untrue.

So `name_width` 236 changes meaning rather than value: it is the
**text budget**, and the drawn column is wider by a per-resolution
remainder. Said in `_name_width_note`.

**What is asserted now.** The column sum is gone — after the above it
balances by construction and cannot fail, and a check that cannot
fail asserts nothing. In its place, across the twelve sizes:

    slot42_right + building + pad_x == list_area.right
    the wide name is cut at EVERY size, the narrow one at none

Both are read off the **surface**. An earlier draft derived `bar_x`
and the clip from `layout.json` the same way the renderer does, which
made it agree with the renderer by construction: it passed unchanged
with the gutter moved a pixel and with the clip tied to the drawn
width — the two failures it exists for. Both breaks were then made
deliberately and both now fail, naming the resolution and the cause.

The condition it had to meet was named in advance, because this label
has failed once before — drawn at the bar's left edge, with the
worker squares painted over it, every number right and nothing on
screen. Below the bar is outside the track's band *by construction*
(squares occupy `y+1` to `y+bar_height-1`), so a full 42-slot row
cannot reach it. That is geometry rather than data, and the smoke
test asserts it against a row with all 42 slots filled — not against
a screenshot that happened to have a gap in it.

**Candidate 2 — measured, it goes the wrong way.** A planet name is a
star name plus a numeral. `s_star.name` is `str15` (star.py:35) and
the player can type all fifteen characters when renaming a home star
(`namestar.cpp:262` caps input at 15); the numeral is at most V,
since `star->planet_index` is [5]. Fifteen wide glyphs measure
**336 px through `Style.render_text`** at `name_font` 21 — six px
MORE than the 330 the column reserves. Holding the longest name the
game can produce therefore costs width instead of recovering it: unit
18 against today's 19.

Narrowing to 230 looks safe on any real galaxy — realistic 15-char
names run 190-230 px, and the widest of the 54 stars in the running
reference game is "Draconis IV" at 124 — and overruns on a name a
player can type. That is the trade being refused, and the render is
what refused it: at `name_width` 230 the name visibly prints over its
own track.

**A latent fault the measurement exposed.** `name_width` was a
reservation nothing enforced — `render_text` output was blitted
unclipped — so the 6 px overrun landed on the track's first slots.
The squares draw after the name, so the data won and the name was the
casualty: the same draw-order fault as the No Farming label, one
column to the left. The name is now clipped to its column, asserted
at the structural maximum rather than at whatever a galaxy generated.
Clipping does not make a narrow column correct; it confines the
damage to the name. Going below 336 needs a stated truncation policy,
an ellipsis being the obvious one, and that has not been built.

**The name column, once it had the width.** The render after the
budget decision showed the column three quarters empty, and two
things came out of that.

**Right-aligned to the column's right edge**, which is where the bar
starts. Left-aligned, a name too long for the column grew rightward
onto the track's first slots, and since the squares draw afterwards
the data won and the name was the casualty. Right-aligned, the same
overflow grows LEFT into `pad_x`, where nothing is drawn. The clip
becomes a fallback rather than the mechanism.

Re-run against the structural maximum: 15 W's plus " V" is 336 px.
That measurement is from the `name_width` 330 era, when it spanned
x=3 to x=335 inside `list_area` and never touched the clip. At the
shipped 236 it does not fit and is not meant to: the room before the
clip is 236 - `name_gap` 14 + `pad_x` 22 = 244 px, so this name is
ellipsised, uses the whole of the padding growing left, and still
finishes clear of the track. That is the designed degradation and it
is now a row in `tools/colony_list_preview.py` rather than a
one-off measurement, because the two things no assertion can settle
— whether the cut still reads as a name, and whether the leftward
overflow reads as overflow rather than as a second column — need a
picture. `name_gap` 14 is the gutter between the block and
the first slot, taken out of `name_width` rather than out of the
shared budget; without it the name ended on exactly the pixel the
first square began on and the two read as a collision, which is what
the first render after right-aligning showed.

**A second line under the name**, and it is an **HD EXTENSION**:
`climate` and `pops/max_pop`, e.g. "Terran 22/24", on EVERY row. The
original prints that pair for the SELECTED colony only, into the
bottom-left scan box at native (13, 354, 80, 88) —
`COLSUM::Draw_Colony_Scan_Info_` (colsum.cpp:1155) formats
`ESTRINGS::E_Strings_(74)` and squeezes it into that rect, guarded by
`_g_colony_n != -1`. The rows themselves carry a name and nothing
else. Per row it makes comparable what the original could only show
one at a time, which is the same family as the allocation bar: not
something MOO2 chose against, something its screen had no room for.
Marked in `colonylist.py`, in `layout.json` under
`list._hd_extension`, here, and in a smoke check that also refuses a
marking which does not name what the original does instead.

It is a SUBSET of that box, deliberately: the original's line carries
planet size, gravity, mineral class and growth as well. Those are not
drawn, and `output_panel` — the box they belong in — is still empty.

**`colony->climate` is what the original reads too.** That choice was
made by reasoning (the colony's field is rewritten when a shield
turns a Radiated world Barren, colcalc.cpp:682) and is now
source-backed: `Draw_Colony_Scan_Info_` takes
`climate_idx = colony->climate` at colsum.cpp:1167 and indexes the
same table. Still deliberately NOT `player_climate()`, which is an
Aquatic transform for the pop limit and would print Terran for an
Ocean world.

**The ten ESTR ids were a second copy, and they are gone.** The note
in `layout.json` listed climate → ESTR id for all ten, assembled by
reading `orion2_str.h`. The original maps climate to string in
exactly ONE place — `estrings.cpp:204-213`, which fills
`MOX::_planet_climate_string[]` from the enum — and every screen that
shows a climate indexes that table (colsum.cpp:1199, colland.cpp:40,
colsysdi.cpp:165, plntsum.cpp:151, mainpups.cpp:348). An independent
second derivation of the same table is the screen-ID-map failure in a
new costume. All ten were checked against `estrings.cpp` and agreed;
they were then removed in favour of a pointer, because a copy that
agrees today is the one that drifts later. The names themselves stay
in `layout.json` — they are not in the orion2re source at all, they
are in the player's LBX — in enum order, which is load-bearing and is
neither alphabetical nor a quality ranking.

Substitution is a `replace`, not `str.format` (decision 37), so a
stray brace in a translated string cannot raise inside the render
path — asserted, along with an out-of-range climate byte degrading to
"?" rather than raising.

### The building column — built at 190, and a correction

**The 190 was right and my measurement of it was wrong.** The number
comes from `Squeeze_Print_Formatted_Paragraph_(0x200, y, 0x55, 0x16)`
(colsum.cpp:621): x 512, width 85, max height 22, of a 640 px screen.
85/640 is 13.3 %, which is 190 of 1408.

I had rejected that as a scaled estimate and measured instead the
widest producing string, on ONE line, at FULL font — 311 px at
small_font — and concluded a column that holds its content does not
fit. `BILL::_Squeeze_Print_Paragraph_` (bill.cpp:147) says otherwise
and settles it: `width` is passed straight into
`get_height(width, text)` and the loop compares `max_height >=
height`. **The text is wrapped into the width and the HEIGHT is what
is made to fit. Width never moves, and there is no truncation branch
in the function at all.** So 85 of 640 is a width reservation, and
all three constraints in my measurement — one line, full font, whole
string unwrapped — are ones the original never imposes. A requirement
the original does not have is not a measurement of the original.

Worth keeping as the shape of the error: it was not a wrong number,
it was the right number measured against the wrong question, and it
came out nearly twice as large and looked exactly as authoritative.

**Built at 190, two lines, small font**, in
`screens/colony_summary/colonybuild.py`: the production name on the
first, `- 8t` and the Buy button on the second.

**The original budgets two lines in that same box.** colsum.cpp:621
passes max height `0x16` = 22 into a row whose pitch is 31 —
`buy_btn_y_coords` steps 35, 65, 96, 128, ... — so the box is two
thirds of its row and holds more than one line of its own font. The
two-line column is therefore the same PLACE as the original's, not
just the same technique applied somewhere else. Our vertical reserve
is the one that freed `tail_width`, `row_height` 62 against
`bar_height` 34.

**The behaviour is transcribed, not the mechanism.** The original
squeezes in three steps: narrow the space glyph
(`font_style_widths[32]--`), then the leading, then step down one
font style. The first is a bitmap-font trick with no Aldrich
equivalent and the third steps between discrete bitmap faces. What
carries over is the shape: **wrap into the width, reduce size until
it fits, never truncate.** At the floor it draws the text whole
anyway, which is what the original does once its loop runs out of
things to shrink.

One gap the render found: the fit test was height-only at first, so
a single word wider than the column — an unbreakable 15-glyph ship
design at 225 px in a 190 px column — sat there overflowing, because
it fits the height on one line and never triggered a shrink. Both
dimensions now.

**Whether that width condition is a transcription turned on one
function, and it is.** `_Squeeze_Print_Paragraph_` loops on height
alone, and `fmtpara.cpp` offers
`Get_Formatted_Paragraph_Max_Width_` right beside the height function
without ever calling it — which leaves two possibilities. Either
`_Print_Formatted_Paragraph_` breaks inside an over-wide token, in
which case height alone is sufficient and our width condition keeps
the same guarantee by other means; or it breaks only at spaces, in
which case a 15-glyph ship design overflows 85 px in the original too
and our refusal to overflow is a deviation.

It breaks inside the token. A character is placed when
`char_x_end <= right_limit_x || line_started != 0` (fmtpara.cpp:567);
`line_started` is 1 at the start of a line and 0 after the first
character (:540, :572), so the first character goes down
unconditionally and every later one must fit. When one does not and
it is not a space, `Return_To_Last_Break_()` is tried — and breaks
are recorded only at spaces, tabs and soft hyphens (:723, :731) — but
`_para_p->str--` runs whether that succeeded or not and the line ends
(:583-587). A token with no break inside it is broken mid-token, and
the paragraph never exceeds the width. **Height alone is sufficient
BECAUSE the width can never be exceeded.**

So the guarantee — no ink past the reserved width, nothing truncated
— is a **transcription**, and our width condition delivers it. The
**means is a marked deviation**: the original character-wraps the
token, we reduce the size and keep it whole. The reason is that the
over-wide token here is a ship design name, user-typed data whose
exact form is the point; a hyphen-less mid-word break that reads as
wrapping in a five-pixel face at 640x480 reads as corruption at HD.
Marked in `colonybuild.py`, in `layout.json` under
`list._width_condition_note`, here, and in a smoke check that refuses
a marking which drops either half or the line that settles it.

**The Buy control is transcribed in position and deviates twice in
form.** The original adds one per row at native x=599
(colsum.cpp:302, `_list_buy_fields[10]`, `buy_btn_y_coords`), right
of the producing text, gated on `Colony_Can_Buy_Product_0_`. That
much is transcribed. Two things are not, and naming only the first
would leave the larger one unmarked:

1. **The label.** `E_Strings_(12)` is empty, so "Buy" is a word this
   project chose. It lives in `layout.json`, decision 15.
2. **Drawing text at all.** The original's control is a **sprite** —
   `_anims[i + 11]` supplies the artwork, which is precisely why its
   label string can be empty. A text button is a different object,
   not a translation of that one; it is drawn this way because the
   sprite is in the player's LBX and is not shipped.

Nothing sends a click yet.

**Still missing: the production names.** `build_rows` leaves
`producing` empty. The id at offset 277 indexes
`TECHDATA::_buildings[]`, whose names load from the player's
`techname.lbx` at runtime (techinit.cpp:43-73) and are `kEmptyName`
in the orion2re source. There is no extractor for that table, so the
column renders empty on the real screen rather than inventing a name
— the rule the help texts and the nebulae already follow. The walk is
proven (it was used to measure the 49 names) and the extractor is a
sibling of `help_extract.py` when somebody wants it. Turn counts need
a cost calculation that is not built either.

### `name_width` re-opened, and lowered to 240

It was rejected at 230 because the render showed the name
overprinting the track — **under left alignment**. Right alignment
sends overflow left into `pad_x`, where nothing is drawn, so that
render no longer applies and the trade re-opened.

Reserved for the REALISTIC range now, with the structural maximum as
the **ellipsis case rather than the reservation**. The widest of the
54 stars in the running reference galaxy is "Draconis IV" at 124 px;
a realistic 15-character name is 190 to 230 ("New Constantine V" is
208). 336 px — fifteen wide glyphs, which a player can type
(namestar.cpp:262) — is cut with an ellipsis instead of being
reserved for. That spends nothing in every case it can hold and
degrades visibly in the one it cannot.

| name_width | no building col | + building 190 |
|---|---|---|
| 330 | 22 | 17 |
| 240 | 24 | 19 |
| **236** | 24 | **20** |

Shipped: `name_width` 236 with the 190 column, **unit 20**. 240 was
shipped for a day and left the budget 38 px short of balancing — see
"It is an identity now" above. The table is in `layout.json` under
`list._horizontal_budget`.

**Figure mode: built, compared, deleted.** For one session the
filled region could draw a sprite per colonist instead of a square,
with the zone colour as a 3 px rule beneath the figures instead of a
background fill, selected by a `list.figures.enabled` key and fed
from a `--pop-dir` outside the repository. It was built to be
compared against the squares and it lost.

What decided it was the preview's 50 % copies. Square mode survives
the reduction — the runs stay clean colour blocks and the zone
boundaries stay readable. The figures collapse into an
undifferentiated stipple, and the only thing still carrying the
profession is the 3 px rule, which is itself close to disappearing.
At a 22 px slot the rule was doing the work the silhouette was
supposed to do, which makes the sprites decoration over a bar that
already said the same thing.

Deleted rather than left switched off: **a dead branch is a file
nobody checks.** `colonyfigures.py`, the layout key, the `--pop-dir`
argument, the crop-baseline guard and the smoke check all went with
it. The smoke check was replaced rather than removed, per the rule
that the count must not go down — the replacement covers the name
block, which is what the freed width went into.

Two things are worth keeping from it. The **height-normalisation
rule** — `common_height = min over the set of (max_width * h/w)`, so
the widest sprite sets the height and every other follows from its
own aspect ratio — was correct and measured, and would be the rule
again for any future sprite set; normalising on width inverts it, the
narrowest figure becoming the tallest. And the **crop-baseline
guard**: a set whose source crops differ in height by more than 2 px
is not a set, because the sizing normalises the whole group onto one
height, so one crop taken two pixels low silently rescales every
figure beside it — and the symptom reads as an art problem when the
fault is a measurement. Both are recorded here rather than in code,
because there is no code left to carry them.

### Looking at it — `tools/colony_list_preview.py`

```bash
python tools/colony_list_preview.py
python tools/colony_list_preview.py --size 2560x1440
```

Headless, no game, no savegame: the real `frame.png` over the real
`boxes.json` geometry around fake rows defined in the script. Writes
to `/tmp/colony_list_preview/`, never into the tree, with absolute
paths in every line it prints. Modelled on `starfield_preview.py`,
for the same reason — judging a track has to cost one second, not one
game start plus 85 turns.

This rendered the comparison that deleted figure mode.

**Every image is written twice, and the 50 % copy is the point.** A
track is forty-two repeating slots with a dashed region and a
hairline in it, which is the kind of picture that looks detailed at
1:1 and turns to grain one step away. No pixel check can see that: it
measures whether ink landed, not whether it settles.

Four rows, each there to settle something: 22 pops (where the
original squishes hardest and the fixed-unit track diverges most),
`max_farms == 0`, a `max_pop` 9 colony whose 33 unreachable slots ask
whether the faint baseline reads as *expandable* or as *cut off*, and
a row meant to show three race groups. Plus the invariant pair — the
same row alone and beside a larger colony — which the tool also
*states*, comparing the two first-row bands and printing whether they
agree, because a picture of two tracks is only evidence if somebody
compares them.

**The race-group row cannot be drawn as one, and the tool says so.**
The note used to give the wrong reason and was corrected on
2 September 2026: the nibble's mask IS confirmed live for 0..7, and
what is still open is only the meaning of 8 and 9 — the android and
native sentinels, which are the cases the shading was wanted for.
`colonyrows` reads no nibble, so every row reaching the renderer is
race-blind. That row is identical to any single-race row with the
same job split. It is kept, with a line in the output, because a
preview that quietly substituted professions for races would answer a
question nobody asked — and would be believed, because it looks like
the screen.

Exit codes carry the findings, so do not chain it behind `&&`: 1 if
the shared row was not identical in both renderings.

Two decisions came out of its renders rather than out of argument:
figure mode was deleted, and the name column was right-aligned and
given a second line. Both are above.

The smoke test asserts the fake rows carry exactly the keys
`build_rows` produces. Nothing else would notice a drift: a stale row
dict still renders, so the preview would go on looking right while
showing a row the game cannot produce.

**Rest of the design, agreed 31 August, not built.** Instead of the
original's three icon columns per colony, one allocation bar per row:
one small square per population unit, three colour zones (farm,
industry, research), two draggable dividers between them, race groups
as shades, androids and natives outlined as locked, `max_farms` as a
tick, "No Farming" as a collapsed zone. Bar length is proportional to
the colony's maximum population, so the squares are the same size in
every row and counting squares means counting pops. Hovering a row
opens a band directly below it with the original sprites, unsquished,
plus the hovered pop's race/job/state — the band pushes the rows
below it down rather than covering them, because the row underneath
is where the next drag goes.

Why this can drive the original: the pop move is click-click, not
drag (`colsum.cpp:851`), the pickup takes a whole identical group
from the clicked icon onward, and the five drop rules are all
checkable from the snapshot before a click is sent. Icon positions
are deterministic from the colony data, so every HD drag becomes
pairs of injected native clicks — two per race group touched. The
mechanics are recorded in the fundament's orion2re facts. The native
list window (`_first`) and sort order have to be tracked locally,
because the snapshot carries neither.

### Galaxy Map
Arranged like the original: bottom bar COLONIES · PLANETS · FLEETS ·
LEADERS · RACES · INFO, TURN bottom right, stardate as the sidebar's
top row, the frame title cutout clickable as the GAME menu.

**Decoupled HD viewport** (`viewctl.py`) — new this session. The
snapshot carries every star's galaxy coordinate, so the wheel zooms
the HD view **at the pointer** and the right button drags the map,
and the game is never told. The first wheel tick decouples from the
game's slice; `0` hands the view back; `+`/`-` zoom on the map centre.

- The float `SmoothMapView` renders. The transcribed integer
  transform would snap stars to whole native pixels at in-between
  scales and make them wobble against each other while panning; it
  stays in use for everything the game sees.
- Sprite steps come from `zoomtables.hd_zoom_level`, a **marked HD
  extension**: it quantizes the continuous scale to the nearest rung
  of the original ladder, and is identical to the transcription on
  every rung the game itself can report.
- Zoom range: scale 5 (twice the original's closest view) up to the
  fit view, which is `max_map_scale` — the same picture the game
  shows fully zoomed out.
- Panning clamps to the galaxy; an axis that overshoots is centred
  rather than pinned to a corner.

What stays coupled, and how:

- **Clicks** land in the game's 640x480 slice, so while decoupled the
  game is parked at maximum zoom-out — throttled activations of the
  zoom-OUT field only. Field 8 (zoom in) is never used by anything;
  it leaves the game in an inescapable rubber-band state. At
  `max_map_scale` the game's slice covers the galaxy to within 1–3
  units on the far edge, checked for all four sizes. HD pixel →
  galaxy goes through whatever view is on screen; galaxy → native
  **always** through the game's own state.
- **Ship icons** are baked in the game's screen space. They are
  re-anchored, not re-derived: in-transit ships draw at the ship's
  own galaxy x/y (exact), orbiting ships at their star's HD position
  plus the game-computed slot offset, scaled to the star sprite
  actually drawn. Which ship sits in which slot still comes from
  `Build_Ship_Icons_`, so decision 24 keeps standing.

Everything else on the map:

- **Stars** — 36 sprites, six per spectral class, selected with
  `clamp(zoom + star.size, 0, 5)`. Missing steps fall back to the
  legacy large/medium/small artwork.
- **Star names** — colour by owner, and a Galactic Lore name on an
  unvisited foreign system renders as `(Name)`.
- **Wormhole links** — 1 px, antialiased, RGBA `[128, 150, 190, 90]`
  from `colors.json`, drawn through `renderer.WormholeLayer` and
  cached on a key.
- **Ship and monster icons** — four size steps per kind under
  `assets/ships/<kind>/0..3.png`, indexed by zoom level. The player
  sprite is one greyscale drawing tinted to the eight MOO2 colours at
  runtime; monsters carry their own artwork and footprint. Owner is
  resolved without a C++ patch by rebuilding `_ship_node` from
  `_ship[]` and validating it against `star_idx`.
- **Sidebar** — five painted readout icons, every readout owning its
  own `sb_<row>_text` and `sb_<row>_icon` box so both are editable in
  F5. Dividers derive from the row boxes.
- **Black holes** — one drawing, rotated at runtime, **90 s per
  revolution in 720 half-degree steps**, stopping when
  `Advance_Black_Hole_Animation_` says the original stops. Frames are
  rotated **on demand and one at a time**, not pre-rendered: at half a
  degree the outer edge of a 195 px icon moves 0.85 px per step, and
  720 surfaces at that size would be 55 MB per icon size and about a
  second of freeze the first time a black hole appeared. The single
  slot costs 2.3–2.8 ms whenever the clock reaches a new step, 8 times
  a second, shared by every black hole on the map because they all
  turn off one clock; a cache hit is 4.5 µs. Roughly 2 % of one core
  while a black hole is on screen.
  Speed and smoothness are now **separate constants**
  (`BH_ROTATE_PERIOD_S`, `BH_ROTATE_STEPS`). They were one decision
  while the frames were pre-rendered, which is why the old 72-frame
  version could not be slowed down: stretching 40 s to 90 s with the
  same 72 frames spaces the same 5° jumps further apart and reads
  *more* stepped, not less.
  Residual drift of the event horizon across the revolution is
  unchanged at 0.37 px at 117 and 0.70 px at 195, against a
  measurement floor of 0.26 and 0.63 — the smoke test asserts under
  0.5 px at 117. The supersample is load-bearing: rotating at icon
  size instead is 13x cheaper (0.19 ms) and drifts 1.4 px, because
  the half-pixel centring rounding then lands at final scale with
  nothing to divide it. **No brightness pulse**: an
  earlier version faded between alpha 165 and 255 every 4.8 s, which
  read as breathing and buried the rotation. It was invented, not
  transcribed — MOO2 is palette-indexed and cannot alpha-blend a
  sprite at all. The smoke test now asserts that frame brightness
  varies by under 12 %. The master is built by
  `tools/make_black_hole_master.py` from a single still: point stars
  removed, alpha from luma, event horizon forced opaque, cut to a
  circle so rotation cannot clip a corner. The tool refuses to write
  a master whose horizon sits more than 2 px off the rotation axis —
  an off-axis horizon orbits the centre instead of turning, which no
  screenshot reveals and only motion does.
- **Nebulas** — twelve masters under `assets/nebula/type_NN.png`,
  one per `s_nebula.type`, sized from `zoomtables.NEBULA_DIM` and
  never from the artwork. Blitted additively, so a master's mean
  premultiplied luma *is* its weight on screen; the smoke test
  measures shape and weight against `assets/nebula_ref`, the same
  extraction that produced the table.
- Decorative star field, hover ring, hovered system name.
- **Home-system ping (HOME)** — three expanding rings over the local
  player's home star, ~3.7 s, then gone. An **invention**, labelled as
  such in `ping.py`, in `layout.json` and in the smoke test, which
  fails if the marker disappears: MOO2 has no ping and cannot
  alpha-blend at all. Kept cosmetic — the key is consumed by
  OrionLayer and never reaches orion2re, the effect expires on its own
  and hands its ring cache back, and radii are in native pixels times
  `ctx.px` so it scales with the zoom like every transcribed layer.
  The home star comes from `s_player.home_planet_id` →
  `s_planet_data.star_index`, both verified specs, with a fallback to
  the first owned star when the index is out of range. 0.22 ms per
  frame while running.
- A star click sends `INJECT_CLICK` at the star's exact 640x480
  point, computed with the game's view state in both modes.

---

### Planets — brief 101, 13 September 2026

**SCREEN_PLANET_SUMMARY (32) has an HD screen**, built from Data's
`frame3.png` and `mockup3.png` (`doc/briefs/101-*`) on Data's Stop 1
decisions (`doc/briefs/102-*`). Reached from the galaxy map's Planets
button (field 11) by the dispatcher's own routing; RETURN activates the
esc button by the field id the live field list carries for hotkey 0x1B.
No framebuffer fallback on the round trip.

- **Rows** — `screens/planets/planetrows.py` transcribes
  `Filter_Explored_Planets_` in the source's order (type, own colony,
  outpost, visited or omniscient, then the toggles), `max_pop` from
  `Planet_Max_Population_For_Player_`, and the rebuild rule that re-sorts
  only when the count changes. Sorting is descending and **stable**; the
  original's `qsort` is not, so planets with equal keys may stand in a
  different order than the game's (Data's acceptance: same set, same
  order between distinct keys).
- **Words** — `planetwords.py`: climate, gravity, minerals, size,
  specials and monster races from ESTRINGS, `-%d%% prod`, `%d
  prod/worker`, `%d max pop` and the status line from **HESTRNGS.LBX**,
  extracted from the player's install by `tools/hestrings_extract.py`
  (decision 38: byte for byte, decoded at load, format-versioned, never
  committed; absent it the lower lines show their bare number).
- **Colours** — the owner's player colour (`galaxy_map.owner_N`) or the
  neutral ramp, brighter for the hovered row (`colors.json` `planets`),
  as `Colony_Owner_Colors_` does. The mockup's per-column scheme is
  dropped.
- **Side column** — the original's inset through the colony summary's
  renderer with a box-size parameter (`colonyinset.render(native=,
  marker=)`, `colonyrows.galaxy_inset_stars(box=)`), the status line
  (star name, `unexplored`, `Black Hole`), three sort keys (injected
  clicks, type 3), five restrictions (hotkeys 1-5), the two send buttons
  drawn available exactly when the game added their fields, RETURN.
- **The list code is shared** — `core/listgrid.py` holds the bands,
  columns, heading plates, row fills and cell outlines; the colony
  modules delegate to it under their own names.
- **Bottom windows** — HD EXTENSION: panel (disc, name, special line,
  larger; nothing computed). The picture window became the monster
  values panel in brief 107 (see "Monster values in the Planets panel").
- **Checked** — seven smoke checks (frame cutouts, row set, order, words,
  wire, help table from `evanhelp.cpp:118`, markings). Rendered once from
  a read-only snapshot of the running game (current_screen 32, 495
  planets, 140 rows; Rex I / Natives / (Hydra) / Gaia 1.5 Food / Normal
  G / Rich 5 prod/worker / Large 20 max pop — the mockup's first row).
- **Stop 3, live — 13 September 2026.** Slot 8,
  `fixture_reference_3502.4.GAM` (loaded through the game's own Load
  dialog: fields G, L, then the slot's hidden field; `verify_colonies`
  all 55 records byte for byte before and after). `SAVE10.GAM`
  `9f9f35e4…` before and after — Data's own autosave from that morning,
  not the secured copy, which was not touched. Every input went through
  the HD screen's own handlers with the live client attached:
  - main → Planets by the galaxy map's field 11; the dispatcher routed
    32 to `planets` with no framebuffer fallback; RETURN by the esc
    field id back to screen 0 (twice).
  - The three sort keys have **no hotkey** in the source and re-sorted
    the native list by injected click at the game's window size
    (decision 20's coordinate fix, `ext_api.cpp:373`).
  - **Hotkeys 1–5 work at HD window size** for all five restrictions,
    on and off; the click fallback was never used.
  - **Row counts agree for every restriction and the combination**
    gravity + hostile + minerals (34), read off the native scroll thumb
    through `Get_Vertical_Scroll_Bar_Height_`: 140, 51, 98, 56, 83, 34.
    The eight visible native rows are all in the HD set with the same
    key values; order differs only inside ties (the stable sort).
    Range: native 41, HD 140 — the marked gap, as designed.
  - **The toggle-state gap showed up for real**: the game's range
    toggle was ON before the screen opened, so the first run compared a
    filtered native list with an unfiltered HD one. The second run
    flipped it once from outside the screen first.
  - All 15 help regions opened their entry; **the first open popup
    crashed** — `help_popup` had no rect. Fixed, and the help check now
    renders an open popup at four sizes.
- **Brief 101 closed.** Deferred, and listed under What is missing:
  the range filter (its own brief), sending ships with ETA markers and
  send cancel (the event-driven send brief), the toggle state on the
  wire, the monster-system ship name, the monster pictures.

### GAME menu — work order Stop 2, 14 September 2026

**SCREEN_GAME (8) has an HD overlay**, `screens/game_menu/`: the whole
tree behind the galaxy map's GAME button that Stop 1 read
(`doc/game_menu_reading.md`) — the menu, Settings, Load, Save, the
NEW/QUIT confirmation and the slot warning. Fundament 59-62 are this
work's decisions.

- **One overlay claims screen 8** (decision 59). The dispatcher is
  unchanged: `update_from_game` already opens an overlay bound to an id
  over the active screen and closes it when the game leaves. Not
  covered, and NOT changed: an HD app that starts while the game is
  already in the popup has no galaxy map underneath and draws the
  overlay over the empty background.
- **Which dialog is up** is `nodes.classify` over the field list —
  type, hotkey, size, never index, never field 0. The measured lists
  are `tools/game_menu_fields.json`, geometry only.
- **Input** is ACTIVATE_FIELD on the field carrying the builder's
  hotkey, looked up at the moment of the click, through a gate that
  sends once per list change (a double click on SETTINGS would
  otherwise toggle a checkbox in the next dialog).
- **Settings checkboxes** are held locally from `core/structs/settings.py`,
  VERIFIED on two sources: the header compiled with static_asserts (one
  deliberately wrong offset fails), and the live bytes against the
  native dialog, 13 of 13, `random_events` skipped as
  `Set_Current_Game_Option_Flags_` skips it. The checkboxes are type 7,
  so decision 20 allows ACTIVATE_FIELD and nothing needed reporting.
- **Name input** is a `TextInput`, committed through `core/injection.py`
  as one PACED step — the strip activation, one backspace, the name,
  Enter, one send per `EFFECT_PAIRS` snapshots. Paced because the
  game's key ring holds TEN (`key.cpp:5`, `:67-72`): a burst of 15 keys
  into a name kept 9 (`probe` below). `type_name` still bursts, and
  Empire Identity's 24 backspaces plus a name overflow that ring for
  names longer than a few characters — **a latent fault in a shipped
  screen, not fixed here**, written down in `type_name`.
- **The galaxy map no longer parks under the overlay.** It sent field 9
  by number from `update()`, and field 9 of the Load dialog is slot 9,
  which loads at once.
- **QUIT -> YES** calls `GameClient.expect_shutdown()` before YES; the
  app ends with the game (decision 62).

**Marked, each in the module, `layout.json` and the smoke test:**

- ~~**OMISSION — the Music and Sound Fx sliders.**~~ Built by work order
  124 C (`gmsliders.py`), help regions 420/421 with them; the omission is
  gone from the module and `layout.json`.
- **OMISSION — the slot game-type icon** (GAME.LBX 16-18, not extracted).
- ~~**HD STATE — slot names.**~~ Gone since open fix 14 was applied
  (16 September 2026): the rows show the engine's names, the warning says
  H 178-180, and a name edit starts from the slot's name.
- **DEVIATION — the empty save slot's name edit starts empty** (marked
  17 September 2026, work order 126 D; kept since 16 September): the
  original pre-fills "... empty slot ..." (loadsave.cpp:517), clears it on
  the first backspace (fields.cpp:1191-1193) and APPENDS a typed character to
  it where the field width allows (fields.cpp:1196-1216 — source reading, not measured). HD's send starts
  with a backspace, so the game gets the typed name or its default name.
  `gmsave.SaveEditor.start`, `layout.json` `save_empty_slot_deviation`, and
  the GAME menu markings check.
- **UNVERIFIED — the Save dialog's right click** outside every help
  region, which the source sends back to the menu. It could not be run:
  the game is a native Wayland client xdotool cannot reach, and every
  field centre in that dialog lies inside a help rectangle, so
  MSG_CANCEL_FIELD cannot produce the case. HD does nothing there until
  a human right-clicks it once on the native window.

**Live acceptance, 14 September 2026** — `tools/game_menu_hd.py`, the
real `App` headless, real pygame events. The game every step ran on was
**not a known fixture** (stardate 3500.0, 99 stars, 50 colony records)
until the save step, and slot 10 after it. Every step hashed
SAVE1-SAVE9 before and after — **identical on all eight steps** — and
logged SAVE10's hash and mtime without comparing it.

| step | result |
|---|---|
| `walk` | PASS. HD GAME click -> field list **equal** to the native GAME click's (11 fields); every node opened and pictured beside the native frame (`orionlayer-fixtures/evidence/game_menu/hd_live/`); starting a name edit sent nothing; ESC while editing -> menu; NO -> menu twice; RETURN -> the galaxy list exactly as before GAME |
| `esc` | PASS. ESC from menu, Settings, Load and Save -> galaxy map; ESC in the confirmation ignored, nothing sent |
| `help` | PASS. 42 of 42 regions over four dialogs open their own entry |
| `toggle` | PASS. Expanding Help on, ESC -> `s_settings` byte 4 is 1; off, ESC -> 0. ESC COMMITS, which Stop 1 had only from the source |
| `probe` | PASS. Native: 15 keys in one burst into slot 10's name kept 9 ("(Auto Save)ABCDEFGHI"); native ESC while editing -> menu (confirms the `-field` path) |
| `save` | PASS on the second reading. Slot 10, "HD Save Test Slot Ten" typed through HD: all 21 characters arrived; SAVE10.GAM was written (`05446424…`) with the description **"HD Save Test Slot Ten_"** — the engine keeps its edit cursor on an Enter save, as the native list's hand-saved "ddddd_" already showed (open fix 19). Reproduced, not repaired |
| `load` | PASS. Slot 10 loaded through HD: the game left the popup to REPORTS (39), overlay closed, stardate 3500.0 as saved |
| `quit` | PASS. QUIT -> YES: SAVE10.GAM rewritten (mtime 19:19:27, same content), the client set `game_ended`, the app left its loop, **no reconnect line** in the run's log, the orion2re process exited. Restarted afterwards |

**Deviations from the native pictures, listed, not explained away:** the
button words are text, not GAME.LBX artwork; the popup frame is the
thin_border skin on the cockpit texture, not the riveted metal; no
slider box in the menu; no hover or pressed state; rows plated by
`draw_plate` instead of recessed bars; checkboxes are filled squares,
not the blue lamp; the confirmation and warning frames are plain
panels (no CONFIRM.LBX / WARNING.LBX art, no animated warning lights);
without the patch every row difference above; the Settings title and
rows set in Aldrich with the game's colours only approximated
(`colors.json` `game_menu`, a palette choice).

**Found on the way, not this work's to fix:** `tools/colony_move_hd.py`
cannot be imported (`palette.require` for `plate_outline` runs before
the palette exists); `tools/game_menu_hd.py` initialises the palette
first and reuses its helpers. **FIXED by work order 126 D (17 September 2026)**, with the four
siblings that had the same fault (`colony_drop_sweep`, `colony_drop_timing`,
`colony_move_probe`, `ship_icon_check` — the last on `ship_0`):
`tools/toolenv.py` initialises the skin palette and every one of them calls
it before its first screen import; `game_menu_hd.py`'s own copy now calls it
too. One new check imports every tool that has a `__main__` (40) in a fresh
interpreter from outside the tree; it fails with the call removed from
`ship_icon_check.py` (`evidence/work_order_126/D2_check_fails_without_fix.txt`).
196 -> **197**. The OrionLayer instance Data had running
(`main.py`, old code) stayed connected throughout, fell back to the
framebuffer at screen 8 as before, and will have reconnected when the
game quit.

**Next screen:** SCREEN_REPORTS (39). After a load the decision-22
fallback shows the native framebuffer.

### OLED floor lift and player-colour presets — two HD EXTENSIONS, 14 September 2026

Brief "OLED floor lift and colour-blind palettes", Data's decisions of
the same day; fundament 63. Both are **HD EXTENSIONS** — MOO2 has no
adjustable floor and assigns its eight player colours fixed — and each
is marked in its module, here and in a smoke check.

- **`core/usersettings.py` / `user_settings.json`** — the player's own
  values, ignored by git, never shipped. Absent: defaults, silent.
  Unreadable: one error line, defaults, the file moved to `.corrupt` on
  the next save. Unknown keys written back. Not `settings.json` (the
  app's committed configuration), not `core/structs/settings.py` (the
  engine's `s_settings`).
- **Game Settings dialog, four row heights below the thirteen** (1080p
  box `orionlayer_rows` [622, 641, 513, 153], ending at 794 against
  ACCEPT at 817): a divider, the "OrionLayer" heading, **Map floor**
  (Off / Light / Haze) and **Player colours** (Original / Okabe-Ito)
  with eight swatches from the SELECTED preset. `screens/game_menu/gmorion.py`.
  No field, no hotkey, and a click on any of the four bands sends
  nothing; the thirteen engine rows keep their state from `s_settings`.
  Values apply in memory at once; the file is written on ACCEPT and on
  the overlay's exit, idempotently. **The restart note sits
  right-aligned in the HEADING band, above the swatches** — four row
  heights leave no fifth; shown only while saved != active preset.
- **Floor lift** — `screens/galaxy_map/floorlift.py`, one additive fill
  after both floor paths in `_render_map`, read at draw time (live).
  Off = no call, byte-identical map. Light (1, 2, 5) and Haze
  (4, 10, 20) are the floor graphic's median and 90th percentile.
- **Presets** — `core/playercolors.py`, applied once by
  `palette.init(preset=)`, which only `main.App` passes (after the user
  file); every other caller gets the original. All four tables swap:
  `owner_*`, `ship_*`, `owner_hover_*`, banner/banner_hd. `ship_*` and
  the banner tables were moved out of code into colors.json first, each
  checked byte for byte (32 ship tints, 24 banners).
- **The rule is a marked DEVIATION** in colors.json [player_presets]:
  owner = base, ship = base lifted by k_ship 0.07, hover = base lifted
  by k_hover 0.45, banner multiply = base with no add. Both k measured,
  with protocol: k_ship is the smallest lift that keeps every preset
  ship at least as bright as the darkest original ship (red, 0.108) at
  all four zoom steps — measured 0.0674, stored up; k_hover matches the
  original's mean hover/owner luminance ratio 1.700 (1.699 at 0.45).
- **Okabe-Ito** with black replaced by white; red -> vermilion, yellow
  -> yellow, green -> bluish green, silver -> white, blue -> blue,
  orange -> orange, brown -> reddish purple, purple -> sky blue (by
  distance, and the nearer relative for a deuteranope). Smallest
  deuteranopia distance dE 17.2 against a threshold of 10; **the
  original's is 3.8 and it is reported, not held to the threshold** —
  a deviation from the brief's "every shipped preset", because the
  original cannot meet any useful one.

### Monster values in the Planets panel — fundament 64, 14 September 2026

**Brief 107** (`doc/briefs/107-*`, decisions `108-*`, release `109-*`).
When the scanned row's star is guarded by a space monster (owners 9..14,
`planetrows.monster_ship`, the transcription of
`HAROLD::Star_Guarded_By_Monster_`), the picture window shows the
creature and its values. **HD EXTENSION, all of it except the type** —
the original shows "(Amoeba)" under the planet and nothing else outside
combat; that line is unchanged.

- **Panel** — `screens/planets/monsterpanel.py`: sprite box left, text
  boxes right, all in boxes.json at both resolutions (`monster_sprite`,
  `monster_type`, `_stage`, `_size`, `_structure`, `_armour`, `_shield`,
  `monster_weapons` with `monster_weapon_counts` beside it,
  `monster_specials`); wording as templates in layout.json
  `monster_values`, the list headings HESTRNGS 0x9D-0x9F. Numbers, no
  judgements. Nothing is sent. The old `monster_picture`/`monster_race`
  pair is gone.
- **Switch** — a fifth OrionLayer row in Game Settings, "Monster values",
  default ON (`user_settings.json` `monster_values`). The rows box grew
  one band and ACCEPT moved down by the same 38 px.
- **Values** — the design block of `s_ship_data` and the weapon records
  are VERIFIED (`core/structs/ship.py`: 48 header asserts and a live
  probe of five monsters against their templates). The damage fields are
  not declared and not read. Stage from the drive. Structure and armour
  as two lines, tactical, from `core/monsterhull.py`;
  `tools/monster_hull_check.py` holds that table to initship.cpp,
  techdata.cpp and orion2_consts.h and the smoke test runs it.
- **Names** — `tools/techname_extract.py` writes a second file,
  `shipparts_<lang>.json` (specials, armour, shields, weapons, hull
  classes; `core/shipparts.py`); without it the panel shows numbers.
- **Sprite** — the galaxy map's own master, exported once more at 314 px
  on the long edge (`zoomtables.MONSTER_PANEL_SPRITE_PX`, DERIVED for the
  4K box; `panel.png` beside the four steps). **DEVIATION**: chosen by
  type, where the original's unreachable popup picks by star index % 5.
  The Amoeba has no master and its box stays empty.
- **Reference save** — `tools/fixtures.py` now also slices the ship
  array (`fixture_ships`, reference 109 records at 82939, natives 71 at
  68828, each found live on a fresh load). Every monster of the
  reference save gives exactly its template and table values in the
  smoke test.

### Galaxy map: the right click is the game's cancel — brief 107, 14 September 2026

A right click on the map (not over a help region) sends CANCEL_FIELD on
the map's grid field, found in the live list by type 12 and rect
22,22-527,421, before the pan drag starts. TRANSCRIBED: with the mouse
cancel disabled the right button returns the grid field negative and
`Main_Screen_` ends the relocation-merge mode and leaves zoom mode —
over a star, a black hole or empty space alike, and nothing else
(layout.json `map_cancel`). Checked live on the reference save: screen
stays 0, field list unchanged.

**Also from brief 107:** `tools/maintext_extract.py` extracts the
system-special descriptions from MAINTEXT.LBX (the file per language
from estrings.cpp) into `maintext_<lang>.json`, read by
`core/maintext.py` (decision 38's pattern). Nothing draws them yet —
they belong to the galaxy map's popups, which are their own brief. The
Amoeba's map footprint is measured off BUFFER0.LBX (13 x 13), and the
same measurement disagrees with the five screenshot values
(`doc/ship_icon_measurement.md`).

### Galaxy map: fleet icons are clickable, and the boxes are read off the field list — brief 110 Part A, step 1, 15 September 2026

**Brief 110** (`doc/briefs/110-*`, decisions `111-*`, release `112-*`).
The first package of Part A, the one everything else in A depends on.

- **Icon hit test** — `screens/galaxy_map/mapclick.py`. TRANSCRIBED
  order: icon before star, star before icon while the fleet box is open
  (mainscr_main.cpp:425-438); the first icon in ARRAY order whose
  rectangle holds the pointer (`Check_Ships_XY_`, mainscr.cpp:1750). The
  rectangle is `ships.icon_box`, the one `render` draws in (decision 5).
  The click goes out at a native point inside the icon and clear of
  every earlier icon, so the game opens that stack and not the star it
  orbits. `_click_star` is gone: one click path for icon, star and empty
  space.
- **Box state** — `screens/galaxy_map/mapboxes.py`: the fleet box, the
  system window and a modal text box, read from the live FIELD_LIST (the
  box fields sit between the last sidebar window and the Q/V/grid tail,
  mainscr.cpp:1405-1427). A list it cannot read is `known = False`. Test
  data: `tools/galaxy_box_fields.json`, recorded live on the reference
  save in brief 110 Stop 1.
- **Decision 65, DEVIATION** — while the fleet box is open, no map click
  the game would resolve to a star (its own radius, `Check_Stars_XY_`) is
  sent; a black hole is exempt. **Consequence, plainly: a fleet cannot be
  moved from the HD map yet.** A click on a fleet or monster opens its
  box in the game (still invisible in HD), a click on another icon
  switches it, and the destination click is refused until HD draws the
  box and the target is chosen there — the next step of Part A.
- **Decision 66** — no CANCEL_FIELD while a box is open: it would land at
  the grid's centre, inside the box.
- **Not built yet:** HD drawing of the system window and the fleet box
  (design (a), decision A1), star identity from the last HD click (A2),
  closing through the CLOSE field.
- **Smoke:** two checks — the box state against the five recorded lists
  (and a moved box followed), and the hit test with the guard; the check
  count is 179.

### Galaxy map: HD draws the system window and the fleet box — brief 110 Part A, step 2, 15 September 2026

**Brief 115** (`doc/briefs/115-*`). Design (a), Data's decision A1.

- **Identity** — `screens/galaxy_map/boxmodel.py` (no pygame). The star or
  stack is HD's own last map click that went out (A2), and a box is drawn
  only when the live list agrees: the window stands where
  `MAINSCR::Popup_XY_` puts it for that star or icon (mainscr.cpp:1060,
  fleet box clamped by fleetpop.cpp:1441), and — system window — every
  planet field lies on the orbit ellipse of one of that star's planets
  (`GEO::_orbit_consts`, geo.cpp:5; sys.cpp:1829). The engine sorts the
  display slots by y (sys.cpp:172, :316), so a field's ORDER says nothing
  about its planet; the ellipse does, and the live Yian lists fit it
  (1.015 and 0.989, the orbit-3 field being the outpost the engine opened).
  Fleet box: one icon field per ship, at most nine. A mismatch draws
  nothing and logs why.
- **Texts** are HESTRNGS': "Star System %s" / "Star System Unexplored",
  the star-class description for an unviewable system, "Wormhole links %s"
  / "Stable Wormhole", "%s Fleet" or the monster's name, and the status
  line "Orbiting %s" / "%d turn(s) to %s" / "ETA %d turn(s)" / Antares.
  **DEVIATION:** the original prints the status line only with nothing
  selected or hovered; HD cannot know the selection and prints it always.
  The box's "N turns to" carries no 20000 condition in the source, so it
  shows on the turn of the order; the map's "eta N" waits a turn (Part B).
- **Drawing and input** — `screens/galaxy_map/boxdraw.py`. Boxes
  `system_*` and `fleet_*` in boxes.json, the CLOSE label in layout.json
  `movable_boxes`. A box sits on the side of the map the game's own
  window is on. CLOSE and ESC send the box's close field (decision 66); a
  planet disc sends its planet field; anything else inside is swallowed.
  **DEVIATION:** planets in a row by orbit, ships as their map icons.
  **OMISSION:** the system window's ship buttons, gate icons and hover
  line; the fleet box's ALL, scroll and five order buttons; the
  space-monster branch; and, drawn without a field, the orbit rings, the
  asteroid belts and the colony markers.
- **Live, SAVE5 (scratch), one connection:** HD drew "Star System Kif"
  with its three planets matched by orbit, CLOSE restored the list
  exactly; the scout's box read "CyberToller Fleet" / "2 turns to Dhira"
  and ESC closed it; a planet disc opened the colony screen, and the
  window the game reopened afterwards was drawn again through the kept
  identity. SAVE1-9 identical, SAVE10 unchanged, no fleet order.
- **`turns_left` (s_ship_data +109) joins the verified spec** in this
  commit, the first that reads it (runs 113/114). `travelling_speed` (+108)
  waits for Part B.
- **Not built:** moving a fleet from the HD box. Decision 65 still refuses
  the destination click; lifting it needs Data's decision on how a target
  is chosen in the HD box (the selection is neither on the wire nor
  settable by field id).
- **Smoke:** two checks (identity rules against the live windows and
  Yian's planets; drawing and the three sends); the count is 181.

### Galaxy map: full fleet control, phase 1 — two patches reported, HD side built — brief 117, 15 September 2026

**Briefs 116 and 117** (`doc/briefs/116-*`, `117-*`). Data's path 1.
Nothing applied, nothing built live; phase 2 is Data applying the patches,
rebuilding orion2re and a live test on scratch saves.

- **Open fix 20 (read), `doc/ext_fleet_selection.patch`** — unchanged: the
  icon owners, then "FSEL", the fleet box stack, one byte per ship node.
- **Open fix 21 (write), `doc/ext_fleet_select_ship.patch`** —
  `MSG_SELECT_SHIP` 0x85: one ship selected or not, every precondition
  checked before a write (box open, stack, own ship,
  `Ship_Can_Be_Selected_`, the ship in the stack's chain). Both patches
  dry-run in both orders on a copy of the tree and compile -fsyntax-only
  with the build's flags, alone and together. `tools/version_check.py`
  reports both markers without failing.
- **HD, against built data** — `core/game_state.py` reads the FSEL block
  (`fleet_selection`, None without the patch); `boxmodel.selection_of`
  maps it to the shown ships by node; `boxdraw` draws one box per ship,
  blue selected, black not, and a click sends `MSG_SELECT_SHIP`
  (`core/game_client.select_ship`). **HD STATE:** without the block the
  cells are outlines and not clickable; past nine ships a scroll bar is
  drawn with its thumb at the top, because the box's scroll position is
  not on the wire — to be measured in phase 2.
- **Fundament 65 amended:** with the selection known a star click moves
  the ships shown blue — variant (a); (b) is still Data's to choose.
- **Smoke:** two checks (the block and the model; the HD box, the send,
  the guard, the scroll display, the checker); the count is 183.

### Galaxy map: full fleet control, phase 2 — both patches applied, confirmed live — briefs 118-120, 15 September 2026

**Briefs 118, 119, 120** (`doc/briefs/118-*`, `119-*`, `120-*`). The
orion2re tree at `~/orion2re` is patched: a permanent change.

- **Applied and built** (`-DORION2RE_EXT=ON`): open fix 21 unchanged, open
  fix 20 as **revision 2**. Revision 1 was applied first (brief 118) and
  taken back out: live, HD's click on ship 13 flipped node 11, because
  `Sort_Ships_In_Stack_` rewrites `ship_idx` inside each chain (fundament
  67). Revision 2 sends `ship_idx` and `selected` per node and the fleet
  box's chain in cell order. `tools/version_check.py` now REQUIRES both
  (markers `fsel_chain_len`, `Select_Ship_`).
- **HD reads the node table off the wire** — `ships.wire_nodes`; owners,
  icon anchors, the icon-click identity and the fleet box use it.
  `build_node_map`, `stack_of` and `selection_of` are gone. A fleet box is
  drawn only from the FSEL block (cells in chain order, colour per node
  byte); without it no fleet box and the guard stands. A star click sent
  as an order keeps the box's identity.
- **Live, SAVE5 (scratch), one connection each run; SAVE1-9 identical,
  SAVE10 unchanged:**
  - check 2: the Yoth chain 9 -> 10 -> 11 carries ships 14, 15, 13; HD's
    first cell (ship 14, node 9) sent one `MSG_SELECT_SHIP`, the engine
    flipped exactly node 9, the original's first cell went black;
  - check 1: on the mixed selection HD's cells, the node bytes and the
    framebuffer's blue share agreed per cell;
  - target click (a): confirmed by Data's hand test (brief 119) — ships
    fly on a star click with the fleet box open; fundament 65's premise is
    measured;
  - check 5 (brief 120, no order sent): a box HD opened and draws gives
    `orders_ok` and the star click plans as an order (not sent); a box
    opened by a direct click on another stack is not drawn, and HD's star
    click on Sol was refused — no click sent, fields and ships unchanged.
- **Gaps, stated:**
  - ~~**the probe's star clicks did not move ships** (run 119): Zibbat was
    out of range (no message, by the source); Sol was in range and the
    original showed "4 turns to Sol", yet nothing moved. Not separated
    from the injection path; Data's hand test is the confirmation of (a);~~
    **RESOLVED (brief 121, Data's hand test in the HD window only, F5
    loaded):** HD's target click flies — the ships leave their orbit slot
    right to left as in the original, so the injected HD click with the box
    open arrives. The failure in run 119 lay in the probe, not in the HD
    path: the Zibbat run's target was out of range (proven by the source);
    for the Sol run the probe-side cause was not isolated further. The
    probe's success test itself was right — an order sets `location` and
    `status` at once (`Make_Ships_Move_To_`, shipmove.cpp:593-600);
  - **check 4, the scroll bar, deferred:** SAVE5's largest stack is seven.
    The box's first visible row is not on the wire; HD shows the chain's
    first nine and draws the bar as HD STATE;
- **Smoke:** the count stays 183; the node-table, block, model, HD-box and
  checker checks were rewritten to the wire data, and they fail if a
  rebuilt table returns.

### Galaxy map: ship destination lines — brief 110 Part B, brief 121, 15 September 2026

**Brief 121** (`doc/briefs/121-*`), with decisions B1-B3 of briefs 111/112.

- **Precondition, measured at the sprite:** the game positions with the
  HEADER size of BUFFER0.LBX entries 205..208 (colour 0), not the ink and
  not `SHIP_ICON_DIM` — `zoomtables.SHIP_ICON_HEADER_DIM`, two sources (LBX
  headers; live framebuffer at zoom 2 and zoom 0), recorded in
  `doc/ship_icon_measurement.md`.
- **`screens/galaxy_map/maplines.py`** — the destination lines, transcribed
  from `Do_Ship_Destination_Lines_`: own ships moving, foreign ships bound
  for a star with our colony or any outpost, the open fleet box's head;
  encoded locations only (from the turn of the order); green/red tables
  (mainscr.cpp:105-106, RGB from two sources, skin keys
  `travel_line_green/red`); from the icon corner plus half the header of
  entry 205 + (3 - zoom) to the star centre; the colour wave with
  `Draw_Directional_Multi_Colored_Line_`'s table and offset. The start
  point is re-anchored like the icon (`ships.anchored_point`).
- **HD EXTENSION B1:** every map line antialiased through ONE routine,
  `maplines.stroke`; the wormhole link goes through it.
- **HD EXTENSION B2:** one wave step is `ctx.px` HD pixels, at least one;
  the phase on a fixed 55 ms clock (the original's minimum pass,
  `Release_Time_(1)`).
- **OMISSION:** the "eta N" label, the order preview line (its colour is
  not on the wire), relocation lines (unverified offset).
- **Live, SAVE5 (scratch), one connection, no order; SAVE1-9 identical,
  SAVE10 unchanged** (evidence b0/b1 pictures, `b121_lines_record.json`):
  the scout bound for Dhira gets its green line; at zoom 2 HD's native
  start is (432, 216), the point the original's line was measured to start
  from, and 75 of 80 steps along the HD segment are green; at zoom 0, 93 of
  105.
- **`travelling_speed` (s_ship_data +108) joins the verified spec** (run
  114), next to `turns_left` (+109).
- **Findings, not acted on:** `SHIP_ICON_DIM` (the HD icon size) is 9 x 8
  at zoom 2 against a 12 x 11 header and 6 x 5 of ink — which one an HD
  icon should match is Data's question. *(Answered 15 September: neither
  moves, it is a DELIBERATE DEVIATION — work order 122 item 2.2, below.)* `tools/make_nebula_icons.py` reads
  FONTS.LBX entry 1 at offset 0; the entries are (flag, r, g, b), measured. *(Fixed 16 September: work order 122 item 2.3, below.)*
- **Smoke:** three checks (who gets a line and where it starts; the wave;
  one routine and the markings); the count is 186.

### Galaxy map: frame v2 installed, the boxes inside its cutouts re-derived — work order 122 Run 1a, 16 September 2026

**Brief 122** (`doc/briefs/122-*`). `screens/galaxy_map/assets/frame.png`
is Data's `galaxy_map_frame_v2.png`, byte for byte (sha256 `4e2aca76…`);
the old 2322x1256 master is gone from the tree and stays in git.

- **The real tool, before `--write`:** `tools/frame_holes.py` finds **10
  holes** in the 1706x922 image (alpha < 16, MIN_AREA 2000) — Chat's count
  holds. The galaxy rule names them without ambiguity: the largest is the
  map, the topmost of the rest the title, two right of the map (sidebar
  above TURN), six in the bottom row by x.

  | box | old image px (2322x1256) | old ref | new image px (1706x922) | new ref |
  |---|---|---|---|---|
  | map_area | 129, 105, 1691, 988 | 105, 88, 1402, 854 | 82, 58, 1260, 752 | 90, 66, 1422, 885 |
  | title (GAME) | 882, 21, 548, 53 | 727, 16, 457, 50 | 548, 2, 337, 51 | 615, 0, 383, 64 |
  | sidebar | 1872, 131, 303, 758 | 1546, 111, 255, 656 | 1394, 77, 213, 723 | 1567, 88, 244, 851 |
  | nav_turn | 1870, 921, 307, 171 | 1544, 790, 258, 151 | 1419, 840, 176, 42 | 1595, 982, 202, 53 |
  | nav_colonies | 143, 1126, 253, 44 | 116, 966, 213, 42 | 94, 830, 186, 39 | 104, 970, 213, 50 |
  | nav_planets | 444, 1126, 258, 44 | 365, 966, 217, 42 | 308, 830, 187, 39 | 345, 970, 214, 50 |
  | nav_fleets | 752, 1126, 252, 43 | 620, 966, 212, 41 | 522, 830, 187, 39 | 585, 970, 214, 50 |
  | nav_leaders | 1051, 1126, 263, 43 | 867, 966, 221, 41 | 737, 830, 188, 39 | 827, 970, 216, 50 |
  | nav_races | 1365, 1126, 253, 44 | 1127, 966, 213, 42 | 954, 830, 190, 39 | 1072, 970, 218, 50 |
  | nav_info | 1666, 1126, 229, 44 | 1376, 966, 193, 42 | 1180, 830, 186, 39 | 1326, 970, 213, 50 |

  `layout.json` `frame.image_size` and `frame.title_rect` follow (the
  smoke check compares both against the tool).
- **Boxes inside cutouts, in BOTH lists (1920x1080, 2560x1440; there is
  no empty list):**
  - `sb_*` — re-derived from the new height, not shifted: inset 10 left
    and right, the old gap-to-height ratio 16.4:93, and top and bottom
    inset `pad_y + 1`. Six rows of 121 at a pitch of 142.05 from y 98;
    text 132 wide, gap 6, icon 86 (the old 138/6/91 scaled by 224/235).
  - `help.json` `pad_y` 7 → **9**: at 7 the right-click regions covered
    95.6 % of the column against the original's 97.0 % and the smoke check
    failed; 9 is again the largest pad that stays inside the cutout
    (89..938 in 88..939), gaps 2-3 as before. The note and the stardate
    region's numbers are rewritten.
  - the system window and fleet box groups sat 12 ref px inside the OLD
    map's right and bottom edges (1495 / 930 against 1507 / 942), which is
    the gap `boxdraw._placed` mirrors on the other sides: both groups move
    by (+5, +9). `help_popup` is centred on the new map, (261, 108).
- **GAME centred by ink.** The label was centred by the font's line box
  and sat 3 / 5 / 5.5 px above the hexagon's centre at 1080p / 1440p /
  2160p; `_render_title` now centres the ink bounding rect in
  `title_rect`, 1 px or less at all three. The hexagon is ~4.5 ref px
  right of the map's centre in the artwork (hole centre x 716 image px
  against the map's 712), and the word follows the hole.
- **Nothing else derives from the old frame:** grep for 2322 / 1256 and
  for the old sidebar and map literals — only the two `layout.json` keys
  above and the boxes. `boxmodel.py` and `mapboxes.py` work in native
  640x480 coordinates.
- **Fit, measured against the frame's alpha** (ink of every string, all
  three resolutions; 2160p uses the 2560x1440 list): no glyph under alpha
  ≥ 16. Nav labels 13 / 17 / 25 px of ink in holes 45 / 60 / 90 px tall,
  clearance top/bottom 13-18 / 18-25 / 29-36; TURN 18 / 24 / 36 px ink,
  13-18 / 16-24 / 25-35. The nav and TURN labels are still centred by line
  box and sit 2.5-5 px high — they fit, and were not changed.
- **Live** (one client, Data's closed; the game as it stood, stardate
  3509.2, 54 stars, not a fixture; no send; SAVE1-9 identical, SAVE10
  unchanged): `~/orionlayer-fixtures/evidence/work_order_16sep/1a_galaxy_*`
  at 1920x1080, 2560x1440 and 3840x2160 beside the native frame. The
  sidebar readouts agree with the original's (157 BC +14, -3 (6), +2,
  +12 (15)). **One difference seen and not touched:** research reads
  "500 RP / +44 RP" in HD where the original prints "~16 turns / 44 RP".
- **The frame blob is 2.1 MB** against the old 0.7 MB.
- **Smoke:** the count stays 186; the frame-cutout check, the class A
  check and the sidebar help coverage check all ran against the new
  artwork.

### GAME menu: a fixed frame image around the popup — work order 122 Run 1b, decision 69, 16 September 2026

**Brief 122** (`doc/briefs/122-*`). Data's `game_menu_frame.png` is
`screens/game_menu/assets/frame.png`, byte for byte (sha256 `cb4d5ad3…`),
and a required input in `tools/setup.py`.

- **The real tool:** one hole, (115, 108, 879, 1193) in the 1108x1419
  image — Chat's claim holds. `layout.json` `frame.opening` carries it and
  the smoke check holds the two equal. Aspect 0.737 against the body box's
  0.739.
- **What changed on screen:** only the popup body. Its `thin_border`
  outline is gone; `gmframe` scales the image with one factor so the
  opening covers the body plus 2 ref px, centred on it, fills the opening
  from the cockpit texture (opaque, undimmed) and draws the frame over it.
  The buttons, slot list, settings rows and the confirmation and warning
  panels keep `thin_border`.
- **The anchor, from the source:** `LOADSAVE::Add_Game_Popup_Fields_`
  (loadsave.cpp:176-293) sets `_popup_base_x/_y = 0x90, 0x19` for all
  four in-game dialogs; `_Draw_Main_Game_Popup_` draws GAME.LBX picture 0
  there (:1356), 279x378. Centre native (283.5, 214), which is **51.68 %
  across and 48.0 % down the map window**, not its centre (the brief's
  expectation) and not the window's. That proportion is applied to the
  galaxy map's `map_area`: every overlay box moved by (-53, +10); the body
  is (511, 66, 628, 850). `help_popup` is centred on the new map like the
  galaxy map's own. Checked to 1 ref px by the suite.
- **Fit, measured on drawn pixels against the scaled alpha, 1080p / 1440p
  / 2160p:** menu, settings, load and save — 0 px outside the octagon.
  **Confirmation and warning do NOT fit**, and nothing was shrunk:
  CONFIRM.LBX (313 px) and WARNING.LBX (331 px) are wider than the popup
  (279) in the original too. At 1920x1080 the confirm panel reaches x 1246
  and the warning panel x 1277 against the opening's right edge 1141 (106
  and 137 ref px over the metal); at 2560x1440 1661 / 1702 against 1520;
  at 3840x2160 2493 / 2555 against 2282. The suite reports these numbers
  every run. They are drawn over the frame with their own opaque fill, so
  nothing is clipped, but the panel visibly lies across the right-hand
  metal: **a clash, reported, not restyled** — Data's decision.
- **The top rim:** at 1920x1080 the frame starts at y -16 and its metal
  about 1-2 px above the window, because the transcribed centre is 17 px
  above the map's. *(Fixed by work order 123 item 2, below.)*
- **Help and hit-tests:** unchanged in code; the boxes moved as one group
  and the GAME menu checks (help regions, the send gate, every node
  rendering) are green against the moved boxes.
- **Live** (one client; the game as it stood, stardate 3509.2, not a
  fixture; SAVE7 absent, so its Load row gives the warning without
  loading; settings left with ESC, not ACCEPT; SAVE1-9 identical, SAVE10
  unchanged): menu, settings, load, the slot-7 warning, save and the NEW
  confirmation at 1920x1080, 2560x1440 and 3840x2160, each beside the
  native frame, `~/orionlayer-fixtures/evidence/work_order_16sep/1b_*`.
  39 activations of the menu's own fields, no click or key injected.
- **Smoke:** the body-skin check rewritten to the new rule (the body
  wears the frame, every other panel `thin_border`), one new check (the
  opening against the tool, loading through the resource roots, the
  anchor, the octagon fit and the fill at three resolutions); a mutation
  of the body by 5 px fails it. The count is 187.

### Galaxy map: the icon size marked as a deliberate deviation — work order 122 item 2.2, 16 September 2026

**DELIBERATE DEVIATION — SHIP_ICON_DIM stays 9 x 8 at zoom 2 against the
12 x 11 sprite header.** Data's decision of 15 September 2026.
`zoomtables.SHIP_ICON_DIM` ((11, 10), (10, 9), (9, 8), (8, 7), by zoom)
sizes and hit-tests the HD icon, and its click area is live-confirmed;
`zoomtables.SHIP_ICON_HEADER_DIM` ((11, 11), (12, 11), (12, 10), (16, 12),
by 3 - zoom) is what the game positions its sprite and its lines with, and
what `maplines` uses. No code changed.

- **Marked** in the `maplines.py` docstring (DELIBERATE DEVIATION, quoting
  both tables), in the comment on each table in `core/zoomtables.py`
  (quoting the other table's values), in `doc/ship_icon_measurement.md`
  and here.
- **Smoke:** one check — the tables may not become equal (whole, or at any
  zoom as they are used against each other), the maplines note must quote
  both current tables, and each zoomtables comment must quote the other's
  current values, so changing one without touching the other's note fails.
  The count is 188.

### Tools: the nebula tool's FONTS.LBX palette read one byte to the left — work order 122 item 2.3, 16 September 2026

`tools/make_nebula_icons.py` `load_game_palette` took bytes 0..2 of each
4-byte `s_palette_entry`; the entry is `{changed, r, g, b}`
(orion2.h:2131-2136), the fault `core/lbx.read_palette` was corrected for
on 6 September, in a second reader. It now takes bytes 1..3.

- **Verifiable without the game:** FONTS.LBX entry 1 begins
  `01 00 00 00  01 00 03 00  01 04 04 06`. Before, the first three entries
  came out (4, 0, 0), (4, 0, 12), (4, 16, 16); after, (0, 0, 0),
  (0, 12, 0), (16, 16, 24). Every flag byte in the entry is 1.
- **Second source, live** (one client; the game as it stood, stardate
  3509.2; no send): the palette the game sends with its galaxy-map frame
  agrees with the fixed reading at 256 of 256 indices and with the old one
  at 0.
- **Visual test:** this galaxy holds ONE nebula, type 1 (zoom 2, native
  top-left (208, 106), 86 x 88). Of its 3973 sprite pixels on screen, 3655
  carry the sprite's own index in the framebuffer (the rest are stars, a
  name and a line drawn over it), and all 3655 equal the fixed palette's
  RGB, none the old one's. Picture: native crop, old palette, new palette
  and the tool's HD output, `~/orionlayer-fixtures/evidence/work_order_16sep/2_3_nebula_0_type01_zoom2.png`.
  **The other eleven types have no native counterpart here**: SAVE4 and
  SAVE5, the scratch saves the protocol allows, hold this same galaxy; a
  before/after sheet of all twelve at zoom 0 without a native half is
  `2_3_all_types_before_after_zoom0.png`.
- **"Regenerate the icons" changed no file in the tree.** The tool ran
  (48 of 48, to a scratch folder), but its output layout,
  `type_NN/zoom_N.png` at 3x, is not what the screen loads (listed under
  "What is missing"), and the committed `assets/nebula/type_NN.png` are
  authored masters of 1952-2208 px, not this tool's output. Overwriting
  them with it would have replaced artwork, so nothing was copied in.
- **Smoke:** one check — the reader against a probe FONTS.LBX whose every
  flag byte is non-zero; with the old byte order it fails. The count is
  189.

### Galaxy map: the "eta N" label — work order 122 item 2.1, 16 September 2026

**The source first, because it decides the label:** the original DRAWS this
label — `SHIPS::Print_Eta_On_Ship_Icon_` (ships.cpp:482-506), called from
`Do_Ship_Destination_Lines_` right after the line, only for 10000 <=
location < 20000 (:471). So it is a TRANSCRIPTION, not an HD extension:
HESTRNGS 307 "eta %d", the owner's font colours, style 1 at zoom 0/1 and 0
beyond, `Print_Right_` with the right edge at the icon's left plus, and the
top at the icon's top plus, the header of the OWNER's own sprite (entry
205 + colour * 4 + (3 - zoom)). `screens/galaxy_map/mapeta.py`; the OMISSION
in `maplines` is gone.

- **The table the brief pointed at is colour 0's only.** The headers differ
  by colour (colour 2 at index 1 is 11 x 11, colours 2-7 reach 17 x 14 at
  index 3), so `zoomtables.SHIP_ICON_HEADER_DIM_BY_COLOUR` (8 x 4, read from
  BUFFER0.LBX, row 0 held equal to `SHIP_ICON_HEADER_DIM`) is what the label
  uses. The digit ink height per style, 5 and 7 native rows, is decoded from
  FONTS.LBX entry 0 (`ETA_DIGIT_INK_ROWS`, MEASURED) — no source holds it.
- **HD geometry from the HD viewport** (Data, decision 35): header index
  3 - `ctx.zoom`, offsets times `ctx.px`; the icon corner is the mapped
  native corner coupled, the ship's galaxy position less half of colour 0's
  header decoupled. Text through `Style.render_text`, digits sized to
  rows x px, ink right-aligned to the anchor.
- **DEVIATION — two locks (Data, 16 September 2026, "Befehlszug"):** a label
  only while the game is on screen 0 in the map's OWN input loop (the map's
  field list, no modal — the fleet box and system window are part of that
  loop); and none between an HD star-click order and its effect (a ship of
  the ordered stack changed location or status), released without an effect
  after more than `EFFECT_PAIRS` newer snapshots (a refused order). Parking
  the game's zoom is NOT a lock.
- **Live, scratch saves SAVE4/SAVE5 only, one client** (Data's OrionLayer
  closed first). The number the original prints is read by machine: the
  FONTS.LBX glyphs rendered at the predicted native position, scored against
  the framebuffer's pixels (hits - false - missing); record and scripts in
  `~/orionlayer-fixtures/evidence/work_order_16sep/2_1_eta_record.json` and
  `scripts/`:

  | case | ship | turns_left (wire) | read from the framebuffer | HD drew |
  |---|---|---|---|---|
  | SAVE4, order turn, location 20025 | scout 10 | 3 | no label (none expected) | nothing |
  | SAVE5, location 10025 (to Dhira) | scout 10 | 2 | **2** — 39 of 39 ink px, 0 false | **eta 2** |
  | SAVE5 + TURN, still 10025 | scout 10 | 1 | **not readable**: Dhira's star sprite is drawn after the label and covers it; "1" is the only digit whose every ink pixel shows (5 of 5), 3, 4 and 9 are not excluded | `labels()` gives eta 1; the drawing was not captured |
  | SAVE4, HD order Zin -> Sol, next turn, 10014 | scout 10 | 4 | **4** — 36 of 36, 0 false (runner-up 9, one pixel short) | **eta 4** |
  | the same + TURN | — | — | stopped: the GNN news screen took no injected click or key | nothing (not the map's loop) |

  Two turns carry a clean read, and both are digit-exact; they are not two
  consecutive turns of one flight. The consecutive pair failed once on
  occlusion and once on the news screen.
- **The locks, live:** under the open GAME menu HD drew 0 labels; on the
  combat select (screen 12), the colony-base dialog and the GNN screen
  (screen 0 with a modal list) none. Two HD orders: the lock set at the
  click, 3 and 2 frames drawn without a label, released on the effect.
- **Found on the way:** the scout in SAVE4/SAVE5 sits at ZIN (star 6), bound
  for Dhira — the brief's "Sol->Dhira" is Zin->Dhira. An HD star click on
  the star the stack stands at is an order with `turns_left` 0: location 6,
  status 0, the Dhira order cancelled (`Make_Ships_Move_To_`, shipmove.cpp).
- **Not clean, and said so:** clearing turn dialogs by clicking CLOSE at a
  fixed native point repeatedly answered the colony-base selection with
  CLOSE and its "Really trash your colony base for 100BC?" — the scratch
  game's treasury went 143 -> 243 BC. In the game's memory only: SAVE1-9
  identical to the session start, SAVE10 rewritten by the turn ends (logged).
  The game was left on the GNN screen.
- **Smoke:** one check — who gets a label (not the order-turn ship), the text
  through `Style.render_text`, the anchor in HD pixels, no label under the
  GAME menu, with a foreign list on screen 0 or a modal, the order lock held
  and released on effect and after the floor, and a blocked 4 substituting
  (a stub font); a mutation without the loop gate fails it. Found by it: the
  lock compared snapshot `id()`s, which a freed snapshot's address reuses —
  it holds the snapshot now. The count is 190.

### GAME menu: confirmation and warning scaled into the frame — work order 123 item 1, 16 September 2026

**Brief 123** (`doc/briefs/123-*`). Data's decision on 122's reported
overhang. **HD DEVIATION:** the confirmation (native 310 px wide, at
161, 117) and the slot warning (331 px, at 154, 144) are wider than the
popup (279 px) and overhang it in the original; HD scales each group by one
factor, body width over panel width — 0.8997 and 0.8430 — rects and font
sizes alike (`boxes.json`, `layout.json` `_dialog_fit_note`), centred on the
body horizontally, vertical centre kept. Marked in `gmframe.py`,
`gmdraw.py`, decision 69 (amended) and the inventory.

- **No extra line:** HESTRNGS 186 and 187 (the NEW and QUIT questions) stay
  two lines, 178-180 (the slot warnings) one, one and four, at 1080p, 1440p
  and 2160p; checked before the change.
- **After NO:** the original stays in `Do_Main_Game_Popup_` with
  `_screen_data` 0 and redraws the main screen under the popup
  (loadsave.cpp:1240-1283), i.e. back to the game menu, which HD already
  does (`confirm_no` -> MENU); the warning returns to the Load dialog.
- **Smoke:** the frame check now holds ALL six dialogs to 0 px outside the
  opening at three resolutions (122's report of the overhang is gone) and
  the fit rule — panel width = body width, centred, text box in its native
  proportion to the panel. The count stays 190.
- **Live** (Data's OrionLayer closed first; the game as it stood, stardate
  3509.2; no slot loaded — SAVE7 is absent; picture after every click;
  SAVE1-9 identical, SAVE10 unchanged): menu, NEW confirmation, after NO,
  Load, slot-7 warning, after it, after CANCEL at 1920x1080, 2560x1440 and
  3840x2160 beside the native frame,
  `~/orionlayer-fixtures/evidence/work_order_123/`.
- **Seen, not part of this item** *(the first fixed by work order 124 D)*:
  under the confirmation HD draws the popup body without the menu's buttons (`present` asks the confirmation's
  own field list, which does not carry them), where the original shows the
  menu underneath; and the warning's text is the HD STATE line until the
  slot patch is in.

### GAME menu: the frame's top edge inside the window — work order 123 item 2, 16 September 2026

**The expression was the scale factor's slack, not a rounding.**
`gmframe.rects` scales with `s = max(want_w / ow, want_h / oh)`; the
opening (879:1193) is a hair narrower than body + bleed, so the WIDTH term
wins and the opening is 3.8 / 5.0 / 7.5 px taller than the body needs at
1080p / 1440p / 2160p. `open_y = body.centery - open_h / 2` split that
slack, half above the body, and the 88 image px of metal over the opening
then started at window y -1.6 / -1.8 / -2.2. The anchor arithmetic was
exact.

- **Fix:** `open_y = body.y - bleed`. The width term stays (the scaled
  dialogs span the body's width and need the side bleed: with the height
  term instead, the confirmation and warning had 284-649 px on the rim);
  the slack goes below the body. The body — the transcribed anchor — does
  not move.
- **Measured:** first frame row with alpha >= 16 at window y 0 / 1 / 1;
  all six dialogs still 0 px outside the opening.
- **Smoke:** the frame check asserts both (metal row >= 0, opening top =
  body top - bleed) at three resolutions. The count stays 190.

### Live protocol: one picture per click; the scratch saves' scout — work order 123 item 3, 16 September 2026

- **Fundament, Diagnosis:** "An injected click on a live game is followed by
  a picture before the next one", beside "A wait needs its traffic", with
  122's scrapped colony base as its source.
- **Scratch-save fact, SAVE4 / SAVE5:** the Scout (ship 10) stands at
  **Zin** (star 6), not at Sol, bound for Dhira. A star click on the star
  the stack stands at is an order with `turns_left` 0 — location 6, status
  0 — and cancels the Dhira order (`Make_Ships_Move_To_`,
  shipmove.cpp). Measured live in work order 122.

### Galaxy map: the eta label on two consecutive turns of one flight — work order 123 item 4, 16 September 2026

**Route:** the Scout (ship 10) in SAVE4, standing at Zin, ordered through
the HD fleet box to **Sol**; the original's box reads **"5 turns to Sol"**
(location 20014, turns_left 5). Turns 1 and 2 end in open space between Vox
and Sol.

| turn (stardate) | turns_left, read from the framebuffer | HD drew | match |
|---|---|---|---|
| 1 (3509.1), location 10014 | 4 — 36 of 36 ink px, 0 false (runner-up 9) | eta 4 | yes |
| 2 (3509.2), location 10014 | 3 — 37 of 37, 0 false (runner-up 2) | eta 3 | yes |

- **Protocol:** Data's OrionLayer closed first; one client; SAVE4 only;
  a picture after every click or activation (fundament, Diagnosis); SAVE1-9
  identical before and after, SAVE10 rewritten by the two turn ends
  (logged). Evidence and scripts:
  `~/orionlayer-fixtures/evidence/work_order_123/eta/` (`eta_record.json`,
  one picture per step, `../scripts/`).
- **Turn dialogs on the way, each answered on its own picture:** the
  colony-base choice for Malus (Malus I and the next planet refused with
  "You cannot build there", Malus II accepted — a colony in the scratch
  game's memory only), the colony landing screen, "just colonized", the
  colony screen's RETURN, the turn summary, the combat selection at Peren,
  a Darlok spy message.
- **Found:** screens that ignore an injected click or key — the colony
  landing (colland.cpp:203-213) — answer `ACTIVATE_FIELD` on their
  whole-screen hidden field, which is what finished this run; 122's GNN
  screen was probably the same case and was not retried. No code change was
  needed; `mapeta` is unchanged.

### GAME menu: the menu stays drawn under the confirmation — work order 124 D, 16 September 2026

**Brief 124** (`doc/briefs/124-*`). The original draws `Confirmation_Box_`
over the popup's own picture (gendraw.cpp:180) and the menu stays visible
behind it; HD drew the body alone, because `present` asked the
confirmation's field list, which carries only YES and NO. The screen now
keeps the menu's buttons as its last MENU list had them (`menu_keys`, so a
multiplayer menu without LOAD and NEW stays without them) and `gmdraw._menu`
draws those under the box.

- **Smoke:** the node-render check asserts the four menu words are drawn
  under the confirmation; the old rule fails it. Count stays 190.
- **Live** (Data's OrionLayer closed first; the game was found with the GAME
  menu open; SAVE4 reloaded through it; a picture after every click; SAVE1-9
  identical, SAVE10 unchanged): NEW confirmation at 1920x1080 and 2560x1440
  beside the native frame, `~/orionlayer-fixtures/evidence/work_order_124/D_*`.

### GAME menu: save slot names — work order 124 A, 16 September 2026 (a report)

**A patch is needed, and it is already written: open fix 14,
`doc/ext_save_slots.patch`, reported 14 September, not applied.** The
original reads the names from the SAVEn.GAM headers into
`MOX::_save_game_description[10]` whenever the dialog opens
(`FILEDEF::Get_Saved_Game_Descriptions_`, filedef.cpp:207-243); the snapshot
carries `_settings` but not that table, and the framebuffer read was
considered and rejected (free text, colour codes, no validation). The patch
still passes `git apply --check` on the current tree. The HD dialogs keep
"Slot N" (HD STATE, decision 60) until Data applies it. Details under open
fix 14.

### GAME menu: the Music and Sound Fx bars — work order 124 C, 16 September 2026

**Built, transcribed, and no patch needed.** Open fix 15's premise was
stale: open fix 3's second half (applied since 5 September) keeps an
injected click's pointer, so an `INJECT_CLICK` on the bar sets the volume.

- **The original, read:** two scroll fields, native (206, 219) and
  (206, 241), 155 x 12, value 0..156 from `Find_Bar_Position_` —
  `(x - 206) * 156 / 155`, so 155 is never produced — stored as
  `level = value * 100 / 155` in `_settings` (5 or less switches the channel
  off), shown on opening as `value = level * 155 / 100`, which is lossy
  (49 -> 75 -> 48). The bar is GAME.LBX picture 7 revealed up to `value`
  pixels: ten blocks, measured off the picture, a block can be partly lit.
  A held press follows the pointer; the level is applied when the press
  ends. Sources in `layout.json` `sliders._note`.
- **Live, before building** (Data's OrionLayer closed; SAVE4 reloaded;
  GAME menu up; a picture after every click): `INJECT_CLICK` (321, 247) set
  Sound Fx 50 -> 74, (284, 247) back to 50.
- **HD** — `screens/game_menu/gmsliders.py`, boxes `volume_panel`,
  `music_label`, `music_bar`, `sound_bar`, `sound_label` at the original's
  rects; block colours measured into `colors.json` (`slider_off`,
  `slider_on`, `slider_glow`). The drawn value is read off `_settings`. A
  press and a drag preview locally and send nothing; the release sends ONE
  click at the native point that gives the chosen value; the preview is held
  until the snapshot carries it. `main.py` now routes a left-button release
  to a screen that has `handle_left_release`. Help regions 420/421 are back.
- **Live, HD:** a drag on the Music bar from 25 % to 75 % sent nothing while
  held and one click on release — Music 49 -> 74, the HD bar and the native
  bar both at seven blocks and part of the eighth; restored to 49 (value
  76). SAVE1-9 identical, SAVE10 unchanged.
- **Open fix 15** answered (no command needed, dependency on open fix 3
  named); decision 61's example amended; the OMISSION is gone from the
  module, `layout.json` and this document.
- **Smoke:** one new check (the arithmetic over every value the game can
  produce, the live 74 and 50, lit width from `_settings`, nothing on press
  or drag, one click on release, the preview released after the floor);
  the help and marking checks follow the new state. **190 -> 191.**

### Pressed words: GAME and the GAME menu — work order 124 B, 16 September 2026

**Mostly a TRANSCRIPTION, and orange is the original's colour.** A held
button field draws frame 1 of its picture (`Draw_Field_`,
fields.cpp:2710-2717; YES/NO in `Draw_Confirm_Box_`, gendraw.cpp:35-49),
and in BUFFER0.LBX 1 (GAME), GAME.LBX's buttons and CONFIRM.LBX 1-2 that
frame is the word in orange, palette index 126 = (252, 136, 0), measured
through the live palette. It lasts while the press does. So HD draws the
word in `button.pressed_text` while the left button is held on it and the
pointer is still inside — not a timed flash.

- **HD INVENTION — the load and save rows.** They are hidden fields and the
  original colours a row by `active_save_slot` only (loadsave.cpp:852-878);
  Data wants every click in the tree to show, so a pressed row turns the
  same orange. Marked in `core/pressfeedback.py`, here and in the smoke test.
- **OMISSION:** the pressed pictures also nudge the word by a native pixel
  or two; not measured cleanly, not reproduced.
- **One implementation:** `core/pressfeedback.Pressed` on every screen
  (`ScreenBase.pressed`, released by `handle_left_release`); the galaxy
  map's GAME word, `gmdraw.button` and the slot rows read it. It starts on
  the press, before anything decides whether to send (decision 33). The
  9-slice frame's old side-button flash is a different mechanism and stays.
- **Smoke:** one check (SETTINGS and GAME orange while held, a Load row
  orange with its send refused, all cleared on release, the markings).
  **191 -> 192.**

### GAME menu frame against the nav bar — work order 124 F, 16 September 2026 (a measurement, no change)

Since 123 the frame's slack goes below the popup. Measured on the drawn
metal (alpha >= 16) against the galaxy map's nav boxes and the ink of their
labels (threshold 60 and again at 10, the second so an anti-aliased edge
cannot hide):

| window | metal reaches into the nav boxes | boxes it overlaps | label ink under metal | metal's last row / labels' first ink row |
|---|---|---|---|---|
| 1920x1080 | 16 px (to y 985, boxes from 970) | PLANETS, FLEETS, LEADERS, RACES | 0 | 985 / 986 |
| 2560x1440 | 23 px (to 1314-1315, boxes from 1293) | the same four | 0 | 1314 / 1315 |
| 3840x2160 | 36 px (to 1973-1975, boxes from 1940) | the same four | 0 | 1973 / 1974 |

**No label is covered, and there is no margin either:** at every size the
metal ends on the row directly above the labels' first ink row. Not fixed,
per the order; a font that is a pixel taller or a label moved up in F5
would be covered. *(Void since work order 125: the frame sits inside the map cutout
and no longer reaches the nav bar at all — below.)*

### Galaxy map: the research readout's source — work order 124 G, 16 September 2026 (a report, no change)

HD prints `research_accumulated` RP over `+research_produced` RP; the
original prints something else, from `MAINSCR::Print_Main_Screen_Data_`
(mainscr_main.cpp:178-243):

- breakthrough -> HESTRNGS 0x183 "Breakthrough"; no field -> 0x188 "none"
  (HD already matches both);
- otherwise `turns = COLCALC::Player_N_Turns_Until_Research_Complete_(plr)`
  (colcalc.cpp:432-458): if the field's status is 3 (researched) 0; if
  `produced == 0 && accumulated <= cost` -1; else repeat
  `turns += 1; accumulated += produced; total += chance(accumulated,
  produced, cost)` until `total >= 100`, where
  `chance = (accumulated - cost) * 100 / cost` when `0 < cost < accumulated`,
  clamped to 100 and raised to 1 if 0, else 0
  (`Chance_For_Research_Breakthrough_Aux_`, :469-484);
- `cost = Player_Research_Cost_(plr, field)` (:526-539) =
  `TECHDATA::_technology_fields[field].cost` (techdata.cpp:319ff), plus
  `hyper_advanced_tech[field - 75] * 10000` from field 75 on;
- `turns > 0`: the chance for THIS turn as "N%" when above 0, then "@" and
  HESTRNGS 0xE1/0xE2 "%d turn(s)", then `research_produced` and the unit;
  `turns < 0`: "0 RP"; `turns == 0`: the chance and `research_produced`.
  The "~" in the native picture is the "@" printed in the sidebar font.

**Checked against what the screens showed:** 412 RP / 44 produced / 18
turns (SAVE4, 3509.0) and 500 RP / 44 / 16 turns (3509.2) are both
reproduced by that loop for any cost from 896 to 935, and the table holds
fields at 900 (for example fields 34, 41, 45).

**What HD would need, and does not have:** the cost table (a copy of
`_technology_fields[].cost`, legitimate only with a checker against
techdata.cpp, as `tools/monster_hull_check.py` does for the hull tables),
the per-field status `tech_fields[]` and `hyper_advanced_tech[]` from
`s_player` — neither is in the verified player spec (decision 23). The
readout was not changed.

### GAME menu inside the map opening — work order 125, 16 September 2026

**HD DEVIATION, superseding 122's anchor.** The frame is fitted to the
galaxy map's `map_area` cutout (from its `boxes.json`, per resolution list):
height = the cutout's, aspect kept, centred. No extra inset — the image's
own transparent margins (20 rows top, 29 bottom, 34 columns each side) keep
the metal about 12 ref px clear of the cutout at the top and 18 at the
bottom. The body is the largest 628:850 box inside the opening less the
bleed; every overlay box is seated by the same move and ONE factor, fonts
through `content_scale` (`gmframe.seat`, run from `_reload_boxes`).
`boxes.json` keeps the design geometry; `Box.to_file` makes an F5 save write
the inverse. Decision 69 amended.

**Measured before building** (rendered ink heights through
`Style.render_text`; factor f = 0.8666 at every size, since `map_area` is
one reference rect):

| | 1920x1080 | 2560x1440 | 3840x2160 |
|---|---|---|---|
| frame today -> new | 426,-14,797,1020 -> 455,66,691,885 | 568,-18,1062,1360 -> 607,88,921,1180 | 853,-27,1593,2041 -> 910,132,1382,1770 |
| size against today | 0.867 w, 0.868 h | 0.867, 0.868 | 0.868, 0.867 |
| opening new | 527,133,548,744 | 702,177,730,992 | 1054,266,1096,1488 |
| menu buttons / SETTINGS / RETURN, font px (ink) | 30 (21) -> 25 (18) | 40 (28) -> 34 (24) | 60 (42) -> 51 (36) |
| slider labels | 30 (22) -> 25 (18) | 40 (29) -> 34 (24) | 60 (43) -> 51 (37) |
| slot row / detail | 28 (20) -> 24 (17) / 22 (16) -> 19 (14) | 37 (27) -> 32 (23) / 29 (21) -> 25 (18) | 56 (40) -> 48 (35) / 44 (32) -> 38 (27) |
| settings option | 24 (22) -> 20 (18) | 32 (30) -> 27 (26) | 48 (45) -> 41 (39) |
| confirmation panel (after 0.900 and f) | 529,338,544,396 | 705,450,725,528 | 1058,676,1088,792 |
| warning panel (after 0.843 and f) | 529,398,544,313 | 705,531,725,418 | 1058,797,1088,627 |
| question lines (NEW, QUIT, slot 7 missing, multiplayer) | 2, 2, 1, 4 — unchanged | unchanged | unchanged |
| slider blocks (device px) | 10 blocks, 27 -> 23-26 | 36 -> 31-34 | 54 -> 46-50 |
| slider values reachable from a device pixel | all 156 before and after | all | all |

Nothing fell below what the order named as a limit: no extra line, ten
countable blocks, every value still reachable. The smallest text is the
slot row's detail line at 1080p, 14 px of ink.

- **The volume bars are in the MENU,** not in Settings: they are fields of
  `Add_Game_Popup_Fields_` case 0 (loadsave.cpp:200-201); the pictures show
  them there.
- **Nav bar and GAME field:** by construction the frame lies inside the
  cutout (y 66..951 at 1080p against the nav boxes from 970 and the GAME
  cutout ending at 64); 124 F's measurement is void.
- **Press feedback and help:** both checks stayed green without change —
  they read the boxes' seated rects, the same objects the hit tests and the
  drawing use, so there was no second rect to miss.
- **Smoke:** the frame check retargeted (inside the cutout, height and
  centre, metal clear of the cutout's edges, one factor, the editor save
  writing the file's rect; it fails with the frame moved 20 px up). The
  count stays 192.
- **Live** (Data's OrionLayer closed first; the game as Data left it, the
  GAME menu open on the SAVE4 state; a picture after every click; SAVE1-9
  identical, SAVE10 unchanged; 44 menu-field activations, no click or key
  injected into the game): menu with the volume bars, Settings, Load, the
  slot-7 warning, Save and the NEW confirmation at 1920x1080, 2560x1440 and
  3840x2160 beside the native frame,
  `~/orionlayer-fixtures/evidence/work_order_125/` (the 1080p menu and
  Settings as `42_*` and `43_*`, see the next line).
- **Found, not fixed:** when OrionLayer connects while the game ALREADY
  shows the GAME menu, the overlay opens over the main-menu screen instead
  of the galaxy map (the dispatcher has never been on the map): the first
  two 1080p pictures show the main-menu artwork behind the frame. After one
  ESC to the map everything is as intended; the 1080p menu and Settings were
  retaken that way.
  **FIXED by work order 126 D (17 September 2026):** `GameMenuScreen.
  OVERLAY_PARENT = "galaxy_map"` (SCREEN_GAME is entered only from the map's
  GAME button, mainscr_main.cpp:609-613) and the dispatcher enters the parent
  before it opens such an overlay. One new check (the app on the main menu,
  a first snapshot at screen 8: the map is active under the menu; with the map
  already active it is not re-entered); it fails without the dispatcher change
  (`evidence/work_order_126/D1_check_fails_without_fix.txt`). 195 -> **196**.
  Headless only; not re-run live.

### GAME menu: the frame missing on the first opening — fixed, 16 September 2026

**Found by Data in the running tree at abcbab0:** the GAME menu drew its
opaque fill and no frame. **Cause:** `GameMenuScreen.enter` called
`super().enter()` — which reloads the boxes and seats them
(`gmframe.seat`) — BEFORE it loaded `layout.json` into `self.words`. On the
first entry `seat` found no `frame` block, so there was no placement:
`gmframe.draw` returned False, `gmdraw.panel` fell back to the fill, and the
boxes stayed at the file's unscaled positions. A second entry (the menu
opened again, a resolution change) had the words and showed everything.
Blit order (fill, then frame) and the scale target (the placement's frame
rect) were right; they were never reached.

**Why nothing caught it:** every frame check, and every live run, entered
the overlay at least twice (`update_from_game` plus an explicit `enter`,
repeated openings, resolution changes), and the checks measured geometry,
not drawn metal.

- **Fix:** the words are loaded before `super().enter()`.
- **Smoke:** one new check — a fresh app, the overlay opened ONCE through
  the dispatcher, rendered, and the drawn pixels compared with the scaled
  frame image wherever it is opaque (alpha >= 250, since `smoothscale` tops
  out at 253), 98 % required at 1080p and 1440p. It fails with the old order
  (no placement on the first opening) and with the image blit removed
  (0 of 145230 pixels). **192 -> 193.**

### GAME menu: save slot names from the engine — open fix 14 applied, 16 September 2026

Data applied `doc/ext_save_slots.patch` and rebuilt orion2re (linux-debug).
Live (orion2re started from `~/Master of Orion 2`, SAVE4 loaded from the
main menu's Load dialog, one client, a picture after every step, SAVE1-10
identical; evidence `~/orionlayer-fixtures/evidence/open_fix_14/`):

- **Load dialog:** `MSG_SAVE_SLOTS` with `screen_data` 2 and the ten
  descriptions as the native dialog prints them; the HD rows draw them with
  stardates and dates. Nothing on the HD side had to change to read it.
- **Save dialog:** `screen_data` 3; a click on a valid row starts the name
  edit with that row's name ("new"), sending nothing — the pre-fill
  (`gmsave.SaveEditor.start`) already existed and only lacked the data.
  **Difference kept:** an EMPTY slot starts the HD edit empty, where the
  original copies "... empty slot ..." into the field (loadsave.cpp:517)
  and the first backspace clears it (fields.cpp:1177-1193); the name that
  reaches the game is the same.
- **The main menu's own Load dialog** gets no block (SCREEN_GAME only) and
  has no HD version.
- **Removed:** the "Slot N" HD STATE — label, `layout.json` words, module
  and status markings. Without the block (only the tick between the field
  list and the slot message) a row now draws its plate and no invented
  label. `tools/version_check.py` requires the patch; open fix 14 reads
  APPLIED; decisions 60 and 61 amended.
- **Smoke:** checks 4 and 7 follow (no "Slot N" may return — fails when the
  label is put back; the marking stays gone), and 124 B's pressed-row check
  now presses a row carrying an engine name. The count stays 193.

### Colony list: a click on a stacked figure picks up that figure — 16 September 2026

**Reported by Data:** with stacked figures one had to click LEFT of the
figure to move. **Not two copies:** the draw (`colonylist`, `blit(surf,
(rect.x, figure_origin_y(...)))`) and the hit test (`cell_at_x`, `rect.x <=
x < rect.x + rect.width`, `width = int(pitch) - gap`) both read the same
`colonytrack.row_boxes`. **The fault was what the one geometry described:**
the slot a sprite is BLITTED at, not where the figure is SEEN. The ink starts
a master column or more into the 28 px canvas, runs past the slot into the
next, and shows through the next figure's transparent columns; the gap
between cells answered nothing. Measured on the extracted figures, clicks on
the centre of each figure's visible area: 165 of 210 missed at 1920x1080,
156 at 2560x1440, 165 at 3840x2160.

**The original** (`Do_Colony_Info_Pop_Stuff_For_Pop_` mode 3,
coldraw.cpp:362-366) takes the first icon in drawing order with `x <= (30 -
squish) * (index + 1) + left_x`: each icon owns the strip up to the next
icon's left CANVAS edge, so where two overlap the COVERING (later-drawn)
figure owns the overlap.

- **DEVIATION — the zone is the figure as seen.** `colonytrack.pick_zones`
  is the one home (decision 5): the sprites are laid out in drawing order at
  the renderer's own x and y, each figure's visible ink gets a centre column,
  neighbours meet halfway between their centres, the first zone starts at
  its slot's edge and the last ends at its last inked column. The covering
  figure still owns the overlap where its ink is; the original's canvas
  strip is replaced by the ink. Identity is unchanged: the pick is (job,
  index) and `colonysend` still injects the original's slot point. Without a
  figure set the zones are the coloured cells as drawn, as before. The pick-
  up passes the set the row is drawn with (`colonymoveui.click(figures=)`).
- **Smoke:** one new check. Every count 1 to 20 in each of the three job
  columns at 1920x1080, 2560x1440 and 3840x2160 is rendered through the real
  screen, each figure in its own colour, and the centre of what is visible of
  it must pick it up. It uses a synthetic silhouette shaped like the game's
  (the extracted figures are not committed, decision 50) and measures the
  extracted set too when it is on disk: 630 of 630 at each size. With the
  old slot rule it fails (426 of 630 at 1920x1080). Count 193 -> **194**.
- **Not live-tested:** a headless measurement; the pick-up is local and sends
  nothing, and the drop path is unchanged.

### The commit is coupled to the smoke test — work order 126 B, 17 September 2026

**A hook, in the tree:** `tools/githooks/pre-commit` runs the full suite
before git writes a commit and refuses it on any exit but 0 (a failure,
139, 137) and on a zero exit without the PASSED line. `tools/setup.py`
sets `core.hooksPath = tools/githooks` (and `--check` reports it);
decision 31 is amended with the rule and why a hook and not a wrapper. It
tests the working tree, not only the index. `--no-verify` bypasses it.

- **Shown** in a throwaway clone with the hook on: a suite replaced by one
  that SIGSEGVs (shell exit 139) and by one that fails — no commit created,
  HEAD unchanged; the real suite green — the commit created. Evidence in
  `~/orionlayer-fixtures/evidence/work_order_126/B_hook_*.txt`.
- **Smoke:** one new check runs the hook against four stub suites (SIGSEGV,
  failure, silent zero exit, pass) and reports whether this clone has the
  hook on. **194 -> 195.**
- **Fundament, filed from the 16 September handover:** decision 5 gains
  "one function makes drawing and hit-testing AGREE, not RIGHT" (the stacked
  figures, 165 of 210); Diagnosis gains the colony screen's right click as a
  live-protocol line; decision 31 the coupling above.

### The smoke test: quiet mode, a memory line, thirty runs — work order 126 C, 17 September 2026

- **`--quiet`** sends everything a run prints (check sentences, reports, log
  lines, SDL output) to a temporary file at descriptor level and shows the
  summary line only; on a failure the last 60 lines of that file, then the
  traceback. Without the switch the output is as before. The hook and
  `tools/setup.py` use it. `faulthandler` writes a crash's Python stack to
  the REAL stderr in both modes, so a 139 leaves a stack behind.
- **Last line, both modes:** `peak resident memory: N MB` (`ru_maxrss`).
- **Check count unchanged: 195.**
- **Thirty full runs** (`--quiet`, one after another, exit and peak RSS per
  run from `wait4`, the suite's own line beside it): **30 of 30 exited 0**;
  peak resident memory **4540 to 4836 MB**; **66.6 to 68.1 s** per run. Table
  in `~/orionlayer-fixtures/evidence/work_order_126/C_thirty_runs.md`, logs
  beside it. The exit-139 question has no occurrence in this sample; the
  memory figure confirms chat's measurement in kind (a 4 GB container dies).
- **Measured against the order:** a full run on this machine takes ~67 s, not
  ~10 s. The order's time argument against running part of the suite is
  therefore weaker here than it was drafted; decision 31 (full suite) is
  unchanged and the question is parked with the memory figure.

### SAVE11.GAM classified — work order 126 D, 17 September 2026

**Nothing in orion2re 1.60.0 writes or reads it**, so in the live protocol it
belongs with SAVE1-9: hashed before and after, identical. From the source:
`FILEDEF::Save_Game_(slot)` writes `SAVE<slot+1>.GAM` (filedef.cpp:43-48),
and its callers pass 9 (initgame.cpp:262, loadsave.cpp:1262, nextturn.cpp:32,
mainscr.cpp:3067), the dialog's slot, bounded to 0-9 (loadsave.cpp:536-539),
or `active_save_slot` behind a `< 10` guard (mainscr_main.cpp:617/628 into
loadsave.cpp:1813). `Load_Game_` is reached with 9 (mainmenu.cpp:472), the
dialog slot, a multiplayer slot 0-9 (multplay.cpp:767-772) or the same
guarded `active_save_slot` (loadsave.cpp:1639). Descriptions, status and
dates loop over ten (filedef.cpp:208, loadsave.cpp:599-640, :688-700).
QUIT sets `active_save_slot = 10` (loadsave.cpp:1263) after saving slot 9,
and both hotkeys that would use it refuse 10. The Extension API names no
save file. **What made the file is not in this tree:** it is dated 30 July
2026, 223,090 bytes like SAVE6 and SAVE9 of the same day, with a mangled
description (`\x031\x01`) — from before this engine's save code as it
stands; not investigated further. CLAUDE.md carries the rule next to SAVE10.

### The colony runs order — what is open, established — work order 126 E, 17 September 2026

The order chat called `workorder_colony_runs_and_doc_audit.md` is filed as
`doc/briefs/88-*` (the full order, 9 September) and `91-*` (its runs, as an
attachment). Against the tree:

- **Part 0** (where are the briefs) — done: `doc/briefs/`, brief 89, 9 Sep.
- **Run A** (pop-move 3a-3c) — done: d98a96d, "Run A — what one command
  would buy" above, then decision 52 and `doc/ext_move_pop.patch` applied
  (open fix 12).
- **Run B, the documentation audit** — NOT done. a83e5fc (12 Sep) was a code
  redundancy audit of the static-frame rebuild, not this. Per work order 126
  it is not today's; it goes with the reading-budget order (127).
- **Brief files:** the four names the 9 September handover missed are all in
  `doc/briefs/` (78, 79, 82, and the pop-move brief as 90). Still missing:
  **the head of brief 90** (it starts mid-sentence) and **work order 125's
  own text** (the GAME menu order the 16 September commits cite). Parked.

Nothing else remains that needs no decision; no live run was needed.

### Galaxy map: input split from rendering — work order 126 F, 17 September 2026

`screens/galaxy_map/screen.py` had one honest seam, and it is the one brief
110 part C will need: INPUT (motion, click and the map click, activation,
keys, right button and map cancel, wheel) against loading, geometry and
drawing. The input bodies moved to `screens/galaxy_map/mapinput.py` as
functions of the screen, `self` renamed `screen`, nothing else changed; the
`handle_*` hooks stay on the class and delegate, falling through to
`ScreenBase` exactly where the methods returned early before. The home ping
and help-rect helpers stayed (the smoke test and `core/screenhelp` call them
on the screen). **583 -> 461 code lines** (890 -> 722 total); still on the
exceptions list, regenerated from `tools/linecount.py` — the rest is one
thing (a screen's render orchestration and state), and a further cut would
be the number talking. Two checks read the moved text and follow it: decision
66's marking now in `mapinput.right_button` (plus: the hook must call it), and
the eta lock line in `mapinput.py`. Smoke **197**, unchanged.

### Read ahead: four screens — work order 126 G, 17 September 2026

Source readings, nothing built: `doc/colony_screen_reading.md` (SCREEN_COLONY 1
and SCREEN_QUEUE_POPUP 25), `doc/tech_change_reading.md` (36),
`doc/fleet_screen_reading.md` (4), `doc/races_screen_reading.md` (6). Written by
read-only sub-sessions and spot-checked where each file's provenance note
says. What they change for the tree today, all parked in
`doc/briefs/126-parked-for-data.md` (items 3-7):
- **Screen id 6 is two screens:** the game's Races screen and, through our
  own `ext_screen_id.patch`, race selection; `select_race` claims 6, so the HD
  map's RACES button is expected to open HD Select Race over diplomacy (not
  seen live). Open fix 22, DESCRIBED, NOT APPLIED.
- **The map's parking vs the turn-start research prompt** (screen 0, field 9
  a choice row) — decision 59's hazard in a second place, from the source.
- **`ship.py` `weapons()`** skips empty slots where flt2.cpp:696-701 stops.
- Neither the colony view nor the build queue fits the draft
  one-content-box rule; research, fleet and races do, with caveats.

### Screen 6 split: race selection reports 51 — work order 128 B, 17 September 2026 (open fix 22 applied)

**Seen live first** on SAVE4 (3509.0): RACES on the HD galaxy map sent
`ACTIVATE_FIELD 14`, the game reported 6 and drew Race Relations, and HD
switched to `select_race` (`evidence/work_order_128/B_before/`).

- **Engine** (Data's decision, the one change to orion2re this order allows):
  race selection reports the synthetic **51**, past the SCREEN enum's last
  value 43; orion2re 3305d78c on `orionlayer-local`, `doc/ext_screen_id.patch`
  revision 2 (hunks regenerated, forward-applied to a pristine export and
  reverse-dry-run against the tree).
- **OrionLayer:** `core/screen_names.py` is the one home — 6 has no HD screen,
  51 is `select_race`, and `ENGINE_SCREEN_MAX = 43`, which
  `tools/version_check.py` now reads from orion2_consts.h and requires with
  the patch's new marker. `select_race` claims 51; Empire Identity's lock is
  51 on the stock path and (50, 51) after Custom Race. The table's entry for 8
  said "no HD screen" although `game_menu` claims 8 — corrected, found by the
  new check. `doc/v3_orion2re_index.md` and `doc/ext_api_dokumentation_v3.md`
  follow.
- **Live after** (new binary, New Game from the main menu, through HD):
  custom path 13 -> 51 select_race -> picture mode -> 50 custom_race -> Accept
  -> Empire Identity (the game stays at 50) -> 39 -> 0 galaxy map; stock path
  13 -> 51 -> Empire Identity (the game stays at 51) -> 39 -> 0. RACES then:
  the game reports 6 and HD falls back to the framebuffer
  (`use_original`), ESC back to the map (`B_after_custom/`, `B_after_stock/`,
  `B_after/`).
- **The stock-race accept leaving the id set:** unchanged in behaviour, changed
  in meaning. The game keeps reporting race selection's id through the name
  and banner dialogs until galaxy generation — 51 now, 6 before — and HD's
  Empire Identity lock depends on it. It no longer reads as the Races screen.
  Not widened. The patch header's claim that every accept goes through
  `Racial_Option_Screen_` is corrected there: the stock accept does not.
- **Smoke:** one new check reads every screen module (tree and mods) and holds
  the rule — one screen per id, engine ids within 0..43, synthetic ids above
  it, the table naming the claiming screen; red with the maximum set to 60 and
  with a mod screen also claiming 51 (`B_screen_id_check_red.txt`). The routing
  instances move 6 -> 51. **197 -> 198.**

### The galaxy map parks only into its own list — work order 128 C, 17 September 2026

**Decided: guard by field-list shape.** Decision 59's own shape test
(`game_menu/nodes.classify`) classifies the GAME popup's dialogs and is not
reusable for the map; what is, is the map cancel's lookup of a field by type
and native rect in the LIVE list (decision 20). It is extracted to
`mapboxes.live_field` (second caller, so named rather than a third copy) and
`mapinput.send_map_cancel` calls it. `screen.update` parks only while the game
reports 0 AND the list holds both the grid field and the zoom-out button
(`layout.json` `zoom_out_field`: type 0, (244,455)-(298,473) — mainscr.cpp:1381
and :1392 for the position and hotkey, the live list and
`tools/galaxy_box_fields.json` for type and end corner), and it sends to the
index found there; `viewctl.ZOOM_OUT_FIELD = 9` is gone.

- **Smoke:** a research-shaped list (doc/tech_change_reading.md section 2) at
  screen 0, zoomed in: nothing sent; the map's own list with the button at
  another index: sent to that index. Red with the old screen-number-only
  guard (`evidence/work_order_128/C_parking_check_red.txt`). The existing
  parking checks now carry the recorded list. **198 -> 199.**
- **Live — the fault itself not reached; a worse one reached by my driver.**
  On a fresh stock-race game (3500.0), HD view zoomed in, one turn: the game
  itself stood at full zoom-out, so the old code had nothing to park and sent
  nothing — the original fault needs the GAME's own map zoomed in at turn
  start, which the HD map does not do. The turn-start "SELECT NEW RESEARCH"
  prompt came up under screen 0 with 38 fields (`C_preC/002_*.png`). **My
  driver misread it as a message box from a stale state and sent
  `ACTIVATE_FIELD 1` into it; orion2re died with SIGSEGV in
  `TECH::_Tech_Select_`** (`C_orion2re_segfault_backtrace.txt`), called from
  `REPORT::Set_Initial_Tech_`. That is the reading's null-dereference
  (tech.cpp:354-369, a commit with the pointer over no entry) confirmed live,
  and exactly the kind of send the guard exists to refuse. No save changed
  except SAVE10, the autosave of that turn end (logged). Not pursued further,
  as the order says. Recorded as open fix 23, an observation.

### Planets: the hovered row is the drawn row — work order 128 D, 17 September 2026

Hover picked its row by `(y - top) * n // height`; the rows were drawn by
`listgrid.all_bands` (h // n, the remainder on the last band) — two
arithmetics, disagreeing on single pixel lines (redundancy audit D8).
`planetdraw.row_bands` is now the one source of the bands, `render_list`
draws in them and the hover finds its row with the new `listgrid.band_at`,
which takes the drawn bands rather than dividing again (decision 5).

- **Smoke:** every pixel line of the list at 1366x768, 1920x1080, 2560x1440
  and 3840x2160 hovers the row drawn there; and against the picture, the first
  and last line of every drawn band, rendered, show `row_selected` at that y.
  Red with the old division: "1366x768 y=149: hover 0, the row drawn there 1"
  (`evidence/work_order_128/D_hover_check_red.txt`). **199 -> 200.**
- **Neighbours read in `doc/redundancy_audit.md`, not worked:** T6 (the scroll
  arrows' rects computed in `render_scroll` and again in `scroll_arrows` for the
  click — they agree today, the same decision-5 shape), D19 (scroll thumb
  arithmetic differs from the colony list's; Planets cites no source), D9
  (window rects through `layout.rect(box_rect)` against `Box.screen_rect`).
  Not live-tested: hover sends nothing to the game.

### `weapons()` stops at the first empty slot — work order 128 E, 17 September 2026

**The two sources, before the change.**
- **Can a gap exist? No, not in `count`.** Every writer packs from slot 0 and
  never leaves a used slot below count 1: the player's design screen puts a new
  weapon in the first empty row (design.cpp:869-876) and `Clear_Weapon_Slot_`
  shifts the later rows down (design.cpp:1724-1745); the AI adders write at a
  running index only for count > 0 (aidesign.cpp:669-704 and siblings);
  templates list from slot 0 (ship_config.cpp:58-80); strategic designs pack
  (initship.cpp:918-968); refit copies the design whole
  (colbldg.cpp:1951-1960); capture changes only the owner and `current_count`
  (combinit.cpp:2876-2913); combat writes back only `current_count`. Empty slots
  carry type 0 (designs) or, on colony and outpost ships, -1 or a planet index
  with count 0 (plntsum.cpp:475-478). A read-only sub-session traced the
  writers; design.cpp:869-876 and :1724-1745 and flt2.cpp:693-701 were checked
  by hand.
- **Saves: 0 gaps.** Live on SAVE4 (3509.0) and SAVE5 (3509.1): 60 ship
  records each, 21 with a weapon, 0 with a gap
  (`evidence/work_order_128/E_probe_SAVE4.json`, `_SAVE5.json`). Offline, a
  scan for the count-prefixed 129-byte ship array, validated against the two
  offsets the live arrays were found at in their files, over SAVE1-11 and the
  three fixtures: every real array with armed ships (60/21, 60/22, 71/37,
  109/61, 31/23, …) has 0 gaps; the only "gaps" are 255-record hits at offsets
  129 bytes apart, which are not the array (`E_offline_scan.json`).

**The change.** `core/structs/ship.py` `weapons()` now stops for good at the
first slot with `type < 0 or count < 1`, as flt2.cpp:693-701 does; its docstring
said `count > 0` for the same lines. **Callers:** one —
`screens/planets/monsterpanel.py:97`, the monster panel's weapon lines. Its
result cannot change for any design the engine writes (packed, and no used slot
with a negative type); it would differ only for a gap nothing produces.
**Smoke:** a constructed ship with a gap, with a used type at count 0, with a
negative type first, and a packed one; red with the old skipping loop
(`E_weapons_check_red.txt`). **200 -> 201.**

### Three small safeguards — work order 128 F, 17 September 2026

- **faulthandler at the top of `tools/smoke_test.py`,** before every other
  import, so a segfault anywhere — imports included — prints the Python stack
  before the process dies; `_run` still re-points it at the real stderr before
  `--quiet` redirects. Shown in a worktree with a forced segfault at import:
  exit 139, "Fatal Python error: Segmentation fault" and the Python and C
  stacks on stderr; `git commit` through the hook refused, HEAD unchanged, the
  stack in the hook's log (`evidence/work_order_128/F1_faulthandler_segfault_demo.txt`).
- **The hook in a fresh clone:** `tools/setup.py` already sets
  `core.hooksPath` (work order 126 B) and stays the one home. Proven: a fresh
  clone has no hooksPath; `python tools/setup.py` rebuilds, runs the suite
  (201 green, 5173 MB) and sets it; an `assert False` at the top of `main()`
  makes `git commit` exit 1 with HEAD unchanged (`F2_fresh_clone_hook.txt`).
- **The decision-28 check reads what it means.** It asked for "decision 28"
  and "DEVIATION" anywhere in four whole files; the fundament passed on words
  from other entries while entry 28's exception carries neither. It now reads
  entry 28 itself ("ONE EXCEPTION, AND IT IS MARKED" and
  `colonytrack.figure_size`), `figure_size`'s docstring, `FigureSet.__init__`
  and the status paragraph of the change. Red with the exception heading
  removed from entry 28, where the old condition stays true
  (`F3_decision28_check_red.txt`). **Neighbours with the same weakness, listed
  not swept** (from 127's Stop 1): the move-markings check (7 needles in the
  status file; 2 match only text saying the marking was withdrawn or removed),
  and the map-lines check's single needle `"maplines.py"`. Count unchanged:
  201.

### A live tool is a client — work order 129 A, 17 September 2026

`tools/livesend.py`: every send identifies the dialog from the FIELD LIST of
the state it is handed at that moment, and refuses — raising — otherwise.
`activate` requires the index to exist in the live list and, where the caller
names them, its type and native rect; `click` resolves the field the point
would reach (lowest index wins, fields.cpp:1264-1283) and checks its type;
`key` needs a screen or a shape, because ESC cascades. The shape tests are the
existing ones: `mapboxes.live_field` (work order 128 C) for a field named by
type and rect, `game_menu.nodes.classify` for the popup's dialogs, plus the
colony summary's seven sort buttons at native y 446..469 (colsum.cpp:267-273,
live 3 September 2026).

- **Moved onto it:** `tools/colony_move_probe.py` (sort key, both scroll
  activations, the pick-up and drop clicks), `tools/game_menu_hd.py` (the slot
  strip, the fifteen-key burst, the native ESC), `tools/zoom_probe.py` (both
  zoom activations, the arrow keys). **Not moved, and why:**
  `tools/colony_move_hd.py`, `colony_drop_sweep.py`, `colony_drop_timing.py`
  and `colony_roundtrip.py` send nothing themselves — they post pygame events
  into the real screens, so the product's own guards decide; `ext_diag*.py`
  and `struct_probe.py` read only.
- **Smoke:** eight wrong-shape sends refused with nothing sent (the research
  prompt's shape under screen 0 among them), and the map's own list passing all
  three send kinds. **201 -> 202.**
- **Fundament:** "A LIVE DRIVER IS A CLIENT" and "A COUNTER-TEST THAT RESTORES
  A FILE CAN BE MEASURING THE MUTATION", both under Diagnosis.

### The two turn-start research dialogs are on the wire — work order 129 B, 17 September 2026 (open fix 24 applied)

**The reading first:** `doc/newtech_reading.md`. The presentation is
`SCIENCE::Science_Room_` (science.cpp:112-392), entered from
`TECH::Tech_Select_` -> `Show_Off_Researched_Tech_` (tech.cpp:103), and the
select list follows at tech.cpp:106 after `current_research_field` and
`research_breakthrough` are zeroed (:104-105) — so which project completed is
off the wire once the list is up. Both run under SCREEN_MAIN, which confirms
126's claim for both. The room's list is three fields (a whole-screen hidden
one and an ESC hotkey, science.cpp:169-171) and one activation advances ONE
discovery; the same room shows stolen and artifact technology
(report.cpp:814, :822), so its shape does not identify research —
`research_breakthrough != 0` does.

**THE FINDING THAT DECIDED THE PATCH.** The path open fix 22 uses — writing
`MOX::_current_screen` — is not available here: the game DRAWS from that
value in both dialogs' description box, for its x (textbox.cpp:40-50) and for
its colour group (textbox.cpp:284). So the ids are reported **on the wire
only**: `ext::g_screen_override`, read by `ext::Tick` when it serializes, set
for a scope by `ext::ScreenOverride` — 52 in the science room, 53 in the
select list, nothing in change mode (which is screen 36). orion2re f838c754,
`doc/ext_research_screens.patch`, open fix 24, required by
`tools/version_check.py`; `core/screen_names.py` carries both ids with no HD
screen, so decision 22 takes over.

**Live** (new game on the stock-race path, the game restarted for it;
evidence `~/orionlayer-fixtures/evidence/work_order_129/`):
- the science room reports **52** and SELECT NEW RESEARCH **53**; in both,
  OrionLayer draws the original picture (`use_original`), has no active
  screen, and sends nothing — a click and a motion into its window reached no
  HD screen (`B_occasion2c_*`, `B_newgame2/005_DIALOG_52_native.png`);
- after the choice HD returns to the galaxy map by itself;
- **the choice itself is NOT reliable through OrionLayer, and is reported
  rather than worked around.** Three occasions: (1) a click on the row at
  native (176,85)-(394,99) through F12's original mode selected field 55;
  (2) a click on (176,51)-(394,84) the same way selected NOTHING — the list
  closed with `current_research_field` still 0; (3) the same row with a real
  `INJECT_CLICK` selected field 78. The reason is in the reading: the commit
  takes the entry under the POINTER (`Get_Selected_Entry_`, tech.cpp:354-369),
  never the activated field. **And a click in the fallback view does not even
  reach the game today:** `App._handle_click` forwards to the original view
  only in render_mode "original" (main.py:217-225), which is F12's mode, not
  the dispatcher's fallback — so with the dialogs up a click in OrionLayer's
  window does nothing at all. Both are for Data; option (c) of the reading is
  not authorised here.
- **Seen on the way:** the colony-base planet picker (the dialog work order
  122 scrapped a base in) also reports screen 0, and its CLOSE field means
  "scrap the base" — the confirmation appeared and the driver refused to
  answer it (129 A's guard doing its job).

**Smoke:** while the state reports 52 or 53 nothing is claimed and no HD
screen sends — with the map decoupled and zoomed in as a positive control.
**203 -> 204** with part D's check.

### The research foundations — work order 129 C, 17 September 2026

Built from the reading the status document already held ("Galaxy map: the
research readout's source", 124 G), so the sidebar can print what the
original prints (129 D).

- **`core/research.py`**, TRANSCRIBED: `FIELD_COST` (the cost column of
  `TECHDATA::_technology_fields`, techdata.cpp:319ff), `cost()`
  (`COLCALC::Player_Research_Cost_`, colcalc.cpp:526-539, with the
  hyper-advanced surcharge), `chance()`
  (`Chance_For_Research_Breakthrough_Aux_`, :469-484) and
  `turns_until_complete()` (`Player_N_Turns_Until_Research_Complete_`,
  :432-458).
- **A checker, not a reminder** (decision 36): `tools/research_cost_check.py`
  reads the 83 costs, `TECH_FIELD_COUNT`, the surcharge's first field and its
  step out of the source and fails on any difference; it locates the cost
  column by `s_tech_field_data`'s own member order (techdata.h:73-81). The
  smoke test runs it.
- **The player fields, decision 23.** `tech_fields[83]` @296 is now in the
  verified spec: orion2re's headers compiled with their own packing put it
  there with `sizeof(s_player) == 0xf0e` (the assert in sizes.h:21), and the
  live read agrees — 0..3 across the array, the researched field at 2, which
  is what makes the loop reproduce the original's own figure.
  `hyper_advanced_tech` @640 stays in `core/structs/unverified.py`: the live
  read is eight zeros, and a zero confirms no offset. **Consequence, on
  record:** for fields 75..82 the turn count is an underestimate until a game
  that has reached hyper-advanced research can be read.
- **Validation, three points and the loop's own arithmetic.** SAVE4 (3509.0):
  field 60, status 2, 412 RP at 44 per turn, cost 900 from the table, the loop
  gives **18** and the native sidebar reads "~18 turns / 44 RP". SAVE5
  (3509.1): 456 RP, **17**, and the native frame reads "~17 turns"
  (`evidence/work_order_129/C_native_SAVE4_research.png`, `C_native_SAVE5_*`,
  `C_probe_SAVE4.json`, `C_probe_SAVE5.json`). The two points the status
  document already carried (412/44/18 and 500/44/16) are reproduced by the
  same code. **A point with the chance above zero was not reached:** it needs
  accumulated points past the cost, which neither scratch save is near, and
  126's rule 8 keeps those saves reloaded rather than played.

### The sidebar's research readout, as the original prints it — work order 129 D, 17 September 2026

HD printed accumulated RP over produced RP; the original prints the chance
for THIS turn as "N%" where it is above zero, then "~N turns", then the
produced points — and "0 RP" when research stands still
(`MAINSCR::Print_Main_Screen_Data_`, mainscr_main.cpp:186-247). The
difference was seen twice on 16 September, deliberately left, described here
and **not marked in the code**, while `sidebar.py`'s docstring claimed to
mirror the original. With 129 C in place it is simply removed rather than
marked: `sidebar.research_readout` is the four cases, through
`core/research.py`.

- Wording comes from the game's own strings where the extractor has them
  (H 0x183 "Breakthrough", 0x188 "none", 0xE1/0xE2 "%d turn(s)"), with the
  JSON label as the fallback (decision 15); the "~" is the "@" the original
  prints, which its sidebar font draws as a tilde. Numbers stay in the
  proportional font, as the module already required.
- The row now carries up to three lines. `draw_text_block` takes a sequence,
  and where the band cannot hold the block the VALUE lines shrink — the label
  is never pushed out — measured by rendering (decision 30's consequence).
- Both docstrings that described the old behaviour are corrected: the
  module's row table and `core/structs/player.py`'s note.
- **Evidence:** HD beside the native frame at 1920x1080, 2560x1440 and
  3840x2160, for a running project (SAVE4's live values: "~18 turns" over
  "44 RP") and for Breakthrough —
  `evidence/work_order_129/D_sidebar_*_vs_native.png`.
- **Smoke:** the four cases on constructed records, including the two
  measured points, and the three-line row rendered at four sizes with its ink
  inside the row's box. **204 -> 205** with part C's checker.

### The eta label under the star sprite — work order 129, an observation (no change)

Data's screenshot showed white text under the star sprite at the destination
end of a selected fleet's course line. **Where the original puts it:**
`SHIPS::Print_Eta_On_Ship_Icon_(node, zoom, ship_x, ship_y)`
(ships.cpp:470-473) — at the SHIP ICON, not at the star; in the native frame
of this session's own run the digits sit clear of Zin, up and left of the
sprite (`evidence/work_order_129/F_eta_native_zoom.png`, from
`work_order_128/A_HEAD/00_start.png`). **Where HD puts it:**
`mapeta.anchor_point` (screens/galaxy_map/mapeta.py:114-127) anchors on the
same icon, plus the owner's header dimension. So the RULE is the same and the
difference is what is drawn around it: HD's star sprites are far larger
relative to the map than the original's handful of pixels, and `render_stars`
runs AFTER `mapeta.render` in `_render_map`, so a ship standing next to its
destination has its label covered. Reported only, as the order asks; a change
would be either the draw order or an offset away from the star, and both are
Data's.

### The fallback view is a view — work order 130 A, 18 September 2026

Decision 22 ("Graceful fallback.") promises the game stays playable on a
screen HD does not know. **It was not kept, and by more than work order
129 reported.** `dispatcher.use_original` was SET by the dispatcher and
READ by nothing in the product: the window filled with a flat (6, 8, 16)
and swallowed every click. 129's Stop 1 §5 and work order 130 both say
"shows the original picture"; the tree showed the fill colour, which is
what measuring it rather than reading it turned up.

With ids 52 and 53 on the wire since open fix 24, that made every
turn-start research a dead end inside OrionLayer's window: nothing to see
and nothing to answer.

`App._showing_original` is now the one question the renderer and the
click handler both ask, so there is no second click path (decision 9).
The only difference between F12 and the fallback is the status bar, which
stays with F12 because it names the MODE and the key that leaves it —
Data chose the plain forwarding fallback over the one with a visible hint
(129 parked point 1, option a over option c). `OriginalView.placement` is
the one home for where the picture lands; drawing and clicking each
carried the same four lines of arithmetic, and this is the order that made
them load-bearing for every screen HD does not claim (decision 5).

This relies on the COORDINATE half of open fix 3, which converts the
client's 640x480 point back to window space. `tools/version_check.py` did
not require it; it does now. Without it a forwarded click lands at roughly
a third of its intended distance from the top left, on a plausible wrong
field, silently.

### An activated research row is the chosen row — work order 130 B (open fix 25 applied)

orion2re **e9d07528** on `orionlayer-local`, bundle
`~/orion2re_bundle_18sep_e9d07528.bundle`, patch
`doc/ext_tech_activate.patch`, required by `tools/version_check.py`.

`TECH::_Tech_Select_`'s commit branch never used the field id it was
handed: `Get_Selected_Entry_` returns whichever entry carries
`current_app_index != 0`, and only `Draw_Tech_Select_` sets that, from
`fields::Scan_Input_()` — the game POINTER. An `ACTIVATE_FIELD` moves no
pointer, so a client's choice committed whatever the cursor rested on, or
nothing at all and then dereferenced the null (open fix 23's SIGSEGV).
Work order 129 B measured all three outcomes on three occasions.

`ext::g_activated_input` carries the field id of the input `Get_Input_`
is returning when it came from an activation, and 0 for every mouse
input. The commit branch, for an activation only, selects that field
before asking which entry is selected; an entry BLOCK resolves to that
entry's last visible row, exactly as `Draw_Tech_Select_` resolves it for
the pointer; and a null selection continues the input loop instead of
being dereferenced. The mouse path is unchanged — the flag is 0 for it,
and for a real click the selection would already be the same. Option (c)
of `doc/tech_change_reading.md` §5.1, the only orion2re change in this
order.

### The offered research rows reconstruct — work order 130 C

`doc/research_screen_stop1.md` §1 found the categories and the offered
field reconstructible and the choice ROWS not, for two named reasons.
Both are addressed.

`s_tech_field_data.tech[4]` is all zeros in techdata.cpp because it is
not a table: it is filled at runtime (techinit.cpp:444-474) by walking
the applications in ascending id and dropping each into the first free
slot of its own field. `core/researchlist.py` transcribes the app -> field
column and runs the same loop.

`tech_applications[212]` @379 now has decision 23's FIRST source —
orion2re's headers compiled with their own packing, `sizeof(s_player) ==
0xf0e`. **The SECOND is not in** and it is the one that matters: a live
read whose values agree with the rows the game's own screen draws. It
therefore sits in `core/structs/unverified.py`, and the screen falls back
rather than draw a list it cannot vouch for.

`validate_against_fields` is decision 25's validation and is not a test:
the screen runs it on every entry. `tools/research_cost_check.py` reads
all four transcribed tables out of the source and fails on any
difference — one row of `_technology_applications` writes its field as
`TECH_FIELD_INVALID` rather than -1, and a parser that only takes digits
reads 211 rows and lines every later application up against the wrong
field.

`tools/struct_header_check.py` is new: decision 23's header route made
mechanical for every covered spec — 133 offsets over seven structs, each
size against `sizes.h`, with a control that moves one offset by a byte
and requires the compile to fail. **`core/structs/ship.py` is NOT
covered** and says so: it names `s_ship_data`'s members itself, and the
rename map that would cover it is work nobody has done.

`core/livefields.py` is the one home for reading a live field by its
shape. The research screen is its third caller, and a screen importing
another screen's module to get at a shared rule is how the rule gets
copied instead.

### The research names come from the player's files — work order 130 D

A THIRD output of `tools/techname_extract.py` (`techfields_<lang>.json`,
`core/technames.py`): the field and application names are the first two
tables of the block it already walks to reach the buildings. And
`tools/billtext_extract.py` is new (`billtext_<lang>.json`,
`core/billtext.py`) for the panel's own wording. BILLTEXT is not shaped
like the other string files: a message is its own six LBX entries, one
per language (`Get_Text_Message_`, jim.cpp:336-359).

`core/technames.py` refuses to name fields 75..82 from that block. The
block DOES carry a string at 75, "Biology" in the English file, and
`Technology_Fields_Name_` does not use it — those eight are
`_hyper_field_title` out of ESTRINGS. Returning the block's string would
be a plausible wrong name.

Both files are gitignored, both are reported by `tools/setup.py`, and
absent, stale and short are three stated states. Read off the English
files, which is also the cross-check on the whole reconstruction: field
21 "Capsule Construction" offers Battle Pods, Survival Pods and Troop
Pods, and message 64 + group names the eight panels BASIC .. OTHER.

### The research select screen — work order 130 E, wire id 53

`screens/research_select/`, structure only. Frame and artwork come later
(Data, 17 September).

**The layout is the original's rectangles**, and the provenance is not on
a box: `Box.to_dict` serializes a fixed key set, so a `native` key would
be dropped the first time the F5 editor saved this screen — decision 38's
trap for `help_id`, and why `colony_summary`'s `boxes.json` carries no
rect either. `boxes.json` names the boxes, `native.py` holds every
rectangle with its tech.cpp line, and `seat()` marks them derived. The
eight entry boxes ARE the game's own entry-block fields.

**One rectangle for drawing and clicking** (decision 5), and because a
shared function guarantees agreement and not correctness, the check
renders and requires every row's VISIBLE CENTRE to pick that row, as work
order 128 D did for the Planets list.

**It refuses before it sends and before it draws.** A click off a row
sends nothing (decision 33); a row resolves by SHAPE in the list of that
frame; a second click after the commit sends nothing; ESC and every other
key send nothing, because select mode has no exit but a commit
(tech.cpp:131) and `ScreenBase.handle_key` would otherwise have forwarded
them.

**`ScreenBase.wants_original`** is decision 22 one step in: a screen that
knows the id but cannot vouch for its own picture hands back to the
original view. Five states do it — no player record, names absent,
wording absent, a field list of the wrong shape, a reconstruction the
list contradicts — and each logs once, not per frame.

**Marked**, each held by a check: four OMISSIONS (the science room
animation, the category list popup, the description box a right click
would open — so a right click inside the panel does nothing — and the
little arrow), one HD EXTENSION (the title, which the original paints
into TECHSEL art), three DEVIATIONS (the category label printed rather
than painted, the RP suffix that ignores `_settings.language`, and
shrinking where `Squeeze_Print_` compresses).

Help 254's three rectangles are transcribed from billhelp.cpp:42-46.
They are NOT "outside the panel" — they lie over the fill's own top and
bottom edges, which is how `doc/tech_change_reading.md` §7 derives the
panel's visible edge. The rule that holds is narrower: no help region may
cover an entry block or a radio, because a right click there is the
description box or the category list, not help.

### The live acceptance of work order 130 — 18 September 2026

A new Psilon game against orion2re **e9d07528** (`orionlayer-local`,
open fixes 24 and 25 applied, rebuilt and the binary checked for
`ext::g_activated_input`). One client throughout; SAVE1-9 and SAVE11
identical before and after, SAVE10 rewritten by the game's own autosaves
and logged only. The driver is `tools/research_hd.py` on
`tools/livedrive.py` and `tools/researchphases.py`.

**The fallback is a view, live.** Every screen HD has no version of drew
the game's own picture in OrionLayer's window and forwarded clicks: the
science room (52), the colony build prompt (1), the end-of-turn report
(39), the GNN broadcast and the leader offers. The record carries the
number of distinct colours beside every capture, which is the check the
129 report did not make.

**The choice means the row.** Two occasions, two categories, and the
game's pointer was never moved by this run — so a pointer standing still
cannot explain two different rows both landing correctly. Open fix 25
is what makes that true; before it, work order 129 measured a selected
field, no selection, and a different field on three occasions.

**And the list does not always wait — open fix 26.** Three times the
select list committed a row BY ITSELF about a second and a half after
the science room handed over, with a send counter proving the client
sent nothing. It is why choosing has to happen in the same process that
walks the room out, and why the HD screen re-reads rather than
remembers.

**One live number for the cost table**: field 62 read 540 accumulated of
650 at 15 RP a turn, and `core.research.cost(62)` is 650.


### Galaxy map: frame v3, holes cut from measured geometry — work order 133, 18 September 2026

`screens/galaxy_map/assets/frame.png` is now built from Data's render of
18 September, `~/orionlayer-fixtures/incoming/galaxy_frame_18sep/ChatGPT
Image Sep 18, 2026, 10_29_27 PM.png` (sha256 `ecf4a687…`). The built
master is `galaxy_map_frame_v3.png` (sha256 `1b93c052…`), **1707x921 —
the render's own size, not resampled**. v2's 1706x922 master stays in
git.

**THE RENDER HAD NO ALPHA AND NO CHECKERBOARD.** Mode RGB, 100 % opaque,
openings painted solid black. `key_frames.py`, which keys BRIGHT
near-neutral regions, returns 0 holes on it. Keying on darkness is no
better as a rule: 58 % of the image is exactly (0,0,0) and that black is
in the metal's own shadows as much as in the openings.

**So the holes are cut from geometry.** Every edge is a half-way
luminance crossing between a hole's own floor and the metal beside it,
measured per scan line, then cut with a 1 px anti-aliased edge —
`cut_holes_from_geometry.py`, kept beside the source. An edge whose scan
lines agree is cut straight from their median; one that genuinely moves
keeps its profile, which is why the title plate's chamfered ends survive
as a hexagon and the nine rectangles are rectangles.

**Why it matters, in one number.** A threshold key put the six nav slots
17 px apart in height and made them swing to 26 px apart as the
threshold moved. The drawing has them **0.42 px apart**; the spread was
the key, not the artwork. Cut from geometry, `tools/frame_holes.py`
reads them at **spread 0 px in both height and top edge**. Every hole
edge is within **0.94 px** of the drawing edge it follows.

Metal opacity 29.2 %, anti-aliased edge 0.6 % of the image, RGB under
alpha 0 set to black.

**The cutouts, regenerated** with `tools/frame_holes.py --write`, which
kept **22 non-cutout boxes** at each of the two resolutions:

  | box | v2 ref | v3 ref |
  |---|---|---|
  | map_area | 90, 66, 1422, 885 | 89, 64, 1410, 844 |
  | sidebar | 1567, 88, 244, 851 | 1555, 93, 251, 805 |
  | nav_turn | 1595, 982, 202, 53 | 1578, 940, 213, 61 |
  | nav_colonies | 104, 970, 213, 50 | 109, 930, 209, 47 |
  | nav_planets | 345, 970, 214, 50 | 348, 930, 209, 47 |
  | nav_fleets | 585, 970, 214, 50 | 586, 930, 208, 47 |
  | nav_leaders | 827, 970, 216, 50 | 824, 930, 209, 47 |
  | nav_races | 1072, 970, 218, 50 | 1062, 930, 209, 47 |
  | nav_info | 1326, 970, 213, 50 | 1304, 930, 215, 47 |

**Two groups of hand-placed boxes had to follow the frame**, because the
openings are smaller: the sidebar is 46 ref px shorter and the map area
41. Moving only the research readout was impossible — 101 px of room
remained for a 121 px row, so it would have overlapped the freighters
row — so each group is reseated by the same affine as its own cutout:
the eleven `sb_*` readouts by the sidebar's, the `system_*` and
`fleet_*` popups by the map's. Every hand-placed box now lies inside its
cutout at both resolutions, measured.

`layout.json` `frame.image_size` and `frame.title_rect` follow the new
master, and the existing check that boxes.json equals what
`frame_holes` derives from the PNG holds them together.

Checked at all four resolutions: the nav labels and TURN put **0 ink
outside their holes** (found by the label's own blue tint, since the
frame's metal is neutral). Renders in
`~/orionlayer-fixtures/evidence/work_order_133/`.


### Fleets: the outer ring, a frame variant of the Planets artwork — work order 134 A, 18 September 2026

Work order 134 built the Fleets screen's frame from the Planets artwork,
Data's decision after 134's check: **the Planets frame does not fit
Fleets as a whole, so only the outer ring is taken** and the Fleets
regions are drawn inside it by the screen.

`screens/fleets/assets/frame.png` (sha256 `149750cd…`), 1920x1080, is
`screens/planets/assets/frame.png` with the inner struts removed —
decision 12's frame variant, one artwork, no runtime tile swapping.
Source and cutting script in
`~/orionlayer-fixtures/incoming/fleets_frame/`.

**Ring and strut are told apart by THICKNESS, not by a threshold on
colour** (the galaxy v3 rule, one step on): the ring is about 74 px
thick and the widest strut 29, so a morphological opening with a disc of
radius 18 keeps the one and drops the other. What is left of the opening
boundary is then the ring's OWN anti-aliased edge, never re-cut.

**Exactly one opening remains**: image (74, 75, 1771, 917), reference
(72, 73, 1775, 921), aspect 1.927. It is precisely the union of the five
Planets openings.

**Five joint remnants were removed and NOTHING was painted.** The struts
met the ring through small arrow-shaped nodes that survive a
thickness test because they are locally thick. Each was removed with its
own fringe, and the ring behind each was then MEASURED rather than
assumed:

| spot (image px) | nearest edge | ring thickness there | 60 px along | verdict |
|---|---|---|---|---|
| x 1456..1475, y 79..82 | top | 79 | 77 | continuous |
| x 1448..1482, y 796..830 | — | — | — | island in the opening, no ring to break |
| x 1842..1844, y 804..821 | right | 75 | 75 | continuous |
| x 1456..1474, y 984..987 | bottom | 92 | 88 | continuous |
| x 596..613, y 988..990 | bottom | 89 | 88 | continuous |

The ring is 2 to 4 px THICKER where a joint sat, which is what says the
joint lay on top of intact ring: removing it leaves the band unbroken
and no fill was needed.

**The opening holds the Fleets union at every resolution.** The union of
the regions in `doc/fleet_screen_reading.md` §7 is native (13,52)-(628,465),
616x414, aspect 1.488 against the opening's 1.927 — so the fit is
height-bound and the spare room is horizontal:

| resolution | opening, window px | union at scale | margin l/r, t/b |
|---|---|---|---|
| 1920x1080 | 72, 73, 1775, 921 | x2.225 | 202.3 / 0.0 |
| 2560x1440 | 96, 97, 2366, 1228 | x2.966 | 269.4 / 0.0 |
| 3440x1440 | 536, 97, 2366, 1228 | x2.966 | 269.4 / 0.0 |
| 3840x2160 | 144, 146, 3550, 1842 | x4.449 | 404.6 / 0.0 |

The inset map keeps 305:182 = 1.676 by construction: one factor scales
both axes. **The vertical margin is zero**, so the layout insets the
content itself rather than letting it touch the ring.

**Decision 3 does not apply to this screen.** It derives no cutouts —
there is one opening and the regions inside it are hand-placed,
F5-editable boxes — so `tools/frame_holes.py` gets no naming rule for
`fleets` and `--write` is never run on it.


### Fleets: built in one run, NOT ACCEPTED — work order 134, 19 September 2026

`screens/fleets/` is orion2re's `SCREEN_FLEET` (4),
`FLT1::Fleet_Screen_` (flt1.cpp:486-837). **HD STATE: built, NOT
accepted.** Nothing has driven it live — `:0` is unreachable from the
session that built it — and the same sentence stands in the module
docstring, in `layout.json`, in the parked file and in a smoke check.

**The frame** is `screens/planets/assets/frame.png` with its inner
struts removed (decision 12's variant; its own section above). One
opening, reference (72, 73, 1775, 921).

**The seat is one factor for both axes, and that is not a preference.**
`fltgeom` holds every native rectangle with its engine line and puts the
union (13, 52, 616, 414) into the opening less the 2 px bleed at
x2.214976, centred — height-bound, so the spare room is 203 reference px
each side. One factor is what keeps the inset map at 305:182, and
`Box_Fleet_Screen_Scanned_Star_` hardcodes 1659 and 2197, which are
506000/305 and 400000/182 (movebox.cpp:193-199): a map box of another
shape puts the star boxes off the stars.

**Sixteen F5-editable boxes**, seeded once by `tools/fleet_boxes.py`.
Decision 3 does NOT apply — the frame has one hole and nothing inside it
is a cutout — so `tools/frame_holes.py` has no `fleets` rule and
`--write` is never run on it.

**Decision 34, answered: all sixteen wear `thin_border`**, because all
sixteen GROUP. `inner_panel` frames pictures, and the one picture on
this screen is the captain's portrait, which is deliberately not a box:
its extent is `animate::Get_Width_/Get_Height_` of LBX art at runtime
(flt2.cpp:848-866), not a constant, so a box would have to invent a
size.

**THE CONTENT CANNOT BE RECONSTRUCTED, and that was established before a
patch was asked for** (decision 25). Three routes, each to the line that
closes it: FSEL sends only the fleet box's chain and that is -1 here
(flt1.cpp:826-832); walking the node table names undetected ships
(shipstak.cpp:200-250, :5-11); grouping by location gives a different
list in membership and order and cannot say so. So **open fix 27** (a
read block) and **open fix 28** (the smallest necessary write), both
applied to `orionlayer-local`, both required by
`tools/version_check.py`, **neither confirmed live**.

`MSG_SELECT_SHIP` was checked before anything new was designed and does
not cover this screen on TWO independent counts: it refuses without the
galaxy map's fleet box, and it writes an array this screen never reads
(flt1.cpp:429). So open fix 28 is a second handler behind the same
message id, branching on the screen.

**The read carries its own validation**, which is the half a read block
usually skips: `Add_Fltscrn_Big_Icon_Fields_` adds one hidden field per
displayed icon at exactly `(x, y, x+58, y+57)` (flt2.cpp:288-290,
:313-320) — the same twenty cells HD draws. The block says how many, the
field list says where, and the screen refuses if they disagree. A
FOREIGN stack adds no fields at all (flt2.cpp:312-322) and is
recognised, not refused.

**The fallback is loud and has four named refusals**, not one:
`NO_BLOCK`, `NO_STACK`, `NO_FIELDS`, `MISMATCH` — each with a sentence,
each sending nothing, each on a real snapshot in the smoke test.

**Four OMISSIONs, each for its own reason**, each marked where it is
performed and each held by a check: the ship's picture (SHIPS.LBX is
MOO2's art), the damage bar (offsets 123/125 are hand counts the ship
spec refuses to carry, and the bar's geometry is unsettled), the move
preview (hover-computed, on no wire), the captain's portrait
(`s_leader_data` unverified). Plus F5/Alt-F5, which `INJECT_KEY` cannot
express at all.

**One HD EXTENSION: the wheel** — and it is not a local scroll. The list
window is the game's (decision 46), so the wheel activates the same
arrow field a click would, and only above twenty icons, where the
original has arrows at all.

**No fundament entry was filed.** Every rule this screen follows was
already there (3, 5, 12, 20, 22, 25, 33, 34, 42, 46, 55, 61, 69), and
the order says to file one only for a decision that is actually new.

Renders at 1080p, 1440p, ultrawide and 2160p in
`~/orionlayer-fixtures/evidence/work_order_134/`. What is parked, and
the six decisions still open, are in `doc/briefs/134-parked-for-data.md`.

## What is missing

### The Fleets ship panel: two things the original prints and HD does not

**20 September 2026, work order 152 item 7.** Both are marked in
`screens/fleets/layout.json` under `marks` and held by a smoke
assertion; they are listed here because a marking in one screen's data
is not a list anybody reads when planning the next piece of work.

**1. The weapon name is always the singular.** The original prints
`TECHDATA::_weapons[t].name_plural` whenever the count is not one
(flt2.cpp:706-711), so it reads "5 Anti-Missile Rockets" where HD reads
"5 Anti-Missile Rocket". `tools/techname_extract.py` takes the record's
`name` field and not its plural one, so the catalogue in this tree has
no plural to print, and the singular stands: an invented "s" is not the
original's word either and is wrong for the first irregular one.

*What lifting it costs:* the plural field added to the extractor, a
`weapons_plural` table beside the five in `core/shipparts.py`, and a
`FORMAT_VERSION` bump — which makes every player re-run the extractor,
so it wants to travel with another change to that file rather than go
alone. `fltrows.panel_lines` already asks for the table and falls back
when it is not there, so nothing else moves.

**AFTER RELEASE.** Fleets is complete for the 22 November release (see "Fleets is done" under What works); this item is not a gap in it.


**2. A damaged special is not shown in red.** The original colours it
with `FLT2::_red_colors` when its bit is set in
`special_device_damage_flags` (flt2.cpp:724-731). That field is at @118
by the header route (orion2.h:2847-2868, the same struct run that
carries the crew fields promoted in the same order) and **it is not
verified**. The obvious live check — a damaged device must be a FITTED
one — held on all 60 ships of the acceptance save and **proved
nothing**, because not one of them had any damage. Decision 23 keeps it
out until there is a second source.

*What lifting it costs:* one live reading on a save with a damaged
ship. The check is already written and is two lines: the damaged bits
must be a subset of the fitted bits, and at least one ship must
actually carry damage or the run says so instead of passing.

**WORK ORDER 159 TRIED THE FILES AND COULD NOT GET THE COUNTS.** It
settled one half and failed the other, and both are worth having.
SETTLED: the serialised ship record IS the packed struct — `Read_Ship_`
and `Read_Ship_Design_` (savegame.cpp) read the declaration order with
no padding, so a record is 129 bytes with
`special_device_damage_flags[5]` at **@118**, which is what this entry
already said. FAILED: a save is a SERIAL stream
(`Read_Game_State_`, savegame.cpp:1419) — settings, a variable number
of colonies, planets and stars, leaders, players, then `_NUM_SHIPS`
and the array — so the ships have no fixed file offset, and 159's
scanner could not locate the array reliably. It was cross-checked
against work order 154's own officer count over the same ten saves (4
of 185) and reproduced neither number, "finding" damaged ships with
one-character names and no fitted devices. **The counts are therefore
not reported**, because a number that is not measuring what it names
is worse than the check 154 said proved nothing.

*What would settle it, cheapest first:* one save where Data knows a
ship has special damage, and which one; or a reader that walks
`Read_Game_State_` as far as the ship array, which is a tool and a
decision rather than cleanup; or the live reading above. Filed with
the scanner at
`~/orionlayer-fixtures/evidence/work_order_159/part3/`.

**AFTER RELEASE.** Fleets is complete for the 22 November release (see "Fleets is done" under What works); this item is not a gap in it.


### The Fleets ship panel: two more, from work order 154

**20 September 2026.** Both are marked in
`screens/fleets/layout.json`, both are held by a smoke assertion, and
both are here for the same reason the two above are.

**3. Beam OCV and Beam DCV are not printed at all.** The original
prints them between the shield line and the destination line — H 0x99
at x 0x12 with its value right-aligned ending at 0x85, H 0x9A at
x 0xAD with its value at 0x73 + 0xAD, one line (flt2.cpp:606-622). HD
drew the two labels with nothing after them for the length of work
order 154 and **Data said no to that on 20 September 2026**: no empty
labels on the player's screen. So the line is gone, HD's head block is
four slots where the original's is five, and the grid is deliberately
one line shorter.

*Why the numbers cannot be had.* `INITSHIP::Get_Ship_Combat_Bonuses_`
(initship.cpp:638-687) is

    Get_Design_Combat_Bonuses_(design)
      + Helmsman_Bonus_ / Weaponry_Bonus_ of ship->officer_index
      + MOX::_crew_data[crew_quality].attack / .defense
      + player.traits[TRAIT_SHIP_ATTACK / TRAIT_SHIP_DEFENSE]
      + (strategic combat) Best_Warp_Drive_ and
        _hull_data[size].strat_def_bonus
      + (trans-dimensional) COMBAT1::_td_combat_speed_bonus * 5

`officer_index` is in HD's ship spec; the two bonuses it feeds read
`special_skills` and `xp` out of `s_leader_data`, which
`core/structs/unverified.py` refuses (decision 23). The traits and the
strategic-combat flag are already decoded.

*What lifting it costs — MEASURED, 20 September 2026, not estimated.*
The attempt is written up at `core/structs/unverified.py`'s `LEADER`
entry; the short version:

* **The static tables are not the problem.** `_crew_data`
  (mox.cpp:780), `_computers[].bonus` and `_hull_data`
  (techdata.cpp:429, :77) are plain literals in the source, and
  `Get_Officer_Base_Level_` (officer.cpp:44-61) is a five-line step
  function. All of it is transcription.
* **The leader record's layout is corroborated but not verified.**
  Two sources agree on it — orion2re's header with the `0x3b` size
  assert, and a live reading of all 67 records where `name`, `title`,
  `type`, `special_skills` and `player_index` agree semantically and
  **`xp` agrees numerically**: the only values present are 0, 60,
  150, 300 and 1000, which are exactly
  `Get_Officer_Base_Level_`'s own thresholds. Seven other fields have
  no ground truth in that reading, and `level` is 0 in all 67.
* **THE OFFICER PATH IS VACUOUS AND THAT IS THE REAL BLOCKER.** The
  panel reaches the leader record only through
  `s_ship_data.officer_index`. The loaded save has 0 of 21 ships with
  an officer; across all ten saves on this disk — read from the
  files, nothing loaded — only SAVE1, SAVE3, SAVE4 and SAVE5 have one
  at all, one each: **4 ships of 185**. That is the shape of the
  damaged-special check above, which held on 60 ships and proved
  nothing.
* **And the ground truth itself is out of reach.** Checking a
  computed bonus means comparing it with the number the game prints,
  and the game prints that panel only for `_scanned_big_ship`, which
  it sets from its OWN cursor — the Extension API has no mouse motion
  (open fixes 3 and 4), which is the same gap work order 153 B worked
  around for HD's side. An INJECT_CLICK would set it, at the cost of
  toggling that ship's selection, and would give one data point on
  one ship.

*So the order is:* a save with several officered ships first, then a
way to read the original's own panel for one of them, then the
transcription. **A partial answer is worse than none here**: a panel
that prints a number for a ship with no captain and nothing for one
with a captain would look like a bug rather than a gap.

**AFTER RELEASE.** Fleets is complete for the 22 November release (see "Fleets is done" under What works); this item is not a gap in it.


**4. A colony, transport or outpost ship gets a different panel
entirely — BUILT, 21 September 2026, work order 159.** Moved to "What
works" below; this entry is kept as the record of what it was, because
the open list is where the next session looks and a silent
disappearance reads as a forgotten item.

### The Fleets ship panel: two more, from work order 155

**20 September 2026, Data's decisions on the strip under the map.**

**5. The strip is silent in eight of its ten states.** HD draws the
two the original reaches with no ships selected — the star's name,
and H 0x94 for a star the player knows nothing of. The other eight
are the MOVE PREVIEW: H 0x67 "Orbiting %s", H 0x69/0x6A "%d turn(s)
to %s", H 0x6B/0x6C "ETA %d turn(s)", H 0x21 a black hole in the way,
H 0x6E immobile, H 0x6F/0x70 "%d parsecs to %s", H 0xEB, H 0x73
hyperspace flux (flt2.cpp:394-500).

**Data's decision, 20 September 2026: the strip stays as built** —
with ships selected the original is answering a different question
and HD should too, rather than printing a name that answers neither.
So this is a PARITY item, not a bug, and it is here rather than in
any order.

*What lifting it costs:* `SHIPMOVE::Ships_Try_To_Move_To_` transcribed
and `_g_ship_move_info` on the wire — the same field work order 144
put to the C++ side, and the same one the galaxy map's own move
preview needs. **It is one piece of work for both screens**, which is
the argument for doing it once and deliberately rather than per
screen — and that note is the reason this one does not simply move to
the Fleets list and get forgotten there.

**AFTER RELEASE.** Fleets is complete for the 22 November release (see "Fleets is done" under What works); this item is not a gap in it.


**6. PREV and NEXT wear words where the original draws arrows.** The
original's two buttons beside the strip are FLEET.LBX arrow glyphs
with no string at all. HD drew nothing, so for two work orders they
were live, clickable and invisible; since 20 September 2026 they say
"Prev" and "Next", which is what this screen already does for the
seven other controls the original also has no string for.

*What lifting it costs:* the two arrows extracted the way
`tools/fleet_art_extract.py` already extracts the rest of this
screen's artwork, and `draw_labels` preferring the sprite over the
word where it has one — exactly the shape the grid cells took in work
order 142 D1, including the fallback for a clone that has not
extracted anything. **The words are not a stopgap to be ashamed of**:
they are the same answer decision 15 gives everywhere else here, and
the artwork replaces them only if it looks better.

A rule holds both halves now: every name in `fltwire.HOTKEYS` that is
also a cutout must be in `fltdraw.CONTROL_WORDS` with a non-empty
word, so a clickable control cannot go unmarked again.

**AFTER RELEASE.** Fleets is complete for the 22 November release (see "Fleets is done" under What works); this item is not a gap in it.


### `font_scale` and `font_size` are two mechanisms — PARKED

**20 September 2026, work order 151 B. Data parked the unification;
the dead keys it turned up are removed.**

A box can carry two font keys and only one of them reaches most
skins:

* **`font_size`** is a reference size and `Box.render` scales it once
  through `Layout.font_size` — `style.get("font_size", 16)`,
  `core/box.py:101`. Every `text`, `button`, `area` and labelled
  `panel` box in the tree is sized this way; there are 60 of them.
* **`font_scale`** is what the F5 editor's Ctrl+Wheel writes
  (`core/editor/editor.py:308-314`), and `Box.render` never reads it.
  It works only where a SCREEN reads it for itself: the colony
  summary's `planet_paragraph` and sidebar, Custom Race, Empire
  Identity, Select Race — and, since this order,
  `fleets.ship_panel_text`, which reads both.

**So a `text` box is not font-editable in F5 at all**, which is
exactly what decision 37 says it should be: *"position, size, font
size and alignment come from boxes.json, so a bare label is
F5-draggable like everything else"*. The wheel turns and nothing
happens.

**What was removed, and what was not.** `fleets.inset_hint` and
`fleets.status_hint` carried `"font_scale": 0.8` on a `text` skin.
Nothing has ever read it — both have always rendered at the default
16 — so it was a number that looked like a setting, and it is gone
from both resolution sets. **Nothing moved on screen**, which is the
point: removing it is not a change of behaviour, it is the deletion of
a value that never had any.

**What the fix would be, and why it is not done here.** One line in
`Box.render`: `style.get("font_size", 16) * style.get("font_scale",
1.0)`. Measured across the tree, 33 boxes carry a `font_scale` that a
core skin would then start reading. Thirty of them carry 1.0 and would
not move. The one that would is the colony summary's
`planet_paragraph` — `font_scale: 1.6`, **in the 2560x1440 set only**
— and that one IS read, by `colonyoutput`, which already applies it
once and correctly (brief 97). Composing it in `Box.render` as well
would apply it twice, at one resolution and not the other. So the
unification needs `planet_paragraph` resolved first, and a check that
no box carries a key its skin ignores; it is a change to shared
machinery and it belongs in its own order, not in the tail of a
screen's.

### Research select — BUILT, NOT ACCEPTED

`screens/research_select/` (wire id 53) is built, committed and green,
and its live acceptance is **not complete**. It is listed here rather
than under "What works" until it is: a screen that has been seen
working twice is not a screen that has been accepted.

**What IS proven live** (18 September 2026, evidence in
`~/orionlayer-fixtures/evidence/work_order_130/`, index `EVIDENCE.md`):
part A twice — on wire id 52 the window shows the game's own picture and
a click in it advances the science room, no F12; part B twice, on two
rows in two categories — an HD row click gave field 4 and a bare
`ACTIVATE_FIELD` gave field 22, each the row's own field, read back off
the wire.

**The open points, all six:**

1. **The list chooses by itself — open fix 26, OPEN and deferred.**
   `SELECT NEW RESEARCH` commits a row about a second and a half after
   the science room hands over, with a send counter proving the client
   sent nothing. Data's counter-test of 19 September 2026 — same binary
   (e9d07528), NO client connected, the dialog clicked away with the
   real mouse — shows the list WAITS. So open fix 25 is not the cause.
   Still suspect, and not separated from each other: the completion
   dialog dismissed by INJECTED clicks, and a connected client as such.
   Deferred by Data.
2. **The third research choice.** The order asks for three occasions in
   three categories; two are done (categories 4 and 6). Two further
   attempts lost the occasion to point 1, and a third could not be run
   — the machine's display server stopped accepting new clients
   (`SDL_Init(SDL_INIT_VIDEO) failed: The video driver did not add any
   displays`), so orion2re could not be restarted.
3. **Two missing resolutions.** HD beside the native frame exists at
   1920x1080 only; the order asks for three.
4. **The crash case from work order 128.** An activation where nothing
   is selectable — the entry block of a category with nothing left to
   offer. No list reached in the run had an empty category, so it was
   never exercised. `python tools/research_hd.py crash` runs it when one
   comes up.
5. **`tech_applications` @379 is still in `unverified.py`.** Decision
   23's SECOND source did arrive on 18 September: the rows the HD screen
   reconstructed FROM that offset matched the game's own panel exactly,
   name for name and count for count, and `validate_against_fields`
   passed against the live FIELD_LIST on several different lists across
   one game. What has NOT been done is the promotion — moving it out of
   `core/structs/unverified.py` on the strength of that. Until then the
   screen keeps validating on every entry, which is the right behaviour
   either way.
6. **The six always-open fields, and creative races — never compared
   against the original.** `Display_Entry_Text_` (tech.cpp:706-716)
   treats a field as "all applications" when the player carries
   `TRAIT_CREATIVE` **or** the field is one of {22, 23, 28, 29, 55, 57},
   the six `_starting_tech_field_ids`. In SELECT mode that branch is
   unreachable for the COLOUR, because `Tech_Select_` zeroes
   `current_research_field` first (tech.cpp:104-105) and the branch sits
   inside `is_current_field` — that much is read from the source and
   written down in `panel.py`. What has NOT been checked is the
   behaviour: the one live comparison was a **Psilon** game, and Psilons
   ARE creative (`RACESTUF.LBX` entry 7, record 9, `traits[22] = 1`). An
   uncreative race has never been put beside the native panel, and
   neither have the six fields.

**The player's way round point 1, while it is open:** click the
completion dialog away in the orion2re window with the real mouse. The
research selection then waits, and the HD screen can be used for the
choice. The same sentence is in `screens/research_select/screen.py`'s
docstring and in `doc/orion2re_open_fixes.md`, and a smoke check holds
it in all three places for as long as open fix 26 says OPEN.

### OLED floor lift and player-colour presets — two HD EXTENSIONS, 14 September 2026

Brief "OLED floor lift and colour-blind palettes", Data's decisions of
the same day; fundament 63. Both are **HD EXTENSIONS** — MOO2 has no
adjustable floor and assigns its eight player colours fixed — and each
is marked in its module, here and in a smoke check.

- **`core/usersettings.py` / `user_settings.json`** — the player's own
  values, ignored by git, never shipped. Absent: defaults, silent.
  Unreadable: one error line, defaults, the file moved to `.corrupt` on
  the next save. Unknown keys written back. Not `settings.json` (the
  app's committed configuration), not `core/structs/settings.py` (the
  engine's `s_settings`).
- **Game Settings dialog, four row heights below the thirteen** (1080p
  box `orionlayer_rows` [622, 641, 513, 153], ending at 794 against
  ACCEPT at 817): a divider, the "OrionLayer" heading, **Map floor**
  (Off / Light / Haze) and **Player colours** (Original / Okabe-Ito)
  with eight swatches from the SELECTED preset. `screens/game_menu/gmorion.py`.
  No field, no hotkey, and a click on any of the four bands sends
  nothing; the thirteen engine rows keep their state from `s_settings`.
  Values apply in memory at once; the file is written on ACCEPT and on
  the overlay's exit, idempotently. **The restart note sits
  right-aligned in the HEADING band, above the swatches** — four row
  heights leave no fifth; shown only while saved != active preset.
- **Floor lift** — `screens/galaxy_map/floorlift.py`, one additive fill
  after both floor paths in `_render_map`, read at draw time (live).
  Off = no call, byte-identical map. Light (1, 2, 5) and Haze
  (4, 10, 20) are the floor graphic's median and 90th percentile.
- **Presets** — `core/playercolors.py`, applied once by
  `palette.init(preset=)`, which only `main.App` passes (after the user
  file); every other caller gets the original. All four tables swap:
  `owner_*`, `ship_*`, `owner_hover_*`, banner/banner_hd. `ship_*` and
  the banner tables were moved out of code into colors.json first, each
  checked byte for byte (32 ship tints, 24 banners).
- **The rule is a marked DEVIATION** in colors.json [player_presets]:
  owner = base, ship = base lifted by k_ship 0.07, hover = base lifted
  by k_hover 0.45, banner multiply = base with no add. Both k measured,
  with protocol: k_ship is the smallest lift that keeps every preset
  ship at least as bright as the darkest original ship (red, 0.108) at
  all four zoom steps — measured 0.0674, stored up; k_hover matches the
  original's mean hover/owner luminance ratio 1.700 (1.699 at 0.45).
- **Okabe-Ito** with black replaced by white; red -> vermilion, yellow
  -> yellow, green -> bluish green, silver -> white, blue -> blue,
  orange -> orange, brown -> reddish purple, purple -> sky blue (by
  distance, and the nearer relative for a deuteranope). Smallest
  deuteranopia distance dE 17.2 against a threshold of 10; **the
  original's is 3.8 and it is reported, not held to the threshold** —
  a deviation from the brief's "every shipped preset", because the
  original cannot meet any useful one.

### Monster values in the Planets panel — fundament 64, 14 September 2026

**Brief 107** (`doc/briefs/107-*`, decisions `108-*`, release `109-*`).
When the scanned row's star is guarded by a space monster (owners 9..14,
`planetrows.monster_ship`, the transcription of
`HAROLD::Star_Guarded_By_Monster_`), the picture window shows the
creature and its values. **HD EXTENSION, all of it except the type** —
the original shows "(Amoeba)" under the planet and nothing else outside
combat; that line is unchanged.

- **Panel** — `screens/planets/monsterpanel.py`: sprite box left, text
  boxes right, all in boxes.json at both resolutions (`monster_sprite`,
  `monster_type`, `_stage`, `_size`, `_structure`, `_armour`, `_shield`,
  `monster_weapons` with `monster_weapon_counts` beside it,
  `monster_specials`); wording as templates in layout.json
  `monster_values`, the list headings HESTRNGS 0x9D-0x9F. Numbers, no
  judgements. Nothing is sent. The old `monster_picture`/`monster_race`
  pair is gone.
- **Switch** — a fifth OrionLayer row in Game Settings, "Monster values",
  default ON (`user_settings.json` `monster_values`). The rows box grew
  one band and ACCEPT moved down by the same 38 px.
- **Values** — the design block of `s_ship_data` and the weapon records
  are VERIFIED (`core/structs/ship.py`: 48 header asserts and a live
  probe of five monsters against their templates). The damage fields are
  not declared and not read. Stage from the drive. Structure and armour
  as two lines, tactical, from `core/monsterhull.py`;
  `tools/monster_hull_check.py` holds that table to initship.cpp,
  techdata.cpp and orion2_consts.h and the smoke test runs it.
- **Names** — `tools/techname_extract.py` writes a second file,
  `shipparts_<lang>.json` (specials, armour, shields, weapons, hull
  classes; `core/shipparts.py`); without it the panel shows numbers.
- **Sprite** — the galaxy map's own master, exported once more at 314 px
  on the long edge (`zoomtables.MONSTER_PANEL_SPRITE_PX`, DERIVED for the
  4K box; `panel.png` beside the four steps). **DEVIATION**: chosen by
  type, where the original's unreachable popup picks by star index % 5.
  The Amoeba has no master and its box stays empty.
- **Reference save** — `tools/fixtures.py` now also slices the ship
  array (`fixture_ships`, reference 109 records at 82939, natives 71 at
  68828, each found live on a fresh load). Every monster of the
  reference save gives exactly its template and table values in the
  smoke test.

### Galaxy map: the right click is the game's cancel — brief 107, 14 September 2026

A right click on the map (not over a help region) sends CANCEL_FIELD on
the map's grid field, found in the live list by type 12 and rect
22,22-527,421, before the pan drag starts. TRANSCRIBED: with the mouse
cancel disabled the right button returns the grid field negative and
`Main_Screen_` ends the relocation-merge mode and leaves zoom mode —
over a star, a black hole or empty space alike, and nothing else
(layout.json `map_cancel`). Checked live on the reference save: screen
stays 0, field list unchanged.

**Also from brief 107:** `tools/maintext_extract.py` extracts the
system-special descriptions from MAINTEXT.LBX (the file per language
from estrings.cpp) into `maintext_<lang>.json`, read by
`core/maintext.py` (decision 38's pattern). Nothing draws them yet —
they belong to the galaxy map's popups, which are their own brief. The
Amoeba's map footprint is measured off BUFFER0.LBX (13 x 13), and the
same measurement disagrees with the five screenshot values
(`doc/ship_icon_measurement.md`).

### Galaxy map: fleet icons are clickable, and the boxes are read off the field list — brief 110 Part A, step 1, 15 September 2026

**Brief 110** (`doc/briefs/110-*`, decisions `111-*`, release `112-*`).
The first package of Part A, the one everything else in A depends on.

- **Icon hit test** — `screens/galaxy_map/mapclick.py`. TRANSCRIBED
  order: icon before star, star before icon while the fleet box is open
  (mainscr_main.cpp:425-438); the first icon in ARRAY order whose
  rectangle holds the pointer (`Check_Ships_XY_`, mainscr.cpp:1750). The
  rectangle is `ships.icon_box`, the one `render` draws in (decision 5).
  The click goes out at a native point inside the icon and clear of
  every earlier icon, so the game opens that stack and not the star it
  orbits. `_click_star` is gone: one click path for icon, star and empty
  space.
- **Box state** — `screens/galaxy_map/mapboxes.py`: the fleet box, the
  system window and a modal text box, read from the live FIELD_LIST (the
  box fields sit between the last sidebar window and the Q/V/grid tail,
  mainscr.cpp:1405-1427). A list it cannot read is `known = False`. Test
  data: `tools/galaxy_box_fields.json`, recorded live on the reference
  save in brief 110 Stop 1.
- **Decision 65, DEVIATION** — while the fleet box is open, no map click
  the game would resolve to a star (its own radius, `Check_Stars_XY_`) is
  sent; a black hole is exempt. **Consequence, plainly: a fleet cannot be
  moved from the HD map yet.** A click on a fleet or monster opens its
  box in the game (still invisible in HD), a click on another icon
  switches it, and the destination click is refused until HD draws the
  box and the target is chosen there — the next step of Part A.
- **Decision 66** — no CANCEL_FIELD while a box is open: it would land at
  the grid's centre, inside the box.
- **Not built yet:** HD drawing of the system window and the fleet box
  (design (a), decision A1), star identity from the last HD click (A2),
  closing through the CLOSE field.
- **Smoke:** two checks — the box state against the five recorded lists
  (and a moved box followed), and the hit test with the guard; the check
  count is 179.

### Galaxy map: HD draws the system window and the fleet box — brief 110 Part A, step 2, 15 September 2026

**Brief 115** (`doc/briefs/115-*`). Design (a), Data's decision A1.

- **Identity** — `screens/galaxy_map/boxmodel.py` (no pygame). The star or
  stack is HD's own last map click that went out (A2), and a box is drawn
  only when the live list agrees: the window stands where
  `MAINSCR::Popup_XY_` puts it for that star or icon (mainscr.cpp:1060,
  fleet box clamped by fleetpop.cpp:1441), and — system window — every
  planet field lies on the orbit ellipse of one of that star's planets
  (`GEO::_orbit_consts`, geo.cpp:5; sys.cpp:1829). The engine sorts the
  display slots by y (sys.cpp:172, :316), so a field's ORDER says nothing
  about its planet; the ellipse does, and the live Yian lists fit it
  (1.015 and 0.989, the orbit-3 field being the outpost the engine opened).
  Fleet box: one icon field per ship, at most nine. A mismatch draws
  nothing and logs why.
- **Texts** are HESTRNGS': "Star System %s" / "Star System Unexplored",
  the star-class description for an unviewable system, "Wormhole links %s"
  / "Stable Wormhole", "%s Fleet" or the monster's name, and the status
  line "Orbiting %s" / "%d turn(s) to %s" / "ETA %d turn(s)" / Antares.
  **DEVIATION:** the original prints the status line only with nothing
  selected or hovered; HD cannot know the selection and prints it always.
  The box's "N turns to" carries no 20000 condition in the source, so it
  shows on the turn of the order; the map's "eta N" waits a turn (Part B).
- **Drawing and input** — `screens/galaxy_map/boxdraw.py`. Boxes
  `system_*` and `fleet_*` in boxes.json, the CLOSE label in layout.json
  `movable_boxes`. A box sits on the side of the map the game's own
  window is on. CLOSE and ESC send the box's close field (decision 66); a
  planet disc sends its planet field; anything else inside is swallowed.
  **DEVIATION:** planets in a row by orbit, ships as their map icons.
  **OMISSION:** the system window's ship buttons, gate icons and hover
  line; the fleet box's ALL, scroll and five order buttons; the
  space-monster branch; and, drawn without a field, the orbit rings, the
  asteroid belts and the colony markers.
- **Live, SAVE5 (scratch), one connection:** HD drew "Star System Kif"
  with its three planets matched by orbit, CLOSE restored the list
  exactly; the scout's box read "CyberToller Fleet" / "2 turns to Dhira"
  and ESC closed it; a planet disc opened the colony screen, and the
  window the game reopened afterwards was drawn again through the kept
  identity. SAVE1-9 identical, SAVE10 unchanged, no fleet order.
- **`turns_left` (s_ship_data +109) joins the verified spec** in this
  commit, the first that reads it (runs 113/114). `travelling_speed` (+108)
  waits for Part B.
- **Not built:** moving a fleet from the HD box. Decision 65 still refuses
  the destination click; lifting it needs Data's decision on how a target
  is chosen in the HD box (the selection is neither on the wire nor
  settable by field id).
- **Smoke:** two checks (identity rules against the live windows and
  Yian's planets; drawing and the three sends); the count is 181.

### Galaxy map: full fleet control, phase 1 — two patches reported, HD side built — brief 117, 15 September 2026

**Briefs 116 and 117** (`doc/briefs/116-*`, `117-*`). Data's path 1.
Nothing applied, nothing built live; phase 2 is Data applying the patches,
rebuilding orion2re and a live test on scratch saves.

- **Open fix 20 (read), `doc/ext_fleet_selection.patch`** — unchanged: the
  icon owners, then "FSEL", the fleet box stack, one byte per ship node.
- **Open fix 21 (write), `doc/ext_fleet_select_ship.patch`** —
  `MSG_SELECT_SHIP` 0x85: one ship selected or not, every precondition
  checked before a write (box open, stack, own ship,
  `Ship_Can_Be_Selected_`, the ship in the stack's chain). Both patches
  dry-run in both orders on a copy of the tree and compile -fsyntax-only
  with the build's flags, alone and together. `tools/version_check.py`
  reports both markers without failing.
- **HD, against built data** — `core/game_state.py` reads the FSEL block
  (`fleet_selection`, None without the patch); `boxmodel.selection_of`
  maps it to the shown ships by node; `boxdraw` draws one box per ship,
  blue selected, black not, and a click sends `MSG_SELECT_SHIP`
  (`core/game_client.select_ship`). **HD STATE:** without the block the
  cells are outlines and not clickable; past nine ships a scroll bar is
  drawn with its thumb at the top, because the box's scroll position is
  not on the wire — to be measured in phase 2.
- **Fundament 65 amended:** with the selection known a star click moves
  the ships shown blue — variant (a); (b) is still Data's to choose.
- **Smoke:** two checks (the block and the model; the HD box, the send,
  the guard, the scroll display, the checker); the count is 183.

### Galaxy map: full fleet control, phase 2 — both patches applied, confirmed live — briefs 118-120, 15 September 2026

**Briefs 118, 119, 120** (`doc/briefs/118-*`, `119-*`, `120-*`). The
orion2re tree at `~/orion2re` is patched: a permanent change.

- **Applied and built** (`-DORION2RE_EXT=ON`): open fix 21 unchanged, open
  fix 20 as **revision 2**. Revision 1 was applied first (brief 118) and
  taken back out: live, HD's click on ship 13 flipped node 11, because
  `Sort_Ships_In_Stack_` rewrites `ship_idx` inside each chain (fundament
  67). Revision 2 sends `ship_idx` and `selected` per node and the fleet
  box's chain in cell order. `tools/version_check.py` now REQUIRES both
  (markers `fsel_chain_len`, `Select_Ship_`).
- **HD reads the node table off the wire** — `ships.wire_nodes`; owners,
  icon anchors, the icon-click identity and the fleet box use it.
  `build_node_map`, `stack_of` and `selection_of` are gone. A fleet box is
  drawn only from the FSEL block (cells in chain order, colour per node
  byte); without it no fleet box and the guard stands. A star click sent
  as an order keeps the box's identity.
- **Live, SAVE5 (scratch), one connection each run; SAVE1-9 identical,
  SAVE10 unchanged:**
  - check 2: the Yoth chain 9 -> 10 -> 11 carries ships 14, 15, 13; HD's
    first cell (ship 14, node 9) sent one `MSG_SELECT_SHIP`, the engine
    flipped exactly node 9, the original's first cell went black;
  - check 1: on the mixed selection HD's cells, the node bytes and the
    framebuffer's blue share agreed per cell;
  - target click (a): confirmed by Data's hand test (brief 119) — ships
    fly on a star click with the fleet box open; fundament 65's premise is
    measured;
  - check 5 (brief 120, no order sent): a box HD opened and draws gives
    `orders_ok` and the star click plans as an order (not sent); a box
    opened by a direct click on another stack is not drawn, and HD's star
    click on Sol was refused — no click sent, fields and ships unchanged.
- **Gaps, stated:**
  - ~~**the probe's star clicks did not move ships** (run 119): Zibbat was
    out of range (no message, by the source); Sol was in range and the
    original showed "4 turns to Sol", yet nothing moved. Not separated
    from the injection path; Data's hand test is the confirmation of (a);~~
    **RESOLVED (brief 121, Data's hand test in the HD window only, F5
    loaded):** HD's target click flies — the ships leave their orbit slot
    right to left as in the original, so the injected HD click with the box
    open arrives. The failure in run 119 lay in the probe, not in the HD
    path: the Zibbat run's target was out of range (proven by the source);
    for the Sol run the probe-side cause was not isolated further. The
    probe's success test itself was right — an order sets `location` and
    `status` at once (`Make_Ships_Move_To_`, shipmove.cpp:593-600);
  - **check 4, the scroll bar, deferred:** SAVE5's largest stack is seven.
    The box's first visible row is not on the wire; HD shows the chain's
    first nine and draws the bar as HD STATE;
- **Smoke:** the count stays 183; the node-table, block, model, HD-box and
  checker checks were rewritten to the wire data, and they fail if a
  rebuilt table returns.

### Galaxy map: ship destination lines — brief 110 Part B, brief 121, 15 September 2026

**Brief 121** (`doc/briefs/121-*`), with decisions B1-B3 of briefs 111/112.

- **Precondition, measured at the sprite:** the game positions with the
  HEADER size of BUFFER0.LBX entries 205..208 (colour 0), not the ink and
  not `SHIP_ICON_DIM` — `zoomtables.SHIP_ICON_HEADER_DIM`, two sources (LBX
  headers; live framebuffer at zoom 2 and zoom 0), recorded in
  `doc/ship_icon_measurement.md`.
- **`screens/galaxy_map/maplines.py`** — the destination lines, transcribed
  from `Do_Ship_Destination_Lines_`: own ships moving, foreign ships bound
  for a star with our colony or any outpost, the open fleet box's head;
  encoded locations only (from the turn of the order); green/red tables
  (mainscr.cpp:105-106, RGB from two sources, skin keys
  `travel_line_green/red`); from the icon corner plus half the header of
  entry 205 + (3 - zoom) to the star centre; the colour wave with
  `Draw_Directional_Multi_Colored_Line_`'s table and offset. The start
  point is re-anchored like the icon (`ships.anchored_point`).
- **HD EXTENSION B1:** every map line antialiased through ONE routine,
  `maplines.stroke`; the wormhole link goes through it.
- **HD EXTENSION B2:** one wave step is `ctx.px` HD pixels, at least one;
  the phase on a fixed 55 ms clock (the original's minimum pass,
  `Release_Time_(1)`).
- **OMISSION:** the "eta N" label, the order preview line (its colour is
  not on the wire), relocation lines (unverified offset).
- **Live, SAVE5 (scratch), one connection, no order; SAVE1-9 identical,
  SAVE10 unchanged** (evidence b0/b1 pictures, `b121_lines_record.json`):
  the scout bound for Dhira gets its green line; at zoom 2 HD's native
  start is (432, 216), the point the original's line was measured to start
  from, and 75 of 80 steps along the HD segment are green; at zoom 0, 93 of
  105.
- **`travelling_speed` (s_ship_data +108) joins the verified spec** (run
  114), next to `turns_left` (+109).
- **Findings, not acted on:** `SHIP_ICON_DIM` (the HD icon size) is 9 x 8
  at zoom 2 against a 12 x 11 header and 6 x 5 of ink — which one an HD
  icon should match is Data's question. *(Answered 15 September: neither
  moves, it is a DELIBERATE DEVIATION — work order 122 item 2.2, below.)* `tools/make_nebula_icons.py` reads
  FONTS.LBX entry 1 at offset 0; the entries are (flag, r, g, b), measured. *(Fixed 16 September: work order 122 item 2.3, below.)*
- **Smoke:** three checks (who gets a line and where it starts; the wave;
  one routine and the markings); the count is 186.

### Galaxy map: frame v2 installed, the boxes inside its cutouts re-derived — work order 122 Run 1a, 16 September 2026

**Brief 122** (`doc/briefs/122-*`). `screens/galaxy_map/assets/frame.png`
is Data's `galaxy_map_frame_v2.png`, byte for byte (sha256 `4e2aca76…`);
the old 2322x1256 master is gone from the tree and stays in git.

- **The real tool, before `--write`:** `tools/frame_holes.py` finds **10
  holes** in the 1706x922 image (alpha < 16, MIN_AREA 2000) — Chat's count
  holds. The galaxy rule names them without ambiguity: the largest is the
  map, the topmost of the rest the title, two right of the map (sidebar
  above TURN), six in the bottom row by x.

  | box | old image px (2322x1256) | old ref | new image px (1706x922) | new ref |
  |---|---|---|---|---|
  | map_area | 129, 105, 1691, 988 | 105, 88, 1402, 854 | 82, 58, 1260, 752 | 90, 66, 1422, 885 |
  | title (GAME) | 882, 21, 548, 53 | 727, 16, 457, 50 | 548, 2, 337, 51 | 615, 0, 383, 64 |
  | sidebar | 1872, 131, 303, 758 | 1546, 111, 255, 656 | 1394, 77, 213, 723 | 1567, 88, 244, 851 |
  | nav_turn | 1870, 921, 307, 171 | 1544, 790, 258, 151 | 1419, 840, 176, 42 | 1595, 982, 202, 53 |
  | nav_colonies | 143, 1126, 253, 44 | 116, 966, 213, 42 | 94, 830, 186, 39 | 104, 970, 213, 50 |
  | nav_planets | 444, 1126, 258, 44 | 365, 966, 217, 42 | 308, 830, 187, 39 | 345, 970, 214, 50 |
  | nav_fleets | 752, 1126, 252, 43 | 620, 966, 212, 41 | 522, 830, 187, 39 | 585, 970, 214, 50 |
  | nav_leaders | 1051, 1126, 263, 43 | 867, 966, 221, 41 | 737, 830, 188, 39 | 827, 970, 216, 50 |
  | nav_races | 1365, 1126, 253, 44 | 1127, 966, 213, 42 | 954, 830, 190, 39 | 1072, 970, 218, 50 |
  | nav_info | 1666, 1126, 229, 44 | 1376, 966, 193, 42 | 1180, 830, 186, 39 | 1326, 970, 213, 50 |

  `layout.json` `frame.image_size` and `frame.title_rect` follow (the
  smoke check compares both against the tool).
- **Boxes inside cutouts, in BOTH lists (1920x1080, 2560x1440; there is
  no empty list):**
  - `sb_*` — re-derived from the new height, not shifted: inset 10 left
    and right, the old gap-to-height ratio 16.4:93, and top and bottom
    inset `pad_y + 1`. Six rows of 121 at a pitch of 142.05 from y 98;
    text 132 wide, gap 6, icon 86 (the old 138/6/91 scaled by 224/235).
  - `help.json` `pad_y` 7 → **9**: at 7 the right-click regions covered
    95.6 % of the column against the original's 97.0 % and the smoke check
    failed; 9 is again the largest pad that stays inside the cutout
    (89..938 in 88..939), gaps 2-3 as before. The note and the stardate
    region's numbers are rewritten.
  - the system window and fleet box groups sat 12 ref px inside the OLD
    map's right and bottom edges (1495 / 930 against 1507 / 942), which is
    the gap `boxdraw._placed` mirrors on the other sides: both groups move
    by (+5, +9). `help_popup` is centred on the new map, (261, 108).
- **GAME centred by ink.** The label was centred by the font's line box
  and sat 3 / 5 / 5.5 px above the hexagon's centre at 1080p / 1440p /
  2160p; `_render_title` now centres the ink bounding rect in
  `title_rect`, 1 px or less at all three. The hexagon is ~4.5 ref px
  right of the map's centre in the artwork (hole centre x 716 image px
  against the map's 712), and the word follows the hole.
- **Nothing else derives from the old frame:** grep for 2322 / 1256 and
  for the old sidebar and map literals — only the two `layout.json` keys
  above and the boxes. `boxmodel.py` and `mapboxes.py` work in native
  640x480 coordinates.
- **Fit, measured against the frame's alpha** (ink of every string, all
  three resolutions; 2160p uses the 2560x1440 list): no glyph under alpha
  ≥ 16. Nav labels 13 / 17 / 25 px of ink in holes 45 / 60 / 90 px tall,
  clearance top/bottom 13-18 / 18-25 / 29-36; TURN 18 / 24 / 36 px ink,
  13-18 / 16-24 / 25-35. The nav and TURN labels are still centred by line
  box and sit 2.5-5 px high — they fit, and were not changed.
- **Live** (one client, Data's closed; the game as it stood, stardate
  3509.2, 54 stars, not a fixture; no send; SAVE1-9 identical, SAVE10
  unchanged): `~/orionlayer-fixtures/evidence/work_order_16sep/1a_galaxy_*`
  at 1920x1080, 2560x1440 and 3840x2160 beside the native frame. The
  sidebar readouts agree with the original's (157 BC +14, -3 (6), +2,
  +12 (15)). **One difference seen and not touched:** research reads
  "500 RP / +44 RP" in HD where the original prints "~16 turns / 44 RP".
- **The frame blob is 2.1 MB** against the old 0.7 MB.
- **Smoke:** the count stays 186; the frame-cutout check, the class A
  check and the sidebar help coverage check all ran against the new
  artwork.

### GAME menu: a fixed frame image around the popup — work order 122 Run 1b, decision 69, 16 September 2026

**Brief 122** (`doc/briefs/122-*`). Data's `game_menu_frame.png` is
`screens/game_menu/assets/frame.png`, byte for byte (sha256 `cb4d5ad3…`),
and a required input in `tools/setup.py`.

- **The real tool:** one hole, (115, 108, 879, 1193) in the 1108x1419
  image — Chat's claim holds. `layout.json` `frame.opening` carries it and
  the smoke check holds the two equal. Aspect 0.737 against the body box's
  0.739.
- **What changed on screen:** only the popup body. Its `thin_border`
  outline is gone; `gmframe` scales the image with one factor so the
  opening covers the body plus 2 ref px, centred on it, fills the opening
  from the cockpit texture (opaque, undimmed) and draws the frame over it.
  The buttons, slot list, settings rows and the confirmation and warning
  panels keep `thin_border`.
- **The anchor, from the source:** `LOADSAVE::Add_Game_Popup_Fields_`
  (loadsave.cpp:176-293) sets `_popup_base_x/_y = 0x90, 0x19` for all
  four in-game dialogs; `_Draw_Main_Game_Popup_` draws GAME.LBX picture 0
  there (:1356), 279x378. Centre native (283.5, 214), which is **51.68 %
  across and 48.0 % down the map window**, not its centre (the brief's
  expectation) and not the window's. That proportion is applied to the
  galaxy map's `map_area`: every overlay box moved by (-53, +10); the body
  is (511, 66, 628, 850). `help_popup` is centred on the new map like the
  galaxy map's own. Checked to 1 ref px by the suite.
- **Fit, measured on drawn pixels against the scaled alpha, 1080p / 1440p
  / 2160p:** menu, settings, load and save — 0 px outside the octagon.
  **Confirmation and warning do NOT fit**, and nothing was shrunk:
  CONFIRM.LBX (313 px) and WARNING.LBX (331 px) are wider than the popup
  (279) in the original too. At 1920x1080 the confirm panel reaches x 1246
  and the warning panel x 1277 against the opening's right edge 1141 (106
  and 137 ref px over the metal); at 2560x1440 1661 / 1702 against 1520;
  at 3840x2160 2493 / 2555 against 2282. The suite reports these numbers
  every run. They are drawn over the frame with their own opaque fill, so
  nothing is clipped, but the panel visibly lies across the right-hand
  metal: **a clash, reported, not restyled** — Data's decision.
- **The top rim:** at 1920x1080 the frame starts at y -16 and its metal
  about 1-2 px above the window, because the transcribed centre is 17 px
  above the map's. *(Fixed by work order 123 item 2, below.)*
- **Help and hit-tests:** unchanged in code; the boxes moved as one group
  and the GAME menu checks (help regions, the send gate, every node
  rendering) are green against the moved boxes.
- **Live** (one client; the game as it stood, stardate 3509.2, not a
  fixture; SAVE7 absent, so its Load row gives the warning without
  loading; settings left with ESC, not ACCEPT; SAVE1-9 identical, SAVE10
  unchanged): menu, settings, load, the slot-7 warning, save and the NEW
  confirmation at 1920x1080, 2560x1440 and 3840x2160, each beside the
  native frame, `~/orionlayer-fixtures/evidence/work_order_16sep/1b_*`.
  39 activations of the menu's own fields, no click or key injected.
- **Smoke:** the body-skin check rewritten to the new rule (the body
  wears the frame, every other panel `thin_border`), one new check (the
  opening against the tool, loading through the resource roots, the
  anchor, the octagon fit and the fill at three resolutions); a mutation
  of the body by 5 px fails it. The count is 187.

### Galaxy map: the icon size marked as a deliberate deviation — work order 122 item 2.2, 16 September 2026

**DELIBERATE DEVIATION — SHIP_ICON_DIM stays 9 x 8 at zoom 2 against the
12 x 11 sprite header.** Data's decision of 15 September 2026.
`zoomtables.SHIP_ICON_DIM` ((11, 10), (10, 9), (9, 8), (8, 7), by zoom)
sizes and hit-tests the HD icon, and its click area is live-confirmed;
`zoomtables.SHIP_ICON_HEADER_DIM` ((11, 11), (12, 11), (12, 10), (16, 12),
by 3 - zoom) is what the game positions its sprite and its lines with, and
what `maplines` uses. No code changed.

- **Marked** in the `maplines.py` docstring (DELIBERATE DEVIATION, quoting
  both tables), in the comment on each table in `core/zoomtables.py`
  (quoting the other table's values), in `doc/ship_icon_measurement.md`
  and here.
- **Smoke:** one check — the tables may not become equal (whole, or at any
  zoom as they are used against each other), the maplines note must quote
  both current tables, and each zoomtables comment must quote the other's
  current values, so changing one without touching the other's note fails.
  The count is 188.

### Tools: the nebula tool's FONTS.LBX palette read one byte to the left — work order 122 item 2.3, 16 September 2026

`tools/make_nebula_icons.py` `load_game_palette` took bytes 0..2 of each
4-byte `s_palette_entry`; the entry is `{changed, r, g, b}`
(orion2.h:2131-2136), the fault `core/lbx.read_palette` was corrected for
on 6 September, in a second reader. It now takes bytes 1..3.

- **Verifiable without the game:** FONTS.LBX entry 1 begins
  `01 00 00 00  01 00 03 00  01 04 04 06`. Before, the first three entries
  came out (4, 0, 0), (4, 0, 12), (4, 16, 16); after, (0, 0, 0),
  (0, 12, 0), (16, 16, 24). Every flag byte in the entry is 1.
- **Second source, live** (one client; the game as it stood, stardate
  3509.2; no send): the palette the game sends with its galaxy-map frame
  agrees with the fixed reading at 256 of 256 indices and with the old one
  at 0.
- **Visual test:** this galaxy holds ONE nebula, type 1 (zoom 2, native
  top-left (208, 106), 86 x 88). Of its 3973 sprite pixels on screen, 3655
  carry the sprite's own index in the framebuffer (the rest are stars, a
  name and a line drawn over it), and all 3655 equal the fixed palette's
  RGB, none the old one's. Picture: native crop, old palette, new palette
  and the tool's HD output, `~/orionlayer-fixtures/evidence/work_order_16sep/2_3_nebula_0_type01_zoom2.png`.
  **The other eleven types have no native counterpart here**: SAVE4 and
  SAVE5, the scratch saves the protocol allows, hold this same galaxy; a
  before/after sheet of all twelve at zoom 0 without a native half is
  `2_3_all_types_before_after_zoom0.png`.
- **"Regenerate the icons" changed no file in the tree.** The tool ran
  (48 of 48, to a scratch folder), but its output layout,
  `type_NN/zoom_N.png` at 3x, is not what the screen loads (listed under
  "What is missing"), and the committed `assets/nebula/type_NN.png` are
  authored masters of 1952-2208 px, not this tool's output. Overwriting
  them with it would have replaced artwork, so nothing was copied in.
- **Smoke:** one check — the reader against a probe FONTS.LBX whose every
  flag byte is non-zero; with the old byte order it fails. The count is
  189.

### Galaxy map: the "eta N" label — work order 122 item 2.1, 16 September 2026

**The source first, because it decides the label:** the original DRAWS this
label — `SHIPS::Print_Eta_On_Ship_Icon_` (ships.cpp:482-506), called from
`Do_Ship_Destination_Lines_` right after the line, only for 10000 <=
location < 20000 (:471). So it is a TRANSCRIPTION, not an HD extension:
HESTRNGS 307 "eta %d", the owner's font colours, style 1 at zoom 0/1 and 0
beyond, `Print_Right_` with the right edge at the icon's left plus, and the
top at the icon's top plus, the header of the OWNER's own sprite (entry
205 + colour * 4 + (3 - zoom)). `screens/galaxy_map/mapeta.py`; the OMISSION
in `maplines` is gone.

- **The table the brief pointed at is colour 0's only.** The headers differ
  by colour (colour 2 at index 1 is 11 x 11, colours 2-7 reach 17 x 14 at
  index 3), so `zoomtables.SHIP_ICON_HEADER_DIM_BY_COLOUR` (8 x 4, read from
  BUFFER0.LBX, row 0 held equal to `SHIP_ICON_HEADER_DIM`) is what the label
  uses. The digit ink height per style, 5 and 7 native rows, is decoded from
  FONTS.LBX entry 0 (`ETA_DIGIT_INK_ROWS`, MEASURED) — no source holds it.
- **HD geometry from the HD viewport** (Data, decision 35): header index
  3 - `ctx.zoom`, offsets times `ctx.px`; the icon corner is the mapped
  native corner coupled, the ship's galaxy position less half of colour 0's
  header decoupled. Text through `Style.render_text`, digits sized to
  rows x px, ink right-aligned to the anchor.
- **DEVIATION — two locks (Data, 16 September 2026, "Befehlszug"):** a label
  only while the game is on screen 0 in the map's OWN input loop (the map's
  field list, no modal — the fleet box and system window are part of that
  loop); and none between an HD star-click order and its effect (a ship of
  the ordered stack changed location or status), released without an effect
  after more than `EFFECT_PAIRS` newer snapshots (a refused order). Parking
  the game's zoom is NOT a lock.
- **Live, scratch saves SAVE4/SAVE5 only, one client** (Data's OrionLayer
  closed first). The number the original prints is read by machine: the
  FONTS.LBX glyphs rendered at the predicted native position, scored against
  the framebuffer's pixels (hits - false - missing); record and scripts in
  `~/orionlayer-fixtures/evidence/work_order_16sep/2_1_eta_record.json` and
  `scripts/`:

  | case | ship | turns_left (wire) | read from the framebuffer | HD drew |
  |---|---|---|---|---|
  | SAVE4, order turn, location 20025 | scout 10 | 3 | no label (none expected) | nothing |
  | SAVE5, location 10025 (to Dhira) | scout 10 | 2 | **2** — 39 of 39 ink px, 0 false | **eta 2** |
  | SAVE5 + TURN, still 10025 | scout 10 | 1 | **not readable**: Dhira's star sprite is drawn after the label and covers it; "1" is the only digit whose every ink pixel shows (5 of 5), 3, 4 and 9 are not excluded | `labels()` gives eta 1; the drawing was not captured |
  | SAVE4, HD order Zin -> Sol, next turn, 10014 | scout 10 | 4 | **4** — 36 of 36, 0 false (runner-up 9, one pixel short) | **eta 4** |
  | the same + TURN | — | — | stopped: the GNN news screen took no injected click or key | nothing (not the map's loop) |

  Two turns carry a clean read, and both are digit-exact; they are not two
  consecutive turns of one flight. The consecutive pair failed once on
  occlusion and once on the news screen.
- **The locks, live:** under the open GAME menu HD drew 0 labels; on the
  combat select (screen 12), the colony-base dialog and the GNN screen
  (screen 0 with a modal list) none. Two HD orders: the lock set at the
  click, 3 and 2 frames drawn without a label, released on the effect.
- **Found on the way:** the scout in SAVE4/SAVE5 sits at ZIN (star 6), bound
  for Dhira — the brief's "Sol->Dhira" is Zin->Dhira. An HD star click on
  the star the stack stands at is an order with `turns_left` 0: location 6,
  status 0, the Dhira order cancelled (`Make_Ships_Move_To_`, shipmove.cpp).
- **Not clean, and said so:** clearing turn dialogs by clicking CLOSE at a
  fixed native point repeatedly answered the colony-base selection with
  CLOSE and its "Really trash your colony base for 100BC?" — the scratch
  game's treasury went 143 -> 243 BC. In the game's memory only: SAVE1-9
  identical to the session start, SAVE10 rewritten by the turn ends (logged).
  The game was left on the GNN screen.
- **Smoke:** one check — who gets a label (not the order-turn ship), the text
  through `Style.render_text`, the anchor in HD pixels, no label under the
  GAME menu, with a foreign list on screen 0 or a modal, the order lock held
  and released on effect and after the floor, and a blocked 4 substituting
  (a stub font); a mutation without the loop gate fails it. Found by it: the
  lock compared snapshot `id()`s, which a freed snapshot's address reuses —
  it holds the snapshot now. The count is 190.

### GAME menu: confirmation and warning scaled into the frame — work order 123 item 1, 16 September 2026

**Brief 123** (`doc/briefs/123-*`). Data's decision on 122's reported
overhang. **HD DEVIATION:** the confirmation (native 310 px wide, at
161, 117) and the slot warning (331 px, at 154, 144) are wider than the
popup (279 px) and overhang it in the original; HD scales each group by one
factor, body width over panel width — 0.8997 and 0.8430 — rects and font
sizes alike (`boxes.json`, `layout.json` `_dialog_fit_note`), centred on the
body horizontally, vertical centre kept. Marked in `gmframe.py`,
`gmdraw.py`, decision 69 (amended) and the inventory.

- **No extra line:** HESTRNGS 186 and 187 (the NEW and QUIT questions) stay
  two lines, 178-180 (the slot warnings) one, one and four, at 1080p, 1440p
  and 2160p; checked before the change.
- **After NO:** the original stays in `Do_Main_Game_Popup_` with
  `_screen_data` 0 and redraws the main screen under the popup
  (loadsave.cpp:1240-1283), i.e. back to the game menu, which HD already
  does (`confirm_no` -> MENU); the warning returns to the Load dialog.
- **Smoke:** the frame check now holds ALL six dialogs to 0 px outside the
  opening at three resolutions (122's report of the overhang is gone) and
  the fit rule — panel width = body width, centred, text box in its native
  proportion to the panel. The count stays 190.
- **Live** (Data's OrionLayer closed first; the game as it stood, stardate
  3509.2; no slot loaded — SAVE7 is absent; picture after every click;
  SAVE1-9 identical, SAVE10 unchanged): menu, NEW confirmation, after NO,
  Load, slot-7 warning, after it, after CANCEL at 1920x1080, 2560x1440 and
  3840x2160 beside the native frame,
  `~/orionlayer-fixtures/evidence/work_order_123/`.
- **Seen, not part of this item** *(the first fixed by work order 124 D)*:
  under the confirmation HD draws the popup body without the menu's buttons (`present` asks the confirmation's
  own field list, which does not carry them), where the original shows the
  menu underneath; and the warning's text is the HD STATE line until the
  slot patch is in.

### GAME menu: the frame's top edge inside the window — work order 123 item 2, 16 September 2026

**The expression was the scale factor's slack, not a rounding.**
`gmframe.rects` scales with `s = max(want_w / ow, want_h / oh)`; the
opening (879:1193) is a hair narrower than body + bleed, so the WIDTH term
wins and the opening is 3.8 / 5.0 / 7.5 px taller than the body needs at
1080p / 1440p / 2160p. `open_y = body.centery - open_h / 2` split that
slack, half above the body, and the 88 image px of metal over the opening
then started at window y -1.6 / -1.8 / -2.2. The anchor arithmetic was
exact.

- **Fix:** `open_y = body.y - bleed`. The width term stays (the scaled
  dialogs span the body's width and need the side bleed: with the height
  term instead, the confirmation and warning had 284-649 px on the rim);
  the slack goes below the body. The body — the transcribed anchor — does
  not move.
- **Measured:** first frame row with alpha >= 16 at window y 0 / 1 / 1;
  all six dialogs still 0 px outside the opening.
- **Smoke:** the frame check asserts both (metal row >= 0, opening top =
  body top - bleed) at three resolutions. The count stays 190.

### Live protocol: one picture per click; the scratch saves' scout — work order 123 item 3, 16 September 2026

- **Fundament, Diagnosis:** "An injected click on a live game is followed by
  a picture before the next one", beside "A wait needs its traffic", with
  122's scrapped colony base as its source.
- **Scratch-save fact, SAVE4 / SAVE5:** the Scout (ship 10) stands at
  **Zin** (star 6), not at Sol, bound for Dhira. A star click on the star
  the stack stands at is an order with `turns_left` 0 — location 6, status
  0 — and cancels the Dhira order (`Make_Ships_Move_To_`,
  shipmove.cpp). Measured live in work order 122.

### Galaxy map: the eta label on two consecutive turns of one flight — work order 123 item 4, 16 September 2026

**Route:** the Scout (ship 10) in SAVE4, standing at Zin, ordered through
the HD fleet box to **Sol**; the original's box reads **"5 turns to Sol"**
(location 20014, turns_left 5). Turns 1 and 2 end in open space between Vox
and Sol.

| turn (stardate) | turns_left, read from the framebuffer | HD drew | match |
|---|---|---|---|
| 1 (3509.1), location 10014 | 4 — 36 of 36 ink px, 0 false (runner-up 9) | eta 4 | yes |
| 2 (3509.2), location 10014 | 3 — 37 of 37, 0 false (runner-up 2) | eta 3 | yes |

- **Protocol:** Data's OrionLayer closed first; one client; SAVE4 only;
  a picture after every click or activation (fundament, Diagnosis); SAVE1-9
  identical before and after, SAVE10 rewritten by the two turn ends
  (logged). Evidence and scripts:
  `~/orionlayer-fixtures/evidence/work_order_123/eta/` (`eta_record.json`,
  one picture per step, `../scripts/`).
- **Turn dialogs on the way, each answered on its own picture:** the
  colony-base choice for Malus (Malus I and the next planet refused with
  "You cannot build there", Malus II accepted — a colony in the scratch
  game's memory only), the colony landing screen, "just colonized", the
  colony screen's RETURN, the turn summary, the combat selection at Peren,
  a Darlok spy message.
- **Found:** screens that ignore an injected click or key — the colony
  landing (colland.cpp:203-213) — answer `ACTIVATE_FIELD` on their
  whole-screen hidden field, which is what finished this run; 122's GNN
  screen was probably the same case and was not retried. No code change was
  needed; `mapeta` is unchanged.

### GAME menu: the menu stays drawn under the confirmation — work order 124 D, 16 September 2026

**Brief 124** (`doc/briefs/124-*`). The original draws `Confirmation_Box_`
over the popup's own picture (gendraw.cpp:180) and the menu stays visible
behind it; HD drew the body alone, because `present` asked the
confirmation's field list, which carries only YES and NO. The screen now
keeps the menu's buttons as its last MENU list had them (`menu_keys`, so a
multiplayer menu without LOAD and NEW stays without them) and `gmdraw._menu`
draws those under the box.

- **Smoke:** the node-render check asserts the four menu words are drawn
  under the confirmation; the old rule fails it. Count stays 190.
- **Live** (Data's OrionLayer closed first; the game was found with the GAME
  menu open; SAVE4 reloaded through it; a picture after every click; SAVE1-9
  identical, SAVE10 unchanged): NEW confirmation at 1920x1080 and 2560x1440
  beside the native frame, `~/orionlayer-fixtures/evidence/work_order_124/D_*`.

### GAME menu: save slot names — work order 124 A, 16 September 2026 (a report)

**A patch is needed, and it is already written: open fix 14,
`doc/ext_save_slots.patch`, reported 14 September, not applied.** The
original reads the names from the SAVEn.GAM headers into
`MOX::_save_game_description[10]` whenever the dialog opens
(`FILEDEF::Get_Saved_Game_Descriptions_`, filedef.cpp:207-243); the snapshot
carries `_settings` but not that table, and the framebuffer read was
considered and rejected (free text, colour codes, no validation). The patch
still passes `git apply --check` on the current tree. The HD dialogs keep
"Slot N" (HD STATE, decision 60) until Data applies it. Details under open
fix 14.

### GAME menu: the Music and Sound Fx bars — work order 124 C, 16 September 2026

**Built, transcribed, and no patch needed.** Open fix 15's premise was
stale: open fix 3's second half (applied since 5 September) keeps an
injected click's pointer, so an `INJECT_CLICK` on the bar sets the volume.

- **The original, read:** two scroll fields, native (206, 219) and
  (206, 241), 155 x 12, value 0..156 from `Find_Bar_Position_` —
  `(x - 206) * 156 / 155`, so 155 is never produced — stored as
  `level = value * 100 / 155` in `_settings` (5 or less switches the channel
  off), shown on opening as `value = level * 155 / 100`, which is lossy
  (49 -> 75 -> 48). The bar is GAME.LBX picture 7 revealed up to `value`
  pixels: ten blocks, measured off the picture, a block can be partly lit.
  A held press follows the pointer; the level is applied when the press
  ends. Sources in `layout.json` `sliders._note`.
- **Live, before building** (Data's OrionLayer closed; SAVE4 reloaded;
  GAME menu up; a picture after every click): `INJECT_CLICK` (321, 247) set
  Sound Fx 50 -> 74, (284, 247) back to 50.
- **HD** — `screens/game_menu/gmsliders.py`, boxes `volume_panel`,
  `music_label`, `music_bar`, `sound_bar`, `sound_label` at the original's
  rects; block colours measured into `colors.json` (`slider_off`,
  `slider_on`, `slider_glow`). The drawn value is read off `_settings`. A
  press and a drag preview locally and send nothing; the release sends ONE
  click at the native point that gives the chosen value; the preview is held
  until the snapshot carries it. `main.py` now routes a left-button release
  to a screen that has `handle_left_release`. Help regions 420/421 are back.
- **Live, HD:** a drag on the Music bar from 25 % to 75 % sent nothing while
  held and one click on release — Music 49 -> 74, the HD bar and the native
  bar both at seven blocks and part of the eighth; restored to 49 (value
  76). SAVE1-9 identical, SAVE10 unchanged.
- **Open fix 15** answered (no command needed, dependency on open fix 3
  named); decision 61's example amended; the OMISSION is gone from the
  module, `layout.json` and this document.
- **Smoke:** one new check (the arithmetic over every value the game can
  produce, the live 74 and 50, lit width from `_settings`, nothing on press
  or drag, one click on release, the preview released after the floor);
  the help and marking checks follow the new state. **190 -> 191.**

### Pressed words: GAME and the GAME menu — work order 124 B, 16 September 2026

**Mostly a TRANSCRIPTION, and orange is the original's colour.** A held
button field draws frame 1 of its picture (`Draw_Field_`,
fields.cpp:2710-2717; YES/NO in `Draw_Confirm_Box_`, gendraw.cpp:35-49),
and in BUFFER0.LBX 1 (GAME), GAME.LBX's buttons and CONFIRM.LBX 1-2 that
frame is the word in orange, palette index 126 = (252, 136, 0), measured
through the live palette. It lasts while the press does. So HD draws the
word in `button.pressed_text` while the left button is held on it and the
pointer is still inside — not a timed flash.

- **HD INVENTION — the load and save rows.** They are hidden fields and the
  original colours a row by `active_save_slot` only (loadsave.cpp:852-878);
  Data wants every click in the tree to show, so a pressed row turns the
  same orange. Marked in `core/pressfeedback.py`, here and in the smoke test.
- **OMISSION:** the pressed pictures also nudge the word by a native pixel
  or two; not measured cleanly, not reproduced.
- **One implementation:** `core/pressfeedback.Pressed` on every screen
  (`ScreenBase.pressed`, released by `handle_left_release`); the galaxy
  map's GAME word, `gmdraw.button` and the slot rows read it. It starts on
  the press, before anything decides whether to send (decision 33). The
  9-slice frame's old side-button flash is a different mechanism and stays.
- **Smoke:** one check (SETTINGS and GAME orange while held, a Load row
  orange with its send refused, all cleared on release, the markings).
  **191 -> 192.**

### GAME menu frame against the nav bar — work order 124 F, 16 September 2026 (a measurement, no change)

Since 123 the frame's slack goes below the popup. Measured on the drawn
metal (alpha >= 16) against the galaxy map's nav boxes and the ink of their
labels (threshold 60 and again at 10, the second so an anti-aliased edge
cannot hide):

| window | metal reaches into the nav boxes | boxes it overlaps | label ink under metal | metal's last row / labels' first ink row |
|---|---|---|---|---|
| 1920x1080 | 16 px (to y 985, boxes from 970) | PLANETS, FLEETS, LEADERS, RACES | 0 | 985 / 986 |
| 2560x1440 | 23 px (to 1314-1315, boxes from 1293) | the same four | 0 | 1314 / 1315 |
| 3840x2160 | 36 px (to 1973-1975, boxes from 1940) | the same four | 0 | 1973 / 1974 |

**No label is covered, and there is no margin either:** at every size the
metal ends on the row directly above the labels' first ink row. Not fixed,
per the order; a font that is a pixel taller or a label moved up in F5
would be covered. *(Void since work order 125: the frame sits inside the map cutout
and no longer reaches the nav bar at all — below.)*

### Galaxy map: the research readout's source — work order 124 G, 16 September 2026 (a report, no change)

HD prints `research_accumulated` RP over `+research_produced` RP; the
original prints something else, from `MAINSCR::Print_Main_Screen_Data_`
(mainscr_main.cpp:178-243):

- breakthrough -> HESTRNGS 0x183 "Breakthrough"; no field -> 0x188 "none"
  (HD already matches both);
- otherwise `turns = COLCALC::Player_N_Turns_Until_Research_Complete_(plr)`
  (colcalc.cpp:432-458): if the field's status is 3 (researched) 0; if
  `produced == 0 && accumulated <= cost` -1; else repeat
  `turns += 1; accumulated += produced; total += chance(accumulated,
  produced, cost)` until `total >= 100`, where
  `chance = (accumulated - cost) * 100 / cost` when `0 < cost < accumulated`,
  clamped to 100 and raised to 1 if 0, else 0
  (`Chance_For_Research_Breakthrough_Aux_`, :469-484);
- `cost = Player_Research_Cost_(plr, field)` (:526-539) =
  `TECHDATA::_technology_fields[field].cost` (techdata.cpp:319ff), plus
  `hyper_advanced_tech[field - 75] * 10000` from field 75 on;
- `turns > 0`: the chance for THIS turn as "N%" when above 0, then "@" and
  HESTRNGS 0xE1/0xE2 "%d turn(s)", then `research_produced` and the unit;
  `turns < 0`: "0 RP"; `turns == 0`: the chance and `research_produced`.
  The "~" in the native picture is the "@" printed in the sidebar font.

**Checked against what the screens showed:** 412 RP / 44 produced / 18
turns (SAVE4, 3509.0) and 500 RP / 44 / 16 turns (3509.2) are both
reproduced by that loop for any cost from 896 to 935, and the table holds
fields at 900 (for example fields 34, 41, 45).

**What HD would need, and does not have:** the cost table (a copy of
`_technology_fields[].cost`, legitimate only with a checker against
techdata.cpp, as `tools/monster_hull_check.py` does for the hull tables),
the per-field status `tech_fields[]` and `hyper_advanced_tech[]` from
`s_player` — neither is in the verified player spec (decision 23). The
readout was not changed.

### GAME menu inside the map opening — work order 125, 16 September 2026

**HD DEVIATION, superseding 122's anchor.** The frame is fitted to the
galaxy map's `map_area` cutout (from its `boxes.json`, per resolution list):
height = the cutout's, aspect kept, centred. No extra inset — the image's
own transparent margins (20 rows top, 29 bottom, 34 columns each side) keep
the metal about 12 ref px clear of the cutout at the top and 18 at the
bottom. The body is the largest 628:850 box inside the opening less the
bleed; every overlay box is seated by the same move and ONE factor, fonts
through `content_scale` (`gmframe.seat`, run from `_reload_boxes`).
`boxes.json` keeps the design geometry; `Box.to_file` makes an F5 save write
the inverse. Decision 69 amended.

**Measured before building** (rendered ink heights through
`Style.render_text`; factor f = 0.8666 at every size, since `map_area` is
one reference rect):

| | 1920x1080 | 2560x1440 | 3840x2160 |
|---|---|---|---|
| frame today -> new | 426,-14,797,1020 -> 455,66,691,885 | 568,-18,1062,1360 -> 607,88,921,1180 | 853,-27,1593,2041 -> 910,132,1382,1770 |
| size against today | 0.867 w, 0.868 h | 0.867, 0.868 | 0.868, 0.867 |
| opening new | 527,133,548,744 | 702,177,730,992 | 1054,266,1096,1488 |
| menu buttons / SETTINGS / RETURN, font px (ink) | 30 (21) -> 25 (18) | 40 (28) -> 34 (24) | 60 (42) -> 51 (36) |
| slider labels | 30 (22) -> 25 (18) | 40 (29) -> 34 (24) | 60 (43) -> 51 (37) |
| slot row / detail | 28 (20) -> 24 (17) / 22 (16) -> 19 (14) | 37 (27) -> 32 (23) / 29 (21) -> 25 (18) | 56 (40) -> 48 (35) / 44 (32) -> 38 (27) |
| settings option | 24 (22) -> 20 (18) | 32 (30) -> 27 (26) | 48 (45) -> 41 (39) |
| confirmation panel (after 0.900 and f) | 529,338,544,396 | 705,450,725,528 | 1058,676,1088,792 |
| warning panel (after 0.843 and f) | 529,398,544,313 | 705,531,725,418 | 1058,797,1088,627 |
| question lines (NEW, QUIT, slot 7 missing, multiplayer) | 2, 2, 1, 4 — unchanged | unchanged | unchanged |
| slider blocks (device px) | 10 blocks, 27 -> 23-26 | 36 -> 31-34 | 54 -> 46-50 |
| slider values reachable from a device pixel | all 156 before and after | all | all |

Nothing fell below what the order named as a limit: no extra line, ten
countable blocks, every value still reachable. The smallest text is the
slot row's detail line at 1080p, 14 px of ink.

- **The volume bars are in the MENU,** not in Settings: they are fields of
  `Add_Game_Popup_Fields_` case 0 (loadsave.cpp:200-201); the pictures show
  them there.
- **Nav bar and GAME field:** by construction the frame lies inside the
  cutout (y 66..951 at 1080p against the nav boxes from 970 and the GAME
  cutout ending at 64); 124 F's measurement is void.
- **Press feedback and help:** both checks stayed green without change —
  they read the boxes' seated rects, the same objects the hit tests and the
  drawing use, so there was no second rect to miss.
- **Smoke:** the frame check retargeted (inside the cutout, height and
  centre, metal clear of the cutout's edges, one factor, the editor save
  writing the file's rect; it fails with the frame moved 20 px up). The
  count stays 192.
- **Live** (Data's OrionLayer closed first; the game as Data left it, the
  GAME menu open on the SAVE4 state; a picture after every click; SAVE1-9
  identical, SAVE10 unchanged; 44 menu-field activations, no click or key
  injected into the game): menu with the volume bars, Settings, Load, the
  slot-7 warning, Save and the NEW confirmation at 1920x1080, 2560x1440 and
  3840x2160 beside the native frame,
  `~/orionlayer-fixtures/evidence/work_order_125/` (the 1080p menu and
  Settings as `42_*` and `43_*`, see the next line).
- **Found, not fixed:** when OrionLayer connects while the game ALREADY
  shows the GAME menu, the overlay opens over the main-menu screen instead
  of the galaxy map (the dispatcher has never been on the map): the first
  two 1080p pictures show the main-menu artwork behind the frame. After one
  ESC to the map everything is as intended; the 1080p menu and Settings were
  retaken that way.
  **FIXED by work order 126 D (17 September 2026):** `GameMenuScreen.
  OVERLAY_PARENT = "galaxy_map"` (SCREEN_GAME is entered only from the map's
  GAME button, mainscr_main.cpp:609-613) and the dispatcher enters the parent
  before it opens such an overlay. One new check (the app on the main menu,
  a first snapshot at screen 8: the map is active under the menu; with the map
  already active it is not re-entered); it fails without the dispatcher change
  (`evidence/work_order_126/D1_check_fails_without_fix.txt`). 195 -> **196**.
  Headless only; not re-run live.

### GAME menu: the frame missing on the first opening — fixed, 16 September 2026

**Found by Data in the running tree at abcbab0:** the GAME menu drew its
opaque fill and no frame. **Cause:** `GameMenuScreen.enter` called
`super().enter()` — which reloads the boxes and seats them
(`gmframe.seat`) — BEFORE it loaded `layout.json` into `self.words`. On the
first entry `seat` found no `frame` block, so there was no placement:
`gmframe.draw` returned False, `gmdraw.panel` fell back to the fill, and the
boxes stayed at the file's unscaled positions. A second entry (the menu
opened again, a resolution change) had the words and showed everything.
Blit order (fill, then frame) and the scale target (the placement's frame
rect) were right; they were never reached.

**Why nothing caught it:** every frame check, and every live run, entered
the overlay at least twice (`update_from_game` plus an explicit `enter`,
repeated openings, resolution changes), and the checks measured geometry,
not drawn metal.

- **Fix:** the words are loaded before `super().enter()`.
- **Smoke:** one new check — a fresh app, the overlay opened ONCE through
  the dispatcher, rendered, and the drawn pixels compared with the scaled
  frame image wherever it is opaque (alpha >= 250, since `smoothscale` tops
  out at 253), 98 % required at 1080p and 1440p. It fails with the old order
  (no placement on the first opening) and with the image blit removed
  (0 of 145230 pixels). **192 -> 193.**

### GAME menu: save slot names from the engine — open fix 14 applied, 16 September 2026

Data applied `doc/ext_save_slots.patch` and rebuilt orion2re (linux-debug).
Live (orion2re started from `~/Master of Orion 2`, SAVE4 loaded from the
main menu's Load dialog, one client, a picture after every step, SAVE1-10
identical; evidence `~/orionlayer-fixtures/evidence/open_fix_14/`):

- **Load dialog:** `MSG_SAVE_SLOTS` with `screen_data` 2 and the ten
  descriptions as the native dialog prints them; the HD rows draw them with
  stardates and dates. Nothing on the HD side had to change to read it.
- **Save dialog:** `screen_data` 3; a click on a valid row starts the name
  edit with that row's name ("new"), sending nothing — the pre-fill
  (`gmsave.SaveEditor.start`) already existed and only lacked the data.
  **Difference kept:** an EMPTY slot starts the HD edit empty, where the
  original copies "... empty slot ..." into the field (loadsave.cpp:517)
  and the first backspace clears it (fields.cpp:1177-1193); the name that
  reaches the game is the same.
- **The main menu's own Load dialog** gets no block (SCREEN_GAME only) and
  has no HD version.
- **Removed:** the "Slot N" HD STATE — label, `layout.json` words, module
  and status markings. Without the block (only the tick between the field
  list and the slot message) a row now draws its plate and no invented
  label. `tools/version_check.py` requires the patch; open fix 14 reads
  APPLIED; decisions 60 and 61 amended.
- **Smoke:** checks 4 and 7 follow (no "Slot N" may return — fails when the
  label is put back; the marking stays gone), and 124 B's pressed-row check
  now presses a row carrying an engine name. The count stays 193.

### Colony list: a click on a stacked figure picks up that figure — 16 September 2026

**Reported by Data:** with stacked figures one had to click LEFT of the
figure to move. **Not two copies:** the draw (`colonylist`, `blit(surf,
(rect.x, figure_origin_y(...)))`) and the hit test (`cell_at_x`, `rect.x <=
x < rect.x + rect.width`, `width = int(pitch) - gap`) both read the same
`colonytrack.row_boxes`. **The fault was what the one geometry described:**
the slot a sprite is BLITTED at, not where the figure is SEEN. The ink starts
a master column or more into the 28 px canvas, runs past the slot into the
next, and shows through the next figure's transparent columns; the gap
between cells answered nothing. Measured on the extracted figures, clicks on
the centre of each figure's visible area: 165 of 210 missed at 1920x1080,
156 at 2560x1440, 165 at 3840x2160.

**The original** (`Do_Colony_Info_Pop_Stuff_For_Pop_` mode 3,
coldraw.cpp:362-366) takes the first icon in drawing order with `x <= (30 -
squish) * (index + 1) + left_x`: each icon owns the strip up to the next
icon's left CANVAS edge, so where two overlap the COVERING (later-drawn)
figure owns the overlap.

- **DEVIATION — the zone is the figure as seen.** `colonytrack.pick_zones`
  is the one home (decision 5): the sprites are laid out in drawing order at
  the renderer's own x and y, each figure's visible ink gets a centre column,
  neighbours meet halfway between their centres, the first zone starts at
  its slot's edge and the last ends at its last inked column. The covering
  figure still owns the overlap where its ink is; the original's canvas
  strip is replaced by the ink. Identity is unchanged: the pick is (job,
  index) and `colonysend` still injects the original's slot point. Without a
  figure set the zones are the coloured cells as drawn, as before. The pick-
  up passes the set the row is drawn with (`colonymoveui.click(figures=)`).
- **Smoke:** one new check. Every count 1 to 20 in each of the three job
  columns at 1920x1080, 2560x1440 and 3840x2160 is rendered through the real
  screen, each figure in its own colour, and the centre of what is visible of
  it must pick it up. It uses a synthetic silhouette shaped like the game's
  (the extracted figures are not committed, decision 50) and measures the
  extracted set too when it is on disk: 630 of 630 at each size. With the
  old slot rule it fails (426 of 630 at 1920x1080). Count 193 -> **194**.
- **Not live-tested:** a headless measurement; the pick-up is local and sends
  nothing, and the drop path is unchanged.

### The commit is coupled to the smoke test — work order 126 B, 17 September 2026

**A hook, in the tree:** `tools/githooks/pre-commit` runs the full suite
before git writes a commit and refuses it on any exit but 0 (a failure,
139, 137) and on a zero exit without the PASSED line. `tools/setup.py`
sets `core.hooksPath = tools/githooks` (and `--check` reports it);
decision 31 is amended with the rule and why a hook and not a wrapper. It
tests the working tree, not only the index. `--no-verify` bypasses it.

- **Shown** in a throwaway clone with the hook on: a suite replaced by one
  that SIGSEGVs (shell exit 139) and by one that fails — no commit created,
  HEAD unchanged; the real suite green — the commit created. Evidence in
  `~/orionlayer-fixtures/evidence/work_order_126/B_hook_*.txt`.
- **Smoke:** one new check runs the hook against four stub suites (SIGSEGV,
  failure, silent zero exit, pass) and reports whether this clone has the
  hook on. **194 -> 195.**
- **Fundament, filed from the 16 September handover:** decision 5 gains
  "one function makes drawing and hit-testing AGREE, not RIGHT" (the stacked
  figures, 165 of 210); Diagnosis gains the colony screen's right click as a
  live-protocol line; decision 31 the coupling above.

### The smoke test: quiet mode, a memory line, thirty runs — work order 126 C, 17 September 2026

- **`--quiet`** sends everything a run prints (check sentences, reports, log
  lines, SDL output) to a temporary file at descriptor level and shows the
  summary line only; on a failure the last 60 lines of that file, then the
  traceback. Without the switch the output is as before. The hook and
  `tools/setup.py` use it. `faulthandler` writes a crash's Python stack to
  the REAL stderr in both modes, so a 139 leaves a stack behind.
- **Last line, both modes:** `peak resident memory: N MB` (`ru_maxrss`).
- **Check count unchanged: 195.**
- **Thirty full runs** (`--quiet`, one after another, exit and peak RSS per
  run from `wait4`, the suite's own line beside it): **30 of 30 exited 0**;
  peak resident memory **4540 to 4836 MB**; **66.6 to 68.1 s** per run. Table
  in `~/orionlayer-fixtures/evidence/work_order_126/C_thirty_runs.md`, logs
  beside it. The exit-139 question has no occurrence in this sample; the
  memory figure confirms chat's measurement in kind (a 4 GB container dies).
- **Measured against the order:** a full run on this machine takes ~67 s, not
  ~10 s. The order's time argument against running part of the suite is
  therefore weaker here than it was drafted; decision 31 (full suite) is
  unchanged and the question is parked with the memory figure.

### SAVE11.GAM classified — work order 126 D, 17 September 2026

**Nothing in orion2re 1.60.0 writes or reads it**, so in the live protocol it
belongs with SAVE1-9: hashed before and after, identical. From the source:
`FILEDEF::Save_Game_(slot)` writes `SAVE<slot+1>.GAM` (filedef.cpp:43-48),
and its callers pass 9 (initgame.cpp:262, loadsave.cpp:1262, nextturn.cpp:32,
mainscr.cpp:3067), the dialog's slot, bounded to 0-9 (loadsave.cpp:536-539),
or `active_save_slot` behind a `< 10` guard (mainscr_main.cpp:617/628 into
loadsave.cpp:1813). `Load_Game_` is reached with 9 (mainmenu.cpp:472), the
dialog slot, a multiplayer slot 0-9 (multplay.cpp:767-772) or the same
guarded `active_save_slot` (loadsave.cpp:1639). Descriptions, status and
dates loop over ten (filedef.cpp:208, loadsave.cpp:599-640, :688-700).
QUIT sets `active_save_slot = 10` (loadsave.cpp:1263) after saving slot 9,
and both hotkeys that would use it refuse 10. The Extension API names no
save file. **What made the file is not in this tree:** it is dated 30 July
2026, 223,090 bytes like SAVE6 and SAVE9 of the same day, with a mangled
description (`\x031\x01`) — from before this engine's save code as it
stands; not investigated further. CLAUDE.md carries the rule next to SAVE10.

### The colony runs order — what is open, established — work order 126 E, 17 September 2026

The order chat called `workorder_colony_runs_and_doc_audit.md` is filed as
`doc/briefs/88-*` (the full order, 9 September) and `91-*` (its runs, as an
attachment). Against the tree:

- **Part 0** (where are the briefs) — done: `doc/briefs/`, brief 89, 9 Sep.
- **Run A** (pop-move 3a-3c) — done: d98a96d, "Run A — what one command
  would buy" above, then decision 52 and `doc/ext_move_pop.patch` applied
  (open fix 12).
- **Run B, the documentation audit** — NOT done. a83e5fc (12 Sep) was a code
  redundancy audit of the static-frame rebuild, not this. Per work order 126
  it is not today's; it goes with the reading-budget order (127).
- **Brief files:** the four names the 9 September handover missed are all in
  `doc/briefs/` (78, 79, 82, and the pop-move brief as 90). Still missing:
  **the head of brief 90** (it starts mid-sentence) and **work order 125's
  own text** (the GAME menu order the 16 September commits cite). Parked.

Nothing else remains that needs no decision; no live run was needed.

### Galaxy map: input split from rendering — work order 126 F, 17 September 2026

`screens/galaxy_map/screen.py` had one honest seam, and it is the one brief
110 part C will need: INPUT (motion, click and the map click, activation,
keys, right button and map cancel, wheel) against loading, geometry and
drawing. The input bodies moved to `screens/galaxy_map/mapinput.py` as
functions of the screen, `self` renamed `screen`, nothing else changed; the
`handle_*` hooks stay on the class and delegate, falling through to
`ScreenBase` exactly where the methods returned early before. The home ping
and help-rect helpers stayed (the smoke test and `core/screenhelp` call them
on the screen). **583 -> 461 code lines** (890 -> 722 total); still on the
exceptions list, regenerated from `tools/linecount.py` — the rest is one
thing (a screen's render orchestration and state), and a further cut would
be the number talking. Two checks read the moved text and follow it: decision
66's marking now in `mapinput.right_button` (plus: the hook must call it), and
the eta lock line in `mapinput.py`. Smoke **197**, unchanged.

### Read ahead: four screens — work order 126 G, 17 September 2026

Source readings, nothing built: `doc/colony_screen_reading.md` (SCREEN_COLONY 1
and SCREEN_QUEUE_POPUP 25), `doc/tech_change_reading.md` (36),
`doc/fleet_screen_reading.md` (4), `doc/races_screen_reading.md` (6). Written by
read-only sub-sessions and spot-checked where each file's provenance note
says. What they change for the tree today, all parked in
`doc/briefs/126-parked-for-data.md` (items 3-7):
- **Screen id 6 is two screens:** the game's Races screen and, through our
  own `ext_screen_id.patch`, race selection; `select_race` claims 6, so the HD
  map's RACES button is expected to open HD Select Race over diplomacy (not
  seen live). Open fix 22, DESCRIBED, NOT APPLIED.
- **The map's parking vs the turn-start research prompt** (screen 0, field 9
  a choice row) — decision 59's hazard in a second place, from the source.
- **`ship.py` `weapons()`** skips empty slots where flt2.cpp:696-701 stops.
- Neither the colony view nor the build queue fits the draft
  one-content-box rule; research, fleet and races do, with caveats.

### Screen 6 split: race selection reports 51 — work order 128 B, 17 September 2026 (open fix 22 applied)

**Seen live first** on SAVE4 (3509.0): RACES on the HD galaxy map sent
`ACTIVATE_FIELD 14`, the game reported 6 and drew Race Relations, and HD
switched to `select_race` (`evidence/work_order_128/B_before/`).

- **Engine** (Data's decision, the one change to orion2re this order allows):
  race selection reports the synthetic **51**, past the SCREEN enum's last
  value 43; orion2re 3305d78c on `orionlayer-local`, `doc/ext_screen_id.patch`
  revision 2 (hunks regenerated, forward-applied to a pristine export and
  reverse-dry-run against the tree).
- **OrionLayer:** `core/screen_names.py` is the one home — 6 has no HD screen,
  51 is `select_race`, and `ENGINE_SCREEN_MAX = 43`, which
  `tools/version_check.py` now reads from orion2_consts.h and requires with
  the patch's new marker. `select_race` claims 51; Empire Identity's lock is
  51 on the stock path and (50, 51) after Custom Race. The table's entry for 8
  said "no HD screen" although `game_menu` claims 8 — corrected, found by the
  new check. `doc/v3_orion2re_index.md` and `doc/ext_api_dokumentation_v3.md`
  follow.
- **Live after** (new binary, New Game from the main menu, through HD):
  custom path 13 -> 51 select_race -> picture mode -> 50 custom_race -> Accept
  -> Empire Identity (the game stays at 50) -> 39 -> 0 galaxy map; stock path
  13 -> 51 -> Empire Identity (the game stays at 51) -> 39 -> 0. RACES then:
  the game reports 6 and HD falls back to the framebuffer
  (`use_original`), ESC back to the map (`B_after_custom/`, `B_after_stock/`,
  `B_after/`).
- **The stock-race accept leaving the id set:** unchanged in behaviour, changed
  in meaning. The game keeps reporting race selection's id through the name
  and banner dialogs until galaxy generation — 51 now, 6 before — and HD's
  Empire Identity lock depends on it. It no longer reads as the Races screen.
  Not widened. The patch header's claim that every accept goes through
  `Racial_Option_Screen_` is corrected there: the stock accept does not.
- **Smoke:** one new check reads every screen module (tree and mods) and holds
  the rule — one screen per id, engine ids within 0..43, synthetic ids above
  it, the table naming the claiming screen; red with the maximum set to 60 and
  with a mod screen also claiming 51 (`B_screen_id_check_red.txt`). The routing
  instances move 6 -> 51. **197 -> 198.**

### The galaxy map parks only into its own list — work order 128 C, 17 September 2026

**Decided: guard by field-list shape.** Decision 59's own shape test
(`game_menu/nodes.classify`) classifies the GAME popup's dialogs and is not
reusable for the map; what is, is the map cancel's lookup of a field by type
and native rect in the LIVE list (decision 20). It is extracted to
`mapboxes.live_field` (second caller, so named rather than a third copy) and
`mapinput.send_map_cancel` calls it. `screen.update` parks only while the game
reports 0 AND the list holds both the grid field and the zoom-out button
(`layout.json` `zoom_out_field`: type 0, (244,455)-(298,473) — mainscr.cpp:1381
and :1392 for the position and hotkey, the live list and
`tools/galaxy_box_fields.json` for type and end corner), and it sends to the
index found there; `viewctl.ZOOM_OUT_FIELD = 9` is gone.

- **Smoke:** a research-shaped list (doc/tech_change_reading.md section 2) at
  screen 0, zoomed in: nothing sent; the map's own list with the button at
  another index: sent to that index. Red with the old screen-number-only
  guard (`evidence/work_order_128/C_parking_check_red.txt`). The existing
  parking checks now carry the recorded list. **198 -> 199.**
- **Live — the fault itself not reached; a worse one reached by my driver.**
  On a fresh stock-race game (3500.0), HD view zoomed in, one turn: the game
  itself stood at full zoom-out, so the old code had nothing to park and sent
  nothing — the original fault needs the GAME's own map zoomed in at turn
  start, which the HD map does not do. The turn-start "SELECT NEW RESEARCH"
  prompt came up under screen 0 with 38 fields (`C_preC/002_*.png`). **My
  driver misread it as a message box from a stale state and sent
  `ACTIVATE_FIELD 1` into it; orion2re died with SIGSEGV in
  `TECH::_Tech_Select_`** (`C_orion2re_segfault_backtrace.txt`), called from
  `REPORT::Set_Initial_Tech_`. That is the reading's null-dereference
  (tech.cpp:354-369, a commit with the pointer over no entry) confirmed live,
  and exactly the kind of send the guard exists to refuse. No save changed
  except SAVE10, the autosave of that turn end (logged). Not pursued further,
  as the order says. Recorded as open fix 23, an observation.

### Planets: the hovered row is the drawn row — work order 128 D, 17 September 2026

Hover picked its row by `(y - top) * n // height`; the rows were drawn by
`listgrid.all_bands` (h // n, the remainder on the last band) — two
arithmetics, disagreeing on single pixel lines (redundancy audit D8).
`planetdraw.row_bands` is now the one source of the bands, `render_list`
draws in them and the hover finds its row with the new `listgrid.band_at`,
which takes the drawn bands rather than dividing again (decision 5).

- **Smoke:** every pixel line of the list at 1366x768, 1920x1080, 2560x1440
  and 3840x2160 hovers the row drawn there; and against the picture, the first
  and last line of every drawn band, rendered, show `row_selected` at that y.
  Red with the old division: "1366x768 y=149: hover 0, the row drawn there 1"
  (`evidence/work_order_128/D_hover_check_red.txt`). **199 -> 200.**
- **Neighbours read in `doc/redundancy_audit.md`, not worked:** T6 (the scroll
  arrows' rects computed in `render_scroll` and again in `scroll_arrows` for the
  click — they agree today, the same decision-5 shape), D19 (scroll thumb
  arithmetic differs from the colony list's; Planets cites no source), D9
  (window rects through `layout.rect(box_rect)` against `Box.screen_rect`).
  Not live-tested: hover sends nothing to the game.

### `weapons()` stops at the first empty slot — work order 128 E, 17 September 2026

**The two sources, before the change.**
- **Can a gap exist? No, not in `count`.** Every writer packs from slot 0 and
  never leaves a used slot below count 1: the player's design screen puts a new
  weapon in the first empty row (design.cpp:869-876) and `Clear_Weapon_Slot_`
  shifts the later rows down (design.cpp:1724-1745); the AI adders write at a
  running index only for count > 0 (aidesign.cpp:669-704 and siblings);
  templates list from slot 0 (ship_config.cpp:58-80); strategic designs pack
  (initship.cpp:918-968); refit copies the design whole
  (colbldg.cpp:1951-1960); capture changes only the owner and `current_count`
  (combinit.cpp:2876-2913); combat writes back only `current_count`. Empty slots
  carry type 0 (designs) or, on colony and outpost ships, -1 or a planet index
  with count 0 (plntsum.cpp:475-478). A read-only sub-session traced the
  writers; design.cpp:869-876 and :1724-1745 and flt2.cpp:693-701 were checked
  by hand.
- **Saves: 0 gaps.** Live on SAVE4 (3509.0) and SAVE5 (3509.1): 60 ship
  records each, 21 with a weapon, 0 with a gap
  (`evidence/work_order_128/E_probe_SAVE4.json`, `_SAVE5.json`). Offline, a
  scan for the count-prefixed 129-byte ship array, validated against the two
  offsets the live arrays were found at in their files, over SAVE1-11 and the
  three fixtures: every real array with armed ships (60/21, 60/22, 71/37,
  109/61, 31/23, …) has 0 gaps; the only "gaps" are 255-record hits at offsets
  129 bytes apart, which are not the array (`E_offline_scan.json`).

**The change.** `core/structs/ship.py` `weapons()` now stops for good at the
first slot with `type < 0 or count < 1`, as flt2.cpp:693-701 does; its docstring
said `count > 0` for the same lines. **Callers:** one —
`screens/planets/monsterpanel.py:97`, the monster panel's weapon lines. Its
result cannot change for any design the engine writes (packed, and no used slot
with a negative type); it would differ only for a gap nothing produces.
**Smoke:** a constructed ship with a gap, with a used type at count 0, with a
negative type first, and a packed one; red with the old skipping loop
(`E_weapons_check_red.txt`). **200 -> 201.**

### Three small safeguards — work order 128 F, 17 September 2026

- **faulthandler at the top of `tools/smoke_test.py`,** before every other
  import, so a segfault anywhere — imports included — prints the Python stack
  before the process dies; `_run` still re-points it at the real stderr before
  `--quiet` redirects. Shown in a worktree with a forced segfault at import:
  exit 139, "Fatal Python error: Segmentation fault" and the Python and C
  stacks on stderr; `git commit` through the hook refused, HEAD unchanged, the
  stack in the hook's log (`evidence/work_order_128/F1_faulthandler_segfault_demo.txt`).
- **The hook in a fresh clone:** `tools/setup.py` already sets
  `core.hooksPath` (work order 126 B) and stays the one home. Proven: a fresh
  clone has no hooksPath; `python tools/setup.py` rebuilds, runs the suite
  (201 green, 5173 MB) and sets it; an `assert False` at the top of `main()`
  makes `git commit` exit 1 with HEAD unchanged (`F2_fresh_clone_hook.txt`).
- **The decision-28 check reads what it means.** It asked for "decision 28"
  and "DEVIATION" anywhere in four whole files; the fundament passed on words
  from other entries while entry 28's exception carries neither. It now reads
  entry 28 itself ("ONE EXCEPTION, AND IT IS MARKED" and
  `colonytrack.figure_size`), `figure_size`'s docstring, `FigureSet.__init__`
  and the status paragraph of the change. Red with the exception heading
  removed from entry 28, where the old condition stays true
  (`F3_decision28_check_red.txt`). **Neighbours with the same weakness, listed
  not swept** (from 127's Stop 1): the move-markings check (7 needles in the
  status file; 2 match only text saying the marking was withdrawn or removed),
  and the map-lines check's single needle `"maplines.py"`. Count unchanged:
  201.

### A live tool is a client — work order 129 A, 17 September 2026

`tools/livesend.py`: every send identifies the dialog from the FIELD LIST of
the state it is handed at that moment, and refuses — raising — otherwise.
`activate` requires the index to exist in the live list and, where the caller
names them, its type and native rect; `click` resolves the field the point
would reach (lowest index wins, fields.cpp:1264-1283) and checks its type;
`key` needs a screen or a shape, because ESC cascades. The shape tests are the
existing ones: `mapboxes.live_field` (work order 128 C) for a field named by
type and rect, `game_menu.nodes.classify` for the popup's dialogs, plus the
colony summary's seven sort buttons at native y 446..469 (colsum.cpp:267-273,
live 3 September 2026).

- **Moved onto it:** `tools/colony_move_probe.py` (sort key, both scroll
  activations, the pick-up and drop clicks), `tools/game_menu_hd.py` (the slot
  strip, the fifteen-key burst, the native ESC), `tools/zoom_probe.py` (both
  zoom activations, the arrow keys). **Not moved, and why:**
  `tools/colony_move_hd.py`, `colony_drop_sweep.py`, `colony_drop_timing.py`
  and `colony_roundtrip.py` send nothing themselves — they post pygame events
  into the real screens, so the product's own guards decide; `ext_diag*.py`
  and `struct_probe.py` read only.
- **Smoke:** eight wrong-shape sends refused with nothing sent (the research
  prompt's shape under screen 0 among them), and the map's own list passing all
  three send kinds. **201 -> 202.**
- **Fundament:** "A LIVE DRIVER IS A CLIENT" and "A COUNTER-TEST THAT RESTORES
  A FILE CAN BE MEASURING THE MUTATION", both under Diagnosis.

### The two turn-start research dialogs are on the wire — work order 129 B, 17 September 2026 (open fix 24 applied)

**The reading first:** `doc/newtech_reading.md`. The presentation is
`SCIENCE::Science_Room_` (science.cpp:112-392), entered from
`TECH::Tech_Select_` -> `Show_Off_Researched_Tech_` (tech.cpp:103), and the
select list follows at tech.cpp:106 after `current_research_field` and
`research_breakthrough` are zeroed (:104-105) — so which project completed is
off the wire once the list is up. Both run under SCREEN_MAIN, which confirms
126's claim for both. The room's list is three fields (a whole-screen hidden
one and an ESC hotkey, science.cpp:169-171) and one activation advances ONE
discovery; the same room shows stolen and artifact technology
(report.cpp:814, :822), so its shape does not identify research —
`research_breakthrough != 0` does.

**THE FINDING THAT DECIDED THE PATCH.** The path open fix 22 uses — writing
`MOX::_current_screen` — is not available here: the game DRAWS from that
value in both dialogs' description box, for its x (textbox.cpp:40-50) and for
its colour group (textbox.cpp:284). So the ids are reported **on the wire
only**: `ext::g_screen_override`, read by `ext::Tick` when it serializes, set
for a scope by `ext::ScreenOverride` — 52 in the science room, 53 in the
select list, nothing in change mode (which is screen 36). orion2re f838c754,
`doc/ext_research_screens.patch`, open fix 24, required by
`tools/version_check.py`; `core/screen_names.py` carries both ids with no HD
screen, so decision 22 takes over.

**Live** (new game on the stock-race path, the game restarted for it;
evidence `~/orionlayer-fixtures/evidence/work_order_129/`):
- the science room reports **52** and SELECT NEW RESEARCH **53**; in both,
  OrionLayer draws the original picture (`use_original`), has no active
  screen, and sends nothing — a click and a motion into its window reached no
  HD screen (`B_occasion2c_*`, `B_newgame2/005_DIALOG_52_native.png`);
- after the choice HD returns to the galaxy map by itself;
- **the choice itself is NOT reliable through OrionLayer, and is reported
  rather than worked around.** Three occasions: (1) a click on the row at
  native (176,85)-(394,99) through F12's original mode selected field 55;
  (2) a click on (176,51)-(394,84) the same way selected NOTHING — the list
  closed with `current_research_field` still 0; (3) the same row with a real
  `INJECT_CLICK` selected field 78. The reason is in the reading: the commit
  takes the entry under the POINTER (`Get_Selected_Entry_`, tech.cpp:354-369),
  never the activated field. **And a click in the fallback view does not even
  reach the game today:** `App._handle_click` forwards to the original view
  only in render_mode "original" (main.py:217-225), which is F12's mode, not
  the dispatcher's fallback — so with the dialogs up a click in OrionLayer's
  window does nothing at all. Both are for Data; option (c) of the reading is
  not authorised here.
- **Seen on the way:** the colony-base planet picker (the dialog work order
  122 scrapped a base in) also reports screen 0, and its CLOSE field means
  "scrap the base" — the confirmation appeared and the driver refused to
  answer it (129 A's guard doing its job).

**Smoke:** while the state reports 52 or 53 nothing is claimed and no HD
screen sends — with the map decoupled and zoomed in as a positive control.
**203 -> 204** with part D's check.

### The research foundations — work order 129 C, 17 September 2026

Built from the reading the status document already held ("Galaxy map: the
research readout's source", 124 G), so the sidebar can print what the
original prints (129 D).

- **`core/research.py`**, TRANSCRIBED: `FIELD_COST` (the cost column of
  `TECHDATA::_technology_fields`, techdata.cpp:319ff), `cost()`
  (`COLCALC::Player_Research_Cost_`, colcalc.cpp:526-539, with the
  hyper-advanced surcharge), `chance()`
  (`Chance_For_Research_Breakthrough_Aux_`, :469-484) and
  `turns_until_complete()` (`Player_N_Turns_Until_Research_Complete_`,
  :432-458).
- **A checker, not a reminder** (decision 36): `tools/research_cost_check.py`
  reads the 83 costs, `TECH_FIELD_COUNT`, the surcharge's first field and its
  step out of the source and fails on any difference; it locates the cost
  column by `s_tech_field_data`'s own member order (techdata.h:73-81). The
  smoke test runs it.
- **The player fields, decision 23.** `tech_fields[83]` @296 is now in the
  verified spec: orion2re's headers compiled with their own packing put it
  there with `sizeof(s_player) == 0xf0e` (the assert in sizes.h:21), and the
  live read agrees — 0..3 across the array, the researched field at 2, which
  is what makes the loop reproduce the original's own figure.
  `hyper_advanced_tech` @640 stays in `core/structs/unverified.py`: the live
  read is eight zeros, and a zero confirms no offset. **Consequence, on
  record:** for fields 75..82 the turn count is an underestimate until a game
  that has reached hyper-advanced research can be read.
- **Validation, three points and the loop's own arithmetic.** SAVE4 (3509.0):
  field 60, status 2, 412 RP at 44 per turn, cost 900 from the table, the loop
  gives **18** and the native sidebar reads "~18 turns / 44 RP". SAVE5
  (3509.1): 456 RP, **17**, and the native frame reads "~17 turns"
  (`evidence/work_order_129/C_native_SAVE4_research.png`, `C_native_SAVE5_*`,
  `C_probe_SAVE4.json`, `C_probe_SAVE5.json`). The two points the status
  document already carried (412/44/18 and 500/44/16) are reproduced by the
  same code. **A point with the chance above zero was not reached:** it needs
  accumulated points past the cost, which neither scratch save is near, and
  126's rule 8 keeps those saves reloaded rather than played.

### The sidebar's research readout, as the original prints it — work order 129 D, 17 September 2026

HD printed accumulated RP over produced RP; the original prints the chance
for THIS turn as "N%" where it is above zero, then "~N turns", then the
produced points — and "0 RP" when research stands still
(`MAINSCR::Print_Main_Screen_Data_`, mainscr_main.cpp:186-247). The
difference was seen twice on 16 September, deliberately left, described here
and **not marked in the code**, while `sidebar.py`'s docstring claimed to
mirror the original. With 129 C in place it is simply removed rather than
marked: `sidebar.research_readout` is the four cases, through
`core/research.py`.

- Wording comes from the game's own strings where the extractor has them
  (H 0x183 "Breakthrough", 0x188 "none", 0xE1/0xE2 "%d turn(s)"), with the
  JSON label as the fallback (decision 15); the "~" is the "@" the original
  prints, which its sidebar font draws as a tilde. Numbers stay in the
  proportional font, as the module already required.
- The row now carries up to three lines. `draw_text_block` takes a sequence,
  and where the band cannot hold the block the VALUE lines shrink — the label
  is never pushed out — measured by rendering (decision 30's consequence).
- Both docstrings that described the old behaviour are corrected: the
  module's row table and `core/structs/player.py`'s note.
- **Evidence:** HD beside the native frame at 1920x1080, 2560x1440 and
  3840x2160, for a running project (SAVE4's live values: "~18 turns" over
  "44 RP") and for Breakthrough —
  `evidence/work_order_129/D_sidebar_*_vs_native.png`.
- **Smoke:** the four cases on constructed records, including the two
  measured points, and the three-line row rendered at four sizes with its ink
  inside the row's box. **204 -> 205** with part C's checker.

### The eta label under the star sprite — work order 129, an observation (no change)

Data's screenshot showed white text under the star sprite at the destination
end of a selected fleet's course line. **Where the original puts it:**
`SHIPS::Print_Eta_On_Ship_Icon_(node, zoom, ship_x, ship_y)`
(ships.cpp:470-473) — at the SHIP ICON, not at the star; in the native frame
of this session's own run the digits sit clear of Zin, up and left of the
sprite (`evidence/work_order_129/F_eta_native_zoom.png`, from
`work_order_128/A_HEAD/00_start.png`). **Where HD puts it:**
`mapeta.anchor_point` (screens/galaxy_map/mapeta.py:114-127) anchors on the
same icon, plus the owner's header dimension. So the RULE is the same and the
difference is what is drawn around it: HD's star sprites are far larger
relative to the map than the original's handful of pixels, and `render_stars`
runs AFTER `mapeta.render` in `_render_map`, so a ship standing next to its
destination has its label covered. Reported only, as the order asks; a change
would be either the draw order or an offset away from the star, and both are
Data's.

### The fallback view is a view — work order 130 A, 18 September 2026

Decision 22 ("Graceful fallback.") promises the game stays playable on a
screen HD does not know. **It was not kept, and by more than work order
129 reported.** `dispatcher.use_original` was SET by the dispatcher and
READ by nothing in the product: the window filled with a flat (6, 8, 16)
and swallowed every click. 129's Stop 1 §5 and work order 130 both say
"shows the original picture"; the tree showed the fill colour, which is
what measuring it rather than reading it turned up.

With ids 52 and 53 on the wire since open fix 24, that made every
turn-start research a dead end inside OrionLayer's window: nothing to see
and nothing to answer.

`App._showing_original` is now the one question the renderer and the
click handler both ask, so there is no second click path (decision 9).
The only difference between F12 and the fallback is the status bar, which
stays with F12 because it names the MODE and the key that leaves it —
Data chose the plain forwarding fallback over the one with a visible hint
(129 parked point 1, option a over option c). `OriginalView.placement` is
the one home for where the picture lands; drawing and clicking each
carried the same four lines of arithmetic, and this is the order that made
them load-bearing for every screen HD does not claim (decision 5).

This relies on the COORDINATE half of open fix 3, which converts the
client's 640x480 point back to window space. `tools/version_check.py` did
not require it; it does now. Without it a forwarded click lands at roughly
a third of its intended distance from the top left, on a plausible wrong
field, silently.

### An activated research row is the chosen row — work order 130 B (open fix 25 applied)

orion2re **e9d07528** on `orionlayer-local`, bundle
`~/orion2re_bundle_18sep_e9d07528.bundle`, patch
`doc/ext_tech_activate.patch`, required by `tools/version_check.py`.

`TECH::_Tech_Select_`'s commit branch never used the field id it was
handed: `Get_Selected_Entry_` returns whichever entry carries
`current_app_index != 0`, and only `Draw_Tech_Select_` sets that, from
`fields::Scan_Input_()` — the game POINTER. An `ACTIVATE_FIELD` moves no
pointer, so a client's choice committed whatever the cursor rested on, or
nothing at all and then dereferenced the null (open fix 23's SIGSEGV).
Work order 129 B measured all three outcomes on three occasions.

`ext::g_activated_input` carries the field id of the input `Get_Input_`
is returning when it came from an activation, and 0 for every mouse
input. The commit branch, for an activation only, selects that field
before asking which entry is selected; an entry BLOCK resolves to that
entry's last visible row, exactly as `Draw_Tech_Select_` resolves it for
the pointer; and a null selection continues the input loop instead of
being dereferenced. The mouse path is unchanged — the flag is 0 for it,
and for a real click the selection would already be the same. Option (c)
of `doc/tech_change_reading.md` §5.1, the only orion2re change in this
order.

### The offered research rows reconstruct — work order 130 C

`doc/research_screen_stop1.md` §1 found the categories and the offered
field reconstructible and the choice ROWS not, for two named reasons.
Both are addressed.

`s_tech_field_data.tech[4]` is all zeros in techdata.cpp because it is
not a table: it is filled at runtime (techinit.cpp:444-474) by walking
the applications in ascending id and dropping each into the first free
slot of its own field. `core/researchlist.py` transcribes the app -> field
column and runs the same loop.

`tech_applications[212]` @379 now has decision 23's FIRST source —
orion2re's headers compiled with their own packing, `sizeof(s_player) ==
0xf0e`. **The SECOND is not in** and it is the one that matters: a live
read whose values agree with the rows the game's own screen draws. It
therefore sits in `core/structs/unverified.py`, and the screen falls back
rather than draw a list it cannot vouch for.

`validate_against_fields` is decision 25's validation and is not a test:
the screen runs it on every entry. `tools/research_cost_check.py` reads
all four transcribed tables out of the source and fails on any
difference — one row of `_technology_applications` writes its field as
`TECH_FIELD_INVALID` rather than -1, and a parser that only takes digits
reads 211 rows and lines every later application up against the wrong
field.

`tools/struct_header_check.py` is new: decision 23's header route made
mechanical for every covered spec — 133 offsets over seven structs, each
size against `sizes.h`, with a control that moves one offset by a byte
and requires the compile to fail. **`core/structs/ship.py` is NOT
covered** and says so: it names `s_ship_data`'s members itself, and the
rename map that would cover it is work nobody has done.

`core/livefields.py` is the one home for reading a live field by its
shape. The research screen is its third caller, and a screen importing
another screen's module to get at a shared rule is how the rule gets
copied instead.

### The research names come from the player's files — work order 130 D

A THIRD output of `tools/techname_extract.py` (`techfields_<lang>.json`,
`core/technames.py`): the field and application names are the first two
tables of the block it already walks to reach the buildings. And
`tools/billtext_extract.py` is new (`billtext_<lang>.json`,
`core/billtext.py`) for the panel's own wording. BILLTEXT is not shaped
like the other string files: a message is its own six LBX entries, one
per language (`Get_Text_Message_`, jim.cpp:336-359).

`core/technames.py` refuses to name fields 75..82 from that block. The
block DOES carry a string at 75, "Biology" in the English file, and
`Technology_Fields_Name_` does not use it — those eight are
`_hyper_field_title` out of ESTRINGS. Returning the block's string would
be a plausible wrong name.

Both files are gitignored, both are reported by `tools/setup.py`, and
absent, stale and short are three stated states. Read off the English
files, which is also the cross-check on the whole reconstruction: field
21 "Capsule Construction" offers Battle Pods, Survival Pods and Troop
Pods, and message 64 + group names the eight panels BASIC .. OTHER.

### The research select screen — work order 130 E, wire id 53

`screens/research_select/`, structure only. Frame and artwork come later
(Data, 17 September).

**The layout is the original's rectangles**, and the provenance is not on
a box: `Box.to_dict` serializes a fixed key set, so a `native` key would
be dropped the first time the F5 editor saved this screen — decision 38's
trap for `help_id`, and why `colony_summary`'s `boxes.json` carries no
rect either. `boxes.json` names the boxes, `native.py` holds every
rectangle with its tech.cpp line, and `seat()` marks them derived. The
eight entry boxes ARE the game's own entry-block fields.

**One rectangle for drawing and clicking** (decision 5), and because a
shared function guarantees agreement and not correctness, the check
renders and requires every row's VISIBLE CENTRE to pick that row, as work
order 128 D did for the Planets list.

**It refuses before it sends and before it draws.** A click off a row
sends nothing (decision 33); a row resolves by SHAPE in the list of that
frame; a second click after the commit sends nothing; ESC and every other
key send nothing, because select mode has no exit but a commit
(tech.cpp:131) and `ScreenBase.handle_key` would otherwise have forwarded
them.

**`ScreenBase.wants_original`** is decision 22 one step in: a screen that
knows the id but cannot vouch for its own picture hands back to the
original view. Five states do it — no player record, names absent,
wording absent, a field list of the wrong shape, a reconstruction the
list contradicts — and each logs once, not per frame.

**Marked**, each held by a check: four OMISSIONS (the science room
animation, the category list popup, the description box a right click
would open — so a right click inside the panel does nothing — and the
little arrow), one HD EXTENSION (the title, which the original paints
into TECHSEL art), three DEVIATIONS (the category label printed rather
than painted, the RP suffix that ignores `_settings.language`, and
shrinking where `Squeeze_Print_` compresses).

Help 254's three rectangles are transcribed from billhelp.cpp:42-46.
They are NOT "outside the panel" — they lie over the fill's own top and
bottom edges, which is how `doc/tech_change_reading.md` §7 derives the
panel's visible edge. The rule that holds is narrower: no help region may
cover an entry block or a radio, because a right click there is the
description box or the category list, not help.

### The live acceptance of work order 130 — 18 September 2026

A new Psilon game against orion2re **e9d07528** (`orionlayer-local`,
open fixes 24 and 25 applied, rebuilt and the binary checked for
`ext::g_activated_input`). One client throughout; SAVE1-9 and SAVE11
identical before and after, SAVE10 rewritten by the game's own autosaves
and logged only. The driver is `tools/research_hd.py` on
`tools/livedrive.py` and `tools/researchphases.py`.

**The fallback is a view, live.** Every screen HD has no version of drew
the game's own picture in OrionLayer's window and forwarded clicks: the
science room (52), the colony build prompt (1), the end-of-turn report
(39), the GNN broadcast and the leader offers. The record carries the
number of distinct colours beside every capture, which is the check the
129 report did not make.

**The choice means the row.** Two occasions, two categories, and the
game's pointer was never moved by this run — so a pointer standing still
cannot explain two different rows both landing correctly. Open fix 25
is what makes that true; before it, work order 129 measured a selected
field, no selection, and a different field on three occasions.

**And the list does not always wait — open fix 26.** Three times the
select list committed a row BY ITSELF about a second and a half after
the science room handed over, with a send counter proving the client
sent nothing. It is why choosing has to happen in the same process that
walks the room out, and why the HD screen re-reads rather than
remembers.

**One live number for the cost table**: field 62 read 540 accumulated of
650 at 15 RP a turn, and `core.research.cost(62)` is 650.

## What is missing

### Research select (work order 130) — what the live run still owes

The live acceptance RAN on 18 September 2026 (evidence under
`~/orionlayer-fixtures/evidence/work_order_130/`). Parts A and B are
proven; part F is one occasion short of what the order asks.

- **Part A — PROVEN, twice.** On wire id 52 the window shows the game's
  own picture and a click in it moves the room on: four and five clicks
  in two separate runs, each advancing one discovery, the last handing
  over to 53. No F12 at any point. Also proven on SCREEN_COLONY (1),
  where a click on RETURN through the fallback took the game from
  1/36 fields to 39/1.
- **Part B — PROVEN, twice, on two rows in two categories.** An HD row
  click gave field 4 (category 4) and a bare `ACTIVATE_FIELD` gave
  field 22 (category 6); each time the wire afterwards reported THAT
  row's field. The order asks for three rows on three occasions — the
  third is missing (below).
- **Part F — ONE of three.** Only the first selection (field 4,
  category 4) was made and read back cleanly inside OrionLayer's
  window. Two further attempts lost the occasion to open fix 26, and a
  third could not be run: the machine's display server stopped
  accepting new clients partway through the evening, so orion2re could
  not be started again (`SDL_Init(SDL_INIT_VIDEO) failed: The video
  driver did not add any displays`). HD beside the native frame exists
  at one resolution, not three.
- **The 128 crash case was NOT run.** It needs a category with nothing
  left to offer, and no list reached in this run had one.

Everything above is in `doc/briefs/130-parked-for-data.md` with what to
re-run.

- **`hyper_advanced_tech` @640 stays quarantined**, as work order 130
  says it should: a late-game save is what it needs. The consequence is
  written down in `core/structs/unverified.py` — the sidebar's turn count
  underestimates for fields 75..82, and an application above id 203 is
  named without its roman numeral rather than with a guessed one.

### OLED floor lift and player-colour presets
- **The white player has no visible hover mark in the Planets list**
  under a preset: a white base cannot get lighter (ratio 1.0). Known
  limit of the rule; if it bothers in play, an off-white base, decided
  with a picture.
- A player's own base table (`player_color_base` in the user file) is
  applied and warned about, but the UI offers presets only.
- Not seen on the real map yet: the floor steps and the preset were
  checked numerically and in an offline render, not in a live session.

### GAME menu
- The slot game-type icon is an OMISSION.
- The Save dialog's right click outside a help region is UNVERIFIED and not built.
- SCREEN_REPORTS (39) is the next screen; a load falls back to the framebuffer there.
- Empire Identity's `type_name` burst overflows the game's ten-key ring for longer names.

### Galaxy Map
- **Anchored zoom — three things only a running game can answer.**
  (a) Does the game clamp `_cur_map_x/_cur_map_y` to 0 at maximum
  zoom-out? The parking logic assumes the parked slice starts at the
  origin; `tools/zoom_probe.py` measures exactly this. (b) Does
  mapgen ever place a star inside the 1–3 unit strip the parked slice
  misses on the far edge? If so, that star is unclickable while
  decoupled. (c) The orbiting-ship slot offsets stretch with the HD
  zoom by design — judge them against the original before calling the
  feature finished.
- **ZOOM rocker.** Fields 8/9 no longer drive the view; field 9 is
  used only by the parking logic. A visible rocker would need two
  cutouts in `frame.png` between FLEETS and LEADERS, then
  `frame_holes.py` and two names in `layout.json` — but with the HD
  zoom on the wheel and on `+`/`-`, it is now cosmetic rather than
  functional.
- **Ship icon artwork gaps: Amoeba and Antaran.** No HD master for the
  amoeba (owner 10) or the antaran (8); both draw as the grey player
  ship — a marked **DEVIATION** at `ships._resolve_sprite`, kept on the
  map because a vanished monster would be a gap against the original
  (Data, brief 107). The smoke test holds the stand-in set to exactly
  these two. Artwork is Data's to make; the Planets panel leaves the
  amoeba's sprite box empty until then. Only zoom level 0 has been
  measured — steps 1..3 are extrapolated, see
  `doc/ship_icon_measurement.md`.
- **The monster footprints disagree with their own sprites.** Measured
  off BUFFER0.LBX (brief 107), guardian 13x11, crystal 15x12, dragon
  13x13, hydra 13x12, eel 15x5 against the table's screenshot values
  12x11, 13x13, 13x10, 11x12, 9x9; the framebuffer matched the LBX
  entries pixel for pixel. Not changed — an open question for Data.
- **The galaxy map's movable boxes are invisible in HD** — the system
  window and the fleet box (brief 107, gaps 1 and 2, one gap). A star
  or fleet click goes to the game, which opens the box on screen 0, and
  the HD screen does not show it. The box registers its own fields
  (live, 14 September 2026: a black-hole click added the ESC close
  button, the title strip, the system grid and the whole-box field, and
  ESC removed exactly those four), so the FIELD_LIST shape is the signal
  and nothing is needed from Joes. Brief 110 Part A: the icon hit test
  and the box state are built (15 September 2026, section above); HD
  still does not DRAW either box, and until it does a fleet cannot be
  moved from the HD map — decision 65 refuses the destination click.
- **Maximum galaxy size (community map) — both bugs fixed, nothing
  open.** Above 72 stars the game leaves the 10/15/20/30 scale ladder
  and builds one by halving `_max_map_scale`, so `zoom_level()` needs
  that value. No caller passed it, and `_extended_zoom_level` then
  fell back to `map_scale`, which satisfies its own top rung at every
  scale: an extended map reported max_zoom however far the player
  zoomed in, and drew its smallest star, ship and font step
  throughout. Fixed; the smoke test pins the ladder at both the table
  and the `MapContext` level. **The second one closed 7 September
  2026**: `max_map_scale` no longer estimates. It transcribes
  `MAPGEN::Maximum_Galaxy_Display_Scale_` from MAP_MAX_X *and*
  MAP_MAX_Y, covers all five galaxy sizes, and was accepted on a live
  probe against a generated 155-star Maximum galaxy — see the entry
  below. `tools/zoom_check.py` remains the live check and now has to
  print MEASURED == DERIVED on any galaxy at all.
  Star names vanishing and the black hole freezing at the widest view
  are NOT bugs — `Print_Star_Names_` bails at
  `Is_Extended_Max_Map_View_`, and `Advance_Black_Hole_Animation_`
  stops once `Star_Scale_Percent_` drops below 100 (scale > 30). Both
  return one zoom step in, confirmed live 29 August. But both fire off
  the derived `max_map_scale`, so they are only right at the right
  scale.
- Popup overlays: system popup (25), build queue, colonisation (30).
- Info panels; the influence overlay the original can draw.

### Colony Summary
- Producing sorts by name until `TECHDATA::_buildings` cost is
  extracted (colsum.cpp:1091).

### Planets
- **Planets In Range is a marked gap** — the toggle drives the game and
  the HD list does not filter on it (brief 101, Data's decision (c)).
  `Star_In_Extended_Range_Of_Player_` needs `s_player.ship_range`, the
  treaty table and each star's black-hole block bitmap, none of them a
  verified spec; `doc/plntsum_reading.md` carries the helper, read, for
  the follow-up brief. Marked in `planetrows.FILTER_GAPS` and
  `layout.json` `restrictions._gap_range`; a smoke check fails if the
  marking and the behaviour disagree.
- **Sending ships** — Send Colony / Send Outpost, the armed row click,
  the ETA markers, send cancel, the inset's directional line and
  markers, and the status line's ETA, out-of-range and blocked lines.
  A second brief, an event-driven chain (decision 21).
- **The five toggles are not on the wire.** HD starts with all five off;
  a toggle the game held on before the screen opened disagrees until it
  is clicked twice. Seen live in Stop 3 on the reference save (range was
  on). A documented gap (Data, after Stop 3); the request to put the
  flags on the wire is `doc/orion2re_open_fixes.md` item 13. No frame
  reading.
- The special line's ship name in a monster system (the design part of
  the ship spec — verified since brief 107, not yet read by the special
  line); the amoeba's panel sprite (no master); the star-click warning box
  (H 0x14F); rotating planets and the inset's animated scanned star.
- Omniscience from a Galactic Lore leader, and Advanced City Planning's
  +5 on `max_pop` — both read from records that are not decoded.

### Context help
- **The colony summary has no help.json yet, and the original has a
  list for it** — `ERICHELP::_colony_summary_screen_help_list`, 22
  entries (erichelp.cpp:65), installed by
  `Set_Colony_Summary_Screen_Help_List_` (colsum.cpp:144 and :531).
  That is the natural next step: the machinery is a mixin, so the
  screen opts in by shipping a `help.json` and a `help_popup` box,
  and the sort buttons and the empire sidebar are exactly the kind
  of control the entries explain. Nothing in `screenhelp.py` needs
  to change.
- **The per-entry animation is not drawn.** `s_help_record` carries
  an `anim_lbx` / `anim_info` pair and the original plays it beside
  the text. The extractor preserves the reference in the JSON, but
  nothing renders it.
- **Galaxy Map help 300 (the ZOOM rocker) has no HD element.** Fields
  8/9 no longer drive the view and there is no rocker cutout in
  `frame.png`; recorded in `help.json` under `_omitted` rather than
  left silently absent.
- **The sidebar help regions are padded vertically, not
  horizontally.** The box union spans 1577–1801 inside a `sidebar`
  cutout of 1567–1811 (galaxy frame v2, 16 September 2026; it was
  1556–1791 in 1546–1801), so about 10 reference pixels down each side of
  the column still answer a right click with nothing. The same
  `pad_y` mechanism would take a `pad_x`; the vertical strips were
  the ones worth 12.8 % of the column, these are worth 8 % of its
  width and were left rather than fixed unmeasured.
- **The runtime-appended Galaxy Map regions are not transcribed.**
  `Set_Main_Screen_Help_List_` appends more for the multiplayer bar
  and the fleet popup; neither exists in HD yet.
- Select Race, Custom Race and the naming dialogs have help lists in
  the original and are deliberately not wired: those screens are
  finished and the entries explain what the HD screens already show.

### The font was replaced — Bank Gothic (DEMO) is gone
Aldrich (Matthew Desmond, OFL) ships instead, with `OFL.txt` beside
it. A demo font is not licensed for redistribution, which stopped
being an abstract debt the moment the tree became a repository.
Chosen by measurement across six OFL candidates: closest in height
(38 vs 40 px at nominal 40) and ascent (29 vs 31), advance widths a
consistent 85-93 % of the old font's — narrower, which is the safe
direction, since text shrinks inside boxes tuned for the wider face
instead of overflowing. One visible change, worth naming: Bank
Gothic drew lowercase as small caps, Aldrich draws true lowercase.

The substitution machinery stays and now reports an empty set, so
every string takes the single-font path. The smoke check was
rewritten with it: it asserted that `(` and `4` *are* substituted,
which tested one font's defect rather than the mechanism. It now
asserts that the shipped font substitutes nothing, that a stub font
with a deliberate collision is still detected, and that any shipped
font has a licence file next to it. Decision 41.

The galaxy map's `help_popup` box grew from 745 to 800 reference
pixels: the new metrics pushed the Command Points table 35 px past
the old bound. Still centred on `map_area`, still inside it.

### DEMO font substitution — the machinery, now dormant
`Style.render_text` is wired into star names, frame titles, frame
buttons, the Custom Race popup and the two generic label helpers in
`style.py`. Several sites still call `get_font(...).render`
directly: the **F5 editor overlay**, `select_race`, `custom_race`'s
panels, `new_game`, `empire_identity`, and the ListView header.

**This stopped being visible on 31 August** — Aldrich substitutes
nothing, so a direct render and `render_text` now produce identical
output, and the smoke test asserts that for four sample strings. It
is no longer a bug; it is a latent one. The moment a mod ships a
demo font, every one of those sites shows watermarks again while the
converted ones stay readable. Still worth converting, now at leisure
rather than under pressure, and each site remains a regression risk
without test coverage.


### Empire Identity
- **The 23-second gap** — dormant since the 30 August reboot, not
  closed. The full record (evidence, ruled-out causes, the withdrawn
  conclusion, and the three commands to run when it reappears) moved
  to `doc/empire_identity_slowload.md`. Short version: one run spent
  23.6 s in the mapgen silence, every run since 2.7 s, a reboot ended
  it, and the likeliest — unproven — mechanism is orion2re
  serializing for dead clients left over from the old watchdog's
  reconnect storm.

### Custom Race
- **Cross-check the Accept guard against the game.** Accept is refused
  locally on `picks_remaining < 0`, computed from HD's own
  `_trait_state`. If the two sides ever drift apart the wrong way
  (HD >= 0, game < 0) the Accept still goes out, orion2re answers with
  its own framebuffer box, and the HD screen sits on Empire Identity
  while the game stays on 50. Reading the trait state from the player
  record removes the drift and therefore this case too.
- Read trait state live from the player record instead of the local
  `_trait_state`.
- Verify the government value mapping (still UNVERIFIED in
  `traits.json`).
- Race key for Custom Race from the player record — also unblocks the
  Empire Identity emblem for custom races.

### Struct verification

**Two of these are what still separates the colony list from full
accuracy.** Both are named in `colonyrows.py`, in `max_population()`,
as deviations; they belong here as well, because a limitation that
lives only in the module that works around it is a limitation nobody
finds.

- **The pop nibble is a PLAYER index, not a race — and for 0..7 it
  now has a second source; only the sentinels do not.** Read out of
  the C++ on 1 September 2026:
  `POP::MASK_RACE` (pop.h:8) is consumed by
  `COLONY::Get_Effective_Pop_Player_` (colony.cpp:1257), which
  returns `pop & 0x0F` as a player index and maps only 8 and 9 to the
  colony's owner. The race is a second lookup —
  `MOX::_player[idx].race` in `Colony_Pop_Anim_` (colony.cpp:1275).
  The header names the mask after the thing two steps away from it,
  and that name is no longer in the spec: the field is
  `player_index`, and the smoke test asserts `pop_race` and
  `POP_MASK_RACE` do not come back.

  A third meaning shares the nibble: `Sum_Colonists_`
  (colony.cpp:2129) matches `>= 14` against a race index directly,
  bypassing the player lookup. So the nibble is not bounded by 9, and
  14 or 15 in live data is a fourth state rather than corruption —
  while 10 to 13, which no branch found reads, would be.

  Both steps are on the wire already: this nibble, and
  `s_player.race` at offset 37 in the verified `player.py` spec. So
  race shading is reachable once the nibble is confirmed; it is the
  nibble that is missing, not the second step.

  `tools/struct_probe.py colonies --pop-nibble` runs the prediction
  the reference save CAN answer: across all 21 colonies, including
  the AI's, the nibble should equal each colony's own `owner`. That
  is falsifiable without a single android, because the AI colonies
  carry owners other than 0 — under the "race" reading the nibble
  would not track the owner across them. Half of the prediction is
  already recorded in `doc/s_colony_offsets.md`: 598 colonists across
  two samples, nibble never above 9. The owner match is the
  discriminating half and was never checked.

  It reports counts and a per-owner table, never a verdict alone,
  because **a wrong mask scatters rather than failing cleanly** — a
  spread across many values is a different fault from a few values
  clustered near the owners, and a pass/fail line throws away the one
  signal that separates them.

  **Run on 1 September 2026 against the reference save, and the race
  reading is refuted.** 21 colonies, 131 live colonists, five owners:
  owner 0 -> nibble 0 (x39), 1 -> 1 (x22), 2 -> 2 (x25), 3 -> 3
  (x28), 4 -> 4 (x17). Zero mismatches, nothing outside 0..9, 751
  unused slots all zero. The 39 for owner 0 agrees with the empire
  sidebar Population recorded when `owner` and `n_pops` were verified
  — a different field in a different struct.

  The decisive part is the second query: `s_player.race` for those
  five players is 5, 2, 3, 4, 0 (CyberToller, Darlok, Elerian,
  Gnolam, Alkari), and **not one player's race equals its own
  index**. Player 0 plays race 5, so a race nibble would decode his
  colonists as 5; they decode as 0. Player 4 plays race 0 and decodes
  as 4. The two readings predict a different number for every player
  here, and all 131 colonists follow the owner. Without that second
  query the correlation would have been suggestive and nothing more —
  it is the one check that separates "the nibble is the owner" from
  "the races happen to be numbered like the players".

  So the nibble has two independent sources for 0..7 and is no longer
  a bare transcription. **The sentinels are still not verified**: 8, 9
  and >= 14 do not occur in this save, so `Get_Effective_Pop_Player_`'s
  branch at colony.cpp:1261 stays untested and needs a savegame with
  androids, natives or a conquered population.

  Consequence for the colony list: race shading is now unblocked in
  principle for single-race and multi-player colonies — nibble ->
  player -> `s_player.race` — but NOT for androids and natives, which
  are exactly the cases the shading was wanted for. Not built.

- **The old note, still true of the sentinels.** Every colonist in the one
  savegame checked is race 0, so nothing there could confirm
  `MASK_RACE` or refute it. Until it is settled: the list draws no
  race shading and no locked androids or natives, and the bar takes
  the population limit for the colony owner's race instead of the
  best over the races present — `Planet_Max_Population_For_Player_`
  walks those races through the mask. What settles it is a savegame
  holding androids, natives or a conquered population, not another
  turn, since the race mix does not change across one.
- **`tech_applications` has no verified offset** in
  `core/structs/player.py`, which does not expose the field at all.
  Advanced City Planning therefore does not add its flat +5 to a bar,
  so every bar on a colony of a player who has researched it is five
  squares short. Confirming that offset is the whole fix; inventing
  one to make a bar longer is the trade decision 23 forbids.

  Both deviations shorten a bar rather than lengthen it, which shows
  as a bar that cannot hold its own squares — visible, and asserted
  by a smoke rule — rather than as a quietly wrong length.

- `s_leader_data` for the Officers screen. `tools/struct_probe.py
  --spec` now decodes any record against its spec, so the 64-byte
  ceiling on the int16 column view no longer stands in the way.

**THE SCANNED COLONY'S NAME IS BRIGHT — TRANSCRIBED, and what is
transcribed is the RELATIONSHIP rather than the RGB.** 9 September
2026. `COLSUM::Draw_Colony_Summary_For_Colony_` calls
`COLONY::Set_Colony_Font_To_Blue_(2, colony_idx ==
COLONY::_g_colony_n)` (colsum.cpp:554), which picks
`_font_bright_color_array` or `_font_color_array`
(colony.cpp:533-546). **The driver is the scanned colony**, the same
`_g_colony_n` that fills the description panel
(`Draw_Colony_Scan_Info_`, colsum.cpp:1155), so the name colour and
the panel read ONE state — `colonyselect.Selection.colony` — and a
smoke check asserts they cannot disagree.

The original's own values, two sources agreeing exactly: the arrays
are palette indices `{245, 253, 252}` and `{244, 133, 132}`
(colony.cpp:139, :141), and measured off its framebuffer the scanned
row's ink is (128, 160, 188) and every other row's (108, 104, 140) —
indices 133 and 253, which is also what settles that slot **[1]** is
the glyph and [0] the shadow.

**THE CHOICE, because it is a choice.** This screen draws in the
project's own palette (decision 34), and the original's dimmed value
is 109 luma against a panel lighter than HD's `8, 11, 20`. So the
scanned name keeps the colour the list already had, (206, 216, 238),
and the dimmed one is that colour at the original's own dim/bright
luma ratio — 0.7115, giving (147, 154, 169), measured back at 0.7128
after integer rounding. Adopting the absolute values would be
answering a different question: how bright a name should be on THIS
panel, which is decision 34's territory and not this transcription's.
The alternative is recorded rather than merely rejected, in
`colors.json` under `_row_name_note`, so a later session can take it
without re-deriving the argument.

A COLOUR AND NOTHING ELSE: no rectangle, no frame — the only
`Fill_`/`Line_` calls in `colsum.cpp` are the scroll thumb (:759-765).

**"No Farming" beside the original — answered 9 September 2026, and
the Part G gap closes.** It could not be asked on the reference save,
whose every `max_farms` is 255; it was asked on `natives_autosave`,
where Neptunus I and Piatuos I carry 0. Both halves from one snapshot,
the game's records verified byte for byte against the fixture before
and after.

**POSITION: transcribed, and it matches.** The original centres the
label in `left_x..right_x` — 101..226 for farmers, `right_x` being the
next column's `left_x` minus 10 — through
`Squeeze_Print_Paragraph_(left_x, top_y + 5, right_x - left_x, 28,
E_Strings_(387), 2)`, where the 2 selects
`fonts::Print_Centered_(x + width/2, y, str)` (coldraw.cpp:315-321).
Measured on its own framebuffer: ink centre native **162.0** against
the 163.5 that expression computes, one glyph's rounding. HD's label
centres at **0.4985** of its FARMERS column against the original's
0.4962 — the two columns differ by the 10 px gap the original leaves
between them and HD tiles over, and the centring rule is the same one.
Vertically HD sits at band +10 of 65 against the original's +5 of 31.

**SIZE: the known gap, unchanged and still owed.** HD's label is 45 %
of its column (ink 157 px of 343) against the original's 57 % (77 of
133). That is `colonylist.NO_FARM_FONT_REF`'s row-to-column
magnification mismatch, and it rests on `NATIVE_LABEL_CAP` — 10 px of
cap height measured off a picture, because font style 3's height
lives in the player's FONTS.LBX and is in no source this project can
read. **The font extractor is owed twice**: here and for the name cap
(`namestar.cpp:246-256`).

### Where the briefs and work orders are

**`doc/briefs/`** — 102 briefs (and the pictures of briefs 92, 95, 97 and 101) with a README that indexes them. Data's
decision of 9 September 2026, and it closed a gap that had been open
since the project started.

Until that evening they were not in the tree and never had been. The
only copies were Claude Code's cache of the chat pastes,
`~/.claude/paste-cache/<hash>.txt` — hash-named, undated inside, in a
directory nothing in this project reads and nothing here would notice
being pruned. A handover of that day called four of them "in the
tree"; none was, and the tree cited nine brief filenames of which none
existed as a file.

Eight of those nine now resolve; `doc/briefs/README.md` carries the
mapping. **The ninth never had a text to import**:
`brief_pop_sprites_assets.md` is named by
`doc/briefs/75-brief-four-parts-three-commits-one-stop.md` and by
nothing else, and whatever it asked for reached the tree only as
decision 50's withdrawal of it. Both places that cited it by name now
say what happened instead of pointing at a file a reader cannot open.

Content is byte for byte what arrived. **Dates are stated only where
the brief's own text carries one** — twelve of the hundred and two; everything
else is undatiert, because a date has to come from the brief or from
the first commit that implements it, and a cache file's timestamp is
neither. The numeric prefix is order, not date.

Two cache files were not imported: they are passages of this tree
pasted back into chat for reference (decision 46's text, and "How work
arrives, and who owns what"), not instructions. Named in the README.

### Acceptance fixtures — the THREE savegames, by name

Recorded 5 September 2026. They live in **`~/orionlayer-fixtures/`**
with a README of their own, and NOT in the repository: a savegame is
the player's own game data, the same line decisions 40 and 42 draw
for the help texts and the nebula sprites. What is in the repository
is the identification, so a run can say whether it is measuring the
save it thinks it is.

| Fixture | Stardate | sha256 (first 16) | What it is for |
|---|---|---|---|
| `fixture_reference_3502.4.GAM` | 3502.4 | `ab70cc9ad5442335` | the move chain. 11 colonies, single race, **no native, no android, no conquered, every `max_farms` 255** — every plan it can produce predicts "all" |
| `fixture_natives_3502.5.GAM` | 3502.5 | `b1f1aa466716d6c0` | population identity. Player 0 Elerian; 8 colonies; **Urna I is the only mixed one**, 1 pop of nibble 0 against 3 of nibble 9, and a real four-cell row. Also the only save with `max_farms == 0` colonies (Neptunus I, Piatuos I) — see the closed item below
| `fixture_natives_autosave_3502.4.GAM` | 3502.4 | `2610f39c00f68ebe` | the turn BEFORE `natives`, and a COPY of the game's own `SAVE10.GAM` — **secured 9 September 2026**, because that slot is the autosave and the game rewrites it at every turn end. Seven player colonies, no Urna I, Rha IV at four pops. The `pick_round` and `pick_hd_*` evidence was taken on it, and it is the ONLY fixture that can show **No Farming** — Neptunus I and Piatuos I carry `max_farms == 0` where the reference save has 255 everywhere. `tools/fixtures` points at the copy and a smoke check refuses any fixture path that reaches into the game's folder. | |

In-game names `"claude nicht lschen"` and `"2Natives"`; the originals
were slots `SAVE8.GAM` and `SAVE2.GAM`. **Anything below that reads a
save reads it by its fixture name**, because a test whose data lives
only on one disk answers differently for everybody else — the
help-file lesson, one domain over.

Zhadoom III (14 pops) is the widest row in either fixture and is
therefore the narrowest-cell case any picture has to survive.

### Claude Code loads saves and restarts the game — 10 September 2026

**Data's decision.** Until now the convention was that Data loaded
the save and Claude Code measured against whatever was in front of
it; every brief that touches the game says "reference save loaded as
slot 8" as a precondition somebody else arranged. Session 2 needed
two different saves and four engine restarts — a patch cannot be
live-verified without rebuilding and restarting — so the convention
was in the way of the work rather than protecting anything.

**Two conditions, and they are the whole of it.**

- **The report names the slot and the fixture for every live step.**
  Not "on the reference save": slot 8, `fixture_reference_3502.4.GAM`,
  `verify_colonies` green before and after. A measurement whose save
  a reader has to infer is a measurement they cannot repeat.
- **`SAVE10.GAM` is checked against the secured fixture copy before
  and after.** That slot is the game's autosave and it is rewritten
  at every turn end, which is why the fixture is a COPY at
  `~/orionlayer-fixtures/` and why `tools/fixtures.py` refuses any
  fixture path reaching into the game's folder. A session that
  restarts the game repeatedly is exactly the one that could lose
  it without noticing.

Loading is done through the Extension API's own field activation —
the main menu's Load Game field, the slot, then `L` — and not by
writing save files. Nothing in the tree writes into
`~/Master of Orion 2/`.

### The pop move is one command, and the click chain is gone — 10 September 2026

Brief 90 Session 2, after Data read Run A and decided all-or-nothing
(fundament 52). `doc/ext_move_pop.patch` is applied to the local
orion2re tree and the engine is rebuilt; the patch is a REQUEST
upstream, filed as item 12 in `doc/orion2re_open_fixes.md`.

**MEASURED, on the reference save, ten runs each.**

| | click chain (Part I) | one command |
|---|---|---|
| five-pop move, last row | **725 ms** median | **55.4 ms** median |
| snapshot rounds | 4 (RESORT, ESTABLISH, PICK, DROP) | **1** |
| same move, FIRST row | faster — ESTABLISH is shorter | **55.4 ms**, identical |

The first/last row figures are the finding, not the headline number:
the whole difference between a near row and a far one WAS the
window-stepping, and there is no window to step now.

**LIVE VERIFICATION — WHICH RULE ON WHICH SAVE.** Every run began
from a freshly loaded slot with `fixtures.verify_colonies` green,
and ended with it green again.

| rule | save | slot | result |
|---|---|---|---|
| 1 — native to research/industry | `fixture_natives_3502.5.GAM` | 2 | **VERIFIED**: refused, colony 37 (Urna I) unchanged, all 38 records still match the `.GAM` |
| 2 — android reconfigure | — | — | **NOT VERIFIED, no fixture has an android pop.** Nibble 8 appears nowhere in any of the three saves, across all 42 pop slots of every colony. Stays on the open acceptance list |
| 3 — the 42-job cap | — | — | **NOT VERIFIED, not reachable.** The biggest single-job count on any player colony is 12 of 42 (reference) and 10 (natives) |
| 4 — `max_farms == 0` into food | `fixture_natives_3502.5.GAM` | 2 | **VERIFIED**: refused on colony 22, nothing moved |
| all-or-nothing | `fixture_natives_3502.5.GAM` | 2 | **VERIFIED**, and the engine log shows it: a list of one legal entry plus one native refusal logged `refused after 1, rolling back` — the legal pop HAD been moved and was put back |
| a legal multi-pop move | both | 2, 8 | **VERIFIED**: three farmers to industry on natives; five pops both directions, ten times, on reference |

**AND THE `natives` FIXTURE HAD NO NATIVES, because the table was
cutting them off.** `FIXTURE_FILES["natives"]["colony_count"]` and
`FIXTURES["natives"]["colonies"]` both said **36**; the engine
reports `num_colonies` **38** on a fresh load, and record 37 —
`607 + 37 * 361` in the file — is **Urna I**, four pops, nibbles
`[0, 9, 9, 9]`, which is exactly what open fix 11 and this
document's own fixture table describe. So:

- `fixture_colonies` returned 36 of 38 records with no error, and
  `verify_colonies` — run before every measuring run since it was
  written — was checking 36 of 38 colonies and calling that a match;
- `fixture_name` could not identify the save AT ALL while the number
  was wrong, which is how it went unnoticed: it failed by returning
  `None`, and nothing treats `None` as a fault;
- rule 1 was about to be filed as "no fixture has a native", which
  would have been a false entry on the open list derived from a
  wrong count rather than from the save.

Both numbers corrected to 38 against the running game. The two
other fixtures were checked the same way and are right.

**WHAT THIS SESSION DECIDED THAT DATA DID NOT**, each with its
reason, because a decision recorded only in a report is one the next
reader re-litigates:

- **The wire shape is `int16 colony_idx, uint8 count, count x (uint8
  pop_idx, uint8 job)`.** Fundament 52 fixed the SHAPE — one colony,
  a list — and not the encoding. Bytes for the pairs because
  `s_colony::pop[42]` (orion2.h:497) caps both fields well under
  255, and `int16` for the colony because that is the type
  `Give_Colonist_New_Job_` takes.
- **The parse buffer went from 8 bytes to 256.** The worst case is
  3 + 42*2 = 87. 256 is that with room and no arithmetic to get
  wrong later; the oversize branch still drops the client rather
  than reading on, so the cap is a guard and not a limit anybody
  should be near.
- **Three guards in the handler are OURS, not transcriptions**, and
  are marked as such in the patch: the colony must belong to the
  local player, the indices must be in range, and the game must not
  be holding a cluster. The original reaches this code from a screen
  that cannot show another player's colony and cannot have a cluster
  in hand at the same time. An API can be sent anything.
- **The rollback saves the whole `pop[]` array, not just the listed
  pops.** Data's instruction, and the reason is in the handler's
  header: 42 words is nothing, and a rollback that covered less than
  the call can touch would have a hole in it — what
  `Give_Colonist_New_Job_` writes is the engine's business to change.
- **The sort-state finding moved rather than died.** The sort STEP
  went with the chain; the finding that `_g_sort_index` is on
  neither channel is about the API, so it is now in
  `colonyselect.py` beside decision 46's other not-on-the-wire
  state, and the smoke check that held it was retargeted, not
  deleted.
- **`STEP_UP_XY` / `STEP_DOWN_XY` became `colonyscroll.ARROW_UP_XY` /
  `ARROW_DOWN_XY`.** They are the original's own two list arrows and
  `colonyscroll` is the only caller left; leaving them in
  `colonysend` would have been a second home for coordinates whose
  feature had moved.
- **`tools/colony_drop_timing.py` is kept, with a dated note.** It
  measures the ENGINE's click path, which still exists, and it
  produced the before-value the command is judged against. A
  measurement tool whose output is still cited is not dead code.

**WHAT THE HD SIDE LOST.** `colonysend.py` went 509 -> 279 lines.
`RESORT`, `ESTABLISH`, `PICK`, `DROP`, the window-stepping plan and
the pick-up interlock are deleted — not kept as a fallback, because
two paths that move pops is the duplicate this project keeps paying
for. `held_cluster` stays: nothing HD does can create a held cluster
now, and the engine refuses the command while one exists, so it is
what lets HD name that state instead of reporting a move that
quietly did nothing.

### Run A — what one command would buy, and the four source answers — 10 September 2026

`doc/briefs/91-colony-runs-and-doc-audit.md`, Run A. Source reading
only: **no patch, no HD code, and fundament entry 52 is not written
here** — it is written after Data has read this, with its number
re-checked at that moment.

**THE PART I TEN-DROP TABLE, BROUGHT IN FROM THE COMMIT MESSAGE.**
Run A asks for a paragraph "filed beside the table in the status
document" and the table was not in this document — it lived only in
`ec6fd98`'s commit message. A measurement that can only be found by
knowing which commit to read is not filed. Reproduced verbatim, not
re-measured (Run A: do not re-measure):

| step | before ms | after ms | states | visuals | floor? |
|---|---|---|---|---|---|
| pick click (local) | 57 | 57 | 1 | 1 | yes |
| held | 0 | 0 | 0 | 0 | yes |
| drop click | 84 | 84 | 1 | 1 | yes |
| RESORT | 54 | 28 | 1 | 1 | yes |
| ESTABLISH | 163 | 162 | 2 | 2 | yes |
| PICK | 194 | 193 | 3 | 3 | past |
| DROP | 217 | 214 | 3 | 3 | past |
| finished | 0 | 0 | 0 | 0 | yes |
| **total median** | **758** | **725** | | | |
| **HD share** | 289 (38 %) | 274 (38 %) | | | |
| **GAME share** | 469 (62 %) | 451 (62 %) | | | |

**3a — WHAT A DIRECT COMMAND REMOVES, AND WHAT IT CANNOT.** Four of
the eight rows are the click chain's own and exist only because the
move is addressed by a click into the game's ten-row window:
**RESORT 28 ms** (injects the sort key so HD's row order matches the
game's, needed only because a click addresses a SLOT and not a
colony), **ESTABLISH 162 ms over two messages** (steps `_first`
until the target row is inside that window — decision 46's
machinery), and **PICK 193 and DROP 214, three messages each** (the
two injected clicks and their waits). Together **597 ms of the
725 ms median**, and they go away with the chain, not with a faster
wire. What does NOT go: the **57 ms local pick** and the **84 ms
from the drop click to the send's first state** are HD's own
scheduling on this side of the socket and are untouched by anything
in Joes' tree; the **recalculation** is one
`COLONY::Col_Calc_Wrapper_` per affected colony
(`colmove.cpp:461-464`) and costs the same however the job change
arrives; and the **snapshot cadence** still owes one state round
trip before HD may draw the result, because HD does not draw
optimistically. The floor is therefore **one send plus one
confirming snapshot** — the table's own single-message steps sit at
57 to 84 ms — on top of the 141 ms of HD front-end that stays.
**The 62 % the game holds is not what this patch is buying**: it is
buying the four chain states, and the honest claim is a drop that
costs roughly one step instead of four, not a fast drop.

**3b — THE FOUR ANSWERS, each from the function that builds the
thing.**

**(1) What `Give_Colonist_New_Job_` reads besides its arguments:
nothing that belongs to a screen.** `colmove.cpp:518-557`. It takes
`colony_idx, pop_idx, new_job, inter_colony_transfer` and reaches
only for state those arguments address —
`MOX::_colony[colony_idx].pop[pop_idx]` and `.max_farms`,
`COLONY::Pop_To_Pop_State_` (`colony.cpp:1240-1255`, pure: the pop
word's low nibble and nothing else) and `COLONY::Sum_Colonists_`
(`colony.cpp:2112-2149`, walks that colony's own `pop[]` and
`MOX::_player[]`). **`COLMOVE::_cluster_colony_n` is not read, no
COLSUM or COLMOVE global is read, and no screen state is read.** It
writes exactly two bit-fields, `POP::Set_Prof` and
`POP::Set_Assigned` (`colmove.cpp:549-551`). Addressed by index, it
is already the function a command wants.

**AND THE ONE THING THAT DISQUALIFIES CALLING IT BLIND: all four
refusals are BLOCKING UI.** `colmove.cpp:527`, `:534`, `:541` and
`:556` each call `GENDRAW::Help_`, which is `Message_Box_`
(`gendraw.cpp:18-24`) -> `TEXTBOX::Do_Text_Box_(nullptr, text, 0)`
(`textbox.cpp:175`) -> `Text_Box_Get_Input_(0)` (`textbox.cpp:251`),
whose zero-ticks path is a spin loop that **waits for a human**:
`do { … } while (fields::Get_Input_() == 0)` at
`textbox.cpp:145-149`. A handler that called
`Give_Colonist_New_Job_` on a refusable move would stop the engine
until somebody dismissed a box the HD player cannot see — and worse,
that inner `Get_Input_()` re-enters `ext::Tick` and drains further
commands from inside the refusal. So the command must decide the
four refusals ITSELF and answer over the wire, or call a
refusal-free inner form. This is decision 33 arriving as a hard
requirement rather than a preference: HD already refuses before
sending, and now the engine side cannot afford it not to.

**(2) The recalculation is PER BATCH, and the source is explicit
about it.** `Give_Colonist_New_Job_` never calls it. `Send_Cluster_`
runs its whole `while` loop over the cluster and only then calls
`COLONY::Col_Calc_Wrapper_(_cluster_colony_n)` and, if the
destination differs, again for it — `colmove.cpp:461-464`, after
the loop closes at `:459`; the early-exit path does the same at
`:145-148`. `Col_Calc_Wrapper_` (`colony.cpp:1091-1106`) is
`COLCALC::Colony_Calculation_` plus a branch guarded by
`COLONY::_move_colonist != -1 && COLONY::_field_mode == 1` — the
click chain's own state, which a command handler never sets, so
only the calculation runs. **A list command is therefore correct
and cheaper: N job changes, one recalculation per affected
colony.**

**(3) A new command byte goes in `ProcessInput()`'s drain loop as
its own `case`, and it does NOT need `g_pending_field`.**
`src/ext/ext_api.cpp:223-319`; the loop is
`while (g_server.PopInput(cmd))` at `:224`, so **five commands in
one tick already all land**. `g_pending_field` exists for one
reason and it is not write safety: `MSG_ACTIVATE` has to impersonate
a field click, and the value must come back as `Get_Input_`'s RETURN
value — the comment at `:229-230` says not to set
`_last_button_number` directly because `Interpret_Mouse_Input_()`
overwrites it. A job change returns nothing to the game's input
machinery, so it writes and is done. **Timing is favourable:**
`ProcessInput` runs from `ext::Tick` (`ext_api.cpp:341-349`), which
`fields::Get_Input_` calls at `fields.cpp:167` — and the colony
summary's loop is `Get_Input_()` at `colsum.cpp:159` followed by
`Draw_Colony_Summary_Screen_()` at `:171`, so a write in the drain
loop is drawn in the **same** iteration.

**(4) The game's own screen redraws from `pop[]` with no cluster
state, and nothing caches the row.** `colsum.cpp:468-470` calls
`Draw_Colony_Summary_For_Colony_(i)` for all ten slots
**unconditionally** — outside both `if (COLONY::_full_draw != 0)`
guards at `:458` and `:474` — so the rows are redrawn every pass
whatever the dirty flag says. The pop drawing itself
(`COLDRAW::Do_Colony_Info_Pop_Stuff_For_Pop_`,
`coldraw.cpp:281-444`) reads `MOX::_colony[colony_idx].pop[pop_idx]`
at `:332` and filters on that word's own bits — `0xf`, `0x180`,
`0x200`, `0x400` at `:333-337`. **`_cluster_colony_n` does not
appear in `coldraw.cpp` at all** (zero occurrences). The only screen
globals in the loop are `COLONY::_scanned_pop` and
`COLONY::_g_colony_n` at `:341`, and they choose a hover
highlight, not what is drawn or where. `pop_index_by_slot[]`
(`:354`) is filled BY the draw and rebuilt each call — an output,
not a cache. Corroboration from the other side: the plain
same-colony job change in `Send_Cluster_` sets no `_full_draw` and
the row still updates.

**3c — PROPOSED COMMAND SHAPE: a LIST, one message, one colony.**

    MSG_SET_JOBS   colony_idx : i16
                   count      : u8
                   [ pop_idx : i16, new_job : u8 ] x count

**Why a list and not one pop per command.** (2) is the reason: the
recalculation is per batch in the original, so a list reproduces the
engine's own grouping, while N single commands would run
`Colony_Calculation_` N times — that is not merely slower, it is a
different sequence of intermediate states than the original ever
produces, and this project's rule is to transcribe the shape and not
just the outcome. A five-pop cluster is the common case and it is
one move to the player.

**Why one colony per command.** `Col_Calc_Wrapper_` is called per
colony and the inter-colony path is not a job change at all — it is
`SETTLER::Pop_Tries_To_Settle_` and `Settle_Pop_`
(`colmove.cpp:278-279`), with eleven refusals, an ETA and two
confirmation boxes. Folding that into this command would smuggle a
second, blocking feature in behind a field. Population TRANSFER
stays out and gets its own decision if it is ever wanted.

**Why the handler must carry the refusal checks.** From (1): the
four refusals inside `Give_Colonist_New_Job_` are blocking text
boxes and re-enter the drain loop. The handler validates first —
native to research or industry, android reconfigure, the 42 cap,
and the `max_farms` food rule, all four readable from `pop[]`,
`max_farms` and `Sum_Colonists_` without drawing anything — and
either applies the WHOLE list or applies none and answers with the
refusal. All-or-nothing is the honest half: the original's
`Send_Cluster_` `return`s mid-cluster on a refusal
(`colmove.cpp:168-173`), leaving some pops moved, which is the
behaviour HD already mirrors as a COUNT rather than a boolean — but
that partial state exists because a click chain cannot ask first,
and a command can. Answering "moved 0, refused by rule 1" is
strictly better than reproducing a half-move, and it is the one
place this proposal deliberately does not transcribe. **Flagged as
such rather than slipped in: it is Data's call, and if she wants
the original's partial move the handler returns the count instead.**

**What this does NOT propose.** No framebuffer change, no new
serialization, no field-list change. `MSG_SET_JOBS` writes `pop[]`
and calls `Col_Calc_Wrapper_` once per touched colony; everything
HD learns afterwards it learns from the snapshot it already reads.

### The list geometry becomes six boxes and a row count — 8 September 2026

**Six column boxes**, `col_name` / `col_farmers` / `col_workers` /
`col_scientists` / `col_building` / `col_scroll`, in `boxes.json` and
F5-draggable like anything else. **One rect source per column**: the
header plate above a column, the cells inside it and the drop target
over it all read the same box, where the header used to tile its own
box from a ref-width table and `colonytrack` tiled a second one.

**The scroll slot is a box too**, deliberately: `colonyscroll` draws
its arrows there and `colonyheader` draws a plate there, so making it
"the remainder" would have given one column two rect sources.

**Only the LEFT EDGE is read.** A box carries four numbers and three
would be a second answer: y and height are `list_area`'s because a
column is a strip of the list, and the WIDTH is the distance to the
next column because the six have to tile the window exactly. Reading
the stored width opened a one-pixel seam at 1280x720 —
`Box.update_layout` truncates x and width independently, so
`int(x*s) + int(w*s)` and `int((x+w)*s)` disagree wherever the
fractions add up. Dragging a column moves a BOUNDARY and its
neighbour follows; `colonyheader.sync_columns` writes the derived
width and the window's y and height back, so the outline shows what
the geometry did rather than what was dragged.

**Derived, never serialized:** the row band (`list_area` height
divided by `list.row_count`, the last band taking the remainder), the
figure step, the cell rect, the drop rect, the plate rect, the figure
origin, the squish pitch and the name block. **`list.row_count = 10`**
is the one value, and it is the original's own window
(`_list_col[10]`, colsum.cpp:348).

**Nine values died**: `row_height`, `pad_x`, `pad_y`, `name_width`,
`name_gap`, `bar_height`, `tail_width`, `building_width`,
`growth_gap`. Every one answered a question a box or the row count
now answers. `row_height` 58 with a 14 px pad happened to yield ten
rows at all three shipped resolutions — by arithmetic coincidence,
and nothing in the tree said which of the three numbers was
load-bearing.

**The hand-written `FIGURE_STEP` table is gone too**, and so is
`layout_reference.figure_scale`, which was the same table in the
design input. The step is the largest whose `28*step` fits the band
under the plate's 1 px line. **Step 1 joined the ladder**: a master
is 28 px and below the reference resolution that is the right answer
— at 1280x720 the band is 42 device px and even a 2x figure needs 57.
It is NOT on `colonyfigures.STEPS`, which is what a MOD may ship as
an explicit `@Nx` file, because `@1x` would be a second name for the
master (decision 50).

**The deviation table, per column.** The transcription is in
`core/zoomtables.NATIVE_JOB_COLUMNS`: `COLSUM::Get_Selected_Pop_`
(colsum.cpp:1006-1024) gives `left_x` 101 / 236 / 378 with `right_x`
= the next `left_x` − 10, and the drawn spans measured off
`colony_summary_native_split.png` are **135 : 142 : 134**, with
WORKERS the widest. **What the original states is that RATIO and not
a width** — HD's job columns are 2.53x their native ones by Data's
Stage 1 decision, so the absolute number is ours. Today's boxes:

**RE-SEATED TWICE ON 12 September 2026** — first for the static
frame's narrower list (1404 ref px), then for Data's new frame, whose
list is **1718** because the right-hand column is gone. The DERIVATION
did not change either time and neither did a single source: the scroll
column keeps its transcribed 27 off the top, **the building column
keeps its 267** (Data's decision, the width it already had), name and
the three jobs split what is left in the proportions they had, and the
three jobs split their share by the original's own ratio. What changed
is one number upstream of all of them.

| column | ref width | against the transcription |
|---|---|---|
| `col_name` | 321 | no native share — DEVIATION, reason in `_list_columns_note` |
| `col_farmers` | 364 | +0.1 % of the 135 share |
| `col_workers` | 382 | −0.1 % of the 142 share |
| `col_scientists` | 360 | +0.0 % of the 134 share |
| `col_building` | 268 | wider than the 13.3 % the original requires — DEVIATION, reason recorded; **+9 on 9 September 2026**, the px `col_scroll` gave up when its width became a transcription, sent here because this column is already the declared home of this screen's surplus |
| `col_scroll` | 27 | **TRANSCRIBED since 9 September 2026** — native 619..627. Arrow field x 619 (`Add_Button_Field_`, colsum.cpp:263-264) and the track it holds at 621..626 (`Add_Scroll_Field_`, colsum.cpp:278, counted exclusively as 5; `Fill_(621, y1, 626, y2, 229)`, colsum.cpp:759, counted inclusively as 6). The anim's own extent is `animate::Get_Width_(pic)` and lives in the player's LBX, so the right edge is MEASURED off `colony_summary_native_split.png` — its LEFT edge reproduces the source's 619 exactly, which is what anchors it. Was 36 = the leftover after the other five |

The check reports every column and goes red only where a deviation
past one per cent is unmarked. **AND IT HOLDS THIS TABLE TO
`boxes.json` SINCE 9 September 2026.** Every width above is a number
somebody typed into a document, and this one went stale within the
hour: `col_building` and `col_scroll` changed in the commit that
transcribed the scroll column and the table still said 315 and 35,
with the scroll row still claiming "no native counterpart" for a
column that had just acquired a source. A hand-copied number without
a checker is this project's oldest recurring fault and the smoke
suite already carries two instruments against it (the engine version,
the check count); this table now has the third.

**FIFTY PLATES, AND A DEVIATION IN KIND.** FIVE columns times the ten
bands of `list.row_count` — **corrected 9 September 2026, and the
scroll slot is the one that left.** It was plated per band like every
other column, which drew ten stacked boxes where the original has a
single continuous channel with a slider in it
(`COLSUM::Draw_Bar_Indicator_`, colsum.cpp:747-771). That is
`colonyscroll.track` and `colonyscroll.slider` now, and the marker in
`colonylist` that said the slider was NOT DRAWN went with it. (*Sixty
for one day, between the plate fix and the slider; fifty before that,
which was five columns times ten and right for the wrong reason —
`col_scroll` was not being counted because empty bands were not being
plated at all.*)

**THE SLIDER IS TRANSCRIBED.** Position from `_first`, extent from the
visible-to-total ratio: `y1 = 271 * _first / n + 40` and
`y2 = 271 * (_first + 10) / n + 40` (colsum.cpp:752-753), where 271 is
the track's own height and 40 its top, so the expression is
`track.h * first / n + track.y`. The 10 is `colonyfirst.WINDOW`, the
ORIGINAL's window from `_list_col[10]` — the same number as HD's
`row_count` today and not the same fact (decision 46's corollary).
**Nothing at all is drawn below ten colonies**, not even the track's
four corner dots, because the original's whole block sits inside
`if (num_colonies >= 10)` (colsum.cpp:751); `colonyfirst.NOT_DRAWN`
already encoded that for the reading direction. Colours are the
palette indices 229 / 230 / 228 and the dots' 80, resolved against the
game's own live palette — and they are ABSOLUTE rather than a
relationship, unlike the name colours, because `colonyfirst` reads
index 229 back off the framebuffer to recover `_first` and a different
blue would make the drawing and the reading disagree.

**`first` IS HD'S OWN VIEW**, which decision 46 permits: the original's
slider reports the window its own rows come from, and so does this
one. While the two windows are decoupled they can differ, and a slider
reporting the other one would be the one that disagreed with the rows
beside it.

**STILL NOT DRAWN, and still recorded at three homes:** the per-row
BUY button the original adds at native x 599 (`_list_buy_fields`,
colsum.cpp:302). See `layout.json`'s `list._buy_note`. Every cell
of every band draws one, including the empty rows and including the
NAME and BUILDING columns. (*Written as "fifty" until 9 September
2026, from the five columns that carry content; corrected here, in
decision 51 and in `colonylist` together with the drawing, which had
been plating only the OCCUPIED bands for three days while all three
documents said otherwise.*) **The original has no per-cell drawing call at
all**: `Draw_Colony_Summary_Screen_` blits ONE bitmap —
`animate::Draw_(0, 0, _anims[0])`, COLSUM.LBX entry 0
(colsum.cpp:461, loaded at :404-408) — and the plates are painted
into it. That is why every cell has one whether or not a colony sits
there; they are part of the picture, not a per-row decision. HD
cannot ship that bitmap (decision 42), so it draws them. Marked in
`colonylist.render` — **not `_render_bar`, which is where the loop
used to be and is the whole of why it plated only the rows that had
a colony** — in `layout.json` under `list._columns_note`, here, and
in two smoke checks: one reads the plate's own four edges off the
rendered surface, the other COUNTS the rects at six colony counts
from one to twenty-five. **Decision 51** is
what makes the drawing legitimate: the plate is
`StyleRenderer.draw_plate`, the rect is computed, and the
`max(6, int(10 * scale))` that used to exist in `draw_thin_border`
AND in `colonyheader.render` now exists once, with a grep holding it
there.

**THE FIRST CELL IS ONE PIXEL INSIDE THE PLATE'S LINE, and that is
transcribed too.** The original's icons start at `left_x` — 101 /
236 / 378 — and its drawn cell boxes at 100 / 235 / 377, measured on
`colony_summary_native_split.png`. The same `+1` at the top is what
`figure_step` reserves, and it is why the list needed 638 px rather
than 630.

**THE 79 % RESIDUE IS ACCEPTED, and here is its arithmetic.** A
figure column fills less of itself than the original's does, and the
ratio is `step x native_width / hd_width`. At 1080p the farmers
column is 343 device px against a native 135 at step 2:
`2 x 135 / 343 = 0.787`. The same holds at 2160p (step 4, column
686). At 1440p the list's growth bought step 3 and the ratio is
`3 x 135 / 457 = 0.886`. **It is structural**: the columns are 2.53x
their native width and the steps are integers, so only a step of 2.53
would close it and there is no such step (decision 28 — a sprite is
swapped, never scaled). No spacing is added; the residue is empty
column to the right of each run, which is where the original has its
own slack too, just less of it.

### The list window grows 29 px so 1440p earns step 3 — 8 September 2026

**The measurement that forced it.** Ten rows is the original's window
(`_list_col[10]`, colsum.cpp:348), so the row band is the list
divided by ten and the figure step is the largest whose `28*step`
fits it. At the old 605 the band was 81 device px at 2560x1440 and
step 3 needs 84, so 1440p fell to step 2 and its figure columns
filled **59 %** of what the original's fill, against 79 % at the
other two.

**The clearance is +8 on top of the +21, and it was measured, not
assumed.** The cell plate is a 1 px line and **46 of the 54 figure
masters carry ink on canvas row 0** — measured over the whole set —
so a figure blitted at the band's top would paint over the plate's
top line. The bottom line needs nothing: every master has at least 3
transparent rows below its ink, which is the same measurement the
row clip already rests on. The rule is therefore `band >= 28*step +
1`, and the smallest list that yields steps 2/3/4 under it is **638
cutout px**, 634 typed plus the 2 px BLEED per side. Bands 63 / 85 /
127, with 6 / 0 / 14 px spare below the figure.

**Where the 29 came from, and the constraint nobody had seen.** Not
the `list_band` rail — Data ruled that out and the A3 numbers
(26 / 28 / 29 / 38) are unchanged and re-asserted. Out of the lower
band's height, 220 -> 191. **But the band's height was pinned by ONE
box**: the galaxy inset was 253 x 200 and its height was described as
fixed by its own aspect, so any growth past 20 px broke it. The
screen has no slack anywhere else either — `18 + 48 + 26 + 605 + 28 +
220 + 29 + 32 + 74 = 1080` and the last term is `ring.bottom`, the
master's own metal, so there is no margin to take.

So the inset is **239 x 189**, the largest pair under 191 whose
aspect is still within a thousandth of the original's coverage
(1.26455 against 1.265134). `planet_output` absorbs the 14 px it gave
up, as `_lower_band_note` says it always does.

**WHAT THAT COST, AND IT IS A MARKED PROPERTY.** At 3840x2160 the
inset box was 506 x 400 device px — the small galaxy's own world
extent at one device pixel per world unit — and a smoke check pinned
it. It is 478 x 378 now and **that property is gone**. It was a
consequence of the box's size and never a requirement of the
drawing: `colonyinset.map_rect` fits 128:91 isotropically on
`min(w/128, h/91)` and no 1:1 relation enters it. The check now
asserts the rule the instance came from — the aspect, and that WIDTH
still binds so the letterbox stays on the vertical axis. The drawn
map shrinks 5.5 %: 257x183 -> 243x173 at 1080p, 514x365 -> 486x346 at
2160p.

**What the reduced band did NOT cost, measured by rendering at all
three resolutions rather than by arithmetic on box heights.** The
sidebar still draws its six rows with no ink on the box edge and no
label touching its value; `planet_output` still draws five; the
description still wraps to five lines and uses 138 of 260 px at
1440p. No font shrank. The first two attempts at this measurement
counted ink bands over the whole screen and answered about the
instrument — they failed at the CURRENT height too, which is the
tell.

**`frame_holes.py --write` kept ZERO non-cutout boxes**, and that is
right rather than suspicious: every box on this screen is a hole in
the plate. The galaxy map's `sb_*` readouts are the case that rule
exists for and they are on another screen.

### The pick round: both frames fall, the pops leave the row — 8 September 2026

The colony row now does what the original does during a move, and
three things it used to do went with the change.

**The held pops LEAVE THE ROW, and there is no `count - n` anywhere.**
`Get_Cluster_` clears bit `0x200` (colmove.cpp:70) and the icon walk's
innermost test is `(pop_val & 0x200) != 0` (coldraw.cpp:336), so a
held pop stops BEING an icon. `colonyrows.build_rows` now takes the
HD selection and does exactly that to a COPY of the words
(`colonymove.held_pops`), and everything else follows for free: the
row is shorter, the squish is recomputed over what is left by the
one function that already served the draw and both hit tests
(`colonyicons.column_pitch`), and `cell_at_x` cannot pick a pop that
is already in hand. **That is the whole mechanism.** A shortened
count computed beside the full one would have had to be subtracted
again in the pitch, again in the hit test and again in the drawing —
four places to keep in step where the original has one bit. A smoke
check asserts the pitch moves to `column_pitch(job, shortened)` and
refuses a `- len(held…)` anywhere on the path.

**Both marks on the row are deleted.** The yellow outline round the
picked cells and the blue frame round the row's drop targets. The
original marks neither: the only `Fill_`/`Line_` calls in
`colsum.cpp` are the scroll thumb (colsum.cpp:759-765). What it draws
instead is the cluster on the POINTER, and that is now transcribed —
`COLMOVE::Draw_Cluster_` (colmove.cpp:7-37), called last with the raw
pointer (colsum.cpp:509-511), each held pop at `x + 5 + 20*k, y - 10`
in ARRAY order. The three numbers and the DEVIATION that multiplying
them by `FIGURE_STEP` is live in `core/zoomtables.py`. **HD hides
nothing:** `Clear_Mouse_Picture_` (colony.cpp:360) REPLACES the
pointer picture rather than removing it, and HD's pointer is already
its own artwork at the original's own 4.38 % of screen height
(`core/cursor.py`), so there is nothing left to swap.

*The picture cannot show the offset and the check can.* A screenshot
of the HD screen has no cursor in it — the pointer is a hardware
cursor and never reaches the surface — so the side-by-side answers
"do the figures hang up and to the right, overlapping" and the smoke
check answers "+5 and -10 times the step, 20 apart, 28*step tall, at
all three steps".

**The three F/W/S markers are gone, marking and all.** They were an
HD EXTENSION standing in for headings a column-less row could not
carry, and Stage 4 gave the row five real columns with those headings
above it; the marking already said "whether they stay is Stage 5's
call". **No invisible button was left behind**: the drop target has
always been the whole column, which is the original's own field —
`Add_Scroll_Field_(left_x, top_y, …, right_x - left_x + 8, 30, …)`
(coldraw.cpp:409), added in mode 1 whether or not the walk drew an
icon. So an empty column accepts a drop in the original too, and
`move._hd_extension_bands` was withdrawn rather than moved: what
survives is a DEVIATION in the rect's HEIGHT, 52 % of the row band
against the original's 97 %. The cells moved left to their column's
own edge, which is where the original starts its icons.

**"No Farming" is centred in the column.** `Squeeze_Print_Paragraph_(
left_x, top_y + 5, right_x - left_x, 28, E_Strings_(387), 2)` and the
2 selects `Print_Centered_(x + width/2, y, str)`. It used to sit
below the bar at the first marker's left edge, argued for on
horizontal budget; the source settles it instead. Measured against
the original's own screen to the pixel: ink centre 163 = `101 + 125/2`,
ink top 136 = `top_y + 5`. **Its SIZE is MEASURED and single-source**
— `Set_Colony_Font_To_(3)` is a style index and the height lives in
the player's FONTS.LBX — so 10 px of cap height off
`colony_summary_native_split.png` is the only number there is, and
`colonylist.NO_FARM_FONT_REF` carries the derivation and the one
proportion it does not reproduce. **A font extractor would turn that
measurement into a transcription and is on the horizon**, not in this
round.

**`planet_info` stops being empty.** The original's scan box is TWO
boxes, filled by one function: the description paragraph at native
(13, 354, 80, 88) and the production rows from native x 106
(colsum.cpp:1155). The description moved into the left panel, the
production stayed in the right, and `colonyoutput.render_for` is now
one call because the original is one call. **The form is
PROVISIONAL**: `output.info_style` renders either the original's own
five lines or the six-row table, both are photographed beside the
native, and Data picks from the pictures. The default is the
transcription because that is this project's default, not because the
question is closed. The move's refusal message still wins that panel
while there is one, and says so.

**What the live runs proved, on the save they name.** The game that
was up carried `~/Master of Orion 2/SAVE10.GAM` — the natives galaxy
one turn before `fixture_natives_3502.5`, now the third entry in
`tools/fixtures.py` as `natives_autosave` — and NOT the reference
save, which no client can load: nothing on the Extension API loads a
savegame and orion2re takes no load-on-start argument. Four gestures
on Draconis III, cluster of four from eight workers: the row drew 4
of 8 at `column_pitch(1, 4)`; a drop into the EMPTY scientists column
moved four pops with every word matching the prediction and one
colony changing; a drop back on the source column and a drop on the
colony NAME each released the selection with nothing sent and no byte
moved. The pops were moved back afterwards, so the game stands where
it did.

**The two put-back cases prove the HD side and not the original's own
re-flag**, and that is said rather than implied: HD sends nothing
there, because `Send_Cluster_(colony, -1)` and `Send_Cluster_(colony,
same job)` both take the branch that sets `0x200` back and consults
no rule (colmove.cpp:161-165), so the array ends as it started and
injecting the pair would create the game's cluster only to release
it. The bytes are unchanged BECAUSE nothing was injected.

**The native pick-up refusal is still unreachable live, and the skip
has a name.** `natives_autosave` has no pop with nibble 9 — Urna I,
the only colony that ever had one, is not in it — and neither does
the reference save. The rule is transcribed in
`colonymove.plan_pickup` (colmove.cpp:59-64) and checked offline
against a synthetic word; what is missing is a save that HOLDS one on
a colony the list draws, which is `fixture_natives_3502.5` and needs
somebody to load it.

**Two tools joined the exceptions list and `tools/fixtures.py` came
out of them.** See the list above.

### Stage A3: every gap became one of the master's rails — 7 September 2026

Stage A2 measured the master's struts and found that no gap was wide
enough for one. **Stage A3 widens the gaps to the struts instead** —
mapped by role, so a gap is no longer a spacing chosen here.

| colony gap | master strut | role | ref px |
|---|---|---|---:|
| header → list | header \| map | a title bar above the main content | 31 px → **26** |
| list → lower band | map \| slot | the main content above the row beneath it | 33 px → **28** |
| lower band → sort row | box \| slot | a **panel** above a button row, which is what this gap is and what map\|slot is not | 34 px → **29** |
| the three band gaps, and sort_bar → return_button | the slot divider | two elements of one row, side by side | 47 px → **38** |

**Rounded DOWN in every case**, so a rail is never wider than the
strut it was measured from. `layout_reference.gaps` holds the four
numbers and a check re-measures the master against them — the same
pattern the ring already uses (decision 36).

**The cost, paid where it is cheapest:**

| | before | after | |
|---|---:|---:|---|
| list height | 652 | **605** | −47 px |
| planet_output width | 746 | **686** | −60 px |
| sort_bar width | 1393 | **1367** | −26 px |
| planet_info, empire_stats, inset | 320 / 320 / 253 | unchanged | fixed by pair and by aspect |
| box heights | 220 / 200 | unchanged | |
| **figure capacity** | 5 | **5** | asserted at all three resolutions |

**The list's width did not change**, so the figure columns did not:
the rails that grew are horizontal, so they cost height. At row
height 58 the list still shows ten rows, which is the game's own
window. The two gaps around the inset are 10 px wider than their role
because the inset is 20 px shorter than its band and centred in it;
that 20 has to go somewhere and splitting it is the least-wrong
place, and the check knows the exception by name rather than
tolerating a range.

**Junctions come from the master's own crossing.** Where a vertical
rail meets a horizontal one, the pixels are the metal between two of
the master's slot buttons where it meets the strip under the map. The
other orientation is that same crop MIRRORED — still only the
master's pixels. **No corner is drawn to fit.**

**The tile's period is gone.** Bare strut texture fell from **2.10 %
of the canvas (44 000 px) to 0.38 % (7 938)**, and the autocorrelation
of its column profile from **lag 64 at 0.92** — the patch's own size —
to **lag 8 at 0.22**. The 64-px repeat that was visible across every
full-width gap is covered by rails.

**And the tool split.** `frame_build.py` passed 300 code lines, so
everything that answers *"what does the master look like"* — ring,
material, bevel hole, rails, crossings, all of it found and none of
it named — is now `tools/frame_master.py` (209), and
`frame_build.py` (165) answers *"how is a plate put together"*.

### Stage A2: the rail rule, and why nothing takes it — 7 September 2026

Every strut of `galaxy_map/assets/frame.png` measured — thirteen of
them, **33 to 52 master px, which is 28.4 to 43.0 reference px** —
and every one carries a lit line on both edges with a moulded ridge
between. The narrowest is the header-to-map strut, 548 x 31 master
px = **26.7 reference px**, and `rail_source` finds it the way the
strut patch and the bevel hole are found: measured, not named.

The rule is a comparison and never a fitting. A gap wider than that
rail gets it laid along its length; a narrower one keeps the line its
bevel already gives it.

**Against this layout, no gap qualifies:**

| gap | axis | ref px | |
|---|---|---:|---|
| header \| list | horizontal | 8 | keeps the line |
| planet_info \| sort_bar, planet_output \| sort_bar, empire_stats \| return_button, return_button \| sort_bar | | 12 | keeps the line |
| list \| planet_info, list \| planet_output, empire_stats \| list | horizontal | 16 | keeps the line |
| the three lower-band gaps | vertical | 18 | keeps the line |
| galaxy_inset \| sort_bar | horizontal | 22 | keeps the line |
| **galaxy_inset \| list** | horizontal | **26** | keeps the line |

**The widest misses the rail by 0.7 px.** That is asserted rather
than noted: a widened gap would start taking rails silently, and the
picture would change without anybody looking at it. The rail path is
exercised on a synthetic 100 px gap in the same check, so the rule is
code and not prose.

`struts()` needed an adjacency filter. Without one the header and the
sort row "face" each other across the whole screen and the tool
reported gaps of 908 px; a gap is a strut only if no window lies
inside it.

**`lay_rail` is a second implementation, and the reason is stated
where it lives:** a rail has two ends and a middle and no corners, so
forcing it through `lay_border` would mean synthesising two corners
the source does not contain — which is exactly what "no invented
pixels" rules out. The third copy of the end/stretch logic is the one
to extract.

**The tile still shows its period.** Rails cover nothing, so the
strut patch remains bare over **2.1 % of the canvas (44 000 px)**,
and the autocorrelation of its column profile peaks at **lag 64 — the
patch's own size — at 0.92**. It repeats, and in the full-width gaps
between header, list, band and sort row it is visible. Two cheap
answers exist and neither is taken here: a larger patch, or mirrored
tiling. Both are polish and polish is a separate decision.

The plate is **byte-identical to Stage A (b4e439e)**, because the
rule laid nothing.

### Stage A: every window gets the master's own light edge — 7 September 2026

**The bevel hole is found, not named**, the same rule as the strut
patch: every hole in `galaxy_map/assets/frame.png` is measured on all
four sides and the one whose four sides agree best is taken, because
a bevel copied from a hole that is bright on the left and flat on the
right would put that asymmetry on every window of the screen.
`python tools/frame_build.py --profiles` printed the measurement.
**That tool is deleted — 12 September 2026, decision 55.** The numbers
in the table below are the record of what was measured on the master
on 7 September; nothing re-derives them, because nothing nine-slices
that master any more.

| master hole | L | R | T | B | agreement |
|---|---:|---:|---:|---:|---:|
| header 548x53 | 49/0 | 51/0 | 74/0 | 86/1 | — a side with no lit edge |
| map 1691x988 | 72/1 | 130/1 | 162/1 | 82/1 | 1.91 |
| **sidebar 303x758** | **162/1** | **110/1** | **74/1** | **97/1** | **2.20** |
| box 307x171 | 98/1 | 4/0 | 8/0 | 64/1 | — |
| six slots | 60..177 / 1 | 29..180 | 44..74 | 54..120 | 0.00..2.05 |

Height over width, in master pixels. **The master's bevel is ONE
pixel wide on every hole that has one** — a single bright line
against a plateau of luminance 2 — which is why `BEVEL_MASTER` is 3:
that line plus the two pixels of falloff behind it, and no more.

**One function lays the ring and every bevel.** They are the same
operation — take the band a source image puts around a rectangular
opening and put it around another rectangle — so `lay_border` does
both, corners lifted whole and scaled once, edges stretched along
their own length only. A second implementation would have been the
second copy, and the second copy is where a difference gets in.

**The bevel fit, every gap against two bevels (6 reference px):**

| gap | px | |
|---|---:|---|
| header → list | 8 | ok |
| list → lower band | 16 | ok |
| lower band → sort row | 12 | ok |
| the three lower-band gaps | 18 | ok |
| sort_bar → return_button | 12 | ok |
| band top → inset top | 10 | ok |
| **window → ring, all four sides** | **0** | by definition |

Every window-to-window gap fits, with 8 px the tightest against 6.
The four zeroes are not a layout problem: the ring IS the metal
between the canvas edge and the first window, so a window at the ring
has no gap by construction, and the bevel there is laid over the
ring's innermost 3 px — which is the master's own edge treatment
already. Nothing was narrowed to fit and **no layout number needs to
change.**

**The check measures a ridge, not ink.** For every window, the three
pixels next to each edge must be at least 8 above the plate's own
metal median, and the eight windows must agree per side to within 4 —
they come from one sampled hole through one function, so drift means
two code paths have got in. Verified to fail: with the bevel pass
removed it reports *"the eight windows' L edges range 15..56"*.

Masks and plates regenerate byte-identical from
`layout_reference.json` plus the master, all seven files.

### The sort bar's rim cannot be rounded without new master artwork — 10 September 2026

**Third request, and this is the dated reason it was not built.** Data
is right about what she is seeing; the obstacle is not the hole and
not the cutter.

**WHAT THE ORIGINAL DOES.** Measured off
`colony_summary_native_split.png` at the sort panel's top-left
corner, native (112, 452): along the top edge the rim reaches full
brightness at x=114, along the left edge at y=453, and the corner
pixel itself sits at luminance 88 against the rim's 120-144. The
bottom-left corner reads the same. So the rim **turns the corner on
a radius of about 2 native px** — a small round, not a chamfer, and
the lit line is continuous through it. Against the HD bar's own
geometry (32 reference px tall where the native panel is 22-24) that
is **≈3 reference px at 1920**, 6 device px at 3840.

**WHAT HD DOES.** The rim is not drawn; it is the master's own lit
edge, nine-sliced around each hole by `frame_build.lay_border`. The
lit line lives in the four EDGE strips and the four CORNER tiles are
`BEVEL_REF` square — 3x3 at 1920, 6x6 at 3840 — of **flat luminance
2**, checked directly out of `bevel_source`. Measured on the shipped
plate, the sort_bar hole's four bevel sides read top 73, bottom 96,
left 162, right 110, which is the master's own per-side profile
exactly; and each of those lines **stops 3 device px short of the
corner**, where the flat tile sits. HD's rim is therefore four bright
lines with a dark notch at every corner, and the original's is one
line that turns.

**WHY THE OBVIOUS CHANGE DOES NOTHING.** `layout_reference.json`
carries `[x, y, w, h]` per hole and no radius, and `frame_cut.cut`
(`tools/frame_cut.py:82-84`) builds the alpha by pasting a solid
rectangle per hole. Adding a per-hole `corner_radius` and a
`rounded_rectangle` paste is a small, contained change — and it is
**cosmetically inert here**. The pixels a rounded alpha would newly
expose at the corner are the flat dark metal that is already there;
what a viewer reads as the rim is the RGB lit line, which the alpha
does not touch. The hole would become rounded and the rim would
still look square.

**AND THE MASTER HAS NO ROUNDED CORNER TO LIFT.** `bevel_source`
requires a rectangular hole (`RECT_FILL`) and says why: it crops a
rectangle and `lay_border` lays it around a rectangle, so a
chamfered source would print its own slanted corners onto every
window of the screen. The master has exactly one non-rectangular
hole — the header cartouche at (882, 21), 548x53, 91.4 % fill — and
it is a **45-degree chamfer roughly 20 px long**, not a radius;
`--profiles` scores it 0.00 because its edge cannot be measured.
Nothing in the master supplies a curved lit corner at any radius.
Synthesising one is refused by the pipeline's own rule, written at
`tools/frame_build.py:253`: *"Only the master's pixels, never a
drawn corner."*

**AND ONE BEVEL SERVES ALL EIGHT HOLES.** `bevel_source` picks a
single source and `build` lays it around every window, so rounding
it rounds the header, the list, all four lower panels and RETURN as
well. Rounding **only** the sort bar needs a per-hole bevel source,
which is a larger change than the radius and a different decision.

**WHAT WOULD ACTUALLY BUILD IT.** Artwork, in the master
(`screens/galaxy_map/assets/frame.png`): the holes' corners rounded
so the lit edge line turns through them, at about **3.6 master px**
(3 reference px at the 0.827 downscale the master ships at). With
that in the master the existing nine-slice picks it up with no code
change at all — the corner tiles would simply stop being flat. If
the rounding should apply to the sort bar alone, the per-hole bevel
source is the second half of the job.

**ALL OF IT CLOSES AS SUPERSEDED — 12 September 2026, decision 55**,
and the verdict above was never wrong; it stopped having a subject.
The colony screen wears one fixed image and the rim is the artwork's
own, so:

| parked item | closed because |
|---|---|
| corner tiles | `bevel_source` and the four flat tiles are deleted with `frame_master.py`. There is no nine-slice to give a corner to. |
| per-hole bevel | it was wanted so the sort bar could be rounded without rounding every window. Each hole carries its own rim now, drawn by hand. |
| master >= 3840 | the master was needed because the plate was assembled from it and upscaled to 2160p. Nothing is assembled. `assets/frame.png` is 1672x941 and is scaled like any other image; whether THAT is enough at 2160p is a question about one file and is answered by looking at it. |
| the rim cannot be rounded | it can. Data chamfered these holes' corners in GIMP on 10 September, which is the file the screen now wears — 1 724 alpha pixels changed, concentrated at the corners. The obstacle was never the radius, it was that the rim was RGB the alpha never touched. |

The measurement that produced all four — the original turns its rim
corner on ~2 native px, ~3 reference — is not superseded and is the
number any future rounding uses.

### Two rules of unknown parentage — 11 September 2026, one settled the same day

Freeing the top and bottom band (fundament decision 53) dropped four
enforcements whose origin was written down. **Two more block the same
work and were deliberately NOT touched, because nothing in the tree
says where they came from and a session does not get to decide that.**

**1. `sort_bar.x` must equal `list_area.x` within 2 px — SETTLED
11 September 2026, and the answer is OURS.** Dropped to a report line
the same day. The premise the rule rested on is simply false: the
original does NOT put its sort strip and its list against one left
edge, it puts them **77 native px apart**.

| | native | source |
|---|---|---|
| sort strip left | 89 | `Add_Multi_Button_Field_`, colsum.cpp:267 (then 140, 219, 262, 326, 393, 480 at :268-273) |
| sort strip right | 515 | live FIELD_LIST, orion2re 1.60, screen 20, stardate 3502.4 — the width is `animate::Get_Width_(pic)` and lives in the player's LBX, so the source alone cannot give it |
| sort strip height | 24 | y 446..469, both sources |
| first list field left | 12 | `Add_Hidden_Field_(12, y1, 101, y_row_end)`, colsum.cpp:291 |
| colony name printed at | 12 | `Squeeze_Formatted_Paragraph_Centered_(0x0C, …)`, colsum.cpp:582 |

77 native px is **231 reference px**. Two independent sources for
every number: the C++ literals and the live field list, agreeing on
all seven button x and on y 446..469.

**THE CITATIONS, RE-VERIFIED 12 September 2026 — AND THIS PARAGRAPH
WAS ITSELF WRONG.** It said `Add_Multi_Button_Field_` is at
colsum.cpp:**265-271** "in this tree, not 267-273". It is at
**:267-273**. `~/orion2re/src/game/colsum.cpp` at cf4d9617, working
tree clean for that file, puts RETURN's
`Add_Button_Field_(531, 445, …)` at :265 and the seven multi-buttons
at :267-273, and `doc/v3_orion2re_index.md:517` says :267-273 too. So
the work order that was "corrected" had it right and the correction
introduced the error — which is the same fault in the other direction,
and the reason the rule is *run the arithmetic, then write the prose,
whoever is writing.*

The second half of that paragraph was RIGHT and its number was off by
two: the full-screen catch-all `Add_Hidden_Field_(0, 0, 639, 479, …)`
is at colsum.cpp:**309**, not :311. The first list field is at :291
and the colony name is printed at :582; both verified and both
unchanged.

**2. `_bare.mean() < 0.01` — no bare strut texture on the built
plate. SETTLED 12 September 2026, and the answer is the one this entry
said would settle it: the colony screen wears a FIXED IMAGE, so the
check measures a generator whose output nobody draws. It is a report
line now. The reading below is unchanged and was right.** This one is not a layout rule at all, which is why it is
here rather than in the dropped set: it measures `frame_build`'s
output quality, and Stage A3's goal that rails cover the tiling. It
fires on a narrower HEADER because `frame_master.struts` only finds
rectangles between FACING windows, so metal beside a header that does
not span the list is covered by nothing. **Measured: a header of
`[200, 24, 1500, 40]` leaves 1.06 % bare and fails; the same header
with the lower band also moved leaves 2.04 %.**

**AND THE HONEST READING OF (2) IS THAT IT IS NOT THE SUITE'S RULE TO
DROP.** What it exposes is that `frame_build` — not the smoke test —
is what actually requires a flush, evenly gapped layout: it can only
fill gaps it can see as rectangles between facing windows. A frame
Data draws herself does not go through it at all (`frame_preview`
false, the artwork used directly), and then the check is measuring a
plate nobody draws. **Which of the two paths the colony screen takes
is the open decision**, and it is upstream of this check rather than
settled by it.

### Data's planet discs, and what else the mockup asks for — 12 September 2026

Two files from Data: `planets.png`, a 5x2 sheet of the ten MOO2 planet
types with captions (1916x821, sha256 `b08c18dc6962851a…`), and
`mockup.png`, a target picture of the whole screen. Only the planets
are in scope here; the rest is listed at the end.

**THE SHEET HAS NO PIXEL GRID, AND THAT IS MEASURED.** The art reads
as chunky pixel work, so the method asked for was "find the block size,
one sample per block". There are no blocks to find:

| measurement | result |
|---|---|
| edge positions modulo b, b in 2..8, thresholds 6 and 120 | uniform in x and y — no offset is preferred |
| within-block variance against b | rises smoothly, no knee; best offset beats worst by 10 % at b=4, which is noise |
| distance between consecutive strong gradient peaks | decays smoothly from 2 px, no preferred spacing |
| Fourier of the gradient profile, per disc | strongest period between 5.8 and 9.5 px, and a different one per disc |

So the sheet was painted or resampled without a grid. What survives of
the instruction is its other half, and it is the half that matters:
**point sampling, never an average** — one source pixel per output
pixel, so every colour in a disc is a colour that is in the sheet.

`BLOCK = 5` is therefore a choice, made from the far end: at 5 a disc
is 46 to 50 px across and the sprite is **54 px**, which is exactly the
height the list gives a row's icon at 1920x1080 (`band 58 - 2 * step`).
The reference resolution draws Data's art at 1:1 and every other size
steps from it.

**The ten, measured off the sheet** (source rect is 270 x 270 around
the disc's centre; the disc radius is the steepest drop in its own
radial profile past r=80, which is the limb and not an interior edge):

| id | type | source rect | disc r, src | disc r, true | sprite |
|---:|---|---|---:|---:|---|
| 0 | toxic | (80, 94, 270, 270) | 116 | 23.2 | 54 x 54 |
| 1 | radiated | (440, 94, 270, 270) | 115 | 23.0 | 54 x 54 |
| 2 | barren | (818, 92, 270, 270) | 122 | 24.4 | 54 x 54 |
| 3 | desert | (1192, 95, 270, 270) | 116 | 23.2 | 54 x 54 |
| 4 | tundra | (1558, 94, 270, 270) | 119 | 23.8 | 54 x 54 |
| 5 | ocean | (76, 428, 270, 270) | 123 | 24.6 | 54 x 54 |
| 6 | swamp | (439, 431, 270, 270) | 122 | 24.4 | 54 x 54 |
| 7 | arid | (814, 430, 270, 270) | 122 | 24.4 | 54 x 54 |
| 8 | terran | (1191, 431, 270, 270) | 124 | 24.8 | 54 x 54 |
| 9 | gaia | (1562, 429, 270, 270) | 120 | 24.0 | 54 x 54 |

Alpha is a CIRCLE on the true grid and never a luma key — the dark limb
of a planet is the planet. Inside the disc's radius the sprite is
opaque whatever colour it is; for three true px beyond it the sheet's
own brightness fades the glow out. **The glow is trimmed where a
caption is close**: the first cut carried an orange fragment of the
word DESERT along the bottom, because that caption sits 126 source px
under its centre and the ring reached 131. `_caption_top` measures the
caption per cell and the mask stops a true pixel short of it.

**The classes are the enum's, all ten present, none missing.**
`PLANET_CLIMATE` (orion2_consts.h:362-374): 0 TOXIC, 1 RADIATED, 2
BARREN, 3 DESERT, 4 TUNDRA, 5 OCEAN, 6 SWAMP, 7 ARID, 8 TERRAN, 9
GAIA. The sheet is drawn in that order, top row then bottom, so the
file names are the enum written once. `colonyrows` already puts
`s_colony.climate` in every row — the COLONY's field, which
`Colony_Calculation_` rewrites when a shield turns a Radiated world
Barren (colcalc.cpp:682) — and the same number picks the disc.

**Placement A, the list.** A square disc at the name cell's left, as
tall as `band - 2 * figure_step` (the clearance the population figures
already keep from the cell plate's line), vertically centred because a
disc sitting on a floor reads as falling. The name and its "Terran
13/22" line start past it, shifted by the disc plus
`list.planet_icon_gap` — 6 reference px, **data in layout.json and not
a number in `colonylist`**, which is what the order asked for and what
lets the next gap be an edit rather than a commit. Marked as a
DEVIATION: the original starts that text at native x 12
(`Squeeze_Formatted_Paragraph_Centered_(0x0C, …)`, colsum.cpp:582) and
draws no planet anywhere.

**Placement B, `planet_info`.** The same sprite at the panel's own
height less its padding — 173 px at 1920x1080 — at the left, with the
five transcribed lines to its right (`output.planet_disc_gap`, 12
reference px). Nothing else in that panel moved: same paragraph, same
wrap, same colours, same red on negative growth.

**Sizes per window, and the scaling.** Nearest neighbour in both
directions, one cached set per pixel size (LRU of four, like the
figures), and no `smoothscale` anywhere:

| | row icon | panel disc |
|---|---:|---:|
| 1920x1080 | 54 (1:1) | 173 |
| 2560x1440 | 73 | 231 |
| 3440x1371 | 69 | 220 |
| 3840x2160 | 108 | 346 |

**Checks: 120 -> 122.** One holds the ASSETS — ten files, the enum's
names in the enum's order, 54 px square, opaque at the centre and gone
at the corners, and **no b x b block uniform for b in 2, 3, 4**, which
is "at their true size" as something a run can fail. The other holds
the DRAWING at four sizes: every row's disc is pixel-for-pixel the
sprite its own climate selects, the name's ink never starts before the
disc ends, and `planet_info`'s lines stay inside the padding beside the
big one.

---

**The mockup's other five ideas — candidates, not decided.** Each with
the one thing that blocks it:

| idea | what it is | the blocker |
|---|---|---|
| Row highlighting | alternating row backgrounds and a lit marker on the selected colony | **BUILT 13 September 2026, briefs 95/96, as an HD EXTENSION** (decision 57): rows A/B by list index and the scanned colony's band filled, from Data's table. No separate hover colour — the hovered row is the scanned row (colsum.cpp:880-890). The original's facts in this cell still stand: its only row state is the NAME's colour (`Set_Colony_Font_To_Blue_`, colsum.cpp:554) and the only `Fill_`/`Line_` calls on the screen are the scroll thumb's (:759-765) |
| Job colours | farmers green, workers orange, scientists blue | **the figure's colour IS the race in the original** — `People_Anim_` indexes `race * 13 + job * 2` (colony_main.cpp:444) and the bronze/teal/white are that race's sprites. Tinting by job throws away the fact the sprite carries, and the identity letters (decision 48) exist because that fact is load-bearing |
| Building icons | an icon per building instead of the bare name | **needs artwork that does not exist** — there is no icon set for 49 buildings and the game ships none; and the names themselves come from the player's TECHNAME.LBX, so a mod-shaped icon path would need the same per-name resolution the figures have |
| Build progress | a bar and "3 Turns" in the BUILDING column | **needs the cost extraction** — `TECHDATA::_buildings[].cost` is not extracted, which is the same absence that makes Producing sort by name (colsum.cpp:1091). Turns remaining is cost against industry and neither half is on the wire yet |
| Output icons | leaf/gear/flask/coins/face beside the five `planet_output` values | **BUILT 13 September 2026, brief 92, as a DEVIATION and not an invention** (decision 56): the glyphs are the original's own counting shapes, used as row labels. INVENTION in this cell is kept for the BARS the mockup draws beside the numbers, which were not built. The separator between the rows came with them, marked HD EXTENSION. See "Brief 92 Run 2" |
| Selected colony in the galaxy inset | a marker on the scanned star | the inset is a TRANSCRIPTION — `Draw_Galaxy_Map_Box_` with view_mode 3 draws stars and nothing else (movebox.cpp:63-105), and the one thing the original adds is the connect line while a cluster is held (colsum.cpp:731-744). A marker would be an invention drawn over a transcription, which is the pairing this project keeps apart |

### Brief 92 Run 1 — output icons and separators: the source answers — 13 September 2026

Reporting stop, no code. `doc/briefs/92-mockup.png` is Data's mockup
of 13 September 2026. Source tree: `~/orion2re` (the one whose line
numbers `colonyoutput`'s docstring already cites; colsum.cpp:1155 is
`Draw_Colony_Scan_Info_` there and 1322 in `orion2re-main-neu`).

**The sources, received.** Data's three AI-generated sheets (ChatGPT)
are under `screens/colony_summary/assets/_src/output/`:
`symbols.png` 1983x793 (sha256 `a37a81cd…`), `normal_moral.png`
1254x1254 (`9441ae25…`), `low_moral.png` **1374x1145** (`5bc347f5…`
— the brief said 1130). None has alpha. The background is not one
colour: every channel is 0 or 1 and all eight combinations occur, so
an exact key leaves speckle and a tolerance eats the icons' own
black (the mask eyes and mouths hold 27,740 to 34,480 pixels at
exactly (0,0,0)). Six components, cut to `_src/output/cut/1..6.png`
with a 4x contact sheet; eleven more specks of 1 to 27 px, none
brighter than 2, are noise. **Data's decisions:** 1 = BC (coin),
2 = food (corn), 3 = industry (pickaxe), 4 = research (test tube),
5 = normal morale (green, laughing), 6 = low morale (brown, sad).
Background = flood fill from the sheet border, any channel >= 2 is
icon, enclosed black stays; eyes and mouths stay black. No true
pixel grid, so ONE Lanczos downscale to the master size below, and
from the master the figure path (nearest neighbour).

**1. Morale in the original: TWO artworks, N copies of one.** The scan
box calls `COLDRAW::Draw_Info_Wee_Morale_` (colsum.cpp:1176 →
coldraw.cpp:724), which is `Draw_Info_Morale_Both_` with `is_mini = 1`
(coldraw.cpp:187). It computes `morale_div2 = (int8_t)morale / 2`
(coldraw.cpp:189, C truncation), draws `abs(morale_div2)` sprites
capped at 20 (:212), draws none at all at `GOVERNMENT_UNIFICATION` or
above (:197-198), and picks the sprite by SIGN alone (:220):
`morale_div2 > 0` → `C_Anims_(8)`, otherwise `C_Anims_(9)` (:222,
:230), which are COLONY2.LBX 0x2B and 0x2C (colony_main.cpp:512,
:514). The full-size screen uses 0x10 / 0x11 by the same rule
(:506, :508). Decoded from the player's COLONY2.LBX: 0x2B is a grey
smiling mask and 0x2C a brown sad one, 16x23 each.

So the original draws N sprites for +N / −N. **The two masks stand
for the SIGN, and the number this panel already prints stands for N**
— the same split as the rest of the panel. Two states cover
everything the original tells apart except one case it draws as an
absence: `morale_div2 == 0` (raw morale −1, 0 or +1) draws NOTHING,
and so does Unification. **For Data:** at zero, (a) no icon, which
transcribes the absence, or (b) the normal mask. Under Unification
the value is already `hidden_value`; the proposal is no icon there
either, whatever (a)/(b) says. Data's green-laughing / brown-sad pair
matches the original's pair in meaning and in order.

**2. Resource icons: the glyphs are the original's, the placement is
not — a CONTINUATION OF THE LABEL+NUMBER DEVIATION.**
`COLONY::Prod_Anims_` (colony.cpp:345-353) loads COLONY2.LBX entry
`type + variant * 4`, +27 for the small set the box uses
(`Draw_Colony_Wee_Prod_`, coldraw.cpp:720, frame 1). Decoded: entries
0-3 are corn, pickaxe, test tube, coin — ECON order FOOD, INDUSTRY,
RESEARCH, BC (orion2_consts.h:119) — and 4-7 the tens sprites. Data's
four are recognisably these four units. **But no routine on either
screen draws one of them singly as a legend or header:** every
`Prod_Anims_` call is inside `Draw_Colony_Prod_Both_`'s counting
loops (coldraw.cpp:118-158) except colbldg.cpp:960, which draws the BC
TENS sprite once as the picture of the Trade Goods item on the build
screen — an item picture, not a resource label. The colony screen
draws the same counting rows (colony.cpp:757) over a background
(COLONY2.LBX 0x31 plus COLPUPS.LBX 5/6, colony_main.cpp:111-115,
colony.cpp:628-632) that carries no glyph beside them. So an icon
beside a label is not a transcription; it extends the deviation this
panel already carries (a label and a number where the original counts
sprites), with borrowed shapes. The 12 September table above called
it an INVENTION; DEVIATION is the proposed marking — Data's word.

**3. Separators: the original draws none — HD EXTENSION.**
`Draw_Colony_Scan_Info_` (colsum.cpp:1155-1208) draws two prod/morale
calls and one paragraph, nothing else. The only `Line_`/`Fill_` calls
in colsum.cpp are the two full-screen clears (:125, :460) and the
scroll thumb (:759-765). And it is not painted into the art either:
COLSUM.LBX entry 0, the background the screen draws (colsum.cpp:461),
is ONE palette index (80) on every pixel of x 102-370, y 349-438.
The native rows could not hold a line anyway: pitch 18 (:1173)
against a 23 px sprite, so consecutive rows overlap by 5 px. The
separator gets the HD EXTENSION marking at the three homes plus a
check. **A question to verify, not a finding:** the colony screen's
COLPUPS.LBX 5 paints compartment frames in its production area — a
precedent for divided rows on the OTHER screen, if Data wants one.

**4. Icon size: ours, so it lives in `layout.json` under `output`,
not in `core/zoomtables`.** Proposed entry:

```json
"icon_size": 31,
"icon_gap": 8,
"_icon_size_note": "31 reference px = the output row's height at 1920x1080, (197 - 2*pad_y - 4*row_gap) // 5 in colonyoutput.render, so the reference resolution draws the master 1:1 and every other size steps from it by nearest neighbour - the rule colonyplanets.MASTER_SIZE follows for 54. NOT FROM THE PNG, and not the original's glyph: COLONY2.LBX's units are 16x23 at a pitch of 18 and overlap; an HD row is 35 px pitch. All six masters share ONE 31x31 footprint, content fitted by its longer edge and centred, so a morale change neither moves nor resizes the icon."
```

Row heights that rule produces, measured from the same formula:
**21** px at 1280x720, **31** at 1920x1080, **42** at 2560x1440,
**40** at 3440x1371, **62** at 3840x2160 (scale × 31, rounded down,
within a pixel of the row). **CORRECTED IN RUN 2:** those rows were
computed from the 197 px HOLE; the drawn box is 201 (2 px bleed each
side), so the rows are 22 / 32 / 43 / 41 / 64 and 31 sits one pixel
under the 1080p row. Data had confirmed 31 on the wrong arithmetic; it
stands, because it still draws 1:1 and still fits every row.
`boxes.json` declares the panel at
1920x1080 and 2560x1440. The master is one file per icon; the panel
has no steps. `icon_gap` 8 is a starting number for the side-by-side.
The label moves right by `icon_size + icon_gap`; the per-row clearance
check (`_geometry_note` (b)) is re-run in Run 2, not assumed.

**5. Next free decision number: 56** — 1 to 55 all present in the
fundament, 56 cited nowhere in the tree. Checked again at Run 2's end.

### Brief 92 Run 2 — the icons and the line are on the panel — 13 September 2026

**Data's decisions after Run 1** (the messages are
`doc/briefs/93-…` and `94-…`): #1 BC, #2 food, #3 industry, #4
research, #5 normal morale, #6 low morale; background by flood fill
from the sheet border with any channel >= 2 counting as icon and
enclosed black kept; one Lanczos downscale to the table's size and
the figure path from there. At zero the morale icon is the NORMAL mask
because it is a label and not a counter; the icon follows the morale
row under Unification; DEVIATION for the icons, INVENTION kept for the
unbuilt bars; `icon_size` 31 and `icon_gap` 8 confirmed. Filed as
**decision 56** under Sizing and artwork.

**ONE CORRECTION TO RUN 1, made here and in the three places that
carried it.** Run 1 computed the row heights from the 197 px HOLE in
`layout_reference.json`. The box the panel draws into is **201**,
the hole plus 2 px of bleed each side, so the rows are **22 / 32 / 43
/ 41 / 64** px at 1280x720 / 1920x1080 / 2560x1440 / 3440x1371 /
3840x2160, and 31 is one px under the 1080p row, not equal to it. The
confirmed 31 stands: it still draws 1:1 at the reference resolution
and still fits every row (20 / 31 / 41 / 39 / 62 drawn). Corrected in
`output._icon_size_note`, in decision 56 and inline in Run 1 above.

**The tool, `tools/make_output_icons.py`.** Reads the three sheets
(refused if a sha256 differs from the one its rectangles were measured
on), and for each of six literal rectangles:

| step | what | why |
|---|---|---|
| background | every channel <= 1 AND 4-connected to the sheet border | Data's rule; 4-connected so a diagonal cannot leak into an enclosed area. The masks' eyes and mouths stay |
| body | the largest 8-connected component inside the rectangle | drops the eleven 1-27 px specks the sheets carry, none brighter than 2 |
| de-fringe | within 3 px of the background: alpha = brightest channel / the icon's brightness 4-6 px inside; colour divided back up by alpha | the art is anti-aliased against black — measured, the brightest channel climbs over the first 2-4 px (coin 3 → 7 → 38 → 91) — so the rim is un-multiplied rather than keyed. Deeper is opaque whatever its colour |
| blank | RGB = 0 wherever alpha = 0 | `BLEND_RGB_ADD` ignores alpha (fundament section 4) |
| resample | **Lanczos, once, in premultiplied alpha**, longer edge to 31, centred on a 31x31 canvas | Data's filter choice. Premultiplied so the transparent black is not averaged into edge colours by the filter's support |
| guard | refuses to write anything unless both morale outputs share the canvas and fill it on their long edge | a state change must not move or resize the icon |

Result, content inside the 31x31 footprint: bc 31x31, food 26x31,
industry 28x31, research 10x31, morale_normal 27x31, morale_low 28x31.
From the master the renderer scales by **nearest neighbour** at
`int(31 * layout.scale)`. **DERIVED, NOT COMMITTED**: `.gitignore`
lists `assets/output/`, `tools/setup.py` runs the tool, and the suite
regenerates into a scratch directory and compares bytes — equal on
this machine. **The licence line**: the docstring says the sources are
AI-generated (Data, ChatGPT) and the project's own artwork, committed
as input under `_src/`. No other asset in the tree carries a written
licence note to copy — the nearest is the planet tool's "Data's own
artwork" — so that wording is modelled on it, and is Data's to
replace if there is a formal one. The Run 1 crops under
`_src/output/cut/` are ignored as well; they were a picture to name
the icons from.

**Rendering.** `layout.json` `output`: `icon_size`, `icon_gap`,
`separator_thickness` (1), `separator_inset` (0), each with its note;
the colour is the skin's `colony_summary.output_separator`
(38, 50, 76). `colonyrows.morale_icon` decides the mask and puts it in
the row as `morale_icon` (pinned key set 23 → 24);
`colonyoutput.visible_rows` hands each entry an `icon` by row id;
`render` draws the icon at the row's left, moves the label by the
SET's size plus the gap (so a missing file cannot put one label out of
line), and fills a line centred in the row gap above every row but the
first. Both read `layout.scale` directly and never `font_size`. With
no selection the function returns before any of it. The loader is
`colonyoutputicons.py`, the planet loader's shape: per-root mod
resolution, refuses a file of the wrong size, cached per pixel size.

**Checks: 122 → 125.** (1) the six files exist at the declared size,
the morale masks fill one footprint, nothing under transparency, and
the byte-for-byte rebuild; (2) at EVERY resolution `boxes.json`
declares `planet_output` for — the rule, not a list — each row's icon
is pixel-for-pixel the one its id or morale sign selects, no icon is
taller than its row, the set of pixel rows fully in the separator
colour is exactly one line between each pair of rows, the Unification
row keeps its icon, and an empty selection puts no ink down; (3) the
marking — DEVIATION and HD EXTENSION in colonyoutput, colonyoutputicons,
colonyrows, layout.json, colors.json, the fundament and here — plus the
three new marked files in the inventory. `tools/linecount.py`: no file
crosses 300 code lines.

**ACCEPTANCE — LIVE, and which save.** Slot **8**,
`fixture_reference_3502.4.GAM`, loaded through the GAME menu's Load
field (the Colonies screen's RETURN → GAME field 6 → Load field 1 →
slot field 8, which loads on selection; no `L` was needed).
`verify_colonies`: all 55 records match, before the renders and
again with them. `SAVE10.GAM` was `6dfcbfc991ae995c` before the first
live step (08:42) and after the last (08:45) — already different from
the secured copy `fixture_natives_autosave_3502.4.GAM` (`2610f39c…`,
intact both times) because the game rewrote it at 07:48, before this
session. **What was running before the load** was a game at stardate
3500.0 that is not a fixture; its state is in that 07:48 autosave.

Pictures in `~/orionlayer-fixtures/evidence/brief92/`, all from one
snapshot each, HD `planet_output` beside the original's scan box cut
from the same framebuffer: `output_{1920,2560}_Draconis_I.png`,
`output_{1920,2560}_Blucher_II.png`, `output_{1920,2560}_Vox_IV.png`,
`native_full.png`.

**NO HIGH-MORALE COLONY EXISTS TO SHOW.** Every player colony in all
three fixtures and in the game that was running has halved morale 0,
except four at −2 — and on the reference save the one −2 is **Draconis
I itself**. So Draconis I shows the LOW mask, and Blucher II and Vox
IV show the normal mask at 0. The normal mask on a positive value is
covered by the suite (morale 7) and not by a picture.

**THE NATIVE BOX IS SCANNING VOX IV**, not row 0: its paragraph reads
"Huge Ocean / Normal Gravity / Mineral Ultra Rich / Population (5/8) /
+61k" and the inset is labelled Vox. The scanned colony is whatever
the pointer last rested on (colsum.cpp:880-890) and the API cannot
move it, so Draconis I and Blucher II have no native counterpart
in these pictures and **Vox IV is the one like-for-like pair.**

**Questions for Data to verify, not findings:**

- Vox IV's native food row reads five corn, a gap, one corn; its BC
  row four coins, a gap, one coin. HD prints 5 and 4. Is the group
  after the gap the imports or secondary group that
  `_deviation_note` (1) says is not drawn?
- Vox IV's native morale row is empty (zero copies) where HD shows
  the normal mask — decision 56's rule. Does it read as intended?
- The test tube fills 10 of 31 px across and reads lighter than the
  other four. Acceptable, or a wider research glyph?
- Is (38, 50, 76) at 1 px the weight the mockup's line has, and is
  `icon_gap` 8 right against the label?

**Next free decision number at Run 2's end: 57.**

### Brief 95 Run 2 — the list palette, RETURN's size, the scan box as boxes — 13 September 2026

Briefs 95 (`doc/briefs/95-…md`, with `95-palette.png`, 1114x687,
sha256 `3c1409a3ba577a64…`) and 96 (Data's decisions on the Stop 1
report, `a59f66f0d9a6032e…`). Decision **57** filed under
**Structure**, beside 34, because it is the same kind of decision —
which colours the project's own palette uses and where they live.

**STOP 1, AS REPORTED.** The list had no per-row fill (one
`panel_background` fill for `list_area` through
`colonyplates.render_fills`, then a 1 px `draw_plate` outline per
cell); the pointer already moves the selection
(`handle_mouse_motion` → `Window.row_at` → `Selection.hover`,
transcribed from colsum.cpp:880-890); the selected row is one variable,
`colonyselect.Selection.colony`; the F5 editor's wheel writes
`font_scale`, which neither the sort keys nor RETURN read, so Part B
could not have been done in-game.

**STOP 2 — THE PALETTE. HD EXTENSION for the row fills.**

| key | value | what reads it |
|---|---|---|
| `panel_background` | #080E17 (8, 14, 23), was (8, 11, 20) | every panel's fill, the sidebar's own fill, the move notice |
| `row_a` / `row_b` | #0A121E / #111E2E | `colonylist.render`, by LIST index (`first` + band) |
| `row_selected` | #182B72 | the scanned colony's band, from the same `scanned` the bright name reads |
| `plate_outline` | #29394C, was a code default (55, 65, 85) | the list's cell outlines only |
| `header_background` | #09111D | `panels.header` names it |
| `header_text` | #79A8E8 | the five column words; `label` untouched |
| `galaxy_inset_fill` | (0, 0, 0), MOVED from `layout.json` | `panels.galaxy_inset` names it |

Removed: `colony_summary.nav_background` and `screen.NAV_BG` — nothing
on this screen read either. **NOT removed: the galaxy map's own
`nav_background`**, which the full-project grep shows is live
(`screens/galaxy_map/screen.py`, the nav buttons), so brief 96's
"anywhere" is held to this screen. No `row_hover` key, deliberately,
and a check fails if one appears. `palette.require` is new in
`core/palette.py`: a colour with no code default raises and names the
key. The colonylist comment that claimed the header and the cells
share one key is corrected: the header plates are `panel.thin_border`.
The fills are drawn under the plates, across the five plated columns,
never behind the scroll track.

**PART B — RETURN 24 → 18, both lists.** The "RETURN is an opaque
plate" check passes at all twelve sizes. Fit and slack, measured
(word + `HIGHLIGHT_PAD` per side against the box):

| size | font | word + pads | box w | slack x (was at 24) | slack y |
|---|---:|---:|---:|---:|---:|
| 1280x720 | 12 | 60 | 89 | 29 (11) | 22 |
| 1366x768 | 12 | 60 | 95 | 35 (14) | 24 |
| 1440x900 | 13 | 63 | 100 | 37 (15) | 25 |
| 1600x900 | 15 | 75 | 111 | 36 (16) | 28 |
| 1680x1050 | 15 | 75 | 117 | 42 (17) | 30 |
| 1920x1080 | 18 | 89 | 134 | 45 (19) | 34 |
| 1920x1200 | 18 | 89 | 134 | 45 (19) | 34 |
| 2048x1152 | 19 | 95 | 142 | 47 (21) | 36 |
| 2560x1080 | 18 | 89 | 134 | 45 (19) | 34 |
| 2560x1440 | 24 | 119 | 178 | 59 (24) | 45 |
| 3440x1440 | 24 | 119 | 178 | 59 (24) | 45 |
| 3840x2160 | 36 | 179 | 268 | 89 (37) | 68 |

The word now sits in visible slack — about a third of the box's width
at every size. The box was NOT resized; that is Data's to move.

**STOP 3 — THE PARAGRAPH AND THE DISC ARE BOXES.** Both in
`layout_reference.json` under `planet_info_parts` (a key in
`colonyplates.NOT_A_WINDOW`, so the hole checks never match them to
the artwork), seated by `colonyplates.part_rects`, listed by name in
both `boxes.json` lists, and **editor-free by construction**:
`colonyplates.editor_free` adds them and `write_back` writes a drag
into `planet_info_parts` unbled. `planet_paragraph` is a `text`-skin
box: the filled template is `Box.text` and its colour `Box.text_color`
at runtime (red for negative growth), and `to_dict` writes neither.
`planet_disc` is a rect and nothing else — the image is still the
climate's, through `colonyplanets` and the resource stack; the one
existing image box in the tree (empire_identity's homeworld art)
stores zoom, crop and fade and no path. **The renderer fits the disc
into the box's SHORTER side, centred**, so a box dragged out of square
does not stretch the planet. The wrap width is the box's width,
measured by rendering as before. Placement reproduces the old
arithmetic at 1920x1080 (disc 595, 734, 177, 177; paragraph 784, 734,
240, 177): **the set of drawn pixels inside `planet_info` is identical
before and after at 1080p (25,859) and 1440p (45,285)**; the only
differences are anti-aliased edges blending into the new panel base.
`planet_disc_gap` had one reader and is deleted with the padding
arithmetic.

**Checks 125 → 129:** the palette (seven keys to Data's hex, no
`nav_background`, no `row_hover`, the marking at every home, no typed
row-background or plate-outline colour anywhere in
`screens/colony_summary/`, read by AST); the stripe and selected fill
rendered at first = 0 and 1; both boxes at every resolution declaring
`planet_info`, inside it, the disc pixel-for-pixel and the paragraph
as `Box.text` / `Box.text_color`; an F5 save round trip (boxes.json
and the reference unchanged, no text, colour, rect or image path on
either box, a dragged disc landing in `planet_info_parts`). Four
existing checks were re-pointed, not deleted: the reference
vocabulary and the editor-free names now include the parts, the panel
fill check samples the header and the inset through their skin keys,
and the hole report names keys.

**SCREENSHOTS.** `~/orionlayer-fixtures/evidence/brief95/{1920x1080,
2560x1440}/`: the HD half LIVE from the running game (slot 8's
`fixture_reference_3502.4.GAM`, stardate 3502.4, `verify_colonies`
all 55 records matching), the native half the LAST native screenshot
of this screen, `evidence/brief92/native_full.png` (08:45, same
fixture). The game was on the galaxy map, so a live native frame would
have been the wrong screen; nothing was loaded or clicked in this run.
`SAVE10.GAM` was `9f9f35e417947840` at 09:41 and at 09:42 — it had
changed since brief 92's `6dfcbfc9…` (08:45), before this run touched
anything, so the game rewrote its autosave in between; the secured
copy `2610f39c…` is intact.

**Questions for Data, not findings:** the HD half selects Blucher II
and the native half scans Vox IV (they are not one moment), so the
lit row has no native counterpart by construction — is #182B72 the
weight wanted against the stripe? Does the header text at #79A8E8
("ca.") read right? RETURN's slack, as above.

**WHAT WOULD BREAK A FRESH CLONE.** Seven colours now have no code
default, so **a skin whose `colors.json` predates them raises
`KeyError` when the colony screen's modules import** — `plate_outline`,
`row_a`, `row_b`, `row_selected`, `header_text` at import, and
`header_background` / `galaxy_inset_fill` at the first frame. Decision
17 resolves a skin as a whole directory, so a mod skin does not
inherit them. **No shipped mod carries a skin or a `colors.json`**
(`mods/example_mod` overrides one main-menu credits file), so a fresh
clone is green; the check that would catch the case is the palette
check above, which requires all seven in the default skin only.

**Next free decision number at the end of this run: 58.**

### Brief 97 Stop 2 — the planet surface tiles, cut — 13 September 2026

Brief 97 (`doc/briefs/97-mockup.png`, 1672x941, `7f40a815…`), after
Data's decisions on Stop 1: names `planet_info` / `colony_panel` /
`galaxy_inset` with `planet_output`, `planet_surface` and
`empire_stats` as parts of `colony_panel`; the shortage figure stays;
the paragraph keeps the original's format and whole-paragraph red,
with only a name heading added as an HD EXTENSION; the fade on both
sides, image-box drawing moved into core, tiles scaled up;
`planet_paragraph` honours `font_scale`, scaled once. **Decision 58**
filed under Sizing and artwork: the surface picture is an **HD
EXTENSION** and the artwork is AI-generated.

**Inputs.** `assets/frame.png` replaced in place (`e2cec1ec…`,
1672x941 RGBA, three bottom holes and no title cartouche);
`assets/_src/surfaces/planet_surfaces.png` committed as source
(`0092f485…`, 2172x724 RGB, Data's ChatGPT sheet, no copyright claim,
listed in LICENSE's scope).

**The mapping is the enum's.** The sheet's labels run Toxic, Radiated,
Barren, Desert, Tundra / Ocean, Swamp, Arid, Terran, Gaia, which is
`PLANET_CLIMATE` 0..9 exactly (orion2_consts.h:362-373) and
`colonyplanets.NAMES` — checked against the source, not assumed.

**The cut, `tools/make_surface_tiles.py`.** Each card is a thin grey
frame on a flat field of about (1, 8, 15); the picture has its own
3 px outline (dark, bright, dark) and one anti-aliased row or column
against it. Brightness masks could not bound the pictures — Barren's
sky and Swamp's left edge are close to black — so the rule is the
edges, from median profiles across all ten cards: first full column
13 + 434·column, 411 wide; rows 124..334 (211 high) on top and
430..643 (214 high) below, the two rows genuinely three pixels apart
on the sheet. A plain crop at sheet resolution, no resampling, sha256
guard on the sheet.

| climate | tile (x, y, w, h) | sha256 |
|---|---|---|
| toxic | (13, 124, 411, 211) | `30bf6b50c989c9e0…` |
| radiated | (447, 124, 411, 211) | `329dd4b4a336e70e…` |
| barren | (881, 124, 411, 211) | `e0434f35a3c018c0…` |
| desert | (1315, 124, 411, 211) | `f82fa12b258698a9…` |
| tundra | (1749, 124, 411, 211) | `ebb9c29301e4f440…` |
| ocean | (13, 430, 411, 214) | `4670f5e4d93edf73…` |
| swamp | (447, 430, 411, 214) | `096e8277ae3e6d3b…` |
| arid | (881, 430, 411, 214) | `9bd57e08c78ea2fa…` |
| terran | (1315, 430, 411, 214) | `fa8749a2998f877a…` |
| gaia | (1749, 430, 411, 214) | `87ac13c9d4f96a9a…` |

Derived and ignored: `tools/setup.py` runs the tool, `.gitignore`
lists `assets/surfaces/`, and a second run into a scratch directory is
byte-identical for all ten. **The loader is `colonysurfaces.py`**, the
planet loader's shape: by climate through the resource roots, kept at
sheet resolution (the image box scales once, at Stop 3), and a root
without tiles is the `missing` state with a log line naming
`tools/setup.py` — decision 38's rule — never an exception. Marked HD
EXTENSION (decision 58) and DEVIATION in kind there, in the fundament,
in LICENSE and here; one new smoke check holds the tile rule over
every climate id, the sizes, the byte rebuild, the missing state and
the markings (**129 → 130**).

**The picture beside the sheet for Data's look:**
`~/orionlayer-fixtures/evidence/brief97/tiles_vs_sheet.png` — each
card at 2x with the cut rectangle drawn on it in magenta, and the cut
tile beside it at 2x.

**THE SUITE IS RED UNTIL STOP 3, AND WHY.** The new frame has three
bottom holes and `layout_reference.json` still names four rectangles,
so the hole match stops the run before it reaches the new check; the
check's assertions were exercised on their own against the cut tiles.
Nothing is committed at this stop. (A copying error in the chat report
put barren's hash tail on toxic; the files were re-hashed, they do not
collide, and the prefixes in the table above were always right.)

### Brief 97 Stop 3 — the bottom row rearranged — 13 September 2026

Data approved the tiles. **The reference first, then the regenerator.**
`layout_reference.json` names the three windows the frame cuts —
`planet_info` [100, 724, 460, 197], `colony_panel` [581, 724, 923,
197], `galaxy_inset` unchanged inside its hole [1534, 723, 282, 199] —
and `tools/frame_holes.py --write` then matched all twelve holes (rows
[1, 3, 8], **every hole claimed, `SPARE_HOLES` empty**) and kept **11
non-cutout boxes in each of the two lists**. `--write` writes NAMES
ONLY for the colony summary now (rects are the reference's, decision
55; `role` was deleted from the data model) and ends the file with a
newline, which also fixed `boxes.json`'s missing one. `BAND_KEYS` is
the three windows; the cartouche explanations in `SPARE_HOLES`,
`_match_by_overlap` and `name_holes_colony_summary` are retired.

**Parts.** `colonyplates.PARTS` holds `planet_info_parts` and
`colony_panel_parts`, both editor-free and written back by an F5 save.
Inside `planet_info`: `planet_disc`, `planet_paragraph` (Data's F5
placement kept, moved with the window by -481 px) and **`planet_name`,
the name heading — HD EXTENSION**, a text box in `header_text`, never
reddened. Inside `colony_panel`: `planet_output`, **`planet_surface`**
(image skin, `fade_left` / `fade_right` 0.2 in both lists) and
`empire_stats`. The panel fill moved to `colony_panel`.

**Drawing.** `core/imagebox.py` is Empire Identity's image-box code,
moved and given `fade_right`; the fade multiplies alpha, so the soft
edge is the panel base under the box. The surface picture is drawn
before the rows. `planet_paragraph` honours its `font_scale` (Data's
1.6) once, before the window scale.

**Three things the rearrangement surfaced, all measured:**

| what | why | done |
|---|---|---|
| the rows need 22 px more than the mockup gives | at the mockup's 246 px, RESEARCH with a three-digit net and a three-digit shortage leaves less than one em between label and value at all twelve sizes (3-36 px short) | `planet_output` 268, `planet_surface` from x 849, 431 wide; 264 was the first width that cleared, 268 clears by >= 5 px. The check was re-pointed from a two-column table nobody draws to the drawn one-column rows with icons |
| the paragraph could run out of its box | each line was squeezed against the whole box height on its own; at 2560x1440 with font_scale 1.6 five lines wrapped to seven and left the box | one size for the whole paragraph, the largest at which all lines fit together |
| **decision 44 is live again** | `empire_stats` is 224 px, under the original's 312, so the clamp fires at every size — the day-old "retired" text was wrong from this frame on | `colonyempire.value_column` and `empire._native_width_note` say DEVIATION, live; the existing check enforces exactly that |

**Checks 130 → 133:** the lower band is three holes matched to the
three windows with no spare hole and the three parts inside
`colony_panel`; `planet_surface` on the screen is `core/imagebox`'s
drawing of the climate's tile with the box's own style, its outer
column is the panel base, and zeroing `fade_left` in the style changes
it; `planet_name` is the colony's name in `header_text` and the
paragraph's first line renders at `font_size(value_font x font_scale)`
at 1080p and 1440p. The brief 95 round trip now covers `planet_name`
and `planet_surface` too.

**SCREENSHOTS** in `~/orionlayer-fixtures/evidence/brief97/`:
`stop3_vs_mockup_native_{1920,2560}.png` (HD, `97-mockup.png`, and the
last native screenshot `evidence/brief92/native_full.png`) and
`stop3_hd_{1920,2560}.png`. **The HD half is LIVE and the save has
DRIFTED**: the game on screen 20 fingerprints as the reference save,
but `verify_colonies` finds 2 of 55 records changed — Vox IV (13
bytes) and Blucher II (2 bytes) — which matches the mockup's Vox IV
(workers and scientists, -189k). Nothing was loaded or clicked in this
run, and the slot was NOT reloaded, because the change is in the game
someone is holding. The captions say so. `SAVE10.GAM` `9f9f35e4…`
before and after; the secured copy intact.

**WHAT WOULD BREAK A FRESH CLONE (brief 97).** A clone that runs the smoke test
before `tools/setup.py` fails the surface check ("no surface tile for
climate 0 … run `python tools/setup.py`"), the same way the output
icons do — the tiles are generated and ignored. The GAME does not
break: `colonysurfaces` reports the missing set once and draws no
picture (decision 38). CLAUDE.md's order is setup, then the smoke test.

### Brief 98 — right-click help on the Colony Summary — 13 September 2026

Handover item 4. **A transcription on the shared machinery, no new
decision.** `screens/colony_summary/help.json` holds
`ERICHELP::_colony_summary_screen_help_list` (erichelp.cpp:65, 22
entries, `s_help_box {help_id, x1, y1, x2, y2}`, orion2.h:993),
installed by `Set_Colony_Summary_Screen_Help_List_` (erichelp.cpp:145)
from colsum.cpp:144 and :531, in the original's order with each entry's
640x480 rectangle as provenance. The walk, the popup (auto-sizing, the
marked HD EXTENSION) and the swallow are `core/screenhelp.py` /
`core/helppopup.py`, the same the galaxy map, Main Menu and New Game
use; the colony screen supplies the file, two region kinds and nothing
else.

**How the regions bind — the existing two routes.** `box` names for
the bottom row (523 `planet_info`, 524 `planet_output`, 525
`galaxy_inset`, 526 `empire_stats`), RETURN (500) and the seven sort
slots (527-533), so they follow brief 97's rearrangement instead of a
scaled rectangle landing on the wrong panel; `screen: true` for the
fallback 513, last; and two screen-specific kinds through
`help_extra_rect`, the seam New Game's `slot` uses, living in
`colonyhelp.py` (decision 6 kept `screen.py` under 300 code lines):
`column` (515-519) is the `col_<key>` box unioned with its heading
plate — Data's decision, because the original's column rectangles run
from y 1 and include the heading — and `scroll` (514, 521, 522) is
`colonyscroll.arrows` / `track`.

| class | entries |
|---|---|
| no HD counterpart | **520**, the Buy column (colsum.cpp:302): HD's Buy is a text button inside `col_building`, which 519 covers first. Kept for order, resolves to nothing, explained in `_no_counterpart` — Data's decision |
| HD boxes with no entry | `planet_surface` and the rest of `colony_panel` answer the general entry 513; `planet_name` and `planet_disc` answer 523 through `planet_info`; the row fills answer their column. No help text was written for any of them |
| the list | one region per COLUMN, heading plus ten rows — not per row |

**THE RIGHT-CLICK PICK DISCARD IS GONE — Data's decision (a).** Entry
513 covers the whole screen, so the original's `Check_Help_List_` hits
on every right click and `Get_Input_` never returns the -1 that means
Cancel (fields.cpp:1240) — there is no "outside every region" on this
screen. The HD extension that discarded a held pick on a right click
could never fire once the table was in, so `screen.handle_right_button`
is deleted and the shared handler answers; a left click off the rows
still discards (`_hd_extension_cancel`, `colonymoveui`, `colonypick`
updated, and the move check re-pointed: a right click with a pick held
opens help and keeps the pick). Two routing gaps closed with it: the
colony `render` never called `render_help`, and its own `handle_click`
did not let an open popup swallow the click.

**The popup box** is `help_popup` at [420, 170, 1080, 745], the Main
Menu / New Game placement, typed in `layout_reference.json` under a new
`screen_parts` (a part: no hole, editor-free, written back like the
others) and named in both `boxes.json` lists.

**The text needs nothing new.** `tools/help_extract.py` writes
`help_en.json`, `HelpText.missing_entry` is the "not extracted yet"
state, and all 22 ids are in the local extraction (500 "Return Button",
513 "Colony Summary Screen : General Help" … 533 "Sort By BC Button").

**Checks 133 -> 134.** The help loop now covers four screens and
accepts a `no_counterpart` entry only if it resolves to nothing and the
file explains it by id; the new check asserts the file against the C++
table's own order when `~/orion2re` is on the disk (and says so when it
is not), the fallback last, every heading plate answering its column,
the bottom row, the scroll arrows and track, a long entry scrolling at
1280x720, 1920x1080, 2560x1440 and 3840x2160, and a left click closing
the popup. `help.json` joins the hand-formatted exceptions of the JSON
round-trip rule, like the other three.

**SCREENSHOT.** `~/orionlayer-fixtures/evidence/brief98/help_516_vs_native.png`:
a right click on the FARMERS heading at 1920x1080 opens "Farmers
Display Window". **The original's own help box is NOT beside it**: the
Extension API injects left clicks only (`INJECT_CLICK`, 640x480 x/y),
so no right click can be sent to the game, and no native screenshot of
a help box exists in the evidence. The native half is the last native
Colonies screen (brief 92).

**WHAT WOULD BREAK A FRESH CLONE (brief 98).** Nothing new: a clone
without the HELP.LBX extraction gets `missing_entry`'s "not extracted
yet" text in the same popup, and every help check asserts regions and
behaviour, never the extracted strings. The order check reads
`~/orion2re` and reports instead of failing when that tree is absent.

### The eighth slot: RETURN is a cutout again — 12 September 2026

Data drew a frame with a slot for RETURN the same evening the 13-hole
one arrived. Confirmed before anything was copied: `~/Downloads/
frame.png`, the only `frame.png` there, mtime 12 September 2026 20:42,
sha256 `b95d0651030c8197…`, 1672x941 — and **14 holes** in the alpha,
against the 13 of the frame it replaces.

| hole | window |
|---|---|
| title cartouche | — SPARE, claimed by nothing, as before |
| list | `list`, with `header` as its top band |
| bottom 1..4 | `planet_output`, `planet_info`, `empire_stats`, `galaxy_inset` |
| sort row, 8 | `sort_name` … `sort_bc` and **`return_button`** |

Naming resolves **13 windows + 1 spare**, rows `[1, 4, 8]`, by overlap
against `layout_reference.json`. RETURN's rect is the artwork's own,
scaled the way every other slot's is — native (1463, 838, 113, 41) →
reference **[1680, 962, 130, 47]**, each edge within half a pixel of
the hole, the same convention the seven keys were measured with.

**What went back.** `_render_return` after the frame is gone; RETURN is
drawn in `_render_buttons` with the seven keys, under the frame, and
`colonysort.render_return` keeps only the hover and the word — the
panel fill arrives with every other cutout's through
`colonyplates.render_fills` (`panels.return`), and the frame supplies
the bezel. The one thing it does NOT share with a sort key is the
highlight: a key lights the word plus `HIGHLIGHT_PAD`, because the
original lights the word; RETURN has no lit state in the original at
all, so the hover fills the whole button, which is what answers a
click.

**The editor.** `return_button` leaves `_windows_without_a_hole` and
`_editor_free`, so `frame_holes.cutout_names` returns all fourteen and
`boxclass` reads the colony screen as **0 free / 6 bound / 14 locked** —
the fourteen cutouts LOCKED because a cutout's rect is the hole's, and
the six columns BOUND to `list_columns`. `_editor_free` stays in the
file as an empty list: that is "no box may be dragged", where a missing
key would be "nobody has said", and a check now asserts the key is
there. The write-back path (`Editor._save` → `screen.save_geometry()` →
`colonyplates.write_back`) stays built and unused — add a name to that
list and the box becomes draggable again, with its drag surviving a
restart.

**Checks: 120, unchanged in count and three of them re-pointed.** The
bottom row is counted against the rule's own names instead of against
`SORT_KEYS`, which is seven and is no longer what the row holds; the
RETURN check asserts what holds for a cutout (panel fill, hover over
the whole box, word inside it with `HIGHLIGHT_PAD` to spare, 19 px of
clearance at the narrowest of twelve sizes) instead of what held for a
plate over the metal; and the editor-class check reads the
DECLARATION either way rather than a literal zero — which is what let
it be right on both days. Class C is empty again and class A stays at
zero: RETURN's word is in a hole now, so nothing this tree draws lands
on opaque alpha. Every window still sits inside its own hole at three
resolutions, RETURN included.

### Die Figur füllt die Zeile: fractional size — 12 September 2026

The anchor work put the figures on the row's floor; it did not make
them any bigger. The step is the largest INTEGER whose figure fits the
band, and at two of the four shipped sizes the band is nowhere near a
multiple of it — so a quarter of every row stayed empty. Data saw A, B
and C side by side (today, nearest neighbour at a fractional size,
integer step up with a smoothscale down) and chose **B**.

**The rule.**

    room  = band - PLATE_LINE
    plain = MASTER_ROWS * figure_step          (today's canvas)
    size  = room   if room - plain >= FIGURE_SIZE_SNAP
          = plain  otherwise                   FIGURE_SIZE_SNAP = 7

| | band | step | plain | room | size | scale | ink |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1920x1080 | 58 | 2 | 56 | 57 | **56** (snap) | 2.000 | 48 |
| 2560x1440 | 77 | 2 | 56 | 76 | **76** | 2.714 | 66 |
| 3440x1371 | 73 | 2 | 56 | 72 | **72** | 2.571 | 62 |
| 3840x2160 | 116 | 4 | 112 | 115 | **112** (snap) | 4.000 | 96 |

**THE SNAP IS A CORRECTION TO THE ORDER, and it is what makes the
order's own condition true.** The order asked for `(band - PLATE_LINE)
/ 28` at every size AND for 1920x1080 and 3840x2160 to be unchanged.
Those two cannot both hold: the room at 1080p is 57 against a 56 px
canvas and at 2160p 115 against 112, so the literal rule moves them by
1 and 3 px. The threshold resolves it in favour of the invariant — the
pixel grid is given up only when a fractional size buys at least a
quarter of a master row, which is 36 % and 29 % of the figure at the
two sizes that needed it and 1.8 % and 2.7 % at the two that did not.
The order's other condition, "the derived size fills the band to
within PLATE_LINE at all four sizes", is therefore asserted as the RULE
with both branches rather than as one instance.

**Sourced from the step BELOW the size** — 2.571 takes the `@2x` set,
a mod's own file if it ships one, and scales THAT. Two nearest-
neighbour maps rather than one, deliberately: what a modder drew at
56 px is what gets stretched, instead of being passed over in favour
of the 28 px master it was drawn to replace. `doc/modding_figures.md`
gains exactly one paragraph saying so and nothing else changes in it.

**What it costs.** Nearest neighbour keeps every colour exactly — no
blending, no half-tones, still the game's palette — and breaks the
pixel GRID: some master rows become three device rows, others two. At
1:1 that is invisible; the 3x zoom of the A/B/C crops is where it can
be seen at all. Variant C kept the grid even and blended the colours;
it was rejected on those crops.

**`FigureSet` is keyed by pixel size now, with an LRU of four.** Keyed
by step there were four possible sets and the cache could not grow;
keyed by size there is one per BAND, and the band tracks the window's
height. Four covers windowed, maximised and fullscreen in one session
and evicts the oldest beyond that. A resize that does not move the
band rebuilds nothing. A stale caller passing a STEP where a size is
wanted now fails loudly — `FigureSet(res, 2)` would have loaded 54
two-pixel sprites.

**Pitches follow the SIZE, not the step**: the cell pitch is the
original's own squish step times the scale, and the held cluster's
`(5, -10)` and 20 are `zoomtables`' native constants times the same.
Where the scale is an integer — the two snapped sizes — every one of
those is the number it always was, which is half of why the renders
are identical there.

**Measured, against the previous commit, whole-screen render, live
rows:** 1920x1080 **0** pixels differ of 2 229 120; 3840x2160 **0** of
8 904 960; 2560x1440 151 795 and 3440x1371 134 532, which is the
figures growing. (The first attempt at this comparison said 8 312 and
28 818 — the worktree of the old commit had no extracted building
names, so its BUILDING column read "names not extracted". The
difference was in the one column that has nothing to do with figures,
which is what made it obvious.)

**Checks: 119 -> 120.** The new one asserts the rule at all four sizes
— the size fills the band but for the plate's line, or it is the
step's own canvas and the shortfall is under the snap — plus that the
size is sourced from the step below it, and that at the two exact
sizes the set is **not resampled** and the scale IS the integer. The
ink-floor check still measures 52 cells per size out of the render and
stays green at the new sizes; `FIGURE_STEPS` membership still points
at `figure_step`, which did not change; the mod-file check still
refuses a wrong-sized `@Nx.png`.

### The row figures move to the band's floor — 12 September 2026

The held cluster was measured onto the row's own figure line on
12 September and was exactly on it. **The line itself was the float.**
At 3440x1371 the band is 73 px and the sprite 56, and all 17 px of the
difference sat below the figures; at 1920x1080 the same rule leaves 2
px and hides the fault where it was checked.

**1. What the original does, measured twice.**

| | native |
|---|---|
| row field | `31*i + 35` … `31*i + 65` INCLUSIVE — `y1 = y_row_end - 30`, `y_row_end` from 65 by 31 (colsum.cpp:283-291); a field's `y_end` is its LAST row (`field->y <= y && y <= field->y_end`, fields.cpp:708, :1268) |
| band height | **31 rows**, and the rows tile the pitch exactly |
| icon canvas | `31*i + 38`, 28 rows → `31*i + 38` … `31*i + 65` (`Draw_Info_Pop_For_`, colsum.cpp:685; mode 0 of `Do_Colony_Info_Pop_Stuff_For_Pop_` draws at `top_y`, coldraw.cpp:281-380) |
| gap above | 3 native px |
| **gap below** | **0 native px** — the canvas's last row IS the band's last row |

Confirmed on the original's own framebuffer
(`evidence/colony_summary_native_split.png`, the natives fixture,
Elerian): row 0 has its top line at native 35, ink at 38..61, the
plate's border at 62-63 and the next row's top line at 66 — and the
Elerian farmer master inks rows 0..23 of its 28, so its canvas is
38..65 and the four rows it ends with are the transparent tail.
Ink-to-border is 0 interior rows; canvas-to-floor is 0.

**A correction on the way past.** `FIGURE_TOP_NATIVE = 4` was derived
from "the field starts at `31*i + 34`". It starts at 35; the 34 is the
coordinate `Add_Fields_Pop_For_` passes with MODE 1 (colsum.cpp:336),
and mode 1 fills `pop_index_by_slot` and never reads `top_y`. The
original's own top gap is **three**, not four. The constant stays as
`figure_step`'s fit measure, with the correction recorded on it.

**2. The anchor.** `colonytrack.figure_origin_y(top, height, step)`:

    origin = band_bottom - (MASTER_ROWS + FIGURE_BOTTOM_NATIVE) * step
           = band_bottom - 28 * step

`colonylist` blits there and `held_figure_y` returns it, so a figure in
hand and a figure in a row cannot land on different lines. It cannot
push the sprite out of the top: `figure_step` needs `29 * step` rows of
band, so `band - 28 * step >= step`. That rule is now one row more
conservative than a bottom anchor requires and is deliberately left
alone — relaxing it would change the step at window sizes nobody is
looking at, which is a different decision.

**What moved:**

| | band | step | origin before | after | figures move |
|---|---:|---:|---:|---:|---|
| 1920x1080 | 58 | 2 | top + 8 | top + 2 | up 6 px |
| 2560x1440 | 77 | 2 | top + 8 | top + 21 | down 13 px |
| 3440x1371 | 73 | 2 | top + 8 | top + 17 | down 9 px |
| 3840x2160 | 116 | 4 | top + 16 | top + 4 | up 12 px |

**2b. THE CANVAS IS NOT THE FIGURE — the same day, one commit later.**
The anchor above put the canvas's floor on the band's floor and the
figures still floated at every size. A master's ink stops before its
canvas does:

| last inked row | masters |
|---:|---|
| 23 of 28 | 51 |
| 24 of 28 | 3 — `bulrathi_farmer`, `bulrathi_worker`, `bulrathi_scientist` |

(Top ink rows, for the record: 0 for 46 of them, 1 for five, 4 for
three.) So a canvas on the floor hangs its sprite four master rows up —
**8 device px at step 2, 16 at step 4** — and that tail was the float.

The rule is now

    origin = plate_inner_floor - ink_bottom
    plate_inner_floor = band_bottom - 1 - PLATE_LINE

with `ink_bottom` the last inked row of THAT sprite, measured on the
stepped surface at load (`colonyfigures.FigureSet.ink_bottom`) rather
than on the master, so a mod's own `@2x.png` — a different image, which
may ink to a different row — is measured as what it is. The held
cluster is anchored per sprite through the same function: `draw_held`
takes a callable now instead of a y, because a cluster can hold two
races whose ink ends on different rows.

**At native scale the original does the same thing**, which is why this
stays one deviation and not two: its ink ends at native 61, the row
above its plate's border at 62-63, and the four rows of tail are spent
on that border and the two rows under it. A step of 1 reproduces it
exactly. The original never steps, so it never has to answer for a tail
8 or 16 px deep. The cost is that the three Bulrathi sprites come up one
row against their neighbours where the original leaves them one row
lower.

**3. It is a DEVIATION and it is marked** in
`colonytrack.figure_origin_y`, in `colonylist` where the blit is, in
`layout.json` under `list._figure_anchor_deviation`, here, and in the
check. What deviates is WHICH EDGE the sprite is fixed to, not the gap:
the two anchors are the same anchor whenever a band is 28 rows per
step, which the original's is and none of ours. It ends if our bands
ever become the original's 31 rows per step.

**4. What the check holds now — and the arithmetic alone could not.**
Every assertion about the canvas was green while the figures floated,
because the canvas was in the right place and the figure was not. So
the check reads the RENDER: at 1920x1080, 2560x1440, 3440x1371 and
3840x2160, for every band and every cell that draws a sprite — 52 cells
per size — the lowest inked pixel is exactly the plate's inner floor,
and so is the held cluster's. The arithmetic is kept beside it for both
ink rows the set holds, 23 and 24, which have to land on the SAME floor
— that is what anchoring by ink buys and what no canvas anchor can
give. `MASTER_ROWS` is held to `colonyfigures.MASTER_SIZE`, because a
second copy of the sprite's height would put the row's figures and the
held ones on different floors.

### The held figure at 3440x1371: not reproducible — 12 September 2026

Reported a second time, at Data's own window size, which the 11:25 fix
had been verified at 1920x1080, 2560x1440 and 3840x2160 only. **It
could not be reproduced.**

**How it was measured.** Live, against the game already running on the
patched build (orion2re pid 18737, Extension API on localhost:17362).
Every step read a `STATE_SNAPSHOT` and nothing was injected — holding a
cluster is local, because the first click of a move sends nothing
(decision 47).

| live step | slot | fixture | what it did |
|---|---|---|---|
| snapshot for the 3440x1371 render | Slot 8 (already loaded) | `fixture_reference_3502.4.GAM`, sha256 `ab70cc9ad5442335…` | 11 player colonies, 10 drawn, stardate 3502.4 |
| snapshot for the four-size measurement | Slot 8 | same | pick row 2 farmer 0, pointer swept through the bands |

`~/Master of Orion 2/SAVE10.GAM` was checked against the secured copy
before and after: `9fb65a9d37349155…` both times, unchanged — no turn
ended, and it is (as always) NOT the autosave fixture's
`2610f39c00f68ebe…`, because the game has been running since 09:41.
Slot 8 was `ab70cc9ad5442335…` before and after, byte-identical to the
fixture.

**What the numbers say.** Pointer at each band's centre, the row's own
figures against the held cluster's, both read back out of the render:

| | band | step | row figures ink | held cluster ink | delta |
|---|---:|---:|---|---|---:|
| 1920x1080 | 58 | 2 | 247..294 | 247..294 | **0** |
| 2560x1440 | 77 | 2 | 326..373 | 326..373 | **0** |
| 3440x1371 | 73 | 2 | 310..357 | 310..357 | **0** |
| 3840x2160 | 116 | 4 | 494..589 | 494..589 | **0** |
| 3440x1440 | 77 | 2 | 326..373 | 326..373 | **0** |

Swept over every y of the window at 3440x1371, the cluster takes the
row's line from y 156 to y 891 — the whole of the list — and the
transcribed pointer offset above and below it. A resize from the
startup 1920x1080 to 3440x1440 through `App._on_resize` was measured
too, in case the fault needed the resize path: delta 0 after it.

**So there is no second anchor at 3440x1371.** Nothing in the held
path is in reference space: the bands, the pointer and the blit are
all window coordinates, and at that size the letterbox is horizontal
only (reference area 2437x1371, x offset 501, y offset 0), so it
cannot move a y at all.

**Two places at that size where the cluster is NOT on a row's line,
both by transcription:** outside the list's bands (above 156, below
891 — the header strip and the lower band), and over a band the empire
has no colony for, because an empty band is not a row and cannot be
dropped on. Either would read as a float in a screenshot.

**What is measured now.** The check gained 3440x1371 as a fourth size
for the arithmetic, and measures the BLIT at two sizes instead of one
(2560x1440 and 3440x1371) — a y that is right and a blit that ignores
it look identical in the arithmetic.

**Data's window is 3440x1371.** `settings.json` asks for 1920x1080 and
nothing in the tree writes a resize back, so the configured size says
nothing about the running one; the display is a single 3440x1440
(`DP-1`), and `App._set_mode`'s own measurement records that this
machine grants 3440x1371 for a 3440x1440 request and for F9's 4K
option. That is where the 1371 comes from. **It is not 3440x1440 and
not 1920x1080.** The window size is not logged unless the grant
differs from the request, which is the case that produced this
number — the line is in the log only at the moment of the change.

### Data's new frame: 13 holes, and RETURN on top of it — 12 September 2026

Data replaced `screens/colony_summary/assets/frame.png`. The right-hand
column is gone, the list is wider, and the lower band carries four
boxes instead of three. The alpha was counted before anything was
changed: **13 holes**, against the old frame's 14.

| hole | window | note |
|---|---|---|
| title cartouche | — | SPARE, claimed by nothing; `frame.title_rect` is absent |
| list | `list` | `header` is its top band, as on the old frame |
| bottom 1..4 | `planet_output`, `planet_info`, `empire_stats`, `galaxy_inset` | named by position, `galaxy_inset` confirmed against colsum.cpp:415 |
| seven slots | `sort_name` … `sort_bc` | one per key, decision 54 |
| — | `return_button` | **no hole at all** |

**RETURN is drawn over the frame.** `screen._render_return` runs
AFTER `_render_frame_image`, with the header plates and for the same
reason; `colonysort.render_return` paints the fill, the plate line
(`StyleRenderer.draw_plate`, decision 51) and the centred word. It is
the one box on this screen the editor may move — `_editor_free` —
and the write-back path is `Editor._save` -> `screen.save_geometry()`
-> `colonyplates.write_back()`, which edits `layout_reference.json`
in place and never `boxes.json`, where a rect would be overwritten by
`reseat` before it was drawn.

That plate covers the three lit lamps painted on the artwork at
reference `[1708, 982, 75, 8]` — 115 of the frame's 1229 lit pixels
at 1080p — because its initial rect is centred on them. The
alternative is the word with no plate: the lamps stay visible, the
button loses its hover surface, and it is one `surface.fill` away.

**The order it is drawn in was wrong for one run and the check that
found it had to be sharpened first.** `_render_buttons` ran before
the frame, so the plate went under the metal and the button was three
lamps with no word; the new check passed anyway, because it only
asked that the pixels were not the magenta the test surface was
filled with — and the frame is not magenta either. It reads the
plate's own `NAV_BG` now, and asserts the label's own colour appears
inside the rect, so neither a missing plate nor a blank one passes.

**`galaxy_inset`: the hole is bigger than the box, on purpose.** The
box is 248 x 196 reference px, whose 1.26531 is the closest any of
the three frames has come to the original's coverage aspect of
1.265134 (movebox.cpp:20-21). The hole is 282 x 199, so 34 px of
width and 3 of height have no box over them. `_hole_galaxy_inset`
declares the hole and `colonyplates.render_fills` lays the panel's
BLACK down over it before the box's own fill — Data's decision:
black, not the screen's background. The number is re-derived from the
alpha by a smoke check rather than trusted (decision 36).

**Decision 44 is retired, and it retired itself.** The clamp was
`min(cutout, native)` on the empire readouts' value column, written
so the deviation would end the day the artwork gave that hole 312
reference px. The new frame gives it 451 (435 usable), so the clamp
fires at **0 of 12** shipped window sizes and the drawn column IS the
original's proportion. `colonyempire.value_column` says RETIRED with
the measurement, the fundament entry is marked retired rather than
deleted, and the smoke check now asserts the CONVERSE: if the clamp
ever fires again, the docstring has to say DEVIATION again.

**Smoke: 117 -> 119 checks.** Two new, none removed:

| check | what it holds |
|---|---|
| declared hole fills | `_hole_galaxy_inset` is the artwork's own hole, re-derived from the alpha, and covers its window |
| RETURN is an opaque plate | at 12 sizes: the fill reaches the rect's edges, the word is on it and fits with `HIGHLIGHT_PAD` per side. The rect itself is NOT asserted — Data moves it |

Three existing checks changed rather than being replaced: the class-A
glyph rule gained **class C** (text on a plate we paint over the
frame, exempt only where `_windows_without_a_hole` declares it — 10
427 px, all RETURN's), the class-B floor and `RULE_NAMES` now read
the no-hole list through `BOX_NAME` (`return_button` there is
`return` here, and the mismatch left RETURN in the floor with no hole
to measure), and the editor's class table expects the DECLARED free
boxes instead of a literal zero.

**Measured, at the shipped sizes:**

| | 1920x1080 | 2560x1440 | 3440x1371 | 3840x2160 |
|---|---|---|---|---|
| list box | 1722 x 580 | 2296 x 773 | 2185 x 736 | 3444 x 1160 |
| row band | 58 | 77 | 73 | 116 |
| figure step | 2 | 2 | 2 | 4 |
| empire box | 451 x 201 | 601 x 268 | 572 x 255 | 902 x 402 |
| empire row | 26.8 | 36.0 | 34.2 | 53.7 |
| tallest ink in a row | 25 | 32 | 31 | 49 |

**The 197 reference px of `empire_stats` does NOT force a smaller
font.** Six rows with `row_pad` 0.10 give 26.8 device px per row at
1080p and the tallest ink block — the 26 px value glyphs — is 25, so
the rows clear by 1.8 px and by more at every larger size. The fonts
stay 18 (label) and 26 (value), and the check that value ink stays
inside the box and clear of its label holds at three resolutions.

**Step 3 at 1440p is still out of reach**, and the list is shorter
than it was: 576 reference px against the 638 the step needs. That is
the same conclusion as 8 September's, with a new frame's numbers.

### One home for every colony rect — 12 September 2026

**`boxes.json` held a second copy of the geometry and nothing read
it.** `colonyplates.reseat` overwrote all fourteen cutout rects at
`_reload_boxes`, before any reader, and the six column rects were
seated from `list_columns` by a tool somebody had to remember to run.
Both are derived at load now.

| | before | after |
|---|---|---|
| 14 cutout rects | in `boxes.json`, overwritten at load | derived from `layout_reference.json` |
| 6 column rects | in `boxes.json`, seated by `--columns` on demand | derived from `list_columns` at load |
| `role` | on every box of all seven screens, 149 entries | gone — `core/box.py` only round-tripped it |
| `locked` | in the data model and `to_dict` | gone — never written, never read |
| `tools/boxes_from_reference.py` | wrote the rects and `--check`ed them | deleted; there is nothing left to write |

**WHAT `boxes.json` STILL CARRIES: twenty names and eight font sizes,
2 473 bytes.** Nothing else. The names are the screen's vocabulary and
the font sizes are the only authored value left in it.

**SHOULD THE FILE GO ENTIRELY? Yes, and it is one decision away.** The
twenty names are derivable — fourteen from `layout_reference.json`
through `BOX_NAME`, six from `list_columns` — so the file's whole
remaining content is `font_size` 18 on the seven sort slots and 24 on
RETURN, which by decision 15 belongs in `layout.json` beside the
labels those sizes are for (`sort.font_size`, `return.font_size`).
What stops it being done here is that `ScreenBase` reads
`BOXES_FILE` for every screen and a screen with no box list has never
existed; that is a change to shared machinery and to the F5 editor's
idea of what it is editing, which is a decision and not a cleanup.

**THE ACCEPTANCE WAS MEASURED, NOT REASONED.** The derivation
reproduces the file it replaced exactly — all twenty rects identical,
diffed before the change — and a whole-screen render before against
after differs by **0 of 2 231 040 pixels at 1920x1080 and 0 of
3 955 200 at 2560x1440**. The budget was "at most the bleed pixel".

**`Box.derived` IS NEW AND IT IS READ.** A box seated from the
reference is marked, and `to_dict` writes no rect for it — otherwise
the first F5 save would put the second copy straight back. Unlike
`role` and `locked`, which this commit removed for the opposite
reason, it is a property of where the rect came from in THIS run and
is never read from the file.

**WHAT THE SUITE DID INSTEAD OF READING THE FILE.** Eleven checks read
a rect out of `boxes.json`; they go through `colony_rects()` or
`_seated()` now — the same pure functions the screen goes through — so
a check cannot measure a geometry the screen would not use. Two
checks changed subject rather than being deleted: `boxes.json ==
the tool's rebuild` became "no entry carries a rect at all, and the
screen's boxes are the reference", and "the column boxes are
resolution-independent" became "seating the same boxes at four window
sizes gives one answer", which is the rule the file comparison stood
in for.

**STILL BOUND IN THE EDITOR, AND THAT IS NOW ODD.** The six columns
are classed BOUND (left and right handles live) and a drag still moves
them for the rest of the session — but `save_boxes` writes no rect for
them and the next load rebuilds them from `list_columns`. A handle
whose result cannot be kept is the fault `core/editor/boxclass.py`
was written against. Making them LOCKED is a behaviour change and is
not in this commit; the way to move a column is to edit
`list_columns`.

### Phase B: what was deleted and what replaced it — 12 September 2026

**Data's decision after seeing all three paths rendered.** Fundament
decision 55 supersedes 49 for this screen. The colony screen wears
`screens/colony_summary/assets/frame.png`, scaled to the reference
area and blitted, and there is nothing to choose.

**Deleted.**

| gone | what it did |
|---|---|
| `tools/frame_build.py` | assembled the plate: ring, rails, junctions, bevel |
| `tools/frame_master.py` | `bevel_source`, the corner tiles, the rail table — what the master CONTAINED |
| `tools/frame_mask.py` | rendered the window mask the plate was cut against |
| `tools/frame_cut.py` | punched the alpha from the mask |
| `tools/colony_frame_check.py` | the read-only validator for Data's working files |
| `tools/gimp_fixtures.py` | wrote the layer mask and the labelled guide |
| `screens/colony_summary/colonyframe.py` | chose between a plate and the shipped artwork |
| `assets/frames/`, `assets/frame_masks/` | the three plates and the masks, with both `.gitignore` entries |
| `setup.py`'s `frame_build` step | rebuilt the plates after a clone |
| `layout_reference`: `ring`, `_ring_source`, `gaps`, `_gaps_note` | the master's metal border and its seven struts |
| `settings.frame_preview`, `settings.colony_plateless` | and their `load_settings` defaults |
| `colonyplates`' drawn fill / rim / lit line, `draw_plate`'s `fill` / `rim` / `radius` | the plateless prototype; every other caller always passed the defaults |
| `output.info_style` | Stage 5 — the switch, not the renderer |
| `frame_holes`: `PANEL_KEYS`, `ROW_SHAPE`, the order fallback | naming by position, which is the fault the overlap match exists to prevent |

**What `tools/frame_holes.py` keeps, and why.** `find_holes` is the
alpha reading every check that measures artwork goes through.
`name_holes` with the colony rule and `_rows` is what holds
`layout_reference.json` to `assets/frame.png` — every rectangle
matched to a hole by OVERLAP, no clean bijection no answer, the holes
nothing claims reported — and the smoke test runs it on the shipped
file. `RULE_NAMES` and `cutout_names` are the vocabulary
`core/editor/boxclass.py` asks for: which boxes are cutouts and
therefore LOCKED in the F5 editor. `to_ref`, `--write` and the
galaxy_map rule are there because **the galaxy map still derives its
boxes from its own `frame.png` that way**, and nothing about that
screen changed. Its own reference loader went: the rule for what
counts as a window now lives in `colonyplates`, which is the side that
has to answer it with no tool on the path.

**galaxy_map is untouched, and this is what was shared.** Its
`assets/frame.png` was the MASTER the colony plate was nine-sliced out
of — `setup.py` called it one and required it for a build step. It is
now simply that screen's own frame, and the line in `REQUIRED_INPUTS`
says so. `core/style.draw_plate` is shared by every screen through
`draw_thin_border` and is back to the one line it was before Phase A.

**The seven deleted checks, and what replaced each.**

| deleted | replaced by |
|---|---|
| colony rebuild frame cut (holes == mask, hard alpha) | every window inside its own hole, measured against `assets/frame.png`'s alpha at three resolutions |
| colony frame validator (passes the reference mask, fails a broken one) | the same check — the validator existed because the suite had no artwork, and now it has |
| colony frame built from the master (nine-slice ring, bevel, struts are metal) | nothing, and nothing is needed: no plate is assembled |
| colony frame switch + decision 49's byte-for-byte plates | nothing generated is left on this screen to reproduce |
| colony frame rails (every gap the master's strut, bare tile) | nothing. The rails covered gaps `frame_master.struts` could see; the artwork covers its own |
| colony_summary draws its own boxes with no artwork | the prototype is deleted |
| the plateless rim is a marked DEVIATION | the marking is deleted with the rim |

Three checks that survived were re-pointed rather than lost: `holes ==
mask == boxes` became `boxes.json` IS `layout_reference.json` plus
BLEED, byte for byte, PLUS an assertion against the LIVE boxes that
`reseat` ran; "every window inside the ring" became "inside its own
hole", which also catches a window inside the metal but over the wrong
hole; and the mask-reproducibility check became "every rectangle
resolves to the box the screen holds".

**Stage 5, folded in.** `info_style` is gone: the two pictures were
rendered beside the native, Data took the paragraph, and a switch with
one live setting is a branch nobody takes (brief 87; brief 81's "if
the paragraph stays the only user"). The `rows` RENDERER stays because
`planet_output` draws it, and the coloured cell renderer stays as it
always was going to (the exclusion recorded above). The smoke check
that asserted "both `info_style` variants draw" was a tautology with
one variant left and now asserts that a stray key cannot bring the
branch back. **The old modules' markers needed no retargeting** — the
marking inventory is green because none of the deleted files carried
one; `gimp_fixtures.py` did, and its entry went with the file. **The
443aff1 tautology was already rewritten** in an earlier commit and
still reads its edges from `boxes.json` rather than from the
renderer's own expression; re-checked, unchanged.

**Green at 1920x1080, 2560x1440, 3840x2160 and 3440x1371**, the last
of which letterboxes 501 px each side.

### Open, not built: the title hole

The pre-Stage-4 title cartouche — image `(640, 10, 386, 45)`,
reference `[735, 11, 443, 52]` — is the one hole no rectangle claims.
It shows the background. `frame.title_rect` is absent and
`frame._no_title_note` says why: this screen has drawn no title since
Stage 4. Candidates, none of them chosen and none of them started:

- **The SORT label.** The original prints SORT in the 77 native px
  between its list and its first sort field — ink at native x 23..74,
  y 456..462, which is 156 x 16 reference px. The cartouche is 443
  wide and 52 high, so it FITS at the transcribed proportion, which no
  other place on this screen does. It is in the wrong place — the
  original's is beside the sort row, not above the list — so it would
  be a DEVIATION in position with a transcription in size. The item
  has been parked since brief 78.
- **The screen's own title.** What the hole was cut for. It would be
  an INVENTION: MOO2 draws no title on this screen, and `_no_title_note`
  is the record of that being noticed.
- **The empire name, or the stardate.** Both are on the wire and
  neither is drawn here. Same objection as the title, plus they
  duplicate the galaxy map.
- **Nothing, and retouch the hole away.** The cheapest, and it is a
  GIMP edit rather than a code change: fill the cartouche with metal
  in `assets/frame.png`, and the smoke test's spare-hole line goes
  from one to none with no rectangle moving.

Whatever goes there is Data's, and the fourth option is the only one
that needs no decision about what this screen says.

### The colony screen wears one fixed image — 12 September 2026

**DATA'S DECISION, AND IT IS THE PATH THAT SHIPS.**
`screens/colony_summary/assets/frame.png` is Data's retouched copy of
the pre-Stage-4 colony frame — 1672x941, 14 holes, stable at alpha
< 8 / 16 / 64 alike — scaled to the reference area and blitted. No
master, no `frame_build`, no nine-slice, no bevel, no rails. Boxes come
from `layout_reference.json`; Data places them into the holes by hand.
`frame_preview` ships **off**. The built plate and the plateless
prototype are both still in the tree and both still green.

**THE SCALE FACTOR, PER RESOLUTION.** The image covers the whole
reference area (`screen._scale_frame`), so each axis scales
independently and the difference between them is the 0.05 % by which
1672:941 is not 16:9:

| window | reference area | x | y | letterbox |
|---|---|---|---|---|
| 1920x1080 | 1920x1080 | 1.148325 | 1.147715 | — |
| 2560x1440 | 2560x1440 | 1.531100 | 1.530287 | — |
| 3840x2160 | 3840x2160 | 2.296651 | 2.295430 | — |
| 3440x1371 | 2437x1371 | 1.457536 | 1.456961 | 501 px each side |

A single uniform factor was NOT adopted and the reason is arithmetic:
at `min` the image is 1 px short of the area and at `max` 1 px over,
and `frame_holes.to_ref` maps holes to rectangles with these same two
factors. Keeping them identical is what makes a hole and its box agree
by construction instead of by two roundings happening to match.

**THE MAPPING, READ OUT OF THE HISTORY AND NOT CHOSEN HERE.**
`tools/frame_holes.py` at 8788d55 names this file's holes: largest is
the list, topmost the title, the two right of the list the sidebar and
RETURN, the bottom row the seven sort buttons, the remaining three left
to right `output_panel` / `spare_panel` / `galaxy_inset`. Stage 4
(ac5b86f) renamed four of them.

| hole (image px) | pre-Stage-4 | today |
|---|---|---|
| (87, 75, 1223, 536) | `list_area` | `list` |
| (1336, 76, 245, 574) | `sidebar` | `empire_stats` |
| (1336, 668, 246, 135) | `return` | `return_button` |
| (87, 631, 401, 172) | `output_panel` | `planet_output` |
| (506, 631, 398, 172) | `spare_panel` | `planet_info` |
| (921, 631, 389, 172) | `galaxy_inset` | `galaxy_inset` |
| seven at y 837/838 | `sort_*` | `sort_*` |
| **(640, 10, 386, 45)** | **`title`** | **LEFT OVER** |

**THE HEADER'S ANSWER IS "NONE", AND THE HISTORY IS WHY.** There was no
header window before Stage 4 and no `colonyheader.py` either — the
column headings did not exist, so this frame has no band for them.
Stage 4's own commit message says *"a header window appeared where the
title hole was"*, which is a replacement in the layout and not an
inheritance of the rect: the cartouche is 443 ref px wide and the
headings span the list's 1404. **Measured rather than argued:** with
the header over the top metal the class-A checker counts 1855 glyph px
under opaque frame alpha at 1080p and 6606 at 2160p — NAME, FARMERS,
WORKERS and BUILDING; SCIENTISTS happens to fall inside the cartouche
— and that rule is zero-tolerance. So the header is the top band of the
LIST's hole, which is where the original puts its headings too.

**THREE NUMBERS IN THAT BAND ARE DERIVED, NOT CHOSEN.** header 32, gap
7, list 576. The gap is `2 * BEVEL_REF + 1`: the generated plate lays a
3 ref px bevel inside every window edge, and two windows 1 px apart
overwrite each other's, which the suite reads as the header's bottom
edge at 54 against the other thirteen's 81. The list's 576 is the
least that keeps a row band of 58 device px at 1080p, which is what
`colonytrack.figure_step` needs for sprite step 2 (4 transcribed + 28 −
3 measured = 29 master rows per step). The header gets what is left.

**WHAT MOVED WITH THE LIST, AND EVERY DERIVATION SURVIVED IT.** The
list hole is 1404 x 615 ref px where the Stage-A3 cutout was 1693 x
649, so three tables downstream were re-derived from their own
unchanged sources: `list_columns` (scroll keeps its transcribed 27 off
the top, the other five split what is left in the proportions they had,
the three jobs split theirs by the original's 135 : 142 : 134),
`no_farming_font` 28 -> 26 (10 of a 31 px row is now 18.4 of a 57 px
band, over Aldrich's 0.70 cap ratio), and the figure step. **1440p
loses sprite step 3** — its band is 77 device px and step 3 needs 87 —
and that is a real cost of the frame, not of the header.

**TWO THINGS SWAPPED SIDES AND ONE IS A HOLE TOO BIG.**
`planet_output` takes the LEFT bottom hole and `planet_info` the middle
one, because Stage 4 moved `spare_panel` left when it became
`planet_info`, so mapping the names back reverses them: the scan box's
production rows are on the left now and the description in the middle.
And `galaxy_inset` is the one rect that is not its whole hole — the
third bottom hole is 447 x 197, aspect 2.269, against the inset's
transcribed 1.265134 (movebox.cpp:20-21, the galaxy size cancels). It
is 248 x 196, the largest pair inside that hole whose aspect passes,
flush to the top and centred; the remaining 199 px of hole show
background either side, which is visible and is Data's to place.

**THE RING IS THIS SCREEN'S OWN NOW.** 100 / 103 / 11 / 70, measured off
this file with the same sweep, replacing the main-screen master's
107 / 120 / 18 / 74. The family ring is gone and nothing checks that it
is not — the suite reports both numbers, and stopped enforcing the pin
on 11 September (decision 53), which is what made this affordable.
"Every window is inside the ring, per side" is KEPT and is now asserted
against the artwork the screen actually draws.

**boxes.json IS DERIVED AT STARTUP.** `tools/boxes_from_reference.py`
writes it, and `colonyplates.reseat` rebuilds the same rects every time
the boxes are loaded — on entry and on every resize. That closes a trap
this session walked into on the day it became possible: edit
`layout_reference.json`, forget the tool, and the screen draws
yesterday's fills behind today's frame with nothing saying so. The file
on disk is a cache of the reference and never the authority. The six
column boxes are NOT rebuilt at startup — they are hand-placed and
draggable — and `--columns` re-seats them from `list_columns` when the
list itself has moved.

**SMOKE: 122, GREEN ON ALL THREE PATHS AT THE SAME COUNT.** The six
plate checks skip with their reason whenever the screen is not wearing
a built plate, which is now `frame_preview` off as well as
`colony_plateless` on. The new check is item 6's: every window sits
inside its own hole at all three resolutions, with the hole FOUND as
the transparent component under the window's own centre — immune to
this artwork's rounded corners, which are real and which
`tools/colony_frame_check.py` reports on all fourteen holes, 80 to 2172
px each. Worst overhang measured: 1 ref px, against 2 px of bleed.

**FIVE CHECKS WERE ASSERTING AN INSTANCE AND NOW ASSERT THE RULE.** The
row shape (a constant `[1, 1, 4, 8]` that described the Stage-A3 plate
and rejected a well-formed frame), RETURN's position (an x-only rule
that assumed RETURN is on the sort row and called a non-overlap an
overlap), the figure-step ladder in two places, and the class-B cutout
floor. Two more were reading a file the screen does not draw — class B
and the editor's cutout-vocabulary check both had the 1080p plate
hardcoded by path — and one, the editor's, was additionally calling the
namer with no image size, which since 12 September means "no reference":
it named nothing and the row check then failed on an empty answer.

**AND ONE OPEN ITEM CLOSES WITH ITS ANSWER.** `_bare.mean() < 0.01`,
the second of the "two rules of unknown parentage", was left standing
on 11 September with the reading that *"which of the two paths the
colony screen takes is the open decision, and it is upstream of this
check rather than settled by it."* The decision is taken: this screen
wears a fixed image, so the check measures the coverage of a generator
whose output nobody draws. It is a report line now, the same way the
four enforcements of decision 53 became report lines, and the static
frame's layout leaves 7.75 % bare where the Stage-A3 one left 0.

### The colony screen without frame artwork — 12 September 2026, PHASE A

**DATA'S DECISION, AND IT IS A PROTOTYPE.** No plate, no master, no
ring. Every box is drawn by code from `layout_reference.json`, and
Data moves a box by editing that file and nothing else. Phase A builds
it beside what exists and deletes nothing; Phase B is a separate order
and is what removes `frame_build` / `frame_mask` / `frame_holes` /
`colony_frame_check` / `gimp_fixtures`, the three plates and the ring
entries, and writes the fundament entry that replaces decision 49 for
this screen. **The flag ships OFF** so a clone still gets today's
screen; flipping `"colony_plateless": true` in `settings.json` is the
whole of what it takes to look.

| | with the plate | without it |
|---|---|---|
| chain to `boxes.json` | reference -> mask -> build -> cut -> holes --write | reference -> `tools/boxes_from_reference.py` |
| what a box's edge is | the master's lit edge, nine-sliced, flat corner tiles | `draw_plate`: fill, 2 ref px rim, 1 px lit line |
| corner | square, and c5977cf says a radius in the data is inert | `frame.plate_corner_radius`, 3 ref px, 0 allowed |
| between two boxes | ring, struts, rails, junctions, tiled texture | the background, and nothing else |
| smoke | 6 plate checks measure | the same 6 skip with their reason, and still count |

**THE RECTS DID NOT MOVE, AND THAT IS ASSERTED.**
`tools/boxes_from_reference.py --check` compares `boxes.json` against
`layout_reference.json` plus 2 px of bleed and the file is byte-for-byte
unchanged. It has to be: `frame_holes.to_ref` maps a hole back with
`int(round(x * REF_W / img_w)) - BLEED` and the plate is generated at
exactly the reference size, so the round trip through the PNG was the
identity all along. Nothing in the list, the panels or the sort code
moves, and the smoke test's own geometry checks are untouched.

**THE CORNER RADIUS IS c5977cf'S MEASUREMENT, FINALLY USABLE.** The
original turns its rim corner on about **2 native px** — at the sort
panel's top-left the top edge reaches full brightness at x=114 and the
left edge at y=453, with the corner pixel at luminance 88 against the
rim's 120-144, and bottom-left reads the same. Two native px is **3
reference px**, which is `layout.json`'s `frame.plate_corner_radius`.
c5977cf's verdict for the PLATE stands and is not contradicted: there
the rim is the master's own lit edge with flat corner tiles, so a
radius in the data is inert because what reads as the rim is RGB the
alpha never touches. A box drawn by code has no such problem. **The
parked "corner tiles" and "sort bar's rim cannot be rounded" items are
therefore answerable for the first time** — Phase B is where they are
closed, not here.

**THE RIM IS A DEVIATION AND IS MARKED.** The original has metal
around every field; we have none, and a 2 ref px band of
`panel.border` stands in for it. What IS transcribed is the
RELATIONSHIP, the same move `_row_name_note` makes for the list's
names: the original's plate reads interior 44, metal 60, outline 96 on
its own framebuffer, so the outline is the brightest of the three and
it is outermost. Ours is fill 11, rim 78, line 134 in luma — same
direction, ratios 1.6 and 1.7 against the original's 1.4 and 1.6.
Absolute greys were rejected for the reason decision 34 gives: this
screen draws in the project's own palette, and a neutral metal edge
would answer a different question from the one being transcribed.

**WHAT LOOKS WORSE, MEASURED BY LOOKING AT ALL THREE RESOLUTIONS.**
Two things, and both are the same thing:

- **The screen has no outer border at all.** The ring was 107/120/18/74
  reference px of metal and it is now background, so the boxes float on
  the starfield with nothing holding them. At 1920 it reads as a clean
  HUD; at 3840 the empty margin is 240 px on the right and reads as
  unfinished rather than as deliberate. This is the one judgement worth
  making on the picture.
- **The band-to-sort-row gap is 9 ref px and now shows.** With the
  plate a rail filled it and the seam read as one piece of metal; with
  nothing between the boxes, 9 px of background between the lower band
  and the sort slots reads as a mistake next to the 38 px gaps inside
  the band. Not new geometry — it is the gap `_sort_slots_note` already
  records and the suite already reports — but it was invisible before
  and is not now.

Nothing else is worse. The header plates, the fifty cell plates, the
figure columns, the galaxy inset and the sort highlights are drawn by
exactly the code that drew them yesterday, and the 50 % reductions show
no new noise. The rim lands where the plate's metal landed, over the
content and under the header plates, so no glyph moved and no clip
changed.

**SMOKE: 121 BOTH WAYS.** Six plate-based checks — the frame cut,
the validator, the built ring and bevel, decision 49's byte-for-byte
plates and the preview switch, the strut rails, and the `holes == mask
== boxes` chain — become a skip that still calls `ok` and still prints
why. Class A and class B drop `colony_summary` from their screen list
with a report line, because `colonyframe.frame_source` still resolves
to a plate and measuring glyphs against artwork nobody drew is the
exact fault that block already records once. Every box check stays and
measures: every window inside the ring, no overlap, the inset aspect,
the figure column at three resolutions, the list height to
`figure_step`. **The count is the same with the flag on and off by
construction**, which is what lets the two documents keep one number.

### The seven sort keys take seven boxes — 12 September 2026

**DEVIATION, fundament decision 54.** The one `sort_bar` hole is seven
`sort_<key>` holes: `sort_name`, `sort_population`, `sort_food`,
`sort_industry`, `sort_science`, `sort_producing`, `sort_bc`. This
reverses "THE BAR IS ONE HOLE NOW" (Stage A3, 7 September 2026), whose
reading of the original is unchanged and still correct — MOO2 lays
seven words along ONE recessed strip, `Add_Multi_Button_Field_(x, 446,
…)` at colsum.cpp:267-273, native y 446..469. What changed is the
artwork: Data's frame cuts a slot per key and places each by hand, so
the division is geometry rather than arithmetic. `colonysort.layout`
takes a rect per key and distributes nothing.

**THE GALAXY MASTER HAS SIX BOTTOM SLOTS, NOT SEVEN.** The work order
named `screens/galaxy_map/assets/frame.png` as the reference artwork
for the slot positions. Measured: 10 holes, and its bottom row is
**six** — (143, 1126, 253, 44), (444, …, 258, 44), (752, …, 252, 43),
(1051, …, 263, 43), (1365, …, 253, 44), (1666, …, 229, 44) of
2322x1256, stable at alpha < 8 / 16 / 64 / 128. They are the main
screen's six nav buttons, which is what `frame_holes.NAV_KEYS` has
always said. A seventh at the row's own pitch (301..314 px) would
start at ~1967 and end at ~2220, past the metal's inner edge at 2177,
so it is not a hole that was missed. **And there is no copy of the
galaxy master in `~/orionlayer-fixtures/gimp/`** to compare against —
that directory holds two colony fixtures of 11 September (the 8-hole
Stage A3 layout) and the superseded 14-hole colony frame.

**SO THE SEVEN COME FROM THE SUPERSEDED FRAME**, which is the only
seven-slot artwork that exists and is the frame this reversal goes
back to: `~/orionlayer-fixtures/gimp/frame_1920_retouched_2026-09-10.png`,
1672x941, whose bottom row is the seven sort buttons at image y 837/838.
Mapped with sx = 1920/1672, sy = 1080/941 — the whole-canvas stretch
`frame_holes.to_ref` applies. Data's artwork is not in the tree and
never will be, so the mapped rects are typed in `layout_reference.json`
and the image is cited beside them.

| box | rect, ref px | source hole | native x |
|---|---|---|---|
| `sort_name` | [162, 961, 198, 45] | (141, 837, 172, 43) | 89 |
| `sort_population` | [378, 961, 193, 45] | (329, 837, 168, 43) | 140 |
| `sort_food` | [588, 962, 194, 44] | (512, 838, 169, 42) | 219 |
| `sort_industry` | [798, 961, 196, 45] | (695, 837, 171, 43) | 262 |
| `sort_science` | [1011, 962, 195, 44] | (880, 838, 170, 42) | 326 |
| `sort_producing` | [1223, 962, 196, 44] | (1065, 838, 171, 42) | 393 |
| `sort_bc` | [1438, 962, **57**, 44] | (1252, 838, 170, 42) | 480 |
| `return` | [1512, 974, 288, 32] | unchanged, not placed here | 531 |

**TWO COLLISIONS, AND THE SLOT GAVE WAY BOTH TIMES.** `sort_bc` mapped
at its source width is [1438, 962, 195, 48] and runs to x 1633, **121
ref px into `return_button` at 1512** — the old frame carried RETURN in
its right-hand column, not on this row, so nothing there had to clear
it. The order is to shrink the slot and not RETURN, so the width is 57:
its right edge sits 17 px short of RETURN, 17 being the median of the
six gaps the source's own slots leave (18 / 17 / 16 / 17 / 17 / 19).
And the whole row mapped 4 px past the ring — slots ending at y 1010
against `ring.bottom` 74, whose inner edge is 1006 — so every slot lost
4 px off the BOTTOM and the top edge stayed where the artwork put it.
"Every window is inside the ring, per side" is on decision 53's
transcribed side and stays a check; the source frame's own bottom band
measures 61 px of 941, which is 70 ref against our 74, and that is the
whole of the 4 px.

**THE `in_row` RAIL BETWEEN SLOTS, REPORTED AND NOT RULED ON.**
`frame_build.lay_rail` scales the master's slot divider — 47 master px,
**38 ref** — across whatever gap the rectangles leave. The seven slots
leave six, and RETURN a seventh:

| gap | ref px |
|---|---|
| `sort_name` → `sort_population` | 18 |
| `sort_population` → `sort_food` | 17 |
| `sort_food` → `sort_industry` | 16 |
| `sort_industry` → `sort_science` | 17 |
| `sort_science` → `sort_producing` | 17 |
| `sort_producing` → `sort_bc` | 19 |
| `sort_bc` → `return` | 17 |

All seven are UNDER-stretched, where the old single gap to RETURN was
over-stretched 3.3x. No rule either way — "every gap equal to its
role's strut" left the suite on 11 September 2026 — and the numbers
come out of `tools/smoke_test.py` and `tools/colony_frame_check.py` on
every run. The band-to-slot gap is 9 ref px against the 22
`gaps.band_sort` documents, reported on the same terms.

**WHAT STAYED TRANSCRIBED.** The highlight is still the WORD plus
`HIGHLIGHT_PAD`, centred in its box, and explicitly **not the box's own
width** — the original lights native 92..138 around ink at 94..136
inside a field that runs 89..139, so the lit box grows with the word and
"Name" lights a short one where "Producing" lights a long one. A smoke
check asserts the tell rather than the construction: no two different
words may light the same width. Unchanged with them: the `native_click`
points and the hotkeys, RETURN's click path, the PRODUCING dimming
deviation and the typography deviation.

**NAMING STOPPED BEING AN INDEX.** `frame_holes` matches a hole to a
`layout_reference.json` rectangle by OVERLAP, rejects anything that is
not a clean bijection, and prints which way it went; the four-row SHAPE
(1 / 1 / 4 / 8, derived from the key lists) stays a check and is what
still catches a RETURN drifted into the band. Asserted by moving
rectangles, not by reading code: two slots are exchanged, a plate is
built from the swapped geometry, and each name has to come back on its
own hole — an index would call the second-from-left `sort_population`
and be wrong. `tools/colony_frame_check.py` handles 14 windows and
calls the same namer.

**THE ORIGINAL'S SORT LABEL NOW HAS AN OBVIOUS SLOT — REPORTED, NOT
BUILT.** The carry-over item parked since brief 78. Measured off the
native framebuffer (`~/Bilder/claude_scratch_2026-09-06/colsum_native.png`,
640x480): the word SORT is ink at native **x 23..74, y 456..462**, grey,
in the 77 native px between the list's left edge (12) and the first sort
field (89). That is **156 x 16 reference px** inside a 231 px run. Our
row leaves the corresponding space between the ring's inner left edge at
107 and `sort_name` at 162: **55 ref px** at the slot row's own y. So
the place is obvious and the size is not — the caption is 156 ref px
wide at the original's proportion and would have to be drawn at about a
third of it, or the first slot moved right when Data places the row.
Nothing was done: no box, no hole, no entry in `layout.json`.

### The sort bar takes the original's proportion — 11 September 2026 — SUPERSEDED 12 September 2026

**CLOSED, AND THE BOX IT IS ABOUT NO LONGER EXISTS.** `sort_bar` was
one hole; it is seven `sort_<key>` holes as of fundament decision 54,
so "the sort bar's width" has no referent and neither the 1281 nor the
124 px gap is a live number. Kept in full below because two of its
measurements outlived the box and are wanted by whoever places the
slots: **the original's strip is 24 native px high, y 446..469, which
is 54 reference px** — our slots are 45 and 44, still well short of
that proportion, same as the old bar's 32 was; and **`lay_rail`
stretches the `in_row` divider across whatever gap it is given**,
which is now six gaps of 16..19 ref px between slots and one of 17 to
RETURN, against the divider's own 38. Under-stretch rather than the
old 3.3x over-stretch, and the same thing to judge on the picture
rather than in an assertion. The three ways out named below are
unchanged and none of them is taken. What is DEAD here: the 1281, the
124 px gap, "the fill follows the hole and the seven labels
redistribute across the shorter bar" — nothing redistributes any more.

`sort_bar` was **1281 reference px wide**, was 1367. Derived, not
chosen: the original's strip is native x 89..515, **427 of 640**, and
427/640 x 1920 = 1281 exactly. RETURN is unchanged at
`[1512, 974, 288, 32]`, so the gap between them is **124 ref px**,
which is what the arithmetic leaves and not a number anybody picked.
The fill follows the hole and the seven labels redistribute across
the shorter bar; both were accepted in advance.

**THE HEIGHT WAS MEASURED AND NOT APPLIED.** The strip is 24 native
px, y 446..469, which is **54 reference px** against our 32 — our bar
is a good deal SHORTER than the original's proportion, and changing
it was not asked for. Recorded here so the next person does not have
to measure it again.

**AND THE GAP IS FILLED BY A STRETCHED MOULDING, which is visible.**
`lay_rail` scales a strut ACROSS its width to whatever gap it is
given, and the `in_row` strut is 47 master px — 38 ref. At 124 ref px
it is stretched **3.3x**, and the moulding's vertical ridges smear
into wide bands. The suite says so on every run now
(`gap at (1388, 974) span 124 | role in_row calls for 38 <-- DIFFERENT`)
because that enforcement became a report the same day. It is the
exact failure the dropped rule guarded — "a rail is never wider than
the strut it was cut from" — and it is now a picture to judge rather
than an assertion to pass. Three ways out if it should not stand, none
of them taken here: a wider strut sampled from the master for this
role, RETURN moved left so the gap returns to 38, or the gap left as
plain strut texture with no rail at all.

**A third thing worth knowing before either is resolved**: now that
the ring table is no longer asserted against the master, this same
bare-texture check still builds its coverage mask out of
`_lr["ring"]`. If the table and the artwork ever diverge, its mask is
wrong in a way nothing reports. It is correct today — the report line
at the ring block prints both numbers on every run.

### The colony frame is built, not rendered — 7 September 2026

Six image-tool renders were measured and none was usable
(`~/Bilder/rahmen/manifest.md`, which is the only place their
original names survive). Five had near-white metal 30 degrees off the
master's hue and **no interior windows at all**; the sixth was the
right frame at aspect 2.0163 — 13.4 % wider than 16:9 — letterboxed
into a 16:9 canvas, and **88 px short** of what a crop to 16:9 needs,
so every such crop cuts into its windows. `background.png` is a
derivative of `colony_summary/assets/frame.png`, stretched 13.4 %
horizontally: its header and its **seven** bottom slots match that
file's to three decimals. Nothing is derived from it.

So `tools/frame_build.py` builds the frame instead. A nine-slice out
of `galaxy_map/assets/frame.png`: the four corners lifted whole and
scaled once, the four edges stretched along their own length only,
the interior tiled with a strut texture, and the eight windows cut by
`frame_cut` from the mask.

**The strut patch is searched, not a coordinate.** It has to be metal
and at least 12 px from any hole so it carries no moulding, and among
those the FLATTEST — lowest luminance variance — because what is
wanted is the material and not the ornament. The first attempt took
the master's bottom band, which is the widest hole-free run it has
and therefore looked obvious; it contains that band's own ornamental
lines and tiling printed them across the interior every 64 px.
**Widest is not flattest.**

**The device ring comes from the windows, not from the table.**
`round(ring * scale)` put the plate's ring one pixel inside its own
first hole at 1440p — 106 where the table says 107 — because the
holes are placed by `Layout.rect`'s truncation. `device_ring` takes
it from the rectangles the holes are cut from, so the two agree by
construction. The check compares in DEVICE pixels for the same
reason: converting an edge back to reference asks
`round(int(107 * 4/3) / (4/3))` to be 107, and at 1440p it is 106.

**Resolution reach, and it is worse than expected.** The master is
2322 px wide, so 1920 is a **downscale** (×0.827) and **both** 2560
(×1.102) and 3840 (×1.654) are **upscaled interim variants**. Not
just 2160p: 1440p too. The tool says so per resolution when it runs.
A master at 3840 or wider would serve all three natively; until one
exists, two of the three ship upscaled and this paragraph is the
dated entry that says so.

**And the picture answers the question it was made for.** Laid at 2x
beside the frame shipped today: the ring, the corner plates and the
amber lamps come through and read as the master. The **plain struts
do not** — the master's metal has a median luminance of **2**, it is
dark material carrying bright ornament, so a strut with no bevel is a
slightly lighter black and is not distinguishable from the window
beside it. The frame shipped today looks like structure because every
strut has a highlight along its edge. Plain struts are what was
asked for and the picture is what they give; polish is a decision for
Data with the picture in hand.

### The list scrolls with the original's own two buttons — 7 September 2026

"N more not shown" was text where the original has controls. It is
gone; the arrows say the same thing and offer a way to act on it.

**THEY ARE NOT BOXES, and that is the decision.** The plate cuts no
hole for them (so not decision 3's cutouts), and the alternative was
two hand-placed boxes with a `thin_border` or `text` skin (decisions
34/37). They are neither: the rectangles come from
`colonytrack.columns(...)["scroll"]` — the same column table the
headings and the cells are laid in — and the list area's own top and
bottom. Two boxes would have been this screen's first non-cutout
entries and, worse, **a second copy of a position the column table
already fixes**. The cost, stated: the arrows are not F5-draggable,
which the rest of this screen's furniture is. That is the right trade
while the column table is the authority — move the column and the
arrows follow.

**Where the original puts them**: `_x_fields[1]` at native (619, 15)
and `_x_fields[2]` at (619, 316), `Add_Button_Field_`
(colsum.cpp:263-264), in the column right of BUILDING. Ours are in
the same column relative to the list; the native x is 1857 reference
px and our list ends at 1802, because the plate's ring is thicker
than the original's frame edge.

**A click does two things and only one of them is load-bearing.** It
moves HD's `Window.top`, which is what scrolls the picture, and it
activates the same field the original's button reaches — found by
its native coordinate in the LIVE field list (`colonysend.field_at`),
so a renumbered list cannot send the wrong one. **The send does not
make the two agree**: decision 46 is unchanged and `colonysend`
re-establishes `_first` from scratch before every injection, so an
arrow the game refused leaves the two out of step and nothing breaks.
It is a courtesy to a human watching both windows, and it is written
down that way so nobody removes the re-establishment on the strength
of it.

**Live on the reference save**, one click each, `_first` read off the
game's own scroll thumb:

    start        HD Window.top = 0   game _first = 0
    click DOWN   HD Window.top = 1   game _first = 1
    click UP     HD Window.top = 0   game _first = 0

**And the first measurement of that read 0 after the down click** —
the pre-effect frame the fundament describes: `ext::Tick()` runs
`ProcessInput()` before it serializes, so the first snapshot after a
send carries the world before the game acted. Waiting for the effect
rather than for a frame is what makes the table above true, and it
caught me out once more in the writing of it.

**The arrows are dimmed, not hidden, where the list cannot move.**
The original's buttons are always drawn and always clickable; a
control that disappears at the end of a list is a different
affordance from one that stops responding. `Decrement_First_` clamps
at 0 and the DOWN step is refused unless
`_g_colony_list_ptr[_first + 10] != -1` (colsum.cpp:796), so "cannot
move" is the original's own state.

**The check moved with the control.** "Ink appears under the last
row" became "the arrow that can move is drawn differently from the
one that cannot", at the top, in the middle and at the bottom of the
window — the same fault watched in the thing that replaced the
sentence — plus an assertion that the strip under the last row is now
EMPTY, so a renderer drawing both would fail. And the arrow rects are
asserted to come from `colonytrack.columns`, which is the rows'
own hit-test geometry (decision 5).

**Still not drawn: the proportional slider** between the two buttons
(`Draw_Bar_Indicator_`, colsum.cpp:747-753). That omission was
already recorded in `colonylist`'s module docstring and is unchanged;
what the arrows add is the two ends of it.

98 checks, unchanged: the two overflow checks became the two arrow
checks in place.

### Stage 3: the population figures are the game's own — 7 September 2026

**THE COLONISTS ARE SPRITES NOW, at three resolutions, beside the
original** (`figures_vs_original_{1920x1080,2560x1440,3840x2160}_3502.4.png`,
one snapshot each of the running game with the reference save loaded
— stardate 3502.4, 99 stars, 55 colony records, 11 the local
player's and not outposts, 10 drawn; save hash `ab70cc9ad5442335`
before and after, `~/Master of Orion 2` and the orion2re tree
unwritten). The species track the original's: Draconis V's four blue
Trilarian workers sit where the original puts them, and Blucher II's
thirteen farmers squish and overlap the same way.

**DECISION 50, extended in the same commit.** The figures come out of
the player's own `RACEICON.LBX` at an integer nearest-neighbour step
and are never scaled (decision 28). HD figure artwork is not a
project deliverable and the brief that had commissioned it is **withdrawn** — it is the one brief with no text to import, named only by `doc/briefs/75-brief-four-parts-three-commits-one-stop.md`; see decision 50 for why the filename is no longer cited.
A mod replaces figures per file — master or step, each alone.

**54 FIGURES, EVERY ONE 28 x 28**, and that is a measurement, not a
convention: across all 171 entries the six job sprites of every race
block and both shared sprites are 28 x 28 without exception, and only
`military_4` (35x28) and `military_5` (24x35) differ — neither drawn
here. 13 races x three jobs, 13 race portraits for a conquered pop,
plus native and android.

**THE STEP IS MADE IN THE LOADER, and that is the mod path's doing.**
A mod ships a 28 x 28 master and it has to arrive at the same size as
the base figure it replaces; a pre-stepping extractor would need a
second path to the same pixel (decision 5). And `figure_step` is now
the ONE home for the number — `colonytrack` took it from its own
`closest_resolution` call until this commit, and a track laid at 3x
holding sprites loaded at 2x is a picture neither module would report.

**THE MOD PATH: one PNG, one name, one folder, restart.**
`assets/shared/figures/<race>_<role>.png`, race keys from the
SOURCE's `STOCK_RACE` and never the localised `_race_names[]`, so a
mod keeps working on a translated install. Beside the master,
`<name>@2x/@3x/@4x.png` at exactly 56/84/112. For one figure at one
step: **explicit step file, then stepped master, then the next
root** — resolved inside each root before moving on, which is what
`Resources.roots()` was added for. Two `resolve` calls would let a
base step file outrank a mod's master, and then a one-file mod is not
one file. A wrong size is refused with one log line and the base
figure is drawn; nothing is ever stretched to fit.
`doc/modding_figures.md` is GENERATED from the loader's table and
compared byte for byte.

**I WAS ABOUT TO CENTRE THE FIGURE IN ITS CELL. The original does
not.** `animate::Draw_((30 - _step_squish) * pop_draw_index + left_x,
top_y, anim)` (coldraw.cpp:349) places the sprite at the slot's own
left edge and at `top_y`, the ROW's top. Centring looked obviously
right and was an invention, and it had a visible cost: the HD cell is
2:1 (the pitch is stepped, the bar height is not), so a 56 px figure
sat 13 px above and below a 30 px bar and, at 1440p, four px into the
rows either side. Top-left, transcribed, is both correct and the fix.

**THE ONE RESOLUTION WHERE THE FIGURE DOES NOT FIT ITS ROW IS
2560x1440, and the reason is the integer step itself.** 1440p takes
step 3 where proportion wants 2.67, so the figure is 12.5 % larger
there relative to the layout than at 1080p or 2160p: 84 px against a
77 px row, where the other two are 56-in-58 and 112-in-116. That is
decision 28's known cost arriving somewhere specific. The row clips
vertically — never horizontally, because horizontal overflow IS the
overlap — and **the clip is measured to be lossless**: every master
carries at least three transparent rows below its ink (the tallest
ink is `alkari_farmer`, 24 of 28 rows), which is nine px at step 3
against seven px to find. A smoke check recomputes that margin from
the files, so a future sprite set with a fuller canvas fails here
instead of losing feet on screen.

**THE OVERLAP DRAWS LEFT TO RIGHT**, asserted in pixels:
`pop_draw_index++` is at coldraw.cpp:377, AFTER the draw at :349, so
each figure covers its LEFT neighbour's right edge.

**THE CLICK DID NOT MOVE, AND IT FOLLOWS THE SLOT, NOT THE INK.**
`case 4` (coldraw.cpp:367) takes the first slot whose right edge is
at or past the pointer — the LEFTMOST, which at an overlap is the
figure partly underneath. The original's own click and ink disagree
there. `colonyicons.slot_at` already transcribed it; "the click
should follow the visible figure" is the invention, and a check now
says so.

**Stage 5's deletion list, with one exclusion. DONE 12 September 2026,
and what it deleted was not what it expected** — the "superseded
frame" turned out to be the frame this screen wears, and it is the
PLATE machinery that went (decision 55). The exclusion held exactly as
written: the coloured cell renderer stays. The re-targeting turned out
to be nothing to do — none of the deleted files carried a marking.**

**STAGE 5'S TAIL, AND IT IS SHORT — 21 September 2026, work order 156,
commit A.** The inventory that opened that order went looking for "old
modules that were superseded but never deleted" and found none: the
12 September list above is the whole of it. What was left was dead code
inside live modules, and this is everything that went, with what
replaced each one:

| removed | where | replaced by |
|---|---|---|
| `_render_title` and its call | `screens/colony_summary/screen.py` | nothing — it read `frame.title_rect`, absent since Stage 4, so it returned before drawing on every frame since |
| `TITLE_COLOR` | same file | nothing — `_render_title` was its only reader |
| `FRAME_TITLE = "Colonies"` | same file | nothing, and see the correction below: the reader both documents named does not exist |
| `colony_summary.title` | `assets/shared/skins/default/colors.json` | nothing — `TITLE_COLOR` was its only reader |
| `frame._title_note` | `screens/colony_summary/layout.json` | nothing — it described the SUPERSEDED frame's title bar and contradicted `_no_title_note` beside it |
| `helpformat.from_json` | `core/helpformat.py` | nothing — the inverse of `to_json`, for a cached or exported form that never arrived |
| `colonypick.column_of` | `screens/colony_summary/colonypick.py` | nothing — no caller in any `.py`, `.json` or `.md` in the tree |
| `nebula_fraction`, `star_fraction`, `black_hole_fraction`, `ship_icon_fraction` | `core/zoomtables.py` | nothing — four "native px → fraction of map width" helpers with no caller. `GALAXY_MAX_SCALE` beside them STAYS: its comment says "Kept for diagnostics", which is a reason |

**No marker moved, because none of these files carried one on the
removed code.** `core/zoomtables.py` and
`screens/colony_summary/colonytrack.py` are both in the suite's
`_MARKED` inventory and both keep their markings (`INSET_DOT_DIM` and
`DEVIATION IN HEIGHT`); `screens/colony_summary/screen.py`,
`core/helpformat.py` and `colonypick.py` are not in it and did not
become empty of one.

**The evidence that nothing on screen moved.** `tools/
colony_list_preview.py` drives the real `ColonySummaryScreen.render`,
and all sixteen PNGs it writes at 1920x1080, 2560x1440, 3840x2160 and
1366x768 are **byte for byte identical** before and after. That is
weaker evidence than it looks and it is worth saying why: the
fundament's rule is that byte-identity proves only the paths that were
EXERCISED. Here it is not the licence — the licence is that
`title_rect` is absent from every `layout.json` in the tree, so the
deleted branch could not be reached by any input. The renders confirm
that reading rather than standing in for it.

**Exactly the inventory's projection: −29 CODE lines** (41 818 →
41 789 by `tools/linecount.py`, `core/` −12 and `screens/` −17; total
lines −43). It landed on the estimate by coincidence rather than by
accuracy — one MORE deletion was found while the commit was being made
(`FRAME_TITLE`, see the correction under "The title is gone"), and the
eight-line comment that records why it went is documentation and not
code, so `screens/` comment lines went UP by 8 in the same commit. The
number to judge this by is the CODE column, which is decision 6's
amendment and the reason that column exists.

**Stage 5's deletion list, with one exclusion.** Stage 5 deletes the
superseded frame and its flag, and re-targets the old markers. **The
coloured cell renderer stays.** Criterion 5 of this stage makes the
cells the picture an install without the extraction sees — the
loader reports `missing`, the row renderer takes `None` and draws
what it always drew, and the screen names the command. That is a
state of the figures feature, not superseded code, and the list is
drawn with it excluded so nobody has to re-derive that later. Also
recorded beside the frame-flag sentence, where a reader of Stage 5
meets it.

**`tools/raceicon_extract.py` was never in `setup.py`** — help,
nebula, techname and estrings all were. It is now, checked by the
FIRST file of the set rather than by the directory, because an
interrupted extraction leaves a directory that exists and is short.
The tool also went over the 300-line guideline, so the three
reference-sheet composers moved to `tools/raceicon_sheets.py` along
a seam its own docstring had already named: `assets/shared/figures/`
is the set the tree LOADS and `raceicon_ref/` is a set nothing loads.
The exceptions list is unchanged.

**The row dict carries a `Cell`, not a string.** A cell now holds
its identity class AND the figure it draws, because both are
branches of the same `Colony_Pop_Anim_` read (colony.cpp:1268-1283)
and two parallel tuples indexed alike is one rebuild away from a cell
that wears an N and draws an android. The conquered test comes FIRST
in that function, so a conquered native draws a portrait — reordering
it reads as a simplification and changes the picture.

**`colonyrows` still imports no pygame.** It imports `colonyfigures`
for `figure_for`, which would have pulled pygame in transitively and
quietly ended the property its docstring claims. The naming half of
that module is pure arithmetic; the loading half imports pygame where
it uses it.

100 -> 102 checks.

### The BUILDING column fills: ESTRINGS, and three things it exposed — 7 September 2026

**IT SAYS "Trade Goods" NOW, on all ten visible rows, matching the
original word for word beside it** (`estrings_building_column_3502.4.png`,
one snapshot of the running game with the reference save loaded —
stardate 3502.4, 99 stars, 55 colony records, 11 the local player's
and not outposts, 10 drawn; save hash `ab70cc9ad5442335`, unchanged
before and after). The `- 1t` suffix the original appends stays off
and stays OPEN, for the reason `build._turns_note` already carries.

**THE COLUMN WAS READING THE WRONG TABLE FOR EVERY ROW IT HAD.**
`COLBLDG::Selection_Name_` (colbldg.cpp:796) has THREE branches. A
BUILDING id goes to techname.lbx; everything that is not a queued
ship goes to `Option_String_` (colbldg.cpp:2338), a seventeen-case
switch of `E_Strings_` indices out of the player's own **estrings.lbx**;
a queued ship goes to `_ship[i].d.name`. The reference save takes the
OPTION branch on every row — `producing[0]` is -2, TRADE_GOODS,
`E_Strings_(0x21D)`. Widening the techname walk would never have
reached it. `core/prodname.py` is now the ONE function both the
column and the sort key call (decision 5); the third branch is
answered with a stated absence, not a guess, because ship names are
not on the wire (`core/structs/ship.py` verifies five fields, and a
name at a guessed offset is decision 23).

**`tools/estrings_extract.py`, the help-text pattern's third use**
(decision 38). The language picks the FILE here — estrings /
estrGERM / estrFREN / estrSPAN / estrITAL / estrPOLI — and it is
always entry 0, where TECHNAME is one file whose ENTRY is the
language. The walk is `Load_E_Strings_`'s own (estrings.cpp:11-37):
`strlen + 1`, **no NUL-run skipping**, so an empty string is a valid
entry. `Advance_To_Next_String_` skips runs and is TECHNAME's; a
check now shows the two walks disagreeing on the same bytes rather
than asserting in prose that they differ.

**THE OFF-BY-ONE, and how it was caught.** The first walk started at
byte 0 and produced 812 plausible strings — but Trade Goods sat at
`0x21E`, which is Transport Ship. `Farload_Library_Data_` reads
`total_count` and `element_size` as two uint16s and seeks to
`sizeof(total_count) + sizeof(element_size) + element_size *
start_idx` (farload.cpp:88-92, :107): a **4-byte header**. The entry
is 21004 bytes, the header says 21000, and 21004 - 4 = 21000. With
it skipped, THIRTEEN of the thirteen non-empty option ids land on the
exact word their enum names — including the crossing pair, -5 WORKER
to 0x0B2 'Android Worker' and -6 SCIENTIST to 0x0B1 'Android
Scientist', which is out of numeric order in the source too and which
no shifted or self-consistent table could reproduce. Three anchors
would have been an argument; the crossing is the proof.

**`is_building(0)` WAS WRONG AND NOTHING COULD SEE IT.**
`Colony_Production_Is_Building_` is `id > BUILDING_NO_BUILDING && id <
BUILDING_COUNT` (colbldg.h:16) — 1..48. Ours said `0 <= id < 49`, and
`Option_String_` claims 0 with an explicit `case 0:` returning the
empty string. A colony producing 0 would have shown `_buildings[0]`,
"No Building", where the original shows nothing. The smoke check
asserted `is_building(0)` and passed, because it had been written
from the same range the code had rather than from the predicate. It
became visible only when a second branch existed to disagree. Both
bounds now spell the named constants.

**An empty string is a VALUE here, so the derived file is a dense
list.** `E_Strings_(0x00C)` is `""` — what NONE, SEPARATOR and 0
resolve to — so a table that stored only non-empty entries could not
tell "the original prints nothing" from "no such index". 812 entries,
length checked at load, `None` reserved for out-of-range.

**The `producing` sort key no longer falls back to the planet name,
and stays declared unavailable.** `cmp_Prod_` (colsum.cpp:1091) is
three levels, and `Switched_cmp_` case 5 does NOT negate while
`cmp_Prod_` negates twice internally — so producing is DESCENDING on
tier and DESCENDING on name (`strcmp`, case-sensitive, unlike
`cmp_Alpha_`'s `strcasecmp`), not ascending as this project's table
said. `Prod_To_Sort_Type_` transcribes completely except for
`_buildings[].cost`, which is not extracted; since cost >= 0 the
building band still sits where the source puts it, above every option
and below FREIGHTERS and every ship. So the key is RIGHT on the
reference save and would order two buildings by name where the
original orders them by cost. Right on one save and wrong on the next
is worse than a control that says it cannot do the job, so
`SORT_UNAVAILABLE` keeps it with a narrowed reason.

**The word lists are NOT switched, and 23 of 26 agree anyway.**
Reported, not changed: `words.sizes` (0x2AB, 0x1E0, 0x173, 0x168,
0x143), `words.minerals` (0x2AC, 0x1A7, 0x2AD, 0x1C2, 0x2AE),
`words.gravities` (0x2AF, 0x2B0, 0x2B1) and `list.climates` (0x21B,
0x2CF, 0x2D0, 0x2D1, 0x2D2, 0x18F, 0x1F5, 0x0B8, 0x2D3, 0x12F) are
all readable now. Every size, mineral and climate is letter for
letter ours already. **The three gravities differ, and they falsify a
claim this project had written down.** `words._note` said
colland.cpp:65 prints the table entry with no format, so "Normal
Gravity" must be in the table. The first half is right; the table
holds **"Normal G"**. The scan box's own format, `E_Strings_(0x4A)`,
is `'%s%s %s \n%sravity\nMineral %s\n...'` (colsum.cpp:1194-1200) —
the slot is `%sravity` and the table supplies the G. The note is
corrected and both halves are pinned. A footnote worth keeping:
"Normal G" was once rejected here as an enum name in title case, and
it is also, letter for letter, the game's own string — the rejection
was right for the wrong reason.

**The row dict's docstring claimed a check that did not exist.** It
said a smoke check held the fake rows to the same key set; nothing
did, which is how `producing_id` and `producing_state` could have
been added without the fixtures following. The 22 keys are read off
`build_rows` with AST and pinned, and the docstring is asserted to
list the new two.

98 -> 100 checks.

### The BUILDING column: the names are extracted, and the reference save needs a second source — 7 September 2026

**PARTLY BUILT, AND THE STOPPING POINT IS THE POINT.**

`tools/techname_extract.py` follows the help-text pattern exactly
(decision 38): it moves the bytes out of the player's own
TECHNAME.LBX untouched, `core/buildnames.py` decodes at load time,
the file is format-versioned, gitignored, in `setup.py`'s report, and
an absent file is a state the column explains rather than an empty
cell. It reads **49 of 49** building names on the first run.

**The walk is transcribed, and the offset is computed rather than
measured.** `TECHINIT::Load_Tech_Names_` (techinit.cpp:43) loads ONE
entry — `techname.lbx` entry `_settings.language` — as a block of
NUL-separated strings and walks it with `Advance_To_Next_String_`
(techinit.cpp:11-21: skip to the next NUL, then skip EVERY NUL after
it, so a run of NULs is one separator). The order is fields,
applications, buildings, specials, armor, shields, weapons, so
building `id` is string `TECH_FIELD_COUNT + TECH_APP_COUNT + id` =
`295 + id`. Those three counts are `orion2_consts.h` enums with
`static_assert`s beside them (83, 212, 49) — the second source for
the offset, and the reason it is a transcription rather than a
number that happens to line up. A check pins the counts and three
names at known ids, so a walk that slips by one string fails instead
of showing a plausible wrong word.

**AND THE COLUMN IS STILL EMPTY ON THE REFERENCE SAVE. This is where
the part stops.** Every one of the eleven colonies carries
`producing[0] == -2`, and −2 is `COLONY_PRODUCTION_TRADE_GOODS`
(orion2_consts.h:67) — **not a building**.
`COLBLDG::Selection_Name_` (colbldg.cpp:796-802) has three branches
and only the first reads `_buildings[]`:

    Colony_Production_Is_Building_(id)  -> Real_Building_Name_(id)
                                          = _buildings[id].name
    not a queued ship                   -> Option_String_(id)
    otherwise                           -> the ship design's name

`Option_String_` (colbldg.cpp:2338) resolves every option through
**`ESTRINGS::E_Strings_`** — Trade Goods is `E_Strings_(0x21D)` — and
that is a **different LBX with a different walk**:
`Load_E_Strings_` (estrings.cpp:11-37) reads entry 0 of
`estrings.lbx` (or `estrGERM/FREN/SPAN/ITAL/POLI.lbx` by language)
and advances `strlen(s) + 1` per string, **without** skipping runs of
NULs — so an empty string is a valid entry there and the TECHNAME
walk would mis-index it.

The horizon named techname.lbx as the source. It is the source for
BUILDINGS and it is not the source for what this save actually
builds. **Per the brief — "if the LBX is not where the pattern
expects … report and stop this part; do not build a second
string-format interpreter without saying so" — the ESTRINGS
extractor is not built.** It is small and fully sourced
(estrings.cpp:33-36 is the whole walk); it needs Data's word, and the
question is whether one derived file should carry both tables or
whether ESTRINGS gets its own.

**What the column does meanwhile is honest, not blank-by-accident.**
`producing` is None for an option id and for an absent file, and the
two are told apart by the loader's `state`: the "names not extracted"
wording appears only when the file is genuinely missing or stale, so
Trade Goods draws nothing rather than accusing the user of not having
run a command they have run.

**The "- 8t" suffix is OPEN, not approximated.** The original appends
it from `COLONY::Calculate_Current_Production_Turn_Count_`
(colsum.cpp:588), a cost calculation over the colony's accumulated
production and the item's price; neither the cost table nor the
accumulation is established on the wire. `producing_turns` stays 0
and the suffix is not drawn, with the reason in
`layout.json` under `build._turns_note` and a check that holds it
there.

97 -> 98 checks.

### Stage 4 closed: the pitch, the 4K readouts, and three readings — 7 September 2026

**A1. THE CELL PITCH WAS THE COLUMN RATIO. It is the sprite step
now.** Stop 3 laid cells at `column_pitch(job, count)` times
`room / native_column_width` — about **2.7** at 1080p for farmers
(342 reference px over 125 native). That is the case the stacking
decision excludes: HD's extra width goes into the column RESERVATION
and never into figure spacing, and a ratio spends the reservation on
spacing. Left alone, Stage 3's sprites at the integer step would have
moved every cell and every drop target a second time.

The factor is `zoomtables.FIGURE_STEP` (decision 26), picked by
`core.box.closest_resolution` over the table's own keys:

| window | layout scale | table key | step |
|---|---:|---|---:|
| 1920x1080 | 1.000 | 1920x1080 | **2** |
| 2560x1440 | 1.333 | 2560x1440 | **3** |
| 3840x2160 | 2.000 | 3840x2160 | **4** |
| 1280x720 | 0.667 | 1920x1080 | 2 |

**One function feeds both paths** (decision 5):
`colonyicons.column_pitch` is what `slot_click_x` multiplies for the
NATIVE click and what `_column_boxes` multiplies by the step for the
HD rect. The step is applied on the HD side only; the wire never sees
it.

**AND IT OVERFLOWS AT ONE WINDOW — a finding, not a reason to go
back.** The original's own run is at most `right_x - left_x - 10`
native px (the `spacing / -3` term in `Calculate_Squish_Step_`), so
at the step it needs that times the step. Room is the column less the
marker and the gap:

| window | column | marker | room | needs | |
|---|---:|---:|---:|---:|---|
| 1920x1080 | 343 | 30 | 311 | 230 | fits |
| 2560x1440 | 457 | 40 | 415 | 345 | fits |
| 3840x2160 | 686 | 60 | 622 | 460 | fits |
| **1280x720** | 229 | 20 | **208** | **230** | **clamp fires** |

(farmers; workers and scientists behave the same.) The worst count is
**6** for scientists, **5** for farmers and **11** for workers — the
pitch clamps at `ICON_SPACING` below four pops, so the widest run is
just past that. 1280x720 resolves to the 1080p step and gets a column
two thirds the width, so the run needs 230 device px in 208.

**What the original does at that count is fill and stop**: its column
is fixed too and `squish_step` divides `right - left - 10` by the
count, so the run never leaves the column. Ours now does the same —
a `min` in the shape of decision 44, so the clamp ends the day the
reservation is wide enough rather than being a special case for one
window.

**A2. THE 4K EMPIRE READOUTS READ THE SCALE TWICE.** Confirmed by
arithmetic and by the picture. `ScreenBase.box_font_scale` multiplies
the stored value by `win_h / 1080`, and `colonyempire` then went
through `Layout.font_size`, which multiplies by the window scale
again:

| window | auto | layout scale | net | intended |
|---|---:|---:|---:|---:|
| 1920x1080 | 1.000 | 1.000 | 1.000 | 1.000 |
| 2560x1440 | 1.333 | 1.333 | 1.778 | 1.333 |
| 3840x2160 | 2.000 | 2.000 | **4.000** | 2.000 |

**The colony summary carries no tuned `font_scale` on any box**, so
there was nothing to cancel it: the six values came out at twice
their size at 4K and collided with their labels. This is the help
popup's fault a second time — the fundament already says "anything
that must work at an untuned resolution reads the stored scale
directly", and `screenhelp` had solved it privately with
`_help_font_scale`. **A second private copy is how the third one gets
written**, so the accessor is extracted:
`ScreenBase.box_font_scale_stored`, and `screenhelp` now calls it.

The check renders the box at all three resolutions and reads INK, not
the renderer's own expression: value ink must stay inside the box and
every row's label must end left of where its value starts. Verified
to fail — with `box_font_scale` put back it reports *"3840x2160: on
row y=57 the label reaches x=361 and the value starts at x=337"*, and
1080p and 1440p still pass, which is the shape of the whole fault.

**The grep found more, and it is NOT all fixable here.** 68 boxes
carry a hand-tuned `font_scale`, and **not one of them is tuned at
3840x2160** — every screen's list stops at 1440p, so at 4K they
resolve by pixel area to the 1440p list and take the same 4.0 net
factor. Custom Race, Select Race, Empire Identity and the galaxy map
all pass `box_font_scale` into a `Layout.font_size` afterwards. They
are NOT changed here, and the reason is the trap: those values were
tuned BY EYE with the double factor already in place, so they encode
it, and un-doubling them without re-tuning would shrink every one.
Colony summary is the clean case — no tuning to break. **Re-tuning
the other four screens for 2160p is a separate decision and is not
Stage 4's.**

**A3. Three readings from the Stop 3 images.**

- **The list window is OURS, by decision 46, and the two images were
  taken at different moments.** Our first drawn row is
  `Window.top(...)` — HD's own scroll state, 0 — while the game's
  `_first` was 1 when the native was captured, which is why ours
  begins at Blucher II and the native at Blucher III. Decision 46
  allows exactly this: the HD list scrolls freely for VIEWING, and
  `_first` is re-established before anything is injected, which
  `colonysend` does on every move. **Not a Stage 3 or Stage 5 item —
  it is settled behaviour**, and the manifest now names the moment
  each image was taken.
- **The empire values are transcribed struct fields, not our
  computation.** Rendered from ONE snapshot, ours reads 878 / +42 /
  78 / 17 / -3 / 27 and the original's own panel in the same frame
  reads 878 / +42 / 78 / 17 / -3 / 27 — six for six. The earlier
  disagreement (+45, -1, 25) was the PICK/DROP runs having moved
  pops between the two captures. The second source for each is the
  original's own screen at the same moment, and the fields are
  `s_player`'s `bc`, `surplus_bc`, `total_pop`,
  `surplus_freighters`, `surplus_food`, `research_produced`, which a
  check already holds to `Draw_Empire_Info_`'s print order.
  **Nothing here is ours by computation and nothing goes to this
  document as unverified.**
- **The scroll control is MISSING, not interim, and this entry is
  where it stops being silent.** The header's 36 px slot is empty
  and the overflow is the text "N more not shown" at the list's
  bottom-left. The original has a scroll bar with arrows in that
  column — `_x_fields[1]` and `[2]`, `Decrement_First_` /
  `Increment_First_` (colsum.cpp:211-226), the same two fields
  `colonysend` already activates to establish `_first`. HD scrolls
  on the wheel and by hover, so nothing is unreachable; what is
  missing is the CONTROL and the affordance. **It belongs to the
  stage that draws the list's furniture — Stage 3** — and it is
  named here so it is not mistaken for a decision.

**A4/A5.** The wrong-game runs are in the fundament under Evidence as
their own line, beside "a test that reads the user's disk" and not
merged with it: that one is about a result that varies with the
reader, this one about a result that is perfectly stable and silent
about its subject.

95 -> 96 checks.

### Stage 4, Stop 3: the rows move into the columns — 7 September 2026

The list draws in the five columns now, in cells, each group under
its own heading. The name column, the ellipsis threshold and "No
Farming" are unchanged; what moved is where a job's cells are.

**THE PITCH IS THE ORIGINAL'S OWN, SCALED.** Each job column lays its
cells at `colonyicons.column_pitch(job, count)` —
`COLDRAW::Calculate_Squish_Step_` (coldraw.cpp:12-33), already
transcribed in the tree for the click path — multiplied by that
column's HD width over its NATIVE width. A column that squeezes in
the original squeezes here by the same amount. The HD row is the
original's own walk under a scale factor, not a second layout that
resembles it.

**IDENTITY IS BY INDEX, WHICH IS WHAT MAKES THE DRAWING FREE.** Cell
k of job j is slot k of the game's column j: `colonysend` injects
`colonyicons.slot_click_x(j, k, count)`, a native x from the same
`column_pitch`. Nothing is transferred from the HD rect into that
call — the two share an index and a count and each works in its own
pixels. **A third source for the column bounds arrived live**: the
colony summary's own FIELD_LIST reports fields 28/29/30 at x 101,
236, 378 — the literals from `Get_Selected_Pop_`, on the wire.

**AND THE CHECK CAUGHT A REAL ONE, of exactly the kind it exists
for.** The marker's width was `min(h, cw // 8)`, and `h` is 0 when
`row_boxes` is called without a band — which is how `cell_at_x` calls
it. So the marker was 2 px wide in the hit test and a full square on
screen, and every cell in the row sat at a different x in the two.
The picture and the click would have disagreed by one marker's width,
with every count on screen correct. It is `track.bar_h` now, which is
band-independent. Found by the check that samples each DRAWN cell's
own pixels and asks what picks up there — the one written because
"they call the same function" is not the same as "they get the same
answer".

**No growth boxes in this layout.** They belong to the COLONY, not to
a job, so in a row of three job columns there is nowhere for them
that is not a lie — a dashed box inside the scientists column says
"scientists". The headroom is already on screen where the original
puts it (`Population (13/22)`, colsum.cpp:1196-1205).

**AND THE TWO EMPTY FIELDS ARE GONE — 21 September 2026, work order
157, closing 156's part C.** This paragraph used to end "The code and
its marking stay; Stage 5 decides whether they return somewhere
honest", and `colonytrack.py` said the same. **What stayed was not
code with a marking.** It was `RowBoxes.growth` and `RowBoxes.beyond`,
returned `()` and `None` by every construction site since `514ebb2`
replaced the allocation bar with six column boxes on 8 September, and
carrying no marking at all. Both belonged to that bar, which was an
INVENTION — the original's row draws population sprites and nothing
else (`Do_Colony_Info_Pop_Stuff_For_Pop_`, coldraw.cpp:282) — so with
the bar gone there was no place left for either value. Unmarked empty
fields left over from a removed invention are residue.

**The question they stood for is NOT closed, and the note now states
it in the terms it actually turns on.** A per-row capacity display is
an open design question for Data. The original shows headroom only as
a number, in the scan box, and only for the colony being scanned
(`Draw_Colony_Scan_Info_`, colsum.cpp:1155), so a per-row display
would be an **HD EXTENSION and would have to be marked as one** — the
same family as the per-row detail line. If it comes, it is built new
against the six column boxes and does **not** bring back `growth`,
`beyond` or `growth_gap`: a display on a track that no longer exists
would be a second geometry beside the columns, which is decision 5's
fault. The old code is at `514ebb2`'s parent for the bar, and at work
order 157's part-1 commit for the fields.

**The markers stay, and their reason has been overtaken.** They were
an HD EXTENSION because "a row without columns cannot carry a
heading"; the row has columns and headings now. They are not removed
here because a marking is re-targeted in the commit that deletes what
it marks — Stage 5 — and until then the marker is still drawn and
still marked.

---

**THE LIVE PROOF, AND IT IS NOT CLEAN.**

**Columns 0 and 1 pass.** On the reference save, one PICK and one
DROP each through the real `App` and a real `MOUSEBUTTONDOWN`:
*"colonies whose bytes changed: 10 = Blucher II"* and *"every pop
word matches the prediction"*, with the first click sending nothing
and the outline sitting on the cells the pick names.

**Column 2 MISMATCHES, reproducibly. THIS BLOCKS STAGE 3.** A
research-to-food move on Blucher II reports "1 moved" and the
predicted pop word is right, but a SECOND colony's bytes change —
always the next index. Reproduced on a freshly loaded reference save
with nothing before it. The exact lines, from both tools:

    tools/colony_move_hd.py --job 2 --commit
      fixture: reference (99 stars, stardate 3502.4) — the run is
        about this save
      target: row 0 'Blucher II' jobs=[12, 0, 1], cell 0 of column 2
        -> column 0
      held locally: Pick(colony=10, job=2, slot=0, pop=11, size=1),
        slots (0,)
      the outline sits on the cells the pick names
      the first click sent nothing, which is the whole design
      finished: '1 moved'
      sends: activate_field=1, inject_click=2, inject_key=2
      colonies whose bytes changed: 10 = Blucher II, 11 = Blucher III
        EXPECTED EXACTLY [10] — another colony changing is the
        invisible failure this run is built against
        MISMATCH

    tools/colony_move_probe.py --commit          (no HD geometry)
      _first read off the scroll thumb: 1
      target: row 0 'Blucher II' jobs=[13, 0, 0] column 0
      pick-up field (230, 49), drop field (372, 49)
      held cluster matches the prediction: colony 10 pops [12]
      colonies whose bytes changed: 10 = Blucher II, 12 = Wolf II
        EXPECTED EXACTLY [10] — a different colony changing is the
        invisible failure this whole sequence is built against
        MISMATCH

**It is NOT the HD geometry.** The probe computes a native click from
`colonyicons` and injects it without touching a single HD rect, and
shows the same shape — on a FARMER move, which is why the second
listing is column 0. So either the game rewrites another colony's
record on a pop move — decision 48 already records that
`Enforce_Population_Limits_At_Colony_` shuffles a whole array on four
occasions, one of them a building completing — or both tools' "exactly
one colony" rule is too strict and is measuring the wrong thing.

**DIAGNOSED AND CLOSED — 7 September 2026.**

**By field, not by offset.** The second colony's `pop[]` is
byte-identical; only `imports[ECON_FOOD]` and `pop_growth` change.
The tools were diffing whole records where the claim they wanted was
about `pop[]`.

**It is not column 2.** The same colony, three moves: scientist ->
farmer (a cluster of 7, food 10 -> 22) changed a second colony;
farmer -> worker and worker -> farmer (one pop, food 22 -> 20 -> 22)
did not; and a **farmer** cluster of 11 (food 22 -> 0) changed the
same second colony in the same two fields. What separates the cases
is the size of the food swing, not the source column.

**The writer.** `Send_Cluster_` (colmove.cpp:460-463) ->
`Col_Calc_Wrapper_` (colony.cpp:1091) -> `Colony_Calculation_`
(colcalc.cpp:1580) -> `Recalculate_Colony_` (colcalc.cpp:519-524) ->
`COLCALC::Pass_Out_Imports_` (colcalc_main.cpp:208), which
redistributes the whole player's food: `imports[ECON_FOOD]` on every
non-outpost colony of the owner (:222, :228, :254, :268), and
`pop_growth` / `pop_roundoff` / `specialty` on every NEEDY one via
`Post_Import_Computing_` (:341-352 -> colcalc.cpp:891).
`Enforce_Population_Limits_At_Colony_`, decision 48's candidate, is
not on this path; `Update_Player_Stats_` reads every colony and
writes only to `s_player`.

**"Always the next index" was coincidence.** The player has five
needy colonies (5, 7, 10, 11, 12); `needy_colony_indices` is filled
in index order and walked round-robin, so the colony at the margin of
the allocation moves — one above the moved colony, three times.

**The rule now has a home and a source**:
`colonymove.move_diff_verdict`, read by BOTH acceptance tools.
Exactly one colony's `pop[]` may change; any other colony may differ
in `imports`, and a colony whose food balance is negative
(`production[FOOD] - maintenance[FOOD] < 0`, colcalc_main.cpp:219)
additionally in `pop_growth`, `pop_roundoff` and `specialty`. Nothing
else, anywhere. It is **stricter** than the rule it replaced, which
accepted any byte difference on the moved colony.

**Two things it cannot see, stated rather than hidden**: the source
also excludes a blockaded colony and one in a space anomaly, and
neither flag is on the wire, so a blockaded needy colony is allowed
here where the game would not have written it.

**Proved able to fail before it was trusted.** Four synthetic diffs
against the rule function: a second colony whose `pop[]` changed
FAILS, one whose `production` changed FAILS, a **non-needy** colony
whose `pop_growth` changed FAILS, and a changed record that will not
parse FAILS; a needy colony's `pop_growth` and any colony's `imports`
PASS. All six are in the smoke test.

**Live, on the reference save, all three columns and the native-click
probe:**

    fixture: reference (99 stars, stardate 3502.4)
    target: row 0 'Blucher II' jobs=[12, 0, 1], cell 0 of column 2
      -> column 0
    the outline sits on the cells the pick names
    the first click sent nothing, which is the whole design
    finished: '1 moved'
    colonies whose bytes changed: 10 = Blucher II, 11 = Blucher III
      colony 11: pop_growth — allowed, the colony is needy and
        Post_Import_Computing_ rewrites it
      colony 11: imports — allowed on any of the owner's colonies,
        Pass_Out_Imports_ rewrites it
      every pop word matches the prediction

**Stage 3 is unblocked.**

---

**AND THREE ACCEPTANCE RUNS WERE MADE AGAINST THE WRONG GAME, which
is the finding worth the most here.** The first set of column proofs
was clean: clicks landed, pop words matched predictions, no other
colony changed. Every line of it was true and none of it was evidence
about the reference save — the game had a 71-star galaxy loaded, and
nothing in the run said so. The status document already required that
"anything below that reads a save reads it by its fixture name"; this
tool did not. `colony_move_hd.py` now identifies the fixture before
it claims anything — stardate AND star count AND colony count,
because 3502.4 and 3502.5 are one tick apart and any game reaches
them — and a wrong save stops the run with what it saw:

    WRONG SAVE. This run claims reference {...}, the game has
    {...} — which is the natives fixture

**Two open items, neither introduced here, both to be decided before
Stage 3 draws:**

- **The producing text is empty.** Every row carries
  `producing=''`, so the BUILDING column draws nothing, while the
  original shows "Trade Goods - 1t" per row. The column is placed
  and its width is the transcribed reservation; what is missing is
  the value. Pre-Stage 4 — the single-track row drew nothing there
  either.
- **`planet_info` is still empty**, as recorded above.

95 checks, unchanged: this stop added no check. The column rule
replaced the flush-run rule inside the existing drop-target check,
which is the same check watching the same failure under new geometry.

### Stage 4: the screen moves onto the new geometry — 7 September 2026

Everything except the list's columns. `boxes.json` now comes from the
built plate, the four lower panels, the sort row and RETURN are in
their new places, the inset is the 253x200 box with its dot table,
and the five column headings exist. The list still draws its OLD
single-track row inside the new `list_area`; putting it in the five
columns is Stop 3.

**THE BOX NAMES CHANGED, and that is the swap.** The superseded frame
cut 14 holes; the plate cuts 8. `output_panel` -> `planet_output`,
`spare_panel` -> `planet_info` (and it moved to the LEFT of the
band), `sidebar` -> `empire_stats` (out of the right-hand column and
into the band), the seven `sort_*` boxes -> one `sort_bar`, and a
`header` window appeared where the title hole was. Twelve of the
thirteen names went; every reader was re-pointed in this commit —
`screen.py`, `colony_list_preview.py` and `smoke_test.py`.

**`frame_holes.name_holes_colony_summary` was rewritten, not
adapted.** The old rule looked for a title, a right-hand column of
two and a bottom row of seven, and `_split_common` exists to find
exactly that — none of which the plate has. The new rule groups holes
into ROWS by vertical overlap and reads four: header, list, the
band's four panels, the sort row's two. Overlap rather than a y
tolerance, because the galaxy inset is 20 px shorter than its band
and centred in it, so a tolerance would be a number somebody has to
keep in step with the layout. It refuses the old frame with a message
rather than mis-naming it.

**`--write` kept 0, and the number is the point.** It reported
`kept 10` on the first run — `sidebar`, `output_panel`, `spare_panel`
and the seven `sort_*`. Those are not hand-placed content boxes,
which is what the keep rule is for (the galaxy map's `sb_*`
readouts); they are cutouts of artwork this screen no longer draws.
Preserving them would have left ten dead boxes that nothing renders
and every check still walks. They were deleted first, and the second
run kept 0. **This screen has no hand-placed box: every one of its
eight is a cutout, and decision 3's chain is unbroken.**

**FLAG-OFF SEMANTICS CHANGED, AND THE DEFAULT FLIPPED WITH THEM.**
`boxes.json` is generated from the plate's holes, so the plate IS
this screen's frame. `frame_preview` ships **on**, and its name is
backwards for one stage: turning it off draws the superseded artwork
over boxes it does not fit. That is not a cosmetic difference — the
class A checker, which asserts no glyph our code places lands under
opaque frame alpha, reports **5822 violating pixels at 1080p and
31654 at 2160p** with the flag off, because the old frame's metal
sits exactly where the new list is. The flag is kept for one stage so
the two can be compared side by side; **Stage 5 deletes the old
frame and the flag together**. **THE COLOURED CELL RENDERER IS NOT
ON THAT LIST** — see "Stage 5's deletion list, with one exclusion"
in the Stage 3 entry: it is what an install without
`tools/raceicon_extract.py` sees, so it is a state of the figures
feature and not superseded code. Both checkers now read the frame the
screen actually DREW rather than a path they assumed — that
assumption is what produced those numbers against artwork nobody
blitted.

**The title is gone, and that is a transcription.** The original's
colony summary has no title text: its five column plates start at the
very top (framebuffer, frame edge y 4..7, plate outlines y 11 and 32,
first row y 35). "COLONIES" was drawn here only because the
superseded frame cut a title hole; with the plate's header window in
that band the two overlapped and the title sat across the WORKERS
heading. `frame._no_title_note` records it.

**AND `FRAME_TITLE` DID NOT SURVIVE ANYTHING — 21 September 2026, work
order 156.** This paragraph said "`FRAME_TITLE` survives for the
framebuffer fallback, which is a different drawing", and
`frame._no_title_note` said it too. **There is no such reader.** The
only one in the tree is `ScreenBase._render_frame_title`, reached from
`_render_frame` behind `if self.USE_FRAME` — and `USE_FRAME` is False
on this screen — while the fallback path draws the dispatcher's own
name (`core/original_view.py:158`) and never a `FRAME_TITLE`. So the
attribute was dead, both documents were asserting a path no file
carries, and it went with `_render_title` in the same commit. The
shape is the one this project keeps paying for: two copies of a claim,
neither of them checked against the code.

**The header: five plates inside our own window, two DEVIATIONS.**

- **The window is ours.** The original has no header window — it
  draws five raised plates straight onto the frame's metal, each a
  recessed dark field with a light rounded outline. Measured on the
  live framebuffer: plate interior luminance **44**, surrounding
  metal **60**, outline **96**. We cut a window and draw the plates
  inside it, so **the window's own panel fill stands in for the
  original's plate recess** — one dark field behind five outlines
  instead of five dark fields on metal. Chosen over closing the hole
  because with the header window removed the ring-to-list gap grows
  to about 74 ref px and the Stage A3 rail pass fills it with a
  stretched rail; that is a change to the plate machinery plus a fill
  under every plate, and Stage 4 is not the place for it.
- **The outline colour is ours.** The original's line is a neutral
  grey at luminance 114-124; ours is `panel.thin_border`
  [55, 65, 85], luminance about 68 and blue — decision 34's own panel
  language. The value is in `colors.json`.

Both in `colonyheader.py`, in `layout.json` under
`header._deviation_window`, here, and in a smoke check.

**THE PLATE HEIGHT IS A FINDING AND IS NOT ABSORBED.** Measured, the
original's plate is native y 11..32 = 22 px = **66 reference px**.
The header window is **48** reference px of drawable height. The
transcribed plate is 37 % too tall to fit. The plates fill the window
instead and `colonyheader.PLATE_HEIGHT_REF` carries the number that
does not fit, with a check that fails if the window ever grows to
meet it — because that is the day the deviation ends and the note
recording it has to go.

**Growing the window to 66 was priced and REFUSED, and it misses by
three pixels.** Taking the 18 px from the list gives 605 -> 587, and
the row arithmetic is `colonytrack.row_bands`: rows of
`row_height` 58 starting at `pad_y` 14 inside the box, which is the
window plus `frame_holes.BLEED` on each side.

| header | list window | box | available | ten rows need | |
|---:|---:|---:|---:|---:|---|
| **48** | 605 | 609 | 609 − 14 = **595** | 580 | fits, 15 px spare |
| 66 | 587 | 591 | 591 − 14 = **577** | 580 | **short by 3** |

**And it would cost the row unevenly**, which is worse than costing
it: 9 rows at 1920x1080, **10** at 2560x1440, 9 at 3840x2160, because
`int(58 * 4/3)` and `int(14 * 4/3)` leave a different remainder. A
visible row count that changes with the window is the shape of fault
this project files under decision 5 — one number, two answers — and
ten is the game's own window (colsum.cpp:348-351), which `_first` is
established against under decision 46.

So **48 stays and the marking stays as built.** Closing it needs a
row pitch or a `pad_y` that was chosen for it, which is a layout
decision and not this stage's.

**The plate GAP is transcribed and was invented before.** The
original's plates share their divider: two pixels at luminance 85 and
93 between two interiors of 44, so the gap is **0** and the divider is
6 reference px. An earlier draft used a 9 px gap that came from
nowhere.

**The three job columns are unequal, and the source says so.**
`COLSUM::Get_Selected_Pop_` (colsum.cpp:1006-1024) passes the column
bounds as literals — `left_x` 101/236/378, `right_x` that minus 10 —
giving spans **135 / 142 / 134** native px with the WORKERS column
the widest. Second source: the separators measured on the live
framebuffer at x 99/234/376/510, which agree to +1 px on all three.
Over the unchanged 1041 px reservation that is **342 / 360 / 339**,
so name, building and scroll do not move and the list is still 1693
wide. They were three equal 347s, which was ours. The capacity
assertion is re-run at the NARROWEST column now, not at the old
uniform one — the check is what allows the change, not the
arithmetic.

**The sort row is one bar divided by one function.** The plate cuts
one `sort_bar` hole where the old frame cut seven buttons, which is
what the original has: a recessed strip with seven words laid along
it and the ACTIVE one lit **at its own label width** — "Name" lights
a short box, "Producing" a long one. `colonysort.layout` returns both
the HIT rect and the HIGHLIGHT rect per key, so the renderer and
`handle_click` cannot disagree (decision 5); a check asserts the
seven tile the bar with no gap and that every highlight sits inside
its own hit area. The even gap between words is **derived, not
transcribed** — the source carries no table of positions, only the
seven `native_click` points, which stay the authority for what gets
injected and are still asserted to fall inside their buttons.

**The class B floor moved from 20 to 17**, with the reason beside it:
the galaxy map's ten straight-edged holes plus the plate's eight less
the title it does not have. A floor, so a frame that stops cutting
holes cannot pass by measuring nothing.

**The inset's dot centre is shown on an image, not only asserted.**
`~/Bilder/rahmen/stage4_inset_dot_centre_536bba387c82.png` renders a
dot at 5 / 7 / 11 px against the derived targets 5.93 / 7.91 / 11.86
and marks the computed pixel: the ink centre IS that pixel at all
three resolutions, which is the property an even dot could not have.

**`screens/colony_summary/screen.py` stayed under 300** — it went to
337 and came back to under 300 by moving the sort bar's rendering and
geometry into `colonysort.py` and the header's into
`colonyheader.py`. Decision 6 says split rather than extend the list,
and the list is still eight entries.

**OPEN LAYOUT ITEM — `planet_info` is empty and that is not a
decision yet.** The original splits its lower-left content across
TWO panels: the scan text (`Huge Terran / Heavy Gravity / Mineral
Ultra Rich / Population (13/22) / +103k`, colsum.cpp:1196-1205 into
`E_Strings_(74)`, native 13,354,80,88) and the production icon
column beside it (`Draw_Colony_Wee_Prod_(..., 106, y_pos, 366, 20)`,
colsum.cpp:1171-1176). **Ours puts both in `planet_output` and leaves
`planet_info` fill-only.** That is where Stage 1's rectangles landed,
not a reading of the original, and nothing has decided whether the
band should follow the original's split, keep ours, or use
`planet_info` for something else. **Not to be assumed by whoever
draws into that band next**: Data decides before Stage 3.

94 -> 95 checks.

### Stage B: the preview switch, and Stage C: the plates are derived — 7 September 2026

**One flag, one place, no second code path.** `frame_preview` in
`settings.json` (default **false**, stated there and in
`core.config.load_settings`'s fallback so a clone with no settings
file and a clone with one agree about what "not configured" means).
`screens/colony_summary/colonyframe.py` turns it into a path;
`screen._load_frame` loads that path, `_scale_frame` scales it and
`_render_frame_image` blits it, exactly as before. **The switch
selects a source, not a code path** — the built plate and the shipped
artwork are both one RGBA image stretched over the reference area, so
nothing downstream learns which it got. If it ever needs a second
drawing routine, the switch is the wrong shape and the plate is not
a frame; that sentence is in the module.

Its own module rather than eleven more lines in `screen.py`: that
file was 316 code lines and would have been 329, and decision 6 says
split rather than extend the exceptions list. It is 299 now, and the
list is still eight entries.

**Nothing about the flag touches `boxes.json`.** It is runtime state,
`Box.to_dict` serializes a fixed key set and would drop it the first
time F5 saved (decision 37), and a render toggle is not layout in any
case.

**Which plate: `core.box.closest_resolution`,** which is decision 1's
exact-then-closest-by-area chain called in its one home. It was
`_find_best_fallback`, private, one caller; it is public now with the
second caller named in its docstring. Not copied — a screen choosing
an image and a screen choosing a box list ask one question, and two
answers drift the day somebody changes "closest by area" to "closest
by width" in one of them. Resolutions come from
`layout_reference.json`'s `_resolutions`, the file `frame_build.py`
and `frame_mask.py` already read.

**Flag off is the tree as it was, asserted and not eyeballed.** Two
halves, both needed: the flag-off path resolves to
`screens/colony_summary/assets/frame.png` (committed, sha256
`6656ac0e34869c48`), and the surface that reaches the screen hashes
identically to that file loaded and scaled the way `_scale_frame`
scales it. Verified to fail: with the flag's gate removed the check
reports *"flag off must draw …/assets/frame.png, got
…/assets/frames/frame_1920x1080.png"*.

**Flag on names the build.** One line at screen load, from
`colony_summary.frame`, silent when off:

    INFO colony_summary.frame: PREVIEW: built plate
    screens/colony_summary/assets/frames/frame_1920x1080.png
    (1920x1080 for a 1920x1080 window), sha256 33f1531d10fc1f4a

The hash is in the line so a screenshot can be matched to the build
that made it, and the check refuses a line without it. At 1280x720
the same line reads `(1920x1080 for a 1280x720 window)` — the
closest-by-area plate, scaled, which is what the shipped 1672x941
frame already does at every size.

**Stage C: derived, decision 49**, with committing them recorded as
the rejected option and permanent history growth as the reason. Both
conditions are in: `frame_build.py` is a step in `tools/setup.py`,
and the check **reports absence rather than skipping** — with
`frames/` moved away the suite still passes at the same count and
the line reads *"plates absent (3 of 3): run `python
tools/frame_build.py`"*. Verified to fail on a changed plate: one
red pixel gives *"the plate on disk is not what frame_build.py
produces … 664456 bytes on disk, 664448 rebuilt"*.

**Two stale claims fixed, and the second is the finding.** The
`.gitignore` entry still called `frames/` "tools/frame_cut.py's
output" whose artwork "lives outside the tree" — both true when
written, neither true since `frame_build.py` replaced the hand-made
plate with a nine-slice of a committed master. And `setup.py` had no
frame step at all, so **the tree had a file gitignored as generated
with nothing that generated it**: decision 40's word without decision
40's licence, for as long as the plates have existed. An ignore rule
is a claim about a file, and this one had gone stale where nothing
reads it.

**The header is an INTERIM and is named as one.** The preview draws
`header` as `[107, 18, 1693, 48]` — full width, flush to the ring on
three sides, which is why it reads as a light line: three of its four
bevels are laid over the ring's innermost 3 px. **That is not the
intended header and must not be mistaken for it.** The master's own
header opening is a 546 px chamfered cartouche at top centre, and the
ORIGINAL colony summary has no header window at all — its top band is
five raised column plates (NAME, FARMERS, WORKERS, SCIENTISTS,
BUILDING) with their own rounded bevels, plus the scroll arrow;
measured live against the reference save, picture in
`~/Bilder/rahmen/`. Deferred to Stage 4 Stop 1, where the list
columns and the sort row are laid out, with two questions attached:
whether the column reservation (302 + 347x3 + 314 + 36) maps onto
five plates plus the scroll arrow, and whether the master carries a
raised-plate element with a rounded bevel or one has to come from
elsewhere.

**And what the flag-on picture is NOT.** `boxes.json` still comes
from the OLD frame's holes, so the sidebar readouts, the lower band
and the sort row sit where the old artwork's holes were rather than
where the plate's windows are. Stage 4 moves the content; this is a
frame preview and nothing else.

**`--profiles` stopped claiming a hole has no lit edge when it has
one.** The tool printed *"(a side with no lit edge)"* for the header
cartouche, whose every side carries a one-pixel lip of 147..222
against metal at 2. The reading walks outward from the BOUNDING BOX,
which for a chamfered hole is not the hole's edge — the bbox starts
at y=21 and the lip sits at y=21..22, so the band above it is three
rows of plain metal. Labelled as bounding-box-based, with a fill
column beside it (91.4 % for that hole against 94.4-99.9 % for the
eight rectangular ones) and an annotation that now says the reading
cannot see the edge rather than that the edge is absent.
`bevel_source` gained the rectangularity gate it always needed —
it CROPS A RECTANGLE, so a chamfered source would print slanted
corners onto every window — and the plates rebuild byte-identical,
so the gate changed no pixel.

**The first diagnosis of that was wrong and the correction is the
part worth keeping.** It was reported at Stop 1 as "the chamfered
corners put hole pixels into the metal band and flatten the average".
Masking every hole pixel out of the band changes **not one of the
forty numbers** the tool prints: the bands lie outside the box and
contain none. Plausible, mechanical, false — and the cheapest test
was to apply the fix it implied and see whether anything moved. In
the fundament under Evidence, as its own line rather than under "a
measurement not stable under its own threshold": there the parameter
was too permissive and sweeping it exposed the fault, here the
parameter is fine and no sweep can find it.

**Carried over from the galaxy-scale commit**: the `max_map_scale`
check now also asserts that no key of `STOCK_MAX_MAP_SCALE` is a
whole number of `MAXIMUM_GALAXY_CELL`s. The two arms of the mapgen
switch are told apart by MAP_MAX_X alone, so an overlap would route
a Maximum galaxy of that width to the literal arm. Added to the
existing check; the count did not move for it.

**`FakeApp` gained `settings`**, and so did `colony_list_preview`'s
`_App`. `main.py:25` sets it and screens read it, so a fake without
it meant no screen could be tested through a settings-driven branch
at all — the same shape as the fake game states that were missing
MAP_MAX_Y, one commit earlier.

93 -> 94 checks. `tools/colony_list_preview.py` 344 -> 345 code
lines, already on the exceptions list and re-measured there.

### `Maximum_Galaxy_Display_Scale_` is transcribed; the 50.6 estimate is retired — 7 September 2026

Reported as a finding the same day and **fixed here**, as its own
commit, ahead of Stage B/C and Stage 4. The reason it goes first is
Stage 4: it brings the 253x200 inset with the dot table onto a live
screen, and the first side-by-side comparison of that inset would
have attributed the offset to the dot table.

**What it was.** `zoomtables.max_map_scale(map_max_x)` recovered
`MOX::_max_map_scale` as `round(map_max_x / 50.6)`, because the
Extension API serializes `MAP_MAX_X` and not the scale. 50.6 is the
four stock sizes' ratio and only theirs (506/10, 759/15, 1012/20,
1518/30). **Two defects in one line**, and each is now held red by
its own assertion: the original takes a CEILING, not a rounding, and
it takes the larger of TWO of them — the second over `MAP_MAX_Y`,
which the estimate never read although it is on the wire beside x
(`ext_api.cpp:113-114`).

**What it is.** `MAPGEN::Maximum_Galaxy_Display_Scale_`
(mapgen.cpp:64-71), transcribed into `core/zoomtables.py` per
decision 26:

    max(ceil(MAP_MAX_X * 10 / 506), ceil(MAP_MAX_Y * 10 / 400))

per axis, the smallest scale at which the galaxy fits the map
rectangle, then the larger — an axis that does not fit is an axis the
player cannot see. **The extent is read, not rebuilt.** The
function's own `map_width`/`map_height` are character for character
what the same branch assigns to `_MAP_MAX_X`/`_MAP_MAX_Y` ten lines
later (mapgen.cpp:1113-1115), so no star count and no grid enter the
transcription at all. `max_map_scale` transcribes the whole switch:
the four stock sizes' literals by exact MAP_MAX_X
(`STOCK_MAX_MAP_SCALE`), the function for GALAXY_SIZE_MAXIMUM — the
two answers mapgen itself gives, in mapgen's order. An extent no
galaxy size produces returns 0, which callers already read as
"unknown".

**MAP_MAX_Y has no default, and the fallback that gave it one is
gone.** The first cut of this shipped `max_map_scale(x, y=0)` plus a
`maximum_galaxy_map_max_y` that inverted the Maximum galaxy's grid to
recover y from x. Data asked which caller it served. **None** — all
seven pass both extents, and the only single-argument calls in the
tree were the two assertions in the smoke test that existed to
exercise the fallback. A fallback justified by a test written for it
is a fallback with no caller, and a `y=0` default hands the next
caller who forgets y exactly the defect this commit retires, at one
galaxy size, silently. Both removed: y is a required positional, and
a missing one is a TypeError where it is written.

The question also answered itself for the stock sizes: 506 is not a
multiple of the 150-unit cell, so an inversion could never have
served them — their extents are literals in the switch, not grid
products. The stock branch keys on MAP_MAX_X alone because each of
506/759/1012/1518 names one arm of that switch, which assigns the
scale without consulting either extent.

**A TypeError only fires on the path that runs, and the paths where
the y ceiling wins are exactly the ones no fixture reaches**, so the
check is static: it walks all 119 python files with `ast` and refuses
any call to `max_map_scale` or `max_zoom_count` with fewer than two
arguments (`f(*pair)` allowed, since ast cannot count through it).
Verified to fail by dropping y in `tools/ship_icon_check.py`, which
needs a live game and which the suite therefore never executes —
`['tools/ship_icon_check.py:106 max_map_scale()']`. The same
regression in `viewctl` was caught by the interpreter instead, which
is the distinction the check exists for.

**The fundament's caveat is withdrawn, not weakened.** It said the
community Maximum size was never part of the derivation. It is now
covered — and so are the other four, by the same expression: the
formula reproduces 10, 15, 20 and 30 from the stock extents, which is
asserted rather than remarked.

**Two independent sources, as the rule requires.**

1. `MAPGEN::Maximum_Galaxy_Display_Scale_` itself.
2. **A live probe, and it is the one that could tell the two
   readings apart.** The reference save could not: 99 stars gives
   MAP_MAX 1800 x 1350 and both readings say 36. So a Maximum galaxy
   was generated at a count where they differ — `map
   maximum_star_count = 155;` in a cfg, New Game -> Maximum, driven
   through race, ruler, banner and home system — giving 155 stars,
   MAP_MAX **2250 x 1800**. Parked with field 9 only, throttled
   (decision 35; field 8 is the rubber-band trap and was never sent),
   the game held at **45**. `tools/zoom_check.py`, still running the
   estimate, printed

        MAP_MAX_X     : 2250
        max_map_scale : 44  (derived)
        widest scale seen: 45
        MEASURED 45 > DERIVED 44: the recovery is WRONG for this
        galaxy size. Star names would switch off at scale 44 instead
        of 45.

   That tool was written for exactly this question and had never had
   a galaxy that could answer it. Its docstring now records the run.

   **Nothing was written to disk to get it.** The game ran with its
   CWD in a scratch directory — every LBX symlinked, the small
   mutable files copied, one real `orion2re.cfg` — because
   `main.cpp:123-139` roots the VFS at the working directory. The
   orion2re tree is unmodified and so is `~/Master of Orion 2`; no
   savegame was written at any point.

**And the probe left no state behind**, which was checked rather
than assumed: the cfg was removed, the game restarted (`configuration:
orion2re.cfg not found; using defaults`), the reference fixture copied
into the scratch directory as a save slot and loaded — stardate
3502.4, 99 stars, MAP_MAX 1800 x 1350 — and `zoom_check.py` reported
**MEASURED == DERIVED** at 36 again. `fixture_reference_3502.4.GAM`
still hashes `ab70cc9ad5442335`.

**The range, reproduced after implementation.** Over 73…1023: **688
of 951** star counts differ from the retired estimate, at **15**
distinct map widths, and the transcription is **never below** it —
the estimate rounds down from a ceiling, so it can only ever be one
short. The x ceiling is the larger at 11 of the 15 widths and the y
ceiling at 4 (4350, 4500, 5100, 5250), which is the half of the
defect a MAP_MAX_X-only reading could not have caught even after it
stopped rounding.

**The check goes red on each defect separately**, verified by
reinstating each and running the suite. Both assertions name the
defect they catch rather than failing bare:

| regression | first assertion to fail |
|---|---|
| commercial rounding back | `assert zt.max_map_scale(2250, 1800) == 45` — *"live probe 2026-09-07, 155 stars"* |
| ceilings on x only | `assert zt.max_map_scale(5250, 4200) == 105` — *"THE Y TERM HAS BEEN DROPPED… 105 against x's 104"* |
| a caller drops MAP_MAX_Y | the call-site walk — *"these call MAP_MAX recovery with one argument"* |

Both reverted; `zoomtables.py` is byte-identical to before the
regressions.

**The check's reference is written out in the test, not imported.**
It walks the other way round — star count -> grid -> extent -> scale,
where zoomtables starts from the extent — and spells the ceiling
`-(-a//b)` against the transcription's `(a + b - 1) // b`, so one
mistyped idiom cannot satisfy both. Four fixed points beside the
range: the stock literals, the probed 155-star value with its source
line, the reference save's 36 (marked as the value that AGREES, which
is why it settles nothing), and the y-dominant 5250 x 4200.

**Same numbers on the reference save, which is the expected result.**
`galaxy_inset_stars` returns 99 dots whose digest is unchanged
(`29d31e5bf2441027`), x range 5..122 and y range 4..81 as before;
`viewctl._fit_scale` is 36.0 as before; the rungs are still
5/9/18/36. **The parked zoom-out step count does not change** — 0
from the game's own 36, and 3/2/1/0 from the four rungs — so decision
35's corollary is untouched here. The only line that differs between
the before and after runs is the one echoing the arguments.

**Two things the inventory turned up, both worth more than the fix.**

- **`smoke_test.py` carried a galaxy that cannot exist.** The
  extended-ladder check used `map_max_x = 2277` with the comment
  "max scale 45" — a width reverse-engineered out of the estimate to
  make it answer 45, and not a multiple of the 150-unit cell, so no
  Maximum galaxy has it. It is now 2250 x 1800, which is the galaxy
  the probe actually ran on. **A fixture that could only exist while
  the thing it tested was wrong.**
- **Every fake game state in the tree was missing MAP_MAX_Y.**
  `gs.map_max_y` was set once, to 600, and eleven later sites
  reassigned `map_max_x` alone — so a medium galaxy's height sat
  under a huge galaxy's width for the rest of the run, and the y
  ceiling could never have been exercised. `_FakeGS` in the inset
  check had no `map_max_y` attribute at all. All twelve carry both
  extents now, in real pairs. **A fake that omits a field the real
  snapshot carries is how a term goes untested.**

**505x399 and 506x400 are one rectangle, not two constants** —
checked because the ceilings divide by 506 and 400 while the
fundament said the viewport is 505x399.
`MAINSCR::Draw_Influence_Overlay_` declares it under those names
(mainscr.cpp:161-164, `map_left = 22, map_top = 22, map_width = 506,
map_height = 400`), and the galaxy map's field 23 arrives on the wire
as (22, 22)-(527, 421) — the same 506 x 400 counted inclusively.
`Star_On_Screen_` then admits the near edge (`x > 0x15` passes at 22)
and excludes the far one (`x < 0x20f` stops at 526), so a STAR
reaches 505 columns and 399 rows inside it. Inclusive against
exclusive. The scale has to cover the rectangle, so the rectangle is
what the ceilings divide by; the fundament bullet now says which is
which.

**50.6 survives in one place and means something else there.**
`506/10` is the map viewport's reach per scale unit
(movebox.cpp:19-20), which is what the inset's 506000 and 400000
divide by. `colonyrows.py` used to source that number to
`zoomtables.MAP_MAX_X_PER_SCALE` — the estimate's constant — which
made one number carry two meanings in one tree. Both sites now cite
movebox.cpp and say which meaning is theirs.

**Consumers re-pointed**, all seven, and a grep proves the identifier
is gone: `MapContext.__init__` and `GalaxyMapScreen._icon_anchor`
(galaxy_map), `ViewControl._fit_scale` (the HD zoom-out limit and
parking target), `colonyrows.galaxy_inset_stars`, `zoom_check.row`,
`ship_icon_check.main`, and the smoke test. `max_zoom_count` takes
both extents too; its answer never changes (mapgen sets 3 for
Maximum, which is what the non-stock branch already returned).

92 -> 93 checks. `galaxy_map/screen.py` 529 -> 531 code lines and
`galaxy_map/renderer.py` 333 -> 335, both already on the exceptions
list and both re-measured there.

### The colony rebuild, Stage 1: layout as data — 6 September 2026

`screens/colony_summary/layout_reference.json` is the **one place**
the rebuilt screen's rectangles are typed, and `tools/frame_mask.py`
renders them into one window mask per supported resolution. The frame
artwork is drawn from the 1080p mask, `frame_holes.py` will derive
the cutouts back out of the artwork, and `boxes.json` is asserted
against both — decision 3's chain, with a committed JSON at the top
of it and everything below generated (decision 40; the masks are in
`.gitignore`).

**The arithmetic holds.** 300 + 394x3 + 314 + 36 = 1832, which is the
list's own width exactly — the columns ARE the list, with no slack to
distribute, unlike the single-track row where six floor divisions
dropped pixels that had to be given to the name column. Every window
sits inside the 36 px bezel, asserted as the rule rather than as a
list of coordinates. And the mask rounds with `Layout.rect`'s own
truncation rather than a second rounding rule, checked at all three
resolutions — that is the class of one-pixel disagreement decision 3
exists to make impossible.

**The inset box is confirmed and the crop is the coverage.** 253 x
200 against the original's coverage aspect of 1.2651 — which is the
same at every galaxy size, because both divisors in
`Draw_Galaxy_Map_Box_` are constants and `_max_map_scale` cancels. So
the crop fills the box with **no letterbox at any size, Maximum
included**; the earlier expectation that Maximum letterboxes is
WITHDRAWN and only held if the crop were the galaxy rather than the
original's reach. At 3840x2160 the box is 506 x 400 device px, the
small galaxy's own world extent at 1:1.

**Two markings, three homes each.**

- **HD EXTENSION — the inset's scale is fixed and off the rung
  ladder.** As a `map_scale` it sits at `2M`: 20, 30, 40, 60, 72, and
  three of the five are not values `zoomtables.scale_rungs` can stand
  on. The reason is *not* "between rungs" — the inset does not zoom
  at all, so it never stands on one, and the two sizes that land on a
  rung do so by arithmetic coincidence. Milder than `hd_zoom_level`,
  which interpolates a ladder the original does stand on. In
  `colonyinset.py`, `layout.json`'s `inset._geometry_note`, here, and
  a check.
- **DEVIATION — isotropic where the original is not.** The original
  compresses y by a constant 3953/4395 = 0.89943, so an isotropic HD
  inset is not the original's picture scaled but its COVERAGE
  re-projected without the squash: every constellation is **11.2 %
  taller relative to its width**. Chosen because a galaxy is a shape,
  the same argument that already refuses stretching the map to fill
  the hole. Same four homes.

**And the 286 px reading is gone.** `inset._geometry_note` recorded
it — the original's own 128 x 91 picture scaled uniformly, which
keeps the squash — against the isotropic reading's 257 px of content
in the same box. An 11 % difference from the same data, and the tree
may hold one of the two. The numbers live in
`doc/colony_inset_geometry.md` 3.5 and are deliberately not repeated
in the note; the check that used to hold the note to `451`,
`128 x 91` and `LETTERBOXED` now holds it to the decided reading and
fails if `286` comes back.

**The star dot is odd, and the requirement picks it.** The acceptance
is that the computed star pixel is the CENTRE of the drawn dot at all
three resolutions — and an even dot has no centre pixel, so the
position could only be placed half a pixel off and the property would
stop being checkable. `zoomtables.INSET_DOT_DIM` is **5 / 7 / 11**,
the nearest odd number to the derived 5.93 / 7.91 / 11.86, as a
DERIVED table with `INSET_DOT_TARGET` beside it in the form
`NEBULA_DIM` uses. The cost, stated: the dot does not scale with the
layout (1.0 / 1.4 / 2.2 against 1.0 / 1.333 / 2.0) and runs up to
10 % large at 2160p — less than the half pixel it buys. The check
**renders** a dot at each size and reads its ink back, so the
centring is asserted on the picture.

**`zoomtables.FIGURE_STEP` is 2 / 3 / 4**, also an HD EXTENSION: a
figure is 28 px native, and the proportional answer is fractional
from either end — 2.667 against the layout scales, or 2.25 and 4.5
against the original's own 640 x 480 — and in one axis only, which
would make the figure anisotropic as well. Integer steps put the
deviation in the SIZE instead of in the pixels: 56 / 84 / 112 against
the proportional 63 / 84 / 126, exact at 1440p and 11 % small at the
other two.

**A new check, and it caught something on its first run.** The
fundament asks a marking to live in its module, in this document and
in a check. The third home is the one that rots: a check greps a
FILE, and a marking that moves to a file no check reads goes on being
true and stops being watched. The marker inventory now walks the tree
for `HD EXTENSION` and `DEVIATION`, and fails if a file carries one
and is not declared — or is declared and no longer carries one. On
its first run it failed on `layout_reference.json`, whose figure-step
marking had gone in minutes earlier with nothing reading the file.

**Three of `doc/pop_stacking.md`'s seven open questions are closed**,
by Data at this stop: HD reproduces the original's overlap with the
squish formula transcribed and multiplied by the integer figure step,
so no replacement formula arises; the extra HD width goes into the
building column's reservation and never into wider figure spacing
(any wider spacing later is a marked HD EXTENSION, not the default);
and the drop target and popup anchor move to the FIGURE SLOT under
one geometry function, while **the identity letter is dropped** —
the original's own sprite carries identity, which is exactly what the
single-track row could not do and what the letter was invented for.

86 -> 89 checks.

### The population figures come out of RACEICON.LBX — 6 September 2026

`tools/raceicon_extract.py` writes the original's own pop sprites to
`screens/colony_summary/assets/raceicon_ref/`, per race and per
profession. **Nothing in the tree reads it**, it is in `.gitignore`,
and the smoke test passes with it absent — decision 38's rule, the
same one the help texts and `nebula_ref/` live under.

**The container moved into `core/lbx.py` first.** RACEICON was the
third reader of the LBX format and the second of the sprite decoders,
and two private copies is one too many. Proof of the refactor was
byte-for-byte: `nebula_ref/` regenerated with 0 bytes changed across
all 61 files, `help_en.json` identical.

**The block is thirteen entries per race, and all four functions were
needed to account for it.** `race * 13 + job * 2 (+1)` is only the
first six:

| offset | what | source |
|---|---|---|
| 0,1 · 2,3 · 4,5 | farmer / worker / scientist, `pop_state` 0 and 2 | `People_Anim_`, colony_main.cpp:444-450 |
| 6…10 | five military variants | `Military_Anims_`, colony.cpp:1298 |
| 11 | spy | `Spy_Anim_`, colony.cpp:237 |
| 12 | race portrait, drawn for a CONQUERED pop | `Colony_Pop_Icon_`, colony.cpp:1285 |

13 races (`enum STOCK_RACE`, orion2_consts.h:444-457, with a
`static_assert` on the count at :1379) x 13, plus 0xA9 android and
0xAA native, is 171 — exactly what the file holds. Names come from
that enum and NOT from `MOX::_race_names[]` (estrings.cpp:108-127),
which holds localised display strings and is a different thing from
the identity of race index 3.

**The resting figure is the ODD entry of each pair, and the even one
is dead code.** `Pop_To_Pop_State_` (colony.cpp:1240-1255) returns
only 2, 3 or 4, and no call site in the tree passes 0. The even
entries are extracted anyway as `_state0`, because a reference that
silently omits half the file cannot be used to check the half it
kept. Recorded for the maintainer in `doc/orion2re_open_fixes.md` as
an OBSERVATION beside the `pop_state == 6` item — same pattern,
second site, no fix wanted.

**The palette is not in RACEICON.LBX** — all 171 entries have
`flags == 0`, so `FLAG_HAS_PALETTE` is set on none. Grayscale by
index is the default output; a coloured set carries the `_game`
suffix, and the suffix is that and not `_colsum` because both colony
screens were compared:

- the SUMMARY screen loads `fonts::Load_Palette_(1, 0, 255)` and then
  COLSUM.LBX entry 0, which defines all 256 indices (colsum.cpp:128-129);
- the MAIN screen loads the same font palette and then `C_Anims_(0)`
  (`Update_Colony_Palette_`, colony.cpp:230-235), which resolves to
  PLANETS.LBX and is therefore a different sprite per climate
  (colony_main.cpp:474, colony.cpp:201).

Whole palettes they are not — over their common range the 30
PLANETS.LBX entries differ from COLSUM entry 0 in 78 to 80 of 80
indices, none identical. But every planet entry declares
`(start 0, count 80)` and **the people sprites use indices 81..239**,
not one of which a planet background can touch. Those come from the
font palette, FONTS.LBX entry 2 (fonts.cpp:72-77), on both screens,
and COLSUM entry 0 agrees with it on **all 76** indices these sprites
use (228 of 256 overall). The colours are the base palette's, not one
screen's private choice.

**A defect fell out of asking that question.** `read_palette` read
`r, g, b, changed`; `s_palette_entry` is `{changed, r, g, b}` —
**the flag first** (orion2.h:2131-2136). Every colour it returned was
one byte to the left, and COLSUM entry 0's white came back as cyan.
It had shipped in `nebula_extract.py` since that tool was written and
was inherited verbatim by `core/lbx.py`, and it was invisible because
**not one of STARBG.LBX's 48 nebula entries carries a palette at
all** — the function had never once run on real data. Correcting it
changes no file in the tree, which is luck; the check now pins the
byte ORDER against the struct, with a non-zero flag byte in the
fixture so a wrong order cannot pass.

**Acceptance, and it is stronger than the question asked.** The
question was whether Elerian's bronze farmer, teal worker and silver
scientist match the original. The native colony summary frame is
palette-INDEXED, so the comparison could be made on indices and never
on colours: entries 40, 42 and 44 match **14, 4 and 8** figures in
that frame index for index, and **every other race matches none** —
which identifies the save's race as Elerian by measurement rather
than by assumption. Entries 39, 41 and 43 match nothing, confirming
the odd-entry rule live. Entry 0xAA matches 3, which is Urna I's
three natives from the day before, and 0xA9 matches 0, which is a
save with no androids. Rendered through the `_game` palette the three
sprites are **pixel-for-pixel identical** to the original's frame:
285, 256 and 239 opaque pixels each, 0 different. That is also what
proves the palette byte-order fix, since the old reading would have
matched nothing.

### One named file per RACEICON entry — 6 September 2026

`raceicon_extract.py` gained two outputs. `figures/` holds **every
entry once**, named by the verified block layout —
`e040_race03_elerian_farmer_game.png` — in the game palette,
**uncropped**, at 1x. `_labelled_sheet.png` is the layout as a
picture: one row per race, the 13 block offsets across, entry number
and role under each figure, 4x nearest-neighbour, android and native
as a last row.

**Uncropped is the point, not an omission.** The canvas is the
animation header's own, so every figure of a race shares one origin
and the baseline sits where the original puts it. Cropping to the ink
would destroy exactly that — so the opaque bounding box is REPORTED
in `summary.txt` beside each file and never applied.

**`figures/` and the per-race directories overlap on purpose.** The
directories answer "what does a Sakkra scientist look like" and hold
six files; `figures/` answers "what IS entry 47", which is the
question the 13-entry block raises and which neither the raw dump
(numbered and nothing else) nor the directories (the six people
entries only) can answer.

**`_contact_sheet.png` stays what it was, and that is deliberate.**
It is the raw file in file order with nothing but a number, and it is
what the block layout was CHECKED against; checking the layout
against a picture that already applies it would be circular. Verified
byte-for-byte: of the 504 files this package found, **only
`summary.txt` changed** and none was lost.

**The military variants are numbered 1..5 in file names, not 0..4.**
`Military_Anims_(variant, race)` (colony.cpp:1298) is reached through
`Military_Anim_` (colony.cpp:1309-1330), which picks variant 0 for
militia, 1 or 2 for troops depending on Powered Armor and 3 or 4 for
the second class depending on Battleoids. A file called `military_0`
would read as "the first one" where the source's 0 is a specific
thing; 1..5 counts files, which is what a file name can honestly do.

**Two things the size pressure produced, both improvements.** The
tool crossed 300 code lines, so the two sheets — which had become two
copies of the same "lay sprites in a grid and label them" — collapsed
into one `sprite_grid`, and `palette_note` shed a 25-line comparison
that already lives in this document, because a second copy of a
finding is what goes stale. It is at **297** now.

**And a defect the merge exposed.** `summary.txt` named
`<stem>.png` for every entry, including the 171 in `figures/`, where
only `<stem>_game.png` is written — so the summary pointed at 171
files that do not exist. It names the file it wrote now, and a check
of the run confirms all 251 named files are present. A summary is a
claim about the directory.

### Two live faults after the row's three groups — 6 September 2026

Both were seen in the running game against the pushed build and
neither was seen by any check, which is the more useful half of both.

**The held selection was outlined on the wrong cell. The DRAWING was
wrong; the hit test was right.** `colonylist.draw_pick` computed
`track_x + slot * step` for itself, and `slot` is an index inside ONE
job's icon column (`Pick.slots()`, from the original's per-column
walk at coldraw.cpp:352) — not a position in the track. So the
outline sat one marker plus every preceding job's cells to the left
of the cell it named. Reported on Horus IV as "exactly one cell",
which is what food alone shows: measured on a nine-pop row, food was
one cell off, industry six and research ten. **It was wrong for
industry and research from the day it was written (343d9ba) and the
markers only made food visible too.** Nothing else was affected — the
pick, the plan, the injected click and the pops that moved were all
correct throughout, which is exactly why nobody saw it for three
days. `draw_pick` now takes the row and the job and asks
`colonytrack.row_boxes`, like everything else that draws or hits.

**`tools/colony_move_hd.py` carried the same arithmetic**, in the
`square_xy` of the run built to accept this screen. It now asks
`row_boxes` too, and it reads the outline back off the rendered frame
before it will proceed. Decision 5 covers `tools/`.

**Why check 6 did not catch it, since it was built for this class.**
It inks `draw_drop_bands` and only its two outermost columns, so it
can say nothing about any cell in between and nothing at all about
the pick-up path; `draw_pick` had never been rendered by any check.
The replacement asserts the RULE the old one only gestured at: **the
cell under a pixel is the cell drawn at that pixel** — the cells are
recovered from their own ink, and `cell_at_x`, `drop_band` and the
pick outline are all asserted against that, for every cell of every
fixture row. It was run against the build's own arithmetic first and
failed with `Draconis V: the pick outline for cell 0 of job 0 inks
[(362, 379)], the cell is at [(382, 399)]`. A check that has never
been seen to fail is a check nobody has tested.

**The minimap was never black.** `galaxy_inset_fill` is inside the
`panels` block of `layout.json`; `_render_panels` read
`self._data[name + "_fill"]`, the top level, missed, and used
`PANEL_BG`. Sampled on a rendered frame it was (8, 11, 20) in 9592 of
10268 samples. The lookup now reads the block the value lives in, and
the live HD frame samples **(0, 0, 0) in 91.4 % of the box**, the
rest stars and the label. The measurement that chose the value was
always right; a measurement justifies a value and never a result.
Marked in the fundament under "the background you see is not always
the background that is set".

**Live acceptance, `tools/colony_move_hd.py --commit`.** Draconis
III, cell 8 of column 2 (research) to column 0: the outline inked at
x 582 and the cell is drawn at x 582 — the old arithmetic would have
put it at 522, three cells left. Two injected clicks on the wire,
`1 moved`, exactly colony 2's bytes changed, every pop word matching
the prediction.

**Two things reported as planned last round, answered.**

- **The cell-per-icon change WAS built**, in 8ac321c, and it is a
  behaviour change rather than a refactor: `row_regions` counts
  `row["cells"]` — one entry per drawn ICON, from
  `colonyicons.icon_pops` — where it used to count `row["jobs"]`, one
  per POP. The two differ by exactly the pops of a held cluster,
  whose `0x200` is clear and which the original does not draw either
  (coldraw.cpp:336). **So a held cluster now leaves the HD row while
  it is in hand, as it leaves the original's column.** Ours is only
  visible in a state the game reaches on its own — our own pick
  injects nothing — but the row is honest whenever it arrives there.
- **The marker fill is ONE colour value.** `MARKER_BG` (86, 92, 104),
  filled with a 3-tuple onto an opaque surface, so nothing blends.
  Sampled inside every marker of a four-pop row and a fourteen-pop
  row: (86, 92, 104) in all six. The lighter reading in one strip of
  the acceptance picture is contrast against its neighbours — a
  marker between long green runs against one hemmed by amber and
  blue — and not a second value.

### The row gets its three groups, a mark and a popup — 6 September 2026

Three decisions built, each narrowing the next, and all three are HD
EXTENSIONS with their markings.

- **HD EXTENSION — three job markers, always. REMOVED 8 September
  2026, marking and all.** Every row carried a marker per job in ECON
  order, each introducing its own cells: `F [food] W [worker]
  S [scientist]`, flush, no gap inside the run. The argument was that
  the original does not need them because it draws three FIXED
  columns under three headings (colsum.cpp:1006-1024), and **a row
  without columns cannot carry a heading** — before them, a colony
  with everyone farming showed a run of squares and then nothing.
  Stage 4 gave the row five real columns with those headings above
  them, so the stand-in had nothing left to stand in for; this entry
  already said "whether they stay is Stage 5's call". Deleted from
  `colonytrack`, `colonylist`, `layout.json` and the checks in ONE
  commit, and **no invisible button was left behind**: the drop
  target was never the marker, it is the whole column (see the
  DEVIATION above). The cells moved left by the marker's width, to
  the column's own left edge, which is where the original starts its
  icons (`left_x`, coldraw.cpp:349).
- **DEVIATION — the held cluster's figures are offset by the SPRITE
  STEP.** `COLMOVE::Draw_Cluster_` (colmove.cpp:7-37) hangs them on
  the pointer at +5 x, −10 y with 20 px between them, native, against
  a 28 px sprite; HD multiplies all three by `FIGURE_STEP` so the
  overlap with the pointer is the original's at every resolution.
  What makes it a deviation is what it is NOT consistent with: the
  job columns are 2.53× their native width and the pointer is
  4.38 % of window height, so three magnifications live on this
  screen and this constant picks the sprite's. In
  `core/zoomtables.CLUSTER_FIGURE_OFFSET`,
  `colonylist.draw_held_cluster`, and a smoke check.
- **HD EXTENSION — an identity letter in the cell, fill untouched.**
  The original carries profession AND race in one sprite
  (`race * 13 + job * 2 + 1`, colony_main.cpp:445) and carries the
  profession by WHICH COLUMN the sprite stands in. One track, no
  columns, so the cell carries both: fill for the profession, letter
  for the identity. The player's own pops carry none. `N` is
  confirmed three ways; `A` and `C` rest on the source alone. In
  `colonylist._cell_mark`, `layout.json` under `_cell_marks_note`,
  and a check.
- **HD EXTENSION — a hover popup below the row.** It overlays and
  never reflows (decision 46: the list is the click frame). It flips
  above in a row at the panel's bottom, and that is not a preference
  — `screen.render` draws the frame image AFTER the content, so a box
  outside the cutout is covered by metal and the only place left is
  above. **And it does not appear at all while a selection is held**,
  because aiming happens on the hovered row and a popup following the
  pointer would flicker under the gesture it interrupts. In
  `colonypopup`, `layout.json` under `_hd_extension_popup`, and a
  check.

**What it collapsed.** No job is ever empty now, so the empty-group
placeholder in `drop_targets` — the seam rule with its two bounds,
written the day before — is GONE rather than bypassed. The marker is
that placeholder, made permanent and visible. One layout path, and a
check that fails if a job's target is ever thinner than a marker.

**One geometry for the whole row.** `colonytrack.row_boxes` returns
markers, cells, targets, growth boxes and the beyond-line in pixels,
and everything that draws or hits calls it. The growth boxes moved to
the END, past a fixed `growth_gap` from `layout.json`: they belong to
the COLONY and not to any job.

**The cost, for Task 6.** The track is now measured from
`POP_LIMIT_CAP + 3` slots plus the gap, so a slot is about a
fifteenth narrower than before. Irrelevant at 42 slots and
**relevant the day the track is shortened to the empire maximum** —
at a maximum of 22 the three markers are an eighth of the row, not a
fifteenth. The trade belongs in that decision, not before it.

**A fifth identity class is deliberately unmarked, and it is a gap
rather than an oversight.** An assimilated pop of another race —
conquered bit clear, nibble not the owner's, which
`invasion.cpp:672-676` produces when the conqueror is Assimilative —
draws exactly like one of the player's own, while the original draws
it with its own race's figure. Its natural mark is a race initial,
which collides with the marker alphabet (Sakkra and Scientist share
a letter), and no fixture holds the case to judge that collision on.
Marking it from a guessed mapping is what a picture of the wrong
thing is made of.

**The minimap is black now, and that is a measurement.** The panel
already had a fill — the cockpit texture was never showing through —
but it was `PANEL_BG` (8, 11, 20) while the original's own inset
region measures (0, 8, 0) over 2475 of about 2700 samples. So black
moves TOWARD the original. Done as a per-box fill
(`galaxy_inset_fill`), not as a change to `colonyinset`, which draws
no background at all by transcription (movebox.cpp:36-38) — and the
sentence in that module claiming the original shows a faint star
texture there is corrected with the measurement.

> **CORRECTION, 6 September 2026 — this paragraph was false for a
> day, and the false half was "now".** The value was right and never
> reached the box: it sits inside `panels` in `layout.json` and
> `_render_panels` read `<name>_fill` from the TOP level of the same
> file, so the lookup missed, the default was used, and the panel
> stayed blue in the running game. Fixed in the entry above, and
> sampled off a live frame rather than asserted from the value.

**Two files were full, so the geometry moved out.**
`colonylist.py` stood at exactly 300 code lines and `screen.py` at
299. `colonytrack.py` is the new home for the row's arithmetic — the
seam this tree already had between the NUMBERS (`colonyrows`) and the
DRAWING (`colonylist`), with the ARITHMETIC unnamed in the middle. It
is also decision 5's home: one function produces the rect, and the
day the drop targets were two copies of a thirds calculation is what
that costs when the geometry is scattered through a drawing module.

### Drop targets follow the groups — rebuilt 5 September 2026

The old shape was three equal thirds of the whole 42-slot track.
**Every job was reachable that way, but only at a place where nothing
stood.** A colony of 13 pops has all its cells inside the first
third, so a click on a worker cell named FOOD, while empty track two
thirds along named research and worked — which is exactly why the
phase 3b acceptance could move pops into industry and research while
every cell in every row named the wrong job. `band_xy` aimed at the
bands, and the bands were reachable; the cells were the part that
lied. Measured across the reference save before the rewrite: every
non-food group of every row named food.

Now the target IS the group — for a job with pops, the exact extent
of its cells — with a one-cell placeholder for an empty job, and no
drawn cell moves. The rule and its two bounds are in
`colonylist.drop_targets`, which is also the ONE function the
outline is drawn from (decision 5); before, the drawing and the hit
test each computed their own thirds and agreed with each other while
disagreeing with the squares.

**One correction to the seam rule as it was handed down.** "No more
than half a neighbour's width" is not enough by itself: against a
two-cell neighbour half its width is a whole cell, and Neptunus I
`[0, 0, 2]` lost the first research cell to two leading placeholders
outright — the same fault in a new place. The second bound is half a
CELL, so half a drawn square always survives on its own side and the
cell keeps its centre. A smoke check asserts the centres rather than
the arithmetic.

### Pop identity — HALF VERIFIED, and the halves are named

5 September 2026, against `fixture_natives_3502.5.GAM`. This is the
first pop-type value in the tree with two independent sources in
decision 23's sense — until now every statement about nibbles 8 and 9
rested on three source sites that could all have been wrong together.

**VERIFIED: nibble 9 = native.** Three sources, one snapshot:

1. **the data** — Urna I holds four pops, one of nibble 0 and three
   of nibble 9, all four profession 0;
2. **the picture** — that row's FARMERS column draws four sprites,
   one thin Elerian farmer with a staff and three stocky figures
   that are a different creature rather than a recolour. Same
   three-to-one split, same column, same snapshot;
3. **the game's own words** — hovering them on the colony screen
   makes it print "Native farmers".

**STILL OPEN: nibble 8 = android, and the conquered bit.** No pop in
either fixture carries either. `Colony_Pop_Anim_` (colony.cpp:1268)
can draw four classes and these saves witness two. So the identity
marks in Task 4 are marked **"0 and 9 verified, 8 and conquered
open"** — not "verified" with a footnote, because those are different
claims and the second one invites a reader to stop reading.

The evidence lives in `~/orionlayer-fixtures/evidence/` with the
saves: the two screenshots Data captured, and a row-level HD/native
pair rendered from one snapshot. Not in the repository — a screenshot
of the player's game is the same category as the savegame.

**A bug in the engine fell out of it**, filed as
`doc/orion2re_open_fixes.md` item 11: `Colony_Has_Natives_`
(colony.cpp:1391) tests nibble 8. It gates the occupation-policy
popup, so a colony with natives is never offered the choice and one
with androids is offered it pointlessly. Reproducible in the named
save; the consequence for the engine is written into the item, and
what we could NOT establish is written there too.

**CLOSED — the `no_farming` test case, open since 4 September.**
Neptunus I and Piatuos I have `max_farms == 0` and hold only
scientists, so dropping one onto the food column is refused at the
first pop: `plan_drop` returns `landed=0, reason=no_farming`. That is
a prediction which is not "all" — the thing the reference save could
not produce and the reason the phase 3b protocol had to record the
gap in a sentence instead of testing it. Of the four items on the
savegame shopping list, two are now closed (natives, no farming) and
two remain open (an android, a conquered pop).

### Zhadoom III — the earlier observation, resolved

The step-1 report suspected the original drew visibly different
sprites inside one job column there. It does not. Zhadoom III's 14
pops all carry nibble 0, no conquered bit, and the picture agrees:
ten identical orange farmers in the farmers column, four identical
cyan workers in the workers column, scientists empty. **The
difference is BETWEEN columns and it is the profession**, which is
`People_Anim_(job, state, race)` indexing `race * 13 + job * 2 + 1`
(colony_main.cpp:445).

Neither candidate from the source applies: the shadow farmer needs
`max_farms != 0xff` (coldraw.cpp:392) and Zhadoom III's is 255, and
the darkened scanned pop blinks under the pointer rather than
persisting. The earlier observation was about columns, and the row
that really does differ within a column is Urna I.

Worth keeping from it, for Task 4: **the original's native sprite
does not encode the job.** Entry 0xAA is one sprite for every native
whatever they do (colony_main.cpp:456); the job is carried by which
COLUMN it stands in. HD's single track has no columns, so a cell must
carry both — which is exactly what the fill-plus-mark split is for.

### Phase 3b — ACCEPTED, 5 September 2026

Run against the reference save with the rebuilt binary, criterion by
criterion, all five green:

| Criterion | Result |
|---|---|
| full colony diff before and after one move | PASS — all 55 records compared, exactly one changed |
| the colony index bound to a name | PASS — "10 = Blucher II"; both tools print it now, because an index alone is not a claim anybody can check |
| abort path sends nothing on the wire | PASS — counted at the client, `activate_field=0 inject_click=0`, not "the screen looks the same" |
| PNG render beside a native screenshot | PASS — `tools/colony_move_hd.py` now writes both halves FROM THE SAME SNAPSHOT and composes them through `colony_list_preview.side_by_side` |
| `python tools/smoke_test.py` under `SDL_VIDEODRIVER=dummy` | PASS — 80 checks |

**What the side-by-side showed that no table had.** The original
draws its pop icons per race AND per job — orange farmers, blue
workers, pale scientists (`People_Anim_`, colony_main.cpp:444) — in
three FIXED, visibly boxed columns, and it fills its building column
with "Trade Goods - 1t" where HD's is empty. The counts agree row for
row (Blucher II 11/1/1, Blucher III 5/0/7, Draconis I 1/0/0), so the
data is right and the two known gaps are exactly the ones already
recorded: no building names without the `techname.lbx` extractor, and
no identity in the cell yet. The HD zone colours are a different
palette from the original's sprites and are already marked INVENTION.

Carry-overs cleared with it: the held-cluster message now names
RETURN — the control, not the gesture — with its reason beside it in
`layout.json`, since pressing it runs `Clear_Cluster_`
(colsum.cpp:804), an exact undo. The `zoom_probe` / `park_game`
citations in fundament section 3 were already corrected in `ccf7e0c`
and were re-read rather than re-written.

### Brief 87 Part 3b — the editor writing frame holes: CLOSED AS SUPERSEDED, 12 September 2026

**There is no plate to rebuild.** This item asked whether the F5
editor should let a cutout be dragged, write `layout_reference.json`
and rebuild the plate through `frame_build.py`; the plate machinery is
deleted (decision 55) and `frame_build.py` with it. The reason it was
deferred — *"a second writer for a derived file"* — has no referent:
nothing on this screen is derived any more.

**What is LEFT of the question is a different one and is not parked
here.** Whether the editor may write `layout_reference.json` at all is
still open, and the objection has changed shape: the file is not a
derived artefact, it is the geometry, and the thing that would have to
survive a drag is not a byte-for-byte rebuild but the rule that every
rectangle lands inside a hole of the artwork. A drag that broke that
would be caught by the smoke test rather than being unanswerable. It
is a smaller question than this one was. The record below is what was
decided on 10 September and why.

Data's decision, 10 September 2026. **NOT `phase 3b` of pop
movement**, the section directly above this one, which is ACCEPTED
— the numbering collides and the two have nothing to do with each
other. This is the open item Part 3 stopped on: whether the F5 box
editor should let a cutout be dragged, writing
`layout_reference.json` and rebuilding the plate through
`frame_build.py`.

**Deferred, and the reason verbatim: "a second writer for a derived
file".**

The plates are DERIVED (decision 49) and the licence to call them
that is a byte-for-byte regeneration, not the existence of a tool
that looks like it made them (decision 40). `frame_build.py` is that
one writer today, so the regeneration either reproduces the tree or
it does not, and the answer is a single check. A second writer with
a mouse on it does not break that property so much as make it
unanswerable: an edit that changed the plate and an edit that
changed nothing would leave the same tree, and "the plate is what
the tool produces" would depend on which writer ran last.

**Resubmit trigger: a frame master at 3840 or wider.** The master is
2322 px, so 1920 is a downscale and 2560 and 3840 are both upscaled
interim variants — the dated entry is under "the colony frame is
built, not rendered". Until a native master exists, dragging a
cutout moves a hole in artwork that is itself provisional at two of
the three shipped resolutions, which is the wrong order to do the
two pieces of work in. When the master lands, the holes are re-cut
against it anyway, and that is the moment to ask whether a mouse
should be one of the things that cuts them.

Nothing in Part 3 depends on this. The editor classifies cutouts as
LOCKED, offers no handle on one, and the info bar names
`tools/frame_holes.py` as the place to change it — which is the
behaviour whether or not 3b is ever built.

### Phase 3c — update to upstream (build 15 Aug 2026): DEFERRED

Decided 5 September 2026. **Not during the colony screen work.**
`doc/orion2re_tree_comparison.md` is the evidence; this is the
decision and the plan.

**Why deferred.** Nothing the colony screen needs is in C. Every
value it reads is already on the wire from the build we have, and
`s_colony` keeps its size and every offset in C anyway — so the
update buys the colony work nothing and costs it a rebuild of every
citation it stands on.

**Why it cannot be done in pieces.** The four are not independent:

1. `platform.cpp` — the pointer fix must be **re-derived, not
   re-anchored**. `Sync_Mouse_State_From_SDL_`'s tail now runs
   through `Forward_Game_Mouse_State_` with a new `debug_overlay`
   consumer, so the place our early return protects has moved. The
   symptom of getting it wrong is the population move going quiet
   again, which looks like nothing at all.
2. `racesel.cpp` — the crash fix (open fix 5) plus the four
   screen-id hunks, by hand: the file is re-indented upstream and no
   hunk applies.
3. `core/game_state.py` and the struct specs — `s_ship_data`
   0x81 -> 0x87, `s_antaran` 0x42 -> 0x44, `s_player` now size
   -configurable (0xf0e or 0x2d86 by `MAX_FREIGHTED_SETTLERS`).
   The snapshot is a sequential concatenation, so those two wrong
   sizes desynchronise everything after the ships block. **And in
   `core/structs/colony.py`, `food2_per_farmer` and
   `industry_per_worker` change `int8_t` -> `uint8_t`** — same size,
   same offset, different meaning above 127: the `imports` sign trap
   (open fix 7) in a second place.
4. every line number in `doc/` and `core/structs/` re-anchored.
   `coldraw.cpp` and `invasion.cpp` are the least trustworthy —
   more differing lines than either file has.

Skipping 3 means a client that reads garbage with no error; skipping
1 means a feature that silently stops; skipping 2 means a crash that
was already fixed once. So it is one piece of work or none.

**Two items that do NOT wait for the update**, and are scheduled
before H1:

- **`tools/version_check.py` reads too little.** C and B carry
  identical `ENGINE_VERSION` and `GAME_VERSION_LABEL`, so the check
  would call this update "no change". It must also read
  `GAME_BUILD_DATE` (May 31 -> Aug 15 2026 is what actually moved)
  and the `sizes.h` asserts for every record our specs cite, so a
  layout change fails the check instead of being discovered by
  garbage on screen.
- **`HELLO_REPLY` should carry the record sizes**, or a hash of
  them — additive in `src/ext/`, so it diverges from nothing — and
  the client refuses to parse on a mismatch rather than reading at
  the wrong offset. `PROTO_VERSION` cannot do this job: the protocol
  did not change, the structs did.

And one request for Joes, filed in `doc/orion2re_open_fixes.md`:
bump `ENGINE_VERSION` when a serialized record layout changes.

### Colony summary — three OPEN DESIGN QUESTIONS, not decisions

Recorded 5 September 2026. `doc/colsum_design_analysis.md`
recommends one answer to each of these; a second design exists that
was worked out in chat and **is written down nowhere in this tree**.
Two candidates where only one is on paper is not a comparison, and a
recommendation in a document nobody can compare against is not a
decision either. So all three are OPEN, and none of them may be
cited as settled.

They are decided by RENDERING both variants side by side against a
native screenshot, at 1920x1080 and at one 4K size, with the cells at
their real size and a dashed free slot adjacent — the collision the
analysis predicts between a mark inside a cell and the free-slot
outline is either visible in that picture or it is not. That is the
tree's own rule (fundament, "render every new renderer to PNG and
look at it before a green table counts as evidence"), and it applies
here more than usual because both candidates are defensible in prose.

1. **Identity mark.** A glyph or letter INSIDE the cell
   (`colsum_design_analysis.md` §8) against a border or shading
   treatment of the cell (the chat design). Both have to carry four
   classes, because `Colony_Pop_Anim_` (colony.cpp:1268) has four:
   conquered, native, android, and per-race-per-job. The scan
   argument cuts both ways and is not settled by argument: over 90 %
   of cells are "own race, normal" and must stay quiet, and a border
   treatment is quieter than a glyph while also being the axis the
   free-slot dashes already use.

2. **Contextual information.** A hover-driven inspector in
   `spare_panel` (§10) against a tooltip below the row. **The
   analysis's rejection of "popup under the row" was imprecise and
   has been amended:** it refuses a box that REFLOWS the list, which
   decision 46 does settle, and it says nothing about a box that
   OVERLAYS it, which is a legibility question. If the tooltip
   variant overlays, it is a live candidate and gets rendered; if it
   reflows, it is out without rendering.

3. **Job band or blocker cell — possibly not a disagreement at
   all.** The analysis's "job band" is a hit region derived from the
   track (`colonylist.drop_band`, three equal thirds while a
   selection is held, HD EXTENSION). The chat design's "blocker
   cell" is described as one PERMANENT cell per job group that is
   separator, drop target and icon carrier at once. Those may be the
   same object seen from two sides, or two different things — one is
   transient and derived, the other permanent and occupying track
   width. **That question is answered first**, because if they are
   the same object there is nothing to decide, and if they are not,
   the permanent variant spends slots the track has to pay for.

The two items that change the horizontal geometry — track width from
the empire maximum, and `row_height` 58 to 46 — are deliberately NOT
in this list. They move the click targets, so they follow the
identity mark rather than accompanying it.

### Not built
Colony, Research, Fleet, Ship Design, Officers, Diplomacy, the
summary and list screens. Tactical Combat is recommended to stay in
original mode. Cross-platform builds. Planet images for 12 of the 13
races.

### Loose ends
- **`doc/v3_fundament.md` vanished from the working tree on
  9 September 2026 and the cause was never established.** It was
  restored with `git checkout` and the restored file is
  **byte-identical** to the committed one, so nothing in the
  document was lost and no commit is affected — the file had not
  been edited since its last commit, which is the only reason the
  restore could be clean. **What is NOT known is why it went.** No
  commit removes it, `git reflog` shows no HEAD movement that could
  have taken it (and `git checkout -- <path>` leaves no reflog entry
  either way), and nothing in the shell history names it. Re-checked
  10 September 2026: the file is present and matches HEAD.
  Kept here rather than closed, for two reasons. The first is that
  an unexplained disappearance is not a fixed one, and the same
  event on a file with uncommitted work in it would be a real loss
  — the fundament is the document every session is told to read
  first, and it is long, hand-written and not derived from anything
  that could rebuild it. The second is the shape: this project's own
  rule is that a fault nobody wrote down is indistinguishable from
  one nobody saw, and a near-miss with no cause is exactly the entry
  that gets dropped because nothing is broken today. What would
  settle it is any second occurrence with the shell history or an
  editor's session log intact — until then it is one event, recorded
  and open.
- **Select Race kept reporting screen 6 after a cancel — FIXED and
  live-confirmed 5 September 2026.** The fourth hunk of
  `doc/ext_screen_id.patch` saves the caller's id on entry and
  restores it before the cancel `return 0`, the same shape the Custom
  Race pair already used. Verified against a rebuilt binary: main
  menu -> New Game -> race selection (id 6) -> ESC -> the next
  snapshot reports 13. Kept here because the SHAPE recurs: an entry
  hunk that sets a reported value needs an exit hunk on every path
  the caller does not cover. What it looked like before: `Race_Selection_Screen_` writes
  `MOX::_current_screen = SCREEN_RACE` on entry (our hunk, now in
  `doc/ext_screen_id.patch`) and nothing clears it: the cancel path
  returns 0 untouched and `newgame.cpp:113` reloads New Game. So a
  player who backs out of race selection leaves the API reporting 6
  while the game draws 13, until New Game itself exits — and the HD
  dispatcher routes on that number, so it draws Select Race over a
  New Game screen with no way to notice. Custom Race does not have
  Custom Race never had it: its cancel restores and its accept is
  covered by the original's own line (racesel.cpp:692).
- **`make_star_icons.py` does not reproduce the star sprites in the
  tree.** The committed 36 are trimmed to content (44 to 206 px); the
  tool emits uniform 256x256 canvases. Both render correctly — the
  renderer scales to the icon size either way — so nothing is broken
  today, and the smoke test's star checks are size-agnostic and do
  not see it. But it means the tool is not a faithful regenerator,
  which is why `stars/` stayed out of `.gitignore`. Either the tool
  gains the trim step that produced the tree's set, or the committed
  set is regenerated at 256 and the artwork re-measured; the first
  is cheaper and the second is more honest. Until then this is the
  only asset set whose generator and output disagree.
- **Nebula masters overhang the original outline** on types 1, 9 and
  11 — 13 to 16 % of the reference area at alpha > 25, and still 7 to
  13 % at alpha > 128, so it is body rather than fringe. The zoom-3
  variant doubles as the gameplay shape
  (`geo.cpp Point_Is_In_Nebula_N_`), so a star just outside the
  boundary can look wrapped in gas while the game counts it as clear.
  Membership is read from `s_star_data.in_nebula`, never from the
  artwork, so nothing computes the wrong answer — it only looks
  wrong, and only at the edge. The originals' own zoom-0 and zoom-3
  outlines already disagree by up to 7 %.
- **`tools/make_nebula_icons.py` writes a layout nothing loads.** It
  produces `type_NN/zoom_N.png`, four pre-rendered variants per type,
  which is what the renderer wanted before the size moved into
  `NEBULA_DIM`; it now loads a single `type_NN.png` per type and
  scales it. The tool is still the only path from STARBG.LBX to
  usable HD artwork, so it wants its output flattened rather than
  deleting it.
- **The original's font sizes are MEASURED off screenshots, because
  there is no font extractor.** `Set_Colony_Font_To_(n)` is a style
  INDEX; the pixel height is `_font_header.font_heights[n]`, read from
  the player's own FONTS.LBX at load (`fonts.cpp Set_Font_Style_`), so
  it is in no source file this project can grep. Every size
  transcribed from the original therefore rests on one picture — today
  that is "No Farming" at 10 px of cap height off
  `colony_summary_native_split.png` (`colonylist.NO_FARM_FONT_REF`),
  and it is marked MEASURED rather than transcribed for exactly that
  reason. A `tools/font_extract.py` in the shape of
  `techname_extract.py` would turn every one of them into a
  transcription with a second source, and would also say which style
  index each screen uses at what height. Not scoped; recorded so the
  next size measured off a picture is the second entry in a known gap
  rather than a fresh surprise.
- **68 boxes carry a hand-tuned `font_scale` that is DOUBLE-SCALED at
  3840x2160, on four screens, and they are known-wrong rather than
  fixed.** Custom Race, Select Race, Empire Identity and the galaxy
  map pass `box_font_scale` into a `Layout.font_size` afterwards, and
  not one of the 68 is tuned at 2160p — every screen's list stops at
  1440p, so at 4K they resolve by pixel area to the 1440p list and
  take the same 4.0 net factor. The measurement, the reason they were
  NOT changed with the colony summary's, and the trap in changing
  them (the values encode the double factor, because they were tuned
  by eye with it already in place) are in "Stage 4 closed: the pitch,
  the 4K readouts, and three readings" above — that section is their
  one home and this is a pointer, so the two cannot drift. Recorded
  here on 8 September 2026 because a fault that lives only inside a
  dated stage narrative is one nobody meets again: re-tuning those
  four screens for 2160p is its own decision and has no owner yet.
- `new_game/boxes.json`: `panel_0`–`10` exist at 2560x1440 but the
  1920x1080 list carries only `help_popup` — so at 1080p New Game
  draws no panel frames at all, in either skin.
- Custom Race homeworld information has no home in the new layout.
- Star size steps 3 and 4 differ by only 2 native pixels, so size is
  indistinguishable when zoomed out. This matches the original
  exactly; spreading `STAR_FIELDS_DIM` would be a design decision, not
  a transcription.

---

## orion2re: open C++ fixes

**The list lives in `doc/orion2re_open_fixes.md` and nowhere else.**
This section and `doc/ext_api_dokumentation_v3.md` have each drifted
from it once; both are pointers now, and the ext API document was
brought back in line this session after describing two applied fixes
as open.

Current state (30 August): **items 3 and 4 are open, both
INJECT_CLICK** — the window-coordinate mapping and the missing
MOUSEMOTION before the button events. Items 1 (SendFrame short
write), 2 (FIELD_LIST after HELLO) and 5 (the `racesel.lbx` crash,
via `_old_race`) are applied in the source tree; the fixes file
carries a grep per item to verify any working copy.

`doc/ext_ship_icon_owner.patch` is **not** requested — see the file
for why it turned out unnecessary. Nothing was added to the list for
the context help: the text lives in HELP.LBX, which a client reads
itself, and the regions live in the C++ only as tables to transcribe.

---

## Scope estimate

~20–22 full screens plus 10–15 dialogs and popups; roughly 30 % done.
Remaining Python is estimated at 20,000–25,000 lines without an HD
tactical combat, 25,000–30,000 with it.

Assets are the real cost driver: 166 MB today after the cleanup,
realistically 500 MB–1 GB at the master resolution.

The C++ side is essentially finished — two ext fixes remain, both
about INJECT_CLICK, both behind `#ifdef`.

Colony is the largest single remaining piece; every screen after it
gets cheaper thanks to the template, auto-discovery, widgets and the
frame system. Leaving Tactical Combat in original mode saves roughly
20 % of the total project.

---

## Commands

**Start the game** (built with `-DORION2RE_EXT=ON`):
```bash
cd "$HOME/Master of Orion 2" && ~/orion2re/out/build/Linux/linux-debug/orion2re
```
Wait for `ext: server started on port 17362`.

**Start the frontend, with a log:**
```bash
cd ~/orionlayerv3 && python main.py 2>&1 | tee ~/orionlayer.log
```

**Verify after any change:**
```bash
python tools/smoke_test.py
```

**Set up a fresh clone** (pygame, numpy and Pillow from your system's
package manager; `pip install` is refused on PEP 668 distributions):
```bash
python tools/setup.py
```
Rebuilds the generated artwork the repository does not carry, then
runs the smoke test. `--check` reports without changing anything.

**See what changed** — the job `verify_tree.py` used to do:
```bash
git status
git diff --stat
```

**Extract MOO2's context-help texts** (once, needs the game folder;
re-run after a game language change):
```bash
python tools/help_extract.py
python tools/help_extract.py --lang de          # GER_HELP.LBX
python tools/help_extract.py --ids 288,547      # print, write nothing
```

**Regenerate artwork** after editing the parameters or a master:
```bash
python tools/make_star_icons.py --sheet
python tools/make_black_hole_master.py
python tools/make_ship_icons.py --sheet
python tools/make_sidebar_icons.py
```

**Measure what a zoom step does to the game's view origin** (game
running, savegame loaded, galaxy map open):
```bash
python tools/zoom_probe.py
```

**Check the zoom ladder** on an extended or Maximum galaxy:
```bash
python tools/zoom_check.py
```

**Diagnose "my new artwork is not showing":**
```bash
python tools/star_icon_check.py
```

**Diagnose a grey fleet or an unidentified monster** (game running):
```bash
python tools/ship_icon_check.py
```

**Regenerate galaxy map boxes** after editing `frame.png`:
```bash
python tools/frame_holes.py screens/galaxy_map/assets/frame.png --write
```

**Probe struct offsets** (game running, savegame loaded):
```bash
python tools/struct_probe.py nebulas
python tools/struct_probe.py colonies --records 2
```

---

## Reference

| Document | Location |
|---|---|
| Decisions, principles, rules | `doc/v3_fundament.md` |
| orion2re source index | `doc/v3_orion2re_index.md` |
| Extension API (for Joes) | `doc/ext_api_dokumentation_v3.md` |
| What is asked of Joes (ONLY home) | `doc/orion2re_open_fixes.md` |
| Empire Identity slow-load record | `doc/empire_identity_slowload.md` |
| Git/GitHub workflow | `doc/UMZUG.md` |
| Working agreement for Claude Code | `CLAUDE.md` |
| Ship icon measurements | `doc/ship_icon_measurement.md` |
| Star field measurements | `doc/starfield_measurement.md` |
| Modding guide | `MODDING.md` |
| Project README | `README.md` |
| Colour palette | `assets/shared/skins/default/colors.json` |
| Sizing tables | `core/zoomtables.py` |
