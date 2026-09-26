# Work order 177 — progress

Unattended run, 26 September 2026. Invisible modals on the galaxy map, the
safety net, Select Race's way back, the main menu's Load dialog, the start
deadline; live tests; push. Evidence root:
`~/orionlayer-fixtures/evidence/work_order_177/`.

## E. The start deadline — **DONE (both: raised AND named)**

`tools/engine_start.py`: the deadline is `START_DEADLINE = 150` s (was
60 s since 174) — the original's logo and intro sequence, which plays
whenever no key or button is down at start (`JIM::Draw_Logos_`,
jim.cpp:18-120), takes 112.9 s every time (11 of 82 starts in 176). While
the log stands at "mox2: data space allocated" WITHOUT the hang's signature
the tool now prints "INTRO: the original's logos and intro are playing" and
keeps waiting, so an intro is neither a timeout nor mistaken for open fix
31's hang. 006e holds the deadline above the intro and the CLI default to
it. (176's parked item 6.)

## A. Every modal the galaxy map can show — INVENTORY (orion2re source)

Read from `~/orion2re/src/game/` (file:line there) and the player's English
LBX string tables; nothing run. **None of the texts below is on the wire**
— a client gets each modal's field rectangles, types and hotkeys (and the
raw structs), never the prompt, the box text or the text being typed. All
report screen 0 unless noted.

| # | modal | trigger | recognisable by (live fields after slot 0) | input | text source | HD in 177 |
|---|---|---|---|---|---|---|
| 1 | **Enter Home Star Name** | `Main_Screen_` at stardate 35000, once (mainscr_main.cpp:351-357) | 2: ACCEPT button t0 hk0 (227,246)-(324,273); input t11 hk0 at (165,200) | type (ASCII), Backspace (first clears all), Enter/ACCEPT commits, ESC restores | HESTR 0x101; the prefilled name = the home star's (`home_planet_id` → planet → star) | **HD view** (B) |
| 2 | Enter Star Name after colonising | a planet picked in #3, star unnamed by the player, animations off (mainpups.cpp:757-763) | same shape at origin (177,125): button (273,225), input (211,179) | as #1 | HESTR 0x100; the star not identifiable from the list | safety net (C) |
| 3 | **Planet selection** — colony ship / **colony base** (174's questions) / outpost | reports phase, `REPORT::Colonization_` (report.cpp:152-293); one round per base | ESC button t0 (410,340)-(476,362); title strip t7 (147,104)+0x2F; a t7 square per planet / ship; last (0,0,639,479) t7 hk0 | click a planet; ESC cancels | ESTRINGS 0x1cd/0x1ce/0x1cb/0x1cf + star name | safety net (C); HD view parked |
| 4 | "Build colony on %s with …" | a planet clicked in #3 | CONFIRMATION (gamebox) | Y / N | ESTRINGS 0xd1 + computed lines | **HD** (crop in a popup block) |
| 5 | "Colonize / outpost the preselected planet of %s?" | auto-colonisation target | CONFIRMATION | Y / N | RSTRING0 175/176 | **HD** (crop) |
| 6 | "Really trash your colony base for %d BC?" | #3 cancelled with a base | CONFIRMATION | Y / N | RSTRING0 174 | **HD** (crop) |
| 7 | New leader for hire | `officer_for_hire` (report.cpp:482-505) | Reject t0 hk'R' (211,333), Hire t0 hk'H' (342,333), skill rows | Hire / Reject | MAINPUPS.LBX 0x30-0x32 | safety net; HD view parked |
| 8 | Leader level / marooned leader | reports | 1: (0,0,639,479) t7 **hk0** | any click | MAINPUPS.LBX 0x33 | safety net |
| 9 | "Scouts arrive at the %s system" | `just_visited` (report.cpp:589-618) | t7 planet/ship fields + (0,0,639,479) hk0, no ESC button | any click | ESTRINGS 0x1c8 + star | safety net |
| 10 | Text box (spy reports, F-key messages, help, errors …) | many | 1: (0,0,639,479) t7 hk **0x1B**; TEXTBOX.LBX at x=84, variable height | any key or click | varies (HESTRNGS, RSTRING0) | safety net (the WARNING crop would be the wrong rectangle) |
| 11 | Warning box (`User_Box_` type 3) | movement errors, no freighters … | same fields as #10; WARNING.LBX at (154,144) | any | HESTR 0x20-0x24, 0xDF, 0xE6 | safety net (indistinguishable from #10) |
| 12 | Confirmations on the map | Attack Antares, fleet without navigator | CONFIRMATION | Y / N | HESTR 0xE4/0xE5; a literal | **HD** (crop) |
| 13 | Tax rate popup | the treasury window | ACCEPT t0 + six t3 multi-buttons at y 0xC6 | a rate, ACCEPT | MAINPUPS.LBX 0x3E-0x45 | safety net |
| 14 | GNN, NPC diplomacy, Antaran room | reports | full screen, 1: (0,0,639,479) t7 hk0 | any click; diplomacy offers lists | EVENTS/jimtext/antarmsg | safety net |
| 15 | Science room / Select research | reports | report 52 / 53 (open fix 24) | — | — | own HD screens already |
| 16 | System box / fleet box | map clicks | the map's own list plus the box's fields | — | — | own HD drawing already |

**Screens reached from the map** (their own ids, not modals): next turn 12,
reports 39 (sets 0 at once), turn summary 40, colony 1, colony landing 33,
diplomacy system view 6, GAME 8, FLEET 4, colony summary 20, INFO 9, RACE
6, planets 32, officers 29, tech change 36, scrap freighters 35, command
points 43, distance 28, colonize/outpost/transport 30/31/34 (which reuse
#3's popup).

**Found on the way:** `core/gamebox`'s WARNING shape (one full-screen field,
hotkey ESC) is also every TEXTBOX text box's (textbox.cpp:249), whose
picture is 380 wide at x=84 with a height from its text — the fixed WARNING
crop `fltbox` draws is the wrong rectangle for those (parked item 2). On the
galaxy map that shape goes to the safety net.

**Typing into the game** (the home star name): INJECT_KEY pushes an SDL key
with the code as key and scancode (ext_api.cpp:770-779); the game reads
ASCII for printable keys (send 0x41 for 'A'), 0x08 Backspace, 0x0D Enter,
0x1B ESC (platform.cpp:412-500). **Commit only with Enter** (or a real click
on ACCEPT): ACTIVATE_FIELD returns early past `Copy_Continuous_String_`
(fields.cpp:172-183) and the typed text is lost. The first Backspace clears
the whole prefilled name, a first printable key appends (fields.cpp:1171-
1227); at most 14 characters and the field's pixel width.

**Found live (not in the source reading above):** the turn summary after
TURN reports screen **0**, not 40 — 10 fields: two t-1001 scroll arrows at
(441,95)/(441,353), five t7 text rows 307x9 from (92,103), CLOSE t0 hk ESC
(242,374), the window (84,51) and the full screen, both hk ESC. The net takes
it (no HD view; parked item 4).

## B. The modals HD draws — **DONE**

`screens/galaxy_map/mapmodal.py` (new), routed from the map's `render`,
`handle_click`, `handle_key_event` and `handle_right_button`:

- **#1 the home star name**: recognised by its exact two fields; a HUD
  popup with the prompt (HESTR 0x101, from the player's own strings), a
  dense panel with the name being typed, a blinking cursor and ACCEPT.
  Prefilled with the home star's name. Typing follows the field's own rules
  (the first Backspace clears the prefilled name, '_' refused, 14
  characters) and every key goes to the game as its ASCII code; ACCEPT and
  Enter send **Enter**, never ACTIVATE_FIELD (which would drop the typed
  text, fields.cpp:172-183). The typed text is not on the wire: HD keeps a
  mirror (HD STATE `typed_name_mirror`), the game's result arrives as
  `star.name` with the next snapshot.
- **#4, #5, #6, #12 the confirmations**: the game's own box pixels (their
  text is not on the wire, open fix 29) cropped into a HUD popup, YES / NO
  over the game's own buttons (`fltbox`'s placement), answered by click and
  by Y / N.
- Data not on the wire (the prompts, the box texts, the typed text): no new
  patch was needed for B — the prompts come from the player's LBX strings,
  the confirmations are shown as the game's pixels, and the typed text is
  mirrored. Open fix 29 (box texts) stays the entry for a text-drawn box.

## C. The safety net — **DONE** (DEVIATION `modal_fallback`)

`core/modalnet.py` (new): a screen names its OWN field list and the modals
it draws itself; any other list under its game screen id, once it has stood
`SETTLE` = 5 snapshots (the no-glimpse rule of 166 A), makes
`wants_original()` true — the window shows the game's own picture, clicks go
through the existing fallback, and **keys** now too (`OriginalView.key_code`
/ `forward_key`, routed in main.py's KEYDOWN branch while the game's picture
is shown: printable characters as ASCII, Backspace, Tab, Enter, ESC,
Delete). One log line per unknown shape (`modalnet: <screen>: a modal HD has
no view for … (<n> fields: type/hotkey/size@position …)`). Used by the
galaxy map (0), the main menu (10) and — found live — Select Race (51),
whose ruler-name popup and banner screen a reconnecting client drew the
race grid over; its own list is the one with radio buttons (racesel.cpp:203,
:312, :343).

## D. Select Race's way back, the main menu's Load dialog — **DONE**

- **Select Race**: ESC and a new **BACK** frame button (HD EXTENSION
  `back_button`) send the list's own ESC hot-key field (racesel.cpp:195-199,
  :355-364) — the original's way back; nothing is sent when the list has none
  (multiplayer). The old `inject_click(162, 445)` (no field there, 174) is
  gone.
- **The main menu's Load dialog** runs under screen 10 with the GAME popup's
  Load fields, but `SerializeSaveSlots` sends slots only on SCREEN_GAME:
  **open fix 34** (`doc/ext_main_menu_save_slots.patch`, NOT APPLIED; entry
  34 in `doc/orion2re_open_fixes.md`, dry-run and syntax check OK). With the
  slots on the wire the GAME menu overlay draws the dialog over screen 10
  (`ALSO_OVER_IDS`); **until then the safety net shows the game's own dialog**
  with its list and LOAD / CANCEL working — that is what ran live.

## Checks — 338 → 344 (fast 328 → 334)

090g (core): the net's rule and its log line; the keys' codes, main.py's
routing, an overlay over a second id. 090h (galaxy_map): the home star
typing, ACCEPT = Enter, four sizes; the confirmation by click and key; the
own list kept, planet selection and a text box to the net. 090i
(select_race): ESC and BACK send the ESC field, nothing without it; the
ruler's name and the banners to the net. 090j (main_menu): the Load dialog
to the net without slots, to the overlay with them. 006e gained the
`--blanked-ok` asserts; 017 lists the three newly marked files.

## Live — own engine, liveguard before and after

The screen was **blanked the whole run** (idle 30 min at the first start):
`engine_start` refused. Its refusal predates open fix 31 (applied in 175, 82
starts without a hang), so it gained **`--blanked-ok`** — default unchanged,
the start prints "BLANKED SCREEN ACCEPTED", the foreign-engine and port
refusals stay. All three starts came up through the intro (READY after
~113 s). Engines: PID 423109, 424116, 426030 — all started here.

Guards: `~/orionlayer-fixtures/live_guard/177_master` (before the first
start), `177_run2`, `177_run3`. **Final verify against 177_master: every
game file identical** (the only difference reported is the tree's git status,
this run's own uncommitted code, since committed). Scratch slot: **SAVE4**
(loaded three times, never saved). SAVE10 (the autosave) was rewritten twice
— by the game's own quit (below) and by the new game + TURN — and restored
from the guard both times; MOX.SET restored twice. SAVE8 never touched.

**A mistake, stated:** to get back to the main menu I sent the GAME menu's
`Q` and confirmed — that is QUIT GAME, not "to the main menu": the engine
exited and saved the autosave. SIGTERM during its shutdown did nothing in
10 s, so it (ours, PID 423109) got SIGKILL. SAVE10 was restored from
177_master and verified identical before the next start.

## Results

Evidence root `~/orionlayer-fixtures/evidence/work_order_177/`; every
picture is a `_hd.png` with its `_native.png` from the same snapshot. The
drivers used (`probe.py`, `turn177.py`) are beside them.

| # | step | result | evidence |
|---|---|---|---|
| 1 | A: every modal of the map from the source, with what it shows, takes and whether HD draws it | done | this file, part A |
| 2 | B: home star name — HD popup, typing, ACCEPT = Enter | done | 090h |
| 3 | B: confirmations drawn and answered in HD | done | 090h |
| 4 | C: safety net + keys + one log line | done | 090g, 090h, 090j, 090i |
| 5 | D: Select Race way back (ESC, BACK) | done | 090i |
| 6 | D: main menu Load dialog (net now; overlay with open fix 34) | done; fix 34 not applied | 090j, `doc/ext_main_menu_save_slots.patch` |
| 7 | E: start deadline 150 s, the intro named | done | 006e; every start this run printed INTRO then READY |
| 8 | live: main menu → CONTINUE → home star dialog in HD, prefilled "Mentar" (1920) | works | `continue_and_load_1920/001_LIVE_1920x1080_continue_home_star_dialog_*` |
| 9 | live: rename to "Nova" by typing, ACCEPT click → "Nova" on the wire and on the map (1920) | works | `continue_and_load_1920/001_…_home_star_typed_*`, `002_…_home_star_renamed_*` |
| 10 | live: CONTINUE, accept unchanged with Enter → "Mentar" kept (2576) | works | `home_star_2576/001_*`, `002_…_accepted_unchanged_*` |
| 11 | live: new game (GAME → NEW) → home star "Sol" → typed "Vega", ACCEPT → "Vega" (2576) | works (mirror caveat after reconnect: parked 5) | `new_game_home_star/*` |
| 12 | live: TURN on SAVE4 — colony-base planet selection through the net, "Build colony on Malus II" drawn in HD, YES (1920; the first pass answered NO six times, each drawn) | works | `turn_modals_1920x1080/*_net_8fields_*`, `*_confirmation_hd_drawn_*` |
| 13 | live: TURN on SAVE4 — ESC → "Really trash your colony base for 100BC?" in HD, NO → selection → square → YES; landing (33) and colony (1) through the fallback; turn summary through the net, ESC → HD map (2576) | works | `turn_modals_2576x1432/001…008_*`, `record_LIVE_2576x1432.json` |
| 14 | live: an unknown modal through the net WITH KEYS — the ruler-name popup: Backspace + "Tester" typed from HD, Enter | works (found and fixed live: Select Race drew its grid over it) | `new_game/001_…_reconnect_in_leader_name_*`, `net_keys/*` |
| 15 | live: the net's mouse — a banner clicked through it → the game started | works | `net_mouse/001_*` |
| 16 | live: Select Race BACK button (1920) and ESC (2576) → New Game | works | `select_race_back/*` |
| 17 | live: main menu Load dialog — listed (net), CANCEL (1920 and 2576), row 4 → SAVE4 loaded, stardate 3509.0 (2576) | works | `continue_and_load_1920/001_…_mm_load_*`, `main_menu_load/*` |
| 18 | liveguard: all game files identical to `177_master` after the run | clean (scratch SAVE4 loaded, never written; SAVE10/MOX.SET restored) | `live_guard/177_master`, `177_run2`, `177_run3` |
