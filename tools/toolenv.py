"""What a tool has to set up before it imports a screen module.

Screen modules bind colours at IMPORT (decision 18), and a colour with no
code default is `palette.require` — which raises if nothing has initialised
the palette yet. `main.App` does that before any screen is imported; a tool
has no App, so it has to do it itself, BEFORE its `from screens…` lines.
`dev:tools/colony_move_hd.py` and four siblings did not, and could not be
imported at all from 14 September 2026 (`plate_outline`, `ship_0`) until
work order 126 D; `dev:tools/game_menu_hd.py` carried its own copy of the fix.
This is the one home, and the smoke test imports every tool with a
`__main__` in a fresh process so a tool that forgets it fails there.

The palette is the SKIN's, without the player's colour preset: tools and
the smoke test never see the player's choice (`core/usersettings.py`).
The one exception is a tool that then starts `main.App` (`livedrive`):
App applies the player's preset, so a palette without it would bind every
screen module imported before App to the original's colours and every one
imported after to the preset's — one live run showed Altair's name in
purple, the next in sky blue (work order 310). Such a tool asks for
`user=True` and binds what App will bind.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def init_palette(user=False, settings_path=None):
    """Initialise resources and the skin palette; returns the resolver.

    `user=True` reads the player's settings the way `main.App.__init__`
    does — mod folder switch, colour preset, own base table — so a tool
    that starts App binds the same colours before App as after it.
    `settings_path` names the settings file (a check forces its own)."""
    from core import palette, resources
    from core.config import load_settings
    settings = load_settings()
    res = resources.init(settings)
    preset = base = None
    if user:
        from core import usermod, usersettings
        mine = usersettings.load(settings_path)
        usermod.init(mine.get("user_mod") != "off")
        preset = mine.get("player_colors")
        base = mine.get("player_color_base")
    skin = settings.get("skin", "default")
    colours = res.load_json(f"assets/shared/skins/{skin}/colors.json", {})
    palette.init(colours, preset=preset, base=base)
    return res
