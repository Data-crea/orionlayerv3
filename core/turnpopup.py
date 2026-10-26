"""The turn-time popups in HD — work order 188 Part 4, on open fix 49.

**WHAT THE ORIGINAL SHOWS AT TURN CHANGE** is inventoried in
`dev:doc/brief_turn_messages.md`. The generic boxes among it (the strategic
combat result, the bombing report, spy reports, "really trash", the treaty
confirmation …) are `core/msgbox.py`'s, on open fix 29. The popups that are
their own dialogs are here, on open fix 49's "TPOP" block
(`doc/ext_turn_popups.patch`): each reports its own id (59-64; 40 kept for
the whole Turn Summary; 52 and 33 keep theirs) and sends what it shows.

ONE PANEL, PER-KIND CONTENT (the order: "one shared HD message box and
per-type content, rather than one screen per message"): `content(popup,
state)` turns a popup into a title, lines, options and buttons, each button
bound to the popup's OWN field — activated, or, where the original acts on
the pointer rather than on the field (the Turn Summary's rows,
turnsum.cpp:176-179, open fix 49's finding 1), an injected click at the
field's own centre (open fix 3 keeps the pointer there). The App draws it
over the held last HD frame (`core.handover.overlay_for`), as the message
box.

WHAT IS TRANSCRIPTION: every text is the game's own — the formatted strings
TPOP carries (the science footer, the GNN news, the planet choice's and the
discovery's titles, the Turn Summary's lines), names off the wire's records
(stars, planets as `HACCESS::Do_Get_Planet_Name_` numbers them, leaders),
technology names from the player's extracted TECHNAME (`core.technames`),
button words from ESTRINGS where the original has a string (hire 0x13C,
reject 0x1B4). The rest of the button words are artwork in the original and
typed in `assets/shared/turnpopup/labels.json` (decision 15).

**DEVIATION `hud_turn_popup`**: the HUD panel instead of each popup's own
artwork (SCIENCE.LBX and the technology animations, TURNSUM.LBX, the
BUFFER0.LBX popup frames with the system display, EVENTS.LBX's GNN picture
and animation, COLONY's landing art); the planet choice's and the
discovery's system display is a list of the star's planets (named) instead
of the planets' pictures; the troop popup (open fix 98, work order 274) is a
table of its lines under the planet's name, without the troops' figures; the science room
lists every discovery at once where the original shows one per click (each
click is still sent, as the original counts them); the GNN picture is not
drawn. (A popup's right click is the original's since work order 200 —
TRANSCRIPTION `popup_right`, `turnpopupcontent.RIGHT_HELP`.)

**THE COMBAT TARGET IS THE ORIGINAL'S WINDOW** (work order 228 B): the star
system window with the star, the orbits, the planets and the fleets, drawn
by the galaxy map's own system window code
(`screens/galaxy_map/combattarget.py`) over the map — not this panel. The
view below hands it the popup and keeps what it drew, in the same shape.
"""
import pygame

from core import helpformat, lang
from core.msgbox import dimmed_base
from core.hud import blocks as hud
from core.hud import text as hudtext
from core.turnpopupwire import (  # noqa: F401 — the names callers use
    KINDS, IDS, SLOTS, SHIP_SLOTS, parse, build)
from core.turnpopupcontent import (  # noqa: F401
    DEFAULT_WORDS, content, leader_card)

REF_W, REF_PAD, REF_FONT, REF_TITLE_FONT = 1000, 30, 28, 38
REF_BUTTON = (220, 58)
REF_OPTION_H = 46
#: The most height a popup's HD picture takes (`c["art"]`), in reference
#: px of 1080 — HD's choice: about half the screen, so the message and the
#: buttons stand under it at every window (work order 326 F).
REF_ART_H = 560
_art_cache = {}


# ── drawing and input ─────────────────────────────────────────────────

class View:
    """The popup over the held frame, for one App: drawing and input."""

    def __init__(self):
        self._base = None
        self.rects = []            # [(rect, action)] of what can be clicked
        self.buttons = []          # the bottom row's actions, in order
        self.sent = None
        #: `point(x, y)` -> an action for a click outside every rect, or
        #: None: the Space Dragon's star choice on the map (work order 319)
        self.point = None
        self._choosing = False     # the last frame drew that star choice

    def reset(self):
        self._base = None
        self.rects = []
        self.buttons = []
        self.point = None
        self._choosing = False

    def render(self, surface, style, labels, popup, state, backdrop=None,
               app=None):
        """`backdrop(surface)`, when given, draws the screen that stands
        behind the popup — the galaxy map for the report phase's popups
        (mainscr2.cpp: Reports_Screen_ runs over the map) — and returns
        True; without one, or when it has nothing to draw, the popup stands
        over the held frame (`msgbox.dimmed_base`, work order 196 A)."""
        # first: no popup but the dragon's star choice keeps its star click
        self.point = None
        choosing = self._choosing
        self._choosing = False
        if popup["kind"] == "combat_target":
            return self._render_window(surface, popup, state, backdrop, app)
        if popup["kind"] == "planet_choice" and not popup.get("text") and \
                app is not None and "galaxy_map" in app.dispatcher.screens:
            # TRANSCRIPTION `planet_choice_window` (Data, 26 October 2026):
            # the planet choice is the system window, as the original draws
            # it (`Draw_Selection_Popup`, mainpups.cpp:1863-1921 calls
            # `SYS::Draw_System_Display_Popup`); a system special's text
            # (the popup's `text`) keeps the panel
            return self._render_window(surface, popup, state, backdrop, app)
        if popup["kind"] == "colony_combat":
            return self._render_invasion(surface, popup, state, backdrop,
                                         app, labels)
        if popup["kind"] == "dragon_bribe":
            from core import dragonwire
            if dragonwire.mode(popup) == dragonwire.CHOOSE:
                if not choosing:
                    self._base = None     # the offer's dimmed copy
                self._choosing = True
                return self._render_dragon(surface, style, labels, popup,
                                           state, backdrop, app)
        self._base = dimmed_base(surface, self._base, 110, backdrop)
        surface.blit(self._base, (0, 0))
        words = dict(DEFAULT_WORDS, **{k: v for k, v in (labels or {}).items()
                                       if k in DEFAULT_WORDS and v})
        c = content(popup, state, words, app)
        self.rects, self.buttons = draw(surface, style, c)
        self.right = list(zip([r for r, _a in self.rects], c["right"])) + \
            [(r, ("field", f)) for r, f in zip(c.get("table_rects", []),
                                               c.get("line_right", []))]
        self.right_help = c["right_help"]
        return self.rects

    def _render_window(self, surface, popup, state, backdrop, app):
        """The combat target window (work order 228 B) over the map, not
        dimmed: the original draws it over the map as it stands
        (combfind.cpp:942-947). It is the galaxy map's window; without the
        map there is nothing to draw it with, and nothing is clickable."""
        self._base = dimmed_base(surface, self._base, 0, backdrop)
        surface.blit(self._base, (0, 0))
        host = app.dispatcher.screens.get("galaxy_map") \
            if app is not None else None
        self.rects, self.right, self.buttons = [], [], []
        self.right_help = None
        if host is None:
            return self.rects
        from screens.galaxy_map import combattarget
        drawn = combattarget.render(host, surface, popup, state, app)
        self.rects, self.right = drawn.rects, drawn.right
        self.buttons, self.right_help = drawn.buttons, drawn.right_help
        return self.rects

    def _render_invasion(self, surface, popup, state, backdrop, app,
                         labels):
        """The colony combat popup (open fix 91, work order 232 C) over the
        map, not dimmed — the original draws it over the main screen as it
        stands (`Do_Popup_Setup_`, mainpups.cpp:115-140)."""
        self._base = dimmed_base(surface, self._base, 0, backdrop)
        surface.blit(self._base, (0, 0))
        host = app.dispatcher.screens.get("galaxy_map") \
            if app is not None else None
        self.rects, self.right, self.buttons = [], [], []
        self.right_help = None
        if host is None:
            return self.rects
        from screens.galaxy_map import invasionpopup
        words = dict(DEFAULT_WORDS, **{k: v for k, v in (labels or {}).items()
                                       if k in DEFAULT_WORDS and v})
        drawn = invasionpopup.render(host, surface, popup, state, app, words)
        self.rects, self.right = drawn.rects, drawn.right
        self.buttons, self.right_help = drawn.buttons, drawn.right_help
        return self.rects

    def _render_dragon(self, surface, style, labels, popup, state, backdrop,
                       app):
        """The Space Dragon's star choice (open fix 108's mode 1, work
        order 319) over the map, not dimmed: the map is where the star is
        chosen (`screens/galaxy_map/dragonpopup.py`). A star can be clicked
        only where the backdrop drew THE galaxy map of this game this frame
        (`Overlays.backdrop_screen`); otherwise the panel alone."""
        self._base = dimmed_base(surface, self._base, 0, backdrop)
        surface.blit(self._base, (0, 0))
        words = dict(DEFAULT_WORDS, **{k: v for k, v in (labels or {}).items()
                                       if k in DEFAULT_WORDS and v})
        c = content(popup, state, words, app)
        host = app.dispatcher.screens.get("galaxy_map") \
            if app is not None else None
        drew = getattr(getattr(backdrop, "__self__", None),
                       "backdrop_screen", None)
        from core.overlays import same_game
        if host is None or drew is not host or not same_game(
                getattr(host, "_state", None), state):
            host = None
        from screens.galaxy_map import dragonpopup
        self.rects, self.buttons, self.point = dragonpopup.render(
            host, surface, style, c, popup, state)
        self.right = []
        self.right_help = c["right_help"]
        return self.rects

    def right_at(self, x, y):
        """A right click's answer: ("field", field), ("help", id) or None
        (`turnpopupcontent.RIGHT_HELP`, TRANSCRIPTION `popup_right`)."""
        for rect, action in getattr(self, "right", []):
            if action is not None and rect.collidepoint(x, y):
                return action
        hid = getattr(self, "right_help", None)
        return ("help", hid) if hid is not None else None

    def action_at(self, x, y):
        for rect, action in self.rects:
            if action is not None and rect.collidepoint(x, y):
                return action
        # a rect that takes no click still covers what lies under it
        if self.point is not None and not any(
                rect.collidepoint(x, y) for rect, _a in self.rects):
            return self.point(x, y)
        return None


def _wrap(style, text, size, width, colour):
    from core.textfit import wrap_rendered
    rows = []
    for ln in helpformat.parse(text or ""):
        plain = ln.plain()
        if not plain.strip():
            rows.append(None)
            continue
        rows.extend(wrap_rendered(style, plain, size, width, colour))
    return rows


def _hd_portrait(rec, k):
    """A leader offer's HD picture (work order 234, `core.leaderportraits`)
    fitted whole into the box the original's 73 x 88 drawing takes at
    `k` x, on a clear canvas of that box — so the text column stands where
    it stands beside the original's portrait — or None."""
    if rec is None:
        return None
    from core import leaderportraits
    box = (leaderportraits.NATIVE_SIZE[0] * k,
           leaderportraits.NATIVE_SIZE[1] * k)
    hd = leaderportraits.picture(rec, box)
    if hd is None:
        return None
    canvas = pygame.Surface(box, pygame.SRCALPHA)
    canvas.blit(hd, hd.get_rect(center=canvas.get_rect().center))
    return canvas


def _art(relpath, w, h):
    """A popup's HD picture (`turnpopupcontent.ART`) fitted whole into
    `w` x `h`, its proportion kept, or None — absent from the player's mod
    folder (the tree holds none) or unreadable, which costs one log line.

    HD EXTENSION `dragon_picture` (work order 326 F): the Space Dragon's
    bribe draws Data's dragon where the original's popup picture
    (MAINPUPS.LBX 0x48, `Load_Dragon_New_Star_Popup_`, mainpups.cpp:2151-
    2156) shows its dragon: at the top of the popup, the message under it
    (`animate::Draw_(0, 0, anims[37])`, :2617; the message box at (188,
    271), :2635). The original draws it in all three modes; HD's star choice
    (mode 1) is a strip over the map and draws none, so the map stays clear
    (OMISSION `dragon_picture_star_choice`, `screens/galaxy_map/
    dragonpopup.py`). Smoothly scaled: a painting, not the game's pixel art
    (decision 28 is about magnifying that)."""
    if not relpath or w <= 0 or h <= 0:
        return None
    import logging
    import os
    from core import resources
    path = resources.res.resolve(relpath)
    if not path:
        return None
    try:
        stamp = os.stat(path).st_mtime_ns
    except OSError:
        return None
    key = (path, stamp, w, h)
    if key in _art_cache:
        return _art_cache[key]
    try:
        src = pygame.image.load(path)
        k = min(w / src.get_width(), h / src.get_height())
        out = pygame.transform.smoothscale(
            # convert_alpha: a cut-out dragon keeps its transparency
            src.convert_alpha() if pygame.display.get_surface() else src,
            (max(1, round(src.get_width() * k)),
             max(1, round(src.get_height() * k))))
    except (pygame.error, OSError, ValueError, ZeroDivisionError) as err:
        logging.getLogger("turnpopup").warning(
            "popup picture %s will not load (%s) — drawn without", path, err)
        out = None
    if len(_art_cache) > 8:
        _art_cache.clear()
    _art_cache[key] = out
    return out


def draw(surface, style, c):
    """The panel. Returns `([(rect, action)] for options and buttons,
    [action] of the buttons)`."""
    win_w, win_h = surface.get_size()
    s = win_h / 1080
    pad = int(REF_PAD * s)
    w = min(int(REF_W * s), win_w - 2 * pad)
    inner = w - 2 * pad
    size = max(10, int(REF_FONT * s))
    colour = hudtext.colour("value")
    pic = c.get("picture")
    k = max(1, int(round(3 * s)))              # integer magnification (28)
    hd = _hd_portrait(c.get("leader"), k)
    if hd is not None:
        pic = hd
    elif pic is not None:
        pic = pygame.transform.scale(pic, (pic.get_width() * k,
                                           pic.get_height() * k))
    rows = []
    # the text column beside a portrait is narrower than the panel: wrap
    # to it (a leader offer's question ran past the panel's edge, seen in
    # work order 200 B's pictures)
    text_w = inner - (pic.get_width() + pad if pic is not None else 0)
    with lang.verbatim():          # the popup's lines are the game's (200 C)
        for text in c["lines"]:
            if isinstance(text, tuple):       # a table row: label, value
                rows.append((style.render_text(text[0], size, colour[:3]),
                             style.render_text(text[1], size, colour[:3])))
                continue
            rows.extend(_wrap(style, text, size, text_w, colour) or [None])
    step = int(size * 1.3)
    title = (style.render_text(c["title"], max(12, int(REF_TITLE_FONT * s)),
                               tuple(hudtext.colour("title")[:3]))
             if c.get("title") else None)
    opt_h = int(REF_OPTION_H * s)
    opts = []
    for label, action in c["options"]:
        rendered = _wrap(style, label, size, inner - 2 * pad, colour) or []
        opts.append((rendered, action))
    opts_h = sum(max(opt_h, len(r) * step + pad // 2) for r, _a in opts)
    bw, bh = int(REF_BUTTON[0] * s), int(REF_BUTTON[1] * s)
    text_h = sum(step if r is not None else step // 2 for r in rows)
    if pic is not None:
        text_h = max(text_h, pic.get_height())
    art = _art(c.get("art"), inner, int(REF_ART_H * s))
    h = pad + (title.get_height() + pad // 2 if title else 0) + text_h + \
        (pad // 2 + opts_h if opts else 0) + pad + bh + pad + \
        (art.get_height() + pad // 2 if art is not None else 0)
    h = min(h, win_h - 2 * pad)
    panel = pygame.Rect((win_w - w) // 2, (win_h - h) // 2, w, h)
    hud.popup(surface, panel, s)
    bottom = panel.bottom - pad - bh - pad
    y = panel.y + pad
    if title:
        surface.blit(title, title.get_rect(midtop=(panel.centerx, y)))
        y += title.get_height() + pad // 2
    if art is not None:              # above the message, as the original
        surface.blit(art, art.get_rect(midtop=(panel.centerx, y)))
        y += art.get_height() + pad // 2
    left = panel.x + pad
    if pic is not None:
        surface.blit(pic, (left, y))
        left += pic.get_width() + pad
    col = pygame.Rect(left, 0, panel.right - pad - left, 1)
    top = y
    for r in rows:
        if y + step > bottom:
            break
        if isinstance(r, tuple):
            surface.blit(r[0], (col.x, y))
            surface.blit(r[1], r[1].get_rect(topright=(col.right, y)))
            c.setdefault("table_rects", []).append(
                pygame.Rect(col.x, y, col.w, step))
        elif r is not None:
            surface.blit(r, r.get_rect(midtop=(col.centerx if pic is not None
                                              else panel.centerx, y)))
        y += step if r is not None else step // 2
    if pic is not None:
        y = max(y, top + pic.get_height())
    out = []
    if opts:
        y += pad // 2
    for rendered, action in opts:
        oh = max(opt_h, len(rendered) * step + pad // 2)
        if y + oh > bottom:
            break
        r = pygame.Rect(panel.x + pad, y, inner, oh - pad // 4)
        hud.panel(surface, r, s, lit=action is not None, dense=True)
        ty = r.y + (r.h - len(rendered) * step) // 2
        for line in rendered:
            surface.blit(line, (r.x + pad // 2, ty))
            ty += step
        out.append((r, action))
        y += oh
    total = len(c["buttons"]) * bw + (len(c["buttons"]) - 1) * pad
    x = panel.centerx - total // 2
    for label, action in c["buttons"]:
        r = pygame.Rect(x, panel.bottom - pad - bh, bw, bh)
        hud.action_button(surface, r, s,
                          "normal" if action is not None else "disabled",
                          label, style_renderer=style)
        out.append((r, action))
        x += bw + pad
    return out, [a for _l, a in c["buttons"]]


#: Snapshots after which an answer to an UNCHANGED popup may be sent again:
#: a click the game ignored (a planet it refuses silently) moves nothing,
#: and a guard that waited for a change would lock the popup for good (found
#: live, work order 188: the planet choice took no second planet).
RESEND_AFTER = 20


def state_key(popup):
    """What makes a popup's state a new one: an answer is sent once per
    state (a second click before the game has moved would land in what
    comes next) — the science room's count of entries shown, the Turn
    Summary's page, a leader offer's state all move it."""
    return (popup["kind"], tuple(popup["args"]), popup.get("title"),
            popup.get("text"), len(popup.get("messages") or ()))


#: The kinds whose last button a key answers: ESC is the original's own
#: hotkey on the Turn Summary's OK, the planet choice's and the combat
#: target's cancel and the science room; the full-screen field of the
#: others takes any input. A leader offer takes no key (its answers carry
#: ESTRINGS hotkeys HD does not type for the player).
KEY_KINDS = ("science", "turn_summary", "planet_choice", "discovery",
             "leader_level", "gnn", "combat_target", "landing", "troops",
             "antaran_room")


def key_action(view, popup, event):
    """The action a key answers: ESC / Enter / Space on the last button —
    or, on the colony combat popup (work order 232 C), the button whose
    field's hotkey the key is (I, B, D, M, H, A; ESC CANCEL's), read off the
    live list the popup's buttons stand in."""
    # the slider popup the same way: its CANCEL carries ESC
    # (`Add_Slider_Fields_`, mainpups.cpp:678-739; work order 316 E).
    # TRANSCRIPTION `slider_hotkeys`: a key is the field's own hotkey as the
    # engine carries it — the down arrow (mp_fields[10]) has E_Strings 137,
    # '+', the up arrow (mp_fields[9]) E_Strings 11, '-' (:696-711; seen
    # live, work order 316) — so a typed '+' LOWERS the value, as in the
    # original, although HD's buttons are worded by what they do
    # the Space Dragon's bribe too (work order 319): NO / CLOSE carries ESC
    # (E 135), YES E 561's "y" (`Update_Dragon_New_Star_Fields_`,
    # mainpups.cpp:2135-2151)
    if popup["kind"] in ("colony_combat", "slider", "dragon_bribe"):
        code = 27 if event.key == pygame.K_ESCAPE else \
            ord((event.unicode or " ")[0].upper())
        for action in view.buttons:
            f = action[1] if action is not None else None
            if f is not None and (f.hotkey or 0) in (code, ord(chr(
                    code).lower()) if code < 128 else -1):
                return action
        return None
    # The Antaran room ends on ANY key (`key::Keyboard_Status()`,
    # antaroom.cpp:69): HD answers every key with the room's one field,
    # the only answer the wire takes (TRANSCRIPTION `antaran_room`)
    if popup["kind"] == "antaran_room":
        buttons = [a for a in view.buttons if a is not None]
        return buttons[-1] if buttons else None
    if popup["kind"] not in KEY_KINDS or event.key not in (
            pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER,
            pygame.K_SPACE):
        return None
    buttons = [a for a in view.buttons if a is not None]
    return buttons[-1] if buttons else None
