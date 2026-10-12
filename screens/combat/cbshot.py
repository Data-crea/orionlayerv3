"""The battle's shots, planned and drawn — work order 199 C2, out of
`cbplay` (the line guideline). `cbplay` finds the shots (`Player._beam`);
this plans their frames (`plan_firing`) and draws them (`draw_firing`).
The bolt itself is `cbbeam`'s port (TRANSCRIPTION `beam_bolt` there), the
shield's flare `cbflare`'s (TRANSCRIPTION `shield_flare`, work order 200).

TRANSCRIPTION `firing` (work order 212, decision 2: the original's tempo).
One FIRE is ONE loop in the original: `Fire_Ship_` records every shot first
(cmbtfire.cpp:1363) and then plays them all through `Beam_SFX_`
(beams.cpp:1312-1712; cmbtfire.cpp:1462), one 55 ms frame a pass
(`Release_Time_(1)`, :1695). Each weapon slot is one entry (its shots fly
from several fire points at once, `N_Fire_Points_`); two entries are drawn
at a time, and the second channel takes the next entry when the first
reaches frame 9, a channel that finishes takes the next at once (:1462-
1556); an entry with weapon special 0x80 plays three times. A channel's
frames are its bolt's 0 .. n (n is the frame it runs out on) — every second
one with FAST ANIMATIONS on (`_speedx2_flag`, :1559-1569: two while two
more fit, then one). The loop ends when both channels are done, the
shield's flare is off and the damage numbers have risen (:1572-1580). Until
work order 212 HD played the shots one after another, which made a volley
up to twice as long as the original's; and it drew one frame more for a
hit flash of its own.
"""
import pygame

from . import cbart, cbbeam, cbdraw, cbflare

#: the frame at which the second channel takes the next entry (beams.cpp:
#: 1466-1470: `frame_idx[other_i] >= 9`)
SECOND_AT = 9
#: a damage number rises for 9 frames (`Done_Drawing_Damage_Message_Queue_`)
NUMBER_TICKS = 9
#: weapon special 0x80: the entry is played three times (`special_timer`)
REPEAT_SPECIAL, REPEATS = 0x80, 3
#: TRANSCRIPTION `multi_beam` (beams.cpp:856-909, 1155-1179, 1243-1266): the
#: Mass Driver and the Gauss Cannon fire three bolts a frame apart with the
#: second muzzle set (`burst_variant` 1, BEAMS.LBX 33-64); the Mauler Device
#: and the dragon's and plasma breaths three bolts with the mauler ball
MULTI_BEAM = {1: 1, 2: 1, 27: 0, 40: 0, 43: 0}      # weapon -> burst variant
MAULER_BALL = 0x58


def bolt_frames(n, fast=False):
    """The bolt frames 0 .. n-1 one shot draws before the frame it runs out
    on; under FAST two at a time while two more fit (a reflection,
    `cbreflect`)."""
    if not fast:
        return list(range(n))
    out, f = [0], 0
    while True:
        f = f + 2 if f + 2 < n else f + 1
        if f >= n:
            return out
        out.append(f)


def schedule(frames, fast=False, repeat=None):
    """`Beam_SFX_`'s two channels over the entries' frame counts:
    [[(entry, frame), ...] for each 55 ms pass]."""
    repeat = repeat or [False] * len(frames)
    cur, frame = [0, -1], [0, 0]
    timer = [REPEATS if repeat and repeat[0] else 0, 0]
    fx, rows = 0, []
    while cur[0] >= 0 or cur[1] >= 0:
        row = []
        for i in (0, 1):
            c = cur[i]
            if c >= 0:
                row.append((c, frame[i]))
                skip = frame[i] >= frames[c]
            else:
                other = cur[1 - i]
                skip = other >= 0 and frame[1 - i] >= SECOND_AT
            if skip:
                frame[i] = 0
                timer[i] -= 1
                if timer[i] <= 0:
                    timer[i] = 0
                    if fx + 1 >= len(frames):
                        cur[i] = -1
                    else:
                        fx += 1
                        cur[i] = fx
                        if repeat[fx]:
                            timer[i] = REPEATS
            elif fast and c >= 0 and frame[i] + 2 < frames[c]:
                frame[i] += 2
            else:
                frame[i] += 1
        rows.append(row)
    return rows


def plan_firing(shots, target, fast=False, total=10):
    """One FIRE's loop. `shots`: [(event, b)] in the engine's order, `b`
    each shot's `Player._beam`; `target` (unit, shield size) or None.
    Returns {"entries": [(event, b, shots)], "rows": per pass [(entry,
    frame)], "flare": per pass (status, counter), "hits": the pass each
    entry runs out on, "b": the flare's drawing fields} — every list as long
    as the loop."""
    entries = []
    for ev, b in shots:
        if entries and entries[-1][0].get("slot") == ev.get("slot"):
            entries[-1][2].append(ev)
        else:
            entries.append((ev, b, [ev]))
    frames = [b["frames"] for _e, b, _s in entries]
    rows = schedule(frames, fast, [bool(int(b.get("specials", 0) or 0) &
                                        REPEAT_SPECIAL)
                                   for _e, b, _s in entries])
    res = [0] * len(entries)
    for k, (_e, _b, evs) in enumerate(entries):
        for ev in evs:
            res[k] |= int(ev.get("result", 0) or 0)
    hits, numbers = [], []
    for k, (_e, b, evs) in enumerate(entries):
        h = hit_frame(b)
        last = b.get("multi", 1) - 1
        hits.append(min(t for t, row in enumerate(rows)
                        for c, f in row if c == k and f + last >= h))
        if any(int(e.get("past_shields", 0) or 0) or
               int(e.get("absorbed", 0) or 0) for e in evs):
            numbers.append(hits[-1])
    lead = entries[0][1]
    flags = []
    for row in rows:
        seen = []
        for c, f in row:
            b = entries[c][1]
            g = lead_frame(b, f)
            seg = cbbeam.segment(b["src"], b["dst"], b["fx"], g, b["stop"]) \
                if g and target is not None else None
            if seg is not None:
                seen.append(bool(res[c] & 1) and cbflare.in_shield(
                    seg[2], seg[3], *b["dst"], target[1]))
        flags.append(None if not seen else any(seen))
    states = cbflare.run(flags, total)[0] if target is not None else \
        [(0, 0)] * len(rows)
    # the loop's end (beams.cpp:1572-1582): checked in each pass after the
    # channels moved and before the flare and the numbers do — both channels
    # done, the flare off since the pass before, every number risen
    p = len(rows) - 1
    while not ((p == 0 or p - 1 >= len(states) or states[p - 1][0] == 0) and
               all(h + NUMBER_TICKS <= p for h in numbers)):
        p += 1
    n = p + 1
    rows += [[]] * (n - len(rows))
    states = (states + [(0, 0)] * n)[:n]
    heavy = [bool(int(b.get("specials", 0) or 0) & cbflare.ENVELOPING or
                  e.get("weapon") == cbflare.PLASMA_CANNON)
             for e, b, _s in entries]
    look = dict(lead)
    if target is not None:
        look.update(
            flare_size=target[1],
            flare_rot=cbflare.hit_facing(lead["src"], lead["dst"],
                                         cbbeam.get_angle),
            flare_special=any(not r & 1 or bool(r & 2) for r in res),
            flare_heavy=[any(heavy[c] and f < frames[c] for c, f in row)
                         for row in rows])
    return {"entries": entries, "rows": rows, "flare": states, "hits": hits,
            "numbers": numbers, "b": look}


def lead_frame(b, f):
    """The frame whose bolt decides the hit and the flare: a multi-beam
    weapon draws three bolts a pass, at frames f, f + 1 and f + 2
    (`loop_count` 3, beams.cpp:1243-1266), and the last one drawn sets
    `_ship_hit_now_flag` — one that has run out (frame >= n) draws nothing
    and leaves the one before it deciding (:2294-2296)."""
    n = b["frames"]
    top = f + b.get("multi", 1) - 1
    return min(top, n - 1) if f < n else f


def hit_frame(b):
    """The frame a bolt strikes (`_ship_hit_now_flag`, beams.cpp:2321-2327):
    the first whose head reaches the target point — at once for a
    continuous beam (:2306-2309) — or `_max_frames - 2`; frame 0 draws only
    the muzzle (:2298-2301)."""
    n = b["frames"]
    rng = cbbeam.ship_range(*b["src"], *b["dst"])
    step = cbbeam.max_frames(b["src"], b["dst"], b["fx"])[1]
    for f in range(1, n):
        if b["fx"].get("style") == 2 or step * f >= rng or f >= n - 2:
            return f
    return max(1, n - 1)


def draw_firing(surface, cam, art, firing, t, cache, palettes, look=None):
    """One pass of the loop at `t` (0..1 of it): each channel's bolt, its
    muzzle burst and hit flash (`_bolt`), the shield's flare."""
    rows = firing["rows"]
    tick = min(len(rows) - 1, int(t * len(rows)))
    for c, frame in rows[tick]:
        ev, b, _s = firing["entries"][c]
        for k in range(b.get("multi", 1)):
            _bolt(surface, cam, art, ev, b, frame + k, cache, palettes)
    st = firing["flare"][tick]
    if st[0] != 0 and look is not None:
        _flare(surface, cam, art, firing["b"], tick, st[1], look, cache)


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
            b["src"], b["dst"], stream, b.get("variant", 0)), frame % 3, pal)
        if pic is not None:
            img = cbdraw.scaled(pic, cam.scale, cache)
            x, y = cam.to_window(*at)
            surface.blit(img, (x - img.get_width() // 2,
                               y - img.get_height() // 2))
    if b.get("ball") and 0 < frame < n and frame < hit_frame(b):
        # TRANSCRIPTION `mauler_ball`: the ball at the bolt's head until it
        # strikes (`_mauler_ball_seg`, BEAMS.LBX 0x58; beams.cpp:2420-2422)
        seg = cbbeam.segment(b["src"], b["dst"], b["fx"], frame, b["stop"])
        pic = art.surface("beams", MAULER_BALL, 0, pal) if seg else None
        if pic is not None:
            img = cbdraw.scaled(pic, cam.scale, cache)
            x, y = cam.to_window(seg[2], seg[3])
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
            nw, nh = cbart.native_size(pic)
            cache[key] = None if m is None else cbflare.brightened(
                pic, m, nw // 2 - d // 2, nh // 2 - d // 2,
                art.palette_with(), cache.setdefault("flare_memo", {}),
                k=cbart.hd_factor(pic))
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
