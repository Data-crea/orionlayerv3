"""galaxy_inset — the original's small galaxy map, bottom right.

A TRANSCRIPTION. `COLSUM::Draw_Galaxy_Map_` (colsum.cpp:415) is one
call, `MOVEBOX::Draw_Galaxy_Map_Box_(nullptr, 0, 0x17c, 0x15d, 0x80,
0x5b, 0, 0, 0, 0, 3, 0)` — native (380, 349, 128, 91), view_mode 3 —
and under that mode the function draws one sprite per star and
nothing else. `COLSUM::Draw_Scan_Info_` then prints the scanned
star's name centred at native (444, 431) (colsum.cpp:86).

The positions and the colour rule are in `colonyrows`, with this
screen's seam: all struct reading lives there and this module is
handed plain tuples.

**THE SPRITE IS MEASURED, because it cannot be shipped.** view_mode 3
draws `MOX::_colony_galaxy_star_seg[color_idx]` at (sx - 1, sy - 1)
(movebox.cpp:99-102), and those are gstar.lbx entries 23..32
(colony.cpp:329-338) — the player's own LBX, which this project does
not redistribute, the same wall the Buy button's artwork and the
morale sprites hit. So the shape was read off the original's own
framebuffer through the Extension API on 4 September 2026, which is
a measurement of the thing itself rather than an estimate:

    a star           a black hole
     .  D  .          d  B  d
     D  B  D          B  k  B
     .  D  .          d  B  d

Three by three, centred on (sx, sy) — which is exactly why the
original's draw call offsets by one. `B` is the bright shade, `D`/`d`
the dark one, `k` a near-black core. Two shades per colour, and the
pairs the reference save exposed, as palette RGB:

    idx 0  (148, 12,  4) / (236, 24, 12)      player colour 0
    idx 1  (168,140,  8) / (224,200, 56)      player colour 1
    idx 2  ( 24,120, 20) / ( 48,196, 36)      player colour 2
    idx 6  ( 68, 36, 92) / (140, 72,140)      player colour 6
    idx 7  (184, 96, 16) / (236,140, 48)      player colour 7
    idx 8  (104,132,156) / (172,212,240)      unowned, visited
    idx 9  ( 96, 56,128) / (152, 96,196)      black hole

**Colours 3, 4 and 5 have no witness.** No player in the reference
save carries them, so their pairs were never read. The HD colours do
not come from that table anyway — see `INSET_COLORS` — but the table
is what the HD ones were checked against, and three of the ten were
not checkable.

**DEVIATIONS, all three of them marked here and in layout.json:**

1. **The sprite is drawn, not blitted.** A 3x3 pattern scaled to the
   panel, rather than the original's artwork, because the artwork is
   in the user's LBX. Same trade as `list._buy_note`.
2. **The colours are the skin's, not the game's palette.** The eight
   owner colours already exist in `galaxy_map.renderer.OWNER_COLORS`,
   checked against the original once and skin-overridable; a second
   hardcoded table read off one savegame would be the third copy of a
   name table this project has already been bitten by twice. The dark
   shade is the bright one dimmed by one factor, where the original
   has a hand-picked palette pair per colour — the measured ratios
   run 0.5 to 0.78 and this uses one number for all of them.
3. **The map does not fill the hole.** See `map_rect`.

**NOT DRAWN, and recorded rather than left to be noticed:**

  the scanned star ANIMATES.  view_mode 3 resets every star's
                              animation frame EXCEPT the scanned one
                              (movebox.cpp:98-101), so that star
                              cycles its sprite while the rest stand
                              still. Reachable — the selection is
                              known — and not drawn because the
                              frames are in the same unshipped LBX.
  the stars are FIELDS.       `_galaxy_map_star_field[]`
                              (colsum.cpp:69-75): hovering a star in
                              the original's inset sets the scanned
                              star AND moves `_g_colony_n` to the
                              best colony there. Not drawn and not
                              wired; this screen's inset is display
                              only.
  the CONNECT line.           `Colsum_Connect_Galaxy_Map_Stars_`
                              (colsum.cpp:731) draws an animated
                              multi-coloured line between two stars,
                              and its caller (colsum.cpp:487-498)
                              fires only while `COLMOVE::
                              _cluster_colony_n != -1` — a population
                              transfer being dragged from one colony
                              to another. OrionLayer has no colonist
                              dragging, so there is no state in which
                              this line would be drawn. Written down
                              because "Connect" reads like a
                              permanent feature of the map and is not
                              one.
"""
import pygame

from core import palette
from screens.galaxy_map.renderer import OWNER_COLORS

#: Colour index -> the BRIGHT shade. 0..7 are player colours and come
#: from the galaxy map's table, which is the one home for them
#: (decision 15, and the name-table lesson in the fundament). 8 and 9
#: are this panel's own and are skin-overridable beside them.
INSET_COLORS = dict(OWNER_COLORS)
INSET_COLORS[8] = palette.col("colony_summary", "inset_star",
                              (172, 212, 240))
INSET_COLORS[9] = palette.col("colony_summary", "inset_black_hole",
                              (152, 96, 196))

#: The dark shade, as a fraction of the bright one. The original has
#: a hand-picked palette pair per colour and the measured ratios run
#: 0.5 to 0.78; one number for all of them is the deviation, and 0.62
#: is the middle of what was measured rather than a taste.
DARK_FACTOR = 0.62

LABEL_COLOR = palette.col("colony_summary", "inset_label",
                          (150, 160, 184))

#: The scanned star's name, native (444, 431) — colsum.cpp:86 —
#: expressed against the inset box's own origin (380, 349) so it
#: moves with the box rather than with the screen.
LABEL_NATIVE = (444 - 380, 431 - 349)


def _dark(colour):
    return tuple(int(c * DARK_FACTOR) for c in colour[:3])


def map_rect(area):
    """Where the original's 128x91 box lands inside the cutout.

    **UNIFORM SCALE, CENTRED, LETTERBOXED** — the same rule
    `core.mapcoords.MapView` already applies when it puts the
    original's map into an HD box, and for the same reason: a galaxy
    is a shape, and the box it goes in does not have to be the shape
    the original's box was.

    It matters here because the cutout is NOT the original's box.
    `galaxy_inset` is 451 x 203 reference px; the original's map is
    128 x 91 native, which is 1.407 wide and the hole is 2.222. The
    hole is not in the same place either — it starts at reference x
    1056 while the original's box maps to 1140, so a box drawn where
    the original puts it would hang 17 px past the hole's right edge.

    Height is therefore what binds: 203/91 = 2.23, giving 285 x 203
    with about 83 px of panel either side. **That margin is the
    deviation and it is visible.** The alternative that fills the
    hole is 384 x 203 — one native pixel to this screen's own
    reference factors, 3 across and 2.25 down — and it was built and
    rejected on the side-by-side: it stretches the galaxy 33 %
    horizontally, and the constellation stops matching the original's
    even though every star is at its own correct fraction of the box.

    Not fixed by widening the frame's hole either, which would be
    deriving artwork from a deviation to make the deviation go away
    (decision 44's second half). If this hole should be 128:91, that
    is an artwork decision with its own reasons.

    `REF_W`/`REF_H` are not used for the scale for exactly that
    reason, and are kept out of this function rather than being
    available to reach for.
    """
    scale = min(area.w / 128.0, area.h / 91.0)
    w, h = int(round(128 * scale)), int(round(91 * scale))
    return pygame.Rect(area.x + (area.w - w) // 2,
                       area.y + (area.h - h) // 2, w, h)


def star_points(stars, rect):
    """(x, y, colour index, cell_w, cell_h) in screen pixels.

    `stars` is `colonyrows.galaxy_inset_stars` output — native
    offsets inside the 128x91 box. One function makes this and both
    the drawing and any future hit-test call it (decision 5).
    """
    cw = max(1, int(round(rect.w / 128.0)))
    ch = max(1, int(round(rect.h / 91.0)))
    out = []
    for nx, ny, cidx in stars:
        out.append((rect.x + int(nx * rect.w / 128.0),
                    rect.y + int(ny * rect.h / 91.0), cidx, cw, ch))
    return out


def _blit_sprite(surface, x, y, cidx, cw, ch):
    """The measured 3x3, one native pixel per (cw, ch) cell.

    Centred on (x, y) rather than drawn from (x - 1, y - 1) scaled:
    the original's offset IS a centring on a 3x3 sprite, and saying
    so in the code keeps the intent when the cell stops being 1 px.
    """
    bright = INSET_COLORS.get(cidx, INSET_COLORS[8])[:3]
    dark = _dark(bright)
    left, top = x - cw, y - ch
    if cidx == 9:
        # A ring: bright edges, dim corners, near-black core.
        for col in range(3):
            for row in range(3):
                if col == 1 and row == 1:
                    continue
                shade = bright if (col == 1 or row == 1) else dark
                surface.fill(shade, (left + col * cw, top + row * ch,
                                     cw, ch))
        surface.fill(_dark(dark), (left + cw, top + ch, cw, ch))
        return
    surface.fill(dark, (left + cw, top, cw, ch))
    surface.fill(dark, (left, top + ch, cw, ch))
    surface.fill(bright, (left + cw, top + ch, cw, ch))
    surface.fill(dark, (left + 2 * cw, top + ch, cw, ch))
    surface.fill(dark, (left + cw, top + 2 * ch, cw, ch))


def render(surface, stars, label, area, cfg, layout, style):
    """Draw the inset into `area`, the `galaxy_inset` cutout.

    `stars` is `colonyrows.galaxy_inset_stars` output and `label` is
    `galaxy_inset_label`'s — plain data, no structs.

    **NOTHING IS DRAWN BEHIND THE STARS, and that is the original's
    own behaviour rather than an omission.** `Draw_Galaxy_Map_Box_`
    fills its box with black only when
    `_using_colony_screen_palette == 0` (movebox.cpp:36-38), and this
    screen sets that flag — so the original leaves whatever the
    screen background put there showing through, which on a native
    capture is the faint star texture of `_anims[0]`. Here the panel
    fill `screen._render_panels` already laid down plays that part.
    """
    if not stars:
        return
    rect = map_rect(area)
    for x, y, cidx, cw, ch in star_points(stars, rect):
        _blit_sprite(surface, x, y, cidx, cw, ch)
    if not label:
        return
    size = layout.font_size(cfg.get("label_font", 15))
    text = style.render_text(str(label), size, LABEL_COLOR[:3])
    lx = rect.x + int(LABEL_NATIVE[0] * rect.w / 128.0)
    ly = rect.y + int(LABEL_NATIVE[1] * rect.h / 91.0)
    surface.blit(text, (lx - text.get_width() // 2,
                        min(ly, area.bottom - text.get_height())))
