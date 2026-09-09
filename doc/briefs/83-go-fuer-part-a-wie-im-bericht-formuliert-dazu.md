Go für Part A wie im Bericht formuliert. Dazu:

Die fünf Screenshots in ~/Bilder/Bildschirmfotos vom 8. September abends sind die vier F9-Größen (1920×1080, 2560×1440, 3440×1440 zweimal, und der 4K-Fall auf dem 3440er). Kopiere sie als after_geometry_<W>x<H>.png nach ~/orionlayer-fixtures/evidence/ und schreib in die README, dass die Zuordnung von mir kommt.
Die zweite Ursache (win_w/win_h von surface.get_size() statt aus der F9-Tabelle) als eigener Commit, mit einer Logzeile mit Zeitstempel, wenn angefragte und gewährte Größe auseinanderliegen.
Der Check in beiden Zuständen — frisch gebaut und hineingeresized — an allen Schlüsseln und den vier F9-Größen, als Regel formuliert.
Grep über den Baum: welche Module halten Box-Objekte länger als einen Frame? Nur melden, nicht fixen, außer es ist eine Zeile.
Prinzip ins Fundament, Abschnitt 2, Diagnose: „Eine Vorschau, die in einer Größe konstruiert, kann keinen Resize-Fehler sehen — der Check muss den Weg gehen, den der Fehler ging."

Danach B bis F nach dem Auftrag. Vor Part E sage ich dir Bescheid, wenn Slot 8 geladen ist.