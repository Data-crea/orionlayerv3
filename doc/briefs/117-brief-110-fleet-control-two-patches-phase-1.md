Weg 1: volle Flottensteuerung in HD über zwei Patches. Phase 1 jetzt, kein Bau live, kein Patch angewendet.

Zweiten Patch beschreiben. Der Umschalt-Befehl (ein einzelnes Schiff im Flottenkasten an-/abwählen), analog Open Fix 12, mit Checker. Als eigener Open Fix abgelegt, als Beschreibung verfasst, nicht angewendet. Open Fix 20 (Lesen) bleibt wie er ist.
Beide Patches zusammen trocken prüfen. Open Fix 20 (Lesen) plus der neue (Schreiben) gegen einen sauberen orion2re-Baum: Dry-Run, dass sie sich nicht gegenseitig zerlegen, Syntax-/Typprüfung mit den Build-Flags. Nicht gebaut, nicht angewendet.
HD-Code bauen, gegen aufgezeichnete Testdaten, nicht live. Der Code, der den Auswahl-Block vom Draht liest (blau/schwarz pro Schiff) und den Umschalt- bzw. Zielbefehl schickt. Solange die Patches nicht in meinem Baum sind, gibt es keine echten Daten — also gegen aufgezeichnete Feldlisten/Snapshots testen. Smoke-Test grün.
Nichts angewendet, nichts gepusht. Am Ende liegen beide Patches beschrieben und trocken geprüft vor mir. Ich lese sie, wende sie an, baue orion2re neu und melde es. Erst dann Phase 2: Live-Test auf Scratch (SAVE4/SAVE5, nie SAVE8), eine Instanz — blau/schwarz stimmt mit dem echten Zustand, ein injizierter Umschalt-Klick ändert ihn, ein Zielklick schickt genau die gewählten Schiffe.

Einzelboxen pro Schiff und Scrollbalken (>9 Schiffe) baust du in Phase 1 als Anzeige mit, den Scrollbalken erst messen, sobald live geht.
