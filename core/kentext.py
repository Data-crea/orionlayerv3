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
        self.absent = ""
        self._load(root or os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))

    def _load(self, root):
        path = os.path.join(root, *string_file(self.language).split("/"))
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
        self.arcs = {int(k): v for k, v in (doc.get("arcs") or {}).items()}

    @property
    def available(self):
        return bool(self.arcs)

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
