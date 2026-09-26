# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 021_core_option_strings_derived_from_the_user.py.
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
#   - the extractor keeps every string's own spaces and line breaks; format-1 files are stale (175)
#   - option strings, derived from the user's ESTRINGS.LBX (); the TECHNAME and ESTRINGS walks stay ap


# THE TWO LOADERS MUST NEVER READ EACH OTHER'S FILE. The walks
# are different — `Advance_To_Next_String_` (techinit.cpp:11-21)
# skips a whole run of NULs, `Load_E_Strings_` (estrings.cpp:33-36)
# steps `strlen + 1` and keeps empties — so crossing them
# mis-indexes the result SILENTLY, which is the failure mode this
# commit already met once. Asserted three ways: the paths differ,
# neither module names the other's file, and the two walks are
# shown to disagree on the same bytes.
assert _es.string_file("en") != _bn.name_file("en")
import tools.estrings_extract as _ee
import tools.techname_extract as _te
for _mod, _forbidden in ((_es, "techname"), (_ee, "techname"),
                         (_bn, "estrings"), (_te, "estrings")):
    _text = open(_mod.__file__, encoding="utf-8").read().lower()
    # The DOCSTRINGS compare the two on purpose, so only the code
    # is searched — a mention in prose is what keeps the two
    # walks from being confused, not what confuses them.
    _code = "\n".join(l for l in _text.splitlines()
                       if not l.strip().startswith("#"))
    _code = _code.split('"""')
    _code = "".join(_code[i] for i in range(0, len(_code), 2))
    assert _forbidden + ".lbx" not in _code, (
        f"{os.path.basename(_mod.__file__)} names "
        f"{_forbidden}.lbx in its code. The two string tables "
        f"live in different files and are walked differently; a "
        f"loader that reaches for the other's file mis-indexes "
        f"every entry after the first gap and looks like data")
_probe = b"A\x00\x00B\x00"
_te_walk = [b.decode() for b in _te.split_block(_probe)]
_ee_walk = [b.decode() for b in
            _ee.split_block(b"\x00\x00\x00\x00" + _probe, 4)]
assert _te_walk[:2] == ["A", "B"], _te_walk
assert _ee_walk[:3] == ["A", "", "B"], (
    f"the ESTRINGS walk swallowed the empty string ({_ee_walk!r}). "
    f"`Load_E_Strings_` steps strlen+1 and an empty entry is "
    f"valid; skipping NUL runs is TECHNAME's walk and would shift "
    f"every index after the first gap")
assert _ee.HEADER_SIZE == 4, (
    "the LBX entry header is not 4 bytes any more. "
    "Farload_Library_Data_ reads total_count and element_size as "
    "two uint16s and seeks past both (farload.cpp:88-92, :107)")
ok(f"option strings, derived from the user's ESTRINGS.LBX "
   f"({_es_note}); the TECHNAME and ESTRINGS walks stay apart")


# ── THE EXTRACTOR KEEPS THE BYTES (work order 175, 167's parked X) ──
# `decode` stripped every string: 96 ESTRINGS and 32 HESTRNGS entries
# lost a leading or trailing space or a trailing line break — ", the ",
# "%s Fleet: ", "  no", "Beam OCV: " — and a title read "Slith,
# theRebel Pilot". The walk is unchanged; the decode keeps what the
# file has; both loaders refuse a format-1 file as stale.
import estrings_extract as _xk
import tempfile as _xk_tmp
from core import estrings as _xk_es, hestrings as _xk_hs
for _xk_raw in (b", the ", b"%s Fleet: ", b"  no", b" ", b"text\n\n"):
    assert _xk.decode(_xk_raw) == _xk_raw.decode("cp437"), _xk_raw
_xk_blob = (b"\x03\x00\x20\x00" + b" %s gains a level\x00"
            + b"Beam OCV: \x00" + b"lore\n\n\x00")
assert [_xk.decode(_r) for _r in _xk.split_block(_xk_blob, 3)] == [
    " %s gains a level", "Beam OCV: ", "lore\n\n"]
assert _xk_es.FORMAT_VERSION == 2 and _xk_hs.FORMAT_VERSION == 2
with _xk_tmp.TemporaryDirectory() as _xk_d:
    _xk_path = os.path.join(_xk_d, *_xk_hs.string_file("en").split("/"))
    os.makedirs(os.path.dirname(_xk_path))
    with open(_xk_path, "w", encoding="utf-8") as _f:
        json.dump({"format": 1, "strings": [""] * _xk_hs.HSTRINGS_COUNT}, _f)
    assert _xk_hs.HStrings("en", root=_xk_d).state == "stale", \
        "a stripped (format 1) file was read as current"
assert "puts the one space back" not in open(os.path.join(
    SCREENS_DIR, "leaders", "ldrrows.py"), encoding="utf-8").read(), \
    "the Leaders workaround for the stripped space is back"
ok("the string extractor keeps every string's own spaces and line breaks "
   "(format 2); a format-1 file is stale; the Leaders workaround is gone")
