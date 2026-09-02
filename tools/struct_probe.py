#!/usr/bin/env python3
"""struct_probe — verify struct offsets against a running game.

Connects to orion2re (localhost:17362), grabs one STATE_SNAPSHOT,
and prints annotated hexdumps of the raw record arrays so offsets
can be verified NUMERICALLY against known in-game facts (project
lesson #1) before a spec in core/structs/ is marked verified=True.

For each requested array it prints, per record:
  - hex bytes in rows of 16 with offsets
  - every plausible int16 interpretation (little-endian) per offset
  - printable ASCII runs (candidate strings)

Usage (from the project root, game running, ideally with a loaded
savegame so the arrays are populated):

    python tools/struct_probe.py nebulas
    python tools/struct_probe.py planets --records 10
    python tools/struct_probe.py colonies --records 2
    python tools/struct_probe.py leaders --records 3

    python tools/struct_probe.py colonies --spec --records 2
    python tools/struct_probe.py colonies --spec --full --records 1
    python tools/struct_probe.py colonies --pop-nibble

--pop-nibble runs one named prediction against every colony at once
instead of dumping records for a human to compare; see
`pop_nibble_report` for what it tests and why that particular
prediction is answerable by a save with no androids in it.

--spec decodes a record against the spec registered for that array
and prints field name, offset, kind and value. It works for a record
of any size, so the 64-byte ceiling on the int16 column view stops
mattering for large structs like s_colony (361 B) — that view is
untouched and still the right tool when there is no spec yet.

Workflow:
  1. Note a ground truth in-game (e.g. a nebula's map position via
     the star coordinates around it, a colony's population).
  2. Run the probe, find the offset whose int16 column matches.
  3. Confirm with a SECOND record / a changed value after one turn.
  4. Enter the field in core/structs/<name>.py with verified=True
     and note the evidence in the module docstring.
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

import struct

from core.game_client import GameClient  # noqa: E402

ARRAYS = {
    "nebulas": ("nebulas_raw", 5),
    "planets": ("planets_raw", 18),
    "colonies": ("colonies_raw", 361),
    "leaders": ("leaders_raw", 59),
    "ships": ("ships_raw", 129),
    "settings": ("settings_raw", None),   # single record
    "players": ("player_raw", 3854),
}


def hexdump(raw, indent="    "):
    for row in range(0, len(raw), 16):
        chunk = raw[row:row + 16]
        hexpart = " ".join(f"{b:02x}" for b in chunk)
        asciipart = "".join(
            chr(b) if 32 <= b < 127 else "." for b in chunk)
        print(f"{indent}{row:4d}  {hexpart:<47}  {asciipart}")


def int16_columns(raw, indent="    "):
    print(f"{indent}int16 (LE) per offset:")
    for off in range(0, len(raw) - 1):
        val = struct.unpack_from("<h", raw, off)[0]
        if val != 0:
            print(f"{indent}  @{off:4d}: {val}")


def ascii_runs(raw, indent="    ", min_len=3):
    run = []
    start = 0
    for i, b in enumerate(raw + b"\x00"):
        if 32 <= b < 127:
            if not run:
                start = i
            run.append(chr(b))
        else:
            if len(run) >= min_len:
                print(f"{indent}string @{start}: {''.join(run)!r}")
            run = []


#: Specs the --spec mode can decode against, by array name. A spec
#: named here is NOT thereby trusted: unverified ones are exactly
#: what this mode exists to check, and it prints their status in the
#: header so a reader cannot mistake a decode for a verification.
SPECS = {
    "colonies": ("core.structs.colony", "SPEC"),
    "leaders": ("core.structs.unverified", "LEADER"),
    "planets": ("core.structs.planet", "SPEC"),
    "nebulas": ("core.structs.nebula", "SPEC"),
    "players": ("core.structs.player", "SPEC"),
}


def load_spec(array):
    """The Spec registered for an array name, or None."""
    entry = SPECS.get(array)
    if entry is None:
        return None
    import importlib
    module, attr = entry
    return getattr(importlib.import_module(module), attr, None)


def spec_decode(raw, spec, indent="    "):
    """Field name / offset / kind / value, one line per field.

    Generic over Spec on purpose. s_leader_data needs exactly this
    and so will anything else promoted out of unverified.py, and a
    decoder wired to one struct is a decoder that gets copied.

    An array field prints its length and its first values rather than
    all of them — pop[42] and buildings[49] would bury the scalars
    that are usually what somebody is checking. `--full` prints
    everything.
    """
    view = spec.parse(raw)
    width = max(len(n) for n, _, _ in spec.fields)
    for name, offset, kind in spec.fields:
        value = getattr(view, name)
        if isinstance(value, list):
            shown = ", ".join(str(v) for v in value[:SPEC_ARRAY_PREVIEW])
            more = "" if len(value) <= SPEC_ARRAY_PREVIEW else ", ..."
            value = f"[{len(value)}] {shown}{more}"
        print(f"{indent}{offset:4d}  {name:<{width}}  "
              f"{kind:<10}  {value}")


def spec_decode_full(raw, spec, indent="    "):
    """Every element of every array field, one per line."""
    view = spec.parse(raw)
    for name, offset, kind in spec.fields:
        value = getattr(view, name)
        if not isinstance(value, list):
            continue
        print(f"{indent}{name} ({kind}) at {offset}:")
        for i, v in enumerate(value):
            print(f"{indent}  [{i:3d}] {v}")


#: How many elements of an array field the compact view shows.
SPEC_ARRAY_PREVIEW = 8


# ── The pop[] nibble ──────────────────────────────────────────────

def pop_nibble_report(records, colony_spec):
    """Counts for the low nibble of every pop[] word, live.

    `pop.h:8` calls this nibble MASK_RACE and the name is wrong.
    `COLONY::Get_Effective_Pop_Player_` (colony.cpp:1257) returns it
    as a PLAYER index, mapping only 8 and 9 to the colony's owner,
    and the race is a second lookup — `MOX::_player[idx].race` in
    `Colony_Pop_Anim_` (colony.cpp:1275).

    THE PREDICTION, which the reference save can answer despite
    holding no androids, no natives and no conquered pops:

        for every colony, for every pop i < n_pops:
            (pop[i] & 0x0F) == colony.owner
        and no value outside 0..9 anywhere.

    It is falsifiable there because the snapshot carries the AI's
    colonies too, and those have owners other than 0. Under the
    "race" reading the nibble would be a race index and would NOT
    track the owner across 21 colonies of several different owners —
    unless every AI happens to play the race whose index equals its
    own player number, which is what `distinct_owners` below is for.
    A save where every colony has the same owner cannot decide this
    at all, and the report says so rather than passing.

    Returns counts, never a verdict alone. **A scattered distribution
    is the tell.** If the mask is wrong — off by a bit, or the field
    is somewhere else entirely — the nibble is effectively arbitrary
    low bits of some other quantity, and what that looks like is a
    spread across many values, not a clean failure. A pass/fail line
    would throw away the one signal that distinguishes "wrong mask"
    from "right mask, unexpected data".
    """
    from collections import Counter
    from core.structs import colony as colony_struct

    dist = Counter()          # nibble -> count, live pops only
    tail = Counter()          # nibble -> count, slots past n_pops
    per_owner = {}            # owner -> Counter of nibbles
    mismatches = []           # (colony, pop, owner, nibble), 0..7 wrong
    sentinels = []            # (colony, pop, owner, nibble), 8 or 9
    out_of_range = []         # (colony, pop, nibble), 10..13
    direct_race = []          # (colony, pop, nibble), >= 14
    live = 0

    for ci, raw in enumerate(records):
        col = colony_spec.parse(raw)
        owner = col.owner
        n = min(col.n_pops, len(col.pop))
        for pi, word in enumerate(col.pop):
            nib = word & colony_struct.POP_MASK_PLAYER_INDEX
            if pi >= n:
                tail[nib] += 1
                continue
            live += 1
            dist[nib] += 1
            per_owner.setdefault(owner, Counter())[nib] += 1
            # 8 and 9 are NOT prediction failures. They are the
            # sentinel branch (colony.cpp:1261) and they resolve to
            # this very owner, so they CONFIRM the player-index
            # reading rather than contradicting it — counting them as
            # mismatches would make the one save that can settle the
            # sentinels report itself as a refutation.
            if nib in (colony_struct.POP_ANDROID, colony_struct.POP_NATIVE):
                sentinels.append((ci, pi, owner, nib))
            elif nib <= colony_struct.POP_PLAYER_INDEX_MAX:
                if nib != owner:
                    mismatches.append((ci, pi, owner, nib))
            # Two different things live above 9 and must not be
            # reported as one. 14 and 15 have a branch in the source
            # (colony.cpp:2129); 10 to 13 have none that was found, so
            # they are genuinely unaccounted for and a stronger signal.
            elif nib >= colony_struct.POP_DIRECT_RACE_MIN:
                direct_race.append((ci, pi, nib))
            else:
                out_of_range.append((ci, pi, nib))

    return {
        "colonies": len(records), "live_pops": live,
        "dist": dist, "tail": tail, "per_owner": per_owner,
        "mismatches": mismatches, "out_of_range": out_of_range,
        "direct_race": direct_race, "sentinels": sentinels,
        "distinct_owners": sorted(per_owner),
    }


def _n(count, noun):
    """'1 pop' / '3 pops'. The output is read by a person."""
    return f"{count} {noun}{'' if count == 1 else 's'}"


def print_pop_nibble_report(rep, indent="  "):
    """The counts first, the verdict last, the caveats after that."""
    from core.structs import colony as cs

    print(f"{indent}{rep['colonies']} colonies, {rep['live_pops']} live "
          f"pops (slots past n_pops counted separately)")
    print(f"\n{indent}nibble distribution over live pops:")
    for value, count in sorted(rep["dist"].items()):
        note = {cs.POP_ANDROID: "  (android sentinel)",
                cs.POP_NATIVE: "  (native sentinel)"}.get(value, "")
        if value >= cs.POP_DIRECT_RACE_MIN:
            note = "  (>= 14: matched as a race directly, colony.cpp:2129)"
        print(f"{indent}  {value:2d}: {count:5d}{note}")
    if rep["tail"]:
        # "0x146" for value 0 count 146 read as a hex number; the
        # separator has to survive being glanced at.
        print(f"{indent}unused slots past n_pops: "
              + ", ".join(f"{v} ({c})" for v, c in sorted(rep["tail"].items())))

    print(f"\n{indent}nibble by colony owner — the load-bearing table:")
    for owner in rep["distinct_owners"]:
        counts = rep["per_owner"][owner]
        shown = ", ".join(f"{v}:{c}" for v, c in sorted(counts.items()))
        # Only a player index that is not this owner is wrong. 8 and 9
        # belong here and flagging them made a save WITH androids —
        # the one that can settle the sentinels — look like the
        # refutation.
        stray = [v for v in counts
                 if v <= cs.POP_PLAYER_INDEX_MAX and v != owner]
        flag = f"   <-- {stray} is not this owner" if stray else ""
        print(f"{indent}  owner {owner}: {shown}{flag}")

    print()
    if len(rep["distinct_owners"]) < 2:
        print(f"{indent}INCONCLUSIVE: every colony has the same owner "
              f"({rep['distinct_owners']}), so 'nibble == owner' and "
              f"'nibble == 0' are the same\n{indent}statement here. "
              f"Load a save with AI colonies in the snapshot.")
    elif rep["mismatches"]:
        print(f"{indent}PREDICTION FAILED: {len(rep['mismatches'])} of "
              f"{rep['live_pops']} pops carry a player index in 0..7 "
              f"that is not their\n{indent}colony's owner.")
        for ci, pi, owner, nib in rep["mismatches"][:12]:
            print(f"{indent}  colony {ci} pop {pi}: owner {owner}, "
                  f"nibble {nib}")
        if len(rep["mismatches"]) > 12:
            print(f"{indent}  ... {len(rep['mismatches']) - 12} more")
        print(f"{indent}Read the distribution above before concluding the "
              f"mask is wrong: a few values\n{indent}clustered near the "
              f"owners is a different fault from a spread across many.")
    else:
        print(f"{indent}PREDICTION HELD across "
              f"{len(rep['distinct_owners'])} distinct owners "
              f"{rep['distinct_owners']}: every live pop in 0..7 carries "
              f"its\n{indent}own colony's owner.")
    if rep["sentinels"]:
        print(f"{indent}Nibble 8 or 9: {_n(len(rep['sentinels']), 'pop')}"
              f". NOT a failure — the android and native sentinels,\n"
              f"{indent}which colony.cpp:1261 resolves to the colony's "
              f"owner. This save can therefore\n{indent}say something "
              f"about the sentinel branch; the reference one cannot.")

    if rep["direct_race"]:
        print(f"{indent}Nibble >= 14: "
              f"{_n(len(rep['direct_race']), 'pop')}. Outside this "
              f"prediction, but NOT corruption —\n{indent}colony.cpp:2129 "
              f"matches those against a race index directly, on a branch "
              f"that\n{indent}skips the player lookup entirely.")
    if rep["out_of_range"]:
        print(f"{indent}Nibble 10 to 13: "
              f"{_n(len(rep['out_of_range']), 'pop')}. No branch in the "
              f"source was found that reads\n{indent}those, so unlike "
              f">= 14 they are unaccounted for — the strongest single "
              f"sign\n{indent}that the mask is wrong.")

    # Say what THIS data leaves open, not a fixed paragraph: a
    # caveat that is printed whatever the numbers say is a caveat
    # nobody reads, and here it would have been false on the one save
    # that carries androids.
    missing = []
    if not rep["sentinels"]:
        missing.append("8 and 9 (android, native), so the sentinel "
                       "branch at colony.cpp:1261")
    if not rep["direct_race"]:
        missing.append(">= 14, so the direct-race branch at "
                       "colony.cpp:2129")
    print()
    if missing:
        print(f"{indent}STILL OPEN — absent from this save:")
        for item in missing:
            print(f"{indent}  - {item}")
        print(f"{indent}Those need a save holding androids, natives or a "
              f"conquered population.\n{indent}Another turn of this one "
              f"will not produce them.")
    else:
        print(f"{indent}This save exercises every branch of the nibble: "
              f"player indices, both\n{indent}sentinels, and at least "
              f"one value >= 14.")


def sidebar_report(records, player_num, indent="  "):
    """The six s_player scalars COLSUM::Draw_Empire_Info_ prints.

    SOURCE TWO, and the only one there is. The offsets come from
    orion2re's own header compiled with its `#pragma pack(1)`, with
    sizeof landing on the 0xf0e in sizes.h — one source, and the one
    that cannot be wrong in the way that matters, because a header
    describes the struct the ENGINE was built from while what is
    parsed here is what came over the wire. A size assert cannot
    catch two adjacent int16s in the wrong order.

    So this prints them beside the labels the original prints, in the
    original's own draw order and with the original's own sign rule,
    for a human to hold against the game's screen. It does not judge:
    there is nothing on the wire to check these against, which is
    exactly why the check is a pair of eyes on two screens.

    THE PAIR TO STARE AT: `surplus_food` (276) and `surplus_bc` (278)
    are two bytes apart, both int16, both net flows, both printed
    signed. Swapped, both stay plausible — they are the same order of
    magnitude in most empires — and no assert anywhere would notice.
    If only one line is going to be checked properly, check those.
    """
    from core.structs import player as player_struct
    from core.structs import unverified as unverified_structs

    kinds = unverified_structs.PLAYER_KINDS
    # Draw order, labels and format from COLSUM::Draw_Empire_Info_
    # (colsum.cpp:418). The ESTR ids are the strings it passes; the
    # text beside them is from orion2_str.h, which carries the table
    # as comments on the enum.
    rows = [
        ("Reserve",    "bc",                 118, False,
         "%sReserve: %s%d"),
        ("Income",     "surplus_bc",         106, True,
         "%sIncome: %s%s%+d"),
        ("Population", "total_pop",          114, False,
         "%sPopulation: %s%d"),
        ("Freighters", "surplus_freighters", 103, False,
         "%sFreighters: %s%d"),
        ("Food",       "surplus_food",       102, True,
         "%sFood: %s%+d"),
        ("Research",   "research_produced",  117, False,
         "%sResearch: %s%d"),
    ]

    if not 0 <= player_num < len(records):
        print(f"{indent}player_num {player_num} is outside the "
              f"{len(records)} player records in the snapshot")
        return

    view = player_struct.parse(records[player_num])
    print(f"{indent}s_player[{player_num}] "
          f"{view.name!r} / {view.race_name!r}\n")
    print(f"{indent}{'label':<11} {'field':<19} {'off':>4} "
          f"{'kind':<9} {'value':>9}   what the original prints")
    print(f"{indent}{'-' * 78}")
    offsets = dict((n, o) for n, o, _k in player_struct.SPEC.fields)
    for label, field, estr, signed, fmt in rows:
        value = getattr(view, field)
        kind = kinds.get(field, ("?", ""))[0]
        shown = f"+{value}" if signed and value >= 0 else str(value)
        print(f"{indent}{label:<11} {field:<19} {offsets[field]:>4} "
              f"{kind:<9} {value:>9}   {label}: {shown}"
              f"   (ESTR {estr} {fmt!r})")

    print(f"\n{indent}Sign rule: only Income (106) and Food (102) "
          f"carry %+d; the other four are %d.")
    print(f"{indent}Income also takes a third %s — the red attribute "
          f"from ERIC::Red_If_Negative_Fmt_String_ (eric.cpp:176), "
          f"which is\n{indent}\\0332 when negative and E_Strings_(12) "
          f"otherwise.")
    print(f"\n{indent}HAZARD: surplus_food @276 and surplus_bc @278 "
          f"are adjacent int16 net flows, both signed-printed.")
    print(f"{indent}Swapped they read plausibly. Check Food and "
          f"Income against the game's own sidebar, not each other.")
    print(f"\n{indent}Kinds are not one kind — do not add a gross to "
          f"a net or difference a count:")
    for _label, field, _e, _s, _f in rows:
        kind, why = kinds.get(field, ("?", "?"))
        print(f"{indent}  {field:<19} {kind:<9} {why}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("array", choices=sorted(ARRAYS))
    ap.add_argument("--records", type=int, default=4,
                    help="how many records to dump (default 4)")
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--port", type=int, default=17362)
    ap.add_argument("--spec", action="store_true",
                    help="decode each record against the registered "
                         "core.structs spec instead of dumping hex")
    ap.add_argument("--full", action="store_true",
                    help="with --spec, print every array element")
    ap.add_argument("--pop-nibble", action="store_true",
                    help="colonies only: test the pop[] low nibble "
                         "against every colony's owner")
    ap.add_argument("--sidebar", action="store_true",
                    help="players only: the six scalars "
                         "COLSUM::Draw_Empire_Info_ prints, beside "
                         "the labels and signs the original uses")
    args = ap.parse_args()

    if args.sidebar and args.array != "players":
        print("--sidebar is a players check; the six scalars live in "
              "s_player")
        return 1

    if args.pop_nibble and args.array != "colonies":
        # Checked before the socket: an argument error should not need
        # a running game to be told about.
        print("--pop-nibble is a colonies check; the nibble lives in "
              "s_colony.pop[]")
        return 1

    spec = load_spec(args.array) if args.spec else None
    if args.spec and spec is None:
        print(f"No spec registered for {args.array!r}. Known: "
              f"{', '.join(sorted(SPECS))}")
        return 1

    client = GameClient()
    if not client.connect(host=args.host, port=args.port):
        print(f"Cannot reach orion2re at {args.host}:{args.port} — "
              f"is the game running with -DORION2RE_EXT=ON?")
        return 1

    print("Waiting for STATE_SNAPSHOT ...")
    gs = None
    deadline = time.monotonic() + 10.0
    while time.monotonic() < deadline:
        client.poll()
        st = client.state
        if st and st.current_screen >= 0:
            gs = st
            break
        time.sleep(0.05)

    if gs is None:
        print("No STATE_SNAPSHOT within 10 s — is a game loaded?")
        client.disconnect()
        return 1
    print(f"Screen {gs.current_screen}, stardate {gs.stardate_str}, "
          f"{gs.num_stars} stars, {gs.num_colonies} colonies, "
          f"{gs.num_nebulas} nebulas\n")

    attr, size = ARRAYS[args.array]
    data = getattr(gs, attr, None)
    client.disconnect()
    if data is None:
        print(f"{attr} not present in state")
        return 1
    records = [data] if isinstance(data, (bytes, bytearray)) else data
    if not records:
        print(f"{attr} is empty — start or load a game with content "
              f"first (the main menu has no map data)")
        return 1

    if args.pop_nibble:
        colony_spec = load_spec("colonies")
        print("── pop[] low nibble: player index, not race "
              + "─" * 20)
        print_pop_nibble_report(pop_nibble_report(records, colony_spec))
        return 0

    if args.sidebar:
        print("── COLSUM::Draw_Empire_Info_ (colsum.cpp:418) "
              + "─" * 20)
        sidebar_report(records, getattr(gs, "player_num", 0))
        print("\n  Read these against the original's own sidebar on "
              "the Colonies screen.\n  Agreement there is the second "
              "source; until then core/structs/unverified.py\n  "
              "PLAYER_SIDEBAR is the honest status, whatever "
              "player.py's verified flag says.")
        return 0

    if spec is not None:
        status = ("VERIFIED" if spec.verified
                  else "UNVERIFIED — this decode is the check, not "
                       "the proof")
        print(f"spec {spec.name}: {spec.size} bytes, "
              f"{len(spec.fields)} fields, {status}")
        if spec.size != size:
            print(f"  WARNING: array record size is {size}, spec says "
                  f"{spec.size} — decoding anyway, but one of the two "
                  f"is wrong and every field below is suspect")
        print()

    for i, raw in enumerate(records[:args.records]):
        print(f"── {args.array}[{i}]  ({len(raw)} bytes) "
              + "─" * 30)
        if spec is not None:
            spec_decode(raw, spec)
            if args.full:
                spec_decode_full(raw, spec)
        else:
            hexdump(raw)
            ascii_runs(raw)
            if len(raw) <= 64:
                int16_columns(raw)
        print()
    print(f"({len(records)} records total; showing "
          f"{min(args.records, len(records))})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
