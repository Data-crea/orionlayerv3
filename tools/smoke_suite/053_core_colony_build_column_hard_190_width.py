# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 053_core_colony_build_column_hard_190_width.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (92 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 6 check(s) it holds:
#   - colony build column (hard 190 width, wrap + shrink, never truncates, all three markings name the
#   - glyph substitution mechanism + lore star names
#   - cursor size (the original's 4.4 % of screen height)
#   - editor overlay (help columns fit, S toggles the star field)
#   - pointer offset (one source, no raw get_pos outside core/mouse)
#   - main menu version line (drawn, right-aligned, one source)


# ── The markings on that column ──
# Three separate claims, three separate homes, and each one has to
# name what the original does instead: a label that records no
# deviation is a label, not a marking.
_cb_src = open(os.path.join(SCREENS_DIR, "colony_summary",
                            "colonybuild.py"), encoding="utf-8").read()
# The width condition transcribes a guarantee and deviates in the
# means. Both halves have to survive, and the line that settles it
# is fmtpara.cpp:567 — without that reference the claim is an
# assertion about the original that nobody can check.
_wc = _cfg.get("_width_condition_note", "")
assert "fmtpara.cpp:567" in _wc and "fmtpara.cpp:567" in _cb_src, \
    ("the width condition no longer cites the line that settles "
     "whether it is a transcription or a deviation")
assert "TRANSCRIPTION" in _wc and "DEVIATION" in _wc, \
    "the width condition's marking lost one of its two halves"
# The Buy control deviates twice. Naming only the label would
# leave drawing text where the original draws a sprite unmarked.
_bn = _cfg.get("_buy_note", "")
assert "DEVIATION 1" in _bn and "DEVIATION 2" in _bn, \
    "the Buy control's marking no longer names both deviations"
assert "E_Strings_(12)" in _bn and "SPRITE" in _bn.upper(), \
    ("the Buy marking no longer names what the original draws "
     "instead of text")
# The two-line box is the original's own budget, not our idea.
_bc = _cfg.get("_building_column_note", "")
assert "colsum.cpp:621" in _bc and "31" in _bc, \
    ("the building column no longer records that the original "
     "budgets two lines in the same box")
ok("colony build column (hard 190 width, wrap + shrink, never "
   "truncates, all three markings name their source)")

# ── Glyph substitution: mechanism, not one font's quirk ──
# This existed because the bundled Bank Gothic was a DEMO build
# that mapped 28 characters onto one watermark bitmap — including
# the DIGIT 4 and the parentheses a Galactic Lore star name is
# wrapped in. The font is now Aldrich (OFL), which substitutes
# nothing, so the assertions that named "(" and "4" would only
# test the artefact of a font we no longer ship.
#
# The machinery stays, because the substitution path is what
# makes a mod's own font safe, and because the DEMO font is one
# `mods/` override away from being back. Tested in both
# directions with stubs, so it holds whatever the shipped font is.
assert not app.style.blocked_glyphs(), \
    f"the shipped font substitutes glyphs: {sorted(app.style.blocked_glyphs())}"

class _StubFont:
    """Renders W, X, Y, Z as one identical bitmap, rest distinct."""
    def __init__(self, size): self.size = size
    def render(self, ch, aa, fg, bg=None):
        surf = pygame.Surface((10, 10))
        surf.fill((0, 0, 0) if ch in "WXYZ" else (ord(ch), 0, 0))
        return surf
    def get_height(self): return 10
    def get_ascent(self): return 8

def _stub_style(font_factory):
    cls = app.style.__class__
    class _S:
        _GLYPH_PROBE_SIZE = cls._GLYPH_PROBE_SIZE
        _GLYPH_COLLISION_MIN = cls._GLYPH_COLLISION_MIN
        _blocked = None
        get_font = staticmethod(font_factory)
        blocked_glyphs = cls.blocked_glyphs
        split_runs = cls.split_runs
    return _S()

# Positive direction: a colliding font IS detected. Without this,
# swapping to a clean font would leave the detector unexercised
# and free to break silently.
_dirty = _stub_style(_StubFont)
assert _dirty.blocked_glyphs() == set("WXYZ"), \
    sorted(_dirty.blocked_glyphs())
# And a group smaller than the threshold is NOT treated as a
# substitution — two glyphs may legitimately share a bitmap.
assert app.style._GLYPH_COLLISION_MIN >= 3

# Negative direction: a normal font reports nothing, so a
# licensed font stops splitting strings across two fonts.
_clean = _stub_style(lambda size: pygame.font.Font(None, size))
assert not _clean.blocked_glyphs()

# Runs alternate on the detected set, whatever it happens to be.
assert _dirty.split_runs("aWb") == \
    [(False, "a"), (True, "W"), (False, "b")]
assert _dirty.split_runs("abc") == [(False, "abc")]
# With nothing blocked, every string takes the single-font path.
assert app.style.split_runs("(Orion)") == [(False, "(Orion)")]
assert app.style.split_runs("") == []

# render_text must equal the plain render when nothing is
# substituted — the fallback path costs nothing on a clean font.
for _txt in ("(Orion)", "Regulus", "+14 (26)", "-1/base"):
    _a = app.style.render_text(_txt, 40, (255, 255, 255))
    _b = app.style.get_font(40).render(_txt, True, (255, 255, 255))
    assert _a.get_size() == _b.get_size(), _txt

# The font that ships must carry its licence next to it.
_font_dir = os.path.join(os.path.dirname(SCREENS_DIR),
                         "assets", "shared", "fonts")
_faces = [f for f in os.listdir(_font_dir)
          if f.lower().endswith((".ttf", ".otf"))]
assert _faces, "no font shipped"
assert any(f.upper().startswith(("OFL", "LICENSE"))
           for f in os.listdir(_font_dir)), \
    f"font shipped without a licence file: {_faces}"

# star_label itself mirrors MAINSCR::Get_Star_Name_: parentheses
# only for an omniscient player looking at an unvisited foreign
# system (HAROLD::s___s__00556ae4 = "(%s)").
if "galaxy_map" in d.screens:
    # owner 3: player 0 has no contact with them (only with 1),
    # so without lore this star stays unlabelled entirely.
    foreign = st.parse(mkstar("Orion", 100, 100, 2, 1, 3, 0b0))
    own = st.parse(mkstar("Sol", 100, 100, 2, 1, 0, 0b1))
    assert gmr.star_label(foreign, 0, gm._players, True) == "(Orion)"
    assert gmr.star_label(foreign, 0, gm._players, False) == ""
    assert gmr.star_label(own, 0, gm._players, True) == "Sol"
    # Visited beats lore: no parentheses once you have been there.
    visited = st.parse(mkstar("Orion", 100, 100, 2, 1, 3, 0b1))
    assert gmr.star_label(visited, 0, gm._players, True) == "Orion"
    # A contacted owner is named plainly even without lore.
    contacted = st.parse(mkstar("Vega", 100, 100, 2, 1, 1, 0b0))
    assert gmr.star_label(contacted, 0, gm._players, False) == "Vega"
ok("glyph substitution mechanism + lore star names")

# ── Cursor size follows the window ──
# The artwork is 4K-sized and used to be handed to SDL unscaled,
# so it stayed 96 px tall at every resolution — right at 2160,
# half again too large at 1440, twice too large at 1080. The
# fraction is the original's own: 21 of 480 lines.
from core import cursor as _cur

_src = (84, 96)
_sizes = {h: _cur.target_size(h, {}, _src)
          for h in (720, 1080, 1440, 2160, 2880)}
assert _sizes[1080][1] == 47 and _sizes[1440][1] == 63, _sizes
assert _sizes[2160][1] == 94, _sizes[2160]
# Monotonic, aspect preserved, and never upscaled past the master.
_heights = [_sizes[h][1] for h in sorted(_sizes)]
assert _heights == sorted(_heights), _heights
assert _sizes[2880] == _src, _sizes[2880]
for _h, (_w, _hh) in _sizes.items():
    assert abs(_w / _hh - _src[0] / _src[1]) < 0.03, (_h, _w, _hh)

# Loading and scaling the real asset must work headless; the
# re-apply on a resolution change is checked on the real App
# further down, where one actually exists.
_cur.reset()
_applied = _cur.apply(res, 1440, {})
assert _applied == _cur.target_size(1440, {}, _cur._source.get_size()), \
    _applied
assert _cur.apply(res, 1440, {"cursor": {"enabled": False}}) is None
ok("cursor size (the original's 4.4 % of screen height)")

# ── Editor overlay: text that cannot overlap itself ──
# The help sheet put descriptions at a fixed 160 reference pixels
# and one key label is 197 wide, so "Shift+Scroll / Alt+Scroll"
# printed straight through its own description at every
# resolution. Geometry now comes from the font, and the test asks
# the font too — a wider label or a bigger UI scale fails here
# instead of on screen.
from core.editor.constants import HELP_SECTIONS as _HS
from core.editor.overlay import help_geometry as _help_geom

for _w, _h in ((1920, 1080), (2560, 1440), (3440, 1440)):
    _L = Layout(_w, _h)
    _fr = app.style.get_font(_L.font_size(13))
    _desc_x, _content = _help_geom(_fr, _HS, _L.scale)
    for _sec, _rows in _HS:
        for _k, _d in _rows:
            assert _fr.size(_k)[0] < _desc_x, \
                f"{_w}x{_h}: key '{_k}' runs into its description"
            assert _desc_x + _fr.size(_d)[0] <= _content, \
                f"{_w}x{_h}: '{_d}' overflows the column"
    assert _content * 2 + int(60 * _L.scale) <= _w, \
        f"{_w}x{_h}: two help columns do not fit"

# The help sheet is where anyone looks up a key, so it has to
# carry the one key that is not the game's own. A name table
# copied into a second file drifts; this is the cheap guard.
_help_keys = [_k for _sec, _rows in _HS for _k, _d in _rows]
assert any("Home" in _k for _k in _help_keys), \
    "editor help no longer lists the home-system ping"

# S hides the star field while boxes are being placed. Duck-typed,
# so a screen without one is silently fine.
_gm = app.dispatcher.top
app.editor.active = True
if getattr(_gm, "_starfield", None) is not None:
    _was = _gm._starfield.enabled
    app.editor.handle_event(
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_s, mod=0))
    assert _gm._starfield.enabled is not _was, "S did not toggle"
    app.editor.handle_event(
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_s, mod=0))
    assert _gm._starfield.enabled is _was
app.editor.active = False
ok("editor overlay (help columns fit, S toggles the star field)")

# ── Pointer coordinates: one source ──
# In fullscreen the content is centred inside black bars, so the
# raw pointer position is in desktop space while every rect a
# screen draws is in window space. Windowed, the offset is zero —
# which is why a forgotten correction is invisible until F11, and
# then only for the one widget that forgot it. The galaxy map's
# nav hover forgot it, the editor re-derived the arithmetic by
# hand, and main.py had the only real copy.
from core import mouse as _mouse

_mouse.set_offset((160, 90))
assert _mouse.adjust(200, 130) == (40, 40), _mouse.adjust(200, 130)
_mouse.set_offset(None)
assert _mouse.adjust(200, 130) == (200, 130)

# The invariant, greppable: nothing outside core/mouse.py polls
# the pointer directly. A fourth copy is otherwise one session
# away, and it will fail in fullscreen only.
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Assembled at runtime so this scanner does not match itself —
# relying on an incidental substring to exclude it would break the
# day somebody rewords the line.
_needle = "pygame.mouse.get_" + "pos"
_offenders = []
for _dir, _subs, _files in os.walk(_root):
    if "__pycache__" in _dir or "/mods/" in _dir.replace("\\", "/"):
        continue
    for _f in _files:
        if not _f.endswith(".py"):
            continue
        _path = os.path.join(_dir, _f)
        if os.path.normpath(_path).endswith(
                os.path.join("core", "mouse.py")):
            continue
        with open(_path, "r", encoding="utf-8") as _fh:
            for _n, _line in enumerate(_fh, 1):
                if _needle in _line:
                    _offenders.append(
                        f"{os.path.relpath(_path, _root)}:{_n}")
assert not _offenders, \
    "polls the pointer without the fullscreen offset: " \
    + ", ".join(_offenders)
ok("pointer offset (one source, no raw get_pos outside core/mouse)")

# ── Main menu version line (bottom right, like the original) ──
# The number is maintained by hand because the Extension API does
# not report it, so the test guards the two ways that goes wrong:
# the box silently stops being drawn, and the literal gets pasted
# into a second file where nobody will find it again.
import json as _json
import numpy as _np
from core.config import ORION2RE_VERSION as _VER

_mm_dir = os.path.join(SCREENS_DIR, "main_menu")
with open(os.path.join(_mm_dir, "boxes.json")) as _fh:
    _mm_boxes = _json.load(_fh)
for _res_key, _entries in _mm_boxes.items():
    _vb = [b for b in _entries if b["name"] == "version_text"]
    assert len(_vb) == 1, f"{_res_key}: {len(_vb)} version boxes"
    _st = _vb[0].get("style", {})
    assert _st.get("skin") == "text", _st
    assert "{version}" in _st.get("label", ""), _st
    # Right-anchored and right-aligned, or it drifts away from the
    # button column the moment the window is not 16:9.
    assert _vb[0].get("anchor") == "right", _vb[0]
    assert _st.get("align") == "right", _st

d.switch_to("main_menu")
_mm = d.active
_vbox = [b for b in _mm.boxes if b.name == "version_text"]
assert len(_vbox) == 1, _mm.boxes
_vbox = _vbox[0]
assert _vbox.text == f"Version {_VER}", _vbox.text
# A runtime string must never reach boxes.json through the editor.
assert "{version}" in _vbox.to_dict()["style"]["label"]
assert _vbox.text not in _json.dumps(_vbox.to_dict())

_r = _vbox.screen_rect
_a = pygame.Surface((1920, 1080))
_mm.render(_a)
_vbox.text = ""
_b = pygame.Surface((1920, 1080))
_mm.render(_b)
_diff = (pygame.surfarray.array3d(_a).astype(int)
         - pygame.surfarray.array3d(_b).astype(int))
_ink = _np.abs(_diff).sum(axis=2)[_r.x:_r.right, _r.y:_r.bottom]
_cols = _np.nonzero(_ink.any(axis=1))[0]
assert _cols.size, "version text is not drawn"
# Right-aligned means the ink ends at the right edge and the box
# is wider than the string — the two halves of "it fits".
assert _r.w - 1 - _cols.max() <= 3, _cols.max()
assert _cols.min() > 4, _cols.min()
_mm._apply_version()

# One home for the number: nothing else in the tree spells it out.
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_strays = []
for _dir, _subs, _files in os.walk(_root):
    if "__pycache__" in _dir:
        continue
    for _f in _files:
        if not _f.endswith((".py", ".json")):
            continue
        _path = os.path.join(_dir, _f)
        if os.path.normpath(_path).endswith(
                os.path.join("core", "config.py")):
            continue
        with open(_path, "r", encoding="utf-8",
                  errors="replace") as _fh:
            for _n, _line in enumerate(_fh, 1):
                if _VER in _line:
                    _strays.append(
                        f"{os.path.relpath(_path, _root)}:{_n}")
assert not _strays, ("orion2re version hardcoded outside "
                     "core/config.py: " + ", ".join(_strays))
ok("main menu version line (drawn, right-aligned, one source)")
