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
    args = ap.parse_args()

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
