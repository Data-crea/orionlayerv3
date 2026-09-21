#!/usr/bin/env python3
"""Rebuild everything a fresh clone is missing, then prove it worked.

The repository does not carry generated artwork: git stores images as
whole blobs rather than diffs, so every regeneration of an icon set
would leave a full extra copy in the history forever — and those are
exactly the sets that get regenerated. `.gitignore` says which, and
why each exception is an exception.

This script runs the generators in order and finishes with the smoke
test, so "did the clone come out complete?" has one answer instead of
a checklist. Everything it does is idempotent, and that is not a
figure of speech: every step here was checked byte-for-byte against
the committed file it replaces. `stars/` is deliberately absent —
`make_star_icons.py` no longer reproduces the trimmed sprites in the
tree, so those are committed rather than generated. A generator that
does not reproduce its own output has no business being in a setup
script.

    python tools/setup.py              # rebuild + verify
    python tools/setup.py --check      # report only, change nothing

What it does NOT do is touch anything derived from your Master of
Orion 2 installation. The context-help texts come from your own
HELP.LBX and the nebula sprites from your own STARBG.LBX; those are
separate, deliberate steps:

    python tools/help_extract.py                    # help texts
    python tools/nebula_extract.py /path/to/starbg.lbx
    python tools/techname_extract.py                # building names
    python tools/estrings_extract.py                # option strings
    python tools/raceicon_extract.py                # population figures
    python tools/maintext_extract.py                # system specials

Missing help texts are not an error — the popup says so and names the
command. The script reports their state and moves on.
"""
import argparse
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.buildnames import name_file as build_name_file
from core.maintext import text_file as maintext_file  # noqa: E402
from core.shipparts import name_file as shipparts_file  # noqa: E402
from core.estrings import string_file as estrings_file  # noqa: E402
from core.hestrings import string_file as hestrings_file  # noqa: E402
from core.technames import name_file as technames_file  # noqa: E402
from core.billtext import message_file as billtext_file  # noqa: E402
from core.kentext import string_file as kentext_file  # noqa: E402
from screens.fleets.fltart import GAMEDATA as _fltart_gamedata  # noqa: E402
from screens.colony_summary.colonyfigures import (  # noqa: E402
    FIGURE_DIR, all_names)
from core.config import load_settings      # noqa: E402
from core.helptext import help_file        # noqa: E402

#: Where git looks for this project's hooks. A clone does not inherit git
#: config, so setup switches it on; the smoke test holds this line to the
#: directory. ONE SETTING SWITCHES BOTH HOOKS ON, which is why there is
#: nothing per-hook to install here.
#:
#:   pre-commit  the FAST tier — refuses the commit on any exit but 0
#:               (work order 126 part B, decision 31)
#:   pre-push    the FULL suite — refuses the push on any exit but 0, and
#:               on a PASSED line that says FAST TIER (work order 158)
#:
#: The pair is the point: the commit gate got cheaper in work order 158
#: and the checks it stopped running did not become optional, they moved
#: one step later. A clone with only one of the two is a clone with a
#: hole in it, so `--check` reports them separately.
HOOKS_PATH = "tools/githooks"

#: Hooks that must exist in HOOKS_PATH and be executable. Named rather
#: than globbed: a hook that silently disappeared is the failure this
#: list exists to make loud.
HOOKS = ("pre-commit", "pre-push")

GM = os.path.join(ROOT, "screens", "galaxy_map", "assets")
CS = os.path.join(ROOT, "screens", "colony_summary", "assets")
#: IMPORTED, not spelled again — `fltart.GAMEDATA` is where the
#: loader looks and therefore the only place that may decide it.
FLEET_GAMEDATA = _fltart_gamedata

#: (tool, arguments, a path that must exist afterwards, what it is)
STEPS = [
    ("make_ship_icons.py", [],
     os.path.join(GM, "ships", "player"),
     "ship and monster steps, scaled from ships/_src/"),
    ("make_sidebar_icons.py", [],
     os.path.join(GM, "icons", "treasury.png"),
     "5 sidebar icons, cut from icons/_source_sheet.png"),
    ("make_black_hole_master.py", [],
     os.path.join(GM, "black_hole.png"),
     "rotatable black hole master"),
    ("make_output_icons.py", [],
     os.path.join(CS, "output", "morale_low.png"),
     "6 output panel icons, cut from assets/_src/output/"),
    ("make_surface_tiles.py", [],
     os.path.join(CS, "surfaces", "gaia.png"),
     "10 planet surface pictures, cut from assets/_src/surfaces/"),
    # THE COLONY FRAME PLATES ARE GONE — Phase B, 12 September 2026,
    # decision 55. They were decision 49's derived files and needed a
    # step here; the colony screen wears one fixed image now and
    # `frame_build.py` is deleted with the rest of the plate
    # machinery. Nothing replaces the step: `assets/frame.png` is
    # authored artwork and is committed.
]

#: Inputs that must be in the repository for the steps to work. If one
#: of these is missing the clone is broken, not merely incomplete.
REQUIRED_INPUTS = [
    (os.path.join(GM, "ships", "_src"), "HD ship masters"),
    # NOT A "MASTER" ANY MORE — Phase B. This file was the metal the
    # colony plate was nine-sliced out of, which is why it was called
    # one and why it was required for a STEP; the colony screen wears
    # its own artwork now and nothing builds from this. It is still
    # required, because it is the galaxy map's own frame and that
    # screen derives its boxes from its holes.
    (os.path.join(GM, "frame.png"), "galaxy map frame"),
    (os.path.join(ROOT, "screens", "colony_summary", "assets",
                  "frame.png"), "colony frame"),
    (os.path.join(ROOT, "screens", "game_menu", "assets", "frame.png"),
     "GAME menu frame (decision 69)"),
    (os.path.join(ROOT, "screens", "colony_summary",
                  "layout_reference.json"), "colony layout reference"),
    (os.path.join(GM, "icons", "_source_sheet.png"), "sidebar icon sheet"),
    (os.path.join(GM, "_black_hole_src.png"), "black hole source"),
    (os.path.join(CS, "_src", "output", "symbols.png"),
     "output icon sheet"),
    (os.path.join(CS, "_src", "output", "normal_moral.png"),
     "normal morale mask sheet"),
    (os.path.join(CS, "_src", "output", "low_moral.png"),
     "low morale mask sheet"),
    (os.path.join(CS, "_src", "surfaces", "planet_surfaces.png"),
     "planet surface sheet"),
    (os.path.join(GM, "stars"), "star sprites (committed, see .gitignore)"),
]

def from_game(settings=None):
    """Files derived from the user's own MOO2 — reported, never run.

    [(path, what, command)]. The help entry is built from the
    language in settings.json rather than from a fixed
    `help_en.json`, because that is the file `HelpText` reads: a
    German install extracted `help_de.json` correctly and was still
    told here that the texts were absent, while an English file with
    `"language": "de"` set was reported ok and showed placeholders in
    game. Both directions were wrong, and neither is visible from
    the report alone.
    """
    lang = (settings if settings is not None else load_settings()
            ).get("language", "en")
    cmd = "python tools/help_extract.py"
    if lang != "en":
        cmd += f" --lang {lang}"
    return [
        (os.path.join(ROOT, *help_file(lang).split("/")),
         f"context-help texts ({lang}) — without them every right "
         f"click shows a placeholder, not the game's text",
         cmd),
        (os.path.join(GM, "nebula_ref"),
         "nebula reference (unlocks 2 smoke assertions)",
         "python tools/nebula_extract.py /path/to/starbg.lbx"),
        (os.path.join(ROOT, *build_name_file(lang).split("/")),
         f"building names ({lang}) — without them the colony summary's "
         f"BUILDING column says so instead of naming what is being "
         f"built",
         "python tools/techname_extract.py"
         + (f" --lang {lang}" if lang != "en" else "")),
        # THE SAME EXTRACTION WRITES A SECOND FILE (fundament 64): the
        # ship part names for the Planets panel's monster values.
        (os.path.join(ROOT, *shipparts_file(lang).split("/")),
         f"ship part names ({lang}) — without them the Planets panel "
         f"shows weapon, shield, special and hull numbers instead of "
         f"names",
         "python tools/techname_extract.py"
         + (f" --lang {lang}" if lang != "en" else "")),
        # AND A THIRD FILE OUT OF THE SAME BLOCK (work order 130 D):
        # the research field and application names, which are the first
        # two tables TECHNAME's walk passes on its way to the buildings.
        (os.path.join(ROOT, *technames_file(lang).split("/")),
         f"research names ({lang}) — without them the research select "
         f"screen cannot name a field or a choice, and hands over to "
         f"the fallback view rather than drawing numbers",
         "python tools/techname_extract.py"
         + (f" --lang {lang}" if lang != "en" else "")),
        # BILLTEXT.LBX: the research panel's own wording. A message per
        # six LBX entries, one per language — not a block like the rest
        # (jim.cpp:336-359).
        (os.path.join(ROOT, *billtext_file(lang).split("/")),
         f"research panel wording ({lang}) — without them the panel "
         f"has no 'Pure research' row label, no 'Research cost: ' and "
         f"no category names, and falls back",
         "python tools/billtext_extract.py"
         + (f" --lang {lang}" if lang != "en" else "")),
        # MAINTEXT.LBX: the system-special descriptions. Nothing draws
        # them yet — the galaxy map's popups are their own brief.
        (os.path.join(ROOT, *maintext_file(lang).split("/")),
         f"system special descriptions ({lang}) — not drawn yet; the "
         f"galaxy map's popups will read them",
         "python tools/maintext_extract.py"
         + (f" --lang {lang}" if lang != "en" else "")),
        # TWO FILES FOR ONE COLUMN, and the second is the one that
        # matters more often. `COLBLDG::Selection_Name_` sends a
        # BUILDING id to techname.lbx and an OPTION id to
        # estrings.lbx, and Trade Goods — what an idle colony
        # produces, and what every row of the reference save produces
        # — is an option. Extracting only the names above leaves the
        # column blank on exactly the saves a player is most likely
        # to open, which is how it stayed blank until 7 September
        # 2026.
        (os.path.join(ROOT, *estrings_file(lang).split("/")),
         f"option strings ({lang}) — without them the BUILDING column "
         f"is blank for Trade Goods, Housing and every other "
         f"non-building the game can produce",
         "python tools/estrings_extract.py"
         + (f" --lang {lang}" if lang != "en" else "")),
        # HAROLD'S MESSAGE STRINGS (brief 101): the Planets list's
        # "-25% prod", "%d prod/worker", "%d max pop" and its status
        # line come from HESTRNGS.LBX, decision 38's pattern.
        (os.path.join(ROOT, *hestrings_file(lang).split("/")),
         f"message strings ({lang}) — without them the Planets list "
         f"shows its values without the original's wording",
         "python tools/hestrings_extract.py"
         + (f" --lang {lang}" if lang != "en" else "")),
        # THE POPULATION FIGURES (decision 50). Checked by the FIRST
        # file of the set rather than by the directory: an interrupted
        # extraction leaves a directory that exists and is short, and
        # a check on the directory would call that done. The loader
        # reports "partial" for the same reason.
        (os.path.join(ROOT, FIGURE_DIR, all_names()[0]),
         f"population figures ({len(all_names())} sprites) — without "
         f"them the colony summary draws coloured cells instead of "
         f"the game's own colonists",
         "python tools/raceicon_extract.py"),
        # KENTEXT.LBX: the weapon firing-arc words. **REGISTERED
        # 20 September 2026 — it had been missing since the extractor
        # was written**, so a clone was never told to run it and this
        # report never said the file was absent. Found by the check
        # below, which is the whole reason the check exists.
        (os.path.join(ROOT, *kentext_file(lang).split("/")),
         f"weapon firing-arc words ({lang}) — without them the Fleets "
         f"ship panel lists a weapon with no arc after its name",
         "python tools/kentext_extract.py"
         + (f" --lang {lang}" if lang != "en" else "")),
        # THE FLEETS SCREEN'S OWN ARTWORK (work order 142 D1), the
        # second one that was missing here. Checked by `manifest.json`
        # rather than by the directory, for the reason the population
        # figures give: an interrupted extraction leaves a directory
        # that exists and is short.
        (os.path.join(FLEET_GAMEDATA, "manifest.json"),
         "Fleets ship pictures — without them a grid cell shows the "
         "builder's colour and the ship's name instead of the "
         "original's own picture",
         "python tools/fleet_art_extract.py"),
    ]


def run(tool, extra):
    """Run a generator. Returns True on success."""
    path = os.path.join(ROOT, "tools", tool)
    proc = subprocess.run([sys.executable, path] + extra,
                          cwd=ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"    FAILED: {tool}")
        for line in (proc.stderr or proc.stdout).strip().splitlines()[-6:]:
            print(f"      {line}")
        return False
    return True


def main():
    ap = argparse.ArgumentParser(
        description="Rebuild generated assets after a clone.")
    ap.add_argument("--check", action="store_true",
                    help="report what is missing, change nothing")
    ap.add_argument("--skip-smoke", action="store_true",
                    help="do not run the smoke test at the end")
    args = ap.parse_args()

    print("OrionLayer v3 setup\n")

    missing_inputs = [(p, what) for p, what in REQUIRED_INPUTS
                      if not os.path.exists(p)]
    if missing_inputs:
        print("  These are committed files and should be here. A clone "
              "missing them is broken, not incomplete:")
        for path, what in missing_inputs:
            print(f"    MISSING  {what} — {os.path.relpath(path, ROOT)}")
        return 1

    hooks = subprocess.run(["git", "config", "--get", "core.hooksPath"],
                           cwd=ROOT, capture_output=True, text=True)
    _missing = [h for h in HOOKS
                if not os.access(os.path.join(ROOT, HOOKS_PATH, h), os.X_OK)]
    if _missing:
        print(f"  Git hooks: MISSING OR NOT EXECUTABLE — {', '.join(_missing)}")
    if hooks.stdout.strip() == HOOKS_PATH:
        print(f"  Git hooks: ok ({HOOKS_PATH}) — pre-commit runs the fast "
              f"tier, pre-push the full suite\n")
    elif args.check:
        print(f"  Git hooks: OFF — setup sets core.hooksPath to {HOOKS_PATH}\n")
    elif os.path.isdir(os.path.join(ROOT, ".git")):
        subprocess.run(["git", "config", "core.hooksPath", HOOKS_PATH],
                       cwd=ROOT, check=True)
        print(f"  Git hooks: switched on ({HOOKS_PATH}) — pre-commit runs "
              f"the fast tier, pre-push the full suite\n")
    else:
        print("  Git hooks: not a git clone, nothing to switch on\n")

    print("  Generated artwork:")
    failed = []
    for tool, extra, produced, what in STEPS:
        present = os.path.exists(produced)
        if args.check:
            print(f"    {'ok      ' if present else 'MISSING '} {what}")
            continue
        print(f"    {what} ...", end=" ", flush=True)
        if run(tool, extra):
            print("ok")
        else:
            failed.append(tool)

    print("\n  Derived from your Master of Orion 2 installation:")
    for path, what, cmd in from_game():
        if os.path.exists(path):
            print(f"    ok       {what}")
        else:
            # Not a failure: the app explains this itself and names
            # the command. Setup only has to make it visible.
            print(f"    absent   {what} — run: {cmd}")

    if failed:
        print(f"\n{len(failed)} generator(s) failed: {', '.join(failed)}")
        return 1
    if args.check:
        print("\nCheck only, nothing was rebuilt.")
        return 0

    if args.skip_smoke:
        print("\nRebuilt. Smoke test skipped.")
        return 0

    print("\n  Verifying:")
    env = dict(os.environ, SDL_VIDEODRIVER="dummy",
               SDL_AUDIODRIVER="dummy")
    proc = subprocess.run(
        [sys.executable, os.path.join(ROOT, "tools", "smoke_test.py"),
         "--quiet"],
        cwd=ROOT, capture_output=True, text=True, env=env)
    tail = (proc.stdout or "").strip().splitlines()
    # --quiet prints the summary and the peak-memory line on a pass.
    for line in tail[-2:]:
        print(f"    {line}")
    if proc.returncode != 0:
        for line in tail[-12:]:
            print(f"    {line}")
        print("\nThe tree is not complete. See above.")
        return 1

    print("\nReady. Start with:  python main.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
