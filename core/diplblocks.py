"""The diplomacy audience's block in the snapshot — open fixes 46 and 47
(work order 185; applied by work order 186, orion2re `8aea1a25`, `ba9b6bc6`).

    "DIPL"  open fix 47 (`doc/ext_audience_state.patch`, on top of fix 46,
            `doc/ext_audience_screen.patch`): while the audience reports
            its synthetic id — 57 the player opened it, 58 an AI asked for
            it — which race, the ambassador's mode, the statement id, the
            reply text AS THE ENGINE FORMATTED IT, and the menu taking input
            now: its title and per item the enable flag and the words.

Written between INFS and COLS (block 5b), so it is read there, WHOLE or
left None — `core/colonyblocks.py`'s rule. An engine without the fixes
writes nothing and the key stays None: the audience then keeps the game's
own picture, as it does today. The layout is the patch's, field for field.
"""
import struct as _st

from core import lang

#: The synthetic ids open fix 46 reports.
AUDIENCE_IDS = {57: "player", 58: "ai"}


def parse(gs, data, pos):
    """Read DIPL at `pos` into `gs.audience` (None when absent or short).
    Returns the new position."""
    gs.audience = None
    if data[pos:pos + 4] != b"DIPL":
        return pos
    start, pos = pos, pos + 4

    def take(fmt):
        nonlocal pos
        size = _st.calcsize("<" + fmt)
        if pos + size > len(data):
            raise ValueError("short")
        vals = _st.unpack_from("<" + fmt, data, pos)
        pos += size
        return vals

    def text():
        (n,) = take("B")
        (raw,) = take(f"{n}s")
        return lang.wire_text(raw)

    try:
        version, mode, ambassador, option, response = take("BBBBh")
        if version != 1 or mode not in (1, 2):
            raise ValueError("version")
        out = {"mode": "player" if mode == 1 else "ai",
               "ambassador": ambassador, "option": option,
               "response": response, "text": text()}
        (n,) = take("h")
        if not 0 <= n <= 40:
            raise ValueError("count")
        out["title"] = text() if n else ""
        items = []
        for _ in range(n):
            (flag,) = take("B")
            items.append({"enabled": flag != 0, "text": text()})
        out["items"] = items
    except ValueError:
        return start
    gs.audience = out
    return pos
