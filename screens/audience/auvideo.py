"""The ambassador as a film clip — work order 359 (Data's Elerian clips).

**HD EXTENSION `ambassador_video`.** A player (or a mod) may put a short
clip per race and mood where the audience's still ambassador is:

    <mod folder>/files/screens/audience/assets/video/<race>/<mood>/
        0001.jpg 0002.jpg ...    the frames, in name order
        audio.ogg                the sound (optional)
        clip.json                {"fps": 24}

    race   the lower-case race name, `RACES` (the order of MOO2's race
           strings, ESTR_ALKARI 645 .. ESTR_TRILARIAN 657, orion2_str.h)
    mood   `aumood.MOODS`: first_contact, friendly, neutral, pleading,
           threatening

`python tools/audience_video_install.py <race> <folder of <mood>.mp4>` makes
that folder from the player's films.

The clip REPLACES the room and the ambassador of the original (they are
one picture in the clip) inside the 4:3 stage the screen shell fits into
the window; a clip of another aspect (widescreen) is fitted, its own
aspect kept, into the whole window instead (`Player.frame`). Never
stretched. The menu and
the statement panels are HD's own and are drawn over it by `audraw`; the
clip carries no text. Without the clip the audience draws the still, as
before: nothing here is required.

**Why frames and not the film file.** The client never starts another
program (it must not launch or signal a process, check 006e, and every
ffmpeg is run through the developer tools' limited runner, check 090zzzr). pygame has no film
decoder, so the installer converts ONCE, with ffmpeg, to what pygame
reads itself (JPEG frames, OGG sound), and the player needs no ffmpeg at
all. A thread loads the frames ahead of the clock.

**HD EXTENSION `ambassador_video_wide`.** See `Player.frame`.

**HD EXTENSION `ambassador_video_hold`.** A clip plays ONCE and holds its
last frame: the clips do not loop (their last frame is not their first;
measured, SSIM 0.33-0.42 on the five Elerian clips). It plays once per
audience, whatever is said in it (a reply, then the menu: Data's
correction of 1 November 2026, the clip had played again at the menu); a
mood with a clip of its own crosses over from the old picture in `FADE`
seconds; leaving the audience stops it, the next one plays it again.

**HD EXTENSION `ambassador_video_lights`.** `clip.json` may carry
`"glow": {"rect": [x, y, w, h], "fps": 24, "pingpong": true}` and the folder
a `glow/` of RGBA patches of that rectangle, one per frame
(`tools/audience_video_install.py --lights`). When the film has ended and
its last frame is held, the patches play over that frame in a loop (from
the last one back to the first and forth again with `pingpong`): the
rectangle holds the green light over the ambassador and the helix beneath
it, the rest of the picture stands still. A clip without them holds its
last frame, as before. Why not loop the film's last seconds: the figure
gestures all the way through the film and the loop read as the whole film
repeating (Data, 1 November 2026).

**UNVERIFIED `ambassador_video_live`.** Not seen in a live run with the
engine (the sound device and the audience's real timing).
"""
import json
import logging
import math
import os
import queue
import threading
import time

import pygame

log = logging.getLogger("audience")

#: `ESTR_ALKARI` 645 .. `ESTR_TRILARIAN` 657 (orion2_str.h:638-650): the
#: ambassador's `race` byte is the offset from 645.
RACES = ("alkari", "bulrathi", "darlok", "elerian", "gnolam", "human",
         "klackon", "meklar", "mrrshan", "psilon", "sakkra", "silicoid",
         "trilarian")
REL = "screens/audience/assets/video"
FADE = 0.25               # s: the cross-over to a new mood's first frame
COVER = 1.06             # fill a window whose aspect is within 6 % of the clip's
QUEUE = 6                 # loaded frames waiting: ~0.25 s of a 24 fps clip

_missing = set()          # faults already reported, once
_sounds = {}              # audio.ogg path -> pygame Sound, or False


def clip_dir(race, mood):
    """The clip's folder for a race index and a mood, or None."""
    if race is None or not 0 <= race < len(RACES):
        return None
    from core import basepack, usermod
    from core.config import BASE_DIR
    roots = (os.path.join(usermod.mod_dir(), usermod.FILES), BASE_DIR,
             basepack.base_dir())
    for name in (mood, "default"):    # `default`: one film for every mood
        rel = f"{REL}/{RACES[race]}/{name}"
        for root in roots:
            if root:
                path = os.path.join(root, *rel.split("/"))
                if _has_frames(path):
                    return path
    return None


def _has_frames(path):
    """A folder with at least one picture: an empty or unreadable mood
    folder is no clip, and the mood falls back to `default`."""
    try:
        return any(n.lower().endswith((".jpg", ".jpeg", ".png"))
                   for n in os.listdir(path))
    except OSError:
        return False


def _finite(value, default):
    """`value` as a finite float of at least 1, else `default` (a frame
    rate of inf or nan in a clip.json must not crash the draw)."""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return default
    return max(1.0, value) if math.isfinite(value) else default


def _once(key, message, *args):
    if key not in _missing:
        _missing.add(key)
        log.warning(message, *args)


class Clip:
    """One clip being played: a thread loading frames, the sound, the
    clock. `frame()` is the surface of the frame due now."""

    def __init__(self, folder):
        self.path = folder
        self.ok = True
        self.ended = False
        self.fps = 24.0
        self._names = sorted(n for n in os.listdir(folder)
                             if n.lower().endswith((".jpg", ".jpeg", ".png")))
        try:
            with open(os.path.join(folder, "clip.json"),
                      encoding="utf-8") as fh:
                self.fps = _finite(json.load(fh).get("fps", 24), 24.0)
        except (OSError, ValueError, TypeError, AttributeError):
            pass                          # 24, as the Elerian clips
        if not self._names:
            self.ok = False
            _once(("empty", folder), "audience video: no frames in %s",
                  folder)
            return
        self._queue = queue.Queue(QUEUE)
        self._stop = threading.Event()    # before any thread starts
        self._glow = []                   # RGBA patches, loaded whole
        self._glow_meta = None
        self._held = None                 # the last frame + the glow on it
        self._base = self._where = None
        self._glow_t0 = 0.0
        self._read_glow(folder)
        self._start = None            # monotonic time of frame 0 shown
        self._surface = None
        self._index = -1
        self._sound = None
        self._thread = threading.Thread(target=self._load, daemon=True,
                                        name="audience-video")
        self._thread.start()

    def _read_glow(self, folder):
        try:
            with open(os.path.join(folder, "clip.json"),
                      encoding="utf-8") as fh:
                meta = json.load(fh).get("glow")
            gdir = os.path.join(folder, "glow")
            if not meta or not os.path.isdir(gdir):
                return
            x, y, w, h = (int(v) for v in meta["rect"])
            meta = {"rect": pygame.Rect(x, y, w, h),
                    "fps": _finite(meta.get("fps", self.fps), self.fps),
                    "pingpong": bool(meta.get("pingpong"))}
        except (OSError, ValueError, TypeError, KeyError, AttributeError):
            return
        self._glow_meta = meta
        threading.Thread(target=self._load_glow, args=(gdir,), daemon=True,
                         name="audience-glow").start()

    def _load_glow(self, gdir):
        patches = []
        try:
            for name in sorted(os.listdir(gdir)):
                if self._stop.is_set():
                    return
                if name.lower().endswith(".png"):
                    patches.append(pygame.image.load(
                        os.path.join(gdir, name)))
        except (pygame.error, OSError) as err:
            _once(("glow", gdir), "audience video: glow %s (%s)", gdir, err)
            return
        self._glow = patches              # whole or not at all

    def _load(self):
        try:
            for n, name in enumerate(self._names):
                if self._stop.is_set():
                    return
                try:
                    pic = pygame.image.load(os.path.join(self.path, name))
                except (pygame.error, OSError) as err:
                    _once(("frame", self.path), "audience video: %s (%s)",
                          name, err)
                    return
                while not self._stop.is_set():
                    try:
                        self._queue.put((n, pic), timeout=0.05)
                        break
                    except queue.Full:
                        continue
        finally:
            while not self._stop.is_set():        # the end of the film
                try:
                    self._queue.put(None, timeout=0.05)
                    break
                except queue.Full:
                    continue

    def _load_sound(self):
        path = os.path.join(self.path, "audio.ogg")
        if path in _sounds:
            return _sounds[path]
        sound = False
        if os.path.isfile(path):
            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                sound = pygame.mixer.Sound(path)
            except pygame.error as err:
                _once(("sound", path), "audience video: no sound for %s "
                      "(%s)", path, err)
        _sounds[path] = sound
        return sound

    def frame(self):
        """The surface due now (the first one once it is loaded), or None
        while nothing has been loaded yet."""
        if not self.ok:
            return None
        if self._start is None:
            try:
                item = self._queue.get_nowait()
            except queue.Empty:
                return None
            if item is None:
                self.ok = False
                return None
            self._take(item)
            # frame 0 is up: the clock and the sound start together
            self._start = time.monotonic()
            self._sound = self._load_sound()
            if self._sound:
                self._sound.play()
            return self._surface
        due = int((time.monotonic() - self._start) * self.fps)
        while not self.ended and self._index < due:
            try:
                item = self._queue.get_nowait()
            except queue.Empty:
                break                     # late: draw what there is
            if item is None:
                self.ended = True         # hold the last frame
                break
            self._take(item)
        return self._glowing() if self.ended else self._surface

    def _glowing(self):
        """The held last frame with the glow loop over it (or without, until
        the glow is loaded or when the clip has none)."""
        patches = self._glow
        if not patches or self._surface is None:
            return self._surface
        if self._held is None:
            # patches are converted once, here (a display exists by now)
            rect = self._glow_meta["rect"]
            if not self._surface.get_rect().contains(rect) or any(
                    p.get_size() != rect.size for p in patches):
                # made for another picture size: no loop, and no crash
                _once(("rect", self.path), "audience video: the glow of %s "
                      "does not fit the frame", self.path)
                self._glow = []
                return self._surface
            self._glow = patches = [p.convert_alpha() for p in patches]
            self._held = self._surface.copy()
            # the held frame's own rectangle: what the patches go back to
            self._where = rect
            self._base = self._held.subsurface(rect).copy()
            self._glow_t0 = time.monotonic()
        meta, n = self._glow_meta, len(patches)
        k = int((time.monotonic() - self._glow_t0) * meta["fps"])
        if meta["pingpong"] and n > 1:
            k %= 2 * (n - 1)
            i = n - 1 - k if k <= n - 1 else k - (n - 1)
        else:
            i = k % n
        self._held.blit(self._base, self._where.topleft)
        self._held.blit(patches[i], meta["rect"].topleft)
        return self._held

    def _take(self, item):
        self._index, self._surface = item

    def picture(self):
        """A copy of the frame now shown, or None."""
        return self._surface.copy() if self._surface is not None else None

    @property
    def playing(self):
        return self.ok and not self.ended

    def close(self):
        if self.ok or self._names:
            self._stop.set()
        if self._sound:
            self._sound.stop()


class Player:
    """The audience's one clip at a time, and what it was asked for."""

    def __init__(self):
        self.clip = None
        self.key = None
        self.prev = None              # the picture crossed over from
        self.crossed_at = 0.0
        self.scaled = None            # the last picture made

    def want(self, race, mood):
        """Start (or keep) the clip for the race and mood. Returns True when
        a clip is on."""
        path = clip_dir(race, mood)
        if path is None:
            self.stop()
            return False
        same = self.clip is not None and self.clip.path == path
        if same:
            return self.clip.ok       # played once per audience, then held
        # a different clip (another mood's) crosses over from the old
        # picture
        old = None if same or self.clip is None else self.clip.picture()
        self.stop(keep=old)
        self.clip = Clip(path)
        self.key = path
        return self.clip.ok

    def frame(self, stage, window):
        """`(picture, topleft)` for the stage (the 4:3 rectangle the screen
        shell fits) inside `window`, or None (the still shows). A 4:3 clip
        fills the stage; any other aspect (a widescreen clip) is fitted,
        its own aspect kept, into the whole window, and the 4:3 stage's
        panels are drawn over it (HD EXTENSION `ambassador_video_wide`)."""
        if self.clip is None:
            return None
        src = self.clip.frame()
        if src is None:
            return None
        w, h = src.get_size()
        if abs(w / h - stage.w / stage.h) < 0.02:
            box = stage
        else:
            lo, hi = sorted((window.w / w, window.h / h))
            # a window within COVER of the clip's aspect is FILLED (the
            # overflow cropped evenly): thin bars of the background beside
            # a picture that all but fits read as a fault (Data, 1 Nov)
            k = hi if hi <= lo * COVER else lo
            box = pygame.Rect(0, 0, round(w * k), round(h * k))
            box.center = window.center
        self.scaled = pygame.transform.scale(src, box.size)
        if self.prev is not None:
            t = (time.monotonic() - self.crossed_at) / FADE
            if t >= 1.0:
                self.prev = None
            else:
                old = pygame.transform.scale(self.prev, box.size)
                old.set_alpha(int(255 * (1.0 - t)))
                self.scaled.blit(old, (0, 0))
        return self.scaled, box.topleft

    @property
    def moving(self):
        return self.clip is not None and (self.clip.playing or
                                          self.prev is not None)

    def stop(self, keep=None):
        if self.clip is not None:
            self.clip.close()
        self.clip, self.key = None, None
        self.prev = keep
        self.crossed_at = time.monotonic()


PLAYER = Player()
