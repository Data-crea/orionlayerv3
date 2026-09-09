Dachte 4 s nach

Auftrag — Pfad ist ~/Bilder/rahmen, sieben Dateien:

Frame candidates — measure, rename, report. No cutting, nothing into the tree.

Folder: ~/Bilder/rahmen/. Six image-tool renders (image-*.jpg) and background.png, which is a hand-made derivative with alpha and is known to be anisotropically stretched — keep it, measure it, but treat it as a derivative, not a candidate.

Step 0 — bezel question, before touching the files. Measure the metal ring width of the main-screen frame.png master at 1920 and compare it with the 36 px bezel in layout_reference.json. If they disagree, report which one has to give and why, then stop. Everything below depends on that answer.

Step 1 — measure every file, one row each:

    canvas size; metal extent by threshold sweep (three thresholds; is the bbox stable?)
    metal aspect ratio, deviation from 16:9 in %
    margin per side — does the frame fill the canvas?
    metal width against 1920 / 2560 / 3840: downscale, upscale factor, or unusable
    interior: one clean rectangle, or remaining struts/stubs (count)
    header window and bottom slots present, count
    light hue vs frame.png (sample the amber, report the shift)

Step 2 — rename by content, keep provenance. Scheme: colony_frame_cand_<NN>_<metalW>x<metalH>.<ext>, numbered in file-timestamp order. background.png becomes colony_frame_derived_stretched_<W>x<H>.png. Write manifest.md in the folder: old name → new name, plus the row from Step 1. Nothing is deleted; the manifest is the only place the original names survive.

Step 3 — recommendation. Which candidate, cropped how (pixels per side, never stretched), serves which resolution; which resolutions become upscaled interim variants and need a dated entry in the status document. Say if none is good enough and what the next render would have to fix.

Reporting stop after Step 3. Cut, scale and write only after Data has read it.