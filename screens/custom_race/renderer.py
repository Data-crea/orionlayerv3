"""Custom Race rendering — Race Picks and Special Abilities panels.

Layout follows the reference mockup:
  Race Picks   two sub-columns; each category is a small blue
               header above a bordered box holding its options
               (radio icon, label, pick value right-aligned)
  Specials     single checkbox column with values right-aligned,
               scrollbar, and a highlight on the trait currently
               shown in the description panel

Geometry lives in the *_layout() functions and is used by BOTH
the render and the hit-test paths, so clicks can never drift
from what is drawn.

All coordinates are 1080p reference space; L.pos()/L.size()
convert at draw time. Icons come from assets (radio_off,
radio_on, checkbox_off) and are cached per pixel size.
"""
import pygame
from core import palette

# Bound once here; description.py imports this same _c instead of
# redefining it, so the whole screen shares one "custom_race"
# color lookup instead of three separate access patterns.
_c = palette.for_section("custom_race")

COL_CAT_HEADER = _c("cat_header",     (91, 155, 213))
COL_LABEL      = _c("label",          (90, 122, 168))
COL_OPTION     = _c("option_label",   (206, 212, 226))
COL_OPTION_SEL = _c("option_selected", (236, 242, 255))
COL_VALUE_POS  = _c("pick_pos",       (80, 200, 120))
COL_VALUE_NEG  = _c("pick_neg",       (216, 88, 78))
COL_BOX_BORDER = _c("box_border",     (42, 66, 104))
COL_BOX_BG     = _c("box_bg",         (12, 20, 38, 120))
COL_ROW_SEL_BG = _c("row_selected_bg", (74, 54, 128, 170))
COL_ROW_SEL_BD = _c("row_selected_border", (146, 108, 226))
COL_CHECK      = _c("check_mark",     (86, 214, 122))
COL_SCROLL_BG  = _c("scroll_bg",      (22, 30, 52))
COL_SCROLL_TH  = _c("scroll_thumb",   (70, 95, 150))

COL_BLOCKED    = _c("blocked",         (70, 75, 90))


# Reference-space metrics
CAT_FONT      = 14
OPT_FONT      = 15
CAT_HEADER_H  = 21
OPT_ROW_H     = 24
BOX_PAD_Y     = 7
BOX_PAD_X     = 9
CAT_GAP       = 11
SUB_GAP       = 16
PANEL_INSET   = 22
ICON_SIZE     = 16
LABEL_GAP     = 9
SPEC_ROW_H    = 27
SPEC_GAP_Y    = 2
SCROLLBAR_W   = 7


def icon(icons, cache, name, size):
    """Scaled icon surface, cached per (name, pixel size)."""
    img = icons.get(name)
    if not img or size < 2:
        return None
    key = (name, size)
    if key not in cache:
        cache[key] = pygame.transform.smoothscale(img, (size, size))
    return cache[key]


# -- Race Picks -------------------------------------------

def picks_layout(categories, rect, fs=1.0):
    """Geometry of the Race Picks panel in reference coords.

    Returns a list of dicts:
      {cat, header: (x,y,w,h), box: (x,y,w,h),
       rows: [(option, (x,y,w,h)), ...]}
    """
    rx, ry, rw, rh = rect
    n = len(categories)
    mid = (n + 1) // 2
    columns = [categories[:mid], categories[mid:]]

    inner_x = rx + PANEL_INSET
    inner_w = rw - 2 * PANEL_INSET
    sub_w = (inner_w - SUB_GAP) / 2
    row_h = OPT_ROW_H * fs
    hdr_h = CAT_HEADER_H * fs
    pad_y = BOX_PAD_Y * fs
    gap = CAT_GAP * fs

    out = []
    for col_idx, col_cats in enumerate(columns):
        cx = inner_x + col_idx * (sub_w + SUB_GAP)
        cy = ry
        for cat in col_cats:
            opts = cat.get("options", [])
            box_h = 2 * pad_y + len(opts) * row_h
            entry = {"cat": cat,
                     "header": (cx, cy, sub_w, hdr_h),
                     "box": (cx, cy + hdr_h, sub_w, box_h),
                     "rows": []}
            oy = cy + hdr_h + pad_y
            for opt in opts:
                entry["rows"].append((opt, (cx, oy, sub_w, row_h)))
                oy += row_h
            out.append(entry)
            cy += hdr_h + box_h + gap
    return out


def render_race_picks_panel(surface, L, style, categories, trait_state,
                            rect, icons, cache, fs=1.0, active=None,
                            blocked=None):
    """Draw category boxes with radio options."""
    if blocked is None:
        blocked = set()
    cat_font = style.get_font(L.font_size(int(CAT_FONT * fs)))
    opt_font = style.get_prop_font(L.font_size(int(OPT_FONT * fs)))
    isize = max(8, int(ICON_SIZE * fs * L.scale))
    pad_x = int(BOX_PAD_X * L.scale)

    for entry in picks_layout(categories, rect, fs):
        cat = entry["cat"]
        cat_blocked = (cat["trait_id"], "all") in blocked
        hx, hy = L.pos(entry["header"][0], entry["header"][1])
        hdr_col = COL_BLOCKED if cat_blocked else COL_CAT_HEADER
        surface.blit(cat_font.render(cat["name"].upper(), True,
                                     hdr_col), (hx, hy))

        bx, by = L.pos(entry["box"][0], entry["box"][1])
        bw, bh = L.size(entry["box"][2], entry["box"][3])
        box = pygame.Rect(bx, by, bw, bh)
        pygame.draw.rect(surface, COL_BOX_BORDER, box, 1,
                         border_radius=max(2, int(4 * L.scale)))

        cur = trait_state.get(cat["trait_id"], 0)
        for opt, (orx, ory, orw, orh) in entry["rows"]:
            ox, oy = L.pos(orx, ory)
            ow, oh = L.size(orw, orh)
            selected = (cur == opt["value"])
            dimmed = cat_blocked

            ic = icon(icons, cache,
                      "radio_on" if selected else "radio_off", isize)
            if ic:
                surface.blit(ic, (ox + pad_x, oy + (oh - isize) // 2))

            col = COL_BLOCKED if dimmed else (
                COL_OPTION_SEL if selected else COL_OPTION)
            lbl = opt_font.render(opt["label"], True, col)
            lx = ox + pad_x + isize + int(LABEL_GAP * L.scale)
            surface.blit(lbl, (lx, oy + (oh - lbl.get_height()) // 2))

            picks = opt["picks"]
            vcol = COL_BLOCKED if dimmed else (
                COL_VALUE_NEG if picks < 0 else COL_VALUE_POS)
            val = opt_font.render(str(picks), True, vcol)
            surface.blit(val, (ox + ow - val.get_width() - pad_x,
                               oy + (oh - val.get_height()) // 2))


def picks_hit_test(L, categories, rect, fs, sx, sy):
    """Screen point -> (category, option) or None."""
    for entry in picks_layout(categories, rect, fs):
        for opt, (orx, ory, orw, orh) in entry["rows"]:
            ox, oy = L.pos(orx, ory)
            ow, oh = L.size(orw, orh)
            if pygame.Rect(ox, oy, ow, oh).collidepoint(sx, sy):
                return entry["cat"], opt
    return None


# -- Special Abilities ------------------------------------

def specials_layout(specials, rect, fs=1.0):
    """Row rects (reference coords) for the specials list."""
    rx, ry, rw, rh = rect
    inner_x = rx + PANEL_INSET
    inner_w = rw - 2 * PANEL_INSET - SCROLLBAR_W
    row_h = SPEC_ROW_H * fs
    rows = []
    y = ry
    for spec in specials:
        rows.append((spec, (inner_x, y, inner_w, row_h)))
        y += row_h + SPEC_GAP_Y * fs
    return rows


def specials_content_height(specials, fs=1.0):
    return len(specials) * (SPEC_ROW_H * fs + SPEC_GAP_Y * fs)


def render_specials_panel(surface, L, style, specials, trait_state,
                          rect, icons, cache, fs=1.0, scroll=0,
                          active=None, blocked=None):
    """Checkbox list with values, selection highlight and scrollbar."""
    if blocked is None:
        blocked = set()
    opt_font = style.get_prop_font(L.font_size(int(OPT_FONT * fs)))
    isize = max(8, int(ICON_SIZE * fs * L.scale))
    pad_x = int(BOX_PAD_X * L.scale)
    rx, ry, rw, rh = rect
    clip_x, clip_y = L.pos(rx, ry)
    clip_w, clip_h = L.size(rw, rh)
    prev_clip = surface.get_clip()
    surface.set_clip(pygame.Rect(clip_x, clip_y, clip_w, clip_h))

    for spec, (orx, ory, orw, orh) in specials_layout(specials, rect, fs):
        ox, oy = L.pos(orx, ory - scroll)
        ow, oh = L.size(orw, orh)
        if oy + oh < clip_y or oy > clip_y + clip_h:
            continue
        checked = (trait_state.get(spec["trait_id"], 0)
                   == spec.get("value", 1))
        dimmed = (spec["trait_id"], spec.get("value", 1)) in blocked

        if active is spec:
            row = pygame.Rect(ox, oy, ow, oh)
            hl = pygame.Surface(row.size, pygame.SRCALPHA)
            hl.fill(COL_ROW_SEL_BG)
            surface.blit(hl, row.topleft)
            pygame.draw.rect(surface, COL_ROW_SEL_BD, row, 1,
                             border_radius=max(2, int(3 * L.scale)))

        ic = icon(icons, cache, "checkbox_off", isize)
        icon_x = ox + pad_x
        icon_y = oy + (oh - isize) // 2
        if ic:
            surface.blit(ic, (icon_x, icon_y))
        if checked:
            _draw_check(surface, icon_x, icon_y, isize, L.scale)

        label_col = COL_BLOCKED if dimmed else COL_OPTION
        lbl = opt_font.render(spec["name"], True, label_col)
        lx = icon_x + isize + int(LABEL_GAP * L.scale)
        surface.blit(lbl, (lx, oy + (oh - lbl.get_height()) // 2))

        picks = spec["picks"]
        vcol = COL_BLOCKED if dimmed else (
            COL_VALUE_NEG if picks < 0 else COL_VALUE_POS)
        val = opt_font.render(str(picks), True, vcol)
        surface.blit(val, (ox + ow - val.get_width() - pad_x * 2,
                           oy + (oh - val.get_height()) // 2))

    surface.set_clip(prev_clip)

    total_h = specials_content_height(specials, fs)
    if total_h > rh:
        track = pygame.Rect(clip_x + clip_w - int(PANEL_INSET * L.scale),
                            clip_y, max(4, int(SCROLLBAR_W * L.scale)),
                            clip_h)
        pygame.draw.rect(surface, COL_SCROLL_BG, track, border_radius=3)
        frac_h = min(1.0, rh / total_h)
        frac_y = min(1.0, scroll / total_h)
        thumb = pygame.Rect(track.x, track.y + int(track.h * frac_y),
                            track.w, max(20, int(track.h * frac_h)))
        pygame.draw.rect(surface, COL_SCROLL_TH, thumb, border_radius=3)


def _draw_check(surface, x, y, size, scale):
    """Green check mark inside a checkbox icon."""
    w = max(2, int(2 * scale))
    p1 = (x + size * 0.26, y + size * 0.52)
    p2 = (x + size * 0.44, y + size * 0.70)
    p3 = (x + size * 0.76, y + size * 0.30)
    pygame.draw.lines(surface, COL_CHECK, False, [p1, p2, p3], w)


def specials_hit_test(L, specials, rect, fs, scroll, sx, sy):
    """Screen point -> the special dict, or None.

    Returns the entry itself (not its trait_id) because Rich and
    Poor Home World share one trait_id and differ only by value.
    """
    rx, ry, rw, rh = rect
    px, py = L.pos(rx, ry)
    pw, ph = L.size(rw, rh)
    if not pygame.Rect(px, py, pw, ph).collidepoint(sx, sy):
        return None
    for spec, (orx, ory, orw, orh) in specials_layout(specials, rect, fs):
        ox, oy = L.pos(orx, ory - scroll)
        ow, oh = L.size(orw, orh)
        if pygame.Rect(ox, oy, ow, oh).collidepoint(sx, sy):
            return spec
    return None
