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
import sys
import zlib
import inspect
import importlib
import importlib.machinery
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
    if from_mod:
        # ONE PACKAGE PER FOLDER: two mods that both replace a screen would
        # share `screens_mod_<name>`, and the second one's `from .renderer
        # import …` would be answered by the first one's cached module
        module_name += "_%08x" % (zlib.crc32(os.path.dirname(
            os.path.abspath(screen_py)).encode("utf-8")) & 0xFFFFFFFF)
    try:
        if from_mod:
            return _load_mod_package(module_name, screen_py)
        # Base screens import as normal packages so their own
        # relative imports (renderer.py etc.) keep working.
        return importlib.import_module(f"screens.{screen_name}.screen")
    except Exception as e:  # noqa: BLE001 — one screen must not end the start
        # WITH THE TRACEBACK: a NameError or a bad import in a base screen
        # used to be one line of its message, after which the screen was
        # simply absent and the game fell back to the original's picture —
        # which reads as a gap in the protocol, not as the fault it is.
        log.error("Failed to load screen '%s' (%s): %s",
                  screen_name, screen_py, e, exc_info=True)
        return None


def _forget(package_name):
    """Drop a mod package and every module imported under it."""
    for key in [k for k in sys.modules
                if k == package_name or k.startswith(package_name + ".")]:
        del sys.modules[key]


def _load_mod_package(package_name, screen_py):
    """A mod's screen folder as a package, so that what a real screen is
    made of — `from .helper import X` beside its screen.py — loads.

    Loaded as a bare file there is no parent package and the first
    relative import fails; every base screen is a package of sibling
    modules, so a mod that replaces one would have had to be a single
    file. The folder becomes the package `package_name` and screen.py its
    submodule `screen`; both leave `sys.modules` again when the import
    fails, so a second try is not answered by a half-built module."""
    folder = os.path.dirname(screen_py)
    _forget(package_name)           # a second discovery starts clean
    package = importlib.util.module_from_spec(importlib.machinery.ModuleSpec(
        package_name, None, is_package=True))
    package.__path__ = [folder]
    sub_name = package_name + ".screen"
    sys.modules[package_name] = package
    try:
        spec = importlib.util.spec_from_file_location(sub_name, screen_py)
        module = importlib.util.module_from_spec(spec)
        sys.modules[sub_name] = module
        spec.loader.exec_module(module)
    except BaseException:
        _forget(package_name)       # siblings that did import, too
        raise
    package.screen = module
    return module


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
        try:
            screen = cls(app)
        except Exception:
            # A MOD's screen whose constructor raises must not end the
            # start for the player (audit TD-10); the base screen of the
            # same name is gone too, so say which one. A BASE screen that
            # cannot be built stays loud: that is the project's own fault.
            if not cls.__module__.startswith("screens_mod_"):
                raise
            log.exception("Mod screen '%s' could not be built — skipped",
                          name)
            continue
        dispatcher.register(name, screen)
