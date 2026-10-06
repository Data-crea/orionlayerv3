"""The player's OrionLayer settings — values the game knows nothing about.

**ONE HOME.** `user_settings.json` in the player's OrionLayer folder —
`$XDG_CONFIG_HOME/orionlayer/` (`~/.config/orionlayer/`), the same base
as the mod folder (decision 72, `usermod.user_dir`) — and this module is
the only thing that reads or writes it (brief decision 7, 14 September
2026; the home moved out of the program folder in work order 179, so a
new checkout or a second copy of the program finds the player's
settings instead of the defaults).

**THE OLD HOME IS READ ONCE AND NEVER WRITTEN.** Until 179 the file lived
beside `settings.json` (`OLD_PATH`). At startup, if the new file is
missing and the old one exists, the old one is COPIED over — never moved,
never changed, so a build from before 179 on the same checkout still
finds its file. If both exist the new one wins and one log line says the
old one is ignored. Every write goes to the new home, and `save` creates
the folder. It is NOT `settings.json`, which is the application's own
configuration and is committed on purpose, and NOT
`core/structs/settings.py`, which is the engine's `s_settings`.

**USER DATA.** Ignored by git, never shipped, not in any `boxes.json`
and never on the F5 editor's save path (decision 19). What it holds is a
property of the player's display and eyes, not of the game.

**THREE STATES, AND ONLY ONE OF THEM IS LOUD.**
- absent: the defaults, silently — a fresh install has no file and that
  is not a fault;
- corrupt (unreadable, not JSON, not an object): ONE error line, the
  defaults, and the program carries on. The file is not overwritten on
  load; the first save moves it aside to `user_settings.json.corrupt`
  so the player's broken file is kept for them to look at;
- ok: the values, with any key this build does not know KEPT and written
  back on save, so an older build cannot eat a newer build's settings.

**ORDER AT STARTUP IS WRITTEN HERE, not left to happen.** The
player-colour preset is read when the palette is initialised
(`palette.init(preset=...)`), so `main.App` loads this file BEFORE
`palette.init`. Tools and the smoke test never read it: they call
`palette.init` without a preset and get the original.
"""
import json
import logging
import os
import shutil

from core import usermod
from core.config import BASE_DIR

log = logging.getLogger("usersettings")

NAME = "user_settings.json"
#: Where the file lived until work order 179 — read by the migration only.
OLD_PATH = os.path.join(BASE_DIR, NAME)


def default_path():
    """The file's home, resolved NOW: `XDG_CONFIG_HOME` (and the
    `ORIONLAYER_USER_DIR` override) are read at every call, not at
    import, so a test or a tool that sets them is honoured."""
    return os.path.join(usermod.user_dir(), NAME)


def migrate(new=None, old=OLD_PATH):
    """The one-time move from the program folder: copy `old` to `new` when
    only `old` exists; say so once when both do. Returns `new`. The old
    file is never deleted or modified."""
    new = new or default_path()
    if os.path.exists(new):
        if old and os.path.exists(old):
            log.info("user settings: %s is used; the old %s is ignored",
                     new, old)
        return new
    if old and os.path.exists(old):
        os.makedirs(os.path.dirname(new), exist_ok=True)
        shutil.copy2(old, new)
        log.info("user settings: copied %s to %s (the old file is left "
                 "as it was)", old, new)
    return new

#: The original's look: no floor lift, the game's own player colours.
#: One exception, Data's decision: the monster values in the Planets
#: panel (fundament 64) are ON by default — they level a field newcomers
#: and veterans do not share, and a switch nobody finds does not.
DEFAULTS = {
    "floor_lift": "off",
    "player_colors": "original",
    "monster_values": "on",
    # The HUD frame colour, a hue in degrees; None is the measured blue
    # (work order 170, `core.hud.tint`).
    "hud_hue": None,
    # Its saturation and brightness factors (work order 171); None is
    # the measured value, so a file written by 170 with hud_hue alone
    # reads the same colour it always did.
    "hud_sat": None,
    "hud_bright": None,
    # The player's mod folder (decision 72): "off" uses the defaults and
    # leaves the folder as it is. Read at start, so a change needs a
    # restart (decision 18). OFF BY DEFAULT since work order 197 (Data;
    # 195's Q5 (a)): the file stores a key only once the player changed
    # it, so a player who switched the folder on keeps it on.
    "user_mod": "off",
    # The Panel glass slider (work order 174), 0 see-through .. 1 solid;
    # None is the default (the measured 0.5, or a mod's).
    "hud_glass": None,
    # The language OrionLayer shows (work order 200 C, `core/lang`): None
    # is settings.json's ("en"). Read at start, so a change needs a restart.
    "language": None,
    # The folder of another install that holds the language's files (a
    # German MOO2 beside an English one, work order 200 C): the extractors
    # read it and the engine is told it (open fix 70). None: the game's own
    # folder. Set by `tools/language_files.py`.
    "language_dir": None,
    # The frame rate (work order 212, decision 79, `core/framerate`): 30, 60,
    # 120, the monitor's rate or unlimited; applied at once.
    "frame_rate": "monitor",
    # How finely the battle holds a painted picture (work order 219,
    # `core/paintdetail`): auto, normal (4 x) or high (8 x); from the next
    # battle on.
    "painted_detail": "auto",
}


class UserSettings:
    """What was read, what was changed, and where it goes."""

    def __init__(self, data=None, state="absent", path=None):
        self.data = dict(data or {})
        self.state = state
        self.path = path or default_path()

    def get(self, key):
        return self.data.get(key, DEFAULTS.get(key))

    def set(self, key, value):
        """In memory at once; the file is written by `save`."""
        self.data[key] = value


def load(path=None):
    """The player's settings. Without `path` the file's own home, after
    the one-time migration; with one, exactly that file (tests, tools)."""
    if path is None:
        path = migrate()
    if not os.path.exists(path):
        return UserSettings(path=path)
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            raise ValueError(f"top level is {type(data).__name__}, not an object")
    except (OSError, ValueError) as err:
        log.error("user settings: %s is unreadable (%s) — using the "
                  "defaults; the file is kept and moved aside on the "
                  "next save", path, err)
        return UserSettings(state="corrupt", path=path)
    return UserSettings(data, "ok", path)


def save(settings):
    """Write the file if its content would change. True if written.

    Idempotent, so ACCEPT and the overlay's exit can both call it: the
    second call finds the file already saying the same thing.
    """
    if not settings.data and not os.path.exists(settings.path):
        return False
    text = json.dumps(settings.data, indent=2, sort_keys=True) + "\n"
    if settings.state == "corrupt" and os.path.exists(settings.path):
        os.replace(settings.path, settings.path + ".corrupt")
        log.warning("user settings: the unreadable file was moved to %s",
                    settings.path + ".corrupt")
        settings.state = "ok"
    try:
        with open(settings.path, encoding="utf-8") as handle:
            if handle.read() == text:
                return False
    except OSError:
        pass
    os.makedirs(os.path.dirname(settings.path) or ".", exist_ok=True)
    tmp = settings.path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        handle.write(text)
    os.replace(tmp, settings.path)
    return True
