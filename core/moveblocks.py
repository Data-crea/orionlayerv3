"""The move verdict at every star — open fix 48, "FMOV" (work order 188).

    "FMOV"  (`doc/ext_fleet_move_verdict.patch`): written LAST in the
            snapshot, only on SCREEN_MAIN while the fleet box is open and a
            ship in it is selected — the original's own hover gate
            (mainscr_main.cpp:451-453). A version byte, int16 the star
            count, uint8 the struct size (14), then per star the
            `s_ship_move_info` `SHIPMOVE::Ships_Try_To_Move_To_` fills for
            the box's selected ships (shipmove.cpp:776-969; orion2.h:2921-
            2936) — the verdict the original computes on HOVER and colours
            its preview line from (mainscr.cpp:535-568).

Read WHOLE or left None (`core/colonyblocks.py`'s rule): a half-read table
would colour some stars from nothing. An engine without the fix writes
nothing and `gs.fleet_move` stays None — the map then draws no preview line
(a state, not a guess: HD never recomputes range, fuel, speed or gates).
"""
import struct as _st

#: s_ship_move_info, field for field (orion2.h:2921-2936), 14 bytes.
FIELDS = (("blackhole_blocks", "b"), ("insufficient_fuel", "b"),
          ("immobile", "b"), ("pad", "b"), ("turns_left", "B"),
          ("moving", "b"), ("out_of_range", "b"), ("has_navigator", "b"),
          ("traveling_speed", "b"), ("parsecs", "B"), ("uses_wormhole", "b"),
          ("has_jumpgate_route", "b"), ("has_stargate_route", "b"),
          ("hyperspace_flux", "b"))
FORMAT = "<" + "".join(f for _n, f in FIELDS)
SIZE = _st.calcsize(FORMAT)
assert SIZE == 14


def parse(gs, data, pos):
    """Read FMOV at `pos` into `gs.fleet_move` (None when absent or short).
    Returns the new position."""
    gs.fleet_move = None
    if data[pos:pos + 4] != b"FMOV" or pos + 8 > len(data):
        return pos
    version, n, size = _st.unpack_from("<BhB", data, pos + 4)
    body = pos + 8
    if version != 1 or size != SIZE or n < 0 or body + n * size > len(data):
        return pos
    verdicts = []
    for i in range(n):
        vals = _st.unpack_from(FORMAT, data, body + i * size)
        verdicts.append(dict(zip((name for name, _f in FIELDS), vals)))
    gs.fleet_move = {"version": version, "verdicts": verdicts}
    return body + n * size


def build(verdicts):
    """The block as the engine writes it — for the checks' stand-ins."""
    out = b"FMOV" + _st.pack("<BhB", 1, len(verdicts), SIZE)
    for v in verdicts:
        out += _st.pack(FORMAT, *(int(v.get(name, 0)) for name, _f in FIELDS))
    return out
