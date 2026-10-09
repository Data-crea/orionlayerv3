"""Research Select — orion2re SELECT NEW RESEARCH, wire id 53.

`TECH::_Tech_Select_(0)` (tech.cpp:111-395), reached at turn start when
a project completes: `Display_Report_Aux_` -> `Has_Research_Breakthrough_`
or `Set_Initial_Tech_` -> `TECH::Tech_Select_` (report.cpp:474, :513).
The game reports SCREEN_MAIN throughout (mainscr2.cpp:119) and open
fix 24 gives it the synthetic **53** on the wire instead.

Built by work order 130 E. STRUCTURE ONLY — frame and artwork come
later (Data, 17 September: "Rahmen und Visuelles kommen später
darüber").

THE BEHAVIOUR IS `core.researchscreen.ResearchPanelScreen`, which both
modes are — the original's own `_Tech_Select_(changing_tech)` is one
function and work order 165 made the HD side one class. What is here
is this mode's configuration and this mode's markings.

SELECT MODE'S OWN FACTS, and they are the only ones:

    there is NO WAY OUT but a commit. Select mode has no ESC field and
    cancel is disabled (tech.cpp:131, :207, fields.cpp:983-988), so
    `HAS_EXIT` is False and the base forwards no key at all.
    the cost is the FULL cost: `_Tech_Select_(0)` passes a research
    offset of 0 (tech.cpp:221), where change mode subtracts what has
    been accumulated.
    the original's SECOND COLOUR is unreachable: `Tech_Select_` zeroes
    `current_research_field` before the list is built (tech.cpp:104-105).

NOT ACCEPTED YET. Open fix 26 — `SELECT NEW RESEARCH` committing a row
by itself about a second and a half after the science room hands over
(measured 18 September 2026) — is CLOSED by open fix 62 (work order 197
A4): the activation came from a field list that had ended. The
workaround this docstring carried while it was open (click the
completion dialog away with the real mouse) is no longer needed. What
the screen still owes before Data can accept it — the third live
choice, two more resolutions, the work order 128 crash case, the six
always-open fields and uncreative races compared against the original —
is its entry in the state, `[research_select.screen]`.

MARKED, and each held by a smoke check so the marking cannot quietly
disappear (decision 61):

  OMISSION      the science room animation on the left strip
                (`SR_R%x_SC.LBX`, tech.cpp:245-273) — artwork, not
                extracted
  DEVIATION     the category list popup (`_Tech_List_`, tech.cpp:847+)
                is BUILT, work order 165 part C, and it sends nothing:
                it is display-only in the original, so HD draws its own
                and the game stays in the panel's loop. What deviates
                is the WINDOW — TECHSEL 0x17-0x1A (change) / 0x09-0x0C
                (select) is not extracted, the page buttons' size is
                not in the source at all (their origins are) and is
                chosen, and the hovered row is filled where the
                original cycles a palette index
  DEVIATION     Q11, the radio index skew: the original indexes
                `entries[input - first_btn_field]` (tech.cpp:378-379)
                while radios exist only for NON-EMPTY entries
                (:236, :497-513), so with an empty category ahead of it
                a button opens the WRONG category's list. HD opens the
                category the button belongs to — the original is
                reading data that was never set
  DEVIATION     the description box a right click over a row opens
                (tech.cpp:323-337, `Draw_Application_Description_`) is
                BUILT, work order 165 part C, and drawn in the shared
                help panel: same trigger, same single help record, same
                full cost on the end. The original's own box is 380 px
                wide at a fixed x (textbox.cpp:40-88) and centres that
                last line; the shared panel sizes itself to its text
                and does not centre
  OMISSION      the little arrow and the cycling selection box
                (`Draw_Little_Arrow_`, tech.cpp:740)
  DEVIATION     the eight entry boxes and the list popup's window are
                DRAWN IN CODE — one fill and one rounded outline
                through `Style.draw_plate`, the way `screens/planets/`
                draws its boxes and out of the same two palette
                entries. They wore the `inner_panel` ARTWORK until work
                order 166 part C, and Data's verdict on the live panel
                was that it does not fit them. The original wears
                TECHSEL art in these places and HD has none of it
  DEVIATION     the outer frame is the HUD popup panel (decision 71,
                work order 169); before it, the Fleets screen's inner
                frame cut from its frame image (work order 166 part B),
                which work order 190 removed. The original draws
                TECHSEL.LBX's own panel art there, so this is a
                different picture in the same place and not an addition
  HD EXTENSION  the title: the original's headline is part of the
                TECHSEL art and is not a string tech.cpp prints
  DEVIATION     the category label is printed as text where the
                original paints it into the panel art; the word itself
                is the game's own (billtext 64 + group)
  DEVIATION     a name too wide is SHRUNK, where `Squeeze_Print_`
                compresses the glyphs (panel.py)
"""
import pygame

from core.researchscreen import (            # noqa: F401  (re-exported)
    COST_SUFFIX, NAMES_MISSING, NO_PLAYER, READY, UNVALIDATED,
    WORDING_MISSING, ResearchPanelScreen, cost_suffix)

#: Every name this module marks, and what kind of marking it is. The
#: smoke test reads THIS, so a marking cannot be removed from the
#: docstring and left in the code or the other way round.
MARKED = {
    "science_room_animation": "OMISSION",
    "category_list_popup": "DEVIATION",
    "radio_index_skew": "DEVIATION",
    "description_box": "DEVIATION",
    "little_arrow": "OMISSION",
    "outer_frame": "DEVIATION",
    "inner_boxes_drawn": "DEVIATION",
    "title": "HD EXTENSION",
    "category_label_as_text": "DEVIATION",
    "shrink_instead_of_squeeze": "DEVIATION",
}


#: THE SCREEN SHELL (work order 225): select mode is a full screen — the
#: science room's strip and the panel — so its two native regions are
#: fitted into the content rectangle, side by side in their native
#: proportion (`core.panelmap`), the title on the plate. Each region IS
#: the box drawn as its panel (the science room's strip, the panel's lit
#: edge), so both meet the rectangle's edges. Change mode is an overlay
#: over the map and keeps its place (the order: no geometry change for
#: overlays); the shared panel code is not touched.
REGIONS_NATIVE = (("science_room", (0, 0, 160, 479)),
                  ("panel", (165, 4, 632, 472)))


class ResearchSelectScreen(ResearchPanelScreen):
    SCREEN_NAME = "research_select"
    GAME_SCREEN_ID = 53         # synthetic, open fix 24, wire only
    MODE = "select"
    LAYOUT_PATH = "screens/research_select/layout.json"
    HAS_EXIT = False
    SHELL_WORN = True

    def __init__(self, app):
        super().__init__(app)
        from core.hud import shell
        self.shell = shell.Shell(title=lambda: self._data.get("title", ""))

    def build_native_map(self):
        """The two regions' panels are the shell's split of the content
        rectangle, not boxes: every box of this screen is SEATED from the
        geometry's own table (`researchnative.seat`), which refuses a box it
        has no native rectangle for."""
        from core import panelmap
        from core.hud import shell
        L = self.app.layout
        widths = [float(n[2] - n[0] + 1) for _k, n in REGIONS_NATIVE]
        parts = shell.split(shell.content(L), L, widths)
        self._native_map = panelmap.PanelMap(L, [
            (k, n, r, True) for (k, n), r in zip(REGIONS_NATIVE, parts)])

    def _dress_boxes(self):
        """Seated, then placed through the map: `Box.update_layout` scales
        a reference rect uniformly, so a seated box is re-placed where the
        map draws its native rectangle (decision 5: the same rect the
        native drawing and `native_point` use). The title's words stand on
        the shell's plate, not in the panel."""
        super()._dress_boxes()
        for box in self.boxes:
            if box.name == "title":
                box.style["label"] = ""
            if box.ref_rect is not None:
                box.screen_rect = pygame.Rect(*self.layout.rect(box.ref_rect))

    def render_content(self, surface):
        super().render_content(surface)
        self.render_shell(surface)
