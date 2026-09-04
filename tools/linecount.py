"""Measure a Python file the way decision 6 means it: CODE lines.

    python tools/linecount.py            # the over-guideline list
    python tools/linecount.py <file>...  # one line per file

**Why this exists.** The ~300-line guideline was read off `wc -l` for
as long as it existed, and `wc -l` counts prose. This project writes
long docstrings on purpose — every value carries the reason it is
that value — so the proxy "a long file does a lot" was broken by the
project's own documentation habit, quietly and in one direction.
Measured properly, 17 of the 24 files over 300 TOTAL lines are under
300 lines of code, and the ranking inverts: on 4 September 2026
`custom_race/screen.py` was 558 total against `colony_summary/
screen.py`'s 666, and 392 code against 218 — so a reader working the
list from the top would have split the wrong file first, and did.

**Every line lands in exactly one bucket**, in this order, so nothing
is counted twice: a blank line inside a docstring is docstring, not
blank, and a `#` line inside one is docstring too.

    docstring   module, class and function docstrings, whole span
    blank       nothing but whitespace
    comment     a whole line whose first non-space character is `#`
    code        everything else — including a trailing `# ...` on a
                statement, which is on a code line

**Docstrings come from `ast`, never from a regex.** A triple-quoted
string that is not in docstring position is a value and is CODE: a
regex that pairs quotes cannot tell the two apart, and would count a
long embedded template as documentation.

Both this and `v3_projektstatus.md`'s exceptions list must agree; the
smoke test asserts it, so the numbers in that document are computed
and merely transcribed, never typed. That is the same trade the check
count makes, and the reason is the same one: the copy without a
checker is the copy that goes stale.
"""
import ast
import os
import sys

#: decision 6. Applied to CODE lines, which is the amendment of
#: 4 September 2026 — see the fundament and `doc/v3_fundament.md`
#: under "a proxy holds until something moves the proxy".
GUIDELINE = 300

#: Where the guideline applies. "" is the repository root itself,
#: which is not walked recursively and is there for `main.py` — the
#: first version of this scan omitted it, and the entry duly went
#: missing from a list whose whole job is to be uncomfortable.
#: `tools/smoke_test.py` is exempt by nature and is named here rather
#: than filtered out silently.
ROOTS = ("", "core", "screens", "tools")
EXEMPT = (os.path.join("tools", "smoke_test.py"),)


def measure(path):
    """(total, code, docstring, comment, blank) for one file."""
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    lines = text.splitlines()
    total = len(lines)
    doc = set()
    for node in ast.walk(ast.parse(text)):
        if not isinstance(node, (ast.Module, ast.ClassDef,
                                 ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body = getattr(node, "body", None)
        if not body:
            continue
        first = body[0]
        if (isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)):
            doc.update(range(first.lineno, first.end_lineno + 1))
    blank = comment = 0
    for n, line in enumerate(lines, 1):
        if n in doc:
            continue
        stripped = line.strip()
        if not stripped:
            blank += 1
        elif stripped.startswith("#"):
            comment += 1
    docstring = len(doc)
    return (total, total - docstring - blank - comment, docstring,
            comment, blank)


def walk(root=None):
    """Every .py file under ROOTS, as (relative path, measurement)."""
    root = root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = []
    for top in ROOTS:
        base = os.path.join(root, top) if top else root
        walked = ([(base, [], sorted(os.listdir(base)))] if not top
                  else os.walk(base))
        for here, _dirs, files in walked:
            if "__pycache__" in here:
                continue
            for name in sorted(files):
                if not name.endswith(".py"):
                    continue
                full = os.path.join(here, name)
                if not os.path.isfile(full):
                    continue
                rel = os.path.relpath(full, root).replace(os.sep, "/")
                out.append((rel, measure(full)))
    return out


def over_guideline(root=None, limit=GUIDELINE):
    """Files over `limit` CODE lines, worst first — THE list.

    Ranked by code, because that is what the guideline is about. A
    file over 300 total on documentation alone is not an exception
    and does not belong here; see decision 6.
    """
    rows = [(rel, m) for rel, m in walk(root)
            if m[1] > limit and rel not in
            {e.replace(os.sep, "/") for e in EXEMPT}]
    return sorted(rows, key=lambda r: -r[1][1])


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    head = f"{'file':<44}{'code':>6}{'total':>7}{'doc':>6}{'cmt':>6}{'blank':>7}"
    if args:
        print(head)
        for path in args:
            t, c, d, m, b = measure(path)
            print(f"{path:<44}{c:>6}{t:>7}{d:>6}{m:>6}{b:>7}")
        return 0
    rows = walk()
    over_total = [r for r in rows if r[1][0] > GUIDELINE]
    over_code = over_guideline()
    print(head)
    for rel, (t, c, d, m, b) in over_code:
        print(f"{rel:<44}{c:>6}{t:>7}{d:>6}{m:>6}{b:>7}")
    print(f"\n{len(over_total)} files over {GUIDELINE} TOTAL lines, "
          f"{len(over_code)} over {GUIDELINE} CODE lines — "
          f"{len(over_total) - len(over_code)} of them are over on "
          f"documentation alone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
