"""One reader for the snapshot's optional blocks — work order 324.

`parse_state` reads the blocks after the fixed part one after another from
where the last one ended (`core/game_state.py`); about forty local `take` /
`block` / `text` helpers had grown up in the block modules, each with its
own idea of a short block, of how far a refused one advances and of what a
negative length does. This is the one reader they share.

THE CONTRACT (the smoke test holds it, `090zzzzzs`):

  * every read is WHOLE or raises `BlockError` (a `ValueError`, as the local
    helpers raised): a read never returns part of what it was asked for,
    and never reads past `len(data)`;
  * a failed read leaves `pos` wherever it had got to — the caller that
    wants the block's start back keeps it (`block` does);
  * `take` always gives a tuple, `one` the single value of a one-item
    format; both little-endian, both cached per format;
  * a refused block is said once through `wire_protocol.refused` and
    `refuse` gives back where the block ended — an int the caller may step
    over, and the line then says it was stepped over — or None when it
    cannot be skipped (the blocks carry a tag and, until the engine writes
    a length, often no size: the rest of the snapshot then reads as
    absent, which is why it is said). One rule with `wire_protocol.refused`
    (work order 326 H1).

No pygame, no drawing: the parsers that use this run in a process that has
no display (decision 97's wire layer; `core.game_state` must import clean).
"""
import struct as _st

from core import lang, wire_protocol

_FORMATS = {}


class BlockError(ValueError):
    """A read that does not fit: short, a negative length, a count out of
    its range. A ValueError, because the block parsers catch that."""


def _fmt(fmt):
    """The cached Struct of `fmt`; always little-endian, a leading "<" (the
    modules' own format constants carry one) is the same thing."""
    s = _FORMATS.get(fmt)
    if s is None:
        s = _FORMATS[fmt] = _st.Struct(fmt if fmt.startswith("<")
                                       else "<" + fmt)
    return s


class Reader:
    """A position over `data`; `pos` is the next byte to read."""
    __slots__ = ("data", "pos")

    def __init__(self, data, pos=0):
        self.data, self.pos = data, pos

    def left(self):
        return len(self.data) - self.pos

    def fits(self, n):
        return 0 <= n <= self.left()

    def at_tag(self, tag):
        return self.data[self.pos:self.pos + len(tag)] == tag

    def enter(self, tag):
        """True and past the tag when the block `tag` starts here."""
        if not self.at_tag(tag):
            return False
        self.pos += len(tag)
        return True

    def take(self, fmt):
        s = _fmt(fmt)
        if s.size > self.left():
            raise BlockError("short")
        vals = s.unpack_from(self.data, self.pos)
        self.pos += s.size
        return vals

    def one(self, fmt):
        (val,) = self.take(fmt)
        return val

    def raw(self, n):
        if not self.fits(n):
            raise BlockError("short")
        out = self.data[self.pos:self.pos + n]
        self.pos += n
        return out

    def text8(self):
        """A string with a uint8 length, as the engine formatted it."""
        return lang.wire_text(self.raw(self.one("B")))

    def text16(self):
        """A string with an int16 length; a negative one is refused."""
        n = self.one("h")
        if n < 0:
            raise BlockError("length")
        return lang.wire_text(self.raw(n))

    def block(self, tag, reader):
        """`reader()`'s value when `tag` starts here, else None; a block
        that raises a ValueError (`BlockError` is one; so are the readers'
        own "version" and "count") is given back as None with `pos` at its
        start, so the next block reads from the same place."""
        if not self.at_tag(tag):
            return None
        start = self.pos
        self.pos += len(tag)
        try:
            return reader()
        except ValueError:
            self.pos = start
            return None

    @staticmethod
    def refuse(tag, why, detail="", end=None):
        """Say once that `tag`'s block was refused (`wire_protocol.refused`,
        the one rule). Returns `end`, where the block ended when it is
        known and can be stepped over — then the line says it was stepped
        over — else None, and the line says the rest is not read."""
        wire_protocol.refused(tag, why, detail, skipped=end is not None)
        return end
