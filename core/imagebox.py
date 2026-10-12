"""Image boxes: a picture cover-filled into a box, with pan, zoom and
edge fades — decision 4.

**ONE HOME SINCE 13 September 2026 (brief 97).** This was Empire
Identity's own renderer code, the only screen with an image box, so a
second screen that wanted one would have had to import another screen's
module or copy it. The colony screen's planet surface picture is that
second screen, so the drawing moved here and `screens/empire_identity`
imports it.

**WHAT A BOX SAYS, AND WHAT IT NEVER SAYS.** The style carries `zoom`,
`crop` ([0..1, 0..1] anchor), `fade_left` and `fade_right` (fractions of
the width, 0 = off) — properties of the box, editable and saved like
any other. It never carries WHICH picture: the caller resolves that
(Empire Identity's homeworld, the colony screen's climate) and hands the
surface in, so a mod's art is found through `core/resources.py` and no
path lands in `boxes.json` (decisions 16, 17, 19).

**THE FADE IS ALPHA, NOT A COLOUR.** The mask multiplies the picture's
alpha, so a faded edge shows whatever was drawn under the box — on the
colony screen, the panel base the cutout was filled with. No colour is
typed here and none is needed. `fade_right` is new with brief 97: the
mockup softens both sides, and a left-only fade was Empire Identity's
need, not a rule.
"""
import pygame


def cover(img, tw, th, crop, zoom):
    """Cover-fill `img` into (tw, th) with zoom and a crop anchor.
    Same semantics as the select_race portrait thumbnails."""
    iw, ih = img.get_width(), img.get_height()
    base = max(tw / iw, th / ih)
    scale = base * max(0.3, zoom)
    sw = max(tw, int(iw * scale))
    sh = max(th, int(ih * scale))
    scaled = pygame.transform.smoothscale(img, (sw, sh))
    cx = int(crop[0] * max(0, sw - tw))
    cy = int(crop[1] * max(0, sh - th))
    return scaled.subsurface((cx, cy, tw, th)).copy()


def fade_mask(w, h, fade_left=0.0, fade_right=0.0):
    """Alpha mask: transparent at a faded edge, opaque inside it.

    Each side ramps over its fraction of the width with the curve
    Empire Identity has always used, `(x / fw) ** 1.5`; the right side
    is the same ramp mirrored. Where the two would overlap the smaller
    alpha wins, so a box faded more than half from both sides stays
    symmetric rather than one ramp overwriting the other.
    """
    mask = pygame.Surface((w, h), pygame.SRCALPHA)
    mask.fill((255, 255, 255, 255))
    alphas = [255] * w
    for side, frac in (("left", fade_left), ("right", fade_right)):
        if frac <= 0:
            continue
        fw = max(1, int(w * frac))
        for i in range(min(fw, w)):
            a = int(255 * (i / fw) ** 1.5)
            x = i if side == "left" else w - 1 - i
            alphas[x] = min(alphas[x], a)
    for x, a in enumerate(alphas):
        if a < 255:
            pygame.draw.line(mask, (255, 255, 255, a), (x, 0), (x, h))
    return mask


def render_image_box(surface, L, img, rect, style, cache):
    """Draw `img` cover-filled into the reference `rect`.

    The rendered surface is cached per (size, zoom, crop, fades, image),
    so a box whose picture changes — the colony screen swaps it with the
    scanned colony's climate — rebuilds only when it has to.
    """
    if img is None:
        return
    px, py = L.pos(rect[0], rect[1])
    pw, ph = L.size(rect[2], rect[3])
    if pw < 2 or ph < 2:
        return
    zoom = float(style.get("zoom", 1.0))
    crop = tuple(style.get("crop", [0.5, 0.5]))
    fade_l = float(style.get("fade_left", 0.0))
    fade_r = float(style.get("fade_right", 0.0))
    key = (pw, ph, zoom, crop, fade_l, fade_r, id(img))
    if cache.get("key") != key:
        out = cover(img, pw, ph, crop, zoom)
        if fade_l > 0 or fade_r > 0:
            # AN ALPHA CHANNEL FIRST. A picture loaded without one would
            # take the mask's multiply on its RGB alone and fade to
            # black instead of to whatever is under the box.
            faded = pygame.Surface((pw, ph), pygame.SRCALPHA)
            faded.blit(out, (0, 0))
            faded.blit(fade_mask(pw, ph, fade_l, fade_r), (0, 0),
                       special_flags=pygame.BLEND_RGBA_MULT)
            out = faded
        cache["key"] = key
        cache["surf"] = out
    surface.blit(cache["surf"], (px, py))
