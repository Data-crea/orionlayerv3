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
      u8, i8, u16, i16, u32, i32, or "strN" (N-byte zero-terminated
      latin-1 string, e.g. "str15").
    """

    _FMT = {"u8": "<B", "i8": "<b", "u16": "<H", "i16": "<h",
            "u32": "<I", "i32": "<i"}

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
