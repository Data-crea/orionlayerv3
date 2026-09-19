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
| Why is it built this way? Decisions, principles, past mistakes | `doc/v3_fundament.md` |
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

**Read `doc/v3_fundament.md` first.** It is long and it is the point
of the project. Every entry in it was paid for by a mistake, and
several of them are counter-intuitive enough that they will be
re-broken by anyone who skips it.

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
python tools/smoke_test.py
```

Git enforces it: `tools/githooks/pre-commit` runs the suite and refuses
the commit on any exit but 0, 139 included. `python tools/setup.py`
switches the hook on in a clone (decision 31).

225 checks, headless, no orion2re needed. **The count must not go
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
doc/                    the documents in the table above
mods/                   file-level overrides; example_mod works
```

Ten screens exist: main menu, new game, select race, custom race,
empire identity, galaxy map, colony summary (list, sidebar, scan
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
reconstructed, or an extractor file is absent).
Screens without an HD version fall back to the original framebuffer,
so the game is always playable — and since work order 130 A that
fallback shows the picture AND forwards clicks, so a dialog HD has no
screen for can be answered in OrionLayer's window.

**Files over 300 lines are listed in `v3_projektstatus.md` with their
count** — the list is meant to be uncomfortable to extend. Split
rather than add to it, unless everything in the file is genuinely one
thing.

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

**AND THAT IS NOT ENOUGH FROM INSIDE A SANDBOXED SESSION.** With all
three set, orion2re still stops after `mox2: data space allocated`,
and the reason is not the game: the process sits at 0 % CPU blocked in
`rt_sigsuspend`, and the shell that launched it exits 144 (SIGUSR1).
It is being suspended from outside. Measure it that way before
theorising — `ps -o stat,%cpu,wchan -p <pid>` separates "the game is
busy" from "the game has been stopped" in one line. Where that
happens, the live part is parked and Data starts the engine from their
own desktop session instead.

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
