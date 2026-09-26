#!/usr/bin/env python3
"""Back up every file a live run can write, and prove afterwards that it did not — work order 175.

    python tools/liveguard.py snapshot DIR          # before a live run
    python tools/liveguard.py verify DIR            # after: names every change
    python tools/liveguard.py verify DIR --restore  # ...and puts it back
    python tools/liveguard.py verify DIR --allow SAVE4.GAM

**WHY.** 174 hashed SAVE1-11 as ordered and still left a file changed:
the game rewrote `MOX.SET` when the loaded scratch game was left for New
Game (`FILEDEF::Save_Game_Settings_`, filedef.cpp:82), with the loaded
save's settings — CONTINUE would have offered the scratch slot — and it
had to be reconstructed from an autosave. A promise about "the files"
has to cover every file, found in the source, not the ones a work order
happened to name.

**WHAT A RUN CAN WRITE**, found in the orion2re source and in this tree
(work order 175):

    the game folder   SAVE1..SAVE10.GAM   Save_Game_ (filedef.cpp:64); SAVE10
                                          is the autosave TURN writes
                      SAVE11.GAM          written by nothing (126 D) — held too
                      MOX.SET             Save_Game_Settings_ (filedef.cpp:24,
                                          loadsave.cpp:1063, initgame.cpp:113)
                      HOF.M2              the Hall of Fame (score.cpp:205, :614)
                      lastrace.rac        the last custom race (racesel.cpp:704)
                      TEMP.TMP            the swap block (swap.cpp:24)
    OrionLayer        user_settings.json  the settings rows (usersettings.save),
                                          with .tmp and .corrupt beside it
                      the tree            the F5 editor saves boxes.json,
                                          races.json, colony plates — held by
                                          the tree's `git status`, before and after
    written anew, never over Data's: orion2re's `logs/game.<pid>.log`
    beside the binary (main.cpp:66), F8 screenshots (ORIONLAYER_SHOTS), the
    mod folder's resize cache — listed, not restored.

A file that is absent before and present after is a change too (a
restore removes it). `--allow` names what a run may change on purpose —
the scratch slot it saved to, if it saved — and nothing else.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME_DIR = os.environ.get("ORIONLAYER_GAME_DIR",
                          os.path.expanduser("~/Master of Orion 2"))

GAME_FILES = tuple(f"SAVE{n}.GAM" for n in range(1, 12)) + (
    "MOX.SET", "HOF.M2", "lastrace.rac", "TEMP.TMP")
LAYER_FILES = ("user_settings.json", "user_settings.json.tmp",
               "user_settings.json.corrupt")


def _find(folder, name):
    """The file as the game opens it — `fopen_case` matches any case."""
    want = name.lower()
    try:
        for f in os.listdir(folder):
            if f.lower() == want:
                return os.path.join(folder, f)
    except OSError:
        pass
    return None


def _sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _tree_status(root=ROOT):
    try:
        return subprocess.run(["git", "status", "--porcelain"], cwd=root,
                              capture_output=True, text=True).stdout
    except OSError:
        return None


def files(game_dir=None, root=None):
    """{key: absolute path or None} of every file a run can write."""
    game_dir, root = game_dir or GAME_DIR, root or ROOT
    out = {f"game/{n}": _find(game_dir, n) for n in GAME_FILES}
    out.update({f"layer/{n}": (os.path.join(root, n)
                               if os.path.exists(os.path.join(root, n))
                               else None) for n in LAYER_FILES})
    return out


def snapshot(dest, game_dir=None, root=None):
    """Copy and hash every file; record the tree's status. Returns the
    manifest."""
    os.makedirs(dest, exist_ok=True)
    man = {"taken": time.strftime("%Y-%m-%d %H:%M:%S"),
           "game_dir": game_dir or GAME_DIR, "root": root or ROOT,
           "files": {}, "tree_status": _tree_status(root or ROOT)}
    for key, path in files(game_dir, root).items():
        if path is None:
            man["files"][key] = None
            continue
        copy = os.path.join(dest, key.replace("/", "__"))
        shutil.copy2(path, copy)
        man["files"][key] = {"path": path, "sha256": _sha(path),
                             "copy": copy}
    with open(os.path.join(dest, "manifest.json"), "w") as fh:
        json.dump(man, fh, indent=1)
    return man


def verify(dest, restore=False, allow=(), log=print):
    """Compare every file with the snapshot. Returns (changes, restored)
    — `changes` [(key, "changed"/"appeared"/"vanished")], allowed ones
    excluded; with `restore`, each is put back (an appeared file is
    removed) and the list of restored keys returned."""
    with open(os.path.join(dest, "manifest.json")) as fh:
        man = json.load(fh)
    now = files(man["game_dir"], man["root"])
    changes, restored = [], []
    for key, before in man["files"].items():
        name = key.split("/", 1)[1]
        if name in allow:
            continue
        path = now.get(key)
        if before is None and path is None:
            continue
        if before is None:
            kind = "appeared"
        elif path is None:
            kind = "vanished"
        elif _sha(path) != before["sha256"]:
            kind = "changed"
        else:
            continue
        changes.append((key, kind))
        if restore:
            if before is None:
                os.remove(path)
            else:
                target = path or before["path"]
                shutil.copy2(before["copy"], target)
                if _sha(target) != before["sha256"]:
                    raise RuntimeError(f"{key}: the restored copy does not "
                                       f"match its hash")
            restored.append(key)
    status = _tree_status(man["root"])
    if man.get("tree_status") is not None and status != man["tree_status"]:
        changes.append(("tree/git status", "changed"))
    for key, kind in changes:
        log(f"{kind.upper():9s} {key}" + ("  -> restored" if key in restored
                                          else ""))
    if not changes:
        log(f"every file identical to the snapshot of {man['taken']}"
            + (f" (allowed: {', '.join(allow)})" if allow else ""))
    return changes, restored


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("snapshot")
    s.add_argument("dir")
    v = sub.add_parser("verify")
    v.add_argument("dir")
    v.add_argument("--restore", action="store_true")
    v.add_argument("--allow", action="append", default=[])
    args = ap.parse_args()
    if args.cmd == "snapshot":
        man = snapshot(args.dir)
        held = sum(1 for f in man["files"].values() if f)
        print(f"{held} files backed up to {args.dir}")
        return 0
    changes, _ = verify(args.dir, args.restore, tuple(args.allow))
    return 1 if changes and not args.restore else 0


if __name__ == "__main__":
    sys.exit(main())
