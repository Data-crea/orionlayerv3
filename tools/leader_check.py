#!/usr/bin/env python3
"""Decision 23's second source for `s_leader_data`, repeatable.

    python tools/leader_check.py                 # every .GAM it can find
    python tools/leader_check.py SAVE4.GAM ...   # named files
    python tools/leader_check.py --live          # the running game's wire

`core/structs/leader.py` was promoted on the header route plus the
numbers this prints. It exists so the promotion is a thing anybody can
re-run rather than a paragraph to believe (the pattern of
`tools/research_cost_check.py`, one level up: that one holds a table to
its source, this holds a byte layout to data).

WHAT IT MEASURES, per file or snapshot — each one a number a wrong
offset cannot produce by accident:

  names     HERODATA.LBX's 67 names at the spec's 59-byte stride
  static    type and pict_num equal to HERODATA.LBX's own record
  value     the stored skill_value against `Officer_Skill_Value_`
            recomputed from general_skills, special_skills and
            tech_application (core/leaderskills.skill_value)
  ships     every status-1 ship officer's location is a ship whose
            officer_index names it back, and no other ship names one
  stars     every status-1 colony leader's location is a star whose
            officer_index[player_index] names it back, and no other
            slot names one
  levels    xp of every UNOWNED leader on a level step of
            Get_Officer_Base_Level_ (0, 60, 150, 300, 500, 1000)

A save is read by locating the array (HERODATA's names at the stride),
then walking the serializer's own order out of it: the stars directly
before the leaders, `NUM_PLAYERS` and eight players after, then
`NUM_SHIPS` and the ships (savegame.cpp:1366-1380). The live wire needs
none of that — `GameState` carries all three arrays.

Exit codes: 0 every measured agreement holds (a disagreement the
module docstring EXPLAINS is reported and does not fail — see
`KNOWN_STORED_VALUE_LINEAGE`), 1 an unexplained one, 2 nothing to read.
"""
import argparse
import glob
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

from core import lbx  # noqa: E402
from core import leaderskills as ls  # noqa: E402
from core.research import FIELD_COST  # noqa: E402
from core.researchlist import APP_FIELD  # noqa: E402
from core.structs import leader as leader_struct  # noqa: E402
from core.structs import ship as ship_struct  # noqa: E402
from core.structs import star as star_struct  # noqa: E402

MOO = os.path.expanduser("~/Master of Orion 2")
FIXTURES = os.path.expanduser(os.environ.get("ORIONLAYER_FIXTURES",
                                             "~/orionlayer-fixtures"))

#: s_player's packed size (sizes.h 0xF0E) — what the save writes per
#: player between NUM_PLAYERS and NUM_SHIPS.
PLAYER_SIZE = 0xF0E

#: The two save headers (savegame.h:6-7). Only the VERSIONED file writes
#: each array at its own count with the record the wire carries; a
#: LEGACY file writes fixed original-sized arrays through
#: version-dependent readers (savegame.cpp:1419-1459), so this tool does
#: not walk past the leaders in one — it says it did not measure there
#: rather than reading bytes of the wrong shape as a disagreement.
LEGACY_HEADER, VERSIONED_HEADER = 0xE0, 0xE1

#: THE ONE DISAGREEMENT THAT IS UNDERSTOOD, and what it looks like. The
#: game that SAVE1 started (SAVE1 -> SAVE3 -> SAVE4 -> SAVE5 on this
#: disk) stores a skill_value that differs from the recomputation on 32
#: of 67 records, the same 32 in all four files, while every skill field
#: equals HERODATA.LBX's. The value is written once, at game creation
#: (initgame.cpp:486), and never again, so a game created by a different
#: computation keeps its numbers. The shape is what makes it a lineage
#: and not an offset: a wrong offset would disagree differently in every
#: file. Recorded by the record SET, not by file name.
KNOWN_STORED_VALUE_LINEAGE = frozenset(
    (2, 3, 9, 11, 12, 14, 15, 18, 19, 20, 21, 22, 29, 31, 35, 36, 40,
     41, 42, 43, 44, 45, 46, 48, 50, 52, 54, 58, 59, 61, 65, 66))


def herodata(folder=MOO):
    """HERODATA.LBX's 67 raw records, or None."""
    path = None
    if os.path.isdir(folder):
        for name in os.listdir(folder):
            if name.lower() == "herodata.lbx":
                path = os.path.join(folder, name)
    if path is None:
        return None
    blob = lbx.read_entries(path)[0]
    count, size = struct.unpack_from("<HH", blob, 0)
    if (count, size) != (leader_struct.COUNT, leader_struct.SIZE):
        raise SystemExit(f"HERODATA.LBX says {count} records of {size} "
                         f"bytes; the spec says {leader_struct.COUNT} of "
                         f"{leader_struct.SIZE}")
    return [blob[4 + i * size: 4 + (i + 1) * size] for i in range(count)]


def locate(blob, hero):
    """The offset of the 67 records in a save, or None."""
    names = [r[:15].split(b"\0")[0] + b"\0" for r in hero]
    pos = 0
    while True:
        k = blob.find(names[0], pos)
        if k < 0:
            return None
        if all(blob[k + i * 59: k + i * 59 + len(n)] == n
               for i, n in enumerate(names)):
            return k
        pos = k + 1


def arrays_from_save(blob, hero):
    """(leaders, stars, ships) raw records out of a save, or None.

    stars and ships are None — NOT empty — for a LEGACY file: not
    measured is a different answer from nothing there.
    """
    k = locate(blob, hero)
    if k is None:
        return None
    size = leader_struct.SIZE
    leaders = [blob[k + i * size: k + (i + 1) * size]
               for i in range(leader_struct.COUNT)]
    if struct.unpack_from("<I", blob, 0)[0] != VERSIONED_HEADER:
        return leaders, None, None
    stars = None
    for n in range(1, 1025):
        at = k - n * star_struct.SIZE - 2
        if at < 0:
            break
        if struct.unpack_from("<h", blob, at)[0] == n:
            base = k - n * star_struct.SIZE
            stars = [blob[base + i * star_struct.SIZE:
                          base + (i + 1) * star_struct.SIZE]
                     for i in range(n)]
            break
    p = k + leader_struct.COUNT * size + 2 + 8 * PLAYER_SIZE
    n_ships = struct.unpack_from("<h", blob, p)[0]
    p += 2
    ships = [blob[p + i * ship_struct.SIZE: p + (i + 1) * ship_struct.SIZE]
             for i in range(n_ships)]
    return leaders, stars or [], ships


def measure(leaders_raw, stars_raw, ships_raw, hero):
    """{check: (agree, of, detail)} for one set of arrays."""
    recs = leader_struct.parse_all(leaders_raw)
    heroes = leader_struct.parse_all(hero) if hero else None
    out = {}
    if heroes:
        out["static"] = (sum(r.type == h.type and r.pict_num == h.pict_num
                             for r, h in zip(recs, heroes)), len(recs), "")
    app_field = (lambda a: APP_FIELD[a] if 0 <= a < len(APP_FIELD) else None)
    bad = [r.index for r in recs
           if ls.skill_value(r, app_field, lambda f: FIELD_COST[f])
           != r.skill_value]
    out["value"] = (len(recs) - len(bad), len(recs), bad)
    if ships_raw is None:
        out["ships"] = (0, 0, "not measured: legacy save layout")
        out["stars"] = (0, 0, "not measured: legacy save layout")
        steps = {0} | set(ls.LEVEL_STEPS)
        unowned = [r for r in recs if r.player_index == -1]
        out["levels"] = (sum(r.xp in steps for r in unowned), len(unowned),
                         "")
        return out
    ships = ship_struct.parse_all(ships_raw)
    fwd = [(r.index, r.location) for r in recs
           if r.type == leader_struct.TYPE_SHIP
           and r.status == leader_struct.STATUS_ASSIGNED and r.location >= 0]
    agree = sum(0 <= loc < len(ships) and ships[loc].officer_index == i
                for i, loc in fwd)
    back = {s.index for s in ships if s.officer_index >= 0}
    out["ships"] = (agree + (back == {loc for _i, loc in fwd}),
                    len(fwd) + 1, f"{len(fwd)} officers, ships naming one "
                                  f"{sorted(back)}")
    stars = star_struct.parse_all(stars_raw)
    cfwd = [(r.index, r.location, r.player_index) for r in recs
            if r.type == leader_struct.TYPE_COLONY
            and r.status == leader_struct.STATUS_ASSIGNED and r.location >= 0]
    cagree = sum(0 <= loc < len(stars)
                 and stars[loc].officer_index[pl] == i
                 for i, loc, pl in cfwd)
    cback = {(s.index, p) for s in stars
             for p, v in enumerate(s.officer_index) if v >= 0}
    out["stars"] = (cagree + (cback == {(loc, pl) for _i, loc, pl in cfwd}),
                    len(cfwd) + 1, f"{len(cfwd)} colony leaders")
    steps = {0} | set(ls.LEVEL_STEPS)
    unowned = [r for r in recs if r.player_index == -1]
    out["levels"] = (sum(r.xp in steps for r in unowned), len(unowned), "")
    return out


def verdict(out):
    """True when nothing disagrees that is not explained."""
    ok = True
    for name, (agree, of, detail) in out.items():
        if agree == of:
            continue
        if name == "value" and set(detail) == KNOWN_STORED_VALUE_LINEAGE:
            continue
        ok = False
    return ok


def report(label, out):
    print(label)
    for name, (agree, of, detail) in out.items():
        note = ""
        if name == "value" and agree != of:
            note = ("  — the SAVE1 lineage's stored values (explained)"
                    if set(detail) == KNOWN_STORED_VALUE_LINEAGE
                    else f"  — UNEXPLAINED, records {detail[:12]}")
        elif detail and not isinstance(detail, list):
            note = f"  ({detail})"
        print(f"  {name:<7} {agree:3d} of {of:3d}{note}")


def live(host, port, hero):
    from struct_probe import fetch_snapshot  # noqa: E402
    gs, why = fetch_snapshot(host=host, port=port)
    if gs is None:
        print(why)
        return 2
    stars = [s.raw for s in gs.stars]
    out = measure(gs.leaders_raw, stars, gs.ships_raw, hero)
    report(f"LIVE: screen {gs.current_screen}, stardate "
           f"{gs.stardate_str}, {gs.num_ships} ships", out)
    return 0 if verdict(out) else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("files", nargs="*")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--port", type=int, default=17362)
    args = ap.parse_args()
    hero = herodata()
    if hero is None:
        print(f"HERODATA.LBX not found in {MOO} — the names that locate "
              f"the array come from it")
        return 2
    if args.live:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        return live(args.host, args.port, hero)
    files = args.files or (sorted(glob.glob(os.path.join(MOO, "SAVE*.GAM")))
                           + sorted(glob.glob(os.path.join(FIXTURES,
                                                           "*.GAM"))))
    if not files:
        print("no .GAM files to read")
        return 2
    all_ok, read = True, 0
    for path in files:
        with open(path, "rb") as fh:
            blob = fh.read()
        arrays = arrays_from_save(blob, hero)
        if arrays is None:
            print(f"{os.path.basename(path)}: the 67 names are not in it")
            continue
        read += 1
        out = measure(*arrays, hero)
        report(os.path.basename(path), out)
        all_ok &= verdict(out)
    print(f"\n{read} file(s) read — "
          + ("every agreement holds or is explained" if all_ok
             else "AN UNEXPLAINED DISAGREEMENT"))
    return 0 if all_ok and read else (1 if read else 2)


if __name__ == "__main__":
    sys.exit(main())
