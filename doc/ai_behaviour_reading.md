> **Provenance (work order 163, 22 September 2026).** A source reading in
> one timeboxed session. **No code was written, nothing was driven, and
> nothing in either tree was changed** except this file. Every statement
> below is *source reading* against `~/orion2re` at
> `ENGINE_VERSION[] = "1.60.0"` (`src/version.h:10`), and every claim
> carries its file and line. Breadth was chosen over depth by the order,
> so most functions below were located and their inputs identified, not
> read line by line; section 8 says exactly what was not read.
> Verify before building on it (CLAUDE.md, "You own every detail").

# What can be modded about orion2re's AI behaviour — a reading

**The one-sentence answer: nothing, today — and the cheapest opening is
smaller than it looks.** Every number an AI player decides with is a C++
literal or a C++ table; none of it comes from an LBX or from a data
file. But orion2re already has a configuration-and-mod system with the
exact shape those tables need, the tables are already `extern` in
headers, and adding them to it is a change to **one schema file plus a
regeneration** — with no edit to any AI source file at all.

---

## 1. Where the AI decides anything

**One driver, one place.** `NEXTTURN::Next_Turn_Calc_` (nextturn.cpp:91)
runs the whole AI turn as a flat ordered list, nextturn.cpp:102-124:

| # | line | call | what it decides |
|---:|---|---|---|
| 1 | :102 | `AIDATA::Compute_AI_Data_` | nothing — it builds the caches every decision below reads |
| 2 | :103-105 | `DIP_SCRN::Resolve_Delayed_Diplomacy_Orders_`, `Set_Opportunity_Attacks_`, `diplomac::Clear_Diplomacy_Messages_` | carries over the human's diplomacy from last turn |
| 3 | :106 | `npcdiplo::NPC_Diplomacy_` | **diplomacy and treaty-breaking** |
| 4 | :107 | `diplomac::Diplomacy_Growth_` | relations drift |
| 5 | :108 | `aileader::Do_AI_Leaders_` | officer hiring and assignment |
| 6 | :109 | `AIBUILD::Compute_Empire_Building_Needs_` | **what the empire needs built** |
| 7 | :110 | `aidudes::All_Colony_AI_` | **per colony: jobs, taxes, build queue** |
| 8 | :111 | `AIMOVE::Move_All_AI_` | **fleet movement, attacks, sneak attacks** |
| 9 | :112 | `COLONIZE::All_AI_Colonize_` | **colonisation** |
| 10 | :113 | `aitech::All_AI_Tech_Select_` | **research** |
| 11 | :118 | `spy::Resolve_Spies_` | **espionage** |
| 12 | :124 | `aitech::Apply_Evolutionary_Upgrades_` | free tech at high difficulty |

Combat is not in this list: it runs inside a battle, from
`CMBTAI::Do_Auto_Ship_Turn_` (cmbtai.cpp:573).

**The loop that separates an AI player from the human is one test,
repeated:** `plr->objectives != PLAYER_OBJECTIVE_HUMAN`
(aidudes.cpp:23, and the same comparison in every area). There is no AI
"controller" object — the AI is the set of functions that run for a
player whose `objectives` is not 100.

### Area by area

| area | the function that DECIDES | supporting |
|---|---|---|
| **Expansion / colonisation** | `AIMOVE::Assign_New_Colony_Ship_Destinations_` (aimove.cpp:1385) picks the target; `COLONIZE::AI_Colonize_` (colonize.cpp:245) plants it | `AIMOVE::Get_Colonizable_Planets_` :356, `Best_Uncolonized_Undestined_Planet_` :190, `AIDATA::Uncolonized_Planet_Worth_To_Player_` (aidata.cpp:1292), `Compute_Contextual_Planet_Values_` :896 |
| **What it builds** | `AIBUILD::Colony_Building_Score_` (aibuild.cpp:530-926) scores every building; `Assign_Colony_New_Building_` :944 takes the winner | `Compute_Needs_` :208, `Compute_Colony_Ship_Need_` :188, `Compute_Freighter_Need_` :194, `Empire_Buy_Outright_` :415 |
| **Colony jobs and taxes** | `aidudes::Colony_AI_` (aidudes.cpp:91) and `Assign_Empire_Building_` :799 | `Do_Unblockaded_Colony_` :549, `Do_Blockaded_Colony_` :614, `Assign_Required_Colonists_` :688, the six `Sort_Pops_*` comparators |
| **Research priorities** | `aitech::AI_Tech_Select_` (aitech.cpp:360) asks `NEWTECH::Choose_Tech_Application_` (newtech.cpp:381) | `Compute_AI_Tech_Info_` (aitech.cpp:135) builds the deltas the choice weights |
| **Diplomacy, treaties, treaty-breaking** | `npcdiplo::NPC_Diplomacy_` (npcdiplo.cpp:72) drives: `NPC_Threats_` :83, `NPC_Declarations_Of_War_` :148, `NPC_Tech_Exchange_` :376, `NPC_Peace_Negotiations_` :443, `NPC_Treaty_Hatred_` :490, `NPC_Surrender_Check_` :570, `NPC_To_NPC_Treaty_Negotiations_` :773 | `diplomac::Change_Relations_` (diplomac.cpp:1019), `Break_Treaties_` :1175, `Limit_Treaty_Modifiers_` :1344, `Set_Demands_` :1814 |
| **War declaration and sneak attacks** | `diplomac::Sneak_Attack_Evaluations_` (diplomac.cpp:46) scores it, `Sneak_Attack_Or_Declare_War_` :647 acts, `Declare_War_` :863 | `diplomac::NPC_Sneak_Attacks_` :239, `AIMOVE::Launch_Sneak_Attack_` (aimove.cpp:33) |
| **What it attacks** | `AIMOVE::Compute_Attack_Worthiness_` (aimove.cpp:2218-2424) | `AI_May_Attack_Player_` :2200 (the legality gate), `Player_Is_Hostile_To_Player_` :2156, `Find_Best_Attack_From_Star_` :1876, `Launch_Attacks_` :293, `Interceptions_` :1489, `Move_To_Stage_Points_` :700, `AISTAGE::Compute_Defensive_Stage_Points_` (aistage.cpp:5) |
| **Invasion** | `aibomb::AI_Invasion_Will_Succeed_` (aibomb.cpp:5) — 46 lines, the whole file |
| **Combat tactics** | `CMBTAI::Do_Auto_Ship_Turn_` (cmbtai.cpp:573) per ship: `Get_Player_Mode_` :320 (stand off or close), `Choose_Target_` :957 / `Target_Ship_Value_` :1037, `Auto_Move_Ship_` :1223 / `Evaluate_Possible_Move_` :1580, `Retreat_Check_` :755, `Boarding_Action_Type_` :1331, `Ai_Self_Destruct_Check_` :2329 | `AIPOWER::*` (aipower.cpp) is the strength arithmetic every one of them asks |
| **Ship design** | `aidesign::Auto_Design_Ship_` (aidesign.cpp:1425) | `Get_Ship_Class_` :710, `Add_*_To_Design_` |
| **Espionage** | `spy::Allocate_AI_Spies_` (spy.cpp:171) | |
| **Reaction to the human** | three distinct places, section 6 | |
| **Leaders** | `aileader::Do_AI_Leaders_` (aileader.cpp:4) | |
| **Advanced-civilisation start** | `ADVCIV::Choose_Adv_Civ_Planets_` (advciv.cpp:234) | |

---

## 2. Where the numbers live

Four categories were asked for. **The fourth is empty: no AI decision
number is loaded from an LBX or from any data file.** `KEN` is the only
AI-adjacent file that opens one at all, and only for text
(`KENTEXT.LBX`, ken.cpp:120-125) and a palette animation
(ken.cpp:95-102).

### (a) Named tables — C++ arrays with a name and an `extern` in a header

These are the ones that matter, because a table with a name is the
cheapest thing to move.

| table | file:line | shape | what it steers |
|---|---|---|---|
| `KEN::_personalities` | ken.cpp:4-20 | `uint8_t[14][10]` | **which personality each race gets, per difficulty roll** |
| `diplodef::_personality_relation_modifiers` | diplodef.cpp:4 | `int16_t[8]` = `{-50,-20,-20,0,20,30,-70,0}` | how much each personality likes anybody |
| `diplodef::_threat_demand_chance` | diplodef.cpp:5 | `int16_t[10]` = `{0,30,80,20,10,0,80,0,0,0}` | chance a threat comes with a demand |
| `diplodef::_personality_threat_modifiers` | diplodef.cpp:6 | `int16_t[10]` = `{40,30,20,5,0,-10,50,0,0,0}` | how readily it threatens |
| `diplodef::_personality_reward_proposal_chance` | diplodef.cpp:10 | `int16_t[10]` = `{0,5,5,10,15,20,0,0,0,0}` | chance it offers a reward instead |
| `diplodef::_personality_max_threats` | diplodef.cpp:11 | `int16_t[10]` = `{1,2,3,3,4,5,2,0,0,0}` | how many threats before it acts |
| `diplodef::_personality_break_treaty_war` | diplodef.cpp:12 | `int16_t[10]` = `{100,50,50,100,50,20,0,0,0,0}` | chance breaking a treaty means war |
| `diplomac::_starting_relations` | diplomac.cpp:17-32 | `int16_t[196]` = 14x14 | **every race's opening opinion of every other** |
| `diplomac::_personality_peace_duration` | diplomac.cpp:34 | `int16_t[12]` = `{5,10,20,5,50,40,5,…}` | how long it keeps a peace |
| `diplomac::_personality_break_peace_treaty_chance` | diplomac.cpp:38 | `int16_t[8]` = `{7,10,1,1,0,0,5,0}` | chance it breaks one |
| `diplomac::_personality_sneak_attack_modifiers` | diplomac.cpp:42 | `int16_t[8]` = `{-10,-5,-3,0,20,20,-10,0}` | how much it likes a sneak attack |
| `AIBUILD::_difficulty_ship_design` | aibuild.cpp:4 | `uint8_t[12]` = `{2,10,35,50,115,…}` | **the ship-upgrade cheat's size, per difficulty** |
| `AIBUILD::_difficulty_intel_bias` | aibuild.cpp:5 | `int8_t[8]` = `{1,1,2,3,4,0,0,0}` | how much of the human's real fleet strength the AI is allowed to see |
| `AIBUILD::_player_ship_size_table` | aibuild.cpp:6 | `uint8_t[9]` = `{1,2,3,5,8,13,0,0,0}` | fleet-size weighting by hull |
| `aidesign::_min_weapon_count_table` | aidesign.cpp:4 | `int16_t[8]` = `{1,2,3,5,7,10,0,0}` | minimum weapons per hull class |
| `NEWTECH::_tech_research_level_values` | newtech.cpp:6 | `int32_t[30]` | what a research level is worth when choosing |
| `aidesign::_*_spcl` (14 tables) | aidesign.cpp:6-186 | `s_spcl[…]` | which specials each design theme reaches for |

Every one of them is declared `extern` in its header
(diplodef.h:6-14, diplomac.h:12-14, aibuild.h:4-6, ken.h:28,
newtech.h:9) — which is exactly what the configuration binding in
section 4 needs, and is why that change is as small as it is.

### (b) Bare literals inside a decision — the bulk of it

This is where most of the behaviour actually is, and it is the part a
data file cannot reach without the function being rewritten.

* **`AIBUILD::Colony_Building_Score_` (aibuild.cpp:530-926)** — the
  single most consequential AI function in the game, 397 lines, and it
  contains **228 bare numeric literals**. Every building's desirability
  weight is one of them; `player->bc >= 1500` and the cap `bc_score >
  10` at :543-547 are two examples out of hundreds.
* **`AIMOVE::Compute_Attack_Worthiness_` (aimove.cpp:2218-2424)** —
  **77 bare literals** decide whether a colony is worth attacking.
* `AIPOWER::Ship_Strength_Vs_Planetary_Shield_` carries its own
  `uint16_t shield_reductions[4] = {2,7,12,22}` as a *function-local*
  array (aipower.cpp:254) — a table with no name outside its function
  and no header, so it is a literal for every purpose here.
* `aidudes::Do_Ship_Upgrade_Cheats_` gates on `MOX::_stardate <= 35035`
  and rolls `Random_(900)` against `(difficulty_bonus + desirability) *
  2` (aidudes.cpp:398-412).

### (c) Named constants

Rare in the AI. `CMBTAI::Retreat_Check_` declares
`kThreatSentinel = 3000000000u` and `kThreatPercentScale = 100`
(cmbtai.cpp:756-757); `diplomac.cpp:5-6` has two marker constants. The
enums (`PLAYER_PERSONALITY_*` orion2_consts.h:432-441,
`PLAYER_OBJECTIVE_*` :422-430, `GAME_DIFFICULTY_*`) are names for
indices, not for tunable values.

### (d) From a data file — **none**

---

## 3. Difficulty and personality

**Two different mechanisms, and only one of them is a table.**

**Personality is a table, and it is rolled once per game.**
`KEN::Init_NPC_Personalities_Objectives_Themes_` (ken.cpp:122-…) is the
only place any of it is assigned:

```
int difficulty_val = game_random::Random_(10) - MOX::_settings.game_difficulty + 1;   // ken.cpp:129
… clamped to 0..9 …                                                                    // :130-134
MOX::_player[i].personality = _personalities[MOX::_player[i].race][difficulty_val];    // :135
```

So the **race** picks the row and a **difficulty-shifted random roll**
picks the column: a harder game shifts every AI toward column 0, which
in `_personalities` is the xenophobic/ruthless end. Seven personalities
(orion2_consts.h:432-441), fourteen race rows.

`objectives` (the six "MILITARIST / EXPANSIONIST / …" traits,
orion2_consts.h:422-430) is chosen in the same function by a **weighted
random draw** whose weights are built from the race's own traits in a
long chain of `if`s with literal weights (ken.cpp:137-235 and beyond:
`obj_w[5] += 100` for a 100 % pop-growth race, `obj_w[1] += 100` for a
+50 ship-attack race, and so on). The two AI ship-design themes are
drawn the same way in the same function.

**Difficulty is branches, plus two tables.** `MOX::_settings.
game_difficulty` is compared in place 28 times across the empire AI —
aidata.cpp:979, :1277; aibuild.cpp:73, :968-973; aidesign.cpp:330,
:1291; aidudes.cpp:100, :381, :386, :406, :1513; aimove.cpp:145, :250,
:1179, :1181, :1419, :1420, :2723 — and only twice indexes a table
(`AIBUILD::_difficulty_ship_design`, `_difficulty_intel_bias`). There is
no single "difficulty multiplier" anywhere; each site decides for
itself.

**Three of those branches are cheats, and they are worth naming**
because they are what "harder AI" mostly means here:

* `aidudes::Freighter_Cheat_` (aidudes.cpp:377-390) — freighters
  materialise, more readily at higher difficulty.
* `aidudes::Do_Ship_Upgrade_Cheats_` (:392-…) — free refits, scaled by
  `_difficulty_ship_design`.
* `AIBUILD::Player_War_Level_` (aibuild.cpp:100-…) — how accurately the
  AI may read the human's fleet, weighted by `_difficulty_intel_bias`
  (:73-74): at Tutor it sees the weakest ship, at Impossible it sees
  close to the true average.

---

## 4. What is moddable today without touching C++

**Nothing of the AI. Plainly: not one number above can be changed from
outside the engine today.**

But the mechanism to change that already exists and is not a sketch:

* `specs/config/main.json5` (2 848 lines) is a schema of **96
  parameters and 18 records**, all of them rules and mechanics — repair
  rates, mount damage, shield data, stealth bonuses, missile defence.
  **Not one is about AI behaviour.**
* `tools/config` generates `src/config/generated/config.cpp` (9 987
  lines) from it: *"Generated from specs/config/main.json5. Do not
  edit."* (config.cpp:1).
* The generated file binds each schema variable to the **address of an
  ordinary C++ global** — e.g. `(void*)&CMBTFIRE::_mount_dmg[i].pd`
  (config.cpp:9073).
* `src/config/mod_manager.cpp` loads `mods/<id>/mod.json5` (:159-196)
  and applies that mod's `.cfg`.
* One mod ships: `data/mods/ver150/` ("Community Patch 1.50"), and its
  `config/main.cfg` is **empty** — a header comment and nothing else.

### The single change that would open the most

**Add the personality and difficulty tables of section 2(a) to the
schema. It is a change to ONE file plus a regeneration, and it edits no
AI source at all.**

Why it is that small: the config binding needs a symbol it can take the
address of, with a stable shape — and every one of those tables is
already a namespace-scope array with an `extern` declaration in its
header. The schema already carries the index type for half of them
(`game_difficulty`, specs/config/main.json5:22-30). An array binding of
exactly this shape is already in use:

```
bind_root: { header: "game/cmbtfire.h", symbol: "CMBTFIRE::_mount_dmg" },
type: { kind: "array", count: 2, index_base: 0,
        index_type: "high_energy_focus_presence", element: { … } },
```

**Size, honestly estimated:** one new enum type for the seven
personalities (~12 lines, the shape of `game_difficulty`), plus one
array parameter per table. Eleven personality and difficulty tables at
roughly 15-20 schema lines each is **about 200 lines in
`specs/config/main.json5`**, one regeneration of
`src/config/generated/config.cpp`, and **zero lines changed in
`diplodef.cpp`, `diplomac.cpp`, `aibuild.cpp`, `ken.cpp` or
`newtech.cpp`**. That is the whole of it.

**What it would and would not buy.** It would make every AI
personality's aggression, threat appetite, peace-keeping, sneak-attack
taste and treaty-breaking chance settable from a mod file, and it would
make the difficulty cheats settable — which between them are most of
what a player experiences as "the AI's character". It would **not**
touch what the AI builds, where it expands, what it researches or how
it fights: those are the 228 and 77 bare literals of section 2(b), and
reaching them means rewriting the functions, not moving a table.

**One caveat to record rather than discover later:**
`diplomac::_starting_relations` is read at game creation, so a change to
it applies to a new game and not to a save. The personality tables have
the same property (`ken.cpp:135` runs once). The difficulty tables are
read every turn and would apply immediately.

---

## 5. What the Extension API exposes

**More than anyone has used, because the snapshot sends `s_player`
whole.**

`ext_api.cpp`'s `SerializeState` writes the player array byte for byte:

```
// Players (8 × sizeof(s_player))
WriteBytes(buf, &MOX::_player[i], sizeof(s_player));     // ext_api.cpp:120-122
```

So every AI-state field in `s_player` is **already on the wire today**,
with no patch and no change to orion2re:

| field | orion2.h | what it is |
|---|---|---|
| `personality` | :1762 | the seven-way character of section 3 |
| `objectives` | :1763 | MILITARIST / EXPANSIONIST / … |
| `ship_design_theme`, `ship_special_theme` | :1795-1796 | what its ships will look like |
| `relations[8]`, `base_relations[8]` | :1834-1835 | how much it likes each player |
| `treaty[8]`, `trade_treaty[8]`, `research_treaty[8]`, `tribute_treaty[8]` | :1836-1839 | every treaty state |
| `diplomacy_incident/message/severity/value/system[8]` | :1840-1844 | what it is angry about, and how much |
| `treaty_modifier`, `trade_modifier`, `tech_exchange_modifier`, `peace_modifier[8]` | :1845-1848 | the running diplomatic arithmetic |
| `threats[8]`, `dishonored_flag[8]`, `peace_duration[8]` | :1858-1860 | the counters the personality tables index against |
| `time_since_last_attack[8]`, `ship_war_losses[8]`, `colony_war_losses[8]` | :1855-1857 | the war record |
| `last_attacker`, `failed_to_expand` | :1794, :1832 | |

**OrionLayer already declares one of them.** `core/structs/player.py`
carries `("personality", 39, "u8")` — verified, at offset 39 — and
`objectives` sits at **offset 40**, immediately after it and
immediately before `home_planet_id` at 41, which the spec also
declares. So the next AI field costs one line in a file that is already
verified at both its neighbours.

**What is NOT on the wire:** every table of section 2(a) (they are
engine statics, not player state), and everything in `AIDATA`'s
per-turn caches — `_ai_player_info`, `_ai_star_info`, `_ai_colony_info`,
the planet values, the stage weights — which are allocated per turn and
freed again at nextturn.cpp:122. A client cannot see what the AI
*thinks*; it can see what the AI *is* and what it has *done*.

---

## 6. Where the reconstruction is incomplete

**Much less than expected, and this is the honest surprise of the
reading.** `files.md` lists **389 files, every one `[X]`** — not a
single AI file is marked outstanding. Searching the AI sources for
`TODO`, `FIXME`, `XXX`, `HACK`, "not implemented", "stub" or
"simplified" returns **four hits, all of them the same thing**: two
empty functions that the original also had, called and doing nothing —
`npcdiplo::NoOp3` (npcdiplo.cpp:563, called at :77) and
`diplomac::NoOp2` (diplomac.cpp:460, called at :465).

Two entries in `todo.md` touch AI data and neither is behaviour:

* `todo.md:23` — "Keep AI design allocation fields as percentages with
  disabled sentinel -1 rather than enums."
* `todo.md:24` — "Resolve the AI design table class mismatch: native
  source has seven tables, while 1.50 declares eight names …"

The second is a real open question and the schema records it too:
*"Complete uint8 semantic-ID domain. Human value 100 is the native
non-AI sentinel, not an eighth AI table class"*
(specs/config/main.json5:312).

**Where a mod would therefore change something the original never did**
is not in a gap in the reconstruction — there is no usable gap. It is
in the three cheats of section 3, which are the only places where the
AI is given something rather than deciding something.

### Three places the AI reads what a player could not

Recorded here because they are the most likely thing a mod would want
to change, and because two of them are not difficulty-gated at all.

1. **`AIBUILD::Player_War_Level_` (aibuild.cpp:100-…)** — walks the
   human's ships directly and blends the true minimum with the true
   average by `_difficulty_intel_bias` (:70-74).
2. **`aidesign::Human_Player_Best_Weapons_Are_Beams_` (aidesign.cpp:906)**
   — the AI asks what the human's best weapons are and picks its
   defensive specials table accordingly, at **seven call sites**
   (:1495, :1519, :1543, :1571, :1599, :1619, :1656). No difficulty
   test.
3. **`AIDATA::_enroute_human_ships` (aidata.cpp:24, filled :221)** — a
   per-star, per-turn map of where the human's ships will be, built
   every turn for the AI to read.

---

## 7. Could not be confirmed

* **Nothing here was driven.** Not one statement was checked against a
  running game. The personality roll at ken.cpp:129 in particular would
  be worth one live confirmation, because its `Random_(10) -
  difficulty + 1` is the whole of "difficulty changes the AI's
  character" and it is asserted from one line.
* **`_personalities` is `[14][10]` and there are 7 personalities**, so
  the table's *values* are a subset of the enum and the second index is
  a 0-9 roll, not a difficulty. That reading is from the one assignment
  at ken.cpp:135; no second source.
* **The `[12]`, `[10]` and `[8]` widths of the personality tables
  against 7 personalities** are unexplained — they are wider than the
  domain and the tail entries are zero. Whether the original used the
  spare slots, or whether they are padding, was not established.
* **`todo.md:24`'s seven-versus-eight AI design table mismatch** is
  quoted, not resolved.

## 8. What was not read — the timebox, stated rather than discovered

The order asked for breadth. These were **located and not read**:

* `AIMOVE` (2 788 lines) — the movement and attack logic was mapped by
  function, and only `AI_May_Attack_Player_` and the head of
  `Compute_Attack_Worthiness_` were read.
* `CMBTAI` (2 491 lines) — the tactical scoring
  (`Evaluate_Possible_Move_`, `Target_Ship_Value_`,
  `Target_Missile_Value_`) was not read at all.
* `aidesign` (1 710) — only its tables and its human-weapon query.
* `AIBUILD::Colony_Building_Score_` — the literals were counted, not
  read. **Which building gets which weight is unknown from this
  reading**, and it is the single most useful thing a follow-up would
  establish.
* `npcdiplo` (1 313) and `diplomac` (3 344) — mapped by function; the
  actual thresholds inside them were not extracted.
* `ADVCIV`, `council.cpp`, `antarans.cpp`, `spy.cpp` — located only.

---

## Open questions for Data

1. **Is the subject worth anything at all to this project?** OrionLayer
   is a frontend. Everything in section 4 is a change to *orion2re*,
   which is Joes' tree and which this project does not modify — so the
   cheapest opening is a REQUEST, not a task, and it belongs in
   `doc/orion2re_open_fixes.md` or nowhere.
2. **If it is worth a request, is it the personality tables?** They are
   the cheapest by a wide margin and they change what a player feels.
   The alternative — the building and attack weights — is a rewrite of
   two functions and would not be a schema change.
3. **Do you want `objectives` on the HD side?** It is one line in
   `core/structs/player.py`, at an offset both of whose neighbours are
   already verified, and it would let an HD screen say what an AI
   player is playing for. `relations[]` and `treaty[]` are the same
   kind of one-line additions and are what a diplomacy screen would
   need.
4. **Are the three "the AI reads the human" places (section 6) a
   finding you want raised with Joes**, or are they the original's own
   behaviour and therefore not a fault at all? This reading cannot tell
   the two apart: it read orion2re, not MOO2.
5. **Is a deeper pass on `Colony_Building_Score_` wanted?** It is the
   one function where knowing the numbers would change what anybody
   could say about the AI, and it was explicitly not read here.
