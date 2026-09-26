# smoke-suite area: main_menu
#
# Part of the OrionLayer smoke suite — 090j_main_menu_the_load_dialog.py.
# Executed in the suite's one namespace, after 090a-090i. Work order 177,
# part D: the main menu's Load dialog.
#
# The 1 check(s) it holds:
#   - the main menu's own list keeps HD's picture; its Load dialog without
#     save slots on the wire (open fix 34 not applied) goes to the safety
#     net; with slots the GAME menu overlay draws it over screen 10 and
#     closes when the dialog does
_mm_scr = _ldw_app.dispatcher.screens["main_menu"]
_ldw_app.dispatcher.switch_to("main_menu")


class _MmS:
    save_slots = None


def _mm_state(fields, slots=None):
    _s = _MmS()
    _s.current_screen, _s.fields, _s.save_slots = 10, fields, slots
    return _s


_mm_own = [_ldw_f(1, (0x19F, 0xD9, 0x237, 0xEE), 7, ord("N")),
           _ldw_f(2, (0x19F, 0x11D, 0x237, 0x132), 7, ord("Q"))]
_mm_rows = [_ldw_f(3 + _k, (209, 75 + 31 * _k, 406, 99 + 31 * _k), 7, 0)
            for _k in range(10)]
_mm_load = [_ldw_f(1, (217, 388, 300, 410), 0, ord("L")),
            _ldw_f(2, (320, 388, 400, 410), 0, ord("C"))] + _mm_rows
from screens.game_menu import nodes as _mm_nodes
assert _mm_nodes.classify(_mm_load) == _mm_nodes.LOAD
_mm_got = []
for _ in range(8):
    _mm_scr.update(_mm_state(_mm_own))
    _mm_got.append(_mm_scr.wants_original())
assert not any(_mm_got), "the menu's own list"
for _ in range(8):
    _mm_scr.update(_mm_state(_mm_load))
assert _mm_scr.wants_original(), "the Load dialog without slots: the net"
assert _ldw_app.dispatcher.overlay_name != "game_menu"
_mm_scr.update(_mm_state(_mm_load, slots=[{"slot": 1}]))
assert _ldw_app.dispatcher.overlay_name == "game_menu" and \
    not _mm_scr.wants_original(), "with slots the GAME menu overlay draws it"
_mm_scr.update(_mm_state(_mm_own))
assert _ldw_app.dispatcher.overlay_name != "game_menu", "closed with it"
ok("the main menu's Load dialog: without slots on the wire the safety net "
   "shows the game's picture, with them the GAME menu overlay draws it over "
   "screen 10 and closes when the dialog closes")
