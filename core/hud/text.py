"""Text in the HUD: every string is drawn in code, sized by cap height.

Decision 71: nothing is baked. A HUD word is sized so its CAP HEIGHT is a
measured fraction of the box it sits in (`measured.text.<role>.cap`,
off Data's mockup), which is what makes a button's label the same weight
at 1080p and 2160p: the box scales with the window, and the text scales
with the box.

The face is the tree's display font, Aldrich (`chosen.font`; the choice
is parked, 169 P3), drawn through `StyleRenderer.render_text` so the
blocked-glyph fallback of decision 30 still applies.
"""
import pygame

from core import lang

from core.hud import style as hudstyle

#: font px -> cap-height px, measured once per font on "H".
def cap_ratio(style_renderer):
    # KEPT ON THE RENDERER, not in a dict keyed by `id(style_renderer)`
    # (work order 179): Python hands a dead object's id to the next one,
    # so a renderer built after another was dropped — every tool and check
    # that stands an app up — inherited the old one's ratio and drew every
    # HUD word at the wrong size (38 px for 16 on the main menu, found by
    # the fresh clone's full run). The app's one renderer never died, so
    # the app never showed it.
    ratio = getattr(style_renderer, "_hud_cap_ratio", None)
    if ratio is None:
        font = style_renderer.get_font(200)
        ink = font.render("H", True, (255, 255, 255)).get_bounding_rect()
        ratio = max(0.3, ink.h / 200.0)
        style_renderer._hud_cap_ratio = ratio
    return ratio


def size_for(style_renderer, role, box_h, scale=1.0):
    """Font px for `role` in a box `box_h` device px tall."""
    st = hudstyle.get()
    cap = float(st.get(f"text.{role}.cap")) * box_h * scale
    px = cap / cap_ratio(style_renderer)
    return max(int(st.get("text_min_px")), int(round(px)))


def colour(role):
    return hudstyle.get().colour(f"text.{role}.color")


def render(style_renderer, text, role, box_h, colour_=None, scale=1.0):
    """The surface for `text` in `role`'s size and colour."""
    size = size_for(style_renderer, role, box_h, scale)
    return style_renderer.render_text(text, size, colour_ or colour(role))


def blit(surface, surf, rect, align="center", valign="center", ink=True):
    """Place `surf` in `rect`. Vertically centred BY INK when `ink`: an
    all-caps word centred by its line box sits high (galaxy frame v2,
    16 September 2026 — the same fault, kept fixed here)."""
    r = pygame.Rect(rect)
    if surf.get_width() > r.w > 0 and lang.current() != lang.DEFAULT:
        # THE TEXT-FIT RULE for a one-line label (`core/textfit`: wrap, then
        # shrink): a German word longer than the English one it replaces
        # is drawn smaller, never past its box (work order 200 C). English
        # is left exactly as it was drawn before.
        surf = pygame.transform.smoothscale(
            surf, (r.w, max(1, surf.get_height() * r.w // surf.get_width())))
    if align == "left":
        x = r.x
    elif align == "right":
        x = r.right - surf.get_width()
    else:
        x = r.x + (r.w - surf.get_width()) // 2
    if ink:
        b = surf.get_bounding_rect()
        if valign == "top":
            y = r.y - b.y
        else:
            y = r.y + (r.h - b.h) // 2 - b.y
    else:
        y = r.y + (r.h - surf.get_height()) // 2
    surface.blit(surf, (x, y))
    return pygame.Rect(x, y, surf.get_width(), surf.get_height())
