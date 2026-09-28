# Work order 186, Part 4 — the hold before modal boxes (measured, nothing changed)

Engine: orion2re `230a0638` (the binary `play.py` starts), Xvfb, every run
through `tools/engine_start.py --guard`, guards verified and restored
(MOX.SET on every load, SAVE10 after each TURN press). Tool:
`tools/modal_hold.py` (OrionLayer, work order 186) — drives the App through
its window and records the input's time, every STATE and FIELD_LIST
arrival with its list, and every presented frame (`core.frametrace`:
`hold` = the gate holding HD's last frame, `net` = the game's picture) with
the snapshot count it was presented at. Raw data: `P4_modal_*/modal_hold.json`,
logs `P4/*.txt`.

## 1. What the gate waits for at a modal box

Nothing that can arrive. A modal box is a list the HD screen does not own
(the designer: no Cancel button in the list, `sdwire.View` → `GAME_BOX`;
the galaxy map: its net's `classify` → unknown). The screen then reports
`wants_original()`, `core/handover.decide_for` renames the hand-over
`modal` (`handover_is_modal()`), and `Gate.decide` holds HD's last frame
for `HOLD` = **36 snapshots** before it shows the picture
(handover.py:96-113). The hold was made for a KNOWN screen whose data is
late — it ends early when that data arrives. For a modal nothing arrives
that would end it, so it always runs its full 36 snapshots. `HOLD` was
sized as "two seconds at the ~18 snapshots a second measured in work order
177" (handover.py:54-58) — the galaxy map's pace. A modal box's own loop is
slower: the warning box waits `Release_Time_(2)` = 110 ms per pass
(gendraw.cpp:141-147), so 36 of its snapshots take ~4 s.

## 2. Where the time goes — three modals, all reachable in the scratch saves

| | designer's shield warning, SAVE4 (id 3), 3 runs | colony-base choice after TURN, SAVE4 (id 0, the map's net) | combat choice after TURN, SAVE5 (id 12, no HD screen) |
|---|---|---|---|
| input → the box's list on the wire | 0.02 / 0.09 / 0.09 s | 0.09 s (through 12 and 39), its 8-field list at 0.25 s | 0.09 s (empty), its 6-field list at 0.25 s |
| longest wire silence before it | 0.10-0.12 s (one ordinary pass) | 0.12 s | 0.11 s |
| gate starts holding | same frame as the list (0.02-0.09 s) | 0.09 s (39, empty: `no_screen`), then the map's net: `modal` | 0.09 s (`no_screen`, empty list) |
| held | **36 snapshots, 3.96-3.97 s** | **36 snapshots, 3.87 s** (+1 on 39) | 1 snapshot, 0.05 s |
| the box's pacing | 106.2-106.5 ms (9.4/s) | 112.9 ms (8.9/s) | 105.8 ms (9.5/s) |
| first frame of the game's picture | **3.99 / 4.04 / 4.06 s** | **4.10 s** | **0.14 s** |

Timeline of the designer's box, typical run: input 0 → the engine takes the
activation and opens the box within one pass, its list arrives 0.02-0.09 s
→ HD holds its last frame from that frame on → the engine keeps sending the
box's snapshots every ~106 ms → after the 36th (3.96 s) the gate releases
→ the next presented frame is the game's picture (3.99-4.06 s). The wire
itself adds nothing measurable (localhost; the list arrives within the same
pass). **~98 % of the wait is the gate counting snapshots at the box's
pace.** 185's 3.76 s (a scratch engine, a coarser clock) is the same wait.

The same holds for every modal box over an HD screen: the map's
colony-base choice waited 36 snapshots too (4.10 s). A box under an id no
HD screen claims is NOT held: the gate shows it once its list has a field
to answer (`no_screen`, handover.py:82) — the combat choice at 0.14 s. The
three are the modal boxes the scratch saves reach without a game decision;
others of the same kind (a colony screen's refusal box, the build popup's
messages) go through the same `modal` path and would wait the same 36 of
their own snapshots.

## 3. Does it depend on the engine's input delay (open fix 42)?

**No.** In every run the longest wire silence between the input and the
box's list is one ordinary loop pass (0.10-0.12 s), and none of the three
paths sets an input delay before its box: `Warning_Box_` →
`Message_Box_Exploding_` (gendraw.cpp:26-150) has none; the text box's
`Set_Input_Delay_(3)` comes only in its cleanup (textbox.cpp:167), i.e. on
the screen AFTER the box. The hold counts snapshots, and the box sends them
throughout; fix 42 (ticking during a delay) would change none of these
numbers. (Where fix 42 does matter is a delay before a KNOWN screen — the
research panel's, the designer's 20 passes before the weapon picker — not
a modal box.)

## 4. Two things found on the way (not changed)

- `core/modalnet.SETTLE` = 5 is documented as snapshots ("a quarter of a
  second", modalnet.py:28-32), but `Net.check` runs once per FRAME (the
  dispatcher's per-frame `update`, `mapmodal.update`) — so the map's net
  settles in ~5 frames (~0.08 s), not 5 snapshots. It is not part of the
  4 s; it is a docstring that does not say what the code counts.
- The frame trace labels these holds `hand_over` (`App._net_kind` is set
  before `decide_for` renames the kind), while the gate's own log says
  `modal`. The count is right, the label in the trace is the pre-rename one.

## 5. Options

| | what | the designer's box would appear after | cost / risk |
|---|---|---|---|
| A | as now | ~4 s | nothing; a player waits ~4 s at every modal box |
| B | a `modal` hand-over is shown at once, as `no_screen` is, once its list has a field to answer — the screen's own classification (the designer: no Cancel; the map: its net) is the guard | ~0.05-0.1 s (the list's frame) | a transient list mid-transition could flash the picture — the case `HOLD` exists for; but the screen has already judged the list NOT its own and NOT a known modal |
| C | B plus `SETTLE` counted in snapshots, as documented (5 of the box's ≈ 0.5 s), applied to every modal screen alike | ~0.5 s | the half-second is a real guard against a list that changes on the next pass; one number to tune |
| D | a smaller `HOLD` for `modal` only (e.g. 5 snapshots) | ~0.5 s | same as C in effect, but keeps two mechanisms (net settle + gate hold) doing the same job |
| E | hold in seconds, not snapshots | 2 s as HOLD meant | against decision 21 (snapshots, not seconds — a silence is not a failure) |

**Recommendation: C.** It is what the two mechanisms already claim to do:
the net waits a stable quarter-to-half second of an unknown list, and the
gate's long hold stays for the case it was built for — a known screen whose
data is late. The player would see the box ~0.5 s after the click instead
of ~4 s, with no new flash risk beyond what the settle already accepts.
**Decision parked for Data; nothing changed.**
