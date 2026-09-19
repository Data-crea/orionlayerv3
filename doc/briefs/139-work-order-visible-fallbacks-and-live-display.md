# Work Order 139: Rückfälle sichtbar machen, Display für Live-Läufe, Fleets live

## Zuerst

Diesen Auftrag unverändert als
doc/briefs/139-work-order-visible-fallbacks-and-live-display.md
ablegen und indexieren (Nummer am Index prüfen).

Pflichtlektüre: doc/v3_fundament.md, CLAUDE.md, Bericht 138,
doc/briefs/134-parked-for-data.md.
orion2re nur lesen und bauen, keine Patches.

## Worum es geht

138 hat gezeigt: Der HD-Fleets-Screen wird aktiv, meldet
wants_original(), und das Fenster zeigt das Original. Warum, steht
in fallback_reason(), aber das liest niemand. Für den Spieler ist das
von „HD-Screen erscheint nicht“ nicht zu unterscheiden. Außerdem sind
Live-Läufe aus dieser Umgebung nicht möglich, weil das Display nicht
erreichbar ist.

Reihenfolge: A–D (Code, je ein Commit, Smoke grün, Rot/Grün gezeigt),
dann E (Display), dann F (live).

## Teil A: Jeder Rückfall wird geloggt

1. An genau einer Stelle, dort, wo main.py entscheidet, ob das
   Original gezeigt wird (main._showing_original, main.py:245-246),
   nicht in jedem Screen: Wechselt die Entscheidung, oder wechselt
   der Grund, wird eine Zeile geloggt, mit Screen-Name, Screen-ID
   des Spiels und fallback_reason(). Hat ein Screen kein
   fallback_reason(), steht dort ausdrücklich „no reason given“.
   Nur bei Änderungen loggen, nie pro Frame.
2. Das gilt für jeden Screen, nicht nur für Fleets. research_select
   hat dieselbe Methode.
3. Erwarteter Übergang, damit er nicht falsch gelesen wird: Laut 138
   trägt der erste Snapshot nach dem Öffnen von Fleets Screen-ID 4,
   aber noch die Feldliste der Karte. Eine kurze Zeile „nicht
   bereit“, gefolgt von READY, ist korrekt. Im Log wird das nicht
   unterdrückt.
4. Smoke-Check: ein Screen, der von READY auf einen Rückfall und
   zurück wechselt, erzeugt genau zwei Zeilen; zehn gleiche Frames
   erzeugen keine weitere.

## Teil B: Jeder Screen-Wechsel wird geloggt

core/dispatcher.py:86-90 (switch_to): eine Zeile mit altem und neuem
Screen und der Screen-ID des Spiels. Smoke-Check wie in A.

## Teil C: OrionLayer loggt beim Start seinen Stand

Beim Start eine Zeile: Commit-Hash, ob der Arbeitsbaum Änderungen
hat, und ORION2RE_VERSION. Ist git nicht verfügbar oder das
Verzeichnis kein Repo: „unknown“, kein Absturz (ein Diagnose-Werkzeug
degradiert, es stürzt nicht ab). Smoke-Check für beide Fälle, den
zweiten erzwungen, nicht von der lokalen Platte abhängig.

## Teil D: Der Grund steht auf dem Schirm

Fällt ein HD-Screen mit bekannter Screen-ID auf das Original zurück,
wird über dem Original-Bild eine Zeile mit dem Grund eingeblendet.

- HD EXTENSION, markiert im Modul, im Statusdokument und in einem
  Smoke-Check, der fehlschlägt, wenn die Einblendung verschwindet.
- Wortlaut-Rahmen in assets/shared/.../labels.json (Entscheidung 15),
  der Grund selbst aus fallback_reason().
- Text über Style.render_text (Entscheidung 30), Hintergrund
  undurchsichtig aus background_cockpit.png, wie beim Hilfe-Popup
  (nicht aus dem darunterliegenden Bild).
- Position: eine Kante des Fensters, die das Original-Bild nicht
  verdeckt; bei 4:3 im Pillarbox-Rand, wenn vorhanden. Die
  Einblendung schluckt keine Klicks, alles geht weiter an das
  Original.
- Kein Grund für den Rückfall: keine Einblendung. Die normale Anzeige
  des Originals (Gefechtskarte, unbekannte Screens nach Entscheidung
  22) bleibt unverändert.
- Renders in allen vier Auflösungen mit einem erzwungenen Rückfall
  (FOREIGN_FIELDS mit einem langen Grund) nach
  ~/orionlayer-fixtures/evidence/work_order_139/. Ein langer Grund
  muss vollständig lesbar bleiben: umbrechen oder kürzen mit Hinweis,
  aber nicht abschneiden.

## Teil E: Display für Live-Läufe

1. Feststellen, warum xdpyinfo -display :0 scheitert: Xwayland-
   Socket unter /tmp/.X11-unix/, XAUTHORITY (unter GNOME typisch
   /run/user/1000/.mutter-Xwaylandauth.*), alternativ SDLs
   Wayland-Treiber (SDL_VIDEODRIVER=wayland) für orion2re und
   OrionLayer.
2. Nur die Umgebung der eigenen Läufe setzen. KEINE Änderung an
   Datas Systemkonfiguration (keine Shell-Profile, keine
   Desktop-Einstellungen, keine Dienste).
3. Nachweis: xdpyinfo (oder das Wayland-Gegenstück) gelingt, und
   orion2re kommt über „mox2: data space allocated“ hinaus bis zum
   offenen Port 17362. Danach Engine sauber beenden.
4. Das Rezept in CLAUDE.md unter Live-Läufe eintragen, so dass jede
   künftige Sitzung es ohne Suche anwenden kann: welche Variablen,
   woher ihre Werte kommen (ermittelt, nicht fest eingetippt, denn
   der Auth-Dateiname wechselt pro Anmeldung), und woran man den
   Fehlschlag erkennt.
5. Geht es ohne Eingriff in Datas System nicht: STOPP für E und F.
   Im Bericht in genau einem Schritt beschreiben, was Data tun müsste.

## Teil F: Fleets live

Regeln wie immer: genau ein Client; SAVE1–9 und SAVE11 vorher und
nachher hashen, die Werte müssen identisch sein; SAVE10 nur
protokollieren; SAVE8 niemals anfassen; livesend liest vor jedem
Senden die Feldliste. Laufen Datas Instanzen: STOPP für F.

1. Engine und OrionLayer starten, Spielstand laden (nicht SAVE8).
2. Auf der HD-Karte Fleets drücken, auf dem Weg, den HD benutzt.
3. Festhalten: Start-Zeile aus C, die Zeilen aus A und B, die
   Feldliste des Spiels zum Zeitpunkt des Rückfalls oder von READY,
   Screenshots von HD-Fenster (mit Einblendung aus D, falls
   Rückfall) und Framebuffer, Seite an Seite.
4. RETURN, zurück auf die Karte, beenden, Hashes prüfen.
5. Keine weiteren Aktionen: keine Auswahl, kein Scrap, keine
   Bewegung.

Ergebnis:
- READY: Der Screen erscheint. Renders gegen die aus 137 legen, und
  nennen, was live anders aussieht als im Fixture. Nichts weiter.
- Rückfall: Ursache mit Log-Zeile und Feldliste belegen. Ist es die
  Feldmenge aus 137 A: die fehlenden Felder mit Rechteck, Typ und
  Quelle (Datei:Zeile im Builder) nennen und die Korrektur
  vorschlagen, aber NICHT anwenden. Ist es etwas anderes: dasselbe,
  mit Beleg.

## Abschluss

Frischer Klon, Smoke grün, dann alle Commits pushen. Schlägt die
Prüfung fehl: selbst reparieren, erneut prüfen, pushen.
Upload-Sperre unverändert.

## Bericht

- A–D: Stellen, Smoke-Nummern, Rot/Grün, Render-Pfade.
- E: Ursache, Rezept, Nachweis.
- F: Log-Zeilen wörtlich, Zustand, Ursache, vorgeschlagene Korrektur.
- Endstand von origin/main.
