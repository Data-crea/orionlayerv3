"""The galaxy map's star system window on the wire — open fix 90, "SYSW" (work order 231 C).

    "SYSW"  (`doc/ext_system_window.patch`): written after TXTF's place,
            only on SCREEN_MAIN while moveable box 0 (the star system
            window) shows. A version byte; int16 the window's star
            (`_moveable_box[0].id`, set by `Do_System_Popup_`,
            mainscr.cpp:1151); uint8 whether the window shows the system
            (`Draw_System_Display_Popup_`'s test, sys.cpp:692: visited or
            omniscient, not a black hole, or the colonies view); then fifteen
            slots, slot = owner, each int16 the ship field (-1000 unused)
            and int16 the stack's head node (-1 unused) — the fleet bar
            (`Build_System_Popup_Ships_`, sys.cpp:2160-2193;
            `Add_System_Display_Popup_Fields_`, :1845-1870).

WHY: the window's star was on the wire nowhere, so HD named a window only by
its own last star click (decision 65's identity, `boxmodel`), and a window the
engine opened itself — F5 / F6, mainscr.cpp:3082-3110 — could not be drawn.
The bar's fields are hidden fields over its pictures whose owner only MOX
knows; the slots are the combat target window's (TPOP kind 8, open fix 49)
in the same shape, so `sysfleets.entries` reads both.

Read WHOLE or left None (`core/colonyblocks.py`'s rule): an engine without the
fix writes none, and the map's window is named by HD's click and has no bar,
as before.
"""
import struct as _st

HEAD = "<BhB"
SLOTS = 15
SIZE = _st.calcsize(HEAD) + SLOTS * _st.calcsize("<hh")
NO_FIELD = -1000


def parse(gs, data, pos):
    """Read SYSW at `pos` into `gs.system_window` (None when absent or
    short). Returns the new position."""
    gs.system_window = None
    if data[pos:pos + 4] != b"SYSW" or pos + 4 + SIZE > len(data):
        return pos
    version, star, viewable = _st.unpack_from(HEAD, data, pos + 4)
    if version != 1:
        return pos
    at = pos + 4 + _st.calcsize(HEAD)
    ships = []
    for _ in range(SLOTS):
        field, node = _st.unpack_from("<hh", data, at)
        ships.append({"field": field, "ship": node})
        at += 4
    gs.system_window = {"star": star, "viewable": bool(viewable),
                        "ships": ships}
    return pos + 4 + SIZE


def ship_fields(gs):
    """The bar's field indices while the block is there, else an empty set."""
    sysw = getattr(gs, "system_window", None) or {}
    return {s["field"] for s in sysw.get("ships", ())
            if s["ship"] > -1 and s["field"] > 0}


def build(star, viewable=True, slots=None):
    """The block as the engine writes it — for the checks' stand-ins.
    `slots`: {owner: (field, node)}."""
    out = b"SYSW" + _st.pack(HEAD, 1, star, int(bool(viewable)))
    for owner in range(SLOTS):
        field, node = (slots or {}).get(owner, (NO_FIELD, -1))
        out += _st.pack("<hh", field, node)
    return out
