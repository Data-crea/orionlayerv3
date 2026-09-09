# Auftrag: Pop-Verschiebung auf dem Colony-Summary-Screen

Aus der Chat-Session, 4. September 2026. Richtung und Akzeptanz kommen
von hier; jede Zahl darin ist ein Startpunkt, keine Tatsache. Prüf sie
und korrigier sie im selben Commit.

---

## Zuerst: zwei offene Enden schließen

**Paket 1 (Randprüfung) zu Ende bringen.** Die Entscheidung ist
getroffen: statt der einen Regel zwei.

- **Klasse A — Text, den unser Code an eine Cutout-Kante setzt.**
  Null Pixel unter deckendem Alpha, an jeder ausgelieferten Größe.
  Keine Toleranz. Heute grün, beißt beim Entfernen des Insets.
- **Klasse B — Inhalt, der auf ein Cutout geclippt wird.** Nicht der
  Rückstand wird geprüft, sondern die Rahmengrafik: wie weit das
  deckende Alpha an den geraden Kanten in jedes Loch hineinreicht.
  Budget pro Cutout, heute gemessen, Ecken ausgenommen.

**Davor eine Frage, die die Ursache vielleicht wegnimmt:** `to_ref`
hat `bleed` als Parameter. Für einen Content-Clip wäre `bleed=0` das
echte Loch, und das Loch ist in MOO2 das Fenster. Die 2 Referenzpixel,
die dabei wegfallen, sind die, die ohnehin unter Metall liegen. Wenn
das stimmt, ist ein unbleedeter Clip treuer, nicht schneidender.
Prüfen, bevor irgendetwas markiert wird.

Zwei Lehren aus dem Survey gehören ins Fundament, als Ergänzung an
bestehende Einträge und nicht als neue Nummern:

- Zu „A check that measures the wrong object is not a check":
  **gemessen wird, was den Clip überlebt, nicht was angefordert
  wurde.** Drei erfundene Labels, 330 px außerhalb.
- Daneben: **die Aussagekraft einer Prüfung ist eine Eigenschaft des
  Zustands, in dem sie läuft.** 22 Blits gegen 65, und keine
  Sternnamen in diesem Save. Ein grüner Lauf im Nullzustand ist
  wertlos.

**Die `plntsum.cpp`-Lesung als Dokument in den Baum committen.** Sie
ist bezahlt und nicht committet. Planets kommt später, wenn die
Rahmengrafik existiert.

Drei Akzeptanzpunkte für Planets, damit sie nicht verlorengehen:
`_plntscrn_delta_y` wird als Tabelle transkribiert, nie als
Schrittweite; die halbe Zeile, um die Gravity ohne Penalty-Meldung
rückt, wird transkribiert, nicht vereinheitlicht; die kleine
Galaxiekarte ist die zweite Fundstelle mit eigenem Mittelpunkt-Offset
— zwei, nicht drei, also vermerken statt extrahieren.

---

## Was gebaut wird

Der Spieler zieht Bauern, Arbeiter und Forscher zwischen den Spalten
um — in HD, mit dem Spiel als Rechenwerk dahinter.

## Was es für den Spieler besser macht

MOO2 ist an dieser Stelle stumm. Ein Klick nimmt eine ganze identische
Gruppe ab dieser Stelle mit, nicht einen Pop, und nichts sagt das
vorher. Eine verweigerte Ablage antwortet im Framebuffer. Ein Spieler
lernt beides durch Ausprobieren.

Der Mehrwert liegt nicht in mehr Funktionen, sondern darin, **die
Regeln sichtbar zu machen, die das Original schon hat**. Drei Dinge,
rein clientseitig, alle als `HD EXTENSION` markiert:

1. Vor dem ersten Klick: welche Pops eine Auswahl mitnehmen würde.
2. Vor dem zweiten Klick: welche Zielspalten annehmen und welche
   nicht — die Verweigerung als Grund statt als Schweigen.
3. Nach dem Klick: was tatsächlich passiert ist.

**Nicht in diesem Paket:** vorausberechnete Ausgabezahlen in Grau.
Das heißt `colcalc` nachbauen, und dieses Projekt hat schon einmal
einen Balken gegen eine Tabelle statt gegen die Funktion gebaut.
Separates Thema, separate Evidenz.

Nichts wird erfunden, was das Original könnte und anders macht. Eine
Vorschau ist eine Erfindung und wird markiert. Eine andere
Bewegungsregel wäre ein Fehler.

---

## Phase 0 — Lesen und berichten. Kein Code.

Die Verweise stehen im Fundament, Abschnitt 3, als Zeiger. Lies sie
dort und dann in der Quelle:

- click-click-Semantik, und wo `Get_Cluster_` / `Send_Cluster_`
  gerufen werden
- die fünf Ablageregeln in `Give_Colonist_New_Job_`
- Icon-Geometrie, Squish-Berechnung, Spaltenkanten

**Berichte, bevor du irgendetwas baust.** Jede Abweichung von dem, was
im Fundament steht, ist eine Korrektur in derselben Antwort. Die
Zahlen dort sind alt genug, um überprüft zu werden.

Zwei Fragen, die den Aufbau entscheiden und die ich nicht beantworten
kann:

- **Was macht `Get_Cluster_` mit einer bestehenden Auswahl, wenn ein
  zweiter Klick woanders landet?** Ersetzen, aufheben, ignorieren —
  davon hängt ab, ob HD einen Zustand halten muss.
- **Gibt es einen Weg, eine Auswahl abzubrechen, ohne sie
  abzulegen?** Wenn nicht, ist jede HD-Vorschau, die eine Auswahl im
  Spiel erzeugt, eine Falle. Dann muss die Vorschau ohne Injektion
  auskommen — was sie ohnehin sollte.

*Überspringst du Phase 0*, steht die Bewegungslogik auf dem
Fundament-Eintrag statt auf der Quelle, und der Eintrag ist selbst
eine Transkription. Zwei Kopien tief.

## Phase 1 — Die fünf Regeln, gespiegelt

Entscheidung 33, und sie ist hier an der Grenze ihres eigenen
Geltungsbereichs: sie erlaubt das Spiegeln, „where the rule is one
comparison". Fünf Regeln sind das nicht mehr.

**Sag zuerst, ob sie noch trägt.** Lassen sich die fünf als eine
Funktion lesen, deren Eingaben alle im Snapshot stehen, trägt sie.
Braucht eine davon Zustand, den wir nicht haben, trägt sie nicht —
dann gehört diese eine auf die C++-Seite als Eintrag in
`doc/orion2re_open_fixes.md`, und der Klick wird dafür nicht
angeboten. Beides ist ein akzeptables Ergebnis. Nicht akzeptabel:
eine Regel raten, weil vier andere sich spiegeln ließen.

Jede der fünf einzeln:

- Quelle mit Zeilennummer
- die Snapshot-Felder, aus denen sie sich entscheidet, jedes mit
  seinem Verifikationsstand nach Entscheidung 23
- ein Check, der sie beißend zeigt

Der Transport-Fall — Klick auf eine andere Kolonie — ist **nicht**
Teil dieses Pakets. Er öffnet einen Dialog, und ein Dialog ist eine
eigene Kette nach Entscheidung 21. Für jetzt: erkennen und ablehnen,
nicht auslösen.

*Spiegelst du eine Regel nur teilweise*, verweigert das Spiel
gelegentlich, HD merkt es nicht, und beide stehen ab da auf
verschiedenen Zuständen. Derselbe Fehlermodus wie in Entscheidung 46.

## Phase 2 — `_first`, bevor ein Klick fliegt

Entscheidung 46, ohne Abkürzung. Etablieren, nicht merken. Sichere
Richtung zuerst. Die Verweigerungen des Fensters vorher spiegeln,
sonst zählt man einen Schritt, den das Spiel nicht gemacht hat.

Zusatz aus derselben Entscheidung: **HDs sichtbare Zeilenzahl ist
nicht die Fensterzahl des Originals.** Jedes k wird gegen das Original
gerechnet.

Akzeptanz: eine Prüfung, die für eine gegebene HD-Zeile und ein
gegebenes `_first` die Schrittfolge berechnet, und die für „weniger
Kolonien als Fensterplätze" das Richtige tut, nämlich nichts.

## Phase 3 — Die zwei Klicks

Erst wenn 1 und 2 grün sind.

Reihenfolge nicht verhandelbar: `_first` etablieren, Regeln prüfen,
dann nehmen, dann ablegen. Der Injektionsweg folgt Entscheidung 39 —
für Positionen im Track gibt es keine Feld-ID, also Koordinate, und
die Einschränkung dieses Weges steht dort.

**Ein Klick, der nicht durchgeht, wird berichtet und nicht
wiederholt.** Kein Retry, keine Heuristik. Melden und stehenbleiben.

## Phase 4 — Die Sichtbarmachung

Erst wenn das Verschieben funktioniert. Rein zeichnerisch, ohne
Injektion, markiert.

Und nach der Regel von der „No Farming"-Beschriftung: **jeden neuen
Renderer nach PNG rendern und ansehen.** Eine grüne Tabelle sagt, dass
die Daten stimmen. Nur das Bild sagt, dass sie sichtbar sind.

---

## Akzeptanz insgesamt

- Smoke-Test grün, Anzahl nicht gesunken
- Jede gespiegelte Regel mit Quellenverweis und einem Check, der beißt
- Jede Erfindung markiert: in der Datei, im Statusdokument, in einem
  Check
- Side-by-Side gegen das Original desselben Saves, nach jeder Phase
  mit sichtbarer Wirkung
- Jede Zahl aus diesem Auftrag: Startpunkt, nicht Tatsache. Korrektur
  im selben Commit.

**Wenn etwas nicht geht: berichten und aufhören.** Wie bei Planets —
das war die richtige Reaktion und hat das Paket besser gemacht.