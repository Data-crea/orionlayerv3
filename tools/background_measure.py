#!/usr/bin/env python3
"""Measure the universal background, and the text standing on it — work order 173.

    python tools/background_measure.py                 # tables to stdout
    python tools/background_measure.py --json out.json
    python tools/background_measure.py --contrast-only --size 1920x1080

Analysis only: it writes nothing into the tree.

**THE PICTURE**, with work order 168's instruments
(`tools/frame_ring_measure.py`: `lapnorm` is detail per pixel with the
contrast divided out, `edge10_90` the median 10-90 % rise of the 400
strongest edges, `block8` JPEG blockiness, ~1.0 is none), on the whole
picture, at its own size and as `core.backgrounds.cover` draws it at
1080p, 1440p and 2160p. Plus the question 168 could only infer: the
EFFECTIVE DETAIL — the picture shrunk to a fraction of its width and
blown back up, the RMS error in % of the luma range. Grain is lost at
any shrink, so the error starts on a floor; the smallest fraction
still within a fifth above that floor is how many of its pixels carry
STRUCTURE, the rest being grain.

**THE TEXT ON IT.** Every screen is rendered three times: as it is;
with every font rendering blank ink (`pygame.font.Font` swapped for a
subclass, so the geometry is unchanged); and with the background
replaced by pure magenta and blank ink. A pixel the ink changes is
text; where the magenta pass shows magenta under it, the text stands
directly on the background — not on a panel, a button or the plate.
Those pixels are grouped into WORDS (ink joined by a 3 px dilation);
per word the text's luminance (90th percentile of its ink — the glyph core, not the
antialiased rim) is set against the BRIGHTEST background under it (95th
percentile) of the BACKGROUND PICTURE at those pixels — map content
such as a star's rays is not the background — as a WCAG contrast ratio. 4.5 is WCAG AA for body text,
3.0 for large text.
"""
import argparse
import json
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np  # noqa: E402
import pygame  # noqa: E402

SIZES = [(1920, 1080), (2560, 1440), (3840, 2160)]
MAGENTA = (255, 0, 255)


def lum(rgb):
    """WCAG relative luminance of an (..., 3) uint8 array."""
    c = rgb.astype(np.float64) / 255.0
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]


def arr(surf):
    return pygame.surfarray.array3d(surf).transpose(1, 0, 2)


# ── the picture ──────────────────────────────────────────

def picture(path):
    import frame_ring_measure as frm
    from core import backgrounds
    src = pygame.image.load(path)
    w, h = src.get_size()
    whole = np.ones((h, w), bool)
    out = {"file": os.path.relpath(path, ROOT), "size": [w, h],
           "aspect": round(w / h, 4), "aspect_16_9": round(16 / 9, 4),
           "source": frm.sharpness(arr(src), whole), "renders": {}}
    for W, H in SIZES + [(2576, 1432), (1920, 1200)]:
        r = backgrounds.cover(src, W, H)
        m = frm.sharpness(arr(r), np.ones((H, W), bool))
        m["upscale"] = round(max(W / w, H / h), 3)
        out["renders"][f"{W}x{H}"] = m
    y = frm.luma(arr(src))
    rng = float(y.max() - y.min()) or 1.0
    trip = {}
    for f in (0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.25, 0.2, 0.15):
        small = pygame.transform.smoothscale(src, (round(w * f), round(h * f)))
        back = frm.luma(arr(pygame.transform.smoothscale(small, (w, h))))
        trip[str(f)] = round(float(np.sqrt(((back - y) ** 2).mean())) / rng
                             * 100, 3)
    out["round_trip_rms_pct"] = trip
    # THE KNEE, not a fixed 1 %: a picture with film grain loses the
    # grain at ANY shrink, so its error is flat at first; the fraction
    # where it starts to climb above that floor (by a fifth) is where
    # structure — not grain — starts to go.
    floor = trip["0.9"]
    ok = [float(f) for f, e in trip.items() if e <= floor * 1.2]
    out["effective_fraction"] = min(ok)
    out["effective_width"] = round(w * out["effective_fraction"])
    return out


# ── the text on it ───────────────────────────────────────

class _Blank(pygame.font.Font):
    """A font whose ink is transparent: the same sizes, no pixels."""

    def render(self, text, antialias, color, background=None):
        s = super().render(text, antialias, color, background)
        return pygame.Surface(s.get_size(), pygame.SRCALPHA, 32)


def _pass(name, W, H, blank, magenta):
    import hud_evidence as he
    from core import backgrounds
    from core.hud import style as hudstyle
    real_font, real_scaled = pygame.font.Font, backgrounds.scaled
    backgrounds.reset()
    for fn in hudstyle._listeners:
        fn()
    if blank:
        pygame.font.Font = _Blank
    if magenta:
        def _mag(screen_name, w, h):
            s = pygame.Surface((w, h))
            s.fill(MAGENTA)
            return s
        backgrounds.scaled = _mag
    try:
        app = he.make_app(W, H)
        he.stage(app, name)
        d = app.dispatcher
        s = pygame.Surface((W, H))
        d.active.render(s)
        if d.overlay_name:
            d.screens[d.overlay_name].render(s)
        pic = None if magenta else backgrounds.scaled(d.active.SCREEN_NAME,
                                                      W, H)
        return arr(s), (arr(pic) if pic is not None else None)
    finally:
        pygame.font.Font, backgrounds.scaled = real_font, real_scaled
        backgrounds.reset()
        for fn in hudstyle._listeners:
            fn()


def contrast(name, W, H):
    a, pic = _pass(name, W, H, False, False)
    c, _ = _pass(name, W, H, True, False)
    m, _ = _pass(name, W, H, True, True)
    if pic is None:
        pic = c
    ink = (a != c).any(axis=2)
    on_bg = ink & (m == MAGENTA).all(axis=2)
    from scipy import ndimage
    la, lc = lum(a), lum(pic)
    # PER WORD, not per grid cell: ink joined into runs (a dilation of a
    # few px bridges the letters of a word, not two labels). A cell held
    # the dark drop shadow of a star's name alone and measured shadow
    # against background — 1.01 for a name that reads cleanly.
    grow = max(1, round(3 * H / 1080))
    words, n = ndimage.label(ndimage.binary_dilation(on_bg, iterations=grow))
    # THE BACKGROUND PICTURE under and right around the glyphs — not the
    # rendered pixels there: a star's rays cross its own name on the map
    # in the original too, and that is map content, not the background
    # this measures.
    ratios = []
    for i, box in enumerate(ndimage.find_objects(words), start=1):
        mine = words[box] == i
        sel = on_bg[box] & mine
        if sel.sum() < 6:
            continue
        t = float(np.percentile(la[box][sel], 90))
        b = float(np.percentile(lc[box][mine], 95))
        hi, lo = max(t, b), min(t, b)
        ratios.append(((hi + 0.05) / (lo + 0.05), (box[1].start,
                                                   box[0].start)))
    ratios.sort()
    return {"ink_px": int(ink.sum()), "on_background_px": int(on_bg.sum()),
            "words": len(ratios),
            "min": round(ratios[0][0], 2) if ratios else None,
            "min_at": ratios[0][1] if ratios else None,
            "p5": round(ratios[len(ratios) // 20][0], 2) if ratios else None,
            "below_4_5": sum(r < 4.5 for r, _ in ratios),
            "below_3": sum(r < 3.0 for r, _ in ratios)}


def screen_names():
    from core.config import SCREENS_DIR
    return sorted(n for n in os.listdir(SCREENS_DIR)
                  if os.path.isfile(os.path.join(SCREENS_DIR, n, "screen.py"))
                  and not n.startswith("_")) + ["game_menu_settings"]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--json")
    ap.add_argument("--size", help="WxH for the contrast part, default 1080p "
                                   "and 2160p")
    ap.add_argument("--contrast-only", action="store_true")
    args = ap.parse_args()
    pygame.init()
    pygame.display.set_mode((64, 64))
    from core import backgrounds
    report = {}
    if not args.contrast_only:
        report["picture"] = picture(os.path.join(ROOT, backgrounds.UNIVERSAL))
        p = report["picture"]
        print(f"{p['file']}: {p['size'][0]} x {p['size'][1]}, aspect "
              f"{p['aspect']} (16:9 is {p['aspect_16_9']}); effective "
              f"detail {p['effective_width']} px wide "
              f"(round trip {p['round_trip_rms_pct']})")
        s = p["source"]
        print(f"  source    lapnorm {s['lapnorm']:.3f}  edge {s['edge10_90']}  "
              f"block8 {s['block8']:.3f}")
        for k, m in p["renders"].items():
            print(f"  {k:10s}x{m['upscale']:<5} lapnorm {m['lapnorm']:.3f}  "
                  f"edge {m['edge10_90']}  block8 {m['block8']:.3f}")
    sizes = ([tuple(int(v) for v in args.size.split("x"))] if args.size
             else [(1920, 1080), (3840, 2160)])
    report["contrast"] = {}
    for W, H in sizes:
        for name in screen_names():
            r = contrast(name, W, H)
            report["contrast"][f"{name}@{W}x{H}"] = r
            print(f"  {name:20s} {W}x{H}  text on background: "
                  f"{r['on_background_px']:6d} px in {r['words']:3d} words, "
                  f"min {r['min']} at {r['min_at']}, p5 {r['p5']}, "
                  f"<4.5: {r['below_4_5']}, <3: {r['below_3']}")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
