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
        first ESC field (tech.cpp:198-200; `Interpret_Keyboard_Input_`,
        fields.cpp:2608-2613), and `input == accept_btn_id` is the one
        branch of the loop that does not commit (:347-353). ESC and a
        click on the button are the same act.
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
        (`SR_R%x_SC.LBX`, :245-273); here the strip is galaxy map.

MARKED, and each held by a smoke check so the marking cannot quietly
disappear (decision 61):

  OMISSION      the category list popup (`_Tech_List_`, tech.cpp:781+),
                which is display-only and is work order 165 part C
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
#: mode's own strip, and that difference is the whole of it.
MARKED = {
    "category_list_popup": "OMISSION",
    "description_box": "DEVIATION",
    "little_arrow": "OMISSION",
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
