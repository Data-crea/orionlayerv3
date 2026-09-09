Paket: Pop-Verschiebung, Phase 3b — die Anbindung an die Maus

Richtung und Abnahme. Jede Zahl, jede Zeilennummer und jedes Offset darin ist ein Ausgangspunkt, kein Befund — prüfen und im selben Commit korrigieren. Alles, was in den Baum geschrieben wird, ist englisch.

Vorher: doc/v3_fundament.md lesen.

Befund vorweg (im Chat gemessen, nachprüfbar)

Zwei Schnappschüsse von src/ liegen vor, einer vor und einer nach den Patches vom 4. September. Sie unterscheiden sich in genau drei Dateien — ext/ext_api.h, ext/ext_api.cpp, game/platform.cpp — also exakt im Umfang von doc/ext_inject_click.patch, ohne dass etwas daneben mitgelaufen wäre.

patch -p1 -R --dry-run nimmt den Patch gegen den neuen Baum sauber zurück, alle Hunks, kein Fuzz; vorwärts wird er als bereits angewandt abgelehnt. Die Rücknahmezeile in der Präambel ist damit geprüft und nicht nur behauptet.

ORION2RE_EXT steht an 13 Stellen in vier von Joes' Dateien (platform.cpp 4, fields.cpp 2, racesel.cpp 3, mox2.cpp 4), src/ext/ umfasst 909 Zeilen. Das sagt, welche Dateien der Diff gegen cf4d9617 überhaupt nennen darf — nicht, was er findet.

0. Tor: der eine Klick

Bevor irgendetwas an der Maus gebaut wird. Spiel neu gestartet, Save geladen, Colonies offen. Dann tools/colony_move_probe.py: Inode gegen 7740112 prüfen, Trockenlauf zeigen, einen Klick schicken.

Läuft das nicht durch: melden und aufhören. Nicht vorbeibauen.

Abnahme dieses Klicks:

Der Vorher/Nachher-Vergleich geht über alle Kolonien des Spielers, nicht nur die Zielkolonie. Send_Cluster_s lange Verzweigung kann zwischen Kolonien schieben, und „eine geändert, die richtige" ist erst eine Aussage, wenn die anderen mitgelesen wurden.
Das Rücklesen wartet auf den State-Zähler, nicht darauf, dass überhaupt ein Bild da ist.
Grün heißt „der Klick kommt an". Es heißt nicht, dass plan_drop stimmt. Das ist eine zweite Behauptung und braucht einen Fall, dessen Vorhersage nicht „alle" lautet. Ist so einer im Referenz-Save nicht erreichbar: als Satz ins Protokoll, nicht stillschweigend mitlaufen lassen.
1. Lesen und berichten, vor dem Bauen

In screens/colony_summary/colonymove.py, colonyselect.py und colonyfirst.py: was ist da, was fehlt?

Die eine Frage, an der die Antwort hängt: berechnet der Spiegel schon die Zusammensetzung des Clusters, oder nur die Ablehnungen? Get_Cluster_ nimmt jeden identischen Pop bis zum Ende des Arrays, nicht den zusammenhängenden Lauf unter dem Zeiger — ein Klick auf ein Icon greift also unter Umständen mehr als das, was daneben liegt.

Fehlt das, ist es der erste Baustein, mit eigenem Nachweis aus pop[].

2. Bedienmodell: Klick-Klick, kein Ziehen

Das Original ist Klick-Klick (colsum.cpp:851). Ziehen wäre eine Erfindung ohne Grund. Erster Klick auf ein Pop-Icon in einer HD-Zeile, zweiter Klick auf eine Job-Spalte.

3. Die Naht — die eigentliche Entscheidung dieses Pakets

Die HD-Auswahl ist rein lokal und schickt nichts. Erst der zweite Klick — Ziel bekannt, alle fünf Regeln durch — löst die Injektion aus, und zwar beide Klicks.

Grund: es gibt keinen Abbruch, der auf dem Screen bleibt. Beide Clear_Cluster_-Aufrufe auf diesem Screen sind Wege heraus. Eine HD-Auswahl, die im Spiel schon einen Cluster erzeugt, strandet den Spieler in dem Moment, in dem er es sich anders überlegt. Eine Vorschau darf nicht injizieren.

Daraus folgt ein Abbruch, den das Original nicht hat: Rechtsklick oder Klick ins Leere verwirft die Auswahl. Das ist eine markierte Abweichung — im Modul, im Statusdokument, und mit einer Prüfung, die fällt, wenn die Markierung verschwindet. Der Satz, den die Markierung tragen muss, ist nicht „wir sind netter", sondern: die HD-Auswahl ist nicht die Auswahl des Spiels, deshalb kostet ihr Verwerfen nichts.

4. Der Ablauf auf der Leitung

Wenn der zweite Klick fällt:

_first etablieren (GameWindow, ACTIVATE_FIELD, einzeln und bestätigt — ein Stapel wird auf den letzten reduziert).
Klick 1 schicken. Auf die Wirkung warten, nicht die Sends zählen: die aufgenommenen Pops werden unzugewiesen, und das steht im Snapshot.
Erst dann Klick 2.
Wieder auf den State warten und gegen plan_drop prüfen.

Bestätigt Schritt 3 oder 4 nicht, hält das Spiel einen Cluster. Dann melden und stehen bleiben — nicht den Screen verlassen, nicht so tun, als sei nichts passiert. Der Zustand ist am Snapshot ablesbar, also kann HD ihn benennen.

Falle, die nach dem Zug aufgeht: die Werte der Kolonie ändern sich, und wenn die HD-Liste nach einem betroffenen Schlüssel sortiert ist, wandert die Zeile. _first wird nach jedem Zug neu etabliert, nie fortgeschrieben.

5. Abnahme
Ein echter Mausklick auf dem HD-Screen verschiebt die vorhergesagte Anzahl in der richtigen Kolonie, und keine andere Kolonie ändert sich.
Der Abbruchweg schickt nichts — nachweisbar daran, dass kein INJECT_CLICK über die Leitung geht, nicht daran, dass hinterher alles gleich aussieht.
Ein abgelehnter Zug schickt nichts und sagt in HD warum; die Formulierung liegt in layout.json unter move.
Den Screen mit gehaltener Vorschau nach PNG rendern und anschauen. Eine grüne Tabelle sagt, dass die Daten stimmen; nur das Bild sagt, dass die Auswahl sichtbar ist.

Die Sichtbarmachung selbst ist Phase 4 und blockiert hier nicht. Für jetzt genügt die einfachste Zeichnung, die man sehen kann.

Smoke-Test grün, Zahl nicht kleiner. git push erst nach Datas Diff.