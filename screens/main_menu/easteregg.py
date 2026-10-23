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
#: console, short of the mug; it may run this far.
SPARK_X1 = 0.64

#: CLOSE, where the mockup has it: x 1163..1326, y 843..890 of the panel.
CLOSE_FRAC = (0.819, 0.900, 0.153, 0.062)

#: Lines that stay one line, as in the mockup: when one does not fit its
#: width, the text takes a smaller font factor instead of wrapping.
ONE_LINE = ("welcome", "title", "subtitle", "spark", "thanks", "signature")
#: The centred headline, fitted by its own factor (`_layout`).
HEADLINE = ("welcome", "title", "subtitle")
#: The most a paragraph gap grows by, as a share of the panel height.
MAX_SPREAD = 0.012

#: role -> (font size as a share of the panel height, colour key, centred,
#: space before as a share of the panel height). Read off the mockup's
#: glyph heights; each set (headline, the rest) is scaled by one factor.
ROLES = {
    "welcome": (0.040, "egg_title", True, 0.0),
    "title": (0.064, "egg_title", True, 0.0),
    "subtitle": (0.036, "egg_accent", True, 0.004),
    "heading": (0.036, "egg_title", False, 0.018),
    "body": (0.024, "egg_body", False, 0.012),
    "line": (0.024, "egg_body", False, 0.0),
    "spark": (0.025, "egg_title", False, 0.018),
    "thanks": (0.036, "egg_title", False, 0.020),
    "signature": (0.030, "egg_body", False, 0.008),
    "hashtag": (0.024, "egg_accent", False, 0.0),
}

#: The range that factor is fitted in (`_layout`).
K_MIN, K_MAX = 0.5, 1.2

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
#: hard to read over the stars and the console; a shade over the whole
#: popup rather than one behind the text): a deep navy at this opacity, over
#: everything inside the frame, measured off the picture (1465 x 1073, the
#: last pixel of the frame's lit edge per side at five rows and columns):
#: 16 px left, 22 right, 25 top, 31 bottom, and the corner ornaments'
#: triangles 6.5 % x 5 % — so the gold frame and its ornaments keep their
#: light. Faded in over SCRIM_FEATHER, from that edge inwards.
#: HD EXTENSION `text_shade`: the mockup has none; it is drawn over Data's
#: picture, which itself stays unaltered.
SCRIM_RGB = palette.col("main_menu", "egg_scrim", (4, 8, 22))
SCRIM_ALPHA = 0.55
#: (left, top, right, bottom) as fractions of the panel.
SCRIM_INSET = (16 / 1465, 25 / 1073, 22 / 1465, 31 / 1073)
SCRIM_CORNER = (0.065, 0.05)
SCRIM_FEATHER = 0.006

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


class EasterEgg:
    """The hidden star and its panel, owned by the main menu screen."""

    def __init__(self, screen):
        self.screen = screen
        self.open = False
        self.star = {}
        self.blocks = []
        self._panel_src = None
        self._panel_cache = None      # ((w, h), scaled picture)
        self._text_cache = None       # ((w, h), [(surface, x, y)])
        self._glow_cache = None       # (radius, sprite)
        self._scrim_cache = None      # ((w, h), (shade, x, y))
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
            self.blocks = [(role, text) for role, text in data["blocks"]
                           if role in ROLES and isinstance(text, str)
                           and text.strip()]
            if not self.blocks:
                raise ValueError("no text block with a known role")
        except (TypeError, OSError, ValueError, KeyError) as err:
            log.warning("easter egg data %s not read (%s) — no star",
                        path, err)
            self.star = {}
        pic = self.screen.asset_path("assets", PANEL_FILE)
        if pic:
            try:
                self._panel_src = pygame.image.load(pic).convert_alpha()
            except pygame.error as err:
                log.warning("easter egg panel %s not read (%s) — the HUD "
                            "popup stands in", pic, err)

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
            pygame.surfarray.pixels_alpha(shade)[:] = (
                ramp * SCRIM_ALPHA * 255).astype(np.uint8)
            self._scrim_cache = (p.size, (shade, x0, y0))
        return self._scrim_cache[1]

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
        and kept until the size changes, with the subtitle's span the gold
        rules stop at."""
        if self._text_cache is None or self._text_cache[0] != p.size:
            self._text_cache = (p.size, *self._layout(p.w, p.h))
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
            lo, hi = K_MIN, K_MAX
            if fits(hi):
                return hi
            for _ in range(9):
                k = (lo + hi) / 2
                lo, hi = (k, hi) if fits(k) else (lo, k)
            return lo

        kh = largest(lambda k: self._flow(pw, ph, k, k, HEADLINE)[1] < 1e9)
        kb = largest(lambda k: self._flow(pw, ph, k, kh)[1] <= avail)
        _placed, used, _span = self._flow(pw, ph, kb, kh)
        # What the fonts leave free goes into the paragraph gaps, capped,
        # so the signature stands near the panel's foot as in the mockup.
        gaps = sum(1 for role, _t in self.blocks
                   if role not in HEADLINE and ROLES[role][3] > 0)
        spread = min(MAX_SPREAD * ph, max(0.0, avail - used) / max(1, gaps))
        placed, _used, span = self._flow(pw, ph, kb, kh, spread=spread)
        return placed, span

    def _flow(self, pw, ph, k, kh, roles=None, spread=0.0):
        """One top-to-bottom pass, the headline at font factor kh and the
        rest at k, over `roles` (all by default): (placed, height used —
        infinite when a one-line role overflows its width —, the
        subtitle's (x0, x1, y) or None)."""
        style = self.screen.style
        x0, x1 = round(COL_X0 * pw), round(COL_X1 * pw)
        centre = round((COL_X0 + RULE_X1) / 2 * pw)
        y = round(TEXT_Y0 * ph)
        top = bottom = y
        placed = []
        span = None
        indent = 0
        overflow = False
        for role, text in self.blocks:
            if roles is not None and role not in roles:
                continue
            frac, colour, centred, before = ROLES[role]
            f = kh if role in HEADLINE else k
            size = max(8, int(frac * ph * f))
            y += round(before * ph * f +
                       (spread if before > 0 and role not in HEADLINE else 0))
            lead = indent if role == "hashtag" else 0
            if centred:
                width = round((RULE_X1 - COL_X0) * pw)
            else:
                width = round((SPARK_X1 if role == "spark" else COL_X1)
                              * pw) - x0 - lead
            lines = [text] if role in ONE_LINE else \
                self._wrap(text, size, width)
            for line in lines:
                surf = self._shadowed(line, size, COLOURS[colour])
                if surf.get_width() > width:
                    overflow = True
                x = centre - surf.get_width() // 2 if centred else x0 + lead
                placed.append((surf, x, y))
                if role == "subtitle":
                    span = (x, x + surf.get_width(),
                            y + surf.get_height() // 2)
                bottom = max(bottom, y + surf.get_height())
                y += round(surf.get_height() * 0.98)
            if role == "signature":
                # The hashtag stands under the name, not under the dash.
                indent = style.render_text(
                    lang.Stored("— "), size, SHADOW).get_width()
        return placed, (float("inf") if overflow else bottom - top), span

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

    def _shadowed(self, text, size, colour):
        """The line with a soft dark shadow, so it holds over the stars and
        the galaxy in Data's picture. English as written: `lang.Stored`
        keeps the translation table off it (parked for Data)."""
        style = self.screen.style
        fg = style.render_text(lang.Stored(text), size, colour)
        bg = style.render_text(lang.Stored(text), size, SHADOW)
        off = max(1, size // 14)
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
