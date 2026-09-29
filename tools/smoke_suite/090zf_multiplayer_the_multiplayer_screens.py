# smoke-suite area: multiplayer
#
# Part of the OrionLayer smoke suite — 090zf_multiplayer_the_multiplayer_screens.py.
# `tools/smoke_test.py` executes this file, and every other module in
# tools/smoke_suite/, in file-name order and in ONE namespace. Do not
# import this file; it is not a module.
#
# The 2 check(s) it holds:
#   - the multiplayer setup reads its type and buttons off its own field list; open fix 51's MPLY parses whole or not at all for its steps; the endpoint and chat stay inside the engine's buffers
#   - MPLY routes to the multiplayer screen over a stale id and ends a sub-screen's lock; a taken banner colour picks the first free tile; each step's view binds its options and buttons to its own fields


# ── MULTIPLAYER (work order 188 Part 7, open fix 51) ─────────────
import struct as _mp_st
import types as _mp_ns
from screens.multiplayer import mpsetup as _mp_setup
from core import mpblocks as _mp_b

_mp_F = lambda i, hk, x=0, y=0, w=9, h=9, t=7: _mp_ns.SimpleNamespace(
    index=i, hotkey=hk, x=x, y=y, x_end=x + w, y_end=y + h, field_type=t)
_mp_base = [_mp_F(i + 1, hk) for i, hk in enumerate(
    (ord("N"), ord("M"), ord("H"), 0x1B, ord("S"), ord("L")))]
_mp_net = _mp_base + [_mp_F(7, ord("J"))]
_mp_online = _mp_net + [_mp_F(8, ord("C"))]
assert [_mp_setup.selected(f) for f in (_mp_net, _mp_online, _mp_base)] == \
    ["network", "online", "hotseat"], "the list names the type (live, 188)"
assert _mp_setup.classify(_mp_net) == _mp_setup.SETUP
assert _mp_setup.classify(_mp_base[:4]) is None, \
    "the first pass (four fields) is not yet the setup"
_mp_comm = [_mp_F(1, 0, 242, 249, 154, 16), _mp_F(2, 0x1B, 60),
            _mp_F(3, 0x1B, 250)]
assert _mp_setup.classify(_mp_comm) == _mp_setup.COMM
_mp_in, _mp_c, _mp_a = _mp_setup.comm_fields(_mp_comm)
assert (_mp_in.index, _mp_c.index, _mp_a.index) == (1, 2, 3), \
    "CANCEL left, ACCEPT right: both carry ESC (fix 51's finding 3)"
assert set(_mp_setup.buttons(_mp_online)) == {
    "network", "online", "hotseat", "cancel", "start", "load", "join", "comm"}


def _mp_s8(t):
    raw = t.encode("latin-1")
    return bytes([len(raw)]) + raw


def _mp_block(code, body):
    return b"MPLY" + bytes([1, code]) + body


_mp_online_blk = _mp_block(2, _mp_st.pack("<hB", 1, 30) + _mp_s8("ATZ") +
                           b"\x00" + _mp_st.pack("<hh", 3, 2))
_mp_list_blk = _mp_block(14, _mp_st.pack("<hB", 5, 1) +
                         _mp_st.pack("<hhhB", 1, 1, 2, 1) + _mp_s8("Game A"))
_mp_hot_blk = _mp_block(5, _mp_st.pack("<bhhhh", 2, 1, 1, 2, 3) +
                        bytes([3, 4]) + _mp_s8("Ruler") + _mp_s8("Race"))
for _mp_blk, _mp_phase in ((_mp_online_blk, "online"),
                           (_mp_list_blk, "join_list"),
                           (_mp_hot_blk, "hotseat")):
    _mp_g = _mp_ns.SimpleNamespace()
    assert _mp_b.parse(_mp_g, _mp_blk + b"zz", 0) == len(_mp_blk), _mp_phase
    assert _mp_g.multiplayer["phase"] == _mp_phase
    _mp_g2 = _mp_ns.SimpleNamespace()
    assert _mp_b.parse(_mp_g2, _mp_blk[:-1], 0) == 0 and \
        _mp_g2.multiplayer is None, _mp_phase
_mp_g = _mp_ns.SimpleNamespace()
_mp_b.parse(_mp_g, _mp_online_blk, 0)
assert _mp_b.endpoint(_mp_g) == "ATZ" and _mp_b.endpoint_max(_mp_g) == 29, \
    "one below the input's 30: the engine's commit writes max + 1 bytes"
_mp_src = io.open(os.path.join(os.path.dirname(SCREENS_DIR), "core",
                               "game_state.py"), encoding="utf-8").read()
assert _mp_src.index("hofblocks.parse(gs, data, pos)") < \
    _mp_src.index("mpblocks.parse(gs, data, pos)"), "MPLY is written LAST"
_mp_scr_src = io.open(os.path.join(SCREENS_DIR, "multiplayer", "screen.py"),
                      encoding="utf-8").read()
assert "max_len=59" in _mp_scr_src, \
    "the chat line: at most 59, the engine's buffer is 60 (finding 1)"
assert "doc/ext_multiplayer_state.patch" in _sd_vc.LOCAL_PATCHES
_mp_nmarks = _sd_marks_named("multiplayer", ("screen.py",))
from core import screen_names as _mp_sn
assert all(_mp_sn.SCREENS[i][1] == "multiplayer"
           for i in (15, 16, 17, 21, 22, 37, 41))
ok(f"the multiplayer setup reads its type and buttons off its own field "
   f"list; open fix 51's MPLY parses whole or not at all for its steps; the "
   f"endpoint and chat stay inside the engine's buffers ({_mp_nmarks} marks)")

# 2. ROUTING, THE BANNER, THE VIEWS.
import hud_evidence as _mp_he
_mp_app = _mp_he.make_app(1920, 1080)
_mp_d = _mp_app.dispatcher
_mp_gs = _mp_he.galaxy_state()
_mp_gs.current_screen = 51            # the stale id race selection leaves
_mp_d.switch_to("empire_identity", _mp_gs, lock_ids=[51])
_mp_b.parse(_mp_gs, _mp_hot_blk, 0)
_mp_gs.fields = [_mp_F(1, 0), _mp_F(2, 0), _mp_F(3, 0x1B)]
_mp_d.update_from_game(_mp_gs)
assert _mp_d.active_name == "multiplayer", _mp_d.active_name
_mp_gs.multiplayer = None
_mp_d.update_from_game(_mp_gs)
assert _mp_d.active_name == "select_race", "without MPLY the id decides"
# the Flag Screen with green taken: seven tiles on their grid
from core import injection as _mp_inj
_mp_tiles = [_mp_F(i + 1, 0, x, y, 83, 98, 0)
             for i, (x, y) in enumerate(_mp_inj.BANNER_GRID) if i != 2]
assert _mp_inj.is_banner_dialog(_mp_tiles)
_mp_sent = []
_mp_cl = _mp_ns.SimpleNamespace(activate_field=lambda i: _mp_sent.append(i))
assert _mp_inj.click_banner(_mp_cl, _mp_tiles, "green",
                            ["red", "yellow", "green", "silver", "blue",
                             "brown", "purple", "orange"])
assert _mp_sent == [1], ("the first free tile", _mp_sent)
# no module but F12 turns the App into the original's picture (a screen
# did, work order 188: Empire Identity after a failed chain)
import glob as _mp_glob
for _mp_path in _mp_glob.glob(os.path.join(SCREENS_DIR, "*", "*.py")) + \
        _mp_glob.glob(os.path.join(os.path.dirname(SCREENS_DIR), "core",
                                   "*.py")):
    _mp_text = io.open(_mp_path, encoding="utf-8").read()
    assert "render_mode = \"original\"" not in _mp_text, _mp_path
# a step's view: its options and buttons are its own fields
from screens.multiplayer import mpdraw as _mp_draw
_mp_scr = _mp_d.screens["multiplayer"]
_mp_scr.enter(None)
_mp_st2 = _mp_ns.SimpleNamespace(
    current_screen=22, fields=[_mp_F(1, 0), _mp_F(5, 0x1B)], player_raw=[])
_mp_b.parse(_mp_st2, _mp_list_blk, 0)
_mp_c2, _ = _mp_draw.content(_mp_scr, _mp_st2)
assert [a[1].index for _l, a in _mp_c2["options"]] == [1] and \
    _mp_c2["buttons"][0][1][1].index == 5
_mp_rects = _mp_draw.draw_step(pygame.Surface((1920, 1080)), _mp_scr,
                               _mp_st2)
assert {f.index for _r, f in _mp_rects.values()} == {1, 5}
ok("MPLY routes to the multiplayer screen over a stale id and ends a "
   "sub-screen's lock; a taken banner colour picks the first free tile; each "
   "step's view binds its options and buttons to its own fields")
