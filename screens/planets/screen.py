"""Planets Screen — orion2re SCREEN_PLANET_SUMMARY (id 32).

`PLNTSUM::Planet_Summary_Screen_` (plntsum.cpp:1931). Brief 101, built
from Data's frame3 and mockup3, 13 September 2026.

What drives the game from here, and how (decision 20):
  RETURN        ACTIVATE_FIELD on the esc button, found in the live field
                list by its 0x1B hotkey (plntsum.cpp:724-731)
  sort keys     INJECT_CLICK at `native_click` — multi-button fields are
                type 3, which ACTIVATE_FIELD does not take
  restrictions  INJECT_KEY "1".."5", the radio fields' own hotkeys, with
                `native_click` as the fallback

  sending       with open fix 97's PLSM block (work order 271,
                `planetsend`): the two send buttons, a row click while a
                send is armed, a click on an order's marker to undo it —
                each the game's own field, the planet brought into the
                game's window by its star icon first

  star click    with PLSM and more than eight rows in the game's list, the
                star's own icon field (plntsum.cpp:2052-2064, v2
                :2044-2058) — the game's warning box (H 0x14F) when the
                star has no planet in its list, HD's message box (work
                order 322 A1)

What is local and sends nothing: the list, its scroll window (decision
46), the hover, the bottom windows. Without PLSM the two send buttons are
display only, as before, and a star click only scrolls HD's list. The
Planets In Range toggle filters the HD list as the game's does
(`planetrange`, work order 322 A3).

The rows, the order and the words are `planetrows` and `planetwords`; the
drawing is `planetdraw`; this file owns the boxes, the input and the wire.
"""
import logging

from core import hestrings
from core import lang
from core import listgrid
from core import planetsblock
from core.hud import shell
from core import mouse as mouse_input
from core.screen_base import ScreenBase
from core.shipparts import ShipPartNames
from screens.colony_summary import colonyrows

from . import monsterpanel, planetdraw, planetrows, planetsend, planetwords

log = logging.getLogger("planets")

from core.nativeview import NATIVE_W, NATIVE_H
#: The native box the inset stars are computed for (plntsum.cpp:1351).
INSET_NATIVE = (443, 17, 180, 116)
KEY_ESC = 27


class PlanetsScreen(ScreenBase):
    SCREEN_NAME = "planets"
    #: Its picture moves only with input, the game and the window: a frame
    #: that would draw it again is not drawn (work order 273, `core/drawgate`).
    STILL = True
    GAME_SCREEN_ID = 32         # SCREEN_PLANET_SUMMARY, orion2_consts.h:487
    USE_FRAME = False
    SHELL_WORN = True           # work order 225, `shell_planets.png`

    def __init__(self, app):
        super().__init__(app)
        self._data = {}
        self._state = None
        self._view = None
        self._list = planetrows.PlanetList()
        self._filters = {key: False for key in planetrows.FILTERS}
        self._words = None
        self._first = 0
        self._hover = None          # list index under the pointer, or None
        self._selected = None       # planet index of the scanned row
        self._scanned = None        # star index + 1000, MOX::_scanned_field
        self._parts = None          # ship part names, core.shipparts
        self._monster_sprites = {}  # owner -> panel sprite or None
        self._monster_scaled = {}   # the one scaled copy on screen
        # THE SHELL (work order 225): the title plate; RETURN is a box of
        # the side panel, so the shell carries no buttons here.
        self.shell = shell.Shell(title=self._title)

    def _title(self):
        """The plate's word: the label of the galaxy map's button that
        opens this screen (layout.json `title`; the original prints no
        title, its word is PLNTSUM.LBX artwork), in the session's words."""
        return lang.tr(self._data.get("title", "Planets"))

    # ── Lifecycle ─────────────────────────────────────────

    def enter(self, game_state=None):
        super().enter(game_state)
        self._data = self.app.res.load_json(
            "screens/planets/layout.json", {}) or {}
        language = (getattr(self.app, "settings", {}) or {}).get(
            "language", "en")
        self._words = planetwords.Words.load(
            language, self._data.get("words", {}).get("food", "%s Food"),
            hestrings.for_app(self.app))
        self._parts = ShipPartNames(language)
        self._list = planetrows.PlanetList(
            self._data.get("sort", {}).get("default", "climate"))
        # MOX::_scanned_field = -1 on entry (plntsum.cpp:1945).
        self._first, self._hover = 0, None
        self._selected = self._scanned = None
        self._sender = planetsend.Sender()
        # No frame image since decision 71 (work order 189 removed the loader).
        self.update(game_state)
        self._push_sort_key()

    def update(self, game_state=None):
        if game_state is None:
            return
        # ONCE PER SNAPSHOT (work order 226 C): the view parses every
        # planet, colony and player record; the App calls `update` every
        # frame with the same snapshot, and re-parsing it cost Planets 8 ms
        # a frame. The list is still refreshed every frame (a filter or a
        # sort clicked since).
        if game_state is not self._state or self._view is None:
            self._view = planetrows.View(game_state)
            self._stars_cache = None
        fresh = self.new_snapshot(game_state)
        self._state = game_state
        sender = getattr(self, "_sender", None)
        if sender is not None:
            sender.step(self.app, planetsend.block(game_state), fresh)
        if self._list.refresh(self._view, self._filters):
            self._clear_scanned()
        self._clamp_after_filter()

    def on_resize(self):
        super().on_resize()

    def _push_sort_key(self):
        """Impose the HD sort key on the game once, on entry — the colony
        summary's trade; a click on the key the game already holds changes
        nothing (plntsum.cpp:2013-2018). One send, as the colony summary's:
        a key named twice in layout.json must not inject twice (work order
        264, D16). No name-first step: `Sort_Planet_Summary_` is the C
        library's unstable `qsort`, so a prior order does not survive it
        ([planets.rows])."""
        spec = next((b for b in self._data.get("sort", {}).get("buttons", [])
                     if b["key"] == self._list.sort_key), None)
        if spec is not None:
            self._inject(spec, f"entry sort {spec['key']}")

    # ── State helpers ─────────────────────────────────────

    @property
    def visible(self):
        return int(self._data.get("list", {}).get("row_count", 8))

    def _clear_scanned(self):
        self._scanned = None
        self._selected = None

    def _clamp_after_filter(self):
        """plntsum.cpp:2022-2028, after a filter click."""
        total = len(self._list.rows)
        if total < self.visible:
            self._first = 0
        elif total < self._first + self.visible:
            self._first = total - self.visible

    def _cells(self):
        if self._view is None or self._words is None:
            return []
        return [planetwords.cells(self._view, row, self._words)
                for row in self._list.rows]

    def _selected_row(self):
        for row in self._list.rows:
            if row["index"] == self._selected:
                return row
        return None

    def _inset_stars(self):
        """The inset's stars, built once per snapshot (work order 226 C):
        a pointer motion off the list asked for them on every event."""
        if self._state is None:
            return []
        cache = getattr(self, "_stars_cache", None)
        if cache is None or cache[0] is not self._state:
            cache = (self._state, colonyrows.galaxy_inset_stars(
                self._state, INSET_NATIVE))
            self._stars_cache = cache
        return cache[1]

    def _send_available(self, hotkey):
        """A send button is available exactly when the game added its
        hidden field (plntsum.cpp:703-713)."""
        fields = getattr(self._state, "fields", None) or []
        return any(f.hotkey in (ord(hotkey.upper()), ord(hotkey.lower()))
                   for f in fields)

    # ── Rendering ─────────────────────────────────────────

    def render(self, surface):
        self._render_background(surface)
        planetdraw.fill_panels(self, surface)
        cells = self._cells()
        rows = self._list.rows
        planetdraw.render_list(self, surface, rows, cells, self._first,
                               self._hover, self._selected)
        self._sender.draw_marks(
            surface, self, planetsend.block(self._state), rows, self._first,
            planetdraw.row_bands(self),
            planetdraw.columns(self, self._data.get("list", {})).get(
                "planet"),
            self.layout.font_size(17), self.layout.scale)
        planetdraw.render_scroll(self, surface, len(rows), self._first,
                                 self.visible)
        stars = self._inset_stars()
        planetdraw.render_inset(self, surface, stars, self._marker())
        planetdraw.render_status(self, surface, planetwords.status_line(
            self._view, self._scanned, self._words)
            if self._view is not None else None)
        self._render_controls(surface)
        row = self._selected_row()
        if row is not None:
            planetdraw.render_planet_panel(
                self, surface, row,
                planetwords.cells(self._view, row, self._words)["planet"])
        monsterpanel.render(self, surface, row)
        self.render_shell(surface)
        self.render_help(surface)

    def _marker(self):
        if self._scanned is None or self._view is None:
            return None
        index = self._scanned - 1000
        if not 0 <= index < len(self._view.stars):
            return None
        owner = int(self._view.stars[index].owner)
        player = self._view.player(owner) if 0 <= owner < 8 else None
        return index, planetdraw.row_color(
            {"owner_color": player.color if player is not None else None},
            False)

    def _render_controls(self, surface):
        mouse = mouse_input.pos()
        words = self._data.get("words", {})
        planetdraw.render_heading(self, surface, "sort_heading",
                                  words.get("sort_heading"))
        planetdraw.render_heading(self, surface, "restrict_heading",
                                  words.get("restrict_heading"))
        for spec in self._data.get("sort", {}).get("buttons", []):
            planetdraw.render_control(self, surface, "sort_" + spec["key"],
                                      spec["label"],
                                      active=spec["key"] == self._list.sort_key,
                                      mouse=mouse)
        for spec in self._data.get("restrictions", {}).get("buttons", []):
            planetdraw.render_control(self, surface, "restrict_" + spec["key"],
                                      spec["label"],
                                      active=self._filters[spec["key"]],
                                      mouse=mouse)
        send = self._data.get("send", {})
        for key in ("colony", "outpost"):
            spec = send.get(key, {})
            state = planetsend.button_state(planetsend.block(self._state),
                                            key)
            planetdraw.render_control(
                self, surface, "send_" + key, spec.get("label"),
                active=state == "active",
                enabled=self._send_available(spec.get("hotkey", "?"))
                if state is None else state != "disabled",
                mouse=mouse)
        planetdraw.render_divider(self, surface)
        planetdraw.render_return(self, surface,
                                 self._data.get("return", {}).get("label"))

    # ── Input ─────────────────────────────────────────────

    def handle_click(self, screen_x, screen_y):
        if self.help_consumes_click(screen_x, screen_y):
            return None
        pos = (screen_x, screen_y)
        up, down = planetdraw.scroll_arrows(self)
        if up and up.collidepoint(pos):
            return self._scroll(-1)
        if down and down.collidepoint(pos):
            return self._scroll(1)
        for spec in self._data.get("sort", {}).get("buttons", []):
            if self._hit("sort_" + spec["key"], pos):
                if spec["key"] != self._list.sort_key:
                    self._list.sort(spec["key"])
                    self._clear_scanned()       # plntsum.cpp:2016
                self._inject(spec, f"sort {spec['key']}")
                return None
        for spec in self._data.get("restrictions", {}).get("buttons", []):
            if self._hit("restrict_" + spec["key"], pos):
                self._filters[spec["key"]] = not self._filters[spec["key"]]
                if self._view is not None and self._list.refresh(
                        self._view, self._filters):
                    self._clear_scanned()
                self._clamp_after_filter()
                self._inject(spec, f"restriction {spec['key']}")
                return None
        b = planetsend.block(self._state)
        for key in ("colony", "outpost"):
            if self._hit("send_" + key, pos):
                if not self._sender.toggle(self.app, b, key):
                    log.info("Send %s ship: no field (no PLSM, or the game "
                             "offers none)", key)
                return None
        mark = self._sender.mark_at(pos)
        if mark is not None:
            self._sender.request(*mark)
            return None
        if planetdraw.return_hit(self, pos):
            self._return()
            return None
        star = planetdraw.inset_star_at(self, self._inset_stars(), *pos)
        if star is not None:
            self._star_click(star)
            return None
        # A row click sends the nearest ship while a send is armed
        # (Scan_Summary_Box_Fields_, plntsum.cpp:1284-1289); without one
        # the original does nothing with it.
        area = planetdraw.window(self, "rows")
        if planetsend.armed(b) and area and area.collidepoint(pos):
            band = listgrid.band_at(planetdraw.row_bands(self), screen_y)
            index = self._first + band if band is not None else -1
            if 0 <= index < len(self._list.rows):
                self._sender.request("send", self._list.rows[index]["index"])
        return None

    def _star_click(self, star):
        """A click on a star of the inset: the original's `planet_icons[i]`
        field (plntsum.cpp:2052-2064, v2 :2044-2058), which acts only with
        more than eight rows in the GAME's list — it scrolls the game's
        list to the star's first planet, or, when the star has none, opens
        `GENDRAW::Warning_Box_` with H 0x14F formatted with the star
        (`HESTR_14F_NO_PLANETS_IN_THE_S_ST`, :2056-2059, v2 :2049-2052),
        which HD's message box draws (MSGB).

        TRANSCRIPTION `star_click` (work order 322 A1): HD sends that
        field, read from the PLSM block of the snapshot on screen, and only
        when the live field list carries it (P816: the decision is the
        game's own count, against the original's literal 8 —
        `planetsblock.ROWS_SHOWN`, not HD's row count — and the game's own
        field, never HD's list); HD scrolls its own list (decision 46)
        where the star has a row. Without PLSM nothing is sent and only
        HD's list scrolls.
        UNVERIFIED `star_click_live`: the field sent and the box seen live
        — no live runs (Data, 20 October 2026)."""
        b = planetsend.block(self._state)
        if b is not None:
            stars = b["fields"]["stars"]
            field = stars[star] if 0 <= star < len(stars) else -1
            live = {getattr(f, "index", None)
                    for f in (getattr(self._state, "fields", None) or [])}
            if b["total"] > planetsblock.ROWS_SHOWN and field >= 0 \
                    and field in live:
                log.info("Planets: star %d's icon -> field %d", star, field)
                if self.app.connected:
                    self.app.client.activate_field(field)
        if len(self._list.rows) <= self.visible:
            return
        row = self._list.first_row_of_star(star)
        if row > -1:
            self._first = row

    def _scroll(self, step):
        """The up/down buttons move one row when there are more than eight
        (plntsum.cpp:2030-2038), clamped at both ends."""
        total = len(self._list.rows)
        if total > self.visible:
            self._first = max(0, min(total - self.visible, self._first + step))
        return None

    def _return(self):
        fields = getattr(self._state, "fields", None) or []
        field = next((f for f in fields if f.hotkey == KEY_ESC), None)
        if field is not None:
            log.info("Action: return (field %s)", field.index)
            if self.app.connected:
                self.app.client.activate_field(field.index)
            return
        log.warning("No esc field in the field list; sending the key")
        if self.app.connected:
            self.app.client.inject_key(KEY_ESC)

    def handle_mouse_motion(self, screen_x, screen_y):
        super().handle_mouse_motion(screen_x, screen_y)
        pos = (screen_x, screen_y)
        area = planetdraw.window(self, "rows")
        self._hover = None
        if area and area.collidepoint(pos):
            # The band the row was DRAWN in (decision 5, work order 128 D).
            band = listgrid.band_at(planetdraw.row_bands(self), screen_y)
            index = self._first + band if band is not None else -1
            if 0 <= index < len(self._list.rows):
                row = self._list.rows[index]
                self._hover = index
                self._selected = row["index"]
                self._scanned = row["star"] + 1000   # plntsum.cpp:1314
            return
        star = planetdraw.inset_star_at(self, self._inset_stars(), *pos)
        if star is not None:
            self._scanned = star + 1000               # plntsum.cpp:2066-2068

    def handle_mousewheel(self, direction, mx, my):
        """HD EXTENSION (layout.json list._hd_extension_wheel): one row per
        notch over the list or its scroll column. Sends nothing."""
        if super().handle_mousewheel(direction, mx, my):
            return True
        if not (self._hit("rows", (mx, my)) or self._hit("scroll", (mx, my))):
            return False
        self._scroll(-direction)
        return True

    def _hit(self, name, pos):
        rect = planetdraw.window(self, name)
        return bool(rect) and rect.collidepoint(pos)

    def _inject(self, spec, what):
        """Hotkey first, native click as the fallback (colony_summary's
        `_inject`, whose docstring carries the live verification)."""
        hotkey = (spec or {}).get("hotkey")
        if isinstance(hotkey, str) and len(hotkey) == 1:
            log.info("Action: %s -> hotkey %r", what, hotkey)
            if self.app.connected:
                self.app.client.inject_key(ord(hotkey))
            return
        point = (spec or {}).get("native_click")
        if not point or not (0 <= point[0] < NATIVE_W
                             and 0 <= point[1] < NATIVE_H):
            log.warning("No usable native click for %s: %s", what, point)
            return
        log.info("Action: %s -> native click %s", what, point)
        if self.app.connected:
            self.app.client.inject_click(*point)
