"""Where the Lightning Field fires in the battle's events — work orders 210
C3 and 305.

HD STATE `lightning_inferred`: no event names the field (proposed open fix
76), so HD puts its frames (`cbplay`, TRANSCRIPTION `lightning`) where the
original draws them. `Resolve_Missile` draws the field first, at a target
with a working one, BEFORE the target's point defence (`Final_Fire`) and
before the stack is checked (v2 cmbtmis.cpp:690-716): the field may leave
nothing to hit, and then the stack is killed (:757-759) with no hit event.
So the field goes

  before the point defence that answers a missile hit or a fighter pass
  (the target's beams and specials at that missile, v2 cmbtfir2.cpp:937-949),
  else right before the hit or pass; and

  before a stack's end at the unit it flies at, inside the unit's missile
  hit radius (`Did_Missile_Hit`, v2 cmbtmis.cpp:212-226; mox.cpp:611) with
  no hit or pass of it before — where the field or the point defence it
  draws first emptied it.

What HD cannot know: a stack emptied that way at a unit in the middle of a
move is tested against the unit's place before and after the snapshot.
"""
from . import cbdraw, cbsound

#: The Lightning Field's special bit (`SPECIAL_LIGHTNING_FIELD`).
LIGHTNING_FIELD = 19
#: `missile_hit_radius` by size class (mox.cpp:611)
HIT_RADIUS = (12, 20, 26, 28, 30, 30)
#: what lies between a field and the hit it answers: the target's point
#: defence at the missile, its aims, its sounds, the charges it takes
_PASS_OVER = ("beam_shot", "special", "beam_aim", "absorb")


def has_field(u):
    """`Does_Combat_Ship_Have_Special(u, SPECIAL_LIGHTNING_FIELD)`: the
    bit set and not damaged."""
    from . import cbpanel
    if u is None:
        return False
    have = cbpanel.special_bits(u.get("special_device_flags") or [0] * 5)
    hurt = cbpanel.special_bits(u.get("special_device_damage_flags") or
                                [0] * 5)
    return LIGHTNING_FIELD in have and LIGHTNING_FIELD not in hurt


def _defence(e, unit, missile):
    """`e` is `unit`'s point defence at `missile`, or what goes with it."""
    if e["kind"] in cbsound.KINDS or e["kind"] == "absorb":
        return True
    return e["kind"] in _PASS_OVER and e.get("source") == unit and \
        e.get("target") == missile and \
        (e["kind"] == "beam_aim" or e.get("at_missile"))


def _within(point, units, i):
    """`point` lies inside unit `i`'s missile hit radius, in any of the
    `units` lists (the states before and after)."""
    for us in units:
        u = us[i] if us and 0 <= i < len(us) else None
        if u is None:
            continue
        cx, cy = cbdraw.centre(u)
        r = HIT_RADIUS[max(0, min(5, int(u["size_class"])))]
        if (point[0] - cx) ** 2 + (point[1] - cy) ** 2 < r * r:
            return True
    return False


def targets_of(ordnance):
    """Missile index -> (the unit it flies at, whether no field can answer
    it: it flies at a missile, or home — fighters land before the field,
    v2 cmbtmis.cpp:673-679) in an ordnance block."""
    return {m["index"]: (m.get("target_unit_idx", -1), bool(
        m.get("is_anti_missile_rocket")) or m.get("target_unit_idx") ==
        m.get("source_unit_idx")) for m in (ordnance or {}).get(
            "missiles", [])}


def place(events, unit, targets, units=()):
    """`events` with a `lightning` event where the field fires. `unit(i)`:
    the shown unit; `targets`: `targets_of` the ordnance before these
    events; `units`: the unit lists to test a stack's end against."""
    targets = dict(targets)
    out, ended = [], set()
    for e in events:
        k = e["kind"]
        if k == "missile_launch":
            targets[e.get("missile")] = (e.get("target", -1), bool(
                e.get("anti_missile")) or e.get("target") == e.get("source"))
        at = None
        if k in ("missile_hit", "missile_merge"):
            # its end follows: the hit's or the merge's, not the field's
            ended.add(e.get("missile"))
        if k in ("missile_hit", "fighter_pass") and \
                not e.get("anti_missile"):
            at = e.get("target", -1)
        elif k == "missile_gone" and e.get("missile") not in ended:
            t, at_missile = targets.get(e.get("missile"), (-1, True))
            if not at_missile and _within((e.get("x", 0), e.get("y", 0)),
                                          units, t):
                at = t
        if at is not None and has_field(unit(at)):
            j = len(out)
            while j and _defence(out[j - 1], at, e.get("missile")):
                j -= 1
            # past the sounds before the point defence: they are the event
            # before's
            while j < len(out) and out[j]["kind"] not in ("beam_shot",
                                                          "special"):
                j += 1
            seq = out[j]["seq"] if j < len(out) else e["seq"]
            out.insert(j, {"kind": "lightning", "seq": seq - 0.5, "unit": at,
                           "serial": e.get("serial")})
        out.append(e)
    return out
