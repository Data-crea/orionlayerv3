# Work order 166 — progress

Unattended run, 23 September 2026. The research screens' look: no
glimpse of the original on entry, an outer frame from the Fleets art,
inner boxes drawn in code, and text that fits its box.

**Written so a fresh session can resume from this file alone.**

Evidence root: `~/orionlayer-fixtures/evidence/work_order_166/`.

---

## Part 0 — the brief filed — **DONE**

The brief, this file, the parked file and the index row, in one commit.
166 was free: `doc/briefs/` had nothing above 165 and the README's last
row was 165.

## Part A — never show the original on entry — **DONE**

### What Data saw, measured before anything was changed

`tools/entry_glimpse.py`, five entries into change mode from the map on
SAVE4, one record line per RENDERED frame:

```
entry 1: 55 frames, 22 of them showing the GAME's picture
         (frames 2..23, screen [36], hd_state ['unvalidated'], fields [0])
… the same 22 for all five entries
```

**The cause is exactly what the order predicted.** `Clear_Fields_`
leaves count 1 (fields.cpp:207) and `parse_fields` drops slot 0, so
between the switch to 36 and `Init_Entry_Data_` finishing the wire
carries **zero fields**. `validate_against_fields` cannot agree with an
absent list, the screen said UNVALIDATED, `wants_original()` said yes,
and `App._render` drew the framebuffer — for 22 frames, every time.

**THE VERDICT IS A PIXEL, AND THE FIRST VERSION OF THE TOOL WAS
WRONG.** It sampled the LETTERBOX BARS and asked whether they were
pure black, because `original_view.render` fills the window black
before it blits. It read "no glimpse" on every one of 275 frames while
the flag said 111 — `core/fallbacknote.render` draws the reason
OUTSIDE the picture, i.e. in the bars (work order 139 D). The tool now
renders the game's picture onto a scratch surface with the product's
own renderer and compares the window against it INSIDE the picture.
A test that can be defeated by something drawing where it samples is
not a test.

### The fix

`core/researchstate.py` — the state rule, extracted as a PURE function
when the new state pushed `researchscreen.py` past 300 code lines, and
split at a seam rather than for the number: "may this screen draw what
it has" is a different question from "how does the panel behave", and
as a function it can be checked without a screen, a window or a game.

**NOT YET, versus WRONG**, and that distinction is the whole fix:

| the wire | state | hands over? |
|---|---|---|
| no list at all, within the bound | `WAITING` | **no** — the game has not built one yet |
| no list at all, past the bound | `UNVALIDATED` | yes, with its own log line |
| a list that is there and disagrees | `UNVALIDATED` | **yes, on the first frame** — the fault 165 D found keeps no grace at all |

`EMPTY_LIST_GRACE = 66` is **measured, not guessed**: 22 frames in all
five entries, three times over. A bound is not a timer (decision 21) —
it is the give-up, and what ends the wait is the list arriving.

**And while it waits it draws NOTHING**, which is the order's own
words: `ScreenBase.draws_this_frame()` is False for an overlay in
`WAITING`, so change mode leaves the HD galaxy map it is a panel over.
Select mode has nothing underneath and draws its own empty panel — the
Fleets screen's answer to the same moment (work order 142 A), whose
`waiting` state this one is named after.

### Acceptance

| | |
|---|---|
| five entries, no frame shows the framebuffer | **yes** — `[0, 0, 0, 0, 0]` against `[22, 22, 22, 22, 22]` before, same tool, same method |
| the counter-test shows the glimpse again | **the before-run IS it**, kept as `A_entry_glimpse_BEFORE_the_fix.json`; and two offline mutations go red (`A_glimpse_red.txt`) |
| a check that holds the rule offline | two, `080h` — the states, and a pixel proof that a waiting overlay changes not one of 42 625 sampled pixels |

### Which other screens the same glimpse could reach

Three screens can ask for the fallback at all: `ScreenBase` says no,
`ResearchPanelScreen` is this one, and `screens/fleets/screen.py`
already has its own waiting state from work order 142 A — the same
moment, found the same way, fixed without a bound. Nothing else in the
tree implements `wants_original`, so the class is closed today; a new
screen that grows one inherits the question and not the answer.

## Part B — the outer frame, from the Fleets art — **not started**

## Part C — inner boxes drawn in code — **not started**

## Part D — text that fits — **not started**

## Part E — one counter in the tree — **not started**
