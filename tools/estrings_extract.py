#!/usr/bin/env python3
"""Extract the original's ESTRINGS table from the user's installation.

    python tools/estrings_extract.py
    python tools/estrings_extract.py --lang de --lbx /path/to/ESTRGERM.LBX

**THE HELP-TEXT PATTERN, THIRD USE** (decision 38): the bytes are
moved out untouched, `core/estrings.py` decodes at load time, the
file carries a format version and is never committed, `setup.py`
names the command when it is absent, and the caller explains the
absence rather than drawing nothing.

**THE WALK IS ESTRINGS' OWN, NOT TECHNAME'S.** `Load_E_Strings_`
(estrings.cpp:11-37) is

    current_string = loaded_data;
    for (i = 0; i < ESTRINGS_COUNT; ++i) {
        _strings[i] = current_string;
        current_string += strlen(current_string) + 1;
    }

— `strlen + 1`, with **no skipping of NUL runs**, so an empty string
is a valid entry. `Advance_To_Next_String_` (techinit.cpp:11-21),
which the building names use, does skip runs; feeding this file
through that walk would swallow every empty entry and shift each
index after the first gap. The two are transcribed separately for
that reason and a smoke check asserts neither loader reads the
other's file.

**THE LANGUAGE PICKS THE FILE HERE, NOT THE ENTRY.** TECHNAME is one
file whose ENTRY is the language index; ESTRINGS is six files and
always entry 0 (estrings.cpp:14-30).

**GENERATED, NEVER COMMITTED** (decisions 38, 40, 42) — it is the
user's game data.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import lbx  # noqa: E402
from core.config import BASE_DIR, load_settings  # noqa: E402
from core.estrings import (  # noqa: E402
    ESTRINGS_COUNT, FORMAT_VERSION, OPTION_STRINGS, string_file)

#: estrings.cpp:14-30 — the language picks the FILE. The names are
#: the source's own, upper-cased the way MOO2 ships them.
LANGUAGE_FILES = {
    "en": "ESTRINGS.LBX", "de": "ESTRGERM.LBX", "fr": "ESTRFREN.LBX",
    "es": "ESTRSPAN.LBX", "it": "ESTRITAL.LBX", "pl": "ESTRPOLI.LBX",
}

GAME_DIR = os.path.expanduser("~/Master of Orion 2")


#: The entry's own header: `total_count` then `element_size`, two
#: uint16s, read by `Farload_Library_Data_` (farload.cpp:88-92) before
#: it seeks to `sizeof(total_count) + sizeof(element_size) +
#: element_size * start_idx` — offset 4 for `start_idx` 0
#: (farload.cpp:107). **THE BLOCK STARTS AT 4, NOT AT 0.**
#:
#: Walking from 0 instead put every string one index late, and the
#: tell was the two independent sources disagreeing: `Option_String_`
#: says Trade Goods is 0x21D and the naive walk had it at 0x21E.
#: Three anchors from that switch — Housing 0x142, Trade Goods 0x21D,
#: Transport Ship 0x21E — all land exactly with the header skipped,
#: which is what turns "it looks about right" into a transcription.
HEADER_SIZE = 4


def read_header(blob):
    """(total_count, element_size) from the entry's own first 4 bytes."""
    if len(blob) < HEADER_SIZE:
        return 0, 0
    return (int.from_bytes(blob[0:2], "little"),
            int.from_bytes(blob[2:4], "little"))


def split_block(blob, count=ESTRINGS_COUNT):
    """The block's strings, in `Load_E_Strings_`'s order.

    `strlen + 1` per string and nothing else: an empty string is a
    valid entry and consuming it would shift every index after it.
    Stops at `count` — the loop is bounded by ESTRINGS_COUNT, not by
    the end of the block, and the source checks afterwards that it did
    not run past its buffer (estrings.cpp:39-41).

    Starts at `HEADER_SIZE`, which is where the game starts.
    """
    out = []
    offset = HEADER_SIZE
    size = len(blob)
    for _ in range(count):
        if offset > size:
            break
        end = offset
        while end < size and blob[end] != 0:
            end += 1
        out.append(blob[offset:end])
        offset = end + 1
    return out


def decode(raw):
    """One string, as the game's own 8-bit text.

    cp437 with replacement, the same reading `techname_extract` uses:
    the LBX predates unicode, and a tool that dies on one odd byte
    takes the other 811 strings with it.
    """
    return raw.decode("cp437", errors="replace").strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--lbx", default=None)
    parser.add_argument("--lang", default=None,
                        help="language code; default: settings.json")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    lang = args.lang or load_settings().get("language", "en")
    if lang not in LANGUAGE_FILES:
        sys.exit(f"unknown language {lang!r}; known: "
                 f"{sorted(LANGUAGE_FILES)}")
    path = args.lbx or os.path.join(GAME_DIR, LANGUAGE_FILES[lang])
    if not os.path.exists(path):
        sys.exit(f"{path} not found. Point --lbx at your own "
                 f"installation's {LANGUAGE_FILES[lang]}.")

    blob = lbx.read_entry(path, 0)
    total_count, element_size = read_header(blob)
    # THE HEADER IS CHECKED, NOT ASSUMED. `Farload_Library_Data_`
    # refuses the file when `element_size != expected_element_size`
    # (farload.cpp:104-107) and the caller passes ESTRINGS_DATA_SIZE,
    # so the entry states its own block length and the two must
    # agree with what is actually there.
    if total_count < 1 or element_size < 1 or \
            len(blob) < HEADER_SIZE + element_size:
        sys.exit(f"{path} entry 0 has a header of "
                 f"count={total_count}, element_size={element_size} "
                 f"over {len(blob)} bytes — that is not the shape "
                 f"Farload_Library_Data_ reads. Nothing written.")
    strings = split_block(blob)
    if len(strings) < ESTRINGS_COUNT:
        sys.exit(f"{path} entry 0 yields {len(strings)} strings and the "
                 f"walk needs {ESTRINGS_COUNT}. Wrong file, or one this "
                 f"tool does not understand — nothing written.")

    # A DENSE LIST, NOT A MAP, and the difference is load-bearing.
    # `E_Strings_(0x00C)` IS the empty string — it is what
    # `Option_String_` returns for NONE, SEPARATOR and 0 — so a table
    # that stores only non-empty entries cannot tell "the original
    # prints nothing here" from "there is no such index", and the
    # loader would report an absent file for a string that is
    # present and blank. A list also carries its own length: an
    # entry cannot go missing without the count moving, which a
    # sparse map keyed by index allows silently.
    table = [decode(raw) for raw in strings]
    non_empty = sum(1 for text in table if text)

    out_dir = args.out or os.path.join(BASE_DIR, "assets", "shared", "names")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, os.path.basename(string_file(lang)))
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump({
            "_comment": ("GENERATED by tools/estrings_extract.py from "
                         f"{os.path.basename(path)}. Derived from the "
                         "user's own MOO2 installation — do not edit, "
                         "do not ship. Regenerate after changing the "
                         "game language."),
            "_source": os.path.basename(path),
            "language": lang,
            "entry": 0,
            "count": ESTRINGS_COUNT,
            "block_bytes": element_size,
            "non_empty": non_empty,
            "format": FORMAT_VERSION,
            "strings": table,
        }, handle, ensure_ascii=False, indent=1)
        handle.write("\n")

    print(f"wrote {out_path}: {non_empty} non-empty of "
          f"{len(table)} strings from entry 0 of "
          f"{os.path.basename(path)}")
    for _pid, _entry in sorted(OPTION_STRINGS.items(), reverse=True)[:4]:
        print(f"   production {_pid:>4} -> {_entry:#05x} = "
              f"{table[_entry]!r}")
    print("OrionLayer reads this on start; restart it to pick them up.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
