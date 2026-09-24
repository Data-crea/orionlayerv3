# Work order 167 — parked for Data

Der Auftrag sagt: offene Fragen und Wahlen kommen hierher, jeweils mit
dem gewählten Default, damit der Lauf weitergehen kann; dazu alles aus
dem Inventar, was nicht gebaut wurde, mit Grund. Jede Wahl mit dem, was
ihre Umkehr kosten würde.

---

## P0 — „Clone per CLAUDE.md (full tree)"

**Gewählt:** gearbeitet im vollständigen Arbeitsbaum
`/home/data/orionlayerv3` — ein kompletter Klon von `origin/main` mit
allen generierten und extrahierten Dateien, derselbe Baum, in dem 164,
165 und 166 committet haben. CLAUDE.md nennt keinen eigenen
Klon-Schritt. **Warum:** der Auftrag berührt Artwork, das nur ein Baum
mit extrahierten Spieldateien zeigen kann, und die Commits sollen lokal
bleiben. **Umkehr:** die Commits in einen frischen Klon holen
(`git fetch /home/data/orionlayerv3 main`). **Kosten:** keine.

**Nebenbefund:** Deine eigene OrionLayer-Sitzung (`python main.py`,
gestartet 19:56) lief während des Laufs aus genau diesem Baum und hielt
die eine erlaubte Verbindung zu orion2re. Dazu Punkt L unten.

---

## W — Open fix 30: go / no-go (Data)

**Was:** `doc/ext_officer_screen_state.patch` hängt einen Block `"OFFS"`
an den Snapshot, nur solange Screen 29 aktiv ist: Ansicht, Button-Modus,
Auswahl, angezeigter und gewählter Stern, der Stack der Schiffsansicht
mit seinen Schiffen und deren Auswahl, die Scroll-Zeile, und — solange
das Anheuer-Popup über diesem Screen läuft — dessen Anführer und Zustand.
Eintrag in `doc/orion2re_open_fixes.md` Punkt 30.

**Gezeigt, und nur das:** der Patch lässt sich auf `src/ext/ext_api.cpp`
bei `e6199966` anwenden (`patch --dry-run`), die gepatchte Datei
kompiliert mit den Flags aus dem Build (`-fsyntax-only`, pch, 
`ORION2RE_EXT`), eine absichtlich falsche Variante wird abgelehnt. **Nicht
angewendet, nicht gelaufen.** orion2re wurde nicht angefasst.

**Default bis zur Entscheidung:** HD liest den Block, wenn er da ist
(`core/game_state.officer_screen`, geprüft in 090b), und zeichnet sonst
einen markierten Platzhalter. Ohne ihn schickt HD nur, was es danach auf
dem Draht sehen kann (Tabs, HIRE, CANCEL, RETURN, Klick auf einen zu
heuernden Anführer, die Popup-Antworten, native Boxen, Rechtsklick auf
ein Porträt). POOL, DISMISS, PREV / NEXT, Zuweisen und die Galaxie-Box
bleiben stumm — ein Klick auf einen Anführer im Pool- oder Dismiss-Modus
HANDELT (officer.cpp:1415-1438), und den Modus sieht HD ohne den Block
nicht.

**Nach einem Go:** anwenden (Zeile im Patch-Kopf), `OFFS` in
`tools/version_check.py` aufnehmen, und live: die Zustände des Blocks
gegen das Originalbild eines Scratch-Spielstands.

## X — Befund außerhalb des Screens: die gemeinsame String-Extraktion schneidet Leerzeichen ab

`tools/estrings_extract.decode` (auch von `hestrings_extract` benutzt)
ruft `.strip()`. Gemessen gegen die Rohbytes der LBX-Dateien: **32
HESTRNGS- und 96 ESTRINGS-Einträge** verlieren führende oder
abschließende Leerzeichen, darunter `", the "` (0x110, 0x182),
`"%s Fleet: "` (0x131), die Familie `"%d Outpost, "` … `"%d Colony
Ships, "` (0x102-0x107), `"Stardate: "`, `"  no"` (0x10A). Auf dem
Leaders-Screen sichtbar als „Slith, theRebel Pilot".

**Was dieser Auftrag getan hat:** nur die eine Stelle auf dem
Leaders-Screen (`ldrrows.the_word`) setzt das fehlende Leerzeichen
zurück, und nur wenn es fehlt — ein Workaround, der von selbst verfällt,
sobald der Extraktor die Bytes behält. `"  no"` bleibt ohne seine zwei
führenden Leerzeichen (die Kosten-Spalte steht dadurch ein wenig links).
**Nicht geändert:** der Extraktor selbst, weil das die Texte aller
anderen Screens verschiebt (Fleets, Planets, Galaxy Map) — das ist ein
eigener Auftrag. **Vorschlag:** `decode` ohne `strip`, Format-Version
beider Loader erhöhen, einmal neu extrahieren, die anderen Screens
gegen das Original ansehen.

## L — Live-Test und Beweisbilder: nicht gelaufen

(wird am Ende des Laufs ergänzt)

## Nicht gebaut, aus dem Inventar (Teil A), jeweils mit Grund

| Inventar | Grund | was HD stattdessen tut |
|---|---|---|
| Rahmen OFFICER.LBX 0 (A3) | der Auftrag: kein äußerer Rahmen | schwarz, innere Boxen im Code |
| Systemanzeige der Kolonie-Ansicht: Stern- und Planetenbilder (A2) | die Bilder sind nicht extrahiert; der angezeigte Stern ist ohne open fix 30 nicht auf dem Draht | Platzhalter; mit dem Block: Sternname und Planeten-Slots als Wörter |
| Große Schiffs-Icons der Schiffs-Ansicht mit Auswahl, Scroll-Daumen (A2) | ohne open fix 30 nicht auf dem Draht; der Scroll-Daumen (`Draw_Generic_Vertical_Scroll_Bar_`) nicht gebaut | Platzhalter; mit dem Block: Schiffsbild (Fleets-Extraktion), Name, Auswahlrahmen |
| POOL / DISMISS / Zuweisen / PREV / NEXT (A4, A5) | brauchen den Modus bzw. den Stern/Stack — open fix 30 | gezeichnet, schicken nichts |
| Galaxie-Box: Zielfahrt-Linien (`Draw_Fltscrn_Ship_Destination_Lines_(29)`), das blinkende Icon des gewählten Stacks (A3) | nicht gebaut; das blinkende Icon braucht den Stack (open fix 30) | Sterne und Stack-Icons, keine Linien |
| Streifen unter der Galaxie-Box (`Print_Galmap_Scanned_Ship_`, A3) | beschreibt den Stack unter dem Zeiger DES SPIELS; die Schiffszählung nach Rumpf ist nicht gebaut | bleibt leer |
| Streifen unter der View-Box, Schiffs-Ansicht (A3) | der „gescannte" große Schiff-Icon ist ohne Block nicht bekannt | leer; Kolonie-Ansicht mit Block: Sternname + Anführer + ETA |
| Rechtsklick auf ein großes Schiffs-Icon → Detailansicht (A5) | `CMBTDRW1::Detailed_View_Ship_` ist ein eigener Screen | nicht gebaut; mit Block ginge der Klick ans Spiel |
| Klicks in die Systemanzeige → „REPORTS phase" (A5) | ohne Systemanzeige kein Ziel | — |
| Hover-Streifen (Stern / kleines Schiff unter dem Zeiger, A5) | der Zeiger des Spiels ist nicht auf dem Draht; HD-eigener Hover nur für die Zeilen gebaut | Zeile unter dem Zeiger wird hervorgehoben und im Anheuer-Modus bepreist |
| Getimte Textbox „Transfering display to …" (A6) | teilt mit der Warnbox das eine ESC-Feld (textbox.cpp:249), liegt aber woanders (x 130, 380 breit, Höhe nach Text, textbox.cpp:40-88) — `core/gamebox` erkennt sie als Warnbox und zeigt **den falschen Ausschnitt**. Bekannte Lücke; die Box schließt sich nach 15 Ticks selbst (officer.cpp:3214-3218) | Crop des Warnbox-Rechtecks, ehrlich: falsch; Abhilfe wäre das Rechteck aus dem Framebuffer zu bestimmen oder open fix 29 |

## Die Wahlen dieses Laufs (Default, Grund, Umkehr)

### C1 — Innere Boxen: Füllung + Plate, wie die Forschungs-Screens (166 C)
**Gewählt**, weil 166 genau diese Frage für die Forschung so entschieden
hat. Die View-Box trägt die Original-Kunst (OFFICER.LBX 1 / 2), wo sie
extrahiert ist. **Umkehr:** eine Funktion (`ldrdraw.draw_frame_boxes`).

### C2 — Schriftgrößen aus dem Zeilenabstand des Originals
`ldrdraw.NATIVE_TEXT` (Name 10, Kosten 7, Status 8, Skill 9, … native px)
und auf die Breite des Originals geschrumpft. **Umkehr:** eine Tabelle.
Die Größe der Kosten-Spalte (7) ist die kleinste, die zwei Zeilen in die
Höhe einer Namenszeile bringt.

### C3 — Sprites: ganzzahlig für Porträts / Icons / Sterne, exakt nearest-neighbour für Buttons und Box-Kunst
Porträts wie die Fleets-Regel (decision 28); Buttons und Box-Kunst
exakt auf ihr natives Rechteck, damit die gemalten Zellen unter den
Feldern liegen. **Umkehr:** zwei Funktionen (`magnified`, `stretched`).

### C4 — Die Skill-Hilfe zeichnet HD selbst (DEVIATION `hd_skill_help`)
Der Text ist vollständig bekannt und ändert nichts im Spiel; die
Spiel-Box würde das Spiel in eine modale Schleife schicken. **Umkehr:**
den Rechtsklick auf der Skill-Zeile an das Spiel schicken (`cancel_field`
auf das Skill-Hilfefeld) und die Box über `fltbox` zeigen.

### C5 — Das Anheuer-Popup zeichnet HD, wenn der Anführer eindeutig ist
Erkennung über die exakten Rechtecke der Skill-Hilfefelder (Spezial-
Skills beginnen 1 px höher als allgemeine); ohne Eindeutigkeit die Pixel
des Spiels. **Umkehr:** immer den Crop.

### C6 — WAITING zeichnet den Screen aus den Datensätzen
und schickt nichts, Schranke 66 Snapshots (166 A gemessen, für Leaders
nicht gemessen — L). **Umkehr:** eine Zahl.

### C7 — Hintergrund schwarz
wo das Original OFFICER.LBX 0 malt. **Umkehr:** eine Zeile.
