"""One shot of the battle, drawn — work order 199 C2, out of `cbplay` (the
line guideline). `cbplay` plans the shot (`Player._beam`) and calls this
for each frame; the bolt itself is `cbbeam`'s port (TRANSCRIPTION
`beam_bolt` there).
"""
import pygame

from . import cbbeam, cbdraw


def draw(surface, cam, art, ev, b, t, cache, palettes):
    """One frame of the shot: the muzzle burst on the first three, the
    bolt, the hit flash at the end (beams.cpp:2294-2479)."""
    n = b["frames"]
    frame = min(n + 1, int(t * (n + 2)))
    key = ("beam", ev.get("seq"), ev.get("serial"), frame,
           round(cam.scale, 3))
    if key not in cache:
        px = cbbeam.shot(b["src"], b["dst"], b["fx"], frame, b["stop"],
                         ev.get("seq", 0) or 0)
        cols = cbbeam.colours(b["fx"])
        if b["fragment"] is not None:
            cols = cbbeam.fragment_colours(art, b["fragment"]) or cols
        img = None
        if px:
            xs = [p[0] for p in px]
            ys = [p[1] for p in px]
            x0, y0 = min(xs), min(ys)
            img = pygame.Surface((max(xs) - x0 + 1, max(ys) - y0 + 1),
                                 pygame.SRCALPHA)
            for (x, y), c in px.items():
                img.set_at((x - x0, y - y0), cols[max(0, min(15, c))])
            img = (cbdraw.scaled(img, cam.scale, {}), (x0, y0))
        cache[key] = img
    if cache[key] is not None:
        img, (x0, y0) = cache[key]
        surface.blit(img, cam.to_window(x0, y0))
    # the burst and the flash paint with the beam slots 0x90-0xAF, which
    # the original fills with the weapon's colours as it fires
    # (Set_Beam_Colors_; BEAMS 1-32 and 65/66 use nothing else) — one
    # palette object per colour set, as `cbart` caches by it
    cols = cbbeam.colours(b["fx"])
    pal = palettes.setdefault(tuple(cols), {
        **{0x90 + i: c for i, c in enumerate(cols)},
        **{0xA0 + i: c for i, c in enumerate(cols)}})
    stream = 0
    if frame < 3:                         # Draw_Ship_Burst_, :2445-2452
        pic = art.surface("beams", cbbeam.muzzle_entry(
            b["src"], b["dst"], stream), frame % 3, pal)
        if pic is not None:
            img = cbdraw.scaled(pic, cam.scale, cache)
            x, y = cam.to_window(*b["src"])
            surface.blit(img, (x - img.get_width() // 2,
                               y - img.get_height() // 2))
    if ev.get("result", 0) & 3 and frame >= n - 2:   # :2459-2477
        cnt = max(2, art.frame_count("beams", 0x41 + stream))
        pic = art.surface("beams", 0x41 + stream,
                          (frame - n + 7) % (cnt - 1), pal)
        if pic is not None:
            img = cbdraw.scaled(pic, cam.scale, cache)
            surface.blit(img, cam.to_window(b["dst"][0] - 8,
                                            b["dst"][1] - 8))
