"""The acceptance fixtures, and what a SNAPSHOT can see of them.

One home for the table, because two tools read it and a second copy
of a savegame map is the screen-ID map's failure with worse
consequences: every picture and every table would still be correct
and none of them would be about what it claimed.

The prose home for the files themselves — where they came from, what
is in them, their sha256 — is `~/orionlayer-fixtures/README.md`,
which is not in the repository because a savegame is the player's own
game data (decisions 40 and 42). What IS here is the fingerprint a
run can check without opening a file.
"""

#: The acceptance fixtures, by what a SNAPSHOT can see of them —
#: `v3_projektstatus.md`, "Acceptance fixtures — the two savegames".
#: Stardate alone is not enough: 3502.4 and 3502.5 are one tick apart
#: and any game reaches them.
FIXTURES = {
    "reference": {"stardate": 35024, "stars": 99, "colonies": 55},
    "natives": {"stardate": 35025, "stars": 71, "colonies": 36},
    # THE AUTOSAVE ONE TURN BEFORE `natives`, added 8 September 2026
    # because it is the state the pick-round evidence was taken on
    # and it was reachable only as "no acceptance fixture at all".
    # `~/Master of Orion 2/SAVE10.GAM`, sha256 2610f39c00f68ebe…,
    # in-game "(Auto Save)". Seven player colonies, no Urna I, Rha IV
    # at four pops — so it has the two `max_farms == 0` colonies the
    # No Farming label needs and, like the reference save, NO NATIVE:
    # the pick-up refusal is unreachable here too.
    "natives_autosave": {"stardate": 35024, "stars": 71,
                         "colonies": 36},
}


def fixture_name(state):
    """Which acceptance fixture a snapshot IS, or None.

    Shared with `colony_list_preview`, which puts the answer on the
    provenance band: two tools, one table. A second copy of this map
    is the screen-ID-map failure with savegames in it — every picture
    would still be correct and none of them would be about what it
    claimed.
    """
    got = {"stardate": state.stardate,
           "stars": len(getattr(state, "stars", None) or []),
           "colonies": state.num_colonies}
    return next((n for n, f in FIXTURES.items() if f == got), None)


def identify(state, expect):
    """True when the game is on the fixture this run claims.

    **ADDED 7 September 2026, AFTER THIS TOOL PRODUCED THREE CLEAN
    ACCEPTANCE RUNS AGAINST THE WRONG GAME.** Every line of them was
    true — the clicks landed, the pop words matched their predictions,
    no other colony changed — and none of it was evidence about the
    reference save, because the game had a different one loaded and
    nothing in the run said so. The status document already required
    that "anything below that reads a save reads it by its fixture
    name"; this tool did not, and a report is only as good as the
    thing it was measured on.

    Reported, never guessed: an unknown state names what it saw.
    """
    if expect == "any":
        print("fixture check skipped (--expect any)")
        return True
    want = FIXTURES.get(expect)
    got = {"stardate": state.stardate,
           "stars": len(getattr(state, "stars", None) or []),
           "colonies": state.num_colonies}
    if want is None:
        print(f"unknown fixture {expect!r}; known: {sorted(FIXTURES)}")
        return False
    if got == want:
        print(f"fixture: {expect} ({got['stars']} stars, stardate "
              f"{got['stardate'] / 10:.1f}) — the run is about this save")
        return True
    named = [n for n, f in FIXTURES.items() if f == got]
    print(f"WRONG SAVE. This run claims {expect} {want}, the game has "
          f"{got}" + (f" — which is the {named[0]} fixture" if named
                      else " — which is no acceptance fixture at all"))
    print("  Load the right slot and re-run. A green table measured on "
          "the wrong game is worse than no table.")
    return False


