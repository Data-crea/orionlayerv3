"""The monster guarding a system, with its values — an HD EXTENSION (fundament 64).

**THE ORIGINAL SHOWS NONE OF THIS.** Outside combat MOO2 names the type
— "(Amoeba)" under the planet in this list, the "guarded by" prompts —
and nothing else: the fleet screen's scan never runs for a monster
stack (`Scan_Fltscrn_Big_Icons_` only for the player's own,
flt1.cpp:614), and the monster system popup is unreachable in a running
game. So everything below the type is an extension: stage, size,
structure, armour, shield, weapons, specials.

**WHY IT IS HERE ANYWAY** (Data, 14 September 2026): the values are
fixed per type (SHIP_CONFIG templates, ship_config.cpp:86-139) and have
been public for years. Showing them removes a disadvantage a newcomer
has and a veteran never had. Numbers, not judgements — no rating, no
colour that means "dangerous". A switch in Game Settings' OrionLayer
rows turns it off; it is on by default (`core/usersettings.py`).

WHAT IS READ, and nothing else:
- the guarding ship — `planetrows.monster_ship`, the transcription of
  `HAROLD::Star_Guarded_By_Monster_`; drawn only for owners 9..14;
- its design block, the VERIFIED part of `core/structs/ship.py`;
- hull points from `core/monsterhull.py` (tactical, structure and armour
  as two lines), which a checker holds to initship.cpp;
- names from `core/shipparts.py` (TECHNAME.LBX) and the fleet screen's
  own "Weapons:" / "Specials:" / "None" from HESTRNGS.
The damage fields are not read: monsters are repaired in full every
turn, so the values drawn are the maxima and they are the true ones.

Nothing here sends anything. The boxes are boxes.json's, the words are
layout.json's `monster_values` templates, the values are filled per
frame and never serialized.
"""
import logging
import os

import pygame

from core import monsterhull
from core import zoomtables as zt
from core.structs import ship as ship_struct
from core.usersettings import DEFAULTS
from screens.galaxy_map import ships as galaxy_ships

from . import planetdraw, planetrows, planetwords

log = logging.getLogger("planets")

SWITCH = "monster_values"
SPRITE_BOX = "monster_sprite"
LINE_BOXES = ("monster_type", "monster_stage", "monster_size",
              "monster_structure", "monster_armour", "monster_shield")
LIST_BOXES = ("monster_weapons", "monster_weapon_counts", "monster_specials")
BOXES = (SPRITE_BOX,) + LINE_BOXES + LIST_BOXES


def enabled(app):
    settings = getattr(app, "user_settings", None)
    value = settings.get(SWITCH) if settings is not None else DEFAULTS[SWITCH]
    return value != "off"


def guard(view, star_index):
    """The guarding ship when it is a monster (owners 9..14), else None."""
    ship = planetrows.monster_ship(view, star_index)
    if ship is None or not ship_struct.is_monster(ship.owner):
        return None
    return ship


def values(view, ship, words, parts, cfg):
    """{box name: text} for the line boxes, {box name: [rows]} for the three
    list boxes. Pure: no drawing, no state, so the smoke test can hold every
    value to the table and the design fields."""
    def part(table, index):
        name = parts.name(table, index) if parts is not None else None
        return name if name else cfg.get("unnamed", "#%d") % int(index)

    def number(template, value):
        return (cfg.get(template, "%d") % value if value is not None
                else cfg.get("unknown", "?"))

    def message(key, fallback):
        index = cfg.get(key)
        text = words.hstrings.message(index) if index is not None else None
        return text if text and text != str(index) else fallback

    stage = monsterhull.stage(ship)
    out = {
        "monster_type": planetwords.race_name(view, int(ship.owner), words),
        "monster_stage": cfg.get("stage", {}).get(stage, "") if stage else "",
        "monster_size": part("hulls", ship.size),
        "monster_structure": number("structure", monsterhull.structure(ship)),
        "monster_armour": number("armour", monsterhull.armour(ship)),
        "monster_shield": part("shields", ship.shield_type),
    }
    none = message("none", "None")
    weapons = ship_struct.weapons(ship)
    out["monster_weapons"] = [message("weapons_heading", "Weapons:")] + (
        [part("weapons", w.type) for w in weapons] or [none])
    out["monster_weapon_counts"] = [""] + [
        cfg.get("count", "x%d") % w.count for w in weapons]
    specials = ship_struct.special_bits(ship)
    out["monster_specials"] = [message("specials_heading", "Specials:")] + (
        [part("specials", i) for i in specials] or [none])
    return out


def sprite_path(screen, owner):
    """The panel sprite for the monster's TYPE, through the resource stack.

    **DEVIATION.** The original's own monster picture — the system popup
    no running game reaches — is chosen by STAR INDEX % 5
    (`RUSS::Star_To_Monster_`, MAINPUPS.LBX 15 + that, mainpups.cpp:1082),
    so a star can show a creature that is not the one guarding it. HD
    shows the type that is there, drawn from the galaxy map's own master
    (`tools/make_ship_icons.py`'s panel export) — one source, no second
    set of artwork. A type without a master (the amoeba today) has no
    file and the box stays EMPTY: no stand-in, no silhouette."""
    kind = galaxy_ships.MONSTER_KINDS.get(int(owner))
    if kind is None:
        return None
    return screen.app.res.resolve(os.path.join(
        "screens", "galaxy_map", "assets", "ships", kind,
        zt.MONSTER_PANEL_SPRITE_FILE))


def _load(screen, owner):
    cache = screen._monster_sprites
    if owner not in cache:
        path = sprite_path(screen, owner)
        cache[owner] = pygame.image.load(path).convert_alpha() if path else None
        if path is None:
            log.info("planets: no panel sprite for monster owner %s — the "
                     "sprite box stays empty", owner)
    return cache[owner]


def _draw_sprite(screen, surface, owner):
    """Contained in the box, never scaled up; `zoom` shrinks it further and
    `crop` anchors it (decision 4's two keys, read as a fit, not a cover:
    a creature cut off at the box edge would be a different picture)."""
    rect = planetdraw.window(screen, SPRITE_BOX)
    img = _load(screen, owner)
    if not rect or img is None:
        return
    style = screen.box_style(SPRITE_BOX)
    zoom = max(0.1, min(1.0, float(style.get("zoom", 1.0))))
    ax, ay = style.get("crop", [0.5, 0.5])
    f = min(1.0, rect.width / img.get_width(),
            rect.height / img.get_height()) * zoom
    size = (max(1, int(img.get_width() * f)), max(1, int(img.get_height() * f)))
    key = (owner, size)
    cached = screen._monster_scaled.get(key)
    if cached is None:
        cached = pygame.transform.smoothscale(img, size)
        screen._monster_scaled = {key: cached}
    surface.blit(cached, (rect.x + int((rect.width - size[0]) * ax),
                          rect.y + int((rect.height - size[1]) * ay)))


def _line(screen, surface, name, text, colour, align="left", rect=None):
    rect = rect or planetdraw.window(screen, name)
    if not rect or not text:
        return
    surf = planetdraw._text(screen.style, text, screen.layout.font_size(
        planetdraw._font(screen, name, 20)), colour, rect.width)
    x = rect.right - surf.get_width() if align == "right" else rect.x
    surface.blit(surf, (x, rect.y + (rect.height - surf.get_height()) // 2))


def _rows(screen, surface, name, rows, count, align="left"):
    rect = planetdraw.window(screen, name)
    if not rect or count <= 0:
        return
    for i, text in enumerate(rows[:count]):
        band = pygame.Rect(rect.x, rect.y + rect.height * i // count,
                           rect.width, rect.height // count)
        colour = planetdraw.HEADING_TEXT if i == 0 else planetdraw.CONTROL_TEXT
        _line(screen, surface, name, text, colour, align, band)


def render(screen, surface, row):
    """Draw the panel for the scanned row. True when something was drawn."""
    view = screen._view
    if row is None or view is None or not enabled(screen.app):
        return False
    ship = guard(view, row["star"])
    if ship is None:
        return False
    cfg = screen._data.get(SWITCH, {})
    vals = values(view, ship, screen._words, screen._parts, cfg)
    _draw_sprite(screen, surface, int(ship.owner))
    for name in LINE_BOXES:
        colour = (planetdraw.HEADING_TEXT if name == "monster_type"
                  else planetdraw.CONTROL_TEXT)
        _line(screen, surface, name, vals[name], colour)
    weapon_rows = int(cfg.get("weapon_rows", 6))
    _rows(screen, surface, "monster_weapons", vals["monster_weapons"],
          weapon_rows)
    _rows(screen, surface, "monster_weapon_counts",
          vals["monster_weapon_counts"], weapon_rows, align="right")
    _rows(screen, surface, "monster_specials", vals["monster_specials"],
          int(cfg.get("special_rows", 9)))
    return True
