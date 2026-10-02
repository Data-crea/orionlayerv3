"""The single-colony screen's right clicks — work order 200 B.

The original answers a right click

  over a help rectangle       the help entry (erichelp.cpp:90, `help.json`)
  on a building of the scene  its description: `Get_App_Description_String_`
                              and `Text_Box_` (colony.cpp:1988-2010; not for
                              the Artemis net, the portal, a star base,
                              fortress or battlestation)
  on a satellite              the same for an orbital building
                              (colony.cpp:1608-1613)

HD draws the buildings as a list (DEVIATION `building_list`, `coldraw`).
TRANSCRIPTION `building_info`: a right click on a row of that list goes to
that building's own field — the cell open fix 36's grid puts it in
(`colgeom.building_field`, the cells check 090p holds against the live
fields), or its satellite slot's field (`Add_Satellite_Fields_`,
colony.cpp:1731-1758) — and the game's `Text_Box_` comes back as HD's
message box (`core/rightinfo`).
"""
from core import rightinfo
from screens.leaders import ldrdraw as nd

from . import colgeom as geom

#: The list `coldraw._buildings` draws: rows 10 native px from y 164.
LIST_X, LIST_Y0, LIST_STEP = (8, 150), 163, 10
#: `Add_Satellite_Fields_`: slot i at x 295 + (-1)^i * i * 50, y 162.
SAT_Y = 162


def sat_x(i):
    return 295 + (1 if i % 2 == 0 else -1) * i * 50


def row_at(screen, ids, x, y):
    """The building id of the list row under a window point, or None."""
    for i, bid in enumerate(ids):
        top = LIST_Y0 + LIST_STEP * i
        if nd.rect(screen.layout, (LIST_X[0], top, LIST_X[1],
                                   top + LIST_STEP - 1)).collidepoint(x, y):
            return bid
    return None


def field_for(placement, live, bid):
    """The live field the original reads `bid` off, or None."""
    if placement is None:
        return None
    hidden = [f for f in live if f.field_type == geom.TYPE_HIDDEN]
    for i, sid in enumerate(placement["satellites"]):
        if sid == bid:
            return next((f for f in hidden
                         if (f.x, f.y) == (sat_x(i), SAT_Y)), None)
    for r, row in enumerate(placement["grid"]):
        for c, cell in enumerate(row):
            if cell == bid:
                rect = geom.building_field(r, c)
                return next((f for f in hidden
                             if (f.x, f.y, f.x_end, f.y_end) == rect), None)
    return None


def answer(screen, x, y):
    """True when a right click on a building row went out."""
    view = screen._view
    if view is None or not view.draws:
        return False
    bid = row_at(screen, view.buildings(), x, y)
    if bid is None:
        return False
    state = screen._state
    f = field_for(getattr(state, "colony_placement", None), screen._live(),
                  bid)
    return rightinfo.send(screen.app, f, f"building {bid}",
                          rightinfo.opener(screen))
