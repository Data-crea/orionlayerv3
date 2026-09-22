# Work order 165 — parked for Data

Der Auftrag sagt: jede getroffene Wahl kommt hierher, mit Begründung
und mit dem, was ihre Umkehr kosten würde. Dazu kommt, was der Lauf
nicht erledigen konnte.

---

## 0. DER GANZE LIVE-TEIL IST BLOCKIERT — und zwar von dir

Als der Lauf anfing, liefen orion2re (PID 35367) **und dein eigener
OrionLayer-Client** (PID 35712), seit 20:28 verbunden auf 17362.

Regel 8 des Standardblocks aus Work Order 126:

> *exactly one client on the server. Check for a running OrionLayer
> before you connect; if Data left his open, do NOT kill it — skip the
> live step and park it.*

Ich habe nichts angefasst. Damit fallen **Teil D und Teil E komplett**
weg und von **Teil A die Hälfte**, weil die zweite Quelle jedes Offsets
(Entscheidung 23, und die Q5-Regel dieses Auftrags wiederholt sie) ein
Live-Lesen ist.

**Was du tun musst, damit es weitergeht:** OrionLayer schließen (das
Spiel kann laufen bleiben) und Bescheid sagen. Die exakten Kommandos
für jeden geparkten Live-Schritt stehen unten.

---

## 1. Die Startregel aus 164 kostet mehr, als 164 wusste

Dieser Auftrag sagt „lies den Index, dann jeden `principles-` Teil und
die Entscheidungsteile, die diese Aufgabe berührt" — und nennt das
Lesebudget aus Work Order 127.

Das geht rechnerisch nicht auf: Index + drei `principles-` Teile +
die drei berührten Entscheidungsteile sind **137,6 KB**, gegen ein
Budget von 60 bis 80 KB. Das ist die Frage, die ich in 164 geparkt
habe, und 165 ist der erste Auftrag, der sie bezahlt.

**Gewählt:** weitergemacht, weil das Fundament in derselben Sitzung
schon vollständig gelesen war (für 162) und ein zweites Lesen das
Budget für null Erkenntnis ausgegeben hätte.

**Deine Entscheidung:** entweder wird die Pflichtlektüre kleiner —
z. B. nur *ein* `principles-` Teil ist Pflicht — oder das Budget wird
auf das angehoben, was die Regel tatsächlich verlangt. Eine Regel, die
in ihrem eigenen ersten Anwendungsfall nicht einhaltbar ist, ist keine
Regel, sondern eine Absichtserklärung.

---

## 2. ZURÜCKGEZOGEN — es ist kein Widerspruch, und der Baum sagt auch warum

Ich hatte hier notiert, Fundament und Baum widersprächen sich bei
Entscheidung 23: das Fundament sagt „live **oder** Header-Route", die
Werkzeuge im Baum nennen die Header-Route „exactly half of decision 23".

**Das war falsch gelesen, und `core/structs/unverified.py` sagt es
selbst**, in der Notiz zu `tech_applications` @379:

> *It is a whole `uint8_t[]` member and not a packed word, so the header
> route carries it end to end (decision 23's own limit does not bite
> here). … SOURCE TWO IS THE ONE THAT MATTERS and is not in: a live read
> whose values agree with the rows the game's own screen draws. The
> header says where the bytes are; only the screen says that these bytes
> mean "this row is offered".*

Das ist genau der zweite Absatz von Entscheidung 23 — *„a transcription
of MEANING is not a measurement of LAYOUT"*. Die Header-Route beweist
die **Lage** des Bytes; dass der Wert 1 „diese Zeile wird angeboten"
**bedeutet**, beweist nur der Bildschirm des Spiels. Beide Quellen sind
nötig, weil sie zwei verschiedene Dinge beweisen, nicht weil zweimal
dasselbe verlangt würde.

**Nichts für dich zu entscheiden.** Der Eintrag bleibt stehen, weil eine
zurückgezogene Feststellung sichtbar zurückgezogen wird und nicht
stillschweigend verschwindet — die Regel, die dieses Projekt sich für
Entscheidung 43 selbst gegeben hat.

---

## 3. Getroffene Wahlen

*(werden eingetragen, sobald die Teile gebaut sind)*

---

## 4. Geparkte Live-Schritte, mit exakten Kommandos

*(wird am Ende des Laufs gefüllt)*
