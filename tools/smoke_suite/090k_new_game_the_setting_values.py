# smoke-suite area: new_game
#
# Part of the OrionLayer smoke suite — 090k_new_game_the_setting_values.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/, in file-name order and in ONE
# namespace. Do not import this file; it is not a module.
#
# Work order 179, part 4: the HD New Game screen offered a fourth tech
# level ("Post Warp", with its own picture) that the original does not
# have — `layout.json` mapped a value 3 the engine never sends, since the
# first v3 commit. Removed; and the rule is asserted for every category,
# not for the one instance.
#
# The 1 check(s) it holds:
#   - New Game: every setting offers exactly the original's values, tech level Pre Warp / Average / Advanced


import json as _ng_json

_ng_dir = os.path.join(SCREENS_DIR, "new_game")
with open(os.path.join(_ng_dir, "layout.json"), encoding="utf-8") as _fh:
    _ng_cfg = _ng_json.load(_fh)

# TRANSCRIPTION — the value count of each of the original's click-through
# buttons, `FAKEBUTS::Add_Click_Thru_Field_(…, strings, COUNT, &variable …)`
# (newgame.cpp:265-281), with the counts from orion2_consts.h:173-189 and
# consts.h:7. The engine cycles each variable through 0..COUNT-1 and sends
# it unchanged (ext_api.cpp:174-181), so a key outside that range is a
# setting the player can never reach, and one missing is a setting HD
# cannot show.
_NG_COUNTS = {
    "difficulty": 5,     # GAME_DIFFICULTY_COUNT, newgame.cpp:265
    "galaxy_size": 5,    # GALAXY_SIZE_COUNT, newgame.cpp:269
    "galaxy_age": 3,     # GALAXY_AGE_COUNT, newgame.cpp:273
    "players": 7,        # MAX_PLAYERS - 1, newgame.cpp:277
    "tech_level": 3,     # _civ_button_strings, 3 — newgame.cpp:281
}
_ng_cats = _ng_cfg["categories"]
assert set(_ng_cats) == set(_NG_COUNTS), sorted(_ng_cats)
for _ng_cat, _ng_n in _NG_COUNTS.items():
    _ng_keys = sorted(_ng_cats[_ng_cat]["values"], key=int)
    assert _ng_keys == [str(_k) for _k in range(_ng_n)], (
        f"new game {_ng_cat}: values {_ng_keys}, the original offers "
        f"0..{_ng_n - 1}")
    for _ng_v in _ng_cats[_ng_cat]["values"].values():
        assert os.path.exists(os.path.join(
            _ng_dir, "assets", _ng_cat, _ng_v["image"] + ".png")), _ng_v

# The tech levels in the original's order: `_civ_button_strings[0..2]` =
# E_Strings 0x1ad, 0xbe, 0xa9 (newgame.cpp:372-374), which read "Pre Warp",
# "Average", "Advanced" in the English ESTRINGS.LBX — and the picture per
# value is `_tech_level_anims[_civ_button_variable]` (:236), same index.
assert [_ng_cats["tech_level"]["values"][str(_k)]["label"]
        for _k in range(3)] == ["Pre Warp", "Average", "Advanced"]
assert [_ng_cats["tech_level"]["values"][str(_k)]["image"]
        for _k in range(3)] == ["pre_warp", "average", "advanced"]
# No picture left in the tree for a value that does not exist.
_ng_used = {_v["image"] for _v in _ng_cats["tech_level"]["values"].values()}
_ng_files = {os.path.splitext(_f)[0].rstrip("1") for _f in os.listdir(
    os.path.join(_ng_dir, "assets", "tech_level")) if _f.endswith(".png")}
assert _ng_files <= _ng_used, sorted(_ng_files - _ng_used)
ok("New Game: every setting offers exactly the original's values (counts "
   "from newgame.cpp's click-through buttons); tech level is Pre Warp / "
   "Average / Advanced = 0 / 1 / 2, no fourth and no picture for one")
