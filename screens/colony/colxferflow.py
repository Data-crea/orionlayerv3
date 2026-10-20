"""One settlement to another colony, from the drop to the last box — work
order 316 (open fix 103), shared by the colony screen and the Colonies list.

THE ORIGINAL runs it all inside `Send_Cluster_` (colmove.cpp:145-531): the
questions where a pop needs them (E 0x209, 0x205 / 0x203, 0x206 / 0x204 in
`Do_Confirmation_Box_`), the "Settlers Failed." text box at the pop it stops
on, then "Settlers Depart" when any went — or `Give_Colonist_New_Job_`'s
refusal box and nothing after it (:279-286). Every one blocks until the
player answers.

HD (TRANSCRIPTION `transfer_boxes`): the same boxes in the same order, in
HD's message box (`core.msgbox.draw`, DEVIATION `hud_message_box`: the HUD
look, CLOSE on a text box), but the questions come BEFORE the command
(fundament 52: a command cannot ask) — asked off `colxfer.walk`'s forecast,
each in the order the walk meets it, and the command carries the answers;
the boxes after it are drawn from what the engine did (STLR,
`core.settlewire`), never from the forecast. A walk that can move nobody is
not sent: its box is shown at once (decision 33), as the original's loop
shows it at its first pop. What waits on the wire waits on STLR's sequence;
no new sequence within `carry.REFUSED_AFTER` snapshots is the original's
fallback, E 0xE4 in a help box.
"""
import logging

import pygame

from core import carry, msgbox, settlewire
from core.structs import colony as colony_struct

from . import colxfer

log = logging.getLogger("colony.transfer")

ASK, SENDING, BOXES, DONE = "ask", "sending", "boxes", "done"


class Flow:
    """`start` -> questions -> (send, wait) -> boxes -> `done`."""

    def __init__(self, strings, client, state, source, held, dest, job=-1,
                 names=None, plague=None, connected=True):
        self.strings = strings
        self.client = client
        self.source, self.dest, self.job = source, dest, job
        self.held = tuple(sorted(held))
        self.names = names or {}        # "noun", "source", "dest"
        self.plague = plague
        self.connected = connected
        self.answers = 0
        self.phase = ASK
        self.question = None
        self.forecast = None
        self.outcome = None             # the Walk the boxes are drawn from
        self.boxes = []                 # [{"kind", "title", "text"}]
        self.sent = False
        self._seq0 = None
        self._snapshots = 0
        self.rects = {}
        self._advance(state)

    # ── The steps ─────────────────────────────────────────────

    def _walk(self, state):
        return colxfer.walk(state, self.source, self.held, self.dest,
                            self.answers, self.job, self.plague)

    def _advance(self, state):
        """The next question, or the command, or the boxes at once."""
        w = self._walk(state)
        if w.stop == settlewire.STOP_DECLINED and w.question is not None:
            self.phase, self.question = ASK, w.question
            return
        self.question, self.forecast = None, w
        if w.settled == 0 or not self.connected:
            # nobody would go: the box the original shows at its first pop
            self._show(w)
            return
        out = settlewire.available(state) and state.settle_outcome
        self._seq0 = out["seq"] if out else None
        self.client.settle_pops(self.source, self.dest, list(self.held),
                                answers=self.answers, job=self.job)
        self.sent = True
        self.phase = SENDING
        log.info("transfer: %d of colony %d -> colony %d (answers %d, job "
                 "%d), %d forecast", len(self.held), self.source, self.dest,
                 self.answers, self.job, w.settled)

    def answer(self, state, yes):
        """The player's answer to the question on screen."""
        if self.phase != ASK or self.question is None:
            return
        if yes:
            self.answers |= self.question.needs
            self._advance(state)
            return
        # NO: the walk stops at this pop (colmove.cpp:264, then the
        # declined lines) — sent if anyone before it goes
        self.question = None
        w = self._walk(state)
        self.forecast = w
        if w.settled == 0 or not self.connected:
            self._show(w)
            return
        out = settlewire.available(state) and state.settle_outcome
        self._seq0 = out["seq"] if out else None
        self.client.settle_pops(self.source, self.dest, list(self.held),
                                answers=self.answers, job=self.job)
        self.sent = True
        self.phase = SENDING

    def update(self, state, new_snapshot):
        """While the command is on the wire: its outcome, or the bound."""
        if self.phase != SENDING:
            return
        out = getattr(state, "settle_outcome", None)
        if out is not None and out["seq"] != self._seq0 and \
                out["source"] == self.source and out["dest"] == self.dest:
            if out["stop"] == settlewire.STOP_LIST:
                self._fallback()
                return
            self._show(colxfer.from_outcome(out, self.forecast))
            return
        self._snapshots += int(bool(new_snapshot))
        if self._snapshots > carry.REFUSED_AFTER:
            self._fallback()

    def _fallback(self):
        w = colxfer.Walk()
        w.stop = settlewire.STOP_LIST
        self.outcome = w
        self.boxes = [self._box("message", None, colxfer.cfmt(
            self.strings.string(colxfer.E_UNSPECIFIED)))]
        self.phase = BOXES

    def _show(self, w):
        """The boxes after the walk, in the original's order."""
        self.outcome = w
        boxes = []
        if w.stop == settlewire.STOP_JOB:
            # `Give_Colonist_New_Job_`'s box, then `return` — no notice
            boxes.append(self._box("message", None,
                                   colxfer.job_refusal_text(
                                       self.strings, w.job_refusal)))
        else:
            if w.stop in (settlewire.STOP_REFUSED, settlewire.STOP_DECLINED):
                text = colxfer.failed_text(self.strings, w)
                boxes.append(
                    self._box("text", self.strings.string(
                        colxfer.E_FAILED_TITLE), text) if text is not None
                    else self._box("message", None, colxfer.cfmt(
                        self.strings.string(colxfer.E_UNSPECIFIED))))
            if w.settled > 0:
                boxes.append(self._box("text", self.strings.string(
                    colxfer.E_DEPART_TITLE), colxfer.depart_text(
                        self.strings, w, self.names.get("noun", ""),
                        self.names.get("source", ""),
                        self.names.get("dest", ""))))
        self.boxes = boxes
        self.phase = BOXES if boxes else DONE

    @staticmethod
    def _box(kind, title, text):
        return {"kind": kind, "title": (title or "").strip(),
                "text": text or ""}

    # ── What is on screen, and the answers to it ───────────────

    @property
    def done(self):
        return self.phase == DONE

    @property
    def busy(self):
        return self.phase != DONE

    def box(self):
        """The box on screen now, or None (also while sending)."""
        if self.phase == ASK and self.question is not None:
            return self._box("confirmation", None, colxfer.question_text(
                self.strings, self.question))
        if self.phase == BOXES and self.boxes:
            return self.boxes[0]
        return None

    def render(self, surface, style, labels):
        box = self.box()
        self.rects = {}
        if box is None:
            return None
        shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shade.fill((0, 0, 0, msgbox.DIM_ALPHA))
        surface.blit(shade, (0, 0))
        panel, self.rects = msgbox.draw(surface, style, labels, box)
        return panel

    def click(self, state, x, y):
        """A left click while a box is up: True when it was the flow's."""
        box = self.box()
        if box is None:
            return self.phase == SENDING      # nothing else while waiting
        hit = next((k for k, r in self.rects.items()
                    if r.collidepoint(x, y)), None)
        if box["kind"] == "confirmation":
            if hit in ("yes", "no"):
                self.answer(state, hit == "yes")
            return True
        self._close()                          # a text box: anywhere
        return True

    def key(self, state, event_key, unicode=""):
        box = self.box()
        if box is None:
            return self.phase == SENDING
        ch = (unicode or "").lower()
        if box["kind"] == "confirmation":
            if ch in ("y", "n"):
                self.answer(state, ch == "y")
            return True
        if event_key in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_SPACE,
                         pygame.K_KP_ENTER):
            self._close()
        return True

    def _close(self):
        if self.boxes:
            self.boxes.pop(0)
        if not self.boxes:
            self.phase = DONE


def names(state, strings, source, dest, held):
    """The notice's noun (the first colonist in hand, `Colony_Pop_String_`
    at colmove.cpp:175) and the two planets' names (`HACCESS::
    Get_Planet_Name_`, :484-491)."""
    from screens.colony_summary import colonyrows
    raws = getattr(state, "colonies_raw", None) or []
    planets = getattr(state, "planets_raw", None) or []
    stars = getattr(state, "stars", None) or []
    if not (0 <= source < len(raws) and 0 <= dest < len(raws)):
        return {}
    src = colony_struct.parse(raws[source])
    dst = colony_struct.parse(raws[dest])
    first = min(held) if held else 0
    word = src.pop[first] if first < src.n_pops else 0
    return {"noun": colxfer.pop_noun(strings, word,
                                     getattr(state, "player_raw", None) or [],
                                     src.owner),
            "source": colonyrows.planet_name(src, planets, stars) or "",
            "dest": colonyrows.planet_name(dst, planets, stars) or ""}


def rest_of(hand, state, w):
    """Whoever did not go, taken again off the wire at the indices the
    walk left them: (indices, words, n_pops), or None when nobody is left
    or the wire does not hold them there (the engine has put them back to
    their jobs either way)."""
    if hand is None or w is None:
        return None
    rest = tuple(w.rest) if w.pops else ()
    raws = getattr(state, "colonies_raw", None) or []
    if not rest or not 0 <= hand.colony < len(raws):
        return None
    rec = colony_struct.parse(raws[hand.colony])
    words = list(rec.pop)[:rec.n_pops]
    _n, want = w.pops[hand.colony]
    mask = ~colony_struct.POP_MASK_ASSIGNED
    if rec.n_pops != len(want) or any(
            i >= len(words) or (words[i] & mask) != (want[i] & mask)
            for i in rest):
        return None
    return rest, words, rec.n_pops
