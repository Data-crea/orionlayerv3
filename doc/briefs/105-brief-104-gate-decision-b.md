Entscheidung zum Gate vor Schritt 3: (b).

Die vier nicht ableitbaren Tabellen werden über eine Regel gefüllt, die ausdrücklich von uns stammt. Markiert als DEVIATION in colors.json neben den Werten, mit Begründung, und im Fundament-Eintrag 63 benannt. Das ist keine Beziehung, die dem Original unterstellt wird – das Gate hat gezeigt, dass es keine gibt – sondern eine markierte Erfindung für ein Preset, das MOO2 nie hatte.

Vorarbeit: ship_* aus ships.py:112-121 nach colors.json, mit demselben Byte-für-Byte-Check wie bei den Bannern. Erst dann Preset-Tabellen.

Die Regel für ein Preset aus acht Basisfarben:

owner = Basis
ship = Basis + (255 − Basis) · k_ship, ein k für alle acht
owner_hover = Basis + (255 − Basis) · k_hover, ein k für alle acht
banner und banner_hd: Multiplikator = Basis, Addition (0,0,0). Die Orange-Addition des Originals ist eine Handkorrektur für eine Farbe, die das Preset nicht hat; sie wird nicht nachgebildet.

Die beiden k werden gemessen, nicht gesetzt. Nicht „ship = Basis": Multiplikator-Tints auf dunklen Graustufen-Sprites brauchen die Anhebung zum Weiß, sonst ist das Preset dunkler als jede Original-Farbe und sieht kaputt aus.

k_ship: Rendere für jede der acht Original-Farben ein Schiff mit dem Original-ship_*-Tint, nimm die mittlere Luminanz über alle acht. Wähle k_ship so, dass die acht Okabe–Ito-Schiffe im Mittel dieselbe Luminanz treffen.
k_hover: Dasselbe für das Verhältnis der Luminanz owner_hover zu owner über alle acht Original-Farben.
Beide Werte mit Messprotokoll in die Palette (welches Sprite, welche Zoomstufe, welcher Mittelwert).

Neuer Smoke-Check: Die mittlere Schiff-Luminanz jedes ausgelieferten Presets liegt innerhalb 10 % des Originals; dasselbe für das Hover-Verhältnis. Damit bleibt die Regel geprüft, wenn später jemand eine Basisfarbe ändert.

Danach Schritt 3 wie im Brief: Presets in der Palette mit Quellen, palette.init(preset=) mit Grep aller Aufrufer, Deuteranopie-Prüfung. Dann Kartenboden, Settings-Zeilen, Markierungen, Doku. Smoke-Test nach jedem Schritt. Am Ende ein Paket, gegen einen frischen Baum verifiziert, mit der Liste der berührten Dateien.

Zwischenhalt: Die gemessenen k mit Zahlen an mich, bevor die Preset-Tabellen geschrieben werden.
