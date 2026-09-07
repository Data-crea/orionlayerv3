#!/usr/bin/env python3
"""Extract the original's building names from the user's TECHNAME.LBX.

    python tools/techname_extract.py
    python tools/techname_extract.py --lang de --lbx /path/to/TECHNAME.LBX

**THE HELP-TEXT PATTERN, EXACTLY** (decision 38). The names are not in
the orion2re source — they are in the player's own installation — so
they are extracted here, written to a derived file that is never
committed, and DECODED AT LOAD TIME by `core/buildnames.py`. The
bytes are moved untouched: this tool splits the block into strings
and writes them, and every question about what a string MEANS is
answered on the other side, so a fix there needs no re-extraction.
The file carries a format version, because a body an older extractor
wrote renders almost right, which is worse than not loading at all.

WHAT IT READS. `TECHINIT::Load_Tech_Names_` (techinit.cpp:43) loads
ONE entry of `techname.lbx` — the index is `MOX::_settings.language`
— as a contiguous block of NUL-separated strings, and walks it with
`Advance_To_Next_String_` (techinit.cpp:11-21): skip to the next NUL,
then skip every NUL after it. The order is fixed:

    string 0             _technology_fields[0]
    1 .. 82              _technology_fields[1 .. 82]
    83 .. 294            _technology_applications[0 .. 211]
    295 .. 343           _buildings[0 .. 48]
    then specials, armor, shields, weapons, ...

so building `id` is string `BUILDING_FIRST_STRING + id`. The offset is
COMPUTED from `orion2_consts.h`'s own counts (TECH_FIELD_COUNT 83,
TECH_APP_COUNT 212, BUILDING_COUNT 49, each with a static_assert
beside it) and not measured off the file — which is what makes it a
transcription rather than a guess that happens to line up.

**GENERATED, NEVER COMMITTED** (decisions 38, 40, 42). It is the
user's game data. `tools/setup.py` names the command when the file is
absent, and the colony screen says so on the BUILDING column rather
than drawing nothing.

Requires nothing beyond the standard library and `core/lbx.py`.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import lbx  # noqa: E402
from core.buildnames import (  # noqa: E402
    BUILDING_COUNT, BUILDING_FIRST_STRING, FORMAT_VERSION, name_file)
from core.config import BASE_DIR, load_settings  # noqa: E402

#: The language index `Load_Tech_Names_` passes as the entry number,
#: in `MOX::_settings.language`'s own order (English, German, French,
#: Spanish, Italian — the same list `mox2.cpp`'s error strings use).
LANGUAGES = {"en": 0, "de": 1, "fr": 2, "es": 3, "it": 4}

DEFAULT_LBX = os.path.expanduser("~/Master of Orion 2/TECHNAME.LBX")


def split_block(blob):
    """The block's strings, in `Advance_To_Next_String_`'s order.

    Transcribed rather than paraphrased: skip to the next NUL, then
    skip every NUL after it. A run of NULs is ONE separator, which is
    why a plain `split(b"\\x00")` would produce empty strings the
    original never counts and shift every index after the first run.
    """
    out = []
    offset = 0
    size = len(blob)
    while offset < size:
        end = offset
        while end < size and blob[end] != 0:
            end += 1
        out.append(blob[offset:end])
        while end < size and blob[end] == 0:
            end += 1
        offset = end
    return out


def decode(raw):
    """One string, as the game's own 8-bit text.

    cp437 rather than utf-8: the LBX predates unicode and the accented
    forms in the French and Spanish blocks are code-page bytes. Errors
    are replaced rather than raised — a tool that dies on one odd byte
    takes the other 300 names with it.
    """
    return raw.decode("cp437", errors="replace").strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--lbx", default=DEFAULT_LBX)
    parser.add_argument("--lang", default=None,
                        help="language code; default: settings.json")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    lang = args.lang or load_settings().get("language", "en")
    if lang not in LANGUAGES:
        sys.exit(f"unknown language {lang!r}; known: {sorted(LANGUAGES)}")
    if not os.path.exists(args.lbx):
        sys.exit(f"{args.lbx} not found. Point --lbx at your own "
                 f"installation's TECHNAME.LBX.")

    blob = lbx.read_entry(args.lbx, LANGUAGES[lang])
    strings = split_block(blob)
    need = BUILDING_FIRST_STRING + BUILDING_COUNT
    if len(strings) < need:
        sys.exit(f"{args.lbx} entry {LANGUAGES[lang]} holds "
                 f"{len(strings)} strings; the walk needs at least "
                 f"{need} to reach the last building. Wrong entry, or "
                 f"a file this tool does not understand — nothing "
                 f"written.")

    buildings = {}
    for index in range(BUILDING_COUNT):
        text = decode(strings[BUILDING_FIRST_STRING + index])
        if text:
            buildings[str(index)] = text

    out_dir = args.out or os.path.join(BASE_DIR, "assets", "shared", "names")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, os.path.basename(name_file(lang)))
    with open(path, "w", encoding="utf-8") as handle:
        json.dump({
            "_comment": ("GENERATED by tools/techname_extract.py from "
                         f"{os.path.basename(args.lbx)}. Derived from "
                         "the user's own MOO2 installation — do not "
                         "edit, do not ship. Regenerate after changing "
                         "the game language."),
            "_source": os.path.basename(args.lbx),
            "language": lang,
            "entry": LANGUAGES[lang],
            "strings_in_block": len(strings),
            "format": FORMAT_VERSION,
            "buildings": buildings,
        }, handle, ensure_ascii=False, indent=1)
        handle.write("\n")

    print(f"wrote {path}: {len(buildings)} of {BUILDING_COUNT} building "
          f"names from entry {LANGUAGES[lang]} ({len(strings)} strings "
          f"in the block)")
    print("OrionLayer reads this on start; restart it to pick them up.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
