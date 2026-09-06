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
  figures/e<NNN>_<race>_<role>_game.png   every entry ONCE, named by
                                      the block layout, uncropped, 1x
  _labelled_sheet.png                 the block layout as a picture:
                                      one row per race, 13 columns
  summary.txt                         entry -> file, dimensions,
                                      flags, palette source

`figures/` and the per-race directories overlap on purpose and answer
different questions. The directories answer "what does a Sakkra
scientist look like" and hold six files; `figures/` answers "what IS
entry 47", which is the question the 13-entry block raises and which
neither the raw dump (numbered and nothing else) nor the directories
(the six people entries only) can answer.

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

#: The 13 offsets of a race block, named. Same four citations as
#: `RACE_STRIDE` above — this is that comment turned into data so the
#: figure files can be labelled without a second reading of it.
#:
#: The military variants are numbered 1..5 and not 0..4 because
#: `Military_Anims_(variant, race)` (colony.cpp:1298) is reached
#: through `Military_Anim_` (colony.cpp:1309-1330), which picks
#: variant 0 for militia, 1 or 2 for troops depending on Powered
#: Armor and 3 or 4 for the second class depending on Battleoids. A
#: file called `military_0` would read as "the first one" where the
#: source's 0 is a specific thing; 1..5 counts files, which is what a
#: file name can honestly do.
#:
#: **THE `_state0` HALF IS DEAD IN THIS CODE.** `People_Anim_` takes
#: `pop_state`, and the only source of it on a colony is
#: `Pop_To_Pop_State_` (colony.cpp:1240-1255), which returns 3, 4 or
#: 2 and cannot return 0; no call site passes 0 either. The even
#: entry of each pair is therefore never drawn. It is extracted
#: anyway, because a reference that silently omits half the file
#: cannot be used to check that the half it kept is the right one.
#: Recorded for the maintainer in `doc/orion2re_open_fixes.md`.
ROLES = ("farmer_state0", "farmer", "worker_state0", "worker",
         "scientist_state0", "scientist",
         "military_1", "military_2", "military_3", "military_4",
         "military_5", "spy", "portrait")

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
    """Where the colours come from, written into summary.txt.

    A PNG whose colours came from somewhere else is exactly the kind
    of thing that gets believed later, so the extracted files carry
    their own provenance — they travel without this repository.

    SHORT ON PURPOSE. The full comparison of the two colony screens'
    palettes lives in `v3_projektstatus.md` under "The population
    figures come out of RACEICON.LBX"; repeating it here would be a
    second copy of a finding, which is what goes stale.
    """
    return [
        "palette source: COLSUM.LBX entry 0 via animate::Draw_Palette_",
        "  (colsum.cpp:128-129, in COLSUM::Colony_Summary_Screen_)",
        "RACEICON.LBX carries none: all 171 entries have flags == 0, so",
        "FLAG_HAS_PALETTE is set on none. The figures are drawn in",
        "whatever the screen last set, and both colony screens set the",
        "same colours over the indices these sprites use (81..239).",
        "Suffix _game, not _colsum, for that reason.",
    ]


def save(pixels, header, palette, path):
    Image.frombytes("RGBA", (header.width, header.height),
                    lbx.rgba_bytes(pixels, palette)).save(path)


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


#: The labelled sheet's scale, its padding and the width of the
#: race-name column at the start of each row.
SHEET_SCALE = 4
SHEET_PAD = 6
SHEET_LABEL_H = 20
SHEET_NAME_W = 116


def labelled_sheet(entries, headers, palette, path):
    """One row per race, 13 columns in block order, everything named.

    A different picture from `_contact_sheet.png` and not a
    replacement for it — see there.
    """
    races = min(len(RACE_NAMES), len(entries) // RACE_STRIDE)
    cells = [(race, offset, race * RACE_STRIDE + offset, [
                  str(race * RACE_STRIDE + offset), role])
             for race in range(races) for offset, role in enumerate(ROLES)]
    cells += [(races, 0, ANDROID_ENTRY, [str(ANDROID_ENTRY), "android"]),
              (races, 1, NATIVE_ENTRY, [str(NATIVE_ENTRY), "native"])]
    names = [f"{race:2d} {RACE_NAMES[race]}" for race in range(races)]
    sprite_grid(entries, headers, palette, path, cells, len(ROLES),
                SHEET_PAD, SHEET_LABEL_H, SHEET_SCALE, SHEET_NAME_W,
                names + ["shared"])


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


def write_figure(entries, headers, palette, directory, stem, entry,
                 lines, grayscale, note=""):
    """One entry to one PNG (two, with the grayscale set), or a line
    saying why not. Both dumps below go through it, so they cannot
    drift apart about what an undecodable entry does."""
    header = headers[entry] if entry < len(headers) else None
    pixels = (lbx.decode_frame(entries[entry], header, 0)
              if header is not None else None)
    if pixels is None:
        lines.append(f"  entry {entry}: no figure, {stem} not written")
        return 0
    os.makedirs(directory, exist_ok=True)
    if grayscale:
        save(pixels, header, {}, os.path.join(directory, f"{stem}.png"))
    if palette:
        save(pixels, header, palette,
             os.path.join(directory, f"{stem}{COLOUR_SUFFIX}.png"))
    # THE LINE NAMES THE FILE THAT EXISTS. It said `<stem>.png` for
    # every entry until the figures dump, which writes only the
    # coloured one — so summary.txt pointed at 171 files that were
    # never written. A summary is a claim about the directory.
    written_stem = stem if grayscale else stem + COLOUR_SUFFIX
    lines.append(f"  entry {entry:3d} -> {os.path.basename(directory)}/"
                 f"{written_stem}.png ({header.width}x{header.height})"
                 f"{note}")
    return 1


def dump_races(entries, headers, palette, out, lines):
    """Stage 2: the block layout, applied — six people files per race
    plus the two shared ones, under readable directory names."""
    written = 0
    races = min(len(RACE_NAMES), len(entries) // RACE_STRIDE)
    for race in range(races):
        directory = os.path.join(out, f"race_{race}_{RACE_NAMES[race]}")
        lines.append(f"race {race} {RACE_NAMES[race]}:")
        for job, stem in JOBS:
            for offset, suffix in ((1, ""), (0, "_state0")):
                written += write_figure(
                    entries, headers, palette, directory, stem + suffix,
                    race * RACE_STRIDE + job * 2 + offset, lines, True)
    shared = os.path.join(out, "shared")
    lines.append("shared (pop_state 3 and 4 ignore the race):")
    written += write_figure(entries, headers, palette, shared, "native",
                            NATIVE_ENTRY, lines, True)
    written += write_figure(entries, headers, palette, shared, "android",
                            ANDROID_ENTRY, lines, True)
    return written


def figure_name(entry):
    """(race stem, role) for one entry, or None if it is neither.

    `race<II>_<name>` matches the per-race directories' `<idx>_<name>`
    with the index zero-padded, so a directory listing of `figures/`
    sorts into block order by itself.
    """
    if entry == NATIVE_ENTRY:
        return "shared", "native"
    if entry == ANDROID_ENTRY:
        return "shared", "android"
    race, offset = divmod(entry, RACE_STRIDE)
    if race < len(RACE_NAMES) and offset < len(ROLES):
        return f"race{race:02d}_{RACE_NAMES[race]}", ROLES[offset]
    return None


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


def dump_figures(entries, headers, palette, out, lines):
    """One labelled PNG per entry, in the game palette.

    Uncropped and 1x. The per-race directories answer "what does a
    farmer look like"; this answers "what is entry 47", which is the
    question the 13-entry block raises and which the raw dump cannot
    answer because its files are numbered and nothing else.
    """
    if not palette:
        lines.append("figures/: NOT written — no game palette, and the "
                     "file names claim one (see above).")
        return 0
    directory = os.path.join(out, "figures")
    written = 0
    for entry, header in enumerate(headers):
        named = figure_name(entry)
        if header is None or named is None:
            continue
        pixels = lbx.decode_frame(entries[entry], header, 0)
        box = opaque_box(pixels, header) if pixels is not None else None
        written += write_figure(
            entries, headers, palette, directory,
            f"e{entry:03d}_{named[0]}_{named[1]}", entry, lines, False,
            f"  {named[1]}  opaque {box if box else 'none'}")
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
    lines += ["", f"Every file without the '{COLOUR_SUFFIX}' suffix is "
              "grayscale by index.", "", "--- stage 1: raw ---"]

    written = dump_raw(entries, headers, palette, args.out, lines)
    contact_sheet(entries, headers, palette,
                  os.path.join(args.out, "_contact_sheet.png"))
    lines += ["", "_contact_sheet.png: every entry with its number, in "
              + ("the game palette." if palette else "grayscale.")]

    if palette:
        labelled_sheet(entries, headers, palette,
                       os.path.join(args.out, "_labelled_sheet.png"))
        lines.append("_labelled_sheet.png: one row per race, the 13 block "
                     "offsets across, entry number and role under each, "
                     f"{SHEET_SCALE}x nearest-neighbour.")
    else:
        lines.append("_labelled_sheet.png: NOT written — it is the game "
                     "palette's picture and there is no palette.")

    if not args.raw_only:
        lines += ["", "--- stage 2: per race ---"]
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
        lines += ["", "--- stage 2: one labelled file per entry ---"]
        lines.append("uncropped: the canvas is the animation header's own, "
                     "so every figure of a race shares one origin and the "
                     "baseline stays where the original puts it. The "
                     "opaque box below is where the ink is inside it.")
        written += dump_figures(entries, headers, palette, args.out, lines)

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
