# Work Order 163 — What can be modded about orion2re's AI behaviour (reading only)

First line for references: "Work Order 163 — What can be modded about
orion2re's AI behaviour (reading only)"

Filed as 163 because 162 was the last one. Check that before filing and
take the next free number if it is taken.

Read `doc/v3_fundament.md` first. `doc/tech_change_reading.md` is the
model for what this order wants: a reading report, not a design.

## What this is and is not

**Reading only. No code, no patch, no proposal for one, not in
OrionLayer and not in orion2re.** Nothing in either tree is changed
except the report this order produces. The result is a document Data
reads to decide whether the subject is worth anything at all.

**Behaviour, not content.** Out of scope: which ship designs the AI can
build, which parts exist, what the tech tree contains. In scope: how an
AI player decides. Expansion and colonisation, what it builds, research
priorities, diplomacy and treaty-breaking, when it declares war and what
it attacks, combat tactics, how it reacts to the human player.

**One session, timeboxed.** This is off the release path. Breadth over
depth: it is better to map all seven areas roughly than to understand
one of them completely. Where the time runs out, say so in the report
instead of going deeper.

**Every claim carries a file and a line**, as always. An inferred call
chain is not evidence — read the function that makes the decision, not
the ones that report it. Anything unconfirmed is labelled as such.

## Questions

1. **Where does the AI decide anything?** Which files and functions, per
   area (the list above). A map, not a deep read.
2. **Where do the numbers live?** Literals in the code, named constants,
   tables, or data loaded from an LBX. For each finding: file, line, and
   which of those four it is.
3. **Difficulty and personality.** MOO2 gives its AI opponents fixed
   traits (aggressive, pacifist, and so on) and scales by difficulty.
   Where is that, and is it a table or a branch?
4. **What is moddable today without touching C++?** If the answer is
   nothing, say so plainly. Then: which single change would open the
   most — for example moving one table into a data file — and how large
   is it, in files and lines?
5. **What does the Extension API expose?** Can a client read any AI
   state at all through the snapshot or any other message? If yes, what.
6. **Where is the reconstruction incomplete?** orion2re rebuilds the
   original. Note TODOs, stubs and visibly simplified behaviour in the
   areas above — that is where a mod would change something the original
   never did.

## Output

`doc/ai_behaviour_reading.md` in the OrionLayer tree, English, same
shape as `doc/tech_change_reading.md`: findings with file and line, a
section for what could not be confirmed, and a closing list of open
questions for Data.

Then a short summary in German in the chat, for someone who will not
read the code: what the AI decides where, whether any of it is moddable
without a C++ change, and what the one cheapest opening would be. Say
honestly if the answer is "nothing without touching the engine".

No commit of anything but the report. Push is Data's decision.
