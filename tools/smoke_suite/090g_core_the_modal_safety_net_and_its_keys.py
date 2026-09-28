# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 090g_core_the_modal_safety_net_and_its_keys.py.
# Executed in the suite's one namespace, after 090a-090f. Work order 177,
# part C: a modal the engine shows and HD has no view for is handed to the
# game's own picture, and the keys go with the clicks.
#
# The 3 check(s) it holds:
#   - the net: its own list and a known modal keep HD's picture; an unknown
#     list hands over only after it has stood SETTLE snapshots, logs its
#     shape once, and lets go on another screen or when the list is known
#   - the keys: a KEYDOWN while the game's picture is shown goes to the
#     game (typed characters as their code, Backspace / Enter / ESC as the
#     control codes, arrows not at all), main.py routes it so, and an
#     overlay may stand over a second screen id (ALSO_OVER_IDS)
#   - the clicks: on the game's picture the first field under a click decides,
#     as in the engine: a string field (type 11) or a radio button goes as
#     INJECT_CLICK, any other field as ACTIVATE_FIELD, no field as
#     INJECT_CLICK (work order 186)
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


# 3. THE CLICKS INTO A STRING FIELD (work order 186, part 3). A click on the
#    game's picture over a field went out as ACTIVATE_FIELD — except a radio
#    button's. Measured on the Ship Designer's name (a continuous string
#    field, type 11): the activation does not open it, the typed keys went
#    nowhere, and Enter pressed the field under the engine's stale pointer
#    (the hull changed). An INJECT_CLICK opens it: the keys append, Enter
#    commits. So a string field goes the radio button's way — and the FIRST
#    field covering the point decides, as the engine's hit test does: the
#    designer's list ends in a full-screen hidden field, and skipping the
#    name field to the next one activated that (measured, the same run).
from core.game_state import FieldInfo as _MnField


class _MnClient:
    def __init__(self, fields):
        self.log = []
        self.state = type("S", (), {"fields": fields})()

    def activate_field(self, i):
        self.log.append(("ACTIVATE_FIELD", i))

    def inject_click(self, x, y):
        self.log.append(("INJECT_CLICK", x, y))


def _mn_field(i, x, y, xe, ye, t):
    f = _MnField()
    f.index, f.x, f.y, f.x_end, f.y_end, f.field_type, f.hotkey = i, x, y, xe, ye, t, 0
    return f


assert _MnOV.CONTINUOUS_INPUT_TYPE == 11 and _MnOV.RADIO_BUTTON_TYPE == 1
_mn_ov = _MnOV()
_mn_cl = _MnClient([_mn_field(0, 0, 0, 639, 479, 7),
                    _mn_field(35, 18, 23, 152, 40, 11),     # the designer's name
                    _mn_field(36, 200, 23, 260, 40, 1),     # a radio button
                    _mn_field(37, 461, 443, 520, 465, 0),   # a button (Cancel)
                    _mn_field(42, 0, 0, 639, 479, 7)])      # the page's full-screen field, last
_mn_x, _mn_y, _mn_w, _mn_h, _mn_s = _mn_ov.placement(1920, 1080)
for _mn_nx, _mn_ny, _mn_want in ((85, 31, ("INJECT_CLICK", 85, 31)),
                                 (230, 31, ("INJECT_CLICK", 230, 31)),
                                 (490, 454, ("ACTIVATE_FIELD", 37)),
                                 (320, 300, ("ACTIVATE_FIELD", 42))):
    _mn_cl.log.clear()
    _mn_ov.forward_click(_mn_cl, int(_mn_x + (_mn_nx + 0.5) * _mn_s),
                         int(_mn_y + (_mn_ny + 0.5) * _mn_s), 1920, 1080)
    assert _mn_cl.log == [_mn_want], (_mn_nx, _mn_ny, _mn_cl.log)
assert _mn_ov.find_field_at(_MnClient([_mn_field(5, 0, 0, 99, 99, 7)]).state.fields,
                            500, 400) is None   # no field there: INJECT_CLICK
ok("on the game's picture the first field under a click decides, as in the "
   "engine: a string field (type 11) or a radio button goes as INJECT_CLICK, "
   "any other field as ACTIVATE_FIELD, no field as INJECT_CLICK (work order 186)")
