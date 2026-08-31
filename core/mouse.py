"""One source for the pointer position.

In fullscreen (F11) the content is rendered at the current F9
resolution and centred on the native desktop with black bars around
it, so a raw `pygame.mouse.get_pos()` is in *desktop* space while
everything a screen draws is in *window* space. Windowed, the
difference is zero — which is exactly why a missing correction stays
invisible until somebody presses F11, and then only for whichever
widget forgot it.

Decision 5 applies to the pointer as much as to a rect: whatever
draws the highlight and whatever decides the hit must ask the same
function. Three variants of this existed before this module:

  main.py             corrected via App._adjust_mouse
  core/editor         re-derived the same arithmetic by hand
  galaxy_map nav      did neither, so its hover was offset by the
                      bar width in fullscreen

The offset is *pushed* here by App whenever it changes rather than
read back out of App, so a screen can ask where the mouse is without
holding a reference to the application.

Events are a separate path and stay that way: `App._handle_events`
rewrites `event.pos` once, at the door, and anything routed from an
event is already in window space. This module is for the code that
polls instead — hover highlights, wheel handlers, the editor.
"""
import pygame

_offset = (0, 0)


def set_offset(offset):
    """Called by App on every fullscreen toggle and at startup."""
    global _offset
    _offset = (int(offset[0]), int(offset[1])) if offset else (0, 0)


def offset():
    """Current desktop -> window offset, (0, 0) when windowed."""
    return _offset


def adjust(x, y):
    """Desktop coordinates -> window coordinates."""
    return (x - _offset[0], y - _offset[1])


def pos():
    """The pointer, in window coordinates.

    Use this instead of `pygame.mouse.get_pos()`. The smoke test
    asserts that this module is the only place that calls it.
    """
    return adjust(*pygame.mouse.get_pos())
