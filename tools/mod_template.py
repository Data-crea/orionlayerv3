#!/usr/bin/env python3
"""Make a ready-to-edit mod folder — HD EXTENSION, work order 173, decision 72.

    python tools/mod_template.py              # the player's mod folder
    python tools/mod_template.py --to DIR     # anywhere else outside the tree

Writes a plain-language `MODDING.md`, a `NAMES.txt` listing every name
the folder can hold with its size and format, and STARTING POINTS under
`originals/` — OrionLayer's own files, which change nothing until one is
copied up a level:

    originals/background.png     Data's universal background
    originals/hud/<piece>.png    the HUD icons and the title plate, cut
                                 from Data's HUD (`tools/hud_cut.py`)
    originals/style.json         every HUD style value
    originals/colour.json        the measured frame colour
    originals/texts/<screen>/…   OrionLayer's OWN texts, by key (work
                                 order 175, `core/modtexts`) — the game's
                                 texts are listed in NAMES.txt by key only

**NEVER A MOO2 FILE.** Pictures extracted from the game, or derived from
its artwork (LICENSE, "Artwork derived from Master of Orion 2"), and the
game's fonts and texts are not ours to hand out: for those `NAMES.txt`
gives the NAME and size only. The smoke suite holds every file this tool
writes to that rule.

**NEVER INSIDE THE TREE, NEVER OVER THE PLAYER'S FILES.** A target in
the repository is refused; a file that already exists is left as it is
and reported.
"""
import argparse
import glob
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Work order 182: SDL's dummy drivers FORCED, never a window or a sound in
# the user's session.
import vdisplay  # noqa: E402
vdisplay.headless_clients()

from core import basepack, modart, modtexts, usermod  # noqa: E402
from screens.colony_summary import colonyplanets  # noqa: E402

STYLE = os.path.join(ROOT, "assets", "shared", "hud", "style.json")
UNIVERSAL = basepack.source(usermod.UNIVERSAL, ROOT)  # the base pack, WO 241

GUIDE = """# Your OrionLayer mod folder

This folder changes how OrionLayer looks. You do not need to know any
programming: you put a picture in here with the right name, restart
OrionLayer, and it is used instead of the built-in one.

**Where it is:** `{folder}`

## How it works

1. Find the name you want in `NAMES.txt`.
2. Put your file here under exactly that name.
   Everything in `originals/` is OrionLayer's own version, ready to edit:
   copy it up here (out of `originals/`) and change it.
3. Restart OrionLayer.

A file you do not put here stays OrionLayer's own. Delete your file and
the original comes back.

## What you can change

- **`background.png`** - the picture behind every screen. Best at
  3840 x 2160 (PNG or JPG). Any size works: it is scaled to fill the
  window without stretching, and the edges are cut off evenly.
- **`backgrounds/<screen>.png`** - a picture for ONE screen, for example
  `backgrounds/galaxy_map.png`. It wins over `background.png`. The screen
  names are in `NAMES.txt`.
- **`hud/<piece>.png`** - the icons on the buttons and the title plate
  at the top. A picture of another size is scaled to the original's size.
- **`style.json`** - the colours and sizes of the frames. Copy
  `originals/style.json` here and change the values you want. You may
  delete every line you do not change: only the values in your file
  count.
- **`colour.json`** - the frame colour OrionLayer starts with:
  `hue` 0 to 360, `saturation` 0 to 1, `brightness` 0.1 to 1.6. The
  colour you pick in the game's settings still wins over it, and
  "Reset" there goes back to this file's colour.
- **`frames/<screen>.png`** - a FRAME painted over one screen, 3840 x
  2160 with transparency. `templates/frames/<screen>.png` shows where the
  screen's boxes are: paint over it and save it under `frames/`. It is
  drawn only while the window is 16:9 and only for the layout it was
  painted for; when a screen's boxes move, a new template is written and
  the old frame waits for a repaint (one line in the log says why). If
  your paint program drops the template's hidden stamp, name it in a
  `mod.json`: `{{"frames": {{"<screen>": "<stamp>"}}}}` -
  `python tools/frame_template.py` prints every stamp.
- **`files/<path>`** - any other picture on the list in `NAMES.txt`, at
  the path shown there; the battle's pictures too, one PNG per drawing;
  and the colony screen's landscape, one PNG per climate at the size
  `NAMES.txt` gives (`files/screens/colony/assets/surfaces/terran.png`);
  and the Leaders screen's pictures - its background, one picture per
  row while a leader stands in it, the empty row and the galaxy map box
  (`files/screens/leaders/assets/pictures/slot_1_background.png`). Paint
  them without a frame: OrionLayer draws the frame round them.
  The galaxy map's ships and monsters go two ways: one icon
  (`files/screens/galaxy_map/assets/ships/<kind>/2.png`) replaces exactly
  that icon; a whole master
  (`files/screens/galaxy_map/assets/ships/_src/<kind>.png`) replaces every
  icon cut from it - OrionLayer cuts it at the next start. A single icon
  beside a master still wins.
- **`texts/<screen>/<key>.txt`** - a TEXT, by its key: `info.tab.reference`
  is `texts/info/tab.reference.txt`. Plain text, saved as UTF-8; a blank
  line starts a paragraph. Long texts wrap and scroll. OrionLayer's own
  texts are in `originals/texts/` to copy; the game's texts are listed in
  `NAMES.txt` by key only.

## If something goes wrong

Nothing you put here can break the game. A file OrionLayer cannot read,
or a name it does not know, is skipped and the original is used. Start
OrionLayer from a terminal to see one line about each such file.

## Switching it on and off

The folder is **Off** until you switch it on (work order 197). In the
game: GAME, then SETTINGS, then **Mod folder: On**. Switching it on
extracts the game's pictures you have not extracted yet - this can take a
while, the row shows how far it is - and writes this guide, `NAMES.txt`
and the frame templates; then restart. **Mod folder: Off** the same
way, and restart: your files stay where they are.

## What is not here

Pictures and texts from Master of Orion 2 itself are not copied into
`originals/`: they belong to the game's owners. `NAMES.txt` lists their
names, so you can make your own.
"""


def pieces(tmp_out):
    """The HUD pieces, cut fresh from Data's HUD into `tmp_out`."""
    import hud_cut
    return hud_cut.write(tmp_out)


def screen_names():
    """Every screen that stands on a background — not the two overlays,
    which draw over the galaxy map and have none of their own."""
    base = os.path.join(ROOT, "screens")
    out = []
    for n in sorted(os.listdir(base)):
        path = os.path.join(base, n, "screen.py")
        if n.startswith("_") or not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as handle:
            if "IS_OVERLAY = True" not in handle.read():
                out.append(n)
    return out


def frame_screens():
    """The screens with a frame slot: those that place boxes
    (`core.frameslot.layout_hash` is None for the others)."""
    base = os.path.join(ROOT, "screens")
    return sorted(n for n in os.listdir(base) if not n.startswith("_")
                  and os.path.isfile(os.path.join(base, n, "screen.py"))
                  and os.path.isfile(os.path.join(base, n, "boxes.json")))


def game_art():
    """Tree path -> (w, h) of every picture `files/` can replace."""
    import pygame
    out = {}
    # the tree's extracted pictures and, since work order 241, the base
    # pack's own (the same tree paths; the tree's file first)
    found = {}
    for root in (basepack.base_dir(), ROOT):
        for pattern in modart.GAME_ART:
            for path in glob.glob(os.path.join(root, pattern)):
                found[os.path.relpath(path, root).replace(os.sep, "/")] = path
    for rel, path in sorted(found.items()):
        if modart.art_class(rel) != "game":
            continue                    # a source (`modart.SOURCES`)
        try:
            out[rel] = pygame.image.load(path).get_size()
        except pygame.error:
            continue
    return out


def names_txt(hud_sizes):
    from PIL import Image
    w, h = Image.open(UNIVERSAL).size
    lines = ["Every name this folder can hold. Sizes are the built-in "
             "file's; another size is scaled.", "",
             f"background.png            the universal background "
             f"(built-in {w} x {h}; 3840 x 2160 recommended), PNG or JPG",
             "", "backgrounds/<screen>.png  one screen's background, "
             "PNG or JPG, any size:"]
    lines += [f"  backgrounds/{n}.png" for n in screen_names()]
    lines += ["", "hud/<piece>.png           PNG with transparency:"]
    lines += [f"  hud/{n}.png  {s[0]} x {s[1]}"
              for n, s in sorted(hud_sizes.items())]
    lines += ["", "frames/<screen>.png       a frame painted over the "
              "screen (work order 197): 3840 x 2160 PNG with transparency,",
              "                          drawn only in a 16:9 window and "
              "only for the layout it was painted for -",
              "                          paint over templates/frames/"
              "<screen>.png (tools/frame_template.py writes them):"]
    lines += [f"  frames/{n}.png" for n in frame_screens()]
    lines += ["", "style.json                HUD style values "
              "(see originals/style.json)",
              "colour.json               the default frame colour "
              "(see originals/colour.json)", "",
              "files/<path>              pictures from the game "
              "(names only - not ours to hand out):"]
    lines += [f"  files/{rel}  {s[0]} x {s[1]}"
              for rel, s in sorted(game_art().items())]
    lines += ship_masters()
    lines += ["", "  the battle's pictures (work order 197), one PNG per "
              "stored drawing, used as painted:",
              "  files/screens/combat/assets/gamedata/<file>/<entry>_<frame>"
              ".png  (<file>: cmbtshp, monster, cmbtplnt, cmbtmisl, "
              "cmbtfgtr, cmbtsfx, beams, sphersfx, combat;",
              "  ships: entry = colour x 45 + design picture, frame = 4 x "
              "facing (0-4, the rest are flips) + glow (0-3))",
              "", "  Fleets, Leaders, Races, the Ship Designer, the "
              "audience (work order 199) and the Tech Review (272), the "
              "same way:",
              "  files/screens/<screen>/assets/gamedata/<group>/<entry>_"
              "<frame>.png  for the extracted <group>/<entry>.bin",
              "", "  the colony screen's surface (work order 232), one PNG "
              "per climate in the screen's format",
              "  (" + ", ".join(f"{w} x {h} at {ww} x {wh}" for (ww, wh), (
                  w, h) in surface_sizes()) +
              "; drawn instead of the game's picture):"]
    lines += [f"  files/screens/colony/assets/surfaces/{n}.png"
              f"  (or {n}_0.png, {n}_1.png, {n}_2.png per ground)"
              for n in colonyplanets.NAMES]
    lines += ["", "  the Leaders screen's pictures (work order 237), each "
              "used only while the folder is on; a missing one",
              "  leaves its box as it is. Any size of roughly the shape "
              "given: scaled to fill the box, never",
              "  stretched, the overflow cut off evenly (the empty slot's "
              "on the right). Sizes are the box at 3840 x 2160:"]
    lines += leaders_pictures()
    lines += ["", "  the galaxy map's ship pictures (work order 311), by the "
              "ship's picture number (45 colony ship,",
              "  46 outpost ship, 47 transport; 0-44 a warship's), facing "
              "right, any size; grey takes the owner's colour:",
              "  files/screens/galaxy_map/assets/ship_pictures/"
              "all_<picture>.png  every player",
              "  files/screens/galaxy_map/assets/ship_pictures/"
              "<colour>_<picture>.png  one colour (0-7), as painted"]
    lines += ["", "texts/<screen>/<key>.txt  a text by its key, UTF-8. "
              "OrionLayer's own (a copy is in originals/texts/):"]
    keys = text_keys()
    lines += [f"  {modtexts.file_name(k)}" for k, src in keys.items()
              if src == "own"]
    lines += ["", "  the game's texts (keys only - not ours to hand out; "
              "OrionLayer reads them from your own game files):"]
    lines += [f"  {modtexts.file_name(k)}" for k, src in keys.items()
              if src == "moo2"]
    return "\n".join(lines) + "\n"


def ship_masters():
    """NAMES.txt's lines for the galaxy map's ships and monsters, both ways
    (work order 243, Data's decision): one icon, or a whole master."""
    from PIL import Image
    from core import shipcut
    out = ["", "  the galaxy map's ships and monsters (work order 243), two "
           "ways:",
           f"  files/{usermod.SHIP_ICONS}/<kind>/<file>  ONE icon: replaces "
           "exactly that icon (the files listed above)",
           f"  files/{usermod.SHIP_MASTERS}/<kind>.png  a WHOLE master: "
           "every icon of that kind is cut from it -",
           "    the four steps 0.png .. 3.png and, for a monster, panel.png "
           "(the Planets panel); a single icon beside it still wins.",
           "    The player's master must be greyscale (it is tinted per "
           "colour). Kinds, with the shipped master's size",
           f"    (Data's own pictures, in the base pack under "
           f"{shipcut.SRC_REL.replace(os.sep, '/')}/):"]
    for kind in shipcut.KINDS:
        path = basepack.source(os.path.join(shipcut.SRC_REL, f"{kind}.png"),
                               ROOT)
        size = (f"{Image.open(path).width} x {Image.open(path).height}"
                if os.path.isfile(path) else "none shipped - yours adds it")
        out.append(f"  files/{usermod.SHIP_MASTERS}/{kind}.png  {size}")
    return out


def leaders_pictures():
    """NAMES.txt's lines for the Leaders screen's eight picture places
    (`screens/leaders/ldrpics`), with the size each box has at 3840x2160."""
    from screens.leaders import ldrpics
    what = {"screen": "the screen's own background, the whole window",
            "slot_empty": "a row with no leader; HD writes the caption",
            "minimap": "the galaxy box, under the stars and fleets",
            "view": "the colony view's star in space, under the orbits"}
    out = []
    for place, name in ldrpics.NAMES.items():
        size = ldrpics.RECOMMENDED["slot" if place.startswith("slot")
                                   else place]
        label = what.get(place) or (f"row {place[-1]} while a leader "
                                    f"stands in it")
        out.append(f"  files/{ldrpics.FOLDER}/{name}  {size[0]} x {size[1]}"
                   f"  ({label})")
    return out


def surface_sizes():
    """[((window w, h), (picture w, h))]: the colony surface's format at
    the two 16:9 sizes a painter works from (`colsurface.format_size`)."""
    from core.layout import Layout
    from screens.colony import colsurface
    return [(size, colsurface.format_size(Layout(*size)))
            for size in ((1920, 1080), (3840, 2160))]


def text_keys():
    """{key: source} of every registered text (`core/modtexts`)."""
    return modtexts.keys()


def own_texts():
    """{mod file name: OrionLayer's own default} — the texts the template
    may copy. A "moo2" default is never read here (MOO2 rule)."""
    out = {}
    for key, src in text_keys().items():
        if src == "own":
            value = modtexts._registry[key][0]
            if isinstance(value, str) and value:
                out[modtexts.file_name(key)] = value
    return out


def make(target, log=print):
    """Write the template into `target`. Returns the files written."""
    target = os.path.abspath(target)
    if os.path.commonpath([target, ROOT]) == ROOT:
        raise SystemExit(f"refused: {target} is inside OrionLayer's tree — "
                         f"the mod folder lives outside it")
    import pygame
    pygame.init()
    written, kept = [], []
    staged = os.path.join(target, usermod.ORIGINALS, "hud")
    os.makedirs(staged, exist_ok=True)
    tmp = os.path.join(target, usermod.ORIGINALS, ".cut")
    hud_sizes = {}
    for name in pieces(tmp):
        src = os.path.join(tmp, name + ".png")
        hud_sizes[name] = pygame.image.load(src).get_size()
        _put(src, os.path.join(staged, name + ".png"), written, kept)
    shutil.rmtree(tmp)
    _put(UNIVERSAL, os.path.join(target, usermod.ORIGINALS,
                                 "background.png"), written, kept)
    _put(STYLE, os.path.join(target, usermod.ORIGINALS, "style.json"),
         written, kept)
    from core.hud import tint
    colour = {"_note": "copy this file up one folder to use it",
              "hue": tint.REFERENCE, "saturation": 1.0, "brightness": 1.0}
    _text(json.dumps(colour, indent=2) + "\n",
          os.path.join(target, usermod.ORIGINALS, "colour.json"),
          written, kept)
    for name, value in own_texts().items():
        _text(value + "\n", os.path.join(target, usermod.ORIGINALS,
                                          *name.split("/")), written, kept)
    for sub in ("backgrounds", "hud", "files", "texts"):
        os.makedirs(os.path.join(target, sub), exist_ok=True)
    _text(GUIDE.format(folder=target), os.path.join(target, "MODDING.md"),
          written, kept)
    _text(names_txt(hud_sizes), os.path.join(target, "NAMES.txt"),
          written, kept)
    for path in kept:
        log(f"kept (already there): {path}")
    log(f"{len(written)} file(s) written to {target}")
    return written


def _put(src, dst, written, kept):
    if os.path.exists(dst):
        kept.append(dst)
        return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst)
    written.append(dst)


def _text(text, dst, written, kept):
    if os.path.exists(dst):
        kept.append(dst)
        return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w", encoding="utf-8") as handle:
        handle.write(text)
    written.append(dst)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--to", default=None,
                    help=f"the folder to write (default {usermod.mod_dir()})")
    args = ap.parse_args()
    make(args.to or usermod.mod_dir())
    return 0


if __name__ == "__main__":
    sys.exit(main())
