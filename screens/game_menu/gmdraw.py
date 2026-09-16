"""Drawing for the GAME menu overlay — one function per dialog.

Every panel and button is a `thin_border` box (decision 34) except
the popup body, which wears one fixed frame image (decision 69,
`gmframe`); a panel with `backdrop` in its style is first filled from
the shared cockpit texture, the same fill the help popup uses, so the
popup is opaque without a dimmed backdrop a palette-indexed engine
could not draw. HD DEVIATION: the confirmation and the slot warning are
drawn at the original's layout scaled to the popup's width, inside the
frame's opening, where the original lets them overhang the popup (work
order 123; `gmframe`'s docstring has the sizes and the reason).
Rows are computed from one box and a count (decision 51) and plated
with `draw_plate`. Every string goes through `Style.render_text`
(decision 30); the words come from layout.json (decision 15) and the
game's own strings from HESTRNGS.
"""
import pygame

from core import palette
from core.hestrings import printf
from core.structs import settings as settings_spec
from core.textfit import wrap_text
from screens.game_menu import gmframe, gmorion, nodes

COL_BUTTON = palette.require("game_menu", "button_text")
COL_TITLE = palette.require("game_menu", "title")
COL_ROW = palette.require("game_menu", "row_text")
COL_ACTIVE = palette.require("game_menu", "row_active")
COL_DETAIL = palette.require("game_menu", "row_detail")
COL_OPTION = palette.require("game_menu", "option_text")
COL_CHECK = palette.require("game_menu", "checkbox_on")
COL_MESSAGE = palette.require("game_menu", "message")
COL_STATE = palette.require("game_menu", "hd_state")

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
    return screen.layout.font_size(b.style.get(key, default))


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
    # The body wears Data's frame image instead of an outline (decision
    # 69, `gmframe`); it fills its own opening, so nothing else is drawn.
    if b.style.get("frame") and gmframe.draw(screen, surface, b.screen_rect):
        return b
    if b.style.get("backdrop"):
        surface.blit(screen.help_backdrop(), b.screen_rect, b.screen_rect)
    b.render(surface, screen.layout, screen.style)
    return b


def button(screen, surface, name, word):
    b = panel(screen, surface, name)
    if b is None:
        return
    size = _size(screen, b, default=30)
    img = screen.style.render_text(
        word, size, tuple(screen.pressed.colour(name, COL_BUTTON)[:3]))
    r = b.screen_rect
    surface.blit(img, (r.x + (r.w - img.get_width()) // 2,
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
    """MSG_SAVE_SLOTS for THIS dialog, or None (the HD STATE)."""
    slots = getattr(screen.state, "save_slots", None)
    if slots and slots.get("screen_data") == SCREEN_DATA.get(node):
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
    base = screen.under if node in (nodes.CONFIRM, nodes.WARNING) else node
    DIALOGS.get(base, lambda s, f: None)(screen, surface)
    if node == nodes.CONFIRM:
        _message(screen, surface, "confirm", screen.confirm_text())
        button(screen, surface, "confirm_yes", word(screen, "confirm", "yes"))
        button(screen, surface, "confirm_no", word(screen, "confirm", "no"))
    elif node == nodes.WARNING:
        _message(screen, surface, "warning", screen.warning_text())


def _menu(screen, surface):
    """The menu, and the menu UNDER a confirmation: the original keeps the
    popup drawn behind `Confirmation_Box_` (it is drawn at 0xa1, 0x75 over
    the popup's own picture, gendraw.cpp:180), while the confirmation's
    field list carries only YES and NO — so which buttons stand is taken
    from the menu's own last list (multiplayer has no LOAD or NEW)."""
    panel(screen, surface, "body")
    under = screen.node != nodes.MENU
    for name, key in screen.BUTTONS[nodes.MENU]:
        if (key in screen.menu_keys) if under else screen.present(nodes.MENU,
                                                                   key):
            button(screen, surface, name,
                   word(screen, "menu", name.split("_", 1)[1]))
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
            screen.style.draw_plate(surface, square, screen.layout.scale)
            if screen.flags is not None and screen.flags[i]:
                surface.fill(tuple(COL_CHECK[:3]), square.inflate(
                    -max(4, side // 4), -max(4, side // 4)))
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
    gmorion.render(screen, surface)
    button(screen, surface, "settings_accept",
           word(screen, "settings", "accept"))


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
            else:
                label = screen.words.get("words", {}).get(
                    "slot", "Slot {n}").replace("{n}", str(i + 1))
                _blit(screen, surface, label, size,
                      screen.pressed.colour(
                          f"slot_{i}", COL_ACTIVE if i == active
                          else COL_STATE), x,
                      top.y + (top.h - size) // 2)
            if slots:
                dy = band.y + int(band.h * rule.get("detail_y", 0.45))
                if slots[i]["description"] != empty:
                    _blit(screen, surface, slots[i]["stardate"], small,
                          COL_DETAIL, x, dy)
                _blit(screen, surface, slots[i]["date"], small, COL_DETAIL,
                      row.x + int(row.w * rule.get("date_x", 0.48)), dy)
    for name, key in screen.BUTTONS[node]:
        button(screen, surface, name, word(screen, node, name.split("_", 1)[1]))


def _message(screen, surface, prefix, text):
    panel(screen, surface, f"{prefix}_panel")
    area_box = box(screen, f"{prefix}_text")
    if area_box is None or area_box.screen_rect is None or not text:
        return
    size = _size(screen, area_box, default=34)
    area = area_box.screen_rect
    lines = wrap_text(screen.style, text, size, area.w)
    imgs = [screen.style.render_text(line, size, tuple(COL_MESSAGE[:3]))
            for line in lines]
    y = area.y + (area.h - sum(i.get_height() for i in imgs)) // 2
    for img in imgs:
        surface.blit(img, (area.x + (area.w - img.get_width()) // 2, y))
        y += img.get_height()


DIALOGS = {
    nodes.MENU: _menu,
    nodes.SETTINGS: _settings,
    nodes.LOAD: lambda s, f: _slots(s, f, nodes.LOAD),
    nodes.SAVE: lambda s, f: _slots(s, f, nodes.SAVE),
}


def help_rect(screen, spec):
    """The two region kinds this overlay adds to help.json."""
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
    return None
