"""Zoom levels and sprite dimensions, transcribed from orion2re.

THREE INDEPENDENT AXES — do not conflate them:

1. ZOOM LEVEL (0..3), from MOX::_cur_map_scale via
   HAROLD::Map_Scale_To_Zoom_Level_. This is the ONLY thing that
   changes icon and font size. It changes while playing, every
   time the user hits + or -.

2. GALAXY SIZE, from MOX::_max_map_scale (recoverable from
   MAP_MAX_X). It does NOT scale anything by itself — it only
   caps how far out the user may zoom, via _max_zoom_count.
   A Huge galaxy zoomed fully IN draws exactly the same 33 px
   star as a Small galaxy, because both sit at scale 10 / zoom 0.
   The only reason a Small galaxy never shows small icons is that
   it cannot zoom out at all (max_zoom_count = 0).

3. STAR COUNT above 72, orion2re's extension beyond the original
   limit. MAP_SCALE::Star_Scale_Percent_ applies an EXTRA shrink
   of 3000/map_scale on top of axis 1, and only when map_scale
   also exceeds 30. In a vanilla game this is always 100 %.

Nothing here is measured or estimated. Sources:
  HAROLD::Map_Scale_To_Zoom_Level_       harold.cpp
  HAROLD::Map_Scale_Star_Size_To_Zoom_Level_
  MOX::_star_fields_dim[6]               harold.cpp (init)
  MAP_SCALE::Star_Scale_Percent_         map_scale.h
  MAP_SCALE::Scale_Star_Dimension_       map_scale.h
  MAINSCR::Draw_Black_Holes_ zoom_dist[] mainscr.cpp
  HAROLD::Zoom_Level_Font_Style_         harold.cpp
  MAPGEN (galaxy size -> max scale)      mapgen.cpp
  MAPGEN::Load_Nebula_Pictures_          mapgen.cpp + STARBG.LBX
                                         (sprite headers, see
                                          NEBULA_DIM)

The original works in native 640x480 pixels. HD rendering wants
fractions of the map width instead, so each table also has a
`*_fraction` helper dividing by MAP_WIDTH.
"""

#: Visible map width in native pixels (527 - 22, see mapcoords).
MAP_WIDTH = 505

#: Star count above which orion2re switches to extended scaling.
ORIGINAL_MAX_STARS = 72

#: AXIS 2 reference data (mapgen.cpp): per galaxy size, the value
#: _max_map_scale is initialised to and the highest zoom level it
#: permits. This caps the zoom RANGE only — it is deliberately not
#: consulted by any sizing function, because galaxy size does not
#: scale icons. Kept for diagnostics and for reading MAP_MAX_X back.
GALAXY_MAX_SCALE = {
    "small":  (10, 0),
    "medium": (15, 1),
    "large":  (20, 2),
    "huge":   (30, 3),
}

#: MOX::_star_fields_dim — indexed by (zoom_level + star.size).
#: Six entries cover zoom 0..3 combined with size 0..2.
STAR_FIELDS_DIM = (33, 29, 25, 23, 21, 17)

#: MAINSCR::Draw_Black_Holes_ zoom_dist[4]. Black holes use their
#: own table and ignore star.size entirely — and zoom 1 and 2 are
#: deliberately the same value in the original.
BLACK_HOLE_DIM = (39, 33, 33, 24)

#: Nebula footprint in native pixels, [type][zoom_level] -> (w, h).
#:
#: Not a source array and not a screenshot measurement: these are the
#: sprite header dimensions of STARBG.LBX entries 6..53, the twelve
#: types x four pre-rendered zoom variants the original swaps between
#: (mapgen.cpp Load_Nebula_Pictures_: entry = type * 4 + zoom + 6).
#: Read back by tools/nebula_extract.py; the reference PNGs and
#: summary.txt under screens/galaxy_map/assets/nebula_ref are the
#: receipt for every number below.
#:
#: Cross-check, second independent source: variant 3 doubles as the
#: gameplay shape, and geo.cpp Point_Is_In_Nebula_N_ maps world
#: coordinates onto its pixel grid through a division by 3. So
#: zoom_3_size * 3 is the nebula's extent in WORLD units, and it
#: agrees with the zoom-0 size here to within 7 % for all twelve
#: types (type 0: 183 vs 185). That is what makes the zoom-0 column
#: the world footprint at map scale 10, where one world unit is one
#: native pixel.
#:
#: The columns are close to Get_Scaled_Value_ (x 10 / map_scale, i.e.
#: 1.0 / 0.667 / 0.5 / 0.333) but not equal to it — per type the
#: measured ratios wander between 0.62 and 0.75 at zoom 1. A formula
#: therefore cannot replace this table, and the artwork's own pixel
#: size must never stand in for it: HD masters are drawn at whatever
#: resolution the artist worked at.
#:
#: NOTE: the renderer does NOT size nebulas from the zoom columns —
#: it uses column 0 as a world footprint and scales it continuously
#: (nebula_native_dimension). The columns 1..3 are kept as the
#: transcription and as the receipt for column 0; the reason the
#: drawn size no longer follows them is written out there.
NEBULA_DIM = (
    ((185, 174), (138, 132), ( 87,  83), ( 61,  56)),   #  0
    ((176, 179), (124, 129), ( 86,  88), ( 48,  51)),   #  1
    ((190, 184), (131, 127), ( 90,  87), ( 66,  67)),   #  2
    ((158, 171), (119, 125), ( 78,  80), ( 57,  56)),   #  3
    ((206, 192), (137, 127), ( 99,  92), ( 65,  60)),   #  4
    ((202, 191), (134, 127), ( 96,  89), ( 67,  63)),   #  5
    ((192, 183), (135, 127), ( 88,  84), ( 60,  55)),   #  6
    ((190, 186), (127, 122), ( 86,  84), ( 64,  64)),   #  7
    ((171, 176), (118, 124), ( 81,  83), ( 53,  55)),   #  8
    ((170, 184), (105, 114), ( 81,  90), ( 61,  58)),   #  9
    ((201, 189), (136, 132), ( 98,  94), ( 63,  61)),   # 10
    ((209, 206), (130, 132), ( 94,  93), ( 64,  64)),   # 11
)

#: Number of nebula shapes; savegame.cpp and netmox.cpp both reject a
#: savegame with type outside 0..11, and Draw_Nebulae_ indexes with
#: type % 12.
NEBULA_TYPE_COUNT = len(NEBULA_DIM)

#: Whether an extended galaxy (> 72 stars, map_scale > 30) shrinks
#: nebulas the way it shrinks stars.
#:
#: UNCONFIRMED, and deliberately False. Star_Scale_Percent_ is only
#: consulted by Map_Scale_Star_Size_To_Zoom_Level_; ship icons have no
#: scaling path at all and keep their size out there. Nebulas swap
#: pre-rendered variants exactly like ship icons do, so they are
#: treated the same until MAINSCR::Draw_Nebulae_ says otherwise.
#: To settle it: grep Draw_Nebulae_ for Star_Scale_Percent_ or
#: Scale_Bitmap_. If it scales, flip this to True — the code path is
#: already here.
NEBULA_EXTENDED_SHRINK = False

#: HAROLD::Zoom_Level_Font_Style_ — the original picks a font
#: STYLE, not a pixel size. Mapped here to relative text scale so
#: an HD renderer can pick a proportional size.
FONT_STYLE_BY_ZOOM = (3, 2, 2, 1)
FONT_SCALE_BY_ZOOM = (1.00, 0.86, 0.86, 0.72)

#: SHIPS::Get_XYs_For_Orbiting_Ships_ — vertical spacing between
#: stacked orbit slots is (11 - zoom_level) native pixels.
ORBIT_STACK_STEP_BASE = 11

#: Ship icon footprint in native pixels, indexed by zoom level.
#:
#: DERIVED, not transcribed — mark any change as a deviation. Unlike
#: the star table there is no array in the source: the sizes live in
#: BUFFER0.LBX (SHIPS::Get_Ship_Icon_Pict_Seg_ loads entry
#: 205 + colour*4 + (3 - zoom)) and are only read back at runtime into
#: MOX::_ship_icon_width/_height[4] (ships.cpp:328).
#:
#: MEASURED, 29 August, from a native 640x480 screenshot: the central
#: blob of the sprite, threshold-swept and cross-checked against the
#: pixel map, is 11 x 10 px at zoom 0. See
#: doc/ship_icon_measurement.md for the method and why it matters.
#:
#: The per-step shrink is one pixel, from the only hint the source
#: gives: MAINSCR::Do_Fleet_Popup_ passes (13 - zoom, 9 - zoom) to
#: Overlapped_Ship_Icon_Button_ as proximity thresholds. Those numbers
#: are NOT the icon size — threshold_y is smaller than the measured
#: height — but the -1 per zoom step is.
#:
#: The height must stay below the orbit stack step (11 - zoom), or
#: four fleets at one star collide. 10 < 11 at every step.
SHIP_ICON_DIM = ((11, 10), (10, 9), (9, 8), (8, 7))

#: Monster icon footprints at zoom 0, measured the same way. Each
#: type has its OWN sprite set in the original (BUFFER0.LBX
#: 241 + (type - 9) * 4 + zoom), so the sizes genuinely differ per
#: type — a guardian is not a ship-sized dot.
#:
#: The guardian was 17 x 16 here until 29 August, and it was wrong:
#: at a low threshold a faint pixel bridge merged the sprite with
#: nearby background stars. It measures 12 x 11. The number reached
#: production because it was never sanity-checked against the others,
#: and it showed on screen as a monster half again too large.
#:
#: UNVERIFIED for amoeba and antaran: no screenshot exists yet, so
#: they borrow the eel and the player footprint respectively.
MONSTER_ICON_DIM_ZOOM0 = {
    "guardian": (12, 11),
    "crystal":  (13, 13),
    "dragon":   (13, 10),
    "hydra":    (11, 12),
    "eel":      ( 9,  9),
    "amoeba":   ( 9,  9),     # UNVERIFIED — copy of eel
    "antaran":  (11, 10),     # UNVERIFIED — copy of the player ship
}

#: Smallest footprint an icon may shrink to, native pixels.
MIN_ICON_DIM = 4

#: MAP_MAX_X / max_map_scale is the same constant for every galaxy
#: size (mapgen.cpp: 506/10, 759/15, 1012/20, 1518/30). The
#: Extension API serializes MAP_MAX_X but NOT _max_map_scale or
#: _max_zoom_count, so both are recovered from it rather than
#: guessed — or than patching the C++ side for two more int16s.
MAP_MAX_X_PER_SCALE = 50.6

#: max_map_scale -> max_zoom_count (mapgen.cpp, same switch).
MAX_ZOOM_BY_SCALE = {10: 0, 15: 1, 20: 2, 30: 3}


def max_map_scale(map_max_x):
    """Recover MOX::_max_map_scale from MAP_MAX_X.

    Returns 0 when map_max_x is missing or nonsensical, which the
    callers treat as "unknown" rather than substituting a value
    that would silently change rendering.
    """
    if not map_max_x or map_max_x <= 0:
        return 0
    scale = int(round(map_max_x / MAP_MAX_X_PER_SCALE))
    # Snap to a value the game actually uses; anything else means
    # a modded galaxy size, and the raw estimate is the best guess.
    for known in (10, 15, 20, 30):
        if abs(scale - known) <= 1:
            return known
    return scale


def max_zoom_count(map_max_x):
    """Recover MOX::_max_zoom_count from MAP_MAX_X."""
    scale = max_map_scale(map_max_x)
    if scale in MAX_ZOOM_BY_SCALE:
        return MAX_ZOOM_BY_SCALE[scale]
    return 3 if scale else 3


def scale_rungs(max_zoom_count=3, num_stars=0, max_map_scale=None):
    """The map_scale values the game itself can stand on.

    Vanilla ladder 10/15/20/30 up to `max_zoom_count`; the extended
    ladder (over 72 stars) is built by halving max_map_scale, exactly
    as _extended_scale_for_zoom does. Sorted ascending.
    """
    if num_stars > ORIGINAL_MAX_STARS and max_map_scale:
        rungs = sorted({_extended_scale_for_zoom(
            max_map_scale, max_zoom_count, lvl)
            for lvl in range(0, max_zoom_count + 1)})
    else:
        rungs = [10, 15, 20, 30][:max_zoom_count + 1] or [10]
    return rungs


def hd_zoom_level(map_scale, max_zoom_count=3, num_stars=0,
                  max_map_scale=None):
    """Zoom level for a CONTINUOUS scale. HD EXTENSION, NOT TRANSCRIBED.

    The decoupled HD viewport zooms smoothly, so its scale sits
    between the rungs the original can stand on — and the transcribed
    zoom_level() answers "not a rung" with max zoom, which would draw
    the smallest sprites while nearly fully zoomed in. This helper
    snaps the scale to the NEAREST rung (ties toward the zoomed-in
    one) and asks the transcription about that rung, so on-rung
    values, including everything the game itself reports, answer
    exactly as before. The deviation is confined to the in-between
    values the original never produces.
    """
    rungs = scale_rungs(max_zoom_count, num_stars, max_map_scale)
    nearest = min(rungs, key=lambda r: (abs(map_scale - r), r))
    return zoom_level(nearest, max_zoom_count, num_stars,
                      max_map_scale)


def zoom_level(map_scale, max_zoom_count=3, num_stars=0,
               max_map_scale=None):
    """HAROLD::Map_Scale_To_Zoom_Level_.

    Returns 0..3. `max_zoom_count` clamps the result, exactly as
    the original does — a small galaxy never leaves zoom 0.

    `max_map_scale` is only consulted on the extended path (more
    than 72 stars), where the scale ladder is built by halving it
    rather than by the fixed 10/15/20 comparison. **It has to be
    passed there.** Omitting it makes _extended_zoom_level fall back
    to `map_scale`, which satisfies its own top rung at every scale
    and pins an extended galaxy to max_zoom no matter how far the
    player zooms in — every sprite, font and icon then draws at its
    smallest step. That was the state until 29 August; the argument
    existed on the inner function and no caller supplied it.
    """
    if num_stars > ORIGINAL_MAX_STARS:
        return _extended_zoom_level(map_scale, max_zoom_count,
                                    max_map_scale)

    if map_scale == 10 and max_zoom_count >= 0:
        return 0
    if map_scale == 15 and max_zoom_count >= 1:
        return 1
    if map_scale == 20 and max_zoom_count >= 2:
        return 2
    if map_scale not in (10, 15, 20) and max_zoom_count >= 3:
        return 3
    return max_zoom_count


def _extended_scale_for_zoom(max_map_scale, max_zoom, level):
    """MAP_SCALE::Extended_Scale_For_Zoom_Level_ — repeated halving."""
    level = max(0, level)
    if level >= max_zoom:
        return max_map_scale
    scale = max_map_scale
    for _ in range(max_zoom, level, -1):
        scale = (scale + 1) // 2
    return scale


def _extended_zoom_level(map_scale, max_zoom, max_map_scale=None):
    """MAP_SCALE::Extended_Zoom_Level_For_Scale_."""
    if max_map_scale is None:
        max_map_scale = map_scale
    for level in range(max_zoom, 0, -1):
        if map_scale >= _extended_scale_for_zoom(
                max_map_scale, max_zoom, level):
            return level
    return 0


def star_scale_percent(num_stars, map_scale):
    """MAP_SCALE::Star_Scale_Percent_.

    100 in every ordinary game. Only a galaxy with more stars than
    the original supported, viewed beyond scale 30, shrinks icons.
    """
    if num_stars <= ORIGINAL_MAX_STARS or map_scale <= 30:
        return 100
    return 3000 // map_scale


def scale_star_dimension(dimension, percent):
    """MAP_SCALE::Scale_Star_Dimension_ — never below 3 px."""
    if percent >= 100:
        return dimension
    dimension = (dimension * percent) // 100
    return 3 if dimension < 3 else dimension


def star_dimension(star_size, zoom, num_stars=0, map_scale=10):
    """Native pixel size of a star icon.

    HAROLD::Map_Scale_Star_Size_To_Zoom_Level_: the zoom level and
    the star's own size index the SAME table, added together.
    """
    idx = zoom + int(star_size)
    idx = max(0, min(len(STAR_FIELDS_DIM) - 1, idx))
    return scale_star_dimension(
        STAR_FIELDS_DIM[idx], star_scale_percent(num_stars, map_scale))


def black_hole_dimension(zoom, num_stars=0, map_scale=10):
    """Native pixel size of a black hole (ignores star.size)."""
    zoom = max(0, min(len(BLACK_HOLE_DIM) - 1, zoom))
    return scale_star_dimension(
        BLACK_HOLE_DIM[zoom], star_scale_percent(num_stars, map_scale))


def black_hole_animates(num_stars, map_scale):
    """MAP_SCALE::Advance_Black_Hole_Animation_.

    The original freezes black hole animation once icons are being
    shrunk — a huge galaxy at maximum zoom-out has still frames.
    """
    return star_scale_percent(num_stars, map_scale) >= 100


def names_suppressed(num_stars, map_scale, max_map_scale):
    """MAINSCR::Print_Star_Names_ bails out entirely here.

    MAP_SCALE::Is_Extended_Max_Map_View_: a galaxy larger than the
    original maximum, viewed at its widest, draws no star names at
    all — they would be unreadable and overlap.
    """
    return (num_stars > ORIGINAL_MAX_STARS
            and map_scale == max_map_scale)


def orbit_stack_step(zoom):
    """Vertical spacing of stacked orbit slots, native pixels."""
    return ORBIT_STACK_STEP_BASE - max(0, min(3, zoom))


def ship_icon_dimension(zoom):
    """(width, height) of a player ship icon in native pixels.

    Ship icons are NOT affected by star_scale_percent: the original
    has no scaling path for them at all (Get_Ship_Icon_Pict_Seg_ just
    picks a sprite). On an extended galaxy zoomed all the way out the
    stars shrink and the ships do not — that is original behaviour,
    not an oversight here.
    """
    zoom = max(0, min(len(SHIP_ICON_DIM) - 1, int(zoom)))
    return SHIP_ICON_DIM[zoom]


def monster_icon_dimension(kind, zoom):
    """(width, height) of a monster icon in native pixels.

    Same one-pixel-per-step shrink as the player ship, applied to the
    per-type zoom-0 footprint. Unknown types fall back to the player
    ship so a new monster never renders at a nonsense size.
    """
    base = MONSTER_ICON_DIM_ZOOM0.get(kind)
    if base is None:
        return ship_icon_dimension(zoom)
    zoom = max(0, min(len(SHIP_ICON_DIM) - 1, int(zoom)))
    return (max(MIN_ICON_DIM, base[0] - zoom),
            max(MIN_ICON_DIM, base[1] - zoom))


def nebula_dimension(neb_type, zoom, num_stars=0, map_scale=10):
    """(width, height) of a nebula in native pixels.

    Indexed by type AND zoom level, because the original ships four
    separately drawn variants per type and never scales them
    (MAINSCR::Draw_Nebulae_). Galaxy size enters only through the
    zoom level: a small galaxy is stuck at zoom 0 and therefore
    always shows the large variant, a huge one reaches zoom 3.

    The caller passes the raw s_nebula.type; the modulo mirrors
    _nebula_pict_seg[type % 12].
    """
    row = NEBULA_DIM[int(neb_type) % NEBULA_TYPE_COUNT]
    w, h = row[max(0, min(len(row) - 1, int(zoom)))]
    if NEBULA_EXTENDED_SHRINK:
        percent = star_scale_percent(num_stars, map_scale)
        w = scale_star_dimension(w, percent)
        h = scale_star_dimension(h, percent)
    return (w, h)


def nebula_world_dimension(neb_type):
    """(width, height) of a nebula in GALAXY units.

    The zoom-0 column: at map scale 10 one world unit is one native
    pixel, so that column is the footprint the map coordinates place
    the sprite into. Independent of zoom, unlike nebula_dimension().
    """
    return NEBULA_DIM[int(neb_type) % NEBULA_TYPE_COUNT][0]


def nebula_native_dimension(neb_type, map_scale, num_stars=0):
    """(width, height) in native pixels for a CONTINUOUS map scale.

    HD EXTENSION, NOT TRANSCRIBED — same class as hd_zoom_level().

    A nebula is not an icon. A star sprite may be any size at any
    zoom, because nothing on the map is measured against it; a
    nebula is a patch of SKY, and the stars inside it are inside it
    in the world, not on the screen (s_star_data.in_nebula,
    geo.cpp Point_Is_In_Nebula_N_). So its screen size must be its
    world footprint pushed through the current scale, exactly like a
    distance between two stars — nebula_world_dimension x 10 /
    map_scale — and never a per-zoom sprite size.

    What this deviates from, and why:

    The original ships four pre-drawn variants per type and swaps
    them by zoom level (nebula_dimension). Those variants are NOT
    exact reductions of each other — the measured ratios wander
    between 0.62 and 0.75 where 10/map_scale says 0.667 — so even
    in the original a nebula covers 12 % more sky at scale 15 than
    at scale 10, anchored top-left. The original gets away with it
    because it can only stand on four rungs and the mismatch is
    frozen at each one.

    A continuous HD scale cannot get away with it: the sprite size
    would hold still between two rungs while the world shrank under
    it, so the nebula would swell from 50 % to 130 % of its true
    footprint across the zoom range and snap back by up to 36 % at
    every rung change. Stars would cross the gas edge while
    standing still.

    On rung 0 (scale 10, where one world unit is one native pixel)
    this returns the transcribed value exactly. The deviation is
    confined to scales at which the original's own answer is
    self-inconsistent.
    """
    w, h = nebula_world_dimension(neb_type)
    if not map_scale:
        map_scale = 10
    factor = 10.0 / float(map_scale)
    w, h = w * factor, h * factor
    if NEBULA_EXTENDED_SHRINK:
        percent = star_scale_percent(num_stars, map_scale)
        w = scale_star_dimension(w, percent)
        h = scale_star_dimension(h, percent)
    return (w, h)


def nebula_fraction(neb_type, zoom, num_stars=0, map_scale=10):
    return nebula_dimension(
        neb_type, zoom, num_stars, map_scale)[0] / MAP_WIDTH


def icon_step_count():
    """Number of pre-rendered ship sprite steps (one per zoom level)."""
    return len(SHIP_ICON_DIM)


# ── HD helpers: native pixels -> fraction of map width ────

def star_fraction(star_size, zoom, num_stars=0, map_scale=10):
    return star_dimension(star_size, zoom, num_stars, map_scale) / MAP_WIDTH


def black_hole_fraction(zoom, num_stars=0, map_scale=10):
    return black_hole_dimension(zoom, num_stars, map_scale) / MAP_WIDTH


def ship_icon_fraction(zoom):
    return ship_icon_dimension(zoom)[0] / MAP_WIDTH


def font_scale(zoom):
    zoom = max(0, min(len(FONT_SCALE_BY_ZOOM) - 1, zoom))
    return FONT_SCALE_BY_ZOOM[zoom]
