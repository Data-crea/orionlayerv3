"""The galactic council's TPOP tail — open fix 96 (work order 270).

The wire half of `screens/council`: kind 12 of open fix 49's "TPOP" block,
reported as id 70 while `council::Main_Council_Screen` runs (council.cpp:
101-146). The layout is `doc/ext_council.patch`'s header, byte by byte:
the council's globals as `Draw_Main_Council_Screen` reads them, its three
top lines formatted as it formats them, its message, and the list taking
input now (the vote, the ruling).
"""
import struct as _st

from core import lang

#: `council_state` (council.cpp:323-343, 521-565): what the message says.
STATES = {0: "convened", 1: "nominees", 2: "vote", 3: "abstain",
          4: "elected", 5: "no_one", 6: "refused", 99: "done"}


def read_tail(take, text):
    """The tail after TPOP's title and text; `take(fmt)` and `text()` are
    the block reader's."""
    (state, n0, n1, got0, got1, own0, own1, total, voter, cast, vote_for,
     flag, winner, n) = take("BBBhhhhhbhBhBB")
    members = [take("Bh") for _ in range(n)]
    lines = [text() for _ in range(3)]
    message = text()
    (items,) = take("h")
    menu = None
    if items > 0:
        (tlen,) = take("B")
        (title,) = take(f"{tlen}s")
        entries = []
        for _ in range(items):
            enabled, ilen = take("BB")
            (word,) = take(f"{ilen}s")
            entries.append({"enabled": bool(enabled),
                            "text": lang.wire_text(word)})
        menu = {"title": lang.wire_text(title), "items": entries}
    return {"state": STATES.get(state, state), "state_code": state,
            "nominees": [n0, n1], "received": [got0, got1],
            "own_votes": [own0, own1], "total": total,
            "voter": voter, "votes_cast": cast, "vote_for": vote_for,
            "flag": flag, "winner": winner,
            "members": [{"player": p, "votes": v} for p, v in members],
            "lines": lines, "message": message, "menu": menu}


def build_tail(council):
    """The tail as the engine writes it — for the checks' stand-ins."""
    c = council
    codes = {v: k for k, v in STATES.items()}
    out = _st.pack("<BBBhhhhhbhBhBB", codes.get(c["state"], 0),
                   c["nominees"][0], c["nominees"][1], c["received"][0],
                   c["received"][1], c["own_votes"][0], c["own_votes"][1],
                   c["total"], c["voter"], c["votes_cast"], c["vote_for"],
                   c["flag"], c["winner"], len(c["members"]))
    for m in c["members"]:
        out += _st.pack("<Bh", m["player"], m["votes"])
    for s in list(c["lines"]) + [c["message"]]:
        raw = (s or "").encode("latin-1")
        out += _st.pack("<h", len(raw)) + raw
    menu = c.get("menu")
    items = (menu or {}).get("items") or []
    out += _st.pack("<h", len(items))
    if items:
        raw = menu["title"].encode("latin-1")
        out += _st.pack("<B", len(raw)) + raw
        for it in items:
            raw = it["text"].encode("latin-1")
            out += _st.pack("<BB", int(it["enabled"]), len(raw)) + raw
    return out
