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

## Part 3 — multi-buttons through F12 — **DONE: a clear forwarding defect, fixed**

Measured the way 186 measured the text field (`evidence/work_order_187/P3/`,
engine `230a0638`, SAVE4, guarded, nothing saved): F12, then clicks on the
game's picture in OrionLayer's window, the input log saying what went out,
the effect read where the wire or the picture shows it. Multi-buttons
(type 3, `Add_Multi_Button_Field_`) the scratch save reaches: the
designer's six hulls (DSGN's size), the Colonies screen's seven sort
buttons (colsum.cpp:267-273, the engine's frame), the Info screen's five
tabs (info.cpp:562-572). Left out: the Races screen's spy / sabotage
buttons and the map's tax buttons — game decisions.

| | before | after |
|---|---|---|
| what went out per click | ACTIVATE_FIELD (128), one each | INJECT_CLICK (130), one each |
| designer hulls (6) | **0 of 6 taken** — the size stayed 1 | **6 of 6**: 0, 1, 2, 3, 4, 5 in order |
| Info tabs (5) | **0 of 5** — the page never changed | **5 of 5** |
| Colonies sort buttons (7) | **0 of 7** — no button redrawn | **6 of 7** redrawn; the 7th was the sort already chosen (all of before's clicks had been lost), where a click changes nothing |

So every multi-button click through F12 was LOST: the button's variable is
written in the mouse path an activation skips — the same kind of fault as
186's string field (check 090g #3). None was taken twice (one message and
one step per click). **The fix**: `original_view.find_field_at` answers
None for a multi-button too, so the click goes as INJECT_CLICK (the first
field under the point still decides). **Check** 090g #3 extended: a hull
button's click goes as INJECT_CLICK; red with type 3 taken out of the rule
(the exact live failure), green again. No new check (count stays 409).

## Part 4 — the disabled "Peace Treaty" — **DONE: the original is different; HD now matches it**

**The original** (its own frames; the same values on 185's `P11` and 186's
`P3` menu frames): the title and every enabled item **(44, 164, 28)**, the
disabled "Peace Treaty" **(0, 92, 0)** — the same green, about half as
bright (luminance 54 against 113, **0.48**) — and the hovered item (92,
208, 44). **HD until now**: enabled white (251, 251, 253), the disabled
item in the HUD's `sub` light blue (145, 182, 224) — nearly the title's
blue (133, 178, 228), so it read as a heading or a highlight, not as
"not available". **Changed** (`screens/audience/audraw.py`,
`augeom.DISABLED_DIM`): a disabled item is the enabled colour at the
original's own ratio, (120, 120, 121) — dimmer, same hue; the proportion is
the transcription (fundament part 06). Check 090z extended (the ratio
0.48 from the two measured colours, the dimmed luminance, never `sub` or
`label`, the enabled item's hue).

**Every disabled item reachable** (`evidence/work_order_187/P4*`, SAVE4 and
SAVE5, guarded, nothing proposed): each save knows two races — slot 0
refuses (no menu), slot 1's menu "How may I serve you:" has ONE disabled
item, "Peace Treaty", in both saves; Declare War's confirmation (186) has
none. Every audience transition 0 native frames. Side by side:
`P4/menu_hd_vs_native.png` — HD's "Peace Treaty" now grey beside white,
the original's dark green beside green.

**Seen, not changed** (parked 2a as a question): HD draws the menu's title
in the HUD's label blue, where the original prints it in the items' own
colour.

## Part 5 — the AI's audience (58) — **DONE: reached in SAVE4 at turn 14**

**Tool**: `tools/turn_audience.py` (new) — loads SAVE4/SAVE5, presses the HD
map's TURN, and answers only prompts it identifies from the list read at
that moment (every send through `livesend`); an unknown one stops the run
with its shape and picture recorded. It was grown one prompt at a time over
ten guarded runs (`evidence/work_order_187/P5/s4a-s4m.txt`; each engine
stopped, SAVE10 and MOX.SET restored from the guard taken before it). The
prompts it met, in the order they appeared, and each default decision:

| prompt (screen) | decision |
|---|---|
| "Select planet for Colony Base in Malus system" (0) | the next planet not yet refused this turn (a planet refused → a message, then the next) |
| "Build colony on Malus II with …" YES / NO (0) | **YES** — the colony base's own confirmation (every other Yes / No: NO) |
| the colony landing (33), its messages | clicked away (full-screen field) |
| the new colony's own screen (1) | its RETURN button (never CRUNCH, TOGGLE or field [0]) |
| the turn summary (0), reports | CLOSE (the one button with ESC) |
| a combat choice (12) | CLOSE — the engine resolves the battle |
| "Administrator Lydon offers to join you …" REJECT / HIRE (0) | **REJECT** |
| the science room (52) | clicked away |
| "SELECT NEW RESEARCH" (53) | the first choice (an injected click on its centre); SAVE4 has every field researched — "Hyper-advanced Construction" |
| the race picks after a research (0, PICKS / ACCEPT) | **ACCEPT with none taken** — the race unchanged |

Every decision of the final run, per turn (`P5_turns_save4_1920x1080/
decisions.json`, 72 entries): t1 colony base placed (planet chosen, YES),
landing, the new colony's screen, the summary; t2 a combat, CLOSE; t3 a
leader rejected; t4 the summary; t5 and t6 a colony base placed each; t7 a
new colony's screen; t9 the summary; t13 the science room, research chosen;
t14 research chosen, race picks accepted unchanged, a colony base placed —
**then five AI ambassadors in a row (58)**. All in memory; nothing saved;
SAVE10 restored after every run.

**The audience (58)**: four statements, all declarations — "Death to the
CyberToller race! …", "Your people are only fit as slaves to the noble
Elerian Empire …", and two of the Gnolam Empire's. No menu and no
proposal came (the AIs declared; nothing was answered but the statements'
own click). HD drew all of it: **279 frames at 58, all HD**. Beside the
native frame after its fade-in (`P5/ai_audience_hd_vs_native.png`): the
same ambassador, room and statement with the same line breaks; the known
differences — the header line ("Elerian Ambassador", OMISSION
`header_line`), the HUD panel under the text (DEVIATION `hud_frameless`),
the fade-in (OMISSION `fade_in`).

**Into and out of it** (the frame sequence recorded around 58): map HD →
5 held → **58: 279 HD** → 29 held → 15 native → HD. **Into 58 and out of it:
no native frame.** The 15 native frames after it are the NEXT prompt — the
turn summary over the map, a box (Part 6's path 5, shown by option C after
5 snapshots) — not the audience's exit. The run's other native frames are
the same kind: the colony landing (33), the science room (52), a combat
turn (12) — screens without an HD version (Part 6's path 1).

**Not done**: SAVE5 was not run (58 reached in SAVE4). One slip of mine in
an intermediate run (`s4k`): after the last audience had ended, the tool
clicked the window's centre once more on a statement read a frame earlier
— it landed on the map; the tool now clicks only while 57/58 still stands.

