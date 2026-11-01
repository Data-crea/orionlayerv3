"""Put the player's ambassador films into the mod folder — work order 359.

    python tools/audience_video_install.py <race> <folder> [--lights[=2]]

`<folder>` holds one film per mood — `first_contact.mp4`, `friendly.mp4`,
`neutral.mp4`, `pleading.mp4`, `threatening.mp4`, and `default.mp4` for
every mood without a film of its own (any may be missing) — and
`<race>` is the race's name (`screens/audience/auvideo.RACES`). Each film
becomes `<mod folder>/files/screens/audience/assets/video/<race>/<mood>/`:
JPEG frames, `audio.ogg` and `clip.json`, which the audience reads with
pygame alone (HD EXTENSION `ambassador_video`, `auvideo`). The films are
read, never changed. Every ffmpeg runs through `ffrun`.

`--lights[=seconds]` (HD EXTENSION `ambassador_video_lights`, needs numpy,
Pillow and scipy): after the film the last frame is held and only the
green light over the ambassador and the helix beneath keep moving, in a
loop over the film's last `seconds` (2). The ambassador stands still: a
film's figure gestures all the way through it, so a loop of its last
seconds would read as the whole film repeating (measured, work order 359).
`cut_lights` writes `glow/NNNN.png`, one RGBA patch per frame, and the
`glow` entry of `clip.json`.
"""
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import ffrun  # noqa: E402
from core import usermod  # noqa: E402
from screens.audience import auvideo, aumood  # noqa: E402

#: JPEG quality 2 (1 best .. 31): grain-free enough for a 4K stage
JPEG_Q = "2"

#: Where the loop looks, in pixels of the 1916 x 1080 films the generator
#: makes (the room is the same in every film): the columns the green light
#: stands in, the last row of it above the ambassador's head, and the box
#: the helix stands in.
LIGHT_X, LIGHT_BOTTOM = (780, 1150), 232
HELIX_BOX = (830, 690, 1075, 990)
#: A helix pixel is a white one; a dim film (the hologram look) needs a
#: lower floor: the environment's `HELIX_WHITE` (the Silicoid: 170).
HELIX_WHITE = int(os.environ.get("HELIX_WHITE", 190))
#: How far the light's mask grows, how far the helix's glow reaches, and
#: how soft the mask's edge is.
LIGHT_GROW, HELIX_GLOW, MASK_BLUR = 8, 22, 8


def _fps(film):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", film],
        capture_output=True, text=True, timeout=60).stdout.strip()
    num, _, den = out.partition("/")
    return float(num) / float(den or 1)


def loop_mask(frames):
    """The loop's mask over `frames` (H x W x 3 uint8 arrays): the green
    light of any frame (grown, closed) and the helix's white strands (grown
    by their glow), as a bool array of the film's size."""
    import numpy as np
    from scipy import ndimage as ndi
    h, w = frames[0].shape[:2]
    light = np.zeros((h, w), bool)
    helix = np.zeros((h, w), bool)
    hx0, hy0, hx1, hy1 = HELIX_BOX
    for f in frames:
        a = f.astype(int)
        # the light is GREEN (not the teal of a nebula sky, which changes
        # from frame to frame) and stands near the dome's apex; the
        # ambassador's white horns start below LIGHT_BOTTOM
        g = a[:LIGHT_BOTTOM]
        lit = (g[..., 1] > g[..., 0] + 15) & (g[..., 1] > g[..., 2] + 25) & \
            (g[..., 1] > 60)
        lit[:, :LIGHT_X[0]] = False
        lit[:, LIGHT_X[1]:] = False
        light[:LIGHT_BOTTOM] |= lit
        # the helix: its white strands inside the box (the robes above and
        # the pillar beside are not white enough)
        helix[hy0:hy1, hx0:hx1] |= \
            a[hy0:hy1, hx0:hx1].min(axis=2) > HELIX_WHITE
    light = ndi.binary_closing(ndi.binary_opening(light, iterations=1),
                               iterations=14)
    mask = ndi.binary_dilation(light, iterations=LIGHT_GROW) | \
        ndi.binary_dilation(helix, iterations=HELIX_GLOW)
    return ndi.binary_closing(mask, iterations=10)


def cut_lights(out, fps, seconds=2.0):
    """Cut the light and the helix from the LAST `seconds` of the frames in
    `out` into `out/glow/`: RGBA PNGs of the rectangle round the mask
    (`loop_mask`), each frame as it is (the room stands, so nothing is
    aligned), alpha = ONE soft mask for all frames, so the held frame's own
    light and helix are covered whatever they do. Returns the `glow` entry
    of clip.json."""
    import numpy as np
    from PIL import Image
    from scipy import ndimage as ndi
    names = sorted(n for n in os.listdir(out) if n.endswith(".jpg"))
    names = names[-max(2, round(seconds * fps)):]
    frames = [np.asarray(Image.open(os.path.join(out, n)).convert("RGB"))
              for n in names]
    h, w = frames[0].shape[:2]
    mask = loop_mask(frames)
    if not mask.any():
        raise SystemExit("no light or helix found in the film's last "
                         f"{seconds} s: nothing to loop")
    ys, xs = np.nonzero(mask)
    pad = 3 * MASK_BLUR
    x0, x1 = max(0, xs.min() - pad), min(w, xs.max() + pad + 1)
    y0, y1 = max(0, ys.min() - pad), min(h, ys.max() + pad + 1)
    alpha = ndi.gaussian_filter(mask.astype(np.float32), MASK_BLUR)
    alpha = (np.clip(alpha * 1.2, 0, 1) * 255).astype(np.uint8)[y0:y1, x0:x1]
    gdir = os.path.join(out, "glow")
    os.makedirs(gdir)
    for n, f in enumerate(frames):
        Image.fromarray(np.dstack([f[y0:y1, x0:x1], alpha]), "RGBA").save(
            os.path.join(gdir, "%04d.png" % (n + 1)))
    return {"rect": [int(x0), int(y0), int(x1 - x0), int(y1 - y0)],
            "fps": fps, "pingpong": True}


def _has_audio(film):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
         "stream=codec_type", "-of", "csv=p=0", film],
        capture_output=True, text=True, timeout=60).stdout.strip()
    return bool(out)


def install(race, folder, lights=None):
    """Convert the films of `folder` for `race`; `lights` is the loop's
    length in seconds or None. A clip is built in a folder of its own and
    put in place only when it is whole, so a failed install leaves the
    clip that was there."""
    if race not in auvideo.RACES:
        raise SystemExit(f"unknown race {race!r}: {auvideo.RACES}")
    done = []
    for mood in aumood.CLIPS:
        film = os.path.join(folder, mood + ".mp4")
        if not os.path.isfile(film):
            continue
        out = os.path.join(usermod.mod_dir(), usermod.FILES,
                           *auvideo.REL.split("/"), race, mood)
        work = out + ".new"
        shutil.rmtree(work, ignore_errors=True)
        os.makedirs(work)
        try:
            ffrun.run(["-v", "error", "-y", "-i", film, "-an", "-q:v",
                       JPEG_Q, os.path.join(work, "%04d.jpg")], seconds=300,
                      max_bytes=2 * 1024 ** 3, check=True)
            if _has_audio(film):         # a silent film is a clip too
                ffrun.run(["-v", "error", "-y", "-i", film, "-vn", "-c:a",
                           "libvorbis", "-q:a", "5",
                           os.path.join(work, "audio.ogg")], seconds=120,
                          max_bytes=256 * 1024 ** 2, check=True)
            meta = {"fps": _fps(film)}
            if lights:
                meta["glow"] = cut_lights(work, meta["fps"], lights)
            with open(os.path.join(work, "clip.json"), "w",
                      encoding="utf-8") as fh:
                json.dump(meta, fh)
        except BaseException:
            shutil.rmtree(work, ignore_errors=True)
            raise
        shutil.rmtree(out, ignore_errors=True)
        os.rename(work, out)
        done.append(mood)
        frames = len([n for n in os.listdir(out) if n.endswith(".jpg")])
        loop = f" + loop {meta['glow']['rect']}" if lights else ""
        print(f"{race}/{mood}: {frames} frames{loop} -> {out}")
    if not done:
        raise SystemExit(f"no <mood>.mp4 in {folder}")


if __name__ == "__main__":
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    loop = None
    for flag in flags:
        if flag.partition("=")[0] != "--lights":
            raise SystemExit(__doc__)
        loop = float(flag.partition("=")[2] or 2.0)
    if len(args) != 2:
        raise SystemExit(__doc__)
    install(args[0].lower(), args[1], loop)
