# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 090u_core_the_click_log.py.
# `tools/smoke_test.py` executes this file, and every other module in
# tools/smoke_suite/, in file-name order and in ONE namespace. Do not
# import this file; it is not a module.
#
# The 1 check(s) it holds:
#   - the click log is off unless switched on, sees every click and key main.App receives, and names why one did not reach the engine


# ── THE CLICK LOG (work order 182, part 3) ──────────────────────
#
# 181 lost one Cancel click at 3840 and nothing could say why. The stress
# of 182 (3009 inputs on the virtual display at 1920, 2576 and 3840) lost
# none and dropped none, so the 181 case counts as outside interference —
# Data was at the desk, and the engine's window follows the real pointer —
# and the log stays, as a tool, behind `ORIONLAYER_INPUT_LOG`. What it must
# keep doing is held here: nothing when off, one entry per click and key
# when on, "sent" only when a message went out while the input was
# handled, and the reason for every drop, in the order `main.App` decides
# them (an app key, the F5 editor, no connection, the game's picture, a
# held frame, and otherwise the screen's own choice — with the field count
# and the view state that explain it).
import types as _il_ns
import inspect as _il_insp
from core import inputlog as _il
import main as _il_main

assert _il.InputLog.open(object(), environ={}) is None, "off by default"


class _IlClient:
    def __init__(self):
        self.sent = []
        self.state = _il_ns.SimpleNamespace(current_screen=25, fields=[1, 2, 3])

    def _send_message(self, t, p):
        self.sent.append(t)


def _il_app(**kw):
    view = _il_ns.SimpleNamespace(state=kw.get("view", "READY"))
    top = _il_ns.SimpleNamespace(_view=view)
    return _il_ns.SimpleNamespace(
        client=_IlClient(),
        dispatcher=_il_ns.SimpleNamespace(overlay_name=None,
                                          active_name="build_queue", top=top),
        editor=_il_ns.SimpleNamespace(active=kw.get("editor", False)),
        _handover=_il_ns.SimpleNamespace(holding=kw.get("hold", False)),
        _showing_original=lambda: kw.get("net", False),
        connected=kw.get("connected", True))


_il_click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(10, 20), button=1)
_il_key = lambda k: pygame.event.Event(pygame.KEYDOWN, key=k)  # noqa: E731
_il_cases = [
    ({}, _il_click, True, ("sent", "")),
    ({}, _il_click, False, ("dropped", "screen sent nothing")),
    ({"hold": True}, _il_click, False, ("dropped", "hold")),
    ({"net": True}, _il_click, False, ("dropped", "net")),
    ({"editor": True}, _il_click, False, ("dropped", "editor")),
    ({"connected": False}, _il_click, False, ("dropped", "not connected")),
    ({}, _il_key(pygame.K_F12), False, ("dropped", "app key")),
    ({"view": "GAME_BOX"}, _il_key(pygame.K_ESCAPE), False,
     ("dropped", "screen sent nothing")),
]
for _il_kw, _il_ev, _il_sends, _il_want in _il_cases:
    _il_a = _il_app(**_il_kw)
    _il_log = _il.InputLog.open(_il_a.client, environ={_il.ENV: "1"})
    _il_log.begin(_il_a, _il_ev)
    if _il_sends:
        _il_a.client._send_message(0x81, b"")
    _il_e = _il_log.end()
    assert (_il_e["outcome"], _il_e["reason"]) == _il_want, (_il_kw, _il_e)
    assert _il_e["fields"] == 3 and _il_e["screen"] == 25 and \
        _il_e["top"] == "build_queue"
    assert _il_e["messages"] == ([0x81] if _il_sends else [])
assert _il_e["view"] == "GAME_BOX", "the view state explains a drop"
# A motion is not an input the log is about; a right click neither.
_il_a = _il_app()
_il_log = _il.InputLog.open(_il_a.client, environ={_il.ENV: "1"})
_il_log.begin(_il_a, pygame.event.Event(pygame.MOUSEMOTION, pos=(1, 1),
                                        rel=(0, 0), buttons=(0, 0, 0)))
assert _il_log.end() is None and not _il_log.entries
# main.App: opened once, begin and end around EVERY event of the loop, and
# no way out of the loop body between them.
_il_src = _il_insp.getsource(_il_main.App._handle_events)
_il_body = _il_src[_il_src.index("for event in pygame.event.get():"):]
assert _il_body.index("self._input_log.begin(self, event)") < \
    _il_body.index("if event.type == pygame.QUIT:")
assert _il_body.rstrip().endswith("self._input_log.end()")
assert "continue" not in _il_body and "return" not in _il_body
assert "inputlog.InputLog.open(self.client)" in _il_insp.getsource(
    _il_main.App.__init__)
ok(f"the click log is off unless switched on, sees every click and key "
   f"main.App receives, and names why one did not reach the engine "
   f"({len(_il_cases)} outcomes)")
