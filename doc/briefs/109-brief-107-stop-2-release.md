Freigabe Stop 2 für doc/brief_map_clicks_and_monsters.md

Beide Zwischenhalt-Fragen sind beantwortet, die Entscheidungen 1–5 aus meiner letzten Antwort gelten. Dazu:

Amoeba-Fallback auf der Karte: bleibt, als markierte Abweichung. Karte und Panel sind verschiedene Fälle: Im Panel ist ein leeres Bild ein verständlicher Zustand, auf der Karte wäre ein unsichtbares Monster eine Lücke gegenüber dem Original. Drei Bedingungen:

DEVIATION-Marker im _resolve_sprite-Zweig, Eintrag im Statusdokument unter bekannten Lücken, Amoeba und Antaran benannt.
Smoke-Check: Die Menge der Typen, die auf den Fallback laufen, ist genau {amoeba, antaran}. Kommt ein Master dazu oder fehlt ein anderer, fällt der Test.
MONSTER_ICON_DIM_ZOOM0["amoeba"] aus BUFFER0.LBX messen wie die anderen fünf, mit Schwellen-Sweep. Die Kopie von Eel wird durch die Messung ersetzt, UNVERIFIED-Marker weg.

Waffennamen: tools/techname_extract.py um den zweiten Bereich erweitern – Waffen 397–442, Schilde 391–396, Panzerungen 384–390. Keine Pluralformen; das Panel zeigt Name plus Anzahl in eigener Spalte.

Umfang von Stop 2:

Teil B vollständig: Spec-Designteil nach verified, Schadensfelder bleiben UNVERIFIED und ungelesen; Hüllenpunkt-Tabelle mit Checker gegen initship.cpp und techdata.cpp; Struktur und Panzerung als zwei Zeilen; Settings-Schalter, Standard an; Panel mit Sprite-Box links und text-Boxen rechts in boxes.json, Wortlaut als Vorlagen in layout.json; Sprite-Stufe fürs Panel über make_ship_icons.py, Exportgröße als DERIVED-Zahl in der Größentabelle; HD-EXTENSION-Marker im Modul, DEVIATION-Marker an der Sprite-Wahl nach Typ.
Teil A, Lücke 3: Rechtsklick sendet die Cancel-Wirkungen (Merge-Modus, Zoom-Modus beenden), bevor HD pannt.
Teil A, Lücke 4: maintext.LBX-Extraktor nach Entscheidung 38, mit --lang.
Lücke 1 und 2 nicht anfassen – eigener Brief.

Smoke-Tests: wie in B.3.5 des Briefs; dazu der Fallback-Check, der Hüllenpunkt-Checker, und: Rechtsklick auf leerer Fläche sendet genau die Cancel-Wirkungen und sonst nichts.

Doku: Fundament-Eintrag unter der nächsten freien Nummer (prüfen, nicht annehmen), mit der vollen Begründung: Original zeigt keinen Wert, Werte fest und öffentlich, Anzeige als Ausgleich. Statusdokument: Inventions-Liste, bekannte Lücken (Amoeba/Antaran-Master, Systemfenster und Flottenbox in HD), Dateilängen prüfen. Brief als erledigt markieren.

Abgabe: Ein Paket, gegen frischen Baum nach tools/setup.py verifiziert, Smoke-Test grün, Liste der berührten Dateien, plus Screenshots des Panels bei einem bewachten System in 1080p und 4K.