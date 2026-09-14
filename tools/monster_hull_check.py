#!/usr/bin/env python3
"""Check core/monsterhull.py against orion2re's own source.

The panel's hull points are a COPY of numbers that live in C++
(`INITSHIP::Get_Ship_Structure_`, the hull and armour tables, two bit
constants). A copy without a checker is the copy that goes stale, and a
wrong hull number on a panel looks exactly like a right one — so this
reads the source and fails on any difference, in the pattern of
`tools/version_check.py`.

What it reads:

    src/game/initship.cpp     Get_Ship_Structure_: the builder threshold
                              and the five (with, without drive) pairs;
                              the tripling in Get_Design_Structure_ and
                              Get_Ship_Armor_Hits_ and which special
                              triggers each
    src/game/techdata.cpp     _hull_data's armor_hp / structure_hp and
                              _armor's ships_bonus, the columns located
                              by name in techdata.h, not by position
    src/game/orion2_consts.h  SPECIAL_HEAVY_ARMOR, SPECIAL_REINFORCED_HULL

Usage (from the project root):
    python tools/monster_hull_check.py
    python tools/monster_hull_check.py ~/some/other/orion2re

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

from core import monsterhull as mh  # noqa: E402
from version_check import DEFAULT_TREES, find_tree  # noqa: E402

RE_STRUCT_FN = re.compile(
    r"Get_Ship_Structure_\s*\(\s*int16_t\s+ship_idx\s*\)\s*\{(.*?)\n    \}",
    re.S)
RE_BUILDER = re.compile(r"if\s*\(\s*builder\s*<=\s*(\d+)\s*\)")
RE_CASE = re.compile(
    r"case\s+(\d+)\s*:\s*result\s*=\s*(\d+)\s*;\s*"
    r"if\s*\(\s*ship->d\.ftl_type\s*<=\s*0\s*\)\s*\{\s*return\s+(\d+)\s*;")
RE_DESIGN_FN = re.compile(
    r"Get_Design_Structure_\s*\(\s*s_ship_design\s+d\s*\)\s*\{(.*?)\n    \}",
    re.S)
RE_ARMOR_FN = re.compile(
    r"Get_Ship_Armor_Hits_\s*\(\s*int16_t\s+ship_idx\s*\)\s*\{(.*?)\n    \}",
    re.S)


def _read(tree, *parts):
    with open(os.path.join(tree, "src", "game", *parts),
              encoding="utf-8", errors="replace") as handle:
        return handle.read()


def _struct_fields(header, name):
    """Member names of `struct <name> { ... };`, in order."""
    m = re.search(r"struct\s+%s\s*\{(.*?)\};" % re.escape(name), header, re.S)
    if not m:
        return None
    return re.findall(r"(\w+)\s*;", m.group(1))


def _table_rows(source, name):
    """Rows of `<type> <name>[...] = { {..}, {..} };` as token lists."""
    m = re.search(r"\b%s\s*\[[^\]]*\]\s*=\s*\{(.*?)\n\};" % re.escape(name),
                  source, re.S)
    if not m:
        return None
    return [[tok.strip() for tok in row.split(",")]
            for row in re.findall(r"\{([^{}]*)\}", m.group(1))]


def _const(consts, name):
    m = re.search(r"\b%s\s*=\s*(-?\d+)" % re.escape(name), consts)
    return int(m.group(1)) if m else None


def read_source(tree):
    """What the source says, or raises ValueError naming what failed."""
    initship = _read(tree, "initship.cpp")
    techdata = _read(tree, "techdata.cpp")
    header = _read(tree, "techdata.h")
    consts = _read(tree, "orion2_consts.h")
    out = {}

    fn = RE_STRUCT_FN.search(initship)
    if not fn:
        raise ValueError("Get_Ship_Structure_ not found in initship.cpp")
    builder = RE_BUILDER.search(fn.group(1))
    if not builder:
        raise ValueError("Get_Ship_Structure_ has no `builder <= N` test")
    out["builder_max"] = int(builder.group(1))
    out["monsters"] = {int(c): (int(without), int(with_))
                       for c, with_, without in RE_CASE.findall(fn.group(1))}

    design = RE_DESIGN_FN.search(initship)
    armor = RE_ARMOR_FN.search(initship)
    if not design or not armor:
        raise ValueError("Get_Design_Structure_ or Get_Ship_Armor_Hits_ "
                         "not found in initship.cpp")
    out["design_triples_on"] = ("SPECIAL_REINFORCED_HULL" in design.group(1)
                                and "*= 3" in design.group(1))
    out["armor_triples_on"] = ("SPECIAL_HEAVY_ARMOR" in armor.group(1)
                               and "*= 3" in armor.group(1))

    hull_fields = _struct_fields(header, "s_tech_hull_data")
    armor_fields = _struct_fields(header, "s_tech_armor_data")
    hull_rows = _table_rows(techdata, "_hull_data")
    armor_rows = _table_rows(techdata, "_armor")
    if not (hull_fields and armor_fields and hull_rows and armor_rows):
        raise ValueError("a table or its struct was not found in "
                         "techdata.cpp / techdata.h")
    ia, is_ = hull_fields.index("armor_hp"), hull_fields.index("structure_hp")
    ib = armor_fields.index("ships_bonus")
    out["hull_armor_hp"] = tuple(int(r[ia]) for r in hull_rows)
    out["hull_structure_hp"] = tuple(int(r[is_]) for r in hull_rows)
    out["armor_ships_bonus"] = tuple(int(r[ib]) for r in armor_rows)

    out["special_heavy_armor"] = _const(consts, "SPECIAL_HEAVY_ARMOR")
    out["special_reinforced_hull"] = _const(consts, "SPECIAL_REINFORCED_HULL")
    return out


def compare(src):
    """[(what, ours, theirs)] for every difference; empty when all agree."""
    pairs = [
        ("builder threshold", mh.DESIGN_BUILDER_MAX, src["builder_max"]),
        ("fixed structure per builder", mh.MONSTER_STRUCTURE,
         src["monsters"]),
        ("hull armor_hp", mh.HULL_ARMOR_HP, src["hull_armor_hp"]),
        ("hull structure_hp", mh.HULL_STRUCTURE_HP, src["hull_structure_hp"]),
        ("armour ships_bonus", mh.ARMOR_SHIPS_BONUS, src["armor_ships_bonus"]),
        ("SPECIAL_HEAVY_ARMOR", mh.SPECIAL_HEAVY_ARMOR,
         src["special_heavy_armor"]),
        ("SPECIAL_REINFORCED_HULL", mh.SPECIAL_REINFORCED_HULL,
         src["special_reinforced_hull"]),
        ("Reinforced Hull triples the design structure", True,
         src["design_triples_on"]),
        ("Heavy Armor triples the armour", True, src["armor_triples_on"]),
    ]
    return [(what, ours, theirs) for what, ours, theirs in pairs
            if ours != theirs]


def main(argv):
    tree = find_tree(argv)
    if tree is None:
        looked = argv[1:] if len(argv) > 1 else DEFAULT_TREES
        print(f"orion2re source tree not found (looked in {looked})")
        return 2
    try:
        src = read_source(tree)
    except (OSError, ValueError) as err:
        print(f"{tree}: cannot read the hull sources — {err}")
        return 1
    diffs = compare(src)
    for what, ours, theirs in diffs:
        print(f"MISMATCH {what}: core/monsterhull.py {ours!r}, "
              f"orion2re {theirs!r}")
    if diffs:
        return 1
    print(f"{tree}: core/monsterhull.py agrees with initship.cpp, "
          f"techdata.cpp and orion2_consts.h")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
