# smoke-suite area: colony_summary
#
# Part of the OrionLayer smoke suite — 040_colony_summary_pop_move_on_the_wire_one.py.
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
#   - pop move on the wire (ONE command, the pre-effect pair is refused, a refusal is reported and not


# ── The send waits for an EFFECT, and the first pair is early ──
# ext::Tick() calls ProcessInput() BEFORE it serializes anything
# (ext_api.cpp:341-386), so the tick that consumes an injected
# command also ships the world from before the game acted on it.
# Measured 5 September 2026 against the running game: one
# increment of the list window read _first unchanged on the first
# state/visual pair and moved on the second. A chain that
# accepted the first pair would confirm every step one tick early
# — and then aim the next click at a window that has not moved.
class _SendClient:
    def __init__(self):
        self.stats = {"state": 0, "visual": 0}
        self.clicks, self.fields, self.keys = [], [], []
        self.jobs = []
        self.order = []          # what went out, in order
    def inject_click(self, x, y):
        self.clicks.append((x, y)); self.order.append(("click", (x, y)))
    def activate_field(self, f):
        self.fields.append(f); self.order.append(("field", f))
    def inject_key(self, k):
        self.keys.append(k); self.order.append(("key", k))
    def set_jobs(self, colony, pairs):
        self.jobs.append((colony, list(pairs)))
        self.order.append(("jobs", (colony, list(pairs))))

class _SendField:
    def __init__(self, index, x, y):
        self.index, self.x, self.y = index, x, y

class _SendState:
    def __init__(self, raws, framebuffer=None, fields=()):
        self.colonies_raw = list(raws)
        self.framebuffer = framebuffer
        self.fields = list(fields)

def _thumb_frame(n, first):
    """A 640x480 index buffer with the scroll thumb drawn at
        `first` — the channel `_first` is read back through."""
    _y1, _y2 = _cf.thumb_bounds(n, first)
    _buf = bytearray(640 * 480)
    for _y in range(_y1 + 1, _y2):
        for _x in range(_cf.THUMB_X0, _cf.THUMB_X1 + 1):
            _buf[_y * 640 + _x] = _cf.THUMB_FILL
    return bytes(_buf)

_sd_off = dict((n, o) for n, o, _k in _cst.SPEC.fields)

def _raw_with(pops, n_pops=3):
    _b = bytearray(_cst.SPEC.size)
    _b[_sd_off["owner"]] = 0
    _b[_sd_off["n_pops"]] = n_pops
    _b[_sd_off["max_farms"]] = 255
    for _i, _w in enumerate(pops):
        struct.pack_into("<I", _b, _sd_off["pop"] + 4 * _i, _w)
    return bytes(_b)

_sd_pops = [_icon_pop(0, 0), _icon_pop(0, 0), _icon_pop(0, 0)]
_sd_cluster = _cm.Cluster([2])
_sd_pred = _cm.predict_pops(_sd_pops, 3, 255, _sd_cluster, 1)
_sd_held = list(_sd_pops)
_sd_held[2] &= ~_cst.POP_MASK_ASSIGNED

_sd_c = _SendClient()
_sd = _cse.Send(_sd_c, colony=0, target_job=1,
                cluster=_sd_cluster, predicted=_sd_pred)

# ONE MESSAGE, SENT IN THE CONSTRUCTOR, and nothing else on the
# wire. Until 10 September 2026 this was RESORT -> ESTABLISH ->
# PICK -> DROP: a sort key, a run of window steps and two clicks,
# because a click names a SLOT and the game's ten-row window had
# to be steered under the target row first. `MSG_SET_JOBS` names
# the colony (fundament 52), so all four are gone and the only
# thing that goes out is the list.
assert _sd.state == _cse.SENT, _sd.state
assert _sd_c.jobs == [(0, [(2, 1)])], _sd_c.jobs
assert _sd_c.clicks == [] and _sd_c.keys == [] and _sd_c.fields == [], (
    f"the move put something other than one command on the wire: "
    f"clicks {_sd_c.clicks}, keys {_sd_c.keys}, "
    f"fields {_sd_c.fields}")
assert [_k for _k, _v in _sd_c.order] == ["jobs"], _sd_c.order

# THE PRE-EFFECT PAIR IS REFUSED even though the predicate is
# already true on it. This is the whole assertion, and it did not
# change with the transport: ext::Tick() consumes input before it
# serializes, so the first snapshot after a send is the world
# from before the game acted.
_sd_c.stats["state"] += 1
_sd_c.stats["visual"] += 1
_sd.update(_SendState([_raw_with(_sd_pred)]))
assert _sd.state == _cse.SENT, (
    f"the send was confirmed by the FIRST snapshot after it "
    f"({_sd.state}); that snapshot is serialized in the tick that "
    f"consumed the command and cannot carry its effect")
_sd_c.stats["state"] += 1
_sd_c.stats["visual"] += 1
_sd.update(_SendState([_raw_with(_sd_pred)]))
assert _sd.state == _cse.DONE and _sd.finished, _sd.state
assert len(_sd_c.jobs) == 1, (
    f"the move went out more than once: {_sd_c.jobs}")

# THE LIST IS ASCENDING, because the engine applies it in order
# and `predict_pops` walks the pop array from index 0
# (colmove.cpp:160-176). A cluster handed over out of order would
# make the command and the prediction two different walks.
_sd_c5 = _SendClient()
_cse.Send(_sd_c5, colony=3, target_job=2,
          cluster=_cm.Cluster([5, 1, 4]), predicted=_sd_pred)
assert _sd_c5.jobs == [(3, [(1, 2), (4, 2), (5, 2)])], _sd_c5.jobs

# AN UNCONFIRMED MOVE IS REPORTED, NOT RETRIED. The engine rolls
# a refused list back whole (fundament 52), so the predicted pops
# never appear and the wait runs out. HD checks the same rules
# before sending (decision 33), so this is a DISAGREEMENT between
# the two sides and not a normal outcome — and an unpatched
# engine, which drops the message entirely, looks the same from
# here. `tools/version_check.py` is what tells those apart.
_sd_c3 = _SendClient()
_sd3 = _cse.Send(_sd_c3, colony=0, target_job=1,
                 cluster=_sd_cluster, predicted=_sd_pred)
_sd3._wait.deadline = 0.0                  # expire it
_sd3.update(_SendState([_raw_with(_sd_pops)]))
assert _sd3.state == _cse.FAILED and _sd3.reason == "move_unconfirmed", (
    f"{_sd3.state}, {_sd3.reason}")
assert len(_sd_c3.jobs) == 1, "an unconfirmed move was sent again"

# A CLUSTER THE GAME HOLDS IS ITS OWN STATE, still. Nothing HD
# does can create one now — the command never picks a pop up, and
# the engine refuses MSG_SET_JOBS outright while
# `_cluster_colony_n != -1` — so this can only come from the
# game's own window. It is reported as HOLDING rather than as
# "nothing happened", because only the player can end it.
_sd_c2 = _SendClient()
_sd2 = _cse.Send(_sd_c2, colony=0, target_job=1,
                 cluster=_sd_cluster, predicted=_sd_pred)
_sd_wrong = list(_sd_pops)
_sd_wrong[0] &= ~_cst.POP_MASK_ASSIGNED     # a pop in the air
_sd2._wait.deadline = 0.0
_sd2.update(_SendState([_raw_with(_sd_wrong)]))
assert _sd2.state == _cse.HOLDING and _sd2.holding, _sd2.state
assert _sd2.reason == "game_holds_cluster", _sd2.reason

# THE FLOOR'S REASON HAS TO STAND BESIDE THE FLOOR. It is a
# count, and decision 21 refuses counted waits — so the next
# reader must find the argument at the constant, or they will
# read it as a settling time and make it three.
for _path, _needle in (
        # the argument, in its one home...
        (("core", "wire_protocol.py"),
         "IT IS NOT A SETTLING TIME, AND DECISION 21 IS WHY"),
        # ...and a pointer to it from each reader, so nobody
        # meets the number without the reason.
        (("screens", "colony_summary", "colonysend.py"),
         "wire_protocol"),
        (("tools", "colony_move_probe.py"),
         "core.wire_protocol.EFFECT_PAIRS")):
    _src = open(os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        *_path)).read()
    assert _needle in _src, (
        f"{'/'.join(_path)} no longer explains why its pre-effect "
        f"floor is not a duration; the count is the exact "
        f"structural gap and raising it starts skipping evidence")
assert _cse.EFFECT_PAIRS == _wire.EFFECT_PAIRS == 2, (
    f"EFFECT_PAIRS is {_cse.EFFECT_PAIRS}; two is the consuming "
    f"tick plus the first that can show the effect, and the "
    f"assertions above pin both sides of it")
assert _scr_op._data["move"].get("stranded"), (
    "there is no wording for a held cluster, which is the one "
    "state only the player can end")

# THE WINDOW-STEPPING TESTS ARE GONE WITH THE CODE. Until
# 10 September 2026 this block asserted that a Send led with
# `GameWindow.max_first(n)` decrements before every pick-up, so
# `_first` was ESTABLISHED and never remembered (decision 46).
# A command addressed by colony index steers no window, so
# there is nothing left here to assert — the decision is not
# retired, it moved to the only caller that still has a window:
# `colonyscroll`, and `colonyselect.GameWindow` keeps its own
# checks above. Recorded rather than silently dropped, because
# a check that disappears with no note is indistinguishable
# from one nobody noticed breaking.
assert not hasattr(_cse, "STEP_UP_XY"), (
    "colonysend still carries the window steppers; they belong "
    "to colonyscroll now (ARROW_UP_XY/ARROW_DOWN_XY) and two "
    "homes for one pair of coordinates is how they drift")
for _gone in ("RESORT", "ESTABLISH", "PICK", "DROP"):
    assert not hasattr(_cse, _gone), (
        f"colonysend still defines the chain state {_gone}; the "
        f"click chain is deleted, not kept as a fallback — two "
        f"paths that move pops is the duplicate fundament 52 "
        f"exists to refuse")
ok("pop move on the wire (ONE command, the pre-effect pair is "
   "refused, a refusal is reported and not retried, the four "
   "chain states and the window stepping are gone)")
