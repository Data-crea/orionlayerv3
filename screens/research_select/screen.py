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

NOT ACCEPTED YET, and the reason is not ours: OPEN FIX 26.
`SELECT NEW RESEARCH` commits a row BY ITSELF, about a second and a half
after the science room hands over to it — measured 18 September 2026
with a send counter proving the client sent nothing. Data's counter-test
of 19 September (same binary, no client connected, the completion dialog
clicked away with the real mouse) shows the list WAITS, so open fix 25
is not the cause; the injected dismissal of that dialog and a connected
client as such are both still suspect and not separated. OPEN, deferred
by Data.

**THE PLAYER'S WAY ROUND IT, while open fix 26 is open: click the
completion dialog away in the orion2re window with the real mouse. The
research selection then waits, and this screen can be used for the
choice.**

That sentence is here, in `doc/orion2re_open_fixes.md` and in
`v3_projektstatus.md`, and a smoke check fails if it leaves any of them
while open fix 26 still says OPEN. The rest of what this screen still
owes — the third live choice, two resolutions, the work order 128 crash
case, the promotion of `tech_applications` out of `unverified.py`, and
the six always-open fields and uncreative races never compared against
the original — is the status document's list.

MARKED, and each held by a smoke check so the marking cannot quietly
disappear (decision 61):

  OMISSION      the science room animation on the left strip
                (`SR_R%x_SC.LBX`, tech.cpp:245-273) — artwork, not
                extracted
  OMISSION      the category list popup (`_Tech_List_`, tech.cpp:781+),
                which is display-only and out of scope for this build
  OMISSION      the description box a right click inside the panel
                opens (tech.cpp:323-337, `Draw_Application_Description_`)
                — so a right click inside the panel does NOTHING here
                rather than something else
  OMISSION      the little arrow and the cycling selection box
                (`Draw_Little_Arrow_`, tech.cpp:740)
  HD EXTENSION  the title: the original's headline is part of the
                TECHSEL art and is not a string tech.cpp prints
  DEVIATION     the category label is printed as text where the
                original paints it into the panel art; the word itself
                is the game's own (billtext 64 + group)
  DEVIATION     a name too wide is SHRUNK, where `Squeeze_Print_`
                compresses the glyphs (panel.py)
"""
from core.researchscreen import (            # noqa: F401  (re-exported)
    COST_SUFFIX, NAMES_MISSING, NO_PLAYER, READY, UNVALIDATED,
    WORDING_MISSING, ResearchPanelScreen, cost_suffix)

#: Every name this module marks, and what kind of marking it is. The
#: smoke test reads THIS, so a marking cannot be removed from the
#: docstring and left in the code or the other way round.
MARKED = {
    "science_room_animation": "OMISSION",
    "category_list_popup": "OMISSION",
    "description_box": "OMISSION",
    "little_arrow": "OMISSION",
    "title": "HD EXTENSION",
    "category_label_as_text": "DEVIATION",
    "shrink_instead_of_squeeze": "DEVIATION",
}


class ResearchSelectScreen(ResearchPanelScreen):
    SCREEN_NAME = "research_select"
    GAME_SCREEN_ID = 53         # synthetic, open fix 24, wire only
    MODE = "select"
    LAYOUT_PATH = "screens/research_select/layout.json"
    HAS_EXIT = False
