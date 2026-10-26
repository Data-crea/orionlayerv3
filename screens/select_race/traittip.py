"""Select Race: the full text of a trait or a government, on hover.

HD EXTENSION `race_panel_pictures` (Data's mockup of 25 Oct 2026). The
texts are the game's own, the ones Custom Race shows for the same pick
(`screens/custom_race/traits.json`): the bonus traits (RACESTUF.LBX index
1..9) carry their category's text, the flags (10..30) their own, a
government the category text of the governments — the data has no text of
a single government. Nothing here is invented.

The box is the HUD's popup block (`hud.popup`, decision 71), the wrap the
race description's (`info_panel.markup_lines`); there was no hover
tooltip before, so this is the one.
"""
import json
import os

import pygame

from core import lang
from core.config import SCREENS_DIR
from core.hud import blocks as hud
from screens.select_race import info_panel
from screens.select_race import renderer as rnd

TIP_W = 500               # reference px
TIP_FONT = 19
TIP_HEAD = 18
PAD = 16
GAP = 8                   # between the card and the box

_texts = {}


def _load():
    """(bonus categories by id, flags by id and by name, governments text),
    read once."""
    if not _texts:
        path = os.path.join(SCREENS_DIR, "custom_race", "traits.json")
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            data = {}
        cats = {c["trait_id"]: c for c in data.get("categories", [])
                if c.get("trait_id")}
        flags, by_name = {}, {}
        for s in data.get("specials", []):
            flags.setdefault(s["trait_id"], s)
            by_name[s["name"]] = s
        gov = next((c for c in data.get("categories", [])
                    if c.get("trait_id") == 0), {})
        _texts.update(cats=cats, flags=flags, names=by_name, gov=gov)
    return _texts


def describe(row):
    """(title, text) of a trait row from `RaceTraits.traits`, or
    (title, None) when the data has no text for it."""
    t = _load()
    if row.get("government"):
        return row.get("value") or row["name"], t["gov"].get("description")
    title = row["name"].rstrip(":").strip()
    tid = row.get("trait")
    if tid in t["cats"]:
        return title, t["cats"][tid].get("description")
    if tid == 31:                       # Poor Home World has no id of its own
        return title, t["names"].get("Poor Home World", {}).get(
            "description")
    return title, t["flags"].get(tid, {}).get("description")


def draw(surface, L, style, hit):
    """The box for `hit` = (card rect, row), below the card — above it
    where the window's edge is in the way."""
    rect, row = hit
    title, text = describe(row)
    if not text:
        return
    fs = L.font_size(TIP_FONT)
    font = style.get_prop_font(fs)
    pad = int(PAD * L.scale)
    width = int(TIP_W * L.scale)
    lines = info_panel.markup_lines(font, lang.tr(text), width - 2 * pad,
                                    info_panel._desc_colour)
    head = style.get_font(L.font_size(TIP_HEAD)).render(
        title.upper(), True, rnd.COL_HEADING)
    line_h = int(fs * info_panel.DESC_LINE)
    gap = int(GAP * L.scale)
    height = 2 * pad + head.get_height() + gap + len(lines) * line_h
    sw, sh = surface.get_size()
    x = max(gap, min(rect.x, sw - width - gap))
    y = rect.bottom + gap
    if y + height > sh - gap:
        y = max(gap, rect.top - gap - height)
    box = pygame.Rect(x, y, width, height)
    hud.popup(surface, box, L.scale)
    surface.blit(head, (x + pad, y + pad))
    ty = y + pad + head.get_height() + gap
    for line in lines:
        info_panel.draw_line(surface, font, line, x + pad, ty)
        ty += line_h
