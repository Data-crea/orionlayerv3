#!/usr/bin/env python3
"""The smoke suite's own baseline — what "nothing was lost" is measured against.

    python tools/smoke_baseline.py capture <dir> [--runs 2]
    python tools/smoke_baseline.py compare <a.json> <b.json>

**Why this exists (work order 162, part 1).** `tools/smoke_test.py` is
being split into per-screen modules by script. The only evidence that a
move of that size lost nothing is the suite's own output: the ORDERED
list of every `ok(...)` sentence, the check count, and which checks the
fast tier does not run. Capture it before the cut, capture it after, and
compare. A count alone cannot do this — two checks could swap places, or
one could be silently replaced by another, and the number would not
move.

**Why the list is normalised.** A sentence that carries a measured value
or a wall-clock number differs between two runs of the same tree, and a
differing baseline proves nothing about the cut. `RULES` below is the
whole normalisation, and **every rule names the message that needed
it** — a rule without a message behind it is a blind spot the size of
its own pattern, so none is added defensively.

**As of 22 September 2026 that table is empty, and it was measured
rather than assumed:** two full runs of the unchanged tree produced
byte-identical `ok(...)` lists, 247 sentences each. The suite renders
into surfaces and reads pixels back, but it prints verdicts and
transcribed constants, not measurements of the clock. The table stays,
with this note, because the next expensive value to reach a sentence
will need it and the place for it should already exist.

**What a capture is NOT.** It is not a check and it does not replace
one; it is a record of one tree at one moment. The suite decides whether
the tree is good. This decides whether two trees agree about what the
suite did.
"""
import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUITE = os.path.join("tools", "smoke_test.py")

#: The prefix `ok()` prints. One place, because both the parser here and
#: any future reader of a captured log depend on it.
OK_PREFIX = "  ok  "

#: `(pattern, placeholder, the message that needed it)`.
#:
#: NOTHING IS ADDED HERE WITHOUT A MESSAGE. See the module docstring:
#: a normalisation rule erases whatever its pattern matches, so a rule
#: written "just in case" is a place where a real difference can hide.
#: Two full runs on 22 September 2026 were byte-identical, so nothing
#: here is about the clock; the one entry is about the tree.
RULES = [
    (r"(both extents required at )\d+( source files)", r"\1<n>\2",
     "max_map_scale transcribes Maximum_Galaxy_Display_Scale_ (…both "
     "extents required at N source files). It walks every .py in the "
     "tree to prove no call site passes MAP_MAX_X alone, and work "
     "order 162 turned the suite's ONE file into ninety, so N went "
     "216 -> 306. What the check asserts did not move and neither did "
     "its code; the size of the tree it walked did."),
]


def normalise(msg):
    """One `ok(...)` sentence, with every run-varying part replaced."""
    for pattern, placeholder, _why in RULES:
        msg = re.sub(pattern, placeholder, msg)
    return msg


def run(tier, root=ROOT):
    """Run the suite once. Returns (rc, seconds, stdout+stderr text).

    Through a subprocess and never by importing `main()`: the suite
    sets SDL variables at import, counts in module globals, and can
    exit 139 — none of which a second run in the same interpreter
    would survive. It is also how the gates run it, so this measures
    what the gates measure.
    """
    argv = [sys.executable, SUITE] + (["--fast"] if tier == "fast" else [])
    start = time.monotonic()
    proc = subprocess.run(argv, cwd=root, capture_output=True, text=True)
    return proc.returncode, time.monotonic() - start, proc.stdout + proc.stderr


def collect(text):
    """{ok, passed, tier, count} out of one run's output."""
    lines = text.splitlines()
    msgs = [l[len(OK_PREFIX):] for l in lines if l.startswith(OK_PREFIX)]
    passed = next((l for l in reversed(lines)
                   if l.startswith("SMOKE TEST PASSED")), "")
    return {"ok": [normalise(m) for m in msgs],
            "ok_raw": msgs,
            "passed": passed,
            "tier": "fast" if "(FAST TIER)" in passed else "full",
            "count": len(msgs)}


def skipped_between(full, fast):
    """The fast tier's skipped set, as sentences, in the full run's order.

    Computed as the full list MINUS the fast list rather than read out
    of `SLOW_TIER`'s names, because the names are the suite's own
    bookkeeping and the sentences are what a lost check would change.
    Walks both in order, so a check that merely MOVED shows up here
    instead of hiding behind an equal count.
    """
    out, i = [], 0
    for msg in full:
        if i < len(fast) and fast[i] == msg:
            i += 1
        else:
            out.append(msg)
    assert i == len(fast), (
        f"the fast tier printed a sentence the full tier did not, at "
        f"{fast[i]!r} — the fast run is not a subsequence of the full "
        f"one, which is the whole premise of the two tiers")
    return out


def capture(out_dir, runs=2, root=ROOT):
    """Run both tiers `runs` times, write the evidence, return the baseline."""
    os.makedirs(out_dir, exist_ok=True)
    record = {"tree": root, "runs": runs, "tiers": {}}
    for tier in ("full", "fast"):
        collected, times = [], []
        for n in range(1, runs + 1):
            rc, secs, text = run(tier, root)
            path = os.path.join(out_dir, f"{tier}_{n}.out")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
            assert rc == 0, (
                f"{tier} run {n} exited {rc} — a baseline is taken off a "
                f"GREEN suite or it is not a baseline. Output: {path}"
                + ("  (139 is a segfault, not a failure to retry)"
                   if rc == 139 else ""))
            got = collect(text)
            assert got["tier"] == tier, (
                f"{tier} run {n} printed the {got['tier']} tier's PASSED "
                f"line — the flag and the output disagree")
            collected.append(got)
            times.append(secs)
            print(f"  {tier} run {n}: {got['count']} checks, {secs:.2f} s")
        first = collected[0]
        for n, got in enumerate(collected[1:], 2):
            assert got["ok"] == first["ok"], (
                f"the {tier} tier is not stable: run 1 and run {n} "
                f"disagree at "
                f"{_first_difference(first['ok'], got['ok'])}. Fix the "
                f"normalisation in RULES, not the suite")
        record["tiers"][tier] = {
            "ok": first["ok"], "count": first["count"],
            "passed": first["passed"],
            "seconds": [round(t, 2) for t in times]}
    record["skipped"] = skipped_between(record["tiers"]["full"]["ok"],
                                        record["tiers"]["fast"]["ok"])
    path = os.path.join(out_dir, "baseline.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print(f"  baseline: {path}")
    return record


def _first_difference(a, b):
    """Where two sentence lists part company, for a message a human reads."""
    for n, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return f"check {n + 1}:\n    A: {x}\n    B: {y}"
    return f"length {len(a)} against {len(b)}"


def compare(path_a, path_b):
    """0 if two baselines agree on every sentence, the count and the skips.

    **Both sides go through today's `RULES` again.** A capture stores
    the sentences it saw; a rule added afterwards therefore applies to
    an old capture as well, which is what makes the table a rule table
    rather than a property of whichever run was taken first. It is
    also idempotent — a sentence already normalised does not change.
    """
    a = json.load(open(path_a, encoding="utf-8"))
    b = json.load(open(path_b, encoding="utf-8"))
    for side in (a, b):
        for tier in side["tiers"].values():
            tier["ok"] = [normalise(m) for m in tier["ok"]]
        side["skipped"] = skipped_between(side["tiers"]["full"]["ok"],
                                          side["tiers"]["fast"]["ok"])
    bad = []
    for tier in ("full", "fast"):
        ta, tb = a["tiers"][tier], b["tiers"][tier]
        if ta["ok"] != tb["ok"]:
            bad.append(f"{tier}: {_first_difference(ta['ok'], tb['ok'])}")
        elif ta["count"] != tb["count"]:
            bad.append(f"{tier}: {ta['count']} checks against {tb['count']}")
    if a["skipped"] != b["skipped"]:
        bad.append("the fast tier's skipped set differs:\n    "
                   + _first_difference(a["skipped"], b["skipped"]))
    for line in bad:
        print(f"  DIFFERS  {line}")
    if not bad:
        print(f"  identical: {a['tiers']['full']['count']} checks, "
              f"{a['tiers']['fast']['count']} in the fast tier, "
              f"{len(a['skipped'])} push-only, every sentence equal")
    return 1 if bad else 0


def main(argv):
    if len(argv) >= 2 and argv[0] == "capture":
        runs = 2
        if "--runs" in argv:
            runs = int(argv[argv.index("--runs") + 1])
        capture(argv[1], runs)
        return 0
    if len(argv) == 3 and argv[0] == "compare":
        return compare(argv[1], argv[2])
    print(__doc__.strip().splitlines()[0])
    print("\n  python tools/smoke_baseline.py capture <dir> [--runs 2]"
          "\n  python tools/smoke_baseline.py compare <a.json> <b.json>")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
