"""What in the battle's event queue belongs to one animation — work orders
212 and 213.

The engine records a battle's events in its own order (open fix 56); HD
plays them one animation at a time (`cbplay.Player`). Some events are not
animations of their own but parts of the one before or after them, and
this module is where that grouping is decided, so the Player only plays:

  a FIRE        the beam shots at one target from one unit, recorded one
                after another (v2 cmbtfire.cpp:1497), are one `Beam_SFX_`
                loop (TRANSCRIPTION `firing`, `cbshot`); the Energy
                Absorber's discharge (slot -1, open fix 74) is its own
                (v2 :1973)
  a reflection  recorded BEFORE the shot it answers (v2 cmbtfire.cpp:1474,
                then :1497), so it goes with the shot after it, and the loop
                draws it after that shot's slot (`reflection_order`)
  its aims      open fix 82: one `beam_aim` per entry, recorded inside the
                loop as it starts the entry — the points the original draws
                it between; they can arrive a snapshot after the shots (the
                shield flare polls input, beams.cpp:705), so a FIRE waits for
                them, briefly
  a gyro's spin open fix 83: `gyro_spin`, the turns the engine drew, after
                the line's sounds
  instant       events HD draws nothing for: played with the animation
                before them
"""
from . import cbsound

#: events HD draws nothing for: played with the animation before them (a
#: FIRE takes its aims and a gyro its spin before that, open fixes 82, 83)
INSTANT = ("missile_launch", "missile_merge", "missile_gone", "beam_aim",
           "gyro_spin")
#: how long a FIRE waits for an aim of open fix 82 still to come
AIM_WAIT_S = 0.3


def same_firing(first, ev):
    """`ev` is another shot of `first`'s FIRE: a beam shot at the same
    target from the same unit, recorded right after it (v2
    cmbtfire.cpp:1497). The Energy Absorber's discharge (slot -1, open fix
    74) is its own loop (v2 cmbtfire.cpp:1973)."""
    return ev["kind"] == "beam_shot" and all(
        ev.get(f) == first.get(f) for f in ("source", "target",
                                             "at_missile")) and \
        -1 not in (ev.get("slot"), first.get("slot"))


#: open fix 94 (work order 259): the Energy Absorber's charge as the engine
#: takes it. TRANSCRIPTION `absorber_charge`: the original takes every
#: shot's damage of a FIRE — and with it every charge (`Apply_Ship_Damage_`,
#: cmbtfire.cpp:776-791) — in its slot loop (`Fire_Beam_Weapon_`, :1323)
#: and plays the one `Beam_SFX_` loop only after it (:1461), so the glow is
#: on from the loop's first frame: a FIRE takes the charges recorded
#: between its shots as it starts.
CHARGE = "absorb"


def reflects_on(shot, ev):
    """`ev` is a reflection of `shot`'s beam: the reflector its target, the
    shooter its source (CEV_REFLECT's target and source, v2
    cmbtfire.cpp:1474)."""
    return ev["kind"] == "reflect" and not shot.get("at_missile") and \
        ev.get("reflector") == shot.get("target") and \
        ev.get("shooter") == shot.get("source")


def _next_shot(first, queue, i):
    """Where the next shot of `first`'s FIRE is in `queue`, at `i` or past
    the charges and the reflections there, else None."""
    while i < len(queue) and (queue[i]["kind"] == CHARGE or
                              reflects_on(first, queue[i])):
        i += 1
    return i if i < len(queue) and same_firing(first, queue[i]) else None


def take_firing(first, queue, charge):
    """The other shots of `first`'s FIRE, taken out of `queue`; each charge
    recorded between them is handed to `charge` now (`absorber_charge`),
    each reflection goes with the shot after it (`_reflects`)."""
    shots = []
    while True:
        j = _next_shot(first, queue, 0)
        if j is None:
            return shots
        for e in queue[:j]:
            if e["kind"] == CHARGE:
                charge(e)
            else:
                queue[j].setdefault("_reflects", []).append(e)
        del queue[:j]
        shots.append(queue.pop(0))


def lead_reflects(queue):
    """A reflection at the head of `queue` goes with the beam shot it comes
    before (v2 cmbtfire.cpp:1474, :1497): moved onto it, past the charges
    between them, which stay to be applied as the FIRE starts. One with no
    shot after it is played alone (`cbreflect`)."""
    if not queue or queue[0]["kind"] != "reflect" or queue[0].get("_slot"):
        return
    probe = {"source": queue[0].get("shooter"),
             "target": queue[0].get("reflector")}
    j = 0
    while j < len(queue) and (queue[j]["kind"] == CHARGE or
                              reflects_on(probe, queue[j])):
        j += 1
    if j == len(queue) or queue[j]["kind"] != "beam_shot" or \
            not reflects_on(queue[j], queue[0]):
        return
    refl = [e for e in queue[:j] if e["kind"] == "reflect"]
    queue[j].setdefault("_reflects", [])[:0] = refl
    queue[:j] = [e for e in queue[:j] if e["kind"] != "reflect"]


def split_at_reflection(shots):
    """TRANSCRIPTION `reflection_order`: the loop draws a reflection after
    the entry of its slot — the slot's damages sent back are one damage
    entry behind that entry (v2 cmbtfire.cpp:1565-1576), and `Beam_SFX`
    fires it back once the entry's channel is done and the other waits
    (v2 beams.cpp:1428-1452), then goes on with the next entries, the
    shield's flare cleared. Returns (the shots up to that slot's last, the
    reflection as one event — the slot's weapon, its damages summed — the
    shots after), or (shots, None, []). The reflection is marked `_slot`:
    its FIRE has placed it."""
    k = 0
    while k < len(shots):
        end = k
        while end + 1 < len(shots) and \
                shots[end + 1].get("slot") == shots[k].get("slot"):
            end += 1
        refl = [r for e in shots[k:end + 1] for r in e.get("_reflects", ())]
        if refl:
            merged = dict(refl[-1], seq=shots[end]["seq"], _slot=True,
                          weapon=shots[k].get("weapon", 0))
            for key in ("past_shields", "absorbed"):
                merged[key] = sum(int(r.get(key, 0) or 0) for r in refl)
            return shots[:end + 1], merged, shots[end + 1:]
        k = end + 1
    return shots, None, []


def take_charges(queue):
    """The charges recorded right after a special's event, past its sounds
    and the events HD draws nothing for, taken out of `queue` (work order
    260): the Stellar Converter draws its line and THEN does its damage
    (`Stellar_Converter_`, cmbtspec.cpp:1014-1035) — HD applies them when
    the line's frames end, before the numbers' hold, as the original does."""
    out, keep, done = [], [], False
    for e in queue:
        if not done and e["kind"] == CHARGE:
            out.append(e)
            continue
        if e["kind"] not in cbsound.KINDS and e["kind"] not in INSTANT:
            done = True
        keep.append(e)
    queue[:] = keep
    return out


def take_converter(queue, special):
    """The converter's charges (`take_charges`), and its two totals (open
    fix 95, recorded after them) put on its `special` event as every hit's
    pair, so its numbers rise after its line (work order 266). An engine
    without the fix sends no totals: no numbers, as before."""
    charges = take_charges(queue)
    for i, e in enumerate(queue):
        if e["kind"] == "converter_hit":
            if e.get("source") == special.get("source") and \
                    e.get("target") == special.get("target"):
                special["past_shields"] = e.get("past_shields", 0)
                special["absorbed"] = e.get("absorbed", 0)
                del queue[i]
            break
        if e["kind"] not in cbsound.KINDS and e["kind"] not in INSTANT:
            break
    return charges


def aims_for(first, aim):
    """`aim` (open fix 82) or a spin (83) is one of `first`'s: the same
    shooter and target."""
    return aim.get("source") == first.get("source") and \
        aim.get("target") == first.get("target")


def fire_extent(queue):
    """The queue's head FIRE: (its entries, the index after its last shot)
    — entries counted as `cbshot.plan_firing` groups them."""
    first, i, entries, slot = queue[0], 0, 0, object()
    while i < len(queue):
        j = i if i == 0 else _next_shot(first, queue, i)
        if j is None:
            break
        if queue[j].get("slot") != slot:
            entries, slot = entries + 1, queue[j].get("slot")
        i = j + 1
    return entries, i


def aims_ready(queue, aims_seen, now):
    """The head FIRE may start: one aim per entry is queued, or a later event
    is (no aim will come then), or it has waited AIM_WAIT_S. An engine that
    has sent no aim (`aims_seen` False) is waited for by nothing."""
    first = queue[0]
    if not aims_seen or "_aims" in first:
        return True
    entries, i = fire_extent(queue)
    aims = 0
    for e in queue[i:]:
        if e["kind"] == "beam_aim":
            aims += aims_for(first, e)
        elif e["kind"] not in cbsound.KINDS and e["kind"] not in INSTANT:
            return True
    if aims >= entries:
        return True
    first.setdefault("_held_at", now)
    return now - first["_held_at"] >= AIM_WAIT_S


def take_aims(queue, ev):
    """The aims of `ev`'s FIRE, taken out of `queue` (past its sounds), in
    the engine's order — one per entry as its loop starts it."""
    out, keep, done = [], [], False
    for e in queue:
        if not done and e["kind"] == "beam_aim" and aims_for(ev, e):
            out.append(e)
            continue
        if e["kind"] not in cbsound.KINDS and e["kind"] not in INSTANT:
            done = True
        keep.append(e)
    queue[:] = keep
    return out


def take_spin(queue, ev):
    """The gyro's spin (open fix 83: the turns the engine drew), taken out
    of `queue` past the line's sounds, into `ev["spin_turns"]`."""
    for i, e in enumerate(queue):
        if e["kind"] == "gyro_spin" and aims_for(ev, e):
            ev["spin_turns"] = int(e.get("turns", 0) or 0)
            del queue[i]
            return
        if e["kind"] not in cbsound.KINDS and e["kind"] not in INSTANT:
            return


def death_on_move(queue, move, cell):
    """TRANSCRIPTION `move_until_death`: where the moving unit died on its
    way (world px), or None. The move is recorded as it starts, to its end
    cell (v2 cmbtmov1.cpp:373); the loop stops where the unit is dead
    (:381-383) — killed by a missile it meets (:445-452; `Resolve_Missile`,
    v2 cmbtmis.cpp:936-943) or by defensive fire (v2 cmbtmov1.cpp:454-460) —
    and the death is drawn there (CEV_DESTROY's x and y px, v2
    cmbtfire.cpp:394; `Destroy_Ship_FX`, v2 cmbtspec.cpp:1206). The death is
    looked for until the next move or turn; one at the end cell or off the
    way is no death on the move."""
    a = (move["from_x"] * cell, move["from_y"] * cell)
    b = (move["to_x"] * cell, move["to_y"] * cell)
    for e in queue:
        if e["kind"] in ("move", "rotate"):
            return None
        if e["kind"] == "destroy" and e.get("unit") == move.get("unit"):
            p = (e.get("x_px"), e.get("y_px"))
            if None in p or p == b or not all(
                    min(a[i], b[i]) <= p[i] <= max(a[i], b[i])
                    for i in (0, 1)):
                return None
            return p
    return None
