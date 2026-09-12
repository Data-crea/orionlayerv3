#!/usr/bin/env python3
"""Hold a colony frame PNG against the rules that are still rules.

    python tools/colony_frame_check.py ~/orionlayer-fixtures/gimp/mine.png
    python tools/colony_frame_check.py mask.png --holes dark

**READ-ONLY, AND IT WRITES NOTHING.** It opens one PNG, measures it
and prints. No boxes.json, no plate, no mask — nothing on disk
changes, so it can be pointed at a working file in the middle of a
GIMP session.

WHY IT EXISTS. On 11 September 2026 four layout enforcements left
`tools/smoke_test.py`, because they were rules WE chose rather than
rules transcribed from MOO2: the lower band flush with the list, the
band's three gaps equal, every gap equal to its role's strut, and the
ring pinned to the main-screen master. The suite keeps reporting
those numbers and no longer fails on them, so Data can move HEADER,
the four lower panels, SORT_BAR and RETURN.

What did NOT move is the rest, and the suite cannot check it on her
file: *"Data's artwork is not in the tree and never will be"* is
written into the frame-cut block, and it is right — a check that
needed her PNG would fail for anyone who cloned the repository. So
the rules that survive get a second home HERE, where the artwork
actually is, and this tool is the thing she runs before handing a
file over.

**IT DECIDES NOTHING.** Every line is a measured value with a verdict
beside it, and the exit code is 1 if any rule fails, so it can be
used in a pipeline — but there is no `--fix`, no writing, and no
guessing at what she meant. A hole that is 3 px off is reported as 3
px off.

**FOURTEEN WINDOWS SINCE 12 September 2026**, not eight: the one
`sort_bar` is seven slots again, one per sort key, because Data's
artwork cuts one per key. Every rule below is per BOX and none of
them counts to eight — `frame_holes.ROW_SHAPE` is where the shape is
stated, derived from the key lists rather than typed here.

THE HOLE CONVENTION IS FOUND, NOT ASSUMED, and that is not politeness
— the two mask conventions in this project are opposites.
`tools/frame_mask.py` writes WINDOWS WHITE on black; a GIMP layer
mask is the other way round, because there white KEEPS the pixel. A
default would silently invert somebody's file. So all three readings
are tried and the one that yields a valid four-row layout wins, and
the chosen one is printed.
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

import frame_holes  # noqa: E402
import frame_mask  # noqa: E402
from core.config import REF_W, REF_H  # noqa: E402

#: The original's widest job column: industry, reach 122 at pitch 30
#: (colsum.cpp:1006-1024 for the bounds). Four figures, and that is
#: the number a column of ours has to beat.
ORIG_FIT = max((r - l - 10) // 30 for l, r in
               ((101, 226), (236, 368), (378, 502)))
#: movebox.cpp:20-21 — the inset's coverage is 128*(506000//128) by
#: 91*(400000//91) world units and the galaxy size cancels.
INSET_ASPECT = (128 * (506000 // 128)) / (91 * (400000 // 91))
CONVENTIONS = ("alpha", "dark", "light")


def hole_mask(arr, how):
    """Boolean array, True where the image says "hole"."""
    if how == "alpha":
        if arr.shape[2] < 4:
            return None
        return arr[:, :, 3] < 16
    lum = arr[:, :, :3].mean(axis=2)
    return lum < 32 if how == "dark" else lum > 223


def find(mask):
    """[(x, y, w, h)] for every blob big enough to be a window."""
    from scipy import ndimage
    lab, n = ndimage.label(mask)
    out = []
    for sl in ndimage.find_objects(lab):
        ys, xs = sl
        x, y = xs.start, ys.start
        w, h = xs.stop - x, ys.stop - y
        if w * h < frame_holes.MIN_AREA:
            continue
        if x == 0 or y == 0 or xs.stop == mask.shape[1] \
                or ys.stop == mask.shape[0]:
            continue                       # touches the border: outside
        out.append((x, y, w, h))
    return out


def read(path, forced=None):
    """(array, convention, holes, rows) — the reading that worked.

    Tried in order and scored by whether the naming rule accepts the
    result, so an image that is legible both ways still lands on the
    one this screen can use.
    """
    arr = np.array(Image.open(path).convert("RGBA"))
    size = (arr.shape[1], arr.shape[0])
    tried = []
    for how in ([forced] if forced else CONVENTIONS):
        mask = hole_mask(arr, how)
        if mask is None or not mask.any():
            tried.append((how, "nothing found"))
            continue
        holes = find(mask)
        rows = frame_holes._rows(holes)
        note = f"{len(holes)} holes, rows {[len(r) for r in rows]}"
        # **SCORED BY WHETHER THE NAMER ACCEPTS IT**, which is what
        # the docstring always claimed and what this stopped doing
        # when the namer began matching against `layout_reference
        # .json`. A row shape compared here was a second, weaker copy
        # of the namer's own gate, and the two parted the first time a
        # window had no hole of its own: the shape of ALL the holes is
        # not the shape of the holes a RECTANGLE claims.
        try:
            frame_holes.name_holes(holes, "colony_summary", size)
            tried.append((how, note))
            return arr, how, holes, rows, tried
        except SystemExit as why:
            tried.append((how, f"{note} — {why}"))
            if forced:
                return arr, how, holes, rows, tried
    return arr, None, [], [], tried


def rule(name, ok_, detail):
    print(f"  {'PASS' if ok_ else 'FAIL'}  {name}: {detail}")
    return 0 if ok_ else 1


def check_rows(rows, holes, size):
    """Name the holes, or say why they cannot be named.

    **THE MATCH IS THE RULE AND THE ROW SHAPE IS NOT** — 12 September
    2026. Order named these holes until the sort row grew to seven
    hand-placed slots; a fixed row shape gated the naming until the
    screen took a frame whose rows are not the plate's. What is left
    is the thing that was always meant: every rectangle in
    `layout_reference.json` finds a hole of its own, no two find the
    same one, and the claimed holes group into the rows the
    rectangles do — which is what still catches a window that has
    drifted into a neighbouring band. `frame_holes` owns all of it;
    this prints the answer and which way it went.
    """
    shape = [len(r) for r in rows]
    try:
        names = frame_holes.name_holes(holes, "colony_summary", size)
    except SystemExit as why:
        bad = rule("every rectangle lands on a hole of its own", False,
                   str(why))
        for i, r in enumerate(rows):
            print(f"          row {i}: {r}")
        return {}, bad
    bad = rule("every rectangle lands on a hole of its own", True,
               f"{len(names)} named, holes in rows {shape}")
    print(f"          matched by {frame_holes.LAST_MATCH}")
    for key, r in names.items():
        print(f"          {key:14s} {tuple(r)}")
    return names, bad


def check_rect_alpha(mask, names):
    """Every hole exactly its own rectangle — no ragged alpha."""
    bad = 0
    for key, (x, y, w, h) in sorted(names.items()):
        got = int(mask[y:y + h, x:x + w].sum())
        bad |= rule(f"rectangular hole {key}", got == w * h,
                    f"{got} of {w * h} px inside its bounding rect"
                    + ("" if got == w * h else
                       f", {w * h - got} missing"))
    return bad


def check_ring(arr, how, names, size):
    """Every hole strictly inside the artwork's own metal."""
    w_img, h_img = size
    if how == "alpha" and arr.shape[2] >= 4:
        metal = arr[:, :, 3] >= 250
    else:
        lum = arr[:, :, :3].mean(axis=2)
        metal = lum >= 32 if how == "dark" else lum <= 223
    ys, xs = np.where(metal)
    mx0, mx1 = int(xs.min()), int(xs.max())
    my0, my1 = int(ys.min()), int(ys.max())
    print(f"          metal spans x {mx0}..{mx1}, y {my0}..{my1} "
          f"of {w_img}x{h_img}")
    # THE RING IS WHAT THE OUTERMOST HOLES LEAVE, not a typed number
    # — the same definition `frame_build.device_ring` uses, and the
    # reason the "fixed ring inset" enforcement could be dropped from
    # the suite without losing anything: measured here, off the file.
    rect = [(x, y, x + w, y + h) for x, y, w, h in names.values()]
    ring = (min(r[0] for r in rect) - mx0,
            mx1 - max(r[2] for r in rect) + 1,
            min(r[1] for r in rect) - my0,
            my1 - max(r[3] for r in rect) + 1)
    print(f"          ring, as the outermost holes leave it: "
          f"left {ring[0]}  right {ring[1]}  top {ring[2]}  "
          f"bottom {ring[3]} px")
    bad = 0
    for key, (x, y, w, h) in sorted(names.items()):
        m = (x - mx0, mx1 - (x + w - 1), y - my0, my1 - (y + h - 1))
        bad |= rule(f"inside the ring {key}", min(m) > 0,
                    f"clear of the metal's edge by l/r/t/b "
                    f"{tuple(int(v) for v in m)}")
    return bad


def to_ref(rect, w_img, h_img):
    x, y, w, h = rect
    sx, sy = REF_W / w_img, REF_H / h_img
    return (x * sx, y * sy, w * sx, h * sy)


def check_inset(names, w_img, h_img):
    x, y, w, h = to_ref(names["galaxy_inset"], w_img, h_img)
    bad = rule("inset aspect (movebox.cpp:20-21)",
               abs(w / h - INSET_ASPECT) < 0.001,
               f"{w / h:.5f} against {INSET_ASPECT:.5f}, "
               f"delta {abs(w / h - INSET_ASPECT):.5f}")
    floor = w * 91 / 128
    bad |= rule("inset minimum height", h >= floor,
                f"{h:.0f} ref px against the {floor:.0f} below which "
                f"HEIGHT binds and the map gets panel either side")
    return bad


def check_list(names, w_img, h_img, lr):
    """figure_step per resolution, and the column capacity under it."""
    import pygame
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    from core.layout import Layout
    from screens.colony_summary import colonytrack
    import json
    cfg = json.load(open(os.path.join(
        os.path.dirname(_HERE), "screens", "colony_summary",
        "layout.json"), encoding="utf-8"))["list"]
    lx, ly, lw, lh = to_ref(names["list_area"], w_img, h_img)
    bleed = frame_holes.BLEED
    area_ref = [lx - bleed, ly - bleed, lw + 2 * bleed, lh + 2 * bleed]
    cols = lr["list_columns"]
    # THE COLUMN IS A FRACTION OF THE LIST (colonytrack.columns), so
    # the narrowest job column follows a list of any width and there
    # is no table to keep in step.
    narrow = min(cols[k] for k in ("farmers", "workers", "scientists"))
    share = narrow / sum(cols.values())
    print(f"          list hole {tuple(round(v) for v in (lx, ly, lw, lh))} "
          f"ref -> list_area {[round(v) for v in area_ref]} (+{bleed}/side)")
    bad = 0
    for spec in lr["_resolutions"]:
        sw, sh = (int(v) for v in spec.split("x"))
        lay = Layout(sw, sh)
        rect = pygame.Rect(*lay.rect(area_ref))
        step = colonytrack.figure_step(rect, cfg)
        colw = area_ref[2] * share * lay.scale
        fits = int((colw - 28 * step) // (30 * step) + 1)
        bad |= rule(f"figure column at {spec}", fits >= ORIG_FIT,
                    f"band {rect.h / 10:.0f} px -> step {step}, "
                    f"column {colw:.0f} px fits {fits} unsquashed "
                    f"figures (original's widest fits {ORIG_FIT})")
    return bad


def report_sort_rails(names, w_img, h_img):
    """The metal between the slots, per gap. A REPORT AND NO RULE.

    The suite dropped "every gap is exactly its role's strut" on
    11 September 2026 because that width is one WE chose, and the
    seven slots make the point again from the other end: their gaps
    are whatever Data's cut-outs leave, and `frame_build.lay_rail`
    stretches the master's `in_row` divider across each one. So the
    numbers come out on every run and none of them decides anything.

    A gap that is much narrower than the 38 ref px the divider was
    measured at is a STRETCHED rail — visible as a flattened
    moulding, not as a failure — which is exactly the judgement that
    has to be made on the picture rather than in a tool.
    """
    row = [(k, to_ref(r, w_img, h_img)) for k, r in names.items()
           if k in frame_holes.SORT_BOX_KEYS or k == "return"]
    row.sort(key=lambda kv: kv[1][0])
    print(f"          sort row, {len(row)} boxes, gaps as ref px "
          f"(in_row divider measures 38):")
    for (ka, a), (kb, b) in zip(row, row[1:]):
        print(f"            {ka:15s} -> {kb:15s} "
              f"{b[0] - (a[0] + a[2]):6.1f}")
    for key, r in row:
        print(f"            {key:15s} x {r[0]:7.1f} w {r[2]:6.1f} "
              f"y {r[1]:7.1f} h {r[3]:5.1f}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("png", help="a mask or a frame/master PNG")
    ap.add_argument("--holes", choices=CONVENTIONS, default=None,
                    help="force the hole convention instead of finding it")
    args = ap.parse_args()

    lr, _windows = frame_mask.load_reference(frame_mask.REFERENCE)
    arr, how, holes, rows, tried = read(args.png, args.holes)
    h_img, w_img = arr.shape[:2]
    print(f"\n{os.path.abspath(args.png)}\n  {w_img}x{h_img}, "
          f"aspect {w_img / h_img:.5f} "
          f"({'16:9' if abs(w_img / h_img - 16 / 9) < 1e-4 else 'NOT 16:9'})")
    print("  readings tried:")
    for name, why in tried:
        print(f"    {name:6s} {why}")
    if how is None:
        print("\n  No reading of this file lets every rectangle in "
              "layout_reference.json\n  land on a hole of its own. "
              "Nothing below can be measured.\n  Force one with "
              "--holes to see what it does find.")
        return 1
    print(f"  convention: {how}\n")

    names, bad = check_rows(rows, holes, (w_img, h_img))
    if not names:
        return 1
    mask = hole_mask(arr, how)
    bad |= check_rect_alpha(mask, names)
    bad |= check_ring(arr, how, names, (w_img, h_img))
    bad |= check_inset(names, w_img, h_img)
    bad |= check_list(names, w_img, h_img, lr)
    report_sort_rails(names, w_img, h_img)
    print(f"\n{'FAILED' if bad else 'ALL RULES HOLD'} — "
          f"chosen rules are not checked here or in the suite; see the "
          f"suite's report lines for their measured values.\n")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
