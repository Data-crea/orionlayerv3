"""Galaxy Map Screen — orion2re SCREEN_MAIN (id 0).

Layout: one cockpit frame PNG (assets/frame.png) with transparent
cutouts, stretched over the 1920x1080 reference area and drawn ABOVE
everything else. The boxes in boxes.json are the cutouts themselves,
derived by tools/frame_holes.py — content is painted underneath and
shows through:
  map_area        the star field
  sidebar         stardate on top, then five resource readouts
  nav_*           seven buttons mirroring the original: six along
                  the bottom (Colonies, Planets, Fleets, Leaders,
                  Races, Info) and nav_turn bottom-right; the title
                  cutout doubles as the GAME menu button
The title cutout is not a box; it lives in layout.json ("frame").

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
from core.config import REF_W, REF_H
from core.screen_base import ScreenBase
from core.structs import nebula as nebula_struct
from core.structs import planet as planet_struct
from core.structs import player as player_struct
from core.structs import ship as ship_struct
from screens.galaxy_map import ping as home_ping
from screens.galaxy_map import renderer as rnd
from screens.galaxy_map import ships as ship_icons
from screens.galaxy_map import viewctl
from screens.galaxy_map import starfield as sf
from screens.galaxy_map import sidebar as sb

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
        self._state = None
        self._hover_star = None
        self._nebulas = []
        self._players = []
        self._ships = []
        self._tints = ship_icons.TintCache()
        self._wormholes = rnd.WormholeLayer()
        self._local = None
        self._frame = None          # original frame PNG
        self._frame_scaled = None   # scaled to the reference area
        self._frame_pos = (0, 0)
        self._map_bg = None         # gas clouds behind the map
        self._map_bg_scaled = None  # cover-scaled + cropped to map_area
        self._starfield = sf.StarfieldLayer()
        self._ping = home_ping.HomePing()
        self._viewctl = viewctl.ViewControl()   # decoupled HD viewport
        self._pan_from = None                   # right-drag anchor

    # ── Lifecycle ─────────────────────────────────────────

    def enter(self, game_state=None):
        super().enter(game_state)
        self._data = self.app.res.load_json(
            "screens/galaxy_map/layout.json", {}) or {}
        self._load_sprites()
        self._load_frame()
        self._load_map_background()
        self._starfield.configure(self._data.get("starfield", {}))
        self._hover_star = None
        self._viewctl.reset()
        self._pan_from = None
        self.update(game_state)

    def _load_sprites(self):
        """Star icons, black hole and nebula shapes (mod-resolved).

        Six steps per class (`0.png`..`5.png`), indexed by
        zoom + star.size like the original. Any step a skin or mod
        does not ship falls back to the nearest legacy artwork
        (large/medium/small), so an incomplete set still renders.
        """
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

    def _load_frame(self):
        """The cutout frame; stretched over the reference area so the
        cutouts coincide with the boxes derived from them."""
        cfg = self._data.get("frame", {})
        path = self.asset_path("assets", cfg.get("image", "frame.png"))
        self._frame = pygame.image.load(path).convert_alpha() if path else None
        self._scale_frame()

    def _scale_frame(self):
        if self._frame is None:
            self._frame_scaled = None
            return
        x, y, w, h = self.layout.rect((0, 0, REF_W, REF_H))
        self._frame_scaled = pygame.transform.smoothscale(self._frame, (w, h))
        self._frame_pos = (x, y)

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
        self._map_bg_scaled = None
        box = self.box_rect("map_area")
        if self._map_bg is None or not box:
            return
        _, _, w, h = self.layout.rect(box)
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
        self._scale_frame()
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
        self._state = game_state
        self._viewctl.park_game(self.app, game_state)

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

    # ── Geometry ──────────────────────────────────────────

    def _map_view(self):
        """The view over the map_area box, or None when unusable.

        Mirroring the game: the transcribed integer MapView on the
        game's own snapshot. Decoupled (after the first wheel tick):
        the float SmoothMapView on the HD origin and scale, dressed
        as a state by the proxy. Everything downstream keeps one
        code path either way.
        """
        box = self.box_rect("map_area")
        if not box or self._state is None:
            return None
        rect = self.layout.rect(box)
        if self._viewctl.active:
            return mc.SmoothMapView(rect, self._viewctl.proxy(self._state))
        return mc.MapView(rect, self._state)

    def _map_context(self):
        """Zoom-derived sizes for this frame, or None when unusable."""
        view = self._map_view()
        if view is None:
            return None
        return rnd.MapContext(view, self._viewctl.proxy(self._state))

    def _icon_anchor(self):
        """Re-anchoring info for ship icons, only when decoupled."""
        if not self._viewctl.active or self._state is None:
            return None
        game_zoom = zt.zoom_level(
            getattr(self._state, "map_scale", 10) or 10,
            zt.max_zoom_count(getattr(self._state, "map_max_x", 0) or 0),
            len(self._stars),
            zt.max_map_scale(getattr(self._state, "map_max_x", 0) or 0))
        return ship_icons.IconAnchor(self._state, self._stars,
                                     self._ships, game_zoom)

    def box_style(self, name):
        for box in self.boxes:
            if box.name == name:
                return box.style
        return {}

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
        self._render_frame_image(surface)
        self._render_title(surface)
        # Above the cockpit frame: the popup is a dialog, not content
        # under a cutout.
        self.render_help(surface)

    def _render_frame_image(self, surface):
        if self._frame_scaled is not None:
            surface.blit(self._frame_scaled, self._frame_pos)
        elif self.USE_FRAME:
            self._render_frame(surface)

    def _render_title(self, surface):
        """Title text inside the frame's title cutout (layout.json)."""
        cfg = self._data.get("frame", {})
        rect = cfg.get("title_rect")
        title = cfg.get("title", self.FRAME_TITLE)
        if not rect or not title:
            return
        x, y, w, h = self.layout.rect(rect)
        font = self.style.get_font(self.layout.font_size(
            cfg.get("title_font", 30)))
        text = font.render(title.upper(), True, TITLE_COLOR[:3])
        surface.blit(text, (x + (w - text.get_width()) // 2,
                            y + (h - text.get_height()) // 2))

    def _render_map(self, surface):
        ctx = self._map_context()
        if ctx is None:
            return
        view = ctx.view
        clip = surface.get_clip()
        surface.set_clip(pygame.Rect(*view.box))
        if (self._map_bg_scaled is not None
                and self._map_bg_scaled.get_size() == view.box[2:]):
            surface.blit(self._map_bg_scaled, view.box[:2])
        else:
            surface.fill(MAP_BG[:3], pygame.Rect(*view.box))

        # Background point stars, added on top of the artwork and
        # under everything the game owns. Additive, so the value a
        # star carries is the light it contributes — the same weight
        # over a gas cloud as over empty space.
        self._starfield.render(surface, view.box, ctx.px)

        player_num = getattr(self._state, "player_num", 0)
        omniscient = self._omniscient

        rnd.render_nebulas(surface, ctx, self._nebulas,
                           self._cache, self._data.get("nebula_forms", []))
        rnd.render_wormholes(surface, ctx, self._stars,
                             player_num, omniscient,
                             layer=self._wormholes)
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
                          anchor=self._icon_anchor())

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
        surface.set_clip(clip)

    def _render_sidebar(self, surface):
        box = self.box_rect("sidebar")
        if not box:
            return
        surface.fill(PANEL_BG[:3], pygame.Rect(*self.layout.rect(box)))
        stardate = (str(getattr(self._state, "stardate_str", "--"))
                    if self._state is not None else "--")
        rows = self._data.get("sidebar_rows") or sb.DEFAULT_ROWS
        icons = self._sidebar_icons()
        sb.render(surface, self.layout, self.style,
                  self._sidebar_geometry(rows, icons),
                  self._local, self._data.get("labels", {}), rows,
                  font_scales=self._sidebar_font_scales(rows),
                  aligns=self._sidebar_aligns(rows),
                  monetary=self._data.get("monetary_unit", "BC"),
                  extras={"stardate": (stardate, "")},
                  icons=icons, cache=self._cache,
                  fonts=self._data.get("sidebar_fonts", sb.DEFAULT_FONTS),
                  panel_box=box,
                  dividers=self._data.get("sidebar_dividers", True))

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
        return {key: self.box_font_scale(
            f"{SIDEBAR_BOX_PREFIX}{key}_text") for key in rows}

    def _sidebar_aligns(self, rows):
        return {key: self.box_style(
            f"{SIDEBAR_BOX_PREFIX}{key}_text").get("align", "center")
            for key in rows}

    def _render_nav(self, surface):
        """Navigation buttons: the frame provides the bezel, so each
        box only gets a fill plus its label; hover brightens the fill."""
        # Window coordinates, not desktop coordinates: in fullscreen
        # the content sits inside black bars and a raw get_pos() puts
        # the highlight one bar-width off the pointer.
        mouse = mouse_input.pos()
        for spec in self._data.get("buttons", []):
            name = f"nav_{spec['key']}"
            box = self.box_rect(name)
            if not box:
                continue
            font = self.style.get_font(self.layout.font_size(
                self.box_style(name).get("font_size", 16)))
            rect = pygame.Rect(*self.layout.rect(box))
            hovered = rect.collidepoint(mouse)
            surface.fill((NAV_HOVER_BG if hovered else NAV_BG)[:3], rect)
            text = font.render(spec["label"].upper(), True, NAV_TEXT[:3])
            surface.blit(text, (rect.x + (rect.w - text.get_width()) // 2,
                                rect.y + (rect.h - text.get_height()) // 2))

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

    def handle_mouse_motion(self, screen_x, screen_y):
        super().handle_mouse_motion(screen_x, screen_y)
        if self._pan_from is not None:
            view = self._map_view()
            if view is not None:
                dx = screen_x - self._pan_from[0]
                dy = screen_y - self._pan_from[1]
                if dx or dy:
                    self._viewctl.pan(view, self._state, dx, dy)
                    self._pan_from = (screen_x, screen_y)
            return
        self._hover_star = self._star_at(screen_x, screen_y)

    def help_extra_rect(self, spec):
        """The title cutout, which is not a box.

        The galaxy map draws its own cockpit frame PNG rather than
        the shared 9-slice, so the title bar lives in layout.json
        under `frame.title_rect` instead of coming from
        `Frame.title_rect()`. Resolved through the same
        `layout.rect()` the click path uses — decision 5.
        """
        if spec.get("title"):
            rect = self._data.get("frame", {}).get("title_rect")
            return pygame.Rect(*self.layout.rect(rect)) if rect else None
        return None

    def handle_click(self, screen_x, screen_y):
        if self.help_consumes_click(screen_x, screen_y):
            return None
        # Title cutout = the original's GAME button (top centre).
        title = self._data.get("frame", {}).get("title_rect")
        if title and pygame.Rect(*self.layout.rect(title)).collidepoint(
                screen_x, screen_y):
            self._activate(self._data.get("actions", {}).get("game_menu"),
                           "game menu")
            return None

        # Navigation buttons next — they sit outside the map area.
        for spec in self._data.get("buttons", []):
            box = self.box_rect(f"nav_{spec['key']}")
            if not box:
                continue
            if pygame.Rect(*self.layout.rect(box)).collidepoint(
                    screen_x, screen_y):
                self._activate(spec["field_id"], spec["key"])
                return None

        star = self._star_at(screen_x, screen_y)
        if star is not None:
            self._click_star(star)
            return None

        # Empty map space: forward the raw position so the game can
        # clear its selection or place a move order. The pixel goes
        # HD -> galaxy through WHATEVER view is on screen, then
        # galaxy -> native through the game's view, which is the one
        # the click has to land in.
        view = self._map_view()
        if view is not None and pygame.Rect(*view.box).collidepoint(
                screen_x, screen_y):
            gx, gy = view.to_galaxy(screen_x, screen_y)
            nx, ny = mc.galaxy_to_native(gx, gy, self._state)
            if mc.on_screen(nx, ny) and self.app.connected:
                self.app.client.inject_click(nx, ny)
            return None

        return super().handle_click(screen_x, screen_y)

    def _click_star(self, star):
        """Select a system by clicking its exact native position.

        Always computed with the GAME's own view state, never the HD
        one: the click has to land inside orion2re's slice, and while
        decoupled the two are different transforms. park_game keeps
        that slice covering the whole galaxy, so the on_screen gate
        only ever rejects during the brief parking transition.
        """
        log.info("Star clicked: %s (%d, %d)", star.name, star.x, star.y)
        if not self.app.connected or self._state is None:
            return
        nx, ny = mc.galaxy_to_native(star.x, star.y, self._state)
        if mc.on_screen(nx, ny):
            self.app.client.inject_click(nx, ny)
        else:
            log.debug("Star %s is off the original viewport", star.name)

    def _activate(self, field_id, what=""):
        log.info("Action: %s (field %s)", what or field_id, field_id)
        if self.app.connected and field_id is not None:
            self.app.client.activate_field(field_id)

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

    def handle_key(self, key):
        if self.help_consumes_key(key):
            return
        actions = self._data.get("actions", {})
        ping_key = self._ping_key()
        if ping_key is not None and key == ping_key:
            # Consumed here on purpose: forwarding it would hand
            # orion2re a key it has no binding for.
            self.ping_home()
            return
        if key == pygame.K_g:
            self._activate(actions.get("game_menu"), "game menu")
            return
        if key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS,
                   pygame.K_MINUS, pygame.K_KP_MINUS):
            view = self._map_view()
            if view is not None:
                bx, by, bw, bh = view.box
                direction = (1 if key in (pygame.K_PLUS, pygame.K_EQUALS,
                                          pygame.K_KP_PLUS) else -1)
                self._viewctl.zoom_at(view, self._state,
                                      bx + bw // 2, by + bh // 2,
                                      direction)
            return
        if key in (pygame.K_0, pygame.K_KP0):
            # Back to the full-galaxy view (mirror the parked game).
            self._viewctl.reset()
            return
        for spec in self._data.get("buttons", []):
            hotkey = spec.get("hotkey")
            if hotkey and key == ord(hotkey):
                self._activate(spec["field_id"], spec["key"])
                return
        super().handle_key(key)

    def handle_right_button(self, down, mx, my):
        """Right button: context help first, then the pan drag.

        The original's help list for this screen covers the sidebar
        readouts, the bottom bar and the title, and pointedly NOT the
        map area (evanhelp.cpp:4) — a right click on the stars means
        nothing to MOO2. So the two uses do not collide: help answers
        over a control, the drag starts over the map.
        """
        if ScreenBase.handle_right_button(self, down, mx, my):
            self._pan_from = None
            return True
        if not down:
            self._pan_from = None
            return False
        view = self._map_view()
        if view is not None and pygame.Rect(*view.box).collidepoint(
                mx, my):
            self._pan_from = (mx, my)
        return False

    def handle_mousewheel(self, direction, mx, my):
        """Wheel over the map zooms the HD viewport, at the pointer.

        The game is not told: the snapshot carries every star's
        galaxy coordinate, so the HD view scales and pans on its
        own. The first tick decouples from the game's slice;
        park_game then walks the game to maximum zoom-out so every
        click keeps resolving (see viewctl).
        """
        view = self._map_view()
        if view is None:
            return
        if self.help_consumes_wheel(direction):
            return
        if not pygame.Rect(*view.box).collidepoint(mx, my):
            return
        self._viewctl.zoom_at(view, self._state, mx, my, direction)
