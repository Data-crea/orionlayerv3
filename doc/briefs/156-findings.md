# Work order 156, Stop 1 — inventory

21 September 2026. **No code changed.** Baseline suite green before and
after the two filing edits below: `SMOKE TEST PASSED — 243 checks green`,
which is the count `CLAUDE.md` and the Snapshot table both carry.

Two edits were made, and both are the filing this order asked for, not
cleanup: `doc/briefs/156-work-order-…md` and its row in
`doc/briefs/README.md`. The second is not optional — the suite asserts
that every file in `doc/briefs/` is linked from that table, and filing
the work order without indexing it turned the suite **red** on the first
run. That is the index check doing its job on its own author.

---

## 0. Three claims in the order, corrected against the tree

The order owns the direction; these are details, and they are the
session's (fundament, "Who owns a detail, and who owns a direction").

**"Stage 5 … old modules that were superseded but never deleted."**
Stage 5's deletion list **ran on 12 September 2026** (decision 55,
Phase B). `frame_preview`, `colony_plateless`, `frame_build`,
`frame_mask`, `frame_cut`, `frame_master`, `colony_frame_check`,
`gimp_fixtures` and `colonyframe` are gone; `v3_projektstatus.md`
records it, `core/config.py:69-76` and
`screens/colony_summary/colonyplates.py:3-13` both carry the note, and
the fundament's entry is headed "SUPERSEDED FOR THE COLONY SCREEN — 12
September 2026" so the paragraphs under it read as record, not as
pending work. **There is no backlog of superseded modules.** What is
left under the Stage 5 heading is smaller and different in kind: two
permanently-empty fields, one dormant renderer, and one tool that is
superseded *and deliberately kept*. Section 2.

**"tools/ is now the largest part of the tree."** True, and only
because of one file. Measured (section 1): `tools/` is 23 380 code
lines, `screens/` 11 743 — but **14 702 of those 23 380 are
`tools/smoke_test.py` alone**, which is exempt by nature and is the
thing the order's acceptance depends on. Without it `tools/` is 8 678
code lines and `screens/` is the largest part of the tree by a factor
of 1.35. Both numbers are in the table below, because a cleanup that
"reduces tools/" by touching the suite would be moving in the wrong
direction.

**The audit's headline defect D8 is fixed.** `doc/redundancy_audit.md`
flags "D8: a decision-5 defect. On Planets the hover row index uses
`(y - area.y) * visible // area.height` while the drawing uses
`listgrid.all_bands`". That formula is gone. `screens/planets/
screen.py:295` is now `listgrid.band_at(planetdraw.row_bands(self),
screen_y)`, `planetdraw.row_bands` (98-107) returns
`listgrid.all_bands` and its docstring says it is "the ONE place the
list's bands come from", and `core/listgrid.band_at:39-51` records the
fault it was extracted to close ("work order 128 D"). Closed between
the audit and today. Nothing to do.

---

## 1. Line-count baseline

**Method, so it can be repeated exactly after Stop 2.** `tools/
linecount.py` is the tree's own measure and decision 6's definition:
docstrings come from `ast` (module, class and function docstring spans,
whole span), then blank, then whole-line `#` comments, then everything
else is CODE — every line in exactly one bucket. The walk is
`linecount.walk()` over its own `ROOTS = ("", "core", "screens",
"tools")`; `""` is the repository root, not walked recursively.
Aggregated per top level with `tools/smoke_test.py` on its own row
because it is `linecount.EXEMPT` and dominates every total.

Repeat with:

```
python -B - <<'EOF'
import os, sys, collections
sys.path.insert(0, "tools"); import linecount
agg = collections.OrderedDict()
for rel, m in linecount.walk():
    k = ("tools/smoke_test.py" if rel == "tools/smoke_test.py"
         else "(root)" if "/" not in rel else rel.split("/")[0] + "/")
    cur = agg.setdefault(k, [0]*6)
    for i in range(5): cur[i] += m[i]
    cur[5] += 1
for k, v in agg.items(): print(k, v)
EOF
```

**Baseline, 21 September 2026, working tree = `8b4f5a9` plus the two
filing edits:**

| folder | files | total | **code** | doc | comment | blank |
|---|---:|---:|---:|---:|---:|---:|
| `(root)` — `main.py` | 1 | 549 | **323** | 98 | 83 | 45 |
| `core/` | 69 | 13 099 | **6 372** | 3 888 | 1 448 | 1 391 |
| `screens/` | 85 | 26 193 | **11 743** | 8 769 | 3 255 | 2 426 |
| `tools/` (without the suite) | 55 | 14 722 | **8 678** | 3 291 | 1 248 | 1 505 |
| `tools/smoke_test.py` | 1 | 21 791 | **14 702** | 209 | 5 857 | 1 023 |
| **TOTAL** | **212** | **76 354** | **41 818** | 16 255 | 11 891 | 6 390 |
| **TOTAL without the suite** | 211 | 54 563 | **27 116** | 16 046 | 6 034 | 5 367 |

Documentation is 39 % of the tree's lines outside the suite. That is
the project's habit and decision 6's amendment exists to stop it being
taxed, so **the number this order should be judged on is CODE**, and a
commit that deletes docstrings to make a total fall is not a cleanup.

The over-guideline list is unchanged: 10 files over 300 CODE lines, 66
over 300 total, "56 of them are over on documentation alone"
(`python tools/linecount.py`).

---

## 2. Stage 5 candidates

Full-project greps below include `tools/` and `tools/smoke_test.py`.
There is **no superseded module left to delete outside `tools/`** — the
candidates are dead code inside live modules.

### S1. `colony_summary._render_title` — a dormant second copy (audit D15)

`screens/colony_summary/screen.py:444-455`, 12 code lines, called at
:405 every frame. It returns immediately: it reads
`self._data["frame"]["title_rect"]`, and `screens/colony_summary/
layout.json` has no such key — the `frame` block holds only `image`,
`_note`, `_title_note`, `_no_title_note`. The screen must have no
title and that is a transcription, stated at length in
`_no_title_note` ("THE SCREEN HAS NO TITLE … There is no title text
anywhere on it. A 'COLONIES' title was drawn here until Stage 4
because the SUPERSEDED frame.png cut a title hole").

- **Replaced by:** nothing. It is the galaxy map's `_render_title`
  (`screens/galaxy_map/screen.py:389`, live) left behind on a screen
  whose title hole went with the superseded frame.
- **Who imports it:** nobody. It is a method, called only at :405.
  The suite's single `_render_title` reference, `tools/
  smoke_test.py:17831`, is `_pf_gm._render_title(surf)` and `_pf_gm`
  is the **galaxy map** (it asserts `("GAME", (252, 136, 0))`).
- **Markers:** none. `_MARKED` does not list
  `screens/colony_summary/screen.py`.
- **Carries with it:** `TITLE_COLOR` (screen.py:130), its only reader,
  and with that the `colony_summary.title` key in
  `assets/shared/skins/default/colors.json` becomes unread.
  `_title_note` in `layout.json` ("the cutout … carries the screen
  name") describes the superseded frame and is contradicted by
  `_no_title_note` beside it.

### S2. `RowBoxes.growth` and `RowBoxes.beyond` — fields that cannot be non-empty

`screens/colony_summary/colonytrack.py:357-358`. Both construction
sites pass constants: `:402` returns `RowBoxes(None, (), (), (), None,
area.x)` and `:531` returns `…, (), None, …`. Nothing else builds one.
`growth_gap`, the layout value they were placed against, was deleted on
8 September 2026 — `layout.json:228` lists it among the "NINE VALUES
[that] DIED".

- **The suite already pins them dead:** `tools/smoke_test.py:8887`,
  `assert not _boxes.growth, _boxes.growth`.
- **Markers:** the module is in `_MARKED` as
  `"screens/colony_summary/colonytrack.py": "DEVIATION IN HEIGHT"` —
  which is the **drop rect's height**, not the growth boxes, and was
  itself re-targeted on 8 September when the F/W/S markers went
  (`smoke_test.py:6398-6403`). So the inventory does not block this,
  but the prose does: `colonytrack.py:459-466` and
  `v3_projektstatus.md:12292-12299` both say **"The code and its
  marking stay; Stage 5 decides whether they come back somewhere
  honest."**
- **This one is Data's call, not a cleanup.** The note reserves the
  decision explicitly. Proposed, not assumed — commit C in section 6.

### S3. `tools/fleet_boxes.py` — superseded, and deliberately kept

The only module in the tree whose own first line says SUPERSEDED
(`"SUPERSEDED by tools/frame_holes.py — work order 146"`). It cannot
run: `screens/fleets/layout.json` has no `frame.opening` any more.

**Recommend: leave, and it is not a close call.** Three reasons, in
order of weight:

1. Its docstring says why it is kept — it "records where the
   original's sixteen rectangles came from, and that reading is still
   the source for `fltgeom.REGIONS` and `fltgeom.CONTROLS`, which the
   wire side still uses". Deleting the file deletes a cited source.
2. Four files in `screens/fleets/` cite it by name
   (`fltplaced.py:40`, `fltgeom.py:5` and `:384`, `screen.py:26`,
   plus `layout.json`'s `_no_cutouts_note`). **`screens/fleets/` is out
   of bounds in this order**, so the citations cannot be re-pointed in
   the same commit — which is exactly the "a marker must never
   disappear because its module did" shape, one level up.
3. `v3_projektstatus.md:907` already records it as superseded.

### S4. Top-level names defined and referenced nowhere

Scanned every top-level `def`, `class` and `CONSTANT` under the four
`ROOTS` for any mention in any `.py`, `.json` or `.md` in the tree.
Screen classes are false positives (auto-discovered by `GAME_SCREEN_ID`,
decision 7) and are excluded. What is left, with a verdict each:

| name | code lines | verdict |
|---|---:|---|
| `core/helpformat.py:200 from_json` | 3 | **delete** — the inverse of `to_json`, written for "a cached or exported form" that never arrived |
| `screens/colony_summary/colonypick.py:283 column_of` | 2 | **delete** — its docstring argues for one home for a count nothing asks for |
| `core/zoomtables.py:873,885,889,893 *_fraction` | 9 | **delete** — four "native px → fraction of map width" helpers, no caller |
| `core/structs/colony.py:332 pop_original_owner` | 2 | **leave** — `core/structs/` is a declarative spec; see below |
| `core/structs/*` constants (`POP_PROF_*`, `STATUS_*`, `PLANET_SLOTS`, `TYPE_COUNT`, `HYPER_ADVANCED_TECH_*`, `TECH_APPLICATION_STATUS_AVAILABLE`) | ~10 | **leave** — a named offset in a verified spec is the transcription, and deleting it loses the reading, not just a symbol (decision 23) |
| `core/config.py:20,21 SKINS_DIR, FONTS_DIR` | 2 | **leave** — path constants beside the ones in use; near-zero gain, and `core/config.py` is where a reader looks for them |
| `core/billtext.py:68,70,73 MSG_*` | 3 | **leave** — wording pulled from the original's own message table |
| `core/widgets/list_view.py:33 COL_ROW_DIM`, `screens/galaxy_map/ping.py:55 RING_ALPHA` | 2 | **leave** — palette/alpha constants beside their live siblings |
| `tools/ext_diag.py:107 star_name_at` | 4 | **leave** — inside the module the fundament licenses as a deliberate second source |
| `tools/researchphases.py:32 SCIENCE_ROOM_FIELDS` | 1 | **leave** — work order 131's toolchain, deferred and out of bounds |

**Deletable from S4: 14 code lines.** That is the honest size of it.

---

## 3. The parked audit groups

`doc/redundancy_audit.md` was written on 17 September against a tree of
197 checks; the suite is 243 now. **Every one of its 36 parked groups
still exists.** Verified by locating each named symbol with `ast` and
re-comparing the copies with the audit's own normaliser (arguments and
locals renamed positionally, docstrings and decorators stripped),
`difflib` ratio against the first copy in each group.

Nothing on the parked list was silently resolved in those four days —
and one thing on the *headline* list was: D8, section 0.

### Still identical or names-only (the ones that could drift silently)

| id | copies | ratio | verdict, one sentence |
|---|---:|---|---|
| **D4** `{key}` fill | 4 | 1.00 / 0.34 / 0.27 | **Extract.** `colonypopup.fill` and `colonypick.fill` are still byte-identical after normalising, and `colonyoutput.fill_template`'s own docstring asks for extraction "at the THIRD copy" — the third and fourth are here, so the tree's own rule has already fired. |
| **T1** `fallback_text_rect` / `busy_text_rect` | 2 | 1.00 | **Leave.** Two copies, and each reads its own module's `FALLBACK_INSET` whose values differ on purpose with the reason at `popup.py:40-41` and `renderer.py:229-230`. |
| **T2** `EStrings.string` / `HStrings.message` | 2 | 1.00 | **Leave.** Two copies, the names follow the originals (`H_Message_`), and merging them would put one screen's text table in the other's module. |
| **D21** `_pick` / `_table` | 2 | 1.00 | **Leave.** Two identical one-line table lookups; a shared home would cost more lines than it saves. |
| **P3** `slot_rows` / `save_strips` | 2 | 1.00 | **Leave — deliberate.** Two different original field sets, each with its own citation (loadsave.cpp:263 and :279). |
| **P4** `resolve` / `resolve_dir` | 2 | 0.99 | **Leave — deliberate.** `exists` vs `isdir` is decision 17's whole-directory override. |
| **T5** `PlanetSet.get` / `SurfaceSet.get` | 2 | 0.99 | **Leave.** Two copies of a dict attribute lookup. |
| **G3** `cover` / `_make_thumbnail` | 2 fn + 3 blocks | 0.98 | **Leave, as 126 parked it.** The two functions are names-only but the three blocks equal `cover(…, (0.5,0.5), 1.0)` only *by arithmetic*, so it is a judgement call and not a move — and `new_game`'s drift is documented as intended. |
| **D16** `_push_sort_key` | 2 | 0.97 | **Leave.** Two copies, and the difference is real: colony `return`s after the first match, planets does not. Merging would change what a duplicate key in `layout.json` does. |
| **T3** `lift` / `_lift` | 2 | 0.96 | **Leave, but it is the one to watch.** Two copies — but `tools/smoke_test.py:17139` uses `playercolors.lift` as the **stand-in** for `ships._lift`, so if the two ever drift the check measures the wrong function and says nothing. Flagged in section 5; a check that they agree is the cheap fix and it adds a check rather than removing code, which is outside this order. |
| **T4** `Window.row` / `_selected_row` | 2 | 0.94 | **Leave.** Two copies. |
| **D1** loaders, `buildnames` vs `maintext` | 5 (+1) | 0.97 down to 0.36 | **Extract the head, keep the tails.** See below. |
| **D2** sprite-directory loaders | 3 | 0.90 / 0.69 | **Leave.** See below. |
| **D24** `predict_pops` / `plan_drop` | 2 | 0.87 | **Leave.** Acknowledged in the docstring; two copies. |
| **D23** frame-button pair | 2 | 0.86 | **Extract, small.** See below. |
| **P1** `_state` / `pop_state` | 2 | 0.83 | **Leave — deliberate**, and the suite already holds them to agreeing (`smoke_test.py:8125-8128`). |
| **D15** `_render_title` | 2 | 0.81 | **Delete the colony copy** — S1 above. This is the only parked group that is *dead code* rather than duplication. |
| **D20** guarded record access | 2 (+5 unguarded) | 0.81 | **Leave.** The audit itself says "Intent unclear; not decided here", and adding guards would change what a short record does on screen. |
| **T7** `button_rect_left` / `_right` | 2 | names-only | **Leave.** Two copies, `btn_left`/`btn_right`. |

### Still genuinely drifted — all **leave**, and why

T6, D5, D6, D7, D8, D9, D10, D11, D12, D13, D19, D22 measured 0.07 to
0.48 against their first copy. In every one of them the drift **is the
behaviour**:

- **D5** (word wrap, 0.38): `textfit.wrap_text` has a fast path that
  returns the string verbatim and keeps runs of spaces;
  `custom_race/popup._lines` always rejoins single-spaced and caches
  rendered lines. Pointing the popup at `textfit` would change what the
  message box draws. **Park — it is a behaviour change, not a cleanup.**
- **D7** (shrink-to-fit, 0.15-0.21) and **D19** (scrollbar thumb,
  0.07-0.17): four different rounding rules, three of them
  transcriptions with citations (`Set_Fitted_Font_Style_` plntsum.cpp:85;
  colsum.cpp:752-753). A shared implementation would have to pick one
  and change the other three screens.
- **D8** (row tiling): the extraction already happened —
  `core/listgrid.band_at`/`all_bands` is the home, Planets was moved
  onto it, and what is left is `gmorion.bands` re-deriving
  `gmdraw.bands` inline (two copies, same file family) and
  `monsterpanel._rows` deliberately not tiling.
- **D9/D10/D22** (named-box rect, font px, layout load): the audit
  calls D22 and D21 "trivial"; D9 has **two sources of truth**
  (`layout.rect(box_rect(name))` honours `content_offset`,
  `Box.screen_rect` honours `anchor`) and `colonytrack.py:245-262`
  documents why the colony moved off `screen_rect`. Merging them is a
  decision about box semantics, not a tidy-up.
- **D6, D11, D12, D13**: markup wrap, hit-test loops, panel
  construction, hover buttons — every copy differs in what it draws or
  what it hit-tests, and the audit records the evidence per copy.

### The three with a real case, sized

| group | copies | code lines today | after extraction, estimated | net |
|---|---:|---:|---:|---:|
| **D1** versioned JSON loader head | 5 | 114 | ~65 | **−49** |
| **D3** per-App LRU `set_for` | 3 | 46 | ~25 | **−21** |
| **D4** `{key}` fill | 4 | 26 | ~14 | **−12** |
| **D23** `_frame_button_side`/`_hit` | 2 | 32 | ~22 | **−10** |

D1 is the largest single reduction available in the whole order, and it
carries the audit's own caution: **"The five `_load`s bypass
`core/resources.py`"**, so a mod cannot override them while `HelpText`
can (decision 16). An extraction that quietly routes them through
`resources` would change which file a modded install reads — that is a
behaviour change. The head must be extracted **as it is**, bypass and
all, with the divergence left recorded.

D2 is **not** on this list although it is 94 code lines across three
copies: planets and icons `break` after a refused file (the next root
is not tried) and surfaces does not scale, does not size-check and uses
`convert()` rather than `convert_alpha()` only when a display surface
exists. Those differences are the mod-resolution and fallback
behaviour of three sprite sets. Leave.

---

## 4. `tools/` audit — 126 part I's method, on the folder it excluded

Same scan: normalised AST over every function of 4+ statements in
`tools/`, exact equality first, then `difflib` ≥ 0.80 cross-file.
303 functions compared across the 55 tools, **plus all 110 of
`tools/smoke_test.py`'s own functions that clear the 4-statement floor**
— every one of them normalised, none failed, and not one paired with
anything at 0.80 or above. So the suite shares no duplicated helper
with any tool, which is worth knowing before anyone proposes tidying
it: its other 162 functions are nested closures inside `main()` and sit
below the floor by nature.

(Two passes were run and agreed exactly: one over `tools/` with
`smoke_test.py` included and no size cap, and one with it excluded and
functions over 120 statements skipped. Both returned the same 8 pairs,
so neither the cap nor the exclusion hid anything.)

**Result: 8 pairs, in 3 families, and every one is two copies.**

| family | pair | ratio | verdict |
|---|---|---|---|
| **native framebuffer → PNG** | `colony_list_preview.write_native:348` ↔ `colony_move_hd.native_png:66` | 1.00 | **Leave — the redundancy is the point and it is already written down.** `write_native`'s docstring: "Kept here as well rather than imported because that module opens a window and drives a game; this one must stay runnable without either." |
| **Extension-API socket trio** | `ext_diag.connect/recv_exact/recv_frame` ↔ `ext_diag_race` same three | 1.00 / 0.82 / 0.81 | **Leave.** Two copies, and one of them is the module the fundament names as the deliberate second source. `ext_diag_race` already gave up its *third* copy of the field parser to `core/wire_protocol` and says so in its docstring; what is left is transport. |
| **live-drive harness** | `colony_move_hd._wrap/pump/wait_for/click_at` ↔ `livedrive._wrap/pump/wait_for/hd_click` | 0.83-0.91 | **Park — out of bounds.** Two copies, so the third-copy rule has not fired; and `livedrive` is `research_hd`/`researchphases`' base, which is work order 131's toolchain, deferred. |

**Unused vs used-only-by-hand.** Every `.py` in `tools/` that nothing
imports has an `if __name__ == "__main__"` block — 39 of them. Cross-
referenced against `tools/setup.py`, `tools/smoke_test.py`, `CLAUDE.md`,
`README.md`, `v3_projektstatus.md` and every other tool:

- **Nothing in `tools/` is dead code.** The 17 with no reference from
  `setup.py` or the suite are manual diagnostics, each with its purpose
  in its own first paragraph: `colony_drop_sweep` ("VERIFIES it rather
  than assuming it"), `colony_drop_timing` (explicitly "Kept, because
  it is what produced…" the measurement, while saying the HD screen no
  longer uses the chain it drives), `colony_move_probe`,
  `ext_diag_race`, `nebula_check`, `nebula_asset_check`,
  `star_icon_check`, `ship_icon_check`, `starfield_measure`
  ("so they can be re-derived instead of believed — a constant nobody
  can trace is a constant nobody dares change"), `starfield_preview`,
  `zoom_probe`, `zoom_check`, `game_menu_hd`, `livedrive`,
  `research_hd`, `researchphases`, `monster_hull_check`.
  The order's own rule settles these: *a manual diagnostic is not dead
  code.*
- **One data file reads as a leftover and is not:**
  `tools/galaxy_box_fields.json` (12 KB) is loaded by nothing —
  `tools/game_menu_fields.json` beside it *is* loaded, by
  `smoke_test.py:3585` and `:17280`. It is live field data recorded off
  the reference save (`v3_projektstatus.md:4906`, `:7022`) and cited
  five times. **Leave** — it is evidence, not code.
- `doc/briefs/136-draft-fleets-opening-check.py` is marked SUPERSEDED
  ("this is in the suite now") and is **kept on purpose**: the briefs
  README says a piece of work a brief asked to be parked travels with
  its brief. It is outside `linecount`'s ROOTS and costs the tree
  nothing. **Leave.**

**Not in the repository at all:** `diff.txt`, `diff_code.txt`,
`diff_doc.txt` sit in the working tree (5 September, 88 KB) and are
**untracked** — a fresh clone does not have them. Out of scope; noted
so nobody counts them as tree weight.

---

## 5. Risk per item, and what would catch it

| item | what could break | which assertion catches it |
|---|---|---|
| **S1** delete colony `_render_title` | nothing drawn — the method returns before it draws, because `title_rect` is absent | **NONE catches the deletion.** `smoke_test.py:17831` exercises the *galaxy map's* copy only. **FLAGGED.** What does hold: if a mod's `layout.json` ever set `title_rect`, a title would appear today and would stop appearing — but `_no_title_note` says a title on this screen is wrong, so that path is a latent fault, not a feature |
| **S1** drop `colony_summary.title` from `colors.json` | a typed colour creeping back in | partial — `smoke_test.py:9938-9947` holds named `colony_summary` keys, and 6017 refuses a typed colour where a key belongs; neither fails on an **unused** key. **FLAGGED** |
| **S2** delete `RowBoxes.growth`/`beyond` | the field count of a namedtuple every row renderer unpacks | **`smoke_test.py:8887`** (`assert not _boxes.growth`) must be **replaced, not deleted** — count must not go down. `:8691-8695` is the model: it asserts `"markers" not in RowBoxes._fields` after the F/W/S removal, so the replacement writes itself |
| **S2** the marking | `colonytrack.py` is in `_MARKED` | **`smoke_test.py:6517-6529`**, the marker inventory, fails if the file stops carrying a marking. Safe here — its `_MARKED` citation is "DEVIATION IN HEIGHT" (the drop rect), which S2 does not touch |
| **S4** delete 4 `zoomtables` fractions | `core/zoomtables.py` is in `_MARKED` on `"INSET_DOT_DIM"` | **`smoke_test.py:6517`** catches an emptied marked file. Safe — the marking is elsewhere in the module |
| **S4** delete `helpformat.from_json`, `colonypick.column_of` | nothing; no caller in py, json or md | **NONE.** **FLAGGED** — the evidence is the tree-wide grep in this report, and it should be re-run at the commit |
| **D4** extract `{key}` fill | `fill_template(None, …)` raises today and the two nested copies coerce `str(template or "")`; a shared home must pick one, and picking the coercion **changes** what a missing template draws | `smoke_test.py:5050, 5185-5186, 9901` call `fill_template`; `8397-10672` call `colonypick.message`. Behaviour on the **None** path is the gap — **FLAGGED**, and the extraction must keep each call site's current None behaviour rather than unify it |
| **D1** extract the loader head | a mod override appearing where none did (decision 16) — the five bypass `core/resources.py` on purpose-by-accident | the derived-stand-in check ("the derived stand-ins are current byte for byte (8 files), each carries the FORMAT_VERSION its loader demands, **each loads through the loader's own path**") exercises all five loaders. It would catch a broken load; it would **not** catch a *newly working* mod override. **FLAGGED** |
| **D3** extract the LRU | eviction order and `SET_CACHE` size differ per set (4 / 2 / 4) and the guards differ (`size <= 0` / `not size` / none) | no check names the LRU. **FLAGGED** — the parameters must stay per-caller |
| **D23** merge the frame-button pair | every click goes through both (`screen_base.py:168, 171`) | frame-button checks exist in the suite; a merged geometry that returns the wrong side breaks the GAME menu's own block. Lower risk than the rest |
| **any** file dropping below/above 300 code lines | `v3_projektstatus.md`'s exceptions list goes stale | **the linecount check** holds the list in both directions — regenerate with `python tools/linecount.py`, never edit by hand |
| **any** commit | — | `tools/githooks/pre-commit` runs `smoke_test.py --quiet` and refuses on any non-zero exit, 139 included |

**Items no test would catch: S1, S4, and the None path of D4.** Those
are the three that need a reader rather than a runner.

---

## 6. Proposed commits — Data decides which run

Ordered by risk, lowest first. Each is one theme, each through the
hook, no push.

**A — Dead code that nothing can reach.** S1 (`_render_title`,
`TITLE_COLOR`, the `colony_summary.title` key, and `_title_note` which
describes the superseded frame) plus the three deletable S4 entries
(`helpformat.from_json`, `colonypick.column_of`, the four
`zoomtables` fraction helpers). **≈ 29 code lines.** No marker moves.
No check changes. Nothing drawn changes, and the reason it cannot is
that `title_rect` does not exist in any `layout.json` in the tree.

**B — `doc/redundancy_audit.md` gets its verdicts.** Not a code commit:
section 3 of this file written back into the audit so it stops reading
as a list of open questions, plus the D8 correction, plus a line saying
`tools/` has now been scanned with the same method and what it found.
**0 code lines.** The reason it is worth a commit: the audit is the
document a forker will read next, and half of it is already answered.

**C — `RowBoxes` loses two fields it cannot fill** (S2). **≈ 4 code
lines**, plus replacing `smoke_test.py:8887` with the
`"growth" not in RowBoxes._fields` form that `:8691` already models,
and striking the "Stage 5 decides" sentence from `colonytrack.py:459`
and `v3_projektstatus.md:12292`. **Needs Data's yes specifically** —
both documents reserve this decision, and "do they come back somewhere
honest" is a design question this order cannot answer.

**D — D4, the `{key}` fill, extracted at the fourth copy.** **≈ −12
code lines.** The tree asked for this in `colonyoutput.py:113-117` and
the third copy arrived without anybody noticing. Condition: each call
site keeps its current None behaviour; the shared function does not
unify it.

**E — D1, the versioned JSON loader head.** **≈ −49 code lines**, the
largest reduction in the order. Conditions: the `core/resources.py`
bypass is preserved exactly and recorded as preserved; the five
payload tails stay where they are; `HelpText.load` is **not** folded in
(it goes through `res.load_json` and keeps `_available`/`_stale`
instead of a `state` — it is the sixth *relative*, not a sixth copy).

**F — D3, the per-App LRU.** **≈ −21 code lines.** Condition: attribute
name, key shape, factory, `SET_CACHE` and the pre-guard stay per
caller; only the get-or-create-and-evict block moves.

**G — D23, the frame-button pair.** **≈ −10 code lines.** Smallest
extraction, in the file every click goes through.

### What I recommend, and what I would not run

**Run A and B.** A is the order's stated goal in its purest form —
strictly less code, provably identical behaviour — and B costs nothing
and retires a document that is half stale.

**Ask Data about C** before touching it; the tree reserves it twice.

**D, E, F, G are the real "less code", and they are also "new
structure", which this order says it does not want.** They total
**≈ −92 code lines**, 0.34 % of the 27 116 outside the suite. My read:
the order's "unless the third-copy rule forces one" licenses **D** (the
tree's own note fired) and **E** (five copies), and does not clearly
license **F** (three) or **G** (two). But none of them is free — each
one trades duplication for a shared path through code that four screens
render from, and the suite's cover of the None path (D) and the mod
path (E) is the gap named in section 5.

**What is not worth doing at all:** everything in section 3's "still
genuinely drifted" list, `tools/` (section 4 found no dead code and
three families that are all two copies), and any attempt to make the
`tools/` total look smaller by touching `tools/smoke_test.py`.

**Honest headline.** The tree is tidier than the order assumes. Stage 5
ran four months into the project and left almost nothing; the audit's
worst finding has been fixed; `tools/` has no dead scripts. The
deletable dead code is **≈ 33 code lines** and the licensed
extractions are **≈ 61** more. Against 27 116 code lines outside the
suite, this order's realistic ceiling is **0.35 %** — and the thing
actually worth the session is **B**, because what a forker trips over
here is not the line count, it is a 404-line audit whose open questions
have mostly been answered and never written down.
