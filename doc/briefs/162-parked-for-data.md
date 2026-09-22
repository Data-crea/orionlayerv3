# Work order 162 — parked for Data

Fragen und Funde, die den Lauf nicht angehalten haben. Nichts davon
wurde repariert: Work Order 162 verschiebt Prüfungen, es ändert keine.

---

## 1. Ein `--screen`, das wirklich weniger *ausführt*, geht nicht — und warum das eine Entscheidung ist

Der Auftrag beschreibt den Schalter so: „läuft der Kern plus alle
Module dieses Screens, sonst nichts". Gebaut ist er anders — er
**zeigt** weniger, er **lässt** nichts weg. Der Grund ist gemessen,
nicht geschätzt:

Die Prüfungen teilen sich ihre Fixtures über Objekte — `d.active`, die
App, ein fertig gelegter Screen — und frühere Prüfungen füllen diese
Objekte über Methodenaufrufe, die keine Namensanalyse sehen kann.
Rechnet man ehrlich (jeder Methodenaufruf auf einem Namen verändert
ihn), hängt ein einzelner Screen an **96 %** der Suite; mit einem
praktischen Netz an **87 %** — und der so verkleinerte Lauf ist an
genau so einer Stelle gestorben, am Zustandsobjekt der Galaxiekarte.

Ein Lauf, der trotzdem verkleinert, wäre **grün gegen einen Zustand,
den andere Prüfungen aufgebaut haben**. Genau diese Form hat 157 schon
einmal abgelehnt, in einem Satz: *„eine Prüfung, die die App einer
anderen Prüfung erbt, ist eine neue Fehlerklasse, die dieses Projekt
noch nicht hatte."*

**Was offen ist, ist deine Entscheidung:** soll ein Entwicklungslauf
irgendwann auch *schneller* werden, dann müssen die Prüfungen aufhören,
sich Fixtures zu teilen. Das ist ein Umbau der Prüfungen, kein Umzug —
und damit außerhalb dieses Auftrags. Die Zahl, an der man den Erfolg
messen würde, steht oben: solange ein Screen an 87 % der Suite hängt,
bringt jeder Selektor nichts.

---

## 2. Drei Prüfungen liegen in der falschen Gruppe

Die Zuordnung ist eine Heuristik und sagt pro Abschnitt, wie sie
entschieden hat. Drei Fälle sind erkennbar daneben:

| Prüfung | liegt in | gehört zu |
|---|---|---|
| `a fallback says why: one log line per change of decision or reason` | `main_menu` | Kern |
| `field 0 is dropped once in parse_fields` | `planets` | `fleets` |
| `colony summary sidebar six …` | Kern | `colony_summary` |

Der Code dieser Prüfungen nennt einen fremden Screen öfter als ihren
eigenen. **Es kostet nichts an Abdeckung** — beide Tore führen sie
unverändert aus; es kostet nur, dass ihr Satz unter dem falschen
`--screen` gedruckt wird. Umhängen ginge in einem Schritt, ändert aber
die Reihenfolge der Module und damit die Sache, die dieser Auftrag
gerade bewiesen hat, dass sie unverändert ist. Deshalb parkt es.

---

## Später, pro Modul

Ideen, die den Umzug verbessern würden und die die `ok(...)`-Liste
ändern — also genau das, was dieser Auftrag verbietet, weil die Liste
sonst eine gute Änderung nicht mehr von einer verlorenen Prüfung
unterscheiden kann. Jede nennt ihr Modul, damit sie drankommt, wenn
dieser Screen das nächste Mal bearbeitet wird und das Modul klein
genug ist, um allein getestet zu werden.

**Die fünf Module über 40 KB sind fünf Prüfungen, die zu viel auf
einmal behaupten.** Jedes enthält *einen* Abschnitt, der allein größer
ist als die Grenze — und ein Abschnitt ist der Block einer Prüfung.
Sie sind nicht zu teilen, ohne eine Prüfung zu teilen, und eine
Prüfung zu teilen ändert die `ok(...)`-Liste.

| Modul | was darin zu groß ist |
|---|---|
| `011_galaxy_map_galaxy_map_stand_in_exactly_amoeba.py` | 51 KB, **dreizehn** `ok()` in einem Block: der Stand-in, die Sprites, die Icon-Größen und die Hüllenwerte hängen an einer gemeinsamen Vorbereitung |
| `013_colony_summary_colony_summary_sort_keys_seven_five.py` | 45 KB für **eine** Prüfung: die sieben Sortierschlüssel über alle Auflösungen |
| `031_core_figures_sit_on_the_plate_s.py` | 44 KB für **eine** Prüfung: die Figuren auf dem Innenboden, vier Auflösungen, jedes Band, aus dem Render gemessen — und darin liegt zusätzlich der tree-weite `squish_step`-Grep, der deshalb im Kern landet |
| `059_core_ship_weapons_end_at_the_first.py` | 43 KB, **neunzehn** `ok()`: die Monster- und Schiffsteil-Werte in einem Lauf |
| `061_core_no_archives_or_backup_copies_anywhere.py` | 40 KB, **zehn** `ok()`: sämtliche tree-weiten Sweeps hintereinander |

Wenn einer dieser Screens das nächste Mal bearbeitet wird, ist das der
Moment, die Prüfung in ihre Teile zu zerlegen — dann ist das Modul
klein genug, um die neue `ok(...)`-Liste einzeln zu prüfen.

---

## Nichts gefunden, was repariert werden müsste

Beim Verschieben ist **kein Fehler in einer Prüfung** aufgefallen. Die
einzige Stelle, an der etwas kaputtging, hat der Umzug selbst erzeugt
(ein Name, den der Läufer besitzt und ein Prüfmodul überschrieb) — das
ist gefunden, behoben und hat seitdem eine eigene Prüfung.
