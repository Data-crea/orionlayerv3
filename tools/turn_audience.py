#!/usr/bin/env python3
"""End turns on a scratch save until a computer player asks for an audience — work order 187, part 5.

    python tools/turn_audience.py SLOT [--turns N]      # SLOT 4 or 5, N <= 30

Data allowed it for this order (187 part 5): in SAVE4/SAVE5 only, in memory,
never saved, game decisions that stop the turn taken with a default choice,
turns ended until an AI's audience (id 58) appears, at most 30 per save,
every decision listed.

EVERY SEND IS DECIDED FROM THE LIST READ AT THAT MOMENT (fundament 08, "A
live driver is a client"), through `tools/livesend.py`; a prompt it cannot
identify stops the run with its shape recorded — nothing is guessed. What it
answers, and how:

    the galaxy map, idle      TURN (the HD map's own button, a player's click)
    a message box             its one full-screen field (activate)
    a CLOSE / OK button       the list's only type-0 button with ESC as its
                              hotkey (reports, the turn summary)
    the colony screen         its own RETURN button (the game opens a new
                              colony's screen after a landing; never CRUNCH,
                              TOGGLE or field [0])
    the colony-base choice    the next planet the game has not refused this
                              turn (the Malus prompt of 186) — a DEFAULT
                              decision; when every planet is refused, CLOSE,
                              and its "trash the colony base?" gets YES — the
                              only answer that lets the turn go on
    a Yes / No box            YES only right after that planet choice ("Build
                              colony on <planet> with …", the decision's own
                              confirmation); every other Yes / No gets NO,
                              which leaves the game as it was (a "Really trash
                              your colony base?" is never confirmed)
    the research selection    the first choice row, by an injected click (53)
    the race picks            ACCEPT with none taken (a research's reward)
    a leader's offer          REJECT (hotkey R beside HIRE's H) — nothing changes
    a combat choice (id 12)   recorded, then CLOSE if the box offers it —
                              the engine then resolves the battle itself
    the audience (57/58)      its statement's one field; in a menu ONLY an item
                              that changes nothing (cancel / good bye / no /
                              reject) — never yes / accept / agree / declare

Each decision goes to `decisions.json` in the evidence folder with the turn,
the stardate, the screen and the list's shape. SAVE10 (the autosave every
TURN writes) and MOX.SET are restored by the caller from the guard taken
before the engine existed.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault("ORIONLAYER_FRAME_TRACE", "1")
os.environ.setdefault("ORIONLAYER_INPUT_LOG", "1")
os.environ.setdefault("ORIONLAYER_EVIDENCE_FOLDER", "work_order_187")

import vdisplay  # noqa: E402
vdisplay.headless_clients()

import pygame  # noqa: E402

import flash_walk  # noqa: E402
import livesend  # noqa: E402
from core import modalnet  # noqa: E402

SAFE = ("cancel", "good bye", "goodbye", "reject", "no")
NEVER = ("yes", "accept", "agree", "declare", "surrender", "give", "demand")
FULL = (0, 0, 639, 479)
MAX_TURNS = 30


def live(st):
    """The answerable fields: not the dummy, not parked off-screen (5000)."""
    return [f for f in (st.fields or []) if f.index != 0 and f.x < 5000]


def rect(f):
    return (f.x, f.y, f.x_end, f.y_end)


class TurnWalk(flash_walk.Walk):

    def __init__(self, slot):
        super().__init__((1920, 1080), f"P5_turns_save{slot}")
        self.slot = slot
        self.decisions = []
        self.turn = 0
        self.base_tried = {}

    def log(self, what, **kw):
        st = self.st
        entry = {"turn": self.turn, "stardate": st.stardate,
                 "screen": st.current_screen, "what": what,
                 "shape": modalnet.signature(st.fields), **kw}
        self.decisions.append(entry)
        print(f"  t{self.turn:02d} {st.stardate} screen {st.current_screen}: {what} {kw or ''}")

    def act(self, f, label):
        livesend.activate(self.app.client, f.index,
                          screen=self.st.current_screen,
                          field_type=f.field_type, rect=rect(f), label=label)
        self.settle(12)

    # ── the prompts it knows ────────────────────────────────────────
    def audience(self):
        from screens.audience import auwire
        from screens.leaders import ldrdraw as nd
        self.settle(45)          # the original's fade-in, for its frame
        self.run.capture(f"audience_t{self.turn:02d}_{len(self.decisions)}")
        v = self.hd("audience")._view
        if v is None:
            return False
        if v.state == auwire.STATEMENT:
            if self.st.current_screen not in (57, 58):
                return True               # it ended meanwhile: nothing sent
            self.log("audience: statement clicked away",
                     text=(self.st.audience or {}).get("text"))
            self.click(self.app.win_w // 2, self.app.win_h // 2)
            self.settle(20)
            return True
        if v.state == auwire.MENU:
            items = [(it, f) for it, f in v.items()]
            pick = next(((it, f) for it, f in items if it["enabled"]
                         and any(it["text"].strip().lower().startswith(k) for k in SAFE)
                         and not any(k in it["text"].lower() for k in NEVER)), None)
            if pick is None:
                self.log("audience: menu without a safe item — NOTHING SENT",
                         items=[it["text"] for it, _ in items])
                return False
            r = nd.rect(self.hd("audience").layout, rect(pick[1]))
            self.log("audience: answered", item=pick[0]["text"].strip(),
                     title=(self.st.audience or {}).get("title"))
            self.click(r.centerx, r.centery)
            self.settle(20)
            return True
        self.log("audience: a list HD has no view for — NOTHING SENT")
        return False

    def respond(self):
        """One step on whatever the game shows now. False = stop."""
        st = self.st
        fields = live(st)
        if st.current_screen in (57, 58) and st.audience:
            return self.audience()
        if livesend.on_galaxy_map(st):
            return None                      # idle: the caller ends the turn
        full = [f for f in fields if rect(f) == FULL]
        if len(fields) == 1 and full:
            self.log("message box: its full-screen field")
            self.act(full[0], "message box")
            return True
        yes = [f for f in fields if f.hotkey == ord("Y")]
        no = [f for f in fields if f.hotkey == ord("N")]
        if len(fields) == 2 and len(yes) == 1 and len(no) == 1:
            last = self.decisions[-1]["what"] if self.decisions else ""
            after_base = last.startswith("colony-base choice")
            pick = yes[0] if after_base else no[0]
            self.run.capture(f"yesno_t{self.turn:02d}_{len(self.decisions)}")
            self.log("Yes/No box: " + (
                ("YES — scrap the colony base every planet refused (DEFAULT, "
                 "the only way the turn goes on)" if "CLOSE" in last else
                 "YES — the colony base's own confirmation (DEFAULT)")
                if after_base else "NO (leaves the game as it was)"))
            self.act(pick, "yes/no")
            return True
        # choice rows: a category column's width (217/218), not its 33-px
        # header — 14 px rows, or one 81-px panel once a field is exhausted
        # ("Hyper-advanced …", seen in SAVE4 at turn 14)
        rows = [f for f in fields if f.field_type == 7 and
                f.x_end - f.x in (217, 218) and f.y_end - f.y != 33]
        if st.current_screen == 53 and rows:
            # The research selection after a project completed: the first
            # choice row, by an injected click on its centre (pointer and
            # field agree — open fix 23's crash was a pointer over none).
            r = sorted(rows, key=lambda f: (f.x, f.y))[0]
            self.run.capture(f"research_t{self.turn:02d}")
            self.log("research selection: the first row (DEFAULT)", at=rect(r))
            livesend.click(self.app.client, (r.x + r.x_end) // 2, (r.y + r.y_end) // 2,
                           screen=53, field_type=7, label="research row")
            self.settle(12)
            return True
        accept = [f for f in fields if f.field_type == 0 and
                  (f.x, f.y, f.x_end, f.y_end) == (506, 448, 572, 468)]
        if st.current_screen == 0 and len(accept) == 1 and \
                len([f for f in fields if f.field_type == 0]) == 1:
            # The race picks after a completed research (PICKS / ACCEPT, the
            # Custom Race grid): ACCEPT with no pick — the race unchanged.
            self.run.capture(f"picks_t{self.turn:02d}")
            self.log("race picks: ACCEPT with none taken (DEFAULT, race unchanged)")
            self.act(accept[0], "picks ACCEPT")
            return True
        rej = [f for f in fields if f.field_type == 0 and f.hotkey == ord("R")]
        hire = [f for f in fields if f.field_type == 0 and f.hotkey == ord("H")]
        if len(rej) == 1 and len(hire) == 1:
            # A leader offers to join (REJECT / HIRE): REJECT changes nothing.
            self.run.capture(f"leader_t{self.turn:02d}")
            self.log("a leader's offer: REJECT (DEFAULT, changes nothing)")
            self.act(rej[0], "leader REJECT")
            return True
        if st.current_screen == 1:
            # The game opens a new colony's screen after a landing: left by
            # its own RETURN button (never CRUNCH, TOGGLE or field [0]).
            from screens.colony import colgeom, colwire
            ret = colwire.live_field(st.fields, colgeom.RETURN)
            if ret is not None:
                self.log("the colony screen (a new colony): RETURN")
                self.act(ret, "colony RETURN")
                return True
        closes = [f for f in fields if f.field_type == 0 and f.hotkey == 27]
        grid = [f for f in fields if f.field_type == 12]
        planets = [f for f in fields if f.field_type == 7
                   and (f.x_end - f.x) <= 30 and (f.y_end - f.y) <= 30]
        if st.current_screen == 0 and grid and planets and closes:
            tried = self.base_tried.setdefault(self.turn, set())
            left = [f for f in sorted(planets, key=lambda f: f.index)
                    if rect(f) not in tried]
            self.run.capture(f"colony_base_t{self.turn:02d}")
            if left:
                p = left[0]
                tried.add(rect(p))
                self.log("colony-base choice: the next planet not yet refused "
                         "(DEFAULT)", planet_field=p.index, at=rect(p))
                self.act(p, "colony base planet")
                return True
            self.log("colony-base choice: every planet refused — CLOSE")
            self.act(closes[0], "colony base CLOSE")
            return True
        if st.current_screen == 12 and not fields:
            return True                      # its list is not built yet
        if st.current_screen == 12:
            self.run.capture(f"combat_t{self.turn:02d}_{len(self.decisions)}")
            if len(closes) == 1:
                self.log("combat choice: CLOSE (the engine resolves)")
                self.act(closes[0], "combat CLOSE")
                return True
            self.log("combat: a list without one CLOSE — NOTHING SENT")
            return False
        if len(closes) == 1:
            # The one button whose hotkey is ESC: the way out that changes
            # nothing (the turn summary's CLOSE, a report's).
            self.log("a report / summary: its CLOSE")
            self.act(closes[0], "CLOSE")
            return True
        if not fields:
            return True                      # a transition: wait
        self.log("a prompt it does not know — NOTHING SENT, run stops")
        self.run.capture(f"unknown_t{self.turn:02d}")
        return False

    def play(self, turns):
        gm = self.hd("galaxy_map")
        for self.turn in range(1, turns + 1):
            date = self.st.stardate
            assert livesend.on_galaxy_map(self.st), "not on the map"
            self.log("TURN")
            self.click_rect(gm.nav_rect("turn"))
            t0, idle = time.monotonic(), 0
            while time.monotonic() - t0 < 180:
                self.frame()
                if self.st.current_screen in (57, 58) and self.st.audience:
                    if self.st.current_screen == 58:
                        self.log("58 REACHED")
                        self.reached = True
                r = self.respond()
                if r is False:
                    return "stopped"
                if r is None:
                    idle += 1
                    if self.st.stardate != date and idle > 40:
                        break
                else:
                    idle = 0
            else:
                self.log("the turn did not come back within 180 s")
                return "timeout"
            if getattr(self, "reached", False):
                return "58 reached"
        return f"{turns} turns, no 58"


def main(argv):
    from livedrive import close, hashes
    args = [a for a in argv if not a.startswith("--")]
    slot = int(args[0]) if args else 4
    assert slot in (4, 5), "SAVE4 or SAVE5 only"
    turns = next((int(a.split("=", 1)[1]) for a in argv if a.startswith("--turns=")), MAX_TURNS)
    assert 1 <= turns <= MAX_TURNS
    flash_walk.SLOT = slot
    saves = hashes()
    w = TurnWalk(slot)
    w.run.wait_for(lambda st: st.current_screen >= 0, seconds=30, label="first")
    w.settle(40)
    assert w.st.current_screen == 10, "not at the main menu — nothing sent"
    assert w.load(), "the load did not arrive"
    w.settle(30)
    result = w.play(turns)
    print(f"  SAVE{slot}: {result}")
    # Every frame that showed the game's picture, and every 58 frame: the
    # proof that the audience, and the way into it and out of it, drew HD.
    from collections import Counter
    frames = list(w.app._frame_trace.frames)
    nets = Counter((f["screen"], f["kind"]) for f in frames if f["source"] == "net")
    at58 = Counter(f["source"] for f in frames if f["screen"] == 58)
    i58 = [i for i, f in enumerate(frames) if f["screen"] == 58]
    around = Counter(f["source"] for f in frames[max(0, i58[0] - 200):i58[-1] + 200]) \
        if i58 else {}
    runs = []
    for f in (frames[max(0, i58[0] - 200):i58[-1] + 200] if i58 else []):
        key = (f["screen"], f["source"], f["kind"])
        if runs and runs[-1][0] == key:
            runs[-1][1] += 1
        else:
            runs.append([key, 1])
    summary = {"runs_around_58": [[*k, n] for k, n in runs],
               "frames": len(frames), "native_frames_by_screen_kind":
               {f"{k[0]}/{k[1]}": n for k, n in nets.items()},
               "frames_at_58": dict(at58), "sources_200_before_to_200_after_58": dict(around)}
    print("  frames:", summary)
    with open(os.path.join(w.run.dir, "decisions.json"), "w", encoding="utf-8") as fh:
        json.dump({"slot": slot, "result": result, "frames": summary,
                   "decisions": w.decisions}, fh,
                  indent=1, default=str)
    w.save({"notes": f"turn_audience SAVE{slot}: {result}", **close(w.run, saves)})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
