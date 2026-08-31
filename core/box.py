"""Box — a UI element with a position in reference space.

Loaded from boxes.json per screen. Each box has a rect
in 1080p reference space, an optional field_id, and an
optional anchor for widescreen positioning.
"""
import json
import os
import pygame
from core.config import REF_W


class Box:
    """A UI element with reference rect and optional field ID."""

    def __init__(self, data):
        self.name = data["name"]
        self.ref_rect = tuple(data["rect"])  # [x, y, w, h] in 1080p
        self.field_id = data.get("field_id")
        self.anchor = data.get("anchor")  # None, "right", "left"
        self.role = data.get("role", [])
        self.style = data.get("style", {})
        self.data_field = data.get("data_field")
        self.hidden = data.get("hidden", False)
        self.locked = data.get("locked", False)
        self.screen_rect = None
        self.hover = False
        # Runtime overrides for the "text" skin. Never serialized: a
        # value a screen computes this frame must not end up in
        # boxes.json when the editor saves.
        self.text = None
        self.text_color = None

    def update_layout(self, layout):
        """Compute window rect from reference rect."""
        x, y, w, h = self.ref_rect
        sw = int(w * layout.scale)
        sh = int(h * layout.scale)
        sy = int(y * layout.scale + layout.offset_y)

        # Content area boundaries (16:9 area centered in window)
        content_right = layout.offset_x + REF_W * layout.scale

        if self.anchor == "right":
            ref_margin = REF_W - x - w
            sx = int(content_right) - sw - int(ref_margin * layout.scale)
        elif self.anchor == "left":
            sx = int(x * layout.scale + layout.offset_x)
        else:
            sx = int(x * layout.scale + layout.offset_x)

        self.screen_rect = pygame.Rect(sx, sy, sw, sh)

    def contains(self, screen_x, screen_y):
        """Hit test in screen coordinates."""
        if self.screen_rect:
            return self.screen_rect.collidepoint(screen_x, screen_y)
        return False

    def _scaled_glow_offsets(self, layout):
        """Convert glow offsets from reference to pixel space."""
        glows_ref = self.style.get("glows")
        if not glows_ref:
            return None
        offsets = {}
        for key in ("tl", "tr", "bl", "br"):
            if key in glows_ref:
                ox, oy = glows_ref[key]
                offsets[key] = (int(ox * layout.scale),
                                int(oy * layout.scale))
        return offsets if offsets else None

    def render(self, surface, layout, style_renderer):
        """Draw the box using the style renderer."""
        if self.hidden or self.screen_rect is None:
            return
        skin = self.style.get("skin", "panel")
        label = self.style.get("label", "")
        font_size = layout.font_size(self.style.get("font_size", 16))

        if skin == "button":
            style_renderer.draw_button(
                surface, self.screen_rect,
                label=label, hover=self.hover,
                font_size=font_size, style=self.style,
                glow_offsets=self._scaled_glow_offsets(layout),
                glow_rotations=self.style.get("glow_rot"),
            )
        elif skin == "asset":
            r = self.screen_rect
            asset_path = self.style.get("asset", "")
            style_renderer.draw_asset(
                surface, asset_path, r.x, r.y, r.w, r.h)
        elif skin == "inner_panel":
            r = self.screen_rect
            style_renderer.draw_inner_panel(
                surface, r.x, r.y, r.w, r.h)
        elif skin == "text":
            self._render_text(surface, style_renderer, font_size)
        elif skin == "thin_border":
            style_renderer.draw_thin_border(
                surface, self.screen_rect, layout.scale)
        elif skin == "panel":
            style_renderer.draw_panel(surface, self.screen_rect)
            if label:
                text_col = style_renderer.colors.get(
                    "text", {}).get("primary", [190, 200, 230])
                style_renderer.draw_label(
                    surface, label,
                    self.screen_rect.x, self.screen_rect.y
                    + (self.screen_rect.h - font_size) // 2,
                    font_size=font_size,
                    color=tuple(text_col[:3]),
                    center=True, width=self.screen_rect.w,
                )
        else:
            pygame.draw.rect(surface, (60, 80, 120),
                             self.screen_rect, 1)

    def _render_text(self, surface, style_renderer, font_size):
        """Bare text in the box rect — no panel, no border.

        The string is `self.text` when a screen has filled it in,
        otherwise the box's own `style.label`. Position, size, font
        size and alignment stay in boxes.json, so the box is
        draggable in F5 like any other.
        """
        text = self.text if self.text is not None else self.style.get(
            "label", "")
        if not text:
            return
        color = self.text_color
        if color is None:
            color = self.style.get("color")
        if color is None:
            color = style_renderer.colors.get("text", {}).get(
                "primary", [190, 200, 230])
        surf = style_renderer.render_text(text, font_size,
                                          tuple(color[:3]))
        r = self.screen_rect
        align = self.style.get("align", "left")
        if align == "center":
            x = r.x + (r.w - surf.get_width()) // 2
        elif align == "right":
            x = r.right - surf.get_width()
        else:
            x = r.x
        y = r.y + (r.h - surf.get_height()) // 2
        surface.blit(surf, (x, y))

    def to_dict(self):
        """Serialize box back to dict for saving."""
        d = {"name": self.name, "rect": list(self.ref_rect)}
        if self.field_id is not None:
            d["field_id"] = self.field_id
        if self.anchor:
            d["anchor"] = self.anchor
        if self.role:
            d["role"] = self.role
        if self.style:
            d["style"] = self.style
        if self.data_field:
            d["data_field"] = self.data_field
        if self.hidden:
            d["hidden"] = True
        if self.locked:
            d["locked"] = True
        return d

    def __repr__(self):
        fid = f" field={self.field_id}" if self.field_id is not None else ""
        return f"<Box '{self.name}' {self.ref_rect}{fid}>"


def _resolution_key(win_w, win_h):
    """Build resolution key string, e.g. '1920x1080'."""
    return f"{win_w}x{win_h}"


def _find_best_fallback(res_dict, target_w, target_h):
    """Find the closest resolution key by pixel count difference."""
    target_pixels = target_w * target_h
    best_key = None
    best_diff = float("inf")
    for key in res_dict:
        parts = key.split("x")
        if len(parts) != 2:
            continue
        try:
            w, h = int(parts[0]), int(parts[1])
        except ValueError:
            continue
        diff = abs(w * h - target_pixels)
        if diff < best_diff:
            best_diff = diff
            best_key = key
    return best_key


def load_boxes(source, win_w=1920, win_h=1080):
    """Load boxes for a specific resolution from boxes.json.

    source: either a boxes.json file path (mod-resolved) or a
    screen directory containing boxes.json.

    File format:
      New (dict): {"1920x1080": [...], "3440x1440": [...]}
      Legacy (list): [...] — treated as "1920x1080"

    Fallback chain: exact key → closest resolution → empty list.
    When falling back, boxes are deep-copied so edits don't affect
    the source resolution.
    """
    if source and os.path.isdir(source):
        path = os.path.join(source, "boxes.json")
    else:
        path = source
    if not path or not os.path.exists(path):
        return []
    with open(path, "r") as f:
        raw = json.load(f)

    # Legacy format: plain list → treat as 1920x1080
    if isinstance(raw, list):
        key = _resolution_key(win_w, win_h)
        if key == "1920x1080":
            return [Box(entry) for entry in raw]
        # Fallback: scale from legacy data as starting point
        return [Box(_copy_entry(entry)) for entry in raw]

    # New format: dict keyed by resolution
    key = _resolution_key(win_w, win_h)
    if key in raw:
        return [Box(entry) for entry in raw[key]]

    # Fallback: find closest resolution
    fallback = _find_best_fallback(raw, win_w, win_h)
    if fallback and raw[fallback]:
        return [Box(_copy_entry(entry)) for entry in raw[fallback]]
    return []


def save_boxes(screen_dir, boxes, win_w=1920, win_h=1080):
    """Save boxes for the current resolution into boxes.json.

    Preserves other resolutions already stored in the file.
    Migrates legacy list format to dict on first save.
    """
    path = os.path.join(screen_dir, "boxes.json")
    key = _resolution_key(win_w, win_h)

    # Load existing data to preserve other resolutions
    res_dict = {}
    if os.path.exists(path):
        with open(path, "r") as f:
            raw = json.load(f)
        if isinstance(raw, list):
            # Migrate legacy list → dict under "1920x1080"
            res_dict["1920x1080"] = raw
        elif isinstance(raw, dict):
            res_dict = raw

    # Write current resolution
    res_dict[key] = [b.to_dict() for b in boxes]

    with open(path, "w") as f:
        json.dump(res_dict, f, indent=2)


def get_stored_resolutions(screen_dir):
    """Return list of resolution keys stored in boxes.json."""
    path = os.path.join(screen_dir, "boxes.json")
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        raw = json.load(f)
    if isinstance(raw, list):
        return ["1920x1080"]
    if isinstance(raw, dict):
        return list(raw.keys())
    return []


def _copy_entry(entry):
    """Deep-copy a box dict so edits don't mutate the source."""
    import copy
    return copy.deepcopy(entry)
