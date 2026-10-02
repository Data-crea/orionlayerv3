"""The LANGUAGE row of Game Settings' OrionLayer rows — HD EXTENSION
`language_switch`, work order 200 C (`core/lang.py`).

English or German, stored in the player's settings and read at the next
start (the heading's restart note says so while the choice differs from the
language in force, `gmorion.restart_pending`). Choosing German starts the
extraction of the player's German game files in the background
(`core/langsetup`); the row shows its progress. Each language is named in
its own words (English, Deutsch), as language switches do.
"""
from core import lang, langsetup, palette

COL_OPTION = palette.require("game_menu", "option_text")
COL_STATE = palette.require("game_menu", "hd_state")


def cycle(settings):
    now = settings.get("language") or lang.current()
    i = lang.LANGUAGES.index(now) if now in lang.LANGUAGES else -1
    settings.set("language", lang.LANGUAGES[(i + 1) % len(lang.LANGUAGES)])
    langsetup.start(settings.get("language"))


def render(screen, surface, row, words, size, lx, vx, text, chosen):
    """`text(string, size, colour, x, rect)` is gmorion's drawing."""
    text(words.get("language", "Language"), size, COL_OPTION, lx, row)
    chosen = chosen or lang.current()
    img = text(words.get("language_steps", {}).get(chosen, chosen), size,
               COL_OPTION, row.x + vx, row)
    job = langsetup.state()
    if job["phase"] == "running":
        note = words.get("language_wait", "Reading game files "
                         "({i}/{n})").format(i=job["i"], n=job["n"])
    elif job["phase"] == "done":
        note = words.get("language_done", "{made} game file(s) "
                         "found").format(made=job["made"])
    else:
        return
    # the note fits the dialog in every language (the row is new, work
    # order 200 C: the German note ran 280 px past the dialog)
    text(note, size, COL_STATE, row.x + vx + img.get_width()
         + int(row.h * 0.6), row, fit=True)
