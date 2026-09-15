# Galaxy map click table (brief 107, Stop 1)

**What this file is.** The click table and gap list from the Stop 1 report
on brief 107, as it was delivered in the session of 14 September 2026
(transcript 11fb1609, 19:38 UTC). Filed on Data's decision A6 of brief 111,
because brief 110 Part C had to rebuild the list from source when the table
turned out to exist only in chat. **The section below is verbatim and in
German**, as delivered; it is a record, and translating it would make it a
second copy that could disagree with the first.

**What has moved since, stated here and not edited into the table:**

- Gap 3 is closed (16c0ae7): a right click on the map sends CANCEL_FIELD on
  the grid field before the pan (`v3_projektstatus.md`, "the right click is
  the game's cancel"). The cells saying the cancel effects are not sent are
  stale.
- Gap 4 is closed (16c0ae7): `tools/maintext_extract.py` and
  `core/maintext.py` exist. Nothing draws the text yet.
- Gaps 1 and 2 (system window, fleet box, icon hit test) are brief 110
  Part A, measured live on the reference save on 15 September 2026; the
  field lists are in brief 110's Stop 1 report and decisions (`doc/briefs/110-*`,
  `111-*`).
- Brief 110 Part C is the current list of what remains after Part A.

---

## Teil A.1: Klickreaktionen der Karte

**Grundlagen aus dem Quelltext:**
- **Klickreihenfolge:** Solange die Flottenbox zu ist, prüft das Spiel erst Schiffe, dann Sterne. Bei offener Flottenbox ist es umgekehrt (`mainscr_main.cpp:425-438`).
- **Rechtsklick:** Zuerst läuft `Check_Help_List_` (`fields.cpp:1240`). Die Hilfetabelle `_main_screen_help_list` (`evanhelp.cpp:4`) hat 15 feste Einträge plus die Flottenbox-Knöpfe, **deckt die Karte aber nicht ab**.
  - Weil `Main_Screen_` den Cancel abschaltet (`Disable_Cancel_`, `mainscr_main.cpp:281`), liefert `Get_Input_` das negative Grid-Feld (`fields.cpp:1360`).
  - `Get_Mouse_Field_` gibt dafür 1 zurück. Jede Objektreaktion verlangt aber 0 (Stern `:463`, Schiff `:594`).
  - Einzige Wirkung: Der Relocation-Merge-Modus endet und der Zoom-Modus wird verlassen (`:397-404`).
- **Doppelklick:** Gibt es im Original nicht (fields.cpp, mouse.cpp, mainscr*.cpp, platform.cpp durchsucht). In HD auch nicht.
- **HD-Grundproblem (aus dem Code, nicht live geprüft):**
  - Systemfenster und Flottenbox sind verschiebbare Boxen auf Screen 0.
  - `core/dispatcher.py:161` schaltet nur nach `current_screen` um, `main.py:245` zeigt im HD-Modus keinen Framebuffer.
  - Folge: Der Klick wird gesendet, aber **die Antwort ist unsichtbar**.

| Objekt | Linksklick | Rechtsklick | Doppelklick |
|---|---|---|---|
| **Unerforschter Stern** | **Wirkung:** `Do_System_Popup_` (`mainscr_main.cpp:472`) → `Draw_System_Display_Popup_` (`sys.cpp:691-705`).<br>**Bild:** nur die Schraffur von `Hide_System_Display_` (`sys.cpp:635`) plus Rahmen. Kein Stern, keine Planeten.<br>**Titel:** HESTR 0x16B „Star System Unexplored“; bei `Contact_With_One_Colony_` 0x16A „Star System %s“.<br>**Text:** `Print_Empty_System_Data_` (`sys.cpp:1536`) mit HESTR 0x0F+Spektralklasse (`sys.cpp:176` → `misc.cpp:156`).<br>**Mit ausgewählten Schiffen:** Flugbefehl; Fehler HESTR 0x21–0x24. Im Merge-Modus HESTR 0xDD.<br>**Textquelle:** HESTRINGS.<br>**HD:** **fehlt** (Klick geht raus, Fenster unsichtbar). | Nur die Cancel-Wirkungen oben.<br>**HD:** teilweise – Hilfe, dann Pan-Drag; die Cancel-Wirkungen werden nicht gesendet. | nichts / nichts |
| **Erforscht, ohne Kolonie** | Systemfenster mit Planeten (`Init_System_Display_`). Die Beschreibung eines Specials kommt aus maintext.LBX (`Draw_System_Special_Popup_`, `sys.cpp:580`; Aufruf in `mainpups.cpp:1573/1713`).<br>**HD:** fehlt. | wie oben | – |
| **Eigene Kolonie** | Mit `auto_select_colony` → `Last_Colony_Selected_` (`haccess.cpp:250`, nur eigene Kolonien) → Kolonie-Screen. Ohne die Einstellung: Systemfenster.<br>**HD:** Kolonie-Screen vorhanden (Screenwechsel, Framebuffer-Fallback); Systemfenster fehlt. | wie oben | – |
| **Fremde Kolonie** | `Last_Colony_Selected_` liefert -1 → Systemfenster.<br>**HD:** fehlt. | wie oben | – |
| **Schwarzes Loch** | Kein Auto-Select (`:466`) → Systemfenster. `Ok_To_View_System_` ist false (`sys.cpp:71`) → Schraffur, Titel 0x16B/0x16A, Text HESTR 0x15.<br>**Mit ausgewählten Schiffen:** Der Zweig ist durch `!= BLACK_HOLE` gesperrt (`:481`) → keine Reaktion.<br>**HD:** fehlt. | **Geklärt:** Weder Hilfe noch Fenster. `Check_Help_List_` läuft zuerst, findet keine Region und gibt 1 zurück; dann `mouse_status` 1 → kein Zweig. | – |
| **Nebel** | Kein Klickobjekt: `Check_Stars_XY_` (`mainscr.cpp:1697`) prüft nur Sterne → wie leerer Raum.<br>**HD:** vorhanden (`_star_at` kennt keine Nebel → Inject). | wie leerer Raum | – |
| **Wurmloch** | Nur eine Linie → wie leerer Raum.<br>**HD:** vorhanden. | wie leerer Raum | – |
| **Monster-Icon** | `Check_Ships_XY_` (`mainscr.cpp:1750`, ohne Owner-Filter) → `Do_Fleet_Popup_` (`:595`) → Flottenbox, zeigt nur den Namen.<br>**HD:** **fehlt / abweichend.** Es gibt keinen Icon-Treffertest. `_star_at` gewinnt (`screen.py:606`), der Klick landet auf dem Sternzentrum → das Spiel öffnet den Stern statt des Monsters. | nichts (`field_res` 1) | – |
| **Eigene Flotte** | Flottenbox mit auswählbaren Schiffen; der nächste Sternklick ist ein Flugbefehl.<br>**HD:** fehlt (kein Icon-Treffer, Box unsichtbar). | nichts | – |
| **Fremde Flotte** | Flottenbox, Palette neu geladen (`mainscr.cpp:1838`), keine Befehle.<br>**HD:** fehlt. | nichts | – |
| **Leerer Raum** | Kein Objekt → keine Wirkung.<br>**HD:** vorhanden (Inject, gleiche Wirkung). | Cancel-Wirkungen.<br>**HD:** Pan; die Cancel-Wirkungen fehlen. | – |

**maintext.LBX:**
- Aufbau: 14 Einträge, je Header count=1/size=600 plus ein 600-Byte-String.
  - 0 „No Special“ … 9 Space Monster, 11 Guardian, 12 Trade Goods, 13 Housing.
  - Der Dateiname ist selbst ein ESTRINGS-Eintrag (`estrings.cpp:51`, Index 368), also sprachabhängig.
- `tools/help_extract.py` deckt die Datei **nicht** ab: Das Tool ist fest auf HELP.LBX gebaut (Record 0x57B, Verkettung).
- Nötig ist ein eigener kleiner Extraktor auf `core/lbx.read_entries`, nach den Regeln aus Entscheidung 38:
  - Die Datei stammt aus der Installation des Spielers und wird nie committet.
  - Die Bytes bleiben unverändert, dekodiert wird beim Laden.
  - Die Datei trägt eine Formatversion.
  - Eine fehlende Datei ist ein Zustand, den HD erklärt, kein Fehler.
  - `--lang` passend zur Spracheinstellung.

**Lücken, nach Häufigkeit sortiert:**
1. **Das Systemfenster ist unsichtbar.** Das betrifft jeden Sternklick, der nicht in den Kolonie-Screen führt. Folgeklicks landen womöglich in der unsichtbaren Box. Vor Stop 2 live zu prüfen.
2. **Flotten- und Monster-Icons haben keinen HD-Treffertest.** Der Stern gewinnt, die Flottenbox ist unsichtbar, Flotten lassen sich auf der HD-Karte nicht bewegen.
3. **Die Cancel-Wirkungen des Rechtsklicks** (Merge-Modus, Zoom-Modus) werden nicht gesendet.
4. **Der maintext.LBX-Text** (Special-Popup) fehlt, weil es noch keinen Extraktor gibt.
5. Doppelklick: keine Lücke.
