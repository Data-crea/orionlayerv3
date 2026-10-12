"""The invasion's pictures, extracted by the player — or their absence, said.
Work order 232 C.

`tools/invasion_art_extract.py` writes the raw LBX blobs and the popup's
palette into `assets/gamedata/`; this decodes them lazily through
`core/lbx.py` and the resolver (`core.blobart`: a mod's painted PNG beside a
blob wins), as `screens/colony/colart.py` does.

TRANSCRIPTION, what the original draws and in which colours:

  a unit        COLGCBT.LBX by side, kind and state as `Action_Anim_` takes
                `_anims[(kind + side * 4) * 5 + state - 1]`
                (colgcbt.cpp:313-330), the table `Load_Combat_Anims_` fills
                (:89-163): `UNIT_ENTRY`; the tanks' five with Battleoids
                when the DEFENDER has them (:139-152); the infantry's
                colours replaced by its side's player colour, the tanks' by
                the defender's (`Replace_Colgcbt_Color_With_Player_Colors_`,
                :79-87: indices 0xC0..0xC7 to `PLAYER_COLOURS`, 0xE8..0xEB to
                `SHORT_COLOURS`, none for colour 2)
  glass         a glassed drawing's pixels 0xF0 + j blend with what lies
                under them by glass colour j (`Draw_Animated_Sprite_`,
                animate.cpp:270-290): FONTS.LBX 0's table, colour 0 made
                50 % black by `Update_Glass_Remap_Colors_` (remap.cpp:153-
                157) — the units' shadows. The original snaps each blend to
                the palette's nearest colour; HD blends exactly (the
                battle's DEVIATION `glass_alpha`, cbart's)
  the remap     the popup's icons, colonists and troops are drawn through
                `Remap_Draw_` after `Calculate_Picture_Remap_Colors_(
                C_Anims_(13))` — in COLONY2.LBX 0x32's palette, each colour
                mapped to the screen's nearest; HD draws that palette's own
                colours (`remap_palette`)
  the palette   the colony screen's while the ground combat runs
                (`COLONY::Update_Colony_Palette_`, colgcbt.cpp:198 — the
                ground's own over FONTS.LBX 2, `colart.palette`); the popup's
                is palette 0 (FONTS.LBX 1, mainpups.cpp:1294) with the planet
                picture's own over it (`Draw_Palette_`, :2444)
"""
import json
import logging
import os

import numpy as np
import pygame

from core import blobart, lbx

log = logging.getLogger("ground_combat")

GAMEDATA = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "assets", "gamedata")
#: The same folder as a tree path: read through the resolver (`core.blobart`).
REL = "screens/ground_combat/assets/gamedata"
FORMAT_VERSION = 1
HOW = "python tools/invasion_art_extract.py"

#: `Load_Combat_Anims_` (colgcbt.cpp:89-163) as `Action_Anim_` reads it:
#: (side, kind) -> the COLGCBT.LBX entries of states 1..5 (die, stand, fire,
#: walk, hit). The attacker's three infantry kinds share one set (5..9,
#: copied to 10..19), as do the defender's (25..29, copied to 30..39); the
#: defender's tanks are 20..24, from 10..14 or, with Battleoids, 15..19.
INFANTRY_ATTACKER = (1, 4, 2, 0, 3)
INFANTRY_DEFENDER = (6, 9, 7, 5, 8)
TANKS = (11, 14, 12, 10, 13)
TANKS_BATTLEOIDS = (16, 19, 17, 15, 18)
FRAME = 21

#: `_player_color_array`, `_short_player_color_array` (colgcbt.cpp:28-48),
#: by the player's colour.
PLAYER_COLOURS = (
    (146, 236, 237, 238, 239, 150, 151, 152),
    (218, 219, 220, 212, 222, 223, 224, 225),
    (192, 193, 194, 195, 196, 197, 198, 199),
    (89, 93, 97, 99, 101, 103, 105, 108),
    (112, 114, 115, 116, 117, 118, 119, 135),
    (210, 211, 212, 213, 214, 215, 216, 217),
    (121, 122, 123, 124, 124, 125, 126, 127),
    (183, 184, 185, 186, 187, 188, 189, 189))
SHORT_COLOURS = (
    (236, 237, 238, 239), (219, 221, 223, 225), (232, 232, 234, 235),
    (86, 97, 103, 107), (114, 116, 118, 119), (211, 213, 214, 216),
    (121, 123, 125, 127), (184, 185, 186, 187))
LONG_FIRST, SHORT_FIRST = 0xC0, 0xE8
#: The colour `Replace_Colgcbt_Color_With_Player_Colors_` leaves as drawn.
UNREPLACED = 2


def unit_entry(side, kind, state, battleoids):
    """The COLGCBT.LBX entry a unit is drawn with, or None (state 0 is not
    drawn; the attacker has no tanks — their `_anims` are never loaded)."""
    if not 1 <= state <= 5:
        return None
    if kind == 0:
        if side != 1:
            return None
        return (TANKS_BATTLEOIDS if battleoids else TANKS)[state - 1]
    if 1 <= kind <= 3:
        return (INFANTRY_ATTACKER if side == 0 else INFANTRY_DEFENDER)[
            state - 1]
    return None


def colour_map(colour):
    """index -> index: the side's player colour in place of the drawing's."""
    out = np.arange(256, dtype=np.uint8)
    if colour == UNREPLACED or not 0 <= colour < len(PLAYER_COLOURS):
        return out
    out[LONG_FIRST:LONG_FIRST + 8] = PLAYER_COLOURS[colour]
    out[SHORT_FIRST:SHORT_FIRST + 4] = SHORT_COLOURS[colour]
    return out


class InvasionArt:
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
                self.reason = (f"The invasion pictures are format "
                               f"{manifest.get('format')}, this build reads "
                               f"{FORMAT_VERSION}. Run: {HOW}")
                return
            with open(self._src.path("palette.json"), encoding="utf-8") as fh:
                self._base = {i: tuple(c) for i, c in enumerate(json.load(fh))}
        except (OSError, ValueError) as exc:
            self.reason = (f"The invasion pictures are not extracted "
                           f"({exc}). Run: {HOW}")

    @property
    def available(self):
        return self._base is not None

    def blob(self, stem):
        """(blob, header) of one stored drawing, or None."""
        if stem not in self._blobs:
            try:
                blob = self._src.read(f"{stem}.bin")
                self._blobs[stem] = (blob, lbx.parse_header(blob, stem))
            except (OSError, ValueError, lbx.LbxError) as exc:
                log.warning("invasion picture %s unreadable: %s", stem, exc)
                self._blobs[stem] = None
        return self._blobs[stem]

    def frames(self, stem):
        """How many frames a drawing has (0 when absent)."""
        got = self.blob(stem)
        return got[1].frame_count if got is not None else 0

    def indices(self, stem, frame):
        """The indices (h, w) of one frame as the engine composes it, or
        None."""
        key = ("idx", stem, frame)
        if key not in self._cache:
            got = self.blob(stem)
            px = None
            if got is not None:
                blob, head = got
                f = min(max(0, frame), head.frame_count - 1)
                px = lbx.decode_composed(blob, head, f)
            self._cache[key] = None if px is None else np.array(
                px, np.uint8).reshape(got[1].height, got[1].width)
        return self._cache[key]

    def remap_palette(self):
        """COLONY2.LBX 0x32's own palette — the popup's figures' colours."""
        got = self.blob("remap_picture")
        if got is None:
            return dict(self._base or {})
        blob, head = got
        return dict(lbx.read_palette(blob, head.frame_count))

    def glass(self):
        """{j: (alpha 0..255, (r, g, b))} for glass pixel 0xF0 + j."""
        if "glass" not in self._cache:
            table = {}
            try:
                with open(self._src.path("glass.json"), encoding="utf-8") as fh:
                    rows = json.load(fh)
                for j, (inten, r, g, b) in enumerate(rows[:16]):
                    table[j] = (inten, (r, g, b))
            except (OSError, ValueError):
                pass
            table[0] = (50, (0, 0, 0))     # Update_Glass_Remap_Colors_
            self._cache["glass"] = {
                j: (int(round(255 * min(100, i) / 100.0)),
                    tuple(min(255, c * 4) for c in rgb))
                for j, (i, rgb) in table.items()}
        return self._cache["glass"]

    def popup_palette(self, climate):
        """The popup's palette: palette 0 with the planet picture's over it."""
        out = dict(self._base or {})
        got = self.blob(f"planet_palette_{int(climate)}")
        if got is not None:
            blob, head = got
            out.update(lbx.read_palette(blob, head.frame_count))
        return out

    def surface(self, stem, frame, palette, remap=None, key=None):
        """One frame as a picture in `palette` ({index: rgb}), index 0
        transparent, `remap` (an index map) applied first; cached by `key`
        (the caller names the palette and the remap). A painted PNG beside
        the blob wins (`blobart`), as painted."""
        ck = ("surf", stem, frame, key)
        if ck in self._cache:
            return self._cache[ck]
        surf = self._src.painted(f"{stem}.bin", frame=frame)
        if surf is None:
            idx = self.indices(stem, frame)
            if idx is not None:
                if remap is not None:
                    idx = remap[idx]
                lut = np.zeros((256, 3), np.uint8)
                for i, rgb in palette.items():
                    if 0 <= i < 256:
                        lut[i] = rgb[:3]
                rgb = lut[idx]
                surf = pygame.Surface((idx.shape[1], idx.shape[0]),
                                      pygame.SRCALPHA)
                view = pygame.surfarray.pixels3d(surf)
                view[...] = rgb.transpose(1, 0, 2)
                del view
                alpha = pygame.surfarray.pixels_alpha(surf)
                alpha[...] = np.where(idx != 0, 255, 0).T
                del alpha
                if self.glassed(stem):
                    self._glass(surf, idx)
        self._cache[ck] = surf
        return surf


    def glassed(self, stem):
        got = self.blob(stem)
        return got is not None and bool(got[1].flags & lbx.FLAG_GLASSED)

    def _glass(self, surf, idx):
        """Glass pixels as their colour at their intensity: drawn OVER what
        lies under them by the blit, so they blend with it."""
        table = self.glass()
        view = pygame.surfarray.pixels3d(surf)
        alpha = pygame.surfarray.pixels_alpha(surf)
        for j in range(16):
            mask = (idx == 0xF0 + j).T
            if not mask.any():
                continue
            a, rgb = table.get(j, (0, (0, 0, 0)))
            view[mask] = rgb
            alpha[mask] = a
        del view, alpha


_loaded = None


def load():
    global _loaded
    if _loaded is None:
        _loaded = InvasionArt()
        log.info("invasion pictures: %s", "loaded" if _loaded.available
                 else _loaded.reason)
    return _loaded
