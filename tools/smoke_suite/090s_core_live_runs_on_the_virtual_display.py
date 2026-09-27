# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 090s_core_live_runs_on_the_virtual_display.py.
# `tools/smoke_test.py` executes this file, and every other module in
# tools/smoke_suite/, in file-name order and in ONE namespace. Do not
# import this file; it is not a module.
#
# The 2 check(s) it holds:
#   - an engine a live run starts goes onto the virtual display; the real desktop only with a named reason
#   - every runnable tool that loads pygame forces SDL's dummy drivers, whatever the shell exports; the real desktop only with a named reason


# ── LIVE RUNS NEVER OPEN A WINDOW IN THE USER'S SESSION (work order 182) ──
#
# Data works at the same desktop while live runs happen; until 182 the
# engine's window opened in front of him and his clicks could land between
# a run's inputs. `tools/vdisplay.py` is the one home of the rule: an
# ENGINE starts on a private Xvfb, a CLIENT gets SDL's dummy drivers
# FORCED, and Data's session only with `--real-desktop REASON`. Both halves
# are asserted by their EFFECT, not by grepping for a call: the client half
# imports every tool in a fresh process with `SDL_VIDEODRIVER=x11`
# exported — the variable CLAUDE.md's live recipe exports — and reads
# what the import left.
import subprocess as _vd_sp
import vdisplay as _vd
import engine_start as _vd_es

_vd_root = os.path.dirname(SCREENS_DIR)
_vd_tools = os.path.join(_vd_root, "tools")

# 1. THE ENGINE. `ensure` is replaced so the check starts no Xvfb.
_vd_real_ensure = _vd.ensure
_vd.ensure = lambda out=print: (":97", 4242, "/nonexistent/xauth")
try:
    _vd_env = _vd_es.run_env(None, out=lambda *_: None)
    assert _vd_env["DISPLAY"] == ":97" and not _vd.is_session_display(_vd_env), \
        _vd_env.get("DISPLAY")
    assert _vd_env["SDL_VIDEODRIVER"] == "x11" and \
        _vd_env["SDL_AUDIODRIVER"] == "dummy" and \
        _vd_env["ORION2RE_NO_VSYNC"] == "1"
    assert "WAYLAND_DISPLAY" not in _vd_env
    _vd_seen = []
    _vd_real = _vd_es.run_env("equivalence proof", out=_vd_seen.append)
    assert _vd_real["DISPLAY"] == ":0" and _vd.is_session_display(_vd_real)
    assert any("equivalence proof" in _l for _l in _vd_seen), \
        "the real desktop's reason must be printed"
finally:
    _vd.ensure = _vd_real_ensure
# The flag: a reason, or a refusal; the environment variable too.
assert _vd.real_desktop_reason([], {}) is None
assert _vd.real_desktop_reason(["--real-desktop", "why"], {}) == "why"
assert _vd.real_desktop_reason(["--real-desktop=why"], {}) == "why"
assert _vd.real_desktop_reason([], {_vd.ENV_FLAG: "why"}) == "why"
for _vd_bad in (["--real-desktop"], ["--real-desktop", "--orders"],
                ["--real-desktop="]):
    try:
        _vd.real_desktop_reason(_vd_bad, {})
        raise AssertionError(f"{_vd_bad} accepted without a reason")
    except _vd.RealDesktopRefused:
        pass
assert _vd.strip_flag(["1920", "--real-desktop", "why", "--orders"]) == \
    ["1920", "--orders"]
# The engine is started with THAT environment and nothing else: the start
# passes `run_env`'s result to Popen and to the intro skip.
_vd_src = open(_vd_es.__file__, encoding="utf-8").read()
assert "env=display_env()" not in _vd_src and \
    "intro_skip.step(pid, text, env," in _vd_src and \
    "env = run_env(real_desktop, out)" in _vd_src
_vd_cli = _vd_sp.run([sys.executable, _vd_es.__file__, "--real-desktop", " ",
                      "--check"], capture_output=True, text=True)
assert _vd_cli.returncode == 2 and "needs a reason" in _vd_cli.stderr, \
    (_vd_cli.returncode, _vd_cli.stderr[-200:])
ok("an engine a live run starts goes onto the virtual display; the real "
   "desktop only with a named reason")

# 2. EVERY CLIENT. Every runnable tool that loads pygame (or a module that
# drives the App) is imported in a fresh interpreter with the SESSION's
# drivers exported, and must leave SDL's dummy drivers set. With the
# escape named in the environment, the live driver keeps the session's —
# the flag exists and is the only way.
_vd_env2 = dict(os.environ, SDL_VIDEODRIVER="x11", SDL_AUDIODRIVER="pulse",
                PYGAME_HIDE_SUPPORT_PROMPT="1")
_vd_env2.pop(_vd.ENV_FLAG, None)
_vd_pat = __import__("re").compile(
    r"(?m)^\s*(import pygame|import livedrive|from livedrive|import main\b|"
    r"import hud_evidence|import colony_move_hd|import colony_live|"
    r"import flash_walk|import colony_offline)")


def _vd_import(name, env):
    r = _vd_sp.run([sys.executable, "-c",
                    f"import sys; sys.path[0] = {_vd_tools!r}; import {name}, "
                    f"os; print(os.environ['SDL_VIDEODRIVER'], "
                    f"os.environ.get('SDL_AUDIODRIVER'))"],
                   capture_output=True, text=True, env=env, cwd="/tmp",
                   timeout=120)
    return (r.stdout.strip().splitlines() or ["?"])[-1]


_vd_names, _vd_bad = [], []
for _vd_path in sorted(glob.glob(os.path.join(_vd_tools, "*.py"))):
    _vd_name = os.path.basename(_vd_path)[:-3]
    _vd_text = open(_vd_path, encoding="utf-8").read()
    if _vd_name in ("smoke_test", "vdisplay") or "__main__" not in _vd_text \
            or not _vd_pat.search(_vd_text):
        continue
    _vd_names.append(_vd_name)
    _vd_got = _vd_import(_vd_name, _vd_env2)
    if _vd_got != "dummy dummy":
        _vd_bad.append((_vd_name, _vd_got))
assert len(_vd_names) >= 25 and {"colony_live", "colony_accept", "flash_walk",
                                 "colony_move_probe"} <= set(_vd_names), \
    _vd_names
assert not _vd_bad, f"tools that would open a window in the session: {_vd_bad}"
assert _vd_import("livedrive", dict(_vd_env2, **{_vd.ENV_FLAG: "a reason"})) \
    == "x11 pulse", "the real-desktop escape must keep the session's drivers"
ok(f"every runnable tool that loads pygame forces SDL's dummy drivers, "
   f"whatever the shell exports ({len(_vd_names)} tools); the real desktop "
   f"only with a named reason")
