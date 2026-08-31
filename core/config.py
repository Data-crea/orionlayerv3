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
        "skin": "default",
        "active_mods": [],
    }
