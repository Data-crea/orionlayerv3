"""The Turn Summary ranked by importance — work order 384, open fix 115.

The engine's Turn Summary (`TURNSUM::Turn_Summary_Popup`) lists the turn's
messages in the order they were added. Open fix 115 sends each message's
engine type with its line (`MSG_TYPE_*`, and for a colony message its
`MSG_COLONY_SUBTYPE_*`, `orion2_consts.h:368-406`), so HD can say how much a
message matters by WHAT IT IS and not by its words (which are the player's
language). This module is that judgement and the grouping; the drawing is
`core/turnsummaryview.py`.

HD EXTENSION `summary_importance` (Data, 10 November 2026): the original
shows no importance, only the order of the list. The table below is HD's
own reading of the engine's types — red: something is lost or going wrong
and wants an answer; yellow: worth a look; green: good news. Nothing in the
engine says it; change the table, not the code, when Data disagrees.
"""
import re

RED, YELLOW, GREEN = 0, 1, 2
SEVERITIES = (RED, YELLOW, GREEN)

#: Categories, in the order a tie between two groups is broken.
COLONY, EMPIRE, SHIPS, SPIES, OTHER = "colony", "empire", "ships", \
    "spies", "other"
CATEGORIES = (COLONY, EMPIRE, SHIPS, SPIES, OTHER)

# `MSG_COLONY_SUBTYPE_*` (orion2_consts.h:394-405)
COLONY_SUBTYPE = {
    0: YELLOW,    # a building scrapped
    1: GREEN,     # production completed
    2: RED,       # genocide
    3: RED,       # assimilation
    4: RED,       # starvation
    5: GREEN,     # settlers arrived
    6: RED,       # plague
    7: GREEN,     # population boom
    8: YELLOW,    # comet
    9: RED,       # rebellion
    10: YELLOW,   # no room for an android
    11: RED,      # an android killed an organic
}
STARVATION = 4

# `MSG_TYPE_*` (orion2_consts.h:368-390) -> (severity, category)
TYPE = {
    1: (GREEN, EMPIRE),     # declare alliance
    2: (RED, EMPIRE),       # declare war
    3: (YELLOW, EMPIRE),    # unknown 0x3
    4: (YELLOW, EMPIRE),    # financial
    5: (RED, SHIPS),        # lost ship
    6: (YELLOW, SHIPS),     # scrap ship
    7: (RED, COLONY),       # lost colony
    8: (YELLOW, SHIPS),     # hyperspace flux
    9: (RED, SHIPS),        # hyperspace beast
    10: (YELLOW, SPIES),    # lost attacking spy
    11: (YELLOW, SPIES),    # lost defending spy
    12: (GREEN, OTHER),     # Artemis
    13: (GREEN, OTHER),     # Artemis leader
    14: (RED, SHIPS),       # failed retreat
    15: (RED, SPIES),       # spy assassination
    16: (YELLOW, OTHER),    # anomaly
    17: (YELLOW, EMPIRE),   # diplomacy
    18: (YELLOW, SHIPS),    # eel spawned
    19: (GREEN, SHIPS),     # eel vanished
    20: (GREEN, OTHER),     # artifacts
    21: (GREEN, OTHER),     # April 1st
    22: (YELLOW, OTHER),    # scrap leader
}


# What each kind is called in a row and in the settings list (English; the
# German is in de.json): `(key, label)`. A key is "c<subtype>" for a colony
# message and "t<type>" for any other; the player's list of hidden kinds
# (`turn_summary_hidden`) holds keys.
COLONY_LABELS = {
    0: "Building scrapped", 1: "Production completed", 2: "Genocide",
    3: "Assimilation", 4: "Starvation", 5: "Settlers arrived",
    6: "Plague", 7: "Population boom", 8: "Comet", 9: "Rebellion",
    10: "No room for an android", 11: "Android killed an organic"}
TYPE_LABELS = {
    1: "Alliance declared", 2: "War declared", 3: "Diplomacy (other)",
    4: "Finances", 5: "Ship lost", 6: "Ship scrapped", 7: "Colony lost",
    8: "Hyperspace flux", 9: "Hyperspace beast", 10: "Attacking spy lost",
    11: "Defending spy lost", 12: "Artemis", 13: "Artemis leader",
    14: "Retreat failed", 15: "Spy assassinated", 16: "Space anomaly",
    17: "Diplomacy", 18: "Space eel appeared", 19: "Space eel vanished",
    20: "Artifacts found", 21: "April 1st", 22: "Leader scrapped"}


def kinds():
    """Every kind the engine reports, as `[(key, label, severity,
    category)]` in the order of the settings list: by category, then
    severity."""
    out = []
    for sub, label in COLONY_LABELS.items():
        out.append(("c%d" % sub, label, COLONY_SUBTYPE[sub], COLONY))
    for kind, label in TYPE_LABELS.items():
        sev, cat = TYPE[kind]
        out.append(("t%d" % kind, label, sev, cat))
    out.sort(key=lambda k: (CATEGORIES.index(k[3]), k[2]))
    return out


def kind_key(msg):
    """The key of a message's kind, or None (an engine without open fix
    115 sends no type)."""
    kind = msg.get("type")
    if kind is None:
        return None
    return "c%d" % msg["subtype"] if kind == 0 else "t%d" % kind


def hidden(settings):
    """The set of kind keys the player has switched off for the Turn
    Summary (`turn_summary_hidden`), tolerant of a hand-edited file."""
    got = (settings or {}).get("turn_summary_hidden") or []
    return {k for k in got if isinstance(k, str)} \
        if isinstance(got, (list, tuple)) else set()


def classify(msg):
    """`(severity, category)` of one message (the wire's dict: `type`,
    `subtype` — None from an engine without open fix 115, which gives
    `(None, OTHER)`: no ranking, the engine's own order)."""
    kind = msg.get("type")
    if kind is None:
        return None, OTHER
    if kind == 0:                       # a colony message: by its subtype
        sev = COLONY_SUBTYPE.get(msg.get("subtype"), YELLOW)
        return sev, COLONY
    return TYPE.get(kind, (YELLOW, OTHER))


def starvation_effect(msg):
    """The number of food a starvation message says it is short of, or
    None: the line's first number (`msg_colony_starvation_food_fmt`,
    "(short %d food)"), read only for the subtype that has one."""
    if msg.get("type") != 0 or msg.get("subtype") != STARVATION:
        return None
    # the line ends "(short N food)": the LAST number, so a star name with a
    # digit in it is not read as the food
    found = re.findall(r"\d+", msg.get("text") or "")
    return int(found[-1]) if found else None


_LEADING_NAME = re.compile(
    r"^([A-Z][\w'-]*(?: (?:[IVX]+|Prime|[A-Z][\w'-]*))*)(?= [a-z(])")
_NOT_NAMES = ("The", "A", "An", "Your", "You", "And", "Scrapped")


def split_name(text, name):
    """`(name, rest)` of a colony line: the line begins with the colony's
    own name (every colony format starts with the planet), so the name
    stands apart as a column and the rest is the sentence; a line that
    does not begin with it stays whole."""
    if name and name != "?" and text.startswith(name):
        return name, text[len(name):].lstrip(" ,:-")
    if name is not None:
        # the colony's listed name is not the line's (a homeworld is "Prime"
        # in the line): the line's own leading name, up to its first
        # lower-case word
        found = _LEADING_NAME.match(text)
        if found and found.group(1).split()[0] not in _NOT_NAMES:
            return found.group(1), text[found.end():].lstrip(" ,:-")
    return None, text


def line_spelling(text, place):
    """`place` ("Thog I") as the line spells it ("Thog Prime") when the line
    names the same star with another suffix; `place` itself otherwise."""
    star = place.rsplit(" ", 1)[0] if " " in place else place
    found = re.search(r"(?<!\w)" + re.escape(star) +
                      r"(?: (?:[IVX]+|Prime))?(?!\w)", text)
    return found.group(0) if found else place


def groups(rows):
    """`rows` are dicts with `severity` (or None), `category` and `order`
    (the engine's own position); returns `[(category, [rows])]`: a group by
    category, the groups by their worst row (then the category order), the
    rows by severity then colony name then the engine's order. Without
    severities (an engine without open fix 115) one group in the engine's
    order."""
    if not rows or any(r["severity"] is None for r in rows):
        return [(OTHER, sorted(rows, key=lambda r: r["order"]))] if rows \
            else []
    by_cat = {}
    for r in rows:
        by_cat.setdefault(r["category"], []).append(r)
    out = []
    for cat, members in by_cat.items():
        members.sort(key=lambda r: (r["severity"], r.get("name") or "",
                                    r["order"]))
        out.append((cat, members))
    out.sort(key=lambda g: (g[1][0]["severity"], CATEGORIES.index(g[0])))
    return out
