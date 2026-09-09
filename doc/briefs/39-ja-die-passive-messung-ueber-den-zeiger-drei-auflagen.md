Ja, die passive Messung über den Zeiger. Drei Auflagen:

1. Vorher aufschreiben, was jede Erklärung vorhersagt. Landet der Zeiger auf der geklickten Koordinate, ist die Abbildung in Ordnung und die Ursache liegt woanders. Landet er versetzt, sagt der Versatz, welche Skalierung dazwischensteht. Beides vor der Messung, nicht danach.

2. Mit bekannter Fenstergröße, und mit mehr als einer. Eine einzelne Messung kann einen Versatz nicht von einem Skalierungsfaktor unterscheiden. Zwei Fenstergrößen, zwei Klickpunkte.

3. Prüf zuerst, ob der Zeiger überhaupt auf dem ankommt, was du bekommst. Entscheidung 39 hält fest, dass er auf die Present-Surface komponiert wird und die Extension API die indizierte schickt. Wenn er nicht drauf ist, muss die Messung anders gebaut werden — und der Fund ist trotzdem etwas wert.

Dazu eine Beobachtung von Data, die eine Vorhersage erlaubt: Scrollen, Sortierreiter und Detailpanel funktionieren live, nur der Pop-Klick tut nichts. Wenn die Sortierreiter wirklich am Spiel ankommen, trennt die beiden etwas Bestimmtes — die Reiter haben einen Hotkey, der Track hat keinen und muss über die Koordinate. Prüf im Log, welchen Weg der Sortierwechsel tatsächlich genommen hat, Taste oder native_click. Ging er über die Koordinate, ist die Fensterkoordinaten-Erklärung schwächer als gedacht.

Auch das vor der Messung aufschreiben. Eine Vorhersage, die nach dem Ergebnis formuliert wird, ist keine.

Ein Klick, keine Wiederholung, Data weiß Bescheid.