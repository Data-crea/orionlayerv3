"""Where the editor saves — HD EXTENSION `editor_mod_save`, work order 334.

**A PLAYER'S EDIT GOES INTO A MOD, NEVER INTO THE BASE.** The editor used
to overwrite whatever file the boxes were loaded from, which for most
people is the shipped `screens/<screen>/boxes.json`: no backup, no way
back without git. Now it writes `mods/<mod>/screens/<screen>/boxes.json`
for the first active mod, or for `my_layout` when none is active, and
says what to add to `settings.json` so the mod loads. The base project
stays what was shipped (this amends decision 19 and work order 324 d).

DEVELOPER MODE: `ORIONLAYER_EDITOR=base` keeps the old route (the file
the boxes were loaded from, plus the screens' own extra files), because
the project's own layout work is done that way.
"""
import json
import os

from core import config

ENV = "ORIONLAYER_EDITOR"
DEFAULT_MOD = "my_layout"


def developer():
    return os.environ.get(ENV, "").strip().lower() == "base"


class Target:
    def __init__(self, folder, label, active=True, hint=""):
        self.folder = folder      # where boxes.json is written
        self.label = label        # one line for the panel
        self.active = active      # the mod loads at the next start
        self.hint = hint          # what to do when it does not


def resolve(app, screen):
    """The `Target` for the screen being edited."""
    base = screen._screen_dir
    if developer():
        folder = getattr(screen, "_boxes_dir", None) or base
        same = os.path.abspath(folder) == os.path.abspath(base)
        return Target(folder, "developer mode: "
                      + ("the base project" if same else "mod " + folder))
    mods = list(getattr(app.res, "mod_dirs", []) or [])
    if mods:
        root, active = mods[0], True
    else:
        root, active = os.path.join(config.MODS_DIR, DEFAULT_MOD), False
    name = os.path.basename(os.path.normpath(root))
    folder = os.path.join(root, "screens", screen.SCREEN_NAME)
    if active:
        return Target(folder, f"mod {name}")
    return Target(folder, f"mod {name} (not active yet)", False,
                  f'Add "{name}" to "active_mods" in settings.json, '
                  f"then restart.")


def prepare(target):
    """Make the folder, and a `mod.json` for a mod this call creates."""
    os.makedirs(target.folder, exist_ok=True)
    root = os.path.dirname(os.path.dirname(os.path.normpath(target.folder)))
    meta = os.path.join(root, "mod.json")
    if not developer() and not os.path.exists(meta):
        with open(meta, "w", encoding="utf-8") as handle:
            json.dump({"name": os.path.basename(root), "version": "1.0",
                       "author": "", "description":
                       "Box layout made with the F3 editor."}, handle,
                      indent=2)
            handle.write("\n")
