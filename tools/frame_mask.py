#!/usr/bin/env python3
"""Render the colony screen's window mask, one PNG per resolution.

    python tools/frame_mask.py
    python tools/frame_mask.py --out /somewhere --resolution 1920x1080

Reads `screens/colony_summary/layout_reference.json` — the ONE place
the screen's rectangles are typed — and writes, per supported
resolution, a black image with every window painted white. That is
the input the frame artwork is drawn from, and it is what
`tools/frame_holes.py` and `boxes.json` are later asserted against
(decision 3): holes == mask == boxes, at every resolution.

**GENERATED, NEVER COMMITTED** (decision 40, `.gitignore`). The
licence to ignore it is that regenerating reproduces it byte for
byte, which the smoke test asserts by rendering the rectangles a
second time and comparing.

**WHITE IS A WINDOW, BLACK IS METAL, AND THERE IS NO THIRD VALUE.**
Not anti-aliased and not greyed at the edges: the mask is a
predicate, and a mask with soft edges cannot answer "is this pixel a
window" without a threshold nobody wrote down. `frame_holes.py`
reads the artwork's alpha and needs the same predicate on both sides.

Requires: Pillow (pip install pillow --break-system-packages).
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is missing. Run: pip install pillow --break-system-packages")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFERENCE = os.path.join(ROOT, "screens", "colony_summary",
                         "layout_reference.json")
#: Anchored to the project, not to the working directory — the fault
#: `nebula_extract.py` and `help_extract.py` each shipped once.
DEFAULT_OUT = os.path.join(ROOT, "screens", "colony_summary", "assets",
                           "frame_masks")

#: Reference space. Same constants `core/config.py` holds for the
#: running app; imported rather than retyped would drag pygame into a
#: tool that needs none of it, so they are asserted against it in the
#: smoke test instead.
REF_W, REF_H = 1920, 1080

WINDOW, METAL = (255, 255, 255), (0, 0, 0)

#: Every key of `layout_reference.json` that is a window. `ring` is
#: four named values rather than a rectangle and `list_columns`
#: divides one that is already here, so neither appears; a key that
#: is neither a window nor explicitly excluded is an error rather
#: than a silent omission. (`bezel` was here until 7 September 2026,
#: when the single number was replaced by the four-value ring: a
#: border that is 107 wide at the sides and 18 at the top cannot be
#: described by one number.)
NOT_A_WINDOW = ("ring", "list_columns", "figure_scale", "_resolutions")


def load_reference(path=REFERENCE):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    windows = {}
    for key, value in data.items():
        if key.startswith("_") or key in NOT_A_WINDOW:
            continue
        if not (isinstance(value, list) and len(value) == 4
                and all(isinstance(v, int) for v in value)):
            sys.exit(f"{key}: not a rectangle and not excluded — add it "
                     f"to NOT_A_WINDOW or make it [x, y, w, h].")
        windows[key] = value
    return data, windows


def scale_rect(rect, scale):
    """Reference rect -> device rect, EXACTLY as `Layout.rect` does.

    `int()` and not `round()`, because the running screen truncates
    (core/layout.py) and a mask that rounded would disagree with the
    boxes by a pixel at 1440p on every odd coordinate — the class of
    fault decision 3 exists to make impossible.

    No letterbox offset: every supported resolution is 16:9, so
    `Layout.offset_x/y` are 0 and adding them here would encode an
    assumption this tool cannot check.
    """
    x, y, w, h = rect
    return (int(x * scale), int(y * scale), int(w * scale), int(h * scale))


def render(windows, width, height):
    scale = min(width / REF_W, height / REF_H)
    image = Image.new("RGB", (width, height), METAL)
    rects = {}
    for name, rect in sorted(windows.items()):
        x, y, w, h = scale_rect(rect, scale)
        rects[name] = [x, y, w, h]
        image.paste(Image.new("RGB", (w, h), WINDOW), (x, y))
    return image, rects


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--reference", default=REFERENCE)
    ap.add_argument("--resolution", action="append",
                    help="WxH; repeatable. Default: the reference file's "
                         "own _resolutions list.")
    args = ap.parse_args()

    data, windows = load_reference(args.reference)
    wanted = args.resolution or data.get("_resolutions")
    if not wanted:
        sys.exit(f"{args.reference} lists no _resolutions and none was "
                 f"passed with --resolution.")

    os.makedirs(args.out, exist_ok=True)
    table = {}
    for spec in wanted:
        try:
            width, height = (int(v) for v in spec.lower().split("x"))
        except ValueError:
            sys.exit(f"--resolution {spec!r}: expected WxH, e.g. 1920x1080")
        image, rects = render(windows, width, height)
        path = os.path.join(args.out, f"frame_mask_{width}x{height}.png")
        image.save(path)
        table[spec] = rects
        covered = sum(r[2] * r[3] for r in rects.values())
        print(f"{spec}: {len(rects)} windows, "
              f"{100 * covered / (width * height):.1f} % of the frame is "
              f"window -> {path}")

    # The device rectangles, so Stage 2 can assert the artwork's holes
    # against the numbers the mask was actually painted with rather
    # than against a second scaling of the reference.
    rects_path = os.path.join(args.out, "rects.json")
    with open(rects_path, "w", encoding="utf-8") as fh:
        json.dump(table, fh, indent=1, sort_keys=True)
    print(f"device rectangles -> {rects_path}")
    print("Generated: none of this is committed (.gitignore, decision 40).")


if __name__ == "__main__":
    main()
