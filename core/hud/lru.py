"""A cache of drawn pictures bounded by bytes as well as by count — work
order 263, Data's decision of work order 262 answering 255 P7.

The HUD shape cache (`blocks`) and the glass cache (`glass`) were bounded
by count only, 400 and 600 entries; at 3840x2160 one entry is up to about
15 MB, so the bound was in the gigabytes, and over 50 turns the client
grew to 1.7 GB (work order 255, Part D). Measured offline at 3840x2160
(work order 263): one screen holds at most about 55 MB in both together,
so the two budgets below (256 MB together) keep several screens' worth.
The least recently used picture goes first; the newest always stays.
"""
from collections import OrderedDict

import pygame


def nbytes(value):
    """The pixel memory a cached value holds: its surfaces, also inside a
    tuple or list (a shape is `(surface, pad)`)."""
    if isinstance(value, pygame.Surface):
        return value.get_pitch() * value.get_height()
    if isinstance(value, (tuple, list)):
        return sum(nbytes(v) for v in value)
    return 0


class Cache:

    def __init__(self, max_items, max_bytes):
        self.max_items, self.max_bytes = max_items, max_bytes
        self._items = OrderedDict()
        self.bytes = 0

    def __len__(self):
        return len(self._items)

    def __contains__(self, key):
        return key in self._items

    def __iter__(self):
        return iter(list(self._items))

    def values(self):
        return [value for value, _size in self._items.values()]

    def get(self, key, default=None):
        if key not in self._items:
            return default
        self._items.move_to_end(key)
        return self._items[key][0]

    def put(self, key, value):
        if key in self._items:
            self.bytes -= self._items.pop(key)[1]
        size = nbytes(value)
        self._items[key] = (value, size)
        self.bytes += size
        while len(self._items) > 1 and (len(self._items) > self.max_items
                                        or self.bytes > self.max_bytes):
            self.bytes -= self._items.popitem(last=False)[1][1]
        return value

    def clear(self):
        self._items.clear()
        self.bytes = 0


class TextCache:
    """Rendered text kept by the picture's whole key — work order 324
    (UNVERIFIED live). A label that is the same every frame (a star's
    name, a log cell) was rendered every frame; this renders it once.

    The key is everything that changes the picture: the style (its fonts),
    the language state (`lang.state_key`, which `render_text` translates
    through), the text, the size and the colour. **A cached surface is
    shared: callers blit it and never draw on it.** Bounded by count and
    by bytes like every cache here (`Cache`)."""

    def __init__(self, max_items=768, max_bytes=24 * 1024 * 1024):
        self._cache = Cache(max_items, max_bytes)
        #: how many pictures were really rendered (a check counts it)
        self.built = 0
        # a picture of text is drawn at a size the player's text size
        # (`core.fontscale`, work order 356) changes: forget them all
        from core import fontscale
        fontscale.on_change(self.clear)

    def __len__(self):
        return len(self._cache)

    def render(self, style, text, size, rgb):
        from core import lang
        return self.fetch((id(style), lang.state_key(), text, size,
                           tuple(rgb)),
                          lambda: style.render_text(text, size, tuple(rgb)))

    def fetch(self, key, build):
        """The picture for `key`, built by `build()` the first time."""
        hit = self._cache.get(key)
        if hit is None:
            hit = self._cache.put(key, build())
            self.built += 1
        return hit

    def clear(self):
        self._cache.clear()
