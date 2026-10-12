"""The base pack: OrionLayer's own pictures, outside the repository — work
order 241 (Data's rule of 11 October 2026: code and pictures fully apart).

The public repository holds no picture. Every picture the screens draw by
default lives in one folder outside the tree, at the path it had in the
tree (`assets/shared/banner/banner_cloth.png`, `screens/<screen>/assets/…`),
so no screen changes what it asks for:

    Linux     $XDG_DATA_HOME/orionlayer/base   (~/.local/share/orionlayer/base)
    Windows   %LOCALAPPDATA%\\OrionLayer\\base
    macOS     ~/Library/Application Support/OrionLayer/base

`ORIONLAYER_BASE_DIR` replaces the whole path (a portable install, a fresh
clone, the smoke suite). It is NOT under `ORIONLAYER_USER_DIR` on purpose:
the suite and the clone checks give the player's folder a throwaway path,
and the pack must still be the installed one.

**THE MANIFEST DESCRIBES THE SHIPPED PACK.** `basepack.json` in the tree
names every file of the pack with its size and sha256 — text, so the
repository knows which pictures a pack holds without holding one. It is
not a lock on the maintainer's working copy (Data, work order 242: he
swaps pictures daily, with no manual step): the start asks only that every
named file is THERE (`missing`, `problems` — what `play.py` and `main.py`
say instead of drawing a screen with holes), a picture under a name the
code asks for is drawn whether the manifest lists it or not, and
`python tools/basepack.py refresh` rewrites the manifest from the
installed pack (`dev:tools/close_run.py` runs it). Size and sha256 are checked
where they mean something: installing a pack from its zip and making the
release zip (`tools/basepack.py install`, `make`).

**ONE RESOLVER.** Nothing reads this folder but `core.resources`, which
tries it after the tree (`Resources.resolve`, `roots`, `resolve_dir`), so
the player's mod folder and active mods still win over it. Files that
`tools/setup.py` extracts from the player's own MOO2 stay where setup puts
them (decision 40); the pack holds only OrionLayer's own pictures.
"""
import json
import os
import sys

ENV = "ORIONLAYER_BASE_DIR"
FOLDER = "base"
#: WHERE A PLAYER GETS THE PACK (Data's decision, work order 243): a GitHub
#: release of the public repository, one per manifest. The tag is named by
#: the manifest's own sha256, so a checkout fetches exactly the pack its
#: `basepack.json` names, and `tools/basepack.py install` checks it file by
#: file. `ORIONLAYER_BASE_PACK_URL` replaces the URL (a mirror, the suite).
RELEASE_REPO = "Data-crea/orionlayerv3"
ASSET = "orionlayer-base-pack.zip"
URL_ENV = "ORIONLAYER_BASE_PACK_URL"
TREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(TREE, "basepack.json")


def base_dir():
    """Where the base pack is (or would be installed)."""
    env = os.environ.get(ENV)
    if env:
        return os.path.abspath(os.path.expanduser(env))
    if sys.platform.startswith("win"):
        root = os.environ.get("LOCALAPPDATA") or os.path.join(
            os.path.expanduser("~"), "AppData", "Local")
        return os.path.join(root, "OrionLayer", FOLDER)
    if sys.platform == "darwin":
        return os.path.expanduser(
            "~/Library/Application Support/OrionLayer/" + FOLDER)
    root = os.environ.get("XDG_DATA_HOME") or os.path.expanduser(
        "~/.local/share")
    return os.path.join(root, "orionlayer", FOLDER)


_read = {}


def manifest(path=MANIFEST):
    """{"version": n, "files": {relpath: [size, sha256]}} — read once per
    path and modification time (the mod folder asks once per file)."""
    key = (path, os.path.getmtime(path))
    if key not in _read:
        with open(path, encoding="utf-8") as f:
            _read[key] = json.load(f)
    return _read[key]


def release_tag(path=MANIFEST):
    """`base-pack-<12 hex>`: the release that carries this manifest's pack."""
    import hashlib
    with open(path, "rb") as f:
        return "base-pack-" + hashlib.sha256(f.read()).hexdigest()[:12]


def release_url(path=MANIFEST):
    """Where `python tools/setup.py` fetches the pack this tree names."""
    return os.environ.get(URL_ENV) or (
        f"https://github.com/{RELEASE_REPO}/releases/download/"
        f"{release_tag(path)}/{ASSET}")


def missing(folder=None, man=None):
    """The manifest's paths that are not in the pack at all. Presence only
    (work order 242): a repainted picture of another size is the pack
    working as meant, not a hole; `tools/basepack.py check` hashes."""
    folder = folder or base_dir()
    man = man or manifest()
    return [rel for rel in sorted(man["files"])
            if not os.path.isfile(os.path.join(folder, rel))]


def problems(folder=None):
    """Plain sentences; [] when the pack is complete."""
    folder = folder or base_dir()
    how = ("python tools/setup.py fetches it, or install it once with  "
           "python tools/basepack.py install orionlayer-base-pack.zip  (from "
           f"{release_url()}; or set the environment variable {ENV} to the "
           "folder that holds it)")
    if not os.path.isdir(folder):
        return [f"OrionLayer's base pack (its pictures) is not at {folder} "
                f"— {how}."]
    gone = missing(folder)
    if gone:
        return [f"OrionLayer's base pack at {folder} lacks {len(gone)} of "
                f"its {len(manifest()['files'])} files ("
                + ", ".join(gone[:5]) + (", …" if len(gone) > 5 else "")
                + f") — {how}."]
    return []


def source(relpath, tree=TREE):
    """A picture's path for a tool that reads one by name (the cutters that
    setup runs, the measuring tools): the tree's file while one is there —
    a developer's work in progress — else the base pack's."""
    p = os.path.join(tree, relpath)
    return p if os.path.exists(p) else os.path.join(base_dir(), relpath)
