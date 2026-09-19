"""DRAFT — the Fleets frame's opening, held to its own alpha.

Work order 136 C. **This is not in the suite and must not be added on
its own: it is RED against today's artwork.** It goes in with the
correction, in the optics round, and then `check()` moves into
`tools/smoke_test.py` and `fleets` joins `_FRAME_SCREENS` there.

Run it as it stands to see what it would say:

    python doc/briefs/136-draft-fleets-opening-check.py

WHAT IT HOLDS, AND WHY EACH HALF IS HERE
----------------------------------------
1. **The opening is the artwork's, not a typed number.**
   `layout.json` `frame.opening` must be `find_holes`' one hole grown
   by `frame_holes.BLEED` on each side. Today it is right — (74, 75,
   1771, 917) + 2 px each way is exactly [72, 73, 1775, 921] — and
   nothing checked it, which is decision 36's shape: a hand-copied
   number is legitimate only with a checker. Decision 3 does not apply
   to this screen (one hole, hand-placed regions inside it), and that
   is precisely why this half is needed: no `frame_holes` rule covers
   `fleets`, so nothing else ever reads that PNG.

2. **No metal reaches into the opening.** The same class-B question
   `tools/smoke_test.py` asks of `colony_summary` and `galaxy_map`,
   asked of the one hole: content clipped to it loses whatever the
   frame paints over, and at 4K every reference pixel is two.

WHY IT IS RED TODAY
-------------------
Four opaque islands sit inside the opening's bounding box, 1147 px in
all (0.071 % of it). None is ornament. Every one traces to the Planets
master this frame was cut from (work order 134 A: "the Planets artwork
with its inner struts removed"), whose five holes are

    (74, 1450, 75, 803)      (1480, 1844, 77, 802)
    (75,  592, 823, 991)     ( 617, 1450, 823, 991)     (1480, 1844, 823, 991)

as x0..x1 / y0..y1. Two causes, and they want different fixes:

  * **Two strut stubs.** x 1452..1478 at the bottom, 4 px deep, and
    x 594..615, 1 px deep — the Planets vertical strut stands at
    x 1451..1479 (between 1450 and 1480) and the lower divider at
    x 593..616 (between 592 and 617). The stubs are the struts where
    they met the ring, left behind when the middles were erased.
  * **The union's own step.** The Planets holes are not flush: the
    right pair starts at y 77 where the left starts at 75, and the
    lower-left one at x 75 where the upper starts at 74. One opening
    made out of all five takes the outermost edge, so the metal that
    used to sit between the two levels is now inside the bounding box —
    a 2 px band along the top from x 1452 to 1844, and a 1 px column at
    x 74 from y 805 down. Not a strut, and not a mistake in the cut:
    the shape is the master's.

AND THE SUITE'S OWN MEASUREMENT WOULD NOT HAVE SEEN IT
------------------------------------------------------
`tools/smoke_test.py`'s class-B pass samples about forty lines per edge
(`step = edge // 40`). On this opening that is a column every 44 px,
and the strut stubs are 27 and 22 wide — so the sampled method reports
**T2 B1** where reading every line says **T4 B4**. The check below
therefore reads every row and column; the images are 1920x1080 and it
costs milliseconds.

The same stride is what the suite uses on `colony_summary` and
`galaxy_map`. Measured both ways on 19 September 2026 they are
unaffected — worst 1 and 0 either way, against a budget of 2 — so
tightening the stride there is safe, and it is left for the commit that
adds this screen rather than done in passing. It is
"a check with a scope has a blind spot exactly the size of that scope"
with the scope being a sampling rate.

WHAT IT COSTS TODAY, MEASURED
-----------------------------
`icon_area` loses 170 x 2 reference px at its top right and
`ship_panel` 22 x 1 at its bottom edge, the same at all four shipped
resolutions (`boxes.json` carries two lists and both resolve to the
same reference rects). At 2160p that is 4 and 2 device px.

THE BUDGET
----------
`_CLASS_B_BUDGET` is 2 in the suite, and it is a MEASUREMENT of the
other two screens, not a tolerance — "the budget IS the measurement, so
any thickening fails". This draft keeps 2 rather than inventing a
looser one for this screen. Whether the strut stubs are cleaned out of
the artwork, or the opening is declared to be the shape it really is,
is Data's call in the optics round; either answer makes this green
without the number moving.
"""
import json
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import frame_holes as fh          # noqa: E402

SCREEN = "fleets"
#: Copied from tools/smoke_test.py, deliberately, not loosened. See the
#: docstring: it is the other two screens' measured worst case.
CLASS_B_BUDGET = 2
#: The suite excludes the corners of a hole before measuring an edge,
#: because a chamfer there is the shape and not an intrusion.
CORNER_TRIM = 0.18
#: Alpha at or above this is metal, the value `frame_holes` cuts on.
OPAQUE = 16


def _png(root):
    return os.path.join(root, "screens", SCREEN, "assets", "frame.png")


def _opening_from_layout(root):
    path = os.path.join(root, "screens", SCREEN, "layout.json")
    with open(path, encoding="utf-8") as fp:
        return list(json.load(fp)["frame"]["opening"])


def _intrusion(alpha, rect, stride=1):
    """Deepest run of metal in from each side of `rect`, corners
    trimmed. Returns [left, right, top, bottom] in image px.

    `stride` 1 reads EVERY row and column. The suite's own copy of this
    function steps `(edge // 40)` instead, and on this frame that is 44
    columns — wide enough to walk straight over a 27 px strut stub. It
    reports T2 B1 here where every line says T4 B4. See the module
    docstring: the stride is the finding, not a detail of this draft.
    """
    x, y, w, h = rect
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(alpha.shape[1], x + w), min(alpha.shape[0], y + h)
    iy = int((y1 - y0) * CORNER_TRIM)
    ix = int((x1 - x0) * CORNER_TRIM)
    out = []
    #: `stride=None` reproduces the suite's per-edge `edge // 40`.
    sy = stride or max(1, (y1 - y0) // 40)
    sx = stride or max(1, (x1 - x0) // 40)
    for cs, horiz in ((range(y0 + iy, y1 - iy, sy), True),
                      (range(x0 + ix, x1 - ix, sx), False)):
        lo = hi = 0
        for c in cs:
            line = alpha[c, x0:x1] if horiz else alpha[y0:y1, c]
            n = 0
            while n < len(line) and line[n] >= OPAQUE:
                n += 1
            lo = max(lo, n)
            n = 0
            while n < len(line) and line[len(line) - 1 - n] >= OPAQUE:
                n += 1
            hi = max(hi, n)
        out += [lo, hi]
    return out


def check(root=ROOT, report=print):
    """Raises AssertionError on the first thing that is wrong."""
    png = _png(root)
    iw, ih, holes = fh.find_holes(png)
    assert len(holes) == 1, (
        f"{SCREEN}/assets/frame.png cuts {len(holes)} holes; this screen "
        f"is built on having exactly one and seating its regions into it "
        f"(fltgeom.seat), so a second hole is a layout question, not a "
        f"tolerance")
    hx, hy, hw, hh = holes[0]

    # 1. The typed opening IS the artwork's hole plus the bleed.
    want = [hx - fh.BLEED, hy - fh.BLEED, hw + 2 * fh.BLEED, hh + 2 * fh.BLEED]
    have = _opening_from_layout(root)
    assert have == want, (
        f"screens/{SCREEN}/layout.json says the opening is {have}; the "
        f"artwork's own hole is {list(holes[0])} and BLEED is "
        f"{fh.BLEED}, which makes it {want}. The number is the frame's, "
        f"not a constant")
    # The image must cover the reference area 1:1, or "reference px" in
    # everything below is a different unit from the boxes'.
    assert (iw, ih) == (1920, 1080), (
        f"{SCREEN}'s frame is {iw}x{ih}; it is plain-scaled over the "
        f"1920x1080 reference area, so anything measured on it is only "
        f"in reference px while it is that size")

    # 2. Nothing paints into the opening.
    alpha = np.array(Image.open(png).convert("RGBA"))[:, :, 3]
    left, right, top, bottom = _intrusion(alpha, holes[0])
    sampled = _intrusion(alpha, holes[0], stride=None)
    report(f"{SCREEN}: metal reaches L{left} R{right} T{top} B{bottom} "
           f"into the opening (budget {CLASS_B_BUDGET}); the suite's own "
           f"40-sample stride would say {sampled}")
    assert max(left, right, top, bottom) <= CLASS_B_BUDGET, (
        f"{SCREEN}: the frame's opaque alpha reaches "
        f"{max(left, right, top, bottom)} px into the one opening "
        f"(L{left} R{right} T{top} B{bottom}), over the budget of "
        f"{CLASS_B_BUDGET}. Content seated into this hole — the big-icon "
        f"grid and the ship panel — loses that much of itself at every "
        f"resolution, and twice that in device px at 2160p")


def islands(root=ROOT):
    """Every opaque island inside the opening, for a report. Returns
    (pixels, x0, y0, x1, y1) in image px, largest first."""
    from collections import deque
    png = _png(root)
    alpha = np.array(Image.open(png).convert("RGBA"))[:, :, 3]
    _, _, holes = fh.find_holes(png)
    x, y, w, h = holes[0]
    sub = alpha[y:y + h, x:x + w] >= OPAQUE
    seen = np.zeros_like(sub, bool)
    out = []
    for r in range(h):
        for c in range(w):
            if not sub[r, c] or seen[r, c]:
                continue
            q, pts = deque([(r, c)]), []
            seen[r, c] = True
            while q:
                rr, cc = q.popleft()
                pts.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and sub[nr, nc] \
                            and not seen[nr, nc]:
                        seen[nr, nc] = True
                        q.append((nr, nc))
            ys = [p[0] for p in pts]
            xs = [p[1] for p in pts]
            out.append((len(pts), min(xs) + x, min(ys) + y,
                        max(xs) + x, max(ys) + y))
    out.sort(reverse=True)
    return out


if __name__ == "__main__":
    for n, x0, y0, x1, y1 in islands():
        print(f"  {n:5d} px   x {x0}..{x1} ({x1 - x0 + 1} wide)   "
              f"y {y0}..{y1} ({y1 - y0 + 1} deep)")
    try:
        check()
    except AssertionError as exc:
        print("\nRED, as this draft says it is:\n")
        print(exc)
        sys.exit(1)
    print("\nGREEN — the artwork has been corrected; move check() into "
          "tools/smoke_test.py and add fleets to _FRAME_SCREENS.")
