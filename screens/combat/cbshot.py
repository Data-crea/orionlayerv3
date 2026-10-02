"""One shot of the battle, planned and drawn — work order 199 C2, out of
`cbplay` (the line guideline). `cbplay` finds the shot (`Player._beam`);
this plans its frames (`plan`) and draws one (`draw`). The bolt itself is
`cbbeam`'s port (TRANSCRIPTION `beam_bolt` there), the shield's flare
`cbflare`'s (TRANSCRIPTION `shield_flare`, work order 200).

THE FRAMES of a shot are the original's shot loop (`Beam_SFX_`,
beams.cpp:1340-1712), one 55 ms frame each: the bolt's frames 0 .. n-1 —
every second one with FAST ANIMATIONS on (`_speedx2_flag`, :1559-1569:
two while two more fit, then one) — then the frame the shot runs out on,
one more for its hit flash (HD's, work order 199), and the flare's play-out
until it is off (:1578-1585). A shot followed by another of the same volley
(the next event, same shooter and target) hands its flare on and ends on
the frame it runs out: the original plays a volley in one loop.
"""
import pygame

from . import cbbeam, cbdraw, cbflare


def bolt_frames(n, fast=False):
    """The bolt frames the loop draws, in order."""
    if not fast:
        return list(range(n))
    out, f = [0], 0
    while True:
        f = f + 2 if f + 2 < n else f + 1
        if f >= n:
            return out
        out.append(f)


def plan(ev, b, target, fast=False, carry=None, volley=False):
    """Fill `b` (`Player._beam`'s shot) with its frames: `ticks` — the bolt
    frame of each 55 ms frame, None once the bolt is done — and `flare` —
    each frame's (status, counter) of the shield's flare, or None. `target`
    is (unit, shield size) or None; `carry` what the volley's shot before
    left; `volley` True when the next event continues the volley. Returns
    what this shot hands on."""
    n = b["frames"]
    seq = bolt_frames(n, fast)
    b["ticks"] = seq + [n] + ([] if volley else [n + 1])
    b["flare"] = None
    res = int(ev.get("result", 0) or 0)
    carry = carry or {"state": (0, 0), "flag": False, "pierced": False}
    pierced = carry["pierced"] or not res & 1 or bool(res & 2)
    if target is None:
        return None
    unit, size = target
    tx, ty = b["dst"]
    flags = []
    for f in seq:
        seg = cbbeam.segment(b["src"], b["dst"], b["fx"], f, b["stop"]) \
            if f else None
        flags.append(None if seg is None else bool(res & 1) and
                     cbflare.in_shield(seg[2], seg[3], tx, ty,
                                       cbflare.SHIP_SIZE.get(
                                           int(unit["size_class"]), 1)))
    flags.append(None if volley else False)       # the frame it runs out
    if not volley:
        flags.append(False)                       # HD's flash frame
    states, flag = cbflare.run(flags, b.get("total", 10), carry["state"],
                               play_out=not volley)
    b["flare"] = states
    b["ticks"] += [None] * (len(states) - len(b["ticks"]))
    b["flare_size"] = size
    b["flare_rot"] = cbflare.hit_facing(b["src"], b["dst"],
                                        cbbeam.get_angle)
    b["flare_special"] = pierced
    heavy = (b.get("specials", 0) & cbflare.ENVELOPING or
             ev.get("weapon") == cbflare.PLASMA_CANNON)
    b["flare_heavy"] = [bool(heavy) and i < len(seq)
                        for i in range(len(states))]
    return {"state": states[-1], "flag": flag, "pierced": pierced} \
        if volley else None


def plan_once(target, size, at, missile_at):
    """A missile's hit on a shield (`Draw_Shield_Hit_Once_Through_`,
    beams.cpp:287-333, from cmbtmis.cpp:543-546 when the hit took shield
    points): the flag for the first frame only, then the play-out — the
    flare centred where the missile struck, turned by the missile's bearing
    from the target and the target's facing (cmbtmis.cpp:339-342)."""
    cx, cy = at
    facing = int(target["facing_dir"]) & 15
    mx, my = missile_at
    bearing = cbbeam.get_angle(mx - cx, cy - my) - facing // 2 - facing * 22
    bearing += 360 if bearing < 0 else 0
    states, _f = cbflare.run([True], 10)
    return {"frames": 0, "ticks": [None] * len(states), "flare": states,
            "flare_size": size, "flare_special": False,
            "flare_rot": ((bearing * 2 + 22) // 45 + facing) & 15,
            "flare_heavy": [False] * len(states), "src": at, "dst": at}


def draw(surface, cam, art, ev, b, t, cache, palettes, look=None):
    """One frame of the shot at `t` (0..1 of its frames): the muzzle burst
    on the bolt's first three frames, the bolt, the hit flash at its end
    (beams.cpp:2294-2479), the shield's flare (`cbflare`)."""
    ticks = b.get("ticks") or list(range(b["frames"] + 2))
    tick = min(len(ticks) - 1, int(t * len(ticks)))
    frame = ticks[tick]
    if frame is not None:
        _bolt(surface, cam, art, ev, b, frame, cache, palettes)
    states = b.get("flare")
    if states and states[tick][0] != 0 and (look is not None or
                                             b.get("reflection")):
        _flare(surface, cam, art, b, tick, states[tick][1], look, cache)


def _bolt(surface, cam, art, ev, b, frame, cache, palettes):
    n = b["frames"]
    key = ("beam", ev.get("seq"), ev.get("serial"), frame,
           round(cam.scale, 3))
    if key not in cache:
        px = cbbeam.shot(b["src"], b["dst"], b["fx"], frame, b["stop"],
                         ev.get("seq", 0) or 0, b.get("skip", 0))
        cols = cbbeam.colours(b["fx"])
        if b["fragment"] is not None:
            cols = cbbeam.fragment_colours(art, b["fragment"]) or cols
        img = None
        if px:
            xs = [p[0] for p in px]
            ys = [p[1] for p in px]
            x0, y0 = min(xs), min(ys)
            img = pygame.Surface((max(xs) - x0 + 1, max(ys) - y0 + 1),
                                 pygame.SRCALPHA)
            for (x, y), c in px.items():
                img.set_at((x - x0, y - y0), cols[max(0, min(15, c))])
            img = (cbdraw.scaled(img, cam.scale, {}), (x0, y0))
        cache[key] = img
    if cache[key] is not None:
        img, (x0, y0) = cache[key]
        surface.blit(img, cam.to_window(x0, y0))
    # the burst and the flash paint with the beam slots 0x90-0xAF, which
    # the original fills with the weapon's colours as it fires
    # (Set_Beam_Colors_; BEAMS 1-32 and 65/66 use nothing else) — one
    # palette object per colour set, as `cbart` caches by it
    cols = cbbeam.colours(b["fx"])
    pal = palettes.setdefault(tuple(cols), {
        **{0x90 + i: c for i, c in enumerate(cols)},
        **{0xA0 + i: c for i, c in enumerate(cols)}})
    stream = 0
    at = b["src"]
    if b.get("skip"):                     # a reflected beam's burst rides at
        seg = cbbeam.segment(b["src"], b["dst"], b["fx"], frame, b["stop"],
                             b["skip"])   # its tail every frame (:2445)
        at = seg[:2] if seg else None
    if at is not None and (frame < 3 or b.get("skip")):  # Draw_Ship_Burst_
        pic = art.surface("beams", cbbeam.muzzle_entry(
            b["src"], b["dst"], stream), frame % 3, pal)
        if pic is not None:
            img = cbdraw.scaled(pic, cam.scale, cache)
            x, y = cam.to_window(*at)
            surface.blit(img, (x - img.get_width() // 2,
                               y - img.get_height() // 2))
    if ev.get("result", 0) & 3 and frame >= n - 2:   # :2459-2477
        cnt = max(2, art.frame_count("beams", 0x41 + stream))
        pic = art.surface("beams", 0x41 + stream,
                          (frame - n + 7) % (cnt - 1), pal)
        if pic is not None:
            img = cbdraw.scaled(pic, cam.scale, cache)
            surface.blit(img, cam.to_window(b["dst"][0] - 8,
                                            b["dst"][1] - 8))


def _flare(surface, cam, art, b, tick, counter, look, cache):
    """`Draw_Shield_Hit_` (beams.cpp:557-704): the target's picture again,
    brightened under the flare's glass pixels, then the flare over it."""
    size, rot = b["flare_size"], b["flare_rot"]
    if b.get("reflection"):           # Draw_Reflection_Field_Hit_ (:1724-1794)
        e = 0x59 + size * 5 + cbflare.BASE_ROT[rot]
        d = cbflare.REFLECTION_DIAMETERS[size]
    else:
        e = cbflare.entry(cbflare.BASE_ROT[rot], size, b["flare_special"],
                          b["flare_heavy"][tick])
        d = cbflare.DIAMETERS[size]
    frame = counter % max(1, art.frame_count("beams", e))
    pic, (ox, oy) = look or (None, (0, 0))
    if pic is not None and not b.get("reflection"):
        key = ("flared", id(pic), e, frame, rot)
        if key not in cache:
            m = cbflare.mask(art, e, frame, rot)
            cache[key] = None if m is None else cbflare.brightened(
                pic, m, pic.get_width() // 2 - d // 2,
                pic.get_height() // 2 - d // 2, art.palette_with(),
                cache.setdefault("flare_memo", {}))
        if cache[key] is not None:
            surface.blit(cbdraw.scaled(cache[key], cam.scale, cache),
                         cam.to_window(ox, oy))
    key = ("flare", e, frame, rot)
    if key not in cache:
        cache[key] = cbflare.mask(art, e, frame, rot)
    if cache[key] is not None:
        att, dfn = b.get("ramps", (0, 0))
        pk = ("flare_pals", att, dfn)
        if pk not in cache:
            cache[pk] = (cbflare.build_palette(art),
                         cbflare.show_palette(art, att, dfn))
        at = b.get("flare_at", b["dst"])
        cbflare.draw_glassed(surface, cache[key][2], cam.to_window(
            at[0] - d // 2, at[1] - d // 2), cam.scale,
            cache[pk][0], cache.setdefault("glass_memo", {}), cache[pk][1])


# ── the screen's player, for the flare ────────────────────────────────
def flared(player, ev, u):
    """(target, its shield size) when the shot struck a shield, else None —
    a planet's size by the planet (`cbflare`)."""
    if u is None or not int(ev.get("result", 0) or 0) & 1:
        return None
    if ev.get("target") == 0:
        if player.planet is None:
            return None
        return u, cbflare.PLANET_SIZE.get(player.planet[1], 7)
    return u, cbflare.SHIP_SIZE.get(int(u["size_class"]), 1)


def ramps(player, b):
    """The attacker's and defender's colours, for the flare's glass."""
    c = player.shown or {}
    b["ramps"] = tuple(player.colours.get(c.get(k, -1), 0)
                       for k in ("attacker", "defender"))
    return b


def look(player, ev, art):
    """The flared target's picture and its top-left (world px)."""
    if ev.get("target") == 0:
        if player.planet is None:
            return None
        u = player.unit(0)
        ox, oy = cbdraw.PLANET_OFF.get(player.planet[1], (7, 7))
        return player.planet[0], (u["x"] * cbdraw.CELL + ox,
                                  u["y"] * cbdraw.CELL + oy)
    u = player.unit(ev.get("target", -1))
    if u is None:
        return None
    return (cbdraw.unit_picture(art, player.colours, u, 0),
            cbdraw.sprite_origin(u))
