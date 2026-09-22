# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 006_core_overlay_layer_open_render_route_auto.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (92 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 3 check(s) it holds:
#   - overlay layer (open/render/route/auto-close)
#   - widgets (ListView scroll/select/keys, TextInput)
#   - struct specs (star, ship_icon, ship)


# ── Overlay layer ──
from core.screen_base import ScreenBase

class FakeQueuePopup(ScreenBase):
    SCREEN_NAME = "_fake_popup"
    GAME_SCREEN_ID = 25          # SCREEN_QUEUE_POPUP
    IS_OVERLAY = True

    def enter(self, game_state=None):
        self.active = True
        self.boxes = []

    def render(self, srf):
        pass

d.register("_fake_popup", FakeQueuePopup(app))
d.switch_to("select_race")
parent = d.active
d.switch_to("_fake_popup")           # routes to open_overlay
assert d.active is parent, "overlay must not replace parent"
assert d.overlay_name == "_fake_popup"
assert d.top is d.overlay
d.render(surf)                       # parent + dim + overlay
d.route_click(960, 540)              # goes to overlay, no crash
d.route_motion(960, 540)

class GSPopup:
    current_screen = 25
assert d.update_from_game(GSPopup()) is True
assert d.overlay_name == "_fake_popup", "stays open on its ID"

class GSBack:
    current_screen = 51
d.update_from_game(GSBack())
assert d.overlay is None, "overlay closes when game leaves ID"
assert d.active_name == "select_race", "parent untouched"
ok("overlay layer (open/render/route/auto-close)")

# ── Widgets ──
from core.widgets import ListView, TextInput

picked = []
lv = ListView(columns=[("NAME", 0.5), ("POP", 0.25),
                       ("PROD", 0.25)],
              on_select=lambda i, row: picked.append(row))
lv.set_rows([(f"Colony {i}", str(i), str(i * 2))
             for i in range(40)])
lrect = pygame.Rect(100, 100, 500, 300)
lv.render(surf, lrect, app.style, app.layout)
assert lv._visible > 3
lv.handle_mousewheel(-1, 300, 200)
assert lv.scroll == 3, lv.scroll
row_y = lv._rows_area(app.layout).y + lv._row_h(app.layout) // 2
idx = lv.handle_click(150, row_y)
assert idx == lv.scroll and picked[-1][0] == f"Colony {idx}"
assert lv.handle_key(pygame.K_DOWN) is True
assert lv.selected == idx + 1
lv.render(surf, lrect, app.style, app.layout)

submitted = []
ti = TextInput(max_len=10, on_submit=submitted.append)
trect = pygame.Rect(100, 500, 400, 50)
ti.render(surf, trect, app.style, app.layout)

def key(k, ch=""):
    return pygame.event.Event(pygame.KEYDOWN, key=k, unicode=ch)

for ch in "Sol-3":
    assert ti.handle_key_event(key(0, ch))
assert ti.value == "Sol-3", ti.value
ti.handle_key_event(key(pygame.K_BACKSPACE))
assert ti.value == "Sol-"
ti.handle_key_event(key(pygame.K_RETURN))
assert submitted == ["Sol-"]
assert ti.handle_click(120, 510) is True   # focus hit
assert ti.handle_click(10, 10) is False    # defocus outside
ti.render(surf, trect, app.style, app.layout)
ok("widgets (ListView scroll/select/keys, TextInput)")

# ── Struct specs ──
import struct as _s
from core.structs import star, ship_icon
raw = bytearray(star.SIZE)
raw[0:4] = b"Sol\x00"
_s.pack_into("<h", raw, 15, 142)
_s.pack_into("<h", raw, 17, 377)
raw[19] = 2
_s.pack_into("<b", raw, 20, 3)
raw[22] = 2
raw[159] = 7
s = star.parse(bytes(raw))
assert (s.name, s.x, s.y, s.owner, s.system_special) == \
    ("Sol", 142, 377, 3, 7)
ic = ship_icon.parse(_s.pack("<6h", 4, 1, 9, 5, 250, 310))
assert (ic.star_idx, ic.stack_slot, ic.x, ic.y) == (9, 5, 250, 310)
# s_ship_data: offsets confirmed by compiling orion2.h with its own
# pragma pack(1); sizeof must equal the sizes.h assert.
from core.structs import ship as _ship
assert _ship.SIZE == 0x81
sraw = bytearray(_ship.SIZE)
_s.pack_into("<b", sraw, 99, 3)          # owner
_s.pack_into("<b", sraw, 100, 1)         # status = in transit
_s.pack_into("<hhh", sraw, 101, 10042, 300, 250)
sv = _ship.parse(bytes(sraw))
assert (sv.owner, sv.status, sv.location, sv.x, sv.y) == \
    (3, 1, 10042, 300, 250)
# Encoded location: moving/wormhole offsets strip back to the star
assert _ship.absolute_location(10042) == 42
assert _ship.absolute_location(20042) == 42
assert _ship.absolute_location(42) == 42
ok("struct specs (star, ship_icon, ship)")
