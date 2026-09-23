#!/usr/bin/env python3
"""Cut the research panel's frame out of the Fleets artwork.

    python tools/make_research_frame.py

Work order 166 part B. Data chose the Fleets screen's own inner frame —
the one around the scanner map, with the orange lamps in its four
corners — as the research panel's outer frame, in both modes.

**DERIVED, not authored** (decision 49's surviving half): the input is
committed, the output is not, the cut is a PLAIN CROP so a rebuild
reproduces it byte for byte, and a smoke check rebuilds it in memory
and compares. `tools/setup.py` runs this, so a clone gets it.

**WHERE IT COMES FROM, measured and not eyeballed.**
`tools/frame_holes.py` reads the Fleets frame's own transparent holes
and names that one `inset_map` at image (228, 211, 1491, 906). The
frame around it was found by walking OUTWARD from the hole's edge on
50 rows and 50 columns and stopping at the first run of eight dark
pixels — the gap between this frame and its neighbours — and taking
the mode of the results:

    left   x 205   (rail 23 px)      right  x 1741  (rail 23 px)
    top    y 189   (rail 22 px)      bottom y 1138  (rail 22 px)

so the cut is (205, 189) to (1741, 1138), 1537 x 950.

**THE CORNERS ARE 140 px**, which is what the nine-slice needs to keep
whole. Each corner bracket reaches at most 132 px along either axis
beyond the plain rail — measured per corner as the furthest opaque
pixel outside the rail band: TL 128x127, TR 127x124, BL 130x130,
BR 132x129. 140 gives every one of them room and leaves 1257 px of
plain rail to stretch.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from core.config import BASE_DIR  # noqa: E402

#: The picture the frame is cut out of. Committed; 3840x2160.
SOURCE = os.path.join("screens", "fleets", "assets", "frame.png")

#: Where the cut goes. Shared, because BOTH research screens wear it
#: and a second copy of one image is a second thing to keep in step.
OUTPUT = os.path.join("assets", "shared", "frames", "research_panel.png")

#: (x, y, w, h) in the source's own pixels — see the module docstring.
CUT = (205, 189, 1537, 950)

#: The nine-slice corner, in the source's pixels. See the docstring:
#: the largest corner bracket reaches 132 px.
CORNER = 140

#: The plain rail's thickness in the source, for the caller that has
#: to put the frame's opening over a box: top/bottom 22, left/right 23.
RAIL = 23


def build(root=None):
    """Write the cut. Returns the output path."""
    root = root or BASE_DIR
    pygame.init()
    src = pygame.image.load(os.path.join(root, SOURCE))
    out = pygame.Surface((CUT[2], CUT[3]), pygame.SRCALPHA)
    out.blit(src, (0, 0), CUT)
    path = os.path.join(root, OUTPUT)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pygame.image.save(out, path)
    return path


def main():
    path = build()
    surf = pygame.image.load(path)
    print(f"  research panel frame: {surf.get_width()}x"
          f"{surf.get_height()} cut at {CUT} from {SOURCE}")
    print(f"  -> {os.path.relpath(path, BASE_DIR)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
