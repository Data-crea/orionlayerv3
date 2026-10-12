"""The engine's government numbers — work order 206.

TRANSCRIBED from `typedef enum GOVERNMENT` (orion2_consts.h:192-202): the
number the game keeps in `traits[TRAIT_CURRENT_GOVERNMENT]` and indexes
its government names by (`MOX::_government_labels`, estrings.cpp:99-106).
Custom Race offers the four base forms; the other four are what research
turns them into.

Until work order 206 `traits.json` gave Democracy 3, which is the
engine's IMPERIUM. The engine never received it — a choice is sent as the
option's own field (ACTIVATE_FIELD) — but HD's own state carried the wrong
number. `normalize` makes every government option read its number from
here, so a mod's `traits.json` written with the old 3 is read as 4; smoke
check 039b holds `traits.json`, this table and, where the engine tree is
on disk, orion2_consts.h to each other.
"""
import logging

log = logging.getLogger("custom_race")

#: label -> the engine's number (orion2_consts.h:193-200).
GOVERNMENTS = {
    "Feudal": 0,
    "Confederation": 1,
    "Dictatorship": 2,
    "Imperium": 3,
    "Democracy": 4,
    "Federation": 5,
    "Unification": 6,
    "Galactic Unification": 7,
}

#: The trait id of the government in Custom Race's own table.
TRAIT_ID = 0


def normalize(categories):
    """Give every government option the engine's number for its label;
    returns the labels that were corrected (logged once each)."""
    fixed = []
    for cat in categories:
        if cat.get("trait_id") != TRAIT_ID:
            continue
        for opt in cat.get("options", []):
            want = GOVERNMENTS.get(opt.get("label"))
            if want is not None and opt.get("value") != want:
                log.warning("traits.json: %s carries %r; the engine's "
                            "number is %d (orion2_consts.h) — read as %d",
                            opt["label"], opt.get("value"), want, want)
                opt["value"] = want
                fixed.append(opt["label"])
    return fixed
