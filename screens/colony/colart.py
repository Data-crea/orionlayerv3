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
  the buildings BLDG<n>.LBX, one 640 x 480 picture per building and grid
               cell, glassed (shadows blend with what is under them); the
               five satellites COLONY.LBX 9 + p (work order 326, `bldg`,
               `satellite`; the rules are `colbuildings`')
  the rows     COLONY2.LBX 0..15, the production rows' symbols, and the
               shortage's outline (`outlined`; work order 326, `colprod`)

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
#: `Short_Anims_`'s outline colour, a palette index (colony.cpp:2173).
SHORT_OUTLINE = 0xED


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

    def _decode(self, stem):
        """The indices (h, w) of one stored drawing, not kept; or None."""
        try:
            blob = self._src.read(f"{stem}.bin")
            head = lbx.parse_header(blob, stem)
            px = lbx.decode_frame(blob, head, 0)
        except (OSError, ValueError) as exc:
            log.warning("colony picture %s unreadable: %s", stem, exc)
            return None
        return None if px is None else np.array(px, np.uint8).reshape(
            head.height, head.width)

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
        key = ("lut", climate, bg)
        if key not in self._cache:
            pal = self.palette(climate, bg)
            lut = np.zeros((256, 3), np.uint8)
            for i, rgb in pal.items():
                if 0 <= i < 256:
                    lut[i] = rgb[:3]
            self._cache[key] = lut
        return self._cache[key]

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

    def glass(self):
        """The 16 glass colours (intensity %, r, g, b in 8 bit): FONTS.LBX
        0's table (`Load_Font_File_`, fonts.cpp:894), colour 0 made 50 %
        black by the colony's palette update (`Update_Glass_Remap_Colors_`,
        remap.cpp:154-157, called colony.cpp:234). None before an
        extraction that wrote it."""
        if "glass" not in self._cache:
            table = None
            try:
                with open(self._src.path("glass.json"), encoding="utf-8") as fh:
                    raw = json.load(fh)
                table = [(int(i), min(int(r) * 4, 255), min(int(g) * 4, 255),
                          min(int(b) * 4, 255)) for i, r, g, b in raw[:16]]
                table[0] = (50, 0, 0, 0)
            except (OSError, ValueError, TypeError) as exc:
                log.info("colony glass table not read: %s", exc)
            self._cache["glass"] = table
        return self._cache["glass"]

    def picture(self, stem, climate, bg, glassed=True):
        """(surface, (x, y)): the inked part of a stored drawing (a building's
        640 x 480 is glassed, a satellite's is not: `glassed`) in the world's palette, and where its corner is in
        the drawing's own canvas — or None (absent, or nothing drawn).
        Cropped, so a city of 36 buildings is not 36 screens in memory."""
        if not self.available or (glassed and self.glass() is None):
            return None
        key = ("picture", stem, climate, bg, glassed)
        if key not in self._cache:
            if len(self._cache) > 400:
                self._cache = {k: v for k, v in self._cache.items()
                               if k[0] != "picture"}
            # decoded and dropped: `_indices` keeps what it decodes, and
            # 1728 whole screens are 500 MB
            got = self._decode(stem)
            out = None
            if got is not None:
                idx = got
                ys, xs = np.nonzero(idx)
                if len(xs):
                    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), \
                        ys.max() + 1
                    out = (_alpha_surface(idx[y0:y1, x0:x1],
                                          self._lut(climate, bg),
                                          self.glass() if glassed else None),
                           (int(x0), int(y0)))
            self._cache[key] = out
        return self._cache[key]

    def has(self, stem):
        """The drawing is there, extracted or painted — asked without
        reading it, so an older extraction is not a log line per name."""
        return self.available and (
            os.path.isfile(self._src.path(f"{stem}.bin"))
            or os.path.isfile(self._src.path(f"{stem}_0.png")))

    def outlined(self, stem, climate, bg, index=SHORT_OUTLINE):
        """A drawing as `Short_Anims_` makes a shortage of it (colony.cpp:
        2168-2176): laid one pixel in on a blank bitmap and outlined in
        palette colour `index` (0xED) — every empty pixel left, right,
        above or below an inked one (`Outline_Bitmap_Pixels_`, shear.cpp:
        371-453, a horizontal and a vertical pass). One pixel larger on
        every side, so it is drawn where the plain drawing would be and
        its picture stands one pixel right and down, as the original's."""
        if not self.available:
            return None
        key = ("outlined", stem, climate, bg, index)
        if key not in self._cache:
            pic = self.sprite(stem, climate, bg)
            surf = None
            if pic is not None:
                w, h = pic.get_size()
                ink = np.zeros((w + 2, h + 2), bool)
                ink[1:-1, 1:-1] = pygame.surfarray.array_alpha(pic) > 0
                ring = np.zeros_like(ink)
                ring[1:, :] |= ink[:-1, :]
                ring[:-1, :] |= ink[1:, :]
                ring[:, 1:] |= ink[:, :-1]
                ring[:, :-1] |= ink[:, 1:]
                ring &= ~ink
                surf = pygame.Surface((w + 2, h + 2), pygame.SRCALPHA)
                surf.blit(pic, (1, 1))
                rgb = self._lut(climate, bg)[index]
                view = pygame.surfarray.pixels3d(surf)
                view[ring] = rgb
                del view
                alpha = pygame.surfarray.pixels_alpha(surf)
                alpha[ring] = 255
                del alpha
            self._cache[key] = surf
        return self._cache[key]


def _alpha_surface(idx, lut, glass):
    """A picture's indices as an RGBA surface: index 0 clear, a glass index
    (0xF0..0xFF, `glass` the 16 (intensity, r, g, b)) its colour at its
    intensity as alpha — the original blends it with the pixel under it
    (`Draw_Glassed_Animated_Sprite_`, animate.cpp:252-292), which on
    HD's ground is an alpha blend — every other index its palette colour."""
    h, w = idx.shape
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    rgb = lut[idx]
    alpha = np.where(idx != 0, 255, 0).astype(np.uint8)
    if glass is not None:
        for g, (inten, r, gr, b) in enumerate(glass):
            hit = idx == 0xF0 + g
            if hit.any():
                rgb[hit] = (r, gr, b)
                alpha[hit] = int(round(inten * 255 / 100))
    view = pygame.surfarray.pixels3d(surf)
    view[...] = rgb.transpose(1, 0, 2)
    del view
    a = pygame.surfarray.pixels_alpha(surf)
    a[...] = alpha.T
    del a
    return surf


def _ground(climate, bg):
    c = int(climate) if 0 <= int(climate) < CLIMATES else 0
    t = int(bg) if 0 <= int(bg) < BG_TYPES else 0
    return f"ground_{c}_{t}"


def bldg_stem(building, col, row):
    """The stored drawing of `building` (1..48) standing on cell (col,
    row) of the 6 x 6 grid: `Cache_Load_Bldg_` (colbcach.cpp:4-19), its
    frame `Bldg_Coords_To_Effective_Frame_` (colony_main.cpp:229-236).
    None for anything that is not a building on a cell."""
    if not (1 <= int(building) <= 48 and 0 <= int(col) < 6
            and 0 <= int(row) < 6):
        return None
    frame = row * 6 + col if row % 2 == 0 else row * 6 - col + 5
    return f"bldgcell_{int(building)}_{frame}"


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
