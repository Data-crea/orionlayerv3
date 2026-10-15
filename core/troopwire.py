"""The troop popup's TPOP tail — open fix 98 (work order 274).

The wire half of the colony screen's troop popup: kind 13 of open fix 49's
"TPOP" block, reported as id 71 while `NEWPUP::Troop_Popup` runs (newpup.cpp:
9-36, opened by a click on the colony screen's marines or armour,
colony.cpp:2007-2013). The layout is `doc/ext_troop_popup.patch`'s header,
byte by byte: the colony's side as `Draw_Troop_Popup` computes it
(`invasion::Compute_Colony_Ground_Combat_Info`), the three lines
`Print_Troop_Totals` prints for each troop type, already in the game's words,
and the summary lines `Print_Data` printed (label and value).
"""
import struct as _st


def read_tail(take, text):
    """The tail after TPOP's title and text; `take(fmt)` and `text()` are
    the block reader's."""
    player, rebels, n = take("bBB")
    types = []
    for _ in range(n):
        count, hits, strength = take("hhh")
        types.append({"count": count, "hits": hits, "strength": strength,
                      "name": text(), "hits_line": text(),
                      "strength_line": text()})
    (n_lines,) = take("B")
    lines = []
    for _ in range(n_lines):
        label = text()
        (value,) = take("h")
        lines.append({"label": label, "value": value})
    return {"player": player, "rebels": bool(rebels), "types": types,
            "lines": lines}


def build_tail(troops):
    """The tail as the engine writes it — for the checks' stand-ins."""
    t = troops

    def txt(s):
        raw = (s or "").encode("latin-1")
        return _st.pack("<h", len(raw)) + raw
    out = _st.pack("<bBB", t["player"], int(t["rebels"]), len(t["types"]))
    for u in t["types"]:
        out += _st.pack("<hhh", u["count"], u["hits"], u["strength"])
        out += txt(u["name"]) + txt(u["hits_line"]) + txt(u["strength_line"])
    out += _st.pack("<B", len(t["lines"]))
    for line in t["lines"]:
        out += txt(line["label"]) + _st.pack("<h", line["value"])
    return out


def rows(troops):
    """The popup's table: the summary lines as `Print_Data` sets them, the
    label left and the value right with its sign (E 0x4B, "%s%s %s%+d"),
    then a blank line and one row per troop type: its count and name, and
    its hits and strength — the words `Print_Troop_Totals` prints, read off
    the wire."""
    out = [(line["label"], f"{line['value']:+d}")
           for line in troops.get("lines", [])]
    if out and troops.get("types"):
        out.append("")
    for u in troops.get("types", []):
        out.append((u["name"], f"{u['hits_line']}   {u['strength_line']}"))
    return out

