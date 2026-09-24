# Work order 167 — parked for Data

Der Auftrag sagt: offene Fragen und Wahlen kommen hierher, jeweils mit
dem gewählten Default, damit der Lauf weitergehen kann; dazu alles aus
dem Inventar, was nicht gebaut wurde, mit Grund. Jede Wahl mit dem, was
ihre Umkehr kosten würde.

---

## P0 — „Clone per CLAUDE.md (full tree)"

**Gewählt:** gearbeitet im vollständigen Arbeitsbaum
`/home/data/orionlayerv3` — ein kompletter Klon von `origin/main` mit
allen generierten und extrahierten Dateien, derselbe Baum, in dem 164,
165 und 166 committet haben. CLAUDE.md nennt keinen eigenen
Klon-Schritt. **Warum:** der Auftrag berührt Artwork, das nur ein Baum
mit extrahierten Spieldateien zeigen kann, und die Commits sollen lokal
bleiben. **Umkehr:** die Commits in einen frischen Klon holen
(`git fetch /home/data/orionlayerv3 main`). **Kosten:** keine.

**Nebenbefund:** Deine eigene OrionLayer-Sitzung (`python main.py`,
gestartet 19:56) lief während des Laufs aus genau diesem Baum und hielt
die eine erlaubte Verbindung zu orion2re. Dazu Punkt L unten.
