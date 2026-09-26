# smoke-suite area: info
#
# Part of the OrionLayer smoke suite — 090f_info_the_info_screen_and_its_texts.py.
# Executed in the suite's one namespace, after 090a-090e (whose record
# packer `_lm_pack`, player builder `_rc_player_raw`, `_ldw_f`, the send
# recorder `_ldw_sent` and the app `_ldw_app` it uses). Work order 175 D:
# the Info screen (SCREEN_INFO, 9) and the text resolver (decision 73).
#
# The 5 check(s) it holds:
#   - the text resolver: a mod file replaces a key, a missing file or key
#     is the default, a broken file (not UTF-8, empty) is one log line and
#     the default, a "game" key is never replaced, keys map to files, and
#     the mod folder's index takes texts/ without a warning
#   - the template writes OrionLayer's own texts and lists the game's by
#     key only — no MOO2 text (any "moo2" default the stand-ins give) in
#     any file it writes; MODDING.md and the template guide both explain it
#   - the pages' data: the Tech Review lists (empty groups dropped), the
#     chart's rounding, the trait lines, the categories without the digit
#     labels, the topics sorted, the race lists; only RETURN / ESC is sent
#   - every page draws at 1080p, 1440p, 2160p and 2576x1432 with a long
#     modded text, and NO line runs out of its box's width or is cut —
#     each is fully visible or scrolled out; markings, routing, the
#     extractor, the loader
#   - open fix 32 applied and wired: the records, the engine's tree, the
#     INFS block parsed, the History curves and the Turn Summary drawn
import logging as _if_log
import tempfile as _if_tmp

from core import infotext as _if_it
from core import modtexts as _if_mt
from core import usermod as _if_um
from screens.info import infobox as _if_box
from screens.info import infogeom as _if_g
from screens.info import infopages as _if_p
from screens.info import infotexts as _if_tx

# ── 1. THE RESOLVER ──────────────────────────────────────────
_if_mt.reset()
assert "info.tab.reference" in _if_mt.keys()
assert _if_mt.file_name("info.reference.213.body") == \
    "texts/info/reference.213.body.txt"
assert _if_mt.keys()["info.stardate"] == "game"


class _IfCatch(_if_log.Handler):
    def __init__(self):
        super().__init__()
        self.lines = []

    def emit(self, record):
        self.lines.append(record.getMessage())


_if_catch = _IfCatch()
_if_log.getLogger("usermod").addHandler(_if_catch)
with _if_tmp.TemporaryDirectory() as _if_d:
    _if_dir = os.path.join(_if_d, "texts", "info")
    os.makedirs(_if_dir)
    for _if_name, _if_raw in (("tab.reference.txt", "Lexikon\n".encode()),
                              ("tab.tech.txt", b"Techn\xe9k"),
                              ("tab.races.txt", b""),
                              ("stardate.txt", b"9999"),
                              ("nonsense.key.txt", b"never asked")):
        with open(os.path.join(_if_dir, _if_name), "wb") as _fh:
            _fh.write(_if_raw)
    _if_catch.lines.clear()
    _if_um.init(True, root=_if_d)
    try:
        assert not any("texts/" in _l and "ignored" in _l
                       for _l in _if_catch.lines), _if_catch.lines
        assert _if_mt.text("info.tab.reference") == "Lexikon"
        assert _if_mt.text("info.tab.history") == "History", "missing file"
        assert _if_mt.text("info.tab.tech") == "Tech Review", "not UTF-8"
        assert _if_mt.text("info.tab.races") == "Race Stats", "empty"
        _if_mt.text("info.tab.tech")
        assert sum("tab.tech.txt" in _l for _l in _if_catch.lines) == 1, (
            "a broken file must cost exactly one log line", _if_catch.lines)
        assert _if_mt.text("info.stardate", "x") == "x", "a game key"
        assert _if_mt.text("no.such.key", "fallback") == "fallback"
    finally:
        _if_um.shutdown()
        _if_log.getLogger("usermod").removeHandler(_if_catch)
assert _if_mt.text("info.tab.reference") == "Reference", "mod gone, default"
ok("the text resolver: a mod file replaces its key, a missing file or key is "
   "the default, a broken file is one log line and the default, a game key "
   "is never replaced, and the mod folder takes texts/ without a warning")

# ── 2. THE TEMPLATE AND THE GUIDE ─────────────────────────────
from core.billtext import BillText
from core.estrings import EStrings
_if_tx.bind(derived(BillText), derived(EStrings), None, derived(_if_it.InfoText),
            None)
_if_moo = []
for _if_k, _if_src in _if_mt.keys().items():
    if _if_src == "moo2":
        _if_v = _if_mt.default(_if_k)
        if _if_v and len(_if_v) > 3:
            _if_moo.append(_if_v)
assert len(_if_moo) > 50, "the stand-ins give the moo2 defaults"
_if_tpl = _ld_tool("mod_template")
with _if_tmp.TemporaryDirectory() as _if_d:
    _if_written = _if_tpl.make(os.path.join(_if_d, "mod"), log=lambda *_a: 0)
    _if_texts = [p for p in _if_written if os.sep + "texts" + os.sep in p]
    assert _if_texts, "the template wrote no texts"
    for _if_p2 in _if_written:
        if not _if_p2.endswith((".txt", ".md", ".json")):
            continue
        _if_body = open(_if_p2, encoding="utf-8").read()
        for _if_v in _if_moo:
            assert _if_v not in _if_body, (
                f"{_if_p2} carries the original's text {_if_v!r}")
    _if_names = open(os.path.join(_if_d, "mod", "NAMES.txt"),
                     encoding="utf-8").read()
    assert "texts/info/reference.213.body.txt" in _if_names
    assert "texts/info/tab.reference.txt" in _if_names
    assert os.path.exists(os.path.join(_if_d, "mod", "originals", "texts",
                                       "info", "tab.reference.txt"))
_if_guide = open(os.path.join(_ldc_root, "MODDING.md"), encoding="utf-8").read()
assert "### Texts" in _if_guide and "texts/info/tab.reference.txt" in _if_guide
assert "texts/<screen>/<key>.txt" in _if_tpl.GUIDE
ok("the mod template writes OrionLayer's own texts and lists the game's by "
   "key only — no original text in any file it writes — and both guides "
   "explain the texts")

# ── 3. THE PAGES' DATA, AND WHAT IS SENT ─────────────────────
_if_me = _rc_player_raw("Us", 0, 0, contact=(1,),
                        bc_produced=100, total_maintenance=60,
                        maintenance=[50, 10, 0, 0, 0, 0],
                        history_btns=(1 << 4) | 3)
_if_mb = bytearray(_if_me)
_if_app = {_n: _o for _n, _o, _k in _rc_player.SPEC.fields}["tech_applications"]
for _if_a in (55, 16, 43):            # two in group 1, one in group 2
    _if_mb[_if_app + _if_a] = 3
_if_mb[_rc_player.TRAITS_OFFSET + 0] = 2           # government
_if_mb[_rc_player.TRAITS_OFFSET + 2] = 2           # food +1
_if_mb[_rc_player.TRAITS_OFFSET + 5] = -1 & 0xFF   # tax -0.5 BC
_if_mb[_rc_player.TRAITS_OFFSET + 15] = -1 & 0xFF  # poor home world
_if_rec = _rc_player.parse(bytes(_if_mb))
assert _if_p.tech_review(_if_rec, 0) == [(1, [55, 16]), (2, [43])], \
    "researched only, the empty groups dropped (info.cpp:1510-1536)"
assert _if_p.chart(_if_rec) == (100, [50, 10, 0, 0, 0, 0],
                                [100, 50, 10, 0, 0, 0, 0], 40)
_if_tl = _if_p.trait_lines(_if_rec)
assert _if_tl[0] == (_if_mt.text("info.races.gov.2") or "")
assert _if_tl[1].endswith("+1") and _if_tl[2].endswith("-0.5 BC")
assert _if_tl[3] == _if_mt.text("info.races.trait.31"), "poor home world"
assert [i for i, _l in _if_p.categories()] == [
    i for i in range(1, 17)
    if not (_if_mt.text(f"info.reference.category.{i}") or "0")[0] <= "9"]
_if_info = derived(_if_it.InfoText)
_if_top = _if_p.topics(_if_info, 3)
assert [t for t, _i in _if_top] == sorted(t for t, _i in _if_top)
_if_ps = [_rc_player.parse(bytes(_if_mb)),
          _rc_player.parse(_rc_player_raw("Them", 1, 1, contact=(0,))),
          _rc_player.parse(_rc_player_raw("Gone", 2, 2, eliminated=1))]
assert _if_p.race_list(_if_ps, 0, 3) == [0, 1, 2]
_if_stale = _if_it.InfoText("en", root=os.path.join(_ldc_root, "nowhere"))
assert _if_stale.state == "missing" and _if_stale.topic_list(1) == []


def _if_state(player=None):
    from core import game_state as _gsm
    _gs = _gsm.GameState()
    _gs.current_screen, _gs.player_num, _gs.num_players = 9, 0, 3
    _gs.stardate = 35024
    _gs.player_raw = [bytes(_if_mb), _rc_player_raw("Them", 1, 1, contact=(0,)),
                      _rc_player_raw("Gone", 2, 2, eliminated=1)] + \
        [bytes(_rc_player.SIZE)] * 5
    _gs.fields = [_ldw_f(1, _if_g.EXIT, 0, 27)]
    return _gs


_ldw_app.dispatcher.switch_to("info")
_if_scr = _ldw_app.dispatcher.screens["info"]
_if_scr.update(_if_state())
assert _if_scr.page == 1, "the tab the game saved (history_btns bits 4-6)"
from core import researchnative as _if_nat


def _if_click(native):
    _ldw_sent.clear()
    _p = _if_nat.window_point(native, _if_scr.layout)
    _if_scr.handle_click(_p[0] + 1, _p[1] + 1)
    return list(_ldw_sent)


import pygame as _if_pg
_if_scr.render(_if_pg.Surface((1920, 1080)))
for _k in range(5):
    _r = _if_g.tab_rect(_k)
    assert _if_click(((_r[0] + _r[2]) // 2, (_r[1] + _r[3]) // 2)) == []
    assert _if_scr.page == _k
    _if_scr.render(_if_pg.Surface((1920, 1080)))
assert _if_click((_if_g.EXIT[0] + 20, _if_g.EXIT[1] + 10)) == [("act", 1)]
_ldw_sent.clear()
_if_scr.handle_key(27)
assert _ldw_sent == [("act", 1)]
ok("the Info pages' data — Tech Review lists, the chart's rounding, the "
   "trait lines, the categories, the sorted topics, the race lists — and "
   "HD navigates the pages itself, sending only RETURN and ESC")

# ── 4. EVERY PAGE, EVERY SIZE, NOTHING CLIPPED ──────────────
_if_long = " ".join(["Scrolled words, supercalifragilisticexpialidocious"
                     "-and-then-some-more"] * 80)
_if_views = ((0, {}), (1, {"tech_tab": 0}), (2, {}), (3, {}), (4, {}),
             (4, {"ref_mode": "category", "ref_ix": 3}),
             (4, {"ref_mode": "howto", "ref_ix": 213}))
with _if_tmp.TemporaryDirectory() as _if_d:
    _if_dir = os.path.join(_if_d, "texts", "info")
    os.makedirs(_if_dir)
    for _if_name in ("reference.213.body.txt", "turns.no_block.txt",
                     "tab.reference.txt", "reference.back.txt"):
        with open(os.path.join(_if_dir, _if_name), "w",
                  encoding="utf-8") as _fh:
            _fh.write(_if_long if "body" in _if_name or "no_block" in _if_name
                      else "A-very-long-label-that-cannot-fit-a-button")
    _if_um.init(True, root=_if_d)
    try:
        _if_n = 0
        for _if_size in ((1920, 1080), (2560, 1440), (3840, 2160),
                         (2576, 1432)):
            _if_app2, _ = _ldw_plv.build_screen(*_if_size)
            _if_app2.dispatcher.switch_to("info")
            _if_x = _if_app2.dispatcher.screens["info"]
            _if_x.update(_if_state())
            for _if_page, _if_extra in _if_views:
                _if_x.page = _if_page
                for _k, _v in _if_extra.items():
                    setattr(_if_x, _k, _v)
                _if_x.render(_if_pg.Surface(_if_size))
                for _if_r, _if_b, _if_drawn in _if_x._drawn:
                    assert _if_b.left <= _if_r.left and \
                        _if_r.right <= _if_b.right, (
                            _if_size, _if_page, "a line runs out of its box",
                            _if_r, _if_b)
                    assert not _if_drawn or _if_b.contains(_if_r), (
                        _if_size, _if_page, "a drawn line is cut",
                        _if_r, _if_b)
                    _if_n += 1
                if _if_extra.get("ref_mode") == "howto":
                    _if_bx = [b for k, b in _if_x._boxes.items()
                              if str(k).startswith("ref.howto.text")]
                    assert _if_bx and _if_bx[0].overflow > 0, \
                        "the long modded body scrolls"
                if _if_page == 3:
                    assert any("supercalifragilistic" in str(_l)
                               for b in _if_x._boxes.values()
                               for _l in getattr(b, "lines", [])), \
                        "the modded placeholder is the one drawn"
    finally:
        _if_um.shutdown()
_if_dir = os.path.join(_ldc_root, "screens", "info")
_if_layout = _ldc_json.load(open(os.path.join(_if_dir, "layout.json"),
                                 encoding="utf-8"))
_if_src = "".join(open(os.path.join(_if_dir, _f), encoding="utf-8").read()
                  for _f in os.listdir(_if_dir) if _f.endswith(".py"))
for _if_key in _if_layout["marks"]:
    if _if_key == "hd_state":
        continue
    _if_word = _if_key.split("_", 1)[1]
    for _if_pre in ("extension_", "state_"):
        if _if_word.startswith(_if_pre):
            _if_word = _if_word[len(_if_pre):]
    assert _if_word in _if_src, f"{_if_key}: no module names {_if_word!r}"
assert "BUILT, NOT ACCEPTED" in _if_src.split('"""')[1] or \
    "BUILT, NOT ACCEPTED" in open(os.path.join(_if_dir, "screen.py"),
                                  encoding="utf-8").read().split('"""')[1]
assert _ldw_app.dispatcher.screen_map.get(9) == "info"
ok(f"every Info page draws at 1080p, 1440p, 2160p and 2576x1432 with long "
   f"modded texts and none of its {_if_n} lines runs out of its box or is "
   f"cut (a long body scrolls); its markings and routing stand")

# ── 5. OPEN FIX 32 — APPLIED by work order 176, and WIRED ─────────────
_if_pp = os.path.join(_ldc_root, "doc", "ext_info_screen_state.patch")
_if_patch = open(_if_pp, encoding="utf-8").read()
assert "STATUS: APPLIED 26 September 2026" in _if_patch and \
    "2269749c" in _if_patch
_if_fixes = open(os.path.join(_ldc_root, "doc", "orion2re_open_fixes.md"),
                 encoding="utf-8").read()
_if_row = next(_l for _l in _if_fixes.splitlines() if _l.startswith("| 32 |"))
assert "**Applied** 26 September 2026 by work order 176" in _if_row
assert _if_fixes.count("## 32. ") == 1 and _if_fixes.count("| 32 |") == 1
_if_sec32 = _if_fixes[_if_fixes.index("## 32. "):]
_if_sec32 = _if_sec32[:_if_sec32.index("\n## ", 6)] if "\n## " in \
    _if_sec32[6:] else _if_sec32
assert _if_sec32.rstrip().endswith("complete either way."), \
    "entry 32 ends whole (no later section cut into it)"
assert '"MOX::_bill_savegame[i]"' in open(os.path.join(
    _ldc_root, "tools", "version_check.py"), encoding="utf-8").read()
if _ldc_tree is not None and os.path.exists(os.path.join(
        _ldc_tree, "src", "ext", "ext_api.cpp")):
    _if_api = os.path.join(_ldc_tree, "src", "ext", "ext_api.cpp")
    with _if_tmp.TemporaryDirectory() as _if_t:
        os.makedirs(os.path.join(_if_t, "src", "ext"))
        with open(_if_api, "rb") as _src, open(os.path.join(
                _if_t, "src", "ext", "ext_api.cpp"), "wb") as _dst:
            _dst.write(_src.read())
        _if_run = _ldc_sp.run(["patch", "-R", "-p1", "--dry-run", "-i",
                               _if_pp], cwd=_if_t, capture_output=True,
                              text=True)
        assert _if_run.returncode == 0, _if_run.stdout + _if_run.stderr
else:
    report("open fix 32 NOT checked against ext_api.cpp — no orion2re tree")
# The block parses from real wire bytes: after OFFS's place, whole or None.
from core import game_state as _if_gsm
_if_tail = b"INFS" + _ld_st.pack("<6h", 2, 0, 3, 1, 2, 5) + \
    _ld_st.pack("<h", 2) + _ld_st.pack("<h", 5) + b"Hello" + \
    _ld_st.pack("<h", 4) + b"\x88 ok"
assert _ldw_snapshot(_ldw_recs, screen=9).info_screen is None, "no block"
_if_s = _ldw_snapshot(_ldw_recs, screen=9, tail=_if_tail)
assert _if_s.info_screen == {"bill": [2, 0, 3, 1, 2, 5],
                             "messages": [b"Hello", b"\x88 ok"]}, \
    _if_s.info_screen
assert _ldw_snapshot(_ldw_recs, screen=9, tail=_if_tail[:-2]).info_screen \
    is None, "a cut block is None, never one message fewer"
assert _if_p.messages(_if_s.info_screen) == ["Hello", "\u00ea ok"]
assert _if_p.year("SD: \u00ea", 35024) == "SD: 3502.4"
# The history: turn count from the stardate, divisors applied, ten smoothing
# passes, the scale ladder, the step and the labels (info.cpp:1222-1643).
assert _if_p.history_length(35024, [2, 0, 1, 1, 1, 1]) == (0, 24)
assert _if_p.history_length(35000 + 400, [2, 17, 1, 1, 1, 1]) == (17, 350)
assert _if_p.x_step(35024) == 10 and _if_p.x_step(35100) == 2
assert _if_p.x_labels(35024)[:3] == ["3500", "3500.5", "3501"]
assert _if_p.smooth([0, 30, 0, 0]) != [0, 30, 0, 0]
_if_hp = bytearray(_if_mb)
_if_off = {_n: _o for _n, _o, _k in _rc_player.SPEC.fields}
for _t in range(24):
    _if_hp[_if_off["population_history"] + _t] = 10 + _t
_if_hist = [_rc_player.parse(bytes(_if_hp))]
_if_g2 = _if_p.history(_if_hist, [0], 0b0001, 35024, [2, 0, 4, 1, 1, 1])
assert _if_g2 is not None and _if_g2[0] == 250 and _if_g2[1] == 10
assert len(_if_g2[2][0]) == 24 and max(_if_g2[2][0]) <= 250
assert _if_p.history(_if_hist, [0], 0, 35024, [2, 0, 4, 1, 1, 1]) is None, \
    "no metric on: nothing drawn"
# Wired: with the block the pages draw curves and messages, the notices gone.
_if_state2 = _if_state()
_if_state2.info_screen = {"bill": [2, 0, 1, 1, 1, 1],
                          "messages": [b"First message.", b"Second one."]}
_if_scr.update(_if_state2)
_if_seen = []
_if_real = _if_scr.style.render_text


def _if_spy(text, *a, **k):
    _if_seen.append(text)
    return _if_real(text, *a, **k)


_if_scr.style.render_text = _if_spy
try:
    for _if_page in (0, 3):
        _if_scr.page = _if_page
        _if_scr.render(_if_pg.Surface((1920, 1080)))
finally:
    _if_scr.style.render_text = _if_real
assert any("First message." in _t for _t in _if_seen)
assert not any("open fix 32" in _t for _t in _if_seen), "a notice is drawn"
assert "3500" in _if_seen, "the history's stardate labels"
_if_state2.info_screen = None
_if_scr.update(_if_state2)
_if_seen.clear()
_if_scr.style.render_text = _if_spy
try:
    _if_scr.page = 3
    _if_scr.render(_if_pg.Surface((1920, 1080)))
finally:
    _if_scr.style.render_text = _if_real
assert any("open fix 32" in _t for _t in _if_seen), \
    "an engine without the block is told so"
ok("open fix 32 is applied (patch, list, version_check, the engine's own "
   "ext_api.cpp) and wired: INFS parses whole or not at all, the History "
   "Graph draws its curves from the divisors, the Turn Summary its "
   "messages, and only an engine without the block gets the notice")
