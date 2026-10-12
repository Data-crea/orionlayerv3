"""The fleet box's order buttons — work order 229 C.

THE ORIGINAL (fleetpop.cpp, mainscr.cpp; read for this order):

  ALL        added while the box shows the player's own, orderable stack
             (fleetpop.cpp:174-186); selects every ship, or none when all
             are chosen (mainscr.cpp:3411-3419).
  Outpost    offered when the stack is the player's, at a star the player
             may colonise (`colonize_player`), holds an outpost ship, and a
             planet there has no colony and no outpost
             (`Set_Build_Outpost_Button_Flag_`, fleetpop.cpp:1478-1533;
             `Can_Build_Outpost_` :1707-1721) -> screen 31, the planet
             choice (mainscr.cpp:3459-3463; mainscr2.cpp:322-398).
  Colonize   the same with a colony ship and a planet (not a gas giant or
             a belt) with no colony or only an outpost
             (`Set_Colonize_Button_Flag_` :1643-1705, `Planet_Is_Colonizable_`
             :1723-1737) -> screen 30, the planet choice, then the landing
             or the star's new name (mainscr.cpp:3438-3444;
             mainscr2.cpp:400-485).
  Engage     a combat ship of the player's at a star where the player's
             combat ships ignore enemies (`Set_Engage_Enemy_Forces_Flag_`
             :1739-1790) -> clears that bit; nothing else
             (mainscr.cpp:3466-3471).
  Transport  a troop transport at a star with a colony of the player's
             (`Set_Transport_Troops_Flag_` :1535-1596) -> screen 34, the
             planet choice, the troops unloaded onto the colony
             (mainscr2.cpp:614-669); with no transport selected the box
             "no transport ships selected" (E3; mainscr.cpp:3446-3457).
  Attack     a combat ship and the Dimensional Portal at the star
             (`Set_Attack_Antares_Button_Flag_` :1598-1641) -> a confirm
             box, then the ships sent to Antares (mainscr.cpp:3474-3500).

A button the flag does not offer is not ADDED (no field, not drawn —
`Add_Added_Buttons_`, :444-510); the original has no disabled state. The
offered ones stack under CLOSE in that order, the box growing by one
button each (`Set_Added_Button_Stuff_` :813-856, drawn :1193-1255).

HD: which button is offered, and its field, come from open fix 86's FBTN
(`core/fleetbuttons.py`); a button is drawn only while its field is in the
live list and FBTN names the stack the box shows (P602). A click sends that
field (decision 20); what follows is the engine's, and HD draws it where it
can: the planet choice is TPOP's popup (open fix 49), the boxes are HD's
message box. DEVIATION `order_buttons`: the original's buttons are
pictures with their words in them (BUFFER0.LBX); HD draws its small button
with the word from `layout.json` (decision 15), and ALL in CLOSE's row
rather than beside the title — the box's layout is HD's (`box_layout`).
"""
import pygame

from core import fleetbuttons
from core.hud import blocks as hud
from core.hud import glyphs

#: The order the original stacks them under CLOSE (Add_Added_Buttons_).
ORDERS = ("outpost", "colonize", "engage", "transport", "attack")
HELP = dict(fleetbuttons.BUTTONS)
#: Space between two stacked buttons, a fraction of a button's height.
GAP = 0.125


def _live(state):
    return {getattr(f, "index", None) for f in (getattr(state, "fields", None)
                                                  or [])}


def offered(state, model):
    """{"all": field or None, "orders": [(name, field, help id)]} for the
    fleet box HD draws — empty unless FBTN describes the stack it shows."""
    out = {"all": None, "orders": []}
    fb = getattr(state, "fleet_buttons", None)
    fsel = getattr(state, "fleet_selection", None) or {}
    if not fb or fb["stack"] != fsel.get("stack", fb["stack"]):
        return out
    live = _live(state)
    if fb["all"]["offered"] and fb["all"]["field"] in live:
        out["all"] = fb["all"]["field"]
    for name in ORDERS:
        b = fb[name]
        if b["offered"] and b["field"] in live:
            out["orders"].append((name, b["field"], HELP[name]))
    return out


def place(rects, names, orders, area):
    """`rects` with the order buttons' rects added (`order_<name>`) under the
    close button (`names[-1]`), and the box (`names[0]`) grown to hold them.
    When the grown box would leave the map's area, everything moves up."""
    close = rects[names[-1]]
    step = close.h + max(1, int(close.h * GAP))
    out = dict(rects)
    for i, (name, _field, _help) in enumerate(orders):
        out[f"order_{name}"] = close.move(0, (i + 1) * step)
    if orders:
        last = out[f"order_{orders[-1][0]}"]
        panel = rects[names[0]]
        out[names[0]] = pygame.Rect(panel.x, panel.y, panel.w,
                                    last.bottom + (panel.bottom - close.bottom)
                                    - panel.y)
        over = out[names[0]].bottom - area.bottom
        if over > 0:
            out = {k: r.move(0, -over) for k, r in out.items()}
    return out


def all_rect(rects, names):
    """ALL's place: CLOSE's row, between the box's left edge and CLOSE."""
    close, panel = rects[names[-1]], rects[names[0]]
    pad = max(2, close.h // 4)
    w = min(close.w, close.x - panel.x - 2 * pad)
    return pygame.Rect(close.x - pad - w, close.y, w, close.h)


def words(screen):
    return (screen._data.get("movable_boxes") or {})


def draw(screen, surface, rects, names, offer, hits, helps):
    """The offered buttons, each a hit sending its field. Their rects by
    name stay on the screen for this frame (`_order_rects`)."""
    label = words(screen)
    scale = screen.layout.scale
    drawn = screen._order_rects = {}
    if offer["all"] is not None:
        rect = drawn["all"] = all_rect(rects, names)
        hud.small_button(surface, rect, scale, "normal", label.get("all", ""),
                         style_renderer=screen.style,
                         icon=glyphs.for_button("galaxy_map", "all"))
        hits.append((rect, offer["all"]))
    for name, field, help_id in offer["orders"]:
        rect = drawn[name] = rects[f"order_{name}"]
        hud.small_button(surface, rect, scale, "normal", label.get(name, ""),
                         style_renderer=screen.style,
                         icon=glyphs.for_button("galaxy_map", name))
        hits.append((rect, field))
        helps.append((rect, help_id))
