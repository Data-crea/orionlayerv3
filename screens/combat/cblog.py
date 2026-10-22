"""The battle log — work order 267 (Data, 15 October 2026: a button in the
free place beside OPTIONS; a click opens a window that tells in detail how
the damage was dealt, in colours that keep it readable).

INVENTION `battle_log`: the original keeps no log; the battle shows each
hit's numbers for half a second and forgets them. HD records every event
the engine sends (open fix 56, one ring, numbered) as it arrives, so the
log is whole even while the picture still plays, and keeps it for the
battle (a new battle's serial starts a new log).

What a hit says, from the engine's own values at the hook: who fired,
what, at whom; the damage the target's shields took (`absorbed`: the
shield arc's hits spent, `Apply_Ship_Damage`'s `sys_dmg`, cmbtfire.cpp:
975-990) and the damage that came through (`past_shields`, its `dmg_out`).
Both zero: the shot missed. A unit destroyed, retreating, captured, a
special used and a bombardment are their own lines. The summary adds up
what each unit took.

The colours (readable on the dark glass, not the original's palette): each
side's name in its player's map colour (the galaxy map's `owner_*`), the
shields' damage light blue, the damage through orange — the hues of the
battle's own two numbers (`cbnumbers`), lifted for text — a loss red, a
miss grey. The words go through OrionLayer's language table.

No help entry: HELP.LBX has none for a button the original lacks.
"""
import pygame

from core import lang, palette
from core.hud import blocks as hud
from core.hud import lru

TEXT = (214, 214, 200)
DIM = (140, 140, 150)
HEAD = (240, 220, 150)
SHIELDS = (120, 165, 255)
DAMAGE = (252, 164, 28)
LOSS = (255, 96, 72)
NEUTRAL = (200, 200, 200)
#: the hit kinds and the event fields that name shooter and target
HITS = {"beam_shot": ("source", "target"), "missile_hit": ("source", "target"),
        "fighter_pass": ("source", "target"),
        "blast_hit": ("source", "unit"), "web_damage": (None, "unit"),
        "reflect": ("reflector", "shooter"),
        "converter_hit": ("source", "target")}
CONVERTER = 38
#: the Energy Absorber's discharge is a beam shot of weapon 46 with no slot
#: (cmbtfire.cpp:1787-1854), a weapon the weapon table does not name; the
#: log names it by the special system, `SPECIAL_ENERGY_ABSORBER` 10
ABSORBER_SHOT, ABSORBER_SPECIAL = 46, 10
#: columns of a line, as fractions of the list's width
COLUMNS = (0.0, 0.07, 0.31, 0.54, 0.78, 0.89, 1.0)


class BattleLog:
    """Every event of one battle, as lines."""

    def __init__(self):
        self.reset()

    def reset(self, serial=None):
        self.serial, self.lines, self._seen = serial, [], set()

    def add(self, events, combat, weapon_name, special_name=None):
        """The snapshot's events not seen yet; `combat` names the units.
        The battle's `turn` counts from 0; the log says it from 1."""
        if combat is not None and combat.get("serial") != self.serial:
            self.reset(combat.get("serial"))
        units = (combat or {}).get("units") or []
        turn = (combat or {}).get("turn")
        turn = turn + 1 if isinstance(turn, int) else turn
        for ev in events:
            key = (ev.get("serial"), ev.get("seq"))
            if key in self._seen:
                continue
            self._seen.add(key)
            line = describe(ev, units, turn, weapon_name, special_name)
            if line is not None:
                self.lines.append(line)

    def totals(self):
        """[(unit, owner, shields, damage, lost)] by damage taken."""
        out = {}
        for ln in self.lines:
            if ln.get("tgt") is None:
                continue
            t = out.setdefault(ln["tgt"], [ln["tgt_owner"], 0, 0, False])
            t[1] += ln.get("shields", 0)
            t[2] += ln.get("damage", 0)
            t[3] = t[3] or ln.get("note") == "destroyed"
        return sorted(((u, *v) for u, v in out.items()),
                      key=lambda r: (-r[3], -r[2] - r[1], r[0]))


def _unit(units, i):
    if i is None or not 0 <= int(i) < len(units):
        return None, None
    u = units[int(i)]
    return (u.get("name") or f"#{i}").strip(), u.get("owner")


def describe(ev, units, turn, weapon_name, special_name=None):
    """One log line for an event, or None for what the log does not say
    (sounds, aims, a missile's flight)."""
    k = ev.get("kind")
    line = {"turn": turn, "kind": k, "src": None, "src_owner": None,
            "tgt": None, "tgt_owner": None, "what": "", "shields": 0,
            "damage": 0, "note": ""}
    if k in HITS:
        s, t = HITS[k]
        if k == "beam_shot" and ev.get("at_missile"):
            return None
        if k == "missile_hit" and ev.get("anti_missile"):
            return None
        line["src"], line["src_owner"] = _unit(units, ev.get(s)) if s \
            else (None, None)
        line["tgt"], line["tgt_owner"] = _unit(units, ev.get(t))
        line["shields"] = max(0, int(ev.get("absorbed", 0) or 0))
        line["damage"] = max(0, int(ev.get("past_shields", 0) or 0))
        wid = {"beam_shot": ev.get("weapon"), "missile_hit": ev.get("type"),
               "fighter_pass": ev.get("type"),
               "converter_hit": CONVERTER}.get(k)
        if wid == ABSORBER_SHOT and special_name is not None:
            line["what"] = special_name(ABSORBER_SPECIAL) or ""
        else:
            line["what"] = (weapon_name(wid) if wid is not None else None)
        line["what"] = line["what"] or {
            "blast_hit": "blast", "web_damage": "plasma web",
            "reflect": "reflected"}.get(k, "")
        if not (line["shields"] or line["damage"]):
            line["note"] = "missed"
        return line
    if k in ("destroy", "retreat"):
        line["tgt"], line["tgt_owner"] = _unit(units, ev.get("unit"))
        line["note"] = {"destroy": "destroyed", "retreat": "retreats"}[k]
        return line
    if k == "capture":
        line["src"], line["src_owner"] = _unit(units, ev.get("attacker"))
        line["tgt"], line["tgt_owner"] = _unit(units, ev.get("defender"))
        line["what"], line["note"] = "boarding", (
            "captured" if ev.get("result") else "repelled")
        return line
    if k in ("special", "bomb"):
        if k == "special" and (ev.get("weapon") == CONVERTER or
                               ev.get("at_missile")):
            return None             # the converter's line is its hit
        line["src"], line["src_owner"] = _unit(units, ev.get("source"))
        line["tgt"], line["tgt_owner"] = _unit(units, ev.get("target"))
        line["what"] = weapon_name(ev.get("weapon")) or ""
        if k == "bomb":
            line["damage"] = max(0, int(ev.get("hits", 0) or 0))
        return line
    return None


def owner_rgb(owner, colours):
    """The player's map colour (`galaxy_map.owner_<colour>`)."""
    c = (colours or {}).get(owner)
    if c is None:
        return NEUTRAL
    return tuple(palette.col("galaxy_map", f"owner_{int(c)}", NEUTRAL))


class LogWindow:
    """The window over the field: the summary, then every line."""

    def __init__(self):
        self.open, self.first, self.rect = False, None, None
        self.close_rect = self.list_rect = None
        self._rows = 1
        #: work order 324 (UNVERIFIED live): `body` and the cell pictures
        #: are kept; `draw` ran both for every visible cell every frame.
        self._body_key, self._body_rows = None, None
        self._pics = lru.TextCache()

    def _body(self, log, colours):
        """`body`, rebuilt only when the log grew or was replaced, or the
        colours changed — the lines are appended and never edited, and a
        new battle's log is a reset list with another length or serial."""
        key = (log, log.serial, len(log.lines), id(log.lines),
               tuple(sorted((colours or {}).items())))
        seen = self._body_key
        if seen is None or seen[0] is not key[0] or seen[1:] != key[1:]:
            self._body_rows = self.body(log, colours)
            self._body_key = key
        return self._body_rows

    def _picture(self, style, text, size, rgb, room, squeeze):
        """The cell's picture: the text, squeezed to `room` px wide when
        it outruns it (a head is never squeezed)."""
        def build():
            img = style.render_text(text, size, rgb)
            if squeeze and img.get_width() > room:
                img = pygame.transform.smoothscale(
                    img, (max(1, room), img.get_height()))
            return img
        return self._pics.fetch((id(style), lang.state_key(), text, size,
                                 tuple(rgb), room if squeeze else None, squeeze),
                                 build)

    def toggle(self):
        self.open, self.first = not self.open, None

    def key(self, key):
        if self.open and key == pygame.K_ESCAPE:
            self.open = False
            return True
        return False

    def wheel(self, dy):
        if not self.open:
            return False
        self.first = max(0, (self.first or 0) - 3 * dy)
        return True

    def click(self, x, y):
        """True when the window takes the click (it is modal)."""
        if not self.open:
            return False
        if self.close_rect is not None and self.close_rect.collidepoint(x, y):
            self.open = False
        return True

    def body(self, log, colours):
        """[(cells, colour of each)] — the summary, then the lines."""
        rows = [([("SUMMARY", HEAD)], "head"),
                ([("", DIM), ("Unit", DIM), ("", DIM), ("", DIM),
                  ("Shields", DIM), ("Damage", DIM)], "cols")]
        for unit, owner, sh, dmg, lost in log.totals():
            rows.append(([("", TEXT), (unit, owner_rgb(owner, colours)),
                          ("destroyed" if lost else "", LOSS),
                          ("", TEXT), (str(sh) if sh else "-", SHIELDS),
                          (str(dmg) if dmg else "-", DAMAGE)], "row"))
        rows.append(([("EVENTS", HEAD)], "head"))
        rows.append(([("Turn", DIM), ("Attacker", DIM), ("Weapon", DIM),
                      ("Target", DIM), ("Shields", DIM), ("Damage", DIM)],
                     "cols"))
        turn = object()
        for ln in log.lines:
            shown_turn = str(ln["turn"]) if ln["turn"] != turn else ""
            turn = ln["turn"]
            note = ln["note"]
            if note in ("destroyed", "retreats", "captured", "repelled"):
                last = [(note, LOSS if note in ("destroyed", "captured")
                         else TEXT), ("", TEXT)]
            elif note == "missed":
                last = [("missed", DIM), ("", DIM)]
            else:
                last = [(str(ln["shields"]) if ln["shields"] else "-",
                         SHIELDS),
                        (str(ln["damage"]) if ln["damage"] else "-", DAMAGE)]
            rows.append(([(shown_turn, DIM),
                          (ln["src"] or "", owner_rgb(ln["src_owner"],
                                                      colours)),
                          (ln["what"], TEXT),
                          (ln["tgt"] or "", owner_rgb(ln["tgt_owner"],
                                                      colours)),
                          *last], "row"))
        return rows

    def draw(self, surface, style, scale, field, log, colours):
        """The window, centred in the field `field` (window px)."""
        if not self.open:
            return
        f = pygame.Rect(field)
        w, h = int(f.w * 0.72), int(f.h * 0.82)
        self.rect = r = pygame.Rect(f.centerx - w // 2,
                                    f.centery - h // 2, w, h)
        hud.popup(surface, r, scale)
        pad = max(6, int(14 * scale))
        size = max(12, int(17 * scale))
        line_h = int(size * 1.55)
        title = style.render_text("BATTLE LOG", int(size * 1.3), HEAD)
        surface.blit(title, (r.centerx - title.get_width() // 2, r.y + pad))
        bw, bh = int(120 * scale), int(30 * scale)
        self.close_rect = pygame.Rect(r.right - pad - bw, r.bottom - pad - bh,
                                      bw, bh)
        hud.small_button(surface, self.close_rect, scale, "normal", "CLOSE",
                         style_renderer=style)
        top = r.y + pad * 2 + title.get_height()
        bar_w = max(6, int(10 * scale))
        self.list_rect = lr = pygame.Rect(r.x + pad, top,
                                          r.w - 3 * pad - bar_w,
                                          self.close_rect.y - pad - top)
        rows = self._body(log, colours)
        self._rows = visible = max(1, lr.h // line_h)
        last_first = max(0, len(rows) - visible)
        if self.first is None:                  # opened: the newest lines
            self.first = last_first
        self.first = min(self.first, last_first)
        clip = surface.get_clip()
        surface.set_clip(lr)
        y = lr.y
        for cells, role in rows[self.first:self.first + visible]:
            if role == "head":
                hud.separator(surface, lr.x, lr.right, y + line_h - 2, scale)
            for n, (text, rgb) in enumerate(cells):
                if not text:
                    continue
                x0 = lr.x + int(lr.w * COLUMNS[n])
                x1 = lr.x + int(lr.w * COLUMNS[n + 1]) - pad // 2
                img = self._picture(style, text, size, rgb, x1 - x0,
                                    role != "head")
                right = n >= 4 and role != "head"
                surface.blit(img, (x1 - img.get_width() if right else x0,
                                   y + (line_h - img.get_height()) // 2))
            y += line_h
        surface.set_clip(clip)
        hud.scrollbar(surface, pygame.Rect(lr.right + pad, lr.y, bar_w, lr.h),
                      scale, self.first, visible, max(len(rows), 1))
