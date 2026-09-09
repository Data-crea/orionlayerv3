Brief — Colony frame, Stage B and Stage C (one stop)

Read doc/v3_fundament.md before touching anything. This brief sets direction and acceptance criteria; every number, line and offset is yours to establish and report. Stages A–A3 are in the tree up to d5b28be plus the galaxy-scale commit; this picks up from there.

Carried over from the last commit

Add to the existing max_map_scale check in tools/smoke_test.py: no key of STOCK_MAX_MAP_SCALE is a product of MAXIMUM_GALAXY_CELL. Message names the consequence (a Maximum galaxy of that width would be routed to the literal arm). No new check, no counter movement.

Stage B — the preview switch

One mechanism, one place. When the flag is on, the colony screen renders the built plate from Stage A3; when it is off, the shipped colony_summary/assets/frame.png path is what runs today, byte for byte. The log states PREVIEW once at screen load when the flag is on, and says nothing when it is off.

Acceptance:

Flag off: the rendered frame surface hashes identically to the current tree's — asserted in the smoke test, not eyeballed. Name the file the hash is read from.
Flag on: the log line is present and names the plate's source and its hash, so a screenshot can be matched to the build that made it.
The switch selects a source, not a code path: no second drawing routine, no duplicated geometry (decision 5). If you find the switch needs a second path, stop and say why.
Nothing about the flag lands in boxes.json (decision 37's serialisation rule applies: runtime state is not layout).
Stage C — derived or asset

Decide whether the built plate is a derived file (never committed, regenerated on every clone, byte-for-byte verified by a smoke check that rebuilds it from the master) or an asset (committed; frame_build.py becomes a tool run only when the master changes, and a smoke check asserts the committed plate matches a fresh rebuild — the pattern of decision 3, frame_holes.py versus boxes.json).

I want your recommendation with the consequences of each, not a preference:

what a fresh sparse clone (no screens/*/assets) can and cannot render in each case;
what the smoke test costs in time per run in each case;
what happens the day the master is replaced by the ≥3840 family master — which files change, which checks fire;
whether either option puts a derived file in the tree without the byte-for-byte verification that licenses the word "derived".

The decision is Data's and goes into the fundament under Sizing and artwork with the next free number, with the rejected option and the reason recorded. Status document entries for B and C.

The header window — a question to verify, not a finding

In the A3 image the header window is visible only as a light line. Question: in galaxy_map/frame.png, is the header opening its own window with a chamfer of its own, or does it share the ring's edge? Measure it in the master with frame_master.py's profile method, put the crop beside a native screenshot of the original colony screen at the same spot, and report what each shows. If the answer is "the original has no such window", say so — that is a legitimate result (fundament: "sometimes the honest answer is the original could not do it either").

Standing permission — orion2re, conditional

Data has authorised changing orion2re if it must be. The conditions are the rule, not the exception:

only when the need cannot be met on OrionLayer's side; state at Stop 1 what was tried there first;
the change is recorded in exactly one home, doc/orion2re_open_fixes.md, with status "applied locally, not upstream", the reason, and the file:line touched;
the diff is kept as a patch file under doc/ so the change can be re-applied to a fresh clone and categorised in the cross-tree comparison;
the reference save and the fixtures are not affected; hashes reported before and after.

I expect this stage needs none of it. If it does, it is a Stop 1 item, not a Stop 2 surprise.

Reporting stops

Stop 1 — before any code. Where the built plate lives today and who reads it; where the switch would sit and why there; your Stage C recommendation with the four consequences above; the header-window measurement beside the native crop; any orion2re need. Wait.

Stop 2 — after implementation. Diff summary, the flag-off hash proof, the flag-on log line, the smoke count, the fundament diff for the Stage C decision, and evidence images