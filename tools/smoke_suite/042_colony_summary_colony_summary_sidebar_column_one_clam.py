# smoke-suite area: colony_summary
#
# Part of the OrionLayer smoke suite — 042_colony_summary_colony_summary_sidebar_column_one_clam.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (93 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 2 check(s) it holds:
#   - colony summary sidebar column (one clamp, both widths kept, and the marking says whether it is f
#   - RETURN is the eighth cutout and behaves like one ( sizes: panel fill, hover over the whole box, 


# ── The sidebar's six s_player scalars ──
# ONE home for these offsets: the verified spec in
# core/structs/player.py. A probe spec briefly duplicated them in
# unverified.py on the mistaken belief that they were unverified;
# it is gone, and this check exists partly so it does not come
# back — a second Spec naming s_player is refused.
#
# What IS asserted is the thing the static assert cannot cover.
# `verified=True` here rests on the header compiled with its own
# pragma pack, sizeof landing on the 0xf0e in sizes.h. That fixes
# the LAYOUT and says nothing about which member is which where
# two are interchangeable — surplus_food @276 and surplus_bc @278
# are adjacent int16 net flows, both printed signed, and the
# struct is exactly as large either way round. So each carries a
# KIND, and tools/struct_probe.py players --sidebar is the check
# that can tell them apart.
from core.structs import player as _plsp
from core.structs import unverified as _unv
assert not any(getattr(_unv, _n, None).__class__.__name__ == "Spec"
               and getattr(_unv, _n).name == "s_player"
               for _n in dir(_unv) if _n.isupper()), (
    "s_player is back in unverified.py — its offsets live in "
    "core/structs/player.py and nowhere else")
_pl_off = dict((n, (o, k)) for n, o, k in _plsp.SPEC.fields)
_six = ("bc", "surplus_bc", "total_pop", "surplus_freighters",
        "surplus_food", "research_produced")
for _f in _six:
    assert _f in _pl_off, f"player.SPEC no longer carries {_f}"
    assert _f in _plsp.SIDEBAR_KINDS, (
        f"{_f} has no kind recorded in player.SIDEBAR_KINDS — "
        f"they are not one kind and adding a gross to a net is "
        f"silently wrong")
    assert _plsp.SIDEBAR_KINDS[_f][0] in (
        "stock", "net flow", "gross", "count"), \
        _plsp.SIDEBAR_KINDS[_f]
assert _plsp.SIDEBAR_KINDS["bc"][0] == "stock"
assert _plsp.SIDEBAR_KINDS["research_produced"][0] == "gross"
assert (_plsp.SIDEBAR_KINDS["surplus_food"][0]
        == _plsp.SIDEBAR_KINDS["surplus_bc"][0] == "net flow")
# The anchors --sidebar carries as controls must resolve.
assert _pl_off["race"][1] == "u8" and _pl_off["race"][0] == 37
assert _plsp.TRAITS_OFFSET == 2308
assert _plsp.TECH_APPLICATIONS_OFFSET == 379

# The sign rule is the original's and is PER ROW: only Income
# (ESTR 106, "%sIncome: %s%s%+d") and Food (ESTR 102,
# "%sFood: %s%+d") carry %+d; Reserve 118, Population 114,
# Freighters 103 and Research 117 are plain %d. A screen-wide
# "sign everything" would be wrong on four rows out of six.
_emp = _cjson.load(open(os.path.join(
    SCREENS_DIR, "colony_summary", "layout.json"),
    encoding="utf-8"))["empire"]
_signed = {r["key"] for r in _emp["rows"] if r.get("signed")}
assert _signed == {"income", "food"}, (
    f"the signed rows are {sorted(_signed)}; the original prints "
    f"%+d on Income (106) and Food (102) and %d on the other four")
_fields = [r["field"] for r in _emp["rows"]]
assert _fields == ["bc", "surplus_bc", "total_pop",
                   "surplus_freighters", "surplus_food",
                   "research_produced"], _fields
# Research is ABSOLUTE and carries no percent. Asserted because
# the claim is easy to cite wrongly: ESTR 117 is
# "%sResearch: %s%d" and there is no %% in it. The note has to
# keep saying so.
assert "no %% in it" in _emp["_estrings_note"], (
    "empire._estrings_note no longer records that ESTR 117 "
    "carries no percent")
for _pct in ("108", "112", "120", "121", "0x142"):
    assert _pct in _emp["_estrings_note"], (
        f"empire._estrings_note no longer lists {_pct} among the "
        f"only string-table entries that DO carry a literal %% — "
        f"the list is what makes 'not 117' checkable rather than "
        f"asserted")
for _key in ("_join_note", "_justify_note", "_geometry_note",
             "_colour_note", "_open_note"):
    assert _emp.get(_key), f"empire.{_key} is gone"
# The justify note carries the corrected mechanism, not the
# first one. justify=3 is inert because the buffer BEGINS with
# s_0, so Set_Justification_ assigns justify_mode = 0 before a
# character is drawn (fmtpara.cpp:1017) — not because CR ends
# each line, which was the first reading. And the layout it
# settles is label-left/value-right, which the renderer now does.
for _cite in ("fmtpara.cpp:1017", "fmtpara.cpp:999",
              "fmtpara.cpp:1699", "strings.cpp:22"):
    assert _cite in _emp["_justify_note"], (
        f"empire._justify_note no longer cites {_cite} — the "
        f"mechanism it records is what makes label-left/"
        f"value-right a transcription rather than a preference")
assert "0x1A" in _emp["_justify_note"], (
    "empire._justify_note no longer records that the prefixes "
    "are 0x1A justification codes — the octal 032/033 confusion "
    "is what got this wrong twice")
assert "OPEN" in _emp["_open_note"], (
    "empire._open_note no longer marks E_Strings_(12) as open")

# ── The sidebar draws label LEFT and value RIGHT ──
# The original's layout, and it is the whole point of the
# justify-code reading above: each entry is one row, the label
# flush against the column's left edge, the value flush against
# its right. Asserted in INK at every resolution, and the edges
# are read from boxes.json rather than recomputed the way
# `_value_column` computes them — deriving the expected edge from
# the renderer's own expression is the tautology 443aff1 shipped
# and had to be rewritten.
#
# Flushness is what distinguishes this from the layout it
# replaced. Centred label-over-value passes no part of it: the
# label would not start at the left edge and the value would not
# end at the right one.
_sb_boxes = _seated(
    os.path.join(SCREENS_DIR, "colony_summary", "boxes.json"),
    1920, 1080)
_sb_ref = [b.ref_rect for b in _sb_boxes if b.name == "empire_stats"]
assert _sb_ref, "colony_summary has no empire_stats box"

from screens.colony_summary import screen as _cs
from screens.colony_summary import colonyempire as _emp_mod0

# The screen loads its boxes and layout.json on activation, and
# the dispatcher has been through other screens since the earlier
# colony_summary check.
d.switch_to("colony_summary")

class _FakePlayer:
    bc = 1234
    surplus_bc = -42
    total_pop = 39
    surplus_freighters = 7
    surplus_food = -3
    research_produced = 88

for _W, _H in _SIZES:
    _lay = Layout(_W, _H)
    _rect = pygame.Rect(*_lay.rect(_sb_ref[0]))
    # The column, derived here from the box, the native width and
    # the inset in layout.json — NOT by calling _value_column.
    # frame_inset keeps both edges out from under the frame's
    # rim; it is a SCREEN-level key because colonylist needs the
    # same number. See _frame_inset_note in layout.json.
    _native = _emp.get("native_width", 104)
    _inset = int(_out_cfg.get("frame_inset", 8) * _lay.scale)
    _col_w = min(max(1, _rect.w - 2 * _inset),
                 int(_native * (1920 / _emp_mod0.NATIVE_W) * _lay.scale))
    _col_l = _rect.x + _inset
    _col_r = _col_l + _col_w

    _sf = pygame.Surface((_W, _H))
    _sf.fill((0, 0, 0))
    # `layout` is a property onto app.layout, so the resolution
    # is swapped on the app for the duration of one render.
    _scr = app.dispatcher.screens["colony_summary"]
    _saved_layout, _saved_local = app.layout, _scr._local
    app.layout, _scr._local = _lay, _FakePlayer()
    try:
        _scr._render_sidebar(_sf)
    finally:
        app.layout, _scr._local = _saved_layout, _saved_local

    _arr = pygame.surfarray.array3d(_sf.subsurface(_rect))
    _lab_rgb = tuple(_emp_mod0.LABEL_COLOR[:3])
    _val_rgb = tuple(_emp_mod0.VALUE_COLOR[:3])
    _warn_rgb = tuple(_emp_mod0.WARN_COLOR[:3])

    def _cols(_rgb):
        _m = (_arr == _rgb).all(axis=2).any(axis=1).nonzero()[0]
        return (int(_m[0]) + _rect.x, int(_m[-1]) + _rect.x) \
            if len(_m) else None

    _lab = _cols(_lab_rgb)
    _val = _cols(_val_rgb)
    _warn = _cols(_warn_rgb)
    assert _lab, f"{_W}x{_H}: no label ink in the sidebar"
    assert _val, f"{_W}x{_H}: no value ink in the sidebar"

    # A glyph's ink does not start at its surface's edge — there
    # is a side bearing, and it grows with the font, which is why
    # a fixed pixel tolerance passed at 1080p and failed at 4K by
    # exactly the bearing. So the bearing is MEASURED off a
    # standalone render of the same string and added to the
    # column edge. That is glyph metrics, not layout: it says
    # nothing about where the renderer decided to put the text,
    # which is the thing under test.
    _fs = _scr.box_font_scale_stored("empire_stats")
    _lab_px = _lay.font_size(int(_emp.get("label_font", 18) * _fs))
    _val_px = _lay.font_size(int(_emp.get("value_font", 26) * _fs))

    def _bearings(_text, _px, _rgb):
        """(ink left, ink right) inside the string's own surface.

            Composited onto the SAME panel fill the sidebar uses.
            Measured against a bare surface the numbers come out a
            couple of pixels different, because an antialiased edge
            column blends with whatever is behind it and stops
            matching the colour exactly — so the bearing has to be
            measured through the same compositing the renderer does,
            or it is measuring a different picture.
            """
        _s2 = app.style.render_text(_text, _px, _rgb)
        _pad = pygame.Surface((_s2.get_width() + 4,
                               _s2.get_height() + 4))
        _pad.fill(_emp_mod0.PANEL_BG[:3])
        _pad.blit(_s2, (2, 2))
        _a2 = pygame.surfarray.array3d(_pad)
        _m2 = (_a2 == _rgb).all(axis=2).any(axis=1).nonzero()[0]
        if not len(_m2):
            return None
        return (int(_m2[0]) - 2,
                (_s2.get_width() + 1) - int(_m2[-1]))

    _want_left, _want_right = [], []
    for _r in _emp["rows"]:
        _b = _bearings(_r["label"].upper(), _lab_px, _lab_rgb)
        if _b:
            _want_left.append(_col_l + _b[0])
        _v = getattr(_FakePlayer, _r["field"])
        _txt = _emp_mod0.format_value(_v, _r.get("signed", False))
        _rgb2 = _warn_rgb if (_r.get("warn_negative")
                              and _v < 0) else _val_rgb
        _b = _bearings(_txt, _val_px, _rgb2)
        if _b:
            _want_right.append(_col_r - _b[1])

    _exp_left, _exp_right = min(_want_left), max(_want_right)
    _val_right = max(_val[1], _warn[1] if _warn else _val[1])
    assert abs(_lab[0] - _exp_left) <= 1, (
        f"{_W}x{_H}: the label's leftmost ink is at {_lab[0]}; "
        f"flush against the column's left edge {_col_l} it would "
        f"be {_exp_left} once the glyph's own {_exp_left - _col_l} "
        f"px bearing is allowed ({_lab[0] - _exp_left:+d}). The "
        f"original left-justifies the label (strings.cpp:22, "
        f"byte 1A 30).")
    assert abs(_val_right - _exp_right) <= 1, (
        f"{_W}x{_H}: the rightmost value ink is at {_val_right}; "
        f"flush against the column's right edge {_col_r} it would "
        f"be {_exp_right} ({_val_right - _exp_right:+d}). The "
        f"original right-justifies the value (strings.cpp:24, "
        f"byte 1A 31; para.x2 = x + width - 1, fmtpara.cpp:657).")
    # And the two columns must not have collapsed into one.
    assert _lab[0] < _val_right, (
        f"{_W}x{_H}: label ink starts at {_lab[0]}, values end at "
        f"{_val_right} — the two columns have collapsed")
# ── The clamped column is a DEVIATION and stays marked ──
# The original's paragraph is 104 native px = 312 reference px;
# the sidebar cutout is 286, and `min` picks the cutout at every
# resolution. Decision 44: the deviation is that the shipped
# column is never the original's proportion, and the risk is the
# native number being deleted once somebody notices it never
# wins. So: it must still be READ, and it must still be LARGER
# than what is drawn — the day it is not, the clamp has stopped
# firing on its own and the deviation is over.
assert "native_width" in _emp, (
    "empire.native_width is gone — it is the original's 104 px "
    "paragraph and the only evidence the drawn column is a "
    "deviation rather than a choice (decision 44)")
for _cite in ("DEVIATION", "colsum.cpp:418", "fmtpara.cpp:657"):
    assert _cite in _emp["_native_width_note"], (
        f"empire._native_width_note no longer carries {_cite!r}")
_fund_dev = read_doc(os.path.join(os.path.dirname(SCREENS_DIR), "doc",
                                  "v3_fundament.md"))
assert "**44." in _fund_dev and "native_width" in _fund_dev, (
    "the fundament no longer carries the clamped sidebar column "
    "as a decision")
# The marking lives with the CODE, so this greps the module the
# clamp is in and not the screen it used to be in. The sidebar
# moved to colonyempire.py on 3 September 2026; a check left
# pointed at screen.py would have gone on passing against a file
# that no longer contains the thing it asserts, which is worse
# than no check because it still reports green.
from screens.colony_summary import colonyempire as _emp_mod
_scr_dev = open(os.path.join(SCREENS_DIR, "colony_summary",
                             "colonyempire.py"),
                encoding="utf-8").read()
# On the FUNCTION THAT CLAMPS, not merely somewhere in the file:
# the module docstring also says "DEVIATION", so a file-wide
# search passes even after the marking is taken off the code it
# is about. Tying it to `value_column.__doc__` is what makes the
# marking travel with the thing it marks.
assert "DEVIATION" in (_emp_mod.value_column.__doc__ or ""), (
    "value_column no longer mentions the clamped width's "
    "DEVIATION at all — whether it is firing or retired, the "
    "record of what it deviated from is decision 44's evidence "
    "and outlives the clamp")
assert "native_column_width" in _scr_dev, (
    "colonyempire.py no longer carries native_column_width")
# ONE home for the clamp, asserted as a rule: screen.py must not
# grow a second copy of it. The sidebar came back into a screen
# once before, as a duplicated s_player spec in unverified.py, and
# the check that refused a second Spec is why it stayed gone.
_scr_now = open(os.path.join(SCREENS_DIR, "colony_summary",
                             "screen.py"), encoding="utf-8").read()
assert "native_width" not in _scr_now, (
    "screen.py mentions native_width again — the clamp and its "
    "marking live in colonyempire.py, and a second copy is what "
    "the marking cannot survive")

_clamped = []
for _W, _H in _SIZES:
    _lay = Layout(_W, _H)
    _rect = pygame.Rect(*_lay.rect(_sb_ref[0]))
    _native = _emp_mod.native_column_width(_emp, _lay)
    _l, _r = _emp_mod.value_column(_rect, _emp, _lay,
                                  _out_cfg.get("frame_inset", 8))
    _drawn = _r - _l
    _inset = int(_out_cfg.get("frame_inset", 8) * _lay.scale)
    _usable = max(1, _rect.w - 2 * _inset)
    assert _drawn == min(_usable, _native), (
        f"{_W}x{_H}: the drawn column {_drawn} is neither the "
        f"cutout less its insets {_usable} nor the native "
        f"{_native} — the clamp has grown a third case")
    _clamped.append(_native > _drawn)
# **THE CLAMP RETIRED ITSELF — 12 September 2026.** This asserted
# `_native > _drawn` at every size, because the marking is only
# true while the clamp fires, and said in its own words: "if this
# ever fails, the cutout has caught up with the original's
# proportion: delete decision 44 and this check rather than
# fixing it." Data's new frame removed the right-hand column and
# put the empire readouts in the lower band; the box is 451
# reference px where it was 286, and `min` selects the NATIVE
# width at all twelve sizes.
#
# What replaces the assertion is its own converse, so the
# retirement cannot quietly un-retire: if the clamp ever fires
# again the marking has to be live again, and this says so.
report(f"sidebar column: the clamp fires at {sum(_clamped)} of "
       f"{len(_clamped)} sizes (native 312 ref px against a box "
       f"of {cs.box_rect('empire_stats')[2]})")
_emp_doc = (_emp_mod.value_column.__doc__ or "")
if any(_clamped):
    assert "DEVIATION" in _emp_doc and "RETIRED" not in _emp_doc, (
        "the clamp fires again and value_column calls the "
        "deviation retired — decision 44 is live whenever the "
        "box is narrower than the original's 312 reference px")
else:
    assert "RETIRED" in _emp_doc, (
        "the clamp fires at no shipped size, so decision 44's "
        "deviation is over and value_column has to say so — "
        "retire the marking, do not restore it")
ok("colony summary sidebar column (one clamp, both widths kept, "
   "and the marking says whether it is firing)")

import numpy as _np
from PIL import Image
from core import style as _style_mod
# ── CLASS A: text OUR CODE places at a cutout edge ──
# Zero pixels under opaque frame alpha, every shipped size, no
# tolerance. This REPLACES a sidebar-only version of the same
# check — that one asserted the instance and this asserts the
# rule, and it found a second instance the first could not: one
# pixel of a fifteen-character colony name at 1600x900, whose
# right-aligned overflow was allowed to run to list_area's own
# edge and therefore under the rim.
#
# NO LIST OF BOXES. The renderers are asked what they drew:
# StyleRenderer.render_text and get_font(...).render are wrapped
# so every text surface is tagged, and the screen renders onto a
# Surface subclass that records where each tagged surface landed.
# A text box added tomorrow is covered without anyone editing
# this.
#
# TWO THINGS THIS MEASURES CAREFULLY, both learned the hard way:
#
#   what SURVIVES the clip, not what was requested. galaxy_map
#   wraps its whole map render in set_clip(map_area), exactly as
#   the original wraps Print_Star_Names_ in Set_Window_/Clip_On_
#   (mainscr.cpp:519). Recording the intended rectangle reports
#   three labels under the frame on that screen, one of them 330
#   px outside the map, and all three are fiction.
#
#   a POPULATED state. With no snapshot the colony summary draws
#   22 glyphs; with one it draws 65, because the list, the scan
#   box and the galaxy inset are all empty until then. A green
#   run over an empty screen asserts nothing.
#
# CLASS B is separated MECHANICALLY, not by a list: content
# clipped to a cutout is the frame's own business and is checked
# against the artwork below, so a glyph whose clip at blit time
# IS one of that screen's cutouts is not Class A.
class _TextRec(pygame.Surface):
    hits = []
    def blit(self, src, dest, *a, **k):
        _clip = self.get_clip()
        _r = super().blit(src, dest, *a, **k)
        if id(src) in _TEXT_IDS:
            _TextRec.hits.append(
                (int(dest[0]), int(dest[1]), src,
                 pygame.Rect(_clip) if _clip else None))
        return _r

_TEXT_IDS = set()
_TEXT_KEEP = []
_orig_rt = _style_mod.StyleRenderer.render_text
_orig_gf = _style_mod.StyleRenderer.get_font

class _TaggedFont:
    def __init__(self, f): self._f = f
    def __getattr__(self, n): return getattr(self._f, n)
    def render(self, *a, **k):
        r = self._f.render(*a, **k)
        _TEXT_IDS.add(id(r)); _TEXT_KEEP.append(r)
        return r

def _tagged_rt(self, *a, **k):
    r = _orig_rt(self, *a, **k)
    _TEXT_IDS.add(id(r)); _TEXT_KEEP.append(r)
    return r

#: THE GALAXY MAP LEFT ON 25 SEPTEMBER 2026 (work order 169, decision
#: 71): it draws no frame image, so no glyph of it can be under one —
#: the subject of both classes is gone there. Its boxes are held to the
#: HUD's measured layout instead ("galaxy_map boxes == the HUD's
#: measured layout", module 007).
_FRAME_SCREENS = ("colony_summary",)
#: CLASS B TAKES ONE MORE, and the split is not tidiness. `fleets`
#: joined on 19 September 2026 (work order 137 E2) once its three
#: strut stubs were out of the artwork — but class A builds each
#: screen at twelve sizes with no snapshot, and this one then draws
#: seven text surfaces, under the floor class A refuses to measure
#: below ("a green run in a null state is not evidence"). Class B
#: reads the PNG and needs no screen at all, so it takes it today
#: and class A waits for a fixture that hands the Fleets screen a
#: snapshot. It is also the first one-opening screen here: decision
#: 3 does not apply to it, so `frame_holes` has no naming rule for
#: it and the loop below names its single hole itself.
_FRAME_SCREENS_B = _FRAME_SCREENS + ("fleets",)
_class_a = {}
_class_b_seen = 0
_class_c = {}

def _cs_ref_for(_sname):
    """That screen's `layout_reference.json`, or {} if it has none."""
    _p = os.path.join(SCREENS_DIR, _sname, "layout_reference.json")
    if not os.path.exists(_p):
        return {}
    with open(_p, encoding="utf-8") as _fh:
        return _json.load(_fh)

_style_mod.StyleRenderer.render_text = _tagged_rt
_style_mod.StyleRenderer.get_font = lambda self, sz: _TaggedFont(
    _orig_gf(self, sz))
try:
    for _name in _FRAME_SCREENS:
        for _W, _H in _SIZES:
            _a2, _ = _pv.build_screen(_W, _H)
            _s2 = _a2.dispatcher.screens[_name]
            _a2.dispatcher.switch_to(_name)
            # THE ALPHA MUST BE THE FRAME THE SCREEN DREW, and
            # since Phase B that is `assets/frame.png` for every
            # screen with no switch anywhere. It was not always:
            # between Stage 4 and Phase B the colony screen drew a
            # per-resolution plate, and reading this path measured
            # glyphs against artwork nobody blitted — 5822
            # "violations" at 1080p against a frame that was not
            # on screen.
            _fpng = res.screen_file(_name, "assets", "frame.png")
            _fbase = Image.open(_fpng).convert("RGBA")
            _s2.enter(None)
            _s2.update(_pv._Snapshot(_pv.COLONIES))
            _cuts = []
            for _b in _s2.boxes:
                _br = _s2.box_rect(_b.name)
                if _br:
                    _cuts.append(pygame.Rect(*_s2.layout.rect(_br)))
            # THE WINDOWS THAT ARE DECLARED TO HAVE NO HOLE, and
            # whose text is therefore MEANT to land on the metal —
            # 12 September 2026, Data's new frame. RETURN is drawn
            # over the frame, on a plate this screen paints itself,
            # at a rect Data sets in the editor; the header is a
            # band of the list's hole and lands on no metal at all.
            # A glyph inside one of these is class C: over a plate
            # of ours, not under the frame. The exemption is the
            # DECLARATION and nothing else — a word that drifts out
            # of the declared rect is class A again, and the plate
            # under RETURN is checked for opacity in its own check.
            _plated = []
            for _pn in _cs_ref_for(_name).get(
                    "_windows_without_a_hole", ()):
                _pr = _s2.box_rect(_cpl.BOX_NAME.get(_pn, _pn))
                if _pr:
                    _plated.append((_pn,
                                    pygame.Rect(*_s2.layout.rect(_pr))))
            _TextRec.hits = []
            _surf2 = _TextRec((_W, _H))
            _surf2.fill((0, 0, 0))
            _s2.render(_surf2)
            assert len(_TextRec.hits) >= 10, (
                f"{_name} at {_W}x{_H} drew {len(_TextRec.hits)} text "
                f"surfaces — too few for this check to mean anything. "
                f"A green run over an empty screen asserts nothing")
            _fx, _fy, _fw, _fh = _s2.layout.rect((0, 0, 1920, 1080))
            _al = _np.array(_fbase.resize((_fw, _fh),
                                          Image.BILINEAR))[:, :, 3]
            for _x, _y, _src, _clip in _TextRec.hits:
                _rgb = pygame.surfarray.array3d(
                    _src).transpose(1, 0, 2).astype(int)
                _m = _rgb.sum(axis=2) > 40
                if _src.get_flags() & pygame.SRCALPHA:
                    _m &= pygame.surfarray.array_alpha(
                        _src).transpose(1, 0) > 40
                _ys, _xs = _np.where(_m)
                if not len(_ys):
                    continue
                _px, _py = _xs + _x, _ys + _y
                if _clip is not None:
                    _k = ((_px >= _clip.x) & (_px < _clip.right)
                          & (_py >= _clip.y) & (_py < _clip.bottom))
                    _px, _py = _px[_k], _py[_k]
                    if not len(_px):
                        continue
                _gx, _gy = _px - _fx, _py - _fy
                _ok = ((_gx >= 0) & (_gx < _fw)
                       & (_gy >= 0) & (_gy < _fh))
                if not _ok.any():
                    continue
                _n = int((_al[_gy[_ok], _gx[_ok]] >= 16).sum())
                if not _n:
                    continue
                _is_b = _clip is not None and any(
                    abs(_clip.x - _c.x) <= 2 and abs(_clip.y - _c.y) <= 2
                    and abs(_clip.w - _c.w) <= 4
                    and abs(_clip.h - _c.h) <= 4 for _c in _cuts)
                _is_c = next(
                    (_pn for _pn, _pr in _plated
                     if _px.min() >= _pr.x and _px.max() < _pr.right
                     and _py.min() >= _pr.y and _py.max() < _pr.bottom),
                    None)
                if _is_b:
                    _class_b_seen += _n
                elif _is_c:
                    _class_c[_is_c] = _class_c.get(_is_c, 0) + _n
                else:
                    _class_a[(_name, _W, _H)] = (
                        _class_a.get((_name, _W, _H), 0) + _n)
finally:
    _style_mod.StyleRenderer.render_text = _orig_rt
    _style_mod.StyleRenderer.get_font = _orig_gf
if slow("return_cutout"):
    assert not _class_a, (
        f"CLASS A violations — text this tree places at a cutout edge, "
        f"drawn under opaque frame alpha: {_class_a}. Zero tolerance: "
        f"raise the screen's frame_inset, or stop placing the text "
        f"against the box edge. (Content CLIPPED to a cutout is class "
        f"B and is checked against the artwork, not here.)")
    # ── RETURN IS THE EIGHTH SLOT, AND IT BEHAVES LIKE ONE ──────
    #
    # **RE-POINTED 12 September 2026, the same day it was written.**
    # For one day this frame cut no hole for RETURN: the button was
    # drawn OVER the metal on a plate of its own, and this asserted
    # that the plate was opaque — because a word on bare artwork is
    # the class-A fault this file holds at zero. Data's frame of that
    # evening cuts an eighth slot in the sort row, so the plate is
    # gone and what has to hold is what holds for the seven keys
    # beside it: the cutout carries the panel fill, the word sits
    # inside the box with `HIGHLIGHT_PAD` to spare, and the hover
    # reaches the WHOLE box, which is the one place RETURN differs
    # from a sort key (a key lights its word, and the original gives
    # RETURN no lit state at all).
    #
    # The rect is asserted by the hole check, not here: it is the
    # artwork's own again, and this box is LOCKED in the editor.
    from screens.colony_summary import colonysort as _rb_sort
    from screens.colony_summary.screen import (PANEL_BG as _rb_bg,
                                               NAV_HOVER_BG as _rb_hov,
                                               NAV_TEXT as _rb_fg)
    _rb_fits = []
    for _W, _H in _SIZES:
        _rb_app, _ = _pv.build_screen(_W, _H)
        _rb_scr = _rb_app.dispatcher.screens["colony_summary"]
        _rb_app.dispatcher.switch_to("colony_summary")
        _rb_scr.enter(None)
        _rb_scr.update(_pv._Snapshot(_pv.COLONIES))
        _rb_r = pygame.Rect(*_rb_scr.layout.rect(
            _rb_scr.box_rect("return")))
        import core.mouse as _rb_m
        _rb_saved = _rb_m.pos

        def _rb_render(_ptr):
            _rb_m.pos = lambda: _ptr
            try:
                _s = pygame.Surface((_W, _H))
                _s.fill((255, 0, 255))
                _rb_scr.render(_s)
                return _s
            finally:
                _rb_m.pos = _rb_saved

        # INSIDE THE ROUNDED CORNERS, INSIDE THE BLEED AND CLEAR OF
        # THE WORD. The box is the hole grown by `colonyplates.BLEED`
        # and the frame's rim is anti-aliased over the top of it, so a
        # sample two pixels in reads the rim blended with the fill —
        # (6, 8, 13) against (8, 11, 20) at 1680x1050, which is the
        # rim at about four fifths. The word is centred and comes
        # within 9 px of the box's width at 1280x720, so the samples
        # stay on the top and bottom edges.
        _rb_rad = max(6, int(10 * _rb_scr.layout.scale))
        _rb_in = max(5, int(5 * _rb_scr.layout.scale))
        _rb_pts = ((_rb_r.centerx, _rb_r.y + _rb_in),
                   (_rb_r.centerx, _rb_r.bottom - 1 - _rb_in),
                   (_rb_r.x + _rb_rad, _rb_r.y + _rb_in),
                   (_rb_r.right - 1 - _rb_rad, _rb_r.bottom - 1 - _rb_in))
        _rb_idle = _rb_render((0, 0))
        for _rb_p in _rb_pts:
            _rb_c = _rb_idle.get_at(_rb_p)[:3]
            assert _rb_c == tuple(_rb_bg[:3]), (
                f"{_W}x{_H}: {_rb_p} of RETURN's cutout "
                f"{tuple(_rb_r)} is {_rb_c} and the panel fill is "
                f"{tuple(_rb_bg[:3])} — the eighth slot is not being "
                f"filled like the other seven")
        # AND THE HOVER REACHES THE WHOLE BOX.
        _rb_over = _rb_render(_rb_r.center)
        for _rb_p in _rb_pts:
            _rb_c = _rb_over.get_at(_rb_p)[:3]
            assert _rb_c == tuple(_rb_hov[:3]), (
                f"{_W}x{_H}: with the pointer on RETURN, {_rb_p} is "
                f"{_rb_c} and the hover fill is {tuple(_rb_hov[:3])} "
                f"— the hover has to reach the whole button")
        # AND THE WORD IS ON IT.
        _rb_ink = _np.array(pygame.surfarray.array3d(
            _rb_idle.subsurface(_rb_r))).reshape(-1, 3)
        assert (_np.abs(_rb_ink - _np.array(_rb_fg[:3])).sum(axis=1)
                < 30).sum() >= 20, (
            f"{_W}x{_H}: RETURN's slot carries no pixel of the "
            f"label's own colour {tuple(_rb_fg[:3])}")
        _rb_word = _rb_scr.style.render_text(
            _rb_scr._data.get("return", {}).get("label", "Return").upper(),
            _rb_scr.layout.font_size(
                _rb_scr.box_style("return").get("font_size", 24)),
            (255, 255, 255))
        _rb_pad = max(1, int(_rb_sort.HIGHLIGHT_PAD * _rb_scr.layout.scale))
        assert _rb_word.get_width() + 2 * _rb_pad <= _rb_r.w, (
            f"{_W}x{_H}: RETURN's label is {_rb_word.get_width()} px "
            f"wide in a {_rb_r.w} px slot with {_rb_pad} px of "
            f"padding per side — the hole the artwork cuts is too "
            f"small for the word at this resolution")
        assert _rb_word.get_height() <= _rb_r.h, (
            f"{_W}x{_H}: RETURN's label is {_rb_word.get_height()} px "
            f"tall in a {_rb_r.h} px slot")
        _rb_fits.append(_rb_r.w - _rb_word.get_width())
    report(f"RETURN label clearance, narrowest of {len(_SIZES)} sizes: "
           f"{min(_rb_fits)} px of the slot's width")
    ok(f"RETURN is the eighth cutout and behaves like one ({len(_SIZES)} "
       f"sizes: panel fill, hover over the whole box, word inside it)")
