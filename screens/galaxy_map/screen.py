"""Galaxy Map Screen — orion2re SCREEN_MAIN (id 0).

Layout: THE HUD, decision 71 (work order 169). No frame image is drawn;
the screen is its background slot (a dark placeholder until Data's
picture arrives), the star map's own floor, and Data's HUD drawn over
it in code by `core.hud` — the title plate, the info panel, six slanted
nav buttons and the TURN action button. The boxes are written from the
HUD's measured layout by `tools/hud_boxes.py` (decision 3's successor):
  map_area        the star field, in the FREE SPACE between the title
                  plate, the bar and the panel (work order 170), and
                  stretching with the window between plate and bar
                  (`anchor_v`); the floor runs under the whole window
  sidebar         the info panel: stardate on top, five readouts
  nav_*           seven buttons mirroring the original: six along
                  the bottom (Colonies, Planets, Fleets, Leaders,
                  Races, Info) and nav_turn bottom-right; the title
                  plate doubles as the GAME menu button

**DEVIATION, and it was one before 169 too:** the original puts its
nav column on the RIGHT of the map and GAME top-left (mainscr.cpp);
HD puts the buttons in a row along the bottom and GAME in the title
plate. The click follows the box — each button activates the
original's field — so only the place differs.

**DEVIATION, work order 170: the map rectangle is not the original's
shape.** The original's map window is native (22,22)-(527,421), 506:400;
HD's is the free space left by the HUD, much wider. `mapcoords.MapView`
fits the native viewport into it, centred, and a click goes back through
the same view's `to_native`, so the click mapping follows the box by
construction — the star under the pointer is the star the game selects.

Positions come from core.mapcoords, which transcribes orion2re's
own transform rather than measuring it. Clicking a star sends an
INJECT_CLICK at the star's exact 640x480 point, so the game selects
the same system the user picked in HD even though the HD icon is
far larger than the original's handful of pixels.

Data sources, all from verified struct specs:
  stars       s_star_data       name, x/y, class, size, owner, visited
  nebulas     s_nebula          x/y/type
  fleets      s_ship_icon       already in screen space
  sidebar     s_player          bc, food, command points, freighters
"""
import logging

import pygame

from core import mapcoords as mc
from core import mouse as mouse_input
from core import palette
from core import zoomtables as zt
from core.screen_base import ScreenBase
from core.structs import nebula as nebula_struct
from core.structs import planet as planet_struct
from core.structs import player as player_struct
from core.structs import ship as ship_struct
from screens.galaxy_map import boxdraw
from screens.galaxy_map import mapboxes
from screens.galaxy_map import mapeta
from screens.galaxy_map import mapinput
from screens.galaxy_map import maplines
from screens.galaxy_map import ping as home_ping
from screens.galaxy_map import renderer as rnd
from screens.galaxy_map import ships as ship_icons
from screens.galaxy_map import viewctl
from screens.galaxy_map import starfield as sf
from screens.galaxy_map import floorlift
from screens.galaxy_map import sidebar as sb
from screens.galaxy_map import hudview

log = logging.getLogger("galaxy_map")

#: Click tolerance around a star, relative to its drawn icon width.
#: Slightly over half so the whole visible sprite is clickable.
STAR_HIT_SCALE = 0.60
#: Floor in HD pixels, so a tiny star stays reachable on a small
#: window or at maximum zoom-out.
MIN_STAR_HIT_PX = 10

#: Cache-key prefix for the sidebar readout icons, so they cannot
#: collide with a star folder or a nebula form name.
SIDEBAR_ICON_PREFIX = "sidebar_icons/"

#: Box-name prefix for the per-element sidebar boxes. Each row owns
#: sb_<row>_text and (except the stardate) sb_<row>_icon, so both are
#: draggable in the F5 editor like on every other screen.
SIDEBAR_BOX_PREFIX = "sb_"

MAP_BG = palette.col("galaxy_map", "map_background", (4, 5, 12))
STATUS_COLOR = palette.col("galaxy_map", "status", (140, 155, 190))
HOVER_COLOR = palette.col("galaxy_map", "hover_ring", (170, 200, 255))
PANEL_BG = palette.col("galaxy_map", "panel_background", (8, 11, 20))
NAV_BG = palette.col("galaxy_map", "nav_background", (10, 14, 26))
NAV_HOVER_BG = palette.col("galaxy_map", "nav_hover", (22, 34, 60))
NAV_TEXT = palette.col("galaxy_map", "nav_text", (196, 208, 236))
TITLE_COLOR = palette.col("galaxy_map", "title", (200, 210, 238))


class GalaxyMapScreen(ScreenBase):
    SCREEN_NAME = "galaxy_map"
    GAME_SCREEN_ID = 0        # SCREEN_MAIN
    USE_FRAME = False              # own frame PNG, see _render_frame_image
    FRAME_TITLE = "Game"

    def __init__(self, app):
        super().__init__(app)
        self._data = {}
        self._cache = rnd.SpriteCache()
        #: What `_load_sprites` last loaded FOR. None means "nothing
        #: yet"; see `_sprite_key` for why it is not a boolean.
        self._sprite_key_loaded = None
        self._state = None
        self._hover_star = None
        self._nebulas = []
        self._players = []
        self._ships = []
        self._tints = ship_icons.TintCache()
        self._wormholes = rnd.WormholeLayer()
        self._local = None
        self._map_bg = None         # gas clouds behind the map
        self._map_bg_scaled = None  # cover-scaled + cropped to map_area
        self._starfield = sf.StarfieldLayer()
        self._ping = home_ping.HomePing()
        self._viewctl = viewctl.ViewControl()   # decoupled HD viewport
        # State the Fleets and Officers screens rewrite for their own
        # inset is theirs, not the map's (ships.GATED_FIELDS).
        self._state_gate = ship_icons.ScreenStateGate()
        self._pan_from = None                   # right-drag anchor
        self._eta_lock = None                   # mapeta: order pending
        self._eta_cache = {}

    # ── Lifecycle ─────────────────────────────────────────

    def enter(self, game_state=None):
        super().enter(game_state)
        self._data = self.app.res.load_json(
            "screens/galaxy_map/layout.json", {}) or {}
        self._load_sprites()
        # No frame image (decision 71): `_load_frame` is not called.
        self._load_map_background()
        self._starfield.configure(self._data.get("starfield", {}))
        self._hover_star = None
        self._viewctl.reset()
        self._state_gate.reset()
        self._pan_from = None
        self.update(game_state)

    def _sprite_key(self):
        """What the loaded sprites depend on — the reload condition.

        **NOT a boolean, and that is the whole point of this method.**
        `asset_path` resolves through `res.screen_file`, so which FILE
        a name reaches depends on the active **skin** and the active
        **mods**; and `nebula_forms` and `sidebar_icons` come from
        `layout.json`, which `enter` re-reads and a mod can replace.
        A guard that only asked "loaded already?" would pin the map to
        artwork from a skin that is no longer active — a second copy
        nobody updates, in a new place.

        So the key is those four together, and `_load_sprites` reloads
        when any of them moves and at no other time.
        """
        res = self.app.res
        return (getattr(res, "skin", None),
                tuple(getattr(res, "mod_dirs", ()) or ()),
                tuple(self._data.get("nebula_forms", []) or ()),
                tuple(sorted((self._data.get("sidebar_icons", {})
                              or {}).items())))

    def _load_sprites(self, force=False):
        """Star icons, black hole and nebula shapes (mod-resolved).

        Six steps per class (`0.png`..`5.png`), indexed by
        zoom + star.size like the original. Any step a skin or mod
        does not ship falls back to the nearest legacy artwork
        (large/medium/small), so an incomplete set still renders.

        **ONCE PER SCREEN OBJECT, not once per `enter` — work order
        161.** This ran on every entry and cost **81
        `pygame.image.load` calls, 409 ms of a 432 ms `enter` at
        1920x1080**, replacing each surface in `_cache` with an
        identical one: `SpriteCache` is built in `__init__`, resize
        clears only the SCALED variants (`clear_scaled`), and nothing
        in the tree calls `SpriteCache.clear()`. Because every RETURN
        from Colonies, Planets and Fleets lands here, that was paid on
        every return and is what Data reported on 21 September 2026 as
        "bei return ist es definitiv langsamer". Measured after:
        426.7 ms -> 44.2 ms, and the rendered frame byte-identical.

        The reload condition is `_sprite_key`, which is about the skin
        and the mods rather than about time.

        **`force=True` reloads regardless**, and it has exactly one
        caller: the nebula check, which puts a flat test surface into
        `_cache` in place of the real artwork and has to put the real
        artwork back. Without the flag that restore became a silent
        no-op and every later check would have rendered the test
        surface — which is why the parameter exists rather than the
        check reaching in and clearing `_sprite_key_loaded` itself.
        """
        # `want_key`, not `key`: the sidebar loop below binds `key` to
        # each icon name, and the first version of this guard stored
        # the last icon name instead of the key. It never matched, so
        # the reload never stopped — caught by the load counter in the
        # same run, which is why that counter is now a smoke check.
        want_key = self._sprite_key()
        if not force and want_key == self._sprite_key_loaded:
            return
        for folder in rnd.CLASS_DIRS.values():
            for step in range(rnd.STEP_COUNT):
                path = self.asset_path("assets", "stars", folder,
                                       f"{step}.png")
                if path is None:
                    legacy = rnd.LEGACY_FOR_STEP[step]
                    path = self.asset_path("assets", "stars", folder,
                                           f"{legacy}.png")
                if path:
                    self._cache.put(f"stars/{folder}/{step}",
                                    pygame.image.load(path).convert_alpha())
            # Legacy keys stay resolvable for star_icon_name(s) without
            # a zoom context (tools, diagnostics).
            for size in rnd.SIZE_DIRS.values():
                path = self.asset_path("assets", "stars", folder,
                                       f"{size}.png")
                if path:
                    self._cache.put(f"stars/{folder}/{size}",
                                    pygame.image.load(path).convert_alpha())

        path = self.asset_path("assets", "black_hole.png")
        if path:
            self._cache.put(
                "black_hole", pygame.image.load(path).convert_alpha())

        # Ship and monster icons: four steps per kind, indexed by zoom
        # level exactly as orion2re swaps its four LBX entries. A kind
        # with no artwork is not an error — ships.py falls back to the
        # player sprite, which keeps unknown monsters visible and in
        # the right place.
        for kind in ship_icons.ALL_KINDS:
            for step in range(zt.icon_step_count()):
                path = self.asset_path("assets", "ships", kind,
                                       f"{step}.png")
                if path:
                    self._cache.put(
                        ship_icons.sprite_key(kind, step),
                        pygame.image.load(path).convert_alpha())

        for form in self._data.get("nebula_forms", []):
            path = self.asset_path("assets", "nebula", f"{form}.png")
            if path:
                self._cache.put(
                    form, pygame.image.load(path).convert_alpha())

        # Sidebar readout icons. A missing file is not fatal: the row
        # then renders as it did before the icons existed.
        for key, filename in self._data.get("sidebar_icons", {}).items():
            path = self.asset_path("assets", "icons", filename)
            if path:
                self._cache.put(f"{SIDEBAR_ICON_PREFIX}{key}",
                                pygame.image.load(path).convert_alpha())
            else:
                log.warning("Sidebar icon not found: %s", filename)

        # LAST, so a throw above leaves the key unset and the next
        # `enter` tries again rather than trusting a half-filled cache.
        self._sprite_key_loaded = want_key

    def _load_map_background(self):
        """Star field artwork drawn under stars, nebulas and fleets.
        Cover-scaled and centre-cropped to the map_area box, so the
        map keeps its aspect and the artwork is never distorted."""
        cfg = self._data.get("frame", {})
        path = self.asset_path("assets",
                               cfg.get("map_background", "map_background.png"))
        self._map_bg = pygame.image.load(path).convert() if path else None
        self._scale_map_background()

    def _scale_map_background(self):
        """Cover-scaled to the WHOLE WINDOW since work order 170.

        The floor was cut to the map box, and outside it — the
        letterbox of a window wider than 16:9, the corner above the
        info panel — the background placeholder showed: the dark strip
        and the black corner of Data's 2576x1432 screenshot. The HUD
        sits on the floor (169, point 5), so the floor is under all of
        it; the stars stay clipped to the map box."""
        self._map_bg_scaled = None
        if self._map_bg is None:
            return
        w, h = self.app.win_w, self.app.win_h
        if w < 1 or h < 1:
            return
        iw, ih = self._map_bg.get_size()
        scale = max(w / iw, h / ih)
        sw, sh = max(w, int(iw * scale)), max(h, int(ih * scale))
        scaled = pygame.transform.smoothscale(self._map_bg, (sw, sh))
        self._map_bg_scaled = scaled.subsurface(
            ((sw - w) // 2, (sh - h) // 2, w, h)).copy()

    def on_resize(self):
        super().on_resize()
        self._cache.clear_scaled()
        # Tinted ship sprites are built FROM scaled ones, so dropping
        # the scaled cache without dropping these would leave the map
        # blitting last resolution's icons.
        self._tints.clear()
        self._wormholes.clear()
        # Ring radii are HD pixels; every cached one is now wrong.
        self._ping.clear_cache()
        self._scale_map_background()

    def exit(self):
        super().exit()
        self._cache.clear_scaled()
        self._tints.clear()
        self._wormholes.clear()
        self._ping.cancel()
        self._frame_scaled = None

    def update(self, game_state=None):
        """Cache the parsed state. Nebulas and players are parsed
        here rather than per frame — they only change per turn.

        Reads every array defensively: a snapshot that arrives
        mid-transition (or a caller passing a stub) must not take
        the screen down, it should just render an empty map.
        """
        if game_state is None:
            return
        # THE ONE PLACE A SNAPSHOT BECOMES THE MAP'S STATE, so it is the
        # one place another screen's state is kept out: the Fleets and
        # Officers screens rewrite `s_ship_icon` and `_cur_map_scale`
        # for their own inset while they are up (ships.GATED_FIELDS
        # names each with its source). Everything downstream reads
        # `_state` and needs no rule of its own — except `park_game`
        # below, which is handed the RAW snapshot on purpose.
        self._state = self._state_gate.state(game_state)
        # ONLY WHILE THE GAME IS ON THIS SCREEN, AND ONLY WHILE THE LIST
        # IS THIS SCREEN'S. This screen keeps updating under an overlay:
        # in the GAME popup's Load dialog field 9 is the ninth slot row,
        # which loads at once (loadsave.cpp:332-375). And the screen number
        # alone is not enough (work order 128 C): the turn-start research
        # prompt runs under screen 0 (mainscr2.cpp:119) and its field 9 is
        # a choice row whose commit reads the pointer (tech.cpp:354-369).
        # So the zoom-out button and the map grid must both be in the live
        # list, and the send goes to the index found there.
        fields = getattr(game_state, "fields", None)
        zoom_out = mapboxes.live_field(fields, self._data.get("zoom_out_field"))
        if (getattr(game_state, "current_screen",
                    self.GAME_SCREEN_ID) == self.GAME_SCREEN_ID
                and zoom_out is not None
                and mapboxes.live_field(fields, self._data.get("map_cancel"))):
            # THE RAW SNAPSHOT, never `self._state`: parking stops on
            # an ABSOLUTE target read off `map_scale`, so a gated one
            # would be a target it could never reach. Safe by two
            # locks anyway — this branch runs only while the game
            # reports screen 0, where the gate is the identity.
            self._viewctl.park_game(self.app, game_state, zoom_out.index)

        raw_nebulas = getattr(game_state, "nebulas_raw", None) or []
        self._nebulas = [nebula_struct.parse(r) for r in raw_nebulas
                         if len(r) >= nebula_struct.SIZE]

        raws = getattr(game_state, "player_raw", None) or []
        self._players = [player_struct.parse(r) for r in raws
                         if len(r) >= player_struct.SIZE]

        # Only needed as the fallback owner source for ship icons; the
        # ext patch makes this redundant but not wrong. Parsed here,
        # not per frame — the array can be thousands of records.
        raw_ships = getattr(game_state, "ships_raw", None) or []
        self._ships = [ship_struct.parse(r) for r in raw_ships
                       if len(r) >= ship_struct.SIZE]
        idx = getattr(game_state, "player_num", 0)
        self._local = (self._players[idx]
                       if 0 <= idx < len(self._players) else None)
        # The eta label's order lock ends on the order's effect (mapeta).
        self._eta_lock = mapeta.advance(self._eta_lock, game_state,
                                        self._ships)

    # ── Geometry ──────────────────────────────────────────

    def _map_view(self):
        """The view over the map_area box, or None when unusable.

        Mirroring the game: the transcribed integer MapView on the
        game's own snapshot. Decoupled (after the first wheel tick):
        the float SmoothMapView on the HD origin and scale, dressed
        as a state by the proxy. Everything downstream keeps one
        code path either way.
        """
        # The box's WINDOW rect (work order 170): `map_area` stretches
        # between the title plate and the bar (`anchor_v`), so its
        # reference rect through `layout.rect` is not where it is.
        rect = self.box_screen_rect("map_area")
        if rect is None or self._state is None:
            return None
        rect = tuple(rect)
        if self._viewctl.active:
            return mc.SmoothMapView(rect, self._viewctl.proxy(self._state))
        return mc.MapView(rect, self._state)

    def _map_context(self):
        """Zoom-derived sizes for this frame, or None when unusable."""
        view = self._map_view()
        if view is None:
            return None
        return rnd.MapContext(view, self._viewctl.proxy(self._state))

    def _game_zoom(self):
        """The GAME's zoom level, from its own snapshot (not the HD view)."""
        map_max_x = getattr(self._state, "map_max_x", 0) or 0
        map_max_y = getattr(self._state, "map_max_y", 0) or 0
        return zt.zoom_level(
            getattr(self._state, "map_scale", 10) or 10,
            zt.max_zoom_count(map_max_x, map_max_y),
            len(self._stars),
            zt.max_map_scale(map_max_x, map_max_y))

    def _icon_anchor(self):
        """Re-anchoring info for ship icons, only when decoupled."""
        if not self._viewctl.active or self._state is None:
            return None
        return ship_icons.IconAnchor(self._state, self._stars,
                                     self._ships, self._game_zoom())

    @property
    def _omniscient(self):
        """Galactic Lore from the local player's racial traits."""
        if self._local is None:
            return False
        return player_struct.has_omniscience(self._local)

    @property
    def _stars(self):
        return getattr(self._state, "stars", None) or []

    def _star_at(self, screen_x, screen_y):
        """Nearest star within its own icon radius, or None.

        The tolerance follows the drawn icon rather than a fixed
        fraction: zoomed out, a small star is only a few pixels
        across and a generous radius would swallow its neighbours;
        zoomed in, a fixed radius would be smaller than the sprite
        and clicks on the visible star would miss.
        """
        ctx = self._map_context()
        if ctx is None:
            return None
        view = ctx.view
        best, best_d = None, None
        for s in self._stars:
            sx, sy = view.to_screen(s.x, s.y)
            d = ((sx - screen_x) ** 2 + (sy - screen_y) ** 2) ** 0.5
            limit = max(MIN_STAR_HIT_PX,
                        rnd.star_icon_width(ctx, s) * STAR_HIT_SCALE)
            if d <= limit and (best_d is None or d < best_d):
                best, best_d = s, d
        return best

    # ── Rendering ─────────────────────────────────────────

    def render(self, surface):
        self._render_background(surface)
        self._render_map(surface)
        self._render_sidebar(surface)
        self._render_nav(surface)
        self._render_title(surface)
        # Above the HUD: the popup is a dialog, not content.
        self.render_help(surface)

    def title_rect(self):
        return hudview.title_rect(self)

    def _render_title(self, surface):
        hudview.render_title(self, surface)

    def _render_floor(self, surface, px=None):
        """The floor over the whole window, with the OLED floor lift
        (HD EXTENSION) — `floorlift.render_floor`."""
        floorlift.render_floor(self, surface, px)

    def _render_map(self, surface):
        ctx = self._map_context()
        self._render_floor(surface, ctx.px if ctx is not None else None)
        if ctx is None:
            return
        view = ctx.view
        clip = surface.get_clip()
        surface.set_clip(pygame.Rect(*view.box))

        player_num = getattr(self._state, "player_num", 0)
        omniscient = self._omniscient

        rnd.render_nebulas(surface, ctx, self._nebulas,
                           self._cache, self._data.get("nebula_forms", []))
        rnd.render_wormholes(surface, ctx, self._stars,
                             player_num, omniscient,
                             layer=self._wormholes)
        # Destination lines under the stars, as the original draws them
        # (mainscr_main.cpp:965, before Draw_Stars_).
        maplines.render_destination_lines(
            surface, ctx, self._state, self._ships, self._stars,
            self._game_zoom(), self._icon_anchor(), pygame.time.get_ticks())
        # "eta N" right after the lines, as Do_Ship_Destination_Lines_
        # prints it (ships.cpp:470-475).
        mapeta.render(surface, ctx, self._state, self._ships, self._stars,
                      self._players, self._icon_anchor(), self.style,
                      boxdraw._texts(self), self._eta_lock, self._eta_cache)
        heights = rnd.render_stars(surface, ctx, self._stars, self._cache)

        # Star name size follows the zoom level, as the original
        # switches font style per zoom (Zoom_Level_Font_Style_).
        name_size = self.layout.font_size(int(
            16 * self.box_font_scale("map_area") * ctx.name_font_scale))

        def render_label(text, colour):
            # Star names can contain characters Bank Gothic DEMO
            # replaces with a watermark — the parentheses around a
            # Galactic Lore name, and the digit 4. render_text falls
            # back per character.
            return self.style.render_text(text, name_size, colour)

        rnd.render_star_names(surface, ctx, self._stars, heights,
                              render_label,
                              player_num, self._players, omniscient)
        rnd.render_fleets(surface, ctx,
                          getattr(self._state, "ship_icons", None) or [],
                          self._players, self._cache, self._tints,
                          cfg=self._data.get("ship_icons") or {},
                          ships=self._ships,
                          anchor=self._icon_anchor(),
                          nodes=ship_icons.wire_nodes(self._state))

        # Home-system ping, above the icons so it cannot be hidden by
        # a fleet parked on the star. Resolved per frame rather than
        # captured at the keypress, so it stays on the right point
        # while the player zooms or scrolls.
        if self._ping.active:
            self._ping.render(surface, ctx, self._ping_position(ctx))

        if self._hover_star is not None:
            sx, sy = view.to_screen(self._hover_star.x, self._hover_star.y)
            r = int(max(MIN_STAR_HIT_PX,
                        rnd.star_icon_width(ctx, self._hover_star) * 0.62))
            pygame.draw.circle(surface, HOVER_COLOR[:3],
                               (int(sx), int(sy)), r, 2)
            self._render_hover_name(surface, view)
        # The movable boxes, above everything on the map (boxdraw).
        boxdraw.render(self, surface)
        surface.set_clip(clip)

    def _render_sidebar(self, surface):
        hudview.render_sidebar(self, surface)

    def _sidebar_icons(self):
        """Row key -> cache key, for the icons that actually loaded."""
        return {key: f"{SIDEBAR_ICON_PREFIX}{key}"
                for key in self._data.get("sidebar_icons", {})
                if self._cache.has(f"{SIDEBAR_ICON_PREFIX}{key}")}

    def _sidebar_geometry(self, rows, icons):
        """Row key -> (text rect, icon rect|None), from the sb_* boxes.

        Falls back to an even split of the sidebar cutout when no
        text box exists for any row — that is a boxes.json from
        before the per-element boxes, or a mod shipping one.
        """
        geo = {}
        for key in rows:
            text = self.box_rect(f"{SIDEBAR_BOX_PREFIX}{key}_text")
            if not text:
                continue
            icon = (self.box_rect(f"{SIDEBAR_BOX_PREFIX}{key}_icon")
                    if key in icons else None)
            geo[key] = (text, icon or None)
        if geo:
            return geo
        box = self.box_rect("sidebar")
        return sb.fallback_geometry(box, rows, icons) if box else {}

    def _sidebar_font_scales(self, rows):
        # The STORED scale: `sidebar.draw_text_block` goes through
        # `Layout.font_size`, which applies the window scale already
        # ("Scaling twice"). Since 169 one value serves every size, so
        # the per-resolution tuning that cancelled the square is gone.
        return {key: self.box_font_scale_stored(
            f"{SIDEBAR_BOX_PREFIX}{key}_text") for key in rows}

    def _sidebar_aligns(self, rows):
        return {key: self.box_style(
            f"{SIDEBAR_BOX_PREFIX}{key}_text").get("align", "center")
            for key in rows}

    def _render_nav(self, surface):
        hudview.render_nav(self, surface)

    def nav_rect(self, key):
        return hudview.nav_rect(self, key)

    def nav_hit(self, key, x, y):
        return hudview.nav_hit(self, key, x, y)

    def _render_hover_name(self, surface, view):
        """Hovered system name, bottom-centre inside the map area.
        The original has no hover feedback; this replaces the old
        status_bar line now that that cutout is the TURN button."""
        if self._hover_star is None:
            return
        fs = self.box_font_scale("map_area")
        font = self.style.get_prop_font(self.layout.font_size(int(18 * fs)))
        text = font.render(self._hover_star.name, True, STATUS_COLOR[:3])
        bx, by, bw, bh = view.box
        surface.blit(text, (bx + (bw - text.get_width()) // 2,
                            by + bh - text.get_height()
                            - int(8 * self.layout.scale)))

    # ── Input ─────────────────────────────────────────────
    # The handling itself is `mapinput` (work order 126 F); these are the
    # ScreenBase hooks, falling through to it where the input was not taken.

    def handle_mouse_motion(self, screen_x, screen_y):
        super().handle_mouse_motion(screen_x, screen_y)
        mapinput.mouse_motion(self, screen_x, screen_y)

    def handle_click(self, screen_x, screen_y):
        if mapinput.click(self, screen_x, screen_y):
            return None
        return super().handle_click(screen_x, screen_y)

    def handle_key(self, key):
        if not mapinput.key_down(self, key):
            super().handle_key(key)

    def handle_right_button(self, down, mx, my):
        return mapinput.right_button(self, down, mx, my)

    def handle_mousewheel(self, direction, mx, my):
        mapinput.mousewheel(self, direction, mx, my)

    def help_extra_rect(self, spec):
        """The title plate, which is not a box: `title_rect`, the same
        function the click and the drawing use (decision 5)."""
        if spec.get("title"):
            return self.title_rect()
        return None

    # ── Home system ping ──────────────────────────────────

    def home_star(self):
        """The local player's home system, or None.

        Two verified specs chained: `s_player.home_planet_id` indexes
        `_planet[]`, and `s_planet_data.star_index` names the system.
        Both offsets come from compiling orion2re's own header, and
        both arrays are already in the snapshot — nothing is inferred
        and no C++ patch is needed.

        The result carries its own check, the way the ship icons do:
        the home system starts the game owned by its player. A
        mismatch is logged rather than acted on, because a homeworld
        that has been captured is a legitimate mismatch and the
        planet record is still right. Only an out-of-range index —
        which would mean the offsets are wrong, not the game state —
        falls back to the first star the player owns.
        """
        stars = self._stars
        if not stars:
            return None
        pid = getattr(self._local, "home_planet_id", None)
        raws = getattr(self._state, "planets_raw", None) or []

        if pid is not None and 0 <= pid < len(raws):
            planet = planet_struct.parse(raws[pid])
            idx = planet.star_index
            if 0 <= idx < len(stars):
                star = stars[idx]
                pnum = getattr(self._state, "player_num", 0)
                if star.owner != pnum:
                    log.info("Home system %s is owned by %s, not by the "
                             "local player — captured, or the planet "
                             "index is off", star.name, star.owner)
                return star
            log.warning("home_planet_id %s -> star_index %s is out of "
                        "range (%d stars)", pid, idx, len(stars))

        pnum = getattr(self._state, "player_num", 0)
        for s in stars:
            if s.owner == pnum:
                log.info("No usable home planet record; pinging %s",
                         s.name)
                return s
        return None

    def _ping_position(self, ctx):
        """HD point the ping rings are centred on, or None.

        A home system outside the current viewport is clamped to the
        edge of the map area instead of being dropped: an invisible
        ping reads as a broken key, and a ring pressed against the
        border still says which way to look.
        """
        star = self.home_star()
        if star is None:
            return None
        bx, by, bw, bh = ctx.view.box
        sx, sy = ctx.view.to_screen(star.x, star.y)
        cx = min(max(sx, bx), bx + bw)
        cy = min(max(sy, by), by + bh)
        return (cx, cy)

    def ping_home(self):
        """Flash the home system. Cosmetic only — nothing is sent to
        orion2re, so the game cannot be disturbed by the key."""
        star = self.home_star()
        if star is None:
            log.info("Home system ping: no home system in this snapshot")
            return False
        log.info("Home system ping: %s", star.name)
        self._ping.trigger()
        return True

    def _ping_key(self):
        """Keycode that triggers the ping, from layout.json.

        Named rather than numeric so a mod can pick a different key
        without knowing pygame's constants. HOME is the default
        because MOO2's galaxy map binds no such key, so nothing is
        taken away from the game.
        """
        cfg = self._data.get("home_ping") or {}
        if not cfg.get("enabled", True):
            return None
        name = cfg.get("key", "home")
        try:
            return pygame.key.key_code(name)
        except (ValueError, AttributeError):
            log.warning("home_ping.key %r is not a key name; using HOME",
                        name)
            return pygame.K_HOME
