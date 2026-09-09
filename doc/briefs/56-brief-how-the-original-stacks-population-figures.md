Brief: how the original stacks population figures

Investigation only. No code in screens/, no layout.json change. Deliverable is one document, doc/pop_stacking.md, that states the rules with citations and a measurement against the running game. Read doc/v3_fundament.md first; the rules that apply most are "read the function that BUILDS the thing" and "two independent sources".

Why

The HD colony screen may get a second population style that draws the original's figures (from raceicon_ref/) instead of the allocation cells. That style has to place figures the way the original does, and today the tree knows only that Calculate_Squish_Step_ exists and that figures overlap. That is not a rule; it is an observation.

Questions the document must answer, each with file:line
Where is it drawn, and on which screens. Which functions place population figures, and which screens call them — colony main screen (colony.cpp), colony summary (colsum.cpp), both, others? Starting points, to be re-anchored: Do_Colony_Info_Pop_Stuff_For_Pop_ (coldraw.cpp:282), Calculate_Squish_Step_ (coldraw.cpp:12-33), the draw call at coldraw.cpp:344-347. If the two screens use different placement, say so and give both.
The step. The exact formula for _step_squish: inputs, the threshold at which figures start overlapping, the minimum step, and whether the count that drives it is the group's, the column's, or the colony's. Quote the arithmetic, not a paraphrase.
Columns. How many, in which order (ECON?), their x origins and widths in 640x480, and whether the width is a constant or comes from a field rectangle. Where does column N end — is there a hard clip, or can a crowded column run into its neighbour?
Draw order = z-order. Within a column, which figure is drawn first and which lands on top. Index 0 is transparent, so the last drawn is fully visible. Is the walk left-to-right, and is the walk order the same one colonyrows.py already transcribes as the display order (storage order is not stable — see memory)?
What is placed where. Within a column, are natives, androids and conquered pops interleaved with the player's race, grouped, or sorted? What decides the sprite per figure — People_Anim_'s race index, and which race field feeds it (the race_idx/MASK_CONQUERED discrepancy already flagged for Joes belongs here)?
pop_state 4. Pop_To_Pop_State_ returns 2, 3 or 4. The figure drawn is the odd entry for state 2. What is drawn for 3 and 4, and when does a pop have those states — is that the held/moving cluster, and does it change position, sprite, or both?
Selection and clusters. When a cluster is picked up (COLMOVE), how are the remaining figures re-laid out — does the step recompute, do gaps appear, do figures shift?
Second source: measure it

Start orion2re with the reference save. For at least three colonies with different counts in one job — small (step 30 expected), the threshold, and a crowded one (Wolf II, 13 pops) — capture the native frame and measure the x position of each figure's leftmost opaque column. Put the measured steps in a table beside the formula's prediction. They must agree to the pixel; if they do not, the formula as read is wrong, and the document says which line was misread.

Use raceicon_ref/ sprites for template matching if that helps — the per-index match already used for acceptance is the right tool.

Out of scope

Do not decide what HD does with the rules. The document ends with a section "Open for HD" listing the choices the rules leave open (reproduce the overlap at HD width, or use the width; hard clip or not), each as a question. No recommendation.

Acceptance
doc/pop_stacking.md, every rule with file:line from the patched working tree, every number with its source.
Measurement table, three colonies minimum, prediction vs measured.
No other files changed. No push.