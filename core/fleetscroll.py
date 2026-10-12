"""The galaxy map fleet box's scroll row — open fix 59, "FBSC" (work order 194).

    "FBSC"  (`doc/ext_fleet_box_scroll.patch`): written after the combat
            blocks, only on SCREEN_MAIN while the fleet box (moveable box 2)
            shows a stack. A version byte, then int16: the stack, the bar's
            `first_visible_row`, `visible_rows`, `total_rows`, and the field
            ids of its up and down buttons (`_fltpop_scroll_bar`,
            orion2.h:2400-2416).

WHY: FLEETPOP builds the box's cells from `first_visible_row * 3`
(fleetpop.cpp:643-644) and resets it when a stack opens
(`Initialize_Scroll_Bar_`); SerializeState sent only `MOX::_scroll_bar`, a
different bar, so HD drew a stack past nine ships from its first nine cells
(work order 191's item 1). WIRE ONLY: the fleet box does not read it yet.

Read WHOLE or left None (`core/colonyblocks.py`'s rule).
"""
import struct as _st

FORMAT = "<Bhhhhhh"
SIZE = _st.calcsize(FORMAT)


def parse(gs, data, pos):
    """Read FBSC at `pos` into `gs.fleet_box_scroll` (None when absent or
    short). Returns the new position."""
    gs.fleet_box_scroll = None
    if data[pos:pos + 4] != b"FBSC" or pos + 4 + SIZE > len(data):
        return pos
    (version, stack, first, visible, total, up, down) = _st.unpack_from(
        FORMAT, data, pos + 4)
    if version != 1:
        return pos
    gs.fleet_box_scroll = {"stack": stack, "first_visible_row": first,
                           "visible_rows": visible, "total_rows": total,
                           "up_field": up, "down_field": down}
    return pos + 4 + SIZE


def build(stack, first, visible=3, total=1, up=-1000, down=-1000):
    """The block as the engine writes it — for the checks' stand-ins."""
    return b"FBSC" + _st.pack(FORMAT, 1, stack, first, visible, total, up,
                              down)
