# smoke-suite area: galaxy_map
#
# Part of the OrionLayer smoke suite — 047_galaxy_map_no_box_sits_on_a_thin.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (93 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 1 check(s) it holds:
#   - no box sits on a thin_border's 1 px line: nested boxes in groups across the tree, named exceptio

#
# Work order 137 E3. `thin_border` GROUPS things (decision 34) and
# is drawn as a 1 px rounded outline — `StyleRenderer.draw_plate`,
# core/style.py:418-420, `pygame.draw.rect(..., 1,
# border_radius=max(6, int(10 * scale)))`. A box whose edge lies ON
# that line draws a second line over it, and at 1080p the two are
# one pixel apart at best.
#
# The Fleets screen had ten of them, and the cause is worth keeping:
# its groups AND its controls are both help rectangles from the same
# table (evanhelp.cpp:154-165), and the original's table gives a
# group and its first control the same left edge. It could — the
# original draws no outline there at all, only artwork. So the GROUP
# gave way and not the control (`fltgeom.GROUP_PAD`), which is
# decision 54's rule one level up: shrink the slot, never the thing
# that is transcribed.
#
# THE RULE IS TREE-WIDE, at every resolution every screen carries.
_TB_MIN_GAP = 1          # the line is 1 px; clearing it is 1 px
#: PAIRS THAT ARE NOT NESTING, each with why. Two kinds, and the
#: difference matters: the first four are boxes that are never on
#: screen together, so no second line is ever drawn; the last two
#: are real and were REPORTED RATHER THAN FIXED (work order 137 E3
#: says so in as many words) — they belong to screens this order
#: did not open.
_TB_ALLOWED = {
    ("galaxy_map", "system_box", "fleet_box"):
        "two movable boxes at one anchor; boxmodel draws one or the "
        "other, never both (screens/galaxy_map/boxmodel.py)",
    ("game_menu", "save_cancel", "load_cancel"):
        "the same rect twice, one per dialog; nodes.classify puts "
        "exactly one dialog on screen",
    ("game_menu", "load_cancel", "save_cancel"):
        "the mirror of the line above",
    ("game_menu", "confirm_panel", "warning_panel"):
        "the confirmation and the slot warning are two dialogs, "
        "never up together (decision 59)",
    ("custom_race", "race_picks_panel", "picks_header"):
        "REPORTED, NOT FIXED (137 E3): the header spans the panel "
        "flush on three sides, L0 T0 R0. Data's screen, Data's call",
    ("empire_identity", "preview_panel", "preview_header"):
        "REPORTED, NOT FIXED (137 E3): the header spans the panel "
        "flush left and right, L0 R0",
}

def _tb_skin(_b):
    _s = _b.get("style")
    return _s.get("skin") if isinstance(_s, dict) else None

_tb_bad, _tb_groups, _tb_pairs = [], 0, 0
for _tb_screen in sorted(os.listdir(SCREENS_DIR)):
    _tb_path = os.path.join(SCREENS_DIR, _tb_screen, "boxes.json")
    if not os.path.exists(_tb_path):
        continue
    _tb_file = _sjson.load(io.open(_tb_path, encoding="utf-8"))
    # `_template` ships a flat list rather than the per-resolution
    # map; it is an example and not a screen, and the rule is about
    # what a screen draws.
    if not isinstance(_tb_file, dict):
        continue
    for _tb_key, _tb_boxes in _tb_file.items():
        _tb_real = [_b for _b in _tb_boxes
                    if isinstance(_b, dict) and _b.get("rect")]
        for _tb_g in [_b for _b in _tb_real
                      if _tb_skin(_b) == "thin_border"]:
            _gx, _gy, _gw, _gh = _tb_g["rect"]
            _tb_groups += 1
            for _tb_o in _tb_real:
                if _tb_o is _tb_g:
                    continue
                _ox, _oy, _ow, _oh = _tb_o["rect"]
                if not (_ox >= _gx and _oy >= _gy
                        and _ox + _ow <= _gx + _gw
                        and _oy + _oh <= _gy + _gh):
                    continue
                _tb_pairs += 1
                _gap = min(_ox - _gx, _oy - _gy,
                           (_gx + _gw) - (_ox + _ow),
                           (_gy + _gh) - (_oy + _oh))
                if _gap >= _TB_MIN_GAP:
                    continue
                if (_tb_screen, _tb_g["name"],
                        _tb_o["name"]) in _TB_ALLOWED:
                    continue
                _tb_bad.append(
                    f"{_tb_screen}/{_tb_key}: {_tb_o['name']} clears "
                    f"{_tb_g['name']}'s rim by {_gap} px")
assert not _tb_bad, (
    f"a box sits on a thin_border's own 1 px line: {_tb_bad}. Either "
    f"grow the GROUP (fltgeom.GROUP_PAD is that move) or put the "
    f"pair in _TB_ALLOWED with the reason the two are never drawn "
    f"together")
# The exception list must not rot into a silence: every entry has to
# name a pair that EXISTS.
_tb_names = set()
for _tb_s in os.listdir(SCREENS_DIR):
    _tb_p = os.path.join(SCREENS_DIR, _tb_s, "boxes.json")
    if not os.path.exists(_tb_p):
        continue
    _tb_f = _sjson.load(io.open(_tb_p, encoding="utf-8"))
    if not isinstance(_tb_f, dict):
        continue
    for _tb_bs in _tb_f.values():
        _tb_ns = [_b["name"] for _b in _tb_bs
                  if isinstance(_b, dict) and _b.get("name")]
        _tb_names |= {(_tb_s, _g, _o)
                      for _g in _tb_ns for _o in _tb_ns}
_tb_stale = sorted(_k for _k in _TB_ALLOWED if _k not in _tb_names)
assert not _tb_stale, (
    f"_TB_ALLOWED names pairs that are not in any boxes.json: "
    f"{_tb_stale}")
assert _tb_groups >= 25 and _tb_pairs >= 25, (
    f"only {_tb_groups} thin_border group(s) and {_tb_pairs} nested "
    f"box(es) were measured; a rule that examines almost nothing "
    f"passes for the wrong reason")
ok(f"no box sits on a thin_border's 1 px line: {_tb_pairs} nested "
   f"boxes in {_tb_groups} groups across the tree, "
   f"{len(_TB_ALLOWED)} named exceptions")
