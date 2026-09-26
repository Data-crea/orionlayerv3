"""The panel GLASS, measured off Data's Select Race mockup — work order 174 B2.

`doc/briefs/174-mockup-select-race.png` (Data's, 26 September 2026,
1683 x 935) shows the look Data wants in its right-hand box: the
background's nebula through a dark gradient. It is a reference for the
look; nothing is cut from it. The background it was painted over is the
universal one (`assets/shared/backgrounds/universal.png`), re-painted by
the generator but close enough to regress against:

1. ALIGN: the universal picture, cover-scaled to the mockup's size, is
   shifted by whole pixels until its luma correlates best with the
   mockup's outside every box (the margins left, right and below).
2. REGRESS: inside the right-hand box, in bands that hold no text, each
   channel of the mockup is fitted as `bg * (1 - a) + g * a` — a straight
   line in the background under it, outliers (stars, stray glyphs)
   dropped once at 2.5 sigma. The slope gives the opacity `a`, the
   intercept the gradient's colour `g`.
3. FIT: opacity and colour against the band's height in the box, one
   straight line each; the ends are the gradient's top and bottom.

The bands are noisy (the generator re-painted the nebula, so the
background under the box is an estimate): opacity scatters by about
0.1 around the line. The numbers are what the look is fitted to, and
where they come from is part of them.
"""
import numpy as np
from PIL import Image

#: The right-hand box, in mockup px, and its text-free bands (y0, y1).
BOX = (1066, 102, 1590, 822)
BANDS = ((112, 130), (365, 395), (395, 425), (425, 455), (455, 485),
         (485, 515), (745, 765), (775, 800), (800, 815))
BAND_X = (1085, 1575)


def measure_glass(mockup_path, background_path):
    m = np.asarray(Image.open(mockup_path).convert("RGB")).astype(float)
    h, w = m.shape[:2]
    src = Image.open(background_path).convert("RGB")
    k = max(w / src.width, h / src.height)
    uw, uh = round(src.width * k), round(src.height * k)
    u = np.asarray(src.resize((uw, uh), Image.BILINEAR)).astype(float)
    outside = np.zeros((h, w), bool)
    outside[:, :105] = outside[:, 1600:] = outside[835:, :] = True
    best = None
    for dx in range(-4, 5):
        for dy in range(-5, 2):
            x0, y0 = (uw - w) // 2 + dx, (uh - h) // 2 + dy
            if x0 < 0 or y0 < 0 or x0 + w > uw or y0 + h > uh:
                continue
            c = u[y0:y0 + h, x0:x0 + w].mean(axis=2)
            r = float(np.corrcoef(m.mean(axis=2)[outside], c[outside])[0, 1])
            if best is None or r > best[0]:
                best = (r, dx, dy)
    r, dx, dy = best
    x0, y0 = (uw - w) // 2 + dx, (uh - h) // 2 + dy
    bg = u[y0:y0 + h, x0:x0 + w]
    ts, alphas, cols = [], [], []
    for ya, yb in BANDS:
        mm = m[ya:yb, BAND_X[0]:BAND_X[1]].reshape(-1, 3)
        bb = bg[ya:yb, BAND_X[0]:BAND_X[1]].reshape(-1, 3)
        coefs = []
        for ch in range(3):
            a_ = np.vstack([bb[:, ch], np.ones(len(bb))]).T
            c, *_ = np.linalg.lstsq(a_, mm[:, ch], rcond=None)
            err = mm[:, ch] - a_ @ c
            keep = np.abs(err) < 2.5 * np.std(err)
            c, *_ = np.linalg.lstsq(a_[keep], mm[keep, ch], rcond=None)
            coefs.append(c)
        a = 1.0 - float(np.mean([c[0] for c in coefs]))
        ts.append(((ya + yb) / 2 - BOX[1]) / (BOX[3] - BOX[1]))
        alphas.append(a)
        cols.append([c[1] / max(a, 1e-3) for c in coefs])
    ts, alphas, cols = np.array(ts), np.array(alphas), np.array(cols)
    a_top, a_bot = np.polyval(np.polyfit(ts, alphas, 1), [0.0, 1.0])
    top, bottom = [], []
    for ch in range(3):
        t0, t1 = np.polyval(np.polyfit(ts, cols[:, ch], 1), [0.0, 1.0])
        top.append(int(round(t0)))
        bottom.append(int(round(t1)))
    return {"top": top, "bottom": bottom,
            "alpha_top": round(float(a_top), 3),
            "alpha_bottom": round(float(a_bot), 3),
            "source": {"mockup": "doc/briefs/174-mockup-select-race.png",
                       "box": list(BOX), "bands": len(BANDS),
                       "align_shift": [dx, dy],
                       "align_correlation": round(r, 3)}}
