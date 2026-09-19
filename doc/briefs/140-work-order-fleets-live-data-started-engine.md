# Work Order 140: Fleets live, Engine von Data gestartet

## Zuerst

Diesen Auftrag unverändert als
doc/briefs/140-work-order-fleets-live-data-started-engine.md ablegen
und indexieren (Nummer am Index prüfen).

## Ausnahme für diesen Lauf

Data startet orion2re selbst aus seiner Desktop-Sitzung. Für diesen
Auftrag gilt das NICHT als „Datas eigenes orion2re läuft“: Der
Live-Teil läuft trotzdem. Datas OrionLayer läuft NICHT; OrionLayer
startet diese Sitzung mit dem Rezept aus CLAUDE.md. Bevor irgendetwas
verbindet: prüfen, dass kein anderer Client am Port 17362 hängt.
Hängt einer: STOPP.

Alle übrigen Live-Regeln unverändert: genau ein Client; SAVE1–9 und
SAVE11 vorher und nachher hashen, die Werte müssen identisch sein;
SAVE10 nur protokollieren; SAVE8 niemals anfassen; livesend liest vor
jedem Senden die Feldliste.

## Teil A: CLAUDE.md korrigieren

Die Diagnoseregel aus 139 E stimmt nicht. Richtigstellen:
- angehalten = Status T; S in rt_sigsuspend = der Prozess wartet
  selbst auf ein Signal, das ist kein Stopp von außen;
- Exit 128+n: n ist die Signalnummer nach `kill -l`; 144 ist Signal
  16 (SIGSTKFLT), nicht SIGUSR1 (10).
Die Ursache des Hängers in der Sandbox bleibt offen und wird als offen
eingetragen, nicht als geklärt.

## Teil B: Fleets live

Genau Teil F aus 139: Spielstand laden (nicht SAVE8), auf der
HD-Karte Fleets drücken, Start-, Wechsel- und Rückfall-Zeile wörtlich
festhalten, Feldliste zum Zeitpunkt von READY oder Rückfall, Screenshots
HD und Framebuffer Seite an Seite, RETURN, Karte, Hashes prüfen.
Keine Auswahl, kein Scrap, keine Bewegung. Die Engine NICHT beenden,
Data beendet sie selbst.

Ergebnis:
- READY: Renders gegen 137 legen und nennen, was live anders ist.
  Nichts weiter.
- Rückfall: Ursache mit Log-Zeile und Feldliste belegen,
  vorgeschlagene Korrektur mit Datei:Zeile, NICHT anwenden.

## Teil C: Nachfrage

Verdeckt die Rückfall-Einblendung bei 4:3 einen Teil des Spielbilds?
Wenn ja: benennen, nicht ändern.

## Abschluss

Frischer Klon, Smoke grün, pushen. Bericht mit den Log-Zeilen
wörtlich, Endstand von origin/main.
