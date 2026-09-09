Kleiner, abgeschlossener Auftrag vor (oder nach) der Colony-Summary-Arbeit — bitte als EIGENEN Commit, nicht in den fachlichen Commit mischen.

Der Mitarbeiter an orion2re heißt **Joes**, nicht Joe. Im Baum steht an 15 Stellen die falsche Form. Alles Prosa, kein einziger Code-Bezeichner, keine Funktions- oder Dateinamen betroffen.

ZU ÄNDERN:
- CLAUDE.md — Zeile 5, 21, 145
- README.md — 322
- doc/orion2re_open_fixes.md — 1 (Überschrift; das ist das Dokument, das Joes selbst zu sehen bekommt)
- doc/ext_api_dokumentation_v3.md — 4, 569
- doc/v3_fundament.md — 467, 635, 664
- v3_projektstatus.md — 231, 232, 522, 814, 2113, 2114
- tools/version_check.py — 8, 96 (beides Kommentare)
- screens/colony_summary/layout.json — im Schlüssel list._open_note, "a question for Joe"

NICHT ANFASSEN — dort steht die richtige Form schon:
- doc/CREDITS.md:72
- screens/main_menu/assets/credits.txt:62

DESHALB: kein blindes Suchen-und-Ersetzen. Mit Wortgrenze arbeiten (\bJoe\b), danach einen Gegen-Grep auf "Joess" laufen lassen. Wenn der etwas findet, ist die Ersetzung über eine der beiden korrekten Stellen gelaufen.

DREI GENITIVE, bitte umformulieren statt Apostroph setzen — mit dem s am Wortende wird jede Genitivform unschön, und die Doku ist englisch:
- doc/v3_fundament.md:664 "Joe's list" → z. B. "the list Joes gets"
- tools/version_check.py:96 "Joe's bug" → z. B. "a bug in orion2re, not here"
- v3_projektstatus.md:522 "Joe's tree" → z. B. "the tree Joes maintains"

VERIFIKATION:
1. grep -rn "\bJoe\b" . muss leer sein (ohne __pycache__)
2. grep -rn "Joess" . muss leer sein
3. grep -rn "Joes" . muss weiterhin CREDITS.md und credits.txt enthalten
4. tools/smoke_test.py grün — layout.json wird angefasst, und dort hängen Markierungs-Checks dran

Danach committen. NICHT pushen, das mache ich selbst.