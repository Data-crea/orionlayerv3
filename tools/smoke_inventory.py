#!/usr/bin/env python3
"""What is inside the smoke suite, read by `ast` and never by eye.

    python tools/smoke_inventory.py                 # the table
    python tools/smoke_inventory.py --json <path>   # the same, for a script
    python tools/smoke_inventory.py --time <path>   # measure, then merge
    python tools/smoke_inventory.py --screen <name> # what that screen runs

**Why this exists (work order 162, part 2).** `tools/smoke_test.py` was
22 221 lines and 1.2 MB, almost all of it inside one `main()` — several
times any context window, and fifteen times work order 127's 80 KB
reading budget. The order that split it forbids reading it as a whole,
for a reason this project has paid for in other shapes: **moving code
by reading blocks into context and writing them out again is how a
check disappears silently.** So the inventory is computed, the TABLE is
what a session reads, and the cut was produced from the table by a
script.

**It did not retire with the cut, and that is deliberate.** The
`--screen` selector asks this file, at run time, which sections a
screen's checks depend on. A baked dependency list would be the second
copy this project keeps paying for; computing it costs about a second
and cannot go stale.

**What a section is, and why the boundary is `ok()`.** The suite draws
no other one, and 157 said so when it measured the same way: the checks
are blocks laid end to end and the only boundary the source carries is
the `ok(...)` that closes each one. A section is a maximal run of
consecutive TOP-LEVEL statements ending with the statement that
contains an `ok(...)` — so a loop that calls `ok()` per iteration is one
section with several checks, and the shared setup in front of a check
belongs to that check's section.
"""
import ast
import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smoke_names as names                                     # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUITE = os.path.join(ROOT, "tools", "smoke_test.py")
SUITE_DIR = os.path.join(ROOT, "tools", "smoke_suite")

#: A check that sweeps the tree polices files that do not exist yet, so
#: it belongs to the core and runs for every screen — work order 162,
#: and 157 section 5(a) for why: a selection keyed on what is there
#: cannot select the check whose whole job is to notice something new.
SWEEP = re.compile(r"os\.walk\(|glob\.glob\(|glob\.iglob\(")

#: File stems every screen has, so they name none of them.
COMMON = frozenset((
    "screen", "layout", "boxes", "help", "assets", "colors", "gamedata",
    "__init__", "reference", "frame", "icons"))


def suite_files():
    """The suite's own sources, in run order: the entry point, then the modules."""
    if not os.path.isdir(SUITE_DIR):
        return [SUITE]
    return [os.path.join(SUITE_DIR, n)
            for n in sorted(os.listdir(SUITE_DIR)) if n.endswith(".py")]


def _body(tree):
    """The statements to cut: `main()`'s body before the cut, the module's after."""
    main = next((n for n in tree.body if isinstance(n, ast.FunctionDef)
                 and n.name == "main"), None)
    return main.body if main is not None else tree.body


def _calls(node, name):
    return [n for n in ast.walk(node) if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name) and n.func.id == name]


def _messages(group):
    """The literal head of each `ok(...)` in a section, for a human reader."""
    out = []
    for stmt in group:
        for call in _calls(stmt, "ok"):
            arg = call.args[0] if call.args else None
            text = ""
            if isinstance(arg, ast.Constant):
                text = str(arg.value)
            elif isinstance(arg, ast.JoinedStr):
                text = "".join(v.value for v in arg.values
                               if isinstance(v, ast.Constant))
            out.append(re.sub(r"\s+", " ", text).strip()[:110])
    return out


def sections(path, glob=None):
    """Every section of one file, with its name flow."""
    src = open(path, encoding="utf-8").read()
    lines = src.splitlines()
    tree = ast.parse(src)
    glob = names.module_names(tree) if glob is None else glob
    groups, cur = [], []
    for stmt in _body(tree):
        cur.append(stmt)
        if _calls(stmt, "ok"):
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)                      # a tail with no check in it
    out = []
    for group in groups:
        start, end = group[0].lineno, group[-1].end_lineno
        reads, binds, mutates = names.free_of(group, glob)
        text = "\n".join(lines[start - 1:end])
        slow = [c.args[0].value for stmt in group for c in _calls(stmt, "slow")
                if c.args and isinstance(c.args[0], ast.Constant)]
        brought = {(a.asname or a.name).split(".")[0]
                   for stmt in group for n in ast.walk(stmt)
                   if isinstance(n, (ast.Import, ast.ImportFrom))
                   for a in n.names}
        out.append({
            "file": os.path.relpath(path, ROOT).replace(os.sep, "/"),
            "start": start, "end": end, "lines": end - start + 1,
            "bytes": len(text) + 1,
            "checks": sum(len(_calls(s, "ok")) for s in group),
            "slow": slow[0] if slow else None,
            "sweep": bool(SWEEP.search(text)),
            "reads": reads, "binds": binds, "mutates": mutates,
            "imports": sorted(brought),
            "msgs": _messages(group), "text": text,
        })
    return out


def screen_tokens(root=ROOT):
    """`{screen: the words that name it}` — from the tree, never typed.

    The folder name alone is a poor net: a check that imports
    `colonyicons` and asserts on it never spells `colony_summary`, so a
    heuristic counting folder names files it under "no screen". Every
    screen therefore contributes its own file basenames as well, which
    is a list nobody maintains and that grows with the screen.

    **Two subtractions, both computed.** A stem that `core/` or
    `tools/` also carries names a shared idea, not a screen —
    `palette` is `core/palette.py` and it made the suite's very first
    block look like a Fleets check. And a stem two screens share
    identifies neither. Both are removed before anything is counted,
    so the net keeps only what is actually distinctive.
    """
    base = os.path.join(root, "screens")
    shared = set()
    for top in ("core", "tools", os.path.join("assets", "shared")):
        for dirpath, dirnames, files in os.walk(os.path.join(root, top)):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            shared.update(os.path.splitext(fn)[0] for fn in files)
    out = {}
    for name in sorted(os.listdir(base)):
        here = os.path.join(base, name)
        if not os.path.isdir(here) or name.startswith("_"):
            continue
        tokens = {name} | {w for w in name.split("_")
                           if len(w) > 3 and w not in COMMON}
        for dirpath, dirnames, files in os.walk(here):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for fn in files:
                stem = os.path.splitext(fn)[0]
                if len(stem) > 5 and stem not in COMMON:
                    tokens.add(stem)
        out[name] = tokens - (shared - {name})
    seen = collections.Counter(t for group in out.values() for t in group)
    return {s: {t for t in group if seen[t] == 1} for s, group in out.items()}


def attribute(row, tokens):
    """Give one section an area, and say how it was decided.

    A section belongs to the screen its own text names most often, and
    only when that screen is a CLEAR winner. **A tree sweep, a tie and
    a section that names no screen all go to the core**, which always
    runs — work order 162's rule, and the safe direction: a check in
    the core runs for every screen, a check in the wrong screen's group
    runs for none of the right ones.
    """
    words = collections.Counter(
        re.findall(r"[a-z_][a-z_0-9]*", row["text"].lower()))
    hits = {}
    for screen, group in tokens.items():
        got = {n: words[n.lower()] for n in group if words[n.lower()]}
        if got:
            hits[screen] = (sum(got.values()), ",".join(
                f"{n}x{c}" for n, c in
                sorted(got.items(), key=lambda kv: -kv[1])[:3]))
    best = sorted(hits.items(), key=lambda kv: (-kv[1][0], kv[0]))
    runner = best[1][1][0] if len(best) > 1 else 0
    if row["sweep"]:
        return "core", "sweeps the tree"
    if not best:
        return "core", "names no screen"
    # A CLEAR WINNER, OR THE CORE. Ties go to the core — work order
    # 162's own rule — and a margin on top of that was measured and
    # dropped: demanding three hits and twice the runner-up moved 53
    # more sections into the core, and since every `--screen` run
    # carries the core, it made every narrowed run bigger (13.3 s to
    # 17.8 s in the fast tier) to file a handful of blocks more
    # cautiously.
    if best[0][1][0] <= runner:
        return "core", "ambiguous: " + " / ".join(
            f"{n}={v[0]}" for n, v in best[:3])
    return best[0][0], best[0][1][1] + (
        f" over {best[1][0]}={runner}" if len(best) > 1 else "")


def build(times=None, areas=None):
    """Every section of the whole suite, in run order, attributed and timed.

    `areas` maps a suite file to the group it belongs to. After the cut
    that comes from the file NAME and no heuristic runs at all; before
    it, every section is attributed by `attribute`.
    """
    tokens = screen_tokens()
    rows = []
    for path in suite_files():
        for row in sections(path):
            row["i"] = len(rows)
            if areas and row["file"] in areas:
                row["area"], row["how"] = areas[row["file"]], "its module"
            else:
                row["area"], row["how"] = attribute(row, tokens)
            rows.append(row)
    if times and os.path.exists(times):
        marks = json.load(open(times, encoding="utf-8"))
        for row in rows:
            here = [m for m in marks
                    if m[3] == row["file"] and row["start"] <= m[2] <= row["end"]]
            row["seconds"] = round(sum(m[1] for m in here), 3)
            row["ran"] = len(here)
        placed = sum(r["ran"] for r in rows)
        assert placed == len(marks), (
            f"{len(marks) - placed} measured checks fell outside every "
            f"section — the table and the run disagree")
    return rows


def depends(rows):
    """`i -> the earlier sections i needs`, and the reason for each.

    A section needs the last section that BOUND a name it reads before
    binding it, and every section that MUTATED that name since. Names
    an `import` statement binds anywhere in the suite are exempt: an
    import is reproducible, so a narrowed run re-runs it rather than
    dragging a section in for it.
    """
    imported = set()
    for row in rows:
        imported.update(row["imports"])
    out = [dict() for _ in rows]
    binder, mutated = {}, collections.defaultdict(list)
    for row in rows:
        i = row["i"]
        for name in row["reads"]:
            if name in imported:
                continue
            if name in binder:
                out[i].setdefault(binder[name], name)
            for m in mutated.get(name, []):
                if m > binder.get(name, -1):
                    out[i].setdefault(m, name + " (mutated)")
        for name in row["binds"]:
            binder[name] = i
            mutated[name] = []
        for name in row["mutates"]:
            mutated[name].append(i)
    return out


def select(rows, screen):
    """The sections a `--screen` run executes: core, the screen, their needs.

    **It can only widen.** Every core section is in, every section of
    the named screen is in, and then the transitive closure of what
    those read. A closure that is too large costs time; one that is too
    small would run a check against state the run never built, which is
    why the mutation edges are in it.
    """
    need = {r["i"] for r in rows if r["area"] in ("core", screen)}
    prod = depends(rows)
    stack = list(need)
    while stack:
        for p in prod[stack.pop()]:
            if p not in need:
                need.add(p)
                stack.append(p)
    return need


def table(rows):
    """One line per section — the whole point of the tool."""
    out = ["  i  lines      L  ckB ch slow             area            "
           "in out mut  first sentence",
           "  " + "-" * 114]
    prod = depends(rows)
    used = collections.Counter(p for d in prod for p in d)
    for r in rows:
        out.append(
            f"{r['i']:>3} {r['start']:>6}-{r['end']:<6} {r['lines']:>4} "
            f"{r['bytes'] / 1024:>4.0f} {r['checks']:>2} "
            f"{(r['slow'] or ''):<16} {r['area'][:15]:<15} "
            f"{len(prod[r['i']]):>3} {used[r['i']]:>3} "
            f"{len(r['mutates']):>3}  {(r['msgs'] or [''])[0][:56]}")
    return "\n".join(out)


def measure(path):
    """157's method: wrap `ok()` and time the segment between two calls.

    **The mark carries the caller's FILE AND LINE, not just its
    sentence.** Call sites outnumber the checks a run produces — some
    sit in branches a run does not take, some are loops — so matching a
    measured run to the table by counting would slide everything after
    the first branch. The position is the join and it cannot slide.
    """
    sys.path.insert(0, ROOT)
    import time
    import tools.smoke_test as st                                # noqa: E402
    marks = []
    real, last = st.ok, [time.monotonic()]

    def timed(msg):
        now = time.monotonic()
        frame = sys._getframe(1)
        marks.append([msg, round(now - last[0], 4), frame.f_lineno,
                      os.path.relpath(frame.f_code.co_filename,
                                      ROOT).replace(os.sep, "/")])
        last[0] = now
        return real(msg)

    st.ok = timed
    rc = st.main()
    assert rc == 0, f"the suite exited {rc}; a timing run needs a green one"
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(marks, fh, indent=1, ensure_ascii=False)
    return 0


def main(argv):
    if argv and argv[0] == "--time":
        return measure(argv[1])
    times = argv[argv.index("--times") + 1] if "--times" in argv else None
    rows = build(times)
    if "--screen" in argv:
        want = argv[argv.index("--screen") + 1]
        need = select(rows, want)
        print(f"{want}: {len(need)} of {len(rows)} sections, "
              f"{sum(rows[i]['bytes'] for i in need) / 1024:.0f} KB, "
              f"{sum(r['checks'] for r in rows if r['i'] in need)} checks")
        return 0
    if "--json" in argv:
        path = argv[argv.index("--json") + 1]
        for row in rows:
            row.pop("text", None)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(rows, fh, indent=1, ensure_ascii=False)
        print(f"{len(rows)} sections -> {path}")
        return 0
    print(table(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
