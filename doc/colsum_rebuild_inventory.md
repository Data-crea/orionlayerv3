# Colony management rebuild — Stage 0 inventory

**6 September 2026.** What is in `screens/colony_summary/` today,
which of it survives the rebuild, and what each replaced module owns
that must not be lost with it. **Nothing is deleted yet.**

The three buckets are the brief's. The classification is not asserted:
it was checked against each module's imports and its use of pygame,
which is the objective form of "does this decide where pixels go".

| module | code | pygame | draws | class |
|---|---:|:---:|:---:|---|
| `colonyrows.py` | 204 | no | no | **LOGIC** |
| `colonyicons.py` | 68 | no | no | **LOGIC** |
| `colonymove.py` | 132 | no | no | **LOGIC** |
| `colonypick.py` | 96 | no | no | **LOGIC** |
| `colonysend.py` | 219 | no | no | **LOGIC** |
| `colonyfirst.py` | 33 | no | no | **LOGIC** |
| `colonyselect.py` | 104 | no | no | **LOGIC-WITH-GEOMETRY** |
| `colonymoveui.py` | 172 | no | yes | **LOGIC-WITH-GEOMETRY** |
| `screen.py` | 300 | yes | yes | **LOGIC-WITH-GEOMETRY** |
| `colonytrack.py` | 117 | yes | no | **PRESENTATION** |
| `colonylist.py` | 194 | yes | yes | **PRESENTATION** |
| `colonypopup.py` | 61 | yes | yes | **PRESENTATION** |
| `colonyoutput.py` | 108 | no | yes | **PRESENTATION** |
| `colonyempire.py` | 53 | yes | yes | **PRESENTATION** |
| `colonybuild.py` | 46 | yes | yes | **PRESENTATION** |
| `colonyinset.py` | 60 | yes | yes | **PRESENTATION** |

1 967 code lines in sixteen modules. **1 328 of them (nine modules)
are LOGIC or LOGIC-WITH-GEOMETRY and are kept**; 639 (seven modules)
are presentation and are replaced — two thirds of the screen survives
the rebuild, and it is the two thirds that talks to the game.

---

## LOGIC — kept as is

### `colonyrows.py` (204) — the snapshot becomes numbers
`build_rows` and everything under it: the struct reads, the sort
comparators and `SORT_UNAVAILABLE`, `max_population`, `colony_morale`
with the Unification rule, `drawn_production`'s four branches and the
`(int8_t)` cast, `production_shortage` and its two refusals,
`galaxy_inset_stars` (the inset transform and its four colour
branches), `galaxy_inset_label`, `planet_name`, and `cells` — one
entry per drawn ICON in `colonyicons.icon_pops` order.

**This module is where the rebuild's content comes from.** The new
panels do not re-read structs; they take these dicts, exactly as
`colonyoutput` does today.

### `colonyicons.py` (68) — the ORIGINAL's geometry, not ours
`icon_pops`, `slot_pop`, `pop_slot`, `squish_step`, `column_pitch`,
`slot_right_edge`, `slot_at`, **`slot_click_x`**, **`row_click_y`**,
`COLUMNS = ((101,226),(236,368),(378,502))`, `ROW_TOP/PITCH = 34/31`.

It contains geometry and it is still LOGIC, because the geometry is
the GAME's 640x480 and not ours: it is what an injected click is
aimed with. `colonysend` calls `slot_click_x` and `row_click_y` for
every PICK and DROP it sends (`colonysend.py:354`, `:356`, `:378`,
`:395`). **Changing anything here changes where clicks land in the
game.** It must come through the rebuild untouched.

`doc/pop_stacking.md` §1 corrects one thing about it that is worth
carrying: the draw top is `row*31 + 38`, the FIELD top is
`row*31 + 34`. `ROW_TOP = 34` is right for the click, which is the
only thing this module aims, and is not the draw origin.

### `colonymove.py` (132) — the five engine rules
`plan_pickup`, `plan_drop`, `predict_pops`, `pop_state`,
`Pops_Identical_`, the four `Give_Colonist_New_Job_` refusals plus
the native refusal at pick-up, and the `state == 6` arm that is
transcribed although it is unreachable.

### `colonypick.py` (96) — the HD decision layer
`Pick`, `Refusal`, `DropPlan`, `pick_at`, `plan_move`, `message`,
`pops_of`, `sort_binds`, and the three refusals that are ours rather
than the engine's (`sort_unavailable`, `no_icon`, `other_colony`).
**Nothing in it can send anything**, and a smoke check asserts the
import list stays that way.

### `colonysend.py` (219) — the wire chain
RESORT → ESTABLISH → PICK → DROP, `_Wait` with the `EFFECT_PAIRS`
floor plus a predicate, `held_cluster`, the interlock that verifies
the cluster the game actually took, and the `HOLDING` state.

### `colonyfirst.py` (33) — `_first` read back off the thumb
Pure arithmetic over the original's framebuffer. Already scheduled
for demotion by the H1 task (the five screen-state values additive in
`src/ext/`); it is unaffected by this rebuild either way.

---

## LOGIC-WITH-GEOMETRY — kept, geometry call replaced

### `colonyselect.py` (104)
The selection (`_g_colony_n` as a COLONY, never a row index; entry on
row 0 of the sorted list; `_reseat_selection` across a sort) and the
scroll `Window` (`top`, `row_at`, `rows_drawn`, the wheel and slider
clamps transcribed from `Update_First_`).

**Geometry calls to replace:** `colonylist.row_at` (3 sites),
`colonylist.rows_drawn` (2 sites). Both re-export `colonytrack`.

### `colonymoveui.py` (172)
`MoveController` — `click`, `_first_click`, `_second_click`, `hover`,
`cancel`, `advance`, the wording lookups, and the "click on the held
pop's own group discards and sends nothing" rule.

**Geometry calls to replace:** `colonylist.cell_at_x`,
`colonylist.drop_band` (2 sites), `colonylist.row_bands` (2 sites),
plus the three draw calls `draw_drop_bands`, `draw_pick`,
`draw_popup`, whose existence is a Stage 3/4 question rather than a
mechanical port (see the HD EXTENSION list below).

### `screen.py` (300)
**Kept:** `enter`/`update`/`on_resize`, `_push_sort_key`,
`_rebuild_rows`, the busy guard on `handle_click`, the sort-button
handler with its three transcribed rules (no direction toggle,
`_first = 0`, the selection keeps its colony), `_inject`, the RETURN
handler, `handle_right_button`'s help-then-cancel order,
`handle_mouse_motion`, `handle_mousewheel`, `_hit`, and the
deliberately inert row click with the reasoning that keeps it inert.

**Replaced:** `render`, `_render_frame_image`, `_render_title`,
`_render_panels`, `_render_list`, `_render_inset`, `_render_output`,
`_render_sidebar`, `_render_buttons`, `_render_move`, `_list_view`,
`_load_frame`, `_scale_frame`, `box_style`.

It is at **exactly 300 code lines** with no headroom, so the rebuild
must not add to it; the render side moving out is what makes room.

---

## PRESENTATION — replaced, and what must survive each one

### `colonytrack.py` (117) — decision 5's current home
`row_boxes`, `track_metrics`, `track_x`, `row_regions`,
`drop_targets`, `drop_band`, `cell_at_x`, `row_bands`, `row_at`,
`rows_drawn`, `MARKER_COUNT`, `MARKER_SLOTS_DEFAULT`.

**Must survive:** the ROLE, not the arithmetic. One function produces
the rect and both drawing and hit-testing call it; the new geometry
module inherits that and the reason for it — the drop targets were
two copies of a thirds calculation that agreed with each other and
disagreed with the squares, and `draw_pick` computed a third copy
that was wrong for two of three jobs from the day it was written.
Also: `row_bands` drops the last row rather than clipping it, so a
row that can be hovered is by construction a row that is on screen.

### `colonylist.py` (194) — the row
`render`, `_render_bar`, `_draw_name_block`, `_cell_mark`,
`draw_pick`, `draw_drop_bands`, `_draw_no_farming`, `_dashed_rect`,
`_draw_overflow`, the palette constants.

**Must survive:**
- **the click-offset correction**, and it must be RE-DERIVED, not
  copied. The chain that works today is: HD cell index k of job j ==
  icon slot k of column j == what `slot_click_x(j, k, count)` aims
  at. It holds only because `colonyrows` builds `cells` in
  `icon_pops` order (decision 48). In the new geometry the same
  identity must be re-established against the figure run and proved
  live, per the brief.
- **the name column's ellipsis threshold** measured in reference px
  and NOT in the drawn width, so the same name cuts at the same
  length on every monitor;
- **`slack` goes to the name column's drawn width only** — the
  pixels six floor divisions drop, which used to land at the right
  edge as dead air;
- **`_pad_left` / `frame_inset`** — text kept off the frame's rim,
  one value for the whole screen (`screen._frame_inset`);
- **"No Farming" is drawn AFTER the run** and must not be painted
  over — the fault that was invisible with every number correct;
- **`_draw_overflow`'s "n not shown" line**, in its own colour so it
  cannot be mistaken for a colony;
- the transcription that a row is one colony and the window belongs
  to the game (decision 46).

### `colonypopup.py` (61) — the hover popup
`lines_for`, `rect_for`, `draw`. **An HD EXTENSION with no original.**
It overlays, never reflows, flips above at the panel bottom and never
appears while a pick is held. Whether it exists at all in the
original layout is a Stage 4 question, not a port.

### `colonyoutput.py` (108) — the scan box
Today one panel; the new layout splits it into `planet_info` and
`planet_output`.

**Must survive:** it is a TRANSCRIPTION and decision 43 (which called
it an HD EXTENSION) is WITHDRAWN — the original draws all of it
(`Draw_Colony_Scan_Info_`, colsum.cpp:1155). The seven values and
their order, the production column from native x 106 with morale
below it, `empty` drawing NOTHING rather than a zero, and the
substitution being a `replace` and never `str.format` (decision 37).
The numbers themselves are `colonyrows`' and stay.

**The shortage marker's rule** lives across `colonyrows.production_shortage`
(kept) and `layout.json._shortage_note` (kept): the marker is drawn
only when imports are non-negative AND the row is not industry; it
FOLLOWS the value; the pair is right-aligned as a group; no element
at all when the shortage is zero; and 0xED is now resolvable through
`core/lbx.py` but is not applied, the `warn` substitute stays.

### `colonyempire.py` (53) — the empire sidebar
Six `s_player` scalars in the original's order, each with its
explicit plus and its red-if-negative, from
`Draw_Empire_Info_` (colsum.cpp:418). Becomes `empire_stats`.

**Must survive:** the six offsets and their order; `FRAME_INSET_DEFAULT`,
which `screen._frame_inset` still reads; and **decision 44's clamp
with its DEVIATION marking**, which two smoke checks assert by
calling `native_column_width` and `value_column` directly and by
grepping this file for the marking string. Those two checks must move
with the behaviour in the same commit or they will pass against a
file that no longer contains what they assert.

### `colonybuild.py` (46) — the building column
**Must survive, and it is a measurement that is easy to get twice as
large:** the column width is a RESERVATION, not a squeeze target.
`BILL::_Squeeze_Print_Paragraph_` (bill.cpp:147) wraps into the width
and shrinks the HEIGHT; width never moves and there is no truncation
branch. 85 of 640 native px is 13.3 %, which is 190 of 1408 today and
becomes 314 of 1832 in the new list — **the percentage is the
transcription, the pixel count is derived from it.** Also the Buy
control being a text button because the sprite is in the player's own
LBX.

### `colonyinset.py` (60) — the galaxy inset
Rebuilt wholesale per `doc/colony_inset_geometry.md`.

**Must survive:** it draws NO background of its own, by transcription
(`Draw_Galaxy_Map_Box_` fills black only when
`_using_colony_screen_palette == 0`, movebox.cpp:36-38) — the fill is
a per-box value, and the lesson that came with it, that the fill must
be read from the block the value lives in. And the guard that this
panel **sends nothing**: the original's stars are fields and ours are
not (decision 46), asserted by a smoke check.

---

## What is NOT a module and must be decided rather than ported

Eight **HD EXTENSIONS** currently live in the presentation layer.
Each needs an explicit keep/retire decision in Stage 3 or 4, because
the original's layout is exactly the thing several of them were
invented to compensate for:

| extension | why it exists today | status in the rebuild |
|---|---|---|
| three job markers per row | a row without columns cannot carry a heading | **the original HAS columns again** — the reason is gone |
| the identity letter in a cell | one track, no columns, so the cell carried both | **columns are back**; the original's own sprite carries race |
| drop bands per job | HD zones are sized by the data | the original's three columns are fixed and always clickable |
| the empty-group placeholder | already retired by the markers | stays retired |
| the growth boxes and the beyond-line | `max_pop` made visible | no original; open |
| the hover popup | no original | open |
| the cancel (right click / off-rows) | our selection is not the game's cluster | **keep** — it rests on nothing presentational |
| "click on your own group discards" | matches the original's outcome | **keep** — same reason |

The last two are the only ones whose argument survives the layout
change untouched. The first three were argued FROM the single-track
row and their premise is what this rebuild removes.

**And one deviation that is not an extension:** a partial move is
refused before it is sent, because the original's refusal opens a
blocking modal over a screen HD does not draw. That is `colonypick`'s
and is kept.

---

## Smoke-test anchors that move with the code

Fifteen of the sixteen modules are named in `tools/smoke_test.py`.
Six checks read a module's SOURCE FILE and grep it for a marking:
`colonylist.py` (twice), `colonyinset.py`, `colonymove.py`,
`colonypick.py`, `colonysend.py`, `colonyempire.py`, `colonyrows.py`,
`colonybuild.py`. **A grep-for-a-marking check does not fail when its
subject is deleted — it fails when the file is missing, which is the
same commit, but it passes silently if the marking is moved to a file
it no longer reads.** Each replaced module's markings therefore need
their check re-pointed in the same commit, and the check count must
not drop (86 today).

---

## Two things to settle before Stage 1

1. **`doc/colony_inset_geometry.md` Part 3 is not written.** The
   brief's Stage 1 makes the 253x200 inset conditional on it, and
   Part 3 was deliberately stopped pending confirmation of Parts 1
   and 2. Stage 1 cannot put that box in the mask until it exists.
2. **`doc/pop_stacking.md` §9 lists seven open questions**, three of
   which the column widths depend on: whether HD reproduces the
   overlap or uses its width, what replaces the formula if it uses
   the width, and whether a figure run keeps the cell-based drop
   target, popup anchor and identity mark. The brief already calls
   the column widths provisional; these are the questions that make
   them final.
