# smoke-suite area: fleets
#
# Part of the OrionLayer smoke suite — 087_fleets_relocation_lines_offset_205_agrees_wit.py.
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
#   - relocation lines: offset 205 agrees with orion2.h's field order and the spec's twelve known offs
#   - the Fleets screen's own artwork: never tracked and gitignored, absent is a state that answers No


# ── THE FLEETS SCREEN'S OWN ARTWORK ─────────────────────────────
#
# Work order 142 D1. The game's own pixels are NEVER in this tree
# (decisions 40 and 42), so the state a fresh clone is in is the
# one without them — and that is exactly the state that rots
# unnoticed, because the session that writes the code has the
# files. Both states are therefore FORCED here, neither is waited
# for, and the checks below run identically on a machine that has
# never seen a Master of Orion 2 installation.
from screens.fleets import fltart as _fa
import screens.fleets.fltdraw as _fd

# 1. THE EXTRACTED FILES ARE NOT IN THE TREE, BY ANY NAME. The
#    extractor's own output directory is the obvious one; the loop
#    after it is the real check, because a second copy under
#    another name is exactly how "never committed" has been broken
#    elsewhere in this project's history.
_fa_out = os.path.relpath(_fa.GAMEDATA, _root0 := os.path.dirname(SCREENS_DIR))
_sp0 = __import__("subprocess")
_fa_tracked = _sp0.run(["git", "ls-files", "-z"], cwd=_root0,
                       capture_output=True, text=True)
_fa_names = [n for n in _fa_tracked.stdout.split("\0") if n]
assert _fa_names, "git ls-files returned nothing; the check is blind"
_fa_bad = [n for n in _fa_names
           if n.startswith(_fa_out.replace(os.sep, "/") + "/")
           or os.path.basename(n).lower() in
           ("ships.lbx", "fleet.lbx", "fonts.lbx", "palette.bin")]
assert not _fa_bad, (
    "extracted game data is TRACKED in this repository: "
    f"{_fa_bad[:5]} — decisions 40 and 42, and the work order's "
    "'no extracted game data in the commit'")

# 2. AND .gitignore SAYS SO, so the next `git add -A` cannot make
#    a liar of check 1. An exclusion that merely happens to hold
#    is not a rule.
with open(os.path.join(_root0, ".gitignore"), encoding="utf-8") as _fh:
    _fa_ign = _fh.read()
assert "screens/fleets/assets/gamedata" in _fa_ign, (
    ".gitignore does not cover the Fleets artwork output "
    "(screens/fleets/assets/gamedata) — check 1 would then pass "
    "only until somebody runs the extractor and commits")

# 3. THE ABSENT STATE IS A STATE, NOT AN ERROR. Forced by pointing
#    the loader at a directory that cannot exist.
_fa_none = _fa.FleetArt(os.path.join(_root0, "no-such-gamedata-dir"))
assert _fa_none.available is False
assert "fleet_art_extract" in _fa_none.reason, _fa_none.reason
for _call in (lambda a: a.ship(0, 0), lambda a: a.star(0),
              lambda a: a.selected_box(), lambda a: a.scanned_box(),
              lambda a: a.background(), lambda a: a.plate(347, 53),
              lambda a: a.radio("support", True)):
    assert _call(_fa_none) is None, "an absent file must answer None"
assert _fa_none.ship_ramp(0) == {}, "no ramp without the files"

# 4. A MANIFEST FROM AN OLDER EXTRACTOR IS REFUSED rather than
#    decoded, which is decision 38's own reason for the version.
import tempfile as _fa_tf
with _fa_tf.TemporaryDirectory() as _fa_tmp:
    with open(os.path.join(_fa_tmp, "manifest.json"), "w",
              encoding="utf-8") as _fh:
        _fh.write('{"format": %d}' % (_fa.FORMAT_VERSION + 1))
    _fa_old = _fa.FleetArt(_fa_tmp)
    assert _fa_old.available is False
    assert str(_fa.FORMAT_VERSION) in _fa_old.reason, _fa_old.reason

# 5. THE CENTRING IS THE ORIGINAL'S, INCLUDING ITS ROUNDING.
#    `0x39 - width` halved TOWARD ZERO (flt1.cpp:81-85), then + 1
#    and + 2. A sprite wider than the cell is the case that tells
#    Python's floor division apart from C's shift, so it is here.
assert _fa.NATIVE_CELL == 0x39, _fa.NATIVE_CELL
assert _fa.cell_offset(52, 48) == (3, 6), _fa.cell_offset(52, 48)
assert _fa.cell_offset(57, 57) == (1, 2)
assert _fa.cell_offset(59, 61) == (0, 0), _fa.cell_offset(59, 61)

# 6. THE MAGNIFICATION IS AN INTEGER, AND NOTHING ELSE. This is the
#    check that reads the HD EXTENSION marking in `fltart`.
_fa_src = open(os.path.join(SCREENS_DIR, "fleets", "fltart.py"),
               encoding="utf-8").read()
assert "HD EXTENSION" in _fa_src, "the deviation lost its marking"
_fa_tree = __import__("ast").parse(_fa_src)
_fa_scale = [n for n in __import__("ast").walk(_fa_tree)
             if isinstance(n, __import__("ast").Attribute)
             and n.attr in ("smoothscale", "rotozoom")]
assert not _fa_scale, (
    "fltart resamples the game's pixels smoothly; the deviation "
    "decision 28 allows is an INTEGER factor, nothing softer")
assert "int(step)" in _fa_src, (
    "fltart.magnified must force the factor to an integer")

# 7. THE CELL SEAT IS AN INTEGER MULTIPLE OF THE NATIVE CELL,
#    centred — decision 54, shrink the slot. Checked as a RULE over
#    every slot at every resolution, not as one measured example.
for _fa_w, _fa_h in ((1920, 1080), (2560, 1440), (3840, 2160)):
    _fa_rect = pygame.Rect(0, 0, _fa_w // 15, _fa_h // 8)
    _fa_seat, _fa_step = _fd.cell_seat(_fa_rect)
    assert _fa_seat.width == _fa_seat.height == _fa.NATIVE_CELL * _fa_step
    assert _fa_seat.width <= _fa_rect.width
    assert _fa_seat.height <= _fa_rect.height
    assert abs((_fa_seat.x - _fa_rect.x)
               - (_fa_rect.right - _fa_seat.right)) <= 1
    assert _fa.magnified(pygame.Surface((4, 4)), _fa_step).get_width() \
        == 4 * _fa_step

# 8. A PLACEHOLDER IS NOT A SHIP. Slot 49 of every colour set is a
#    2x1 palette carrier (ken.cpp:71-77) and the monster set is
#    full of 1x1 stubs; drawing one would put a stray pixel in a
#    cell. The threshold is checked against the sizes that exist.
assert _fa.MIN_PICTURE > 2, _fa.MIN_PICTURE
assert _fa.MIN_PICTURE <= 48, "a real 52x48 picture must pass"
assert _fa.SHIP_PALETTE_SLOT == 49 and _fa.SHIP_STRIDE == 50
assert _fa.MAX_PLAYERS == 8, "consts.h:7"
assert set(_fa.SPECIAL_PALETTE) == {8, 9, 10, 11, 12, 13, 14}, (
    "the owners ken.cpp:83-102 switches on")

# 9. THE FILTER RADIOS MAP TO THE FLTS FIELDS THE ENGINE POINTS AT
#    (flt1.cpp:1255-1256). A radio whose state came from somewhere
#    else would light for the wrong reason.
assert _fd.RADIOS == {"btn_support": ("support", "support_filter"),
                      "btn_combat": ("combat", "combat_filter")}

# ── RELOCATION LINES: ONE FACT, TWO LOOKS ──────────────────────
#
# Work order 144 Part 2. The Fleets minimap and the galaxy map draw
# relocation lines from the SAME data and with DIFFERENT colours,
# and the original is what makes them differ. The checks below hold
# the parts that could drift apart silently.
from core.structs import star as _rl_star
import screens.galaxy_map.maplines as _rl_ml
import screens.fleets.fltdraw as _rl_fd

# 1. THE OFFSET IS THE HEADER'S, and the arithmetic that produced
#    it still reproduces every offset this spec already held. If a
#    future edit moves a field, this fails before the lines go to
#    the wrong stars.
_rl_MP, _rl_MS = 8, 1024
_rl_fields = [
    ("name", 15), ("x", 2), ("y", 2), ("size", 1), ("owner", 1),
    ("pict_type", 1), ("spectral_class", 1),
    ("last_planet_selected", _rl_MP), ("black_hole_blocks", (_rl_MS + 7) // 8),
    ("system_special", 1), ("wormhole_star_id", 2), ("blockaded", 1),
    ("blockaded_by", _rl_MP), ("visited", 1), ("just_visited", 1),
    ("ignore_colony_ships", 1), ("ignore_combat_ships", 1),
    ("colonize_player", 1), ("has_colony", 1),
    ("has_warp_field_interdictor", 1), ("next_wfi_in_list", 2),
    ("has_tachyon", 1), ("has_subspace", 1), ("has_stargate", 1),
    ("has_jumpgate", 1), ("has_artemis_net", 1),
    ("has_dimensional_portal", 1), ("is_stagepoint", 1),
    ("officer_index", _rl_MP), ("planet_index", 10),
    ("relocate_ship_to", 2 * _rl_MP), ("twinkling1", 1),
    ("twinkling2", 1), ("not_used3", 1), ("surrender_to", _rl_MP),
    ("in_nebula", 1), ("artifacts_gave_app", 1)]
_rl_off, _rl_pos = {}, 0
for _rl_n, _rl_s in _rl_fields:
    _rl_off[_rl_n] = _rl_pos
    _rl_pos += _rl_s
assert _rl_pos == _rl_star.SIZE, (_rl_pos, _rl_star.SIZE)
_rl_spec = {n: o for n, o, _k in _rl_star.SPEC.fields}
for _rl_n, _rl_o in _rl_spec.items():
    if _rl_n in _rl_off:
        assert _rl_off[_rl_n] == _rl_o, (
            f"s_star_data layout moved: {_rl_n} is {_rl_o} in the spec "
            f"and {_rl_off[_rl_n]} in orion2.h's field order")
assert _rl_star.RELOCATE_OFFSET == _rl_off["relocate_ship_to"] == 205
assert _rl_star.PLANET_INDEX_OFFSET + 10 == _rl_star.RELOCATE_OFFSET

# 2. -1 IS "NO RELOCATION" AND MUST NOT REACH A CALLER as a star
#    index: `Star_Has_Relocation_` is exactly `!= -1`
#    (haccess.cpp:114), and -1 would index the last star in Python.
_rl_raw = bytearray(_rl_star.SIZE)
struct.pack_into("<h", _rl_raw, 205 + 2 * 3, 42)
struct.pack_into("<h", _rl_raw, 205 + 2 * 0, -1)
_rl_view = _rl_star.parse(bytes(_rl_raw))
assert _rl_star.relocation_target(_rl_view, 3) == 42
assert _rl_star.relocation_target(_rl_view, 0) is None
assert _rl_star.relocation_target(_rl_view, 8) is None, "out of range"

# 3. ONE FACT, NOT TWO. Both screens' lines must come from
#    `maplines.relocation_pairs`; a second walk over the stars
#    testing offset 205 is the copy decision 68 exists to stop.
_rl_fd_src = io.open(os.path.join(SCREENS_DIR, "fleets", "fltdraw.py"),
                     encoding="utf-8").read()
# Read the CODE, not the prose: `draw_relocation_lines`' docstring
# explains that the gate is the galaxy map's, so a plain grep finds
# the word and calls it a use. Comments and string literals are
# stripped before the question is asked.
def _rl_code_only(src):
    import io as _io, tokenize as _tk
    out = []
    for tok in _tk.generate_tokens(_io.StringIO(src).readline):
        if tok.type in (_tk.COMMENT, _tk.STRING):
            continue
        out.append(tok.string)
    return " ".join(out)
_rl_fd_code = _rl_code_only(_rl_fd_src)
assert "maplines.relocation_pairs" in _rl_fd_src, (
    "the Fleets minimap no longer takes its relocations from "
    "maplines.relocation_pairs")
assert "RELOCATE_OFFSET" not in _rl_fd_code and "205" not in _rl_fd_code, (
    "fltdraw reaches for the relocation offset itself; the fact "
    "belongs to core/structs/star through maplines")
# and it must draw through the one line primitive (decision 68)
assert "maplines.stroke" in _rl_fd_src, (
    "the relocation lines no longer go through maplines.stroke")

# 4. THE MINIMAP'S RAMP IS THE GREY ONE. The Fleets mockup showed
#    GREEN lines and the mockup is not evidence: palette 6..10 of
#    FONTS.LBX 9 is grey, and the green table (0x6E,0x6F,0x70) is
#    the GALAXY MAP's, on a different screen. A green ramp here
#    would mean the mockup had been believed over the source.
for _rl_c in _rl_fd.RELOCATION_RAMP:
    _rl_r, _rl_g, _rl_b = _rl_c[:3]
    assert abs(_rl_r - _rl_g) <= 4 and _rl_b >= _rl_g, (
        f"the relocation ramp entry {_rl_c} is not the grey-blue of "
        f"palette 6..10; flt1.cpp:1460-1467")
    assert not (_rl_g > _rl_r + 20), "green ramp — that is the mockup, not the source"
assert len(_rl_fd.RELOCATION_RAMP) == 8, "s_colors carries eight"

# 5. THE MINIMAP IS NOT GATED BY THE GALAXY MAP'S SETTING, and the
#    galaxy map's omission still says why it is still omitted.
assert "show_relocation_lines" not in _rl_fd_code, (
    "the minimap consults the galaxy map's setting; flt1.cpp:1480 "
    "has no such gate")
_rl_ml_src = io.open(os.path.join(SCREENS_DIR, "galaxy_map",
                                  "maplines.py"), encoding="utf-8").read()
assert "show_relocation_lines" in _rl_ml_src and \
    "144-parked-for-data" in _rl_ml_src, (
        "the galaxy map's relocation omission lost the half of its "
        "reason that still stands")

ok("relocation lines: offset 205 agrees with orion2.h's field order "
   "and the spec's twelve known offsets, -1 never reaches a caller, "
   "both screens share one fact and one stroke, the minimap's ramp "
   "is the source's grey and not the mockup's green, and the galaxy "
   "map's remaining gate is still recorded")

ok("the Fleets screen's own artwork: never tracked and gitignored, "
   "absent is a state that answers None everywhere, an older "
   "format is refused, the centring keeps the original's rounding, "
   "the magnification is integer-only and the seat an integer "
   "multiple of the 0x39 cell, placeholders are not ships, and the "
   "radios read the FLTS fields the engine points at")
