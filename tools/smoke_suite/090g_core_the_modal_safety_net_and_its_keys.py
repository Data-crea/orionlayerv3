# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 090g_core_the_modal_safety_net_and_its_keys.py.
# Executed in the suite's one namespace, after 090a-090f. Work order 177,
# part C: a modal the engine shows and HD has no view for is handed to the
# game's own picture, and the keys go with the clicks.
#
# The 2 check(s) it holds:
#   - the net: its own list and a known modal keep HD's picture; an unknown
#     list hands over only after it has stood SETTLE snapshots, logs its
#     shape once, and lets go on another screen or when the list is known
#   - the keys: a KEYDOWN while the game's picture is shown goes to the
#     game (typed characters as their code, Backspace / Enter / ESC as the
#     control codes, arrows not at all), main.py routes it so, and an
#     overlay may stand over a second screen id (ALSO_OVER_IDS)
import logging as _mn_log

from core import modalnet as _mn
from core.original_view import OriginalView as _MnOV


class _MnS:
    pass


def _mn_state(screen, fields):
    _s = _MnS()
    _s.current_screen, _s.fields = screen, fields
    return _s


_mn_own = [_ldw_f(1, (10, 10, 20, 20), 0, ord("O"))]
_mn_box = [_ldw_f(1, (30, 30, 40, 40), 7, ord("K"))]
_mn_odd = [_ldw_f(1, (0, 0, 639, 479), 7, 0), _ldw_f(2, (5, 5, 9, 9), 7, 0)]
_mn_net = _mn.Net("test", lambda f: f[0].hotkey == ord("O"),
                  known=(("k", lambda f: f[0].hotkey == ord("K")),))


class _MnCatch(_mn_log.Handler):
    def __init__(self):
        super().__init__()
        self.lines = []

    def emit(self, record):
        self.lines.append(record.getMessage())


_mn_catch = _MnCatch()
_mn_log.getLogger("modalnet").addHandler(_mn_catch)
try:
    assert not _mn_net.check(_mn_state(0, _mn_own), 0)
    assert not _mn_net.check(_mn_state(0, _mn_box), 0)
    _mn_seen = [_mn_net.check(_mn_state(0, _mn_odd), 0)
                for _ in range(_mn.SETTLE + 3)]
    assert _mn_seen == [False] * (_mn.SETTLE - 1) + [True] * 4, _mn_seen
    assert len(_mn_catch.lines) == 1 and "2 fields" in _mn_catch.lines[0], \
        _mn_catch.lines
    assert not _mn_net.check(_mn_state(4, _mn_odd), 0), "another screen"
    assert not _mn_net.check(_mn_state(0, _mn_own), 0), "known again"
    assert not _mn_net.check(_mn_state(0, _mn_odd), 0), "the streak restarts"
finally:
    _mn_log.getLogger("modalnet").removeHandler(_mn_catch)
assert "DEVIATION `modal_fallback`" in (_mn.__doc__ or ""), \
    "the net is marked where it lives"
ok("the modal safety net keeps HD's picture for its own list and a known "
   "modal, hands an unknown one to the game's picture only after SETTLE "
   "snapshots, logs its shape once, and lets go when it leaves")


class _MnE:
    def __init__(self, key, uni=""):
        self.key, self.unicode = key, uni


assert _MnOV.key_code(_MnE(pygame.K_a, "A")) == 65
assert _MnOV.key_code(_MnE(pygame.K_a, "a")) == 97
assert _MnOV.key_code(_MnE(pygame.K_BACKSPACE, "\b")) == 8
assert _MnOV.key_code(_MnE(pygame.K_RETURN, "\r")) == 13
assert _MnOV.key_code(_MnE(pygame.K_KP_ENTER, "\r")) == 13
assert _MnOV.key_code(_MnE(pygame.K_ESCAPE, "\x1b")) == 27
assert _MnOV.key_code(_MnE(pygame.K_LEFT, "")) is None
_mn_sent = []
_MnCl = type("_MnCl", (), {"inject_key": lambda self, k: _mn_sent.append(k)})
assert _MnOV().forward_key(_MnCl(), _MnE(pygame.K_m, "M")) == 77 and \
    _mn_sent == [77]
_mn_main = open(os.path.join(os.path.dirname(SCREENS_DIR), "main.py"),
                encoding="utf-8").read()
_mn_kd = _mn_main[_mn_main.index("elif event.type == pygame.KEYDOWN:"):
                  _mn_main.index("elif event.type == pygame.MOUSEBUTTONDOWN")]
assert _mn_kd.index("self._showing_original()") < _mn_kd.index(
    "forward_key") < _mn_kd.index("route_key_event"), \
    "main.py sends the keys to the game while its picture is shown"
from core.dispatcher import Dispatcher as _MnD
_mn_d = _MnD()
_MnOver = type("_MnOver", (), {"GAME_SCREEN_ID": 8, "ALSO_OVER_IDS": (10,),
                               "exit": lambda self: None,
                               "update": lambda self, s=None: None})
_mn_d.overlay, _mn_d.overlay_name = _MnOver(), "game_menu"
assert _mn_d.update_from_game(_mn_state(10, [])) is True and \
    _mn_d.overlay_name == "game_menu", "the overlay stands over screen 10"
_mn_d.screen_map = {}
_mn_d.update_from_game(_mn_state(0, []))
assert _mn_d.overlay is None, "and closes on any other screen"
ok("while the game's picture is shown its keys go to the game — typed "
   "characters as their codes, Backspace, Enter, ESC — main.py routes them "
   "so, and an overlay may stand over a second screen id")
