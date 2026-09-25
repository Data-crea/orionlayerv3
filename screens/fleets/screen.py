"""Fleets — orion2re SCREEN_FLEET (4), `FLT1::Fleet_Screen_` (flt1.cpp:486-837).

HD STATE: **BUILT, NOT ACCEPTED.** No live acceptance has run against
this screen — work order 134's live part is parked in
`doc/briefs/134-parked-for-data.md`, with the exact steps. Decision 61,
and a smoke check fails if this sentence leaves this docstring.

Entered from the galaxy map's Fleets button, which is the only place in
the engine that assigns the id (`mainscr_main.cpp:632-643`); the loop
rebuilds its whole field list every iteration (flt1.cpp:582-585), so
every send identifies its field in the list that is on the wire at the
moment of the click (decision 20) and never by an index remembered from
an earlier one.

**THE SCREEN IS DRAWN, NOT COMPOSED.** The original's picture is one
full-screen image (FLEET.LBX 0) with its slots, rails and button faces
painted in; that art is MOO2's and stays out of this tree, so `fltdraw`
draws all of it. `fltgeom` holds every native rectangle with its source
line, and the wire side still recognises the game's fields by them.

**THE THREE PARAGRAPHS THAT USED TO STAND HERE WERE OUT OF DATE** and
are corrected rather than deleted, because a stale sentence about
where boxes come from is exactly what sends the next session to the
wrong tool. The frame is NOT the Planets artwork with its struts
removed (work order 146 replaced that), it does NOT have one hole, and
`boxes.json` was NOT seeded by `tools/fleet_boxes.py` — that tool is
superseded and must not be run. Decision 3 DOES apply: the frame cuts
32 holes, `tools/frame_holes.py` has a `fleets` rule that refuses any
other shape, and the six boxes with no hole are placed by
`screens/fleets/fltplaced.py` (work order 153). `layout.json`'s
`frame._note` is the full account.
"""
import logging

import pygame

from core.screen_base import ScreenBase

from core import hestrings
from core import kentext
from core import mouse as mouse_input
from core.shipparts import ShipPartNames
from screens.colony_summary import colonyrows

from . import fltart
from . import fltdraw
from . import flthud
from . import fltbox, fltmove, fltpanel, fltgeom, fltrows, fltscan
from . import fltwire

log = logging.getLogger("fleets")


class FleetsScreen(ScreenBase):
    SCREEN_NAME = "fleets"
    GAME_SCREEN_ID = fltgeom.GAME_SCREEN_ID   # 4, orion2_consts.h:465
    USE_FRAME = False        # its own fixed image, not the 9-slice

    def __init__(self, app):
        super().__init__(app)
        self._data = {}
        self._words = {}
        self._first_row = 0      # top row of the big-icon grid HD shows
        self._total_rows = 0     # rows the filtered list needs
        self._icon_count = 0     # big icons the grid is holding
        self._status = ""        # the line under the inset map
        self._state = None       # the snapshot this frame was drawn from
        self._view = None        # fltwire.View: what may be believed
        self._cells = []         # fltrows.Cell per displayed slot
        self._panel = []         # the scanned ship's lines
        self._parts = None       # ship part names (shields, weapons, specials)
        self._hover_cell = None  # slot under the pointer, HD's own hover
        # HD's own `MOX::_scanned_big_ship`: WHICH ship the panel is
        # showing and which cell wears the hover mark. One value for
        # both, because the original has one (work order 153 B).
        self._scan = fltscan.Scan()
        # HD's own `MOX::_galaxy_map_scanned_star`: the star under the
        # pointer in the inset, which is what the strip under the map
        # names (work order 155). -1 is "nothing scanned", and the
        # original prints the strip not at all in that state.
        self._scan_star = -1
        # The game's own artwork, when the player has extracted it.
        # Never committed and never shipped, so `available` is False in
        # a fresh clone and the cells fall back — `fltart` says why.
        self._art = fltart.load()

    # ── Lifecycle ─────────────────────────────────────────

    def enter(self, game_state=None):
        super().enter(game_state)
        self._data = self.app.res.load_json(
            "screens/fleets/layout.json", {}) or {}
        self._words = self._data.get("words", {})
        # MOX::_scanned_big_ship = -1 and _scanned_small_ship = -1 on
        # entry (flt1.cpp:527-528); nothing is scanned, so no status line.
        self._first_row, self._status = 0, ""
        language = (getattr(self.app, "settings", {}) or {}).get(
            "language", "en")
        self._parts = ShipPartNames(language)
        # The original's own wording for the crew word, the two column
        # headings, "none" and the location line (HESTRNGS), and for the
        # weapon firing arcs (KENTEXT.LBX). Both are derived files the
        # player extracts; absent, what depends on them is left out.
        # ONE CONSTRUCTION SITE (D17, work order 159) — this built a
        # fourth copy per screen.
        self._strings = hestrings.for_app(self.app)
        self._arcs = kentext.ArcWords(language)
        self._view, self._cells, self._panel = None, [], []
        self._hover_cell = None
        self._scan.clear()
        self._scan_star = -1
        # No frame image since decision 71: `_load_frame` is not called.
        self.update(game_state)

    def on_resize(self):
        super().on_resize()

    def update(self, game_state=None):
        """Read the snapshot, validate it, and keep only what survived.

        `fltwire.View` does the deciding — it is the module that knows
        why reconstruction does not reach here and what the field list
        can confirm. This method holds no rule of its own; it turns the
        View's answer into the four things the renderer draws.
        """
        if game_state is None:
            return
        self._state = game_state
        self._view = fltwire.View(game_state, fltgeom.native_cells())
        # **A NATIVE BOX KEEPS THE SCREEN UP** (work order 152, items 1
        # and 2). The FLTS block survives a box untouched, so the grid
        # and the panel go on being drawn from it; only the clicking
        # stops, because the screen's fields are not on the wire to
        # send to. Falling through to the clear below is what produced
        # the empty grid Data photographed.
        if self._view.in_box:
            self._cells = fltrows.cells(self._view, game_state)
            return
        if not self._view.ok:
            self._cells, self._panel = [], []
            self._icon_count, self._total_rows, self._first_row = 0, 0, 0
            return
        block = self._view.block
        self._icon_count = len(self._view.rows)
        self._total_rows = max(0, int(block.get("rows", 0)))
        self._first_row = max(0, int(block.get("first_row", 0)))
        self._cells = fltrows.cells(self._view, game_state)
        self._scan.follow(block)
        self._panel = self._panel_for(game_state, block)
        self._status = self._status_line(game_state, block)

    def _panel_for(self, game_state, block):
        """The scanned ship's lines, for whichever ship is scanned.

        `fltscan` decides WHICH — HD's own hover first, then the
        `scanned_big` on the wire — and this only reads it. Everything
        it needs is in the snapshot the screen already holds, which is
        why a hover costs nothing on the wire; `fltscan`'s docstring
        has the reason that is a requirement and not a nicety.
        """
        icon = self._scan.resolve(block)
        ships = block.get("ship_idx") or []
        if not (0 <= icon < len(ships)):
            return []
        return fltrows.panel_lines(ships[icon], game_state, self._parts,
                                   self._strings, self._arcs)

    def _status_line(self, game_state, block):
        """The strip under the inset map.

        **IT NAMES THE STAR HD'S OWN POINTER IS OVER** — work order
        155 — and nothing else. `Print_Fltscrn_Scanned_Star_Name_` is
        called only under `if (_galaxy_map_scanned_star > -1)`
        (flt1.cpp:397), so with nothing scanned the original writes
        the strip not at all and it is empty; `self._scan_star` is
        HD's copy of that variable and -1 means the same thing.

        **WHAT IT DELIBERATELY DOES NOT DO.** With ships selected the
        original's strip is a MOVE PREVIEW, not a name — eight of its
        ten states come from `SHIPMOVE::Ships_Try_To_Move_To_`, which
        is on no wire (the OMISSION `layout.json` carries). Printing
        the star's name there would answer a different question from
        the one the original is answering, so HD says nothing instead.
        `fltrows.scanned_star_line` holds that rule.

        The previous version read `scanned_small` — the small ship
        icon the GAME's pointer is over — and printed that ship's
        star. It was marked an unmarked invention by work order 152
        and it could never move for a client anyway, because the API
        has no mouse motion.
        """
        if self._scan_star < 0:
            return ""
        if int(block.get("selected_count", 0) or 0) > 0:
            return ""
        return fltrows.scanned_star_line(game_state, self._scan_star,
                                         self._strings)

    def wants_original(self):
        """Hand over whenever the View is not READY — decision 22's
        promise one step in, and the same shape the research screen
        uses. A fleet grid drawn without the block would be twenty
        empty slots over a stack that has ships in it, which is worse
        than the original picture and says nothing about why.

        WAITING IS THE ONE EXCEPTION (work order 142 A). The first
        snapshot at screen 4 still carries the galaxy map's field list,
        and handing over for it made the original flash up every time
        the screen opened. It is a frame or two, it ends when the list
        arrives (decision 21, no timer), and HD stays on its own
        picture — empty, because nothing is `ok`, but its own.
        """
        return not (self._view and (self._view.ok or self._view.waiting
                                    or self._view.in_box))

    def _inert(self):
        """True while nothing here may be sent.

        NOT the same question as `wants_original`: WAITING keeps the
        HD picture up AND sends nothing, because a send resolves its
        field in the list it was handed (decision 20) and that list is
        the previous screen's.
        """
        return not (self._view and self._view.ok)

    def fallback_reason(self):
        """The sentence shown when this screen hands over."""
        return self._view.reason if self._view else ""

    @property
    def problems(self):
        return [self._view.reason] if self.wants_original() else []

    # ── Geometry, in one place ────────────────────────────

    def opening(self):
        """The frame's one opening in reference px, as layout.json
        caches it from the artwork (work order 134 A measured it)."""
        return self._data.get("frame", {}).get("opening")

    def box_by_name(self, name):
        for box in self.boxes:
            if box.name == name:
                return box
        return None

    def icon_slots(self):
        """The twenty cell rects in window px — the same list the
        drawing uses, because the hit-test must not build a second
        one (decision 5)."""
        return fltdraw.icon_slots(self)

    def editor_note(self, box):
        """What F5 cannot see: the geometry that FOLLOWS a box.

        Dragging `scroll_column` moves three parts and dragging
        `icon_area` moves twenty cells, and neither has a rect of its
        own in the file. Without this the person dragging is dragging
        blind — the hook `ScreenBase.editor_note` exists for.
        """
        if box.name == "scroll_column":
            return ("holds the up arrow, the 234-unit track and the down "
                    "arrow (fltgeom.SCROLL_PARTS)")
        if box.name == "icon_area":
            return (f"holds {fltgeom.GRID_MAX_ICONS} icon cells, "
                    f"{fltgeom.GRID_COLUMNS}x{fltgeom.GRID_ROWS}, and the "
                    f"scroll column sits at its right edge")
        if box.name == "inset_map":
            return "aspect-bound 305:182 (movebox.cpp:193-199)"
        return None

    # ── Drawing ───────────────────────────────────────────

    def _fill_hints(self):
        """The two hint labels, set on their boxes for this frame only.

        `Box.text` is deliberately not serialized (decision 37), so a
        value computed here can never reach `boxes.json`. The inset's
        hint stands whenever it can be shown — a click there sends
        nothing and never will until relocation and move orders are
        built (OMISSION, 137 E5). The status strip's stands only while
        HD has no star name to put there, because the name is the part
        HD CAN say.

        **AND THE INSET'S IS DROPPED WHEN A STAR IS UNDER IT.** The
        strip sits on the map's bottom edge (`fltgeom.hint_rect`), and
        a galaxy whose lowest stars reach that edge would have them
        read through the words. The map is the thing this box explains;
        covering part of it to say so is the wrong trade, so the words
        go and the map stays whole. The OMISSION remains marked in
        `layout.json` and in `fltwire`, which is where a marking has to
        survive anyway — a hint that only appears sometimes was never
        the marking (fundament: "a labelling rule without a check is an
        intention").
        """
        for name, (_region, word) in fltgeom.HINTS.items():
            box = self.box_by_name(name)
            if box is None:
                continue
            if name == "status_hint":
                # **THE ORIGINAL SHOWS NOTHING HERE, SO NEITHER DO WE.**
                # `Print_Fltscrn_Scanned_Star_Name_` is called only
                # under `if (_galaxy_map_scanned_star > -1)`
                # (flt1.cpp:397) — with nothing hovered the strip is
                # not written at all, which is what the original's own
                # screenshot shows. HD used to fill the emptiness with
                # "Hover a stack in the game window", which invents a
                # line the game never prints and makes an EMPTY state
                # look like an explained one. The 137 E5 omission stays
                # marked where a marking belongs, in `layout.json`
                # `marks` and in `fltwire` — not as text on the screen.
                box.text = None
                continue
            if name == "inset_hint" and fltgeom.hint_collides(
                    self._inset_stars()):
                box.text = None
                continue
            box.text = self._words.get(word)

    def render(self, surface):
        self._render_background(surface)
        self._fill_hints()
        flthud.draw_hud(surface, self, self.enabled_buttons(),
                        self._filter_state())
        fltdraw.fill_inset(surface, self)
        for box in self.boxes:
            box.render(surface, self.layout, self.style)
        fltdraw.draw_slots(surface, self)
        fltdraw.draw_cells(surface, self, self._cells, self._art)
        fltdraw.draw_scroll(surface, self, self._first_row, self._total_rows)
        fltdraw.draw_labels(surface, self, self._words,
                            self.enabled_buttons(), self._art,
                            self._filter_state())
        fltpanel.draw_panel(surface, self, self._panel, self._words)
        _stars = self._inset_stars()
        fltdraw.draw_inset(surface, self, _stars,
                           self._inset_markers(), self._art)
        fltdraw.draw_relocation_lines(surface, self, self._state, _stars,
                                      pygame.time.get_ticks())
        fltdraw.draw_status(surface, self, self._status)
        # The frame LAST, so its metal covers the two reference px each
        # box is allowed to bleed under it (fltgeom.BLEED).
        self._render_frame_image(surface)
        # AFTER the frame: the box is the game's and it is modal, so
        # nothing of this screen may cover it. Before the help popup,
        # which is the player's own and may.
        fltbox.draw(surface, self, self._state)
        self.render_help(surface)

    def enabled_buttons(self):
        """The control boxes that are live, or None before a snapshot.

        The FIELD LIST answers it and the view state does not, which is
        the honest way round: the original adds SCRAP and ALL only under
        conditions (flt1.cpp:1185-1199) and turns LEADERS into a hidden
        field with no hotkey when no officer exists (:1232-1241). So
        "is there a field with this hotkey and this type, in the list a
        click would go to" IS the question.
        """
        if self._state is None or self._view is None:
            return None
        return self._view.enabled_buttons(
            getattr(self._state, "fields", None))

    def _filter_state(self):
        """Which filter radios are on, by box name.

        `support_filter` and `combat_filter` come from the FLTS block
        (open fix 27), which is the same pair of variables the original
        hands `Add_Radio_Button_Field_` at flt1.cpp:1255-1256. Empty
        when there is no block: a radio whose state is unknown is drawn
        unlit rather than guessed at, which is the same answer the
        screen gave before it could show the state at all.
        """
        block = getattr(self._state, "fleet_screen", None) or {}
        return {name: bool(block.get(key))
                for name, (_which, key) in fltdraw.RADIOS.items()}

    def _inset_stars(self):
        """Every star as (native_x, native_y, colour index) inside the
        inset box — `colonyrows.galaxy_inset_stars` with THIS screen's
        native box (15, 52, 305, 182), flt1.cpp:411. One transform for
        all three inset sites, given a different box each time, rather
        than a third copy of `MOVEBOX::Draw_Galaxy_Map_Box_`."""
        if self._state is None:
            return []
        # BLACK HOLE 10, NOT 9. `_using_colony_screen_palette ? 9 : 10`
        # (movebox.cpp:70) and this screen clears the flag
        # (flt1.cpp:522); the eleventh sprite exists here and is loaded
        # (flt1.cpp:1441-1444, mox.h:110).
        return colonyrows.galaxy_inset_stars(
            self._state, fltgeom.REGIONS["inset_map"], black_hole=10)

    def _inset_markers(self):
        """Every ship stack marker as (native_x, native_y, owner).

        `s_ship_icon.x/y` are ALREADY in this box's space while screen 4
        is up: `FLT::Set_Fltscrn_Small_Ship_Icon_XYs_(15, 52, 305, 182)`
        overwrites them on entry (flt.cpp:24-55, flt1.cpp:531). So this
        reads them and converts nothing — and it is also decision 59's
        hazard from the other side, which is why the galaxy map must
        ignore `s_ship_icon` while the screen id is not 0.

        The box origin is subtracted because those coordinates are
        absolute native, and `fltdraw.draw_inset` works inside the box.
        """
        if self._state is None:
            return []
        bx, by, _bw, _bh = fltgeom.REGIONS["inset_map"]
        out = []
        for icon in (getattr(self._state, "ship_icons", None) or []):
            x, y = int(icon.x), int(icon.y)
            if x < 0 or y < 0:
                continue        # the -1 sentinel: not placed this frame
            out.append((x - bx, y - by, getattr(icon, "owner", None)))
        return out

    # ── Input ─────────────────────────────────────────────
    #
    # DECISION 20, AND IT IS THE WHOLE RULE ON THIS SCREEN. The loop
    # rebuilds its field list on EVERY iteration (flt1.cpp:582-585) and
    # the ids shift with the icon count, the star count and every
    # conditional button, so an index remembered from an earlier list
    # names something else by the time it is sent. Every send below
    # resolves its field in the list that is on the wire at the moment
    # of the click, by hotkey and type, and does not go at all if it is
    # not there.
    #
    # WHAT IS NOT SENT, and each for its own reason:
    #   - the big-icon SELECTION goes through MSG_SELECT_SHIP, not a
    #     field: an activation of a big icon only SCANS
    #     (flt2.cpp:924-928), and the toggle is painted from the live
    #     mouse button, which no injected click reaches (open fix 28).
    #   - the scroll THUMB is a pointer value; HD scrolls with the two
    #     arrow fields and never with the scroll field (decision 39).
    #   - F5 and Alt-F5 (merge, clear relocations) cannot be sent at
    #     all: INJECT_KEY's keysym is an int16 and SDLK_F5 is
    #     0x4000003e (the reading's §2). OMISSION.

    #: ESC, which the RETURN button carries as its hotkey.
    KEY_ESC = 27

    def _live(self, name):
        """The live field for one control, or None."""
        return fltwire.hotkey_field(
            getattr(self._state, "fields", None), name)

    def _activate(self, name, why):
        """ACTIVATE_FIELD on one control, or nothing. True if it went."""
        if not self.app.connected:
            return False
        field = self._live(name)
        if field is None:
            log.info("fleets: %s is not in the live field list (%s)",
                     name, why)
            return False
        self.app.client.activate_field(field.index)
        return True

    def handle_click(self, screen_x, screen_y):
        if self.help_consumes_click(screen_x, screen_y):
            return None
        # **THE BOX ANSWERS FIRST, AND IT IS THE ONE SEND `_inert`
        # DOES NOT STOP.** Its fields ARE the live list, so a send to
        # them resolves in the list it was handed (decision 20); it is
        # everything else on this screen that has nothing to send to.
        if self._view is not None and self._view.in_box:
            return self._click_game_box(screen_x, screen_y)
        if self._inert():
            return None
        for box in self.boxes:
            if box.name in fltwire.HOTKEYS and box.contains(screen_x,
                                                            screen_y):
                # THE TWO FILTERS ARE RADIOS AND NEED A CLICK, NOT AN
                # ACTIVATION. ACTIVATE_FIELD returns a type-1 field's id
                # without toggling it (fields.cpp:1018-1024, :1116-1122,
                # :1292-1297) and the handler then finds one status still
                # 1 and only rebuilds the list — so the filter would
                # never change. An injected click toggles (:1292-1297).
                if box.name in ("btn_support", "btn_combat"):
                    self._click_field(box.name)
                else:
                    self._activate(box.name, "clicked")
                return box
        slot = self._slot_at(screen_x, screen_y)
        if slot is not None:
            self._toggle_slot(slot)
            return None
        if self._map_click(screen_x, screen_y):
            return None
        return super().handle_click(screen_x, screen_y)

    def _click_game_box(self, screen_x, screen_y):
        """Answer the native box, through its own field. True if it went."""
        rects = fltbox.button_rects(self)
        for key, field, rect in rects:
            if rect.collidepoint(screen_x, screen_y):
                if not self.app.connected:
                    return None
                log.info("game box: %s -> field %d", key, field.index)
                self.app.client.activate_field(field.index)
                return None
        return None

    def _map_click(self, screen_x, screen_y):
        """A click on a star in the inset — `fltmove.click` decides."""
        return fltmove.click(self, screen_x, screen_y)

    def _click_field(self, name):
        """INJECT_CLICK at a radio field's own centre.

        Its rect comes from the LIVE field, not from our box: the box is
        where HD drew the word and the field is where the game will read
        the click (decision 35 — the click frame is the game's).
        """
        if not self.app.connected:
            return False
        field = self._live(name)
        if field is None:
            return False
        self.app.client.inject_click((field.x + field.x_end) // 2,
                                     (field.y + field.y_end) // 2)
        return True

    def _slot_at(self, screen_x, screen_y):
        """The displayed grid slot under a point, or None."""
        for slot, rect in enumerate(self.icon_slots()):
            if rect.collidepoint(screen_x, screen_y):
                return slot if slot < len(self._cells) else None
        return None

    def _toggle_slot(self, slot):
        """Select or deselect the ship in one cell — MSG_SELECT_SHIP.

        Open fix 28 makes this reach the fleet screen at all; open fix
        21's handler refuses here (it wants the galaxy map's fleet box)
        and writes an array this screen does not read. Nothing is
        assumed about the result: the selection HD draws next frame is
        the one the FLTS block reports, never the one sent.

        Refused where the engine would refuse it (decision 33): a
        foreign stack cannot be selected (flt1.cpp:1185, :1193) and
        relocate mode 1 turns the painting off entirely (flt1.cpp:413).
        """
        if not (self.app.connected and self._view and self._view.ok):
            return
        if not self._view.own_stack:
            return
        if int(self._view.block.get("relocate_mode", 0)) == 1:
            return
        cell = self._cells[slot]
        self.app.client.select_ship(cell.ship_idx, not cell.selected)

    def handle_mouse_motion(self, screen_x, screen_y):
        """The pointer over a ship shows that ship in the panel.

        TRANSCRIPTION of the hover half of the original's own loop:
        `Scan_Fltscrn_Big_Icons_` answers result 4 for the field under
        the pointer and `_scanned_big_ship` takes it (flt1.cpp:616-620,
        flt2.cpp:938-946). `fltscan` holds the rule, including where
        the original refuses — a foreign stack and an empty slot.

        **AND IT SENDS NOTHING.** The panel is rebuilt from the
        snapshot this screen already has. The Extension API has no
        mouse motion at all (open fixes 3 and 4), so there is nothing
        to send that would help, and a send per mouse movement would
        flood the input loop the API does have.
        """
        self._hover_cell = self._slot_at(screen_x, screen_y)
        if (self._view is not None and self._view.ok
                and self._scan.hover(self._hover_cell, self._first_row,
                                     self._view.own_stack,
                                     self._view.rows)):
            self._panel = self._panel_for(self._state, self._view.block)
            # **THE THREE SCANS ARE MUTUALLY EXCLUSIVE IN THE
            # ORIGINAL**, and this is the half that clears the star:
            # taking a big icon sets `_scanned_big_ship` and then
            # `_galaxy_map_scanned_star = -1` in the same branch
            # (flt1.cpp:616-620). The strip goes quiet when the
            # pointer moves onto the grid, which is what the original
            # does.
            self._scan_star = -1
        elif self._view is not None and self._view.ok:
            # A STAR UNDER THE POINTER. The other half of the same
            # exclusion: `if (scanned_star_id >= 0) {
            # _galaxy_map_scanned_star = …; _scanned_small_ship = -1; }`
            # (flt1.cpp:649-652) — and it does NOT clear
            # `_scanned_big_ship`, so the ship panel keeps its ship
            # while the strip names a star. HD does the same.
            #
            # AND IT SENDS NOTHING. `fltmove.star_at` resolves the
            # star from the stars HD already draws, exactly as 153 B
            # resolves the hovered ship from the block it already has.
            _in_map, _star = fltmove.star_at(self, screen_x, screen_y)
            if _in_map:
                self._scan_star = -1 if _star is None else _star
                self._status = self._status_line(self._state,
                                                 self._view.block)
        return super().handle_mouse_motion(screen_x, screen_y)

    def handle_mousewheel(self, direction, screen_x, screen_y):
        """The wheel scrolls the grid through the game's own arrows.

        HD EXTENSION — the original has no wheel here, only the two
        arrow buttons and the bar (flt1.cpp:1211-1215). It is NOT a
        local scroll either: the list window belongs to the game
        (decision 46) and `first_visible_row` comes back in the FLTS
        block, so the wheel activates the same field the arrow does and
        HD waits to be told where the list now is.

        Refused where the game would refuse it (decision 33): the two
        arrows only exist above twenty icons (flt1.cpp:1212), so above
        the grid with a shorter list the wheel does nothing, exactly as
        a click on the absent arrow would.
        """
        if self.help_consumes_wheel(direction):
            return True
        if self._inert() or not (self._view and self._view.scrollable()):
            return False
        return self._activate("scroll_up" if direction > 0
                              else "scroll_down", "wheel")

    def handle_key(self, key):
        if self.help_consumes_key(key):
            return
        if self._inert():
            return
        if key == self.KEY_ESC:
            self._activate("btn_return", "ESC")
            return
        super().handle_key(key)

    # ── Right-click help ──────────────────────────────────

    def open_help_at(self, screen_x, screen_y):
        """The static table first, then help 360 over the EMPTY slots.

        `Set_Fleet_Screen_Help_List_` copies the twelve static entries
        and APPENDS the dynamic ones after them (`help_list_count`
        starts at 12, evanhelp.cpp:378-407), and `Check_Help_List_`
        takes the first hit (fields.cpp:2924-2932). So the order here is
        the engine's: `super()` walks `help.json`, and only what it
        misses reaches the slots.

        An OCCUPIED slot deliberately gets nothing: that is what leaves
        the right button free to open the detailed ship view
        (flt2.cpp:929-933).
        """
        if super().open_help_at(screen_x, screen_y):
            return True
        slots = self.icon_slots()
        if not slots:
            return False
        empty = (slots if self._icon_count == 0
                 else slots[self._icon_count:])
        for slot in empty:
            if slot.collidepoint(screen_x, screen_y):
                entry = self.helptext.entry(360) or \
                    self.helptext.missing_entry(360)
                self.help.open(360, *entry)
                return True
        return False
