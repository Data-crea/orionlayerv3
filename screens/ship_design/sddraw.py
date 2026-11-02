"""Drawing the Ship Designer's page in the HUD style (decision 71).

Every value sits at the HD image of the native anchor the original prints
it at (`sdgeom`, through `nativedraw` as the colony screen maps its own), in
the colony screen's text helper (`coldraw.text`: one line at a native
anchor, fitted to a native width). What is drawn and where it comes from:

  TRANSCRIPTION  every position; every label (HESTRNGS by the original's
                 own ids); every number off open fix 44's "DSGN" block as
                 the engine computed it; the damage and modification
                 strings as the engine formatted them; the per-weapon cost
                 and space divided as `Print_Current_Design_` divides them
                 (floor 1); the beam-defence sign as the original prints it
                 — a sign character before the signed number, so a negative
                 value reads "--n" there too; "(ammo)" after a rack weapon
                 (ammo > 0 exactly for those: `Update_Weapon_Replacement_`
                 writes 0 for every other weapon, desbox.cpp)
  DEVIATION      `hud_frameless` — HUD glass panels and buttons where the
                 original wears DESIGN.LBX's background and button art
  DEVIATION      `button_words` — the three bottom buttons', the icon
                 arrows' and the plus / minus words drawn in code; the
                 original paints them into DESIGN.LBX's button art
  HD EXTENSION   `title` — the title plate; no string table carries the
                 word the original paints into its background
  OMISSION       `hover_messages` — "Add New Weapon" / "NOT ENOUGH SPACE…"
                 over an empty row need `Space_For_Weapon_Replacement_`,
                 which is not on the wire; `flashing_hover` — the cycling
                 palette index of a hovered row
  HD EXTENSION   `hull_blue` — the hull column's box and the chosen hull's
                 band in the original's blue, and its words in the
                 original's grey and white, mixed case (Data, 2 November
                 2026)
"""

import pygame

from core.hestrings import printf
from core.hud import blocks as hud
from core.hud import hover as hud_hover
from core.hud import text as hudtext
from screens.colony import coldraw
from core import nativedraw as nd, textfit

from . import sdart, sdgeom as geom, sdwire

BULLET = "•"


def line(words):
    """HESTRNGS' `^` is the original font's bullet glyph."""
    return (words or "").replace("^", BULLET)


def draw(surface, screen, view, names):
    layout = screen.layout
    d = view.design
    # The title stands on the shell's plate (work order 225).
    for k, native in enumerate(geom.PANELS):
        r = nd.rect(layout, native)
        if k == geom.NAME_PANEL:
            hud.field(surface, r, layout.scale)
            continue
        nd.draw_box(surface, screen, native)
        if k == geom.HULL_PANEL:
            _hull_blue(surface, hud.panel_inner(r, layout.scale))
        if k in geom.FIELD_PANELS:
            hud.field(surface, hud.panel_inner(r, layout.scale),
                      layout.scale)
    hud.field(surface, nd.rect(layout, geom.PICTURE_BOX), layout.scale)
    _ship(surface, screen, view, names)
    _hulls(surface, screen, view, names)
    _systems(surface, screen, d, names)
    _weapons(surface, screen, view, names)
    _specials(surface, screen, view, names)
    _bottom(surface, screen, view, names)


#: share of a native row pitch a line of text may fill above factor 1.0,
#: so two rows keep a gap.
ROW_FILL = 0.75


def _t(surface, screen, words, x, y, w, key="value", role="value",
       align="left", pitch=None):
    """`pitch`: the native row pitch this line sits on. HD EXTENSION
    `font_scale` (WO 356): the rows do not move with the text size, so
    above 1.0 the size is fitted to `ROW_FILL` of the pitch
    (`core.textfit.fit_height_size`); at 1.0 and below it is the key's own
    size, as before."""
    size = None
    if pitch is not None:
        base = coldraw.font(screen.layout, key)
        size = textfit.fit_height_size(
            screen.style, base,
            int(pitch * nd.native_scale(screen.layout) * ROW_FILL))
    return coldraw.text(surface, screen, words, x, y, w, key, role,
                        align=align, size=size)


def _ship(surface, screen, view, names):
    d = view.design
    _t(surface, screen, d["name"], 0x14, 0x19, 0x84, "value", "title")
    art = sdart.load()
    pic = art.ship(d["picture"], view.colour) \
        if view.colour is not None else None
    box = nd.rect(screen.layout, geom.PICTURE_BOX)
    if pic is not None:
        big = nd.magnified(pic, screen.layout)
        at = (box.centerx - big.get_width() // 2,
              box.centery - big.get_height() // 2)
        # HD EXTENSION `painted_lists` (work order 239, `core/shippicture`):
        # the painted ship in the player's colour and livery where the mod
        # folder holds one, fitted into the sprite's own drawn pixels
        from core import shippicture
        hd = shippicture.fitted(
            screen.app, view.colour, d["picture"],
            shippicture.footprint(pic, at, big.get_width() // max(
                1, pic.get_width())),
            own=view.colour, size=d.get("size"))
        surface.blit(*(hd if hd is not None else (big, at)))
    for ident, word in ((geom.PICTURE_LEFT, "<"), (geom.PICTURE_RIGHT, ">")):
        f = sdwire.live_field(view.fields, ident)
        if f is not None:
            r = nd.rect(screen.layout, (f.x, f.y, f.x_end, f.y_end))
            hud.small_button(surface, r, screen.layout.scale,
                             hud_hover.pointer_state(r), word,
                             style_renderer=screen.style)
    _t(surface, screen, names.h(0x30), *geom.SPACE_LABEL, 0x40, "value",
       "label")
    _t(surface, screen, str(d["hull_space"]), geom.SPACE_RIGHT,
       geom.SPACE_LABEL[1], 0x40, align="right")


#: THE ORIGINAL'S BLUE, measured off Data's native screenshot of the hull
#: list (2 November 2026, a 347x319 crop): the box (4, 0, 56); the chosen
#: row's band (12, 4, 154) on its top and bottom rows and (16, 8, 200)
#: between — a band the width of the box.
HULL_BOX = (4, 0, 56)
HULL_BAND_EDGE, HULL_BAND = (12, 4, 154), (16, 8, 200)


def _hull_blue(surface, inner):
    """The hull column's box in the original's blue (HD EXTENSION
    `hull_blue`, Data, 2 November 2026)."""
    # LOOK EXCEPTION transcription: the hull list's box in the original's own blue, measured off Data's native screenshot
    surface.fill(HULL_BOX, inner)


def _hull_band(surface, rect, inner):
    """The chosen row's band across the box, edge rows lighter-dimmed as the
    original's three-step band."""
    band = pygame.Rect(inner.x, rect.y, inner.w, rect.h)
    edge = max(1, band.h // 8)
    # LOOK EXCEPTION transcription: the chosen hull's band in the original's blue, measured off Data's native screenshot
    surface.fill(HULL_BAND, band)
    # LOOK EXCEPTION transcription: the band's dimmer top and bottom rows, measured off Data's native screenshot
    surface.fill(HULL_BAND_EDGE, (band.x, band.y, band.w, edge))
    surface.fill(HULL_BAND_EDGE, (band.x, band.bottom - edge, band.w, edge))


#: The hull words as the original prints them, measured off the same
#: screenshot (the brightest pixels of the words): the unchosen grey, the
#: chosen one white. Mixed case ("Frigate"), one size for all six rows and
#: about three quarters of a row (the rows differ by a pixel or two
#: natively; the words do not).
HULL_WORD, HULL_WORD_ON = (126, 126, 134), (240, 240, 248)
HULL_WORD_FRAC, HULL_ROW_NATIVE = 0.78, 15


def _hull_word(surface, screen, rect, label, colour):
    if not label:
        return
    size = int(nd.rect(screen.layout, (0, 0, 0, HULL_ROW_NATIVE)).h
               * HULL_WORD_FRAC)
    hudtext.blit(surface, screen.style.render_text(label, size, colour),
                 rect)


def _hulls(surface, screen, view, names):
    d = view.design
    layout = screen.layout
    inner = hud.panel_inner(nd.rect(layout, geom.PANELS[geom.HULL_PANEL]),
                            layout.scale)
    for size, (y1, y2) in enumerate(geom.HULL_ROWS):
        r = nd.rect(layout, (geom.HULL_X[0], y1, geom.HULL_X[1], y2))
        label = names.part("hulls", size) or ""
        if size == d["size"]:
            # the chosen hull is the blue band with a white word, and
            # stays one under the pointer; the other rows show the HUD's
            # hover highlight under their grey word
            _hull_band(surface, r, inner)
            _hull_word(surface, screen, r, label, HULL_WORD_ON)
            continue
        state = (hud_hover.pointer_state(r) if view.hull_offered(size)
                 else "disabled")
        if state != "normal":
            hud.small_button(surface, r, layout.scale, state)
        _hull_word(surface, screen, r, label, HULL_WORD if state != "disabled"
                   else tuple(c // 2 for c in HULL_WORD))


def _systems(surface, screen, d, names):
    h = names.h
    _t(surface, screen, names.part("drives", d["ftl"]), *geom.DRIVE_NAME,
       0xB0, "value", "title")
    for (x, y), text in zip(geom.DRIVE_LINES,
                            (printf(h(0x17E) or "", d["warp_speed"]),
                             printf(h(0x54) or "", d["combat_speed"]))):
        _t(surface, screen, line(text), x, y, 0xA0, "line", "sub")
    _t(surface, screen, names.part("armor", d["armor"]), *geom.ARMOR_NAME,
       0xB0, "value", "title")
    for (x, y), text in zip(geom.ARMOR_LINES,
                            (printf(h(0x55) or "", d["structure"]),
                             printf(h(0x56) or "", d["armor_points"]))):
        _t(surface, screen, line(text), x, y, 0xA0, "line", "sub")
    if d["shield"] == 0:
        texts = (h(0x36), h(0x57), h(0x58))
    else:
        texts = (names.part("shields", d["shield"]),
                 printf(h(0x59) or "", d["shield_strength"]),
                 printf(h(0x5A) or "", d["shield_blocked"]))
    _t(surface, screen, texts[0], *geom.SHIELD_NAME, 0xB0, "value", "title")
    for (x, y), text in zip(geom.SHIELD_LINES, texts[1:]):
        _t(surface, screen, line(text), x, y, 0xA0, "line", "sub")
    _t(surface, screen, names.part("computers", d["computer"]),
       *geom.COMPUTER_NAME, 0xB0, "value", "title")
    _t(surface, screen, line(printf(h(0x5B) or "", d["beam_attack"])),
       *geom.COMPUTER_LINE, 0xA0, "line", "sub")
    sign = "+" if d["beam_defense"] >= 0 else "-"
    for (x, y), label, value in (
            (geom.BEAM_DEFENSE, h(0x5C), f"{sign}{d['beam_defense']}"),
            (geom.MISSILE_EVASION, h(0x5D), f"{d['missile_evasion']}%")):
        pitch = geom.MISSILE_EVASION[1] - geom.BEAM_DEFENSE[1]
        _t(surface, screen, label, x, y, 0x80, "value", "label",
           pitch=pitch)
        _t(surface, screen, value, geom.VALUE_RIGHT, y, 0x30, align="right",
           pitch=pitch)


def _weapons(surface, screen, view, names):
    h = names.h
    for sid, x in geom.WEAPON_HEADS:
        _t(surface, screen, h(sid), x, geom.WEAPON_HEAD_Y, 0x50, "value",
           "label")
    cols = geom.WEAPON_COLS
    for row, (slot, w) in enumerate(view.weapon_rows()):
        y = geom.WEAPON_TEXT_Y0 + row * geom.ROW_STEP
        name = names.part("weapons" if w["count"] < 2 else "weapon_plurals",
                          w["type"]) or ""
        if w["ammo"] > 0:
            name = f"{name} ({w['ammo']})"
        per = lambda v: str(max(1, v // w["count"] if w["count"] else 0))  # noqa: E731
        _t(surface, screen, str(w["count"]), cols["count"], y, 0x20,
           align="right", pitch=geom.ROW_STEP)
        _t(surface, screen, name, cols["name"], y, 0x90,
           pitch=geom.ROW_STEP)
        _t(surface, screen, w["damage"], cols["damage"], y, 0x40,
           align="center", pitch=geom.ROW_STEP)
        _t(surface, screen, names.arc(w["arc"]), cols["arc"], y, 0x2E,
           align="center", pitch=geom.ROW_STEP)
        _t(surface, screen, per(w["cost"]), cols["cost"], y, 0x28,
           align="center", pitch=geom.ROW_STEP)
        _t(surface, screen, per(w["space"]), cols["space"], y, 0x28,
           align="center", pitch=geom.ROW_STEP)
        _t(surface, screen, w["mods_text"], cols["mods"], y, 0x90,
           align="center", pitch=geom.ROW_STEP)
    # plus / minus: the live button where the list has one, and DULL where
    # a loaded row has none — `Draw_Down_Buttons_` draws the dull minus
    # and plus for every row that holds a weapon but has no active button.
    loaded = len(view.weapon_rows())
    for i in range(8):
        y = geom.WEAPON_ROW_Y0 + i * geom.ROW_STEP
        for x, word in ((geom.MINUS_X, "-"), (geom.PLUS_X, "+")):
            f = sdwire.at_origin(view.fields, x, y, (geom.TYPE_BUTTON,))
            if f is None and i >= loaded:
                continue
            native = (f.x, f.y, f.x_end, f.y_end) if f is not None else \
                (x, y, x + 10, y + 8)
            r = nd.rect(screen.layout, native)
            hud.small_button(surface, r, screen.layout.scale,
                             hud_hover.pointer_state(r)
                             if f is not None else "disabled", word,
                             style_renderer=screen.style)


def _specials(surface, screen, view, names):
    for sid, x in geom.SPECIAL_HEADS:
        _t(surface, screen, names.h(sid), x, geom.SPECIAL_HEAD_Y, 0x90,
           "value", "label")
    for row, (_slot, sp) in enumerate(view.specials()):
        y = geom.SPECIAL_TEXT_Y0 + row * geom.ROW_STEP
        _t(surface, screen, names.part("specials", sp),
           geom.SPECIAL_COLS["name"], y, 0xE0, pitch=geom.ROW_STEP)
        _t(surface, screen, names.description(sp),
           geom.SPECIAL_COLS["description"], y, 0x160, "line", "sub",
           pitch=geom.ROW_STEP)


def _bottom(surface, screen, view, names):
    d = view.design
    y = geom.BOTTOM_BAND[0] + 6
    for label_x, right, label, value in (
            (geom.COST_LABEL_X, geom.COST_RIGHT, names.h(0x185),
             d["printed_cost"]),
            (geom.AVAIL_LABEL_X, geom.AVAIL_RIGHT, names.h(0x63),
             d["printed_space_available"])):
        _t(surface, screen, label, label_x, y, 0x80, "value", "label")
        _t(surface, screen, str(value), right, y, 0x40, align="right")
    cancel = sdwire.live_field(view.fields, geom.CANCEL)
    size = (cancel.x_end - cancel.x, cancel.y_end - cancel.y) \
        if cancel is not None else (69, 22)
    for key, ident in (("clear", geom.CLEAR), ("cancel", geom.CANCEL),
                       ("build", geom.BUILD)):
        f = sdwire.live_field(view.fields, ident)
        native = (f.x, f.y, f.x_end, f.y_end) if f is not None else \
            (ident[1], ident[2], ident[1] + size[0], ident[2] + size[1])
        r = nd.rect(screen.layout, native)
        hud.slant_button(surface, r, screen.layout.scale,
                         "disabled" if f is None else
                         hud_hover.pointer_state(r),
                         screen.word(key), style_renderer=screen.style)
