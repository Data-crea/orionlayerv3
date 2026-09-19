"""The Fleets screen's own artwork, decoded at load time.

**TRANSCRIPTION.** Every sprite here is one the original draws, at the
entry the original asks for; nothing in this file chooses a picture,
invents a colour or decides a size. What it is allowed to do is
magnify, and that one thing is marked below.

WHERE THE BYTES COME FROM. `tools/fleet_art_extract.py`, out of the
player's own Master of Orion 2, as RAW LBX ENTRY BLOBS — decision 38:
the extractor hands the bytes over untouched and the decoding happens
here, so a fix to `core/lbx` needs no re-extraction. The files are
gitignored and the smoke test refuses game data anywhere in the tree
(decisions 40 and 42), so **the normal state of a fresh clone is that
this loader finds nothing**, and that is a STATE and not an error:
`available` is False, `reason` says how to get the files, and the
screen draws what it drew before (work order 142 D1.4).

THE PALETTE IS THE SCREEN'S, NOT THE SPRITE'S. `flt1.cpp:555` calls
`fonts::Load_Palette_(8, 0, 255)`, which is FONTS.LBX entry 9
(fonts.cpp:73, `palette_id + 1`) — so that is the palette these
sprites are drawn in, and `palette.bin` is it. A sprite that carries
its OWN palette overrides that range for itself, exactly as
`Set_Animation_Palette_` does. Without the screen palette
`lbx.rgba_bytes` would answer a grey ramp, which is honest and is not
the picture.

**HOW THE ORIGINAL COLOURS A SHIP: BY PALETTE.** Not by a remap table
and not by tinted artwork — this was read wrong twice on the way here
and the evidence is worth stating. The ship sprites are drawn in
palette indices 192..239, which the SCREEN palette above leaves as
bright green `(0, 252, 0)` placeholder — a reserved range, not a
colour. `KEN::Load_Player_Ship_Palette_` (ken.cpp:71) then loads
SHIPS.LBX entry `colour * 50 + 49` and calls `animate::Draw_Palette_`
(ken.cpp:106), which installs THAT entry's embedded 48-entry ramp over
192..239. The Fleets screen does it at flt1.cpp:561 for the first
icon's owner, and again through `FLT2::Fix_Palette_` (flt2.cpp:196)
whenever `_fix_palette` is set.

So slot 49 of every colour set — the 2x1 entry that looks like a
placeholder — is a PALETTE CARRIER and is the whole colouring
mechanism. Sets 8..14 (monsters and the rest) carry theirs at the
scattered entries `SPECIAL_PALETTE` names (ken.cpp:83-102). This is
decision 29 exactly as the original already had it: the colour is
resolved when the ship is drawn and is never in the artwork.

AND THE TWO COLOURS ARE NOT THE SAME ONE. The SPRITE is chosen by
`previous_owner` (ken.cpp:453) and the PALETTE by the screen's owner
(flt1.cpp:561, `_ship[...].owner`) — so a captured ship shows its old
owner's outline in its new owner's colours. That is the original's
behaviour and it is transcribed, not tidied.

WHAT IS NOT A PICTURE. Besides the palette carriers, the monster set
at 400..448 is largely 1x1 stubs. A 1x1 is not a ship, and blitting it
would put one stray pixel in a cell and read as a rendering fault.
Anything smaller than `MIN_PICTURE` is a HOLE and answers None, which
the screen handles exactly as it handles the files being absent.

SIZE IS NEVER READ OFF THE ARTWORK — except where the original reads
it. That rule is about deriving geometry from assets, and the cell is
`0x39` from `flt1.cpp:81`, not from any PNG. But the original itself
asks the sprite for its size (`animate::Get_Width_`, animate.cpp:79)
and centres it in that cell, because the sprites genuinely differ:
52x48 is the common one, 52x52, 55x55 and 51x49 all occur. So
`cell_offset` transcribes that centring rather than assuming a size.
"""
import json
import logging
import os

import pygame

from core import lbx

log = logging.getLogger("orionlayer")

#: Where `tools/fleet_art_extract.py` writes. Gitignored.
GAMEDATA = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "assets", "gamedata")

#: Refused rather than rendered almost right — decision 38's own
#: reason for carrying a version at all.
FORMAT_VERSION = 1

#: The grid cell, `0x39` at flt1.cpp:81 and :83. NOT measured off a
#: sprite.
NATIVE_CELL = 0x39

#: `ship_type + colour * 50`, `Do_Get_Ship_Picture_Seg` (ken.cpp:466).
SHIP_STRIDE = 50
#: consts.h:7. A ship whose owner is not a player is drawn in set 8.
MAX_PLAYERS = 8

#: Below this a decoded entry is not a ship — see the module
#: docstring. The real pictures are 48 px and up; the palette carriers
#: and stubs are 1x1 and 2x1, so anything in between would be a file
#: this loader has never seen and is refused rather than drawn.
MIN_PICTURE = 8

#: `colour * 50 + 49`, the entry whose EMBEDDED palette is the
#: player's ship ramp (ken.cpp:77).
SHIP_PALETTE_SLOT = 49

#: The same thing for the owners that are not players, which do not
#: follow the stride at all (ken.cpp:83-102). Keyed by the owner index
#: the original switches on.
SPECIAL_PALETTE = {8: 413, 9: 419, 10: 417, 11: 416, 12: 414,
                   13: 415, 14: 418}

#: How to get the files, said once, where the screen can show it.
HOW = "python tools/fleet_art_extract.py"


def cell_offset(width, height, cell=NATIVE_CELL):
    """Where a sprite of this size sits in the cell (flt1.cpp:81-86).

    The original computes `0x39 - width`, halves it with an arithmetic
    shift corrected for the sign — which is division TOWARD ZERO, not
    Python's floor — and draws at `x + half + 1, y + half + 2`. The
    `+1` and `+2` are the original's and are not a nudge of ours; a
    sprite WIDER than the cell gives a negative difference, which is
    why the rounding direction had to be transcribed rather than
    written as `// 2`.
    """
    return (_half(cell - width) + 1, _half(cell - height) + 2)


def _half(diff):
    return diff // 2 if diff >= 0 else -((-diff) // 2)


def magnified(surface, step):
    """`surface` at an integer magnification. **HD EXTENSION.**

    Decision 28 says a size is chosen by swapping the sprite the
    zoomtable names, never by scaling — and SHIPS.LBX holds exactly
    ONE size of each ship, so there is nothing to swap to. The
    deviation is therefore the smallest one available: an INTEGER
    factor with nearest-neighbour sampling, which reproduces every
    original pixel as a square block and invents no colour between
    them. A fractional or smoothed scale would blend palette indices
    into colours the game's palette does not contain, and decision 29
    is that a colour is resolved, never baked.
    """
    if step <= 1:
        return surface
    return pygame.transform.scale_by(surface, int(step))


class FleetArt:
    """The extracted artwork, or an honest account of its absence."""

    def __init__(self, folder=GAMEDATA):
        self.folder = folder
        self.reason = ""
        self._palette = None
        self._cache = {}
        self._ramps = {}
        self._manifest = self._load_manifest()

    # ── Availability ──────────────────────────────────────

    def _load_manifest(self):
        path = os.path.join(self.folder, "manifest.json")
        if not os.path.exists(path):
            self.reason = (f"The game's own Fleets artwork is not "
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
            self._palette = lbx.screen_palette(
                self._blob(os.path.join(self.folder, "palette.bin")))
        except (OSError, lbx.LbxError) as exc:
            self.reason = f"The screen palette is unusable ({exc}). Run: {HOW}"
            return None
        return manifest

    @property
    def available(self):
        return self._manifest is not None

    # ── The pictures ──────────────────────────────────────

    def ship(self, ship_type, colour, owner=None):
        """The ship picture in the owner's colours, or None.

        `ship_type + colour * 50`, `Do_Get_Ship_Picture_Seg`
        (ken.cpp:466). `colour` is the SPRITE set, resolved by the
        caller from `previous_owner` as the original does; `owner` is
        whose RAMP is installed over 192..239, which on this screen is
        the displayed stack's owner (flt1.cpp:561). They differ for a
        captured ship — see the module docstring.

        `owner` None means the sprite set's own colour, which is what
        an uncaptured ship gives and is the common case. None comes
        back for a slot the file has no picture in: the monster set is
        sparse, so that is a NORMAL answer and not a failure.
        """
        if not self.available:
            return None
        if not 0 <= ship_type < SHIP_STRIDE or not 0 <= colour <= MAX_PLAYERS:
            return None
        index = ship_type + colour * SHIP_STRIDE
        return self._sprite(os.path.join(self.folder, "ships",
                                         f"{index}.bin"),
                            minimum=MIN_PICTURE,
                            ramp=colour if owner is None else owner)

    def ship_ramp(self, owner):
        """The owner's ship colours for 192..239, or `{}`.

        `Load_Player_Ship_Palette_` (ken.cpp:71): entry
        `colour * 50 + 49` for a player, one of `SPECIAL_PALETTE`
        otherwise, installed by `animate::Draw_Palette_` (ken.cpp:106).
        `{}` leaves the screen palette's reserved green showing, which
        is what the range IS when nothing has filled it — an invented
        ramp here would be a colour the game does not have.
        """
        if not self.available or owner is None:
            return {}
        if owner in self._ramps:
            return self._ramps[owner]
        if 0 <= owner < MAX_PLAYERS:
            index = owner * SHIP_STRIDE + SHIP_PALETTE_SLOT
        else:
            index = SPECIAL_PALETTE.get(owner)
        ramp = {}
        if index is not None:
            try:
                blob = self._blob(os.path.join(self.folder, "ships",
                                               f"{index}.bin"))
                header = lbx.parse_header(blob, f"ships/{index}")
                if header.has_palette:
                    ramp = lbx.read_palette(blob, header.frame_count)
            except (OSError, lbx.LbxError, ValueError):
                ramp = {}
        self._ramps[owner] = ramp
        return ramp

    def star(self, colour, frame=0):
        """An inset star, FLEET.LBX 34 + colour (flt1.cpp:1439-1447)."""
        if not self.available or not 0 <= colour < 11:
            return None
        return self._sprite(os.path.join(self.folder, "fleet",
                                         f"star_{colour}.bin"), frame=frame)

    def radio(self, which, on):
        """A filter radio's face, FLEET.LBX 9 or 10, or None.

        `Add_Radio_Button_Field_` takes the animation and a POINTER to
        the status variable (flt1.cpp:1255-1256), and the frame drawn
        is that status — so the lit button is not a colour this project
        chooses, it is frame 1 of the original's own two-frame sprite.
        """
        if which not in ("support", "combat"):
            return None
        return self._sprite(os.path.join(self.folder, "fleet",
                                         f"radio_{which}.bin"),
                            frame=1 if on else 0)

    def selected_box(self):
        """FLEET.LBX 17, the box round a selected cell (flt1.cpp:103)."""
        return self._fleet("selected_box")

    def scanned_box(self):
        """FLEET.LBX 18, the scanned cell (flt1.cpp:1100-1104)."""
        return self._fleet("scanned_box")

    def background(self):
        """FLEET.LBX 0, the whole 640x480 screen (flt1.cpp:1130)."""
        return self._fleet("background")

    def plate(self, native_x, native_y, size=NATIVE_CELL):
        """One grid cell's plate, cut out of the background.

        The plate is not an entry of its own: the rails, the panel
        surrounds and the cells are PAINTED INTO FLEET.LBX 0
        (`_fleet_background_seg`, flt1.cpp:1130), so the only way to
        have the original's cell is to cut it out of the original's
        screen at the coordinates the original puts the cell at
        (`FLT2::Get_Fltscrn_Big_Icon_XY_`, via `fltgeom.native_cells`).
        That is decision 3's cutout rule applied to a background
        instead of a frame, and it is why nothing here invents a
        rectangle: the coordinates come from the geometry module that
        already had to agree with the engine.
        """
        source = self.background()
        if source is None:
            return None
        rect = pygame.Rect(native_x, native_y, size, size)
        if not source.get_rect().contains(rect):
            return None
        key = ("plate", native_x, native_y, size)
        if key not in self._cache:
            self._cache[key] = source.subsurface(rect).copy()
        return self._cache[key]

    def _fleet(self, name):
        if not self.available:
            return None
        return self._sprite(os.path.join(self.folder, "fleet", f"{name}.bin"))

    # ── Decoding ──────────────────────────────────────────

    def _sprite(self, path, frame=0, minimum=1, ramp=None):
        """One decoded frame as a surface, or None.

        None for every reason a file can fail to be a picture — absent,
        unreadable, a mode `core/lbx` does not decode, or too small to
        be anything but a placeholder. The caller cannot tell them
        apart and must not: all of them mean "draw the fallback".
        """
        key = (path, frame, ramp)
        if key in self._cache:
            return self._cache[key]
        surface = None
        try:
            blob = self._blob(path)
            header = lbx.parse_header(blob, os.path.basename(path))
            if header.width >= minimum and header.height >= minimum:
                surface = self._surface(blob, header, frame, ramp)
        except (OSError, lbx.LbxError, ValueError):
            surface = None
        self._cache[key] = surface
        return surface

    def _surface(self, blob, header, frame, ramp=None):
        pixels = lbx.decode_frame(blob, header, frame)
        if pixels is None:
            return None
        palette = dict(self._palette)
        if ramp is not None:
            # The owner's ship ramp over the screen palette's reserved
            # 192..239, exactly the order the original installs them in
            # (flt1.cpp:557 then :561).
            palette.update(self.ship_ramp(ramp))
        if header.has_palette:
            # The sprite's own palette wins over the screen's, for the
            # range it covers — `Set_Animation_Palette_` (animate.cpp).
            palette.update(lbx.read_palette(blob, header.frame_count))
        rgba = lbx.rgba_bytes(pixels, palette)
        return pygame.image.frombuffer(
            rgba, (header.width, header.height), "RGBA").convert_alpha()

    @staticmethod
    def _blob(path):
        with open(path, "rb") as fh:
            return fh.read()


_loaded = None


def load(folder=GAMEDATA):
    """The one instance. Decoding is lazy; this only reads the manifest."""
    global _loaded
    if _loaded is None or _loaded.folder != folder:
        _loaded = FleetArt(folder)
        log.info("fleets artwork: %s",
                 "loaded from " + folder if _loaded.available
                 else _loaded.reason)
    return _loaded
