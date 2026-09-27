"""The Ship Designer's pictures: the ship, and the weapon picker's arcs,
arc and rack words and filter buttons.

Work order 185. Decoded at load time from the raw blobs the extractors
wrote (decision 38): the arc pictures and the designer's palette from
`tools/design_art_extract.py`; the ship pictures from the Fleets screen's
extraction (`tools/fleet_art_extract.py`, the same SHIPS.LBX entries,
`ship_type + colour * 50`) — read from there, NOT copied, and decoded in
THE DESIGNER'S palette (FONTS 5) with the owner's ship ramp over 192..239,
as the designer draws them (`Load_Player_Ship_Palette_` on entry). Every
missing piece answers None; the screen then draws no picture and says
nothing invented.
"""
import json
import logging
import os

import pygame

from core import lbx
from screens.fleets import fltart

log = logging.getLogger("ship_design")

GAMEDATA = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "assets", "gamedata")
FORMAT_VERSION = 2
SHIP_STRIDE = 50


class DesignArt:
    def __init__(self, folder=GAMEDATA):
        self.folder = folder
        self.reason = ""
        self._palette = None
        self._cache = {}
        path = os.path.join(folder, "manifest.json")
        try:
            with open(path, encoding="utf-8") as fh:
                manifest = json.load(fh)
            if int(manifest.get("format", 0)) != FORMAT_VERSION:
                raise ValueError(f"format {manifest.get('format')}")
            with open(os.path.join(folder, "palette.bin"), "rb") as fh:
                self._palette = lbx.screen_palette(fh.read())
        except (OSError, ValueError, lbx.LbxError) as err:
            self.reason = (f"no designer artwork ({err}) — run "
                           "`python tools/design_art_extract.py`")

    @property
    def available(self):
        return self._palette is not None

    def arc(self, index):
        """Arc picture 0..4, or None."""
        if not self.available or not 0 <= index < 5:
            return None
        return self._decode(os.path.join(self.folder, "arcs", f"{index}.bin"))

    #: The label groups and each one's picture count (the extractor's).
    LABELS = {"arc": ("arc_words", 5), "rack": ("rack_words", 5),
              "filter": ("filters", 4)}

    def label(self, kind, index, frame=0):
        """An arc word, a rack word or a filter button (`kind`), in its
        animation frame `frame` — the status the original sets before it
        draws (`Set_Animation_Frame_`), or None."""
        folder, count = self.LABELS[kind]
        if not self.available or not 0 <= index < count:
            return None
        return self._decode(os.path.join(self.folder, folder,
                                         f"{index}.bin"), frame=frame)

    def ship(self, picture, colour):
        """The ship picture `picture` in player colour `colour`, or None."""
        fleets = fltart.load()
        if not self.available or not fleets.available:
            return None
        if not 0 <= picture < SHIP_STRIDE or not 0 <= colour < 8:
            return None
        path = os.path.join(fleets.folder, "ships",
                            f"{picture + colour * SHIP_STRIDE}.bin")
        return self._decode(path, fleets.ship_ramp(colour))

    def _decode(self, path, ramp=None, frame=0):
        key = (path, id(ramp) if ramp else None, frame)
        if key in self._cache:
            return self._cache[key]
        surface = None
        try:
            with open(path, "rb") as fh:
                blob = fh.read()
            header = lbx.parse_header(blob, os.path.basename(path))
            pixels = lbx.decode_frame(blob, header, frame)
            if pixels is not None and header.width > 2:
                palette = dict(self._palette)
                if ramp:
                    palette.update(ramp)
                if header.has_palette:
                    palette.update(lbx.read_palette(blob, header.frame_count))
                surface = pygame.image.frombuffer(
                    lbx.rgba_bytes(pixels, palette),
                    (header.width, header.height), "RGBA").convert_alpha()
        except (OSError, ValueError, lbx.LbxError):
            surface = None
        self._cache[key] = surface
        return surface


_loaded = None


def load(folder=GAMEDATA):
    global _loaded
    if _loaded is None or _loaded.folder != folder:
        _loaded = DesignArt(folder)
        log.info("designer artwork: %s", "loaded from " + folder
                 if _loaded.available else _loaded.reason)
    return _loaded
