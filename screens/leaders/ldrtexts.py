"""The Leaders screen's own words, by a stable key — work order 237,
decision 73 (`core/modtexts`): replaceable from the player's mod folder
(`texts/leaders/<rest>.txt`), German through `assets/shared/lang/de.json`
like every word of OrionLayer's own.

The caption of a row with no leader (`ldrdraw.draw_empty`), over the
empty-slot picture. INVENTION: the original draws nothing in an empty row
(officer.cpp:1975-1991 prints only the listed leaders); the words are the
mockup's (Data, 11 October 2026), the colony tab's title chosen to fit a
colony leader. The wording is Data's (238 P1, decided for work order
239): in German "Kein Anführer" on COLONY LEADERS, "Kein Offizier" on SHIP
OFFICERS, the second line "Anführer aus dem Pool zuweisen." on both.
"""
TEXTS = {
    "leaders.empty.colony.title": ("No Leader Assigned", "own"),
    "leaders.empty.colony.hint": ("Assign a leader from the pool.", "own"),
    "leaders.empty.ship.title": ("No Officer Assigned", "own"),
    "leaders.empty.ship.hint": ("Assign a leader from the pool.", "own"),
}
