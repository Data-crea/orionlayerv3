"""Generate the galaxy map star icons — six size steps per class.

    python tools/make_star_icons.py [--out DIR] [--size PX] [--sheet]

orion2re draws stars from SIX pre-rendered sprites per spectral
class, not from one artwork scaled down. MAINSCR::Get_Star_Picture_Seg_
indexes BUFFER0.LBX with (spectral_class * 6 + zoom_level + star.size):
zoom and size are ADDED into one 0..5 axis, and the matching pixel
sizes in MOX::_star_fields_dim are 33, 29, 25, 23, 21, 17. A large
star at zoom 1 is literally the same sprite as a medium one at
zoom 0.

That is why a single downscaled artwork never looks right: the
original does not scale, it swaps to a drawing made for that size.
This script reproduces the idea — step 0 carries full detail, step 5
is a bold core with four short spikes and nothing that could turn to
mush below 50 px.

Two rules make the small steps readable, and both go against what
looks best in isolation:

1. The core keeps the CLASS colour as the steps shrink. A white-hot
   centre is what sells a big star, but at 47 px it swallows the hue
   and every class ends up looking white — and colour is the only
   thing left that identifies a class at that size.
2. Nothing thin survives. Ray count drops 16 -> 4 while each ray
   grows thicker, so the silhouette stays a star instead of decaying
   into a fuzzy dot.

Output: <out>/<class>/0.png .. 5.png, RGBA, transparent background,
all rendered at the same canvas size (the renderer scales them to
the exact zoom width). Step 0 is drawn for ~180 px on screen, step 5
for ~50 px, so each is used near its native detail level.
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import zoomtables as zt  # noqa: E402

#: Folder names must match renderer.CLASS_DIRS.
#: (base, hot) — base carries the class identity, hot is the centre
#: at the large steps. Loosely after the original's palette ramps.
CLASSES = {
    "blue":   ((70, 140, 255), (205, 232, 255)),
    "white":  ((200, 214, 240), (255, 255, 255)),
    "yellow": ((255, 200, 60), (255, 248, 200)),
    "orange": ((255, 142, 38), (255, 224, 158)),
    "red":    ((238, 70, 52), (255, 196, 152)),
    "brown":  ((186, 116, 66), (245, 206, 156)),
}

#: Per size step (0 = biggest). See the module docstring for why the
#: values move the way they do.
#:   rays        fine rays around the disc
#:   ray_pow     higher = thinner rays
#:   spike       length of the four main spikes, in canvas radii
#:   spike_pow   higher = thinner spikes
#:   core        disc radius, in canvas radii — grows as steps shrink
#:   glow        halo radius, in canvas radii
#:   hot         0..1 how far the centre goes towards the hot colour
STEPS = [
    dict(rays=16, ray_pow=20, spike=0.97, spike_pow=34, core=0.240,
         glow=0.42, hot=1.00),
    dict(rays=12, ray_pow=16, spike=0.92, spike_pow=30, core=0.265,
         glow=0.44, hot=0.90),
    dict(rays=10, ray_pow=13, spike=0.86, spike_pow=26, core=0.295,
         glow=0.46, hot=0.78),
    dict(rays=8,  ray_pow=10, spike=0.79, spike_pow=22, core=0.330,
         glow=0.49, hot=0.62),
    dict(rays=6,  ray_pow=8,  spike=0.71, spike_pow=18, core=0.375,
         glow=0.53, hot=0.42),
    dict(rays=4,  ray_pow=6,  spike=0.62, spike_pow=14, core=0.430,
         glow=0.58, hot=0.22),
]

CANVAS = 256
SUPERSAMPLE = 2


def _fields(n):
    """Radius (0..1 at the edge) and angle grids for an n x n canvas."""
    a = (np.arange(n) + 0.5) / n * 2.0 - 1.0
    x, y = np.meshgrid(a, a)
    return np.hypot(x, y), np.arctan2(y, x)


def _lobes(theta, count, power):
    """`count` angular lobes, peaking at 1. cos(count*theta/2) hits
    +-1 exactly at 2*pi*k/count, so squaring gives evenly spaced
    petals and the exponent controls how thin they are."""
    return np.power(np.cos(count * theta / 2.0) ** 2, power / 2.0)


def _falloff(r, reach, softness=2.0):
    """1 at the centre, 0 beyond `reach`, with a soft shoulder."""
    t = np.clip(1.0 - r / max(reach, 1e-6), 0.0, 1.0)
    return t ** softness


def _disc(r, radius, edge=0.35):
    """Solid disc with a soft rim. `edge` is the rim width relative
    to the radius — a hard edge aliases, a soft one turns to fog."""
    inner = radius * (1.0 - edge)
    t = np.clip((radius - r) / max(radius - inner, 1e-6), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)          # smoothstep


def intensity(step, n):
    """Scalar brightness field for one size step.

    Built around a SOLID DISC, not a flare. The disc carries the
    class colour and most of the icon's area; spikes and rays sit on
    top. Reversing that (long spikes, small core) is what makes an
    icon look like a lens flare and lose its hue when it shrinks.
    """
    r, theta = _fields(n)
    core = step["core"]

    disc = _disc(r, core)
    # Centre a touch brighter, so the disc is not a flat blob.
    disc = np.clip(disc + _falloff(r, core * 0.55, 1.4) * 0.30, 0.0, 1.0)

    # Halo hugging the disc, giving it presence without fog.
    glow = _falloff(r, step["glow"], 2.4) * 0.42

    # Four main spikes: the silhouette that still says "star" at the
    # smallest step. They start inside the disc so they grow out of
    # it rather than crossing it.
    spike_shape = np.power(np.cos(2.0 * theta) ** 2, step["spike_pow"])
    spikes = spike_shape * _falloff(r, step["spike"], 1.1) * 0.92

    # Fine rays, fading out well before the spike tips.
    rays = _lobes(theta, step["rays"], step["ray_pow"])
    rays = rays * _falloff(r, core + (step["spike"] - core) * 0.45, 1.2) * 0.78

    field = np.maximum(np.maximum(glow, spikes), rays)
    return np.clip(np.maximum(field, disc), 0.0, 1.0)


def colourise(field, base, hot, hotness):
    """Map brightness to RGBA. The centre mixes towards `hot` only as
    far as `hotness` allows — the small steps stay in class colour so
    the hue survives at 50 px."""
    base = np.array(base, dtype=np.float64)
    hot = np.array(hot, dtype=np.float64)
    centre = base + (hot - base) * hotness

    # Brightness drives BOTH the hue mix (rim -> centre) and alpha.
    mix = np.clip((field - 0.45) / 0.55, 0.0, 1.0)[..., None]
    rgb = base[None, None, :] * (1.0 - mix) + centre[None, None, :] * mix

    # Lift the very brightest pixels a little further, so a big star
    # still has a highlight without washing out the class colour.
    peak = np.clip((field - 0.88) / 0.12, 0.0, 1.0)[..., None]
    rgb = rgb + (hot[None, None, :] - rgb) * peak * hotness * 0.75

    alpha = np.clip(field * 1.12, 0.0, 1.0) ** 0.85
    out = np.concatenate([np.clip(rgb, 0, 255), alpha[..., None] * 255.0],
                         axis=2)
    return out.astype(np.uint8)


def render(step, base, hot, size=CANVAS, ss=SUPERSAMPLE):
    big = size * ss
    field = intensity(step, big)
    img = Image.fromarray(colourise(field, base, hot, step["hot"]), "RGBA")
    return img.resize((size, size), Image.LANCZOS) if ss > 1 else img


def contact_sheet(out_dir, size=CANVAS):
    """Preview every class at the TRUE on-screen size of its step.

    Judging these at canvas resolution is misleading — step 5 looks
    crude until you see it at the 47 px it will actually occupy.
    """
    factor = 1402 / zt.MAP_WIDTH          # map_area width / native
    widths = [max(8, round(d * factor)) for d in zt.STAR_FIELDS_DIM]
    pad, label = 14, 26
    cell = max(widths) + pad
    sheet = Image.new("RGBA",
                      (cell * len(widths) + pad,
                       (cell + label) * len(CLASSES) + pad),
                      (8, 10, 18, 255))
    for row, name in enumerate(CLASSES):
        for col, w in enumerate(widths):
            src = Image.open(os.path.join(out_dir, name, f"{col}.png"))
            icon = src.resize((w, w), Image.LANCZOS)
            x = pad + col * cell + (cell - w) // 2
            y = pad + row * (cell + label) + (cell - w) // 2
            sheet.alpha_composite(icon, (x, y))
    return sheet


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(
        here, "screens", "galaxy_map", "assets", "stars"))
    ap.add_argument("--size", type=int, default=CANVAS)
    ap.add_argument("--sheet", action="store_true",
                    help="also write _contact_sheet.png next to --out")
    args = ap.parse_args()

    for name, (base, hot) in CLASSES.items():
        folder = os.path.join(args.out, name)
        os.makedirs(folder, exist_ok=True)
        for idx, step in enumerate(STEPS):
            img = render(step, base, hot, args.size)
            img.save(os.path.join(folder, f"{idx}.png"))
        print(f"  {name}: 6 steps -> {folder}")

    if args.sheet:
        path = os.path.join(os.path.dirname(args.out), "_contact_sheet.png")
        contact_sheet(args.out, args.size).save(path)
        print("  sheet ->", path)


if __name__ == "__main__":
    main()
