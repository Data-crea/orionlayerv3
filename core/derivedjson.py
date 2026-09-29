"""The head every versioned derived-file loader shares — audit D1.

The files the extractors write from the player's own MOO2 installation
(building, ship-part and research names, BILLTEXT, ESTRINGS, HESTRNGS,
MAINTEXT, SKILDESC) are each read by a loader of the same shape: the
file may be absent (the player has not run the extractor — said once,
at info), unreadable (a warning), or written by an older extractor
(`format` below the loader's `FORMAT_VERSION`: the state is "stale" and
the warning names the command). Only what each does with the data after
that differs. Until work order 190 that head stood in eight modules,
copied (`dev:doc/redundancy_audit.md`, D1); this is its
one home, and each loader keeps its own tail.

**IT READS THE FILE WHERE THE LOADER POINTS IT, and not through
`core/resources.py`** — exactly what the eight copies did (decision 16):
moving the head must not change which file a modded install reads.

The words of every log line are the caller's, passed in, so a loader
logs what it logged before, letter for letter.
"""
import json
import os


def load(path, log, label, how, rerun, format_version):
    """`(data, stale)` for the versioned JSON file at `path`.

    `(None, False)` when it is absent (info: "`label`: path absent — run
    `how`") or will not load (warning); `(None, True)` when its format is
    older than `format_version` (warning: "… — re-run `rerun`"); otherwise
    `(data, False)` with the parsed dict.
    """
    if not os.path.exists(path):
        log.info(f"{label}: %s absent — run `{how}`", path)
        return None, False
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except (ValueError, OSError) as err:
        log.warning(f"{label}: %s will not load (%s)", path, err)
        return None, False
    if int(data.get("format", 0)) < format_version:
        log.warning(f"{label}: %s is format %s, this build reads %s — "
                    f"re-run {rerun}", path, data.get("format"),
                    format_version)
        return None, True
    return data, False
