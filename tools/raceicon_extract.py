#!/usr/bin/env python3
"""Extract the population figures from the player's RACEICON.LBX.

The colony screens draw one sprite per pop, and which sprite carries
BOTH the profession and the race: `race * 13 + job * 2 (+1)`. This
tool writes those sprites out as PNG so the HD colony summary has the
original to hold its own icons against, and so the colour/tool
mapping rests on more than one framebuffer of one race.

Usage:
  python tools/raceicon_extract.py                   # search default dirs
  python tools/raceicon_extract.py /path/to/RACEICON.LBX
  python tools/raceicon_extract.py --raw-only        # stage 1 only

Output, under `screens/colony_summary/assets/raceicon_ref/`:

  raw/entry_<NNN>/frame_<F>.png       every entry, every frame
  raw/entry_<NNN>/frame_<F>_game.png  the same, in the game's palette
  _contact_sheet.png                  all of them, entry number under
                                      each, in the game's palette
  race_<idx>_<name>/farmer.png        the resting figure
                    farmer_state0.png the unreachable one (see below)
                    worker*, scientist*
  shared/native.png  android.png
  summary.txt                         entry -> file, dimensions,
                                      flags, palette source

**NOTHING HERE IS COMMITTED** (decision 38 and `.gitignore`): it is
extracted from somebody's own copy of the game and is not ours to
ship. The tree must not need it — nothing in `screens/` reads this
directory, and the smoke test passes with it absent.

Requires: Pillow (pip install pillow --break-system-packages).
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import lbx  # noqa: E402

try:
    from PIL import Image, ImageDraw
except ImportError:
    sys.exit("Pillow is missing. Run: pip install pillow --break-system-packages")

#: `enum STOCK_RACE` (orion2_consts.h:444-457), in its own order, with
#: `STOCK_RACE_COUNT == 13` held by a static_assert at line 1379. The
#: names are transcribed from the SOURCE and not from `estrings.lbx`:
#: `MOX::_race_names[]` (estrings.cpp:108-127) holds the LOCALISED
#: display strings, which are a different thing from the identity of
#: race index 3.
RACE_NAMES = ("alkari", "bulrathi", "darlok", "elerian", "gnolam",
              "human", "klackon", "meklar", "mrrshan", "psilon",
              "sakkra", "silicoid", "trilarian")

#: `COLONY::People_Anim_` (colony_main.cpp:444-450) and the three
#: functions that share the same 13-entry stride:
#:
#:   0,1  2,3  4,5   farmer / worker / scientist, `job * 2` with
#:                   `+1` for pop_state 2   People_Anim_
#:   6..10           five military variants  Military_Anims_,
#:                                           colony.cpp:1298
#:   11              spy                     Spy_Anim_, colony.cpp:237
#:   12              race portrait, drawn for a CONQUERED pop
#:                                           Colony_Pop_Icon_,
#:                                           colony.cpp:1285
#:
#: 13 races x 13 + the two shared entries below is 171, which is
#: exactly what the file holds.
RACE_STRIDE = 13
#: `People_Anim_` again: pop_state 3 and 4 ignore the race entirely.
NATIVE_ENTRY = 0xAA
ANDROID_ENTRY = 0xA9

#: (job index, file stem). `ECON_FOOD/INDUSTRY/RESEARCH` are 0/1/2
#: (orion2_consts.h:119-121).
JOBS = ((0, "farmer"), (1, "worker"), (2, "scientist"))

#: **THE RESTING FIGURE IS THE ODD ENTRY OF EACH PAIR.**
#: `People_Anim_` takes `pop_state`, and the only source of that on a
#: colony is `Pop_To_Pop_State_` (colony.cpp:1240-1255), which returns
#: 3 for a native, 4 for an android and **2 for everything else** — it
#: cannot return 0. No caller in the tree passes 0 either: all nine
#: call sites pass 2 or 4. So the `+1` entry is the one the game
#: draws and the even entry is dead in this code.
#:
#: The even ones are written out anyway, as `_state0`, because a
#: reference that silently omits half the file cannot be used to check
#: that the half it kept is the right one. Recorded for the
#: maintainer in `doc/orion2re_open_fixes.md`.
RESTING_STATE, DEAD_STATE = 2, 0

#: The palette these sprites are drawn in. NOT in RACEICON.LBX: all
#: 171 entries have `flags == 0`, so none carries one
#: (`FLAG_HAS_PALETTE`, orion2_consts.h). See `palette_note` for where
#: it does come from and why this file is the right source.
PALETTE_LBX, PALETTE_ENTRY = "COLSUM.LBX", 0
#: The suffix on the coloured set. `_game` and not `_colsum` because
#: the comparison in `palette_note` showed the colours are the same on
#: both colony screens.
COLOUR_SUFFIX = "_game"

DEFAULT_SEARCH = [
    os.path.expanduser("~/Master of Orion 2"),
    os.path.expanduser("~/Master of Orion 2/DATA"),
    ".",
]

#: Anchored to the project and not to the working directory — the
#: fault `nebula_extract.py` and `help_extract.py` each shipped once,
#: where a bare relative default wrote into whatever directory the
#: shell happened to be in, and for one run that was the repository
#: root.
DEFAULT_OUT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "screens", "colony_summary", "assets", "raceicon_ref")


def find_lbx(explicit, filename):
    if explicit:
        if os.path.isfile(explicit):
            return explicit
        sys.exit(f"File not found: {explicit}")
    for d in DEFAULT_SEARCH:
        if not os.path.isdir(d):
            continue
        for name in os.listdir(d):
            if name.lower() == filename.lower():
                return os.path.join(d, name)
    return None


def game_palette(raceicon_path):
    """The palette the colony screens draw these sprites in, or {}.

    It is looked for BESIDE the RACEICON.LBX that was opened, so a
    second installation cannot contribute half of the answer.
    """
    path = os.path.join(os.path.dirname(raceicon_path), PALETTE_LBX)
    if not os.path.isfile(path):
        alt = find_lbx(None, PALETTE_LBX)
        if alt is None:
            return {}, None
        path = alt
    try:
        blob = lbx.read_entries(path)[PALETTE_ENTRY]
        header = lbx.parse_header(blob, PALETTE_LBX)
    except (lbx.LbxError, IndexError):
        return {}, None
    if not header.has_palette:
        return {}, None
    return lbx.read_palette(blob, header.frame_count), path


def palette_note():
    """Why the coloured set is `_game` and not `_colsum`.

    Written into summary.txt so the file carries its own provenance —
    a PNG whose colours came from somewhere else is exactly the kind
    of thing that gets believed later.
    """
    return [
        "palette source: COLSUM.LBX entry 0 via animate::Draw_Palette_",
        "  (colsum.cpp:128-129, inside COLSUM::Colony_Summary_Screen_)",
        "",
        "RACEICON.LBX carries NO palette of its own: all 171 entries",
        "have flags == 0, so FLAG_HAS_PALETTE is set on none of them.",
        "The figures are drawn in whatever the screen last set.",
        "",
        "BOTH COLONY SCREENS WERE COMPARED, and the colours these",
        "sprites use are the same on both:",
        "  - the colony SUMMARY screen loads fonts::Load_Palette_(1,",
        "    0, 255) and then COLSUM.LBX entry 0, which defines all",
        "    256 indices (colsum.cpp:128-129);",
        "  - the colony MAIN screen loads the same font palette and",
        "    then C_Anims_(0) (COLONY::Update_Colony_Palette_,",
        "    colony.cpp:230-235), which is Cache_Load_Planet_ ->",
        "    PLANETS.LBX (colony_main.cpp:474, colony.cpp:201) and",
        "    therefore a DIFFERENT sprite per climate.",
        "",
        "Whole palettes they are not: over their common range the 30",
        "PLANETS.LBX entries differ from COLSUM entry 0 in 78 to 80",
        "of 80 indices, and none of the 30 is identical. But every",
        "one of them declares (start 0, count 80), and the people",
        "sprites use indices 81..239 — not one index in the range a",
        "planet background can touch. Those come from the font",
        "palette, FONTS.LBX entry 2 (fonts.cpp:72-77, palette_id + 1),",
        "on both screens, and COLSUM entry 0 agrees with FONTS entry 2",
        "on ALL 76 indices these sprites use (228 of 256 overall).",
        "",
        "So the suffix is _game: the colours are the base font",
        "palette's, which every screen loads, and not one screen's",
        "private choice.",
    ]


def save(pixels, header, palette, path):
    Image.frombytes("RGBA", (header.width, header.height),
                    lbx.rgba_bytes(pixels, palette)).save(path)


def contact_sheet(entries, headers, palette, path, columns=16):
    """Every entry with its NUMBER under it.

    The number is the point of the sheet: it is what the block layout
    above gets checked against, and a sheet of unlabelled figures
    proves nothing about which entry is which.
    """
    pad, label_h = 4, 11
    cell_w = max(h.width for h in headers if h) + 2 * pad
    cell_h = max(h.height for h in headers if h) + 2 * pad + label_h
    rows = (len(entries) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * cell_w, rows * cell_h), (24, 24, 28))
    draw = ImageDraw.Draw(sheet)
    for i, (blob, header) in enumerate(zip(entries, headers)):
        x, y = (i % columns) * cell_w, (i // columns) * cell_h
        if header is not None:
            pixels = lbx.decode_frame(blob, header, 0)
            if pixels is not None:
                sprite = Image.frombytes(
                    "RGBA", (header.width, header.height),
                    lbx.rgba_bytes(pixels, palette))
                sheet.paste(sprite, (x + pad, y + pad), sprite)
        draw.text((x + pad, y + cell_h - label_h), str(i), fill=(210, 210, 220))
    sheet.save(path)


def dump_raw(entries, headers, palette, out, lines):
    """Stage 1: every entry, every frame, no interpretation."""
    written = 0
    for i, (blob, header) in enumerate(zip(entries, headers)):
        if header is None:
            lines.append(f"entry {i:3d}: not an animation header — skipped")
            continue
        entry_dir = os.path.join(out, "raw", f"entry_{i:03d}")
        os.makedirs(entry_dir, exist_ok=True)
        frames = 0
        for f in range(header.frame_count):
            pixels = lbx.decode_frame(blob, header, f)
            if pixels is None:
                lines.append(f"entry {i:3d} frame {f}: undecodable — skipped")
                continue
            save(pixels, header, {}, os.path.join(entry_dir, f"frame_{f}.png"))
            if palette:
                save(pixels, header, palette,
                     os.path.join(entry_dir,
                                  f"frame_{f}{COLOUR_SUFFIX}.png"))
            frames += 1
            written += 1
        lines.append(f"entry {i:3d}: {header.width}x{header.height} "
                     f"frames={header.frame_count} written={frames} "
                     f"flags=0x{header.flags:02X} "
                     f"palette={'embedded' if header.has_palette else 'none'}")
    return written


def dump_races(entries, headers, palette, out, lines):
    """Stage 2: the block layout, applied."""
    written = 0

    def one(entry, directory, stem):
        nonlocal written
        header = headers[entry]
        if header is None:
            lines.append(f"  entry {entry}: no header, {stem} not written")
            return
        pixels = lbx.decode_frame(entries[entry], header, 0)
        if pixels is None:
            lines.append(f"  entry {entry}: undecodable, {stem} not written")
            return
        os.makedirs(directory, exist_ok=True)
        save(pixels, header, {}, os.path.join(directory, f"{stem}.png"))
        if palette:
            save(pixels, header, palette,
                 os.path.join(directory, f"{stem}{COLOUR_SUFFIX}.png"))
        written += 1
        lines.append(f"  entry {entry:3d} -> "
                     f"{os.path.basename(directory)}/{stem}.png "
                     f"({header.width}x{header.height})")

    races = min(len(RACE_NAMES), len(entries) // RACE_STRIDE)
    for race in range(races):
        directory = os.path.join(out, f"race_{race}_{RACE_NAMES[race]}")
        lines.append(f"race {race} {RACE_NAMES[race]}:")
        for job, stem in JOBS:
            one(race * RACE_STRIDE + job * 2 + 1, directory, stem)
            one(race * RACE_STRIDE + job * 2, directory, f"{stem}_state0")
    shared = os.path.join(out, "shared")
    lines.append("shared (pop_state 3 and 4 ignore the race):")
    one(NATIVE_ENTRY, shared, "native")
    one(ANDROID_ENTRY, shared, "android")
    return written


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("lbx", nargs="?", help="path to RACEICON.LBX")
    ap.add_argument("--out", default=DEFAULT_OUT,
                    help="output directory (default: the project's own "
                         "screens/colony_summary/assets/raceicon_ref)")
    ap.add_argument("--raw-only", action="store_true",
                    help="stage 1 only: the raw dump and the sheet")
    args = ap.parse_args()

    path = find_lbx(args.lbx, "RACEICON.LBX")
    if path is None:
        looked = "\n  ".join(DEFAULT_SEARCH)
        sys.exit(f"RACEICON.LBX not found. Looked in:\n  {looked}\n"
                 f"Pass the path explicitly:\n"
                 f"  python tools/raceicon_extract.py /path/to/RACEICON.LBX")
    try:
        entries = lbx.read_entries(path)
    except lbx.LbxError as exc:
        sys.exit(f"{exc} Is this really RACEICON.LBX?")

    headers = []
    for i, blob in enumerate(entries):
        try:
            headers.append(lbx.parse_header(blob, f"entry {i}"))
        except lbx.LbxError:
            headers.append(None)

    palette, palette_path = game_palette(path)
    os.makedirs(args.out, exist_ok=True)
    lines = [f"source: {path}", f"entries: {len(entries)}", ""]
    lines += palette_note()
    if palette:
        lines.append(f"read from: {palette_path} ({len(palette)} indices)")
    else:
        # A STATE, NOT AN ERROR (decision 38). The grayscale set is
        # complete on its own and says what it is.
        lines.append(f"NOT FOUND beside {os.path.basename(path)} — the "
                     f"coloured set was NOT written. Every PNG here is "
                     f"GRAYSCALE BY PALETTE INDEX: the grey level IS "
                     f"the index and is not a colour.")
    lines.append("")
    lines.append("Every file without the "
                 f"'{COLOUR_SUFFIX}' suffix is grayscale by index.")
    lines.append("")
    lines.append("--- stage 1: raw ---")

    written = dump_raw(entries, headers, palette, args.out, lines)
    contact_sheet(entries, headers, palette,
                  os.path.join(args.out, "_contact_sheet.png"))
    lines.append("")
    lines.append("_contact_sheet.png: every entry with its number, in "
                 + ("the game palette." if palette else "grayscale."))

    if not args.raw_only:
        lines.append("")
        lines.append("--- stage 2: per race ---")
        lines.append("block layout, People_Anim_ (colony_main.cpp:444-450), "
                     "Military_Anims_ (colony.cpp:1298), Spy_Anim_ "
                     "(colony.cpp:237), Colony_Pop_Icon_ (colony.cpp:1285):")
        lines.append("  race * 13 + 0,1 farmer  2,3 worker  4,5 scientist")
        lines.append("             + 6..10 military  11 spy  12 portrait")
        lines.append("  0xAA native, 0xA9 android — both race-independent")
        lines.append("names: enum STOCK_RACE, orion2_consts.h:444-457")
        lines.append("the ODD entry of each pair is the one the game draws: "
                     "Pop_To_Pop_State_ (colony.cpp:1240-1255) cannot "
                     "return 0, so _state0 is unreachable in this code")
        written += dump_races(entries, headers, palette, args.out, lines)

    summary = os.path.join(args.out, "summary.txt")
    with open(summary, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"{written} PNGs written to {os.path.abspath(args.out)} — "
          f"details in {os.path.abspath(summary)}")
    if not palette:
        print(f"No {PALETTE_LBX} beside the LBX: everything is grayscale "
              f"by palette index. See summary.txt.")
    print("Nothing in the tree reads this directory; it is a reference "
          "and it is not committed (.gitignore).")


if __name__ == "__main__":
    main()
