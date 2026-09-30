"""The HUD button's hover state — work order 196 D and E.

Its own module (decision 6: `blocks.py` is at the line guideline), and the
one home of a test five screens had written for themselves or not at all.
"""
import pygame


def pointer_state(rect, base="normal", hit=None):
    """`"hover"` while the pointer is over a clickable button, else `base`.

    The HUD button's hover state (decision 71's four states, `chosen.button`)
    is HD's own look: the original's buttons have no hover at all, only the
    pressed frame while the mouse button is held on them (`Push_Field_Down_`,
    fields.cpp:2136-2165). One home since work order 196 D/E, where the build
    popup and the Races screen never passed it and their buttons stayed dark
    under the pointer while every other screen's lit. A state other than
    "normal" (active, disabled) wins. `hit(rect, x, y)` is the screen's own
    click test, so the hover and the click are one shape (decision 5); the
    rect by default."""
    if base != "normal":
        return base
    from core import mouse
    x, y = mouse.pos()
    inside = hit(rect, x, y) if hit is not None else \
        pygame.Rect(rect).collidepoint(x, y)
    return "hover" if inside else "normal"
