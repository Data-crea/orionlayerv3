#!/usr/bin/env python3
"""The game's words in another language, from another install — work order
200 C.

    python tools/language_files.py "/path/to/a German Master of Orion 2"
    python tools/language_files.py FOLDER --check     # look, change nothing

A MOO2 bought in one language holds that language's files only: an English
install has no GER_HELP.LBX, HGSTRNGS.LBX, ESTRGERM.LBX, MAINGERM.LBX,
GERSKLLS.LBX, GERTECD.LBX, FONTSG.LBX, HERODATG.LBX or GERCRDTS.LBX
(`core/lang.GERMAN_FILES`). A player who also
owns a German one names its folder here, and:

  1. the folder is checked: every German file is there (names in any case);
  2. it is recorded as `language_dir` in the player's settings
     (`core/usersettings`), so choosing Deutsch in Game Settings extracts
     from it (`core/langsetup`) and the engine is told it at start (open fix
     70: `ORION2RE_LANGUAGE_DIR`, read only — `core/lang.engine_env`);
  3. the German extractors run against it now, each its own process, and
     write the player's German files (`assets/shared/{names,help}/*_de.json`,
     never committed, decision 38).

The folder is only read. Nothing is copied into the game's own folder.

THE IDS MUST BE THE GAME'S. A German file is read by the ids of the
English one the engine uses; work order 200 C checked a Steam German 1.31
against a patched English install and found the German files on the
patched layout (GER_HELP's 707 entries, HGSTRNGS's 397) while that
install's own English HELP.LBX and HESTRNGS.LBX were the older 1.31 ones.
The developer store's German check (de_check) compares the two languages entry by
entry; run it after a new folder.
"""
import argparse
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core import lang, usersettings  # noqa: E402

#: (extractor, how it is told the file or folder) for a language's files;
#: TECHNAME, BILLTEXT, KENTEXT and RACESTUF hold every language in one file, in the
#: game's own folder, and need only the language.
STEPS = (
    ("help_extract.py", "GER_HELP.LBX", "positional"),
    ("estrings_extract.py", "ESTRGERM.LBX", "--lbx"),
    ("hestrings_extract.py", "HGSTRNGS.LBX", "--lbx"),
    ("maintext_extract.py", "MAINGERM.LBX", "--lbx"),
    ("skildesc_extract.py", "GERSKLLS.LBX", "--lbx"),
    ("techdesc_extract.py", "GERTECD.LBX", "--lbx"),
    ("infotext_extract.py", None, "--dir"),
    ("techname_extract.py", None, None),
    ("billtext_extract.py", None, None),
    ("kentext_extract.py", None, None),
    ("racestuf_extract.py", None, None),
)


find = lang.find_file


def missing(folder, language="de"):
    """The language's files the folder lacks."""
    return lang.missing_files(language, folder)


def steps(language, folder):
    """[argv] of the extractors, against `folder` (paths under tools/)."""
    if language != "de":
        return []
    out = []
    for tool, name, how in STEPS:
        argv = [os.path.join("tools", tool), "--lang", language]
        if how == "positional":
            argv.insert(1, find(folder, name))
        elif how == "--lbx":
            argv += ["--lbx", find(folder, name)]
        elif how == "--dir":
            argv += ["--dir", folder]
        out.append(argv)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("folder")
    ap.add_argument("--lang", default="de", choices=["de"])
    ap.add_argument("--check", action="store_true",
                    help="check the folder only; record and extract nothing")
    args = ap.parse_args(argv)
    folder = os.path.abspath(os.path.expanduser(args.folder))
    gone = missing(folder, args.lang)
    if gone:
        print(f"{folder}: no {', '.join(gone)} — not a German install")
        return 1
    print(f"{folder}: every German file is there")
    if args.check:
        return 0
    settings = usersettings.load()
    settings.set("language_dir", folder)
    usersettings.save(settings)
    print(f"recorded as language_dir in {settings.path}")
    failed = 0
    for argv_ in steps(args.lang, folder):
        rc = subprocess.call([sys.executable] + argv_, cwd=ROOT)
        failed += rc != 0
        print(f"  {'ok' if rc == 0 else 'FAILED'}  {' '.join(argv_)}")
    print("done — choose Deutsch in Game Settings and restart" if not failed
          else f"{failed} extractor(s) failed — see above")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
