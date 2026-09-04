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

from core import palette

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
                                  "label value column shortage")


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


def visible_rows(row, cfg, words, climates):
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
    """
    if row is None:
        return []
    values = row_values(row, words, climates)
    hidden = cfg.get("hidden_value", "")
    template = cfg.get("shortage_value", "")
    out = []
    for spec in cfg.get("rows", []):
        text = fill_template(spec.get("value", ""), values)
        if spec.get("id") == "morale" and not row.get("morale_applies", True):
            text = hidden
        short = row_shortage(row, spec)
        out.append(PanelRow(
            spec.get("label", ""), text, int(spec.get("column", 0)),
            fill_template(template, {"shortage": short}) if short > 0
            else ""))
    return out


def render(surface, row, area, cfg, words, climates, layout, style):
    """Draw the panel into `area`; `row` is None when nothing is
    selected, and then nothing is drawn.

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

    entries = visible_rows(row, cfg, words, climates)
    if not entries:
        return

    columns = max(1, int(cfg.get("columns", 1)))
    pad_x = int(cfg.get("pad_x", 18) * layout.scale)
    pad_y = int(cfg.get("pad_y", 14) * layout.scale)
    gap = int(cfg.get("row_gap", 4) * layout.scale)
    col_gap = int(cfg.get("column_gap", 12) * layout.scale)
    label_px = layout.font_size(cfg.get("label_font", 14))
    value_px = layout.font_size(cfg.get("value_font", 20))

    short_gap = int(cfg.get("shortage_gap", 8) * layout.scale)
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
            lab = style.render_text(entry.label.upper(), label_px,
                                    LABEL_COLOR[:3])
            val = style.render_text(str(entry.value), value_px,
                                    VALUE_COLOR[:3])
            sht = (style.render_text(entry.shortage, label_px,
                                     SHORTAGE_COLOR[:3])
                   if entry.shortage else None)
            block_h = max(lab.get_height(), val.get_height())
            y = top + max(0, (row_h - block_h) // 2)
            surface.blit(lab, (left, y + (block_h - lab.get_height())))
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
