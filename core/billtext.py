"""The original's BILLTEXT messages, loaded from a derived file.

**THE HELP-TEXT PATTERN AGAIN** (decision 38), after the help texts,
the building names, ESTRINGS, HESTRNGS and the research names:
`tools/billtext_extract.py` moves the bytes out untouched, this module
decodes at load time, the file carries a format version and is never
committed, and its absence is a state the screen explains — the
research screen's own JSON labels stand in, and it says so.

**THE FILE'S SHAPE IS `Get_Text_Message_`'s** (jim.cpp:336-359):

    entry index  = message id * 6 + MOX::_settings.language
                   (the language is clamped to 0 above 5)
    the entry    = the usual (total_count, element_size) 4-byte header
                   (`Farload_Library_Data_`, farload.cpp:90-113), then
                   ONE record of element_size bytes — 100 for this
                   file — holding a NUL-terminated string.

So a message is its own six LBX entries, one per language slot, and
NOT an offset into a block the way TECHNAME and ESTRINGS work. The
extractor reads the whole file at the language it is given.

**WHAT THE RESEARCH SCREEN USES** (doc/tech_change_reading.md §3, and
read out of the English file on 18 September 2026):

    1     the science room's headline, "Your scientists have completed
          their research in ..." — the FMTPARA argument is the 0x8B
          byte, see core/helpformat.py
    61    "Research cost: ", the description box's prefix (tech.cpp:735)
    62    "Pure research", the row a category shows when it has no
          pickable application (tech.cpp:624-636) — NOT an error and
          not an empty row: picking it is how the original spends a
          field on research points alone
    63    " LIST", and 64..73 the eight category names plus two,
          "BASIC" first — the list popup's title is 64 + group then 63
          (tech.cpp:802-816)

The ids are the game's, so `message()` takes the id and nothing here
renumbers them.
"""
import json
import logging
import os

from core.config import BASE_DIR

log = logging.getLogger("billtext")

#: Bumped when the extractor's output shape changes (decision 38).
FORMAT_VERSION = 1

#: `Get_Text_Message_`'s own arithmetic (jim.cpp:346).
LANGUAGE_SLOTS = 6

#: The element size this file declares, checked rather than assumed —
#: `Farload_Library_Data_` errors out when it disagrees
#: (farload.cpp:104-107), so a file with another size is a file this
#: walk does not understand.
ELEMENT_SIZE = 100

#: The ids the research screens read, for the extractor's report and
#: for a check that the file actually carries them.
RESEARCH_MESSAGES = (1, 61, 62, 63) + tuple(range(64, 74))

#: `_Tech_Select_`'s "no available application" row (tech.cpp:515).
MSG_NO_APPLICATION = 62
#: The description box's cost prefix (tech.cpp:735).
MSG_RESEARCH_COST = 61
#: The list popup's title parts (tech.cpp:802-816).
MSG_LIST_SUFFIX = 63
MSG_FIRST_GROUP = 64
#: The science room's headline (science.cpp, work order 129 B).
MSG_RESEARCH_COMPLETED = 1


def message_file(language="en"):
    """Where the extractor writes and the loader reads."""
    return os.path.join("assets", "shared", "names",
                        f"billtext_{language}.json")


class BillText:
    """Loaded messages, or a stated absence ("ok", "missing", "stale")."""

    def __init__(self, language="en", root=None):
        self.language = language
        self.state = "missing"
        self.messages = {}
        self._load(root or BASE_DIR)

    def _load(self, root):
        path = os.path.join(root, *message_file(self.language).split("/"))
        if not os.path.exists(path):
            log.info("billtext: %s absent — run "
                     "`python tools/billtext_extract.py`", path)
            return
        try:
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)
        except (ValueError, OSError) as err:
            log.warning("billtext: %s will not load (%s)", path, err)
            return
        if int(data.get("format", 0)) < FORMAT_VERSION:
            self.state = "stale"
            log.warning("billtext: %s is format %s, this build reads %s — "
                        "re-run tools/billtext_extract.py",
                        path, data.get("format"), FORMAT_VERSION)
            return
        self.messages = {int(k): v
                         for k, v in data.get("messages", {}).items()}
        # A file that loads but lacks what the screen reads is NOT "ok":
        # it would leave the panel half in the game's words and half in
        # OrionLayer's, which reads as a broken screen rather than an
        # absent file.
        self.state = "ok" if all(i in self.messages
                                 for i in RESEARCH_MESSAGES) else "missing"

    def message(self, message_id):
        """The message, or None for an absent file or an id it lacks."""
        if message_id is None:
            return None
        return self.messages.get(int(message_id))

    def group_name(self, group):
        """A technology category's name, message 64 + group."""
        return self.message(MSG_FIRST_GROUP + int(group))
