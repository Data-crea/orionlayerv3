"""The GAME menu's Music and Sound Fx volume bars — work order 124, item C.

TRANSCRIBED (layout.json `sliders._note` carries every source line): two
scroll fields at native (206, 219) and (206, 241), 155 x 12, value 0..156
from `fields::Find_Bar_Position_`, stored as `level = value * 100 / 155` in
`_settings` (on at more than 5), drawn as GAME.LBX picture 7 — ten blocks —
revealed up to `value` pixels, so a block can show partly lit. The value
HD draws is read off the snapshot's `_settings` (`value = level * 155 /
100`, loadsave.cpp:1139-1140), never remembered.

HOW IT REACHES THE GAME: an `INJECT_CLICK` on the bar. Open fix 15 asked for
a command because an injected click used to lose its pointer; open fix 3's
second half (`doc/ext_inject_click.patch`, applied) suppresses the mouse
sync while injected input is unconsumed, and a live click at native
(321, 247) set Sound Fx 50 -> 74, the value this module's arithmetic
predicts (work order 124 C, 16 September 2026). The same patch is required:
without it the click lands but the value comes from the real pointer.

THE GESTURE is the original's: `Find_Bar_Position_` follows a held press
(fields.cpp:1387-1405, 2124), and the level is applied once the press ends
(the input loop's return, loadsave.cpp:1302-1306). HD previews the press
and the drag locally and sends nothing until release; the release sends
ONE click at the native point that yields the chosen value (decision 47's
shape). The preview is kept until a snapshot carries the sent level or
`EFFECT_PAIRS` newer snapshots have passed.
"""
from core import palette
from core.structs import settings as settings_spec
from core.wire_protocol import EFFECT_PAIRS
from screens.game_menu import gmdraw as gd, nodes

COL_OFF = palette.require("game_menu", "slider_off")
COL_ON = palette.require("game_menu", "slider_on")
COL_GLOW = palette.require("game_menu", "slider_glow")
COL_WORD = palette.require("game_menu", "button_text")

#: (bar box, label box, settings field, native y key)
BARS = {"music": ("music_bar", "music_label", "music_level", "music_y"),
        "sound": ("sound_bar", "sound_label", "sound_fx_level", "sound_y")}


def spec(screen):
    return screen.words.get("sliders") or {}


def level_to_value(level, cfg):
    """`_game_popup_fields->*_level = level * 155 / 100` (loadsave.cpp:1139)."""
    return int(level) * cfg["width"] // 100


def value_to_level(value, cfg):
    """`value * 100 / 0x9B`, and 5 or less is off (loadsave.cpp:1686-1717)."""
    level = int(value) * 100 // cfg["width"]
    return 0 if level <= 5 else level


def native_value(x, cfg):
    """`Find_Bar_Position_` for a native pointer x (fields.cpp:1707-1718)."""
    left = cfg["native_x"]
    right = left + cfg["width"]
    if x >= right:
        return cfg["range_max"]
    if x <= left:
        return 0
    return (x - left) * cfg["range_max"] // cfg["width"]


def native_x_for(value, cfg):
    """The smallest native x whose `Find_Bar_Position_` is `value`."""
    left = cfg["native_x"]
    for x in range(left, left + cfg["width"] + 1):
        if native_value(x, cfg) >= value:
            return x
    return left + cfg["width"]


def wire_value(screen, key):
    raw = getattr(screen.state, "settings_raw", b"") or b""
    if len(raw) < settings_spec.SIZE:
        return None
    level = getattr(settings_spec.parse(raw), BARS[key][2])
    return level_to_value(max(0, level), spec(screen))


def shown_value(screen, key):
    drag = getattr(screen, "slider_drag", None)
    if drag and drag["key"] == key:
        return drag["value"]
    held = (getattr(screen, "slider_sent", None) or {}).get(key)
    if held is not None:
        return held["value"]
    return wire_value(screen, key)


def _value_at(screen, key, x):
    cfg = spec(screen)
    bar = gd.rect(screen, BARS[key][0])
    frac = (x - bar.x) / max(1, bar.w)
    # A native POINTER is an integer; the game's arithmetic never yields 155
    # (x 360 gives 154, x 361 is clamped to 156), and neither may HD.
    return native_value(cfg["native_x"] + round(frac * cfg["width"]), cfg)


def render(screen, surface):
    cfg = spec(screen)
    if not cfg:
        return
    gd.panel(screen, surface, "volume_panel")
    words = cfg.get("words", {})
    for key, (bar_name, label_name, _, _) in BARS.items():
        label = gd.box(screen, label_name)
        if label is not None and label.screen_rect is not None:
            gd._blit(screen, surface, words.get(key, key),
                         gd._size(screen, label, default=30), COL_WORD,
                         label.screen_rect.x, label.screen_rect.y)
        bar = gd.rect(screen, bar_name)
        if bar is None:
            continue
        value = shown_value(screen, key)
        sx, sy = bar.w / cfg["width"], bar.h / cfg["height"]
        top, bottom = cfg["block_rows"]
        y0, y1 = bar.y + round(top * sy), bar.y + round((bottom + 1) * sy)
        screen.style.draw_plate(surface, bar, screen.layout.scale)
        for first, last in cfg["blocks"]:
            x0, x1 = bar.x + round(first * sx), bar.x + round((last + 1) * sx)
            surface.fill(tuple(COL_OFF[:3]), (x0, y0, x1 - x0, y1 - y0))
            if value is None or value <= first:
                continue
            lit = min(x1, bar.x + round(value * sx))
            surface.fill(tuple(COL_ON[:3]), (x0, y0, lit - x0, y1 - y0))
            gx0 = x0 + (x1 - x0) // 4
            gx1 = min(lit, x1 - (x1 - x0) // 4)
            gy0, gy1 = y0 + (y1 - y0) // 4, y1 - (y1 - y0) // 4
            if gx1 > gx0:
                surface.fill(tuple(COL_GLOW[:3]),
                             (gx0, gy0, gx1 - gx0, gy1 - gy0))


def press(screen, x, y):
    """True if (x, y) starts a drag on a bar; nothing is sent."""
    if screen.node != nodes.MENU or not spec(screen):
        return False
    for key, (bar_name, _, _, _) in BARS.items():
        if gd.hit(screen, bar_name, x, y):
            screen.slider_drag = {"key": key,
                                  "value": _value_at(screen, key, x)}
            return True
    return False


def motion(screen, x, y):
    drag = getattr(screen, "slider_drag", None)
    if drag:
        drag["value"] = _value_at(screen, drag["key"], x)


def release(screen, x, y):
    """End the drag: ONE injected click where the game computes the value.
    Returns the native point sent, or None."""
    drag = getattr(screen, "slider_drag", None)
    screen.slider_drag = None
    if not drag or screen.node != nodes.MENU:
        return None
    cfg = spec(screen)
    value = _value_at(screen, drag["key"], x)
    point = (native_x_for(value, cfg),
             cfg[BARS[drag["key"]][3]] + cfg["height"] // 2)
    if getattr(screen.app, "connected", False):
        screen.app.client.inject_click(*point)
    sent = getattr(screen, "slider_sent", None) or {}
    sent[drag["key"]] = {"value": value, "state": screen.state, "seen": 0,
                         "level": value_to_level(value, cfg)}
    screen.slider_sent = sent
    return point


def advance(screen, state):
    """Drop a held preview once the snapshot carries it, or after the
    floor of snapshots that would have shown it."""
    sent = getattr(screen, "slider_sent", None)
    if not sent:
        return
    for key in list(sent):
        held = sent[key]
        if state is held["state"]:
            continue
        held["state"], held["seen"] = state, held["seen"] + 1
        raw = getattr(state, "settings_raw", b"") or b""
        got = (getattr(settings_spec.parse(raw), BARS[key][2])
               if len(raw) >= settings_spec.SIZE else None)
        if got == held["level"] or held["seen"] > EFFECT_PAIRS:
            del sent[key]
