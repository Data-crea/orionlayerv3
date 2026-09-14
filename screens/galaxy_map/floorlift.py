"""The map floor lift for OLED panels — an HD EXTENSION (fundament 63).

MOO2 has no user-adjustable floor. On an OLED panel the galaxy map's
near-black floor crushes to pure off-pixels and the faint gas of
`map_background.png` disappears; a small constant added to the floor
brings it back. On any other panel it is a grey veil, so the default
is `off`.

**ONE APPLICATION POINT.** `_render_map` calls `apply` once, after the
floor is drawn and before the star field, so the lift reaches the floor
whichever path drew it — the graphic, or the `map_background` fill a
tree without the graphic uses. Nothing else in the map is lifted: the
stars, nebulas, names and fleets are drawn after it.

**AN ADDITIVE FILL.** `surface.fill(lift, rect, BLEND_RGB_ADD)` on the
drawn floor gives, pixel for pixel, the same as filling with the lift
and blitting the floor additively on top — the form the brief measured
— and it needs no second copy of the floor. The smoke test holds the
two equal byte for byte. With step `off` nothing is called at all, so
the map is the map it always was.

**READ AT DRAW TIME, so the change is live**: the step comes from the
player's settings (`core.usersettings`) on every frame, and the Game
Settings screen behind the open popup shows it at once. The colours of
the steps are the skin's (`galaxy_map` floor_lift_light / _haze), with
their measurement next to them.
"""
import pygame

from core import palette

OFF, LIGHT, HAZE = "off", "light", "haze"
STEPS = (OFF, LIGHT, HAZE)

LIFT = {
    OFF: (0, 0, 0),
    LIGHT: palette.require("galaxy_map", "floor_lift_light"),
    HAZE: palette.require("galaxy_map", "floor_lift_haze"),
}


def step(app):
    """The player's step, or `off` for anything unknown or absent."""
    settings = getattr(app, "user_settings", None)
    value = settings.get("floor_lift") if settings is not None else OFF
    return value if value in STEPS else OFF


def apply(surface, rect, app):
    """Lift the floor inside `rect`. Returns the lift that was added."""
    lift = tuple(LIFT[step(app)][:3])
    if any(lift):
        surface.fill(lift, rect, special_flags=pygame.BLEND_RGB_ADD)
    return lift
