"""Which dialog of `LOADSAVE::_Game_Popup_` is up — read off FIELD_LIST.

**THE DIALOG IS NOT ON THE WIRE.** The game reports SCREEN_GAME (8) for
all four dialogs, the confirmation and the warning; `MOX::_screen_data`
is not serialized (doc/game_menu_reading.md §2). What IS on the wire is
the field list each builder leaves behind, and in a single-player game
every node has its own shape (measured 14 September 2026, §4):

  menu      11  `Add_Game_Popup_Fields_` case 0, loadsave.cpp:181-203
  settings  30  case 1, :204-221
  load      16  case 2, :257-266
  save      25  case 3, :267-284
  confirm    3  `GENDRAW::Confirmation_Box_`, gendraw.cpp:172-173
  warning    2  `GENDRAW::Message_Box_Exploding_`, gendraw.cpp:105

**FIELD 0 NEVER COUNTS.** After a message box it carries the geometry
of whatever the list held before (measured: `(193,185)-(387,197)` in
the warning, `(173,62)-(388,73)` in a confirmation), so it is dropped
before any test. The shapes below are tested by TYPE, HOTKEY and SIZE,
never by index: a multiplayer menu omits LOAD and NEW (:190-193) and
every index after them moves.

Pure functions over `FieldInfo`-shaped objects, so the smoke test feeds
them the measured lists without a game.
"""

MENU = "menu"
SETTINGS = "settings"
LOAD = "load"
SAVE = "save"
CONFIRM = "confirm"
WARNING = "warning"

TYPE_BUTTON = 0      # FIELD_TYPE_BUTTON, orion2_consts.h:205
TYPE_SCROLL = 6      # FIELD_TYPE_SCROLL
TYPE_HIDDEN = 7      # FIELD_TYPE_HIDDEN
TYPE_INPUT = 11      # FIELD_TYPE_CONTINUOUS_INPUT

ESC = 0x1B
SLOTS = 10           # `for (i = 0; i < 10; ++i)`, loadsave.cpp:258, :268
OPTIONS = 13         # loadsave.cpp:211


def real(fields):
    """The list without field 0 — see the module docstring."""
    return [f for f in (fields or []) if f.index != 0]


def _size(f):
    return (f.x_end - f.x, f.y_end - f.y)


def _full_screen(f):
    return (f.x, f.y, f.x_end, f.y_end) == (0, 0, 639, 479)


def hotkey_field(fields, key, ftype=None):
    """The FIRST field carrying `key`, in list order.

    First, because that is the walk `Interpret_Keyboard_Input_` makes
    (fields.cpp:2608-2613): ESC in the menu reaches RETURN (index 6)
    before the whole-screen field (index 10), which is why the two
    leave the popup by different paths (loadsave.cpp:1234 against
    :1309).
    """
    code = ord(key) if isinstance(key, str) else key
    for f in real(fields):
        if f.hotkey == code and (ftype is None or f.field_type == ftype):
            return f
    return None


def _rows(fields, ftype, count):
    """`count` fields of one type and one size, top to bottom.

    The slot rows share a size with each other and with nothing else
    in their dialog — the body field (279x378) and the whole-screen
    field are the only other type-7 fields without a hotkey.
    """
    groups = {}
    for f in real(fields):
        if f.field_type == ftype and f.hotkey == 0 and not _full_screen(f):
            groups.setdefault(_size(f), []).append(f)
    for group in groups.values():
        if len(group) == count:
            return sorted(group, key=lambda f: (f.y, f.x))
    return []


def classify(fields):
    """The node name for a field list, or None for anything else.

    None is a real state and not an error: the first tick at screen 8
    still carries the galaxy map's list (the screen changed before
    `_Game_Popup_` cleared the fields), and a caller draws nothing for
    it rather than guessing.
    """
    rest = real(fields)
    if not rest:
        return None
    keys = {f.hotkey for f in rest}
    if (len(rest) == 2 and keys == {ord("Y"), ord("N")}
            and all(f.field_type == TYPE_HIDDEN for f in rest)):
        return CONFIRM
    if (len(rest) == 1 and rest[0].hotkey == ESC
            and rest[0].field_type == TYPE_HIDDEN and _full_screen(rest[0])):
        return WARNING
    button = lambda k: hotkey_field(fields, k, TYPE_BUTTON)  # noqa: E731
    inputs = [f for f in rest if f.field_type == TYPE_INPUT]
    if len(inputs) == SLOTS and button("S") and button("C"):
        return SAVE
    if button("L") and button("C") and len(_rows(fields, TYPE_HIDDEN,
                                                 SLOTS)) == SLOTS:
        return LOAD
    if button("A") and len(_rows(fields, TYPE_HIDDEN, OPTIONS)) == OPTIONS:
        return SETTINGS
    scrolls = [f for f in rest if f.field_type == TYPE_SCROLL]
    if (button("S") and button("Q") and button("O") and button(ESC)
            and len(scrolls) == 2):
        return MENU
    return None


def slot_rows(fields):
    """Load: the ten slot rows (`saved_game_fields`, loadsave.cpp:263)."""
    return _rows(fields, TYPE_HIDDEN, SLOTS)


def save_inputs(fields):
    """Save: the ten name inputs (`saved_game_fields`, loadsave.cpp:274)."""
    rows = [f for f in real(fields) if f.field_type == TYPE_INPUT]
    return sorted(rows, key=lambda f: (f.y, f.x)) if len(rows) == SLOTS else []


def save_strips(fields):
    """Save: the ten hidden strips under the names (loadsave.cpp:279).

    Activating one starts editing that slot's name WITHOUT a mouse —
    `_input_field_active = 1` and the description copied into the edit
    string (loadsave.cpp:512-520) — which is what lets a name reach the
    game through keys alone.
    """
    return _rows(fields, TYPE_HIDDEN, SLOTS)


def option_toggles(fields):
    """Settings: the thirteen LABEL fields, top to bottom.

    Each option has two hidden fields, the checkbox and the label, and
    either one toggles it (`option_names[i] == input ||
    option_toggles[i] == input`, loadsave.cpp:434). The label is the
    wider of the pair and is what HD activates.
    """
    groups = {}
    for f in real(fields):
        if f.field_type == TYPE_HIDDEN and f.hotkey == 0 \
                and not _full_screen(f):
            groups.setdefault(_size(f), []).append(f)
    pairs = [g for g in groups.values() if len(g) == OPTIONS]
    if len(pairs) != 2:
        return []
    labels = max(pairs, key=lambda g: _size(g[0])[0])
    return sorted(labels, key=lambda f: f.y)


def esc_field(fields):
    """What an ESC key reaches, or None where it reaches nothing.

    The confirmation has no ESC field and its loop waits for YES or NO
    (gendraw.cpp:212) — measured: 25 frames after ESC, list unchanged.
    """
    return hotkey_field(fields, ESC)


def signature(fields):
    """The list's shape WITHOUT field 0, for "has the dialog changed"."""
    return tuple((f.x, f.y, f.x_end, f.y_end, f.field_type, f.hotkey)
                 for f in real(fields))
