"""Runtime-tinted MOO2 banners.

Two banner types, one principle: a greyscale cloth layer is tinted
into the eight MOO2 colours at runtime, the race emblem is embedded
into the folds, and the metal frame lies on its own untouched layer.

  BANNER_TILE      framed banner        1254x1254  (selection tile)
  BANNER_STAND_HD  banner on a stand    1338x1175  (detail / preview)
  BANNER_STAND     same, low resolution  300x367   (legacy)

8 colours x 13 races = 104 combinations per type from 3 + 13 files.

Assets live in assets/shared/banner/ and resolve as a whole
directory through core.resources (a mod replaces the folder or
nothing). Screens obtain a renderer via get_renderer(); the cache is
process-wide so the grid and the preview share tinted cloths.

Ported from Data's banner_v4 package (algorithm and colour tables
unchanged); identifiers translated to English per project rule.
"""
import os
import glob
import pygame

ASSET_REL = os.path.join("assets", "shared", "banner")
EMBLEM_DIR = "emblems"


# --------------------------------------------------------------------
# Banner types
# --------------------------------------------------------------------
class BannerType:
    def __init__(self, cloth, frame, frame_nobg, center, box, shadow,
                 gloss=None, colors=None):
        self.cloth = cloth            # diffuse greyscale shading + alpha
        self.frame = frame            # metal + background
        self.frame_nobg = frame_nobg  # same, background removed
        self.center = center          # centre of the emblem area
        self.box = box                # emblem is fitted proportionally
        self.shadow = shadow          # (offset_x, offset_y, blur_factor)
        self.gloss = gloss            # optional additive highlight layer
        self.colors = colors          # own colour table, else default


# The HD stand has more dynamic range than the other two assets, so it
# carries its own table - same target hue, different mid-tone.
COLORS_HD = {
    "red":    ((146,   6,   6), (0, 0, 0)),
    "yellow": ((225, 192,   6), (0, 0, 0)),
    "green":  ((  6, 137,  39), (0, 0, 0)),
    "silver": ((112, 141, 156), (0, 0, 0)),
    "blue":   ((  6,   6, 173), (0, 0, 0)),
    "brown":  ((149,  74,  44), (0, 0, 0)),
    "purple": (( 99,   6, 141), (0, 0, 0)),
    "orange": ((255, 121,   6), (2, 1, 0)),
}

BANNER_TILE = BannerType(
    "banner_cloth.png", "banner_frame.png", "banner_frame_nobg.png",
    center=(624, 493), box=(480, 560), shadow=(6, 10, 6))

BANNER_STAND = BannerType(
    "stand_cloth.png", "stand_frame.png", "stand_frame_nobg.png",
    center=(163, 163), box=(118, 140), shadow=(2, 3, 4))

BANNER_STAND_HD = BannerType(
    "stand_hd_cloth.png", "stand_hd_frame.png", "stand_hd_frame_nobg.png",
    center=(666, 526), box=(409, 504), shadow=(7, 11, 7),
    gloss="stand_hd_gloss.png", colors=COLORS_HD)


# --------------------------------------------------------------------
# Colour table - measured on the reference screenshot, mid-tone +-1
# --------------------------------------------------------------------
BANNER_COLORS = {                     # (multiply, add)
    "red":    ((162,   6,   6), (0, 0, 0)),
    "yellow": ((249, 213,   6), (0, 0, 0)),
    "green":  ((  6, 152,  44), (0, 0, 0)),
    "silver": ((124, 157, 173), (0, 0, 0)),
    "blue":   ((  7,   6, 192), (0, 0, 0)),
    "brown":  ((166,  82,  49), (0, 0, 0)),
    "purple": ((110,   6, 157), (0, 0, 0)),
    "orange": ((255, 121,   6), (18, 8, 0)),   # above the source cloth's
}                                              # red maximum -> add needed

RACES = ["alkari", "bulrathi", "darlok", "elerian", "gnolam", "human",
         "klackon", "meklar", "mrrshan", "psilon", "sakkra", "silicoid",
         "trilarian"]


# --------------------------------------------------------------------
# Building blocks
# --------------------------------------------------------------------
def tint(shading, multiply, add=(0, 0, 0)):
    """Colour a greyscale shading; folds and highlights survive."""
    out = shading.copy()
    out.fill(multiply, special_flags=pygame.BLEND_RGB_MULT)
    if any(add):
        out.fill(add, special_flags=pygame.BLEND_RGB_ADD)
    return out


def _blur(surf, factor=6):
    w, h = surf.get_size()
    small = pygame.transform.smoothscale(surf, (max(1, w // factor),
                                                max(1, h // factor)))
    return pygame.transform.smoothscale(small, (w, h))


def _shadow(emblem, factor, strength=140):
    sh = emblem.copy()
    sh.fill((0, 0, 0), special_flags=pygame.BLEND_RGB_MULT)
    sh.fill((255, 255, 255, strength), special_flags=pygame.BLEND_RGBA_MULT)
    return _blur(sh, factor)


def embed_emblem(target, shading, emblem, btype):
    """Fit the emblem into the box and place it on the centre. The
    folds are multiplied in (softened) so the emblem lies in the cloth
    instead of sticking to it."""
    f = min(btype.box[0] / emblem.get_width(),
            btype.box[1] / emblem.get_height())
    w = max(1, round(emblem.get_width() * f))
    h = max(1, round(emblem.get_height() * f))
    sym = pygame.transform.smoothscale(emblem, (w, h))
    pos = (btype.center[0] - w // 2, btype.center[1] - h // 2)

    folds = pygame.Surface((w, h), pygame.SRCALPHA)
    folds.blit(shading, (0, 0), pygame.Rect(pos[0], pos[1], w, h))
    folds.fill((115, 115, 115), special_flags=pygame.BLEND_RGB_MULT)
    folds.fill((150, 150, 150), special_flags=pygame.BLEND_RGB_ADD)

    sym_rgb = sym.copy()
    sym_rgb.blit(folds, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

    dx, dy, blur = btype.shadow
    target.blit(_shadow(sym, blur), (pos[0] + dx, pos[1] + dy))
    target.blit(sym_rgb, pos)
    return target


# --------------------------------------------------------------------
# Renderer
# --------------------------------------------------------------------
class BannerRenderer:
    """
        br = BannerRenderer(BANNER_STAND)
        br.warm_up(["human"])
        screen.blit(br.get("blue", "human"), (x, y))
    """

    def __init__(self, btype=BANNER_TILE, asset_dir=None,
                 with_background=True):
        if asset_dir is None:
            from core.resources import res
            asset_dir = res.resolve_dir(ASSET_REL)
        self.type = btype
        self.dir = asset_dir
        self.cloth = pygame.image.load(
            os.path.join(asset_dir, btype.cloth)).convert_alpha()
        filename = btype.frame if with_background else btype.frame_nobg
        self.frame = pygame.image.load(
            os.path.join(asset_dir, filename)).convert_alpha()
        self.gloss = None
        if btype.gloss:
            self.gloss = pygame.image.load(
                os.path.join(asset_dir, btype.gloss)).convert()
        self.colors = btype.colors or BANNER_COLORS

        self.emblems = {}
        for path in sorted(glob.glob(os.path.join(asset_dir, EMBLEM_DIR,
                                                  "*.png"))):
            key = os.path.splitext(os.path.basename(path))[0]
            self.emblems[key] = pygame.image.load(path).convert_alpha()

        self._cache = {}

    def get(self, color, race=None):
        """Full-size banner surface for (colour, race); cached."""
        key = (color, race)
        if key in self._cache:
            return self._cache[key]

        mul, add = self.colors[color]
        surf = tint(self.cloth, mul, add)
        if self.gloss is not None:
            # Highlights are additive: multiplication can never get
            # brighter than the cloth colour, satin needs white peaks.
            surf.blit(self.gloss, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        if race:
            embed_emblem(surf, self.cloth, self.emblems[race], self.type)
        surf.blit(self.frame, (0, 0))

        self._cache[key] = surf
        return surf

    def get_scaled(self, color, race, height):
        """Like get(), scaled to a target pixel height (aspect kept).
        Scaled variants are cached per pixel height."""
        key = (color, race, "h", int(height))
        if key not in self._cache:
            src = self.get(color, race)
            f = height / src.get_height()
            size = (max(1, round(src.get_width() * f)),
                    max(1, int(height)))
            self._cache[key] = pygame.transform.smoothscale(src, size)
        return self._cache[key]

    def warm_up(self, races=None):
        for color in self.colors:
            for r in (races if races else [None]):
                self.get(color, r)

    def clear(self):
        self._cache.clear()


# --------------------------------------------------------------------
# Process-wide access
# --------------------------------------------------------------------
_RENDERERS = {}


def get_renderer(btype, with_background=True):
    """Shared renderer per banner type (lazy, cached). None when the
    asset directory is missing."""
    key = (id(btype), with_background)
    if key not in _RENDERERS:
        from core.resources import res
        if not res.resolve_dir(ASSET_REL):
            return None
        _RENDERERS[key] = BannerRenderer(btype, with_background=with_background)
    return _RENDERERS[key]
