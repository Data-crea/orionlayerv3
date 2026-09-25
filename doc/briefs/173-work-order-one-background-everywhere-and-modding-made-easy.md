Work order <n> — One background everywhere, and modding made easy

Number: next free work-order number from the tree; rename before filing under doc/briefs/.

Mode

Unattended single run, no reporting stops, ending with a push (see the last section). Choices go to doc/briefs/<n>-parked-for-data.md with the default taken, progress to doc/briefs/<n>-progress.md. Builds on 169–172 (decision 71).

Start

Clone per CLAUDE.md. Read the fundament index, all principles- parts, part 04 with decision 71, and the progress and parked files of 169–172. Find how resources are resolved today (resource roots, setup.py, user_settings.json) before designing anything.

1. The universal background

~/Downloads/background_univeral.png (name as Data spelled it) is the background for every HD screen and popup backdrop — the slot 169 created with a dark placeholder.

Put it into the tree as authored artwork (decision 58's pattern), LICENSE entry as for the HUD. Measure its size, aspect and effective detail as in 168; say how it holds up at 2160p.
Scaling: fill the window without distortion (cover, crop the overflow, centred), at every window size including non-16:9. No stretching, no letterbox strips. Scaled once per window size and cached.
The galaxy map: use it as the map floor too, unless the current floor carries game content (it must not hide nebulae, wormholes or anything the engine draws). If in doubt, keep the game content on top and park the question with renders.
Readability: every text and table stays readable over the background. If a screen needs it, the HUD panel fill does the work — no per-screen darkening hacks. Measure contrast where text sits directly on the background.
The frame tint does not touch the background (172's component rule).
2. Modding: replace assets by dropping files in a folder

Goal: someone who is not a developer can change the look without touching code or the tree.

One override folder outside the tree (a user-writable location next to the settings file; find the right place on Linux and Windows). Same file name as the default = replacement. Missing file = default. Nothing is copied into the tree, nothing in it is ever committed.
What can be overridden, at least:
the universal background, and optionally one background per screen (per-screen file beats the universal one);
the HUD style values (a partial style.json — only the keys present override);
the HUD icons and the cut HUD pieces, by name;
the default frame colour (hue, saturation, brightness). Anything else that is easy to add through the same mechanism, add; list it.
Robust: a broken, wrong-format or odd-sized file never crashes and never breaks a screen — log one clear line and fall back to the default. Size mismatches are scaled like the default, not rejected.
One resolver for defaults and overrides; no screen loads its own files around it.
A template tool (tools/mod_template.py or similar) that creates a ready-to-edit mod folder: every overridable file name, recommended size and format, and a short MODDING.md in plain language. It copies OrionLayer's own assets (HUD pieces, icons, background, style values) as starting points. It never copies original MOO2 assets (extracted LBX art, fonts, texts) — for those, it lists the names only, because they are not ours to distribute.
A setting to switch mods off (use defaults) without deleting the folder. Whether several mods can be kept side by side and chosen is your call — park it.
Mark the whole feature HD EXTENSION; record it in the fundament as a new decision (resolver, override order, what is overridable, the MOO2-asset rule).
Tests
Full suite green, fresh clone green.
Checks: background covers the window at several sizes without distortion or strips; override order (per-screen > universal > default); partial style.json override; broken file falls back; mods-off setting; the template tool produces no MOO2-derived file.
Renders under ~/orionlayer-fixtures/evidence/work_order_<n>/: every screen at 1080p and 2160p with the new background, galaxy at 2576x1432, and one demo mod (a different background and colour) applied to galaxy and colony. Listed as things for Data to look at.
Live test only if orion2re starts cleanly; do not connect to an engine Data started. If blocked, run offline and park it.
Done when

Background on every screen, modding works through one folder with a template and a plain-language guide, decision recorded, checks in. Progress file ends with what was built, what was parked, and what Data should look at first.

Push — authorised by Data for this order

At the end, push to the remote. Data authorises this push explicitly; it replaces the usual "no push" for this order only.

Push only if, right before pushing: the full suite is green, a fresh clone with setup.py is green, and the working tree is clean.
This is a complete push: the whole local state of the OrionLayer repository goes to the remote — every local commit not yet pushed, from every work order since the last push (at least 167–172 and this one), plus any other local branch or tag of the OrionLayer repository that is not on the remote. Nothing is held back or picked. Before pushing, list everything that will go out in the progress file; after pushing, confirm local and remote are identical.
Nothing is force-pushed; no history is rewritten. orion2re stays local — only the OrionLayer repository is pushed.
If any gate fails, do not push: park it with the reason.
After pushing, record the pushed commit range and remote state in the progress file.
