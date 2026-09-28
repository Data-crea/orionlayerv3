#!/usr/bin/env python3
"""The diplomacy audience walked live — work order 185, parts 10 and 11.

    python tools/audience_walk.py W H

ONLY AGAINST AN ENGINE CARRYING OPEN FIXES 46 AND 47 — applied since work
order 186, so the engine `tools/engine_start.py` starts; without them the
audience is the game's picture. Every transition through the HD window
(`colony_accept.Accept`: every frame traced and pixel-checked, recorded
for the flash check's replay fixture, `tools/flash_fixture.py`):

    galaxy map -> Races (the nav bar)
    AUDIENCE, race slot 0 -> the audience (the scratch save's slot 0
        refuses: a statement), a click -> Races
    AUDIENCE, race slot 1 -> the audience (the greeting), a click -> the
        menu, Good Bye -> Races
    Races -> galaxy map (ESC)

Nothing is agreed: only the statements' clicks and Good Bye are sent. No
TURN, no SAVE; the save is SAVE4 (scratch). The AI's audience (58) comes
only at a turn start and is not walked.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame  # noqa: E402

import colony_accept  # noqa: E402
import livesend  # noqa: E402
from livedrive import close, hashes  # noqa: E402

from screens.audience import auwire  # noqa: E402
from screens.races import racesgeom as rg, raceswire as rw  # noqa: E402


class AudienceWalk(colony_accept.Accept):

    def races_main(self, st):
        v = self.hd("races")._view
        return st.current_screen == 6 and v is not None and \
            v.state == rw.MAIN

    def audience_in(self, state):
        def ready(st):
            v = self.hd("audience")._view
            return st.current_screen == 57 and v is not None and \
                v.state == state
        return ready

    def centre(self):
        self.click(self.app.win_w // 2, self.app.win_h // 2)

    def open(self, slot):
        """AUDIENCE, then race `slot`; the audience's first state."""
        races = self.hd("races")
        self.click_field(races, rg.button_rect("audience"))
        self.wait(lambda st: self.hd("races")._view is not None and
                  self.hd("races")._view.state == rw.WHO, 10)
        self.settle(5)
        return self.transition(
            f"races -> audience (race slot {slot})", "audience",
            lambda: self.click_field(races, rg.who_field(slot)),
            lambda st: st.current_screen == 57 and
            self.hd("audience")._view is not None and
            self.hd("audience")._view.draws)

    def through(self, record):
        """Statements clicked away until the menu; Good Bye; or a refusal
        clicked away — back to Races either way."""
        scr = self.hd("audience")
        for _ in range(3):
            v = scr._view
            if v is None or v.state != auwire.STATEMENT:
                break
            if v.refused:
                record("refused")
                return self.transition("audience -> races (refusal clicked)",
                                       "races", self.centre, self.races_main)
            record("statement")
            self.transition("audience -> audience (statement clicked)",
                            "audience", self.centre,
                            self.audience_in(auwire.MENU))
        v = scr._view
        if v is None or v.state != auwire.MENU:
            print(f"  no menu: {v.state if v else None} — nothing sent")
            return False
        record("menu")
        bye = next((f for item, f in v.items()
                    if "bye" in item["text"].lower()), None)
        if bye is None:
            print("  no Good Bye in the menu — nothing sent")
            return False
        from screens.leaders import ldrdraw as nd
        r = nd.rect(scr.layout, (bye.x, bye.y, bye.x_end, bye.y_end))
        return self.transition("audience -> races (Good Bye)", "races",
                               lambda: self.click(r.centerx, r.centery),
                               self.races_main)


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    size = (int(args[0]), int(args[1]))
    os.environ.setdefault("ORIONLAYER_FRAME_TRACE", "1")
    saves = hashes()
    w = AudienceWalk(size, os.environ.get("FLASH_WALK_TAG", "P10_audience"))
    w.run.wait_for(lambda st: st.current_screen >= 0, seconds=30,
                   label="the first snapshot")
    w.settle(40)
    if w.st.current_screen == 10:
        w.load()
    if not livesend.on_galaxy_map(w.st):
        raise livesend.WrongDialog(f"screen {w.st.current_screen}, not the "
                                   f"galaxy map — nothing sent")
    stops = []

    def record(label):
        w.run.capture(f"audience_{label}")
        stops.append({"label": label, "audience": w.st.audience})

    gm = w.hd("galaxy_map")
    results = {"races": w.transition(
        "galaxy_map -> races", "races",
        lambda: w.click_rect(gm.nav_rect("races")), w.races_main)}
    for slot in (0, 1):
        if w.open(slot):
            results[f"slot {slot}"] = w.through(record)
        w.wait(w.races_main, 20)
        w.settle(10)
    w.transition("races -> galaxy_map (ESC)", "galaxy_map",
                 lambda: w.key(pygame.K_ESCAPE), livesend.on_galaxy_map)
    with open(os.path.join(w.run.dir, "stops.json"), "w",
              encoding="utf-8") as fh:
        json.dump(stops, fh, indent=1, default=str)
    w.save({"results": results, **close(w.run, saves)})
    bad = [r["transition"] for r in w.rows if r["native_total"]]
    print(f"\n  {len(w.rows)} transitions, {len(bad)} with native frames")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
