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

It also writes the BASE FIGURE SET the screens actually draw, into
`assets/shared/figures/` — 54 masters at 28x28, named the way a mod
names them (decision 50). That directory is the only output anything
in `screens/` opens; everything under `raceicon_ref/` is a reference
for reading by eye.

**NOTHING HERE IS COMMITTED** (decisions 38, 40, 42 and `.gitignore`):
both outputs are extracted from somebody's own copy of the game and
are not ours to ship. The tree must not need either — the smoke test
passes with both absent, and the colony summary falls back to its
coloured cells and names this command.

Requires: Pillow (pip install pillow --break-system-packages).
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import lbx  # noqa: E402
from tools.raceicon_sheets import (  # noqa: E402
    SHEET_SCALE, contact_sheet, labelled_sheet, opaque_box, sprite_grid)
from core.config import BASE_DIR  # noqa: E402
from screens.colony_summary import colonyfigures as figures  # noqa: E402

#: The loader's own constants, imported and never repeated here.
FIGURE_DIR = figures.FIGURE_DIR
MASTER_SIZE = figures.MASTER_SIZE

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






#: The labelled sheet's scale, its padding and the width of the
#: race-name column at the start of each row.




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


def dump_base_set(entries, headers, palette, lines):
    """The 54 figures the colony screens actually draw, under
    `assets/shared/figures/`, named the way a MOD names them.

    **THIS IS THE ONLY STAGE THE TREE READS.** The three stages above
    are a reference for reading by eye — numbered dumps, contact
    sheets, per-race directories — and nothing in `screens/` opens
    any of them. This one writes the file names
    `screens/colony_summary/colonyfigures.py` resolves and a mod
    overrides, one PNG at a time (decision 50).

    THE NAMES COME FROM THE LOADER'S OWN TABLE, imported rather than
    repeated. A second list of 54 names here would be a second home
    for the mod convention, and `doc/modding_figures.md` is generated
    from that same table — three copies of a naming rule is how the
    screen-ID map went wrong.

    Only entries the SCREEN can draw are written: the three job
    sprites at `pop_state == 2` (the ODD entry of each pair, since
    `Pop_To_Pop_State_` cannot return 0), the race portrait for a
    conquered pop, and the two race-independent sprites. Military,
    spy and the unreachable `_state0` half stay in the reference
    dumps, where they are useful, and out of the set the game loads.
    """
    if not palette:
        lines.append(f"{FIGURE_DIR}/: NOT written — no game palette. "
                     f"The screen would draw grayscale figures, which "
                     f"is worse than the coloured cells it falls back "
                     f"to.")
        return 0
    directory = os.path.join(BASE_DIR, FIGURE_DIR)
    os.makedirs(directory, exist_ok=True)
    written = 0
    for entry, name in base_set_entries():
        header = headers[entry] if entry < len(headers) else None
        pixels = (lbx.decode_frame(entries[entry], header, 0)
                  if header is not None else None)
        if pixels is None:
            lines.append(f"  entry {entry:3d}: no figure, {name} not "
                         f"written")
            continue
        if (header.width, header.height) != (MASTER_SIZE, MASTER_SIZE):
            # REFUSED, NOT RESIZED. The loader refuses a wrong-sized
            # mod file for the same reason and with the same words:
            # a figure one step out of line with its neighbours reads
            # as a rendering fault, not as a bad file.
            lines.append(f"  entry {entry:3d}: {header.width}x"
                         f"{header.height}, not {MASTER_SIZE}x"
                         f"{MASTER_SIZE} — {name} not written")
            continue
        save(pixels, header, palette, os.path.join(directory, name))
        lines.append(f"  entry {entry:3d} -> {FIGURE_DIR}/{name}")
        written += 1
    return written


def base_set_entries():
    """(RACEICON entry, file name) for the 54, in the loader's order.

    The entry arithmetic is `People_Anim_` and `Colony_Pop_Icon_`
    (colony_main.cpp:444-450, colony.cpp:1285) — `race * 13 + job * 2
    + 1` for a job at pop_state 2 and `race * 13 + 12` for the
    portrait — computed here from RACE_STRIDE rather than tabulated,
    so it cannot disagree with the block layout above it.
    """
    for race, _key in enumerate(figures.RACE_KEYS):
        for job, _role in enumerate(figures.ROLE_KEYS):
            yield race * RACE_STRIDE + job * 2 + 1, \
                figures.master_name(race=race, role=job)
        yield race * RACE_STRIDE + 12, \
            figures.master_name(race=race, portrait=True)
    yield NATIVE_ENTRY, figures.master_name(shared=figures.NATIVE)
    yield ANDROID_ENTRY, figures.master_name(shared=figures.ANDROID)


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
                       os.path.join(args.out, "_labelled_sheet.png"),
                       RACE_NAMES, RACE_STRIDE, ROLES,
                       NATIVE_ENTRY, ANDROID_ENTRY)
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
        lines += ["", "--- stage 3: the base set the SCREEN reads ---"]
        lines.append(f"written to {FIGURE_DIR}/ — this is the ONLY stage "
                     f"anything in screens/ loads. Everything above is a "
                     f"reference for reading by eye.")
        lines.append("masters at 28x28, 1x. The STEP is made in the "
                     "loader (colonyfigures.py), not here: a mod ships a "
                     "28x28 master and it must arrive at the same size as "
                     "the base figure it replaces, so there is one path "
                     "to the stepped pixel and not two (decision 5).")
        written += dump_base_set(entries, headers, palette, lines)

    summary = os.path.join(args.out, "summary.txt")
    with open(summary, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"{written} PNGs written to {os.path.abspath(args.out)} — "
          f"details in {os.path.abspath(summary)}")
    if not palette:
        print(f"No {PALETTE_LBX} beside the LBX: everything is grayscale "
              f"by palette index. See summary.txt.")
    print(f"raceicon_ref/ is a reference and nothing in the tree reads "
          f"it. {FIGURE_DIR}/ IS read — by the colony summary, one file "
          f"at a time. Neither is committed (.gitignore).")
    print("OrionLayer reads the figures on start; restart it to pick "
          "them up.")


if __name__ == "__main__":
    main()
