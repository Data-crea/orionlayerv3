#!/usr/bin/env python3
"""Generate the HD galaxy-map nebula sprites from the extracted originals.

Input is the reference set written by tools/nebula_extract.py: 12 types
x 4 zoom variants, stored as grayscale-by-index PNGs (STARBG.LBX has no
embedded palettes, so each pixel's gray value IS its palette index).

Colors come from the same place the game takes them: the galaxy map
calls fonts::Load_Palette_(0, 0, 255) (mainscr.cpp:1208), which loads
FONTS.LBX entry 1 — an array of 4-byte entries with 6-bit VGA
components. This tool reads that entry directly from FONTS.LBX.

NOTE, 30 August 2026: THE OUTPUT LAYOUT IS NO LONGER WHAT THE GAME
LOADS. This tool writes type_NN/zoom_N.png — four pre-rendered
variants per type — which is what the renderer wanted while the
footprint still came from the artwork. It now takes the footprint
from zoomtables.NEBULA_DIM and loads ONE master per type as
assets/nebula/type_NN.png, scaling it per zoom. Point --out somewhere
scratch and flatten by hand until this is fixed; writing straight
into assets/nebula would leave twelve directories the screen ignores.

Output follows the star-sprite principle (status decision #27): one
pre-rendered drawing per zoom variant, never scaled at runtime. Each
variant is rendered at HD_SCALE x its original pixel size (default 3,
matching 1920x1080 vs 640x480). The silhouette is kept true to the
original because zoom variant 3 doubles as the gameplay mask
(geo.cpp Point_Is_In_Nebula_N_) — detail is added inside the shape,
the outline only frays inward, never outward.

Usage:
  python tools/make_nebula_icons.py \
      --ref screens/galaxy_map/assets/nebula_ref \
      --fonts "$HOME/Master of Orion 2/FONTS.LBX" \
      --out screens/galaxy_map/assets/nebula

  Options:
    --scale N       HD scale factor (default 3)
    --sheet         also write a preview sheet (all types, zoom 0)
    --recolor-ref   additionally rewrite the reference PNGs in true
                    color (originals at 1x, useful for comparison)

Requires: numpy, Pillow.
"""

import argparse
import os
import struct
import sys

try:
    import numpy as np
    from PIL import Image
except ImportError as e:
    sys.exit(f"Missing dependency ({e.name}). "
             "Run: pip install numpy pillow --break-system-packages")

LBX_MAGIC = 0xFEAD
LBX_OFFSET_COUNT = 510
FONTS_PALETTE_ENTRY = 1     # fonts.cpp Load_Palette_: palette_id 0 -> entry 1
NEBULA_TYPES = 12
NEBULA_ZOOMS = 4
DEFAULT_SCALE = 3           # 1920x1080 HD reference vs 640x480 original
EDGE_LOW, EDGE_HIGH = 0.05, 0.95   # alpha band treated as "edge" for fraying


# ---------------------------------------------------------------- palette

def read_lbx_entry(path, entry_idx):
    with open(path, "rb") as f:
        data = f.read()
    if len(data) < 8 + 4 * LBX_OFFSET_COUNT:
        sys.exit(f"{path}: too small to be an LBX container.")
    entry_count, magic, _ = struct.unpack_from("<HHI", data, 0)
    if magic != LBX_MAGIC:
        sys.exit(f"{path}: bad LBX magic 0x{magic:04X}.")
    if entry_idx >= entry_count:
        sys.exit(f"{path}: entry {entry_idx} out of range ({entry_count}).")
    offsets = struct.unpack_from(f"<{LBX_OFFSET_COUNT}I", data, 8)
    return data[offsets[entry_idx]:offsets[entry_idx + 1]]


def load_game_palette(fonts_path):
    """FONTS.LBX entry 1: s_palette_entry[256], 4 bytes each, 6-bit VGA."""
    blob = read_lbx_entry(fonts_path, FONTS_PALETTE_ENTRY)
    if len(blob) < 256 * 4:
        sys.exit(f"{fonts_path}: palette entry is only {len(blob)} bytes, "
                 "1024 expected.")
    raw = np.frombuffer(blob[:256 * 4], dtype=np.uint8).reshape(256, 4)
    pal = np.minimum(raw[:, :3].astype(np.uint16) * 4, 255).astype(np.uint8)
    return pal  # (256, 3) RGB 0..255


# ---------------------------------------------------------------- helpers

def resize(arr, w, h, mode=Image.BICUBIC):
    return np.asarray(Image.fromarray(arr).resize((w, h), mode))


def value_noise(w, h, cell, rng):
    """One octave of smooth value noise in [0, 1]."""
    gw, gh = max(2, w // cell + 2), max(2, h // cell + 2)
    grid = rng.random((gh, gw)).astype(np.float32)
    return resize(grid, w, h, Image.BICUBIC).clip(0.0, 1.0)


def fractal_noise(w, h, base_cell, octaves, rng):
    total = np.zeros((h, w), dtype=np.float32)
    amp, amp_sum, cell = 1.0, 0.0, base_cell
    for _ in range(octaves):
        total += amp * value_noise(w, h, max(2, cell), rng)
        amp_sum += amp
        amp *= 0.5
        cell = max(2, cell // 2)
    return total / amp_sum


# ---------------------------------------------------------------- render

def load_index_image(path):
    """Reference PNG back to (index array, alpha array). The extractor
    wrote gray == palette index and alpha 0 for index 0."""
    img = np.asarray(Image.open(path).convert("RGBA"))
    idx = img[..., 0].astype(np.uint8).copy()
    idx[img[..., 3] == 0] = 0
    return idx


def render_hd(idx, palette, scale, seed):
    """One HD nebula from one original index image."""
    h, w = idx.shape
    hd_w, hd_h = w * scale, h * scale
    rng = np.random.default_rng(seed)

    rgb = palette[idx].astype(np.float32) / 255.0          # (h, w, 3)
    alpha = (idx > 0).astype(np.float32)

    # Smooth upscale of color and coverage.
    rgb_hd = np.stack(
        [resize(rgb[..., c], hd_w, hd_h) for c in range(3)], axis=-1
    ).clip(0.0, 1.0)
    alpha_hd = resize(alpha, hd_w, hd_h).clip(0.0, 1.0)

    # Never grow past the original silhouette (bicubic overshoot):
    # bilinear coverage of the binary mask bounds the shape.
    bound = resize(alpha, hd_w, hd_h, Image.BILINEAR).clip(0.0, 1.0)
    alpha_hd = np.minimum(alpha_hd, bound)

    # Gas texture: brightness modulation inside the body.
    detail = fractal_noise(hd_w, hd_h, base_cell=10 * scale, octaves=3,
                           rng=rng)
    luminance_mod = 1.0 + 0.28 * (detail - 0.5)
    rgb_hd = (rgb_hd * luminance_mod[..., None]).clip(0.0, 1.0)

    # Fray the outline inward: only where the upscaled alpha is already
    # partial does noise thin it further. Solid interior and empty
    # exterior are untouched, so the silhouette matches the original.
    edge = (alpha_hd > EDGE_LOW) & (alpha_hd < EDGE_HIGH)
    fray = fractal_noise(hd_w, hd_h, base_cell=3 * scale, octaves=2, rng=rng)
    alpha_hd = np.where(edge, alpha_hd * (0.55 + 0.45 * fray), alpha_hd)

    # Slight translucency so stars shimmer through, as in the original
    # (indices are drawn opaque there, but over the black starfield the
    # dark tones read as thin gas; keep dark areas more transparent).
    lum = rgb_hd.mean(axis=-1)
    alpha_hd = alpha_hd * (0.55 + 0.45 * np.sqrt(lum.clip(0, 1)))

    out = np.empty((hd_h, hd_w, 4), dtype=np.uint8)
    out[..., :3] = (rgb_hd * 255.0 + 0.5).astype(np.uint8)
    out[..., 3] = (alpha_hd * 255.0 + 0.5).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def recolor_reference(idx, palette):
    rgb = palette[idx]
    out = np.zeros((*idx.shape, 4), dtype=np.uint8)
    out[..., :3] = rgb
    out[..., 3] = np.where(idx > 0, 255, 0)
    return Image.fromarray(out, "RGBA")


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ref", required=True,
                    help="nebula_ref directory from nebula_extract.py")
    ap.add_argument("--fonts", required=True, help="path to FONTS.LBX")
    ap.add_argument("--out", required=True, help="output directory")
    ap.add_argument("--scale", type=int, default=DEFAULT_SCALE)
    ap.add_argument("--sheet", action="store_true")
    ap.add_argument("--recolor-ref", action="store_true")
    args = ap.parse_args()

    if not os.path.isfile(args.fonts):
        sys.exit(f"FONTS.LBX not found: {args.fonts}\n"
                 "Hint: find ~ -iname 'fonts.lbx'")
    palette = load_game_palette(args.fonts)

    made, previews = 0, []
    for t in range(NEBULA_TYPES):
        out_dir = os.path.join(args.out, f"type_{t:02d}")
        os.makedirs(out_dir, exist_ok=True)
        for z in range(NEBULA_ZOOMS):
            src = os.path.join(args.ref, f"type_{t:02d}", f"zoom_{z}.png")
            if not os.path.isfile(src):
                print(f"missing reference {src} — skipped")
                continue
            idx = load_index_image(src)
            hd = render_hd(idx, palette, args.scale, seed=1000 * t + z)
            hd.save(os.path.join(out_dir, f"zoom_{z}.png"))
            made += 1
            if z == 0:
                previews.append((t, hd))
            if args.recolor_ref:
                recolor_reference(idx, palette).save(
                    os.path.join(args.ref, f"type_{t:02d}",
                                 f"zoom_{z}_color.png"))

    if args.sheet and previews:
        cols = 4
        rows = (len(previews) + cols - 1) // cols
        cell = max(max(p.size) for _, p in previews) + 16
        sheet = Image.new("RGBA", (cols * cell, rows * cell), (8, 8, 16, 255))
        for i, (t, p) in enumerate(previews):
            x = (i % cols) * cell + (cell - p.width) // 2
            y = (i // cols) * cell + (cell - p.height) // 2
            sheet.alpha_composite(p, (x, y))
        sheet_path = os.path.join(args.out, "preview_sheet.png")
        sheet.save(sheet_path)
        print(f"preview sheet: {sheet_path}")

    print(f"{made}/{NEBULA_TYPES * NEBULA_ZOOMS} HD nebulas written to "
          f"{args.out}/ at {args.scale}x")


if __name__ == "__main__":
    main()
