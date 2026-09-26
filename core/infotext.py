"""The Info screen's own original texts, loaded from a derived file.

Decision 38's pattern (the help texts, BILLTEXT, ESTRINGS …):
`tools/infotext_extract.py` moves the player's own bytes out — the
Reference topic lists (HELP.LBX 1-16), the trait names (RACESTUF.LBX
8 + language) and the Tech Review's group names (BILLTEX2.LBX) — this
module reads them, the file carries a format version and is never
committed, and its absence is a state the screen explains.
"""
import json
import logging
import os

from core.config import BASE_DIR

log = logging.getLogger("infotext")

FORMAT_VERSION = 1
HOW = "python tools/infotext_extract.py"


def text_file(language="en"):
    return f"assets/shared/names/infotext_{language}.json"


class InfoText:
    """Loaded texts, or a stated absence ("ok", "missing", "stale")."""

    def __init__(self, language="en", root=None):
        self.language = language
        self.state = "missing"
        self.topics, self.traits, self.groups = {}, [], {}
        path = os.path.join(root or BASE_DIR, *text_file(language).split("/"))
        if not os.path.exists(path):
            log.info("infotext: %s absent — run `%s`", path, HOW)
            return
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError) as err:
            log.warning("infotext: %s will not load (%s)", path, err)
            return
        if int(data.get("format", 0)) != FORMAT_VERSION:
            self.state = "stale"
            log.warning("infotext: %s is format %s, this build reads %s — "
                        "re-run %s", path, data.get("format"), FORMAT_VERSION,
                        HOW)
            return
        self.topics = {int(k): [(t, int(i)) for t, i in v]
                       for k, v in data.get("topics", {}).items()}
        self.traits = list(data.get("traits", []))
        self.groups = {int(k): v for k, v in data.get("groups", {}).items()}
        self.state = "ok" if self.topics and self.traits else "missing"

    def topic_list(self, entry):
        return self.topics.get(int(entry), [])

    def trait(self, index):
        return self.traits[index] if 0 <= index < len(self.traits) else None

    def group(self, group_id):
        return self.groups.get(int(group_id))
