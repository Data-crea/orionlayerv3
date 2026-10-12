"""The leaders' HD portraits — work order 234. HD EXTENSION `hd_portraits`:
the original has one 73 x 88 drawing per leader (OFFICER.LBX `0x15 + n`); HD
draws a painted picture in its place while the mod folder is on.

WHERE THEY LIVE. `mods/leader_portraits/<category>/<pict_num>_<name>.png`,
`colony_leaders/` and `ship_officers/` (the leader's `type`,
`core/structs/leader.py`), `pict_num` two digits — the identity the game
knows the leader by (HERODATA.LBX's record number, held equal on every save
by `dev:tools/leader_check.py`). The name after the number is for people: a
picture is found by its number, so a file renamed with a different name
still counts and the folder can hold a translation's spelling.

WHICH FILE WINS. Each source root in order (`Resources.roots`, decision
16): the player's mod folder's `files/` — so
`files/mods/leader_portraits/colony_leaders/01_kimbuzzi.png` there replaces
the tree's picture by the existing convention, decision 72 — then the
developer mods, then the tree. The first root with a `<nn>_*.png` for the
leader answers; an unreadable file costs one log line and the next root is
asked.

WHEN. Only while the player's mod folder is on (`usermod.active()`): the
pictures are mod content (the order, step 4). Folder off, or no picture for
a leader: the caller draws the original's portrait itself, in the same box
— never the original's screen (Data's rule since work order 187; the
portrait is HD's own drawing of the extracted art, as before this order).

HOW BIG. Every box gets the WHOLE picture, scaled to fit inside it and
centred (`fit`); nothing is cut. The boxes do not share one proportion
(measured at 3840x2160, work order 234 step 3): the Leaders row's cell is
540 x 343, the two popups the original's 73 x 88. The set is cut for the
Leaders screen (its height binds) and stored 528 high, the tallest box —
which proportion the other boxes should cut to is parked for Data
(234-parked-for-data.md).

DARK. The original swaps in a darkened drawing (`0x8F + n`) while a
leader travels or is for hire (officer.cpp:2656, :3533). Measured over all
67 pairs of the extracted art: the dark drawing is 0.546 of the normal one's
brightness (0.524-0.556, every channel alike within 0.05), so HD multiplies
the picture by `DARK` — DEVIATION `dark_hd`: a multiply, not the original's
palette remap.
"""
import glob
import logging
import os

import pygame

log = logging.getLogger("orionlayer")

FOLDER = "mods/leader_portraits"
#: `LEADER_TYPE_*` -> the sub-folder (core/structs/leader.py).
CATEGORY = {0: "ship_officers", 1: "colony_leaders"}
#: The original's drawing, the box both popups give a portrait.
NATIVE_SIZE = (73, 88)
#: The dark drawing's brightness against the normal one's (measured).
DARK = 0.546

_cache = {}
_fitted = {}


def enabled():
    from core import usermod
    return usermod.active()


def path_for(pict_num, leader_type):
    """The picture file for a leader, or None (folder off, or no file)."""
    if not enabled():
        return None
    cat = CATEGORY.get(int(leader_type))
    if cat is None:
        return None
    from core import resources
    for root in resources.res.roots():
        hits = sorted(glob.glob(os.path.join(
            root, FOLDER, cat, f"{int(pict_num):02d}_*.png")))
        if len(hits) > 1:
            log.warning("leader portraits: %d files for %s %02d in %s — "
                        "%s is used", len(hits), cat, int(pict_num),
                        os.path.join(root, FOLDER, cat),
                        os.path.basename(hits[0]))
        for path in hits[:1]:
            if _load(path) is not None:
                return path
    return None


def _load(path):
    try:
        stamp = os.stat(path).st_mtime_ns
    except OSError:
        return None
    hit = _cache.get(path)
    if hit is not None and hit[0] == stamp:
        return hit[1]
    try:
        img = pygame.image.load(path)
        img = img.convert() if pygame.display.get_surface() else img
    except (pygame.error, OSError) as exc:
        log.warning("leader portraits: %s unreadable (%s) — the original's "
                    "portrait is drawn", path, exc)
        img = None
    _cache[path] = (stamp, img)
    return img


def picture(rec, size, dark=False):
    """The leader's HD picture fitted inside `size` (w, h), or None — then
    the caller draws the original's portrait in the same box."""
    path = path_for(rec.pict_num, rec.type)
    if path is None:
        return None
    img = _load(path)
    key = (path, _cache[path][0], tuple(size), bool(dark))
    hit = _fitted.get(key)
    if hit is not None:
        return hit
    out = fit(img, size)
    if dark:
        k = int(round(DARK * 255))
        out = out.copy()
        out.fill((k, k, k), special_flags=pygame.BLEND_RGB_MULT)
    if len(_fitted) > 256:
        _fitted.clear()
    _fitted[key] = out
    return out


def fit(img, size):
    """`img` scaled smoothly to fit inside `size`, its proportion kept."""
    w, h = img.get_size()
    bw, bh = max(1, int(size[0])), max(1, int(size[1]))
    k = min(bw / w, bh / h)
    return pygame.transform.smoothscale(
        img, (max(1, round(w * k)), max(1, round(h * k))))
