Patch 20 neu fassen: pro Knoten selected und ship_idx, plus die Box-Stack-Kette in Anzeige-Reihenfolge. HD liest die Zuordnung vom Draht statt sie zu rekonstruieren.

Ursache ist bestätigt: Sort_Ships_In_Stack_ (shipstak.cpp:261-278) sortiert die Schiffe innerhalb der Knoten um, die Knotenplätze bleiben. Deshalb sind beide bisherigen HD-Annahmen falsch (Knoten n = n-tes Schiff; Box in Array-Reihenfolge). Den Sort in HD nachzubauen ist kein Weg — qsort ist nicht stabil.

Beschreiben, mir vorlegen, dann anwenden. Kurzfassung, was sich gegenüber der jetzigen Fassung ändert, damit im Diff steht, was neu in Joes Baum geht.
Im Baum zurücknehmen und neu anwenden. Der alte Patch 20 ist angewendet — sauber zurücknehmen (gesicherter Vor-Zustand im Scratchpad), neue Fassung anwenden, orion2re mit -DORION2RE_EXT=ON neu bauen. version_check.py muss beide weiter als „applied" zeigen. Hakt etwas oder bricht der Build: anhalten und melden, nicht live gehen.
HD-Seite auf beide neuen Felder umstellen:
selection_of und die Zellenreihenfolge lesen aus dem Draht (ship_idx je Knoten, Anzeige-Reihenfolge aus der Box-Stack-Kette).
owners_from_nodes auf dieselbe Quelle umstellen — sie ist heute nur zufällig richtig, weil alle Schiffe eines Stacks denselben Eigentümer haben. Keine zweite Kopie der alten rekonstruierten Zuordnung im Baum lassen.
ships.build_node_map und die Array-Reihenfolge-Annahme entfernen, wo die Draht-Daten sie ersetzen.
Live-Test auf SAVE5 wiederholen, Prüfung 2 zuerst: Zellklick auf die erste Zelle dreht im Original die richtige Zelle schwarz, und der Knoten, den die Engine dreht, ist der, den HD anzeigt. Dann Prüfung 1 an einem Stack mit unterschiedlicher Auswahl (nicht alle gleich, sonst nicht aussagekräftig), dann 3 (Zielklick a) und 5 (Schutz aus Entscheidung 65).
Scrollbalken (Prüfung 4) zurückstellen — SAVE5 hat keinen Stack über neun Schiffe (größter: sieben). Ich lege einen Scratch-Stand mit großer Flotte an und sage Bescheid.

Protokoll: genau eine Instanz, SAVE1–SAVE9 vorher/nachher hashen, SAVE10 nur protokollieren, kein Flottenbefehl über den Test hinaus, nie SAVE8. Kein Push.

Dokumente erst einlösen, wenn Patch 20 in dieser Form live bestätigt ist: Brief 118 committen, Open Fixes 20/21 auf „angewendet", version_check auf Pflicht. Nicht davor — sonst steht „angewendet" über einem Patch, der nochmal umgebaut wird.
