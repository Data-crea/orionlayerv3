# 146 — parked for Data

## 1. The frame carries its own outer ring, and it is not the shared one

Built as it is, per the order. The question is whether it should stay
that way.

Metal pixels only (luma > 45, saturation < 0.34):

| ring | metal mean RGB | median luma |
|---|---|---|
| **v4 Fleets (its own)** | (88.7, 87.4, 86.4) | 80.0 |
| planets | (97.2, 98.1, 98.7) | 83.7 |
| shared `skins/default/frame` | (97.4, 96.2, 95.1) | 78.7 |
| galaxy_map | (87.4, 88.1, 86.0) | 75.3 |

Side by side in `RINGS_side_by_side.png`.

**It is not an outlier — it sits between the two rings already in the
tree.** v4 (88.7) is within 1.5 of galaxy_map's (87.4) and about 9
below planets'. So "the Fleets ring differs from the shared ring" is
true, and the shared ring is not itself uniform: galaxy_map's is
already 10 darker than planets'.

Three ways, none of them mine to pick:

1. Leave it. Fleets wears its own ring, as galaxy_map effectively
   already does, and the tree accepts that screens differ by a shade.
2. Re-cut v4's ring to the planets/shared value. That means retouching
   Data's artwork, which this order forbade, so it would be a new
   order with a new image.
3. Make the ring shared for real — one ring image behind every screen,
   with each screen contributing only its inner holes. That is the
   biggest change and the only one that makes "the shared ring" a fact
   rather than a description.

## 2. The known source artefact is still there

A short bright stroke beside the text panel's bottom-left corner, at
roughly image (208..232, 938) in reference px. Left alone as
instructed, and noted in `layout.json`'s `frame._note` so nobody
"fixes" it later without knowing it was deliberate.

## 3. The display cannot present a window, and this is now worked around

`import -window` could not photograph anything: the compositor placed
OrionLayer at **(-985, -565)**, and a fullscreen request was answered
with **"granted 1x38"** (in the log, verbatim). The game renders
correctly the whole time — the surface is right, the output is not.

Rather than park the evidence, this run added **F8, a TOOL that saves
`pygame.display.get_surface()`**, and the live screenshots in
`evidence/work_order_146/` come from it. It is in `main.py` with its
reason, and it is the reason `main.py` went from 304 to 323 code lines
on the over-300 list.

Worth Data knowing because the same display state will defeat any
future `import`-based evidence, and because two earlier orders (138,
139) burned a session each on display problems of this family.

## 4. One live step not done

Clicking a ship cell and watching the selection change could not be
**verified** live: the proof is visual (a selection frame, SCRAP
lighting) and, with no window to capture at the moment those steps ran,
there was nothing to compare. The geometry itself is proven live
another way — `btn_return` fired from its new hole-derived position
(1670, 924) and the game changed screen — and the cell rects are held
to the holes by a smoke check. A later run with F8 in place can close
it in one pass.
