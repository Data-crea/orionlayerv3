# OrionLayer v3 — Fundament

The part of the project that has stopped moving: architecture
decisions, working principles, and the rules that produced them.

Read this before touching the code. `v3_projektstatus.md` says what
exists *today* and is rewritten every session; this file changes only
when a decision is reversed or a new lesson is paid for.

Every entry here was expensive. None of them is a preference.

---

<!-- fundament-index -->

## The parts

**Read the index `doc/v3_fundament.md` first, then the parts your
task needs, and always every `principles-` part.** The rules live
in `doc/fundament/`; this file lists them and carries none of them
itself, so a rule has exactly one home and a reader is never
comparing two copies.

Work order 164 moved them there by script on 22 September 2026,
out of one 195 KB file that every session was supposed to
read at startup — two and a half times work order 127's reading
budget. **Not a sentence changed**: the parts concatenate back to
the original byte for byte, and a smoke check holds the list below
to the directory in both directions.

| file | part | KB | decisions | what it covers |
|---|---|---:|---|---|
| [`fundament/01-decisions-layout-structure-and-data.md`](fundament/01-decisions-layout-structure-and-data.md) | **Layout, structure and data** | 22 | 1-19, 34, 37-38, 50-51, 57, 70 | How the HD client is laid out and where its data lives — the section's own preamble, Layout and coordinates, Structure, Data and resources. |
| [`fundament/02-decisions-the-orion2re-boundary.md`](fundament/02-decisions-the-orion2re-boundary.md) | **The orion2re boundary** | 36 | 20-25, 33, 35-36, 39-48, 52, 59-60, 62 | Everything that crosses to the engine: field input, struct offsets, injected clicks, what ships and what does not, and the deviations the boundary forced. |
| [`fundament/03-decisions-sizing-sprites-and-fonts.md`](fundament/03-decisions-sizing-sprites-and-fonts.md) | **Sizing, sprites and fonts** | 16 | 26-30, 32, 49, 53-54 | Sizes, sprite steps, tints, rotation and fonts — and the two entries about who owns a rule that the artwork decisions rest on. |
| [`fundament/04-decisions-screen-artwork-and-markings.md`](fundament/04-decisions-screen-artwork-and-markings.md) | **Screen artwork and markings** | 29 | 55-56, 58, 61, 63-69 | One screen, one frame image: the per-screen artwork decisions, the display settings, and the marking vocabulary. |
| [`fundament/05-decisions-process.md`](fundament/05-decisions-process.md) | **Process** | 7 | 31 | Decision 31 — the smoke suite, the two gates, and what a narrowed run is not. |
| [`fundament/06-principles-evidence-and-comparison.md`](fundament/06-principles-evidence-and-comparison.md) | **Evidence, and comparison against the original** | 26 | — | How a claim is established, and how it is checked against the original — the section's own preamble, Evidence, Comparison against the original. |
| [`fundament/07-principles-delivery.md`](fundament/07-principles-delivery.md) | **Delivery** | 11 | — | Who owns a detail and who owns a direction, and how a package travels without losing anything. |
| [`fundament/08-principles-diagnosis-and-refactoring.md`](fundament/08-principles-diagnosis-and-refactoring.md) | **Diagnosis and refactoring** | 26 | — | How a fault is found when nothing looks wrong — Diagnosis, Refactoring. |
| [`fundament/09-facts-orion2re-and-pygame.md`](fundament/09-facts-orion2re-and-pygame.md) | **orion2re and pygame facts** | 28 | — | Details that are cheap to look up and expensive to get wrong: the orion2re facts and the pygame facts. |

**Every decision keeps its number.** They are identities, cited across the
tree, so a decision that moved to another file did not move to another
number — which is why the table above runs out of order.

