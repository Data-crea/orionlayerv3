"""Select Race, right panel: the race's picture, and its traits with icons.

HD EXTENSION `race_panel_pictures` (Data's mockup of 25 Oct 2026): the
original prints plain words. Here the panel opens with a wide picture of
the race under its name, and every trait and the government stand beside
an icon.

THE PICTURE is the race's own portrait, cover-cropped wide
(`imagebox.cover`, never stretched); `banner_crop_y` in `races.json`
says where the strip is cut, because the heads sit at different heights.
THE ICONS are one file per trait or government,
`assets/icons/traits/<key>.png` / `assets/icons/govs/<key>.png` in the
screen's folder (a mod replaces one by name). A missing icon is a state,
not an error (decision 38): the HUD's own icon stands in where one fits
(`HUD_FALLBACK`), else a faint ring keeps the row's place. The keys are
the trait's index in RACESTUF.LBX (`racestuf.RaceTraits.names`), so a
translated name finds its icon too.

THE ROOM. The texts differ in length (3 to 8 lines of description), so the
boxes are fixed for the longest; the traits are cards, two to a row, the
government a card at the box's foot (`render_traits`), and the full texts
are the tooltip's (`traittip`), never on the card.
"""
import math

import pygame

from core import fontscale, imagebox
from core.hud import art as hud_art
from core.hud import blocks as hud
from screens.select_race import renderer as rnd

#: Trait index (RACESTUF.LBX names, 1..31) -> the icon's file key.
TRAIT_KEYS = {
    1: "population_growth", 2: "food_production",
    3: "industrial_production", 4: "scientific_research", 5: "tax",
    6: "ship_defense", 7: "ship_offense", 8: "ground_combat",
    9: "espionage", 10: "low_gravity", 11: "high_gravity", 12: "aquatic",
    13: "subterranean", 14: "large_home_world", 15: "rich_home_world",
    16: "artifacts_home_world", 17: "cybernetic", 18: "lithovore",
    19: "repulsive", 20: "charismatic", 21: "uncreative", 22: "creative",
    23: "tolerant", 24: "expert_traders", 25: "telepathic", 26: "lucky",
    27: "omniscient", 28: "stealth_ships", 29: "trans_dimensional",
    30: "warlord", 31: "poor_home_world",
}
#: Government index (the record's byte 0) -> the icon's file key.
GOV_KEYS = {
    0: "feudal", 1: "confederation", 2: "dictatorship", 3: "imperium",
    4: "democracy", 5: "federation", 6: "unification",
    7: "galactic_unification",
}
#: A HUD icon that stands in for a trait icon not drawn yet.
HUD_FALLBACK = {
    "population_growth": "person", "food_production": "food",
    "industrial_production": "industry", "scientific_research": "science",
    "tax": "coin", "ship_defense": "shield", "ship_offense": "swords",
    "low_gravity": "gravity", "high_gravity": "gravity",
    "large_home_world": "planets", "rich_home_world": "crystal",
}
ICON_H = 44               # reference px
CARD_H = 60               # a card: the icon and 8 px above and below
CARD_PAD = 8
COL_GAP = 12
BANNER_ART_Y = 0.35       # where a city view is cut: 0 top .. 1 bottom
BANNER_FADE = 0.75        # the title strip's dark ramp, of the width
BANNER_DARK = 200


def trait_icon_keys():
    """Every icon file this panel can ask for, as (folder, key)."""
    return ([("traits", k) for k in sorted(TRAIT_KEYS.values())]
            + [("govs", k) for k in sorted(GOV_KEYS.values())])


def _icon(find, cache, folder, key, px):
    """The icon at `px` high, or None. `find` is the screen's
    `asset_path`; the result, absent too, is kept per size."""
    ck = (folder, key, px)
    if ck in cache:
        return cache[ck]
    img = None
    path = find("assets", "icons", folder, key + ".png") if find else None
    if path:
        try:
            raw = pygame.image.load(path).convert_alpha()
            w = max(1, round(raw.get_width() * px / raw.get_height()))
            img = pygame.transform.smoothscale(raw, (w, px))
        except pygame.error:
            img = None
    if img is None and folder == "traits" and key in HUD_FALLBACK:
        img = hud_art.icon(HUD_FALLBACK[key], px)
    cache[ck] = img
    return img


def _draw_icon(surface, find, cache, folder, key, x, y, px):
    img = _icon(find, cache, folder, key, px)
    if img is None:                       # keeps the row's place
        pygame.draw.circle(surface, rnd.COL_SEPARATOR,
                           (x + px // 2, y + px // 2), px // 2 - 2, 2)
        return
    surface.blit(img, (x + (px - img.get_width()) // 2, y))


def render_banner(surface, L, race, img, rect, cache, banner_y=None,
                  own=False):
    """The race's picture in `rect` (reference px), with the dark ramp
    under the name on its left."""
    x, y = L.pos(rect[0], rect[1])
    w, h = L.size(rect[2], rect[3])
    if img is None or w < 2 or h < 2:
        return
    # a city view is cut round its middle; a portrait from its top, where
    # the head is
    cy = (race.get("banner_art_y", BANNER_ART_Y) if own
          else race.get("banner_crop_y", 0.08)) if banner_y is None \
        else banner_y
    key = (race.get("id"), w, h, cy, own)
    pic = cache.get(key)
    if pic is None:
        pic = imagebox.cover(img, w, h, [0.5, cy], 1.0)
        # darkest top left, fading both right and down, so the ramp has no
        # edge of its own
        ramp = pygame.Surface((w, h), pygame.SRCALPHA)
        top = int(h * 0.55)
        for cx in range(int(w * BANNER_FADE)):
            a = (1 - cx / (w * BANNER_FADE)) ** 1.5
            for cy2 in range(top):
                v = int(BANNER_DARK * a * (1 - cy2 / top) ** 1.2)
                if v:
                    ramp.set_at((cx, cy2), (6, 8, 14, v))
        pic.blit(ramp, (0, 0))
        cache[key] = pic
    surface.blit(pic, (x, y))


def _card(surface, L, style, find, cache, trait, rect, fs_scale, hover):
    """One trait or the government as a card: the HUD's field block
    (lit while the mouse is over it), the icon, the name, the value."""
    hud.field(surface, rect, L.scale, on=hover)
    px = max(8, int(ICON_H * L.scale))
    pad = max(4, int(CARD_PAD * L.scale))
    folder, key = ("govs", GOV_KEYS.get(trait.get("gov_id"), "")) \
        if trait.get("government") else \
        ("traits", TRAIT_KEYS.get(trait.get("trait"), ""))
    _draw_icon(surface, find, cache, folder, key, rect.x + pad,
               rect.y + (rect.h - px) // 2, px)
    size = L.font_size(int(rnd.TRAIT_FONT * fs_scale))
    # the government card's own words are the form of government
    label = trait["value"] if trait.get("government") else trait["name"]
    value = trait.get("value", "")
    tx = rect.x + 2 * pad + px
    room = rect.right - pad - tx
    if fontscale.factor() > 1.0:
        # HD EXTENSION `font_scale` (WO 356): the card is a fixed width, so
        # above 1.0 name and value are fitted TOGETHER (a '+2' was cut
        # off); at 1.0 and below the size is the card's own, as before.
        gap = int(8 * L.scale)
        floor = max(8, math.ceil(size / fontscale.factor() - 1e-6))  # the 1.0 size
        while size > floor and style.get_font(size).size(label)[0] + (
                gap + style.get_prop_font(size).size(value)[0]
                if value and not trait.get("government") else 0) > room:
            size -= 1
    font = style.get_font(size)
    name = font.render(label, True, rnd.COL_NEUTRAL
                       if trait.get("government") else rnd.COL_VALUE)
    ty = rect.y + (rect.h - name.get_height()) // 2
    surface.blit(name, (tx, ty), area=(0, 0, min(name.get_width(), room),
                                       name.get_height()))
    if value and not trait.get("government"):
        good = trait.get("good")
        col = (rnd.COL_GOOD if good is True else rnd.COL_BAD
               if good is False else rnd.COL_NEUTRAL)
        vs = style.get_prop_font(size).render(value, True, col)
        vx = tx + name.get_width() + int(8 * L.scale)
        if vx + vs.get_width() <= rect.right - pad:
            surface.blit(vs, (vx, rect.y + (rect.h - vs.get_height()) // 2))


def block_height(cards):
    """The height of RACE TRAITS + GOVERNMENT for `cards` trait cards, in
    reference px: the heading, the rows of cards (two to a row), a gap,
    the government's heading and card. The screen puts this block right
    under the description, whose height is the rest."""
    rows = max(1, (cards + 1) // 2)
    return 26 + rows * (CARD_H + 6) - 6 + 12 + 24 + CARD_H


def render_traits(surface, L, style, race, rect, cache, find=None,
                  fs_scale=1.0, mouse=None):
    """RACE TRAITS as cards in two columns, GOVERNMENT as a card of its
    own beneath. Returns (card rect, row) of the card under `mouse`, or
    None — the screen draws the tooltip for it last, over everything.

    THE GOVERNMENT SITS AT THE BOX'S FOOT; the box is `block_height`
    high, so it follows the cards, and the whole block follows the
    description (the screen sets both)."""
    rx, ry, rw, rh = rect
    if not race.get("traits"):            # the Custom Race has none
        return None
    hfont = style.get_font(L.font_size(int(rnd.HEADING_FONT * fs_scale)))
    hx, hy = L.pos(rx, ry)
    surface.blit(hfont.render("RACE TRAITS", True, rnd.COL_LABEL), (hx, hy))
    rows = [t for t in race.get("traits", []) if not t.get("government")]
    gov = next((t for t in race.get("traits", [])
                if t.get("government")), None)
    gap = 6
    col_w = (rw - COL_GAP) / 2
    gov_y = ry + rh - CARD_H - 24
    top = ry + 26
    per = max(1, (gov_y - 10 - top + gap) // (CARD_H + gap))
    over = None
    for i, t in enumerate(rows[:2 * per]):
        c, r = i % 2, i // 2
        x, y = L.pos(rx + c * (col_w + COL_GAP), top + r * (CARD_H + gap))
        card = pygame.Rect(x, y, int(col_w * L.scale),
                           int(CARD_H * L.scale))
        hov = bool(mouse) and card.collidepoint(mouse)
        _card(surface, L, style, find, cache, t, card, fs_scale, hov)
        if hov:
            over = (card, t)
    gx, gy = L.pos(rx, gov_y - 2)
    surface.blit(hfont.render("GOVERNMENT", True, rnd.COL_LABEL), (gx, gy))
    if gov:
        x, y = L.pos(rx, gov_y + 22)
        card = pygame.Rect(x, y, int(rw * L.scale), int(CARD_H * L.scale))
        hov = bool(mouse) and card.collidepoint(mouse)
        _card(surface, L, style, find, cache, gov, card, fs_scale, hov)
        if hov:
            over = (card, gov)
    return over


#: The Custom Race's panel: the slogan, then the picture, in place of the
#: traits (it has none). Reference px.
TAG_H = 44
TAG_FONT = 24
CUSTOM_FOOT_MIN = TAG_H + 150


def _picture(find, cache, key, *parts):
    """A picture of the screen's own folder, loaded once (absent too, a
    state and no error, decision 38); a mod replaces it by name."""
    if key not in cache:
        img = None
        path = find("assets", *parts) if find else None
        if path:
            try:
                img = pygame.image.load(path).convert()
            except pygame.error:
                img = None
        cache[key] = img
    return cache[key]


def custom_picture(find, cache):
    """The picture under the Custom Race's text, or None."""
    return _picture(find, cache, "custom_panel", "custom_panel.png")


def banner_picture(find, cache, race, portrait):
    """The wide picture over a race's text: its own
    `assets/banners/<name>.png` (a city view, 16 : 9), else the portrait
    the grid shows. Returns (image, True when it is the banner's own)."""
    key = race.get("key") or race["name"].lower()
    img = _picture(find, cache, ("banner", key), "banners", key + ".png")
    return (img, True) if img is not None else (portrait, False)


def render_custom_footer(surface, L, style, tagline, img, rect, cache):
    """The slogan in gold, and the picture below it cover-cropped to what
    is left of `rect` (reference px)."""
    rx, ry, rw, rh = rect
    if tagline:
        font = style.get_font(L.font_size(TAG_FONT))
        tx, ty = L.pos(rx + 12, ry)
        surf = font.render(tagline, True, rnd.COL_GOLD)
        surface.blit(surf, (tx, ty + (int(TAG_H * L.scale)
                                      - surf.get_height()) // 2))
    if img is None:
        return
    px, py = L.pos(rx, ry + TAG_H)
    pw, ph = L.size(rw, rh - TAG_H)
    if pw < 2 or ph < 2:
        return
    key = ("custom_footer", pw, ph)
    pic = cache.get(key)
    if pic is None:
        pic = imagebox.cover(img, pw, ph, [0.5, 0.5], 1.0)
        cache[key] = pic
    surface.blit(pic, (px, py))
