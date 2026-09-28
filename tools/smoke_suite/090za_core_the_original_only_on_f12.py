# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 090za_core_the_original_only_on_f12.py.
# `tools/smoke_test.py` executes this file, and every other module in
# tools/smoke_suite/, in file-name order and in ONE namespace. Do not
# import this file; it is not a module.
#
# The 2 check(s) it holds:
#   - the original only on F12 (work order 188, Stage 1): none of the six paths of 187-original-visibility, nor a native box's crop (4b), presents a native frame without F12 — each holds with the F12 notice; F12 still shows the picture
#   - the flash rule everywhere: every native frame without F12 is a flash (frametrace, the App's own count, the walks' verdict), the notice is drawn from the HD string file and marked


# ── THE ORIGINAL ONLY ON F12 (work order 188, Part 1) ─────────────
#
# Data's rule (work order 187): the player never sees any part of the
# original picture unless he presses F12. `doc/briefs/187-original-
# visibility.md` ("Work order 187, Part 6 — where the original can still
# show without F12") names six paths; work order 188 found a seventh way
# the game's pixels reached the window — a native box CROPPED into an HD
# panel (`screens/fleets/fltbox`, the map's confirmation, the Leaders
# popup) — filed as 4b. Each path is driven through the gate as the App
# asks it (`handover.decide_for`), with the state that path has.
import types as _of_ns
from core import handover as _of_ho
from core import f12notice as _of_fn
from core import frametrace as _of_ft


def _of_app(gate):
    return _of_ns.SimpleNamespace(
        _handover=gate,
        client=_of_ns.SimpleNamespace(state=None, stats={}),
        dispatcher=_of_ns.SimpleNamespace(overlay_name="", active_name=""))


class _OfTop:
    def __init__(self, name, modal=False, box=False, reason=""):
        self.name, self._m, self._b, self._r = name, modal, box, reason

    def handover_is_modal(self):
        return self._m

    def modal_is_box(self):
        return self._b

    def fallback_reason(self):
        return self._r


def _of_walk(gate, screen, live, top, want, kind, n=60, sig=None):
    """`n` snapshots of one path; what each frame would present."""
    app = _of_app(gate)
    out = []
    for i in range(n):
        app.client.state = _of_ns.SimpleNamespace(
            current_screen=screen,
            fields=[_of_ns.SimpleNamespace(index=k + 1, field_type=0, x=k,
                                           y=0, x_end=k + 9, y_end=9)
                    for k in range(live)])
        app.client.stats = {"state": 1000 + i}
        app.dispatcher.active_name = top.name if top else ""
        shown = _of_ho.decide_for(app, want, kind, top)
        out.append("net" if shown else ("notice" if gate.notice is not None
                                        else ("hold" if gate.holding
                                              else "hd")))
    return out


# Each path as `(name, screen, live, top, want, kind)`: the state the
# inventory says it has.
_OF_PATHS = [
    # 1. an id with no HD screen, a list to answer (the combat choice, 12)
    ("1 no HD screen, answerable", 12, 3, None, True, _of_ho.NO_SCREEN),
    # 2. the same with an EMPTY list, past EMPTY_HOLD (a long silent id)
    ("2 no HD screen, empty list", 39, 0, None, True, _of_ho.NO_SCREEN),
    # 3. a known screen declining its id is the dispatcher's no-screen
    #    fallback — the same way in as 1, with the declining screen's id
    ("3 a screen declines its id", 1, 4, None, True, _of_ho.NO_SCREEN),
    # 4. a box over an HD page (GAME_BOX: the designer's warning)
    ("4 a box over an HD page", 3, 1,
     _OfTop("ship_design", modal=True, box=True), True, _of_ho.HAND_OVER),
    # 5. a box over a screen with a modal net (the colony-base choice),
    #    and the net's full hold for an unknown list
    ("5 a net's box", 0, 5, _OfTop("galaxy_map", modal=True, box=True),
     True, _of_ho.HAND_OVER),
    ("5 a net's unknown list", 10, 2, _OfTop("main_menu", modal=True),
     True, _of_ho.HAND_OVER),
    # 6. a known screen that cannot vouch (extractor files absent)
    ("6 a screen cannot vouch", 53, 8,
     _OfTop("research_select", reason="run tools/setup.py"), True,
     _of_ho.HAND_OVER),
]
_of_seen = {}
for _of_p in _OF_PATHS:
    _of_g = _of_ho.Gate()
    _of_pres = _of_walk(_of_g, *_of_p[1:])
    assert "net" not in _of_pres, (_of_p[0], _of_pres)
    _of_seen[_of_p[0]] = _of_pres
    # and the counter-test: the same path through a gate without Stage 1
    # DOES present the picture — so the check can fail
    _of_back = _of_walk(_of_ho.Gate(stage1=False), *_of_p[1:])
    assert "net" in _of_back, (_of_p[0], "the path never reached the "
                               "picture: the check measures nothing")
# what each path shows instead: the notice where the game waits for an
# answer, the plain hold where it has none (path 2)
assert _of_seen["1 no HD screen, answerable"][0] == "notice"
assert set(_of_seen["2 no HD screen, empty list"]) == {"hold"}
assert _of_seen["4 a box over an HD page"][-1] == "notice"
assert _of_seen["5 a net's box"].index("notice") == _of_ho.MODAL_SETTLE
assert _of_seen["5 a net's unknown list"].index("notice") == _of_ho.HOLD
assert _of_seen["6 a screen cannot vouch"].index("notice") == _of_ho.HOLD
# F12 is the player's own mode: the picture, never held, no notice
_of_g = _of_ho.Gate()
assert set(_of_walk(_of_g, 12, 3, None, True, _of_ho.F12, n=5)) == {"net"}
assert _of_g.notice is None and not _of_g.holding
# a hand-over whose data never came is still COUNTED as a failure
_of_g = _of_ho.Gate()
_of_walk(_of_g, 53, 8, _OfTop("research_select"), True, _of_ho.HAND_OVER)
assert _of_g.failures == 1 and _of_g.notices == 1
# the notice names what the game waits for: the screen's own reason, else
# the engine's screen name and id
assert _of_fn.what_for("hand_over", 53, _OfTop("x", reason="R.")) == "R."
assert _of_fn.what_for("no_screen", 12) == "NEXT_TURN (12)"

# 4b. A NATIVE BOX'S CROP. With the box's pixels in a colour nothing HD
# draws, the box's HD panel carries none of them, and no button answers
# blind (the question is not on the wire until open fix 29).
from screens.fleets import fltbox as _of_fb
from core import gamebox as _of_gb
assert _of_fb.SHOW_CROP is False
_of_box = _of_gb.CONFIRMATION
_of_fbscr = _of_ns.SimpleNamespace(
    app=_of_ns.SimpleNamespace(win_w=1920, win_h=1080, _note_labels={}),
    layout=_of_ns.SimpleNamespace(scale=1.0), style=app.style,
    _view=_of_ns.SimpleNamespace(in_box=True, box=_of_box))
_of_state = _of_ns.SimpleNamespace(
    framebuffer=bytes([7]) * (640 * 480),
    palette=[(250, 0, 250)] * 256)
_of_surf = pygame.Surface((1920, 1080))
_of_surf.fill((0, 0, 0))
assert _of_fb.draw(_of_surf, _of_fbscr, _of_state)
_of_px = pygame.surfarray.array3d(_of_surf)
_of_magenta = int(((_of_px[:, :, 0] == 250) & (_of_px[:, :, 1] == 0) &
                   (_of_px[:, :, 2] == 250)).sum())
assert _of_magenta == 0, f"{_of_magenta} pixels of the game's box shown"
assert int((_of_px.sum(axis=2) > 0).sum()) > 10000, "the notice drew nothing"
assert _of_fb.button_rects(_of_fbscr) == []
# every screen that draws a native box goes through `fltbox` — the map's
# confirmation and the Leaders popup included — and no screen crops the
# framebuffer itself
import glob as _of_glob
_of_crop = []
for _of_path in _of_glob.glob(os.path.join(SCREENS_DIR, "*", "*.py")):
    _of_src = io.open(_of_path, encoding="utf-8").read()
    for _of_n, _of_line in enumerate(_of_src.splitlines(), 1):
        _of_code = _of_line.split("#", 1)[0]
        if ("gamebox.crop(" in _of_code or "fb.subsurface(" in _of_code) \
                and not _of_path.endswith(os.path.join("fleets",
                                                       "fltbox.py")):
            _of_crop.append(f"{os.path.relpath(_of_path, SCREENS_DIR)}:"
                            f"{_of_n}")
for _of_c in _of_crop:
    _of_file = os.path.join(SCREENS_DIR, _of_c.split(":")[0])
    _of_src = io.open(_of_file, encoding="utf-8").read()
    assert "fltbox.SHOW_CROP" in _of_src, (
        f"{_of_c} crops the game's picture outside fltbox and is not gated "
        f"by fltbox.SHOW_CROP — the original outside F12")
ok("the original only on F12 (work order 188, Stage 1): none of the six "
   "paths of 187-original-visibility, nor a native box's crop (4b), "
   "presents a native frame without F12 — each holds with the F12 notice; "
   "F12 still shows the picture")


# ── THE FLASH RULE EVERYWHERE ────────────────────────────────────
# 180 A2 allowed one native frame: an id with no HD screen showing a list
# to answer. Since work order 188 every native frame without F12 is a
# flash — in the transition summary, in the App's own count of every
# presented frame (not only the walks' recorded transitions), and in the
# walks' exit code.
_of_frames = [
    {"t": 0.0, "source": "net", "kind": "no_screen", "live": 3, "hd": "",
     "reason": "", "screen": 12},
    {"t": 0.1, "source": "net", "kind": "f12", "live": 3, "hd": "",
     "reason": "", "screen": 12},
    {"t": 0.2, "source": "hold", "kind": "no_screen", "live": 3, "hd": "",
     "reason": "", "screen": 12, "notice": True},
    {"t": 0.3, "source": "hd", "kind": "", "live": 3, "hd": "galaxy_map",
     "reason": "", "screen": 0},
]
_of_sum = _of_ft.summarise(_of_frames)
assert _of_sum["flash_total"] == 1 and _of_sum["notice_total"] == 1, _of_sum
import inspect as _of_inspect
import main as _of_main
_of_render = _of_inspect.getsource(_of_main.App._render)
assert 'self.native_frames["f12" if self._net_kind == frametrace.F12' in \
    _of_render.replace("\n", " ").replace("  ", " ") or \
    "native_frames[" in _of_render, "the App counts every native frame"
assert "self._notice_view.render(" in _of_render
_of_close = _of_inspect.getsource(sys.modules.get("livedrive") or
                                  __import__("livedrive")).split(
    "def close(")[1]
assert "native_frames" in _of_close, "every live run reports the count"
for _of_tool in ("flash_walk.py", "design_walk.py", "audience_walk.py"):
    _of_src = io.open(os.path.join(os.path.dirname(SCREENS_DIR), "tools",
                                   _of_tool), encoding="utf-8").read()
    assert 'closed["native_frames"].get("without_f12")' in _of_src, _of_tool
# the words: the HD string file, the player's mod can replace them; the
# marking in module, status document and here
_of_labels = json.load(io.open(os.path.join(
    os.path.dirname(SCREENS_DIR), "assets", "shared", "fallback",
    "labels.json"), encoding="utf-8"))
assert _of_labels.get("notice_answer") == "F12 to answer"
assert _of_fn.words(_of_labels)[1] == "F12 to answer"
assert _of_fn.words({}) == (_of_fn.DEFAULTS["notice_waiting"],
                            _of_fn.DEFAULTS["notice_answer"])
assert "HD EXTENSION `f12_notice`" in (_of_fn.__doc__ or "")
assert "HD EXTENSION `f12_notice`" in io.open(os.path.join(
    os.path.dirname(SCREENS_DIR), "v3_projektstatus.md"),
    encoding="utf-8").read()
# the panel draws on a held frame without accumulating: two renders of the
# same notice give the same pixels
_of_s = pygame.Surface((960, 540))
_of_s.fill((40, 80, 120))
_of_nv = _of_fn.Notice()
_of_nv.render(_of_s, app.style, _of_labels, "NEXT_TURN (12)")
_of_a = pygame.image.tostring(_of_s, "RGB")
_of_nv.render(_of_s, app.style, _of_labels, "NEXT_TURN (12)")
assert pygame.image.tostring(_of_s, "RGB") == _of_a, "the notice accumulates"
_of_nv.reset(_of_s)
assert _of_s.get_at((5, 5))[:3] == (40, 80, 120), \
    "the held frame comes back undimmed when the notice ends"
ok("the flash rule everywhere: every native frame without F12 is a flash "
   "(frametrace, the App's own count, the walks' verdict), the notice is "
   "drawn from the HD string file and marked")
