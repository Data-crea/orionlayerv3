"""Drawing the Races screen — every piece at the HD image of its native
rectangle (`racesgeom`, through `core/researchnative`, the helpers the
Leaders screen already uses: `screens/leaders/ldrdraw`).

WHAT IS TRANSCRIPTION AND WHAT IS OURS — each marked where it happens:

  TRANSCRIPTION   every position, every string, which portrait, the frame
                  colours (`_banner_color_high/low` by the player's colour,
                  racescrn.cpp:50-52, :270-279), the slider's height, the
                  spy icons' spacing, the relation word on hover
  OMISSION        `outer_frame` — RACES.LBX 0 (the background with the
                  panels, bars and buttons painted in) is not drawn: decision
                  71's HUD style draws the panels, the bars, the sliders and
                  the buttons in code (DEVIATION `hud_parts`)
  DEVIATION       `button_words` — the buttons, the mission row, the title
                  and the BONUSES label are words the original has baked into
                  its art; HD writes them (OrionLayer's words)
  DEVIATION       `hd_font` — the bitmap fonts become the HD font at the
                  native line height, shrunk to the original's width
  HD EXTENSION    `sprite_scale` — portraits and spy icons at an integer
                  magnification, centred on their native cell
"""
import pygame

from core.hud import blocks as hud
from core.hud import text as hudtext
from screens.leaders import ldrdraw as nd

from . import racesgeom as geom

#: `_race_normal_color` / `_race_high_color` body indices (racescrn.cpp:
#: 48-49) and what they are in RACES.LBX 0's palette when it is absent.
TEXT_INDEX = {"normal": 185, "high": 191}
TEXT_FALLBACK = {"normal": (150, 170, 190), "high": (230, 236, 240)}
BANNER_HIGH = (67, 139, 147, 38, 61, 95, 106, 47)
BANNER_LOW = (70, 138, 149, 35, 59, 96, 110, 49)
#: The palette-cycled highlight (colour 0xFF, :590) — HD draws one tone.
HIGHLIGHT = 0xFF
HIGHLIGHT_FALLBACK = (240, 220, 120)

#: DEVIATION `button_words`: OrionLayer's words where the art has them.
WORDS = {"exit": "RETURN", "ignore": "IGNORE", "report": "REPORT",
         "audience": "AUDIENCE", "war": "DECLARE WAR",
         "missions": ("ESPIONAGE", "SABOTAGE", "HIDE"),
         "title": "RACE RELATIONS", "bonuses": "BONUSES"}


def ink(art, key):
    rgb = art.palette_rgb(TEXT_INDEX[key]) if art is not None else None
    return tuple(rgb) if rgb else TEXT_FALLBACK[key]


def _pal(art, index, fallback):
    rgb = art.palette_rgb(index) if art is not None else None
    return tuple(rgb) if rgb else fallback


def draw_frame(surface, screen):
    """The panels: seven slots, the agents' strip with the bonuses, the
    buttons' box — glass HUD panels (174's blocks)."""
    for i in range(geom.SLOTS):
        nd.draw_box(surface, screen, geom.slot_box(i))
    nd.draw_box(surface, screen, geom.BONUS_BOX)
    nd.draw_box(surface, screen, geom.BUTTON_BOX)
    layout = screen.layout
    # The title on the HUD's title plate, as the galaxy map's (the words
    # are baked into RACES.LBX 0 in the original — `button_words`).
    hud.title_plate(surface, nd.point(layout, 320, 0)[0], 0, layout.scale,
                    WORDS["title"], screen.style)
    x, y = nd.point(layout, geom.BONUS_BOX[0] + 8, geom.BONUS_BOX[1] + 3)
    nd.blit_text(surface, screen.style, WORDS["bonuses"], x, y,
                 nd.rect(layout, (0, 0, 80, 0)).w, nd.font_px(layout, "note"),
                 hudtext.colour("button"))


def draw_slot(surface, screen, slot, art, lit=False):
    """One race: portrait and frame, name, treaty lines or NO CONTACT, the
    IGNORED mark, and — for an active race — the bar, the slider, the spies
    and the mission row."""
    layout, style = screen.layout, screen.style
    i = slot.index
    px, py = geom.PICTURE[i]
    cell = nd.rect(layout, (px, py, px + geom.PORTRAIT[0] - 1,
                            py + geom.PORTRAIT[1] - 1))
    pic = art.portrait(slot.race) if art is not None else None
    if pic is not None:
        big = nd.magnified(pic, layout)
        surface.blit(big, big.get_rect(center=cell.center))
    else:
        style.draw_plate(surface, cell.inflate(-4, -4), layout.scale,
                         nd.BOX_OUTLINE)
    if slot.eliminated and art is not None and art.eliminated() is not None:
        over = nd.magnified(art.eliminated(), layout)
        surface.blit(over, over.get_rect(center=cell.center))
    width = max(1, int(nd.native_scale(layout)))
    c = slot.colour if 0 <= slot.colour < 8 else 0
    pygame.draw.rect(surface, _pal(art, BANNER_HIGH[c], (180, 180, 180)),
                     cell.inflate(2 * width, 2 * width), width)
    pygame.draw.rect(surface, _pal(art, BANNER_LOW[c], (110, 110, 110)),
                     cell, width)
    if lit:
        # The original boxes the portrait in the cycling 0xFF (:555); HD
        # also lights the whole panel's edge — the popup's lit edge, so
        # the race a click will pick is unmistakable (HD EXTENSION
        # `who_lit`).
        pygame.draw.rect(surface, _pal(art, HIGHLIGHT, HIGHLIGHT_FALLBACK),
                         cell.inflate(4 * width, 4 * width), width)
        hud.panel(surface, nd.rect(layout, geom.slot_box(i)), layout.scale,
                  lit=True, filled=False)
    name_at = nd.point(layout, px + geom.NAME_W // 2, py + geom.NAME_DY)
    nd.blit_text(surface, style, slot.name, name_at[0], name_at[1],
                 nd.rect(layout, (0, 0, geom.NAME_W - 1, 0)).w,
                 nd.font_px(layout, "status"), ink(art, "high"), "center")
    if slot.ignored:
        at = nd.point(layout, px + geom.IGNORED_DX, py + geom.IGNORED_DY)
        nd.blit_text(surface, style, screen.words_ignored, at[0], at[1],
                     cell.w, nd.font_px(layout, "note"), ink(art, "high"),
                     "center")
    _draw_text(surface, screen, slot, art)
    _draw_bar(surface, screen, i, slot.relation if slot.active else None,
              art)
    if slot.active and not slot.eliminated:
        draw_icons(surface, screen, geom.SPY_GROUP[i], slot.spies,
                   screen.my_race, art)
        _draw_missions(surface, screen, i, slot.mission)


def draw_empty(surface, screen, i, art):
    """An unused slot: NO CONTACT, and the slider parked (:121-125, :247)."""
    _no_contact(surface, screen, i, art)
    _draw_bar(surface, screen, i, None, art)


def _no_contact(surface, screen, i, art):
    tx, ty = geom.TEXT[i]
    at = nd.point(screen.layout, tx + geom.NO_CONTACT_DX,
                  ty + geom.NO_CONTACT_DY)
    nd.blit_text(surface, screen.style, screen.words_no_contact, at[0], at[1],
                 nd.rect(screen.layout, (0, 0, geom.TEXT_BOX[0], 0)).w,
                 nd.font_px(screen.layout, "name"), ink(art, "normal"),
                 "center")


def _draw_text(surface, screen, slot, art):
    if not slot.contact:
        _no_contact(surface, screen, slot.index, art)
        return
    if not slot.lines:
        return
    tx, ty = geom.TEXT[slot.index]
    box = nd.rect(screen.layout, (tx, ty, tx + geom.TEXT_BOX[0] - 1,
                                  ty + geom.TEXT_BOX[1] - 1))
    size = nd.font_px(screen.layout, "skill")
    step = box.h // max(3, len(slot.lines))
    size = min(size, max(nd.MIN_FONT, int(step * 0.85)))
    y = box.y + (box.h - step * len(slot.lines)) // 2
    for line in slot.lines:
        nd.blit_text(surface, screen.style, line, box.centerx, y, box.w,
                     size, ink(art, "normal"), "center")
        y += step


def _draw_bar(surface, screen, i, relation, art):
    """The bar (RACES.LBX 3, 8 x 88) and the slider (2, 25 x 13) as HUD
    parts; an unused slot shows the slider parked (:241-251)."""
    layout = screen.layout
    bx, by = geom.BAR[i]
    if relation is not None:
        track = nd.rect(layout, (bx, by, bx + geom.BAR_SIZE[0] - 1,
                                 by + geom.BAR_SIZE[1] - 1))
        hud.panel(surface, track, layout.scale, filled=True, dense=True)
        y = geom.slider_y(i, relation)
    else:
        y = by + geom.SLIDER_PARKED
    sx = geom.SLIDER_X[i]
    knob = nd.rect(layout, (sx, y, sx + geom.SLIDER_SIZE[0] - 1,
                            y + geom.SLIDER_SIZE[1] - 1))
    hud.small_button(surface, knob, layout.scale,
                     "active" if relation is not None else "disabled")


def relation_word(surface, screen, slot, art):
    """On hover over the bar: the word, centred on the bar at the slider
    (:563-566)."""
    i = slot.index
    at = nd.point(screen.layout, geom.BAR[i][0] + 4,
                  geom.slider_y(i, slot.relation) + 1)
    nd.blit_text(surface, screen.style, slot.relation_word, at[0], at[1],
                 nd.rect(screen.layout, (0, 0, 120, 0)).w,
                 nd.font_px(screen.layout, "status"), ink(art, "high"),
                 "center")


def draw_icons(surface, screen, box, count, race, art):
    """`Draw_Icon_Group_` (:659-675): `count` spy icons from the box's left,
    `Calculate_Icon_Group_Data_`'s step apart. Without the art a count."""
    if count <= 0:
        return
    layout = screen.layout
    icon = art.spy(race) if art is not None else None
    if icon is None:
        at = nd.point(layout, box[0] + 3, box[1] + 3)
        nd.blit_text(surface, screen.style, f"{count}", at[0], at[1],
                     nd.rect(layout, (0, 0, 60, 0)).w,
                     nd.font_px(layout, "name"), ink(art, "normal"))
        return
    step = geom.icon_spacing(count, box, icon.get_width())
    big = nd.magnified(icon, layout)
    for k in range(count):
        surface.blit(big, nd.point(layout, box[0] + k * step, box[1]))


def _draw_missions(surface, screen, i, mission):
    """The mission row (RACES.LBX 10+i, 17+i, 24+i), the current one lit —
    DISPLAY ONLY: a click on it is not sent (parked, 175)."""
    layout = screen.layout
    for k, word in enumerate(WORDS["missions"]):
        r = nd.rect(layout, geom.mission_rect(i, k))
        hud.small_button(surface, r, layout.scale,
                         "active" if k == mission else "normal")
        size = nd.font_px(layout, "cost")
        nd.blit_text(surface, screen.style, word, r.centerx,
                     r.y + (r.h - size) // 2, r.w - 2, size,
                     hudtext.colour("button"), "center")


def draw_buttons(surface, screen, live, armed):
    layout = screen.layout
    for name in geom.BUTTONS:
        r = nd.rect(layout, geom.button_rect(name))
        state = ("disabled" if name not in live else
                 "active" if name == armed else "normal")
        hud.small_button(surface, r, layout.scale, state)
        colour = hudtext.colour("button")
        if state == "disabled":
            colour = tuple(v // 2 for v in colour)
        size = nd.font_px(layout, "button")
        nd.blit_text(surface, screen.style, WORDS[name], r.centerx,
                     r.y + (r.h - size) // 2, r.w - 4, size, colour,
                     "center")


def draw_bonuses(surface, screen, bonuses, art):
    """SPY: n% and AGENT: n% (`Squeeze_Centered_Print_`, :222-229)."""
    if bonuses is None:
        return
    layout = screen.layout
    for (x, y), w, label, value in (
            (geom.SPY_BONUS_AT, geom.SPY_BONUS_W, screen.words_spy,
             bonuses[0]),
            (geom.AGENT_BONUS_AT, geom.AGENT_BONUS_W, screen.words_agent,
             bonuses[1])):
        if not label:
            continue
        # `Squeeze_Centered_Print_(x, y, text, w)`: centred in [x, x + w].
        at = nd.point(layout, x + w // 2, y)
        nd.blit_text(surface, screen.style, f"{label}{value}%", at[0], at[1],
                     nd.rect(layout, (0, 0, w, 0)).w,
                     nd.font_px(layout, "status"), ink(art, "normal"),
                     "center")
