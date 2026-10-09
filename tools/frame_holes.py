"""Which boxes are CUTOUT boxes, per screen — the F5 editor's lock.

**WHAT IS LEFT OF THIS MODULE SINCE WORK ORDER 190.** Until then it
derived box rects from the transparent holes of a screen's frame image
(`find_holes`, a namer per screen, `to_ref`, `--write`). Decision 71
stopped every frame from being drawn (work order 169), work orders 189
and 190 removed the images, and the smoke checks that held live boxes to
their holes measure the boxes the screens draw instead. What survives
is the VOCABULARY those namers produced, because it is still true and
still asked for:

  `RULE_NAMES` /
  `cutout_names`           which boxes are cutouts and therefore LOCKED
                           in the F5 editor (`core/editor/boxclass.py`)
  `NAV_KEYS`, `SORT_KEYS`,
  `SORT_BOX_KEYS`,
  `BAND_KEYS`, `BOX_NAME`,
  `BLEED`                  the names and the one number the colony
                           screen, the galaxy map and the smoke suite
                           build those names from

The rects themselves come from `layout_reference.json` (colony summary,
`colonyplates.reseat`), `dev:tools/hud_boxes.py` (galaxy
map) and the
screens' `boxes.json`; nothing here reads an image any more.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# THE REFERENCE RULE LIVES ON THE SCREEN SIDE since Phase B: what a
# rectangle is called once it is a box, and the bleed it is grown by,
# are the screen's own answers and this module asks for them rather than
# keeping a second copy.
from screens.colony_summary import colonyplates as _cplates  # noqa: E402

#: Reference-pixel bleed every cutout box was grown by — IMPORTED, not
#: declared (12 September 2026, the redundancy audit).
BLEED = _cplates.BLEED
NAV_KEYS = ["colonies", "planets", "fleets", "leaders", "races", "info"]

SORT_KEYS = ["name", "population", "food", "industry", "science",
             "producing", "bc"]
#: One box per sort key, named `sort_<key>` — DEVIATION, 12 September
#: 2026, reversing Stage A3's single `sort_bar`; see
#: `layout_reference._sort_slots_note` and `colonysort`. DERIVED FROM
#: `SORT_KEYS` AND NOT TYPED OUT: `colonysort.box_name` builds the same
#: string from the other end and a smoke check holds the two together.
SORT_BOX_KEYS = [f"sort_{k}" for k in SORT_KEYS]

#: `layout_reference.json` names a RECTANGLE, `boxes.json` names a BOX,
#: and two of them differ. IMPORTED, not restated.
BOX_NAME = _cplates.BOX_NAME

#: The colony screen's lower band's WINDOWS — three since 13 September
#: 2026 (brief 97). `planet_output` and `empire_stats` were windows until
#: then; they are parts of `colony_panel` now (`colonyplates.PARTS`).
BAND_KEYS = ["planet_info", "colony_panel", "galaxy_inset"]

#: The Planets screen's five cutouts — brief 101: the list and the right
#: column on top, then three bottom windows left to right.
PLANETS_KEYS = [["list_area", "side_panel"],
                ["planet_panel", "picture_panel", "button_panel"]]

#: The Fleets screen's cutouts, in the order the ORIGINAL adds the fields.
#: Every name here is a control `screens/fleets/fltwire.CONTROL_ORIGINS`
#: already knows by its `flt1.cpp` line, so the layout and the wire cannot
#: drift into two different vocabularies.
FLEETS_ROW1 = ["btn_all", "btn_relocate", "btn_scrap"]        # flt1.cpp:1195, :1229, :1187
FLEETS_ROW2 = ["btn_leaders", "btn_support", "btn_combat",    # :1234, :1256, :1257
               "btn_return"]                                  # :1201
FLEETS_ARROW = ["prev_fleet", "status_band", "next_fleet"]    # :1217, help 363, :1218
FLEETS_COLS, FLEETS_ROWS = 4, 5                               # flt1.cpp:506-507

#: WHICH BOX NAMES ARE CUTOUTS — the vocabulary, not a second copy of the
#: geometry. Added 9 September 2026 for the F5 editor, which has to know
#: whether a box is a cutout before it offers a resize handle (decision 3:
#: a cutout's rect is derived, and dragging one by hand moves content off
#: its place). BUILT FROM THE CONSTANTS ABOVE, never typed out beside them.
#:
#: THE ALTERNATIVE WAS A FLAG IN `boxes.json` AND IT WAS REFUSED:
#: `Box.locked` existed, was serialized and never read; it is deleted
#: (12 September 2026, the redundancy audit) and so is `Box.role`.
RULE_NAMES = {
    "galaxy_map": {"title", "map_area", "sidebar", "nav_turn"}
                  | {f"nav_{k}" for k in NAV_KEYS},
    # `table` since work order 225: the shell panel the header and the
    # rows stand in.
    "colony_summary": {"table", "header", "list_area", "return"}
                      | set(BAND_KEYS) | set(SORT_BOX_KEYS),
    "planets": {name for row in PLANETS_KEYS for name in row},
    "fleets": (set(FLEETS_ROW1) | set(FLEETS_ROW2) | set(FLEETS_ARROW)
               | {"inset_map", "ship_panel"}
               | {f"cell_{i:02d}" for i in range(FLEETS_COLS * FLEETS_ROWS)}),
}


def editor_free(screen):
    """Box names the F5 editor may move, from the screen's own file.

    Declared in `layout_reference.json` under `_editor_free`, in the
    reference's own spelling, and returned in the BOX's. Read rather than
    listed here because whether a box may be dragged is a fact about that
    screen's layout — RETURN is placed by hand on the colony screen.
    """
    try:
        data, _w = _cplates.load_reference(_cplates.reference_path(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            screen))
    except Exception:
        return set()
    # The parts inside a window (brief 95 Part C) are free by
    # construction; `colonyplates.editor_free` is the one home for that.
    return set(_cplates.editor_free(data))


def cutout_names(screen):
    """The cutout names of `screen` the editor may not move — LOCKED.

    A screen with no entry has no cutout boxes at all — every box on it is
    hand-placed — which is a real answer and not a missing one.
    `RULE_NAMES` stays the vocabulary; a box whose rect is derived but
    which Data positions himself is subtracted here, because the editor
    asks this one.
    """
    return RULE_NAMES.get(screen, set()) - editor_free(screen)
