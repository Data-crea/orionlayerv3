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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("array", choices=sorted(ARRAYS))
    ap.add_argument("--records", type=int, default=4,
                    help="how many records to dump (default 4)")
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--port", type=int, default=17362)
    args = ap.parse_args()

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

    for i, raw in enumerate(records[:args.records]):
        print(f"── {args.array}[{i}]  ({len(raw)} bytes) "
              + "─" * 30)
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
