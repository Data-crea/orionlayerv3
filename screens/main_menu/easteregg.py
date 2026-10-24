"""The main menu's easter egg — work order 327, Data's thank-you to GetDaved.

INVENTION `easter_egg`: the original's main menu has no hidden field and no
panel of its own (`MAINMENU::Add_Main_Menu_Fields_`, mainmenu.cpp:110-140,
builds only the six buttons). This is OrionLayer's own and says so: one small
four-pointed star in Data's menu background lights up under the pointer, and a
click on it opens a thank-you panel in the middle of the screen.

**THE STAR IS A POINT OF THE PICTURE, NOT OF THE LAYOUT.** The background is
drawn to cover the window, cropped evenly (`core.backgrounds.cover`), so the
star moves differently from everything placed in the 16:9 content area. Its
position is a fraction of the background picture (`assets/easter_egg.json`,
with the measurement), mapped every frame through `backgrounds.point`, the
same arithmetic `cover` crops with; nothing here keeps a window coordinate
across frames (P809).

**THE PANEL IS DATA'S PICTURE, THE TEXT IS OURS.** `assets/easter_egg_panel.png`
(base pack, moddable like the logo) is drawn whole, scaled to keep its shape;
the words are rendered over it from `assets/easter_egg.json`, after Data's
mockup. While it is open the menu behind it takes nothing: no click, no key,
no hover, no right-click help; ESC and CLOSE close it, as the settings window
does (`screens/game_menu/olwin.py`).
"""
import json
import logging
import math

import numpy as np
import pygame

from core import backgrounds, lang, palette
from core.hud import blocks as hud
from core.hud.hover import pointer_state

log = logging.getLogger("main_menu.easter_egg")

PANEL_FILE = "easter_egg_panel.png"
DATA_FILE = "easter_egg.json"
#: The text in another language the switch offers, beside it (work order
#: 328): `easter_egg_<code>.json`, blocks only; read when that language is
#: the one shown, English where it is missing or unusable.
LANG_FILE = "easter_egg_{}.json"

#: The panel's height as a share of the window, unless the width runs out
#: first (a 5:4 window). Data's mockup shows it at 75 % of the screen; 80 %
#: keeps the body text readable at 1280x720.
PANEL_H_FRAC = 0.80
PANEL_W_FRAC = 0.94

#: The text column, as fractions of the panel, measured off the mockup
#: (b.png, panel 292..1356 x 155..920): text starts 4.6 % in, the headline
#: and its gold rules are centred over 4.6 %..61 %, the hashtag's foot is at
#: 95 %, inside the frame's lower rail. The body wraps at 58 %, clear of
#: the galaxy's core.
COL_X0, COL_X1, RULE_X1 = 0.046, 0.58, 0.61
TEXT_Y0, TEXT_Y1 = 0.035, 0.95
#: The gold "spark" line stands on one line in the mockup, over the
#: console; it may run this far before it wraps — short of the mug, whose
#: left edge is at 62 % of the panel's width (work order 328: the German
#: line ran into it at 64 %).
SPARK_X1 = 0.60

#: CLOSE, where the mockup has it: x 1163..1326, y 843..890 of the panel.
CLOSE_FRAC = (0.819, 0.900, 0.153, 0.062)

#: Lines that stay one line, as in the mockup: when one does not fit its
#: width, the text takes a smaller font factor instead of wrapping. The gold
#: key sentence is not one of them (work order 328): in English it stands on
#: one line anyway at the size the column's height allows, and the German
#: one, longer, would otherwise shrink the whole text to keep it there.
ONE_LINE = ("welcome", "title", "subtitle", "thanks", "signature")
#: The centred headline, fitted by its own factor (`_layout`).
HEADLINE = ("welcome", "title", "subtitle")
#: A line's step as a multiple of its font size, every role alike, and
#: always a pixel more than the line's own height: Aldrich's ink fills
#: its line from top to bottom, so a step of the height alone lets a
#: descender meet the next line's ascender. Data's final polish of the
#: easter egg put air between lines and paragraphs before the largest
#: font (English body about 22 px at 1920x1080).
LINE_STEP = 1.1
#: How much a gap may grow, relative to itself, from the height the text
#: leaves free — every gap in proportion, so the hierarchy holds. The base
#: gaps are the least a gap is, and the font factor is fitted with them,
#: so they trade against the font. The free height opens them up to twice.
MAX_SPREAD = 1.0

#: role -> (font size as a share of the panel height, colour key, centred,
#: gap before, gap after). Sizes read off the mockup's glyph heights; each
#: set (headline, the rest) is scaled by one factor. Gaps are in body
#: line steps, before MAX_SPREAD opens them (work order 328): the gold key
#: sentence set apart by almost twice a paragraph's gap either side, the
#: thanks more, the heading's own text close under it, the signature close
#: to the thanks and the hashtag under the name. A gap AFTER a role, where it has one, is the
#: gap to whatever follows it.
ROLES = {
    "welcome": (0.040, "egg_title", True, 0.0, None),
    "title": (0.064, "egg_title", True, 0.0, None),
    "subtitle": (0.036, "egg_accent", True, 0.1, None),
    "heading": (0.036, "egg_title", False, 0.6, 0.2),
    "body": (0.024, "egg_body", False, 0.4, None),
    "line": (0.024, "egg_body", False, 0.0, None),
    "spark": (0.025, "egg_title", False, 0.75, 0.75),
    "thanks": (0.036, "egg_title", False, 1.0, 0.18),
    "signature": (0.030, "egg_body", False, 0.18, 0.0),
    "hashtag": (0.024, "egg_accent", False, 0.0, None),
}

#: The range that factor is fitted in (`_layout`), and its coarse step.
K_MIN, K_MAX, K_COARSE = 0.5, 1.2, 0.05

# Skin-overridable colours (colors.json section "main_menu"), picked off
# the mockup: the gold headline, the blue "GetDaved" and hashtag, the body.
COLOURS = {
    "egg_title": palette.col("main_menu", "egg_title", (236, 190, 96)),
    "egg_accent": palette.col("main_menu", "egg_accent", (58, 156, 240)),
    "egg_body": palette.col("main_menu", "egg_body", (206, 218, 236)),
    # Gold, Data's choice between the star's own blue-white and gold (work
    # order 327): the colour change says "this reacts" more plainly, and it
    # answers the menu's gold accents.
    "egg_glow": palette.col("main_menu", "egg_glow", (255, 196, 110)),
}
SHADOW = (0, 0, 0)

#: The shade over the panel's inside (Data, work order 327: the text was
#: hard to read over the stars and the console; reworked after his
#: reference picture, "a calm dark-blue text zone on the left that runs out
#: softly into the galaxy on the right"): a deep navy (#07111F) at an
#: opacity that follows the panel's width — SCRIM_PROFILE below — over
#: everything inside the frame, measured off the picture (1465 x 1073, the
#: last pixel of the frame's lit edge per side at five rows and columns):
#: 16 px left, 22 right, 25 top, 31 bottom, and the corner ornaments'
#: triangles 6.5 % x 5 % — so the gold frame and its ornaments keep their
#: light. Faded in over SCRIM_FEATHER, from that edge inwards.
#: HD EXTENSION `text_shade`: the mockup has none; it is drawn over Data's
#: picture, which itself stays unaltered.
SCRIM_RGB = palette.col("main_menu", "egg_scrim", (7, 17, 31))
#: (opacity over the text zone, opacity over the galaxy, panel x up to which
#: the first holds, panel x from which the second holds), smoothstep
#: between. Left: the stars, nebula and console light behind the text keep
#: about a tenth of their light, so they show faintly and no longer compete
#: with the letters (the text column ends at 0.60 of the width); right: the
#: galaxy, the commander and the mug keep nearly all of theirs.
SCRIM_PROFILE = (0.90, 0.08, 0.56, 0.72)
#: (left, top, right, bottom) as fractions of the panel.
SCRIM_INSET = (16 / 1465, 25 / 1073, 22 / 1465, 31 / 1073)
SCRIM_CORNER = (0.065, 0.05)
SCRIM_FEATHER = 0.006
#: The lit consoles right behind the gold key sentence, dimmed further
#: (Data: the sentence was hard to read there): a shade of SCRIM_RGB at
#: this opacity on top of the panel shade, over the sentence's own box,
#: faded out smoothly over these shares of the panel (sideways, up and down)
#: so no edge shows, and gone by SPARK_SHADE_X1 of the panel's width, before
#: the mug. The consoles still show through; the gold letters are drawn over
#: it unchanged.
SPARK_SHADE_ALPHA = 0.40
SPARK_SHADE_FEATHER = (0.03, 0.025)
SPARK_SHADE_X1 = 0.615

#: The hover area never shrinks below this many device pixels, so the
#: star stays easy to hit in the smallest window (1280x720).
MIN_HIT_PX = 14


def _glow_sprite(radius, rgb):
    """The star's hover light: a soft halo and four long rays, to be ADDED
    onto the sky (it only brightens what is there, so the star's white core
    stays and it reads as the same star burning warmer, not a sticker)."""
    r = max(4, int(radius))
    ax = np.arange(-r, r + 1, dtype=np.float32)
    dx, dy = np.meshgrid(ax, ax, indexing="ij")
    d = np.hypot(dx, dy) / r
    halo = 0.55 * np.exp(-(d / 0.30) ** 2) + 0.9 * np.exp(-(d / 0.08) ** 2)
    width = max(1.0, r * 0.045)
    rays = (np.exp(-(dy / width) ** 2) * np.exp(-np.abs(dx) / (0.38 * r))
            + np.exp(-(dx / width) ** 2) * np.exp(-np.abs(dy) / (0.50 * r)))
    light = np.clip(halo + 0.8 * rays, 0, 1) * np.clip(1.2 - d, 0, 1)
    arr = np.stack([light * c for c in rgb], axis=-1).astype(np.uint8)
    return pygame.surfarray.make_surface(arr)


def _shadow_offset(size):
    """How far a line's shadow lies down and right of it, in pixels."""
    return max(1, size // 14)


def _blocks(data):
    """[(role, text)] of a data file's blocks: known roles with text only;
    none at all is a fault, so the caller falls back."""
    out = [(role, text) for role, text in data["blocks"]
           if role in ROLES and isinstance(text, str) and text.strip()]
    if not out:
        raise ValueError("no text block with a known role")
    return out


class EasterEgg:
    """The hidden star and its panel, owned by the main menu screen."""

    def __init__(self, screen):
        self.screen = screen
        self.open = False
        self.star = {}
        self._blocks = {}             # language -> [(role, text)]
        self._panel_src = None
        self._panel_cache = None      # ((w, h), scaled picture)
        self._text_cache = None       # (((w, h), language), placed, span,
                                      #  spark box)
        self._glow_cache = None       # (radius, sprite)
        self._scrim_cache = None      # ((w, h), (shade, x, y))
        self._spark_cache = None      # (((w, h), box), (shade, x, y))
        self._load()

    # ── data ──

    def _load(self):
        path = self.screen.asset_path("assets", DATA_FILE)
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            # Every value checked here, once: a mod's file with a key
            # missing or a word where a number belongs would otherwise fail
            # in the render path, every frame.
            self.star = {k: float(data["star"][k]) for k in
                         ("x", "y", "hit_radius", "glow_radius")}
            self._blocks[lang.DEFAULT] = _blocks(data)
        except (TypeError, OSError, ValueError, KeyError) as err:
            log.warning("easter egg data %s not read (%s) — no star",
                        path, err)
            self.star = {}
        for code in lang.LANGUAGES:
            if code == lang.DEFAULT or not self.star:
                continue
            other = self.screen.asset_path("assets", LANG_FILE.format(code))
            if not other:
                continue
            try:
                with open(other, encoding="utf-8") as f:
                    self._blocks[code] = _blocks(json.load(f))
            except (TypeError, OSError, ValueError, KeyError) as err:
                log.warning("easter egg text %s not read (%s) — English",
                            other, err)
        pic = self.screen.asset_path("assets", PANEL_FILE)
        if pic:
            try:
                self._panel_src = pygame.image.load(pic).convert_alpha()
            except pygame.error as err:
                log.warning("easter egg panel %s not read (%s) — the HUD "
                            "popup stands in", pic, err)

    @property
    def blocks(self):
        """The text in the language shown now — the switch applies as you
        go (decision 99), so it is asked at every layout."""
        return self._blocks.get(lang.current()) or \
            self._blocks.get(lang.DEFAULT, [])

    # ── the star ──

    def star_at(self, w, h):
        """(x, y, hit radius, glow radius) in device pixels at w x h, or None."""
        if not self.star or not self._own_background():
            return None
        p = backgrounds.point("main_menu", w, h, self.star["x"],
                              self.star["y"])
        if p is None:
            return None
        x, y, scale = p
        return (x, y, max(MIN_HIT_PX, self.star["hit_radius"] * scale),
                self.star["glow_radius"] * scale)

    @staticmethod
    def _own_background():
        """The star is a point of the menu's own picture: on the universal
        one, which stands in when that picture is missing or unreadable,
        there is no star to find, so there is no egg either."""
        path = backgrounds.source_path("main_menu")
        return bool(path) and path.replace("\\", "/").endswith(
            backgrounds.DIR + "/main_menu.png")

    def star_hit(self, mx, my, w, h):
        s = self.star_at(w, h)
        return s is not None and (mx - s[0]) ** 2 + (my - s[1]) ** 2 <= \
            s[2] ** 2

    def render_star(self, surface, mouse_pos):
        """The glow, only while the pointer is on the star and the panel is
        shut; drawn right after the background, so it is part of the sky."""
        if self.open:
            return
        w, h = surface.get_size()
        s = self.star_at(w, h)
        if s is None or not self.star_hit(*mouse_pos, w, h):
            return
        radius = max(4, int(round(s[3])))
        if self._glow_cache is None or self._glow_cache[0] != radius:
            self._glow_cache = (radius, _glow_sprite(
                radius, COLOURS["egg_glow"]))
        surface.blit(self._glow_cache[1],
                     (round(s[0]) - radius, round(s[1]) - radius),
                     special_flags=pygame.BLEND_RGB_ADD)

    # ── the panel ──

    def panel_rect(self, w, h):
        """The panel, centred, scaled with the window at the picture's own
        shape."""
        iw, ih = self._panel_src.get_size() if self._panel_src else \
            (1465, 1073)
        s = min(PANEL_H_FRAC * h / ih, PANEL_W_FRAC * w / iw)
        pw, ph = round(iw * s), round(ih * s)
        return pygame.Rect((w - pw) // 2, (h - ph) // 2, pw, ph)

    def close_rect(self, w, h):
        p = self.panel_rect(w, h)
        fx, fy, fw, fh = CLOSE_FRAC
        return pygame.Rect(p.x + round(fx * p.w), p.y + round(fy * p.h),
                           round(fw * p.w), round(fh * p.h))

    def render_panel(self, surface):
        if not self.open:
            return
        w, h = surface.get_size()
        p = self.panel_rect(w, h)
        if self._panel_src is not None:
            if self._panel_cache is None or self._panel_cache[0] != p.size:
                self._panel_cache = (p.size, pygame.transform.smoothscale(
                    self._panel_src, p.size))
            surface.blit(self._panel_cache[1], p.topleft)
        else:
            hud.popup(surface, p, h / 1080)
        placed = self._text(p)
        shade, sx, sy = self._scrim(p)
        surface.blit(shade, (p.x + sx, p.y + sy))
        spark = self._spark_shade(p, self._text_cache[3])
        if spark is not None:
            shade, sx, sy = spark
            surface.blit(shade, (p.x + sx, p.y + sy))
        for surf, x, y in placed:
            surface.blit(surf, (p.x + x, p.y + y))
        for a, b in self._rules(p, self._text_cache[2]):
            # LOOK EXCEPTION marking: the mockup's two thin gold rules
            # beside "with me, GetDaved!", in the headline's own colour.
            pygame.draw.line(surface, COLOURS["egg_title"], a, b,
                             max(1, round(p.h * 0.002)))
        r = self.close_rect(w, h)
        hud.action_button(surface, r, h / 1080, pointer_state(r),
                          self.screen.helptext.label("close"),
                          style_renderer=self.screen.style)

    def _scrim(self, p):
        """(surface, x, y) relative to the panel: the shade over the inside
        of the frame, its corners cut where the ornaments are, built once
        per panel size."""
        if self._scrim_cache is None or self._scrim_cache[0] != p.size:
            x0 = math.ceil(SCRIM_INSET[0] * p.w)
            y0 = math.ceil(SCRIM_INSET[1] * p.h)
            x1 = p.w - math.ceil(SCRIM_INSET[2] * p.w)
            y1 = p.h - math.ceil(SCRIM_INSET[3] * p.h)
            bw, bh = max(1, x1 - x0), max(1, y1 - y0)
            cx, cy = SCRIM_CORNER[0] * p.w, SCRIM_CORNER[1] * p.h
            u = np.arange(bw, dtype=np.float32)
            v = np.arange(bh, dtype=np.float32)
            ex = np.minimum(u, u[::-1])[:, None]       # to the nearer side
            ey = np.minimum(v, v[::-1])[None, :]
            # Distance inside the corner cut: the line ex/cx + ey/cy = 1,
            # in pixels along its normal.
            cut = (ex / cx + ey / cy - 1) * (cx * cy / np.hypot(cx, cy))
            edge = np.minimum(np.minimum(ex, ey), cut)
            ramp = np.clip(edge / max(1.0, SCRIM_FEATHER * p.h), 0, 1)
            shade = pygame.Surface((bw, bh), pygame.SRCALPHA)
            # LOOK EXCEPTION marking: the shade over the easter egg's
            # panel, Data's call for readability over his picture.
            shade.fill(SCRIM_RGB)
            a_text, a_sky, x_full, x_gone = SCRIM_PROFILE
            t = np.clip(((x0 + u) / p.w - x_full) / (x_gone - x_full), 0, 1)
            alpha = (a_text + (a_sky - a_text) * t * t * (3 - 2 * t))[:, None]
            pygame.surfarray.pixels_alpha(shade)[:] = (
                ramp * alpha * 255).astype(np.uint8)
            self._scrim_cache = (p.size, (shade, x0, y0))
        return self._scrim_cache[1]

    def _spark_shade(self, p, box):
        """(surface, x, y) relative to the panel: the extra shade behind the
        gold key sentence (SPARK_SHADE_ALPHA), or None without one; built
        once per panel size and sentence box."""
        if box is None:
            return None
        key = (p.size, box)
        if self._spark_cache is None or self._spark_cache[0] != key:
            bx0, by0, bx1, by1 = box
            fx = SPARK_SHADE_FEATHER[0] * p.w
            fy = SPARK_SHADE_FEATHER[1] * p.h
            x0 = max(0, math.floor(bx0 - fx))
            x1 = min(math.ceil(SPARK_SHADE_X1 * p.w), math.ceil(bx1 + fx))
            y0 = max(0, math.floor(by0 - fy))
            y1 = min(p.h, math.ceil(by1 + fy))
            bw, bh = max(1, x1 - x0), max(1, y1 - y0)
            u = x0 + np.arange(bw, dtype=np.float32) + 0.5
            v = y0 + np.arange(bh, dtype=np.float32) + 0.5
            # Full inside the box, smoothstep down to nothing over the
            # feather; on the right the fade ends at the box's end plus the
            # feather or SPARK_SHADE_X1, whichever comes first.
            right = min(bx1 + fx, SPARK_SHADE_X1 * p.w)
            tx = np.maximum(np.clip((bx0 - u) / fx, 0, 1),
                            np.clip((u - (right - fx)) / fx, 0, 1))
            ty = np.clip(np.maximum(by0 - v, v - by1) / fy, 0, 1)
            sx = 1 - tx * tx * (3 - 2 * tx)
            sy = 1 - ty * ty * (3 - 2 * ty)
            shade = pygame.Surface((bw, bh), pygame.SRCALPHA)
            # LOOK EXCEPTION marking: the shade behind the easter egg's key
            # sentence, Data's call for readability over his picture.
            shade.fill(SCRIM_RGB)
            pygame.surfarray.pixels_alpha(shade)[:] = (
                SPARK_SHADE_ALPHA * 255 * sx[:, None] * sy[None, :]
            ).astype(np.uint8)
            self._spark_cache = (key, (shade, x0, y0))
        return self._spark_cache[1]

    def _rules(self, p, sub):
        if not sub:
            return []
        x0, x1, y = sub
        gap = round(p.h * 0.012)
        return [((p.x + round(COL_X0 * p.w), p.y + y),
                 (p.x + x0 - gap, p.y + y)),
                ((p.x + x1 + gap, p.y + y),
                 (p.x + round(RULE_X1 * p.w), p.y + y))]

    def _text(self, p):
        """[(surface, x, y)] relative to the panel, laid out for its size
        and the language shown, kept until either changes, with the
        subtitle's span the gold rules stop at."""
        key = (p.size, lang.current())
        if self._text_cache is None or self._text_cache[0] != key:
            self._text_cache = (key, *self._layout(p.w, p.h))
        return self._text_cache[1]

    def _layout(self, pw, ph):
        """Two font factors, each the largest up to K_MAX that fits: the
        headline's by its width (it is centred over the gold rules), the
        rest by the column's height, so the closing lines end where the
        mockup's do whatever the font's width does to the wrapping. A
        bisection, because the line count jumps: the height is not
        proportional to the factor."""
        avail = (TEXT_Y1 - TEXT_Y0) * ph

        def largest(fits):
            # Coarse from the top down, then a bisection inside the first
            # step that fits: a wrap that jumps makes "fits" not monotonic
            # over the whole range (the German text fitted at 0.81 and at
            # 0.87 but not between), so a bisection over all of it can
            # settle on a lower plateau (work order 328).
            hi = K_MAX
            while hi > K_MIN and not fits(hi):
                hi -= K_COARSE
            if hi <= K_MIN:
                return K_MIN
            lo, hi = hi, min(K_MAX, hi + K_COARSE)
            if fits(hi):
                return hi
            for _ in range(6):
                k = (lo + hi) / 2
                lo, hi = (k, hi) if fits(k) else (lo, k)
            return lo

        kh = largest(lambda k: self._flow(pw, ph, k, k, HEADLINE)[1] < 1e9)
        kb = largest(lambda k: self._flow(pw, ph, k, kh)[1] <= avail)
        _placed, used, _span, gaps, _spark = self._flow(pw, ph, kb, kh)
        # What the fonts leave free goes into the gaps, each in proportion
        # to itself and capped, so the signature stands near the panel's
        # foot as in the mockup and a larger gap stays the larger.
        # Half a pixel a gap held back: each gap is rounded on its own.
        n = sum(1 for role, _t in self.blocks if role not in HEADLINE)
        spread = min(MAX_SPREAD, max(0.0, avail - used - 0.5 * n) / gaps) \
            if gaps else 0.0
        placed, _used, span, _gaps, spark = self._flow(pw, ph, kb, kh,
                                                       spread=spread)
        return placed, span, spark

    def _flow(self, pw, ph, k, kh, roles=None, spread=0.0):
        """One top-to-bottom pass, the headline at font factor kh and the
        rest at k, over `roles` (all by default), every gap grown by
        `spread` of itself: (placed, height used — infinite when a one-line
        role overflows its width —, the subtitle's (x0, x1, y) or None, the
        sum of the body's gaps in pixels, the gold key sentence's ink box
        (x0, y0, x1, y1) or None)."""
        style = self.screen.style
        x0, x1 = round(COL_X0 * pw), round(COL_X1 * pw)
        centre = round((COL_X0 + RULE_X1) / 2 * pw)
        y = round(TEXT_Y0 * ph)
        top = bottom = y
        placed = []
        span = None
        spark = None
        indent = 0
        overflow = False
        gaps = 0.0
        step = ROLES["body"][0] * ph * k * LINE_STEP   # one body line
        after = None
        for role, text in self.blocks:
            if roles is not None and role not in roles:
                continue
            frac, colour, centred, before, gap_after = ROLES[role]
            f = kh if role in HEADLINE else k
            size = max(8, int(frac * ph * f))
            gap = (before if after is None else after) * \
                (step if role not in HEADLINE else frac * ph * f)
            if placed:
                if role not in HEADLINE:
                    gaps += gap
                    gap *= 1 + spread
                y += round(gap)
            after = gap_after
            lead = indent if role == "hashtag" else 0
            if centred:
                width = round((RULE_X1 - COL_X0) * pw)
            else:
                width = round((SPARK_X1 if role == "spark" else COL_X1)
                              * pw) - x0 - lead
            # The shadow hangs out by its offset; a line is wrapped so that
            # it fits WITH it, or a line that just fits counts as too wide.
            lines = [text] if role in ONE_LINE else \
                self._wrap(text, size, width - _shadow_offset(size))
            if role == "spark" and len(lines) > 1:
                # One line, as the mockup sets it, if a little smaller
                # does it; else two even lines at the size.
                small = self._one_line_size(
                    text, size, width,
                    max(8, int(ROLES["body"][0] * ph * k)))
                if small:
                    size, lines = small, [text]
                else:
                    lines = self._balanced(text, size, lines,
                                           width - _shadow_offset(size))
            plain = self._plain_height(size)
            line_step = max(round(size * LINE_STEP), plain + 1)
            for i, line in enumerate(lines):
                if i:
                    y += line_step
                surf = self._shadowed(line, size, COLOURS[colour])
                if surf.get_width() > width:
                    overflow = True
                x = centre - surf.get_width() // 2 if centred else x0 + lead
                # A capital umlaut makes the line taller ABOVE its baseline
                # (the fallback font's ascent): drawn that much higher, so
                # every line of a role sits on the same baseline step.
                rise = max(0, surf.get_height() - plain)
                placed.append((surf, x, y - rise))
                if role == "subtitle":
                    span = (x, x + surf.get_width(),
                            y + plain // 2)
                bottom = max(bottom, y + plain)
                if role == "spark":
                    b = (x, y, x + surf.get_width(), y + plain)
                    spark = b if spark is None else (
                        min(spark[0], b[0]), min(spark[1], b[1]),
                        max(spark[2], b[2]), max(spark[3], b[3]))
            # The headline stacks tight, as the mockup sets it; any other
            # block ends one full line step on, so a gap of 0 ("line")
            # continues its paragraph at the same rhythm.
            y += plain if role in HEADLINE else line_step
            if role == "signature":
                # The hashtag stands under the name, not under the dash.
                indent = style.render_text(
                    lang.Stored("— "), size, SHADOW).get_width()
        return (placed, (float("inf") if overflow else bottom - top), span,
                gaps, spark)

    def _plain_height(self, size):
        """A line's height at `size` with no fallback glyph in it, the
        shadow's offset included (`_shadowed`)."""
        return self._shadowed("Ag", size, SHADOW).get_height()

    def _wrap(self, text, size, width):
        style = self.screen.style
        words, lines, cur = text.split(), [], ""
        for word in words:
            trial = f"{cur} {word}".strip()
            if cur and style.render_text(
                    lang.Stored(trial), size, SHADOW).get_width() > width:
                lines.append(cur)
                cur = word
            else:
                cur = trial
        return lines + [cur] if cur else lines

    def _one_line_size(self, text, size, width, body):
        """The largest size down to the body's (`body`, never less: the key
        sentence must not stand out less than the text around it) at which
        `text` stands on one line in `width`, or None."""
        for s in range(size, min(size, body) - 1, -1):
            if self._shadowed(text, s, SHADOW).get_width() <= width:
                return s
        return None

    def _balanced(self, text, size, lines, width):
        """The key sentence's lines as even as they can be at the same
        count: the narrowest width that still wraps it into as many lines
        (a bisection on the width), so no word stands alone under it — the
        German sentence left "zündet." on a line of its own."""
        lo, hi = width // 2, width
        best = lines
        while hi - lo > 2:
            mid = (lo + hi) // 2
            trial = self._wrap(text, size, mid)
            if len(trial) <= len(lines):
                hi, best = mid, trial
            else:
                lo = mid
        return best

    def _shadowed(self, text, size, colour):
        """The line with a soft dark shadow, so it holds over the stars and
        the galaxy in Data's picture. Drawn as the data file has it:
        `lang.Stored` keeps the UI's translation table off it — the file of
        the language shown already is the translation (work order 328)."""
        style = self.screen.style
        fg = style.render_text(lang.Stored(text), size, colour)
        bg = style.render_text(lang.Stored(text), size, SHADOW)
        off = _shadow_offset(size)
        out = pygame.Surface((fg.get_width() + off, fg.get_height() + off),
                             pygame.SRCALPHA)
        out.blit(bg, (off, off))
        out.blit(fg, (0, 0))
        return out

    # ── input while open ──

    def click(self, x, y, w, h):
        """True if the egg took the click: CLOSE, anything while the panel
        is open, or the star while it is shut."""
        if self.open:
            if self.close_rect(w, h).collidepoint(x, y):
                self.open = False
            return True
        if self.star_hit(x, y, w, h):
            self.open = True
            return True
        return False

    def key(self, key):
        """True if the egg took the key: every key while open, ESC closes."""
        if not self.open:
            return False
        if key == pygame.K_ESCAPE:
            self.open = False
        return True
