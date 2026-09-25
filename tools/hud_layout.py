"""The HUD's LAYOUT, measured: where Data's galaxy HUD puts things.

Split out of `tools/hud_measure.py` (work order 169) — it is the half
of the measurement that says WHERE rather than HOW IT LOOKS, and
`tools/hud_boxes.py` writes the galaxy map's boxes from it. Its output
is `measured.galaxy` in `assets/shared/hud/style.json`, held to it by
the smoke test with the rest of the measured block. The helpers are
imported where they are used: `hud_measure` imports this module.
"""
import numpy as np


def _peaks(prof, floor, rise, gap=12):
    return [x for x in range(gap, len(prof) - 1)
            if prof[x] > floor and prof[x] >= prof[x - 1]
            and prof[x] > prof[x + 1] and prof[x] > prof[x - gap] + rise]


def galaxy_layout(a):
    """Where the HUD puts things, in REFERENCE px — the galaxy map's
    boxes are written from this (`tools/hud_boxes.py`), as they were
    once cut from `frame.png`'s holes (decision 3, superseded by 71).

    y is converted by the same factor as x, from the TOP: the title
    plate hangs from the top edge, and the HUD's 0.4 % of extra height
    falls below the nav row, where nothing is."""
    from hud_measure import ref, underlines, _luma
    lum = _luma(a)
    opaque = a[..., 3] >= 250
    # The info panel: the opaque column right of x 5500, rows 250-3290.
    sub = opaque[250:3290, 5500:]
    ys = np.where(sub.any(axis=1))[0]
    xs = np.where(sub.any(axis=0))[0]
    panel = [5500 + int(xs.min()), 250 + int(ys.min()),
             5500 + int(xs.max()) + 1, 250 + int(ys.max()) + 1]
    # Its separators: the peaks of a profile down its middle.
    col = lum[:, 5850:6000].mean(axis=1)
    seps = [y for y in _peaks(col[400:panel[3] - 30], 60, 40, 15)]
    seps = [y + 400 for y in seps]
    # The nav row's two edge lines: peaks of a profile down button 2.
    nav = lum[3300:3620, 1300:1800].mean(axis=1)
    lines = sorted(_peaks(nav, 40, 20, 6), key=lambda y: -nav[y])[:2]
    top, bottom = sorted(y + 3300 for y in lines)
    n, uw, _uh, _c = underlines(a)
    centres = _underline_centres(a)
    pitch = float(np.mean(np.diff(centres)))
    # The gap between two buttons: the two parallel lines of one divider.
    row = lum[3378:3383, 60:5560].mean(axis=0)
    pk = _peaks(row, 30, 15, 8)
    pairs = [q - p for p, q in zip(pk, pk[1:]) if q - p < 80]
    gap = float(np.median(pairs))
    # TURN: its four edge lines.
    mid = lum[3440:3480, 5500:6680].mean(axis=0)
    tl = [x + 5500 for x in _peaks(mid, 80, 40, 6)]
    turn_x = (min(tl), max(tl))
    vert = lum[3280:3640, 5900:6300].mean(axis=1)
    tv = [y + 3280 for y in _peaks(vert, 80, 40, 6)]
    turn_y = (min(tv), max(tv))
    out = {
        "panel": [ref(v, 0) for v in panel],
        "separators": [ref(y, 0) for y in seps],
        "nav_top": ref(top, 0), "nav_bottom": ref(bottom, 0),
        "nav_centres": [ref(c, 0) for c in centres],
        "nav_width": ref(pitch - gap, 0),
        "turn": [ref(turn_x[0], 0), ref(turn_y[0], 0),
                 ref(turn_x[1], 0), ref(turn_y[1], 0)],
        # THE HUD'S OWN SCREEN-EDGE MARGIN, work order 170: the gap
        # between the info panel's opaque right edge and the image's
        # right edge. The one place the artwork says how far a block
        # sits from the screen's edge — the bottom edge of the image
        # is NOT such a place: 137 transparent rows under the bar,
        # which 169 took for layout and which is the band Data saw.
        "edge_margin": ref(a.shape[1] - panel[2], 0),
    }
    return out


def _underline_centres(a):
    from hud_measure import NAV_UNDERLINE, _crop
    c = _crop(a, NAV_UNDERLINE)
    bright = c[..., :3].sum(axis=2) > 600
    xs = np.sort(np.where(bright)[1])
    groups, s = [], 0
    for i in range(1, len(xs) + 1):
        if i == len(xs) or xs[i] - xs[i - 1] > 40:
            groups.append((xs[s] + xs[i - 1]) / 2 + NAV_UNDERLINE[0])
            s = i
    return groups
