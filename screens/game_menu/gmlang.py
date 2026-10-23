"""The LANGUAGE row of the OrionLayer settings — HD EXTENSION
`language_switch`, work order 200 C (`core/lang.py`).

English or German, stored in the player's settings and read at the next
start (the heading's restart note says so while the choice differs from the
language in force, `gmorion.restart_pending`). Choosing German starts the
extraction of the player's German game files in the background
(`core/langsetup`); the row shows its progress. Each language is named in
its own words (English, Deutsch), as language switches do.
"""
from core import langsetup, palette

COL_OPTION = palette.require("game_menu", "option_text")
COL_STATE = palette.require("game_menu", "hd_state")


def render_note(screen, surface, geo, words, size):
    """The reading's progress right of the language field, while it runs
    and when it is done (the choice itself is the row's drop-down list,
    `oldrop`, since work order 251)."""
    from . import gmorion
    row, field = geo["language"], geo["language_field"]
    job = langsetup.state()
    if job["phase"] == "running":
        note = words.get("language_wait", "Reading game files "
                         "({i}/{n})").format(i=job["i"], n=job["n"])
    elif job["phase"] == "done" and job["error"]:
        # a job that could not plan, stopped or had a step raise is said
        # as a failure, not as a count (work order 326 H1)
        note = words.get("language_failed", "Failed — see the log "
                         "({made} file(s) found)").format(made=job["made"])
    elif job["phase"] == "done":
        note = words.get("language_done", "{made} game file(s) "
                         "found").format(made=job["made"])
    else:
        return
    x = field.right + int(row.h * 0.4)
    gmorion._text(screen, surface, note, size, COL_STATE, x, row,
                  row.right - x, fit=True)
