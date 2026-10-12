"""Where the engine's raw records keep their members — decision 97, work order 243.

**THE ONE PLACE OrionLayer LEARNS A BYTE POSITION.** The Extension API sends
the game's records (`s_player`, `s_colony`, … and the battle's units) as raw
bytes. An engine with the LAYOUT message (orion2re v2 and later with
OrionLayer's fork; `docs/extension-api.md` there) sends, once per
connection, every member of those records by name: offset, size, element
size and kind, as its compiler laid them out. `core.game_client` hands that
table to `install`; from then on the specs in this package
(`core/structs/*.py`) and the snapshot's reader (`core/game_state.py`) take
every position from it, by the member's name. A record that grows or a
member that moves in the engine changes nothing here; a member the engine
no longer has reads as None and is named once in the log.

An engine without the message (`orionlayer-local`, orion2re 1.60) gets
`None` from `current()`: the specs' own offsets are that engine's, read off
its headers and live (decision 23), and the suite's recorded fixtures are
that engine's bytes.

Nothing outside `core/structs/` and `core/game_state.py` reads a position;
a screen asks a spec for a member by name.
"""
import logging
import struct

log = logging.getLogger("layout")

#: The LAYOUT message's own format version this reader knows.
VERSION = 1
SIGNED, UNSIGNED, TEXT, RECORD, OTHER = range(5)
_SCALAR = {(1, SIGNED): "i8", (1, UNSIGNED): "u8", (2, SIGNED): "i16",
           (2, UNSIGNED): "u16", (4, SIGNED): "i32", (4, UNSIGNED): "u32"}


class Member:
    """One member of a record, as the engine compiled it."""

    __slots__ = ("name", "offset", "size", "element", "kind", "record")

    def __init__(self, name, offset, size, element, kind, record=""):
        self.name, self.offset, self.size = name, offset, size
        self.element, self.kind, self.record = element, kind, record

    @property
    def count(self):
        """Elements in the member (1 for a scalar; arrays flattened)."""
        return self.size // self.element if self.element else 1

    def scalar(self):
        """The spec kind of ONE element ("i16", …), or None (text, record)."""
        return _SCALAR.get((self.element, self.kind))

    def __repr__(self):
        return (f"Member({self.name}@{self.offset}, {self.size} B, "
                f"{self.count} x {self.element}, kind {self.kind})")


class Record:
    """One record: its size and its members by name."""

    __slots__ = ("name", "size", "members")

    def __init__(self, name, size, members):
        self.name, self.size, self.members = name, size, members

    def member(self, name):
        return self.members.get(name)


class Layout:
    """The records an engine described in its LAYOUT message, and its
    constants (MAX_PLAYERS, MAX_LEADERS, …)."""

    def __init__(self, version, records, constants=None):
        self.version = version
        self.records = records
        self.constants = constants or {}

    def record(self, name):
        return self.records.get(name)

    def size(self, name, default=None):
        rec = self.records.get(name)
        return rec.size if rec else default


def parse(payload):
    """A LAYOUT message's payload -> Layout. Raises ValueError on one that is
    short or of a version this reader does not know."""
    pos = 0

    def take(fmt):
        nonlocal pos
        vals = struct.unpack_from("<" + fmt, payload, pos)
        pos += struct.calcsize("<" + fmt)
        return vals

    def text():
        nonlocal pos
        (n,) = take("B")
        raw = payload[pos:pos + n]
        if len(raw) != n:
            raise ValueError("LAYOUT: a name runs past the message")
        pos += n
        return raw.decode("ascii")

    try:
        version, n_records = take("HH")
        if version != VERSION:
            raise ValueError(f"LAYOUT version {version}, this reader knows "
                             f"{VERSION}")
        records = {}
        for _ in range(n_records):
            name = text()
            size, n_members = take("IH")
            members = {}
            for _ in range(n_members):
                mname = text()
                offset, msize, element, kind = take("IIIB")
                members[mname] = Member(mname, offset, msize, element, kind,
                                        text())
            records[name] = Record(name, size, members)
        constants = {}
        (n_constants,) = take("H")
        for _ in range(n_constants):
            cname = text()
            (constants[cname],) = take("i")
    except struct.error as err:
        raise ValueError(f"LAYOUT: short message ({err})") from None
    return Layout(version, records, constants)


#: Members the engine RENAMED, by the name a spec uses -> the engine's
#: names to try after it (the one place a rename is answered; decision 97:
#: OrionLayer changes when a member it uses is removed or renamed, and only
#: here). orion2re v2.0.0 renamed these.
ALIASES = {
    ("s_missile", "is_anti_missile_rocket"): ("target_is_missile",),
    ("s_missile", "pad"): ("field14_0x18",),
}

_state = {"layout": None, "missing": set()}


def install(layout):
    """The connected engine's layout (None: an engine without the message)."""
    _state["layout"] = layout
    _state["missing"] = set()
    if layout is not None:
        log.info("engine layout: %d records (%s)", len(layout.records),
                 ", ".join(f"{n} {r.size} B"
                           for n, r in list(layout.records.items())[:5]))


def current():
    """The installed Layout, or None (the specs' own offsets hold)."""
    return _state["layout"]


def size(record, default):
    """The record's size on the wire: the engine's when it said, else
    `default` (the size of the engine the specs were read against)."""
    layout = _state["layout"]
    return layout.size(record, default) if layout else default


def constant(name, default):
    """An engine constant (MAX_PLAYERS, …): the engine's when it said."""
    layout = _state["layout"]
    return layout.constants.get(name, default) if layout else default


def member(record, name):
    """The engine's Member for `record.name`, or None when the engine sent
    no layout, does not send `record`, or has no such member (named once)."""
    layout = _state["layout"]
    if layout is None:
        return None
    rec = layout.record(record)
    if rec is None:
        return None
    m = rec.member(name) or _nested(layout, rec, name)
    for alias in ALIASES.get((record, name), ()):
        if m is None:
            m = rec.member(alias)
    if m is None and (record, name) not in _state["missing"]:
        _state["missing"].add((record, name))
        log.warning("engine layout: %s has no member %s — read as None",
                    record, name)
    return m


def _nested(layout, rec, name, depth=2):
    """`name` inside a record-typed member, at its offset in `rec`: the
    ship record starts with its design (`s_ship_data.d`, an
    `s_ship_design`), and the specs name the design's members as the
    ship's own, as the original's code reads them. Only one match counts;
    two would be a guess."""
    hits = []
    for outer in rec.members.values():
        if outer.kind != RECORD or not outer.record or outer.count != 1:
            continue
        inner_rec = layout.record(outer.record)
        if inner_rec is None:
            continue
        inner = inner_rec.member(name) or (
            _nested(layout, inner_rec, name, depth - 1) if depth > 1 else None)
        if inner is not None:
            hits.append(Member(name, outer.offset + inner.offset, inner.size,
                               inner.element, inner.kind, inner.record))
    return hits[0] if len(hits) == 1 else None


def offset(record, name, default):
    """A member's offset in the connected engine, else `default`."""
    m = member(record, name) if has(record) else None
    return m.offset if m is not None else default


def generation():
    """Which engine's behaviour a transcription follows: 2 for an engine
    that sends its LAYOUT (orion2re 2.x with OrionLayer's changes, work
    order 243), 1 for the engine the screens were first written against
    (orion2re 1.60, `orionlayer-local`). The few places where v2 changed
    what the original does ask this, each citing both sources."""
    return 2 if _state["layout"] is not None else 1


def has(record):
    """True when the installed layout describes `record`."""
    layout = _state["layout"]
    return bool(layout and layout.record(record))
