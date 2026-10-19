"""A retreat, drawn — work order 305 (the audit's item 18). Until then HD
drew CMBTSFX 42 over the unit's centre for a fixed 12 frames and hid the
unit from half-way.

TRANSCRIPTION `retreat_slide` (`Draw_Retreating_Ship`, v2
cmbtdrw1.cpp:2455-2572; the turn before it is its own event, `Rotate_Ship`
:2474-2476): the warp effect CMBTSFX 42 stands beside the ship — left of it
for the attacker, 28 px past half the ship's drawn width and the effect's
own width, right of it for the defender, 31 px past half its width — centred
on the ship's height (:2497-2504); every one of its frames is drawn, every
third under FAST ANIMATIONS (:2539-2544), a tick each (:2561); the ship
slides into it, `x_offset / 3` px a frame for the first five, `x_offset / 4
+ 1` after, times the frame step (:2460-2461, :2545-2546, :2563-2567),
drawn only inside the window between the effect's inner edge and the ship's
far side (:2523-2534, :2557-2558), so it vanishes into the effect. A ship
that died turning away draws nothing (:2478-2480; CEV_RETREAT's status 5).

OMISSION `retreat_view_clamp`: the original keeps the effect 4 px inside its
640 x 350 view (:2506-2518) — HD's camera is no such view.
"""
import pygame

from . import cbart, cbdraw

ENTRY = 42
#: the attacker's and the defender's gap (v2 cmbtdrw1.cpp:2458)
GAP = {True: 28, False: 31}


def _actual(pic):
    """`Get_Ship_Actual_Size`: the drawn pixels' width and height, in the
    stored drawing's pixels (v2 cmbtdrw1.cpp:2732-2744)."""
    k = cbart.hd_factor(pic)
    r = pic.get_bounding_rect()
    return max(1, r.width // k), max(1, r.height // k)


def plan(u, attacker, art, colours, fast):
    """The retreat's frames and places (world px), or None (no unit, a
    ship that died turning away). `attacker`: the unit is the attacker's."""
    if u is None or art is None:
        return None
    frames = art.frame_count("cmbtsfx", ENTRY)
    fx = art.surface("cmbtsfx", ENTRY, 0)
    pic = cbdraw.unit_picture(art, colours, u, 1)
    if frames <= 0 or fx is None:
        return None
    ew, eh = cbart.native_size(fx)
    sw, sh = _actual(pic) if pic is not None else (20, 20)
    cx, cy = (int(v) for v in cbdraw.centre(u))
    gap = GAP[attacker]
    x = cx - sw // 2 - gap - ew if attacker else cx + sw // 2 + gap
    y = cy - eh // 2
    clip = (x + 0x21, y + 0x35, cx + sw, cy + sh) if attacker else \
        (cx - sw, y + 0x35, x + 0x1E, y + eh)
    step = 3 if fast else 1
    offsets, off = [], 0
    for f in range(0, frames, step):
        offsets.append((f, off))
        move = (gap // 3 if f < 5 else gap // 4 + 1) * step
        off += -move if attacker else move
    return {"at": (x, y), "clip": clip, "passes": offsets}


def length(p):
    """How many ticks the retreat takes."""
    return len(p["passes"]) if p else 0


def draw(surface, cam, art, colours, u, p, t, cache, glow=1):
    """Pass `t` (0..1) of the retreat: the effect's frame beside the ship
    and the ship slid into it, clipped to the original's window."""
    if p is None or u is None:
        return
    k = min(len(p["passes"]) - 1, int(t * len(p["passes"])))
    frame, off = p["passes"][k]
    pic = art.surface("cmbtsfx", ENTRY, frame)
    if pic is not None:
        surface.blit(cbdraw.scaled(pic, cam.scale, cache),
                     cam.to_window(*p["at"]))
    ship = cbdraw.unit_picture(art, colours, u, glow)
    if ship is None:
        return
    x1, y1 = cam.to_window(p["clip"][0], p["clip"][1])
    x2, y2 = cam.to_window(p["clip"][2] + 1, p["clip"][3] + 1)
    was = surface.get_clip()
    surface.set_clip(pygame.Rect(int(x1), int(y1), int(x2 - x1),
                                 int(y2 - y1)).clip(was))
    ox, oy = cbdraw.sprite_origin(u)
    surface.blit(cbdraw.scaled(ship, cam.scale, cache),
                 cam.to_window(ox + off, oy))
    surface.set_clip(was)
