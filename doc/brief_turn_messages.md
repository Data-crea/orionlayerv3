# The turn-change messages — inventory and HD coverage

Work order 188, Part 4 ("Turn-change messages in HD"). Every box and message
that can appear when the player ends a turn, read from the orion2re source
(`src/game`, `orionlayer-local`), with the screen id it reports, what it
shows, its buttons and where each leads — and how HD draws it since this
work order. The full source reading with every line reference is kept in the
evidence (`~/orionlayer-fixtures/evidence/work_order_188/readings/
turn_messages_reading.md`); this file is the brief the building follows.

## How a turn runs, and what the wire says

1. **TURN** (`MAINSCR::Do_Next_Turn_`, mainscr.cpp:2678) sets
   `_current_screen` 12 and the return screen 39.
2. **Processing (12)**: `NEXTTURN::Next_Turn_Calc_` (nextturn.cpp:91-166)
   mostly QUEUES (messages, reports, events). It DRAWS only in the battles
   (`COMBFIND::Search_For_Battles_`, :123) and the council (:147). The
   bombing report and ground combat switch the reported id to 39 for the
   rest of processing (colbomb.cpp:18, colgcbt.cpp:271).
3. **Reports (39 for one tick, then 0)**: `MAINSCR2::Reports_Screen_`
   (mainscr2.cpp:115-118) runs the fixed chain of `REPORT::
   Display_Report_Aux_` (report.cpp:296-325) under SCREEN_MAIN: Antarans,
   GNN, research, evolution, leader for hire, colonisation, discovery,
   leader level, spy reports, AI audiences, Turn Summary, empty build queue,
   occupation policy.

**The id problem** (before work order 188): every report-phase popup
reported 0, so a client could not tell a leader offer from the galaxy map,
and the Turn Summary reported 40 for one tick only (turnsum.cpp:90).
**Open fix 49** ("TPOP", applied in this order) gives each popup its own id
and sends what it shows; **open fix 29** ("MSGB") sends every generic box's
text.

## The inventory

HD column: **box** = the HD message box (`core/msgbox.py`, open fix 29);
**popup** = the HD turn popup (`core/turnpopup.py`, open fix 49);
**screen** = an existing HD screen; **notice** = the Stage 1 F12 notice
(`core/f12notice.py`) — the picture only on F12, parked.

| # | Item | Function | Id on the wire | Shows | Buttons → where | HD |
|---|---|---|---|---|---|---|
| 1 | Player attacked | `MAINPUPS::Player_Attacked_Popup_` mainpups.cpp:482 | 12 | ESTRINGS 0x30/0x31 with attacker, defender, place | click anywhere → the battle | box (warning) |
| 2 | Combat target at a star | `MAINPUPS::Defense_Colony_Selection_Popup_` mainpups.cpp:544 | **64** (fix 49) | the star's system: planets, ships; title ESTRINGS 0x45 | a colony / a ship's owner → attack (then #3 if a treaty); CLOSE → no attack | popup |
| 3 | Treaty "really risk war?" | `COMBFIND::Human_Confirms_Attack_` combfind.cpp:1272 | 12 | the treaties and the question | YES → attack; NO → back to #2 | box (confirmation) |
| 4 | Sneak-attack audience | `DIP_SCRN::Show_Sneak_Attack_Message_` | 58 | the ambassador | click → on | screen (audience) |
| 5 | Strategic combat result | `COMBAT::Message_Box_Titled_` combat.cpp:927 | 12 | summary title, details | click anywhere → on | box (text, titled) |
| 6 | Tactical combat | `COMBINIT::Tactical_Combat_` | 12 | the combat screen | its own | notice — combat itself is out of this order's scope |
| 7 | Artemis net / ships lost | combinit.cpp:623, combfind.cpp:1722 | 12 | the loss | click → on | box |
| 8 | Invasion / bombard choice | `MAINPUPS::Colony_Selection_Popup_` mainpups.cpp:1121 | 12 | troops, bomb results | invade / bomb / close | notice (parked) |
| 9 | Bombing report | `COLBOMB::Colony_Bombing_Screen_` → Text_Box_ colbomb.cpp:98 | 12 → 39 | title ESTRINGS 0x1F2, lines | click → on | box (text, titled) |
| 10 | Ground combat | `COLGCBT::Colony_Combat_Screen_` colgcbt.cpp:165 | 12 → 39 | the animated fight | click → on | notice (parked) |
| 11 | Captured technology | `SCIENCE::Show_Off_Captured_Tech_` | 52 | the science room | click → next / ESC → close | popup (science) |
| 12 | Loknar rescued / flics | `OFFICER::Rescued_Loknar_Popup_` | 12 | a message | click → on | box; the flics notice |
| 13 | Monster bribe | `MAINPUPS::Dragon_New_Star_Popup_` mainpups.cpp:431 | 12 | a star choice | star / refuse | notice (parked) |
| 14 | Galactic council | `council::Main_Council_Screen_` council.cpp:101 | 12 | the council, votes | list fields (vote, accept) | notice (parked) |
| 15 | Antaran attack | `ANTAROOM::Main_Antaran_Room_Screen_` | 0 | the Antaran room | click → on | notice (parked) |
| 16 | GNN news | `EVENTS::Drive_Event_Screen_` events.cpp:2540 | **63** (fix 49) | the event's text (`_event_message`), picture EVENTS.LBX | click anywhere → next | popup (gnn) — picture not drawn |
| 16b | Event as a box (GNN off) | `MAINSCR::Mini_Main_Screen_Text_Box_` | 0 | title, event text | click → on | box (text, titled) |
| 17 | Science room (research done) | `SCIENCE::Show_Off_Researched_Tech_` science.cpp:410 | 52 | the discoveries, BILLTEXT footer | click → next entry, ESC → close | popup (science) |
| 18 | SELECT NEW RESEARCH | `TECH::_Tech_Select_` | 53 | the choice list | a row → chosen | screen (research_select) |
| 19 | Evolutionary mutation | `raceopt::Evolutionary_Mutation_Screen_` | 0 | the picks | picks / accept | notice (parked) |
| 20 | Leader for hire | `MAINPUPS::Random_New_Officer_Popup_` mainpups.cpp:784 | **59** (fix 49) | the leader's card, cost, upkeep | REJECT → gone; HIRE → hired (or "too poor") | popup (leader_hire) |
| 21 | Colonisation planet choice | `MAINPUPS::New_Colony_Selection_Popup_` mainpups.cpp:710 | **60** (fix 49) | "Select planet for …", the system | a planet → #22's confirmation; CLOSE → base unused (then "really trash") | popup (planet_choice) |
| 22 | Colony confirmation / "really trash" | `GENDRAW::Do_Confirmation_Box_` report.cpp:179/201/221 | 60 / 0 | "Build colony on …", the planet's numbers | YES → the colony; NO → back | box (confirmation) |
| 23 | Star rename | `namestar::Change_Star_Name_Popup_` | 0 / 33 | a name field | typing, Enter | notice (parked; the map's home-star dialog is HD) |
| 24 | Colony landing | `COLLAND::Colony_Landing_Screen_` colland.cpp:153 | 33 | ESTRINGS 0xE5 with the planet | click → (#23) → the colony screen (1) | popup (landing) — art not drawn |
| 25 | New system explored | `MAINPUPS::New_System_Discovery_Popup_` mainpups.cpp:936 | **61** (fix 49) | the system, its special | click → on | popup (discovery) |
| 26 | Leader gains a level | `OFFICER::Officer_Made_Level_Report_` → `Officer_Gains_Level_Popup_` | **62** (fix 49) | the leader | click → on | popup (leader_level) |
| 27 | Spy reports | `REPORT::Has_Report_` report.cpp:799 | 0 / 52 | "… spy steals …" | click → on | box (text) |
| 28 | AI audience | `DIP_SCRN::Npc_Diplomacy_Screen_` | 58 | the ambassador | statement → on, menu | screen (audience) |
| 29 | Turn Summary | `TURNSUM::Turn_Summary_Popup_` turnsum.cpp:84 | **40** kept (fix 49) | the turn's messages | a colony message → that colony's screen, and back; up / down; CLOSE → on | popup (turn_summary) |
| 30 | Empty build queue | `REPORT::Empty_Colony_Queue_` report.cpp:843 | 1 | the colony screen + "place your orders" box | the colony screen's own | screen (colony) + box |
| 31 | Occupation policy | `REPORT::Need_To_Set_Occupation_Policy_` | 1 / 33 | the colony screen / a popup | its own | screen (colony); the popup notice |
| 32 | Auto-turn stardate banner | `MAINSCR2::Do_Begin_Of_Turn_` mainscr2.cpp:566 | 0 | race and stardate | none | the map (no field to answer) |
| 33 | End of game | nextturn.cpp:47-82 | 12 → 10 | flics, the Hall of Fame | on | notice / Hall of Fame (Part 6) |

## Jumping to a colony (known issue, open fix 33)

Open fix 33 ("The Info screen's Turn Summary never jumps to a colony") is the
INFO screen's path: `Info_Screen_` overwrites the jump with SCREEN_MAIN
(info.cpp:641). The turn-time Turn Summary (#29) calls the same
`MSG_::Goto_Msg_Colony_` but has no such overwrite and sets its own return
screen (turnsum.cpp:176-185, :222-225) — so its jump works: **seen live in
this order**, the row "… finished construction …" opened that colony's
screen (1) and its RETURN came back to the Turn Summary (40). No engine fix
is needed for any turn-time jump; #24, #30 and #31 go straight to the
colony screen and never pass through the Info screen. Open fix 33 stays as
it is (the Info screen, not a turn message).

**One trap found by fix 49's reading**: a Turn Summary row acts on the row
under the POINTER, not on the field it was given (turnsum.cpp:176-179; the
class of open fix 23) — so HD answers a row with an injected click at the
row's own centre, which puts the pointer there (open fix 3), never with an
activation.

## What each HD view sends

Every answer is the popup's or box's own field: activated where the original
compares the returned field (boxes, the science room, the landing, the GNN),
an injected click at the field's centre where it reads the pointer (the Turn
Summary's rows and buttons, the planet and combat choices, the leader
offer). Each answer goes once per state of the popup, and again only once the
game has moved or stood still for 20 snapshots (a refused planet leaves the
popup as it was).
