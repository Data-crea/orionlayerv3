"""The Leaders screen's dialogs: the hire popup and the skill help box.

The game's own message boxes — the confirmation, the message and the
warning (`Officer_Screen_User_Box_`, officer.cpp:1696-1722) — are drawn
by `screens/fleets/fltbox`, reused as it is: `core/gamebox` recognises
them by their whole field list and the crop is the game's own pixels
(the marked limitation open fix 29 would lift).

THE HIRE POPUP (`ldrpopup` says which leader and why it is known).

  identified    HD draws it: the popup art MAINPUPS.LBX 0x39 at its
                native rectangle, the portrait, the title
                `Leader_Name_(id, 1)`, the skill lines exactly as the
                row prints them, the question `Ask_For_Hire_` puts, and
                REJECT / HIRE — every piece at the source's own offsets
                (ldrpopup). DEVIATION `hd_font`, as everywhere.
  not identified   the game's own pixels of the popup's rectangle,
                scaled nearest-neighbour onto that same rectangle — the
                `core/gamebox` limitation, for a popup whose leader the
                wire does not name. The buttons answer either way,
                through the popup's own fields.

THE SKILL HELP BOX. `Print_Officer_Skill_Help_` (officer.cpp:1761-1792)
opens `TEXTBOX::Text_Box_` with a title and a paragraph and changes
nothing in the game. **DEVIATION `hd_skill_help`: HD draws that box
itself and does not ask the game to open it** — the text is fully
determined by what HD holds (SKILDESC.LBX, the record, the bonus), and
opening the game's box would put the game into a modal loop for a
display-only answer. Placed where `Box_Centered_On_XY_` places it off
the main screen: x 130, 380 wide, the paragraph wrapped at 339 and the
box as tall as the text plus 85 (textbox.cpp:40-88, :186-224).
"""
import pygame

from core.hud import blocks as hud

from core import textfit

from . import ldrdraw as draw
from . import ldrgeom as geom
from . import ldrpopup

#: `Box_Centered_On_XY_` off the main screen (textbox.cpp:52-55): x 130;
#: the paragraph is 339 wide (:186) inside a 380-wide box.
TEXTBOX_X, TEXTBOX_W, TEXTBOX_TEXT_W = 130, 380, 339
TEXTBOX_PAD_H = 85
TEXTBOX_TEXT_DX, TEXTBOX_TEXT_DY = 20, 42


def framebuffer_surface(game_state):
    """The game's 640x480 picture, or None — `fltbox`'s own reader."""
    from screens.fleets import fltbox
    return fltbox._framebuffer_surface(game_state)


def popup_rects(screen):
    """`[(key, window rect)]` of the popup's two answers — the drawing's
    and the hit test's (decision 5)."""
    layout = screen.layout
    return [("reject", draw.rect(layout, ldrpopup.REJECT_RECT)),
            ("hire", draw.rect(layout, ldrpopup.HIRE_RECT))]


def draw_popup(surface, screen, view, rows_words, art, game_state):
    """The hire popup, HD-drawn when its leader is known."""
    layout = screen.layout
    box = draw.rect(layout, ldrpopup.popup_rect())
    popup = view.popup
    if popup is None:
        return
    if not popup.identified:
        fb = framebuffer_surface(game_state)
        crop = None
        if fb is not None:
            x1, y1, x2, y2 = ldrpopup.popup_rect()
            crop = fb.subsurface(pygame.Rect(x1, y1, x2 - x1 + 1,
                                             y2 - y1 + 1)).copy()
        if crop is not None:
            surface.blit(pygame.transform.scale(crop, box.size), box.topleft)
        else:
            draw.draw_box(surface, screen, ldrpopup.popup_rect())
        return
    # The HUD popup block (decision 71, work order 169): every dialog
    # wears it; the OFFICER.LBX popup picture is not drawn — DEVIATION,
    # the same as the buttons' (`ldrdraw.draw_button`).
    hud.popup(surface, box, layout.scale)
    idx = popup.leader
    rec = view.leaders[idx]
    sprite = art.portrait(rec.pict_num) if art is not None and \
        art.available else None
    if sprite is not None:
        px, py = ldrpopup.PORTRAIT_AT
        surface.blit(draw.magnified(sprite, layout), draw.point(layout, px, py))
    words = rows_words["words"]
    level, title_word, the_word = rows_words["name_parts"](rec, idx)
    ink = draw.text_colour(art, "normal")
    x, y, w, h = ldrpopup.TITLE_RECT
    title_rect = draw.rect(layout, (x, y, x + w - 1, y + h - 1))
    from core import leaderskills as ls
    name = ls.leader_name(rec, title_word or "", the_word)
    _paragraph(surface, screen, name, title_rect, ink,
               draw.font_px(layout, "name"))
    _popup_skills(surface, screen, rec, level, words, art, ink)
    question = ldrpopup.question(view, idx, words.h, title_word or "",
                                 the_word)
    x, y, w, h = ldrpopup.MESSAGE_RECT
    _paragraph(surface, screen, question or "",
               draw.rect(layout, (x, y, x + w - 1, y + h - 1)), ink,
               draw.font_px(layout, "strip"))
    for key, sprite_name, native in (
            ("reject", "popup_reject", ldrpopup.REJECT_RECT),
            ("hire", "popup_hire", ldrpopup.HIRE_RECT)):
        r = draw.rect(layout, native)
        # HUD small buttons with their words (decision 71).
        hud.small_button(surface, r, layout.scale)
        if True:
            draw.blit_text(surface, screen.style, key.upper(), r.centerx,
                           r.y + r.h // 4, r.w - 4,
                           draw.font_px(layout, "button"), ink, "center")


def _popup_skills(surface, screen, rec, level, words, art, ink):
    """The skill lines as `Print_Officer_Data_` prints them in the popup
    (officer.cpp:3747-3837 with the popup's arguments, ldrpopup)."""
    from core import leaderskills as ls
    layout = screen.layout
    size = draw.font_px(layout, "skill")
    right = draw.point(layout, ldrpopup.TEXT_X + ldrpopup.RIGHT_COLUMN
                       - geom.VALUE_RIGHT_INSET, 0)[0]
    y = ldrpopup.TEXT_Y
    for sid in ls.displayed_skills(rec):
        icon = art.skill_icon(sid) if art is not None and art.available \
            else None
        if icon is not None:
            surface.blit(draw.magnified(icon, layout),
                         draw.point(layout, ldrpopup.TEXT_X + 2, y - 4))
        at = draw.point(layout, ldrpopup.TEXT_X + geom.SKILL_NAME_DX, y)
        value = ls.c_format(ls.SKILLS[sid][6], ls.skill_bonus(level, sid))
        drawn = draw.blit_text(surface, screen.style, value, right, at[1],
                               right - at[0], size, ink, "right")
        draw.blit_text(surface, screen.style,
                       words.estring(ls.SKILL_NAME_ESTRINGS[sid]) or "",
                       at[0], at[1], (drawn.x if drawn else right) - at[0] - 4,
                       size, ink)
        y += geom.SKILL_STEP


def _paragraph(surface, screen, text, r, colour, size):
    """A centred paragraph squeezed into `r` (`ERIC::Print_Paragraph_
    Centered_` / `BILL::Squeeze_Paragraph_Centered_`: the original
    squeezes, HD shrinks — `core/textfit`)."""
    if not text:
        return
    sizes = list(range(size, draw.MIN_FONT - 1, -1))
    lines, _size = textfit.squeeze_lines(screen.style, text, r.w, r.h,
                                         sizes, colour)
    total = textfit.block_height(lines)
    y = r.y + max(0, (r.h - total) // 2)
    for line in lines:
        surface.blit(line, (r.centerx - line.get_width() // 2, y))
        y += line.get_height()


def skill_help_rect(screen, title, body):
    """The help box's window rect for this text (textbox.cpp:40-88)."""
    layout = screen.layout
    size = draw.font_px(layout, "strip")
    width = draw.rect(layout, (0, 0, TEXTBOX_TEXT_W - 1, 0)).w
    lines = textfit.wrap_text(screen.style, body or "", size, width)
    line_h = screen.style.render_text("Ag", size, (0, 0, 0)).get_height()
    native_h = int(round(len(lines) * line_h / draw.native_scale(layout)))
    h = min(TEXTBOX_PAD_H + native_h, geom.NATIVE_H - 8)
    y = (geom.NATIVE_H - h) // 2
    return draw.rect(layout, (TEXTBOX_X, y, TEXTBOX_X + TEXTBOX_W - 1,
                              y + h - 1)), lines, size


def draw_skill_help(surface, screen, title, body, art):
    """DEVIATION `hd_skill_help` — see the module docstring."""
    r, lines, size = skill_help_rect(screen, title, body)
    hud.popup(surface, r, screen.layout.scale)
    ink = draw.text_colour(art, "normal")
    head = draw.text_colour(art, "selected")
    scale = draw.native_scale(screen.layout)
    draw.blit_text(surface, screen.style, title, r.centerx,
                   r.y + int(8 * scale), r.w - int(20 * scale),
                   draw.font_px(screen.layout, "name"), head, "center")
    y = r.y + int(TEXTBOX_TEXT_DY * scale)
    x = r.x + int(TEXTBOX_TEXT_DX * scale)
    for line in lines:
        surf = screen.style.render_text(line, size, ink)
        surface.blit(surf, (x, y))
        y += surf.get_height()
    return r
