#!/usr/bin/env python3
"""Extract the score screen's portraits from the player's MOO2 — work order 406.

    python tools/score_art_extract.py                 # the usual dirs
    python tools/score_art_extract.py /path/to/DATA   # a folder with SCORE.LBX
    python tools/score_art_extract.py --list          # say what it would take

The popup extractor's shape (decision 38): raw LBX entry blobs and a manifest
with a format version, decoded at load time in `screens/score/popicons.py` through
`core/lbx.py`. Never committed, never shipped (decisions 40, 42, 95): the
output directory is gitignored.

WHAT IT TAKES (`SCORE::Load_Hi_Score_Graphics`, score.cpp:1255-1275):

  SCORE.LBX
    0                    the screen's 640 x 480 picture; its PALETTE is the
                         one the portraits are drawn with (their own headers
                         carry none)
    1                    42 x 48 frame drawn over each eliminated player's
                         portrait (`race_icon_frame_anim`)
    2..14                the 40 x 46 portrait of race `entry - 2`, the 13
                         stock races (`race_icon_anims[i]`, STOCK_RACE_COUNT)

The population icons are RACEICON.LBX's and already extracted by
`tools/raceicon_extract.py`.
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
DEFAULT_OUT = os.path.join(ROOT, "assets", "shared", "score", "gamedata")
#: STOCK_RACE_COUNT (orion2_consts.h:1379).
STOCK_RACE_COUNT = 13


def wanted():
    """{file stem: (lbx, entry)}."""
    out = {"score_0": ("SCORE.LBX", 0), "score_1": ("SCORE.LBX", 1)}
    for race in range(STOCK_RACE_COUNT):
        out[f"score_{race + 2}"] = ("SCORE.LBX", race + 2)
    return out


#: The file `tools/setup.py` takes as proof of a finished extraction.
SENTINEL = "score_2"


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
                     f"    python tools/score_art_extract.py "
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
        "_what": ("The score screen's palette, portrait frame and the 13 "
                  "race portraits out of the player's own Master of Orion 2. "
                  "Never committed, never shipped (decisions 38, 40, 42, "
                  "95). Rebuild with tools/score_art_extract.py."),
        "source": {k: {"path": v, "sha256": _sha(v)} for k, v in paths.items()},
        "entries": {k: {"lbx": n, "entry": e, "bytes": len(files[n][e])}
                    for k, (n, e) in take.items()},
    }
    if dry_run:
        return manifest
    os.makedirs(out, exist_ok=True)
    # Every file goes through a temp name and a rename, so an interrupted run
    # never leaves a half-written .bin under its real name, and the SENTINEL
    # (`score_2.bin`, the file tools/setup.py looks for) is renamed LAST:
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
