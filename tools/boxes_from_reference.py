#!/usr/bin/env python3
"""Write a screen's cutout boxes straight from `layout_reference.json`.

    python tools/boxes_from_reference.py colony_summary
    python tools/boxes_from_reference.py colony_summary --check

**THE MIDDLE OF THE CHAIN IS GONE** — 12 September 2026, Data's
decision, Phase A. Decision 3's chain was

    layout_reference.json -> frame_mask -> frame_build -> frame_cut
                          -> frame_holes --write -> boxes.json

and the artwork in the middle of it existed to turn a rectangle into
a hole so the hole could be measured back into a rectangle. With the
colony screen drawing its own boxes there is no artwork, so the chain
is `layout_reference.json -> boxes.json` and this is the whole of it.

**IT PRODUCES THE SAME NUMBERS, AND THAT IS ASSERTED AND NOT HOPED.**
`frame_holes.to_ref` maps a hole back with `int(round(x * REF_W /
img_w)) - BLEED`, and the plate is generated at exactly the reference
size, so the scale is 1 and the round-trip is the identity. The rects
this writes are therefore byte-for-byte what `frame_holes --write`
wrote, which is what lets the flag be flipped without a single content
rect moving. `--check` is that comparison, and the smoke test runs it.

**WHAT IT DOES NOT TOUCH.** Boxes that are not cutouts survive
verbatim — the six colony column boxes are strips of `list_area`,
placed by hand in the editor, and regenerating the cutouts must not
delete them. Same rule, and the same reason, as `frame_holes --write`.

**AND IT KEEPS STYLE AND ROLE.** A cutout box carries a `role` and
sometimes a `style` (`font_size` on the seven sort slots and RETURN),
neither of which is derivable from a rectangle. They are read off the
file being rewritten, so the only thing this changes is geometry.
"""
import argparse
import collections
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(_HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, _HERE)
# The screen package imports pygame; this tool never opens a window.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

#: Reference-pixel bleed so content covers what the rim overlaps.
#: **THE SAME TWO PX, AND NOT A NEW NUMBER.** With the plate it paid
#: for an anti-aliased hole edge; with a drawn box it pays for the rim
#: band and the lit line that sit on the rectangle's own edge
#: (`colonyplates.RIM_REF` is 2). One number, one reason either way:
#: the drawable rect is the typed rect grown by what overlaps it.
BLEED = 2

#: The keys of `layout_reference.json` that are not windows, and the
#: rectangle-to-box renaming. BOTH ARE THE SCREEN'S, imported rather
#: than retyped — `screens/colony_summary/colonyplates.py` is where
#: they live once the tools are gone, so a tool that kept its own copy
#: would be the second copy this project keeps paying for.
def _screen_rules(screen):
    sys.path.insert(0, ROOT)
    mod = __import__(f"screens.{screen}.colonyplates",
                     fromlist=["colonyplates"])
    return mod.NOT_A_WINDOW, mod.BOX_NAME


def reference_boxes(screen):
    """[(box name, [x, y, w, h])] in `layout_reference.json`'s order."""
    not_a_window, box_name = _screen_rules(screen)
    path = os.path.join(ROOT, "screens", screen, "layout_reference.json")
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh, object_pairs_hook=collections.OrderedDict)
    out = []
    for key, value in data.items():
        if key.startswith("_") or key in not_a_window:
            continue
        if not (isinstance(value, list) and len(value) == 4
                and all(isinstance(v, int) for v in value)):
            sys.exit(f"{key}: not a rectangle and not excluded — add it "
                     f"to colonyplates.NOT_A_WINDOW or make it "
                     f"[x, y, w, h].")
        x, y, w, h = value
        out.append((box_name.get(key, key),
                    [x - BLEED, y - BLEED, w + 2 * BLEED, h + 2 * BLEED]))
    return out


def rebuild(screen, boxes_path=None):
    """The new `boxes.json` content, as an OrderedDict. Writes nothing."""
    boxes_path = boxes_path or os.path.join(
        ROOT, "screens", screen, "boxes.json")
    with open(boxes_path, encoding="utf-8") as fh:
        data = json.load(fh, object_pairs_hook=collections.OrderedDict)
    derived = reference_boxes(screen)
    names = {n for n, _r in derived}
    for res, boxes in data.items():
        old = {b["name"]: b for b in boxes}
        out = []
        for name, rect in derived:
            was = old.get(name, {})
            entry = collections.OrderedDict(
                (("name", name), ("rect", rect),
                 ("role", was.get("role", ["display"]))))
            if "style" in was:
                entry["style"] = was["style"]
            out.append(entry)
        data[res] = out + [b for b in boxes if b["name"] not in names]
    return data


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("screen")
    ap.add_argument("--check", action="store_true",
                    help="compare against boxes.json and exit 1 on a "
                         "difference; write nothing")
    args = ap.parse_args()

    path = os.path.join(ROOT, "screens", args.screen, "boxes.json")
    with open(path, encoding="utf-8") as fh:
        before = fh.read()
    after = json.dumps(rebuild(args.screen), indent=2) + "\n"
    derived = reference_boxes(args.screen)
    if args.check:
        if before == after:
            print(f"{args.screen}: boxes.json IS layout_reference.json "
                  f"plus {BLEED} px of bleed, {len(derived)} cutouts")
            return 0
        print(f"{args.screen}: boxes.json is NOT what "
              f"layout_reference.json plus {BLEED} px gives. Run "
              f"without --check to rewrite it.")
        return 1
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(after)
    print(f"{args.screen}: {len(derived)} cutout boxes from "
          f"layout_reference.json + {BLEED} px -> {path}"
          + ("" if before != after else "  (unchanged)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
