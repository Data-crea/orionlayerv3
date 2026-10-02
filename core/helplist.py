"""The help list a right click is checked against — open fix 69, "HLPL"
(work order 200 B).

    "HLPL"  (`doc/ext_help_list.patch`): written after COPT while a help
            list is active. A version byte, int16 n (at most 64), then n
            entries of five int16 — the help id, x1, y1, x2, y2 — as
            `fields::Check_Help_List_` walks them (fields.cpp:2935-2954): the
            first entry with an id (not -1) under the pointer wins.

WHY: many of the original's help lists are built at run time from the
game's state — the audience's per menu (`Setup_Diplomacy_Help_`,
dip_scrn_main.cpp:1966-1993), the popups that keep their caller's — and
none was on the wire. A message or text box switches help off while it is
up, so the block is absent then (`gs.help_list` None).

Read WHOLE or left None (`core/colonyblocks.py`'s rule).
"""
import struct as _st

ENTRY = "<5h"
ENTRY_SIZE = _st.calcsize(ENTRY)
MAX = 64


def parse(gs, data, pos):
    """Read HLPL at `pos` into `gs.help_list` — [(id, x1, y1, x2, y2)] — or
    None. Returns the new position."""
    gs.help_list = None
    if data[pos:pos + 4] != b"HLPL" or pos + 7 > len(data):
        return pos
    version, n = _st.unpack_from("<Bh", data, pos + 4)
    end = pos + 7 + n * ENTRY_SIZE
    if version != 1 or not 0 < n <= MAX or end > len(data):
        return pos
    gs.help_list = [_st.unpack_from(ENTRY, data, pos + 7 + i * ENTRY_SIZE)
                    for i in range(n)]
    return end


def build(entries):
    """The block as the engine writes it — for the checks' stand-ins."""
    return b"HLPL" + _st.pack("<Bh", 1, len(entries)) + b"".join(
        _st.pack(ENTRY, *e) for e in entries)


def help_at(entries, x, y):
    """`Check_Help_List_`'s answer for a native point: the id, or None."""
    for hid, x1, y1, x2, y2 in entries or ():
        if hid != -1 and x1 <= x <= x2 and y1 <= y <= y2:
            return hid
    return None
