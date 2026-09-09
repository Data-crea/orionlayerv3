"""The acceptance fixtures, and what a SNAPSHOT can see of them.

One home for the table, because two tools read it and a second copy
of a savegame map is the screen-ID map's failure with worse
consequences: every picture and every table would still be correct
and none of them would be about what it claimed.

The prose home for the files themselves — where they came from, what
is in them, their sha256 — is `~/orionlayer-fixtures/README.md`,
which is not in the repository because a savegame is the player's own
game data (decisions 40 and 42). What IS here is the fingerprint a
run can check without opening a file — and, since 9 September 2026,
the check that the loaded game still IS that file.
"""
import hashlib
import os

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




# ── THE SAVE ON DISK IS THE AUTHORITY ────────────────────────────
#
# `identify` above answers "is the game on the right save" from a
# fingerprint — stardate, star count, colony count. That is enough to
# catch the wrong slot and not enough to catch the RIGHT slot after
# something has written to it, which is the failure that cost a run
# on 9 September 2026: a diagnostic made thirty real pop moves,
# several of which did not restore, and every later run would have
# been measured against a save that had drifted while reporting
# "fixture: reference" on every line.
#
# So the records are compared against the file. MOO2 writes the
# colony array uncompressed, and on a freshly loaded slot the
# snapshot's `colonies_raw` is byte-for-byte what the `.GAM` holds.
#
# THE OFFSET IS GATED ON THE SHA256, which is what makes a stored
# offset legitimate rather than a magic number: a different file
# cannot be sliced at 607 and believed. It was established by
# locating the live array in the file on a fresh load — `gam.find(
# b"".join(colonies_raw))` — and it is re-derivable that way in one
# line by anyone who doubts it.
FIXTURE_FILES = {
    "reference": {
        "file": "fixture_reference_3502.4.GAM",
        "sha256": "ab70cc9ad5442335a58498bf49de8c6517838826fb"
                  "07a789e323b85c02370bd6",
        "colony_offset": 607,
        "colony_count": 55,
    },
    "natives": {
        "file": "fixture_natives_3502.5.GAM",
        "sha256": "b1f1aa466716d6c0c6b28c84fe270f430c732ec7cb"
                  "3172d221be44b68708e2c8",
        "colony_offset": 607,
        "colony_count": 36,
    },
}

#: `s_colony`'s packed size. Imported rather than repeated — the spec
#: is the one home for it (decision 23).
try:
    from core.structs.colony import SIZE as COLONY_SIZE
except Exception:                              # pragma: no cover
    COLONY_SIZE = 361

#: Where the fixtures live. Outside the repository, because a
#: savegame is the player's own game data (decisions 40 and 42).
FIXTURE_DIR = os.path.expanduser(
    os.environ.get("ORIONLAYER_FIXTURES", "~/orionlayer-fixtures"))


def fixture_colonies(expect, root=None):
    """The colony records the `.GAM` holds, or (None, why).

    Absence is a STATE and not an error: a clone has no fixtures, and
    a run that cannot find one has to say so rather than skip the
    check silently (decision 42's pattern).
    """
    spec = FIXTURE_FILES.get(expect)
    if spec is None:
        return None, f"no file is recorded for the {expect!r} fixture"
    path = os.path.join(root or FIXTURE_DIR, spec["file"])
    if not os.path.exists(path):
        return None, f"the fixture is not on this disk: {path}"
    with open(path, "rb") as fh:
        blob = fh.read()
    got = hashlib.sha256(blob).hexdigest()
    if got != spec["sha256"]:
        return None, (f"{spec['file']} has sha256 {got[:16]}…, the "
                      f"table says {spec['sha256'][:16]}… — the stored "
                      f"offset describes a different file")
    off, n = spec["colony_offset"], spec["colony_count"]
    end = off + n * COLONY_SIZE
    if end > len(blob):
        return None, (f"{spec['file']} is {len(blob)} bytes and the "
                      f"array would end at {end}")
    return [blob[off + i * COLONY_SIZE: off + (i + 1) * COLONY_SIZE]
            for i in range(n)], None


def verify_colonies(state, expect, names=None, root=None):
    """True when every colony record equals the one in the `.GAM`.

    **THIS IS THE CHECK THAT `identify` IS NOT.** The fingerprint says
    which save is loaded; this says the save is still as it was
    loaded. A tool that injects clicks writes to the player's game,
    and the difference between "the reference fixture" and "the
    reference fixture with three pops moved" is invisible to every
    other line a run prints.

    `names` maps a colony index to a name, for the report — the
    eleven the player owns are the ones a reader can act on, and an
    index alone sends them back to a struct dump.
    """
    want, why = fixture_colonies(expect, root)
    if want is None:
        print(f"COLONY CHECK SKIPPED: {why}")
        print("  The run continues, and it is NOT evidence that the "
              "save is unmodified.")
        return True
    got = [bytes(r) for r in state.colonies_raw]
    if len(got) != len(want):
        print(f"the game reports {len(got)} colony records and the "
              f"file holds {len(want)}")
        return False
    bad = [i for i, (a, b) in enumerate(zip(got, want)) if a != b]
    if not bad:
        print(f"colonies: all {len(got)} records match "
              f"{FIXTURE_FILES[expect]['file']} byte for byte")
        return True
    print(f"THE LOADED GAME HAS DRIFTED FROM THE SAVE. "
          f"{len(bad)} of {len(got)} colony records differ:")
    for i in bad[:15]:
        label = (names or {}).get(i)
        offs = [k for k in range(COLONY_SIZE) if got[i][k] != want[i][k]]
        print(f"  colony {i:3d}"
              + (f" {label!r}" if label else "")
              + f": {len(offs)} bytes differ, first at {offs[:8]}")
    if len(bad) > 15:
        print(f"  … and {len(bad) - 15} more")
    print("  RELOAD THE SLOT. Every number this run would print is "
          "true and none of it would be about the fixture it names.")
    return False
