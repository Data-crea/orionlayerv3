"""Galaxy map ship and monster icons.

WHAT ORION2RE GIVES US
----------------------
`s_ship_icon.x/y` are already 640x480 SCREEN coordinates with the
icon's TOP-LEFT as the anchor — orion2re fills them in
SHIPS::Set_Ship_Icon_XYs_ / MAINSCR::Draw_Ship_Icons_ using the orbit
slot geometry of Get_XYs_For_Orbiting_Ships_. Nothing here recomputes
slot positions; doing so would duplicate logic that can only drift.

An icon still carrying the -1 sentinel has not been placed this frame
and is skipped.

WHICH SPRITE
------------
SHIPS::Get_Ship_Icon_Pict_Seg_ (ships.cpp:337) dispatches on the
ship's `owner`:

    0..7   player      BUFFER0.LBX 205 + colour*4 + (3 - zoom)
    8      antaran     BUFFER0.LBX 237 + (3 - zoom)
    9..14  monster     BUFFER0.LBX 241 + (owner - 9)*4 + zoom

Note the inversion: players and Antarans index the sprite backwards
by zoom, monsters forwards. That is an LBX-layout detail and stops
here — every kind in this module uses `0.png`..`3.png` with the zoom
level as a plain index.

The eight player colours are ONE greyscale sprite tinted at runtime,
not eight files. Same principle as core/banner.py: the original ships
32 palette-swapped drawings, we ship one and multiply.

SIZE
----
Footprints come from core/zoomtables.py and nothing else
(architecture decision #28). They depend ONLY on the zoom level:
galaxy size caps how far the player may zoom out (_max_zoom_count),
it never scales an icon by itself. A Small galaxy is stuck at zoom 0
and therefore always draws the largest ship icon — which is exactly
what the reference screenshot shows.

Ship icons are also NOT touched by star_scale_percent. On an extended
galaxy (>72 stars) zoomed fully out the stars shrink and the ships do
not. That asymmetry is in the original.

OWNER
-----
`s_ship_icon` has no owner field. The chain in the C++ is
node_idx -> MOX::_ship_node[] -> MOX::_ship[].owner, and `_ship_node`
is not serialized — but it does not need to be. It is a pure function
of `_ship[]`, which IS serialized, so build_node_map() rebuilds it
from SHIPSTAK::Find_Ship_Stacks_ and owners_from_nodes() validates the
result against `star_idx` before trusting it. No C++ patch required.

Three sources in descending order of certainty, see resolve_owners():
the optional owner byte from doc/ext_ship_icon_owner.patch, the
rebuilt node table, and finally a per-star guess that only answers
when the star is unambiguous.
"""
import logging
import math

import pygame

from core import palette
from core import zoomtables as zt
from core.structs import ship as ship_struct

log = logging.getLogger("galaxy_map.ships")

#: Cache key prefix, kept distinct from star folders and nebula forms.
KEY_PREFIX = "ships/"

#: owner value -> asset folder. Players share one folder and differ
#: only by tint; everything else has its own artwork.
MONSTER_KINDS = {
    ship_struct.OWNER_ANTARAN:  "antaran",
    ship_struct.OWNER_GUARDIAN: "guardian",
    ship_struct.OWNER_AMOEBA:   "amoeba",
    ship_struct.OWNER_CRYSTAL:  "crystal",
    ship_struct.OWNER_DRAGON:   "dragon",
    ship_struct.OWNER_EEL:      "eel",
    ship_struct.OWNER_HYDRA:    "hydra",
}

PLAYER_KIND = "player"

#: Folders make_ship_icons.py can produce.
ALL_KINDS = (PLAYER_KIND,) + tuple(
    MONSTER_KINDS[k] for k in sorted(MONSTER_KINDS))

#: How the artwork sits inside its native footprint box.
#:   height  match the original silhouette HEIGHT. The DEFAULT, and
#:           the safe one: the orbit slots sit only (11 - zoom) px
#:           apart vertically, so height is the dimension that decides
#:           whether a four-deep stack collides.
#:   width   match the WIDTH instead. Faithful to the original
#:           silhouette only if the artwork shares its aspect ratio;
#:           taller artwork overflows top and bottom and reads as an
#:           icon a size too large.
#:   box     fit entirely inside, never overflow. Smallest result.
#:   area    match the box's AREA, not either edge. For artwork whose
#:           aspect is far from the original's — the eel is 3.3:1
#:           against a 10x9 box — width-fit leaves a sliver and
#:           height-fit a banner three times too long. Area splits the
#:           difference and keeps the visual weight of a 10x9 icon.
FIT_MODES = ("height", "width", "box", "area")
DEFAULT_FIT = "height"

#: Player colour -> tint multiplier. Same eight-entry order as
#: renderer.OWNER_COLORS and core/banner.py: red, yellow, green,
#: silver, blue, brown, purple, orange (MOX::_main_palette_player_colors).
SHIP_COLORS = {
    0: palette.col("galaxy_map", "ship_0", (214,  72,  52)),
    1: palette.col("galaxy_map", "ship_1", (232, 196,  40)),
    2: palette.col("galaxy_map", "ship_2", ( 78, 186,  76)),
    3: palette.col("galaxy_map", "ship_3", (222, 230, 238)),
    4: palette.col("galaxy_map", "ship_4", (108, 156, 232)),
    5: palette.col("galaxy_map", "ship_5", (204, 132,  84)),
    6: palette.col("galaxy_map", "ship_6", (176,  96, 204)),
    7: palette.col("galaxy_map", "ship_7", (255, 138,  20)),
}

#: A pure multiply drives the highlights straight into the hue and the
#: hull stops reading as metal. Lifting the multiplier toward white by
#: this fraction keeps the specular pixels bright while the midtones
#: still carry the player colour. 0 reproduces banner.py's behaviour.
TINT_KEEP_WHITE = 0.22

#: Drawn when a sprite is missing entirely — the pre-existing
#: behaviour, so a project without the ship assets still shows fleets.
FALLBACK_OUTLINE = palette.col("galaxy_map", "fleet_outline", (16, 16, 20))
NEUTRAL_COLOR = palette.col("galaxy_map", "fleet_neutral", (170, 170, 180))


def kind_for_owner(owner):
    """Asset folder for an owner value, or None if unknown."""
    if owner is None:
        return None
    if 0 <= owner < 8:
        return PLAYER_KIND
    return MONSTER_KINDS.get(owner)


def sprite_key(kind, step):
    return f"{KEY_PREFIX}{kind}/{step}"


def native_size(kind, zoom):
    """Native footprint in 640x480 pixels."""
    if kind == PLAYER_KIND or kind is None:
        return zt.ship_icon_dimension(zoom)
    return zt.monster_icon_dimension(kind, zoom)


# ── Owner resolution ─────────────────────────────────────

def build_node_map(ships):
    """Rebuild MOX::_ship_node's node_idx -> ship_idx mapping.

    `_ship_node` is not serialized, but it does not have to be: it is a
    pure function of `_ship[]`, which is. Transcribed from
    SHIPSTAK::Find_Ship_Stacks_ (shipstak.cpp:45).

    The part that is easy to get wrong: node numbers have NOTHING to do
    with the stacking. Both branches of the loop do the same thing —

        next_free = _next_free_node;
        _ship_node[next_free].ship_idx = i;
        _next_free_node++;

    — so node N is simply the N-th ship that was not skipped, in ship
    array order. The location/x/y/owner comparison decides which stack a
    ship joins, never which node it occupies. Reproducing the grouping
    here would be dead code.

    Skipped ships are those with `status >= 3` (shipstak.cpp:56).

    `_ship_node[].ship_idx` is written nowhere else in the source —
    checked across all 319 .cpp files — so nothing can renumber behind
    our back.
    """
    return [i for i, s in enumerate(ships)
            if s.status < ship_struct.STATUS_STACK_SKIP]


def owners_from_nodes(icons, ships):
    """Exact owner per icon via the rebuilt node table, or None.

    Returns None — for the WHOLE set, not per icon — when the mapping
    cannot be validated. The check is free and exact:
    SHIPSTAK::Ship_Stack_Star_Id_ (shipstak.cpp:25) is literally

        _ship[_ship_node[node].ship_idx].location

    and Build_Ship_Icons_ stores that value in `star_idx`. So every
    icon's star_idx must equal the raw (still encoded) location of the
    ship its node points at. One mismatch means `_ship[]` moved on
    since the last Find_Ship_Stacks_ call, and a stale map produces
    plausible, wrong colours — the worst possible outcome. All or
    nothing.
    """
    if not ships:
        return None
    node_ship = build_node_map(ships)
    out = []
    for icon in icons:
        node = getattr(icon, "node_idx", -1)
        if not 0 <= node < len(node_ship):
            return None
        s = ships[node_ship[node]]
        if s.location != getattr(icon, "star_idx", None):
            return None
        out.append(s.owner)
    return out


def resolve_owners(icons, ships):
    """Owner per icon. Returns a list of int or None, one per icon.

    Three sources, in descending order of certainty:

      1. The per-icon owner byte, if orion2re carries the optional
         doc/ext_ship_icon_owner.patch. Ground truth, no reconstruction.
      2. owners_from_nodes() — the rebuilt node table, validated
         against star_idx. This is the normal path and needs no patch.
      3. A last-resort guess from the ships parked at the icon's star,
         used only where exactly one owner is present there.

    An icon that survives all three stays None and renders neutral. A
    grey fleet is a visible gap; a wrongly coloured one is a lie.
    """
    owners = [getattr(icon, "owner", None) for icon in icons]
    if all(o is not None for o in owners):
        return owners

    exact = owners_from_nodes(icons, ships or [])
    if exact is not None:
        return [o if o is not None else e for o, e in zip(owners, exact)]

    by_star = {}
    for s in (ships or []):
        if s.status >= ship_struct.STATUS_STACK_SKIP:
            continue
        star = ship_struct.absolute_location(s.location)
        if star < 0:
            continue
        by_star.setdefault(star, set()).add(s.owner)

    for i, icon in enumerate(icons):
        if owners[i] is not None:
            continue
        star = ship_struct.absolute_location(
            getattr(icon, "star_idx", -1))
        seen = by_star.get(star)
        if seen and len(seen) == 1:
            owners[i] = next(iter(seen))
    return owners


# ── Tinting ──────────────────────────────────────────────

def _lift(color, keep=TINT_KEEP_WHITE):
    return tuple(int(round(c + (255 - c) * keep)) for c in color[:3])


class TintCache:
    """Tinted copies of the greyscale player sprite, per (key, colour).

    Separate from renderer.SpriteCache because the key needs a colour
    and because clearing on resize must drop tinted variants too —
    they are built from already-scaled surfaces.
    """

    def __init__(self):
        self._tinted = {}

    def get(self, base, cache_key, color_idx):
        key = (cache_key, base.get_width(), base.get_height(), color_idx)
        hit = self._tinted.get(key)
        if hit is not None:
            return hit
        color = SHIP_COLORS.get(color_idx)
        if color is None:
            return base
        out = base.copy()
        out.fill(_lift(color), special_flags=pygame.BLEND_RGB_MULT)
        self._tinted[key] = out
        return out

    def clear(self):
        self._tinted.clear()


# ── Rendering ────────────────────────────────────────────

def _fit_size(sprite, box_w, box_h, mode):
    sw, sh = sprite.get_size()
    if sw <= 0 or sh <= 0:
        return box_w, box_h
    ratio = sh / sw
    if mode == "width":
        w = box_w
        h = max(1, int(round(w * ratio)))
    elif mode == "box":
        f = min(box_w / sw, box_h / sh)
        w = max(1, int(round(sw * f)))
        h = max(1, int(round(sh * f)))
    elif mode == "area":
        # Same drawn area as the native box, aspect preserved:
        # w * h = box_w * box_h with h = w * ratio.
        w = max(1, int(round(math.sqrt(box_w * box_h / ratio))))
        h = max(1, int(round(w * ratio)))
    else:                                    # "height", the default
        h = box_h
        w = max(1, int(round(h / ratio)))
    return w, h


def _resolve_sprite(cache, kind, step):
    """Sprite for (kind, step) with two documented fallbacks.

    A missing step inside an existing kind falls back to step 0 — an
    artist adding a hand-drawn 2.png should not have to ship all four.
    A missing kind falls back to the player ship, so a monster the
    project has no artwork for is still visible and still in the right
    place.
    """
    key = sprite_key(kind, step)
    if cache.has(key):
        return key
    key0 = sprite_key(kind, 0)
    if cache.has(key0):
        return key0
    if kind != PLAYER_KIND:
        return _resolve_sprite(cache, PLAYER_KIND, step)
    return None


def kind_config(cfg, kind):
    """(fit, scale) for one kind: the per-kind override, else global.

    Per-kind exists because artwork aspect ratios differ wildly. One
    global mode that suits the ship makes the eel a sliver, and the
    other way round. layout.json:

        "ship_icons": {
          "fit": "height", "scale": 1.0,
          "kinds": { "eel": { "fit": "area" } }
        }
    """
    cfg = cfg or {}
    per = (cfg.get("kinds") or {}).get(kind) or {}
    fit = per.get("fit") or cfg.get("fit") or DEFAULT_FIT
    if fit not in FIT_MODES:
        log.warning("Unknown ship icon fit %r for %s, using %s",
                    fit, kind, DEFAULT_FIT)
        fit = DEFAULT_FIT
    scale = per.get("scale", cfg.get("scale", 1.0))
    try:
        scale = float(scale)
    except (TypeError, ValueError):
        scale = 1.0
    return fit, scale


def icon_screen_pos(icon, ctx, anchor, box_w, box_h):
    """Top-left HD position for a ship icon.

    Coupled view (anchor is None): s_ship_icon.x/y are the game's
    finished 640x480 coordinates and map straight into the box —
    decision 24, unchanged.

    Decoupled view: those coordinates were computed for the GAME's
    slice, not ours, so they are re-anchored rather than re-derived:

      * ships in transit or in a wormhole draw at the ship's own
        galaxy x/y — exact, and better than any back-transform;
      * orbiting ships draw at their star's HD position plus the
        game-computed slot offset (icon minus star, both in the
        game's native pixels — exact integers). The offset is scaled
        by ctx.px times the ratio of star sprite sizes between the
        HD zoom step and the game's, so the slot hugs the star sprite
        we actually drew instead of the one the game drew.

    The slot GEOMETRY still comes from Build_Ship_Icons_ — which
    ship sits in which slot, and where that slot is relative to the
    star. Only the anchor changes frame.
    """
    from core import mapcoords as mc

    view = ctx.view
    if anchor is None:
        return (view.off_x + (icon.x - mc.MAP_LEFT) * view.scale,
                view.off_y + (icon.y - mc.MAP_TOP) * view.scale)

    game_state, stars, ship, game_zoom = anchor.resolve(icon)

    if ship is not None and ship_struct.absolute_location(
            ship.location) != ship.location:
        # In transit / in a wormhole: the ship's own coordinates.
        return _centred(view.to_screen(ship.x, ship.y), box_w, box_h)

    star_idx = ship_struct.absolute_location(
        getattr(icon, "star_idx", -1))
    if stars and 0 <= star_idx < len(stars):
        star = stars[star_idx]
        snx, sny = mc.galaxy_to_native(star.x, star.y, game_state)
        game_ms = getattr(game_state, "map_scale", 0) or mc.SCALE_UNIT
        ratio = (zt.star_dimension(0, ctx.zoom, ctx.num_stars,
                                   ctx.map_scale)
                 / zt.star_dimension(0, game_zoom, ctx.num_stars,
                                     game_ms))
        sx, sy = view.to_screen(star.x, star.y)
        return (sx + (icon.x - snx) * ctx.px * ratio,
                sy + (icon.y - sny) * ctx.px * ratio)

    # No star, no ship — back-transform through the game's slice.
    gx, gy = mc.native_to_galaxy(icon.x, icon.y, game_state)
    return view.to_screen(gx, gy)


def _centred(pos, box_w, box_h):
    """Centre point -> top-left, matching the icon.x/y convention."""
    return (pos[0] - box_w / 2.0, pos[1] - box_h / 2.0)


class IconAnchor:
    """Everything icon_screen_pos needs about the game's own view."""

    def __init__(self, game_state, stars, ships, game_zoom):
        self.game_state = game_state
        self.stars = stars or []
        self.game_zoom = game_zoom
        self._node_ship = build_node_map(ships or [])
        self._ships = ships or []

    def resolve(self, icon):
        ship = None
        node = getattr(icon, "node_idx", -1)
        if 0 <= node < len(self._node_ship):
            candidate = self._ships[self._node_ship[node]]
            if candidate.location == getattr(icon, "star_idx", None):
                ship = candidate       # same validation as the owners
        return self.game_state, self.stars, ship, self.game_zoom


def render(surface, ctx, icons, players, cache, tints,
           cfg=None, ships=None, anchor=None):
    """Draw every placed ship icon.

    `players` supplies the `color` field per player index; the tint
    keys on that, not on the player index, so two players can never
    end up sharing a colour just because they sit next to each other
    in the array.
    """
    if not icons:
        return
    px = ctx.px
    owners = resolve_owners(icons, ships or [])

    # Back to front, exactly as MAINSCR::Draw_Ship_Icons_ does
    # (`for i = _ship_icon_count - 1; i >= 0; --i`). The order is not
    # cosmetic: Build_Ship_Icons_ puts the local player's stack in
    # slot 0, so drawing backwards is what keeps your own fleet on top
    # of a foreign one parked at the same star.
    for icon, owner in reversed(list(zip(icons, owners))):
        if icon.x < 0 or icon.y < 0:
            continue

        kind = kind_for_owner(owner)
        fit, scale = kind_config(cfg, kind or PLAYER_KIND)
        nw, nh = native_size(kind, ctx.zoom)
        box_w = max(2, int(round(nw * px * scale)))
        box_h = max(2, int(round(nh * px * scale)))

        # Top-left anchor, then centre the artwork on the box so a
        # sprite whose aspect differs from the original grows evenly
        # instead of hanging off one edge.
        left, top = icon_screen_pos(icon, ctx, anchor, box_w, box_h)
        cx = left + box_w / 2.0
        cy = top + box_h / 2.0

        key = _resolve_sprite(cache, kind or PLAYER_KIND, ctx.zoom)
        if key is None:
            _draw_fallback(surface, cx, cy, box_w, box_h, owner)
            continue

        base = cache.base(key)
        w, h = _fit_size(base, box_w, box_h, fit)
        sprite = cache.scaled(key, w)
        if sprite is None:
            _draw_fallback(surface, cx, cy, box_w, box_h, owner)
            continue
        if h != sprite.get_height():
            h = sprite.get_height()

        if kind == PLAYER_KIND:
            color_idx = _player_color(players, owner)
            if color_idx is not None:
                sprite = tints.get(sprite, key, color_idx)

        surface.blit(sprite, (int(round(cx - sprite.get_width() / 2.0)),
                              int(round(cy - sprite.get_height() / 2.0))))


def _player_color(players, owner):
    """The player's `color` field (0..7), or None when unavailable.

    Falls back to the player INDEX only if the record has no color —
    in a stock game the two agree for player 0 and diverge afterwards,
    so this is a last resort, not a shortcut.
    """
    if owner is None or not (0 <= owner < 8):
        return None
    if players and owner < len(players):
        color = getattr(players[owner], "color", None)
        if color is not None and 0 <= color < 8:
            return int(color)
    return owner


def _draw_fallback(surface, cx, cy, w, h, owner):
    """Pre-asset behaviour: a flat marker, never nothing."""
    color = NEUTRAL_COLOR
    if owner is not None and 0 <= owner < 8:
        color = SHIP_COLORS.get(owner, NEUTRAL_COLOR)
    rect = pygame.Rect(int(cx - w / 2), int(cy - h / 2), w, h)
    pygame.draw.rect(surface, color[:3], rect)
    pygame.draw.rect(surface, FALLBACK_OUTLINE[:3], rect, 1)
