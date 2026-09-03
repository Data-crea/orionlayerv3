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
at 446 lines before this and the guideline is ~300 (decision 6); a
panel that draws ten values from a dict is not "being a screen" in the
sense the rest of that file is. The seam is the one `colonyrows` and
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

The three deviations this panel carries — BC not shown, one number
per production row where the original draws several, and morale as a
number where the original draws sprites — are stated in `layout.json`
under `output._deviation_note`, with what it would take to undo each.
"""
from core import palette

LABEL_COLOR = palette.col("colony_summary", "label", (140, 155, 190))
VALUE_COLOR = palette.col("colony_summary", "value", (220, 228, 245))
EMPTY_COLOR = palette.col("colony_summary", "nav_text_dim",
                          (104, 116, 142))


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


def row_values(row, words, climates):
    """The ten values, as strings, keyed by their placeholder.

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
        "growth": row.get("growth", 0),
        "food": row.get("production", (0, 0, 0, 0))[0],
        "industry": row.get("production", (0, 0, 0, 0))[1],
        "research": row.get("production", (0, 0, 0, 0))[2],
        "bc": row.get("production", (0, 0, 0, 0))[3],
        "morale": row.get("morale", 0),
    }


def visible_rows(row, cfg, words, climates):
    """(label, value, column) per configured row, for one colony.

    Morale is the one row that can be present and have nothing to
    say: under Unification the original draws no marks at all, so the
    value becomes `hidden_value` — empty by default — and the LABEL
    stays. That is the shape of the original's own absence: the box is
    still there and the morale part of it is blank.

    Split out from `render` so a smoke check can ask what the panel
    would draw without needing a surface, and so the empty-selection
    rule is one `if` in one place instead of a guard per row.
    """
    if row is None:
        return []
    values = row_values(row, words, climates)
    hidden = cfg.get("hidden_value", "")
    out = []
    for spec in cfg.get("rows", []):
        text = fill_template(spec.get("value", ""), values)
        if spec.get("id") == "morale" and not row.get("morale_applies", True):
            text = hidden
        out.append((spec.get("label", ""), text, int(spec.get("column", 0))))
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

    grouped = [[(lab, val) for lab, val, col in entries
                if min(columns - 1, max(0, col)) == c]
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
        for i, (label, value) in enumerate(column_rows):
            top = area.y + pad_y + i * (row_h + gap)
            lab = style.render_text(label.upper(), label_px, LABEL_COLOR[:3])
            val = style.render_text(str(value), value_px, VALUE_COLOR[:3])
            block_h = max(lab.get_height(), val.get_height())
            y = top + max(0, (row_h - block_h) // 2)
            surface.blit(lab, (left, y + (block_h - lab.get_height())))
            surface.blit(val, (right - val.get_width(),
                               y + (block_h - val.get_height())))
