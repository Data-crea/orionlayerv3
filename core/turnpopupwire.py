"""The turn-time popups' block, "TPOP" — open fix 49 (work order 188).

The wire half of `core/turnpopup.py` (split for decision 6): the kinds, the
ids open fix 49 reports, and the reader and writer of the block. The layout
is `doc/ext_turn_popups.patch`'s header, byte by byte.
"""
import struct as _st

KINDS = {1: "science", 2: "turn_summary", 3: "leader_hire",
         4: "planet_choice", 5: "discovery", 6: "leader_level", 7: "gnn",
         8: "combat_target", 9: "landing"}
#: The ids open fix 49 reports (40, 52 and 33 are the game's own).
IDS = {40: "turn_summary", 52: "science", 59: "leader_hire",
       60: "planet_choice", 61: "discovery", 62: "leader_level", 63: "gnn",
       64: "combat_target", 33: "landing"}
#: The system display's slots (MAX_PLANETS_PER_STAR) and ship buttons.
SLOTS, SHIP_SLOTS = 5, 15


def parse(gs, data, pos):
    """Read TPOP at `pos` into `gs.turn_popup` (None when absent or short).
    Returns the new position. Layout: `doc/ext_turn_popups.patch`."""
    gs.turn_popup = None
    if data[pos:pos + 4] != b"TPOP":
        return pos
    at = pos + 4

    def take(fmt):
        nonlocal at
        size = _st.calcsize("<" + fmt)
        if at + size > len(data):
            raise ValueError("short")
        vals = _st.unpack_from("<" + fmt, data, at)
        at += size
        return vals

    def text():
        (n,) = take("h")
        if n < 0:
            raise ValueError("length")
        (raw,) = take(f"{n}s")
        return raw.decode("latin-1")
    try:
        version, kind, n = take("BBh")
        if version != 1 or kind not in KINDS or not 0 <= n <= 16:
            return pos
        args = list(take(f"{n}h")) if n else []
        popup = {"kind": KINDS[kind], "args": args + [-1] * (16 - n),
                 "title": text() or None, "text": text() or None}
        if KINDS[kind] == "turn_summary":
            (count,) = take("h")
            msgs = []
            for _ in range(max(0, count)):
                line = text()
                jumps, colony, page, first, nfields = take("BhBhB")
                msgs.append({"text": line, "jumps": bool(jumps),
                             "colony": colony, "page": page,
                             "first_field": first, "fields": nfields})
            popup["messages"] = msgs
        if KINDS[kind] in ("planet_choice", "discovery", "combat_target"):
            star, grid = take("hh")
            planets = [take("hh") for _ in range(SLOTS)]
            ships = [take("hh") for _ in range(SHIP_SLOTS)]
            popup["system"] = {"star": star, "grid_field": grid,
                               "planets": [{"field": f, "planet": p}
                                           for f, p in planets],
                               "ships": [{"field": f, "ship": s}
                                         for f, s in ships]}
        if KINDS[kind] == "combat_target":
            colonies = list(take("5h"))
            (nc,) = take("h")
            players = list(take("15h"))
            (np_,) = take("h")
            popup["targets"] = {"colonies": colonies[:max(0, nc)],
                                "players": players[:max(0, np_)]}
    except ValueError:
        return pos
    gs.turn_popup = popup
    return at


def build(kind, args=(), title=None, text=None, messages=None, system=None,
          targets=None):
    """The block as the engine writes it — for the checks' stand-ins."""
    code = {v: k for k, v in KINDS.items()}[kind]
    out = b"TPOP" + _st.pack("<BBh", 1, code, len(args))
    out += _st.pack(f"<{len(args)}h", *args) if args else b""
    for s in (title or "", text or ""):
        raw = s.encode("latin-1")
        out += _st.pack("<h", len(raw)) + raw
    if kind == "turn_summary":
        messages = messages or []
        out += _st.pack("<h", len(messages))
        for m in messages:
            raw = m["text"].encode("latin-1")
            out += _st.pack("<h", len(raw)) + raw
            out += _st.pack("<BhBhB", int(m.get("jumps", 0)),
                            m.get("colony", -1), m.get("page", 1),
                            m.get("first_field", -1), m.get("fields", 0))
    if kind in ("planet_choice", "discovery", "combat_target"):
        system = system or {}
        out += _st.pack("<hh", system.get("star", -1),
                        system.get("grid_field", -1000))
        planets = (system.get("planets") or [])[:SLOTS]
        planets += [{"field": -1000, "planet": -1}] * (SLOTS - len(planets))
        for p in planets:
            out += _st.pack("<hh", p["field"], p["planet"])
        ships = (system.get("ships") or [])[:SHIP_SLOTS]
        ships += [{"field": -1000, "ship": -1}] * (SHIP_SLOTS - len(ships))
        for sh in ships:
            out += _st.pack("<hh", sh["field"], sh["ship"])
    if kind == "combat_target":
        targets = targets or {}
        cols = (targets.get("colonies") or [])[:5]
        pls = (targets.get("players") or [])[:15]
        out += _st.pack("<5h", *(cols + [-1] * (5 - len(cols))))
        out += _st.pack("<h", len(cols))
        out += _st.pack("<15h", *(pls + [-1] * (15 - len(pls))))
        out += _st.pack("<h", len(pls))
    return out


