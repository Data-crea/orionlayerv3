#!/usr/bin/env python3
"""Check core/structs specs against orion2re's own headers.

Decision 23 names two routes to a verified offset. This is the FIRST:
compile orion2re's headers with their own `#pragma pack(1)` and let the
compiler assert every offset, plus the struct's size against the assert
in `sizes.h`. It was done by hand twice — for `s_settings` on 14
September 2026 and for `s_player.tech_fields` on 17 September — and a
check done by hand is a check that is done once. This makes it
mechanical, so the day Joes moves a member the suite says so instead of
OrionLayer reading a plausible wrong number.

**It is exactly half of decision 23 and says so.** `offsetof` and a
satisfied size assert fix where a member begins and how wide it is.
They say nothing about the meaning of bits inside one, and nothing about
whether the value on the wire is the value the screen shows. The second
source — a live read that agrees with the game's own picture — is not
here and cannot be: this runs headless.

WHAT IT DOES

    For each covered spec it writes a throwaway translation unit
    OUTSIDE orion2re's tree — one `static_assert(offsetof(S, m) == n)`
    per field, one `static_assert(sizeof(S) == size)` — and compiles it
    with -fsyntax-only. A disagreement is a compile error naming the
    field.

    The size is cross-read from `src/game/sizes.h` as well, so the
    number in the Python spec and the number the engine asserts for
    itself are compared directly and not only through `sizeof`.

    And it proves it can fail: one spec is compiled a second time with
    a single offset deliberately moved by one byte, and that compile
    MUST fail. A check that cannot fail has been passing for a reason
    nobody has looked at (the same control the s_settings verification
    ran by hand).

Usage (from the project root):
    python tools/struct_header_check.py
    python tools/struct_header_check.py ~/some/other/orion2re

Exit codes: 0 all agree, 1 a disagreement or a compile that could not
be run for any other reason, 2 no orion2re tree and/or no C++ compiler
on this disk — which is not the same answer as a wrong offset.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from version_check import find_tree  # noqa: E402  (one home for the tree list)

#: The headers a unit needs before `orion2.h` will parse, in order.
#: Taken from the hand-run of 17 September 2026 (work order 129 C).
HEADERS = ("compat.h", "types.h", "settler.h", "consts.h",
           "orion2_consts.h", "orion2.h")

#: Spec modules this route covers: every field name in the Python spec
#: is also the C++ member's name, so the assert can be generated.
COVERED = ("player", "settings", "colony", "planet", "star", "nebula",
           "ship_icon", "leader")

#: And the one it does NOT cover, named rather than silently skipped
#: (decision 61 — an omission is marked). `core/structs/ship.py` uses
#: OrionLayer's own names for `s_ship_data`'s members: `name`, `size`,
#: `ship_type`, `cost` and ten more have no member of that name in the
#: header. Covering it needs a Python-name -> C++-name map, and such a
#: map is a transcription that would itself need verifying — which is
#: the work, not a detail of it. Its offsets rest on their live
#: corroboration alone until somebody does that.
NOT_COVERED = {
    "ship": "core/structs/ship.py names s_ship_data's members itself; "
            "the header route needs a rename map nobody has verified",
}

#: The negative control: this spec, this field, moved one byte.
CONTROL_SPEC = "player"
CONTROL_FIELD = "race"


def spec_of(module_name):
    """The SPEC object of core.structs.<module_name>, or None."""
    mod = __import__("core.structs." + module_name, fromlist=["SPEC"])
    return getattr(mod, "SPEC", None)


def unit(spec, skew_field=None):
    """The translation unit that asserts `spec` against the headers.

    `skew_field` moves that one field's offset by one byte — the
    control, which must NOT compile.
    """
    lines = ["#include <cstddef>"]
    lines += [f'#include "{h}"' for h in HEADERS]
    for name, offset, _kind in spec.fields:
        if name == skew_field:
            offset += 1
        lines.append(
            f'static_assert(offsetof({spec.name}, {name}) == {offset},'
            f' "{spec.name}.{name}");')
    lines.append(
        f'static_assert(sizeof({spec.name}) == {spec.size},'
        f' "sizeof({spec.name})");')
    return "\n".join(lines) + "\n"


def compile_unit(compiler, tree, source):
    """Compile `source` for syntax only. Returns (ok, output)."""
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "spec_assert.cpp")
        with open(path, "w") as handle:
            handle.write(source)
        proc = subprocess.run(
            [compiler, "-std=c++20", "-fsyntax-only",
             "-I", os.path.join(tree, "src", "game"),
             "-I", os.path.join(tree, "src"), path],
            capture_output=True, text=True, timeout=300)
    return proc.returncode == 0, (proc.stdout + proc.stderr)


def engine_sizes(tree):
    """{struct name: asserted size} out of src/game/sizes.h."""
    path = os.path.join(tree, "src", "game", "sizes.h")
    if not os.path.isfile(path):
        return {}
    pattern = re.compile(
        r"ORION2RE_STATIC_SIZE_ASSERT\(\s*(\w+)\s*,\s*(0x[0-9a-fA-F]+|\d+)\s*\)")
    out = {}
    with open(path, errors="replace") as handle:
        for name, size in pattern.findall(handle.read()):
            out[name] = int(size, 0)
    return out


def main():
    tree = find_tree(sys.argv)
    compiler = (shutil.which("g++") or shutil.which("clang++")
                or shutil.which("c++"))
    if tree is None or compiler is None:
        print("no orion2re tree" if tree is None else f"tree {tree}")
        print("no C++ compiler" if compiler is None else f"compiler {compiler}")
        print("SKIPPED — the header route needs both")
        return 2

    print(f"orion2re {tree}")
    print(f"compiler {compiler}")
    sizes = engine_sizes(tree)
    bad = 0

    for name in COVERED:
        spec = spec_of(name)
        if spec is None:
            print(f"  {name:<10} no SPEC in the module")
            bad += 1
            continue
        # The size, straight out of the engine's own assert, before
        # anything is compiled: two numbers that must already agree.
        asserted = sizes.get(spec.name)
        if asserted is None:
            print(f"  {name:<10} {spec.name}: sizes.h asserts no size for it")
        elif asserted != spec.size:
            print(f"  {name:<10} {spec.name}: spec says {spec.size} "
                  f"(0x{spec.size:x}), sizes.h asserts {asserted} "
                  f"(0x{asserted:x})")
            bad += 1
            continue
        good, out = compile_unit(compiler, tree, unit(spec))
        if good:
            print(f"  {name:<10} {spec.name}: {len(spec.fields)} offsets "
                  f"and sizeof agree")
        else:
            print(f"  {name:<10} {spec.name}: DISAGREES")
            print("".join(f"      {line}\n" for line in
                          out.splitlines() if "static_assert" in line
                          or "error" in line)[:4000])
            bad += 1

    for name, why in sorted(NOT_COVERED.items()):
        print(f"  {name:<10} NOT COVERED — {why}")

    # The control. It compiles the same spec with one offset moved by a
    # byte and requires the compiler to refuse it.
    control = spec_of(CONTROL_SPEC)
    good, _out = compile_unit(compiler, tree,
                              unit(control, skew_field=CONTROL_FIELD))
    if good:
        print(f"  CONTROL FAILED: {control.name}.{CONTROL_FIELD} moved one "
              f"byte and the unit still compiled — this check proves "
              f"nothing")
        bad += 1
    else:
        print(f"  control    {control.name}.{CONTROL_FIELD} off by one is "
              f"refused, so a wrong offset would be")

    if bad:
        print(f"\n{bad} disagreement(s)")
        return 1
    print("\nOK — every covered spec matches orion2re's headers")
    return 0


if __name__ == "__main__":
    sys.exit(main())
