"""A restored film's frames in place of the engine's picture — work order 386.

**HD EXTENSION `film_restored`.** Decision 101 draws the engine's own
framebuffer while a film plays. A player (or a mod) may put the film's
restored frames where OrionLayer looks:

    <mod folder>/files/assets/shared/films/<film>/
        0001.jpg 0002.jpg ...    the frames, in name order
        clip.json                {"fps": 12.9995}   (informational)

    film   the film's file name without its extension, lower case:
           genwinfn, wininfin, anwinfin, loserfin, orionfin, dimtvfin,
           plntdfin, amebafin, anatkfin (`core.filmblock.FILMS`)

`python tools/film_install.py <film> <video or folder of frames>` makes that
folder from the player's own restored film.

**The engine still plays the film.** Its sound, its pace, its end and the
skip (decision 101, `core.filmview`) are the engine's; the restored frame
shown is the one with the number FILM reports (`core.filmblock`), so picture
and sound cannot drift apart, and a skipped film ends at once. The clip's
own frame count is kept, whatever the original's: when it differs from
FILM's total the frame is chosen in proportion.

**TRANSCRIPTION `film_frame_index`.** FILM's frame is "the last drawn,
0-based, plus one" (`core.filmblock`), so the picture of the frame drawn is
clip frame `frame - 1`.

The film's picture is fitted into the window with its OWN aspect (a wide
3:1 strip or the 288 x 208 popup), never stretched, the bars black. Without
a clip, or while its first frame is not yet loaded, `core.filmview` draws
the engine's picture as before: nothing here is required.

**Why a thread.** A frame of a 4K film is a 4 MP JPEG; pygame has no film
decoder (`core.auvideo`'s reason). A thread loads the frames just ahead of
the one asked for; the draw never waits for a disk.

**UNVERIFIED `film_restored_live`.** Not seen in a live run with the
engine (the index FILM reports against the sound's pace).
"""
import json
import logging
import os
import threading

import pygame

log = logging.getLogger("orionlayer")

REL = "assets/shared/films"
AHEAD = 6            # frames loaded beyond the one asked for
KEEP_BEHIND = 2      # and kept behind it (a snapshot may be a frame late)

_logged = set()      # films reported once


def stem(name):
    """`"PLNTDFIN.LBX"` or `"loserfin.lbx"` -> `"plntdfin"`."""
    base = os.path.basename(str(name or "").replace("\\", "/")).lower()
    return os.path.splitext(base)[0]


def _roots():
    from core import basepack, usermod
    from core.config import BASE_DIR
    return (os.path.join(usermod.mod_dir(), usermod.FILES), BASE_DIR,
            basepack.base_dir())


def clip_dir(name):
    """The folder of the film's restored frames, or None."""
    film = stem(name)
    if not film or not film.isalnum():
        return None
    for root in _roots():
        if root:
            path = os.path.join(root, *REL.split("/"), film)
            if _frame_names(path):
                return path
    return None


def _frame_names(path):
    try:
        return sorted(n for n in os.listdir(path)
                      if n.lower().endswith((".jpg", ".jpeg", ".png")))
    except OSError:
        return []


def frame_index(frame, total, count):
    """Clip frame (0-based) for FILM's `frame` of `total` (TRANSCRIPTION
    `film_frame_index`); `count` is the clip's frames."""
    if count <= 0:
        return 0
    last = max(0, int(frame) - 1)
    if total and total > 1 and total != count:
        last = round(last * (count - 1) / (total - 1))
    return max(0, min(count - 1, last))


def fit(win_w, win_h, w, h):
    """`(x, y, w, h)` of a `w` x `h` picture fitted in the window, its
    aspect kept, centred."""
    scale = min(win_w / w, win_h / h)
    fw, fh = max(1, round(w * scale)), max(1, round(h * scale))
    return (win_w - fw) // 2, (win_h - fh) // 2, fw, fh


class Clip:
    """One film's frames, loaded by a thread just ahead of the asked one."""

    def __init__(self, path):
        self.path = path
        self.names = _frame_names(path)
        self.count = len(self.names)
        self._cache = {}
        self._want = 0
        self._cv = threading.Condition()
        self._stop = False
        self._scaled = None       # (index, size, surface)
        self.failed = False       # the loader died: the engine's picture
        self._thread = threading.Thread(target=self._run, daemon=True,
                                        name="film-frames")
        self._thread.start()

    def close(self):
        with self._cv:
            self._stop = True
            self._cv.notify_all()
        self._thread.join(timeout=2)
        self._cache.clear()
        self._scaled = None

    def _load(self, i, size=None):
        """Frame `i` as a 24-bit surface (an indexed or grey PNG is
        converted here, in the thread: smoothscale takes only 24 or 32
        bits), or None."""
        try:
            img = pygame.image.load(os.path.join(self.path, self.names[i]))
            return img if img.get_bitsize() in (24, 32) else img.convert(24)
        except Exception as err:   # a bad frame must not end the thread
            log.warning("film frame %s: %s", self.names[i], err)
            return None

    def _run(self):
        try:
            self._loop()
        except Exception:
            log.exception("film frames: loader stopped")
            with self._cv:
                self.failed = True

    def _loop(self):
        while True:
            with self._cv:
                while not self._stop:
                    want = self._want
                    todo = [i for i in range(want, min(self.count,
                                                       want + AHEAD + 1))
                            if i not in self._cache]
                    if todo:
                        break
                    self._cv.wait(0.2)
                if self._stop:
                    return
            i = todo[0]
            img = self._load(i)
            with self._cv:
                self._cache[i] = img if img is not None else False
                for k in [k for k in self._cache
                          if k < self._want - KEEP_BEHIND]:
                    del self._cache[k]

    def get(self, i):
        """Frame `i`'s surface, the nearest one loaded at or before it when
        it is not here yet, or None before any."""
        with self._cv:
            self._want = i
            self._cv.notify_all()
            for k in range(i, max(-1, i - AHEAD - KEEP_BEHIND), -1):
                img = self._cache.get(k)
                if img:
                    return k, img
        return None

    def draw(self, surface, i):
        """Draw frame `i` on `surface` (black bars), fitted. Returns the
        placement `(x, y, w, h, scale)`, or None while nothing is loaded."""
        got = self.get(i)
        if got is None:
            return None
        k, img = got
        win = surface.get_size()
        x, y, w, h = fit(win[0], win[1], *img.get_size())
        if self._scaled is None or self._scaled[:2] != (k, (w, h)):
            # a JPEG loads 24-bit, a PNG 24 or 32: both smoothscale takes
            self._scaled = (k, (w, h),
                            pygame.transform.smoothscale(img, (w, h)))
        surface.fill((0, 0, 0))
        surface.blit(self._scaled[2], (x, y))
        return x, y, w, h, w / img.get_width()


class Player:
    """The restored frames of the film that plays, or nothing."""

    def __init__(self):
        self.name = None
        self.clip = None

    def reset(self):
        """The film has gone: stop loading, free the frames."""
        if self.clip is not None:
            self.clip.close()
        self.name = self.clip = None

    def picture(self, surface, film):
        """Draw the restored frame of `film` (FILM's dict); returns the
        placement, or None when there is no clip or no frame yet."""
        name = stem(film.get("name"))
        if name != self.name:
            self.reset()
            self.name = name
            path = clip_dir(name)
            if path:
                self.clip = Clip(path)
                if name not in _logged:
                    _logged.add(name)
                    log.info("film %s: restored frames, %d from %s", name,
                             self.clip.count, path)
        if self.clip is None or self.clip.failed:
            return None
        try:
            return self.clip.draw(surface, frame_index(
                film.get("frame", 0), film.get("total", 0), self.clip.count))
        except Exception:   # a draw fault must never end the App's frame
            log.exception("film %s: restored frame not drawn", name)
            self.clip.failed = True
            return None


def read_fps(path):
    """The clip's frame rate from `clip.json`, or None (display only)."""
    try:
        with open(os.path.join(path, "clip.json"), encoding="utf-8") as fh:
            return float(json.load(fh)["fps"])
    except (OSError, ValueError, KeyError, TypeError):
        return None
