1. Outpost-Filter scharf. col.outpost_flag != 0 in build_rows, Quelle colxport.cpp:91-99. In colony.py ersetzt der Beleg den Vorbehalt: Sterndatum 3502.4, 55 Kolonien, Kolonie 54 auf Planet 239, vom Spiel selbst als „Yian I (Elerian Outpost)" beschriftet mit 0/4 pop, auf dem Colonies-Schirm nicht gelistet — elf Zeilen gegen zwölf Datensätze mit passendem Besitzer. Dazu colonize.cpp:381-382 als einzige Schreibstelle. Smoke-Check: eine Fake-Kolonie mit gesetztem Flag muss aus den Zeilen fallen.

2. Sidebar-Posten schließen. Sechs von sechs gegen die Originalbox, -10 gegen +30 schließt die Verwechslung von surplus_food und surplus_bc aus. player.py verliert seinen Vorbehalt.

3. BC nachziehen. Vierte Produktionszeile, ECON_COUNT=4, Geometrie bestätigt es: 349, 367, 385, 403, Moral bei 421. Die markierte Abweichung und ihr Smoke-Check verschwinden.

4. screen.py teilen. 691 Zeilen gegen eine Richtgröße von 300. Die Auswahl-Maschinerie ist ein eigenes Modul.

5. Die fehlende Zeile sichtbar machen. colonylist.render() bricht still ab, wenn die nächste Zeile nicht mehr in list_area passt — auf deinem Screenshot fehlt Woz III, und nichts sagt es. Erst sichtbar machen plus Smoke-Check gezeichnet gegen vorhanden, dann getrennt über Scrollen entscheiden.