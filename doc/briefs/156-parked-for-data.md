# Work order 156 — parked for Data

21 September 2026. A and B are done (`156-progress.md`). This is what
is left, in the order Data needs to answer it.

---

## 1. C — awaiting your decision

**What it changes.** The row structure that describes one colony line
has two compartments for things this screen does not draw. They have
been permanently empty since 8 September, when the layout value they
were placed against was deleted; C throws the two empty compartments
away.

**What could break.** Only one thing: every place that unpacks such a
row expects a fixed number of compartments, so a missed one fails
immediately and visibly — a crash on drawing or clicking the colony
list, not a quietly wrong picture.

**Would a test catch it? Yes.** The suite builds these rows itself at
several places and asserts one of the two fields outright
(`smoke_test.py:8887`), so the run goes red before the hook lets a
commit through.

**The real question is not technical.** `colonytrack.py:459-466` and
`v3_projektstatus.md` both say, in the same words, *"The code and its
marking stay; Stage 5 decides whether they come back somewhere
honest."* Those two fields are a parked design idea — the colony's
spare capacity drawn as dashed boxes — not an oversight. The note
argues there is nowhere honest to put them in a row of three job
columns, because a dashed box inside the scientists column says
"scientists", which is what spare capacity is not. **Deleting them
closes that option.** Keeping them costs 2 lines and one assertion.

If you say yes, the commit is: remove the two fields, replace
`smoke_test.py:8887` with the `"growth" not in RowBoxes._fields` form
that `:8691` already models for the F/W/S markers (count does not go
down, an obsolete check is replaced), and strike the "Stage 5 decides"
sentence from both documents.

---

## 2. D to G — parked by your decision, kept measured

Not re-opened here. Recorded so the numbers do not have to be
re-derived if they are ever taken up, and written into
`doc/redundancy_audit.md` as parked rather than open.

| | group | now | after | net | the condition that matters |
|---|---|---:|---:|---:|---|
| **D** | `{key}` template fill, 4 copies | 26 | ~14 | **−12** | each call site keeps its current `None` behaviour — the nested copies coerce `str(template or "")` and `fill_template` raises, and unifying that changes what a missing template draws |
| **E** | versioned JSON loader head, 5 copies | 114 | ~65 | **−49** | the `core/resources.py` bypass is preserved exactly — a mod cannot override these five while `HelpText` can (decision 16), and "fixing" that silently changes which file a modded install reads |
| **F** | per-App LRU `set_for`, 3 copies | 46 | ~25 | **−21** | attribute name, key shape, factory, `SET_CACHE` (4/2/4) and the pre-guard stay per caller; **no check names the LRU**, so an eviction mistake would be invisible |
| **G** | `_frame_button_side`/`_hit` | 32 | ~22 | **−10** | smallest; in the file every click goes through |

Together **≈ −92 code lines, 0.34 %** of the tree outside the suite.

---

## 3. Two items that belong to nobody's order

Found by the inventory, outside 156's remit, not acted on.

### 3.1 The suite measures one function by standing in another (T3)

`tools/smoke_test.py:17139` uses `core.playercolors.lift` as the
**stand-in** for `screens/galaxy_map/ships._lift` when it checks the
ship tint presets. The two are names-only copies today (ratio 0.96 —
identical but for the parameter's default). If they ever drift, that
check goes on passing while measuring the wrong function, and nothing
says so.

`doc/redundancy_audit.md` already named this risk on 17 September; it
is repeated here because it is the only parked group whose failure
mode is **a green check that means nothing**, and 156 could not fix it:
the fix ADDS an assertion — "these two agree" — and 156 is a removal
order that may not raise the count on its own initiative.

It is two lines of check, on the model of the one that already holds
`colonyicons._state` and `colonymove.pop_state` together
(`smoke_test.py:8125-8128`, P1).

### 3.2 D17, three `HStrings` construction sites

`screenhelp.py:57-60` argues for "exactly one construction site" and
there are three (`app.hstrings`, `screen._hstrings`, and a fresh
instance per Planets entry), with the language lookup spelled two
ways — one of which, `colonybuild`'s, raises if `settings` is absent.
The galaxy map and the game menu therefore read HESTRNGS into two
objects.

Left alone deliberately: it is a construction-site question rather
than a duplicated body, and **somebody should measure what the second
read actually costs** before it is called a fault. Naming it so it is
not re-discovered a third time.

---

## 4. One thing that needs no decision, recorded anyway

`screens/colony_summary/layout.json:_no_title_note` and
`v3_projektstatus.md` both claimed `FRAME_TITLE` survived "for the
framebuffer fallback path". No such reader existed. Both were
corrected in `a3d2292`, in the commit that removed the attribute.

Worth a line here because of what it says about the tree rather than
about this screen: **the claim was in two documents and in neither
case beside the code**, which is the fault this project has paid for
repeatedly. The inventory found it only by tracing callers of something
it was already deleting. There may be more of that shape, and no scan
finds it — a grep can show that a symbol is unused, not that a sentence
about it is false.
