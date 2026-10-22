"""A film in HD — decision 101, open fix 112 (work order 320).

**HD EXTENSION `film_in_hd`.** Decision 76 keeps the original's picture
behind F12; decision 101 makes the films its one exception ("Filme sollen
einfach die originalen angezeigt werden und skipbar sein", Data, 21 October
2026): a film is the original's art, not its interface, and HD cannot draw
it again (no Smacker decoder, and the pictures are the player's own). While
the engine reports one (`core/filmblock.py`, id 86) the App draws the
engine's framebuffer — the film's own frames, as F12 shows them, but
without F12 — scaled into the window with its 4:3 aspect kept and the bars
black (`OriginalView.render`, the one placement drawing and clicking
share). The frames are the original's and carry no marking; what HD adds
is the black bars and the hint.

**TRANSCRIPTION `film_skip`.** The original ends a film on any key or any
mouse button (`SMACK::Play_Cinematic_`, smack.cpp:105-113 in 1.60; :102-110
in v2 before open fix 112, :108-116 with it: `Keyboard_Status() == 1` reads
the key away with `Read_Key`; `Mouse_Button() != 0`), and at its last frame
(:121-123 in 1.60). HD answers a click or a key with that input.

**DEVIATION `film_skip_esc`.** Whatever the player pressed — a mouse button
or any key but a lone modifier — HD sends ONE key, ESC, once per film. The
original's skip test sees a key as it sees a button, and a key is read away
by the film's own `Read_Key`; a click's button state outlives the film — the
engine holds its release until the film ends (open fix 112) and the press is
in the mouse buffer — so the next screen could take it as a click at that
point, as the original's would. The key is always ESC and sent once: a
second one, or Enter or a letter, would reach whatever follows the film
(the second of two films, the high score, a popup) once the film has gone.
Nothing is sent once the film is within two frames of its end: it ends by
itself. A lone Shift, Ctrl, Alt or Meta skips nothing (Alt-Tab leaves the
window, it does not end the film).

**HD EXTENSION `film_skip_hint`.** One small line, "Click or press a key to
skip", in the bar beside the picture (`fallbacknote.band`'s choice: the
pillarbox, then the letterbox, then the window's bottom edge), never over
the film where a bar has room. The words are `assets/shared/fallback/
labels.json`'s (decision 15).

**UNVERIFIED `film_live`.** No live run has seen a film reported, drawn or
skipped (Data's decision of 20 October 2026: no live runs).
"""
import logging

import pygame

from core import fallbacknote, filmblock

log = logging.getLogger("orionlayer")

#: ESC (`pygame.K_ESCAPE`, the code INJECT_KEY takes for it): the one key
#: sent for any skip (DEVIATION `film_skip_esc`).
SKIP_KEY = 27
#: Keys that skip nothing alone.
MODIFIERS = (pygame.K_LSHIFT, pygame.K_RSHIFT, pygame.K_LCTRL,
             pygame.K_RCTRL, pygame.K_LALT, pygame.K_RALT, pygame.K_LMETA,
             pygame.K_RMETA, pygame.K_LSUPER, pygame.K_RSUPER,
             pygame.K_CAPSLOCK, pygame.K_NUMLOCK, pygame.K_MODE)
#: The film ends by itself this close to its total (smack.cpp:121-123 in
#: 1.60 ends the loop at total - 1; the snapshot may be a frame behind).
END_MARGIN = 2
HINT_DEFAULT = "Click or press a key to skip"
#: The hint's height at 1080 lines, and its colour (the HUD's label grey).
REF_HINT_H = 22
HINT_COLOUR = (200, 206, 214)


class View:
    def __init__(self):
        #: (name, total) of the film a skip was sent for: one per film,
        #: kept until the film has gone (`Overlays.update` resets it).
        self.sent = None

    def reset(self):
        self.sent = None

    def render(self, surface, app, film, labels=None):
        """Draw the film's frame and the hint. Returns the picture's
        placement `(x, y, w, h, scale)`."""
        picture = app.original_view.render(surface, app.layout)
        # the engine's picture, not an HD frame: no hold may keep it (with
        # its hint) once the film has gone (`handover.render_hold`)
        app._surface_hd = False
        hint(surface, app.style, (labels or {}).get(
            "film_skip_hint", HINT_DEFAULT), picture)
        return picture

    @staticmethod
    def skips(event=None):
        """True for a click (`event` None) and a key that is not a lone
        modifier."""
        return event is None or getattr(event, "key", None) not in MODIFIERS

    def skip(self, client, film, event=None):
        """Send the skip for a click (`event` None) or a key. Returns the
        code sent, or None when nothing was sent."""
        if film is None or client is None or not self.skips(event):
            return None
        frame, total = film.get("frame", 0), film.get("total", 0)
        if total > 0 and frame >= total - END_MARGIN:
            return None
        key = (film.get("name"), total)
        if self.sent == key:
            return None
        self.sent = key
        code = SKIP_KEY
        client.inject_key(code)
        log.info("film %s: skip at frame %d of %d (key %d)",
                 filmblock.title(film), frame, total, code)
        return code


def hint_rect(win_w, win_h, picture, text_w, text_h):
    """Where the hint goes: bottom-centred in `fallbacknote.band`'s band."""
    x, y, w, h = fallbacknote.band(win_w, win_h, picture)
    pad = max(4, int(12 * win_h / 1080))
    return pygame.Rect(x + max(0, (w - text_w) // 2),
                       y + h - text_h - pad, text_w, text_h)


def _lines(style, text, size, width):
    """`text` broken at spaces into lines no wider than `width`."""
    words, lines, line = text.split(), [], ""
    for word in words:
        trial = f"{line} {word}".strip()
        if line and style.render_text(trial, size, HINT_COLOUR).get_width() \
                > width:
            lines.append(line)
            line = word
        else:
            line = trial
    if line:
        lines.append(line)
    return lines


def hint(surface, style, text, picture):
    """Draw the hint; returns the rect it covers, or None."""
    if not text:
        return None
    win_w, win_h = surface.get_size()
    size = max(8, int(REF_HINT_H * win_h / 1080))
    x, _y, w, _h = fallbacknote.band(win_w, win_h, picture)
    inner = max(1, w - 2 * max(4, int(12 * win_h / 1080)))
    surfs = [style.render_text(t, size, HINT_COLOUR)
             for t in _lines(style, text, size, inner)]
    if not surfs:
        return None
    line_h = max(s.get_height() for s in surfs)
    text_w = max(s.get_width() for s in surfs)
    rect = hint_rect(win_w, win_h, picture, text_w, line_h * len(surfs))
    over = rect.colliderect(pygame.Rect(picture[:4]))
    if over:
        # a 4:3 window has no bar: a dark plate under the line, so the film
        # under it is dimmed only where the words are
        plate = pygame.Surface(rect.inflate(16, 8).size, pygame.SRCALPHA)
        plate.fill((0, 0, 0, 150))
        surface.blit(plate, rect.inflate(16, 8).topleft)
    for i, s in enumerate(surfs):
        surface.blit(s, (rect.x + (text_w - s.get_width()) // 2,
                         rect.y + i * line_h))
    return rect
