# Work order 175 — progress

Unattended run, 26 September 2026. Fixes 30 and 31 applied, Leaders
complete, the Races and Info screens, Info's texts moddable, the string
extractor keeps its spaces, and the live-test protocol backs up every
file a run writes. Builds on 167 and 169-174 (decisions 71, 72).

Evidence root: `~/orionlayer-fixtures/evidence/work_order_175/`.

## Precondition — checked at the start

Data's engine is running: orion2re PID 368253 (parent 35660, started
10:03:06), listening on 17362, with Data's own client (`python main.py`,
PID 369007). Neither is connected to nor stopped. Everything that needs
no engine goes ahead; a live step runs only on an engine this run starts,
which the port does not allow while Data's is up.

## The live-test protocol, extended — **DONE** (before anything live)

**What a run can write, found in the source** (not named by an order):
the game writes SAVE1-10 (`Save_Game_`, filedef.cpp:64; SAVE10 is the
autosave TURN writes), `MOX.SET` (`Save_Game_Settings_`, filedef.cpp:24
— after every save, filedef.cpp:82, and when a loaded game is left for
New Game, which is 174's case; loadsave.cpp:1063, initgame.cpp:113),
`HOF.M2` (score.cpp:205, :614), `lastrace.rac` (racesel.cpp:704),
`TEMP.TMP` (swap.cpp:24) — all in the game folder, `fopen_case`, any
case — and a new `logs/game.<pid>.log` beside its binary per process
(main.cpp:66; new files, never Data's). SAVE11 is written by nothing and
held anyway. OrionLayer writes `user_settings.json` (with `.tmp` and
`.corrupt`), F8 screenshots and the mod folder's resize cache (new files
only), and — through the F5 editor only — `boxes.json`, `races.json` and
the colony plates in the tree.

**`tools/liveguard.py`**: `snapshot DIR` copies and hashes every one of
them and records the tree's `git status`; `verify DIR` names every
change (changed, appeared, vanished, the tree), `--restore` puts it back
and re-hashes, `--allow SAVE4.GAM` exempts the scratch slot a run saves
to. **`tools/engine_start.py` takes the snapshot before the engine
exists** (a new folder under `~/orionlayer-fixtures/live_guard/`, or
`--guard DIR`) and prints the verify command. Check 006e (321): a run's
changes in a scratch game folder — SAVE10 rewritten, `mox.set` (lower
case) rewritten, `TEMP.TMP` appeared, `HOF.M2` vanished, the settings
written, the allowed scratch slot saved — all named, all restored, the
scratch slot left. Recorded in CLAUDE.md beside the protocol and in
fundament part 09 beside the start hang.

## The string extractor keeps its spaces — **DONE** (167's parked X)

`tools/estrings_extract.decode` (also `hestrings_extract`'s) called
`.strip()`. Measured on the raw bytes of the player's files
(`extractor/strings_losing_spaces.json`): **96 ESTRINGS and 32 HESTRNGS
entries** lost a leading or trailing space or a trailing line break —
`", the "` (0x110, 0x182), `"%s Fleet: "` (0x131), `"  no"` (0x10A),
`"Beam OCV: "` (0x99), the GAME menu's engine-row labels (0xAA...),
`" %s gains a level"` and the other ESTRINGS messages, and the long
lore texts' trailing `\n\n`. The docstring had promised the bytes all
along; the decode now keeps them. Both loaders are **format 2**, so a
stripped file reads as stale and `setup.py` names the command. Re-
extracted on this disk; the committed stand-ins regenerated
(`tools/make_derived_fixtures.py`). The Leaders workaround
(`ldrrows.the_word`, and its `workaround_the_word` marking) is removed:
the word is the file's own string.

**Before/after**: `extractor/strings_before_after.png` — each affected
string as a screen composes it (Leaders' title and cost column, the
galaxy map's fleet box, a Fleets ship value, a GAME menu settings row,
a Leaders message): "Slith, theRebel Pilot" -> "Slith, the Rebel Pilot",
"Kif Fleet:3 ships" -> "Kif Fleet: 3 ships". The six screens that use
the strings rendered offline before and after (`extractor/before`,
`after`) are pixel-identical: offline states draw none of these strings
(no leader rows, no fleet box, no ship values) — the live test is where
they show in place. Check (322): the decode keeps spaces and line
breaks, a synthetic block walks with them, format-1 files are stale,
the workaround is gone.

## A. Fixes 30 and 31 applied — **DONE (applied, built); the re-measure waits for the port**

Both on orion2re `orionlayer-local`, one commit each, from the patch files
under `doc/` exactly as they stood:

| Fix | orion2re commit | What | OrionLayer record |
|---|---|---|---|
| 31 | `f98b8547` | `platform.cpp`: present without VSync when `ORION2RE_NO_VSYNC=1` | `64bb4ec` |
| 30 | `cc542e02` | `ext_api.cpp`: the OFFS block after FSEL while screen 29 is up | `9cfa50e` |

Rebuilt with `ninja -C out/build/Linux/linux-debug` (binary 10:30:47);
Data's running engine was not touched (a rebuilt file on disk does not
change a running process). Bundle `~/orion2re_bundle_26sep_cc542e02.bundle`
(`--all`, verified, 21 refs), beside the others in `~/`. Nothing went
online. `doc/orion2re_open_fixes.md` rows and sections 30 and 31 say
**Applied** with commit and date; both patch headers say
`STATUS: APPLIED`; `tools/version_check.py` requires both markers; the
smoke group holds all three and, where the tree is on disk, the marker in
the source and a clean `patch -R --dry-run` (006e, 090c).

**Fix 31's re-measure (many starts, tearing on the galaxy map and in a
scrolling list) is NOT DONE** — it needs an engine this run starts, and
the Extension API's port is fixed (`ext_api.h:11`, `Init(uint16_t port =
17362)`), held all run by Data's engine (PID 368253). Parked with the
exact steps (parked item 1).

## B. Leaders complete — **DONE offline; live test parked (port)**

What 167 left dead, now wired to the OFFS block (`screens/leaders/`):

- **POOL, DISMISS, PREV / NEXT, the scroll arrows** go to their live
  fields whenever the block is on the wire (they were refused without the
  mode). The original decides what they do in each mode
  (officer.cpp:961-1134); HD sends and reads the answer back.
- **Assigning** (officer.cpp:1383-1462, :986-1086): select a leader, then
  a star with the player's colony (colony view) or a combat ship's big
  icon (ship view) — or the other order. New `ldrmap`: a star's field is
  `Add_Galaxy_Map_Fields_2_`'s `(sx-3, sy-3, sx+8, sy+9)` at
  `Get_Galaxy_Map_Star_XY_`'s point; a stack icon's field is the hidden
  field at the icon's own x/y; a big icon's `(x, y, x+0x39, y+0x39)`.
  Only in mode -1 and in the view where the loop acts; a star without the
  player's colony is not sent (the game ignores it). A right click on a
  big icon asks the game for its ship view (shown as the fallback).
- **The top-right box** shows what the game shows: the colony view's
  `_officer_star_displayed` (its name, each planet in orbit order as the
  colony screens' disc with its name; OMISSION `system_pictures`: the
  star picture and orbits), the ship view's stack in the block's display
  order with its scroll bar. The placeholder naming open fix 30 is gone
  (090d checks nothing drawn says it, and the code has no PLACEHOLDER).
- **The box under PREV/NEXT** (167 A: `officer.cpp:810-826`, `:695-727`):
  the displayed star with its leader ("%s (%s)", HESTR 0x92/0x93 while on
  the way), or in the ship view the big icon under the pointer.
- **The box above HIRE** (the strip under the map, 167 A:
  `Print_Galmap_Scanned_Ship_`, officer.cpp:2094-2204, and
  `Do_Officer_Screen_Stuff_`, movebox.cpp:229-291): the star under the
  pointer (or HESTR 0x94 "unexplored") or the stack — "%s Fleet: ", the
  outpost/transport/colony-ship counts and the hulls, one hull by
  `_hull_data[i].name`, more by `.size_name`. The plurals were not
  extracted: `core/shipparts` format 2 adds `hull_plurals` (TECHNAME
  strings 551-559, techinit.cpp:147-157); re-extracted here, stand-ins
  regenerated. The stack's ships are `Find_Ship_Stacks_`'s rule over the
  FSEL node table's head ship (`next_node` is not on the wire).
  Monster stacks print a race name that is not on the wire: OMISSION
  `map_strip_monsters`.
- **HD's pointer** (TRANSCRIPTION `pointer`): the loop's `_scanned_*`
  rules applied by HD, since the API has no mouse motion — star boxes
  (0x1E displayed, 0x6E-ramp chosen, 0x71 scanned; unanimated), the
  ship view's stack outlined.
- **Glass everywhere.** Data's near-black boxes and black mini-map: the
  view box and hire mode's panel no longer draw OFFICER.LBX 1/2/17
  (DEVIATION `view_box_glass`), the galaxy box is glass (DEVIATION
  `map_glass`) and 006f's glass check no longer excuses it — every box on
  the screen is a 174 glass panel.

Checks: new `090d` (4 checks: every button in both views to its own
field; map and grid sends; the strips' words and the pointer rules; no
placeholder, no excuse in 006f); 090c's marking list follows the new
marks; 059's loader check reads each loader's own format. 322 -> 326
(fast 316).

Offline evidence, from the reference fixture's own arrays with a made-up
view state (`tools/leaders_offline.py`, which says exactly what is made
up): `evidence/work_order_175/leaders/leaders_{colony,ship}_view_offline_
*_{1920x1080,2560x1440,3840x2160,2576x1432}.png`. No native half: that
needs the live game.

**Live test (every button in both tabs; hire on a scratch save)**:
parked for the port (parked item 2), with `tools/leaders_hd.py run 5`
ready.

## C. Races screen — INVENTORY (from the orion2re source, before building)

The long reading is `doc/races_screen_reading.md` (work order 126 G); it
was re-checked against today's tree and holds, with four corrections
marked **[175]** below. orion2re file:line throughout.

**Screen.** `SCREEN_RACE` = 6 (orion2_consts.h:466), `RACESCRN::Race_Screen_`
(racescrn.cpp:677-1093); entered by the galaxy map's RACES button
(`Add_Irregular_Button_Field_(386,435,453,471,…,"R")`, mainscr.cpp:1398;
mainscr_main.cpp:665-669); left by EXIT / ESC to SCREEN_MAIN after
`Update_Spy_Stuff_` (:857-874). **[175]** 6 no longer clashes with Select
Race (which reports the synthetic 51).

**Modes.** Main; WHO (after AUDIENCE / REPORT / DECLARE WAR / IGNORE,
:1085-1088: the next click on a race runs the action, a click elsewhere
or on the button again cancels, :878-1014, :1058-1066); spy drag
(:1037-1043); network wait box (multiplayer, :593-605).

**Fields.** Main (`Setup_Main_Fields_` :338-373): EXIT button (535,433)
ESC (art RACES 9, 73x18); radios IGNORE (429,444) I, REPORT (429,423) R,
AUDIENCE (334,423) A, DECLARE WAR (334,444) D (arts 6/7/8/60, 87-88 x 17);
only EXIT without an active race. Then (`Setup_Race_Display_Fields_`
:426-457) the agent pool (328,386)-(613,415) and per race the three
mission multi-buttons at `_race_spy_btns` (+0, +76, +149), the spy strip
(sx, sy-6)-(sx+187, sy+25), the relation bar (bx-6, by-6)-(bx+8, by+88),
then the whole-screen catcher (:815): **8 + 5n**. WHO (`Setup_Race_Who_
Fields_` :459-488): one hidden field per race (xo, py)-(xo+319, py+88),
xo 0 / 320, then the catcher: **7 + n**. **[175]** the third mission is
HIDE, not assassination (spy.cpp:407-432; the background art says
ESPIONAGE / SABOTAGE / HIDE).

**Draws.** RACES.LBX 0 background; portraits `race + 32` (76x88) at
`_race_picture` with banner-colour frames (`_banner_color_high/low/edge`
by `s_player.color`, :50-52, :270-279) and the ELIMINATED overlay 31; the
name under the portrait (:140-146); the treaty paragraph in (tx, ty,
182x43): `_treaty_labels[min(treaty,5)]` (ESTRINGS 0x275-0x27B), research
treaty BILLTEXT 0x39 + level + RP/BC, trade 0x3A + level + BC, tribute
0x3B/0x3C with 5 %/10 % (:111-216); NO CONTACT (0x33) for an empty or
uncontacted slot; "(IGNORED)" 0x32 (:569-572); relation bar RACES 3 and
slider 2 at `bar_y + _slider_remap_list[(rel+100)/8] - 6`, the word
0x21-0x31 on hover (:232-312, :563-566); spy icons `myrace + 46` in each
strip and the agent pool, spaced `(w - 28) / (n - 1)` capped at 28
(:57-86, :659-675); SPY / AGENT bonus 0x34 / 0x35 at (417,372) / (519,372)
(`spy::Compute_Spy_Bonuses_`, spy.cpp:35-81).

**Lists.** Portraits and texts: `Get_Players_Dead_Or_Alive_Or_Omniscient_`
(bill.cpp:312-338): contacted living players, then the eliminated (and
all, when omniscient). Bars, fields, spies: `Get_Active_Players_(0,0)`
(:792; bill.cpp:565-596): contacted living only.

**Dialogs.** Race report (`RACERPRT::Race_Report_Screen_`,
racerprt.cpp:9-155), diplomacy (`DIP_SCRN::Diplomacy_Screen_`,
dip_scrn_main.cpp:1257-1349), the declare-war confirmation
(`Do_Confirmation_Box_`, BILLTEX2 0x1A), multiplayer boxes. All report 6.

**Reads.** `s_player`: name, race_name, eliminated, race, color,
personality, objectives, contact, the agreement levels, relations,
treaty, trade/research/tribute treaty, traits, tech_applications, spies,
ignoring; the leader records (spy master / telepath). **[175]** every
field is in the snapshot; the ones not decoded are added to
`core/structs/player.py` in this order (header route + `tools/
races_check.py` over 14 saves).

**Triggers.** `ignoring` (:888, :910), `spies[]` on commit (:518-530),
`delayed_diplomacy_orders` (:905, war), the diplomacy screen's results,
back to SCREEN_MAIN.

**Right-click help.** `BILLHELP::Races_Help_` (billhelp.cpp:74-83): 259
Agents, 260 Ignore, 261 Report, 262 Audience, 572 Declare War, 258 the
two halves; the report's 263 over the whole screen. All in `help_en.json`.

**Not on the wire:** the spy drag in progress and the missions before
commit; who mode's armed action; the report's and diplomacy's own state
(all three report 6 — told apart only by the field list); BILLTEX2 (no
extractor); a leader at a space anomaly (the event table).

## C. Races screen — BUILT (offline); live test parked (port)

`screens/races/` (id 6, `core/screen_names` now routes it), six modules
(`racesgeom`, `raceswire`, `racesrows`, `racesdraw`, `racesart`,
`screen.py`), each under the 300-line rule.

**Complete against the inventory:**

| inventory item | built | how |
|---|---|---|
| portraits, frames, ELIMINATED, name | yes | RACES.LBX 31/32+race, banner colours by `color` |
| treaty paragraph / NO CONTACT / (IGNORED) | yes | ESTRINGS 0x275+, BILLTEXT 0x32-0x3C |
| relation bar, slider, word on hover | yes | `slider_y`, `relation_word_id` from the source tables |
| spies per race, agents' pool | yes (display) | RACES.LBX 46+race, `icon_spacing` |
| SPY / AGENT bonus | yes | `Compute_Spy_Bonuses_`; OMISSION `anomaly_leaders` |
| RETURN / ESC, AUDIENCE, REPORT, DECLARE WAR, IGNORE | yes, sent | radios activated; WHO read off the list |
| WHO mode: pick a race / cancel | yes, sent | who fields, the catcher |
| declare-war confirmation | yes | `core/gamebox` + `fltbox` drawing |
| race report, diplomacy | fallback | same id, neither list: DIALOG hands over (decision 22) |
| missions, spy drag | display only | parked: effect reaches the wire only on commit |
| right-click help | yes | `help.json` from `_races_help_list` |
| background, bars, buttons art | no (by design) | OMISSION `outer_frame`, DEVIATION `hud_parts` |

**New data**: 11 `s_player` fields (`objectives`, the two agreement-level
arrays, `relations`, `treaty`, `trade_treaty`, `research_treaty`,
`tribute_treaty`, `spies`, `ignoring`) — header route green (40 offsets),
`tools/races_check.py` 14 of 14 saves (it found that treaty runs to 6 —
total war, clamped to label 5 by the screen). New extractor
`tools/races_art_extract.py`, registered in `tools/setup.py`, output
gitignored.

**Checks**: new `090e` (4). 326 -> 330 (fast 320). Core inventories
extended: 017 (markings), 055 (help.json's hd_extension), 059 (the
extractor registry), 062 (JSON exceptions); 001's "6 has no HD screen"
became "6 routes to races".

**Evidence (offline, the reference fixture's own players)**:
`evidence/work_order_175/races/races_{main,who}_offline_*_{1920x1080,
2560x1440,3840x2160,2576x1432}.png` (`tools/races_offline.py`). No native
half — that needs the live game.

## D. Info screen — INVENTORY (from the orion2re source, before building)

**Screen.** `SCREEN_INFO` = 9 (orion2_consts.h:469), `INFO::Info_Screen_`
(info.cpp:510-642); the galaxy map's INFO button (`Add_Irregular_Button_
Field_(462,435,526,471,…,"I")`, mainscr.cpp:1399; mainscr_main.cpp:651-655);
always back to SCREEN_MAIN (:641), `Set_Plyr_Info_Btns_` saving the tab into
`history_btns` bits 4-6 (bill.cpp:379-382). **Finding:** info.cpp:641 sets
SCREEN_MAIN unconditionally, so the Turn Summary's jump to a colony
(`Goto_Msg_Colony_`, msg.cpp:653-672) is overwritten — looks like a port
deviation; parked for Joes (item 6).

**Fields.** EXIT (535,434) ESC (INFO.LBX 2, 91x30); five tabs, multi-buttons
bound to the LOCAL `current_tab` (:563-574, `_sub_scr_field` :174); per page:
History's four metric toggles (y 427, INFO.LBX 8-11), Tech's four category
tabs (`_tech_rev_field`, INFO.LBX 16-19), up/down pagers and list rows, the
race page button (385,427) past four races, Turn Summary's pagers and rows,
Reference's index rows (`(0xDD, y-2, 0x19B, y+18)` / `(0x1A5, …, 0x263, …)`
from y 100 by 20), BACK (386,427), the category pagers and topic rows.

**Draws.** Left: stardate (151,27); chart — income bar (30,212), six
maintenance bars 18 apart, percents `((v*1000)/max+5)/10`, labels BILLTEXT
17-27 (net income with the stat byte). Pages: History (legend in player
colours, axes, eight stardate labels, a y ladder, one polyline per player,
`(ring * divisor)` smoothed ten times, :1222-1347); Tech Review (the four
`_review_*` tables :35-70, researched applications only, empty groups
dropped; name, APP_PICS picture, HELP.LBX record body); Race Statistics
(race name upper-cased, trait lines as `Print_Player_Specials_To_Bitmap_`
:338-404, ELIMINATED / NO CONTACT); Turn Summary (BILLTEXT 26 header,
`MSG_::sprintf_msg_` lines, NO MESSAGES); Reference (BILLTEX 10/11 heads,
the category labels ESTRINGS 0x294+ without the digit ones, HELP.LBX 15's
"How to?" list; a category: HELP.LBX entry n sorted, the record's title and
body; a how-to: its body). Long texts: FMTPARA into fixed bitmaps, lists
paged, no scrolling (:917-931, :1086-1093, :1893-1906).

**Reads.** `s_player`: bc_produced, total_maintenance, maintenance[6],
tech_applications, traits, contact, n_times_established_contact,
eliminated, race_name, the four history rings, history_btns; `_stardate`;
**not on the wire:** `_bill_savegame[6]` (the rings' divisors and ring
start) and `MSG_::_msgs` (the turn messages) — open fix 32 below; the pages'
own state (tab, tech tab, race page, reference page, selection).

**Right-click help.** `_info_help_list` 242/243 over the left panel, then
250 / 249 / 248 / 247 / 244 / 245 / 246 per page (billhelp.cpp:3-40; the
category/how-to installers named the other way round, info.cpp:1936-1947).

## D. Info screen — BUILT (offline); texts moddable; live test parked

`screens/info/` (id 9 was already routed to "info"; now there is a screen):
`infogeom`, `infotexts`, `infopages`, `infobox`, `infodraw`, `infoview`,
`screen.py`.

| inventory item | built | how |
|---|---|---|
| stardate, chart, net income | yes | `infopages.chart`, new player fields |
| tabs, RETURN / ESC | yes | HD-local tabs (HD STATE `local_navigation`), RETURN sent |
| Tech Review | yes | the four tables transcribed; HELP.LBX body; OMISSION `app_pictures` |
| Race Statistics | yes | `race_list(previously=True)`, `trait_lines` |
| Reference: index, category, how-to | yes | topic lists extracted (`tools/infotext_extract.py`) |
| History Graph | legend + toggles; curves parked | open fix 32 (divisors not on the wire) |
| Turn Summary | placeholder | open fix 32 (messages not on the wire) |
| right-click help | yes | `open_help_at`, the billhelp ids |
| paging | replaced | HD EXTENSION `wrap_and_scroll` |

**Moddable texts** (`core/modtexts`, decision 73 in fundament part 01):
1060 stable keys; `texts/<screen>/<rest of key>.txt`, plain UTF-8 (format
parked, item 5); missing = default; broken (not UTF-8, empty, > 64 KB) = one
log line and default (read by `core/usermod.read_text` — the folder still
has one reader). `tools/mod_template.py` writes OrionLayer's own texts to
`originals/texts/` and lists the game's keys only; MODDING.md has a Texts
section. **Could use it next:** the main and GAME menus, Custom Race's
messages, the HUD headings, the Leaders and Races button words, the help
popup's HD entries.

**Open fix 32** written and parked: `doc/ext_info_screen_state.patch`
("INFS": `_bill_savegame[6]` and the rendered messages), dry-run applies to
orionlayer-local, syntax-checked with the engine's flags plus a refused
control; row and section 32 in `doc/orion2re_open_fixes.md`.

**New data**: `s_player` total_maintenance @280, maintenance[6] @284,
n_times_established_contact @1521, the four history rings @2372.. (read
unsigned, as info.cpp:1255-1266 casts), history_btns @3780 — header route
green (48 offsets).

**Checks**: new `090f` (4). 330 -> 334 (fast 324). 017 lists the new
markings.

**Evidence (offline)**: `evidence/work_order_175/info/info_*_offline_*` —
seven views (five pages, a category, a how-to) at 1080p, 1440p, 2160p and
2576x1432, and the same with the demo text mod (`*_MOD_*`); the mod itself
is `evidence/work_order_175/demo_text_mod/` (four replacements, one long body
that scrolls, one non-UTF-8 and one empty file that fall back with one log
line each).
