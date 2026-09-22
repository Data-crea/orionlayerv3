# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 089_core_the_fundament_is_an_index_and_its_parts.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (92 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# This one did NOT stand inside main(): it is work order 164, the check
# that holds the fundament's index to its parts, and it is the only
# check that order added.
#
# The 1 check(s) it holds:
#   - the fundament is an index and its parts: every part listed, every
#     decision in exactly one of them, no rule text in the index

# ── THE INDEX AND THE PARTS HOLD EACH OTHER ──
#
# `doc/v3_fundament.md` was 200 KB and every session was supposed to
# read it at startup. Work order 164 made it an INDEX and moved the
# rules into `doc/fundament/`, nine parts, by script, with the parts
# concatenating back to the original byte for byte.
#
# What can rot afterwards is the join, and it can rot in four ways.
# Each one is asserted here:
#
#   1. a part exists that the index does not list — a rule nobody is
#      sent to, which is the same as a rule nobody reads;
#   2. the index lists a part that is not there — a link that resolves
#      to nothing, the briefs index's own failure one document over;
#   3. a decision number in two parts, or in none — the numbers are
#      IDENTITIES, cited across the tree, and the whole licence for
#      moving a decision between files was that its number does not
#      move with it;
#   4. rule text creeping back into the index — then a rule has two
#      homes and a reader is comparing copies, which is the fault this
#      project has paid for more often than any other.
import re as _fd_re

_fd_index = io.open(FUNDAMENT, encoding="utf-8").read()
_fd_head, _, _fd_own = _fd_index.partition("<!-- fundament-index -->")
assert _fd_own, (
    "doc/v3_fundament.md has lost its `<!-- fundament-index -->` "
    "sentinel. It is what separates the preamble the split kept "
    "verbatim from the list the split wrote, and it is what the "
    "identity proof strips by")

# 1 and 2 — the directory and the list, both ways.
_fd_files = sorted(f for f in os.listdir(FUNDAMENT_DIR) if f.endswith(".md"))
assert len(_fd_files) == len(os.listdir(FUNDAMENT_DIR)), (
    f"doc/fundament/ holds something that is not a .md file: "
    f"{sorted(set(os.listdir(FUNDAMENT_DIR)) - set(_fd_files))}")
assert len(_fd_files) >= 4, (
    f"only {len(_fd_files)} parts — finding the fundament nearly empty "
    f"means this check is measuring the wrong directory")
_fd_listed = set(_fd_re.findall(r"\(fundament/([\w.\-]+\.md)\)", _fd_own))
assert _fd_listed == set(_fd_files), (
    f"the index and doc/fundament/ disagree — in the directory and not "
    f"listed: {sorted(set(_fd_files) - _fd_listed)}; listed and not in "
    f"the directory: {sorted(_fd_listed - set(_fd_files))}. A rule "
    f"nobody is sent to is a rule nobody reads")

# 3 — every decision number in exactly one part.
_fd_where = {}
for _fd_f in _fd_files:
    _fd_text = io.open(os.path.join(FUNDAMENT_DIR, _fd_f),
                       encoding="utf-8").read()
    assert "<!-- fundament-body -->" in _fd_text, (
        f"{_fd_f} has lost its `<!-- fundament-body -->` sentinel; the "
        f"proof that the parts are the original text strips by it")
    for _fd_n in _fd_re.findall(r"^\*\*(\d+)\.", _fd_text, _fd_re.M):
        _fd_where.setdefault(int(_fd_n), []).append(_fd_f)
_fd_twice = {_n: _f for _n, _f in _fd_where.items() if len(_f) > 1}
assert not _fd_twice, (
    f"these decision numbers are in more than one part: {_fd_twice}. A "
    f"decision number is an identity and it has exactly one home")

# The whole document still agrees with itself: the numbers the index
# NAMES are the numbers the parts carry. The index writes them as
# ranges, so they are expanded before the comparison.
_fd_named = set()
for _fd_line in _fd_own.splitlines():
    if not _fd_line.startswith("| [`fundament/"):
        continue
    # `| file | part | KB | decisions | what it covers |` — the cell is
    # taken by POSITION, not by looking for something that resembles a
    # number: the KB column resembles one too, and a pattern that took
    # the first match compared the sizes against the decisions and
    # passed for the wrong reason.
    _fd_cells = [_c.strip() for _c in _fd_line.split("|")]
    assert len(_fd_cells) == 7, (
        f"the index's table is no longer five columns: {_fd_line[:80]}")
    for _fd_span in _fd_cells[4].split(","):
        _fd_span = _fd_span.strip()
        if "-" in _fd_span:
            _fd_a, _fd_b = _fd_span.split("-")
            _fd_named.update(range(int(_fd_a), int(_fd_b) + 1))
        elif _fd_span.isdigit():
            _fd_named.add(int(_fd_span))
assert _fd_named == set(_fd_where), (
    f"the index names decisions the parts do not carry "
    f"{sorted(_fd_named - set(_fd_where))} or misses ones they do "
    f"{sorted(set(_fd_where) - _fd_named)}")

# 4 — the index carries no rule of its own.
assert not _fd_re.search(r"^\*\*\d+\.", _fd_own, _fd_re.M), (
    "doc/v3_fundament.md carries a decision heading of its own. It is "
    "an index: it points at the parts and holds no rule text, or a "
    "rule has two homes")

# AND EVERY PART FITS WHAT A SESSION MAY READ. The same number a check
# module is held to, deliberately: both are one thing a session opens,
# and half of work order 127's 80 KB budget is what that is worth.
_fd_over = {_f: os.path.getsize(os.path.join(FUNDAMENT_DIR, _f))
            for _f in _fd_files
            if os.path.getsize(os.path.join(FUNDAMENT_DIR, _f))
            > CHECK_MODULE_LIMIT}
assert not _fd_over, (
    f"these fundament parts are over the {CHECK_MODULE_LIMIT // 1024} KB "
    f"reading limit: { {_f: _s // 1024 for _f, _s in _fd_over.items()} }. "
    f"Split the part by subject, in the text's own order, and list it "
    f"in the index")

# THE STARTUP RULE IS IN TWO FILES ON PURPOSE, so the two are held
# equal to the letter. Work order 162 found the opposite by looking,
# after a rule in CLAUDE.md had been paraphrased from the fundament's.
_fd_rule = ("Read the index `doc/v3_fundament.md` first, then the parts "
            "your task needs, and always every `principles-` part.")
_fd_flat = _fd_re.sub(r"\s+", " ", _fd_own)
_fd_claude = _fd_re.sub(r"\s+", " ", io.open(
    os.path.join(os.path.dirname(FUNDAMENT_DIR), "..", "CLAUDE.md"),
    encoding="utf-8").read())
for _fd_home, _fd_src in (("the index", _fd_flat), ("CLAUDE.md", _fd_claude)):
    assert _fd_rule in _fd_src, (
        f"{_fd_home} no longer carries the startup rule word for word: "
        f"{_fd_rule!r}. It is deliberately in both files, so the two "
        f"read the same or neither is trustworthy")

ok(f"the fundament is an index and {len(_fd_files)} parts: every part "
   f"listed both ways, {len(_fd_where)} decisions each in exactly one "
   f"part and each named by the index, no rule text in the index, none "
   f"over {CHECK_MODULE_LIMIT // 1024} KB, and the startup rule "
   f"identical in both its homes")
