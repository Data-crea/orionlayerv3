"""
Constants, paths, reference resolution.
Nothing here changes at runtime.
"""
import json
import os

# --- Reference resolution ---
# All coordinates in boxes.json live in this space.
# layout.py scales from here to the actual window.
REF_W = 1920
REF_H = 1080

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_PATH = os.path.join(BASE_DIR, "settings.json")
SCREENS_DIR = os.path.join(BASE_DIR, "screens")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
SHARED_DIR = os.path.join(ASSETS_DIR, "shared")
SKINS_DIR = os.path.join(SHARED_DIR, "skins")
FONTS_DIR = os.path.join(SHARED_DIR, "fonts")
MODS_DIR = os.path.join(BASE_DIR, "mods")

# --- FPS ---
TARGET_FPS = 60

# --- orion2re engine version ---
# Shown on the main menu, bottom right, exactly like the original.
#
# Maintained BY HAND, because the Extension API does not report it:
# HELLO_REPLY carries only PROTO_VERSION (the wire protocol), and the
# state snapshot has no version field. Sending it would mean patching
# orion2re, which we deliberately do not do — see
# doc/ext_api_dokumentation_v3.md, "What the snapshot deliberately
# omits".
#
# Source of truth, in orion2re:
#   src/version.h:10        ENGINE_VERSION[] = "1.60.0"
#   src/game/consts.h:43    GAME_VERSION_LABEL[] = "Version 1.60.0"
#
# A hand-copied number in a foreign tree drifts silently, so it has a
# check instead of a reminder:  python tools/version_check.py
ORION2RE_VERSION = "1.60.0"


def load_settings():
    """Load settings.json. Returns defaults if not found."""
    if os.path.exists(SETTINGS_PATH):
        with open(SETTINGS_PATH, "r") as f:
            return json.load(f)
    return {
        # Cursor height as a share of window height. 4.38 % is the
        # original's own proportion (21 of 480 lines); the artwork is
        # 4K-sized and gets scaled down to match. See core/cursor.py.
        "cursor": {
            "enabled": True,
            "height_fraction": 0.04375,
        },
        "window": {
            "width": REF_W,
            "height": REF_H,
            "fullscreen": False,
            "resizable": True,
            "vsync": True,
            "min_width": 1280,
            "min_height": 720,
        },
        "render_mode": "hd",
        # THE COLONY FRAME FLAGS ARE GONE — Phase B, 12 September
        # 2026. `frame_preview` chose between a built plate and the
        # shipped artwork and `colony_plateless` drew every box by
        # code with no artwork at all; the screen wears one fixed
        # image now (decision 55) and neither has anything left to
        # choose. Stated here because this dict is what a clone with
        # no settings.json gets, and a stale key in it is a key
        # somebody will try to set.
        "skin": "default",
        "active_mods": [],
    }


# --- Which OrionLayer is running (work order 139 C) ------------------
#
# A DIAGNOSTIC DEGRADES, IT DOES NOT CRASH. Work order 138 could not
# say which commit Data's run was on, because nothing logged it — and
# the answer decided whether a rule that had never run live was even
# in that build. So the first line of every log says it.
#
# git is asked, not a file: a version written into the tree is the
# hand-copied number decision 36 is about, and this one has no checker
# it could be held to. Everything that can fail is a state with a
# word: no git, no repository, a timeout, a non-zero exit — all of
# them "unknown", never an exception out of a log call.

#: What is reported when git cannot answer. One word, so a log line
#: reads the same shape either way.
UNKNOWN_BUILD = "unknown"


def build_id(root=None, timeout=3.0):
    """`(commit, dirty)` for the tree this file is in.

    `commit` is the short hash or `UNKNOWN_BUILD`; `dirty` is True
    when the working tree has changes, False when it is clean, and
    None when git could not say. Raises nothing.
    """
    import subprocess
    root = root or BASE_DIR
    try:
        rev = subprocess.run(
            ["git", "-C", root, "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=timeout)
        if rev.returncode != 0 or not rev.stdout.strip():
            return UNKNOWN_BUILD, None
        status = subprocess.run(
            ["git", "-C", root, "status", "--porcelain"],
            capture_output=True, text=True, timeout=timeout)
        dirty = (bool(status.stdout.strip())
                 if status.returncode == 0 else None)
        return rev.stdout.strip(), dirty
    except (OSError, ValueError, subprocess.SubprocessError):
        return UNKNOWN_BUILD, None


def build_line():
    """The one line a log starts with."""
    commit, dirty = build_id()
    if commit == UNKNOWN_BUILD:
        state = UNKNOWN_BUILD
    else:
        state = ("modified" if dirty else
                 "clean" if dirty is False else UNKNOWN_BUILD)
    return (f"OrionLayer {commit} ({state}), "
            f"orion2re {ORION2RE_VERSION}")
