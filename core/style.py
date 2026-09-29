"""Style system — the box skins, fonts and the skin frame's geometry.

Ported from v2 style.py, adapted for v3:
  - Colors from colors.json (not hardcoded)
  - Font sizes in reference space, scaled by Layout

Since decision 71 every box skin draws a HUD block (`core.hud.blocks`).
The cockpit layers this drew until work order 169 — the 9-slice skin
texture, the corner glow images, the inner panel tiles, the frame
overlay — were removed with their loaders by work order 189; the skin
frame stays for its geometry (`core/frame.py`).
"""
import os
import hashlib
import logging
import pygame

from core.hud import blocks as hud

log = logging.getLogger("style")


def _scale_of(surface):
    """Device px per reference px for a skin drawn on `surface`, the
    window: `Layout.scale`'s own rule (the smaller axis factor), for the
    callers that hand a skin a rect and no layout."""
    return min(surface.get_width() / 1920.0, surface.get_height() / 1080.0)


class StyleRenderer:
    """Renders UI elements using skin assets.

    Created once at startup. Loads the font and the skin frame's
    geometry from the skin directory; draws the box skins as HUD
    blocks at any size.

    Usage:
        style = StyleRenderer(skin_dir, font_path, colors)
        style.draw_button(surface, rect, label="CONTINUE", hover=False)
        style.draw_panel(surface, rect)
    """

    def __init__(self, skin_dir, font_path, colors):
        self.colors = colors
        self._asset_cache = {}
        self._font_path = font_path
        self._font_cache = {}
        self._blocked = None      # lazily detected substitution glyphs
        self.frame = None
        self._skin_dir = skin_dir

        self._load_frame(skin_dir)

        what = []
        if self.frame and self.frame.available:
            what.append("frame")
        if self._font_path and os.path.exists(self._font_path):
            what.append("font")
        log.info("Loaded: %s", ", ".join(what) or "nothing")

    def _load_frame(self, skin_dir):
        from core.frame import FrameRenderer
        frame_dir = os.path.join(skin_dir, "frame")
        self.frame = FrameRenderer(frame_dir)

    def get_font(self, size):
        """Get cached display font at pixel size."""
        size = max(8, size)
        if size not in self._font_cache:
            if self._font_path and os.path.exists(self._font_path):
                self._font_cache[size] = pygame.font.Font(
                    self._font_path, size)
            else:
                self._font_cache[size] = pygame.font.Font(None, size)
        return self._font_cache[size]

    def get_prop_font(self, size):
        """Get cached proportional (system default) font at pixel size.

        Use for body text, trait values, notes — anything where
        a substituting font's glyphs on +/- would be a problem.
        """
        size = max(8, size)
        key = ("prop", size)
        if key not in self._font_cache:
            self._font_cache[key] = pygame.font.Font(None, size)
        return self._font_cache[key]

    # ── Glyph substitution handling ──────────────────────

    #: Probe size for glyph detection. Big enough that two genuinely
    #: different glyphs cannot hash the same, small enough to be free.
    _GLYPH_PROBE_SIZE = 48

    #: How many characters must share one bitmap before it is treated
    #: as a substitution glyph rather than a coincidence. The DEMO
    #: Bank Gothic this project used to ship mapped 28 characters
    #: onto one watermark; the shipped Aldrich maps none. A licensed
    #: font maps none, so detection simply finds nothing and every
    #: string renders in one font.
    _GLYPH_COLLISION_MIN = 4

    def blocked_glyphs(self):
        """Characters this font renders as one shared substitute.

        Detected, never hardcoded, and the reason that mattered is
        now history: the DEMO Bank Gothic this project shipped until
        31 August replaced 28 characters with one watermark, the
        DIGIT FOUR among them — easy to miss, because it only shows
        up inside numbers.

        The shipped font (Aldrich, OFL) substitutes nothing, so this
        returns an empty set and `render_text` takes the single-font
        path. The machinery stays because a mod may drop in any font,
        including that one. Finding the characters that share a
        bitmap costs one render pass per font and is self-correcting;
        a hardcoded list would have kept splitting strings forever
        after the font was replaced.
        """
        if self._blocked is not None:
            return self._blocked

        font = self.get_font(self._GLYPH_PROBE_SIZE)
        groups = {}
        for code in range(33, 127):
            ch = chr(code)
            surf = font.render(ch, True, (255, 255, 255), (0, 0, 0))
            key = (surf.get_size(),
                   hashlib.md5(pygame.image.tostring(
                       surf, "RGB")).hexdigest())
            groups.setdefault(key, []).append(ch)

        blocked = set()
        for chars in groups.values():
            if len(chars) >= self._GLYPH_COLLISION_MIN:
                blocked.update(chars)
        self._blocked = blocked
        if blocked:
            log.info("Font substitutes %d glyphs: %s",
                     len(blocked), "".join(sorted(blocked)))
        return blocked

    def split_runs(self, text):
        """Split text into (is_blocked, run) pairs, in order."""
        blocked = self.blocked_glyphs()
        if not blocked or not text:
            return [(False, text)] if text else []
        runs = []
        for ch in text:
            flag = ch in blocked
            if runs and runs[-1][0] == flag:
                runs[-1][1].append(ch)
            else:
                runs.append((flag, [ch]))
        return [(flag, "".join(chars)) for flag, chars in runs]

    def render_text(self, text, size, color, antialias=True):
        """Render text, falling back per character on blocked glyphs.

        Bank Gothic for everything it can draw, the proportional font
        for the characters it would replace with a watermark. Runs are
        aligned on the BASELINE, not the top: the two fonts have
        different ascents, and top-aligning them makes parentheses sit
        visibly high against the caps.

        A string with no blocked characters takes the single-font path
        and costs exactly what font.render() used to.
        """
        size = max(8, size)
        runs = self.split_runs(text)
        if len(runs) <= 1 and not (runs and runs[0][0]):
            return self.get_font(size).render(text, antialias, color)

        main = self.get_font(size)
        alt = self.get_prop_font(size)
        pieces = []
        for is_blocked, run in runs:
            font = alt if is_blocked else main
            pieces.append((font, font.render(run, antialias, color)))

        width = sum(surf.get_width() for _, surf in pieces)
        ascent = max(font.get_ascent() for font, _ in pieces)
        descent = max(font.get_descent() for font, _ in pieces)
        height = max(ascent - descent, max(s.get_height()
                                           for _, s in pieces))
        out = pygame.Surface((max(1, width), max(1, height)),
                             pygame.SRCALPHA)
        x = 0
        for font, surf in pieces:
            out.blit(surf, (x, ascent - font.get_ascent()))
            x += surf.get_width()
        return out

    # -- Public drawing API --

    def draw_button(self, surface, rect, label="", hover=False,
                    font_size=16, style=None, glow_offsets=None,
                    glow_rotations=None, icon=None):
        """The `button` box skin: the HUD's slanted button (decision 71).

        The skin texture, the two border lines and the corner glow images
        this drew until work order 169 are the cockpit look 71 replaced;
        work order 189 removed them from the skin. `font_size`,
        `glow_offsets` and `glow_rotations` are accepted and unused — a
        HUD label is sized from the button's own height, and a box that
        still carries them in `boxes.json` must not raise."""
        hud.slant_button(surface, rect, _scale_of(surface),
                         "hover" if hover else "normal", label,
                         icon=icon, style_renderer=self)

    def draw_panel(self, surface, rect):
        """The `panel` box skin: a HUD panel (decision 71)."""
        hud.panel(surface, rect, _scale_of(surface))

    def draw_inner_panel(self, surface, x, y, w, h):
        """The `inner_panel` skin: a HUD panel since decision 71.

        Decision 34's two skins keep their names so no `boxes.json`
        changes; `inner_panel` framed pictures and still does, as a
        filled HUD panel the picture is drawn onto."""
        hud.panel(surface, (x, y, w, h), _scale_of(surface))

    def draw_plate(self, surface, rect, scale=1.0, color=None):
        """One plate outline. **Decision 51, drawn by decision 71's block.**

        The rect may come from a `Box` or be computed — the colony
        screen's sixty cell plates and its column headings are `column x
        band`, and there is no box for any of them. What 34 protects is
        the APPEARANCE having one home: since work order 169 that home is
        `core.hud.blocks.outline`, the separator-coloured line with small
        cut corners. `color` is accepted and IGNORED — a screen asking
        for its own outline colour is a screen drawing its own variant of
        a block, which decision 71 rules out."""
        hud.outline(surface, rect, scale)

    def draw_thin_border(self, surface, rect, scale=1.0, filled=False,
                         dense=False):
        """The `thin_border` skin: a HUD panel WITHOUT fill (decision 71).

        It was always an outline drawn round content that is already
        there — Custom Race's columns, New Game's image boxes, the
        message popup — so it stays one: the HUD panel's edge, glow and
        inner band, no fill over what the box holds.

        `filled` is a box's own `"fill": true` (work order 173): the
        groups whose words stand directly on the universal background,
        drawn BEFORE their content, take the panel's fill — "the HUD
        panel fill does the work", never a darkening of one screen.
        Since 174 that fill is GLASS; a box's `"glass": "dense"` asks for
        the dense variant (a portrait grid)."""
        hud.panel(surface, rect, scale, filled=filled, dense=dense)

    def get_asset(self, rel_path):
        """Load and cache an image from the skin directory."""
        if rel_path in self._asset_cache:
            return self._asset_cache[rel_path]
        path = os.path.join(self._skin_dir, rel_path)
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            self._asset_cache[rel_path] = img
            return img
        self._asset_cache[rel_path] = None
        return None

    def draw_asset(self, surface, rel_path, x, y, w, h):
        """Draw a skin asset scaled to fill (x, y, w, h)."""
        img = self.get_asset(rel_path)
        if img:
            scaled = pygame.transform.smoothscale(img, (w, h))
            surface.blit(scaled, (x, y))
        else:
            pygame.draw.rect(surface, (80, 40, 40),
                             (x, y, w, h), 1)

    def draw_label(self, surface, text, x, y, font_size=16,
                   color=None, center=False, width=0):
        """Draw standalone text."""
        if not text:
            return
        col = color or tuple(
            self.colors.get("text", {}).get("primary",
                                            [190, 200, 230])[:3])
        surf = self.render_text(text, font_size, col)
        if center and width > 0:
            x = x + (width - surf.get_width()) // 2
        surface.blit(surf, (x, y))

    def clear_caches(self):
        """Clear all caches (on resolution change)."""
        self._asset_cache.clear()
        self._font_cache.clear()
