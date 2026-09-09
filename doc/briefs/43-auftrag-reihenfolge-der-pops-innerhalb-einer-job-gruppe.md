Auftrag: Reihenfolge der Pops innerhalb einer Job-Gruppe

Sitzungsanfang wie immer: Repo klonen, doc/v3_fundament.md aus dem Repo lesen, bevor irgendetwas vorgeschlagen wird. Die Kopie im Chat-Projekt ist veraltet.

Dies ist ein Untersuchungsauftrag. Ergebnis ist ein Bericht mit Fundstellen, kein Patch und keine Änderung an der Darstellung. Wo eine Aussage nicht belegbar ist, soll das dort stehen statt einer Vermutung.

Vorgehen. Die Logik ist aus dem Code herzuleiten. Ein Savegame ist dafür nicht vorgesehen und soll nicht abgewartet werden — ein Save mit Native oder Android existiert derzeit nicht. Nur wenn eine Frage im Code nicht entscheidbar ist, wird sie als solche gemeldet, mit der Angabe, welche Konstellation im Save sie klären würde.

Es gilt die Regel des Fundaments: die Funktion lesen, die das Array füllt, nicht die, die es lesen. Eine zeichnende Funktion belegt die Speicherreihenfolge nicht. Und es gilt die Zwei-Quellen-Regel: eine reine Code-Lesung ist eine Quelle, sie darf die Zeichenentscheidung tragen, aber nichts wird auf ihrer Grundlage als verifiziert geführt. Jede Aussage im Bericht ist entsprechend zu kennzeichnen.

Hintergrund. Für den Colonies-Screen ist entschieden, dass die Pop-Zeile nach Job gruppiert bleibt und die Rassen-/Android-Eigenschaft in der Zellbehandlung getragen wird, nicht in der Farbe. Bevor gezeichnet wird, muss die Ordnung innerhalb einer Gruppe bekannt sein, sonst wird sie beim Zeichnen unbemerkt miterfunden.

Frage 1 — Speicherreihenfolge. In welcher Reihenfolge liegen die Pops einer Kolonie im Array? Gibt es eine Ordnung nach Rasse, nach Android-Status, nach Job, oder ist es Entstehungsreihenfolge? Was passiert mit der Position eines Pops beim Jobwechsel, und was, wenn ein Pop entsteht oder verschwindet? Zu beantworten von der schreibenden Seite her.

Frage 2 — Zeichenreihenfolge. Zeichnet das Original in Array-Reihenfolge, oder sortiert es beim Zeichnen um? Falls umsortiert: wonach, und innerhalb einer Job-Gruppe stabil oder nicht? Getrennt von Frage 1 beantworten — die Speicherreihenfolge ist bindend, die Zeichenreihenfolge ist eine Darstellungsentscheidung, die HD übernehmen oder als Abweichung markieren kann.

Frage 3 — Kollision mit der bestehenden Auswahlregel. Die Auswahl greift heute „alle identischen bis zum Ende des Arrays". Ordnet HD innerhalb einer Gruppe anders an als das Array, klickt der Nutzer auf eine Zelle und es bewegt sich eine andere. Aus dem Code herzuleiten: kann ein rassenfremder Pop überhaupt zwischen zwei eigenen derselben Gruppe stehen? Ergibt der Code, dass diese Konstellation nicht entstehen kann, ist der noch offene zweite Testfall damit erledigt statt offen — das ausdrücklich feststellen.

Randfälle im Bericht: eine Gruppe ohne Pops; ein Android und ein rassenfremder Pop in derselben Gruppe; ein rassenfremder Pop zwischen zwei eigenen in derselben Gruppe.

Mitzuklärende Stelle. Die notierte offene Frage zu Do_Colony_Info_Pop_Stuff_For_Pop_ (coldraw.cpp:325-330): die zweite Schleifenebene heißt race_idx, testet aber pop_val & 0x400, laut pop.h MASK_CONQUERED, während der Bericht „Nibble" MASK_RACE (0x0F) meint. Diese Schleife entscheidet, welcher Pop anders gezeichnet wird.

Ablage. Der Befund zu Frage 1 bis 3 geht in die Projektdokumentation, nicht nach doc/orion2re_open_fixes.md — dort steht ausschließlich, was Joes gefragt wird. Nur die coldraw.cpp-Frage wird dort eingetragen, in der Form von Punkt 6 und 7: eine Frage, kein Fix. Was aus dem Befund dauerhaft gilt, gehört als nummerierte Entscheidung ins Fundament, nächste freie Nummer laut Übergabe 48.

Nebenergebnis, falls beim Lesen ohnehin sichtbar: was ein Savegame enthalten müsste, um die vier offenen Punkte gemeinsam zu schließen — Ablehnungsregeln, Pop-Nibble-Wächter 8 und 9, Rassenunterscheidung am Bildschirm, Sortierung. Also welche Rasse, welcher Planet, welcher max_farms-Wert. Einkaufsliste für später, kein Arbeitsauftrag jetzt.

git push bleibt Datas Kontrollpunkt, immer nach dem Diff.