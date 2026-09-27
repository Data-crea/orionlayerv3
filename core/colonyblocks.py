"""Open fixes 35-40's blocks in the snapshot — work order 180 B and C
(applied on orionlayer-local by work order 181).

Split out of `core/game_state.py` so that file stays under the 300-line
guideline; `parse_state` calls `parse` right after the INFS block.
"""


def parse(gs, data, pos):
    """Open fixes 35-40 (work order 180): six OPTIONAL blocks after INFS's
    place, in the order the engine writes them, each only on its screen —
    COLS and CPRD on 1 and 25, CBLD and CEVT on 1, BLDQ and BLDL on 25.
    Each is read WHOLE or left None, for FLTS's reason: a half-read block
    would draw a colony's screen from half its data without saying so.
    An engine without the fixes writes none of them, and every key stays
    None — the state the screens fall back on (the safety net)."""
    import struct as _st

    def take(fmt):
        nonlocal pos
        size = _st.calcsize("<" + fmt)
        if pos + size > len(data):
            raise ValueError("short")
        vals = _st.unpack_from("<" + fmt, data, pos)
        pos += size
        return vals

    def block(tag, reader):
        nonlocal pos
        if data[pos:pos + 4] != tag:
            return None
        start = pos
        pos += 4
        try:
            return reader()
        except ValueError:
            pos = start
            return None

    gs.colony_screen = block(b"COLS", lambda: dict(zip(
        ("star", "orbit", "colony", "drawing_display", "field_mode",
         "autobuild_enabled"), take("hhhBBB"))))
    def _cbld():
        grid = list(take("36h"))
        return {"grid": [grid[r * 6:r * 6 + 6] for r in range(6)],
                "satellites": list(take("10h"))}
    gs.colony_placement = block(b"CBLD", _cbld)
    def _cevt():
        plague, boom = take("BB")
        return {"plague": None if plague == 0xFF else bool(plague),
                "pop_boom": None if boom == 0xFF else bool(boom)}
    gs.colony_events = block(b"CEVT", _cevt)
    gs.colony_product = block(b"CPRD", lambda: dict(zip(
        ("producing", "cost", "turns"), take("hih"))))
    def _bldq():
        return {"items": list(take("7h")), "active": list(take("4h")),
                "field_mode": take("B")[0], "auto_building": take("h")[0]}
    gs.build_queue = block(b"BLDQ", _bldq)
    def _bldl():
        out = {}
        for key in ("buildings", "others"):
            n = take("h")[0]
            if not 0 <= n <= 54:
                raise ValueError("count")
            out[key] = [dict(zip(("id", "cost", "maintenance", "time"),
                                 take("4h"))) for _ in range(n)]
        # The seven queue items with the same numbers (fix 40 as amended by
        # work order 180 C: a queued item need not be in either list).
        out["queue"] = [dict(zip(("id", "cost", "maintenance", "time"),
                                 take("4h"))) for _ in range(7)]
        return out
    gs.build_lists = block(b"BLDL", _bldl)
    return pos
