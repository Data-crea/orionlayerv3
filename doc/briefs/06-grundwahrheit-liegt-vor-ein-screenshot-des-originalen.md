Grundwahrheit liegt vor: ein Screenshot des originalen
Colony-Summary-Schirms, Spielstand 85 Züge, derselbe Zustand wie
dein letzter Lauf. Ich habe die Bevölkerungssymbole NICHT gezählt —
diese Zahlen sind unten bewusst nicht enthalten. Prüf gegen das,
was diskret ablesbar ist.

Vom Schirm, sortiert nach Name:
  Ixion II · Kif II · Malus I · Sol I · Sol II · Sol III · Sol IV
Sieben Kolonien des lokalen Spielers. Dein Snapshot hat 21 — der
Rest gehört anderen Spielern.

"No Farming" steht bei: Kif II, Malus I, Sol III, Sol IV.
Nicht bei: Ixion II, Sol I, Sol II.
Ixion II und Sol I zeigen eine leere Farmer-Spalte ohne Text, Sol II
zwei Farmer-Symbole.

Sol II ist die einzige Kolonie mit sichtbar zwei Rassen: die beiden
Farmer sind farblich von den Arbeitern abgesetzt.

Empire-Sidebar: Reserve 103, Income +1, Population 39,
Freighters 13, Food -1, Research 44.

Planetensteckbrief des ausgewählten Planeten (Ixion II, laut
Karteneinsatz "Ixion"): Small Ocean, Normal Gravity,
Mineral Abundant, Population (3/5).

Prüfe damit:

1. owner — genau sieben Kolonien tragen die Spielernummer des
   lokalen Spielers, und deren Sternnamen sind die sieben oben.
   Der Weg dahin ist colony -> planet -> star -> name; die
   Kolonie selbst trägt keinen Namen. Die Zeilenreihenfolge auf
   dem Schirm ist nach Name sortiert, nicht Arrayreihenfolge —
   ordne über den Namen zu, nie über den Index.

2. max_farms — bei Kif II, Malus I, Sol III, Sol IV muss 0 stehen,
   bei Ixion II, Sol I, Sol II 255. Sieben von sieben oder es
   stimmt etwas nicht. Das ist der Schiedsrichter, auf den du
   gewartet hast.

3. Summe der n_pops über diese sieben Kolonien == 39, der
   Population-Wert der Sidebar aus s_player. Zwei unabhängige
   Felder in zwei Structs, die übereinstimmen müssen. Weicht es ab,
   ist das ein Befund, kein Rundungsfehler.

4. MASK_RACE — Sol II muss genau zwei verschiedene Rassenwerte im
   pop[] tragen, alle übrigen sechs Kolonien genau einen. Sind die
   beiden abweichenden Pops in Sol II zugleich die mit Beruf 0
   (Farmer), stützt das MASK_PROFESSION zusätzlich.

5. planet.py, alle vier Enum-Richtungen an einem Datensatz: der
   Planet mit n_pops 3, dessen Kolonie Ixion II heißt, muss
   size=Small, climate=Ocean, gravity_class=Normal,
   mineral_class=Abundant decodieren. Trag pro Feld ein, dass die
   Richtung jetzt live gesehen wurde, mit Datum und Planet.

6. Offener Widerspruch, vor Punkt 5 zu klären: du hast berichtet,
   die Bevölkerungsgrenze komme aus
   MOX::_planet_max_population[] = {5,10,15,20,25}, indiziert nach
   Größe mit Tiny=0..Huge=4. Der Schirm zeigt für ein SMALL
   Ocean-Planeten "Population (3/5)". Index 1 wäre 10, nicht 5.
   Klär, was die angezeigte Grenze tatsächlich berechnet — grep
   die Stelle, die den Steckbrief unten links zeichnet — und ob
   Klima oder Gravitation eingehen. Das ist nicht nebensächlich:
   das Balken-Design der HD-Liste macht die Balkenlänge
   proportional zur Maximalbevölkerung, also hängt eine
   Kernentscheidung des Screens an dieser Zahl.
   Falls die Größen-Aufzählung dabei umgekehrt herauskommt, ist das
   der schwerste Befund und geht Punkt 5 vor.

Erst wenn 1 bis 5 halten: COLONY nach core/structs/colony.py mit
verified=True, Beleg im Docstring (Datum, Spielstand, welche
Kolonien welche Werte bestätigt haben), Eintrag in der
"Already promoted"-Liste, und der Abschnitt "second source still
missing" in doc/s_colony_offsets.md wird durch das Ergebnis
ersetzt. Weicht eines ab: nichts promoten, melden.

Der zweite Datenpunkt (dieselbe Kolonie einen Zug später) fehlt
noch. Sag beim Bericht, ob du ihn nach 1 bis 5 überhaupt noch
brauchst, oder ob "No Farming" und die Rassenmischung als zweite
Quelle tragen.