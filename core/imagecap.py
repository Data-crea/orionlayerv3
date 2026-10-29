"""A picture from a mod folder is read by its header first (audit TD-09).

The mod folder is drop-in data other players share. A 20000x20000 PNG decodes
to about 1.6 GB, and PIL's `DecompressionBombError` is not an `OSError` or a
`ValueError`, so the handlers around the loads let it through into the frame
guard. `header_size` reads the size without decoding and says no, as a
`ValueError` the callers already catch, to anything past `MAX_PIXELS`
(8000 x 8000; the biggest picture the project itself uses is the frame at
3840 x 2160, 8.3 million).
"""
MAX_PIXELS = 64_000_000


def header_size(path):
    """(width, height) of the picture at `path`, from its header.

    Raises ValueError when the file cannot be read as a picture or is bigger
    than MAX_PIXELS. Returns None when PIL is not installed (nothing to
    check with; the callers then load as before)."""
    try:
        from PIL import Image
    except ImportError:
        return None
    try:
        with Image.open(path) as img:
            size = img.size
    except (OSError, ValueError, Image.DecompressionBombError) as err:
        raise ValueError(f"cannot be read as a picture ({err})") from None
    if size[0] * size[1] > MAX_PIXELS:
        raise ValueError(f"{size[0]}x{size[1]} is more than {MAX_PIXELS} "
                         f"pixels")
    return size
