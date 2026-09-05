"""The original's pop icons: which pop each one is, and where it sits.

`colonymove` mirrors the RULES; this module mirrors the LIST the
rules are applied to. They are separate because they fail
differently: a wrong rule refuses a move that would have worked, a
wrong list moves the wrong pops and every number on both screens
stays correct.

**A COLUMN IS NOT `pop[]` IN ARRAY ORDER, and that is the whole
reason this file exists.** `Do_Colony_Info_Pop_Stuff_For_Pop_`
(coldraw.cpp:282-386) walks five nested loops to decide which icon is
drawn where:

    for state       0..6      `Pop_To_Pop_State_`, so 2, 3, 4
      for conquered 0..1      `(pop & 0x400) >> 10`
        for job     the column
          for nibble in (9, 0, 1, 2, 3, 4, 5, 6, 7, 8)
            for i   0..n_pops, in array order

so normal pops come before natives, natives before androids, and a
conquered pop after an unconquered one of the same state. Only INSIDE
one of those groups is the order the array's. The fundament's "within
an identical group the icons are drawn in array order" is exactly
right and is exactly as far as it goes: `Get_Cluster_` takes an
identical group, so a cluster IS a run of adjacent icons — but the
icon at slot m of a column is not the m-th pop of that job.

The source calls the second loop `race_idx`. It is the CONQUERED bit
(`POP_MASK_CONQUERED`, pop.h:12), and this module names it that, for
the reason `core/structs/colony.py` refuses to call the low nibble a
race: a wrong name outlives every comment that corrects it.

**ONLY ASSIGNED POPS ARE ICONS** — `(pop_val & 0x200) != 0`,
coldraw.cpp:343. A pop in a held cluster has that bit cleared and
draws nothing, which is how the original shows a cluster in hand. The
HD row's squares come from `colonyrows.build_rows`, which counts
every pop of a job whether it is assigned or not, so the two lists
have the same length only while nothing is held. `slot_pop` answers
None past the end of the icon list rather than guessing, and the
caller refuses the click — see `colonypick`.

**THE GEOMETRY IS A SQUISH, NOT A CONSTANT PITCH.**
`Calculate_Squish_Step_` (coldraw.cpp:12-33) divides the column by
the icon count, so a colony with twelve farmers draws them at a 9 px
pitch where four would sit at 30. `30 / -3` is C truncation toward
zero and is -10 exactly; it is written as such below because the
integer divisions are the transcription and a float would round the
other way on the odd counts.

**WHAT THE CLICK IS COMPARED AGAINST IS THE SCROLL FIELD'S VALUE, NOT
THE CLICK POINT** — corrected 5 September 2026, against the
fundament, which said `Get_Selected_Pop_` reads `mouse::Pointer_X_()`.
The chain is one link longer and the extra link matters:

  `Get_Selected_Pop_` (colsum.cpp:1006) calls mode 3, whose test is
  `*scroll_value_ptr <= (30 - squish) * (slot + 1) + left_x ||
  *last_slot_idx_ptr == slot` (coldraw.cpp:361);

  `scroll_value_ptr` is the value of the scroll field mode 1 added
  over the column (coldraw.cpp:409), and `Find_Bar_Position_`
  (fields.cpp:1702-1743) writes it from `mouse::Pointer_X_() +
  _pointer_offset` when the field is pushed down
  (`Draw_Field_`, fields.cpp:2837);

  the field's range is `(left_x, right_x + 8)` over a width of
  `right_x - left_x + 8`, so the arithmetic reduces to the identity
  and the value IS the pointer x, clamped to `[left_x, right_x]`.

Two consequences a click frame has to live with, and neither is
something this module can compute away. The value SURVIVES between
clicks, because nothing resets it — so a column that has never been
pushed carries whatever it last held. And `_pointer_offset` is the
current mouse picture's frame number (mouse.cpp:115), which is not
zero for every cursor. Both are why the caller VERIFIES the cluster
the game actually took against the one it predicted, instead of
trusting this arithmetic: the interlock is the measurement, and this
is only the aim.
"""
from core.structs import colony as colony_struct

#: `pop_order` in `Do_Colony_Info_Pop_Stuff_For_Pop_`
#: (coldraw.cpp:287-297). Natives (low nibble 9) are drawn before
#: player indices 0..8 — inside their own state group, which is where
#: the state loop has already put them second.
POP_ORDER = (9, 0, 1, 2, 3, 4, 5, 6, 7, 8)

#: The state loop's range, coldraw.cpp:325. `Pop_To_Pop_State_` can
#: only return 2, 3 or 4 (colony.cpp:1240), so four of the seven
#: passes find nothing; the range is transcribed rather than reduced,
#: for the same reason `colonymove` keeps `state == 6`.
STATE_COUNT = 7

#: `icon_spacing`, the fourth argument every call site passes
#: (coldraw.cpp:409 and :419). The unsquished pitch.
ICON_SPACING = 30

#: (left_x, right_x) per job, from `Get_Selected_Pop_`
#: (colsum.cpp:1006-1024), which passes `ebp_val` as left and
#: `ebx_val - 10` as right. `Add_Fields_Pop_For_` (colsum.cpp:311-345)
#: builds the fields from the same pairs.
COLUMNS = ((101, 226), (236, 368), (378, 502))

#: A row's top and its pitch — `colony_idx * 31 + 34`,
#: colsum.cpp:311-345, and the scroll field's height 30
#: (coldraw.cpp:409). The row a click names is a SLOT in the game's
#: window, never a colony (decision 46).
ROW_TOP, ROW_PITCH, ROW_HEIGHT = 34, 31, ICON_SPACING


def _state(word):
    """`Pop_To_Pop_State_` (colony.cpp:1240) — 3, 4 or 2.

    A second copy of `colonymove.pop_state`, and deliberately not an
    import: this module transcribes a DRAWING loop and that one
    transcribes the RULES, and the day one of them is found to be
    wrong is the day the other has to be re-read rather than silently
    corrected with it. They are three lines each and the smoke test
    holds them to agreeing.
    """
    nibble = colony_struct.pop_player_index(word)
    if nibble == 9:
        return 3
    if nibble == 8:
        return 4
    return 2


def icon_pops(pops, n_pops, job):
    """The pop indices of one column's icons, in DRAW order.

    This is mode 1's `pop_index_by_slot[]` (coldraw.cpp:352) computed
    without the game: slot i of column `job` shows pop `icon_pops(
    …)[i]`. The five loops are transcribed in their own order, which
    is what makes the answer the original's rather than a plausible
    one.
    """
    limit = min(int(n_pops), len(pops))
    order = []
    for state in range(STATE_COUNT):
        for conquered in (0, 1):
            for nibble in POP_ORDER:
                for i in range(limit):
                    word = pops[i]
                    if colony_struct.pop_player_index(word) != nibble:
                        continue
                    if _state(word) != state:
                        continue
                    if colony_struct.pop_prof(word) != job:
                        continue
                    if not colony_struct.pop_is_assigned(word):
                        continue
                    if bool(word & colony_struct.POP_MASK_CONQUERED) != bool(
                            conquered):
                        continue
                    order.append(i)
    return tuple(order)


def slot_pop(pops, n_pops, job, slot):
    """Which pop icon `slot` of a column is, or None.

    None is the answer for a slot past the end of the icon list, and
    it is a state rather than an error: the HD row draws a square for
    every pop of a job and the game draws an icon only for the
    ASSIGNED ones, so the two lists differ exactly while a cluster is
    held. A caller that guessed here would aim at an icon that is not
    on screen.
    """
    icons = icon_pops(pops, n_pops, job)
    if 0 <= slot < len(icons):
        return icons[slot]
    return None


def pop_slot(pops, n_pops, job, pop_index):
    """Where a pop sits in its column, or None if it draws no icon."""
    icons = icon_pops(pops, n_pops, job)
    return icons.index(pop_index) if pop_index in icons else None


def squish_step(left_x, right_x, count, spacing=ICON_SPACING):
    """`Calculate_Squish_Step_` (coldraw.cpp:12-33), returning the
    PITCH — the `30 - _step_squish` every draw and every hit test
    multiplies by.

    Transcribed with its integer divisions intact. `spacing / -3` is
    -10 for the only spacing any call site passes, and it is written
    as the division because that is what the source computes; C
    truncates toward zero, which for these values is the same as
    Python's `int()` and is NOT `//`.
    """
    divisor = max(int(count), 1)
    intermediate = int(spacing / -3) - int(left_x) + int(right_x)
    step = int(intermediate / divisor)
    if step <= 1:
        step = 1
    return step if step < spacing else spacing


def column_pitch(job, count):
    """The pitch of one job column at this icon count."""
    left_x, right_x = COLUMNS[job]
    return squish_step(left_x, right_x, count)


def slot_right_edge(job, slot, count):
    """`(30 - squish) * (slot + 1) + left_x` — the value the walk
    compares against (coldraw.cpp:361)."""
    left_x, _right = COLUMNS[job]
    return column_pitch(job, count) * (slot + 1) + left_x


def slot_at(job, value, count):
    """The slot the original's walk would select, or None.

    Mode 3, transcribed including the `||` that makes the LAST slot
    the fallback: a value past every icon selects the last one rather
    than nothing (coldraw.cpp:361). `None` is only for a column with
    no icons at all, where `Get_Selected_Pop_` returns -1 and
    `Get_Cluster_` is never called.
    """
    if int(count) <= 0:
        return None
    last = int(count) - 1
    for slot in range(int(count)):
        if value <= slot_right_edge(job, slot, count) or last == slot:
            return slot
    return None


def slot_click_x(job, slot, count):
    """The x to inject so the walk lands on `slot`.

    The icon's own right edge, which is the largest value that still
    selects it — the walk takes the FIRST slot whose right edge is at
    or past the value, so anything from one past the previous edge to
    this one works and the edge itself is the one number the source
    writes down.

    It cannot fall outside the column: the pitch is
    `(right_x - left_x - 10) / count` truncated, so the last icon's
    right edge is at least ten px inside `right_x` and the clamp in
    `Find_Bar_Position_` never bites. The clamp is applied anyway,
    because a `count` that did not come from `icon_pops` would
    otherwise aim outside the field and the failure would be a click
    that lands on the wrong icon rather than one that is refused.
    """
    _left, right_x = COLUMNS[job]
    return min(slot_right_edge(job, slot, count), right_x)


def row_click_y(row_slot):
    """The y to inject for a row of the GAME's window.

    `colony_idx * 31 + 34` is the top of the row's fields
    (colsum.cpp:311-345) and the scroll field is 30 high, so the
    middle is `+ 15`. The argument is a SLOT in the game's ten-row
    window and never an HD row (decision 46).
    """
    return ROW_TOP + ROW_PITCH * int(row_slot) + ROW_HEIGHT // 2
