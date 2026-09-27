# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 090w_core_research_entry_timing.py.
# `tools/smoke_test.py` executes this file, and every other module in
# tools/smoke_suite/, in file-name order and in ONE namespace. Do not
# import this file; it is not a module.
#
# The 1 check(s) it holds:
#   - the research entry timing is off unless switched on and then wraps
#     nothing; on, it splits an entry into phases that add up to the whole


# ── THE RESEARCH ENTRY TIMING (work order 184, part 1) ─────────
#
# Work order 184 measures before it optimises, and this is the measuring
# tool: `core/entrytiming.py`, switched on by `ORIONLAYER_ENTRY_TIMING`.
# Two things must keep holding. OFF, it costs nothing — not "one test per
# frame" but NOTHING: `open` returns None and no method of the app, its
# client or a screen is replaced, so the product's loop is the loop it
# always was. ON, it splits one entry — click, switch, the wait for the
# list, the first frame — into phases that are CONSECUTIVE: (a)+(b)+(c)+
# d_ready+(e) is the time from the click's frame to the panel's flip, by
# construction, so a phase table can never add up to more or less than
# what the player waited. Driven here through a stand-in app on the same
# three wrapped paths the real one has: the send, the message, the frame.
import types as _et_ns
from core import entrytiming as _et
from core.wire_protocol import MSG_FIELDS as _ET_F, MSG_STATE as _ET_S
from core.wire_protocol import MSG_VISUAL as _ET_V


class _EtClient:
    def __init__(self):
        self.state = _et_ns.SimpleNamespace(current_screen=0, fields=[],
                                            framebuffer=b"")
        self.inbox = []

    def _send_message(self, t, p=b""):
        return None

    def _handle_message(self, t, flags, payload):
        kind, value = payload
        if kind == "screen":
            self.state.current_screen = value
        elif kind == "fields":
            self.state.fields = list(range(value))
        elif kind == "visual":
            self.state.framebuffer = value


class _EtScreen:
    GAME_SCREEN_ID = 36
    READY_STATE = "ok"

    def __init__(self):
        self.state = "waiting"
        self.calls = []

    def enter(self, game_state=None):
        self.calls.append("enter")
        self.update(game_state)

    def update(self, game_state=None):
        self.calls.append("update")
        if len(getattr(game_state, "fields", None) or []) > 1:
            self.state = "ok"

    def render(self, surface):
        self.calls.append("render")

    def on_resize(self):
        pass


def _et_app():
    app = _et_ns.SimpleNamespace()
    app.client = _EtClient()
    app.win_w, app.win_h = 1920, 1080
    app._handover = _et_ns.SimpleNamespace(holding=False)
    app._surface_hd = True
    scr = _EtScreen()
    d = _et_ns.SimpleNamespace(screens={"research_change": scr},
                               overlay_name="", active_name="galaxy_map")
    d.top = scr
    app.dispatcher = d
    app.inputs = []

    def handle_events():
        for send in app.inputs:
            app.client._send_message(0x80, b"")
        app.inputs = []

    def update():
        for msg in app.client.inbox:
            app.client._handle_message(*msg)
        app.client.inbox = []
        st = app.client.state
        if st.current_screen == 36 and d.overlay_name != "research_change":
            d.overlay_name = "research_change"
            scr.enter(st)
        elif d.overlay_name == "research_change":
            scr.update(st)

    def render():
        if d.overlay_name:
            scr.render(None)
    app._handle_events, app._update, app._render = (handle_events, update,
                                                    render)
    return app, scr


# OFF: nothing built, nothing replaced.
_et_off, _et_off_scr = _et_app()
_et_before = (_et_off._handle_events, _et_off._update, _et_off._render,
              _et_off.client._send_message, _et_off.client._handle_message,
              _et_off_scr.enter, _et_off_scr.update, _et_off_scr.render)
assert _et.EntryTiming.open(_et_off, environ={}) is None, "on by default"
assert (_et_off._handle_events, _et_off._update, _et_off._render,
        _et_off.client._send_message, _et_off.client._handle_message,
        _et_off_scr.enter, _et_off_scr.update, _et_off_scr.render) == \
    _et_before, "the timing replaced a method while it was OFF"
# And main.App asks for it in exactly one place, its constructor — no line
# of the loop tests for it (the hooks are installed by wrapping).
_et_main_src = io.open(os.path.join(os.path.dirname(SCREENS_DIR), "main.py"),
                       encoding="utf-8").read()
assert _et_main_src.count("_entry_timing") == 1 and \
    "entrytiming.EntryTiming.open(self)" in _et_main_src, (
        "main.App refers to the entry timing outside its one line")

# ON: one entry through the three paths.
_et_on, _et_scr = _et_app()
_et_t = _et.EntryTiming.open(_et_on, environ={_et.ENV: "1"})
assert _et_t is not None and _et_on._render is not _et_before[2]
_et_on.inputs = ["click"]                     # the player's click
_et_on._handle_events()
_et_on._update()
_et_on._render()
assert _et_t._pending is not None and _et_t._pending["by_input"], \
    "a send while an input was handled was not taken as the click"
_et_on.client.inbox = [(_ET_S, 0, ("screen", 36)), (_ET_F, 0, ("fields", 0)),
                       (_ET_V, 0, ("visual", b"map"))]
for _ in range(3):                            # the switch, and the wait
    _et_on._handle_events()
    _et_on._update()
    _et_on._render()
    _et_on.client.inbox = []
assert _et_t.entries == [] and _et_t._entry is not None, \
    "the entry ended before the screen had its list"
_et_on.client.inbox = [(_ET_S, 0, ("screen", 36)), (_ET_F, 0, ("fields", 35)),
                       (_ET_V, 0, ("visual", b"panel"))]
_et_on._handle_events()
_et_on._update()
_et_on._render()
assert len(_et_t.entries) == 1, _et_t.entries
_et_rec = _et_t.entries[0]
assert _et_rec["reached"] and _et_rec["first_after_start"] \
    and _et_rec["by_input"] and _et_rec["target"] == "research_change"
assert _et_rec["snaps_c"] == 2 and _et_rec["snaps_b"] == 0, _et_rec
assert [n for _t, n in _et_rec["fields"]] == [0, 35], _et_rec["fields"]
assert len(_et_rec["visuals"]) == 2 and \
    _et_rec["visuals"][0][1] != _et_rec["visuals"][1][1]
assert set(_et_rec["prep"]) >= {"enter", "update", "render"}, _et_rec["prep"]
_et_sum = sum(_et_rec[k] for k in ("a_ms", "b_ms", "c_ms", "d_ready_ms",
                                   "e_ms"))
assert abs(_et_sum - _et_rec["total_ms"]) < 0.05, (
    f"the phases add up to {_et_sum:.3f} ms, the entry took "
    f"{_et_rec['total_ms']:.3f} ms — they are not consecutive")
# The enter ran inside (c) and is not counted twice: `d_ms` is its own sum.
assert all(v >= 0 for k, v in _et_rec.items() if k.endswith("_ms")), _et_rec
# A SECOND entry is "later", and a left screen ends an entry unreached.
_et_on.dispatcher.overlay_name = ""
_et_scr.state = "waiting"
_et_on.client.inbox = [(_ET_S, 0, ("screen", 0)), (_ET_F, 0, ("fields", 23))]
_et_on._update()
_et_on.client.inbox = [(_ET_S, 0, ("screen", 36)), (_ET_F, 0, ("fields", 0))]
_et_on._update()
_et_on.client.inbox = [(_ET_S, 0, ("screen", 0))]
_et_on._update()
assert len(_et_t.entries) == 2 and not _et_t.entries[1]["reached"] \
    and not _et_t.entries[1]["first_after_start"], _et_t.entries[1:]
ok("the research entry timing is off unless switched on and then wraps "
   "nothing; on, it splits an entry into phases that add up to the whole")
