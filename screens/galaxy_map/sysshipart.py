"""The star system window's fleet pictures, extracted by the player — or their
absence, said. Work order 326 C.

TRANSCRIPTION `fleet_bar_picture`: the original draws each owner's icon in
the window's bar as a picture of its own, BUFFER0.LBX 273 + the player's
colour for a player, 281 for owner 8 and (owner - 9) + 282 for a monster
(`SYS::Buffer_Reload_System_Ships`, sys.cpp:1032-1052), at its native size
(`animate::Draw`, `Draw_System_Ship_Icons_`, sys.cpp:1062-1094) — eight
different ships, one per player colour, not the map's ship icon. Until work
order 326 HD drew the owner's tinted map icon there (`sysfleets.icon`, which
stays the fallback while the pictures are not extracted; the marking and
its check live with `sysfleets`).

`tools/sysship_art_extract.py` writes the raw blobs (`sysship_<entry>.bin`)
and the main screen's palette into `assets/gamedata/`; this decodes them
lazily through `core/lbx.py`, file by file through the resource roots
(`core.blobart.Source`), so a PNG painted for an entry,
`sysship_<entry>_0.png`, is drawn as painted (`core.blobart`'s painted-PNG
route, marked there). Nothing here is committed or shipped (decisions 38,
40, 42).
"""
import json
import logging

import pygame

from core import blobart, lbx

log = logging.getLogger("galaxy_map.sysship")

REL = "screens/galaxy_map/assets/gamedata"
FORMAT_VERSION = 1
HOW = "python tools/sysship_art_extract.py"
#: sys.cpp:1036-1051: a player's colour 0-7, owner 8, monsters 9-14.
PLAYER_BASE, OWNER_8, MONSTER_BASE = 273, 281, 282
MAX_PLAYERS, LAST_OWNER = 8, 14


def entry(owner, colour):
    """The BUFFER0.LBX entry the bar draws for `owner` (`colour`: the
    player's `color` field), or None where the original draws nothing
    (sys.cpp:1053, owner 15 and on)."""
    if owner is None or owner < 0:
        return None
    if owner < MAX_PLAYERS:
        return None if colour is None else PLAYER_BASE + int(colour)
    if owner == MAX_PLAYERS:
        return OWNER_8
    if owner <= LAST_OWNER:
        return owner - (MAX_PLAYERS + 1) + MONSTER_BASE
    return None


class SysShipArt:
    """`folder` None resolves every file through the resource roots; a
    folder reads that folder only (the checks' way)."""

    def __init__(self, folder=None):
        self._src = blobart.Source(REL, folder)
        self.reason = ""
        self._palette = None
        self._cache = {}
        self._scaled = {}
        try:
            with open(self._src.path("sysship_manifest.json"),
                      encoding="utf-8") as fh:
                manifest = json.load(fh)
            if int(manifest.get("format", 0)) != FORMAT_VERSION:
                self.reason = (f"the fleet pictures are format "
                               f"{manifest.get('format')}, this build reads "
                               f"{FORMAT_VERSION}. Run: {HOW}")
                return
            with open(self._src.path("sysship_palette.json"),
                      encoding="utf-8") as fh:
                self._palette = {i: tuple(c) for i, c in
                                 enumerate(json.load(fh))}
        except (OSError, TypeError, ValueError) as exc:
            self.reason = (f"the fleet pictures are not extracted ({exc}). "
                           f"Run: {HOW}")

    @property
    def available(self):
        return self._palette is not None

    def picture(self, number):
        """BUFFER0.LBX entry `number` at its native size, or None. Frame 0:
        the entries' eight frames are one picture (measured, work order
        326), so the original's animation shows nothing moving."""
        if not self.available or number is None:
            return None
        if number in self._cache:
            return self._cache[number]
        name = f"sysship_{int(number)}.bin"
        surface = self._src.painted(name)
        if surface is None:
            try:
                blob = self._src.read(name)
                header = lbx.parse_header(blob, name)
                pixels = lbx.decode_frame(blob, header, 0)
                if pixels is not None:
                    surface = pygame.image.frombuffer(
                        lbx.rgba_bytes(pixels, self._palette),
                        (header.width, header.height), "RGBA")
                    surface = surface.convert_alpha() \
                        if pygame.display.get_surface() is not None \
                        else surface.copy()
            except (OSError, TypeError, lbx.LbxError, ValueError):
                surface = None
        self._cache[number] = surface
        return surface

    def scaled(self, number, scale, box_w, box_h):
        """Entry `number` grown by the largest WHOLE step not above `scale`
        (device px per native px; the original draws it 1:1 on its 640x480
        screen) that fits `box_w` x `box_h`, nearest neighbour, so every
        pixel stays the game's (the Fleets art's rule, decision 28). Only a
        box too small for the native picture shrinks it, smoothly."""
        img = self.picture(number)
        if img is None:
            return None
        w, h = img.get_size()
        step = int(min(float(scale), box_w / max(1, w), box_h / max(1, h)))
        if step >= 1:
            size = (w * step, h * step)
        else:
            f = min(box_w / max(1, w), box_h / max(1, h))
            size = (max(1, int(w * f)), max(1, int(h * f)))
        key = (number, size)
        hit = self._scaled.get(key)
        if hit is None:
            if size == (w, h):
                hit = img
            elif step >= 1:
                hit = pygame.transform.scale(img, size)
            else:
                hit = pygame.transform.smoothscale(img, size)
            if len(self._scaled) > 64:
                self._scaled.clear()
            self._scaled[key] = hit
        return hit


_loaded = None


def load():
    global _loaded
    if _loaded is None:
        _loaded = SysShipArt()
        log.info("system window fleet pictures: %s",
                 "loaded" if _loaded.available else _loaded.reason)
    return _loaded
