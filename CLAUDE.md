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
| The Extension API protocol | `doc/ext_api_dokumentation_v3.md` |
| What is being asked of Joes — **the only list** | `doc/orion2re_open_fixes.md` |
| How mods override files | `MODDING.md` |

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

68 checks, headless, no orion2re needed. **The count must not go
down.** If a change makes a check obsolete, replace it — do not
delete it. Add a check for anything a future session could silently
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

Seven screens exist: main menu, new game, select race, custom race,
empire identity, galaxy map, colony summary (frame + sidebar only).
Screens without an HD version fall back to the original framebuffer,
so the game is always playable.

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
```

Without the first, every right click opens a panel naming that
command instead of the game's text — which reads as a broken feature,
and did. The `--lang` must match `"language"` in `settings.json`; the
loader reads `help_<language>.json` and no other name.

**Never modify orion2re's tree.** C++ additions are gated behind
`#ifdef ORION2RE_EXT`, and anything wanted from Joes goes in
`doc/orion2re_open_fixes.md` — that file is the only list, and it has
drifted from a second copy twice.

---

## Working with the maintainer

Terminal instructions should be **self-contained, copy-ready blocks**
with the expected output stated, and file counts plus an abort
condition where something could go wrong. No explanatory prose inside
a command block.

Do not chain a verifier behind `&&` — it exits non-zero when it finds
something, which is the point.

State findings plainly, including the unwelcome ones. A wrong
assumption caught early is worth more than a smooth answer: most of
this project's best moments came from someone saying "that is not
what the source says".
