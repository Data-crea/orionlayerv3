"""A reflection, played — work order 200 A3. Until then HD showed nothing for
CMEV's `reflect` (its word mark looked for a key the event does not have).

TRANSCRIPTION `reflection` — a Reflection Field sends part of a beam back
(`Fire_Beam_Weapon_`, cmbtfire.cpp:1743-1748; the event at :1340-1342) and
the shot loop plays it after the shots (`Beam_SFX_`, beams.cpp:1480-1530):
the same weapon fired back from the reflector at the shooter
(`reflected_fx`), its tail a third of the reflection field's diameter out
(`Fire_Weapon_`, :2388-2395) and its strands starting there (:2421-2424),
past every shield (its special flag is set); the reflection field's own
flare on the reflector — BEAMS.LBX 0x59 + size * 5 + rotation, the
rotation from the shooter (:1630-1640), on at once, four frames in, then
out (`Adjust_Reflection_Field_Display_Status_`, :1797-1837;
`Draw_Reflection_Field_Hit_`, :1724-1794) — and the reflected damage over
the shooter.

The weapon is the shooter's last shot at the reflector, as the event comes
right after it; without one HD fires the thin bolt.
"""
from . import cbbeam, cbdraw, cbflare, cbshot


def plan(player, ev):
    """The reflected shot as `cbshot` draws it, or None."""
    ref, shooter = player.unit(ev.get("reflector", -1)), \
        player.unit(ev.get("shooter", -1))
    if ref is None or shooter is None:
        return None
    last = player.last_beam or {}
    weapon = last.get("weapon", 3) if last.get("source") == ev["shooter"] \
        and last.get("target") == ev["reflector"] else 3
    b = player._beam({"source": ev["reflector"], "target": ev["shooter"],
                      "weapon": weapon, "slot": -1, "result": 2})
    if b is None:
        return None
    size = cbflare.SHIP_SIZE.get(int(ref["size_class"]), 1)
    b["skip"] = cbflare.REFLECTION_DIAMETERS[size] // 3
    seq = cbshot.bolt_frames(b["frames"], player.fast)
    states = cbflare.reflection_run(max(1, player.reflection_frames))
    n = max(len(seq) + 1, len(states))
    b["ticks"] = (seq + [b["frames"]] + [None] * n)[:n]
    b["flare"] = (states + [(0, 0)] * n)[:n]
    b.update(reflection=True, flare_size=size, flare_special=False,
             flare_heavy=[False] * n, flare_at=cbdraw.centre(ref),
             flare_rot=cbflare.hit_facing(cbdraw.centre(shooter),
                                          cbdraw.centre(ref),
                                          cbbeam.get_angle))
    return b
