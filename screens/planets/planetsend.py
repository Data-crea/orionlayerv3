"""Sending colony and outpost ships from the Planets screen — work order 271.

The original (`Planet_Summary_Screen`, plntsum.cpp:1929-2136): SEND COLONY
SHIP and SEND OUTPOST SHIP arm a send (`send_choice` 0 or 1, the button
drawn on; a second click disarms, :2075-2110); with a send armed, a click on
a row sends the nearest such ship there (`Scan_Summary_Box_Fields`,
:1261-1295 -> `Send_Nearest_Ship`, :209-317: the game's own confirmation
and message boxes, then `Make_Ships_Move_To`); a planet with an order shows
its colony or outpost marker and the ship's ETA, and a click on the marker
undoes the order (`Undo_Send_Order`, :1503-1575).

HD drives exactly those fields, read from open fix 97's PLSM block — never a
position of its own: a button is its field; a row is the game's row field
for that planet. HD's list is its own (sorted and scrolled by HD, decision
46), so a planet the game's window does not show is first brought into it
by the game's star icon for its star (:2042-2051, the star's first row at
the top) — an event-driven chain (decision 21): the click waits for the
snapshot that shows the planet in the game's window, then sends its row
field, at most `TRIES` star clicks. The boxes the game opens are HD's
message box (open fix 29).

HD EXTENSION `send_markers`: the marker is a tag in the planet cell — the
ship kind's word and its ETA in turns — not the original's ship pictures.
"""
import logging

from core import planetsblock
from core.hud import blocks as hud

log = logging.getLogger("planets")

TRIES = 2
COLONY_RGB = (120, 220, 120)
OUTPOST_RGB = (120, 180, 255)


def block(state):
    return getattr(state, "planets_screen", None)


def button_state(b, key):
    """'active' armed, 'normal' selectable, 'disabled' — or None without
    the block (HD's display only, as before)."""
    if b is None:
        return None
    return {2: "active", 1: "normal"}.get(b["buttons"][key], "disabled")


def armed(b):
    return b is not None and b["send_choice"] in (0, 1)


def etas(b, planet):
    """(colony ETA, outpost ETA) of the planet's orders, -1 for none."""
    i = planetsblock.row_of(b, planet)
    if i is None:
        return -1, -1
    r = b["rows"][i]
    return r["colony_eta"], r["outpost_eta"]


class Sender:
    """One pending action at a time: ('send' | 'undo_colony' |
    'undo_outpost', planet), carried out on the snapshots that follow."""

    def __init__(self):
        self.pending = None
        self.marks = []          # [(rect, kind, planet)] drawn this frame

    def toggle(self, app, b, key):
        f = b["fields"]["send_" + key] if b else planetsblock.NO_FIELD
        if f == planetsblock.NO_FIELD or f < 0:
            return False
        log.info("Send %s ship: field %d", key, f)
        if app.connected:
            app.client.activate_field(f)
        return True

    def request(self, kind, planet):
        self.pending = {"kind": kind, "planet": planet, "tries": 0,
                        "waiting": False}
        log.info("Planets: %s at planet %d", kind, planet)

    def step(self, app, b, fresh):
        """On a fresh snapshot: send the row's or marker's field if the
        game's window shows the planet, else its star icon, once a try."""
        p = self.pending
        if p is None or b is None or not fresh:
            return
        i = planetsblock.row_of(b, p["planet"])
        if i is None:
            log.info("Planets: planet %d is not in the game's list",
                     p["planet"])
            self.pending = None
            return
        vis = i - b["first"]
        if 0 <= vis < planetsblock.ROWS_SHOWN:
            key = {"send": "rows", "undo_colony": "colony",
                   "undo_outpost": "outpost"}[p["kind"]]
            f = b["fields"][key][vis]
            self.pending = None
            if f == planetsblock.NO_FIELD or f < 0:
                log.info("Planets: no %s field on row %d", key, vis)
                return
            log.info("Planets: %s -> field %d (game row %d)", p["kind"], f, i)
            if app.connected:
                app.client.activate_field(f)
            return
        if p["tries"] >= TRIES:
            log.info("Planets: planet %d stays out of the game's window",
                     p["planet"])
            self.pending = None
            return
        star = getattr(app.client.state, "planets_raw", None)
        from core.structs import planet as planet_struct
        try:
            st = planet_struct.parse(star[p["planet"]]).star_index
        except (TypeError, IndexError, ValueError):
            self.pending = None
            return
        stars = b["fields"]["stars"]
        if not 0 <= st < len(stars) or stars[st] < 0:
            self.pending = None
            return
        p["tries"] += 1
        log.info("Planets: star %d's icon -> field %d (bring planet %d in)",
                 st, stars[st], p["planet"])
        if app.connected:
            app.client.activate_field(stars[st])

    def draw_marks(self, surface, screen, b, rows, first, bands, col,
                   size, scale=1.0):
        """The orders' tags in the planet cell, right-aligned; their rects
        are the undo clicks."""
        self.marks = []
        if b is None or col is None:
            return
        x, w = col
        for band, (by, bh) in enumerate(bands):
            li = first + band
            if li >= len(rows):
                break
            planet = rows[li]["index"]
            c_eta, o_eta = etas(b, planet)
            right = x + w - size // 2
            for kind, eta, rgb, word in (
                    ("undo_outpost", o_eta, OUTPOST_RGB, "OUTPOST"),
                    ("undo_colony", c_eta, COLONY_RGB, "COLONY")):
                if eta < 0:
                    continue
                text = f"{word} {eta}" if eta > 0 else word
                img = screen.style.render_text(text, size, rgb)
                r = img.get_rect(right=right, centery=by + bh // 4 + 2)
                hud.field(surface, r.inflate(6, 2), scale)
                surface.blit(img, r)
                self.marks.append((r.inflate(6, 2), kind, planet))
                right = r.x - size

    def mark_at(self, pos):
        return next(((k, p) for r, k, p in self.marks if r.collidepoint(pos)),
                    None)
