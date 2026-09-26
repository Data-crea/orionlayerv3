# smoke-suite area: leaders
#
# Part of the OrionLayer smoke suite — 090c_leaders_drawing_help_markings_and_extraction.py.
# Executed in the suite's one namespace, after 090a and 090b (whose
# snapshot and field builders it uses). Work order 167, the Leaders
# screen: what it draws, what it says it does not, and where its words
# and pictures come from.
#
# The 5 check(s) it holds:
#   - the screen draws at 1080p, 1440p and 2160p with the art absent
#     (forced) and present (when extracted), and every line of text it
#     draws fits the width the original gives it
#   - help.json is the original's two help tables (evanhelp.cpp), the
#     rows shrink by their skill lines, and help 333 covers the empty
#     big-icon cells
#   - the markings: every layout.json mark is named in the module that
#     performs it, the HD STATE sentence stands in all its homes, and
#     screen 29 routes to this screen
#   - the two extractors write into the project, git ignores what they
#     write, and both loaders say absent and stale; the skill help box
#     formats the stand-in texts the original's way
#   - open fix 30 is applied: patch, list and version_check say so, the tree carries it (175); was: NOT APPLIED, its entry is on the
#     one list, nothing requires it yet, and it applies to the engine's
#     own ext_api.cpp when that tree is on this disk
import json as _ldc_json
import subprocess as _ldc_sp
import tempfile as _ldc_tmp

from core.estrings import EStrings
from core.skildesc import SkillDesc
from screens.leaders import ldrart as _ldc_art
from screens.leaders import ldrdraw as _ldc_draw
from screens.leaders import ldrrows as _ldc_rows

_ldc_dir = os.path.join(SCREENS_DIR, "leaders")
_ldc_root = os.path.dirname(SCREENS_DIR)

# ── 9. IT DRAWS, AND THE TEXT FITS ────────────────────────────
# Every text the screen draws goes through `ldrdraw.blit_text` with the
# width the original gives it; the wrapper records what came out.
_ldc_drawn = []
_ldc_real_blit = _ldc_draw.blit_text


def _ldc_spy(surface, style, text, x, y, max_w, size, colour, align="left"):
    _r = _ldc_real_blit(surface, style, text, x, y, max_w, size, colour,
                        align)
    if _r is not None:
        _ldc_drawn.append((text, _r.w, max_w, size))
    return _r


_ldc_draw.blit_text = _ldc_spy
try:
    _ldc_arts = [("absent", _ldc_art.LeaderArt(
        os.path.join(_ldc_root, "no-such-gamedata-dir")))]
    _ldc_have = _ldc_art.LeaderArt()
    if _ldc_have.available:
        _ldc_arts.append(("present", _ldc_have))
    else:
        report("the Leaders artwork is not extracted on this disk — drawn "
               "with the art absent only")
    assert not _ldc_arts[0][1].available
    assert "officer_art_extract" in _ldc_arts[0][1].reason
    for _ldc_w, _ldc_h in ((1920, 1080), (2560, 1440), (3840, 2160)):
        _ldc_app, _ = _ldw_plv.build_screen(_ldc_w, _ldc_h)
        _ldc_app.dispatcher.switch_to("leaders")
        _ldc_scr = _ldc_app.dispatcher.screens["leaders"]
        _ldc_scr._words = _ldc_rows.Words(derived(EStrings),
                                          derived(HStrings), "en")
        for _ldc_label, _ldc_a in _ldc_arts:
            _ldc_scr._art = _ldc_a
            for _ldc_view, _ldc_block in ((_ldw_g.VIEW_SHIP, None),
                                          (_ldw_g.VIEW_COLONY, None),
                                          (_ldw_g.VIEW_SHIP, _ldw_block)):
                _ldc_s = _ldw_snapshot(_ldw_recs, block=_ldc_block)
                _ldc_s.fields = _ldw_fields(_ldc_s, _ldc_view)
                _ldc_scr.update(_ldc_s)
                assert _ldc_scr._view.state == _ldw.READY
                _ldc_surf = pygame.Surface((_ldc_w, _ldc_h))
                _ldc_drawn.clear()
                _ldc_hr = _ldc_draw.rect(_ldc_scr.layout,
                                         _ldw_g.text_field(0))
                _ldc_scr.handle_mouse_motion(*_ldc_hr.center)
                _ldc_scr.render(_ldc_surf)
                assert _ldc_drawn, "the screen drew no text at all"
                _ldc_over = [(t, w, m, s) for t, w, m, s in _ldc_drawn
                             if w > m]
                assert not _ldc_over, (
                    f"{_ldc_w}x{_ldc_h} {_ldc_label}: text wider than the "
                    f"original's width for it: {_ldc_over[:4]}")
                # The rows are there: the names were drawn.
                assert any(t.endswith("Leader 2") for t, *_x in _ldc_drawn
                           ) or _ldc_view == _ldw_g.VIEW_COLONY
        # The popup and a native box draw over the screen too.
        _ldc_s = _ldw_snapshot(_ldw_recs)
        _ldc_s.fields = _ldw_popup_fields(_ldw_leader.parse(_ldw_recs[7]))
        _ldc_scr.update(_ldc_s)
        _ldc_scr.render(pygame.Surface((_ldc_w, _ldc_h)))
        _ldc_s.fields = [_ldw_f(1, (0, 0, 639, 479), 7, 0x1B)]
        _ldc_scr.update(_ldc_s)
        assert _ldc_scr._view.state == _ldw.IN_BOX
        _ldc_scr.render(pygame.Surface((_ldc_w, _ldc_h)))
finally:
    _ldc_draw.blit_text = _ldc_real_blit
ok("the Leaders screen draws at 1080p, 1440p and 2160p with the art "
   "absent and present, the popup and a native box over it, and no text "
   "is wider than the original's width for it")

# ── 10. HELP ──────────────────────────────────────────────────
_ldc_help = _ldc_json.load(open(os.path.join(_ldc_dir, "help.json"),
                                encoding="utf-8"))
assert "339" in _ldc_help["hd_extension"]
_ldc_regs = _ldc_help["regions"]
_ldc_colony = [r for r in _ldc_regs if r["view"] == "colony"]
_ldc_ship = [r for r in _ldc_regs if r["view"] == "ship"]
assert (len(_ldc_colony), len(_ldc_ship)) == (16, 18)
import re as _ldc_re
_ldc_tree = _ld_lsc.find_tree(["smoke"])
if _ldc_tree is not None:
    _ldc_src = open(os.path.join(_ldc_tree, "src", "game", "evanhelp.cpp"),
                    encoding="utf-8", errors="replace").read()
    for _ldc_name, _ldc_mine in (("_static_coloff_screen_help_list",
                                  _ldc_colony),
                                 ("_static_shipoff_screen_help_list",
                                  _ldc_ship)):
        _ldc_m = _ldc_re.search(_ldc_name + r"\[\d+\]\s*=\s*\{(.*?)\n    \};",
                                _ldc_src, _ldc_re.S)
        assert _ldc_m, _ldc_name
        _ldc_rows_src = [tuple(int(v) for v in row.split(","))
                         for row in _ldc_re.findall(
                             r"\{\s*([\d,\s]+?)\s*\}", _ldc_m.group(1))]
        assert _ldc_rows_src == [tuple([r["help_id"]] + r["native"])
                                 for r in _ldc_mine], _ldc_name
else:
    report("help.json NOT held to evanhelp.cpp — no orion2re tree on "
           "this disk")
_ldc_list = _ldw_g.help_list(_ldc_regs, _ldw_g.VIEW_COLONY, [2, 0, 0, 0])
assert _ldc_list[3] == (316, (91, 34 + 2 * 17 + 16, 299, 140)), _ldc_list[3]
assert _ldc_list[4] == (316, (91, 143, 299, 250))
assert _ldw_g.help_empty_cells(0) == [_ldw_g.HELP_EMPTY_GRID_ALL]
assert len(_ldw_g.help_empty_cells(6)) == 9
ok("help.json is the original's two help tables, the rows give their "
   "skill lines back, and help 333 covers the empty big-icon cells")

# ── 11. THE MARKINGS ──────────────────────────────────────────
_ldc_layout = _ldc_json.load(open(os.path.join(_ldc_dir, "layout.json"),
                                  encoding="utf-8"))
_ldc_marks = _ldc_layout["marks"]
_ldc_src = {_fn: open(os.path.join(_ldc_dir, _fn), encoding="utf-8").read()
            for _fn in os.listdir(_ldc_dir) if _fn.endswith(".py")}
_ldc_all = "".join(_ldc_src.values())
for _ldc_key, _ldc_word in (
        ("deviation_inner_boxes_drawn", "inner_boxes_drawn"),
        ("deviation_hd_font", "hd_font"),
        ("hd_extension_sprite_scale", "sprite_scale"),
        ("deviation_button_words", "button_words"),
        ("deviation_hd_skill_help", "hd_skill_help"),
        ("hd_state_engine_without_fix_30", "NO_BLOCK"),
        ("deviation_view_box_glass", "view_box_glass"),
        ("deviation_map_glass", "map_glass"),
        ("deviation_strip_ink", "strip_ink"),
        ("omission_map_strip_monsters", "map_strip_monsters"),
        ("transcription_pointer", "ldrmap.scan"),
        ("omission_system_pictures", "system_pictures"),
        ("omission_outer_frame", "OFFICER.LBX 0")):
    assert _ldc_key in _ldc_marks, f"layout.json lost {_ldc_key}"
    assert _ldc_word in _ldc_all, (
        f"{_ldc_key}: no module names {_ldc_word!r} — a marking with no "
        f"home in the code is a label, not a record")
for _ldc_key, _ldc_text in _ldc_marks.items():
    if _ldc_key.startswith(("deviation_", "hd_extension_", "omission_")):
        assert any(_w in _ldc_text for _w in
                   ("DEVIATION", "HD EXTENSION", "OMISSION")), _ldc_key
_ldc_state = "BUILT, NOT ACCEPTED"
assert _ldc_state in _ldc_marks["hd_state"]
assert _ldc_state in _ldc_src["screen.py"].split('"""')[1]
_ldc_status = open(os.path.join(_ldc_root, "v3_projektstatus.md"),
                   encoding="utf-8").read()
assert "screens/leaders/" in _ldc_status and \
    "Leaders — BUILT, NOT ACCEPTED" in _ldc_status, (
        "v3_projektstatus.md does not carry the Leaders screen's state")
from core.screen_names import SCREENS as _ldc_names
assert _ldc_names[29] == ("OFFICERS", "leaders")
assert d.screen_map.get(29) == "leaders" or \
    _ldw_app.dispatcher.screen_map.get(29) == "leaders"
ok("the Leaders markings: every mark named in the module that performs "
   "it, the HD STATE sentence in all its homes, screen 29 routed here")

# ── 12. EXTRACTORS AND LOADERS ────────────────────────────────
for _ldc_tool, _ldc_const in (("officer_art_extract.py", "DEFAULT_OUT"),):
    _ldc_mod = _ld_tool(_ldc_tool[:-3])
    _ldc_out = getattr(_ldc_mod, _ldc_const)
    assert os.path.isabs(_ldc_out) and \
        os.path.commonpath([_ldc_root, _ldc_out]) == _ldc_root, _ldc_out
_ldc_ign = _ldc_sp.run(["git", "-C", _ldc_root, "check-ignore",
                        "--no-index", "screens/leaders/assets/gamedata/",
                        "assets/shared/names/skildesc_en.json"],
                       capture_output=True, text=True)
assert len(_ldc_ign.stdout.split()) == 2, (
    "git does not ignore the Leaders screen's extracted files")
with _ldc_tmp.TemporaryDirectory() as _ldc_t:
    with open(os.path.join(_ldc_t, "manifest.json"), "w") as _fh:
        _fh.write('{"format": %d}' % (_ldc_art.FORMAT_VERSION + 1))
    _ldc_old = _ldc_art.LeaderArt(_ldc_t)
    assert not _ldc_old.available and \
        str(_ldc_art.FORMAT_VERSION) in _ldc_old.reason
    for _ldc_call in (lambda a: a.portrait(0), lambda a: a.skill_icon(10),
                      lambda a: a.star(0), lambda a: a.sprite("hire")):
        assert _ldc_call(_ldc_old) is None
_ldc_desc = derived(SkillDesc)
assert _ldc_desc.title(11) == "SKILL 5"
_ldc_none = SkillDesc("en", root=os.path.join(_ldc_root, "nowhere"))
assert _ldc_none.state == "missing" and _ldc_none.title(0) is None
_ldc_words = _ldc_rows.Words(None, derived(HStrings), "en")
_ldc_rec = _ldw_leader.parse(_ld_pack(name="Leader 4", title="Title 4",
                                      general_skills=0x200, type=1))
_ldc_t, _ldc_body = _ldc_rows.skill_help_text(
    _ldc_rec, 4, 29, 0, _ldc_words, _ldc_desc, ", the ")
assert _ldc_t == "SKILL 14" and _ldc_body.endswith("worth 15."), _ldc_body
assert "Title 4," in _ldc_body, "the title and its comma (officer.cpp:1769)"
# The expiring workaround: a trailing space is put back only if missing.
# SINCE WORK ORDER 175 the extractor keeps the trailing space, so the
# word is the file's own string and the workaround that restored it is
# gone (167's parked item X): what the loader holds is what is used.
_LdcK = type("_LdcK", (), {"hstring": lambda self, i: ", the "})
assert _ldc_rows.the_word(_LdcK(), 3) == ", the "
assert "workaround_the_word" not in _ldc_marks
ok("the Leaders extractors write into the project and git ignores their "
   "output; both loaders say absent and stale; the skill help box "
   "formats the original's way")

# ── 13. OPEN FIX 30 — APPLIED by work order 175 ─────────────────
# The patch's header, the one list and version_check say so; where an
# orion2re tree is on this disk it carries the marker and the patch comes
# back off cleanly (`patch -R --dry-run`), which is what "applied" means.
_ldc_patch = os.path.join(_ldc_root, "doc", "ext_officer_screen_state.patch")
_ldc_ptext = open(_ldc_patch, encoding="utf-8").read()
assert "STATUS: APPLIED 26 September 2026" in _ldc_ptext and "cc542e02" in _ldc_ptext
_ldc_fixes = open(os.path.join(_ldc_root, "doc", "orion2re_open_fixes.md"),
                  encoding="utf-8").read()
assert "## 30. The Leaders screen's view state" in _ldc_fixes
_ldc_row = next(_l for _l in _ldc_fixes.splitlines() if _l.startswith("| 30 |"))
assert "**Applied** 26 September 2026 by work order 175" in _ldc_row, _ldc_row
_ldc_vc = open(os.path.join(_ldc_root, "tools", "version_check.py"),
               encoding="utf-8").read()
assert '"_officer_star_displayed"' in _ldc_vc, "version_check does not require open fix 30"
if _ldc_tree is not None and os.path.exists(os.path.join(
        _ldc_tree, "src", "ext", "ext_api.cpp")):
    _ldc_api = os.path.join(_ldc_tree, "src", "ext", "ext_api.cpp")
    assert "_officer_star_displayed" in open(_ldc_api, encoding="utf-8",
                                             errors="replace").read()
    with _ldc_tmp.TemporaryDirectory() as _ldc_t:
        os.makedirs(os.path.join(_ldc_t, "src", "ext"))
        with open(_ldc_api, "rb") as _src, open(os.path.join(
                _ldc_t, "src", "ext", "ext_api.cpp"), "wb") as _dst:
            _dst.write(_src.read())
        # Open fix 32 (work order 176) sits right after this block in the
        # same file: it comes off the scratch copy first, as the stack was
        # applied, so fix 30's own context is what is checked.
        _ldc_later = os.path.join(_ldc_root, "doc",
                                  "ext_info_screen_state.patch")
        if "MOX::_bill_savegame[i]" in open(_ldc_api, encoding="utf-8",
                                            errors="replace").read():
            _ldc_off = _ldc_sp.run(["patch", "-R", "-p1", "-i", _ldc_later],
                                   cwd=_ldc_t, capture_output=True, text=True)
            assert _ldc_off.returncode == 0, _ldc_off.stdout + _ldc_off.stderr
        _ldc_run = _ldc_sp.run(["patch", "-R", "-p1", "--dry-run", "-i",
                                _ldc_patch], cwd=_ldc_t,
                               capture_output=True, text=True)
        assert _ldc_run.returncode == 0, _ldc_run.stdout + _ldc_run.stderr
else:
    report("open fix 30 NOT checked against ext_api.cpp — no orion2re "
           "tree on this disk")
ok("open fix 30 is applied: the patch and the one list say so with its "
   "commit, version_check requires its marker, and the engine's own "
   "ext_api.cpp carries it (the patch comes back off cleanly)")
