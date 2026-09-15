Brief 110 Teil A: Auswahl-Zustand der Flottenbox klären, bevor Einzelboxen und Zielklick gebaut werden.

Zuerst ein Live-Test auf Scratch-Stand (SAVE4/SAVE5, nie SAVE8), genau eine Instanz am Server, kein Flottenbefehl über den Test hinaus. Falls ein Umschalt-Klick als Befehl durchschlagen könnte, auf einer Flotte, an der nichts verloren ist (der Scout). Drei Fragen, in dieser Reihenfolge:

Steht der Schiff-Auswahlzustand (im Original blau = gewählt, schwarz = abgewählt) in ships_raw oder sonst irgendwo auf dem Draht? ships_raw vor und nach einem Umschalten vergleichen. Stop 1 sagte, selected und _fleet_icon_selection_status seien nicht serialisiert — live bestätigen oder widerlegen.
Schaltet ein INJECT_CLICK auf ein einzelnes Schiff-Feld das Schiff um? Rückmeldung maschinell aus dem Framebuffer lesen (blaues vs. schwarzes Feld), nicht per Auge. Hängt an Entscheidung 39 (Zeiger-Sync), deshalb nur live klärbar.
Falls beides nein — Zustand nicht lesbar und injizierter Klick schaltet nicht um: als Open Fix ablegen (Patch, der den Auswahlzustand auf den Draht legt, nicht angewendet, wie Open Fix 14). Nichts im Code.

Ergebnis melden. Erst danach entscheide ich über:

(a) oder (b) für den Zielklick,
eine eigene Auswahl-Box pro Schiff mit blau/schwarz, wie im Original,
einen Scrollbalken bei mehr als 9 Schiffen (im Original vorhanden, in Stop 1 gesehen, noch nicht gemessen).
