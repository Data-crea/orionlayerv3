"""The galaxy map's ship and monster icons, cut from one master per kind.

The one cut, shared by `tools/make_ship_icons.py` (setup cuts the base
pack's masters into the tree) and `core.usermod` (a master in the
player's mod folder replaces every icon cut from it — Data's decision,
work order 243). Both cut by exactly these functions, so a mod's master
comes out the way the shipped one does: four size steps per kind and, for
a monster, the Planets panel's picture.

The masters are Data's own HD pictures (work order 243, P1): they are in
the base pack and there is no extractor for them.
"""
import os

import numpy as np
from PIL import Image

from core import zoomtables as zt

#: Exported pixels per native pixel. 8 keeps step 0 at 104 px wide,
#: comfortably above the ~65 px it occupies on a 4K map.
EXPORT_SCALE = 8

#: Alpha below this is cleared. The masters are upscaled pixel art
#: with a soft halo; left in, the halo becomes a grey box once the
#: sprite is composited over the star field.
ALPHA_FLOOR = 12

#: Kinds and where their footprint comes from. "player" uses the ship
#: table, everything else the per-type monster table.
KINDS = ("player", "guardian", "amoeba", "crystal", "dragon", "eel",
         "hydra", "antaran")

SRC_REL = os.path.join("screens", "galaxy_map", "assets", "ships", "_src")
OUT_REL = os.path.join("screens", "galaxy_map", "assets", "ships")


def native_dim(kind, step):
    if kind == "player":
        return zt.ship_icon_dimension(step)
    return zt.monster_icon_dimension(kind, step)


def trim(img):
    """Crop to the visible content so the footprint means something.

    An untrimmed master carries a transparent margin, and the renderer
    fits the sprite into a native-pixel box: with the margin included
    the visible ship would come out a third too small and sit off
    centre. Cheapest possible source of a calibration bug.
    """
    a = np.array(img)
    mask = a[..., 3] > ALPHA_FLOOR
    if not mask.any():
        return img
    ys, xs = np.where(mask)
    return img.crop((int(xs.min()), int(ys.min()),
                     int(xs.max()) + 1, int(ys.max()) + 1))


def clean_alpha(img):
    a = np.array(img).astype(np.int16)
    faint = a[..., 3] <= ALPHA_FLOOR
    a[faint, 3] = 0
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def desaturate(img):
    """Force RGB to luma, alpha untouched.

    The master is greyscale to within a couple of levels, but LANCZOS
    ringing at the hard pixel-art edges pushes single channels apart by
    up to ~20. Tinting multiplies by a colour, so a stray green pixel
    survives as a stray green pixel. Cheaper to guarantee it here than
    to explain it later.
    """
    a = np.array(img).astype(np.float32)
    luma = (0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2])
    a[..., 0] = a[..., 1] = a[..., 2] = luma
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def render_step(master, kind, step):
    """One size step, exported at EXPORT_SCALE x its native footprint.

    Aspect ratio of the artwork is preserved; it is the renderer, not
    this script, that decides how the sprite sits inside the native
    box (see ships.py FIT_MODES). Fitting here would bake one choice
    into the asset and make the layout.json switch a lie.
    """
    nw, _nh = native_dim(kind, step)
    target_w = max(8, nw * EXPORT_SCALE)
    ratio = master.height / master.width
    target_h = max(8, int(round(target_w * ratio)))
    out = master.resize((target_w, target_h), Image.LANCZOS)
    out = clean_alpha(out)
    if kind == "player":
        out = desaturate(out)
    return out


#: The Planets panel's sprite file, beside the four steps (fundament 64).
PANEL_FILE = zt.MONSTER_PANEL_SPRITE_FILE


def render_panel(master):
    """The Planets panel's sprite: longest edge MONSTER_PANEL_SPRITE_PX.

    **HD EXTENSION.** One more export from the SAME master as the four
    map steps — the brief's "one source, no second set of artwork" — at
    the size the panel's 4K box needs, so the panel only scales down.
    Not an upscale of a step: the masters are 1536x1024 canvases with
    the creature 434 to 1436 px across, far above 314."""
    edge = zt.MONSTER_PANEL_SPRITE_PX
    f = edge / max(master.width, master.height)
    size = (max(1, int(round(master.width * f))),
            max(1, int(round(master.height * f))))
    return clean_alpha(master.resize(size, Image.LANCZOS))


def is_greyscale(img):
    a = np.array(img)
    vis = a[..., 3] > ALPHA_FLOOR
    if not vis.any():
        return True
    rgb = a[..., :3][vis].astype(int)
    return int((rgb.max(1) - rgb.min(1)).max()) <= 16


def files(kind):
    """The file names one master is cut into, in the kind's own folder."""
    steps = [f"{s}.png" for s in range(zt.icon_step_count())]
    return steps if kind == "player" else steps + [PANEL_FILE]


def cut(master_path, kind):
    """{file name: picture} — every icon cut from one master."""
    master = trim(Image.open(master_path).convert("RGBA"))
    out = {f"{s}.png": render_step(master, kind, s)
           for s in range(zt.icon_step_count())}
    if kind != "player":
        out[PANEL_FILE] = render_panel(master)
    return out
