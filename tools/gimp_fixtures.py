#!/usr/bin/env python3
"""Write the two PNGs Data cuts the colony frame against, in GIMP.

    python tools/gimp_fixtures.py
    python tools/gimp_fixtures.py --resolution 3840x2160 --out /tmp/g

Two files per run, both from `layout_reference.json` and nothing else:

  colony_layermask_<WxH>_<date>.png   a GIMP LAYER MASK. White keeps
                                      the pixel, black cuts it, so the
                                      windows are BLACK on white —
                                      the opposite of what
                                      `tools/frame_mask.py` writes,
                                      and the reason
                                      `colony_frame_check.py` finds
                                      the convention instead of
                                      assuming one.
  colony_holes_guide_<WxH>_<date>.png the same rectangles with their
                                      NAMES and coordinates beside
                                      them, to read while placing
                                      boxes. Not a mask: it carries
                                      ink inside the metal.

**WHY THIS FILE EXISTS AT ALL** — 12 September 2026. Both PNGs were
already in `~/orionlayer-fixtures/gimp/`, dated 11 September, made by
hand with nothing in the tree that could make them again. That is the
state decision 40 is about: a file nobody can regenerate is authored
state whoever believes otherwise, and the first thing that happens to
it is that the layout moves and it does not. The sort row going from
two boxes to eight is exactly that, and rather than hand-editing them
a second time the generator is written.

**FOURTEEN RECTANGLES, NOT EIGHT** — the one `sort_bar` is seven
`sort_<key>` slots since 12 September 2026 (DEVIATION, fundament
decision 54), and the guide says so in the picture, because the
picture is what Data has open while he places them.

**IT WRITES OUTSIDE THE TREE ON PURPOSE.** The default output is
`~/orionlayer-fixtures/gimp/`, where Data's artwork lives, because
these are working files for a GIMP session and not repository
content — *"Data's artwork is not in the tree and never will be"*.
Nothing here is committed and nothing in the repository reads them.

**THE TEXT IS GERMAN** and that is not a slip of the English rule:
the rule is for identifiers, comments and documentation, and this is
neither — it is a note to the maintainer, printed into a picture he
opens in GIMP. Conversation with the maintainer is German.

Requires: Pillow.
"""
import argparse
import datetime
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("Pillow is missing. Run: pip install pillow --break-system-packages")

import frame_holes  # noqa: E402
import frame_mask  # noqa: E402

DEFAULT_OUT = os.path.expanduser("~/orionlayer-fixtures/gimp")

#: A GIMP layer mask keeps what is white. So the metal is white and
#: every window is black — the inverse of `frame_mask.py`'s WINDOW /
#: METAL, which is the whole reason the validator tries three
#: readings rather than defaulting to one.
MASK_METAL, MASK_WINDOW = 255, 0

GUIDE_GROUND = (24, 24, 28)
GUIDE_HOLE = (0, 0, 0)
GUIDE_EDGE = (255, 70, 255)
GUIDE_NAME = (255, 110, 255)
GUIDE_VALUE = (175, 175, 190)
GUIDE_FAINT = (110, 110, 120)

FONTS = ("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")


def font(size):
    for path in FONTS:
        if os.path.isfile(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def layermask(windows, width, height):
    image = Image.new("L", (width, height), MASK_METAL)
    _img, rects = frame_mask.render(windows, width, height)
    for _name, (x, y, w, h) in sorted(rects.items()):
        image.paste(Image.new("L", (w, h), MASK_WINDOW), (x, y))
    return image, rects


def guide(windows, width, height, lr):
    """The same rectangles, named, with the notes underneath.

    **NAMES COME FROM THE NAMER, NOT FROM THE REFERENCE FILE.**
    `layout_reference.json` calls two of them `return_button` and
    `list`; the boxes on the screen are `return` and `list_area`, and
    a guide that printed the reference's spelling would have Data
    looking for a box nobody else calls that.

    **A BOX TOO SMALL FOR ITS OWN CAPTION GETS A NUMBER**, and the
    numbers are listed inside `list_area`, which is the one window
    with room to spare. The eight boxes of the sort row are that
    case: the previous guide put a one-line caption above each of
    two, and eight of them overprinted each other into a smear —
    which is a guide that is worse than none, because it looks like
    it says something. The captions are never drawn outside the
    canvas either: this image is exactly the frame's size, so a
    caption above the header has nowhere to go and goes inside it.
    """
    image = Image.new("RGB", (width, height), GUIDE_GROUND)
    draw = ImageDraw.Draw(image)
    _img, rects = frame_mask.render(windows, width, height)
    scale = min(width / frame_mask.REF_W, height / frame_mask.REF_H)
    big, mid, small = (font(max(9, int(v * scale)))
                       for v in (22, 17, 13))
    pad = int(6 * scale)
    legend = []
    # ROW BY ROW, THEN LEFT TO RIGHT — `frame_holes._rows`' own
    # grouping and not a sort on y. The sort slots sit at y 961 and
    # 962 because that is where the artwork cut them, so a plain y
    # sort interleaves the row and numbers it 1 2 4 3 5.
    _order = {}
    for _i, _row in enumerate(frame_holes._rows(list(rects.values()))):
        for _j, _r in enumerate(_row):
            _order[tuple(_r)] = (_i, _j)
    for name, (x, y, w, h) in sorted(
            rects.items(), key=lambda kv: _order[tuple(kv[1])]):
        draw.rectangle((x, y, x + w - 1, y + h - 1), fill=GUIDE_HOLE,
                       outline=GUIDE_EDGE, width=max(1, int(2 * scale)))
        label = frame_holes.BOX_NAME.get(name, name).upper()
        stack = [(label, GUIDE_NAME, big),
                 (f"x {x}   y {y}", GUIDE_VALUE, mid),
                 (f"b {w}   h {h}", GUIDE_VALUE, mid),
                 (f"letztes Px  x {x + w - 1}, y {y + h - 1}",
                  GUIDE_FAINT, small)]
        tall = sum(int(f.size * 1.35) for _t, _c, f in stack)
        wide = max(draw.textlength(t, font=f) for t, _c, f in stack)
        one = f"{label}   x {x}  y {y}  b {w}  h {h}"
        if tall + 2 * pad <= h and wide + 2 * pad <= w:
            ty = y + pad
            for text, colour, fnt in stack:
                draw.text((x + pad, ty), text, fill=colour, font=fnt)
                ty += int(fnt.size * 1.35)
        elif draw.textlength(one, font=mid) + 2 * pad <= w and \
                mid.size + 2 * pad <= h:
            draw.text((x + pad, y + (h - mid.size) // 2), one,
                      fill=GUIDE_NAME, font=mid)
        else:
            legend.append((len(legend) + 1, label, x, y, w, h))
            tag = str(legend[-1][0])
            tw = draw.textlength(tag, font=big)
            draw.text((x + (w - tw) // 2, y + (h - big.size) // 2 - 2),
                      tag, fill=GUIDE_NAME, font=big)

    ring = lr["ring"]
    notes = [
        f"Leinwand {width}x{height}, exakt 16:9 - das Bild wird ueber "
        f"die ganze {frame_mask.REF_W}x{frame_mask.REF_H}-"
        f"Referenzflaeche gezogen (screen._scale_frame).",
        f"Die {len(rects)} schwarzen Rechtecke sind die Loecher. Zum "
        f"Schneiden die Maske nehmen "
        f"(colony_layermask_{width}x{height}_<datum>.png), nicht diese "
        f"Datei - hier steht Schrift IN den Loechern.",
        "SORT_BAR ist seit 12.09. weg: die sieben Sortiertasten haben "
        "wieder je ein eigenes Loch. Das ist die Umkehrung von Stufe "
        "A3 und steht als DEVIATION im Fundament, Entscheidung 54.",
        "Ausgangswerte gemessen am alten 14-Loch-Rahmen "
        "(frame_1920_retouched_2026-09-10.png), NICHT am Galaxy-"
        "Master: dessen Unterkante hat SECHS Loecher, nicht sieben.",
        "SORT_BC ist schmal, weil es sonst 121 ref px in RETURN "
        "laeuft, und die ganze Reihe ist 4 px niedriger als gemessen, "
        "weil sie sonst aus dem Ring faellt. Verschoben wird der Slot, "
        "nie RETURN und nie der Ring.",
        "Die Sortierslots sind von Hand zu setzen. Die Namen folgen "
        "der GEOMETRIE, nicht der Reihenfolge - zwei vertauschte "
        "Slots behalten ihre Namen (tools/frame_holes.py).",
    ]
    # THE LEGEND AND THE NOTES GO INSIDE `list_area`. The bottom ring
    # band is 148 px at 3840x2160 and this is fifteen lines; the list
    # is the only window with the room, and it is empty in a guide.
    # `rects` is keyed by layout_reference's own names, so the list is
    # `list` here and `list_area` only after `BOX_NAME`.
    _list_key = next(k for k in rects
                     if frame_holes.BOX_NAME.get(k, k) == "list_area")
    lx, ly, lw, _lh = rects[_list_key]
    ty = ly + pad + int(big.size * 1.35) + 3 * int(mid.size * 1.35) \
        + int(small.size * 1.35) + int(20 * scale)
    if legend:
        draw.text((lx + pad, ty), "Zu klein fuer eine Beschriftung im "
                  "Loch - hier die Nummern:", fill=GUIDE_NAME, font=mid)
        ty += int(mid.size * 1.7)
        for idx, label, x, y, w, h in legend:
            draw.text((lx + pad, ty),
                      f"{idx:>2}  {label:<16s} x {x:>5} y {y:>5} "
                      f"b {w:>5} h {h:>4}   letztes Px x {x + w - 1}, "
                      f"y {y + h - 1}", fill=GUIDE_VALUE, font=mid)
            ty += int(mid.size * 1.35)
        ty += int(14 * scale)
    for line in notes:
        draw.text((lx + pad, ty), line, fill=GUIDE_FAINT, font=small)
        ty += int(small.size * 1.45)

    draw.text((lx, height - ring["bottom"] * scale + pad),
              f"RING (Metall aussen, kein Loch):  links "
              f"{int(ring['left'] * scale)}   rechts "
              f"{int(ring['right'] * scale)}   oben "
              f"{int(ring['top'] * scale)}   unten "
              f"{int(ring['bottom'] * scale)} px",
              fill=GUIDE_VALUE, font=mid)
    return image


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--reference", default=frame_mask.REFERENCE)
    ap.add_argument("--resolution", action="append",
                    help="WxH; repeatable. Default: 3840x2160, the "
                         "size the fixtures are cut at.")
    ap.add_argument("--date", default=None,
                    help="date stamp in the file name; default today")
    args = ap.parse_args()

    lr, windows = frame_mask.load_reference(args.reference)
    stamp = args.date or datetime.date.today().isoformat()
    os.makedirs(args.out, exist_ok=True)
    for spec in args.resolution or ["3840x2160"]:
        width, height = (int(v) for v in spec.lower().split("x"))
        mask, rects = layermask(windows, width, height)
        mpath = os.path.join(
            args.out, f"colony_layermask_{width}x{height}_{stamp}.png")
        mask.save(mpath)
        gpath = os.path.join(
            args.out, f"colony_holes_guide_{width}x{height}_{stamp}.png")
        guide(windows, width, height, lr).save(gpath)
        print(f"{spec}: {len(rects)} rects -> {mpath}")
        print(f"{spec}: {len(rects)} rects named -> {gpath}")
    print("Written outside the tree; nothing here is committed.")


if __name__ == "__main__":
    main()
