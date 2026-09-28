"""What the diplomacy audience reads off the wire, and whether it may draw.

Work order 185 part 10. The screen draws ONLY from open fix 47's "DIPL"
block (`core/diplblocks.py`) and the list the game built; fixes 46 and 47
are applied since work order 186 (orion2re `8aea1a25`, `ba9b6bc6`). Without 46 the audience
runs under its caller's id and never reaches this screen; with 46 and
without 47 the screen declines 57 / 58 and the game's picture is shown.

THE STATES:
  MENU       DIPL carries a list, and the live list is its shape: one
             type-10 field per item plus the title's (`Get_List_Field_`,
             fields.cpp:1561-1620). The screen draws the menu and takes a
             click on an enabled item.
  STATEMENT  DIPL carries no list and the live list is one field over the
             whole screen: a statement waiting for a click (the refusal,
             a greeting, a reply). Any click answers it.
  GAME_BOX   anything else — the system picker (its own loop and stars,
             dip_scrn.cpp:700-860), a list that disagrees with DIPL: HD has
             no view for it and hands over, a modal net (decision 22).
"""
from . import augeom as geom

MENU, STATEMENT, GAME_BOX = "menu", "statement", "game_box"


def claims(state):
    """57 / 58 are HD's only with DIPL on the wire (open fix 47)."""
    return getattr(state, "audience", None) is not None


class View:
    """One snapshot's reading of the audience."""

    def __init__(self, state):
        self.audience = getattr(state, "audience", None)
        self.fields = [f for f in (getattr(state, "fields", None) or [])
                       if f.index != 0]
        self.race = _race(state, self.audience)
        lists = sorted((f for f in self.fields
                        if f.field_type == geom.TYPE_LIST), key=lambda f: f.y)
        a = self.audience
        if a is None:
            self.state, self.reason = GAME_BOX, "no DIPL block (open fix 47)"
        elif a["items"] and len(lists) == len(a["items"]) + 1 and \
                len(self.fields) == len(lists):
            self.state, self.reason = MENU, ""
        elif not a["items"] and len(self.fields) == 1 and \
                (self.fields[0].x, self.fields[0].y, self.fields[0].x_end,
                 self.fields[0].y_end) == geom.FULL_SCREEN:
            self.state, self.reason = STATEMENT, ""
        else:
            self.state = GAME_BOX
            self.reason = ("a list over the audience HD has no view for — "
                           "the game's own picture answers it")
        self.title_field = lists[0] if lists else None
        self.item_fields = lists[1:]

    @property
    def draws(self):
        return self.state in (MENU, STATEMENT)

    @property
    def refused(self):
        """The ambassador is not drawn when the audience is refused
        (`_ambassador_option` 0, dip_scrn_main.cpp:1562)."""
        return self.audience is not None and self.audience["option"] == 0

    def items(self):
        """[(item dict, its field)] top to bottom."""
        if self.state != MENU:
            return []
        return list(zip(self.audience["items"], self.item_fields))


def _race(state, audience):
    """The ambassador's race (`s_player.race` @37), or None."""
    if audience is None:
        return None
    from core.structs import player as player_spec
    raws = getattr(state, "player_raw", None) or []
    i = audience["ambassador"]
    if not 0 <= i < len(raws) or raws[i] is None:
        return None
    try:
        return int(player_spec.SPEC.parse(raws[i]).race)
    except (AttributeError, ValueError, TypeError, IndexError):
        return None
