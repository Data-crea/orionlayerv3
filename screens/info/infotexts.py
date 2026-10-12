"""Every text the Info screen shows, by a stable key — work order 175 D,
decision 73 (`core/modtexts`).

`TEXTS` is `{key: (default, source)}`. A "moo2" default is a callable
that reads the player's own extracted file when asked (BILLTEXT, ESTRINGS,
HELP.LBX records, the Info texts, TECHNAME) — the original's words are
never written into this tree or into the mod template. An "own" default
is OrionLayer's words (where the original has its words baked into the
art, or where HD says something the original does not); a "game" key is
a value the game supplies (a number, a name) and is never replaced.

The loaders are bound once per app (`bind`); unbound, a "moo2" default is
None and the screen says less rather than something of ours.
"""
_src = {"billtext": None, "estrings": None, "help": None, "info": None,
        "tech": None}


def bind(billtext=None, estrings=None, helptext=None, infotext=None,
         technames=None):
    _src.update(billtext=billtext, estrings=estrings, help=helptext,
                info=infotext, tech=technames)


def _ok(name):
    got = _src.get(name)
    if got is None:
        return None
    state = getattr(got, "state", "ok")
    return got if state == "ok" or name in ("help", "tech") else None


def _bill(i):
    def get():
        b = _ok("billtext")
        return b.message(i) if b is not None else None
    return get


def _est(i):
    def get():
        e = _ok("estrings")
        return e.string(i) if e is not None else None
    return get


def _help(i, part):
    def get():
        h = _ok("help")
        entry = h.entry(i) if h is not None else None
        return entry[part] if entry else None
    return get


def _topic(i):
    def get():
        t = _ok("info")
        if t is None:
            return None
        for lst in t.topics.values():
            for text, tid in lst:
                if tid == i:
                    return text
        return None
    return get


def _trait(i):
    def get():
        t = _ok("info")
        return t.trait(i) if t is not None else None
    return get


def _group(i):
    def get():
        t = _ok("info")
        return t.group(i) if t is not None else None
    return get


def _app(i):
    def get():
        t = _ok("tech")
        return t.application_name(i) if t is not None else None
    return get


#: The five pages, in the tab order (`_sub_scr_field`, info.cpp:174).
PAGES = ("history", "tech", "races", "turns", "reference")

TEXTS = {}
# The pages' titles (billtext 5-9, info.cpp:1150, :1500, :1659, :2018, :1935)
for _k, _p in enumerate(PAGES):
    TEXTS[f"info.title.{_p}"] = (_bill(5 + _k), "moo2")
# The tab buttons: the original has these words in INFO.LBX 3-7.
for _p, _w in zip(PAGES, ("History", "Tech Review", "Race Stats",
                          "Turn Summary", "Reference")):
    TEXTS[f"info.tab.{_p}"] = (_w, "own")
TEXTS.update({
    "info.exit": ("RETURN", "own"),
    "info.chart.income": (_bill(17), "moo2"),
    "info.chart.maintenance": (_bill(18), "moo2"),
    "info.chart.net_income": (_bill(27), "moo2"),
    "info.races.eliminated": (_bill(14), "moo2"),
    "info.races.none": (_bill(15), "moo2"),
    "info.turns.empty": (_bill(16), "moo2"),
    "info.turns.header": (_bill(26), "moo2"),
    "info.reference.categories": (_bill(10), "moo2"),
    "info.reference.howto": (_bill(11), "moo2"),
    "info.reference.category_prefix": (_bill(12), "moo2"),
    "info.reference.howto_prefix": (_bill(13), "moo2"),
    "info.reference.back": ("BACK", "own"),
    "info.stardate": ("", "game"),
    # OrionLayer's own: what HD says on an engine without open fix 32
    # (applied since work order 176), the history metrics and the tech categories whose words the
    # original bakes into INFO.LBX 8-11 and 16-19.
    "info.history.no_block": (
        "This engine does not send the scale its history is stored in "
        "(open fix 32, doc/ext_info_screen_state.patch, is not in it), so "
        "the curves cannot be drawn. The races and their colours are "
        "shown.", "own"),
    "info.turns.no_block": (
        "This engine does not send the turn's messages (open fix 32, "
        "doc/ext_info_screen_state.patch, is not in it).", "own"),
    "info.history.metric.population": ("Population", "own"),
    "info.history.metric.production": ("Production", "own"),
    "info.history.metric.fleet": ("Fleet", "own"),
    "info.history.metric.tech": ("Technology", "own"),
    "info.tech.tab.achievements": ("Achievements", "own"),
    "info.tech.tab.colony": ("Colony", "own"),
    "info.tech.tab.weapons": ("Weapons", "own"),
    "info.tech.tab.equipment": ("Equipment", "own"),
    "info.tech.none": ("Nothing researched in this group yet.", "own"),
    "info.missing": (
        "The game's own words for this page are not extracted on this "
        "computer. Run: python tools/billtext_extract.py, "
        "tools/help_extract.py, tools/infotext_extract.py", "own"),
})
# The chart's labels: " BC INCOME", then BUILDINGS … LEADERS (billtext 19-25).
for _k, _w in enumerate(("income", "buildings", "freighters", "ships",
                         "spies", "tribute", "leaders")):
    TEXTS[f"info.chart.label.{_w}"] = (_bill(19 + _k), "moo2")
# The Reference: the category names (ESTRINGS 0x294.., estrings.cpp:130-145)
for _i in range(1, 17):
    TEXTS[f"info.reference.category.{_i}"] = (_est(0x293 + _i), "moo2")
# The governments (ESTRINGS 0x27C.., estrings.cpp:99-106) and the traits
# (RACESTUF, loader.cpp:104-128).
for _i in range(8):
    TEXTS[f"info.races.gov.{_i}"] = (_est(0x27C + _i), "moo2")
for _i in range(32):
    TEXTS[f"info.races.trait.{_i}"] = (_trait(_i), "moo2")
# The Tech Review's group names (BILLTEX2 0-25) and application names.
for _i in range(26):
    TEXTS[f"info.tech.group.{_i}"] = (_group(_i), "moo2")
for _i in range(212):
    TEXTS[f"info.tech.app.{_i}.name"] = (_app(_i), "moo2")
# HELP.LBX: every record the Info screen reads (0-211 the applications'
# descriptions, 212-227 the "How to?" pages, up to 240 the topic lists'
# ids), and every topic-list entry by its record id.
for _i in range(241):
    TEXTS[f"info.reference.{_i}.title"] = (_help(_i, 0), "moo2")
    TEXTS[f"info.reference.{_i}.body"] = (_help(_i, 1), "moo2")
    TEXTS[f"info.topic.{_i}"] = (_topic(_i), "moo2")
