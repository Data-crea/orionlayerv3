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
#: (`colonyplates.RIM_REF` is 2), and with the static frame for the
#: artwork's own rim. One number, one reason every way: the drawable
#: rect is the typed rect grown by what overlaps it.
#:
#: IMPORTED FROM THE SCREEN, never declared here. The screen rebuilds
#: these same rects at startup (`colonyplates.box_rects`), so a tool
#: with its own copy could write a `boxes.json` two pixels away from
#: what the running screen uses and nothing would report it.
def _bleed():
    return __import__("screens.colony_summary.colonyplates",
                      fromlist=["colonyplates"]).BLEED

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
    BLEED = _bleed()
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


def reseat_columns(data, screen):
    """Lay the `col_*` boxes across `list_area` by `list_columns`.

    **THE SPLIT IS ALREADY DECLARED and this is the only place that
    reads it as geometry.** `layout_reference.list_columns` holds six
    reference widths summing to the list's own width, which is where
    every note about the columns argues from; `colonytrack.columns`
    then reads each BOX's left edge as an offset into `list_area` and
    takes the width as the distance to the next. So seating a column
    means putting its left edge at the running sum of the split,
    scaled into whatever width the list now has.

    Order matters and is the file's: `list_columns` is written in
    ECON order with the name column first and the scroll slot last,
    the same order `colonyheader.COLUMN_BOXES` names them in.
    """
    path = os.path.join(ROOT, "screens", screen, "layout_reference.json")
    with open(path, encoding="utf-8") as fh:
        ref = json.load(fh, object_pairs_hook=collections.OrderedDict)
    cols = ref.get("list_columns")
    if not cols:
        return 0
    # **THE SCROLL COLUMN IS AN ABSOLUTE WIDTH AND THE OTHER FIVE ARE
    # FRACTIONS.** Native x 619..627 is 9 px, which is 27 reference px
    # (colsum.cpp:263-264 for the arrows' field x, :278 and :759 for
    # the track it holds), and a smoke check holds `col_scroll` to
    # exactly that. Scaling it with the rest put it at 22 the first
    # time the list got narrower — the transcription quietly turned
    # into a share. So it is taken off the top and the remaining five
    # split what is left, in their own ratios.
    last = list(cols)[-1]
    fixed = cols[last]
    total = sum(v for k, v in cols.items() if k != last)
    moved = 0
    for _res, boxes in data.items():
        area = next((b["rect"] for b in boxes if b["name"] == "list_area"),
                    None)
        if area is None:
            continue
        ax, ay, aw, ah = area
        span = aw - fixed
        off = 0
        for key, width in cols.items():
            name = f"col_{key}"
            box = next((b for b in boxes if b["name"] == name), None)
            if box is None:
                continue
            if key == last:
                want = [ax + aw - fixed, ay, fixed, ah]
            else:
                x = ax + round(off * span / total)
                nxt = (ax + aw - fixed if off + width >= total
                       else ax + round((off + width) * span / total))
                want = [x, ay, nxt - x, ah]
            if box["rect"] != want:
                box["rect"] = want
                moved += 1
            off += width
    return moved


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
    ap.add_argument("--columns", action="store_true",
                    help="also re-seat the six colony column boxes from "
                         "layout_reference's `list_columns` onto "
                         "`list_area`. NOT part of the default run: a "
                         "column is hand-placed and draggable, and "
                         "re-seating it throws a drag away. Run it when "
                         "the LIST has moved and the columns no longer "
                         "tile it.")
    ap.add_argument("--check", action="store_true",
                    help="compare against boxes.json and exit 1 on a "
                         "difference; write nothing")
    args = ap.parse_args()

    BLEED = _bleed()
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
    data = rebuild(args.screen)
    _moved = reseat_columns(data, args.screen) if args.columns else 0
    after = json.dumps(data, indent=2) + "\n"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(after)
    if args.columns:
        print(f"{args.screen}: {_moved} column box(es) re-seated from "
              f"list_columns onto list_area")
    print(f"{args.screen}: {len(derived)} cutout boxes from "
          f"layout_reference.json + {BLEED} px -> {path}"
          + ("" if before != after else "  (unchanged)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
