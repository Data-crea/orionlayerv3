1. Ja, vollständig als HD EXTENSION. Das Original zeigt nichts, also ist alles außer dem Typ Extension – der Fundament-Eintrag sagt das in diesem Umfang, nicht kleiner. Das Argument bleibt: Werte fest, seit Jahren öffentlich, die Anzeige nimmt Neulingen einen Nachteil. „Spoiler" trifft es nicht – ein Spoiler ist eine Information, die man nicht hätte haben können. Schalter Standard an, wie entschieden.

2. Taktisch, und Struktur und Panzerung als zwei Zeilen. Im Kampf sind es zwei verschiedene Dinge, die Panzerung wird zuerst abgetragen. Bei den fünf Monstern steht dann „Armour 0", das ist ehrlich. Die strategischen Werte aus aipower.cpp sind KI-Heuristiken, keine Spielerinformation – nicht in die Tabelle.

3. Ja, nur Maximalwerte. Die Schadensfelder bleiben UNVERIFIED und werden nicht gelesen. Eine Null bestätigt keinen Offset, und was nicht benutzt wird, muss nicht verifiziert werden. Die Viper-VII-Records sind ein Ansatz für später – notieren, nicht jetzt verfolgen.

4. Amoeba: Artwork-Auftrag an mich, bis dahin bleibt das Bild leer. Kein Platzhalter, keine Silhouette – leer ist ein Zustand, ein erfundenes Bild wäre eine Abweichung. Frage zurück: Fehlt der Amoeba-Master auch für die Galaxiekarte, oder nur für die große Stufe? Wenn die Karte heute ein anderes Sprite für Amoeba zeigt, ist das ein eigener Befund.

5. Ja, eine größere Stufe aus den Mastern über make_ship_icons.py, gleiche Pipeline wie die vorhandenen Stufen. Die Exportgröße steht als Zahl mit Quelle in der Größentabelle, markiert DERIVED – nicht aus der Boxgröße gelesen, die kann sich ändern. Ausgelegt auf die 4K-Box, Panel skaliert nach unten.

6. Das ist ein eigener Brief, nicht dieser. Lücke 1 und 2 sind dieselbe Lücke: Das Original öffnet auf Screen 0 verschiebbare Boxen, und HD kann sie nicht zeigen. Systemfenster und Flottenbox brauchen dieselbe Antwort. Bevor ein Wunsch nach orion2re_open_fixes.md geht, prüfe eines: Registriert das Systemfenster beim Öffnen eigene Felder (CLOSE-Knopf, Planeten)? Wenn ja, ist die FIELD_LIST-Formänderung nach Entscheidung 21 schon das Signal für den Box-Zustand, und Joe muss nichts anfassen. Live bestätigen, dann Stop 1 für „Popups der Galaxiekarte in HD". Bis dahin ändert dieser Auftrag nichts am Klickverhalten.

7. Ja, eigener Extraktor auf core/lbx.read_entries nach Entscheidung 38, mit --lang.

8. Ja, vor Stop 2. Eine Waffe ohne Namen kann nicht angezeigt werden. Wahrscheinlich ESTRINGS oder eine zweite Namenstabelle; Quellstelle melden.

Was aus Teil A jetzt in Stop 2 kommt: Lücke 3 (Cancel-Wirkungen des Rechtsklicks senden) und Lücke 4 (Extraktor). Beides klein und ohne die Box-Frage lösbar. Lücke 1 und 2 warten auf den eigenen Brief.

Zwischenhalt vor Stop 2: Waffennamen-Quelle und die Antwort zu den Systemfenster-Feldern.