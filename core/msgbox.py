"""The HD message box — work order 188, Parts 4 and 5, on open fix 29.

**ONE BOX FOR EVERY GENERIC BOX THE GAME OPENS.** `TEXTBOX::Do_Text_Box_`
(with `Text_Box_`, `Timed_Text_Box_`, `GENDRAW::Message_Box_`, `Help_`,
`COMBAT::Message_Box_Titled_`, `MAINSCR::Mini_Main_Screen_Text_Box_` and
`HAROLD::User_Box_`'s text types), `GENDRAW::Message_Box_Exploding_` (and
`Warning_Box_`, `Message_Box_Exploding_Star_`) and
`GENDRAW::Confirmation_Box_` print a string their caller formatted, which
until open fix 29 reached a client only as pixels. "MSGB" puts the kind,
the title, the text (raw, FMTPARA codes and all) and the answer fields on
the wire while the box takes input; this draws it in HD wherever it opens,
over the screen that is open — an HD page, the galaxy map at turn start and
through turn processing, where no HD screen claims the id — or over the held
last HD frame under an HD popup (`core.overlays.backdrop`, work order 196 A).

WHAT IS TRANSCRIPTION: the text and title are the game's own, as the caller
formatted them; the answers are the box's own fields (Yes = "Y", No = "N",
the dismiss field ESC), activated by their id — which is what the box's own
input loop compares (gendraw.cpp:201-207, textbox.cpp `Text_Box_Get_Input_`).
The line breaks and columns follow FMTPARA (`core.helpformat`); the values
the text's item codes print come with the block (open fix 67, version 2) —
the boarding result's bonuses and marines.

**DEVIATION `hud_message_box`**: drawn in the HUD style (glass, the frame
colour, HD's font) instead of TEXTBOX.LBX / WARNING.LBX / CONFIRM.LBX art,
the warning box's animation not played, and — because the original's
message and text boxes are answered by a click ANYWHERE (one full-screen
hidden field) — HD draws the text box's CLOSE button on every box that is
not a confirmation (the warning box has none in the original), and takes
a click anywhere and Enter / ESC / Space.

TRANSCRIPTION `box_columns` (work order 213): a row whose runs sit at \\aX
columns is laid out at those columns, as shares of the paragraph width the
box formats at (339 px, textbox.cpp:200-208) — a left run from its column, a
right- or centre-justified one up to the column the next X names: the
boarding result's two sides side by side (cmbtfir2.cpp:1650-1666). The words on the buttons are artwork in the original
and typed in `assets/shared/msgbox/labels.json` (decision 15).
"""
import struct as _st

import pygame

from core import helpformat, lang
from core.hud import blocks as hud
from core.hud import text as hudtext

KINDS = {1: "text", 2: "timed", 3: "message", 4: "warning",
         5: "confirmation"}
DEFAULT_WORDS = {"yes": "YES", "no": "NO", "close": "CLOSE"}
#: Reference geometry (1080 px tall), scaled by `win_h / 1080`.
REF_W = 900
REF_PAD = 34
#: The text's and the title's font px at 1080 — a paragraph, not a label in
#: a box, so sized directly and scaled once by `win_h / 1080` (090t).
REF_FONT, REF_TITLE_FONT = 30, 38
REF_BUTTON = (220, 60)
#: The held frame's dim under the box (as the F12 notice's).
DIM_ALPHA = 110


def parse(gs, data, pos):
    """Read MSGB at `pos` into `gs.message_box` (None when absent or short).
    Returns the new position."""
    gs.message_box = None
    if data[pos:pos + 4] != b"MSGB" or pos + 12 > len(data):
        return pos
    version, kind, fa, fb, ticks = _st.unpack_from("<BBhhh", data, pos + 4)
    at = pos + 12
    texts = []
    for _ in range(2):
        if at + 2 > len(data):
            return pos
        (n,) = _st.unpack_from("<h", data, at)
        at += 2
        if n < 0 or at + n > len(data):
            return pos
        texts.append(lang.wire_text(data[at:at + n]))
        at += n
    items = {}
    if version == 2:
        # the values of the text's item codes (open fix 67): a count, then
        # an index byte and an int32 each
        if at >= len(data) or at + 1 + data[at] * 5 > len(data):
            return pos
        for k in range(data[at]):
            idx, val = _st.unpack_from("<Bi", data, at + 1 + 5 * k)
            items[idx] = val
        at += 1 + data[at] * 5
    if version not in (1, 2) or kind not in KINDS:
        return pos
    gs.message_box = {"kind": KINDS[kind], "field_a": fa, "field_b": fb,
                      "ticks": ticks, "title": texts[0] or None,
                      "text": texts[1], "items": items}
    return at


def build(kind, text, title=None, field_a=1, field_b=-1, ticks=0,
          items=None):
    """The block as the engine writes it — for the checks' stand-ins;
    version 2 (open fix 67) when `items` are given."""
    code = {v: k for k, v in KINDS.items()}[kind]
    out = b"MSGB" + _st.pack("<BBhhh", 1 if items is None else 2, code,
                             field_a, field_b, ticks)
    for s in (title or "", text):
        raw = s.encode("latin-1")
        out += _st.pack("<h", len(raw)) + raw
    if items is not None:
        out += bytes([len(items)]) + b"".join(
            _st.pack("<Bi", k, v) for k, v in items.items())
    return out


def answers(box, fields):
    """`[(key, field)]` for the box's answers, each resolved in the LIVE
    list by the id the box reported — or None for a field not in it (the
    box and the list come in two messages; a list from before the box has
    no such field and nothing is sent until it does)."""
    by_index = {getattr(f, "index", None): f for f in (fields or [])}
    if box["kind"] == "confirmation":
        keys = (("yes", box["field_a"]), ("no", box["field_b"]))
    else:
        keys = (("close", box["field_a"]),)
    return [(key, by_index.get(fid)) for key, fid in keys]


def lines_of(text):
    """The text's lines as FMTPARA lays them out: [(plain, paragraph)]."""
    return [(ln.plain(), ln.paragraph_break)
            for ln in helpformat.parse(text or "")]


#: The paragraph width `Do_Text_Box_` formats at (textbox.cpp:200-208).
TEXT_W = 339


def column_runs(line):
    """`[(text, align, x0, x1)]` in the original's px for a line with a
    column (an X function), else None: where each run sits — a left run from
    its column, a right or centred one within its column and the next."""
    runs = [r for r in line.runs if r.text.strip()]
    if not any(r.x is not None or r.end_x is not None for r in runs):
        return None
    out, at = [], 0
    for k, r in enumerate(runs):
        x0 = r.x if r.x is not None else at
        x1 = r.end_x if r.end_x is not None else (
            runs[k + 1].x if k + 1 < len(runs) and runs[k + 1].x is not None
            else TEXT_W)
        out.append((r.text.strip(), r.align or "left", x0, x1))
        at = x1
    return out


def split_right(line):
    """`(left, right)` for a line whose last run is right-justified (a
    table row: "Food per farmer" … "0"), else None."""
    runs = [r for r in line.runs if r.text]
    if len(runs) >= 2 and runs[-1].align == "right":
        return (" ".join(r.text.strip() for r in runs[:-1]),
                runs[-1].text.strip())
    return None


class View:
    """The box over the held frame, for one App: drawing and input."""

    def __init__(self):
        self._base = None
        self._key = None
        self.rects = {}           # key -> window rect of its button
        self.panel = None

    def reset(self):
        self._base = None
        self._key = None
        self.rects = {}
        self.panel = None

    def render(self, surface, style, labels, box, backdrop=None):
        """Draw `box` over the screen behind it; returns the panel rect.

        `backdrop(surface)` draws the screen that is open and returns True,
        or False when there is none to draw — then the box stands over the
        held surface, dimmed once (`core.overlays`, work order 196 A)."""
        self._base = dimmed_base(surface, self._base, DIM_ALPHA, backdrop)
        surface.blit(self._base, (0, 0))
        self.panel, self.rects = draw(surface, style, labels, box)
        return self.panel

    def answer_at(self, box, fields, x, y):
        """The field a click at (x, y) answers, or None. A text / message
        box takes a click anywhere (its one full-screen field)."""
        live = dict(answers(box, fields))
        for key, rect in self.rects.items():
            if rect.collidepoint(x, y):
                return live.get(key)
        if box["kind"] != "confirmation":
            return live.get("close")
        return None

    @staticmethod
    def answer_key(box, fields, event):
        """The field a key answers: Y / N on a confirmation (the box's own
        hotkeys), Enter / ESC / Space on the others."""
        live = dict(answers(box, fields))
        ch = (getattr(event, "unicode", "") or "").lower()
        if box["kind"] == "confirmation":
            return live.get({"y": "yes", "n": "no"}.get(ch, ""))
        if event.key in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_SPACE,
                         pygame.K_KP_ENTER):
            return live.get("close")
        return None


def dimmed_base(surface, base, alpha, backdrop=None):
    """What a box or popup stands on, dimmed by `alpha`: the screen that is
    open, drawn NOW by `backdrop` (a live screen, so every frame), or — when
    `backdrop` draws nothing — the held surface, copied once and kept
    (`base`), because after the first frame the surface holds the box too.
    Shared by the message box and the turn popups (work order 196 A)."""
    size = surface.get_size()
    live = backdrop is not None and backdrop(surface)
    if not live and base is not None and base.get_size() == size:
        return base
    out = surface.copy()
    shade = pygame.Surface(size, pygame.SRCALPHA)
    shade.fill((0, 0, 0, alpha))
    out.blit(shade, (0, 0))
    return out


def draw(surface, style, labels, box):
    """The panel: title, the text, the buttons. `(panel, {key: rect})`."""
    win_w, win_h = surface.get_size()
    s = win_h / 1080
    words = dict(DEFAULT_WORDS, **{k: v for k, v in (labels or {}).items()
                                   if k in DEFAULT_WORDS and v})
    pad = int(REF_PAD * s)
    w = int(REF_W * s)
    inner = w - 2 * pad
    size = max(10, int(REF_FONT * s))
    colour = hudtext.colour("value")
    # the box's text and title are the game's: no word of them is
    # OrionLayer's to translate (work order 200 C, `core/lang.verbatim`)
    with lang.verbatim():
        rows = []
        from core.textfit import wrap_rendered
        for ln in helpformat.parse(box["text"] or "", box.get("items")):
            plain = ln.plain()
            if not plain.strip():
                rows.append(None)
                continue
            cols = column_runs(ln)
            pair = split_right(ln)
            if cols is not None:
                rows.append([(style.render_text(t, size, colour[:3]), a, x0,
                              x1) for t, a, x0, x1 in cols])
            elif pair is not None:
                # a table row: the label left and the value right, in a column
                # of the box's text width (FMTPARA's justification codes)
                rows.append((style.render_text(pair[0], size, colour[:3]),
                             style.render_text(pair[1], size, colour[:3])))
            else:
                rows.extend(wrap_rendered(style, plain, size, inner, colour))
            if ln.paragraph_break:
                rows.append(None)
        while rows and rows[-1] is None:
            rows.pop()
        step = int(size * 1.3)
        title = style.render_text(box["title"], max(12, int(REF_TITLE_FONT * s)),
                                  tuple(hudtext.colour("title")[:3])) \
            if box.get("title") else None
    bw, bh = int(REF_BUTTON[0] * s), int(REF_BUTTON[1] * s)
    text_h = sum(step if r is not None else step // 2 for r in rows)
    h = pad + (title.get_height() + pad // 2 if title else 0) + text_h + \
        pad + bh + pad
    h = min(h, win_h - 2 * pad)
    panel = pygame.Rect((win_w - w) // 2, (win_h - h) // 2, w, h)
    hud.popup(surface, panel, s)
    y = panel.y + pad
    if title:
        surface.blit(title, title.get_rect(midtop=(panel.centerx, y)))
        y += title.get_height() + pad // 2
    col = pygame.Rect(0, 0, int(inner * 0.72), 1)
    col.centerx = panel.centerx
    for r in rows:
        if r is None:
            y += step // 2
            continue
        if y + step > panel.bottom - pad - bh:
            break                   # the original clips at its window too
        if isinstance(r, list):
            left = panel.x + pad
            for img, a, x0, x1 in r:
                p0, p1 = (left + inner * v // TEXT_W for v in (x0, x1))
                at = {"right": "topright", "center": "midtop"}.get(a,
                                                                  "topleft")
                px = {"right": p1, "center": (p0 + p1) // 2}.get(a, p0)
                surface.blit(img, img.get_rect(**{at: (px, y)}))
        elif isinstance(r, tuple):
            surface.blit(r[0], (col.x, y))
            surface.blit(r[1], r[1].get_rect(topright=(col.right, y)))
        else:
            surface.blit(r, r.get_rect(midtop=(panel.centerx, y)))
        y += step
    keys = ("yes", "no") if box["kind"] == "confirmation" else ("close",)
    gap = pad
    total = len(keys) * bw + (len(keys) - 1) * gap
    x = panel.centerx - total // 2
    rects = {}
    for key in keys:
        r = pygame.Rect(x, panel.bottom - pad - bh, bw, bh)
        hud.action_button(surface, r, s, "normal", words[key],
                          style_renderer=style)
        rects[key] = r
        x += bw + gap
    return panel, rects
