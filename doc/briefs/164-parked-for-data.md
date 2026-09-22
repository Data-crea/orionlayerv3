# Work order 164 — parked for Data

Zwei Entscheidungen, die ich getroffen habe und die dir gehören, und
eine Sache, die ich **nicht** getan habe, weil der Auftrag es verbietet.

---

## 1. Die Präambel steht noch wörtlich da — und das war meine Wahl

Ganz oben in `doc/v3_fundament.md` steht weiterhin, unverändert:

> Read this before touching the code.

Direkt darunter steht jetzt die neue Startregel. Beide stimmen: „read
this" heißt jetzt „lies den Index", und die Regel darunter sagt, wie es
weitergeht.

**Warum ich sie nicht umgeschrieben habe:** die harte Vorgabe lautet
„der Text ändert sich nicht", und wenn die Präambel unangetastet bleibt,
deckt der Byte-für-Byte-Beweis die **ganze** Datei ab statt alles außer
den obersten dreizehn Zeilen. Hätte ich den Satz ersetzt, wäre der
Beweis schwächer geworden — für einen Satz, der nicht falsch ist.

**Deine Entscheidung:** soll der Satz weg oder umformuliert werden,
sage es, dann fällt er in einem eigenen Schritt, mit einem Diff von
genau einer Zeile. Der Beweis ist dann schon erbracht und braucht nicht
noch einmal die ganze Datei.

---

## 2. Die Arbeitsprinzipien sind 62 KB, und die werden jetzt immer gelesen

Die Startregel sagt „und immer jeden `principles-` Teil". Das sind drei
Teile mit zusammen **62,3 KB**; mit dem Index kommt eine Sitzung auf
**66 KB** Pflichtlektüre, gegen 195 KB vorher.

Das ist eine echte Verbesserung — aber es sind immer noch 66 KB von den
80 KB, die Work Order 127 für **eine** Sache vorsieht, bevor der
eigentliche Aufgaben-Teil dazukommt.

**Was ich nicht tun durfte:** kürzen. Der Text darf sich nicht ändern,
also ist 62 KB die ehrliche Zahl und keine, an der ich drehen konnte.

**Deine Entscheidung:** soll wirklich *jeder* `principles-` Teil immer
gelesen werden, oder reicht als Pflicht einer davon — und wenn einer,
welcher? `08-principles-diagnosis-and-refactoring.md` (25 KB) ist der
Teil, dessen Regeln am häufigsten gebrochen wurden; `07-principles-
delivery.md` (11 KB) ist der, der die Arbeitsteilung zwischen dir und
einer Sitzung regelt.

---

## Widersprüche im Text

**Keine gefunden — und das ist eine schwächere Aussage, als sie
aussieht.** Der Schnitt läuft entlang der Überschriften, die das
Dokument schon hatte; ich habe den Text dafür nicht Satz für Satz
gelesen und behaupte deshalb nicht, dass keiner drin ist. Was ich
sagen kann: beim Aufteilen ist keiner aufgefallen.

---

## Später

Nichts. Work Order 164 verschiebt Text und hinterlässt keine halbe
Arbeit.
