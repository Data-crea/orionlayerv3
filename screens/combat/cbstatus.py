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
DEVIATION `status_words`: the officer's mark (KENTEXT 86, "(L)" in the
English game) and "Immobile" (KENTEXT 0x47) are OrionLayer's words, as the
rest of the panel (`hud_panel`).
OMISSION `status_planet`: the planet's box (its picture and its defences'
names, :2068-2129, and its bars, :958-994) is not this — the panel keeps
HD's rings for the planet.
UNVERIFIED `status_monster`: a monster's bars (builder 10 and up,
:1087-1138) are transcribed from the source; no battle with a monster was
held against the engine's frame in work order 256, nor a unit whose
internal systems were hit (the internals bar's damage).
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
    x1, y1 = min(CANVAS, x + w), min(CANVAS, y + h)
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


def shield_canvas(ship, unit, masks, dividers):
    """The 98 x 98 bitmap `Draw_Ship_Status_` draws, as palette indices,
    and the bitmap of where the unit itself is on it."""
    canvas = np.zeros((CANVAS, CANVAS), np.uint8)
    facing = int(unit["facing_dir"])
    x = ship_x(facing)
    _place(canvas, ship, x, 11)
    if int(unit["shield_type"]) > 0 and int(unit["shield_current_hits"]) > 0:
        outline(canvas, 1)
        outline(canvas, 2)
        val = min(10, _cdiv(int(unit["shield_arc_max"]) + 19, 10))
        if 0 <= val - 1 <= 9:
            colours, steps = SHIELD_CASES[(val - 1) // 2]
            for c in colours:
                outline(canvas, c)
            quadrant, turn = facing // 4, facing % 4
            for arc in range(4):
                strength = int(unit["shield_arc_current"][arc])
                if strength >= steps[0][0]:
                    continue
                part = canvas.copy()
                mask = masks[(arc - quadrant + 4) % 4 + turn * 4]
                h, w = mask.shape
                part[:h, :w][mask == 0] = 0
                for below, c in steps:
                    if strength < below:
                        part[part == c] = 1
                canvas[part != 0] = part[part != 0]
        div = dividers[facing % 4]
        h, w = div.shape
        canvas[:h, :w][div != 0] = 0
        _place(canvas, ship, x, 11)
    hull = np.zeros_like(canvas, dtype=bool)
    probe = np.zeros_like(canvas)
    _place(probe, np.where(ship != 0, 3, 0).astype(np.uint8), x, 11)
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
    """What `monsterhull.armour` reads, from a wire unit."""

    def __init__(self, unit, size):
        self.size = size
        self.armor_type = int(unit["armor_type"])
        self.special_device_flags = unit["special_device_flags"]


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

        def put(px, x, y, keep_zero=False):
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
        rings = np.where(hull, 0, canvas).astype(np.uint8)
        put(rings, *AT)
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
        pal = art.palette_with()
        rgba = np.zeros((BOX.h, BOX.w, 4), np.uint8)
        for i in np.unique(idx[drawn]):
            rgb = pal.get(int(i), (int(i),) * 3)
            sel = drawn & (idx == i)
            rgba[sel, :3] = rgb[:3]
            rgba[sel, 3] = 255
        box = pygame.image.frombuffer(rgba.tobytes(), (BOX.w, BOX.h),
                                      "RGBA").copy()
        star = art.surface("combat", CREW_STAR)
        self._box = (box, (AT[0] + ship_x(unit["facing_dir"]) - BOX.x,
                           AT[1] + 11 - BOX.y), ship.shape, star, stars)
        return self._box


def fit(rect):
    """The box's scale in `rect`: as large as fits (a whole multiple
    would leave a quarter of the room empty at 3840 x 2160)."""
    return max(0.5, min(rect.w / BOX.w, rect.h / BOX.h))


def draw(surface, rect, status, art, colour, unit, monster, picture, style,
         scale):
    """The box centred in `rect`, as large as fits. False when it could
    not be built (the caller then draws HD's rings)."""
    built = status.build(art, colour, unit, monster)
    if built is None:
        return False
    box, (sx, sy), _shape, star, stars = built
    k = fit(rect)
    out = pygame.Rect(0, 0, round(BOX.w * k), round(BOX.h * k))
    out.center = rect.center

    def at(x, y):
        """The original's (x, y) in the box, in the window."""
        return out.x + round(x * k), out.y + round(y * k)

    big = status._scaled.get(out.size)
    if big is None:
        big = status._scaled[out.size] = pygame.transform.scale(box, out.size)
    surface.blit(big, out)
    clip = surface.get_clip()
    x0, y0 = at(AT[0] - BOX.x, AT[1] - BOX.y)
    canvas = pygame.Rect(x0, y0, round(CANVAS * k), round(CANVAS * k))
    surface.set_clip(canvas.clip(out).clip(clip) if clip else canvas.clip(out))
    if picture is not None:
        f = cbart.hd_factor(picture)
        size = (max(1, round(picture.get_width() * k / f)),
                max(1, round(picture.get_height() * k / f)))
        img = (cbart.smooth if f > 1 and size[0] < picture.get_width()
               else pygame.transform.scale)(picture, size)
        surface.blit(img, at(sx, sy))
    surface.set_clip(clip)
    if star is not None and stars:
        s = pygame.transform.scale(star, (round(star.get_width() * k),
                                          round(star.get_height() * k)))
        for x, y in stars:
            surface.blit(s, at(x, y))
    from core.hud import text as hudtext
    small = max(9, int(16 * scale))
    if int(unit["officer_idx"]) > -1:
        img = style.render_text(lang.tr("Officer"), small,
                                hudtext.colour("value")[:3])
        surface.blit(img, img.get_rect(topright=at(AT[0] + 87 - BOX.x,
                                                   AT[1] + 2 - BOX.y)))
    if int(unit["current_speed"]) <= 0:
        img = style.render_text(lang.tr("Immobile"), small, (230, 60, 50))
        surface.blit(img, img.get_rect(center=at(AT[0] + 45 - BOX.x,
                                                 AT[1] + 70 - BOX.y)))
    return True
