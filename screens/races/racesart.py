"""The Races screen's artwork, extracted by the player — or its absence, said.

`tools/races_art_extract.py` writes the raw RACES.LBX blobs and the
screen's palette (RACES.LBX 0's, over FONTS.LBX 9) into `assets/gamedata/`;
this decodes them lazily through `core/lbx.py`, the Leaders loader's path.
Nothing here is committed or shipped (decisions 38, 40, 42).
"""
import json
import logging
import os

import pygame

from core import lbx

log = logging.getLogger("races")

GAMEDATA = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "assets", "gamedata")
FORMAT_VERSION = 1
HOW = "python tools/races_art_extract.py"
RACES = 13


class RacesArt:
    def __init__(self, folder=GAMEDATA):
        self.folder = folder
        self.reason = ""
        self._palette = None
        self._cache = {}
        self._load()

    def _load(self):
        try:
            with open(os.path.join(self.folder, "manifest.json"),
                      encoding="utf-8") as fh:
                manifest = json.load(fh)
            if int(manifest.get("format", 0)) != FORMAT_VERSION:
                self.reason = (f"The Races artwork is format "
                               f"{manifest.get('format')}, this build reads "
                               f"{FORMAT_VERSION}. Run: {HOW}")
                return
            with open(os.path.join(self.folder, "palette.json"),
                      encoding="utf-8") as fh:
                self._palette = {i: tuple(c) for i, c in
                                 enumerate(json.load(fh))}
        except (OSError, ValueError) as exc:
            self.reason = f"The Races artwork is not extracted ({exc}). Run: {HOW}"

    @property
    def available(self):
        return self._palette is not None

    def palette_rgb(self, index):
        return self._palette.get(int(index)) if self._palette else None

    def portrait(self, race):
        return self._sprite(f"portrait_{int(race)}") \
            if 0 <= int(race) < RACES else None

    def spy(self, race):
        return self._sprite(f"spy_{int(race)}") \
            if 0 <= int(race) < RACES else None

    def eliminated(self):
        return self._sprite("eliminated")

    def _sprite(self, name):
        if not self.available:
            return None
        if name in self._cache:
            return self._cache[name]
        surface = None
        path = os.path.join(self.folder, f"{name}.bin")
        try:
            with open(path, "rb") as fh:
                blob = fh.read()
            header = lbx.parse_header(blob, name)
            pixels = lbx.decode_frame(blob, header, 0)
            if pixels is not None:
                palette = dict(self._palette)
                if header.has_palette:
                    palette.update(lbx.read_palette(blob, header.frame_count))
                surface = pygame.image.frombuffer(
                    lbx.rgba_bytes(pixels, palette),
                    (header.width, header.height), "RGBA").copy()
        except (OSError, lbx.LbxError, ValueError):
            surface = None
        self._cache[name] = surface
        return surface


_loaded = None


def load(folder=GAMEDATA):
    global _loaded
    if _loaded is None or _loaded.folder != folder:
        _loaded = RacesArt(folder)
        log.info("races artwork: %s", "loaded from " + folder
                 if _loaded.available else _loaded.reason)
    return _loaded
