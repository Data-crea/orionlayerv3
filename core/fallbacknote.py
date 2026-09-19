"""The sentence a handing-over HD screen leaves on screen.

**HD EXTENSION.** MOO2 has nothing like it and could not: the original
has no second renderer to fall back FROM, so there is no state for it
to explain. This is OrionLayer explaining its own.

WHY IT EXISTS. Work order 138: the Fleets screen became active, said
`wants_original()`, and the window showed the game's picture — which
from the player's side is indistinguishable from the HD screen never
arriving. The sentence that says why was already written, by
`fallback_reason()`, and had one caller in the whole tree, a live tool
for a different screen. Work order 139 A put it in the log; this puts
it where the player is looking.

It is the same argument the Empire Identity progress box already won
(fundament, "Marked inventions are allowed"): an HD screen that stays
up across a state the original never had to explain has to say what it
is waiting for.

WHAT IT MUST NOT DO, and each of these is a rule from somewhere:

* **Cover the game's picture.** The note goes in a band the picture
  does not use — the pillarbox at 4:3 in a wide window, the letterbox
  otherwise. The rect comes from `OriginalView.placement` through the
  caller; recomputing it here would be the second copy decision 5 is
  about, and the one that already had to be removed once between the
  renderer and the click forwarder.
* **Swallow a click.** It draws and returns; `main._handle_click`
  forwards every click to the game exactly as before. A note that ate
  a click would be the fallback view's old fault (work order 130 A)
  in a new costume.
* **Fill from what is underneath.** "A trick that works on one screen
  is not a rule" — blitting the background back at the same
  coordinates reproduces what was already there and turns the panel
  invisible. The fill is `background_cockpit.png` through
  `helppopup.Backdrop`, the same source the help popup settled on.
* **Type its own words.** The frame is
  `assets/shared/fallback/labels.json` (decision 15); the reason is
  the screen's.
* **Measure with one font.** `Style.render_text` can mix two fonts
  inside one string (decision 30), so a line's width is measured by
  rendering it and never by `font.size()`.
* **Truncate silently.** A reason that does not fit is wrapped; if it
  still does not fit after the font has shrunk to `MIN_FONT`, it is
  cut at a word boundary and the labels' `cut` marker is appended, so
  a shortened sentence says that it is shortened.
"""
import logging

import pygame

from core import palette

log = logging.getLogger("orionlayer")

#: WHAT A SCREEN THAT HANDS OVER AND SAYS NOTHING IS WRITTEN AS. It is
#: a state and not an error — decision 22's fallback for an id no HD
#: screen claims has no screen to ask — and it is spelled out so a log
#: line can never read as though the reason were empty by accident.
#: No note is drawn for it: a panel over the game's own picture saying
#: "no reason given" is noise.
NO_REASON = "no reason given"


class Reporter:
    """The log half of the same job, kept beside the drawing half.

    `main.App._showing_original` decides; this reports. ON CHANGE
    ONLY — that method is asked twice a frame, by the renderer and by
    the click handler, and the answer is the same both times and for
    as long as nothing moves. The key carries the REASON as well as
    the verdict, so a screen that stays down for a NEW reason still
    writes a line.

    The transient is logged and is not a fault: the first snapshot
    after the Fleets button carries screen id 4 with the galaxy map's
    field list still in it, so a short not-ready line followed by a
    ready one is the correct shape (work order 138).
    """

    def __init__(self):
        self._last = None

    def note(self, shown, top, dispatcher, screen_id):
        """Log the change, and return what to draw over the picture.

        None means draw nothing: F12's mode is the player's own choice
        and decision 22's unknown id has no screen to quote.
        """
        name = dispatcher.active_name or "-"
        if top is not None and top is dispatcher.overlay:
            name = dispatcher.overlay_name or name
        reason = ""
        if shown:
            getter = getattr(top, "fallback_reason", None)
            reason = (getter() if callable(getter) else "") or NO_REASON
        key = (shown, name, screen_id, reason)
        if key != self._last:
            self._last = key
            if shown:
                log.info("original shown: %s, game screen %s — %s",
                         name, screen_id, reason)
            else:
                log.info("HD draws: %s, game screen %s", name, screen_id)
        return (reason if shown and top is not None
                and reason != NO_REASON else None)

#: Reference-pixel geometry, scaled by `win_h / 1080` like every other
#: size in the tree.
REF_FONT = 20
REF_MIN_FONT = 13
REF_PAD = 10
#: A band narrower than this is not worth writing in; the note then
#: takes the bottom edge instead.
REF_MIN_BAND = 90

TEXT = palette.col("fallback", "note_text", (214, 222, 240))
RULE = palette.col("fallback", "note_rule", (92, 108, 140))


def _wrap(style, text, size, width, color):
    """`text` rendered into lines no wider than `width`.

    Measured by rendering, because `render_text` may mix two fonts in
    one string (decision 30). Returns the surfaces, in order.
    """
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = f"{current} {word}".strip()
        if style.render_text(trial, size, color).get_width() <= width \
                or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return [style.render_text(line, size, color) for line in lines]


def _shorten(style, text, size, width, rows, color, marker):
    """`text` cut at a word boundary so it fits `rows` lines, with the
    marker appended. Only ever reached when the font is already at
    `REF_MIN_FONT` — see the module docstring."""
    words = text.split()
    while words:
        candidate = " ".join(words) + marker
        if len(_wrap(style, candidate, size, width, color)) <= rows:
            return candidate
        words.pop()
    return marker


def band(win_w, win_h, picture):
    """Where the note goes: `(x, y, w, h)` in window pixels.

    `picture` is `OriginalView.render`'s `(x, y, w, h, scale)`. The
    pillarbox first — at 4:3 in a 16:9 window it is the widest thing
    on screen that carries nothing — then the letterbox, then the
    bottom edge of the window, which does cover the picture and is the
    case a 4:3 window leaves.
    """
    px, py, pw, ph, _scale = picture
    right = win_w - (px + pw)
    if px >= REF_MIN_BAND * win_h / 1080 and px >= right:
        return (0, 0, px, win_h)
    if right >= REF_MIN_BAND * win_h / 1080:
        return (px + pw, 0, right, win_h)
    below = win_h - (py + ph)
    if below >= REF_MIN_BAND * win_h / 1080 * 0.4:
        return (0, py + ph, win_w, below)
    height = int(REF_MIN_BAND * win_h / 1080 * 0.6)
    return (0, win_h - height, win_w, height)


def render(surface, style, res, backdrop, reason, labels, picture):
    """Draw the note. Returns the rect it covers, or None.

    `picture` is what `OriginalView.render` just returned. It is PASSED
    and not recomputed: `placement` is the one function that says where
    the 4:3 area lands, and a second copy of that arithmetic here is
    the drift decision 5 exists to stop — the same one that would put
    a forwarded click a bar's width from the pixel aimed at.

    `reason` None or empty draws nothing: decision 22's fallback for an
    id no HD screen claims has no screen to quote, and F12's mode is
    the player's own choice. Both keep the picture they always had.
    """
    if not reason:
        return None
    win_w, win_h = surface.get_size()
    scale = win_h / 1080
    pad = max(4, int(REF_PAD * scale))
    x, y, w, h = band(win_w, win_h, picture)
    inner = max(1, w - 2 * pad)

    text = f"{labels.get('prefix', '')} {reason}".strip()
    size = max(8, int(REF_FONT * scale))
    floor = max(8, int(REF_MIN_FONT * scale))
    rows = max(1, (h - 2 * pad) // max(1, int(size * 1.35)))
    lines = _wrap(style, text, size, inner, TEXT)
    while len(lines) > rows and size > floor:
        size -= 1
        rows = max(1, (h - 2 * pad) // max(1, int(size * 1.35)))
        lines = _wrap(style, text, size, inner, TEXT)
    if len(lines) > rows:
        text = _shorten(style, text, size, inner, rows, TEXT,
                        labels.get("cut", " ..."))
        lines = _wrap(style, text, size, inner, TEXT)

    fill = backdrop.surface(res, win_w, win_h)
    rect = pygame.Rect(x, y, w, h)
    if fill is not None:
        surface.blit(fill, (x, y), rect)
    else:
        surface.fill((10, 13, 22), rect)
    pygame.draw.rect(surface, RULE, rect, max(1, int(scale)))

    step = int(size * 1.35)
    top = y + pad
    for line in lines:
        surface.blit(line, (x + pad, top))
        top += step
    return (x, y, w, h)
