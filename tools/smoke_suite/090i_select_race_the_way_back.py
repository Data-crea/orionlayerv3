# smoke-suite area: select_race
#
# Part of the OrionLayer smoke suite — 090i_select_race_the_way_back.py.
# Executed in the suite's one namespace, after 090a-090h. Work order 177,
# part D: Select Race gets the original's way back — its ESC hot key.
#
# The 1 check(s) it holds:
#   - ESC and the frame's Back button send the list's own ESC field
#     (racesel.cpp:195-199, :355-364) and nothing when the list has none;
#     a list without a radio button under screen 51 (the ruler's name,
#     the banners) goes to the safety net
_sr_scr = _ldw_app.dispatcher.screens["select_race"]
_ldw_app.dispatcher.switch_to("select_race")


class _SrS:
    pass


_sr_st = _SrS()
_sr_st.fields = [_ldw_f(3, (351, 90, 473, 137), 1, 0),
                 _ldw_f(7, (0, 0, 0, 0), 7, 0x1B)]
_ldw_app.client.state = _sr_st
_ldw_sent.clear()
_sr_scr.handle_key(pygame.K_ESCAPE)
assert _ldw_sent == [("act", 7)], ("ESC sends the ESC hot key's field, "
                                   "not a click where no field lies",
                                   _ldw_sent)
_sr_src = open(os.path.join(SCREENS_DIR, "select_race", "screen.py"),
               encoding="utf-8").read()
assert "inject_click(162, 445)" not in _sr_src
assert _sr_scr.FRAME_BTN_LEFT[0] == "Back" and \
    "HD EXTENSION `back_button`" in _sr_src
from core.hud import screenframe as _sr_sf
_sr_scr.render(pygame.Surface((_ldw_app.win_w, _ldw_app.win_h)))
_sr_hit = None
for _sr_y in range(0, _ldw_app.win_h, 6):
    for _sr_x in range(0, _ldw_app.win_w // 2, 6):
        if _sr_sf.side_at(_sr_scr, _sr_x, _sr_y) == "left":
            _sr_hit = (_sr_x, _sr_y)
            break
    if _sr_hit:
        break
assert _sr_hit is not None, "the Back button is drawn"
_ldw_sent.clear()
_sr_scr.handle_click(*_sr_hit)
assert _ldw_sent == [("act", 7)], ("Back sends the ESC field", _ldw_sent)
_sr_st.fields = [_ldw_f(3, (351, 90, 473, 137), 1, 0)]
_ldw_sent.clear()
_sr_scr.handle_key(pygame.K_ESCAPE)
assert _ldw_sent == [], "no ESC field (a multiplayer game): nothing sent"
# The net (found live in work order 177): the leader name's input box
# under screen 51 has no ESC field — after it settles, the game's picture.
_sr_st.current_screen = 51
_sr_st.fields = [_ldw_f(1, (273, 225, 371, 253), 7, 0),
                 _ldw_f(2, (211, 179, 313, 205), 11, 0)]
_sr_seen = [(_sr_scr.update(_sr_st), _sr_scr.wants_original())[1]
            for _ in range(6)]
assert _sr_seen[0] is False and _sr_seen[-1] is True, _sr_seen
_sr_st.fields = [_ldw_f(3, (351, 90, 473, 137), 1, 0),
                 _ldw_f(7, (0, 0, 0, 0), 7, 0x1B)]
_sr_scr.update(_sr_st)
assert not _sr_scr.wants_original(), "the race list is its own"
# The banners (Flag_Screen_, racesel.cpp:899): hidden fields and an ESC,
# no radio button — a dialog too.
_sr_st.fields = [_ldw_f(1 + _k, (96 + 124 * (_k % 4), 144, 179, 242), 7, 0)
                 for _k in range(8)] + [_ldw_f(9, (5000,) * 4, 7, 0x1B)]
assert [(_sr_scr.update(_sr_st), _sr_scr.wants_original())[1]
        for _ in range(6)][-1], "the banners go to the net"
_ldw_app.client.state = type("_SrE", (), {"fields": []})()
ok("Select Race's way back: ESC and the frame's Back button send the list's "
   "own ESC hot-key field, and nothing when the list has none; the ruler's "
   "name and the banners under its id go to the safety net")
