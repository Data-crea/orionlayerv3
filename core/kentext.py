"""The weapon firing-arc words, loaded from a derived file.

`tools/kentext_extract.py` moves them out of the player's own
KENTEXT.LBX; this decodes at load time (decision 38) and answers None
for anything it does not have, so a caller can say the word is missing
instead of inventing one.

**THE ORDER MATTERS AND IT IS THE ORIGINAL'S.**
`DESIGN::Weapon_Arc_String_` (design.cpp) tests the bits one at a time
and RETURNS on the first hit — forward, forward-extended,
back-extended, rear, then 360. An arc of 0x0F (ALL_SECTORS) has four of
those bits set and the original prints the FORWARD word for it, so the
order here is not a tidy-up, it is the answer.
"""
import json
import logging
import os

log = logging.getLogger("kentext")

FORMAT_VERSION = 1

#: `WEAPON_FIRING_ARC` (orion2_consts.h:1078-1085) -> the message index
#: `Weapon_Arc_String_` asks `KEN::Ken_Get_Text_Message_` for.
ARC_MESSAGES = {
    0x01: 3,    # FORWARD
    0x02: 4,    # FORWARD_EXTENDED
    0x04: 6,    # BACK_EXTENDED
    0x08: 5,    # REAR
}

#: The battle panel's words over the unit's status box (work order 258):
#: what -> KENTEXT message (`KEN::Ken_Get_Text_Message_`, below 0x50 so
#: KENTEXT.LBX): the officer's mark (cmbtdrw1.cpp:1222-1245, "(L)" in the
#: English game) and "Immobile" (cmbtdrw1.cpp:2355).
PANEL_MESSAGES = {"officer": 86, "immobile": 0x47,
                  # the systems box (`Draw_Internals_Display_`,
                  # cmbtdrw1.cpp:360-425), work order 258
                  "systems": 36, "drive": 14, "no_drive": 37, "shields": 39,
                  "no_shields": 38, "computer": 21, "structure": 16,
                  "armor": 18, "max_speed": 40, "remaining": 90,
                  # the hovered missile's box (`Draw_Missile_Status_`,
                  # cmbtmis.cpp:1395-1436), work order 259: "Target:" run
                  # into the name, the quantity's words with their space
                  "target": 52, "missile": 53, "torpedo": 54,
                  "missiles": 107, "torpedoes": 108,
                  # the ship scan (`Combat_Draw_View_Ship_`, cmbtdrw1.cpp:
                  # 3223-4007), work order 290
                  "no_specials": 7, "bonuses": 8, "beam_attack": 9,
                  "beam_defense": 10, "missile_evasion": 11, "marines": 12,
                  "captured": 13, "parsecs": 15, "combat_speed": 17,
                  "computer_bonus": 22, "no_bonus": 23, "weapons": 25,
                  "ammo": 26, "mods": 27, "ready": 28, "none": 29,
                  "specials": 30, "crew_green": 31, "crew_regular": 32,
                  "crew_veteran": 33, "crew_elite": 34, "crew_ultra": 35,
                  "structure_of": 0x59, "armor_of": 0x5B}

#: The bits in the order the original tests them, 0x10 last.
ARC_ORDER = (0x01, 0x02, 0x04, 0x08, 0x10)

#: **NOT IN ANY TABLE.** `Weapon_Arc_String_` answers 0x10 with
#: `strlcpy(dest_str, "360", …)` — a literal in the engine — so this is
#: a transcription and not an extraction, and it needs no file.
ARC_360 = "360"


def string_file(language="en"):
    """Where the extractor writes and the loader reads."""
    return os.path.join("assets", "shared", "names",
                        f"kentext_{language}.json").replace(os.sep, "/")


class ArcWords:
    """The loaded table, or a stated absence. Never an exception."""

    def __init__(self, language="en", root=None):
        self.language = language
        self.arcs = {}
        self.panel = {}
        self.absent = ""
        self._load(root or os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))

    def _load(self, root):
        from core import lang
        path, language = lang.source(
            os.path.join(root, *string_file(self.language).split("/")))
        if not os.path.exists(path):
            self.absent = (f"{string_file(self.language)} is not there — "
                           f"run: python tools/kentext_extract.py "
                           f"--lang {self.language}")
            return
        try:
            with open(path, encoding="utf-8") as handle:
                doc = json.load(handle)
        except (OSError, ValueError) as exc:
            self.absent = f"{path}: {exc}"
            return
        if doc.get("format") != FORMAT_VERSION:
            self.absent = (f"{path}: format {doc.get('format')!r}, this "
                           f"build reads {FORMAT_VERSION} — re-extract")
            return
        self.arcs = {int(k): v for k, v in
                     lang.decode(doc.get("arcs") or {}, language).items()}
        # absent from a file extracted before work order 258: the panel
        # then says so with OrionLayer's word (`panel_word`)
        self.panel = {int(k): v for k, v in
                      lang.decode(doc.get("panel") or {}, language).items()}

    @property
    def available(self):
        return bool(self.arcs)

    def panel_word(self, what):
        """The game's word for `what` in `PANEL_MESSAGES`, or None (the
        file predates work order 258: run the extractor again)."""
        return self.panel.get(PANEL_MESSAGES[what])

    def arc(self, flags):
        """The word for a firing arc, or None.

        `Weapon_Arc_String_`'s own test order, first hit wins.
        """
        try:
            flags = int(flags)
        except (TypeError, ValueError):
            return None
        for bit in ARC_ORDER:
            if not flags & bit:
                continue
            if bit == 0x10:
                return ARC_360
            return self.arcs.get(bit)
        return None
