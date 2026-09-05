"""Galaxy map — the decoupled HD viewport.

The snapshot carries every star's galaxy coordinate, so the HD map
does not have to show the slice orion2re is looking at: rendering can
run on its own origin and scale, and the game never learns that the
wheel zoomed. ViewControl owns that origin and scale.

What stays coupled, and how it is handled:

  * **Clicks.** INJECT_CLICK lands in the GAME's 640x480 viewport, so
    a star the game's slice does not contain is unreachable. The fix
    is to park the game at maximum zoom-out once: at max_map_scale
    its slice covers the whole galaxy to within 1-3 units on the far
    edge (505*scale/10 against MAP_MAX_X, checked for all four
    sizes). park_game() sends zoom-out steps, throttled, until the
    game reports max_map_scale. Only the zoom-OUT field is ever used;
    the zoom-in field is the one with the rubber-band trap.

  * **Ship icons.** s_ship_icon.x/y are baked in the game's screen
    space — ships.py re-anchors them (see there).

Semantics mirror the game's own triple: `x`/`y` are the galaxy
coordinates of the viewport's top-left, `scale` is a tenths divisor
(10 = 1:1), except that here all three are floats and scale moves
continuously. proxy() dresses them up as a state object so MapView,
MapContext and every renderer keep their one code path.

The wheel anchors on the pointer by construction: the galaxy point
under the cursor is read off BEFORE the scale changes and the origin
is solved so the point maps back to the same pixel AFTER. No
iteration, one closed form — `view.scale` (HD pixels per native
pixel) does not depend on map_scale, so the equation is linear.
"""
import time

from core import mapcoords as mc
from core import zoomtables as zt

#: Zoom-in limit. Scale 5 shows the map at twice the original's
#: closest view — past that the artwork runs out of pixels.
MIN_SCALE = 5.0

#: Wheel step per tick. 1.15 needs ~13 ticks from Huge's fit view
#: (30) to MIN_SCALE, which matches how trackpads and wheels feel in
#: map applications.
WHEEL_FACTOR = 1.15

#: Seconds between parking zoom-out steps, so a slow republish never
#: turns into a flood of field activations.
PARK_INTERVAL = 0.7

#: The galaxy-map zoom-out button (field 9). The zoom-in field (8) is
#: deliberately absent from this module.
ZOOM_OUT_FIELD = 9


class _ViewProxy:
    """A state whose view triple is the HD one; everything else is
    the game's. What MapView and MapContext read of the view goes
    through here, what they read of the world (stars, counts,
    MAP_MAX) falls through to the real snapshot."""

    def __init__(self, state, x, y, scale):
        self._state = state
        self.map_x = x
        self.map_y = y
        self.map_scale = scale

    def __getattr__(self, name):
        return getattr(self._state, name)


class ViewControl:
    """Origin and scale of the HD map, plus the game-parking logic."""

    def __init__(self):
        self.active = False        # False = mirror the game's view
        self.x = 0.0
        self.y = 0.0
        self.scale = 0.0
        self._park_sent = 0.0

    # ── State plumbing ───────────────────────────────────

    def proxy(self, state):
        """State object for MapView/MapContext construction."""
        if not self.active:
            return state
        return _ViewProxy(state, self.x, self.y, self.scale)

    def _adopt(self, state):
        """Start from the view the player is looking at right now."""
        self.x = float(getattr(state, "map_x", 0) or 0)
        self.y = float(getattr(state, "map_y", 0) or 0)
        self.scale = float(getattr(state, "map_scale", 0)
                           or mc.SCALE_UNIT)
        self.active = True

    def reset(self):
        """Back to mirroring the game (fit view once it is parked)."""
        self.active = False

    # ── Interaction ──────────────────────────────────────

    def zoom_at(self, view, state, mx, my, direction):
        """One wheel tick, anchored on the pixel (mx, my).

        `view` is the CURRENT frame's view (either kind); the galaxy
        point under the cursor is taken from it before anything
        changes, which is what makes the very first tick anchor
        correctly even while still mirroring the game.
        """
        gx, gy = view.to_galaxy(mx, my)
        if not self.active:
            self._adopt(state)

        factor = WHEEL_FACTOR if direction < 0 else 1.0 / WHEEL_FACTOR
        self.scale = min(self._fit_scale(state),
                         max(MIN_SCALE, self.scale * factor))

        # Solve the origin so (gx, gy) stays under the cursor:
        #   sx = off_x + ((gx - x) * 10 / ms + 21 - 22) * K
        # with K and off_x independent of ms.
        k = view.scale
        self.x = gx - ((mx - view.off_x) / k + mc.MAP_LEFT
                       - mc.MAP_ORIGIN) * self.scale / mc.SCALE_UNIT
        self.y = gy - ((my - view.off_y) / k + mc.MAP_TOP
                       - mc.MAP_ORIGIN) * self.scale / mc.SCALE_UNIT
        self._clamp(state, view)

    def pan(self, view, state, dx_px, dy_px):
        """Drag the map by a pixel delta (right-button drag)."""
        if not self.active:
            self._adopt(state)
        units_per_px = self.scale / (mc.SCALE_UNIT * view.scale)
        self.x -= dx_px * units_per_px
        self.y -= dy_px * units_per_px
        self._clamp(state, view)

    # ── Limits ───────────────────────────────────────────

    def _fit_scale(self, state):
        """The scale at which the whole galaxy fits the viewport.

        max_map_scale is exactly that value by construction
        (MAP_MAX_X / max_map_scale is a constant 50.6 across all
        galaxy sizes), so the HD zoom-out limit and the game's are
        the same view.
        """
        mms = zt.max_map_scale(getattr(state, "map_max_x", 0) or 0)
        return float(mms or 30)

    def _clamp(self, state, view):
        """Keep the viewport on the galaxy; centre an overshooting
        axis instead of pinning it to a corner."""
        nw = (mc.MAP_RIGHT - mc.MAP_LEFT) * self.scale / mc.SCALE_UNIT
        nh = (mc.MAP_BOTTOM - mc.MAP_TOP) * self.scale / mc.SCALE_UNIT
        for attr, span, limit in (
                ("x", nw, getattr(state, "map_max_x", 0) or 0),
                ("y", nh, getattr(state, "map_max_y", 0) or 0)):
            if not limit:
                continue
            if span >= limit:
                setattr(self, attr, (limit - span) / 2.0)
            else:
                value = max(0.0, min(limit - span, getattr(self, attr)))
                setattr(self, attr, value)

    # ── Game parking ─────────────────────────────────────

    def park_game(self, app, state):
        """Drive the game to maximum zoom-out, one throttled step.

        Runs only while the HD view is decoupled; while mirroring,
        the game's own view IS the picture and must not be touched.
        Uses the zoom-out field exclusively, so the game can never
        end up more zoomed in than the player left it.

        **THE TERMINATING CONDITION IS ABSOLUTE, AND THAT IS LOAD
        BEARING — do not turn it into a delta.** `current >= fit`
        compares against the target, never against the previous
        reading. It has to: the first snapshot after any send is
        serialized in the tick that CONSUMED the send
        (ext_api.cpp:341-386), so `map_scale` still reads the old
        value, and a loop that stopped on "the scale did not change"
        would park half way — at whatever zoom the game happened to
        be on, with every injected click afterwards aimed through a
        slice that no longer covers the galaxy, and nothing about the
        picture revealing it (decision 35). A stale snapshot costs
        this loop one redundant zoom-out step, which is free because
        the step clamps at the maximum.

        Audited 5 September 2026, when the colony summary's move
        chain paid for that rule; a smoke check now feeds this the
        same stale state repeatedly and fails if it stops.
        """
        if not self.active or not app.connected:
            return
        fit = self._fit_scale(state)
        current = getattr(state, "map_scale", 0) or 0
        if current >= fit:
            return
        now = time.monotonic()
        if now - self._park_sent < PARK_INTERVAL:
            return
        self._park_sent = now
        app.client.activate_field(ZOOM_OUT_FIELD)
