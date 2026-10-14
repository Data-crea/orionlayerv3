"""The acting unit's status picture — work order 256 (Data, 14 Oct 2026).

TRANSCRIPTION `status_picture`: the left box of the original's panel as
`Draw_Main_Combat_Screen_` builds it for the acting unit
(cmbtdrw1.cpp:522-524): `Draw_Ship_Status_(14, 376)` — the black fill and
the star picture COMBAT.LBX 0x2D, then the unit on a 98 x 98 bitmap with
its shield (:2057-2359) — `Draw_Grey_Damage_Bars_(14, 376)` (:948-1139)
and `Draw_Crew_Level_Stars_(15, 379)` (:1222-1245). Line numbers are the
1.60 source's (`version_check.find_source_tree`).

THE SHIELD IS NOT A STORED PICTURE. The original grows it out of the
unit's own outline: `Outline_Bitmap_` puts one pixel of a colour round
everything drawn (`Outline_Bitmap_Pixels_`, shear.cpp:132-214: a
horizontal pass, then a vertical one, each colouring an empty pixel — 0
or the colour itself — beside a drawn one). Two outlines of colours 1
and 2 (removed at the end: the gap round the hull), then one ring per
step of the green ramp 0x50-0x57, how many by `shield_arc_max`
(`(max + 19) / 10`, at most 10, five cases, :2161-2327). For each of the four arcs
weaker than the case's top, the arc's part is cut out with COMBAT.LBX
0x10 + arc mask (`(arc - facing / 4 + 4) % 4 + facing % 4 * 4`) and its
outer rings are turned back to colour 1 by the arc's strength; the gaps
between the arcs are cut with COMBAT.LBX 0xC-0xF (`facing % 4`), and the
unit is drawn again over it all. Every step is copied as the engine does
it, the masks' 85 x 80 window included (`Mask_Out_Bitmap_With_Bitmap_`,
bitmap.cpp:214-296: the pixels right of and under the mask are not
touched), and a colour outlined twice adds nothing the second time
(case 8-9's 0x53 and 0x54), as in the engine.

The bars (`Draw_Grey_Damage_Bars_`): COMBAT.LBX 0x2B over the box and
0x2C under it carry the full bars; the damage is COMBAT.LBX 0x57 (grey)
drawn over them through a window — the armour from both ends of the top
bar, the structure from the left and the internal systems from the right
of the bottom bar; a monster (builder 10 and up) has 0x59 and 0x58 and
its structure and internals from both ends. Armour's whole is
`_hull_data[size].armor_hp` with the armour's ships bonus, three times
with Heavy Armor (`core.monsterhull.armour`, held by its checker); a
satellite's hull is `size_class + 4` (`Combat_Satellite_Hull_Class_`,
combinit.h:26-29 — `_satellite_size_class_plus_one` is 0 and no line
of the engine sets it, :16).

HD EXTENSION `status_painted`: a painted unit (`cbart.hd_factor` > 1) is
drawn at the box's scale over the rings, which keep the stored drawing's
outline; the box is drawn as large as the panel's room allows.
TRANSCRIPTION `status_words` (work order 258): the officer's mark and
"Immobile" are the game's own words in its language — KENTEXT 86 ("(L)",
German "(A)") and 0x47 ("Immobile", "Unbeweglich"), `core.kentext`; in
HD's font, as the rest of the panel (`hud_panel`). Without the extracted
file, OrionLayer's words.
OMISSION `status_planet`: the planet's box (its picture and its defences'
names, :2068-2129, and its bars, :958-994) is not this — the panel keeps
HD's rings for the planet.
UNVERIFIED `status_internals`: a ship's internals bar with its internal
systems hit was not seen live (work order 258's runs never reached them);
a monster's bars (builder 10 and up, :1087-1138), undamaged and damaged,
were held against the engine's hover box in work order 258, 0 differing.
"""
import numpy as np
import pygame

from core import lang
from core import monsterhull
from . import cbart

#: The engine's bitmaps for this (`Get_Bitmap_Size_(0x62, 0x62)`,
#: combinit.cpp:709-711).
CANVAS = 0x62
#: Where `Draw_Ship_Status_` is called for the acting unit (cmbtdrw1.cpp:522).
AT = (14, 376)
#: The box in the original's pixels: 0x2B at (13, 375) to 0x2C's right
#: and bottom edge (103, 468).
BOX = pygame.Rect(13, 375, 91, 94)

STARS_BG, BAR_TOP, BARS, GREY, MONSTER_BOTTOM, MONSTER_TOP, CREW_STAR = (
    0x2D, 0x2B, 0x2C, 0x57, 0x58, 0x59, 0x2A)
#: `shield_mask_bitmap[16]` = COMBAT.LBX 0x10.. and `shield_div_bitmap[4]`
#: = 0xE, 0xF, 0xC, 0xD (combinit.cpp:714-723).
MASK_FIRST = 0x10
DIVIDERS = (0xE, 0xF, 0xC, 0xD)

#: `switch (shield_val - 1)` (cmbtdrw1.cpp:2161-2327), case by case: the
#: colours outlined after the two of 1 and 2, and for a weaker arc the
#: (strength below which, colour turned back to 1) steps — the first
#: step's strength is the case's own gate for the arc.
SHIELD_CASES = (
    ((1, 2, 0x51, 0x52), ((11, 0x52), (1, 0x51))),
    ((1, 2, 0x50, 0x52, 0x54, 0x56),
     ((31, 0x56), (22, 0x54), (12, 0x52), (1, 0x50))),
    ((1, 2, 0x50, 0x51, 0x53, 0x54, 0x55, 0x56),
     ((51, 0x56), (42, 0x55), (32, 0x54), (22, 0x53), (12, 0x51),
      (1, 0x50))),
    ((0x50, 0x51, 0x52, 0x53, 0x54, 0x55, 0x56, 0x57),
     ((71, 0x57), (62, 0x56), (52, 0x55), (42, 0x54), (32, 0x53),
      (22, 0x52), (12, 0x51), (1, 0x50))),
    ((0x50, 0x51, 0x52, 0x53, 0x53, 0x54, 0x54, 0x55, 0x56, 0x57),
     ((91, 0x57), (82, 0x56), (72, 0x55), (62, 0x54), (42, 0x53),
      (22, 0x52), (12, 0x51), (1, 0x50))),
)

MAX_PLAYERS = 8
#: `Draw_Crew_Level_Stars_`: a star per crew level above green, 11 apart.
STAR_STEP = 11

#: HD EXTENSION `shield_from_painted` (work order 257, variant B; the
#: default since work order 258, Data's decision): the rings round a
#: painted unit are grown from the painted picture's own outline, as it is
#: turned and mirrored for the facing, by the same steps at the picture's
#: k (`shield_canvas(k)`, `outline_thick`, the masks k x k per pixel, their
#: steps kept). DEVIATION `painted_rings`: original = the rings follow the
#: stored drawing's outline; HD = round a painted unit they follow the
#: painting. A unit without a painted picture keeps the original's rings,
#: pixel for pixel. ORIONLAYER_SHIELD_OUTLINE=original switches back to
#: variant A for comparisons.
OUTLINE_ENV = "ORIONLAYER_SHIELD_OUTLINE"
#: How many variant-B ring pictures are kept (one is 98 k square: 2.4 MB
#: at k = 8).
PAINTED_KEPT = 16


#: The shield's colours a mod may give (work order 258, Data: "the green
#: stays generated, only its colours become replaceable"): HD EXTENSION
#: `shield_colours`. The project's file is empty — the game's own colours,
#: the 256 pixel match; the player's mod folder replaces it.
SHIELD_COLOURS = "screens/combat/assets/shield_colours.json"
RING_FIRST, RING_LAST = 0x50, 0x57
_ring_colours = {}


def ring_colours():
    """{index: (r, g, b)} for the ring colours a mod gives, read once."""
    if "v" in _ring_colours:
        return _ring_colours["v"]
    import json
    import logging
    from core import resources
    got = {}
    path = resources.res.resolve(SHIELD_COLOURS)
    try:
        doc = json.load(open(path, encoding="utf-8")) if path else {}
        for k, v in (doc.get("colours") or {}).items():
            i = int(k, 0)
            if isinstance(v, str):
                v = v.lstrip("#")
                rgb = tuple(int(v[j:j + 2], 16) for j in (0, 2, 4))
            else:
                rgb = tuple(int(c) for c in v)
            if not RING_FIRST <= i <= RING_LAST or len(rgb) != 3 or \
                    not all(0 <= c <= 255 for c in rgb):
                raise ValueError(f"{k}: {v}")
            got[i] = rgb
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        logging.getLogger("combat").warning(
            "mod: %s cannot be read (%s) — the game's shield colours are "
            "used", SHIELD_COLOURS, exc)
        got = {}
    _ring_colours["v"] = got
    return got


def palette(art):
    """The battle palette with a mod's ring colours (`ring_colours`)."""
    pal = art.palette_with()
    pal.update(ring_colours())
    return pal


def painted_outline():
    """Whether variant B draws (the default); "original" in the
    environment switches to variant A."""
    import os
    return os.environ.get(OUTLINE_ENV, "").strip().lower() != "original"


def _cdiv(a, b):
    """C's division, toward zero."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b > 0) else -q


def outline(canvas, colour):
    """`Outline_Bitmap_Pixels_` (shear.cpp:132-214) in place. Each pass reads
    a pixel before anything writes it, so the passes are taken whole."""
    for grid in (canvas, canvas.T):
        empty = (grid == 0) | (grid == colour)
        solid = ~empty
        after = np.zeros_like(empty)          # empty, its left one drawn
        after[:, 1:] = empty[:, 1:] & solid[:, :-1]
        before = np.zeros_like(empty)         # empty, its right one drawn
        before[:, :-1] = empty[:, :-1] & solid[:, 1:]
        grid[after | before] = colour


def _place(canvas, ship, x, y):
    """`Add_Picture_To_Bitmap_` (bitmap.cpp:770): every non-zero pixel,
    clipped."""
    h, w = ship.shape
    x1, y1 = min(canvas.shape[1], x + w), min(canvas.shape[0], y + h)
    if x1 <= x or y1 <= y:
        return
    part = ship[:y1 - y, :x1 - x]
    view = canvas[y:y1, x:x1]
    view[part != 0] = part[part != 0]


def ship_x(facing):
    """The unit's x on the bitmap: 14 for facings 5-12, else 16
    (cmbtdrw1.cpp:2148, :2338 — C's division groups facing 0 with 1-4)."""
    q = max(0, _cdiv(int(facing) - 1, 4))
    return 14 if q in (1, 2) else 16


def outline_thick(canvas, colour, k):
    """`outline` k pixels thick: every empty pixel (0 or the colour) within
    k steps left, right, up or down of a drawn one — the original's one
    pixel at k times the drawing (work order 257, variant B). k = 1 is
    `outline` itself, pixel for pixel."""
    solid = (canvas != 0) & (canvas != colour)
    grown = solid.copy()
    for _ in range(k):
        step = grown.copy()
        step[1:, :] |= grown[:-1, :]
        step[:-1, :] |= grown[1:, :]
        step[:, 1:] |= grown[:, :-1]
        step[:, :-1] |= grown[:, 1:]
        grown = step
    canvas[grown & ~solid] = colour


def _scaled_mask(mask, k):
    """A COMBAT.LBX mask at k times its pixels, each pixel a k x k block
    (variant B's "masks scaled to the painted size")."""
    return mask if k == 1 else np.kron(mask, np.ones((k, k), np.uint8))


def shield_canvas(ship, unit, masks, dividers, k=1):
    """The 98 x 98 bitmap `Draw_Ship_Status_` draws, as palette indices,
    and the bitmap of where the unit itself is on it. With `k` > 1 (work
    order 257, variant B) the same steps on a bitmap k times the size:
    `ship` is then the painted picture's outline, each ring k pixels
    thick, the masks and the unit's place k times theirs."""
    canvas = np.zeros((CANVAS * k, CANVAS * k), np.uint8)
    facing = int(unit["facing_dir"])
    x = ship_x(facing) * k
    _place(canvas, ship, x, 11 * k)
    ring = outline if k == 1 else (lambda cv, c: outline_thick(cv, c, k))
    if int(unit["shield_type"]) > 0 and int(unit["shield_current_hits"]) > 0:
        ring(canvas, 1)
        ring(canvas, 2)
        val = min(10, _cdiv(int(unit["shield_arc_max"]) + 19, 10))
        if 0 <= val - 1 <= 9:
            colours, steps = SHIELD_CASES[(val - 1) // 2]
            for c in colours:
                ring(canvas, c)
            quadrant, turn = facing // 4, facing % 4
            for arc in range(4):
                strength = int(unit["shield_arc_current"][arc])
                if strength >= steps[0][0]:
                    continue
                part = canvas.copy()
                mask = _scaled_mask(masks[(arc - quadrant + 4) % 4 + turn * 4],
                                    k)
                h, w = mask.shape
                part[:h, :w][mask == 0] = 0
                for below, c in steps:
                    if strength < below:
                        part[part == c] = 1
                canvas[part != 0] = part[part != 0]
        div = _scaled_mask(dividers[facing % 4], k)
        h, w = div.shape
        canvas[:h, :w][div != 0] = 0
        _place(canvas, ship, x, 11 * k)
    hull = np.zeros_like(canvas, dtype=bool)
    probe = np.zeros_like(canvas)
    _place(probe, np.where(ship != 0, 3, 0).astype(np.uint8), x, 11 * k)
    hull[probe != 0] = True
    canvas[(canvas == 1) | (canvas == 2)] = 0
    return canvas, hull


def satellite(unit):
    """`Is_Combat_Satellite_` (combinit.h:19-24) for a unit other than the
    planet: no ship record, no drive — and, in orion2re v2 (the engine
    OrionLayer runs), not a generated Antaran (builder 8, no officer)."""
    antaran = int(unit["ship_idx"]) == -1 and \
        int(unit["previous_owner"]) == MAX_PLAYERS and \
        int(unit["officer_idx"]) == -1
    return int(unit["ship_idx"]) == -1 and int(unit["ftl_type"]) == 0 and \
        not antaran


class _View:
    """What `monsterhull.armour` reads, from a wire unit. The bars ask
    `Does_Combat_Ship_Have_Special_` (combinit.cpp:483-493): a system that
    is DAMAGED counts as absent, so a damaged Heavy Armor no longer triples
    the whole — and with the remaining armour then above it, the original
    greys nothing (work order 258, seen live on a hovered Def Doom Star)."""

    def __init__(self, unit, size):
        self.size = size
        self.armor_type = int(unit["armor_type"])
        damaged = unit.get("special_device_damage_flags") or [0] * 5
        self.special_device_flags = [int(f) & ~int(d) & 0xFF for f, d in
                                     zip(unit["special_device_flags"],
                                         damaged)]


def armour_whole(unit):
    size = int(unit["size_class"])
    if satellite(unit):
        size += 4
    return monsterhull.armour(_View(unit, size))


def internal_space(unit):
    """(`Max_Total_Internal_Space_`, `Total_Internal_Space_`),
    cmbtfir2.cpp:517-534 and :961-978."""
    whole = int(unit["drive_max_hits"]) // 2 + int(unit["computer_max_hits"]) \
        + sum(int(v) for v in unit["weapon_total_hits"]) \
        + sum(int(v) for v in unit["special_device_hits"]) \
        + int(unit["shield_max_hits"])
    drive = int(unit["drive_current_hits"])
    left = (1 if drive == 1 else drive // 2) + \
        int(unit["computer_current_hits"]) + \
        sum(int(v) for v in unit["weapon_hits"]) + \
        sum(int(v) for v in unit["special_hits"]) + \
        int(unit["shield_current_hits"])
    return whole, left


def grey_windows(unit):
    """The grey 0x57's (row, first column, last column) cuts, in the
    original's columns, and which bar pictures lie under them:
    `Draw_Grey_Damage_Bars_` for a unit other than the planet."""
    x = AT[0]
    top, bottom = AT[1] + 0x4F, AT[1] + 0x55
    cuts = []

    def both(row, length):
        cuts.append((row, x + 1, x + length + 1))
        cuts.append((row, x - length + 0x58, x + 0x58))

    whole_space, left_space = internal_space(unit)
    space = whole_space - left_space
    structure = int(unit["structure_damage"])
    if int(unit["previous_owner"]) <= 9:
        whole = armour_whole(unit)
        lost = (whole or 0) - int(unit["armor_remaining"])
        if whole and lost:
            both(top, _cdiv(_cdiv(lost * 88, whole), 2))
        if structure > 0 and int(unit["structure_max"]) > 0:
            n = max(2, _cdiv(structure * 44, int(unit["structure_max"])))
            cuts.append((bottom, x + 1, x + n + 1))
        if space and whole_space:
            n = max(2, _cdiv(space * 44, whole_space))
            cuts.append((bottom, x - n + 0x58, x + 0x58))
        return (BARS, None), cuts
    if structure > 0 and int(unit["structure_max"]) > 0:
        both(bottom, _cdiv(_cdiv(structure * 88, int(unit["structure_max"])),
                           2))
    if space and whole_space:
        both(top, _cdiv(_cdiv(space * 88, whole_space), 2))
    return (BARS, (MONSTER_TOP, MONSTER_BOTTOM)), cuts


class StatusPicture:
    """The box, built in the original's pixels and kept until what it
    shows changes."""

    def __init__(self):
        self._key = None
        self._box = None
        self._scaled = {}
        #: (indices, drawn, the unit's own pixels) of the last box built,
        #: in the original's pixels — what a live check holds against the
        #: engine's frame
        self.indices = None
        self._masks_now = None
        self._painted = {}        # variant B's rings, `painted_rings`

    def _combat(self, art, entry):
        """COMBAT.LBX `entry` as indices (the masks, bars and stars)."""
        return self._decode(art.blob("combat", entry), 0)

    def _indices(self, art, entry, frame):
        return self._decode(art.blob(*entry), frame)

    @staticmethod
    def _decode(b, frame):
        if b is None:
            return None
        from core import lbx
        try:
            h = lbx.parse_header(b)
            px = lbx.decode_composed(b, h, frame)
        except (lbx.LbxError, ValueError):
            return None
        if px is None:
            return None
        return np.frombuffer(bytes(px), np.uint8).reshape(h.height, h.width)

    def _masks(self, art):
        masks = [self._combat(art, MASK_FIRST + i)
                 for i in range(16)]
        dividers = [self._combat(art, e) for e in DIVIDERS]
        if any(m is None for m in masks + dividers):
            return None
        return masks, dividers

    def stored(self, art, colour, unit, monster):
        """The unit's stored drawing at its facing, glow frame 0, as
        indices (`Draw_Ship_To_Bitmap_`, cmbtdrw1.cpp:1978-2050)."""
        name, entry = art._unit_entry(colour, unit["picture_num"], monster)
        facing, mirror, flip = cbart.stored_facing(unit["facing_dir"])
        px = self._indices(art, (name, entry), 4 * facing)
        if px is None:
            return None
        if mirror:
            px = px[:, ::-1]
        if flip:
            px = px[::-1, :]
        return np.ascontiguousarray(px)

    def build(self, art, colour, unit, monster):
        """The box as an RGBA surface in the original's pixels, and the
        unit's place on it, or None when a picture is missing."""
        key = (colour, monster, int(unit["picture_num"]),
               int(unit["facing_dir"]), int(unit["shield_type"]),
               int(unit["shield_current_hits"]), int(unit["shield_arc_max"]),
               tuple(int(v) for v in unit["shield_arc_current"]),
               tuple(c for c in grey_windows(unit)[1]),
               int(unit["crew_quality"]))
        if key == self._key:
            return self._box
        self._key, self._box, self._scaled = key, None, {}
        ship, masks = self.stored(art, colour, unit, monster), \
            self._masks(art)
        if ship is None or masks is None:
            return None
        canvas, hull = shield_canvas(ship, unit, *masks)
        idx = np.zeros((BOX.h, BOX.w), np.uint8)
        drawn = np.zeros((BOX.h, BOX.w), bool)

        layers = [(idx, drawn)]

        def put(px, x, y, keep_zero=False):
            for target, mark in layers:
                _put(target, mark, px, x, y, keep_zero)

        def _put(idx, drawn, px, x, y, keep_zero):
            if px is None:
                return
            x0, y0 = x - BOX.x, y - BOX.y
            h, w = px.shape
            sx0, sy0 = max(0, -x0), max(0, -y0)
            x1, y1 = min(BOX.w, x0 + w), min(BOX.h, y0 + h)
            if x1 <= max(0, x0) or y1 <= max(0, y0):
                return
            part = px[sy0:sy0 + y1 - max(0, y0), sx0:sx0 + x1 - max(0, x0)]
            on = np.ones_like(part, bool) if keep_zero else part != 0
            view = idx[max(0, y0):y1, max(0, x0):x1]
            dview = drawn[max(0, y0):y1, max(0, x0):x1]
            view[on] = part[on]
            dview[on] = True

        # the fill (0x0F, 0x17B)-(0x66, 0x1C5) in colour 0, then the stars
        put(np.zeros((0x1C5 - 0x17B + 1, 0x66 - 0x0F + 1), np.uint8),
            0x0F, 0x17B, keep_zero=True)
        put(self._combat(art, STARS_BG), 0x0F, 0x17B)
        # variant B (work order 257) draws its own rings: the box without
        # them is the same steps less this one
        bare_idx, bare_drawn = idx.copy(), drawn.copy()
        rings = np.where(hull, 0, canvas).astype(np.uint8)
        put(rings, *AT)
        layers.append((bare_idx, bare_drawn))
        frames, cuts = grey_windows(unit)
        put(self._combat(art, BAR_TOP), AT[0] - 1, AT[1] - 1)
        put(self._combat(art, frames[0]), AT[0], AT[1] + 0x4E)
        if frames[1]:
            put(self._combat(art, frames[1][0]), AT[0] + 1,
                AT[1] + 0x4F)
            put(self._combat(art, frames[1][1]), AT[0] + 1,
                AT[1] + 0x55)
        grey = self._combat(art, GREY)
        for row, first, last in cuts:
            if grey is None:
                break
            cut = grey[:, max(0, first - AT[0] - 1):max(0, last - AT[0])]
            put(cut, max(first, AT[0] + 1), row)
        # the crew stars come last in the original (over the bars); HD
        # draws them over its own picture of the unit, the indices keep
        # them for a comparison with the engine's frame
        star_px = self._combat(art, CREW_STAR)
        quality = int(unit["crew_quality"])
        stars = [(15 + STAR_STEP * k - BOX.x, 379 - BOX.y)
                 for k in range(quality)] if quality > 0 else []
        hull_box = np.zeros_like(drawn)
        hx, hy = AT[0] - BOX.x, AT[1] - BOX.y
        hull_box[hy:, hx:] = hull[:BOX.h - hy, :BOX.w - hx]
        with_stars = idx.copy(), drawn.copy()
        for x, y in stars:
            if star_px is None:
                break
            h, w = star_px.shape
            part = star_px[:BOX.h - y, :BOX.w - x]
            on = part != 0
            with_stars[0][y:y + h, x:x + w][on] = part[on]
            with_stars[1][y:y + h, x:x + w][on] = True
        self.indices = with_stars + (hull_box,)
        pal = palette(art)
        box, bare = (_surface(i, d, pal) for i, d in ((idx, drawn),
                                                       (bare_idx, bare_drawn)))
        star = art.surface("combat", CREW_STAR)
        self._masks_now = masks
        self._box = (box, (AT[0] + ship_x(unit["facing_dir"]) - BOX.x,
                           AT[1] + 11 - BOX.y), ship.shape, star, stars, bare)
        return self._box

    def painted_rings(self, art, colour, unit, monster, picture):
        """Variant B's rings (work order 257): `shield_canvas` at the
        painted picture's k on its outline, as an RGBA surface 98 k wide,
        kept per ship, facing, shield and picture size (the detail
        setting), with that key; None for a drawing that is not painted."""
        k = int(round(cbart.hd_factor(picture)))
        if k <= 1 or self._masks_now is None:
            return None
        key = (colour, monster, int(unit["picture_num"]),
               int(unit["facing_dir"]), picture.get_size(),
               int(unit["shield_type"]), int(unit["shield_current_hits"]),
               int(unit["shield_arc_max"]),
               tuple(int(v) for v in unit["shield_arc_current"]))
        got = self._painted.get(key)
        if got is None:
            sil = silhouette(picture)
            canvas, hull = shield_canvas(sil, unit, *self._masks_now, k)
            rings = np.where(hull, 0, canvas).astype(np.uint8)
            got = _surface(rings, rings != 0, palette(art))
            if len(self._painted) >= PAINTED_KEPT:
                self._painted.clear()
            self._painted[key] = got
        return key, got


def silhouette(picture, threshold=128):
    """A painted picture's outline as variant B reads it: its pixels at
    alpha `threshold` and up, as a drawing (0xFE, a colour no ring uses)."""
    alpha = pygame.surfarray.array_alpha(picture).T
    return np.where(alpha >= threshold, 0xFE, 0).astype(np.uint8)


def _surface(idx, drawn, pal):
    rgba = np.zeros(idx.shape + (4,), np.uint8)
    for i in np.unique(idx[drawn]):
        rgb = pal.get(int(i), (int(i),) * 3)
        sel = drawn & (idx == i)
        rgba[sel, :3] = rgb[:3]
        rgba[sel, 3] = 255
    return pygame.image.frombuffer(rgba.tobytes(), idx.shape[::-1],
                                   "RGBA").copy()


_STARS = {}


def stars_tile(art, k):
    """The status box's star picture (COMBAT.LBX 0x2D, 88 x 89) at the
    box's scale `k`, opaque, for the panel's other windows (work order 258,
    Data: "the same blue background as the box on the left"); None without
    the game's pictures."""
    if art is None:
        return None
    key = (id(art), round(k, 3))
    if key in _STARS and _STARS[key][0] is art:
        return _STARS[key][1]
    px = StatusPicture._decode(art.blob("combat", STARS_BG), 0)
    if px is None:
        return None
    img = _surface(px, np.ones_like(px, bool), palette(art))
    img = cbart.display_format(pygame.transform.scale(
        img, (max(1, round(img.get_width() * k)),
              max(1, round(img.get_height() * k)))))
    _STARS.clear()
    _STARS[key] = (art, img)
    return img


def tile(surface, rect, img):
    """`img` repeated over `rect`, clipped to it."""
    clip = surface.get_clip()
    surface.set_clip(rect.clip(clip) if clip else rect)
    w, h = img.get_size()
    for y in range(rect.y, rect.bottom, h):
        for x in range(rect.x, rect.right, w):
            surface.blit(img, (x, y))
    surface.set_clip(clip)


def word(ken, what, fallback):
    """The game's own word over the box in the game's language (KENTEXT,
    `core.kentext.PANEL_MESSAGES`, work order 258), else OrionLayer's."""
    got = ken.panel_word(what) if ken is not None and \
        hasattr(ken, "panel_word") else None
    return got or lang.tr(fallback)


def fit(rect):
    """The box's scale in `rect`: as large as fits (a whole multiple
    would leave a quarter of the room empty at 3840 x 2160)."""
    return max(0.5, min(rect.w / BOX.w, rect.h / BOX.h))


def draw(surface, rect, status, art, colour, unit, monster, picture, style,
         scale, ken=None):
    """The box centred in `rect`, as large as fits. False when it could
    not be built (the caller then draws HD's rings)."""
    built = status.build(art, colour, unit, monster)
    if built is None:
        return False
    box, (sx, sy), _shape, star, stars, bare = built
    got_b = status.painted_rings(art, colour, unit, monster, picture) \
        if picture is not None and painted_outline() else None
    rings_key, rings_b = got_b or (None, None)
    if rings_b is not None:
        box = bare
    k = fit(rect)
    out = pygame.Rect(0, 0, round(BOX.w * k), round(BOX.h * k))
    out.center = rect.center

    def at(x, y):
        """The original's (x, y) in the box, in the window."""
        return out.x + round(x * k), out.y + round(y * k)

    big = status._scaled.get(("box", rings_b is not None, out.size))
    if big is None:
        big = status._scaled[("box", rings_b is not None, out.size)] = \
            cbart.display_format(pygame.transform.scale(box, out.size))
    surface.blit(big, out)
    clip = surface.get_clip()
    x0, y0 = at(AT[0] - BOX.x, AT[1] - BOX.y)
    canvas = pygame.Rect(x0, y0, round(CANVAS * k), round(CANVAS * k))
    surface.set_clip(canvas.clip(out).clip(clip) if clip else canvas.clip(out))
    if rings_b is not None:
        key = ("rings", rings_key, canvas.size)
        img = status._scaled.get(key)
        if img is None:
            img = status._scaled[key] = cbart.display_format(
                cbart.smooth(rings_b, canvas.size))
        surface.blit(img, canvas)
    if picture is not None:
        f = cbart.hd_factor(picture)
        size = (max(1, round(picture.get_width() * k / f)),
                max(1, round(picture.get_height() * k / f)))
        # kept with the box: the picture is scaled once per size, not
        # every frame (work order 257: "nothing per frame")
        # the picture itself is kept beside it, so a new picture with a
        # recycled id() is never served the old one's (fundament P828)
        held = status._scaled.get(("ship", size))
        if held is None or held[0] is not picture:
            how = cbart.smooth if f > 1 and size[0] < picture.get_width() \
                else pygame.transform.scale
            held = status._scaled[("ship", size)] = (
                picture, cbart.display_format(how(picture, size)))
        surface.blit(held[1], at(sx, sy))
    surface.set_clip(clip)
    if star is not None and stars:
        s = pygame.transform.scale(star, (round(star.get_width() * k),
                                          round(star.get_height() * k)))
        for x, y in stars:
            surface.blit(s, at(x, y))
    from core.hud import text as hudtext
    small = max(9, int(16 * scale))
    if int(unit["officer_idx"]) > -1:
        img = style.render_text(word(ken, "officer", "Officer"), small,
                                hudtext.colour("value")[:3])
        surface.blit(img, img.get_rect(topright=at(AT[0] + 87 - BOX.x,
                                                   AT[1] + 2 - BOX.y)))
    if int(unit["current_speed"]) <= 0:
        img = style.render_text(word(ken, "immobile", "Immobile"), small,
                                (230, 60, 50))
        surface.blit(img, img.get_rect(center=at(AT[0] + 45 - BOX.x,
                                                 AT[1] + 70 - BOX.y)))
    return True
