"""The battle playback's pace and the plan of an effect's frames.

Moved out of `cbplay` by work order 338 with the values and the code
unchanged (`cbplay` still names every constant, so callers read them
there). The pace is the original's, TRANSCRIPTION `pace`; the one chosen
value is DEVIATION `untimed_pace`.
"""
MOVE_S = 0.15
#: DEVIATION `untimed_pace` (decision 80, Data, work order 214): a loop of
#: the source without a wait (the move, cmbtmov1.cpp:309-317; the plasma
#: web's travel, cmbtspec.cpp:1075-1094; the gyro's random spin, :580-597;
#: the teleport, cmbtmov1.cpp:816-886; a missile's flight and launch) is
#: paced only by its page flip — 1.9 ms a pass measured (work order 213), a
#: flight would be invisible; HD gives each of its frames a fixed 15 ms, the
#: move's own pace, 10 frames a cell in 0.15 s (decision H of work order
#: 202), so they keep one tempo with each other.
UNTIMED_S = MOVE_S / 10
FRAME_S = 0.055
NUMBER_S = 9 * FRAME_S
BOLT_S = 6 * FRAME_S
#: The beams the colour table does not carry (beams.cpp:1124-1192):
#: weapon id (orion2_consts.h:993-1035) -> (BEAMS.LBX 0's palette fragment,
#: the bolt's length, its step a frame) — the spatial compressor, the
#: mauler, the dragon and plasma breaths, weapon 46.
FRAGMENT = {13: (2, 40, 55), 27: (5, 20, 40), 40: (5, 20, 40),
            43: (5, 20, 40), 46: (6, 40, 50)}
DEATH_SFX = {0: 3, 1: 4, 2: 4, 3: 5, 4: 5, 5: 5}


def sfx_times(p, step):
    """TRANSCRIPTION `effect_pace` (work order 212, decision 2): when each
    frame of an effect's plan is drawn — its `phases` [(frames, seconds a
    frame)], by default all of them a 55 ms tick times `wait` (the
    `Release_Time_(n)` of the source's loop) — every `step`-th one under
    FAST ANIMATIONS, after `delay` seconds; then `hold` ticks in which the
    damage numbers rise and nothing is drawn
    (`Draw_Damage_Message_Queue_Until_Done_`, beams.cpp:495-508). Stores
    `_times` [(start, end, frame)], `_length` and `_number_at` (when the
    effect's number appears: at `number_frame`, else when the frames end) in
    the plan; returns the length in seconds."""
    phases = p.get("phases") or [(p["frames"], FRAME_S * p.get("wait", 1))]
    times, t, base = [], float(p.get("delay", 0.0)), 0
    for count, per in phases:
        for f in range(0, count, max(1, step)):
            times.append((t, t + per, base + f))
            t += per
        base += count
    p["_times"], p["_length"] = times, t + p.get("hold", 0) * FRAME_S
    at = p.get("number_frame")
    p["_number_at"] = next((s for s, _e, i in times if i >= at), t) \
        if at is not None else t
    return p["_length"]


def sfx_frame(p, t):
    """The plan's frame at `t` (0..1 of its length), or None: before the
    delay, in the hold, after the end."""
    tau = t * p.get("_length", 0.0)
    return next((i for s, e, i in p.get("_times", ()) if s <= tau < e), None)
