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
node_idx -> MOX::_ship_node[] -> MOX::_ship[].owner, and the node table
comes off the wire: open fix 20 sends `_ship_node[].ship_idx` per node
(`wire_nodes`). It is NOT rebuilt from `_ship[]`. Until brief 119 it
was, on the belief that node n is the n-th ship with status < 3 — true
of `SHIPSTAK::Find_Ship_Stacks_` alone, false after it:
`Sort_Ships_In_Stack_` (shipstak.cpp:261-278) qsorts every stack's ships
by type and writes `ship_idx` back along the chain, and qsort is not
stable. The owners only came out right because every ship of a stack has
the same owner; the fleet box's per-ship selection did not (run 118).

Three sources in descending order of certainty, see resolve_owners():
the owner byte open fix 20 carries, the wire's node table validated
against `star_idx`, and finally a per-star guess that only answers when
the star is unambiguous.
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
#: The values are the skin's (`galaxy_map` ship_0..7, colors.json) with NO
#: code default — decision 14; moved out of literals here on 14 September
#: 2026, the tinted sprites compared byte for byte.
SHIP_COLORS = {i: palette.require("galaxy_map", f"ship_{i}") for i in range(8)}

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


# ── Which snapshot's icons the map may believe ───────────

#: SCREEN_MAIN — the only screen whose snapshot describes the galaxy
#: map. The same number as GalaxyMapScreen.GAME_SCREEN_ID.
MAP_SCREEN_ID = 0

#: THE SNAPSHOT FIELDS ANOTHER SCREEN REWRITES WHILE IT IS UP, each with
#: the line that writes it. ONE list: a field is added here and nowhere
#: else, and the smoke test iterates this dict rather than naming a
#: field of its own.
#:
#: Both entries belong to the Fleets screen AND to the Officers screen,
#: which is why the rule is "screen 0 only" and not "not screen 4":
#: `Set_Fltscrn_Small_Ship_Icon_XYs_` is called from flt1.cpp:531 and
#: :711 and from officer.cpp:905, and both screens save the map scale on
#: entry and put it back on exit. A list of guilty screens would have
#: missed screen 29 on the day it was written.
GATED_FIELDS = {
    "ship_icons": (
        "FLT::Set_Fltscrn_Small_Ship_Icon_XYs_ overwrites x/y with "
        "FLEET-INSET coordinates (flt.cpp:54-55) and "
        "FLT2::Add_Fltscrn_Small_Icon_Fields_ overwrites stack_id with "
        "the id of the hidden field it adds for that icon "
        "(flt2.cpp:34). Serialized at ext_api.cpp:165-167; only "
        "MAINSCR::Main_Screen_ puts them back "
        "(mainscr_main.cpp:314-315)."),
    "map_scale": (
        "FLT::Set_Fltscrn_Small_Ship_Icon_XYs_ sets _cur_map_scale = "
        "_max_map_scale so the inset covers the whole galaxy "
        "(flt.cpp:14). FLT1::Fleet_Screen_ saves it on entry and "
        "restores it on exit (flt1.cpp:487, :835), and "
        "OFFICER::Officer_Screen_ does the same (officer.cpp:857, "
        ":1191). Serialized at ext_api.cpp:111."),
}

#: What a gated field holds before any screen-0 snapshot has arrived:
#: `core.game_state.GameState`'s own starting values. An empty map is a
#: state every renderer here already handles; another screen's map is
#: not. Copied per gate, never shared.
BLANK_FIELDS = {"ship_icons": [], "map_scale": 0}

#: NOT GATED, and each for a reason that had to be read rather than
#: assumed:
#:   map_x / map_y  `MOX::_cur_map_x/_cur_map_y` are written only by
#:                  savegame.cpp:1514-1515, mainscr.cpp and
#:                  mainscr_main.cpp — nothing under flt*.cpp or
#:                  officer.cpp touches them, so the map ORIGIN is
#:                  already the map's.
#:   fleet_selection FSEL's stack is `_fleet_box_ship_stack`, written
#:                  once on EXIT (flt1.cpp:827) and never during the
#:                  screen, and `_ship_node[].selected` is not touched
#:                  either: the Fleets screen keeps its own selection in
#:                  `_fltscrn_big_icon[].selected` (flt1.cpp:429) and
#:                  open fix 28 writes that array, not the node table.
#:   ships / stars / colonies  SCRAP, a move order and a relocation are
#:                  real changes to the game and MUST reach the map.
#:                  A screen's own display state is what is gated here,
#:                  never a thing the player did.


class _GatedSnapshot:
    """A snapshot whose gated fields are the map's; everything else is
    the game's, live.

    Same shape as `viewctl._ViewProxy` and for the same reason: a few
    attributes are ours and the rest must fall through. A COPY of the
    state would have been simpler and is wrong — `core/game_client.py`
    sets `fields`, `framebuffer` and `save_slots` onto the snapshot
    object after `parse_state` built it, and a copy would freeze the
    field list, which is the thing that decides what may be sent
    (decision 59, work order 128 C).
    """

    def __init__(self, state, held):
        self._state = state
        self.__dict__.update(held)

    def __getattr__(self, name):
        return getattr(self._state, name)


class ScreenStateGate:
    """State a screen rewrites for itself is that screen's, not the
    map's: every field of `GATED_FIELDS` is adopted from screen 0 and
    from nowhere else.

    Nothing about the records says which space they are in. They parse,
    they are in range, and a map drawn from them puts every stack at an
    inset position at a scale meant for a 305x182 box — with every
    other number on screen still correct, which is this project's worst
    failure shape (decision 35). Mixing HALF of them is the same fault
    one layer down: work order 135 gated the icons and left the scale,
    so the map held screen-0 icons against a screen-4 scale, which is
    two reference frames in one picture.

    THE GATE IS HERE, at the one point where a snapshot becomes the
    map's state, and not at each reader: `render_fleets`, `maplines`,
    `mapeta`, `mapinput`/`mapclick`, `boxmodel.remember` and the two
    map views all read the screen's `_state` and therefore all get the
    same answer. Work orders 135 B and 136 B; the hazard is question 15
    of `doc/fleet_screen_reading.md`.

    **`viewctl.park_game` is deliberately NOT behind it.** Parking
    drives the GAME's own zoom and stops on an absolute target read off
    the snapshot, so a frozen scale would be a target it can never
    reach. It is handed the raw snapshot in `GalaxyMapScreen.update`
    and it already refuses unless the game reports screen 0 with this
    screen's field list; a smoke check holds both halves.

    On screen 0 the snapshot is handed back untouched, so the normal
    case costs one comparison and no wrapper.
    """

    def __init__(self):
        self.held = dict(BLANK_FIELDS)

    def reset(self):
        """Forget what was held — a fresh entry to the screen has
        nothing, and an empty map is honest where a stale one is not."""
        self.held = dict(BLANK_FIELDS)

    def state(self, game_state):
        """The snapshot as the galaxy map may read it."""
        if getattr(game_state, "current_screen",
                   MAP_SCREEN_ID) != MAP_SCREEN_ID:
            return _GatedSnapshot(game_state, self.held)
        for _name in GATED_FIELDS:
            _value = getattr(game_state, _name, None)
            self.held[_name] = (BLANK_FIELDS[_name] if _value is None
                                else _value)
        return game_state


# ── Owner resolution ─────────────────────────────────────

def wire_nodes(state):
    """`MOX::_ship_node[n].ship_idx` for every node in use, from open fix
    20's FSEL block (core/game_state.py), or None without it."""
    sel = getattr(state, "fleet_selection", None)
    return list(sel["ships"]) if sel else None


def owners_from_nodes(icons, ships, nodes):
    """Exact owner per icon via the wire's node table, or None.

    Returns None — for the WHOLE set, not per icon — when there is no
    table or it cannot be validated. The check is free and exact:
    SHIPSTAK::Ship_Stack_Star_Id_ (shipstak.cpp:25) is literally

        _ship[_ship_node[node].ship_idx].location

    and Build_Ship_Icons_ stores that value in `star_idx`. So every
    icon's star_idx must equal the raw (still encoded) location of the
    ship its node points at. One mismatch means the table and `_ship[]`
    do not describe the same moment, and a stale map produces
    plausible, wrong colours — the worst possible outcome. All or
    nothing.
    """
    if not ships or nodes is None:
        return None
    out = []
    for icon in icons:
        node = getattr(icon, "node_idx", -1)
        if not 0 <= node < len(nodes) or not 0 <= nodes[node] < len(ships):
            return None
        s = ships[nodes[node]]
        if s.location != getattr(icon, "star_idx", None):
            return None
        out.append(s.owner)
    return out


def resolve_owners(icons, ships, nodes=None):
    """Owner per icon. Returns a list of int or None, one per icon.

    Three sources, in descending order of certainty:

      1. The per-icon owner byte open fix 20 carries (block 1, once
         doc/ext_ship_icon_owner.patch). Ground truth.
      2. owners_from_nodes() — the wire's node table (`wire_nodes`),
         validated against star_idx.
      3. A last-resort guess from the ships parked at the icon's star,
         used only where exactly one owner is present there.

    An icon that survives all three stays None and renders neutral. A
    grey fleet is a visible gap; a wrongly coloured one is a lie.
    """
    owners = [getattr(icon, "owner", None) for icon in icons]
    if all(o is not None for o in owners):
        return owners

    exact = owners_from_nodes(icons, ships or [], nodes)
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

    **DEVIATION, kept on purpose (Data, 14 September 2026).** Today that
    is the AMOEBA and the ANTARAN: no HD master exists for either, and
    both draw as the untinted grey player ship in their own footprint.
    An invented picture, and marked as one — but on the map a monster
    that vanished would be a gap against the original, which draws it,
    so the stand-in stays until the artwork arrives. The Planets panel
    decides the other way (an empty sprite box is an understandable
    state there). The smoke test holds the set of kinds that reach this
    branch to exactly {amoeba, antaran}: a new master, or a lost one,
    fails it.
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

    return _star_anchored(icon, icon.x, icon.y, ctx, anchor)


def _star_anchored(icon, nx, ny, ctx, anchor):
    """A native point of an orbiting icon, re-anchored on its star: the
    star's HD position plus the game-computed offset, scaled by ctx.px and
    the star sprite ratio (see icon_screen_pos). Without a star, the
    point is back-transformed through the game's slice."""
    from core import mapcoords as mc

    view = ctx.view
    game_state, stars, _, game_zoom = anchor.resolve(icon)
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
        return (sx + (nx - snx) * ctx.px * ratio,
                sy + (ny - sny) * ctx.px * ratio)

    # No star, no ship — back-transform through the game's slice.
    gx, gy = mc.native_to_galaxy(nx, ny, game_state)
    return view.to_screen(gx, gy)


def anchored_point(icon, nx, ny, ctx, anchor):
    """HD position of a native point that belongs to a ship icon — the
    destination line's start (maplines) — placed so it keeps its native
    offset from the icon HD actually draws.

    Coupled view: the native point maps straight, as the icon does. In
    transit (decoupled): HD centres the icon on the ship's own galaxy
    position, the game centres it on half the header of BUFFER0.LBX entry
    205 + zoom (`Get_Ship_Icon_Coords_In_Space_`, ships.cpp:516-531), so
    the point keeps its offset from that centre. Orbiting: re-anchored on
    the star like the icon itself.
    """
    from core import mapcoords as mc

    view = ctx.view
    if anchor is None:
        return (view.off_x + (nx - mc.MAP_LEFT) * view.scale,
                view.off_y + (ny - mc.MAP_TOP) * view.scale)
    _, _, ship, game_zoom = anchor.resolve(icon)
    if ship is not None and ship_struct.absolute_location(
            ship.location) != ship.location:
        cw, ch = zt.ship_icon_header_dimension(game_zoom)
        hx, hy = view.to_screen(ship.x, ship.y)
        return (hx + (nx - icon.x - (cw >> 1)) * ctx.px,
                hy + (ny - icon.y - (ch >> 1)) * ctx.px)
    return _star_anchored(icon, nx, ny, ctx, anchor)


def icon_box(icon, owner, ctx, anchor=None, cfg=None):
    """(left, top, width, height) in HD pixels — the ONE rectangle an icon
    has: `render` draws into it and `mapclick.icon_at` hit-tests it
    (decision 5)."""
    kind = kind_for_owner(owner)
    _, scale = kind_config(cfg, kind or PLAYER_KIND)
    nw, nh = native_size(kind, ctx.zoom)
    box_w = max(2, int(round(nw * ctx.px * scale)))
    box_h = max(2, int(round(nh * ctx.px * scale)))
    left, top = icon_screen_pos(icon, ctx, anchor, box_w, box_h)
    return left, top, box_w, box_h


def _centred(pos, box_w, box_h):
    """Centre point -> top-left, matching the icon.x/y convention."""
    return (pos[0] - box_w / 2.0, pos[1] - box_h / 2.0)


class IconAnchor:
    """Everything icon_screen_pos needs about the game's own view."""

    def __init__(self, game_state, stars, ships, game_zoom):
        self.game_state = game_state
        self.stars = stars or []
        self.game_zoom = game_zoom
        self._nodes = wire_nodes(game_state) or []
        self._ships = ships or []

    def resolve(self, icon):
        ship = None
        node = getattr(icon, "node_idx", -1)
        if 0 <= node < len(self._nodes) \
                and 0 <= self._nodes[node] < len(self._ships):
            candidate = self._ships[self._nodes[node]]
            if candidate.location == getattr(icon, "star_idx", None):
                ship = candidate       # same validation as the owners
        return self.game_state, self.stars, ship, self.game_zoom


def render(surface, ctx, icons, players, cache, tints,
           cfg=None, ships=None, anchor=None, nodes=None):
    """Draw every placed ship icon.

    `players` supplies the `color` field per player index; the tint
    keys on that, not on the player index, so two players can never
    end up sharing a colour just because they sit next to each other
    in the array. `nodes` is `wire_nodes(state)`.
    """
    if not icons:
        return
    owners = resolve_owners(icons, ships or [], nodes)

    # Back to front, exactly as MAINSCR::Draw_Ship_Icons_ does
    # (`for i = _ship_icon_count - 1; i >= 0; --i`). The order is not
    # cosmetic: Build_Ship_Icons_ puts the local player's stack in
    # slot 0, so drawing backwards is what keeps your own fleet on top
    # of a foreign one parked at the same star.
    for icon, owner in reversed(list(zip(icons, owners))):
        if icon.x < 0 or icon.y < 0:
            continue

        kind = kind_for_owner(owner)
        fit, _ = kind_config(cfg, kind or PLAYER_KIND)

        # Top-left anchor, then centre the artwork on the box so a
        # sprite whose aspect differs from the original grows evenly
        # instead of hanging off one edge.
        left, top, box_w, box_h = icon_box(icon, owner, ctx, anchor, cfg)
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
