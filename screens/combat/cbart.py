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
                DEVIATION `glass_alpha` — unless the drawing names its
                glass table (`glass`, work order 210): then glass pixel
                0xF0 + j is the table's colour j at its per cent, j = 0
                black at 50 (`Update_Glass_Remap_Colors_`, remap.cpp:153-187;
                the tables of combinit.cpp:854-990: shield and stasis ball,
                pulsar, warp core, tractor, black hole, plasma web, stellar
                converter). The original snaps each blend to the palette's
                nearest colour; HD blends exactly.
"""
import json
import logging
import os
import weakref

import pygame

from core import lbx

log = logging.getLogger("combat")

#: HD EXTENSION `hd_painted` (decision 80's sibling, decision 81: Data, work
#: order 214): a painted picture may carry k times the pixels of the stored
#: drawing it replaces, k a whole number, width and height exactly; it is
#: drawn at the stored drawing's size, so its detail shows as the camera
#: zooms in. The original draws its 640 x 480 drawings and nothing finer.
#: Held per surface, weakly: a flip of a painted picture keeps its factor.
_FACTOR = weakref.WeakKeyDictionary()


def hd_factor(surf):
    """How many pixels of `surf` make one pixel of the drawing it stands
    for: 1 for a stored drawing, k for a painted picture at k times it."""
    return _FACTOR.get(surf, 1) if surf is not None else 1


def native_size(surf):
    """`surf`'s size in the stored drawing's pixels."""
    k = hd_factor(surf)
    w, h = surf.get_size()
    return w // k, h // k


def painted_as(surf, k):
    """`surf`, a picture made from a painted one at k times its drawing
    (stretched, turned), marked so that `cbdraw.scaled` shrinks it by k:
    a new surface has lost the mark (work order 215)."""
    if k > 1 and surf is not None:
        _FACTOR[surf] = k
    return surf

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

    def glass(self, name):
        """The glass table `name` (combinit.cpp:854-990): sixteen (r, g, b,
        alpha), entry 0 black at 50 % (remap.cpp:154-157)."""
        key = ("glass", name)
        if key in self._cache:
            return self._cache[key]
        pal = self.palette_with()

        def own(lbx_name, entry):
            out = dict(pal)
            b = self.blob(lbx_name, entry)
            try:
                h = lbx.parse_header(b)
                if h.has_palette:
                    out.update(lbx.read_palette(b, h.frame_count))
            except (lbx.LbxError, TypeError):
                pass
            return out
        rows = [(0, 0, 0, 50)]
        for j in range(1, 16):
            if name == "shield":
                rows.append(((2 * j + 13) * 4, (2 * j + 30) * 4, 252,
                             23 + 3 * (j - 1)))
                continue
            if name == "pulsar":
                src, at, pct = own("cmbtsfx", 0x34), 144 + j, 53 + 3 * (j - 1)
            elif name == "warp_core":
                src, at, pct = own("sphersfx", 0), 144 + j, 53 + 3 * (j - 1)
            elif name == "tractor":
                src, at, pct = pal, 80 + j // 2, 23 + 3 * (j - 1)
            elif name == "bhg":
                src, at, pct = own("cmbtsfx", 0x2E), 144 + j, 2 * j + 60
            elif name == "plasma_web":
                src, at, pct = pal, 176 + j, min(100, (3 * j + 15) * 2)
            elif name == "stellar_converter":
                src, at, pct = own("cmbtsfx", 0x28), 144 + 2 * j, \
                    53 + 3 * (j - 1)
            else:
                raise KeyError(name)
            rows.append((*src.get(at, (0, 0, 0)), pct))
        table = [(r, g, b, min(255, pct * 255 // 100)) for r, g, b, pct in rows]
        self._cache[key] = table
        return table

    def surface(self, lbx_name, entry, frame=0, palette=None, mirror=False,
                flip=False, glass=None):
        """One frame as an RGBA surface at native size, or None; `glass`
        names the table its glass pixels blend by (`glass`)."""
        key = ("sprite", lbx_name, int(entry), int(frame), id(palette),
               mirror, flip, glass)
        if key in self._cache:
            return self._cache[key]
        surf = self._painted(lbx_name, entry, frame)
        if surf is not None:
            if mirror or flip:
                k = hd_factor(surf)
                surf = pygame.transform.flip(surf, mirror, flip)
                if k > 1:
                    _FACTOR[surf] = k
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
                    surf = display_format(_rgba(
                        px, h.width, h.height, pal,
                        self.glass(glass) if glass else None))
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
        are flips stay flips (a modder paints the 5 stored ones).

        HD EXTENSION `hd_painted` (decision 81): at the stored drawing's
        size or k times it (k whole, both sides exactly), drawn at the
        stored drawing's size; any other size is refused with one log line
        and the stored drawing is drawn (decision 50's rule: a loader checks
        a file's size and refuses a wrong one). Without the extracted
        drawing there is no size to check against: used as painted."""
        return self.painted_file(lbx_name, f"{int(entry)}_{int(frame)}.png",
                                 entry)

    def painted_file(self, lbx_name, name, size_entry):
        """The painted PNG `<lbx>/<name>`, sized against the stored drawing
        `size_entry` (decision 81, as `_painted`), or None. Asked once per
        name: a wrong size logs its one line once, and the battle's per-frame
        lookups (`cbpaint`) do not reload the file (work order 217)."""
        key = ("painted", lbx_name, name)
        if key not in self._cache:
            self._cache[key] = self._load_painted(lbx_name, name, size_entry)
        return self._cache[key]

    def _load_painted(self, lbx_name, name, entry):
        path = self._path(f"{lbx_name}/{name}")
        if not path or not os.path.isfile(path):
            return None
        try:
            img = display_format(pygame.image.load(path))
        except (pygame.error, OSError):
            return None
        b = self.blob(lbx_name, entry)
        try:
            h = lbx.parse_header(b) if b else None
        except lbx.LbxError:
            h = None
        if h is None:
            return img
        w, hh = img.get_size()
        k = w // h.width if h.width else 0
        if k >= 1 and w == k * h.width and hh == k * h.height:
            if k > 1:
                _FACTOR[img] = k
            return img
        log.warning("combat: %s is %d x %d; a painted picture is the stored "
                    "drawing's %d x %d or a whole multiple of it — the "
                    "game's drawing is used", os.path.basename(path), w, hh,
                    h.width, h.height)
        return None

    def indexed(self, lbx_name, entry, frame=0, palette=None, mirror=False,
                flip=False):
        """One frame as palette indices — (h x w uint8 array, its palette)
        — flipped as `surface` flips it, or None (no art, or a painted
        picture: a mod's PNG has no indices). For drawings that remap the
        indices first, as the original's `Plasma_Darken_` and
        `Outline_Bitmap_` do (`cbcloak`, work order 210 C1)."""
        if self._painted(lbx_name, entry, frame) is not None:
            return None
        b = self.blob(lbx_name, entry)
        if b is None or not self.available:
            return None
        try:
            import numpy as np
            h = lbx.parse_header(b)
            pal = self.palette_with()
            if h.has_palette:
                pal.update(lbx.read_palette(b, h.frame_count))
            if palette:
                pal.update(palette)
            px = lbx.decode_composed(b, h, frame)
            if px is None:
                return None
            arr = np.frombuffer(bytes(px), dtype=np.uint8).reshape(
                h.height, h.width)
        except (lbx.LbxError, ValueError):
            return None
        if mirror:
            arr = arr[:, ::-1]
        if flip:
            arr = arr[::-1, :]
        return np.ascontiguousarray(arr), pal

    def from_indices(self, pixels, palette):
        """An index array (`indexed`) as the RGBA surface `surface` makes."""
        h, w = pixels.shape
        return display_format(_rgba(pixels.tobytes(), w, h, palette))

    def ship_indices(self, colour, picture, facing, glow=0, monster=False):
        """`ship`'s frame as indices (`indexed`); None for a painted
        picture, the colour-free one too (`cbpaint`)."""
        stored, mirror, flip = stored_facing(facing)
        frame = 4 * stored + max(0, min(3, int(glow)))
        if not (monster or picture == 44):
            from . import cbpaint
            if cbpaint.ship(self, colour, picture, facing, glow) is not None:
                return None
        if monster or picture == 44:
            return self.indexed("monster", 25 if picture == 44 else picture,
                                frame, None, mirror, flip)
        return self.indexed("cmbtshp", int(colour) * 45 + int(picture), frame,
                            self.ramp(colour), mirror, flip)

    def ship(self, colour, picture, facing, glow=0, monster=False):
        """A battle unit's picture for its facing and glow frame 0..3: the
        colour's own painted file, else the colour-free painted picture in
        the owner's colour (`cbpaint`, HD EXTENSION `plating_colour`), else
        the stored drawing."""
        stored, mirror, flip = stored_facing(facing)
        frame = 4 * stored + max(0, min(3, int(glow)))
        if monster or picture == 44:
            return self.surface("monster", 25 if picture == 44 else picture,
                                frame, None, mirror, flip)
        from . import cbpaint
        free = cbpaint.ship(self, colour, picture, facing, glow)
        if free is not None:
            return free
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


def display_format(surf):
    """The surface in the display's own pixel format, once, after decoding
    (work order 202 A). `_rgba` builds R-G-B-A bytes (red mask 0xff); the
    display keeps red at 0xff0000 (Xvfb's x11 and SDL's dummy driver,
    measured in 202), so SDL converted every pixel of every blit: the
    three star layers alone cost 148 ms a frame
    (`dev:doc/combat_lag_analysis.md` §2, item 1). Converting changes no
    pixel (201's counter-test, 202's walk over every picture).
    Without a display (a tool that never opens one) the surface stays as
    it is: `convert_alpha` needs a display to convert to."""
    if surf is None or pygame.display.get_surface() is None:
        return surf
    return surf.convert_alpha()


def _rgba(pixels, w, h, palette, glass=None):
    out = bytearray(w * h * 4)
    for i, idx in enumerate(pixels):
        if idx == 0:
            continue
        if glass is not None and idx >= GLASS_FIRST:
            out[4 * i:4 * i + 4] = bytes(glass[idx - GLASS_FIRST])
            continue
        r, g, b = palette.get(idx, (idx, idx, idx))
        out[4 * i:4 * i + 4] = bytes((r, g, b, GLASS_ALPHA
                                      if idx >= GLASS_FIRST else 255))
    return pygame.image.frombuffer(bytes(out), (w, h), "RGBA").copy()
