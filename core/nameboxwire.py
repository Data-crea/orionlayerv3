"""The name box's block, "INBX" — open fix 87 (work order 230 D).

The wire half of `core/namebox.py` (work order 324): the reader and the
writer of the block, and the text the box shows. Split out because
`parse_state` reads the block in every process that parses a snapshot, and
`core/namebox.py` imports pygame to draw the box. Layout: that module's
docstring and `doc/ext_name_box.patch`. `core/namebox.py` re-exports the
names callers use.
"""
import struct as _st

from core import textfields


def parse(gs, data, pos):
    """Read INBX at `pos` into `gs.name_box` (None when absent or short).
    Returns the new position."""
    gs.name_box = None
    if data[pos:pos + 4] != b"INBX":
        return pos
    try:
        version, x, y = _st.unpack_from("<Bhh", data, pos + 4)
        if version != 1:
            return pos
        entry, at = textfields.input_field(data, pos + 4 + 5)
        (button,) = _st.unpack_from("<h", data, at)
        prompt, at = textfields.s8(data, at + 2)
        if at >= len(data):
            return pos
        animated = data[at]
        at += 1
    except (ValueError, IndexError, _st.error):
        return pos
    gs.name_box = {"x": x, "y": y, "field": entry["field"],
                   "max": entry["max"], "text": entry["text"],
                   "editing": entry["editing"], "typed": entry["typed"],
                   "button": button, "prompt": prompt,
                   "animated": bool(animated)}
    return at


def build(x, y, field, limit, text, typed, button, prompt, animated=0):
    """The block as the engine writes it — for the checks' stand-ins."""
    def s8(s):
        raw = s.encode("latin-1")
        return bytes([len(raw)]) + raw
    out = b"INBX" + _st.pack("<BhhhB", 1, x, y, field, limit) + s8(text)
    out += bytes([1]) + s8(typed) if typed is not None else bytes([0])
    return out + _st.pack("<h", button) + s8(prompt) + bytes([animated])


def shown(box):
    """The name the box shows: what is typed, else what it opened with.
    The typed text carries the game's own cursor, a trailing '_' (fix 51's
    note: the commit strips it; '_' cannot be typed, fields.cpp:1210-1238)."""
    return textfields.typed_text(box)
