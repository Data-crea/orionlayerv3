#!/usr/bin/env python3
"""Extract the original's BILLTEXT messages from the user's installation.

    python tools/billtext_extract.py
    python tools/billtext_extract.py --lang de --lbx /path/to/BILLTEXT.LBX

**THE HELP-TEXT PATTERN** (decision 38): the bytes are moved out
untouched, `core/billtext.py` decodes at load time, the file carries a
format version and is never committed, and an absent file is a state
the screen explains rather than an error.

**THE WALK IS `Get_Text_Message_`'s** (jim.cpp:336-359), and it is not
the TECHNAME/ESTRINGS shape: a message is not an offset into one block,
it is its OWN LBX entry, six per message — one per language slot:

    entry index = message id * 6 + language

and the entry carries the ordinary (total_count, element_size) 4-byte
header (`Farload_Library_Data_`, farload.cpp:90-113) followed by one
record of element_size bytes with a NUL-terminated string in it. The
element size is CHECKED against what the entry declares, because the
engine itself errors out when the two disagree (farload.cpp:104-107) —
a file this walk does not understand must not be half-read.

The whole file is extracted, not a range: the ids are the game's own
and picking a window here would mean a second id map on the other side.

**GENERATED, NEVER COMMITTED** (decisions 38, 40, 42) — it is the
user's game data.

Requires nothing beyond the standard library and `core/lbx.py`.
"""
import argparse
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import lbx  # noqa: E402
from core.billtext import (  # noqa: E402
    ELEMENT_SIZE, FORMAT_VERSION, LANGUAGE_SLOTS, RESEARCH_MESSAGES,
    message_file)
from core.config import BASE_DIR, load_settings  # noqa: E402

#: The language's slot inside each message's six entries, in
#: `MOX::_settings.language`'s own order (jim.cpp:339-342).
LANGUAGES = {"en": 0, "de": 1, "fr": 2, "es": 3, "it": 4}

DEFAULT_LBX = os.path.expanduser("~/Master of Orion 2/BILLTEXT.LBX")


def entry_count(path):
    """How many entries the container holds (its own 2-byte count)."""
    with open(path, "rb") as handle:
        head = handle.read(4)
    if len(head) < 4:
        raise lbx.LbxError("File is too small to be an LBX container.")
    return struct.unpack_from("<H", head, 0)[0]


def decode(raw):
    """One message, as the game's own 8-bit text.

    cp437, like every other string out of these files: the LBX predates
    unicode. Errors are replaced rather than raised — one odd byte must
    not take the other seventy-seven messages with it. The FMTPARA
    control bytes are left in place; `core/helpformat.py` is where a
    control code means something.
    """
    return raw.split(b"\x00")[0].decode("cp437", errors="replace")


def read_message(blob):
    """(text, problem) for one entry's 4-byte header and one record."""
    if len(blob) < 4:
        return None, "entry is shorter than its own header"
    total, size = struct.unpack_from("<HH", blob, 0)
    if size != ELEMENT_SIZE:
        return None, (f"element size {size}, not {ELEMENT_SIZE} — the "
                      f"engine refuses this too (farload.cpp:104)")
    if total < 1:
        return None, "entry declares no records"
    if len(blob) < 4 + size:
        return None, f"entry holds {len(blob) - 4} bytes, needs {size}"
    return decode(blob[4:4 + size]), None


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
                 f"installation's BILLTEXT.LBX.")

    entries = entry_count(args.lbx)
    total_messages = entries // LANGUAGE_SLOTS
    slot = LANGUAGES[lang]
    messages = {}
    problems = []
    for message_id in range(total_messages):
        index = message_id * LANGUAGE_SLOTS + slot
        if index >= entries:
            break
        try:
            blob = lbx.read_entry(args.lbx, index)
        except lbx.LbxError as err:
            problems.append(f"message {message_id}: {err}")
            continue
        text, problem = read_message(blob)
        if problem:
            problems.append(f"message {message_id}: {problem}")
            continue
        messages[str(message_id)] = text

    missing = [i for i in RESEARCH_MESSAGES if str(i) not in messages]
    if missing:
        sys.exit(f"{args.lbx} yielded {len(messages)} messages but not "
                 f"{missing}, which the research screens read. Wrong file, "
                 f"or one this tool does not understand — nothing written."
                 + ("\n  " + "\n  ".join(problems[:5]) if problems else ""))

    out_dir = args.out or os.path.join(BASE_DIR, "assets", "shared", "names")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, os.path.basename(message_file(lang)))
    with open(path, "w", encoding="utf-8") as handle:
        json.dump({
            "_comment": ("GENERATED by tools/billtext_extract.py from "
                         f"{os.path.basename(args.lbx)}. Derived from the "
                         "user's own MOO2 installation — do not edit, do "
                         "not ship. Regenerate after changing the game "
                         "language."),
            "_source": os.path.basename(args.lbx),
            "language": lang,
            "slot": slot,
            "entries_in_file": entries,
            "format": FORMAT_VERSION,
            "messages": messages,
        }, handle, ensure_ascii=False, indent=1)
        handle.write("\n")

    print(f"wrote {path}: {len(messages)} of {total_messages} messages "
          f"from slot {slot}")
    if problems:
        print(f"  {len(problems)} entries were skipped:")
        for line in problems[:5]:
            print(f"    {line}")
    print("OrionLayer reads this on start; restart it to pick them up.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
