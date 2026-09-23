# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 085a_core_a_stand_in_field_list_is_numbered.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (101 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# This one did NOT stand inside main(): it is work order 165 part H,
# two faults Data found by reading a report.
#
# The 2 check(s) it holds:
#   - a stand-in for state.fields is numbered the way parse_fields
#     numbers, and the RAW fixtures that keep slot 0 are told apart
#   - a send counter puts the client back and hands out a copy, so a
#     step's number cannot grow after it was taken

# ── A DOUBLE THAT DISAGREES WITH THE WIRE ──
#
# Work order 131 part E's lesson, and 165 part D already paid for it
# once: a test double written by the same hand as the code shares its
# mistakes. `_rl_list` numbered its fields from 0 while `state.fields`
# starts at 1 — `parse_fields` drops slot 0 and renumbers nothing (work
# order 142 B, the block above) — so a check that printed an index
# printed one the wire cannot produce. Worse, the value it produced was
# 0, which is exactly the send 142 B's own note names as the symptom of
# the fault it had just fixed: "a stale hotkey in slot 0 would have
# sent ACTIVATE_FIELD 0".
#
# Data caught it on 23 September 2026 by reading a counter-test's
# output against a live run's, and asking why one said 0 and the other
# said 1.
assert min(_f.index for _f in _z0_fields) == 1, (
    "parse_fields no longer starts at 1; the rule these doubles copy "
    "has moved and they have not")
for _si_mode in (True, False):
    _si_rows = _rl_list(_rl_entries, select_mode=_si_mode)
    assert _si_rows, _si_mode
    assert [_f.index for _f in _si_rows] == \
        list(range(1, len(_si_rows) + 1)), (
            _si_mode, [_f.index for _f in _si_rows][:6])
    assert all(_f.index != 0 for _f in _si_rows), _si_mode

# AND THE RAW FIXTURES THAT DO CARRY SLOT 0 ARE A DIFFERENT THING, so
# they are named here rather than swept up. `tools/game_menu_fields.json`
# records the list as the ENGINE writes it, dummy included, because
# `screens/game_menu/nodes.py` is tested on being robust to it —
# `nodes.real()` drops index 0 itself, which is the per-consumer filter
# work order 142 B deliberately left in place.
_si_gm = _gm_fields(_gm_fix["load"])
assert any(_f.index == 0 for _f in _si_gm), (
    "the GAME menu fixture has lost its slot 0; it is the RAW list on "
    "purpose, and nodes.real() is tested against it")
assert all(_f.index != 0 for _f in _gm_nodes.real(_si_gm))
ok("a stand-in for state.fields is numbered the way parse_fields "
   "numbers, and the RAW fixtures that keep slot 0 are told apart")

# ── A NUMBER THAT GREW AFTER IT WAS TAKEN ──
#
# The second fault in the same report. `tools/livedrive.SendCounter`
# WRAPS the client's three send methods, so a second counter wraps the
# first: every send after that increments both. A step that stored the
# LIVE dict wrote down a number that was true when it was printed and
# false afterwards — a record said `activate_field: 3` for a step whose
# own line said 0.
import importlib.util as _si_ilu

_si_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "tools", "livedrive.py")
_si_src = io.open(_si_path, encoding="utf-8").read()
# `livedrive` imports pygame and `main.App`, so the class is taken out
# of the file by ast rather than by importing the module.
import ast as _si_ast

_si_tree = _si_ast.parse(_si_src)
_si_cls = next(n for n in _si_tree.body
               if isinstance(n, _si_ast.ClassDef)
               and n.name == "SendCounter")
_si_ns = {}
exec(compile(_si_ast.Module(body=[_si_cls], type_ignores=[]),
             _si_path, "exec"), _si_ns)
_SiCounter = _si_ns["SendCounter"]


class _SiClient:
    def __init__(self):
        self.log = []

    def activate_field(self, i):
        self.log.append(i)

    def inject_click(self, x, y):
        self.log.append((x, y))

    def inject_key(self, k):
        self.log.append(k)


_si_client = _SiClient()


def _si_unwrapped():
    """True when the client's method is its OWN again.

    Compared by `__func__`, not by identity: attribute access builds a
    fresh bound method every time, so `is` is false even for the real
    one — while the counter's replacement is a closure with no
    `__func__` at all.
    """
    return getattr(_si_client.activate_field, "__func__",
                   None) is _SiClient.activate_field


assert _si_unwrapped()
with _SiCounter(_si_client) as _si_outer:
    _si_client.activate_field(1)
    # THE SNAPSHOT IS A COPY, and this is the half that actually bit:
    # the record stored the LIVE dict, so a step's number went on
    # growing after the step was over. Taken here, while the counter is
    # still active, because a released one counts nothing more and
    # could not tell a copy from an alias.
    _si_counts, _si_sent = _si_outer.snapshot()
    with _SiCounter(_si_client) as _si_inner:
        _si_client.activate_field(2)
    _si_inner_counts, _si_inner_sent = _si_inner.snapshot()
    # The inner step saw its own send…
    assert _si_inner_counts["activate_field"] == 1, _si_inner_counts
    assert _si_inner_sent == [("activate_field", (2,))], _si_inner_sent
    # …and once released, it stops seeing anything.
    _si_client.activate_field(3)
    assert _si_inner.snapshot()[0]["activate_field"] == 1, (
        "a released counter is still counting; it never put the "
        "client's own method back")
    # The OUTER one saw all three, and the snapshot taken after the
    # first did not move with it.
    assert _si_outer.counts["activate_field"] == 3, _si_outer.counts
    assert _si_counts["activate_field"] == 1, (
        f"the snapshot moved with the counter: {_si_counts}")
    assert len(_si_sent) == 1, _si_sent
# AND THE CLIENT IS ITSELF AGAIN when the last counter is released.
_si_client.activate_field(4)
assert _si_outer.counts["activate_field"] == 3, _si_outer.counts
assert _si_unwrapped(), (
    "the client is still wrapped after every counter was released")
assert _si_client.log == [1, 2, 3, 4], _si_client.log
# ── AND THERE IS ONE OF IT ──
#
# Work order 166 part E. `tools/colony_move_hd.Counter` stood beside
# `SendCounter` doing the same job — SendCounter was written from it —
# so when 165 H found that a counter which never puts the client back
# keeps counting the steps after it, only the younger one was repaired
# and nobody was going to fix the same fault twice. The older one is
# gone and its three callers take this one.
#
# Read by `ast`, not by a grep: a class is what is being counted, and
# a name in a comment is not one.
_si_classes = []
for _si_name in sorted(os.listdir(os.path.join(
        os.path.dirname(SCREENS_DIR), "tools"))):
    if not _si_name.endswith(".py"):
        continue
    _si_file = os.path.join(os.path.dirname(SCREENS_DIR), "tools",
                            _si_name)
    for _si_node in _si_ast.walk(_si_ast.parse(
            io.open(_si_file, encoding="utf-8").read())):
        if not isinstance(_si_node, _si_ast.ClassDef):
            continue
        _si_body = _si_ast.dump(_si_node)
        # A COUNTER REPLACES the client's methods; a stub client
        # merely defines them (`colony_list_preview._Client`). So
        # `setattr` is part of the shape being counted, or the test
        # counts every fake client in the tree.
        if (all(_si_w in _si_body for _si_w in
                ("activate_field", "inject_click", "inject_key"))
                and "setattr" in _si_body):
            _si_classes.append(f"{_si_name}:{_si_node.name}")
assert _si_classes == ["livedrive.py:SendCounter"], (
    f"the tree has {len(_si_classes)} classes that wrap the client's "
    f"three send paths: {_si_classes}. One of them will be repaired "
    f"and the others will not — which is what work order 166 part E "
    f"closed")
ok("a send counter puts the client back and hands out a copy, so a "
   "step's number cannot grow after it was taken — and the tree has "
   "exactly one of them")
