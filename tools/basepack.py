#!/usr/bin/env python3
"""Install, check or make OrionLayer's base pack — work order 241.

    python tools/basepack.py install orionlayer-base-pack.zip
    python tools/basepack.py check            # every file, by sha256
    python tools/basepack.py make OUT.zip     # the pack as a zip (maintainer)
    python tools/basepack.py manifest         # rewrite basepack.json from
                                              # the installed pack (maintainer)

The pictures are not in this repository (see `core/basepack.py`): they
come as one zip and go into the base pack folder, `--to DIR` or
`ORIONLAYER_BASE_DIR` choosing another one. `install` unpacks only the
files `basepack.json` names, refuses a zip whose files differ from it,
and never touches anything else in the folder.
"""
import argparse
import hashlib
import json
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import basepack  # noqa: E402


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def check(folder):
    """[fault, …] for the pack in folder against the manifest."""
    faults = []
    for rel, (size, sha) in sorted(basepack.manifest()["files"].items()):
        p = os.path.join(folder, rel)
        if not os.path.isfile(p):
            faults.append("missing: " + rel)
            continue
        with open(p, "rb") as f:
            data = f.read()
        if len(data) != size or _sha(data) != sha:
            faults.append("differs: " + rel)
    return faults


def install(zip_path, folder):
    files = basepack.manifest()["files"]
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


def write_manifest(folder, path=basepack.MANIFEST):
    files = {}
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames.sort()
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, folder).replace(os.sep, "/")
            with open(full, "rb") as f:
                data = f.read()
            files[rel] = [len(data), _sha(data)]
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"version": 1, "files": files}, f, indent=2, sort_keys=True)
        f.write("\n")
    print(f"{path}: {len(files)} files")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("what", choices=("install", "check", "make", "manifest"))
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
    if a.what == "manifest":
        return write_manifest(folder)
    faults = check(folder)
    for f in faults[:20]:
        print("FAULT", f)
    n = len(basepack.manifest()["files"])
    print(f"{folder}: {n - len(faults)} of {n} files as basepack.json names "
          f"them — {'COMPLETE' if not faults else 'NOT COMPLETE'}")
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(main())
