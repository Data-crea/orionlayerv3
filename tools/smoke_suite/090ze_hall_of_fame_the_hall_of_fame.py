# smoke-suite area: hall_of_fame
#
# Part of the OrionLayer smoke suite — 090ze_hall_of_fame_the_hall_of_fame.py.
# `tools/smoke_test.py` executes this file, and every other module in
# tools/smoke_suite/, in file-name order and in ONE namespace. Do not
# import this file; it is not a module.
#
# The 2 check(s) it holds:
#   - open fix 50's HOFM block parses whole or not at all, LAST; the Hall of Fame claims 14 only with it and draws ten numbered rows, no header, at 1920 and 3840
#   - the Hall of Fame's one way out is its full-screen ESC field (a click or ESC), no other key reaches the game (never the file-resetting 'C'); the main menu resolves each button by hotkey, so HALL OF FAME is never QUIT


# ── THE HALL OF FAME (work order 188 Part 6, open fix 50) ────────
import types as _hf_ns
from core import hofblocks as _hf_b
import hud_evidence as _hf_he

_hf_rows = [{"record": 9 - i, "score": 1600 - 110 * i, "difficulty": i % 5,
             "name": f"Name {i + 1}", "race": "Race",
             "difficulty_word": "Level"} for i in range(10)]
_hf_blk = _hf_b.build(_hf_rows, flash=6)
_hf_g = _hf_ns.SimpleNamespace()
assert _hf_b.parse(_hf_g, _hf_blk + b"zz", 0) == len(_hf_blk)
assert [r["score"] for r in _hf_g.hall_of_fame["rows"]] == \
    [1600 - 110 * i for i in range(10)] and \
    _hf_g.hall_of_fame["flash"] == 6 and \
    _hf_g.hall_of_fame["file_version"] == 0x82
for _hf_bad in (_hf_blk[:-1], b"HOFX" + _hf_blk[4:],
                _hf_blk[:4] + b"\x02" + _hf_blk[5:]):
    _hf_g2 = _hf_ns.SimpleNamespace()
    assert _hf_b.parse(_hf_g2, _hf_bad, 0) == 0 and \
        _hf_g2.hall_of_fame is None
_hf_src = io.open(os.path.join(os.path.dirname(SCREENS_DIR), "core",
                               "game_state.py"), encoding="utf-8").read()
assert _hf_src.index("turnpopup.parse(gs, data, pos)") < \
    _hf_src.index("hofblocks.parse(gs, data, pos)"), "HOFM is written LAST"
_hf_counts = {}
for _hf_size in ((1920, 1080), (3840, 2160)):
    _hf_app = _hf_he.make_app(*_hf_size)
    _hf_gs = _hf_he.stage(_hf_app, "hall_of_fame")
    _hf_scr = _hf_app.dispatcher.screens["hall_of_fame"]
    assert _hf_scr.claims(_hf_gs) and not _hf_scr.claims(
        _hf_ns.SimpleNamespace(hall_of_fame=None)), "claims only with HOFM"
    _hf_texts = []
    _hf_real = _hf_scr.style.render_text
    _hf_scr.style.render_text = lambda t, *a, **k: (
        _hf_texts.append(t), _hf_real(t, *a, **k))[1]
    try:
        _hf_scr.update(_hf_gs)
        _hf_scr.render(pygame.Surface(_hf_size))
    finally:
        _hf_scr.style.render_text = _hf_real
    for _hf_i in range(10):
        assert f"Name {_hf_i + 1}" in _hf_texts and \
            str(_hf_i + 1) in _hf_texts, (_hf_i, _hf_texts)
    assert not {"NAME", "RACE", "DIFFICULTY", "SCORE"} & set(_hf_texts), \
        "the original has no header row"
    _hf_counts[_hf_size] = len(_hf_texts)
# the marks, in the module and the status document
_hf_nmarks = _sd_marks_named("hall_of_fame", ("screen.py",))
assert "doc/ext_hall_of_fame.patch" in _sd_vc.LOCAL_PATCHES
from core import screen_names as _hf_sn
assert _hf_sn.SCREENS[14] == ("HALL_OF_FAME", "hall_of_fame")
ok(f"open fix 50's HOFM block parses whole or not at all, LAST; the Hall of "
   f"Fame claims 14 only with it and draws ten numbered rows, "
   f"no header, at 1920 and 3840 ({_hf_nmarks} marks)")

# 2. THE WAY OUT, and nothing else.
_hf_F = lambda i, x, y, x2, y2, hk: _hf_ns.SimpleNamespace(
    index=i, x=x, y=y, x_end=x2, y_end=y2, hotkey=hk, field_type=7)
_hf_fields = [_hf_F(0, 0, 0, 0, 0, 0)] + \
    [_hf_F(i + 1, 139, 131 + 29 * i, 155, 153 + 29 * i, 0) for i in range(10)] \
    + [_hf_F(11, 0, 0, 639, 479, 0x1B), _hf_F(12, -1, -1, -1, -1, ord("C"))]
_hf_sent = []
_hf_app.client = _hf_ns.SimpleNamespace(
    state=_hf_ns.SimpleNamespace(fields=_hf_fields),
    activate_field=lambda i: _hf_sent.append(("act", i)),
    send_key=lambda k: _hf_sent.append(("key", k)),
    inject_key=lambda k: _hf_sent.append(("key", k)))
_hf_app.connected = True
_hf_scr.handle_click(100, 100)
_hf_scr.handle_key_event(_hf_ns.SimpleNamespace(key=pygame.K_ESCAPE,
                                                unicode="\x1b"))
for _hf_k, _hf_u in ((pygame.K_c, "c"), (pygame.K_RETURN, "\r")):
    assert _hf_scr.handle_key_event(_hf_ns.SimpleNamespace(
        key=_hf_k, unicode=_hf_u)) is True
_hf_scr.handle_key(pygame.K_c)
assert _hf_sent == [("act", 11), ("act", 11)], _hf_sent
# the main menu: a button is its own field by hotkey and rectangle — with
# no CONTINUE save the list shifts, and HALL OF FAME's old 5 is QUIT
_hf_mm = _hf_app.dispatcher.screens["main_menu"]
_hf_menu = [_hf_F(0, 0, 0, 0, 0, 0)]
for _hf_n, (_hf_hk, _hf_r) in _hf_mm.BUTTON_FIELDS.items():
    if _hf_n != "continue":
        _hf_menu.append(_hf_F(len(_hf_menu), *_hf_r, _hf_hk))
_hf_hof = _hf_mm.button_field("hall_of_fame", _hf_menu)
assert _hf_hof is not None and _hf_hof.index == 4 and \
    _hf_mm.button_field("quit", _hf_menu).index == 5 and \
    _hf_mm.button_field("continue", _hf_menu) is None
ok("the Hall of Fame's one way out is its full-screen ESC field (a click or "
   "ESC), no other key reaches the game (never the file-resetting 'C'); the "
   "main menu resolves each button by hotkey, so HALL OF FAME is never QUIT")
