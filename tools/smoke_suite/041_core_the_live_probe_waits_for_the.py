# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 041_core_the_live_probe_waits_for_the.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (91 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 1 check(s) it holds:
#   - the live probe waits for the effect too (same rule, second loop, asserted rather than assumed)


# AND THE PROBE HAS THE SAME WAIT, because it is the tool that
# runs against a live game and it got this wrong twice: once by
# waiting for a fresh STATE while reading the FRAME, and once by
# waiting for a fresh frame that was still the pre-effect one.
# Two loops rather than one shared helper — this one blocks and
# the chain's is driven a frame at a time — so the rule is
# asserted in both places rather than assumed to have travelled.
import importlib.util as _ilu
_pb_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "tools", "colony_move_probe.py")
_pb_spec = _ilu.spec_from_file_location("_probe", _pb_path)
_pb = _ilu.module_from_spec(_pb_spec)
_pb_spec.loader.exec_module(_pb)

class _PollClient:
    def __init__(self):
        self.stats = {"state": 0, "visual": 0}
        self.state = type("S", (), {"framebuffer": b"\0"})()
    def poll(self):
        self.stats["state"] += 1
        self.stats["visual"] += 1

_pb_c = _PollClient()
_pb_seen = []
assert _pb.after_send(_pb_c, lambda st: _pb_seen.append(
    _pb_c.stats["state"]) or True, tries=4) is not None
assert _pb_seen and min(_pb_seen) >= 2, (
    f"the probe's after_send accepted the world at pair "
    f"{min(_pb_seen)}; the first pair after a send is serialized "
    f"in the tick that consumed it")
_pb_c2 = _PollClient()
assert _pb.after_send(_pb_c2, lambda st: False, tries=3) is None, (
    "a predicate that never holds must time out, not settle")
ok("the live probe waits for the effect too (same rule, second "
   "loop, asserted rather than assumed)")
