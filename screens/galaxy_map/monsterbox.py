"""The space monster's window over the galaxy map — an HD EXTENSION
(fundament 64, moved from the Planets screen by Data's mockup).

**THE ORIGINAL SHOWS NONE OF THIS.** Outside combat MOO2 names a monster
and nothing else: the fleet screen's scan never runs for a monster stack
(`Scan_Fltscrn_Big_Icons_` only for the player's own, flt1.cpp:614), and
the monster system popup is unreachable in a running game. A click on a
monster's icon opens the engine's fleet box (title: the ship's own name in
capitals, fleetpop.cpp:615-627); HD draws THIS window in its place, with
the same CLOSE field, and the values below are the extension: class,
structure, armour, shield, weapons, specials.

**WHY IT IS HERE ANYWAY** (Data, 14 September 2026): the values are fixed
per type (SHIP_CONFIG templates, ship_config.cpp:86-139) and have been
public for years. Showing them removes a disadvantage a newcomer has and a
veteran never had. Numbers, not judgements — no rating, no colour that
means "dangerous". A switch in Game Settings' OrionLayer rows turns it off
(the engine's fleet box is drawn then); it is on by default
(`core/usersettings.py`).

WHAT IS READ, and nothing else:
- the stack's head ship, `model["records"][0]`, owners 9..14 only;
- its design block, the VERIFIED part of `core/structs/ship.py`;
- hull points from `core/monsterhull.py` (tactical, structure and armour
  as two lines), which a checker holds to initship.cpp;
- names from `core/shipparts.py` (TECHNAME.LBX) and the fleet screen's own
  "Weapons:" / "Specials:" / "None" from HESTRNGS.
The damage fields are not read: monsters are repaired in full every turn,
so the values drawn are the maxima and they are the true ones.

HD EXTENSION `monster_stars`: the picture box shows the system window's star
field behind the creature (`sysstars`), Data's wish after the first look.

DEVIATION `monster_description`: the original has no text per monster. The
Guardian's sentence is Data's mockup text (`layout.json` `monster_window`);
every other type shows the original's own description of the space-monster
special (MAINTEXT, `sysextras.monster_words`).

Nothing here sends anything: CLOSE is the fleet box's own field, which
`boxdraw` sends. The boxes are boxes.json's, the words layout.json's.
"""
import logging
import os

import pygame

from core import hestrings, monsterhull, textfit
from core import zoomtables as zt
from core.hud import blocks as hud
from core.hud import text as hudtext
from core.structs import ship as ship_struct
from core.usersettings import DEFAULTS
from screens.galaxy_map import ships as galaxy_ships
from screens.galaxy_map import sysextras, sysfleets, sysstars, syswindow

log = logging.getLogger("galaxy_map.monster")

SWITCH = "monster_values"
BOXES = ("monster_box", "monster_title", "monster_close", "monster_picture",
         "monster_class", "monster_hitpoints", "monster_weapons",
         "monster_specials", "monster_text")
CONFIG = "monster_window"


def enabled(app):
    settings = getattr(app, "user_settings", None)
    value = settings.get(SWITCH) if settings is not None else DEFAULTS[SWITCH]
    return value != "off"


def head(model):
    """The stack's head ship when it is a monster (owners 9..14), else None."""
    records = model.get("records") or []
    if not records or not ship_struct.is_monster(records[0].owner):
        return None
    return records[0]


def applies(screen, model):
    return model["kind"] == "fleet" and enabled(screen.app) \
        and head(model) is not None


def values(ship, parts, hstrings, cfg, description):
    """The window's text. Pure: no drawing, no state, so the smoke test can
    hold every value to the table and the design fields.

    `class`: the hull's name; `hit_points`: [(label, number)] and the
    shield's name; `weapons`: [(name, count)]; `specials`: [name]; each
    list's heading and the "None" row are HESTRNGS's (`headings`)."""
    def part(table, index):
        name = parts.name(table, index) if parts is not None else None
        return name if name else cfg.get("unnamed", "#%d") % int(index)

    def number(value):
        return str(int(value)) if value is not None else cfg.get(
            "unknown", "?")

    def message(key, fallback):
        index = cfg.get(key)
        text = hstrings.message(index) if hstrings is not None \
            and index is not None else None
        return text if text and text != str(index) else fallback

    none = message("none", "None")
    heads = dict(cfg.get("headings", {}))
    for key in ("weapons", "specials"):
        heads[key] = message(key + "_heading", heads.get(key, ""))
    weapons = ship_struct.weapons(ship)
    specials = ship_struct.special_bits(ship)
    return {
        "class": part("hulls", ship.size),
        "hit_points": [
            (cfg.get("structure", "Structure"),
             number(monsterhull.structure(ship))),
            (cfg.get("armour", "Armour"), number(monsterhull.armour(ship)))],
        "shield": part("shields", ship.shield_type),
        "weapons": [(part("weapons", w.type), cfg.get("count", "x%d") % w.count)
                    for w in weapons] or [(none, "")],
        "specials": [part("specials", i) for i in specials] or [none],
        "headings": heads,
        "description": description,
    }


def description(screen, owner, cfg):
    """DEVIATION `monster_description`: the type's own sentence where
    `layout.json` has one, else the original's space-monster text."""
    own = cfg.get("descriptions", {}).get(str(int(owner)))
    return own if own else (sysextras.monster_words(screen)[1] or "")


def sprite_path(screen, owner):
    """The panel sprite for the monster's TYPE, through the resource stack.

    **DEVIATION.** The original's own monster picture — the system popup
    no running game reaches — is chosen by STAR INDEX % 5
    (`RUSS::Star_To_Monster_`, MAINPUPS.LBX 15 + that, mainpups.cpp:1082),
    so a star can show a creature that is not the one guarding it. HD
    shows the type that is there, drawn from the galaxy map's own master (`tools/make_ship_icons.py`'s
    panel export) — one source, no second set of artwork. A type without a
    master (the amoeba today) has no file and the box stays EMPTY: no
    stand-in, no silhouette."""
    kind = galaxy_ships.MONSTER_KINDS.get(int(owner))
    if kind is None:
        return None
    return screen.app.res.resolve(os.path.join(
        "screens", "galaxy_map", "assets", "ships", kind,
        zt.MONSTER_PANEL_SPRITE_FILE))


def _load(screen, owner):
    cache = screen.__dict__.setdefault("_monster_sprites", {})
    if owner not in cache:
        path = sprite_path(screen, owner)
        try:
            cache[owner] = pygame.image.load(path).convert_alpha() \
                if path else None
        except (pygame.error, OSError) as exc:
            log.warning("galaxy_map: the panel sprite %s cannot be read (%s)"
                        " — the picture box stays empty", path, exc)
            cache[owner] = None
        if path is None:
            log.info("galaxy_map: no panel sprite for monster owner %s — "
                     "the picture box stays empty", owner)
    return cache[owner]


def _draw_sprite(screen, surface, rect, owner):
    """Contained in the box, never scaled up — a creature cut off at the
    edge would be a different picture."""
    img = _load(screen, owner)
    if img is None:
        return
    f = min(1.0, rect.width / img.get_width(), rect.height / img.get_height())
    size = (max(1, int(img.get_width() * f)), max(1, int(img.get_height() * f)))
    scaled = screen.__dict__.setdefault("_monster_scaled", {})
    if (owner, size) not in scaled:
        scaled.clear()                   # the one copy on screen
        scaled[(owner, size)] = pygame.transform.smoothscale(img, size)
    surface.blit(scaled[(owner, size)], scaled[(owner, size)].get_rect(
        center=rect.center))


def _line(screen, surface, name, rect, text, colour, align="left", room=None):
    """One line of text in its band, fitted to the band's height
    (HD EXTENSION `font_scale`, work order 356: a band does not grow with
    the text size) and, when `room` is given, stepped down until it is no
    wider than `room` px (a weapon's name beside its count)."""
    if not text:
        return
    size = textfit.fit_height_size(screen.style, syswindow.font(
        screen, name, 20), rect.height)
    surf = screen.style.render_text(text, size, tuple(colour[:3]))
    while room is not None and surf.get_width() > room and size > 8:
        size -= 1
        surf = screen.style.render_text(text, size, tuple(colour[:3]))
    x = rect.right - surf.get_width() if align == "right" else rect.x
    surface.blit(surf, (x, rect.y + (rect.height - surf.get_height()) // 2))


def _rows(screen, surface, name, rect, heading, rows, count):
    """A heading and its rows in `count` equal bands (at least the rows
    given); a row is a text or a (text, right-hand text) pair."""
    band = rect.height // max(count, len(rows) + 1)
    label, value = hudtext.colour("label"), hudtext.colour("value")
    for i, row in enumerate([heading] + list(rows)):
        left, right = row if isinstance(row, tuple) else (row, "")
        r = pygame.Rect(rect.x, rect.y + band * i, rect.width, band)
        gap = screen.style.render_text(right + " ", 20, (0, 0, 0)).get_width() \
            if right else 0
        _line(screen, surface, name, r, left, label if i == 0 else value,
              room=r.width - gap)
        _line(screen, surface, name, r, right, value, "right")


def _texts(screen):
    text = hestrings.for_app(screen.app)
    return text if text.state == "ok" else None


def draw(screen, surface, r, model):
    """Draw the window into the rects `r` (box name -> HD rect)."""
    ship = head(model)
    cfg = screen._data.get(CONFIG, {})
    owner = int(ship.owner)
    vals = values(ship, sysfleets.part_names(screen),
                  _texts(screen), cfg,
                  description(screen, owner, cfg))
    scale = screen.layout.scale
    syswindow.frame(screen, surface, r["monster_box"])
    for name in BOXES[3:]:
        hud.panel(surface, r[name], scale)
    syswindow.text(screen, surface, r["monster_title"], model["title"],
                   syswindow.font(screen, "monster_title", 24),
                   hudtext.colour("title"))
    pic = r["monster_picture"]
    # HD EXTENSION `monster_stars` (Data, 30 October 2026): the picture stands
    # on the system window's own star field, so the box is not an empty dark
    # square around a small creature; the field is `sysstars`, one source.
    sysstars.draw(screen, surface, hud.panel_inner(pic, scale),
                  float(cfg.get("star_scale", 2.0)) * scale)
    _draw_sprite(screen, surface, pic.inflate(-pic.width // 8,
                                              -pic.height // 8), owner)
    pad = max(4, int(10 * scale))

    def inner(name):
        return r[name].inflate(-2 * pad, -pad)
    heads, count = vals["headings"], cfg.get("rows", {})
    _rows(screen, surface, "monster_class", inner("monster_class"),
          heads.get("class", ""), [vals["class"]], count.get("class", 2))
    _rows(screen, surface, "monster_hitpoints", inner("monster_hitpoints"),
          heads.get("hit_points", ""),
          vals["hit_points"] + [(vals["shield"], "")],
          count.get("hit_points", 4))
    _rows(screen, surface, "monster_weapons", inner("monster_weapons"),
          heads.get("weapons", ""), vals["weapons"],
          count.get("weapons", 6))
    _rows(screen, surface, "monster_specials", inner("monster_specials"),
          heads.get("specials", ""), vals["specials"],
          count.get("specials", 9))
    text = inner("monster_text")
    size = syswindow.font(screen, "monster_text", 20)
    y = text.y
    step = int(size * 1.25)
    for line in textfit.wrap_text(screen.style, vals["description"], size,
                                  text.width):
        if y + step > text.bottom:
            break
        _line(screen, surface, "monster_text",
              pygame.Rect(text.x, y, text.width, step), line,
              hudtext.colour("value"))
        y += step
