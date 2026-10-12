#!/usr/bin/env python3
"""Install, check or make OrionLayer's base pack — work order 241.

    python tools/basepack.py install orionlayer-base-pack.zip
    python tools/basepack.py check            # every file, by sha256
    python tools/basepack.py make OUT.zip     # the pack as a zip (maintainer)
    python tools/basepack.py refresh          # rewrite basepack.json from
                                              # the installed pack (maintainer;
                                              # `manifest` is the old name)

The pictures are not in this repository (see `core/basepack.py`): they
come as one zip and go into the base pack folder, `--to DIR` or
`ORIONLAYER_BASE_DIR` choosing another one. `install` unpacks only the
files `basepack.json` names, refuses a zip whose files differ from it,
and never touches anything else in the folder. `make` refuses a pack
that differs from the manifest: a release zip is what `refresh` last
recorded, file for file.

The pack carries its licence, `LICENSE.txt` at its top (CC BY 4.0, Data's
decision of work order 243); the manifest names it beside the pictures.

`refresh` is how the manifest follows the maintainer's pack (work order
242: Data swaps pictures daily and no picture needs a manual step;
`dev:tools/close_run.py` runs it). It records every picture in the pack and
says what changed. A listed picture that is gone from the pack is
dropped from the manifest and NAMED — with the code that still mentions
it, so a drop the code would miss is never silent. A file that is not a
picture is left out and named too (the manifest names pictures only).
"""
import argparse
import hashlib
import json
import os
import sys
import zipfile

TREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PICTURE_EXT = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tga",
               ".svg", ".ico")
#: The pack's licence (Data's decision, work order 243: the pictures are
#: under CC BY 4.0). Named in the manifest like a picture, so installing,
#: making the release zip and the start's presence check all carry it: the
#: credits travel with every copy of the pack.
NOTICES = ("LICENSE.txt",)
#: Where the code that asks for a picture lives (for naming a dropped one).
CODE_DIRS = ("core", "screens", "tools", "mods")
CODE_EXT = (".py", ".json")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import basepack  # noqa: E402


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def check(folder, man=None):
    """[fault, …] for the pack in folder against the manifest."""
    faults = []
    for rel, (size, sha) in sorted((man or basepack.manifest())
                                   ["files"].items()):
        p = os.path.join(folder, rel)
        if not os.path.isfile(p):
            faults.append("missing: " + rel)
            continue
        with open(p, "rb") as f:
            data = f.read()
        if len(data) != size or _sha(data) != sha:
            faults.append("differs: " + rel)
    return faults


def install(zip_path, folder, man=None):
    files = (man or basepack.manifest())["files"]
    with zipfile.ZipFile(zip_path) as z:
        names = set(z.namelist())
        bad = [rel for rel in files if rel not in names]
        bad += [rel for rel in files if rel in names and
                _sha(z.read(rel)) != files[rel][1]]
        if bad:
            print(f"{zip_path} is not the base pack this OrionLayer expects "
                  f"({len(bad)} file(s) missing or different, first: "
                  f"{bad[0]}); nothing installed.")
            return 1
        for rel in sorted(files):
            dest = os.path.join(folder, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as f:
                f.write(z.read(rel))
    print(f"Installed {len(files)} files into {folder}.")
    return 0


def make(out, folder):
    faults = check(folder)
    if faults:
        print(f"The pack in {folder} does not match basepack.json: "
              f"{faults[0]} (+{len(faults) - 1}); no zip written.")
        return 1
    files = basepack.manifest()["files"]
    with zipfile.ZipFile(out, "w", zipfile.ZIP_STORED) as z:
        for rel in sorted(files):
            z.write(os.path.join(folder, rel), rel)
    print(f"{out}: {len(files)} files, {os.path.getsize(out) / 1e6:.1f} MB")
    return 0


def scan(folder):
    """({relpath: [size, sha256]} of the pack's pictures and its licence,
    [left out])."""
    files, other = {}, []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, folder).replace(os.sep, "/")
            if name.startswith(".") or not (name.lower().endswith(PICTURE_EXT)
                                            or rel in NOTICES):
                other.append(rel)
                continue
            with open(full, "rb") as f:
                data = f.read()
            files[rel] = [len(data), _sha(data)]
    return files, other


def mentions(rel, tree=TREE):
    """`path:line` of the tree's code that names rel's file (its tree path
    or its bare file name) — evidence that the code may still ask for it."""
    name = os.path.basename(rel)
    hits = []
    for top in CODE_DIRS:
        for dirpath, dirnames, filenames in os.walk(os.path.join(tree, top)):
            dirnames[:] = sorted(d for d in dirnames
                                 if d not in ("__pycache__", "smoke_suite"))
            for fn in sorted(filenames):
                if not fn.endswith(CODE_EXT):
                    continue
                full = os.path.join(dirpath, fn)
                try:
                    with open(full, encoding="utf-8") as f:
                        for i, line in enumerate(f, 1):
                            if rel in line or name in line:
                                hits.append("%s:%d" % (
                                    os.path.relpath(full, tree), i))
                except (OSError, UnicodeDecodeError):
                    continue
    return hits


def refresh(folder, path=basepack.MANIFEST, log=print):
    """Rewrite the manifest from the pack; (added, changed, dropped)."""
    if not os.path.isdir(folder):
        log(f"no base pack at {folder}; basepack.json left as it is")
        return None
    with open(path, encoding="utf-8") as f:
        old = json.load(f)["files"]
    files, other = scan(folder)
    added = sorted(set(files) - set(old))
    dropped = sorted(set(old) - set(files))
    changed = sorted(r for r in set(files) & set(old) if files[r] != old[r])
    for rel in added:
        log(f"  added    {rel}")
    for rel in changed:
        log(f"  changed  {rel}")
    for rel in dropped:
        hits = mentions(rel)
        log(f"  DROPPED  {rel} — " + (
            "still named in " + ", ".join(hits[:4])
            + (" …" if len(hits) > 4 else "") if hits
            else "no code names it"))
    for rel in other:
        log(f"  left out {rel} (not a picture)")
    if added or changed or dropped:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"version": 1, "files": files}, f, indent=2,
                      sort_keys=True)
            f.write("\n")
    log(f"{path}: {len(files)} files — {len(added)} added, {len(changed)} "
        f"changed, {len(dropped)} dropped"
        + ("" if added or changed or dropped else ", unchanged"))
    return added, changed, dropped


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("what", choices=("install", "check", "make", "refresh",
                                     "manifest"))
    ap.add_argument("zip", nargs="?")
    ap.add_argument("--to", help="the pack folder (default: "
                    + basepack.base_dir() + ")")
    a = ap.parse_args(argv)
    folder = os.path.abspath(a.to) if a.to else basepack.base_dir()
    if a.what in ("install", "make") and not a.zip:
        ap.error(a.what + " needs a zip path")
    if a.what == "install":
        return install(a.zip, folder)
    if a.what == "make":
        return make(a.zip, folder)
    if a.what in ("refresh", "manifest"):
        return 0 if refresh(folder) is not None else 1
    faults = check(folder)
    for f in faults[:20]:
        print("FAULT", f)
    n = len(basepack.manifest()["files"])
    print(f"{folder}: {n - len(faults)} of {n} files as basepack.json names "
          f"them — {'COMPLETE' if not faults else 'NOT COMPLETE'}")
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(main())
