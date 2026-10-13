# Reading and changing the code

## Notes in the source

Comments in the code cite the maintainer's developer notes as
`dev:<path>`. Those notes (design decisions, working principles, readings
of the orion2re source, measurements and the maintainer's test suite) are
not part of this repository. A citation says where the reasoning behind a
line is recorded; it is not a file you are missing. The numbers of work
orders, decisions and open fixes in comments refer to the same notes.

A comment that cites `file.cpp:line` points into the orion2re source
whose behaviour the line copies. The line numbers are those of an earlier
orion2re version, so look the function up by its name. Labels in capitals say how a piece
relates to the original game: `TRANSCRIPTION` (copied from the original,
with its source), `INVENTION` (something the original cannot do),
`HD EXTENSION` and `DEVIATION` (a deliberate difference), `OMISSION`
(something the original has and OrionLayer does not yet).

## Pull requests

Issues and pull requests are welcome. Start OrionLayer and look at what
you changed (`python main.py` runs without the game); a change to a screen
is best shown with a screenshot beside the original's (F12 shows it, F8
saves a picture).
