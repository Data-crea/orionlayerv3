# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 090n_core_the_frame_trace.py.
# `tools/smoke_test.py` executes this file, and every other module in
# tools/smoke_suite/, in file-name order and in ONE namespace. Do not
# import this file; it is not a module.
#
# The 3 check(s) it holds:
#   - the frame trace is off unless ORIONLAYER_FRAME_TRACE is set, and then records in memory or to a file
#   - every presented frame is tagged hd, net (with its way in) or fill, by the branch App._render takes
#   - a transition's summary counts native frames before the TARGET's first HD frame, and after it


# ── THE FRAME TRACE (work order 180 A1) ─────────────────────────
#
# Data saw the game's own picture flash up before HD appeared. A1 had to
# count it on every transition, so every presented frame gets its source.
# It is a TOOL behind an environment variable, the debug input's rule:
# absent, `open()` is None and `_render` pays one `is None` test.
import json as _ft_json
import os as _ft_os
import tempfile as _ft_tempfile
import types as _ft_ns
from core import frametrace as _ft

assert _ft.FrameTrace.open({}) is None, \
    "the frame trace must be OFF unless its variable is set"
_ft_mem = _ft.FrameTrace.open({_ft.ENV: "1"})
assert _ft_mem is not None and _ft_mem.path is None
with _ft_tempfile.TemporaryDirectory() as _ft_dir:
    _ft_path = _ft_os.path.join(_ft_dir, "trace.jsonl")
    _ft_file = _ft.FrameTrace.open({_ft.ENV: _ft_path})
    _ft_file.record(screen=4, fields=23, source=_ft.NET,
                    kind=_ft.HAND_OVER, hd="fleets", reason="why")
    _ft_file.close()
    with open(_ft_path, encoding="utf-8") as _ft_fh:
        _ft_lines = [_ft_json.loads(l) for l in _ft_fh]
    assert len(_ft_lines) == 1 and _ft_lines[0]["source"] == "net" \
        and _ft_lines[0]["kind"] == "hand_over", _ft_lines
ok("the frame trace is off unless ORIONLAYER_FRAME_TRACE is set, and "
   "then records in memory or to a file")


def _ft_app(shown_kind, active, overlay=""):
    """Only what `record_app_frame` reads."""
    app = _ft_ns.SimpleNamespace(
        connected=True, _net_kind=shown_kind, _fallback_note=None,
        client=_ft_ns.SimpleNamespace(state=_ft_ns.SimpleNamespace(
            current_screen=4, fields=[1, 2, 3])),
        dispatcher=_ft_ns.SimpleNamespace(
            active=object() if active else None,
            active_name=active, overlay_name=overlay,
            top=object() if (active or overlay) else None),
        _frame_trace=_ft.FrameTrace())
    return app


_ft_cases = [
    (True, _ft.HAND_OVER, "fleets", "", ("net", "hand_over", "fleets")),
    (True, _ft.NO_SCREEN, "", "", ("net", "no_screen", "")),
    (False, "", "galaxy_map", "game_menu", ("hd", "", "game_menu")),
    (False, "", "", "", ("fill", "", "")),
]
for _shown, _kind, _active, _over, _want in _ft_cases:
    _e = _ft.record_app_frame(_ft_app(_kind, _active, _over), _shown)
    assert (_e["source"], _e["kind"], _e["hd"]) == _want, (_e, _want)
    assert _e["screen"] == 4 and _e["fields"] == 3
# And the wiring: `App._render` records the value it branches on, and the
# App opens the trace through the switch. Read off the source, because a
# real App drags a window and a client with it.
import inspect as _ft_inspect
import main as _ft_main
_ft_render = _ft_inspect.getsource(_ft_main.App._render)
assert "shown = self._showing_original()" in _ft_render and \
    "if self._frame_trace is not None:" in _ft_render and \
    "frametrace.record_app_frame(self, shown)" in _ft_render and \
    _ft_render.index("record_app_frame") < _ft_render.index("if shown:"), \
    "App._render must record the branch it takes, before it takes it"
assert "frametrace.FrameTrace.open()" in _ft_inspect.getsource(
    _ft_main.App.__init__)
ok(f"every presented frame is tagged hd, net (with its way in) or fill, "
   f"by the branch App._render takes ({len(_ft_cases)} branches)")

# A TRANSITION STARTS ON THE OLD SCREEN, which is HD too: "the first HD
# frame" is the TARGET's. Two native frames before it and one after it
# are counted apart; the seconds run from the first native frame to the
# frame that replaced the last.
_ft_seq = [
    {"t": 0.00, "source": "hd", "hd": "galaxy_map", "kind": "",
     "reason": "", "screen": 0},
    {"t": 0.02, "source": "net", "hd": "fleets", "kind": "hand_over",
     "reason": "why", "screen": 4},
    {"t": 0.05, "source": "net", "hd": "fleets", "kind": "hand_over",
     "reason": "why", "screen": 4},
    {"t": 0.14, "source": "hd", "hd": "fleets", "kind": "", "reason": "",
     "screen": 4},
    {"t": 0.16, "source": "net", "hd": "fleets", "kind": "hand_over",
     "reason": "why", "screen": 4},
]
_ft_sum = _ft.summarise(_ft_seq, "fleets")
assert _ft_sum["first_hd_frame"] == 3 and _ft_sum["native_before_hd"] == 2
assert abs(_ft_sum["native_seconds"] - 0.12) < 1e-9, _ft_sum
assert _ft_sum["native_total"] == 3 and _ft_sum["kinds"] == ["hand_over"]
assert _ft.summarise(_ft_seq)["native_before_hd"] == 0, \
    "without a target the old screen's HD frame is the first HD frame"
ok("a transition's summary counts native frames before the TARGET's "
   "first HD frame, and after it")
