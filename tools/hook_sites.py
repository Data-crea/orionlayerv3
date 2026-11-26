"""The battle's hook calls, counted per file (work order 437).

Moved out of `tools/patch_markers.py`, which the table would have pushed
over the 40 KB limit (decision 6). `tools/version_check.py` calls
`hook_site_problems`; the golden table is held by check 090r.
"""
import os


#: Golden count of the tactical battle's hook calls per file: every
#: `ext::Combat_Event(ext::CEV_...` and `ext::Combat_Note(ext::CEV_...` in
#: `src/game/` of the orionlayer branch, read on 26 November 2026 (work
#: order 437, audit combat F1). `LOCAL_PATCHES` holds ONE marker per patch
#: in ONE file (patch 56 spans eleven files), so a hook lost in a merge of
#: another file — as the upstream split moved `Fire_Ship`, `Resolve_Raid`
#: and `Kill_Missile` — passed `version_check` unseen. A function the
#: upstream moves again shows here as one file down and another up: change
#: this table in the same commit as the hook, and say why. The total is
#: the sum; `Combat_Note` (open fixes 82-95) and `Combat_Event` (56, 63,
#: 77) are counted together because both are lost the same way.
HOOK_SITES = {
    os.path.join("src", "game", "beams.cpp"): 1,
    os.path.join("src", "game", "cmbtfir2_boarding.cpp"): 2,
    os.path.join("src", "game", "cmbtfire.cpp"): 4,
    os.path.join("src", "game", "cmbtmis.cpp"): 4,
    os.path.join("src", "game", "cmbtmov1.cpp"): 3,
    os.path.join("src", "game", "cmbtspec.cpp"): 3,
    os.path.join("src", "game", "combat1.cpp"): 2,
    os.path.join("src", "game", "combat_firing.cpp"): 4,
    os.path.join("src", "game", "combinit.cpp"): 1,
    os.path.join("src", "game", "missile_tracking.cpp"): 2,
}

#: What a hook call looks like in the source; the lines in `src/ext/` that
#: DEFINE and forward the two functions do not start with `ext::`.
HOOK_CALL = r"ext::Combat_(?:Event|Note)\(ext::CEV_"


def hook_site_problems(tree, min_files=100):
    """Lines to report for `tree`: a hook-carrying file whose count is not
    the golden one, and a file outside the table that gained a hook.

    A tree with fewer than `min_files` sources in `src/game` is not an
    engine (the suite's marker-only stand-ins): nothing to count there, so
    no problem is reported for it; the real tree has about 360."""
    import re
    pattern = re.compile(HOOK_CALL)
    found, problems = {}, []
    game = os.path.join(tree, "src", "game")
    if not os.path.isdir(game):
        return []
    names = [n for n in sorted(os.listdir(game)) if n.endswith(".cpp")]
    if len(names) < min_files:
        return []
    for name in names:
        with open(os.path.join(game, name), errors="replace") as handle:
            count = len(pattern.findall(handle.read()))
        if count:
            found[os.path.join("src", "game", name)] = count
    for rel in sorted(set(HOOK_SITES) | set(found)):
        want, have = HOOK_SITES.get(rel, 0), found.get(rel, 0)
        if want != have:
            problems.append(
                f"{rel} carries {have} battle hook call(s), "
                f"tools/hook_sites.HOOK_SITES says {want} — a hook "
                f"lost or moved by a merge (open fix 56 and its "
                f"successors)")
    return problems
