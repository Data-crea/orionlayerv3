"""How each kind of event starts — its plan, its length, its numbers.

Moved out of `cbplay.Player._start` by work order 338 with the behaviour
unchanged: the event kinds that need more than a few lines to plan (an
effect, a FIRE of beam shots, a death, the anti-missile rocket). Each takes
the `Player` as its first argument and reads and writes the state the
original methods did, in the same order; `Player._start` stays the one place
that picks the kind and returns the animation's length in seconds.
"""
from . import (cbart, cbbeamfx, cbblast, cbdraw, cbmonsterdeath, cbnumbers,
               cbpace, cbqueue, cbsfx, cbshot)


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
        # point (cmbtdrw1.cpp:3115-3117)
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
        if u is not None and not ev.get("at_missile") and k == "bomb":
            # TRANSCRIPTION `point_numbers`: `Draw_Bombs_` shows the
            # hits only, by `Add_Damage_Indicator_For_Missile` or, for
            # the Death Spore and the Bio-Terminator, `_For_Biological`
            # (cmbtdrw1.cpp:3158-3162; beams.cpp:673-697)
            player._number_point(u, ev.get("hits"), now + p["_number_at"],
                                 int(ev.get("weapon", 0)) in cbsfx.BIO)
        elif u is not None and not ev.get("at_missile"):
            player._number(u, hit, ev.get("absorbed"),
                         now + p["_number_at"])
        if ev.get("_destroyed"):
            # the missiles destroyed, over the missile as the blast
            # starts (`Add_Damage_Indicator_For_Missile_`,
            # cmbtspec.cpp:772)
            # TRANSCRIPTION `point_numbers`: the same rising, drifting
            # orange number as a missile's hit, 8 right and 8 up of the
            # missile (`Add_Damage_Indicator_For_Missile`, beams.cpp:
            # 673-686; cmbtspec.cpp:806), no longer a static word mark
            m = cbnumbers.mark_point(ev["_at"], ev["_destroyed"],
                                     now + p["fly"] * cbpace.FRAME_S)
            if m is not None:
                player._numbers.append(m)
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
    # TRANSCRIPTION `missile_numbers` (work order 398): a beam that strikes
    # a missile or a fighter group queues `Add_Damage_Indicator_For_Missile`
    # at the group's place (no centre offset, `target_center_x =
    # target_x`), the damage alone, in the pass the bolt strikes
    # (beams.cpp:1244-1262, 1594-1602); the sound 0x1c and the group's
    # quantity are the engine's (the sound event, the next state)
    at = player._target_point(ev) if ev.get("at_missile") else None
    for (_e, _b, evs), hit in zip(f["entries"], f["hits"]):
        if at is not None:
            m = cbnumbers.mark_point(
                at, sum(int(e.get("past_shields", 0) or 0) for e in evs),
                now + hit * cbpace.FRAME_S)
            if m is not None:
                player._numbers.append(m)
        if u is not None:
            # the numbers appear in the pass the bolt strikes
            # (beams.cpp:1660-1672), the pair the entry summed
            player._number(u, *(sum(int(e.get(k, 0) or 0) for e in evs)
                              for k in ("past_shields", "absorbed")),
                         now + hit * cbpace.FRAME_S, side)
    return len(f["rows"]) * cbpace.FRAME_S


def destroy(player, ev):
    """A unit's death, in a blast or on its own."""
    # TRANSCRIPTION `Destroy_Ship_By` (cmbtfire.cpp:400): the original draws
    # the death only for a unit whose status was 0 when it was destroyed. The
    # engine's CEV_DESTROY is sent first thing, before that test
    # (cmbtfire.cpp:394), so a second destroy of a unit that is already out
    # (status 5 retreated or dead) arrives as an event with a status above 0
    # and draws nothing here either. Work order 437, audit combat F12; the
    # case itself is UNVERIFIED live.
    if int(ev.get("status_before", 0) or 0) != 0:
        return 0.0
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
    # TRANSCRIPTION `monster_death` (work order 393, `cbmonsterdeath`): a
    # monster has its own death pictures, whatever the death state
    mp = cbmonsterdeath.plan(u, player._art)
    if mp is not None:
        ev["_mdeath"] = mp
        return cbpace.sfx_times(mp, ev["_step"])
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
