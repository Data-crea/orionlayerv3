Phase 2: Du wendest die Patches selbst an, baust und testest live. Zielklick bleibt (a).

Vorher lesen und mir vorlegen, was du anwendest — kurze Zusammenfassung beider Patch-Dateien (ext_fleet_selection.patch, ext_fleet_select_ship.patch), damit im Diff steht, was in Joes Baum ging.
Beide anwenden, nicht zusätzlich ext_ship_icon_owner.patch (Eigentümer-Bytes stecken in Open Fix 20). orion2re neu bauen mit -DORION2RE_EXT=ON.
python tools/version_check.py muss beide als „applied" zeigen. Zeigt es das nicht, oder hakt ein Patch, oder bricht der Build — anhalten und melden, nicht live gehen. Ein halb angewendeter Patch ist ein stiller Fehler.
Genau eine Instanz am Server, keine parallele Verbindung (auch der Smoke-Test zählt als eine).

Dann live auf SAVE4/SAVE5, nie SAVE8. Eine Verbindung, SAVE1–SAVE9 vorher/nachher hashen, SAVE10 nur protokollieren, kein Flottenbefehl über den Test hinaus. Prüfen und melden:

Blau/schwarz stimmt mit dem echten Auswahlzustand, maschinell aus dem Framebuffer.
Ein Zellklick schickt MSG_SELECT_SHIP und ändert genau ein Schiff; der nächste Block bestätigt es.
Zielklick (a): ein Sternklick bei bekannter Auswahl bewegt genau die blau gezeigten Schiffe.
Scrollbalken an einem Stack über neun Schiffen; die benannte Scroll-Abweichung live bestätigen.
Schutz aus Entscheidung 65: Sternklick nur bei bekannter Auswahl frei, sonst blockiert.

Der orion2re-Baum ist nach diesem Lauf gepatcht — das ist eine dauerhafte Änderung. OrionLayer nicht pushen; Diff liegt mir vor. Offset 108 und die verified-Einträge kommen mit Teil B.
