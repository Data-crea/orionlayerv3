"""The player's mod folder — HD EXTENSION, work order 173, decision 72.

**ONE FOLDER, OUTSIDE THE TREE, DROP FILES IN.** Somebody who is not a
developer changes the look by putting a file with a known name into one
folder; a missing file is the default. Nothing is copied into the tree,
and the folder is never under git.

    Linux     $XDG_CONFIG_HOME/orionlayer/mod   (~/.config/orionlayer/mod)
    Windows   %APPDATA%\\OrionLayer\\mod
    macOS     ~/Library/Application Support/OrionLayer/mod

`ORIONLAYER_USER_DIR` replaces the part before `mod` (a portable
install, and the smoke test).

**ONE RESOLVER.** Nothing reads this folder but this module, and
nothing asks this module but `core.resources` (`Resources.resolve`, and
`Resources.roots` for the loaders that choose per root, `files_root`) and
the two values that are not files (`style_overrides`, `frame_colour`).
A screen asks for its default path as it always did and gets the
player's file when there is a valid one — so no screen loads around it.

**THE NAMES** (`NAMES`; the template tool writes them all out):

    background.png            the universal background
    backgrounds/<screen>.png  one screen's background — beats the universal
    hud/<piece>.png           a HUD icon or the title plate, by its name
    style.json                a PARTIAL HUD style: only the keys present
    colour.json               the default frame colour
    files/<tree path>         any other image, at its path in the tree
    texts/<screen>/<key>.txt  a text by its stable key (work order 175,
                              `core.modtexts`, decision 73)

**NEVER A CRASH, NEVER A BROKEN SCREEN.** Every file is checked before it
is handed out: an image must load, a JSON file must be an object whose
values have the default's type. A file that fails costs ONE log line and
the default is used. An image of another size than the default is scaled
to the default's size once (a copy in `cache/` beside the folder), so
every loader sees what it always saw — "scaled like the default, not
rejected". Backgrounds are the exception: they are cover-scaled to the
window anyway, so any size is fine as it is.

**OFF WITHOUT DELETING.** `user_mod` in `user_settings.json` ("on" /
"off", the GAME menu's settings row). Read at start, like every
resource choice (decision 18): switching needs a restart.

**INERT UNTIL `init`.** Only `main.App` calls `init`; the tools and the
smoke suite never see the player's folder unless they point one at it.
"""
import hashlib
import json
import logging
import os
import sys

from core import modlayout  # noqa: E402

log = logging.getLogger("usermod")

ENV = "ORIONLAYER_USER_DIR"
FOLDER = "mod"
CACHE = "cache"

#: The picture formats pygame loads everywhere OrionLayer runs.
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".bmp")

#: The names and the tree paths they stand for are `core.modlayout`'s; the
#: pieces `tree_path` and `init` need of them are named here.
UNIVERSAL = modlayout.UNIVERSAL
FILES = "files/"
FRAMES = modlayout.FRAMES
#: Slots with no file of OrionLayer's own at their tree path: a mod file
#: there ADDS the picture instead of replacing one — the frames; the
#: extracted artwork's pictures as PNG (195 §7, work order 199 D:
#: `core.blobart` and the battle's `cbart`, before a blob is decoded); and
#: the population figures — extracted from the player's MOO2 (absent in a
#: tree that was not) and with steps the tree has no file for
#: (`<name>@2x.png`, decision 50), read through `files_root`; and the
#: colony screen's surface pictures in its own format (work order 232,
#: `screens/colony/colsurface.py`), which the tree does not ship yet; and
#: the leaders' HD portraits (work orders 234 and 255,
#: `core/leaderportraits.py`, in the base pack since 255), found by their
#: number, so a picture under another name after the number is a picture,
#: not a typo — and a leader the pack has no picture for can get one; and the Leaders screen's seven picture
#: places (work order 237, `screens/leaders/ldrpics.NAMES`, held equal by
#: the leaders' smoke group), by exact name, so a misspelt one says so; and
#: the galaxy map's ship pictures (work order 311,
#: `screens/galaxy_map/shippics.SLOT`), which the base pack may fill too —
#: the transport, colony and outpost ships have no picture of their own —
#: by exact name, `all_<picture>.png` or `<colour 0-7>_<picture>.png` for
#: picture_num 0-47 (`SHIP_PICTURE_NAMES`), so a misspelt one says so.
#: And the Races screen's painted race leaders (work order 315 B,
#: `screens/races/racesleaders.py`), found by the race's number like the
#: leaders' portraits; the tree and the base pack hold none.
#: Globs relative to the tree.
SHIP_PICTURE_DIR = "screens/galaxy_map/assets/ship_pictures/"
SHIP_PICTURE_NAMES = "all_<0-47>.png or <0-7>_<0-47>.png"
SLOTS = ("screens/*/assets/frame.png",
         "screens/*/assets/gamedata/*.png",
         "assets/shared/figures/*.png",
         "screens/colony/assets/surfaces/*.png",
         "screens/leaders/assets/portraits/*/*.png",
         "screens/races/assets/leaders/*.png",
         "screens/leaders/assets/pictures/screen_background.png",
         "screens/leaders/assets/pictures/slot_[1234]_background.png",
         "screens/leaders/assets/pictures/slot_empty_background.png",
         "screens/leaders/assets/pictures/minimap_background.png",
         "screens/leaders/assets/pictures/view_background.png",
         # WO 326 E: the research panel's eight category pictures, by
         # exact name (`core/researchart.NAMES`), so a misspelt one says so
         *(f"assets/shared/research/{_n}.png" for _n in (
             "biology", "power", "physics", "construction", "force_fields",
             "chemistry", "computers", "sociology")),
         # WO 326 B: the Fleets map's picture (`screens/fleets/fltminimap`)
         "screens/fleets/assets/pictures/minimap_background.png",
         ) + tuple(f"{SHIP_PICTURE_DIR}{c}_{n}.png"
                   for c in ("all", "[0-7]")
                   for n in ("[0-9]", "[1-3][0-9]", "4[0-7]"))
#: Work order 326 F (HD EXTENSION, Data's pictures; neither tree nor base
#: pack holds one): the Space Dragon's picture in the bribe popup
#: (`core.turnpopupcontent.ART`), and the planet pictures, one per climate,
#: that every place drawing a planet but the battle takes first
#: (`screens/colony_summary/colonyplanets.PICTURE`). Exact names — the ten
#: are PLANET_CLIMATE's (`colonyplanets.NAMES`, orion2_consts.h:362-374) —
#: so a misspelt one is said, not silently unused.
PLANET_PICTURE_DIR = "screens/colony_summary/assets/planet_pictures/"
SLOTS += ("assets/shared/turnpopup/dragon_bribe.png",) + tuple(
    f"{PLANET_PICTURE_DIR}{n}.png" for n in (
        "toxic", "radiated", "barren", "desert", "tundra",
        "ocean", "swamp", "arid", "terran", "gaia"))
#: HD EXTENSION `building_pictures`: one painted picture per building
#: (`core.buildingart`), by exact name.
from core import buildingart  # noqa: E402
SLOTS += buildingart.slots()
#: HD EXTENSION `star_shape_by_size`: a class's three star pictures by
#: star.size (`galaxy_map.renderer.SIZE_DIRS`), drawn at the zoom's width.
SLOTS += tuple(f"screens/galaxy_map/assets/stars/*/{n}.png"
               for n in ("large", "medium", "small"))
#: Work order 331: the rotating planets' maps, a surface per type
#: (`<type>_surface.png`, in the base pack) and an optional cloud layer
#: (`<type>_clouds.png`, with transparency; nothing ships). Any size, 2:1,
#: so `_checked_image` never rescales them to the base map's.
PLANET_MAPS = "assets/shared/planets/"
SLOTS += (PLANET_MAPS + "*_clouds.png", PLANET_MAPS + "*_surface.png")
#: The galaxy map's ship masters (work order 243, Data's decision): a whole
#: master `files/<SHIP_MASTERS>/<kind>.png` replaces every icon cut from it
#: (`core.shipcut`: the four steps and the Planets panel's picture), cut
#: once into `cache/` and drawn as cut; a single icon under
#: `files/<SHIP_ICONS>/<kind>/<file>` still wins over the cut, because it
#: names exactly that icon. A kind with no master in the base pack (the
#: amoeba, the antaran) may get one this way.
SHIP_MASTERS = "screens/galaxy_map/assets/ships/_src"
SHIP_ICONS = "screens/galaxy_map/assets/ships"
#: The optional file a mod states its frames' layouts in (195 §3.5).
MOD_JSON = "mod.json"
#: The two files that are values, not pictures.
STYLE = "style.json"
COLOUR = "colour.json"
#: The rotating planets' values (work order 331), merged like style.json.
PLANETS = "planets.json"
#: What the template lists and MODDING.md explains, in this order.
NAMES = ("background.png", "backgrounds/<screen>.png", "hud/<piece>.png",
         "frames/<screen>.png", STYLE, COLOUR, PLANETS, "files/<path in the tree>",
         "texts/<screen>/<key>.txt")
#: The texts' folder: read by `read_text`, asked by `core.modtexts`.
TEXTS = "texts/"

#: What the template tool writes that is not read as a replacement:
#: the guide, the name list, and the starting points in `originals/`
#: (copy one up a level to use it — until then it changes nothing).
GUIDE = ("MODDING.md", "NAMES.txt")
ORIGINALS = "originals"
#: The frame templates `tools/frame_template.py` writes into the folder
#: (`templates/frames/<screen>.png`): pictures to paint over, never a
#: replacement — not scanned, so they cost no "not a name" line at every
#: start (work order 219: 22 of them); a real misnamed file still does.
TEMPLATES = "templates"

#: What `files/` lists for the template, and every other picture in the
#: tree with the reason it is not listed: `core.modart` (work order 199 D).

#: colour.json's keys and their ranges (`core.hud.tint`'s own).
COLOUR_KEYS = {"hue": (0.0, 360.0), "saturation": (0.0, 1.0),
               "brightness": (0.1, 1.6)}

_state = {"root": None, "index": {}, "checked": {}, "texts": {},
          "enabled": None, "mirror": None}


def user_dir():
    """Where OrionLayer keeps the player's things, per platform."""
    env = os.environ.get(ENV)
    if env:
        return env
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or os.path.join(
            os.path.expanduser("~"), "AppData", "Roaming")
        return os.path.join(base, "OrionLayer")
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Application Support/OrionLayer")
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, "orionlayer")


def mod_dir():
    return os.path.join(user_dir(), FOLDER)


#: F8's pictures (work order 219): in the player's own folder beside the mod
#: folder and the settings — never the working directory, which put a
#: screenshot of the game into the program's folder (and once into git).
SCREENSHOTS = "screenshots"


def screenshot_dir():
    return os.path.join(user_dir(), SCREENSHOTS)


def tree_path(name):
    """The tree path a mod file name replaces, or None if nothing does."""
    name = name.replace("\\", "/")
    laid = modlayout.to_tree(name, _screens())
    if laid is not None:
        return laid
    if name.startswith(FILES) and len(name) > len(FILES):
        rest = name[len(FILES):]
        return None if ".." in rest.split("/") else rest
    return None


_screen_set = []


def _screens():
    """The tree's screens (`core.modlayout`'s screen shortcut), once."""
    if not _screen_set:
        from core.config import BASE_DIR
        _screen_set.append(modlayout.screen_names(BASE_DIR))
    return _screen_set[0]


def init(enabled=True, root=None):
    """Index the folder once. Returns the number of files that will be
    used; every file that will not says why, once."""
    _state.update(root=None, index={}, checked={}, texts={}, mirror=None,
                  enabled=bool(enabled),
                  # a number, not an address: a freed index's id can be
                  # reused by the next one (work order 326 review)
                  generation=_state.get("generation", 0) + 1)
    from core import buildingart
    buildingart.forget()
    root = root or mod_dir()
    if not enabled:
        log.info("mod folder switched off (user_mod: off) — defaults only; "
                 "%s is left as it is", root)
        return 0
    if not os.path.isdir(root):
        log.info("no mod folder at %s — defaults only", root)
        return 0
    _state["root"] = root
    from core.config import BASE_DIR
    by_layout = set()
    for dirpath, _dirs, files in os.walk(root):
        _dirs.sort()
        for f in sorted(files):
            full = os.path.join(dirpath, f)
            name = os.path.relpath(full, root).replace(os.sep, "/")
            if (name in (STYLE, COLOUR, PLANETS, MOD_JSON) or name in GUIDE
                    or name.startswith((ORIGINALS + "/", TEMPLATES + "/"))
                    or _is_notice(name)):
                continue
            if name.startswith(TEXTS):
                if not name.endswith(".txt"):
                    log.warning("mod: %s — a text is a .txt file — ignored",
                                name)
                continue
            target = tree_path(name)
            if target is None or not name.lower().endswith(IMAGE_EXT):
                log.warning("mod: %s is not a name OrionLayer looks for — "
                            "ignored", name)
                continue
            if not _known(name, target, BASE_DIR):
                continue
            laid = modlayout.to_tree(name, _screens()) is not None
            if ((laid and not modlayout.direct(name))
                    or name.startswith(FILES)) and \
                    not fills_a_picture(target):
                log.warning("mod: %s replaces nothing (no %s in OrionLayer) "
                            "— ignored%s", name, target,
                            f"; the map's ship pictures are named "
                            f"{SHIP_PICTURE_NAMES}"
                            if target.startswith(SHIP_PICTURE_DIR) else "")
                continue
            if name.startswith("files/") and modlayout.themed(target):
                log.info("mod: %s still works; the name is now %s",
                         name, modlayout.from_tree(target, _screens()))
            if target in _state["index"]:
                # one picture, two names: the new name wins; two NEW names
                # keep the first in name order, so the choice never depends
                # on the disk's order
                other = os.path.relpath(_state["index"][target], root)
                log.warning("mod: %s and %s fill the same picture — %s is "
                            "used", name, other,
                            name if laid and target not in by_layout
                            else other)
                if not laid or target in by_layout:
                    continue
            if laid:
                by_layout.add(target)
            _state["index"][target] = full
    _build_mirror(root)
    log.info("mod folder %s: %d file(s) in use", root, len(_state["index"]))
    return len(_state["index"])


def _build_mirror(root):
    """The folder's pictures at their TREE paths, in `cache/` beside it —
    the resource root of the loaders that join a root and a tree path
    (`files_root`). The folder's own names are the modder's and no longer
    mirror the tree (`core.modlayout`), so the tree-shaped copy is made
    here, by link where the platform allows and by copy where not, anew
    at every start."""
    import shutil
    base = os.path.join(os.path.dirname(root), CACHE, FOLDER, "tree")
    shutil.rmtree(base, ignore_errors=True)
    # what the loaders always saw: every file under `files/`, indexed or
    # not (a loader may name a file the index has no slot for) ...
    links = {}
    legacy = os.path.join(root, "files")
    for dirpath, _dirs, names in os.walk(legacy):
        for f in names:
            full = os.path.join(dirpath, f)
            links[os.path.relpath(full, legacy).replace(os.sep, "/")] = full
    # ... and over it the folder's own names, at their tree paths
    links.update(_state["index"])
    for target, src in sorted(links.items()):
        out = os.path.join(base, *target.split("/"))
        if os.path.lexists(out):
            # two paths that differ only in case on a case-insensitive disk:
            # the first stays, and the player's file is never written to
            log.warning("mod: %s is the same file as another name here — "
                        "left out", target)
            continue
        try:
            os.makedirs(os.path.dirname(out), exist_ok=True)
            try:
                # absolute: a relative target would be read from the link's
                # own folder
                os.symlink(os.path.abspath(src), out)
            except (OSError, NotImplementedError):
                shutil.copyfile(src, out)
        except OSError as err:
            log.warning("mod: %s cannot be offered to the loaders (%s)",
                        target, err)
    _state["mirror"] = base if os.path.isdir(base) else None


def fills_a_picture(target):
    """True when a mod file at the tree path `target` replaces or adds a
    picture OrionLayer asks for: the tree has it, it is a slot, the base
    pack has it, or it is a ship master. What `init` indexes, and what
    `tools/mod_migrate.py` holds a file to before it moves it."""
    from core.config import BASE_DIR
    return (os.path.exists(os.path.join(BASE_DIR, target))
            or is_slot(target) or _in_base_pack(target)
            or target.startswith(SHIP_MASTERS + "/"))


def files_root():
    """The folder's pictures as a RESOURCE ROOT shaped like the tree, or
    None (work order 199 D, 195 §11.1; since 336 built from the index by
    `_build_mirror`, whatever names the files have): a loader that
    chooses between file forms per source root (`Resources.roots`, decision 50's master-or-step
    — the colony screens' figures, planet discs, surfaces and output icons)
    tries it first. Such a loader checks a file's size itself and refuses a
    wrong one (decision 50) — it is not scaled here."""
    return _state.get("mirror") if _state["root"] else None


def is_slot(target):
    """A tree path a mod file may fill although OrionLayer has no file
    there (`SLOTS`)."""
    import fnmatch
    return any(fnmatch.fnmatchcase(target, g) for g in SLOTS)


def frame_layouts():
    """mod.json's `{"frames": {"<screen>": "<layout hash>"}}`, or {}."""
    data = _read_json(MOD_JSON) or {}
    frames = data.get("frames")
    return {str(k): str(v) for k, v in frames.items()} \
        if isinstance(frames, dict) else {}


def _is_notice(name):
    """A mod's README or LICENSE travels with its pictures (WO 241: the leader
    portraits became a mod in this folder) and is read by people only."""
    return os.path.basename(name).upper().startswith(("README", "LICENSE"))


def _in_base_pack(target):
    """A default picture lives in the base pack, not the tree, since work
    order 241; `basepack.json` names it even where no pack is installed,
    and a picture the maintainer added to the pack counts before the
    manifest follows (work order 242: no manual step for a new picture)."""
    from core import basepack
    if os.path.isfile(os.path.join(basepack.base_dir(), target)):
        return True
    try:
        return target in basepack.manifest()["files"]
    except (OSError, ValueError):
        return False


def _known(name, target, base):
    """A background or HUD piece name OrionLayer asks for; a typo says so."""
    stem = os.path.splitext(os.path.basename(target))[0]
    if name.startswith("backgrounds/"):
        if stem == "universal" or os.path.isfile(
                os.path.join(base, "screens", stem, "screen.py")):
            return True
        log.warning("mod: %s — there is no screen called %s — ignored",
                    name, stem)
        return False
    if name.startswith(FRAMES):
        stem = os.path.splitext(os.path.basename(name))[0]
        if os.path.isfile(os.path.join(base, "screens", stem, "screen.py")):
            return True
        log.warning("mod: %s — there is no screen called %s — ignored",
                    name, stem)
        return False
    if target.startswith(SHIP_MASTERS + "/"):
        from core import shipcut
        if stem in shipcut.KINDS:
            return True
        log.warning("mod: %s — there is no ship kind called %s (%s) — "
                    "ignored", name, stem, ", ".join(shipcut.KINDS))
        return False
    if name.startswith("hud/"):
        from core.hud import art
        if stem in art.PIECES:
            return True
        log.warning("mod: %s — there is no HUD piece called %s — ignored",
                    name, stem)
        return False
    return True


def active():
    """True when a folder was found and is switched on."""
    return _state["root"] is not None


def started_enabled():
    """Whether this run started with the folder switched on; None when
    `init` never ran (the tools and the suite)."""
    return _state["enabled"]


def targets(pattern):
    """The tree paths the folder fills that match the glob `pattern`, in
    order: what a window may offer (work order 220, the livery's ships and
    masks), asked of the index `init` built, never of the disk."""
    import fnmatch
    return sorted(t for t in _state["index"]
                  if fnmatch.fnmatchcase(t, pattern))


def in_use():
    """How many of the folder's files are in use (the settings row):
    its pictures, style.json and colour.json where present, and its
    text files (counted as present; a bad one says so when first asked)."""
    root = _state["root"]
    if root is None:
        return 0
    texts = 0
    for _dir, _sub, files in os.walk(os.path.join(root, TEXTS)):
        texts += sum(f.endswith(".txt") for f in files)
    return len(_state["index"]) + texts + sum(
        os.path.exists(os.path.join(root, n)) for n in (STYLE, COLOUR, PLANETS))


def read_text(name, max_bytes):
    """The player's text file `name` (under `texts/`) as a str, or None.
    Absent: None, silently. Unreadable, not UTF-8, empty or larger than
    `max_bytes`: ONE log line per file per run, then None (the caller's
    default)."""
    root = _state["root"]
    if root is None or not name.startswith(TEXTS) or ".." in name.split("/"):
        return None
    if name in _state["texts"]:
        return _state["texts"][name]
    path = os.path.join(root, *name.split("/"))
    value = None
    if os.path.isfile(path):
        try:
            if os.path.getsize(path) > max_bytes:
                raise ValueError(f"larger than {max_bytes} bytes")
            with open(path, "rb") as fh:
                raw = fh.read()
            value = raw.decode("utf-8-sig").replace("\r\n", "\n")
            if value.endswith("\n"):
                value = value[:-1]
            if not value.strip():
                raise ValueError("empty")
        except (OSError, UnicodeDecodeError, ValueError) as err:
            log.warning("mod: %s cannot be used (%s) — the default text is "
                        "used", name, err)
            value = None
    _state["texts"][name] = value
    return value


def shutdown():
    """Back to never-initialised: the smoke suite, after a check."""
    _state.update(root=None, index={}, checked={}, texts={}, enabled=None,
                  mirror=None)


def override(relpath, default_path):
    """The player's file for `relpath`, checked and sized, or None."""
    if not _state["index"]:
        return None
    key = relpath.replace(os.sep, "/")
    src = _state["index"].get(key)
    if src is None:
        return _ship_cut(key)
    if key not in _state["checked"]:
        _state["checked"][key] = _checked_image(key, src, default_path)
    return _state["checked"][key]


def _ship_cut(key):
    """An icon cut from the mod folder's master of its kind, or None.

    Made once per master (the cache is keyed by the master's bytes) and
    handed out as cut: the cut is the shipped icons' own rule, so it is
    not scaled to the default's size the way a single picture is."""
    head, _, rest = key.partition(SHIP_ICONS + "/")
    if head or "/" not in rest or rest.startswith("_src/"):
        return None
    kind, file = rest.split("/", 1)
    master = _state["index"].get(f"{SHIP_MASTERS}/{kind}.png")
    if master is None:
        return None
    if key in _state["checked"]:
        return _state["checked"][key]
    from core import shipcut
    name = os.path.relpath(master, _state["root"]).replace(os.sep, "/")
    try:
        with open(master, "rb") as handle:
            digest = hashlib.sha1(handle.read()).hexdigest()[:16]
        folder = os.path.join(os.path.dirname(_state["root"]), CACHE, FOLDER,
                              f"ships_{digest}", kind)
        if not all(os.path.isfile(os.path.join(folder, f))
                   for f in shipcut.files(kind)):
            os.makedirs(folder, exist_ok=True)
            for f, img in shipcut.cut(master, kind).items():
                img.save(os.path.join(folder, f))
            log.info("mod: %s — every %s icon cut from it (%s)", name, kind,
                     ", ".join(shipcut.files(kind)))
    except (OSError, ValueError) as err:
        log.warning("mod: %s cannot be cut (%s) — the default is used",
                    name, err)
        for f in shipcut.files(kind):
            if f"{SHIP_ICONS}/{kind}/{f}" not in _state["index"]:
                _state["checked"][f"{SHIP_ICONS}/{kind}/{f}"] = None
        return None
    for f in shipcut.files(kind):
        icon = f"{SHIP_ICONS}/{kind}/{f}"
        if icon not in _state["index"]:     # a single icon keeps its own
            _state["checked"][icon] = os.path.join(folder, f)
    return _state["checked"].get(key)


def _checked_image(key, src, default_path):
    import pygame
    name = os.path.relpath(src, _state["root"]).replace(os.sep, "/")
    try:
        img = pygame.image.load(src)
        if img.get_width() < 1 or img.get_height() < 1:
            raise ValueError("empty picture")
    except (pygame.error, ValueError, OSError) as err:
        log.warning("mod: %s cannot be read (%s) — the default is used",
                    name, err)
        return None
    if key.startswith(("assets/shared/backgrounds/", PLANET_MAPS)) \
            or not default_path:
        return src
    try:
        want = pygame.image.load(default_path).get_size()
    except (pygame.error, OSError):
        return src
    if img.get_size() == want:
        return src
    return _resized(name, src, img, want)


def _resized(name, src, img, want):
    """The picture at the default's size, made once and kept."""
    import pygame
    with open(src, "rb") as handle:
        digest = hashlib.sha1(handle.read()).hexdigest()[:16]
    # BESIDE THE FOLDER IN USE, never a fixed place: the smoke suite's
    # temporary folder must not write into the player's own directory.
    out = os.path.join(os.path.dirname(_state["root"]), CACHE, FOLDER,
                       f"{digest}_{want[0]}x{want[1]}.png")
    if not os.path.exists(out):
        rgba = pygame.Surface(img.get_size(), pygame.SRCALPHA, 32)
        rgba.blit(img, (0, 0))
        try:
            os.makedirs(os.path.dirname(out), exist_ok=True)
            pygame.image.save(pygame.transform.smoothscale(rgba, want), out)
        except (OSError, pygame.error) as err:
            log.warning("mod: %s could not be resized (%s) — the default "
                        "is used", name, err)
            return None
    log.info("mod: %s is %dx%d, the default %dx%d — scaled to fit", name,
             img.get_width(), img.get_height(), *want)
    return out


def _read_json(name):
    if _state["root"] is None:
        return None
    path = os.path.join(_state["root"], name)
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            raise ValueError("not a { ... } object")
        return data
    except (OSError, ValueError) as err:
        log.warning("mod: %s cannot be read (%s) — the default is used",
                    name, err)
        return None


def _same_kind(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool)
    if isinstance(a, (int, float)):
        return isinstance(b, (int, float))
    if isinstance(a, list):
        return (isinstance(b, list) and len(a) == len(b)
                and all(_same_kind(x, y) for x, y in zip(a, b)))
    return type(a) is type(b)


def merge(default, partial, where="", name=STYLE):
    """`default` with every key of `partial` that exists there and has
    the same kind of value; each key that does not is named once and
    skipped. Neither argument is changed."""
    out = dict(default)
    for key, value in partial.items():
        path = f"{where}{key}"
        if key not in default:
            log.warning("mod: %s has no key %s — skipped", name, path)
        elif isinstance(default[key], dict):
            if isinstance(value, dict):
                out[key] = merge(default[key], value, path + ".", name)
            else:
                log.warning("mod: %s key %s must be a group { ... } — "
                            "skipped", name, path)
        elif _same_kind(default[key], value):
            out[key] = value
        else:
            log.warning("mod: %s key %s is %r, the default is %r — skipped",
                        name, path, value, default[key])
    return out


def style_overrides(default):
    """The HUD style with the player's partial style.json over it."""
    partial = _read_json(STYLE)
    return merge(default, partial) if partial else default


def planet_overrides(default):
    """The rotating planets' values with the player's partial
    `planets.json` over them (work order 331, `core.planetspin`)."""
    partial = _read_json(PLANETS)
    return merge(default, partial, name=PLANETS) if partial else default


def frame_colour():
    """{hue, saturation, brightness} from colour.json; a key that is
    absent, null or out of range is the measured value (None)."""
    data = _read_json(COLOUR) or {}
    out = {}
    for key, (lo, hi) in COLOUR_KEYS.items():
        v = data.get(key)
        if v is not None and (isinstance(v, bool) or
                              not isinstance(v, (int, float))
                              or not lo <= v <= hi):
            log.warning("mod: %s %s is %r, not a number from %g to %g — "
                        "the default is used", COLOUR, key, v, lo, hi)
            v = None
        out[key] = v
    return out
