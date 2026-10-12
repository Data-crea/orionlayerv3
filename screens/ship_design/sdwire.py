"""What the Ship Designer reads off the wire, and whether it may draw.

Work order 185. The page draws ONLY from open fix 44's "DSGN" block
(`core/designblocks.py`) — applied with 45 by work order 186 (orion2re
`70d31b10`, `4af9fefa`) and seen live on that engine, so the page is HD on
the engine `play.py` starts. On an engine without the block `claims`
answers False and id 3 stays the game's own picture through the safety
net. Nothing is drawn from an invented value (decision 61).

THE STATES:
  READY     DSGN on the wire and the page's own list up (its Cancel button
            at the source's origin): the page draws and takes input.
  GAME_BOX  DSGN on the wire and a list that is NOT the page's: a warning
            or message box over the designer ("You may not upgrade the
            ship's shield." — the reading, section 10), or a picker on an
            engine with fix 44 and without 45. HD has no view for it: the
            screen hands over (`wants_original`) and the hand-over gate
            treats it as a modal net (`handover_is_modal`) — the game's
            picture answers it, which is decision 22's case.
  PICKER    DSGN and open fix 45's DSBX on the wire: a picker is up, drawn
            by `screens/design_box` over this page. The page draws under
            it from the design and the last list of its own it saw (the
            buttons' places and states only — nothing is SENT from a
            remembered list, decision 20; the picker is the top screen and
            takes every input).
"""
from . import sdgeom as geom

READY, GAME_BOX, PICKER = "ok", "game_box", "picker"


def live_field(fields, ident):
    """The field of `ident` = (type, x, y) in the list read now, or None —
    matched by type and origin, never by index (decision 20)."""
    ftype, x, y = ident
    for f in fields or []:
        if f.index != 0 and f.field_type == ftype and (f.x, f.y) == (x, y):
            return f
    return None


def at_origin(fields, x, y, types=None):
    """The field at native origin (x, y), of one of `types` if given."""
    for f in fields or []:
        if f.index != 0 and (f.x, f.y) == (x, y) and \
                (types is None or f.field_type in types):
            return f
    return None


def claims(state):
    """Id 3 is the HD screen's only with DSGN on the wire (open fix 44)."""
    return getattr(state, "ship_design", None) is not None


class View:
    """One snapshot's reading: the design, and whether the page is up."""

    def __init__(self, state, page_fields=None):
        self.design = getattr(state, "ship_design", None)
        self.fields = getattr(state, "fields", None) or []
        self.colour = _colour(state)
        if self.design is None:
            self.state, self.reason = GAME_BOX, "no DSGN block (open fix 44)"
        elif getattr(state, "design_box", None) is not None:
            self.state, self.reason = PICKER, ""
            self.fields = page_fields or []
        elif live_field(self.fields, geom.CANCEL) is None:
            self.state = GAME_BOX
            self.reason = ("a box over the designer HD has no view for — "
                           "the game's own picture answers it")
        else:
            self.state, self.reason = READY, ""

    @property
    def draws(self):
        return self.state in (READY, PICKER)

    def weapon_rows(self):
        """[(slot, weapon dict)] of the loaded weapons, in slot order."""
        return [(i, w) for i, w in enumerate(self.design["weapons"])
                if w["type"] != 0]

    def specials(self):
        return [(i, s) for i, s in enumerate(self.design["specials"])
                if s != 0]

    def hull_offered(self, size):
        """A hull button field (type 3) exists for `size` — the original
        adds a hidden field instead where it may not be chosen."""
        y1 = geom.HULL_ROWS[size][0]
        return at_origin(self.fields, geom.HULL_X[0], y1,
                         (geom.TYPE_MULTI,)) is not None


def _colour(state):
    """The local player's colour byte (the ship pictures' set)."""
    from core.structs import player as player_spec
    raws = getattr(state, "player_raw", None) or []
    me = getattr(state, "player_num", 0) or 0
    if not 0 <= me < len(raws) or raws[me] is None:
        return None
    try:
        return int(player_spec.SPEC.parse(raws[me]).color)
    except (AttributeError, ValueError, TypeError, IndexError):
        return None
