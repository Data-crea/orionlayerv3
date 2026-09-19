# Work Order 136: Screen-4-Sperre verallgemeinern, Öffnung des Fleets-Rahmens messen

## Zuerst

Diesen Auftrag unverändert als
doc/briefs/136-work-order-screen-state-gate-and-fleets-opening.md
ablegen und im README indexieren, bevor irgendetwas anderes passiert.
Die nächste freie Nummer vorher am Index prüfen; ist 136 belegt, die
tatsächlich freie nehmen und im Bericht nennen.

Pflichtlektüre: doc/v3_fundament.md, CLAUDE.md,
doc/briefs/134-parked-for-data.md, Bericht 135.
Kein orion2re-Eingriff. Kein Live-Teil. Nicht pushen.

## Worum es geht

135 B sperrt s_ship_icon, solange die Screen-ID nicht 0 ist. Der
Bericht hat daneben gefunden, dass Fleet_Screen_ auch
MOX::_cur_map_scale umschreibt (flt.cpp:14, gesichert und
wiederhergestellt in flt1.cpp:487/:835) und dass es als gs.map_scale
auf dem Draht liegt. Durch den Proxy mischt der Kartenstand
jetzt Icons aus Screen 0 mit einem Maßstab aus Screen 4, also zwei
Bezugsrahmen (Entscheidung 35). Statt Feld für Feld nachzutragen,
wird die Regel verallgemeinert: Alles, was der Fleets-Screen an
Engine-Zustand umschreibt und was auf dem Draht liegt, übernimmt die
Karte nur aus Screen 0.

Zweitens ist die Öffnung des Fleets-Rahmens eine getippte Zahl, gegen
die nichts prüft. Die Renders aus 134 zeigen drei trapezförmige
Halterungen der Innenkante, die über dem Raster und über der
Unterkante des Info-Panels liegen. Das wird hier nur gemessen, nicht
behoben.

## Teil A: Was schreibt der Fleets-Screen um?

Die Funktionen lesen, die den Zustand herstellen, nicht die, die ihn
lesen: das Setup in flt.cpp, Fleet_Screen_ in flt1.cpp samt allem,
was es beim Betreten aufruft, und das Zurückstellen in
mainscr_main.cpp.

Tabelle in den Bericht, eine Zeile pro Variable, die während Screen 4
einen anderen Wert hat als auf der Karte:
- Variable, geschrieben wo (Datei:Zeile), zurückgestellt wo;
- liegt sie auf dem Draht (ext_api.cpp:Zeile, Feldname im Snapshot)?
- welche OrionLayer-Stellen lesen sie (Datei:Zeile)?

Bekannt sind s_ship_icon und _cur_map_scale. Offen ist mindestens der
Karten-Ursprung. Was nicht auf dem Draht liegt, kommt in die Tabelle,
aber nicht in die Sperre.

## Teil B: Die Sperre verallgemeinern

1. IconGate wird zu einem Gate für alle Snapshot-Felder aus Teil A,
   die auf dem Draht liegen. Die Liste der gesperrten Felder steht an
   genau einer Stelle, jedes Feld mit seiner Quelle (Datei:Zeile) als
   Kommentar. Bleibt die Klasse für mehr als Icons zuständig, passt
   der Name nicht mehr: umbenennen, Grep über das ganze Projekt.
2. Vor dem Einbau jeden Leser von map_scale (und jedem weiteren Feld)
   einordnen: Rendern, Re-Anchoring, Parken (Entscheidung 35),
   Umrechnung Galaxie → nativ für Klicks. Für jeden Leser im Bericht
   sagen, ob er den gesperrten Wert bekommen soll, und warum.
   Besonders prüfen: Die Umrechnung für den Draht muss den
   tatsächlichen Spielzustand nutzen, und das Parken darf nicht auf
   einen eingefrorenen Wert hereinfallen. Widerspricht die Sperre
   dort Entscheidung 35, STOPP und melden, nicht auflösen.
3. Der Smoke-Check aus 135 B wird auf die Regel umgestellt: Er
   iteriert über die Feldliste des Gates, statt Icons fest
   abzufragen. Für Screen 4 und mindestens drei weitere Screen-IDs
   ungleich 0 bleibt jedes gesperrte Feld exakt unverändert, alles
   andere fällt live durch. Zusätzlich gilt: Ein Kartenstand nach
   einer Folge Screen 0 → 4 → 4 enthält in keinem gesperrten Feld
   einen Wert aus Screen 4 (der erste Frame nach RETURN, bevor ein
   neuer Snapshot für Screen 0 da ist). Echte Bytes durch parse_state,
   wie gehabt. Rot zeigen, dann grün.
4. Einen Vorschlag für einen Fundament-Eintrag formulieren, aber nicht
   eintragen. Arbeitstitel: „Zustand, den ein Screen umschreibt, gilt
   nur für diesen Screen.“ Der Wortlaut kommt in den Bericht, die
   Entscheidung trifft Data.

## Teil C: Öffnung des Fleets-Rahmens messen

Nur messen und berichten, nichts an Boxen oder Rahmen ändern.

1. find_holes auf dem Fleets-Rahmen-PNG laufen lassen und das Ergebnis
   gegen opening [72, 73, 1775, 921] in layout.json stellen.
2. Die Alpha-Einbruchsmessung (Klasse B) auf dem Fleets-Rahmen
   ausführen, wie für colony_summary und galaxy_map.
3. Bericht: jede Stelle, an der Metall in die Öffnung reicht
   (Referenzkoordinaten, Tiefe in px), und welche Boxen aus
   boxes.json sie berühren, für alle vier Auflösungen.
4. Sagen, ob die drei Halterungen (oben bei etwa x 1460, unten bei
   etwa x 600 und x 1460 in 1080p) Ornament des Rings sind oder Reste
   der Streben, die nach 134 A hätten entfernt werden sollen, mit
   Beleg aus dem Planets-Master.
5. Fleets NICHT in _FRAME_SCREENS eintragen und keinen roten Check
   committen. Der Check kommt zusammen mit der Korrektur in der
   Optik-Runde. Den fertigen Check-Code als Entwurf unter
   doc/briefs/136-draft-fleets-opening-check.py ablegen.

## Teil D: Zwei Fragen für die Live-Abnahme (nur lesen)

Aus dem Code beantworten, nichts bauen:
1. Was tut der HD-Fleets-Screen heute bei einem Klick auf einen Stern
   bzw. in die Inset-Karte? Geht etwas auf den Draht, passiert
   nichts, oder fällt er auf das Original zurück?
2. Was tut der HD-Fleets-Screen, wenn sich die Feldliste ändert, ohne
   dass die Screen-ID wechselt, z. B. wenn Scrap eine native
   Bestätigungsbox öffnet? Wird das erkannt, und fällt er dann auf den
   Framebuffer zurück? Dazu in den Quellen belegen, ob Scrap eine
   solche Box öffnet.
Beide Antworten als Schritte in 134-parked-for-data.md eintragen,
den zu Scrap vor dem ersten Scrap-Klick.

## Abschluss

Getrennte Commits für Brief-Ablage, Teil B und Teil D. Teil C ist nur
der Entwurf und die Messung, eventuell im selben Commit wie D. Smoke
grün im frischen Klon. Nicht pushen.

## Bericht

- Nummer und Ablage des Auftrags.
- Teil A: die Tabelle.
- Teil B: Leser-Einordnung, gesperrte Felder, neue Smoke-Nummer,
  Rot/Grün-Beleg, Vorschlag für den Fundament-Eintrag.
- Teil C: Messergebnis, betroffene Boxen, Ornament oder Rest.
- Teil D: beide Antworten mit Quellen.
- Stand gegenüber origin/main.
