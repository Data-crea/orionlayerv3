# smoke-suite area: main_menu
#
# Part of the OrionLayer smoke suite — 048_main_menu_a_fallback_says_why_one_log.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (92 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 1 check(s) it holds:
#   - a fallback says why: one log line per change of decision or reason at main._verdict and nowhere 


# ── A FALLBACK SAYS WHY: IN THE LOG, AND ON THE SCREEN ──────────
#
# Work order 139 A-D, from what 138 found: the Fleets screen became
# active, answered `wants_original()`, and the window showed the
# game's own picture — indistinguishable from the HD screen never
# arriving. `fallback_reason()` already held the sentence and had
# ONE caller in the whole tree, a live tool for another screen.
#
# Four things are held here, because they are one behaviour:
#   A  every change of the decision or of the reason is one log
#      line, at the ONE place main.py decides it, and ten identical
#      frames add none
#   B  every screen switch is one line, with the game's own id
#   C  the first line of the log says which OrionLayer is running,
#      and says "unknown" rather than raising when git cannot
#   D  the reason is drawn over the game's picture, outside it,
#      and swallows no click
if slow("fallback_verdict_log"):
    import logging as _fb_logging
    import tempfile
    import types as _nt
    import main as _fb_main
    from core import config as _fb_config
    from core import fallbacknote as _fb_note

    class _FbLog(_fb_logging.Handler):
        def __init__(self):
            super().__init__()
            self.lines = []

        def emit(self, record):
            self.lines.append(f"{record.name}: {record.getMessage()}")

    class _FbScreen:
        """A screen with a reason, and one without — the two shapes A
            has to tell apart."""
        def __init__(self, reason=None, has_method=True):
            self._reason = reason
            if not has_method:
                del self.__class__.fallback_reason

        def wants_original(self):
            return self._reason is not None

        def fallback_reason(self):
            return self._reason or ""

    class _FbApp:
        """Only what `_showing_original` reads. Built by hand rather
            than through `build_screen`, because what is under test is a
            DECISION and its log line, and a real app would drag a window
            and a client in with it."""
        connected = True
        render_mode = "hd"

        def __init__(self, screen):
            self.client = _nt.SimpleNamespace(
                state=_nt.SimpleNamespace(current_screen=4))
            self.dispatcher = _nt.SimpleNamespace(
                use_original=False, top=screen, overlay=None,
                active_name="fleets", overlay_name="")
            self._reporter = _fb_note.Reporter()
            self._fallback_note = None

        _verdict = _fb_main.App._verdict
        _showing_original = _fb_main.App._showing_original

    _fb_handler = _FbLog()
    _fb_root = _fb_logging.getLogger()
    _fb_root.addHandler(_fb_handler)
    try:
        # A1/A4. READY -> fallback -> READY is EXACTLY two lines, and
        # ten identical frames in each state add nothing.
        _fb_screen = _FbScreen(None)
        _fb_app = _FbApp(_fb_screen)
        for _ in range(10):
            assert _fb_app._showing_original() is False
        _fb_first = len(_fb_handler.lines)
        assert _fb_first == 1, _fb_handler.lines
        _fb_screen._reason = "the block and the field list disagree"
        for _ in range(10):
            assert _fb_app._showing_original() is True
        assert len(_fb_handler.lines) == 2, _fb_handler.lines
        assert "original shown" in _fb_handler.lines[1]
        assert "fleets" in _fb_handler.lines[1]
        assert "game screen 4" in _fb_handler.lines[1]
        assert "the block and the field list disagree" in _fb_handler.lines[1]
        _fb_screen._reason = None
        for _ in range(10):
            assert _fb_app._showing_original() is False
        assert len(_fb_handler.lines) == 3, _fb_handler.lines
        assert "HD draws" in _fb_handler.lines[2]

        # A1 again: THE REASON CHANGING IS ALSO A CHANGE. A screen that
        # stays down for a new reason has to write a second line, or a
        # log says "it is still down" and never why it is down NOW.
        _fb_screen._reason = "no field list"
        _fb_app._showing_original()
        _fb_screen._reason = "a field this screen does not build"
        _fb_app._showing_original()
        assert len(_fb_handler.lines) == 5, _fb_handler.lines
        assert "a field this screen does not build" in _fb_handler.lines[4]

        # A1, the other half: a screen with no `fallback_reason` at all
        # says so IN AS MANY WORDS. An empty tail would read as though
        # the reason were blank by accident.
        class _FbMute:
            def wants_original(self):
                return True
        _fb_mute = _FbApp(_FbMute())
        assert _fb_mute._showing_original() is True
        assert _fb_note.NO_REASON in _fb_handler.lines[-1], _fb_handler.lines[-1]
        # ...and it draws NO note: a panel over the game's picture
        # saying "no reason given" is noise.
        assert _fb_mute._fallback_note is None

        # A2. THE RULE IS NOT ABOUT FLEETS. Every screen with the method
        # goes through the same place, so the check names the ones that
        # have it rather than one of them.
        _fb_with = sorted(
            _f for _f in ("screens/fleets/screen.py",
                          "screens/research_select/screen.py")
            if "def fallback_reason" in io.open(
                os.path.join(os.path.dirname(SCREENS_DIR), _f),
                encoding="utf-8").read())
        assert len(_fb_with) == 2, _fb_with
        _fb_src = io.open(os.path.join(os.path.dirname(SCREENS_DIR),
                                       "main.py"), encoding="utf-8").read()
        assert _fb_src.count("def _verdict") == 1, (
            "the fallback verdict is decided in more than one place")
        assert "fallback_reason" not in _fb_src.replace(
            "`fallback_reason()` had exactly one", ""), (
            "main.py looks the reason up itself; the decision is made "
            "here and reported in core.fallbacknote, so the log line "
            "and the on-screen note can never disagree")
        _fb_rep = io.open(os.path.join(os.path.dirname(SCREENS_DIR),
                                       "core", "fallbacknote.py"),
                          encoding="utf-8").read()
        assert _fb_rep.count('"fallback_reason"') == 1, (
            "the reason is looked up more than once")

        # B. EVERY SCREEN SWITCH IS ONE LINE, with the game's id, and a
        # switch to the screen already active is not a switch.
        _fb_app2, _ = _pv.build_screen(1920, 1080)
        # AFTER the build: `build_screen` switches to its own screen on
        # the way up, and that line is a real one — it just is not the
        # one under test.
        _fb_handler.lines.clear()
        _fb_disp = _fb_app2.dispatcher
        _fb_gs = _nt.SimpleNamespace(current_screen=0)
        _fb_disp.switch_to("galaxy_map", _fb_gs)
        _fb_disp.switch_to("fleets", _nt.SimpleNamespace(current_screen=4))
        _fb_switch = [_l for _l in _fb_handler.lines if "screen:" in _l]
        assert len(_fb_switch) == 2, _fb_handler.lines
        assert "-> galaxy_map (game screen 0)" in _fb_switch[0], _fb_switch[0]
        assert "galaxy_map -> fleets (game screen 4)" in _fb_switch[1], \
            _fb_switch[1]
        _fb_before = len(_fb_handler.lines)
        _fb_disp.switch_to("fleets", _nt.SimpleNamespace(current_screen=4))
        assert len(_fb_handler.lines) == _fb_before, (
            "switching to the screen already active wrote a line")
    finally:
        _fb_root.removeHandler(_fb_handler)

    # C. THE BUILD LINE, both ways. The second case is FORCED rather
    # than left to the disk: a check that depends on whether this
    # machine happens to have git is the fault "a test that reads the
    # user's disk answers differently for the user" is about.
    _fb_line = _fb_config.build_line()
    assert "OrionLayer" in _fb_line and _fb_config.ORION2RE_VERSION in _fb_line
    _fb_commit, _fb_dirty = _fb_config.build_id()
    assert _fb_commit == _fb_config.UNKNOWN_BUILD or (
        len(_fb_commit) >= 7 and all(_c in "0123456789abcdef"
                                     for _c in _fb_commit)), _fb_commit
    # No repository: a real directory that is not one.
    assert _fb_config.build_id(root=tempfile.gettempdir()) == \
        (_fb_config.UNKNOWN_BUILD, None)
    # No git at all: PATH emptied, so the call raises OSError inside.
    _fb_path = os.environ.get("PATH", "")
    try:
        os.environ["PATH"] = ""
        assert _fb_config.build_id()[0] == _fb_config.UNKNOWN_BUILD
        assert _fb_config.UNKNOWN_BUILD in _fb_config.build_line()
    finally:
        os.environ["PATH"] = _fb_path

    # D. THE NOTE IS DRAWN, OUTSIDE THE PICTURE, AND SAYS SO.
    from core import helppopup as _fb_help
    from core.original_view import OriginalView as _fb_ov
    _fb_note_backdrop = _fb_help.Backdrop()
    # `placement` is the one function that says where the 4:3 picture
    # lands (decision 5), so the check asks IT rather than repeating
    # the arithmetic — the same reason `fallbacknote.render` takes the
    # rect as a parameter.
    _fb_view = _fb_ov()
    assert "HD EXTENSION" in (_fb_note.__doc__ or ""), (
        "core/fallbacknote.py no longer marks itself an HD EXTENSION; "
        "the original has no second renderer to fall back FROM")
    _fb_labels = _sjson.load(io.open(
        os.path.join(os.path.dirname(SCREENS_DIR), "assets", "shared",
                     "fallback", "labels.json"), encoding="utf-8"))
    assert _fb_labels.get("prefix") and _fb_labels.get("cut"), _fb_labels
    _fb_style = _fb_app2.style
    _fb_reason = ("A long reason, because a long one is the case that "
                  "breaks: 12 field(s) in the live list that this screen "
                  "does not build: (235, 302, 286, 323) type 7, "
                  "(345, 302, 396, 323) type 7 and 10 more. Something "
                  "else is on screen.")
    for _fb_w, _fb_h in ((1920, 1080), (2560, 1440), (3440, 1440),
                         (3840, 2160), (1440, 1080)):
        _fb_surf = pygame.Surface((_fb_w, _fb_h))
        _fb_surf.fill((7, 9, 18))
        _fb_pic = _fb_view.placement(_fb_w, _fb_h)
        _fb_rect = _fb_note.render(_fb_surf, _fb_style, _fb_app2.res,
                                   _fb_note_backdrop, _fb_reason,
                                   _fb_labels, _fb_pic)
        assert _fb_rect is not None, (_fb_w, _fb_h)
        _nx, _ny, _nw, _nh = _fb_rect
        _px, _py, _pw, _ph, _ = _fb_pic
        # OUTSIDE THE PICTURE at every window that has room. 4:3 has
        # none, and that case is allowed to overlap — it is the one the
        # order names as the exception.
        if _fb_w * 3 > _fb_h * 4 + 1:
            assert (_nx + _nw <= _px or _nx >= _px + _pw
                    or _ny + _nh <= _py or _ny >= _py + _ph), (
                f"the note covers the game's picture at {_fb_w}x{_fb_h}: "
                f"note {_fb_rect} over picture {_fb_pic[:4]}")
        # AND IT DREW INK. A band filled and left empty is the "a later
        # draw can erase an earlier one" fault with no draw at all.
        _fb_arr = pygame.surfarray.array3d(
            _fb_surf.subsurface(pygame.Rect(_fb_rect)))
        assert len(_np.unique(_fb_arr.reshape(-1, 3), axis=0)) > 3, (
            f"the note drew no text at {_fb_w}x{_fb_h}")
    # NO REASON, NO NOTE — decision 22's fallback has no screen to quote.
    _fb_surf = pygame.Surface((1920, 1080))
    assert _fb_note.render(_fb_surf, _fb_style, _fb_app2.res,
                           _fb_note_backdrop, None, _fb_labels,
                           _fb_view.placement(1920, 1080)) is None
    # A LONG REASON IS SHORTENED WITH ITS MARKER, never cut in silence.
    _fb_huge = " ".join(["word"] * 400)
    _fb_lines = _fb_note._wrap(_fb_style, _fb_huge, 20, 200,
                              _fb_note.TEXT)
    assert len(_fb_lines) > 1, "the wrapper did not wrap"
    _fb_short = _fb_note._shorten(_fb_style, _fb_huge, 20, 200, 3,
                                  _fb_note.TEXT, _fb_labels["cut"])
    assert _fb_short.endswith(_fb_labels["cut"]), _fb_short[-40:]
    assert len(_fb_note._wrap(_fb_style, _fb_short, 20, 200,
                              _fb_note.TEXT)) <= 3
    # AND IT SWALLOWS NO CLICK: `_handle_click` forwards to the game
    # whenever the original is shown, and knows nothing about the note.
    assert "fallbacknote" not in _fb_src.split("def _handle_click")[1][:600], (
        "the click handler has learned about the note; it must forward "
        "every click to the game exactly as before")

    ok("a fallback says why: one log line per change of decision or "
       "reason at main._verdict and nowhere else, one per screen "
       "switch, the build line with git and without, and the reason "
       "drawn outside the game's picture at five window shapes, "
       "shortened with its marker rather than cut")
