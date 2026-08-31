"""Editor overlay rendering — selection, info bar, help, fields.

Pure drawing functions; all state lives on the Editor instance
passed in as `ed`. Split from editor.py to keep both files under
the 300-line limit.
"""
import time
import pygame

from core.box import get_stored_resolutions
from core.editor.constants import (
    H_REF, G_REF, C_SEL, C_GLO, C_GLO_ACT, C_OUT, C_IBG, C_ITX,
    C_ASN, C_FTX, C_HELP_BG, C_HELP_KEY, C_HELP_TXT, C_HELP_HDR,
    FIELD_TYPES, HELP_SECTIONS,
)


def render(ed, surface):
    """Full editor overlay. Called from the main render loop."""
    if not ed.active:
        return
    L = ed.app.layout
    scr = ed.app.dispatcher.top
    if not scr:
        return
    for box in scr.boxes:
        if box.screen_rect:
            pygame.draw.rect(surface, C_OUT, box.screen_rect, 1)
    if ed.selected and ed.selected.screen_rect:
        draw_sel(ed, surface, L)
    draw_info(ed, surface, L)
    if ed.show_fields:
        draw_fields(ed, surface, L)
    if ed.show_help:
        draw_help(ed, surface, L)
    f = ed.app.style.get_font(L.font_size(14))
    res = f"{ed.app.win_w}x{ed.app.win_h}"
    gk = ed.glow_key
    if gk:
        badge = f"EDITOR [{res}]  glow: {gk.upper()}"
    else:
        badge = f"EDITOR [{res}]  (H = Help)"
    surface.blit(f.render(badge, True,
                 C_GLO_ACT if gk else C_SEL), (10, 10))
    if ed._save_flash and time.monotonic() - ed._save_flash < 2:
        sf = ed.app.style.get_font(L.font_size(18))
        surface.blit(sf.render(f"SAVED [{res}]", True, C_ASN),
                     (10, 38))


def draw_sel(ed, surface, L):
    box = ed.selected
    r = box.screen_rect
    pygame.draw.rect(surface, C_SEL, r, 2)
    hs = max(4, int(H_REF * L.scale))
    bx, by, bw, bh = r.x, r.y, r.w, r.h
    for hx, hy in [(bx, by), (bx+bw, by), (bx, by+bh),
                    (bx+bw, by+bh), (bx+bw//2, by),
                    (bx+bw//2, by+bh), (bx, by+bh//2),
                    (bx+bw, by+bh//2)]:
        pygame.draw.rect(surface, C_SEL,
                         (hx-hs//2, hy-hs//2, hs, hs))
    if box.style.get("skin") == "button":
        glows = box.style.get("glows", {})
        gs = max(5, int(G_REF * L.scale))
        active_key = ed.glow_key
        for key, (cx, cy) in ed.corners(box).items():
            off = glows.get(key, [0, 0])
            px, py = L.pos(cx + off[0], cy + off[1])
            col = C_GLO_ACT if key == active_key else C_GLO
            w = 3 if key == active_key else 2
            pygame.draw.circle(surface, col, (px, py), gs, w)

def draw_info(ed, surface, L):
    ih = max(24, int(28 * L.scale))
    bg = pygame.Surface((ed.app.win_w, ih), pygame.SRCALPHA)
    bg.fill(C_IBG)
    iy = ed.app.win_h - ih
    surface.blit(bg, (0, iy))
    if ed.selected:
        b = ed.selected
        x, y, w, h = b.ref_rect
        skin = b.style.get("skin", "none")
        fid = b.field_id if b.field_id is not None else "none"
        gk = ed.glow_key
        if gk:
            off = b.style.get("glows", {}).get(gk, [0, 0])
            rot = b.style.get("glow_rot", {}).get(gk, 0)
            t = (f"'{b.name}' glow {gk.upper()} "
                 f"pos=({off[0]},{off[1]}) rot={rot}")
        else:
            extra = ""
            if b.name == "race_grid":
                scr = ed.app.dispatcher.top
                if scr and hasattr(scr, "_race_by_id"):
                    r = scr._race_by_id(scr._selected_id)
                    if r:
                        c = r.get("portrait_crop", [0.5, 0.5])
                        z = r.get("portrait_zoom", 1.0)
                        extra = (f" [{r['name']}] "
                                 f"zoom={z:.2f} "
                                 f"crop=({c[0]:.2f},"
                                 f"{c[1]:.2f})")
            if b.style.get("pannable"):
                c = b.style.get("crop", [0.5, 0.5])
                extra = (f" zoom={b.style.get('zoom', 1.0):.2f} "
                         f"crop=({c[0]:.2f},{c[1]:.2f})")
            co = b.style.get("content_offset")
            co_str = f" co=({co[0]},{co[1]})" if co else ""
            t = (f"'{b.name}' ({x},{y}) {w}x{h} "
                 f"skin={skin} field={fid} "
                 f"fs={b.style.get('font_scale', 1.0):.1f}"
                 f"{co_str}{extra}")
    else:
        scr = ed.app.dispatcher.top
        stored = []
        if scr and scr._screen_dir:
            stored = get_stored_resolutions(scr._screen_dir)
        res_key = f"{ed.app.win_w}x{ed.app.win_h}"
        if stored:
            src = "own" if res_key in stored else "fallback"
            res_info = f"  [{src} | saved: {', '.join(stored)}]"
        else:
            res_info = "  [no saved data]"
        t = ("Click to select | Ctrl+N button | "
             "Ctrl+I panel | H help" + res_info)
    f = ed.app.style.get_font(L.font_size(13))
    surface.blit(f.render(t, True, C_ITX), (10, iy + 4))

def help_geometry(font, sections, scale):
    """Column geometry for the help sheet, measured not guessed.

    The description column used to start at a fixed 160 reference
    pixels. Any key label wider than that — "Shift+Scroll /
    Alt+Scroll", "Corner/Edge Drag" — ran straight into its own
    description, and the same overflow pushed long descriptions into
    the neighbouring column. Both are font-dependent, so the fix has
    to ask the font instead of assuming a width.

    Returns (desc_x, content_w) in pixels, relative to a column's
    left edge.
    """
    keys = [k for _, rows in sections for k, _ in rows]
    descs = [d for _, rows in sections for _, d in rows]
    gap = max(12, int(24 * scale))
    desc_x = (max(font.size(k)[0] for k in keys) + gap) if keys else 0
    widest = max(font.size(d)[0] for d in descs) if descs else 0
    return desc_x, desc_x + widest


def draw_help(ed, surface, L):
    w, h = ed.app.win_w, ed.app.win_h
    overlay = pygame.Surface((w, h), pygame.SRCALPHA)
    overlay.fill(C_HELP_BG)
    surface.blit(overlay, (0, 0))
    fs_title = L.font_size(22)
    fs_hdr = L.font_size(16)
    fs_row = L.font_size(13)
    ft = ed.app.style.get_font(fs_title)
    fh = ed.app.style.get_font(fs_hdr)
    fr = ed.app.style.get_font(fs_row)
    title = ft.render("EDITOR SHORTCUTS", True, C_SEL)
    surface.blit(title, ((w - title.get_width()) // 2,
                          int(60 * L.scale)))
    desc_x, content_w = help_geometry(fr, HELP_SECTIONS, L.scale)
    col_w = max(int(420 * L.scale), content_w)
    col_gap = int(60 * L.scale)
    total_w = col_w * 2 + col_gap
    cx = (w - total_w) // 2
    cy = int(120 * L.scale)
    # Row and header height follow the font, so a larger UI scale
    # cannot squeeze the lines into each other.
    row_h = max(fr.get_linesize() + max(2, int(4 * L.scale)),
                int(22 * L.scale))
    hdr_h = max(fh.get_linesize() + max(4, int(8 * L.scale)),
                int(34 * L.scale))
    col = 0
    y = cy
    for section_name, shortcuts in HELP_SECTIONS:
        needed = hdr_h + len(shortcuts) * row_h + 12
        if y + needed > h - 80 * L.scale and col == 0:
            col = 1
            y = cy
        x = cx + col * (col_w + col_gap)
        hdr = fh.render(section_name, True, C_HELP_HDR)
        surface.blit(hdr, (x, y))
        y += hdr_h
        for key, desc in shortcuts:
            ks = fr.render(key, True, C_HELP_KEY)
            ds = fr.render(desc, True, C_HELP_TXT)
            surface.blit(ks, (x, y))
            surface.blit(ds, (x + desc_x, y))
            y += row_h
        y += int(12 * L.scale)
    foot = fr.render("Press H or click anywhere to close",
                     True, (120, 130, 150))
    surface.blit(foot, ((w - foot.get_width()) // 2,
                         h - int(50 * L.scale)))

def draw_fields(ed, surface, L):
    fields = (ed.app.client.state.fields
              if ed.app.connected else [])
    if not fields: return
    px, py, pw, ph = L.rect((1500, 80, 380, 700))
    bg = pygame.Surface((pw, ph), pygame.SRCALPHA)
    bg.fill((10, 14, 28, 220))
    surface.blit(bg, (px, py))
    pygame.draw.rect(surface, (60, 80, 120),
                     (px, py, pw, ph), 1)
    f = ed.app.style.get_font(L.font_size(13))
    surface.blit(f.render("FIELDS (click to assign)", True,
                          C_SEL), (px+8, py+6))
    fs = ed.app.style.get_font(L.font_size(11))
    rh = L.font_size(11) + 6
    y = py + 32
    for fi in fields:
        if fi.index < 1: continue
        if y + rh > py + ph: break
        hk = chr(fi.hotkey) if 32 < fi.hotkey < 127 else ""
        tp = FIELD_TYPES.get(fi.field_type, f"t{fi.field_type}")
        fw = fi.x_end - fi.x
        fh = fi.y_end - fi.y
        t = (f"[{fi.index:2d}]  {hk:1s}  {tp:<8s} "
             f"{fw}x{fh}  ({fi.x},{fi.y})")
        sel = (ed.selected and
               ed.selected.field_id == fi.index)
        surface.blit(fs.render(t, True,
                     C_ASN if sel else C_FTX), (px+8, y))
        y += rh
