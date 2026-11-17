"""The end-of-game score screen on the wire — open fix 120 (work order 403).

    87      synthetic screen id (`core.screen_names`): reported while
            `SCORE::Hi_Score_Screen` (score.cpp:490-545) takes input, by a
            ScreenOverride, as the Hall of Fame reports 14.
    "SCOR"  (`doc/ext_score_screen.patch`): written while that holds, before
            FILM. A version byte (1), then int16: the player the tally is
            for, the whole-screen field that ends it (hotkey ESC), the nine
            scores (time, population, elimination, captured colonists,
            technology, Orion, Antares, council), the raw subtotal, the
            modifier in percent, the final score; then int16: the stardate
            figure of the time line, the raw population, the opponents
            defeated, the captured colonies; then ten strings (uint8 length
            and bytes): the lines time, population, elimination, captured
            colonies, technology, Orion, Antares, council (empty when its
            score is not above 0), the total's label, the total's figure;
            the player's name and race name; then uint8 n and per defeated
            player uint8 index, uint8 race, int16 the defeat's figure (tenths)
            and a string, the name.

WHY: `Draw_Hi_Score_Screen` (score.cpp:86-120) printed these nine numbers
from `SCORE::hi`, and nothing sent them: the screen ran under its caller's
id and HD showed the F12 notice. The strings are the engine's own words
(H_Message formats), so the player's language needs no table here.

Read WHOLE or left None (`core/colonyblocks.py`'s rule): an engine without
the fix writes none and reports the caller's id, and HD shows the notice
as before.
"""
import struct as _st

from core.blockreader import Reader

SCREEN_ID = 87
#: The nine components in the order the block carries them and the screen
#: draws them (`Draw_Hi_Score_Screen`, score.cpp:92-100).
COMPONENTS = ("time", "population", "elimination", "captured_colonies",
              "technology", "orion", "antares", "council", "total")
LINES = ("time", "population", "elimination", "captured_colonies",
         "technology", "orion", "antares", "council", "total_label",
         "total_figure")
NUMBERS = ("time", "population", "elimination", "captured_colonies",
           "technology", "orion", "antares", "council", "raw_subtotal",
           "modifier_pct", "final")
RAW = ("stardate", "raw_population", "defeated", "raw_captured_colonies")


def parse(gs, data, pos):
    """Read SCOR at `pos` into `gs.score` (None when absent, short or of
    another version). Returns the new position."""
    gs.score = None
    r = Reader(data, pos)
    if not r.at_tag(b"SCOR"):
        return pos
    r.pos += 4
    try:
        version = r.one("B")
        if version != 1:
            r.refuse("SCOR", f"version {version}")
            return pos
        player, field = r.take("hh")
        scores = dict(zip(NUMBERS, r.take("h" * len(NUMBERS))))
        raw = dict(zip(RAW, r.take("h" * len(RAW))))
        lines = {k: r.text8() for k in LINES}
        name, race_name = r.text8(), r.text8()
        defeated = []
        for _ in range(r.one("B")):
            index, race, figure = r.take("BBh")
            defeated.append({"player": index, "race": race,
                             "figure": figure, "name": r.text8()})
    except ValueError:
        r.refuse("SCOR", "short")
        return pos
    gs.score = {"player": player, "exit_field": field, "scores": scores,
                "raw": raw, "lines": lines, "name": name,
                "race_name": race_name, "defeated": defeated}
    return r.pos


def for_state(state):
    """The score, or None: the block, under the screen's own id."""
    score = getattr(state, "score", None)
    if score is None or getattr(state, "current_screen", -1) != SCREEN_ID:
        return None
    return score


def total_rows(score):
    """What the screen lists, in the original's order: (key, words, figure)
    per component. The council line is left out when its score is not above
    0 (`Draw_Council_Score`, score.cpp:807-812); the total comes last, as
    `Draw_Total_Score` has it, with its own words and figure."""
    out = []
    for key in COMPONENTS[:-1]:
        figure = score["scores"][key]
        if key == "council" and figure <= 0:
            continue
        out.append((key, score["lines"][key], str(figure)))
    out.append(("total", score["lines"]["total_label"],
                score["lines"]["total_figure"]))
    return out


def build(player=0, field=1, scores=None, raw=None, lines=None, name="",
          race_name="", defeated=()):
    """The block as the engine writes it — for the checks' stand-ins."""
    scores = scores or {}
    raw = raw or {}
    lines = lines or {}

    def s(text):
        b = text.encode("latin-1")
        return bytes([len(b)]) + b
    out = b"SCOR" + _st.pack("<Bhh", 1, player, field)
    out += _st.pack("<" + "h" * len(NUMBERS),
                    *(scores.get(k, 0) for k in NUMBERS))
    out += _st.pack("<" + "h" * len(RAW), *(raw.get(k, 0) for k in RAW))
    out += b"".join(s(lines.get(k, "")) for k in LINES)
    out += s(name) + s(race_name) + bytes([len(defeated)])
    for d in defeated:
        out += _st.pack("<BBh", d["player"], d["race"], d["figure"]) + \
            s(d["name"])
    return out
