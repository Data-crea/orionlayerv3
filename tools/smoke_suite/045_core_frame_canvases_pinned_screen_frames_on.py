# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 045_core_frame_canvases_pinned_screen_frames_on.py.
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
#   - frame canvases pinned: screen frames, on the x canvas (decision 70)


# ── THE FRAME CANVAS IS PINNED (decision 70) ───────────────────
#
# 3840x2160 is the source canvas for every NEW or REPLACED frame
# image; the frames already in the tree keep their own size until
# something replaces them (work order 151, Data's decision).
#
# A RULE ABOUT "NEW" CANNOT BE CHECKED BY LOOKING AT WHAT IS
# ALREADY HERE, so the check holds the other half of the sentence:
# each screen frame is EITHER the size it had when the decision was
# filed, OR the canvas. Change one of these files to any third size
# and this fails — which is the exact moment the decision applies.
# Without it the entry would be an intention, which is the
# principle "a labelling rule without a check is an intention".
from PIL import Image as _fc_Image
_FRAME_CANVAS = (3840, 2160)
_fc_pinned = {
    "colony_summary": (1672, 941),
    "fleets": (1445, 811),
    "galaxy_map": (1707, 921),
    "game_menu": (1108, 1419),
    "planets": (1920, 1080),
}
_fc_seen = {}
for _fc_name in sorted(os.listdir(SCREENS_DIR)):
    _fc_png = os.path.join(SCREENS_DIR, _fc_name, "assets", "frame.png")
    if os.path.exists(_fc_png):
        _fc_seen[_fc_name] = _fc_Image.open(_fc_png).size
assert set(_fc_seen) == set(_fc_pinned), (
    "the set of screens carrying a frame.png changed: "
    f"{sorted(set(_fc_seen) ^ set(_fc_pinned))}. A NEW frame is "
    f"{_FRAME_CANVAS[0]}x{_FRAME_CANVAS[1]} (decision 70); add it "
    "to the table in this check with that size")
for _fc_name, _fc_size in sorted(_fc_seen.items()):
    assert _fc_size in (_fc_pinned[_fc_name], _FRAME_CANVAS), (
        f"screens/{_fc_name}/assets/frame.png is "
        f"{_fc_size[0]}x{_fc_size[1]}; it was "
        f"{_fc_pinned[_fc_name][0]}x{_fc_pinned[_fc_name][1]} and a "
        f"REPLACED frame is {_FRAME_CANVAS[0]}x{_FRAME_CANVAS[1]} "
        "(decision 70), never a third size")
_fc_on = sum(1 for _fc_size in _fc_seen.values()
             if _fc_size == _FRAME_CANVAS)
ok(f"frame canvases pinned: {len(_fc_seen)} screen frames, {_fc_on} "
   f"on the {_FRAME_CANVAS[0]}x{_FRAME_CANVAS[1]} canvas "
   f"(decision 70)")
