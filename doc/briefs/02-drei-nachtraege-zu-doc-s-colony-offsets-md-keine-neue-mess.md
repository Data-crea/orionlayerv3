Drei Nachträge zu doc/s_colony_offsets.md, keine neue Messung.

1. In den Kopf der Datei: den gemessenen sizeof(s_colony) und den
   Wortlaut des Asserts aus sizes.h, mit Datei:Zeile. Wenn beide
   361 sagen, steht das da; wenn nicht, ist das der Bericht und
   alles andere wartet.
2. git status --short -- src/orion2.h src/sizes.h im orion2re-Baum.
   Sind die Dateien lokal geändert, gehört das in die
   Provenienzzeile — der Commit-Hash allein beschreibt die Messung
   dann nicht. Nur berichten, nichts dort anfassen.
3. python tools/version_check.py und python tools/smoke_test.py,
   Ergebnis melden. Beides stand im vorigen Auftrag und fehlt im
   Bericht.

Danach: git add doc/s_colony_offsets.md, committen, pushen.
Commit-Message im Ton des Repos, und sie muss sagen, dass die
zweite Quelle noch fehlt.

Zur Anmerkung über Entscheidung 23: berechtigt, und die Auflösung
ist nicht "strenger", sondern eine Grenze der Regel. offsetof
bestätigt Offset und Breite des Pop-Worts, aber nicht die Lage der
Bits darin — die Anordnung von Bitfeldern innerhalb der
Speichereinheit ist implementierungsdefiniert. Für s_planet_data
trug Header plus static_assert vollständig, für s_colony trägt es
bis zum Pop-Wort. Trag das als Zusatz in Entscheidung 23 in
doc/v3_fundament.md nach, zwei bis drei Sätze, im Stil der
Umgebung, und vermerk in v3_projektstatus.md, dass 23 präzisiert
wurde und warum. Keine Umnummerierung, keine neue Entscheidung.