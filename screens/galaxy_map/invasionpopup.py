"""The colony combat popup — the invasion choice and the bombing — work order
232 C, on open fix 91's TPOP kind 10 (id 68).

After a won battle at an enemy colony the original asks the attacker what to
do: `MAINPUPS::Colony_Selection_Popup_` -> `Colony_Combat_Popup_` mode 0
(mainpups.cpp:1211-1415); after BOMBARD the same box in mode 1, the bombing
(`Colony_Bombing_Popup_`, :1462-1486). Read in
`dev:doc/briefs/232-invasion-reading.md` §2-3. The App draws it over the held
map (`core.turnpopup.View`, `core.handover.overlay_for`), as the combat
target window.

TRANSCRIPTION — what it shows (`Draw_Colony_Combat_Popup_`, :2682-2811),
each at its native place in the box (MAINPUPS.LBX 0x4E, 337 x 266, centred,
`Get_Picture_Draw_XY_` :110-113), the box carried to the window at the native
picture's scale, centred as the original centres it:
  the title     the title line as the engine last printed it (E 458 "Select
                Combat at %s" with the planet's name), centred at (+168, +20)
  the planet    CMBTPLNT.LBX `size + climate * 6` in its own palette over
                palette 0, centred in the box (:2696-2700; :2431-2448)
  left          from (+20, +50), 30 apart, icon then text at +55: the
                buildings (COLONY2 0x2F, E 19), the best shield building
                (0x30, E 70 with its name), the colonists (the first pop's
                figure, E 20), the defender's infantry then tanks (their
                figure, E 14 "%d %s" with the troop's name)
  right         right-aligned at +w-45, icon at +w-40: the attacker's
                infantry (E 14), the bombardment (0x2E, E 21 "%d est. bomb
                hits" in the choice, E 18 "%d bomb strikes" while bombing)
  the bombing   each strike's explosion where the engine queued it (MAINPUPS
                0x3D, a biological one 0x49), frame by frame (`FLCQUEUE`)
  the buttons   each field the engine added, at its place in the live list:
                CANCEL [6] (ESC), INVADE [12] (I), BOMBARD [13] (B), DESTROY
                [14] (D), MIND CONTROL [15] (M; grey when it cannot work,
                MAINPUPS 0x51), and while bombing BOMBARD [18], HALT [17]
                (H), DROP ALL [16] (A)

TRANSCRIPTION — what a click does: the field is activated, and every answer
is the engine's (`Evaluate_Colony_Combat_Input_`, :2450-2510); a right click
on a button is a right click on its field — the game's own help box
(`TEXTBOX::Text_Box_`, MSGB); a key is the field whose hotkey it is
(`core.turnpopup.key_action`).

DEVIATION `hud_turn_popup` (core/turnpopup.py's): the HUD panel and small
buttons with their words in code instead of MAINPUPS.LBX's box and button
art (decision 71).
"""
import logging

import pygame

from core.hestrings import printf
from core.hud import blocks as hud
from core.hud import text as hudtext
from core import nativedraw as nd

log = logging.getLogger("galaxy_map.invasion_popup")

BOX_W, BOX_H = 337, 266
TITLE_AT = (168, 20)
LEFT_ICON_X, LEFT_TEXT_X, LIST_Y, LIST_PITCH = 20, 55, 50, 30
RIGHT_ICON_DX, RIGHT_TEXT_DX = 40, 45
#: The fields in the tail's order and their words (`DEFAULT_WORDS`).
WORDS = {k: f"inv_{k}" for k in ("close", "invade", "bomb", "destroy",
                                 "mind_control", "drop_all", "cease_fire",
                                 "bomb_hits")}
MIND_CANNOT = 2


class Drawn:
    """What the popup drew this frame, in the turn popup view's shape."""

    def __init__(self):
        self.rects, self.right, self.buttons = [], [], []
        self.right_help = None


class BoxMap:
    """The box's native pixels -> window pixels: the native picture's scale
    at this window, the box centred in the window as the original centres
    it on its screen."""

    def __init__(self, layout, size, corner):
        self.k = nd.native_scale(layout)
        self.step = max(1, int(self.k))
        self.x0, self.y0 = corner
        w, h = int(round(BOX_W * self.k)), int(round(BOX_H * self.k))
        self.rect = pygame.Rect(0, 0, w, h)
        self.rect.center = (size[0] // 2, size[1] // 2)

    def point(self, nx, ny):
        """A native SCREEN point (as the engine draws) in the window."""
        return (int(round(self.rect.x + (nx - self.x0) * self.k)),
                int(round(self.rect.y + (ny - self.y0) * self.k)))

    def native_rect(self, x1, y1, x2, y2):
        ax, ay = self.point(x1, y1)
        bx, by = self.point(x2 + 1, y2 + 1)
        return pygame.Rect(ax, ay, bx - ax, by - ay)


def _field(state, index):
    return next((f for f in (getattr(state, "fields", None) or [])
                 if getattr(f, "index", None) == index and index > 0), None)


def buttons(state, popup):
    """[(key, field)] of the buttons the engine added this pass and the live
    list holds — two sources (P602): the tail's index and the list."""
    fields = (popup.get("invasion") or {}).get("fields") or {}
    out = []
    for key in WORDS:
        f = _field(state, fields.get(key, -1000))
        if f is not None:
            out.append((key, f))
    return out


def _player(state, idx):
    from core.structs import player as player_struct
    raws = getattr(state, "player_raw", None) or []
    return player_struct.parse(raws[idx]) if 0 <= idx < len(raws) else None


def render(screen, surface, popup, state, app=None, words=None):
    """Draw the popup over what `surface` holds; return `Drawn`."""
    from core.estrings import EStrings
    from screens.ground_combat import gcart, gcdraw
    out = Drawn()
    a = popup["args"]
    inv = popup.get("invasion") or {}
    lay = screen.app.layout
    bm = BoxMap(lay, surface.get_size(), (a[9], a[10]))
    lang = (getattr(app, "settings", None) or {}).get("language", "en") \
        if app is not None else "en"
    if getattr(screen, "_invasion_words", None) is None or \
            screen._invasion_words[0] != lang:
        screen._invasion_words = (lang, EStrings(lang))
    e = screen._invasion_words[1]
    hud.panel(surface, bm.rect, lay.scale)
    style = screen.style
    size = max(nd.MIN_FONT, int(round(9 * bm.k)))
    colour = hudtext.colour("value")
    tx, ty = bm.point(bm.x0 + TITLE_AT[0], bm.y0 + TITLE_AT[1])
    nd.blit_text(surface, style, popup.get("title") or "", tx, ty - size // 2,
                 bm.rect.w - 2 * size, int(size * 1.25),
                 hudtext.colour("title"), align="center")
    colony = a[0]
    climate, bg = gcdraw.colony_world(state, colony)
    art = gcart.load()
    s = bm.step
    if art.available:
        pal = art.popup_palette(climate)
        from core.structs import colony as colony_struct
        from core.structs import planet as planet_struct
        cols = getattr(state, "colonies_raw", None) or []
        planets = getattr(state, "planets_raw", None) or []
        size_ = 2
        if 0 <= colony < len(cols):
            pl = colony_struct.parse(cols[colony]).planet
            if 0 <= pl < len(planets):
                size_ = int(planet_struct.parse(planets[pl]).size)
        pic = art.surface(f"planet_{climate}_{size_}", 0, pal,
                          key=("popup", climate))
        if pic is not None:
            big = pygame.transform.scale(pic, (pic.get_width() * s,
                                               pic.get_height() * s))
            # Data's painted battle planet, the same picture as in battle,
            # at the drawing's size (DEVIATION `painted_planets`).
            from screens.colony_summary import colonyplanets
            from core import resources
            big = colonyplanets.painted(resources.res, climate, size_,
                                        max(big.get_size())) or big
            cx, cy = bm.point(bm.x0 + BOX_W // 2, bm.y0 + BOX_H // 2)
            surface.blit(big, big.get_rect(center=(cx, cy)))
    defender, attacker = _player(state, a[8]), _player(state, a[7])

    def icon(pic, nx, ny):
        if pic is not None:
            big = pygame.transform.scale(pic, (pic.get_width() * s,
                                               pic.get_height() * s))
            surface.blit(big, bm.point(nx, ny))

    def line(words_, nx, ny, align="left"):
        x, y = bm.point(nx, ny)
        nd.blit_text(surface, style, words_, x, y, bm.rect.w // 2, size,
                     colour, align=align)

    # the icons, colonists and troops through `Remap_Draw_`: COLONY2.LBX
    # 0x32's palette (`gcart.remap_palette`, mainpups.cpp:2702-2703)
    remap = art.remap_palette() if art.available else {}

    def military(p, kind):
        if p is None or not art.available:
            return None
        without, with_ = gcdraw.TROOP_FIGURES[kind]
        app_ = gcdraw.TROOP_NAMES[kind][2]
        v = with_ if gcdraw.researched(p, app_) else without
        return art.surface(f"military_{int(p.race)}_{v}", 0, remap,
                           key=("remap",))

    # left: the defender (mainpups.cpp:2714-2766)
    x0, y0 = bm.x0, bm.y0
    row = 0
    if art.available:
        pal0 = remap
        if a[5] > 0:
            icon(art.surface("icon_buildings", 0, pal0, key=("remap",)),
                 x0 + LEFT_ICON_X, y0 + LIST_Y)
            line(printf(e.string(19) or "%d", a[5]), x0 + LEFT_TEXT_X,
                 y0 + LIST_Y)
            row = 1
        if a[6] != -1:
            from core.buildnames import BuildingNames
            icon(art.surface("icon_shield", 0, pal0, key=("remap",)),
                 x0 + LEFT_ICON_X, y0 + LIST_Y + row * LIST_PITCH)
            line(printf(e.string(70) or "%s", BuildingNames(lang).building(
                a[6]) or ""), x0 + LEFT_TEXT_X, y0 + LIST_Y + row * LIST_PITCH)
            row += 1
        if a[4] > 0:
            race = int(defender.race) if defender is not None else 0
            icon(art.surface(f"people_{race}_{max(0, min(2, a[13]))}", 0,
                             pal0, key=("remap",)),
                 x0 + LEFT_ICON_X, y0 + LIST_Y + row * LIST_PITCH)
            line(printf(e.string(20) or "%d", a[4]), x0 + LEFT_TEXT_X,
                 y0 + LIST_Y + row * LIST_PITCH)
            row += 1
    counts = inv.get("defender_counts") or [0] * 4
    for kind in (1, 0):
        if counts[kind] > 0:
            ny = y0 + LIST_Y + row * LIST_PITCH
            icon(military(defender, kind), x0 + LEFT_ICON_X, ny)
            line(printf(e.string(14) or "%d %s", counts[kind],
                        gcdraw.troop_name(e, defender, kind)),
                 x0 + LEFT_TEXT_X, ny)
            row += 1
    # right: the attacker (:2768-2808)
    right = 0
    acounts = inv.get("attacker_counts") or [0] * 4
    if acounts[1] > 0:
        icon(military(attacker, 1), x0 + BOX_W - RIGHT_ICON_DX, y0 + LIST_Y)
        line(printf(e.string(14) or "%d %s", acounts[1],
                    gcdraw.troop_name(e, attacker, 1)),
             x0 + BOX_W - RIGHT_TEXT_DX, y0 + LIST_Y, "right")
        right = 1
    if a[2] >= 0:
        ny = y0 + LIST_Y + right * LIST_PITCH
        if art.available:
            icon(art.surface("icon_bombard", 0, remap, key=("remap",)),
                 x0 + BOX_W - RIGHT_ICON_DX, ny)
        line(printf(e.string(21 if a[1] == 0 else 18) or "%d", a[2]),
             x0 + BOX_W - RIGHT_TEXT_DX, ny, "right")
    # the bombing's explosions (:1509-1590, FLCQUEUE)
    if art.available:
        pal0 = art.popup_palette(climate)
        for fl in inv.get("flics") or []:
            stem = gcdraw.FLIC_STEMS.get(fl["picture"])
            if stem in ("bomb", "bio"):
                icon(art.surface(stem, fl["frame"], pal0,
                                 key=("popup", climate)), fl["x"], fl["y"])
    # the buttons, each where the live list puts its field
    words = words or {}
    for key, f in buttons(state, popup):
        r = bm.native_rect(f.x, f.y, f.x_end, f.y_end)
        grey = key == "mind_control" and a[11] == MIND_CANNOT
        hud.small_button(surface, r, lay.scale,
                         "disabled" if grey else "normal",
                         words.get(WORDS[key], WORDS[key]),
                         style_renderer=style)
        out.rects.append((r, ("activate", f)))
        out.right.append((r, ("field", f)))
        out.buttons.append(("activate", f))
    # ESC is CANCEL's own hotkey: the last button a key answers
    close = [b for k, b in ((k, ("activate", f)) for k, f in
                            buttons(state, popup)) if k == "close"]
    if close:
        out.buttons = [b for b in out.buttons if b != close[0]] + close
    return out
