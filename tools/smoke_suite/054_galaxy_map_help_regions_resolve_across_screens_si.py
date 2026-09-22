# smoke-suite area: galaxy_map
#
# Part of the OrionLayer smoke suite — 054_galaxy_map_help_regions_resolve_across_screens_si.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (91 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 1 check(s) it holds:
#   - help regions resolve ( across screens, sidebar tiles its column)


# ── Right-click context help ──
# Transcribed from fields.cpp Check_Help_List_ (2916): the regions
# are walked in order, the first hit wins, and the click is
# swallowed instead of acting as Cancel. Both properties are
# asserted, plus the thing a config-driven feature always needs —
# that every region still resolves to a rect. A renamed box logs
# nothing and simply stops answering, which is invisible on
# screen and obvious to a test.
import json as _hjson
from core.helppopup import HelpPopup as _HelpPopup

_help_screens = ("main_menu", "new_game", "galaxy_map", "colony_summary")
_region_total = 0
for _name in _help_screens:
    _hp = os.path.join(SCREENS_DIR, _name, "help.json")
    assert os.path.exists(_hp), f"{_name} has no help.json"
    with open(_hp, encoding="utf-8") as _fh:
        _help_doc = _hjson.load(_fh)
    _regions = _help_doc["regions"]
    assert _regions, _name
    _ids = [r["help_id"] for r in _regions]
    assert len(_ids) == len(set(_ids)), (_name, _ids)
    # A screen-wide fallback can only ever be last: the walk stops
    # at the first hit, exactly where the original keeps its own
    # ({545, 0,0,639,479} closes New Game's list).
    for _i, _r in enumerate(_regions[:-1]):
        assert not _r.get("screen"), (_name, _i, _r["help_id"])

    d.switch_to(_name)
    _s = d.active
    _s.update(None)
    assert len(_s._help_regions) == len(_regions), _name
    for _r in _regions:
        _rect = _s.help_region_rect(_r)
        if _r.get("no_counterpart"):
            # KEPT FOR ORDER, RESOLVES TO NOTHING — and the file has
            # to say why, by id, or it is an entry that silently
            # stopped answering.
            assert _rect is None and str(_r["help_id"]) in \
                _help_doc.get("_no_counterpart", ""), (
                f"{_name} help {_r['help_id']} is marked no_counterpart "
                f"but resolves to {_rect} or is not explained in "
                f"_no_counterpart")
            continue
        assert _rect and _rect.w > 0 and _rect.h > 0, \
            (_name, _r["help_id"], _r)
        _region_total += 1

    # The popup box exists at every stored resolution, so the
    # constant fallback in helppopup.py stays a safety net rather
    # than the actual layout.
    with open(os.path.join(SCREENS_DIR, _name, "boxes.json"),
              encoding="utf-8") as _fh:
        for _res, _bl in _hjson.load(_fh).items():
            assert any(_b["name"] == "help_popup" for _b in _bl), \
                (_name, _res)
# The sidebar regions have to tile the column, not merely cover
# the readouts. MOO2's rectangles span the whole row band and
# leave 2 native pixels between consecutive entries
# (evanhelp.cpp:4); the HD sb_* boxes are sized to their content,
# so without help.json's pad_y a right click between two readouts
# opens nothing. That strip is invisible on screen — the region
# it belongs to is not drawn — so it needs a test.
#
# Asserted as the rule, against the file's own provenance
# rectangles rather than a copied constant: the HD column must
# cover at least the fraction of its span that the original
# covers of its own, the regions must not overlap (first hit
# wins, so an overlap silently shadows an entry), and none may
# leave the sidebar cutout.
d.switch_to("galaxy_map")
_gm_s = d.active
_gm_s.update(None)
with open(os.path.join(SCREENS_DIR, "galaxy_map", "help.json"),
          encoding="utf-8") as _fh:
    _sb_specs = [_r for _r in _hjson.load(_fh)["regions"]
                 if "sb_" in str(_r.get("box"))]
assert len(_sb_specs) == 6, len(_sb_specs)

# Sort the specs themselves, so spec[i], native[i] and rect[i] are
# the same row. Reading the file order would agree today and stop
# agreeing the first time somebody reorders a region.
_sb_specs.sort(key=lambda r: r["native"][1])
_nat = [_r["native"] for _r in _sb_specs]
_nat_cov = (sum(_n[3] - _n[1] for _n in _nat)
            / (_nat[-1][3] - _nat[0][1]))
_hd = [_gm_s.help_region_rect(_r) for _r in _sb_specs]
assert _hd == sorted(_hd, key=lambda r: r.top), \
    "HD sidebar rows are not in the original's top-to-bottom order"
_hd_cov = sum(_r.h for _r in _hd) / (_hd[-1].bottom - _hd[0].top)
assert _hd_cov >= _nat_cov, (
    f"sidebar help covers {_hd_cov:.1%} of its column, the original "
    f"{_nat_cov:.1%} — dead strip between readouts")
for _a, _b in zip(_hd, _hd[1:]):
    assert _b.top >= _a.bottom, (_a, _b)

# A region that fills its HD row where the original's does not
# fill its own is a deliberate deviation and has to say so —
# CLAUDE.md's rule that an HD EXTENSION is marked where it lives,
# so it cannot quietly become "how it has always been". Asserted
# as the rule rather than by naming the stardate: any future
# region that stops matching the original's proportions is caught
# the same way. The 0.9 separates 0.81 (the original's stardate,
# 17 of a 21-pixel row) from 0.97 (every readout) with room on
# both sides; it is a divider, not a tuned threshold.
_FILLS_ROW = 0.9
for _i, _spec in enumerate(_sb_specs[:-1]):
    _n, _n_next = _nat[_i], _nat[_i + 1]
    _nat_fill = (_n[3] - _n[1]) / (_n_next[1] - _n[1])
    _hd_fill = _hd[_i].h / (_hd[_i + 1].top - _hd[_i].top)
    if _nat_fill < _FILLS_ROW <= _hd_fill:
        assert _spec.get("hd_extension"), (
            f"help {_spec['help_id']} covers {_hd_fill:.0%} of its HD "
            f"row where the original covers {_nat_fill:.0%} of its "
            f"own — a deviation that is not marked hd_extension")
_cut = pygame.Rect(*_gm_s.box_rect("sidebar"))
for _r in _hd:
    assert _cut.contains(_r), (_r, _cut)
ok(f"help regions resolve ({_region_total} across "
   f"{len(_help_screens)} screens, sidebar tiles its column)")
