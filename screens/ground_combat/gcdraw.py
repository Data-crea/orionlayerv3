"""The ground combat's drawing — work order 232 C.

Everything comes from open fix 91's TPOP kind 11 (`core.invasionwire`): the
frame the engine's `Draw_Colony_Combat_Screen_` drew last — each unit, beam
and explosion where and as it drew it, in its order — and both sides' boxes.
HD draws that frame; it computes no motion of its own, so the motion and its
pace are the original's (one frame per 55 ms tick, a round every sixth).

TRANSCRIPTION:
  the scene     the colony's sky and ground (`C_Anims_(1)`, `C_Anims_(0)`,
                colgcbt.cpp:854-857), the colony screen's own picture
                (`colart.scene`), at the field's integer scale (`gcgeom`)
  a unit        its COLGCBT.LBX picture by side, kind and state at its frame
                and place (`Do_Unit_Turn_`, :463-606; `gcart.unit_entry`),
                its side's colour, the colony screen's palette
  a beam        `Draw_CGCBT_Beam_`'s one-pixel line (:1420-1460) as
                `bolt::Bolt_Segment_` colours it (bolt.cpp:153-260): from
                the base colour across the range along the line, clamped,
                every eighth pixel lit with sparkles, the tip brightened
  an explosion  COLONY.LBX 7 at its frame and place (`FLCQUEUE`)
  a box         the header in its side's colour, the bonus lines as
                `Print_Data_` prints them (label left, value right, E 0x4B
                "%+d"), the troop totals: per kind present its figure
                (`Player_Troop_Anim_`) and three lines, all in the
                ATTACKER'S colour in both boxes, as the original sets it
                (`Set_Colony_Font_To_Player_(1, _g_attack_ptr->player_id)`,
                :946)

DEVIATION `beam_jitter`: a beam's colour jitter (`Random_(100) <
color_jitter_chance`) is HD's own random — the engine's draws advance the
fight's seed, which HD does not replay.
OMISSION `ground_buildings`: the colony's buildings on the scene
(`COLONY::Draw_Colony_Bldgs_`, :862) are not drawn — HD places no building on
a colony's ground yet ([colony.buildings], parked since work order 180).
"""
import random

import pygame

from core.hestrings import printf
from screens.colony import colart
from screens.leaders import ldrdraw as nd

from . import gcart, gcgeom as geom

#: `_player_font_color_array` (colony.cpp:153-162): a player colour's font
#: colours, set shadow-down (`Set_Font_Style_Shadow_Down_`, fonts.cpp:824-
#: 827): the second is the glyphs', the first their shadow one pixel below —
#: measured on the native frame (work order 232: player colour 1's text is
#: index 187, (228, 136, 32), over a 183 shadow; colour 2's 234 over 232).
GLYPH, SHADOW = 1, 0
PLAYER_FONT = ((236, 238, 237), (183, 187, 185), (232, 234, 233),
               (83, 102, 100), (245, 251, 249), (154, 156, 155),
               (240, 242, 241), (154, 156, 155))
#: COLONY.LBX 7's picture as the explosion queue names it.
FLIC_STEMS = {"ground": "explosion", "bomb": "bomb", "bio": "bio"}
#: Troop names by kind (`Player_Troop_Name_`, colony.cpp:2296-2315): (E
#: string without, with the technology, the technology application) — tanks
#: with Battleoids (24), infantry with Powered Armor (144); militia 0x174,
#: kind 3 0x1BC.
TROOP_NAMES = {0: (0x1F8, 0xC3, 24), 1: (0x14D, 0x1AC, 144),
               2: (0x174, 0x174, None), 3: (0x1BC, 0x1BC, None)}
#: `Player_Troop_Anim_` (colony.cpp:2317-2336) -> `Military_Anims_(v, race)`:
#: (without, with the technology).
TROOP_FIGURES = {0: (3, 4), 1: (1, 2), 2: (0, 0), 3: (1, 1)}
RESEARCHED = 3


def fmt(template, *values):
    """An E string with its values: they are C formats ("%d %s", "%+d
    combat"); Python's % reads them, `printf` what it cannot."""
    try:
        return template % values
    except (TypeError, ValueError):
        return printf(template, *values)


def player(state, idx):
    from core.structs import player as player_struct
    raws = getattr(state, "player_raw", None) or []
    return player_struct.parse(raws[idx]) if 0 <= idx < len(raws) else None


def researched(p, app):
    apps = list(getattr(p, "tech_applications", ()) or ())
    return app is not None and len(apps) > app and apps[app] == RESEARCHED


def colony_world(state, colony):
    """(climate, ground type) of the colony's planet, as the colony screen
    takes them (`colart`): the colony record's climate, the planet's
    `climate_bg_type`."""
    from core.structs import colony as colony_struct
    from core.structs import planet as planet_struct
    cols = getattr(state, "colonies_raw", None) or []
    if not 0 <= colony < len(cols):
        return 0, 0
    c = colony_struct.parse(cols[colony])
    planets = getattr(state, "planets_raw", None) or []
    bg = 0
    if 0 <= c.planet < len(planets):
        bg = int(getattr(planet_struct.parse(planets[c.planet]),
                         "climate_bg_type", 0) or 0)
    return int(c.climate), bg


class Frame:
    """What one draw needs: the popup's numbers and the pictures' state."""

    def __init__(self, screen, popup, state):
        self.screen, self.popup, self.state = screen, popup, state
        a = popup["args"]
        self.colony, self.attacker, self.defender = a[0], a[1], a[2]
        self.battleoids = a[6] == 1
        self.climate, self.bg = colony_world(state, self.colony)
        self.inv = popup.get("invasion") or {}
        self.art = gcart.load()
        self.colart = colart.load()
        self.palette = self.colart.palette(self.climate, self.bg) \
            if self.colart.available else {}
        pa, pd = player(state, self.attacker), player(state, self.defender)
        self.players = (pa, pd)
        self.colours = tuple(int(getattr(p, "color", 0)) if p else 0
                             for p in self.players)

    def rgb(self, index):
        c = self.palette.get(int(index) & 0xFF)
        return tuple(c[:3]) if c else (255, 255, 255)


def draw(surface, screen, popup, state):
    """The whole screen but the shell (the screen draws the plate and the
    panels): the field and the two boxes' contents."""
    f = Frame(screen, popup, state)
    lay = screen.app.layout
    field = screen.box_screen_rect(geom.FIELD)
    if field is not None:
        fm = geom.FieldMap(lay, field)
        old = surface.get_clip()
        surface.set_clip(fm.clip)
        _scene(surface, f, fm)
        _units(surface, f, fm)
        _beams(surface, f, fm)
        _flics(surface, f, fm, f.inv.get("flics") or [])
        surface.set_clip(old)
        scale = fm.scale
    else:
        scale = geom.scale_for(lay, 640 * 3)
    for side, name in enumerate(geom.BAND):
        r = screen.box_screen_rect(name)
        if r is not None:
            _box(surface, f, geom.BoxMap(lay, r, scale), side)


def _scene(surface, f, fm):
    if not f.colart.available:
        return
    pic = f.colart.scene(f.climate, f.bg)
    if pic is None:
        return
    s = fm.scale
    part = pic.subsurface(pygame.Rect(0, fm.top, geom.NATIVE_W,
                                      geom.NATIVE_H - fm.top))
    surface.blit(pygame.transform.scale(part, (part.get_width() * s,
                                               part.get_height() * s)),
                 fm.rect.topleft)


def _sprite(f, stem, frame, colour, s):
    key = ("gc", f.climate, f.bg, colour, s)
    pic = f.art.surface(stem, frame, f.palette, gcart.colour_map(colour),
                        key=key[:4])
    if pic is None:
        return None
    return pygame.transform.scale(pic, (pic.get_width() * s,
                                        pic.get_height() * s))


def _units(surface, f, fm):
    if not f.art.available:
        return
    for u in f.inv.get("units") or []:
        entry = gcart.unit_entry(u["side"], u["type"], u["state"],
                                 f.battleoids)
        if entry is None:
            continue
        # the infantry wear their side's colour; the tanks are the defender's
        colour = f.colours[1] if u["type"] == 0 else \
            f.colours[1 if u["side"] == 1 else 0]
        pic = _sprite(f, f"gcbt_{entry}", u["frame"], colour, fm.scale)
        if pic is not None:
            surface.blit(pic, fm.point(u["x"], u["y"]))


def beam_pixels(x1, y1, x2, y2, colour, rng=random):
    """`bolt::Bolt_Segment_`'s line (bolt.cpp:153-260): [(nx, ny, index)]
    along the line from (x1, y1) to (x2, y2), coloured as it colours them.
    `colour` is `Draw_CGCBT_Beam_`'s p5..p14: base, range, jitter chance,
    jitter range, min, max, (legacy), sparkles, sparkle phase, tip."""
    base, rng_c, chance, jrange, lo, hi, _leg, sparkles, phase, tip = colour
    dx, dy = abs(x2 - x1), abs(y2 - y1)
    n = max(dx, dy) + 1
    buf = [0] * (n + 2)
    step = (rng_c << 16) // n
    acc, jit = 32000 // n, 0
    up = y2 < y1
    for i in range(n + 1):
        c = ((acc >> 16) + jit + base) & 0xFF
        buf[(n - i + 1) if up else (i + 1)] = c
        acc += step
        jit = (rng.randrange(jrange * 2 + 1) - jrange) \
            if rng.randrange(100) < chance else 0
    if up:
        buf[n], buf[0] = base & 0xFF, (base + rng_c - 1) & 0xFF
    else:
        buf[0], buf[n] = base & 0xFF, (base + rng_c - 1) & 0xFF
    if sparkles == 1:
        for i in range(phase % 8, n + 2, 8):
            buf[i] = (buf[i] + 3) & 0xFF
    buf = [min(max(c, lo), hi) for c in buf]
    if tip:
        fade = 3 // tip
        idx = range(1, 7) if up else (range(n - 6, n) if n > 5 else ())
        for i in idx:
            buf[i] = (buf[i] + fade) & 0xFF
    buf = [min(c, base + 15) for c in buf]
    # `line::Plasma_Line_` (line.cpp:568-…): drawn from the UPPER end down,
    # the colour run taken from its start — which is why the run above is
    # written backwards for a line that rises
    if y1 > y2:
        x1, y1, x2, y2 = x2, y2, x1, y1
    out = []
    for i in range(n):
        t = i / (n - 1) if n > 1 else 0.0
        out.append((int(round(x1 + (x2 - x1) * t)),
                    int(round(y1 + (y2 - y1) * t)), buf[i]))
    return out


def _beams(surface, f, fm):
    s = fm.scale
    for b in f.inv.get("beams") or []:
        for nx, ny, idx in beam_pixels(b["x1"], b["y1"], b["x2"], b["y2"],
                                       b["colour"]):
            x, y = fm.point(nx, ny)
            # LOOK EXCEPTION transcription: a beam's pixels in the original's palette colours (bolt.cpp:153-260)
            surface.fill(f.rgb(idx), (x, y, s, s))


def _flics(surface, f, fm, flics):
    for e in flics:
        stem = FLIC_STEMS.get(e["picture"])
        if stem is None or not f.art.available:
            continue
        pic = _sprite(f, stem, e["frame"], 2, fm.scale)
        if pic is not None:
            surface.blit(pic, fm.point(e["x"], e["y"]))


def _text(surface, screen, words, x, y, size, colour, align="left", w=600,
          shadow=None, drop=0):
    """One line; with `shadow`, first in that colour `drop` px lower — the
    original's shadow-down style."""
    if shadow is not None and drop:
        nd.blit_text(surface, screen.style, words, x, y + drop, w, size,
                     shadow, align=align)
    return nd.blit_text(surface, screen.style, words, x, y, w, size, colour,
                        align=align)


def troop_name(estrings, p, kind):
    """`Player_Troop_Name_` (colony.cpp:2296-2315): the kind's name, the
    technology's where the player has researched it."""
    without, with_, app = TROOP_NAMES[kind]
    return estrings.string(with_ if researched(p, app) else without) or ""


def _box(surface, f, bm, side):
    """A summary box (`Draw_Summary_Box_ATK_` / `_DEF_`, `Print_Data_`,
    `Print_Troop_Totals_`)."""
    s = bm.scale
    e = f.screen.estrings
    sides = f.inv.get("sides") or []
    if side >= len(sides):
        return
    me = sides[side]
    font = PLAYER_FONT[f.colours[side] % 8]
    ink, shade = f.rgb(font[GLYPH]), f.rgb(font[SHADOW])
    size = max(nd.MIN_FONT, 9 * s)
    x, y = bm.point(geom.HEADER_DX, geom.HEADER_Y - 40)
    _text(surface, f.screen, e.string(0xBB if side == 0 else 0x100) or "",
          x, y, size, ink, "center", shadow=shade, drop=s)
    for i, line in enumerate(me.get("lines") or []):
        ly = geom.LINE_Y0 - 40 + (i + 1) * geom.LINE_PITCH
        lx, ly_ = bm.point(geom.LINE_DX, ly)
        rx, _ry = bm.point(geom.LINE_DX + geom.LINE_W, ly)
        _text(surface, f.screen, line["label"], lx, ly_, size, ink,
              shadow=shade, drop=s)
        _text(surface, f.screen, fmt("%+d", line["value"]), rx, ly_,
              size, ink, "right", shadow=shade, drop=s)
    _totals(surface, f, bm, side, me)


def _totals(surface, f, bm, side, me):
    s = bm.scale
    p = f.players[side]
    race = int(getattr(p, "race", 0)) if p else 0
    kinds = [k for k, t in enumerate(me.get("troops") or []) if t["count"]]
    if not kinds:
        return
    spacing = geom.TOTALS_SPAN // (len(kinds) + 1)
    font = PLAYER_FONT[f.colours[0] % 8]                 # the attacker's
    colour, shade = f.rgb(font[GLYPH]), f.rgb(font[SHADOW])
    size = max(nd.MIN_FONT, 8 * s)
    e = f.screen.estrings
    for i, kind in enumerate(kinds):
        t = me["troops"][kind]
        cx = spacing * (i + 1)
        without, with_ = TROOP_FIGURES[kind]
        _n, _w, app = TROOP_NAMES[kind]
        v = with_ if researched(p, app) else without
        pic = f.colart.sprite(f"military_{race}_{v}", f.climate, f.bg) \
            if f.colart.available else None
        if pic is not None:
            big = pygame.transform.scale(pic, (pic.get_width() * s,
                                               pic.get_height() * s))
            fx, fy = bm.point(cx, geom.TOTALS_FIGURE_FOOT - 40)
            surface.blit(big, (fx - big.get_width() // 2,
                               fy - big.get_height()))
        hits = e.string(22 if t["hits"] <= 1 else 23) or "%d"
        for line, ny in zip((fmt(e.string(14) or "%d %s", t["count"],
                                 troop_name(e, p, kind)),
                             fmt(hits, t["hits"]),
                             fmt(e.string(13) or "%+d", t["combat"])),
                            geom.TOTALS_LINES):
            x, y = bm.point(cx, ny - 40)
            _text(surface, f.screen, line, x, y, size, colour, "center",
                  shadow=shade, drop=s)
