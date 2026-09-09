Schrift: Versalien ohne Doppelpunkt bleiben auf Sidebar und Sortiertasten. Als DEVIATION (Typografie des HD-Frontends) an drei Orten markieren, gegen ESTR_SRESERVE_SD und die layout.json-Labels. Eine Runde, kein Umbau.

Sortierleiste, zwei Fragen (Screenshot 1080p):

Das aktive Feld (INDUSTRY) deckt das Wort nicht ganz ab. Woher kommt die Rechteckbreite — gespeicherter Wert oder Style.render_text-Breite plus Rand? Wenn gespeichert: durch Rendern messen, wie beim Namen. Was zeigt das Original — Fläche mit welchem Rand um das Wort (colsum.cpp, die Multi-Button-Zeichnung)? Transkribieren.
PRODUCING ist grau, INDUSTRY blau. Ist grau der „unavailable"-Zustand der Producing-Sortierung (keine Kostentabelle), und ist er an drei Orten markiert? Wenn ja: so lassen, aber Data sieht zwei Highlights — der Zustand muss sich vom aktiven Feld unterscheidbar lesen, nicht wie eine zweite Auswahl. Wenn nein: Befund, Ursache nennen.

Editor, jede Box in Breite und Höhe ziehbar. Data will im Werkzeug jede Box verkleinern und vergrößern können, nicht nur verschieben. Vor dem Bau ein Stopp mit der Aufteilung:

welche Boxen frei in beiden Achsen (handplatzierte Inhaltsboxen),
welche gebunden (die sechs Spalten: nur x-Kanten, Höhe aus dem Band; das sagt der Editor beim Versuch),
welche gesperrt (Ausschnitte aus dem Rahmen, Entscheidung 3 — der Editor lehnt ab und verweist auf frame_holes; sonst rutscht Inhalt unter sein Loch),
und was bei einer Größenänderung abgeleitet nachzieht (Font-Skalierung, Absatzumbruch, Inset-Seitenverhältnis 1,2651 — der Inset hält sein Verhältnis, egal an welcher Kante gezogen wird).
Griffe an Kanten und Ecken; Save-Reload-Diff, dass nur ref_rect geschrieben wird. Danach bauen.

Notiert, nicht jetzt: Hintergrund richtig zuschneiden (Data, später).