"""The battle's scan view and board popup — open fix 66, "CPOP" (work order 199).

    "CPOP"  (`doc/ext_combat_popup.patch`): written after CMEV, only while
            the battle's scan view (66) or board popup (67) is up. A version
            byte, then int16: the screen, the battle's serial, the scanned
            unit (`_ship_data_id`, -1 in the popup), the popup's range and
            the marines chosen (`CMBTDRW1::_g_min`, `_g_max`, `_g_var`, 0 in
            the scan view); then the popup's message — a length byte and
            that many bytes (`_g_msg`, the game's KENTEXT message 41; empty
            in the scan view).

WHY: `Detailed_View_Ship_` draws a copy of the unit it was given
(cmbtdrw1.cpp:1549-1551) and `Board_Popup_` keeps its message, range and
choice in CMBTDRW1's globals (cmbtdrw1.cpp:1581-1666); none of it was on
the wire, so HD could neither draw these two nor see an arrow's effect.

Read WHOLE or left None (`core/colonyblocks.py`'s rule).
"""
import struct as _st

from core import lang

HEAD = "<Bhhhhhh"
HEAD_SIZE = _st.calcsize(HEAD)
SCAN, BOARD = 66, 67


def parse(gs, data, pos):
    """Read CPOP at `pos` into `gs.combat_popup` (None when absent or
    short). Returns the new position."""
    gs.combat_popup = None
    if data[pos:pos + 4] != b"CPOP" or pos + 4 + HEAD_SIZE + 1 > len(data):
        return pos
    (version, screen, serial, unit, low, high, chosen) = _st.unpack_from(
        HEAD, data, pos + 4)
    at = pos + 4 + HEAD_SIZE
    n = data[at]
    if version != 1 or screen not in (SCAN, BOARD) or at + 1 + n > len(data):
        return pos
    gs.combat_popup = {"screen": screen, "serial": serial, "unit": unit,
                       "min": low, "max": high, "marines": chosen,
                       "message": lang.wire_text(data[at + 1:at + 1 + n])}
    return at + 1 + n


def build(screen, serial=1, unit=-1, low=0, high=0, chosen=0, message=""):
    """The block as the engine writes it — for the checks' stand-ins."""
    text = message.encode("latin-1")
    return (b"CPOP" + _st.pack(HEAD, 1, screen, serial, unit, low, high,
                               chosen) + bytes([len(text)]) + text)
