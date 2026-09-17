#!/usr/bin/env python3
"""Check core/research.py's cost table against orion2re's own source.

`core.research.FIELD_COST` is a COPY of the sixth column of
`TECHDATA::_technology_fields` (techdata.cpp:319ff). A copy without a
checker is the copy that goes stale, and a wrong research cost shows up as
a turn count that looks exactly as plausible as a right one — so this reads
the table out of the source and fails on any difference, in the pattern of
`tools/monster_hull_check.py` and `tools/version_check.py` (decision 36).

What it reads:

    src/game/techdata.cpp     _technology_fields, one row per technology
                              field; the cost column located by the
                              struct's own member order in orion2.h, not
                              by counting commas blindly
    src/game/techdata.h       s_tech_field_data, to know which member of
                              the row the cost is
    src/game/orion2_consts.h  TECH_FIELD_COUNT
    src/game/colcalc.cpp      Player_Research_Cost_: the field from which
                              the hyper-advanced surcharge applies and
                              what one count costs

Usage (from the project root):
    python tools/research_cost_check.py
    python tools/research_cost_check.py ~/some/other/orion2re

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

from core import research  # noqa: E402
from version_check import DEFAULT_TREES, find_tree  # noqa: E402

#: The row as techdata.cpp writes it: a name, then five numbers, a brace
#: group of four, then the cost and one more number. The cost's POSITION is
#: taken from the struct below rather than assumed.
ROW = re.compile(
    r"\{\s*[A-Za-z_]\w*\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,"
    r"\s*\{[^}]*\}\s*,\s*(\d+)\s*,\s*(\d+)\s*\}")


def read_source(tree):
    """(costs, field_count, hyper_first, hyper_step) from the source."""
    problems = []
    consts = open(os.path.join(tree, "src", "game", "orion2_consts.h"),
                  encoding="utf-8", errors="replace").read()
    m = re.search(r"TECH_FIELD_COUNT\s*=\s*(\d+)", consts)
    count = int(m.group(1)) if m else None
    if count is None:
        problems.append("TECH_FIELD_COUNT not found in orion2_consts.h")

    header = open(os.path.join(tree, "src", "game", "techdata.h"),
                  encoding="utf-8", errors="replace").read()
    block = re.search(r"struct s_tech_field_data \{(.*?)\};", header, re.S)
    members = re.findall(r"\b(\w+)\s*(?:\[[^\]]*\])?\s*;", block.group(1)) \
        if block else []
    # The row's fourth captured number is the sixth member; say so rather
    # than trusting the regex's shape alone.
    if len(members) < 7 or members[5] != "cost":
        problems.append(
            f"s_tech_field_data's sixth member is "
            f"{members[5] if len(members) > 5 else '?'}, not 'cost' — this "
            f"checker reads the wrong column now")

    src = open(os.path.join(tree, "src", "game", "techdata.cpp"),
               encoding="utf-8", errors="replace").read()
    start = src.find("_technology_fields[TECH_FIELD_COUNT] = {")
    if start < 0:
        problems.append("_technology_fields not found in techdata.cpp")
        return None, count, None, None, problems
    body = src[start:src.index("\n};", start)]
    costs = [int(r[3]) for r in ROW.findall(body)]

    calc = open(os.path.join(tree, "src", "game", "colcalc.cpp"),
                encoding="utf-8", errors="replace").read()
    fn = re.search(r"Player_Research_Cost_\(s_player.*?\n    \}", calc, re.S)
    hyper_first = hyper_step = None
    if fn:
        first = re.search(r"tech_field >= (\d+)", fn.group(0))
        step = re.search(r"modifier \* (\d+)", fn.group(0))
        hyper_first = int(first.group(1)) if first else None
        hyper_step = int(step.group(1)) if step else None
    else:
        problems.append("Player_Research_Cost_ not found in colcalc.cpp")
    return costs, count, hyper_first, hyper_step, problems


def main():
    tree = find_tree(sys.argv)
    if tree is None:
        print(f"orion2re source tree not found (looked in "
              f"{sys.argv[1:] or DEFAULT_TREES})")
        return 2
    costs, count, hyper_first, hyper_step, problems = read_source(tree)
    print(f"orion2re    {tree}")
    print(f"            TECH_FIELD_COUNT              : {count}")
    print(f"            _technology_fields rows read  : "
          f"{len(costs) if costs else 0}")
    print(f"            hyper-advanced from field     : {hyper_first} "
          f"(+{hyper_step} per count)")

    if costs is not None:
        if len(costs) != count:
            problems.append(
                f"techdata.cpp gives {len(costs)} rows, TECH_FIELD_COUNT is "
                f"{count} — the table was not read whole")
        if tuple(costs) != tuple(research.FIELD_COST):
            diff = [(i, a, b) for i, (a, b) in enumerate(
                zip(costs, research.FIELD_COST)) if a != b][:8]
            problems.append(
                f"core/research.FIELD_COST differs from techdata.cpp at "
                f"(field, source, ours): {diff}")
    if count is not None and count != research.FIELD_COUNT:
        problems.append(f"core/research.FIELD_COUNT is "
                        f"{research.FIELD_COUNT}, the source says {count}")
    if hyper_first is not None and \
            hyper_first != research.HYPER_ADVANCED_FIRST_FIELD:
        problems.append(
            f"the hyper-advanced surcharge starts at field {hyper_first} in "
            f"the source, at {research.HYPER_ADVANCED_FIRST_FIELD} here")
    if hyper_step is not None and hyper_step != research.HYPER_ADVANCED_STEP:
        problems.append(
            f"one hyper-advanced count is {hyper_step} in the source, "
            f"{research.HYPER_ADVANCED_STEP} here")

    if problems:
        print("\nMISMATCH")
        for line in problems:
            print(f"  - {line}")
        return 1
    print(f"\nOK — {len(costs)} costs, the count, the surcharge field and "
          f"its step all agree")
    return 0


if __name__ == "__main__":
    sys.exit(main())
