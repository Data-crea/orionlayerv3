"""The colony screen's planet pictures, extracted by the player — or their
absence, said. Work order 223 (Data's decision 3: "the right planet
pictures are not shown yet").

`tools/colony_art_extract.py` writes the raw LBX blobs and the screen's
palette into `assets/gamedata/`; this decodes them lazily through
`core/lbx.py` (decision 38's path, the Races loader's shape). Nothing here
is committed or shipped (decisions 38, 40, 42).

TRANSCRIPTION, what the original draws and in which colours:

  the scene    COLONY2.LBX 0x31, the sky, then PLANETS.LBX
               `climate * 3 + climate_bg_type` over it — index 0 of the
               ground lets the sky through (`Draw_Colony_Screen_`,
               colony_main.cpp:111-115; `C_Anims_(0)`, :475-479)
  the palette  FONTS.LBX 2 — palette 1 (`Load_Palette_(1, 0, 255)`,
               colony.cpp:231, fonts.cpp:72-73) — with the ground's own
               palette laid over it (`Draw_Palette_`, colony.cpp:233), so
               every picture of the screen is coloured by the world shown
  the system   COLSYSDI.LBX `climate * 5 + size + 11` for a planet, 0x3E a
               gas giant, 0x3F an asteroid belt, 0x41 the orbit marker
               (colsysdi.cpp:4-45)

Measured: with this palette, sky and ground, the composed scene equals the
native frame of a live colony screen pixel for pixel wherever no building
stands (work order 223, Sol II: terran, ground type 1).
"""
import json
import logging
import os

import numpy as np
import pygame

from core import blobart, lbx

log = logging.getLogger("colony")

GAMEDATA = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "assets", "gamedata")
#: The same folder as a tree path: read through the resolver (`core.blobart`).
REL = "screens/colony/assets/gamedata"
FORMAT_VERSION = 3
HOW = "python tools/colony_art_extract.py"
CLIMATES, BG_TYPES, SIZES = 10, 3, 5


class ColonyArt:
    def __init__(self, folder=None):
        self._src = blobart.Source(REL, folder)
        self.reason = ""
        self._base = None
        self._blobs = {}
        self._cache = {}
        try:
            with open(self._src.path("manifest.json"), encoding="utf-8") as fh:
                manifest = json.load(fh)
            if int(manifest.get("format", 0)) != FORMAT_VERSION:
                self.reason = (f"The colony pictures are format "
                               f"{manifest.get('format')}, this build reads "
                               f"{FORMAT_VERSION}. Run: {HOW}")
                return
            with open(self._src.path("palette.json"), encoding="utf-8") as fh:
                self._base = {i: tuple(c) for i, c in enumerate(json.load(fh))}
        except (OSError, ValueError) as exc:
            self.reason = f"The colony pictures are not extracted ({exc}). Run: {HOW}"

    @property
    def available(self):
        return self._base is not None

    def _indices(self, stem):
        """(header, indices (h, w)) of one stored drawing, or None."""
        if stem not in self._blobs:
            try:
                blob = self._src.read(f"{stem}.bin")
                head = lbx.parse_header(blob, stem)
                px = lbx.decode_frame(blob, head, 0)
                self._blobs[stem] = None if px is None else (
                    blob, head, np.array(px, np.uint8).reshape(
                        head.height, head.width))
            except (OSError, ValueError) as exc:
                log.warning("colony picture %s unreadable: %s", stem, exc)
                self._blobs[stem] = None
        return self._blobs[stem]

    def palette(self, climate, bg):
        """The screen's palette while this world is shown: FONTS.LBX 2 with
        the ground's own palette over it."""
        out = dict(self._base or {})
        got = self._indices(_ground(climate, bg))
        if got is not None:
            blob, head, _px = got
            out.update(lbx.read_palette(blob, head.frame_count))
        return out

    def _lut(self, climate, bg):
        pal = self.palette(climate, bg)
        lut = np.zeros((256, 3), np.uint8)
        for i, rgb in pal.items():
            if 0 <= i < 256:
                lut[i] = rgb[:3]
        return lut

    def scene(self, climate, bg):
        """The sky with the world's ground over it, 640 x 480, opaque — or
        None without the pictures."""
        if not self.available:
            return None
        key = ("scene", climate, bg)
        if key not in self._cache:
            sky, ground = self._indices("sky"), self._indices(
                _ground(climate, bg))
            surf = None
            if sky is not None and ground is not None:
                idx = np.where(ground[2] != 0, ground[2], sky[2])
                rgb = self._lut(climate, bg)[idx]
                surf = pygame.surfarray.make_surface(rgb.transpose(1, 0, 2))
            self._cache[key] = surf
        return self._cache[key]

    def sprite(self, stem, climate, bg):
        """A system-display drawing (`planet_<c>_<s>`, `gas_giant`,
        `asteroids`, `marker`) in the palette of the world shown; index 0
        transparent. A painted PNG beside it wins (`blobart`)."""
        if not self.available:
            return None
        key = ("sprite", stem, climate, bg)
        if key not in self._cache:
            surf = self._src.painted(f"{stem}.bin")
            got = None if surf is not None else self._indices(stem)
            if got is not None:
                idx = got[2]
                rgb = self._lut(climate, bg)[idx]
                surf = pygame.Surface((idx.shape[1], idx.shape[0]),
                                      pygame.SRCALPHA)
                view = pygame.surfarray.pixels3d(surf)
                view[...] = rgb.transpose(1, 0, 2)
                del view
                alpha = pygame.surfarray.pixels_alpha(surf)
                alpha[...] = np.where(idx != 0, 255, 0).T
                del alpha
            self._cache[key] = surf
        return self._cache[key]


def _ground(climate, bg):
    c = int(climate) if 0 <= int(climate) < CLIMATES else 0
    t = int(bg) if 0 <= int(bg) < BG_TYPES else 0
    return f"ground_{c}_{t}"


def planet_stem(climate, size):
    if not 0 <= int(climate) < CLIMATES or not 0 <= int(size) < SIZES:
        return None
    return f"planet_{int(climate)}_{int(size)}"


_loaded = None


def load():
    global _loaded
    if _loaded is None:
        _loaded = ColonyArt()
        log.info("colony pictures: %s", "loaded" if _loaded.available
                 else _loaded.reason)
    return _loaded
