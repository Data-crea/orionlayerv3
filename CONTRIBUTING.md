# Reading and changing the code

## Notes in the source

Comments in the code cite the maintainer's developer notes as
`dev:<path>`. Those notes (design decisions, working principles, readings
of the orion2re source, measurements and the maintainer's test suite) are
not part of this repository. A citation says where the reasoning behind a
line is recorded; it is not a file you are missing. The numbers of work
orders, decisions and open fixes in comments refer to the same notes.

### Reading the numbers

| In a comment | It means | Where you can look it up here |
|---|---|---|
| `work order N`, `WO N` | one unit of the maintainer's work | recent commit messages start `Work order N:`; older ones name it in the text or at the end, so search with `git log -E --grep="(work orders?|WO) [^:]*N" -i` |
| `open fix N`, `fix N` | one change the OrionLayer branch of the engine fork [Data-crea/orion2re](https://github.com/Data-crea/orion2re) carries | the head of a patch file in `doc/` or `doc/v2/` (`grep -rli "open fix N" doc --include='*.patch'`; a few heads say `item N` instead, and a number may have no file); the fork's `docs/extension-api.md` describes the interface |
| `decision N` | a numbered project rule | the ones that shape this repository: generated files are never committed; no picture is in the repository (the base pack, listed in `basepack.json`, holds them); only the maintainer accepts a screen, by playing it or from pictures; how the engine fork is changed, what of it goes online, and the form of the Extension API |
| `PNNN`, `FNNN` | a working principle or a fact the notes record | e.g. two independent sources before a value is trusted; a value is measured, not judged by eye |
| `dev:doc/...`, `dev:tools/...` | a file of the notes | not here; the sentence around it states the reason |

A number is a pointer to a reason, and the sentence beside it should carry
the reason itself. If a comment's number leads nowhere you can follow and
its sentence does not explain the line, that is a documentation fault:
say so in an issue.

A comment that cites `file.cpp:line` points into the orion2re source
whose behaviour the line copies. The line numbers are those of an earlier
orion2re version, so look the function up by its name. Labels in capitals
say how a piece relates to the original game:

- `TRANSCRIPTION`: copied from the original, with its source.
- `INVENTION`: something the original cannot do.
- `HD EXTENSION` and `DEVIATION`: a deliberate difference.
- `OMISSION`: the original has it and OrionLayer does not draw it yet.
- `HD STATE`: OrionLayer draws or keeps a state itself because the engine
  does not send it (a stand-in for a value, or a local the engine never
  holds).
- `UNVERIFIED`: read from the source but not yet confirmed in a running
  game.

Please keep these labels, and the source references, when you change a line
they sit on.

## Pull requests

Issues and pull requests are welcome; open them against `main` (players
clone the `beta` branch, which the maintainer moves forward). Start
OrionLayer and look at what you changed (`python main.py` runs without the
game); a change to a screen is best shown with a screenshot beside the
original's (F12 shows it, F8 saves a picture).

The maintainer's test suite is not in this repository: he runs it on every
change before it is merged, and tells you what it found. What you can run
yourself is `python tools/setup.py --check` (reports what is missing and
changes nothing) and the program itself.
