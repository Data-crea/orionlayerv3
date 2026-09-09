Vier Nachträge am Colony Summary, alle klein, ein Commit reicht.

1. Die Wörter tragen ihr Vorwort nicht, das Label trägt es.
Die Quelle entscheidet das feiner als „unsere Liste ist falsch". colland.cpp:59-61 steckt den Mineralwert in ein eigenes Format, E_Strings_(0x176) — das Wort „Mineral" gehört zum Format, nicht zum Tabellenwert. Die Tabelle führt „Rich". Die Gravitation daneben wird bei colland.cpp:65 ohne jedes Format gedruckt, dort steht der volle String „Normal Gravity" in der Tabelle.
Für ein Panel mit Labels heißt das: „Mineral Rich" wäre falsch, das ergäbe MINERALS Mineral Rich. Unsere Ablesung „Rich" stimmt. Bei der Gravitation ist die Liste tatsächlich falsch, aber die wörtliche Korrektur ergäbe GRAVITY Normal Gravity — dasselbe Problem. Also: Werte ohne ihr Vorwort, das Label trägt es, und das gehört als Regel in die Herkunftsnotiz statt als drei Einzelentscheidungen. Die Gravitationswerte entsprechend prüfen und angleichen.

2. Growth mit Vorzeichen und k.
Das k ist keine Beschriftung, sondern eine Einheit — MOO2 zählt Bevölkerung in Tausend. +63k, nicht 63.

3. Die zehnte Zeile.
Das Fenster des Originals fasst zehn (_list_col[10]), wir zeichnen neun auf 1920×1080. Die ehrliche Beschriftung war der richtige erste Schritt, der Zustand ist es nicht. row_height senken ist der billigere der zwei Wege — list_area zu verlängern hinge am Rahmenbild. Bei 62 px sollte Luft sein.

4. Sortierung setzen statt abfragen.
_g_sort_index steht nicht im Snapshot, und dafür wird orion2re nicht angefasst. Stattdessen injiziert HD beim Betreten des Schirms einmal seinen eigenen Schlüssel; danach sind beide Seiten per Konstruktion gleich, weil jede weitere Änderung ohnehin durch HD läuft. Ein Zustand, den man selbst herstellt, muss nicht gelesen werden — dieselbe Strategie wie beim Scrollfenster.

Zum Notieren, nicht zu ändern: die Metallkante des Rahmens ragt drei bis vier Pixel in list_area (die 310 Pixel bei x 0..3 und 1405..1407). Heute harmlos, aber frame_holes.py leitet die Box aus dem Bild ab, und jemand wird sich später fragen, warum die nutzbare Breite nicht die Boxbreite ist.

Danach: --live --native erneut, dann fallen pop_growth und morale.