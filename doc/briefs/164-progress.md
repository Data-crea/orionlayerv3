# Work order 164 — progress

Unattended run, 22 September 2026. Splitting `doc/v3_fundament.md`
(3 515 lines, 199 974 bytes) into an index plus parts under
`doc/fundament/`, **by script**, so a session reads the index and the
parts its task needs instead of 200 KB at startup.

**Written so a fresh session can resume from this file alone.**

Evidence root: `~/orionlayer-fixtures/evidence/work_order_164/`.

---

## State at the start

| | |
|---|---|
| HEAD | `d4c5bab` (163) |
| tree | clean |
| `doc/v3_fundament.md` | 3 515 lines, 199 974 bytes |
| suite | 248 checks, 241 in the fast tier |

**The order's own line numbers were checked first and they hold**: the
four sections begin at 14, 1914, 3027 and 3493. The file is 3 515 lines
rather than 3 516 and 199 974 bytes rather than "about 200 KB"; work
order 162 added text to decisions 6 and 31 on the same day and the
section starts happened not to move.

## Part 0 — the brief filed — **DONE**

## Part 1 — the cut — **DONE**

**The full split was built, not the fallback.** The byte-for-byte
comparison passed on the first run and has passed on every run since,
so the abort rule never came near firing.

`evidence/work_order_164/fundament_split.py` is the splitting script,
and it is deliberately NOT in `tools/`: its input no longer exists as
one file, so it can never run again, and a tool in `tools/` has to
import in a fresh process and be maintained. `--verify` still runs at
any time against `evidence/work_order_164/v3_fundament.original.md`.

### Nine parts, and where each boundary came from

**Every boundary is a heading the document already carried.** Seven of
the nine fall on a `##` or `###` heading. Two fall inside a subsection
that is too large for one part, and both of those fall on a decision
heading — the next boundary down that the text itself draws:

* **"Sizing and artwork" is 44 KB** and splits at decision 55, where
  the entry that says a screen wears one fixed image begins; after it
  the run is per screen and per marking.
* **"Working principles" is 61 KB** and splits at its own `###`
  headings, so no subject is cut at all.

| part | KB | lines of the original | decisions |
|---|---:|---|---|
| `01-decisions-layout-structure-and-data.md` | 21.9 | 14-419 | 1-19, 34, 37-38, 50-51, 57, 70 |
| `02-decisions-the-orion2re-boundary.md` | 35.8 | 420-1062 | 20-25, 33, 35-36, 39-48, 52, 59-60, 62 |
| `03-decisions-sizing-sprites-and-fonts.md` | 15.9 | 1063-1326 | 26-30, 32, 49, 53-54 |
| `04-decisions-screen-artwork-and-markings.md` | 29.2 | 1327-1809 | 55-56, 58, 61, 63-69 |
| `05-decisions-process.md` | 6.6 | 1810-1913 | 31 |
| `06-principles-evidence-and-comparison.md` | 25.8 | 1914-2375 | — |
| `07-principles-delivery.md` | 11.0 | 2376-2576 | — |
| `08-principles-diagnosis-and-refactoring.md` | 25.5 | 2577-3026 | — |
| `09-facts-orion2re-and-pygame.md` | 27.8 | 3027-3515 | — |

**No exceptions were needed** — the largest part is 35.8 KB against the
40 KB limit. The index is 3.7 KB.

### The proof

`fundament_split.py --verify`:

```
IDENTICAL: 199974 bytes, 3515 lines, the index and 9 parts
concatenate back to the original
decisions: 70, every number exactly once, the same set as before
```

**One sentinel per file is what makes it provable.** The index carries
`<!-- fundament-index -->` and each part `<!-- fundament-body -->`;
everything before the sentinel is what the split wrote and everything
after it is the original, so "strip what was added" is one `index()`
call and not a pattern that could match the text itself. The fundament
carried no HTML comment of any kind — checked before the sentinel was
chosen, and asserted by the script before it writes.

**The preamble was kept VERBATIM**, which is why the proof covers the
whole file and not all-but-the-top. The order asks for the startup rule
to be rewritten *in the index*; it is stated in full in the index's own
section, immediately under the preamble, and the preamble's own "Read
this before touching the code" is still true of an index and was not
touched.

## Part 2 — the startup rule — **DONE**

> **Read the index `doc/v3_fundament.md` first, then the parts your
> task needs, and always every `principles-` part.**

In `CLAUDE.md` ("Before you change anything") and in the index ("The
parts"), **word for word the same**, and a check holds the two equal
after normalising whitespace — 162 found a paraphrased copy of a
shared rule by looking, which is not a method that scales.

**What a session reads at startup now:** the index (3.7 KB) plus the
three `principles-` parts (62.3 KB) = **66 KB**, against **195 KB**
before, plus whatever part the task needs. The always-read floor is the
working principles because the order says so, and 62 KB of it is what
that costs — the text may not change, so that number is not negotiable
here.

## Part 3 — references and checks — **DONE**

**Line-number citations: exactly one in the whole tree**, and it is in
`doc/briefs/23-…md`, which is a byte-for-byte archive of what arrived
(`doc/briefs/README.md` says so). It stays. Every other reference names
the file without a line, and since the index keeps the old path they
all still land somewhere useful — which is why the order asked for the
path to be kept.

**Ten checks read the fundament**, in eight modules, and all ten were
rewritten by script to `smoke_test.read_doc()`, which returns the index
and every part in order. Every assertion is the one it always was.
**No check names a part**: a part name in an assertion would be the
second copy this project keeps paying for, and it would go stale the
first time a decision moved between parts — the move being exactly what
the split makes cheap.

| module | what it asks the fundament |
|---|---|
| `008` | the sort slots' DEVIATION is at every home |
| `032` (twice) | decisions 56 and 57 are marked at every home |
| `033` | decision 58's HD EXTENSION |
| `035` | decision 28's "ONE EXCEPTION, AND IT IS MARKED" |
| `042` | decision 44 and `native_width` |
| `050` | the colony row's two deviations and their citations |
| `059` | decision 64 and the sprite deviation |
| `061` | decision numbers are unique |

**One check added** (248 -> 249),
`089_core_the_fundament_is_an_index_and_its_parts.py`, in the core so
it runs in the tier a commit goes through. It asserts the four ways the
join can rot: a part not listed, a listing with no part, a decision in
two parts or in none, and rule text creeping back into the index — plus
the 40 KB limit and the startup rule's two copies. It runs at **089**,
before the whole-run bookkeeping at 091, so the documents' check count
still counts everything.


---

## Acceptance

| the order asks | result |
|---|---|
| concatenation identical to the original; the diff (or its absence) in the evidence folder | **identical** — `identity_proof.txt`: 199 974 bytes, 3 515 lines. There is no diff to store, which is the result |
| every decision number present exactly once, and the same set as before | **yes** — 70 decisions, each in exactly one part, the set compared against the original's before the parts were written |
| full suite green, fast tier green, on a fresh clone | **yes** — clone + `python tools/setup.py` green, full 249 in 56.2 s, fast 242 in 30.5 s (`fresh_clone.txt`) |
| no part over 40 KB except listed exceptions | **no exceptions needed** — the largest part is 35.8 KB |
| the startup rule reads the same in `CLAUDE.md` and the index | **yes**, and a check holds it there |
| push | **Data's decision** |

### Evidence

| file | what it is |
|---|---|
| `v3_fundament.original.md` | the file as it was, 199 974 bytes — what the proof compares against |
| `fundament_split.py` | the splitting script; `--verify` re-runs the proof at any time |
| `identity_proof.txt` | its output |
| `full_run_after.out` | the full suite after the split, 249 green |
| `fresh_clone.txt` | the clone, `setup.py`, both tiers |

### Commits

| | |
|---|---|
| `a4fafc1` | the brief, the progress file, the parked file and their index row |
| `3d08a71` | the cut, the adapted checks, the new check, the startup rule, the documents |
