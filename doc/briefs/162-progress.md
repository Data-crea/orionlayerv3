# Work order 162 — progress

Unattended run, 22 September 2026. Splitting `tools/smoke_test.py`
(22 221 lines, 1 172 833 bytes, almost all of it inside one `main()`)
into per-screen modules **by script**, so that screen work reads and
runs only that screen's checks plus the shared core.

**Written so a fresh session can resume from this file alone.** Each
part says what is done, what is committed, what the next step is and
where the evidence lives.

Evidence root: `~/orionlayer-fixtures/evidence/work_order_162/`.

---

## State at the start of the run

| | |
|---|---|
| HEAD | `a5c3f4e` (161) |
| tree | clean |
| suite | 247 checks, full tier; 7 push-only (`SLOW_TIER`), 240 in the fast tier |
| `tools/smoke_test.py` | 22 221 lines, 1 172 833 bytes; `main()` is lines 265–22147 |
| gates | pre-commit `--fast`, pre-push full (158, unchanged by this order) |

---

## Part 0 — the brief filed — **DONE**

`162-work-order-…md` byte for byte as it arrived, this file,
`162-parked-for-data.md`, and their row in `doc/briefs/README.md` in
the same step (the suite asserts the index in both directions).

## Part 1 — the baseline tool — **BUILT**

`tools/smoke_baseline.py`: `capture <dir>` runs both tiers N times,
records the ordered `ok(...)` list, the check count, the fast tier's
skipped set and the runtimes, refuses anything but a green run, and
fails if two runs of the same tier disagree. `compare <a> <b>` is what
the cut is held to.

**The normalisation table is EMPTY, and that was measured rather than
assumed.** Two full runs of the unchanged tree produced byte-identical
`ok(...)` lists, 247 sentences each — the suite prints verdicts and
transcribed constants, not measurements of the clock. The table stays
in the tool with that note and the rule that every rule names the
message that needed it: a rule written defensively is a blind spot the
size of its own pattern.

## Part 2 — the inventory tool — **BUILT**

`tools/smoke_names.py` (a library) and `tools/smoke_inventory.py` (the
tool). 221 sections, 247 checks, 1 040 KB of `main()` body.

**A section is a maximal run of top-level statements ending at an
`ok(...)`** — the only boundary the suite itself draws, which is what
157 measured against too.

**The name flow is ordered, not set-based.** `_fh = open(_fh)` reads a
name it then binds and `_fh = open(path)` does not; a "reads minus
binds" set cannot tell them apart and reported 881 free reads as
though every reused throwaway name were a dependency. Mutation is
tracked separately, because `_surf.blit(...)` binds nothing and
changes everything a later reader sees — and it is the edge that
matters most: 13 sections are pulled into the core's dependency
closure by a mutation of `app` alone.

**Attribution, and how each section's area was decided.** Tokens come
from the tree: each screen's folder name, its name parts longer than
three characters, and every file stem in its folder longer than five —
minus any stem `core/`, `tools/` or `assets/shared/` also carries, and
minus any stem two screens share. (`palette` is `core/palette.py` and
had filed the suite's very first block as a Fleets check.) A tree
sweep — `os.walk`, `glob.glob` — goes to the core whatever it names,
because it polices files that do not exist yet (157 section 5a). A tie
or no screen at all goes to the core. A margin on top of the tie rule
was measured and dropped: demanding three hits and twice the runner-up
moved 53 more sections into the core, and since every `--screen` run
carries the core it made every narrowed run *bigger*.

| area | sections | KB | s |
|---|---:|---:|---:|
| colony_summary | 53 | 372 | 45.1 |
| core | 82 | 237 | 9.0 |
| galaxy_map | 29 | 170 | 5.8 |
| fleets | 19 | 125 | 3.9 |
| planets | 11 | 40 | 1.5 |
| game_menu | 8 | 27 | 4.2 |
| empire_identity | 3 | 23 | 0.6 |
| research_select | 4 | 22 | 0.6 |
| main_menu | 6 | 13 | 0.1 |
| custom_race | 3 | 8 | 0.3 |
| select_race | 2 | 2 | 0.5 |
| new_game | 1 | 1 | 0.0 |

Evidence: `inventory_before.txt` (the table, 29 KB — the thing a
session reads) and `inventory_before.json` (the rows, for the cutting
script), plus `times_before.json`, a measured run with every check's
segment time anchored to its own file and line.

**The tool did not retire with the cut.** `--screen` asks it at run
time which sections a screen depends on; a baked dependency list would
be the second copy this project keeps paying for.

## Part 3 — the cut — **DONE**

**The full split was built, not the fallback.** `tools/smoke_test.py`
is the runner; the checks are 90 files in `tools/smoke_suite/`, one
group per screen plus a shared core, in the original order.

The cutting script is `evidence/work_order_162/smoke_cut.py`, and it
is deliberately NOT in `tools/`: its input no longer exists, so it can
never run again, and a tool in `tools/` has to import in a fresh
process and be maintained.

### How the modules are made

* **A module is a CONTIGUOUS run of sections of one area**, split at a
  section boundary when it would pass 40 KB. Contiguous because the
  runner executes modules in file-name order and the full run keeps
  the original order — a module holding sections from two places would
  reorder the suite.
* **Every line of `main()` lands somewhere.** A section owns the lines
  from the end of the one before it to its own last line, so the
  comment that introduces a check travels with the check.
* **The dedent is tokenize-aware.** A plain four-space dedent changes
  the continuation lines of a multi-line string: it altered
  `drawn_pixels`'s docstring on the first attempt, which is how the
  rule got written. Lines inside a multi-line string token are left
  alone.
* **The module header is a COMMENT block, never a docstring.** A
  docstring would be a string constant in the AST, and the proof below
  is that the modules' statements are `main()`'s statements and nothing
  else. It carries the module's group (`# smoke-suite area: <name>`,
  which the runner reads) and the sentence of every check in it.

### The proof

| | |
|---|---|
| **AST** | the modules' statements, concatenated in order, `ast.dump` identically to `main()`'s 4 020 top-level statements. Asserted by the cutting script BEFORE anything is written — stronger than output, because it says every statement arrived unchanged and in order before a check has run |
| **normalised `ok(...)` list** | identical to the baseline, `baseline_before/` against `baseline_after/` |
| **counts** | 247 full, 240 fast, 7 push-only — identical |
| **runtimes** | full 71.7 s / 71.8 s before, 71.7 s / 71.7 s after; fast 31.9 s before, 31.8 s after |

**One normalisation rule was needed and it is the only one:**
`max_map_scale transcribes Maximum_Galaxy_Display_Scale_ (… both
extents required at N source files)`. That check walks every `.py` in
the tree to prove no call site passes `MAP_MAX_X` alone, and the cut
turned the suite's one file into ninety, so N went 216 -> 306. What it
asserts did not move and neither did its code; the size of the tree it
walked did. The rule names that message, as the tool requires.

### The seven rewrites, and why each was unavoidable

Every one is a SELF-REFERENCE. The suite was one file, so "exclude my
own source" was one path and "read my own source" was `__file__`.
Neither is true of a directory, and both would have measured the wrong
thing silently — the marker inventory would have reported all ninety
modules as carrying an unread HD EXTENSION, and the push-only guard
inventory would have found no guards at all.

| rewrite | fires | what it repairs |
|---|---:|---|
| `_SELF = os.path.join("tools", "smoke_test.py")` -> `SUITE_FILES` | 1 | the marker inventory's own exclusion |
| `if _rel == _SELF:` -> `if _rel in _SELF:` | 1 | …and the comparison with it |
| `os.path.relpath(_fp, _proj) == os.path.join("tools", "smoke_test.py")` -> `in SUITE_FILES` | 2 | the `squish_step` and plate-radius one-home greps |
| `if _rel2 == os.path.join(…)` -> `if _rel2 in SUITE_FILES:` | 1 | the dead list-config grep |
| `if _f not in ("main.py", "tools/smoke_test.py"):` | 1 | `palette.init`'s call-site check |
| `_dl_src = io.open(os.path.abspath(__file__)…)` -> `suite_source()` | 1 | the derived-loader check parses the suite's own source |
| `_st_src = …` -> `suite_source()` | 1 | the push-only guard inventory greps it |

Each is counted and the count asserted; a rewrite that fired a
different number of times than the original had would have stopped the
run.

**`__file__` itself needed nothing.** The modules are executed into the
entry point's own namespace, so the ten `os.path.dirname(os.path.
dirname(os.path.abspath(__file__)))` expressions still name the project
root.

### Two things outside the suite had to move with it

* **`tools/linecount.py`** exempts `tools/smoke_suite/` as it exempted
  `tools/smoke_test.py`. The exemption did not widen — it is the same
  file in ninety pieces — and part 5 holds the pieces to something
  stricter in its place.
* **`doc/redundancy_audit.md`**'s sixteen `smoke_test.py:<line>`
  citations now name the MODULE, found by grepping for the symbol each
  entry itself quotes. Several of the old numbers were already stale
  against the file they named, which is the other half of the reason a
  line number was not translated into a line number. **The briefs were
  not touched**: `doc/briefs/README.md` says their content is byte for
  byte what arrived, so their citations are historical and stay.

### The ambiguous cases, as the order asks

The attribution is a heuristic and it says so per section (`how` in the
inventory). Sweeps, ties and sections that name no screen go to the
core — 82 sections, 237 KB. Cases worth naming:

* **`resources + palette`, the suite's first block**, names
  `select_race` exactly once, inside `palette.col("select_race", …)`.
  It is the core; `MIN_HITS = 2` is what files it there.
* **`a fallback says why`** is filed under `main_menu` and **`field 0
  is dropped once in parse_fields`** under `planets`: both are
  cross-cutting checks whose CODE names another screen more often than
  their own sentence does. They are in the fast tier and the full
  suite either way; what it costs is that their sentence is printed
  under the wrong screen's `--screen` run.
* **`the Fleets reshape (work order 153)`** was filed under
  `galaxy_map` until the sentence was given five times the weight of
  the code — its code is full of galaxy-stretch arithmetic. A check's
  own sentence says what it is ABOUT; its code says what it touches.

### The five modules over 40 KB

Each holds ONE section, and a section is one check's block: splitting
it would split a check. They are listed in `v3_projektstatus.md` with
that reason, the way decision 6 handles a file over 300 lines.

## Part 4 — the development selector — **DONE, and it is not what the order expected**

`--screen <name>` exists. **It narrows what the run PRINTS and not
what it runs**, and that is a decision taken on a measurement rather
than on taste.

**What was tried first.** A real selector needs to know which sections
a screen's checks depend on. `tools/smoke_inventory.py --closure`
computes exactly that: core + the screen + the transitive closure of
what they read, mutation edges included.

* Under the practical mutation net — the common container and surface
  methods — a screen's closure is **87 %** of the suite, and a narrowed
  run built on it **died** on the galaxy map's own screen object:
  `_gm = d.active` is fresh, but `_gm._state.fields` was filled by an
  earlier check through a method call on `d.active`.
* Under the only rule that is actually SOUND — every method call on a
  name changes it, because `d.active.update_from_game(...)` does — the
  closure is **96 %** of the suite.

So a narrowing that is provably safe is not achievable for this suite
as it stands, and one that is merely usually safe would produce a
GREEN run against state a different set of checks had built. **157 had
already refused this shape once**, for its caching idea, in one
sentence: *"a check that inherits another check's app is a new class
of fault this project has not had yet."*

**What `--screen` therefore is.** Every check still runs; only the
named screen's sentences and the core's are printed, and the first and
last line say `SCREEN <name> ONLY — NOT A GATE` with how many ran and
how many were shown. The output is what lands in a session's context,
which is the order's own measure.

**It still widens itself.** Before it narrows anything it asks `git
status --porcelain` — index, working tree and untracked alike — and if
anything outside the screen's territory has changed it runs the FAST
TIER with its full output and names the files, on the first line and
again on the last. The territory is one function, `territory()`, and
it is computed: a screen owns `screens/<name>/` and its own check
modules, so a new screen needs no edit.

## Part 5 — the size limit — **DONE**

`tools/smoke_suite/090_core_the_suite_holds_itself_to_a_size.py`, the
**one check this work order added** (247 -> 248, so `CLAUDE.md` and the
Snapshot table moved with it). It asserts three things, each the shape
of a fault the split would otherwise re-acquire:

1. **every module declares its group** (`# smoke-suite area: <name>`,
   its first line) and the group is a real screen folder or the core.
   A group that is a typo is a module every `--screen` run silently
   leaves out of its output.
2. **no module passes `CHECK_MODULE_LIMIT`, 40 KB**, unless
   `v3_projektstatus.md` lists it at that size — both directions, the
   decision-6 shape, because a hand-kept list is legitimate only with
   a checker. Five exceptions today, every one the same thing: a
   single section bigger than the limit, and a section is one check's
   block.
3. **no module rebinds a name `tools/smoke_test.py` owns at module
   level.** The modules are executed INTO the runner's namespace, so a
   bare `_why` there is a name 91 files can replace — and one of them
   did, which cost the `--screen` widening line its second printing
   before this check existed. 47 names, no collisions.

**Red and green, in a throwaway change** (`size_limit_red.txt`): 600
padding lines on `002_core_screen_lifecycles…py` took it to 41 633
bytes and the run went red naming the file and the limit; the file was
restored, the caches cleared, and the next run was green. The check is
in the **core**, so it runs in the fast tier — the tier a commit goes
through, which is the tier that has to notice.

It runs at **090**, before the two whole-run assertions: the documents'
check count can only count what ran before it, so
`089_core_a_fallback_window…py` was renumbered to **091**. Nothing
moved relative to anything else; a new check was inserted in front of
the last moved module.

## Documentation

| where | what it now says |
|---|---|
| `CLAUDE.md`, "Non-negotiable habits" | the three commands, and the working rule in the same words as decision 31 |
| `CLAUDE.md`, "Layout of the tree" | `tools/smoke_suite/` and what it holds |
| `CLAUDE.md`, "Files over 300 lines" | the suite is exempt from the line guideline and held to 40 KB per module; a screen's check goes in that screen's group |
| `doc/v3_fundament.md`, decision **6** | the exemption did not widen — the same file in pieces — and what replaces it is a SIZE, with the rule for a screen that outgrows it |
| `doc/v3_fundament.md`, decision **31** | extended, not reversed: the suite is a directory, `--screen` is not a gate and why, the selector widens itself, and the working rule |
| `v3_projektstatus.md`, Snapshot | 248 checks, the three commands, `--screen` is never a gate |
| `v3_projektstatus.md`, new section "The suite is a directory" | the three proofs, the measured closure, the size rule |
| `v3_projektstatus.md`, exceptions | the five modules over 40 KB, with their sizes and the one reason |
| `doc/redundancy_audit.md` | sixteen `smoke_test.py:<line>` citations repointed to their module |


---

## Acceptance

| the order asks | result |
|---|---|
| normalised baseline stable across two runs | **yes** — two full runs of the unchanged tree, 247 sentences, byte-identical before any normalisation rule existed |
| identical after the cut; count and skipped set identical | **yes** — `smoke_baseline.py compare` says *identical: 247 checks, 240 in the fast tier, 7 push-only, every sentence equal*. One normalisation rule, named to its message |
| evidence stored | `~/orionlayer-fixtures/evidence/work_order_162/` |
| full suite and fast tier green on a fresh clone | **yes** — clone + `python tools/setup.py`, 248 green; full 56.4 s, fast 30.5 s |
| both hooks proved by running them | **yes** — a commit went through the pre-commit hook (fast tier), a push through the pre-push hook (full suite) to a LOCAL bare repository, and a third run proved the pre-commit hook refuses a red tree and leaves HEAD alone. Nothing reached GitHub; the clone's origin was replaced and checked for the absence of a github remote before any push, and the whole scratch setup was removed |
| `--screen` for at least two screens | **yes** — `research_select` (112 of 241 sentences) and `colony_summary` (151), and `fleets` (126) |
| a change inside the screen's folder runs the narrow selection | **yes** — `screens/research_select/screen.py` touched, the run stayed narrow |
| a change in `core/` with the same flag widens and names the file | **yes** — `WIDENED TO FAST TIER: core/box.py changed outside screens/research_select/`, on the first line and the last. Both throwaway changes reverted, tree clean |
| the size-limit check fails on a deliberately oversized module | **yes** — 600 padding lines took a module to 41 633 bytes and the run went red naming it; restored, caches cleared, green again |
| push | **done, 22 September 2026**, after Data asked for it — through the pre-push hook, which ran the FULL suite (248 green) before git sent anything. `a5c3f4e..7bc73bb` on `github.com:Data-crea/orionlayerv3`; `HEAD` and `origin/main` are the same commit and the tree is clean |

### Runtimes, before and after

| | before the cut | after the cut | fresh clone |
|---|---:|---:|---:|
| full suite | 71.88 / 71.83 s | 71.75 / 71.70 s | 56.4 s |
| fast tier | 31.90 / 31.97 s | 31.77 / 31.81 s | 30.5 s |
| `--screen <name> --fast` | — | 32.0 s | 30.6 s |

**The cut costs nothing and saves nothing in time**, which is what a
pure move should do. The numbers are lower than work order 158's
(79.5–80.4 s full, 38.9–39.2 s fast) and that difference is not this
order's: both of the runs above were measured on the same tree, before
and after, and the *before* number was already 71.9 s.

### What one run prints — the direct measure of what lands in context

| run | bytes | lines | sentences |
|---|---:|---:|---:|
| full suite | 39 093 | 301 | 248 |
| fast tier (the commit gate) | 37 735 | 290 | 241 |
| `--screen research_select --fast` | **16 160** | 144 | 112 |
| `--screen fleets --fast` | 20 412 | 157 | 126 |
| `--screen colony_summary --fast` | 24 834 | 200 | 151 |
| full suite `--quiet` (the hooks' own form) | 69 | 2 | 0 |

A screen run prints **41 % to 64 %** of a full run, depending on how
much of the suite is that screen's. Measured, `output_bytes.txt`.

### Evidence

| file | what it is |
|---|---|
| `baseline_before/`, `baseline_after/` | two full and two fast runs each, and `baseline.json` |
| `inventory_before.txt`, `.json` | the 221-section table the cut was decided from |
| `times_before.json` | a measured run, every check's segment anchored to its own file and line |
| `smoke_cut.py` | the cutting script, kept here because its input no longer exists |
| `size_limit_red.txt` | part 5 red and green |
| `screen_selector_proofs.txt` | the two `--screen` acceptance cases |
| `fresh_clone_and_hooks.txt` | the clone, both tiers, and all three hook proofs |
| `output_bytes.txt` | what each run shape prints |

### Commits

| | |
|---|---|
| `8133b4f` | the brief, the progress file, the parked file and their index row |
| `413fc6e` | parts 1 and 2 — the baseline tool and the inventory |
| `3e1532e` | part 3 and part 4 — the cut and the selector |
| `e0c2a60` | part 5 and the documentation |
| `99fab4c` | the acceptance table, the measurements and the parked file |
| `07c5b81`, `7bc73bb` | the four sentences that live in both `CLAUDE.md` and the fundament, made literally identical |
| the commit after `7bc73bb` | the push recorded — see the Acceptance table. It names no hash of its own, because a commit cannot carry its own, and a placeholder left in a document is the stale second copy this project keeps paying for |

**Pushed 22 September 2026**, all seven through
`tools/githooks/pre-push`, which ran the full suite first:
`SMOKE TEST PASSED — 248 checks green`, then
`a5c3f4e..7bc73bb  main -> main`. Evidence: `push.txt`.
