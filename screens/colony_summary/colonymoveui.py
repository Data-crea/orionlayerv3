"""The HD side of a pop move: what is picked, and what is in flight.

Three modules meet here and the split between them is the point:

  `colonypick`   decides. Pure, reaches no client, cannot send.
  `colonysend`   drives the wire, one confirmed step at a time.
  this one       holds the state between two clicks, and is the only
                 place that turns the second click into a `Send`.

It lives beside the screen rather than in it for the reason
`colonyselect` does: the screen owns the boxes and hands the rect
over, and everything done with the rect is somebody else's subject.
That is also what makes the rules testable without a screen at all —
the smoke test drives this class with a fake client and asserts that
the cancel path and every refusal send NOTHING, which is the claim
section 3 of this phase rests on.

**THE FIRST CLICK IS LOCAL AND THE SECOND SENDS BOTH.** The reason is
in `colonypick`: a preview that created the game's own cluster would
strand a player who changed their mind, because both `Clear_Cluster_`
call sites on this screen are leave-the-screen paths
(colsum.cpp:804, :938). So `pick` only computes, and `Send` is
constructed at the drop, with both clicks in it.

**THE SELECTION MAY BE DISCARDED — HD EXTENSION.** Right click, or a
left click on neither an icon nor a drop band. Marked here, in
`colonypick`, in `layout.json` under `move`, in `v3_projektstatus.md`,
and in a smoke check.
"""
import logging

import pygame

from core import textfit

from . import colonylist
from . import colonypopup
from . import colonytrack
from . import colonymove
from . import colonypick
from . import colonysend

log = logging.getLogger("colony_summary.move")


def sort_hotkey(buttons, sort_key):
    """The key that re-sorts the game's list, or None.

    `colonysend` pushes it again once a move has landed, which is not
    housekeeping: HD re-sorts from every snapshot and the game
    re-sorts only when a sort field is activated
    (`Sort_Col_List_`, colsum.cpp:829-838), so a move under a
    production key leaves the two lists in different orders with
    every value on both screens still correct.

    None where the button has no usable letter — RETURN reports 0x25
    and the seven sort buttons all have one, so today this only
    answers None for a `layout.json` somebody has edited. The send
    then simply skips the step, which leaves the two lists to be
    re-bound by the next entry to the screen (`_push_sort_key`).
    """
    for spec in buttons:
        if spec.get("key") != sort_key:
            continue
        key = spec.get("hotkey")
        if isinstance(key, str) and len(key) == 1 and key.isascii():
            return ord(key)
        return None
    return None


class MoveController:
    """One pop move at a time, from the first click to the last word."""

    def __init__(self):
        #: The local selection. Never reaches the game.
        self.pick = None
        #: (row index, job) the pointer is over, or None. Cleared the
        #: moment a pick exists — see `hover`.
        self.over = None
        #: The wire sequence, or None. Exists only between the second
        #: click and its confirmation.
        self.send = None
        #: A REFUSAL's sentence, and nothing else. Empty is a state,
        #: not a placeholder. It is the guest in `planet_info` — the
        #: original's own description paragraph owns that panel and
        #: gets it back the moment this clears (decision 33 is why a
        #: refusal may take it at all: the original answers one with
        #: a blocking text box, textbox.cpp:149).
        self.message = ""
        #: **HD EXTENSION — the stranded notice.** The one state that
        #: is neither a refusal nor a result: the game is holding a
        #: cluster HD did not manage to place, and only the player
        #: can end it. It gets its OWN strip over the top of the list
        #: (`draw_notice`) and never the description panel, because
        #: it persists until the player acts and would sit on top of
        #: the paragraph for as long as it did. MOO2 shows nothing
        #: like it — its own answer is the blocking box — so it is
        #: marked here, in `layout.json` under
        #: `move._hd_extension_notice`, and in a smoke check.
        self.notice = ""
        self._plan = None
        self._size = 0

    @property
    def busy(self):
        return self.send is not None

    # ── Input ─────────────────────────────────────────────

    def click(self, *, rows, row_index, x, state, area, cfg, scale,
              sort_key, words, client, connected, sort_hotkey=None,
              n_colonies=None):
        """A left click on row `row_index`. True if it was taken.

        False means "this was not a click on the population track" —
        the screen then does whatever it does with a row click, which
        today is to swallow it.
        """
        if self.busy:
            return True          # a move is on the wire; ignore clicks
        if not 0 <= row_index < len(rows):
            return False
        row = rows[row_index]
        loaded = colonypick.pops_of(state, row["index"])
        if loaded is None:
            return False
        pops, n_pops, max_farms = loaded
        if self.pick is None:
            return self._first_click(row, row_index, pops, n_pops, x,
                                     area, cfg, scale, sort_key, words)
        return self._second_click(row, row_index, pops, n_pops, max_farms,
                                  x, area, cfg, scale, words, client,
                                  connected, sort_hotkey,
                                  n_colonies if n_colonies is not None
                                  else len(rows))

    def _first_click(self, row, row_index, pops, n_pops, x, area, cfg,
                     scale, sort_key, words):
        """Pick up — locally. Nothing is sent, whatever the answer."""
        cell = colonylist.cell_at_x(area, cfg, scale, row, x)
        if cell is None:
            return False         # a marker, a growth box, or bare track
        job, index = cell
        outcome = colonypick.pick_at(pops, n_pops, job, index,
                                     row["index"], row_index, sort_key)
        if isinstance(outcome, colonypick.Refusal):
            self.message = colonypick.message(words, outcome)
            return True
        self.pick = outcome
        self.message = ""
        self.notice = ""
        log.info("pop move: picked %r", outcome)
        return True

    def _second_click(self, row, row_index, pops, n_pops, max_farms, x,
                      area, cfg, scale, words, client, connected,
                      sort_hotkey, n_colonies):
        """Drop — and this is the only path that can inject."""
        job = colonylist.drop_band(area, cfg, scale, row, x)
        if job is None:
            if colonytrack.on_name(area, cfg, scale, row, x):
                # **THE NAME FIELD IS "PUT THEM BACK" — TRANSCRIBED.**
                # `_list_fields[i]` with a cluster held is
                # `Send_Cluster_(_list_col[i], -1)` (colsum.cpp:909),
                # and on the colony the cluster came from that takes
                # the re-flag branch: `requested_job == -1` sets
                # `0x200` back and consults no rule
                # (colmove.cpp:161-165). The array ends exactly as it
                # started.
                #
                # So nothing goes on the wire, and that is the
                # transcription rather than a shortcut: our selection
                # was never the game's cluster (decision 47), so
                # releasing it reproduces the original's OUTCOME with
                # no injection at all. Injecting the pair would
                # create the cluster in the game only to release it,
                # which is strictly more that can go wrong for a
                # gesture whose whole content is "nothing happened".
                self.cancel("dropped on the colony name")
                return True
            self.cancel("dropped outside every target")
            return True
        if job == self.pick.job:
            # THE HELD POP'S OWN GROUP. Discard and send nothing.
            #
            # It matches the original's OUTCOME rather than diverging
            # from it: `Send_Cluster_` with the job the pops already
            # hold takes the re-flag path (colmove.cpp:165), sets
            # 0x200 back and consults no rule, so the array ends up
            # exactly as it started and the cluster is released. Ours
            # ends up the same way with nothing on the wire, because
            # our selection was never the game's cluster.
            #
            # Holding the selection instead would be the deviation:
            # the original ends the gesture here, so keeping it would
            # leave HD in a state the original cannot be in. The only
            # thing to mark is that nothing is sent.
            self.cancel("dropped on the group it came from")
            return True
        outcome = colonypick.plan_move(self.pick, pops, n_pops, max_farms,
                                       row["index"], job)
        if isinstance(outcome, colonypick.Refusal):
            self.message = colonypick.message(words, outcome)
            return True
        if not connected:
            self.message = words.get("offline", "")
            return True
        # `row_index` and not the pick's own position: the drop has to
        # be on the same colony, so this is where that colony sits
        # NOW, which is the number `GameWindow` turns into a slot.
        predicted = colonymove.predict_pops(pops, n_pops, max_farms,
                                            self.pick.cluster, job)
        self._plan, self._size = outcome, self.pick.size
        self.message = ""
        self.notice = ""
        # ONE COMMAND, ADDRESSED BY COLONY (fundament 52). The row's
        # position, the game's ten-row window and the sort key were
        # all arguments to a click chain that named a SLOT; a command
        # names the colony, so none of them is an input any more.
        self.send = colonysend.Send(
            client, colony=self.pick.colony, target_job=job,
            cluster=self.pick.cluster, predicted=predicted)
        log.info("pop move: %r -> column %d, %r", self.pick, job, outcome)
        return True

    def hover(self, rows, row_index, x, area, cfg, scale):
        """Remember which job group the pointer is over, or nothing.

        **Nothing while a selection is held**, which is the popup's
        own rule and is enforced here rather than at the draw so a
        reader cannot find a second answer: aiming happens on the
        hovered row, and a popup that followed the pointer would
        flicker under the gesture it interrupts.
        """
        if self.pick is not None or self.busy:
            self.over = None
            return
        if row_index is None or not 0 <= row_index < len(rows):
            self.over = None
            return
        job = colonylist.drop_band(area, cfg, scale, rows[row_index], x)
        self.over = None if job is None else (row_index, job)

    def draw_popup(self, surface, rows, first, area, cfg, scale, style,
                   layout, data):
        """The hover popup, or nothing. Returns its rect or None.

        It takes `data` rather than the wording, because which block
        of `layout.json` the words come from is this class's business
        and not the screen's — the screen owns the boxes.
        """
        if self.over is None or self.pick is not None:
            return None
        row_index, job = self.over
        bands = colonylist.row_bands(area, cfg, scale, len(rows) - first)
        band = row_index - first
        if not 0 <= band < len(bands):
            return None
        words = data.get("popup", {})
        return colonypopup.draw(surface, area, cfg, scale,
                                rows[row_index], job, bands[band],
                                style, layout.font_size(
                                    words.get("font", 15)), words)

    def cancel(self, why):
        """Discard the selection — **HD EXTENSION**, see the module
        docstring. Nothing was injected, so there is nothing to undo
        on the other side of the wire."""
        if self.pick is None:
            return
        log.info("pop move: selection discarded (%s)", why)
        self.pick = None
        self.message = ""

    # ── The wire ──────────────────────────────────────────

    def advance(self, state, words):
        """Drive a move in flight, one step per frame.

        The chain waits for EFFECTS and not for messages — the reason
        is in `colonysend`: the first snapshot after a send is
        serialized in the very tick that consumed it.
        """
        if self.send is None:
            return
        self.send.update(state)
        if not self.send.finished:
            return
        if self.send.state == colonysend.DONE:
            # NOTHING. A move that worked is reported by the row —
            # see `colonypick.message`, which returns "" for a
            # success and why.
            self.message = colonypick.message(words, self._plan, self._size)
        elif self.send.holding:
            # NOT a message, and NOT in the description panel: the
            # game has a cluster in hand, which is a state only the
            # player can end, so it gets its own strip over the list.
            # See `notice` and `draw_notice`.
            self.notice = words.get("stranded", "")
        else:
            self.message = words.get(self.send.reason,
                                     self.send.reason or "")
        log.info("pop move finished: %s (%s)", self.send.state,
                 self.send.reason)
        self.send = None
        self.pick = None

    # ── The drawing ───────────────────────────────────────

    def draw_message(self, surface, rect, px, style, color):
        """The last word, wrapped and centred in the rect it is given.

        The screen owns the box; what goes in it is this class's, so
        that "was anything said?" is one question with one answer.

        **It wraps and shrinks, and that is not decoration.** Drawn
        as one line at 18 px the longest of these sentences — a rule
        plus its count, "This job is full — only 2 of 12 would move,
        10 would stay" — is wider than `spare_panel` and lost its
        first and last characters under the frame's metal rim. Only
        the PNG showed it: every value was right and the text was
        drawn, and a check that asked "did it draw ink?" would have
        passed. That is decision 44's class A rule, met from a new
        direction, so the fitting is `core.textfit`'s — measured by
        rendering, shrunk until BOTH dimensions fit, never truncated.

        The rect is inset by one line's width on each side rather
        than used to its edges: `spare_panel` is a frame CUTOUT, and
        `frame_holes.to_ref` bleeds it two reference px outward on
        every side so panel fills cover the anti-aliased rim, with
        the artwork reaching further in still.
        """
        if not self.message:
            return
        inset = max(2, px // 2)
        room = max(1, rect.w - 2 * inset)
        sizes = [px - step for step in range(0, max(1, px - 9))]
        lines, _size = textfit.squeeze_lines(
            style, self.message, room, rect.h - 2 * inset, sizes, color)
        height = sum(s.get_height() for s in lines)
        y = rect.y + (rect.h - height) // 2
        for surf in lines:
            surface.blit(surf, (rect.x + (rect.w - surf.get_width()) // 2, y))
            y += surf.get_height()

    def draw_notice(self, surface, area, cfg, px, style, color, fill):
        """The stranded notice, on a strip across the top of the list.

        **HD EXTENSION — marked in `__init__`, in `layout.json` under
        `move._hd_extension_notice`, and in a smoke check.** MOO2 has
        no such strip. Its answer to a cluster it is holding is
        `GENDRAW::Help_` -> `TEXTBOX::Do_Text_Box_`, a modal that sits
        in `do { … } while (fields::Get_Input_() == 0)`
        (textbox.cpp:149) until something clicks or types. HD must not
        reproduce that — it refuses before sending precisely so the
        player is never trapped — but the state itself is real and
        only the player can end it, so it has to be said somewhere.

        **NOT IN `planet_info`, AND THAT IS THE WHOLE REASON THIS
        FUNCTION EXISTS.** That panel is the left half of the
        original's own scan box, the description paragraph at native
        (13, 354, 80, 88) (`Draw_Colony_Scan_Info_`, colsum.cpp:1155).
        A refusal may borrow it because a refusal is transient and
        `_render_info` draws the paragraph back on the next frame.
        This notice is not transient: it stands until the player
        presses RETURN, so putting it there would evict a
        transcription for an unbounded time.

        THE TOP BAND IS THE PLACE, and it costs the least true thing
        on screen. While the game holds a cluster the list is not
        actionable — every further drop compounds the mismatch — so a
        strip over the first row hides a row the player must not use
        anyway, and it is where the eye already is. It is drawn over
        the rows and under the frame, like the hover popup, so it
        cannot spill outside the cutout.
        """
        if not self.notice:
            return
        band = colonytrack.band_height(area, cfg)
        strip = pygame.Rect(area.x, area.y, area.width, band)
        surface.fill(fill[:3], strip)
        inset = max(2, px // 2)
        sizes = [px - step for step in range(0, max(1, px - 9))]
        lines, _size = textfit.squeeze_lines(
            style, self.notice, max(1, strip.w - 2 * inset),
            strip.h - 2 * inset, sizes, color)
        y = strip.y + (strip.h - sum(s.get_height() for s in lines)) // 2
        for surf in lines:
            surface.blit(surf,
                         (strip.x + (strip.w - surf.get_width()) // 2, y))
            y += surf.get_height()

    def draw(self, surface, rows, first, area, cfg, scale, style=None,
             layout=None, data=None):
        """The hover popup, and NOTHING ELSE ON THE ROW.

        **BOTH MARKS ARE GONE — 8 September 2026.** An outline round
        the cells a pick would take, and a frame round the three drop
        targets while one was held. The original marks neither: the
        only drawing `colsum.cpp` does outside its fields and its
        paragraphs is the scroll thumb (colsum.cpp:759-765), and what
        it does instead is take the held pops OUT of the row
        (`0x200`, coldraw.cpp:336) and hang them on the pointer
        (`Draw_Cluster_`, colmove.cpp:7-37). Both are now transcribed
        — `colonyrows.build_rows` does the first and
        `colonylist.draw_held_cluster` the second — so the marks were
        a third statement of a thing the picture already said twice.

        The held cluster is NOT drawn from here. It sits at the
        POINTER and over everything, which is where the original puts
        it (after `Draw_Visible_Fields_`, colsum.cpp:506-511), so the
        screen draws it last rather than inside this layer.
        """
        if style is not None:
            self.draw_popup(surface, rows, first, area, cfg, scale,
                            style, layout, data)

    def draw_held(self, surface, rows, pointer, figures, step, y=None):
        """The pops in hand, on the pointer. Nothing when none is.

        The screen decides WHEN — last, over the frame, which is
        where the original draws it (colsum.cpp:506-511) — and this
        decides WHAT, because the held cluster is this class's state.
        The offsets and the step are `colonylist`'s and
        `zoomtables`'.

        `y` is a CALLABLE taking one sprite's last inked row, not a
        number: the figures are anchored by their ink and a cluster
        can hold two races whose ink ends on different rows. See
        `colonytrack.figure_origin_y`.
        """
        if self.pick is None:
            return
        row = next((r for r in rows
                    if r["index"] == self.pick.colony), None)
        if row is None:
            return
        colonylist.draw_held_cluster(surface, pointer, figures,
                                     row.get("held") or (), step, y)

    def held(self):
        """(colony index, held pop indices), or None.

        What `build_rows` needs to clear `0x200` on, which is the
        whole of how a held cluster leaves the row. It survives into
        the send: the game takes the pops at the first injected
        click, so a row that put them back while the wire was working
        would be showing a state neither side is in.
        """
        if self.pick is None:
            return None
        return (self.pick.colony, self.pick.cluster.indices)


def render_for(screen, surface, text_color, fill_color):
    """Everything the move draws, in the order it is drawn.

    Moved out of `ColonySummaryScreen._render_move` on 9 September
    2026, when the stranded notice made it three layers. The screen
    owns the boxes and hands them over; what is done with them is
    this module's — the same seam `colonyoutput.render_for` and
    `colonyheader.render_for` already take on this screen.

    THREE LAYERS, AND WHERE EACH GOES:

    - the hover popup, over the rows and under the frame image, which
      is why it has to stay inside the cutout (see `colonypopup`);
    - the stranded notice, on its own strip across the top band —
      **never `planet_info`**, see `draw_notice`;
    - a REFUSAL's sentence in `planet_info`.

    **THE PANEL IS SHARED, AND THE SENTENCE IS THE GUEST.** This used
    to argue that `planet_info` owes nothing to the original and is
    therefore free. That stopped being true on 8 September 2026: the
    panel is the left half of the original's own scan box, the
    description paragraph at native (13, 354, 80, 88). A refusal
    still wins it while there is one — the original answers a refusal
    with `GENDRAW::Help_`, a BLOCKING message box over the whole
    screen (textbox.cpp:149) that HD must not reproduce because it
    refuses BEFORE sending — but it is transient, and
    `_render_info` draws the paragraph back the moment it clears.

    **A MOVE THAT WORKED PUTS NOTHING HERE AT ALL** since 9 September
    2026; see `colonypick.message`. The row is the feedback, which is
    what the original does.

    **AND THE MARKS ON THE ROW ARE GONE**; see `MoveController.draw`.
    """
    move = screen._move
    words = screen._move_words()
    px = screen.layout.font_size(words.get("font", 18))
    area, cfg, scale, _n = screen._list_view()
    if screen.box_rect("list_area"):
        move.draw(surface, screen._rows, screen._first, area, cfg,
                  scale, screen.style, screen.layout, screen._data)
        move.draw_notice(surface, area, cfg, px, screen.style,
                         text_color, fill_color)
    box = screen.box_rect("planet_info")
    if move.message and box:
        move.draw_message(surface, pygame.Rect(*screen.layout.rect(box)),
                          px, screen.style, text_color)
