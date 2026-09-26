# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 006g_core_settings_home_and_migration.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/, in file-name order and in ONE
# namespace. Do not import this file; it is not a module.
#
# Work order 179, part 1: `user_settings.json` moved out of the program
# folder into the player's OrionLayer folder, the same base as the mod
# folder (decision 72) — with a one-time copy from the old home that
# never touches the old file, and the live guard holding both.
#
# The 3 check(s) it holds:
#   - settings home: new missing / both present / neither — the migration's three states
#   - settings home: XDG_CONFIG_HOME honoured, every write to the new home only
#   - live guard: the settings in both homes backed up, verified and restored


import logging as _sh_logging
import shutil as _sh_shutil
import tempfile as _sh_tmp

import liveguard as _sh_lg
from core import usermod as _sh_um
from core import usersettings as _sh_us


class _ShCatch(_sh_logging.Handler):
    def __init__(self):
        super().__init__()
        self.lines = []

    def emit(self, record):
        self.lines.append(record.getMessage())


def _sh_env(**values):
    """Set (or, with None, remove) environment variables; return the old
    values for `_sh_env(**old)` to put back."""
    old = {k: os.environ.get(k) for k in values}
    for k, v in values.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    return old


def _sh_write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def _sh_read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


# 1 — THE MIGRATION'S THREE STATES. The old file is read, never written:
#     a build from before 179 on the same checkout still finds it.
_sh_catch = _ShCatch()
_sh_logging.getLogger("usersettings").addHandler(_sh_catch)
# The migration's lines are INFO, which the app logs (main.py) and a bare
# logger drops.
_sh_level = _sh_logging.getLogger("usersettings").level
_sh_logging.getLogger("usersettings").setLevel(_sh_logging.INFO)
_sh_dir = _sh_tmp.mkdtemp()
_sh_old_env = _sh_env(ORIONLAYER_USER_DIR=os.path.join(_sh_dir, "home"))
try:
    _sh_old = os.path.join(_sh_dir, "program", "user_settings.json")
    _sh_new = _sh_us.default_path()
    assert _sh_new == os.path.join(_sh_dir, "home", "user_settings.json"), \
        _sh_new
    # (a) neither: the defaults, silently, and nothing created.
    assert _sh_us.migrate(_sh_new, _sh_old) == _sh_new
    assert not os.path.exists(os.path.dirname(_sh_new)), \
        "the migration created the folder with nothing to copy"
    assert _sh_us.load(_sh_us.migrate(_sh_new, _sh_old)).state == "absent"
    assert _sh_catch.lines == [], _sh_catch.lines
    # (b) only the old one: copied, byte for byte, the old one untouched.
    _sh_write(_sh_old, '{"hud_hue": 161, "floor_lift": "light"}\n')
    _sh_stat = os.stat(_sh_old)
    _sh_us.migrate(_sh_new, _sh_old)
    assert _sh_read(_sh_new) == _sh_read(_sh_old)
    assert os.stat(_sh_old).st_mtime_ns == _sh_stat.st_mtime_ns
    assert _sh_us.load(_sh_new).get("hud_hue") == 161
    assert len(_sh_catch.lines) == 1 and "copied" in _sh_catch.lines[0], \
        _sh_catch.lines
    # (c) both: the new one wins, ONE line names the ignored old one, and
    #     neither file changes.
    _sh_write(_sh_new, '{"hud_hue": 280}\n')
    _sh_catch.lines.clear()
    _sh_us.migrate(_sh_new, _sh_old)
    assert _sh_us.load(_sh_new).get("hud_hue") == 280
    assert _sh_read(_sh_old) == '{"hud_hue": 161, "floor_lift": "light"}\n'
    assert len(_sh_catch.lines) == 1 and "ignored" in _sh_catch.lines[0], \
        _sh_catch.lines
    # And `load()` without a path is exactly "migrate, then read the home".
    _sh_src = open(_sh_us.__file__, encoding="utf-8").read()
    assert "path = migrate()" in _sh_src
    assert "self.path = path or default_path()" in _sh_src
finally:
    _sh_logging.getLogger("usersettings").removeHandler(_sh_catch)
    _sh_logging.getLogger("usersettings").setLevel(_sh_level)
    _sh_env(**_sh_old_env)
    _sh_shutil.rmtree(_sh_dir, ignore_errors=True)
ok("settings home: new missing -> the old file copied (old untouched), "
   "both present -> the new one wins with one log line, neither -> the "
   "defaults and nothing created")


# 2 — XDG_CONFIG_HOME, and every write to the new home only.
_sh_dir = _sh_tmp.mkdtemp()
_sh_old_env = _sh_env(ORIONLAYER_USER_DIR=None,
                      XDG_CONFIG_HOME=os.path.join(_sh_dir, "xdg"))
try:
    if not sys.platform.startswith("win") and sys.platform != "darwin":
        assert _sh_us.default_path() == os.path.join(
            _sh_dir, "xdg", "orionlayer", "user_settings.json"), \
            _sh_us.default_path()
        # The same base as the mod folder (decision 72), by construction.
        assert os.path.dirname(_sh_us.default_path()) == \
            os.path.dirname(_sh_um.mod_dir())
        _sh_env(XDG_CONFIG_HOME=None)
        assert _sh_us.default_path() == os.path.join(
            os.path.expanduser("~/.config"), "orionlayer", "user_settings.json")
        _sh_env(XDG_CONFIG_HOME=os.path.join(_sh_dir, "xdg"))
    _sh_old = os.path.join(_sh_dir, "program", "user_settings.json")
    _sh_write(_sh_old, '{"floor_lift": "light"}\n')
    _sh_set = _sh_us.load(_sh_us.migrate(old=_sh_old))
    _sh_set.set("floor_lift", "strong")
    assert _sh_us.save(_sh_set) is True
    assert _sh_set.path == _sh_us.default_path()
    assert '"strong"' in _sh_read(_sh_us.default_path())
    assert _sh_read(_sh_old) == '{"floor_lift": "light"}\n', \
        "a save wrote the old home"
    # save() creates the folder when it is missing.
    _sh_fresh = _sh_us.UserSettings({"hud_hue": 10}, "ok", os.path.join(
        _sh_dir, "not", "yet", "user_settings.json"))
    assert _sh_us.save(_sh_fresh) and os.path.exists(_sh_fresh.path)
    # Nothing else in the tree writes the file: the old path is named by
    # usersettings.OLD_PATH and by nothing that writes.
    assert _sh_us.OLD_PATH == os.path.join(
        os.path.dirname(SCREENS_DIR), "user_settings.json")
finally:
    _sh_env(**_sh_old_env)
    _sh_shutil.rmtree(_sh_dir, ignore_errors=True)
ok("settings home: XDG_CONFIG_HOME/orionlayer (default ~/.config/orionlayer), "
   "the mod folder's base; every write goes to the new home, the folder is "
   "created, the old file never written")


# 3 — THE LIVE GUARD HOLDS BOTH HOMES. The new one because every run
#     writes it; the old one while it exists, because it is the player's
#     file and a run must still not change it.
_sh_dir = _sh_tmp.mkdtemp()
try:
    _sh_game = os.path.join(_sh_dir, "game")
    _sh_root = os.path.join(_sh_dir, "program")
    _sh_conf = os.path.join(_sh_dir, "config")
    _sh_dest = os.path.join(_sh_dir, "guard")
    _sh_write(os.path.join(_sh_game, "SAVE4.GAM"), "save")
    _sh_write(os.path.join(_sh_root, "user_settings.json"), '{"a": 1}\n')
    _sh_write(os.path.join(_sh_conf, "user_settings.json"), '{"b": 2}\n')
    _sh_man = _sh_lg.snapshot(_sh_dest, _sh_game, _sh_root, _sh_conf)
    for _sh_key in ("layer/user_settings.json", "config/user_settings.json"):
        assert _sh_man["files"][_sh_key] and os.path.exists(
            _sh_man["files"][_sh_key]["copy"]), _sh_key
    assert _sh_man["config_dir"] == _sh_conf
    assert _sh_lg.verify(_sh_dest, log=lambda *_a: None)[0] == []
    _sh_write(os.path.join(_sh_root, "user_settings.json"), '{"a": 9}\n')
    _sh_write(os.path.join(_sh_conf, "user_settings.json"), '{"b": 9}\n')
    _sh_write(os.path.join(_sh_conf, "user_settings.json.tmp"), "x")
    _sh_ch, _ = _sh_lg.verify(_sh_dest, log=lambda *_a: None)
    assert dict(_sh_ch) == {"layer/user_settings.json": "changed",
                            "config/user_settings.json": "changed",
                            "config/user_settings.json.tmp": "appeared"}, _sh_ch
    _sh_lg.verify(_sh_dest, restore=True, log=lambda *_a: None)
    assert _sh_lg.verify(_sh_dest, log=lambda *_a: None)[0] == []
    assert _sh_read(os.path.join(_sh_conf, "user_settings.json")) == '{"b": 2}\n'
    assert _sh_read(os.path.join(_sh_root, "user_settings.json")) == '{"a": 1}\n'
    # The whole config folder gone (a fresh machine): restored with it.
    _sh_shutil.rmtree(_sh_conf)
    _sh_lg.verify(_sh_dest, restore=True, log=lambda *_a: None)
    assert _sh_read(os.path.join(_sh_conf, "user_settings.json")) == '{"b": 2}\n'
    # An old home that does not exist is not held and not reported.
    os.remove(os.path.join(_sh_root, "user_settings.json"))
    _sh_man = _sh_lg.snapshot(_sh_dest + "2", _sh_game, _sh_root, _sh_conf)
    assert _sh_man["files"]["layer/user_settings.json"] is None
    assert _sh_lg.verify(_sh_dest + "2", log=lambda *_a: None)[0] == []
    # The default is the settings' own home, not a second spelling of it.
    assert _sh_lg.files()["config/user_settings.json"] in (
        None, _sh_us.default_path())
finally:
    _sh_shutil.rmtree(_sh_dir, ignore_errors=True)
ok("live guard: user_settings.json in its new home AND in the old one "
   "backed up, a change in either named, both restored (a missing folder "
   "recreated); an absent old home not held")
