"""The combat target window — work order 228 B (Data: "the original opens a
window with the star, the orbits and the planets").

After TURN, where the player's ships meet more than nothing at a star, the
original asks which target to fight: `COMBFIND::Get_Local_Human_Target_`
(combfind.cpp:928-975) runs `MAINPUPS::Defense_Colony_Selection_Popup_`
(mainpups.cpp:547-606) — the STAR SYSTEM WINDOW, drawn by the function that
draws the galaxy map's (`SYS::Draw_System_Display_Popup_`, mode 1, with the
map window's offsets 13 / 47, mainpups.cpp:2121-2150) and given its fields
by the same builder (`SYS::Wrapper_For_Informational_System_Fields_`,
sys.cpp:1722-1744). Open fix 49 reports it as id 64 with its TPOP block.

TRANSCRIPTION — what it shows (one drawing with the map's: `syswindow`,
`sysfleets`):
  the title     E 0x45 "%s select combat at %s", the choosing player's race
                and the star (mainpups.cpp:2130-2135)
  the place     centred on the screen (`Get_Picture_Draw_XY_`,
                mainpups.cpp:110-113): HD centres the map's window in the
                HD window
  the view      the sun, the orbits, each planet where the engine put it
                (its field's place), the colony markers; the planet under
                the pointer bracketed and its information at the view's
                top-left corner
  the bar       one icon per owner with ships at the star, the fleet under
                the pointer described in the same box (`sysfleets`)
  CLOSE         the ESC button at the window's bottom right (+0x107, +0xEC,
                sys.cpp:1772-1778)

TRANSCRIPTION — what a click does (`Check_System_Display_Fields_Defense_
Selection_`, mainpups.cpp:2964-3041; the original reads the POINTER, so HD
injects the click at the field's centre and every answer is the engine's):
  a planet      another player's colony: that colony is the target
                (`colony_idx + 15`), its owner the defender; an unsettled
                planet: E 0x250 (a planet) or E 0x24F; the player's own
                colony: E 0x252
  a fleet       another player's, who has no colony or outpost at the star:
                that player is the target; with one there: E 0x24E; the
                player's own: E 0x253, "You may not attack your own fleet.
                Hit the Close button if you want no combat at the star"
  CLOSE / ESC   -1 (`_mp_fields[6]`, mainpups.cpp:2152-2155): no combat at
                this star (combfind.cpp:957-968)
  then          a chosen target asks `COMBFIND::Human_Confirms_Attack_`;
                refused, the window comes back (combfind.cpp:970-972)

While the window is up the App holds the map: no click, wheel or key
reaches it (`core.overlays`), and its hover is cleared (work order 226 F's
rule for the system window). A right click on a planet is a right click on
its field (the engine's colony information, as before); the window has no
whole-window help (`turnpopupcontent.RIGHT_HELP`).
"""
import logging

import pygame

from core.hestrings import printf
from screens.galaxy_map import boxdraw, boxmodel, sysfleets, sysorbits
from screens.galaxy_map import syswindow

log = logging.getLogger("galaxy_map.combat_target")

E_TITLE = 0x45
#: CLOSE's place off the window's corner (sys.cpp:1772-1778).
CLOSE_AT = (0x107, 0xEC)


def _field(state, index):
    return next((f for f in (getattr(state, "fields", None) or [])
                 if getattr(f, "index", None) == index and index > 0), None)


def title(state, star, estrings):
    """E 0x45 with the chooser's race and the star (`Draw_Defense_Selection_
    Popup_`, mainpups.cpp:2130-2135 — "CyberToller select combat at
    Altair"). The chooser is the local player (`_g_player_n`). Without the
    string file the star's name alone (work order 208 A4)."""
    from core.structs import player as player_struct
    stars = getattr(state, "stars", None) or []
    name = stars[star].name if 0 <= star < len(stars) else "?"
    template = estrings.string(E_TITLE) if estrings is not None else None
    if not template:
        return name
    raws = getattr(state, "player_raw", None) or []
    me = getattr(state, "player_num", 0)
    race = player_struct.parse(raws[me]).race_name \
        if 0 <= me < len(raws) else "?"
    return printf(template, race, name)


def model(state, popup, text, estrings, omniscient=False):
    """(model, None) or (None, reason): the map window's model (`boxmodel.
    system_model`'s keys) from the popup's block — each planet where its
    field says, the fleets of the bar, the close field."""
    sysd = popup.get("system") or {}
    a = popup["args"]
    star = sysd.get("star", -1)
    stars = getattr(state, "stars", None) or []
    if not 0 <= star < len(stars):
        return None, f"star {star} is not in the snapshot"
    close = _field(state, a[2])
    if close is None:
        return None, f"the close field {a[2]} is not in the live list"
    # The planets' places off the orbit centre, as `boxmodel.match_planets`
    # reads the map's: the window's corner is CLOSE's place less its offset.
    ox = close.x - CLOSE_AT[0] + boxmodel.ORBIT_CENTRE[0]
    oy = close.y - CLOSE_AT[1] + boxmodel.ORBIT_CENTRE[1]
    known = {p["planet"]: p for p in boxmodel.star_planets(state, stars[star])}
    planets = []
    for slot in sysd.get("planets", []):
        if slot["planet"] < 0 or slot["field"] <= 0:
            continue                      # no planet, or a belt (no field)
        f, p = _field(state, slot["field"]), known.get(slot["planet"])
        if f is None or p is None:
            return None, (f"planet {slot['planet']}'s field {slot['field']} "
                          f"is not in the live list or not at {stars[star].name}")
        cx, cy = f.x + (f.x_end - f.x) // 2, f.y + (f.y_end - f.y) // 2
        planets.append(dict(p, field=f.index, at=(cx - ox, cy - oy)))
    out = boxmodel.window_texts(state, star, text, omniscient)
    out.update({"star": star, "name": stars[star].name, "close": close.index,
                "title": title(state, star, estrings),
                "planets": sorted(planets, key=lambda q: q["orbit"]),
                "belts": boxmodel.star_belts(state, stars[star]),
                "fleets": sysfleets.entries(sysd.get("ships"),
                                            getattr(state, "fields", None))})
    return out, None


def rects(screen, size):
    """The map's system window rects (boxes.json), centred in the window as
    the original centres its picture; the bar is CLOSE's row left of it."""
    out = {}
    for name in boxdraw.SYSTEM_BOXES:
        ref = screen.box_rect(name)
        if not ref:
            return None
        out[name] = pygame.Rect(*screen.layout.rect(ref))
    panel = out["system_box"]
    dx = size[0] // 2 - panel.centerx
    dy = size[1] // 2 - panel.centery
    out = {n: r.move(dx, dy) for n, r in out.items()}
    view, close = out["system_view"], out["system_close"]
    out["system_fleets"] = pygame.Rect(view.x, close.y,
                                       max(0, close.x - view.x - close.h // 2),
                                       close.h)
    return out


class Drawn:
    """What the window drew this frame: its click areas, in the turn popup
    view's shape (`core.turnpopup.View`)."""

    def __init__(self):
        self.rects, self.right, self.buttons = [], [], []
        self.right_help = None


def render(screen, surface, popup, state, app=None):
    """Draw the window over what `surface` holds; return `Drawn`."""
    from core import hestrings, mouse
    from core.estrings import EStrings
    from core.shipparts import ShipPartNames
    out = Drawn()
    r = rects(screen, surface.get_size())
    if r is None:
        log.info("combat target window: the map has no system window boxes")
        return out
    screen._hover_star = None               # nothing of the map under it
    lang = (getattr(app, "settings", None) or {}).get("language", "en") \
        if app is not None else "en"
    if getattr(screen, "_combat_words", None) is None or \
            screen._combat_words[0] != lang:
        screen._combat_words = (lang, EStrings(lang), ShipPartNames(lang))
    _l, estrings, parts = screen._combat_words
    text = hestrings.for_app(screen.app)
    text = text if text.state == "ok" else None
    m, why = model(state, popup, text, estrings,
                   getattr(screen, "_omniscient", False))
    # UNDER A BOX (the engine's answer to a click, E 0x24E, 0x253 …) the
    # live list is the box's, not the window's: the window is drawn as it
    # last stood for this popup, as the original's stays under its help
    # box, and it takes no click (the box does) — found live, work order 228.
    key = (tuple(popup["args"]), (popup.get("system") or {}).get("star"))
    last = getattr(screen, "_combat_window", None)
    live = m is not None
    if live:
        screen._combat_window = (key, m)
    stale = not live and last is not None and last[0] == key
    if stale:
        m = last[1]
    syswindow.frame(screen, surface, r["system_box"])
    if m is None:
        log.info("combat target window: %s", why)
        m = {"title": title(state, (popup.get("system") or {}).get(
            "star", -1), estrings), "viewable": False, "body": why,
            "close": popup["args"][2], "planets": [], "fleets": [],
            "wormhole": ""}
    syswindow.text(screen, surface, r["system_title"], m["title"],
                   syswindow.font(screen, "system_title", 20),
                   syswindow.TITLE_COLOR)
    view = r["system_view"]
    drawn = syswindow.draw_view(screen, surface, view, m, state)
    s = sysorbits.frame(view)[0]
    fleets = sysfleets.draw_bar(screen, surface, r["system_fleets"],
                                m["fleets"], s)
    pointer = mouse.pos()
    over = next((owner for rect, owner, _f in fleets
                 if rect.collidepoint(pointer)), None)
    if over is not None:
        colour = sysfleets.player_colour_index(state, over)
        syswindow.info_box(screen, surface, view,
                           sysfleets.lines(state, m["star"], over, text,
                                           parts),
                           syswindow.owner_colour(colour))
    else:
        syswindow.planet_info(screen, surface, view, drawn, pointer, state)
    syswindow.text(screen, surface, r["system_text"], m.get("wormhole"),
                   syswindow.font(screen, "system_text", 16),
                   syswindow.TEXT_COLOR, "left")
    close = r["system_close"]
    syswindow.close_button(screen, surface, close, syswindow.close_label(screen))
    if stale:
        return out
    for p, rect in drawn:
        f = _field(state, p["field"])
        out.rects.append((rect, ("click", f) if f is not None else None))
        out.right.append((rect, ("field", f) if f is not None else None))
    for rect, _owner, f in fleets:
        out.rects.append((rect, ("click", f)))
        out.right.append((rect, None))
    cf = _field(state, m["close"])
    close_action = ("click", cf) if cf is not None else None
    out.rects.append((close, close_action))
    out.right.append((close, None))
    out.buttons = [close_action]
    return out
