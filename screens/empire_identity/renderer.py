"""Empire Identity rendering — banner grid, bordered boxes, image box.

Geometry lives in *_layout() functions used by BOTH the render and
the hit-test paths (custom_race pattern), so clicks can never drift
from what is drawn.

All coordinates are 1080p reference space; L.pos()/L.size() convert
at draw time. Banners come from core.banner (tinted at runtime,
cached per pixel size).
"""
import time
import pygame
from core import palette
from core import gridlayout

_c = palette.for_section("empire_identity")


# Same thin blue lines as the Custom Race category boxes
COL_BOX_BORDER = _c("box_border",   (42, 66, 104))
COL_BOX_BG     = _c("box_bg",       (12, 20, 38, 120))
COL_HEADER     = _c("header",       (120, 170, 255))
COL_HINT       = _c("hint",         (168, 176, 196))
COL_SELECTED   = _c("banner_selected", (70, 140, 255))
COL_HOVER      = _c("banner_hover", (60, 90, 150))
COL_TITLE      = _c("empire_title", (120, 170, 255))
COL_LABEL      = _c("preview_label", (110, 160, 240))
COL_VALUE      = _c("preview_value", (235, 240, 250))
COL_ICON       = _c("icon",         (80, 160, 255))

# Reference-space metrics
GRID_COLS   = 4
GRID_PAD    = 12      # inset inside the grid box
CELL_GAP    = 8
SEL_WIDTH   = 2
BOX_RADIUS  = 4


# -- Thin bordered box ------------------------------------

def draw_thin_box(surface, L, rect, fill=True):
    """Blue 1px outline with a dark translucent fill (custom_race look)."""
    bx, by = L.pos(rect[0], rect[1])
    bw, bh = L.size(rect[2], rect[3])
    r = pygame.Rect(bx, by, bw, bh)
    radius = max(2, int(BOX_RADIUS * L.scale))
    if fill and len(COL_BOX_BG) == 4 and COL_BOX_BG[3] < 255:
        fs = pygame.Surface(r.size, pygame.SRCALPHA)
        pygame.draw.rect(fs, COL_BOX_BG, fs.get_rect(),
                         border_radius=radius)
        surface.blit(fs, r.topleft)
    elif fill:
        pygame.draw.rect(surface, COL_BOX_BG[:3], r, border_radius=radius)
    pygame.draw.rect(surface, COL_BOX_BORDER, r, 1, border_radius=radius)
    return r


# -- Text helpers -----------------------------------------

def draw_centered(surface, font, text, color, rect_px):
    x, y, w, h = rect_px
    s = font.render(text, True, color)
    surface.blit(s, (x + (w - s.get_width()) // 2,
                     y + (h - s.get_height()) // 2))
    return s.get_height()


def draw_title_hint(surface, L, style, title, hint, rect, fs=1.0):
    """Bank Gothic heading (uppercase) with a proportional hint below,
    both centered in the box rect."""
    x, y = L.pos(rect[0], rect[1])
    w, h = L.size(rect[2], rect[3])
    tfont = style.get_font(L.font_size(int(19 * fs)))
    hfont = style.get_prop_font(L.font_size(int(16 * fs)))
    t = tfont.render(title.upper(), True, COL_HEADER)
    hs = hfont.render(hint, True, COL_HINT)
    total = t.get_height() + int(4 * L.scale) + hs.get_height()
    ty = y + (h - total) // 2
    surface.blit(t, (x + (w - t.get_width()) // 2, ty))
    surface.blit(hs, (x + (w - hs.get_width()) // 2,
                      ty + t.get_height() + int(4 * L.scale)))


# -- Banner grid ------------------------------------------

def banner_grid_layout(colors, rect, cols=GRID_COLS):
    """Cell rects (reference coords) for the banner grid, laid out
    in `cols` columns, square cells, centered inside `rect`.

    Returns [(color_key, (x, y, w, h)), ...]. Thin wrapper around
    core.gridlayout.packed_grid (shared with select_race's portrait
    grid) so the arithmetic lives in one place.
    """
    return gridlayout.packed_grid(colors, rect, cols,
                                  pad=GRID_PAD, gap=CELL_GAP)


def render_banner_grid(surface, L, colors, race, selected, hover,
                       rect, renderer):
    """Draw the 4x2 banner tiles with selection / hover outline."""
    for key, (cx, cy, cw, ch) in banner_grid_layout(colors, rect):
        px, py = L.pos(cx, cy)
        pw, ph = L.size(cw, ch)
        cell = pygame.Rect(px, py, pw, ph)
        inset = max(2, int(4 * L.scale))
        if renderer:
            img = renderer.get_scaled(key, race, ph - 2 * inset)
            surface.blit(img, (px + (pw - img.get_width()) // 2,
                               py + inset))
        else:
            pygame.draw.rect(surface, (80, 40, 40), cell, 1)
        if key == selected:
            pygame.draw.rect(surface, COL_SELECTED, cell,
                             max(1, int(SEL_WIDTH * L.scale)),
                             border_radius=max(2, int(3 * L.scale)))
        elif key == hover:
            pygame.draw.rect(surface, COL_HOVER, cell, 1,
                             border_radius=max(2, int(3 * L.scale)))


def banner_hit_test(L, colors, rect, sx, sy):
    """Screen point -> color key or None."""
    for key, (cx, cy, cw, ch) in banner_grid_layout(colors, rect):
        px, py = L.pos(cx, cy)
        pw, ph = L.size(cw, ch)
        if pygame.Rect(px, py, pw, ph).collidepoint(sx, sy):
            return key
    return None


# -- Image box (cover-fill, pan/zoom, edge fade) -----------

def _cover(img, tw, th, crop, zoom):
    """Cover-fill `img` into (tw, th) with zoom and crop anchor.
    Same semantics as the select_race portrait thumbnails."""
    iw, ih = img.get_width(), img.get_height()
    base = max(tw / iw, th / ih)
    scale = base * max(0.3, zoom)
    sw = max(tw, int(iw * scale))
    sh = max(th, int(ih * scale))
    scaled = pygame.transform.smoothscale(img, (sw, sh))
    cx = int(crop[0] * max(0, sw - tw))
    cy = int(crop[1] * max(0, sh - th))
    return scaled.subsurface((cx, cy, tw, th)).copy()


def _fade_mask(w, h, fade_left):
    """Alpha mask: transparent at the left edge, opaque after
    `fade_left` (fraction of width)."""
    mask = pygame.Surface((w, h), pygame.SRCALPHA)
    fw = max(1, int(w * fade_left))
    for x in range(fw):
        a = int(255 * (x / fw) ** 1.5)
        pygame.draw.line(mask, (255, 255, 255, a), (x, 0), (x, h))
    pygame.draw.rect(mask, (255, 255, 255, 255), (fw, 0, w - fw, h))
    return mask


def render_image_box(surface, L, img, rect, style, cache):
    """Draw `img` cover-filled into the box; style keys:
       zoom (float), crop ([0-1, 0-1]), fade_left (fraction, 0=off).
    The rendered surface is cached per (size, zoom, crop, fade)."""
    if img is None:
        return
    px, py = L.pos(rect[0], rect[1])
    pw, ph = L.size(rect[2], rect[3])
    if pw < 2 or ph < 2:
        return
    zoom = float(style.get("zoom", 1.0))
    crop = tuple(style.get("crop", [0.5, 0.5]))
    fade = float(style.get("fade_left", 0.0))
    key = (pw, ph, zoom, crop, fade)
    if cache.get("key") != key:
        out = _cover(img, pw, ph, crop, zoom)
        if fade > 0:
            out.blit(_fade_mask(pw, ph, fade), (0, 0),
                     special_flags=pygame.BLEND_RGBA_MULT)
        cache["key"] = key
        cache["surf"] = out
    surface.blit(cache["surf"], (px, py))


# -- Small vector icons for the preview -------------------

def draw_icon_ruler(surface, x, y, size):
    """Person silhouette: head + shoulders."""
    s = size
    head_r = max(2, int(s * 0.22))
    pygame.draw.circle(surface, COL_ICON,
                       (int(x + s / 2), int(y + s * 0.28)), head_r)
    body = pygame.Rect(int(x + s * 0.12), int(y + s * 0.55),
                       int(s * 0.76), int(s * 0.45))
    pygame.draw.rect(surface, COL_ICON, body,
                     border_top_left_radius=int(s * 0.38),
                     border_top_right_radius=int(s * 0.38))


def draw_icon_star(surface, x, y, size):
    """Eight-pointed star burst."""
    import math
    cx, cy = x + size / 2, y + size / 2
    pts = []
    for i in range(16):
        ang = math.pi * i / 8
        r = size / 2 if i % 2 == 0 else size * 0.2
        pts.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r))
    pygame.draw.polygon(surface, COL_ICON, pts)


# -- Preview text block -----------------------------------

def render_preview_text(surface, L, style, fs, rect, empire, rows):
    """Empire title plus (icon, label, value) rows inside `rect`."""
    x, y = L.pos(rect[0], rect[1])
    w, h = L.size(rect[2], rect[3])
    title_font = style.get_font(L.font_size(int(34 * fs)))
    label_font = style.get_font(L.font_size(int(15 * fs)))
    value_font = style.get_prop_font(L.font_size(int(24 * fs)))

    t = title_font.render(empire.upper(), True, COL_TITLE)
    surface.blit(t, (x, y))

    icon = int(24 * fs * L.scale)
    row_h = int(56 * fs * L.scale)
    ry = y + t.get_height() + int(24 * L.scale)
    col_label = x + icon + int(16 * L.scale)
    col_value = x + int(w * 0.36)
    for draw_icon, label, value in rows:
        base = ry + row_h // 2 - int(row_h * 0.2)
        draw_icon(surface, x, base - icon // 2, icon)
        ls = label_font.render(label.upper(), True, COL_LABEL)
        vs = value_font.render(value, True, COL_VALUE)
        surface.blit(ls, (col_label, base - ls.get_height() // 2))
        surface.blit(vs, (col_value, base - vs.get_height() // 2))
        ry += row_h


# -- Busy panel -------------------------------------------
#
# INVENTION, not a transcription. MOO2 shows nothing at all while it
# generates the galaxy — the screen simply sits there. OrionLayer has
# to say something, because its HD screen stays up across a wait the
# original never had to explain: the three dialogs are being answered
# by an injection chain, and the gap between the banner and the home
# star name is a whole mapgen (see core/injection.py).
#
# Marked here, in screen.py, in the status document and in the smoke
# test, which fails if the panel stops being drawn while a chain runs.
# It is cosmetic in the strict sense: it consumes no input, sends
# nothing to orion2re, and disappears with the chain.

COL_BUSY_TEXT = _c("busy_text",   (214, 226, 246))
COL_BUSY_STEP = _c("busy_step",   (150, 190, 255))
COL_BAR_BG    = _c("busy_bar_bg", (28, 44, 72))
COL_BAR_FILL  = _c("busy_bar",    (70, 140, 255))

BUSY_TITLE_FONT = 22      # reference units, Bank Gothic
BUSY_STEP_FONT  = 20      # reference units, proportional
BUSY_BAR_H      = 7
BUSY_BAR_GAP    = 6
BUSY_LINE_GAP   = 14      # between title and step line, stacked mode
BUSY_SEP        = "   —   "
BUSY_SWEEP_S    = 1.6     # seconds for one pass of the moving block
BUSY_SWEEP_FRAC = 0.42    # width of the block, share of one segment

# The panel has two layouts and picks by height, because the two
# places it wants to live are shaped differently: the empty strip
# above the identity panel is wide and shallow, anywhere over the
# preview artwork is roomy. Short box -> title and step share one
# line. Tall box -> stacked, the way the message popup reads.
# Nothing to configure: drag the box in F5 and the layout follows.

# Used only when the box is missing from boxes.json, so a bad edit
# cannot hide the fact that something is happening.
FALLBACK_PANEL = (110, 78, 1700, 46)
FALLBACK_INSET = (24, 7)


def busy_text_rect(panel):
    """Text area inset into a panel rect (reference units)."""
    ix, iy = FALLBACK_INSET
    return (panel[0] + ix, panel[1] + iy,
            panel[2] - 2 * ix, panel[3] - 2 * iy)


def render_busy_panel(surface, L, style, panel, text_rect, title,
                      step_text, step_no, step_count, waited,
                      elapsed_fmt="", backdrop=None, now=None):
    """Progress box for a running injection chain.

    Same construction as the Custom Race message box: opaque, filled
    from the screen's own scaled background rather than a sampled
    colour, outlined with the shared thin border.
    """
    px, py = L.pos(panel[0], panel[1])
    pw, ph = L.size(panel[2], panel[3])
    if pw < 8 or ph < 8:
        return
    rect = pygame.Rect(px, py, pw, ph)
    if backdrop is not None and backdrop.get_rect().contains(rect):
        surface.blit(backdrop, (px, py), rect)
    else:
        surface.fill(COL_BOX_BG[:3], rect)
    style.draw_thin_border(surface, rect, L.scale)

    tx, ty = L.pos(text_rect[0], text_rect[1])
    tw, th = L.size(text_rect[2], text_rect[3])
    if tw < 8 or th < 8:
        return

    line = step_text
    if elapsed_fmt and waited >= 3.0:
        line = f"{line}   {elapsed_fmt.format(s=int(waited))}"

    title_size = max(8, L.font_size(BUSY_TITLE_FONT))
    step_size = max(8, L.font_size(BUSY_STEP_FONT))
    bar_h = max(2, int(BUSY_BAR_H * L.scale))
    gap = max(2, int(BUSY_LINE_GAP * L.scale))

    title_surf = style.render_text(title.upper(), title_size, COL_BUSY_TEXT)
    step_font = style.get_prop_font(step_size)
    step_surf = step_font.render(line, True, COL_BUSY_STEP)

    stacked = (title_surf.get_height() + gap + step_surf.get_height()
               + gap + bar_h) <= th
    if stacked:
        surface.blit(title_surf,
                     (tx + (tw - title_surf.get_width()) // 2, ty))
        surface.blit(step_surf,
                     (tx + (tw - step_surf.get_width()) // 2,
                      ty + title_surf.get_height() + gap))
    else:
        # One line: title, separator, step. Shrink the title first —
        # the step text is the part that carries information.
        # Proportional font for the separator on purpose: the DEMO
        # font maps every dash onto its watermark glyph (fundament,
        # section 3), and render_text would substitute a lone dash
        # into a string of its own anyway.
        sep = step_font.render(BUSY_SEP, True, COL_BUSY_STEP)
        total = (title_surf.get_width() + sep.get_width()
                 + step_surf.get_width())
        x = tx + max(0, (tw - total) // 2)
        row_h = max(title_surf.get_height(), step_surf.get_height())
        base = ty + (th - bar_h - gap // 2 - row_h) // 2
        for surf_ in (title_surf, sep, step_surf):
            surface.blit(surf_,
                         (x, base + (row_h - surf_.get_height()) // 2))
            x += surf_.get_width()

    _draw_progress_bar(surface, L,
                       pygame.Rect(tx, ty + th - bar_h, tw, bar_h),
                       step_no, step_count, now)


def _draw_progress_bar(surface, L, bar, step_no, step_count, now=None):
    """One segment per chain step: done segments solid, the running
    one carrying a block that sweeps back and forth.

    Motion rather than a fill percentage, because a chain step has no
    percentage — it is waiting for a field list that either arrives or
    does not.
    """
    count = max(1, step_count)
    gap = max(1, int(BUSY_BAR_GAP * L.scale))
    seg_w = max(2, (bar.width - gap * (count - 1)) // count)
    if now is None:
        now = time.monotonic()
    phase = (now % BUSY_SWEEP_S) / BUSY_SWEEP_S
    travel = abs(1.0 - 2.0 * phase)          # ping-pong 1 -> 0 -> 1

    for i in range(count):
        x = bar.x + i * (seg_w + gap)
        seg = pygame.Rect(x, bar.y, seg_w, bar.height)
        if i < step_no - 1:
            surface.fill(COL_BAR_FILL[:3], seg)
            continue
        surface.fill(COL_BAR_BG[:3], seg)
        if i != step_no - 1:
            continue
        block_w = max(2, int(seg_w * BUSY_SWEEP_FRAC))
        bx = seg.x + int((seg_w - block_w) * travel)
        surface.fill(COL_BAR_FILL[:3],
                     pygame.Rect(bx, seg.y, block_w, seg.height))
