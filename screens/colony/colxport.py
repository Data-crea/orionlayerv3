"""The transport popup — the colony screen's TRANSPORT button and the list
of colonies it opens (work order 316 B; open fix 103 carries the move).

THE ORIGINAL: while colonists are in hand the colony screen adds a button
at (307, 159) ([11], C_Anims_ 24; colony.cpp:1771-1781, while an unassigned
pop is left and the colony is valid); its click runs `COLXPORT::Xport_Popup_`
(colony_main.cpp:1068-1076; colxport.cpp:112-172): COLPUPS.LBX 0x10 over the
screen, the player's colonies that are not outposts in array order
(`Build_Global_Colony_List_`, :91-104 — the colony itself and those at its
star too), SIX rows at a time (y 38 i + 54): the planet's name in a
130 x 28 paragraph at x 15, red where its star is blockaded for the player
or the colony has the plague (:248-262), and every pop of the colony in one
strip from x 148 to 441 (`Draw_Info_Pop_For_`, :295-309: all three jobs,
the icon walk's order); a hidden field over each row (x 15..441, :232-241),
the up and down arrows (COLPUPS 0x13 at (448, 52), 0x14 at (447, 243);
`Decrement_First_` / `Increment_First_` by six, :139-146), a slider from
six colonies on (:185-201, the thumb :271-293), and the cancel button
(0x11 at (352, 285), :222-229). A row returns its colony and the screen
calls `Send_Cluster_(colony, -1)` (colony_main.cpp:1072): the move with all
its questions and boxes (`colxferflow`); cancel returns -1 and the
colonists stay in hand.

HD (TRANSCRIPTION `transport_popup`): the same list, the same six rows and
the same steps, what a row answers and what cancel does, drawn by HD.
DEVIATION `transport_popup_hud`: the HUD look (decision 71) in place of
COLPUPS.LBX 0x10's art (471 x 323 at the screen's top left: two column
heads, "COLONY NAME" and "COLONY POPULATION", six ruled rows, the arrows
and CANCEL) — a lit popup panel centred on the screen, the heads' and the
button's words typed in `layout.json` `transport` (decision 15), the arrows
drawn as triangles, the thumb as a bar; the rows' place and size are the
panel's, the original's proportions inside it.
HD EXTENSION `transport_row_hover`: the row under the pointer is drawn as
the HUD's selected row (the original marks nothing over its hidden
fields).
OMISSION `transport_plague_red`: the plague reddens a row's name in the
original; the wire carries the plague for the colony on screen only
(CEVT), so only a blockade reddens it in HD.
HD EXTENSION `transport_escape`: ESC is cancel (the original's loop ends
on its cancel field or a row alone).
"""
import pygame

from core import mouse as mouse_input
from core.hud import blocks as hud
from core.hud import tables as hudtables
from core.hud import text as hudtext
from core.structs import colony as colony_struct
from core.structs import planet as planet_struct
from core.structs import player as player_struct
from core import colonyfacts
from screens.colony_summary import colonyfigures

ROWS = 6
#: The original's row geometry, native px (colxport.cpp:232-262, :295-309).
NAME_X, NAME_W, STRIP_X0, STRIP_X1, ROW_STEP = 15, 130, 148, 441, 38
#: Reference geometry of HD's panel at 1080, scaled by `win_h / 1080`.
REF_W, REF_ROW, REF_PAD, REF_TITLE, REF_BAR = 1180, 96, 30, 40, 40
REF_FONT, REF_BUTTON = 30, (240, 60)


def colonies(state):
    """`Build_Global_Colony_List_`: the player's colonies that are not
    outposts, in array order (colxport.cpp:91-104)."""
    me = getattr(state, "player_num", 0)
    out = []
    for i, raw in enumerate(getattr(state, "colonies_raw", None) or []):
        rec = colony_struct.parse(raw)
        if rec.owner == me and rec.outpost_flag == 0:
            out.append(i)
    return out


def strip_words(rec, held=()):
    """Every assigned pop of a colony in the icon walk's order with no job
    filter (`Do_Colony_Info_Pop_Stuff_For_Pop_`, coldraw.cpp:281-337:
    state, conquered, job, the nibble order 9, 0, ..., 8, then the array)."""
    # the colonists in hand are HD's (decision 47): on the wire they are
    # still assigned, in the original they are not, and the strip draws
    # assigned pops only (coldraw.cpp:336)
    words = [w for i, w in enumerate(list(rec.pop)[:rec.n_pops])
             if i not in held]
    order = (9, 0, 1, 2, 3, 4, 5, 6, 7, 8)

    def state(w):
        nib = w & 0x0F
        return 3 if nib == 9 else 4 if nib == 8 else 2

    out = []
    for st in range(7):
        for conq in (0, 1):
            for job in range(3):
                for nib in order:
                    for w in words:
                        if (w & 0x0F) == nib and state(w) == st and \
                                colony_struct.pop_prof(w) == job and \
                                w & colony_struct.POP_MASK_ASSIGNED and \
                                ((w >> 10) & 1) == conq:
                            out.append(w)
    return out


class Popup:
    """The open popup: its list, its window, what is drawn and hit."""

    def __init__(self, state, source, held=()):
        self.source = source
        self.held = tuple(held)
        self.first = 0
        self.list = colonies(state)
        self.rects = {}             # "row<i>" / "up" / "down" / "cancel"
        self.panel = None

    def step(self, delta):
        """`Decrement_First_` clamps at 0; `Increment_First_` only while a
        colony stands beyond the window (colxport.cpp:139-146)."""
        if delta < 0:
            self.first = max(0, self.first - 1)
        elif self.first + ROWS < len(self.list):
            self.first += 1

    def visible(self):
        return self.list[self.first:self.first + ROWS]

    def click(self, x, y):
        """("choose", colony) / ("cancel", None) / ("step", None) / None."""
        for key, rect in self.rects.items():
            if not rect.collidepoint(x, y):
                continue
            if key == "cancel":
                return "cancel", None
            if key in ("up", "down"):
                self.step(-1 if key == "up" else 1)
                return "step", None
            if key.startswith("row"):
                return "choose", int(key[3:])
        return None

    def render(self, surface, state, style, words, figures):
        win_w, win_h = surface.get_size()
        s = win_h / 1080
        pad, row_h = int(REF_PAD * s), int(REF_ROW * s)
        title_h, bar = int(REF_TITLE * s * 1.4), int(REF_BAR * s)
        bw, bh = int(REF_BUTTON[0] * s), int(REF_BUTTON[1] * s)
        w = int(REF_W * s)
        h = pad + title_h + ROWS * row_h + pad + bh + pad
        panel = pygame.Rect((win_w - w) // 2, (win_h - h) // 2, w, h)
        shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 110))
        surface.blit(shade, (0, 0))
        hud.popup(surface, panel, s)
        self.panel, self.rects = panel, {}
        top = panel.y + pad + title_h
        inner = pygame.Rect(panel.x + pad, top, panel.w - 3 * pad - bar,
                            ROWS * row_h)
        # the original's proportions inside the list: name 130 of the
        # 426 px from x 15 to 441, the strip 293 from 148
        span = STRIP_X1 - NAME_X
        name_w = inner.w * NAME_W // span
        strip_x = inner.x + inner.w * (STRIP_X0 - NAME_X) // span
        strip_w = inner.right - strip_x
        head = tuple(hudtext.colour("title")[:3])
        for key, x in (("name", inner.x + pad // 2), ("population",
                                                       strip_x)):
            img = style.render_text(words.get(key, ""),
                                    max(12, int(REF_TITLE * s * 0.8)), head)
            surface.blit(img, img.get_rect(midleft=(x, panel.y + pad +
                                                    title_h // 2)))
        size = max(10, int(REF_FONT * s))
        me = getattr(state, "player_num", 0)
        races = {}
        for pi, raw in enumerate(getattr(state, "player_raw", None) or []):
            if raw:
                races[pi] = int(player_struct.parse(raw).race)
        raws = getattr(state, "colonies_raw", None) or []
        planets = getattr(state, "planets_raw", None) or []
        stars = getattr(state, "stars", None) or []
        for k, index in enumerate(self.visible()):
            row = pygame.Rect(inner.x, top + k * row_h, inner.w, row_h)
            self.rects[f"row{index}"] = row
            # the row under the pointer as the HUD's selected row: where a
            # click goes (the original marks nothing over its hidden field)
            hudtables.table_row(surface, row, s, k, selected=row.collidepoint(
                *mouse_input.pos()))
            rec = colony_struct.parse(raws[index])
            name = colonyfacts.planet_name(rec, planets, stars)
            red = False
            if 0 <= rec.planet < len(planets):
                si = planet_struct.parse(planets[rec.planet]).star_index
                if 0 <= si < len(stars):
                    red = bool((int(stars[si].blockaded) >> (me & 0x1F)) & 1)
            colour = hudtext.colour("negative" if red else "value")
            img = style.render_text(name or "", size, tuple(colour[:3]))
            if img.get_width() > name_w:
                img = pygame.transform.smoothscale(
                    img, (name_w, max(1, img.get_height() * name_w //
                                      img.get_width())))
            surface.blit(img, img.get_rect(midleft=(row.x + pad // 2,
                                                    row.centery)))
            self._strip(surface, rec, races, figures,
                        pygame.Rect(strip_x, row.y, strip_w, row.h),
                        self.held if index == self.source else ())
        # the arrows and the thumb, in the scroll column
        col = pygame.Rect(inner.right + pad, top, bar, ROWS * row_h)
        up = pygame.Rect(col.x, col.y, bar, bar)
        down = pygame.Rect(col.x, col.bottom - bar, bar, bar)
        ink = tuple(hudtext.colour("label")[:3])
        # LOOK EXCEPTION marking: the popup's up arrow in the label colour (COLPUPS 0x13, colxport.cpp:204-211)
        pygame.draw.polygon(surface, ink, [(up.centerx, up.y + 4),
                                           (up.right - 4, up.bottom - 4),
                                           (up.x + 4, up.bottom - 4)])
        # LOOK EXCEPTION marking: the popup's down arrow in the label colour (COLPUPS 0x14, colxport.cpp:213-220)
        pygame.draw.polygon(surface, ink, [(down.x + 4, down.y + 4),
                                           (down.right - 4, down.y + 4),
                                           (down.centerx, down.bottom - 4)])
        self.rects["up"], self.rects["down"] = up, down
        n = len(self.list)
        track = pygame.Rect(col.x + bar // 4, up.bottom + 4, bar // 2,
                            down.y - up.bottom - 8)
        if n >= ROWS:                           # colxport.cpp:185, :274
            y1 = track.y + self.first * track.h // n
            y2 = track.y + (self.first + ROWS) * track.h // n
            # LOOK EXCEPTION marking: the popup's thumb, the original's own bar (colxport.cpp:271-293)
            pygame.draw.rect(surface, ink, (track.x, y1, track.w,
                                            max(2, y2 - y1)))
        cancel = pygame.Rect(0, 0, bw, bh)
        cancel.midbottom = (panel.centerx, panel.bottom - pad)
        hud.action_button(surface, cancel, s, "normal",
                          words.get("cancel", "CANCEL"),
                          style_renderer=style)
        self.rects["cancel"] = cancel
        return panel

    @staticmethod
    def _strip(surface, rec, races, figures, rect, held=()):
        """The colony's pops in one row, squeezed as the original squeezes
        (`Calculate_Squish_Step_`: full pitch while they fit)."""
        words = strip_words(rec, held)
        if not words or figures is None or figures.state == "missing":
            return
        owner_race = races.get(rec.owner)
        pics = [figures.get(colonyfigures.figure_for(w, owner_race, races))
                for w in words]
        size = max((p.get_width() for p in pics if p is not None),
                   default=0)
        if not size:
            return
        n = len(pics)
        pitch = size if n < 2 else min(size, max(1, (rect.w - size) //
                                                 (n - 1)))
        for k, pic in enumerate(pics):
            if pic is not None:
                surface.blit(pic, (rect.x + k * pitch,
                                   rect.centery - pic.get_height() // 2))
