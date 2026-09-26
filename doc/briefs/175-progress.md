# Work order 175 — progress

Unattended run, 26 September 2026. Fixes 30 and 31 applied, Leaders
complete, the Races and Info screens, Info's texts moddable, the string
extractor keeps its spaces, and the live-test protocol backs up every
file a run writes. Builds on 167 and 169-174 (decisions 71, 72).

Evidence root: `~/orionlayer-fixtures/evidence/work_order_175/`.

## Precondition — checked at the start

Data's engine is running: orion2re PID 368253 (parent 35660, started
10:03:06), listening on 17362, with Data's own client (`python main.py`,
PID 369007). Neither is connected to nor stopped. Everything that needs
no engine goes ahead; a live step runs only on an engine this run starts,
which the port does not allow while Data's is up.
