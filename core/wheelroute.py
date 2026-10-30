"""Where a mouse-wheel event goes (split off `main.App` at the 40 KB limit,
work order 356, which added Ctrl + wheel).

In this order: nothing while a held frame or F12 owns the pointer (D13);
the player's text size when Ctrl is down (`core.textsize`);
the F3 editor; else the top screen's `handle_mousewheel`.

HD EXTENSION `font_scale`: Ctrl + wheel is the text size (work order 356).
"""
from core import mouse as mouse_input
from core import pointergate, textsize


def route(app, event):
    if not pointergate.PointerGate.passes(app._pointer_open()):
        return                       # a held frame / F12 (D13)
    if textsize.wheel(app, event) or app.editor.handle_event(event):
        return
    top = app.dispatcher.top
    if top and hasattr(top, "handle_mousewheel"):
        mx, my = mouse_input.pos()
        top.handle_mousewheel(event.y, mx, my)
