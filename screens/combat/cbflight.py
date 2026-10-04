"""Missiles, torpedoes and fighters in flight, and a fighter pass's beams —
work order 212 E (Data's decision 6 of work order 201, built here).

TRANSCRIPTION `flight` (`COMBAT1::Seeking_Missiles_`, combat1.cpp:2158-2249;
`CMBTMIS::Move_Missile_`, cmbtmis.cpp:132-216; `Coord_Movement_`, :218-237):
the original flies every missile and fighter group together, pass by pass —
each moves its own `speed` in px along the longer axis toward its target and
turns to face it (`Get_Facing_`), the screen is drawn, and the hits are
resolved as they arrive — until all have arrived or run out of range. The
loop has no wait (HD STATE `untimed_pace`: HD gives each pass the move's
pace, `cbplay.UNTIMED_S`). Until work order 212 HD showed every missile at
the snapshot's place: they jumped.

HD STATE `flight_batch`: no event says where a missile was in each pass; HD
flies each from where the snapshot before put it to where its own snapshot
ends it — the place its `missile_gone` names, or its new place — once per
snapshot, before the snapshot's first hit. A missile launched in the same
snapshot appears where the state after it puts it.

TRANSCRIPTION `fighter_beams` (`CMBTMIS::Fighter_Combat_SFX_`, cmbtmis.cpp:
875-970, open fix 77's CEV_FIGHTER_BEAM): at each pass the group fires its
owner's best point-defence beam from a quarter of its fighters (1 to 9),
each from its place in the group's stack pattern
(`Get_Multiple_Missile_Coords_`, :775-873, `_missile_group_offset`, :9-26),
2 px up and left (:930-933), at the target point, frame by frame until the
beam's frames run out (`Draw_Fighter_Beam_`, beams.cpp:737-773), then the
damage numbers rise until done (:946-967).
"""
from . import cbbeam
from .cbbeamfx import get_angle

#: `CMBTMIS::_missile_group_offset[16][16]` (cmbtmis.cpp:9-26): per facing,
#: eight (x, y) places of a stack's members.
GROUP_OFFSET = (
    (0, -12, 8, -6, 15, 0, 8, 6, 0, 12, -8, 6, -15, 0, -8, -6),
    (-9, -10, 1, -8, 13, -8, 11, 1, 9, 10, -1, 8, -13, 8, -11, -1),
    (13, -8, 11, 1, 9, 10, -1, 8, -13, 8, -11, -1, -9, -10, 1, -8),
    (-11, -7, -3, -8, 6, -11, 10, -4, 12, 6, 3, 8, -6, 11, -10, 4),
    (0, -12, 8, -6, 15, 0, 8, 6, 0, 12, -8, 6, -15, 0, -8, -6),
    (-12, 7, -9, -3, -6, -11, 3, -8, 12, -7, 9, 3, 6, 11, -3, 8),
    (13, -8, 11, 1, 9, 10, -1, 8, -13, 8, -11, -1, -9, -10, 1, -8),
    (-9, -10, 1, -8, 13, -8, 11, 1, 9, 10, -1, 8, -13, 8, -11, -1),
    (0, -12, 8, -6, 15, 0, 8, 6, 0, 12, -8, 6, -15, 0, -8, -6),
    (-9, -10, 1, -8, 13, -8, 11, 1, 9, 10, -1, 8, -13, 8, -11, -1),
    (13, -8, 11, 1, 9, 10, -1, 8, -13, 8, -11, -1, -9, -10, 1, -8),
    (11, 7, 3, 8, -6, 11, -10, 4, -12, -6, -3, -8, 6, -11, 10, -4),
    (0, -12, 8, -6, 15, 0, 8, 6, 0, 12, -8, 6, -15, 0, -8, -6),
    (-12, 7, -9, -3, -6, -11, 3, -8, 12, -7, 9, 3, 6, 11, -3, 8),
    (13, -8, 11, 1, 9, 10, -1, 8, -13, 8, -11, -1, -9, -10, 1, -8),
    (-9, -10, 1, -8, 13, -8, 11, 1, 9, 10, -1, 8, -13, 8, -11, -1),
)
#: which of the eight places a stack of n uses (`Get_Multiple_Missile_
#: Coords_`'s cases; None: the group's own place, an unset slot is 0, 0)
PLACES = {2: (1, 5), 4: (1, 3, 5, 7), 5: (None, 1, 3, 5, 7),
          6: (1, 2, 3, 5, 6, 7), 7: (None, 1, 2, 3, 5, 6, 7),
          8: (0, 1, 2, 3, 4, 5, 6, 7), 9: (None, 0, 1, 2, 3, 4, 5, 6, 7)}
NUMBERS = 9                     # passes the damage numbers rise


def facing(x1, y1, x2, y2):
    """`CMBTMOV1::Get_Facing_`: 0..15, 0 up, clockwise."""
    return int(round(get_angle(x2 - x1, y1 - y2) / 22.5)) & 15


def stack_coords(quantity, dir_, odd_stardate=False):
    """`Get_Multiple_Missile_Coords_(missile, quantity)`: the offsets of a
    stack's members (px). Two use half of places 1 and 5; three use 1 and 5
    or, on an odd stardate, 3 and 7 — the first left at the group's place."""
    row = GROUP_OFFSET[int(dir_) & 15]
    if quantity == 2:                    # C's division: toward zero
        return [(int(row[2] / 2), int(row[3] / 2)),
                (int(row[10] / 2), int(row[11] / 2))]
    if quantity == 3:
        a, b = (3, 7) if odd_stardate else (1, 5)
        return [(0, 0), (row[a * 2], row[a * 2 + 1]),
                (row[b * 2], row[b * 2 + 1])]
    if quantity not in PLACES:
        return [(0, 0)] * max(1, quantity)
    return [(0, 0) if p is None else (row[p * 2], row[p * 2 + 1])
            for p in PLACES[quantity]]


# ── flight ────────────────────────────────────────────────────────────
def plan(before, after, gone):
    """The flight from `before` (the ordnance the snapshot before left)
    to `after` (this snapshot's), `gone` {missile index: (x, y)} where a
    `missile_gone` of this snapshot ends one. None when nothing moves."""
    ends = {m["index"]: (m["x"], m["y"]) for m in
            (after or {}).get("missiles", [])}
    ends.update(gone)
    moves = []
    for m in (before or {}).get("missiles", []):
        end = ends.get(m["index"])
        if end is None or end == (m["x"], m["y"]):
            continue
        speed = max(1, int(m.get("speed", 0) or 0))
        major = max(abs(end[0] - m["x"]), abs(end[1] - m["y"]))
        moves.append({"index": m["index"], "from": (m["x"], m["y"]),
                      "to": end, "passes": max(1, -(-major // speed)),
                      "facing": facing(m["x"], m["y"], *end)})
    if not moves:
        return None
    return {"moves": moves, "frames": max(mv["passes"] for mv in moves)}


def launch(record, start, end, fast=False):
    """TRANSCRIPTION `launch_flight` (`Missile_Launch_FX_`, cmbtspec.cpp:
    856-948): a missile leaves its ship flying 12 px a pass (36 under FAST),
    with no wait, to where the state after its launch puts it — the Proton
    Torpedo and the Dragon Breath the whole way to their target (:876-879).
    `record` is the missile as the state after it (or its launch event)
    gives it; it is drawn while it flies even before that state is shown."""
    step = 36 if fast else 12
    major = max(abs(end[0] - start[0]), abs(end[1] - start[1]))
    mv = {"index": record["index"], "from": tuple(start), "to": tuple(end),
          "passes": max(1, -(-int(major) // step)),
          "facing": facing(*start, *end), "record": dict(record)}
    return {"moves": [mv], "frames": mv["passes"]}


def at(flight, ordnance, frame):
    """The ordnance with every flying missile where pass `frame` has it —
    a launched one added while it flies."""
    ordnance = ordnance if ordnance is not None else {"missiles": []}
    by = {mv["index"]: mv for mv in flight["moves"]}
    out, seen = [], set()

    def place(m, mv):
        f = min(1.0, frame / mv["passes"])
        return dict(m, x=round(mv["from"][0] + (mv["to"][0] -
                                                 mv["from"][0]) * f),
                    y=round(mv["from"][1] + (mv["to"][1] - mv["from"][1]) * f),
                    facing_dir=mv["facing"])
    for m in ordnance.get("missiles", []):
        mv = by.get(m["index"])
        seen.add(m["index"])
        out.append(place(m, mv) if mv is not None else m)
    for mv in flight["moves"]:
        if mv["index"] not in seen and mv.get("record"):
            out.append(place(mv["record"], mv))
    return dict(ordnance, missiles=out)


# ── a fighter pass's beams (open fix 77) ──────────────────────────────
def beams_plan(ev, odd_stardate=False):
    """The pass's bolts: [(bolt `b` as `cbshot._bolt` draws it)] and the
    passes they take — a quarter of the group's fighters, 1 to 9."""
    q = int(ev.get("quantity", 0) or 0)
    count = max(1, min(9, int(q / 4)))
    gx, gy = int(ev.get("x", 0)), int(ev.get("y", 0))
    dst = (int(ev.get("target_x", 0)), int(ev.get("target_y", 0)))
    f = cbbeam.fx(int(ev.get("beam", 0) or 0), 0)
    if f is None:
        f = dict(cbbeam.fx(3), style=0, length=20, step=40)
    bolts = []
    for ox, oy in stack_coords(count, int(ev.get("facing", 0) or 0),
                               odd_stardate)[:count]:
        src = (gx + ox - 2, gy + oy - 2)
        n, _s = cbbeam.max_frames(src, dst, f)
        bolts.append({"fx": f, "fragment": None, "src": src, "dst": dst,
                      "frames": n, "stop": None, "specials": 0,
                      "total": 10})
    frames = max(b["frames"] for b in bolts) + 1
    return {"bolts": bolts, "frames": frames, "numbers": NUMBERS}


def draw_beams(surface, cam, art, ev, p, frame, cache, palettes):
    from . import cbshot
    for i, b in enumerate(p["bolts"]):
        if frame <= b["frames"]:
            cbshot._bolt(surface, cam, art,
                         {"seq": int(ev.get("seq", 0) * 16) + i,
                          "serial": ev.get("serial"), "result": 0},
                         b, frame, cache, palettes)

