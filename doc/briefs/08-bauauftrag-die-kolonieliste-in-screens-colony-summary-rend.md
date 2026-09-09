Bauauftrag: die Kolonieliste in screens/colony_summary/ rendern.
Erster sichtbarer Schritt. Statisch — kein Hover-Band, keine
ziehbaren Trenner, keine Klick-Injektion. Die kommen danach, auf
einer Darstellung, der man schon glaubt.

Lies doc/v3_fundament.md vollständig. Das hier fasst einen Screen,
Boxen, Layout-JSON und einen Renderer an, also die lange Runde. Der
Design-Entwurf steht in v3_projektstatus.md im Colony-Summary-
Abschnitt; er ist die Vorgabe, nicht eine Anregung.

Daten, alle vorhanden:
- core/structs/colony.py — owner, planet, n_pops, max_farms
  belegt; pop_prof() belegt; pop_race() offen, siehe unten.
- core/structs/planet.py für size/climate, star.py für den Namen.
  Der Name geht Kolonie -> Planet -> Stern; die römische Ziffer
  kommt aus HAROLD::Planet_Number_, also belegte Slots zählen,
  nicht Orbit. Du hast die Regel im letzten Lauf hergeleitet.
- Balkenlänge: Planet_Max_Population_For_Player_ nachbilden
  (colcalc.cpp:896), niemals _planet_max_population[size] allein.
  Steht mit Formel im Fundament, Abschnitt 3.

Zu bauen:
1. Nur die Kolonien des lokalen Spielers, sortiert wie die
   Sortiertaste sagt; _sort_key existiert schon und wird bisher
   nur angezeigt. Anfangs reicht "name".
2. Pro Zeile: Name, dann ein Balken aus einem Quadrat je Pop, drei
   Farbzonen nach pop_prof. Balkenlänge proportional zur
   Maximalbevölkerung, damit ein Quadrat in jeder Zeile gleich
   gross ist und Quadrate zählen heisst Pops zählen.
3. "No Farming" statt der Farmzone, wenn max_farms == 0 — der
   Originalschirm zeigt genau das, in vier von sieben Zeilen.
4. Alles Sichtbare durch F5-Boxen und layout.json, nichts als
   Konstante im Renderer. Wortlaut nach layout.json.
5. Der Balken ist eine INVENTION — das Original zeichnet drei
   Sprite-Spalten. Markieren in screen.py, in layout.json, im
   Projektstatus und in einer Smoke-Regel, die anschlägt, wenn die
   Markierung verschwindet.

Grenzen:
- pop_race() hat keine zweite Quelle. Die Rassengruppen des
  Entwurfs (Schattierungen, Androiden und Ureinwohner als
  gesperrt) bleiben deshalb DRAUSSEN. Bau die Zonen so, dass sie
  später dazukommen können, aber zeichne heute nichts, was von
  einer unbelegten Maske abhängt.
- screen.py hat 258 Zeilen und die Grenze liegt bei ~300. Die
  Liste gehört in ein eigenes Modul im selben Ordner, nicht ans
  Ende von screen.py.
- Nichts injizieren. Der Screen bleibt lesend.

Verifikation, und das ist der Punkt: der Maintainer hat einen
Screenshot des Originalschirms zu genau diesem Spielstand
(85 Züge, Stardate 3508.5). Sieben Zeilen — Ixion II, Kif II,
Malus I, Sol I, Sol II, Sol III, Sol IV — "No Farming" bei Kif II,
Malus I, Sol III, Sol IV; Sol II als einzige mit Farmern und
Wissenschaftlern, alle übrigen reine Arbeiterkolonien; Summe 39.
Render die HD-Liste gegen denselben Zustand und vergleiche Zeile
für Zeile. Namen, Reihenfolge, welche Zeile "No Farming" trägt,
Pops je Zeile und je Beruf. Berichte die Gegenüberstellung als
Tabelle, auch wo sie stimmt.

Smoke-Test: die Zahl darf nicht sinken, neue Regeln prüfen die
Regel statt der Instanz — z.B. dass Zeilen ohne Farmzone genau die
mit max_farms == 0 sind, und dass die Balkenlänge nie über die
Maximalbevölkerung hinausgeht.

Alle Aussagen hier über orion2re stammen aus dem Fundament und aus
deinen eigenen Berichten, nicht aus der Quelle. Prüf sie.