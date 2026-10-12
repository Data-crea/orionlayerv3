#!/usr/bin/env python3
"""The RACEICON reference sheets — pictures for reading by eye.

Split out of `tools/raceicon_extract.py` on 7 September 2026, when
that file went over the 300-line guideline (decision 6). The seam is
one the extractor's own docstring already named and is not a
line-count convenience: **`assets/shared/figures/` is the set the
tree LOADS, and `raceicon_ref/` is a set nothing loads.** These three
functions compose the second kind — a contact sheet of all 171
entries, a labelled 13-column sheet of the block layout, and the grid
both are built on. They answer "is entry 47 the sprite I think it
is", which is a question a person asks once and no code ever asks.

Nothing here decides a file name or knows the block layout: the
labelled sheet is HANDED the race names, the stride and the role
names rather than importing them, so this module cannot become a
second home for the 13-entry layout that `raceicon_extract` and
`colonyfigures` already share.
"""
import os

try:
    from PIL import Image, ImageDraw
except ImportError:  # pragma: no cover - the extractor reports it
    Image = ImageDraw = None

from core import lbx

#: Sheet composition only — how big a cell is drawn and how much
#: room its caption gets. They moved here with the three functions
#: that are their only readers.
SHEET_SCALE = 4
SHEET_PAD = 6
SHEET_LABEL_H = 20
SHEET_NAME_W = 116


def sprite_grid(entries, headers, palette, path, cells, columns,
                pad, label_h, scale=1, name_w=0, row_names=()):
    """Lay sprites out in a grid and write their labels under them.

    Both sheets are this, and they were two copies of it for half a
    day. `cells` is (row, column, entry, [lines]) — the caller owns
    which entry goes where and what it is called, this owns the
    geometry and the compositing. Nothing here decides anything.

    NEAREST only, and only where the caller asks for a scale: these
    are 28 px sprites and smoothing would invent pixels the original
    does not have, which is the one thing a reference picture may not
    do.
    """
    cell_w = scale * max(h.width for h in headers if h) + 2 * pad
    cell_h = scale * max(h.height for h in headers if h) + 2 * pad + label_h
    rows = max(r for r, *_ in cells) + 1
    sheet = Image.new("RGB", (name_w + columns * cell_w, rows * cell_h),
                      (24, 24, 28))
    draw = ImageDraw.Draw(sheet)
    for row, name in enumerate(row_names):
        draw.text((6, row * cell_h + cell_h // 2 - 4), name,
                  fill=(226, 226, 236))
    for row, column, entry, labels in cells:
        x, y = name_w + column * cell_w, row * cell_h
        header = headers[entry] if entry < len(headers) else None
        pixels = (lbx.decode_frame(entries[entry], header, 0)
                  if header is not None else None)
        if pixels is not None:
            sprite = Image.frombytes("RGBA", (header.width, header.height),
                                     lbx.rgba_bytes(pixels, palette))
            if scale != 1:
                sprite = sprite.resize(
                    (sprite.width * scale, sprite.height * scale),
                    Image.NEAREST)
            sheet.paste(sprite, (x + pad, y + pad), sprite)
        for i, text in enumerate(labels):
            draw.text((x + pad, y + cell_h - label_h + 9 * i), text,
                      fill=(210, 210, 220) if i == 0 else (150, 160, 180))
    sheet.save(path)


def contact_sheet(entries, headers, palette, path, columns=16):
    """Every entry with its NUMBER under it, in FILE order.

    The number is the point of the sheet: it is what the block layout
    was checked against, and a sheet of unlabelled figures proves
    nothing about which entry is which. It stays unlabelled by role
    on purpose — checking the layout against a picture that already
    applies it would be circular.
    """
    sprite_grid(entries, headers, palette, path,
                [(i // columns, i % columns, i, [str(i)])
                 for i in range(len(entries))],
                columns, 4, 11)


def labelled_sheet(entries, headers, palette, path,
                   race_names, stride, roles,
                   native_entry, android_entry):
    """One row per race, 13 columns in block order, everything named.

    A different picture from `_contact_sheet.png` and not a
    replacement for it — see there.
    """
    races = min(len(race_names), len(entries) // stride)
    cells = [(race, offset, race * stride + offset, [
                  str(race * stride + offset), role])
             for race in range(races) for offset, role in enumerate(roles)]
    cells += [(races, 0, android_entry, [str(android_entry), "android"]),
              (races, 1, native_entry, [str(native_entry), "native"])]
    names = [f"{race:2d} {race_names[race]}" for race in range(races)]
    sprite_grid(entries, headers, palette, path, cells, len(roles),
                SHEET_PAD, SHEET_LABEL_H, SHEET_SCALE, SHEET_NAME_W,
                names + ["shared"])


def opaque_box(pixels, header):
    """The bounding box of the non-transparent indices, or None.

    Index 0 is the alpha (`Draw_Bitmap_Sprite_`, draw.cpp), so this is
    where the figure actually is inside a canvas that is NOT cropped —
    the canvas is the header's own, so every figure of a race shares
    one origin and the baseline stays where the original puts it.
    Cropping would destroy exactly that, which is why the box is
    REPORTED rather than applied.
    """
    on = [i for i, v in enumerate(pixels) if v]
    if not on:
        return None
    xs, ys = [i % header.width for i in on], [i // header.width for i in on]
    return min(xs), min(ys), max(xs), max(ys)
