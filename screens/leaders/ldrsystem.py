"""The Leaders screen's colony view as a star system (Data, 16 Oct 2026).

TRANSCRIPTION `system_orbits`: the original's colony view is the system
window of `_officer_star_displayed` drawn off screen
(`Wrapper_For_Offscrn_System_Popup`, officer.cpp:2050-2058): the star, one
ellipse per orbit that holds something, each planet at
`GEO::Get_Orbit_Display_X_Y` (geo.cpp:244-283), still for the whole turn.
HD draws it with the galaxy map's own orbits (`sysorbits`): the rings, the
belts and the planets back to front, the places from the stardate
(`sysorbits.orbit_place` — this screen has no engine field to read them
off, as the map's window does), the original's 322 x 183 view fitted into
the box.

HD EXTENSION `view_picture`: the star and the space behind it are Data's
picture, the Leaders picture place "view" (`ldrpics`); the rings are
centred on its painted star (`ldrpics.sun_centre`), so the picture's star
needs no exact place; the system scaled to stand between the star's name
and the box's foot (`fit`, work order 285). DEVIATION `ring_colour`: the rings one thin line in
the cyan of Data's mockup (`VIEW_RING`), not the original's dark blues.
INVENTION `colony_brackets`: a planet with a colony wears the mockup's
corner brackets (`BRACKET`). The planets are Data's painted ones where the
mod folder has them (`colonyplanets.painted_planets`), else the discs;
a gas giant is the map's painted one (`gasgiant`).

Without the picture the colony view stays the row of discs (`ldrright`,
OMISSION `system_pictures`); the ship view keeps its glass panel.
"""
import pygame

from core.structs import planet as planet_struct
from core.structs import star as star_struct
from screens.galaxy_map import sysorbits

from . import ldrdraw
from . import ldrgeom as geom
from . import ldrpics

PLACE = "view"
#: The rings' core in the mockup's cyan; no darker sides.
VIEW_RING = ((80, 190, 225), None)
#: The rings' opacity on the Leaders view (Data, work order 286: a little
#: more discreet on the held-back picture, `ldrpics.mute`); the galaxy
#: map's system window keeps VIEW_RING opaque.
VIEW_RING_ALPHA = 0.60
#: The colony brackets: the mockup's gold, each arm a quarter of the
#: planet's side, `BRACKET_GAP` of the side clear of it.
BRACKET = (232, 196, 64)
BRACKET_ARM = 0.25
BRACKET_GAP = 0.10
#: The room kept clear under the star's name and over the box's foot, of
#: the name's font size.
NAME_GAP = 0.4
#: `PLANET_TYPE` (orion2_consts.h:400-403).
ASTEROID, GAS_GIANT = 1, 2
#: The outermost orbit a planet can stand on (five per star, 0-4).
OUTER_ORBIT = 4


def reach():
    """How far the system reaches up and down from its centre, per unit of
    scale: the outermost orbit's half height and the largest planet's half
    side on it."""
    return (sysorbits.radii(OUTER_ORBIT, 1.0)[1]
            + sysorbits.PLANET_DIM[sysorbits.HUGE] / 2.0)


def fit(s, cy, top, bottom):
    """THE ORBITS BETWEEN TWO LINES (work order 285, Data: they ran into the
    star's name): the scale, at most `s`, at which the outermost orbit with
    the largest planet on it stays between `top` and `bottom` round a centre
    at `cy` — whatever the star's own orbits, so the system's size does not
    change from star to star."""
    r = reach()
    return max(0.1, min(s, (cy - top) / r, (bottom - cy) / r))


def shows(screen):
    """True while the colony view is on and the picture is there."""
    view = getattr(screen, "_view", None)
    return view is not None and getattr(view, "view", None) == \
        geom.VIEW_COLONY and ldrpics.source(PLACE) is not None


def draw_box(surface, screen, art):
    """The view box with Data's picture, the star's name kept readable over
    it; False where it is not shown (the caller draws the glass panel)."""
    if not shows(screen):
        return False
    layout = screen.layout
    r = ldrdraw.rect(layout, geom.VIEW_BOX)
    from core.hud import fill
    size = ldrdraw.font_px(layout, "strip")
    band = pygame.Rect(r.x, r.y, r.w, int(size * 2.2))
    ceil = ldrpics.ceiling(ldrdraw.text_colour(art, "normal"),
                           fill.member("panel"))
    return ldrpics.draw_box(surface, r, layout.scale, PLACE, [(band, ceil)],
                            muted=True)


def frame_at(screen):
    """(scale, centre x, centre y): the original's view fitted into the
    box, the rings' centre on the picture's star where it has one, the
    whole system under the star's name and above the box's foot (`fit`)."""
    r = ldrdraw.rect(screen.layout, geom.VIEW_BOX)
    s, cx, cy = sysorbits.frame(r)
    sun = ldrpics.sun_centre(PLACE, r.size)
    if sun is not None:
        cx, cy = r.x + sun[0], r.y + sun[1]
    size = ldrdraw.font_px(screen.layout, "strip")
    gap = int(size * NAME_GAP)
    top = r.y + size // 2 + int(size * 1.2) + gap      # the name's foot
    return fit(s, cy, top, r.bottom - gap), cx, cy


def model(game_state, star):
    """The star's planets and belts as `sysorbits.draw` takes them, each
    planet at the original's place for this stardate."""
    stars = getattr(game_state, "stars", None) or []
    raws = getattr(game_state, "planets_raw", None) or []
    stardate = int(getattr(game_state, "stardate", 0) or 0)
    planets, belts = [], []
    for index in star_struct.planet_indices(stars[star]):
        if not 0 <= index < len(raws):
            continue
        p = planet_struct.parse(raws[index])
        if int(p.planet_type) == ASTEROID:
            belts.append(int(p.orbit))
            continue
        planets.append({"planet": index, "orbit": int(p.orbit),
                        "size": int(p.size), "climate": int(p.climate),
                        "type": int(p.planet_type),
                        "colony": int(p.colony_index),
                        "at": sysorbits.orbit_place(star, int(p.orbit),
                                                    stardate)})
    return {"star": star, "planets": planets, "belts": belts}


def ring_colours():
    """VIEW_RING with its core at VIEW_RING_ALPHA."""
    core, side = VIEW_RING
    return (tuple(core) + (int(round(255 * VIEW_RING_ALPHA)),), side)


def _brackets(surface, rect, width):
    gap = max(2, int(rect.w * BRACKET_GAP))
    r = rect.inflate(2 * gap, 2 * gap)
    arm = max(4, int(rect.w * BRACKET_ARM))
    for (x, y), (dx, dy) in (((r.left, r.top), (1, 1)),
                             ((r.right, r.top), (-1, 1)),
                             ((r.left, r.bottom), (1, -1)),
                             ((r.right, r.bottom), (-1, -1))):
        pygame.draw.line(surface, BRACKET, (x, y), (x + dx * arm, y), width)
        pygame.draw.line(surface, BRACKET, (x, y), (x, y + dy * arm), width)


def draw(surface, screen, game_state, art, star):
    """The system over the picture, then the star's name on top."""
    from screens.colony_summary import colonyplanets
    from screens.galaxy_map import gasgiant
    stars = getattr(game_state, "stars", None) or []
    if not 0 <= star < len(stars):
        return []
    layout = screen.layout
    r = ldrdraw.rect(layout, geom.VIEW_BOX)
    width = max(2, int(round(layout.scale * 2)))

    def planet(p, centre, side):
        if p["type"] == GAS_GIANT:
            pic = gasgiant.picture(side)
        else:
            discs = colonyplanets.set_for(screen, side, p["size"])
            pic = discs.get(p["climate"]) if discs is not None else None
        at = pygame.Rect(0, 0, side, side)
        at.center = centre
        if pic is not None:
            surface.blit(pic, pic.get_rect(center=centre))
        if p["colony"] >= 0:
            _brackets(surface, at, width)
        return at

    hits = sysorbits.draw(surface, r, model(game_state, star), planet,
                          at=frame_at(screen), colours=ring_colours())
    size = ldrdraw.font_px(layout, "strip")
    ldrdraw.blit_text(surface, screen.style, stars[star].name, r.centerx,
                   r.y + size // 2, r.w - 8, int(size * 1.2),
                   ldrdraw.text_colour(art, "normal"), "center")
    return hits
