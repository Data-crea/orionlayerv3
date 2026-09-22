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

**Nur eine, weil nur ein Teil gebaut werden konnte.**

### Die Q4-Prüfung als EIGENE Prüfung, nicht als dritte Zahl in der bestehenden

**Gewählt:** eine zweite `ok()` im selben Modul, statt 36 und 53 in die
vorhandene Parkprüfung (Screen 8) aufzunehmen.

**Warum:** Screen 8 ist das GAME-Popup, wo Feld 9 eine Ladeslot-Zeile
ist. Bei 36 und 53 ist Feld 9 eine **Auswahlzeile**, und deren Commit
liest den Mauszeiger des Spiels — ein dorthin gesendetes Parken wählt
also, worauf der Spieler gerade zeigt, oder dereferenziert null im
Spielprozess (Open Fix 23, als SIGSEGV in 128 C gesehen). Dieselbe
Wache, aber nicht derselbe Unfall; zwei Sätze im Lauf sagen das, einer
nicht.

**Umkehr:** zwei Zeilen — die zweite `ok()` löschen, die Ids in die
erste Prüfung aufnehmen, Zählerstand 250 -> 249 in beiden Dokumenten.

**Kosten, falls du es anders willst:** keine. Beide Varianten prüfen
dasselbe.

---

## 4. Geparkte Live-Schritte, mit exakten Kommandos

**Voraussetzung für alles hier: dein OrionLayer ist zu.** Das Spiel darf
laufen bleiben. Prüfen mit:

```bash
ss -tnp | grep 17362          # darf nur orion2re als LISTEN zeigen
pgrep -af "main.py"           # darf nichts zeigen
```

### A — die zweiten Quellen (Entscheidung 23)

Vier Offsets brauchen je ein Live-Lesen, das mit dem Bild des Spiels
übereinstimmt. Der Header-Teil ist für alle vier schon mechanisch
(`tools/struct_header_check.py` läuft in jedem Lauf):

| Offset | was das Live-Lesen beweisen muss |
|---|---|
| `tech_applications` @379 | Wert 1 heißt „diese Zeile wird angeboten" — gegen die Zeilen, die der Bildschirm des Spiels zeichnet |
| `hyper_advanced_tech` @640 | die Stufe, die als römische Ziffer erscheint |
| `current_research_application` @902 | die Anwendung, die das Spiel als laufend anzeigt |
| `s_settings.language` | das Byte, das RP / FP / PR wählt (tech.cpp:631-639) |

Erst wenn @379 und @640 beide Quellen haben, dürfen sie aus
`core/structs/unverified.py` heraus. Erst wenn `language` drin ist,
fällt die RP-Abweichung in `screens/research_select/` — der Auftrag
verlangt beides im selben Commit.

### B, C, D, E — der ganze Rest

Teil B (Change Mode) und Teil C (die beiden Popups) sind **offline
baubar**, aber ihre Abnahme ist es nicht: „row clicks and bare
activations both commit, **read back off the wire**". Teil D und Teil E
sind von Anfang bis Ende live.

Der fertige Startpunkt für die Live-Teile steht schon in
`doc/briefs/130-parked-for-data.md` und gilt unverändert:

```bash
cd "$HOME/Master of Orion 2" && \
    ~/orion2re/out/build/Linux/linux-debug/orion2re &
cd ~/orionlayerv3
python tools/research_hd.py newgame     # zur Karte, Zug eins
python tools/research_hd.py advance     # zum ersten Dialog
python tools/research_hd.py roomchoose 1 hd F4
python tools/research_hd.py crash       # wenn eine Kategorie leer ist
```

**Was der nächste Lauf zuerst tun sollte:** Teil A live abschließen. Er
ist der kleinste, er entsperrt die RP-Abweichung und die beiden
Promotions, und er ist die Voraussetzung dafür, dass Change Mode
überhaupt etwas anzeigen darf, wofür es einstehen kann.
