"""The original is never shown without F12 — work order 188, Part 1 (Stage 1).

**Data's standing rule (work order 187, and every order after it):** the
player never sees any part of the original picture unless he presses F12.
No hand-over to the original for input, no native frame in a transition,
no original screen as a fallback.

**HD EXTENSION `f12_notice`.** Wherever the game's picture WOULD have been
shown (`doc/briefs/187-original-visibility.md`, "Work order 187, Part 6 —
where the original can still show without F12", paths 1-6, and the crop of
a native box inside an HD panel, path 4b found by work order 188), HD keeps
its last frame, dimmed, and draws one panel: what the game is waiting for,
and "F12 to answer". F12 then shows the original exactly as it always did
(`main.App._cycle_render_mode`), and F12 again returns to HD. The original
has nothing like it and could not: it has no second renderer to hold. The
words are OrionLayer's own and live in the HD string file
`assets/shared/fallback/labels.json` (decision 15), which the player's mod
folder replaces like every other file — so they can be translated without
touching code.

**WHAT IT IS NOT.** Not an answer: nothing is sent to the game while the
notice stands (a click on a held frame is not a choice, decision 65's
reasoning and 180 A2's hold). Stage 2 of work order 188 replaces the
notice with a real HD view path by path; what stays under the notice is
parked for Data by name.

**THE PICTURE BEHIND IT** is built ONCE per notice and window size: the
held surface as the last HD frame left it (or the universal background),
dimmed — so a glass panel drawn on it is never blended over itself, frame
after frame.
"""
import pygame

from core.hud import blocks as hud
from core.hud import text as hudtext

#: The labels' defaults, used when the string file lacks a key — the file
#: is the one home of the wording; these only keep a damaged file from
#: blanking the one panel that tells the player what to do.
DEFAULTS = {
    "notice_waiting": "The game is waiting for an answer",
    "notice_answer": "F12 to answer",
}
#: Reference geometry (1080 px tall), scaled by `win_h / 1080`.
REF_W, REF_H = 760, 190
#: How much of the held frame is left when it is dimmed (0..255 black).
DIM_ALPHA = 120


def words(labels):
    """`(waiting, answer)` from the string file, with the defaults."""
    labels = labels or {}
    return tuple(labels.get(k) or DEFAULTS[k]
                 for k in ("notice_waiting", "notice_answer"))


def what_for(kind, screen_id, top=None, engine_name=None):
    """The one line naming what the game shows: the screen's own reason
    (a hand-over), else the game's screen by its engine name and id."""
    if top is not None and kind == "hand_over":
        getter = getattr(top, "fallback_reason", None)
        reason = getter() if callable(getter) else ""
        if reason:
            return reason
    if engine_name is None:
        from core import screen_names
        engine_name = screen_names.engine_name(screen_id)
    return f"{engine_name} ({screen_id})"


def panel_rect(win_w, win_h):
    scale = win_h / 1080
    w, h = int(REF_W * scale), int(REF_H * scale)
    return pygame.Rect((win_w - w) // 2, (win_h - h) // 2, w, h)


class Notice:
    """The dimmed held frame and its panel, for one App."""

    def __init__(self):
        self._base = None       # the dimmed frame
        self._orig = None       # the frame as it was held, undimmed
        self._key = None        # (size, what) it was built for

    def reset(self, surface=None):
        """The notice has ended. With `surface` (a plain hold follows),
        the held frame is put back as it was, without the panel."""
        if surface is not None and self._orig is not None and \
                self._orig.get_size() == surface.get_size():
            surface.blit(self._orig, (0, 0))
        self._base = self._orig = None
        self._key = None

    def render(self, surface, style, labels, what):
        """Draw the notice over the held `surface`. Returns the panel rect.

        The first call of a notice copies what the surface holds (the last
        HD frame, `handover.render_hold` has made sure of that) and dims
        it; every later call blits that copy, so nothing accumulates."""
        size = surface.get_size()
        key = (size, what)
        if self._base is None or self._key != key:
            if self._base is None or self._base.get_size() != size:
                self._orig = surface.copy()
                base = surface.copy()
                shade = pygame.Surface(size, pygame.SRCALPHA)
                shade.fill((0, 0, 0, DIM_ALPHA))
                base.blit(shade, (0, 0))
                self._base = base
            self._key = key
        surface.blit(self._base, (0, 0))
        return draw_panel(surface, style, labels, what)


def draw_panel(surface, style, labels, what, rect=None):
    """The panel alone, in `rect` or centred: HUD popup (glass, the frame
    colour), the waiting line, the screen's line, "F12 to answer"."""
    win_w, win_h = surface.get_size()
    scale = win_h / 1080
    rect = pygame.Rect(rect) if rect is not None else panel_rect(win_w, win_h)
    hud.popup(surface, rect, scale)
    waiting, answer = words(labels)
    line_h = max(8, rect.h // 4)
    rows = [(waiting, "title"), (what or "", "label"), (answer, "action")]
    top = rect.y + (rect.h - line_h * len(rows)) // 2
    for text, role in rows:
        if not text:
            top += line_h
            continue
        # A line wider than the panel takes a smaller font, never a
        # resampled picture of the text (and never a silent cut).
        inner = rect.w - 2 * max(4, int(20 * scale))
        box_h = line_h
        surf = hudtext.render(style, text, role, box_h)
        while surf.get_width() > inner and box_h > 8:
            box_h = int(box_h * 0.9)
            surf = hudtext.render(style, text, role, box_h)
        hudtext.blit(surface, surf, pygame.Rect(rect.x, top, rect.w, line_h))
        top += line_h
    return rect
