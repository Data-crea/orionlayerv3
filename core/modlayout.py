"""The names of the player's mod folder — HD EXTENSION `mod_layout`, work
order 336 (Data, 27 October 2026: "we need one structure here").

A modder must never have to know OrionLayer's folder tree. Until 336 the
folder held a few flat names (`backgrounds/`, `hud/`, `frames/`) and, for
everything else, `files/<path in the tree>` — `files/screens/colony/assets/
surfaces/terran.png` — so the program's own layout was the modder's
interface, the same picture lived under a different kind of path on each
screen, and one subject (the planets, the ships, the buildings) was spread
over several screens' folders.

THE RULE, stated once (and in `MODDING.md`):

  * a picture that SEVERAL screens draw lives under its SUBJECT:
    `buildings/`, `ships/`, `planets/`, `landscapes/`, `stars/`, `leaders/`,
    `races/`, `research/`, `popups/`, `fleets/`;
  * a picture that belongs to ONE screen lives under that SCREEN's name,
    the path below its `assets/` folder: `new_game/difficulty/…`,
    `select_race/portraits/…`, `galaxy_map/nebula/…`;
  * `shared/<path>` is the program's `assets/shared/<path>`;
  * `background.png`, `backgrounds/`, `frames/`, `hud/`, `texts/` and the
    three `.json` files are as they were.

`files/<path in the tree>` is still read, for every picture, so no mod made
before 336 breaks — it is the advanced way and the template no longer
teaches it. Where both names fill one picture, the new name wins and the
log says so.

The tree does not move: this module only translates a mod file's name into
the tree path `core.usermod` indexes (`to_tree`), and back (`from_tree`,
for `tools/mod_migrate.py` and the log's "use … instead"). No loader knows
the new names.
"""
import os
import re

#: The universal background, a file of the base pack.
UNIVERSAL = "assets/shared/backgrounds/universal.png"

#: (mod folder, tree folder): a prefix is replaced by a prefix, the rest of
#: the name is kept. The SUBJECT folders. Order does not matter: no mod
#: folder here starts with another.
FOLDERS = (
    # leaders: the portraits are found by NUMBER (`core.leaderportraits`),
    # so `<nn>_<anything>.png`; the skill icons and the screen's pictures by
    # exact name
    ("leaders/colony/", "screens/leaders/assets/portraits/colony_leaders/"),
    ("leaders/officers/", "screens/leaders/assets/portraits/ship_officers/"),
    ("leaders/skill_icons/", "screens/leaders/assets/gamedata/officer/"),
    ("leaders/screen/", "screens/leaders/assets/pictures/"),
    ("races/leaders/", "screens/races/assets/leaders/"),
    ("research/", "assets/shared/research/"),
    ("popups/", "assets/shared/turnpopup/"),
    # the look: a screen's own background and the HUD pieces
    ("backgrounds/", "assets/shared/backgrounds/"),
    ("hud/", "assets/shared/hud/cut/"),
    # the planets: three different things, three folders
    ("landscapes/colony/", "screens/colony/assets/surfaces/"),
    ("landscapes/colonies_list/", "screens/colony_summary/assets/surfaces/"),
    ("planets/pictures/", "screens/colony_summary/assets/planet_pictures/"),
    ("planets/maps/", "assets/shared/planets/"),
    # the ships: the map's pictures per colour, the masters, single icons,
    # and the battle's stored drawings
    ("ships/map/", "screens/galaxy_map/assets/ship_pictures/"),
    ("ships/masters/", "screens/galaxy_map/assets/ships/_src/"),
    ("ships/icons/", "screens/galaxy_map/assets/ships/"),
    ("ships/battle/", "screens/combat/assets/gamedata/cmbtshp/"),
    ("stars/", "screens/galaxy_map/assets/stars/"),
)
#: One file with a name of its own on each side.
SINGLES = (
    ("races/eliminated.png", "screens/races/assets/gamedata/eliminated_0.png"),
    # a single, not a folder: `fleets/` is a screen, whose other pictures
    # keep the screen shortcut
    ("fleets/minimap_background.png",
     "screens/fleets/assets/pictures/minimap_background.png"),
    ("background.png", UNIVERSAL),
)
#: A screen's frame (work order 197 E): `frames/<screen>.png` over the
#: screen, drawn by `core.frameslot`.
FRAMES = "frames/"
FRAME_TREE = "screens/{screen}/assets/frame.png"
#: The names whose own rules (`usermod._known`: a screen or a piece that
#: exists, a typo says so) replace the "does the tree have this picture"
#: test — they may ADD a picture, so no file of the tree stands behind them.
DIRECT = ("backgrounds/", "hud/", FRAMES)
#: The buildings: `buildings/<nn>_<anything>.png`, the NUMBER decides
#: (`core.buildingart`, techdata.cpp:25-74), like the leaders' portraits.
BUILDINGS = "buildings/"
_NUMBERED = re.compile(r"^(\d{1,2})_[^/]*$")

#: First segments with a subject folder: a screen of the same name (leaders,
#: races, fleets) is NOT also a screen shortcut, or one picture would have
#: two names.
SUBJECTS = frozenset(
    {f[0].split("/")[0] for f in FOLDERS} | {"buildings", "races"})
#: (a subject folder that is also a screen name — leaders, races — keeps the
#: screen shortcut for what no subject name covers, and `themed` refuses the
#: rest, so no picture has two names)
#: The tree folders that have a subject name: the screen shortcut refuses
#: them (one name per picture) and says which name to use.
_THEMED_TREE = tuple(t for _m, t in FOLDERS) + tuple(
    t for _m, t in SINGLES)


def to_tree(name, screens=None):
    """The tree path the mod file `name` (relative, `/`) fills, or None.

    `screens` is the set of screen names (a folder of `screens/`), asked
    for the screen shortcut; None skips the shortcut (the callers that only
    want the subject folders). Nothing here checks that the tree HAS the
    file: `core.usermod` does, by the rule it always applied to `files/`."""
    name = name.replace("\\", "/")
    if ".." in name.split("/"):
        return None
    for mod, tree in SINGLES:
        if name == mod:
            return tree
    if name.startswith(FRAMES) and name.count("/") == 1:
        stem = os.path.splitext(name[len(FRAMES):])[0]
        return FRAME_TREE.format(screen=stem) if stem else None
    if name.startswith(BUILDINGS) and name.count("/") == 1:
        from core import buildingart
        found = _NUMBERED.match(name[len(BUILDINGS):])
        return buildingart.tree_path(int(found.group(1))) if found else None
    for mod, tree in FOLDERS:
        if name.startswith(mod) and len(name) > len(mod):
            rest = name[len(mod):]
            # `ships/icons/_src/…` would be a second name for the masters
            if mod == "ships/icons/" and rest.startswith("_src/"):
                return None
            return tree + rest
    if name.startswith("shared/") and len(name) > 7:
        tree = "assets/shared/" + name[7:]
        return None if themed(tree) else tree
    first, _, rest = name.partition("/")
    if screens and rest and first in screens:
        tree = f"screens/{first}/assets/{rest}"
        return None if themed(tree) else tree
    return None


def from_tree(target, screens=()):
    """The new name of the tree path `target`, or None when it keeps only
    its `files/` name — what `tools/mod_migrate.py` moves a file to."""
    got = re.fullmatch(r"screens/([^/]+)/assets/frame\.png", target)
    if got:
        return FRAMES + got.group(1) + ".png"
    if target.startswith("screens/colony/assets/buildings/"):
        got = re.match(r"(\d\d)_[^/]*\.png$", target.rsplit("/", 1)[-1])
        return BUILDINGS + target.rsplit("/", 1)[-1] if got else None
    for mod, tree in SINGLES:
        if target == tree:
            return mod
    # the longest tree folder first: ships/ is inside galaxy_map/assets/
    for mod, tree in sorted(FOLDERS, key=lambda f: -len(f[1])):
        if target.startswith(tree) and len(target) > len(tree):
            return mod + target[len(tree):]
    if target.startswith("assets/shared/") and len(target) > 14:
        return "shared/" + target[14:]
    parts = target.split("/", 3)
    if len(parts) == 4 and parts[0] == "screens" and parts[2] == "assets" \
            and parts[1] in screens:
        return f"{parts[1]}/{parts[3]}"
    return None


def themed(target):
    """True when `target` has a subject name — the screen shortcut and the
    `files/` route say 'use the subject name' for it."""
    return target.startswith(_THEMED_TREE) or target.startswith(
        "screens/colony/assets/buildings/") or bool(
        re.fullmatch(r"screens/[^/]+/assets/frame\.png", target))


def direct(name):
    """True when `name` is one of the looks (`DIRECT`, `background.png`):
    its own checks apply, not the tree's."""
    return name == "background.png" or name.startswith(DIRECT)


#: Tree pictures a mod fills only under their `files/` name, with the
#: reason — a glob to a sentence. Empty since work order 336 named every
#: picture; the check (090zzzzzzx) holds the list to the tree both ways, so
#: a picture added later must get a name or be written here.
FILES_ONLY = {}


def unnamed(tree_paths, screens):
    """Of the tree paths, those with no new name that are not on
    `FILES_ONLY`: the check's answer and `tools/mod_template.py`'s guard."""
    import fnmatch
    return sorted(p for p in tree_paths
                  if from_tree(p, screens) is None and not any(
                      fnmatch.fnmatchcase(p, g) for g in FILES_ONLY))


def tree_pictures(base):
    """Every picture a mod could fill by its tree path: the images under
    `screens/` and `assets/` of the tree at `base` and the base pack's
    manifest (whose files may not be installed in a clone), as tree paths."""
    from core import basepack
    ext = (".png", ".jpg", ".jpeg", ".bmp")
    found = set()
    for top in ("screens", "assets"):
        for folder, dirs, names in os.walk(os.path.join(base, top)):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for f in names:
                if f.lower().endswith(ext):
                    found.add(os.path.relpath(
                        os.path.join(folder, f), base).replace(os.sep, "/"))
    try:
        found |= {p for p in basepack.manifest()["files"]
                  if p.lower().endswith(ext)}
    except (OSError, ValueError):
        pass
    return found


def screen_names(base):
    """The screens of the tree rooted at `base`, as a set."""
    folder = os.path.join(base, "screens")
    try:
        return {d for d in os.listdir(folder)
                if os.path.isfile(os.path.join(folder, d, "screen.py"))}
    except OSError:
        return set()
