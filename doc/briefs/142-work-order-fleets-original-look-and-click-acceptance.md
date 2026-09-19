# Work Order 142: Kein Aufblitzen, Feld 0 zentral, Debug-Eingabe, Fleets im Look des Originals, Klick-Abnahme

## Zuerst

Diesen Auftrag unverändert als
doc/briefs/142-work-order-fleets-original-look-and-click-acceptance.md
ablegen und indexieren (Nummer am Index prüfen).

Pflichtlektüre: doc/v3_fundament.md (besonders 18, 26, 29, 38 und
die Grundsätze zu Artwork und Messung), CLAUDE.md, Berichte 138–141,
doc/briefs/134-parked-for-data.md, Briefs 54–57 (RACEICON-Extraktion
und Palette).
orion2re nur lesen und bauen, keine Patches.

Reihenfolge: A, B, C, D (je eigene Commits, Smoke grün, Rot/Grün
gezeigt), dann E live. Push am Ende nach frischem Klon.

## Teil A: Kein Aufblitzen beim Öffnen

Befund: Der erste Snapshot nach dem Öffnen trägt Screen-ID 4, aber
noch die Feldliste der Karte. Der Fleets-Screen wertet das als
FOREIGN_FIELDS und zeigt kurz das Original.

1. Neuer Zustand WAITING: Die Feldliste stammt noch nicht vom
   Fleets-Screen. Erkennungsmerkmal ist das Fangfeld (0,0,639,479)
   Typ 7 (flt1.cpp:1261). Fehlt es, hat Fleet_Screen_ seine Liste
   noch nicht gebaut. Das Merkmal im Bericht mit Quelle bestätigen.
2. WAITING zeigt nicht das Original: HD bleibt auf seinem eigenen
   Bild, sendet nichts, und der Zustand endet ereignisgesteuert,
   sobald die Liste da ist (Entscheidung 21). Kein Timer.
3. FOREIGN_FIELDS gilt nur noch, wenn die Fleets-Liste da ist und
   zusätzlich fremde Felder hat (der echte Box-Fall).
4. Smoke-Check: Kartenliste mit Screen 4 → WAITING, kein
   wants_original, nichts gesendet; dann Fleets-Liste → READY;
   Fleets-Liste plus die zwei Felder aus gendraw.cpp:172-173 →
   FOREIGN_FIELDS. Mit Feld 0 in jeder Liste.

## Teil B: Feld 0 zentral

Der Vorschlag aus 141 C ist freigegeben: Feld 0 in
core/game_state.parse_fields wegfiltern. Indizes bleiben die der
Engine. Die Einzelfilter in den Verbrauchern bleiben stehen, sie
schaden nicht. Smoke-Check: Rohliste mit Feld 0 → es kommt nicht an;
ext_diag sieht es weiterhin. Dazu ein Check für den Planets-Fall aus
141 C: Feld 0 mit ESC-Hotkey → _return sendet nicht ACTIVATE_FIELD 0.

## Teil C: Debug-Eingabe

Der Vorschlag aus 141 E ist freigegeben, wie beschrieben: Unix-Socket
unter $XDG_RUNTIME_DIR, nur mit ORIONLAYER_DEBUG_INPUT, Dateirechte
0600 (geprüft), pygame.event.post vor der normalen Schleife, eine
Log-Zeile beim Öffnen, Markierung TOOL. Smoke-Check für beide
Zustände, erzwungen. Maus-Koordinaten sind Fensterkoordinaten, die
denselben Weg wie ein echter Klick nehmen (Entscheidung 5).

## Teil D: Fleets im Look des Originals

Data will den Fleets-Screen so, wie das Original ihn zeigt: schwarze
Karte, die Originalgrafiken, die Farben des Originals. Die
HD-Knöpfe bleiben, aber in den Farben des Originals.

### D1: Originalgrafiken aus Datas Installation

1. Für jede Grafik zuerst die Funktion lesen, die sie im Original
   zeichnet, und im Bericht nennen, mit Datei:Zeile, LBX-Datei und
   Eintrag:
   - Schiffsbild in der Rasterzelle (ken.cpp:451-466 und SHIPS.LBX);
   - Zellplatte des Rasters (blaue Platte mit Kreisen);
   - Sterne der Inset-Karte, nach Klasse (farbige Kreuze), sowie
     alles Weitere, was das Original im Inset zeichnet (Schiffs-
     Stacks, Ringe, Nebel), mit der jeweiligen Zeichenfunktion.
2. Wie färbt das Original Schiffe (Spielerfarbe) und Sterne? Palette,
   Remap-Tabelle oder eigene Sprites je Farbe? Mit Quelle. HD macht
   es auf dieselbe Weise (Entscheidung 29 sagt: nie gebacken).
3. Extraktion wie bei HELP.LBX (Entscheidung 38): ein Werkzeug liest
   aus Datas Installation, reicht die Daten unverändert weiter, und
   decodiert wird zur Ladezeit. Das vorhandene LBX- und
   Palettenwerkzeug aus Briefs 54–57 wiederverwenden, keine zweite
   Kopie. Erzeugte Dateien werden NIE committet und NIE
   ausgeliefert; der bestehende Smoke-Check gegen Engine- und
   Spieldaten im Baum muss sie abdecken, sonst erweitern.
4. Fehlen die Dateien, fällt der Screen auf die heutige Darstellung
   zurück (Farbblock plus Name), und ein Hinweis sagt, wie man
   extrahiert. Das ist ein Zustand, den man erklärt, kein Fehler.
   Smoke-Check für beide Fälle, erzwungen, nicht von der Platte
   abhängig.
5. Die Auslassung „Schiffsbild“ wird mit vorhandenen Dateien
   aufgehoben: Markierung und Check entsprechend anpassen.
6. Größen: Die Sprites werden nach Stufen gewählt, nicht skaliert
   (Entscheidung 28). Gibt es nur eine Größe, die ganzzahlige
   Vergrößerung wählen, die in die Zelle passt, und das als
   HD EXTENSION markieren. Keine Größe aus der Grafik ablesen
   (Grundsatz „An asset is not a measurement“).

### D2: Die Inset-Karte

1. Schwarzer Hintergrund wie im Original, kein durchscheinendes
   Cockpit-Muster.
2. Sterne, Stacks und was das Original sonst zeigt, mit den Grafiken
   aus D1, an den Positionen, die das Original aus dem Snapshot
   berechnet (Box_Fleet_Screen_Scanned_Star_ bzw. die Zeichenfunktion
   aus D1.1). Fehlt etwas auf dem Draht: benennen, nicht erfinden.
3. Der Hinweis „Map view is the game's…“ verschwindet aus der Mitte.
   Die Auslassung (Klicks ins Inset sind nicht gebaut) bleibt im Code
   markiert. Auf dem Schirm steht, wenn überhaupt, ein vollständig
   lesbarer, kurzer Hinweis am Rand der Karte, nie über Sternen.
   Wortlaut in JSON.

### D3: Farben des Originals

1. Die Farben des Fleets-Screens aus der Palette des Spiels nehmen:
   Rasterplatten (falls nicht als Grafik aus D1), Scrollbalken,
   Filter-Radios (an/aus), Knöpfe, Rahmenlinien und Schrift.
   Die Werte kommen aus der Palette mit Palettenindex und
   Quelle in einer Tabelle, nicht vom Screenshot abgelesen
   („Numerically verify, never estimate visually“).
2. Über palette.col und das bestehende Palettensystem, damit
   Skin-Wechsel und die farbenblinden Paletten (Briefs 103–106)
   weiter greifen. Geht das für eine Farbe nicht: benennen.
3. Die Filter-Radios zeigen ihren Zustand aus dem FLTS-Block
   (support, combat), wie im Original blau hinterlegt, wenn an.

### D4: Die Statuszeile

„Hover a stack in the game window“ verweist auf ein Fenster, das der
Spieler in HD nicht sieht. Aus den Quellen klären, was das Original
dort bei nichts Überfahrenem zeigt (laut Original-Screenshot: leer),
und genau das tun. Die Auslassung aus 137 E5 bleibt markiert.

### D5: Renders

Alle vier Auflösungen, mit und ohne extrahierte Grafiken, nach
~/orionlayer-fixtures/evidence/work_order_142/. Dazu eine
Gegenüberstellung Original gegen HD aus einem Live-Snapshot aus
Teil E.

## Teil E: Klick-Abnahme live (ohne Zerstörung)

Data startet nur orion2re. Ausnahme und Regeln wie in 140:
genau ein Client, Hashes (SAVE1–9, SAVE11 identisch; SAVE10 nur
protokollieren), SAVE8 nie, livesend liest die Feldliste, Engine nicht
beenden. OrionLayer startet diese Sitzung mit
ORIONLAYER_DEBUG_INPUT, alle Eingaben über den Socket aus C.

1. Spielstand laden (nicht SAVE8), HD-Karte.
2. Fleets per HD-Klick auf den Knopf. Erwartet: WAITING, dann READY,
   kein Original-Bild dazwischen. Log-Zeilen wörtlich.
3. Eine Zelle auswählen und wieder abwählen. HD und Framebuffer
   stimmen überein. SCRAP wird hell und wieder gedimmt.
4. Einen Filter umschalten und zurück. Der Zustand in HD folgt dem
   Spiel.
5. RETURN per HD-Klick.
6. Auf der Karte: Die Stacks sitzen dort, wo das Original sie
   zeichnet, und ein Klick auf einen Stack öffnet die Box dieses
   Stacks (Evidence 8, an den Schiffen der Box geprüft). Seite an
   Seite gegen den Framebuffer.
7. Hashes prüfen.
KEIN Scrap, keine Bewegung, keine Relocation. Scrap bekommt einen
eigenen Lauf.
Weicht etwas ab: belegen, Korrektur vorschlagen, NICHT anwenden.

## Abschluss

Frischer Klon, Smoke grün, pushen. Schlägt die Prüfung fehl: selbst
reparieren, erneut prüfen, pushen. Upload-Sperre unverändert. Keine
extrahierten Spieldaten im Commit.

## Bericht

- A–D: Stellen, Quellen, Smoke-Nummern, Rot/Grün, Render-Pfade.
- D1: Tabelle der Grafiken (Zeichenfunktion, LBX, Eintrag,
  Färbung).
- D3: Tabelle der Farben (Element, Palettenindex, Quelle).
- E: Log-Zeilen wörtlich, Ergebnis je Schritt, Screenshots.
- Endstand von origin/main.
