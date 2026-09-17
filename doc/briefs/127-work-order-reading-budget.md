Work order <next free number> — A reading budget: split the status document and the fundament, and give the split a checker (drafted 17 Sep 2026, to be run later)

Assign the next free work-order number when this is filed under doc/briefs/. It was drafted in chat against origin/main at d8006d7 and is meant to run AFTER the colony runs that are open today, not between them. No live run is needed anywhere in this order. Separate commits, push stays with Data.

If Run 3 of workorder_colony_runs_and_doc_audit.md (the documentation audit) is still open when this starts, do the two together. Run 3's rules apply here unchanged: a deletion only with a named new home, evidence preserved, no renumbering of decisions, and a mandatory CLAUDE.md change statement.


Why

The files in this tree are not long because of their code. Decision 6 already counts CODE lines since 4 September, and by that measure the tree is fine. What has grown is the prose, and the reader of that prose is you: everything a session must read before it may touch anything is context that is gone before the work starts, and rules read at the top of a long session are the ones that get broken at the bottom of it.

The aim is NOT fewer tokens. The aim is that the mandatory reading is small enough to stay present for a whole session, that nothing expensive is lost to get there, and that the size is held by a check instead of by good intentions (decision 36: a checker, not a reminder).


Chat's measurements — claims to verify, not facts

Measured in chat on a fresh clone of d8006d7 with a throwaway script, NOT with tools/linecount.py. Per the division of labour these are yours to confirm or correct before anything is built on them.

  v3_projektstatus.md         about 9,700 lines, about 556 KB
  doc/v3_fundament.md         about 3,200 lines, about 184 KB
  CLAUDE.md                   about 9 KB
  core/ + screens/ + main.py  about 32,500 lines, of which about 15,500 are code (47 %)
  colony_summary/colonyrows.py   about 1,080 lines, about 240 code (it was 629 / 141 in the status entry of 4 September)
  colony_summary/colonytrack.py  about 980 lines, about 190 code
  colony_summary/colonylist.py   about 940 lines, about 225 code
  core/zoomtables.py             about 900 lines, about 205 code
  tools/smoke_test.py opens v3_projektstatus.md in roughly 37 places and doc/v3_fundament.md in roughly 14

The status document describes itself as rewritten every session. At this size it is appended to, which is the thing the fundament says about date-ordered lists.


STOP 1 — read, measure, propose. No file is changed.

A. The numbers. Run tools/linecount.py and report the table above from it, corrected where chat was wrong. Add two figures chat did not have: the total byte size of everything CLAUDE.md makes mandatory at session start, and for every product file over 400 total lines its text share (docstrings plus whole-line comments over total).

B. Every check that reads a document. List each place in tools/smoke_test.py and in tools/*.py that opens v3_projektstatus.md, doc/v3_fundament.md, CLAUDE.md or doc/orion2re_open_fixes.md. For each: which file it reads, which needle or marker it looks for, and what it asserts. This list is the precondition for moving anything — a check that stays green after its needle has moved to another file is worse than a red one, because it now asserts nothing.

C. A split for the status document. Propose which sections are CURRENT (what exists today, what is missing, the knowingly-over-300 list, the deviation table, open items — whatever a session actually needs) and which are ARCHIVE (the narrative of past sessions and closed work orders). Say where every marker from B would live afterwards. The current file keeps its path, v3_projektstatus.md, so pointers and checks do not all have to move.

D. A split for the fundament. Propose a kernel entry format — the rule, ONE sentence of the case that paid for it, and a pointer to the full case — and a home for the full cases. Rewrite exactly two entries in that format as samples and put them in the report, not in the tree: decision 38, and the working principle about a measurement that is not stable under its own threshold. Data judges from those two whether a kernel entry still carries its weight. "Numerically verify" alone is a platitude; "the guardian shipped at 17x16 and is 12x11" is what makes it a rule. If a sample cannot be shortened without losing that, say so instead of shortening it.

E. A budget. Propose a byte ceiling for the mandatory reading set, with the measurement behind it: what the set would weigh after C and D. Chat suggested something near 60 KB as a starting point; that is a guess, not a requirement.

F. Three files, classified, not edited. For colonyrows.py, colonytrack.py and zoomtables.py, sort every docstring and comment block into one of three kinds and report the share of each:
  EVIDENCE    where a number or rule comes from (a source file and lines in orion2re, a measurement document). This is the project's capital and stays beside the code.
  HISTORY     how the code came to be — what it was split from, what it used to do, which guideline it was brought back under. This belongs in a commit message. It goes stale in place: colonyrows.py still says it was split to get back under the 300-line guideline.
  DERIVATION  longer reasoning, and "not drawn / not done" sections. The tree already has a home for these in the doc/*_reading.md pattern; the code keeps a pointer.
Where a block is two kinds at once, say so; do not force it.

Report and stop. Data decides: the budget figure, whether the two kernel samples are acceptable, how fine the archive is cut (per work order, per month, one file), and the text-share threshold for the warning in Stop 2 part 3.


STOP 2 — build, after Data's decisions. One commit per part.

1. Split the status document as decided. Archive files are append-only and nobody reads them by default. For EVERY check from B whose needle is affected: show that it still finds its marker, and show once that it can still fail — remove the needle in a scratch copy, see red, put it back. Report that per check, not as a summary.

2. Split the fundament as decided. doc/v3_fundament.md stays at its path and becomes the kernel. Decision numbers are identities: no number moves, none is reused, the uniqueness check keeps running. Add two checks: every pointer in the kernel resolves to an existing case, and every case has a kernel entry. Nothing is deleted in this commit — a case moves whole, byte for byte, and only then is the kernel entry shortened.

3. The checker. tools/linecount.py learns the mandatory reading set and its ceiling; the smoke test fails when the set is over budget. The list of files in the set has exactly ONE home, and CLAUDE.md points to it rather than repeating it (the fundament's own rule about a name table copied into three files). The per-file text share is printed as a WARNING list above the decided threshold — a warning, not a failure: a high text share is a reason to look, not proof of a fault, because evidence is text too.

4. CLAUDE.md. The reading rule becomes: kernel always; the full case when the area it covers is touched; the archive only on instruction. Write the mandatory change statement. This rule is deliberately mirrored in chat memory, and silent divergence between the two copies is a known failure of this project — so put the exact new wording in the report, in one block Data can carry to chat.

5. The docstring rule, filed as a new decision under the next free number: a docstring says what holds and where it comes from, not how it got there; history goes to the commit message; long derivations go to a reading document with a pointer left behind. This is NOT a sweep. It applies to a file when other work touches that file anyway. The only files edited for it in this order are the three from Stop 1 F, as the worked example, and only if Data approved that at Stop 1. In those three: no source reference is removed, and every moved block has its new home named in the commit message.


Not in this order

No restructuring of code. No shorter identifiers, no merged modules, no function made denser to save tokens — the code is already cut small and that is what keeps it reviewable.
No source reference is shortened or removed anywhere. "colxport.cpp:91-99" costs a few tokens and saves a reading session.
screens/galaxy_map/screen.py is the one module that is genuinely large by CODE, and Brief 110 part C will land in it. Splitting it along a seam it already has is worth doing before part C, but it is a separate order — note in the report whether you see such a seam, and leave it there.


Protocol

Smoke test green before every commit, and the commit coupled to the test result — the exit-139 run that was committed anyway is the reason this line is here. Verify the final state in a fresh clone before reporting done. No push.


How this will be judged

Not by the byte count. Record the before-and-after sizes in the report so the comparison exists, but the question Data will ask after a few work orders is whether late-session violations of rules read at session start have become rarer. If they have not, the split did not do its job and the report from this order is where the next attempt starts.
