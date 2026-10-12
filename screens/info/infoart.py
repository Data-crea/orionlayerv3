"""The Tech Review's pictures, extracted by the player — or their absence, said.

Work order 196 F. `tools/info_art_extract.py` writes the raw APP_PICS.LBX
blobs (`app_<id>.bin`, technology application `id`) and the main palette into
`assets/gamedata/`; this decodes them lazily through `core/lbx.py`, the Races
loader's path, each picture's own palette over the main one
(`Draw_Palette_`, info.cpp:896). Nothing here is committed or shipped
(decisions 38, 40, 42).

**FILE BY FILE THROUGH THE RESOURCE ROOTS** (decisions 16 and 72, 195's rule
for a picture Data adds): each file is `Resources.resolve`d, so a mod or the
player's mod folder replaces one picture and the rest stay the game's.
"""
import json
import logging
import os

import pygame

from core import lbx

log = logging.getLogger("info")

REL = "screens/info/assets/gamedata"
FORMAT_VERSION = 1
HOW = "python tools/info_art_extract.py"


class InfoArt:
    """`folder` None resolves every file through the resource roots; a folder
    reads that folder only (the checks' way)."""

    def __init__(self, folder=None):
        self.folder = folder
        self.reason = ""
        self._palette = None
        self._cache = {}
        self._load()

    def _path(self, name):
        if self.folder is not None:
            return os.path.join(self.folder, name)
        from core import resources
        return resources.res.resolve(f"{REL}/{name}")

    def _load(self):
        try:
            path = self._path("manifest.json")
            if not path:
                raise OSError("no manifest.json")
            with open(path, encoding="utf-8") as fh:
                manifest = json.load(fh)
            if int(manifest.get("format", 0)) != FORMAT_VERSION:
                self.reason = (f"The Tech Review pictures are format "
                               f"{manifest.get('format')}, this build reads "
                               f"{FORMAT_VERSION}. Run: {HOW}")
                return
            with open(self._path("palette.json"), encoding="utf-8") as fh:
                self._palette = {i: tuple(c) for i, c in
                                 enumerate(json.load(fh))}
        except (OSError, TypeError, ValueError) as exc:
            self.reason = (f"The Tech Review pictures are not extracted "
                           f"({exc}). Run: {HOW}")

    @property
    def available(self):
        return self._palette is not None

    def picture(self, app_id):
        """Application `app_id`'s picture as a surface, or None."""
        if not self.available or app_id is None or int(app_id) < 0:
            return None
        key = int(app_id)
        if key in self._cache:
            return self._cache[key]
        surface = None
        path = self._path(f"app_{key}.bin")
        try:
            with open(path, "rb") as fh:
                blob = fh.read()
            header = lbx.parse_header(blob, f"app {key}")
            pixels = lbx.decode_frame(blob, header, 0)
            if pixels is not None:
                palette = dict(self._palette)
                if header.has_palette:
                    palette.update(lbx.read_palette(blob, header.frame_count))
                surface = pygame.image.frombuffer(
                    lbx.rgba_bytes(pixels, palette),
                    (header.width, header.height), "RGBA")
                # once in the display's format (work order 202 A, as `ldrart`):
                # R-G-B-A is converted pixel by pixel on every blit otherwise
                surface = surface.convert_alpha() \
                    if pygame.display.get_surface() is not None else surface.copy()
        except (OSError, TypeError, lbx.LbxError, ValueError):
            surface = None
        self._cache[key] = surface
        return surface


_loaded = None


def load():
    global _loaded
    if _loaded is None:
        _loaded = InfoArt()
        log.info("Tech Review pictures: %s", "loaded" if _loaded.available
                 else _loaded.reason)
    return _loaded
