"""The battle's spherical blasts — work order 210 C3 and C4.

TRANSCRIPTION `spherical_sfx`: `Do_Spherical_SFX_` (cmbtspec.cpp:1589-1840)
round its source's centre, one picture a tick for frames 0..frame_count
(the last one shown twice, `Set_Animation_Frame_` holds it), two at a time
under FAST ANIMATIONS:
  type 0, 1   Plasma Flux, Pulsar (cmbtfire.cpp:1617-1621, 1576-1580):
              CMBTSFX 0x34, the source drawn over it
  type 2      Spatial Compressor (:1537-1542): CMBTSFX 6, the source over it
  type 3, 4   a ship dying in a blast (death state 3 or 4: a broken engine,
              the Quantum Detonator; `Destroy_Ship_FX_`, cmbtspec.cpp:1178-
              1188): SPHERSFX 0 / 1, the ship collapsing under it — its
              glow-0 picture turned one facing a frame and scaled from 100 %
              (type 3, less 10 a frame) or 132 % (type 4, less 8; 99 at
              most) until below 2 % (`Draw_Ship_Collapsing_`, :1558-1586)
Every live unit within the picture's half-width of the centre (not the
source, not held in stasis, not phased) shakes while the blast passes it:
by its distance in cells d = max(|dx|, |dy|) / 20 — d 1 frames 0-4, 2
frames 1-6, 3 frames 5-12, 4 from frame 9 — and, for types 2-4, while
the blast's ring (`anim_frames`, :1590-1601) reaches it.
DEVIATION `shake_random`: a shaken unit is drawn -2..+2 px off its place,
the original's numbers from the game's own `Random_(5)`, HD's from its own.
The blast is drawn on the event that fires it — a special weapon's, a
destroyed unit's — every time, whether or not anything is in reach; the
`blast_hit`s that follow carry only their damage (`cbsfx.plan`).

TRANSCRIPTION `death_picture` (work order 210 C4): a unit destroyed with
death state 1 (or 0) plays CMBTSFX 3 / 4 / 5 by size, frames 0..n-1 a tick
each, its top-left at the unit's centre less (12, 9) / (23, 20) / (47, 44),
the unit hidden from the frame `n / 2` on (cmbtspec.cpp:1192-1276).
"""
import random

from . import cbdraw

#: Weapon -> blast type (cmbtfire.cpp:1537-1621).
AREA = {13: 2, 36: 1, 44: 0}
#: Blast type -> (LBX, entry).
PICTURE = {0: ("cmbtsfx", 0x34), 1: ("cmbtsfx", 0x34), 2: ("cmbtsfx", 6),
           3: ("sphersfx", 0), 4: ("sphersfx", 1)}
#: `anim_frames[125]`: the ring's radius by type * 25 + frame (:1590-1601).
RING = (0,) * 75 + (0xd, 0xd, 0x16, 0x2e, 0x3d, 0x3d, 0x56, 0x5f, 0x6b,
                    0x72, 0x76) + (0,) * 14 + (
    0xd, 0x10, 0x19, 0x1e, 0x23, 0x23, 0x23, 0x23, 0x23, 0x23, 0, 0, 0xb,
    0x15, 0x2d, 0x40, 0x41, 0x55, 0x61, 0x6c, 0x73, 0x73, 0, 0, 0)
#: `Destroy_Ship_FX_`'s death picture by size: (entry, x, y off the centre).
DEATH = {0: (3, -12, -9), 1: (4, -23, -20), 2: (4, -23, -20),
         3: (5, -47, -44), 4: (5, -47, -44), 5: (5, -47, -44)}


def ring(kind, frame):
    i = kind * 25 + frame
    return RING[i] if 0 <= i < len(RING) else 0


def shaken(kind, frame, ratio, dist_sq, size_class):
    """Whether a unit `ratio` cells off (`dist_sq` px²) is drawn shaken in
    this frame (:1741-1779)."""
    if kind <= 2 and ((frame < 5 and ratio == 1) or
                      (0 < frame < 7 and ratio == 2) or
                      (4 < frame < 13 and ratio == 3) or
                      (frame > 8 and ratio == 4)):
        return True
    if kind in (0, 1):
        return False
    r = ring(kind, frame)
    if dist_sq <= r * r + int(size_class) * 25:
        return r < 85 or dist_sq <= r * r - 625
    return False


def in_reach(units, source, centre, radius_sq):
    """[(unit, ratio, dist_sq)] the blast reaches (:1677-1706)."""
    out = []
    for i, u in enumerate(units):
        if i == 0 or i == source or u["unit_status"] != 0 or \
                u.get("stasis_source_idx", 255) != 255 or \
                int(u.get("special_status_flag", 0)) == 4:
            continue
        cx, cy = cbdraw.centre(u)
        dx, dy = cx - centre[0], cy - centre[1]
        d2 = dx * dx + dy * dy
        if d2 <= radius_sq:
            out.append((i, int(max(abs(dx), abs(dy)) // 20), d2))
    return out


def plan(player, source, kind, art, rng=random):
    """The blast of `kind` round unit `source` of the shown battle: a dict
    with its `frames`, `draw(surface, cam, cache, frame)` and `finish()`,
    or None."""
    units = player.shown["units"] if player.shown else []
    if not 0 <= source < len(units) or art is None:
        return None
    src = units[source]
    lbx_name, entry = PICTURE[kind]
    n = max(1, art.frame_count(lbx_name, entry))
    pic0 = art.surface(lbx_name, entry, 0)
    half = (pic0.get_width() // 2) if pic0 is not None else 0
    centre = cbdraw.centre(src)
    reach = in_reach(units, source, centre, half * half)
    colours = player.colours

    def draw(surface, cam, cache, frame):
        for i, ratio, d2 in reach:
            u = units[i]
            u["_off"] = (rng.randint(-2, 2), rng.randint(-2, 2)) if shaken(
                kind, frame, ratio, d2, u["size_class"]) else (0, 0)
        if kind >= 3 and src["unit_status"] == 0:
            pct = (100 - 10 * frame) if kind == 3 else (132 - 8 * frame)
            if pct < 2:
                src["unit_status"] = 5
            else:
                _collapsing(surface, cam, cache, art, colours, src, frame,
                            min(99, pct) / 100.0, centre)
        _centred(surface, cam, cache, art.surface(lbx_name, entry,
                                                  min(frame, n - 1)), centre)
        if kind <= 2 and src["unit_status"] == 0:
            pic = cbdraw.unit_picture(art, colours, src, 0)
            if pic is not None:
                surface.blit(cbdraw.scaled(pic, cam.scale, cache),
                             cam.to_window(*cbdraw.sprite_origin(src)))

    def finish():
        for i, _r, _d in reach:
            units[i].pop("_off", None)
        if kind >= 3:
            src["unit_status"] = 5

    return {"frames": n + 1, "draw": draw, "finish": finish}


def _centred(surface, cam, cache, pic, at):
    if pic is None:
        return
    img = cbdraw.scaled(pic, cam.scale, cache)
    x, y = cam.to_window(*at)
    surface.blit(img, (x - img.get_width() // 2, y - img.get_height() // 2))


def _collapsing(surface, cam, cache, art, colours, u, frame, pct, at):
    turned = dict(u, facing_dir=(int(u["facing_dir"]) + int(frame)) & 15)
    pic = cbdraw.unit_picture(art, colours, turned, 0)
    if pic is not None:
        _centred(surface, cam, cache, cbdraw.scaled(pic, pct, {}), at)


def death_plan(u, art, step=1):
    """`Destroy_Ship_FX_`'s plain death (`death_picture`): (entry, frames,
    top-left offset)."""
    entry, ox, oy = DEATH.get(int(u["size_class"]), DEATH[1])
    # without the player's art the picture's length is unknown: 18 frames,
    # the playback's old fixed length
    n = (art.frame_count("cmbtsfx", entry) if art else 0) or 18
    return entry, n, (ox, oy)
