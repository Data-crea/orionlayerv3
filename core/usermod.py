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
nothing asks this module but `core.resources` (`Resources.resolve`) and
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

log = logging.getLogger("usermod")

ENV = "ORIONLAYER_USER_DIR"
FOLDER = "mod"
CACHE = "cache"

#: The picture formats pygame loads everywhere OrionLayer runs.
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".bmp")

#: Mod name (or prefix) -> the tree path it replaces.
UNIVERSAL = "assets/shared/backgrounds/universal.png"
PREFIXES = (("backgrounds/", "assets/shared/backgrounds/"),
            ("hud/", "assets/shared/hud/cut/"),
            ("files/", ""))
SINGLES = {"background.png": UNIVERSAL}
#: The two files that are values, not pictures.
STYLE = "style.json"
COLOUR = "colour.json"
#: What the template lists and MODDING.md explains, in this order.
NAMES = ("background.png", "backgrounds/<screen>.png", "hud/<piece>.png",
         STYLE, COLOUR, "files/<path in the tree>")

#: What the template tool writes that is not read as a replacement:
#: the guide, the name list, and the starting points in `originals/`
#: (copy one up a level to use it — until then it changes nothing).
GUIDE = ("MODDING.md", "NAMES.txt")
ORIGINALS = "originals"

#: The groups of pictures `files/` replaces that the screens are KNOWN
#: to ask for through `Resources.resolve` (a trace of every screen's
#: render, work order 173). Globs relative to the tree. Their pictures
#: are MOO2's or derived from them: the template lists the names only.
GAME_ART = ("screens/custom_race/assets/*.png",
            "screens/empire_identity/assets/*.png",
            "screens/galaxy_map/assets/black_hole.png",
            "screens/galaxy_map/assets/icons/*.png",
            "screens/galaxy_map/assets/nebula/*.png",
            "screens/galaxy_map/assets/ships/*/*.png",
            "screens/galaxy_map/assets/stars/*/*.png",
            "screens/main_menu/assets/logo.png",
            "screens/new_game/assets/*/*.png",
            "screens/select_race/assets/portraits/*.png")

#: colour.json's keys and their ranges (`core.hud.tint`'s own).
COLOUR_KEYS = {"hue": (0.0, 360.0), "saturation": (0.0, 1.0),
               "brightness": (0.1, 1.6)}

_state = {"root": None, "index": {}, "checked": {}, "enabled": None}


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


def tree_path(name):
    """The tree path a mod file name replaces, or None if nothing does."""
    name = name.replace("\\", "/")
    if name in SINGLES:
        return SINGLES[name]
    for prefix, target in PREFIXES:
        if name.startswith(prefix) and len(name) > len(prefix):
            rest = name[len(prefix):]
            if prefix == "files/" and ".." in rest.split("/"):
                return None
            return target + rest
    return None


def init(enabled=True, root=None):
    """Index the folder once. Returns the number of files that will be
    used; every file that will not says why, once."""
    _state.update(root=None, index={}, checked={}, enabled=bool(enabled))
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
    for dirpath, _dirs, files in os.walk(root):
        for f in sorted(files):
            full = os.path.join(dirpath, f)
            name = os.path.relpath(full, root).replace(os.sep, "/")
            if (name in (STYLE, COLOUR) or name in GUIDE
                    or name.startswith(ORIGINALS + "/")):
                continue
            target = tree_path(name)
            if target is None or not name.lower().endswith(IMAGE_EXT):
                log.warning("mod: %s is not a name OrionLayer looks for — "
                            "ignored", name)
                continue
            if not _known(name, target, BASE_DIR):
                continue
            if name.startswith("files/") and not os.path.exists(
                    os.path.join(BASE_DIR, target)):
                log.warning("mod: %s replaces nothing (no %s in OrionLayer) "
                            "— ignored", name, target)
                continue
            _state["index"][target] = full
    log.info("mod folder %s: %d file(s) in use", root, len(_state["index"]))
    return len(_state["index"])


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


def in_use():
    """How many of the folder's files are in use (the settings row):
    its pictures, and style.json and colour.json where present."""
    root = _state["root"]
    if root is None:
        return 0
    return len(_state["index"]) + sum(
        os.path.exists(os.path.join(root, n)) for n in (STYLE, COLOUR))


def shutdown():
    """Back to never-initialised: the smoke suite, after a check."""
    _state.update(root=None, index={}, checked={}, enabled=None)


def override(relpath, default_path):
    """The player's file for `relpath`, checked and sized, or None."""
    if not _state["index"]:
        return None
    key = relpath.replace(os.sep, "/")
    src = _state["index"].get(key)
    if src is None:
        return None
    if key not in _state["checked"]:
        _state["checked"][key] = _checked_image(key, src, default_path)
    return _state["checked"][key]


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
    if key.startswith("assets/shared/backgrounds/") or not default_path:
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


def merge(default, partial, where=""):
    """`default` with every key of `partial` that exists there and has
    the same kind of value; each key that does not is named once and
    skipped. Neither argument is changed."""
    out = dict(default)
    for key, value in partial.items():
        path = f"{where}{key}"
        if key not in default:
            log.warning("mod: %s has no key %s — skipped", STYLE, path)
        elif isinstance(default[key], dict):
            if isinstance(value, dict):
                out[key] = merge(default[key], value, path + ".")
            else:
                log.warning("mod: %s key %s must be a group { ... } — "
                            "skipped", STYLE, path)
        elif _same_kind(default[key], value):
            out[key] = value
        else:
            log.warning("mod: %s key %s is %r, the default is %r — skipped",
                        STYLE, path, value, default[key])
    return out


def style_overrides(default):
    """The HUD style with the player's partial style.json over it."""
    partial = _read_json(STYLE)
    return merge(default, partial) if partial else default


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
