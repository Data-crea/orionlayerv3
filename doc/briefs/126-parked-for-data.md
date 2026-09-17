# Work order 126 — parked for Data

Every question this run met that is Data's to decide. Each item says what
it is, why it is Data's, the options with their cost, and what was done
meanwhile, so it can be answered in one line. Written as the run goes;
the closing state of this list is stated at the end.

## 1. Split the smoke test's `main()` into groups? (part C)

**What:** `tools/smoke_test.py` is ~16,400 lines, almost all ONE function.
Thirty runs today: 30 of 30 exit 0, peak resident memory 4540–4836 MB,
66.6–68.1 s each on this machine (not ~10 s as the order assumed). Locals of
one function live until it returns, which is the likely reason memory only
grows. **Why yours:** a 16,000-line refactor with no behaviour change, whose
time argument the order had dropped; the numbers above partly revive it.
**Options:** (a) leave it — costs ~4.8 GB per run and one exception still
aborts every later check; (b) split into group functions called from `main()`
with a per-group try/report — one careful order, frees memory per group, the
count must stay 195; (c) split AND allow running a group alone for iteration,
the full suite still before every commit (decision 31) — (b) plus a CLI.
**Meanwhile:** nothing split; quiet mode and the memory line are in.
**Answer in one line:** a / b / c.

## 2. Two brief texts are still missing from `doc/briefs/` (part E)

**What:** the beginning of brief 90 (the pop-move brief starts mid-sentence
inside section 1) and work order 125 (the GAME menu order that abcbab0 and
the status document cite; no file). **Why yours:** the texts exist only on
the chat side; nothing in the tree can rebuild them. **Options:** (a) paste
both and a session files them byte for byte — minutes; (b) declare them lost
and let the README row for 90 and a new row for 125 say so — nothing else
changes. **Meanwhile:** 126 was numbered after 125, so 125 stays reserved.
**Answer in one line:** a / b.

## 3. Screen id 6 is Select Race in OrionLayer AND the Races screen in the game (part G)

**What:** `SCREEN_RACE` (6) is the Races/diplomacy screen (mox2.cpp:61-63,
set by the map's RACES button, mainscr_main.cpp:666). Our own
`ext_screen_id.patch` makes race SELECTION report 6 too, and `select_race`
claims 6. So the HD galaxy map's RACES button (field 14, hotkey r) should put
HD Select Race over the Races screen, with its clicks landing in diplomacy —
a source reading, checked in three files, NOT seen live. Also: the stock-race
Accept leaves 6 set (racesel.cpp:451). Open fix 22 describes a patch.
**Why yours:** a change to our patch in Joes' tree, or a routing rule in HD.
**Options:** (a) open fix 22 — Select Race reports a synthetic 51, restored on
the stock accept; four OrionLayer ids change and Custom Race's 50 -> 6 hop is
re-measured live; (b) no patch — HD tells the two apart by `previous_screen`
(0 on the Races screen) and the field-list shape; needs a dispatcher rule it
does not have; (c) until either: the HD map does not send RACES (falls back
to the framebuffer) — one line, loses nothing that works today.
**Meanwhile:** nothing changed in code; open fix 22 filed as DESCRIBED, NOT
APPLIED; `doc/races_screen_reading.md` §4-5. **Answer:** a / b / c (c can go
with a or b).

## 4. The galaxy map may park INTO the turn-start research prompt (part G)

**What:** the map sends `ACTIVATE_FIELD 9` whenever the game reports screen 0
and is not fully zoomed out (decision 59's guard). The research prompt at
turn start runs under screen 0 (mainscr2.cpp:119 then report.cpp), and there
field 9 is a choice row; the commit reads the POINTER's entry, not the field
(tech.cpp:354-369), and with the pointer over no entry dereferences null
(tech.cpp:367, per the reading). Source reading, not observed; at turn start
the map is normally already zoomed out. **Why yours:** it changes when HD may
park, and a fix wants a live check. **Options:** (a) park only while the
field list matches the map's own shape — cheap, the same rule decision 59
states for update(); (b) leave it until the research screen is built and
measure then. **Meanwhile:** nothing changed; `doc/tech_change_reading.md`.
**Answer:** a / b.

## 5. DRAFT rule, not filed: a screen built before its frame hangs from ONE provisional content box (part G)

**The draft as chat worded it:** a screen built before its frame exists hangs
everything from one provisional content-area box, so the frame, when it
comes, moves one box and not a hundred (the colony list's stale columns;
decision 3). **What the four readings say:** colony view — does NOT fit (a
full-bleed landscape with building anchors past the canvas, under its own
top-band art); build queue — does NOT fit (one frame with six fixed holes);
research — fits in change mode (every position offset from `_g_scrn_x`),
select mode moves the panel 81 px; fleet — fits as one box (13,52)-(628,465)
but is four panels divided by the art; races — fits only as the whole native
screen, with uneven per-slot tables. **Why yours:** a rule for the fundament.
**Options:** (a) file it as worded; (b) file it with the exception "unless
the original's screen is itself one frame with fixed holes" (colony, queue);
(c) do not file. **Meanwhile:** nothing filed. **Answer:** a / b / c.

## 6. `core/structs/ship.py` `weapons()` skips empty slots; the fleet screen stops at the first (part G)

**What:** `flt2.cpp:696-701` breaks the weapon list at the first slot with
`type < 0 || count < 1`; `weapons()` returns every slot with `count > 0` and its
docstring cites the fleet screen for that. They differ only for a design with
a gap between used slots. **Why yours:** which reading HD transcribes (the
Planets panel's monster values use it). **Options:** (a) transcribe the stop
and fix the docstring — one check; (b) keep skipping, marked DEVIATION.
**Meanwhile:** unchanged; `doc/fleet_screen_reading.md`. **Answer:** a / b.

## 7. The per-screen questions of the four readings (part G)

Each reading ends with its own list, every question answerable in a line:
`doc/colony_screen_reading.md` §8 (14), `doc/tech_change_reading.md` (12),
`doc/fleet_screen_reading.md` (17), `doc/races_screen_reading.md` §8 (15).
They are not copied here — one home. **Meanwhile:** nothing built.

## 8. Work order 127 Stop 1 — the report, and Data's four decisions (part H)

**What:** Stop 1 done as written, no file in the tree changed. The report is
outside the tree: `~/orionlayer-fixtures/evidence/work_order_126/H_reading_budget_stop1.md`.
Headlines: the mandatory reading is CLAUDE.md + the fundament, 195,162 bytes
(the status document is not ordered read; with it, 752,296); 26 document reads
in 20 checks, all in `tools/smoke_test.py`; a ceiling of 80 KB proposed
(60 KB only with one-sentence entries, which lose weight); the threshold
principle cannot be shortened (388 B against 396 B); decision 38 is five rules.
**One finding checked by hand:** the decision-28 check (smoke_test.py:10284-10289)
asserts "decision 28" and "DEVIATION" anywhere in the whole fundament, and
decision 28's exception paragraph carries neither word — it passes on text
from other entries, i.e. asserts nothing today. Not fixed (127 Stop 2 part 1
re-proves every document check).
**Why yours:** Stop 1 ends in Data's decisions. **Options, one line each:**
the budget figure (80 KB / 60 KB / other); the two kernel samples acceptable
(yes / no); archive granularity (per work order / per month / one file); the
text-share warning threshold (the report proposes a figure).
**Meanwhile:** nothing of Stop 2.

