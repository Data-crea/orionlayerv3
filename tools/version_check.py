#!/usr/bin/env python3
"""Check ORION2RE_VERSION against orion2re's own source.

The version shown on the main menu is maintained by hand, because
the Extension API does not report it: HELLO_REPLY carries only
PROTO_VERSION and the state snapshot has no version field. A number
copied out of somebody else's tree drifts silently, so this turns
"did Joe bump the version?" into a command instead of a memory task.

It reads the two places orion2re keeps it:

    src/version.h        ENGINE_VERSION[] = "<x.y.z>"
    src/game/consts.h    GAME_VERSION_LABEL[] = "Version <x.y.z>"

Those two are separate literals in orion2re, not one derived from
the other, so they can disagree with each other as well as with us.
All three are reported.

Usage (from the project root):
    python tools/version_check.py
    python tools/version_check.py ~/some/other/orion2re

Exit codes: 0 all three agree, 1 a mismatch, 2 the source tree was
not found (checked, not crashed — an unreachable tree is not the
same answer as a wrong version).
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

from core.config import ORION2RE_VERSION  # noqa: E402

DEFAULT_TREES = ["~/orion2re", "~/src/orion2re", "/tmp/orion2re-main"]

RE_ENGINE = re.compile(
    r'ENGINE_VERSION\s*\[\s*\]\s*=\s*"([^"]+)"')
RE_LABEL = re.compile(
    r'GAME_VERSION_LABEL\s*\[\s*\]\s*=\s*"([^"]+)"')


def find_tree(argv):
    """First existing candidate tree, or None."""
    candidates = argv[1:] if len(argv) > 1 else DEFAULT_TREES
    for cand in candidates:
        path = os.path.expanduser(cand)
        if os.path.isfile(os.path.join(path, "src", "version.h")):
            return path
    return None


def grep(path, pattern):
    """First capture group of pattern in path, or None."""
    if not os.path.isfile(path):
        return None
    with open(path, "r", errors="replace") as f:
        match = pattern.search(f.read())
    return match.group(1) if match else None


def main():
    tree = find_tree(sys.argv)
    print(f"OrionLayer  core/config.ORION2RE_VERSION : "
          f"{ORION2RE_VERSION}")

    if not tree:
        looked = sys.argv[1:] or DEFAULT_TREES
        print("\norion2re source not found — looked in: "
              + ", ".join(looked))
        print("Pass the path:  python tools/version_check.py "
              "~/path/to/orion2re")
        return 2

    print(f"orion2re    {tree}")
    engine = grep(os.path.join(tree, "src", "version.h"), RE_ENGINE)
    label = grep(os.path.join(tree, "src", "game", "consts.h"),
                 RE_LABEL)
    print(f"            src/version.h ENGINE_VERSION      : "
          f"{engine or '(not found)'}")
    print(f"            src/game/consts.h VERSION_LABEL   : "
          f"{label or '(not found)'}")

    problems = []
    if engine is None:
        problems.append("ENGINE_VERSION not found in src/version.h")
    elif engine != ORION2RE_VERSION:
        problems.append(
            f"engine is {engine}, OrionLayer says {ORION2RE_VERSION}"
            " — update core/config.ORION2RE_VERSION")
    if label is None:
        problems.append(
            "GAME_VERSION_LABEL not found in src/game/consts.h")
    elif engine and label != f"Version {engine}":
        # orion2re's own two literals disagreeing is Joe's bug, not
        # ours, but it decides which string the main menu shows.
        problems.append(
            f"orion2re disagrees with itself: label is {label!r}, "
            f"engine is {engine!r}")

    if problems:
        print("\nMISMATCH")
        for line in problems:
            print(f"  - {line}")
        return 1

    print("\nOK — all three agree")
    return 0


if __name__ == "__main__":
    sys.exit(main())
