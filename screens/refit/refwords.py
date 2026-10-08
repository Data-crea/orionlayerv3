"""What Refit says, as data — work order 223.

The paragraph the original prints for the ship under its pointer and for a
design (`Build_Ship_Info_Formatted_Paragraph_` and
`Build_Ship_Design_Info_Formatted_Paragraph_`, colbldg.cpp:1217-1336):
the name line, Cost / Shield / Computer / Armor / Ftl, the weapons and the
specials two to a line — every word the game's (ESTRINGS formats, the ship
part names the designer reads, HESTRNGS for the crew), every number the
record's.

TRANSCRIPTION   the lines, their order, the pairs (E_Strings 87 / 88 and
                89 / 90 alternate, :1244-1301)
OMISSION        `weapon_mods`: a weapon's modification words
                (`Build_Weapon_String_`'s prefixes and postfixes,
                colbldg.cpp:2301-2340) are not printed — the name and the
                count are; the widths the original measures to put a long
                item on its own line are HD's wrap
"""
from core.structs import leader as leader_struct
from core.structs import player as player_struct
from core.structs import ship as ship_struct

from . import refgeom as geom

#: The two codes the formats carry — the paragraph's alignment and its
#: column switch — become a split point; HD draws label and value.
SPLIT = "\x00"


def _fmt(fmt, *values):
    try:
        return (fmt or "") % values
    except (TypeError, ValueError):
        return fmt or ""


def _pair(fmt, value):
    """'%sCost to build: %s%d\\n' -> ('Cost to build:', '82')."""
    text = _fmt(fmt, "", SPLIT, value).strip("\n")
    label, _, rest = text.partition(SPLIT)
    return label.strip(), rest.strip()


def _items(fmt_a, fmt_b, values):
    """Items two to a line, as the formats alternate (87/88, 89/90)."""
    rows, line = [], []
    for v in values:
        line.append(v)
        if len(line) == 2:
            rows.append(tuple(line))
            line = []
    if line:
        rows.append(tuple(line))
    return rows


def design_lines(view, e, names):
    """The design part: [(label, value) or ('', text) or (head,)]."""
    out = [_pair(e(geom.E_COST), int(view.cost)),
           _pair(e(geom.E_SHIELD), names.name("shields", int(view.shield_type)) or ""),
           _pair(e(geom.E_COMPUTER), names.name("computers", int(view.computer_type)) or ""),
           _pair(e(geom.E_ARMOR), names.name("armor", int(view.armor_type)) or ""),
           _pair(e(geom.E_FTL), names.name("drives", int(view.ftl_type)) or "")]
    weapons = []
    for w in ship_struct.weapons(view):
        table = "weapon_plurals" if int(w.count) > 1 else "weapons"
        name = names.name(table, int(w.type)) or names.name("weapons", int(w.type)) or ""
        weapons.append(f"{int(w.count)} {name}")
    out.append((_fmt(e(geom.E_WEAPONS), "").strip(),))
    out += _items(None, None, weapons)
    specials = [names.name("specials", b) or "" for b in
                ship_struct.special_bits(view)]
    if specials:
        out.append((_fmt(e(geom.E_SPECIALS), "").strip(),))
        out += _items(None, None, specials)
    return out


def ship_lines(view, ship_index, state, e, h, names):
    """The ship's paragraph: its name and crew (and officer), then its
    design (colbldg.cpp:1309-1336)."""
    crew = h(geom.H_CREW + int(getattr(view, "crew_quality", 0) or 0)) or ""
    officer = int(getattr(view, "officer_index", -1))
    leaders = getattr(state, "leaders_raw", None) or []
    if 0 <= officer < len(leaders):
        lead = leader_struct.parse(leaders[officer]).name
        head = f"{view.name} : {lead} - {crew}"
    else:
        head = f"{view.name} : {crew}"
    return [("", head)] + design_lines(view, e, names)


def design_view(player, k):
    """Design slot k of a player as a ship view (a design IS the record's
    first 99 bytes, `s_ship_design`)."""
    o = player_struct.SHIP_DESIGNS_OFFSET + player_struct.DESIGN_SIZE * k
    raw = bytes(player.raw[o:o + player_struct.DESIGN_SIZE])
    return ship_struct.parse(raw + bytes(ship_struct.SIZE - len(raw)))
