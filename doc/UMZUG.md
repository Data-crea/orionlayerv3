# Umzug nach Git und GitHub

Einmalige Einrichtung, danach der neue Arbeitsablauf. Auf Deutsch,
weil es an dich gerichtet ist und nicht an den Code.

---

## 1. Repository anlegen

Der ausgelieferte Baum ist bereits der Repository-Inhalt: generierte
Assets fehlen, `.gitignore` liegt bei, nichts muss vorher aufgeräumt
werden.

```bash
cd ~
rm -rf orionlayerv3-git && mkdir orionlayerv3-git
unzip -q -d orionlayerv3-git ~/Downloads/orionlayerv3-git.zip
cd orionlayerv3-git
N=$(find . -type f | wc -l)
echo "Dateien: $N (erwartet 328)"
```

Stimmt die Zahl nicht, hier abbrechen und nachfragen.

```bash
python tools/setup.py
```

Braucht pygame, numpy und Pillow. Auf Arch verweigert `pip` die
systemweite Installation (PEP 668) — das ist Absicht, nicht ein
Fehler:

```bash
sudo pacman -S python-pygame python-numpy python-pillow
```

Auf anderen Systemen `pip install -r requirements.txt`. Da du das
Projekt ohnehin fährst, sind die drei meistens längst da; dann
kannst du diesen Schritt überspringen.

Erwartet: drei Generatoren `ok`, dann `absent context-help texts`,
dann `SMOKE TEST PASSED — 50 checks green`.

Der alte Baum bleibt vorerst liegen — `~/orionlayerv3` erst löschen,
wenn der neue eine Woche funktioniert hat.

## 2. Git initialisieren

Einmalig, falls Git dich noch nicht kennt — sonst bricht der erste
Commit mit „Identität des Autors unbekannt" ab, nachdem alles schon
vorgemerkt ist:

```bash
git config --global user.name "Dein Name"
git config --global user.email "du@example.com"
```

**Bei einem öffentlichen Repository landet diese Adresse in jedem
Commit** und ist für alle lesbar — Adress-Sammler lesen GitHub
routinemäßig aus. GitHub stellt dafür eine Weiterleitungsadresse
bereit: unter *Settings → Emails → Keep my email addresses private*
steht eine Adresse der Form `12345678+name@users.noreply.github.com`.
Die als `user.email` eintragen, dann bleibt die echte privat und die
Commits werden trotzdem deinem Konto zugeordnet. Nachträglich ändern
geht nur durch Umschreiben der Historie, also besser vor dem ersten
Commit entscheiden.

Und die Extraktionen **vor** dem ersten Commit, damit der Baum
vollständig ist:

```bash
python tools/help_extract.py
python tools/nebula_extract.py "$HOME/Master of Orion 2/STARBG.LBX"
```

Beide schreiben in den Projektbaum und geben den absoluten Pfad aus.
Landet etwas anderswo, sagt `git status` es dir sofort — dort tauchen
dann Dateien auf, die die `.gitignore` nicht kennt.

```bash
cd ~/orionlayerv3-git
git init
git branch -M main
git add -A
git commit -m "OrionLayer v3 — 7 HD-Screens, 48 Checks"
```

`git status` muss danach `nothing to commit, working tree clean`
sagen. Tut es das nicht, zeigt es dir, welche generierte Datei die
`.gitignore` noch nicht erfasst — das ist eine Information, kein
Fehler.

## 3. Zu GitHub schieben

Repository auf github.com anlegen, **ohne** README, `.gitignore` oder
Lizenz — die sind schon da, und GitHub würde sonst einen zweiten
Anfangs-Commit erzeugen, der beim ersten Push kollidiert.

```bash
git remote add origin git@github.com:<dein-name>/orionlayerv3.git
git push -u origin main
```

**Es wird öffentlich.** Damit kann ich das Repository aus meiner
Sandbox klonen — du gibst mir künftig die URL statt einer Datei, und
ich sehe garantiert den echten Stand. Das ist genau der Fehler, der
uns eine Sitzung gekostet hat: zwei parallele Arbeitsstände, die
nichts voneinander wussten.

Vorbereitet ist dafür alles:

- **`LICENSE`** — MIT für Code und Dokumentation, mit einem Abschnitt,
  der länger ist als die Lizenz selbst und sagt, was sie *nicht*
  abdeckt: das aus MOO2 abgeleitete Bildmaterial, die Schrift (OFL),
  und alles, was zur Laufzeit extrahiert wird.
- **README-Hinweis** — dass eine eigene, legal erworbene Kopie des
  Spiels nötig ist und OrionLayer nichts davon ersetzt.
- **`nebula_ref/` ist raus.** Das war die einzige Stelle im Baum mit
  unverändertem Originalmaterial — Sprites aus `starbg.lbx`, Pixel für
  Pixel, ohne eigenen Anteil. Wird jetzt wie die Hilfetexte zur
  Laufzeit extrahiert. Die Nebel-Master in `nebula/` bleiben: das ist
  deine Bearbeitung.
- **Die DEMO-Schrift ist ersetzt** durch Aldrich (OFL). Die war die
  einzige Stelle, an der das Texture-Pack-Argument nicht getragen
  hätte.

Das kostet eine Prüfung: ohne `nebula_ref` kann der Smoke-Test Form
und Helligkeit der Nebel nicht mehr vergleichen. Er verschweigt das
nicht — die Prüfung meldet dann, welcher Befehl die Referenzen
zurückholt, und die Gesamtzahl bleibt bei 48.

```bash
python tools/nebula_extract.py /pfad/zu/starbg.lbx
```

---

## Der neue Ablauf

### Vor jeder Änderung

```bash
git status
```

Muss sauber sein. Sonst mischen sich deine eigenen unversicherten
Änderungen mit dem, was gleich dazukommt, und die Diff-Anzeige
verliert genau den Wert, wegen dem das hier existiert.

### Ein Paket von mir anwenden

```bash
cd ~/orionlayerv3-git
git switch -c feature/kurzer-name

cp -r ~/Downloads/pkg_xyz/paketordner/. .

git status          # was hat sich WIRKLICH geändert
git diff --stat
```

`git status` ist der Ersatz für `verify_tree.py` — ohne Manifest,
ohne Pflege, immer aktuell. Ein Paket, das heimlich `smoke_test.py`
zurücksetzt, steht hier als geänderte Datei, **bevor** du irgendetwas
ausführst. Genau das war der Fehler, den du sonst erst am
Prüfergebnis gemerkt hättest.

Dann prüfen:

```bash
python tools/smoke_test.py
```

Passt es:

```bash
git add -A
git commit -m "Kurze Beschreibung"
git switch main
git merge feature/kurzer-name
git push
```

Passt es nicht — und das ist der eigentliche Gewinn:

```bash
git checkout . && git clean -fd
```

Alles zurück auf den letzten Commit. Kein sha256, kein Rätselraten,
welche der achtzehn ZIP-Dateien die richtige war.

### Regeln, die den Rest tragen

- **Commit erst nach grünem Smoke-Test.** Dann ist jeder Commit auf
  `main` ein Zustand, zu dem du zurückkannst.
- **Nie `git add -f`** auf eine ignorierte Datei. Fehlt dir eine:
  `python tools/setup.py`.
- **Kein `&&` hinter einen Prüfer.** Er endet mit Fehlercode, wenn er
  etwas findet — das ist der Sinn.
- **Brace-Erweiterung wie `{a,b,c}` nur unter bash.** Unter `sh`
  schlägt sie still fehl und der Befehl tut scheinbar nichts.

---

## Sitzungen mit Claude

### Hier im Chat

Am Anfang gibst du mir den aktuellen Stand. Bei einem privaten
Repository reicht meistens ein Schnappschuss ohne Assets — 356 KB
statt 170 MB:

```bash
cd ~/orionlayerv3-git
tar -czf ~/code.tgz --exclude='*/assets/*' --exclude=assets \
    --exclude=.git --exclude=__pycache__ .
```

Assets brauche ich nur, wenn wir an Grafik arbeiten. Ist das
Repository öffentlich, genügt die URL.

### In Claude Code

Die Desktop-App hat drei Reiter — Chat, Cowork und Code. **Code** ist
der richtige für dieses Projekt: ein Fenster mit direktem Zugriff auf
deine lokalen Dateien, kein Terminal. Der Terminal-Weg, den du
furchtbar findest, ist nur eine von mehreren Varianten.

`CLAUDE.md` im Wurzelverzeichnis wird dort beim Start automatisch
gelesen. Darin stehen keine Regeln, sondern Zeiger auf die
Dokumente, die sie enthalten — damit es keine vierte Stelle gibt, an
der dieselbe Regel veralten kann. Der Smoke-Test prüft, dass jeder
Pfad darin existiert und die genannte Check-Anzahl stimmt.

Was sich dort ändert: Claude arbeitet direkt im Arbeitsbaum und
committet selbst, der Paket-Schritt entfällt. Was gleich bleibt: der
Smoke-Test vor jedem Commit, und dass die Entscheidung bei dir liegt.

Beide Wege bleiben nebeneinander sinnvoll. Recherche im
orion2re-Quellcode und Entscheidungen lassen sich hier im Chat gut
führen; das Ausführen gehört eher dorthin.

---

## Wenn etwas schiefgeht

| Problem | Befehl |
|---|---|
| Änderungen seit dem letzten Commit verwerfen | `git checkout . && git clean -fd` |
| Letzten Commit rückgängig, Änderungen behalten | `git reset --soft HEAD~1` |
| Was hat sich wann geändert | `git log --oneline --stat` |
| Wer hat diese Zeile geschrieben und warum | `git log -p -- pfad/zur/datei` |
| Ignorierte Datei fehlt | `python tools/setup.py` |
| Stand einer alten Version ansehen | `git switch --detach <commit>` |

Der letzte Punkt ist der, der dir das Sternsprite-Rätsel beantwortet
hätte: mit Historie wäre nachvollziehbar gewesen, welcher Aufruf von
`make_star_icons.py` die beschnittenen 36 Sprites erzeugt hat.
