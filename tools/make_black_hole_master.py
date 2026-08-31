#!/usr/bin/env python3
"""Build the rotatable black hole master from a single source still.

The galaxy map draws one black hole drawing and rotates it at runtime
(renderer._black_hole_frame). That only works if the event horizon sits
exactly on the rotation axis: an off-axis horizon does not turn, it
orbits the centre, and at 117 px that is immediately visible.

This tool takes any still image of a black hole on a black background
and produces that master:

  1. removes baked-in point stars with a median filter (point sources
     vanish, disc filaments survive)
  2. locates the centre with a ring matched filter — a dark core inside
     a bright annulus — rather than trusting the source's framing
  3. measures the horizon and outer radius from the radial profile
  4. subtracts the source's noise floor BEFORE the alpha curve
  5. builds alpha from luma, with the horizon forced fully opaque
  6. crops to a circle, so rotation never clips a corner
  7. verifies the horizon lands on the axis and fails loudly if not

Why the noise floor matters: a gamma below 1 lifts faint detail, and it
lifts the source's noise with it. Without NOISE_FLOOR, 47 per cent of
the sprite was a barely-visible haze. That haze is invisible against
the near-black map, but it inflates the sprite — and because the sprite
is scaled to black_hole_dimension(), an inflated footprint shrinks the
black hole inside it.

Sizing is NOT baked in here. The renderer scales this master to
zoomtables.black_hole_dimension() * view.scale, so the master only has
to be large enough for the biggest window: 39 native px times the HD
factor, where the factor is map_area_width / 505.

Usage:
    python tools/make_black_hole_master.py
    python tools/make_black_hole_master.py --src other.png --margin 1.15
"""

import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

DEFAULT_SRC = "screens/galaxy_map/assets/_black_hole_src.png"
DEFAULT_OUT = "screens/galaxy_map/assets/black_hole.png"

STAR_MEDIAN_RADIUS = 3      # kills point sources, keeps disc filaments
NOISE_FLOOR = 14.0          # luma pedestal removed before the alpha curve
GLOW_KNEE = 34.0            # luma at which the glow becomes fully opaque
GLOW_GAMMA = 0.85           # < 1 lifts the faint outer filaments
BRIGHTNESS = 1.55           # compensates for the alpha cut
EDGE_FEATHER = 5.0          # px of soft falloff at the outer rim
OUTER_THRESHOLD = 0.06      # fraction of peak luma that ends the disc
HORIZON_THRESHOLD = 0.30    # fraction of peak luma that ends the horizon
MAX_AXIS_OFFSET = 2.0       # px; beyond this the sprite wobbles visibly


def find_centre(luma):
    """Ring matched filter: a dark core inside a bright annulus."""
    response = ndimage.gaussian_filter(luma, 30) - ndimage.gaussian_filter(luma, 9)
    margin = min(luma.shape) // 6
    response[:margin] = -1e9
    response[-margin:] = -1e9
    response[:, :margin] = -1e9
    response[:, -margin:] = -1e9
    cy, cx = np.unravel_index(np.argmax(response), response.shape)
    return int(cx), int(cy)


def radial_profile(luma, cx, cy, limit):
    y, x = np.mgrid[0:luma.shape[0], 0:luma.shape[1]]
    radius = np.hypot(y - cy, x - cx)
    out = np.zeros(limit)
    for r in range(limit):
        band = (radius >= r) & (radius < r + 1)
        if band.any():
            out[r] = luma[band].mean()
    return out


def measure(luma, cx, cy):
    """Return (horizon_radius, outer_radius) in source pixels."""
    limit = min(luma.shape) // 2
    profile = radial_profile(luma, cx, cy, limit)
    peak = int(np.argmax(profile))
    horizon = max(
        (r for r in range(1, peak)
         if profile[r] < profile[peak] * HORIZON_THRESHOLD),
        default=max(1, peak // 2),
    )
    outer = next(
        (r for r in range(peak, limit)
         if profile[r] < profile[peak] * OUTER_THRESHOLD),
        limit - 1,
    )
    return horizon, outer


def build_master(path, margin=1.04):
    source = np.asarray(Image.open(path).convert("RGB")).astype(float)

    cleaned = np.stack(
        [ndimage.median_filter(source[..., c], STAR_MEDIAN_RADIUS)
         for c in range(3)],
        axis=2,
    )
    stars_removed = int((np.abs(source - cleaned).max(axis=2) > 20).sum())

    luma = cleaned.max(axis=2)
    cx, cy = find_centre(luma)
    horizon, outer = measure(np.clip(luma - NOISE_FLOOR, 0, None), cx, cy)

    half = int(outer * margin)
    canvas = np.zeros((2 * half, 2 * half, 3))
    y0, x0 = cy - half, cx - half
    sy0, sx0 = max(0, y0), max(0, x0)
    sy1 = min(cleaned.shape[0], y0 + 2 * half)
    sx1 = min(cleaned.shape[1], x0 + 2 * half)
    canvas[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = cleaned[sy0:sy1, sx0:sx1]

    y, x = np.mgrid[0:2 * half, 0:2 * half]
    radius = np.hypot(y - half, x - half)
    lum = canvas.max(axis=2)

    glow = np.clip(np.clip(lum - NOISE_FLOOR, 0, None) / GLOW_KNEE, 0, 1)
    glow = glow ** GLOW_GAMMA
    core = np.clip((horizon + 2 - radius) / 2.0, 0, 1)
    alpha = np.maximum(glow, core)
    # Circular cut. Everything outside is empty, so rotating the square
    # can never move content into a corner and lose it.
    alpha *= np.clip((outer - radius) / EDGE_FEATHER, 0, 1)

    rgb = np.clip(canvas * BRIGHTNESS, 0, 255)
    rgb[radius <= horizon] = 0     # event horizon: real black, fully opaque

    # Blank the RGB under every transparent pixel. Masking alone leaves
    # the source's stars sitting in the corners at up to 174 — invisible
    # under a normal blit, and a bright square the moment anything
    # blends additively or switches blending off, because BLEND_RGB_ADD
    # and set_alpha(None) both ignore the alpha channel. The nebulas
    # already paid for this lesson once (see SpriteCache.
    # scaled_additive). Costs nothing here and removes the trap.
    rgb[alpha <= 0.004] = 0

    # The horizon must sit on the rotation axis. Verified, not assumed.
    core_mask = ndimage.binary_opening(
        (alpha > 0.8) & (rgb.max(axis=2) < 3), np.ones((5, 5)))
    hy, hx = np.where(core_mask)
    if len(hy) == 0:
        raise SystemExit("no event horizon found — is the source too bright?")
    offset = (float(hx.mean() - (half - 0.5)), float(hy.mean() - (half - 0.5)))

    visible = alpha > 0.04
    haze = float(((alpha > 0.04) & (lum < 12)).sum() / max(1, visible.sum()))

    master = np.dstack([rgb, alpha * 255]).astype(np.uint8)
    stats = {
        "stars_removed": stars_removed,
        "centre": (cx, cy),
        "horizon_r": horizon,
        "outer_r": outer,
        "master_px": 2 * half,
        "horizon_offset": offset,
        "horizon_fraction": 2.0 * horizon / (2 * half),
        "haze_fraction": haze,
    }
    return Image.fromarray(master, "RGBA"), stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=DEFAULT_SRC)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--margin", type=float, default=1.04,
                    help="canvas radius as a multiple of the disc radius; "
                         "raise it if the black hole reads too large in game")
    args = ap.parse_args()

    if not os.path.exists(args.src):
        raise SystemExit(f"source not found: {args.src}")

    master, s = build_master(args.src, args.margin)
    print("stars removed:      {stars_removed}".format(**s))
    print("source centre:      {centre}".format(**s))
    print("horizon / outer r:  {horizon_r} / {outer_r}".format(**s))
    print("master:             {master_px} px square".format(**s))
    print("horizon offset:     ({:+.1f}, {:+.1f}) px from the rotation axis"
          .format(*s["horizon_offset"]))
    print("horizon / sprite:   {:.0%}".format(s["horizon_fraction"]))
    print("faint haze:         {:.0%} of visible area".format(s["haze_fraction"]))

    worst = max(abs(v) for v in s["horizon_offset"])
    if worst > MAX_AXIS_OFFSET:
        print(f"\nFAILED: horizon is {worst:.1f} px off axis. Rotating this "
              f"master makes the black hole orbit the centre instead of "
              f"turning. Nothing written.", file=sys.stderr)
        return 1

    master.save(args.out)
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
