# Work order 166 — parked for Data

Der Auftrag sagt: jede getroffene Wahl kommt hierher, mit Begründung
und mit dem, was ihre Umkehr kosten würde — 165 hat gezeigt, was
passiert, wenn eine Wahl stillschweigend fällt. Dazu kommt, was der
Lauf nicht erledigen konnte.

---

## Die getroffenen Wahlen

Jede mit dem, was ihre Umkehr kosten würde.

### A — die Schranke: `EMPTY_LIST_GRACE = 66` Frames

**Gewählt:** das Dreifache der gemessenen 22. Fünf Eintritte, jeder
genau 22 Frames von der Aktivierung bis zur gültigen Liste.
**Warum:** der Auftrag verlangt eine Schranke „aus den Aufnahmen
gemessen, mit Reserve". Drei Mal gibt einer langsameren Maschine oder
einer größeren Liste Luft, und ein Spiel, das 36 meldet und nie eine
Liste baut, landet trotzdem beim Bild — mit eigener Logzeile.
**Umkehr:** eine Zahl. **Kosten:** keine.

### A — ein wartendes Overlay zeichnet GAR NICHTS

**Gewählt:** `draws_this_frame()` ist False für ein Overlay im
Zustand `waiting`, also bleibt die HD-Galaxiekarte stehen. Select Mode
hat nichts darunter und zeichnet sein eigenes leeres Panel — die
Antwort des Fleets-Bildschirms auf denselben Moment (142 A).
**Warum:** die Worte des Auftrags („HD keeps drawing what it drew last
— here the HD galaxy map"). Die Alternative, das leere Panel sofort zu
zeigen und es füllen zu lassen, ist das, was Fleets tut.
**Umkehr:** eine Zeile. **Kosten:** keine — aber es ist eine Wahl über
das, was der Spieler sieht, und deshalb steht sie hier.

### B — Eckgröße 140, Rahmenmaßstab `0.5 * layout.scale`

**Gewählt:** 140 px Ecke (größter Eckwinkel 132 gemessen), und der
Maßstab ist halb der Fensterskala, weil die Fleets-Grafik die
1920x1080-Referenz in 2x ist. Bei 1080p ist eine Ecke 70 px, bei
3840x2160 ist sie 140 — die Originalgröße der Grafik.
**Warum:** Ecken, die mit dem Fenster skalieren statt fix oder
achsenweise gedehnt zu sein. Keiner der beiden vorhandenen
Nine-Slicer im Baum tut das.
**Umkehr:** zwei Konstanten. **Kosten:** die Prüfung, die die Lampen
misst, müsste mitgehen.

### C — Füllung und Umriss kommen vom Planets-Bildschirm

**Gewählt:** `colony_summary.panel_background` und
`panel.thin_border`, gelesen aus den Abschnitten, denen sie gehören.
**Warum:** die beiden Bildschirme sollen wie ein System aussehen, und
eine zweite Kopie einer Farbe ist die Kopie, die veraltet.
**Umkehr:** zwei Zeilen und ein eigener Abschnitt in `colors.json`.
**Kosten:** die Prüfung, die die beiden gleich hält, müsste weg.

### D — die gezeichnete Box ist der INHALT plus 4 px — **auf 2 korrigiert, Nachtrag**

**Diese Wahl ist überholt.** Data hat sie live gesehen und den Nachtrag
geschrieben: 4 px lassen zwischen den Spalten genau 1 px, und das liest
sich als eine breite Box mit einer Naht, nicht als zwei Boxen.
`BOX_MARGIN = 2` — die Spalten stehen 5 native px auseinander, CANCEL
hat 4 px unter der unteren Boxenreihe, und der Text liegt weiter mit
Rand in seiner Box (die Prüfung aus 166 D ist grün geblieben).
**Warum der Default und nicht eine breitere Box:** Data hat ihn im
Nachtrag benannt — weniger Rand um den Inhalt statt mehr Platz für die
Box. **Umkehr:** eine Zahl. **Kosten:** die Regel „Boxen und Knopf
halten 3 native px Abstand" in `080k` geht bei 4 rot, und das ist
genau der Fall, den der Nachtrag beanstandet hat.

Der Text darunter ist die ursprüngliche Begründung und bleibt stehen,
weil die Rechnung stimmt und nur die Schlussfolgerung falsch war: 9 px
sind das Budget, und 4+4 füllt es ganz aus.

### D — die gezeichnete Box ist der INHALT plus 4 px (ursprünglich)

**Gewählt:** nicht das Blockfeld des Spiels, sondern die Zeilen plus
4 native px. Das Blockfeld bleibt, was es ist: das Feld des Spiels.
**Warum:** die Zeilen und die Textanker sind transkribiert, das
gezeichnete Kästchen ist es nicht — das Original malt seine Felder in
die TECHSEL-Grafik. Entscheidung 53: was wir gewählt haben, ist deins.
**4 ist das Maximum**: zwischen Zeilenende (313) und nächstem Eintrag
(322) liegen 9 px.
**Umkehr:** eine Zahl. **Kosten:** bei 5 berühren sich die Spalten.

### D — die Kopfwörter bleiben ÜBER der Box

**Gewählt:** Kategoriename und Kosten stehen weiter bei `y + 2`, also
oberhalb des Kästchens; HD zeichnet dort keine eigene Kopfplatte.
**Warum:** beide Anker sind transkribiert (tech.cpp:683-706), und das
Original hat dort eine Platte in der Grafik, die HD nicht hat. Eine
erfundene Kopfplatte wäre eine zweite Abweichung.
**Umkehr:** eine Box mehr je Eintrag. **Kosten:** deine Entscheidung,
ob der Kopf eine Platte bekommen soll — das ist Artwork.

---

## Geparkt

### Select Mode ist nur offline geprüft

Jede Regel dieses Auftrags gilt für beide Modi und ist für beide
offline geprüft. **Live gesehen ist nur Change Mode**, weil Select Mode
(53) am Turn-Start hängt und Open Fix 26 dort eine echte Maus
verlangt. Der Auftrag nimmt das ausdrücklich aus.

**Eine Einschränkung, die daraus folgt und die du wissen solltest:**
Teil A unterscheidet „noch nicht" von „falsch" an einer **leeren**
Feldliste, und das ist, was bei 36 gemessen wurde. Kommt Select Mode
mit einer FREMDEN, nicht-leeren Liste herein — wie der Fleets-Bildschirm
es bei Screen 4 tut —, greift die Regel dort nicht und der Fallback
blitzt weiter auf. Das ist nicht messbar ohne deine Maus, also ist es
nicht geraten worden.


---

## Nachtrag zu 166 — die Wahlen, die er offen gelassen hat

### Die Bandhöhe wird abgeleitet, nicht gesetzt

**Gewählt:** `BAND_H = ROW_Y2[1] - ROW_Y1[1] + 1` (= 15) in
`core/researchlist.py`, nicht eine getippte 15.
**Warum:** der Nachtrag sagt „bei allen Zeilen gleich hoch", und die
Höhe, die alle Zeilen schon haben, ist die der Zeilen 1 bis 3 aus der
transkribierten Tabelle. Eine getippte Zahl wäre eine zweite Kopie
davon — und die Kopie ist die, die veraltet.
**Umkehr:** eine Zeile. **Kosten:** die Prüfung hält `BAND_H` gegen die
Tabelle, die müsste mitgehen.

### Das Band beginnt auf der Beschriftungszeile, nicht 5 px darunter

**Gewählt:** Oberkante = `app_label_y[row]`, also genau die Zeile, in
der die Anwendung steht.
**Warum:** `Draw_Little_Arrow_` setzt die Pfeilspitze auf
`app_label_y[i] + 5` und den Stamm bis `app_label_y[0] - 3`
(tech.cpp:740-775) — die Markierung des Originals umfasst die
Beschriftungszeile, sie sitzt nicht darunter. Ein Band, das 5 px tiefer
anfängt, würde die Spitze treffen und die Zeile halb stehen lassen.
**Umkehr:** eine Konstante. **Kosten:** die Regel „kein Band schneidet
die Feldüberschrift" bliebe grün, die Zeile sähe nur falsch aus — das
ist der Fall, in dem eine Prüfung nichts sagt und ein Bild alles.

### 3 native px sind der Boden für „sichtbar Abstand"

**Gewählt:** die neue Regel verlangt 3 native px zwischen je zwei Boxen
und zwischen Box und CANCEL.
**Warum:** der Nachtrag sagt „sichtbar", und eine Zahl ist das, was
eine Prüfung halten kann. 3 native px sind bei 1920x1080 neun
Fensterpixel; `BOX_MARGIN = 4` lässt 1 und geht rot, was genau der Fall
ist, den du beanstandet hast.
**Umkehr:** eine Zahl. **Kosten:** unter 3 hält die Regel nichts mehr,
was ein Auge nicht auch sieht; darüber wird die Box enger als der Text
erlaubt, und dann geht die Prüfung aus 166 D rot statt dieser.

### Die Aufnahmen entstehen im Vollbild, nicht im Fenster

**Gewählt:** `tools/research_hover_hd.py` schaltet für jede der vier
F9-Auflösungen ins Vollbild.
**Warum:** ein Fenster bekommt nicht die Größe, die es verlangt — der
Compositor hat hier aus 1440 px Höhe 1371 gemacht, und eine Aufnahme,
die du dir ansehen sollst, muss die Auflösung haben, die in ihrem Namen
steht. Im Vollbild ist die Inhaltsfläche die des Presets
(main.py:501-529).
**Umkehr:** die F11-Tastendrücke weglassen. **Kosten:** drei statt vier
Auflösungen, und zwei davon mit falschem Namen.
