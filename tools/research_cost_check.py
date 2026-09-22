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
from core import researchlist  # noqa: E402
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


#: An application row: a name, its own id, then its field — which is a
#: number in 211 rows and the symbolic TECH_FIELD_INVALID in one
#: (app 125). A regex that only takes digits reads 211 rows and lines
#: every later app up against the wrong field, silently.
APP_ROW = re.compile(
    r"\{\s*[A-Za-z_]\w*\s*,\s*(\d+)\s*,\s*(-?\d+|[A-Za-z_]\w*)\s*,")


def read_tables(tree):
    """The four tables core/researchlist.py transcribes, from the source.

    Returns (tables, problems). `tables` maps the module's own constant
    names to what the source says, so the comparison in main() cannot
    name one table and read another.
    """
    problems = []
    game = os.path.join(tree, "src", "game")

    def load(name):
        return open(os.path.join(game, name), encoding="utf-8",
                    errors="replace").read()

    consts = load("orion2_consts.h")
    const = {m.group(1): int(m.group(2)) for m in
             re.finditer(r"(TECH_(?:FIELD|APP)_\w+)\s*=\s*(-?\d+)", consts)}

    src = load("techdata.cpp")
    start = src.find("_technology_fields[TECH_FIELD_COUNT] = {")
    rows = ROW.findall(src[start:src.index("\n};", start)]) if start >= 0 \
        else []
    if not rows:
        problems.append("_technology_fields not found in techdata.cpp")
    # The row's first number is the field's own id; if that is not the
    # row index, `next_field_id` cannot be indexed by field id either.
    if [int(r[0]) for r in rows] != list(range(len(rows))):
        problems.append("_technology_fields rows are not in field-id order "
                        "— NEXT_FIELD cannot be indexed by field id")
    next_field = tuple(int(r[2]) for r in rows)

    start = src.find("_technology_applications[TECH_APP_COUNT] = {")
    arows = APP_ROW.findall(src[start:src.index("\n};", start)]) \
        if start >= 0 else []
    if not arows:
        problems.append("_technology_applications not found in techdata.cpp")
    if [int(r[0]) for r in arows] != list(range(len(arows))):
        problems.append("_technology_applications rows are not in app-id "
                        "order — APP_FIELD cannot be indexed by app id")
    unknown = [r[1] for r in arows
               if not re.match(r"^-?\d+$", r[1]) and r[1] not in const]
    if unknown:
        problems.append(f"tech_field_id values this cannot resolve: "
                        f"{sorted(set(unknown))}")
    app_field = tuple(int(r[1]) if re.match(r"^-?\d+$", r[1])
                      else const.get(r[1], -99999) for r in arows)

    tech = load("tech.cpp")
    mox = load("mox.cpp")

    def array(text, decl):
        m = re.search(decl + r"\s*=\s*\{([^}]*)\}", text)
        return tuple(int(v) for v in re.findall(r"-?\d+", m.group(1))) \
            if m else ()

    entry_to_group = array(tech, r"_entry_to_group\[8\]")
    first_in_group = array(mox, r"_first_field_in_group\[10\]")
    techdata = load("techdata.cpp")
    starting = array(techdata, r"_starting_tech_field_ids\[6\]")
    if not starting:
        problems.append("_starting_tech_field_ids not found in "
                        "techdata.cpp")
    # AND THE SAME SIX, WRITTEN OUT AS HEX ONE BY ONE at tech.cpp:668.
    # The array and the branch are two copies in the ENGINE, so both are
    # read: a transcription that agreed with one of them and not the
    # other would be right about nothing in particular.
    branch = re.search(
        r"bool is_creative = false;(.*?)\n        \}", tech, re.S)
    inline = tuple(int(v, 16) for v in re.findall(
        r"tid == (0x[0-9A-Fa-f]+)", branch.group(1))) if branch else ()
    if not inline:
        problems.append("Display_Entry_Text_'s six field ids could not "
                        "be read from tech.cpp")

    # The hyper-advanced switch, as an offset rather than eight cases:
    # every TECH_FIELD_X case must return TECH_APP_X at the same
    # distance, or researchlist.hyper_application() is wrong.
    fn = re.search(r"Get_Hyper_Tech_App_ID_\(int16_t \w+\) \{(.*?)\n    \}",
                   tech, re.S)
    hyper = []
    if fn:
        for field_name, app_name in re.findall(
                r"case\s+(TECH_FIELD_\w+):\s*\n\s*return\s+(TECH_APP_\w+);",
                fn.group(1)):
            if field_name in const and app_name in const:
                hyper.append((const[field_name], const[app_name]))
        if not hyper:
            problems.append("Get_Hyper_Tech_App_ID_'s cases could not be read")
    else:
        problems.append("Get_Hyper_Tech_App_ID_ not found in tech.cpp")

    return {
        "NEXT_FIELD": next_field,
        "APP_FIELD": app_field,
        "ENTRY_TO_GROUP": entry_to_group,
        "FIRST_FIELD_IN_GROUP": first_in_group,
        "_hyper_cases": tuple(hyper),
        "ALL_APPLICATIONS_FIELDS": starting,
        "_inline_six": inline,
        "_consts": const,
    }, problems


def check_tables(tree):
    """Problems comparing core/researchlist.py against the source."""
    tables, problems = read_tables(tree)
    for name in ("NEXT_FIELD", "APP_FIELD", "ENTRY_TO_GROUP",
                 "FIRST_FIELD_IN_GROUP"):
        ours = tuple(getattr(researchlist, name))
        theirs = tables[name]
        if not theirs:
            continue                 # already reported by read_tables
        if ours != theirs:
            diff = [(i, a, b) for i, (a, b) in enumerate(zip(theirs, ours))
                    if a != b][:8]
            problems.append(
                f"researchlist.{name} differs from the source: "
                f"{len(theirs)} entries there, {len(ours)} here; "
                f"(index, source, ours) {diff}")
        else:
            print(f"            researchlist.{name:<21}: "
                  f"{len(ours)} entries agree")

    # THE SIX "EVERYONE GETS EVERYTHING" FIELDS, against BOTH of the
    # engine's own copies: the array and the inline branch.
    if tables["ALL_APPLICATIONS_FIELDS"]:
        ours = tuple(researchlist.ALL_APPLICATIONS_FIELDS)
        if set(ours) != set(tables["ALL_APPLICATIONS_FIELDS"]):
            problems.append(
                f"researchlist.ALL_APPLICATIONS_FIELDS is {sorted(ours)}, "
                f"_starting_tech_field_ids is "
                f"{sorted(tables['ALL_APPLICATIONS_FIELDS'])}")
        elif tables["_inline_six"] and \
                set(ours) != set(tables["_inline_six"]):
            problems.append(
                f"researchlist.ALL_APPLICATIONS_FIELDS is {sorted(ours)}, "
                f"Display_Entry_Text_ tests "
                f"{sorted(tables['_inline_six'])}")
        else:
            print(f"            _starting_tech_field_ids      : "
                  f"{len(ours)} ids agree, and so does the inline branch")

    # The three sentinels and the two boundaries, by name.
    const = tables["_consts"]
    for ours_name, theirs_name in (
            ("FIELD_INVALID", "TECH_FIELD_INVALID"),
            ("FIELD_STARTING_TECH", "TECH_FIELD_STARTING_TECH"),
            ("FIELD_XENON_TECHNOLOGY", "TECH_FIELD_XENON_TECHNOLOGY"),
            ("FIELD_HYPER_FIRST", "TECH_FIELD_BIOLOGY"),
            ("APP_HYPER_FIRST", "TECH_APP_BIOLOGY"),
            ("FIELD_COUNT_HYPER_LAST", "TECH_FIELD_SOCIOLOGY")):
        if theirs_name not in const:
            problems.append(f"{theirs_name} not found in orion2_consts.h")
        elif getattr(researchlist, ours_name) != const[theirs_name]:
            problems.append(
                f"researchlist.{ours_name} is "
                f"{getattr(researchlist, ours_name)}, {theirs_name} is "
                f"{const[theirs_name]}")

    # The hyper-advanced switch really is one offset.
    for field_id, app_id in tables["_hyper_cases"]:
        if researchlist.hyper_application(field_id) != app_id:
            problems.append(
                f"Get_Hyper_Tech_App_ID_ maps field {field_id} to app "
                f"{app_id}; researchlist gives "
                f"{researchlist.hyper_application(field_id)}")
    if tables["_hyper_cases"]:
        print(f"            Get_Hyper_Tech_App_ID_        : "
              f"{len(tables['_hyper_cases'])} cases are one offset")

    # And the derivation the whole reconstruction rests on runs without
    # overflowing a field's four slots — the condition the original
    # exits the game on (techinit.cpp:466-468).
    try:
        derived = researchlist.field_applications()
        print(f"            tech[4] derivation            : "
              f"{len(derived)} fields carry applications")
    except AssertionError as exc:
        problems.append(str(exc))
    return problems


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

    problems += check_tables(tree)

    if problems:
        print("\nMISMATCH")
        for line in problems:
            print(f"  - {line}")
        return 1
    print(f"\nOK — {len(costs)} costs, the count, the surcharge field and "
          f"its step, and the four tables core/researchlist.py transcribes, "
          f"all agree")
    return 0


if __name__ == "__main__":
    sys.exit(main())
