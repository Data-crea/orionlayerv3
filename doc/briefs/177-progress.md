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
