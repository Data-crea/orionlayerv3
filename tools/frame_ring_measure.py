#!/usr/bin/env python3
"""Measure the OUTER RING of every frame image — work order 168.

    python tools/frame_ring_measure.py                # tables to stdout
    python tools/frame_ring_measure.py --json out.json
    python tools/frame_ring_measure.py --evidence DIR # crops and renders
                                  # (`tools/frame_ring_evidence.py`)

Analysis only: it reads frame images and writes nothing into the tree.
The report is `doc/briefs/168-frame-evaluation.md`; this is how its
numbers are made, so anybody can rerun them.

WHAT "THE RING" IS, per image, from the image's own alpha and nothing
else (no box, no layout file — the question is about the artwork):

  1. opaque   alpha >= 250; hole alpha < 16 (`tools/frame_holes`'s
              threshold)
  2. per side the ring THICKNESS: on 41 scanlines spread over the middle
              60 % of that side, the distance from the image edge to the
              first hole pixel; the side's thickness is the MEDIAN, so a
              title plate or a strut met by a few scanlines does not
              move it. Also reported: the 10th..90th percentile of those
              41, which is how a plate, a rail or a strut shows up
  3. the band for SHARPNESS is COMMON to all frames: `BAND_REF` = 60
              reference px deep from each image edge, opaque pixels only,
              less 3 px at its inner side and eroded by one so no alpha
              edge is measured as "sharp metal". Every full-screen ring
              is at least 65.7 ref px thick, so the band never reaches a
              hole or an interior strut. The GAME menu's frame is a popup
              on a transparent canvas: its band is all of its opaque art.

THE RENDERS are what the app draws: `pygame.transform.smoothscale` of
the whole image straight to the window's 16:9 area, exactly
`ScreenBase._scale_frame` — 1920x1080, 2560x1440, 3840x2160. The ring
mask is scaled with it (nearest).

THE METRICS, on luma (0.299 R + 0.587 G + 0.114 B) inside the ring:

  lapvar      variance of the 3x3 Laplacian (scipy.ndimage.laplace).
              Grows with sharpness AND with contrast.
  lapnorm     lapvar / variance of luma — the same with the contrast
              divided out, so two frames of different brightness compare
  edge10_90   the median 10 %-90 % rise distance, in pixels of the image
              measured, across the 400 strongest edges of the ring: at
              each of the top Sobel magnitudes (non-maximum suppressed,
              >= 12 px apart), a 25 px luma profile along the dominant
              gradient axis, the rise from 10 % to 90 % of its range at
              the crossings nearest the centre, linearly interpolated. A crisp edge is 1-2 px; an upscale
              by k multiplies it by about k.
  block8      JPEG-style blockiness: mean |horizontal gradient| on
              columns x % 8 == 7 over the mean on all other columns (and
              the same vertically), averaged. ~1.0 is no 8-px grid.
  sym_*       mirror symmetry inside the common band: mean absolute luma
              difference (0..255) between the top-left corner square
              (60 x 60 ref px) and each other corner flipped onto it, the
              left band against the right one flipped, the top against
              the bottom — opaque pixels of both only. 0 is a mirrored
              copy; the scale is luma levels.
  inner_soft  pixels with 16 <= alpha < 250 counted along the inner edge
              of each side on the same 41 scanlines, median: 0-1 is a
              hard cut a hole can be measured off, more is feathered.
  inner_wobble  the 10th..90th percentile spread of the inner edge
              position over those scanlines, in image px — 0 for a
              straight edge, large where a side has struts or plates.
"""
import argparse
import json
import os
import sys

import numpy as np

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame  # noqa: E402
from scipy import ndimage  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.expanduser("~/orionlayer-fixtures")

#: The candidates. In the tree first, then the 18 September set that
#: Data delivered and that sits outside the tree (work order 132).
CANDIDATES = [
    ("galaxy_map", os.path.join(ROOT, "screens/galaxy_map/assets/frame.png")),
    ("colony_summary", os.path.join(ROOT, "screens/colony_summary/assets/frame.png")),
    ("planets", os.path.join(ROOT, "screens/planets/assets/frame.png")),
    ("fleets", os.path.join(ROOT, "screens/fleets/assets/frame.png")),
    ("game_menu", os.path.join(ROOT, "screens/game_menu/assets/frame.png")),
    ("in:frame_plain", os.path.join(FIX, "incoming/frames_18sep/frame_plain.png")),
    ("in:frame_map_sidebar", os.path.join(FIX, "incoming/frames_18sep/frame_map_sidebar.png")),
    ("in:frame_map_4panels", os.path.join(FIX, "incoming/frames_18sep/frame_map_4panels_7buttons.png")),
]
RENDERS = ((1920, 1080), (2560, 1440), (3840, 2160))
REF_W, REF_H = 1920, 1080
OPAQUE, HOLE = 250, 16
SCANLINES = 41
KEEP_OFF_INNER = 3


def load(path):
    surf = pygame.image.load(path)
    rgb = surf_arrays(surf)
    alpha = (pygame.surfarray.pixels_alpha(surf).T.copy()
             if surf.get_flags() & pygame.SRCALPHA
             else np.full(rgb.shape[:2], 255, np.uint8))
    return surf, rgb, alpha


def luma(rgb):
    return (0.299 * rgb[..., 0] + 0.587 * rgb[..., 1]
            + 0.114 * rgb[..., 2]).astype(np.float64)


def side_scan(alpha, side):
    """Per scanline: thickness to the first hole pixel and the number of
    soft-alpha pixels just before it. Scanlines over the middle 60 %."""
    h, w = alpha.shape
    if side in ("left", "right"):
        pos = np.linspace(0.2 * h, 0.8 * h, SCANLINES).astype(int)
        lines = [alpha[p, :] if side == "left" else alpha[p, ::-1]
                 for p in pos]
    else:
        pos = np.linspace(0.2 * w, 0.8 * w, SCANLINES).astype(int)
        lines = [alpha[:, p] if side == "top" else alpha[::-1, p]
                 for p in pos]
    thick, soft = [], []
    for line in lines:
        # From the first OPAQUE pixel: a popup frame (the GAME menu's)
        # sits on a transparent canvas, and its margin is not a hole.
        solid = np.nonzero(line >= OPAQUE)[0]
        start = int(solid[0]) if len(solid) else 0
        holes = np.nonzero(line[start:] < HOLE)[0]
        t = start + (int(holes[0]) if len(holes) else len(line) - start)
        thick.append(t)
        # soft pixels in the last 12 before the hole
        seg = line[max(0, t - 12):t]
        soft.append(int(((seg >= HOLE) & (seg < OPAQUE)).sum()))
    return np.array(thick), np.array(soft)


def ring_geometry(alpha):
    out = {}
    for side in ("left", "right", "top", "bottom"):
        t, s = side_scan(alpha, side)
        out[side] = {"median": int(np.median(t)),
                     "min": int(np.percentile(t, 10)),
                     "max": int(np.percentile(t, 90)),
                     "soft": float(np.median(s)),
                     "wobble": int(np.percentile(t, 90)
                                   - np.percentile(t, 10))}
    return out


#: THE COMMON BAND for the sharpness metrics: this deep from each edge,
#: in REFERENCE px, on every frame — the order's "same regions on every
#: frame". 60 is under every full-screen frame's measured ring (the
#: thinnest median is 65.7 ref px, the galaxy map's top), so the band
#: never reaches a hole or an interior strut; what it holds is outer
#: metal, corners, lights and rivets. The Fleets frame's "first hole"
#: distance is 116-228 ref px because a dark chassis plate lies between
#: its ring and its holes; the band keeps that plate out too.
BAND_REF = 60


def ring_mask(alpha, geo, popup=False):
    h, w = alpha.shape
    if popup:
        # One opening, the whole opaque art is the ring.
        return ndimage.binary_erosion(alpha >= OPAQUE,
                                      iterations=KEEP_OFF_INNER)
    m = np.zeros_like(alpha, bool)
    l = r = int(round(BAND_REF * w / REF_W)) + KEEP_OFF_INNER
    t = b = int(round(BAND_REF * h / REF_H)) + KEEP_OFF_INNER
    k = KEEP_OFF_INNER
    m[:, :max(0, l - k)] = True
    m[:, w - max(0, r - k):] = True
    m[:max(0, t - k), :] = True
    m[h - max(0, b - k):, :] = True
    return m & (alpha >= OPAQUE)


#: Half the profile length: 12 px each side, long enough for an edge
#: that a 2.3x upscale has spread over ~5 px.
HALF = 12


def edge_widths(y, mask, n=400):
    gx = ndimage.sobel(y, axis=1)
    gy = ndimage.sobel(y, axis=0)
    mag = np.hypot(gx, gy) * mask
    # non-maximum suppression over a 12 px neighbourhood
    peak = (mag == ndimage.maximum_filter(mag, size=12)) & (mag > 0)
    idx = np.argwhere(peak)
    vals = mag[peak]
    order = np.argsort(vals)[::-1][:n]
    widths = []
    h, w = y.shape
    for (py, px) in idx[order]:
        horiz = abs(gx[py, px]) >= abs(gy[py, px])
        if horiz:
            if px < HALF or px > w - HALF - 1:
                continue
            prof = y[py, px - HALF:px + HALF + 1]
        else:
            if py < HALF or py > h - HALF - 1:
                continue
            prof = y[py - HALF:py + HALF + 1, px]
        lo, hi = prof.min(), prof.max()
        if hi - lo < 20:
            continue
        # orient rising
        if prof[0] > prof[-1]:
            prof = prof[::-1]
        p10 = lo + 0.1 * (hi - lo)
        p90 = lo + 0.9 * (hi - lo)

        # The crossing NEAREST the centre, walking out from it: a long
        # profile holds neighbouring edges too, and the first crossing
        # from the end would measure one of them.
        c = HALF

        def cross(level):
            best = None
            for i in range(1, len(prof)):
                if prof[i - 1] < level <= prof[i] and (
                        best is None or abs(i - c) < abs(best[0] - c)):
                    best = (i, prof[i - 1])
            if best is None:
                return None
            i = best[0]
            return i - 1 + (level - prof[i - 1]) / (prof[i] - prof[i - 1])
        a, b = cross(p10), cross(p90)
        if a is not None and b is not None and b >= a:
            widths.append(b - a)
    return float(np.median(widths)) if widths else None, len(widths)


def blockiness(y, mask):
    gx = np.abs(np.diff(y, axis=1))
    gy = np.abs(np.diff(y, axis=0))
    mx = mask[:, 1:] & mask[:, :-1]
    my = mask[1:, :] & mask[:-1, :]
    cols = np.arange(gx.shape[1]) % 8 == 7
    rows = np.arange(gy.shape[0]) % 8 == 7
    def ratio(g, m, sel, axis):
        on = g[:, sel][m[:, sel]] if axis == 1 else g[sel, :][m[sel, :]]
        off = g[:, ~sel][m[:, ~sel]] if axis == 1 else g[~sel, :][m[~sel, :]]
        return float(on.mean() / off.mean()) if len(on) and off.mean() else None
    a, b = ratio(gx, mx, cols, 1), ratio(gy, my, rows, 0)
    vals = [v for v in (a, b) if v is not None]
    return float(np.mean(vals)) if vals else None


def sharpness(rgb, mask):
    y = luma(rgb)
    lap = ndimage.laplace(y)
    sel = mask & ndimage.binary_erosion(mask, iterations=1)
    lapvar = float(lap[sel].var()) if sel.any() else None
    lv = float(y[sel].var()) if sel.any() else None
    ew, n = edge_widths(y, sel)
    return {"lapvar": lapvar, "lapnorm": (lapvar / lv) if lv else None,
            "edge10_90": ew, "edges": n, "block8": blockiness(y, sel)}


def symmetry(rgb, geo, alpha):
    """Mirror differences inside the COMMON band (`BAND_REF`), opaque
    pixels of both halves only — the same regions on every frame."""
    y = luma(rgb)
    h, w = y.shape
    sx = int(round(BAND_REF * w / REF_W))
    sy = int(round(BAND_REF * h / REF_H))
    op = alpha >= OPAQUE

    def mad(a, b, ma, mb):
        m = ma & mb
        return float(np.abs(a - b)[m].mean()) if m.any() else None
    cut = lambda img, ys, xs: img[ys, xs]
    TL = (slice(0, sy), slice(0, sx))
    TR = (slice(0, sy), slice(w - sx, w))
    BL = (slice(h - sy, h), slice(0, sx))
    BR = (slice(h - sy, h), slice(w - sx, w))
    fl = lambda a: a[:, ::-1]
    fu = lambda a: a[::-1, :]
    tl, tlm = cut(y, *TL), cut(op, *TL)
    mid_y = slice(int(.2 * h), int(.8 * h))
    mid_x = slice(int(.2 * w), int(.8 * w))
    return {"band_px": [sx, sy],
            "tl_tr": mad(tl, fl(cut(y, *TR)), tlm, fl(cut(op, *TR))),
            "tl_bl": mad(tl, fu(cut(y, *BL)), tlm, fu(cut(op, *BL))),
            "tl_br": mad(tl, fu(fl(cut(y, *BR))), tlm, fu(fl(cut(op, *BR)))),
            "left_right": mad(y[mid_y, :sx], fl(y[mid_y, w - sx:]),
                              op[mid_y, :sx], fl(op[mid_y, w - sx:])),
            "top_bottom": mad(y[:sy, mid_x], fu(y[h - sy:, mid_x]),
                              op[:sy, mid_x], fu(op[h - sy:, mid_x]))}


def render(surf, size):
    return pygame.transform.smoothscale(surf, size)


#: The GAME menu is not stretched to the window: `gmframe.placement`
#: scales it by ONE factor, the galaxy map's `map_area` height (844 ref
#: px at every resolution) over the image's height.
POPUP_REF_H = 844


def render_size(size, window, popup):
    if not popup:
        return window
    k = POPUP_REF_H * window[1] / REF_H / size[1]
    return (round(size[0] * k), round(size[1] * k))


def surf_arrays(surf):
    return pygame.surfarray.pixels3d(surf).transpose(1, 0, 2).copy()


def measure(name, path):
    surf, rgb, alpha = load(path)
    h, w = alpha.shape
    geo = ring_geometry(alpha)
    popup = name == "game_menu"
    mask = ring_mask(alpha, geo, popup)
    kx, ky = ((POPUP_REF_H / h,) * 2 if popup else (REF_W / w, REF_H / h))
    out = {"name": name, "path": path, "size": [w, h], "popup": popup,
           "has_alpha": bool((alpha < 255).any()),
           "aspect": round(w / h, 4),
           "scale": {f"{rw}x{rh}": [round(sw / w, 3), round(sh / h, 3)]
                     for rw, rh in RENDERS for sw, sh in
                     [render_size((w, h), (rw, rh), popup)]},
           "geometry": geo,
           "ring_ref_px": {
               "left": round(geo["left"]["median"] * kx, 1),
               "right": round(geo["right"]["median"] * kx, 1),
               "top": round(geo["top"]["median"] * ky, 1),
               "bottom": round(geo["bottom"]["median"] * ky, 1)},
           "ring_pixels": int(mask.sum()),
           "source": sharpness(rgb, mask),
           "symmetry": symmetry(rgb, geo, alpha)}
    r = out["ring_ref_px"]
    out["content_ref"] = [round(w * kx - r["left"] - r["right"], 1),
                          round(h * ky - r["top"] - r["bottom"], 1)]
    mask_surf = pygame.Surface((w, h))
    pygame.surfarray.blit_array(mask_surf, (mask.T * 255).astype(np.uint8)[..., None].repeat(3, 2))
    out["renders"] = {}
    for rw, rh in RENDERS:
        size = render_size((w, h), (rw, rh), popup)
        rs = render(surf, size)
        rm = pygame.transform.scale(mask_surf, size)
        m = pygame.surfarray.pixels_red(rm).T > 127
        out["renders"][f"{rw}x{rh}"] = sharpness(surf_arrays(rs), m)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json")
    ap.add_argument("--evidence")
    args = ap.parse_args()
    pygame.init()
    results = []
    for name, path in CANDIDATES:
        if not os.path.exists(path):
            print(f"{name}: not on this disk ({path})")
            continue
        results.append(measure(name, path))
    fmt = lambda v, p=2: "-" if v is None else f"{v:.{p}f}"
    print(f"{'frame':22} {'size':>10} {'x@1080':>12} {'x@2160':>12} "
          f"{'ring L/R/T/B ref px':>22} {'content':>13}")
    for r in results:
        s = r["scale"]
        g = r["ring_ref_px"]
        print(f"{r['name']:22} {r['size'][0]:>4}x{r['size'][1]:<5} "
              f"{s['1920x1080'][0]:>5}/{s['1920x1080'][1]:<6} "
              f"{s['3840x2160'][0]:>5}/{s['3840x2160'][1]:<6} "
              f"{g['left']:>5}/{g['right']}/{g['top']}/{g['bottom']:<6} "
              f"{r['content_ref'][0]}x{r['content_ref'][1]}")
    print()
    print(f"{'frame':22} {'lapnorm src':>11} {'1080':>7} {'1440':>7} "
          f"{'2160':>7} {'edge src':>9} {'1080':>6} {'1440':>6} {'2160':>6} "
          f"{'block8':>7}")
    for r in results:
        rr = r["renders"]
        print(f"{r['name']:22} {fmt(r['source']['lapnorm'], 3):>11} "
              + " ".join(f"{fmt(rr[k]['lapnorm'], 3):>7}" for k in
                         ("1920x1080", "2560x1440", "3840x2160"))
              + f" {fmt(r['source']['edge10_90']):>9} "
              + " ".join(f"{fmt(rr[k]['edge10_90']):>6}" for k in
                         ("1920x1080", "2560x1440", "3840x2160"))
              + f" {fmt(r['source']['block8']):>7}")
    print()
    print(f"{'frame':22} {'tl-tr':>6} {'tl-bl':>6} {'tl-br':>6} {'L-R':>6} "
          f"{'T-B':>6}  {'soft L/R/T/B':>14} {'wobble L/R/T/B':>16}  "
          f"{'spread (min..max) L | R | T | B'}")
    for r in results:
        sy, g = r["symmetry"], r["geometry"]
        sides = ("left", "right", "top", "bottom")
        print(f"{r['name']:22} {fmt(sy['tl_tr'], 1):>6} "
              f"{fmt(sy['tl_bl'], 1):>6} {fmt(sy['tl_br'], 1):>6} "
              f"{fmt(sy['left_right'], 1):>6} {fmt(sy['top_bottom'], 1):>6}  "
              f"{'/'.join(fmt(g[s]['soft'], 0) for s in sides):>14} "
              f"{'/'.join(str(g[s]['wobble']) for s in sides):>16}  "
              + " | ".join(f"{g[s]['min']}..{g[s]['max']}" for s in sides))
    if args.json:
        with open(args.json, "w") as fh:
            json.dump(results, fh, indent=1)
    if args.evidence:
        import frame_ring_evidence
        frame_ring_evidence.evidence(results, args.evidence)
    return 0


if __name__ == "__main__":
    sys.exit(main())
