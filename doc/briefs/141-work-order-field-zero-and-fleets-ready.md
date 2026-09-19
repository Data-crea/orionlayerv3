# Work Order 141: Feld 0, realistische Fixtures, Fleets live auf READY

## Zuerst

Diesen Auftrag unverändert als
doc/briefs/141-work-order-field-zero-and-fleets-ready.md ablegen und
indexieren (Nummer am Index prüfen).

## Teil A: Die Korrektur aus 140

Die vorgeschlagene Bedingung in fltwire (Feld 0 überspringen, mit
Kommentar) ist freigegeben.

## Teil B: Fixtures tragen immer ein Feld 0

1. Den Baukasten, aus dem Smoke-Checks Feldlisten bauen, so ändern,
   dass jede Liste mit einem Feld 0 mit Müll-Geometrie beginnt, wie
   die echte Engine (fields.cpp:207, ext_api.cpp:326). Gibt es mehrere
   Baukästen: alle, und im Bericht nennen.
2. Der Fleets-Check verlangt mit Feld 0 READY. Rot zeigen: Teil A
   zurückgenommen → FOREIGN_FIELDS.
3. Fallen andere Checks durch das realistische Feld 0 um: nicht
   stillschweigend anpassen, sondern jeden Fall nennen. Ein Check, der
   jetzt rot wird, hat einen echten Fehler gefunden.

## Teil C: Wer liest Feldlisten? (nur lesen)

Tabelle aller Verbraucher von Feldlisten: Datei:Zeile, ob Feld 0
heute übersprungen wird, und ob Feld 0 dort Schaden anrichten
könnte. ext_diag.py ist absichtlich redundant und wird nur genannt.
Vorschlag, ob Feld 0 an einer zentralen Stelle entfernt werden
sollte, mit Begründung gegen Entscheidung 59. Nicht umbauen.

## Teil D: Fleets live

Data startet orion2re selbst. Ausnahme und Regeln wie in 140
(ein Client, Hashes, SAVE8 nie, livesend liest die Feldliste,
Engine nicht beenden).

1. Spielstand laden (nicht SAVE8), Fleets per Hotkey f.
2. Erwartet READY: Log-Zeilen wörtlich, Screenshot HD-Fenster und
   Framebuffer Seite an Seite.
3. HD-Screen gegen die Renders aus 137 legen: Was ist live anders
   (Schiffe, Namen, Farben, Leerflächen, Einblendungen)?
4. RETURN, Karte, Hashes.
5. Keine Auswahl, kein Scrap, keine Bewegung.
Ist es nicht READY: Ursache mit Log und Feldliste, Korrektur
vorschlagen, NICHT anwenden.

## Teil E: Klicks für Live-Abnahmen (nur Vorschlag)

Die nächsten Abnahmeschritte sind Klickpfade, und der Zeiger lässt
sich aus der Sitzung nicht bewegen. Einen Vorschlag machen, nicht
bauen: eine Debug-Möglichkeit, Maus-Ereignisse direkt in die
pygame-Schleife zu geben, die denselben Weg nimmt wie ein echter
Klick (Entscheidung 5), im normalen Betrieb aus ist und als
Werkzeug markiert wird. Aufwand, Risiko, und woran ein Test
erkennt, dass sie nicht versehentlich an ist.

## Abschluss

Frischer Klon, Smoke grün, pushen. Bericht: A–E, Log-Zeilen
wörtlich, Endstand von origin/main.
