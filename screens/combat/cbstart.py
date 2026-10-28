"""How each kind of event starts — its plan, its length, its numbers.

Moved out of `cbplay.Player._start` by work order 338 with the behaviour
unchanged: the event kinds that need more than a few lines to plan (an
effect, a FIRE of beam shots, a death, the anti-missile rocket). Each takes
the `Player` as its first argument and reads and writes the state the
original methods did, in the same order; `Player._start` stays the one place
that picks the kind and returns the animation's length in seconds.
"""
from . import (cbart, cbbeamfx, cbblast, cbdraw, cbnumbers, cbpace, cbqueue,
               cbsfx, cbshot)


def effect(player, ev, now, k):
    """The effect's length, or None when `Player._start` goes on to its
    word."""
    w = int(ev.get("weapon", 0))
    # a spherical blast is drawn on the special that fires it, every
    # time (work order 210 C3, `cbblast`)
    p = cbblast.plan(player, ev.get("source", -1), cbblast.AREA[w],
                     player._art) if k == "special" and \
        w in cbblast.AREA else None
    if p is None and k == "special" and w == cbsfx.ANTI_MISSILE:
        p = anti_missile(player, ev)
    if k == "bomb" and player.planet is not None:
        # the planet picture's size, for the Transporters' start
        # point (cmbtdrw1.cpp:3026-3027)
        w, h = cbart.native_size(player.planet[0])
        ev["_planet_half"] = (w // 2, h // 2)
    if k == "special" and w == cbsfx.GYRO:
        player._take_spin(ev)
    if p is None:
        p = cbsfx.plan(ev, player._unit, player._art, player._last)
    if p is not None:
        ev["_sfx"] = p
        if k == "special" and w == cbsfx.CONVERTER:   # work order 260
            ev["_charges"] = cbqueue.take_converter(player._queue, ev)
        u = player._unit(ev.get("unit", ev.get("target", -1)))
        hit = ev.get("past_shields") or ev.get("hits")
        length = cbpace.sfx_times(p, p.get("step", ev["_step"]))
        if u is not None and not ev.get("at_missile"):
            player._number(u, hit, ev.get("absorbed"),
                         now + p["_number_at"])
        if ev.get("_destroyed"):
            # the missiles destroyed, over the missile as the blast
            # starts (`Add_Damage_Indicator_For_Missile_`,
            # cmbtspec.cpp:772)
            player._marks.append((str(ev["_destroyed"]), *ev["_at"],
                                now + p["fly"] * cbpace.FRAME_S,
                                (0xff, 0xcc, 0x40)))
        return length


def beam_shot(player, ev, now):
    """One FIRE as one loop (TRANSCRIPTION `firing`)."""
    # TRANSCRIPTION `firing` (`cbshot`, work order 212): every shot
    # of one FIRE is one loop — the queued shots at the same target
    # go with this one
    shots = [ev] + cbqueue.take_firing(ev, player._queue, player._charge)
    # a reflection is drawn after its slot, the rest of the FIRE
    # after it (`cbqueue.split_at_reflection`)
    shots, back, rest = cbqueue.split_at_reflection(shots)
    ev["_tail"] = shots[-1]["seq"]
    player.last_beam = shots[-1]
    u = None if ev.get("at_missile") else \
        player._unit(ev.get("target", -1))
    aims = player._take_aims(ev)
    if back is not None:
        n = len({e.get("slot") for e in shots})
        if rest:
            rest[0]["_aims"] = aims[n:]
        player._queue[:0] = [back] + rest
    planned, k, slot = [], -1, object()
    for e in shots:
        if e.get("slot") != slot:
            k, slot = k + 1, e.get("slot")
        aim = aims[k] if k < len(aims) and int(
            aims[k].get("weapon", -1)) == int(e.get("weapon", 0)) \
            else None
        b = player._beam(e, aim)
        if b is not None:
            planned.append((e, b))
    if not planned:
        return cbpace.BOLT_S
    f = ev["_firing"] = cbshot.plan_firing(
        planned, cbshot.flared(player, ev, u), player.fast,
        cut=back is not None)
    src = player._unit(ev.get("source", -1))
    side = 1 if src is None or u is None else cbnumbers.side_of(
        cbdraw.centre(u), cbdraw.centre(src), cbbeamfx.get_angle)
    for (_e, _b, evs), hit in zip(f["entries"], f["hits"]):
        if u is not None:
            # the numbers appear in the pass the bolt strikes
            # (beams.cpp:1660-1672), the pair the entry summed
            player._number(u, *(sum(int(e.get(k, 0) or 0) for e in evs)
                              for k in ("past_shields", "absorbed")),
                         now + hit * cbpace.FRAME_S, side)
    return len(f["rows"]) * cbpace.FRAME_S


def destroy(player, ev):
    """A unit's death, in a blast or on its own."""
    u = player._unit(ev.get("unit", -1))
    state = int(ev.get("death_state", 1))
    # HD STATE `view_pause`: `Destroy_Ship_FX_` waits 7 ticks before
    # a ship off ITS 32 x 18 view explodes (cmbtspec.cpp:1175-1178),
    # the view fix 65 centres on the action; HD's camera is not that
    # view, and measured on the same battle (work order 212, run M4)
    # the pause fell where the original took none — HD does not wait
    delay = 0.0
    if u is not None and state in (2, 3, 4) and \
            int(ev.get("previous_owner", 0)) < 10:
        # a ship dying in a blast (work order 210 C4, `cbblast`)
        p = cbblast.plan(player, ev["unit"], state, player._art)
        if p is not None:
            p["delay"] = delay
            ev["_sfx"] = p
            return cbpace.sfx_times(p, ev["_step"])
    if u is None:
        return 18 * cbpace.FRAME_S / ev["_step"]
    ev["_death"] = cbblast.death_plan(u, player._art)
    ev["_dp"] = {"frames": ev["_death"][1], "delay": delay}
    return cbpace.sfx_times(ev["_dp"], ev["_step"])


def anti_missile(player, ev):
    """The anti-missile rocket's plan, or None: HD STATE
    `anti_missile_count` (`cbsfx.anti_missile_for`) reads the stacks
    it destroyed from the next state queued."""
    later = next((o for seq, _c, o in player._after
                  if seq is None or seq >= ev["seq"]), None)
    return cbsfx.anti_missile_for(ev, player._unit(ev.get("source", -1)),
                                  player.ordnance, later, player._queue,
                                  player._art, player.fast)
