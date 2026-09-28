#!/usr/bin/env python3
"""Recorded transitions, for the smoke suite to replay — work order 180 A2.

    python tools/flash_fixture.py RUN_DIR [RUN_DIR ...]

The run folders it was last written from (work order 185), under
~/orionlayer-fixtures/evidence/: work_order_180/{A2_after,B_live,B_net}_
{1920x1080,2576x1432}, work_order_181/P3_orders_{1920x1080,2576x1432} and
work_order_185/P7_design_{1920x1080,2576x1432} (`tools/design_walk.py`,
on a scratch engine with open fixes 44 and 45 — not applied) and
work_order_185/P10_audience_{1920x1080,2576x1432} (`tools/audience_walk.py`,
with open fixes 46 and 47 — not applied), and work_order_187/
P2_name_walk_1920x1080 (the designer's name typed in HD, Enter and ESC
recorded as transitions; the 233 before it reproduced byte for byte first),
and work_order_188/P6_hof_{1920x1080,3840x2160} (the Hall of Fame, in and out
by ESC and by a click, on open fix 50; the 240 before it reproduced byte
for byte first).

Reads the `trace.jsonl` of `tools/flash_walk.py` runs and writes
`tools/fixtures/transitions_180.json`: every walked transition as the
INPUTS the hand-over gate reads, one row per snapshot —

    [snapshot, screen id, live fields, top screen, wants the picture, way in]

`wants the picture` is true where the frame was held or shown natively
(the app's own reading before the gate), `way in` is what the app called
it (`no_screen`, `hand_over`, `f12` or ""). Rows are relative to the
transition's first snapshot. Identical sequences recorded at two window
sizes or on repeated walks are kept once.

The fixture records what the ENGINE and the screens said, not what the
gate did with it, so replaying it through another gate — a regression,
`hold=0` — shows the flash again. That is how the check proves it can
fail.

`research_select` (53) cannot be walked (the engine reaches it only when
a project completes at TURN, which writes SAVE10), so it is added as a
SYNTHETIC transition, named as such, from the shape `core/researchscreen`
documents: the first snapshot at 53 carries the map's list (WAITING, no
hand-over), then the screen's own.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "tools", "fixtures", "transitions_180.json")

SYNTHETIC = [{
    "transition": "galaxy_map -> research_select (SYNTHETIC)",
    "target": "research_select",
    "synthetic": "not walkable: 53 comes only after TURN completes a "
                 "project, and TURN writes SAVE10",
    "rows": [[0, 0, 23, "galaxy_map", False, ""],
             [1, 53, 23, "research_select", False, ""],
             [2, 53, 35, "research_select", False, ""]],
}]


def rows_of(frames):
    out, base = [], None
    for f in frames:
        if f.get("snap") is None:
            raise SystemExit("a trace without snapshot numbers (from before "
                             "180 A2) cannot be replayed")
        base = f["snap"] if base is None else base
        want = f["source"] in ("net", "hold")
        row = [f["snap"] - base, f["screen"], f.get("live") or 0,
               f["hd"], want, f["kind"] if want else ""]
        if not out or out[-1] != row:
            out.append(row)
    return out


def build(dirs):
    seen, transitions = set(), []
    for d in dirs:
        by_name = {}
        order = []
        with open(os.path.join(d, "trace.jsonl"), encoding="utf-8") as fh:
            for line in fh:
                f = json.loads(line)
                key = f["transition"]
                by_name.setdefault(key, []).append(f)
                if key not in order:
                    order.append(key)
        with open(os.path.join(d, "transitions.json"),
                  encoding="utf-8") as fh:
            targets = {r["transition"]: r["target"]
                       for r in json.load(fh)["rows"]}
        # A repeated transition name holds several walks back to back;
        # the walk restarts where the snapshot count falls back or jumps
        # by more than a walk can take (a new mark in flash_walk).
        for name in order:
            walks, cur = [], []
            for f in by_name[name]:
                if cur and f["t"] - cur[-1]["t"] > 5.0:
                    walks.append(cur)
                    cur = []
                cur.append(f)
            if cur:
                walks.append(cur)
            for frames in walks:
                rows = rows_of(frames)
                sig = (name, json.dumps(rows))
                if sig in seen:
                    continue
                seen.add(sig)
                transitions.append({"transition": name,
                                    "target": targets[name],
                                    "source": os.path.basename(d),
                                    "rows": rows})
    return transitions + SYNTHETIC


def main(dirs):
    data = {"_note": "Work order 180 A2: recorded transitions, replayed by "
                     "tools/smoke_suite/090o. Written by "
                     "tools/flash_fixture.py from flash_walk traces; work "
                     "order 181 added every way into and out of screens 1 "
                     "and 25 (tools/colony_accept.py, P3_orders_*); work "
                     "order 185 the Ship Designer and its pickers "
                     "(tools/design_walk.py on a scratch engine with open "
                     "fixes 44 and 45, P7_design_*) and the diplomacy audience "
                     "(tools/audience_walk.py, fixes 46 and 47, "
                     "P10_audience_*).",
            "columns": ["snapshot", "screen", "live_fields", "top",
                        "wants_picture", "way_in"],
            "transitions": build(dirs)}
    # One transition per line: small, and a diff shows which one moved.
    head = {k: v for k, v in data.items() if k != "transitions"}
    lines = [json.dumps(t, separators=(",", ":"))
             for t in data["transitions"]]
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(head, separators=(",", ":"))[:-1]
                 + ',"transitions":[\n' + ",\n".join(lines) + "\n]}\n")
    print(f"{len(data['transitions'])} transitions -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
