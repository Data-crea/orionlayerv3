"""What in the battle's event queue belongs to one animation — work orders
212 and 213.

The engine records a battle's events in its own order (open fix 56); HD
plays them one animation at a time (`cbplay.Player`). Some events are not
animations of their own but parts of the one before or after them, and
this module is where that grouping is decided, so the Player only plays:

  a FIRE        the beam shots at one target from one unit, recorded one
                after another (cmbtfire.cpp:1363), are one `Beam_SFX_` loop
                (TRANSCRIPTION `firing`, `cbshot`); the Energy Absorber's
                discharge (slot -1, open fix 74) is its own (:1842)
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
    target from the same unit, recorded right after it (cmbtfire.cpp:1363).
    The Energy Absorber's discharge (slot -1, open fix 74) is its own loop
    (cmbtfire.cpp:1842)."""
    return ev["kind"] == "beam_shot" and all(
        ev.get(f) == first.get(f) for f in ("source", "target",
                                             "at_missile")) and \
        -1 not in (ev.get("slot"), first.get("slot"))


def aims_for(first, aim):
    """`aim` (open fix 82) or a spin (83) is one of `first`'s: the same
    shooter and target."""
    return aim.get("source") == first.get("source") and \
        aim.get("target") == first.get("target")


def fire_extent(queue):
    """The queue's head FIRE: (its entries, the index after its last shot)
    — entries counted as `cbshot.plan_firing` groups them."""
    first, i, entries, slot = queue[0], 0, 0, object()
    while i < len(queue) and (i == 0 or same_firing(first, queue[i])):
        if queue[i].get("slot") != slot:
            entries, slot = entries + 1, queue[i].get("slot")
        i += 1
    return entries, i


def aims_ready(queue, aims_seen, now):
    """The head FIRE may start: one aim per entry is queued, or a later event
    is (no aim will come then), or it has waited AIM_WAIT_S. An engine that
    has sent no aim (`aims_seen` False) is waited for by nothing."""
    if not aims_seen:
        return True
    first = queue[0]
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
