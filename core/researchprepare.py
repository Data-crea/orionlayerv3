"""The research panel drawn once, off screen, while the game builds its list.

WORK ORDER 184. Opening the research screen the first time after a start
took 1.2 s at 1920 and 3.0 s at 3840, against 0.7 and 0.9 s for every
later entry, and the difference was the screen's first `render`: the HUD
panels and their glass, built at the window's size and cached from then
on (`core.hud.blocks`, `core.hud.glass`) — 19 shapes, 17 glass fills.

AND THE ENGINE IS SILENT FOR ~550 ms AFTER THE SWITCH, whatever HD does.
The first snapshot at 36 comes from `Screen_Control_`'s own `ext::Tick`
(mox2.cpp:41), with the list `Clear_Fields_` left behind
(mainscr_main.cpp:699) — nothing. The list itself is serialised on the
SIXTH `Get_Input_` of `_Tech_Select_`'s loop: `Set_Input_Delay_(5)`
(tech.cpp:286) makes the first five return before `ext::Tick`
(fields.cpp:161-167), and each idle pass waits `Release_Time_(2)`, 110 ms
(tech.cpp:351-353; timer.cpp:15, 55 ms a tick). Measured live: every one
of 75 entries had exactly two snapshots in that phase, 505-594 ms apart.
So the building is done HERE, in that wait, instead of after it.

**NOTHING OF IT IS SHOWN.** It draws onto a scratch surface that is thrown
away, so the rule the screen lives by — it does not draw a list it cannot
vouch for (work order 130 C) — is not touched: the entries are the
reconstruction, not yet validated against the game's list, and the window
keeps showing the galaxy map (`ResearchPanelScreen.draws_this_frame`).
What survives is only what the blocks, the glass and the fonts cache,
keyed on the rectangles, the window size, the style and the glass slider
— the keys the READY frame asks for, through the same calls, so that
frame's pixels are the pixels it always drew: the renders at 1920, 2576
and 3840 are byte for byte the ones before (`~/orionlayerv3-dev/tools/research_render.py`),
and a smoke check holds that the READY frame after a wait builds no HUD
shape at all.

WHAT INVALIDATES IT is therefore what invalidates those caches, and
nothing of its own: a resize (a new size is a new key; `on_resize`
re-seats the boxes), the frame colour and the glass slider
(`core.hud.style.on_change` clears both caches), a mod folder (read at
start), F5 box edits (a moved box is a new rectangle, so a new key), the
language (the text is rendered by the READY frame itself, never taken
from here). It keeps no cache — the one thing it remembers is that it has
run in this visit (`_prepared`, reset by `enter`), because a warm cache
makes it a few milliseconds and a second rule about what a cache holds
would be a second thing to keep right.

Select mode (53) never gets here: its id is set inside `_Tech_Select_`
(the ScreenOverride, tech.cpp:137), so the first snapshot that carries it
already carries the list — it never waits.

**THE STATE IS SET TO READY FOR THE DRAWING AND PUT BACK**, because
`render_content` draws nothing in any other state, and a copy of its body
here would be a second drawing of the panel to keep equal to the first.
"""
import pygame


def prepare(screen):
    """Once per visit: draw `screen`'s panel off screen, as READY."""
    if getattr(screen, "_prepared", False):
        return False
    screen._prepared = True
    scratch = pygame.Surface((screen.layout.window_w,
                              screen.layout.window_h))
    state = screen._state
    screen._state = screen.READY_STATE
    try:
        screen._render_background(scratch)
        for box in screen.boxes:
            box.render(scratch, screen.layout, screen.style)
        screen.render_content(scratch)
    finally:
        screen._state = state
    return True
