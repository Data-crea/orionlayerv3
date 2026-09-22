# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 055_core_help_json_marks_the_auto_sizing.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (90 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 2 check(s) it holds:
#   - help.json marks the auto-sizing panel ( files, tree-wide)
#   - help: right click opens, left click is swallowed


# The auto-sizing panel is a marked HD EXTENSION: the original
# draws a fixed box and lets FMTPARA wrap into it at a fixed
# 339 px (textbox.cpp:307), which at four HD resolutions either
# wastes half the screen or clips a long entry. `helppopup.py`
# and the fundament both said the marking also stood in
# `screens/*/help.json`. It stood in none of the three, for as
# long as both documents claimed it — which is how a marking
# rots: nothing reads it, so nothing notices it left.
#
# Walked over the tree rather than over a list of screens. A list
# is a second thing to remember, and the file this rule is for is
# the one somebody adds next year. Mods are included: a mod that
# ships its own help.json ships the same popup and inherits the
# same deviation.
_tree = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_help_files = []
for _dir, _subs, _files in os.walk(_tree):
    if "__pycache__" in _dir or os.sep + ".git" in _dir:
        continue
    if "help.json" in _files:
        _help_files.append(os.path.join(_dir, "help.json"))
assert _help_files, "no help.json in the tree at all"
for _hf in sorted(_help_files):
    _rel = os.path.relpath(_hf, _tree)
    with open(_hf, encoding="utf-8") as _fh:
        _note = _hjson.load(_fh).get("hd_extension", "")
    assert _note, (
        f"{_rel} carries no top-level 'hd_extension': the "
        f"auto-sizing help panel is a deviation from the original "
        f"and has to say so where it is read")
    # Not just the key — the reason. A marking that does not name
    # what the original does instead is a label, not a record.
    assert "339" in _note, (
        f"{_rel}: hd_extension does not name the original's fixed "
        f"339 px wrap")
ok(f"help.json marks the auto-sizing panel "
   f"({len(_help_files)} files, tree-wide)")

# Right click opens, left click closes and does NOT reach the game
d.switch_to("main_menu")
_mmh = d.active
_mmh.update(None)
_btn = next(b for b in _mmh.boxes if b.name == "new_game")
_cx, _cy = _btn.screen_rect.center

class _RecClient(FakeClient):
    def __init__(self): self.acts = []
    def activate_field(self, fid): self.acts.append(fid)

_prev_c, _prev_conn = app.client, app.connected
app.client, app.connected = _RecClient(), True
assert _mmh.handle_right_button(True, _cx, _cy) is True
assert _mmh.help.visible and _mmh.help.help_id == 647, _mmh.help.help_id
_mmh.render(surf)
_mmh.handle_click(_cx, _cy)
assert not _mmh.help.visible, "left click did not close the popup"
assert app.client.acts == [], \
    f"the swallowed click reached the game: {app.client.acts}"
# Now that it is closed the same click has to work normally again.
_mmh.handle_click(_cx, _cy)
assert app.client.acts == [3], app.client.acts
# Outside every region, a right click does nothing at all — the
# original has no help box over empty screen here either.
assert _mmh.handle_right_button(True, 5, 5) is False
app.client, app.connected = _prev_c, _prev_conn
ok("help: right click opens, left click is swallowed")
