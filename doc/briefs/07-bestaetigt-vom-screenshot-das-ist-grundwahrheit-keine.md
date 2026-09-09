Bestätigt vom Screenshot, das ist Grundwahrheit, keine
Interpretation: die beiden abgesetzten Symbole in Sol II stehen in
der Spalte FARMERS. Sol II ist die einzige Zeile mit Inhalt in
dieser Spalte; alle sechs anderen zeigen ausschließlich Arbeiter.
Deine Lesart trifft zu, der Farbunterschied ist der Beruf.

Meine Aussage "Sol II hat sichtbar zwei Rassen" war falsch — ich
habe einen Farbunterschied gesehen und als Rassenmischung gelesen.
Streich sie überall, wo sie in die Doku gewandert ist, und notier
sie als das, was sie war: eine Ablesung, die eine Vermutung
enthielt. Prüfung 4 hat nichts widerlegt, sie hatte nie eine
Grundlage.

Damit:

1. COLONY promoten wie vorgeschlagen — owner, planet, n_pops,
   max_farms belegt, die Pop-Masken als eigene, noch offene
   Behauptung markiert. MASK_PROFESSION trägt jetzt zwei
   unabhängige Belege: 3/3 im Decode und die Spaltenzuordnung auf
   dem Schirm. MASK_RACE bleibt offen, mit dem, was es schliesst:
   eine Kolonie mit Androiden, Ureinwohnern oder eroberter
   Bevölkerung. Kein Zug später, sondern ein anderer Spielstand.
   Beleg in den Docstring: Datum, Spielstand 85 Züge, welche
   Kolonie welchen Wert bestätigt hat.

2. Punkt 6 gehört ins Fundament, nicht nur in die Structdoku. Die
   angezeigte Bevölkerungsgrenze ist
   Planet_Max_Population_For_Player_ (colcalc.cpp:896) und geht
   über Klima, Immunität und Advanced City Planning;
   _planet_max_population[size] ist nur die Basis. Trag es in
   Abschnitt 3 unter den orion2re-Fakten ein, mit der Konsequenz:
   die HD-Balkenlänge bildet diese Funktion nach, nie die Tabelle
   allein. Zahlenbeispiel dazu, es macht den Fehler greifbar —
   Ixion II, Small Ocean, Tabelle sagt 10, Spiel zeigt 5.
   Prüf beim Schreiben, ob dazu auch eine Smoke-Regel möglich ist,
   die nicht bloss die Formel wiederholt.

3. star.py:56 begründet planet_indices() mit "the Spec format has
   no array kind". Seit deinem u32[42] stimmt das nicht mehr.
   Korrigier nur den Kommentar auf den echten Grund — die Funktion
   bleibt, sie ist bequemer als ein rohes Array. Ein verifizierter
   Spec, also Offsets und verified=True unangetastet.

4. v3_projektstatus.md nachziehen: Struct-Verifikation, der
   Colony-Summary-Abschnitt, und dass die Liste jetzt nicht mehr
   an s_colony hängt.

Danach pushen.