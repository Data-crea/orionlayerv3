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

from core import modtexts, usermod  # noqa: E402

STYLE = os.path.join(ROOT, "assets", "shared", "hud", "style.json")
UNIVERSAL = os.path.join(ROOT, *usermod.UNIVERSAL.split("/"))

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
- **`files/<path>`** - any other picture on the list in `NAMES.txt`, at
  the path shown there.
- **`texts/<screen>/<key>.txt`** - a TEXT, by its key: `info.tab.reference`
  is `texts/info/tab.reference.txt`. Plain text, saved as UTF-8; a blank
  line starts a paragraph. Long texts wrap and scroll. OrionLayer's own
  texts are in `originals/texts/` to copy; the game's texts are listed in
  `NAMES.txt` by key only.

## If something goes wrong

Nothing you put here can break the game. A file OrionLayer cannot read,
or a name it does not know, is skipped and the original is used. Start
OrionLayer from a terminal to see one line about each such file.

## Switching it off

In the game: GAME, then SETTINGS, then **Mod folder: Off**, and restart.
Your files stay where they are; switch it on again the same way.

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


def game_art():
    """Tree path -> (w, h) of every picture `files/` can replace."""
    import pygame
    out = {}
    for pattern in usermod.GAME_ART:
        for path in sorted(glob.glob(os.path.join(ROOT, pattern))):
            if "/_src/" in path.replace(os.sep, "/"):
                continue
            rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
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
    lines += ["", "style.json                HUD style values "
              "(see originals/style.json)",
              "colour.json               the default frame colour "
              "(see originals/colour.json)", "",
              "files/<path>              pictures from the game "
              "(names only - not ours to hand out):"]
    lines += [f"  files/{rel}  {s[0]} x {s[1]}"
              for rel, s in sorted(game_art().items())]
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
