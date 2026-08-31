"""Select Race info panel — name, description, traits.

Split out of renderer.py: everything right of the portrait grid.
Colors and font sizes are shared with renderer.py so the skin's
"select_race" colors.json section covers both files.
"""
import re
import pygame

from screens.select_race.renderer import (
    COL_HEADING, COL_LABEL, COL_VALUE, COL_GOOD, COL_BAD,
    COL_NEUTRAL, COL_FLAVOR, COL_HIGHLIGHT, COL_KEYWORD,
    COL_SUBTITLE, COL_SEPARATOR,
    TITLE_FONT, SUBTITLE_FONT, BODY_FONT, HEADING_FONT, TRAIT_FONT,
)


def render_race_name(surface, L, style, race, rect, fs_scale=1.0):
    """Render race name + subtitle in its own box."""
    rx, ry, rw, rh = rect

    # Race name
    tfs = L.font_size(int(TITLE_FONT * fs_scale))
    tfont = style.get_font(tfs)
    tx, ty = L.pos(rx, ry)
    t_surf = tfont.render(race["name"].upper(), True, COL_HEADING)
    surface.blit(t_surf, (tx, ty))

    # Subtitle below name
    sub = race.get("subtitle", "")
    if sub:
        sfs = L.font_size(int(SUBTITLE_FONT * fs_scale))
        sfont = style.get_font(sfs)
        sx, sy = L.pos(rx, ry + 34)
        s_surf = sfont.render(sub.upper(), True, COL_SUBTITLE)
        surface.blit(s_surf, (sx, sy))


def render_race_description(surface, L, style, race, rect,
                            scroll_offset=0, fs_scale=1.0):
    """Render scrollable description with markup in its own box."""
    rx, ry, rw, rh = rect
    desc = race.get("description", "")
    if not desc:
        return
    _render_description(surface, L, style, desc,
                        rx, ry, rw, rh, scroll_offset, fs_scale)


def render_race_traits(surface, L, style, race, rect, fs_scale=1.0):
    """Render RACE TRAITS section in its own box."""
    rx, ry, rw, rh = rect
    _render_traits_section(surface, L, style, race,
                           rx, ry, rw, fs_scale)


def _render_description(surface, L, style, text, rx, ry, rw, rh,
                        scroll_offset, fs_scale):
    """Scrollable description with *highlight* and ~keyword~ markup."""
    fs = L.font_size(int((BODY_FONT + 1) * fs_scale))
    font = style.get_prop_font(fs)
    max_w = int(rw * L.scale)
    sx, sy = L.pos(rx, ry)
    sh = int(rh * L.scale)
    line_h = int(fs * 1.5)
    space_w = font.size(" ")[0]

    # Parse markup
    parts = re.split(r'(\*[^*]+\*|~[^~]+~)', text)
    words = []
    for p in parts:
        if p.startswith('*') and p.endswith('*'):
            for w in p[1:-1].split():
                words.append((w, COL_HIGHLIGHT))
        elif p.startswith('~') and p.endswith('~'):
            for w in p[1:-1].split():
                words.append((w, COL_KEYWORD))
        elif p:
            for w in p.split():
                words.append((w, COL_FLAVOR))

    # Word-wrap
    lines = []
    cur_line = []
    cur_text = ""
    for word, col in words:
        test = f"{cur_text} {word}".strip()
        if font.size(test)[0] > max_w and cur_line:
            lines.append(cur_line)
            cur_line = [(word, col)]
            cur_text = word
        else:
            cur_line.append((word, col))
            cur_text = test
    if cur_line:
        lines.append(cur_line)

    # Render with clipping
    clip = pygame.Rect(sx, sy, max_w, sh)
    old_clip = surface.get_clip()
    surface.set_clip(clip)

    y = sy - scroll_offset
    for line_words in lines:
        if y + line_h > sy - line_h and y < sy + sh + line_h:
            x = sx
            for word, col in line_words:
                w_surf = font.render(word, True, col)
                surface.blit(w_surf, (x, y))
                x += w_surf.get_width() + space_w
        y += line_h

    surface.set_clip(old_clip)


TWO_COL_THRESHOLD = 3  # switch to two columns when more traits than this


def _trait_width(trait, name_font, note_font, val_font, scale):
    """Measure the pixel width a trait needs (name+value or note)."""
    gap = int(10 * scale)
    name_w = name_font.size(trait["name"])[0]
    value = trait.get("value", "")
    if value:
        name_w += gap + val_font.size(value)[0]
    note = trait.get("note", "")
    note_w = note_font.size(note)[0] if note else 0
    return max(name_w, note_w)


def _render_traits_section(surface, L, style, race, rx, ry, rw,
                           fs_scale):
    """Render RACE TRAITS heading + trait list + government.

    Auto-switches to two-column layout when trait count exceeds
    TWO_COL_THRESHOLD. Traits that are too wide for a half-column
    get their own full-width row; only narrow traits are paired.
    Government always renders full-width at bottom.
    """
    hfs = L.font_size(int(HEADING_FONT * fs_scale))
    hfont = style.get_font(hfs)
    hx, hy = L.pos(rx, ry)
    h_surf = hfont.render("RACE TRAITS", True, COL_LABEL)
    surface.blit(h_surf, (hx, hy))

    tfs = L.font_size(int(TRAIT_FONT * fs_scale))
    nfs = L.font_size(int(13 * fs_scale))
    name_font = style.get_font(tfs)
    note_font = style.get_prop_font(nfs)
    val_font = style.get_prop_font(tfs)
    note_offset = int(20 * fs_scale)
    row_note = int(42 * fs_scale)
    row_plain = int(26 * fs_scale)

    # Separate government from other traits
    gov_value = None
    traits = []
    for trait in race.get("traits", []):
        if trait["name"] == "Government":
            gov_value = trait.get("value", "")
        else:
            traits.append(trait)

    two_col = len(traits) > TWO_COL_THRESHOLD
    col_gap = int(12 * fs_scale)
    col_w = (rw - col_gap) / 2 if two_col else rw

    if two_col:
        # Measure each trait and classify as wide or narrow
        half_px = int(col_w * L.scale)
        narrow = []
        wide = []
        for trait in traits:
            w = _trait_width(trait, name_font, note_font,
                             val_font, L.scale)
            if w > half_px:
                wide.append(trait)
            else:
                narrow.append(trait)

        row_y = ry + 24
        ti = 0  # index into original traits (for ordering)

        while ti < len(traits):
            trait = traits[ti]
            if trait in wide:
                # Full-width row
                row_y = _draw_trait(surface, L, name_font, note_font,
                                    val_font, trait, rx, row_y, rw,
                                    note_offset, row_note, row_plain,
                                    fs_scale)
                ti += 1
            else:
                # Pair narrow traits: find next narrow after ti
                left = trait
                right = None
                ti += 1
                while ti < len(traits):
                    if traits[ti] in wide:
                        ti += 1
                    else:
                        right = traits[ti]
                        ti += 1
                        break

                # Draw left
                left_y = _draw_trait(surface, L, name_font, note_font,
                                     val_font, left, rx, row_y,
                                     col_w, note_offset, row_note,
                                     row_plain, fs_scale)
                if right:
                    right_y = _draw_trait(
                        surface, L, name_font, note_font, val_font,
                        right, rx + col_w + col_gap, row_y,
                        col_w, note_offset, row_note, row_plain,
                        fs_scale)
                    row_y = max(left_y, right_y)
                else:
                    row_y = left_y
    else:
        row_y = ry + 24
        for trait in traits:
            row_y = _draw_trait(surface, L, name_font, note_font,
                                val_font, trait, rx, row_y, rw,
                                note_offset, row_note, row_plain,
                                fs_scale)

    # Government separator + value
    col_x_right = rx + (rw - col_gap) / 2 + col_gap
    row_y += int(6 * fs_scale)
    sx1, sy1 = L.pos(rx, row_y)
    sx2, _ = L.pos(rx + rw, row_y)
    pygame.draw.line(surface, COL_SEPARATOR, (sx1, sy1), (sx2, sy1), 1)
    row_y += int(10 * fs_scale)
    gx, gy = L.pos(rx, row_y)
    g_label = name_font.render("Government", True, COL_VALUE)
    surface.blit(g_label, (gx, gy))
    if gov_value:
        gv_surf = val_font.render(gov_value, True, COL_NEUTRAL)
        y_off = g_label.get_height() - gv_surf.get_height()
        gvx, _ = L.pos(col_x_right, row_y)
        surface.blit(gv_surf, (gvx, gy + y_off))


def _draw_trait(surface, L, name_font, note_font, val_font,
                trait, rx, row_y, col_w, note_offset,
                row_note, row_plain, fs_scale):
    """Draw a single trait entry. Returns the next row_y."""
    good = trait.get("good")
    vcol = (COL_GOOD if good is True
            else COL_BAD if good is False
            else COL_NEUTRAL)
    max_w = int(col_w * L.scale)

    tx, ty = L.pos(rx, row_y)
    t_surf = name_font.render(trait["name"], True, COL_VALUE)
    surface.blit(t_surf, (tx, ty))

    value = trait.get("value", "")
    if value:
        gap = int(10 * L.scale)
        v_surf = val_font.render(value, True, vcol)
        y_off = t_surf.get_height() - v_surf.get_height()
        surface.blit(v_surf, (tx + t_surf.get_width() + gap,
                              ty + y_off))

    note = trait.get("note", "")
    if note:
        nx, ny = L.pos(rx, row_y + note_offset)
        n_surf = note_font.render(note, True, vcol)
        if n_surf.get_width() > max_w:
            n_surf = n_surf.subsurface(
                (0, 0, max_w, n_surf.get_height()))
        surface.blit(n_surf, (nx, ny))
        return row_y + row_note
    return row_y + row_plain


