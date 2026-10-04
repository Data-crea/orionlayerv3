"""What the research panel may vouch for — the states, and the rule.

Split out of `core/researchscreen.py` by work order 166 part A, when
the waiting state pushed that file past the 300-line guideline
(decision 6) — and split at a seam rather than to satisfy a number:
"may this screen draw what it has" is a different question from "how
does the panel behave", and the answer to it is a PURE FUNCTION here,
so the rule can be checked without a screen, a window or a game.
"""
import logging

from core import researchlist

log = logging.getLogger("research")

#: Why the screen is on the fallback, in the order they are tested.
READY = "ok"
NO_PLAYER = "no_player"
NAMES_MISSING = "names_missing"
WORDING_MISSING = "wording_missing"
UNVALIDATED = "unvalidated"

#: THE GAME HAS NOT BUILT ITS LIST YET — not a disagreement, an
#: absence, and the one state that does NOT hand over.
#:
#: `Clear_Fields_` leaves count 1 (fields.cpp:207) and `parse_fields`
#: drops slot 0, so the wire carries ZERO fields between the switch to
#: 36 and `Init_Entry_Data_` finishing. Until work order 166 that was
#: treated as a contradiction and the screen handed over — the
#: original flashed up on every entry, which is what Data saw at
#: stardate 3500.3.
#:
#: The Fleets screen met the same thing at screen 4 (work order 142 A,
#: `screens/fleets/screen.py`) and calls it `waiting`. The name is
#: taken from there on purpose.
WAITING = "waiting"

#: How many consecutive SNAPSHOTS with an EMPTY list the screen waits
#: before it calls the silence a failure and hands over after all.
#:
#: **MEASURED, not guessed** (`dev:tools/entry_glimpse.py`, work order 166
#: part A): five entries into change mode on SAVE4, and every one of
#: them took exactly **22 frames** at 60 Hz from the activation to a
#: validated list — 0.37 s, 7 snapshots at the engine's one per 55 ms input
#: tick (18.2 a second, work order 177). Three times that, so a slower
#: machine or a bigger list has room, and a game that reports 36 and never
#: builds a list still ends up on the picture with the reason in the log.
#: Counted in snapshots since work order 212 (decision 78): 66 FRAMES gave
#: up after 1.1 s at 60 Hz and far sooner at a higher frame rate; 20
#: snapshots are the same 1.1 s at every frame rate.
#:
#: A BOUND IS NOT A TIMER (decision 21): it is the give-up, and the
#: thing that ends the wait is the list arriving.
EMPTY_LIST_GRACE = 20


def classify(names, wording, record, fields, select_mode, empty_frames):
    """`(entries, state, problems)` for one frame's inputs.

    The order of the tests is the order of the states above, and it is
    the order the screen used before this became a function: names,
    wording, a player record, then the game's own field list.

    `record` is `(tech_fields, tech_applications)` or None.
    `empty_frames` is how many consecutive snapshots the wire has carried
    NO list — which is what tells `WAITING` from `UNVALIDATED`.
    """
    if names is not None and names.state != "ok":
        return [], NAMES_MISSING, [f"research names: {names.state}"]
    if wording is not None and wording.state != "ok":
        return [], WORDING_MISSING, [f"panel wording: {wording.state}"]
    if record is None:
        return [], NO_PLAYER, ["no player record on the wire"]
    tech_fields, tech_applications = record
    # `current_field=0` IN BOTH MODES: the game has zeroed it before
    # the list is built in select mode and zeroes it around the call in
    # change mode, so the current field IS offered in change mode
    # without anything here asking for it.
    entries = researchlist.reconstruct(
        tech_fields, tech_applications, current_field=0,
        select_mode=select_mode)
    problems = researchlist.validate_against_fields(
        entries, fields, select_mode=select_mode)
    if not problems:
        return entries, READY, []
    # NOT YET, versus WRONG. An empty list is the game between
    # `Clear_Fields_` and `Init_Entry_Data_`; a list that is there and
    # disagrees is the fault work order 165 part D found, and that one
    # hands over at once, on the first frame, exactly as before.
    if not fields and empty_frames <= EMPTY_LIST_GRACE:
        return entries, WAITING, problems
    return entries, UNVALIDATED, problems
