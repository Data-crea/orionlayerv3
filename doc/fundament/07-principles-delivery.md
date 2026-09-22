# The fundament, part 7 of 9 — Delivery

Who owns a detail and who owns a direction, and how a package travels without losing anything.

**Decisions in this part:** no decisions.

The index is [`../v3_fundament.md`](../v3_fundament.md), and it is
what to read first. This file is one part of the fundament and
carries no rule that is not in it; the text below is what stood in
`doc/v3_fundament.md` before work order 164 moved it, unchanged.

<!-- fundament-body -->
### Delivery

**Who owns a detail, and who owns a direction.** Agreed 4 September
2026, after three claims written in chat reached packages and did not
survive a check: a sprite group read as one number, two conditions
treated as one gate, and a field value assumed to reach 200 where its
source caps it at 20.

The session at the tree has the source, the repository and a running
game, and therefore owns every DETAIL — line numbers, offsets, values,
branch tables, worked examples, live data. A number in a package is a
starting point. Verify it before building on it and correct it in the
same commit.

The chat side owns DIRECTION and ACCEPTANCE: what to build, where it
lives — file, function, box — and how it will be judged. It names
WHERE, not WHAT is there.

**The evidence, because it is unambiguous.** Of the seven packages
delivered that day, six asserted a detail and every one of the six was
wrong somewhere: a namespace, `colsum.cpp:209` for `:210`, four line
numbers in `coldraw.cpp` at once, a line count computed from
overlapping buckets, a reason two branches were unreachable, and an
example needing an import value the field cannot hold. The seventh
asserted nothing — it said "read the source, I have not" — and needed
no correction at all.

**And it is not "the chat side is unreliable", which is the reading
that would make this useless.** In those same sessions the tree side
published a wrong cast boundary and a first `map_rect` that broke a
rule already in `mapcoords`, both for the identical reason: a numeric
claim written in prose before the arithmetic was run. The rule is
about the ORDER, not the author. Run it, then write it, whoever is
writing.

**Package length follows the work.** Evidence, markings, and choices
that are expensive to reverse — names, module seams, deviations,
anything entering this file — arrive long and specific, because the
precision is the deliverable. Drawing work arrives short: what, where,
and "render it beside a native screenshot of the same save". If it
does not match, say what differs rather than adjusting until it does.

**A screenshot comparison from chat is a QUESTION, not a finding.**
"The BC row looks like two groups — verify" is the shape, and it was
the right shape: it was two groups. Treat it as a lead.

**When something does not work, report it and stop.** It gets fixed
against the result, not talked out beforehand.

**This entry is KNOWINGLY duplicated**, in the memory a chat session
loads, because that session has no tree to read a pointer into — the
one case where this project's "exactly one home, everything else a
pointer" rule cannot be applied. That makes it the exact shape of the
oldest recurring fault here, so: the two move together or the
agreement is void, and each copy says the other exists. If you are
reading this and cannot confirm the other copy matches, that is the
thing to fix first.

**Verify against a pristine tree, not the working one.** Unpack the
last known upload fresh, apply only the new package, run the smoke
test. Testing in a tree that already has everything proves nothing.

**One package per screen, even if files ship twice.** Split deliveries
create hidden dependencies: package B's `screen.py` called a function
that only existed in package A, and the failure surfaced in the
sidebar, nowhere near the cause.

**Ship cumulatively while a package is unconfirmed.** If the previous
delivery has not been installed yet, the next one carries it too. Two
packages that each assume the other landed is the same hidden
dependency as a split delivery, one session removed.

**Count the unpacked files before copying.** Three rounds were lost to
a package that was never copied at all; the symptom looked like a
rendering bug. Use `cp -r` without `--delete` for partial packages.

**The same bug twice, because the fix was applied to the instance.**
`help_extract.py` defaulted its output to a relative path and wrote
the help texts wherever the shell happened to be. That was found,
understood, anchored to the project, and written up as "a tool that
writes where the loader does not look is the same class of fault as a
config key that never gets saved". `nebula_extract.py` had the
identical default the whole time and nobody looked. A week later it
put 61 sprite files in the repository root, git staged them for the
first commit, and the smoke test went on reporting the references as
absent — because they were. Both failures printed a success line with
a relative path in it, which is what hid them.

The rule is now a check: every tool that writes into the tree has its
default output anchored to the project, asserted by importing the
constant and testing the path, not by grepping the source. When you
fix a fault, the next question is which sibling has it too — the
write-up of the lesson is not the fix.

**A pin records a verification; it does not create one.**
`requirements.txt` shipped with exact versions and a paragraph
explaining why rounding differences in pygame and Pillow could show
up as a two-pixel drift. The reasoning was sound and the numbers were
whatever happened to be installed where the file was written. The
first machine to actually run the clone had different ones — Python
3.14 against 3.12, SDL 2.32 against 2.28 — and all 47 checks were
green, which is evidence the tolerance is wider than the pins
claimed. They are floors now, with both verified combinations listed
by name. The same instinct that says "measure it, do not assume it"
applies to a version number: if nobody has run the pinned
combination, the pin is a guess wearing a decimal point.

**A check with a scope has a blind spot exactly the size of that
scope.** The hygiene check that refuses archives in the tree was
written after a `stars.zip` was found, so it walked `screens/` —
where the fault had been. It then found a second pair on its first
run and looked thoroughly validated. A `9-slice.zip` sat in
`assets/shared/skins/` the whole time, holding a `9slice.json` ten
days older than the one beside it, and survived two passes. The
check now walks the whole tree. When a check is written in response
to one instance, its scope is drawn around that instance by
accident, and passing does not mean the tree is clean — it means
nothing was found where you looked.

**Version control is not a nice-to-have; it was the missing tool
under four separate lessons.** The mis-copy, the eighteen ambiguous
ZIPs, the manifest pair written to survive them, the rule about
package folder names, the two documents that drifted apart, the same
decision number taken twice by two same-day sessions — every one of
those is a symptom of having no history to diff against. They were
each solved with a handmade instrument, and the instruments worked.
They were still all replacements for `git status`, `git diff` and
`git log`, and each one had to be maintained. Keep the lessons: they
are about verifying a copy, and they are why the repository exists.
Do not keep rebuilding the tools.

**A check that measures the wrong object is not a check.** The count
above fired exactly as designed — 496 instead of 12 — and was
useless, because the package's root folder was named `orionlayerv3/`
and a folder of that name from an earlier session was already sitting
in `~/Downloads`. The count measured that one. The `cp` that followed
copied an old tree over the project. So: **the folder inside a
package must never carry the project's own name**, and the count has
to be taken on the path that was just unpacked, not on a name that
could already exist.

**Measure what survives, not what was asked for** — 4 September 2026,
a rendering check, and the same class one layer down. A tree-wide
check for text drawn under the cockpit frame recorded where each
glyph was *blitted*. It reported three star names under the frame on
the galaxy map, one of them 330 px outside the map area. All three
were fiction: `_render_map` wraps its whole render in
`set_clip(map_area)`, exactly as the original wraps
`Print_Star_Names_` in `Set_Window_`/`Clip_On_` (mainscr.cpp:519), so
those glyphs never reached the screen. Honouring the clip at blit
time took the same screen from 4862 reported pixels to 98 real ones.
A drawing call is a request; the surface decides what happens to it.

**And the force of a check is a property of the state it runs in.**
The same check, run against a screen nobody had given a snapshot to,
recorded 22 text surfaces. With a snapshot it records 65 — the list,
the scan box and the galaxy inset are all empty until then, and every
one of them was reported clean without ever being drawn. On the
galaxy map it is sharper still: that save has 99 stars at scale 36,
and `Print_Star_Names_` bails out entirely above 72 stars at that
zoom, so **the check saw no star name at all** and said so as a pass.
A green run in a null state is not evidence, and a check that can
reach a null state should say how much it saw — the count of things
examined belongs in the assertion, not just the verdict.

**Identify an archive by its content, not its name.** Eighteen ZIPs in
one download folder, three of them `orionlayerv3*.zip`, and the actual
working state was in none of them — the download had been renamed
after the folder inside it. One grep for a file only the new package
contains settles it in a line:

```bash
for f in *.zip; do unzip -l "$f" | grep -q verify_tree.py && echo "$f"; done
```

**A smoke test says THAT something broke; a manifest says WHAT.** The
mis-copy stopped the smoke test at its first failing assertion, which
named one screen and nothing else. `cp -r` deletes nothing, so the
real damage was a mix: every file the old tree also had was rolled
back, everything else survived. A sha256 per file found all of it,
including eleven images and three portraits that no test looks at —
`klackon.png` had come back and `select_race` resolves `.png` before
`.jpg` and `.webp`, so three races were quietly showing old artwork
while every check stayed green.

`tools/make_manifest.py` writes the list when a state is known good;
`tools/verify_tree.py` measures a later tree against it. The manifest
is a delivery artifact, not a lock on the tree — it goes stale on the
next edit, and that is fine. The smoke test therefore checks the two
tools against a throwaway tree rather than checking this tree against
a shipped manifest, because a test that fails on every legitimate
change is ignored within a day.

**Never chain a verifier behind `&&`.** It exits non-zero when it
finds something, which is the whole point, and the rest of the line
then silently does not run.

**Check that the file you copied is the file you built.**

**Verify asset identity; do not assume upload order.**

