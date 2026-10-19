"""The galaxy map's merge-relocation mode on the wire — open fix 102, "MREL" (work order 310).

    "MREL"  (`doc/ext_merge_relocation_mode.patch`): written after PLSM's
            place, only on SCREEN_MAIN. A version byte, then uint8
            `MAINSCR::merging_relocations` (0 or 1).

WHY: F4 turns the mode on, never off: its case would toggle the flag
(`Check_Function_Keys_`, mainscr.cpp:3112-3129), but F4 is a negative input,
which clears the flag first (mainscr_main.cpp:396-399, :599), so the case
always sets it again (`core/keyfwd.py` F4). It swaps the pointer over the
map to the relocation cursor (mainscr.cpp:3120; `_mouse_list_relocation`); the next
star click then sets every relocation to
that star and says so in HESTR 0xDD's box (mainscr_main.cpp:455-462), a
right click on the map ends the mode (:397-400). The flag was on the wire
nowhere: FLTS carries `FLT1::_merging_relocations`, the Fleets screen's own
variable of the same name (flt1.cpp:605-656), and only while that screen is
up. So HD could not show the mode, and the next star click re-routed every
relocation without a sign (309's finding 5).

Read WHOLE or left None (`core/colonyblocks.py`'s rule): an engine without
the fix writes none, and HD shows no mode, as before.
"""
import struct as _st

HEAD = "<BB"
SIZE = _st.calcsize(HEAD)


def parse(gs, data, pos):
    """Read MREL at `pos` into `gs.merging_relocations` (None when absent
    or short, else a bool). Returns the new position."""
    gs.merging_relocations = None
    if data[pos:pos + 4] != b"MREL" or pos + 4 + SIZE > len(data):
        return pos
    version, flag = _st.unpack_from(HEAD, data, pos + 4)
    if version != 1:
        return pos
    gs.merging_relocations = bool(flag)
    return pos + 4 + SIZE


def build(merging):
    """The block as the engine writes it — for the checks' stand-ins."""
    return b"MREL" + _st.pack(HEAD, 1, 1 if merging else 0)
