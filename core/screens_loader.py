"""Screen auto-discovery.

Scans screens/ in the base project AND in every active mod for
folders containing a screen.py that defines a ScreenBase subclass.
No central registration list: dropping a folder with a screen.py
into screens/ (or mods/<mod>/screens/) is enough.

Conventions for a screen module:
  - File:  screens/<name>/screen.py
  - Class: subclass of ScreenBase with SCREEN_NAME = "<name>"
  - Optional: GAME_SCREEN_ID = <orion2re screen id> to auto-switch
    when orion2re enters that screen. Sub-screens (opened manually
    via dispatcher.switch_to) leave it at None.

Mods win: if a mod ships screens/<name>/screen.py for an existing
name, the mod's class replaces the base one.

Folders starting with "_" (e.g. _template) are skipped.
"""
import os
import inspect
import importlib
import importlib.util
import logging

from core.config import SCREENS_DIR
from core.screen_base import ScreenBase

log = logging.getLogger("screens")


def _load_module(screen_name, screen_py, from_mod):
    """Import a screen module from an explicit file path."""
    # Unique module name so a mod screen never collides with base
    mod_tag = "mod" if from_mod else "base"
    module_name = f"screens_{mod_tag}_{screen_name}"
    try:
        if from_mod:
            spec = importlib.util.spec_from_file_location(
                module_name, screen_py)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        # Base screens import as normal packages so their own
        # relative imports (renderer.py etc.) keep working.
        return importlib.import_module(f"screens.{screen_name}.screen")
    except Exception as e:
        log.error("Failed to load screen '%s' (%s): %s",
                  screen_name, screen_py, e)
        return None


def _find_screen_class(module, screen_name):
    """Find the ScreenBase subclass defined in this module."""
    for _, obj in inspect.getmembers(module, inspect.isclass):
        if (issubclass(obj, ScreenBase) and obj is not ScreenBase
                and getattr(obj, "SCREEN_NAME", "") == screen_name):
            return obj
    log.warning("screen.py in '%s' has no ScreenBase subclass "
                "with SCREEN_NAME='%s'", screen_name, screen_name)
    return None


def discover_screens(resources):
    """Return {screen_name: screen_class} from base + active mods.

    Base screens are collected first, then mods overwrite by name
    (mods are iterated in priority order, highest priority last
    so it wins).
    """
    found = {}

    roots = resources.screen_roots()          # mods first, base last
    base_root = os.path.abspath(SCREENS_DIR)
    for root in reversed(roots):              # base first, mods override
        from_mod = os.path.abspath(root) != base_root
        for entry in sorted(os.listdir(root)):
            if entry.startswith("_"):
                continue
            screen_py = os.path.join(root, entry, "screen.py")
            if not os.path.isfile(screen_py):
                continue
            module = _load_module(entry, screen_py, from_mod)
            if not module:
                continue
            cls = _find_screen_class(module, entry)
            if cls:
                origin = "mod" if from_mod else "base"
                if entry in found and from_mod:
                    log.info("Screen '%s' overridden by mod", entry)
                found[entry] = cls
                log.debug("Screen discovered: %s (%s)", entry, origin)

    log.info("Screens: %s", ", ".join(sorted(found)))
    return found


def register_all(app, dispatcher, resources):
    """Discover and register all screens on the dispatcher."""
    for name, cls in discover_screens(resources).items():
        dispatcher.register(name, cls(app))
