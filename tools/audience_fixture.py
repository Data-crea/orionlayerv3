#!/usr/bin/env python3
"""Cut the diplomacy audience's committed stand-in from live recordings.

    python tools/audience_fixture.py <refused folder> <audience folder>
    python tools/audience_fixture.py <refused folder> <audience folder> --check

Work order 185 part 9, the Ship Designer fixture's pattern
(`tools/design_fixture.py`): per stop the snapshot's tail from open fix
47's "DIPL" tag to the end as a scratch engine carrying fixes 46 and 47
wrote it — every text the game wrote replaced by a stand-in (`neutral`),
every number as it came — hex, and the stop's field list — so the smoke suite and
`tools/hud_evidence.stage` can put the audience on screen with no engine.
The tail holds COLS's place and what follows, which on these stops is
nothing: the audience reports 57, not 1 or 25.

Three stops: the refusal (race slot 0, at war), the greeting and the menu
(race slot 1), from the scratch recorder's folders (`state.bin`,
`fields.bin` per stop).
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core import game_state  # noqa: E402

OUT = os.path.join(ROOT, "tools", "fixtures", "audience_blocks_185.json")
STOPS = (("refused", 0, "01_opened"), ("greeting", 1, "01_opened"),
         ("menu", 1, "02_menu"))


def _swap(tail, words, stand_in):
    """One length-prefixed text of the block, `words`, for `stand_in`."""
    old = bytes([len(words)]) + words.encode("latin-1")
    new = bytes([len(stand_in)]) + stand_in.encode("latin-1")
    assert old in tail, words
    return tail.replace(old, new, 1)


def neutral(tail, audience):
    """The block with every text the game wrote replaced by a stand-in —
    the reply is the player's DIPLOMSx sentence, the menu JIMTEXT's words,
    and neither is ours to commit (the derived stand-ins' rule,
    `tools/make_derived_fixtures.py`). Lengths change; the block is read
    by its own length bytes, so the layout holds."""
    if audience["text"]:
        tail = _swap(tail, audience["text"], f"Reply {audience['response']}")
    if audience["title"]:
        tail = _swap(tail, audience["title"], "Menu title")
    for k, item in enumerate(audience["items"]):
        tail = _swap(tail, item["text"], f"Item {k}")
    return tail


def cut(folders):
    stops = []
    for name, which, stop in STOPS:
        d = os.path.join(folders[which], stop)
        with open(os.path.join(d, "state.bin"), "rb") as fh:
            state = fh.read()
        with open(os.path.join(d, "fields.bin"), "rb") as fh:
            fields = game_state.parse_fields(fh.read())
        gs = game_state.parse_state(state)
        if gs.audience is None:
            sys.exit(f"{d}: no DIPL block — not a fix-47 recording")
        at = state.index(b"DIPL")
        stops.append({
            "name": name, "screen": gs.current_screen,
            "tail": neutral(state[at:], gs.audience).hex(),
            "fields": [[f.index, f.field_type, f.x, f.y, f.x_end, f.y_end,
                        f.hotkey] for f in fields]})
    return {"_note": (
        "Work order 185 part 9: open fix 47's DIPL block and what follows "
        "it as a scratch engine carrying fixes 46 and 47 wrote it (SAVE4; "
        "never applied to orionlayer-local), every text the game wrote "
        "replaced by a stand-in (Reply N, Menu title, Item k), hex, and each "
        "stop's "
        "field list [index, type, x1, y1, x2, y2, hotkey]. Built by "
        "tools/audience_fixture.py from evidence/work_order_185/"
        "P9_audience_*; read by tools/hud_evidence.stage and the audience "
        "smoke group."), "stops": stops}


def state(stop):
    """A stop of the committed stand-in as a snapshot."""
    from core import diplblocks
    from core.game_state import FieldInfo, GameState
    with open(OUT, encoding="utf-8") as fh:
        found = next(s for s in json.load(fh)["stops"] if s["name"] == stop)
    gs = GameState()
    gs.current_screen = found["screen"]
    diplblocks.parse(gs, bytes.fromhex(found["tail"]), 0)
    gs.fields = [FieldInfo(index=i, field_type=t, x=x1, y=y1, x_end=x2,
                           y_end=y2, hotkey=k)
                 for i, t, x1, y1, x2, y2, k in found["fields"]]
    return gs


def main(argv):
    folders = [a for a in argv if not a.startswith("--")]
    if len(folders) != 2:
        sys.exit(__doc__)
    text = json.dumps(cut(folders), indent=2) + "\n"
    if "--check" in argv:
        with open(OUT, encoding="utf-8") as fh:
            same = fh.read() == text
        print("fixture matches the recordings" if same else
              "fixture DIFFERS from the recordings")
        return 0 if same else 1
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"wrote {len(STOPS)} stops -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
