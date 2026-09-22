# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 012_core_struct_specs_nebula_planet_player_s.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (93 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 2 check(s) it holds:
#   - struct specs (nebula, planet, player; s_colony promoted, pop masks, quarantine contract, max-pop
#   - struct_probe pop-nibble report (owner match, scatter, sentinels, 10-13 vs >=14)


# ── Struct specs promoted from unverified.py ──
from core.structs import nebula as _neb, planet as _pln
n = _neb.parse(bytes([0x76, 0x01, 0xAA, 0x00, 0x01]))
assert (n.x, n.y, n.type) == (374, 170, 1)
p = _pln.parse(_s.pack("<hh", 7, 3) + bytes(14))
assert (p.colony_index, p.star_index) == (7, 3)
pv = pl.parse(bytes(PLAYER_SIZE))
assert len(pl.contacts(pv)) == 8 and len(pl.traits(pv)) == 31

# ── unverified.py's contract, asserted rather than trusted ──
# The file exists to quarantine specs that have ONE source. A
# spec promoted by flipping the flag in place, without moving to
# its own module with the evidence in the docstring, would leave
# no trace anywhere — so the flag is checked here for every spec
# the module exposes, not for a named list of them.
from core.structs import Spec as _Spec
from core.structs import unverified as _unv
_quarantined = [v for v in vars(_unv).values()
                if isinstance(v, _Spec)]
assert _quarantined, "unverified.py exposes no specs at all"
for _sp in _quarantined:
    assert not _sp.verified, (
        f"{_sp.name} is marked verified inside unverified.py — "
        f"promotion means moving it to its own module with the "
        f"evidence, not flipping the flag here")

# ── A spec must tile its struct ──
# Asserted as the rule over every spec in the tree that claims a
# size, not as a list of s_colony's 50 offsets: a field added,
# removed or mistyped shifts the chain and is caught without
# anybody updating this test. s_colony is packed with no padding
# (proved by compiling the header, doc/s_colony_offsets.md), so
# for it the chain must close exactly on 361.
from core.structs import colony as _col
_colony = _col.SPEC
assert _colony.verified, "s_colony was promoted; the flag must say so"
assert _colony.size == 361 and len(_colony.fields) == 50, \
    (_colony.size, len(_colony.fields))
_end = 0
for _name, _off, _kind in _colony.fields:
    assert _off == _end, (
        f"s_colony: {_name} starts at {_off}, previous field "
        f"ended at {_end} — the spec has a gap or an overlap")
    _end = _off + _Spec.kind_width(_kind)
assert _end == _colony.size, \
    f"s_colony fields end at {_end}, spec size is {_colony.size}"
_cv = _colony.parse(bytes(_colony.size))
assert len(_cv.pop) == 42 and len(_cv.buildings) == 49, \
    (len(_cv.pop), len(_cv.buildings))

# ── The pop word's masks must not overlap ──
# Bits inside a member are NOT fixed by offsetof (decision 23's
# addition): they are a transcription of pop.h, so the one thing
# checkable without live data is that the transcription is at
# least self-consistent. Two masks sharing a bit would make one
# field silently corrupt the other's reads.
_masks = {n: v for n, v in vars(_col).items()
          if n.startswith("POP_MASK_")}
assert len(_masks) == 5, sorted(_masks)
_seen = 0
for _n, _m in sorted(_masks.items()):
    assert _m and not (_m & _seen), \
        f"{_n} = {_m:#x} overlaps a mask already claimed"
    _seen |= _m
# The profession field must be wide enough for its own maximum,
# and pop.h defines no fourth profession.
assert _col.POP_PROF_MAX <= (_col.POP_MASK_PROF >> 7), \
    "POP_MASK_PROF cannot hold POP_PROF_MAX"
assert _col.pop_prof(_col.POP_MASK_PROF) == 3, "prof shift is wrong"
assert _col.pop_player_index(_col.POP_NATIVE) == 9
# The nibble is a PLAYER index, not a race: pop.h:8 names it
# MASK_RACE, but Get_Effective_Pop_Player_ (colony.cpp:1257)
# returns it as a player and maps only 8 and 9 to the colony
# owner, after which the race is a SECOND lookup
# (MOX::_player[idx].race, colony.cpp:1275). The wrong name
# must not come back into the spec — asserted here because a
# rename that reads plausibly is exactly what a later session
# would undo.
assert not hasattr(_col, "pop_race"), \
    "pop_race is back — the nibble is a player index"
assert not hasattr(_col, "POP_MASK_RACE"), \
    "POP_MASK_RACE is back — see colony.cpp:1257"
assert _col.pop_effective_player(_col.POP_ANDROID, 5) == 5
assert _col.pop_effective_player(_col.POP_NATIVE, 5) == 5
assert _col.pop_effective_player(3, 5) == 3
# ── The max-population base table never travels alone ──
# orion2re's _planet_max_population[] (mox.cpp:796) is the BASE
# of a computation, not the answer: the climate factor and the
# immunity bonus halve it on Ixion II (10 -> 5), and the colony
# list's bar length is meant to be proportional to the real
# maximum. Asserted as the rule rather than by reimplementing the
# formula and checking it against itself: any file that carries
# the size table must also carry the climate factors, so the base
# cannot be transcribed on its own and quietly used as a maximum.
# Not vacuous — planet.py carries both today and is what this
# check measures.
_base_re = re.compile(r"5\s*,\s*10\s*,\s*15\s*,\s*20\s*,\s*25")
_fac_re = re.compile(r"40\s*,\s*60\s*,\s*80\s*,\s*100")
_root_pm = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_lonely, _seen_base = [], 0
for _dir, _subs, _files in os.walk(_root_pm):
    if "__pycache__" in _dir or os.sep + ".git" in _dir:
        continue
    for _f in _files:
        if not _f.endswith(".py"):
            continue
        _fp = os.path.join(_dir, _f)
        with open(_fp, encoding="utf-8", errors="replace") as _fh:
            _txt = _fh.read()
        if not _base_re.search(_txt):
            continue
        _seen_base += 1
        if not _fac_re.search(_txt):
            _lonely.append(os.path.relpath(_fp, _root_pm))
assert not _lonely, (
    "the planet max-population size table appears without the "
    "climate factors in: " + ", ".join(_lonely) + " — that base "
    "is not a maximum (colcalc.cpp:896)")
assert _seen_base, \
    "nothing in the tree carries the max-population base table any more"

ok("struct specs (nebula, planet, player; s_colony promoted, "
   "pop masks, quarantine contract, max-pop base table)")

# ── struct_probe's pop-nibble report ──
# The only check in this file for a tool that CANNOT run here: it
# needs a live orion2re. So its classification is exercised on
# synthetic records instead, which is the whole of what could
# silently rot — three separate misclassifications were found by
# hand while it was being written, and each one read plausibly.
#
# Behaviour, not wording. The strings are for a person; what must
# not drift is which pops land in which bucket.
import importlib.util as _spu
_sp_spec = _spu.spec_from_file_location(
    "_probe_struct_probe",
    os.path.join(os.path.dirname(SCREENS_DIR), "tools",
                 "struct_probe.py"))
_sp = _spu.module_from_spec(_sp_spec)
_sp_spec.loader.exec_module(_sp)

def _mk_col(owner, nibbles):
    b = bytearray(_col.SIZE)
    b[0] = owner & 0xFF
    b[10] = len(nibbles)
    for _i, _nib in enumerate(nibbles):
        b[12 + 4 * _i:16 + 4 * _i] = _s.pack(
            "<I", (_i % 3) << 7 | _nib | _col.POP_MASK_ASSIGNED)
    return bytes(b)

# The reference save's shape: several owners, no androids. The
# prediction is answerable precisely because the owners differ.
_rep = _sp.pop_nibble_report(
    [_mk_col(0, [0] * 6), _mk_col(3, [3] * 4), _mk_col(5, [5] * 9)],
    _col.SPEC)
assert not _rep["mismatches"] and _rep["distinct_owners"] == [0, 3, 5], _rep
assert _rep["live_pops"] == 19 and not _rep["sentinels"], _rep
assert _rep["dist"][5] == 9 and _rep["tail"][0] == 3 * 42 - 19, _rep

# A wrong mask does not fail cleanly, it SCATTERS — that spread is
# the tell the report exists to show, so a run that produced one
# value per colony would be a different fault entirely.
_scatter = _sp.pop_nibble_report(
    [_mk_col(0, [1, 4, 10, 2]), _mk_col(3, [11, 6, 2])], _col.SPEC)
assert len(_scatter["mismatches"]) == 5, _scatter["mismatches"]
assert len(_scatter["dist"]) >= 6, _scatter["dist"]

# Androids and natives are NOT prediction failures. They resolve
# to the colony's owner (colony.cpp:1261), so they CONFIRM the
# player-index reading — counting them as mismatches made the one
# save that can settle the sentinels report itself as a
# refutation, which is how this check earned its place.
_andro = _sp.pop_nibble_report(
    [_mk_col(0, [0, _col.POP_ANDROID, _col.POP_NATIVE]),
     _mk_col(2, [2, 2])], _col.SPEC)
assert not _andro["mismatches"], _andro["mismatches"]
assert len(_andro["sentinels"]) == 2, _andro["sentinels"]

# 10..13 and >= 14 are different findings: the second has a branch
# in the source (colony.cpp:2129), the first has none that was
# found, so only the first is evidence against the mask.
_above = _sp.pop_nibble_report(
    [_mk_col(0, [0, 11, 14, 15])], _col.SPEC)
assert [n for _c, _p, n in _above["out_of_range"]] == [11], _above
assert sorted(n for _c, _p, n in _above["direct_race"]) == [14, 15], _above
assert not _above["mismatches"], _above["mismatches"]

# A save whose colonies share one owner cannot decide anything:
# "nibble == owner" and "nibble == 0" are then the same sentence.
_one = _sp.pop_nibble_report([_mk_col(0, [0] * 4)], _col.SPEC)
assert _one["distinct_owners"] == [0] and not _one["mismatches"], _one
ok("struct_probe pop-nibble report (owner match, scatter, sentinels, "
   "10-13 vs >=14)")
