"""The battle's reduced map in the panel — work order 209 B1, Data's decision 1.

TRANSCRIPTION `reduced_map`: what `Draw_Reduced_Combat_Map_` and
`Draw_Reduced_Map_Box_` draw (cmbtdrw1.cpp:1168-1262) into the panel's right
end, a 121 x 102 window at (500, 364) — the whole 81 x 68 field at 3/2 px a
cell (`x * 3 / 2 + 500`):

  the planet   at unit 0's cell: a tiny one as a 4 x 4 blip in the
               defender's ramp, else COMBAT.LBX 0x36 + size + colour * 4 at
               `size - 7` px, its 0x50..0x5F recoloured into the defender's
               ramp (combinit.cpp:1468, 1474)
  each unit    alive (`unit_status` 0): a blip by size class — 2 x 2 (0),
               3 x 3 (1, 2), 4 x 4 (3), 5 x 5 (4, 5) — its dots at ramp
               offsets 1..9 (`Draw_Blip2_`..`Draw_Blip5_`, :1332-1435) of
               0x20 for the attacker, 0x60 for the defender: the two sides'
               own colour ramps (`Load_Combat_Ship_Palette_`, combinit.cpp:
               1435-1488)
  each missile one dot in 0x1C at `(x / 20) * 3 / 2`
  the view     four corner brackets, 7 px long, in 0x8A round the main
               view: the view's cells at 3/2 px, one px outside it
  the acting   its blip stepping through offsets 0, 2, 5, 2 at
  unit         `(_ship_frame / 2) % 4` (`Draw_Fake_Combat_Buttons_`,
               :883-929)

A click is the map's grid field (combat1.cpp:120, :156; one cell a native
px) and centres the view on the cell under it, `(map * 2) / 3`
(`Snap_Center_Combat_Screen_`, :685-686). HD centres its own camera there
and sends nothing: the engine's view is hidden and is centred on every
command anyway (open fix 65).

HD STATE `view_frame`: the brackets frame what HD's camera shows, which at a
wider zoom is more than the original's 32 x 18 cells (HD EXTENSION
`free_camera`, [combat.field]).
OMISSION `missile_warning_picture`: with MISSILE WARNING on and a missile on
its way to a human player's unit the original shows its warning picture in
the map's place (cmbtdrw1.cpp:874-878, 1849-1857); the warning is not on the
wire, so HD keeps the map.
"""
import pygame

from core import lbx

#: The map's native window: `Add_Grid_Field_(500, 364, 1, 1, 121, 102, …)`.
NATIVE_W, NATIVE_H = 121, 102
#: Palette indices (the battle palette, FONTS.LBX 4).
ATTACKER, DEFENDER, MISSILE, FRAME = 0x20, 0x60, 0x1C, 0x8A
#: `Draw_Blip2_`..`Draw_Blip5_`: each blip's dots as ramp offsets, by row.
BLIPS = {
    2: ((9, 6), (6, 4)),
    3: ((9, 6, 4), (6, 6, 4), (4, 4, 1)),
    4: ((1, 4, 4, 1), (4, 9, 6, 4), (4, 6, 6, 4), (1, 4, 4, 1)),
    5: ((2, 4, 4, 4, 1), (4, 9, 9, 6, 4), (4, 9, 6, 6, 4), (4, 6, 6, 6, 4),
        (1, 4, 4, 4, 1)),
}
#: size class -> blip size (cmbtdrw1.cpp:1192-1209).
BLIP_OF = {0: 2, 1: 3, 2: 3, 3: 4, 4: 5, 5: 5}
#: `blip_frame_arr` (cmbtdrw1.cpp:884-885).
PULSE = (0, 2, 5, 2)
#: The bracket's length past its corner: 499..506 (cmbtdrw1.cpp:1251).
BRACKET = 7
CELL = 20


def rect_for(area):
    """The map's rect at the right end of `area`, the original's 121:102,
    as tall as the area."""
    h = area.h
    w = int(round(h * NATIVE_W / NATIVE_H))
    return pygame.Rect(area.right - w, area.y, w, h)


def cell_at(rect, x, y):
    """The field cell a click on the map names, `(map * 2) / 3`, or None."""
    if not rect.collidepoint(x, y):
        return None
    mx = int((x - rect.x) * NATIVE_W / rect.w)
    my = int((y - rect.y) * NATIVE_H / rect.h)
    return (mx * 2) // 3, (my * 2) // 3


def ramps(art, combat, colours):
    """{palette index: RGB} for 0x20.. and 0x60..: the attacker's and the
    defender's ramps — a player's CMBTSHP colour * 45 + 44, a monster's
    MONSTER.LBX player + 5 (combinit.cpp:1447-1455)."""
    out = {}
    if art is None or not art.available:
        return out
    for side, base in (("attacker", ATTACKER), ("defender", DEFENDER)):
        player = int(combat.get(side, -1))
        if 0 <= player < 8:
            blob = art.blob("cmbtshp", int(colours.get(player, 0)) * 45 + 44)
        else:
            blob = art.blob("monster", player + 5)
        try:
            h = lbx.parse_header(blob)
            if not h.has_palette:
                continue
            for i, rgb in lbx.read_palette(blob, h.frame_count).items():
                if 0x20 <= i < 0x40:
                    out[i - 0x20 + base] = rgb
        except (lbx.LbxError, TypeError):
            continue
    return out


def _colour(palette, index):
    return palette.get(index, (255, 0, 255))


def _blip(surface, rect, k, nx, ny, base, size, palette):
    for row, offs in enumerate(BLIPS[size]):
        for col, off in enumerate(offs):
            px = rect.x + int((nx + col) * k)
            py = rect.y + int((ny + row) * k)
            surface.fill(_colour(palette, base + off),
                         (px, py, max(1, int(k + 0.5)), max(1, int(k + 0.5))))


def view_box(rect, cam):
    """The camera's visible field in map px (window coordinates), one
    native px outside the cells it shows (`Draw_Reduced_Map_Box_`)."""
    k = rect.w / NATIVE_W
    vx, vy = cam.ox / CELL, cam.oy / CELL
    vw, vh = cam.area[2] / cam.scale / CELL, cam.area[3] / cam.scale / CELL
    return pygame.Rect(int(rect.x + (vx * 1.5 - 1) * k),
                       int(rect.y + (vy * 1.5 - 1) * k),
                       int((vw * 1.5 + 2) * k), int((vh * 1.5 + 2) * k))


_PLANETS = {}


def planet_picture(art, combat, colours, size, palette, pulse=0):
    """COMBAT.LBX 0x36 + size + colour * 4 with its 0x50..0x5F taken into
    the defender's ramp at 0x60 (combinit.cpp:1457-1476), darkened by
    `pulse` steps while the planet acts (cmbtdrw1.cpp:896-902), or None —
    the defender is the planet's owner; with no player (MAX_PLAYERS) size 2
    and colour 2 (:1459-1461). Kept per key with its palette, because the
    art's cache knows a palette by its identity."""
    if art is None or not art.available:
        return None
    player = int(combat.get("defender", -1))
    colour = int(colours.get(player, 0)) if 0 <= player < 8 else 2
    size = int(size) if 0 <= player < 8 else 2
    if size <= 0:
        return None
    ramp = tuple(palette.get(0x60 + i) for i in range(16))
    key = (id(art), size, colour, pulse, ramp)
    if key not in _PLANETS:
        extra = {0x50 + i: ramp[max(0, i - pulse)] for i in range(16)
                 if ramp[max(0, i - pulse)] is not None}
        _PLANETS[key] = (extra, art.surface("combat", 0x36 + size +
                                            colour * 4, 0, extra))
    return _PLANETS[key][1]


def draw(surface, rect, combat, ordnance, cam, art, colours, planet,
         clock, scale):
    """The map into `rect`. `planet` is the battlefield planet's (picture,
    size) (`cbart.planet_picture`) or None; `clock` the screen's
    `ship_frame`."""
    palette = dict(art.palette_with() if art is not None and art.available
                   else {})
    palette.update(ramps(art, combat, colours))
    surface.fill((0, 0, 0), rect)
    k = rect.w / NATIVE_W
    clip = surface.get_clip()
    surface.set_clip(rect)
    units = combat["units"]
    cur = combat["cur_ship"]
    attacker = combat.get("attacker")
    pulse = PULSE[(clock // 2) % 4]
    if combat.get("colony", -1) != -1 and units and planet is not None:
        u = units[0]
        nx, ny = u["x"] * 3 // 2, u["y"] * 3 // 2
        size = int(planet[1])
        planet_pic = planet_picture(art, combat, colours, size, palette,
                                    pulse if cur == 0 else 0)
        if planet_pic is None:
            _blip(surface, rect, k, nx, ny, DEFENDER + (pulse if cur == 0
                                                        else 0), 4, palette)
        else:
            img = pygame.transform.scale(planet_pic, (
                max(1, int(planet_pic.get_width() * k)),
                max(1, int(planet_pic.get_height() * k))))
            surface.blit(img, (rect.x + int((nx + size - 7) * k),
                               rect.y + int((ny + size - 7) * k)))
    for i, u in enumerate(units):
        if i == 0 or u["unit_status"] != 0:
            continue
        base = ATTACKER if u["owner"] == attacker else DEFENDER
        if i == cur:
            base += pulse
        _blip(surface, rect, k, u["x"] * 3 // 2, u["y"] * 3 // 2, base,
              BLIP_OF.get(int(u["size_class"]), 2), palette)
    for m in (ordnance or {}).get("missiles", []):
        nx, ny = (int(m["x"]) // CELL) * 3 // 2, (int(m["y"]) // CELL) * 3 // 2
        surface.fill(_colour(palette, MISSILE),
                     (rect.x + int(nx * k), rect.y + int(ny * k),
                      max(1, int(k + 0.5)), max(1, int(k + 0.5))))
    if cam is not None:
        box = view_box(rect, cam)
        c, w = _colour(palette, FRAME), max(1, int(k + 0.5))
        b = int(BRACKET * k)
        for (x, y, dx, dy) in ((box.left, box.top, 1, 1),
                               (box.right, box.top, -1, 1),
                               (box.left, box.bottom, 1, -1),
                               (box.right, box.bottom, -1, -1)):
            pygame.draw.line(surface, c, (x, y), (x + dx * b, y), w)
            pygame.draw.line(surface, c, (x, y), (x, y + dy * b), w)
    surface.set_clip(clip)
