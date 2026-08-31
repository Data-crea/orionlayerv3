# Where the background star field numbers come from

The galaxy map's HD background carries gas clouds but no point
stars, and next to the original that reads as an empty map. This is
the measurement that decided what to draw instead of guessing.

Source: a native-resolution screenshot of the original galaxy map,
`1788014399143_grafik.png`, 1494x1199, upscaled 2.855x from a
523x420 crop of the 640x480 screen. Reproduce with:

```bash
python tools/starfield_measure.py <screenshot.png> --threshold 12
python tools/starfield_measure.py <screenshot.png> --crop 30,200,280,400
```

The tool detects the upscale factor from the periodicity of the
image's own column gradient, so every number below is in **native**
pixels regardless of how the screenshot was scaled.

---

## Method

1. Label connected lit regions; keep only those under 1.9 native
   pixels across. Star sprites (17–33 px), names, nebulas and
   wormhole links are all larger and drop out.
2. Split survivors by `|R - G| > 6` into grey (the field) and
   coloured (nebula fringe, 6 % of hits — discarded).
3. Take the brightest pixel of each survivor as its grey level.

Thresholds were swept at 12, 20, 32, 48 and 72. The count falls
smoothly and the tier shares stay put, which is what a genuine
brightness distribution looks like — as opposed to the guardian
icon, whose size jumped 45 % across a sweep because the measurement
had bridged into two background stars.

---

## Results

### Density — two independent crops

| Region (native) | Area | Grey stars | 1 star per |
|---|---|---|---|
| 30,200–280,400 (below the fleet lane) | 50,000 px² | 1,501 | 33.3 px² |
| 300,60–500,200 (upper right, no nebula) | 28,000 px² | 864 | 32.4 px² |
| whole map rect, nebulas included | 191,127 px² | 5,110 | 37.4 px² |

Two nebula-free crops agree within 3 %. `DENSITY_NATIVE = 33.0`;
the whole-rect figure is the far end of the bracket, low because
nebula-covered area still counts as available sky.

Over the full map area (505x399, field 23) that is **6,105 stars**,
covering 3.0 % of all pixels.

### Brightness tiers

All values are multiples of 4 — a 6-bit VGA palette ramp — and every
grey star measured as `(v, v, v + 8)`. The ramp itself is tinted
blue; the stars are not individually coloured.

| Grey | Count | Share | Cumulative |
|---|---|---|---|
| 16 | 1,566 | 30.6 % | 30.6 % |
| 24 | 1,599 | 31.3 % | 61.9 % |
| 36 | 217 | 4.2 % | 66.2 % |
| 44 | 1,210 | 23.7 % | 89.9 % |
| 60 | 114 | 2.2 % | 92.2 % |
| 72 | 88 | 1.7 % | 93.9 % |
| 80 | 81 | 1.6 % | 95.5 % |
| 88 | 87 | 1.7 % | 97.2 % |
| 96 | 65 | 1.3 % | 98.5 % |
| 108–172 | 65 | 1.3 % | 100 % |

**This is the whole answer to "how do I keep it calm".** The field
is dense — three per cent of every pixel — and 90 % of it sits at or
below grey 44, between 6 % and 17 % of full white. Fewer than one
star in seventy exceeds 96. Density is not what makes a star field
noisy; brightness is.

The smoke test asserts the dim share stays above 85 %.

### Spatial distribution

Counted into an 8x6 grid, cell-to-cell spread is 50 against the 12
that uniform noise would give — the original field is clumped, with
a denser band through the middle. That sample is contaminated: the
nebulas sit inside the measured rect and contribute dim pixels of
their own. So the transcription stops at "not uniform" and
`clumping` ships at 0. Turning it on is a design decision, not a
correction.

---

## What is deliberately not transcribed

**Motion.** Nothing in the field moves. MOO2 draws its backdrop
palette-indexed and cannot fade or animate a background pixel, so a
twinkle would be an invention — the same class of mistake as the
black hole's brightness pulse, which took a session to notice and a
minute to delete.

**Dot size.** In the original a star is one pixel. On an ultrawide
that pixel is about 4.8 HD pixels across, and drawn at full size the
field turns into visible blobs (variant A in
`starfield_variants.png`). `dot_native` and `count_scale` exist for
exactly this trade and are the only knobs that are deviations rather
than transcriptions. Whatever ships above `count_scale = 1.0` should
be recorded as a deviation in the status document.

---

## Open question for the source

Does the original's backdrop scroll with the map on a galaxy large
enough to pan? `StarfieldLayer` is anchored to the map box, which is
what a painted backdrop does and what the current HD background
image already assumes. Confirm in `MAINSCR::Main_Screen_`'s redraw
path before treating it as settled — if the backdrop is redrawn at a
map offset, the layer needs the offset folded into its cache key and
a slightly larger surface to pan across.
