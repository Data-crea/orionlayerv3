# Work order 156, Stop 2 — A and B implemented

21 September 2026. Data released **A and B**; **D to G parked**; **C**
asked for a plain-language explanation before deciding. Two commits,
one per group, each through the pre-commit hook. **Not pushed.**

| | |
|---|---|
| `a3d2292` | **A** — Stage 5's tail: dead code nothing can reach, and a path two documents invented |
| `8454d05` | **B** — the redundancy audit gets verdicts, and stops leading with a fixed defect |

Suite green after each: **243 checks**, the count unchanged. No check
was added and none removed, so `CLAUDE.md` and the Snapshot table need
no edit.

---

## Line count, before and after, same method as Stop 1

`tools/linecount.py` — `ast` docstring spans, then blank, then
whole-line `#`, then CODE; `linecount.walk()` over `ROOTS = ("",
"core", "screens", "tools")`; `tools/smoke_test.py` on its own row
because it is `linecount.EXEMPT`. The repeat snippet is in
`156-findings.md` §1 and was re-run verbatim.

### CODE lines — the column decision 6 is about

| folder | before | after | delta |
|---|---:|---:|---:|
| `(root)` — `main.py` | 323 | 323 | 0 |
| `core/` | 6 372 | 6 360 | **−12** |
| `screens/` | 11 743 | 11 726 | **−17** |
| `tools/` (without the suite) | 8 678 | 8 678 | 0 |
| `tools/smoke_test.py` | 14 702 | 14 702 | 0 |
| **TOTAL** | **41 818** | **41 789** | **−29** |
| **TOTAL without the suite** | 27 116 | 27 087 | **−29** |

### Total lines, all buckets

| folder | before | after | delta |
|---|---:|---:|---:|
| `core/` | 13 099 | 13 074 | −25 |
| `screens/` | 26 193 | 26 175 | −18 |
| everything else | 37 062 | 37 062 | 0 |
| **TOTAL** | **76 354** | **76 311** | **−43** |

**−29 code lines, 0.11 % of the tree outside the suite.** That is what
was there to take, and Stop 1 said so before the work started: the
estimate was ≈29 and the outturn is 29. It landed there by two
offsetting surprises — one more deletion was found than projected
(`FRAME_TITLE`), and the eight comment lines recording why it went are
documentation, not code, so `screens/` comment lines went **up** by 8
in the same commit.

The over-guideline list is unchanged: **10 files over 300 CODE lines**,
none of them touched. Files over 300 TOTAL fell from 66 to 65
(`core/zoomtables.py` crossed), which is a summary line in
`linecount.py`'s output and is not transcribed anywhere, so nothing
needed editing to match it.

---

## Deleted files

**None.** Every removal was dead code inside a live module. The
inventory went looking for superseded modules and the only one in the
tree, `tools/fleet_boxes.py`, is deliberately kept and cited from four
files in `screens/fleets/`, which this order may not touch.

## Deleted symbols and keys

| removed | file |
|---|---|
| `_render_title` and its call site | `screens/colony_summary/screen.py` |
| `TITLE_COLOR` | `screens/colony_summary/screen.py` |
| `FRAME_TITLE = "Colonies"` | `screens/colony_summary/screen.py` |
| `colony_summary.title` | `assets/shared/skins/default/colors.json` |
| `frame._title_note` | `screens/colony_summary/layout.json` |
| `from_json` | `core/helpformat.py` |
| `column_of` | `screens/colony_summary/colonypick.py` |
| `nebula_fraction`, `star_fraction`, `black_hole_fraction`, `ship_icon_fraction` | `core/zoomtables.py` |

## Markers moved

**None, and that is checked rather than asserted.** No removed code
carried an HD EXTENSION, DEVIATION or DERIVED marking.
`core/zoomtables.py` and `screens/colony_summary/colonytrack.py` are
both in the suite's `_MARKED` inventory and both keep their markings
(`INSET_DOT_DIM`, `DEVIATION IN HEIGHT`); the other three files edited
are not in the inventory and did not become empty of a marking. The
inventory check (`smoke_test.py:6517-6529`) runs in both directions and
passed on every run.

---

## The one thing Stop 1 did not find

`FRAME_TITLE = "Colonies"` on the colony summary. Tracing what
`_render_title` read turned it up, and **both**
`layout.json:_no_title_note` and `v3_projektstatus.md` said the word
"survives as `ScreenBase.FRAME_TITLE` for the framebuffer fallback
path, which is a different drawing".

**No such reader exists.** The only one in the tree is
`ScreenBase._render_frame_title`, reached from `_render_frame` behind
`if self.USE_FRAME` — and `USE_FRAME` is `False` on this screen — while
the fallback path draws the dispatcher's own name
(`core/original_view.py:158`) and never a `FRAME_TITLE`. Two documents
asserting a path no file carries: the same shape as the help panel's
HD EXTENSION marking that two documents claimed and no file had. Both
corrected in the commit that removed the attribute.

It is also the answer to a question Stop 1 left open. §5 flagged S1 as
an item **no test would catch**, and that was right — what caught this
was reading the callers, not running anything.

---

## Fresh-clone verification

Against clones, not the working tree.

1. **`git clone` of the tree at `8454d05`**, then `python
   tools/setup.py`: **SMOKE TEST PASSED — 243 checks green**, with
   every one of the twelve player-derived inputs reported `absent`.
   The clone has nothing from Data's MOO2 installation and passes
   anyway, which is the state a forker starts in.
2. **A second clone at `92d52c2`** (the commit before A), set up the
   same way, and `tools/colony_list_preview.py` run in both at
   1920x1080, 2560x1440, 3840x2160 and 1366x768. All **16 PNGs byte
   for byte identical**, clone to clone.

**And the two comparisons exercised different code.** The working-tree
run (also 16/16 identical) had all 54 population figures present; the
clone run had none, so it drew the coloured-cell fallback instead —
the two sets of renders differ from each other by SHA-256, and each set
is internally identical before and after. So **both** branches of the
figures feature were measured, which is the question the fundament says
to ask after a byte-identity check: *which inputs did it NOT see.*

The hashes are filed at
`~/orionlayer-fixtures/evidence/work_order_156/A_colony_render_identity.txt`,
on the pattern of 126's `I_frame_trio_render_identity.txt` — outside
the tree, because evidence is (decision 42).

Stated plainly, because the fundament is explicit that byte-identity
proves only the paths that were exercised: **the renders confirm the
reading, they do not license it.** The licence is that `title_rect` is
absent from every `layout.json` in the tree, so the deleted branch had
no input that could reach it.

---

## What B changed

`doc/redundancy_audit.md` only, no code. It carried a banner, a
verdict and a ratio for all 36 parked groups, both D8 claims corrected
in place with the original text kept as a quote, and a new `tools/`
section — that document opened with "`tools/` is out of scope" and by
21 September that folder was the largest part of the tree.

D4, D1 and D23 are recorded there as **EXTRACT, parked by Data on
21 September**, not as open questions. D15 is recorded as **DONE**.

---

## Parked

`doc/briefs/156-parked-for-data.md` — C, D to G, and two items the
inventory turned up that belong to nobody's current order.
