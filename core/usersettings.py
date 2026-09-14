"""The player's OrionLayer settings — values the game knows nothing about.

**ONE HOME.** `user_settings.json` beside `settings.json`, and this module
is the only thing that reads or writes it (brief decision 7, 14 September
2026). It is NOT `settings.json`, which is the application's own
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

from core.config import BASE_DIR

log = logging.getLogger("usersettings")

PATH = os.path.join(BASE_DIR, "user_settings.json")

#: The original's look: no floor lift, the game's own player colours.
DEFAULTS = {
    "floor_lift": "off",
    "player_colors": "original",
}


class UserSettings:
    """What was read, what was changed, and where it goes."""

    def __init__(self, data=None, state="absent", path=PATH):
        self.data = dict(data or {})
        self.state = state
        self.path = path

    def get(self, key):
        return self.data.get(key, DEFAULTS.get(key))

    def set(self, key, value):
        """In memory at once; the file is written by `save`."""
        self.data[key] = value


def load(path=PATH):
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
    tmp = settings.path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        handle.write(text)
    os.replace(tmp, settings.path)
    return True
