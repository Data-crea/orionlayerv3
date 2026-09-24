#!/usr/bin/env python3
"""Check core/leaderskills.py against orion2re's own source.

The Leaders screen's skill rows, prices and titles are computed from a
COPY of numbers that live in C++ and on no wire: `MOX::_skill_data[54]`,
the ESTRINGS ids its names and the level titles come from, and the xp
steps of `Get_Officer_Base_Level_`. A wrong bonus on a leader's row
looks exactly like a right one, so this reads the source and fails on
any difference, in the pattern of `tools/monster_hull_check.py`.

What it reads:

    src/game/mox.cpp       the `_skill_data[54]` initialiser, row by row
    src/game/estrings.cpp  `_skill_data[i].name = E_Strings_(n)` and the
                           two `*_officer_level_names[i] = E_Strings_(n)`
                           blocks
    src/game/officer.cpp   the five `if (xp < n)` steps, `Officer_Is_Female_`'s
                           ids, and Loknar's maintenance index

Usage (from the project root):
    python tools/leader_skill_check.py
    python tools/leader_skill_check.py ~/some/other/orion2re

Exit codes: 0 all agree, 1 a mismatch or a source this cannot parse,
2 the source tree was not found (an unreachable tree is not the same
answer as a wrong number).
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import leaderskills as ls  # noqa: E402
from version_check import find_tree  # noqa: E402

RE_TABLE = re.compile(r"s_skill_data\s+_skill_data\[54\]\s*=\s*\{(.*?)\n\s*\};",
                      re.S)
RE_ROW = re.compile(
    r"\{\s*(\d+)\s*,\s*(0x[0-9a-fA-F]+|\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,"
    r"\s*(\d+)\s*,\s*(\d+)\s*,\s*nullptr\s*,\s*\"([^\"]*)\"\s*\}")
RE_NAME = re.compile(
    r"_skill_data\[(\d+)\]\.name\s*=\s*ESTRINGS::E_Strings_\((0x[0-9a-fA-F]+|\d+)\)")
RE_LEVEL = re.compile(
    r"MOX::(_officer_level_names|_star_officer_level_names)\[(\d+)\]\s*=\s*"
    r"ESTRINGS::E_Strings_\((0x[0-9a-fA-F]+|\d+)\)")
RE_BASE_FN = re.compile(
    r"Get_Officer_Base_Level_\(int16_t xp, int8_t warlord\)\s*\{(.*?)\n    \}",
    re.S)
RE_STEP = re.compile(r"if\s*\(\s*xp\s*<\s*(\d+)\s*\)")
RE_FEMALE_FN = re.compile(
    r"bool __cdecl Officer_Is_Female_\(int16_t officer_idx\)\s*\{(.*?)\n    \}",
    re.S)
RE_FEMALE_ID = re.compile(r"officer_idx\s*==\s*(\d+)")
RE_LOKNAR = re.compile(r"if\s*\(\s*leader_idx\s*==\s*(\d+)\s*/\*\s*0x41\s*\*/"
                       r"\s*\|\|\s*has_free_maintenance_skill\s*\)")


def _read(tree, name):
    with open(os.path.join(tree, "src", "game", name),
              encoding="utf-8", errors="replace") as handle:
        return handle.read()


def read_source(tree):
    """Everything this checker compares, as read out of the tree."""
    mox = _read(tree, "mox.cpp")
    table = RE_TABLE.search(mox)
    rows = []
    if table:
        for m in RE_ROW.finditer(table.group(1)):
            sid, mask, typ, strength, level_up, cost, fmt = m.groups()
            rows.append((int(sid), int(mask, 0), int(typ), int(strength),
                         int(level_up), int(cost), fmt))
    est = _read(tree, "estrings.cpp")
    names = {int(i): int(n, 0) for i, n in RE_NAME.findall(est)}
    levels = {"_officer_level_names": {}, "_star_officer_level_names": {}}
    for which, i, n in RE_LEVEL.findall(est):
        levels[which][int(i)] = int(n, 0)
    off = _read(tree, "officer.cpp")
    base = RE_BASE_FN.search(off)
    steps = tuple(int(s) for s in RE_STEP.findall(base.group(1))) \
        if base else ()
    fem = RE_FEMALE_FN.search(off)
    female = frozenset(int(i) for i in RE_FEMALE_ID.findall(fem.group(1))) \
        if fem else frozenset()
    loknar = RE_LOKNAR.search(off)
    return {"rows": rows, "names": names, "levels": levels,
            "steps": steps, "female": female,
            "loknar": int(loknar.group(1)) if loknar else None}


def compare(src):
    """A list of disagreements, empty when the copy matches the source."""
    out = []
    if len(src["rows"]) != ls.SKILL_COUNT:
        out.append(f"mox.cpp: {len(src['rows'])} _skill_data rows parsed, "
                   f"leaderskills has {ls.SKILL_COUNT}")
    for got, want in zip(src["rows"], ls.SKILLS):
        if got != want:
            out.append(f"skill {want[0]}: mox.cpp {got}, leaderskills {want}")
    want_names = dict(enumerate(ls.SKILL_NAME_ESTRINGS))
    if src["names"] != want_names:
        diff = sorted(k for k in set(src["names"]) | set(want_names)
                      if src["names"].get(k) != want_names.get(k))
        out.append(f"skill name ESTRINGS differ at {diff[:10]}")
    for which, typ in (("_officer_level_names", 0),
                       ("_star_officer_level_names", 1)):
        got = tuple(src["levels"][which].get(i) for i in range(6))
        if got != ls.LEVEL_NAME_ESTRINGS[typ]:
            out.append(f"{which}: estrings.cpp {got}, leaderskills "
                       f"{ls.LEVEL_NAME_ESTRINGS[typ]}")
    if src["steps"] != ls.LEVEL_STEPS:
        out.append(f"Get_Officer_Base_Level_ steps {src['steps']}, "
                   f"leaderskills {ls.LEVEL_STEPS}")
    if src["female"] != ls.FEMALE:
        out.append(f"Officer_Is_Female_ {sorted(src['female'])}, "
                   f"leaderskills {sorted(ls.FEMALE)}")
    if src["loknar"] != ls.LOKNAR:
        out.append(f"Officer_Maintenance_'s free index {src['loknar']}, "
                   f"leaderskills {ls.LOKNAR}")
    return out


def main(argv):
    tree = find_tree(argv)
    if tree is None:
        print("no orion2re tree found — nothing checked")
        return 2
    try:
        src = read_source(tree)
    except (OSError, AttributeError) as exc:
        print(f"could not read the source: {exc}")
        return 1
    diff = compare(src)
    print(f"orion2re {tree}")
    print(f"  _skill_data rows {len(src['rows'])}, names {len(src['names'])}, "
          f"level steps {src['steps']}")
    if diff:
        for line in diff:
            print("  MISMATCH " + line)
        return 1
    print("OK — core/leaderskills.py matches mox.cpp, estrings.cpp and "
          "officer.cpp")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
