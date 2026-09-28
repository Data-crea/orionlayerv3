"""The audience's pictures: the race's room and its ambassador.

Work order 185 part 10. Decoded at load time from the raw blobs
`tools/audience_art_extract.py` wrote (decision 38), in the palette the
race's cursor picture carries (the original installs it with
`Draw_Palette_`, dip_scrn_main.cpp:465-480). The room is frame 0 of its
entry; the ambassador frame 0 of its, drawn at (0, 0) over the room as
`Setup_Ambassador_Pic_` draws it — the picture the original shows with
animations off (:1665-1678). Every missing piece answers None; the screen
then draws the stage without it.
"""
import json
import logging
import os

import pygame

from core import lbx

log = logging.getLogger("audience")

GAMEDATA = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "assets", "gamedata")
FORMAT_VERSION = 1


class AudienceArt:
    def __init__(self, folder=GAMEDATA):
        self.folder = folder
        self.reason = ""
        self.races = 0
        self._cache = {}
        try:
            with open(os.path.join(folder, "manifest.json"),
                      encoding="utf-8") as fh:
                manifest = json.load(fh)
            if int(manifest.get("format", 0)) != FORMAT_VERSION:
                raise ValueError(f"format {manifest.get('format')}")
            self.races = int(manifest.get("races", 0))
        except (OSError, ValueError) as err:
            self.reason = (f"no audience artwork ({err}) — run "
                           "`python tools/audience_art_extract.py`")

    @property
    def available(self):
        return self.races > 0

    def _blob(self, group, race):
        with open(os.path.join(self.folder, group, f"{race}.bin"),
                  "rb") as fh:
            return fh.read()

    def _palette(self, race):
        blob = self._blob("palettes", race)
        header = lbx.parse_header(blob, "palette")
        return lbx.read_palette(blob, header.frame_count)

    def picture(self, group, race):
        """"rooms" or "ambassadors" for `race`, frame 0, or None."""
        key = (group, race)
        if key in self._cache:
            return self._cache[key]
        surface = None
        if self.available and 0 <= race < self.races:
            try:
                blob = self._blob(group, race)
                header = lbx.parse_header(blob, group)
                pixels = lbx.decode_frame(blob, header, 0)
                if pixels is not None:
                    surface = pygame.image.frombuffer(
                        lbx.rgba_bytes(pixels, self._palette(race)),
                        (header.width, header.height), "RGBA").convert_alpha()
            except (OSError, ValueError, lbx.LbxError):
                surface = None
        self._cache[key] = surface
        return surface


_loaded = None


def load(folder=GAMEDATA):
    global _loaded
    if _loaded is None or _loaded.folder != folder:
        _loaded = AudienceArt(folder)
        log.info("audience artwork: %s", "loaded from " + folder
                 if _loaded.available else _loaded.reason)
    return _loaded
