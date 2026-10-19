"""What the ship scan SAYS — work order 290, before any pixel.

`CMBTDRW1::Combat_Draw_View_Ship_` (cmbtdrw1.cpp:3223-4007) draws one
unit's combat record. `build` turns the same record into the rows of HD's
scan view (`cbscanview` draws them) — ONE view since work order 298 (Data:
the Normal / Detailed switch of 290-297 is gone, Normal was a subset of
Detailed and every layout had to hold twice):

  TRANSCRIPTION `scan_contents`: everything the original prints is in the
             one view — the combat bonuses (:3439-3463), the crew word
             (:3465-3472), marines (:3474-3482), drive hits and parsecs a
             turn (:3505-3566), structure (:3568-3576), combat speed
             (:3601-3610), armour with the scan's own total (:3612-3647),
             computer hits (:3655-3757), the
             shield's name and hits (:3738-3758, its weakest arc shown as
             all four arcs), every weapon slot with a weapon — count, name,
             arc, ammunition, mods (:3801-3918) — and the special systems,
             a damaged one in the damage colour (:3939-3963). The game's
             words, where the player's KENTEXT.LBX has them
             (`core.kentext`, the scan's messages).
  DEVIATION `scan_computer_line` (Data, work order 301): the original's
             "^ +n beam attack" / "no bonus" line under the computer
             (cmbtdrw1.cpp:3593-3606) is not in the view; the computer's
             bonus stands as its line in Beam Attack's card (HD EXTENSION
             `scan_breakdown`), so it shows only under the pointer and only
             when the parts make the engine's sum.
  HD EXTENSION `scan_detailed` (Data, work order 290, for every unit, own
             and enemy, attacker and defender): the same record, finer —
             the four shield arcs, a weapon's original count and its hits,
             a special system's hits, the crew's experience. Laid out as
             Rocco asked (work order 294): the arcs without the weakest-arc
             and shield-name lines, a weapon slot as "count/original" and
             the HP of the weapon in front; and as Data decided from the
             analysis of 18 Oct 2026 (work order 297): combat speed as
             current / maximum
             (`max_speed`), a value's number coloured by THIS ship's
             systems behind it (`contributors`), the shield generator and
             its upgrades in the shields' head; COMBAT VALUES four values
             and nothing under them (Data, work order 301: the card shows
             every part, one sub-line under Beam Attack showed only the
             computer as if it were the only one). The original's scan shows
             any living unit's record to anyone (combat1.cpp:952, no owner
             test, `Tactical_Combat_View_Subject` cmbtdrw1.cpp:18-29),
             stores nothing and costs nothing; the computer reads every
             record anyway. Nothing here is knowledge the scan does not
             give.

Beside them: HD EXTENSION `scan_officer` — the officer aboard, his portrait,
level and the skills that act in a battle (the original's scan only greys
the fleet icon, :3313-3326); HD EXTENSION `scan_identity` — the hull class,
the owner and the design's date from the ship record. OMISSION
`scan_planet`: the planet's scan (unit 0) shows its record's values, not
the original's ground-defence structure line and the colony's shield
strength (v2 cmbtdrw1.cpp:3571-3593, :3762-3772; 1.60 :3442-3466,
:3609-3620). TRANSCRIPTION `scan_planet_hull`: the planet is no
satellite and no hull — no hull class under its name, no armour row
(`build`).

Nothing here imports pygame; the smoke suite reads it without a window.
"""
from core import leaderskills as ls
from core.structs import leader as leader_struct
from core.structs import player as player_struct
from core.structs import ship as ship_struct

#: `TECHDATA::_computers[i].bonus` (techdata.cpp:429-436).
COMPUTER_BONUS = (0, 25, 50, 75, 100, 125)
#: `TECHDATA::drives[i].warp_speed` (techdata.cpp:405-412; v2 :417-424).
DRIVE_WARP = (0, 2, 3, 4, 5, 6, 7)
#: `INITSHIP::Get_FTL_Speed_` (initship.cpp:252-266; v2 :430-444): the
#: trans-dimensional trait adds `td_ftl_bonus` (v2 initship_config.cpp:6);
#: an owner that is no player moves 1 with any drive — but the scan does
#: not ask it for such an owner (`ftl_speed`).
TRAIT_TRANS_DIMENSIONAL, TD_FTL_BONUS = 29, 2
MAX_PLAYERS = 8
#: `TECHDATA::weapons[i].type` 2 with `ammo` > 0 (techdata.cpp:516-518,
#: :537): the torpedoes' charge boxes in the scan (:3863-3887).
TORPEDO_AMMO = {18: 2, 19: 2, 20: 2, 40: 1}
#: `WEAPON_FIRING_ARC_*` as the scan's switch tests them (:3818-3838).
ARC_FORWARD, ARC_ALL = 0x01, 0x0F
#: The specials `Init_Internal_Space` gives no hits (cmbtfir2.cpp:668-672),
#: by the bits it tests — its comments name other systems; the enum
#: (orion2_consts.h:591-614) says Battle Pods 4, Extended Fuel Tanks 11,
#: Heavy Armor 14, Quantum Detonator 24, Reinforced Hull 27.
NO_HITS = frozenset((4, 11, 14, 24, 27))
#: `Init_Internal_Space` walks bits 0..38 (cmbtfir2.cpp:661); the SPECIALS
#: list stops below Regeneration (39) as the panel's (`cbpanel`).
INTERNAL_BITS, REGENERATION = 39, 39

#: The officer skills a battle reads (cmbtfir2.cpp:94-180, :475-485,
#: :1866-1910): `LEADER_SHIP_SKILL_*` (orion2_consts.h:272-289) and the
#: general `LEADER_GENERAL_SKILL_COMMANDO` (:283-284) — Engineer, Fighter
#: Pilot, Galactic Lore, Helmsman, Ordnance, Security, Weaponry, Commando,
#: each with its starred form. Navigator moves the fleet between stars, not
#: in a battle. As (skill_type, mask) of `leaderskills.SKILLS`.
COMBAT_SKILL_MASKS = {
    ls.SHIP_SPECIAL: 0x1 | 0x2 | 0x4 | 0x8 | 0x10 | 0x20 | 0x40 | 0x80 |
    0x400 | 0x800 | 0x1000 | 0x2000 | 0x4000 | 0x8000,
    ls.GENERAL: 0x4 | 0x8,
}

#: HD's states of a part (HD EXTENSION `scan_detailed`): the original only
#: tells a destroyed special system by its colour.
OK, DAMAGED, DESTROYED = "Operational", "Damaged", "Destroyed"


def combat_skill(sid):
    _i, mask, typ, *_r = ls.SKILLS[sid]
    return bool(COMBAT_SKILL_MASKS.get(typ, 0) & mask)


def strip(word):
    """A KENTEXT line as a table cell: the `^ ` bullet and a trailing
    colon go (the scan prints them in its own columns)."""
    if word is None:
        return None
    word = str(word)
    if word.startswith("^ "):
        word = word[2:]
    return word.rstrip().rstrip(":")


def c_printf(fmt, *values):
    """The scan's own one- and two-`%d` formats (`%+d` too)."""
    out, vals = [], list(values)
    i = 0
    while i < len(fmt):
        if fmt.startswith("%+d", i) and vals:
            out.append(f"{int(vals.pop(0)):+d}")
            i += 3
        elif fmt.startswith("%d", i) and vals:
            out.append(str(int(vals.pop(0))))
            i += 2
        else:
            out.append(fmt[i])
            i += 1
    return "".join(out)


def signed(value):
    """`Build_Signed_Bonus_String` (cmbtdrw1.cpp:3098-3104; v2 :3174-3180):
    "+n" above 0, "0" at 0 — the cards print their numbers the same way
    (`cbscancard.signed`)."""
    return f"+{int(value)}" if int(value) > 0 else str(int(value))


#: The scan's labels: `core.kentext.PANEL_MESSAGES` key -> OrionLayer's
#: English where the player's KENTEXT.LBX was not extracted —
#: DEVIATION `scan_words`. Bullets and colons go (`strip`).
LABELS = {"beam_attack": "Beam Attack", "beam_defense": "Beam Defense",
          "missile_evasion": "Missile Evasion", "marines": "Marines",
          "captured": "Captured", "drive": "Drive",
          "parsecs": " parsecs/turn", "structure": "Structure",
          "armor": "Armor", "computer": "Computer",
          "no_specials": "No Special Devices", "none": "None"}


def labels(words):
    out = {}
    for key, english in LABELS.items():
        w = words.ken_word(key, english)
        # a leading space is part of " parsecs/turn" (it follows a number)
        out[key] = w.rstrip().rstrip(":") if key == "parsecs" else strip(w)
    return out


def bit(flags, b):
    return bool(int(flags[b >> 3]) >> (b & 7) & 1)


def satellite(unit, index=None):
    """`Is_Combat_Satellite_` (combinit.h:19-24; v2 :115-121). Its
    `ship != combat_data` keeps unit 0, the planet, out: the planet has no
    ship record and no drive either, and read as a satellite it took hull
    class size + 4, past the hull table (audit 23, work order 305).
    `index`: the unit's place in the battle, else the `_index` `build_for`
    puts on it; the status box's rule (`cbstatus.satellite`) is asked
    only for the other units."""
    from .cbstatus import satellite as sat
    if (unit.get("_index") if index is None else index) == 0:
        return False
    return sat(unit)


def hull_class(unit):
    """`Combat_Satellite_Hull_Class_` (combinit.h:26-29; v2 :123-126) for
    a satellite, else the size."""
    size = int(unit["size_class"])
    return size + 4 if satellite(unit) else size


def armour_total(unit):
    """The scan's armour total (v2 cmbtdrw1.cpp:3619-3640; 1.60 :3483-3507
    picks the hull by owner and drive instead): the hull's armour scaled by
    the armour's ships bonus, tripled by Heavy Armor as the flag stands —
    damaged or not, unlike the status box (`cbstatus._View`)."""
    from core import monsterhull

    class View:
        size = hull_class(unit)
        armor_type = int(unit["armor_type"])
        special_device_flags = [int(f) for f in unit["special_device_flags"]]
    return monsterhull.armour(View)


def ftl_speed(unit, traits_of):
    """Parsecs a turn as the scan prints them, TRANSCRIPTION `scan_ftl_speed`
    (v2 cmbtdrw1.cpp:3548-3560; 1.60 :3430-3440 prints the drive's warp
    speed alone): 0 without a ship record or a drive, else the drive's warp
    speed, and only for an owner 0-7 the galaxy's own rule, Get_FTL_Speed
    (the trans-dimensional bonus). A monster or Antaran with a drive keeps
    the warp speed — Get_FTL_Speed's 1 for a non-player is never asked
    (audit 25, work order 305). `traits_of` (player) -> traits or None."""
    drive = int(unit["ftl_type"])
    if drive <= 0 or int(unit["ship_idx"]) < 0:
        return 0
    speed = DRIVE_WARP[drive] if drive < len(DRIVE_WARP) else 0
    owner = int(unit["owner"])
    if not 0 <= owner < MAX_PLAYERS:
        return speed
    traits = traits_of(owner)
    if traits is not None and traits[TRAIT_TRANS_DIMENSIONAL]:
        speed += TD_FTL_BONUS
    return speed


def weapon_hp(hits, per_unit):
    """A slot's hits as its weapons hold them: `Apply_Internal_Damage`
    takes a hit from ONE weapon at a time — the partial one,
    `hits % per_unit`, else a whole one (cmbtfir2.cpp:1300-1315) — so the
    slot is `hits // per_unit` whole weapons and at most one partial.
    (whole, partial or None, per_unit)."""
    hits, per = max(0, int(hits)), int(per_unit)
    if per <= 0:
        return 0, None, 0
    partial = hits % per
    return hits // per, partial or None, per


def weapon_hp_text(count, hits, per_unit):
    """The HP of the slot's weapon in front (Rocco's feedback, work order
    294): the partial one's "1/3", else a whole one's "3/3", "0/3" when
    none is left; "" without hits per weapon. The others are whole — a hit
    takes from one weapon at a time (`weapon_hp`)."""
    _whole, partial, per = weapon_hp(hits, per_unit)
    if per <= 0:
        return ""
    if count <= 0:
        return f"0/{per}"
    return f"{per if partial is None else partial}/{per}"


class Words:
    """The words of the scan: the game's (`core.kentext`, HESTRNGS) where
    the player's files have them, else OrionLayer's English — DEVIATION
    `scan_words` for those, through `core.lang` like every HD word."""

    def __init__(self, ken=None, names=None, estrings=None, hstrings=None,
                 unit="BC"):
        self.ken, self.names = ken, names
        self.e = estrings if getattr(estrings, "state", None) == "ok" \
            else None
        self.h = hstrings if getattr(hstrings, "state", None) == "ok" \
            else None
        self.unit = unit

    def ken_word(self, what, fallback):
        w = self.ken.panel_word(what) if self.ken is not None else None
        return w if w else fallback

    def part(self, table, index, fallback=None):
        n = self.names.name(table, index) if self.names is not None else None
        return n if n else fallback

    def estring(self, index):
        return self.e.string(index) if self.e is not None else None

    def hstring(self, index):
        return self.h.message(index) if self.h is not None else None


#: The scan's own KENTEXT lines (cmbtdrw1.cpp) and OrionLayer's English for
#: a missing file — `core.kentext.PANEL_MESSAGES` names the numbers.
CREW_KEYS = ("crew_green", "crew_regular", "crew_veteran", "crew_elite",
             "crew_ultra")
CREW_ENGLISH = ("Green Crew", "Regular Crew", "Veteran Crew", "Elite Crew",
                "Ultra Elite Crew")


def crew_word(words, quality):
    """`Copy_Crew_Quality_Without_Parenthetical` (cmbtdrw1.cpp:3182-3188):
    KENTEXT 31-35 cut at the "(".  Ultra Elite only from 4.

    DEVIATION `scan_crew_level_5` (work order 299, Data's P5 of 298): a
    level above the table's last row (`Calc_Ship_Level_` caps at 5 after
    the Warlord's +1, ericnet.cpp:217-236; `_crew_data` has rows 0-4,
    mox.cpp:780-786) has no word in the original — `Crew_Quality_String_`'s
    switch falls to its default and prints nothing (cmbtdrw1.cpp:3850-3851)
    — HD names the highest known level instead of an empty word. Open fix
    100 registers the level (an observation)."""
    q = int(quality)
    if q >= len(CREW_KEYS):
        q = len(CREW_KEYS) - 1
    if q < 0:
        return ""
    w = words.ken_word(CREW_KEYS[q], CREW_ENGLISH[q])
    return w.split("(")[0].rstrip()


def special_slots(unit, start_damage):
    """The special system each of the eight hit slots belongs to:
    `Init_Internal_Space` numbers the specials present and UNDAMAGED when
    the battle began, bits 0..38, eight at most (cmbtfir2.cpp:658-685).
    `start_damage` is the ship record's `special_device_damage_flags` (the
    battle copies them in, combinit.cpp:368-372; the record changes only
    after the battle); None for a unit with no record. The damage path
    counts every PRESENT bit instead (:1391-1394) — a ship that began with
    a damaged special loses the wrong one; the state shown is the flag's,
    the hits the slot's, both as the game holds them."""
    flags = unit["special_device_flags"]
    start = start_damage or [0] * 5
    out = []
    for b in range(INTERNAL_BITS):
        if len(out) >= 8:
            break
        if bit(flags, b) and not bit(start, b):
            out.append(b)
    return out


def special_rows(unit, start_damage, words=None):
    """[(bit, name, current hits or None, max hits or None, state)], the
    original's order (bits below Regeneration)."""
    slots = {b: k for k, b in enumerate(special_slots(unit, start_damage))}
    rows = []
    for b in range(REGENERATION):
        if not bit(unit["special_device_flags"], b):
            continue
        k = slots.get(b)
        cur = most = None
        if k is not None and b not in NO_HITS:
            cur = int(unit["special_hits"][k])
            most = int(unit["special_device_hits"][k])
        if bit(unit["special_device_damage_flags"], b):
            state = DESTROYED
        elif most is not None and cur < most:
            state = DAMAGED
        else:
            state = OK
        name = words.part("specials", b, f"special {b}") if words \
            is not None else f"special {b}"
        rows.append((b, name, cur, most, state))
    return rows


def ammo_cell(w, words):
    """The scan's ammunition column (cmbtdrw1.cpp:3846-3890), by type."""
    from .cbpanel import WEAPON_TYPE
    wid = int(w["weapon_id"])
    kind = WEAPON_TYPE[wid] if 0 <= wid < len(WEAPON_TYPE) else 0
    if kind == 0:
        return "-"
    if kind in (1, 3, 4):
        return str(int(w["ammo"]))
    if kind == 2 and TORPEDO_AMMO.get(wid, 0) > 0:
        if int(w["ammo"]) == 0:
            return strip(words.ken_word("ready", "Ready"))
        return f"{int(w['ammo'])} / {TORPEDO_AMMO[wid]}"
    return ""


def mods_cell(w, words):
    """The mods column (:3893-3912): each set bit's plural name, or KENTEXT
    0x1D ("None")."""
    bits = int(w["specials"])
    if bits == 0:
        return words.ken_word("none", "None")
    names = []
    for k in range(16):
        if bits >> k & 1:
            names.append(words.part("weapon_mod_plurals", k, f"mod {k}"))
    return ", ".join(names)


def arc_cell(w, words):
    """The arc word (v2 :3821-3845, 1.60 :3668-3693): F, Fx, B, Bx, 360 —
    the scan leaves it out for a forward mount; HD's column shows it for
    every mount. An arc with no word is "-", as an empty ammunition cell
    (work order 299, Data's P9 of 298): the original's switch adds no
    word for it (its default) and prints empty brackets, " ()"
    (1.60 :3668-3699). Seen on the Diablo test saves, whose
    Doom Star `battle_saves` gave firing arc 0 on purpose (work order 296,
    Data: Diablo never fires): combat copies the design's arc
    (combinit.cpp:303) and a weapon whose arc meets no sector never has a
    target in arc (cmbtfire.cpp:1246)."""
    arc = int(w["arc"])
    if arc == ARC_ALL:
        return "360"
    if words.ken is not None and arc in (1, 2, 4, 8):
        return words.ken.arc(arc) or "-"
    return {1: "F", 2: "Fx", 4: "Bx", 8: "B"}.get(arc, "-")


def weapon_rows(unit, words, unit_hits=None, hits_per_unit=None):
    """Every slot with a weapon (`weapon_id != 0`, :3805), as dicts."""
    rows = []
    unit_hits = unit_hits or unit.get("weapon_unit_hits") or [0] * 8
    hits_per = hits_per_unit or unit.get("weapon_hits_per_unit") or [0] * 8
    for k, w in enumerate(unit["weapons"]):
        wid = int(w["weapon_id"])
        if wid == 0:
            continue
        count = int(w["count"])
        per = int(unit_hits[k])
        whole = int(unit["weapon_total_hits"][k]) // per if per > 0 else count
        single = words.part("weapons", wid, f"weapon {wid}")
        name = single if count == 1 else \
            words.part("weapon_plurals", wid, single)
        hits = int(unit["weapon_hits"][k])
        _w, partial, _p = weapon_hp(hits, hits_per[k])
        if count <= 0:
            state = DESTROYED
        elif count < whole or partial is not None:
            state = DAMAGED
        else:
            state = OK
        hp = weapon_hp_text(count, hits, hits_per[k])
        rows.append({"slot": k, "id": wid, "count": count, "whole": whole,
                     "count_of": f"{max(0, count)}/{whole}",
                     "name": name, "arc": arc_cell(w, words),
                     "ammo": ammo_cell(w, words), "mods": mods_cell(w, words),
                     "hp": hp, "state": state,
                     "lost": max(0, whole - count)})
    return rows


def officer(unit, leaders_raw, words, warlord_of):
    """The officer aboard (HD EXTENSION `scan_officer`), or None: his
    record, name, title, level word and the skills a battle reads, each
    with the value the Leaders screen prints (`ldrrows.skill_value`)."""
    idx = int(unit["officer_idx"])
    if idx < 0 or leaders_raw is None or idx >= len(leaders_raw):
        return None
    rec = leader_struct.SPEC.parse(leaders_raw[idx])
    level = ls.shown_level(rec, idx, warlord_of)
    from screens.leaders.ldrrows import skill_value
    skills = []
    for sid in ls.displayed_skills(rec):
        if not combat_skill(sid):
            continue
        name = words.estring(ls.SKILL_NAME_ESTRINGS[sid]) or f"skill {sid}"
        skills.append((sid, name, skill_value(sid, level, words.unit)))
    return {"index": idx, "rec": rec, "name": str(rec.name),
            "title": str(rec.title), "level": level,
            "level_word": words.estring(ls.level_name_estring(rec, level)),
            "skills": skills}


class Model:
    """Everything one scan view shows, as words and numbers."""

    def __init__(self, **kw):
        self.__dict__.update(kw)


def build(unit, words, ship_rec=None, leaders_raw=None, players=None,
          num_players=0):
    """The scan of `unit` (a CMBT unit dict). `ship_rec` is its ship record
    (`ships_raw[ship_idx]` parsed) or None; `players` the player records
    parsed (traits, race name); `leaders_raw` the leader records."""

    def traits_of(p):
        if players is None or not 0 <= p < len(players):
            return None
        return player_struct.traits(players[p])

    def warlord_of(p):
        t = traits_of(p)
        return bool(t is not None and t[ls.TRAIT_WARLORD])

    owner = int(unit["owner"])
    # tactical combat keeps unit 0 for the colony (cmbtdrw1.cpp:23-26)
    planet = unit.get("_index") == 0
    owner_name = None
    if players is not None and 0 <= owner < min(num_players or 8,
                                                len(players)):
        owner_name = str(players[owner].race_name)
    hits = lambda cur, most: (int(unit[cur]), int(unit[most]))
    computer = int(unit["computer_type"])
    shield_most = int(unit["shield_arc_max"])
    armour = armour_total(unit)
    structure_left = int(unit["structure_max"]) - int(unit["structure_damage"])
    date = int(ship_rec.date_of_design) if ship_rec is not None else None
    specials = special_rows(unit, list(ship_rec.special_device_damage_flags)
                            if ship_rec is not None else None, words)
    parts = contributors(unit, specials)
    m = Model(
        name=str(unit["name"]), owner=owner, owner_name=owner_name,
        hull=None if planet else words.part("hulls", hull_class(unit)),
        design_date=f"{date // 10}.{date % 10}" if date else None,
        planet=planet, captured=int(unit["is_captured"]) == 1,
        attack=int(unit["tac_val_attack"]),
        defense=int(unit["tac_val_defense"]),
        evasion=int(unit["tac_val_evade"]),
        crew=crew_word(words, unit["crew_quality"]) if owner <= 9 else None,
        crew_quality=int(unit["crew_quality"]),
        experience=int(ship_rec.crew_experience) if ship_rec is not None
        else None,
        marines=None if planet or int(unit["marine_count"]) == 0xFF
        else int(unit["marine_count"]),
        drive=hits("drive_current_hits", "drive_max_hits")
        if int(unit["ftl_type"]) > 0 and int(unit["ship_idx"]) >= 0 else None,
        parsecs=ftl_speed(unit, traits_of),
        speed=(int(unit["current_speed"]), int(unit["combat_speed_base"])),
        speed_max=max_speed(unit, traits_of),
        value_states={k: worst([s for _n, s in v]) for k, v in parts.items()},
        shield_tags=[(n, s) for b, n, _c, _m, s in specials
                     if b in SHIELD_UPGRADES or
                     (b == DAMPER_FIELD and int(unit["shield_type"]) > 0)],
        damper=next(((n, s) for b, n, _c, _m, s in specials
                     if b == DAMPER_FIELD), None)
        if int(unit["shield_type"]) <= 0 else None,
        structure=(structure_left, int(unit["structure_max"])),
        # the planet's armour line is KENTEXT 0x14 under the ground
        # defence, no figure (v2 cmbtdrw1.cpp:3613-3618; 1.60 :3517-3523)
        armour=None if planet else (int(unit["armor_remaining"]), armour),
        armour_name=words.part("armor", int(unit["armor_type"])),
        computer=hits("computer_current_hits", "computer_max_hits"),
        computer_name=words.part("computers", computer),
        shield_name=words.part("shields", int(unit["shield_type"]))
        if 0 <= int(unit["shield_type"]) < 10 else None,
        shield_system=hits("shield_current_hits", "shield_max_hits")
        if int(unit["shield_type"]) > 0 else None,
        arcs=[int(v) for v in unit["shield_arc_current"]],
        shield_max=shield_most,
        weapons=weapon_rows(unit, words),
        specials=specials,
        words=labels(words),
        officer=officer(unit, leaders_raw, words, warlord_of),
        officer_mark=words.ken_word("officer", "(L)"),
        alive=int(unit["unit_status"]) == 0,
        cards=None,
    )
    m.hull_cards = hull_cards(unit, m, traits_of)
    return m


#: `Maximum_Combat_Speed_` (combat1.cpp:12-26): the design's speed, Augmented
#: Engines' bonus while the device is fitted (damaged or not: the flag
#: alone), Trans-Dimensional's for an owner that is a player. The bonuses
#: are the defaults (`_augmented_engines_speed_bonus`, design_config.h:34;
#: `_td_combat_speed_bonus`, combat1.h:8) — orion2re v2 lets a mod change
#: them, and HD does not see that.
AUGMENTED_ENGINES, AUGMENTED_SPEED = 2, 5
TD_COMBAT_SPEED = 4


def max_speed(unit, traits_of):
    speed = int(unit["combat_speed_base"]) & 0xFF
    if bit(unit["special_device_flags"], AUGMENTED_ENGINES):
        speed += AUGMENTED_SPEED
    owner = int(unit["owner"])
    traits = traits_of(owner) if 0 <= owner < MAX_PLAYERS else None
    if traits is not None and traits[TRAIT_TRANS_DIMENSIONAL]:
        speed += TD_COMBAT_SPEED
    return speed


def drive_speed(unit):
    """The speed the drive's hits scale (`Calc_Current_Speed`,
    combat1.cpp:1355-1386): the design's, Augmented Engines' bonus while
    they work — before the trans-dimensional bonus, tractors and a black
    hole."""
    speed = int(unit["combat_speed_base"]) & 0xFF
    if bit(unit["special_device_flags"], AUGMENTED_ENGINES) and \
            not bit(unit["special_device_damage_flags"], AUGMENTED_ENGINES):
        speed += AUGMENTED_SPEED
    return speed


def drive_zero(most, speed):
    """The most drive hits that still give speed 0 to an owner 0-9: the
    engine's whole-number `(hits - most/2) * speed / (most - most/2)`
    (combat1.cpp:1376-1379) is 0 below `most/2 + ceil(range / speed)`."""
    half, rng = most // 2, most - most // 2
    if speed <= 0 or rng <= 0:
        return most
    return half + -(-rng // speed) - 1


def hull_cards(unit, m, traits_of):
    """HD EXTENSION `scan_hull_cards` (Data, work order 302, P7 of 301):
    what damage to each HULL AND SYSTEMS row does, as the engine's rules
    say it (the texts of 301-report.md Q6, its numbers this unit's):
    {"structure" | "armor" | "drive" | "computer": (title, the row's
    "cur / max", [sentences])}. The planet's scan (unit 0) has none: its
    rows are the colony's, not a ship's (OMISSION `scan_planet`)."""
    if m.planet:
        return {}
    out = {}
    cur, most = m.structure
    out["structure"] = ("Structure", f"{cur} / {most}", [
        "The hull's own hit points; at 0 the ship is destroyed.",
        "Hit when the armor is gone or skipped: armor piercing (not "
        "against Heavy or Xentronium Armor), Achilles Targeting. A "
        "Graviton Beam adds damage here through the armor; a hit past a "
        "broken drive lands here too.",
        "The less structure is left, the likelier a hit goes inside to a "
        "system."])
    cur, most = m.armour
    out["armor"] = (m.armour_name or m.words["armor"],
                    f"{cur} / {most}" if most is not None else str(cur), [
        "Takes every hit first, before the structure or any system.",
        "Losing armor changes none of this ship's values.",
        "Skipped by armor piercing (not against Heavy or Xentronium Armor) "
        "and by Achilles Targeting; the Ion Pulse Cannon skips armor and "
        "structure and hits the systems."])
    if m.drive is not None:
        cur, most = m.drive
        speed = drive_speed(unit)
        owner = int(unit["owner"])
        player = owner <= 9         # the engine's own test (combat1.cpp:1376)
        if speed <= 0:
            first = "This design has no combat speed to lose."
        elif player:
            first = (f"Combat speed falls over the drive's upper half: "
                     f"{most} hits give the full {speed}, "
                     f"{drive_zero(most, speed)} hits or fewer give 0. "
                     f"Now {cur}: speed {m.speed[0]}.")
        else:
            # monsters: linear to 0 in whole numbers (:1381)
            first = (f"Combat speed falls with the drive's hits: {most} "
                     f"hits give the full {speed}, {(most - 1) // speed} "
                     f"or fewer give 0. Now {cur}: speed {m.speed[0]}.")
        traits = traits_of(owner) if 0 <= owner < MAX_PLAYERS else None
        lines = [first]
        if traits is not None and traits[TRAIT_TRANS_DIMENSIONAL]:
            lines.append(f"The trans-dimensional race adds "
                         f"{TD_COMBAT_SPEED} after that.")
        lines += [
            "At speed 0 the ship cannot retreat and can be boarded "
            "without transporters.",
            "Beam Defense +5 a point of speed, -20 at speed 0."]
        if player:
            # `Is_Combat_Ship_Dead` tests owner <= 9 (cmbtfire.cpp:320-323)
            lines.append("At 0 hits the drive explodes and destroys the "
                         "ship.")
        lines.append("The speed changes at once, the ship's moves from its "
                     "next turn, the combat values at the next round "
                     "(standard rules).")
        out["drive"] = (m.words["drive"], f"{cur} / {most}", lines)
    cur, most = m.computer
    ctype = int(unit["computer_type"])
    bonus = COMPUTER_BONUS[ctype] if 0 <= ctype < len(COMPUTER_BONUS) \
        else 0
    out["computer"] = (m.computer_name or m.words["computer"],
                       f"{cur} / {most}", [
        f"Gives its whole bonus, Beam Attack {signed(bonus)}, while one hit "
        f"is left; a damaged computer loses nothing.",
        "At 0 hits: no bonus, from the next round on (standard rules)."]
        if ctype > 0 else ["No computer: no beam attack bonus from one."])
    return out


def part_state(cur, most):
    if most and cur >= most:
        return OK
    return DAMAGED if cur > 0 else DESTROYED


#: The specials that give a combat value a bonus — which device is THIS
#: ship's contribution to which value (`Ship_Specials_Offensive_Bonus_`
#: cmbtfir2.cpp:222-230, `Ship_Specials_Defensive_Bonus_` :730-787; v2
#: names the cloak each 80 belongs to). Only the best jammer counts.
BATTLE_SCANNER, INERTIAL_NULLIFIER, INERTIAL_STABILIZER = 5, 17, 18
CLOAKING_DEVICE, PHASING_CLOAK, STEALTH_FIELD = 6, 23, 31
ECM_JAMMER, MULTI_WAVE_JAMMER, WIDE_AREA_JAMMER = 9, 21, 38
JAMMERS = ((WIDE_AREA_JAMMER, 130), (MULTI_WAVE_JAMMER, 100),
           (ECM_JAMMER, 70))
#: `special_status_flag` 1: cloaked — the cloak's beam defence counts only
#: then (:735; v2's phasing-cloak variant needs a config switch).
CLOAKED = 1


def contributors(unit, specials):
    """{value: [(name, state)]}: THIS ship's systems that give each combat
    value its bonus — what colours the value (Data, work order 297: a
    damaged one orange, a destroyed one red; another ship's never)."""
    by_bit = {b: (name, state) for b, name, _c, _m, state in specials}
    has = lambda b: b in by_bit
    out = {"attack": [], "defense": [], "evasion": [], "speed": []}
    if int(unit["computer_type"]) > 0:
        out["attack"].append(("computer", part_state(
            int(unit["computer_current_hits"]),
            int(unit["computer_max_hits"]))))
    if has(BATTLE_SCANNER):
        out["attack"].append(by_bit[BATTLE_SCANNER])
    for b in (INERTIAL_STABILIZER, INERTIAL_NULLIFIER):
        if has(b):
            out["defense"].append(by_bit[b])
            out["evasion"].append(by_bit[b])
    if int(unit.get("special_status_flag", 0)) == CLOAKED:
        for b in (CLOAKING_DEVICE, PHASING_CLOAK):
            if has(b):
                out["defense"].append(by_bit[b])
    jam = next((b for b, _v in JAMMERS if has(b)), None)
    if jam is not None:
        out["evasion"].append(by_bit[jam])
    if int(unit["ftl_type"]) > 0 and int(unit["drive_max_hits"]) > 0:
        drive = ("drive", part_state(int(unit["drive_current_hits"]),
                                     int(unit["drive_max_hits"])))
        out["speed"].append(drive)
        out["defense"].append(drive)       # its speed times 5 (:182-187)
    if has(AUGMENTED_ENGINES):
        out["speed"].append(by_bit[AUGMENTED_ENGINES])
        out["defense"].append(by_bit[AUGMENTED_ENGINES])
    return out


def worst(states):
    for s in (DESTROYED, DAMAGED):
        if s in states:
            return s
    return OK


#: The shield's upgrades ACGIFT asked for in the SHIELDS box (work order
#: 297), and the Damper Field that stands where a shield would.
SHIELD_UPGRADES = (13, 30, 20)          # Hard Shields, Shield Capacitor,
DAMPER_FIELD = 7                        # Multi-Phased Shields


def build_for(unit_index, shown, state, words, start=None):
    """`build` from the battle as drawn (`shown`) and the snapshot;
    `start`: the battle's units at the round's start
    (`cbscansources.Sources.round_start`), what the combat values' parts are
    counted from."""
    unit = dict(shown["units"][unit_index])
    unit["_index"] = unit_index
    ship_rec = None
    idx = int(unit["ship_idx"])
    ships = getattr(state, "ships_raw", None) or []
    if 0 <= idx < len(ships):
        ship_rec = ship_struct.SPEC.parse(ships[idx])
    players = [player_struct.SPEC.parse(raw)
               for raw in getattr(state, "player_raw", None) or []]
    leaders = getattr(state, "leaders_raw", None)
    m = build(unit, words, ship_rec, leaders, players,
              getattr(state, "num_players", 0))
    # the combat values' parts (HD EXTENSION `scan_breakdown`, work order
    # 297): from every unit of the battle as drawn, the players' traits
    # and the officers' records
    from . import cbscanparts
    m.cards = cbscanparts.breakdown(
        unit_index, shown["units"],
        [player_struct.traits(p) for p in players] if players else None,
        (lambda oi: leader_struct.SPEC.parse(leaders[oi])
         if 0 <= oi < len(leaders) else None) if leaders else None,
        int(shown.get("attacker", 0)), int(shown.get("defender", 0)),
        lambda b: words.part("specials", b, f"special {b}"),
        crew_word(words, unit["crew_quality"]), m.computer_name, start,
        m.owner_name)
    return m
