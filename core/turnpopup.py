"""The turn-time popups in HD — work order 188 Part 4, on open fix 49.

**WHAT THE ORIGINAL SHOWS AT TURN CHANGE** is inventoried in
`doc/brief_turn_messages.md`. The generic boxes among it (the strategic
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
and animation, COLONY's landing art); the system display is a list of the
star's planets (named) instead of the planets' pictures; the science room
lists every discovery at once where the original shows one per click (each
click is still sent, as the original counts them); the GNN picture is not
drawn. A popup's help texts on right click are not offered.
"""
import pygame

from core import helpformat
from core.hud import blocks as hud
from core.hud import text as hudtext
from core.turnpopupwire import (  # noqa: F401 — the names callers use
    KINDS, IDS, SLOTS, SHIP_SLOTS, parse, build)
from core.turnpopupcontent import (  # noqa: F401
    DEFAULT_WORDS, content, leader_card)

REF_W, REF_PAD, REF_FONT, REF_TITLE_FONT = 1000, 30, 28, 38
REF_BUTTON = (220, 58)
REF_OPTION_H = 46


# ── drawing and input ─────────────────────────────────────────────────

class View:
    """The popup over the held frame, for one App: drawing and input."""

    def __init__(self):
        self._base = None
        self.rects = []            # [(rect, action)] of what can be clicked
        self.buttons = []          # the bottom row's actions, in order
        self.sent = None

    def reset(self):
        self._base = None
        self.rects = []
        self.buttons = []

    def render(self, surface, style, labels, popup, state, backdrop=None,
               app=None):
        """`backdrop(surface)`, when given, draws what stands behind the
        popup in the original — the galaxy map for the report phase's
        popups (mainscr2.cpp: Reports_Screen_ runs over the map) — once,
        when the popup first appears, instead of whatever HD frame came
        last (a new colony's screen before the Turn Summary, seen live)."""
        size = surface.get_size()
        if self._base is None or self._base.get_size() != size:
            if backdrop is not None:
                backdrop(surface)
            base = surface.copy()
            shade = pygame.Surface(size, pygame.SRCALPHA)
            shade.fill((0, 0, 0, 110))
            base.blit(shade, (0, 0))
            self._base = base
        surface.blit(self._base, (0, 0))
        words = dict(DEFAULT_WORDS, **{k: v for k, v in (labels or {}).items()
                                       if k in DEFAULT_WORDS and v})
        self.rects, self.buttons = draw(surface, style,
                                        content(popup, state, words, app))
        return self.rects

    def action_at(self, x, y):
        for rect, action in self.rects:
            if action is not None and rect.collidepoint(x, y):
                return action
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
    if pic is not None:
        k = max(1, int(round(3 * s)))          # integer magnification (28)
        pic = pygame.transform.scale(pic, (pic.get_width() * k,
                                           pic.get_height() * k))
    rows = []
    for text in c["lines"]:
        if isinstance(text, tuple):           # a table row: label, value
            rows.append((style.render_text(text[0], size, colour[:3]),
                         style.render_text(text[1], size, colour[:3])))
            continue
        rows.extend(_wrap(style, text, size, inner, colour) or [None])
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
    h = pad + (title.get_height() + pad // 2 if title else 0) + text_h + \
        (pad // 2 + opts_h if opts else 0) + pad + bh + pad
    h = min(h, win_h - 2 * pad)
    panel = pygame.Rect((win_w - w) // 2, (win_h - h) // 2, w, h)
    hud.popup(surface, panel, s)
    bottom = panel.bottom - pad - bh - pad
    y = panel.y + pad
    if title:
        surface.blit(title, title.get_rect(midtop=(panel.centerx, y)))
        y += title.get_height() + pad // 2
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
             "leader_level", "gnn", "combat_target", "landing")


def key_action(view, popup, event):
    """The action a key answers: ESC / Enter / Space on the last button."""
    if popup["kind"] not in KEY_KINDS or event.key not in (
            pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER,
            pygame.K_SPACE):
        return None
    buttons = [a for a in view.buttons if a is not None]
    return buttons[-1] if buttons else None
