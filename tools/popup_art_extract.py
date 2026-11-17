#!/usr/bin/env python3
"""Extract the turn popups' pictures from the player's MOO2 — work order 402.

    python tools/popup_art_extract.py                 # the usual dirs
    python tools/popup_art_extract.py /path/to/DATA   # a folder with the LBX files
    python tools/popup_art_extract.py --list          # say what it would take

The invasion extractor's shape (decision 38): raw LBX entry blobs and a
manifest with a format version, decoded at load time in `core/popupart.py`
through `core/lbx.py`. Never committed, never shipped (decisions 40, 42, 95):
the output directory is gitignored.

WHAT IT TAKES (events.cpp, antaroom.cpp):

  EVENTS.LBX
    0                    the event screen's mouse picture, whose palette the
                         event screen sets (`Event_Fade_In`, events.cpp:
                         2731-2754) — kept for the manifest's completeness
    2..37                the news picture of event `entry - 2`, 0..35
                         (`Load_Event_Picture`, events.cpp:2053-2056)
  ANTAROOM.LBX
    0                    24 x 24 mouse picture; the room's PALETTE
                         (`Reload_Main_Antaran_Room_Screen`, antaroom.cpp:96)
    1                    the room's full-screen file animation, 55 frames,
                         about 12 MB (`Open_File_Animation`, :117)

NOT taken: the studio animation EVENTS.LBX entry 1 (31 frames, 1.4 MB) the
GNN event screen plays behind the news picture — HD's popup keeps Data's
studio from the mod folder (core/turnpopupcontent.py `gnn_studio`).
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import lbx  # noqa: E402
from fleet_art_extract import _sha, find_lbx  # noqa: E402

FORMAT_VERSION = 1
DEFAULT_OUT = os.path.join(ROOT, "assets", "shared", "turnpopup", "gamedata")
EVENT_COUNT = 36


def wanted():
    """{file stem: (lbx, entry)}."""
    out = {"events_0": ("EVENTS.LBX", 0)}
    for i in range(EVENT_COUNT):
        out[f"event_{i}"] = ("EVENTS.LBX", i + 2)
    out["antaroom_0"] = ("ANTAROOM.LBX", 0)
    out["antaroom_1"] = ("ANTAROOM.LBX", 1)
    return out


#: The file `tools/setup.py` takes as proof of a finished extraction.
SENTINEL = "event_0"


def _write(path, data):
    tmp = path + ".part"
    with open(tmp, "wb") as fh:
        fh.write(data)
    os.replace(tmp, path)


def extract(folder=None, out=DEFAULT_OUT, dry_run=False):
    paths = {}
    for name in sorted({n for n, _e in wanted().values()}):
        found = find_lbx(folder, name)
        if found is None:
            sys.exit(f"{name} not found. Give the folder that holds it:\n"
                     f"    python tools/popup_art_extract.py "
                     f"/path/to/'Master of Orion 2'")
        paths[name] = found
    files = {k: lbx.read_entries(v) for k, v in paths.items()}
    take = wanted()
    for stem, (name, entry) in take.items():
        if entry >= len(files[name]):
            sys.exit(f"{paths[name]} holds {len(files[name])} entries; "
                     f"{stem} needs {entry}")
    manifest = {
        "format": FORMAT_VERSION,
        "_what": ("The turn popups' pictures — the GNN news picture of each "
                  "event and the Antaran room's palette and animation — out "
                  "of the player's own Master of Orion 2. Never committed, "
                  "never shipped (decisions 38, 40, 42, 95). Rebuild with "
                  "tools/popup_art_extract.py."),
        "source": {k: {"path": v, "sha256": _sha(v)} for k, v in paths.items()},
        "entries": {k: {"lbx": n, "entry": e, "bytes": len(files[n][e])}
                    for k, (n, e) in take.items()},
    }
    if dry_run:
        return manifest
    os.makedirs(out, exist_ok=True)
    # Every file goes through a temp name and a rename, so an interrupted run
    # never leaves a half-written .bin under its real name, and the SENTINEL
    # (`event_0.bin`, the file tools/setup.py looks for) is renamed LAST:
    # a run that stops early is not mistaken for a finished extraction.
    order = [s for s in take if s != SENTINEL] + [SENTINEL]
    for stem in order:
        name, entry = take[stem]
        if stem == SENTINEL:
            _write(os.path.join(out, "manifest.json"),
                   (json.dumps(manifest, indent=2) + "\n").encode("utf-8"))
        # indent=2: the tree's JSON convention (smoke check 062).
        _write(os.path.join(out, f"{stem}.bin"), files[name][entry])
    return manifest


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("folder", nargs="?", default=None)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    m = extract(a.folder, a.out, dry_run=a.list)
    print(f"{len(m['entries'])} entries from "
          + ", ".join(sorted(m["source"])))
    if not a.list:
        print(f"written to {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
