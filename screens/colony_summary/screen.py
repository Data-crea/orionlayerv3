"""Colony Summary — orion2re SCREEN_COLONY_SUMMARY (id 20).

The original's "Colonies" list: every colony in a row with its
population split into farmers, workers and scientists, sortable by
seven keys, with the empire totals on the right (colsum.cpp).

Layout: one cockpit frame PNG (assets/frame.png) with transparent
cutouts, stretched over the 1920x1080 reference area and drawn above
everything else — the same construction as the galaxy map. The
boxes in boxes.json ARE the cutouts, derived by tools/frame_holes.py:
  list_area       the colony rows (population bars: next step)
  sidebar         the six empire readouts
  output_panel    per-colony food/industry/research — TRANSCRIPTION
                  (COLSUM::Draw_Colony_Scan_Info_, colsum.cpp:1155);
                  the earlier HD EXTENSION marking is withdrawn, see
                  below and fundament 43
  galaxy_inset    the original's small galaxy map, the RIGHTMOST of
                  the three bottom holes — TRANSCRIPTION, drawn from
                  colsum.cpp:415, native (380, 349, 128, 91); see
                  `colonyinset` for what it does NOT draw
  spare_panel     reserved; the MIDDLE hole, over the native column
                  output_panel already answers for
  return          RETURN
  sort_*          the seven sort buttons
The title cutout is not a box; it lives in layout.json ("frame").

Input goes to the original without ever touching the field list. Two
paths, and which one is taken is a property of the button:

  a HOTKEY, where the original gives the button one. The seven sort
  buttons do (`n p f i s r b` in layout.json), so a sort sends
  `INJECT_KEY` and nothing else. Preferred because it moves nothing:
  `INJECT_CLICK` arrives as an SDL button event, and platform.cpp:1171
  feeds its coordinates to `Set_Present_Mouse_Position_` and
  platform.cpp:1172 enqueues them as a mouse input event, so the
  game's pointer is left standing on whichever button we clicked. The
  key path (platform.cpp:1131) touches neither.

  a NATIVE CLICK otherwise, and as the fallback for a button whose
  hotkey is missing or malformed. `native_click` is a point inside
  the original's own button, taken from its `Add_*_Field_` call with
  a line number (colsum.cpp:265-273) — checkable by a grep, needing
  no live session, and surviving a field list that shifts. RETURN
  takes this path: its field carries a hotkey byte of 0x25, which is
  not a letter anybody can be asked to press.

Both are decision 39's trade: `INJECT_CLICK` carries window
coordinates (open fix 3), so the click path holds at a 640x480
window. The key path has no such constraint, which is a second
reason to prefer it.

Data: the sidebar is transcribed from COLSUM::Draw_Empire_Info_
(colsum.cpp:418), six lines, each one s_player field. Every file:line
in this module and in layout.json's `empire` block was read in
orion2re 1.60; a 1.31 archive numbers them differently, and that
block carries the same warning. The draw order, the labels, the ESTR
ids, the per-row sign rule and the red-if-negative on Income are all
the original's and all carry their source there. `warn_negative` on
Food and Freighters is an HD EXTENSION and marked there — the
original reddens Income alone.

The row layout is SETTLED since 2 September 2026 and the renderer
draws it: one row per entry, label left and value right, because the
two per-line prefixes are justification codes (1A 30 / 1A 31). The
argument and its sources live in `layout.json` under
`empire._justify_note`; what is still open is the column WIDTH, not
the alignment, and that is `colonyempire.value_column.__doc__`
(decision 44).

**`output_panel` is a TRANSCRIPTION — the earlier marking here was
wrong and is withdrawn (fundament 43).** It is to show the selected
colony's food, industry and research, and this module claimed the
original draws none of the three per colony. It draws all four.
`COLSUM::Draw_Colony_Scan_Info_` (colsum.cpp:1155), reached from
`Draw_Scan_Info_` at colsum.cpp:485, loops `i < ECON_COUNT` calling
`Draw_Colony_Wee_Prod_(_g_colony_n, i, 106, y_pos, 366, 20)` with
`y_pos` stepping 18, then adds morale at (106, 421); that path ends
in `COLDRAW::Draw_Colony_Prod_Both_` (coldraw.cpp:36), which reads
`colony->production[prod_type]` (coldraw.cpp:60) and draws it as
tens-and-units sprites. Native x 106, y 349 upward — the bottom-left,
which is where `output_panel` is.

The claim came from grepping THIS FILE for the words
"food|industry|research". The call site has none of them: the value
is picked by a loop index against `ECON_COUNT`, and the drawing lives
in `coldraw.cpp`. Searching for `production[` would have found it at
once. A wrong marking defended by a smoke check is worse than no
marking, and this one was.

What the panel still owes is the OTHER half of that box: the seven
values `E_Strings_(74)` carries (colsum.cpp:1196-1205), of which the
HD row already draws three. See `colonylist._draw_name_block` and the
module docstring there.

The list waits on nothing now — `s_colony` is verified.
"""
import logging

import pygame

from core import mouse as mouse_input
from core import palette
from core.config import REF_W, REF_H
from core.screen_base import ScreenBase
from core.structs import player as player_struct

from . import (colonybuild, colonyempire, colonyfigures,
               colonyheader, colonyinset, colonylist,
               colonymoveui, colonyoutput, colonyrows, colonyscroll,
               colonyplates, colonyselect, colonysort, colonytrack)

log = logging.getLogger("colony_summary")

PANEL_BG = palette.col("colony_summary", "panel_background", (8, 11, 20))
NAV_BG = palette.col("colony_summary", "nav_background", (10, 14, 26))
NAV_HOVER_BG = palette.col("colony_summary", "nav_hover", (22, 34, 60))
NAV_ACTIVE_BG = palette.col("colony_summary", "nav_active", (30, 48, 88))
HEADER_OUTLINE = palette.col("panel", "thin_border", (55, 65, 85))
HEADER_TEXT = palette.col("colony_summary", "label", (150, 168, 200))
NAV_TEXT = palette.col("colony_summary", "nav_text", (196, 208, 236))
#: The sort row's seven words, ALL SEVEN THE SAME — 12 September 2026.
#: The original's own inactive label, measured on its framebuffer
#: (colsum.cpp:267-273 draws all seven from one field). It was
#: `NAV_TEXT` with `nav_text_dim` for a key this build cannot honour;
#: see `colonysort.render` for why the dimming went. The palette key
#: `nav_text_dim` stays — `colonyoutput` draws its empty rows with it.
SORT_TEXT = palette.col("colony_summary", "sort_text", (196, 196, 196))
TITLE_COLOR = palette.col("colony_summary", "title", (200, 210, 238))
MOVE_TEXT = palette.col("colony_summary", "move_text", (206, 216, 238))

#: The native screen the original draws under this one. Defined in
#: `colonyempire`, which is the module that scales BY it; `_inject`
#: only bounds-checks against it, and one home beats two.
NATIVE_W, NATIVE_H = colonyempire.NATIVE_W, colonyempire.NATIVE_H


class ColonySummaryScreen(ScreenBase):
    SCREEN_NAME = "colony_summary"
    GAME_SCREEN_ID = 20         # SCREEN_COLONY_SUMMARY
    USE_FRAME = False           # own frame PNG, see _render_frame_image
    FRAME_TITLE = "Colonies"

    def __init__(self, app):
        super().__init__(app)
        self._data = {}
        self._frame = None
        self._frame_scaled = None
        self._frame_pos = (0, 0)
        self._local = None          # parsed s_player of the local player
        self._sort_key = "name"     # what the original starts on
        self._state = None          # last snapshot, for the list
        # The rows for `_state` + `_sort_key`, and which COLONY is
        # selected — a colony index and never a row index, which is
        # `colonyselect`'s whole subject.
        self._selection = colonyselect.Selection()
        # Which slice of those rows is on screen. VIEWING ONLY —
        # nothing on this screen sends it anywhere (decision 46).
        self._window = colonyselect.Window()
        # The pop move, click-click. The first click is LOCAL and
        # reaches no client — see `colonypick`, which is where the
        # reason lives — and the second one sends both clicks.
        self._move = colonymoveui.MoveController()

    # ── Lifecycle ─────────────────────────────────────────

    def enter(self, game_state=None):
        super().enter(game_state)
        self._data = self.app.res.load_json(
            "screens/colony_summary/layout.json", {}) or {}
        self._sort_key = self._data.get("sort", {}).get("default", "name")
        self._load_frame()
        # A selection does not survive leaving the screen, because in
        # the game it could not: leaving is one of the two
        # `Clear_Cluster_` paths (colsum.cpp:804 and :938), so a pick
        # carried across would describe a state the original has
        # already discarded — and an in-flight send would be waiting
        # for an effect nobody is going to produce.
        self._move = colonymoveui.MoveController()
        self.update(game_state)
        # THE SIX COLUMN BOXES BECOME THE COLUMN TABLE, once, on
        # load: what is bound is the live `Box` objects, so a drag in
        # the F5 editor moves the cells, the plates, the drop rects
        # and the heading above them on the same frame. `colonyheader`
        # draws the plates from the same rects `colonytrack` lays the
        # cells in, so a heading is over its own column by
        # construction and not by two numbers that agree today.
        colonyheader.install_columns(self)
        self._push_sort_key()

    def _push_sort_key(self):
        """SET the game's sort order instead of reading it.

        `_g_sort_index` is not on the wire — the snapshot carries
        settings, players, stars, ships, colonies, planets, nebulas,
        leaders, antarans and ship icons (ext_api.cpp:53-136) and no
        screen state — so the HD list and the original's could sit on
        different keys with neither being wrong. The first real
        side-by-side showed exactly that: the game on Population, HD
        on Name, and two correctly sorted lists that did not match.

        **A state you establish yourself does not have to be read.**
        Sending our own key once, on entry, makes the two agree by
        construction: every later change goes through `handle_click`,
        which injects as it goes, so there is no second path that
        could drift them apart. That is the same trade as parking the
        galaxy map at maximum zoom-out (decision 35) and as the
        scroll window — the alternative was four lines of C++ in
        somebody else's tree to report a number we can simply impose,
        which is decision 36's line.

        Idempotent by the original's own design: `Switched_cmp_` has
        no direction toggle (colsum.cpp:378-401), so re-sorting by
        the key the game already holds re-sorts identically. Entering
        the screen repeatedly costs one keystroke and changes
        nothing.

        It is a no-op while disconnected, and deliberately not
        retried: `_inject` sends nothing without a client, and a
        screen that is up without a game has no original behind it to
        disagree with.
        """
        for spec in self._data.get("sort", {}).get("buttons", []):
            if spec["key"] == self._sort_key:
                self._inject(spec, f"entry sort {spec['key']}")
                return

    def update(self, game_state=None):
        if game_state is None:
            return
        # Kept whole for the list, which needs colonies, planets and
        # stars together; the sidebar only ever wanted the local
        # player's record.
        self._state = game_state
        # ADVANCE FIRST, THEN BUILD. A chain that finished this frame
        # releases the pick, and the rows carry the held cluster —
        # built in the other order they would show pops in hand that
        # nothing is holding, for one frame, every time a move lands.
        self._move.advance(game_state, self._move_words())
        self._rebuild_rows()
        raws = getattr(game_state, "player_raw", None) or []
        players = [player_struct.parse(r) for r in raws
                   if len(r) >= player_struct.SIZE]
        idx = getattr(game_state, "player_num", 0)
        self._local = players[idx] if 0 <= idx < len(players) else None

    def on_resize(self):
        super().on_resize()
        self._scale_frame()

    # ── Selection ─────────────────────────────────────────
    #
    # The state machine and the two rules that move it live in
    # `colonyselect`; what stays here is the geometry, because the
    # screen is what owns the boxes. `_rows` and `_selected` are
    # properties over it so nothing else in this file has to know
    # which object holds them.

    def _rebuild_rows(self):
        """Rebuild the rows, held cluster included.

        `_move.held()` is what turns a local selection into the
        original's own picture: those pops lose `0x200` and stop
        being icons, so the row shortens, its pitch shortens with it
        and the hit test agrees — one list, three readers
        (decision 5). Called from every path that can CHANGE the
        selection as well as from `update`, because the hover has to
        hit-test the rows that were drawn.
        """
        self._selection.rebuild(self._state, self._sort_key,
                                colonybuild.names_for(self),
                                held=self._move.held())

    @property
    def _rows(self):
        return self._selection.rows

    @property
    def _selected(self):
        return self._selection.colony

    def _frame_inset(self):
        """Reference px this screen keeps between text and the frame.

        One key for the whole screen, not one per block: the sidebar
        and the colony list both put text against a cutout edge and
        both need the same number. See `_frame_inset_note` in
        layout.json for what it was measured against.
        """
        return self._data.get("frame_inset",
                              colonyempire.FRAME_INSET_DEFAULT)

    def _list_view(self):
        """(area, cfg, scale, n_rows) — everything `Window` needs.

        The screen owns the boxes, so resolving `list_area` to screen
        pixels stays here; how many rows fit in it, which one is on
        top and which one a point lands on are all the OFFSET's
        business and live on `colonyselect.Window`. This is the whole
        of the seam between the two.

        **THE COLUMN REBIND HAPPENS HERE, and that is why it is here
        and not in `_render_list` — 9 September 2026.** `sync_columns`
        holds the six boxes to this window and rebinds the table to
        the boxes the screen currently HAS, which
        `ScreenBase.on_resize` replaces wholesale. Doing it in the
        renderer made the drawn frame right and left every hit test
        that ran before it reading the previous window — and a click
        arriving in the same event batch as a resize is exactly that.
        This is the seam every reader goes through, drawing and
        clicking alike, which is the only place decision 5 is
        actually enforceable.
        """
        colonyheader.sync_columns(self)
        box = self.box_rect("list_area")
        return (pygame.Rect(*self.layout.rect(box)) if box
                else pygame.Rect(0, 0, 0, 0),
                self._data.get("list", {}), self.layout.scale,
                len(self._rows))

    @property
    def _first(self):
        """The topmost drawn row — `Window.top`, which clamps."""
        return self._window.top(*self._list_view())

    def selected_row(self):
        return self._selection.row()

    def selected_position(self):
        return self._selection.position()


    # ── The pop move ──────────────────────────────────────
    #
    # Click-click, like the original (colsum.cpp:851-870). The state
    # between the two clicks, the rules and the wire sequence are
    # `colonymoveui`'s; what stays here is what the screen owns — the
    # boxes, the wording out of layout.json, and the client.

    def _move_words(self):
        """The wording, from layout.json (decision 15)."""
        return self._data.get("move", {})

    def save_geometry(self):
        """The F5 editor's write-back, and the ONE path it takes.

        Called by `Editor._save` the way `save_races` already is. What
        it writes is `layout_reference.json` and never `boxes.json`:
        that file carries no rectangle for this screen and
        `colonyplates.reseat` rebuilds every one at the next start, so
        a rect saved there would be overwritten before it was drawn.
        Only the boxes `_editor_free` names — RETURN today — because
        every other box on this screen is a cutout the editor refuses
        to move.
        """
        return colonyplates.write_back(self)

    def _reload_boxes(self):
        """The base's load, then the cutouts re-derived from the
        reference — see `colonyplates.box_rects` for why the file on
        disk is a cache and not the authority."""
        super()._reload_boxes()
        if self.boxes:
            colonyplates.reseat(self)

    def _render_move(self, surface):
        """Everything the move draws — `colonymoveui.render_for`.

        **THE BODY MOVED OUT ON 9 September 2026.** Three layers had
        accumulated here — the hover popup, the stranded notice and a
        refusal in `planet_info` — each needing the same four
        arguments assembled from this screen, and none of them
        anything the screen decides. `colonymoveui` owns the move; it
        owns what the move draws, the same seam `colonyoutput` and
        `colonyheader` already take. What stays here is the boxes,
        which is what a screen is for.
        """
        colonymoveui.render_for(self, surface, MOVE_TEXT, PANEL_BG)

    # ── Frame ─────────────────────────────────────────────

    def _load_frame(self):
        """The frame; stretched over the reference area so its holes
        coincide with the boxes measured out of them.

        ONE FILE AND NO SWITCH since Phase B (12 September 2026).
        `colonyframe` chose between a built plate and this, and
        `frame_preview` said which; both are gone with the plate
        machinery. What is left is a load, a scale and a blit, which
        is what that module's own docstring said the two paths shared.
        """
        path = self.asset_path("assets",
                               self._data.get("frame", {}).get(
                                   "image", "frame.png"))
        self._frame = (pygame.image.load(path).convert_alpha()
                       if path else None)
        self._scale_frame()

    def _scale_frame(self):
        if self._frame is None:
            self._frame_scaled = None
            return
        x, y, w, h = self.layout.rect((0, 0, REF_W, REF_H))
        self._frame_scaled = pygame.transform.smoothscale(self._frame, (w, h))
        self._frame_pos = (x, y)

    # ── Rendering ─────────────────────────────────────────

    def render(self, surface):
        self._render_background(surface)
        self._render_panels(surface)
        self._render_list(surface)
        # BOTH HALVES OF THE ORIGINAL'S SCAN BOX IN ONE CALL,
        # because `Draw_Colony_Scan_Info_` (colsum.cpp:1155) is one
        # function: the description paragraph at native
        # (13, 354, 80, 88) and the production rows from native
        # x 106. Splitting it across two screen methods had put both
        # into the right-hand hole with the left one empty.
        colonyoutput.render_for(self, surface)
        self._render_inset(surface)
        self._render_sidebar(surface)
        self._render_move(surface)
        self._render_buttons(surface)
        self._render_frame_image(surface)
        self._render_return(surface)
        self._render_header(surface)
        self._render_title(surface)
        # LAST, OVER THE FRAME. `COLMOVE::Draw_Cluster_(
        # mouse::Pointer_X_(), mouse::Pointer_Y_())` is the final
        # call of `Draw_Colony_Summary_Screen_` (colsum.cpp:506-511),
        # after `Draw_Visible_Fields_` and inside a window set to the
        # whole screen (colmove.cpp:15-16). `core.mouse.pos()` and
        # not pygame's own: in fullscreen the window is letterboxed
        # and the raw pointer is in DESKTOP coordinates, which would
        # hang the figures a border's width from the cursor at
        # exactly the resolution nobody checks.
        _area, _cfg, _scale, _n = self._list_view()
        _step = colonytrack.figure_step(_area, _cfg)
        _first = self._window.top(_area, _cfg, _scale, _n)
        self._move.draw_held(
            surface, self._rows, mouse_input.pos(),
            colonyfigures.set_for(self, _area, _cfg), _step,
            lambda _ink: colonytrack.held_figure_y(
                _area, _cfg, _scale, _n - _first, mouse_input.pos(),
                _step, _ink))

    def _render_return(self, surface):
        """RETURN, AFTER THE FRAME — 12 September 2026, Data's new
        artwork. It is drawn with the header plates and for the same
        reason: this frame cuts no hole for it, so a plate laid with
        the other buttons went straight under the metal and the button
        vanished — three lamps of artwork where the word should be.
        The seven sort keys stay UNDER the frame, because each has a
        hole and the frame's rim is what finishes their edges."""
        colonysort.render_return(surface, self, mouse_input.pos(), NAV_BG,
                                 NAV_HOVER_BG, NAV_TEXT, HEADER_OUTLINE)

    def _render_header(self, surface):
        """The five column headings — see `colonyheader` for the two
        DEVIATIONS they carry (the window is ours; the outline colour
        is ours). Drawn AFTER the frame, because the plates sit inside
        the header cutout and the frame's rim overlaps it."""
        colonyheader.render_for(self, surface, HEADER_OUTLINE, HEADER_TEXT)

    #: What a column box means, for the F5 info bar. Delegated to
    #: `colonyheader`, which owns the column boxes: the line is
    #: entirely about geometry this screen does not compute.
    editor_note = colonyheader.editor_note

    def _render_frame_image(self, surface):
        """The frame, over the content and under the header plates."""
        if self._frame_scaled is not None:
            surface.blit(self._frame_scaled, self._frame_pos)
        elif self.USE_FRAME:
            self._render_frame(surface)

    def _render_title(self, surface):
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

    def _render_panels(self, surface):
        """Every cutout that shows content gets the panel fill, so the
        frame never sits over raw background — `colonyplates
        .render_fills`, which owns what a fill is and whether it is
        square or rounded."""
        colonyplates.render_fills(self, surface)

    def _render_list(self, surface):
        """The colony list. The bar is an INVENTION — see colonylist.

        Read-only: the rows come out of the snapshot and nothing here
        sends anything to the game. Static for now, by design; the
        hover band and the draggable dividers belong on a picture
        somebody already believes.
        """
        # The six column boxes are held to the window's own y and
        # height by `_list_view`, which every reader goes through —
        # see there for why the rebind moved out of this renderer.
        box = self.box_rect("list_area")
        if not box:
            return
        cfg = colonybuild.list_cfg(self)
        colonylist.render(surface, self._rows,
                          pygame.Rect(*self.layout.rect(box)),
                          cfg, self.layout, self.style, self._first,
                          self._frame_inset(),
                          colonyfigures.set_for(
                              self, pygame.Rect(*self.layout.rect(box)),
                              cfg),
                          # ONE SOURCE WITH THE DESCRIPTION PANEL.
                          # `_selected` IS `_g_colony_n`'s
                          # transcription (`colonyselect`), and it is
                          # what `_render_info` hands the panel — the
                          # original drives both from that one state
                          # (colsum.cpp:554 and :1155), so giving the
                          # name colour a hover of its own would be
                          # two answers to one question.
                          self._selected)

    def _render_inset(self, surface):
        """The original's small galaxy map — a TRANSCRIPTION.

        `COLSUM::Draw_Galaxy_Map_` (colsum.cpp:415) is one call into
        `MOVEBOX::Draw_Galaxy_Map_Box_` with view_mode 3, and the
        label under it is `Draw_Scan_Info_`'s (colsum.cpp:86). The
        positions and the colour rule are `colonyrows`', the drawing
        is `colonyinset`'s, and what is NOT drawn — the scanned
        star's animation, the star fields, the population-transfer
        connect line — is recorded there.

        Display only. Nothing here reaches the game, which on this
        screen is a rule and not an accident (decision 46).
        """
        box = self.box_rect("galaxy_inset")
        if not box or self._state is None:
            return
        colonyinset.render(
            surface, colonyrows.galaxy_inset_stars(self._state),
            colonyrows.galaxy_inset_label(self._state, self._selected),
            pygame.Rect(*self.layout.rect(box)),
            self._data.get("inset", {}), self.layout, self.style)

    def _render_sidebar(self, surface):
        """The six empire readouts. Everything about them, including
        the clamp that is decision 44's marked DEVIATION, is in
        `colonyempire` — this hands over the box, the config block
        and the parsed `s_player` and nothing else."""
        colonyempire.render(
            surface, self.box_rect("empire_stats"),
            self._data.get("empire", {}), self._local,
            self.layout, self.style, self.box_font_scale_stored("empire_stats"),
            self._frame_inset())


    def _render_buttons(self, surface):
        """The seven sort keys: the frame provides the bezel, so
        each box gets a fill plus its label; hover brightens it and
        the active sort key stays lit. The seven sort keys have a
        cut-out each since 12 September 2026, and their panel fill
        arrives with every other cutout's through `_render_panels` —
        this method draws the highlight and the word and nothing
        underneath them.

        **The active header does not indicate a direction, because
        the original has none.** `Switched_cmp_` (colsum.cpp:378-401)
        bakes the sign into each `case` as a literal — five of the
        seven descending, Name and Producing ascending — and there is
        no toggle anywhere: clicking the lit header re-sorts
        identically. No arrow is drawn for that reason, and its
        absence is a transcription rather than an omission.

        A key this build cannot honour is drawn LIKE THE OTHER SIX
        since 12 September 2026 — see `colonysort.render`. It still
        injects its click, because the original's own list behind us
        sorts perfectly well and the injection is what keeps the two
        screens agreeing; what it cannot do is reorder OUR rows, and
        `colonyrows.SORT_UNAVAILABLE` is still what says so to
        everything that asks.
        """
        mouse = mouse_input.pos()
        colonysort.render(surface, self._sort_buttons(), self._sort_key,
                          mouse, self.style, colonysort.font_size(self),
                          NAV_ACTIVE_BG, NAV_HOVER_BG, SORT_TEXT)

    def _sort_buttons(self):
        """The seven keys, one `sort_<key>` box each — see
        `colonysort.for_screen`, which is their ONE geometry."""
        return colonysort.for_screen(self)

    def box_style(self, name):
        for box in self.boxes:
            if box.name == name:
                return box.style
        return {}

    # ── Input ─────────────────────────────────────────────

    def handle_click(self, screen_x, screen_y):
        if colonyscroll.handle(self, screen_x, screen_y):
            return
        if self._move.busy:
            # A move is on the wire. Every other button on this
            # screen injects something — a sort re-orders the game's
            # own list and resets `_first` (colsum.cpp:829-838), and
            # RETURN leaves the screen, which is one of the two
            # `Clear_Cluster_` paths — so a click accepted now would
            # move the ground under a chain that has already sent its
            # first click.
            return None
        for spec in self._data.get("sort", {}).get("buttons", []):
            if spec["key"] == colonysort.button_at(
                    self._sort_buttons(), screen_x, screen_y):
                # No direction toggle, even on the active header:
                # Switched_cmp_ has none (colsum.cpp:378-401), so a
                # second click re-sorts identically. Assigning the
                # same key again IS the transcription.
                self._sort_key = spec["key"]
                # Re-sort now, so the rows the next hover hit-tests
                # are the rows about to be drawn. The SELECTION
                # survives it — `_reseat_selection` keeps the colony
                # and lets its row move, which is what the original
                # does by not touching `_g_colony_n` here at all
                # (colsum.cpp:830-837).
                self._rebuild_rows()
                # The original scrolls back to the top on any sort
                # click — `_first = 0` at colsum.cpp:832, inside the
                # same handler that deliberately does NOT touch
                # `_g_colony_n` (colsum.cpp:830-837). Two rules for
                # one event: the window goes home, the selection
                # keeps its colony and moves with the new order.
                self._window.reset()
                why = colonyrows.SORT_UNAVAILABLE.get(spec["key"])
                if why:
                    log.info("Sort %r not applied to the HD rows: %s",
                             spec["key"], why)
                self._inject(spec, f"sort {spec['key']}")
                return None
        if self._hit("return", screen_x, screen_y):
            self._inject(self._data.get("return", {}), "return")
            return None
        area, cfg, scale, _n_rows = self._list_view()
        row_index = self._window.row_at(area, cfg, scale, _n_rows,
                                        (screen_x, screen_y))
        if row_index is not None and self._move.click(
                rows=self._rows, row_index=row_index, x=screen_x,
                state=self._state, area=area, cfg=cfg, scale=scale,
                sort_key=self._sort_key, words=self._move_words(),
                client=self.app.client, connected=self.app.connected,
                sort_hotkey=colonymoveui.sort_hotkey(
                    self._data.get("sort", {}).get("buttons", []),
                    self._sort_key)):
            # The selection may have appeared or gone. Rebuild NOW,
            # not at the next snapshot: the rows carry the held
            # cluster, so the picture and the next hover would
            # otherwise be a frame behind the click that changed it.
            self._rebuild_rows()
            return None
        if row_index is None:
            # Off the rows — and a held selection is DISCARDED here.
            # HD EXTENSION, argued in `_cancel_pick` and
            # `colonypick`: nothing has been injected, so there is
            # nothing on the other side of the wire to undo.
            self._move.cancel("clicked off the rows")
            self._rebuild_rows()
        if row_index is not None:
            # DELIBERATELY INERT, and that is worth a comment because
            # the original does something substantial here: clicking a
            # row's name field sets `MOX::_current_screen =
            # SCREEN_COLONY` and hands over the star and orbit
            # (colsum.cpp:912-920), so the click leaves this screen
            # for the colony screen. Clicking the PRODUCING text goes
            # somewhere else again, to SCREEN_QUEUE_POPUP
            # (colsum.cpp:922-944).
            #
            # Neither destination has an HD screen yet, and sending
            # the injection anyway would move the game to a screen the
            # HD side cannot draw — the fallback would take over and
            # the player would be looking at 640x480 with no way back
            # that this screen knows about. So the click is swallowed
            # here rather than passed on.
            #
            # It is swallowed and NOT left to fall through, because
            # falling through is the version that looks the same today
            # and stops looking the same the moment anything else
            # claims that area. An absence that is written down is a
            # state; an absence that happens to work out is a bug
            # waiting for its second cause.
            #
            # The hover has already moved the selection by the time a
            # click arrives, so a player who clicks a row does see the
            # panel change — which reads as the click working. That is
            # the honest risk in leaving it inert, and it is the
            # reason this comment is longer than the branch.
            return None
        return super().handle_click(screen_x, screen_y)

    def handle_right_button(self, down, screen_x, screen_y):
        """Help first, then discard a held selection.

        The ORDER is transcribed. `fields::Get_Input_()` checks the
        active help list before it lets the right button mean Cancel
        (`Check_Help_List_`, fields.cpp:2916): over a help rectangle
        the entry is drawn and the click is swallowed, and only
        outside one does the right button return -1. So the base
        class's help handling runs first and this only sees the
        clicks it did not want.

        The discard itself is the **HD EXTENSION** — the original has
        no cancel that stays on this screen at all. See
        `colonymoveui` and `colonypick`.
        """
        if super().handle_right_button(down, screen_x, screen_y):
            return True
        if not down or self._move.pick is None:
            return False
        self._move.cancel("right click")
        self._rebuild_rows()
        return True

    def handle_mouse_motion(self, screen_x, screen_y):
        """Hover selects, which is the original's own behaviour.

        TRANSCRIBED. `Evaluate_Colony_Pop_Input_` takes the CLICKED
        field and the SCANNED one separately, and it is the scanned
        one that moves the selection: over a row's name, producing or
        buy field it assigns `COLONY::_g_colony_n = colony_id`
        (colsum.cpp:880-890). "Scanned" is this engine's word for
        hovered — `fields::Scan_Input_` returns the field under the
        pointer (fields.cpp:652), with no button involved.

        Leaving the list does NOT clear the selection, and that is
        the source too: the assignment has no else branch, so
        `_g_colony_n` keeps whatever it last held. The scan box goes
        on showing the last colony the pointer crossed, which is what
        makes it readable at all — a panel that emptied whenever the
        mouse moved off the list would be blank most of the time.
        """
        super().handle_mouse_motion(screen_x, screen_y)
        area, cfg, scale, n_rows = self._list_view()
        row = self._window.row_at(area, cfg, scale, n_rows,
                                  (screen_x, screen_y))
        self._selection.hover(row)
        # The popup rides the same hover the original scans with; the
        # controller is what refuses one while a selection is up.
        self._move.hover(self._rows, row, screen_x, area, cfg, scale)

    def handle_mousewheel(self, direction, mx, my):
        """Scroll the colony list, one row per notch.

        **HD EXTENSION.** MOO2 has no wheel here at all: the original
        moves its window with two step buttons either side of a
        proportional slider (`_x_fields[1]` and `_x_fields[2]`,
        colsum.cpp:790-800; `Draw_Bar_Indicator_`, colsum.cpp:747-753),
        and that slider is NOT DRAWN by this screen — see
        `colonylist`'s module docstring, where the omission is
        recorded. Marked here, in `layout.json` under
        `list._hd_extension_wheel`, and in a smoke check.

        **IT SENDS NOTHING TO THE GAME, and that is what makes this
        safe to ship** (decision 46). The original's rows are ten
        SLOTS over the sorted array, so an injected click names a
        position in the GAME's window and `_first` decides which
        colony it reaches; ours is a viewing offset the game has
        never heard of. Every colony is already in the snapshot, so
        scrolling needs nothing from it. What must not happen is an
        injection while the two windows disagree — synchronising them
        is decision 46's other half and is not built. A smoke check
        asserts that no scroll path calls `inject_click`,
        `activate_field` or `inject_key`, so the first edit that adds
        one fails rather than silently sending a click to the wrong
        colony.

        Wheel up is `direction` +1 and moves the window towards row
        0, matching every other scrolling surface in the tree.

        The clamps are `colonyselect.Window`'s and are transcribed
        there; the visible count is derived from `list_area` and is
        never the game's ten.
        """
        if super().handle_mousewheel(direction, mx, my):
            return True        # an open help popup took it
        box = self.box_rect("list_area")
        if not box or not self._rows:
            return False
        if not pygame.Rect(*self.layout.rect(box)).collidepoint(mx, my):
            return False
        _area, _cfg, _scale, _n = self._list_view()
        self._window.scroll(-direction, _n,
                            self._window.visible(_area, _cfg, _scale, _n))
        # The SELECTION is deliberately not touched. It holds a
        # COLONY, not a row index (colsum.cpp:830-837 and
        # `colonyselect`), so moving the window past it changes what
        # is on screen and not what the scan box is showing — the
        # same asymmetry a sort has.
        return True

    def _hit(self, name, x, y):
        box = self.box_rect(name)
        return bool(box) and pygame.Rect(*self.layout.rect(box)).collidepoint(x, y)

    def _inject(self, spec, what):
        """Send `spec` to the original: its hotkey if it has one, else
        a click at its `native_click`.

        The two paths are not interchangeable and the difference is
        invisible from here, which is why the choice is made once, in
        one place, rather than per call site.

        VERIFIED LIVE, 3 September 2026, against orion2re 1.60 on the
        reference save with the Colonies screen up. The check had to
        be done before switching, because a key that is silently
        dropped and a key that works produce the same picture: the
        original re-sorts by a key it already holds without changing
        a pixel (there is no direction toggle), so "nothing moved" is
        the success case AND the failure case. Sorting AWAY from the
        active key is what separates them. `INJECT_KEY` with `p` from
        a name-sorted list moved 15071 of the 640x480 framebuffer's
        pixels; `n` moved them back; `B` and `S` moved it again. The
        game folds case — both `n` (110) and `N` (78) arrive, which
        matters because the field list reports the binding as the
        UPPERCASE byte while layout.json stores the lowercase letter,
        and a future reader "fixing" that mismatch would be fixing
        nothing. A frame taken after the key and a frame taken after
        the equivalent `native_click` came out byte-identical.

        What that live check could NOT show is the pointer, and the
        limit is worth stating rather than leaving as a gap: the
        cursor is composited onto the ARGB present surface
        (platform.cpp:794-822), while the Extension API sends the
        indexed `g_present_surface` (ext_api.cpp:165), so no cursor
        of any kind is on the wire. The claim that a click moves the
        pointer and a key does not rests on platform.cpp:1171-1172
        against platform.cpp:1131-1134, and on nothing else.
        """
        hotkey = (spec or {}).get("hotkey")
        if isinstance(hotkey, str) and len(hotkey) == 1 and hotkey.isascii():
            log.info("Action: %s -> hotkey %r", what, hotkey)
            if self.app.connected:
                self.app.client.inject_key(ord(hotkey))
            return
        if hotkey is not None:
            # Not a fall-through worth staying quiet about: a hotkey
            # that is present but unusable means layout.json changed
            # in a way nobody meant, and the click below would hide it
            # by working.
            log.warning("Unusable hotkey %r for %s, falling back to the "
                        "native click", hotkey, what)
        point = (spec or {}).get("native_click")
        if not point:
            log.warning("No native click point for %s", what)
            return
        nx, ny = point
        if not (0 <= nx < NATIVE_W and 0 <= ny < NATIVE_H):
            log.warning("Native point off screen for %s: %s", what, point)
            return
        log.info("Action: %s -> native click (%d, %d)", what, nx, ny)
        if self.app.connected:
            self.app.client.inject_click(nx, ny)
