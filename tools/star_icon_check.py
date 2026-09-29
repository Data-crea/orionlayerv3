"""Report which file each star sprite step actually resolves to.

    python tools/star_icon_check.py

Answers "why am I still seeing the old stars?" without guessing.
For every spectral class it prints the resolved path per step 0..5,
marks whether it is a numbered sprite or a legacy fallback, and
flags the three things that make new artwork not show up:

  MOD      an active mod ships its own stars/ and wins over the base
  LEGACY   the numbered file is missing, so the old artwork is used
  STALE    a __pycache__ entry is newer than its source .py

The renderer picks sprites with star_step() = clamp(zoom + size, 0, 5)
(HAROLD::Map_Scale_Star_Size_To_Zoom_Level_), so a class showing
LEGACY on some steps and numbered files on others will visibly
change look as you zoom.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import config, resources  # noqa: E402
from core import zoomtables as zt  # noqa: E402
from screens.galaxy_map import renderer as rnd  # noqa: E402

SCREEN = "galaxy_map"
WATCH = ("screens/galaxy_map/renderer.py", "screens/galaxy_map/screen.py")


def check_pycache():
    """A .pyc newer than its .py means the interpreter may still be
    running last week's renderer (project lesson: check __pycache__)."""
    stale = []
    for rel in WATCH:
        src = os.path.join(config.BASE_DIR, rel)
        if not os.path.exists(src):
            continue
        cache = os.path.join(os.path.dirname(src), "__pycache__")
        if not os.path.isdir(cache):
            continue
        stem = os.path.basename(src)[:-3]
        for entry in os.listdir(cache):
            if entry.startswith(stem + ".") and entry.endswith(".pyc"):
                pyc = os.path.join(cache, entry)
                if os.path.getmtime(pyc) > os.path.getmtime(src):
                    stale.append((rel, entry))
    return stale


def main():
    settings = config.load_settings()
    res = resources.Resources(settings.get("active_mods", []),
                              settings.get("skin", "default"))
    print(f"base   : {config.BASE_DIR}")
    print(f"mods   : {res.mod_dirs or 'none active'}")

    # The renderer on disk may predate the six-step lookup. Say so
    # plainly — an AttributeError here reads like a script bug when
    # it actually means the update never landed.
    if not hasattr(rnd, "STEP_COUNT"):
        print("\n  OLD RENDERER: screens/galaxy_map/renderer.py has no"
              " STEP_COUNT.")
        print("  It still picks sprites by star.size alone, so the"
              " numbered PNGs")
        print("  are never requested. The six-step update did not land"
              " — re-copy")
        print("  renderer.py and screen.py, then run this again.")
        return

    print(f"steps  : {rnd.STEP_COUNT}   native px {zt.STAR_FIELDS_DIM}\n")

    missing = legacy = 0
    for folder in rnd.CLASS_DIRS.values():
        marks = []
        for step in range(rnd.STEP_COUNT):
            path = res.screen_file(SCREEN, "assets", "stars", folder,
                                   f"{step}.png")
            if path:
                where = "MOD" if any(path.startswith(m)
                                     for m in res.mod_dirs) else "ok"
            else:
                fb = rnd.LEGACY_FOR_STEP[step]
                path = res.screen_file(SCREEN, "assets", "stars", folder,
                                       f"{fb}.png")
                where = f"LEGACY->{fb}" if path else "MISSING"
                legacy += path is not None
                missing += path is None
            marks.append(f"{step}:{where}")
        print(f"  {folder:7s} " + "  ".join(marks))

    stale = check_pycache()
    print()
    if stale:
        for rel, entry in stale:
            print(f"  STALE  {entry} is newer than {rel}")
        print("  -> rm -rf screens/galaxy_map/__pycache__")
    if legacy:
        print(f"  {legacy} step(s) fell back to legacy artwork —"
              " the numbered PNGs did not land.")
    if missing:
        print(f"  {missing} step(s) resolve to nothing at all.")
    if not (stale or legacy or missing):
        print("  All steps resolve to numbered sprites in the base project.")


if __name__ == "__main__":
    main()
