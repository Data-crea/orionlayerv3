Der Zustandswechsel ist erklärt: der Maintainer hat mitten in
deinem Lauf ein 50 Runden altes Savegame geladen. Andere Galaxie,
kein Rätsel. Trag es als Provenienz nach, dann steht in der Doku
warum, nicht nur dass.

Zwei Prüfungen, beide ohne Grundwahrheit, beide vor dem
Savegame-Durchlauf:

1. max_population im GELADENEN Spielstand. Deine Schreibmenge sagt:
   nur savegame.cpp:322 und ericnet.cpp:443, also nur beim Laden.
   Wir sind jetzt in einem geladenen Spielstand. Steht das Feld
   dort immer noch bei allen 21 Kolonien auf 0, widerlegt das die
   eigene Erklärung, und der wahrscheinlichste Grund ist dann, dass
   orion2.h diesen Offset falsch benennt. Lies es explizit im
   aktuellen Zustand aus und berichte den Wert je Kolonie, nicht
   nur "unverändert".
   Ergibt sich ein Widerspruch: nachsehen, was savegame.cpp:322
   tatsächlich beschreibt, und ob der Ladepfad in orion2re
   überhaupt durchlaufen wird.

2. planet.colony_index. 132 Planeten tragen einen Wert >= 0 bei 21
   Kolonien, mehrere teilen sich denselben. Der Docstring von
   core/structs/planet.py sagt "-1 when the planet is uncolonised"
   und legt damit nahe, ein nichtnegativer Wert benenne die eigene
   Kolonie. Das trägt die Daten nicht. Such die Schreibstellen im
   C++ und klär, was der Wert auf einem unbesiedelten Planeten
   bedeutet.
   Der Spec steht auf verified=True, wird ausserhalb der
   Struct-Module aber nur in smoke_test.py:1840 gelesen — kein
   Produktionspfad hängt daran, es eilt also nicht. Es ist aber
   eine unbelegte Bedeutungsangabe in einem verifizierten Spec,
   also genau der Fall, den Entscheidung 23 seit gestern benennt.
   Korrigier den Docstring auf das, was belegt ist, und markier den
   Rest als offen. Die Offsets bleiben unangetastet, verified=True
   bleibt — es geht um Bedeutung, nicht um Layout.

Danach pushen, damit ich den Stand lesen kann. Weiterhin nichts
promoten, kein colony.py.