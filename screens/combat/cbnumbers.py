"""The damage numbers over a hit unit — work order 265.

TRANSCRIPTION of `BEAMS::Add_Damage_Indicator_For_Ship` and
`Draw_Damage_Indicator` (beams.cpp:245-266, :312-364): every hit queues two
numbers, the damage through the shields (`total_dmg`) and the damage the
shields took (`hull_dmg` in the source's names; `Apply_Ship_Damage`'s
`sys_dmg` is the shield arc's hits spent, cmbtfire.cpp:975-990 — work order
267 corrected the "structure" of 265), each drawn only when above 0; the
damage at the point, the shields' 20 native px to its left (a third place, 10 px left, is the shield's, and
no caller fills it). The point is the unit's centre (`Ship_Center_Offsets`)
moved by its size class x 8 up and to the side; for 9 frames of a tick
each the numbers rise 1 px and drift 1 px to that side, then they are gone.
Each frame takes its colours from its own three entries of a ramp: the
damage from 0xB0-0xBA (orange, fading to dark red), the shields' from
0xC0-0xCC (blue-violet); the first entry is the shadow, one pixel down
(`Set_Font_Style_Shadow_Down`), the second the glyph.

Every hit event carries both values (open fix 56): `past_shields` is
`accum_hit_x` / `dmg_accum` / `total_damage`, `absorbed` is `accum_hit_y` /
`sys_dmg_accum` / `struct_damage` (the shields' share, whatever the name) (cmbtfire.cpp:1497, cmbtmis.cpp:886,
cmbtspec.cpp:1989, combinit.cpp:3306). Until work order 265 HD drew only
the first, in one yellow.

The side: a beam's is `Do_Get_SFX_Draw_Shield_Facing` (beams.cpp:2092-
2095, the facing from target to attacker, right when `(f + 4) % 16 < 8`);
every other caller passes 1, right.

DEVIATION `number_size`: Font 1's digits are 6 native px tall (measured on
the original running alone, work order 260's capture at +2.85 s: "480",
rows 211-216 of 480); HD draws them 6 world px tall at the camera's scale,
but never smaller than at the original's framing (32 cells across) — the
whole field zoomed out keeps them readable, zoomed in they grow with the
ships as the original's would. The original has no zoom.
"""
import pygame

#: The colour steps, three entries a frame (beams.cpp:313-321).
TOTAL_STEPS = (0xb0, 0xb9, 0xba, 0xb0, 0xb8, 0xb9, 0xb0, 0xb7, 0xb8, 0xb0,
               0xb6, 0xb7, 0xb0, 0xb5, 0xb6, 0xb0, 0xb4, 0xb5, 0xb0, 0xb3,
               0xb4, 0xb0, 0xb2, 0xb3, 0xb0, 0xb1, 0xb2)
HULL_STEPS = (0xc0, 0xcc, 0xc5, 0xc0, 0xcc, 0xc5, 0xc0, 0xcc, 0xc5, 0xc0,
              0xc4, 0xcc, 0xc0, 0xcb, 0xc4, 0xc0, 0xc3, 0xcb, 0xc0, 0xc3,
              0xcb, 0xc0, 0xca, 0xc3, 0xc0, 0xc2, 0xca)
#: Without the player's palette (a fresh clone): the ramps' first frame,
#: read off the game's combat palette — (shadow, glyph).
FALLBACK = {"total": ((80, 4, 0), (252, 164, 28)),
            "hull": ((4, 0, 56), (60, 56, 184))}
FRAMES = 9
HULL_DX = -20
DIGIT_PX = 6
FRAMING_CELLS = 32
CELL = 20


def side_of(target_centre, attacker_centre, get_angle):
    """`Do_Get_SFX_Draw_Shield_Facing(attacker, target)`: 1 right, 0 left."""
    tx, ty = target_centre
    ax, ay = attacker_centre
    facing = (get_angle(tx - ax, ay - ty) // 22) % 16
    return 1 if (facing + 4) % 16 < 8 else 0


def mark(unit_centre, size_class, total, hull, t0, side=1):
    """A queued pair, or None when neither is above 0."""
    total, hull = int(total or 0), int(hull or 0)
    if total <= 0 and hull <= 0:
        return None
    off = max(0, min(5, int(size_class))) * 8
    x, y = unit_centre
    return {"x": x + (off if side else -off), "y": y - off, "t0": t0,
            "side": side, "total": total, "hull": hull}


def digit_px(cam):
    """The digits' height in window px (DEVIATION `number_size`)."""
    framing = cam.area[2] / (FRAMING_CELLS * CELL)
    return DIGIT_PX * max(cam.scale, framing)


def _colours(steps, frame, palette, kind):
    pal = palette or {}
    shadow, glyph = pal.get(steps[frame * 3]), pal.get(steps[frame * 3 + 1])
    if shadow is None or glyph is None:
        return FALLBACK[kind]
    return tuple(shadow[:3]), tuple(glyph[:3])


def _text(style, text, px, rgb, cache):
    """The number at a font size whose digits are `px` tall."""
    key = (text, round(px), rgb)
    img = cache.get(key)
    if img is None:
        probe = style.render_text("0", 100, (255, 255, 255))
        ink = max(1, probe.get_bounding_rect().h)
        size = max(8, int(round(100 * px / ink)))
        img = style.render_text(text, size, rgb)
        if len(cache) > 256:
            cache.clear()
        cache[key] = img
    return img


def draw(surface, cam, style, marks, now, frame_s, palette, cache):
    """Draw the live pairs; return the ones still to come or rising."""
    keep = []
    px = digit_px(cam)
    for m in marks:
        age = now - m["t0"]
        if age < 0:
            keep.append(m)
            continue
        frame = int(age / frame_s)
        if frame >= FRAMES:
            continue
        keep.append(m)
        dx = frame if m["side"] else -frame
        for kind, value, steps, ox in (("total", m["total"], TOTAL_STEPS, 0),
                                       ("hull", m["hull"], HULL_STEPS,
                                        HULL_DX)):
            if value <= 0:
                continue
            shadow, glyph = _colours(steps, frame, palette, kind)
            x, y = cam.to_window(m["x"] + ox + dx, m["y"] - frame)
            down = max(1, int(round(px / DIGIT_PX)))
            img = _text(style, str(value), px, glyph, cache)
            top = y - img.get_bounding_rect().y
            surface.blit(_text(style, str(value), px, shadow, cache),
                         (x, top + down))
            surface.blit(img, (x, top))
    return keep
