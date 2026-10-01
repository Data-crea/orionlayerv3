"""The tactical battle's artwork, extracted by the player — or its absence,
said. Work order 197 C.

`tools/combat_art_extract.py` writes every entry of the battle's LBX files as
raw blobs (`<file>/<entry>.bin`) and the battle palette (FONTS.LBX 4,
`Load_Palette_(3)`, combinit.cpp:661) into `assets/gamedata/`; this decodes
them lazily through `core/lbx.py`, keyframes composed as the engine composes
them (`decode_composed`). Nothing here is committed or shipped (decisions 38,
40, 42). **File by file through the resource roots** (decisions 16 and 72,
195's rule): a mod replaces one picture and the rest stay the game's.

THE ORIGINAL'S RULES, transcribed (`dev:doc/combat_drawing_reading.md`):

  ship picture  CMBTSHP[colour * 45 + picture_num] for a player's ship
                (`previous_owner`'s colour), MONSTER[picture_num] otherwise,
                picture 44 -> MONSTER 25 (cmbtdrw1.cpp:2533-2548)
  its ramp      CMBTSHP[colour * 45 + 44]'s 32-colour palette at 0x20; the
                attacker's ship pixels are moved to 0x20-0x3F, the
                defender's to 0x60-0x7F with its ramp there
                (cmbtdrw1.cpp:2550-2553, combinit.cpp:1482-1488) — so HD
                gives both ranges the owner's ramp
  facing        16 facings from 5 stored ones, 4 frames each (frame 0 no
                engine glow): 0-4 as stored, 5-8 stored 8-f mirrored left to
                right, 9-12 stored f-8 turned half round, 13-15 stored 16-f
                upside down (cmbtdrw1.cpp:2557-2615, bitmap.cpp:125-150 —
                `Flip_Bitmap_` mode 0 reverses each row, mode 3 the rows)
  glass         pixels 0xF0-0xFF blend with what is under them
                (animate.cpp:279-287): HD draws them at half alpha —
                DEVIATION `glass_alpha`, the original's per-effect blend
                tables are not reproduced
"""
import json
import logging
import os

import pygame

from core import lbx

log = logging.getLogger("combat")

REL = "screens/combat/assets/gamedata"
FORMAT_VERSION = 1
HOW = "python tools/combat_art_extract.py"
GLASS_FIRST = 0xF0
GLASS_ALPHA = 128


def stored_facing(facing):
    """(stored direction 0..4, mirror left-right, flip upside down) for a
    facing 0..15 — `Draw_Ship_`'s quadrant switch."""
    f = int(facing) & 15
    q = max(0, (f - 1) // 4)
    if q == 0:
        return f, False, False
    if q == 1:
        return 8 - f, True, False
    if q == 2:
        return f - 8, True, True
    return 16 - f, False, True


class CombatArt:
    """`folder` None resolves every file through the resource roots; a
    folder reads that folder only (the checks' way)."""

    def __init__(self, folder=None):
        self.folder = folder
        self.reason = ""
        self._palette = None
        self._blobs = {}
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
                self.reason = (f"The battle's artwork is format "
                               f"{manifest.get('format')}, this build reads "
                               f"{FORMAT_VERSION}. Run: {HOW}")
                return
            with open(self._path("palette.bin"), "rb") as fh:
                self._palette = lbx.screen_palette(fh.read())
        except (OSError, TypeError, ValueError, lbx.LbxError) as exc:
            self.reason = (f"The battle's artwork is not extracted ({exc}). "
                           f"Run: {HOW}")

    @property
    def available(self):
        return self._palette is not None

    def blob(self, lbx_name, entry):
        key = (lbx_name, int(entry))
        if key not in self._blobs:
            path = self._path(f"{lbx_name}/{int(entry)}.bin")
            try:
                with open(path, "rb") as fh:
                    self._blobs[key] = fh.read()
            except (OSError, TypeError):
                self._blobs[key] = None
        return self._blobs[key]

    def frame_count(self, lbx_name, entry):
        b = self.blob(lbx_name, entry)
        try:
            return lbx.parse_header(b).frame_count if b else 0
        except lbx.LbxError:
            return 0

    def palette_with(self, extra=None):
        pal = dict(self._palette or {})
        if extra:
            pal.update(extra)
        return pal

    def ramp(self, colour):
        """The colour's 32-entry ship ramp, at 0x20 AND 0x60."""
        key = ("ramp", int(colour))
        if key not in self._cache:
            out = {}
            b = self.blob("cmbtshp", int(colour) * 45 + 44)
            try:
                h = lbx.parse_header(b)
                if h.has_palette:
                    base = lbx.read_palette(b, h.frame_count)
                    for i, rgb in base.items():
                        out[i] = rgb
                        out[i - 0x20 + 0x60] = rgb
            except (lbx.LbxError, TypeError):
                pass
            self._cache[key] = out
        return self._cache[key]

    def surface(self, lbx_name, entry, frame=0, palette=None, mirror=False,
                flip=False):
        """One frame as an RGBA surface at native size, or None."""
        key = ("sprite", lbx_name, int(entry), int(frame), id(palette),
               mirror, flip)
        if key in self._cache:
            return self._cache[key]
        surf = self._painted(lbx_name, entry, frame)
        if surf is not None:
            if mirror or flip:
                surf = pygame.transform.flip(surf, mirror, flip)
            self._cache[key] = surf
            return surf
        b = self.blob(lbx_name, entry)
        if b is not None and self.available:
            try:
                h = lbx.parse_header(b)
                pal = self.palette_with()
                if h.has_palette:
                    pal.update(lbx.read_palette(b, h.frame_count))
                if palette:
                    pal.update(palette)
                px = lbx.decode_composed(b, h, frame)
                if px is not None:
                    surf = _rgba(px, h.width, h.height, pal)
                    if mirror or flip:
                        surf = pygame.transform.flip(surf, mirror, flip)
            except (lbx.LbxError, ValueError):
                surf = None
        self._cache[key] = surf
        return surf

    def _painted(self, lbx_name, entry, frame):
        """A PNG for this stored drawing, if a mod gives one (work order 197
        E, 195 §7): `<lbx>/<entry>_<frame>.png` beside the extracted blobs,
        resolved like every file here — the player's mod folder
        (`files/screens/combat/assets/gamedata/…`), a developer mod, the
        project. Used as painted: no palette, no ramp; the facings that
        are flips stay flips (a modder paints the 5 stored ones)."""
        path = self._path(f"{lbx_name}/{int(entry)}_{int(frame)}.png")
        if not path or not os.path.isfile(path):
            return None
        try:
            img = pygame.image.load(path)
        except (pygame.error, OSError):
            return None
        return img.convert_alpha() if pygame.display.get_surface() else img

    def ship(self, colour, picture, facing, glow=0, monster=False):
        """A battle unit's picture for its facing and glow frame 0..3."""
        stored, mirror, flip = stored_facing(facing)
        frame = 4 * stored + max(0, min(3, int(glow)))
        if monster or picture == 44:
            return self.surface("monster", 25 if picture == 44 else picture,
                                frame, None, mirror, flip)
        return self.surface("cmbtshp", int(colour) * 45 + int(picture), frame,
                            self.ramp(colour), mirror, flip)


def planet_picture(art, state, c):
    """(picture, size) of the battle's planet: CMBTPLNT[climate * 6 + size],
    its palette at +5 (combinit.cpp:1539-1559), or None. Moved here from the
    screen by work order 199 (the screen's line guideline)."""
    col = c.get("colony", -1)
    try:
        from core.structs import colony as colony_struct
        from core.structs import planet as planet_struct
        if col < 0:
            return None
        colony = colony_struct.SPEC.parse(state.colonies_raw[col])
        p = planet_struct.parse(state.planets_raw[colony.planet])
    except (IndexError, TypeError, AttributeError, ValueError):
        return None
    climate, size = int(p.climate), int(p.size)
    pal_blob = art.blob("cmbtplnt", climate * 6 + 5)
    extra = None
    if pal_blob:
        from core import lbx
        try:
            h = lbx.parse_header(pal_blob)
            extra = lbx.read_palette(pal_blob, h.frame_count) \
                if h.has_palette else None
        except lbx.LbxError:
            extra = None
    pic = art.surface("cmbtplnt", climate * 6 + size, 0, extra)
    return (pic, size) if pic is not None else None


def _rgba(pixels, w, h, palette):
    out = bytearray(w * h * 4)
    for i, idx in enumerate(pixels):
        if idx == 0:
            continue
        r, g, b = palette.get(idx, (idx, idx, idx))
        out[4 * i:4 * i + 4] = bytes((r, g, b, GLASS_ALPHA
                                      if idx >= GLASS_FIRST else 255))
    return pygame.image.frombuffer(bytes(out), (w, h), "RGBA").copy()
