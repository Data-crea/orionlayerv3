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
