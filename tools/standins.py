"""Screens `tools/hud_evidence.stage` puts up from a committed stand-in.

Work order 185: the Ship Designer (`tools/design_fixture.py`), its special
picker over it (the weapon picker needs the player's DESIGN.LBX art) and
the diplomacy audience's menu (`tools/audience_fixture.py`) — recorded
blocks of open fixes that are not applied, so no engine a player has can
show them. Where the player's text files are absent — a clone — the
committed text stand-ins are used, so the screen draws the same number of
texts there.
"""
import importlib
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: name: (the tool that reads the stand-in, the stop).
STAND_INS = {"ship_design": ("design_fixture", "designer"),
             "design_box": ("design_fixture", "special"),
             "audience": ("audience_fixture", "menu")}


def stage(app, name):
    tool, stop = STAND_INS[name]
    gs = importlib.import_module(tool).state(stop)
    d = app.dispatcher
    d.update_from_game(gs)
    derived = os.path.join(ROOT, "tools", "fixtures", "derived")
    for scr in (d.active, d.overlay):
        if scr is None:
            continue
        if hasattr(scr, "names") and scr.names().state != "ok":
            from core.hestrings import HStrings
            from screens.ship_design.screen import Names
            app.hstrings = HStrings("en", root=derived)
            scr._names = Names(app, "en", root=derived)
        scr.update(gs)
    return gs
