"""The ship scan's SHIELDS picture: the unit with the battle status box's
own shield rings round it.

DEVIATION `scan_shield_rings`: the original's scan prints no picture of the
shield. HD drew four green arcs round the unit (work order 290); Data
decided on 6 November 2026 to show what the status box shows instead — the
rings `Draw_Ship_Status_` grows out of the unit's own outline
(cmbtdrw1.cpp:2057-2359), one ring per step of the ramp 0x50-0x57, cut per
arc by its strength. The steps are `cbstatus.shield_canvas`; this module
only builds the 98 x 98 picture from them and scales it.

The unit is drawn nose up (`cbscanview.NOSE_UP`, the same facing as the
scan's own `pics.upright`), so Front stays at the top and the arc masks of
that facing cut the right sides. A painted unit picture takes variant B's
route like the status box (`cbstatus.painted_rings`: rings grown at the
picture's k on its silhouette, the painted picture over them); the game's
own drawing is drawn from its stored pixels (`cbstatus.StatusPicture.stored`)
in its drawing's colours.

Nothing here for a unit without shields, a planet, or without the game's
art: `picture` returns None and the view keeps its arcs.
"""
import numpy as np
import pygame

from . import cbart, cbdraw, cbscanview, cbstatus

KEPT = 16


class ShieldPictures:
    """Made once per state of the shield; kept with what they were made
    from (a scan redraws every frame)."""

    def __init__(self, art, colours, unit):
        self.art, self.colours, self.unit = art, colours, unit
        self.status = cbstatus.StatusPicture()
        self._kept = {}

    def picture(self, model, size, upright):
        """The finished RGBA picture, `size` pixels square, or None."""
        sysm = getattr(model, "shield_system", None)
        if self.art is None or sysm is None or sysm[0] <= 0 or \
                int(self.unit.get("_index", 1)) == 0 or model.shield_max <= 0:
            return None
        u = dict(self.unit, facing_dir=cbscanview.NOSE_UP, shield_type=1,
                 shield_current_hits=int(sysm[0]),
                 shield_arc_max=int(model.shield_max),
                 shield_arc_current=[int(v) for v in model.arcs])
        painted = upright is not None and cbart.hd_factor(upright) > 1
        key = (id(upright) if painted else None, int(u["picture_num"]),
               int(u["previous_owner"]), int(u["owner"]),
               tuple(sorted(self.colours.items())), u["shield_current_hits"],
               u["shield_arc_max"], tuple(u["shield_arc_current"]), size)
        hit = self._kept.get(key)
        if hit is None or (painted and hit[0] is not upright):
            if len(self._kept) >= KEPT:
                self._kept.clear()
            hit = self._kept[key] = (upright, self._build(u, size, painted,
                                                         upright))
        return hit[1]

    def _build(self, u, size, painted, upright):
        art, status = self.art, self.status
        colour = cbdraw.unit_colour(self.colours, u)
        monster = cbdraw.from_monster_file(u)
        masks = status._masks(art)
        if masks is None:
            return None
        status._masks_now = masks
        out = pygame.Surface((size, size), pygame.SRCALPHA)
        x0 = cbstatus.ship_x(u["facing_dir"])
        if painted:
            got = status.painted_rings(art, colour, u, monster, upright)
            if got is None:
                return None
            rings = cbart.smooth(got[1], (size, size))
            f = cbart.hd_factor(upright)
            s = size / cbstatus.CANVAS
            pic = cbart.smooth(upright, (max(1, round(upright.get_width()
                                                      * s / f)),
                                         max(1, round(upright.get_height()
                                                      * s / f))))
            out.blit(rings, (0, 0))
            out.blit(pic, (round(x0 * s), round(11 * s)))
            return cbart.display_format(out)
        ship = status.stored(art, colour, u, monster)
        if ship is None:
            return None
        canvas, hull = cbstatus.shield_canvas(ship, u, *masks)
        pal = cbstatus.palette(art)
        rings = np.where(hull, 0, canvas).astype(np.uint8)
        box = pygame.Surface(canvas.shape[::-1], pygame.SRCALPHA)
        box.blit(cbstatus._surface(rings, rings != 0, pal), (0, 0))
        # the unit in the drawing's own colours: its palette, then the
        # owner's ramp (`CombatArt.surface`)
        from core import lbx
        name, entry = art._unit_entry(colour, u["picture_num"], monster)
        blob = art.blob(name, entry)
        upal = dict(pal)
        if blob is not None:
            head = lbx.parse_header(blob)
            if head.has_palette:
                upal.update(lbx.read_palette(blob, head.frame_count))
        if name == "cmbtshp":
            upal.update(art.ramp(colour))
        full = np.zeros_like(canvas)
        h = min(ship.shape[0], canvas.shape[0] - 11)
        w = min(ship.shape[1], canvas.shape[1] - x0)
        full[11:11 + h, x0:x0 + w] = ship[:h, :w]
        box.blit(cbstatus._surface(full, full != 0, upal), (0, 0))
        return cbart.display_format(pygame.transform.smoothscale(
            box, (size, size)))
