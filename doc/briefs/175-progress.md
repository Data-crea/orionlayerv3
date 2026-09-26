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
