"""The ship detail view outside a battle on the wire — open fix 106, "SHPV" (work order 317).

    81      synthetic screen id (`core.screen_names`): reported while
            `CMBTDRW1::Detailed_View_Ship` (cmbtdrw1.cpp:227) runs OUTSIDE a
            battle; in a battle the same view stays 66 with CPOP.
    "SHPV"  written after CPOP's place, only while 81 is reported. A version
            byte (1); int16 the ship (`ship_idx`), the view's subject
            (`combat_view_subject`, cmbtdrw1.cpp:7-14, :243-249), the name
            field (-1 when the name is not editable) and the exit field;
            uint8 n and n bytes of the name in the view's own buffer (at
            most 15: what the field last committed — Enter, or a click on
            another field, fields.cpp:1038-1053, :1068-1081, :1304-1321;
            the keys typed since are TXTF's, open fix 88); int16 the
            record's size, then
            `MOX::global_combat_data` exactly as CMBT sends a unit (the
            struct without its picture pointer: 309 bytes on orion2re 1.60,
            314 on v2) — read by CMBT's own parser (`combatblocks.unit`),
            never a second one.

WHY: the view draws only from the DERIVED record `Load_Display_Combat_Ship`
and `Get_Ship_Combat_Bonuses` build (cmbtdrw1.cpp:250-256; combinit.cpp:242-
400): bonuses, maximum hits, speed, ammunition, crew and marines, none of
which the ship record on the wire carries. Without the fix the view runs
under its caller's id (0, 4, 29) with its three fields alone in the list —
`bare` recognises that, and the screen's F12 notice names it.

Read WHOLE or left None (`core/colonyblocks.py`'s rule): an engine without
the fix writes none. A block whose head and declared size are there but
which is refused (another version, a name over 15, another record size) is
stepped over, so the blocks after it (TXTF among them) are still read; only
a truncated block leaves the position where it was.
"""
import struct as _st

from core import combatblocks, lang
from core.blockreader import Reader
from core.structs import combat as combat_struct

#: The synthetic id the view reports outside a battle (open fix 106).
SCREEN_ID = 81
#: The callers' ids (mainscr.cpp:3641, flt1.cpp:633, officer.cpp:1175).
CALLERS = (0, 4, 29)
HEAD = "<Bhhhh"
HEAD_SIZE = _st.calcsize(HEAD)
#: `Combat_View_Subject` (cmbtdrw1.cpp:7-14): the three a view outside a
#: battle can have (:243-249) — 0 a combat ship, 1 a non-combat ship (a
#: lander), 2 any ship under strategic combat.
SUBJECTS = {0: "ship", 1: "lander", 2: "strategic_combat_ship"}

#: The view's fields (cmbtdrw1.cpp:300-304), native rectangles as the list
#: carries them (x, y, x_end, y_end): the name, a continuous input field
#: 0x67 x 0xC at (0x106, 0x32); the hidden field over the name's line that
#: keeps a click there from closing the view; the hidden exit field over
#: the whole screen, added last.
TYPE_HIDDEN, TYPE_CONTINUOUS_INPUT = 7, 11
NAME_RECT = (0x106, 0x32, 0x106 + 0x67, 0x32 + 0xC)
GUARD_RECT = (0x10C, 0x32, 0x17F, 0x40)
EXIT_RECT = (0, 0, 0x27F, 0x1DF)

#: The F12 notice's sentence for a view the engine runs without the fix.
BARE_REASON = ("The ship's detail view: this orion2re lacks open fix 106 "
               "(python tools/version_check.py)")


def parse(gs, data, pos):
    """Read SHPV at `pos` into `gs.ship_view` (None when absent, short or of
    another version or record size). Returns the new position."""
    gs.ship_view = None
    r = Reader(data, pos)
    if not r.at_tag(b"SHPV") or not r.fits(4 + HEAD_SIZE + 1):
        return pos
    r.pos += 4
    version, ship, subject, name_field, exit_field = r.take(HEAD)
    n = r.one("B")
    if not r.fits(n + 2):
        return pos                          # truncated
    name = lang.wire_text(r.raw(n))
    size = r.one("h")
    if size < 0 or not r.fits(size):
        return pos                          # truncated
    if version != 1 or n > 15 or \
            size != combat_struct.UNIT_SPEC.resolved()[0]:
        return r.pos + size                 # refused, stepped over
    gs.ship_view = {"ship_idx": ship, "subject": subject,
                    "name_field": name_field, "exit_field": exit_field,
                    "name": name, "unit": combatblocks.unit(r.raw(size))}
    return r.pos


def build(ship_idx, record, name="", subject=0, name_field=-1, exit_field=-1,
          size=None, version=1):
    """The block as the engine writes it — for the checks' stand-ins.
    `record`: the unit's bytes in CMBT's form."""
    text = name.encode("latin-1")
    return (b"SHPV" + _st.pack(HEAD, version, ship_idx, subject, name_field,
                               exit_field) + bytes([len(text)]) + text +
            _st.pack("<h", len(record) if size is None else size) +
            bytes(record))


def for_state(state):
    """SHPV while the view reports 81, else None."""
    view = getattr(state, "ship_view", None)
    if view is None or getattr(state, "current_screen", -1) != SCREEN_ID:
        return None
    return view


def _rect(f):
    return (f.x, f.y, f.x_end, f.y_end)


def live_field(state, index, ftype, rect):
    """The live field `index` when it has the type and rectangle the view
    gives it, else None (decision 20: never a remembered index)."""
    return next((f for f in (getattr(state, "fields", None) or [])
                 if getattr(f, "index", 0) == index and index > 0 and
                 f.field_type == ftype and _rect(f) == rect), None)


def exit_field(state, view):
    return live_field(state, view["exit_field"], TYPE_HIDDEN, EXIT_RECT)


def name_field(state, view):
    return live_field(state, view["name_field"], TYPE_CONTINUOUS_INPUT,
                      NAME_RECT)


def bare(state):
    """True when the engine runs the view WITHOUT open fix 106: its caller's
    id, no SHPV, and the view's three fields in the list.

    HD STATE `ship_view_bare`: HD has no view of what the engine shows then;
    the screen's F12 notice names it at once (`bare_reason`,
    `ScreenBase.no_view_reason`)."""
    if getattr(state, "ship_view", None) is not None or \
            getattr(state, "current_screen", -1) not in CALLERS:
        return False
    shapes = {(f.field_type, _rect(f))
              for f in (getattr(state, "fields", None) or [])
              if getattr(f, "index", 0)}
    return {(TYPE_CONTINUOUS_INPUT, NAME_RECT), (TYPE_HIDDEN, GUARD_RECT),
            (TYPE_HIDDEN, EXIT_RECT)} <= shapes


def bare_reason(state):
    """The F12 notice's sentence for `bare`, else None."""
    return BARE_REASON if bare(state) else None
