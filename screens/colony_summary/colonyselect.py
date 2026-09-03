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

Split out of `screen.py` on 3 September 2026, when that file reached
691 lines against a ~300 guideline (decision 6). Nothing here draws
or hit-tests: geometry stays with the screen, which owns the boxes,
and this module never imports pygame.
"""
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
