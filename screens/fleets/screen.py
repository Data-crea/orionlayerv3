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
line and seats them, as one group under one factor, into the single
opening of `assets/frame.png` — the frame is the Planets artwork with
its struts removed (decision 12's variant, work order 134 A).

Decision 3 does not apply here: the frame has ONE hole and nothing
inside it is a cutout, so `tools/frame_holes.py` has no rule for this
screen. `tools/fleet_boxes.py` seeded `boxes.json` once and F5 owns it
from there.
"""
import logging

from core.screen_base import ScreenBase

from . import fltdraw, fltgeom

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

    # ── Lifecycle ─────────────────────────────────────────

    def enter(self, game_state=None):
        super().enter(game_state)
        self._data = self.app.res.load_json(
            "screens/fleets/layout.json", {}) or {}
        self._words = self._data.get("words", {})
        # MOX::_scanned_big_ship = -1 and _scanned_small_ship = -1 on
        # entry (flt1.cpp:527-528); nothing is scanned, so no status line.
        self._first_row, self._status = 0, ""
        self._load_frame(
            self._data.get("frame", {}).get("image", "frame.png"))
        self.update(game_state)

    def on_resize(self):
        super().on_resize()
        self._scale_frame()

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

    def render(self, surface):
        self._render_background(surface)
        for box in self.boxes:
            box.render(surface, self.layout, self.style)
        fltdraw.draw_slots(surface, self)
        fltdraw.draw_scroll(surface, self, self._first_row, self._total_rows)
        fltdraw.draw_labels(surface, self, self._words, self.enabled_buttons())
        fltdraw.draw_status(surface, self, self._status)
        # The frame LAST, so its metal covers the two reference px each
        # box is allowed to bleed under it (fltgeom.BLEED).
        self._render_frame_image(surface)
        self.render_help(surface)

    def enabled_buttons(self):
        """Which of the seven are live this frame, or None for all.

        Part C replaces this with the field list's own answer, which is
        where it belongs: the original adds SCRAP and ALL only under
        conditions (flt1.cpp:1185-1199) and LEADERS as a hidden field
        when no officer exists (:1232-1241), so the wire says which are
        real and HD never has to guess.
        """
        return None

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
