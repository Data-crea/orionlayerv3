"""What a tool has to set up before it imports a screen module.

Screen modules bind colours at IMPORT (decision 18), and a colour with no
code default is `palette.require` — which raises if nothing has initialised
the palette yet. `main.App` does that before any screen is imported; a tool
has no App, so it has to do it itself, BEFORE its `from screens…` lines.
`tools/colony_move_hd.py` and four siblings did not, and could not be
imported at all from 14 September 2026 (`plate_outline`, `ship_0`) until
work order 126 D; `tools/game_menu_hd.py` carried its own copy of the fix.
This is the one home, and the smoke test imports every tool with a
`__main__` in a fresh process so a tool that forgets it fails there.

The palette is the SKIN's, without the player's colour preset: tools and
the smoke test never see the player's choice (`core/usersettings.py`).
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def init_palette():
    """Initialise resources and the skin palette; returns the resolver."""
    from core import palette, resources
    from core.config import load_settings
    settings = load_settings()
    res = resources.init(settings)
    skin = settings.get("skin", "default")
    palette.init(res.load_json(f"assets/shared/skins/{skin}/colors.json", {}))
    return res
