Wichtige Korrektur der Ausgangslage: der Snapshot stammt NICHT aus
einem Savegame. Stardate 3500.0, frisch generierte Galaxie, vor dem
ersten Zug. Das war mir beim Auftrag nicht bekannt und dir nicht.

Folgen:

1. Der max_farms/max_population-Befund ist damit nicht entschieden.
   Deine beiden Hypothesen bleiben, aber es gibt eine dritte, die
   zuerst geprüft gehört: das Feld wird in der Zugverarbeitung
   geschrieben und ist vor Zug 1 schlicht noch nicht berechnet.
   Kein Urteil über orion2.h, solange die nicht ausgeschlossen ist.
   ericnet.cpp:162 ist dann nur eine von mehreren Schreibstellen —
   grep nach allen Zuweisungen an max_farms und max_population, und
   sieh nach, ob eine davon im Zug-Pass liegt.

2. Verdacht, den die Daten selbst nahelegen und den keine der
   Invarianten fangen kann: die Zuordnung der Profession-Werte
   könnte vertauscht sein. Kolonie 0 zeigt 2F/2W/4S bei 8 Pops; eine
   MOO2-Heimatwelt startet nach Angabe des Maintainers mit 4F/2W/2S.
   Über alle Kolonien 232 Forscher gegen 116 Farmer, was für einen
   Spielstart unplausibel ist. Summe == n_pops und Wertebereich 0..2
   halten unter jeder Permutation der drei Berufe — die Invarianten
   sind also kein Beleg für die Zuordnung, nur für die Bitlage.
   Such die Stelle im C++, die einen Profession-Wert auf eine
   Spalte, ein Sprite oder eine Beschriftung abbildet
   (coldraw.cpp, colsum.cpp, colmove.cpp), und leite die Zuordnung
   daraus ab statt aus der Reihenfolge in pop.h.
   Falls sie vertauscht ist: das ist der wichtigste Befund des
   Durchlaufs und geht allem anderen vor.

3. Der bisherige Lauf ist nicht wertlos, aber er ist keine
   Verifikation. Er prüft die Bitlage, nicht die Bedeutung. Trag das
   so in doc/s_colony_offsets.md ein — mit Stardate und dem Zustand
   "vor dem ersten Zug" als Provenienz der Messung, im selben Geist
   wie der Commit-Hash bei Phase A. Eine Messung ohne den Zustand,
   in dem gemessen wurde, ist die Messung an einem unbekannten Baum
   nochmal.

4. Die vier geänderten Dateien darfst du committen — Spec-Arrays,
   --spec im Probe, COLONY mit verified=False, die drei
   Smoke-Regeln. Alles davon steht unabhängig vom Zeitpunkt, und
   verified=False sagt bereits das Richtige. Die Commit-Message
   nennt den Zustand des Snapshots und den offenen
   Profession-Verdacht. Weiterhin nichts promoten, kein colony.py.

Die Grundwahrheit kommt aus einem echten Savegame mit gespielten
Zügen, nicht aus dem Startzustand. Der Probe wird dort wiederholt.