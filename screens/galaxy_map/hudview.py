"""The galaxy map's HUD: Data's frame picture, its words and its buttons
(decision 104, work order 420; decision 71 for the pre-104 look).

**Since work order 420 the HUD is ONE PICTURE** — `core.hud.art.GALAXY_FRAME`,
a base-pack picture that follows the player's frame colour — with the
hamburger button (GAME), the info panel's compartments and the icon bar
with the play button in it. Everything the picture cannot say is drawn
here over it: the GAME word, the readouts and the HUD's own icons in the
panel, hover and pressed over a button, and the status block at the top
right (`OrionRE | v<engine version>   <time>`). The rectangles are the
picture's measured parts (`assets/shared/hud/galaxy_frame.json`).

HD EXTENSION `galaxy_frame` (work order 420, Data): the picture, the status
block and the colour that follows the player's frame colour are ours — MOO2
has one look and no such block; marked in the status document and held by
smoke checks 007, 011a and 006c.

The old text of this docstring, which still holds for the seam it names:
title plate, info panel and nav row (decision 71).

Split out of `screen.py` by work order 169 along the seam the screen
already had — `screen.py` keeps loading, geometry of the map and input
hooks; this draws the HUD over the map's floor and answers where its
buttons are. Every shape is a `core.hud` block; nothing here draws its
own panel or button.

**One function per place, for drawing AND hitting** (decision 5):
`title_rect` is the GAME button's click area, its help region and where
its word goes; `nav_rect` / `nav_hit` are where a nav button is drawn
and the shape it is hit as.
"""
import json
import time

import pygame

from core import lang
from core import resources
from core.config import ORION2RE_VERSION

from core import mouse as mouse_input
from core.config import REF_H, REF_W
from core.hud import art as hudart
from core.hud import blocks as hud
from core.hud import text as hudtext
from screens.galaxy_map import boxdraw
from screens.galaxy_map import sidebar as sb
from screens.galaxy_map import terrpanel


#: The picture's pixel to the layout's reference pixel (1920 / 2560).
PICTURE_REF = 0.75
_geo = {}


def geometry():
    """The picture's measured parts, in its own pixels
    (`assets/shared/hud/galaxy_frame.json`, measured by the store's
    galaxy-frame tool)."""
    if not _geo:
        with open(resources.res.shared("hud", "galaxy_frame.json"),
                  encoding="utf-8") as f:
            _geo.update(json.load(f))
    return _geo


def picture_rect(screen, rect):
    """A rectangle in the picture's pixels as a window rect: the picture
    is drawn over the layout's content area (16:9, centred), as the
    reference space is."""
    k = PICTURE_REF
    x, y, w, h = rect
    return pygame.Rect(*screen.layout.rect((x * k, y * k, w * k, h * k)))


def frame_rect(screen):
    """Where the frame picture is drawn: the whole content area."""
    return pygame.Rect(*screen.layout.rect((0, 0, REF_W, REF_H)))


def render_frame(screen, surface):
    """Data's frame picture over the map, in the player's frame colour.
    A pack without it draws nothing (absent is a state, decision 38)."""
    r = frame_rect(screen)
    img = hudart.frame(r.w, r.h)
    if img is not None:
        surface.blit(img, r.topleft)


def title_rect(screen):
    """The hamburger button in device px: the GAME button's click area,
    its help region and the frame the word sits in."""
    return picture_rect(screen, geometry()["hamburger"])


#: The time of day the status block shows (`time.localtime`), replaced by a
#: test or an evidence render that needs one frozen picture. It is the
#: wall clock, read once per frame — not decision 78's `planetspin.now()`,
#: a monotonic elapsed time that cannot say HH:MM.
_wall_clock = time.localtime


def set_wall_clock(fn):
    """Inject the clock (`fn()` -> a `time.struct_time`), or None."""
    global _wall_clock
    _wall_clock = fn or time.localtime


def status_words(now=None):
    """The status block's three words: ("OrionRE", "v2.0.2", "18:56") —
    the engine's version OrionLayer is built for
    (`core.config.ORION2RE_VERSION`) and the local time."""
    t = now or _wall_clock()
    return ("OrionRE", f"v{ORION2RE_VERSION}",
            time.strftime("%H:%M", t))


def _word(screen, text, role, cap_px, colour):
    """`text` in `role`'s face, its capital height `cap_px` PICTURE pixels
    tall at the picture's own size (the HUD's measured sizing: a word's
    size follows the box it stands in, decision 71)."""
    from core.hud import style as hudstyle
    k = PICTURE_REF * screen.layout.scale
    ratio = float(hudstyle.get().get(f"text.{role}.cap"))
    return hudtext.render(screen.style, text, role,
                          cap_px * 4 / 3 * k / ratio, colour)


def render_status(screen, surface):
    """`OrionRE | v<version>   <time>` at the top right, as in Data's
    mock-up ("Neon Galactic Strategy Command Map"): the name and the time
    in the value colour, the version dimmer, a thin bar between the name
    and the version. Right-aligned to the picture's `top_right.right`,
    centred on `top_right.cy`."""
    geo = geometry()["top_right"]
    draw_status(surface, screen.style, screen.layout.scale,
                picture_rect(screen, (geo["right"], geo["cy"], 0, 0)).x,
                picture_rect(screen, (0, geo["cy"], 0, 0)).y)


def draw_status(surface, style, scale, right_px, cy_px):
    """The status block right-aligned at `right_px`, centred on `cy_px`
    (device px): the galaxy map's own, and the colony summary's since 20
    Nov 2026 (Data's Futuristic mockup)."""
    from core.hud import style as hudstyle
    name, version, clock = status_words()
    k = PICTURE_REF * scale
    big = hudtext.colour("value")[:3]
    dim = hudtext.colour("label")[:3]
    # (text, role, capital height in picture px, colour, gap to the next)
    # Sized to stand RIGHT of the picture's top bar's step (its line falls
    # from y 45 to y 80 at picture x ~1990, `top_right.min_left`): the first
    # build (34 / 19 px caps) reached x 1960 and the name stood on the
    # step — Data saw it at once (18 November 2026). Clock 27 -> 19 and
    # GAME 22 -> 16 after his looks: "etwas zu groß", then "sieht immer noch
    # gleich groß aus" at 23 / 19 (19 November).
    parts = [(clock, "value", 19, big, 24), (version, "label", 15, dim, 11),
             (None, None, 0, None, 11), (name, "label", 15, big, 0)]
    x = right_px
    for text, role, cap, col, gap in parts:
        if text is None:
            # the bar between the name and the version: the HUD's own
            # separator block (screens draw no lines of their own)
            h = int(21 * k)
            hud.separator(surface, cy_px - h // 2, cy_px + h // 2,
                          x - int(2 * k), scale, vertical=True)
            x -= int(4 * k) + int(gap * k)
            continue
        ratio = float(hudstyle.get().get(f"text.{role}.cap"))
        img = hudtext.render(style, text, role, cap * 4 / 3 * k / ratio, col)
        ink = img.get_bounding_rect()
        surface.blit(img, (x - ink.right, cy_px - ink.y - ink.h // 2))
        x -= ink.w + int(gap * k)


def render_title(screen, surface):
    """The word GAME on the hamburger button (layout.json `frame.title`)
    and the status block. The pressed GAME word is orange, as BUFFER0.LBX
    1's frame 1 is. The word is centred BY INK (`core.hud.text.blit`)."""
    cfg = screen._data.get("frame", {})
    title = cfg.get("title", screen.FRAME_TITLE)
    box = picture_rect(screen, geometry()["game_word"])
    col = screen.pressed.colour("title", hudtext.colour("title"))[:3]
    word = _word(screen, title.upper(), "title", 16, col)
    hudtext.blit(surface, word, box, align="left")
    render_status(screen, surface)


def render_sidebar(screen, surface):
    """The info panel's CONTENT: the HUD's own icons and the readouts in
    code, over the frame picture's compartments (the panel and its
    separators are the picture's since work order 420)."""
    box = screen.box_rect("sidebar")
    if not box:
        return
    L = screen.layout
    state = screen._state
    stardate = (str(getattr(state, "stardate_str", "--"))
                if state is not None else "--")
    rows = screen._data.get("sidebar_rows") or sb.DEFAULT_ROWS
    geometry = screen._sidebar_geometry(rows, set(hudart.ICONS))
    for key, (_text, icon) in geometry.items():
        if icon is not None and key in hudart.ICONS:
            _blit_icon(surface, key, pygame.Rect(*L.rect(icon)))
    sb.render(surface, L, screen.style, geometry,
              screen._local, screen._data.get("labels", {}), rows,
              font_scales=screen._sidebar_font_scales(rows),
              aligns=screen._sidebar_aligns(rows),
              # the unit in the session's words (work order 208 B7, Data's
              # decision 6): "MC" in German, as the game's own texts and
              # the info screen print it — the whole readout "132 BC" is
              # no key of the table, so the unit is translated by itself
              monetary=lang.tr(screen._data.get("monetary_unit", "BC")),
              extras={"stardate": (stardate, "")},
              icons={}, cache=screen._cache,
              fonts=screen._data.get("sidebar_fonts", sb.DEFAULT_FONTS),
              panel_box=box, dividers=False,
              hstrings=boxdraw._texts(screen))


def _blit_icon(surface, key, r):
    """The HUD's icon for `key`, fitted into `r`, aspect kept."""
    img = hudart.icon(key, r.h)
    if img is None:
        return
    if img.get_width() > r.w:
        img = hudart.fit("icon_" + key,
                         max(1, int(r.h * r.w / img.get_width())), r.w)
    surface.blit(img, (r.x + (r.w - img.get_width()) // 2,
                       r.y + (r.h - img.get_height()) // 2))


def render_nav(screen, surface):
    """The six nav buttons and TURN are in the picture (the icons and the
    play triangle); hover lights a button and the pressed one is drawn
    pressed, an overlay in its rectangle (`hud.picture_button`)."""
    # Window coordinates, not desktop coordinates: in fullscreen the
    # content sits inside black bars and a raw get_pos() puts the
    # highlight one bar-width off the pointer.
    mouse = mouse_input.pos()
    for spec in screen._data.get("buttons", []):
        key = spec["key"]
        rect = nav_rect(screen, key)
        if rect is None:
            continue
        if screen.pressed.is_down(key):
            state = "pressed"   # decision 92: the click, never the 'on' look
        elif nav_hit(screen, key, *mouse):
            state = "hover"
        else:
            state = "normal"
        hud.picture_button(surface, rect, screen.layout.scale, state)
        _nav_word(screen, surface, spec, rect, state)


def _nav_word(screen, surface, spec, rect, state):
    """The button's word, right of the icon the picture holds (the picture
    carries no text): the word's room is measured in `galaxy_frame.json`."""
    geo = geometry()
    key = spec["key"]
    if key == "turn":
        x0, x1 = geo["turn_label"]
        room = picture_rect(screen, (x0, geo["turn"][1], x1 - x0,
                                     geo["turn"][3]))
        role = "action"
    else:
        x0 = geo["nav_icon_right"][key] + geo["label_gap"]
        x1 = geo["nav_x"][key][1] - geo["label_pad_right"]
        room = picture_rect(screen, (x0, geo["nav_y"][0], x1 - x0,
                                     geo["nav_y"][1]))
        role = "button"
    hud.picture_label(surface, screen.style, room, spec["label"], role, state)


def nav_rect(screen, key):
    """The button's window rect, from its box (the picture's measured
    segment of the icon bar, or the play button)."""
    return screen.box_screen_rect(f"nav_{key}")


def nav_hit(screen, key, x, y):
    """A nav button is hit as the rectangle it lights as (decision 5)."""
    rect = nav_rect(screen, key)
    return rect is not None and rect.collidepoint(x, y)


def render_backdrop(screen, surface):
    """The map behind a box or a turn-time popup (work order 196 A).

    While the engine processes a turn it reports ids no HD screen claims,
    the dispatcher EXITS the map, and `ScreenBase.exit` drops its boxes.
    Rendered then, the map had no map area, sidebar or nav and drew only
    its floor and the title: the black screen Data saw behind the Turn
    Summary, the landing and every box after them. So an exited map loads
    its boxes for the window as it is and draws the map as it last saw it
    (no `update`: that would park the game and read the engine's modals).
    Its own modal (`_modal`) and help are left out — the App's box is the
    dialog, and two would stack."""
    size = (screen.app.win_w, screen.app.win_h)
    if not screen.active and (not screen.boxes
                              or screen._backdrop_size != size):
        screen._reload_boxes()
        screen._update_box_layout()
        screen._backdrop_size = size
    screen._render_map(surface)
    render_frame(screen, surface)
    render_sidebar(screen, surface)
    terrpanel.render(screen, surface)
    render_nav(screen, surface)
    render_title(screen, surface)
