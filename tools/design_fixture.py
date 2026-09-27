#!/usr/bin/env python3
"""Cut the Ship Designer's committed stand-in from a live recording.

    python tools/design_fixture.py <recording folder>     # writes the fixture
    python tools/design_fixture.py <recording folder> --check

Work order 185 part 7, the colony fixture's pattern (work order 180,
`tools/fixtures/colony_blocks_180.json`): per stop the trailing blocks of
open fixes 44 and 45 exactly as a scratch engine carrying the patches wrote
them, cut at the DSGN tag, hex — and the stop's field list — so the smoke
suite and `tools/hud_evidence.stage` can put the designer and its pickers
on screen with no engine. Only ids, numbers and the engine-formatted
strings; the design's name is the one the game gave it.

The recording is the scratch recorder's (one folder per stop holding the
snapshot `state.bin` and the list `fields.bin`, and `record.json` naming
the stops); the stops taken are the designer and the three pickers.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core import game_state  # noqa: E402

OUT = os.path.join(ROOT, "tools", "fixtures", "design_blocks_185.json")
STOPS = ("designer", "computer", "weapon", "special")


def cut(folder):
    stops = []
    for name in STOPS:
        d = os.path.join(folder, name)
        with open(os.path.join(d, "state.bin"), "rb") as fh:
            state = fh.read()
        with open(os.path.join(d, "fields.bin"), "rb") as fh:
            fields = game_state.parse_fields(fh.read())
        gs = game_state.parse_state(state)
        if gs.ship_design is None:
            sys.exit(f"{d}: no DSGN block — not a fix-44 recording")
        at = state.index(b"DSGN")
        stops.append({
            "name": name, "screen": gs.current_screen,
            "tail": state[at:].hex(),
            "fields": [[f.index, f.field_type, f.x, f.y, f.x_end, f.y_end,
                        f.hotkey] for f in fields]})
    return {"_note": (
        "Work order 185 part 7: the trailing blocks of open fixes 44 and 45 "
        "(DSGN, DSBX) exactly as a scratch engine carrying the patches wrote "
        "them (SAVE4; never applied to orionlayer-local), cut at the DSGN "
        "tag, hex, and each stop's field list [index, type, x1, y1, x2, y2, "
        "hotkey]. Built by tools/design_fixture.py from the recording in "
        "evidence/work_order_185; read by tools/hud_evidence.stage and the "
        "ship_design smoke group."), "stops": stops}


def state(stop):
    """A stop of the committed stand-in as a snapshot: open fix 44's and
    45's blocks as a scratch engine wrote them, and the stop's field list
    (`tools/hud_evidence.stage` and the ship_design smoke group read it)."""
    from core import designblocks
    from core.game_state import FieldInfo, GameState
    with open(OUT, encoding="utf-8") as fh:
        found = next(s for s in json.load(fh)["stops"] if s["name"] == stop)
    gs = GameState()
    gs.current_screen = found["screen"]
    designblocks.parse(gs, bytes.fromhex(found["tail"]), 0)
    gs.fields = [FieldInfo(index=i, field_type=t, x=x1, y=y1, x_end=x2,
                           y_end=y2, hotkey=k)
                 for i, t, x1, y1, x2, y2, k in found["fields"]]
    return gs


def main(argv):
    folder = next((a for a in argv if not a.startswith("--")), None)
    if folder is None:
        sys.exit(__doc__)
    data = cut(folder)
    text = json.dumps(data, indent=2) + "\n"
    if "--check" in argv:
        with open(OUT, encoding="utf-8") as fh:
            same = fh.read() == text
        print("fixture matches the recording" if same else
              "fixture DIFFERS from the recording")
        return 0 if same else 1
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"wrote {len(data['stops'])} stops -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
