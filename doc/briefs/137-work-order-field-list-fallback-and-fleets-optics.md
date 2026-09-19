# Work Order 137: Feldlisten-Rückfall, Kartensperre, Eintrag 70, Fleets-Optik

## Zuerst

1. Diesen Auftrag unverändert als
   doc/briefs/137-work-order-field-list-fallback-and-fleets-optics.md
   ablegen und indexieren. Die Nummer am Index prüfen; ist 137
   belegt, die freie nehmen und im Bericht nennen.
2. Die fünf lokalen Commits aus 135/136 (9d0de95, 8edec3f, fa514b3,
   46c69b3, f0daba1) pushen: frischer Klon, Smoke grün, dann Push.
   Schlägt die Prüfung fehl, selbst reparieren, erneut prüfen, pushen.

Pflichtlektüre: doc/v3_fundament.md, CLAUDE.md,
doc/briefs/134-parked-for-data.md, Berichte 135 und 136.
orion2re nur lesen, keine Patches. Kein Live-Teil.
Der Fleets-Screen bleibt „BUILT, NOT ACCEPTED“.

Reihenfolge: A, B, C, D, E. Jeder Teil ein eigener Commit, Smoke grün
vor jedem Commit.

## Teil A: Unbekannte Felder führen zurück zum Original

Befund aus 136 D: Scrap öffnet über HAROLD::User_Box_ eine native
Bestätigungsbox, die zwei Hidden Fields ergänzt (gendraw.cpp:172-173),
ohne die übrigen Felder zu löschen. fltwire.View._read prüft nur, ob
die erwarteten Felder da sind, nicht, ob fremde dazugekommen sind.
HD bleibt READY über einem Spiel, das in einem Modal wartet.

1. Aus den Quellen, nicht aus einem Feld-Dump, die vollständige Menge
   der Felder bestimmen, die Fleet_Screen_ selbst anlegt: Big Icons,
   Buttons, Filter, Scroll, Stern- und Gitterfelder des Insets
   (MOVEBOX::Add_Galaxy_Map_Fields_2_, flt1.cpp:1250), Leaders, alles
   Weitere. Erkannt wird über Geometrie und Typ, nicht über IDs
   (die IDs sind laufende Nummern). Felder, die als Klasse auftreten,
   etwa die Sternfelder im Inset, werden als Klasse über ihr
   umschließendes Rechteck anerkannt.
2. Ein Feld außerhalb dieser Menge führt zu einem neuen Zustand, z. B.
   FOREIGN_FIELDS: wants_original(), fallback_reason() nennt die
   fremden Felder mit Rechteck. Verschwinden sie wieder, kehrt der
   Screen ohne Neustart zu READY zurück.
3. Smoke-Check über echte Bytes durch parse_state: ein echter Snapshot
   plus die zwei Felder aus gendraw.cpp:172-173 ergibt
   FOREIGN_FIELDS; Klick, Wheel und ESC senden nichts an HD-Logik
   vorbei. Ohne die zwei Felder ergibt er READY. Ein fremdes Feld
   an beliebiger anderer Stelle ergibt ebenfalls FOREIGN_FIELDS.
   Das prüft die Regel, nicht die eine Box. Rot zeigen, dann grün.
4. Lässt sich die Feldmenge nicht vollständig aus den Quellen
   bestimmen: STOPP für Teil A, melden, mit B weitermachen.
5. Evidence 10 in 134-parked-for-data.md anpassen: Der Scrap-Fall mit
   Box ist jetzt ein Prüfschritt für den Rückfall, nicht mehr
   verboten.
6. Nur lesen, nichts ändern: Welche anderen HD-Screens lesen ihre
   Feldliste ebenfalls nur auf Anwesenheit? Tabelle mit Screen,
   Datei:Zeile, und ob dort eine native Box auftreten kann (mit Quelle).

## Teil B: Die Karte sendet nichts außerhalb von Screen 0

In mapinput.map_click: nichts senden, solange die Screen-ID des
Spiels nicht 0 ist. Das ist eine Verweigerung nach Entscheidung 33,
denn heute hält der Ausschluss nur zufällig. Smoke-Check: Kartenklick
bei Screen 4 und 29 sendet nichts, bei Screen 0 wie bisher.

## Teil C: Eintrag 70

1. Baumweiter Grep: Wer außerhalb von screens/galaxy_map/ liest
   ship_icons oder map_scale aus dem Snapshot? Besonders das
   Galaxie-Inset des Kolonie-Screens prüfen (Brief 58). Tabelle mit
   Datei:Zeile.
2. Keine Leser außerhalb: Den Smoke-Assert „kein Modul liest
   client.state“ auf den ganzen Baum ausdehnen und Eintrag 70 in
   doc/v3_fundament.md eintragen. Er steht in der Sprache und im
   Stil des Fundaments (Englisch), unter der passenden Gruppe, nächste
   freie Nummer nach Prüfung. Grundlage ist der Wortlaut aus Bericht
   136, ergänzt um einen Satz, wo die Regel durchgesetzt wird
   (ScreenStateGate, ein Übernahmepunkt, baumweiter Assert). Der Satz
   „Anzeigezustand wird gesperrt, nie etwas, das der Spieler getan
   hat“ muss erhalten bleiben. Kürzen ist erlaubt, Inhalt streichen
   nicht.
3. Leser außerhalb gefunden: Eintrag 70 NICHT eintragen, Tabelle
   melden. Ich entscheide, ob die Sperre dorthin wächst.

## Teil D: Lücken im Brief-Index

Den Index-Check aus 135 C erweitern: Keine Nummer zwischen 1 und der
höchsten darf fehlen, außer den Nummern auf einer Ausnahmeliste im
Check selbst, jede mit Begründung. Dafür vorher die heutigen Lücken
ermitteln und im Bericht nennen, ohne sie zu füllen.

## Teil E: Fleets-Optik

1. Strebenstümpfe entfernen. Nur die zwei aus 136 C: x 1452..1478
   oben und unten, x 594..615 unten (Referenz). Nichts malen: Die
   Pixel jenseits der Linie der angrenzenden Ringkante werden
   transparent. Die Stufen des Masters (y 75/77, x 74/75) bleiben
   unverändert. Ist das ohne Malen nicht sauber möglich: STOPP für E1
   mit Vorher-/Nachher-Ausschnitt.
2. Fleets in _FRAME_SCREENS aufnehmen, den Entwurf
   doc/briefs/136-draft-fleets-opening-check.py als echten Check
   übernehmen und die Klasse-B-Messung verfeinern: jede Zeile und
   Spalte oder ein Raster, das schmaler ist als der schmalste
   bekannte Einbruch. colony_summary und galaxy_map müssen grün
   bleiben. Das Ziel für Fleets ist L1 R0 T2 B1 oder besser.
3. Doppelte Linien. Eine Box innerhalb einer thin_border-Gruppe darf
   nicht auf deren Rand liegen. Den Mindestabstand aus bestehenden
   Screens ableiten (Custom Race, New Game) und mit Quelle nennen.
   Betroffen sind die Dreierleiste unter dem linken Panel und die
   Button-Gruppe (Leaders, Return). Smoke-Check als Regel: jede
   Box in jeder Gruppe, auf allen Screens, die thin_border-Gruppen
   haben. Findet der Check Verstöße auf anderen Screens: nicht
   beheben, melden.
4. Return. Die gezeichnete Box kommt nur aus dem Feld (556,430). Das
   Hilfe-Rechteck 374 bleibt in help.json und bestimmt keine
   Box-Kante (Entscheidung 38).
5. Leere Flächen.
   - Inset-Karte: sichtbarer Hinweis als text-Box (Entscheidung 37),
     Wortlaut in JSON (Entscheidung 15), OMISSION-Markierung wie bei
     den anderen vier, Smoke-Check hält sie. Hat der Screen einen Weg
     für einen gewollten Rückfall auf das Original, führt ein Klick
     ins Inset dorthin. Gibt es keinen: nur Hinweis und Markierung,
     im Bericht sagen.
   - Dreierleiste: aus den Quellen bestimmen, was das Original dort
     zeigt. Liegen die Daten auf dem Draht, füllen. Sonst als
     OMISSION markieren wie das Inset.
6. Zwei hervorgehobene Zellen (Ship 2 und 5 im Render): aus den
   Quellen klären, ob das Original Mehrfachauswahl kennt und was
   das Info-Panel dann zeigt. Ist die HD-Darstellung falsch,
   korrigieren. Ist sie richtig, im Bericht belegen.
7. Renders in allen vier Auflösungen nach
   ~/orionlayer-fixtures/evidence/work_order_137/, dazu ein Ausschnitt
   jeder vorher betroffenen Stelle, vorher und nachher.

## Abschluss

Frischer Klon, Smoke grün, dann alle neuen Commits pushen. Schlägt
die Prüfung fehl: selbst reparieren, erneut prüfen, pushen. Upload-
Sperre unverändert. Teile, die auf STOPP enden, werden ohne sie
gepusht; das steht im Bericht.

## Bericht

- Nummer, Ablage, Push-Ergebnis nach „Zuerst“.
- A: Feldmenge mit Quellen, neuer Zustand, Smoke-Nummer, Rot/Grün,
  Tabelle der anderen Screens.
- B: Stelle, Smoke-Nummer.
- C: Grep-Tabelle; eingetragen ja/nein, Nummer, endgültiger Wortlaut.
- D: heutige Lücken, Ausnahmeliste.
- E: je Punkt, was gemacht wurde; neue Einbruchswerte; Verstöße auf
  anderen Screens; Pfade der Renders.
- Endstand von origin/main.
