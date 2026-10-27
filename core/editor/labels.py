"""The names the editor shows for a box.

`screens/<screen>/box_labels.json` holds, for every box of the screen,
`{"title": ..., "about": ...}` — what a person calls it and one sentence
on what is drawn or hit there. The file is the screen's own (a mod may
replace it like any JSON file); a smoke check holds it to the box list
in both directions, so a box added without a label fails the suite.
"""
import json
import logging
import os

log = logging.getLogger("editor.labels")

FILE = "box_labels.json"
_cache = {}


def load(screen_dir):
    """`{box name: {"title", "about"}}` for a screen folder; {} when the
    file is missing or damaged (the panel then falls back to the name)."""
    path = os.path.join(screen_dir, FILE) if screen_dir else ""
    if path not in _cache:
        data = {}
        try:
            with open(path, encoding="utf-8") as handle:
                raw = json.load(handle)
            if isinstance(raw, dict):
                data = {k: v for k, v in raw.items() if isinstance(v, dict)}
        except (OSError, ValueError) as err:
            if path:
                log.info("no box labels at %s (%s)", path, err)
        _cache[path] = data
    return _cache[path]


def title(labels, name):
    """The box's title, or its name made readable when it has none."""
    t = (labels.get(name) or {}).get("title")
    return t if t else name.replace("_", " ").title()


def about(labels, name):
    return (labels.get(name) or {}).get("about", "")
