# smoke-suite area: galaxy_map
#
# Part of the OrionLayer smoke suite — 090h_galaxy_map_the_modals_over_the_map.py.
# Executed in the suite's one namespace, after 090a-090g. Work order 177,
# parts A-C on the galaxy map: the home star name drawn and typed in HD,
# the game's confirmations drawn and answered, everything else routed to
# the safety net.
#
# The 2 check(s) it holds:
#   - the home star name: recognised by its exact two fields, prefilled
#     with the home star's name, typed by the field's own rules (the first
#     Backspace clears, '_' refused, 14 characters), each key sent as its
#     code, ACCEPT and Enter send Enter and never an activation; drawn at
#     four sizes
#   - a confirmation over the map is drawn and answered (click, Y / N); the
#     map's own list and the known modals keep HD's picture; the colony-base
#     planet selection and a text box are routed to the safety net
import hud_evidence as _gx_he
from screens.galaxy_map import mapmodal as _gx_mm

_gx_home = [_ldw_f(1, _gx_mm.HOME_STAR_BUTTON, 0, 0),
            _ldw_f(2, (165, 200, 300, 226), 11, 0)]
assert _gx_mm.is_home_star(_gx_home)
assert not _gx_mm.is_home_star([_ldw_f(1, (273, 225, 370, 252), 0, 0),
                                _ldw_f(2, (211, 179, 300, 205), 11, 0)]), \
    "the colonise rename (origin 177,125) is not the home star's"


def _gx_app(w=1920, h=1080):
    _a = _gx_he.make_app(w, h)
    _a.dispatcher.switch_to("galaxy_map")
    _s = _a.dispatcher.active
    _gs = _gx_he.galaxy_state()
    _gs.current_screen = 0
    _a.connected = True
    _sent = []

    class _C:
        state = _gs

        def activate_field(self, i):
            _sent.append(("act", i))

        def inject_key(self, k):
            _sent.append(("key", k))

        def inject_click(self, x, y):
            _sent.append(("click", x, y))
    _a.client = _C()
    return _a, _s, _gs, _sent


class _GxE:
    def __init__(self, key, uni=""):
        self.key, self.unicode = key, uni


_gx_a, _gx_s, _gx_gs, _gx_sent = _gx_app()
_gx_gs.fields = _gx_home
_gx_s.update(_gx_gs)
_gx_m = _gx_s._modal
_gx_star = _gx_s.home_star()
assert _gx_m.kind == "home_star" and _gx_m.text == (
    _gx_star.name if _gx_star else "")[:14], (_gx_m.kind, _gx_m.text)
assert not _gx_s.wants_original()
for _gx_ev in (_GxE(pygame.K_BACKSPACE), _GxE(pygame.K_m, "M"),
               _GxE(pygame.K_e, "e"), _GxE(pygame.K_MINUS, "_"),
               _GxE(pygame.K_n, "n")):
    _gx_s.handle_key_event(_gx_ev)
assert _gx_m.text == "Men", _gx_m.text
assert _gx_sent == [("key", 8), ("key", 77), ("key", 101), ("key", 110)], \
    _gx_sent
_gx_s.handle_key_event(_GxE(pygame.K_BACKSPACE))
assert _gx_m.text == "Me", "a later Backspace deletes one character"
for _ in range(20):
    _gx_s.handle_key_event(_GxE(pygame.K_x, "x"))
assert len(_gx_m.text) == 14, "at most 14 characters (a 15-byte buffer)"
import pygame as _gx_pg
_gx_surf = _gx_pg.Surface((1920, 1080))
_gx_s.render(_gx_surf)
_gx_sent.clear()
_gx_s.handle_click(*_gx_m._rects["accept"].center)
assert _gx_sent == [("key", 13)], ("ACCEPT sends Enter, never an "
                                   "activation (fields.cpp:172-183)", _gx_sent)
_gx_sent.clear()
_gx_s.handle_key_event(_GxE(pygame.K_RETURN, "\r"))
assert _gx_sent == [("key", 13)]
for _gx_size in ((2560, 1440), (3840, 2160), (2576, 1432)):
    _gx_a2, _gx_s2, _gx_gs2, _ = _gx_app(*_gx_size)
    _gx_gs2.fields = _gx_home
    _gx_s2.update(_gx_gs2)
    _gx_s2.render(_gx_pg.Surface(_gx_size))
    assert "accept" in _gx_s2._modal._rects
ok("the home star name dialog: recognised by its two fields, prefilled "
   "with the home star, typed by the field's own rules with every key sent "
   "as its code, ACCEPT and Enter send Enter (never an activation), drawn "
   "at four sizes")

# ── a confirmation, the own list, the net ──────────────────
_gx_conf = [_ldw_f(1, (235, 302, 286, 323), 7, ord("Y")),
            _ldw_f(2, (345, 302, 396, 323), 7, ord("N"))]
_gx_gs.fields = _gx_conf
_gx_s.update(_gx_gs)
assert _gx_m.kind == "confirmation" and not _gx_s.wants_original()
# Work order 188, Stage 1: the question is not on the wire (open fix 29) —
# the F12 notice in the box's place, and neither a click nor Y / N answers
# blind. With the crop switch on, the old mapping (kept for the HD box).
from screens.fleets import fltbox as _gx_fb
_gx_s.render(_gx_surf)
assert _gx_m._rects == {}
_gx_sent.clear()
_gx_s.handle_click(960, 540)
_gx_s.handle_key_event(_GxE(pygame.K_n, "n"))
assert _gx_sent == [], _gx_sent
_gx_fb.SHOW_CROP = True
try:
    _gx_s.render(_gx_surf)
    _gx_sent.clear()
    _gx_yes = _gx_m._rects["yes"][0]
    _gx_s.handle_click(*_gx_yes.center)
    assert _gx_sent == [("act", 1)], _gx_sent
    _gx_sent.clear()
    _gx_s.handle_key_event(_GxE(pygame.K_n, "n"))
    assert _gx_sent == [("act", 2)], _gx_sent
finally:
    _gx_fb.SHOW_CROP = False
    _gx_m._rects = {}
_gx_d = _gx_s._data
_gx_ownf = [_ldw_f(1, tuple(_gx_d["map_cancel"]["rect"]),
                   _gx_d["map_cancel"]["field_type"], 0),
            _ldw_f(2, tuple(_gx_d["zoom_out_field"]["rect"]),
                   _gx_d["zoom_out_field"]["field_type"], ord("-"))]
_gx_planets = [_ldw_f(1, (410, 340, 476, 362), 0, 0x1B),
               _ldw_f(2, (147, 104, 494, 151), 7, 0),
               _ldw_f(3, (300, 200, 320, 220), 7, 0),
               _ldw_f(4, (0, 0, 639, 479), 7, 0)]
_gx_textbox = [_ldw_f(1, (0, 0, 639, 479), 7, 0x1B)]
for _gx_name, _gx_f, _gx_want in (("own list", _gx_ownf, False),
                                  ("planet selection", _gx_planets, True),
                                  ("text box", _gx_textbox, True)):
    _gx_gs.fields = _gx_ownf
    _gx_s.update(_gx_gs)
    _gx_gs.fields = _gx_f
    _gx_got = [(_gx_s.update(_gx_gs), _gx_s.wants_original())[1]
               for _ in range(8)]
    assert _gx_got[-1] is _gx_want and _gx_got[0] is False, (
        _gx_name, _gx_got)
    assert not _gx_s._modal.active or _gx_name == "own list"
ok("a confirmation over the map is drawn and answered by click and by "
   "Y / N; the map's own list keeps HD's picture; the colony-base planet "
   "selection and a text box go to the safety net after it settles")
