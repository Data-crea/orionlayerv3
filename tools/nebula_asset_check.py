"""Report which artwork each nebula type actually resolves to.

    python tools/nebula_asset_check.py

Answers "why are the nebulas still the old ones?" without guessing.
For every entry in layout.json's nebula_forms it prints the resolved
file, its size and its dominant hue, and flags what stops new artwork
from appearing:

  LEGACY   the forms list still names the old Form*.png artwork
  WRAP     fewer than twelve forms, so shapes repeat across types
  MOD      an active mod ships its own nebula/ and wins over the base
  MISSING  the file named in layout.json does not resolve at all
  STALE    a __pycache__ entry is newer than its source .py

Also reports the blend mode the installed renderer uses. The original
draws nebulas OPAQUE over black space (MAINSCR::Draw_Nebulae_), so
additive blending is what reproduces it over a lit HD backdrop; a flat
alpha shows the sprite's bounding box as a rectangle.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import config, resources  # noqa: E402
from core import zoomtables as zt  # noqa: E402
from screens.galaxy_map import renderer as rnd  # noqa: E402

SCREEN = "galaxy_map"
WATCH = ("screens/galaxy_map/renderer.py", "screens/galaxy_map/screen.py")
EXPECTED_FORMS = 12          # savegame.cpp validates s_nebula.type 0..11

#: An HD master may be any resolution, but not any shape: the
#: renderer sets its width from NEBULA_DIM and lets the height follow
#: the artwork. 10 % covers the redraw jitter of the current masters
#: (worst case type 2 at 4.4 %) and still catches a cropped or padded
#: canvas.
ASPECT_TOLERANCE = 0.10


def check_pycache():
    """Report a .pyc compiled from a DIFFERENT version of its source.

    File mtimes cannot answer this: importing anything from the
    project rewrites the .pyc, making it newer than the .py it was
    just built from. CPython stores the source mtime it compiled
    against in the .pyc header (bytes 8..12, PEP 552 timestamp
    format); comparing that to the source's own mtime is exact.
    """
    import struct as _struct
    stale = []
    for rel in WATCH:
        src = os.path.join(config.BASE_DIR, rel)
        if not os.path.exists(src):
            continue
        cache = os.path.join(os.path.dirname(src), "__pycache__")
        if not os.path.isdir(cache):
            continue
        stem = os.path.basename(src)[:-3]
        src_mtime = int(os.path.getmtime(src)) & 0xFFFFFFFF
        for entry in os.listdir(cache):
            if not (entry.startswith(stem + ".") and entry.endswith(".pyc")):
                continue
            pyc = os.path.join(cache, entry)
            try:
                with open(pyc, "rb") as f:
                    head = f.read(12)
                if len(head) < 12:
                    continue
                flags, recorded = _struct.unpack("<II", head[4:12])
                if flags & 0x1:      # hash-based .pyc: no timestamp
                    continue
            except OSError:
                continue
            if recorded != src_mtime:
                stale.append((rel, entry))
    return stale


def describe(path):
    """(size, hue) of an image, without requiring pygame's display."""
    try:
        from PIL import Image
    except ImportError:
        return "", "(install pillow for colour info)"
    try:
        img = Image.open(path).convert("RGBA")
    except OSError as e:
        return "", f"(unreadable: {e})"
    w, h = img.size
    px = [p for p in img.convert("RGBA").tobytes()]
    pixels = [(px[i], px[i + 1], px[i + 2], px[i + 3])
              for i in range(0, len(px), 4)]
    px = [p for p in pixels if p[3] > 60]
    if not px:
        return f"{w}x{h}", "fully transparent"
    n = len(px)
    r = sum(p[0] for p in px) / n
    g = sum(p[1] for p in px) / n
    b = sum(p[2] for p in px) / n
    if g > r and g > b:
        hue = "green"
    elif b > g and r > g:
        hue = "purple"
    elif r > g and r > b:
        hue = "red"
    elif b > r and b > g:
        hue = "blue"
    else:
        hue = "grey"
    return f"{w}x{h}", f"{hue} ({r:.0f},{g:.0f},{b:.0f})"


def footprint_line(neb_type):
    """The four native sizes this type is drawn at, zoom 0..3."""
    return "  ".join(
        f"z{z}:{w}x{h}"
        for z, (w, h) in enumerate(zt.NEBULA_DIM[neb_type % len(zt.NEBULA_DIM)]))


def aspect_deviation(neb_type, size_str):
    """Relative gap between the artwork's aspect and the original's.

    Size is taken from `describe()`'s "WxH" string so the image is not
    opened twice. Returns None when it could not be determined (no
    Pillow, unreadable file).

    Only the aspect matters now: the renderer scales to the table
    width and lets the height follow the artwork, so a master whose
    proportions drifted would silently cover the wrong patch of sky
    vertically.
    """
    if "x" not in size_str:
        return None
    try:
        w, h = (int(v) for v in size_str.split("x"))
    except ValueError:
        return None
    if not h:
        return None
    ow, oh = zt.NEBULA_DIM[neb_type % len(zt.NEBULA_DIM)][0]
    return abs((w / h) - (ow / oh)) / (ow / oh)


def load_forms(res):
    path = res.screen_file(SCREEN, "layout.json")
    if not path:
        return None, None
    import json
    with open(path, encoding="utf-8") as f:
        return json.load(f).get("nebula_forms", []), path


def main():
    settings = config.load_settings()
    res = resources.Resources(settings.get("active_mods", []),
                              settings.get("skin", "default"))
    print(f"base   : {config.BASE_DIR}")
    print(f"mods   : {res.mod_dirs or 'none active'}")

    forms, layout_path = load_forms(res)
    if forms is None:
        print("\n  MISSING: screens/galaxy_map/layout.json does not resolve.")
        return
    print(f"layout : {layout_path}")

    if hasattr(rnd, "NEBULA_BRIGHTNESS"):
        blend = f"additive, brightness {rnd.NEBULA_BRIGHTNESS}"
    elif hasattr(rnd, "NEBULA_ALPHA"):
        blend = (f"flat alpha {rnd.NEBULA_ALPHA} — OLD RENDERER: this "
                 "draws the sprite's\n         bounding box as a "
                 "rectangle over a lit background")
    else:
        blend = "unknown (renderer has neither constant)"
    print(f"blend  : {blend}")
    print(f"forms  : {len(forms)}\n")

    print("  footprint = native pixels from zoomtables.NEBULA_DIM "
          "(zoom 0..3);\n  the artwork's own resolution does not "
          "affect size, only its aspect.\n")

    legacy = missing = modded = skewed = 0
    for i, form in enumerate(forms):
        path = res.screen_file(SCREEN, "assets", "nebula", f"{form}.png")
        if not path:
            print(f"  [{i:2d}] {form:10s} MISSING")
            missing += 1
            continue
        size, hue = describe(path)
        marks = []
        if any(path.startswith(m) for m in res.mod_dirs):
            marks.append("MOD")
            modded += 1
        if not form.startswith("type_"):
            marks.append("LEGACY")
            legacy += 1
        dev = aspect_deviation(i, size)
        if dev is not None and dev > ASPECT_TOLERANCE:
            marks.append(f"ASPECT {dev * 100:.0f}%")
            skewed += 1
        print(f"  [{i:2d}] {form:10s} {size:10s} {hue:22s} "
              f"{' '.join(marks)}")
        print(f"       footprint {footprint_line(i)}")

    stale = check_pycache()
    print()
    if legacy:
        print(f"  {legacy} entr(ies) still name the old Form* artwork.")
        print("  -> layout.json nebula_forms should be "
              "type_00 .. type_11")
    if len(forms) and len(forms) < EXPECTED_FORMS:
        print(f"  WRAP: {len(forms)} forms for {EXPECTED_FORMS} nebula "
              "types — shapes repeat.")
    if missing:
        print(f"  {missing} form(s) resolve to nothing at all.")
    if modded:
        print(f"  {modded} form(s) come from an active mod, not the "
              "base project.")
    if skewed:
        print(f"  ASPECT: {skewed} master(s) deviate more than "
              f"{ASPECT_TOLERANCE * 100:.0f}% from the original shape.")
        print("  -> the sprite covers the wrong patch of sky "
              "vertically; recrop the canvas.")
    if stale:
        for rel, entry in stale:
            print(f"  STALE  {entry} was compiled from another version of {rel}")
        print("  -> rm -rf screens/galaxy_map/__pycache__")
    if not (legacy or missing or stale) and len(forms) == EXPECTED_FORMS:
        print("  All twelve types resolve to extracted artwork in the "
              "base project.")
        print("  If the game still shows the old nebulas, OrionLayer "
              "was started")
        print("  before the update landed — restart it.")


if __name__ == "__main__":
    main()
