# Work order 186 — parked for Data

Every item names the default this run continued with and why. First what
this order decided or left open, then the items carried over unchanged.

## 1. From this order

### 1a. Open fix 42 — not approved, not applied, stays open

Entry 42, "A screen is silent on the wire while its input delay counts
down": NOT APPLIED, its row and `version_check`'s `REPORTED_PATCHES` as
before; nothing in this run builds on it. Part 4 measures whether the
modal hold depends on it (see there). **Default: open.**

### 1b. The bundles' names

The order's pattern is `~/orion2re_bundle_<date>_<hash>_fixes34-<last>.bundle`.
Fix 42 is in none of the bundles, and the last fix applied is 43, which is
lower than 47 — so the five are named `…_fixes34-44`, `-45`, `-46`, `-47`
and `…_230a0638_fixes34-47_43.bundle`, the last saying that 43 came after
47. **Default: as named**; README names the newest.
