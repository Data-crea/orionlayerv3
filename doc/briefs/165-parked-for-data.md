# Work order 165 — parked for Data

Der Auftrag sagt: jede getroffene Wahl kommt hierher, mit Begründung
und mit dem, was ihre Umkehr kosten würde. Dazu kommt, was der Lauf
nicht erledigen konnte.

---

## 0. DRITTE SITZUNG: DER PORT WAR FREI, UND ES IST FAST ALLES DURCH

Du hast den Client geschlossen und den Push freigegeben. Was daraus
geworden ist, steht in `165-progress.md`; hier stehen nur die
**Entscheidungen** und das, was **geparkt** ist.

**Alle elf `SAVE*.GAM` sind byte-identisch mit dem Stand vor dem Lauf**,
SAVE10 und SAVE11 eingeschlossen. Es wurde nie gespeichert; die
Scratch-Slots wurden ausschließlich GELESEN.

**Was du geladen vorfindest: SAVE5 (Sternzeit 3509.1)**, weil dort der
letzte Wechsel gemessen wurde. Dein eigenes Spiel stand bei Beginn auf
Sternzeit 3500.3 mit 2 Spielern, 54 Sternen, 28 Koloniesätzen — und
`SAVE10.GAM`, der Autosave, hält genau diese Sternzeit. Zurückholen:

```bash
cd ~/orionlayerv3 && python tools/gameload.py load 10
```

Ich habe das **nicht** selbst getan: das Protokoll nennt Slot 4 und 5,
und das Laden jedes anderen Slots ist deine Entscheidung.

**Die neuen Commits sind NICHT gepusht.** Deine Freigabe galt den zwölf
Commits, die es beim Start gab (`57e3eda..f8d259a`, gepusht). Alles
danach wartet auf dein Wort.

---

## 0a. NACHTRAG, 23. September 2026 — der Hintergrund des Change-Modus

**Die Wahl fiel ohne Begründung auf die Alternative und ist auf deine
Entscheidung zurückgenommen.**

Der Auftrag stellte sie so: Default ein Panel über der eingefrorenen
HD-Galaxiekarte nach dem Muster des GAME-Menüs; Alternative *nur*, wenn
dieses Muster nicht trägt, ein eigener Bildschirm mit neutralem
Hintergrund, **markiert**. Gebaut wurde in der zweiten Sitzung die
Alternative — eigener Bildschirm, geteilte Cockpit-Textur. Dass das
Muster nicht getragen hätte, steht nirgends; die Wahl steht weder als
Markierung im Baum noch als Eintrag in dieser Datei, obwohl der Auftrag
beides verlangt. Sie war also keine Wahl, sondern ein Standardpfad, den
niemand als Wahl erkannt hat.

**Jetzt gebaut: der Default.** `IS_OVERLAY`, `OVERLAY_PARENT =
"galaxy_map"`, `OVERLAY_DIM = 0`; die Dispatcher-Sperre für Id 36 hält
das Panel, solange der Draht 36 meldet, und schließt es, sobald er es
nicht mehr tut; die Karte bekommt keine Eingabe, weil `dispatcher.top`
das Overlay ist. **Keine Markierung mehr nötig** — der Default ist das,
was das Original tut (`Draw_Mini_Main_Screen_`, mainscr_main.cpp:700-703).

**Und dabei ist ein Fehler aufgefallen, den nur das Hinsehen zeigt:**
das Panel füllte seine eigene Fläche nicht. Die Karte schien durch die
Zeilen. Das Original füllt `(s+4, 4)-(s+471, 472)` mit Palettenindex 0,
bevor es die Panel-Grafik darüber zeichnet (tech.cpp:290-291) — jetzt
transkribiert. Die erste Prüfung hätte es nicht gefunden: sie fragte
nur, ob die Seitenbänder gleich bleiben.

**Eine Beobachtung war hier notiert — der fehlende Exit-Knopf — und
sie ist am selben Tag erledigt** (Teil G, dein Auftrag darauf). Er wird
gezeichnet und angeklickt, an dem Rechteck, das der Draht meldet; ein
Klick sendet dasselbe wie ESC. Die Beschriftung ist Text und als
`exit_button_as_text` markiert, wie die Kategorienamen, bis das
Artwork kommt. Die nicht markierte Auslassung aus Teil B ist damit
weg — sie war die letzte.

---

## 0b. DIE ENTSCHEIDUNGEN DIESER SITZUNG

Jede mit dem, was ihre Umkehr kosten würde.

### Teil C, Q1/Q10 — Umfang: **beide Popups, in beiden Modi** (Default)

**Warum:** beide sind im Original reine Anzeige, beide hängen an
derselben Klasse, und das Original hat für beide EINE Implementierung.
**Umkehr:** eines von beiden wieder ausbauen — zwei Module und zwei
Markierungen. **Kosten:** die Abnahme dieses Auftrags fiele weg.

### Teil C, Q11 — der Radio-Index-Versatz: **HD öffnet die RICHTIGE Kategorie** (Default)

**Warum:** das Original indiziert `entries[input - first_btn_field]`,
während es Radios nur für nicht-leere Einträge gibt — es liest Daten,
die nie gesetzt wurden. Eine Transkription davon machte HD genau in dem
Fall falsch, in dem der Spieler es sieht.
**Umkehr:** eine Zeile in `open_list_at`, plus die Markierung.
**Kosten:** keine — beide Varianten sind eine Zeile.

### Teil C — voller gegen verbleibende Kosten: **transkribiert** (Default)

Verbleibend auf dem Eintrag, voll in der Beschreibung. Das ist die
Absicht des Originals (§3), kein Fehler, und die Prüfung verlangt, dass
die beiden Zahlen sich unterscheiden.

### Teil C — die Beschreibungsbox liegt im GEMEINSAMEN Hilfe-Panel

**Gewählt:** `core/helppopup.py` zeichnet sie, statt die 380 px breite
Box des Originals an fester x-Position nachzubauen.
**Warum:** dieselbe Sache — Titel und Körper eines Hilfe-Datensatzes —
und das Panel gibt es schon, samt Umbruch, Scrollen und Schließen.
**Umkehr:** eine eigene Box mit transkribierter Breite; die Höhe des
Originals hängt an seinen Font-Metriken und ist nicht transkribierbar.
**Kosten:** Markierung `description_box` müsste mitgehen.

### Teil E — der Namensvergleich statt des Id-Vergleichs

**Gewählt:** HD markiert die Zeile, deren NAME dem der laufenden
Anwendung entspricht, case-insensitiv — wie `strcasecmp` im Original.
**Warum:** es ist die Transkription. Bei eindeutigen Namen ist es
derselbe Vergleich wie vorher; bei zwei gleichnamigen Anwendungen
markiert das Original beide.
**Umkehr:** eine Zeile. **Kosten:** keine.

---

## 0c. GEPARKT — und jedes mit einer GEMESSENEN Begründung

### 1. Der Rest von Teil E (Work Order 131 B und C-live)

**131 Teil C live:** die sechs „alle bekommen alles"-Felder sind die
STARTFELDER, und beide Scratch-Saves haben alle sechs auf Status 3 —
erforscht. Live gelesen: `29:3, 55:3, 22:3, 57:3, 28:3, 23:3`. Der Fall
ist in SAVE4/SAVE5 **nicht erreichbar**; er braucht ein neues Spiel.

**131 Teil B:** die dritte Auswahl im SELECT-Modus und dessen fehlende
Auflösungen. Select Mode zu erreichen heißt: Zug beenden, dann den
Abschlussdialog wegklicken — und genau diese Konfiguration ist Open Fix
26. Dein Gegentest vom 19. September (echte Maus, kein Client) zeigt,
dass die Liste wartet. **Die eine Variable, die Select Mode benutzbar
macht, ist eine echte Maus im orion2re-Fenster**, und die hat eine
unbeaufsichtigte Sitzung nicht.

**Was du tun müsstest**, wenn du es willst: ein neues Spiel starten,
den Abschlussdialog mit der echten Maus wegklicken, dann sagen — die
Sitzung kann ab da mit `python tools/research_hd.py choose <entry> hd`
weitermachen.

### 2. Open Fix 26 — der eine zugestandene Versuch ist NICHT verbraucht

Der Auftrag gibt ihm „einen begrenzten Versuch: die Trennung der
Variablen und das Lesen des Injected-Click-Pfads". Die Trennung ist die
Hälfte, die entscheidet, und der „verbunden und still"-Lauf braucht
einen Abschlussdialog, der OHNE Client weggeklickt wird — was der
Auftrag selbst als möglicherweise nicht werkzeugbar bezeichnet und dann
dir zuweist. Er ist es. Ein Quellenlesen allein wäre eine Theorie ohne
Messung dagegen, und die Regel des Auftrags ist dann: parken.

**Nichts unter Open Fix 26 eingetragen**, weil nichts gelernt wurde,
was dort nicht schon steht. Ein Eintrag, der nur wiederholt, was der
vorige sagt, ist die Kopie, die veraltet.

### 3. Der Absturzfall aus 128

Braucht eine Liste mit einer LEEREN Kategorie. Change Mode bietet auf
SAVE4 und SAVE5 alle acht an. `python tools/research_hd.py crash` sagt
selbst, wenn der Fall nicht erreichbar ist.

### 4. `hyper_advanced_tech` @640 — unverändert offen

Acht Nullen in jedem erreichbaren Spiel. Der nächste Lauf in einer
späten Partie schließt es in einer Minute ab. Das Listen-Popup behandelt
es explizit: ohne zweite Quelle greift die Hyper-Auslassung **nicht**,
das Feld bleibt in der Liste — eine Liste, die still eine Zeile zu kurz
ist, ist der Fehler, den dieser Bildschirm schon einmal bezahlt hat.

---

## 0d. ERLEDIGT — der Live-Block der ersten Sitzung

**Steht stehen, weil eine erledigte Feststellung sichtbar erledigt wird
und nicht stillschweigend verschwindet** (dieselbe Regel wie §2 unten).
Der Port ist seit der zweiten Sitzung frei; alles, was hier blockiert
war, ist inzwischen gelaufen oder in §0c geparkt.

Als der erste Lauf anfing, liefen orion2re (PID 35367) **und dein
eigener OrionLayer-Client** (PID 35712), seit 20:28 verbunden auf 17362.

Regel 8 des Standardblocks aus Work Order 126:

> *exactly one client on the server. Check for a running OrionLayer
> before you connect; if Data left his open, do NOT kill it — skip the
> live step and park it.*

Ich habe nichts angefasst. Damit fallen **Teil D und Teil E komplett**
weg und von **Teil A die Hälfte**, weil die zweite Quelle jedes Offsets
(Entscheidung 23, und die Q5-Regel dieses Auftrags wiederholt sie) ein
Live-Lesen ist.

**Was zu tun war:** OrionLayer schließen. Getan. Die Kommandos in §4
unten sind damit Geschichte — was davon noch offen ist, steht in §0c.

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

## 2b. EIN OFFSET BLEIBT UNVERIFIZIERT, und das ist kein Versäumnis

`hyper_advanced_tech` @640 liest in deinem laufenden Spiel **acht
Nullen**. Der Header sagt, wo die Bytes liegen; was sie bedeuten, sagt
nur ein Wert, der nicht null ist. Niemand in dieser Partie hat ein
hyper-advanced Feld erreicht, also ist die Lesung ergebnislos — nicht
falsch, ergebnislos.

**Nichts zu entscheiden**, nur zu wissen: er bleibt in
`core/structs/unverified.py`, und der nächste Lauf in einem späten
Spiel schließt ihn in einer Minute ab.

---

## 3. Getroffene Wahlen

### Der Cost-Suffix als TABELLE im Code, nicht in `layout.json`

**Gewählt:** `COST_SUFFIX = {0: " RP", 1: " FP", 3: " RP", 4: " PR"}`
steht in `screens/research_select/screen.py`, und `layout.json` hat
seinen `cost_suffix` verloren.

**Warum:** `layout.json` ist laut Entscheidung 15 für die Wörter, die
**OrionLayer** besitzt. RP / FP / PR sind die Wörter des **Spiels**
(tech.cpp:631-639), gewählt von einem Byte auf dem Draht. Sie dort zu
lassen hieße, eine zweite Kopie einer Spielkonstante in unserer eigenen
Textdatei zu halten — genau die Kopie, die veraltet.

**Umkehr:** eine Zeile zurück in `layout.json`, eine Zeile im Screen.
**Kosten:** die Prüfung, die die Tabelle gegen die vier Fälle des
Originals hält, müsste mitgehen.

---

**Und die aus der ersten Sitzung:**

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
