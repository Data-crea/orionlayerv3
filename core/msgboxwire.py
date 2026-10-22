"""The message box's block, "MSGB" — open fix 29 (work order 188), and 67.

The wire half of `core/msgbox.py` (work order 324): the kinds, the reader
and the writer of the block. It is split out because `parse_state` reads
this block in every process that parses a snapshot, and `core/msgbox.py`
imports pygame and the HUD to draw it — a parser has no business needing a
display. `core/msgbox.py` re-exports the names callers use.

Layout (`doc/ext_message_box_text.patch`, the item values
`doc/ext_msgbox_items.patch`): "MSGB", uint8 version (1; 2 when the item
values follow, open fix 67), uint8 kind, int16 answer field a, int16
answer field b, int16 ticks; two strings with an int16 length (title,
text); for version 2 a uint8 count and per item a uint8 index and an int32
value. Read WHOLE or left None; a block this reader refuses is not stepped
over (it has no length), as the other optional blocks.
"""
import struct as _st

from core.blockreader import Reader

KINDS = {1: "text", 2: "timed", 3: "message", 4: "warning",
         5: "confirmation"}


def parse(gs, data, pos):
    """Read MSGB at `pos` into `gs.message_box` (None when absent or short).
    Returns the new position."""
    gs.message_box = None
    r = Reader(data, pos)
    if not r.at_tag(b"MSGB") or not r.fits(12):
        return pos
    r.pos += 4
    version, kind, fa, fb, ticks = r.take("BBhhh")
    try:
        texts = [r.text16() for _ in range(2)]
        items = {}
        if version == 2:
            # the values of the text's item codes (open fix 67): a count,
            # then an index byte and an int32 each
            n = r.one("B")
            if not r.fits(n * 5):
                return pos
            for _ in range(n):
                idx, val = r.take("Bi")
                items[idx] = val
    except ValueError:
        return pos
    if version not in (1, 2) or kind not in KINDS:
        return pos
    gs.message_box = {"kind": KINDS[kind], "field_a": fa, "field_b": fb,
                      "ticks": ticks, "title": texts[0] or None,
                      "text": texts[1], "items": items}
    return r.pos


def build(kind, text, title=None, field_a=1, field_b=-1, ticks=0,
          items=None):
    """The block as the engine writes it — for the checks' stand-ins;
    version 2 (open fix 67) when `items` are given."""
    code = {v: k for k, v in KINDS.items()}[kind]
    out = b"MSGB" + _st.pack("<BBhhh", 1 if items is None else 2, code,
                             field_a, field_b, ticks)
    for s in (title or "", text):
        raw = s.encode("latin-1")
        out += _st.pack("<h", len(raw)) + raw
    if items is not None:
        out += bytes([len(items)]) + b"".join(
            _st.pack("<Bi", k, v) for k, v in items.items())
    return out
