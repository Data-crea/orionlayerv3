"""Data's painted race leaders on the Races screen — work order 315 B.

HD EXTENSION `hd_leaders`: the original draws one 76 x 88 palette drawing
per race in a slot's portrait cell (RACES.LBX 32 + race, racescrn.cpp:328,
`racesart.portrait`); HD draws Data's painting of that race's leader in
the same cell, inside the same banner frame.

DEVIATION `leader_cover`: the original's 76 x 88 drawing is enlarged by
whole pixels and centred in the cell (`sprite_scale`), which the screen
shell's panel map draws wider than native — 1.16 to 1.17 : 1 at every
window size measured for work order 315 (238 x 205 at 1920 x 1080, 476 x
409 at 3840 x 2160), against the drawing's 0.86 : 1. Data's paintings
(1341 x 1173, 1.143 : 1) are made for that cell: every one FILLS it by ONE
rule, never a per-picture crop — scaled to cover the cell, the overhang
cut (`window`, `ANCHOR`): centred across, kept from the top, so at 1.165
the bottom 21 of 1173 rows go and no head is touched (every leader's head
is in the picture's upper half, work order 315's sheets). A player's
picture of another proportion gets the same rule.

WHERE THEY LIVE (decision 95; the leader portraits' route, work order
268): not the base pack — they are redrawings of the game's race
portraits, which its CC BY licence cannot cover — but the player's mod
folder, `files/screens/races/assets/leaders/<nn>_<name>.png` (a slot of
`core.usermod`), `<nn>` the race's number 00-12 (`s_player.race`, the
order of `screens/select_race/races.json`); the name after it is for
people. Installed by `dev:tools/races_leaders_install.py`, which stores
each whole (uncut) at the width HD draws the cell at 3840 x 2160, so the
rule above lives here once and a player's own picture gets it too.

NONE FOR A RACE (no download, a race without a picture, the mod folder
off, an unreadable file): None, and the caller draws the original's
portrait as before — never the original's screen (Data's rule since work
order 187).
"""
import glob
import logging
import os
import time

import pygame

log = logging.getLogger("races")

FOLDER = "screens/races/assets/leaders"
RACES = 13
#: The crop window's place in the overhang, (x, y) as a fraction of it:
#: centred across, from the top (the heads), see `leader_cover`.
ANCHOR = (0.5, 0.0)

_cache = {}
_fitted = {}
#: race -> (when looked, path or None): the folder is listed at most once a
#: second per race, not every frame for every slot (review of work order
#: 315); a picture dropped in shows within that second
_found = {}
LOOK_AGAIN = 1.0


def path_for(race):
    """The picture file for a race, or None — the first source root
    (`Resources.roots`: the player's mod folder first) with a readable
    `<nn>_*.png`."""
    race = int(race)
    if not 0 <= race < RACES:
        return None
    from core import resources
    roots = tuple(resources.res.roots())
    now = time.monotonic()
    hit = _found.get(race)
    if hit is not None and hit[1] == roots and now - hit[0] < LOOK_AGAIN:
        return hit[2]
    path = _look(race, roots)
    _found[race] = (now, roots, path)
    return path


def _look(race, roots):
    for root in roots:
        hits = sorted(glob.glob(os.path.join(root, FOLDER,
                                             f"{race:02d}_*.png")))
        if len(hits) > 1:
            log.warning("race leaders: %d files for race %02d in %s — %s is "
                        "used", len(hits), race, os.path.join(root, FOLDER),
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
        log.warning("race leaders: %s unreadable (%s) — the original's "
                    "portrait is drawn", path, exc)
        img = None
    _cache[path] = (stamp, img)
    return img


def window(src_size, size, anchor=ANCHOR):
    """The part of a `src_size` picture that covers a `size` cell: the
    largest rectangle of the cell's proportion inside the picture, placed
    by `anchor` in what overhangs. (x, y, w, h) in source pixels."""
    sw, sh = src_size
    bw, bh = max(1, int(size[0])), max(1, int(size[1]))
    k = max(bw / sw, bh / sh)
    w, h = min(sw, round(bw / k)), min(sh, round(bh / k))
    return (round((sw - w) * anchor[0]), round((sh - h) * anchor[1]), w, h)


def cover(img, size, anchor=ANCHOR):
    """`img` cut to `window` and scaled smoothly to exactly `size`."""
    x, y, w, h = window(img.get_size(), size, anchor)
    part = img.subsurface(pygame.Rect(x, y, w, h))
    return pygame.transform.smoothscale(
        part, (max(1, int(size[0])), max(1, int(size[1]))))


def picture(race, size):
    """The race's leader painting covering a `size` (w, h) cell, or None —
    then the caller draws the original's portrait in the cell."""
    path = path_for(race)
    if path is None:
        return None
    key = (path, _cache[path][0], tuple(int(v) for v in size))
    hit = _fitted.get(key)
    if hit is None:
        if len(_fitted) > 64:
            _fitted.clear()
        hit = _fitted[key] = cover(_cache[path][1], size)
    return hit
