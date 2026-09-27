# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 080l_core_the_research_panel_is_prepared_while_it_waits.py.
# `tools/smoke_test.py` executes this file, and every other module in
# tools/smoke_suite/, in file-name order and in ONE namespace. Do not
# import this file; it is not a module.
#
# This one did NOT stand inside main(): it is work order 184 part 2, the
# research panel's first entry made as fast as its later ones.
#
# The 1 check(s) it holds:
#   - the research panel is prepared off screen while it waits: its READY
#     frame then builds no HUD panel and is byte for byte the frame drawn
#     cold — after a resize, a frame colour, the glass slider, a moved box
#     and other names; once per visit; a mod folder only at a start


# ── PREPARED WHILE THE GAME IS SILENT (work order 184) ──────────
#
# The first entry into change mode took 1.2 s at 1920 and 3.0 s at 3840
# against 0.7 and 0.9 s for every later one: the screen's first render
# built its HUD panels. And the engine is silent for ~550 ms after the
# switch whatever HD does (its input delay, `core/researchprepare.py`).
# So while the screen is WAITING it draws its panel ONCE onto a scratch
# surface; the READY frame then finds every panel cached.
#
# What is held, and why each is the rule rather than an instance:
# - THE READY FRAME AFTER A WAIT BUILDS NO HUD PANEL — no new "panel" key
#   in the blocks' cache and no shape for one — which is the gain, in a
#   form no timing threshold can make flaky.
# - IT IS BYTE FOR BYTE THE FRAME DRAWN COLD, with every cache emptied
#   and no preparation — so the preparation changes nothing the player
#   sees. And that equality is asserted AFTER each thing that could make
#   a prepared cache stale, done while the cache is warm: a resize, the
#   frame colour, the glass slider, a box somewhere else (what an F5 edit
#   does to a rect), other names (a language or a text resolver). A stale
#   entry would draw the old picture and fail the equality.
# - NOTHING OF IT REACHES THE WINDOW: while it waits, the screen still
#   draws nothing (`draws_this_frame`) — 080h compares the window with and
#   without the overlay pixel by pixel, and still passes with this in.
# - ONCE PER VISIT, and again on the next `enter`.
# - A MOD FOLDER changes only at a start: `usermod.init` has one caller,
#   `main.App.__init__`, and the caches are the process's own memory —
#   the preparation writes no file.
from core import researchprepare as _pp
from core import usermod as _pp_um
from core.hud import blocks as _pp_b, glass as _pp_g, raster as _pp_r
from core.hud import style as _pp_hs, tint as _pp_tint

_pp_count = [0]
_pp_shape = _pp_r.shape


def _pp_counted(*a, **k):
    _pp_count[0] += 1
    return _pp_shape(*a, **k)


def _pp_cold():
    _pp_b.clear()
    _pp_g.forget()
    _pp_r.clear_geometry()


class _PpNames:
    """Other names — what a language or a text resolver changes."""

    def __init__(self, inner):
        self._inner = inner
        self.state = inner.state

    def field_name(self, n):
        return "Q" + str(self._inner.field_name(n) or "")[::-1]

    def __getattr__(self, name):
        return getattr(self._inner, name)


def _pp_frame(prepared, mutate=None, names=None):
    """The READY frame's bytes, the HUD shapes it built, and the panel
    keys it added. `prepared`: through a WAIT (the preparation runs) on
    whatever the caches hold; else cold, entered with the list at once."""
    _dx_scr.app.client, _dx_scr.app.connected = _rs_client, True
    if prepared:
        _rs_client.state = _wt_empty_state
        _dx_scr.enter(_wt_empty_state)
        _dx_scr._names = names or derived(_dx_tn.TechNames)
        _dx_scr._wording = derived(_dx_bt.BillText)
        _dx_scr.update(_wt_empty_state)
        assert _dx_scr.state == "waiting" and _dx_scr._prepared, (
            _dx_scr.state, _dx_scr._prepared)
        assert _dx_scr.draws_this_frame() is False
        _pp_n = _pp_count[0]
        _dx_scr.update(_wt_empty_state)
        assert _pp_count[0] == _pp_n, "prepared twice in one visit"
    else:
        _pp_cold()
        _rs_client.state = _dx_state
        _dx_scr.enter(_dx_state)
        _dx_scr._names = names or derived(_dx_tn.TechNames)
        _dx_scr._wording = derived(_dx_bt.BillText)
    _rs_client.state = _dx_state
    _dx_scr.update(_dx_state)
    assert _dx_scr.state == "ok", _dx_scr.state
    if mutate is not None:
        mutate()
    _pp_keys = set(_pp_b._CACHE)
    _pp_n = _pp_count[0]
    _pp_s = pygame.Surface((_rs_app.layout.window_w, _rs_app.layout.window_h))
    _pp_s.fill((0, 0, 0))
    _dx_scr.render(_pp_s)
    _pp_new = [k for k in _pp_b._CACHE if k not in _pp_keys]
    return (pygame.image.tobytes(_pp_s, "RGB"), _pp_count[0] - _pp_n,
            [k for k in _pp_new if k[0] == "panel"])


def _pp_moved():
    _pp_box = next(b for b in _dx_scr.boxes
                   if b.style.get("skin") == "thin_border")
    _pp_box.screen_rect = _pp_box.screen_rect.move(37, 11)


_pp_tone = (_pp_tint._hue, _pp_tint._sat, _pp_tint._bright)
_pp_glass = _pp_g._value
_pp_size = (_rs_app.win_w, _rs_app.win_h, _rs_app.layout)
_pp_r.shape = _pp_counted
try:
    _pp_seen = []
    for _pp_what, _pp_change, _pp_mut, _pp_names in (
            ("as it is", None, None, None),
            ("a resize to 2576x1432", "resize", None, None),
            ("the frame colour", lambda: _pp_hs.set_tone(30, 0.6, 0.3),
             None, None),
            ("the glass slider", lambda: _pp_g.set_value(0.85), None, None),
            ("a box somewhere else", None, _pp_moved, None),
            ("other names", None, None, "other")):
        if _pp_change == "resize":
            _rs_app.win_w, _rs_app.win_h = 2576, 1432
            _rs_app.layout = Layout(2576, 1432)
            _dx_scr.on_resize()
        elif _pp_change is not None:
            _pp_change()
        _pp_nm = (lambda: _PpNames(derived(_dx_tn.TechNames))) \
            if _pp_names else (lambda: None)
        # WARM: whatever the previous case left in the caches, then a wait.
        _pp_warm, _pp_built, _pp_panels = _pp_frame(True, _pp_mut, _pp_nm())
        assert _pp_panels == [], (
            f"{_pp_what}: the READY frame after a wait built HUD panels "
            f"{_pp_panels} — the preparation did not serve it")
        _pp_cold_px, _pp_cold_built, _ = _pp_frame(False, _pp_mut, _pp_nm())
        assert _pp_cold_built > _pp_built, (
            f"{_pp_what}: the cold frame built {_pp_cold_built} shapes and "
            f"the prepared one {_pp_built} — the control proves nothing")
        assert _pp_warm == _pp_cold_px, (
            f"{_pp_what}: the prepared READY frame differs from the frame "
            f"drawn cold — a cache the preparation warmed is stale")
        _pp_seen.append(_pp_what)
    assert len(_pp_seen) == 6, _pp_seen
finally:
    _pp_r.shape = _pp_shape
    _pp_hs.set_tone(*_pp_tone)
    _pp_g.set_value(_pp_glass)
    _rs_app.win_w, _rs_app.win_h, _rs_app.layout = _pp_size
    _dx_scr.on_resize()
    _rs_client.state = _dx_state
    _dx_scr.enter(_dx_state)
    _dx_scr._names = derived(_dx_tn.TechNames)
    _dx_scr._wording = derived(_dx_bt.BillText)
    _dx_scr.update(_dx_state)
# THE MOD FOLDER: one caller, at the start; the preparation writes nothing.
_pp_calls = []
for _pp_dir in ("core", "screens"):
    for _pp_root, _pp_d, _pp_files in os.walk(os.path.join(
            os.path.dirname(SCREENS_DIR), _pp_dir)):
        for _pp_f in _pp_files:
            if _pp_f.endswith(".py"):
                _pp_t = io.open(os.path.join(_pp_root, _pp_f),
                                encoding="utf-8").read()
                if "usermod.init(" in _pp_t:
                    _pp_calls.append(_pp_f)
_pp_main = io.open(os.path.join(os.path.dirname(SCREENS_DIR), "main.py"),
                   encoding="utf-8").read()
assert _pp_calls == [] and _pp_main.count("usermod.init(") == 1, (
    _pp_calls, "a mod folder can change while the program runs — a warm "
    "cache would outlive it")
_pp_src = io.open(_pp.__file__, encoding="utf-8").read()
assert "open(" not in _pp_src and "save(" not in _pp_src, \
    "the preparation writes somewhere"
assert _pp_um.init.__module__ == "core.usermod"
ok("the research panel is prepared off screen while it waits: its READY "
   "frame then builds no HUD panel and is byte for byte the frame drawn "
   "cold — after a resize, a frame colour, the glass slider, a moved box "
   "and other names; once per visit; a mod folder only at a start")
