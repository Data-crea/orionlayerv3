"""Research Change — orion2re CHANGE CURRENT RESEARCH, wire id 36.

`TECH::_Tech_Select_(1)` (tech.cpp:111-395), reached from the galaxy
map's research window: `_research_window_field` (mainscr.cpp:1405), its
handler at mainscr_main.cpp:697-713 sets `_return_screen = SCREEN_MAIN`
and `_current_screen = SCREEN_TECH_CHANGE`, and `Screen_Control_`
(mox2.cpp:177-180) calls `TECH::Tech_Change_` (tech.cpp:1157-1168).
**36 is the engine's own number** — unlike select mode's 53 there is
nothing synthetic about it, and the wire reports it for the main panel,
the list popup and the description box alike (tech.cpp:1167 restores
the map's 0 on the way out).

Built by work order 165 part B. STRUCTURE ONLY — frame and artwork
come later (Data, 17 September: "Rahmen und Visuelles kommen später
darüber").

THE BEHAVIOUR IS `core.researchscreen.ResearchPanelScreen`, which both
modes are — the original's own `_Tech_Select_(changing_tech)` is one
function and work order 165 made the HD side one class. What is here
is this mode's configuration and this mode's markings.

CHANGE MODE'S OWN FACTS, and each is a line of the source:

    _g_scrn_x = 80, so the whole panel sits 81 px left of select
        mode's                                        (tech.cpp:146)
    THERE IS A WAY OUT, and it changes nothing. The exit button is the
        first ESC field (tech.cpp:208-210; `Interpret_Keyboard_Input_`,
        fields.cpp:2608-2613), and `input == accept_btn_id` is the one
        branch of the loop that does not commit (:357). ESC and a click
        on the button are the same act, and HD sends the same thing for
        both. The button is DRAWN and clickable at the rectangle the
        wire reports — the source has its origin only, the art carries
        its size.
    the cost is what is LEFT: `_Tech_Select_(1)` passes
        `research_accumulated` as the offset (:203), where select mode
        passes 0 (:221). The description box still shows the FULL cost
        (:735) — the original's design, not a bug
        (`doc/tech_change_reading.md` §3).
    THE CURRENT FIELD IS OFFERED, and it costs nothing to arrange: the
        game zeroes `current_research_field` around the call (:201,
        :204), so the reconstruction asks for the same `current_field=0`
        both modes ask for.
    THE SECOND COLOUR HAS SOMETHING TO MARK here and nowhere else.
        `TECH::_tech_color[2]` is the field being researched and its
        chosen application (:686-696); select mode cannot reach it.
    no science room. That animation is select mode's left strip
        (`SR_R%x_SC.LBX`, :245-273); here the strip is galaxy map —
        and since work order 165 part F it IS the HD galaxy map, live
        underneath. This screen is an OVERLAY over it, on the GAME
        menu's pattern (decision 69): the map keeps drawing, takes no
        input while the panel is up, and the dispatcher holds the
        overlay for as long as the wire reports 36.

MARKED, and each held by a smoke check so the marking cannot quietly
disappear (decision 61):

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
  DEVIATION     the exit button's LABEL is printed as text. The
                original paints it into the button art (TECHSEL 0x1B,
                tech.cpp:176) and passes `Add_Button_Field_` an EMPTY
                label string (:208-210), so there is no string
                tech.cpp prints to transcribe — the same situation the
                category labels are in, and marked the same way. The
                word is the one the art shows and the RECTANGLE is the
                one the wire reports, never a constant: the source has
                only the origin, because the art carries the size
  DEVIATION     the outer frame is the FLEETS screen's inner frame —
                the one around its scanner map, orange lamps in the
                corners — cut out of `screens/fleets/assets/frame.png`
                and nine-sliced around the panel's content box (work
                order 166 part B, Data's decision). The original draws
                TECHSEL.LBX's own panel art there, so this is a
                different picture in the same place and not an addition
  HD EXTENSION  the title: the original's headline is part of the
                TECHSEL art and is not a string tech.cpp prints. Its
                WORDING is the game's own name for the screen, help
                255's title
  DEVIATION     the category label is printed as text where the
                original paints it into the panel art; the word itself
                is the game's own (billtext 64 + group)
  DEVIATION     a name too wide is SHRUNK, where `Squeeze_Print_`
                compresses the glyphs (`core/researchpanel.py`)
"""
from core.researchscreen import (            # noqa: F401  (re-exported)
    COST_SUFFIX, NAMES_MISSING, NO_PLAYER, READY, UNVALIDATED,
    WORDING_MISSING, ResearchPanelScreen, cost_suffix)

#: Every name this module marks, and what kind of marking it is. The
#: smoke test reads THIS, so a marking cannot be removed from the
#: docstring and left in the code or the other way round.
#:
#: It is select mode's list MINUS the science room, which is select
#: mode's own strip, PLUS the exit button's label, which select mode
#: has no button to print — `accept_btn_id = -1` there (tech.cpp:216).
#: Both differences are asserted, in both directions.
MARKED = {
    "category_list_popup": "DEVIATION",
    "exit_button_as_text": "DEVIATION",
    "radio_index_skew": "DEVIATION",
    "description_box": "DEVIATION",
    "little_arrow": "OMISSION",
    "outer_frame": "DEVIATION",
    "title": "HD EXTENSION",
    "category_label_as_text": "DEVIATION",
    "shrink_instead_of_squeeze": "DEVIATION",
}


class ResearchChangeScreen(ResearchPanelScreen):
    SCREEN_NAME = "research_change"
    GAME_SCREEN_ID = 36         # SCREEN_TECH_CHANGE, the engine's own
    MODE = "change"
    LAYOUT_PATH = "screens/research_change/layout.json"
    HAS_EXIT = True
    #: A PANEL OVER THE HD GALAXY MAP — the GAME menu's pattern
    #: (decision 69), and the original's own: `Draw_Mini_Main_Screen_`
    #: paints the map before the screen is switched
    #: (mainscr_main.cpp:700-703), and `_Tech_Select_(1)` fills only
    #: `(s+4, 4)-(s+471, 472)` over it (tech.cpp:290-291).
    IS_OVERLAY = True
    #: SCREEN_TECH_CHANGE is entered from ONE place, the galaxy map's
    #: research window (mainscr_main.cpp:697-713, `_return_screen =
    #: SCREEN_MAIN`), so the map is what it belongs over — and a client
    #: connecting while change mode is already up has never been on the
    #: map, which is the case work order 126 D found for the GAME menu.
    OVERLAY_PARENT = "galaxy_map"
    #: No dimming: a palette-indexed engine cannot darken what is under
    #: a panel, and the original draws over the map as it is.
    OVERLAY_DIM = 0
