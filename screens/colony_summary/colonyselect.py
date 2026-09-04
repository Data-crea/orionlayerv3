"""Which colony the scan box is showing, and how that changes.

The original keeps exactly one number for this — `COLONY::_g_colony_n`
— and everything on the screen that is per-colony reads it. This
module is that number plus the two rules that move it, kept together
because they only make sense together: a selection stored the wrong
way still looks right on entry and goes wrong on the first sort.

**It holds a COLONY, never a row index.** The sort handler
(colsum.cpp:830-837) re-sorts the list, clears the window array and
resets `_first`, and never touches `_g_colony_n` — so the selected
colony keeps its identity and moves to wherever the new order puts
it. A row index would keep the highlight still and change the colony
under it, which is the opposite behaviour and is indistinguishable
from the right one until something re-sorts.

**Entry lands on row 0 of the SORTED list.** colsum.cpp:139 assigns
`_g_colony_n = COLSUM::_list_col[0]` in the screen's setup, before
the input loop runs, and `_list_col` is filled from the sorted
`_g_colony_list_ptr` by `Update_Col_List_` (colsum.cpp:348-351) — so
it is the first row as sorted, not the first colony in the array.

**After that it follows the pointer, not the clicks.**
`Evaluate_Colony_Pop_Input_` is handed the clicked field and the
scanned one as two separate arguments and it is the SCANNED one that
assigns `_g_colony_n`, over a row's name, producing or buy field
(colsum.cpp:880-890). "Scanned" is this engine's word for hovered:
`fields::Scan_Input_` (fields.cpp:652) returns the field under the
pointer with no button involved, and colsum.cpp:159-162 hands
`Evaluate_Input_` both values every frame.

**Leaving the list keeps the last colony.** That assignment has no
else branch, so `_g_colony_n` holds whatever it last held. It is
also the only thing that makes the panel readable — one that emptied
whenever the pointer left the rows would be blank most of the time.

**THERE ARE TWO WINDOWS IN THIS FILE AND THEY ARE NOT THE SAME
NUMBER.** `Window` is HD's viewing offset over the rows it draws, and
how many it draws comes from `list_area` and `row_height`.
`GameWindow` is the ORIGINAL's ten slots. They are adjacent on
purpose: decision 46's corollary is precisely that confusing the two
is the available mistake, and a reader who meets only one of them is
the person who makes it.

**A SORT TOUCHES BOTH OF THIS MODULE'S OBJECTS, AND DIFFERENTLY.**
That is why the scroll window lives here beside the selection rather
than in a module of its own. `Sort_Col_List_`'s handler re-sorts,
clears the window array and sets `_first = 0` (colsum.cpp:830-837) —
so the WINDOW goes back to the top — and it never assigns
`_g_colony_n`, so the SELECTION keeps its colony and simply moves to
wherever the new order puts it. Two rules for one event, opposite in
what they preserve, and a reader who sees only one of them will
guess the other wrong.

Split out of `screen.py` on 3 September 2026, when that file reached
691 lines against a ~300 guideline (decision 6), and grown on
4 September when `Window` took the two methods that were only ever
about the offset.

**Nothing here draws.** It hit-tests now, which it did not before:
`Window.row_at` turns a point into a row index, because that answer
is a band number PLUS the offset and the offset is the whole of what
this module is for. The rect and the config are handed in — the
screen still owns the boxes and resolves `list_area` itself — so
this module reaches no box, no style and no surface.

It does reach `colonylist` for two pure functions of
(area, cfg, scale, count), `rows_drawn` and `row_at`, which is where
the row pitch is computed once for the drawing and the hit-test alike
(decision 5). That import brings pygame in transitively, and the
sentence that used to stand here — *this module never imports
pygame* — is no longer true and is not worth preserving by keeping a
second copy of the pitch instead.
"""
from . import colonylist
from . import colonyrows


class Selection:
    """The rows for one snapshot, and which colony is selected."""

    def __init__(self):
        self.rows = []
        #: The colony's index in the snapshot's array — the same
        #: number `_list_col[]` holds. None only when there are no
        #: colonies at all.
        self.colony = None

    def rebuild(self, state, sort_key):
        """Rebuild the rows and keep the selection pointing at a
        colony that is still in them.

        Called when the snapshot changes and when the sort key does,
        rather than once per frame in the renderer. The hover has to
        hit-test the SAME list the renderer drew, and two lists built
        from one snapshot agree today but would stop agreeing the
        first time anything about the build depended on when it ran.
        """
        self.rows = colonyrows.build_rows(state, sort_key)
        self.reseat()

    def reseat(self):
        """Keep the selected colony if it is still listed, else row 0.

        A selection whose colony has left the list — lost, or the
        snapshot changed under us — falls back to row 0 rather than
        to nothing, because the original has no state in which this
        screen is up and no colony is scanned. Nothing is selected
        only when the list is empty.
        """
        if not self.rows:
            self.colony = None
            return
        if any(row["index"] == self.colony for row in self.rows):
            return
        self.colony = self.rows[0]["index"]

    def hover(self, index):
        """Select the colony in row `index`; a None index changes
        nothing, which is the source's missing else branch."""
        if index is not None and 0 <= index < len(self.rows):
            self.colony = self.rows[index]["index"]

    def row(self):
        """The selected row dict, or None. The panel's whole input."""
        for row in self.rows:
            if row["index"] == self.colony:
                return row
        return None

    def position(self):
        """Where the selection sits in the CURRENT order, or None.

        Only the smoke test and a future highlight want this. The
        selection itself is never stored this way — see the module
        docstring for why that distinction is the whole point.
        """
        for i, row in enumerate(self.rows):
            if row["index"] == self.colony:
                return i
        return None


class Window:
    """Which slice of the rows is on screen — the HD side of `_first`.

    **It scrolls for VIEWING ONLY, and nothing here reaches the game**
    (decision 46). The original's list is ten SLOTS over the sorted
    array, `_list_col[i] = _g_colony_list_ptr[_first + i]`
    (colsum.cpp:348-351), and every clickable field in a row is built
    per slot (`Add_Fields_Pop_For_`, colsum.cpp:312-346) — so an
    injected click names a position in the GAME's window, which this
    number is not. Every colony is already in the snapshot, so HD can
    show any of them without the game knowing; what it must not do is
    inject while the two windows disagree. Synchronising them is
    decision 46's other half and is not built yet, which is why a
    smoke check asserts that no scroll path sends anything at all.

    **THE CLAMPS ARE TRANSCRIBED, not chosen.** All three:

      lower bound 0    `Decrement_First_` computes `_first - 1` and
                       floors it (colsum.cpp:211-214).
      upper bound      `Increment_First_` is reached only when
                       `_g_colony_list_ptr[_first + 10] != -1`
                       (colsum.cpp:796) — the original refuses the
                       step that would leave the window's last slot
                       empty, so its last page is FULL. That is
                       `first <= n_rows - visible`.
      too few rows     neither step runs at all when
                       `colonies_count < num_items` (colsum.cpp:210
                       and :226), and `Update_First_` additionally
                       forces `_first = 0` in that case every draw
                       (colsum.cpp:194-197).

    That third source is why `clamp` MUTATES and is called on the way
    in rather than only when the offset moves: `Update_First_` runs
    from `Draw_Bar_Indicator_` (colsum.cpp:749) on every frame, so
    re-establishing the offset against the current row count is the
    original's own shape and not a defensive habit. A window left
    pointing past a shrunken list would otherwise spring back into
    range the moment the colonies returned.

    `visible` is always passed IN, never computed here: it is derived
    from `list_area` and `row_height` at the current resolution
    (`colonylist.rows_drawn`). It is ten today, which is the original's
    number, and that is arithmetic out of the frame artwork rather
    than a transcription — see `layout.json._row_height_note`, and
    decision 46's corollary for why the coincidence must not be
    leaned on.
    """

    def __init__(self):
        #: Index into the sorted rows of the topmost DRAWN row.
        self.first = 0

    def limit(self, n_rows, visible):
        """The largest `first` the original would allow."""
        return max(0, n_rows - visible)

    def clamp(self, n_rows, visible):
        """Re-establish the offset against the rows there are now."""
        self.first = min(max(0, self.first), self.limit(n_rows, visible))
        return self.first

    def scroll(self, delta, n_rows, visible):
        """Move by `delta` rows and return the resulting `first`.

        The refusals are mirrored before the move, not after
        (decision 33): with fewer rows than fit, the original's two
        steppers do nothing at all, so neither does this.
        """
        if n_rows <= visible:
            self.first = 0
            return self.first
        self.first = min(max(0, self.first + delta),
                         self.limit(n_rows, visible))
        return self.first

    def reset(self):
        """Back to the top — what a sort does (`_first = 0`,
        colsum.cpp:832). The selection is deliberately not touched;
        see the module docstring."""
        self.first = 0

    # ── What the screen asks, in its own coordinates ──────
    #
    # These three take (area, cfg, scale, n_rows) and nothing else:
    # `area` is `list_area` already resolved to screen pixels, `cfg`
    # the `list` block of layout.json. The screen owns the boxes and
    # hands the rect over; what is done with it is the offset's
    # business, which is why they live here and not there.

    def visible(self, area, cfg, scale, n_rows):
        """How many rows `area` holds at this resolution.

        DERIVED, never ten. It is ten today — `layout.json`'s
        `_row_height_note` is where that arithmetic lives — and that
        is a property of the frame artwork, not a transcription of
        the original's `_list_col[10]`. Decision 46's corollary: any
        future synchronisation counts against the GAME's ten, not
        against this.

        It is also the number `clamp` and `scroll` need, which is the
        reason this is a method here rather than a helper on the
        screen: the window cannot bound itself without it.
        """
        return colonylist.rows_drawn(area, cfg, scale, n_rows)

    def top(self, area, cfg, scale, n_rows):
        """The topmost drawn row, re-established against the rows
        there are now.

        Reading CLAMPS, because the original does: `Update_First_`
        runs from `Draw_Bar_Indicator_` every frame and forces
        `_first = 0` whenever the colony count has fallen below the
        window (colsum.cpp:193-205, :749). A snapshot that loses
        colonies must not leave the HD list scrolled past its own
        end, and one method is the place every reader goes through.
        """
        return self.clamp(n_rows, self.visible(area, cfg, scale, n_rows))

    def row_at(self, area, cfg, scale, n_rows, point):
        """Index into the ROWS of the row under `point`, or None.

        The geometry comes from `colonylist.row_at`, which is the same
        function `colonylist.render` lays the rows out with — one
        source for the rect, per decision 5. A second copy of the
        pitch is how a list starts highlighting the row above the one
        it draws.

        `colonylist.row_at` answers in BAND numbers, which is what
        `render` draws in; the offset is added HERE, and that
        addition is the reason this method is on `Window` rather than
        on the screen. Getting it wrong is the exact fault decision 5
        exists for, one scroll offset removed — every row correct and
        the highlight `first` rows off — so `first` comes from the
        same `top` the renderer was handed, not from a second read.
        """
        if not n_rows or not area.collidepoint(*point):
            return None
        first = self.top(area, cfg, scale, n_rows)
        band = colonylist.row_at(area, cfg, scale, n_rows - first, point)
        return None if band is None else first + band


class FirstPlan:
    """A step sequence for the game's window, and why it is that long.

    `down` activations of `_x_fields[1]` then `up` of `_x_fields[2]`.
    `refused` names a target the game would not reach, in which case
    both counts are 0 — a plan that cannot be carried out is not
    shortened, it is refused.
    """

    __slots__ = ("down", "up", "first", "refused")

    def __init__(self, down=0, up=0, first=0, refused=None):
        self.down = down
        self.up = up
        self.first = first
        self.refused = refused

    @property
    def steps(self):
        return self.down + self.up

    def __repr__(self):
        return (f"FirstPlan(down={self.down}, up={self.up}, "
                f"first={self.first}, refused={self.refused!r})")


class GameWindow:
    """The original's ten-slot list window — `COLSUM::_first`.

    **NOT `Window`.** That one is how far HD has scrolled its own
    drawing; this one is where the GAME's list starts, and it is the
    only one an injected click cares about. Decision 46: the row a
    click names is a POSITION IN THE GAME'S WINDOW, so `_first` has
    to agree with the HD row before anything is sent.

    **ESTABLISHED, NEVER REMEMBERED.** Nothing on the wire reports
    `_first`, and the game's window is visible to a human whenever
    `ext::g_hide_window` is unset (platform.cpp:1379) — which is how
    this screen was compared against the original in the first place
    — so a remembered value is a lie the caller cannot detect. The
    plan therefore always starts by driving the window to a known
    end: `Decrement_First_` clamps at 0 (colsum.cpp:211-214), so
    enough decrements reach the top from wherever it was, and the
    increments then walk it to the target.

    **THE REFUSALS ARE MIRRORED BEFORE THE STEPS ARE COUNTED**
    (decision 33), because counting a step the game declined is
    exactly how the two windows come apart:

      below ten colonies, NEITHER stepper runs at all. Both are
      guarded by `colonies_count >= num_items` (colsum.cpp:210
      and :226), and `Update_First_` additionally forces `_first = 0`
      whenever the count is under the window (colsum.cpp:194-197).
      So the right plan is no steps, and the only reachable target
      is 0.

      the last page is FULL. `_x_fields[2]` only calls
      `Increment_First_` while `_g_colony_list_ptr[_first + 10] !=
      -1` (colsum.cpp:796), and that array is padded with -1 past
      the colony count, so `_first` stops at `n - 10`.

    **`n` IS THE GAME'S COUNT AND IT AGREES WITH HD'S ROWS.**
    `COLXPORT::N_Colonies_` (colxport.cpp:67) counts colonies whose
    `owner` is the player and whose `outpost_flag` is 0, which is the
    same pair `colonyrows.build_rows` filters on. One caveat that is
    not ours to fix: that function returns a table entry instead when
    `_cheezy_hack_col_count_state` is set, so a game in that state
    would count differently and nothing on the wire would say so.

    **THE POSITIONS MUST BE THE SAME ORDER.** A plan maps an HD row
    to a game slot by position, which only holds while both lists are
    sorted alike — which is why this screen pushes its own sort key
    to the game on entry rather than reading one (`screen.
    _push_sort_key`).
    """

    #: `COLSUM::_list_col[10]`, filled by `Update_Col_List_`
    #: (colsum.cpp:348-351). **This is not HD's row count**, which is
    #: derived from `list_area` and happens to be ten today; see
    #: `Window.visible` and decision 46's corollary.
    SLOTS = 10

    #: Reasons a target is unreachable. Wording is layout.json's.
    REFUSE_WINDOW_FIXED = "window_fixed"
    REFUSE_PAST_END = "past_end"

    @classmethod
    def max_first(cls, n_colonies):
        """The largest `_first` the game will hold.

        `n - 10`, from the guard at colsum.cpp:796 rather than from a
        clamp inside the stepper: the increment is refused when slot
        ten would be empty, so the last page is always full.
        """
        return max(0, int(n_colonies) - cls.SLOTS)

    @classmethod
    def scrolls(cls, n_colonies):
        """False when the window cannot move at all — under ten."""
        return int(n_colonies) >= cls.SLOTS

    @classmethod
    def plan(cls, n_colonies, target_first):
        """Steps to put the game's window at `target_first`.

        Safe direction first and unconditionally: `down` is the
        largest `_first` the game can hold, so the sequence reaches
        the top from any state without needing to know which one it
        was in.
        """
        n = int(n_colonies)
        target = int(target_first)
        if not cls.scrolls(n):
            if target != 0:
                return FirstPlan(refused=cls.REFUSE_WINDOW_FIXED)
            return FirstPlan(0, 0, 0)
        if target < 0 or target > cls.max_first(n):
            return FirstPlan(refused=cls.REFUSE_PAST_END)
        return FirstPlan(cls.max_first(n), target, target)

    @classmethod
    def slot_for(cls, n_colonies, position):
        """(plan, slot) putting the row at `position` in the window.

        The window is placed as early as it will go — `first =
        min(position, max_first)` — so a row near the end of a long
        list lands in the last full page rather than off it. `slot`
        is where the row then sits, and it is the number a click
        names.
        """
        n = int(n_colonies)
        pos = int(position)
        if pos < 0 or pos >= n:
            return FirstPlan(refused=cls.REFUSE_PAST_END), None
        first = min(pos, cls.max_first(n)) if cls.scrolls(n) else 0
        plan = cls.plan(n, first)
        if plan.refused:
            return plan, None
        slot = pos - plan.first
        if not 0 <= slot < cls.SLOTS:
            return FirstPlan(refused=cls.REFUSE_PAST_END), None
        return plan, slot
