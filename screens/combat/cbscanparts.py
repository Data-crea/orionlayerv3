"""The combat values' parts — work order 297 part B (Data, 18 Oct 2026).

The engine sends each unit's three sums (`tac_val_attack`, `tac_val_defense`,
`tac_val_evade`) and its `current_speed`, never their parts.
HD EXTENSION `scan_breakdown`: the Detailed scan's card names the parts, computed here
the way the engine adds them, and shows them only when they add up to the
engine's own sum — otherwise the sum alone and "Breakdown not available",
never a part that might be wrong.

The engine OrionLayer runs is orion2re v2; the transcription follows it.
Line numbers are the 1.60 source's (`version_check.find_source_tree`) where
it agrees, and v2 is named where it does not:

  Beam Attack     `Offensive_Combat_Bonus_` (cmbtfir2.cpp:281-300): the
                  computer while it has a hit left (`Computer_Bonus_`
                  :209-215), the crew (`Crew_Attack_Bonus_` :217-220), the
                  race's ship attack, the Battle Scanner
                  (`Ship_Specials_Offensive_Bonus_` :222-230) and the fleet
                  (`Fleet_Offensive_Bonus_` :232-279): the best Weaponry
                  officer of the side's living units, a station's bonus,
                  against Antarans or monsters the best Galactic Lore and a
                  Scout Lab.
  Beam Defense    `Defensive_Combat_Bonus_(…, 0)` (:175-207): the crew,
  Missile Evasion the speed (5 a point, -20 at a standstill; none against
  (`…, 1`)        missiles, where the crew counts half), the race's ship
                  defence (ships only), the ship's devices
                  (`Ship_Specials_Defensive_Bonus_` :730-779; v2 names the
                  cloak behind each 80) and the fleet's best Helmsman (half
                  against missiles) with, against missiles, a Wide Area
                  Jammer anywhere in the side (`Fleet_Defensive_Bonus_`
                  :133-173) — of the ship's own jammer and that, only the
                  larger counts (:197-201).
  Combat speed    `Calc_Current_Speed_` (combat1.cpp:1193-1258; v2 stops a
                  unit with neither a ship record nor a drive).

The engine adds them up at the start of every combat round
(combinit.cpp:1053-1061: the round loop) — unless orion2re's
`interactive_combat_stats` is on, a 1.50 option, off by default. So the
parts are counted from the battle as it stood when the round began (HD
keeps that snapshot, `cbscanview.Sources.round_start`) and told against
the battle now: a system destroyed since still counts, "counts until end of
round", and so does a unit of the side that has fallen out since. Nothing
is guessed: without the round's start the parts are counted from now and
shown only when they make the sum exactly. The bonuses are orion2re's
defaults; a mod that changes one makes the sum differ, and the card says
the breakdown is not available.

Nothing here imports pygame; the smoke suite reads it without a window.
"""
from core import leaderskills as ls

from . import cbscan

MAX_PLAYERS = 8
#: `_crew_data` (mox.cpp:780-786): attack, defence by crew level.
CREW_ATTACK = (0, 15, 30, 50, 75)
CREW_DEFENCE = (0, 15, 30, 50, 75)
TRAIT_SHIP_DEFENSE, TRAIT_SHIP_ATTACK, TRAIT_WARLORD = 6, 7, 30
#: The fixed bonuses as the 1.60 source writes them and v2's defaults
#: (`combat_bonus`, `missile_defense`).
BATTLE_SCANNER_BONUS = 50
STATION_BONUS = (0, 10, 20)         # star base, battlestation, star fortress
HULL_STAR_BASE = 6
SCOUT_LAB, SCOUT_LAB_BONUS = 28, 20
STABILIZER_BEAM, STABILIZER_MISSILE = 50, 25
NULLIFIER_BEAM, NULLIFIER_MISSILE = 100, 50
#: v2: while cloaked, the best of the cloaks fitted (stealth field 0);
#: against missiles `cloaking_device_missile_defense`, 0.
CLOAK_BEAM = ((cbscan.STEALTH_FIELD, 0), (cbscan.CLOAKING_DEVICE, 80),
              (cbscan.PHASING_CLOAK, 80))
CLOAK_MISSILE = 0
FLEET_WIDE_AREA_JAMMER = 70
#: `LEADER_SHIP_SKILL_*` (orion2_consts.h:272-289): plain, starred.
WEAPONRY, HELMSMAN, GALACTIC_LORE = (0x4000, 0x8000), (0x40, 0x80), \
    (0x10, 0x20)
#: `_tractors_to_stop` (combat1.h:11): how many tractor beams stop a size.
TRACTORS_TO_STOP = (1, 2, 3, 4, 5, 6)
TRACTOR_BEAM = 39

SYSTEM, BASE, FLEET, FORMULA = "system", "base", "fleet", "formula"


def cdiv(a, b):
    """C's integer division: toward zero."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


class Part:
    """One line of a card: what, how much, whose. `value` None is a
    formula line (combat speed); `sources` the grey sub-line of a Base;
    `bit` the special system (or "computer") a SYSTEM line is, `src` the
    unit a FLEET line comes from."""

    def __init__(self, kind, label, value, state=cbscan.OK, sources=(),
                 note=None, bit=None, src=None):
        self.kind, self.label, self.value = kind, label, value
        self.state, self.sources, self.note = state, list(sources), note
        self.bit, self.src = bit, src

    def __repr__(self):
        return f"Part({self.kind}, {self.label!r}, {self.value}, {self.state})"


class Card:
    """A value's card: its parts and the engine's own sum; `ok` False when
    the parts do not make the sum (then only the sum is shown)."""

    def __init__(self, key, total, parts, ok):
        self.key, self.total, self.parts, self.ok = key, total, parts, ok


def officer_bonus(rec, skill, level):
    """`Weaponry_Bonus_`, `Helmsman_Bonus_`, `Galactic_Lore_Bonus_`
    (cmbtfir2.cpp:21-110): the plain skill first, then the starred."""
    plain, star = skill
    bits = int(rec.special_skills)
    if bits & plain:
        return (level + 1) * 5
    if bits & star:
        return cdiv((level * 3 + 3) * 5, 2)
    return 0


def officer_level(rec, idx, traits_of):
    """`Owned_Officer_Level_` (officer.cpp:82-103): every officer in a
    battle is counted at its owner's level, WARLORD included."""
    t = traits_of(int(rec.player_index))
    return ls.owned_level(rec, idx, bool(t is not None and t[TRAIT_WARLORD]))


def station_bonus(tier):
    """v2's choice (`Fleet_Offensive_Bonus`): tier 0 a star base, 1 a
    battlestation, anything else a star fortress."""
    return STATION_BONUS[0 if tier == 0 else 1 if tier == 1 else 2]


class Side:
    """What a side's living units give every one of them (the fleet
    bonuses): the best officer per skill with the unit it sits on, the
    station, the Scout Lab, a Wide Area Jammer. `known` False when an
    officer's record is not in the snapshot."""

    def __init__(self, owner, units, leader, traits_of, ancient):
        self.best, self.known = {}, True
        self.station = self.lab = self.jammer = None
        for i, u in enumerate(units):
            if int(u["owner"]) != owner or int(u["is_captured"]) != 0 or \
                    int(u["unit_status"]) != 0:
                continue
            still = stasis(u)
            if i and cbscan.satellite(u) and not still:
                self.station = (i, station_bonus(
                    cbscan.hull_class(u) - HULL_STAR_BASE))   # the last
            oi = int(u["officer_idx"])
            if oi > -1:
                rec = leader(oi) if leader is not None else None
                if rec is None:
                    self.known = False
                    continue
                level = officer_level(rec, oi, traits_of)
                for key, skill in (("weaponry", WEAPONRY),
                                   ("helmsman", HELMSMAN),
                                   ("lore", GALACTIC_LORE)):
                    if key == "lore" and not ancient:
                        continue
                    b = officer_bonus(rec, skill, level)
                    if b > self.best.get(key, (0,))[0]:
                        self.best[key] = (b, i, oi, rec)
            if ancient and not still and has(u, SCOUT_LAB):
                self.lab = (i, SCOUT_LAB_BONUS)
            if not still and has(u, cbscan.WIDE_AREA_JAMMER):
                self.jammer = (i, FLEET_WIDE_AREA_JAMMER)


def ref(u, field):
    """The unit a unit-index field names, or None (`cbdraw.unit_ref`: v2
    widened the field, "none" is the all-ones value of its width)."""
    from .cbdraw import unit_ref
    return unit_ref(u, field)


def stasis(u):
    return ref(u, "stasis_source_idx") is not None


def functional(u):
    """`Combat_Ship_Is_Functional`: alive, not captured, not held."""
    return int(u["unit_status"]) == 0 and int(u["is_captured"]) == 0 and \
        not stasis(u)


def fitted(u, b):
    return cbscan.bit(u["special_device_flags"], b)


def has(u, b):
    """`Does_Combat_Ship_Have_Special_`: fitted and not destroyed."""
    return fitted(u, b) and not cbscan.bit(u["special_device_damage_flags"],
                                           b)


def device(u, b, value, names):
    """A device of this ship as a part: its bonus if it worked."""
    return Part(SYSTEM, names(b), value if has(u, b) else 0, bit=b)


def breakdown(index, units, players, leader, attacker, defender, names,
              crew_word, computer_name=None, start=None):
    """{"attack", "defense", "evasion", "speed": Card} for unit `index`, or
    None when the side's records are not there. `players`: each player's
    traits; `leader(i)`: leader i's record (special_skills, xp,
    player_index, name) or None. `start`: the battle's units as they stood
    at the round's start — what the engine added up (the round loop,
    combinit.cpp:1053-1061); the parts are counted from it, the notes from
    `units` (now). Without it the parts are counted from now, and only a
    sum the parts make exactly is shown: nothing is guessed."""
    if start is None or len(start) != len(units):
        start = units
    u = start[index]
    owner = int(u["owner"])
    if players is None:
        return None

    def traits_of(p):
        return players[p] if 0 <= p < len(players) else None

    ancient = attacker > MAX_PLAYERS or defender > MAX_PLAYERS
    side = Side(owner, start, leader, traits_of, ancient)
    if not side.known:
        return None
    traits = traits_of(owner) if owner < MAX_PLAYERS else None
    q = max(0, min(4, int(u["crew_quality"])))
    crew = crew_word or cbscan.CREW_ENGLISH[q]
    now = units[index]

    def base(value_parts):
        """The fixed bonuses as one line, its sources under it."""
        src = [(lab, v) for lab, v in value_parts if v]
        return Part(BASE, "Base", sum(v for _l, v in value_parts),
                    sources=src)

    def fleet_officer(key, label, value=None):
        best = side.best.get(key)
        if best is None:
            return None
        b, i, oi, rec = best
        b = b if value is None else value(b)
        who = f"{label} ({str(rec.name)})"
        if i == index:
            return who, b
        return Part(FLEET, f"Fleet: {who} aboard {units[i]['name']}", b,
                    src=i)

    def take(got, parts, fixed):
        if isinstance(got, Part):
            parts.append(got)
        elif got:
            fixed.append(got)

    # ── Beam Attack ─────────────────────────────────────────
    parts, fixed = [], [(crew, CREW_ATTACK[q])]
    if traits is not None:
        fixed.append(("Race", int(traits[TRAIT_SHIP_ATTACK])))
    ctype = int(u["computer_type"])
    if ctype > 0:
        full = cbscan.COMPUTER_BONUS[ctype] if ctype < len(
            cbscan.COMPUTER_BONUS) else 0
        parts.append(Part(SYSTEM, computer_name or "Computer",
                          full if int(u["computer_current_hits"]) >= 1 else 0,
                          bit="computer"))
    if fitted(u, cbscan.BATTLE_SCANNER):
        parts.append(device(u, cbscan.BATTLE_SCANNER, BATTLE_SCANNER_BONUS,
                            names))
    for key, label in (("weaponry", "Weaponry"), ("lore", "Galactic Lore")):
        take(fleet_officer(key, label), parts, fixed)
    if side.station is not None:
        i, b = side.station
        take(("Station", b) if i == index else
             Part(FLEET, f"Fleet: station {units[i]['name']}", b, src=i),
             parts, fixed)
    if side.lab is not None:
        i, b = side.lab
        label = names(SCOUT_LAB)
        parts.append(Part(SYSTEM, label, b, bit=SCOUT_LAB) if i == index
                     else Part(FLEET, f"Fleet: {label} aboard "
                               f"{units[i]['name']}", b, src=i))
    cards = {"attack": settle("attack", int(now["tac_val_attack"]),
                              [base(fixed)] + parts, now, units)}

    # ── Beam Defense and Missile Evasion ───────────────────
    cloaked = int(u.get("special_status_flag", 0)) == cbscan.CLOAKED
    for key, missiles in (("defense", False), ("evasion", True)):
        parts = []
        crew_v = CREW_DEFENCE[q] // 2 if missiles else CREW_DEFENCE[q]
        fixed = [(crew, crew_v)]
        if traits is not None and int(u["ship_idx"]) != -1:
            fixed.append(("Race", int(traits[TRAIT_SHIP_DEFENSE])))
        if not missiles:
            parts.append(speed_part(int(u["current_speed"])))
            if cloaked:
                # v2: the stealth field first, a cloak only when it gives
                # more (:822-831) — at 80 and 80 the Cloaking Device
                best = None
                for b, v in CLOAK_BEAM:
                    if has(u, b) and (best is None or v > best[1]):
                        best = (b, v)
                if best is not None and best[1]:
                    parts.append(device(u, best[0], best[1], names))
        own_jam = jam = None
        if missiles:
            jam = next(((b, v) for b, v in cbscan.JAMMERS if has(u, b)), None)
            own_jam = jam[1] if jam else 0
        for b, beam, missile in ((cbscan.INERTIAL_NULLIFIER, NULLIFIER_BEAM,
                                  NULLIFIER_MISSILE),
                                 (cbscan.INERTIAL_STABILIZER,
                                  STABILIZER_BEAM, STABILIZER_MISSILE)):
            if fitted(u, b):
                parts.append(device(u, b, missile if missiles else beam,
                                    names))
        take(fleet_officer("helmsman", "Helmsman",
                           (lambda b: b // 2) if missiles else None),
             parts, fixed)
        if missiles:
            fleet_jam = side.jammer[1] if side.jammer else 0
            # of the ship's own jammer and the side's, the larger (:197-201)
            if fleet_jam > own_jam:
                i = side.jammer[0]
                label = names(cbscan.WIDE_AREA_JAMMER)
                parts.append(Part(SYSTEM, label, fleet_jam,
                                  bit=cbscan.WIDE_AREA_JAMMER) if i == index
                             else Part(FLEET, f"Fleet: {label} aboard "
                                       f"{units[i]['name']}", fleet_jam,
                                       src=i))
            elif jam is not None:
                parts.append(device(u, jam[0], jam[1], names))
            for b, _v in cbscan.JAMMERS:
                if fitted(u, b) and not has(u, b):
                    parts.append(Part(SYSTEM, names(b), 0, bit=b))
        total = int(now["tac_val_evade" if missiles else "tac_val_defense"])
        cards[key] = settle(key, total, [base(fixed)] + parts, now, units)
    cards["speed"] = speed_card(index, units, traits_of, names)
    return cards


def speed_part(speed):
    if speed == 0:
        return Part(FORMULA, "Combat speed 0, at a standstill", -20)
    return Part(FORMULA, f"Combat speed {speed} × 5", speed * 5)


def settle(key, total, parts, now, units):
    """The card: the parts as counted, checked against the engine's sum,
    then told against the unit as it stands now — a system that gave its
    bonus and is destroyed since counts until the round's end, so does
    another unit that has fallen out since, and a speed that has changed."""
    if sum(p.value for p in parts) != total:
        return Card(key, total, parts, False)
    rows = {b: st for b, _n, _c, _m, st in cbscan.special_rows(now, None)}
    for p in parts:
        if p.kind == SYSTEM and p.bit is not None:
            if p.bit == "computer":
                cur = int(now["computer_current_hits"])
                p.state = cbscan.part_state(cur, int(now["computer_max_hits"]))
                works = cur >= 1
            else:
                p.state = rows.get(p.bit, cbscan.OK)
                works = has(now, p.bit)
            if p.value and not works:
                p.state, p.note = cbscan.DESTROYED, "counts until end of round"
        elif p.kind == FLEET and p.src is not None and \
                not functional(units[p.src]):
            p.note = "counts until end of round"
        elif p.kind == FORMULA and p.value is not None and \
                speed_part(int(now["current_speed"])).value != p.value:
            p.note = f"at the round's start; now {int(now['current_speed'])}"
    shown = [p for p in parts if p.value or p.kind == BASE and p.sources or
             (p.kind == SYSTEM and p.state != cbscan.OK)]
    return Card(key, total, shown, True)


def speed_card(index, units, traits_of, names):
    """Combat speed as its formula (`Calc_Current_Speed_`), checked against
    the engine's `current_speed`."""
    u = units[index]
    cur = int(u["current_speed"])
    lines = []
    if (int(u["ship_idx"]) < 0 and int(u["ftl_type"]) == 0) or \
            ref(u, "black_hole_source_idx") is not None:
        why = "no drive" if int(u["ftl_type"]) == 0 else "held by a black hole"
        lines.append(Part(FORMULA, f"Speed 0: {why}", 0))
        return Card("speed", cur, lines, cur == 0)
    base = int(u["combat_speed_base"]) & 0xFF
    lines.append(Part(FORMULA, "Design speed", base))
    speed = base
    if fitted(u, cbscan.AUGMENTED_ENGINES):
        ok = has(u, cbscan.AUGMENTED_ENGINES)
        lines.append(Part(SYSTEM, names(cbscan.AUGMENTED_ENGINES),
                          cbscan.AUGMENTED_SPEED if ok else 0,
                          cbscan.OK if ok else cbscan.DESTROYED))
        speed += cbscan.AUGMENTED_SPEED if ok else 0
    owner = int(u["owner"])
    hits, most = int(u["drive_current_hits"]), int(u["drive_max_hits"])
    if int(u["ftl_type"]) == 0:
        top = 0
    elif most <= 0:
        top = 0
    elif owner <= 9:
        half = most // 2
        top = cdiv((hits - half) * speed, most - half)
    else:
        top = cdiv(hits * speed, most)
    top = max(0, top)
    if top != speed:
        lines.append(Part(SYSTEM, f"Drive {hits} / {most} hits", None,
                          cbscan.part_state(hits, most),
                          note=f"{speed} → {top}"))
    speed = top
    t = traits_of(owner) if owner < MAX_PLAYERS else None
    if t is not None and t[cbscan.TRAIT_TRANS_DIMENSIONAL]:
        lines.append(Part(FORMULA, "Trans-Dimensional",
                          cbscan.TD_COMBAT_SPEED))
        speed += cbscan.TD_COMBAT_SPEED
    if speed > 0:
        beams = 0
        for i, v in enumerate(units):
            if ref(v, "special_cooldown") == index and \
                    int(v["unit_status"]) == 0 and \
                    int(v["is_captured"]) == 0 and not stasis(v):
                beams += sum(int(w["count"]) & 0xFF for w in v["weapons"]
                             if int(w["weapon_id"]) == TRACTOR_BEAM)
        if beams:
            size = int(u["size_class"])
            stop = TRACTORS_TO_STOP[size] if 0 <= size < len(
                TRACTORS_TO_STOP) else size + 1
            after = 0 if stop <= 0 or beams >= stop else \
                max(1, speed - (speed * beams) // stop)
            lines.append(Part(FLEET, f"Tractor beams {beams} of {stop}",
                              after - speed))
            speed = after
    return Card("speed", cur, lines, speed == cur)
