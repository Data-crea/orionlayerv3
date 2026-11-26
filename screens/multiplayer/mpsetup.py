"""The multi-player setup (id 15) read from its own field list — work order 188.

`MULTPLAY::Multi_Player_Screen` (multplay.cpp) builds its buttons in
`Add_MP_Setup_Screen_Fields` (multplay_fields.cpp, v2; multplay.cpp of 1.60),
each with its own hotkey: the three type radios N, M, H (the keys of
`BUTTONS`: "network", "online", "hotseat"), CANCEL (ESC), START NEW GAME "S",
LOAD GAME "L", JOIN GAME "J" (absent under Hotseat) and, on the OLD engine
only, COMM INFO "C" (only under Online). On the old engine the list says which
type is selected — measured live in work order 188 (`P7_explore`): Network
lists J, Online J and C, Hotseat neither.

WHAT THE RADIOS ARE ON ORION2RE v2 (work order 437 F12, source): N sets
`multi_player_game_type` 2, `Set_Multi_Player_Game_Type` turns that into
`net.mode = 1`, which `netcode_bootstrap.cpp` maps to a direct endpoint
(`BOOTSTRAP_DIRECT_ENDPOINT`: the router named by `interface router` in
`data/orion2re.cfg`) — ONLINE; M sets 1, `net.mode = 0`, the embedded router
and LAN discovery — LAN. So the keys "network" (N) and "online" (M) are the
original's legacy names and `V2_WORDS` names them as v2 behaves.

THE COMM INFO DIALOG IS V1 ONLY (work order 437 F1)
DEVIATION `comm_info_v1_only`: in v2 `Add_MP_Setup_Screen_Fields` sets
`field_id_setup = -1000` ("Router configuration is supplied by the local
interface config", multplay_fields.cpp) and no code opens
`Online_Setup_Screen` (`MP_ONLINE_SETUP` is only a `case` in `ext_api.cpp`),
so `classify` and `comm_fields` below serve the old engine alone and the
setup draws no COMM INFO button under `layout.generation() >= 2`.

The old engine's COMM INFO dialog (`Online_Setup_Screen_`, still under 15) has
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


#: `multi_player_game_type` -> the radio's key (multplay.cpp: N sets 2,
#: M sets 1, H sets 4 — the same in orion2re 1.60 and v2).
GAME_TYPES = {2: "network", 1: "online", 4: "hotseat"}

#: The words for the first two radios on orion2re v2, as the source behaves
#: (work order 437 F12): N is the direct endpoint (`net.mode` 1, ONLINE), M
#: the embedded router with LAN discovery (`net.mode` 0). UNVERIFIED against
#: the artwork itself, which was not read.
V2_WORDS = {"network": "ONLINE", "online": "LAN"}


def selected(fields, settings_raw=None):
    """The chosen type. On orion2re v2 the list may not say it: the source
    has no COMM INFO button in the setup (TRANSCRIPTION `Add_MP_Setup_Screen_
    Fields` in multplay_fields.cpp sets `field_id_setup = -1000`, the router
    configuration comes from the local interface config; `Draw_MP_Setup_Screen`
    draws that slot greyed), so the settings record is read first
    (`multi_player_game_type`, the value the radios write). Work order 245's
    live walk reported a COMM INFO button; the source cannot show one, so
    that report is taken for the old engine (work order 437 F1, closes
    `comm_info_v2`). On the old engine the list says it: J and C → online, J
    alone → network, neither → hotseat (multplay.cpp:608-634 of 1.60).
    """
    from core.structs import layout
    if settings_raw and layout.generation() >= 2:
        from core.structs import settings
        try:
            kind = GAME_TYPES.get(settings.parse(settings_raw)
                                  .multi_player_game_type)
        except ValueError:
            kind = None
        if kind:
            return kind
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
