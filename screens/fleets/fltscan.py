"""Which ship the panel shows — `MOX::_scanned_big_ship`, in HD.

**WHAT THE ORIGINAL DOES, read out of the source before anything was
built** (work order 153, Part B):

* The panel is printed under one condition and one only —
  `if (_scanned_big_ship > -1 && _scanned_big_ship < MAX_SHIPS &&
  _current_screen == SCREEN_FLEET)`, then
  `Print_Scanned_Ship_Data_(_fltscrn_big_icon[_scanned_big_ship].ship_idx)`
  (flt1.cpp:401-406).
* `_scanned_big_ship` is the HOVER and nothing else. It is set from
  `hovered_icon_idx` whenever that is not negative (flt1.cpp:616-620),
  and `hovered_icon_idx` is `Scan_Fltscrn_Big_Icons_`'s FIRST out
  parameter: result 4 sets only it, matching `scan_val.full`, the
  field under the pointer (flt2.cpp:938-946). A click matches `input`
  instead and sets BOTH (result 0 or 1, :925-935), so a positive first
  index is the hover — which is what work order 151 B measured live
  and the opposite of the star scanner on the same screen.
* **SELECTION NEVER FEEDS THE PANEL.** `_fltscrn_big_icon[i].selected`
  is a separate flag with its own sprite (`_selected_box_seg`,
  flt1.cpp:93-104); the scanned icon has its own
  (`Draw_Box_Around_Scanned_Ship_`, :89-91). A cell can wear both, and
  selecting twenty ships leaves the panel showing whichever one the
  pointer last crossed.
* **WITH NEITHER, THE PANEL KEEPS THE LAST HOVERED SHIP.** Nothing
  clears `_scanned_big_ship` when the pointer leaves the grid. It goes
  back to -1 on entering the screen (:528), on the scroll bar being
  DRAGGED (:449 — not on an arrow click, :731-735), after SCRAP
  (:714), and when the small-ship stack pointer changes (:677, :757,
  :765). At -1 nothing is printed and the area is empty.

**IT IS AN ICON INDEX, NOT A SLOT.** `_fltscrn_big_icon` is the whole
filtered list and the five rows are a window on it, so after an arrow
scroll the panel still shows the SAME ship — which may no longer be on
screen, in which case no box is drawn either
(`Draw_Fltscrn_Big_Ship_Icons_` only walks the visible ones). This
module stores the same thing for the same reason.

**AND HD HAS TO DO ITS OWN SCANNING.** The Extension API has no mouse
motion (open fixes 3 and 4), so the game's pointer never moves for a
client and the `scanned_big` on the wire is frozen wherever the game's
own cursor was left. Everything the panel needs is already in HD's
hands — the FLTS block's `ship_idx` and `ships_raw` from the same
snapshot — so **hovering sends nothing**, which it must not: one send
per mouse movement would flood the input loop the API does have.
"""

from . import fltgeom

#: The original's `_big_icon_display_columns`, via the one place this
#: tree keeps it. An absolute icon index is `first_row * this + slot`.
COLUMNS = fltgeom.GRID_COLUMNS


class Scan:
    """HD's own `_scanned_big_ship`: an absolute icon index, or -1."""

    __slots__ = ("icon", "_key")

    def __init__(self):
        self.icon = -1
        self._key = None

    def clear(self):
        """Entering the screen — flt1.cpp:528."""
        self.icon = -1
        self._key = None

    def follow(self, block):
        """Clear where the original clears. Once per snapshot.

        The original's four resets are events; HD sees states, so each
        is recognised by what it changes in the block. The stack
        pointer moving covers :677, :757 and :765; the icon count
        moving covers SCRAP (:714) and the two filters, which rebuild
        the list. **The scroll bar being dragged (:449) has no HD
        equivalent** — HD's bar has no draggable thumb, its wheel and
        its arrows go through the game's own arrow fields, and the
        original does not clear on those.
        """
        key = (block.get("stack"), block.get("icons"))
        if key != self._key:
            self._key = key
            self.icon = -1
        if not (0 <= self.icon < int(block.get("icons", 0) or 0)):
            self.icon = -1

    def hover(self, slot, first_row, own_stack, rows):
        """The pointer is over `slot`. True when the panel changed.

        Refused exactly where the original refuses, and for its
        reasons: a FOREIGN stack is outside
        `if (_PLAYER_NUM == _fltscrn_stack_owner)` (flt1.cpp:615), and
        an EMPTY slot has no icon to match because the scan loop stops
        at `_n_fltscrn_big_icons` (flt2.cpp:906-909). Both leave the
        panel on the ship it was already showing.
        """
        if slot is None or not own_stack:
            return False
        if not any(row[0] == slot for row in rows):
            return False
        icon = max(0, int(first_row)) * COLUMNS + int(slot)
        if icon == self.icon:
            return False
        self.icon = icon
        return True

    def resolve(self, block):
        """The icon the panel shows and the mark is drawn on, or -1.

        HD's own hover wins, because it is the pointer the player is
        actually using. With none — nothing hovered since the screen
        opened — the wire's `scanned_big` still stands: it is the same
        field, read off the game's own cursor, and dropping it would
        throw away the one case where the engine does have an answer.
        """
        if self.icon >= 0:
            return self.icon
        return int(block.get("scanned_big", -1))

    def slot(self, block):
        """The displayed slot carrying the scanned icon, or None.

        None when nothing is scanned and when the scanned ship has
        scrolled out of the five rows — the original draws its box
        only over the icons it is drawing (flt1.cpp:85-91, inside
        `Draw_Fltscrn_Big_Ship_Icons_`).
        """
        icon = self.resolve(block)
        if icon < 0:
            return None
        slot = icon - max(0, int(block.get("first_row", 0) or 0)) * COLUMNS
        return slot if 0 <= slot < fltgeom.GRID_MAX_ICONS else None
