"""The text fields on the wire — open fix 88, "TXTF" (work order 230 E).

    "TXTF"  (`doc/ext_text_fields.patch`): written after INBX's place while
            the field list holds a continuous input field. A version byte;
            uint8 n (at most 16); per field, in list order, the input field
            as fix 51 writes one — int16 field, uint8 max length, s8 its
            buffer, uint8 editing, s8 the typed text only while editing (the
            game's cursor '_' at its end).

WHY: a name a player types — the race's on Custom Race (raceopt.cpp:1157-
1167), a ship's, a save's — is a continuous input field. It opens only by a
click (fields.cpp:1076-1105, F904), takes keys into `_continuous_string` and
stores them in its buffer on Enter (:1057-1068). The field list carries its
rectangle and type, never its text; with TXTF HD shows the name the game
holds and reads back what Enter stored.

Read WHOLE or left None (`core/colonyblocks.py`'s rule): an engine without
the fix writes none.
"""
import struct as _st

from core import lang


def s8(data, pos):
    """An uint8-length string at `pos`: (text, end). Raises ValueError when
    the data is short."""
    if pos >= len(data):
        raise ValueError("short")
    n = data[pos]
    end = pos + 1 + n
    if end > len(data):
        raise ValueError("short")
    return lang.wire_text(data[pos + 1:end]), end


def input_field(data, pos):
    """Fix 51's input field at `pos`: (dict, end)."""
    if pos + 3 > len(data):
        raise ValueError("short")
    field, limit = _st.unpack_from("<hB", data, pos)
    text, at = s8(data, pos + 3)
    if at >= len(data):
        raise ValueError("short")
    editing = data[at]
    at += 1
    typed = None
    if editing:
        typed, at = s8(data, at)
    return {"field": field, "max": limit, "text": text,
            "editing": bool(editing), "typed": typed}, at


def typed_text(entry):
    """What the field shows: the typed text without the game's cursor while
    it is edited, else its buffer."""
    if entry["editing"] and entry["typed"] is not None:
        t = entry["typed"]
        return t[:-1] if t.endswith("_") else t
    return entry["text"]


def parse(gs, data, pos):
    """Read TXTF at `pos` into `gs.text_fields` ({field: entry}, or None).
    Returns the new position."""
    gs.text_fields = None
    if data[pos:pos + 4] != b"TXTF" or pos + 6 > len(data):
        return pos
    version, n = data[pos + 4], data[pos + 5]
    if version != 1:
        return pos
    at, out = pos + 6, {}
    try:
        for _ in range(n):
            entry, at = input_field(data, at)
            out[entry["field"]] = entry
    except (ValueError, _st.error):
        return pos
    gs.text_fields = out
    return at


def build(entries):
    """The block as the engine writes it — for the checks' stand-ins:
    `entries` [(field, max, text, typed or None)]."""
    def enc(s):
        raw = s.encode("latin-1")
        return bytes([len(raw)]) + raw
    out = b"TXTF" + bytes([1, len(entries)])
    for field, limit, text, typed in entries:
        out += _st.pack("<hB", field, limit) + enc(text)
        out += (bytes([1]) + enc(typed)) if typed is not None else bytes([0])
    return out
