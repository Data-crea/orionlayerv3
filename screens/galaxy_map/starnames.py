"""What the galaxy map's star names say and how they are coloured — work
order 402 (package 1), the rules `starnamedraw.star_label` used to approximate
with the star's single owner field.

No pygame here: every rule is a plain function a check can call.

`MAINSCR::Get_Star_Name_` (mainscr.cpp:1417-1486) reads the COLONIES of the
system, not only `star.owner`:

  TRANSCRIPTION `name_contact` (mainscr.cpp:1447-1456, harold.cpp:673-691):
                 without Galactic Lore a name is shown when the star's owner
                 is 0..7 AND any colony owner at the star is in contact with
                 the local player (`Contact_With_One_Colony_`); otherwise
                 only a VISITED star shows its name, in the neutral colour.
                 The local player is in contact with itself: DEVIATION
                 `self_contact`, see `_in_contact`.
  TRANSCRIPTION `name_outpost` (`Star_Is_Outpost_Star_`, harold.cpp:89-112;
                 mainscr.cpp:1462, :1484): a system with outposts and no
                 colony is written lower-case (`String_To_Lower_`) and its
                 colour is `Decrease_Font_Color_Range_` darker, by 1 step for
                 an owner's colour, by 2 for the neutral one (misc.cpp:125).
  TRANSCRIPTION `name_split` (`Print_Star_Name_To_Bitmap_`, mainscr.cpp:
                 1488-1535, `Colony_Owners_` harold.cpp:480-510): a system
                 with more than one colony owner prints its name split into
                 the owners' colours, in player order, each owner's share
                 `count x ceil(width / total)` of the name's width
                 (`Get_Bitmap_String_Range_`, misc.cpp:496-516); only owners
                 in contact count unless the player is omniscient. The
                 darkening of an outpost-only system is not carried into the
                 owners' colours (the swap takes the players' own).
  TRANSCRIPTION `name_lore` (mainscr.cpp:1469-1471): an omniscient player
                 sees the name of a foreign system it has not visited in
                 brackets.
  DEVIATION      `name_step_darker`: the original's colour is a palette ramp
                 and a "step" is one palette index; HD's colours are single
                 RGB values, so a step is `STEP_FACTOR` of the brightness.
                 UNVERIFIED: the factor is not measured against a native
                 screenshot (no live run, Data's decision of 20 October 2026).

THE HIGHLIGHT (`Highlight_Star_`, mainscr.cpp:1833-1842; `Print_Highlighted_
Star_Name_`, :1844-1872):

  TRANSCRIPTION `name_pulse_sequence`: the name of the pointed-at star, of
                 the ETA star and of the open system window's star is printed
                 again each frame with the colour offset
                 `selected_star_color_offset`, which steps 0, 1, 2, 3, 2, 1,
                 0, -1, 0, ... (it starts at 0, adds `..._mod` (+1) after
                 each print and turns at 3 and at -1, harold.cpp:1332).
  INVENTION      `name_pulse_pace`: the original steps once per drawn frame
                 and `pulse_level` steps by time instead; `PULSE_STEP_S`
                 is a guess at its frame pace. UNVERIFIED live.
  DEVIATION      `name_pulse_shade`: the offset is added to the palette
                 indices (neutral: offset x 9 / 5, a player's colour:
                 offset x 3 / 2); HD mixes the colour toward white by
                 `PULSE_MIX` per step, and below it by `PULSE_DIM` at -1.
  OMISSION       `eta_star_pulse`: the engine's `eta_star_id` is not on the
                 wire; the star the pointer is on stands in for it
                 (`screen._hover_star`, as `maplines.render_hover_preview`).
"""
from core.structs import colony as colony_struct
from core.structs import planet as planet_struct
from core.structs import player as player_struct
from core.structs import star as star_struct

MAX_PLAYERS = 8
#: DEVIATION `name_step_darker`: brightness kept per palette step.
STEP_FACTOR = 0.80
#: TRANSCRIPTION `name_pulse_sequence`: the offsets of one period.
PULSE_SEQUENCE = (0, 1, 2, 3, 2, 1, 0, -1)
#: INVENTION `name_pulse_pace`: seconds per step.
PULSE_STEP_S = 0.07
#: DEVIATION `name_pulse_shade`: mix toward white per positive step, and the
#: brightness kept at -1.
PULSE_MIX = 0.20
PULSE_DIM = 0.90


class Facts:
    """The colonies of one system: owner -> count, and the two kinds."""
    __slots__ = ("owners", "colonies", "outposts")

    def __init__(self):
        self.owners = {}
        self.colonies = 0
        self.outposts = 0


def build_facts(state):
    """{star index: Facts} for every system with a colony — read through
    `star.planet_index` -> `planet.colony_index` -> the colony, as the
    original does (harold.cpp:89-112). A record out of range is skipped."""
    planets = getattr(state, "planets_raw", None) or []
    colonies = getattr(state, "colonies_raw", None) or []
    out = {}
    for s in getattr(state, "stars", None) or []:
        fact = None
        for pi in star_struct.planet_indices(s):
            if not 0 <= pi < len(planets):
                continue
            raw = planets[pi]
            if len(raw) < planet_struct.SIZE:
                continue
            ci = int(planet_struct.parse(raw).colony_index)
            if not 0 <= ci < len(colonies):
                continue
            raw = colonies[ci]
            if len(raw) < colony_struct.SIZE:
                continue
            c = colony_struct.parse(raw)
            owner = int(c.owner)
            if owner < 0:
                continue
            if fact is None:
                fact = out[int(s.index)] = Facts()
            fact.owners[owner] = fact.owners.get(owner, 0) + 1
            if c.outpost_flag:
                fact.outposts += 1
            else:
                fact.colonies += 1
    return out


def facts_of(screen):
    """The screen's facts for its snapshot (None: no colony records),
    built once per snapshot (the three lists are replaced by every
    snapshot, so identity is the key, as `screen.update`'s `_parse_key`)."""
    state = getattr(screen, "_state", None)
    if state is None:
        return None
    key = (getattr(state, "planets_raw", None),
           getattr(state, "colonies_raw", None),
           getattr(state, "stars", None))
    seen = getattr(screen, "_star_facts", None)
    if seen is not None and all(a is b for a, b in zip(seen[0], key)):
        return seen[1]
    # None, not {}: a snapshot without colony records (an older engine, a
    # stand-in) says nothing about who holds what, and `spec` then reads
    # the star's own owner field as it did before work order 402.
    facts = build_facts(state) if key[0] and key[1] else None
    screen._star_facts = (key, facts)
    return facts


def outpost_star(fact):
    """`Star_Is_Outpost_Star_`: outposts and not one colony."""
    return fact is not None and fact.outposts > 0 and fact.colonies == 0


def ascii_lower(text):
    """`String_To_Lower_` (strings.cpp:40-50) maps only 0x41-0x5A, so a
    non-ASCII capital of a mod's or a translation's name stays as it is;
    `str.lower()` would lower it. TRANSCRIPTION `name_outpost`."""
    return "".join(chr(ord(c) + 32) if "A" <= c <= "Z" else c
                   for c in text)


def _in_contact(local, player_num, owner):
    """`Contact_With_Player_` (harold.cpp:665-670): `player[local].contact
    [owner]` for an owner below the player count. DEVIATION `self_contact`:
    the local player is in contact with itself here without reading the
    array (the original reads `contact[self]`, which is 1 in all 40 saves
    read on 16 November 2026), so a snapshot that leaves the own flag 0
    does not hide the player's own systems. UNVERIFIED for a fresh game."""
    if owner == player_num:
        return True
    if local is None or not 0 <= owner < MAX_PLAYERS:
        return False
    contact = player_struct.contacts(local)
    return owner < len(contact) and bool(contact[owner])


class Spec:
    """One name: its text, the player whose colour it takes (None = the
    neutral colour), how many palette steps darker, and the split."""
    __slots__ = ("text", "owner", "steps", "split")

    def __init__(self, text, owner, steps, split):
        self.text, self.owner, self.steps, self.split = (
            text, owner, steps, split)


def spec(s, player_num, players, omniscient, facts=None):
    """`Get_Star_Name_` for one star: a Spec, or None when the name stays
    hidden (a black hole has none; an unvisited system nobody in contact
    holds has none). `facts` None reads the star's own `owner` field only,
    the way HD did before work order 402 (no outposts, no split)."""
    if star_struct.is_black_hole(s):
        return None
    visited = star_struct.visited_by(s, player_num)
    owner = int(s.owner)
    local = players[player_num] if 0 <= player_num < len(players) else None
    fact = (facts or {}).get(int(s.index)) if facts is not None else None
    outpost = outpost_star(fact)
    name = s.name
    if not omniscient:
        if facts is None:
            contact = 0 <= owner < MAX_PLAYERS and _in_contact(
                local, player_num, owner)
        else:
            contact = 0 <= owner < MAX_PLAYERS and fact is not None and any(
                _in_contact(local, player_num, o) for o in fact.owners)
        if not contact:
            if not visited:
                return None
            # TRANSCRIPTION `name_outpost`: neutral colour, two steps
            return Spec(ascii_lower(name) if outpost else name, None,
                        2 if outpost else 0, None)
    text = f"({name})" if (omniscient and owner != player_num
                           and not visited) else name
    steps = 1 if outpost else 0
    if outpost:
        text = ascii_lower(text)
    colour = owner if 0 <= owner < MAX_PLAYERS else None
    split = None
    if fact is not None and len(fact.owners) > 1:
        split = colony_split(fact, player_num, local, omniscient)
    return Spec(text, colour, steps, split)


def owner_known(s, player_num, players, omniscient, facts=None):
    """True when the star's name is drawn in its OWNER's colour: the
    owner is met (or the player is omniscient). A visited star whose
    owners are all unmet has a name, in the neutral colour, and says
    nothing of who holds it (`Spec.owner` None), so the territory view
    must not credit `s.owner` for it (`terrfield.empires`)."""
    sp = spec(s, player_num, players, omniscient, facts)
    return sp is not None and sp.owner is not None


def colony_split(fact, player_num, local, omniscient):
    """`Colony_Owners_` with `have_contact = !omniscient`: [(owner, count)]
    in player order, or None when one owner or none is left
    (`Print_Star_Name_To_Bitmap_` returns false for <= 1)."""
    seen = []
    for owner in sorted(fact.owners):
        if not 0 <= owner < MAX_PLAYERS:
            continue
        if omniscient or _in_contact(local, player_num, owner):
            seen.append((owner, fact.owners[owner]))
    return seen if len(seen) > 1 else None


def spans(split, width):
    """[(owner, x0, x1)] of the name's width, `Get_Bitmap_String_Range_`:
    each share is `count x ceil(width / total)` and the running x advances
    by it, both ends held to the width."""
    total = sum(n for _o, n in split)
    each = ((width * 10) // total + 9) // 10
    out, x = [], 0
    for owner, n in split:
        w = min(n * each, width)
        out.append((owner, min(x, width), min(x + w, width)))
        x += w
    return out


def darker(rgb, steps):
    """DEVIATION `name_step_darker`."""
    k = STEP_FACTOR ** steps
    return tuple(int(c * k) for c in rgb[:3])


def pulse_level(now):
    """TRANSCRIPTION `name_pulse_sequence` at INVENTION `name_pulse_pace`:
    the colour offset (-1..3) at `now` seconds."""
    return PULSE_SEQUENCE[int(now / PULSE_STEP_S) % len(PULSE_SEQUENCE)]


def shade(rgb, level):
    """DEVIATION `name_pulse_shade`: the colour at pulse offset `level`."""
    if level > 0:
        m = min(1.0, PULSE_MIX * level)
        return tuple(int(c + (255 - c) * m) for c in rgb[:3])
    if level < 0:
        return tuple(int(c * PULSE_DIM) for c in rgb[:3])
    return tuple(rgb[:3])


def highlighted(screen):
    """Star indices whose names pulse, in the original's call order: the
    pointed-at star (`Highlight_Star_` of the ETA star, mainscr_main.cpp:
    :984-996; OMISSION `eta_star_pulse`) and then the open system window's
    star (:1019, `box_id == 0`). A list, not a set: each call steps
    `selected_star_color_offset` once (see `pulses_of`)."""
    out = []
    hov = getattr(screen, "_hover_star", None)
    if hov is not None:
        out.append(int(hov.index))
    sysw = getattr(getattr(screen, "_state", None), "system_window", None)
    star = sysw.get("star", -1) if isinstance(sysw, dict) else -1
    if isinstance(star, int) and star >= 0:
        out.append(int(star))
    return out


_clock = None


def set_clock(fn):
    """A test or the evidence tool drives the pulse's time (seconds), as
    `core.planetspin.set_clock` does for the spin; None restores the real
    one. Two renders of one picture must differ only by what a check
    changes."""
    global _clock
    _clock = fn


def now():
    """The pulse's time in seconds: the driven clock, else the real one."""
    import time
    return _clock() if _clock is not None else time.monotonic()


def pulses_of(screen, now):
    """{star index: colour offset} of every highlighted name at `now`
    seconds. TRANSCRIPTION `name_pulse_sequence`: the original's single
    `selected_star_color_offset` advances once per `Highlight_Star_` call
    (mainscr.cpp:1833-1842), so with two highlighted stars the second one
    is printed one step further along the sequence; a star named twice
    keeps its last print, as the original's later draw covers the earlier.
    INVENTION `name_pulse_pace`: the pace is by time per step, so two
    highlights do not make the cycle twice as fast as the original's per-
    frame stepping would."""
    base = int(now / PULSE_STEP_S)
    return {i: PULSE_SEQUENCE[(base + k) % len(PULSE_SEQUENCE)]
            for k, i in enumerate(highlighted(screen))}
