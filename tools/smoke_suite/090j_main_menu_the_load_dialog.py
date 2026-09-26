# smoke-suite area: main_menu
#
# Part of the OrionLayer smoke suite — 090j_main_menu_the_load_dialog.py.
# Executed in the suite's one namespace, after 090a-090i. Work order 177,
# part D: the main menu's Load dialog.
#
# The 2 check(s) it holds:
#   - the main menu's own list keeps HD's picture; its Load dialog without
#     save slots on the wire (open fix 34 not applied) goes to the safety
#     net; with slots the GAME menu overlay draws it over screen 10 and
#     closes when the dialog does
#   - open fix 34 applied (work order 179): required by version_check, and
#     a slot message behind the menu's OWN list — what the engine sends
#     after the dialog is left with ESC — opens nothing
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


# 2 — WORK ORDER 179: open fix 34 is applied, and its one side effect is
#     held here. The dialog's ESC exit (`screen_cancel_field_id`,
#     loadsave.cpp:388-391) leaves `_screen_data` at 2 where CANCEL resets
#     it (:382-383), so the main menu's own list comes back with a slot
#     message behind it — measured live (evidence/work_order_179/
#     fix34_esc_side_effect/). The slots alone must never open the dialog:
#     only the dialog's field shape AND slots do.
import version_check as _mm_vc
assert "doc/ext_main_menu_save_slots.patch" in _mm_vc.LOCAL_PATCHES
assert "doc/ext_main_menu_save_slots.patch" not in _mm_vc.REPORTED_PATCHES
assert _mm_vc.LOCAL_PATCHES["doc/ext_main_menu_save_slots.patch"][1] in \
    open(os.path.join(os.path.dirname(SCREENS_DIR), "doc",
                      "ext_main_menu_save_slots.patch"), encoding="utf-8").read()
# A new machine learns which engine it needs from the README's table
# (work order 179): every required patch named there, fix 34 included.
_mm_readme = open(os.path.join(os.path.dirname(SCREENS_DIR), "README.md"),
                  encoding="utf-8").read()
_mm_sec = _mm_readme[_mm_readme.index("<!-- orion2re-patches -->"):]
_mm_sec = _mm_sec[:_mm_sec.index("\n## ")]
_mm_missing = [k for k in _mm_vc.LOCAL_PATCHES if f"`{k}`" not in _mm_sec]
assert not _mm_missing, f"README's orion2re table does not name {_mm_missing}"
_mm_stale = [{"status": 0, "description": "x", "stardate": "", "date": ""}]
for _ in range(8):
    _mm_scr.update(_mm_state(_mm_own, slots={"screen_data": 2,
                                             "slots": _mm_stale}))
    assert _ldw_app.dispatcher.overlay_name != "game_menu", \
        "a stale slot message behind the menu's own list opened the dialog"
    assert not _mm_scr.wants_original(), \
        "a stale slot message behind the menu's own list reached the net"
ok("open fix 34 applied, required by version_check and named in the "
   "README's orion2re table with every other required patch; the slot message "
   "the engine sends behind the main menu's own list after an ESC exit "
   "opens nothing — only the dialog's fields with slots do")
