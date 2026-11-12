"""The fullscreen content surface — work order 390.

A plain `pygame.Surface((w, h))` made after a fullscreen `set_mode` is ARGB:
a blit of a picture with transparent pixels then leaves alpha-0 pixels, and
the next blit onto one copies the source as it is, so the transparent part
of a ship picture came out black (Data: the colony ship in a fleet box, full
screen only). The window's display surface has no alpha; this one has none.
"""
import pygame

#: R, G, B masks and no alpha mask.
XRGB = (0xFF0000, 0xFF00, 0xFF, 0)


def content_surface(w, h):
    return pygame.Surface((w, h), 0, 32, XRGB)
