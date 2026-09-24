# smoke-suite area: leaders
#
# Part of the OrionLayer smoke suite — 090a_leaders_the_leader_record_and_skill_table.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/, in file-name order and in ONE
# namespace. This one did NOT stand inside main(): it is work order
# 167, the Leaders screen, part B — the data the screen is drawn from.
#
# The 4 check(s) it holds:
#   - s_leader_data is VERIFIED and out of quarantine: its 15 members
#     tile 59 bytes under the C++ names, the header route covers it,
#     and the star spec carries officer_index[8] at 187
#   - core/leaderskills.py == mox.cpp, estrings.cpp and officer.cpp
#     (tools/leader_skill_check.py), and the checker refuses a skewed copy
#   - the officer.cpp rules the rows are built from: levels, bonuses,
#     the C format, the listed leaders, the price and the upkeep
#   - the second source for the struct (tools/leader_check.py) measures
#     both link directions and refuses a broken one; on a disk with the
#     player's saves it also reads them and says so
import importlib.util as _ld_ilu
import struct as _ld_st

from core import leaderskills as _ld_ls
from core.structs import Spec as _LdSpec
from core.structs import leader as _ld_leader
from core.structs import star as _ld_star
from core.structs import unverified as _ld_unv

_ld_root = os.path.dirname(SCREENS_DIR)


def _ld_tool(name):
    """A tool module, loaded by path — the suite's own pattern."""
    _spec = _ld_ilu.spec_from_file_location(
        f"_ld_{name}", os.path.join(_ld_root, "tools", f"{name}.py"))
    _mod = _ld_ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    return _mod


def _ld_pack(**kw):
    """One s_leader_data, packed through the verified spec's own
    offsets and kinds, every field not given at the engine's "nobody"
    values (status -1, player -1, location -1)."""
    _vals = {"status": -1, "player_index": -1, "location": -1,
             "tech_application": [0, 0, 0]}
    _vals.update(kw)
    _b = bytearray(_ld_leader.SIZE)
    _fmt = {"u8": "<B", "i8": "<b", "i16": "<h", "u32": "<I"}
    for _n, _o, _k in _ld_leader.SPEC.fields:
        _v = _vals.get(_n)
        if _v is None:
            continue
        if _k.startswith("str"):
            _raw = _v.encode("latin-1")[:int(_k[3:]) - 1]
            _b[_o:_o + len(_raw)] = _raw
        elif _k == "u8[3]":
            _b[_o:_o + 3] = bytes(_v)
        else:
            _b[_o:_o + _LdSpec.kind_width(_k)] = _ld_st.pack(_fmt[_k], _v)
    return bytes(_b)


# ── 1. THE STRUCT IS VERIFIED, AND IT SAYS SO IN THE RIGHT PLACES ──
_ld_spec = _ld_leader.SPEC
assert _ld_spec.verified and _ld_spec.size == 59 and _ld_leader.COUNT == 67
_ld_end = 0
for _n, _o, _k in _ld_spec.fields:
    assert _o == _ld_end, f"s_leader_data: {_n} at {_o}, expected {_ld_end}"
    _ld_end = _o + _LdSpec.kind_width(_k)
assert _ld_end == 59, _ld_end
assert [f[0] for f in _ld_spec.fields] == [
    "name", "title", "type", "xp", "general_skills", "special_skills",
    "tech_application", "pict_num", "skill_value", "level", "location",
    "eta", "display_level_popup", "status", "player_index"], (
    "the spec's member names are the C++ names — that is what lets the "
    "header route generate its asserts")
_ld_shc = _ld_tool("struct_header_check")
assert "leader" in _ld_shc.COVERED, "the header route no longer covers it"
assert not any(isinstance(_v, _LdSpec) and _v.name == "s_leader_data"
               for _v in vars(_ld_unv).values()), (
    "s_leader_data is back in the quarantine")
for _cite in ("SOURCE 1", "SOURCE 2", "tools/leader_check.py",
              "skill_value", "officer_index"):
    assert _cite in _ld_leader.__doc__, f"leader.py lost {_cite!r}"
_ld_sv = _ld_leader.parse(_ld_pack(name="Leader 1", title="Title 1",
                                   type=1, xp=150, general_skills=0x40,
                                   special_skills=0x4, skill_value=9,
                                   location=12, eta=3, status=1,
                                   player_index=2, pict_num=5))
assert (_ld_sv.name, _ld_sv.title, _ld_sv.type, _ld_sv.xp) == (
    "Leader 1", "Title 1", 1, 150)
assert (_ld_sv.location, _ld_sv.eta, _ld_sv.status,
        _ld_sv.player_index, _ld_sv.pict_num) == (12, 3, 1, 2, 5)
_ld_so = {_n: (_o, _k) for _n, _o, _k in _ld_star.SPEC.fields}
assert _ld_so.get("officer_index") == (187, "i8[8]"), _ld_so.get(
    "officer_index")
ok("s_leader_data verified and out of quarantine: 15 members tile 59 "
   "bytes under the C++ names, the header route covers it, and the "
   "star spec carries officer_index[8] at 187")

# ── 2. THE SKILL TABLE IS HELD TO THE SOURCE ──────────────────
_ld_lsc = _ld_tool("leader_skill_check")
_ld_tree = _ld_lsc.find_tree(["smoke"])
if _ld_tree is not None:
    _ld_src = _ld_lsc.read_source(_ld_tree)
    assert _ld_lsc.compare(_ld_src) == [], _ld_lsc.compare(_ld_src)
    # THE CONTROL: the same source with one strength moved must be
    # refused, or the comparison is not looking.
    _ld_bad = dict(_ld_src)
    _ld_bad["rows"] = [tuple(_r) for _r in _ld_src["rows"]]
    _r0 = list(_ld_bad["rows"][30])
    _r0[3] += 1
    _ld_bad["rows"][30] = tuple(_r0)
    assert _ld_lsc.compare(_ld_bad), "a skewed row passed the checker"
    report(f"skill table read from {_ld_tree}: "
           f"{len(_ld_src['rows'])} rows")
else:
    report("skill table NOT checked against mox.cpp — no orion2re tree "
           "on this disk")
assert len(_ld_ls.SKILLS) == 54 and len(_ld_ls.SKILL_NAME_ESTRINGS) == 54
assert _ld_ls.SKILL_NAME_ESTRINGS[4] == 0x26F and \
    _ld_ls.SKILL_NAME_ESTRINGS[40] == 0x2A0, "the two names that break the run"
ok("core/leaderskills.py == mox.cpp, estrings.cpp and officer.cpp "
   "(tools/leader_skill_check.py), and the checker refuses a skewed copy")

# ── 3. THE RULES A ROW IS BUILT FROM ─────────────────────────
_LdRec = type("_LdRec", (), {})


def _ld_rec(**kw):
    _r = _LdRec()
    _d = {"name": "Leader", "title": "", "type": 0, "xp": 0,
          "general_skills": 0, "special_skills": 0,
          "tech_application": [0, 0, 0], "skill_value": 0, "location": -1,
          "eta": 0, "status": -1, "player_index": -1, "pict_num": 0}
    _d.update(kw)
    for _k, _v in _d.items():
        setattr(_r, _k, _v)
    return _r


# Levels step at 60/150/300/500/1000, and 5 only with WARLORD
# (officer.cpp:44-61); leader 66 never gets it (:88-89).
assert [_ld_ls.base_level(_x, False) for _x in
        (0, 59, 60, 149, 150, 299, 300, 499, 500, 999, 1000)] == \
    [0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 4]
assert _ld_ls.base_level(1000, True) == 5
_ld_w = _ld_rec(xp=1000, player_index=0)
assert _ld_ls.shown_level(_ld_w, 3, lambda p: True) == 5
assert _ld_ls.shown_level(_ld_w, 66, lambda p: True) == 4
assert _ld_ls.shown_level(_ld_rec(xp=1000), 3, lambda p: True) == 4
# Bonus = ceil((level + 1) / level_up) * strength / 10 — Navigator
# (skill 30, level_up 4) is the case that shows the ceiling.
assert [_ld_ls.skill_bonus(_l, 30) for _l in range(6)] == [1, 1, 1, 1, 2, 2]
assert [_ld_ls.skill_bonus(_l, 31) for _l in range(6)] == [1, 1, 1, 2, 2, 2]
assert _ld_ls.skill_bonus(1, 10) == 120      # Famous at level 1
# The C format, including the lone '%' glibc prints as nothing.
assert _ld_ls.c_format("+%d%", 1) == "+1"
assert _ld_ls.c_format("%d%%", 3) == "3%"
assert _ld_ls.c_format("-%dBC", 60) == "-60BC"
assert _ld_ls.c_format("+10BC", 7) == "+10BC"
# Special skills of the leader's type first, then the general ones.
_ld_mix = _ld_rec(type=0, general_skills=0x4, special_skills=0x1 | 0x4000)
assert _ld_ls.displayed_skills(_ld_mix) == [6, 52, 2]
# The listed leaders: own, of the view's type, status >= 0, index
# order, four at most (officer.cpp:2705-2730).
_ld_many = [_ld_rec(type=_i % 2, status=(0 if _i != 4 else -1),
                    player_index=(1 if _i < 12 else 0))
            for _i in range(14)]
assert _ld_ls.captain_id_list(_ld_many, 1, 0) == [0, 2, 6, 8]
assert _ld_ls.captain_id_list(_ld_many, 0, 0) == [12]
# Price and upkeep: stored skill_value x (unowned level + 1) x 10, x 20
# for Megawealth, less the best famous bonus; upkeep (cost + 99) / 100,
# at least 1, 0 for Megawealth and for Loknar (officer.cpp:383-434).
_ld_team = [_ld_rec(type=1, skill_value=6, xp=60, status=4,
                    player_index=0),
            _ld_rec(type=1, general_skills=0x40, xp=150, status=1,
                    player_index=0),
            _ld_rec(type=0, general_skills=0x100, skill_value=3, status=4,
                    player_index=0)]
_ld_nw = (lambda p: False)
assert _ld_ls.famous_bonus(_ld_team, 0, _ld_nw) == 180
assert _ld_ls.hire_cost(_ld_team, 0, 0, _ld_nw) == 0           # 120 - 180
assert _ld_ls.hire_cost(_ld_team, 0, 1, _ld_nw) == 120         # nobody famous
assert _ld_ls.maintenance(_ld_team, 0, 1, _ld_nw) == 2
assert _ld_ls.hire_cost(_ld_team, 2, 1, _ld_nw) == 60          # x20
assert _ld_ls.maintenance(_ld_team, 2, 1, _ld_nw) == 0
ok("the officer.cpp rules a row is built from: level steps and WARLORD, "
   "the bonus ceiling, the C format, the listed leaders, price and upkeep")

# ── 4. THE SECOND SOURCE, AS A TOOL THAT CAN FAIL ────────────
_ld_lc = _ld_tool("leader_check")
from core.structs import ship as _ld_ship


def _ld_ship_bytes(officer):
    _b = bytearray(_ld_ship.SIZE)
    _b[116:118] = _ld_st.pack("<h", officer)
    return bytes(_b)


def _ld_star_bytes(slots):
    _b = bytearray(_ld_star.SIZE)
    _b[187:195] = _ld_st.pack("<8b", *slots)
    return bytes(_b)


_ld_recs = [_ld_pack(name=f"Leader {_i}") for _i in range(67)]
_ld_recs[3] = _ld_pack(name="Leader 3", type=0, status=1, location=1,
                       player_index=2)
_ld_recs[5] = _ld_pack(name="Leader 5", type=1, status=1, location=0,
                       player_index=1)
_ld_ships = [_ld_ship_bytes(-1), _ld_ship_bytes(3)]
_ld_stars = [_ld_star_bytes([-1, 5, -1, -1, -1, -1, -1, -1])]
_ld_m = _ld_lc.measure(_ld_recs, _ld_stars, _ld_ships, None)
assert _ld_m["ships"][:2] == (2, 2) and _ld_m["stars"][:2] == (2, 2), _ld_m
assert _ld_lc.verdict(_ld_m)
# Broken in each direction: the ship names nobody, and a star names a
# leader in the WRONG player's slot.
_ld_m2 = _ld_lc.measure(_ld_recs, [_ld_star_bytes([5, -1, -1, -1, -1, -1,
                                                   -1, -1])],
                        [_ld_ship_bytes(-1), _ld_ship_bytes(-1)], None)
assert _ld_m2["ships"][0] < _ld_m2["ships"][1] and \
    _ld_m2["stars"][0] < _ld_m2["stars"][1], _ld_m2
assert not _ld_lc.verdict(_ld_m2), "a broken link was not a disagreement"
_ld_hero = _ld_lc.herodata()
if _ld_hero is not None:
    import glob as _ld_glob
    _ld_files = sorted(_ld_glob.glob(os.path.join(_ld_lc.MOO, "SAVE*.GAM")))
    _ld_read = 0
    for _ld_f in _ld_files:
        _ld_arr = _ld_lc.arrays_from_save(open(_ld_f, "rb").read(), _ld_hero)
        if _ld_arr is None:
            continue
        _ld_read += 1
        assert _ld_lc.verdict(_ld_lc.measure(*_ld_arr, _ld_hero)), _ld_f
    report(f"leader records measured in {_ld_read} of the player's own "
           f"saves on this disk")
else:
    report("the player's HERODATA.LBX is not on this disk — the tool was "
           "checked on the forced states only")
ok("tools/leader_check.py measures the ship and star links in both "
   "directions and refuses a broken one")
