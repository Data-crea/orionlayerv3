# Work order 187 — progress

Unattended run, 28 September 2026. Evidence root:
`~/orionlayer-fixtures/evidence/work_order_187/`. The order:
`doc/briefs/187-work-order-modal-hold-hd-name-entry-ai-audience-original-only-on-f12.md`.

## Before part 1

- **Number 187**: the last brief in `doc/briefs/` is 186.
- **Baseline as expected**: main = origin/main = `557da0f` (186, "Work order
  186 Part 5: gates green and the end of the order"), 407 green by 186's
  push gate; orion2re `orionlayer-local` = `230a0638` (fixes 34-41, 43-47),
  its three untracked files left alone.
- Read: `doc/v3_fundament.md`, the three `principles-` parts, part 09, 186's
  progress, parked file and `186-modal-hold.md` (all read or written in
  this session).
- **Data was playing at the start**: `python play.py` (PID 199264, started
  18:40:33), its engine 199278 and OrionLayer 199301 — not touched, never
  connected to. `engine_start --check` refused (a foreign engine, the port
  taken). Live parts wait until his session has ended; the order's first
  guard is taken then, not mid-play (it would record his own saves as
  changes). Non-live work went first.
- 19:11 his session had ended; the order's first guard `guard_187_start`
  was taken (SAVE1 written by his session at 19:03, SAVE4/SAVE5 unchanged
  since 15 September). **At 19:12:29 an engine started again from his
  desktop session** (PID 215004, parent `systemd --user`) — his, not this
  run's: not touched, never connected to. `guard_187_start` is therefore
  not the first guard of this order's live runs; a new one is taken once
  that engine has ended.
- 19:25 Data said his engine was closed; PID 215004 still held the port.
  On his instruction ("dann schließe ihn") it was closed with
  `engine_start --close-foreign` (the auto-mode classifier had refused the
  first attempt): backup `live_guard/close_20260928_192524`, ended on
  SIGTERM. **The order's first live guard is `guard_187_first`** (taken
  after that); between 19:11 and then only his engine had changed a file
  (MOX.SET — his).

## Part 6 — where the original can still show (inventory, no change) — **DONE (committed before parts 1-5: it needs no live run, and Data was playing)**

Report: `doc/briefs/187-original-visibility.md`. **6 paths** by which the
original can show without F12, all through `main.App._showing_original`
and the gate: (1) a game screen with no HD screen (ids 7, 12, 14, 18, 30,
39, 40, 52 and every unlisted one, e.g. 33); (2) such an id with an empty
list past `EMPTY_HOLD`; (3) a known screen declining its id (an engine
without fixes 35-40 / 44-47); (4) a box over an HD page (`GAME_BOX`);
(5) a box over a screen with a modal net (map, main menu, select race);
(6) a known screen that cannot vouch (missing extractor files, a dialog
it cannot name) — the safety net's keys and clicks (7) are their input,
not an extra path. Seen in walks: 1, 4, 5 (the gate's log lines of
180-186: 10 designer-box and 2 colony-base releases; SAVE5's combat choice);
never seen: 2, 3, 6. **Recommendation**: one rule for all six — never the
picture, HD's last frame dimmed with a notice "Press F12 to answer it"
(needs Data's decision first); then one HD message box on open fix 29,
"A native message box's text is not in the snapshot" (needs Data's decision
first: an engine fix); then HD screens by frequency. Parked 1a.

## Part 1 — the modal hold, option C — **DONE**

**The change** (`core/handover.py`): a MODAL hand-over that is a BOX —
`ScreenBase.modal_is_box()` — is shown once its live list has stood
unchanged for `MODAL_SETTLE` = `modalnet.SETTLE` = 5 snapshots; a list that
changes restarts the count; everything else keeps the full `HOLD` (36).
"No late data can come" is made exact per screen: the `GAME_BOX` screens
(designer, pickers, colony, build popup, audience) answer True only with
their own block on the wire (the box replaced their page); the three
modal-net screens (galaxy map, main menu, select race) answer through the
base: True only once their own list was seen this visit (`Net.own_seen`,
`Net.box`) — so the main menu's opening animation, which comes BEFORE the
menu's list (work order 180 A1's flash), keeps the full hold. `modalnet`'s
`SETTLE` comment now says it counts frames there (186's finding).

**Before / after**, input to the first frame showing the box (engine
`230a0638`, Xvfb, SAVE4/SAVE5, guarded; "before" = the same code with the
early release switched off in the measuring process only, `modal_hold.py
--before`; evidence `work_order_187/P1/`):

| modal box | screen | before | after | held (snapshots) | box pace |
|---|---|---|---|---|---|
| the designer's shield warning ("You may not upgrade the ship's shield."), 3 runs | 3 | 4.01 / 4.05 / 4.07 s | **0.57 / 0.64 / 0.64 s** | 36 → 5 | 106 ms |
| the colony screen's BUY → a message box (SAVE4's home colony) | 1 | 2.11 s | **0.38 s** | 36 → 5 | 54 ms |
| SAVE4's TURN → the colony-base choice (the map's net) | 0 | 4.11 s | **0.68 s** | 38 → 7 | 114 ms |
| SAVE5's TURN → the combat choice (no HD screen: not a box, unchanged) | 12 | (186: 0.14 s) | 0.13 s | 1 | 107 ms |

These are every modal box the scratch saves reach without a game decision
(SAVE4's home colony answers BUY with a message box, not the Yes/No
confirmation — which would take the same GAME_BOX path).
**Note, against Data's rule**: "shown" is still the GAME'S picture of the
box — sooner, not replaced. See Part 6 and parked 1a.

**Flash walk with the change** (engine `230a0638`, guard `P1/guard_flash`,
verified identical): `flash_walk` 29 transitions, `design_walk` 11,
`audience_walk` 7, `colony_accept` 17 (282 colony frames agreeing, 0
disagreeing) — **0 native frames**; the main menu's net was never
released. Guards: SAVE10 and MOX.SET restored after each TURN run from the
guard taken before that engine; every one verified identical.

**Checks**: 090o #5 (new) — the gate's early release, a changing list,
the full hold for non-boxes / empty lists / hand-overs, the nets' own-list
rule, each screen's answer; shown red with the early release disabled.
Count 407 → 408.

## Part 2 — the designer's name entry in HD — **DONE: it works in HD, 0 native frames**

**The path the HD screens that take text use** — the save dialog
(`screens/game_menu/gmsave.py`, work order 124) and Empire Identity
(`core/injection.py`): HD holds the text in its own `TextInput` (field,
cursor, typed text drawn by HD); on Enter one paced `InjectionChain` step
sends the field's opening input and the keys, one per tick (the game's key
ring holds ten). **The designer now takes the same path**
(`screens/ship_design/sdname.py`, new): a click on the name opens HD's
field; Enter sends an injected click on the original's name field (an
activation does not open this field — 186), **15 Backspaces**, the letters,
Enter; ESC cancels in HD with nothing sent; a click away commits (as the
original's field does); other input is refused while the keys go out.
Letters but `_`, at most 14 (fields.cpp:1204-1216).

**Found on the way, live**: the first version sent ONE Backspace, as the
save dialog does, trusting `_active_input_field_first` (its first
Backspace clears all, fields.cpp:1196-1199). "Rafale" + "Hawke" became
"RafalHawke": the click sets that flag only when it OPENS the field
(:1437), and the designer's field was already active, so one Backspace took
one letter. The always-clearing code 0x0E7F (:1181) no injected key
produces (Delete is 0x10000, platform.cpp:435). 15 Backspaces clear any
name in either state (an empty field ignores them, :1193).

**Live on Xvfb** (engine `230a0638`, SAVE4, guarded, nothing saved;
`evidence/work_order_187/P2*`): open the field, clear, type "Hawkz",
Backspace, "e", Enter → the engine's name **"Hawke"** after 4.9-5.7 s (21
keys at one per tick); open again, type "Xyz", ESC → still "Hawke", the
page stays; **0 native frames** in 329 and 397 presented frames, 0 held;
both recorded as transitions ("name entry: Enter", "name entry: ESC").
Screenshots: HD's glass field with the text and its caret.

**Checks**: 090x #7 (new) — keys stay local until Enter; then click,
15 Backspaces, the keys, Enter; ESC sends nothing; `_` and a 15th letter
refused; the page never asks for the picture; the live name entry is in
the replay set (`transitions_180.json` 233 → 240, the 233 reproduced byte
for byte first) that 090o replays with 0 native frames. Shown red with an
activation instead of the click. Marks: DEVIATION `name_field` replaces
OMISSION `name_entry`. Count 408 → 409.

