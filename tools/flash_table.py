#!/usr/bin/env python3
"""The flash table: every walked transition, how often it showed native frames.

    python tools/flash_table.py RUN_DIR [RUN_DIR ...]

Work order 180. Reads the `transitions.json` each `tools/flash_walk.py`
run writes and aggregates per (transition, window size): how many walks,
how many of them presented a native frame, the native frames by the
trace and by the pixel test, and the longest time a native picture stood
before the target's first HD frame. A2's before/after table is two calls
of this, one over the A1 runs and one over the runs after the fix.
"""
import collections
import json
import os
import sys


def aggregate(dirs):
    agg = collections.OrderedDict()
    for d in dirs:
        path = os.path.join(d, "transitions.json")
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        size = "x".join(str(v) for v in data["size"])
        for row in data["rows"]:
            key = (row["transition"], size)
            a = agg.setdefault(key, {"walks": 0, "flashed": 0, "frames": 0,
                                     "pixels": 0, "max_s": 0.0,
                                     "kinds": set()})
            a["walks"] += 1
            a["flashed"] += 1 if row["native_total"] else 0
            a["frames"] += row["native_total"]
            a["pixels"] += row["pixel_native_total"]
            if row["native_before_hd"]:
                a["max_s"] = max(a["max_s"], row["native_seconds"])
            a["kinds"].update(row["kinds"])
    return agg


def table(agg):
    lines = ["| transition | size | walks | with native frames | native "
             "frames (trace / pixels) | longest before HD (s) | kind |",
             "|---|---|---:|---:|---:|---:|---|"]
    for (name, size), a in agg.items():
        lines.append(
            f"| {name} | {size} | {a['walks']} | {a['flashed']} | "
            f"{a['frames']} / {a['pixels']} | {a['max_s']:.3f} | "
            f"{', '.join(sorted(a['kinds'])) or '—'} |")
    walks = sum(a["walks"] for a in agg.values())
    flashed = sum(a["flashed"] for a in agg.values())
    lines.append(f"\n{walks} transition walks, {flashed} with native frames.")
    return "\n".join(lines)


if __name__ == "__main__":
    print(table(aggregate(sys.argv[1:])))
