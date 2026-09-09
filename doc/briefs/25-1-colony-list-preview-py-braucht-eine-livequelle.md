1. colony_list_preview.py braucht eine Livequelle.
Das Werkzeug rendert aus eingebauten Fake-Zeilen und fragt den Snapshot nicht an. Beleg: Lauf um 20:42 gegen ein laufendes Spiel mit 55 Kolonien auf Sterndatum 3502.4, gerendert wurden Vega I, Sol III, Kif II, ein Name aus zehn W und Nazin I, Sidebar 18432/−214/39/7/+12/1180. Der native Schuss daneben zeigt Blucher II, Wolf II, Draconis V und 878/+42/78/17/−3/27. Zwei verschiedene Welten nebeneinander, und nichts im Bild sagt es.
Dass die API erreichbar war, ist belegt: struct_probe.py colonies --outposts gegen dasselbe laufende Spiel meldet „Screen 20, stardate 3502.4, 99 stars, 55 colonies".
Gewünscht: ein --live-Schalter, der den Snapshot holt — der Code dafür steht in struct_probe.py — und build_rows über den echten Zustand laufen lässt. Damit wird --native erstmals ein Verifikationswerkzeug statt einer Layout-Vorschau.

2. Die Herkunft der Zeilen muss im Bild stehen.
Auch mit --live. Ein Werkzeug, dessen Ausgabe wie eine Messung aussieht, darf nicht ohne Vermerk erfundene Daten zeichnen. Das ist dieselbe Klasse wie die still abgeschnittene zehnte Zeile: eine Abwesenheit, die aussieht wie ein Ergebnis.

3. Der Invariantenprüfer misst das falsche Objekt.
Bei --sort population meldet er „NO — the unit moved with the row set", bei --sort name „yes". Die Slotbreite wird aus POP_LIMIT_CAP und der Panelbreite gerechnet und kann sich mit der Zeilenmenge überhaupt nicht bewegen; der Prüfer vergleicht in Wahrheit Zeile 1 über zwei Läufe, und dort steht bei anderer Sortierung eine andere Kolonie. Er soll die Invariante prüfen, nicht die Zeile. Vorbestehend, war schon auf HEAD so.

4. Sidebar aus screen.py herausziehen.
_render_sidebar, _value_column, _native_column_width, _empire_value, rund 130 Zeilen. Eigener Commit, weil die zwei Smoke-Checks für die Klemme aus Entscheidung 44 direkt in _native_column_width und _value_column greifen und mitwandern müssen — das ist die einzige Aufgabe dieses Schritts.

Offen und nicht Teil dieses Auftrags: pop_growth und morale ruhen weiter allein auf den Namen im Header. Sie fallen, sobald 1 steht und der Vergleich mit echten Daten läuft. Der native Schuss dafür existiert bereits.