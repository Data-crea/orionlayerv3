# smoke-suite area: galaxy_map
#
# Part of the OrionLayer smoke suite — 060_galaxy_map_help_popup_sits_inside_the_galaxy.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (90 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 1 check(s) it holds:
#   - help popup sits inside the galaxy map cutout


# On the galaxy map the popup belongs inside the map cutout, not
# centred on the window: the sidebar owns the right edge and the
# cockpit frame owns the rim, so a window-centred box sits off to
# one side and runs under the sidebar. Containment is the rule
# worth asserting rather than the exact centre — the box is
# F5-movable by design, and a nudge is not a regression while
# sliding under the frame is.
with open(os.path.join(SCREENS_DIR, "galaxy_map", "boxes.json"),
          encoding="utf-8") as _fh:
    for _res, _bl in _hjson.load(_fh).items():
        _by = {b["name"]: b["rect"] for b in _bl}
        _area = _by["map_area"]
        _pop_r = _by["help_popup"]
        assert (_pop_r[0] >= _area[0]
                and _pop_r[1] >= _area[1]
                and _pop_r[0] + _pop_r[2] <= _area[0] + _area[2]
                and _pop_r[1] + _pop_r[3] <= _area[1] + _area[3]), \
            (_res, _pop_r, _area)
ok("help popup sits inside the galaxy map cutout")
