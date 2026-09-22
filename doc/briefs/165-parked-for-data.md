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

## 2. Ein Widerspruch zwischen Fundament und Baum (Entscheidung 23)

Beim Ansehen von Teil A gefunden, **nicht repariert**, weil ein
Widerspruch laut 164 geparkt und nicht aufgelöst wird:

- **Das Fundament sagt ODER.** Entscheidung 23: *"Verification means
  numeric agreement with live data via `tools/struct_probe.py`, **or**
  compiling orion2re's own header … and matching the assert in
  `sizes.h`."*
- **Der Baum sagt UND.** `tools/struct_header_check.py` nennt sich
  selbst *"exactly half of decision 23"*, und `core/structs/
  unverified.py` hält `tech_applications` @379 zurück mit der
  Begründung, *"ONE of its two sources is in"*.

Nach dem Fundament wäre @379 längst verifiziert; nach dem Baum nicht.
Dieser Auftrag entscheidet es für sich selbst (Q5: „two sources per
offset"), also habe ich mich an den Baum gehalten — aber das Fundament
sagt weiterhin etwas anderes, und es ist die Datei, die eine neue
Sitzung zuerst liest.

**Deine Entscheidung:** entweder das Fundament schärfen (zwei Quellen,
und die Header-Route allein reicht nie) oder den Baum lockern. Es zu
ändern kostet einen Satz — aber es ist ein Fundament-Eintrag, und die
darf ich laut Auftrag nicht selbst anlegen.

---

## 3. Getroffene Wahlen

*(werden eingetragen, sobald die Teile gebaut sind)*

---

## 4. Geparkte Live-Schritte, mit exakten Kommandos

*(wird am Ende des Laufs gefüllt)*
