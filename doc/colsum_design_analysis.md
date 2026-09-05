# The Colonies screen: what it is, what OrionLayer may do with it,
# and what it should build

Written 5 September 2026, from a reading of **orion2re 1.60.0**
(`src/version.h`, git `cf4d9617`) and of this tree at commit
`a4dbee0`. It answers one question:

> What is the best Colony Management UI OrionLayer can give in 2026
> while keeping orion2re minimal, safe and maintainable?

Not "what would the best UI look like". A design that needs surgery
on the restored game is not a design this project can have.

**Marking, as in `doc/pop_order_reading.md`:** `CONFIRMED` is read
from the source; `INFERRED` is a conclusion drawn rather than read;
`UNVERIFIED` is one source with no live witness. A code reading may
carry a DRAWING decision and may not put anything in `core/structs`
as verified (decision 23).

**The finding that moves the whole cost calculation, first:** the
Extension API already ships every `s_colony` record whole
(ext_api.cpp:126-131), and `src/ext/` is OUR directory, untracked in
Joes' tree. The boundary this analysis has to respect is therefore
not "touch orion2re / don't" — see section 3.

---

## 1. The original system

### 1.1 The structure — CONFIRMED

`struct s_colony` (orion2.h:487), 361 bytes, 49 fields:

| Area | Fields |
|---|---|
| identity | `owner`, `allocated_to`, `planet`, `officer`, `outpost_flag`, `specialty`, `n_turns_existed` |
| population | `n_pops`, `pop[42]`, `pop_roundoff[10]`, `pop_growth[10]` |
| yield per head | `food2_per_farmer`, `industry_per_worker`, `research_per_scientist` |
| limits | `max_farms`, `max_population`, `climate` |
| economy | `production[4]`, `maintenance[4]`, `imports[4]`, `production_surplus`, `n_industry_taxed`, `n_industry_recyclers`, `n_food_replicated` |
| demand, itemised | `food2_needed_for_our_empire / _assimilated / _conquered / _natives`, `industry2_needed_for_our_empire / _androids / _assimilated / _conquered`, `food2_needed_for_empire[8]`, `industry2_needed_for_empire[8]` |
| building | `producing[7]`, `just_produced`, `production_spent`, `bought_outright`, `auto_building`, `buildings[49]`, `last_turn_building_destroyed` |
| condition | `morale`, `pollution`, `occupation_points`, `occupation_policy`, `military[2]`, `ground_strength`, `space_strength` |

**A trap inside it — CONFIRMED.** `max_population` (offset 225) is
written by the savegame reader and by nothing else in play
(savegame.cpp:268 and :322; no other writer exists). The live value
is always `COLCALC::Planet_Max_Population_For_Player_`
(colcalc.cpp:896). Reading the field would be reading a corpse, which
is why `colonyrows.max_population` mirrors the function instead.

### 1.2 Population units — CONFIRMED

One `uint32_t` per colonist, at most 42. Bit layout, `pop.h`:

| Mask | Meaning |
|---|---|
| `0x0F` `MASK_RACE` | player index 0..7, **8 = android, 9 = native** |
| `0x70` `MASK_ORIGINAL_OWNER` | original owner |
| `0x180` `MASK_PROF` | 0 farmer, 1 worker, 2 scientist |
| `0x200` `MASK_ASSIGNED` | assigned; cleared while in a held cluster |
| `0x400` `MASK_CONQUERED` | conquered |

`POP::Get_Effective_Player(pop, owner)` returns the colony owner for
8 and 9 and the nibble otherwise. **UNVERIFIED:** the meaning of 8
and 9 has three agreeing source sites and no live witness.

The array has no order — read from the writing side and recorded in
`doc/pop_order_reading.md`. Short form: appended on growth, replaced
by the last entry on removal, and shuffled outright
(invasion.cpp:721) when a colony completes Biospheres.

### 1.3 Assignment and movement — CONFIRMED

| Function | Where | Role |
|---|---|---|
| `Get_Selected_Pop_` | colsum.cpp:1006 | click -> pop index, through the scroll field's value (mode 3) |
| `COLMOVE::Get_Cluster_` | colmove.cpp:56 | takes every identical pop to the end of the array, clears `0x200`, recalculates |
| `Pops_Identical_` | colmove.cpp:106 | profession + state + nibble/conquered |
| `Send_Cluster_` | colmove.cpp:130 | the drop; same colony or transport |
| `Give_Colonist_New_Job_` | colmove.cpp:518 | **the assignment function**, four rules |
| `Clear_Cluster_` | colmove.cpp:39 | exact undo, reachable only by leaving the screen |

`Give_Colonist_New_Job_` is the "Farmer -> Worker" function the design
question asks about. It takes `(colony_idx, pop_idx, new_job,
inter_colony_transfer)` and is the only place in the game where a
profession changes.

### 1.4 Transfer between colonies — CONFIRMED

`SETTLER::Pop_Tries_To_Settle_` (settler.cpp:230) only DECIDES. It
fills `s_settler_settle_result` (orion2.h:2827): `can_settle`,
`eta_turns`, and eleven separate refusal flags —
`dest_owner_mismatch`, `source_blockaded`, `source_space_anomaly`,
`dest_is_outpost`, `only_one_pop_left`, `insufficient_freighters`,
`max_settlers_in_transit`, `source_plague`,
`no_room_at_destination`, `dest_blockaded`, `dest_space_anomaly`.
`SETTLER::Settle_Pop_` (settler.cpp:315) then acts. The in-transit
queue is `s_player.settlers[25]` with `settlers_freighted`, 64-bit
words whose masks are in `settler.h`.

Decision and action are already separate in the original. That is
exactly the shape decision 33 asks for and it is free.

### 1.5 Building, buying, derived values — CONFIRMED

- turns remaining: `COLONY::Calculate_Current_Production_Turn_Count_`
  (colony.cpp:445) -> `COLCALC::Colony_N_Turns_To_Produce_`
- cost: `Colony_Producing_Product_Cost_` (colcalc.cpp:1468); buy
  price: `Colony_Cost_To_Buy_Given_Product_` (colcalc.cpp:1472)
- the buy action: `COLONY::Tested_Colony_Buys_Outright_`, reached
  through `_list_buy_fields[i]` (colsum.cpp:302)
- building NAMES are not in the source: `kEmptyName` in
  techdata.cpp:25, filled at runtime from `techname.lbx`
  (techinit.cpp:71). Costs and numbers ARE in that table.
- morale: `COLCALC::Colony_Morale_` (colcalc_main.cpp:6) writes
  `colony->morale` (unit: 5 %) and, given a `STRBUILD::s_builder*`,
  emits the complete itemised explanation as formatted text.
- production: `COLCALC::Colony_Job_Production_` (colcalc_main.cpp:651)
  fills `s_colony_job_production` — base, racial bonuses, tech
  applications, buildings, food/artifact/intelligence bonuses,
  gravity, conquered penalty, pollution, morale, government,
  blockade, officer, difficulty, final. **No write to `colony->`
  occurs in its body, and the chain below it takes `const s_colony*`
  (colcalc.cpp:1444), so the read-only property is guaranteed by the
  compiler rather than by a reading.**

### 1.6 Selection, sorting, window, navigation — CONFIRMED

- selection: `COLONY::_g_colony_n`, assigned from the SCANNED
  (hovered) field, not the clicked one (colsum.cpp:880-890)
- sorting: `Sort_Col_List_` (colsum.cpp:363), `Switched_cmp_`
  (:378-401), seven keys, direction baked in as a literal, no
  toggle. It runs at exactly two places — screen entry (:110) and
  the sort handler (:830) — and never on its own.
- window: `_first` + `_list_col[10]`, `Update_Col_List_` (:348),
  steppers `_x_fields[1]`/`[2]` (:790-800), thumb drawn by
  `Draw_Bar_Indicator_` (:747-771)
- navigation: the name field leaves for `SCREEN_COLONY`
  (:912-920), the producing field for `SCREEN_QUEUE_POPUP` (:922-944)
- recalculation: `COLCALC::Colony_Calculation_` (colcalc.cpp:1580).
  After a COMPLETE drop it runs (`Col_Calc_Wrapper_`,
  colmove.cpp:461); the early `return` on a refusal (:168-173)
  SKIPS it, so a refused partial drop also leaves the derived values
  stale — on top of the modal and the held cluster.

---

## 2. What OrionLayer does today

```
orion2re                    Extension API             OrionLayer
──────────────────────────────────────────────────────────────────────
_colony[i] (361 B, whole) ─► STATE, every tick ─────► colony.SPEC (verified)
_player[8], _planet[], _star[]                        colonyrows.build_rows
fields::_fields[]         ─► FIELD_LIST (geometry) ─► click targets, stepper ids
g_present_surface         ─► VISUAL (640x480 idx) ──► _first, read off the thumb
                                                       ▼
                                            HD drawing, selection, preview
                                                       ▼
_pending_field  ◄── ACTIVATE_FIELD ◄───────────────── window steps
SDL event       ◄── INJECT_CLICK   ◄───────────────── the two pop clicks, RETURN
SDL key         ◄── INJECT_KEY     ◄───────────────── the seven sort keys
```

**Robust:** the read path (whole struct on the wire, verified spec);
the move chain (every step waits for its effect, interlocked against
the wrong cluster); the five rules mirrored before anything is sent.

**Fragile, in order:**

1. **`_first` is read out of pixels** (`colonyfirst.py`, palette index
   229 in the framebuffer). A channel that depends on artwork and
   palette.
2. **The order binding is an assumption.** HD sorts its own rows and
   pushes the key; that both lists agree is nowhere readable, and a
   human can separate them in the game's own visible window.
3. **Two duplications of real game logic:** `max_population`
   (mirrors colcalc.cpp:896) and `drawn_production` (mirrors the
   four branches in coldraw.cpp:60).
4. The held cluster is INFERRED (a scan of every colony for
   unassigned pops), not read.
5. `INJECT_CLICK` presupposes a locally patched binary.

---

## 3. The capability map, with the boundary drawn correctly

The usual four levels assume "level 2 = modify orion2re". That is
not the boundary here:

| Level | What it actually costs |
|---|---|
| **1** | OrionLayer alone. Everything already in the snapshot — which is the WHOLE of `s_colony`. |
| **2** | Additive lines in `src/ext/ext_api.cpp`. **Diverges from nothing** — that directory is ours and untracked in Joes' tree. Cost: a rebuild and a protocol version. |
| **3** | A change to a file Joes owns. **CORRECTED 5 September 2026: five files, fourteen hunks** — see `doc/orion2re_tree_comparison.md`. Thirteen of the fourteen are inside `#ifdef ORION2RE_EXT`; the fourteenth is the documented crash fix (open fix 5). The "exactly one" this table used to claim was a statement about ONE PATCH read as a statement about the whole tree. |
| **4** | Game logic. Rejected. |

| Capability | Level | Evidence |
|---|---|---|
| different row rendering | 1 | presentation only |
| individual population cells | 1 | `pop[42]` is on the wire |
| job colours | 1 | `MASK_PROF` |
| race markers | 1 | nibble, `_player[i].race` |
| android / native markers | 1 | nibble 8/9 |
| conquered marker | 1 | `0x400` |
| empty capacity | 1 today (mirrored), 2 to stop mirroring | colcalc.cpp:896 |
| click-based assignment | **1, already built** | runs live through two injected clicks |
| group reassignment | 1 | `Get_Cluster_` mirrored and checked |
| drag and drop | 1 technically / **reject** | section 9 |
| sorting, filtering | 1 | filtering is HD-only; sorting must keep the binding |
| warnings, production indicators | 1 | `production`, `maintenance`, `imports`, `pollution`, `morale` |
| hover tooltip / inspector | 1 | `spare_panel` exists and is empty |
| popup under the row | 1 technically / **reject** | section 10 |
| expandable rows | 1 technically / **reject** | reflows the click frame |
| detailed colony information | 1 | all in the struct |
| building name, turns, buy price | 1 with an extractor + transcription, or 2 | techinit.cpp:71; colony.cpp:445; colcalc.cpp:1468/1472 |
| colony-to-colony transfer | **2** | otherwise HD mirrors eleven refusal rules |
| production breakdown / "what if" | **2** | `Colony_Job_Production_`, const-correct |
| build selection, buying | 1 (click the original's field) or 2 | an HD build screen would be 4 |
| OrionLayer's own job counts | **4 — reject** | section 16 |

---

## 4. The budget

**Further than the question assumes.** The read side is solved, the
write side already exists as a proven two-click chain, and the rest
is presentation. Without one line in a file Joes owns: a completely
new row rendering, two-dimensional cells, preview, movement,
sorting, filtering, warnings, a persistent inspector and a transit
display. What buys robustness on top of that is a handful of
additive values in OUR OWN API file.

---

## 5. Original actions to reuse rather than recreate

| Wanted | Existing function | Reusable? |
|---|---|---|
| Farmer->Worker, Worker->Scientist, … | `Give_Colonist_New_Job_` (colmove.cpp:518) | **Yes, already in use** through the two clicks |
| move several units | `Get_Cluster_` (colmove.cpp:56) | **Yes** — and the group size is selectable: the clicked cell and every cell after it in its group |
| transport | `Pop_Tries_To_Settle_` + `Settle_Pop_` | decision and action are already separate |
| colony selection | `_g_colony_n` from the hover | yes |
| build selection | `SCREEN_QUEUE_POPUP` via `_list_col_prod_fields[i]` | yes, as a hand-off |
| buying | `Tested_Colony_Buys_Outright_` via `_list_buy_fields[i]` | yes |
| sorting | `Sort_Col_List_` through the seven hotkeys | yes, in use |
| navigation | `_list_fields[i]` -> `SCREEN_COLONY` | yes; deliberately swallowed today |
| turns / cost | `Calculate_Current_Production_Turn_Count_`, `Colony_*_Cost_` | only through a new read command |
| maximum population | `Planet_Max_Population_For_Player_` | mirrored today; level 2 would end the duplication |

---

## 6. What OrionLayer can safely read

| Information | In orion2re | Accessible today | Easy to expose | Risk |
|---|---|---|---|---|
| colony name | via `planet` + `star` | **yes** | — | none |
| planet type, climate, size, gravity, minerals | `s_planet_data`, `colony.climate` | **yes** | — | climate: the COLONY's field, not the planet's |
| population / maximum | `n_pops` / computed | yes / **mirrored** | level 2 | the record's `max_population` is dead |
| farmer / worker / scientist | `pop[]` `MASK_PROF` | **yes** | — | none |
| race per pop | `pop[]` nibble | **yes** | — | 8/9 without a live witness |
| android status | nibble 8 | **yes** | — | as above |
| conquered | `0x400` | **yes** | — | none |
| morale | `colony.morale` (x5 %) | **yes** | breakdown: level 2 | none |
| food / industry / research / BC | `production[4]` | **yes** | — | drawn value != stored value (coldraw.cpp:60) |
| surplus / demand | `maintenance[]`, `imports[]`, the eight `*_needed_for_*` | **yes** | — | the `imports` sign trap, open fix 7 |
| pollution | `pollution` | **yes** | — | none |
| growth | `pop_growth[10]` | **yes** | — | an accumulator, not pops per turn |
| current construction | `producing[7]` | yes (index) | name: extractor | names are the user's own data |
| turns remaining | computed | **no** | level 2 | rebuilding it would be a duplicate |
| buildings | `buildings[49]` | **yes** | names: extractor | none |
| income | `production[ECON_BC]`, `n_industry_taxed` | **yes** | — | none |
| planet specials | `planet_special`, `specialty` | **yes** | — | `specialty` unexamined |
| **`_first`, sort index, `_list_col[10]`, selection, held cluster** | colsum.h:9,13,18; colony.h:407; colmove.h:5 | **no** | **level 2, trivial** | none — all `extern` |

---

## 7. The current HD design

**Keep:** the row with the right-aligned name (the marked deviation
buys the name column), the three zone colours, the dashed free
slots, the "No Farming" line under the bar, the sidebar,
`output_panel` as a transcription, the galaxy inset, the sort headers
with no direction arrow.

**Three things that cost measurably:**

**The 42-slot track.** Measured against the reference save: the BEST
colony reaches 22 of 42 slots. **48 % of every row is permanently
unreachable in that game**; Draconis I uses 4 of 42. The reason for
42 — one cell is the same size in every row, and `POP_LIMIT_CAP` is
the engine's own ceiling — survives if the track's WIDTH is derived
from the largest reachable `max_pop` in the empire instead. The
comparability property is unchanged; only the constant moves.

**Row count does not scale with the display.** `Layout.scale =
min(scale_x, scale_y)` with letterboxing (core/layout.py:24), so at
3440x1440 the screen is drawn 2560x1440 with 440 px of bar on each
side, and ten rows remain ten rows — larger ones. More rows cost
either `row_height` (level 1, one number in `layout.json`: 58 -> 46
gives thirteen) or new frame artwork (decision 3).

**The bar does not know identity.** `build_rows.jobs[]` counts
professions and counts UNASSIGNED pops with them, which the original
does not draw (coldraw.cpp:336). Correct while nothing is held, and
still the wrong source for a cell.

---

## 8. The visualisation problem

Two dimensions, and the source says how many classes there really
are — CONFIRMED, `Colony_Pop_Anim_` (colony.cpp:1268):

| Class | Sprite in the original |
|---|---|
| conquered | static race portrait, `race*13+12` |
| native | **one** sprite `0xAA` for every race |
| android | **one** sprite `0xA9` for every race |
| otherwise | `race*13 + job*2 + 1`, per race AND per job |

The original carries both dimensions in the sprite and never in a
colour. Four classes, not two.

**Fill = occupation, mark = identity, and the mark appears only when
it says something.** In a typical colony over 90 % of cells are "own
race, normal"; those must stay quiet or scanning twenty rows dies.
So: no mark for the normal case; one glyph for android; another for
native; a race letter for a foreign race; a corner triangle in
addition for conquered. Border coding, textures and silhouettes are
out — they cost legibility at a 20 px cell and collide with the
dashed outline of a free slot.

---

## 9. Interaction

**Click-click stays**, on a source argument rather than piety: the
original has no drag (colsum.cpp:851-870), the chain runs live, and
every other model needs either an invention on the game side or more
injected clicks.

The important find is inside `Get_Cluster_`: it takes the clicked
unit AND every identical one after it. So "how many do I move" is
already selectable — the last cell of a group moves one, the third
from last moves three. That is not a limitation to work around but a
mechanism the preview already teaches: the highlighted cells ARE the
answer. No change needed anywhere.

Rejected: drag and drop (two more states, no gain over two clicks,
and cancelling gets harder); `+/-` steppers (one pop each, so n
two-click chains for n pops); clicking group boundaries
(undiscoverable at 20 px).

---

## 10. Contextual information

**AMENDED 5 September 2026, and the amendment is a correction to
this section rather than a note on it.** The paragraph below rejected
"popup under the row" in one move. It conflated two different things,
and only one of them is refused by the argument it gives:

- a box that INSERTS itself between two rows and pushes the rows
  below it down — **out**, by the argument that follows;
- a box that OVERLAYS the rows below it and moves nothing — **not
  settled by that argument at all**. It obscures neighbouring rows
  while it is open, which is a legibility question and is decided by
  looking, not by citing decision 46.

The distinction matters because the second variant is the one a
reviewer is likely to mean, and this document as first written would
have been cited to rule it out. It is not ruled out. Both it and the
inspector go to a render comparison; see the status document's open
design questions.

**A box that reflows the list: no**, and the reason is technical. It
moves the rows below it, and the list IS the click frame: their
position is what `GameWindow` maps onto a slot of the game's ten-row
window. Any HD row shifting against that window is precisely the
invisible failure decision 46 exists for. Expandable rows fail at
the same point, and for them the reflow is the whole idea rather
than a side effect.

**Preferred, but not decided: a persistent inspector in
`spare_panel`, driven by hover.** Hover is the original's own
selection semantics (colsum.cpp:880-890 reads the SCANNED field), the
panel exists, is empty by decision, and owes the original nothing;
and it sits outside the list, so it can obscure nothing and move
nothing. Its cost is mouse travel: the answer appears far from the
question, which is exactly what an overlaid tooltip buys back. That
trade is not decidable from the source, so it is not decided here.

---

## 11. Worth doing, and not

**HIGH VALUE / LOW COST**

1. Track width from the empire maximum instead of 42 — half a row
   recovered.
2. Lower `row_height`: thirteen rows instead of ten.
3. Identity marks in the cell (four classes, quiet by default).
4. The inspector in `spare_panel`, hover-driven.
5. Warnings from fields already present: food deficit, pollution,
   morale below zero, "No Farming", unassigned pops.
6. Filters (starving / idle / growing) — HD-only, no binding to the
   game's list.
7. A transit display from `s_player.settlers[25]` — information the
   original barely surfaces.

**HIGH VALUE / ACCEPTABLE COST** (all additive in `src/ext/`)

8. `_first`, `_g_sort_index`, `_list_col[10]`, `_g_colony_n`,
   `_cluster_colony_n` in the snapshot.
9. A read command for `Colony_Job_Production_` — a real breakdown,
   and what a move would be worth.
10. A read command for `Pop_Tries_To_Settle_` — the transfer UI with
    no mirrored rules.
11. A read command for turns / cost / buy price — the building
    column finished.
12. A `techname.lbx` extractor for building names.

**NOT WORTH IT**

- An HD build screen or a building list with actions (level 4,
  duplicates the queue).
- Drag and drop.
- Popup under the row; expandable rows.
- A modifier to move exactly one pop — already available by clicking
  the last cell of a group.
- Optimisation advice ("best split") — needs the simulator twice.
- Any independently held job count (section 16).

---

## 12. The recommended design

**Layout.** The frame stays. The list on top (`list_area`);
bottom left `output_panel` (the selected colony's four production
values, a transcription); bottom middle `spare_panel` as the
INSPECTOR; bottom right the galaxy inset; the sidebar with the
empire totals; the seven sort headers and RETURN below.

**The row, left to right**

1. **Name block**, right-aligned, with `climate  pops/max` under it.
2. **Status strip**, about 10 px: coloured dots only when something
   is wrong (starvation, pollution, morale, idle pops).
3. **Population track**, length = the empire's maximum, cell size
   equal everywhere: filled cells in the occupation colour, free
   slots dashed to `max_pop`, nothing beyond but the baseline.
4. **Building column**, 190 reference px: name, then `- n t` and
   "Buy" where it applies.

**The cell.** Fill = occupation. Mark = identity, only when it
differs from "own race, normal": android glyph, native glyph, race
letter for a foreign race, plus a corner triangle for conquered.

**Interaction**

- *hover a cell* — the inspector shows the colony, that unit
  (occupation, race, status) and WHAT A CLICK WOULD TAKE. Nothing is
  sent.
- *click a cell* — local selection; the cells that would travel with
  it light up. Nothing is sent.
- *click a job band* — all five rules, then both clicks as one
  gesture, each step confirmed against its effect.
- *right click / click into empty space* — discard (marked HD
  extension).
- *click a sort header* — the hotkey goes to the game, HD re-sorts.
- *click the name* — swallowed today; the hand-off the day an HD
  colony screen exists.
- *transfer* — NOT on a second click into another row at this stage;
  it waits for the read endpoint in 11.10.

**Permanently visible:** name, climate, pops/max, the job split,
free capacity, warnings, construction. **Contextual:** breakdowns,
per-pop identity, growth, pollution, buildings, transfer targets.

---

## 13. Implementation impact

| Feature | Impact |
|---|---|
| track scale, row height, status strip, marks, filters | OrionLayer only |
| inspector + hover | OrionLayer only |
| warnings, transit display | OrionLayer only |
| click-click movement | OrionLayer only (already built) |
| five screen-state values in the snapshot | tiny orion2re hook, our own file |
| production / transfer / cost read commands | tiny orion2re hook, our own file |
| building names | OrionLayer only (extractor) |
| an HD build screen | significant — not recommended |

**Overall: LOW-MODERATE**, and the moderate part is entirely inside
`src/ext/`. Joes' files gain nothing beyond what they already carry —
which is five files and fourteen hunks, not one
(`doc/orion2re_tree_comparison.md`), thirteen of them ifdef-guarded.

---

## 14. HIGH-LEVERAGE INTEGRATION POINTS

**H1 — five state values in the snapshot.** `COLSUM::_first`,
`_g_sort_index`, `_list_col[10]` (colsum.h:9,13,18),
`COLONY::_g_colony_n` (colony.h:407), `COLMOVE::_cluster_colony_n`
(colmove.h:5). All `extern`, all additive in our own file. It
retires the pixel reading of the scroll thumb ENTIRELY; it replaces
window planning with reading; `_list_col[i]` says directly which
colony sits in slot *i*, so the row-to-slot mapping stops being an
inference; and the held cluster is read instead of deduced. **The
best trade in this document.** Caveat: `_list_col` is only
maintained while the colony summary is up, so a client may trust it
only when `current_screen == 20`.

**H2 — `COLCALC::Colony_Job_Production_` (colcalc_main.cpp:651).**
Fully itemised production per job. The chain below it takes
`const s_colony*` (colcalc.cpp:1444), so evaluating a scratch copy is
safe by the type system. Enables real explanations and "this move is
worth +3 industry, -2 food" with no re-implemented economics.

**H3 — `SETTLER::Pop_Tries_To_Settle_` (settler.cpp:230).**
Decision, ETA and eleven named refusals, side-effect free. Enables
the whole transfer UI with refusal-before-send and not one mirrored
rule.

**H4 — `COLCALC::Planet_Max_Population_For_Player_`
(colcalc.cpp:896).** Ends the one real logic duplication in the tree.

**H5 — `Calculate_Current_Production_Turn_Count_` /
`Colony_Producing_Product_Cost_` /
`Colony_Cost_To_Buy_Given_Product_`.** Finishes the building column
instead of recomputing it.

**H6 — `COLCALC::Colony_Morale_` with a builder
(colcalc_main.cpp:6).** The game already writes the morale
breakdown as text.

---

## 15. Synchronisation traps

The current system keeps NO authoritative copy: it draws from the
snapshot, plans from the snapshot, and re-reads the snapshot after
every move. That stays the rule.

Three real risks, all named:

1. **Order.** HD re-sorts from every snapshot; the game sorts only
   when a sort field is activated. Healed today by pushing the sort
   key at the start of every move; with **H1** it would be readable
   instead of healed.
2. **Derived values after a refused move.** The early `return` in
   `Send_Cluster_` (colmove.cpp:168-173) skips `Col_Calc_Wrapper_`
   (:461), so production would stand still. HD refuses partial moves
   before sending and never reaches that state.
3. **Any future optimistic UI** that draws a move before the
   snapshot confirms it. Explicitly forbidden: the only permitted
   anticipation is the PREVIEW, which asserts nothing.

---

## 16. Verdict

- **How much of the ideal UI fits inside OrionLayer?** Nearly all of
  the presentation, cells, marks, preview, selection, movement,
  sorting, filters, warnings and the inspector. The read side is
  already complete.
- **The most useful hooks:** H1, H2, H3, H5, H4.
- **Reuse, do not recreate:** `Give_Colonist_New_Job_`,
  `Get_Cluster_`/`Send_Cluster_`, `Pop_Tries_To_Settle_`/
  `Settle_Pop_`, `Sort_Col_List_` through the hotkeys,
  `Tested_Colony_Buys_Outright_`, `SCREEN_QUEUE_POPUP`.
- **Biggest gain per unit of work:** the hover inspector plus
  warnings — no game side at all. For ROBUSTNESS: H1.
- **Attractive and to be refused:** an HD build screen.
- **Do pops stay individual cells?** Yes. The engine keeps them
  individually, the selection works on them individually, and the
  cell is the only place where both dimensions meet without extra
  area.
- **Occupation + race + android at once:** fill = occupation, mark =
  identity, mark only where it differs from the normal case, four
  classes as in the original.
- **Best assignment method:** click-click, unchanged, with the group
  size chosen by which cell is clicked.
- **Secondary information:** OPEN. A persistent inspector driven by
  hover is preferred here; an OVERLAYING tooltip under the row is
  not excluded and is decided by rendering both (section 10, as
  amended). Only the REFLOWING variants — an inserted box, an
  expandable row — are refused, and by decision 46 rather than by
  taste.
- **What survives:** the row structure, the name block, the zone
  colours, free slots, "No Farming", the sidebar, `output_panel`,
  the inset, the sort headers, the whole move chain.
- **What is replaced:** the 42-slot track width, `row_height`, the
  job count as the cell source, the pixel reading of `_first`.
- **Overall impact on orion2re: LOW-MODERATE**, additive and inside
  `src/ext/` — confirmed against a real cross-tree diff on
  5 September 2026, which also corrected this document's count of
  existing hunks in Joes' files from one to fourteen
  (`doc/orion2re_tree_comparison.md`).

### RECOMMENDED COLONY MANAGEMENT ARCHITECTURE

1. orion2re stays authoritative; OrionLayer is presentation and
   intent.
2. Read only from the snapshot; no second model of the state.
3. Every action is: mirror the rules -> refuse or send -> wait for
   the effect -> re-read -> draw.
4. Write only through original functions, triggered by a click, a
   key or a field activation.
5. The row is the unit; the list never reflows, because it is the
   click frame.
6. One pop is one cell: fill = occupation, mark = identity, quiet in
   the normal case.
7. The track is as long as the empire's maximum, and a cell is the
   same size everywhere.
8. Free capacity is shown; unreachable capacity is not.
9. Selection is local; only the target click sends, and then both
   clicks go as one gesture.
10. The group size lives in the click position, and the preview
    teaches it.
11. Discarding is always possible because the preview injected
    nothing — a marked extension.
12. Secondary information lives in the inspector, never in the list.
13. Warnings come from existing fields and sit on the left, where
    the eye starts.
14. Order and window are established before every move, never
    remembered — and read rather than established once H1 exists.
15. New values arrive additively through `src/ext/`; Joes' files stay
    untouched.
16. Computed values are asked for, not rebuilt; every remaining
    duplicate carries its reason.
17. Every deviation from the original is marked in the module, in the
    status document, and in a check.
