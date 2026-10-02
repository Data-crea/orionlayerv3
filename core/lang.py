"""The language OrionLayer shows — work order 200 C
(`dev:doc/briefs/200-german-inventory.md`).

THREE KINDS OF WORDS, ONE LANGUAGE (decision C-1):

  the game's, extracted   a derived file per language (`*_<lang>.json`,
                          written by the extractors from the player's own
                          install). A file the install has no German source
                          for is read in English — `source` — and named once
                          in the log: "no German source".
  the game's, on the wire the engine formats them; it is English in this
                          install (it forces `_settings.language` to 0, and
                          the German files it would open are absent) —
                          parked, P-C1
  OrionLayer's own        one table per language, `assets/shared/lang/
                          <lang>.json`: {the English words: the German}, read
                          through the resources (a mod replaces the file,
                          decision C-3); `tr` is applied where text reaches a
                          font (`core/style.StyleRenderer.render_text`) and
                          where a sentence is wrapped (`core/textfit`), so a
                          sentence is translated whole before it is cut

ENGLISH IS THE IDENTITY. With "en" `tr` returns its argument unchanged and
`source` the path it was given: nothing in an English session changes
(090zs holds it byte for byte).

THE GERMAN CHARACTERS of the original's LBX texts are its German font's
slots (`CHARSET`), decoded when a German file is loaded (`decode`, applied
in `core/derivedjson.load`, `core/helptext`, `core/kentext`).
"""
import contextlib
import logging
import os
import re

log = logging.getLogger("lang")

#: The languages the switch offers, in its order; the first is the default.
LANGUAGES = ("en", "de")
DEFAULT = "en"
#: The original's language number for each (mox2.cpp, `_settings.language`).
NUMBERS = {"en": 0, "de": 1}
#: The files a German MOO2 has and an English one lacks, every one the
#: engine opens by `_settings.language` (textbox.cpp:25, harold.cpp:51 and
#: :1531, estrings.cpp:18, design.cpp:1025, officer.cpp:3474,
#: mainmenu.cpp:604, the font `fontsg.lbx` — a missing one is the engine's
#: fatal exit "fontsg.lbx [entry 0] could not be found", seen 2 October
#: 2026) and the extractors read (`tools/language_files.py`).
GERMAN_FILES = ("GER_HELP.LBX", "HGSTRNGS.LBX", "ESTRGERM.LBX", "MAINGERM.LBX",
                "GERSKLLS.LBX", "GERTECD.LBX", "FONTSG.LBX", "HERODATG.LBX",
                "GERCRDTS.LBX")
#: Every file the German language owns — the ones above and two an English
#: install DOES have, as English copies under the German names (Data's:
#: DIPLOMSG.LBX and EVENTMSG.LBX byte for byte DIPLOMSE / EVENTMSE, the
#: audience's statements and the events, dip_scrn_main.cpp:579,
#: events.cpp:2366). With another install named, the engine reads these
#: from there FIRST (open fix 70, `ORION2RE_LANGUAGE_FILES`); every other
#: file stays the game folder's own.
GERMAN_OWNED = GERMAN_FILES + ("DIPLOMSG.LBX", "EVENTMSG.LBX")

#: The German font's slots for the characters ASCII lacks, read off the
#: words of TECHNAME and BILLTEXT ("Geb[ude", "K#nstliche", "Bewu|tsein",
#: "Galaktische {konomie", "TECHNOLOGIE$BERSICHT", "GEB]UDE"); `\x08` marks
#: where a word may be hyphenated and is not drawn.
CHARSET = {"de": str.maketrans({"[": "ä", "]": "Ä", "}": "ö", "{": "Ö",
                                "#": "ü", "$": "Ü", "|": "ß", "\x08": ""})}

_FILE = re.compile(r"_([a-z]{2})\.json$")
#: {asked path: path read} for every file read in English instead.
FALLBACKS = {}

_state = {"language": DEFAULT, "table": {}, "upper": {}, "templates": [],
          "memo": {}, "verbatim": False, "engine": 0}
#: Placeholders that stand for a number, matched as one: a template "{job}:
#: {count} of {pops}" took "Cost[0]: In this form of government" for a
#: count while its placeholders matched anything (the German walk).
NUMERIC = {"n", "i", "id", "count", "pops", "max_pop", "total", "landed",
           "carried", "turns", "growth", "food", "industry", "research",
           "bc", "morale", "shortage", "made"}
_FIELD = re.compile(r"\{(\w+)\}|%[sd]")


def current():
    return _state["language"]


def configure(language, res=None):
    """Make `language` the one `tr` translates into; its table is read
    through `res` (mod resolution). Unknown languages are English."""
    if language not in LANGUAGES:
        if language:
            log.warning("language %r is not offered — English", language)
        language = DEFAULT
    table = {}
    if language != DEFAULT and res is not None:
        table = res.load_json(f"assets/shared/lang/{language}.json", {}) or {}
        table = {k: v for k, v in table.get("words", {}).items()
                 if isinstance(k, str) and isinstance(v, str)}
    _state["language"], _state["table"] = language, table
    # a label the HUD draws in capitals ("COLONIES") is the table's word
    # ("Colonies") in capitals: German capitals, `str.upper` (ß -> SS)
    _state["upper"] = {k.upper(): v.upper() for k, v in table.items()
                       if k.upper() not in table}
    _state["templates"] = [t for t in (_template(k, v) for k, v in
                                       table.items()) if t]
    _state["memo"] = {}
    return language


def _template(english, german):
    """A key with placeholders ({name}, %s, %d) as (regex, german, names):
    the screens format first and draw after, so the drawn text is matched
    against the template and its values carried over."""
    fields = list(_FIELD.finditer(english))
    # a template needs something of its own besides spaces: "{size}
    # {climate}" would match every two-word string ("Trade Goods" ->
    # "Trade, Goods", seen in the German walk of work order 200 C), while
    # "{climate} {pops}/{max_pop}" is held by its slash
    if not fields or not _FIELD.sub("", english).strip():
        return None
    parts, names, at = [], [], 0
    for i, m in enumerate(fields):
        parts.append(re.escape(english[at:m.start()]))
        name = m.group(1) or f"_{i}"
        if name in names:              # the same value twice: one group
            parts.append(f"(?P={name})")
        else:
            names.append(name)
            numeric = m.group() == "%d" or m.group(1) in NUMERIC
            parts.append(f"(?P<{name}>[-+]?[\\d.,]+)" if numeric
                         else f"(?P<{name}>.+?)")
        at = m.end()
    parts.append(re.escape(english[at:]))
    return re.compile("^" + "".join(parts) + "$", re.S), german, names


def _fill(german, values):
    seq = iter(values[n] for n in sorted(values) if n.startswith("_"))
    return _FIELD.sub(lambda m: tr(values[m.group(1)]) if m.group(1)
                      else next(seq, m.group()), german)


def tr(text):
    """OrionLayer's own words in the current language; anything the table
    does not hold (the game's words, names, numbers) unchanged."""
    if _state["language"] == DEFAULT or _state["verbatim"] or \
            not isinstance(text, str):
        return text
    hit = _state["table"].get(text)
    if hit is None and text.isupper():
        hit = _state["upper"].get(text)
    if hit is not None:
        return hit
    memo = _state["memo"]
    if text in memo:
        return memo[text]
    out = text
    for rx, german, _names in _state["templates"]:
        m = rx.match(text)
        if m:
            out = _fill(german, m.groupdict())
            break
    if len(memo) < 20000:
        memo[text] = out
        if out is text and _MISSES is not None:
            _MISSES.add(text)
    return out


#: A developer's record of every string `tr` left as it was (the language
#: walk's: `ORIONLAYER_LANG_TRACE=<file>` writes them at exit).
_MISSES = set() if os.environ.get("ORIONLAYER_LANG_TRACE") else None
if _MISSES is not None:
    import atexit
    import json as _json

    def _dump():
        with open(os.environ["ORIONLAYER_LANG_TRACE"], "w",
                  encoding="utf-8") as fh:
            _json.dump(sorted(_MISSES), fh, ensure_ascii=False, indent=0)
    atexit.register(_dump)


@contextlib.contextmanager
def verbatim():
    """The game's own text being drawn (a help entry, a message box, a
    popup's lines): `tr` leaves every piece of it alone, so a highlighted
    word inside a sentence ("~Farmers~ produce food") is not translated on
    its own (seen in the German walk)."""
    old, _state["verbatim"] = _state["verbatim"], True
    try:
        yield
    finally:
        _state["verbatim"] = old


def source(path):
    """(the path to read, its language) for a derived file: a file in a
    language whose file is absent is read in English."""
    m = _FILE.search(path)
    if m is None:
        return path, None
    lang = m.group(1)
    # only a language the switch offers falls back: a file in any other
    # stays what it was, absent (decision 38's state, 061 #2)
    if lang == DEFAULT or lang not in LANGUAGES or os.path.exists(path):
        return path, lang
    english = path[:m.start()] + f"_{DEFAULT}.json"
    if path not in FALLBACKS:
        FALLBACKS[path] = english
        log.info("lang: no %s source for %s — the English file is read",
                 lang, os.path.basename(path))
    return english, DEFAULT


def set_engine_language(number):
    """The language the engine's own texts are in: `_settings.language`,
    byte 210 of every snapshot's settings (open fix 70 lets it be other than
    0). Read before any block of the snapshot is parsed (`game_state`)."""
    _state["engine"] = number


def engine_settings(raw):
    """`set_engine_language` from a snapshot's settings bytes; returns
    them."""
    set_engine_language(raw[210] if len(raw) > 210 else 0)
    return raw


def engine_language():
    """The engine's language as a code ("en", "de"), None for one HD does
    not offer."""
    return next((k for k, v in NUMBERS.items() if v == _state["engine"]), None)


def wire_text(raw, encoding="latin-1"):
    """A string the engine sent: its bytes in latin-1 (or `encoding`), and
    in the German font's slots decoded when the engine speaks German
    (`CHARSET`) — an English engine's "[" stays a bracket."""
    text = raw.decode(encoding, errors="replace")
    table = CHARSET.get(engine_language())
    return text.translate(table) if table else text


def find_file(folder, name):
    """`name` in `folder`, in whatever case the install wrote it; None."""
    if not folder or not os.path.isdir(folder):
        return None
    wanted = name.lower()
    return next((os.path.join(folder, f) for f in sorted(os.listdir(folder))
                 if f.lower() == wanted), None)


def missing_files(language, *folders):
    """The language's files that none of `folders` holds."""
    names = GERMAN_FILES if language == "de" else ()
    return [n for n in names
            if not any(find_file(f, n) for f in folders if f)]


def engine_env(settings, game_dir=None):
    """`(env, missing)`: the variables an engine with open fix 70 reads at
    start — the player's language (`ORION2RE_LANGUAGE`, the original's
    number) and the other install holding its files (`ORION2RE_LANGUAGE_DIR`,
    recorded by `tools/language_files.py`, with the files the language owns,
    `ORION2RE_LANGUAGE_FILES`, read from there first) — and the files that
    keep it
    English. ONLY WITH EVERY FILE: an engine told German without them stops
    at its first one (the font). English sets nothing: an engine starts as
    before the fix."""
    language = (settings or {}).get("language") or DEFAULT
    if language == DEFAULT or language not in NUMBERS:
        return {}, []
    folder = (settings or {}).get("language_dir")
    gone = missing_files(language, game_dir, folder)
    if gone:
        return {}, gone
    env = {"ORION2RE_LANGUAGE": str(NUMBERS[language])}
    if folder:
        env["ORION2RE_LANGUAGE_DIR"] = folder
        env["ORION2RE_LANGUAGE_FILES"] = ",".join(GERMAN_OWNED)
    return env, []


def decode(value, language):
    """A German file's strings in Unicode (`CHARSET`); dict KEYS and
    non-strings untouched; any other language unchanged."""
    table = CHARSET.get(language)
    if table is None:
        return value
    if isinstance(value, str):
        return value.translate(table)
    if isinstance(value, list):
        return [decode(v, language) for v in value]
    if isinstance(value, dict):
        return {k: (v if k.startswith("_") else decode(v, language))
                for k, v in value.items()}
    return value
