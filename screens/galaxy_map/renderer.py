"""Galaxy map drawing — stars, names, nebulas, black holes, fleets.

Everything positional goes through core.mapcoords.MapView, so the
HD map box can sit anywhere and be any size; the transform back to
orion2re's 640x480 stays exact.

Anchor points follow the original (see mapcoords docstring):
stars are centred on their transformed point, nebulas and ship
icons hang from their top-left. Getting this wrong shifts sprites
by half their width, which looks like a calibration error but is
not one.

Scaled sprites are cached per (asset, pixel size). The cache is
keyed on the rounded size so a resize rebuilds once, not per frame.
"""
import math
import time

import pygame

from core import palette
from core import zoomtables as zt
from core.structs import star as star_struct

# ── Asset naming ─────────────────────────────────────────

#: spectral_class -> folder name under assets/stars/
CLASS_DIRS = {
    star_struct.CLASS_B: "blue",
    star_struct.CLASS_F: "white",
    star_struct.CLASS_G: "yellow",
    star_struct.CLASS_K: "orange",
    star_struct.CLASS_M: "red",
    star_struct.CLASS_DWARF: "brown",
}

#: Number of star sprite steps. orion2re ships SIX pre-rendered
#: sprites per spectral class and indexes them with
#: (zoom_level + star.size) — one axis, not two
#: (MAINSCR::Get_Star_Picture_Seg_, BUFFER0.LBX 148 + class*6 + idx).
#: A large star at zoom 1 is the same sprite as a medium at zoom 0.
STEP_COUNT = len(zt.STAR_FIELDS_DIM)

#: Legacy artwork keyed by star.size alone (one file scaled to every
#: zoom). Still resolvable so a mod shipping only these keeps working;
#: each step falls back to its nearest legacy file.
SIZE_DIRS = {0: "large", 1: "medium", 2: "small"}
LEGACY_FOR_STEP = ("large", "large", "medium", "medium", "small", "small")

# ── Colours (all skin-overridable) ───────────────────────

#: Star name colour per owning player's `color` field (0..7).
OWNER_COLORS = {
    0: palette.col("galaxy_map", "owner_0", (196, 74, 56)),
    1: palette.col("galaxy_map", "owner_1", (206, 172, 34)),
    2: palette.col("galaxy_map", "owner_2", (86, 166, 70)),
    3: palette.col("galaxy_map", "owner_3", (226, 226, 234)),
    4: palette.col("galaxy_map", "owner_4", (126, 174, 216)),
    5: palette.col("galaxy_map", "owner_5", (196, 130, 88)),
    6: palette.col("galaxy_map", "owner_6", (162, 104, 136)),
    7: palette.col("galaxy_map", "owner_7", (238, 132, 12)),
}
NEUTRAL_COLOR = palette.col("galaxy_map", "star_name", (150, 152, 166))
OUTLINE_COLOR = palette.col("galaxy_map", "star_name_outline", (0, 0, 0))
#: Wormhole link colour, RGBA. The original draws these in palette
#: index 4 (MAINSCR::Draw_Wormhole_Links_ -> line::Line_(..., 4)), a
#: dark grey barely above the star field — on the original screenshot
#: the links read as a hint, not as a border. A skin can override both
#: the tint and the alpha; the fourth component is optional.
WORMHOLE_COLOR = palette.col("galaxy_map", "wormhole",
                             (128, 150, 190, 90))

# ── Sizing ───────────────────────────────────────────────
# Star and black hole sizes are NOT tuned here — they come from
# core.zoomtables, which transcribes orion2re's own dimension
# tables. Both scale with the zoom level, so zooming in enlarges
# icons exactly as the original does.

#: Nebula size comes from core.zoomtables.NEBULA_DIM — the sprite
#: dimensions of the four pre-rendered variants the original swaps
#: between, per type and zoom level.
#:
#: It used to be derived from the HD artwork instead
#: (asset_width / 3 as the world footprint, then x 10 / map_scale).
#: That held exactly as long as every master stayed at 3 x its
#: original sprite, and broke the moment new artwork was drawn at a
#: working resolution of its own: the twelve current masters imply
#: scale factors between 3.3 and 4.1, so each type came out its own
#: amount too large, and the error rode along with the zoom level —
#: which is why it read as "wrong per galaxy". Artwork resolution is
#: now irrelevant to size; only its aspect ratio still matters.

#: Additive strength. The original draws nebulas OPAQUE over black
#: space, so their visual weight equals their pixel brightness.
#: Additive blending reproduces exactly that on any background:
#: near-black gas adds nothing, bright wisps glow. A flat alpha
#: instead washes the whole bounding box over a lit background,
#: because even the near-black interior keeps ~55% coverage.
#: 255 = original brightness; slightly below keeps star names on
#: top comfortably readable.
NEBULA_BRIGHTNESS = 230

#: Black hole animation. The original advances its frames only
#: while icons are drawn at full size (Advance_Black_Hole_Animation_),
#: which core.zoomtables.black_hole_animates() reports.
#:
#: There is NO brightness pulse. An earlier version faded the sprite
#: between alpha 165 and 255 every 4.8 s, which read as breathing and
#: drowned out the 40 s rotation. It was invented here, not
#: transcribed: MOO2 draws palette-indexed and has no alpha blending
#: at all, so the original could not pulse a sprite even if it wanted
#: to. Frames are therefore left at their own per-pixel alpha and
#: set_alpha is never called.
#:
#: Note for anyone tempted to reinstate it: set_alpha(None) is NOT
#: how you turn a pulse off. In pygame 2 it switches the surface to
#: SDL_BLENDMODE_NONE, which ignores per-pixel alpha entirely and
#: draws the sprite's full bounding box as an opaque square.
#: Seconds per revolution, and how finely the revolution is cut.
#:
#: The two used to be one decision, because the frames were
#: pre-rendered: 72 frames over 40 s meant a 5-degree jump every
#: 0.55 s, which at a 117 px icon moves the outer edge 5 px at a
#: time. Slowing that down without adding frames only spaces the
#: same jumps further apart, so it reads MORE stepped, not less.
#:
#: Frames are now rotated on demand (see _rotated_frame), so the
#: two numbers are independent. BH_ROTATE_STEPS is an angular
#: RESOLUTION — half a degree, which moves a 117 px icon's outer
#: edge by 0.5 px and a 195 px icon's by 0.85 px, i.e. under one
#: pixel everywhere the black hole is ever drawn. Below a pixel the
#: antialiasing carries the motion and the step stops being a step.
#:
#: Cost is per step reached, not per rendered frame: 720 steps over
#: 90 s is 8 rotations a second, about 2.5 ms each, shared by every
#: black hole on the map because they all turn in phase. Neither
#: number changes that; a faster period just reaches steps sooner.
BH_ROTATE_PERIOD_S = 90.0
BH_ROTATE_STEPS = 720

STAR_NAME_GAP = 0.30      # of icon height, below the star centre

#: Wormhole links are drawn one pixel wide and antialiased. The
#: original is one native pixel; a thicker HD line turns a faint hint
#: into a hard border across the map.


class MapContext:
    """Everything the layers need that depends on the zoom level.

    Derived once per frame rather than per sprite: zoom_level()
    walks a small decision tree, and every layer would otherwise
    recompute the same answer for every star on the map.
    """

    def __init__(self, view, state):
        self.view = view
        self.map_scale = getattr(state, "map_scale", 10) or 10
        self.num_stars = len(getattr(state, "stars", None) or [])

        # _max_map_scale and _max_zoom_count are NOT in the snapshot.
        # Both follow from MAP_MAX_X, which is — see zoomtables.
        map_max_x = getattr(state, "map_max_x", 0) or 0
        self.max_map_scale = zt.max_map_scale(map_max_x) or self.map_scale
        self.max_zoom = zt.max_zoom_count(map_max_x)

        # max_map_scale must go in as well: above 72 stars the zoom
        # ladder is derived from it by halving, and without it every
        # scale reports max_zoom (see zoomtables.zoom_level).
        # hd_zoom_level, not zoom_level: the decoupled HD viewport
        # produces scales between the rungs, and the transcription
        # answers those with max zoom. On the rungs themselves —
        # which is all the game ever reports — both are identical.
        self.zoom = zt.hd_zoom_level(self.map_scale, self.max_zoom,
                                     self.num_stars, self.max_map_scale)
        #: HD pixels per native pixel — the single conversion factor.
        self.px = view.scale

    def star_px(self, star_size):
        """HD width of a star icon."""
        return max(2, int(zt.star_dimension(
            star_size, self.zoom, self.num_stars, self.map_scale) * self.px))

    def black_hole_px(self):
        return max(2, int(zt.black_hole_dimension(
            self.zoom, self.num_stars, self.map_scale) * self.px))

    def nebula_px(self, neb_type):
        """HD width of a nebula of type `neb_type`.

        From the WORLD footprint through the current scale, not from
        the per-zoom sprite table — see
        zoomtables.nebula_native_dimension for the full reasoning.
        Short version: a nebula is a patch of sky, so it has to move
        with the stars it contains, and the per-zoom variants do not
        (they are 12 to 25 % off 10/map_scale, differently per rung).
        Under a continuous HD zoom that error stops being frozen and
        turns into stars drifting across the gas edge.
        """
        native = zt.nebula_native_dimension(neb_type, self.map_scale,
                                            self.num_stars)[0]
        return max(8, int(native * self.px))

    @property
    def animate_black_holes(self):
        return zt.black_hole_animates(self.num_stars, self.map_scale)

    @property
    def names_hidden(self):
        return zt.names_suppressed(self.num_stars, self.map_scale,
                                   self.max_map_scale)

    @property
    def name_font_scale(self):
        return zt.font_scale(self.zoom)


class SpriteCache:
    """Scales sprites on demand and remembers the result.

    Keyed by (name, width) — height follows from the aspect ratio,
    so a single number identifies a scaled variant.
    """

    def __init__(self):
        self._base = {}
        self._scaled = {}
        self._circular = {}
        self._rotations = {}

    def put(self, name, surface):
        self._base[name] = surface
        self._circular.pop(name, None)
        # Keyed by (name, factor), so every factor of this name goes.
        for key in [k for k in self._rotations if k[0] == name]:
            del self._rotations[key]

    def base(self, name):
        """The unscaled master, or None. Read-only counterpart to put().

        The masters are already loaded once per screen, so anything
        that wants to inspect the artwork itself — the smoke test
        measures every nebula against its extracted original — reads
        it from here instead of opening the file a second time.
        """
        return self._base.get(name)

    def supersampled(self, name, factor):
        """The master at `factor` x its own size, or None.

        Kept out of `_scaled` on purpose: it does not depend on an
        icon size, so a resolution change must not throw it away.
        Rotation reads from here — see _rotated_frame for why the
        rotation happens at master resolution and not at icon size.
        """
        key = (name, int(factor))
        if key not in self._rotations:
            src = self._base.get(name)
            if src is None or src.get_width() != src.get_height():
                self._rotations[key] = None
            else:
                side = src.get_width() * int(factor)
                self._rotations[key] = pygame.transform.smoothscale(
                    src, (side, side))
        return self._rotations[key]

    def circular(self, name):
        """Whether this asset's content fits its inscribed circle.

        Answered from the unscaled base once and remembered, because
        the answer is a property of the artwork, not of a size.
        """
        hit = self._circular.get(name)
        if hit is None:
            src = self._base.get(name)
            hit = bool(src is not None and _content_is_circular(src))
            self._circular[name] = hit
        return hit

    def has(self, name):
        return name in self._base

    def scaled(self, name, width):
        src = self._base.get(name)
        if src is None or width < 1:
            return None
        width = int(width)
        key = (name, width)
        hit = self._scaled.get(key)
        if hit is not None:
            return hit
        ratio = src.get_height() / src.get_width()
        surf = pygame.transform.smoothscale(
            src, (width, max(1, int(width * ratio))))
        self._scaled[key] = surf
        return surf

    def scaled_additive(self, name, width, brightness):
        """scaled(), premultiplied by its own alpha, then dimmed.

        BLEND_RGB_ADD ignores the alpha channel, so an asset whose
        transparent margin carries non-black RGB (palette index 0 is
        not always black) would brighten its whole bounding box into
        a visible rectangle. Blitting onto black with normal alpha
        blending yields rgb * alpha exactly: fully transparent pixels
        become black and add nothing, edge pixels contribute in
        proportion. Done once per cached size, not per frame.
        """
        key = (name, int(width), int(brightness), "add")
        hit = self._scaled.get(key)
        if hit is not None:
            return hit
        src = self.scaled(name, width)
        if src is None:
            return None
        surf = pygame.Surface(src.get_size())      # opaque, black
        surf.blit(src, (0, 0))                     # -> rgb * alpha
        if brightness < 255:
            surf.fill((brightness,) * 3, special_flags=pygame.BLEND_RGB_MULT)
        self._scaled[key] = surf
        return surf

    def clear_scaled(self):
        self._scaled.clear()


# ── Black hole animation ─────────────────────────────────

#: Supersampling factor for the rotation. The master is scaled up
#: once, rotated at that size and scaled back down to the icon size,
#: which is what keeps the sprite on its axis — see _rotated_frame.
BH_ROTATE_SUPERSAMPLE = 2


def _rotated_frame(cache, name, width, angle, supersample=BH_ROTATE_SUPERSAMPLE):
    """`name` rotated by `angle` degrees, exactly `width` px square.

    Three approaches were measured before this one, and the two that
    failed are worth keeping because both looked obviously right.

    1. `pygame.transform.rotate`, cropping the middle of the result
       with `(rw - side) // 2`. Rotate returns the bounding box of the
       rotated rectangle, whose edge length is even at some angles and
       odd at others, so the floor truncated in a direction that
       changed per frame. Drift: 1.3 px at 117, 2.9 px at 195. On
       screen the black hole swam instead of turning.

    2. Aligning each frame by its alpha bounding box, on the theory
       that circular content gives a rotation-invariant box. Rotate
       applies no filtering, so the ragged edge gains and loses pixels
       per angle; across 5..75 degrees the box ran from 179x183 to
       185x186. Drift got WORSE: 5.0 px at 195.

    3. Measuring the event horizon per frame and correcting. Also
       worse — the thresholded centroid is noisier than the error it
       was correcting.

    What works is the plain geometric centre with a filtered rotation.
    `rotozoom` interpolates where `rotate` snaps, and it maps the
    source centre onto (rw/2, rh/2) exactly, so centring by surface
    size is correct as long as the offset is rounded rather than
    floored. What is left is that rounding, and supersampling is what
    shrinks it: the offset is rounded at master resolution and the
    error divides by the downscale.

    Residual drift is 0.37 px at 117 and 0.70 px at 195 — against a
    measurement floor of 0.26 and 0.63 px established from the exact
    90-degree frames, which cannot drift at all. So roughly a tenth of
    a pixel is real and the rest is the ruler.

    Rotating at ICON size instead, and skipping the supersample,
    would cost 0.19 ms rather than 2.5 — and drifts 1.4 px, because
    the same half-pixel rounding then lands at final scale with
    nothing to divide it. That is the whole reason this is not the
    obvious one-line `rotozoom` call.

    Returns None for artwork that is not a square circle; the caller
    then falls back to the old path rather than not drawing.
    """
    if not cache.circular(name):
        return None
    big = cache.supersampled(name, supersample)
    if big is None:
        return None
    side = big.get_width()
    rot = pygame.transform.rotozoom(big, angle, 1.0)
    rw, rh = rot.get_size()
    dst = pygame.Surface((side, side), pygame.SRCALPHA)
    dst.blit(rot, (int(round((side - rw) / 2.0)),
                   int(round((side - rh) / 2.0))))
    w = max(1, int(width))
    return pygame.transform.smoothscale(dst, (w, w))


def _content_is_circular(surface):
    """True when nothing visible lies outside the inscribed circle.

    Such a sprite can be rotated inside its own square without
    padding: the corners are empty, so nothing can move into them.
    tools/make_black_hole_master.py cuts its output to a circle for
    exactly this reason. Measured once per asset, not per frame.
    """
    w, h = surface.get_size()
    if w != h:
        return False
    try:
        alpha = pygame.surfarray.array_alpha(surface)
    except Exception:
        return False
    import numpy as _np
    c = (w - 1) / 2.0
    y, x = _np.mgrid[0:w, 0:h]
    outside = _np.hypot(x - c, y - c) > c
    return not bool((alpha[outside] > 8).any())


def black_hole_step(now=None):
    """Which of the BH_ROTATE_STEPS angles the clock is on right now.

    Split out so a test can ask for any step without waiting for the
    clock to reach it.
    """
    if now is None:
        now = time.time()
    return int((now / BH_ROTATE_PERIOD_S) * BH_ROTATE_STEPS) % BH_ROTATE_STEPS


def _black_hole_frame(cache, width, animate=True, step=None):
    """The black hole at `width` px, turned to the current angle.

    `animate=False` returns the still frame at angle 0, matching
    MAP_SCALE::Advance_Black_Hole_Animation_: the original stops black
    hole animation once icons are being shrunk.

    ONE FRAME IS KEPT, not a set. The frames used to be pre-rendered,
    which tied smoothness to the frame count and the frame count to
    memory: half-degree steps at a 195 px icon would be 720 surfaces,
    55 MB per icon size, and a second of freeze the first time a black
    hole appeared. Rotating on demand costs 2.5 ms and is paid only
    when the angle actually reaches a new step — 8 times a second at
    the shipped period — and every black hole on the map shares the
    result, because they all turn in phase off one clock.

    The single slot is enough because a map has exactly one icon size
    at a time. Zooming changes the width continuously and therefore
    misses the slot every frame, which is correct: the sprite has to
    be rebuilt at the new size anyway.

    Artwork that is not circular cannot be rotated inside its own
    square, so it falls back to diagonal padding and an unfiltered
    rotate. That path drifts by up to a pixel; it exists so an
    unexpected master still renders instead of vanishing.
    """
    if step is None:
        step = black_hole_step() if animate else 0
    key = (int(width), int(step))
    slot = cache._scaled.get("_bh_slot")
    if slot is not None and slot[0] == key:
        return slot[1]

    angle = 360.0 * step / BH_ROTATE_STEPS
    frame = _rotated_frame(cache, "black_hole", width, angle)

    if frame is None:
        base = cache.scaled("black_hole", width)
        if base is None:
            return None
        bw, bh = base.get_size()
        diag = int(math.ceil(math.hypot(bw, bh))) + 2
        if (diag - bw) % 2:
            diag += 1
        square = pygame.Surface((diag, diag), pygame.SRCALPHA)
        square.blit(base, ((diag - bw) // 2, (diag - bh) // 2))
        rot = pygame.transform.rotate(square, angle)
        rw, rh = rot.get_size()
        frame = rot.subsurface(pygame.Rect(
            (rw - diag) // 2, (rh - diag) // 2, diag, diag)).copy()

    cache._scaled["_bh_slot"] = (key, frame)
    return frame


# ── Layers ───────────────────────────────────────────────

def render_nebulas(surface, ctx, nebulas, cache, forms):
    """Nebulas sit behind everything; anchored TOP-LEFT.

    Blitted ADDITIVELY (see NEBULA_BRIGHTNESS): the original
    composites opaque gas over black space, and addition gives the
    identical result over the HD backdrop without washing the
    sprite's bounding box across it. BLEND_RGB_ADD ignores alpha,
    so the cache hands back an alpha-premultiplied copy — see
    scaled_additive(); without it, artwork whose transparent margin
    is not pure black shows its bounding box as a rectangle.
    """
    if not nebulas or not forms:
        return
    view = ctx.view
    for neb in nebulas:
        # savegame.cpp validates type 0..11; with all twelve forms
        # in layout.json this modulo is exact, not a wrap-around.
        name = forms[neb.type % len(forms)]
        if not cache.has(name):
            continue
        # Sized from neb.type, never from the artwork: a master drawn
        # at 2000 px and one drawn at 555 px must land on the same
        # patch of sky. The asset only contributes its aspect ratio,
        # which scaled() preserves.
        img = cache.scaled_additive(name, ctx.nebula_px(neb.type),
                                    NEBULA_BRIGHTNESS)
        if img is None:
            continue
        sx, sy = view.to_screen(neb.x, neb.y)
        surface.blit(img, (int(sx), int(sy)),
                     special_flags=pygame.BLEND_RGB_ADD)


class WormholeLayer:
    """Cached, antialiased overlay for the wormhole links.

    Two reasons this is not just a draw call:

    1. pygame.draw.aaline antialiases but IGNORES the alpha in its
       colour, and pygame.gfxdraw.line honours alpha but does not
       antialias. Neither alone gives a faint, smooth line. Drawing
       white aalines onto a transparent layer and then multiplying the
       whole layer by an RGBA colour gives both: the coverage the
       antialiasing produced survives as alpha and gets scaled.

    2. A per-pixel-alpha surface the size of the map box is several
       megabytes; allocating and clearing one every frame would cost
       more than everything else this screen draws. The links only
       move when the view or the visible set changes, so the layer is
       rebuilt on a key and reused otherwise.

    Faintness matters more than it sounds: the original draws these in
    palette index 4 (MAINSCR::Draw_Wormhole_Links_, `line::Line_(...,
    4)`), a dark grey barely above the background. A bright line reads
    as a border between regions rather than a route.
    """

    def __init__(self):
        self._key = None
        self._layer = None

    def clear(self):
        self._key = None
        self._layer = None

    def _build(self, box, segments, colour):
        w, h = max(1, int(box[2])), max(1, int(box[3]))
        layer = pygame.Surface((w, h), pygame.SRCALPHA)
        ox, oy = box[0], box[1]
        for x1, y1, x2, y2 in segments:
            pygame.draw.aaline(layer, (255, 255, 255),
                               (x1 - ox, y1 - oy), (x2 - ox, y2 - oy))
        rgba = tuple(colour[:3]) + (
            colour[3] if len(colour) > 3 else 255,)
        layer.fill(rgba, special_flags=pygame.BLEND_RGBA_MULT)
        self._layer = layer

    def render(self, surface, box, segments, colour):
        key = (tuple(int(v) for v in box), tuple(segments),
               tuple(colour))
        if key != self._key:
            self._key = key
            self._build(box, segments, colour)
        if self._layer is not None:
            surface.blit(self._layer, (int(box[0]), int(box[1])))


def wormhole_segments(ctx, stars, player_num, omniscient):
    """Visible wormhole links as (x1, y1, x2, y2) in screen space.

    MAINSCR::Draw_Wormhole_Links_ only draws a link the local player
    has EARNED: the origin system must have been visited, or the
    player must have Galactic Lore. Drawing every link would hand
    the user free map knowledge the original withholds.

    wormhole_star_id is -1 when a system has no link. A pair shows
    up twice, once from each end, but the two ends can differ in
    visibility — so this mirrors the original and tests each end
    separately rather than deduplicating.
    """
    view = ctx.view
    out = []
    for s in stars:
        other = getattr(s, "wormhole_star_id", -1)
        if other is None or other < 0 or other >= len(stars):
            continue
        if not (omniscient or star_struct.visited_by(s, player_num)):
            continue
        x1, y1 = view.to_screen(s.x, s.y)
        x2, y2 = view.to_screen(stars[other].x, stars[other].y)
        out.append((int(x1), int(y1), int(x2), int(y2)))
    return out


def render_wormholes(surface, ctx, stars, player_num, omniscient,
                     layer=None):
    """Lines between wormhole-linked systems, drawn under the stars."""
    segments = wormhole_segments(ctx, stars, player_num, omniscient)
    if not segments:
        if layer is not None:
            layer.clear()
        return
    if layer is None:
        layer = WormholeLayer()
    layer.render(surface, ctx.view.box, segments, WORMHOLE_COLOR)


def star_step(ctx, s):
    """The 0..5 sprite step for a star — HAROLD's combined index.

    Zoom level and star.size are ADDED, exactly as
    Map_Scale_Star_Size_To_Zoom_Level_ does, and clamped to the
    table. This is why zooming out one notch looks the same as the
    star being one size smaller: it is the same sprite.
    """
    return max(0, min(STEP_COUNT - 1, ctx.zoom + int(s.size)))


def star_icon_name(s, ctx=None):
    """Asset key for a star, or None when it has no icon."""
    if star_struct.is_black_hole(s):
        return "black_hole"
    folder = CLASS_DIRS.get(s.spectral_class)
    if not folder:
        return None
    if ctx is None:                      # no zoom context: middle step
        return f"stars/{folder}/{SIZE_DIRS.get(s.size, 'medium')}"
    return f"stars/{folder}/{star_step(ctx, s)}"


def star_icon_width(ctx, s):
    """HD icon width, straight from orion2re's dimension tables."""
    if star_struct.is_black_hole(s):
        return ctx.black_hole_px()
    return ctx.star_px(s.size)


def render_stars(surface, ctx, stars, cache):
    """Stars, anchored on their CENTRE. Returns icon heights by
    star index so the name layer can sit below each icon."""
    view = ctx.view
    heights = {}
    for s in stars:
        name = star_icon_name(s, ctx)
        if not name:
            continue
        width = star_icon_width(ctx, s)
        if star_struct.is_black_hole(s):
            img = _black_hole_frame(cache, width, ctx.animate_black_holes)
        else:
            img = cache.scaled(name, width)
        if img is None:
            continue
        sx, sy = view.to_screen(s.x, s.y)
        iw, ih = img.get_size()
        surface.blit(img, (int(sx - iw / 2), int(sy - ih / 2)))
        heights[s.index] = ih
    return heights


def star_label(s, player_num, players, omniscient):
    """Name to draw for a star, or "" when it stays hidden.

    Mirrors MAINSCR::Get_Star_Name_:
      - black holes are never labelled
      - without lore: an unvisited system with no contacted owner
        shows nothing
      - with lore: an unvisited foreign system shows "(Name)"
    """
    if star_struct.is_black_hole(s):
        return ""
    visited = star_struct.visited_by(s, player_num)
    owner = s.owner

    if not omniscient:
        has_contact = False
        if 0 <= owner < len(players) and owner != player_num:
            from core.structs import player as player_struct
            local = players[player_num] if player_num < len(players) else None
            if local is not None:
                has_contact = bool(player_struct.contacts(local)[owner])
        elif owner == player_num:
            has_contact = True
        if not has_contact and not visited:
            return ""
        return s.name

    if owner != player_num and not visited:
        return f"({s.name})"
    return s.name


def render_star_names(surface, ctx, stars, heights, render_label,
                      player_num, players, omniscient):
    """Star names with a one-pixel outline, centred under the icon.

    Bails out entirely when the map is too dense to label — see
    MAINSCR::Print_Star_Names_, which returns before drawing
    anything on an extended map at maximum zoom-out.

    `render_label(text, colour)` returns a surface. It is a callable
    rather than a pygame Font because a lore-only name reads "(Name)",
    and the DEMO Bank Gothic draws parentheses as a watermark — the
    caller hands in Style.render_text, which splits the string across
    two fonts. Keeping that decision out of here means the renderer
    still knows nothing about skins.
    """
    if ctx.names_hidden:
        return
    view = ctx.view
    for s in stars:
        label = star_label(s, player_num, players, omniscient)
        if not label:
            continue
        colour = NEUTRAL_COLOR
        owner = s.owner
        if 0 <= owner < len(players):
            pcol = getattr(players[owner], "color", None)
            if pcol is not None:
                colour = OWNER_COLORS.get(pcol, NEUTRAL_COLOR)

        text = render_label(label, colour[:3])
        shadow = render_label(label, OUTLINE_COLOR[:3])
        sx, sy = view.to_screen(s.x, s.y)
        ih = heights.get(s.index, 0)
        x = int(sx - text.get_width() / 2)
        y = int(sy + ih * STAR_NAME_GAP)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            surface.blit(shadow, (x + dx, y + dy))
        surface.blit(text, (x, y))


def render_fleets(surface, ctx, icons, players, cache, tints,
                  cfg=None, ships=None, anchor=None):
    """Fleet and monster icons from s_ship_icon.

    Everything about sprite choice, footprint and player tinting lives
    in screens/galaxy_map/ships.py; this stays a one-line entry point
    so the draw order in screen.py reads as one list of layers.
    """
    from screens.galaxy_map import ships as ship_icons
    ship_icons.render(surface, ctx, icons, players, cache, tints,
                      cfg=cfg, ships=ships, anchor=anchor)
