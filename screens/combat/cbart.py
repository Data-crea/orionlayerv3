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
  glass         pixels 0xF0-0xFF blend with what is under them only in a
                GLASSED drawing — its header's flag `ANIMATION_FLAG_GLASSED`
                (animate.cpp:122-160, 572-640), or one the battle glasses as
                it draws (`Set_Picture_Glassed_`: the planet's shield flares,
                beams.cpp:605, :704; the small tractor, CMBTSFX 2,
                cmbtspec.cpp:164, :209, :668); in every other drawing they
                are colours of its palette, opaque — the battle's planets
                (CMBTPLNT, flags 0; draw.cpp:59-95), a few ship and monster
                pixels (work order 219: until then HD glassed every drawing,
                and 6-43 % of a planet let the stars through).
                TRANSCRIPTION `glassed_only`. In a glassed drawing HD draws
                them at half alpha — DEVIATION `glass_alpha` — unless the
                drawing names its glass table (`glass`, work order 210):
                then glass pixel 0xF0 + j is the table's colour j at its per
                cent, j = 0 black at 50 (`Update_Glass_Remap_Colors_`,
                remap.cpp:153-187; the tables of combinit.cpp:854-990: shield
                and stasis ball, pulsar, warp core, tractor, black hole,
                plasma web, stellar converter). The original snaps each
                blend to the palette's nearest colour; HD blends exactly.
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


def derived(new, source):
    """`new`, made from `source` at the same size (a copy brightened,
    recoloured, given an alpha), with `source`'s painted factor. Every
    picture made from a battle picture passes through here or
    `painted_as`: a copy without it is drawn k times too large (work order
    219: the shield flare drew a painted ship 4 or 8 times its size while
    it lasted, the cloak too)."""
    return painted_as(new, hd_factor(source))

#: No cap: a painted picture is held at the factor its file has.
DETAIL_FULL = 1 << 16
#: The filter a painted picture is shrunk by when the detail setting holds
#: it smaller than its file (`held`): Lanczos keeps its edges and fine lines
#: where an average would soften them; Pillow shrinks RGBA premultiplied, so
#: no dark fringe comes in from the transparent pixels.
HOLD_FILTER = "LANCZOS"


def held(img, w, h, k):
    """`img`, a painted picture larger than k times its drawing (w x h),
    shrunk ONCE to exactly k x that size — at load, before the owner's
    colour is laid on (HD EXTENSION `painted_detail`, work order 219)."""
    from PIL import Image
    size = (w * k, h * k)
    pil = Image.frombytes("RGBA", img.get_size(),
                          pygame.image.tobytes(img, "RGBA"))
    pil = pil.resize(size, getattr(Image.Resampling, HOLD_FILTER))
    return display_format(pygame.image.frombytes(pil.tobytes(), size,
                                                 "RGBA").copy())


def smooth(surf, size):
    """`surf` scaled smoothly to `size`. Shrinking, an area average
    (Pillow's BOX, on premultiplied alpha): `pygame.transform.smoothscale`
    shrinking by a ratio that is not whole sums its fixed-point weights to
    252-253 of 255, so every opaque pixel of a shrunk painted picture came
    out 1 % see-through and 2-3 levels darker (work order 219: the stars
    showed through a painted planet at 6 x, and through a 4 x ship at the
    1080p opening view, since work order 214). Enlarging, smoothscale is
    exact and stays."""
    w, h = surf.get_size()
    if size[0] >= w and size[1] >= h:
        return pygame.transform.smoothscale(surf, size)
    from PIL import Image
    pil = Image.frombytes("RGBA", (w, h), pygame.image.tobytes(surf, "RGBA"))
    pil = pil.resize(tuple(size), Image.Resampling.BOX)
    return display_format(pygame.image.frombytes(pil.tobytes(), tuple(size),
                                                 "RGBA").copy())


REL = "screens/combat/assets/gamedata"
FORMAT_VERSION = 1
HOW = "python tools/combat_art_extract.py"
GLASS_FIRST = 0xF0
GLASS_ALPHA = 128
#: Drawings without the glassed flag that the battle glasses as it draws
#: them (`Set_Picture_Glassed_`): the planet's shield flares, BEAMS
#: 113 + size * 5 + rotation for sizes 4-7 (beams.cpp:605, :704, :808-819),
#: and the small tractor, CMBTSFX 2 (combinit.cpp:909; cmbtspec.cpp:164,
#: :209, :668). Every other picture of the battle that is glassed carries
#: the flag (work order 219, every header read).
GLASSED_AS_DRAWN = frozenset([("beams", e) for e in range(133, 153)]
                             + [("cmbtsfx", 2)])


def glassed(lbx_name, entry, header):
    """Do the drawing's pixels 0xF0-0xFF blend (TRANSCRIPTION
    `glassed_only`), or are they colours?"""
    return bool(header.flags & lbx.FLAG_GLASSED) or \
        (lbx_name, int(entry)) in GLASSED_AS_DRAWN


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
        #: the largest factor a painted picture is held at (`set_detail`)
        self.detail = DETAIL_FULL
        #: the livery painted ships are coloured in (`set_livery`)
        from core import livery
        self.livery = livery.DEFAULT
        self._load()

    def set_detail(self, cap):
        """Hold painted pictures at `cap` times their drawing at most (HD
        EXTENSION `painted_detail`, `core/paintdetail`). A change drops
        every picture made so far, painted or made from one; True if it
        did. The battle asks once, when its first view is built."""
        cap = int(cap) if cap else DETAIL_FULL
        if cap == self.detail:
            return False
        self.detail = cap
        self._drop()
        return True

    def set_livery(self, liv):
        """Colour painted ships in the livery `liv` (HD EXTENSION `livery`,
        `core/livery`, work order 220). A change drops every picture made
        so far in the old one, and only those: no picture of the old livery
        stays in memory (part D), while the files read and held stay (they
        do not depend on it; the window's preview asks at every change).
        True if it did."""
        if liv == self.livery:
            return False
        self.livery = liv
        for key in [k for k in self._cache
                    if k[0] in ("plating", "plating_src", "plating_lit",
                                "plating_turn")]:
            del self._cache[key]
        cc = getattr(self, "_cloak_cache", None)
        if cc is not None:
            cc.clear()
        return True

    def _drop(self):
        self._cache.clear()
        cc = getattr(self, "_cloak_cache", None)
        if cc is not None:
            cc.clear()

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
                        self.glass(glass) if glass else None,
                        glassed(lbx_name, entry, h)))
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
            if k > self.detail:
                img, k = held(img, h.width, h.height, self.detail), self.detail
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
        """An index array (`indexed`) as the RGBA surface `surface` makes —
        a unit's picture (`cbcloak`): not a glassed drawing."""
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
        lbx_name, entry = self._unit_entry(colour, picture, monster)
        from . import cbpulse
        if cbpulse.own(self, lbx_name, entry, stored, glow, mirror,
                       flip) is not None:
            return None
        if lbx_name == "monster":
            return self.indexed("monster", entry, frame, None, mirror, flip)
        return self.indexed("cmbtshp", entry, frame, self.ramp(colour),
                            mirror, flip)

    @staticmethod
    def _unit_entry(colour, picture, monster):
        """(file, entry) of a unit's stored drawing (cmbtdrw1.cpp:2533)."""
        if monster or picture == 44:
            return "monster", 25 if picture == 44 else int(picture)
        return "cmbtshp", int(colour) * 45 + int(picture)

    def ship(self, colour, picture, facing, glow=0, monster=False):
        """A battle unit's picture for its facing and glow frame 0..3: the
        colour's own painted file, else the colour-free painted picture in
        the owner's colour (`cbpaint`, HD EXTENSION `plating_colour`), else
        the stored drawing."""
        stored, mirror, flip = stored_facing(facing)
        frame = 4 * stored + max(0, min(3, int(glow)))
        lbx_name, entry = self._unit_entry(colour, picture, monster)
        if lbx_name == "cmbtshp":
            from . import cbpaint
            free = cbpaint.ship(self, colour, picture, facing, glow)
            if free is not None:
                return free
        # a painted file without this glow frame: made from its frame 0,
        # not the stored drawing between painted ones (`cbpulse`)
        from . import cbpulse
        made = cbpulse.own(self, lbx_name, entry, stored, glow, mirror, flip)
        if made is not None:
            return made
        if lbx_name == "monster":
            return self.surface("monster", entry, frame, None, mirror, flip)
        return self.surface("cmbtshp", entry, frame, self.ramp(colour),
                            mirror, flip)


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


def _rgba(pixels, w, h, palette, glass=None, is_glassed=False):
    """Indices to RGBA: a glass pixel blends (`glass`'s table, else half
    alpha) only in a glassed drawing (`glassed`)."""
    out = bytearray(w * h * 4)
    for i, idx in enumerate(pixels):
        if idx == 0:
            continue
        if glass is not None and idx >= GLASS_FIRST:
            out[4 * i:4 * i + 4] = bytes(glass[idx - GLASS_FIRST])
            continue
        r, g, b = palette.get(idx, (idx, idx, idx))
        out[4 * i:4 * i + 4] = bytes((r, g, b, GLASS_ALPHA if is_glassed
                                      and idx >= GLASS_FIRST else 255))
    return pygame.image.frombuffer(bytes(out), (w, h), "RGBA").copy()
