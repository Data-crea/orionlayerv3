# Work order 165 — progress

Unattended run, 22 September 2026. The research screen complete inside
its frame: change mode (36), the two shared popups, and the rest of
select mode (53).

**Written so a fresh session can resume from this file alone.**

Evidence root: `~/orionlayer-fixtures/evidence/work_order_165/`.

---

## UPDATE, third session: PUSHED, and PART D IS CLOSED

Data freed the port and released the push. In order:

**The twelve commits of 165 are on GitHub**, `57e3eda..f8d259a`, after
the fresh-clone verification the tree's rule asks for: clone,
`python tools/setup.py`, full suite 251 green in 57 s, fast tier 244 in
30 s, both hooks live off `core.hooksPath` (`fresh_clone_push.txt`).
The push itself went through `tools/githooks/pre-push`, which ran the
FULL suite again before git sent anything.

**The load driver exists** — `tools/gameload.py`, the thing part D
parked on. It is the chain the second session said was missing, and its
own commit says what it checks against.

**Part D's last item is done live**: three changes in three categories,
every one read back off the wire as a PAIR, one of them by bare
`ACTIVATE_FIELD`. **Open fix 25's commit path covers change mode.**

SAVE1-9 byte-identical across everything below; SAVE10 and SAVE11
unchanged too. Nothing was ever saved — the scratch slots were only
ever READ.

**What Data will find loaded:** SAVE5 (stardate 3509.1), because that is
where the last change was measured. His own game was at stardate 3500.3
with 2 players, 54 stars, 28 colony records when this session started,
and `SAVE10.GAM` — the autosave — holds exactly that stardate.
`python tools/gameload.py load 10` puts it back; this run did not do it
on its own, because the protocol names slots 4 and 5 and a load of any
other slot is Data's.

---

## UPDATE, second session: the port was freed and PART A IS DONE

Data closed his client. orion2re itself is still the same process
(pid 35367, running since 20:28) — **his game, not a fresh one** — so
everything below was done read-only: one client, one snapshot, nothing
sent but the handshake. SAVE1-11 identical before and after, SAVE10
included.

Part A is committed (`06aca9a`). Parts B to E are not built; the run
stopped at the point where the next step was a large refactor, and
said so rather than starting one it could not finish well. What Part B
needs is written out below, including the seams, so it is a short job
and not a re-derivation.

---

## THE RUN WAS BLOCKED FOR EVERY LIVE STEP — the first session's finding

**Data is playing right now.** Checked before anything else was done,
which is rule 8 of the standing block in
`doc/briefs/126-work-order-unattended-run.md`:

```
LISTEN  127.0.0.1:17362   users:(("orion2re",pid=35367))
ESTAB   127.0.0.1:37656 -> 127.0.0.1:17362   users:(("python",pid=35712))
35367  Di Sep 22 20:28:44 2026   orion2re
35712  Di Sep 22 20:28:52 2026   python main.py
```

orion2re **and Data's own OrionLayer client** have been attached since
20:28. The rule is not ambiguous:

> *exactly one client on the server. Check for a running OrionLayer
> before you connect; if Data left his open, do NOT kill it — skip the
> live step and park it.*

Evidence: `live_blocked.txt`.

**What that removes from this order:**

| part | what is blocked |
|---|---|
| **A** | the SECOND source of every offset. Decision 23 wants two and this order's Q5 rule repeats it; the second is a live read and a live read needs the port |
| **B** | its whole acceptance — "row clicks and bare activations both commit, **read back off the wire**" |
| **C** | nothing. It is display-only and offline-provable |
| **D** | all of it |
| **E** | all of it — 131's parts A, B and C are live from end to end |

**What remains and is being built:** the offline half of A, then C, then
B, each with the offline proof it can have (headless renders,
hit-testing against drawn pixels, markings held by checks), and every
live item parked with the exact commands to finish it.

This is the order's own sanctioned path, not an improvisation: part D's
abort rule already says *"finish parts B and C offline, describe the
needed engine change, park"*, and rule 3 of the standing block says a
parked item is a finished result.

---

## THE READING BUDGET — the second finding, and it is structural

The order says: *read the index first, then every `principles-` part and
the decision parts this task touches. Reading budget as in work order
127.*

**That instruction cannot be satisfied inside that budget**, and work
order 164 is why:

| | KB |
|---|---:|
| the index | 3.7 |
| the three `principles-` parts (always read, 164's rule) | 62.3 |
| `02-decisions-the-orion2re-boundary.md` (20-25, 33, 39 — all touched here) | 35.8 |
| `05-decisions-process.md` (31) | 6.6 |
| `04-decisions-screen-artwork-and-markings.md` (61, and 69 for the GAME-menu precedent) | 29.2 |
| **total** | **137.6** |

Work order 127 proposes "something near 60 KB" and Data never fixed a
figure; 162 and 164 have been using 80 KB as the working number. Either
way the orientation this order asks for is 1.7 to 2.3 times it, **before
a line of the task's own material is read**.

**The run did not stop on it**, and the reason is a fact rather than a
judgement: the whole fundament was read verbatim earlier in this same
session, for work order 162, and is still present. Re-reading it would
have spent the budget to learn nothing. What was read for THIS order is
the task's own material — the standing rules, work order 129's three
additions, `tech_change_reading.md`, 131, 130's parked file, 127 itself
and the existing screen — about 72 KB.

**This is the question 164 parked, arriving.** 164 asked whether every
`principles-` part should really always be read; 165 is the first order
to pay for the answer being "yes". It is in the parked file with the
options.

---

## Part 0 — the brief filed — **DONE**

## Part A — foundations — **DONE**, `06aca9a`

**Three of four offsets got their second source, and the surprise is
that none of them needed the game's own screen.** `unverified.py` had
recorded that source two for @379 would have to be "a live read whose
values agree with the rows the game's own screen draws". It turned out
three agreements inside one read-only snapshot are stronger, because
each one is against something already verified:

| offset | second source |
|---|---|
| `s_player.current_research_application` @902 | reads 196, and application 196's field through the app->field table `tools/research_cost_check.py` holds to techdata.cpp is 45 — which is exactly what the VERIFIED `current_research_field` @901 beside it says |
| `s_player.tech_applications` @379 | every one of the 212 bytes is a TECH_RESEARCH_STATUS; all 52 RESEARCHED applications are backed by a researched field in the VERIFIED `tech_fields` @296; and the application @902 calls in progress reads **available**, not researched — a field you are working on is not one you have finished. Its two siblings under field 45 read available too, which is what an unfinished category looks like |
| `s_settings.language` @210 | pinned by its neighbour `number_of_players` @213, whose value 2 equals the player count the SNAPSHOT HEADER carries independently of the settings block. A misplaced block would have to put a 2 exactly there by accident — and `core/game_state.py` has been reading `difficulty` at @212 all along, which is the same block agreeing a third time |

The header route was re-run for all four with `offsetof` directly
(sizeof(s_settings) == 553, sizeof(s_player) == 0xF0E), and
`tools/struct_header_check.py` now asserts the three new fields on
every suite.

**`hyper_advanced_tech` @640 stays in `unverified.py`, and says why:**
all eight bytes are 0 in this game, so the read is inconclusive. It
needs a game that has reached a hyper-advanced field. That is the one
item of part A still owed.

**The RP deviation is gone.** With `language` in the spec the suffix
follows the game (RP / FP / PR, tech.cpp:631-639). The marking went
with its cause, `layout.json` lost the suffix it had been carrying —
it is the GAME'S word and a second copy in OrionLayer's own wording
file is the stale copy this project pays for — and the check that held
the marking was replaced by one that holds the TABLE to the original's
four cases. Shown red by losing the language-1 case, caches cleared,
`python -B`.

**What the promotion does NOT license**, written beside the spec field
rather than left to be discovered: the second source settles where the
bytes are and that they are research statuses, not that status 1 means
"this row appears on the game's own screen".
`researchlist.validate_against_fields` still tests that on every entry
and the screen still hands over when it disagrees.

**A note on the marker net, because it worked.** The first draft of the
`language` comment used the word DEVIATION while describing one being
removed, and the tree-wide marker inventory refused the commit: a file
carrying a marking no check reads. Reworded, not suppressed.

## Part A, as first written — **BLOCKED**, and its offline half was smaller than it looked

Three bullets, and the live block takes the first two:

1. **Spec entries per the Q5 rule** — blocked. Every one of the four
   offsets needs a second source and the second source is a live read.
   The header half is already mechanical for all four
   (`tools/struct_header_check.py` runs it every suite), so what is
   owed is exactly the live half and nothing else.
2. **Drop the RP deviation** — blocked, because it is conditional on
   `language` reaching the settings spec, which is (1).
3. **"A fallback from any HD research screen writes one log line with
   the reason"** — **already true, tree-wide, before this order.**
   `main.App._showing_original` routes every hand-over through one
   `_verdict`, and `core/fallbacknote.py` reports it beside the
   sentence it draws (work order 139 A). `research_select` reaches it
   through `wants_original()`. The second half of that bullet — the
   live driver's record naming the HD screen that was drawing — is a
   live-driver change and its correctness is only observable live.

**Nothing was added to `core/structs/unverified.py`.** A half-verified
entry that says "the header route is in" reads, three weeks later, like
an entry that is in — and the file's whole purpose is quarantine. The
owed work is in the parked file as four rows instead.

## Part B — change mode — **DONE**, `777a4de` `02ce4b3` `742a8e3` `889f7dc` `29225db`

Four commits at the seam the last session measured, and one repair.

| | |
|---|---|
| `777a4de` | `core/researchnative.py`: the geometry, parameterised by mode. Select mode's rectangles come out byte for byte what they were |
| `02ce4b3` | `core/researchscreen.py`: the behaviour. `screens/research_select/screen.py` is **eighteen lines** of configuration now and every one of its checks passed unchanged |
| `742a8e3` | `screens/research_change/`, wire id **36** — the engine's own SCREEN_TECH_CHANGE. Its slug in `core/screen_names.py` had named a folder that never existed, so 36 fell through to the framebuffer |
| `889f7dc` | the galaxy map's research window opens it, the field found in the LIVE list by shape |
| `29225db` | a check that asked a FILE LIST went green by absence when the behaviour moved; it asks the CLASS now |

`core/researchpanel.py` took the drawing with it, and with it the
second colour: `_tech_color[2]` marks the field being researched and
its chosen application (tech.cpp:686-696), which select mode cannot
reach because `Tech_Select_` zeroes the field before its list exists.

**One check added** (250 -> 251), and it is about the four places the
modes part company — a configuration that silently collapses into the
other mode is what this shape invites. Every entry exactly 81 px
apart, a different set of help bands, the remaining cost against the
full one, and a way out select mode must never grow.

## Part B — as first written, the seam

Still not built, and the reason changed: it is no longer the live
block, it is size. What is left is a refactor across three modules
plus a new screen folder, and starting one at the end of a long run is
how a screen with fifteen checks on it ends up green and wrong.

**What the next session does NOT have to work out**, because this one
did:

* **The data layer needs nothing.** `core/researchlist.py` carries
  change mode end to end already — `ENTRY_POS_CHANGE`,
  `PANEL_ORIGIN_CHANGE`, and a `select_mode=False` path through
  `reconstruct`, `expected_fields`, `validate_against_fields` and
  `row_field`.
* **"The current field IS offered" costs nothing.** Both modes pass
  `current_field=0` to `offered_field` and the docstring says why: the
  game zeroes it around the call in change mode and before it in
  select mode. The difference is in `tech_fields`, not in the call.
* **The seam is `native.py`.** It is the only module that hardcodes
  the mode — `PANEL_ORIGIN_SELECT` and `ENTRY_POS_SELECT` at module
  level, and `BOX_NATIVE` built from them. Parameterising THAT is the
  refactor; `panel.py` and `screen.py` follow.
* **`panel.py` already expects the second colour.** Its docstring
  records that `_tech_color[2]` "is not missing, it has nothing to
  mark" in select mode. Change mode is what gives it something.
* **Three markings come off** when it is built: the two popups are
  part C, and the RP deviation is already gone.

**The shape**: the behaviour moves to `core/` as a base class with the
mode as configuration; each screen folder keeps its own three JSON
files and a thin subclass, because decision 7 gives every screen its
own folder and change mode cannot share one.

## Part B — as first written

Offline-buildable and deliberately not built. Its acceptance is
entirely live ("row clicks and bare activations both commit, **read
back off the wire**"), and 130's lesson is exactly what a second
unaccepted research screen would repeat: *"130's screen fell back on
every real state and nobody could tell, because falling back looks
like working."* This order exists to fix that, not to double it.

**What the next session inherits, and it is more than it sounds.**
`core/researchlist.py` already carries change mode end to end —
`ENTRY_POS_CHANGE`, `PANEL_ORIGIN_CHANGE`, and a `select_mode=False`
path through `reconstruct`, `expected_fields`,
`validate_against_fields` and `row_field`. The data layer is done. What
is missing is a screen class, its three JSON files, the galaxy-map
entry and the mode configuration.

**The shape it should take**, so the next session does not re-derive
it: `screens/research_select/` is already `native.py` (rectangles),
`panel.py` (drawing) and `screen.py` (behaviour). The order wants "one
implementation and two configurations". That means the behaviour moves
to `core/` as a base class with the mode as configuration, and each
screen folder keeps only its own JSON and a thin subclass — decision 7
gives each screen its folder, so change mode cannot share one.

## Part C — the shared popups — **DONE**, both, both modes

Built in `core/`, once, because both modes are one class already. The
order's scope choice (Q1/Q10) is the default: **both popups, in both
modes.**

### The description box

`core/researchpopups.py`. A right click over a ROW opens the help
record for that row's application — one record, no chain walk, which is
what `Draw_Application_Description_` reads (tech.cpp:786-845) — with
billtext 61, the cost and the language's unit appended as the original
appends them.

**Q9 is settled and needed no extractor.** Every one of the 212 help
records in 0..211 reports `pages == 1`, so the chain walk in
`tools/help_extract.py` has nothing to join in that range and
`help_en.json` already holds exactly the record tech.cpp reads.

**The cost there is the FULL one** where the entry beside it shows what
is left in change mode — the original's design (§3), transcribed, and
the check asserts the two numbers differ so it cannot be measuring one
of them twice.

**It opens over a row and nowhere else.** `Set_Selected_Entry_` matches
`app_click_field_ids` and nothing else (tech.cpp:468-487).

### The category list popup

`core/researchtechlist.py` (content, geometry, paging, drawing) and
`core/researchpopups.py` (the input). It sends **nothing**: the popup
is display-only in the original, so HD draws its own and the game stays
in `_Tech_Select_`'s loop with the panel's field list — which is also
what keeps `validate_against_fields` passing while it is up.

**AND THE RECONSTRUCTION WAS CHECKED AGAINST THE ENGINE'S OWN LIST,
LIVE.** `python tools/research_change_hd.py listprobe <slot> <entry>`
sends the category button ONCE so the engine builds its own popup, then
compares. Both columns:

| | category | HD reconstructs | the game's list | rows |
|---|---|---|---|---|
| SAVE4, entry 0 (left column, window on the right) | 4 | 11 fields over 2 pages | 18 fields | **14 = 14, every rectangle MATCH** |
| SAVE5, entry 1 (right column, window on the left) | 2 | 7 fields over 2 pages | 18 fields | **14 = 14, every rectangle MATCH** |

The pair `(60, 136)` before and after each probe. That is decision 25's
own condition met: the reconstruction carries its own validation.

**It also settled the `tech[4]` padding.** `Get_Group_List_` walks all
four slots and reads `tech_applications[tech[i]]` for the empty ones,
which is `tech_applications[0]`. HD transcribes that rather than
dropping the padding — and in this game the byte is 0, so no phantom
rows appear, which the live match confirms.

### The choices this part made

* **Q1/Q10 scope** — the default: both popups, both modes.
* **Q11, the radio index skew** — the default: HD opens the RIGHT
  category and marks it a DEVIATION. The original indexes
  `entries[input - first_btn_field]` while radios exist only for
  non-empty entries, so it opens the wrong list when a category ahead
  is empty — it is reading data that was never set.
* **Full versus remaining cost** — the default: transcribed. Remaining
  on the entry, full in the description.

### Markings

`category_list_popup` and `description_box` moved from OMISSION to
DEVIATION on both screens, and `radio_index_skew` is new. Two omissions
are left on select mode (the science room, the little arrow) and one on
change mode. Every one is held by a check, and the tree-wide marker
inventory now lists `core/researchpopups.py` and
`core/researchtechlist.py`.

### The defect part C found

**The help popup was drawn UNDER the panel.** `ScreenBase.render` ends
with `render_help` and both research screens drew their entries after
calling it. `ScreenBase` has a `render_content` hook now. The check
renders four frames — baseline, panel only, popup only, both — because
two could not tell the orders apart: 0 of 185 overlapping pixels wrong
as built, 185 of 185 with the order swapped.

## Part C — as first written — **NOT BUILT**

Offline-buildable and offline-*provable*, and still not built, for a
reason that is the project's own rule rather than the live block: the
order asks for them "once, in both modes", and the second mode does not
exist. An abstraction with one caller is a guess — *the third copy is
the signal to extract*. Built now it would be shaped by select mode
alone and reshaped when change mode arrived.

## Part D — live acceptance — **DONE**, and it found three faults

Run against Data's own game, read-only except for the two activations
that open and leave change mode. **SAVE1-11 byte-identical to the
start of the run**, SAVE10 included, and the game was left on the
galaxy map with `current_research_field` 45 and application 196
exactly as found.

### What it proved

| item | result |
|---|---|
| the galaxy map does not park at 36 or 53 | **done offline**, `f172a09`, with a discriminating counter-test |
| ESC and exit leave `current_research_field` and the application unchanged | **DONE LIVE.** Field 45, application 196, before and after. The exit button was found in the live list at `(269,452)-(360,470)` |
| one field with research accumulated: the entry shows REMAINING | **DONE LIVE.** `research_accumulated` 175 on the wire, `cost_offset()` 175 in change mode and 0 in select mode, and every offered entry showed full − 175 — field 45 at 900 showing 725 RP |
| three changes in three categories, read back off the wire | **DONE LIVE**, third session — see below |
| HD beside the native frame at every resolution | **one resolution**, 1920x1080, in `D_change_mode/` |

And the entry path itself: an HD click on the sidebar's research
window sent `ACTIVATE_FIELD 20`, the game moved to 36, the dispatcher
switched to `research_change`, and the screen drew — state `ok`,
`wants_original` False.

### THE TWO FAULTS, and neither was visible to a green suite

**1. The research screen has been handing over to the fallback on
every real snapshot since 19 September.** `expected_fields` carried a
leading dummy for slot 0. Work order 130 C wrote it when the wire
still sent that slot; work order 142 B dropped it once in
`parse_fields` and did not move this list with it. One field too many,
so `validate_against_fields` failed every time and the screen showed
the game's own picture — *which looks exactly like working*, the
sentence work order 130 wrote about itself.

**The checks were green throughout because the stand-in they compare
against is built FROM `expected_fields`**, so the dummy sat on both
sides of the comparison. That is work order 131 part E's own lesson
arriving live: a test double written by the same hand as the code
shares its mistakes. The count is now asserted against the ORIGINAL's
build order — rows + 8 blocks + radios + whole screen, plus the exit
in change mode — computed from the entries and not from the function
under test. Putting the dummy back goes red (`slot0_check_red.txt`).

**2. `current_research_application` was wrong an hour after part A
promoted it.** Declared `i8` because the header says `int8_t`;
application ids run past 127, so the live value 196 came back as −60
and every lookup against the app table missed. The header route fixes
the offset and the width — it does not promise the C type is the one a
reader wants. `u8` now, with that sentence beside it.

### Item 1, done: three changes, three categories, one of them bare

`tools/research_change_hd.py run`, evidence in `D_run/`. Each change
starts from a FRESHLY LOADED scratch slot, because three changes made
one after another on one loaded game are three changes of which only
the first started from a state anybody can reproduce.

| | slot | how | entry / category | committed | the wire says | |
|---|---|---|---|---|---|---|
| 1 | SAVE4 | HD click at window 700,153 | entry 0, category 4 | field 21, application 25 | 21 / 25 | **MATCH** |
| 2 | SAVE4 | bare `ACTIVATE_FIELD 4` | entry 1, category 2 | field 41, application 96 | 41 / 96 | **MATCH** |
| 3 | SAVE5 | HD click at window 700,389 | entry 2, category 6 | field 2, application 106 | 2 / 106 | **MATCH** |

Each one was `(60, 136)` before and the row's own pair after.

**THIS IS THE PROOF THE ORDER ASKED FOR.** `doc/ext_tech_activate.patch`
was measured in select mode (work order 130 B) and covers change mode by
SOURCE READING — `_Tech_Select_(changing_tech)` is one function. Change 2
is that reading measured: a bare activation with no click anywhere, and
the row's field AND its application came back. Without the patch the
commit branch reads the game's POINTER (`Get_Selected_Entry_`,
tech.cpp:356) and an activation either commits whatever the pointer is
over or dereferences null — open fix 23's SIGSEGV, seen live in 128 C.

**Why the PAIR and not the field.** A category offers one field and
several applications. The pointer explanation dies on the application:
the pointer never moved in this run, and three different rows came back
with three different application ids.

**The reload is visible in the data, not only in the driver's word.**
After change 1 the wire read field 21; at change 2's panel capture it
read 60 again, which is SAVE4's own value. The fingerprint check says
"unchanged" for the second and third loads of SAVE4 — stardate, players,
stars and colonies do not move when research does — and the research
field is what shows the slot came back.

### Why item 1 was not done in the second session

Three commits in three categories CHANGE the research, and the
standing protocol is explicit: *scratch saves SAVE4/SAVE5 only,
RELOADED, never continued*. Loading a save needs a drive through the
GAME menu's Load dialog, and **there is no such driver in the tree** —
`screens/game_menu/nodes.py` classifies the dialog and names the slot
rows, but nothing assembles the chain.

Building it is its own piece of work and the Load dialog is precisely
where a wrong field loads a game (decision 59's own hazard, and the
reason the galaxy map stopped parking under the overlay). Doing the
commits on Data's continued game instead is what the protocol forbids,
and the evidence would not be reproducible anyway.

**Parked with the exact next step**, not skipped.

## Part D — as first written — **BLOCKED, parked** — except one item, which is DONE

Five items on the list. Four need the port. The fifth does not:

> *The galaxy map does not park while 36 or 53 is up.*

**Done and committed** (`f172a09`), with a discriminating counter-test:
the guard widened to admit 36 and 53 — which the neighbouring screen-8
check survives on purpose — makes the new check and only the new check
go red. 249 -> 250 checks.

## Part E — the rest of select mode — **PART C's OFFLINE HALF DONE, the rest parked**

The order's scope choice for part E is "131 parts B and C, the 128
crash case, and one bounded attempt at open fix 26". What was reachable
this session is 131 part C's OFFLINE half, and it was a real gap rather
than a formality.

### Done: the six "everyone gets everything" fields, and Creative

`Display_Entry_Text_` (tech.cpp:648-706) picks ONE colour for the
current field's name AND its cost, then marks its applications:

* ALL of them when the player is Creative (`traits[TRAIT_CREATIVE]`,
  orion2_consts.h:971) **or** the field is one of the six
  `_starting_tech_field_ids` (techdata.cpp:548);
* otherwise the one whose **NAME** matches the current application's —
  `strcasecmp`, not an id comparison.

**HD did none of the three.** It marked one row, by id, and printed the
cost in its own colour whatever the entry was. All three are
transcribed now:

| | before | now |
|---|---|---|
| the six fields / Creative | one row marked | every row (`researchpanel.marks_every_row`) |
| which row | `app == current[1]` | the NAME, case-folded (`marks_row`) |
| the cost | always `cost` | the current colour when the entry is current |

`ALL_APPLICATIONS_FIELDS` is in `core/researchlist.py` with the other
transcribed tables, and `tools/research_cost_check.py` reads it out of
the source — **out of BOTH of the engine's own copies**, the array and
the six ids `Display_Entry_Text_` writes inline as hex, because a
transcription that agreed with one of them and not the other would be
right about nothing in particular.

Two checks, one of them a rendering: two frames of the same state, one
Creative and one not, on a field that is NOT one of the six, and the
rows below the chosen one must differ. A flag that never reached the
panel would draw the same picture twice — which is 129's own fault one
level up.

### Parked, with the reason measured rather than assumed

**131 part C's LIVE half is unreachable in the scratch saves.** The six
fields are the STARTING technology fields, and both scratch saves have
all six at status 3 — researched. Read live, 22 September:

```
the six starting fields: 29:3, 55:3, 22:3, 57:3, 28:3, 23:3
```

So the case needs a NEW GAME, which is the select-mode path.

**131 part B, and the select-mode path with it.** Reaching SELECT mode
means ending a turn and dismissing the completion dialog, and open fix
26 is exactly about that configuration: with a client connected and the
dialog dismissed by an INJECTED click, the list commits a row by itself
about a second and a half later. Data's own counter-test (19 September,
real mouse, no client) shows the list waits. **The one variable that
makes select mode usable is a real mouse in the orion2re window, which
an unattended session does not have.** So 131 part B's third live
choice and its missing resolutions stay parked — and change mode's
resolutions, which do NOT need select mode, were done instead (part D,
all four).

**The 128 crash case** needs a list with an EMPTY category, which
neither scratch save offers: change mode on SAVE4 and SAVE5 offers all
eight. `research_hd.py crash` still exists and says so when it is run
where the case is unreachable.

**Open fix 26's bounded attempt** was not spent. The order gives it one
attempt at "the separation of variables and the reading of the injected
click path", and the separation is the half that decides: the
"connected and silent" run needs the dialog dismissed WITHOUT the
client, which the order itself says may be impossible from a tool and
is then Data's run. It is. The reading alone would be a theory with no
measurement to hold it against, and the order's own instruction is to
park rather than let it hold up the rest.


---

## Commits

| | |
|---|---|
| `6ab5de7` | the brief, the progress file, the parked file, the index row — and the two findings that shaped the run |
| `f172a09` | the one item of part D that does not need the port: the galaxy map does not park at 36 or 53 |
| `ec6e0c4` | work order closed at the block, with the ground for the next run |
| `06aca9a` | part A: three offsets get their second source, and the RP deviation goes |
| `0bcef38` | part A written up, and part B's seam measured before it is cut |
| `777a4de` | part B, the seam: the geometry is one module, two modes |
| `02ce4b3` | part B: the panel is one class with two configurations |
| `742a8e3` | part B: change mode exists — screen 36 is an HD screen |
| `889f7dc` | part B: the galaxy map's research window opens change mode |
| `29225db` | a check that asked a file list went green by absence, so it asks the class |
| `1aa80b3` | part D found it: the research screen had been falling back since 142 B |
| `f8d259a` | part D: what the live run proved, and why its last item was parked |
| — | **PUSHED here**, `57e3eda..f8d259a`, after the fresh-clone verification |
| `100b320` | part D needs a load driver, so the Load dialog got one |
| `6462bfb` | part D is closed: open fix 25's commit path covers change mode |
| `2293ace` | part C: the description box, and the popup it found under the panel |
| `49d9210` | part C: the category list popup, checked against the engine's own |
| `ac5ce9a` | part E: the current field's second colour was wrong in three ways |

## What the next session does first

**Nothing in this order that a session can reach on its own.** Parts A
to D are done, part C is done, and what is left of part E is parked in
`165-parked-for-data.md` §0c with the reading that makes each one
unreachable rather than merely undone:

* 131 part B and part C's live half need SELECT mode, and select mode
  needs a real mouse in the orion2re window while open fix 26 is open;
* the 128 crash case needs a list with an empty category, and neither
  scratch save has one;
* `hyper_advanced_tech` @640 needs a game that has reached a
  hyper-advanced field;
* open fix 26's own bounded attempt is unspent, and its deciding half
  is Data's run.

If Data hands over one of those states, the tools are in the tree:
`tools/gameload.py` for the slot, `tools/research_change_hd.py` for
change mode, `tools/research_hd.py` for select mode.
