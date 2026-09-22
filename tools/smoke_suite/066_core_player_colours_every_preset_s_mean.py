# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 066_core_player_colours_every_preset_s_mean.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (91 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 2 check(s) it holds:
#   - player colours: every preset's mean hover/owner luminance ratio is within 10 % of the original's
#   - palette.init: call sites, only main.py passes a preset, after usersettings.load()


# 10. THE HOVER RULE STAYS WITHIN 10 % OF THE ORIGINAL'S MEAN RATIO.
def _pc_rl(_c):
    _l = [_pc._linear(_v) for _v in _c[:3]]
    return 0.2126 * _l[0] + 0.7152 * _l[1] + 0.0722 * _l[2]
def _pc_ratio(_cols):
    return sum(_pc_rl(_cols["planets"][f"owner_hover_{_i}"])
               / _pc_rl(_cols["galaxy_map"][f"owner_{_i}"])
               for _i in range(8)) / 8
_pc_r0 = _pc_ratio(_pc_skin)
for _pc_n in _pc_names[1:]:
    _pc_r = _pc_ratio(_pc.apply(_pc_skin, _pc_n)[0])
    assert abs(_pc_r - _pc_r0) <= 0.10 * _pc_r0, (_pc_n, _pc_r, _pc_r0)
ok(f"player colours: every preset's mean hover/owner luminance ratio is "
   f"within 10 % of the original's {_pc_r0:.3f}")

# 11. ONLY main.App PASSES A PRESET; tools and this test never read the
#     player's file, and the user settings load before the palette.
_pc_root = os.path.dirname(SCREENS_DIR)
_pc_callers = []
for _dp, _dn, _fn in os.walk(_pc_root):
    _dn[:] = [_d for _d in _dn if _d not in (".git", "__pycache__")]
    for _f in _fn:
        if _f.endswith(".py"):
            _txt = open(os.path.join(_dp, _f), encoding="utf-8").read()
            for _line in _txt.splitlines():
                # A CALL, not a mention: the line starts with it.
                # A docstring naming palette.init(preset=...) is
                # documentation, and counting it failed this
                # check on its first run.
                if _line.lstrip().startswith("palette.init("):
                    _pc_callers.append((os.path.relpath(
                        os.path.join(_dp, _f), _pc_root), _line.strip()))
_pc_with = {_f for _f, _l in _pc_callers if "preset" in _l or "," in _l}
_pc_main = open(os.path.join(_pc_root, "main.py"), encoding="utf-8").read()
assert _pc_main.index("usersettings.load()") < _pc_main.index("palette.init("), \
    "main.App initialises the palette before the user settings are read"
assert "preset=" in _pc_main.split("palette.init(", 1)[1][:200]
for _f, _l in _pc_callers:
    if _f != "main.py" and _f not in SUITE_FILES:
        assert "preset" not in _l and "user" not in _l, (_f, _l)
ok(f"palette.init: {len(_pc_callers)} call sites, only main.py passes a "
   f"preset, after usersettings.load()")
