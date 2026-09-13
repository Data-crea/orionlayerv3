"""output_panel — the original's scan box for the SELECTED colony.

A TRANSCRIPTION, and the marking is worth restating because it was
briefly the opposite: decision 43 called this panel an HD EXTENSION on
the strength of a word grep and is WITHDRAWN. The original draws all
of it. `COLSUM::Draw_Colony_Scan_Info_` (colsum.cpp:1155) fills the
native box at (13, 354, 80, 88) with a formatted paragraph over
`ESTRINGS::E_Strings_(74)` carrying seven values (colsum.cpp:1196-1205)
and, from native x 106, a column of production rows plus morale
(colsum.cpp:1171-1176). That box is where `output_panel` sits.

**Its own module rather than the end of `screen.py`.** The screen was
already well over the ~300-line guideline (decision 6); a panel that
draws eleven values from a dict is not "being a screen" in the sense
the rest of that file is. The seam is the one `colonyrows` and
`colonylist` already use: this module is handed plain dicts and knows
nothing about structs, so it cannot reach back into a record and a
spec change cannot break it silently — it breaks in one place, in
`build_rows`, where the offsets are.

**Nothing here decides what the panel says.** The labels, the value
templates, the column split and the word lists are all in
`layout.json` (decision 15), and substitution is a `replace` and never
`str.format` (decision 37): a stray brace in a translated label cannot
raise inside the render path, and an unknown placeholder is left
standing where somebody can see it rather than swallowed.

**An empty selection draws nothing.** Not a dash, not a zero, not a
label with a blank beside it. The original's box is guarded by
`_g_colony_n != -1` (colsum.cpp:1165) and is simply not drawn, and a 0
would be a value where the original has an absence — the same
distinction the sidebar makes with "--" while disconnected, reached
from the other side.

**The production rows draw the original's NET, not the record.**
`COLDRAW::Draw_Colony_Prod_Both_` (coldraw.cpp:36) computes what it
draws before it draws anything, in four branches (coldraw.cpp:73-94),
and only one of the four is `production[t]` itself. Until 4 September
2026 this panel printed the stored value and the difference was
called a subset; it is not a subset, it is a different number, and on
the reference save it differed on nine colonies of eleven. The
branches, the `(int8_t)` cast that chooses between them and the
shortage beside the value all live in `colonyrows` — this module is
handed the answers, per the seam above.

The deviations this panel still carries — imports and the secondary
group not drawn, and morale as a number where the original draws
sprites — are stated in `layout.json` under
`output._deviation_note`, with what it would take to undo each. A
third is gone: BC was not drawn until the geometry settled it.
`y_pos` starts at 349 and steps 18 (colsum.cpp:1170-1173) and morale
is at 421 (colsum.cpp:1176), so there is room above it for exactly
four production rows — 349, 367, 385, 403 — and not three, which
agrees with `ECON_COUNT` being 4 without having to take the constant
on trust.
"""
import collections

import pygame

from core import palette
from core import textfit

from .colonyempire import format_value
from .colonyrows import ECON_BC, ECON_FOOD, ECON_INDUSTRY, ECON_RESEARCH

LABEL_COLOR = palette.col("colony_summary", "label", (140, 155, 190))
VALUE_COLOR = palette.col("colony_summary", "value", (220, 228, 245))
EMPTY_COLOR = palette.col("colony_summary", "nav_text_dim",
                          (104, 116, 142))
#: The shortage marker. `COLONY::Short_Anims_` (colony.cpp:2192) is
#: the import sprite outlined in palette index 0xED — a colour this
#: project cannot resolve to RGB, because the palette comes from the
#: player's own LBX and is not shipped. So the screen's existing
#: `warn` is reused rather than a second red invented beside it: it
#: is the same red the sidebar reddens a negative Income with, which
#: IS the original's (see `colonyempire._red_note`).
SHORTAGE_COLOR = palette.col("colony_summary", "warn", (214, 88, 74))
#: The line between two rows — an HD EXTENSION, see `render` and
#: `output._separator_note`. The skin's, like every other colour here.
SEPARATOR_COLOR = palette.col("colony_summary", "output_separator",
                              (38, 50, 76))
#: The name heading above the paragraph — the header's own colour,
#: Data's #79A8E8, because it heads a panel the way the column words
#: head the list. HD EXTENSION, brief 97; no code default (decision 14).
HEADING_COLOR = palette.require("colony_summary", "header_text")

#: Which row id wears which icon file. The morale row is not here: its
#: mask depends on the value and `colonyrows.morale_icon` decides it.
ICON_BY_ID = {"food": "food", "industry": "industry",
              "research": "research", "bc": "bc"}

#: Which panel row names which ECON slot. The ids are layout.json's
#: (decision 15) and the indices are the engine's
#: (orion2_consts.h:119-123, one home in `colonyrows`) — this map is
#: the only place the two meet, so a renamed row loses its shortage
#: rather than silently taking another row's.
ECON_BY_ID = {"food": ECON_FOOD, "industry": ECON_INDUSTRY,
              "research": ECON_RESEARCH, "bc": ECON_BC}

#: What `visible_rows` answers with. A named tuple rather than a
#: widening tuple: `shortage` is empty on most rows and a positional
#: fourth element is how a caller ends up reading the column index as
#: a string.
PanelRow = collections.namedtuple("PanelRow",
                                  "label value column shortage icon")


def fill_template(template, values):
    """`{key}` -> value, by replace and never by `str.format`.

    Decision 37. The second copy of this shape in the tree — the
    first is `colonylist._detail_text`, which fills the per-row
    detail line the same way. The rule is that the THIRD copy is the
    signal to extract, so this note is here to make the third one
    obvious rather than to apologise for the second.

    An unknown placeholder survives into the drawn string. That is
    deliberate: a label that renders `{gravity}` on screen says which
    key is missing, and one that renders nothing says only that
    something is wrong.
    """
    for key, value in values.items():
        template = template.replace("{" + key + "}", str(value))
    return template


def _drawn(row, econ):
    """The net the original would draw on one production row."""
    return (row.get("drawn_production") or (0, 0, 0, 0))[econ]


def row_shortage(row, spec):
    """The shortage for one panel row, as a NUMBER, or 0.

    0 covers three different things and deliberately does not tell
    them apart: the row is not a production row, the colony is not
    short, or the original refuses to draw a shortage there at all
    (industry, or negative imports — `colonyrows.production_shortage`
    is where that refusal is transcribed, from coldraw.cpp:152). All
    three mean the same thing here, which is that no marker is drawn.
    """
    econ = ECON_BY_ID.get(spec.get("id"))
    if econ is None:
        return 0
    return (row.get("shortage") or (0, 0, 0, 0))[econ]


def row_values(row, words, climates):
    """Every value the panel can name, keyed by its placeholder.

    Every list lookup falls back to "?" rather than raising or
    clamping. An index outside its enum means the spec moved or the
    save holds something the enum does not, and both are worth seeing
    on screen: a clamp would draw "Huge" for a value of 9 and look
    like data.
    """
    def word(table, index):
        return table[index] if 0 <= index < len(table) else "?"

    return {
        "size": word(words.get("sizes") or (), row.get("size", -1)),
        "climate": word(climates or (), row.get("climate", -1)),
        "gravity": word(words.get("gravities") or (), row.get("gravity", -1)),
        "mineral": word(words.get("minerals") or (), row.get("mineral", -1)),
        "pops": row.get("pops", 0),
        "max_pop": row.get("max_pop", 0),
        # SIGNED, through the sidebar's own formatter rather than a
        # second copy of the rule: growth is a net flow and a
        # negative one means the colony is shrinking, which is the
        # same reason Income and Food carry an explicit plus. The
        # UNIT — MOO2 counts population in thousands, so the
        # original prints "+63k" — is wording and lives in the
        # value template in layout.json (decision 15). Nothing here
        # divides or scales: see output._growth_note.
        "growth": format_value(row.get("growth", 0), signed=True),
        # THE NET, NOT THE STORED VALUE. The original computes what
        # it draws before it draws anything and only one of its four
        # branches is `production[t]` itself — see
        # `colonyrows.drawn_production`, which carries all four and
        # the (int8_t) cast that chooses between them. `production`
        # is still in the row and is still what the four SORT keys
        # read, because the original sorts on the record and not on
        # this. Falling back to `production` when the key is absent
        # would hide exactly the difference this exists to show, so
        # the fallback is a zero row.
        "food": _drawn(row, ECON_FOOD),
        "industry": _drawn(row, ECON_INDUSTRY),
        "research": _drawn(row, ECON_RESEARCH),
        "bc": _drawn(row, ECON_BC),
        "morale": row.get("morale", 0),
    }


def visible_rows(row, cfg, words, climates, only=None):
    """(label, value, column) per configured row, for one colony.

    Morale is the one row that can be present and have nothing to
    say: under Unification the original draws no marks at all, so the
    value becomes `hidden_value` — empty by default — and the LABEL
    stays. That is the shape of the original's own absence: the box is
    still there and the morale part of it is blank.

    The SHORTAGE is a second element beside the value and is empty on
    every row that has none. Empty and not "0": the original draws
    `Short_Anims_` sprites, so a colony that is not short has nothing
    on that row at all, and a zero would be a claim where the
    original has an absence — the same rule the empty selection and
    the Unification morale row follow. The wording is the template's
    (decision 15) and is filled by `replace` (decision 37); the
    decision to draw it at all is the NUMBER's, taken here, so a
    template that renders "0" cannot bring the element back.

    Split out from `render` so a smoke check can ask what the panel
    would draw without needing a surface, and so the empty-selection
    rule is one `if` in one place instead of a guard per row.

    `only` is a set of column indices, or None for all of them. It
    exists because the original's box is TWO boxes and always was —
    a formatted paragraph at native (13, 354, 80, 88) and a column of
    production rows from native x 106 (colsum.cpp:1171-1176, :1206) —
    and as of 8 September 2026 the HD screen puts them in the two
    holes the frame gives it rather than both in the right-hand one.
    The `column` field in `layout.json` already said which row
    belonged to which half; this is what reads it.
    """
    if row is None:
        return []
    values = row_values(row, words, climates)
    hidden = cfg.get("hidden_value", "")
    template = cfg.get("shortage_value", "")
    out = []
    for spec in cfg.get("rows", []):
        if only is not None and int(spec.get("column", 0)) not in only:
            continue
        text = fill_template(spec.get("value", ""), values)
        if spec.get("id") == "morale" and not row.get("morale_applies", True):
            text = hidden
        short = row_shortage(row, spec)
        # THE ICON FOLLOWS THE ROW (decision 56): a row that is listed
        # has one, including morale under Unification, whose value is
        # blank but whose label still prints.
        icon = (row.get("morale_icon") if spec.get("id") == "morale"
                else ICON_BY_ID.get(spec.get("id")))
        out.append(PanelRow(
            spec.get("label", ""), text, int(spec.get("column", 0)),
            fill_template(template, {"shortage": short}) if short > 0
            else "", icon))
    return out


def render_for(screen, surface):
    """Both halves of the scan box, into the screen's own two boxes.

    `COLSUM::Draw_Colony_Scan_Info_` (colsum.cpp:1155) is ONE
    function that fills two rectangles — the description paragraph at
    native (13, 354, 80, 88) and the production rows from native
    x 106 — so this is one call too. It lives here rather than in
    `screen.py` for the seam `colonyheader.render_for` already uses:
    the screen owns which BOX, the panel owns what goes in it.

    The climate words come from the `list` block and the other three
    lists from `words`. They are not merged into one block because
    `list.climates` already had a home and its own provenance note,
    and a second copy that agrees today is the screen-ID-map failure
    waiting to happen. A smoke check asserts the ten climate words
    appear in exactly one of the two.

    **THE MOVE'S LAST WORD WINS `planet_info` WHILE THERE IS ONE.**
    A refusal is what a player needs to read, and the original
    answers one with a blocking box HD must not reproduce
    (textbox.cpp:149, and see decision 33). It is transient; the
    paragraph comes back the moment it clears. That is a change of
    ownership rather than a collision — the panel used to owe nothing
    to the original and now owes it a paragraph.
    """
    row = screen.selected_row()
    cfg = screen._data.get("output", {})
    words = screen._data.get("words", {})
    climates = screen._data.get("list", {}).get("climates", ())
    # ── THE SURFACE PICTURE — HD EXTENSION, decision 58 ─────────
    # DEVIATION IN KIND as well: AI-generated artwork (Data's ChatGPT
    # sheet, no copyright claim). The original shows no landscape on
    # this screen. `planet_surface` is a part of `colony_panel` and says
    # where, how big and how soft (`fade_left` / `fade_right`); WHICH
    # picture is the scanned colony's climate through `colonysurfaces`
    # and the resource roots. Drawn before the rows, so a row's text
    # can never end up under it, and onto the panel base the cutout was
    # filled with, which is what the fade reveals. No selection, or no
    # tiles on this clone: no picture.
    surf_box = _box(screen, "planet_surface")
    if row is not None and surf_box is not None and surf_box.ref_rect:
        from core import imagebox
        from . import colonysurfaces
        picture = colonysurfaces.set_for(screen).get(row.get("climate"))
        if picture is not None:
            if not hasattr(screen, "_surface_cache"):
                screen._surface_cache = {}
            imagebox.render_image_box(surface, screen.layout, picture,
                                      surf_box.ref_rect, surf_box.style,
                                      screen._surface_cache)
    box = screen.box_rect("planet_output")
    if box:
        from . import colonyoutputicons
        render(surface, row, pygame.Rect(*screen.layout.rect(box)), cfg,
               words, climates, screen.layout, screen.style, only={1},
               icons=colonyoutputicons.set_for(screen, cfg))
    box = screen.box_rect("planet_info")
    if box and not screen._move.message:
        # TWO BOXES INSIDE `planet_info` — brief 95 Part C, 13 September
        # 2026. The paragraph and the disc were placed by arithmetic
        # (padding, then the disc, then a gap) and neither could be
        # dragged in F5; they are `planet_paragraph` and `planet_disc`
        # now, seated from `layout_reference.json` like every other
        # rect on this screen (`colonyplates.part_rects`). The disc box
        # is a RECT AND NOTHING ELSE: which image fills it is the
        # climate's, resolved through `colonyplanets` and the resource
        # stack, so a mod's discs still win (decisions 16, 17, 19).
        # ── THE NAME HEADING — HD EXTENSION, brief 97 ──────────────
        # The original's box prints no name — `E_Strings_(74)` starts
        # at the planet's size (colsum.cpp:1196-1206), and the name is
        # the list row's. Data's decision of 13 September 2026 adds it
        # as a heading ABOVE the paragraph and changes nothing in the
        # paragraph itself. A `text`-skin box: the string is `Box.text`
        # at runtime, never saved (decision 37), drawn in the header's
        # own colour, and never reddened — the red belongs to the
        # original's paragraph.
        name_box = _box(screen, "planet_name")
        if name_box is not None and name_box.screen_rect is not None:
            name_box.text = row["name"] if row is not None else None
            name_box.text_color = HEADING_COLOR
            name_box.render(surface, screen.layout, screen.style)
        text_box = _box(screen, "planet_paragraph")
        disc_box = _box(screen, "planet_disc")
        if text_box is None or text_box.ref_rect is None:
            return
        text_rect = pygame.Rect(*screen.layout.rect(text_box.ref_rect))
        disc_rect = (pygame.Rect(*screen.layout.rect(disc_box.ref_rect))
                     if disc_box is not None and disc_box.ref_rect
                     else None)
        # THE BIG DISC, at the box's SHORTER side — see `render_info`.
        # The set is `colonyplanets`', cached per pixel size, so this
        # one and the row icons are two sets and neither rebuilds the
        # other.
        from . import colonyplanets
        _disc = (colonyplanets.set_for(
            screen, max(1, min(disc_rect.w, disc_rect.h)))
            if disc_rect is not None else None)
        render_info(surface, row, text_rect, cfg, words, climates,
                    screen.layout, screen.style, planets=_disc,
                    disc_rect=disc_rect, text_box=text_box)


def _box(screen, name):
    """The `Box` called `name` on `screen`, or None."""
    for box in screen.boxes:
        if box.name == name:
            return box
    return None


def render_info(surface, row, area, cfg, words, climates, layout, style,
                planets=None, disc_rect=None, text_box=None):
    """The LEFT half of the original's scan box — the description.

    `area` is the PARAGRAPH's rect — the `planet_paragraph` box — and
    `disc_rect` the `planet_disc` box's, or None for no disc. Since
    13 September 2026 nothing here places either: the wrap width is the
    paragraph box's width and the text starts at its corner, and the
    disc is fitted into the disc box's shorter side and centred, so a
    box dragged to a non-square shape still draws a round world rather
    than a stretched one. `text_box`, when given, receives the filled
    string and its colour as `Box.text` / `Box.text_color` (decision
    37) — runtime values that `Box.to_dict` never writes.

    `COLSUM::Draw_Colony_Scan_Info_` fills two boxes, not one
    (colsum.cpp:1155). This is the first: one formatted paragraph at
    native (13, 354, 80, 88) over `ESTRINGS::E_Strings_(74)`, with
    seven values substituted (colsum.cpp:1194-1206). The second — the
    four production rows and morale from native x 106 — is `render`'s,
    and until 8 September 2026 both were drawn into `planet_output`
    while `planet_info`, the hole the first one belongs in, was
    empty.

    **THE FORM IS SETTLED AND `info_style` IS GONE** — Stage 5,
    12 September 2026. The key chose between `paragraph` — the
    original's own five lines — and `rows`, the label-and-value table
    this panel drew before it. Both were built because the two
    pictures were the decision and a screenshot is what settles it
    (fundament: "a screenshot comparison from chat is a QUESTION").
    The pictures were taken, the transcription won, and a switch with
    one live setting is a branch nobody takes: brief 87 listed its
    removal in Stage 5 and brief 81 had already said "if the paragraph
    stays the only user". It did.

    The `rows` arm is NOT deleted code — `render` below still draws
    the table, because it is what `planet_output` draws and what the
    empty-selection path uses. What went is the choice.

    THE PARAGRAPH IS NOT THE TABLE RE-PUNCTUATED. It is five lines
    where the table has six rows: size and climate share a line
    ("Medium Ocean"), and growth carries no label at all ("+0k").
    Every noun in it — Gravity, Mineral, Population — belongs to the
    FORMAT and not to the word lists, which is the same rule the
    table follows from the other side (`words._note`): the list
    holds the bare quality, the surrounding text supplies the noun.
    """
    if row is None:
        if text_box is not None:
            text_box.text = None
        return render(surface, row, area, cfg, words, climates, layout,
                      style, only={0})
    template = cfg.get("info_paragraph", "")
    if not template:
        return
    values = row_values(row, words, climates)
    # THE WHOLE PARAGRAPH REDDENS ON NEGATIVE GROWTH — transcribed.
    # E_Strings_(74) takes the sign string TWICE, once at the very
    # front and once before the growth number, and closes with
    # "\x1B" "0" (colsum.cpp:1186-1206); a negative total_growth makes
    # both of them "\x1B" "2", the inline attribute that switches
    # colour until the reset. So the attribute is opened before the
    # first word and closed after the last: the box is red, not the
    # number. The red is the sidebar's own `warn`, which is the
    # original's (see `colonyempire._red_note`).
    color = (SHORTAGE_COLOR if int(row.get("growth", 0) or 0) < 0
             else VALUE_COLOR)
    text = fill_template(template, values)
    if text_box is not None:
        # THE RED REACHES THE WHOLE PARAGRAPH THROUGH THE BOX: the
        # string and its colour are the box's runtime text, and what is
        # drawn below reads them back, so the box and the pixels cannot
        # say two things.
        text_box.text = text
        text_box.text_color = color
        text, color = text_box.text, text_box.text_color
    # THE BOX'S `font_scale` IS HONOURED, AND ONCE — brief 97. It
    # multiplies the reference size BEFORE `layout.font_size` scales it
    # to the window, never after: `box_font_scale` on top of
    # `font_size` is the double scale the help popup drew at twice its
    # size with at 3840x2160 (fundament, "Scaling twice").
    font_scale = (float((text_box.style or {}).get("font_scale", 1.0))
                  if text_box is not None else 1.0)
    px = layout.font_size(int(round(cfg.get("value_font", 20) * font_scale)))
    # ── THE PLANET, IN ITS OWN BOX ─────────────────────────────
    #
    # **THE SAME DEVIATION AS THE ROW ICON** (`layout.json`,
    # `list._planet_icon_deviation`): the original's scan box is five
    # lines of text and no picture. Data's decision of 12 September
    # 2026 puts the world beside the words here too, and larger,
    # because this panel is about one colony. The disc is square, so
    # it takes the box's SHORTER side and is centred in the other one:
    # the renderer fits, the box does not have to be square.
    disc = (planets.get(row.get("climate"))
            if planets is not None and disc_rect is not None else None)
    if disc is not None:
        surface.blit(disc, (
            disc_rect.x + (disc_rect.w - disc.get_width()) // 2,
            disc_rect.y + (disc_rect.h - disc.get_height()) // 2))
    # THE WRAP WIDTH IS THE BOX'S WIDTH, still measured by rendering
    # (decision 30) — `textfit.squeeze_lines` renders each candidate.
    room_w = max(1, area.w)
    room_h = max(1, area.h)
    # ONE SIZE FOR THE WHOLE PARAGRAPH — brief 97. Each of the five
    # lines used to be squeezed on its own against the WHOLE box height,
    # so every line fitted alone and the five together could run past
    # the box: at 2560x1440 with Data's font_scale 1.6 they wrapped to
    # seven lines and left it. The largest size at which every line,
    # wrapped, fits the box together is the size; measured by rendering
    # (decision 30), smallest size if nothing fits.
    sizes = [px - n for n in range(0, max(1, px - 7))]
    lines = []
    for size in sizes:
        lines = [style.render_text(part, size, color[:3])
                 for para in text.split("\n")
                 for part in textfit.wrap_text(style, para, size, room_w)]
        if (sum(s.get_height() for s in lines) <= room_h
                and max(s.get_width() for s in lines) <= room_w):
            break
    # LEFT-ALIGNED, which is what the original's flags argument says:
    # Squeeze_Print_Formatted_Paragraph_(13, 354, 80, 88, buffer, 0)
    # and 0 is JUSTIFY_LEFT (colsum.cpp:1206; the same argument
    # decision 45 reads for the colony name).
    y = area.y
    for surf in lines:
        surface.blit(surf, (area.x, y))
        y += surf.get_height()


def render(surface, row, area, cfg, words, climates, layout, style,
           only=None, icons=None):
    """Draw the panel into `area`; `row` is None when nothing is
    selected, and then nothing is drawn — no label, no icon, no line.

    `icons` is a `colonyoutputicons.IconSet` or None. With a set, each
    row whose entry names an icon draws it at the left and its label
    moves right by the icon and `icon_gap` — a DEVIATION, decision 56.
    Without one the panel is what it was before the icons existed.

    Label left, value right, in as many columns as `columns` says —
    the same arrangement as the sidebar, and for the same reason: it
    is what the original does with a paragraph whose two halves carry
    their own justification codes (see `screen._render_sidebar`).
    Here it is a CHOICE rather than a transcription, because the
    original's scan box is one squeezed paragraph and not a table.
    What is transcribed is which values appear, not how they sit.
    """
    if row is None:
        empty = cfg.get("empty", "")
        if not empty:
            return
        text = style.render_text(
            empty, layout.font_size(cfg.get("label_font", 14)),
            EMPTY_COLOR[:3])
        surface.blit(text, (area.x + (area.w - text.get_width()) // 2,
                            area.y + (area.h - text.get_height()) // 2))
        return

    entries = visible_rows(row, cfg, words, climates, only)
    if not entries:
        return

    # ONE COLUMN PER PANEL when the caller named a set: the two
    # halves are two boxes now, so each lays its own rows out in a
    # single column and `columns` is only consulted for the whole
    # panel. Renumbered to 0.. so the grouping below does not have to
    # know which of the original's halves it is drawing.
    columns = (len(only) if only is not None
               else max(1, int(cfg.get("columns", 1))))
    if only is not None:
        order = {c: i for i, c in enumerate(sorted(only))}
        entries = [e._replace(column=order.get(e.column, 0))
                   for e in entries]
    pad_x = int(cfg.get("pad_x", 18) * layout.scale)
    pad_y = int(cfg.get("pad_y", 14) * layout.scale)
    gap = int(cfg.get("row_gap", 4) * layout.scale)
    col_gap = int(cfg.get("column_gap", 12) * layout.scale)
    label_px = layout.font_size(cfg.get("label_font", 14))
    value_px = layout.font_size(cfg.get("value_font", 20))

    short_gap = int(cfg.get("shortage_gap", 8) * layout.scale)
    # ICONS AND SEPARATORS READ `layout.scale` DIRECTLY — the stored
    # scale, never `font_size`, which multiplies a second time for a
    # box tuned per resolution and is how the help popup drew at twice
    # its size at an untuned 3840x2160 (fundament, "Scaling twice").
    has_icons = icons is not None and icons.state != "missing"
    icon_gap = int(cfg.get("icon_gap", 0) * layout.scale) if has_icons else 0
    sep_ref = cfg.get("separator_thickness", 0)
    sep_px = max(1, int(round(sep_ref * layout.scale))) if sep_ref else 0
    sep_inset = int(cfg.get("separator_inset", 0) * layout.scale)
    grouped = [[e for e in entries
                if min(columns - 1, max(0, e.column)) == c]
               for c in range(columns)]

    # The FULLEST column sets the pitch, so both columns share one
    # baseline grid. Sizing each to its own count would let a
    # five-row column and a four-row column drift apart by half a row
    # and read as a misalignment rather than as two lists.
    per_column = max(1, max(len(g) for g in grouped))
    col_w = (area.w - 2 * pad_x) // columns
    row_h = max(1, (area.h - 2 * pad_y - gap * (per_column - 1)) // per_column)

    for c, column_rows in enumerate(grouped):
        left = area.x + pad_x + c * col_w
        right = left + col_w - col_gap
        for i, entry in enumerate(column_rows):
            top = area.y + pad_y + i * (row_h + gap)
            # ── THE SEPARATOR — HD EXTENSION ──────────────────────
            # The original draws no line in this box: its only
            # Line_/Fill_ calls are the screen clears and the scroll
            # thumb (colsum.cpp:125, :460, :759-765), and COLSUM.LBX
            # entry 0 is one palette index across the whole box. Data's
            # mockup of 13 September 2026 draws one between consecutive
            # rows, so it is drawn ABOVE every row but the first — never
            # above the first, never under the last — centred in the
            # row gap the geometry already leaves. See
            # `output._separator_note`, and the smoke check that fails
            # if it goes.
            if i > 0 and sep_px:
                sep_y = top - gap + max(0, (gap - sep_px) // 2)
                surface.fill(SEPARATOR_COLOR[:3], pygame.Rect(
                    left + sep_inset, sep_y,
                    max(0, right - left - 2 * sep_inset), sep_px))
            text_left = left
            sprite = icons.get(entry.icon) if has_icons else None
            if has_icons:
                # The label moves by the SET's size whether or not this
                # row has a sprite, so a missing file cannot put one
                # label out of line with the other four.
                text_left = left + icons.size + icon_gap
            if sprite is not None:
                surface.blit(sprite, (left, top + max(
                    0, (row_h - sprite.get_height()) // 2)))
            lab = style.render_text(entry.label.upper(), label_px,
                                    LABEL_COLOR[:3])
            val = style.render_text(str(entry.value), value_px,
                                    VALUE_COLOR[:3])
            sht = (style.render_text(entry.shortage, label_px,
                                     SHORTAGE_COLOR[:3])
                   if entry.shortage else None)
            block_h = max(lab.get_height(), val.get_height())
            y = top + max(0, (row_h - block_h) // 2)
            surface.blit(lab, (text_left,
                               y + (block_h - lab.get_height())))
            # THE SHORTAGE FOLLOWS THE VALUE, because that is the
            # order the original draws them in: net, gap, secondary,
            # gap, imports, shortage — the shortage is the LAST group
            # (coldraw.cpp:170-177, after the import loops). It sat
            # to the LEFT until 4 September 2026, which inverted the
            # only two groups this panel draws.
            #
            # The pair is right-aligned AS A GROUP rather than the
            # marker being hung past the value's right edge. Two
            # reasons and the second is the one that decided it: the
            # widest structural marker does not fit in `column_gap`
            # at any shipped size, and the space beyond that gap is
            # the panel's own margin, where the frame's rim sits —
            # the fault just fixed in the sidebar. So the value moves
            # left on a row that has a marker, which is also closer
            # to the original: its row is anchored at x and grows
            # rightward, not pinned to a right edge.
            end = right
            if sht is not None:
                surface.blit(sht, (right - sht.get_width(),
                                   y + (block_h - sht.get_height())))
                end = right - sht.get_width() - short_gap
            surface.blit(val, (end - val.get_width(),
                               y + (block_h - val.get_height())))
