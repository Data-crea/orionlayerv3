#!/usr/bin/env python3
"""Extract the 48 galaxy-map nebula sprites from starbg.lbx.

The original stores 12 nebula types x 4 zoom variants in starbg.lbx,
entries 6..53 (entry = type * 4 + zoom + 6, mapgen.cpp
Load_Nebula_Pictures_). Like the star sprites, the four zoom variants
are separate pre-rendered drawings, never scaled at runtime
(mainscr.cpp Draw_Nebulae_ draws at native size).

Zoom variant 3 doubles as the GAMEPLAY geometry: geo.cpp
Point_Is_In_Nebula_N_ maps world coordinates through /3 onto that
sprite's raw pixel grid and treats palette index > 5 as "inside the
nebula". This tool therefore also writes that mask so HD artwork can
be shaped to match it.

Formats implemented from the orion2re source:
  LBX container      vfs_lbx.cpp   (magic 0xFEAD, 510 uint32 offsets)
  animation header   orion2.h      s_animation_header (12 bytes)
  bitmap frames      draw.cpp      Draw_Bitmap_Sprite_ (raw, 0 = alpha)
  packed frames      draw.cpp      Draw_Animated_Sprite_ (RLE runs)
  embedded palette   animate.cpp   Set_Animation_Palette_ (4 B/entry,
                                   6-bit VGA)

Usage:
  python tools/nebula_extract.py                       # search default dirs
  python tools/nebula_extract.py /path/to/starbg.lbx
  python tools/nebula_extract.py --out screens/galaxy_map/assets/nebula_ref

Output (per type t, zoom z):
  <out>/type_<t>/zoom_<z>.png        RGBA sprite (embedded palette or
                                     grayscale-by-index fallback)
  <out>/type_<t>/mask.png            gameplay mask from zoom 3
                                     (white = index > 5, geo.cpp rule)
  <out>/summary.txt                  dimensions, flags, frame counts

Requires: Pillow (pip install pillow --break-system-packages).
"""

import argparse
import os
import struct
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is missing. Run: pip install pillow --break-system-packages")

LBX_MAGIC = 0xFEAD
LBX_OFFSET_COUNT = 510          # vfs_lbx.cpp VFS_LBX_OFFSET_COUNT
NEBULA_FIRST_ENTRY = 6          # mapgen.cpp: type * 4 + frame + 6
NEBULA_TYPES = 12
NEBULA_ZOOMS = 4
GAMEPLAY_ZOOM = 3               # geo.cpp uses variant [3]
GAMEPLAY_THRESHOLD = 5          # geo.cpp: pixel_data[...] > 5

FLAG_DRAW_MODE_MASK = 0x03      # orion2_consts.h
FLAG_HAS_PALETTE = 0x10
DRAW_MODE_ANIMATED = 0
DRAW_MODE_BITMAP = 1

DEFAULT_SEARCH = [
    os.path.expanduser("~/Master of Orion 2"),
    os.path.expanduser("~/Master of Orion 2/DATA"),
    ".",
]


def find_lbx(explicit):
    if explicit:
        if os.path.isfile(explicit):
            return explicit
        sys.exit(f"File not found: {explicit}")
    for d in DEFAULT_SEARCH:
        if not os.path.isdir(d):
            continue
        for name in os.listdir(d):
            if name.lower() == "starbg.lbx":
                return os.path.join(d, name)
    sys.exit("starbg.lbx not found. Pass the path explicitly:\n"
             "  python tools/nebula_extract.py /path/to/starbg.lbx")


def read_entries(path):
    """Return the raw bytes of every LBX entry, per vfs_lbx.cpp."""
    with open(path, "rb") as f:
        data = f.read()
    if len(data) < 8 + 4 * LBX_OFFSET_COUNT:
        sys.exit("File is too small to be an LBX container.")
    entry_count, magic, _header_data = struct.unpack_from("<HHI", data, 0)
    if magic != LBX_MAGIC:
        sys.exit(f"Bad LBX magic 0x{magic:04X} (expected 0xFEAD). "
                 "Is this really starbg.lbx?")
    offsets = struct.unpack_from(f"<{LBX_OFFSET_COUNT}I", data, 8)
    entries = []
    for i in range(entry_count):
        start, end = offsets[i], offsets[i + 1]
        if end < start or end > len(data):
            sys.exit(f"Entry {i}: corrupt offsets {start}..{end}.")
        entries.append(data[start:end])
    return entries


def parse_header(blob, label):
    if len(blob) < 12:
        sys.exit(f"{label}: entry too short for an animation header.")
    width, height, _cur, frame_count, _loop, _key, _unk, flags = \
        struct.unpack_from("<hhhhbbBB", blob, 0)
    if width <= 0 or height <= 0 or frame_count <= 0:
        sys.exit(f"{label}: implausible header "
                 f"(w={width} h={height} frames={frame_count}).")
    frame_offsets = struct.unpack_from(f"<{frame_count + 1}I", blob, 12)
    return width, height, frame_count, flags, frame_offsets


def read_palette(blob, frame_count):
    """Embedded palette per Set_Animation_Palette_: header after the
    frame-offset table, 4 bytes per entry, 6-bit VGA components."""
    pos = 12 + 4 * (frame_count + 1)
    start, count = struct.unpack_from("<hh", blob, pos)
    pos += 4
    palette = {}
    for i in range(count):
        r, g, b, _flag = struct.unpack_from("<BBBB", blob, pos + 4 * i)
        palette[start + i] = (min(r * 4, 255), min(g * 4, 255), min(b * 4, 255))
    return palette


def decode_bitmap(blob, offset, width, height):
    """Raw indexed bitmap, index 0 transparent (Draw_Bitmap_Sprite_)."""
    pixels = blob[offset:offset + width * height]
    if len(pixels) < width * height:
        return None
    return bytearray(pixels)


def decode_packed(blob, offset, width, height):
    """RLE frame per Draw_Animated_Sprite_: 4-byte frame header
    (unknown, start_y), then runs of (pixel_count, skip_count).
    pixel_count == 0 advances skip_count rows; otherwise skip_count
    advances x, pixel_count literal bytes follow, stream padded to
    an even offset."""
    out = bytearray(width * height)
    _unknown, start_y = struct.unpack_from("<HH", blob, offset)
    pos = offset + 4
    y = start_y
    x = 0
    remaining = height - start_y
    while remaining > 0:
        if pos + 4 > len(blob):
            return None
        pixel_count, skip_count = struct.unpack_from("<hh", blob, pos)
        pos += 4
        if pixel_count == 0:
            remaining -= skip_count
            y += skip_count
            x = 0
        else:
            x += skip_count
            run = blob[pos:pos + pixel_count]
            if len(run) < pixel_count or y >= height or x + pixel_count > width:
                return None
            out[y * width + x: y * width + x + pixel_count] = run
            x += pixel_count
            pos += pixel_count
            if (pos - offset) & 1:
                pos += 1
    return out


def to_rgba(pixels, width, height, palette):
    img = Image.new("RGBA", (width, height))
    px = img.load()
    for y in range(height):
        for x in range(width):
            idx = pixels[y * width + x]
            if idx == 0:
                px[x, y] = (0, 0, 0, 0)
            elif idx in palette:
                px[x, y] = (*palette[idx], 255)
            else:
                px[x, y] = (idx, idx, idx, 255)   # grayscale fallback
    return img


#: Anchored to the project, not to the working directory. `--out`
#: defaulted to a bare "nebula_ref" and therefore landed wherever the
#: shell happened to be — for one run, the repository root, where git
#: staged 61 files nobody meant to commit while the smoke test went
#: on reporting the references as absent. The identical fault was
#: fixed in help_extract.py days earlier and not looked for here.
DEFAULT_OUT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "screens", "galaxy_map", "assets", "nebula_ref")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("lbx", nargs="?", help="path to starbg.lbx")
    ap.add_argument("--out", default=DEFAULT_OUT,
                    help="output directory (default: the project's own "
                         "screens/galaxy_map/assets/nebula_ref)")
    args = ap.parse_args()

    path = find_lbx(args.lbx)
    entries = read_entries(path)
    needed = NEBULA_FIRST_ENTRY + NEBULA_TYPES * NEBULA_ZOOMS
    if len(entries) < needed:
        sys.exit(f"{path} has only {len(entries)} entries, "
                 f"{needed} expected. Wrong file version?")

    os.makedirs(args.out, exist_ok=True)
    lines = [f"source: {path}", f"entries: {len(entries)}", ""]
    ok = 0

    for t in range(NEBULA_TYPES):
        type_dir = os.path.join(args.out, f"type_{t:02d}")
        os.makedirs(type_dir, exist_ok=True)
        for z in range(NEBULA_ZOOMS):
            entry_idx = t * NEBULA_ZOOMS + z + NEBULA_FIRST_ENTRY
            label = f"type {t} zoom {z} (entry {entry_idx})"
            blob = entries[entry_idx]
            width, height, frames, flags, offs = parse_header(blob, label)
            palette = (read_palette(blob, frames)
                       if flags & FLAG_HAS_PALETTE else {})
            mode = flags & FLAG_DRAW_MODE_MASK
            if mode == DRAW_MODE_BITMAP:
                pixels = decode_bitmap(blob, offs[0], width, height)
            elif mode == DRAW_MODE_ANIMATED:
                pixels = decode_packed(blob, offs[0], width, height)
            else:
                lines.append(f"{label}: unsupported draw mode {mode} — skipped")
                continue
            if pixels is None:
                lines.append(f"{label}: frame data truncated — skipped")
                continue

            to_rgba(pixels, width, height, palette).save(
                os.path.join(type_dir, f"zoom_{z}.png"))
            lines.append(f"{label}: {width}x{height} frames={frames} "
                         f"flags=0x{flags:02X} palette={len(palette)}")
            ok += 1

            if z == GAMEPLAY_ZOOM:
                mask = Image.new("L", (width, height))
                mask.putdata([255 if p > GAMEPLAY_THRESHOLD else 0
                              for p in pixels])
                mask.save(os.path.join(type_dir, "mask.png"))
                lines.append(f"  gameplay mask written (index > "
                             f"{GAMEPLAY_THRESHOLD}, world/3 grid)")

    summary = os.path.join(args.out, "summary.txt")
    with open(summary, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"{ok}/{NEBULA_TYPES * NEBULA_ZOOMS} sprites extracted to "
          f"{os.path.abspath(args.out)} — details in "
          f"{os.path.abspath(summary)}")
    print("The smoke test's nebula shape and weight assertions read "
          "this directory.")
    if ok < NEBULA_TYPES * NEBULA_ZOOMS:
        print("Some entries were skipped; see summary.txt.")


if __name__ == "__main__":
    main()
