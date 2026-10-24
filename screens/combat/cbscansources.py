"""What the ship scan reads besides the battle, and its pictures — split
off `cbscanview` (work order 303, at the 40 KB limit): the screen's
tables, art and colours, the round's first frame (`Sources`), the unit's
and the officer's pictures (`Pictures`). The window itself is
`cbscanview`; what it says, `cbscan`.
"""
from . import cbscan
from .cbscanview import NOSE_UP


class Pictures:
    """The pictures of one scan: the unit as the battle draws it, the same
    unit nose up for the shields' ring, the officer's portrait (the Leaders
    screen's: `core.leaderportraits`, else OFFICER.LBX's) and his skills'
    icons (OFFICER.LBX `0x58 + id / 2`, `ldrart.skill_icon`)."""

    def __init__(self, art, colours, unit, leader_art):
        from . import cbdraw
        self.ship = cbdraw.unit_picture(art, colours, unit, 0)
        self.upright = cbdraw.unit_picture(
            art, colours, {**unit, "facing_dir": NOSE_UP}, 0)
        self._leader_art = leader_art

    def portrait(self, officer, size):
        from core import leaderportraits
        rec = officer["rec"]
        hd = leaderportraits.picture(rec, size)
        if hd is not None:
            return hd
        la = self._leader_art
        sprite = la.portrait(rec.pict_num) if la is not None and \
            la.available else None
        return leaderportraits.fit(sprite, size) if sprite is not None \
            else None

    def skill_icon(self, sid, size):
        la = self._leader_art
        icon = la.skill_icon(sid) if la is not None and la.available \
            else None
        if icon is None:
            return None
        from core import nativedraw
        return nativedraw.skill_icon(icon, size)


class Sources:
    """What the scan reads besides the battle: the screen's tables, its
    art and colours. Built by the combat screen."""

    def __init__(self, screen):
        self._screen = screen
        self._words = None
        self._round = None
        self._leader_art = None
        self._pictures = {}

    def words(self):
        s = self._screen
        key = (id(s._names), id(s._ken), s._language)
        if self._words is None or self._words[0] != key:
            from core import estrings, hestrings, skildesc
            from screens.leaders import ldrrows
            unit = ldrrows.UNIT.get(s._language, ldrrows.UNIT_DEFAULT)
            self._words = (key, cbscan.Words(
                s._ken, s._names, estrings.EStrings(s._language),
                hestrings.for_app(s.app), unit,
                skildesc.for_app(s.app)))
        return self._words[1]

    def note_round(self, shown):
        """Keep the battle's units as the first frame of each combat round
        shows them: what the engine added the combat values up from (its
        round loop, combinit.cpp:1053-1061) — the card's parts are counted
        from it (`cbscanparts.breakdown`). A new battle, or a frame from
        before the one kept, starts over."""
        turn, units = int(shown.get("turn", 0)), shown.get("units") or []
        r = self._round
        if r is None or r[0] != turn or len(r[1]) != len(units):
            self._round = (turn, [dict(u) for u in units])

    def round_start(self, shown):
        r = self._round
        if r is None or r[0] != int(shown.get("turn", 0)):
            return None
        return r[1]

    def pictures(self, unit):
        """Made once per unit, picture and colours (P828: kept with what
        they were made from)."""
        s = self._screen
        if self._leader_art is None:
            from screens.leaders import ldrart
            self._leader_art = ldrart.load()
        key = (unit["name"], int(unit["picture_num"]),
               int(unit["facing_dir"]), int(unit["owner"]),
               int(unit["previous_owner"]), id(s._art),
               tuple(sorted(s._play.colours.items())))
        hit = self._pictures.get(key)
        if hit is None:
            if len(self._pictures) > 32:
                self._pictures.clear()
            hit = self._pictures[key] = Pictures(
                s._art, s._play.colours, unit, self._leader_art)
        return hit
