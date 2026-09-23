"""The research selection's offered rows, reconstructed (decision 25).

`TECH::Init_Entry_Data_` (tech.cpp:580-682) builds the eight category
entries the research screen shows. Every input it uses is either already
on the wire inside `s_player` — `tech_fields`, `tech_applications`,
`current_research_field` — or a static table in orion2re's source. So
the list is reconstructed here rather than asked for over the wire, and
decision 25's condition holds: the data carries its own validation.
`validate_against_fields` is that validation, and the screen runs it on
every entry.

WHAT WAS IN THE WAY, AND WHAT MOVED IT

`doc/research_screen_stop1.md` §1 found the categories and the offered
field reconstructible, and the choice ROWS not, for two named reasons.
Work order 130 C addressed both rather than routing around them:

1. **`s_tech_field_data.tech[4]` is all zeros in techdata.cpp** and is
   filled at runtime (techinit.cpp:444-474). It is not a table to read;
   it is a DERIVATION, and a pure one: walk
   `_technology_applications[]` in ascending app id and drop each app
   into the first free slot of its own field, skipping the three
   sentinel fields. `field_applications()` is that loop. What had to be
   transcribed is the app -> field column, not the slots.

2. **`tech_applications[212]` @379 had no verified source.** It has two
   now (decision 23): orion2re's headers compiled with their own
   `#pragma pack(1)` put it at 379 with `sizeof(s_player) == 0xf0e`,
   the assert in sizes.h:21 — `tools/struct_header_check.py` runs that
   on every suite — and a live read against the game's own screen.

THE TABLES BELOW ARE TRANSCRIPTIONS, and every one of them has a
checker: `tools/research_cost_check.py` reads all four out of the
source and fails on any difference. A hand-copied table without a
checker is the nebula sizes again (decision 36).

Costs are NOT here. `core/research.py` owns the cost table and the
turn arithmetic, and it stays the one home for them.
"""

from core.livefields import live_field, rect

#: Which technology CATEGORY each of the eight panel entries shows, in
#: panel order (`TECH::_entry_to_group`, tech.cpp:42).
ENTRY_TO_GROUP = (4, 2, 6, 8, 7, 1, 3, 5)

#: The first technology field of each category, indexed by the category
#: id above (`MOX::_first_field_in_group`, mox.cpp:103). Index 0 is the
#: "no category" sentinel and the walk never starts there.
FIRST_FIELD_IN_GROUP = (0, 18, 55, 57, 29, 7, 22, 28, 10, 74)

#: `TECHDATA::_technology_fields[i].next_field_id` (techdata.cpp:319ff).
#: The chain a category is walked along; 0 ends it.
NEXT_FIELD = (
    0, 34, 47, 21, 3, 41, 32, 36, 11, 2, 73, 67,
    6, 46, 25, 60, 65, 70, 1, 8, 62, 20, 9, 5,
    33, 24, 61, 72, 56, 4, 17, 66, 82, 49, 35, 44,
    45, 38, 40, 69, 76, 13, 58, 12, 30, 27, 37, 53,
    80, 81, 48, 39, 59, 50, 16, 23, 15, 31, 78, 51,
    14, 71, 63, 19, 26, 52, 54, 42, 79, 77, 75, 68,
    64, 43, 74, 0, 0, 0, 0, 0, 0, 0, 0,
)

#: `TECHDATA::_technology_applications[i].tech_field_id` (techdata.cpp:104ff)
#: — which field each application belongs to. Three values are sentinels
#: and carry no application into a field: -1 (TECH_FIELD_INVALID), 0
#: (TECH_FIELD_STARTING_TECH) and 74 (TECH_FIELD_XENON_TECHNOLOGY).
APP_FIELD = (
    0, 49, 48, 42, 63, 73, 24, 24, 24, 36, 13, 13,
    13, 4, 20, 58, 8, 63, 12, 47, 5, 25, 3, 8,
    19, 21, 66, 62, 17, 70, 74, 11, 0, 7, 45, 64,
    61, 68, 26, 1, 29, 23, 6, 14, 25, 74, 56, 74,
    1, 67, 67, 9, 51, 71, 51, 58, 4, 7, 28, 14,
    37, 18, 70, 22, 63, 6, 4, 20, 46, 55, 31, 5,
    5, 31, 70, 32, 33, 6, 64, 16, 36, 26, 3, 42,
    30, 37, 60, 18, 38, 37, 38, 39, 6, 71, 36, 40,
    41, 41, 47, 65, 57, 57, 72, 29, 7, 39, 2, 34,
    53, 23, 49, 64, 52, 53, 15, 54, 54, 50, 40, 55,
    55, 22, 56, 74, 27, -1, 68, 52, 52, 68, 61, 16,
    3, 19, 45, 43, 60, 59, 59, 40, 59, 49, 2, 60,
    62, 0, 38, 30, 72, 47, 74, 14, 8, 74, 11, 56,
    62, 57, 15, 15, 39, 41, 1, 10, 20, 74, 0, 22,
    29, 42, 69, 26, 27, 27, 69, 25, 65, 71, 44, 21,
    66, 66, 34, 35, 48, 69, 19, 22, 16, 23, 46, 9,
    21, 17, 50, 33, 45, 72, 44, 61, 73, 74, 50, 53,
    75, 76, 77, 78, 79, 80, 81, 82,
)

#: The three sentinels of the derivation (orion2_consts.h:861, :862, :936).
FIELD_INVALID = -1
FIELD_STARTING_TECH = 0
FIELD_XENON_TECHNOLOGY = 74

#: `TECH_FIELD_BIOLOGY` (orion2_consts.h:937) — at and above this a field
#: is hyper-advanced and has exactly one application, by a switch rather
#: than by the table (`Get_Hyper_Tech_App_ID_`, tech.cpp:1063-1084).
FIELD_HYPER_FIRST = 75

#: `TECH_APP_BIOLOGY` (orion2_consts.h:849). The switch maps fields
#: 75..82 to applications 204..211 one for one, so it is this offset and
#: not eight cases — asserted by the checker against the switch itself.
APP_HYPER_FIRST = 204

#: The last hyper-advanced field (`TECH_FIELD_SOCIOLOGY`,
#: orion2_consts.h:944) — the switch's last case, and with
#: FIELD_HYPER_FIRST the extent this module claims the offset covers.
FIELD_COUNT_HYPER_LAST = 82

#: The six fields for which EVERY application counts as the chosen one
#: — `TECHDATA::_starting_tech_field_ids` (techdata.cpp:548), and the
#: same six ids `Display_Entry_Text_` tests one by one at tech.cpp:668
#: (0x37, 0x39, 0x1D, 0x16, 0x1C, 0x17) and `Draw_Little_Arrow_` again
#: at :756. A player researching one of them gets all of its
#: applications, so the original marks all of its rows.
#:
#: Transcribed, and `tools/research_cost_check.py` reads the array out
#: of the source and fails on any difference — a hand-copied table
#: without a checker is the nebula sizes again (decision 36).
ALL_APPLICATIONS_FIELDS = (29, 55, 22, 57, 28, 23)

#: A field is OFFERABLE at status 2 (tech.cpp:591); 3 is researched
#: (`core.research.STATUS_RESEARCHED`).
FIELD_STATUS_OFFERABLE = 2

#: An application may be picked at status 1
#: (`TECH_RESEARCH_STATUS_AVAILABLE`, orion2_consts.h:1323).
APP_STATUS_AVAILABLE = 1

#: The row rectangle inside an entry, as `Init_Entry_Data_` adds it:
#: `(x, y1[k] + y + 21) .. (x + 218, y2[k] + y + 21)` (tech.cpp:30-32,
#: :607-615). Row 0 is 34 px tall, rows 1-3 are 15.
ROW_Y1 = (0, 34, 49, 64)
ROW_Y2 = (33, 48, 63, 78)
ROW_X_SPAN = 218
ROW_Y_BASE = 21

#: Entry origins, (x, y) per panel entry, HIWORD y / LOWORD x out of
#: `_tech_select_pos` and `_tech_change_pos` (tech.cpp:20-28, :412-413).
#: Select mode sits 81 px right of change mode, which is the difference
#: between the two panel origins (161 and 80).
ENTRY_POS_SELECT = ((176, 30), (403, 31), (176, 135), (403, 135),
                    (176, 240), (403, 240), (176, 347), (403, 347))
ENTRY_POS_CHANGE = ((95, 30), (322, 31), (95, 135), (322, 135),
                    (95, 240), (322, 240), (95, 347), (322, 347))

#: Where `Display_Entry_Text_` puts an entry's three kinds of text
#: (tech.cpp:683-738), relative to the entry origin:
#:   the cost string  right-aligned at (x + 212, y + 2), font style 3
#:   the field name   at (x, y + 21), squeezed into 218 px, style 4
#:   an app name k    at (x + 10, y + 21 + _app_name_y[k]), 208 px
#: `_app_name_y` is tech.cpp:34. Note what this makes row 0: its
#: rectangle starts at y + 21, the same line the FIELD NAME is printed
#: on, and its own label sits 19 px below — which is why row 0 is 34 px
#: tall and the others 15.
COST_DX, COST_DY = 212, 2
FIELD_NAME_DX, FIELD_NAME_DY = 0, 21
FIELD_NAME_WIDTH = 218
APP_LABEL_DX = 10
APP_LABEL_WIDTH = 208
APP_NAME_Y = (19, 34, 49, 64)

#: THE DRAWN BAND'S HEIGHT, and it is DERIVED from the table above
#: rather than typed: rows 1..3 are already exactly this tall
#: (`ROW_Y2[1] - ROW_Y1[1] + 1` = 15), which is the pitch of
#: `APP_NAME_Y`. Only row 0's rectangle is taller, because it swallows
#: the FIELD NAME's line — and that is a CLICK area, not a mark.
#:
#: WHERE the band sits is not here: it is centred on the text, which
#: takes the rendered font, so `core/researchband.py` owns it and this
#: module owns only the height. There is no native rectangle for it —
#: the one that used to be here hung the band's top edge on the
#: label's top edge, and Data saw the words clinging to the ceiling.
BAND_H = ROW_Y2[1] - ROW_Y1[1] + 1

#: The maximum rows one entry can show — `tech[4]` has four slots, and
#: the placeholder row uses one of them.
MAX_ROWS = 4


class Entry:
    """One category panel: its field, its rows, and where they are.

    `field` is 0 for a category with nothing to offer. Such an entry is
    still drawn as an empty panel and still has an entry-block field on
    the wire, but it has no rows and no radio button — which is the
    source of the radio index skew in `doc/tech_change_reading.md` §2.4.
    """

    __slots__ = ("index", "group", "field", "apps", "x", "y",
                 "placeholder")

    def __init__(self, index, group, field, apps, x, y, placeholder):
        self.index = index
        self.group = group
        self.field = field
        self.apps = tuple(apps)
        self.x = x
        self.y = y
        #: True when the single row is billtext.lbx message 62, "no
        #: available application", which the original shows with app id
        #: 0 — a row that exists and cannot be chosen.
        self.placeholder = placeholder

    @property
    def offered(self):
        """True when this entry shows a field at all."""
        return self.field != 0

    def row_rect(self, row):
        """The row's 640x480 rectangle, as the original adds the field.

        ONE FUNCTION for drawing, hover and hit-testing (decision 5).
        The HD screen scales this rect; it never recomputes it.
        """
        if not 0 <= row < len(self.apps):
            raise IndexError(f"entry {self.index} has {len(self.apps)} "
                             f"rows, asked for {row}")
        return (self.x,
                self.y + ROW_Y_BASE + ROW_Y1[row],
                self.x + ROW_X_SPAN,
                self.y + ROW_Y_BASE + ROW_Y2[row])

    def block_rect(self):
        """The entry's BLOCK rectangle (tech.cpp:225-231).

        All eight exist whether or not the category offers anything —
        the original adds the field and draws an empty panel for a
        category with nothing to offer — so this is both the field the
        reconstruction is validated against AND the box the HD panel
        draws. One home for it, because two rectangles for one thing is
        how a box and its hit test come apart (decision 5).
        """
        return (self.x + BLOCK_DX1, self.y + BLOCK_DY1,
                self.x + BLOCK_DX2, self.y + BLOCK_DY2)

    def panel_box(self, margin):
        """The box HD DRAWS for this entry: its rows, plus a margin.

        **NOT `block_rect`.** That is the game's own entry-block FIELD,
        a transcription, and it is 3 px narrower than the rows it
        contains (`x - 2 .. x + 215` against `x .. x + 218`) and starts
        3 px above the field name. Drawing it put the name on the box's
        top edge and let the hover band run past its right edge — which
        is what Data saw on the live panel (work order 166, points 3
        and 4).

        The original has no such box: its panels are painted into the
        TECHSEL artwork, and where the art's edges are, nobody here can
        read. So the drawn box is OURS (decision 53 — a rule we chose
        is Data's), and the honest shape for it is the CONTENT plus a
        margin, so that every transcribed anchor keeps its place and
        only the thing nobody transcribed moves.
        """
        return (self.x - margin,
                self.y + ROW_Y_BASE - margin,
                self.x + ROW_X_SPAN + margin,
                self.y + ROW_Y_BASE + ROW_Y2[-1] + margin)

    def band_span(self):
        """The band's x span, which is the row's own and transcribed.

        The y is not here — see `BAND_H` and `core/researchband.py`.
        """
        return self.x, self.x + ROW_X_SPAN

    def cost_anchor(self):
        """Where the "N RP" string ENDS — it is printed right-aligned."""
        return (self.x + COST_DX, self.y + COST_DY)

    def field_name_anchor(self):
        """(x, y, max width) of the field name (tech.cpp:700)."""
        return (self.x + FIELD_NAME_DX, self.y + FIELD_NAME_DY,
                FIELD_NAME_WIDTH)

    def app_label_anchor(self, row):
        """(x, y, max width) of one row's application name.

        Inside `row_rect(row)` but not at its top for row 0: the field
        name occupies that line (tech.cpp:735, :492).
        """
        if not 0 <= row < len(self.apps):
            raise IndexError(f"entry {self.index} has {len(self.apps)} "
                             f"rows, asked for {row}")
        return (self.x + APP_LABEL_DX,
                self.y + ROW_Y_BASE + APP_NAME_Y[row],
                APP_LABEL_WIDTH)

    def __repr__(self):
        return (f"Entry(index={self.index}, group={self.group}, "
                f"field={self.field}, apps={self.apps}, "
                f"placeholder={self.placeholder})")


def field_applications():
    """{field id: (app id, ...)} — orion2re's runtime `tech[4]`.

    A transcription of techinit.cpp:444-474: every application in
    ascending id order goes into the first free slot of its own field.
    The three sentinel fields take none. The original aborts the game
    when a fifth application wants a slot ("tech has too many apps");
    here that is an assertion, because it would mean the transcribed
    table and the engine's have diverged, and silently dropping the
    fifth would hide exactly that.
    """
    slots = {}
    for app, field in enumerate(APP_FIELD):
        if field in (FIELD_INVALID, FIELD_STARTING_TECH,
                     FIELD_XENON_TECHNOLOGY):
            continue
        row = slots.setdefault(field, [])
        if len(row) >= MAX_ROWS:
            raise AssertionError(
                f"application {app} is the fifth for field {field} — "
                f"APP_FIELD disagrees with techdata.cpp, which "
                f"tools/research_cost_check.py would have caught")
        row.append(app)
    return {f: tuple(a) for f, a in slots.items()}


def hyper_application(field):
    """The one application of a hyper-advanced field (tech.cpp:1063)."""
    return APP_HYPER_FIRST + (field - FIELD_HYPER_FIRST)


def offered_field(tech_fields, group, current_field):
    """The field a category offers, or 0 (tech.cpp:587-600).

    The walk TESTS the chain's first field before advancing, so a
    category whose first field is already offerable never steps.
    `current_field` is excluded — in select mode the game has zeroed
    it by the time this runs (tech.cpp:104-105), and in change mode it
    zeroes it around the call, so passing 0 gives change mode's list.
    """
    field = FIRST_FIELD_IN_GROUP[group]
    if field == 0:
        return 0
    while True:
        if (tech_fields[field] == FIELD_STATUS_OFFERABLE
                and current_field != field):
            return field
        field = NEXT_FIELD[field]
        if field == 0:
            return 0


def offered_rows(field, tech_applications, apps_by_field=None):
    """(app ids, placeholder) for one offered field (tech.cpp:602-652).

    Below the hyper-advanced boundary the rows are those of the field's
    four slots the player may still pick. A field with none still shows
    ONE row — billtext message 62, app id 0 — because the original adds
    a field for it, so the wire has a rectangle there and a
    reconstruction without it would be one row short.
    """
    if field >= FIELD_HYPER_FIRST:
        return (hyper_application(field),), False
    slots = (apps_by_field or field_applications()).get(field, ())
    rows = tuple(a for a in slots
                 if tech_applications[a] == APP_STATUS_AVAILABLE)
    if not rows:
        return (0,), True
    return rows, False


def reconstruct(tech_fields, tech_applications, current_field=0,
                select_mode=True):
    """The eight entries the screen would show, in panel order.

    `tech_fields` and `tech_applications` come straight out of the
    player record on the wire. Returns eight `Entry` objects; the ones
    with `field == 0` are the categories with nothing left to offer.
    """
    positions = ENTRY_POS_SELECT if select_mode else ENTRY_POS_CHANGE
    apps_by_field = field_applications()
    entries = []
    for index, group in enumerate(ENTRY_TO_GROUP):
        field = offered_field(tech_fields, group, current_field)
        x, y = positions[index]
        if field == 0:
            entries.append(Entry(index, group, 0, (), x, y, False))
            continue
        apps, placeholder = offered_rows(field, tech_applications,
                                         apps_by_field)
        entries.append(Entry(index, group, field, apps, x, y, placeholder))
    return entries


# ── The validation the data provides (decision 25) ────────────────────
#
# A reconstruction without a validation the data itself carries "is a
# guess with extra steps". This is that validation, and it is not a
# test: the SCREEN runs it every time it is entered, and hands over to
# the fallback view when it fails (work order 130 C). A list HD cannot
# vouch for is not drawn.

#: `_g_scrn_x` per mode (tech.cpp:146-147, :170-171). `_g_scrn_y` is 0
#: in both.
PANEL_ORIGIN_SELECT = 161
PANEL_ORIGIN_CHANGE = 80

#: The entry BLOCK field each entry gets, offered or not
#: (tech.cpp:225-231): `(x - 2, y + 18, x + 215, y + 99)`.
BLOCK_DX1, BLOCK_DY1, BLOCK_DX2, BLOCK_DY2 = -2, 18, 215, 99

#: `_tech_button_pos` (tech.cpp:38-43), the radio of entry i at
#: `(pos[2i] + _g_scrn_x, pos[2i+1] + _g_scrn_y)`. Only non-empty
#: entries get one (`Setup_Entry_Buttons_`, tech.cpp:497-513), which is
#: the radio index skew of doc/tech_change_reading.md §2.4.
RADIO_POS = ((21, 30), (248, 31), (21, 135), (248, 135),
             (21, 240), (248, 240), (21, 347), (248, 347))

TYPE_BUTTON = 0
TYPE_RADIO = 1
TYPE_HIDDEN = 7
FULL_SCREEN_RECT = (0, 0, 639, 479)


def expected_fields(entries, select_mode=True):
    """The field list the reconstruction says the game must have built.

    In the order `_Tech_Select_` adds them (tech.cpp:206-250):

      [0]          change mode only: the exit button
      then         every offered entry's rows, entry by entry, row by
                   row — `Init_Entry_Data_`
      then         eight entry blocks, one per entry, EMPTY ONES TOO
      then         one radio per non-empty entry
      last         a whole-screen hidden field

    Returns a list of `(kind, field_type, rect)`, rect None where the
    rectangle is not predictable (the exit button's, whose end comes
    from the art — `doc/tech_change_reading.md` §2 has it as NOT
    SETTLED).

    **SLOT 0 IS NOT IN THIS LIST, and it used to be.** `Clear_Fields_`
    leaves a dummy at slot 0 (fields.cpp:201) and `SerializeFields`
    sends it (ext_api.cpp:326), so when this function was written in
    work order 130 C the wire carried it and the reconstruction had to
    expect it. Work order 142 B then dropped it ONCE, in
    `core.game_state.parse_fields` — "a labelling rule without a check
    is an intention, and it decays" — and this list was not moved with
    it. The count was one too high from that day, so
    `validate_against_fields` failed on every real snapshot and the
    select screen handed over to the fallback every time it was
    entered.

    **The check did not catch it because the check built its stand-in
    FROM THIS FUNCTION**, so the dummy sat on both sides of the
    comparison. That is work order 131 part E's own lesson — a test
    double written by the same hand as the code shares its mistakes —
    and it is why one live run in work order 165 part D found what
    every green run since 19 September had not.
    """
    origin = PANEL_ORIGIN_SELECT if select_mode else PANEL_ORIGIN_CHANGE
    want = []
    if not select_mode:
        want.append(("exit", TYPE_BUTTON, None))
    for entry in entries:
        for row in range(len(entry.apps)):
            want.append((f"row {entry.index}.{row}", TYPE_HIDDEN,
                         entry.row_rect(row)))
    for entry in entries:
        want.append((f"block {entry.index}", TYPE_HIDDEN,
                     entry.block_rect()))
    for entry in entries:
        if entry.offered:
            x, y = RADIO_POS[entry.index]
            want.append((f"radio {entry.index}", TYPE_RADIO,
                         (x + origin, y, None, None)))
    want.append(("whole screen", TYPE_HIDDEN, FULL_SCREEN_RECT))
    return want


def validate_against_fields(entries, fields, select_mode=True):
    """Problems, as sentences. Empty means the two agree.

    Every sentence names what disagreed, because this is what the
    screen logs before it hands over to the fallback, and "the
    reconstruction failed" is not something anyone can act on.

    The radio's END is not checked: its rectangle comes from the button
    art, whose size the source does not give (§2, NOT SETTLED). Its
    ORIGIN is checked, and so is its type and its count, which is what
    the index skew would break.
    """
    fields = list(fields or [])
    want = expected_fields(entries, select_mode)
    problems = []
    if len(fields) != len(want):
        problems.append(
            f"the game's list has {len(fields)} fields, the "
            f"reconstruction wants {len(want)} "
            f"({sum(len(e.apps) for e in entries)} rows over "
            f"{sum(1 for e in entries if e.offered)} offered categories)")
        return problems
    for got, (name, ftype, want_rect) in zip(fields, want):
        if ftype is not None and got.field_type != ftype:
            problems.append(
                f"{name}: the game has field type {got.field_type} "
                f"where the reconstruction wants {ftype}")
            continue
        if want_rect is None:
            continue
        got_rect = rect(got)
        if want_rect[2] is None:          # origin-only (the radios)
            if got_rect[:2] != want_rect[:2]:
                problems.append(
                    f"{name}: the game has it at {got_rect[:2]}, the "
                    f"reconstruction at {want_rect[:2]}")
        elif got_rect != want_rect:
            problems.append(
                f"{name}: the game has {got_rect}, the reconstruction "
                f"{want_rect}")
    return problems


def row_field(fields, entry, row, select_mode=True):
    """The LIVE field for one row, looked up by shape. None if absent.

    By shape and never by a remembered index — the rule work order 128 C
    put into `core.livefields.live_field`, which this calls rather than
    carrying a second copy of it.
    """
    return live_field(fields, {"field_type": TYPE_HIDDEN,
                               "rect": entry.row_rect(row)})
