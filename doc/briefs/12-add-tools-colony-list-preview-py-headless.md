Read doc/v3_fundament.md and CLAUDE.md first.

Add tools/colony_list_preview.py, modelled on
tools/starfield_preview.py. Headless (SDL_VIDEODRIVER=dummy), fake
colony rows defined in the script, no game connection, no snapshot.

It renders the real frame (screens/colony_summary/assets/frame.png)
through the real boxes.json geometry, and writes PNGs at 1920x1080
plus a 50% downscale of each. The 50% version is the noise test:
structure that survives the reduction reads as calm at full size.

Both modes in one run, written to distinct filenames - square mode and
figure mode must come out of the same invocation and the same
geometry, or the pair compares two layouts instead of two renderings.

Figure sprites come from a --pop-dir argument. Without it, run square
mode only and say so in one line - never crash. Nothing is read from
the repository for this.

Rows to include:
  - 22 pops, single race (the stress case; this is where the original
    squishes hardest)
  - three race groups in one row
  - max_farms == 0
  - a small colony, max_pop 9, so the unreachable region is 33 slots
    wide and you can judge whether the faint baseline reads as
    "expandable" rather than "cut off"
  - the same row rendered alone and inside a list containing a larger
    colony, side by side: that is the invariant the new smoke check
    asserts, made visible.