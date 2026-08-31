"""Context help text — the strings MOO2 shows on a right click.

The right-click help is a TRANSCRIPTION, not an invention. In the
original, `fields::Get_Input_()` answers a right button by walking the
active help list (`fields::Check_Help_List_`, fields.cpp:2916); a hit
draws `TEXTBOX::Draw_Help_Entry_(help_id)` (textbox.cpp:307) and the
click is swallowed instead of acting as Cancel. Every screen installs
its own list through `fields::Set_Help_List_`.

The text itself is NOT in the source. It lives in the game's own
`HELP.LBX` (or `GER_HELP.LBX`, `FRE_HELP.LBX`, `SPA_HELP.LBX`,
`ITA_HELP.LBX` — chosen by `MOX::_settings.language`,
textbox.cpp:17), and orion2re does not put it on the Extension API.
OrionLayer therefore reads it the same way it reads nebula sprites:
straight out of the LBX with `tools/help_extract.py`, which writes

    assets/shared/help/help_<lang>.json

That file is generated, never hand-edited, and is not shipped with
the project — it is derived from the user's own MOO2 installation.
Until it is generated, `entry()` returns None and the popup says so
with the command that fixes it, rather than drawing an empty box.

Wording that belongs to OrionLayer rather than to MOO2 (the CLOSE
label, the "not extracted yet" message) lives in
`assets/shared/help/labels.json`, so a translation replaces it
without touching code — decision 15.
"""
import logging

log = logging.getLogger("helptext")

#: Bumped when the extractor's output changes shape. Format 1 was
#: written by a version that stripped trailing whitespace per line
#: and destroyed FMTPARA's tab and form-feed codes with it; format 2
#: hands the bytes over untouched and decoding happens at load time.
FORMAT_VERSION = 2

#: Language code -> LBX file, transcribed from textbox.cpp:17
#: (`TEXTBOX::Get_Help_Lbx_Name_`). Index is
#: `MOX::_settings.language`; 0 falls through to the default.
HELP_LBX = {
    "en": "HELP.LBX",
    "de": "GER_HELP.LBX",
    "fr": "FRE_HELP.LBX",
    "es": "SPA_HELP.LBX",
    "it": "ITA_HELP.LBX",
}

#: Directory the extracted files live in, resource-relative.
HELP_DIR = "assets/shared/help"


def help_file(language):
    """Resource path of the extracted help file for a language.

    The one place this string is built. It had been written out
    independently in three: here, in `tools/help_extract.py` (which
    writes the file) and in `tools/setup.py` (which reports whether
    it is there). setup checked `help_en.json` while the loader read
    `help_<language>.json`, so a German install was told to run an
    extractor it had already run — the name-table-in-three-files
    failure, in its checking variant. The smoke test now asserts the
    three agree.
    """
    return f"{HELP_DIR}/help_{language}.json"


#: Used when labels.json is missing so the popup never renders blank.
FALLBACK_LABELS = {
    "close": "CLOSE",
    "scroll_hint": "scroll",
    "missing_title": "Help text not installed",
    "missing_body": (
        "The help texts live in your own MOO2 installation, not in "
        "OrionLayer. Extract them once with:  "
        "python tools/help_extract.py"
    ),
    "stale_title": "Help text out of date",
    "stale_body": (
        "The help file was written by an older version of the "
        "extractor and is missing layout information. Run it again:  "
        "python tools/help_extract.py"
    ),
    "unknown_title": "No help entry",
    "unknown_body": (
        "The help file loaded, but it has no entry {id}. That points "
        "at a different game version or a different language file, "
        "not at a missing extraction step."
    ),
}


class HelpText:
    """Loads and serves the extracted help entries.

    One instance per App. Resolution goes through `core.resources`,
    so a mod can ship its own help file or a translation.
    """

    def __init__(self, res, language="en"):
        self.res = res
        self.language = language
        self._entries = {}
        self._labels = dict(FALLBACK_LABELS)
        self._available = False
        self._stale = False
        self.load()

    # ── Loading ──────────────────────────────────────────

    def load(self):
        """(Re)read the help file and the label file."""
        labels = self.res.load_json(f"{HELP_DIR}/labels.json")
        if isinstance(labels, dict):
            self._labels.update(labels)

        data = self.res.load_json(help_file(self.language))
        if not isinstance(data, dict):
            self._entries = {}
            self._available = False
            self._stale = False
            log.info("No help_%s.json — right-click help will point "
                     "at tools/help_extract.py", self.language)
            return

        raw = data.get("entries", {})
        # An earlier extractor rstripped every line, which quietly ate
        # the trailing \t, \v and \f that FMTPARA uses. A file from it
        # renders *almost* right, which is worse than not loading at
        # all — so the version is checked and a stale file is refused
        # with the command that fixes it.
        version = data.get("format", 1)
        if version < FORMAT_VERSION:
            self._entries = {}
            self._available = False
            self._stale = True
            log.warning(
                "help_%s.json is format %d, this build needs %d — "
                "re-run: python tools/help_extract.py",
                self.language, version, FORMAT_VERSION)
            return

        self._stale = False
        # Keys arrive as strings from JSON; the call sites hold ints.
        self._entries = {}
        for key, value in raw.items():
            try:
                self._entries[int(key)] = value
            except (TypeError, ValueError):
                continue
        self._available = bool(self._entries)
        log.info("Help text: %d entries (%s)",
                 len(self._entries), self.language)

    # ── Queries ──────────────────────────────────────────

    @property
    def available(self):
        return self._available

    def label(self, key):
        return self._labels.get(key, FALLBACK_LABELS.get(key, ""))

    def entry(self, help_id):
        """Return (title, body) for a help id, or None.

        None means "nothing to show": either the file has not been
        extracted or this id is missing from it. Both are the
        caller's problem to present, not this module's.
        """
        rec = self._entries.get(help_id)
        if not isinstance(rec, dict):
            return None
        title = (rec.get("title") or "").strip()
        body = (rec.get("body") or "").strip()
        if not title and not body:
            return None
        return (title, body)

    def missing_entry(self, help_id=None):
        """The placeholder shown when `entry()` returned nothing.

        Two different faults produce the same empty box, and telling
        the user to run the extractor is only right for one of them.
        If the file loaded, the extractor has already done its job
        and the real problem is that this id is not in it — a version
        or language mismatch, not a missing step.
        """
        if self._stale:
            return (self.label("stale_title"), self.label("stale_body"))
        if not self._available:
            return (self.label("missing_title"),
                    self.label("missing_body"))
        body = self.label("unknown_body")
        if help_id is not None:
            body = body.replace("{id}", str(help_id))
        return (self.label("unknown_title"), body)
