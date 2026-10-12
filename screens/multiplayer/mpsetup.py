"""The multi-player setup (id 15) read from its own field list — work order 188.

`MULTPLAY::Multi_Player_Screen_` (multplay.cpp:244-389) builds its buttons
in `Add_MP_Setup_Screen_Fields_` (:520-637), each with its own hotkey: the
three type radios NETWORK "N", MODEM "M" (orion2re's ONLINE), HOTSEAT "H";
CANCEL (ESC), START NEW GAME "S", LOAD GAME "L", JOIN GAME "J" (absent under
Hotseat, :608-619) and COMM INFO "C" (only under Online, :622-634). So the
list itself says which type is selected — measured live in work order 188
(`P7_explore`): Network lists J, Online J and C, Hotseat neither — and the
setup needs nothing more from the wire.

The COMM INFO dialog (`Online_Setup_Screen_`, :677-725, still under 15) has
three fields: the endpoint's continuous input and two ESC buttons, CANCEL
(left) and ACCEPT (right).
"""
#: Every setup button: (key, hotkey). The words are the view's.
BUTTONS = (("network", ord("N")), ("online", ord("M")),
           ("hotseat", ord("H")), ("start", ord("S")), ("load", ord("L")),
           ("join", ord("J")), ("comm", ord("C")), ("cancel", 0x1B))

SETUP, COMM, NONE = "setup", "comm", None


def live(fields):
    return [f for f in (fields or []) if getattr(f, "index", 0) > 0]


def by_hotkey(fields):
    out = {}
    for f in live(fields):
        out.setdefault(f.hotkey, f)
    return out


def classify(fields):
    """SETUP (the setup's own list), COMM (the COMM INFO dialog), or None."""
    fl = live(fields)
    hk = by_hotkey(fl)
    if all(k in hk for k in (ord("N"), ord("M"), ord("H"), 0x1B, ord("S"),
                             ord("L"))):
        return SETUP
    if len(fl) == 3 and sum(1 for f in fl if f.hotkey == 0x1B) == 2:
        return COMM
    return NONE


def selected(fields):
    """The type the list says is selected: J and C → online, J alone →
    network, neither → hotseat (multplay.cpp:608-634)."""
    hk = by_hotkey(fields)
    if ord("J") in hk and ord("C") in hk:
        return "online"
    if ord("J") in hk:
        return "network"
    return "hotseat"


def buttons(fields):
    """`{key: field}` for the setup's buttons the list has."""
    hk = by_hotkey(fields)
    return {k: hk[h] for k, h in BUTTONS if h in hk}


def comm_fields(fields):
    """`(input, cancel, accept)` of the COMM INFO dialog, or Nones."""
    fl = live(fields)
    esc = sorted((f for f in fl if f.hotkey == 0x1B), key=lambda f: f.x)
    inp = next((f for f in fl if f.hotkey != 0x1B), None)
    if len(esc) != 2:
        return inp, None, None
    return inp, esc[0], esc[1]
