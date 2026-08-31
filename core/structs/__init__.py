"""Declarative parsers for orion2re binary structs.

game_state.py stores most struct arrays as raw bytes. This package
turns them into named fields via declarative specs — one module per
struct, one source of truth for offsets.

VERIFICATION POLICY (project lesson #1: verify numerically, never
guess): a spec is only marked verified=True after its offsets have
been confirmed against live game data (known star names, known
coordinates, ext_diag output). Unverified specs exist as documented
starting points and are NOT used by production code paths.
Use tools/struct_probe.py to verify offsets against a running game.

Usage:
    from core.structs import star
    s = star.parse(raw_bytes)     # -> StructView with named fields
    s.name, s.x, s.y, s.raw
"""
import re as _re
import struct as _struct


class StructView:
    """Parsed struct: named fields as attributes + .raw bytes."""

    __slots__ = ("raw", "_values")

    def __init__(self, raw, values):
        self.raw = raw
        self._values = values

    def __getattr__(self, name):
        try:
            return self._values[name]
        except KeyError:
            raise AttributeError(name) from None

    def set_derived(self, name, value):
        """Attach a value that is NOT part of the binary struct.

        Used for data the Extension API sends alongside a record
        rather than inside it — currently the ship icon owner, which
        orion2re resolves through _ship_node and appends as a separate
        block. Keeping it out of the Spec is the point: a spec lists
        wire offsets, and inventing one for a synthetic field is how
        an offset table starts to lie.
        """
        self._values[name] = value

    def __repr__(self):
        inner = ", ".join(f"{k}={v!r}" for k, v in self._values.items())
        return f"StructView({inner})"


class Spec:
    """Field layout of one binary struct.

    fields: list of (name, offset, kind) where kind is one of
      u8, i8, u16, i16, u32, i32, "strN" (N-byte zero-terminated
      latin-1 string, e.g. "str15"), or a repeat of a scalar written
      "u32[42]", which parses to a list of that many values.

    The array form exists because s_colony is mostly arrays —
    pop[42], buildings[49], production[ECON_COUNT] — and a spec that
    could only name scalars would have to either skip them or invent
    42 field names. It is spelled inside the kind rather than as a
    fourth tuple element so that every existing three-tuple field
    keeps parsing unchanged.
    """

    _FMT = {"u8": "<B", "i8": "<b", "u16": "<H", "i16": "<h",
            "u32": "<I", "i32": "<i"}
    _WIDTH = {"u8": 1, "i8": 1, "u16": 2, "i16": 2, "u32": 4, "i32": 4}
    _ARRAY_RE = _re.compile(r"^([iu](?:8|16|32))\[(\d+)\]$")

    @classmethod
    def kind_width(cls, kind):
        """Bytes one field of this kind occupies. Raises on nonsense.

        Used by the parser, by tools/struct_probe.py to lay out its
        columns, and by the smoke test to assert a spec covers its
        struct without gaps — one place that knows how wide a kind
        is, so those three cannot disagree.
        """
        if kind.startswith("str"):
            return int(kind[3:])
        m = cls._ARRAY_RE.match(kind)
        if m:
            return cls._WIDTH[m.group(1)] * int(m.group(2))
        return cls._WIDTH[kind]

    def __init__(self, name, size, fields, verified=False, note=""):
        self.name = name
        self.size = size
        self.fields = fields
        self.verified = verified
        self.note = note

    def parse(self, raw):
        """Parse one record. Raises ValueError on size mismatch."""
        if len(raw) < self.size:
            raise ValueError(
                f"{self.name}: got {len(raw)} bytes, need {self.size}")
        values = {}
        for name, offset, kind in self.fields:
            if kind.startswith("str"):
                length = int(kind[3:])
                chunk = raw[offset:offset + length]
                values[name] = (chunk.split(b"\x00")[0]
                                .decode("latin-1", errors="replace"))
                continue
            m = self._ARRAY_RE.match(kind)
            if m:
                scalar, count = m.group(1), int(m.group(2))
                width = self._WIDTH[scalar]
                values[name] = [
                    _struct.unpack_from(self._FMT[scalar], raw,
                                        offset + i * width)[0]
                    for i in range(count)]
            else:
                values[name] = _struct.unpack_from(
                    self._FMT[kind], raw, offset)[0]
        return StructView(raw, values)

    def parse_all(self, raw_list):
        """Parse a list of raw records, attaching .index to each."""
        out = []
        for i, raw in enumerate(raw_list):
            view = self.parse(raw)
            view._values["index"] = i
            out.append(view)
        return out
