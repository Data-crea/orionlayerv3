#!/usr/bin/env python3
"""Measure the HUD style values off Data's artwork (work order 169).

    python tools/hud_measure.py            # print the measured values
    python tools/hud_measure.py --check    # compare with style.json, exit 1

`assets/shared/hud/style.json` carries every colour, width, softness and
proportion the HUD blocks draw with (decision 71). Its `measured` block is
a COPY of what this tool prints, and a copy is legitimate only with a
checker: the smoke test runs `measure()` and holds the file to it, so a
value edited by hand is a value that fails.

**Two sources, both committed.** `assets/shared/hud/galaxy_hud.png`, the
HUD itself (6704x3756, AI-generated, text removed), and
`doc/briefs/169-mockup-galaxy.png`, Data's mockup of the finished galaxy
screen — the only place the HUD's TEXT can be measured, because the HUD
has none. Data's colony mockup is NOT in the tree (21 MB); what it
contributed is in style.json's `mockup_colony` block with the file's
sha256, and this tool re-measures it only when given its path.

**Where a number comes from is part of the number.** Every region below
is in the source image's own pixels and named for what it is. A width is
converted to REFERENCE px (1920x1080) by the image's width alone,
`1920 / 6704` — the HUD is 0.4 % taller than 16:9, and a width must not
depend on which axis that slack went to. *An asset is not a measurement*
of world geometry; what is read here is the ARTWORK's own proportions,
which is what a style is.

**Method, in short.** A line's colour is its peak along a profile taken
across it and averaged along it; its width is the full width at half
maximum of luma. A fill is the median of a patch that holds nothing
else. A glow's width is the run of partial alpha (16..249) outside the
opaque edge. A text colour is the median of the brightest 15 % of a
word's box, and a text size is the ink height over the box it sits in.
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import hud_colony  # noqa: E402  (the two halves split out of this tool)
import hud_layout  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HUD = os.path.join(ROOT, "assets", "shared", "hud", "galaxy_hud.png")
MOCKUP = os.path.join(ROOT, "doc", "briefs", "169-mockup-galaxy.png")
STYLE = os.path.join(ROOT, "assets", "shared", "hud", "style.json")

#: HUD px -> reference px, by width (see the docstring).
HUD_W = 6704
TO_REF = 1920 / HUD_W
#: Mockup px -> reference px. The galaxy mockup is 1676x939.
MOCK_W = 1676
MOCK_TO_REF = 1920 / MOCK_W

# ── Regions, in HUD px, (x0, y0, x1, y1), each found by looking and then
# measured; the comment says what the region holds and nothing else ──

#: The right info panel's four sides, a strip across each edge line.
PANEL_LEFT = (5640, 1500, 5720, 1800)
PANEL_RIGHT = (6560, 1500, 6640, 1800)
PANEL_TOP = (5900, 290, 6300, 340)
PANEL_BOTTOM = (5900, 3200, 6300, 3260)
#: Deep inside the panel, between two separators, left of the icons.
PANEL_DEEP = (5800, 1450, 6200, 1550)
#: The panel's top-left corner, where the chamfer is.
PANEL_CORNER = (5600, 280, 5800, 400)
#: One separator line and the stretch of it to profile.
SEPARATOR = (5800, 687, 6300, 717)
#: The same line across the whole panel, for its two insets.
SEPARATOR_ROW = (5600, 700, 6680, 705)
#: The nav row: first button, inside, between icon and slant.
NAV_DEEP = (1300, 3380, 1800, 3500)
NAV_TOP = (1300, 3336, 1800, 3366)
#: Two rows through the nav row's slanted dividers, for the slant.
NAV_SLANT_ROWS = (3380, 3540)
NAV_SLANT_SPAN = (60, 5560)
#: The band the six underlines sit in.
NAV_UNDERLINE = (60, 3530, 5600, 3600)
#: The TURN button: its left edge, its top edge, its inside.
TURN_LEFT = (5555, 3440, 5645, 3480)
TURN_TOP = (5900, 3285, 6300, 3380)
TURN_DEEP = (6000, 3420, 6400, 3500)

#: Words in the galaxy mockup, in MOCKUP px, (x0, y0, x1, y1), and the
#: box each sits in for its size: the title plate, a sidebar row, a nav
#: button. Boxes are read off the mockup the same way, by their lines.
WORDS = {
    "title": (780, 10, 900, 45),
    "label": (1440, 203, 1545, 222),      # TREASURY
    "value": (1440, 227, 1535, 253),      # 304 BC
    "sub": (1440, 256, 1520, 275),        # +24 BC
    "button": (120, 862, 210, 884),       # COLONIES
    "action": (1495, 855, 1575, 885),     # TURN
    "negative": (1440, 482, 1490, 512),   # FOOD -11
}
#: Heights of the boxes those words are sized against, in mockup px:
#: the title plate (0..52), one sidebar row (separator to separator,
#: 176..305), a nav button (848..898), the TURN button (840..898).
BOX_H = {"title": 52, "label": 129, "value": 129, "sub": 129,
         "button": 50, "action": 58, "negative": 129}


def load(path):
    return np.asarray(Image.open(path).convert("RGBA")).astype(float)


def _crop(a, r):
    x0, y0, x1, y1 = r
    return a[y0:y1, x0:x1]


def _luma(c):
    return 0.299 * c[..., 0] + 0.587 * c[..., 1] + 0.114 * c[..., 2]


def line(a, region, axis):
    """(peak RGB, FWHM in source px) of the one line across `region`.

    `axis` is the direction the profile runs: 0 down the rows (a
    horizontal line), 1 along the columns (a vertical line)."""
    c = _crop(a, region)
    prof = c.mean(axis=1 if axis == 0 else 0)
    lum = _luma(prof)
    i = int(np.argmax(lum))
    half = (lum[i] + lum.min()) / 2
    lo = i
    while lo > 0 and lum[lo] > half:
        lo -= 1
    hi = i
    while hi < len(lum) - 1 and lum[hi] > half:
        hi += 1
    return [int(round(v)) for v in prof[i, :3]], hi - lo - 1


def fill(a, region):
    c = _crop(a, region)[..., :3].reshape(-1, 3)
    return [int(round(v)) for v in np.median(c, axis=0)]


def glow(a, region):
    """(colour, width) of the partial-alpha run outside a vertical edge."""
    c = _crop(a, region)
    alpha = c[..., 3].mean(axis=0)
    soft = np.where((alpha >= 16) & (alpha < 250))[0]
    first_opaque = int(np.argmax(alpha >= 250))
    soft = soft[soft < first_opaque]
    rgb = c[:, soft, :3].reshape(-1, 3)
    return [int(round(v)) for v in np.median(rgb, axis=0)], len(soft)


def inner_glow(a, region, start):
    """Depth, in source px, from `start` (just inside the edge line) to
    where the fill has fallen nine tenths of the way to the deep — the
    soft band a reader sees along the inside of every edge."""
    c = _crop(a, region)
    lum = _luma(c.mean(axis=0))
    deep = lum[-20:].mean()
    top = lum[start]
    target = deep + 0.1 * (top - deep)
    j = start
    while j < len(lum) - 1 and lum[j] > target:
        j += 1
    return j - start


def chamfer(a, region):
    """The corner cut, in source px, followed along the EDGE LINE: rows
    from the first row the line is lit to the row where it reaches the
    panel's side. Not by alpha — the glow outside the line is partial
    alpha and runs on down the side, which put the cut twice as long."""
    c = _crop(a, region)
    lum = _luma(c) * (c[..., 3] >= 128)
    lit = [y for y in range(len(lum)) if lum[y].max() > 100]
    xs = {y: int(np.argmax(lum[y])) for y in lit}
    side = int(np.median([xs[y] for y in lit[-20:]]))
    return next(y for y in lit if xs[y] <= side + 2) - lit[0]


def inset(a, region, left_edge, right_edge):
    """A separator's distance from the panel's two edge lines."""
    c = _crop(a, region)
    lum = _luma(c.mean(axis=0))
    x0 = region[0]
    inner = np.arange(len(lum)) + x0
    keep = (inner > left_edge + 12) & (inner < right_edge - 12)
    peak = lum[keep].max()
    on = inner[keep][lum[keep] > peak / 2]
    return int(on.min() - left_edge), int(right_edge - on.max())


def slant(a):
    """dx/dy of the nav row's dividers, from the matching divider peaks
    on two rows: the median shift of each upper peak to its nearest
    lower one."""
    lum = _luma(a)
    ya, yb = NAV_SLANT_ROWS
    x0, x1 = NAV_SLANT_SPAN

    def peaks(y):
        r = lum[y - 2:y + 3, x0:x1].mean(axis=0)
        return [x + x0 for x in range(12, len(r) - 1)
                if r[x] > 50 and r[x] >= r[x - 1] and r[x] > r[x + 1]
                and r[x] > r[x - 12] + 25]
    top, bot = peaks(ya), peaks(yb)
    shifts = []
    for x in top:
        near = min(bot, key=lambda b: abs((x - 115) - b))
        if abs((x - 115) - near) < 40:
            shifts.append(x - near)
    return round(float(np.median(shifts)) / (yb - ya), 3)


def underlines(a):
    """Width, core height and colour of the nav row's bright underlines."""
    c = _crop(a, NAV_UNDERLINE)
    bright = c[..., :3].sum(axis=2) > 600
    ys, xs = np.where(bright)
    order = np.argsort(xs)
    xs, ys = xs[order], ys[order]
    groups, s = [], 0
    for i in range(1, len(xs) + 1):
        if i == len(xs) or xs[i] - xs[i - 1] > 40:
            groups.append((xs[s:i], ys[s:i]))
            s = i
    widths = [int(g[0].max() - g[0].min() + 1) for g in groups]
    heights = [int(g[1].max() - g[1].min() + 1) for g in groups]
    core = c[bright][:, :3]
    return (len(groups), int(np.median(widths)), int(np.median(heights)),
            [int(round(v)) for v in np.median(core, axis=0)])


def word(m, box):
    c = _crop(m, box)[..., :3]
    lum = c.sum(axis=2)
    on = lum > max(np.percentile(lum, 85), 250)
    ys, _ = np.where(on)
    return ([int(round(v)) for v in np.median(c[on], axis=0)],
            int(ys.max() - ys.min() + 1))


def ref(px, digits=1):
    """Source px -> reference px; `digits=0` gives an int (a position)."""
    if digits == 0:
        return int(round(px * TO_REF))
    return round(px * TO_REF, digits)


def measure(hud_path=HUD, mockup_path=MOCKUP):
    a = load(hud_path)
    assert a.shape[1] == HUD_W, f"the HUD is {a.shape[1]} px wide, not {HUD_W}"
    out = {"source": {"width": HUD_W, "to_ref": round(TO_REF, 6)}}
    left, lw = line(a, PANEL_LEFT, 1)
    right, rw = line(a, PANEL_RIGHT, 1)
    top, tw = line(a, PANEL_TOP, 0)
    bottom, bw = line(a, PANEL_BOTTOM, 0)
    # The side edges are the bright ones; top and bottom carry less
    # light in the artwork. The block draws one edge, so it takes the
    # sides' colour and records the top's as the dim variant.
    sides = [int(round((x + y) / 2)) for x, y in zip(left, right)]
    lc = _crop(a, PANEL_LEFT)
    lpeak = int(np.argmax(_luma(lc.mean(axis=0))))
    gcol, gw = glow(a, PANEL_LEFT)
    out["panel"] = {
        "fill": fill(a, PANEL_DEEP),
        "fill_edge": fill(a, (PANEL_LEFT[0] + lpeak + 6, PANEL_LEFT[1],
                              PANEL_LEFT[0] + lpeak + 14, PANEL_LEFT[3])),
        "inner_glow": ref(inner_glow(
            a, (PANEL_LEFT[0], PANEL_LEFT[1], PANEL_LEFT[0] + 260,
                PANEL_LEFT[3]), lpeak + 10)),
        "edge": sides,
        "edge_dim": [int(round((x + y) / 2)) for x, y in zip(top, bottom)],
        "edge_width": ref((lw + rw) / 2),
        "glow": gcol,
        "glow_width": ref(gw),
        "chamfer": ref(chamfer(a, PANEL_CORNER)),
    }
    scol, sw = line(a, SEPARATOR, 0)
    lx = PANEL_LEFT[0] + lpeak
    rx = PANEL_RIGHT[0] + int(np.argmax(_luma(
        _crop(a, PANEL_RIGHT).mean(axis=0))))
    il, ir = inset(a, SEPARATOR_ROW, lx, rx)
    out["separator"] = {"color": scol, "width": ref(sw),
                        "inset_left": ref(il), "inset_right": ref(ir)}
    ncol, nw = line(a, NAV_TOP, 0)
    n, uw, uh, ucol = underlines(a)
    out["button"] = {
        "fill": fill(a, NAV_DEEP), "edge": ncol, "edge_width": ref(nw),
        "slant": slant(a),
        "underline": ucol, "underline_width": ref(uw),
        "underline_height": ref(uh), "underlines_found": n,
    }
    tl, tlw = line(a, TURN_LEFT, 1)
    tt, ttw = line(a, TURN_TOP, 0)
    out["action"] = {"fill": fill(a, TURN_DEEP),
                     "edge": [int(round((x + y) / 2)) for x, y in zip(tl, tt)],
                     "edge_width": ref((tlw + ttw) / 2),
                     "inner": fill(a, (TURN_LEFT[0] + 58, TURN_LEFT[1],
                                       TURN_LEFT[0] + 70, TURN_LEFT[3]))}
    out["galaxy"] = hud_layout.galaxy_layout(a)
    m = load(mockup_path)
    assert m.shape[1] == MOCK_W, f"the mockup is {m.shape[1]} px wide"
    text = {}
    for key, box in WORDS.items():
        col, h = word(m, box)
        text[key] = {"color": col, "cap": round(h / BOX_H[key], 3)}
    out["text"] = text
    return out


def compare(measured, stored):
    """Paths where style.json's `measured` block differs from the tool."""
    bad = []

    def walk(p, x, y):
        if isinstance(x, dict):
            for k in set(x) | set(y if isinstance(y, dict) else {}):
                walk(f"{p}.{k}", x.get(k),
                     y.get(k) if isinstance(y, dict) else None)
        elif x != y:
            bad.append((p, x, y))
    walk("measured", measured, stored)
    return bad


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true",
                    help="compare with assets/shared/hud/style.json")
    ap.add_argument("--colony", metavar="PNG",
                    help="Data's colony mockup, to re-measure the table "
                         "values (it is not in the tree)")
    args = ap.parse_args()
    got = measure()
    if args.colony:
        got["mockup_colony"] = hud_colony.measure_colony(args.colony)
    if not args.check:
        print(json.dumps(got, indent=2))
        return 0
    with open(STYLE, encoding="utf-8") as f:
        stored = json.load(f)["measured"]
    if not args.colony:
        stored = {k: v for k, v in stored.items() if k != "mockup_colony"}
    bad = compare(got, stored)
    for p, x, y in bad:
        print(f"{p}: measured {x}, style.json {y}")
    print("style.json matches the measurement" if not bad
          else f"{len(bad)} value(s) differ")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
