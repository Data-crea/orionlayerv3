"""The painted ships' engines pulse — work order 221, decision 82 as amended.

HD EXTENSION `engine_pulse` (Data's decision 1 of work order 221; 2-5
proposed by the chat side): a painted battle picture brings one frame per
facing, and its glow frames 1-3 are MADE from it at runtime — the engines
lit up and down as the original's are — where an ENGINE MASK says where the
engines are. The original has no rule like it: it draws four stored frames
per facing, painted by hand.

THE ORIGINAL, transcribed (`Draw_Ship_`, cmbtdrw1.cpp:2498-2615): frame 0
of a facing is the ship with its engines off; frames 1-3 are its engines
lit, and the battle draws a player's or an Antaran's ship at
`{1, 2, 3, 2}[(_ship_frame / 2 + unit) % 4]` — a monster at
`(_ship_frame / 2) % 4` — so every ship runs the cycle low, middle, high,
middle, phased by its unit number (`cbdraw.glow_frame`, the clock
`screen.ship_frame`, a step every 55 ms; measured on orion2re's own window
by work orders 202 G and 221: 79 steps in 4.3 s, three states per engine in
the order A B C B). Frame 0 is drawn for a unit that is done or captured
(:2563-2566) and wherever the battle redraws a ship through
`Draw_Ship_To_Bitmap_` (:2683-2711: the shield flare, the cloak's fade, the
teleport, the death blast), which HD draws at glow 0 likewise.

WHAT A LIT FRAME IS, measured on the original's own drawings (40 player
ships and the Doom Star, every owner colour, five stored facings: 1640
facings; `dev:tools/engine_pulse_measure.py`): the frames differ only in
the engine zone, at the ship's back; its hue stays (about 263 degrees);
against frame 1 its mean lightness (W3C Lum) is 1.094 x in frame 2 and
1.201 x in frame 3 (p10-p90 1.03-1.15 and 1.10-1.32), and its lit area
1.09 x and 1.12 x — the flame lengthens by about a pixel at 1 x. Frame 0
has 0.39 x frame 1's lit area at 0.80 x its light: the engines off.

THE PAINTED PULSE: the painting stands for frame 1 — the templates the
fleet was painted from were photographed at glow frame 1, the battle draws
no other (`ship_templates.py`) — and frame 0 is the painting too; frames 2
and 3 lift the light of the pixels under the mask by `LEVEL`, weighted by
the mask (white lit fully, black not at all, grey in between), keeping each
pixel's hue and saturation (W3C SetLum, `cbpaint.set_lum`): the painted
engine keeps its colour, only its light changes (decision 4); the zone does
not grow. The owner's colour and the livery never touch the zone
(`keep`, used by `cbpaint`). A glow frame a modder paints wins for that
frame (decision 3); a picture without a mask stands still, every frame its
frame 0 (decision 82 as before).

THE MASK: `<stem>_engine.png` beside the picture, `<stem>` the picture's
name without `.png` — `all_<picture>_<frame>_engine.png` for a colour-free
ship, `<colour * 45 + picture>_<frame>_engine.png` for a colour's own,
`<entry>_<frame>_engine.png` in monster/ — greyscale at the picture's size,
read through the picture's own loader (held as it is, decision 83); one of
another size is not used, with one log line. It is applied to the stored
facing's picture before that is turned, mirrored or flipped, so it follows
the picture through all of them, the detail setting's shrinking, the cloak
and the flare (decision 82's rule for masks).
"""
import logging

import numpy as np
import pygame

from . import cbart

log = logging.getLogger("combat")

#: The light of glow frames 0-3 over the painting's (measured, see above):
#: the painting is frame 1, frame 0 is drawn as painted too.
LEVEL = (1.0, 1.0, 1.094, 1.201)
#: The engine mask's suffix after the picture's own name.
SUFFIX = "_engine.png"


def mask_name(stem):
    return f"{stem}{SUFFIX}"


def mask(art, lbx_name, stem, size_entry, size):
    """The engine mask of the painted picture `<lbx>/<stem>.png`, 0..1
    (w, h), or None: read and held as its picture (`painted_file`); one of
    another size than `size` is not used, with one log line."""
    key = ("engine_mask", lbx_name, stem)
    cache = art._cache
    if key not in cache:
        m = art.painted_file(lbx_name, mask_name(stem), int(size_entry))
        if m is not None and m.get_size() != tuple(size):
            log.warning("combat: %s is %d x %d, its picture %d x %d — not "
                        "used", mask_name(stem), *m.get_size(), *size)
            m = None
        cache[key] = None if m is None else \
            pygame.surfarray.array3d(m)[..., 0].astype(float) / 255
    return cache[key]


def lit(surf, m, level):
    """`surf` with the light under `m` lifted `level` times, each pixel's
    hue and saturation kept; alpha, everything outside the mask and the
    painted factor as they were. Only the mask's bounding box is computed:
    the engines are 0.5-2.5 % of a painted ship."""
    from . import cbpaint
    out = surf.copy()
    xs, ys = np.nonzero(m > 0)
    if level != 1 and len(xs):
        x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        px = pygame.surfarray.pixels3d(out)
        rgb = px[x0:x1, y0:y1].astype(float) / 255
        w = m[x0:x1, y0:y1]
        lum = cbpaint._lum(rgb) * (1 + (level - 1) * w)
        px[x0:x1, y0:y1] = np.clip(cbpaint.set_lum(rgb, lum) * 255 + 0.5,
                                   0, 255).astype("uint8")
        del px
    return cbart.painted_as(out, cbart.hd_factor(surf))


def frame(art, key, surf, lbx_name, stem, size_entry, glow):
    """`surf`, a painted stored facing's frame 0 (coloured as the battle
    draws it), at glow frame `glow`: lit under its engine mask, else `surf`
    itself. Cached under `key` + the glow (the caller's key names what
    `surf` depends on)."""
    level = LEVEL[max(0, min(3, int(glow)))]
    if level == 1:
        return surf
    m = mask(art, lbx_name, stem, size_entry, surf.get_size())
    if m is None:
        return surf
    k = key + (int(glow),)
    if k not in art._cache:
        art._cache[k] = lit(surf, m, level)
    return art._cache[k]


def own(art, lbx_name, entry, stored, glow, mirror, flip):
    """A painted file's missing glow frame (a colour's own ship, a MONSTER
    picture): made from its facing's frame 0 — lit under its mask, else
    frame 0 itself, flipped as the stored drawing would be. None when glow
    is 0, the glow frame is painted, or frame 0 is not."""
    g = max(0, min(3, int(glow)))
    if not g or art._painted(lbx_name, entry, 4 * stored + g) is not None:
        return None
    base = art._painted(lbx_name, entry, 4 * stored)
    if base is None:
        return None
    key = ("pulse_own", lbx_name, int(entry), int(stored), g, mirror, flip)
    cache = art._cache
    if key not in cache:
        out = frame(art, ("pulse_own_lit", lbx_name, int(entry),
                          int(stored)), base, lbx_name,
                    f"{int(entry)}_{4 * int(stored)}", entry, g)
        if mirror or flip:
            out = cbart.painted_as(pygame.transform.flip(out, mirror, flip),
                                   cbart.hd_factor(out))
        cache[key] = out
    return cache[key]
