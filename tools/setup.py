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

Missing help texts are not an error — the popup says so and names the
command. The script reports their state and moves on.
"""
import argparse
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GM = os.path.join(ROOT, "screens", "galaxy_map", "assets")

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
]

#: Inputs that must be in the repository for the steps to work. If one
#: of these is missing the clone is broken, not merely incomplete.
REQUIRED_INPUTS = [
    (os.path.join(GM, "ships", "_src"), "HD ship masters"),
    (os.path.join(GM, "icons", "_source_sheet.png"), "sidebar icon sheet"),
    (os.path.join(GM, "_black_hole_src.png"), "black hole source"),
    (os.path.join(GM, "stars"), "star sprites (committed, see .gitignore)"),
]

#: Derived from the user's own MOO2 files — reported, never run.
FROM_GAME = [
    (os.path.join(ROOT, "assets", "shared", "help", "help_en.json"),
     "context-help texts", "python tools/help_extract.py"),
    (os.path.join(GM, "nebula_ref"),
     "nebula reference (unlocks 2 smoke assertions)",
     "python tools/nebula_extract.py /path/to/starbg.lbx"),
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
    for path, what, cmd in FROM_GAME:
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
        [sys.executable, os.path.join(ROOT, "tools", "smoke_test.py")],
        cwd=ROOT, capture_output=True, text=True, env=env)
    tail = (proc.stdout or "").strip().splitlines()
    for line in tail[-1:]:
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
