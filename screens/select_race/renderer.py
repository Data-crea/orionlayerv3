"""Select Race rendering — portrait grid.

Info panel rendering (name/description/traits) lives in
info_panel.py; both share the color constants defined here.

All positions come from box rects (1920x1080 reference).
"""
import pygame
from core import palette
from core import gridlayout

# Colors — every value can be overridden in the skin's
# colors.json under the "select_race" section.
_c = palette.for_section("select_race")

COL_HEADING   = _c("heading",    (138, 180, 232))
COL_LABEL     = _c("label",      (90, 122, 168))
COL_VALUE     = _c("value",      (200, 202, 212))
COL_GOOD      = _c("good",       (80, 200, 120))
COL_BAD       = _c("bad",        (212, 160, 74))
COL_NEUTRAL   = _c("neutral",    (138, 180, 232))
COL_FLAVOR    = _c("flavor",     (144, 152, 176))
COL_HIGHLIGHT = _c("highlight",  (100, 210, 140))
COL_KEYWORD   = _c("keyword",    (140, 185, 240))
COL_SUBTITLE  = _c("subtitle",   (120, 104, 176))
COL_SEPARATOR = _c("separator",  (60, 80, 120))
COL_SELECTED  = _c("selected",   (120, 170, 255))
COL_BORDER    = _c("border",     (50, 70, 110))
COL_CELL_BG   = _c("cell_bg",    (16, 20, 38, 160))
COL_NAME_SEL  = _c("name_selected", (180, 220, 255))
COL_GOLD      = _c("gold",       (212, 160, 74))

# Grid layout
GRID_COLS = 5
GRID_ROWS = 3
GRID_PAD = 16       # padding inside the grid panel
CELL_GAP = 12       # gap between cells
NAME_H = 32         # height reserved for name label below portrait
HEADER_H = 32       # "CHOOSE YOUR RACE" header height

# Font sizes
TITLE_FONT = 28
SUBTITLE_FONT = 15
BODY_FONT = 15
HEADING_FONT = 13
TRAIT_FONT = 15
NAME_FONT = 13


def grid_cell_rect(grid_rect, index):
    """Calculate cell rect in reference coords for grid index 0-14.

    Returns (x, y, w, h) in reference coords or None if out of range.
    Thin wrapper around core.gridlayout.grid_cell_rect (shared with
    empire_identity's banner grid) so the arithmetic lives in one
    place.
    """
    return gridlayout.grid_cell_rect(
        grid_rect, index, GRID_COLS, GRID_ROWS,
        pad=GRID_PAD, gap=CELL_GAP, header=HEADER_H)


# ── Portrait grid ────────────────────────────────────────

def render_race_grid(surface, L, style, races, selected_id, rect,
                     portraits, thumb_cache, fs_scale=1.0,
                     picture_mode=False):
    """Render 5x3 portrait grid with race names."""
    gx, gy, gw, gh = rect

    # Header
    hfs = L.font_size(int(HEADING_FONT * fs_scale))
    hfont = style.get_font(hfs)
    hx, hy = L.pos(gx + GRID_PAD, gy + GRID_PAD)
    hw = int((gw - GRID_PAD * 2) * L.scale)
    header = "SELECT RACE PICTURE" if picture_mode else "CHOOSE YOUR RACE"
    h_surf = hfont.render(header, True, COL_LABEL)
    surface.blit(h_surf, (hx + (hw - h_surf.get_width()) // 2, hy))

    nfs = L.font_size(int(NAME_FONT * fs_scale))
    name_font = style.get_font(nfs)

    for i, race in enumerate(races):
        # Hide Custom Race cell in picture mode
        if picture_mode and race.get("id") == 13:
            continue
        cell = grid_cell_rect(rect, i)
        if cell is None:
            continue
        cx, cy, cw, ch = cell
        sx, sy = L.pos(cx, cy)
        sw, sh = L.size(cw, ch)
        selected = (race["id"] == selected_id)

        # Portrait area (cell minus name label)
        name_sh = int(NAME_H * L.scale)
        port_h = sh - name_sh

        # Cell background
        bg = pygame.Surface((sw, port_h), pygame.SRCALPHA)
        bg.fill(COL_CELL_BG)
        surface.blit(bg, (sx, sy))

        # Portrait thumbnail
        img = portraits.get(race["id"])
        crop = race.get("portrait_crop", [0.5, 0.5])
        zoom = race.get("portrait_zoom", 1.0)
        if img:
            cache_key = (race["id"], sw, port_h)
            if cache_key not in thumb_cache:
                thumb_cache[cache_key] = _make_thumbnail(
                    img, sw, port_h, crop, zoom)
            surface.blit(thumb_cache[cache_key], (sx, sy))
        else:
            render_portrait_placeholder(surface, sx, sy, sw, port_h,
                                        (100, 120, 180), style)

        # Selection border
        if selected:
            bdr = pygame.Surface((sw, port_h), pygame.SRCALPHA)
            pygame.draw.rect(bdr, (*COL_SELECTED, 200),
                             (0, 0, sw, port_h), 3, border_radius=3)
            surface.blit(bdr, (sx, sy))
        else:
            pygame.draw.rect(surface, COL_BORDER,
                             (sx, sy, sw, port_h), 1, border_radius=2)

        # Race name below portrait
        is_custom = (race.get("key") == "custom" or race["id"] == 13)
        if is_custom:
            col = COL_GOLD
        elif selected:
            col = COL_NAME_SEL
        else:
            col = COL_HEADING
        n_surf = name_font.render(race["name"].upper(), True, col)
        nx = sx + (sw - n_surf.get_width()) // 2
        ny = sy + port_h + (name_sh - n_surf.get_height()) // 2
        surface.blit(n_surf, (nx, ny))


def _make_thumbnail(img, tw, th, crop=(0.5, 0.5), zoom=1.0):
    """Cover-fill thumbnail with zoom and crop.

    zoom=1.0: default cover-fill (image fills the cell exactly)
    zoom>1.0: zoom in (shows less of the image, more detail)
    zoom<1.0: zoom out (shows more of the image, may letterbox)
    crop=[0-1, 0-1]: anchor point for pan (0.5, 0.5 = center)
    """
    iw, ih = img.get_width(), img.get_height()
    base_scale = max(tw / iw, th / ih)
    scale = base_scale * max(0.3, zoom)
    sw = max(tw, int(iw * scale))
    sh = max(th, int(ih * scale))
    scaled = pygame.transform.smoothscale(img, (sw, sh))
    cx = int(crop[0] * max(0, sw - tw))
    cy = int(crop[1] * max(0, sh - th))
    return scaled.subsurface((cx, cy, tw, th)).copy()


# ── Portrait helpers ─────────────────────────────────────

def render_portrait_placeholder(surface, px, py, pw, ph, col, style=None):
    """Dark placeholder with ? symbol."""
    bg = pygame.Surface((pw, ph), pygame.SRCALPHA)
    bg.fill((20, 18, 35, 180))
    pygame.draw.rect(bg, (*col, 40), (0, 0, pw, ph), 1, border_radius=4)
    surface.blit(bg, (px, py))
    fs = max(8, ph // 4)
    sym_font = (style.get_prop_font(fs)
                if style else pygame.font.Font(None, fs))
    sym = sym_font.render("?", True, (*col, 80))
    surface.blit(sym, (px + (pw - sym.get_width()) // 2,
                       py + (ph - sym.get_height()) // 2))
