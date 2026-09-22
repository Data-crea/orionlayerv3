# smoke-suite area: game_menu
#
# Part of the OrionLayer smoke suite — 077a_game_menu_the_load_driver_names_a_slot.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (94 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# This one did NOT stand inside main(): it is work order 165 part D,
# the driver that loads a saved game through the GAME menu.
#
# The 3 check(s) it holds:
#   - the load driver refuses SAVE8 and any slot outside 1..10 before
#     it reads a field
#   - a slot row is named by two sources that have to agree, and one
#     row out is a refusal
#   - the file and the dialog must be talking about the same save, and
#     the counter-check is about the snapshot

# ── THE DIALOG WHERE A WRONG FIELD LOADS A GAME ──
#
# `tools/gameload.py` drives the Load dialog, which is decision 59's own
# hazard: a row does not select, it LOADS (loadsave.cpp:332-375). So the
# three things that decide WHICH row are checked here without a game —
# the driver's deciding half is pure for exactly that reason, and so is
# `screens/game_menu/nodes.py`, which it is built on.
import contextlib as _ld_ctx
import importlib.util as _ld_ilu
import io as _ld_io

_ld_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "tools", "gameload.py")
_ld_spec = _ld_ilu.spec_from_file_location("_gameload", _ld_path)
_ld = _ld_ilu.module_from_spec(_ld_spec)
_ld_spec.loader.exec_module(_ld)


class _LdRun:
    """Just enough of a `Run` to hand the driver a field list."""

    def __init__(self, rows):
        self.state = _GmState()
        self.state.fields = _gm_fields(rows)


# 1. SAVE8 IS THE REFERENCE FIXTURE and is read, never played (work
#    order 126, rule 8; `tools/fixtures.py` slices its bytes for every
#    acceptance that names the reference save). `run` is None here on
#    purpose: the refusal has to come BEFORE the first field is read,
#    so anything that touched the list would raise AttributeError
#    instead and this assert would fail.
assert _ld.REFERENCE_SLOT == 8
for _ld_bad in (_ld.REFERENCE_SLOT, 0, -1, 11, 99):
    try:
        _ld.load_slot(None, _ld_bad)
    except ValueError:
        pass
    except Exception as _ld_exc:                       # pragma: no cover
        raise AssertionError(
            f"slot {_ld_bad} was refused by {type(_ld_exc).__name__}, not "
            f"by the driver — something read the world first") from _ld_exc
    else:                                              # pragma: no cover
        raise AssertionError(f"slot {_ld_bad} was not refused at all")
ok("the load driver refuses SAVE8 and any slot outside 1..10 before it "
   "reads a field")

# 2. TWO SOURCES FOR "THIS ROW IS SLOT n", and `slot_row` needs both:
#    the row's place in the list sorted top to bottom, and the native
#    rectangle `Add_Game_Popup_Fields_` builds it at (loadsave.cpp:263).
#    The measured list in `tools/game_menu_fields.json` satisfies both.
#    One row out — the shift that would load the neighbouring slot — is
#    a refusal and not a load.
_ld_run = _LdRun(_gm_fix["load"])
for _ld_i in range(_gm_nodes.SLOTS):
    _ld_row = _ld.slot_row(_ld_run, _ld_i + 1)
    assert (_ld_row.x, _ld_row.y, _ld_row.x_end, _ld_row.y_end) == \
        _ld.row_rect(_ld_i), _ld_i
_ld_shifted = [list(r) for r in _gm_fix["load"]]
for _ld_r in _ld_shifted:
    if _ld_r[5] == _gm_nodes.TYPE_HIDDEN and _ld_r[3] - _ld_r[1] == 197:
        _ld_r[2] += 31
        _ld_r[4] += 31
try:
    _ld.slot_row(_LdRun(_ld_shifted), 1)
except _ld.livesend.WrongDialog:
    pass
else:                                                  # pragma: no cover
    raise AssertionError(
        "a Load dialog whose rows sit one row lower was accepted; the "
        "rectangle is the second source and it has to bite")
ok("a slot row is named by two sources that have to agree, and one row "
   "out is a refusal")

# 3. THE FILE AND THE DIALOG have to be talking about the same save
#    before anything is sent, and the SNAPSHOT is what says the load
#    happened. Slot 10's description is forced to "(Auto Save)" by
#    filedef.cpp:227, so file and dialog differ there BY DESIGN; the
#    active slot's colour codes come off both sides the way
#    `Remove_Embedded_Special_Codes_` takes them off (loadsave.cpp:1672).
_ld_disk = {"description": "new", "stardate": 35090}
_ld_wire = {"description": "new", "stardate": "Stardate: 3509.0"}
assert _ld.agreement(4, _ld_disk, _ld_wire) == "agrees"
assert _ld.agreement(4, None, _ld_wire) == "empty"
assert _ld.agreement(4, _ld_disk, None) == "no wire"
assert _ld.agreement(4, _ld_disk, dict(_ld_wire, description="old")) \
    .startswith("MISMATCH")
assert _ld.agreement(4, _ld_disk, dict(_ld_wire,
                                       stardate="Stardate: 3509.1")) \
    .startswith("MISMATCH")
assert _ld.agreement(10, {"description": "whatever", "stardate": 35003},
                     {"description": "(Auto Save)",
                      "stardate": "Stardate: 3500.3"}) == "agrees"
assert _ld._plain("\x03new\x01") == "new" and _ld._plain("new") == "new"
_ld_was = {"stardate": 35003, "players": 2, "stars": 54, "colonies": 28}
_ld_now = {"stardate": 35090, "players": 5, "stars": 54, "colonies": 22}
_ld_rec = {"file": _ld_disk, "arrived": True,
           "before": _ld_was, "after": _ld_now}
with _ld_ctx.redirect_stdout(_ld_io.StringIO()):
    assert _ld.check_loaded(_ld_rec) is True
    assert _ld.check_loaded(dict(_ld_rec, arrived=False)) is False
    assert _ld.check_loaded(dict(_ld_rec, after=_ld_was)) is False
ok("the file and the dialog must be talking about the same save, and "
   "the counter-check is about the snapshot")
