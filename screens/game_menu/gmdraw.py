"""Drawing for the GAME menu overlay — one function per dialog.

Every panel and button is a `thin_border` box (decision 34) except
the popup body, which wears one fixed frame image (decision 69,
`gmframe`); a panel with `backdrop` in its style is first filled from
the shared cockpit texture, the same fill the help popup uses, so the
popup is opaque without a dimmed backdrop a palette-indexed engine
could not draw. The NEW/QUIT confirmation and the slot warning are not
drawn here: they are the game's generic boxes, `core/msgbox.py`'s
(TRANSCRIPTION `one_confirmation_box`, work order 316).
Rows are computed from one box and a count (decision 51) and plated
with `draw_plate`. Every string goes through `Style.render_text`
(decision 30); the words come from layout.json (decision 15) and the
game's own strings from HESTRNGS.
"""
import pygame

from core import fontscale, lang, mouse as mouse_input
from core.hud import blocks as hud
from core.hud import glyphs

from core import palette
from core.structs import settings as settings_spec
from screens.game_menu import gmframe, nodes

COL_BUTTON = palette.require("game_menu", "button_text")
COL_TITLE = palette.require("game_menu", "title")
COL_ROW = palette.require("game_menu", "row_text")
COL_ACTIVE = palette.require("game_menu", "row_active")
COL_DETAIL = palette.require("game_menu", "row_detail")
COL_OPTION = palette.require("game_menu", "option_text")

#: Which HESTRNGS id is the Load/Save status a slot message names.
SCREEN_DATA = {nodes.LOAD: 2, nodes.SAVE: 3}


def box(screen, name):
    return next((b for b in screen.boxes if b.name == name), None)


def rect(screen, name):
    b = box(screen, name)
    return b.screen_rect if b is not None else None


def hit(screen, name, x, y):
    r = rect(screen, name)
    return bool(r and r.collidepoint(x, y))


def bands(area, count):
    """`count` rows tiling `area` exactly: edges from one division."""
    edges = [area.y + (area.h * i) // count for i in range(count + 1)]
    return [pygame.Rect(area.x, edges[i], area.w, edges[i + 1] - edges[i])
            for i in range(count)]


def row_at(screen, name, count, x, y):
    area = rect(screen, name)
    if not area or not area.collidepoint(x, y):
        return None
    for i, band in enumerate(bands(area, count)):
        if band.collidepoint(x, y):
            return i
    return None


def _size(screen, b, key="font_size", default=24):
    # The seated menu's ONE factor applies to type as to rects (gmframe.seat).
    return screen.layout.font_size(b.style.get(key, default)
                                   * getattr(screen, "content_scale", 1.0))


def _blit(screen, surface, text, size, color, x, y, center_w=None):
    img = screen.style.render_text(text, size, tuple(color[:3]))
    if center_w is not None:
        x += (center_w - img.get_width()) // 2
    surface.blit(img, (x, y))
    return img


def _blit_fit(screen, surface, text, size, color, x, y, width):
    """Shrink one line until it fits `width`, never cut it — the
    original squeezes rather than truncates (fundament, "When the
    original states a PROPORTION")."""
    img = screen.style.render_text(text, size, tuple(color[:3]))
    while img.get_width() > width and size > 8:
        size -= 1
        img = screen.style.render_text(text, size, tuple(color[:3]))
    surface.blit(img, (x, y))


def panel(screen, surface, name):
    b = box(screen, name)
    if b is None or b.screen_rect is None:
        return None
    # The body wears the HUD popup block (decision 71; it wore Data's frame
    # image under decision 69, `gmframe`); nothing else is drawn for it.
    if b.style.get("frame") and gmframe.draw(screen, surface, b.screen_rect):
        return b
    # A panel with a `backdrop` is a DIALOG: the popup block too, opaque,
    # as every dialog is since 71.
    if b.style.get("backdrop"):
        hud.popup(surface, b.screen_rect, screen.layout.scale)
        return b
    b.render(surface, screen.layout, screen.style)
    return b


def fit_size(screen, b, word):
    """The font size `word` is drawn at in button box `b`: the box's own,
    and outside English the largest one that keeps the word inside 90 % of
    the button (the text-fit rule, work order 200 C: ÜBERNEHMEN was wider
    than its button); English is drawn exactly as before."""
    size = _size(screen, b, default=30)
    scaled = fontscale.factor() != 1.0
    if lang.current() == lang.DEFAULT and not scaled:
        return size
    r = b.screen_rect
    room = r.w * 0.9
    if scaled:
        # HD EXTENSION `font_scale` (work order 356): the text-size factor
        # grows the word, not the button, so English is fitted too, and
        # the word leaves room for the button's glyph (RETURN lost its
        # arrow at 1.20). At 1.0 nothing changes.
        room = r.w - 2 * int(r.h * 0.2) - int(r.h * 0.6) - int(r.h * 0.12) \
            if glyphs.for_button("game_menu", b.name) else room
    while size > 8 and screen.style.render_text(
            word, size, (255, 255, 255)).get_width() > room:
        size -= 1
    return size


def group_size(screen, items):
    """HD EXTENSION `button_group_size` (Data, 26 October 2026: in German
    SPIEL SPEICHERN and EINSTELLUNGEN stood smaller than SPIEL LADEN beside
    them): outside English the buttons of one dialog share ONE font size,
    the smallest `fit_size` any of them needs, so no word is drawn past its
    button and none looks larger than its neighbours. `items` is
    [(box name, word)]; None in English, where each button keeps its own
    size as before."""
    if lang.current() == lang.DEFAULT and fontscale.factor() == 1.0:
        return None
    sizes = []
    for name, text in items:
        b = box(screen, name)
        if b is not None and b.screen_rect is not None:
            sizes.append(fit_size(screen, b, text))
    return min(sizes) if sizes else None


def button(screen, surface, name, word, size=None):
    """A button of the menu: the HUD's small button (decision 71), lit
    while pressed and on hover; its word in code as before. `size` is the
    dialog's shared size (`group_size`), None for the button's own."""
    b = box(screen, name)
    if b is None or b.screen_rect is None:
        return
    if screen.pressed.is_down(name):
        state = "pressed"       # decision 92: the click, never the 'on' look
    elif b.screen_rect.collidepoint(mouse_input.pos()):
        state = "hover"
    else:
        state = "normal"
    hud.small_button(surface, b.screen_rect, screen.layout.scale, state)
    size = size or fit_size(screen, b, word)
    img = screen.style.render_text(
        word, size, tuple(screen.pressed.colour(name, COL_BUTTON)[:3]))
    r = b.screen_rect
    # The button's glyph beside the word when both fit (work order 179).
    cx = hud.icon_beside(surface, r, glyphs.for_button("game_menu", name),
                         img.get_width())
    surface.blit(img, (cx - img.get_width() // 2,
                       r.y + (r.h - img.get_height()) // 2))


def word(screen, group, key):
    return screen.words.get("words", {}).get(group, {}).get(key, key)


def game_string(screen, hid):
    text = screen.hstrings.message(hid) if screen.hstrings else None
    if text is None:
        text = screen.words.get("words", {}).get(
            "string_missing", "String {id}").replace("{id}", str(hid))
    return text


def slots_for(screen, node):
    """MSG_SAVE_SLOTS for THIS dialog, or None — open fix 14 is required
    (tools/version_check.py); None is only the tick between the field list
    and the slot message that follows it."""
    slots = getattr(screen.state, "save_slots", None)
    if slots and slots.get("screen_data") == SCREEN_DATA.get(node) and \
            len(slots["slots"]) >= nodes.SLOTS:
        # all ten or none: the dialog indexes `slots[i]` for each of its
        # ten rows, so a short message (the count byte is the wire's) is
        # the same tick-between-messages case as no message — drawn as
        # such — and not an IndexError in every frame after it
        return slots["slots"]
    return None


def active_slot(screen):
    raw = getattr(screen.state, "settings_raw", b"") or b""
    if len(raw) < settings_spec.SIZE:
        return None
    return settings_spec.parse(raw).active_save_slot


def render(screen, surface):
    node = screen.node
    if node is None:
        return
    # The NEW/QUIT confirmation and the slot warning are NOT drawn here:
    # they are `GENDRAW::Confirmation_Box_` and `Message_Box_Exploding_`
    # (gendraw.cpp:160-231, :93-112), the generic boxes every screen opens,
    # and `core/msgbox.py` draws them from open fix 29's MSGB with the
    # engine's own text (TRANSCRIPTION `one_confirmation_box`, work order
    # 316: until then this module drew a second copy). Under one, the
    # popup draws the dialog the box covers, as the original keeps it.
    base = screen.under if node in (nodes.CONFIRM, nodes.WARNING) else node
    DIALOGS.get(base, lambda s, f: None)(screen, surface)


def _menu(screen, surface):
    """The menu, and the menu UNDER a confirmation: the original keeps the
    popup drawn behind `Confirmation_Box_` (it is drawn at 0xa1, 0x75 over
    the popup's own picture, gendraw.cpp:180), while the confirmation's
    field list carries only YES and NO — so which buttons stand is taken
    from the menu's own last list (multiplayer has no LOAD or NEW)."""
    panel(screen, surface, "body")
    under = screen.node != nodes.MENU
    shown = [(name, word(screen, "menu", name.split("_", 1)[1]))
             for name, key in screen.BUTTONS[nodes.MENU]
             if ((key in screen.menu_keys) if under else
                 screen.present(nodes.MENU, key))]
    size = group_size(screen, shown)
    for name, text in shown:
        button(screen, surface, name, text, size)
    from screens.game_menu import gmsliders
    gmsliders.render(screen, surface)


def _settings(screen, surface):
    panel(screen, surface, "body")
    title = box(screen, "settings_title")
    if title is not None:
        title.text = word(screen, "settings", "title")
        title.text_color = COL_TITLE
        title.render(surface, screen.layout, screen.style)
    rule = screen.words.get("settings_rows", {})
    area_box = box(screen, "settings_rows")
    if area_box is not None and area_box.screen_rect:
        size = _size(screen, area_box)
        ids, alts = rule.get("label_ids", []), rule.get("alt", [])
        for i, band in enumerate(bands(area_box.screen_rect, nodes.OPTIONS)):
            side = int(band.h * rule.get("checkbox", 0.7))
            square = pygame.Rect(band.x, band.y + (band.h - side) // 2,
                                 side, side)
            # The HUD checkbox (work order 172): one block for every
            # checkbox, the tick following the frame colour.
            hud.checkbox(surface, square, screen.layout.scale,
                         bool(screen.flags is not None and screen.flags[i]))
            ty = band.y + (band.h - size) // 2
            if i < len(ids):
                lx = band.x + int(band.w * rule.get("label_x", 0.11))
                limit = (int(band.w * rule.get("alt_x", 0.77))
                         if i < len(alts) and alts[i] else band.w)
                _blit_fit(screen, surface, game_string(screen, ids[i]),
                          size, COL_OPTION, lx, ty, band.x + limit - lx)
            if i < len(alts) and alts[i]:
                _blit(screen, surface, alts[i], size, COL_OPTION,
                      band.x + int(band.w * rule.get("alt_x", 0.77)), ty)
    _orionlayer_button(screen, surface)
    button(screen, surface, "settings_accept",
           word(screen, "settings", "accept"))


def _orionlayer_button(screen, surface):
    """ORIONLAYER SETTINGS … (HD EXTENSION `orionlayer_window`, work order
    251, `olwin`): below the engine rows, a line, then the button that
    opens OrionLayer's own window — the gear, the word, the arrow, as in
    Data's mockup. It has no field and sends nothing."""
    b = box(screen, "orionlayer_open")
    if b is None or b.screen_rect is None:
        return
    r = b.screen_rect
    rows = box(screen, "settings_rows")
    if rows is not None and rows.screen_rect is not None:
        y = (rows.screen_rect.bottom + r.y) // 2
        hud.separator(surface, r.x, r.right, y, screen.layout.scale)
    state = ("pressed" if screen.pressed.is_down("orionlayer_open") else
             "hover" if r.collidepoint(mouse_input.pos()) else "normal")
    hud.small_button(surface, r, screen.layout.scale, state)
    col = tuple(screen.pressed.colour("orionlayer_open", COL_BUTTON)[:3])
    from core.hud import art
    ic = art.mask("gameplay", int(r.h * 0.55), col)
    x = r.x + int(r.h * 0.4)
    if ic is not None:
        surface.blit(ic, (x, r.y + (r.h - ic.get_height()) // 2))
        x += ic.get_width() + int(r.h * 0.35)
    arrow = int(r.h * 0.6)
    _blit_fit(screen, surface, word(screen, "settings", "orionlayer"),
              _size(screen, b, default=30), col, x,
              r.y + (r.h - _size(screen, b, default=30)) // 2,
              r.right - arrow - x)
    s = max(3, r.h // 6)
    cx, cy = r.right - arrow // 2 - s // 2, r.centery
    # LOOK EXCEPTION marking: the button's arrow (Data's mockup), its word's colour
    pygame.draw.lines(surface, col, False, [(cx - s // 2, cy - s),
                                            (cx + s // 2, cy),
                                            (cx - s // 2, cy + s)],
                      max(2, r.h // 14))


def _slots(screen, surface, node):
    panel(screen, surface, "body")
    rule = screen.words.get("slot_rows", {})
    list_box = box(screen, "slot_list")
    if list_box is not None and list_box.screen_rect:
        size = _size(screen, list_box, default=28)
        small = _size(screen, list_box, "detail_font_size", 22)
        slots, active = slots_for(screen, node), active_slot(screen)
        empty = game_string(screen, rule.get("empty", 388))
        editor = screen.save
        for i, band in enumerate(bands(list_box.screen_rect, nodes.SLOTS)):
            row = pygame.Rect(band.x, band.y, band.w,
                              int(band.h * rule.get("row", 0.774)))
            screen.style.draw_plate(surface, row, screen.layout.scale)
            x = row.x + int(row.w * rule.get("name_x", 0.03))
            top = pygame.Rect(x, row.y, row.right - x, int(band.h * rule.get(
                "detail_y", 0.45)))
            if node == nodes.SAVE and editor.slot == i and editor.input:
                editor.input.render(surface, top, screen.style, screen.layout)
            elif slots:
                slot = slots[i]
                text = (rule.get("invalid", "* INVALID *")
                        if slot["status"] == 2 else slot["description"])
                color = screen.pressed.colour(
                    f"slot_{i}", COL_ACTIVE if i == active else COL_ROW)
                _blit_fit(screen, surface, text, size, color, x,
                          top.y + (top.h - size) // 2, top.w)
            # Without the slot message a row is its plate and nothing more:
            # no number stands in for a name the engine did not send.
            if slots:
                dy = band.y + int(band.h * rule.get("detail_y", 0.45))
                if slots[i]["description"] != empty:
                    _blit(screen, surface, slots[i]["stardate"], small,
                          COL_DETAIL, x, dy)
                _blit(screen, surface, slots[i]["date"], small, COL_DETAIL,
                      row.x + int(row.w * rule.get("date_x", 0.48)), dy)
    shown = [(name, word(screen, node, name.split("_", 1)[1]))
             for name, key in screen.BUTTONS[node]]
    size = group_size(screen, shown)
    for name, text in shown:
        button(screen, surface, name, text, size)


DIALOGS = {
    nodes.MENU: _menu,
    nodes.SETTINGS: _settings,
    nodes.LOAD: lambda s, f: _slots(s, f, nodes.LOAD),
    nodes.SAVE: lambda s, f: _slots(s, f, nodes.SAVE),
}


def help_rect(screen, spec):
    """The region kinds this overlay adds to help.json."""
    around = spec.get("around")
    if around:
        body = rect(screen, around)
        if body is None:
            return None
        w, h = screen.app.win_w, screen.app.win_h
        side = spec.get("side")
        if side == "top":
            return pygame.Rect(body.x, 0, w - body.x, body.y)
        if side == "left":
            return pygame.Rect(0, 0, body.x, h)
        if side == "bottom":
            return pygame.Rect(body.x, body.bottom, body.w, h - body.bottom)
        if side == "right":
            return pygame.Rect(body.right, body.y, w - body.right,
                               h - body.y)
        return None
    name = spec.get("rows_box")
    if name:
        area = rect(screen, name)
        if area is None:
            return None
        return bands(area, spec.get("rows", 1))[spec.get("row", 0)]
    if spec.get("livery_part"):
        # the livery window (work order 220): `gmlivery.geometry`, the one
        # geometry its drawing and its clicks use (decision 5)
        from . import gmlivery
        return gmlivery.help_rect(screen, spec)
    if spec.get("ol_part"):
        # the OrionLayer window's own parts (work order 251): `olwin.geometry`
        from . import olwin
        return olwin.help_rect(screen, spec)
    band = spec.get("orionlayer_band")
    if band:
        # an OrionLayer row (work order 212): `gmorion.bands`, the one
        # geometry its drawing and its clicks use (decision 5)
        from . import gmorion
        geo = gmorion.bands(screen)
        return geo.get(band) if geo else None
    return None
