"""The Hall of Fame in the snapshot — open fix 50, "HOFM" (work order 188).

    "HOFM"  (`doc/ext_hall_of_fame.patch`): written LAST, only while
            `SCORE::Hall_Of_Fame_Screen_` takes input (it reports 14 on both
            ways in, the main menu's and the end of a game's). A version
            byte, int16 the file's version (0x82), int16 the entry the screen
            flashes (-1 none; a record index), uint8 the count (10), then per
            row in the DISPLAY order (score descending, Init's sort): int16
            record, int16 score, int16 race id, uint8 difficulty, and three
            length-prefixed strings — the player's name, the race's name, and
            the difficulty's word as the engine loaded it (ESTRINGS 545, 280,
            190, 318, 328; score.cpp:298-302).

Read WHOLE or left None (`core/colonyblocks.py`'s rule).
"""
import struct as _st

from core import lang


def parse(gs, data, pos):
    """Read HOFM at `pos` into `gs.hall_of_fame` (None when absent or
    short). Returns the new position."""
    gs.hall_of_fame = None
    if data[pos:pos + 4] != b"HOFM":
        return pos
    at = pos + 4
    try:
        version, file_version, flash, count = _st.unpack_from("<BhhB", data,
                                                              at)
        at += 6
        if version != 1 or not 0 <= count <= 10:
            return pos
        rows = []
        for _ in range(count):
            record, score, race_id, difficulty = _st.unpack_from("<hhhB",
                                                                 data, at)
            at += 7
            texts = []
            for _k in range(3):
                n = data[at]
                at += 1
                if at + n > len(data):
                    return pos
                texts.append(lang.wire_text(data[at:at + n]))
                at += n
            rows.append({"record": record, "score": score,
                         "race_id": race_id, "difficulty": difficulty,
                         "name": texts[0], "race": texts[1],
                         "difficulty_word": texts[2]})
    except (IndexError, _st.error):
        return pos
    gs.hall_of_fame = {"file_version": file_version, "flash": flash,
                       "rows": rows}
    return at


def build(rows, flash=-1, file_version=0x82):
    """The block as the engine writes it — for the checks' stand-ins."""
    out = b"HOFM" + _st.pack("<BhhB", 1, file_version, flash, len(rows))
    for r in rows:
        out += _st.pack("<hhhB", r["record"], r["score"], r.get("race_id", 0),
                        r["difficulty"])
        for k in ("name", "race", "difficulty_word"):
            raw = r[k].encode("latin-1")
            out += bytes([len(raw)]) + raw
    return out
