"""The galaxy map fleet box's order buttons — open fix 86, "FBTN" (work order 229 C).

    "FBTN"  (`doc/ext_fleet_box_buttons.patch`): written after RFIT's place,
            only on SCREEN_MAIN while the fleet box (moveable box 2) shows a
            stack. A version byte; int16 the stack; int16 the stack's star
            (`HACCESS::Ship_Stack_Star_Id_`); uint8 whether the player's
            combat ships there ignore enemies (`star.ignore_combat_ships`,
            the bit Engage clears; 0xFF without a star); then per button,
            in `BUTTONS` order, uint8 offered and int16 its field (-1000 when
            not added).

WHY: which order buttons the box offers is `FLEETPOP::Set_Added_Button_Stuff_`
(fleetpop.cpp:813-856), each a test of the stack's ships, the star and its
planets; their fields are added under the box's CLOSE in that order
(`Add_Added_Buttons_`, :444-510) and only MOX knows which id is which. The
engine answers a button only while its flag is set and its field is the
input (mainscr.cpp:3411-3500). HD recomputes none of it (P602: the field list
is the second source — every field named here must be in the live list).

Read WHOLE or left None (`core/colonyblocks.py`'s rule): an engine without
the fix writes none and the box offers no order buttons, as before.
"""
import struct as _st

#: The buttons in the block's order, with the help entry the original
#: appends for each (evanhelp.cpp, `Set_Main_Screen_Help_List_`: 305 Attack
#: Antares, 306 Colonize, 307 Engage, 308 Unload Transports, 309 Outpost).
BUTTONS = (("all", None), ("outpost", 309), ("colonize", 306),
           ("engage", 307), ("transport", 308), ("attack", 305))
HEAD = "<BhhB"
SIZE = _st.calcsize(HEAD) + len(BUTTONS) * _st.calcsize("<Bh")
NO_FIELD = -1000


def parse(gs, data, pos):
    """Read FBTN at `pos` into `gs.fleet_buttons` (None when absent or short).
    Returns the new position."""
    gs.fleet_buttons = None
    if data[pos:pos + 4] != b"FBTN" or pos + 4 + SIZE > len(data):
        return pos
    version, stack, star, ignore = _st.unpack_from(HEAD, data, pos + 4)
    if version != 1:
        return pos
    at = pos + 4 + _st.calcsize(HEAD)
    out = {"stack": stack, "star": star,
           "ignores_enemies": None if ignore == 0xFF else bool(ignore)}
    for name, _help in BUTTONS:
        offered, field = _st.unpack_from("<Bh", data, at)
        out[name] = {"offered": bool(offered), "field": field}
        at += 3
    gs.fleet_buttons = out
    return pos + 4 + SIZE


def build(stack, star=-1, ignore=0xFF, **buttons):
    """The block as the engine writes it — for the checks' stand-ins.
    `buttons`: name=(offered, field)."""
    out = b"FBTN" + _st.pack(HEAD, 1, stack, star, ignore)
    for name, _help in BUTTONS:
        offered, field = buttons.get(name, (False, NO_FIELD))
        out += _st.pack("<Bh", int(bool(offered)), field)
    return out
