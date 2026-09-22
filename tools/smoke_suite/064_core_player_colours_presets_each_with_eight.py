# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 064_core_player_colours_presets_each_with_eight.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (90 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 3 check(s) it holds:
#   - player colours: presets, each with eight owner, ship, hover and banner entries
#   - player colours: every colour-blind preset keeps dE >= under a deuteranopia simulation (Vienot 19
#   - player colours: an indistinct user table warns and still applies; an unknown preset is the origi


# ── Player-colour presets (fundament 63, an HD EXTENSION) ──
import copy as _pc_copy
from core import playercolors as _pc
_pc_skin = _pc_copy.deepcopy(colors)

# 6. EVERY SHIPPED PRESET HAS EIGHT ENTRIES IN EACH OF THE FOUR TABLES.
_pc_names = _pc.names(_pc_skin)
assert _pc_names[0] == "original" and "okabe_ito" in _pc_names, _pc_names
for _pc_n in _pc_names:
    _pc_out, _pc_act = _pc.apply(_pc_skin, _pc_n)
    assert _pc_act == _pc_n, (_pc_n, _pc_act)
    assert all(len(_pc_out["galaxy_map"].get(f"{_k}_{_i}", [])) == 3
               for _k in ("owner", "ship") for _i in range(8)), _pc_n
    assert all(len(_pc_out["planets"].get(f"owner_hover_{_i}", [])) == 3
               for _i in range(8)), _pc_n
    for _sec in ("banner", "banner_hd"):
        assert len([_c for _c in _pc_out[_sec] if not _c.startswith("_")]) \
            == 8, (_pc_n, _sec)
# THE MARKING: the presets are an HD EXTENSION, and it is said where
# the code is (fundament 63).
assert "HD EXTENSION" in (_pc.__doc__ or ""), "playercolors lost its marking"
assert "HD EXTENSION" in (palette.init.__doc__ or ""), \
    "palette.init lost its marking"
ok(f"player colours: {len(_pc_names)} presets, each with eight owner, "
   f"ship, hover and banner entries")

# 7. THE COLOUR-BLIND PRESETS STAY APART FOR A DEUTERANOPE; the
#    original is reported, not held to it (it is why the preset exists).
_pc_limit = _pc_skin["player_presets"]["deuteranopia_min_delta_e"]
for _pc_n in _pc_names[1:]:
    if not _pc_skin["player_presets"][_pc_n].get("colour_blind"):
        continue
    _pc_d, _pc_a, _pc_b = _pc.deuteranopia_min(_pc.base(_pc_skin, _pc_n))
    assert _pc_d >= _pc_limit, (
        f"{_pc_n}: {_pc.ORDER[_pc_a]} and {_pc.ORDER[_pc_b]} are dE "
        f"{_pc_d:.1f} apart for a deuteranope, the presets keep {_pc_limit}")
_pc_od = _pc.deuteranopia_min(_pc.base(_pc_skin, "original"))
report(f"deuteranopia, smallest dE76: original {_pc_od[0]:.1f} "
       f"({_pc.ORDER[_pc_od[1]]}/{_pc.ORDER[_pc_od[2]]}), okabe_ito "
       f"{_pc.deuteranopia_min(_pc.base(_pc_skin, 'okabe_ito'))[0]:.1f}")
ok(f"player colours: every colour-blind preset keeps dE >= {_pc_limit} "
   f"under a deuteranopia simulation (Vienot 1999)")

# 8. THE PLAYER'S OWN TABLE IS CHECKED AT LOAD AS A WARNING, NEVER AN
#    ABORT; a bad table or an unknown preset falls back to the original.
class _PcCatch(logging.Handler if "logging" in globals() else
               __import__("logging").Handler):
    def __init__(self):
        super().__init__()
        self.lines = []
    def emit(self, record):
        self.lines.append(record.getMessage())
_pc_catch = _PcCatch()
__import__("logging").getLogger("playercolors").addHandler(_pc_catch)
try:
    _pc_bad = [(200, 0, 0)] * 2 + [(0, 0, 200)] * 6
    _pc_out, _pc_act = _pc.apply(_pc_skin, "okabe_ito", _pc_bad)
    assert _pc_act == "okabe_ito" and any("deuteranope" in _l
                                          for _l in _pc_catch.lines)
    assert _pc_out["galaxy_map"]["owner_0"] == [200, 0, 0]
    _pc_same, _pc_act = _pc.apply(_pc_skin, "no_such_preset")
    assert _pc_act == "original" and _pc_same is _pc_skin
    assert _pc.apply(_pc_skin, "original")[0] is _pc_skin
finally:
    __import__("logging").getLogger("playercolors").removeHandler(_pc_catch)
ok("player colours: an indistinct user table warns and still applies; an "
   "unknown preset is the original; original leaves the skin untouched")
