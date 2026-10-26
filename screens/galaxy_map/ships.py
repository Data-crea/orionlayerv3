"""Galaxy map ship and monster icons.

WHAT ORION2RE GIVES US
----------------------
`s_ship_icon.x/y` are already 640x480 SCREEN coordinates with the
icon's TOP-LEFT as the anchor — orion2re fills them in
SHIPS::Set_Ship_Icon_XYs_ / MAINSCR::Draw_Ship_Icons_ using the orbit
slot geometry of Get_XYs_For_Orbiting_Ships_. The coupled view draws
them as they are; HD's own zoom stands on a rung the game did not
compute them for, so there the slot geometry is transcribed
(`orbit_slot_offset`, work order 310) while the slot itself stays the
game's.

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
SHIP_COLORS = {}


@palette.on_preset
def _bind_ship_colours():
    """HD EXTENSION `preset_at_once` (work order 312): the Player colours
    list applies at once, so the tints are bound again in place and every
    `TintCache` drops what it made under the old table (`follow`).
    Registered in `layout.json` `_markings`."""
    SHIP_COLORS.update({i: palette.require("galaxy_map", f"ship_{i}")
                        for i in range(8)})


_bind_ship_colours()

#: A pure multiply drives the highlights straight into the hue and the
#: hull stops reading as metal. Lifting the multiplier toward white by
#: this fraction keeps the specular pixels bright while the midtones
#: still carry the player colour. 0 reproduces banner.py's behaviour.
TINT_KEEP_WHITE = 0.22

#: Drawn when a sprite is missing entirely — the pre-existing
#: behaviour, so a project without the ship assets still shows fleets.
FALLBACK_OUTLINE = palette.col("galaxy_map", "fleet_outline", (16, 16, 20))
NEUTRAL_COLOR = palette.col("galaxy_map", "fleet_neutral", (170, 170, 180))


#: HD EXTENSION `monster_fixed_size` (Data, 25 October 2026): a monster is
#: drawn at the footprint, inset and picture of zoom 0, the largest, at
#: every zoom; zoomed out it was too small to make out. The original steps
#: it down with the zoom (MONSTER_ICON_DIM). Orbit slots stay on the zoom.
MONSTER_ZOOM = 0
#: HD EXTENSION `monster_fixed_size`: and 20 % smaller than that (Data,
#: 25 October 2026), hit box included.
MONSTER_SHRINK = 0.8


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
    of `dev:doc/fleet_screen_reading.md`.

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

      1. The per-icon owner byte open fix 20 carries (block 1 of
         doc/ext_fleet_selection.patch). Ground truth.
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
        self._gen = palette.generation()
        # the stacks' ship pictures are made at the box's size too, so they
        # go with the tinted sprites (HD EXTENSION `strongest_ship_icon`)
        from screens.galaxy_map import shippics
        self.pictures = shippics.ShipPictures()

    def follow(self):
        """Drop the tints and pictures made under an older colour table
        (`palette.apply_preset`): one integer compared per call."""
        if self._gen != palette.generation():
            self._gen = palette.generation()
            self.clear()

    def get(self, base, cache_key, color_idx):
        self.follow()
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
        self.pictures.clear()


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


def icon_screen_pos(icon, ctx, anchor, box_w, box_h, owner=None,
                    inset=(0, 0)):
    """Top-left HD position of a ship icon's box. `inset` is where the
    drawn pixels start inside the sprite's header box, native px (a
    monster's, zoomtables.monster_icon_inset).

    Coupled view (anchor is None): s_ship_icon.x/y are the game's
    finished 640x480 coordinates and map straight into the box —
    decision 24, unchanged.

    Decoupled view: those coordinates were computed for the GAME's
    slice and zoom, not ours, so they are re-derived at HD's own rung:

      * ships in transit (status 1) or in slot 5 draw centred on the
        ship's own galaxy x/y — exact, and better than any
        back-transform. DEVIATION `slot_five`: for a slot-5 ship that
        is NOT in transit the original reads `Get_Scaled_Value_(x)`
        without the map's origin or the 21 px edge (ships.cpp:248-250);
        HD keeps the ship's own place (`layout.json` `_markings`);
      * every other ship sits in its orbit slot, TRANSCRIPTION
        `orbit_slots` (`orbit_slot_offset`), at the star the ship
        stands on — whatever its location says, so a fresh order
        (location 10000 or 20000 + star) keeps its slot as in the
        original (live 309: the Scout at Zin fell onto the star).

    Which ship sits in which slot is Build_Ship_Icons_'s (`stack_slot`,
    decision 24); only the geometry is redone.
    """
    from core import mapcoords as mc

    view = ctx.view
    dx, dy = inset[0] * ctx.px, inset[1] * ctx.px
    if anchor is None:
        return (view.off_x + (icon.x - mc.MAP_LEFT) * view.scale + dx,
                view.off_y + (icon.y - mc.MAP_TOP) * view.scale + dy)

    _, _, ship, _ = anchor.resolve(icon)
    if _in_space(icon, ship) and owner is not None and owner >= 8 and \
            getattr(ship, "status", None) == ship_struct.STATUS_IN_TRANSIT:
        # TRANSCRIPTION `monster_in_space`: the sprite's corner is the
        # ship's point less HALF THE PLAYER ICON's header, BUFFER0.LBX
        # 205 + zoom (`Get_Ship_Icon_Coords_In_Space_`, ships.cpp:514-531),
        # whatever sprite is drawn there; the drawn pixels start at the
        # monster's own inset (`layout.json` `_markings`).
        hw, hh = zt.ship_icon_header_dimension(ctx.zoom)
        cx, cy = view.to_screen(ship.x, ship.y)
        return (cx - (hw >> 1) * ctx.px + dx, cy - (hh >> 1) * ctx.px + dy)
    if _in_space(icon, ship):
        return _centred(view.to_screen(ship.x, ship.y), box_w, box_h)

    pos = _orbit_slot_pos(icon, ctx, anchor, owner)
    if pos is None:
        pos = _star_anchored(icon, icon.x, icon.y, ctx, anchor)
    return pos[0] + dx, pos[1] + dy


def _in_space(icon, ship):
    """`Get_Ship_Icon_Coords_`'s first test (status 1, ships.cpp:211) and
    its slot 5 (:248): the icon is placed off the ship, not off a star."""
    if ship is None:
        return False
    return (getattr(ship, "status", None) == ship_struct.STATUS_IN_TRANSIT
            or getattr(icon, "stack_slot", -1) == 5)


def sprite_header_width(owner, zoom, players=None):
    """Width of the sprite `Get_Ship_Icon_Pict_Seg_(owner, 0)` returns at
    `zoom` (ships.cpp:337-397): a player's own colour, entry index
    3 - zoom; the Antaran's and each monster's from their own table."""
    if owner is not None and 0 <= owner < 8:
        return zt.ship_icon_header_dimension_for_colour(
            _player_color(players, owner), 3 - zoom)[0]
    dim = zt.monster_icon_header_dimension(MONSTER_KINDS.get(owner), zoom)
    if dim is None:
        return zt.ship_icon_header_dimension(3 - zoom)[0]
    return dim[0]


def orbit_slot_offset(slot, owner, zoom, star_dim, header_w, rung_scale):
    """TRANSCRIPTION `orbit_slots`: the icon's top-left in native px
    relative to the star's draw point, for slot 0..4; None otherwise
    (`layout.json` `_markings`).

    `SHIPS::Get_XYs_For_Orbiting_Ships_` (ships.cpp:289-326, v2 288-325
    the same) with `star_size` = the star's own
    `Map_Scale_Star_Size_To_Zoom_Level_` (harold.cpp:1066-1073) and
    `width` = the owner's sprite header, and the slot switch of
    `Get_Ship_Icon_Coords_` (ships.cpp:222-252): slot 0 right of the
    star, slot 1 left, 2..4 below slot 1 by 11 - zoom, one pixel
    further left; slot 1 two pixels left again for an owner above 9 at
    map scale 10 or 15 (:231-233). C division of positive values.
    """
    zoom_offset = 1 - zoom
    local = -(star_dim // 2)
    half_w = header_w // 2
    if slot == 0:
        return (zoom_offset - half_w + local + star_dim,
                local + zoom_offset - 1)
    x2 = local - half_w - zoom_offset + 2
    y2 = local + zoom_offset - 2
    if slot == 1:
        if owner is not None and owner > 9 and rung_scale in (10, 15):
            x2 -= 2
        return (x2, y2)
    if slot in (2, 3, 4):
        return (x2 - 1, y2 + (min(slot - 2, 2) + 1) * zt.orbit_stack_step(zoom))
    return None


def _orbit_slot_pos(icon, ctx, anchor, owner=None):
    """HD top-left of the sprite's header box in its orbit slot at HD's
    own zoom, or None when star, owner or slot is unknown. The star is
    `XY_To_Star_Id_(ship.x, ship.y)` (ships.cpp:209, harold.cpp:780-788),
    else the icon's own star."""
    _, stars, ship, _ = anchor.resolve(icon)
    if ship is not None:
        owner = ship.owner
    if owner is None or not stars:
        return None
    star = None
    if ship is not None:
        star = next((s for s in stars
                     if s.x == ship.x and s.y == ship.y), None)
    if star is None:
        idx = ship_struct.absolute_location(getattr(icon, "star_idx", -1))
        star = stars[idx] if 0 <= idx < len(stars) else None
    if star is None:
        return None
    off = orbit_slot_offset(
        getattr(icon, "stack_slot", -1), owner, ctx.zoom,
        zt.star_dimension(star.size, ctx.zoom, ctx.num_stars, ctx.map_scale),
        sprite_header_width(owner, ctx.zoom, anchor.players),
        zt.hd_rung(ctx.map_scale, ctx.max_zoom, ctx.num_stars,
                   ctx.max_map_scale))
    if off is None:
        return None
    sx, sy = ctx.view.to_screen(star.x, star.y)
    return sx + off[0] * ctx.px, sy + off[1] * ctx.px


def _star_anchored(icon, nx, ny, ctx, anchor):
    """The FALLBACK for an icon `_orbit_slot_pos` cannot place (no owner
    known, or a slot outside 0..4 without a ship): the star's HD position
    plus the game-computed offset, scaled by ctx.px and the star sprite
    ratio. Without a star, the point is back-transformed through the
    game's slice."""
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
    if _in_space(icon, ship):
        cw, ch = zt.ship_icon_header_dimension(game_zoom)
        hx, hy = view.to_screen(ship.x, ship.y)
        return (hx + (nx - icon.x - (cw >> 1)) * ctx.px,
                hy + (ny - icon.y - (ch >> 1)) * ctx.px)
    pos = _orbit_slot_pos(icon, ctx, anchor)
    if pos is not None:
        return pos[0] + (nx - icon.x) * ctx.px, pos[1] + (ny - icon.y) * ctx.px
    return _star_anchored(icon, nx, ny, ctx, anchor)


def icon_box(icon, owner, ctx, anchor=None, cfg=None):
    """(left, top, width, height) in HD pixels — the ONE rectangle an icon
    has: `render` draws into it and `mapclick.icon_at` hit-tests it
    (decision 5)."""
    kind = kind_for_owner(owner)
    _, scale = kind_config(cfg, kind or PLAYER_KIND)
    if kind not in (None, PLAYER_KIND):
        scale *= MONSTER_SHRINK
    nw, nh = native_size(kind, ctx.zoom if kind in (None, PLAYER_KIND)
                         else MONSTER_ZOOM)
    box_w = max(2, int(round(nw * ctx.px * scale)))
    box_h = max(2, int(round(nh * ctx.px * scale)))
    inset = (zt.monster_icon_inset(kind, MONSTER_ZOOM)
             if kind not in (None, PLAYER_KIND) else (0, 0))
    left, top = icon_screen_pos(icon, ctx, anchor, box_w, box_h, owner,
                                inset)
    return left, top, box_w, box_h


def _centred(pos, box_w, box_h):
    """Centre point -> top-left, matching the icon.x/y convention."""
    return (pos[0] - box_w / 2.0, pos[1] - box_h / 2.0)


class IconAnchor:
    """Everything icon_screen_pos needs about the game's own view."""

    def __init__(self, game_state, stars, ships, game_zoom, players=None):
        self.game_state = game_state
        self.stars = stars or []
        self.game_zoom = game_zoom
        #: For the owner's colour, whose sprite width places the slot.
        self.players = players or []
        self._nodes = wire_nodes(game_state) or []
        self._ships = ships or []

    def resolve(self, icon):
        return (self.game_state, self.stars,
                head_ship(icon, self._nodes, self._ships), self.game_zoom)


def head_ship(icon, nodes, ships):
    """The ship at the icon's node (the head of its stack), or None; the
    same validation as the owners: its location is the icon's."""
    node = getattr(icon, "node_idx", -1)
    if nodes and ships and 0 <= node < len(nodes) \
            and 0 <= nodes[node] < len(ships):
        candidate = ships[nodes[node]]
        if candidate.location == getattr(icon, "star_idx", None):
            return candidate
    return None


def render(surface, ctx, icons, players, cache, tints,
           cfg=None, ships=None, anchor=None, nodes=None, me=None,
           settings=None):
    """Draw every placed ship icon.

    `players` supplies the `color` field per player index; the tint
    keys on that, not on the player index, so two players can never
    end up sharing a colour just because they sit next to each other
    in the array. `nodes` is `wire_nodes(state)`; `me` the player's
    index and `settings` the user settings, for the stack's ship picture
    (`shippics`).
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

        if kind == PLAYER_KIND:
            pic = _stack_picture(icon, owner, players, tints, ships, nodes,
                                 me, settings, box_w, box_h)
            if pic is not None:
                _blit_haloed(surface, pic, cx, cy)
                continue

        key = _resolve_sprite(
            cache, kind or PLAYER_KIND,
            ctx.zoom if kind in (None, PLAYER_KIND) else MONSTER_ZOOM)
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

        _blit_haloed(surface, sprite, cx, cy)


#: Haloed copies made so far, keyed by the sprite they came from (held, so
#: its id cannot be reused); bounded.
_HALOED = {}
HALO_KEEP = 256
#: A ship's dark glow (a light rim looked wrong on black, Data).
GLOW_COLOR = (0, 0, 8)


def haloed(sprite):
    """`sprite` with a dark glow round its silhouette,
    on a canvas grown by the glow (HD EXTENSION `map_icon_halo`, Data: ships
    and monsters must stand out from the background)."""
    hit = _HALOED.get(id(sprite))
    if hit is not None and hit[0] is sprite:
        return hit[1]
    w, h = sprite.get_size()
    g = max(2, min(4, round(min(w, h) / 10)))
    pad = g + 1
    mask = pygame.mask.from_surface(sprite, 40)
    sil = mask.to_surface(setcolor=(255, 255, 255, 255),
                          unsetcolor=(0, 0, 0, 0))

    def tinted(colour, alpha):
        t = sil.copy()
        t.fill(colour + (255,), special_flags=pygame.BLEND_RGBA_MULT)
        t.set_alpha(alpha)
        return t

    out = pygame.Surface((w + 2 * pad, h + 2 * pad), pygame.SRCALPHA, 32)
    glow = tinted(GLOW_COLOR, 80)
    for d in range(2, g + 1):
        for dx, dy in ((-d, 0), (d, 0), (0, -d), (0, d),
                       (-d, -d), (d, -d), (-d, d), (d, d)):
            out.blit(glow, (pad + dx, pad + dy))
    # only the ring: the silhouette itself is cut out, the sprite is blitted
    # on its own, first, and the ring over its edge (see `_blit_haloed`)
    out.blit(sil, (pad, pad), special_flags=pygame.BLEND_RGBA_SUB)
    if len(_HALOED) >= HALO_KEEP:
        _HALOED.clear()
    _HALOED[id(sprite)] = (sprite, out)
    return out


def _blit_haloed(surface, sprite, cx, cy):
    x = int(round(cx - sprite.get_width() / 2.0))
    y = int(round(cy - sprite.get_height() / 2.0))
    ring = haloed(sprite)
    pad = (ring.get_width() - sprite.get_width()) // 2
    # the ring is the outline round the picture, so it goes over the
    # picture's own edge pixels only where the picture is transparent
    surface.blit(sprite, (x, y))
    surface.blit(ring, (x - pad, y - pad))


def _stack_picture(icon, owner, players, tints, ships, nodes, me,
                   settings, box_w, box_h):
    """HD EXTENSION `strongest_ship_icon` (`shippics`): the picture of the
    stack's representative ship in the box `icon_box` gave, or None for
    the tinted master. The head is the node table's ship (`head_ship`),
    never a guess."""
    pictures = getattr(tints, "pictures", None)
    if pictures is None:
        return None
    if hasattr(tints, "follow"):
        tints.follow()
    head = head_ship(icon, nodes, ships)
    ship = pictures.representative(head, ships, me)
    return ship_picture(tints, ship, owner, players, me, settings,
                        box_w, box_h)


def ship_picture(tints, ship, owner, players, me, settings, box_w, box_h):
    """`ship`'s own picture (`shippics.ShipPictures.icon`) fitted into
    box_w x box_h, or None for the tinted master: the shape the builder's
    (`previous_owner`, as `Get_Ship_Id_Picture_Seg_` picks it, ken.cpp:451-
    455), the colour the owner's. One rule for the map's stack and the
    fleet box's cell (HD EXTENSION `box_ship_picture`, `boxdraw`)."""
    pictures = getattr(tints, "pictures", None)
    if pictures is None or ship is None:
        return None
    if hasattr(tints, "follow"):
        tints.follow()       # the box's cells follow a preset change too
    builder = int(ship.previous_owner)
    shape = _player_color(players, builder if 0 <= builder < 8 else owner)
    return pictures.icon(ship, _player_color(players, owner), shape, box_w,
                         box_h, settings, _player_color(players, me))


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
    # LOOK EXCEPTION picture: a ship icon's stand-in in its owner's colour
    pygame.draw.rect(surface, color[:3], rect)
    pygame.draw.rect(surface, FALLBACK_OUTLINE[:3], rect, 1)
