# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 006d_core_background_and_mod_folder.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/, in file-name order and in ONE
# namespace. Do not import this file; it is not a module.
#
# Work order 173, decision 72: Data's universal background behind every
# screen, and the player's mod folder outside the tree. Core, because
# every screen stands on the one and resolves through the other.
#
# The 7 check(s) it holds:
#   - background covers the window at every size: no distortion, no strip, one copy per size
#   - mod folder: per-screen > universal > default, file by file
#   - mod folder: a partial style.json overrides only its keys
#   - mod folder: a broken, wrong or odd-sized file falls back and no screen breaks
#   - mod folder: switched off it is not read; colour.json is the default frame colour
#   - mod template: the player's starting points hold no MOO2 file
#   - text directly on the universal background keeps its contrast


import json as _um_json
import shutil as _um_shutil
import tempfile as _um_tmp

import numpy as _um_np

import hud_evidence as _um_he
from core import backgrounds as _um_bg
from core import resources as _um_res
from core import usermod as _um
from core.hud import art as _um_art
from core.hud import style as _um_hs
from core.hud import tint as _um_tint

_UM_ROOT = os.path.dirname(SCREENS_DIR)
_um_src = pygame.image.load(os.path.join(_UM_ROOT, _um_bg.UNIVERSAL))
assert "HD EXTENSION, work order 173, decision 72" in (_um.__doc__ or ""), \
    "core/usermod.py lost its marking"


def _um_reset():
    _um.shutdown()
    _um_bg.reset()
    _um_hs.reset()
    _um_art.reset()
    _um_hs.set_tone(None, None, None)


def _um_png(path, size, rgb, alpha=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    s = pygame.Surface(size, pygame.SRCALPHA if alpha else 0, 32)
    s.fill(rgb)
    pygame.image.save(s, path)


def _um_at(surf, xy=(7, 7)):
    return tuple(surf.get_at(xy))[:3]


# 1 — THE BACKGROUND COVERS THE WINDOW, at every size, 16:9 or not: the
#     picture keeps its own aspect (x and y scaled alike to within a
#     pixel), fills both axes (no strip), is cut evenly, and is scaled
#     ONCE per size — the second screen at that size gets the same copy.
_UM_SIZES = ((1280, 720), (1920, 1080), (2560, 1440), (3840, 2160),
             (2576, 1432), (1920, 1200), (3440, 1440), (1280, 1024))
_um_iw, _um_ih = _um_src.get_size()
_um_reset()
for _W, _H in _UM_SIZES:
    _um_k = max(_W / _um_iw, _H / _um_ih)
    _um_sw, _um_sh = max(_W, round(_um_iw * _um_k)), max(_H, round(_um_ih * _um_k))
    assert abs(_um_sw / _um_iw - _um_sh / _um_ih) * min(_um_iw, _um_ih) <= 1.0, (
        f"{_W}x{_H}: scaled {_um_sw}x{_um_sh}, the picture's aspect is lost")
    assert min(_um_sw - _W, _um_sh - _H) <= 1, (_W, _H, _um_sw, _um_sh)
    _um_a = _um_bg.scaled("planets", _W, _H)
    assert _um_a.get_size() == (_W, _H), (_W, _H, _um_a.get_size())
    assert _um_bg.scaled("fleets", _W, _H) is _um_a, (
        f"{_W}x{_H}: two screens on one picture hold two copies")
    # THE CROP IS CENTRED: the window's centre pixel is the picture's.
    _um_c = _um_src.get_at((_um_iw // 2, _um_ih // 2))[:3]
    _um_w = _um_a.get_at((_W // 2, _H // 2))[:3]
    assert max(abs(int(p) - int(q)) for p, q in zip(_um_c, _um_w)) <= 40, (
        _W, _H, _um_c, _um_w)
# The tree's own per-screen picture beats the universal one.
assert _um_bg.source_path("main_menu").endswith("main_menu.png")
assert _um_bg.source_path("galaxy_map").endswith("universal.png")
# NEVER TINTED: the frame colour does not reach the background.
_um_before = pygame.image.tobytes(_um_bg.scaled("planets", 640, 360), "RGB")
_um_hs.set_tone(*_um_tint.NAMED["black"])
_um_bg.reset()
assert pygame.image.tobytes(_um_bg.scaled("planets", 640, 360), "RGB") == \
    _um_before, "the frame colour changed the background"
_um_reset()
ok(f"background covers the window at {len(_UM_SIZES)} sizes: the "
   f"picture's aspect, both axes filled, centred, one copy per size shared "
   f"by the screens, never tinted")

# The rest runs on a mod folder in a temporary directory, never the
# player's: `usermod.init(root=...)`.
_um_dir = _um_tmp.mkdtemp()
try:
    _um_mod = os.path.join(_um_dir, "mod")

    # 2 — THE ORDER, file for file: a mod's per-screen picture beats its
    #     universal one; its universal one replaces the tree's universal
    #     picture; the tree's own per-screen picture (Main Menu) is its
    #     own file and stays until the mod names it too.
    _um_png(os.path.join(_um_mod, "background.png"), (160, 90), (200, 0, 0))
    _um_png(os.path.join(_um_mod, "backgrounds", "galaxy_map.png"),
            (90, 160), (0, 200, 0))
    _um_reset()
    assert _um.init(True, _um_mod) == 2
    assert _um_at(_um_bg.scaled("galaxy_map", 320, 180)) == (0, 200, 0)
    assert _um_at(_um_bg.scaled("planets", 320, 180)) == (200, 0, 0)
    assert _um_bg.source_path("main_menu").endswith(
        os.path.join("backgrounds", "main_menu.png"))
    assert not _um_bg.source_path("main_menu").startswith(_um_mod)
    _um_png(os.path.join(_um_mod, "backgrounds", "main_menu.png"),
            (64, 64), (0, 0, 200))
    _um_reset()
    _um.init(True, _um_mod)
    assert _um_at(_um_bg.scaled("main_menu", 320, 180)) == (0, 0, 200)
    # And through the screens themselves, the galaxy map's floor too.
    _um_app = _um_he.make_app(640, 360)
    _um_he.stage(_um_app, "galaxy_map")
    _um_s = pygame.Surface((640, 360))
    _um_app.dispatcher.active.render(_um_s)
    assert _um_at(_um_s, (3, 180)) == (0, 200, 0), _um_at(_um_s, (3, 180))
    # Removed, the default is back.
    _um_shutil.rmtree(_um_mod)
    _um_reset()
    _um.init(True, _um_mod)
    assert _um_bg.source_path("planets").startswith(_UM_ROOT)
    ok("mod folder: per-screen > universal > default, file by file — the "
       "galaxy map's floor included; a removed file is the default again")

    # 3 — A PARTIAL style.json: only its keys; a key of the wrong kind or
    #     one the style does not have is skipped, the rest still applies.
    os.makedirs(_um_mod, exist_ok=True)
    _um_reset()
    _um_def = _um_hs.get()
    _um_want = {k: _um_def.get(k) for k in
                ("panel.edge", "panel.fill", "panel.edge_width",
                 "button.edge")}
    with open(os.path.join(_um_mod, "style.json"), "w") as _f:
        _um_json.dump({"measured": {"panel": {"edge": [255, 0, 0],
                                              "edge_width": "wide",
                                              "no_such_key": 3}},
                       "chosen": {"background_placeholder": [9, 9, 9]},
                       "nonsense": 1}, _f)
    _um_reset()
    _um.init(True, _um_mod)
    _um_new = _um_hs.get()
    assert _um_new.get("panel.edge") == [255, 0, 0]
    assert _um_new.get("background_placeholder") == [9, 9, 9]
    assert _um_new.get("panel.edge_width") == _um_want["panel.edge_width"]
    assert _um_new.get("panel.fill") == _um_want["panel.fill"]
    assert _um_new.get("button.edge") == _um_want["button.edge"]
    # The tree's file is untouched, and the measured-block check reads it.
    assert _um_json.load(open(os.path.join(_UM_ROOT, "assets", "shared",
                                           "hud", "style.json")))[
        "measured"]["panel"]["edge"] == _um_want["panel.edge"]
    ok("mod folder: a partial style.json overrides only its keys; a wrong "
       "kind, an unknown key and a stray group are skipped")

    # 4 — BROKEN, WRONG OR ODD FILES: never a crash, never a broken
    #     screen. Garbage bytes under a picture name, a picture under the
    #     wrong name, style.json and colour.json that are not JSON, an
    #     icon of another size (scaled to the default's), a transparent
    #     plate of another aspect — and every screen still renders.
    _um_shutil.rmtree(_um_mod)
    os.makedirs(os.path.join(_um_mod, "hud"))
    with open(os.path.join(_um_mod, "background.png"), "wb") as _f:
        _f.write(b"not a picture at all")
    with open(os.path.join(_um_mod, "style.json"), "w") as _f:
        _f.write("{ this is not json")
    with open(os.path.join(_um_mod, "colour.json"), "w") as _f:
        _f.write("[1, 2, 3]")
    _um_png(os.path.join(_um_mod, "hud", "icon_food.png"), (500, 37),
            (0, 255, 0), alpha=True)
    _um_png(os.path.join(_um_mod, "hud", "icon_nosuch.png"), (9, 9),
            (0, 255, 0))
    _um_png(os.path.join(_um_mod, "backgrounds", "no_such_screen.png"),
            (9, 9), (0, 255, 0))
    _um_png(os.path.join(_um_mod, "files", "screens", "galaxy_map",
                         "assets", "nosuch.png"), (9, 9), (0, 255, 0))
    _um_reset()
    assert _um.init(True, _um_mod) == 2, _um._state["index"]
    assert _um_bg.source_path("planets").startswith(_UM_ROOT), \
        "a broken background.png was used"
    assert _um_hs.get().get("panel.edge") == _um_want["panel.edge"]
    _um_food = _um_res.res.shared("hud", "cut", "icon_food.png")
    _um_dflt = os.path.join(_UM_ROOT, "assets", "shared", "hud", "cut",
                            "icon_food.png")
    if os.path.exists(_um_dflt):
        assert _um_food.startswith(_um_dir), _um_food
        assert pygame.image.load(_um_food).get_size() == \
            pygame.image.load(_um_dflt).get_size(), "not scaled to fit"
    _um_n = 0
    for _um_name in ("galaxy_map", "planets", "colony_summary", "new_game",
                     "game_menu_settings"):
        _um_app = _um_he.make_app(960, 540)
        _um_he.stage(_um_app, _um_name)
        _um_s = pygame.Surface((960, 540))
        _um_app.dispatcher.active.render(_um_s)
        if _um_app.dispatcher.overlay_name:
            _um_app.dispatcher.screens[
                _um_app.dispatcher.overlay_name].render(_um_s)
        _um_n += 1
    ok(f"mod folder: garbage, unknown names and non-JSON fall back with a "
       f"line each, an odd-sized icon is scaled to the default's; "
       f"{_um_n} screens render on the broken folder")

    # 5 — SWITCHED OFF, NOT READ; colour.json IS THE DEFAULT COLOUR. The
    #     player's own colour beats it, RESET returns to it, and what the
    #     settings row stores is the player's value, never the mod's.
    _um_shutil.rmtree(_um_mod)
    _um_png(os.path.join(_um_mod, "background.png"), (160, 90), (200, 0, 0))
    with open(os.path.join(_um_mod, "colour.json"), "w") as _f:
        _um_json.dump({"hue": 280, "saturation": 0.5, "brightness": 7}, _f)
    _um_reset()
    assert _um.init(False, _um_mod) == 0
    assert not _um.active() and _um.started_enabled() is False
    assert _um_bg.source_path("planets").startswith(_UM_ROOT)
    _um_hs.set_tone(None, None, None)
    assert _um_tint.is_default(), "a switched-off folder set the colour"
    _um_reset()
    _um.init(True, _um_mod)
    _um_hs.set_tone(None, None, None)
    assert round(_um_tint.hue()) == 280 and _um_tint.sat() == 0.5
    assert _um_tint._bright is None, "brightness 7 is out of range"
    _um_hs.set_tone(40, None, None)
    assert round(_um_tint.hue()) == 40 and _um_tint.sat() == 0.5
    from screens.game_menu import gmorion as _um_gmo
    from core import usersettings as _um_us

    class _UmScreen:
        class app:
            user_settings = _um_us.UserSettings(path=os.devnull)
    _um_gmo.set_tone(_UmScreen, sat=0.3)
    assert _UmScreen.app.user_settings.get("hud_hue") is None, (
        "the settings row stored the mod's hue as the player's")
    assert round(_um_tint.hue()) == 280 and _um_tint.sat() == 0.3
    _um_gmo.set_tone(_UmScreen, None, None, None)
    assert round(_um_tint.hue()) == 280 and _um_tint.sat() == 0.5
    # main.App reads the switch, and the row offers it.
    _um_main = open(os.path.join(_UM_ROOT, "main.py"), encoding="utf-8").read()
    assert 'usermod.init(self.user_settings.get("user_mod") != "off")' in \
        _um_main
    assert "mods" in _um_gmo.BANDS and _um_gmo.MOD_STEPS == ("on", "off")
    assert _um_us.DEFAULTS["user_mod"] == "on"
    ok("mod folder: switched off it is not read; colour.json is the "
       "default frame colour — the player's beats it, RESET returns to it, "
       "the row stores the player's value; main.App reads the switch")

    # 6 — THE TEMPLATE HOLDS NO MOO2 FILE. Everything it copies is
    #     OrionLayer's own: the universal background, the HUD pieces cut
    #     from Data's HUD, the style file — and nothing it writes equals
    #     any other picture in the tree, extracted or derived. The MOO2
    #     names are listed as text only. It refuses the tree itself.
    import mod_template as _um_tpl
    assert "HD EXTENSION, work order 173, decision 72" in (
        _um_tpl.__doc__ or ""), "the template tool lost its marking"
    _um_out = os.path.join(_um_dir, "template")
    _um_written = _um_tpl.make(_um_out, log=lambda *_a: None)
    _um_own = {os.path.join(_UM_ROOT, _um_bg.UNIVERSAL),
               os.path.join(_UM_ROOT, "assets", "shared", "hud", "style.json")}
    import hashlib as _um_hl

    def _um_sha(p):
        return _um_hl.sha256(open(p, "rb").read()).hexdigest()
    _um_ours = {_um_sha(p) for p in _um_own}
    _um_cut = os.path.join(_um_dir, "cut")
    import hud_cut as _um_cutter
    _um_cutter.write(_um_cut)
    _um_ours |= {_um_sha(os.path.join(_um_cut, f)) for f in os.listdir(_um_cut)}
    _um_theirs = set()
    for _r, _ds, _fs in os.walk(_UM_ROOT):
        _ds[:] = [x for x in _ds if x not in (".git", "__pycache__")]
        for _f in _fs:
            if _f.lower().endswith((".png", ".jpg", ".ttf", ".lbx", ".json",
                                    ".txt")):
                _um_theirs.add(_um_sha(os.path.join(_r, _f)))
    _um_theirs -= _um_ours
    _um_bad = [p for p in _um_written if _um_sha(p) in _um_theirs]
    assert not _um_bad, f"the template copied files that are not ours: {_um_bad}"
    _um_pics = [p for p in _um_written
                if p.lower().endswith((".png", ".jpg", ".ttf"))]
    assert all(_um_sha(p) in _um_ours for p in _um_pics), [
        p for p in _um_pics if _um_sha(p) not in _um_ours]
    assert len(_um_pics) == len(_um_art.PIECES) + 1, _um_pics
    _um_names = open(os.path.join(_um_out, "NAMES.txt"), encoding="utf-8").read()
    assert "files/screens/select_race/assets/portraits/" in _um_names
    assert "hud/title_plate.png" in _um_names
    assert "backgrounds/galaxy_map.png" in _um_names
    assert "backgrounds/game_menu.png" not in _um_names, "an overlay listed"
    assert "Mod folder: Off" in open(os.path.join(_um_out, "MODDING.md"),
                                     encoding="utf-8").read()
    # Nothing it wrote is read until a starting point is copied up.
    _um_reset()
    assert _um.init(True, _um_out) == 0
    try:
        _um_tpl.make(os.path.join(_UM_ROOT, "mods", "_x"), log=lambda *_a: None)
        raise AssertionError("the template wrote into the tree")
    except SystemExit:
        pass
    ok(f"mod template: {len(_um_written)} files, the {len(_um_pics)} "
       f"pictures all OrionLayer's own; no MOO2 file, names only; refused "
       f"inside the tree")
finally:
    _um_reset()
    _um_shutil.rmtree(_um_dir, ignore_errors=True)

# 7 — TEXT DIRECTLY ON THE UNIVERSAL BACKGROUND KEEPS ITS CONTRAST.
#     `tools/background_measure.py` renders each screen three ways and
#     measures every word that stands on the picture (not on a panel)
#     against the brightest background under it. The floor is 3.4:1 —
#     what the dimmest words measured on the old placeholder already
#     (3.35: New Game's "|" separators); the background may not take any
#     word below it. Push-only: ~20 s.
if slow("background_contrast"):
    import background_measure as _um_bm
    _um_words, _um_low = 0, []
    for _um_name in ("galaxy_map", "new_game", "select_race", "custom_race",
                     "research_select", "game_menu_settings"):
        _um_r = _um_bm.contrast(_um_name, 1920, 1080)
        _um_words += _um_r["words"]
        if _um_r["min"] is not None and _um_r["min"] < 3.4:
            _um_low.append((_um_name, _um_r["min"], _um_r["min_at"]))
    assert _um_words >= 150, f"only {_um_words} words measured"
    assert not _um_low, f"words below 3.4:1 on the background: {_um_low}"
    ok(f"text on the universal background: {_um_words} words on six "
       f"screens, none below 3.4:1")
