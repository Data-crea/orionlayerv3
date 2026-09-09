Push freigegeben.

Danach zwei Dinge, beide klein:

1. Der unsichtbare "No Farming"-Fall gehört ins Fundament, unter
   Diagnose. Er ist eine neue Ausprägung einer bekannten Regel:
   sieben Zeilen in jeder Zahl korrekt, auf dem Schirm nichts,
   weil eine spätere Zeichenoperation die frühere übermalt. Kein
   Test, der Werte prüft, kann das fangen — auch der neue nicht,
   der jetzt Pixel misst, denn der prüft die Balkenfläche und
   nicht die Sichtbarkeit einer Beschriftung. Zwei, drei Sätze im
   Stil der Umgebung, mit der Konsequenz: nach jedem Renderer
   einmal nach PNG ausgeben und ansehen, bevor die grüne Tabelle
   als Beleg gilt.
   Falls die vorhandene Regel zum Hilfe-Popup das schon abdeckt,
   sag das und häng es dort an, statt einen zweiten Eintrag
   anzulegen.

2. tech_applications in player.py hat keinen verifizierten
   Offset — deshalb fehlt Advanced City Planning in der
   Balkenlänge. Trag das in v3_projektstatus.md unter die offenen
   Punkte der Struct-Verifikation, zusammen mit pop_race. Das sind
   jetzt die zwei Dinge, die die Liste noch von der vollen
   Genauigkeit trennen, und sie sollten an einer Stelle stehen und
   nicht nur im Docstring des Moduls.

Kein neuer Bau in diesem Zug.