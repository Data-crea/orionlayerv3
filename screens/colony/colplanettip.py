"""The planet description over the system display.

HD EXTENSION `planet_hover` (Data, 25 October 2026).

The original prints the short summary beside each planet and opens the
long description in a box only on a CLICK on that text (`colony.cpp:
1798-1836`, `Build_Generic_Planet_Or_Colony_Description_String_Formatted_`,
mainpups.cpp:313). HD shows the same description while the pointer rests
on the orbit's row, in the HUD's popup block.

TRANSCRIPTION of the lines, by the original's ESTRINGS ids: the title
(0x52, or 0x49 for a settled planet, 0x56 + 0x133 for a gas giant or an
asteroid field), size and climate (0x4D), mineral class (0x6F), gravity
(0x53), the settled planet's population (0x71) or an empty one's maximum
(0x6D), the special (0x50). The words are the full tables the Planets
screen uses (`planetwords`), as `MOX::planet_size_string` and its
neighbours are.

OMISSION `planet_hover_potential`: the original's food, industry and
research per worker, the maintenance and worker penalties of an empty
planet (`COLCALC::Compute_Potential_Colony_Info_`) and a settled planet's
base rates and morale are not shown yet: the first needs the owner's
traits and researched applications run through four tables, the others'
wire fields are not verified (`core/structs/colony.py`).
"""
import pygame

from core import mouse as mouse_input
from core import nativedraw as nd
from core.hud import blocks as hud
from core.hud import text as hudtext
from core.structs import colony as colony_struct
from core.structs import player as player_struct
from core import colonyfacts
from screens.planets import planetwords

from . import coldraw
from . import colgeom as geom

E_TITLE, E_TITLE_OWNED, E_NAME, E_UNINHABITABLE = 0x52, 0x49, 0x56, 0x133
E_SIZE_CLIMATE, E_MINERAL, E_GRAVITY = 0x4D, 0x6F, 0x53
E_MAX_POP, E_POPULATION, E_SPECIAL = 0x6D, 0x71, 0x50
PLANET_TYPE_ASTEROID, PLANET_TYPE_GAS_GIANT = 1, 2
NO_SPECIAL = 0

TIP_GROW = 1.3          # over the summary's own text size, for reading
PAD = 5
GAP = 4


def row_at(screen, x, y):
    """The orbit row (0..4) whose native rectangle holds window point
    (x, y), or -1."""
    for i in range(5):
        if nd.rect(screen.layout, geom.sys_row_rect(i)).collidepoint(x, y):
            return i
    return -1


def _fmt(template, *values):
    if template is None:
        return None
    try:
        return template.replace("\x1a", "") % values
    except (TypeError, ValueError):
        return None


def lines(view, state, words, i):
    """The description of orbit `i` as a list of text lines, [] where the
    row is empty or the wire cannot name the planet."""
    planet = view.system[i] if 0 <= i < len(view.system) else None
    index = view.system_ids[i] if 0 <= i < len(view.system_ids) else -1
    if planet is None or view.star is None or index < 0:
        return []
    name = colonyfacts.star_planet_name(view.star, index)
    e = words.e
    out = []
    if int(planet.planet_type) in (PLANET_TYPE_ASTEROID,
                                   PLANET_TYPE_GAS_GIANT):
        return _split(_fmt(e(E_NAME), name), _fmt(e(E_UNINHABITABLE)))
    colonies = getattr(state, "colonies_raw", None) or []
    players = getattr(state, "player_raw", None) or []
    ci = int(planet.colony_index)
    colony = colony_struct.parse(colonies[ci]) \
        if 0 <= ci < len(colonies) else None
    owner = (player_struct.parse(players[int(colony.owner)])
             if colony is not None and 0 <= int(colony.owner) < len(players)
             else None)
    if colony is None:
        out.append(_fmt(e(E_TITLE), "", name))
        climate = int(planet.climate)
    else:
        out.append(_fmt(e(E_TITLE_OWNED), "", name,
                        owner.race_name if owner is not None else ""))
        climate = int(colony.climate)
    out.append(_fmt(e(E_SIZE_CLIMATE), "",
                    e(planetwords._pick(planetwords.SIZE_WORDS,
                                        int(planet.size))) or "",
                    e(planetwords._pick(planetwords.CLIMATE_WORDS,
                                        climate)) or ""))
    out.append(_fmt(e(E_MINERAL), "",
                    e(planetwords._pick(planetwords.MINERAL_WORDS,
                                        int(planet.mineral_class))) or ""))
    out.append(_fmt(e(E_GRAVITY), "",
                    e(planetwords._pick(planetwords.GRAVITY_WORDS,
                                        int(planet.gravity_class))) or ""))
    me = int(getattr(state, "player_num", 0) or 0)
    who = owner if owner is not None else (
        player_struct.parse(players[me]) if 0 <= me < len(players) else None)
    traits = player_struct.traits(who) if who is not None else None
    stand_in = colony if colony is not None else _bare(planet)
    maximum = colonyfacts.max_population(
        stand_in, planet, traits, colonyfacts.city_planning(who))
    if colony is None:
        out.append(_fmt(e(E_MAX_POP), "", " ", maximum))
    else:
        out.append(_fmt(e(E_POPULATION), "", "", int(colony.n_pops),
                        maximum))
    special = int(planet.planet_special)
    if special != NO_SPECIAL:
        out.append(_fmt(e(E_SPECIAL), "", e(planetwords._pick(
            planetwords.SPECIAL_WORDS, special)) or ""))
    return _split(*out)


def _bare(planet):
    from screens.galaxy_map import sysinfo
    return sysinfo._bare_colony(planet)


def _split(*parts):
    """The strings carry their own newlines; blank lines are the
    original's paragraph gaps and are dropped."""
    out = []
    for part in parts:
        for line in (part or "").split("\n"):
            if line.strip():
                out.append(line.strip())
    return out


def draw(surface, screen, view, state, words):
    """The box beside the hovered row, or nothing. Not while colonists
    are in hand: the pointer then carries the drop."""
    if screen.carry.carrying:
        return
    x, y = mouse_input.pos()
    i = row_at(screen, x, y)
    if i < 0:
        return
    text = lines(view, state, words, i)
    if not text:
        return
    scale = nd.native_scale(screen.layout)
    size = max(nd.MIN_FONT, int(round(coldraw.font(screen.layout, "line")
                                      * TIP_GROW)))
    pad, gap = int(PAD * scale), int(GAP * scale)
    surfs = [screen.style.render_text(t, size, hudtext.colour(
        "value" if n else "label")) for n, t in enumerate(text)]
    width = max(s.get_width() for s in surfs) + 2 * pad
    line_h = max(s.get_height() for s in surfs)
    height = line_h * len(surfs) + 2 * pad
    row = nd.rect(screen.layout, geom.sys_row_rect(i))
    sw, sh = surface.get_size()
    bx = min(row.right + gap, sw - width - gap)
    by = max(gap, min(row.top, sh - height - gap))
    box = pygame.Rect(bx, by, width, height)
    hud.popup(surface, box, screen.layout.scale)
    ty = by + pad
    for s in surfs:
        surface.blit(s, (bx + pad, ty))
        ty += line_h
