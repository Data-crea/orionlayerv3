#!/usr/bin/env python3
"""Move a mod folder's `files/<tree path>` pictures to the new names —
HD EXTENSION `mod_layout`, work order 336.

    python tools/mod_migrate.py [--folder DIR]          # dry run: lists moves
    python tools/mod_migrate.py --apply [--folder DIR]  # moves them

Until 336 a mod folder mirrored the program's tree under `files/`. The new
names (`core/modlayout.py`: `buildings/`, `stars/`, `new_game/…`) need no
knowledge of the tree. `files/` still works, so migrating is optional; this
tool only saves a modder the typing.

SAFE BY DESIGN. Nothing is overwritten (a taken target is a reported
conflict), a file with no new name stays in `files/`, and only EMPTY
directories are removed afterwards. Before the first move a plain list
`migrate_<time>.txt` (old name -> new name) is written beside the mod
folder, so any move can be undone by hand. A second run moves nothing.
A folder inside the repository is refused.
"""
import argparse
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vdisplay  # noqa: E402
vdisplay.headless_clients()

from core import modlayout, usermod  # noqa: E402
from core.config import BASE_DIR  # noqa: E402


def plan(folder, screens):
    """([(old, new)], kept, conflicts): names relative to `folder`, `/`.

    A move is planned only when the new name translates back to the same
    tree path (`to_tree`): a building file with a non-canonical name would
    otherwise change which picture it fills."""
    legacy = os.path.join(folder, "files")
    moves, kept, conflicts = [], 0, []
    taken = set()
    for dirpath, _dirs, names in os.walk(legacy):
        for f in sorted(names):
            rel = os.path.relpath(os.path.join(dirpath, f), legacy)
            tree = rel.replace(os.sep, "/")
            new = None
            if tree.lower().endswith(usermod.IMAGE_EXT):
                new = modlayout.from_tree(tree, screens)
                if new is not None and (modlayout.to_tree(
                        new, screens) != tree
                        or not usermod.fills_a_picture(tree)):
                    # a name `init` would not index stays where a loader
                    # that reads `files/` finds it
                    new = None
            if new is None:
                kept += 1
            elif os.path.lexists(os.path.join(folder, *new.split("/"))) \
                    or new.casefold() in taken:
                # (casefold: two names that are one file on a disk that
                # ignores case)
                conflicts.append(("files/" + tree, new))
            else:
                taken.add(new.casefold())
                moves.append(("files/" + tree, new))
    return moves, kept, conflicts


def prune(folder):
    """Remove the empty directories below `files/` (never a file)."""
    legacy = os.path.join(folder, "files")
    for dirpath, _dirs, _names in os.walk(legacy, topdown=False):
        if dirpath != legacy:
            try:
                os.rmdir(dirpath)       # fails on a non-empty one, by design
            except OSError:
                pass


def migrate(folder, apply=False, screens=None, log=print):
    """Plan, and with `apply` do. Returns (moved, kept, conflicts, list)."""
    folder = os.path.abspath(folder)
    try:
        inside = os.path.commonpath([folder, ROOT]) == ROOT
    except ValueError:                  # another drive on Windows
        inside = False
    if inside:
        raise SystemExit(f"refused: {folder} is inside OrionLayer's tree — "
                         f"the mod folder lives outside it")
    if not os.path.isdir(folder):
        raise SystemExit(f"no such folder: {folder}")
    if screens is None:
        screens = modlayout.screen_names(BASE_DIR)
    moves, kept, conflicts = plan(folder, screens)
    for old, new in moves:
        log(f"{'move' if apply else 'would move'}: {old} -> {new}")
    for old, new in conflicts:
        log(f"CONFLICT: {old} -> {new} (the target exists; left alone)")
    listing = None
    if apply and moves:
        stamp = time.strftime("%Y%m%d_%H%M%S")
        listing = os.path.join(os.path.dirname(folder),
                               f"migrate_{stamp}.txt")
        n = 1
        while os.path.exists(listing):  # never over an earlier list
            n += 1
            listing = os.path.join(os.path.dirname(folder),
                                   f"migrate_{stamp}_{n}.txt")
        with open(listing, "w", encoding="utf-8") as out:
            out.writelines(f"{o} -> {n}\n" for o, n in moves)
        log(f"undo list: {listing}")
        for old, new in moves:
            dest = os.path.join(folder, *new.split("/"))
            if os.path.lexists(dest):
                log(f"CONFLICT: {old} -> {new} (appeared meanwhile)")
                continue
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            os.replace(os.path.join(folder, *old.split("/")), dest)
        prune(folder)
    log(f"{'moved' if apply else 'would move'} {len(moves)}, kept in "
        f"files/ {kept}, conflicts {len(conflicts)}")
    return len(moves), kept, len(conflicts), listing


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--folder", default=None,
                    help="the mod folder (default: the player's)")
    ap.add_argument("--apply", action="store_true",
                    help="move the files (default: only list)")
    args = ap.parse_args(argv)
    try:
        _m, _k, conflicts, _l = migrate(args.folder or usermod.mod_dir(),
                                        args.apply)
    except OSError as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    return 1 if conflicts else 0


if __name__ == "__main__":
    sys.exit(main())
