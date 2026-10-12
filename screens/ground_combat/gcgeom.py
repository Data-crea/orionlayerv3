"""The ground combat's geometry — work order 232 C.

`COLGCBT::Colony_Combat_Screen_` (colgcbt.cpp:165-273) draws one 640 x 480
picture. Every number below is a literal of that source (read in
`dev:doc/briefs/232-invasion-reading.md`), placed by HD into the screen
shell's content rectangle:

  the band      the two summary boxes, `Draw_Summary_Box_ATK_` at (1, 40)
                and `_DEF_` at (378, 40), each COLGCBT.LBX 21 (261 x 149)
                darkened inside — two shell panels side by side, the box's
                contents at the battlefield's scale, centred in each
  the field     the colony's scene with the units, beams and explosions on
                it — one shell panel under the band, down to the
                rectangle's bottom; the scene from `field_top` to the
                picture's foot at ONE INTEGER scale (decision 28: steps,
                never stretches) — the native picture's scale at the window
                to the step below it (`scale_for`) — centred, so the
                picture, the units'
                places and their sprites are the original's, each native
                pixel `scale` window pixels

HD EXTENSION `shell` (decisions 86-90): the original's boxes over its scene
become panels; DEVIATION `field_window`: the scene shows from `field_top`
down, as much of the sky as the panel holds (the units never stand above
y 330: `Add_Unit_` puts them at 360..444 and `Move_Is_Legal_` keeps them
under the top line, :1424-1470).
"""
import pygame

NATIVE_W, NATIVE_H = 640, 480

#: `Draw_Summary_Box_ATK_` / `_DEF_` (colgcbt.cpp:279-296, :363-384): the
#: frame COLGCBT.LBX 21 at (1, 40) / (0x17A, 0x28), darkened inside
#: (2, 0x29)..(0x103, 0xB8) / (0x17B, 0x29)..(0x27E, 0xB8).
BOX_ATK = (1, 40, 261, 188)
BOX_DEF = (378, 40, 638, 188)
BOX_W, BOX_H = 261, 149
#: The header line, centred at (0x82, 50) / (0x1FC, 50) — relative to the
#: box: 129 and 10; the lines `Print_Data_` prints at x + 9, 0xF3 wide,
#: from y 50 + 11 per row (:738-756); the troop totals
#: (`Print_Troop_Totals_`, :929-985): figures bottom-centred at y 157,
#: their three lines centred at y 158, 167, 176, spaced 261 / (kinds + 1).
HEADER_DX, HEADER_Y = 129, 50
LINE_DX, LINE_W, LINE_Y0, LINE_PITCH = 9, 0xF3, 50, 11
TOTALS_FIGURE_FOOT, TOTALS_LINES = 157, (158, 167, 176)
TOTALS_SPAN = 261
#: The title line, centred at (319, 10) (:906, :650) — HD's plate.
TITLE_CENTRE = (319, 10)
#: The colony's scene starts under the colony screen's band (`colgeom.
#: SCENE`, 152): above it the picture is the sky the boxes stand over.
SCENE_TOP = 152

BAND = ("gc_attack", "gc_defense")
FIELD = "gc_field"


def shell_boxes(layout):
    """{box name: (x, y, w, h)}: the shell's cut — the band of two panels,
    each half the rectangle, as tall as a summary box at the field's scale
    plus the panel's inset; the field panel under it to the rectangle's
    bottom (no button row: the screen has no button)."""
    from core.hud import shell
    area = shell.panels(layout, row=False)
    s = scale_for(layout, area.w)
    band_h = BOX_H * s + 2 * shell.inset(layout)
    band, field = _cut(area, layout, band_h)
    left, right = shell.split(band, layout, [1.0, 1.0])
    return {BAND[0]: tuple(left), BAND[1]: tuple(right),
            FIELD: tuple(field)}


def _cut(area, layout, band_h):
    from core.hud import shell
    g = shell.gap(layout)
    band = pygame.Rect(area.x, area.y, area.w, band_h)
    field = pygame.Rect(area.x, band.bottom + g, area.w,
                        area.bottom - band.bottom - g)
    return band, field


def scale_for(layout, width):
    """The field's integer scale: the native picture's scale at this window
    (`researchnative`'s, 2.25 at 1920 x 1080) to the step below it — 2 at
    1920 x 1080, 4 at 3840 x 2160, 3 at 3440 x 1440 — and no more than its
    640 native pixels fit `width` less the panel's inset (at least 1)."""
    from core.hud import shell
    from core.panelmap import _island
    island = int(_island()[0] * layout.scale)
    fits = int((width - 2 * shell.inset(layout)) // NATIVE_W)
    return max(1, min(island, fits))


class FieldMap:
    """Native screen pixels of the ground combat -> window pixels, one
    integer scale on both axes, the picture's foot on the panel's inner
    bottom, centred across."""

    def __init__(self, layout, panel):
        from core.hud import shell
        inner = shell.inner(pygame.Rect(panel), layout)
        self.scale = scale_for(layout, pygame.Rect(panel).w)
        s = self.scale
        #: how much of the scene the panel holds: from `top` to the foot
        self.top = max(SCENE_TOP, NATIVE_H - inner.h // s)
        self.rect = pygame.Rect(0, 0, NATIVE_W * s, (NATIVE_H - self.top) * s)
        self.rect.midbottom = inner.midbottom
        self.clip = inner

    def point(self, nx, ny):
        return (self.rect.x + nx * self.scale,
                self.rect.y + (ny - self.top) * self.scale)


class BoxMap:
    """A summary box's native pixels (relative to the box) -> window
    pixels inside its panel: the field's scale, the box centred."""

    def __init__(self, layout, panel, scale):
        from core.hud import shell
        inner = shell.inner(pygame.Rect(panel), layout)
        self.scale = scale
        self.rect = pygame.Rect(0, 0, BOX_W * scale, BOX_H * scale)
        self.rect.center = inner.center
        self.clip = inner

    def point(self, bx, by):
        return (self.rect.x + bx * self.scale, self.rect.y + by * self.scale)


#: `_colony_ground_combat_screen_help` (colgcbt.cpp:5-9): (help id, native
#: rect) — the attack box, the defense box, the whole screen last.
HELP = ((541, (1, 40, 260, 185)), (542, (378, 40, 639, 185)),
        (540, (0, 0, 639, 479)))
