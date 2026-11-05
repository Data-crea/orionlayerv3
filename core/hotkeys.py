"""The player's hotkeys — HD EXTENSION `hotkey_remap` (work order 364).

MOO2 has fixed hotkeys. The GAME menu's OrionLayer window ("Hotkeys" on the
SYSTEM tab, `screens/game_menu/gmkeys.py`) lists the keys a screen answers
and lets the player give an action another key. The game knows nothing of it:
a key the player pressed is changed into the ORIGINAL's key before any screen
sees it (`translate`, called by `Dispatcher.route_key_event`), so every
screen and the one rule that passes keys to the engine (`core/keyfwd.py`)
act exactly as for the original key. Nothing is sent to the engine for a
choice; it lives in the player's settings (`hotkey_map`).

WHAT CAN BE CHANGED: a single letter or digit with no Ctrl, Alt or Meta
held. The F keys and the Alt combinations stay as they are: the engine
expects fixed codes for them (`keyfwd.ENGINE_FKEYS`, open fix 89) and HD's
own keys (F3, F7, F8, F11, F12 — `core/hdkeys.py`) are taken before any
screen.

WHAT IS LISTED: the keys whose effect `dev:doc/briefs/230-keys.md` names
(the original's `file.cpp:line` stands there); a screen's other keys keep
working as ever and are simply not offered. UNVERIFIED `table_covers`: the
table is not every key of every screen.

THE RULE FOR A CHOICE: a key is free when no other action of the screen has
it — neither as its original key nor as its own choice. A key that is taken
is refused, never swapped, so no choice can silently undo another one. The
original key of an action that has another key does nothing on that screen
(the player gave it away); it comes back with RESET.

NO CHANGE WHILE TYPING OR IN A DIALOG: a name typed into a field must read as
typed, and a dialog that takes keys itself (the tax rate's digits, a box's
Y and N) must get the key that was pressed. So a key is never changed while
the engine edits a text field (open fix 88, `keyfwd.editing`), an HD text
field has the focus, or the screen says `hotkeys_suspended()` (its dialog is
open).

KEYS THAT HAVE ANOTHER JOB: a screen answers keys that are not in the table
(`RESERVED`: the galaxy map's 0, the colony's B and C, the build queue's Q, B
and the digits, combat's H). They cannot be given to an action: the key
would stop doing its own job. UNVERIFIED `reserved_covers`: the lists are the
keys the sources name; a screen may answer more.

INVENTION `typing_guard`: the original has no such rule; it has no remapping.
"""
import pygame

SETTING = "hotkey_map"

#: screen -> ((original key, action id, English label), ...). The keys and
#: their effect are `230-keys.md`'s, the order is the original's.
TABLE = {
    "galaxy_map": (
        ("g", "game_menu", "Game menu"), ("t", "next_turn", "Next turn"),
        ("c", "colonies", "Colonies"), ("p", "planets", "Planets"),
        ("f", "fleets", "Fleets"), ("l", "leaders", "Leaders"),
        ("r", "races", "Races"), ("i", "info", "Info")),
    "combat": (
        ("a", "auto", "Auto"), ("s", "scan", "Scan"),
        ("b", "board", "Board"), ("r", "retreat", "Retreat"),
        ("w", "wait", "Wait"), ("d", "done", "Done"),
        ("t", "end_turn", "End turn"), ("z", "super_fast", "Super fast auto"),
        ("o", "options", "Options"),
        ("c", "centre", "Centre on the acting ship")),
    "colony": (
        ("l", "leaders", "Leaders"), ("a", "autobuild", "Autobuild")),
    "build_queue": (
        ("r", "refit", "Refit"), ("d", "design_mode", "Design mode"),
        ("e", "repeat_mode", "Repeat mode")),
    "custom_race": (
        ("a", "accept", "Accept"), ("c", "default", "Default")),
    # the ids are `racesgeom.BUTTONS`' and `ldrgeom.BUTTONS`' names, which
    # the check holds to the key (racescrn.cpp:338-372, officer.cpp:2954-3021)
    "races": (
        ("a", "audience", "Audience"), ("r", "report", "Report"),
        ("i", "ignore", "Ignore"), ("d", "war", "Declare war")),
    "planets": (
        ("1", "enemy", "No Enemy Presence"), ("2", "gravity", "Normal Gravity"),
        ("3", "hostile", "Non-Hostile Environment"),
        ("4", "minerals", "Mineral Abundance"), ("5", "range", "Planets In Range"),
        ("c", "colony", "Send Colony Ship"), ("o", "outpost", "Send Outpost Ship")),
    "fleets": (
        ("s", "btn_scrap", "Scrap"), ("a", "btn_all", "All"),
        ("l", "btn_leaders", "Leaders"), ("r", "btn_relocate", "Relocate"),
        ("u", "btn_support", "Support"), ("c", "btn_combat", "Combat")),
    "leaders": (
        ("c", "tab_colony", "Colony leaders"), ("s", "tab_ship", "Ship leaders"),
        ("h", "hire", "Hire"), ("p", "pool", "Pool"),
        ("d", "dismiss", "Dismiss"), ("x", "cancel", "Cancel hire")),
    # the ids are `layout.json`'s sort keys, the keys its hotkeys
    # (colsum.cpp:377-383)
    "colony_summary": (
        ("n", "name", "Name"), ("p", "population", "Population"),
        ("f", "food", "Food"), ("i", "industry", "Industry"),
        ("s", "science", "Science"), ("r", "producing", "Producing"),
        ("b", "bc", "BC")),
}

#: screen -> the letters and digits the screen answers that are NOT in the
#: table (`230-keys.md`, the screens' own `KEYS`): not offered to an action.
RESERVED = {"galaxy_map": "0", "colony": "bc", "build_queue": "qb0123456789",
            "combat": "h",
            # Q, C, T and the digits (colsum.cpp:356-371), Z a redraw key
            # (:391; UNVERIFIED, a mod's string file gives the letter)
            "colony_summary": "qctz0123456789"}

#: The screens' names for the window's selector, in the order it steps.
SCREEN_ORDER = tuple(TABLE)
SCREEN_LABELS = {"galaxy_map": "Galaxy map", "combat": "Combat",
                 "colony": "Colony", "build_queue": "Build queue",
                 "custom_race": "Custom Race", "races": "Races",
                 "leaders": "Leaders", "planets": "Planets",
                 "fleets": "Fleets", "colony_summary": "Colony Summary"}

BLOCKING_MODS = pygame.KMOD_ALT | pygame.KMOD_CTRL | pygame.KMOD_META


def can_bind(char):
    """A key that may be given to an action: one letter or digit."""
    return isinstance(char, str) and len(char) == 1 and \
        char.isascii() and char.isalnum() and char == char.lower()


def _settings(app):
    return getattr(app, "user_settings", None)


def _map(app):
    settings = _settings(app)
    raw = settings.get(SETTING) if settings is not None else None
    return raw if isinstance(raw, dict) else {}


def reserved(screen_name, char):
    return char in RESERVED.get(screen_name, "")


def chosen(app, screen_name):
    """{original key: the player's key} for one screen: only what the rules
    allow, so a hand-edited file cannot make a key do what it must not (an
    unknown action, a key with another job, one key for two actions)."""
    entry = _map(app).get(screen_name)
    if not isinstance(entry, dict):
        return {}
    originals = {orig for orig, _i, _l in TABLE.get(screen_name, ())}
    out = {orig: mine for orig, mine in entry.items()
           if orig in originals and can_bind(mine) and mine != orig
           and not reserved(screen_name, mine)}
    # a key may be another action's original only while that action has
    # given it away, and no key serves two actions: until nothing changes,
    # because dropping one entry can orphan another
    changed = True
    while changed:
        changed, seen = False, set()
        for orig, mine in list(out.items()):
            if mine in seen or (mine in originals and mine not in out):
                del out[orig]
                changed = True
            else:
                seen.add(mine)
    return out


def key_of(app, screen_name, original):
    """The key an action answers to now."""
    return chosen(app, screen_name).get(original, original)


def entries(app, screen_name):
    """[(original key, id, label, the key now)] for one screen."""
    return [(orig, ident, label, key_of(app, screen_name, orig))
            for orig, ident, label in TABLE.get(screen_name, ())]


def _in_use(app, screen_name):
    """{key: original key of the action that has it} for one screen."""
    return {key_of(app, screen_name, orig): orig
            for orig, _i, _l in TABLE.get(screen_name, ())}


def owner(app, screen_name, char, ignoring=None):
    """The original key of the action that has `char`, or None."""
    found = _in_use(app, screen_name).get(char)
    return None if found == ignoring else found


def rebind(app, screen_name, original, char):
    """Give the action `original` the key `char`. Returns None when it was
    done, else why not: "key" (not a letter or digit), "reserved" (the
    screen answers it for another job), "taken" (another action has it)."""
    if not can_bind(char):
        return "key"
    if reserved(screen_name, char):
        return "reserved"
    if owner(app, screen_name, char, ignoring=original) is not None:
        return "taken"
    entry = chosen(app, screen_name)
    if char == original:
        entry.pop(original, None)
    else:
        entry[original] = char
    _store(app, screen_name, entry)
    return None


def reset(app, screen_name):
    _store(app, screen_name, {})


def _store(app, screen_name, entry):
    settings = _settings(app)
    if settings is None:
        return
    whole = {k: dict(v) for k, v in _map(app).items()
             if isinstance(v, dict) and v}
    if entry:
        whole[screen_name] = entry
    else:
        whole.pop(screen_name, None)
    settings.set(SETTING, whole or None)


def _typing(screen):
    """INVENTION `typing_guard`: a name being typed must not be changed."""
    from core import keyfwd
    state = getattr(getattr(screen.app, "client", None), "state", None)
    if state is not None and keyfwd.editing(state):
        return True
    return any(getattr(v, "focused", False) and hasattr(v, "handle_key_event")
               for v in vars(screen).values())


def translate(screen, event):
    """The event the screen should see: the key the player pressed changed
    into its action's original key, the event itself where nothing is
    chosen, or None where the pressed key is an original key the player gave
    away."""
    name = getattr(screen, "SCREEN_NAME", None)
    if name not in TABLE or event.type != pygame.KEYDOWN:
        return event
    mods = getattr(event, "mod", 0)
    if mods & BLOCKING_MODS or not 32 <= event.key < 127:
        return event
    mapped = chosen(screen.app, name)
    if not mapped or _typing(screen):
        return event
    suspended = getattr(screen, "hotkeys_suspended", None)
    if callable(suspended) and suspended():
        return event                       # a dialog of the screen's own
    pressed = chr(event.key)
    for orig, mine in mapped.items():
        if mine == pressed:
            char = orig.upper() if mods & pygame.KMOD_SHIFT else orig
            return pygame.event.Event(pygame.KEYDOWN, {
                "key": ord(orig), "mod": mods, "unicode": char})
    if pressed in mapped:
        return None                       # given away: it does nothing now
    return event
