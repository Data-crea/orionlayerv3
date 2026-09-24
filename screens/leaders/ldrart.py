"""The Leaders screen's own artwork, decoded at load time.

**TRANSCRIPTION.** Every sprite here is one the original draws, at the
entry the original asks for (`tools/officer_art_extract.py` names each
entry and the line that loads it); nothing in this file chooses a
picture or invents a colour. What the screen does with a sprite — how
large it is drawn — is decided in `ldrdraw` and marked there.

WHERE THE BYTES COME FROM. The extractor, out of the player's own
Master of Orion 2, as RAW LBX ENTRY BLOBS (decision 38) — the Fleets
screen's shape, `screens/fleets/fltart.py`, whose decode path this
repeats for a different set of files. The files are gitignored and the
smoke test refuses game data anywhere in the tree (decisions 40 and
42), so **the normal state of a fresh clone is that this loader finds
nothing**: `available` is False, `reason` says how to get the files,
and the screen draws its words and boxes without the pictures.

THE PALETTE IS THE SCREEN'S. `Fade_Into_Leaders_Screen_` loads
`fonts::Load_Palette_(8, 0, 0xFF)` (officer.cpp:674), which is
FONTS.LBX entry 9 (fonts.cpp:73) — the same palette the Fleets screen
uses. A sprite that carries its own palette overrides its range, as
`Set_Animation_Palette_` does.
"""
import json
import logging
import os

import pygame

from core import lbx

log = logging.getLogger("orionlayer")

#: Where `tools/officer_art_extract.py` writes. Gitignored.
GAMEDATA = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "assets", "gamedata")

FORMAT_VERSION = 1

#: How to get the files, said once, where the screen can show it.
HOW = "python tools/officer_art_extract.py"

#: `MAX_LEADERS`; a `pict_num` outside it has no portrait.
PORTRAITS = 67
SKILL_ICONS = 27
STARS = 11
SMALL_SHIPS = 15


class LeaderArt:
    """The extracted artwork, or an honest account of its absence."""

    def __init__(self, folder=GAMEDATA):
        self.folder = folder
        self.reason = ""
        self._palette = None
        self._cache = {}
        self._manifest = self._load_manifest()

    def _load_manifest(self):
        path = os.path.join(self.folder, "manifest.json")
        if not os.path.exists(path):
            self.reason = (f"The game's own Leaders artwork is not "
                           f"extracted. Run: {HOW}")
            return None
        try:
            with open(path, encoding="utf-8") as fh:
                manifest = json.load(fh)
        except (OSError, ValueError) as exc:
            self.reason = f"{path} could not be read ({exc}). Run: {HOW}"
            return None
        found = manifest.get("format")
        if found != FORMAT_VERSION:
            self.reason = (f"The extracted artwork is format {found}, "
                           f"this build reads {FORMAT_VERSION}. Run: {HOW}")
            return None
        try:
            with open(os.path.join(self.folder, "palette.bin"), "rb") as fh:
                self._palette = lbx.screen_palette(fh.read())
        except (OSError, lbx.LbxError) as exc:
            self.reason = f"The screen palette is unusable ({exc}). Run: {HOW}"
            return None
        return manifest

    @property
    def available(self):
        return self._manifest is not None

    def palette_rgb(self, index):
        """The screen palette's colour at `index`, or None — how a
        transcribed colour INDEX becomes a colour (see `ldrdraw`)."""
        if not self.available:
            return None
        return self._palette.get(int(index))

    # ── The pictures ──────────────────────────────────────

    def sprite(self, name, frame=0):
        """A named entry (`officer_art_extract.OFFICER_ENTRIES` or the
        three popup pieces), one frame, or None."""
        if not self.available:
            return None
        return self._sprite(os.path.join(self.folder, "officer",
                                         f"{name}.bin"), frame)

    def portrait(self, pict_num, dark=False):
        """OFFICER.LBX `0x15 + pict_num`, or the darkened `0x8F + n`
        (officer.cpp:2656, :3533) — or None."""
        n = int(pict_num)
        if not 0 <= n < PORTRAITS:
            return None
        return self.sprite(f"{'dark' if dark else 'portrait'}_{n}")

    def skill_icon(self, skill_id):
        """OFFICER.LBX `0x58 + skill_id / 2` (officer.cpp:3574-3576)."""
        k = int(skill_id) // 2
        if not 0 <= k < SKILL_ICONS:
            return None
        return self.sprite(f"skill_{k}")

    def star(self, colour, frame=0):
        """A galaxy-box star, OFFICER.LBX `0x82 + colour` (:2206-2214)."""
        if not 0 <= int(colour) < STARS:
            return None
        return self.sprite(f"star_{int(colour)}", frame)

    # ── Decoding (fltart's path, for this folder) ─────────

    def _sprite(self, path, frame=0):
        key = (path, frame)
        if key in self._cache:
            return self._cache[key]
        surface = None
        try:
            with open(path, "rb") as fh:
                blob = fh.read()
            header = lbx.parse_header(blob, os.path.basename(path))
            pixels = lbx.decode_frame(blob, header, frame)
            if pixels is not None:
                palette = dict(self._palette)
                if header.has_palette:
                    palette.update(lbx.read_palette(blob, header.frame_count))
                rgba = lbx.rgba_bytes(pixels, palette)
                surface = pygame.image.frombuffer(
                    rgba, (header.width, header.height), "RGBA")
                if pygame.display.get_surface() is not None:
                    surface = surface.convert_alpha()
                else:
                    surface = surface.copy()
        except (OSError, lbx.LbxError, ValueError):
            surface = None
        self._cache[key] = surface
        return surface


_loaded = None


def load(folder=GAMEDATA):
    """The one instance. Decoding is lazy; this only reads the manifest."""
    global _loaded
    if _loaded is None or _loaded.folder != folder:
        _loaded = LeaderArt(folder)
        log.info("leaders artwork: %s",
                 "loaded from " + folder if _loaded.available
                 else _loaded.reason)
    return _loaded
