# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 090o_core_no_native_frame_on_a_known_screen.py.
# `tools/smoke_test.py` executes this file, and every other module in
# tools/smoke_suite/, in file-name order and in ONE namespace. Do not
# import this file; it is not a module.
#
# The 4 check(s) it holds:
#   - the hand-over gate: a known screen is held for its data and falls back once as a failure; a modal net and an empty no-screen id are held, not failed
#   - main.App asks the gate for every hand-over, a held frame keeps the last HD frame or the universal background, and no input reaches it
#   - recorded transitions for every registry screen replay with no native frame, before the target's first HD frame or after it, and no fallback
#   - the replay can fail: without the hold, the three flashes work order 180 A1 measured come back


# ── A SCREEN HD DRAWS NEVER PRESENTS A NATIVE FRAME (180 A2) ────
#
# Work order 180 A1 measured three transitions that showed the game's own
# picture before HD (`doc/briefs/180-flash-findings.md`). The fix is ONE
# gate at the one place every hand-over passes, `main.App._showing_original`
# — `core/handover.py` says why it is not in the screens.
import inspect as _ho_inspect
import json as _ho_json
import types as _ho_ns
import main as _ho_main
from core import handover as _ho

# 1. THE GATE'S RULES, one way in at a time.
_hg = _ho.Gate(hold=3, empty_hold=3)
assert _hg.decide(True, _ho.F12, "", 4, 0, 0) is True and not _hg.holding, \
    "F12 is the player's own mode and is never held"
assert _hg.decide(True, _ho.NO_SCREEN, "", 1, 40, 1) is True, \
    "an id with no HD screen and a list to answer is shown at once"
# an empty no-screen list: held, and a SILENCE (no new snapshot) never
# runs the bound out — the load's screen 39 then the map
assert [_hg.decide(True, _ho.NO_SCREEN, "", 39, 0, 10) for _ in range(9)] \
    == [False] * 9 and _hg.holding
assert _hg.decide(False, "", "galaxy_map", 0, 23, 11) is False \
    and not _hg.holding and _hg.resolved == 1
# a known screen's first snapshot judged a refusal (Fleets): held, resolved
assert _hg.decide(True, _ho.HAND_OVER, "fleets", 4, 23, 20) is False \
    and _hg.holding
assert _hg.decide(False, "", "fleets", 4, 73, 21) is False \
    and _hg.resolved == 2 and _hg.failures == 0
# data that never comes: held for the bound, then shown ONCE — and it stays
# shown while the request stands, no flip-flop — counted as a failure
_hseq = [_hg.decide(True, _ho.HAND_OVER, "races", 6, 17, n)
         for n in range(30, 38)]
assert _hseq == [False, False, False, True, True, True, True, True], _hseq
assert _hg.failures == 1
# a modal net doing its job: held the same way, then shown, NOT a failure
_hseq = [_hg.decide(True, _ho.MODAL, "galaxy_map", 0, 5, n)
         for n in range(40, 45)]
assert _hseq == [False, False, False, True, True] and _hg.failures == 1
assert "DEVIATION `hold_last_frame`" in (_ho.__doc__ or ""), \
    "the hold is the original's picture withheld: marked in its module"
assert "DEVIATION `hold_last_frame`" in io.open(os.path.join(
    os.path.dirname(SCREENS_DIR), "v3_projektstatus.md"),
    encoding="utf-8").read(), "…and in the status document"
assert _ho.HOLD >= 36 and _ho.EMPTY_HOLD >= 36, (
    "the bound must outlast the longest transition measured: the main "
    "menu's opening animation, 24 snapshots (work order 180 A2)")
ok("the hand-over gate: a known screen is held for its data and falls back "
   "once as a failure; a modal net and an empty no-screen id are held, not "
   "failed")

# 2. THE WIRING. `_showing_original` reaches the gate on every way in but
# the unconnected one; the held frame is its own branch of `_render`,
# before any HD drawing, and draws no editor over a stale frame; clicks,
# keys and the right button stop at a hold.
_ho_src = _ho_inspect.getsource(_ho_main.App._showing_original)
assert _ho_src.count("self._gated(") == 3, \
    "every way into the game's picture must pass the hand-over gate"
_ho_render = _ho_inspect.getsource(_ho_main.App._render)
assert "elif self._handover.holding:" in _ho_render and \
    _ho_render.index("self._handover.holding") < \
    _ho_render.index("self.dispatcher.render"), _ho_render
assert "handover.render_hold(self)" in _ho_render
assert "if not self._handover.holding:\n            self.editor.render" \
    in _ho_render
assert "elif self._handover.holding:\n            return" in \
    _ho_inspect.getsource(_ho_main.App._handle_click)
_ho_events = _ho_inspect.getsource(_ho_main.App._handle_events)
assert "elif self._handover.holding:\n                    pass" in _ho_events
assert "and not self._handover.holding" in _ho_events
# The held frame itself: a surface that shows the game's picture (or a new
# one after a resize) is covered with the universal background; a surface
# that shows HD is left exactly as it is.
import pygame as _ho_pg
_ho_app = _ho_ns.SimpleNamespace(surface=_ho_pg.Surface((64, 36)),
                                 _surface_hd=False)
_ho_app.surface.fill((200, 0, 200))           # stands for the game's picture
_ho.render_hold(_ho_app)
assert _ho_app._surface_hd and _ho_app.surface.get_at((5, 5))[:3] \
    != (200, 0, 200), "a held frame over the game's picture must cover it"
_ho_app.surface.fill((1, 2, 3))               # stands for the last HD frame
_ho.render_hold(_ho_app)
assert _ho_app.surface.get_at((5, 5))[:3] == (1, 2, 3), \
    "a held frame over an HD frame must keep it"
assert "self._surface_hd = False" in _ho_inspect.getsource(
    _ho_main.App._after_resolution_change)
ok("main.App asks the gate for every hand-over, a held frame keeps the last "
   "HD frame or the universal background, and no input reaches it")

# 3. THE REPLAY. `tools/fixtures/transitions_180.json` holds every
# transition the A2 walks recorded — what the engine and the screens SAID,
# one row per snapshot — and this feeds each through `handover.decide_for`
# with the screen's own `handover_is_modal()` from the live registry.
with open(os.path.join(os.path.dirname(SCREENS_DIR), "tools", "fixtures",
                       "transitions_180.json"), encoding="utf-8") as _ho_fh:
    _ho_fix = _ho_json.load(_ho_fh)["transitions"]


def _ho_replay(rows, gate):
    """Each row through the gate; returns what each would present."""
    class _Top:
        def __init__(self, name):
            self.name = name

        def handover_is_modal(self):
            screen = d.screens.get(self.name)
            return bool(screen is not None and screen.handover_is_modal())
    app = _ho_ns.SimpleNamespace(
        _handover=gate,
        client=_ho_ns.SimpleNamespace(state=None, stats={}),
        dispatcher=_ho_ns.SimpleNamespace(overlay_name="", active_name=""))
    out = []
    for snap, screen, live, top, want, kind in rows:
        app.client.state = _ho_ns.SimpleNamespace(
            current_screen=screen,
            fields=[_ho_ns.SimpleNamespace(index=i + 1) for i in range(live)])
        app.client.stats = {"state": snap}
        app.dispatcher.active_name = top
        shown = _ho.decide_for(app, want, kind, _Top(top) if top else None)
        out.append("net" if shown else ("hold" if gate.holding
                                        else ("hd" if top else "fill")))
    return out


def _ho_flashes(tr, presented):
    """Native frames anywhere in the transition — before the target's
    first HD frame AND after it: A1's main-menu flash came 62 frames
    after HD had drawn — except the one the rule allows: an id HD has no
    screen for, with a list to answer."""
    rows = tr["rows"]
    return [i for i in range(len(rows)) if presented[i] == "net"
            and not (rows[i][5] == "no_screen" and rows[i][2] > 0)]


_ho_bad, _ho_fail, _ho_held = [], 0, 0
for _tr in _ho_fix:
    _hgate = _ho.Gate()
    _pres = _ho_replay(_tr["rows"], _hgate)
    if _ho_flashes(_tr, _pres):
        _ho_bad.append(_tr["transition"])
    _ho_fail += _hgate.failures
    _ho_held += _pres.count("hold")
assert not _ho_bad, f"native frames before HD on replay: {_ho_bad}"
assert _ho_fail == 0, f"{_ho_fail} fallback(s) on replay — a failure"
# EVERY SCREEN IN THE REGISTRY IS A TARGET, or the check has a hole the
# size of the next screen. The registry is what the app discovers — the
# screens folder and the active mods — not `d.screens`, which also holds
# screens other checks register for themselves.
from core.screens_loader import discover_screens as _ho_discover
_ho_registry = set(_ho_discover(app.res))
_ho_targets = {_tr["target"] for _tr in _ho_fix}
_ho_missing = sorted(_ho_registry - _ho_targets)
assert not _ho_missing, (
    f"screens in the registry with no recorded transition: {_ho_missing} — "
    f"walk them (tools/flash_walk.py) and rebuild the fixture "
    f"(tools/flash_fixture.py), or add a SYNTHETIC one with its reason")
_ho_synth = [_tr for _tr in _ho_fix if _tr.get("synthetic")]
assert [_tr["target"] for _tr in _ho_synth] == ["research_select"], \
    "a synthetic transition stands only where no walk can go, with a reason"
ok(f"recorded transitions for every registry screen replay with no native "
   f"frame, before the target's first HD frame or after it, and no fallback "
   f"({len(_ho_fix)} transitions, {len(_ho_registry)} screens, {_ho_held} "
   f"held snapshots)")

# 4. AND IT CAN FAIL. The same recordings through a gate that holds
# nothing bring back exactly the A1 shapes: Fleets' first snapshot, the
# load's empty screen 39, the main menu's opening animation.
_ho_back = set()
for _tr in _ho_fix:
    if _ho_flashes(_tr, _ho_replay(_tr["rows"], _ho.Gate(0, 0))):
        _ho_back.add(_tr["transition"])
assert {"galaxy_map -> fleets", "startup -> main_menu",
        "load dialog -> galaxy_map (SAVE4)"} <= _ho_back, sorted(_ho_back)
ok(f"the replay can fail: without the hold, the three flashes work order "
   f"180 A1 measured come back ({len(_ho_back)} transitions)")
