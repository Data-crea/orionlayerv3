"""What each race slot says — `Draw_Race_Text_`, `Init_Race_Display_Data_`
and `spy::Compute_Spy_Bonuses_` as data (racescrn.cpp:111-230, :283-336;
spy.cpp:8-81).

Every string is the original's, from the player's own extracted files:
BILLTEXT (`core/billtext`) and ESTRINGS (`core/estrings`). Where one is
missing the slot says less, never something of ours in its place.
"""
from dataclasses import dataclass, field

from core import leaderskills as ls
from core.structs import leader as leader_struct
from core.structs import player as player_struct

from . import racesgeom as geom

#: BILLTEXT ids (racescrn.cpp:688-705).
B_IGNORED, B_NO_CONTACT = 0x32, 0x33
B_SPY, B_AGENT = 0x34, 0x35
B_RESEARCH, B_TRADE, B_GIVING, B_RECEIVING = 0x39, 0x3A, 0x3B, 0x3C
#: `_treaty_labels`: ESTRINGS 0x275.. (estrings.cpp:91-97), six of them.
E_TREATY_FIRST, TREATY_LABELS = 0x275, 6
#: The FMTPARA placeholder `Decode_Text_Stat_` replaces (jim.cpp:280).
STAT_MARK = "é"

# spy.cpp:4-31 and the constants it names (orion2_consts.h).
GOV_ATTACK = (0, 0, 10, 15, -10, -10, 15, 15)
TECH_SPY = ((43, 10), (114, 10), (147, 10), (173, 10), (182, 5))
RESEARCHED = 3
TRAIT_GOVERNMENT, TRAIT_SPYING, TRAIT_TELEPATHIC = 0, 9, 25
SPY_MASTER, SPY_MASTER2 = 0x4000, 0x8000
TELEPATH, TELEPATH2 = 0x10000, 0x20000
TRAIT_WARLORD = 30


def clean(text):
    """A BILLTEXT string as HD prints it: FMTPARA's '^' (a line/centre
    mark, core/helpformat) dropped, the spaces kept."""
    return (text or "").replace("^", "").strip("\r")


@dataclass
class Slot:
    index: int                    # 0..6, the screen's slot
    player: int                   # the player shown there
    name: str = ""
    race: int = 0
    colour: int = 0
    active: bool = False          # in `Get_Active_Players_(0, 0)`
    contact: bool = True
    eliminated: bool = False
    lines: list = field(default_factory=list)    # the treaty paragraph
    relation: int = 0
    relation_word: str = ""
    ignored: bool = False
    spies: int = 0
    mission: int = 0              # 0 espionage, 1 sabotage, 2 hide


def _stat(text, value):
    return (text or "").replace(STAT_MARK, str(value))


def treaty_lines(me, other, index, words):
    """The paragraph `Draw_Race_Text_` builds (racescrn.cpp:148-213), as
    lines — its `\\r` separators."""
    lines = []
    t = int(me.treaty[index])
    if t > 0:
        label = words.estring(E_TREATY_FIRST + min(t, TREATY_LABELS - 1))
        if label:
            lines.append(label.upper())
    if me.research_treaty[index]:
        level = int(me.current_research_agreement_level[index])
        unit = "RP" if level >= 0 else "BC"    # language 0 (:164-186)
        lines.append(f"{words.billtext(B_RESEARCH) or ''}{level}{unit}")
    if me.trade_treaty[index]:
        level = int(me.current_trade_agreement_level[index])
        lines.append(f"{words.billtext(B_TRADE) or ''}{level}BC")
    mine = int(me.tribute_treaty[index])
    theirs = int(other.tribute_treaty[words.me])
    if mine:
        lines.append(_stat(words.billtext(B_GIVING), 5 if mine == 1 else 10))
    elif theirs:
        lines.append(_stat(words.billtext(B_RECEIVING),
                           5 if theirs == 1 else 10))
    lines = [clean(x) for x in lines if x]
    if not lines:
        label = words.estring(E_TREATY_FIRST)
        lines = [clean(label.upper())] if label else []
    return lines


def slots(view, words):
    """`[Slot]` for the shown players, in the screen's order."""
    players, me = view.players, view.me
    mine = players[me]
    omni = player_struct.has_omniscience(mine)
    met = player_struct.contacts(mine)
    out = []
    for i, p in enumerate(view.shown):
        other = players[p]
        s = Slot(index=i, player=p, name=other.name, race=int(other.race),
                 colour=int(other.color), active=p in view.active,
                 eliminated=bool(other.eliminated))
        s.contact = not (omni and not met[p])
        s.relation = int(mine.relations[p])
        s.relation_word = clean(words.billtext(
            geom.relation_word_id(s.relation)))
        s.ignored = bool(int(mine.ignoring) & (1 << p))
        s.spies = int(mine.spies[p]) & 0x3F
        s.mission = int(mine.spies[p]) >> 6
        if s.contact and not s.eliminated:
            s.lines = treaty_lines(mine, other, p, words)
        out.append(s)
    return out


def agents(view):
    """`Get_My_Agent_Number_` (bill.cpp:349-352): spies[me], bits 0-5."""
    return int(view.players[view.me].spies[view.me]) & 0x3F


def spy_bonuses(view, leaders_raw):
    """(defence, attack) — `Compute_Spy_Bonuses_` (spy.cpp:35-81). A
    leader at a space anomaly (`Leader_At_Anomaly_`, colcalc.cpp:1206)
    would not count; the event table is not on the wire, so HD counts
    every leader (OMISSION `anomaly_leaders`)."""
    me = view.players[view.me]
    traits = player_struct.traits(me)
    apps = list(me.tech_applications)
    tech = sum(v for app, v in TECH_SPY if apps[app] == RESEARCHED)
    base = tech + traits[TRAIT_SPYING] + traits[TRAIT_TELEPATHIC] * 10
    warlord = bool(traits[TRAIT_WARLORD]) if len(traits) > TRAIT_WARLORD \
        else False
    best_def = best_atk = 0
    recs = leader_struct.parse_all(leaders_raw) \
        if len(leaders_raw or []) == leader_struct.COUNT else []
    for i, rec in enumerate(recs):
        if int(rec.player_index) != view.me or not 0 <= int(rec.status) <= 2:
            continue
        level = ls.owned_level(rec, i, warlord)
        g = int(rec.general_skills)
        d = (level * 3 + 3 if g & SPY_MASTER2 else
             level * 2 + 2 if g & SPY_MASTER else 0)
        a = ((level + 1) * 3 if g & TELEPATH2 else
             (level + 1) * 2 if g & TELEPATH else 0)
        best_def, best_atk = max(best_def, d), max(best_atk, a)
    gov = traits[TRAIT_GOVERNMENT]
    attack = (GOV_ATTACK[gov] if 0 <= gov < len(GOV_ATTACK) else 0)
    return best_def + base, attack + best_atk + base


class Words:
    """BILLTEXT and ESTRINGS, each honest about its absence."""

    def __init__(self, billtext=None, estrings=None, me=0):
        self.b = billtext if getattr(billtext, "state", None) == "ok" \
            else None
        self.e = estrings if getattr(estrings, "state", None) == "ok" \
            else None
        self.me = me

    def billtext(self, i):
        return self.b.message(i) if self.b is not None else None

    def estring(self, i):
        return self.e.string(i) if self.e is not None else None
