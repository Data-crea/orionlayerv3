Phase B: s_colony gegen laufende Daten prüfen. Zweite Quelle.

Lies doc/v3_fundament.md vollständig — das hier fasst Structs,
Werkzeuge und am Ende einen Produktionspfad an, also die lange
Runde. Dazu doc/s_colony_offsets.md aus deinem eigenen Phase-A-Lauf.

Voraussetzung: orion2re läuft mit geladenem Savegame. Die
Grundwahrheit kommt vom Maintainer im nächsten Zug; frag danach,
bevor du prüfst, statt sie aus dem Hexdump zu erraten.

1. COLONY in core/structs/unverified.py mit den Offsets aus
   doc/s_colony_offsets.md füllen, verified=False, Quelle im
   Kommentar. Das ist kein Widerruf der bisherigen Vorgabe, sondern
   ihr Zweck: unverified.py IST die Quarantäne für Specs aus einer
   Quelle. Kein core/structs/colony.py, nichts in screens/.

2. tools/struct_probe.py bekommt einen Modus, der einen Record
   gegen einen Spec dekodiert und Feldname/Offset/Wert ausgibt,
   statt nur Hexdump. Generisch über Spec, nicht auf s_colony
   verdrahtet — s_leader_data braucht dasselbe. Damit fällt die
   64-Byte-Grenze der int16-Ansicht weg, ohne sie anzufassen.

3. Prüfen in dieser Reihenfolge, jeweils gegen die Grundwahrheit:
   owner (0), n_pops (10), planet (2), max_farms (224). Dann das
   Pop-Array: Berufe je Pop gegen die notierte Aufteilung, Rassen
   gegen die notierte Mischung, MASK_RACE/MASK_PROFESSION usw. aus
   pop.h. Zwei Invarianten, die unabhängig von der Grundwahrheit
   greifen: die Berufe summieren sich auf n_pops, und jeder
   Profession-Wert liegt im gültigen Bereich.
   Danach derselbe Datensatz nach einem Spielzug, mit der zweiten
   notierten Bevölkerungszahl.

4. planet.py: dessen Docstring nennt Bedeutungen, die nie gegen
   laufende Daten gesehen wurden — colony_index == -1, und die
   Enum-Zuordnungen für climate, size, gravity_class,
   mineral_class aus orion2_consts.h. Die Offsets sind verifiziert,
   die Bedeutungen sind Transkription. Prüf sie gegen die vom
   Maintainer notierten Planeten und trag im Docstring ein, was
   live gesehen wurde und was aus dem Header stammt. Wenn eine
   Zuordnung nicht stimmt, ist das der wichtigste Befund des
   Durchlaufs und geht allem anderen vor.

5. Erst wenn beide Quellen übereinstimmen: COLONY nach
   core/structs/colony.py mit verified=True, Beleg im Docstring
   (Datum, Kolonie, welche Werte übereinstimmten), Eintrag in der
   "Already promoted"-Liste in unverified.py, und der Abschnitt
   "second source still missing" in doc/s_colony_offsets.md wird
   durch das Ergebnis ersetzt. Weicht irgendetwas ab: nichts
   promoten, Abweichung dokumentieren, berichten.

6. Smoke-Test: mindestens eine Prüfung dazu, die eine stille
   Regression fängt. Die Regel prüfen, nicht die Instanz —
   z.B. dass die COLONY-Offsets lückenlos sind und auf 361 enden,
   und dass die Pop-Masken sich nicht überlappen. Zahl darf nicht
   sinken.

7. v3_projektstatus.md nachziehen: Struct-Verifikation, der
   Colony-Summary-Abschnitt, und was jetzt nicht mehr blockiert
   ist.

Alle Aussagen in diesem Auftrag über orion2re stammen aus
doc/v3_fundament.md und aus deinem eigenen Phase-A-Bericht, nicht
aus der Quelle. Prüf sie, statt sie zu übernehmen. Meine letzte
Begründung zu Entscheidung 23 war sachlich falsch und du hast sie
zu Recht ersetzt — dasselbe gilt hier.