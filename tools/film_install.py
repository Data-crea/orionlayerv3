"""Put a restored film's frames into the mod folder — work order 386.

    python tools/film_install.py <film> <source> [--crop WxH] [--fps N]

`<film>` is the film's file name without its extension (`genwinfn`,
`wininfin`, `anwinfin`, `loserfin`, `orionfin`, `dimtvfin`, `plntdfin`,
`amebafin`, `anatkfin`: `core.filmblock.FILMS`). `<source>` is a video, or
a folder of PNG/JPEG frames in name order (the lossless way: no second
lossy step). The result is
`<mod folder>/files/assets/shared/films/<film>/NNNN.jpg` and `clip.json`,
which `core.filmhd` reads with pygame alone (HD EXTENSION `film_restored`).

`--crop WxH` cuts the picture out of a video that carries black bars (a
3840 x 2160 canvas holding a 3840 x 1280 film: `--crop 3840x1280`), centred.
`--fps` is the clip's rate for `clip.json` (display only; the engine's frame
number picks the frame); a video gives its own.

The source is read, never changed. Every ffmpeg runs through `ffrun`.
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
from core import filmblock, filmhd, usermod  # noqa: E402

#: JPEG quality (1 best .. 31): grain-free enough for a 4K picture.
JPEG_Q = "3"
#: The game's own rate (25000/1923, `ffprobe` of every film), when a folder
#: of frames says none.
GAME_FPS = 25000 / 1923


def _fps(video):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", video],
        capture_output=True, text=True, timeout=60).stdout.strip()
    num, _, den = out.partition("/")
    return float(num) / float(den or 1)


def _args(argv):
    opts = {"crop": None, "fps": None}
    rest = []
    it = iter(argv)
    for a in it:
        if a in ("--crop", "--fps"):
            opts[a[2:]] = next(it, None)
        elif a.startswith("--crop=") or a.startswith("--fps="):
            opts[a[2:a.index("=")]] = a.split("=", 1)[1]
        else:
            rest.append(a)
    return rest, opts


def main(argv):
    rest, opts = _args(argv)
    if len(rest) != 2:
        raise SystemExit(__doc__)
    film, source = filmhd.stem(rest[0]), rest[1]
    known = {filmhd.stem(n) for n in filmblock.FILMS}
    if film not in known:
        raise SystemExit(f"unknown film {film!r}; one of "
                         f"{', '.join(sorted(known))}")
    out = os.path.join(usermod.mod_dir(), usermod.FILES,
                       *filmhd.REL.split("/"), film)
    work = out + ".new"
    vf = []
    if opts["crop"]:           # read BEFORE anything is made on disk
        try:
            w, _, h = opts["crop"].partition("x")
            vf = ["-vf", f"crop={int(w)}:{int(h)}"]
        except ValueError:
            raise SystemExit("--crop takes WxH, e.g. 3840x1280")
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)
    try:
        if os.path.isdir(source):
            names = [n for n in sorted(os.listdir(source))
                     if n.lower().endswith((".png", ".jpg", ".jpeg"))]
            if not names:
                raise SystemExit(f"no frames in {source}")
            if not os.path.splitext(names[0])[0].isdigit():
                raise SystemExit("frames must be numbered (00001.png ..)")
            ext = os.path.splitext(names[0])[1]
            # a numbered run (00001.png ..): ffmpeg's own pattern
            first = os.path.splitext(names[0])[0]
            pattern = os.path.join(source, f"%0{len(first)}d{ext}")
            args = ["-v", "error", "-y", "-start_number", str(int(first)),
                    "-i", pattern, *vf]
            fps = float(opts["fps"] or GAME_FPS)
        else:
            args = ["-v", "error", "-y", "-i", source, "-an", *vf]
            fps = float(opts["fps"] or _fps(source))
        ffrun.run([*args, "-q:v", JPEG_Q, os.path.join(work, "%04d.jpg")],
                  seconds=900, max_bytes=4 * 1024 ** 3, check=True)
        with open(os.path.join(work, "clip.json"), "w",
                  encoding="utf-8") as fh:
            json.dump({"fps": fps}, fh)
    except BaseException:
        shutil.rmtree(work, ignore_errors=True)
        raise
    count = len([n for n in os.listdir(work) if n.endswith(".jpg")])
    if count == 0:    # never swap a good clip for an empty one
        shutil.rmtree(work, ignore_errors=True)
        raise SystemExit("no frame was written; the installed clip is kept")
    shutil.rmtree(out, ignore_errors=True)
    os.rename(work, out)
    print(f"{film}: {count} frames -> {out}")


if __name__ == "__main__":
    main(sys.argv[1:])
