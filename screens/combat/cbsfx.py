"""The battle's special effects in the original's frames — work order 199 C2.

TRANSCRIPTION `special_effects` (`dev:doc/combat_drawing_reading.md` §5,
cmbtspec.cpp): what an event that is not a beam looks like —

  stasis field (32)    CMBTSFX 1 stretched along the line, two frames a
                       picture (`Release_Time_(2)`), then the stasis ball
                       growing over 10 frames to 90 % (:451-531, 273-355)
  tractor beam (39)    CMBTSFX 2 frames 0-7 along the line, a tick each
                       (:642-684); the held line is the state's
  gyro destabilizer    CMBTSFX 8 along the line, then the target spun one
  (34)                 facing a frame for 8 frames (:1441-1556)
  plasma web (35)      CMBTSFX 14 along the line, then its impact 36-39 by
                       size on the target (:1048-1140)
  black hole (37)      CMBTSFX 47 along the line for 12 ticks
                       (cmbtfire.cpp:1913-1979); the hole on the target
                       is the state's (`cbdraw.lasting_overlay`)
  stellar converter    CMBTSFX 40 along the line, its impact 41 from frame 9
  (38)                 at the target less 60 (:950-1046)
  a bomb               CMBTMISL 144 + facing (160 biological) flying 6 px a
                       frame, then CMBTSFX 7 at the target less 12
                       (cmbtdrw1.cpp:3012-3096)
  a blast hit          its number only: the blast is drawn on the event that
                       fires it (`cbblast`, work order 210)
  web damage           the web on the unit: CMBTSFX 21-35 by size and facing
                       (:357-450)

"Along the line" is `Draw_Bitmap_Line_` (bitmap.cpp:298-336): the picture
stretched to the line's length, turned to its angle, centred on its middle.
HD turns it with pygame's rotation — DEVIATION `texture_line`: the
original's own resampling is not traced (the reading says so).
"""
import math

import pygame

from . import cbdraw
from .cbbeamfx import get_angle

STASIS, ANTI_MISSILE, GYRO, WEB, PULSAR, BLACK_HOLE, CONVERTER, TRACTOR = \
    32, 33, 34, 35, 36, 37, 38, 39
TICK = 0.055                 # s: `Release_Time_(1)`
UNTIMED = 0.015              # s: a frame of a loop without a wait
                             # (DEVIATION `untimed_pace`, decision 80)
#: the damage numbers rise 9 frames (`Draw_Damage_Indicator_`, beams.cpp:
#: 380-382); `Draw_Damage_Message_Queue_Until_Done_` waits for them
NUMBERS = 9
WEB_STEP = 6                 # px a frame (`Plasma_Web_`, cmbtspec.cpp:1073)
TRANSPORTERS = 35            # SPECIAL_TRANSPORTERS
TRANSPORTER_TICKS = 8        # `Draw_Transporter_Bomb_Beam_`'s loop
SPIN_TURNS = 2               # HD STATE `gyro_spin`
BHG = {0: 46, 1: 45, 2: 45, 3: 44, 4: 44, 5: 43}
#: The plasma web and the caustic slime: one routine, `Plasma_Web_`
#: (cmbtfire.cpp:1566-1570).
CAUSTIC_SLIME = 45
WEBS = (WEB, CAUSTIC_SLIME)
BIO = (25, 26)                       # death spore, bio terminator


def has_special(u, bit):
    """`Does_Combat_Ship_Have_Special_`: the bit set and not damaged."""
    from . import cbpanel
    have = cbpanel.special_bits(u.get("special_device_flags") or [0] * 5)
    hurt = cbpanel.special_bits(u.get("special_device_damage_flags") or
                                [0] * 5)
    return bit in have and bit not in hurt


def _range(x1, y1, x2, y2):
    """`special::Range_` (special.cpp:5-25): the longer axis and half the
    shorter."""
    dx, dy = abs(x2 - x1), abs(y2 - y1)
    return dy // 2 + dx if dy < dx else dx // 2 + dy


def _step(x, y, tx, ty, n):
    """`special::Absolute_Interpolate_Line_` from (x, y): `n` px along the
    longer axis toward (tx, ty), the shorter in proportion."""
    dx, dy = tx - x, ty - y
    if abs(dy) < abs(dx):
        k = min(n, abs(dx))
        return x + (k if dx > 0 else -k), y + int(dy * k / abs(dx))
    k = min(n, abs(dy))
    if k == 0:
        return x, y
    return x + int(dx * k / abs(dy)), y + (k if dy > 0 else -k)


def _frames(art, entry, lbx="cmbtsfx"):
    return max(1, art.frame_count(lbx, entry))


def _size_idx(u):
    return {0: 0, 1: 1, 2: 1, 3: 2, 4: 3, 5: 3}.get(int(u["size_class"]), 1)


def _blit_centred(surface, cam, cache, pic, wx, wy, scale=1.0):
    if pic is None:
        return
    img = cbdraw.scaled(pic, cam.scale * scale, cache)
    x, y = cam.to_window(wx, wy)
    surface.blit(img, (x - img.get_width() // 2, y - img.get_height() // 2))


def _blit_at(surface, cam, cache, pic, wx, wy):
    if pic is not None:
        surface.blit(cbdraw.scaled(pic, cam.scale, cache),
                     cam.to_window(wx, wy))


def texture_line(surface, cam, cache, pic, a, b):
    """`Draw_Bitmap_Line_`: `pic` stretched from a to b (world px)."""
    if pic is None or a == b:
        return
    length = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1])))
    key = ("tline", id(pic), length, get_angle(b[0] - a[0], b[1] - a[1]),
           round(cam.scale, 3))
    if key not in cache:
        img = pygame.transform.scale(pic, (length, pic.get_height()))
        img = pygame.transform.rotate(
            img, -get_angle(b[0] - a[0], b[1] - a[1]))
        cache[key] = cbdraw.scaled(img, cam.scale, {})
    img = cache[key]
    x, y = cam.to_window((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    surface.blit(img, (x - img.get_width() // 2, y - img.get_height() // 2))


def stasis_ball(art, u):
    """(entry, mirror, flip) of the stasis ball for `u` (cmbtspec.cpp:273-355):
    0x35 / 0x3A / 0x3F / 9 by size, the facing folded to 0..4."""
    f = int(u["facing_dir"]) & 15
    if 4 < f < 9:
        d, mirror, flip = 8 - f, True, False
    elif 8 < f < 13:
        d, mirror, flip = f - 8, False, False
    elif f >= 13:
        d, mirror, flip = 16 - f, False, True
    else:
        d, mirror, flip = f, False, False
    base = {0: 0x35, 1: 0x3A, 2: 0x3A, 3: 0x3F}.get(int(u["size_class"]), 9)
    return base + d, mirror, flip


def web_picture(u):
    """(entry, mirror, flip) of the plasma web on `u` (cmbtspec.cpp:357-450)."""
    f = int(u["facing_dir"]) & 15
    sub = 4 if f in (4, 12) else f % 4
    even = ((f // 4) & 1) == 0
    s = int(u["size_class"])
    if s == 0:
        e = sub + 31 if even else 35 - sub
    elif s in (1, 2):
        e = sub + 26 if even else 30 - sub
    elif s == 3:
        e = sub + 21 if even else 25 - sub
    else:
        e = sub + 21 if even else 20 - sub
    q = f // 4
    return e, q == 1, q == 3


def anti_missile(a, b, destroyed, art, fast=False):
    """TRANSCRIPTION `anti_missile` (work order 210 C3): the rocket a 3 x 3
    dot in palette 25 with its corners in 16, from the source's centre to
    the missile 20 px a tick (30 under FAST) along the line's major axis
    (`Draw_Anti_Missile_Rockets_`, `Absolute_Interpolate_Line_`,
    cmbtspec.cpp:686-730, 1395-1408); then, when it destroyed any, CMBTSFX 7
    at the missile less 12, a tick a frame (:766-797). `destroyed` is HD's
    reading (HD STATE `anti_missile_count`, `cbplay`)."""
    speed = 30 if fast else 20
    major = max(abs(b[0] - a[0]), abs(b[1] - a[1]))
    fly = max(1, -(-int(major) // speed))
    m = _frames(art, 7) if destroyed else 0
    pal = art.palette_with() if hasattr(art, "palette_with") else {}
    body, corner = pal.get(25, (200, 200, 200)), pal.get(16, (120, 120, 120))

    def draw(surface, cam, cache, frame):
        if frame < fly:
            t = min(1.0, (frame + 1) * speed / max(1, major))
            x = a[0] + (b[0] - a[0]) * t
            y = a[1] + (b[1] - a[1]) * t
            k = max(1, int(round(cam.scale)))
            cx, cy = cam.to_window(x, y)
            surface.fill(body, (cx - k, cy - k, 3 * k, 3 * k))
            for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
                surface.fill(corner, (cx + dx * k, cy + dy * k, k, k))
        elif m:
            _blit_at(surface, cam, cache, art.surface("cmbtsfx", 7,
                                                      frame - fly),
                     b[0] - 12, b[1] - 12)
    # FAST steps the flight, not the blast: `_draw_event`'s step is 1 here
    return {"frames": fly + m, "draw": draw, "step": 1, "fly": fly}


def plan(ev, unit, art, previous=None):
    """The event's effect: a dict with its `frames` and a `draw(surface,
    cam, cache, frame)`, or None when it has none here. `unit(i)` is the
    shown battle's unit; `previous` the event played before (a blast that
    hits several units is drawn once)."""
    k = ev["kind"]
    if k == "special":
        src, dst = unit(ev.get("source", -1)), unit(ev.get("target", -1))
        if src is None or dst is None:
            return None
        a = tuple(int(v) for v in cbdraw.centre(src))
        b = tuple(int(v) for v in cbdraw.centre(dst))
        w = int(ev.get("weapon", 0))
        if w == STASIS:
            n = _frames(art, 1)
            ball, mirror, flip = stasis_ball(art, dst)

            def draw(surface, cam, cache, frame):
                if frame < 2 * n:
                    texture_line(surface, cam, cache,
                                 art.surface("cmbtsfx", 1, frame // 2), a, b)
                else:
                    pct = min(90, (frame - 2 * n + 1) * 10) / 100
                    _blit_centred(surface, cam, cache, art.surface(
                        "cmbtsfx", ball, 0, None, mirror, flip,
                        glass="shield"), *b, pct)
            return {"frames": 2 * n + 10, "draw": draw}
        if w == TRACTOR:
            # `Tractor_Beam_` fires frames 0-7 once, a tick each
            # (cmbtspec.cpp:642-684); the line that stays is the state's
            # (`cbdraw.draw_tractors`, work order 210 C2)
            def draw(surface, cam, cache, frame):
                texture_line(surface, cam, cache, art.surface(
                    "cmbtsfx", 2, frame, glass="tractor"), a, b)
            return {"frames": 8, "draw": draw}
        if w == GYRO:
            # `Draw_Gyro_Special_Effect_` (cmbtspec.cpp:1441-1556): the line,
            # a tick a frame; eight passes of 2 ticks, the target turned one
            # facing each and the line looping its last three frames (:1511-
            # 1549, TRANSCRIPTION `gyro_line`); then `Gyro_Destablizer_`'s
            # spin with no wait (:580-597) — TRANSCRIPTION `gyro_spin` (Data's
            # decision 2 of work order 213): its count is the engine's own
            # random draw (19 of `Random_(13)`, then more while it would end
            # 15, 0 or 1 sixteenths round, :566-575), on the wire since open
            # fix 83 (`spin_turns`, taken by `cbplay`); an engine without it
            # leaves HD STATE `gyro_spin`, two turns round; then the numbers
            # (:637)
            n = _frames(art, 8)
            face0 = int(dst["facing_dir"])
            spin = int(ev.get("spin_turns") or SPIN_TURNS * 16)

            def draw(surface, cam, cache, frame):
                if frame < n:
                    texture_line(surface, cam, cache,
                                 art.surface("cmbtsfx", 8, frame), a, b)
                elif frame < n + 16:
                    k = (frame - n) // 2
                    texture_line(surface, cam, cache, art.surface(
                        "cmbtsfx", 8, k % 3 + n - 3), a, b)
                    dst["facing_dir"] = (face0 + k + 1) & 15
                else:
                    dst["facing_dir"] = (face0 + 9 + frame - n - 16) & 15
                    if frame >= n + 16 + spin - 1:
                        dst["facing_dir"] = face0
            # its sounds, in the engine's order: 11 for the line and its
            # fade, 11 again for the turn and its fade (cmbtspec.cpp:1470,
            # :1508, :1511, :1555), then 3 for the spin, faded once the
            # numbers have risen (:579, :638)
            line, turn = n * TICK, (n + 16) * TICK
            return {"frames": n + 16 + spin, "draw": draw, "hold": NUMBERS,
                    "phases": [(n, TICK), (16, TICK), (spin, UNTIMED)],
                    "sound_times": [0.0, line, line, turn, turn,
                                    turn + spin * UNTIMED + NUMBERS * TICK]}
        if w in WEBS:
            # TRANSCRIPTION `web_travel` (`Plasma_Web_`, cmbtspec.cpp:
            # 1060-1140): CMBTSFX 14, its frames running on, travels from 20
            # px above-left of the source's centre to the same of the
            # target's, 6 px a frame on the longer axis, then the impact
            # 36-39 by size, centred where the blob stopped; neither loop
            # waits (DEVIATION `untimed_pace`)
            n, m = _frames(art, 14), _frames(art, 36 + _size_idx(dst))
            sx, sy, tx, ty = a[0] - 20, a[1] - 20, b[0] - 20, b[1] - 20
            fly = max(1, -(-max(abs(tx - sx), abs(ty - sy)) // WEB_STEP))

            def draw(surface, cam, cache, frame):
                if frame < fly:
                    f = frame / fly
                    _blit_at(surface, cam, cache, art.surface(
                        "cmbtsfx", 14, frame % n), sx + (tx - sx) * f,
                        sy + (ty - sy) * f)
                else:
                    _blit_centred(surface, cam, cache, art.surface(
                        "cmbtsfx", 36 + _size_idx(dst), frame - fly,
                        glass="plasma_web"), *b)
            # its sounds, in the engine's order: the travel's (0x1B) and its
            # fade as the blob arrives, the impact's (0x44) and its fade at
            # the end (cmbtspec.cpp:1072, :1096, :1114, :1148)
            return {"frames": fly + m, "draw": draw,
                    "phases": [(fly + m, UNTIMED)],
                    "sound_times": [0.0, fly * UNTIMED, fly * UNTIMED,
                                    (fly + m) * UNTIMED]}
        if w == BLACK_HOLE:
            # `BHG_` (cmbtfire.cpp:1913-1979): CMBTSFX 47 along the line to
            # the target's centre less half the picture's height, frame
            # `counter % frames` for 12 ticks; the hole itself is the state
            # that follows (`cbdraw.lasting_overlay`, work order 210 C2)
            n = _frames(art, 47)
            pic0 = art.surface("cmbtsfx", 47, 0)
            b2 = (b[0], b[1] - (pic0.get_height() // 2 if pic0 else 0))

            def draw(surface, cam, cache, frame):
                texture_line(surface, cam, cache,
                             art.surface("cmbtsfx", 47, frame % n), a, b2)
            return {"frames": 12, "draw": draw}
        if w == CONVERTER:
            n, m = _frames(art, 40), _frames(art, 41)

            def draw(surface, cam, cache, frame):
                if frame < n:
                    texture_line(surface, cam, cache, art.surface(
                        "cmbtsfx", 40, frame, glass="stellar_converter"), a, b)
                if frame >= 9 and frame - 9 < m:
                    _blit_at(surface, cam, cache, art.surface(
                        "cmbtsfx", 41, frame - 9, glass="stellar_converter"),
                        b[0] - 60, b[1] - 60)
            # each frame `Release_Time_(2)` (cmbtspec.cpp:1013), then the
            # damage numbers until done (:1044)
            return {"frames": max(n, 9 + m), "draw": draw, "wait": 2,
                    "hold": NUMBERS}
        return None
    if k == "bomb":
        src, dst = unit(ev.get("source", -1)), unit(ev.get("target", -1))
        if src is None or dst is None:
            return None
        a, b = cbdraw.centre(src), cbdraw.centre(dst)
        # TRANSCRIPTION `transporter_beam` (`Draw_Bombs_`, cmbtdrw1.cpp:
        # 3024-3040; `Draw_Transporter_Bomb_Beam_`, cmbtspec.cpp:800-854):
        # with working Transporters the bomb starts near the planet — 20 px
        # at a time toward it until within its picture's half-diagonal and
        # 60 px — after 8 ticks of CMBTSFX 15 (frames 0-2) along the line
        # from the ship to there, in the stasis bubble's glass (the shield's
        # table, combinit.cpp:929)
        start, beam = a, 0
        half = ev.get("_planet_half")
        if half and has_special(src, TRANSPORTERS):
            limit = half[0] ** 2 + half[1] ** 2 + 3600
            sx, sy = int(a[0]), int(a[1])
            while _range(sx, sy, int(b[0]), int(b[1])) ** 2 > limit:
                sx, sy = _step(sx, sy, int(b[0]), int(b[1]), 20)
            start, beam = (sx, sy), TRANSPORTER_TICKS
        dist = max(abs(b[0] - start[0]), abs(b[1] - start[1]))
        fly = max(1, -(-int(dist) // 6))
        facing = int(round(get_angle(b[0] - start[0],
                                     start[1] - b[1]) / 22.5)) & 15
        pic_entry = (160 if int(ev.get("weapon", 0)) in BIO else 144) + facing
        m = _frames(art, 7)

        def draw(surface, cam, cache, frame):
            if frame < beam:
                texture_line(surface, cam, cache, art.surface(
                    "cmbtsfx", 15, frame % 3, glass="shield"), a, start)
            elif frame < beam + fly:
                t = (frame - beam) / fly
                _blit_at(surface, cam, cache, art.surface("cmbtmisl",
                                                          pic_entry, 0),
                         start[0] + (b[0] - start[0]) * t - 17,
                         start[1] + (b[1] - start[1]) * t - 17)
            else:
                _blit_at(surface, cam, cache, art.surface(
                    "cmbtsfx", 7, frame - beam - fly), b[0] - 12, b[1] - 12)
        # `Draw_Bombs_` (cmbtdrw1.cpp:3049-3095): a tick a step, the numbers
        # from the impact on, rising through the explosion's frames, then
        # held until done (at least one pass, a do-while)
        return {"frames": beam + fly + m, "draw": draw,
                "number_frame": beam + fly, "hold": max(1, NUMBERS - m)}
    if k == "blast_hit":
        # the blast itself is drawn on the event that fires it (`cbblast`,
        # work order 210 C3/C4); its hits only raise their numbers, held as
        # `Draw_Damage_Message_Queue_Until_Done_` holds them once for all
        # (cmbtspec.cpp:1981-1983)
        if previous is not None and previous.get("kind") == "blast_hit" and \
                previous.get("source") == ev.get("source") and \
                previous.get("blast") == ev.get("blast"):
            return {"frames": 0, "draw": lambda *a_: None}
        if unit(ev.get("source", -1)) is None:
            return None
        return {"frames": 9, "draw": lambda *a_: None}
    if k == "web_damage":
        # the web is on the unit for as long as it burns (the state,
        # `cbdraw.lasting_overlay`); the damage round only raises its
        # numbers (`Plasma_Web_Damage_`, combinit.cpp:2927-3005)
        if unit(ev.get("unit", -1)) is None:
            return None
        return {"frames": 9, "draw": lambda *a_: None}
    return None
