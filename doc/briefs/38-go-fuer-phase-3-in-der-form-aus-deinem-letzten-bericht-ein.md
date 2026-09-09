Go für Phase 3, in der Form aus deinem letzten Bericht: eine Aktivierung nach der anderen, Thumb-verifiziert, Regeln geprüft, dann die zwei Klicks, mit dem Vorher/Nachher-Diff als Akzeptanz.

Drei Auflagen:

1. Der Thumb-Zusammenhang ist gemessen, nicht abgeleitet. Ein Treffer bei _first = 0 mit 11 Kolonien ist ein Punkt. Transkribier die Formel aus der Quelle und prüf sie an mehreren _first und mehreren Koloniezahlen. Ein Punkt ist keine Kurve.

2. Das Rücklesen braucht seinen eigenen Nullzustand. Zeichnet die Leiste nicht — unter zehn Kolonien tut sie das nicht —, muss das Zurücklesen „nicht gezeichnet" liefern und nicht 0. Ein Leerlauf, der wie ein gültiges _first = 0 aussieht, ist der grüne Lauf im Nullzustand aus der Randprüfung, eine Domäne weiter.

3. Vor dem ersten Klick zwei Bestätigungen: dass der g_pending_field-Slot im Fundament steht, und das Ergebnis des Greps — batcht sonst noch jemand ACTIVATE_FIELD? Wenn ja, liegt der Fehler heute schon im Baum und gehört vor Phase 3 gefixt.

Nebenbei, aus dem Smoke-Test-Lauf: Unknown ship icon fit 'sideways' for player, using height. Der Check daneben ist grün. Sag einmal, ob das alt und harmlos ist oder ein stiller Default über einem echten Wert.