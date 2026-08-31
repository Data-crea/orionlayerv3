"""Measure the original galaxy map star field from a screenshot.

The numbers in `screens/galaxy_map/starfield.py` came out of this
tool. It exists so they can be re-derived instead of believed — a
constant nobody can trace is a constant nobody dares change.

    python tools/starfield_measure.py shot.png
    python tools/starfield_measure.py shot.png --threshold 20 --grid 8x6

What it does, in order:

1. Finds the screenshot's upscale factor from the periodicity of its
   own column gradient. A scaled shot has a hard edge every `k`
   pixels; the strongest FFT peak of that signal is `k`. Everything
   afterwards is reported in NATIVE pixels.
2. Labels connected lit regions and keeps only those under 1.9
   native pixels across. Star sprites, names, nebulas and wormhole
   links are all larger and drop out.
3. Splits the survivors into grey and coloured by |R - G|, since the
   background field is grey and the leftovers are nebula fringe.
4. Reports coverage, the grey-level histogram, and how far the
   spatial distribution sits from uniform noise.

Point 4 is the one worth reading twice: cell counts four times
noisier than Poisson mean the original field is clumped, not
uniform — but the nebulas sit inside the measured rect and inflate
exactly that number, which is why `clumping` defaults to 0.

The threshold is swept by default. A count that moves smoothly with
the threshold is a brightness distribution; a count that jumps is a
measurement error (see the guardian icon in `v3_fundament.md`).
"""
import argparse
import collections
import math
import sys

try:
    import numpy as np
    from PIL import Image
except ImportError as exc:
    print("needs numpy and pillow: %s" % exc)
    sys.exit(2)


def detect_scale(gray):
    """Upscale factor of a screenshot, from its column gradient."""
    d = np.abs(np.diff(gray, axis=1)).sum(axis=0)
    if len(d) < 64:
        return 1.0
    d = d - d.mean()
    power = np.abs(np.fft.rfft(d * np.hanning(len(d)))) ** 2
    freqs = np.fft.rfftfreq(len(d))
    idx = int(np.argmax(power[1:])) + 1
    if freqs[idx] <= 0:
        return 1.0
    period = 1.0 / freqs[idx]
    return period if 1.05 <= period <= 12.0 else 1.0


def components(mask):
    """4-connected components as (min_y, min_x, max_y, max_x, pixels)."""
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    out = []
    ys, xs = np.nonzero(mask)
    for sy, sx in zip(ys.tolist(), xs.tolist()):
        if seen[sy, sx]:
            continue
        stack = [(sy, sx)]
        seen[sy, sx] = True
        pixels = []
        y0 = y1 = sy
        x0 = x1 = sx
        while stack:
            y, x = stack.pop()
            pixels.append((y, x))
            y0, y1 = min(y0, y), max(y1, y)
            x0, x1 = min(x0, x), max(x1, x)
            for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] \
                        and not seen[ny, nx]:
                    seen[ny, nx] = True
                    stack.append((ny, nx))
        out.append((y0, x0, y1, x1, pixels))
    return out


def measure(rgb, scale, threshold, grid):
    lit = rgb.max(axis=2)
    area = (lit.shape[0] / scale) * (lit.shape[1] / scale)
    tiers = collections.Counter()
    points = []
    blobs = 0
    blob_area = 0.0
    for y0, x0, y1, x1, pixels in components(lit > threshold):
        span = max(y1 - y0 + 1, x1 - x0 + 1) / scale
        if span > 1.9:
            blobs += 1
            blob_area += ((y1 - y0 + 1) / scale) * ((x1 - x0 + 1) / scale)
            continue
        py, px = max(pixels, key=lambda p: int(lit[p[0], p[1]]))
        r, g, b = (int(v) for v in rgb[py, px])
        if abs(r - g) > 6:
            tiers[None] += 1
            continue
        tiers[r] += 1
        points.append(((x0 + x1) / 2.0 / scale, (y0 + y1) / 2.0 / scale))
    return area, blob_area, blobs, tiers, points


def report(area, blob_area, blobs, tiers, points, grid):
    coloured = tiers.pop(None, 0)
    total = sum(tiers.values())
    clean = max(1.0, area - blob_area)
    print("map area         %.0f native px^2 gross, %.0f after removing "
          "%d large blobs" % (area, clean, blobs))
    print("grey point stars %d   coloured %d" % (total, coloured))
    if total:
        print("density          1 per %.1f native px^2  (%.2f %% coverage)"
              % (area / total, 100.0 * total / area))
        print("                 1 per %.1f blob-corrected — an UPPER bound: "
              "blob boxes overlap" % (clean / total))
        print("                 measure a nebula-free crop instead of "
              "trusting either")
    print()
    print("  grey   count   share  cumulative")
    run = 0
    for value in sorted(tiers):
        run += tiers[value]
        print("  %4d  %6d  %5.1f%%  %6.1f%%"
              % (value, tiers[value], 100.0 * tiers[value] / total,
                 100.0 * run / total))
    if not points:
        return
    gx, gy = grid
    arr = np.array(points)
    hist, _, _ = np.histogram2d(arr[:, 0], arr[:, 1], bins=[gx, gy])
    poisson = math.sqrt(hist.mean()) if hist.mean() else 0.0
    print()
    print("spatial spread over a %dx%d grid: mean %.1f, std %.1f, "
          "uniform noise would give %.1f (%.1fx)"
          % (gx, gy, hist.mean(), hist.std(), poisson,
             hist.std() / poisson if poisson else 0.0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image", help="screenshot of the original galaxy map")
    ap.add_argument("--threshold", type=int, default=None,
                    help="single threshold; omit to sweep")
    ap.add_argument("--crop", default=None,
                    help="x0,y0,x1,y1 in NATIVE pixels")
    ap.add_argument("--grid", default="8x6")
    ap.add_argument("--scale", type=float, default=None)
    args = ap.parse_args()

    rgb = np.asarray(Image.open(args.image).convert("RGB")).astype(int)
    scale = args.scale or detect_scale(rgb.mean(axis=2))
    print("%s  %dx%d  upscale %.3f  -> native %.0fx%.0f"
          % (args.image, rgb.shape[1], rgb.shape[0], scale,
             rgb.shape[1] / scale, rgb.shape[0] / scale))
    if args.crop:
        x0, y0, x1, y1 = (int(v) for v in args.crop.split(","))
        rgb = rgb[int(y0 * scale):int(y1 * scale),
                  int(x0 * scale):int(x1 * scale)]
        print("cropped to native (%d,%d)-(%d,%d)" % (x0, y0, x1, y1))
    grid = tuple(int(v) for v in args.grid.lower().split("x"))

    thresholds = ([args.threshold] if args.threshold
                  else [12, 20, 32, 48, 72])
    for i, thr in enumerate(thresholds):
        print()
        print("── threshold %d %s" % (thr, "─" * 40))
        report(*measure(rgb, scale, thr, grid), grid=grid)


if __name__ == "__main__":
    main()
