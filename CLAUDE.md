# OrionLayer v3 — working agreement

An HD frontend for **Master of Orion 2**, built on **orion2re** (an
open-source C++ reimplementation of the original engine, maintained
by a collaborator, Joes). orion2re runs the game; OrionLayer replaces
its 640x480 interface with high-resolution pygame screens. They talk
over a TCP Extension API on `localhost:17362`.

This file is the short version, for orientation. It deliberately does
**not** restate the rules — they live in `doc/v3_fundament.md`, and a
second copy of a rule is a copy that goes stale. Read that file
before changing anything; this one only says where to look and which
habits are non-negotiable.

| Question | File |
|---|---|
| Why is it built this way? Decisions, principles, past mistakes | `doc/v3_fundament.md` — the index — and `doc/fundament/` |
| What exists today, what is missing, how to run things | `v3_projektstatus.md` |
| What does the original C++ do? | `doc/v3_orion2re_index.md` |
| The Planets screen: the source reading, and the range helper for its follow-up | `doc/plntsum_reading.md` |
| The Colonies screen: capability map, leverage points, the design | `doc/colsum_design_analysis.md` |
| The Extension API protocol | `doc/ext_api_dokumentation_v3.md` |
| What is being asked of Joes — **the only list** | `doc/orion2re_open_fixes.md` |
| How mods override files | `MODDING.md` |
| The 54 figure names, generated | `doc/modding_figures.md` |

---

## Before you change anything

**Read the index `doc/v3_fundament.md` first, then the parts your
task needs, and always every `principles-` part.** The fundament is
the point of the project and it is 195 KB — two and a half times what
work order 127 allows a session to read of one thing — so since work
order 164 that path is an INDEX and the rules are nine parts under
`doc/fundament/`, each one under 40 KB. Every entry in them was paid
for by a mistake, and several are counter-intuitive enough that they
will be re-broken by anyone who skips them. The sentence in bold above
is in the index too, word for word, and a smoke check holds the two
equal.

**Check the source, do not guess.** When the original's behaviour is
in question, grep the orion2re C++ rather than inferring from how the
game looks. `doc/v3_orion2re_index.md` is the map. This is the single
most productive habit in the project's history — the FMTPARA control
codes, the nebula world scale and the right-click help all came out
of reading the source after a guess had already been made and was
wrong.

**Two independent sources before a value is trusted.** Struct
offsets, sprite dimensions and colours get a numeric confirmation —
`tools/struct_probe.py` against a live game, a measurement off a
native screenshot — never an eyeballed estimate. And: *an asset is
not a measurement.* Pixel dimensions of a PNG must never be used to
derive world geometry.

---

## Non-negotiable habits

**The smoke test must be green before every commit.**

```bash
python tools/smoke_test.py             # everything — 299 checks, ~72 s
python tools/smoke_test.py --fast      # the commit gate's 292, ~32 s
python tools/smoke_test.py --screen colony_summary --fast   # NOT a gate
```

**During screen work iterate with `--screen <name>`; before every
handoff run the full suite; the push gate stays mechanical.** That is
the working rule, and it reads the same here and in decision 31.
`--screen` narrows what a run PRINTS — every check still runs, because
the checks share their fixtures and a run that skipped the others
would be measuring an app somebody else built (work order 162 measured
it: one screen's dependency closure is 87 % of the suite, and 96 %
under the only sound rule). It says `SCREEN <name> ONLY — NOT A GATE`
on its first and last line, and it widens itself to the fast tier,
naming the files, the moment anything outside that screen's own folder
and check modules has changed against HEAD.

**Two gates, both enforced by git** (decision 31, refined by work order
158). `tools/githooks/pre-commit` runs the **fast** tier;
`tools/githooks/pre-push` runs the **full** suite and refuses the push
on any exit but 0, 139 included, and on a PASSED line that says FAST
TIER. `python tools/setup.py` switches both on in a clone —
`core.hooksPath` names the directory, so it is the pair or neither.

**Full is the default.** The bare command above runs everything; only
the pre-commit hook passes `--fast`. A fast run says so in its PASSED
line, with the number of checks it did not run, so it cannot be mistaken
for a full one. The seven push-only checks are declared in
`smoke_test.SLOW_TIER` with the reason each is expensive, and a check in
the fast tier holds that list and the guards to each other.

**What the trade costs:** a fault only those seven can see lands at push
time, not at commit time. See decision 31 and
`doc/briefs/157-suite-profile.md`.

299 checks, headless, no orion2re needed. **The count must not go
down.** If a change makes a check obsolete, replace it — do not
delete it. It went down exactly once, on 12 September 2026, when
Phase B deleted the frame machinery the checks were about (decision
55): seven checks went with the tools they measured, and the
deletion is listed in `v3_projektstatus.md` with what replaced each
one. That is the only shape in which it may happen — the code a
check measures is gone, not the check. Add a check for anything a future session could silently
break; several checks exist because a fault was invisible on screen.

Prefer asserting the *rule* over the instance: "every `inner_panel`
box sits inside a `thin_border` box", not a list of coordinates.

**Label transcription against invention, everywhere.** Behaviour
copied from the original is a transcription and is marked as such,
with a source reference (`file.cpp:line`). Anything the original
cannot do — MOO2 is palette-indexed and cannot alpha-blend — is
marked `INVENTION`. A deliberate deviation is `HD EXTENSION`. The
label goes in the source, in the docs, and in a smoke check, so it
cannot quietly disappear.

**Generated files are never committed.** See decision 40 and
`.gitignore`. The licence to call a file "derived" is a byte-for-byte
check that regenerating reproduces it — not the existence of a tool
that looks like it made it.

**Code and documentation in English.** Conversation with the
maintainer is in German; identifiers, comments and docs are English.

**Comments explain why, not what.** Especially: why a value is that
value, and what was tried and rejected.

---

## Layout of the tree

```
main.py                 entry point, window, event routing
core/                   shared machinery — resources, layout, boxes,
                        style, the game client, the F5 box editor
core/structs/           declarative struct specs for the wire format
screens/<name>/         one folder per HD screen:
                          screen.py    behaviour
                          layout.json  content, labels, field IDs
                          boxes.json   positions, per resolution
                          help.json    right-click help regions
                          assets/
tools/                  smoke test, generators, live diagnostics
tools/smoke_suite/      the smoke test's 109 check modules, one group
                        per screen plus a shared core; smoke_test.py
                        is the runner (work order 162)
doc/                    the documents in the table above
mods/                   file-level overrides; example_mod works
```

Thirteen screens exist (the list below names eleven; fleets and
research change are in `v3_projektstatus.md`): main menu, new game,
select race, custom race, empire identity, galaxy map, colony
summary (list, sidebar, scan
box and galaxy inset; sort and RETURN wired, scrolling for
viewing only, and the population move click-click on the rows —
the first HD gesture that drives the game, see decision 47), and
planets (brief 101: list, sort, the five restrictions and RETURN
wired; sending ships is not built, and the range restriction is a
marked gap in the HD list), and the GAME menu overlay
(`screens/game_menu/screen.py`: the whole tree behind the galaxy
map's GAME button — slot names from `doc/ext_save_slots.patch` (applied),
the volume bars are built from work order 124, decisions 59-62),
and research select (`screens/research_select/`, wire id 53, work
order 130: the eight category panels, their rows and the commit, with
the frame and the artwork still to come — it hands BACK to the
fallback whenever the game's own field list contradicts the list it
reconstructed, or an extractor file is absent), and leaders
(`screens/leaders/`, wire id 29, work order 167: both views, every
leader row with the original's portraits and skill icons, the buttons,
the galaxy box, the hire popup and the skill help — BUILT, NOT
ACCEPTED, no outer frame yet, and without open fix 30 (not applied)
it sends only what it can see the effect of).
Screens without an HD version fall back to the original framebuffer,
so the game is always playable — and since work order 130 A that
fallback shows the picture AND forwards clicks, so a dialog HD has no
screen for can be answered in OrionLayer's window.

**Files over 300 lines are listed in `v3_projektstatus.md` with their
count** — the list is meant to be uncomfortable to extend. Split
rather than add to it, unless everything in the file is genuinely one
thing. The smoke suite is exempt from that guideline and held to a
stricter one: **no check module may pass 40 KB**, listed exceptions in
the same document, checked by the suite itself. A screen that outgrows
the limit gets another module in its own group, split by topic; a new
screen gets its own group; and a screen-specific check never goes into
another screen's group or into the core.

---

## Running it

```bash
pip install -r requirements.txt
python tools/setup.py          # rebuild generated artwork, then verify
python main.py                 # standalone works without orion2re
```

With the game (built `-DORION2RE_EXT=ON`), in a separate terminal:

```bash
cd "$HOME/Master of Orion 2" && ~/orion2re/out/build/Linux/linux-debug/orion2re
```

Two things come from the user's own MOO2 installation and are not in
the repository — neither is required to start:

```bash
python tools/help_extract.py                        # context-help texts
python tools/nebula_extract.py /path/to/starbg.lbx  # nebula sprites
python tools/techname_extract.py                    # building, ship-part
                                                    #   and research names
python tools/billtext_extract.py                    # research panel wording
python tools/estrings_extract.py                    # option strings
python tools/raceicon_extract.py                    # population figures
python tools/hestrings_extract.py                   # message strings
python tools/maintext_extract.py                    # system special texts
python tools/kentext_extract.py                     # weapon firing-arc words
python tools/officer_art_extract.py                 # Leaders screen artwork
python tools/skildesc_extract.py                    # officer skill help texts
```

Without the first, every right click opens a panel naming that
command instead of the game's text — which reads as a broken feature,
and did. The `--lang` must match `"language"` in `settings.json`; the
loader reads `help_<language>.json` and no other name.

**Never modify orion2re's tree.** C++ additions are gated behind
`#ifdef ORION2RE_EXT`, and anything wanted from Joes goes in
`doc/orion2re_open_fixes.md` — that file is the only list, and it has
drifted from a second copy twice.

**HARD RULE, NO EXCEPTIONS (Data): the orion2re project is never
uploaded anywhere — no push, no new remote, no fork, no copy of its
tree or bundles to GitHub or any other host. Patch files under `doc/`
in orionlayerv3 are explicitly allowed and not covered by this rule.**

The clone's push URL is disabled for that reason, and the smoke test
holds the other half: no orion2re source file may be tracked here, by
any name. Bundles go beside the tar backup in `~/` and stay there.

---

## Working with the maintainer

**You own every detail; the package owns the direction.** Line
numbers, offsets, values, branch tables and worked examples are
yours to verify — a number in a package is a starting point, and
correcting it belongs in the same commit. See "Who owns a detail,
and who owns a direction" in `doc/v3_fundament.md`, which is the
whole agreement and also records that a second copy of it lives in
chat-session memory and has to move with it.

Terminal instructions should be **self-contained, copy-ready blocks**
with the expected output stated, and file counts plus an abort
condition where something could go wrong. No explanatory prose inside
a command block.

Do not chain a verifier behind `&&` — it exits non-zero when it finds
something, which is the point.

**The display a live run needs, and how to find it.** Work order 139 E.
Two sessions before it recorded "`:0` is not reachable" and parked
their live part on it. **`xdpyinfo` was never installed** — the probe
was reporting `command not found`, and a tool that cannot measure
something must not be read as the thing being absent. The display was
reachable the whole time.

This session runs Wayland with Xwayland on `:0`, and SDL's wayland
driver does not work here ("the video driver did not add any
displays") while its x11 driver does. So a live run sets three
variables, and **the auth file is determined, never typed** — mutter
makes a new name at every login:

```bash
export DISPLAY=:0
export XAUTHORITY=$(ls -t /run/user/$(id -u)/.mutter-Xwaylandauth.* | head -1)
export SDL_VIDEODRIVER=x11
python - <<'EOF'
import pygame; pygame.display.init(); pygame.display.set_mode((160, 120))
print("display OK:", pygame.display.get_driver())
EOF
```

`display OK: x11` means the environment is right; anything else means
it is not, and the reason is in the exception, not in a missing
binary. `XAUTHORITY` is usually already correct in an inherited
environment — check it before setting it. Set these for the RUN, never
in a profile: Data's system configuration is not ours to change.

**IT DID NOT STOP ON 20 SEPTEMBER 2026.** With exactly the three
variables above, a session-launched orion2re ran through to `ext:
server started on port 17362` and served a full live acceptance (work
order 151 B). **Why it used to stop is still not established, so the
paragraph below stays** — a run that works is not a cause any more
than a run that failed was. What it does mean: try it before assuming
it will not come up, and do not park a live part on this note.

**AND THAT IS NOT ENOUGH FROM INSIDE A SANDBOXED SESSION — CAUSE
OPEN.** With all three set, orion2re still stops after `mox2: data
space allocated` from a session-launched run: the process sits at 0 %
CPU in state `S` at `rt_sigsuspend`, and the shell that launched it
exits 144. **Why is not established.** Work order 139 E wrote it up as
"suspended from outside" and that reading was wrong twice, corrected
by work order 140 A:

- **`S` is not stopped.** `T` is stopped. A process in `S` at
  `rt_sigsuspend` called `sigsuspend()` ITSELF and is waiting for a
  signal of its own — its own code's doing, not an outside stop.
- **144 is not SIGUSR1.** `128 + n` names signal *n* as `kill -l`
  numbers them, and on Linux 16 is **SIGSTKFLT**; SIGUSR1 is 10. The
  number was read off a habit rather than off `kill -l`.

So the two observations stand and the conclusion does not. What is
worth keeping is the METHOD: `ps -o stat,%cpu,wchan -p <pid>`
separates "the game is busy" from "the game is waiting" in one line,
and `kill -l <n>` is what names a signal — neither of them is a guess,
and the guess is what had to be withdrawn. Where the engine does not
come up, Data starts it from their own desktop session and this
session connects to it (work order 140).

**Loading a save and restarting the game are yours to do** (Data's
decision, 10 September 2026) — on two conditions: the report says
which slot and which fixture was loaded for each live step, and it
states that `~/Master of Orion 2/SAVE10.GAM` was checked against the
secured fixture copy before and after, because that slot is the
autosave and the game rewrites it at every turn end.
`SAVE11.GAM` in that folder is written and read by nothing in the engine
(every `Save_Game_`/`Load_Game_` slot is 0-9 and the slot loops stop at ten);
it is hashed with SAVE1-9 and must stay identical (work order 126 D,
`v3_projektstatus.md`).

State findings plainly, including the unwelcome ones. A wrong
assumption caught early is worth more than a smooth answer: most of
this project's best moments came from someone saying "that is not
what the source says".
