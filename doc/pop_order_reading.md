# The order of `s_colony.pop[]` — a reading

Read 5 September 2026 against **orion2re 1.60.0** (`src/version.h`,
git `cf4d9617`). The question came from the Colonies screen: before
anything draws a pop cell, the order inside a job group has to be
known, or it gets invented at draw time and nobody notices.

**EVERY STATEMENT HERE IS A CODE READING AND NOTHING MORE.** That is
one source. Under decision 23 it may carry a DRAWING decision — which
is what it was bought for — and it may not put anything in
`core/structs` as verified, and it may not close a live test case
that needs a witness. Each finding below carries its own marker:

  `CODE`          derived from the source, one source, no witness.
  `CODE+WITNESS`  a code reading with live agreement already on
                  record elsewhere in this tree.
  `OPEN`          not decidable from the source; what would settle it
                  is named.

No savegame was waited for. Where one is needed, the constellation is
written down instead — see the last section.

---

## 1. Memory order — answered from the writing side

The fundament's rule is to read the function that FILLS the array.
There are exactly nine of them in the tree, and they fall into four
idioms. `grep -n "pop\[" *.cpp` filtered to assignments is how the
list was closed; a drawing or counting function was not consulted for
this section at all.

### 1.1 A pop that appears is APPENDED — `CODE`

Three sites, all writing to `pop[n_pops]` and then incrementing:

| Site | Event | What it writes |
|---|---|---|
| `colcalc.cpp:2387` | natural growth | job from the food/industry balance, `0x200`, the growing race in the low nibble, the colony owner in bits 4-6 |
| `colcalc.cpp:3802` | the colony PRODUCES an android | `0x200`, nibble forced to `8`, job from the build item |
| `settler.cpp:49` | a settler transport lands | race and job copied off the settler record |

There is no fourth. Nothing inserts into the middle, and no site
writes at an index it searched for.

### 1.2 A pop that disappears is REPLACED BY THE LAST ONE — `CODE`

Six sites, every one of them the same idiom —
`colony->pop[hole] = colony->pop[--n_pops]`:

| Site | Event |
|---|---|
| `colcalc.cpp:2138` | assimilation removes a native or a conquered pop |
| `colcalc.cpp:2231` | starvation kills one pop of a shrinking race |
| `colcalc.cpp:3796` | an android is scrapped to make room |
| `bomb.cpp:206` | a bombardment hit |
| `bomb.cpp:243` | a biological weapon hit |
| `settler.cpp:349` | a settler leaves for another colony |

**So a removal REORDERS the array.** The last pop jumps into the
hole. There is no compaction and no memmove anywhere.

### 1.3 The whole array is SHUFFLED on four occasions — `CODE`

`invasion::Enforce_Population_Limits_At_Colony_` (invasion.cpp:700)
begins with

    RUSS::Shuffle_(colony->pop, sizeof(colony->pop[0]), colony->n_pops);
                                                    invasion.cpp:721

— an unconditional Fisher-Yates over the live entries
(`RUSS::Shuffle_Int_`, russ.cpp:139), executed whether or not the
function then removes anything. Its callers:

| Caller | Event |
|---|---|
| `invasion.cpp:684` | the colony is invaded |
| `colcalc.cpp:2478` | the colony is surrendered in diplomacy |
| `combfind.cpp:2274` | an Amoeba renders the planet toxic |
| `ericnet.cpp:555` | **a building completes: Biospheres, or a Barrier / Flux / Radiation Shield falling through to it** |

The fourth is the one that matters for a peaceful single-player game:
building Biospheres shuffles that colony's pop array. **Any order a
client believes it can rely on has a half-life measured in
buildings.**

### 1.4 In-place rewrites that keep every index — `CODE`

Conquest (`invasion.cpp:659-681`), surrender (`colcalc.cpp:2468`),
assimilation's owner bits (`colcalc.cpp:3576`), the AI's own job
assignment (`aidudes.cpp:583`), colony (re)founding by combat
(`combfind.cpp:836`) and the network/init path (`ericnet.cpp:96`) all
rewrite `pop[i]` at the index they found it. None reorders.

Founding (`colonize.cpp:347-371`) writes `pop[0]` for the settler and,
on a planet carrying `SYSTEM_SPECIAL_NATIVES`, `pop[1..3]` as natives
with `n_pops = 4`. That is the one place where a colony starts with a
NON-arbitrary order — one own pop, then three natives — and it is
also the shortest route to a save that has natives in it.

Saving and loading preserve the array exactly: 42 words in, 42 words
out, index for index (`savegame.cpp:314`).

### 1.5 The array IS sorted, but never for a human player — `CODE`

`aidudes.cpp` qsorts `colony->pop` in four places, and one of them
sorts the whole array:

    qsort(colony->pop, colony->n_pops, 4, aidudes::Sort_Pops_Fixed_);
                                                    aidudes.cpp:742

`Sort_Pops_Fixed_` (aidudes.cpp:749) puts androids and natives FIRST
— nibble 8 or 9 before everything else — so the AI can treat the
un-reassignable pops as a fixed prefix. qsort is not stable, so the
order inside each class is whatever the implementation leaves.

**It cannot reach a human player's colony.** `All_Colony_AI_`
(aidudes.cpp:18-27) iterates players and calls `Colony_AI_(i)` only
where `plr->objectives != PLAYER_OBJECTIVE_HUMAN`, and the whole
chain to the qsort runs from there via `nextturn.cpp:110`. The HD
list is filtered to `owner == MOX::_PLAYER_NUM`
(`COLXPORT::N_Colonies_`, colxport.cpp:67), so the arrays HD draws
are not the sorted ones.

`OPEN`, and small: this holds while the local player's `objectives`
IS `PLAYER_OBJECTIVE_HUMAN`. Nothing on the wire reports `objectives`,
so a client cannot check it. Nothing in this project produces a state
where it would differ, and no reading of ours makes it impossible.

### 1.6 The answer

**There is no order.** Not by race, not by android status, not by
job, and creation order only until the first removal. A job change
does not move a pop — `Give_Colonist_New_Job_` (colmove.cpp:549) and
`Send_Cluster_` write the profession bits in place, at the index they
were given. What moves pops is removal (swap with the last), and what
destroys the order outright is the shuffle in 1.3.

Consequence for the Colonies screen: **`pop[]` is a bag with stable
indices between events, not a list with a meaning.** Any grouping HD
shows is HD's own, and the only ordering the engine itself imposes on
what a player SEES is the draw order in section 2.

---

## 2. Draw order — a separate question, and a display decision

`COLDRAW::Do_Colony_Info_Pop_Stuff_For_Pop_` (coldraw.cpp:282-386)
serves every mode this screen uses: drawing (0), building the
slot→pop map (1), the squish pass (2), and the two hit tests (3, 4).
Its five nested loops (coldraw.cpp:326-337) decide the order, and it
is NOT the array's — `CODE`:

    for state      0..6      COLONY::Pop_To_Pop_State_, so 2, 3, 4
      for conquered 0..1     (pop & 0x400) >> 10
        for job     the column being drawn
          for nibble in (9, 0, 1, 2, 3, 4, 5, 6, 7, 8)   coldraw.cpp:287-297
            for i   0..n_pops, ARRAY ORDER

Only assigned pops are icons (`(pop_val & 0x200) != 0`,
coldraw.cpp:336) — which is how a cluster in hand disappears from the
screen.

So the drawn column is grouped by (state, conquered, nibble), and the
array is consulted only INSIDE such a group. Normal pops come before
natives, natives before androids; within a state, unconquered before
conquered; within that, the low nibbles in the order 9, 0, 1 … 8.

`CODE+WITNESS` for the array part: measured on the reference save
5 September 2026, a colony with twelve farmers and a scientist held
the scientist at index 11 and the last farmer at index 12, and a
click past every icon selected pop 12 — the position the walk gives
it, not the array's.

**This is a display decision, and HD may keep it or deviate from it
with a marking.** It is also the only ordering in the whole subject
that the original itself performs, which is an argument for keeping
it — see section 3, where keeping it turns out to be load-bearing
rather than merely faithful.

### 2.1 Which pop is drawn differently, and by what — `CODE`

Worth writing down because the Colonies screen has decided to carry
the race and android property in the CELL rather than in the colour,
and the original agrees — it carries it in the sprite, and it has
four classes, not two:

| Condition | Sprite | Source |
|---|---|---|
| conquered (`0x400`) | `Colony_Pop_Icon_(race)` = RACEICON entry `race * 13 + 12` — a static race portrait | colony.cpp:1278, :1285 |
| native (state 3) | RACEICON entry `0xAA`, one sprite for ALL natives | colony_main.cpp:456 |
| android (state 4) | RACEICON entry `0xA9`, one sprite for ALL androids | colony_main.cpp:460 |
| otherwise | `race * 13 + job * 2 + 1` — per race AND per job | colony_main.cpp:445 |

`race` is not the nibble: it is
`MOX::_player[Get_Effective_Pop_Player_(...)].race`, and
`Get_Effective_Pop_Player_` (colony.cpp:1257) returns the COLONY
OWNER for nibble 8 and 9 and the nibble otherwise. So an android in
my colony resolves to my race and is then drawn with the android
sprite anyway; a foreign pop of mine resolves to that player's race
and is drawn as that race's figure.

Two consequences for a cell treatment. A conquered pop is not a
tinted version of anything — it is a different picture, a portrait
where the others are working figures. And an android and a native
have no race at all on screen: one sprite each, for every race in the
game.

---

## 3. The collision with the selection rule — derived, and decided

`COLMOVE::Get_Cluster_` (colmove.cpp:56-76) takes every pop identical
to the clicked one from its index **to the end of the array**, where
`Pops_Identical_` (colmove.cpp:106-126) compares the profession bits,
the pop state, and the nibble together with the conquered bit.

Put that beside the draw order and the answer falls out — `CODE`:

**The set `Get_Cluster_` takes is exactly "the clicked icon and every
icon after it in the drawn column", provided the column is drawn in
the original's own order.** Because: the three fields
`Pops_Identical_` compares are precisely the three the walk groups by
(state, conquered, nibble), inside a single job column, and within
such a group the walk is in array order. So an identical group is one
contiguous block of icons; the clicked pop's array index splits that
block; and everything at or after it in the array is at or after it
in the block.

That is what makes today's HD behaviour correct, and it is
conditional. **Order the cells inside a job group by anything else —
by array index, by race, by anything — and the selection stops being
a contiguous run:** the player clicks a cell and cells elsewhere in
the row move. Nothing on screen would reveal it, because every count
stays right.

Hence decision 48 in the fundament.

### 3.1 Can a foreign pop stand between two of one's own? — `CODE`

**In the ARRAY: yes, and the code produces it rather than merely
allowing it.** Growth walks the races in a per-turn SHUFFLED order
(`player_order`, shuffled at colcalc.cpp:2277 with the owner swapped
to the front) and appends one pop per race per pass, so a
multi-race colony interleaves by construction. Removal then swaps the
last pop into arbitrary holes (1.2), and the four events in 1.3
shuffle the lot. Job plays no part in any of it: `job_class` is
computed from the colony's food and industry balance, never from the
race.

**In the DRAWN COLUMN: no.** The nibble loop groups the pops of one
player index together before the array is consulted, so between two
icons of nibble *n* there can never be an icon of nibble *m*.

**Therefore the second open test case is NOT closed by this reading,
and it is not the case it was thought to be.** What was open was "a
foreign pop between two own ones in the same group". In the array
that constellation is normal; in the original's column it cannot be
drawn. What a live witness is still needed for is not whether the
constellation exists but whether OUR mirror of the walk reproduces
the original's column when it does — and that needs a save with two
races in one colony. It stays open, and section 5 says what would
close it.

---

## 4. The edge cases that were asked for

**A job group with no pops.** `CODE`. The column simply has no
icons: the walk emits nothing, `Get_Selected_Pop_` returns -1
(the walk finds no match and the function returns -1,
coldraw.cpp:439) and `Get_Cluster_` is
never called, so a first click there does nothing at all. A DROP
there is unaffected — `Send_Cluster_` (colsum.cpp:869) is given the
job index and never consults an icon, which is what makes it possible
to start an empty column. The squish divides by
`max(count, 1)` (coldraw.cpp:19-22), so the geometry does not divide
by zero either.

**An android and a foreign pop in the same job group.** `CODE`. They
are never in the same group as the walk means it: the android is
state 4 and the foreign pop state 2, and the state loop is the
outermost of the five. In the drawn column the android sits after
every state-2 pop of that job, whatever the array says. They are also
never in one cluster — `Pops_Identical_` compares the state, so a
click on one cannot take the other.

**A foreign pop between two own ones in one group.** Section 3.1.

---

## 5. What is NOT decidable from the source

Three things, and each names the save that would settle it.

**The meaning of nibble 8 and 9 has no live witness.** Three sites
agree that 8 is an android and 9 a native — `pop.h` (`RACE_ANDROID`,
`RACE_NATIVE`), `Pop_To_Pop_State_` (colony.cpp:1240) and
`Pop_Race_String_` (colony.cpp:948, which returns two dedicated
ESTRINGs for them and `_player[nibble].race_name` for everything
else) — and all three are the same reading of the same tree. The
nibble is verified live for 0..7 as a player index and not for 8 and
9. A save with one android and one native pop closes it.

**Whether our transcription of the walk reproduces the original's
column** is verified only for the single-race case (section 2). A
multi-race colony is what would exercise the nibble loop and the
conquered loop, which are exactly the two levels no reference save
has ever driven.

**Whether qsort could ever touch a human colony** — section 1.5.
Nothing observable would separate the two states; this one is a
reading with a stated limit rather than a test case.

---

## 6. What a savegame would have to contain

Not a work item. Written down while the source was open, because
four open points in this project all wait on the same one or two
colonies, and buying the save once is cheaper than four times.

| To close | The colony needs |
|---|---|
| refusal `no_farming`, and `max_farms` as a live witness | a colony whose planet yields no food: `Colony_Food2_Per_Farmer_` 0 sets `max_farms = 0` (colcalc.cpp:692-696) — a Toxic, Radiated or Barren planet without the tech that fixes it, and at least one pop NOT farming, so a drop onto the food column can be refused |
| refusal `native_job`, pick-up refusal `native_pickup`, nibble 9 | a colony founded on a planet carrying the **Natives** system special: founding writes three native pops outright (colonize.cpp:360-371). It has to be COLONISED, not conquered — the special is cleared on founding |
| refusal `android`, nibble 8 | a colony that has BUILT an android: the Android Farmer / Worker / Scientist build item appends a pop with the nibble forced to 8 (colcalc.cpp:3802-3816). Needs the Androids tech |
| race distinction on screen, the nibble loop, the conquered loop | a colony holding pops of two player races, at least one of them with the conquered bit — i.e. a colony taken by invasion and held (invasion.cpp:659-681 sets `0x400` on foreign-race pops unless the owner is Assimilative, trait 25) |
| the sort / window binding | ten or more colonies. The current reference save already has eleven |
| refusal `job_full` | 42 pops in one job. Reachable only in principle; not worth building a save for |

The cheapest shape that covers five of the six is **one save, late
game, with: a Natives planet colonised by the player, one android
built anywhere, one enemy colony invaded and kept, one colony on a
Radiated or Toxic world, and the eleven colonies already present.**
