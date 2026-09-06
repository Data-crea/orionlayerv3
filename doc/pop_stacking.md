# How the original stacks population figures

**An investigation, 6 September 2026.** It states rules and measures
them; it decides nothing. Every line number was re-anchored against
the working tree at `~/orion2re` on that date, and every number below
either carries a `file:line` or was measured against the running game.

The reason this exists: the HD colony summary may get a second
population style that draws the original's own figures out of
`raceicon_ref/` instead of allocation cells. Before that, the tree
knew two things — that `Calculate_Squish_Step_` exists and that
figures overlap. Neither is a rule.

---

## 0. The one function, and its five modes

Everything below goes through **`COLDRAW::Do_Colony_Info_Pop_Stuff_For_Pop_`**
(`coldraw.cpp:281-443`). It is not a drawing routine — it is one walk
over a colony's pops with a `mode` that says what to do at each one:

| mode | what it does | where |
|---|---|---|
| 0 | draws the figure | `coldraw.cpp:339-352` |
| 1 | fills `pop_index_by_slot[]` and adds the scroll field | `:354`, `:409` |
| 2 | counts, then sets the step | `:413-420` |
| 3 | hit test against a scroll field's value | `:361` |
| 4 | hit test against the live pointer x | `:367` |

**Mode 2 runs first, always.** `coldraw.cpp:300-302`: any call whose
mode is not 2 re-enters itself with mode 2 before doing anything
else. That pass counts and calls `Calculate_Squish_Step_`; the outer
pass then uses `COLONY::_step_squish` and resets it to 0 on the way
out (`Reset_Step_Squish_`, `colony.cpp:2108-2110`, reached by the
`reset_step_squish_and_return` label at `coldraw.cpp:440`).

So **the step is never remembered between draws.** It is recomputed
from the pop array every single time a column is drawn or hit-tested.

---

## 1. Where it is drawn, and on which screens

Three screens call it, with **three different geometries**. The
placement is entirely in the caller's arguments; the walk itself
knows only `left_x`, `top_y` and `right_x`.

### Colony summary — three columns side by side, per row

| | value | source |
|---|---|---|
| columns | 3, one per job, ECON order | `job_filter` = 0,1,2 |
| left_x | 101, 236, 378 | `colsum.cpp:702-708` |
| right_x | 226, 368, 502 (`coord_c - 10`) | `colsum.cpp:691-697`, `:711` |
| row top (draw) | `colony_idx * 31 + 38` | `colsum.cpp:685` |
| row top (field) | `colony_idx * 31 + 34` | `colsum.cpp:331-335` |
| farm shadows | **off** (argument 7 = 0) | `colsum.cpp:722` |

Drawn by `COLSUM::Draw_Info_Pop_For_` (`colsum.cpp:683`), called per
row at `colsum.cpp:550` and `:586`. The click fields are added by
`Add_Fields_Pop_For_` (`colsum.cpp:312-344`) with the same three
`(left, right)` pairs, and the hit tests are `Get_Selected_Pop_`
(`colsum.cpp:1006`, mode 3) and `Get_Scanned_Pop_` (`colsum.cpp:963`,
mode 4).

**The draw top and the field top differ by 4 px** — 38 against 34.
The field is the 30-px scroll bar added at `coldraw.cpp:409`; the
figures are drawn 4 px lower inside it. `colonyicons.ROW_TOP` is 34,
which is right for the click and is *not* the draw origin.

### Colony main screen — three rows stacked, one x range

| | value | source |
|---|---|---|
| rows | 3, one per job | `Draw_Colony_Info_Pop_For_(0..2)`, `colony.cpp:767-771` |
| left_x | 310 (0x136), all three | `colony.cpp:1336-1339` |
| right_x | 510 (0x1FE), all three | `colony.cpp:1341` |
| row top | `type * 30 + 62` → 62, 92, 122 | `colony.cpp:1334` |
| farm shadows | **on** (argument 7 = 1) | `colony.cpp:1342` |

Hit tests `Get_Scanned_Pop_` (`colony.cpp:1438`, mode 4) and
`Get_Selected_Pop_` (`colony.cpp:1456`, mode 3) repeat the same
310/510 literals, and `Add_Job_Field_For_` (`colony.cpp:1475`) adds
the fields.

### Population transport — one run of all three jobs

`COLXPORT::Draw_Info_Pop_For_` (`colxport.cpp:295-311`) passes
`job_filter = -1`, `left_x = 148` (0x94), `right_x = 441` (0x1B9),
top `entry_index * 38 + 54`, `show_farm_shadows` 0 (`colxport.cpp:307`).
A `job_filter` of -1 makes the walk
cover jobs 0..2 in one pass (`coldraw.cpp:307-314`), so **all of a
colony's pops form a single run** on that screen, farmers then
workers then scientists, sharing one step.

---

## 2. The step

`COLDRAW::Calculate_Squish_Step_` (`coldraw.cpp:12-33`), quoted:

```c
int16_t divisor = icon_count;
int16_t base_val = icon_spacing;

int16_t intermediate = (int16_t)(base_val / -3);
intermediate = (intermediate - start_x) + available_width;

if (divisor <= 1) { divisor = 1; }

int16_t step_calc = intermediate / divisor;

if (step_calc <= 1) { step_calc = 1; }

if (step_calc < base_val) { COLONY::_step_squish = base_val - step_calc; }
else                      { COLONY::_step_squish = 0; }
```

and the pitch every draw and hit test uses is `30 - _step_squish`
(`coldraw.cpp:349` and `:399` for the two draws, `:361` and `:367`
for the two hit tests).

**`available_width` is a misnomer at every pop call site: `right_x`
is passed.** `coldraw.cpp:419` is
`Calculate_Squish_Step_(left_x, right_x, squish_count, 30)`. So with
`icon_spacing = 30`, `30 / -3` is **-10** by C truncation toward
zero, and the whole expression reduces to

```
pitch = clamp(  (right_x - left_x - 10) / n  )      n >= 1
        with the quotient truncated toward zero,
        raised to 1 if it is <= 1,
        and capped at 30.
```

Both divisions are integer. `30 / -3` is exactly -10 and not -11 —
this is the one place a float would round the other way.

### The inputs, per column

| screen | job | left | right | `right - left - 10` |
|---|---|---|---|---|
| summary | food | 101 | 226 | **115** |
| summary | industry | 236 | 368 | **122** |
| summary | research | 378 | 502 | **114** |
| colony main | all three | 310 | 510 | **190** |
| transport | all jobs in one | 148 | 441 | **283** |

### The overlap threshold

Figures start overlapping when the quotient falls below 30, i.e. at
the first `n` with `(right - left - 10) / n < 30`:

| column | fits at full 30 px | first overlapping count | pitch there |
|---|---|---|---|
| summary food | n ≤ 3 | **n = 4** | 28 |
| summary industry | n ≤ 4 | **n = 5** | 24 |
| summary research | n ≤ 3 | **n = 4** | 28 |
| colony main | n ≤ 6 | **n = 7** | 27 |

The industry column is one wider than its neighbours, so four workers
still stand apart where four farmers do not. That is a data
difference, not an artefact — 122 against 115 and 114.

The minimum pitch is **1 px**, from `if (step_calc <= 1) step_calc = 1`.
It is not 0: figures can never be drawn on top of each other exactly.

### Whose count drives it

**The count is the COLUMN's, not the colony's and not the group's**,
and it is the count of *drawn* figures — the walk increments
`pop_draw_index` only inside the `(pop_val & 0x200) != 0` test
(`coldraw.cpp:336`), so an unassigned pop contributes nothing.

With one exception, and it is the colony main screen's:

```c
int16_t squish_count = pop_draw_index;
const uint8_t max_farms = MOX::_colony[colony_idx].max_farms;
if (show_farm_shadows != 0 && job_filter == 0 && max_farms != 0xff) {
    squish_count = (int16_t)max_farms;
}
```
`coldraw.cpp:414-419`.

**On a screen that draws farm shadows, the food column's step comes
from `max_farms` — the number of farm SLOTS — and not from the number
of farmers.** The colony main screen passes `show_farm_shadows = 1`
(`colony.cpp:1342`); the colony summary passes 0 (`colsum.cpp:722`)
and the transport screen passes 0 (`colxport.cpp:307`). So the same
colony's food column is spaced differently on the two screens
whenever `max_farms != 255`.

The shadows themselves are drawn by mode 0's tail
(`coldraw.cpp:391-404`): after the real farmers, `Shadow_Farmer_Bitm_`
is drawn at the same pitch (`coldraw.cpp:399`) until `pop_draw_index` reaches
`max_farms`. The sprite is the player's own farmer, glassed and
outlined (`Create_Shadow_Farmer_`, `colony.cpp:2227-2246`).

**Not measured here.** Both fixture savegames have `max_farms == 255`
in every colony, so this branch never fires in anything this project
can measure today. The rule is read, not confirmed.

---

## 3. Columns, and where a column ends

Three columns on the summary, in **ECON order** — `ECON_FOOD` 0,
`ECON_INDUSTRY` 1, `ECON_RESEARCH` 2 (`orion2_consts.h:119-121`) —
laid left to right in that order.

**The widths are literals in the caller, not field rectangles.** The
101/236/378/512 chain appears three times over
(`colsum.cpp:691-708`, `:976-982`, `:1007-1023`), each time as an
if-chain of constants. The scroll field that *does* exist is built
from those same numbers afterwards (`coldraw.cpp:409`), so the field
follows the constants and not the other way round.

**There is no clip.** Mode 0 calls `animate::Draw_` directly
(`coldraw.cpp:349`), and `animate::Draw_` clips only against the
screen window (`animate.cpp:104-124`), which the colony summary
leaves at the full 640x480. `right_x` is an input to the step
arithmetic and nothing else — no figure is ever cut at it.

So a crowded column **can** run past its own right edge and into its
neighbour. The sprites are 28 px wide (measured; `raceicon_ref`
summary.txt), so the rightmost figure ends at
`left + pitch * (n - 1) + 28`, and maximising that over n = 1..42:

| column | worst case | last figure's right edge | past `right_x` | into the next column |
|---|---|---|---|---|
| food | n = 38, pitch 3 | 240 | 14 px | **4 px** (industry starts at 236) |
| industry | n = 40, pitch 3 | 381 | 13 px | **3 px** (research starts at 378) |
| research | n = 38, pitch 3 | 517 | 15 px | — |

It is a narrow case — it needs about forty pops in one job — but it
is not prevented by anything, and the last figure of a full food
column would be drawn *under* the first worker, because the worker
column is drawn afterwards (`colsum.cpp:687`, the `pop_slot` loop).

---

## 4. Draw order is z-order

The walk is five nested loops (`coldraw.cpp:326-386`), and figure
`pop_draw_index` is drawn at `left_x + pitch * pop_draw_index`
(`coldraw.cpp:349`) — so **`pop_draw_index` increases left to
right, and each figure is drawn after the one to its left.**

Index 0 is transparent in both frame formats (`Draw_Bitmap_Sprite_`
and `Draw_Animated_Sprite_`, `draw.cpp`), so where two figures
overlap, **the right-hand one is whole and the left one is cut on its
right side.** A column of overlapping figures reads as a row of
shoulders with one complete figure at the right end.

**The walk order is the one `screens/colony_summary/colonyicons.py`
already transcribes** as `icon_pops` — state, then the conquered bit,
then job, then the low-nibble order `(9, 0, 1..8)`, then array order.
That transcription was re-verified by pixels for this document; see
§8.

Storage order is not stable and must never be used instead: pops are
appended, removed by swapping the last entry into the hole, and the
whole array is shuffled when a colony builds Biospheres
(`invasion.cpp:721`; recorded in `doc/pop_order_reading.md` and as
decision 48).

---

## 5. What is placed where, and which sprite

Grouping is **not** a sort applied to the list — it falls out of the
loop nesting (`coldraw.cpp:326-332`):

```
for state       0..6      Pop_To_Pop_State_
  for race_idx  0..1      (pop & 0x400) >> 10   -- the CONQUERED bit
    for job     the column
      for nibble in (9, 0, 1, 2, 3, 4, 5, 6, 7, 8)
        for i   0..n_pops                        -- array order
```

So within one column the figures are **grouped, never interleaved**,
in this sequence: the player's own and other players' pops (state 2)
before natives (state 3) before androids (state 4); and inside each
state, unconquered before conquered.

The nibble order puts **9 (native) first inside its own group** —
which does nothing observable, because a native is state 3 and the
state loop has already separated it.

The sprite per figure is `COLONY::Colony_Pop_Anim_`
(`colony.cpp:1268-1283`):

```c
if ((pop_data & 0x400) != 0) { return Colony_Pop_Icon_(race); }
return People_Anim_(type, pop_state, race);
```

- `race` is `MOX::_player[ Get_Effective_Pop_Player_(...) ].race`
  (`colony.cpp:1273-1274`). `Get_Effective_Pop_Player_`
  (`colony.cpp:1257-1266`) maps nibble 8 and 9 to the **colony's
  owner** and every other nibble to itself. So a pop's sprite race
  comes from the PLAYER TABLE via the nibble — never from the nibble
  itself.
- `Colony_Pop_Icon_(race)` is `race * 13 + 12` (`colony.cpp:1285-1289`),
  a static race portrait rather than a working figure.
- `People_Anim_` is `race * 13 + job * 2 (+1)`
  (`colony_main.cpp:444-450`); the block layout of the 13 is in
  `tools/raceicon_extract.py` and `v3_projektstatus.md`.

**The `race_idx` naming discrepancy belongs here.** The second loop
is called `race_idx` in the source (`coldraw.cpp:327`) and is the
conquered bit, `MASK_CONQUERED` (`pop.h:12`) — it has nothing to
do with a race index. It is not cosmetic: that loop is what makes a
column read "working figures first, then race portraits", because a
conquered pop is drawn from a different sprite class entirely. Filed
as item 9 in `doc/orion2re_open_fixes.md`.

**One case draws differently again**: the scanned pop, while the
cycler is on, is drawn through `Draw_Pop_Dark_`
(`coldraw.cpp:341-345`, `colony.cpp:2210-2221`) — the same sprite
composited into a 30x30 scratch bitmap and tinted. Same position,
same pitch.

---

## 6. `pop_state` 3 and 4

`COLONY::Pop_To_Pop_State_` (`colony.cpp:1240-1255`) is the only
source of the value on a colony pop, and it reads the low nibble:

| nibble | state | figure |
|---|---|---|
| 9 | 3 | RACEICON entry **0xAA**, one sprite for every native |
| 8 | 4 | RACEICON entry **0xA9**, one sprite for every android |
| anything else | 2 | `race * 13 + job * 2 + 1` |

`People_Anim_`'s branches for 3 and 4 ignore the race argument
entirely (`colony_main.cpp:456-461`).

**State does not change position, only the sprite and the group.**
There is no separate x rule for a native or an android; they occupy
slots in the same run at the same pitch, placed where the state loop
puts them — after every state-2 figure of that column.

**None of the three states is the held cluster.** A held pop is not
in any state as far as the drawing is concerned: it has its `0x200`
bit cleared and the walk skips it at `coldraw.cpp:336`, one test after
`Pop_To_Pop_State_`. See §7.

`People_Anim_` also has a `pop_state == 0` branch
(`colony_main.cpp:450-453`) that `Pop_To_Pop_State_` cannot produce
and no call site passes. It is recorded as an observation in
`doc/orion2re_open_fixes.md`.

---

## 7. Selection and clusters

`COLMOVE::Get_Cluster_` (`colmove.cpp:56-77`) clears bit `0x200` on
every identical pop from the clicked one to the end of the array:

```c
colony->pop[i] &= 0xFFFFFDFF;
```

The drawing walk tests exactly that bit (`coldraw.cpp:336`), so:

1. **the held figures vanish from the column** — the original shows a
   cluster in hand by removing it from the row, not by greying it;
2. **no gap appears.** `pop_draw_index` only advances for drawn
   figures, so the survivors close up;
3. **the step recomputes.** Mode 2 counts the same reduced set
   (`coldraw.cpp:414`), so a column that loses three of eight figures
   is redrawn at a wider pitch and **every remaining figure moves.**

The cluster in hand is drawn somewhere else entirely, by
`COLMOVE::Draw_Cluster_(x, y)` (`colmove.cpp:7-36`), and its rules
are different in every respect:

| | held cluster | a column |
|---|---|---|
| position | at the mouse, `y - 10` | fixed `left_x`, `top_y` |
| pitch | **20 px, constant** (`colmove.cpp:28`) | `30 - _step_squish` |
| order | **array order** `i = 0..n_pops` (`colmove.cpp:24`) | the five-loop walk |
| backdrop | `C_Anims_(15)` drawn first (`colmove.cpp:19`) | none |
| clipping | `Set_Window_(0,0,639,479)` + `Clip_On_` (`colmove.cpp:16-17`) | none |

So the one place the original *does* clip a pop figure is the cluster
in hand, and the one place it uses array order is the same.

---

## 8. Measurement — the second source

**Save**: `SAVE8.GAM` in the player's install, sha256
`ab70cc9a…70bd6`, byte-identical to
`~/orionlayer-fixtures/fixture_reference_3502.4.GAM` (the reference
save; 11 colonies, single race, every `max_farms` 255). Loaded
through the game's own Load dialog on 6 September 2026, colony
summary opened, and the original's 640x480 frame taken from the
Extension API's `VISUAL` — the game's own framebuffer, not a
screenshot of a window.

The frame is **palette-indexed**, and so are the sprites in
`raceicon_ref/`, so the whole comparison is on indices and never on
colours.

Measuring the leftmost opaque column of each figure individually
under-counts as soon as figures overlap — a covered figure is no
longer a whole sprite. So the measurement **predicts the entire
column** instead: it composites `n` sprites at the predicted pitch,
left to right with later on top and index 0 transparent, and compares
every pixel the composite makes opaque against the frame. That tests
the pitch, the origin, the row pitch, the z-order and the sprite
choice at once.

Rows on screen are the game's window; this save was showing
`_first = 1`, so slot 0 is the second colony by name.

### Prediction against measurement

| colony | job | n | predicted pitch | measured pitch | last figure x, predicted | opaque px compared | differing |
|---|---|---:|---:|---:|---:|---:|---:|
| Blucher III | food | 5 | 115/5 = **23** | 23 | 193 | 1425 | **0** |
| Blucher III | research | 7 | 114/7 = **16** | (covered) | 474 | 1637 | **0** |
| Draconis I | food | 1 | **30** (capped) | — | 101 | 285 | **0** |
| Draconis V | food | 5 | **23** | 23 | 193 | 1425 | **0** |
| Draconis V | industry | 4 | 122/4 = **30** | 30 | 326 | 1024 | **0** |
| Irra III | food | 7 | 115/7 = **16** | (covered) | 197 | 1923 | **0** |
| Irra III | research | 1 | **30** | — | 378 | 239 | **0** |
| Ktynga I | food | 3 | 115/3 = 38 → **30** | 30 | 161 | 855 | **0** |
| Sadak I | food | 3 | **30** | 30 | 161 | 855 | **0** |
| Sadak I | research | 1 | **30** | — | 378 | 239 | **0** |
| Vox IV | food | 3 | **30** | 30 | 161 | 855 | **0** |
| Vox IV | research | 2 | 114/2 = 57 → **30** | 30 | 408 | 478 | **0** |
| Waghi I | food | 3 | **30** | 30 | 161 | 855 | **0** |
| **Wolf II** | food | 8 | 115/8 = **14** | (covered) | 199 | 2084 | **0** |
| **Wolf II** | research | 5 | 114/5 = **22** | 22 | 466 | 1195 | **0** |
| Woz III | food | 4 | 115/4 = **28** | 28 | 185 | 1140 | **0** |
| Woz III | research | 3 | 114/3 = 38 → **30** | 30 | 438 | 717 | **0** |

**17 columns, 17 331 opaque pixels compared, 0 differing.**

"measured pitch" is the spacing between the figures a whole-sprite
match still finds; "(covered)" means the overlap is deep enough that
only the rightmost figure survives as a complete sprite — for those,
the composite is the measurement, and the predicted x of that last
figure is what the table names. Wolf II's eight farmers at pitch 14
put the last one at 101 + 7·14 = **199**, and a whole-sprite search
finds exactly one farmer, at 199.

The row geometry falls out of the same run: matched figures sit at
y = 38, 69, 100, 131, … — **top 38, pitch 31**, confirming
`colony_idx * 0x1f + 0x26` (`colsum.cpp:685`) to the pixel.

### The three regimes the brief asked for

- **below the threshold** — Ktynga I, Sadak I, Vox IV, Waghi I: three
  farmers, quotient 38, capped at 30, no overlap.
- **at the threshold** — Woz III: four farmers, 115/4 = 28, the first
  overlapping count in that column. Draconis V's four workers sit at
  30 in the same frame, because 122/4 is exactly 30 — the two
  columns disagree at the same count, which is what makes the
  per-column width real rather than decorative.
- **crowded** — Wolf II: eight farmers at 14, and Blucher III's seven
  scientists at 16.

### Order and sprite choice, measured separately

The reference save is single-race, so every figure in it is the same
sprite and the composite above cannot see a wrong ORDER. The natives
fixture (`SAVE2.GAM`, sha256 `b1f1aa46…08e2c8`) was loaded for that,
and the same composite run with **one sprite chosen per pop** through
`Colony_Pop_Anim_`'s rules, in `colonyicons.icon_pops` order:

| colony | job | n | pitch | entries drawn, left to right | differing px |
|---|---|---:|---:|---|---:|
| Draconis III | industry | 8 | 15 | 42 ×8 | 0 |
| Horus IV | food | 6 | 19 | 40 ×6 | 0 |
| Rha IV | food | 4 | 28 | 40 ×4 | 0 |
| **Urna I** | food | 4 | 28 | **40, 170, 170, 170** | 0 |
| Zhadoom III | food | 10 | 11 | 40 ×10 | 0 |
| Zhadoom III | industry | 4 | 30 | 42 ×4 | 0 |

**Urna I is the case that carries it**: the player's own Elerian
farmer (entry 40) is drawn first and the three natives (0xAA) after
it, at the same pitch, with the natives overlapping the farmer's
right side. Twelve columns, 0 differing pixels. That confirms the
grouping of §5, the left-to-right z-order of §4 and the sprite rules
of §5 in one measurement — and it confirms `colonyicons.icon_pops`
against pixels rather than against a re-reading of the same source.

---

## 9. Open for HD — **three of seven answered, 6 September 2026**

Questions the rules leave open. No recommendation was made here; the
answers below are Data's, taken at the colony-rebuild Stage 1 stop,
and they are recorded rather than argued.

> **1. Reproduce the overlap.** The squish formula is TRANSCRIBED —
> computed in native units, then multiplied by the same integer step
> the sprites are (`zoomtables.FIGURE_STEP`, 2 / 3 / 4). The extra
> HD width goes into the COLUMN RESERVATION (`colonybuild`), not into
> wider figure spacing. Any wider spacing later is a marked HD
> EXTENSION and never the default.
>
> **2. Therefore no replacement formula.** Question 2 does not arise.
>
> **5. The drop target and the popup anchor move to the FIGURE
> SLOT**, and one geometry function serves the draw, the hit test and
> the popup (decision 5). **The identity letter is dropped** — the
> original's own sprite carries identity, which is exactly what the
> single-track row could not do and what the letter was invented for.
> Which field gives the race index for a conquered pop is settled at
> the sprites-assets brief's stop, not here.

The remaining four stand as written.

1. **Reproduce the overlap, or use the HD width?** The original
   overlaps because 640x480 gave it 115 px for up to 42 figures. An
   HD row has room the original never had. Reproducing the pitch
   formula faithfully means deliberately hiding most of a crowded
   colony's figures on a screen wide enough to show them; using the
   width means a colony's row length stops matching the original's at
   the same pop count.
2. **If the width is used, what replaces the formula?** A fixed pitch
   at sprite width, the HD track's own slot arithmetic
   (`colonytrack.track_metrics`), or the original's formula with
   `right_x - left_x` scaled? Each gives a different answer to "how
   long is a row of twelve farmers".
3. **Hard clip, or let a column run into its neighbour?** The
   original does not clip and can overrun by a few px at extreme
   counts (§3). HD could clip at the group boundary, keep the
   overrun, or size the groups so it cannot happen.
4. **Which screen's food-column rule?** `max_farms`-driven spacing
   (colony main) and pop-driven spacing (colony summary) are both the
   original's, on different screens. An HD colony summary that shows
   farm shadows would have to pick one — and the shadows themselves
   are a third question, since they are figures with no pop behind
   them.
5. **Does the figure style keep the marker/cell geometry?** The job
   markers, drop targets and the identity letter are all defined on
   cells today (`colonytrack.row_boxes`). A figure run has no cells,
   so the drop target, the hover popup's anchor and the identity mark
   each need an answer that does not assume one.
6. **What is drawn for a held cluster?** The original removes the
   figures from the row and draws them at the mouse at a constant
   20 px pitch (§7). HD refuses to inject on the first click, so it
   has no cluster in hand to draw — the question is whether the
   preview imitates the removal, and if so, whether the surviving
   figures re-space as the original's do.
7. **Where does the sprite come from at runtime?** `raceicon_ref/` is
   a reference and is never shipped (decision 38). A figure style
   needs the player's own RACEICON.LBX at load time, or HD artwork of
   its own, or it does not ship.
