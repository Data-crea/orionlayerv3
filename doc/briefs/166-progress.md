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

## Part B — the outer frame, from the Fleets art — **DONE**

### Where it was cut from, measured

`tools/frame_holes.py` reads the Fleets frame's own transparent holes
and names the scanner map's `inset_map` at image (228, 211, 1491, 906).
The frame around it was found by walking OUTWARD from the hole's edge
on 50 rows and 50 columns, stopping at the first run of eight dark
pixels — the gap between this frame and its neighbours — and taking the
mode:

```
left  x 205 (rail 23)   right  x 1741 (rail 23)
top   y 189 (rail 22)   bottom y 1138 (rail 22)
```

so the cut is **(205, 189, 1537, 950)**, by `tools/make_research_frame.py`.
**DERIVED**, decision 49's surviving half: the input is committed, the
output is not, the cut is a plain crop, `tools/setup.py` runs it, and a
smoke check rebuilds it in a temporary tree and compares byte for byte.

The nine-slice corner is **140 px**, and that is measured too: each
corner bracket reaches at most 132 px along either axis beyond the
plain rail — TL 128x127, TR 127x124, BL 130x130, BR 132x129.

### The corners scale, they do not stretch

The tree had two nine-slicers and neither does what this needs:

| | corner rule |
|---|---|
| `core/nineslice.NineSlice` | the SOURCE's pixel size, whatever the window is |
| `core/frame.FrameRenderer` | target/source PER AXIS — stretches when the aspect differs, and this panel is square where the cut is 1.62:1 |

What is wanted is one factor from the WINDOW. `core/researchframe.py`
gets it by SCALING THE SOURCE ONCE and nine-slicing the result, so
`NineSlice` still does the slicing and there is no third implementation
of it — only a third rule about its corners. The factor is
`0.5 * layout.scale`, because `screens/fleets/assets/frame.png` is
3840x2160, the reference at 2x: a corner is 70 px at 1080p and 140 —
the source's own — at 3840x2160.

Marked `outer_frame`: **DEVIATION**, not an extension. The original
draws TECHSEL.LBX's own panel art in that place, so this is a different
picture where there was one, and decision 61's vocabulary reserves
"extension" for what the original does not do at all.

### THE FAULT IT UNCOVERED: the title was lost to every resize

The 4K capture had no headline. Not the frame's doing:
`ScreenBase.on_resize` calls `_reload_boxes`, which REPLACES every box
object — so the label `enter()` wrote onto the title box was written
onto an object the screen no longer had. **The research panel lost its
title at every resolution the player did not enter at**, and had since
the screen was built.

It is the colony column's own fault one screen over, and the offline
check could not have found it: it CONSTRUCTS a screen at each size, and
the fundament says exactly that — *"A PREVIEW THAT CONSTRUCTS IN ONE
SIZE CANNOT SEE A RESIZE FAULT — the check has to go the way the fault
went."* `_dress_boxes()` is now one place that seats the boxes AND
gives the title its word, called from `enter` and from `on_resize`, and
the check enters at one size and resizes through all four.

### Acceptance

| | |
|---|---|
| captures at all four resolutions, beside the native frame | `D_resolutions_4/` — 1080p, 1440p, ultrawide, 4K, each with its native picture |
| corner lamps unstretched, measured | the lamp's bounding-box aspect at each resolution against the cut's own, within 0.06, and its size within 4 px of the source's times the window factor |
| CANCEL stays inside the frame | yes, in every capture |
| the frame grows outward, never inward over content | it does — no collision at 1080p, so the default was not needed |

Three checks (271 -> 274).

## Part C — inner boxes drawn in code — **DONE**

The eight entry boxes wore `inner_panel`, a nine-sliced IMAGE out of
the skin, and Data's verdict on the live panel was that it does not fit
them. They carry **no skin at all** now — a box with none draws nothing
of its own — and `core.researchpanel.draw_box` draws them the way
`screens/planets/` draws its boxes:

| | |
|---|---|
| the fill | `colony_summary.panel_background`, which is what `planetdraw.PANEL_BG` fills its five windows with |
| the outline | `panel.thin_border` through `Style.draw_plate`, the rounded 1 px plate of decision 51 — the same call `planetdraw` makes for its headings, controls and status |

Both are read from the section that owns them rather than copied into
this screen's own section, and a check asserts the two are still equal
to the Planets screen's.

**The list popup's window goes through the same helper.** It drew
itself with two hand-written `draw.rect` calls and two colours of its
own; the entry boxes would have made that a third copy.

**All eight boxes are drawn, offered or not** — `Init_Entry_Data_` adds
a block field for every category and the original draws an empty panel
for one with nothing to offer (tech.cpp:225-231) — and at the game's
OWN rectangle: `Entry.block_rect()` is one function now, used by the
drawing and by `expected_fields`, so the box and the field the
reconstruction is validated against cannot come apart (decision 5).

Marked `inner_boxes_drawn`: DEVIATION. The original wears TECHSEL art
in these places and HD has none of it.

Two checks (274 -> 276). Captures at four resolutions in
`D_resolutions_4/`; beside the native frame the boxes now read as the
same kind of thing.

## Part D — text that fits — **DONE**

### What was wrong, and which of the two things moved

Both of Data's observations are the SAME cause, and it is not the text:

| | |
|---|---|
| the field name sits on the top edge of its box | the name is at `y + 21`; the block field starts at `y + 18` — 3 px above it |
| the hover band runs past the right edge of its box | the row runs `x .. x + 218`; the block field ends at `x + 215` — 3 px inside it |

The rows and the name anchors are TRANSCRIBED (tech.cpp:27-32,
:683-738). The block field is the game's own field and also a
transcription. What was NOT transcribed is the box HD draws, because
the original has none — its panels are painted into the TECHSEL
artwork and where the art's edges are, nobody here can read.

So the thing that moved is the thing nobody transcribed:
`Entry.panel_box(margin)` is the CONTENT plus a margin, and
`block_rect()` stays the game's field. Decision 53 exactly — a rule we
chose is Data's, a rule transcribed stays a check.

**`BOX_MARGIN = 4`, and 4 is the most the layout allows**: entry 0's
rows end at native x 313 and entry 1 begins at 322, a gap of 9, so two
margins have to fit in 9 and 5 would make the columns touch.

### The proof

An offline check renders both screens at **all four resolutions** with
**two name sets** — the longest field name each of the eight categories
can offer out of the committed stand-in, and a synthetic name longer
than any technology has, which is what the shrink rule has to survive.
The text is measured as the DIFFERENCE between a render with the text
and one without, so it is the drawing that is measured and not a second
computation of where the drawing should have gone.

Every text pixel must lie inside its own box's inner rect or in the
header strip above it; the hover band must be inside its box by at
least 2 px on each side and must change nothing outside its own row;
CANCEL must stay inside the button the wire reported; the description
box must stay inside the help panel.

Counter-tests, both red (`D_text_red.txt`):

| mutation | what went red |
|---|---|
| `BOX_MARGIN = 0` — the box hugs the text | 8 of 7686 text pixels outside, at 1440p |
| the field name moved onto the box's top edge | 36 of 4316 outside, at 1080p |

### And then looked at, every one

All four captures in `D_resolutions_4/`, at 1:1. The names sit inside
their boxes with a visible margin, the header words stay above, the
corner lamps are round at every size and the title is there at every
size. Nothing the eye found was missing from the check this time — the
one thing it did find, the missing 4K title, was found in part B and is
fixed there.

## Part E — one counter in the tree — **DONE**

`tools/colony_move_hd.Counter` is gone. It and `livedrive.SendCounter`
were two classes doing one job — SendCounter was written from it — so
when work order 165 H found that a counter which never puts the client
back keeps counting the steps after it, only the younger one was
repaired and nobody was going to fix the same fault twice.

Its three callers (`colony_move_hd`, `game_menu_hd`,
`colony_drop_sweep`) take `SendCounter` under its own name, not an
alias: an alias is a second name for one thing, which is how a reader
ends up believing there are two. `SendCounter` gained the `__repr__`
its callers print. No record on disk changed.

A check reads the tree by `ast` — a class is what is being counted, and
a name in a comment is not one — and asserts there is exactly ONE class
that replaces the client's three send methods. `setattr` is part of the
shape, or the test counts every stub client in the tree instead.
Counter-test: a second such class anywhere under `tools/` turns it red
(`E_one_counter_red.txt`).

---

## What the fresh-clone run caught, twice

The fifth and sixth occurrence of the fault the fundament describes
under *"A CHECK THAT READS THE PLAYER'S OWN FILES PASSES ON THE MACHINE
THAT WROTE THEM"* — and the fresh-clone gate caught both, as it has
caught every one before them.

`080f` sets the committed stand-ins and then has the dispatcher OPEN
the overlay. **Opening it ENTERS the screen**, and `enter` rebuilds its
two loaders from the real tree: here they come back `ok` and nothing is
noticed; in a clone they come back missing, the screen is not READY,
`render_content` returns early, and the outer frame the block measures
is never drawn. The check failed on "the frame changed nothing in the
bands", which was true and was not the frame's fault.

Setting them after the first open was not enough — the click control
closes and reopens the overlay — so the second run failed the same way.
They are set again in both places now, and the block **asserts the
screen is READY before it measures**, so a clone that is not gets the
reason instead of a symptom.

## Closing

| | |
|---|---|
| suite | **278** green, full and fast, here and in a fresh clone (`fresh_clone.txt`: full 64 s, fast 38 s) |
| working tree | clean |
| SAVE10 | reloaded and confirmed: stardate 3500.3, 2 players, 54 stars, 28 colony records |
| every `SAVE*.GAM` | byte-identical to the start of work order 165 — nothing was ever saved |
| captures | `~/orionlayer-fixtures/evidence/work_order_166/` |
