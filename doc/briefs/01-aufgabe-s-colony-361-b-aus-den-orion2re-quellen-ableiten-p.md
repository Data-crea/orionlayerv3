Aufgabe: s_colony (361 B) aus den orion2re-Quellen ableiten. Phase A —
nur Quellcode lesen, kein laufendes Spiel nötig, KEINE Änderung an
Produktionspfaden.

Vorher lesen: doc/v3_fundament.md (ganz, nicht überfliegen), besonders
Entscheidung 23 und den Abschnitt "Evidence". CLAUDE.md kennst du.
Ausserdem core/structs/unverified.py und core/structs/planet.py als
Vorbild für einen fertigen Spec.

Kontext: colonies_raw kommt bereits über die Leitung
(core/game_state.py:182-185). Blockiert ist nur die Feldzuordnung.
COLONY in unverified.py hat bewusst eine leere Feldliste. Sie bleibt
leer, bis zwei unabhängige Quellen übereinstimmen.

Zu tun:

1. Im orion2re-Baum die Definition von s_colony finden (grep in
   orion2.h und Nachbarn) und die Memberliste vollständig
   transkribieren — Reihenfolge, Typen, Arraylängen, verschachtelte
   Structs.
2. Den Assert in sizes.h für s_colony finden und zitieren.
3. Eine Wegwerf-TU in einem Scratch-Verzeichnis ausserhalb des
   orion2re-Baums schreiben, die den Header mit seinem #pragma pack(1)
   einbindet und pro Member offsetof + sizeof ausgibt, plus
   sizeof(s_colony). Kompilieren, laufen lassen. Erwartete Ausgabe:
   sizeof == 361. Weicht sie ab, ABBRECHEN und melden — dann stimmt
   etwas an Packing oder Headerversion nicht, und jede weitere Zahl
   wäre wertlos.
   Der orion2re-Baum wird nicht angefasst. Keine Datei dort anlegen,
   ändern oder löschen.
4. Das Ergebnis als doc/s_colony_offsets.md ablegen, im Stil von
   doc/ship_icon_measurement.md: Tabelle Offset/Typ/Name/Herkunft mit
   Datei:Zeile, darüber ein Absatz was gemacht wurde, darunter
   ausdrücklich "second source still missing: live probe".

Priorität in der Tabelle, falls die Zeit knapp wird — das sind die
Felder, die das Bar-Design des Screens tatsächlich verbraucht:
  owner, star-/planet-index, Population,
  das Pro-Pop-Array (job, race, state, conquered flag),
  max_farms.
Ohne das Pop-Array ist kein HD-Drag in native Klicks übersetzbar, weil
Pops_Identical_ genau darüber gruppiert.

Ausdrücklich NICHT:
- COLONY in unverified.py füllen
- core/structs/colony.py anlegen
- irgendetwas in screens/colony_summary/ anfassen
- ein Feld als verified markieren
Ein Header allein ist eine Quelle. Solange die zweite fehlt, ist die
Tabelle Dokumentation und sonst nichts.

Bekannte Einschränkung für Phase B: tools/struct_probe.py druckt die
int16-Spalten nur für Records <= 64 Byte. Für 361 B kommen nur
Hexdump und ASCII-Runs. Nicht jetzt ändern — nur in
doc/s_colony_offsets.md als Notiz für Phase B festhalten.

Zum Schluss: python tools/smoke_test.py muss grün bleiben, die
Prüfzahl darf nicht sinken. Danach knapp berichten, was übereinstimmt
und was nicht, unbequeme Befunde eingeschlossen.