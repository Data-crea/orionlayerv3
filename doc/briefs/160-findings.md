# Work order 160 — findings

21 September 2026. **No code changed in either tree.** `~/orion2re` was
read with `git log`, `git show`, `git grep` and `grep` only.

The corrected copy is
`~/orionlayer-fixtures/evidence/work_order_160/orionlayer_notes_for_joes.md`.
`~/Downloads/orionlayer_notes_for_joes.md` is **untouched** (13 110
bytes, 21 September 20:38).

---

## Every changed sentence, old → new

**Two statements were false. Both are in Part B. Everything else
verified true.**

### 1. Part B intro — the unguarded line

> **old:** It is compiled only with `-DORION2RE_EXT=ON`. It is OFF by
> default, and a build without it is your code unchanged.

> **new:** It is compiled only with `-DORION2RE_EXT=ON`. It is OFF by
> default, and a build without it is your code unchanged, **apart from
> the one unguarded line in B3.**

`6598052c` is the only commit on the branch with **no** `#ifdef
ORION2RE_EXT` marker in an engine file. It adds one line to
`racesel.cpp`: `_old_race = static_cast<int16_t>(i);`. With the flag
OFF that line is still there, so "your code unchanged" is not exactly
true. **The document already discloses this three paragraphs later**
("`racesel.cpp`, unguarded, one line"), so this is a qualifier, not a
reversal — but Joes reads closely and this is the kind of sentence he
would test.

### 2. B4 — one synthetic id where there are two, and not wire-only

> **old:** Select Race and Custom Race reported `SCREEN_RACE` (6),
> which the Races/diplomacy screen also uses. On the wire only, race
> selection now reports a synthetic id, 51.

> **new:** Select Race and Custom Race reported `SCREEN_RACE` (6),
> which the Races/diplomacy screen also uses. **They now report two
> synthetic ids: 51 for Select Race, 50 for Custom Race. Unlike B5,
> this one is not wire-only** — it assigns `MOX::_current_screen`
> itself, inside `#ifdef ORION2RE_EXT` and restoring the old value on
> the way out, so in an extension build the engine's own screen
> variable carries the synthetic id while those two screens are up.

**Two things were wrong.**

**(a) There are two ids, not one.** `racesel.cpp:480` on
`orionlayer-local` is `MOX::_current_screen = 50;` for Custom Race,
with the comment "Custom Race is a sub-screen of race selection
without its own screen ID". Select Race is `EXT_SCREEN_RACE_SELECTION
= 51`. Our own HD screens agree: `custom_race/screen.py:38`
`GAME_SCREEN_ID = 50`, `select_race/screen.py:33` `GAME_SCREEN_ID =
51`. The old sentence names both screens and then gives one id, which
a careful reader takes as covering both.

**(b) "On the wire only" is false here.** `3305d78c` replaces
`MOX::_current_screen = SCREEN_RACE;` with
`MOX::_current_screen = EXT_SCREEN_RACE_SELECTION;` — the engine's own
variable. **B5's identical phrase is true**, and the contrast is worth
keeping: B5 uses `ext::ScreenOverride`, which sets `g_screen_override`
in `src/ext/` and whose own comment reads *"the game's own
`MOX::_current_screen` is untouched"* (`ext_api.cpp:795-799`). So the
document uses one phrase for two different mechanisms, and only one of
them is wire-only.

---

## Part 1 — B1 to B8 against `orionlayer-local`

Branch base confirmed: `git merge-base orionlayer-local main` =
`cf4d9617` "1.50 Backport: mixed race penalty", which is the commit
the document names. `src/version.h` on the branch is `1.60.0`, as Part
B states. Ten commits sit on the branch.

| | commit(s) | files named vs files touched | status claim |
|---|---|---|---|
| **B1** base hooks | `a111355d` | names CMakeLists.txt, mox2.cpp, fields.cpp, platform.cpp — touches exactly those plus `src/ext/` (4 files) **OK** | — |
| **B2** injected clicks | `191aaa78` | `platform.cpp` only **OK** | "verified live" — item 3: "both VERIFIED LIVE 5 Sep 2026" **OK** |
| **B3** `_old_race` | `6598052c` | `racesel.cpp`, 1 insertion, unguarded **OK** | "Your tree already has an equivalent fix" — **true**: `~/orion2re-main-neu/src/game/racesel.cpp` has `_old_race = i;` in the same function. Our item 5: "Applied in the 30 Aug tree" **OK** |
| **B4** race ids | `e099d3fc` + `3305d78c` | `racesel.cpp` only **OK** | **WRONG** — see correction 2 |
| **B5** research dialogs | `f838c754` | names science.cpp, tech.cpp — touches those plus `src/ext/` **OK** (the B items name Joes' files; `src/ext/` is ours) | ids 52 and 53 confirmed; "on the wire only" **true**, via `ScreenOverride` |
| **B6** move pops | `7067c366` | `colmove.cpp`, `colmove.h` **OK** | "verified live" — item 12: "VERIFIED LIVE" **OK**. Four `Refusal_Help_` sites confirmed, matching "the four refusal messages" |
| **B7** research rows | `e9d07528` | names fields.cpp, tech.cpp — touches those plus `src/ext/` **OK** | "The mouse path is unchanged" — `ext_api.h:56-58`: "leave the mouse path untouched — which is the whole point" **OK** |
| **B8** ext-only | `a111355d` (save slots, fleet box), `cc5ec133`, `e6199966` | the two B8-specific commits touch `src/ext/ext_api.cpp` only **OK** | "The last two are not yet confirmed live" — items 27 and 28 both say **NOT CONFIRMED LIVE** **OK** |

Also verified from B1's own text: the `SDL_ShowWindow` guard is
`if (!ext::g_hide_window)`; `CMakeLists.txt` has
`option(ORION2RE_EXT "..." OFF)`; and `src/ext` is absent from
`origin/main`, so "not in your tree" holds.

**One note on B8 that is not an error.** All ten branch commits are
dated 17–19 September, including the initial `a111355d`, so the save
slot list and the fleet box selection — worked on 14–16 September —
sit inside that first commit rather than in commits of their own. The
document does not claim otherwise.

---

## Part 2 — the move-pop contradiction: **`doc/ext_move_pop.patch` is the stale one**

`MSG_SET_JOBS` is on the branch (`ext_api.cpp:699`), and the engine
side is `7067c366` "Open fix 12: pop-move refusals without the message
box (colmove)". **So the change is applied.**

- `doc/orion2re_open_fixes.md` item 12 — "**patched locally** 10
  September 2026, **VERIFIED LIVE** the same day" — **true**.
- `doc/ext_move_pop.patch` line 11 — "NOT YET APPLIED" — **stale**.

**And a second one, found while checking the first.**
`doc/ext_save_slots.patch` line 16 says "STATUS: REPORTED, NOT APPLIED
(14 September 2026)". `MSG_SAVE_SLOTS = 0x14` is on the branch
(`ext_server.h:27`, sent at `ext_api.cpp:843`), and item 14 says
"**Applied** 16 September 2026 by Data, confirmed live the same
evening". **Also stale.**

Both repairs are **parked**, not made — `doc/briefs/160-parked-for-data.md`.

**Neither affects the handover**, which does not quote either header.

---

## Part 3 — "still open on our side": all three still open

156 to 159 touched none of them — those orders were the Stage 5 /
redundancy cleanup, the C/T3/D17 items and the suite profile, the
two-tier gate, and the Fleets pass.

| item | our record | still open? |
|---|---|---|
| Radio buttons | item **4**, "INJECT_CLICK pushes no MOUSEMOTION before the buttons — **Open**" | **yes** |
| Planets filters | item **13**, "**Request**" | **yes** |
| SELECT NEW RESEARCH | item **26**, "**OPEN, deferred by Data 19 September 2026**" | **yes** |

The handover's framing is right in each case. In particular "the
likely fix is a mouse-motion event before the button events, **in our
own code**" matches item 4's own fix section: the motion has to be
pushed from `ProcessInput()`, which is ours in `src/ext/`; the
`platform.cpp` reference there is where motion is *handled*, not where
the fix goes. And "only with OrionLayer connected … most likely
something on our side" matches item 26, where Data reproduced the
no-client case by hand on 19 September and the list waited.

---

## Part 4 — the references and the URL: **OK**

Every file the handover names exists in the **pushed** tree
(`git cat-file -e origin/main:…`):

`doc/ext_api_dokumentation_v3.md`, `doc/orion2re_open_fixes.md`,
`doc/ext_inject_click.patch`, `doc/ext_move_pop.patch`,
`doc/ext_research_screens.patch`, `doc/ext_screen_id.patch`,
`doc/ext_tech_activate.patch` — 7 of 7 present.

**The repo is public**, which the handover asserts. An
**unauthenticated** `git ls-remote https://github.com/Data-crea/orionlayerv3`
succeeds with no credentials, returning `be27c12`. So
`https://github.com/Data-crea/orionlayerv3/tree/main/doc` resolves for
Joes.

---

## Part 5 — the measured claims in C and D: **OK**

- **"55 ms per move instead of 725 ms"** — `doc/orion2re_open_fixes.md`
  item 12: "725 ms against 55 ms measured". **Matches.**
- **"`_ship_node[]` can be rebuilt from `_ship[]`"** — fundament
  decision 25: "`MOX::_ship_node[]` looked like it had to be
  serialized; it is a pure function of `_ship[]`". The withdrawn-proposals
  section adds the reason: "`Find_Ship_Stacks_` allocates nodes strictly
  sequentially in both branches of its loop, so node N is the N-th ship
  with `status < 3`". **Matches.**
- **"The engine version on the wire. We keep it ourselves and check it
  against your source."** — withdrawn, and `tools/version_check.py`
  compares `core/config.ORION2RE_VERSION` against `src/version.h` and
  `src/game/consts.h`. **Matches.**
- **"A command to scroll the map. The snapshot's galaxy coordinates are
  enough."** — withdrawn: "A command to move `_cur_map_x` /
  `_cur_map_y` … the snapshot already carries every star's galaxy
  coordinate". **Matches.**

Part C's six requests each restate an item checked above (C1→B1,
C2→B4/B5, C3→A2/B7, C4→B6, C5→A3, C6→A4). Nothing in C asserts a fact
that is not covered.

---

## Part 6 — anything else I would not sign as true

Nothing further in B, C or D. Two observations that are **not**
corrections:

1. **Part A's premise could not be checked from here, and it is out of
   scope.** The document says Part A was checked against the upload
   with `ENGINE_VERSION "2.0.0"` and `GAME_BUILD_DATE "Aug 15 2026"`.
   **Neither orion2re tree on this disk reports that**: `~/orion2re`
   and `~/orion2re-main-neu` both say `ENGINE_VERSION[] = "1.60.0"`,
   and neither defines `GAME_BUILD_DATE` at all. A4 thanks Joes for the
   bump and quotes both strings. This order was told Part A is out of
   scope, so **nothing in Part A was changed or checked** — it is
   recorded only because A4's two quoted strings are the kind of detail
   Joes would verify first, and the tree they came from is not on this
   machine.
2. **B5 touches `src/ext/` as well as the two engine files it names.**
   Not an error: the B items name the files in *Joes'* tree, and
   `src/ext/` is ours and is declared as ours in the same section. The
   same is true of B7.
