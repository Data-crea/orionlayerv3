"""Style system — panels, button skins, corner glows, fonts.

Ported from v2 style.py, adapted for v3:
  - Colors from colors.json (not hardcoded)
  - Font sizes in reference space, scaled by Layout
  - Pre-rotated corner glow images (no runtime flip)
  - NineSlice lives in core/nineslice.py

Rendering layers (bottom to top):
  1. Background — 9-slice skin texture (scales to any size)
  2. Border — programmatic lines (pixel-accurate)
  3. Corner glows — images positioned on border corners
  4. Label — centered text in the display font
"""
import os
import hashlib
import logging
import pygame

from core.nineslice import NineSlice, load_tile_directory

log = logging.getLogger("style")

# 9-slice margins for outer_box_dark_blue.png (chamfered corners)
SKIN_MARGINS = (60, 60, 60, 60)  # left, right, top, bottom


class StyleRenderer:
    """Renders UI elements using skin assets.

    Created once at startup. Loads textures, font, corner glows
    from the skin directory. Draws buttons and panels at any size
    with per-size caching.

    Usage:
        style = StyleRenderer(skin_dir, font_path, colors)
        style.draw_button(surface, rect, label="CONTINUE", hover=False)
        style.draw_panel(surface, rect)
    """

    CORNER_INSET = 18   # corner glow position relative to box edge
    HOVER_TINT = (30, 80, 120, 60)

    def __init__(self, skin_dir, font_path, colors):
        self.colors = colors
        self.skin = None
        self.inner_panel = None
        self.corners = {}
        self._corner_cache = {}
        self._bg_cache = {}
        self._asset_cache = {}
        self._font_path = font_path
        self._font_cache = {}
        self._blocked = None      # lazily detected substitution glyphs
        self.frame = None
        self._skin_dir = skin_dir

        self._load_skin(skin_dir)
        self._load_inner_panel(skin_dir)
        self._load_corners(skin_dir)
        self._load_frame(skin_dir)

        what = []
        if self.skin:
            what.append("skin")
        if self.inner_panel:
            what.append("inner_panel")
        if self.corners:
            what.append(f"corners({len(self.corners)})")
        if self.frame and self.frame.available:
            what.append("frame")
        if self._font_path and os.path.exists(self._font_path):
            what.append("font")
        log.info("Loaded: %s", ", ".join(what) or "nothing")

    def _load_skin(self, skin_dir):
        path = os.path.join(skin_dir, "outer_box_dark_blue.png")
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            l, r, t, b = SKIN_MARGINS
            self.skin = NineSlice(img, l, r, t, b)

    def _load_inner_panel(self, skin_dir):
        """Load inner panel 9-slice from inner_panel/ directory."""
        panel_dir = os.path.join(skin_dir, "inner_panel")
        if not os.path.isdir(panel_dir):
            return
        self.inner_panel = load_tile_directory(panel_dir)
        if self.inner_panel:
            img = self.inner_panel.image
            log.info("Inner panel loaded: %dx%d, corner=%d",
                     img.get_width(), img.get_height(),
                     self.inner_panel.left)

    def _load_corners(self, skin_dir):
        for key in ("tl", "tr", "bl", "br"):
            path = os.path.join(skin_dir, f"corner_glow_{key}.png")
            if os.path.exists(path):
                self.corners[key] = pygame.image.load(path).convert_alpha()

    def _load_frame(self, skin_dir):
        from core.frame import FrameRenderer
        frame_dir = os.path.join(skin_dir, "frame")
        self.frame = FrameRenderer(frame_dir)
        self._frame_variants = {}  # name → FrameRenderer
        self._frame_dir = frame_dir

    def get_frame_variant(self, name):
        """Get a named frame variant (loaded from frame/<name>/ subdir)."""
        if name not in self._frame_variants:
            from core.frame import FrameRenderer
            variant_dir = os.path.join(self._frame_dir, name)
            renderer = FrameRenderer(variant_dir)
            self._frame_variants[name] = renderer
            if renderer.available:
                log.info("Frame variant '%s' loaded", name)
        return self._frame_variants.get(name)

    def draw_frame(self, surface, variant=None):
        """Draw the 9-slice frame overlay filling the entire surface.

        variant: name of a frame subdirectory (e.g. 'select_race')
                 to use instead of the default frame tiles.
        """
        frame = self.frame
        if variant:
            v = self.get_frame_variant(variant)
            if v and v.available:
                frame = v
        if not frame or not frame.available:
            return
        w, h = surface.get_width(), surface.get_height()
        frame_surf = frame.render(w, h)
        if frame_surf:
            surface.blit(frame_surf, (0, 0))

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

    def _get_bg(self, w, h):
        """Get background surface for a box size (cached)."""
        key = (w, h)
        if key not in self._bg_cache:
            if not self.skin:
                return None
            src = self.skin.image
            sw, sh = src.get_width(), src.get_height()
            l, r, t, b = SKIN_MARGINS
            if h >= t + b + 2:
                self._bg_cache[key] = self.skin.render(w, h)
            else:
                cy = (sh - h) // 2
                cx = (sw - w) // 2 if w < sw else 0
                crop_w = min(w, sw)
                strip = src.subsurface((cx, cy, crop_w, h)).copy()
                if w != crop_w:
                    strip = pygame.transform.smoothscale(strip, (w, h))
                self._bg_cache[key] = strip
        return self._bg_cache[key]

    def _get_scaled_corners(self, box_h):
        """Corner glow surfaces scaled to box height (cached)."""
        if box_h not in self._corner_cache:
            if len(self.corners) < 4:
                return None
            orig = self.corners["tl"]
            scale = min(box_h / orig.get_height(), 1.0)
            new_w = max(1, int(orig.get_width() * scale))
            new_h = max(1, int(orig.get_height() * scale))
            scaled = {}
            for k, surf in self.corners.items():
                scaled[k] = pygame.transform.smoothscale(
                    surf, (new_w, new_h))
            self._corner_cache[box_h] = scaled
        return self._corner_cache[box_h]

    # -- Public drawing API --

    def draw_button(self, surface, rect, label="", hover=False,
                    font_size=16, style=None, glow_offsets=None,
                    glow_rotations=None):
        """Draw a button with skin background, border, glows, label."""
        sx, sy, sw, sh = rect.x, rect.y, rect.w, rect.h
        if sw < 4 or sh < 4:
            return
        btn = self.colors.get("button", {})
        style = style or {}

        # 1. Background (9-slice texture)
        bg = self._get_bg(sw, sh)
        if bg:
            surface.blit(bg, (sx, sy))

        # 1b. Hover tint
        if hover:
            tint = pygame.Surface((sw, sh), pygame.SRCALPHA)
            tint.fill(self.HOVER_TINT)
            surface.blit(tint, (sx, sy))

        # 2. Border lines
        if hover:
            border_col = btn.get("border_hover", [120, 160, 220])[:3]
            alpha = 240
        else:
            border_col = btn.get("border", [70, 95, 145])[:3]
            alpha = 180
        glow_col = self.colors.get("grid", [25, 35, 55])[:3]

        line = pygame.Surface((sw, sh), pygame.SRCALPHA)
        pygame.draw.rect(line, (glow_col[0], glow_col[1],
                                glow_col[2], alpha // 3),
                         (0, 0, sw, sh), 1, border_radius=3)
        pygame.draw.rect(line, (border_col[0], border_col[1],
                                border_col[2], alpha),
                         (1, 1, sw - 2, sh - 2), 1, border_radius=2)
        surface.blit(line, (sx, sy))

        # 3. Corner glows
        glows = self._get_scaled_corners(sh)
        if glows:
            corners = [("tl", sx, sy), ("tr", sx + sw, sy),
                       ("bl", sx, sy + sh), ("br", sx + sw, sy + sh)]
            for key, cx, cy in corners:
                img = glows[key]
                rot = glow_rotations.get(key, 0) if glow_rotations else 0
                if rot:
                    img = pygame.transform.rotate(img, rot)
                iw, ih = img.get_width(), img.get_height()
                if glow_offsets:
                    ox, oy = glow_offsets.get(key, (0, 0))
                    surface.blit(img, (cx + ox - iw//2, cy + oy - ih//2))
                else:
                    ci = self.CORNER_INSET
                    dx = ci if 'l' in key else -ci
                    dy = ci if 't' in key else -ci
                    surface.blit(img, (cx + dx - iw//2, cy + dy - ih//2))

        # 4. Label
        if label:
            if hover:
                text_col = btn.get("text_hover", [220, 230, 255])[:3]
            else:
                text_col = btn.get("text", [180, 195, 225])[:3]
            text = self.render_text(label.upper(), font_size, text_col)
            tx = sx + (sw - text.get_width()) // 2
            ty = sy + (sh - text.get_height()) // 2
            surface.blit(text, (tx, ty))

    def draw_panel(self, surface, rect):
        """Draw a panel background (9-slice, no border/glows)."""
        bg = self._get_bg(rect.w, rect.h)
        if bg:
            surface.blit(bg, (rect.x, rect.y))

    def draw_inner_panel(self, surface, x, y, w, h):
        """Draw an inner content panel using the inner_panel 9-slice.

        Renders the beveled frame with transparent center.
        Call with pixel coordinates (already scaled by Layout).
        """
        if not self.inner_panel:
            pygame.draw.rect(surface, (50, 70, 110), (x, y, w, h), 1,
                             border_radius=3)
            return
        panel = self.inner_panel.render(w, h)
        surface.blit(panel, (x, y))

    def draw_thin_border(self, surface, rect, scale=1.0):
        """Draw the thin rounded outline used as a light panel skin.

        The counterpart to `draw_inner_panel`: no texture, no fill,
        just the line. Custom Race groups its three columns with it,
        New Game its five setting boxes, and the message popup borders
        itself with it — three call sites, which is why the arithmetic
        lives here instead of being pasted a fourth time.
        """
        col = self.colors.get("panel", {}).get(
            "thin_border", [55, 65, 85])[:3]
        pygame.draw.rect(surface, tuple(col), rect, 1,
                         border_radius=max(6, int(10 * scale)))

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
        if self.skin:
            self.skin.clear_cache()
        if self.inner_panel:
            self.inner_panel.clear_cache()
        self._corner_cache.clear()
        self._bg_cache.clear()
        self._asset_cache.clear()
        self._font_cache.clear()
        if self.frame:
            self.frame.clear_cache()
