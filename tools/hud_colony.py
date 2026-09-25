"""The table values, measured off Data's colony mockup (work order 169).

Split out of `tools/hud_measure.py`. The mockup is NOT in the tree
(6700x3756, 21 MB), so this runs only when it is given
(`hud_measure.py --colony <png>`), refuses any other file by sha256, and
the smoke test REPORTS its block in style.json instead of checking it —
a check that read ~/Downloads would pass on one machine only.
"""
import hashlib

import numpy as np
from PIL import Image


#: Data's colony mockup, NOT in the tree (6700x3756, 21 MB): regions in
#: the coordinates of its 1800 px wide thumbnail, (x0, y0, x1, y1). It is
#: the only source for the table blocks, because the HUD has no table.
COLONY_SHA256 = ("9c9b90497e6274b312f5091d067da094969537a5848b239a"
                 "fa3c21c634d09900")
COLONY = {
    "row_a": (1280, 245, 1360, 280),       # Draconis I's row, WORKERS empty
    "row_b": (1280, 190, 1360, 228),       # Dante I's
    "selected": (1280, 462, 1360, 502),    # Hase I, the scanned row
    "header": (1280, 90, 1360, 118),       # the header band, no word
}
#: A thin line: (x0, y0, x1, y1) across it, profiled down the rows.
COLONY_LINES = {
    "row_line": (1280, 560, 1360, 572),        # between two rows
    "selected_edge": (1280, 502, 1360, 516),   # the scanned row's rim
}
COLONY_WORDS = {"header": (245, 97, 305, 113),      # NAME
                "row": (188, 135, 262, 155)}        # Dante I
#: The scroll bar: its thumb and its empty track.
COLONY_SCROLL = {"thumb": (1690, 200, 1700, 480),
                 "track": (1690, 530, 1700, 640)}


def measure_colony(path):
    """The table values off Data's colony mockup, when it is at hand."""
    from hud_measure import fill, line, word
    with open(path, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    assert digest == COLONY_SHA256, f"not Data's colony mockup: {digest}"
    img = Image.open(path).convert("RGB")
    img = img.resize((1800, round(img.height * 1800 / img.width)),
                     Image.BOX)
    m = np.asarray(img).astype(float)
    out = {"sha256": digest}
    for key, r in COLONY.items():
        out[key] = fill(m, r)
    for key, r in COLONY_LINES.items():
        out[key] = line(m, r, 0)[0]
    for key, r in COLONY_SCROLL.items():
        out["scroll_" + key] = fill(m, r)
    for key, r in COLONY_WORDS.items():
        out["text_" + key] = word(m, r)[0]
    return out
