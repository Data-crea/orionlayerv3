"""The painted ships' engines pulse — work orders 221 and 222, decision 82
as amended.

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

THE PAINTED PULSE (work order 222: Data's decisions 1-3, the chat side's
7-9, confirmed): the painting stands for frame 1 — the templates the fleet
was painted from were photographed at glow frame 1, the battle draws no
other (`ship_templates.py`). Under the mask (white fully, black not at
all, grey in between) each frame sets the light to `LEVEL` times the
painting's, each pixel's hue and saturation kept (W3C SetLum,
`cbpaint.set_lum`): the painted engine keeps its colour. Frames 2 and 3
add a GLOW that reaches past the mask's edge, as the original's flame
grows: the mask pushed `SHIFT` x the reach out of the ship's back (the
mask's centre away from the hull's) and softened by `SOFT` x the reach,
at `GLOW` strength, in the painted engine's own colour (its colour spread
by the reach, at full value), laid on by "screen" and given its own alpha
where the ship has none. `REACH` is the original's growth: its flame
lengthens about a pixel by frame 3 (lit area 1.12 x), frame 2 three
quarters of that (1.09 x), in the stored drawing's pixels — the painted
factor times it on the picture.

HOW STRONG, MEASURED (decision 8, `dev:tools/engine_pulse_strength.py`):
the visible change over one cycle {1, 2, 3, 2} — the summed difference of
W3C Lum, on black, between successive frames, the painted ship brought to
the original's size as the battle shrinks it (`cbart.smooth`) — is the
original's, ship by ship (facing 0, the original's mean over its 8 owner
colours, 40 ships): `GLOW` is fitted so the median ratio of each step,
1 -> 2 and 2 -> 3, is 1 (41 ships: 1.006 and 0.996). Work order 221's lift
alone gave 0.35.

FRAME 0, ENGINES OFF (decision 9): the light under the mask (its
enclosed white-hot cores included, `filled`) times `LEVEL[0]`, and its
colour times `SAT[0]` at that light, fitted by the same measure against
the original's frame 0 (its engines off: 0.39 x frame 1's lit area at
0.80 x its light, about an eighth of its colour). Light: 0.326, down to a
third — the original's own frame 0 keeps 0.80 x 0.39 = 0.31 of its zone's
light, a second, independent reading of the same. Colour: 0, grey, the
end of the range; the original's change of colour is not reached in full
(0.84 x), because its flame pixels vanish. The original draws frame 0
for a unit that is done or captured and through `Draw_Ship_To_Bitmap_`
(`cbdraw.glow_frame`, the flare, the cloak's fade, the teleport, the
blast, the panel). A modder who paints frame 1 as well paints the
engines-off frame 0 himself: with `<…>_1.png` given, frame 0 is drawn as
painted and frames 2 and 3 are made from frame 1 (the original's own
convention, frame 0 off and frame 1 lit).

The owner's colour and the livery never touch the zone (`keep`, used by
`cbpaint`), nor the glow, which is laid on after them in the engine's
colour. A glow frame a modder paints wins for that frame (decision 3); a
picture without a mask stands still, every frame its frame 0 (decision 82
as before).

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
import math

import numpy as np
import pygame

from . import cbart

log = logging.getLogger("combat")

#: The light under the mask at glow frames 0-3 over the painting's: frame
#: 0 engines off (fitted, decision 9), frame 1 the painting, 2 and 3 the
#: original's own lift (1640 facings, work order 221).
LEVEL = (0.326, 1.0, 1.094, 1.201)
#: The colour under the mask at glow frames 0-3, as a share of the
#: painting's saturation at the same light: frame 0 loses its engine's
#: colour as the original's does (decision 9; the fit runs into 0, fully
#: grey, and still loses 0.84 x the original's colour — whose flame
#: pixels vanish altogether).
SAT = (0.0, 1.0, 1.0, 1.0)
#: The glow's strength at glow frames 0-3 (fitted, decision 8).
GLOW = (0.0, 0.0, 0.244, 0.347)
#: How far the flame grows by each glow frame, in the stored drawing's
#: pixels (the original's lit area: 1.09 x and 1.12 x, about a pixel).
REACH = (0.0, 0.0, 0.75, 1.0)
#: The glow's shape against its reach: how far the mask is pushed out of
#: the ship's back, and how soft it is.
SHIFT, SOFT = 0.6, 0.5
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
            filled(pygame.surfarray.array3d(m)[..., 0].astype(float) / 255)
    return cache[key]


def filled(m):
    """`m` with its enclosed holes white (work order 222): a hole the mask
    closes round is engine too. The chat side's masks cover the engines'
    purple, the pixels of engine hue, and leave out the white-hot cores
    the purple encloses, so a darkened engine kept a white core."""
    from PIL import Image, ImageDraw
    xs, ys = np.nonzero(m >= 0.5)
    if not len(xs):
        return m
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    out = np.full((x1 - x0 + 2, y1 - y0 + 2), 255, np.uint8)
    out[1:-1, 1:-1][m[x0:x1, y0:y1] >= 0.5] = 0
    img = Image.fromarray(np.ascontiguousarray(out.T)).copy()
    ImageDraw.floodfill(img, (0, 0), 128)
    holes = np.asarray(img).T[1:-1, 1:-1] == 255
    res = m.copy()
    res[x0:x1, y0:y1][holes] = 1.0
    return res


def blur(a, sigma):
    """`a` (w, h) or (w, h, n) under a Gaussian of `sigma` pixels in x and
    y, zeros outside; the channels of an (w, h, n) array in one pass."""
    if sigma <= 0:
        return a
    r = int(math.ceil(3 * sigma))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    for ax in (0, 1):
        pad = [(r, r) if i == ax else (0, 0) for i in range(a.ndim)]
        p = np.pad(a, pad)
        n = a.shape[ax]
        out = k[0] * (p[:n] if ax == 0 else p[:, :n])
        for i in range(1, len(k)):
            out += k[i] * (p[i:i + n] if ax == 0 else p[:, i:i + n])
        a = out
    return a


def _shifted(a, dx, dy):
    out = np.zeros_like(a)
    ix, iy = int(round(dx)), int(round(dy))
    w, h = a.shape
    if abs(ix) >= w or abs(iy) >= h:
        return out
    out[max(0, ix):w + min(0, ix), max(0, iy):h + min(0, iy)] = \
        a[max(0, -ix):w - max(0, ix), max(0, -iy):h - max(0, iy)]
    return out


def back(alpha, m):
    """The unit vector from the hull's centre to the engines' (x, y): the
    way the flame grows. Read off every second pixel: a direction, not a
    picture."""
    a, w = alpha[::2, ::2], (m * alpha)[::2, ::2]
    xs = np.arange(a.shape[0])[:, None]
    ys = np.arange(a.shape[1])[None, :]
    if a.sum() <= 0 or w.sum() <= 0:
        return 0.0, 0.0
    d = ((xs * w).sum() / w.sum() - (xs * a).sum() / a.sum(),
         (ys * w).sum() / w.sum() - (ys * a).sum() / a.sum())
    n = math.hypot(*d)
    return (d[0] / n, d[1] / n) if n > 1e-6 else (0.0, 0.0)


#: (mask id, picture size) -> (the mask, its box, the way back): the same
#: for every owner colour and livery of one picture, so found once.
_GEOMETRY = {}


def _geometry(surf, m, with_back):
    """(the mask's bounding box (x0, x1, y0, y1) or None, the way the flame
    grows) for `surf` under `m`, cached per mask."""
    key = (id(m), surf.get_size(), with_back)
    hit = _GEOMETRY.get(key)
    if hit is not None and hit[0] is m:
        return hit[1], hit[2]
    xs, ys = np.nonzero(m > 0)
    box = None if not len(xs) else \
        (int(xs.min()), int(xs.max()) + 1, int(ys.min()), int(ys.max()) + 1)
    way = (0.0, 0.0)
    if with_back and box is not None:
        view = pygame.surfarray.pixels_alpha(surf)
        way = back(view.astype(np.float32) / 255, m)
        del view
    if len(_GEOMETRY) > 256:
        _GEOMETRY.clear()
    _GEOMETRY[key] = (m, box, way)
    return box, way


def lit(surf, m, level, glow=0.0, reach=0.0, sat=1.0):
    """`surf` with the light under `m` set to `level` times its own, each
    pixel's hue and saturation kept, and a glow of strength `glow` grown
    `reach` stored-drawing pixels out of the ship's back; the painted
    factor kept. Only a box round the mask is computed: the engines are
    0.5-2.5 % of a painted ship."""
    from . import cbpaint
    k = cbart.hd_factor(surf)
    out = surf.copy()
    box, (dx, dy) = _geometry(surf, m, bool(glow))
    if box is None:
        return cbart.painted_as(out, k)
    r = reach * k
    pad = int(math.ceil(r * (SHIFT + 3 * max(SOFT, 1)))) + 1 if glow else 0
    w, h = m.shape
    x0, x1 = max(0, box[0] - pad), min(w, box[1] + pad)
    y0, y1 = max(0, box[2] - pad), min(h, box[3] + pad)
    view = pygame.surfarray.pixels_alpha(surf)
    a = view[x0:x1, y0:y1].astype(np.float32) / 255
    del view
    px = pygame.surfarray.pixels3d(out)
    rgb = px[x0:x1, y0:y1].astype(np.float32) / 255
    mm = m[x0:x1, y0:y1]
    if level != 1 or sat != 1:
        on = mm > 0
        sel, w_ = rgb[on], mm[on][:, None]
        sel = cbpaint.set_lum(sel, cbpaint._lum(sel) *
                              (1 + (level - 1) * mm[on]))
        if sat != 1:
            # towards the grey of its own light: Lum stays, colour goes
            grey = cbpaint._lum(sel)[:, None]
            sel = grey + (sel - grey) * (1 - (1 - sat) * w_)
        rgb[on] = sel
    if glow:
        lift = np.clip(blur(_shifted(mm.astype(np.float32), dx * r * SHIFT,
                                     dy * r * SHIFT), r * SOFT) * glow, 0, 1)
        # the engine's colour spread by the reach: a smooth field, so made
        # on every second pixel and stretched back (work order 222: a lit
        # frame in 2 ms instead of 9 at 8 x)
        mw = (mm * a).astype(np.float32)
        half = np.concatenate([rgb[::2, ::2] * mw[::2, ::2, None],
                               mw[::2, ::2, None]], -1).astype(np.float32)
        spread = blur(half, r / 2).repeat(2, 0).repeat(2, 1)[
            :mm.shape[0], :mm.shape[1]]
        col = spread[..., :3] / np.maximum(spread[..., 3], 1e-6)[..., None]
        col /= np.maximum(col.max(-1, keepdims=True), 1e-6)
        on = lift > 0
        pre = rgb[on] * a[on][:, None]
        pre = 1 - (1 - pre) * (1 - lift[on][:, None] * col[on])
        a[on] = a[on] + lift[on] * (1 - a[on])
        rgb[on] = pre / np.maximum(a[on], 1e-6)[:, None]
        pa = pygame.surfarray.pixels_alpha(out)
        pa[x0:x1, y0:y1] = np.clip(a * 255 + 0.5, 0, 255).astype("uint8")
        del pa
    px[x0:x1, y0:y1] = np.clip(rgb * 255 + 0.5, 0, 255).astype("uint8")
    del px
    return cbart.painted_as(out, k)


def frame(art, key, surf, lbx_name, stem, size_entry, glow, dark=True):
    """`surf`, a painted stored facing's frame (coloured as the battle
    draws it), at glow frame `glow`: made under its engine mask, else
    `surf` itself. `dark` False leaves frame 0 as painted (a modder's own
    engines-off frame). Cached under `key` + the glow (the caller's key
    names what `surf` depends on)."""
    g = max(0, min(3, int(glow)))
    if (LEVEL[g] == 1 and SAT[g] == 1 and not GLOW[g]) or \
            (g == 0 and not dark):
        return surf
    m = mask(art, lbx_name, stem, size_entry, surf.get_size())
    if m is None:
        return surf
    k = key + (g,)
    if k not in art._cache:
        art._cache[k] = lit(surf, m, LEVEL[g], GLOW[g], REACH[g], SAT[g])
    return art._cache[k]


def own(art, lbx_name, entry, stored, glow, mirror, flip):
    """A painted file's glow frame that is made (a colour's own ship, a
    MONSTER picture): from its facing's frame 1 if painted, else frame 0 —
    lit or darkened under that picture's mask (else frame 0's), else the
    picture itself — flipped as the stored drawing would be. None when the
    glow frame is painted, frame 0 is not, or nothing is made (frame 0
    without a mask, or with frame 1 painted: drawn as painted)."""
    g = max(0, min(3, int(glow)))
    if g and art._painted(lbx_name, entry, 4 * stored + g) is not None:
        return None
    if art._painted(lbx_name, entry, 4 * stored) is None:
        return None
    at = 4 * stored + 1 if g and art._painted(
        lbx_name, entry, 4 * stored + 1) is not None else 4 * stored
    base = art._painted(lbx_name, entry, at)
    stem = f"{int(entry)}_{at}"
    if mask(art, lbx_name, stem, entry, base.get_size()) is None:
        stem = f"{int(entry)}_{4 * int(stored)}"
    dark = art._painted(lbx_name, entry, 4 * stored + 1) is None
    if not g and (not dark or mask(art, lbx_name, stem, entry,
                                   base.get_size()) is None):
        return None
    key = ("pulse_own", lbx_name, int(entry), int(stored), g, mirror, flip)
    cache = art._cache
    if key not in cache:
        out = frame(art, ("pulse_own_lit", lbx_name, int(entry), at), base,
                    lbx_name, stem, entry, g, dark)
        if mirror or flip:
            out = cbart.painted_as(pygame.transform.flip(out, mirror, flip),
                                   cbart.hd_factor(out))
        cache[key] = out
    return cache[key]
