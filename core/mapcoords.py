"""Galaxy coordinates <-> orion2re's 640x480 map, and -> HD.

Transcribed from orion2re, not measured. The relevant sources:

  HAROLD::Get_Scaled_Value_(v)      harold.cpp
      return v * 10 / MOX::_cur_map_scale

  MAINSCR::Get_Star_Draw_Coords_()  mainscr.cpp
      out_x = Get_Scaled_Value_(star.x - _cur_map_x) + 0x15
      out_y = Get_Scaled_Value_(star.y - _cur_map_y) + 0x15

  MAINSCR::Star_On_Screen_()        mainscr.cpp
      visible when 0x15 < x < 0x20f and 0x15 < y < 0x1a5

MAINSCR::Draw_Nebulae_() uses the identical transform, so stars and
nebulas share one code path here.

ANCHOR POINTS DIFFER — this bites if ignored:
  stars        Get_Star_Draw_Coords_ returns the CENTER; the sprite
               is drawn at center - dimension/2
               (Draw_Scaled_Star_Picture_)
  nebulas      animate::Draw_ is called with the transformed point
               directly, i.e. it is the TOP-LEFT of the sprite
  ship icons   s_ship_icon.x/y are already screen coordinates and
               also TOP-LEFT (Draw_Ship_Icons_ stores exactly what
               Get_Ship_Icon_Coords_ returned)

Map scale per galaxy size (mapgen.cpp), scale 10 == 1:1:
  Small   MAP_MAX 506 x 400   scale 10   zoom levels 0..0
  Medium  MAP_MAX 759 x 600   scale 15   zoom levels 0..1
  Large   MAP_MAX 1012 x 800  scale 20   zoom levels 0..2
  Huge    MAP_MAX 1518 x 1200 scale 30   zoom levels 0..3

Note the 15: an earlier empirical guess assumed the scales were
1, 1/2 and 1/3 only, which silently mis-places every star in a
medium galaxy.
"""

#: The original map viewport in 640x480 space. Values from
#: Star_On_Screen_() / the Set_Window_ call in Print_Star_Names_.
MAP_ORIGIN = 0x15          # 21 — added after scaling
MAP_LEFT, MAP_TOP = 0x16, 0x16        # 22, 22
MAP_RIGHT, MAP_BOTTOM = 0x20F, 0x1A5  # 527, 421

#: _cur_map_scale is a tenths-based divisor; 10 means 1:1.
SCALE_UNIT = 10


def scaled(value, map_scale):
    """HAROLD::Get_Scaled_Value_ — integer division, as in C."""
    if not map_scale:
        map_scale = SCALE_UNIT
    return int(value) * SCALE_UNIT // int(map_scale)


def up_scaled(value, map_scale):
    """HAROLD::Get_Up_Scaled_Value_ — the inverse of scaled()."""
    if not map_scale:
        map_scale = SCALE_UNIT
    return int(value) * int(map_scale) // SCALE_UNIT


def _view_params(state):
    """(map_x, map_y, map_scale), tolerating a partial state.

    A snapshot can arrive before the map globals are populated
    (main menu, mid-transition). Falling back to scale 10 / origin
    0 keeps the transform defined instead of raising.
    """
    return (getattr(state, "map_x", 0) or 0,
            getattr(state, "map_y", 0) or 0,
            getattr(state, "map_scale", 0) or SCALE_UNIT)


def galaxy_to_native(gx, gy, state):
    """Galaxy coordinate -> 640x480 map point (star CENTER).

    `state` is a GameState carrying map_scale / map_x / map_y.
    """
    mx, my, ms = _view_params(state)
    return (scaled(gx - mx, ms) + MAP_ORIGIN,
            scaled(gy - my, ms) + MAP_ORIGIN)


def native_to_galaxy(nx, ny, state):
    """640x480 map point -> galaxy coordinate.

    Lossy: scaled() truncates, so a round trip can differ by up to
    one map_scale step. Fine for "which star did the user mean",
    not for storing positions.
    """
    mx, my, ms = _view_params(state)
    return (up_scaled(nx - MAP_ORIGIN, ms) + mx,
            up_scaled(ny - MAP_ORIGIN, ms) + my)


def on_screen(nx, ny):
    """MAINSCR::Star_On_Screen_ — strict bounds, as in the original."""
    return (MAP_ORIGIN < nx < MAP_RIGHT
            and MAP_ORIGIN < ny < MAP_BOTTOM)


class MapView:
    """Maps galaxy coordinates into an HD box on screen.

    The HD map box is free — it does not have to mirror the
    original's 22..527 viewport. Everything the game sees still
    goes through the native transform above, so clicks land where
    orion2re expects them.

    `box` is a window rect (x, y, w, h) in pixels.
    """

    def __init__(self, box, state):
        self.box = box
        self.state = state
        bx, by, bw, bh = box

        # The visible slice of the map in native pixels.
        native_w = MAP_RIGHT - MAP_LEFT
        native_h = MAP_BOTTOM - MAP_TOP
        # Uniform scale so the aspect ratio survives; the map is
        # centred in the box and letterboxed if the box is a
        # different shape.
        self.scale = min(bw / native_w, bh / native_h)
        self.off_x = bx + (bw - native_w * self.scale) / 2
        self.off_y = by + (bh - native_h * self.scale) / 2

    def to_screen(self, gx, gy):
        """Galaxy coordinate -> HD pixel (centre point)."""
        nx, ny = galaxy_to_native(gx, gy, self.state)
        return (self.off_x + (nx - MAP_LEFT) * self.scale,
                self.off_y + (ny - MAP_TOP) * self.scale)

    def to_native(self, sx, sy):
        """HD pixel -> 640x480 map point, for INJECT_CLICK."""
        nx = (sx - self.off_x) / self.scale + MAP_LEFT
        ny = (sy - self.off_y) / self.scale + MAP_TOP
        return int(round(nx)), int(round(ny))

    def to_galaxy(self, sx, sy):
        """HD pixel -> galaxy coordinate (float)."""
        mx, my, ms = _view_params(self.state)
        nx = (sx - self.off_x) / self.scale + MAP_LEFT
        ny = (sy - self.off_y) / self.scale + MAP_TOP
        return ((nx - MAP_ORIGIN) * ms / SCALE_UNIT + mx,
                (ny - MAP_ORIGIN) * ms / SCALE_UNIT + my)

    def star_click_target(self, star):
        """The 640x480 point to click to select `star`.

        Uses the star's own coordinates rather than the cursor
        position, so the click lands dead centre on what the user
        picked in HD even when the HD icon is far larger than the
        original's few pixels.
        """
        return galaxy_to_native(star.x, star.y, self.state)


class SmoothMapView(MapView):
    """MapView with float precision, for the decoupled HD viewport.

    The base class transcribes the original's integer transform
    (`scaled()` truncates like the C code), which is right for
    everything the game sees — but a viewport the game does NOT see
    has no reason to inherit the truncation. At an intermediate
    scale like 12.7 the integer path would snap every star to whole
    native pixels, and one native pixel is several HD pixels: stars
    would wobble against each other while panning.

    Same (map_x, map_y, map_scale) semantics, so `state` can be a
    proxy carrying the HD view's own values. `to_native` stays
    integer — its only consumer is INJECT_CLICK, and half pixels do
    not exist on the wire — but everything drawn goes through the
    float path.
    """

    def to_screen(self, gx, gy):
        mx, my, ms = _view_params(self.state)
        nx = (gx - mx) * SCALE_UNIT / ms + MAP_ORIGIN
        ny = (gy - my) * SCALE_UNIT / ms + MAP_ORIGIN
        return (self.off_x + (nx - MAP_LEFT) * self.scale,
                self.off_y + (ny - MAP_TOP) * self.scale)
