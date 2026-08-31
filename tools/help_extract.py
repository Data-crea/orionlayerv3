#!/usr/bin/env python3
"""Extract MOO2's context-help texts from HELP.LBX.

The right-click help that OrionLayer draws in HD is a transcription
of `TEXTBOX::Draw_Help_Entry_` (textbox.cpp:307). The *regions* are in
the orion2re source and live in `screens/<name>/help.json`; the *text*
is not in the source at all. It sits in the game's own HELP.LBX, and
orion2re does not put it on the Extension API — so OrionLayer reads it
the same way `nebula_extract.py` reads STARBG.LBX.

Formats implemented from the orion2re source:
  LBX container    vfs_lbx.cpp    magic 0xFEAD, 510 uint32 offsets
  record array     farload.cpp:90 Farload_Library_Data_ — entry 0
                   begins uint16 total_count, uint16 element_size,
                   then count x element_size records
  s_help_record    orion2.h:1004  1403 bytes, #pragma pack(1),
                   confirmed by sizes.h:73
                   ORION2RE_STATIC_SIZE_ASSERT(s_help_record, 0x57b)

    char     title[80]
    char     anim_lbx[14]
    uint32   anim_info        low 16 bits = LBX record index
    uint8    unknown_0x62
    uint32   next_help_idx    0xFFFFFFFF = the next record follows,
                              0 = end of chain
    char     body[1300]

The chain is walked exactly as `Draw_Help_Entry_` walks it: at most 9
records, stopping when the next index is 0. Chained bodies are joined
with a blank line, which is how they read stacked in the original box.

Language follows `MOX::_settings.language` (textbox.cpp:17):
  0/default HELP.LBX   1 GER_HELP.LBX   2 FRE_HELP.LBX
  3 SPA_HELP.LBX       4 ITA_HELP.LBX

Usage (from the project root):
  python tools/help_extract.py                     # search default dirs
  python tools/help_extract.py --lang de
  python tools/help_extract.py /path/to/HELP.LBX
  python tools/help_extract.py --ids 645,547,288   # print, do not write

Output:
  assets/shared/help/help_<lang>.json

That file is DERIVED from the user's own MOO2 installation and is not
part of the project. Nothing else in the tree changes.
"""

import argparse
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

from core import helpformat  # noqa: E402
from core.helptext import HELP_LBX  # noqa: E402

LBX_MAGIC = 0xFEAD
LBX_OFFSET_COUNT = 510          # vfs_lbx.cpp VFS_LBX_OFFSET_COUNT
HELP_ENTRY = 0                  # textbox.cpp: Far_Reload_Next_Data_(..., 0, ...)
RECORD_SIZE = 0x57B             # sizes.h:73
MAX_CHAIN = 9                   # Draw_Help_Entry_: record_count <= 8
CHAIN_END = 0
CHAIN_NEXT = 0xFFFFFFFF

DEFAULT_SEARCH = [
    os.path.expanduser("~/Master of Orion 2"),
    os.path.expanduser("~/Master of Orion 2/DATA"),
    os.path.expanduser("~/.wine/drive_c/GOG Games/Master of Orion 2"),
    ".",
]

#: Anchored to the project root, not to the working directory. The
#: loader resolves through core.resources, which is rooted at
#: BASE_DIR — so a relative default would write a file nothing reads
#: the moment the tool is run from anywhere but the project root.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(PROJECT_ROOT, "assets", "shared", "help")


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
    looked = "\n  ".join(d for d in DEFAULT_SEARCH)
    sys.exit(f"{filename} not found. Looked in:\n  {looked}\n"
             f"Pass the path explicitly:\n"
             f"  python tools/help_extract.py /path/to/{filename}")


def read_entry(path, index):
    """Raw bytes of one LBX entry, per vfs_lbx.cpp."""
    with open(path, "rb") as f:
        data = f.read()
    if len(data) < 8 + 4 * LBX_OFFSET_COUNT:
        sys.exit("File is too small to be an LBX container.")
    entry_count, magic, _ = struct.unpack_from("<HHI", data, 0)
    if magic != LBX_MAGIC:
        sys.exit(f"Not an LBX file (magic 0x{magic:04X}).")
    if not 0 <= index < entry_count:
        sys.exit(f"Entry {index} is outside the file's {entry_count}.")
    offsets = struct.unpack_from(
        f"<{LBX_OFFSET_COUNT}I", data, 8)
    start, end = offsets[index], offsets[index + 1]
    if not 0 < start <= end <= len(data):
        sys.exit(f"Entry {index} has a bad offset pair "
                 f"({start}, {end}).")
    return data[start:end]


def parse_records(blob):
    """[(title, anim_lbx, anim_idx, next_idx, body)] from entry 0."""
    if len(blob) < 4:
        sys.exit("Help entry is too short to hold a record header.")
    total, element_size = struct.unpack_from("<HH", blob, 0)
    if element_size != RECORD_SIZE:
        sys.exit(f"Record size is {element_size}, expected "
                 f"{RECORD_SIZE} — this is not a help LBX.")
    out = []
    for i in range(total):
        off = 4 + i * element_size
        if off + element_size > len(blob):
            break
        title = cstr(blob[off:off + 80])
        anim_lbx = cstr(blob[off + 80:off + 94])
        anim_info, _pad, next_idx = struct.unpack_from(
            "<IBI", blob, off + 94)
        body = cstr(blob[off + 103:off + 103 + 1300])
        out.append((title, anim_lbx, anim_info & 0xFFFF, next_idx,
                    body))
    return out


def cstr(raw):
    """NUL-terminated MOO2 string -> str (code page 437)."""
    end = raw.find(b"\x00")
    if end >= 0:
        raw = raw[:end]
    return raw.decode("cp437", errors="replace")


def clean(text):
    """Trim the trailing NUL padding, and NOTHING else.

    An earlier version stripped and re-joined lines, which looked
    harmless and was not: MOO2's bodies carry `FMTPARA` control codes
    (\\a sequences, \\r, \\t) and the column positions inside them are
    what makes the Command Points table a table. Decoding is
    `core/helpformat.py`'s job and happens at load time, so a fix
    there needs no re-extraction. The extractor's job is to hand over
    the bytes unharmed.
    """
    return text.rstrip("\x00").rstrip()


def build_entry(records, start):
    """Follow the chain from `start`, exactly like Draw_Help_Entry_."""
    if start >= len(records):
        return None
    idx = start
    titles, bodies, anims = [], [], []
    for _ in range(MAX_CHAIN):
        if idx >= len(records):
            break
        title, anim_lbx, anim_idx, next_idx, body = records[idx]
        titles.append(title)
        bodies.append(clean(body))
        if anim_lbx:
            anims.append({"lbx": anim_lbx, "index": anim_idx})
        idx = idx + 1 if next_idx == CHAIN_NEXT else next_idx
        if idx == CHAIN_END:
            break
    entry = {
        "title": titles[0].strip(),
        # "\f" is the original's own paragraph advance, so chained
        # pages join with the break the engine would have used.
        "body": "\f".join(b for b in bodies if b),
        "pages": len(bodies),
    }
    dropped = helpformat.dropped_functions(entry["body"])
    if dropped:
        # Recorded per entry rather than assumed away: the HD popup
        # honours X and T and drops the rest, and this is how anybody
        # can check what that actually costs.
        entry["dropped_functions"] = dropped
    if anims:
        # Kept as a reference, not rendered. The HD popup draws text
        # only; recording the pointer means the omission stays a
        # decision rather than a loss.
        entry["anim"] = anims
    return entry


def main():
    ap = argparse.ArgumentParser(
        description="Extract MOO2 context-help texts from HELP.LBX.")
    ap.add_argument("lbx", nargs="?",
                    help="path to HELP.LBX (searched if omitted)")
    ap.add_argument("--lang", default="en",
                    choices=sorted(HELP_LBX),
                    help="language, picks the LBX name (default en)")
    ap.add_argument("--out", default=OUT_DIR,
                    help="output directory (default: the project's "
                         "own assets/shared/help)")
    ap.add_argument("--ids",
                    help="comma-separated help ids: print them and "
                         "write nothing")
    args = ap.parse_args()

    filename = HELP_LBX[args.lang]
    path = find_lbx(args.lbx, filename)
    records = parse_records(read_entry(path, HELP_ENTRY))
    print(f"{os.path.basename(path)}: {len(records)} help records")

    if args.ids:
        for raw in args.ids.split(","):
            hid = int(raw.strip())
            entry = build_entry(records, hid)
            print(f"\n=== {hid} =========================")
            if entry is None:
                print("(out of range)")
                continue
            print(entry["title"])
            print("-" * len(entry["title"]))
            print(entry["body"])
        return 0

    entries = {}
    for hid in range(len(records)):
        entry = build_entry(records, hid)
        if entry and (entry["title"] or entry["body"]):
            entries[str(hid)] = entry

    os.makedirs(args.out, exist_ok=True)
    out_path = os.path.join(args.out, f"help_{args.lang}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "_comment": ("GENERATED by tools/help_extract.py from "
                         f"{os.path.basename(path)}. Derived from the "
                         "user's own MOO2 installation — do not edit, "
                         "do not ship. Regenerate after changing the "
                         "game language."),
            "_source": os.path.basename(path),
            "language": args.lang,
            "record_count": len(records),
            "format": 2,
            "entries": entries,
        }, f, ensure_ascii=False, indent=1)
        f.write("\n")

    print(f"wrote {out_path}: {len(entries)} entries")
    print("OrionLayer reads this file on start; restart it to pick "
          "the texts up.")

    # The regions OrionLayer actually uses, checked here so a missing
    # id surfaces at extraction time rather than as an empty popup.
    missing = []
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for screen in ("main_menu", "new_game", "galaxy_map"):
        rp = os.path.join(root, "screens", screen, "help.json")
        if not os.path.exists(rp):
            continue
        with open(rp, encoding="utf-8") as f:
            for region in json.load(f).get("regions", []):
                hid = str(region.get("help_id"))
                if hid not in entries:
                    missing.append(f"{screen}:{hid}")
    if missing:
        print("WARNING: help ids used by a screen but not in this "
              "file: " + ", ".join(missing))
    else:
        print("all help ids used by the HD screens are present")
    return 0


if __name__ == "__main__":
    sys.exit(main())
