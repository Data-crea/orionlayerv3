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
  output_panel    per-colony food/industry/research — HD EXTENSION,
                  see below (later)
  galaxy_inset    the original's small galaxy map (later)
  spare_panel     reserved
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

Stacking the label above its value is a deviation too, and what the
original does instead is currently OPEN rather than known. justify=3
is certainly inert (fmtpara.cpp:1057 drops to JUSTIFY_LEFT before the
CR that joins the six). But the two per-line prefixes turn out to be
justification codes themselves — bytes 1A 30 and 1A 31, and 0x1A is
Set_Justification_, not Set_Current_Colors_ — which sets LEFT for the
label and RIGHT for the value. So the original may well draw
label-left/value-right, which an earlier version of this note called
an invention. Nothing here has been changed on the strength of that;
see `empire._justify_note` for what is settled and what is not.

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

from . import colonylist, colonyoutput, colonyrows

log = logging.getLogger("colony_summary")

PANEL_BG = palette.col("colony_summary", "panel_background", (8, 11, 20))
NAV_BG = palette.col("colony_summary", "nav_background", (10, 14, 26))
NAV_HOVER_BG = palette.col("colony_summary", "nav_hover", (22, 34, 60))
NAV_ACTIVE_BG = palette.col("colony_summary", "nav_active", (30, 48, 88))
NAV_TEXT_DIM = palette.col(
    "colony_summary", "nav_text_dim", (104, 116, 142))
NAV_TEXT = palette.col("colony_summary", "nav_text", (196, 208, 236))
TITLE_COLOR = palette.col("colony_summary", "title", (200, 210, 238))
LABEL_COLOR = palette.col("colony_summary", "label", (140, 155, 190))
VALUE_COLOR = palette.col("colony_summary", "value", (220, 228, 245))
WARN_COLOR = palette.col("colony_summary", "warn", (235, 90, 80))

#: Native screen the original draws under this one (640x480).
NATIVE_W, NATIVE_H = 640, 480


def format_value(value, signed=False):
    """'+12' / '-3' with signed, else plain — the original's %+d / %d."""
    if signed and value >= 0:
        return f"+{value}"
    return str(value)


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
        self._rows = []             # build_rows for _state + _sort_key
        # The SELECTED colony, as its index in the snapshot's colony
        # array — the same number the original keeps in
        # `COLONY::_g_colony_n`, and not a row index. See
        # `_reseat_selection`.
        self._selected = None

    # ── Lifecycle ─────────────────────────────────────────

    def enter(self, game_state=None):
        super().enter(game_state)
        self._data = self.app.res.load_json(
            "screens/colony_summary/layout.json", {}) or {}
        self._sort_key = self._data.get("sort", {}).get("default", "name")
        self._load_frame()
        self.update(game_state)

    def update(self, game_state=None):
        if game_state is None:
            return
        # Kept whole for the list, which needs colonies, planets and
        # stars together; the sidebar only ever wanted the local
        # player's record.
        self._state = game_state
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

    def _rebuild_rows(self):
        """The rows for the current snapshot and sort key, once.

        `_render_list` used to call `build_rows` every frame. It is
        called here instead because the hover has to hit-test the
        SAME list the renderer drew — two lists built from one
        snapshot agree today and would not the first time anything
        about the build depended on when it ran.
        """
        self._rows = colonyrows.build_rows(self._state, self._sort_key)
        self._reseat_selection()

    def _reseat_selection(self):
        """Entry lands on row 0; after that the colony is kept.

        TRANSCRIBED, and the two halves have different sources.

        **Entry is row 0 of the sorted list.** colsum.cpp:139 sets
        `COLONY::_g_colony_n = COLSUM::_list_col[0]` in the screen's
        setup, before the input loop runs — and `_list_col` is filled
        from the sorted `_g_colony_list_ptr` by `Update_Col_List_`
        (colsum.cpp:348-351), so it is the first row as SORTED and
        not the first colony in the array.

        **A sort does not reseat it.** The sort handler
        (colsum.cpp:830-837) re-sorts, clears the window array and
        resets `_first`, and never touches `_g_colony_n`. So the
        selected COLONY is kept and moves to wherever the new order
        puts it — which is why the selection is stored as a colony
        index and not as a row. Storing the row would keep the
        HIGHLIGHT still and change the colony under it, which is the
        opposite behaviour and would look identical on entry.

        A selection whose colony has left the list — it was lost, or
        the snapshot changed under us — falls back to row 0 rather
        than to nothing, because the original has no state in which
        this screen is up and no colony is scanned. Nothing is
        selected only when there are no colonies at all.
        """
        if not self._rows:
            self._selected = None
            return
        if any(row["index"] == self._selected for row in self._rows):
            return
        self._selected = self._rows[0]["index"]

    def selected_row(self):
        """The selected row dict, or None. The panel's whole input."""
        for row in self._rows:
            if row["index"] == self._selected:
                return row
        return None

    def selected_position(self):
        """Where the selection sits in the CURRENT order, or None.

        Only the renderer's highlight and the smoke test want this;
        the selection itself is never stored this way.
        """
        for i, row in enumerate(self._rows):
            if row["index"] == self._selected:
                return i
        return None

    # ── Frame ─────────────────────────────────────────────

    def _load_frame(self):
        """The cutout frame; stretched over the reference area so the
        cutouts coincide with the boxes derived from them."""
        cfg = self._data.get("frame", {})
        path = self.asset_path("assets", cfg.get("image", "frame.png"))
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
        self._render_output(surface)
        self._render_sidebar(surface)
        self._render_buttons(surface)
        self._render_frame_image(surface)
        self._render_title(surface)

    def _render_frame_image(self, surface):
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
        frame never sits over raw background."""
        for name in self._data.get("panels", {}):
            if name.startswith("_"):
                continue
            box = self.box_rect(name)
            if box:
                surface.fill(PANEL_BG[:3], pygame.Rect(*self.layout.rect(box)))

    def _render_list(self, surface):
        """The colony list. The bar is an INVENTION — see colonylist.

        Read-only: the rows come out of the snapshot and nothing here
        sends anything to the game. Static for now, by design; the
        hover band and the draggable dividers belong on a picture
        somebody already believes.
        """
        box = self.box_rect("list_area")
        if not box:
            return
        cfg = self._data.get("list", {})
        colonylist.render(surface, self._rows,
                          pygame.Rect(*self.layout.rect(box)),
                          cfg, self.layout, self.style)

    def _render_output(self, surface):
        """The original's scan box for the selected colony.

        A TRANSCRIPTION — see `colonyoutput`, and fundament 43 for
        why that marking is worth stating rather than assuming. The
        panel draws NOTHING when nothing is selected, which is the
        original's own guard (`_g_colony_n != -1`, colsum.cpp:1165)
        and not a placeholder waiting to be filled.

        The climate words come from the `list` block and the other
        three lists from `words`. They are not merged into one block
        because `list.climates` already had a home and its own
        provenance note, and a second copy that agrees today is the
        screen-ID-map failure waiting to happen. A smoke check
        asserts the ten climate words appear in exactly one of the
        two.
        """
        box = self.box_rect("output_panel")
        if not box:
            return
        colonyoutput.render(
            surface, self.selected_row(),
            pygame.Rect(*self.layout.rect(box)),
            self._data.get("output", {}),
            self._data.get("words", {}),
            self._data.get("list", {}).get("climates", ()),
            self.layout, self.style)

    def _render_sidebar(self, surface):
        """Six rows, label LEFT and value RIGHT — the original's.

        TRANSCRIBED, and it took two passes to read correctly. Each
        entry is built as `<attr>Label: <attr><value>` and the two
        `<attr>` are `ESTRINGS::s_0_0055110c` and `s_1_00551110`.
        Those are not colour codes: they are the bytes `1A 30` and
        `1A 31`, and FMTPARA sends 0x1A to `Set_Justification_`
        (0x1B is `Set_Current_Colors_`, fmtpara.cpp:364-368). The
        1.60 tree spells them a third time, unambiguously and with
        the answer in the comment — `strings.cpp:22`, `"\x1A" "0"`,
        */ switches paragraph justification to left alignment /*,
        and `:24` the same for right.

        So: LEFT for the label, then `Set_Justification_`
        (fmtpara.cpp:999) flushes the label segment when
        `char_count > 0`, then RIGHT for the value —
        `Justify_Line_` mode 1 adds the whole remaining width to the
        first character's advance (fmtpara.cpp:1699). **One row per
        entry, not two:** `Set_Justification_` never advances y, and
        y moves only on \r \n \v \f (fmtpara.cpp:322-341). The CR
        that `String_Builder2_` joins the six with is what ends each
        row.

        The right edge is the paragraph's own: `para.x2 = x + width
        - 1` (fmtpara.cpp:657) over
        `Print_Formatted_Paragraph_(520, 354, 104, ...)`, so 623 of
        640 native. See `_value_column` for how that reaches HD.
        """
        box = self.box_rect("sidebar")
        cfg = self._data.get("empire", {})
        rows = cfg.get("rows", [])
        if not box or not rows:
            return
        rect = pygame.Rect(*self.layout.rect(box))
        surface.fill(PANEL_BG[:3], rect)
        left, right = self._value_column(rect)
        fs = self.box_font_scale("sidebar")
        label_size = self.layout.font_size(int(cfg.get("label_font", 18) * fs))
        value_size = self.layout.font_size(int(cfg.get("value_font", 26) * fs))
        pad = int(rect.h * cfg.get("row_pad", 0.10))
        row_h = (rect.h - 2 * pad) / len(rows)
        for i, row in enumerate(rows):
            top = rect.y + pad + int(i * row_h)
            label = self.style.render_text(row["label"].upper(), label_size,
                                           LABEL_COLOR[:3])
            value, warn = self._empire_value(row)
            # render_text, not font.render: the sign characters are on
            # Bank Gothic DEMO's watermark list and get substituted.
            # Red-if-negative IS the original's and is kept — see
            # `empire._red_note`. It was queried as possibly resting
            # on a mis-transcribed byte; it does not.
            vt = self.style.render_text(
                value, value_size, (WARN_COLOR if warn else VALUE_COLOR)[:3])
            block_h = max(label.get_height(), vt.get_height())
            y = top + (int(row_h) - block_h) // 2
            # Both on ONE row: label flush left, value flush right.
            surface.blit(label, (left, y + (block_h - label.get_height())))
            surface.blit(vt, (right - vt.get_width(),
                              y + (block_h - vt.get_height())))

    def _value_column(self, rect):
        """(left, right) of the row — right is where a value ends.

        The alignment is TRANSCRIBED: the value ends at the column's
        right edge, because the original right-justifies it
        (`para.x2 = x + width - 1`, fmtpara.cpp:657, over
        `Print_Formatted_Paragraph_(520, 354, 104, buffer, 3)` at
        colsum.cpp:418). See `_render_sidebar` for the justification
        codes that establish it.

        **The WIDTH is a DEVIATION, and it is live at every
        resolution.** The original's paragraph is 104 native px of
        640, which is 312 reference px once scaled by
        `REF_W / NATIVE_W`. The `sidebar` cutout gives 286. The
        column is `min` of the two, so the shipped column is always
        the cutout's 286 — the clamp fires everywhere and the
        original's proportion is never the one drawn. Marked in
        `doc/v3_fundament.md` and in a smoke check.

        It is not a rounding difference: 286 against 312 is 8.3 % of
        the column, and every value on the screen sits 26 reference
        px left of where the original's proportion would put it.

        **Both numbers are kept, and the clamp is written to stop
        firing on its own.** The cutout comes from the frame artwork
        via `frame_holes.py` and can move; 104 is the transcription
        and cannot. If a future frame gives this hole 312 reference
        px or more, `min` selects the native width and the deviation
        ends without anybody remembering to come back — which is the
        only reason a clamp is the right shape here rather than a
        note saying "286 for now". The frame art is NOT being changed
        to suit this: that would be deriving geometry from a
        deviation, and the artwork is a separate decision.

        What must not happen is the native number quietly
        disappearing once somebody notices it never wins. The smoke
        check asserts `native_width` is still read and still larger
        than what gets drawn, so deleting it as dead weight fails.
        """
        native_w = self._native_column_width()
        return rect.x, rect.x + min(rect.w, native_w)

    def _native_column_width(self):
        """The original's 104 px paragraph, in this screen's pixels.

        Separate from `_value_column` so the smoke check can ask for
        the unclamped number without re-deriving it, and so deleting
        it breaks a test rather than silently ending the marking.
        """
        return int(self._data.get("empire", {}).get("native_width", 104)
                   * (REF_W / NATIVE_W) * self.layout.scale)

    def _empire_value(self, row):
        """(text, warn). '--' while disconnected, never a fake zero."""
        if self._local is None:
            return "--", False
        value = getattr(self._local, row["field"], None)
        if value is None:
            return "--", False
        warn = bool(row.get("warn_negative")) and value < 0
        return format_value(value, row.get("signed", False)), warn

    def _render_buttons(self, surface):
        """Sort buttons and RETURN: the frame provides the bezel, so
        each box gets a fill plus its label; hover brightens it and
        the active sort key stays lit.

        **The active header does not indicate a direction, because
        the original has none.** `Switched_cmp_` (colsum.cpp:378-401)
        bakes the sign into each `case` as a literal — five of the
        seven descending, Name and Producing ascending — and there is
        no toggle anywhere: clicking the lit header re-sorts
        identically. No arrow is drawn for that reason, and its
        absence is a transcription rather than an omission.

        A key this build cannot honour is drawn DIMMED
        (`colonyrows.SORT_UNAVAILABLE`). It still injects its click,
        because the original's own list behind us sorts perfectly
        well and the injection is what keeps the two screens
        agreeing; what it cannot do is reorder OUR rows. Dimming is
        the difference between an absence that is visible and one
        that is silent.
        """
        mouse = mouse_input.pos()
        unavailable = colonyrows.SORT_UNAVAILABLE
        specs = [(f"sort_{b['key']}", b["label"], b["key"] == self._sort_key,
                  b["key"] in unavailable)
                 for b in self._data.get("sort", {}).get("buttons", [])]
        specs.append(("return",
                      self._data.get("return", {}).get("label", "Return"),
                      False, False))
        for name, label, active, dim in specs:
            box = self.box_rect(name)
            if not box:
                continue
            rect = pygame.Rect(*self.layout.rect(box))
            hovered = rect.collidepoint(mouse)
            fill = NAV_HOVER_BG if hovered else (
                NAV_ACTIVE_BG if active else NAV_BG)
            surface.fill(fill[:3], rect)
            font = self.style.get_font(self.layout.font_size(
                self.box_style(name).get("font_size", 18)))
            colour = NAV_TEXT_DIM if dim else NAV_TEXT
            text = font.render(label.upper(), True, colour[:3])
            surface.blit(text, (rect.x + (rect.w - text.get_width()) // 2,
                                rect.y + (rect.h - text.get_height()) // 2))

    def box_style(self, name):
        for box in self.boxes:
            if box.name == name:
                return box.style
        return {}

    # ── Input ─────────────────────────────────────────────

    def handle_click(self, screen_x, screen_y):
        for spec in self._data.get("sort", {}).get("buttons", []):
            if self._hit(f"sort_{spec['key']}", screen_x, screen_y):
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
                # click — `_first = 0` at colsum.cpp:828. Nothing to
                # reset here yet: the HD list does not scroll, it
                # draws every row that fits. When scrolling arrives
                # this is where the reset goes.
                why = colonyrows.SORT_UNAVAILABLE.get(spec["key"])
                if why:
                    log.info("Sort %r not applied to the HD rows: %s",
                             spec["key"], why)
                self._inject(spec, f"sort {spec['key']}")
                return None
        if self._hit("return", screen_x, screen_y):
            self._inject(self._data.get("return", {}), "return")
            return None
        if self._row_at(screen_x, screen_y) is not None:
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

    def _row_at(self, screen_x, screen_y):
        """Index into `_rows` of the row under the pointer, or None.

        The geometry comes from `colonylist.row_at`, which is the same
        function `colonylist.render` lays the rows out with — one
        source for the rect, per decision 5. A second copy of the
        pitch here is how a list starts highlighting the row above
        the one it draws.
        """
        box = self.box_rect("list_area")
        if not box or not self._rows:
            return None
        area = pygame.Rect(*self.layout.rect(box))
        if not area.collidepoint(screen_x, screen_y):
            return None
        return colonylist.row_at(area, self._data.get("list", {}),
                                 self.layout.scale, len(self._rows),
                                 (screen_x, screen_y))

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
        index = self._row_at(screen_x, screen_y)
        if index is not None:
            self._selected = self._rows[index]["index"]

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
