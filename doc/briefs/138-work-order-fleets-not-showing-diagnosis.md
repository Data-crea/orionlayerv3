# Work Order 138: Warum erscheint der HD-Fleets-Screen nicht?

## Zuerst

Diesen Auftrag unverändert als
doc/briefs/138-work-order-fleets-not-showing-diagnosis.md ablegen und
indexieren (Nummer am Index prüfen).

Pflichtlektüre: doc/v3_fundament.md, CLAUDE.md,
doc/briefs/134-parked-for-data.md.

## Worum es geht

Data sieht im laufenden Spiel den HD-Fleets-Screen nicht. Nichts davon
ist bisher live gelaufen: weder die Patches 27/28 noch
ACTIVATE_FIELD 12 für den Fleets-Button noch die Feldmengen-Regel aus
137 A. Das ist ein Diagnose-Auftrag. Ursache finden und belegen, nicht
raten und nicht nebenbei umbauen.

## Teil A: Ohne Engine

1. ~/orion2re: Stand von orionlayer-local, und ob beide Patch-Commits
   (cc5ec133, e6199966) enthalten sind. Zeitstempel des Binaries
   out/build/Linux/linux-debug/orion2re gegen den letzten Commit.
2. Ist das Binary älter: cmake --build --preset linux-debug. Das ist
   ein Build, keine Quelländerung, und ist freigegeben.
3. OrionLayer: Stand gleich origin/main (8515081)?
4. Wo schreibt OrionLayer sein Log, und landet fallback_reason() des
   Fleets-Screens dort? Wenn nicht: Das ist ein Befund, im Bericht
   nennen; für diesen Lauf darf eine temporäre Log-Zeile gesetzt
   werden, die danach wieder entfernt wird.

## Teil B: Live

Regeln wie immer: genau ein Client am Server; SAVE1–9 und SAVE11
vorher und nachher hashen, die Werte müssen identisch sein; SAVE10
nur protokollieren; SAVE8 niemals anfassen; livesend liest vor jedem
Senden die Feldliste. Laufen Datas eigene Instanzen noch, oder ist
kein Display erreichbar: STOPP für Teil B, Befund melden.

Nur die Schritte aus 134-parked-for-data.md, die bis zum Öffnen des
Screens nötig sind:
1. Spielstand laden (nicht SAVE8), Galaxiekarte.
2. Feldliste lesen: Welches Feld ist der Fleets-Button? Stimmt 12,
   mit Beleg aus der Quelle?
3. Fleets öffnen, auf dem Weg, den HD benutzt.
4. Festhalten: Screen-ID des Spiels, kommt ein FLTS-Block, Zustand
   der Fleets-View (READY / NO_BLOCK / NO_FIELDS / NO_STACK /
   MISMATCH / FOREIGN_FIELDS), fallback_reason(), und bei
   FOREIGN_FIELDS jedes fremde Feld mit Rechteck und Typ.
5. Screenshots: HD-Fenster und orion2re-Framebuffer, Seite an Seite.
6. RETURN, zurück auf die Karte, Spiel beenden, Hashes prüfen.

Keine Aktionen darüber hinaus: kein Scrap, keine Auswahl, keine
Bewegung.

## Teil C: Ergebnis

- Ursache mit Beleg (Log-Zeile, Feldliste, Screenshot).
- War es nur das veraltete Binary und erscheint der Screen danach:
  Das ist die Lösung, nichts weiter ändern.
- Ist es ein Fehler im Code (falsche Feld-ID, Lücke in der
  Feldmenge, fehlendes Routing): NICHT beheben. Ursache, betroffene
  Stelle (Datei:Zeile) und vorgeschlagene Korrektur in den Bericht.
  Die Korrektur gebe ich frei.

Evidence nach ~/orionlayer-fixtures/evidence/work_order_138/.
Commit nur für die Brief-Ablage und gegebenenfalls einen Eintrag im
Statusdokument; pushen, nachdem der frische Klon grün ist.
