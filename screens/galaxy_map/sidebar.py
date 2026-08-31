"""Galaxy map sidebar — stardate plus the five resource readouts.

Mirrors the original's right-hand column: the stardate box sits on
top (as in MAINSCR), followed by what Draw_Main_Screen_Info_ prints,
read from the local player's record instead of from pixels:

  Stardate      from the snapshot (passed in via `extras`)
  Treasury      bc                    surplus_bc on a second line
  Command       cp - cp_used          (command_points) in brackets
  Food          surplus_food          signed
  Freighters    surplus_freighters    (n_freighters) in brackets
  Research      breakthrough / none / accumulated RP

Negative values render in the warning colour, matching the
original's red pulse for a deficit.

**Every element has its own box.** Each row owns two boxes in
boxes.json, `sb_<row>_text` and `sb_<row>_icon`, so both can be
moved, resized and font-scaled in the F5 editor like on every other
screen. The stardate row has no icon box. A row whose boxes are
missing falls back to an even split of the `sidebar` cutout, which
is what this module did before the boxes existed — that keeps a mod
shipping an older boxes.json working.

The sub-value follows the original's own rule: a bracketed count
("(15)") sits on the value line, a signed second quantity ("+12 BC")
gets a line of its own. See SUB_INLINE_PREFIX.

All numeric text uses the PROPORTIONAL font: Bank Gothic (DEMO)
renders +, -, / and % as watermark glyphs, and every line here can
carry a sign.
"""
import pygame

from core import palette
from core.structs import player as player_struct

LABEL_COLOR = palette.col("galaxy_map", "sidebar_label", (128, 146, 180))
VALUE_COLOR = palette.col("galaxy_map", "sidebar_value", (206, 216, 238))
WARN_COLOR = palette.col("galaxy_map", "sidebar_warning", (214, 88, 74))
SUB_COLOR = palette.col("galaxy_map", "sidebar_secondary", (150, 162, 190))
DIVIDER_COLOR = palette.col("galaxy_map", "sidebar_divider", (44, 56, 84))

#: Order and labels of the five readouts. Overridable via layout.json.
DEFAULT_ROWS = ["treasury", "command", "food", "freighters", "research"]

#: Reference font sizes; scaled by each text box's own font_scale.
DEFAULT_FONTS = {"label": 15, "value": 26, "sub": 18}

#: A sub-value starting with this joins the value line instead of
#: taking one of its own — the original prints "+14 (15)" on one
#: line but treasury's income below the balance.
SUB_INLINE_PREFIX = "("

#: Gap between value and inline sub, and divider offset above a row
#: band; both in reference pixels.
INLINE_GAP = 6
DIVIDER_LIFT = 8
#: Breathing room between the label and the value line.
LABEL_GAP = 5

#: Fallback geometry, used only when the sb_* boxes are absent.
DEFAULT_ICON_FRAC = 0.40
ICON_PAD = 0.12


def _fmt_signed(value):
    """'+12' / '-3' — the original prints an explicit plus."""
    return f"+{value}" if value >= 0 else str(value)


def _fmt_thousands(value):
    return f"{value:,}".replace(",", " ")


def readout(key, plr, labels, monetary="BC"):
    """(label, main, sub, warn) for one sidebar row.

    `plr` is a parsed s_player view, or None when disconnected —
    in that case every row shows a placeholder rather than zeros,
    so a missing connection never looks like a broke empire.
    """
    label = labels.get(key, key.title())
    if plr is None:
        return label, "--", "", False

    if key == "treasury":
        return (label, f"{_fmt_thousands(plr.bc)} {monetary}",
                f"{_fmt_signed(plr.surplus_bc)} {monetary}",
                plr.bc < 0 or plr.surplus_bc < 0)

    if key == "command":
        surplus = player_struct.command_point_surplus(plr)
        return (label, _fmt_signed(surplus),
                f"({plr.command_points})", surplus < 0)

    if key == "food":
        return (label, _fmt_signed(plr.surplus_food), "",
                plr.surplus_food < 0)

    if key == "freighters":
        return (label, _fmt_signed(plr.surplus_freighters),
                f"({plr.n_freighters})", plr.surplus_freighters < 0)

    if key == "research":
        if plr.research_breakthrough:
            return label, labels.get("breakthrough", "Breakthrough"), "", False
        if plr.current_research_field == 0:
            return label, labels.get("no_research", "None"), "", False
        return (label, f"{_fmt_thousands(plr.research_accumulated)} RP",
                f"{_fmt_signed(plr.research_produced)} RP", False)

    return label, "--", "", False


# ── Geometry ─────────────────────────────────────────────

def row_rects(box, count):
    """Split a sidebar box into `count` evenly stacked row rects."""
    x, y, w, h = box
    if count < 1:
        return []
    step = h / count
    return [(x, y + i * step, w, step) for i in range(count)]


def split_row(rect, has_icon, frac=DEFAULT_ICON_FRAC):
    """(text_rect, icon_rect) for one row of the fallback layout."""
    x, y, w, h = rect
    if not has_icon:
        return (x, y, w, h), None
    icon_w = int(w * frac)
    pad = int(h * ICON_PAD)
    return ((x, y, w - icon_w, h),
            (x + w - icon_w + pad, y + pad,
             max(1, icon_w - 2 * pad), max(1, h - 2 * pad)))


def fallback_geometry(box, rows, icons):
    """Even-split geometry for a boxes.json without sb_* boxes."""
    return {key: split_row(rect, key in icons)
            for key, rect in zip(rows, row_rects(box, len(rows)))}


# ── Drawing helpers ──────────────────────────────────────

def _fit_width(text_surface, max_w):
    """Shrink a rendered line that would overrun its box.

    A text box can be dragged narrow in the editor, and font_scale
    is applied on top of the resolution scale, so a line can end up
    wider than its box at 1440p even when it fits at 1080p. Scaling
    the finished surface keeps one font size per row.
    """
    if max_w < 1 or text_surface.get_width() <= max_w:
        return text_surface
    ratio = max_w / text_surface.get_width()
    return pygame.transform.smoothscale(
        text_surface, (int(max_w),
                       max(1, int(text_surface.get_height() * ratio))))


def _place(x, w, width, align):
    """Left edge of a `width` wide line inside a column."""
    if align == "left":
        return x
    if align == "right":
        return x + w - width
    return x + (w - width) // 2


def blit_icon(surface, cache, key, rect):
    """Draw an icon into `rect`, aspect kept, centred.

    Scaling goes through the screen's SpriteCache, so a resize or a
    drag in the editor rebuilds each icon once, not every frame.
    """
    src = cache.base(key) if cache is not None else None
    if src is None:
        return
    x, y, w, h = rect
    ratio = src.get_height() / max(1, src.get_width())
    width = int(min(w, h / ratio)) if ratio else int(w)
    scaled = cache.scaled(key, width)
    if scaled is None:
        return
    surface.blit(scaled, (x + (w - scaled.get_width()) // 2,
                          y + (h - scaled.get_height()) // 2))


def _pair_surface(vt, st, gap):
    """Value and inline sub merged, so they can be shrunk together."""
    surf = pygame.Surface(
        (vt.get_width() + gap + st.get_width(),
         max(vt.get_height(), st.get_height())), pygame.SRCALPHA)
    surf.blit(vt, (0, 0))
    surf.blit(st, (vt.get_width() + gap, vt.get_height() - st.get_height()))
    return surf


def draw_text_block(surface, style, layout, rect, label, main, sub,
                    warn, font_scale, align, fonts):
    """Label, value and sub inside one text box, vertically centred."""
    x, y, w, h = rect
    label_font = style.get_font(
        layout.font_size(int(fonts["label"] * font_scale)))
    value_font = style.get_prop_font(
        layout.font_size(int(fonts["value"] * font_scale)))
    sub_font = style.get_prop_font(
        layout.font_size(int(fonts["sub"] * font_scale)))

    lt = _fit_width(label_font.render(label.upper(), True,
                                      LABEL_COLOR[:3]), w)
    vt = value_font.render(main, True,
                           (WARN_COLOR if warn else VALUE_COLOR)[:3])
    st = sub_font.render(sub, True, SUB_COLOR[:3]) if sub else None

    if st is not None and sub.startswith(SUB_INLINE_PREFIX):
        vt, st = _fit_width(
            _pair_surface(vt, st, max(1, int(INLINE_GAP * layout.scale))),
            w), None
    else:
        vt = _fit_width(vt, w)
        st = _fit_width(st, w) if st is not None else None

    gap = int(LABEL_GAP * layout.scale)
    block_h = lt.get_height() + gap + vt.get_height() \
        + (st.get_height() if st is not None else 0)
    cy = y + max(0, (h - block_h) // 2)

    surface.blit(lt, (_place(x, w, lt.get_width(), align), cy))
    cy += lt.get_height() + gap
    surface.blit(vt, (_place(x, w, vt.get_width(), align), cy))
    if st is not None:
        cy += vt.get_height()
        surface.blit(st, (_place(x, w, st.get_width(), align), cy))


def draw_dividers(surface, layout, panel_box, bands):
    """A hairline above every row band except the topmost.

    Derived from the row boxes themselves, so the separators follow
    the text boxes when they are dragged instead of staying on a
    fixed grid that no longer matches them.
    """
    if len(bands) < 2:
        return
    px, _, pw, _ = layout.rect(panel_box)
    inset = int(pw * 0.06)
    lift = int(DIVIDER_LIFT * layout.scale)
    for top in sorted(bands)[1:]:
        pygame.draw.line(surface, DIVIDER_COLOR[:3],
                         (px + inset, top - lift),
                         (px + pw - inset, top - lift), 1)


# ── Entry point ──────────────────────────────────────────

def render(surface, layout, style, geometry, plr, labels, rows=None,
           font_scales=None, aligns=None, monetary="BC", extras=None,
           icons=None, cache=None, fonts=None, panel_box=None,
           dividers=True):
    """Draw the sidebar from per-element geometry.

    `geometry` maps a row key to (text_ref_rect, icon_ref_rect|None),
    both in reference space; the screen builds it from the sb_* boxes
    or from `fallback_geometry`. `font_scales` and `aligns` are keyed
    the same way. `extras` supplies ready (main, sub) pairs for rows
    that are not in the player record — the stardate.
    """
    rows = rows or DEFAULT_ROWS
    extras = extras or {}
    icons = icons or {}
    font_scales = font_scales or {}
    aligns = aligns or {}
    fonts = fonts or DEFAULT_FONTS
    bands = []

    for key in rows:
        geo = geometry.get(key)
        if geo is None:
            continue
        text_rect, icon_rect = geo
        bands.append(layout.rect(text_rect)[1])

        if key in extras:
            main, sub = extras[key]
            label, warn = labels.get(key, key.title()), False
        else:
            label, main, sub, warn = readout(key, plr, labels, monetary)

        if icon_rect is not None and key in icons:
            blit_icon(surface, cache, icons[key], layout.rect(icon_rect))

        draw_text_block(surface, style, layout, layout.rect(text_rect),
                        label, main, sub, warn,
                        font_scales.get(key, 1.0),
                        aligns.get(key, "center"), fonts)

    if dividers and panel_box is not None:
        draw_dividers(surface, layout, panel_box, bands)
