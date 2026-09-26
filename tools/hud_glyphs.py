#!/usr/bin/env python3
"""Draw the HUD's button glyphs (work order 179, part 6).

    python tools/hud_glyphs.py --out DIR     # write icon_<glyph>.png

Called by `tools/hud_cut.py`, which writes them beside the pieces it cuts
out of Data's HUD, into `assets/shared/hud/cut/` — DERIVED, never
committed (decision 40), rebuilt by `tools/setup.py`, and compared byte
for byte against a scratch rebuild by the smoke test. The shapes are
`assets/shared/hud/glyphs.json`; the colour, line and glow are
`chosen.glyph` in `style.json`.

**INVENTION** (decision 71's HUD style): MOO2 has no icons on these
buttons. Every glyph is our own line art, drawn here from coordinates —
no pixel of it comes from a MOO2 file.

**How a glyph is drawn.** At four times the master height, as lines and
filled shapes in white on transparent, then reduced (LANCZOS) — the
edges come out anti-aliased the way the cut icons' do. A soft glow (a
Gaussian blur of the same shape, at half strength) sits under it, as the
HUD's lit lines have. The RGB is the one colour, the shape is the alpha:
the frame colour then turns the whole glyph like a nav glyph
(`core.hud.tint.FOLLOWS`).
"""
import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GLYPHS = os.path.join(ROOT, "assets", "shared", "hud", "glyphs.json")
STYLE = os.path.join(ROOT, "assets", "shared", "hud", "style.json")
SS = 4


def load():
    with open(GLYPHS, encoding="utf-8") as fh:
        glyphs = json.load(fh)
    with open(STYLE, encoding="utf-8") as fh:
        style = json.load(fh)["chosen"]["glyph"]
    return glyphs, style


def _pts(points, n):
    return [(x * n, y * n) for x, y in points]


def _stroke(draw, pts, w):
    draw.line(pts, fill=255, width=w, joint="curve")
    r = w / 2
    for x, y in (pts[0], pts[-1]):
        draw.ellipse((x - r, y - r, x + r, y + r), fill=255)


def shape(prims, n, stroke):
    """The glyph's alpha mask, `n` px square."""
    im = Image.new("L", (n, n), 0)
    d = ImageDraw.Draw(im)
    w = max(1, round(stroke * n))
    for p in prims:
        kind = p[0]
        if kind == "line":
            pts = _pts(p[1], n)
            if p[2]:
                pts = pts + pts[:1]
            _stroke(d, pts, w)
        elif kind == "poly":
            d.polygon(_pts(p[1], n), fill=255)
        elif kind in ("circle", "disc"):
            cx, cy, r = (v * n for v in p[1:4])
            box = (cx - r, cy - r, cx + r, cy + r)
            if kind == "disc":
                d.ellipse(box, fill=255)
            else:
                d.ellipse(box, outline=255, width=w)
        elif kind == "arc":
            cx, cy, r = (v * n for v in p[1:4])
            a0, a1 = p[4], p[5]
            # PIL's own arc (a polyline of many short segments shows its
            # joints at this width), with the line's round caps at both
            # ends; PIL measures the width inward from the box, so the box
            # grows by half of it to keep the radius the centre line's.
            h = w / 2
            d.arc((cx - r - h, cy - r - h, cx + r + h, cy + r + h), a0, a1,
                  fill=255, width=w)
            for a in (a0, a1):
                x = cx + r * math.cos(math.radians(a))
                y = cy + r * math.sin(math.radians(a))
                d.ellipse((x - h, y - h, x + h, y + h), fill=255)
        else:
            raise ValueError(f"unknown glyph primitive {kind!r}")
    return im


def render(prims, style):
    """RGBA uint8 array, `style['height']` px square."""
    h = int(style["height"])
    big = shape(prims, h * SS, float(style["stroke"]))
    core = np.asarray(big.resize((h, h), Image.LANCZOS), dtype=np.float64)
    glow = np.asarray(big.filter(ImageFilter.GaussianBlur(
        float(style["glow"]) * h * SS)).resize((h, h), Image.LANCZOS),
        dtype=np.float64)
    alpha = np.clip(np.maximum(core, glow * 0.5), 0, 255)
    rgb = np.broadcast_to(np.array(style["colour"], dtype=np.float64),
                          (h, h, 3))
    return np.round(np.dstack([rgb, alpha])).astype(np.uint8)


def write(out):
    glyphs, style = load()
    os.makedirs(out, exist_ok=True)
    names = []
    for name, prims in sorted(glyphs["glyphs"].items()):
        piece = f"icon_{name}"
        Image.fromarray(render(prims, style), "RGBA").save(
            os.path.join(out, piece + ".png"), optimize=False)
        names.append(piece)
    return names


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=os.path.join(
        ROOT, "assets", "shared", "hud", "cut"))
    args = ap.parse_args()
    names = write(args.out)
    print(f"{len(names)} glyphs written to {os.path.abspath(args.out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
