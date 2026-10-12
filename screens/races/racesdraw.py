"""Drawing the Races screen — every piece at the HD image of its native
rectangle (`racesgeom`, through `core/researchnative`, the helpers the
Leaders screen already uses: `screens/leaders/ldrdraw`).

WHAT IS TRANSCRIPTION AND WHAT IS OURS — each marked where it happens:

  TRANSCRIPTION   every position, every string, which portrait, the frame
                  colours (`_banner_color_high/low` by the player's colour,
                  racescrn.cpp:50-52, :270-279), the slider's height, the
                  spy icons' spacing, the relation word on hover, the
                  relation bar's picture (RACES.LBX 3, :240-243) and the
                  greyed mission words of a slot without missions
                  (work order 223)
  OMISSION        `outer_frame` — RACES.LBX 0 (the background with the
                  panels, bars and buttons painted in) is not drawn: decision
                  71's HUD style draws the panels, the striped fields (the
                  shared field, work order 223), the sliders and the
                  buttons in code (DEVIATION `hud_parts`)
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
from core.hud import hover
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
    # The agents' strip: where the pool's spies stand and are dropped
    # back — a field, as RACES.LBX 0 paints it (work order 223).
    hud.field(surface, nd.rect(layout, geom.AGENT_BOX), layout.scale)
    # The title stands on the shell's plate (work order 225; the words
    # are baked into RACES.LBX 0 in the original — `button_words`).
    x, y = nd.point(layout, geom.BONUS_BOX[0] + 8, geom.BONUS_BOX[1] + 3)
    nd.blit_text(surface, screen.style, WORDS["bonuses"], x, y,
                 nd.rect(layout, (0, 0, 80, 0)).w, nd.font_px(layout, "note"),
                 hudtext.colour("button"))


def draw_fields(surface, screen, i):
    """The slot's striped fields as the original paints them into
    RACES.LBX 0: the treaty field, the spy strip — where spies are
    dropped — and the portrait cell, each the shared field (work order
    223: "I cannot even see where to place the spies")."""
    layout = screen.layout
    for box in (geom.treaty_box(i), geom.spy_box(i), geom.portrait_box(i)):
        hud.field(surface, nd.rect(layout, box), layout.scale)


def draw_slot(surface, screen, slot, art, lit=False, carried=0,
              mission=None):
    """One race: portrait and frame, name, treaty lines or NO CONTACT, the
    IGNORED mark, and — for an active race — the bar, the slider, the spies
    and the mission row."""
    layout, style = screen.layout, screen.style
    i = slot.index
    draw_fields(surface, screen, i)
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
    width = banner_frame(surface, layout, cell, slot.colour, art)
    if lit:
        # LOOK EXCEPTION transcription: the WHO box in the cycling 0xFF (:555)
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
        # The spies in hand have left the group (`Move_Spies_Group_`,
        # racescrn.cpp:411-414): it shows what stays (work order 226 E).
        draw_icons(surface, screen, geom.SPY_GROUP[i], slot.spies - carried,
                   screen.my_race, art)
        _draw_missions(surface, screen, i,
                       slot.mission if mission is None else mission)
    else:
        _draw_missions(surface, screen, i, None)


def banner_frame(surface, layout, cell, colour, art):
    """The portrait's frame in the player's banner colours — high round
    it, low on it (`Draw_Race_Photos_`, racescrn.cpp:270-279; the race
    report's racerprt.cpp:105-107). Returns the line width."""
    width = max(1, int(nd.native_scale(layout)))
    c = colour if 0 <= colour < 8 else 0
    # LOOK EXCEPTION transcription: the banner frame's colours (racescrn.cpp:50-52, :270-279)
    pygame.draw.rect(surface, _pal(art, BANNER_HIGH[c], (180, 180, 180)),
                     cell.inflate(2 * width, 2 * width), width)
    pygame.draw.rect(surface, _pal(art, BANNER_LOW[c], (110, 110, 110)),
                     cell, width)
    return width


def draw_empty(surface, screen, i, art):
    """An unused slot: its fields, NO CONTACT, the empty bar track with
    the slider parked (:121-125, :247) and the mission words greyed — the
    words RACES.LBX 0 has baked in where no mission button is drawn."""
    draw_fields(surface, screen, i)
    _no_contact(surface, screen, i, art)
    _draw_bar(surface, screen, i, None, art)
    _draw_missions(surface, screen, i, None)


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
    """The bar and the slider (2, 25 x 13, a HUD part). A race in contact
    has RACES.LBX 3 drawn — green at the top to red at the bottom, the
    colour IS what the bar says (`Draw_Relations_Sliders_`, :240-243);
    without the extracted picture it is a field. An unused slot draws no
    bar: the background's empty track shows, a field here, and the
    slider stands parked (:244-248)."""
    layout = screen.layout
    bx, by = geom.BAR[i]
    track = nd.rect(layout, geom.bar_box(i))
    pic = art.bar() if (art is not None and relation is not None) else None
    if pic is not None:
        surface.blit(nd.stretched(pic, track), track.topleft)
    else:
        hud.field(surface, track, layout.scale)
    if relation is not None:
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


def draw_spy_hand(surface, screen, hand, pointer, art=None):
    """The spies in hand on the pointer, as the original carries them
    (work order 226 E, Data's decision 4): `Redraw_Spy_Mouse_`
    (racescrn.cpp:608-622) puts the spy icon at (1, 1) of the mouse
    picture and, for more than one, the count at (8, 4); the picture is
    drawn at the pointer + (3, 2) (`Draw_Race_Screen_`, :584-588: :586). HD draws
    the same at its own pointer, every frame (`pointer`: window px).
    Drawing only — nothing is sent while the spies are carried."""
    if hand is None or pointer is None:
        return
    layout = screen.layout
    k = nd.native_scale(layout)
    x0, y0 = pointer[0] + round(3 * k), pointer[1] + round(2 * k)
    icon = art.spy(screen.my_race) if art is not None else None
    if icon is not None:
        surface.blit(nd.magnified(icon, layout),
                     (x0 + round(1 * k), y0 + round(1 * k)))
    if hand.count > 1 or icon is None:
        nd.blit_text(surface, screen.style, f"{hand.count}",
                     x0 + round(8 * k), y0 + round(4 * k),
                     nd.rect(layout, (0, 0, 40, 0)).w,
                     nd.font_px(layout, "name"), ink(art, "high"))


def _draw_missions(surface, screen, i, mission):
    """The mission row (RACES.LBX 10+i, 17+i, 24+i), the current one 'on'
    — a click sends the race's mission with open fix 64 (work order 197;
    `racesspies`). `mission` None: no buttons, the words greyed, as the
    background shows them under a slot with none (empty or eliminated)."""
    layout = screen.layout
    for k, word in enumerate(WORDS["missions"]):
        r = nd.rect(layout, geom.mission_rect(i, k))
        state = ("disabled" if mission is None else
                 "active" if k == mission else "normal")
        hud.small_button(surface, r, layout.scale, state)
        colour = hudtext.colour("button")
        if state == "disabled":
            colour = tuple(v // 2 for v in colour)
        size = nd.font_px(layout, "cost")
        nd.blit_text(surface, screen.style, word, r.centerx,
                     r.y + (r.h - size) // 2, r.w - 2, size, colour,
                     "center")


def draw_buttons(surface, screen, live, armed):
    layout = screen.layout
    from core.hud import shell
    for name in geom.BUTTONS:
        if name == "exit" and hasattr(screen, "exit_rect"):
            # The closing action: slanted, in the panel's corner (225).
            shell.draw_button(surface, screen.exit_rect(), screen.ref_layout,
                              WORDS[name], screen.style,
                              "disabled" if name not in live else "normal")
            continue
        r = nd.rect(layout, geom.button_rect(name))
        state = hover.pointer_state(r, "disabled" if name not in live else
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
