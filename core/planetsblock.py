"""The Planets screen's own state on the wire — open fix 97, "PLSM" (work order 271).

    "PLSM"  (`doc/ext_planets_send.patch`): written after SYSW's place,
            only while SCREEN_PLANET_SUMMARY (32) is up. A version byte;
            int16 send_choice (-1 none, 0 colony, 1 outpost); uint8 the
            Send Colony and Send Outpost buttons' states (0 not selectable,
            1 selectable, 2 armed); uint8 can_reach_scanned_planet; int8
            box_field_scanned; int16 last_ship_moved; int16 scanned_field;
            int16 the scroll window's first row and total rows; the fields:
            8 row fields, 8 colony and 8 outpost marker fields, up, down,
            Send Colony, Send Outpost (-1000 absent); int16 n stars and each
            star icon's field; int16 n rows and per row, in the game's order,
            int16 planet, the colony and outpost orders' ETAs (-1 none: the
            markers), the best colony and outpost ship's ETA, the best colony
            ship and the best outpost ship (-1 none), int8 blocked; then the hovered row's try (g_ship_move_info):
            uint8 turns_left and int8 moving, out_of_range, blackhole_blocks,
            insufficient_fuel.

WHY: `Planet_Summary_Screen` (plntsum.cpp:1929-2136) keeps its list, its
scroll window and its send mode where only it can read them; HD could
neither arm a send nor click the row the game shows, nor show an order's
ETA or undo it. Read WHOLE or left None: an engine without the fix writes
none, and the send buttons stay HD's display only, as before.
"""
import struct as _st

from core.blockreader import Reader

NO_FIELD = -1000
ROWS_SHOWN = 8


def parse(gs, data, pos):
    """Read PLSM at `pos` into `gs.planets_screen` (None when absent or
    short). Returns the new position."""
    gs.planets_screen = None
    if data[pos:pos + 4] != b"PLSM":
        return pos
    r = Reader(data, pos + 4)
    take = r.take
    try:
        (version,) = take("B")
        if version != 1:
            return pos
        (choice, colony_btn, outpost_btn, reach, scanned_box, last_moved,
         scanned_field, first, total) = take("hBBBbhhhh")
        rows_f = list(take("8h"))
        colony_f = list(take("8h"))
        outpost_f = list(take("8h"))
        up, down, send_colony, send_outpost = take("4h")
        (n_stars,) = take("h")
        stars = list(take(f"{max(0, n_stars)}h")) if n_stars > 0 else []
        (n_rows,) = take("h")
        rows = []
        for _ in range(max(0, n_rows)):
            (planet, c_eta, o_eta, c_best, o_best, c_ship, o_ship,
             blocked) = take("hhhhhhhb")
            rows.append({"planet": planet, "colony_eta": c_eta,
                         "outpost_eta": o_eta, "colony_best_eta": c_best,
                         "outpost_best_eta": o_best, "colony_ship": c_ship,
                         "outpost_ship": o_ship, "blocked": bool(blocked)})
        turns, moving, out_of_range, bh, fuel = take("Bbbbb")
    except ValueError:
        return pos
    gs.planets_screen = {
        "send_choice": choice, "buttons": {"colony": colony_btn,
                                           "outpost": outpost_btn},
        "can_reach": bool(reach), "box_scanned": scanned_box,
        "last_moved": last_moved, "scanned_field": scanned_field,
        "first": first, "total": total,
        "fields": {"rows": rows_f, "colony": colony_f, "outpost": outpost_f,
                   "up": up, "down": down, "send_colony": send_colony,
                   "send_outpost": send_outpost, "stars": stars},
        "rows": rows,
        "try": {"turns": turns, "moving": bool(moving),
                "out_of_range": bool(out_of_range),
                "blocked": bool(bh), "no_fuel": bool(fuel)}}
    return r.pos


def build(b):
    """The block as the engine writes it — for the checks' stand-ins."""
    f = b["fields"]
    out = b"PLSM" + _st.pack("<BhBBBbhhhh", 1, b["send_choice"],
                             b["buttons"]["colony"], b["buttons"]["outpost"],
                             int(b["can_reach"]), b["box_scanned"],
                             b["last_moved"], b["scanned_field"], b["first"],
                             b["total"])
    out += _st.pack("<8h", *f["rows"]) + _st.pack("<8h", *f["colony"])
    out += _st.pack("<8h", *f["outpost"])
    out += _st.pack("<4h", f["up"], f["down"], f["send_colony"],
                    f["send_outpost"])
    out += _st.pack("<h", len(f["stars"]))
    out += _st.pack(f"<{len(f['stars'])}h", *f["stars"])
    out += _st.pack("<h", len(b["rows"]))
    for r in b["rows"]:
        out += _st.pack("<hhhhhhhb", r["planet"], r["colony_eta"],
                        r["outpost_eta"], r["colony_best_eta"],
                        r["outpost_best_eta"], r["colony_ship"],
                        r["outpost_ship"], int(r["blocked"]))
    t = b["try"]
    out += _st.pack("<Bbbbb", t["turns"], int(t["moving"]),
                    int(t["out_of_range"]), int(t["blocked"]),
                    int(t["no_fuel"]))
    return out


def row_of(block, planet):
    """The game's row index of `planet` in the block, or None."""
    for i, r in enumerate((block or {}).get("rows") or []):
        if r["planet"] == planet:
            return i
    return None
