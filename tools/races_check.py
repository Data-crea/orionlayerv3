#!/usr/bin/env python3
"""The Races screen's s_player fields against the game's own invariants —
the second source for the offsets work order 175 C added (decision 23).

    python tools/races_check.py                 # every save on this disk
    python tools/races_check.py FILE.GAM ...

Read only. The first source is the compiler (`tools/struct_header_check.py`
asserts every offset against orion2re's headers); this one asks whether
the bytes AT those offsets behave like the fields they are named for, in
every save found:

  treaty      0..6 — six labels (`_treaty_labels`, estrings.cpp:91-97)
              and 6, total war, which the screen clamps to label 5
              (racescrn.cpp:151-155; diplomac.cpp:1978-1979) — and the SAME
              seen from both sides for every pair of living players —
              `Declare_War_`/`Make_Treaty_` write both records
              (dip_scrn_main.cpp:1006-1019)
  relations   -100..100 (the slider remaps (rel + 100) / 8, racescrn.cpp:
              304-312)
  trade / research treaty flags 0..1-ish and their levels >= 0
  spies       bits 0-5 a count, bits 6-7 a mission 0..3 (bill.cpp:41-59)
  ignoring    a bitmask over the eight players

A wrong offset lands on neighbouring bytes, which do not keep all of that
across a dozen saves. Exit 0 when every save agrees, 1 otherwise, 2 when
no save could be read.
"""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.structs import leader as leader_struct  # noqa: E402
from core.structs import player as player_struct  # noqa: E402


def players_of(blob, hero):
    import leader_check as lc
    k = lc.locate(blob, hero)
    if k is None:
        return None
    q = k + leader_struct.COUNT * leader_struct.SIZE + 2
    n = int.from_bytes(blob[q - 2:q], "little", signed=True)
    return n, [player_struct.parse(blob[q + i * player_struct.SIZE:
                                     q + (i + 1) * player_struct.SIZE])
            for i in range(8)]


def check(n_players, players):
    """[problem strings] — empty when the invariants hold. Only the
    `_NUM_PLAYERS` slots the save says are in the game: the others keep
    whatever the new-game setup left in them."""
    bad = []
    alive = [i for i, p in enumerate(players[:n_players])
             if p.name and not p.eliminated]
    for i in alive:
        p = players[i]
        for j in range(n_players):
            t, r = p.treaty[j], p.relations[j]
            if not 0 <= t <= 6:
                bad.append(f"player {i} treaty[{j}] = {t}")
            if not -100 <= r <= 100:
                bad.append(f"player {i} relations[{j}] = {r}")
            if p.trade_treaty[j] < 0 or p.research_treaty[j] < 0:
                bad.append(f"player {i} trade/research treaty[{j}] < 0")
            if (p.spies[j] >> 6) > 3:
                bad.append(f"player {i} spies[{j}] mission")
            if j in alive and j != i and players[j].treaty[i] != t:
                bad.append(f"treaty {i}->{j} = {t} but {j}->{i} = "
                           f"{players[j].treaty[i]}")
    return bad


def main():
    import leader_check as lc
    files = sys.argv[1:] or sorted(
        glob.glob(os.path.join(lc.MOO, "SAVE*.GAM"))
        + glob.glob(os.path.expanduser("~/orionlayer-fixtures/*.GAM")))
    hero = lc.herodata()
    read, failed = 0, 0
    for path in files:
        got = players_of(open(path, "rb").read(), hero)
        if got is None:
            print(f"  --   {os.path.basename(path)}: no leader array found")
            continue
        read += 1
        n_players, players = got
        bad = check(n_players, players)
        pairs = sum(1 for p in players if p.name and not p.eliminated)
        wars = sum(1 for p in players for t in p.treaty if t >= 4)
        if bad:
            failed += 1
            print(f"  BAD  {os.path.basename(path)}: {bad[:3]}")
        else:
            print(f"  ok   {os.path.basename(path)}: {pairs} living players, "
                  f"treaties symmetric, {wars} war/treaty>=4 entries")
    if not read:
        return 2
    print(f"{read - failed} of {read} save(s) agree")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
