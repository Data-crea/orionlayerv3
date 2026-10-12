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

from core.structs import combat as combat_struct

#: s_ship_move_info, whole: `core/structs/combat.py` (it follows the
#: engine's layout; 14 bytes on the old engine).
SPEC = combat_struct.MOVE_INFO_SPEC
FIELDS = tuple(name for name, _o, _k in SPEC.fields)
SIZE = SPEC.size


def parse(gs, data, pos):
    """Read FMOV at `pos` into `gs.fleet_move` (None when absent or short).
    Returns the new position."""
    gs.fleet_move = None
    if data[pos:pos + 4] != b"FMOV" or pos + 8 > len(data):
        return pos
    version, n, size = _st.unpack_from("<BhB", data, pos + 4)
    body = pos + 8
    if version != 1 or size != SPEC.resolved()[0] or n < 0 or \
            body + n * size > len(data):
        return pos
    verdicts = [combat_struct.record(SPEC, data[body + i * size:
                                                body + (i + 1) * size])
                for i in range(n)]
    gs.fleet_move = {"version": version, "verdicts": verdicts}
    return body + n * size


def build(verdicts):
    """The block as the engine writes it — for the checks' stand-ins."""
    out = b"FMOV" + _st.pack("<BhB", 1, len(verdicts), SIZE)
    for v in verdicts:
        out += SPEC.pack({name: int(v.get(name, 0)) for name in FIELDS})
    return out
