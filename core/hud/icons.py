"""Button icons beside words (work order 179, part 6).

`icon_beside` is for a screen that draws its button's word itself; the
HUD blocks' own label path (`blocks._label`) follows the same rule — the
word stays whole, and the icon is drawn only when both fit. `RECORD`
lets a check or a tool see which icons a screen really drew.
"""
import pygame

from core.hud import art

#: None, or a list every drawn button icon's key is appended to — for the
#: smoke test (work order 179, 006h), which needs to know
#: which glyphs a screen really shows, not which it asked for.
RECORD = None


def _drawn(icon):
    if RECORD is not None:
        RECORD.append(icon)


def icon_beside(surface, rect, icon, text_w, dim=False):
    """For a screen that draws its button's word itself (work order 179):
    the glyph `icon` left of a word `text_w` wide, the two centred as ONE
    group in `rect`. Returns the x the word's CENTRE goes to — the rect's
    own centre when there is no icon or the two do not fit, so a narrow
    button keeps its word whole and simply shows no icon."""
    r = pygame.Rect(rect)
    ic = art.icon(icon, int(r.h * 0.6)) if icon else None
    if ic is None:
        return r.centerx
    gap = int(r.h * 0.12)
    total = ic.get_width() + gap + text_w
    if total > r.w - 2 * int(r.h * 0.2):
        return r.centerx
    left = r.centerx - total // 2
    if dim:
        ic = ic.copy()
        ic.set_alpha(128)
    surface.blit(ic, (left, r.y + (r.h - ic.get_height()) // 2))
    _drawn(icon)
    return left + ic.get_width() + gap + text_w // 2


def fitted_word(surface, style, rect, text, color, share=0.52, icon=None,
                dim=False):
    """One line, centred, shrunk until it fits the box's width — with
    `icon` beside it where both fit (`icon_beside`). Fleets' `_centred`
    until work order 179, moved here with the icon so that file stayed
    inside the line guideline."""
    size = max(8, int(rect.height * share))
    while size > 8:
        surf = style.render_text(text, size, color)
        if surf.get_width() <= rect.width - 2:
            break
        size -= 1
    else:
        surf = style.render_text(text, size, color)
    cx = icon_beside(surface, rect, icon, surf.get_width(), dim)
    surface.blit(surf, surf.get_rect(center=(cx, rect.centery)))
