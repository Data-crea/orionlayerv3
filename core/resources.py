"""Mod-aware resource resolution.

Every file the game loads (assets, JSON data, skins, screens)
is resolved through this module. Active mods are searched first,
in the order listed in settings.json ("active_mods"); the base
project is the final fallback.

A mod is a folder under mods/<mod_name>/ that mirrors the
project structure. To override a file, a mod ships the same
relative path:

    mods/my_mod/screens/select_race/races.json
    mods/my_mod/screens/main_menu/assets/logo.png
    mods/my_mod/assets/shared/skins/neon/...      (a whole skin)
    mods/my_mod/screens/my_screen/screen.py       (a new screen)

Rules:
  - File-level override: first mod that has the file wins.
  - Skins are resolved as whole directories (skin_dir()).
  - Writes (editor saves) always go to the base project,
    never into a mod folder.

Usage: core.resources.init(settings) once at startup, then
use the module-level helpers or the `res` singleton.
"""
import os
import json
import logging
from core.config import BASE_DIR, MODS_DIR

log = logging.getLogger("resources")


class Resources:
    """Resolves relative paths against active mods, then the base."""

    def __init__(self, active_mods=None, skin="default"):
        self.skin = skin
        self.mod_dirs = []      # absolute mod roots, in priority order
        self.mods_meta = []     # parsed mod.json per active mod

        for name in (active_mods or []):
            mod_dir = os.path.join(MODS_DIR, name)
            if not os.path.isdir(mod_dir):
                log.warning("Active mod not found: %s", name)
                continue
            self.mod_dirs.append(mod_dir)
            meta = self._read_meta(mod_dir, name)
            self.mods_meta.append(meta)
            log.info("Mod active: %s %s", meta.get("name", name),
                     meta.get("version", ""))

    @staticmethod
    def _read_meta(mod_dir, fallback_name):
        path = os.path.join(mod_dir, "mod.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (ValueError, OSError) as e:
                log.warning("Bad mod.json in %s: %s", fallback_name, e)
        return {"name": fallback_name}

    # ── Core resolution ──────────────────────────────────

    def resolve(self, relpath):
        """Return the absolute path of relpath, mods first.

        Returns None if the file exists nowhere.
        """
        for mod_dir in self.mod_dirs:
            p = os.path.join(mod_dir, relpath)
            if os.path.exists(p):
                return p
        p = os.path.join(BASE_DIR, relpath)
        return p if os.path.exists(p) else None

    def resolve_dir(self, relpath):
        """Return the first existing DIRECTORY for relpath, mods first.

        Used for resources that load as a unit (skins, frame tile
        sets). A mod overrides the whole directory or nothing.
        """
        for mod_dir in self.mod_dirs:
            p = os.path.join(mod_dir, relpath)
            if os.path.isdir(p):
                return p
        p = os.path.join(BASE_DIR, relpath)
        return p if os.path.isdir(p) else None

    # ── Convenience helpers ──────────────────────────────

    def screen_file(self, screen_name, *parts):
        """Resolve a file inside screens/<screen_name>/."""
        return self.resolve(os.path.join("screens", screen_name, *parts))

    def shared(self, *parts):
        """Resolve a file inside assets/shared/."""
        return self.resolve(os.path.join("assets", "shared", *parts))

    def skin_dir(self):
        """Absolute directory of the active skin (whole-dir override)."""
        return self.resolve_dir(
            os.path.join("assets", "shared", "skins", self.skin))

    def font(self, filename="Aldrich-Regular.ttf"):
        return self.shared("fonts", filename)

    def load_json(self, relpath, default=None):
        """Load a JSON file through mod resolution."""
        path = self.resolve(relpath)
        if not path:
            return default
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (ValueError, OSError) as e:
            log.warning("Bad JSON %s: %s", relpath, e)
            return default

    def screen_roots(self):
        """All screens/ directories, mods first, then base.

        Used by the screen loader to discover screens added by mods.
        """
        roots = [os.path.join(d, "screens") for d in self.mod_dirs]
        roots.append(os.path.join(BASE_DIR, "screens"))
        return [r for r in roots if os.path.isdir(r)]


# ── Module-level singleton ───────────────────────────────

res = Resources()  # replaced by init(); safe default (no mods)


def init(settings):
    """Initialize the global resolver from settings.json."""
    global res
    res = Resources(active_mods=settings.get("active_mods", []),
                    skin=settings.get("skin", "default"))
    return res
