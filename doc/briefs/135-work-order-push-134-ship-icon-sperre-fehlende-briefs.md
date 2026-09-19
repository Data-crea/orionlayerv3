# Work Order 135: Push 134, Ship-Icon-Sperre, fehlende Briefs

## Worum es geht

Work Order 134 (Fleets) ist gebaut und liegt in vier lokalen Commits
(a47650f, 0f0e488, b6b1f6f, 14a6db7) vor origin/main 2306f3d. Die
Frage nach einer doppelt vergebenen Nummer ist geklärt: Die
Rahmenprüfung war Schritt 1 von 134 (v3_projektstatus.md:5041), kein
eigener Auftrag. Es wird nichts umbenannt.

Vor der Live-Abnahme von 134 fehlt eine Sperre: Solange Screen 4 offen
ist, liegt jedes s_ship_icon auf dem Draht im Fleet-Inset-Raum, und
stack_id trägt eine Feld-ID. Die Galaxiekarte darf diese Daten nicht
übernehmen. Außerdem fehlen in doc/briefs/ mehrere Auftragsdateien.

Pflichtlektüre: doc/v3_fundament.md, CLAUDE.md.
Kein orion2re-Eingriff. Kein Live-Teil.

## Teil A: Prüfung und Push von 134

Push ist mit diesem Auftrag freigegeben.

1. Frischer Klon, Smoke-Test, alles grün.
2. Schlägt die Prüfung fehl: selbst reparieren, erneut im frischen
   Klon prüfen, dann pushen.
3. Upload-Sperre gilt unverändert.
4. Neuen Stand von origin/main im Bericht nennen.

## Teil B: Ship-Icon-Sperre

1. Zuerst alle Stellen finden, an denen die Galaxiekarte s_ship_icon
   oder stack_id aus dem Snapshot übernimmt, einschließlich Caches
   und allem, was einen Klick auf einen Stack in ein Kommando
   übersetzt. Liste mit Datei:Zeile in den Bericht.
2. Die Sperre an genau einer Stelle einbauen, dort, wo Snapshot-Daten
   in den Kartenstand übernommen werden, nicht bei jedem Verbraucher.
   Regel: s_ship_icon wird nur übernommen, wenn die Screen-ID des
   Snapshots 0 ist. Sonst bleibt der letzte Stand aus Screen 0
   unverändert stehen.
3. Smoke-Check, der die Regel prüft, nicht den Einzelfall, über echte
   Bytes durch parse_state:
   - Snapshot Screen 0 einspeisen und den Kartenstand merken.
   - Snapshot Screen 4 mit Inset-Koordinaten und Feld-IDs als
     stack_id: Kartenstand exakt unverändert.
   - Dasselbe mit mindestens einer weiteren Screen-ID ungleich 0.
   - Snapshot Screen 0 mit geänderten Icons: Kartenstand übernommen.
4. Den Punkt in doc/briefs/134-parked-for-data.md ergänzen: Die
   Live-Abnahme prüft auch, dass die Karte nach Rückkehr aus Fleets
   korrekte Positionen zeigt und ein Klick auf einen Stack den
   richtigen Stack meint.

## Teil C: Fehlende Auftragsdateien

In doc/briefs/ fehlen die Auftragsdateien zu 125, 132, 133 und 134
(bei 134 liegen nur progress und parked; die Datei war
workorder_fleets_screen.md).

1. In ~/orionlayer-fixtures/incoming/ und in der Git-Historie suchen.
2. Gefundene Dateien unverändert nach doc/briefs/ kopieren, nach dem
   bestehenden Namensschema benennen und in doc/briefs/README.md
   indexieren wie die übrigen.
3. Nicht auffindbare Dateien nicht nachschreiben, sondern im Bericht
   als fehlend nennen.

## Abschluss

Teile B und C lokal committen (getrennte Commits), Smoke grün im
frischen Klon. Nicht pushen, das gebe ich nach dem Bericht frei.

## Bericht

- Teil A: neuer Stand von origin/main.
- Teil B: Verbraucherliste, Stelle der Sperre, neue Smoke-Nummer.
- Teil C: welche Dateien gefunden und wo, welche fehlen.
- Die sechs offenen Entscheidungen aus 134-parked-for-data.md wörtlich
  aufgelistet, damit ich sie hier im Chat beurteilen kann.
- Zwei Nachfragen zu 134:
  1. Sind die Cutout-Boxen des Fleets-Rahmens per
     tools/frame_holes.py --write erzeugt, und prüft der Smoke-Test
     die Übereinstimmung von Rahmen und Boxen (Entscheidung 3)?
     Wenn nein: benennen, nicht nachbauen.
  2. Welche Asserts sind mit Smoke 216 und 217 dazugekommen? Liste.
