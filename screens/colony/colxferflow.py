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

THE QUESTION THE FORECAST MISSED: the forecast reads the owner race's room
alone, `Room_For_Another_` (settler.cpp:65-123) each race's with mixed
limits, so the engine may stop on "no room" (or an ETA) at a pop HD never
asked about (STLR stop DECLINED). The original asks at that very pop, so HD
asks then, off the outcome — the number sent so far in its text — and on
YES sends the colonists still in hand, as one walk; on NO the boxes are the
first command's, as after any NO. Only where the wire does not hold the rest
where the walk left them is the outcome shown as it stands.

DEVIATION `config_bound_send`: original = `Send_Cluster_` stops at its
first pop on "the last pop" or "25 in transit" and shows its box; HD = a
walk that only these stop is SENT, and the engine's STLR draws the box —
v2 reads both rules from its config (colony.allow_last_population_transfer,
settler.cpp:268; colony.max_pop_freighted, :289), which HD cannot read, so
a refusal off the defaults could refuse a move the engine makes
(`colxfer.engine_decides`). On the defaults the box is the same, one
snapshot later.
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
        self.moved = 0                  # settled by an earlier command
        self.asked = 0                  # the question kinds put to the player
        self._extra = False             # `extra_success_notice` so far
        self._earlier = None            # the outcome a late question stopped
        self._seq0 = None
        self._snapshots = 0
        self._sent_state = None
        self.rects = {}
        self._advance(state)

    # ── The steps ─────────────────────────────────────────────

    def _walk(self, state):
        return colxfer.walk(state, self.source, self.held, self.dest,
                            self.answers, self.job, self.plague, self.moved)

    def _advance(self, state):
        """The next question, or the command, or the boxes at once."""
        w = self._walk(state)
        if w.stop == settlewire.STOP_DECLINED and w.question is not None:
            self.phase, self.question = ASK, w.question
            return
        self.question = None
        self._send_or_show(state, w)

    def _send_or_show(self, state, w):
        self.forecast = w
        if (w.settled == 0 and not colxfer.engine_decides(w)) or \
                not self.connected:
            # nobody would go: the box the original shows at its first pop
            self._show(self._total(w))
            return
        out = settlewire.available(state) and state.settle_outcome
        self._seq0 = out["seq"] if out else None
        self._snapshots = 0
        self._sent_state = state
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
        self.asked |= self.question.needs
        earlier, self._earlier = self._earlier, None
        if yes:
            self.answers |= self.question.needs
            self._advance(state)
            return
        self.question = None
        if earlier is not None:
            # NO to a late question: the walk ended where the engine
            # stopped, the boxes are that command's
            self._show(earlier)
            return
        # NO: the walk stops at this pop (colmove.cpp:264, then the
        # declined lines) — sent if anyone before it goes
        self._send_or_show(state, self._walk(state))

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
            w = colxfer.from_outcome(out, self._basis(int(out["settled"])))
            if w.stop == settlewire.STOP_DECLINED and self._late(state, w):
                return
            self._show(self._total(w))
            return
        self._snapshots += int(bool(new_snapshot))
        if self._snapshots > carry.REFUSED_AFTER:
            self._fallback()

    def _basis(self, settled):
        """The forecast the outcome's arrays come from: the forecast where
        it settled as many, else its replay up to the engine's count."""
        f = self.forecast
        if f is not None and f.settled == settled:
            return f
        if self._sent_state is None:
            return None
        return colxfer.walk(self._sent_state, self.source, self.held,
                            self.dest, self.answers, self.job, self.plague,
                            self.moved, upto=settled)

    def _late(self, state, w):
        """A DECLINED outcome on a question never put to the player (the
        module docstring): asked now, the rest in hand. False when it was
        asked (a NO) or the rest cannot be found on the wire."""
        needs = colxfer.needs_of(w.result)
        if not needs or self.asked & needs:
            return False
        held = self.held
        if w.settled:
            rest = rest_at(state, self.source, w)
            if rest is None:
                log.info("transfer: a late question, but the rest is not "
                         "on the wire where the walk left it")
                return False
            held = rest[0]
        k = w.settled
        self.moved += k
        self._extra = self._extra or w.extra
        self.held = tuple(sorted(held))
        self.question = colxfer.question(w.result, self.moved,
                                         len(self.held))
        w.settled = self.moved
        self.outcome = self._earlier = w
        self.phase = ASK
        log.info("transfer: the engine stopped at a question HD did not "
                 "ask (%d sent): asked now", k)
        return True

    def _total(self, w):
        """`w` as the whole `Send_Cluster_`: with what earlier commands of
        this walk sent and the notice they set (`moved_count`,
        `extra_success_notice`, colmove.cpp:146-148)."""
        w.settled += self.moved
        w.extra = w.extra or self._extra
        return w

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
    from core import colonyfacts
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
            "source": colonyfacts.planet_name(src, planets, stars) or "",
            "dest": colonyfacts.planet_name(dst, planets, stars) or ""}


def rest_of(hand, state, w):
    """Whoever did not go, taken again off the wire at the indices the
    walk left them: (indices, words, n_pops), or None when nobody is left
    or the wire does not hold them there (the engine has put them back to
    their jobs either way)."""
    if hand is None or w is None:
        return None
    return rest_at(state, hand.colony, w)


def rest_at(state, colony, w):
    """`rest_of` for the colony `colony` the walk took them from."""
    rest = tuple(w.rest) if w.pops else ()
    raws = getattr(state, "colonies_raw", None) or []
    if not rest or not 0 <= colony < len(raws) or colony not in w.pops:
        return None
    rec = colony_struct.parse(raws[colony])
    words = list(rec.pop)[:rec.n_pops]
    _n, want = w.pops[colony]
    mask = ~colony_struct.POP_MASK_ASSIGNED
    if rec.n_pops != len(want) or any(
            i >= len(words) or (words[i] & mask) != (want[i] & mask)
            for i in rest):
        return None
    return rest, words, rec.n_pops
