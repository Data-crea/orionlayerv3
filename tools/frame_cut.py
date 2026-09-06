#!/usr/bin/env python3
"""Cut the window holes into the frame artwork, one PNG per resolution.

    python tools/frame_cut.py path/to/frame_1080p.png
    python tools/frame_cut.py art.png --resolution 3840x2160

Takes the artwork Data draws from the 1080p mask — metal only,
windows flat black — scales it to each supported resolution and
writes an RGBA frame whose alpha is 0 exactly where
`layout_reference.json` says a window is.

**THE ALPHA COMES FROM THE MASK, NEVER FROM THE ARTWORK'S OWN
BLACK.** Two reasons, and the second is the one that bites. Artwork
black is not reliably 0 after a scale — a bilinear resample bleeds
the metal into the hole and a threshold has to be invented — and the
holes have to land on the SAME rectangles at every resolution, which
only the reference file knows. Cutting from the artwork would make
the hole a property of the picture; cutting from the mask makes it a
property of the layout, which is what `boxes.json` and every hit test
also read.

**AND IT KILLS THE NAME GUESS.** `frame_holes.py` maps a hole to a
box name BY POSITION, with a hand-written rule per screen — and it
had the colony screen's last two names the wrong way round until
4 September 2026 (`layout.json`, `panels._note`). Here every hole is
cut from a rectangle that already has a name, so the mapping is by
construction and there is nothing to get the wrong way round.
`--boxes` writes that mapping out; `frame_holes.py` then verifies
rather than guesses.

**GENERATED, NEVER COMMITTED** (decision 40). The artwork is the
input and is Data's; everything this writes is derived from it plus
a committed JSON, and regenerating reproduces it byte for byte.

Requires: Pillow (pip install pillow --break-system-packages).
"""
import argparse
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
# ITS OWN DIRECTORY, EXPLICITLY. `import frame_mask` resolved only
# because running a script puts its directory on sys.path — so this
# module imported fine from the shell and not from a loader that
# addresses it by path, which is how the smoke test reaches it. It
# passed there only because something earlier in that run had
# already put tools/ on the path: a dependency on the order of
# unrelated checks, which is the shape of fault this project keeps
# writing down.
sys.path.insert(0, _HERE)

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is missing. Run: pip install pillow --break-system-packages")

import frame_mask  # noqa: E402  (same directory)

ROOT = frame_mask.ROOT
DEFAULT_OUT = os.path.join(ROOT, "screens", "colony_summary", "assets",
                           "frames")

#: Alpha values. Opaque metal, fully transparent window — and nothing
#: between: `frame_holes.py` thresholds at 16 and a soft rim would
#: make the hole's size depend on where that threshold sits.
OPAQUE, HOLE = 255, 0


def cut(artwork, windows, width, height):
    """The artwork at `width x height`, holes punched from the mask.

    LANCZOS for the metal because it is a photograph of a surface and
    a nearest-neighbour resample of one is visibly wrong; the ALPHA is
    built from the rectangles afterwards and never resampled, so the
    edges stay hard whatever the filter does to the colour.
    """
    scaled = artwork.convert("RGB").resize((width, height), Image.LANCZOS)
    alpha = Image.new("L", (width, height), OPAQUE)
    _image, rects = frame_mask.render(windows, width, height)
    for _name, (x, y, w, h) in sorted(rects.items()):
        alpha.paste(Image.new("L", (w, h), HOLE), (x, y))
    scaled.putalpha(alpha)
    return scaled, rects


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("artwork", help="the frame artwork, metal only")
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--reference", default=frame_mask.REFERENCE)
    ap.add_argument("--resolution", action="append")
    ap.add_argument("--boxes", metavar="PATH",
                    help="also write the named rectangles as a boxes.json "
                         "fragment. It is NOT written over boxes.json: the "
                         "screen that reads that file is still the old one, "
                         "and the swap belongs to the commit that makes the "
                         "new modules default.")
    args = ap.parse_args()

    if not os.path.isfile(args.artwork):
        sys.exit(f"No artwork at {args.artwork}. It is drawn from the 1080p "
                 f"mask that tools/frame_mask.py writes — metal only, "
                 f"windows flat black.")
    data, windows = frame_mask.load_reference(args.reference)
    wanted = args.resolution or data.get("_resolutions")
    artwork = Image.open(args.artwork)

    os.makedirs(args.out, exist_ok=True)
    fragment = {}
    for spec in wanted:
        width, height = (int(v) for v in spec.lower().split("x"))
        image, rects = cut(artwork, windows, width, height)
        path = os.path.join(args.out, f"frame_{width}x{height}.png")
        image.save(path)
        # The reference rect is what boxes.json holds — `Layout.rect`
        # scales it at load. The device rect is what this run punched
        # and is what `frame_holes.py` will measure.
        fragment[spec] = [{"name": name, "rect": list(windows[name]),
                           "role": ["display"]}
                          for name in sorted(rects)]
        print(f"{spec}: {len(rects)} holes -> {path}")

    if args.boxes:
        with open(args.boxes, "w", encoding="utf-8") as fh:
            json.dump(fragment, fh, indent=2, sort_keys=True)
            fh.write("\n")
        print(f"boxes fragment -> {args.boxes} (NOT boxes.json)")
    print("Generated: none of this is committed (.gitignore, decision 40).")


if __name__ == "__main__":
    main()
