"""The unit or missile under the pointer, in the systems window — work order
259 (258 P1, Data: "build it as in the original").

TRANSCRIPTION `target_box`: while the pointer is over a unit or a missile,
the original's systems box at x 400 shows THAT, and the systems again when
the pointer leaves (cmbtdrw1.cpp:600-790; orion2re v2 the same at
cmbtdrw1.cpp:640-830):

  when    only in the player's own orders (the computer's turn shows the
          clock pointer, combat1.cpp:1731-1735) and only while the WEAPONS
          tab is shown — under SPECIALS the box keeps the systems
          (`_ship_status_display`, cmbtdrw1.cpp:708-709)
  missile first: a missile's hidden field, 8 x 8 px up and left of its
          point, every missile on the map, the player's too (combat1.cpp
          :1658-1689, `Add_Missile_Fields_`; cmbtdrw1.cpp:609-627)
  unit    with the pointer picture 1 or 12 (cmbtdrw1.cpp:722): another own
          unit (1), an enemy (12, or 1 in stasis); never the acting unit
          (picture 2), nor in SCAN (13/14) or BOARD mode (2/3)
          (`Assign_Mouse_Images_`, combat1.cpp:1730-1834); a destroyed unit
          shows the systems (:745-750)

What it draws:

  unit    the unit's name, centred and squeezed into the box's 89 px
          (font 2, `Squeeze_Print_Centered_(445, 362, …)`), and its status
          box as the acting unit's — `Draw_Ship_Status_(400, 376)`, the
          grey bars, the crew stars (cmbtdrw1.cpp:729-737), HD's
          `cbstatus`; the planet keeps HD's rings (OMISSION
          `status_planet`, as the acting planet's box)
  missile the weapon's name (font 1, `Squeeze_Print_Centered_(445, 365,
          …)`, :714-718) over `Draw_Missile_Status_` (cmbtmis.cpp:1383
          -1437): the star picture (COMBAT.LBX 45), the missile at the
          centre, "Target:" (KENTEXT 52) run straight into the target's
          name — the missile's target, an anti-missile rocket's the
          missile's weapon — at the top, and the quantity with " Missile"
          / " Missiles" (53 / 107), " Torpedo" / " Torpedoes" (54 / 108) or
          the fighter's name, singular for one, at the bottom; the game's
          words in its language (`core.kentext`)

DEVIATION `target_missile_picture`: the missile in the box is the one
picture HD draws on the map for a group (`cbdraw.draw_ordnance`), not the
original's group of pictures (`Draw_Missile_`, cmbtmis.cpp:1130-1180) — the
quantity is in the line under it, as there.
"""
import pygame

from core.hud import text as hudtext
from . import cbdraw, cbstatus

#: The original's box at x 400: the name row (401..489, 362..374) and the
#: status box under it (401..488, 379..467), cmbtdrw1.cpp:714-750.
NAME_W = 89
MISSILE_BOX = pygame.Rect(401, 379, 88, 89)
#: `Draw_Missile_Status_`'s rows, from the box's top (cmbtmis.cpp:1401, 1436)
TARGET_ROW, QUANTITY_ROW = 2, 81
#: TECHDATA weapon types (`cbpanel.WEAPON_TYPE`): missile, fighter
MISSILE, FIGHTER = 1, 4
#: The hidden field over a missile (combat1.cpp:1670-1677): x - 16 .. x - 8
FIELD_FROM, FIELD_TO = 16, 8


def missile_under(ordnance, cam, x, y):
    """The missile whose original hidden field is under window point
    (x, y) — any owner's (`Add_Missile_Fields_`) — or None."""
    for m in (ordnance or {}).get("missiles", []):
        x0, y0 = cam.to_window(m["x"] - FIELD_FROM, m["y"] - FIELD_FROM)
        x1, y1 = cam.to_window(m["x"] - FIELD_TO, m["y"] - FIELD_TO)
        if x0 <= x <= x1 and y0 <= y <= y1:
            return m
    return None


def squeezed(style, text, size, width, colour):
    """`text` at `size`, smaller until it fits `width` — the original
    squeezes a name into the box's 89 px (`Squeeze_Print_Centered_`)."""
    img = style.render_text(text, size, colour)
    while img.get_width() > width and size > 8:
        size = max(8, int(size * width / img.get_width()))
        img = style.render_text(text, size, colour)
    return img


def missile_lines(m, combat, missiles, names, ken, weapon_type):
    """(the top line, the bottom line) of `Draw_Missile_Status_`
    (cmbtmis.cpp:1395-1436)."""
    def word(what, fallback):
        return cbstatus.word(ken, what, fallback)
    units = combat["units"]
    t = int(m["target_unit_idx"])
    if int(m.get("is_anti_missile_rocket", 0)):
        aimed = next((o for o in missiles if int(o["index"]) == t), None)
        target = names.name("weapons", int(aimed["type"])) if aimed else ""
    else:
        target = units[t]["name"] if 0 <= t < len(units) else ""
    top = word("target", "Target:") + (target or "")
    kind, q = int(m["type"]), int(m["quantity"])
    wtype = weapon_type(kind)
    if wtype == MISSILE:
        tail = word("missile", " Missile") if q == 1 else \
            word("missiles", " Missiles")
    elif wtype == FIGHTER:
        tail = " " + ((names.name("weapons", kind) if q == 1 else
                       names.name("weapon_plurals", kind)) or "")
    else:
        tail = word("torpedo", " Torpedo") if q == 1 else \
            word("torpedoes", " Torpedoes")
    return top, f"{q}{tail}"


def draw_unit(surface, title, room, status, unit, status_args, picture,
              style, scale, size, ken, rings):
    """The hovered unit: its name over its status box. `rings` draws HD's
    rings for the planet (no `status_args`)."""
    img = squeezed(style, unit["name"], size, title.w,
                   hudtext.colour("value")[:3])
    hudtext.blit(surface, img, title, align="center")
    if status_args is None or not cbstatus.draw(
            surface, room, status, *status_args, picture, style, scale,
            ken=ken):
        rings(surface, room, unit, picture)


def draw_missile(surface, title, room, m, combat, missiles, art, names, ken,
                 style, small, weapon_type, cache):
    """The hovered missile: its weapon's name over `Draw_Missile_Status_`."""
    name = names.name("weapons", int(m["type"])) or ""
    hudtext.blit(surface, squeezed(style, name, small, title.w,
                                   hudtext.colour("value")[:3]),
                 title, align="center")
    k = min(room.w / MISSILE_BOX.w, room.h / MISSILE_BOX.h)
    box = pygame.Rect(0, 0, round(MISSILE_BOX.w * k),
                      round(MISSILE_BOX.h * k))
    box.center = room.center
    stars = cbstatus.stars_tile(art, k)
    if stars is not None:
        cbstatus.tile(surface, box, stars)
    kind = int(m["type"])
    facing = int(m["facing_dir"]) & 15
    pic = art.surface("cmbtfgtr", cbdraw.FIGHTER_TYPE[kind] * 16 + facing,
                      0) if kind in cbdraw.FIGHTER_TYPE else \
        art.surface("cmbtmisl", cbdraw.MISSILE_TYPE[kind] * 16 + facing, 0) \
        if kind in cbdraw.MISSILE_TYPE else None
    if pic is not None:
        img = cbdraw.scaled(pic, k, cache)
        surface.blit(img, img.get_rect(center=(box.x + round(44 * k),
                                               box.y + round(44 * k))))
    top, bottom = missile_lines(m, combat, missiles, names, ken,
                                weapon_type)
    text = max(8, int(small * 0.9))
    for line, row in ((top, TARGET_ROW), (bottom, QUANTITY_ROW)):
        img = squeezed(style, line, text, box.w, hudtext.colour("value")[:3])
        surface.blit(img, img.get_rect(midtop=(box.x + round(43 * k),
                                               box.y + round(row * k))))
