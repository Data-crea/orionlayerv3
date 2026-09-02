# orion2re Quellcode-Index

Nachschlagewerk für den orion2re-Quellcode. Basis: `orion2re-main.zip`
im Uploads-Ordner, entpackt nach `/tmp/orion2re-main/`.

Aktualisiert 29. August 2026. Neu in dieser Fassung: „Schiff- und
Monster-Icons", „Schiff-Stacks und die Knotentabelle",
„Sternnamen und Wurmloch-Linien". Jede Zahl darin ist beim Bau der
HD-Icons einzeln nachgeschlagen worden.

**Zwei Einträge sind hier gelandet, weil ihr Fehlen Zeit gekostet
hat.** `Find_Ship_Stacks_` beantwortet die Frage, ob `_ship_node`
serialisiert werden muss (nein) — ohne diesen Abschnitt wurde
stattdessen ein C++-Patch vorgeschlagen. Und `line::Line_(..., 4)`
beantwortet, wie hell Wurmloch-Linien sein dürfen.

---

## Projekt-Übersicht

- 624 Dateien, 319 .cpp, 229 .h
- Ghidra-basierte Dekompilierung + Reimplementierung
- Baut nativ für Windows (MSVC/MinGW), macOS, Linux
- Braucht Original-MOO2-Dateien (GOG/Steam)
- Eigenes Savegame-Format v1 (abwärtskompatibel zu Legacy v0)

```
orion2re-main/
├── src/
│   ├── game/           # Kompletter Spielcode (Kern)
│   │   ├── orion2.h         # ALLE Struct-Definitionen (3173 Z.)
│   │   ├── orion2_consts.h  # ALLE Enums (1398 Z.)
│   │   ├── consts.h         # MAX_*-Konstanten
│   │   ├── sizes.h          # Static-Assert Struct-Größen
│   │   ├── map_scale.h      # Zoom-/Skalierungs-Helfer (inline)
│   │   ├── mox.h/cpp        # Globale Spielvariablen
│   │   └── (200+ weitere)
│   ├── ext/            # Extension API (nur mit -DORION2RE_EXT=ON)
│   ├── config/         # Konfigurations- und Mod-System
│   ├── network/        # Multiplayer Router
│   └── main.cpp
├── docs/               # Entwickler-Dokumentation
├── data/mods/          # Community Patch Mod
└── vendors/            # libsmacker, SDL, miniz, lz4, ...
```

---

## Zentrale Header

### `orion2.h` — Structs

| Zeile | Struct | Größe | OrionLayer-Relevanz |
|---|---|---|---|
| 487 | `s_colony` | 0x169 = 361 B | Colony-Screen, Savegame |
| 826 | `s_fleet_movement_icon` | — | Galaxy-Map Fleet-Icons |
| 1088 | `s_leader_data` | 0x3B = 59 B | Officer-Screen |
| 1653 | `s_nebula` | 0x05 = 5 B | Galaxy-Map — VERIFIZIERT |
| 1755 | `s_player` | 0xF0E = 3854 B | Alles — teilverifiziert |
| 2146 | `s_planet_data` | 0x12 = 18 B | Colony/Planet — VERIFIZIERT |
| 2305 | `s_racecust_race_customize` | — | Custom-Race-Screen |
| 2423 | `s_settings` | 0x229 = 553 B | New-Game, Savegame-Header |
| 2847 | `s_ship_data` | 0x81 = 129 B | Fleet/Galaxy-Map — VERIFIZIERT (Teilfelder) |
| 2910 | `s_ship_icon` | 12 B | Galaxy-Map — VERIFIZIERT |
| 2940 | `s_ship_node` | 5 B | Fleet-Gruppierung — NICHT serialisiert, rekonstruierbar |
| 2976 | `s_star_data` | 0x73 = 115 B | Galaxy-Map — VERIFIZIERT |

### `orion2_consts.h` — Enums (Auswahl)

| Zeile | Enum | Werte |
|---|---|---|
| 163 | `GAME_DIFFICULTY` | Tutor=0..Impossible=4 |
| 171 | `GALAXY_AGE` | Young=0, Average=1, Old=2 |
| 177 | `GALAXY_SIZE` | Small=0..Huge=3 (COUNT=5 mit Maximum) |
| 185 | `GOVERNMENT` | Feudal=0..Unification=6 |
| 195 | `FIELD_TYPE` | 15 UI-Feldtypen |
| 397 | `PLANET_CLIMATE` | Toxic=0..Gaia=9 |
| 462 | `STOCK_RACE` | Alkari=0..Trilarian=12 |
| 478 | `SCREEN` | 38 Screen-IDs (-1..43) |
| 597 | `STAR_CLASS` | B=0, F=1, G=2, K=3, M=4, Dwarf=5, BlackHole=6 |
| 607 | `SYSTEM_SPECIAL` | NoSpecial=0..SpaceMonster=9 |
| 980 | `TRAIT` | 31 Traits |

### `consts.h` — Kapazitäten

| Konstante | Original | orion2re |
|---|---|---|
| `MAX_PLAYERS` | 8 | 8 |
| `MAX_STARS` | 72 | 1024 |
| `MAX_SHIPS` | 500 | 9000 |
| `MAX_PLANETS` | 360 | 5120 |
| `MAX_COLONIES` | 250 | 5120 |
| `MAX_NEBULAS` | 4 | 57 |
| `MAX_LEADERS` | 67 | 67 |

`ORIGINAL_MAX_STARS` = 72 ist die Schwelle, ab der orion2re auf
erweiterte Skalierung umschaltet — siehe unten.

---

## Galaxy-Map Sternen-Sprites

Der Abschnitt, der beim HD-Nachbau am meisten Zeit gespart hätte.

### Sprite-Auswahl — EINE Achse, nicht zwei

`MAINSCR::Get_Star_Picture_Seg_` (mainscr.cpp:368):

```cpp
int16_t zoom_level   = HAROLD::Map_Scale_To_Zoom_Level_();
int16_t class_offset = spectral_class * 6;
int16_t result_ax    = zoom_level;
if (spectral_class != STAR_CLASS_BLACK_HOLE)
    result_ax += size;
result_ax += class_offset;
// BUFFER0.LBX, Eintrag final_index + 148
```

`zoom_level` (0..3) und `star.size` (0..2) werden **addiert** und
indizieren zusammen einen Bereich 0..5. Pro Spektralklasse liegen
also sechs separat gezeichnete Sprites vor, nicht drei Größen mal
vier Zoomstufen.

Konsequenz: Ein großer Stern bei Zoom 1 ist dasselbe Bild wie ein
mittlerer bei Zoom 0. „Groß" und „klein" sind keine absoluten
Größen.

`pict_type` wird übergeben, im Rumpf aber nie benutzt — mapgen
würfelt es (`Random_(3) - 1`), es wählt kein Sprite.

LBX-Belegung: 6 Klassen × 6 = 36 Sprites ab Index 148; die
Black-Hole-Klasse (6) belegt 184..189 und wird getrennt gezeichnet.

### Pixelgrößen

`MOX::_star_fields_dim[6]`, gesetzt in initgame.cpp:185 (und
identisch in harold.cpp:1483 in Hex):

```
Index  0   1   2   3   4   5
px    33  29  25  23  21  17
```

| Zoom | large (size 0) | medium (size 1) | small (size 2) |
|---|---|---|---|
| 0 (scale 10) | 33 | 29 | 25 |
| 1 (scale 15) | 29 | 25 | 23 |
| 2 (scale 20) | 25 | 23 | 21 |
| 3 (scale 30) | 23 | 21 | 17 |

Stufe 3 und 4 trennen nur 2 px (9 %) — die Größenunterscheidung
beim Herauszoomen ist auch im Original praktisch nicht lesbar.

Black Holes: eigene Tabelle in `Draw_Black_Holes_` (mainscr.cpp:706),
`zoom_dist[4] = {0x27, 0x21, 0x21, 0x18}` = 39, 33, 33, 24 —
ignoriert `star.size` vollständig, und Zoom 1 und 2 sind bewusst
gleich.

### Das Original skaliert NICHT

`MAINSCR::Draw_Scaled_Star_Picture_` (mainscr.cpp:20):

```cpp
int16_t scale_percent = HAROLD::Map_Star_Scale_Percent_();
if (scale_percent >= 100) {
    animate::Draw_(center_x - unscaled_dimension / 2, ..., picture);
    return;                      // native Größe, kein Skalieren
}
// sonst: bitmap::Scale_Bitmap_ auf scale_percent
```

In einem normalen Spiel ist `scale_percent` immer 100. Der
Tabellenwert dient dann nur zum **Zentrieren** — er ist gleich der
tatsächlichen Sprite-Pixelgröße. Nur bei über 72 Sternen *und*
`map_scale > 30` wird wirklich verkleinert.

### Zoomstufe und Skalierung

`HAROLD::Get_Scaled_Value_` (harold.cpp:169):

```cpp
return (value * 10) / MOX::_cur_map_scale;
```

Kleine `map_scale` = herangezoomt. scale 10 → Faktor 1.0,
scale 30 → 0.33.

`HAROLD::Map_Scale_To_Zoom_Level_` (harold.cpp:1085):
10 → 0, 15 → 1, 20 → 2, sonst 3; immer auf `_max_zoom_count`
geklemmt. Eine kleine Galaxie kommt nie über Zoom 0 hinaus.

### `map_scale.h` — erweiterte Skalierung (> 72 Sterne)

Alles `inline`, kompakt und gut lesbar:

| Funktion | Verhalten |
|---|---|
| `Uses_Extended_Scaling_` | `star_count > 72` |
| `Star_Scale_Percent_` | 100, außer erweitert UND `map_scale > 30`, dann `3000 / map_scale` |
| `Scale_Star_Dimension_` | multipliziert mit Prozent, Untergrenze 3 px |
| `Extended_Scale_For_Zoom_Level_` | wiederholtes Halbieren von `max_map_scale` |
| `Is_Extended_Max_Map_View_` | erweitert UND `map_scale == max_map_scale` |
| `Advance_Black_Hole_Animation_` | nur bei `scale_percent >= 100` |

Bei `Is_Extended_Max_Map_View_` steigt `Print_Star_Names_`
(mainscr.cpp:504) **sofort aus** — auf der maximal weiten Karte gibt
es überhaupt keine Sternnamen.

### Galaxie-Größe → max_map_scale

mapgen.cpp: 506/10, 759/15, 1012/20, 1518/30 — das Verhältnis
`MAP_MAX_X / max_map_scale` ist konstant **50.6**. Damit lassen sich
`_max_map_scale` und `_max_zoom_count` aus dem serialisierten
`MAP_MAX_X` zurückrechnen, ohne die Ext-API zu erweitern.

---

## Schiff- und Monster-Icons

`SHIPS::Get_Ship_Icon_Pict_Seg_` (ships.cpp:337) verteilt anhand von
`ship.owner`:

| owner | Bedeutung | BUFFER0.LBX-Index | Sprites |
|---|---|---|---|
| 0–7 | Spieler | `205 + player.color*4 + (3 - zoom)` | 8 × 4 = 32 |
| 8 | Antaraner | `237 + (3 - zoom)` | 4 |
| 9–14 | Monster | `241 + (owner - 9)*4 + zoom` | 6 × 4 = 24 |

**Zwei Fallen.** Der Spieler- und der Antaranerzweig invertieren den
Zoom, der Monsterzweig nicht. Und `is_highlighted` lädt denselben
LBX-Index — es gibt gar keine eigene Highlight-Grafik.

`NONPLAYER_SHIP_TYPE` (orion2_consts.h:528):

```
8  ANTARAN   9  GUARDIAN  10 AMOEBA
11 CRYSTAL   12 DRAGON    13 EEL     14 HYDRA
```

Spielerfarbe: `_player[i].color` indiziert
`MOX::_main_palette_player_colors[8] = {73, 98, 110, 32, 62, 148, 45, 85}`
(mox.cpp:903) — Paletten-Indizes der Hauptbildschirm-Palette. Die
Reihenfolge ist rot, gelb, grün, silber, blau, braun, violett, orange.

### Icon-Größen

Es gibt **keine Tabelle im Quellcode.** Die Maße liegen im LBX und
werden zur Laufzeit zurückgelesen:

```cpp
// ships.cpp:328
void Get_Ship_Icon_Dimensions_(int16_t zoom_level, uint8_t* w, uint8_t* h) {
    anim = buffer::Buffer_Reload_("BUFFER0.LBX", zoom_level + 0xCD, ...);
    *w = animate::Get_Width_(anim);
    *h = animate::Get_Height_(anim);
}
```

Ergebnis landet in `MOX::_ship_icon_width[4]` / `_ship_icon_height[4]`
(mox.h:625). Zwei indirekte Hinweise auf die Werte:

- `MAINSCR::Do_Fleet_Popup_` (mainscr.cpp:1797) übergibt
  `(13 - zoom, 9 - zoom)` als Überlappungsschwellen an
  `Overlapped_Ship_Icon_Button_`.
- Der Stapelabstand `11 - zoom` muss die Icon-Höhe übersteigen.

Gemessen an einem nativen Screenshot bei Zoom 0: **13 × 10 px** für
das Spielerschiff. Vollständige Herleitung in
`doc/ship_icon_measurement.md`.

**Schiff-Icons werden nie skaliert.** `Star_Scale_Percent_` greift
ausschließlich in `Map_Scale_Star_Size_To_Zoom_Level_`;
`Get_Ship_Icon_Pict_Seg_` hat keinen Skalierungspfad. In einer
erweiterten Galaxie ganz herausgezoomt schrumpfen die Sterne, die
Schiffe nicht.

---

## Schiff-Stacks und die Knotentabelle

`SHIPSTAK::Find_Ship_Stacks_` (shipstak.cpp:45). Der Abschnitt, der
einen unnötigen C++-Patch verhindert hätte.

```cpp
MOX::_ship_stack_count = 0;
MOX::_next_free_node = 0;

for (i = 0; i < _NUM_SHIPS; ++i) {
    if (ship_skip_flags[i] == 1) continue;      // status >= 3
    // gleiche location, x, y UND owner wie der Kopf eines Stacks?
    //   ja  -> anhängen
    //   nein-> neuer Stack, _ship_stack_start[count++] = next_free
    next_free = MOX::_next_free_node;
    MOX::_ship_node[next_free].ship_idx = i;
    MOX::_next_free_node++;
}
```

**Die Knotennummern hängen nicht am Stacking.** Beide Zweige der
Schleife vergeben genau einen Knoten in Array-Reihenfolge; der
Vergleich auf `location`/`x`/`y`/`owner` entscheidet nur, welchem
Stack ein Schiff beitritt. Knoten N ist also schlicht das N-te Schiff
mit `status < 3`.

`_ship_node[].ship_idx` wird in **keiner** der 319 .cpp-Dateien
außerhalb von shipstak.cpp geschrieben. Damit ist die Tabelle aus dem
serialisierten `_ship[]` exakt rekonstruierbar, und `_ship_node`
muss nicht über die Ext-API gehen.

Selbstprüfung dazu: `SHIPSTAK::Ship_Stack_Star_Id_` (shipstak.cpp:25)
ist wörtlich

```cpp
return MOX::_ship[MOX::_ship_node[node_idx].ship_idx].location;
```

und `Build_Ship_Icons_` schreibt genau diesen Wert in `star_idx`.
Jedes Icon trägt also seine eigene Prüfsumme: stimmt `star_idx` nicht
mit der rohen `location` des zugeordneten Schiffs überein, ist die
Zuordnung veraltet.

`s_ship_data.location` ist kodiert (consts.h:22, `Absolute_Location_`
in harold.cpp:815):

```
0     .. 9999   am Stern `location`
10000 .. 19999  unterwegs zu (location - 10000)
20000 .. 29999  im Wurmloch zu (location - 20000)
```

---

## Sternnamen und Wurmloch-Linien

### `MAINSCR::Get_Star_Name_` (mainscr.cpp:1253)

Entscheidet, ob und wie ein Stern beschriftet wird:

- **Ohne Galactic Lore, kein Kontakt zum Besitzer:** nie besucht →
  gar kein Name. Besucht → `star.name`.
- **Mit Lore oder Kontakt:** fremdes, nie besuchtes System →
  `snprintf(out, size, HAROLD::s___s__00556ae4, star->name)`, und
  `s___s__00556ae4` ist **`"(%s)"`** (harold.cpp:11). Sonst
  `star.name` unverändert.
- **Außenposten** (`Star_Is_Outpost_Star_`): Name in Kleinbuchstaben,
  Farbbereich um eine Stufe reduziert. In OrionLayer noch nicht
  umgesetzt.
- **Mehrere Kolonie-Besitzer** (`N_Colony_Owners_ > 1`): der Name
  wird als Bitmap gerendert und pro Besitzer eingefärbt
  (`Print_Star_Name_To_Bitmap_`). Ebenfalls noch nicht umgesetzt.

`Print_Star_Names_` (mainscr.cpp:505) steigt bei
`Is_Extended_Max_Map_View_` sofort aus — auf der maximal weiten Karte
gibt es überhaupt keine Sternnamen.

### `MAINSCR::Draw_Wormhole_Links_` (mainscr.cpp:623)

```cpp
if (wormhole_id != -1) {
    bool is_visible = Player_Has_Visited_(PLAYER_NUM, star_idx)
                   || Player_Is_Omniscient_(PLAYER_NUM);
    if (is_visible) {
        Get_Star_Draw_Coords_(star_idx,    &x1, &y1);
        Get_Star_Draw_Coords_(wormhole_id, &x2, &y2);
        line::Line_(x1, y1, x2, y2, 4);
    }
}
```

**Palettenindex 4** — ein dunkles Grau knapp über dem Sternenfeld.
Eine helle Linie liest sich als Grenze zwischen Regionen statt als
Route. Sichtbar ist ein Link nur, wenn das *Ausgangssystem* besucht
wurde; ein Paar wird von beiden Enden geprüft, und die beiden Enden
können sich unterscheiden.

---

## Kolonie-Subsystem

10.840 Zeilen in acht Dateien. Wer den Colony- oder den
Colony-Summary-Screen anfasst, fängt hier an.

| Datei | Zeilen | Rolle |
|---|---|---|
| `colcalc.cpp` | 3900 | Wirtschaftsrechnung, 103 Funktionen |
| `colony.cpp` | 2374 | Colony Screen (ID 1) |
| `colony_main.cpp` | 1295 | Ablauf des Colony Screens |
| `colsum.cpp` | 1264 | **Colony Summary (ID 20)** |
| `coldraw.cpp` | 849 | gemeinsame Zeichenroutinen |
| `colmove.cpp` | 587 | Bevölkerung aufnehmen und absetzen |
| `build_queue.cpp` | 544 | Bauliste |
| `colxport.cpp` | 314 | Transportansicht |

### Bevölkerungseinheiten — `pop.h`

Jede Einheit ist ein `uint32_t` mit Bitmasken:

| Maske | Bedeutung |
|---|---|
| `0x0000000F` | Rasse; 8 = Android, 9 = Native |
| `0x00000070` | ursprünglicher Besitzer |
| `0x00000180` | Beruf: 0 Farmer, 1 Arbeiter, 2 Forscher |
| `0x00000200` | zugewiesen (nicht „in der Hand") |
| `0x00000400` | erobert |

`COLONY::Pop_To_Pop_State_` (colony.cpp:1240) liefert in dieser
Implementierung nur drei Werte — 2 normal, 3 Native, 4 Android; die
Sieben-Zustände-Schleife in der Zeichenroutine ist Erbe von 1.31.

### Zeichnen und Klicken — `coldraw.cpp`

`Do_Colony_Info_Pop_Stuff_For_Pop_` (Zeile 281) macht über einen
`mode`-Parameter alles: 0 zeichnen, 1 Klickfelder anlegen, 2 Squish
berechnen, 3/4 Treffer suchen. Reihenfolge der Icons ist eine
fünffach verschachtelte Schleife über Zustand, Rasse-Flag, Beruf,
`pop_order` (beginnt mit 9, dann 0..8) und Pop-Index — keine
Sortierung, sondern Gruppierung.

`Calculate_Squish_Step_` (Zeile 12) staucht den 30-px-Schritt, wenn
die Icons nicht passen. **`30 / -3` ist C-Trunkierung Richtung Null**
— in Python `int(a / b)`, niemals `//`.

Spaltenkanten des Summary-Screens (colsum.cpp:311): Farmer 101–226,
Arbeiter 236–368, Forscher 378–502; Zeile *i* bei `y = 31*i + 34`,
zehn Zeilen sichtbar.

### Umverteilen — `colmove.cpp`

Klick–Klick, kein Ziehen (colsum.cpp:851 `Evaluate_Colony_Pop_Input_`).

- `Get_Cluster_` (56) hebt die Zuweisung des angeklickten Pops und
  aller **identischen** danach auf — `Pops_Identical_` (106)
  vergleicht Beruf, Zustand, Rasse und Erobert-Flag.
- `Send_Cluster_` (128) setzt sie ab; andere Kolonie = Transport mit
  ETA-Dialog über `SETTLER::Pop_Tries_To_Settle_`.
- `Give_Colonist_New_Job_` (518) hält fünf Regeln: Natives nur Farm,
  Androiden behalten den Beruf, max. 42 pro Beruf, Farmer ≤
  `max_farms` außer bei Transfer, sonst Fehlermeldung.

### Wirtschaft — `colcalc.cpp`

`Colony_Food2_Per_Farmer_` (542), `Colony_Industry_Per_Worker_` (579)
und `Colony_Research_Per_Scientist_` (627) schreiben ihre
Zwischenschritte in `s_colony_job_production`: Basis, Rassenboni, 14
Tech-Applikationen, Gebäudeboni, Gravitation, Verschmutzung, Moral,
Regierungsform, Blockade, Offizier, Schwierigkeitsgrad, Endwert.
Damit ist jede Produktionszahl **aufschlüsselbar** — das Original
zeigt nur die Summe.

Weiter: `Colony_Pop_Grows_` (760) Wachstum, `Colony_Food_Maintenance_`
(1148), `Colony_Industry_Maintenance_` (1045), `Colony_BC_Maintenance_`
(1243), `Apply_Assimilation_` (3500), `Mixed_Race_Morale_Penalty_`
(700).

### Reichszahlen — `COLSUM::Draw_Empire_Info_`

Sechs Zeilen, nativ bei (520, 354) gedruckt, jede ein ESTRING mit
einem `s_player`-Feld: `bc` (118), `surplus_bc` (106), `total_pop`
(114), `surplus_freighters` (103), `surplus_food` (102),
`research_produced` (117).

### Sortierung und Fenster

Neu gelesen am 3. September 2026 gegen **orion2re 1.60**
(`src/version.h`); alle Zeilennummern in diesem Abschnitt stammen aus
diesem Baum. Frühere Notizen nannten 1.31-Nummern.

`Sort_Col_List_` (colsum.cpp:363) ist ein Bubblesort über
`COLXPORT::_g_colony_list_ptr`, `MAX_COLONIES` volle Durchläufe ohne
Abbruch. `-1`-Einträge liefern 0 und wandern deshalb nicht.

**Die sieben Sortierköpfe** (colsum.cpp:267-273), alle
`Add_Multi_Button_Field_(x, 446, …, &_g_sort_index, N, hotkey, 41)`:

| `_x_fields` | x | `_g_sort_index` | Hotkey | Vergleicher | Richtung |
|---|---|---|---|---|---|
| 5 | 89 | 0 | ESTR 384 `n` | `cmp_Alpha_` (:1042) | aufsteigend |
| 6 | 140 | 1 | `p` | `cmp_Pops_` (:1064) | **negiert** |
| 7 | 219 | 2 | `f` | `cmp_Food_` (:1071) | **negiert** |
| 8 | 262 | 3 | ESTR 327 `i` | `cmp_Industry_` (:1076) | **negiert** |
| 9 | 326 | 4 | `s` | `cmp_Research_` (:1081) | **negiert** |
| 10 | 393 | 5 | ESTR 436 `r` | `cmp_Prod_` (:1091) | aufsteigend |
| 11 | 480 | 6 | ESTR 193 `b` | `cmp_BC_` (:1086) | **negiert** |

`Switched_cmp_` (colsum.cpp:378-401) schaltet per `switch` auf
`_g_sort_index`. **Es gibt keinen Richtungsumschalter.** Das
Vorzeichen steht als Literal im jeweiligen `case`; ein zweiter Klick
auf denselben Kopf sortiert identisch noch einmal. Fünf der sieben
sind absteigend, `Name` und `Producing` aufsteigend.

**Klick auf einen Sortierkopf** (colsum.cpp:825-838) — alle sieben
teilen sich einen Zweig:

```
Sort_Col_List_(); Clear_List_Col_Array_(); _first = 0;
Decrement_First_(10); Update_First_(10, …); Update_Col_List_();
```

`_first = 0` springt an den Listenanfang zurück. Das folgende
`Decrement_First_(10)` (colsum.cpp:207) bewegt `_first` nicht mehr —
`0 - 1` wird auf 0 geklemmt —, es setzt den Schieberegler.

**Das Zehn-Zeilen-Fenster.** `_list_col[10]` (colsum.cpp:15) ist ein
Fenster über die sortierte Liste; `Update_Col_List_` (colsum.cpp:348)
füllt es mit `_g_colony_list_ptr[_first + i]` für `i < 10`.
`Update_First_(10, &_first, &_slider_bar_position)` (colsum.cpp:193,
gerufen u. a. :456) setzt bei weniger als zehn Kolonien
`slider = -1, first = 0`.

Geometrie — **zwei verschiedene Zahlen, für zwei verschiedene
Zwecke**: gezeichnet wird bei `y = list_idx * 0x1F + 0x26`, also
`slot*31 + 38` (colsum.cpp:581); das *Klickband* einer Zeile ist
`y1 = slot*31 + 35` bis `y2 = slot*31 + 65` (colsum.cpp:285-307,
`y_row_end` startet bei 65 und wächst um 31, `y1 = y_row_end - 30`).
Der Name liegt bei x 12–101, die Produktion bei x 512–597, `Buy` bei
x 599.

Die Klickschleife ist `for (int i = 0; i < 10; ++i)` in
`Evaluate_Col_List_Input_` (colsum.cpp:893, Schleife :904). Zeilen
mit `_list_col[i] == -1` bekommen `-1000` statt eines Feldes, haben
also **keine** anklickbare Fläche. **Aber:** `_x_fields[0] =
Add_Hidden_Field_(0, 0, 639, 479, …)` (colsum.cpp:309) wird als
Letztes angelegt und deckt den ganzen Schirm ab — außerhalb der zehn
Zeilen gibt es keine *zeilenbezogene* Klickfläche, aber sehr wohl ein
Auffangfeld.

**Das Scroll-Feld und die Feld-IDs** (colsum.cpp:276-280):

```
if (num_colonies < 10) { _x_fields[12] = -1000; }
else { _x_fields[12] = Add_Scroll_Field_(621, 40, …); }
```

`-1000` ist ein Sentinel, **kein Feld** — bei weniger als zehn
Kolonien wird nichts angelegt, und jedes danach erzeugte Feld
bekommt eine um eins kleinere ID: `_x_fields[13]`, die dreißig
Zeilenfelder, die Pop-Felder aus `Add_Fields_Pop_For_`, und
`_x_fields[0]`. **Die Feldnummerierung dieses Screens hängt also von
der Kolonienzahl ab**, weshalb OrionLayer hier über Koordinaten
klickt und nicht über IDs (Entscheidung 39). Die Pfeile bei (619,15)
und (619,316) sind `_x_fields[1]` und `[2]` und existieren immer.

### Struktur — `s_colony`, 361 Byte, UNVERIFIZIERT

Feldreihenfolge aus `orion2.h:487` bekannt, Offsets nicht numerisch
bestätigt. Wichtige Felder: `owner`, `planet`, `n_pops`, `pop[42]`,
`max_farms`, `max_population`, `food2_per_farmer`,
`industry_per_worker`, `research_per_scientist`, `production[4]`,
`producing[7]`, `buildings[]`. Ohne Verifikation ist der
Summary-Screen ein Rahmen ohne Liste.

## Kontexthilfe (Rechtsklick)

Der Abschnitt, der beantwortet, warum ein Rechtsklick im Original
manchmal einen Textkasten öffnet statt abzubrechen.

### Der Auslöser — `fields::Check_Help_List_` (fields.cpp:2916)

`Get_Input_()` prüft bei gedrückter rechter Maustaste **zuerst** die
aktive Hilfeliste, an zwei Stellen (fields.cpp:1240 und 1364):

```cpp
if (_help_list_active != 0 && Check_Help_List_() == 0) {
    mouse::Mouse_Buffer_();
    mouse::Mouse_Buffer2_();
    return 0;                    // Klick geschluckt, kein Cancel
}
if (_mouse_cancel_disabled == 0) {
    ...
    return -1;                   // erst hier: Cancel
}
```

`Check_Help_List_` läuft die Liste in Reihenfolge durch, **der erste
Treffer gewinnt**, und ruft `TEXTBOX::Draw_Help_Entry_(help_id)`.
Ein `help_id` von -1 wird übersprungen.

### Die Tabellen

`s_help_box` (orion2.h:993) ist `{int16 help_id, x1, y1, x2, y2}`.
Jeder Screen installiert seine Liste per `fields::Set_Help_List_`;
die Listen selbst liegen in drei Dateien.

| Screen | Liste | Einträge | Ort |
|---|---|---|---|
| Main Menu | `_main_menu_screen_help_list` | 6 (645–650) | evanhelp.cpp:55 |
| New Game | `_new_game_screen_help_list` | 11 | erichelp.cpp:27 |
| Galaxy Map | `_main_screen_help_list` | 15 statisch | evanhelp.cpp:4 |
| Race Selection | `MOX::_help_entry_list` | 15, zur Laufzeit | racesel.cpp:129 |
| Custom Race | `MOX::_help_entry_list` | zur Laufzeit | raceopt.cpp:796 |
| Namens-/Bannerdialog | `_input_box_help_list` | 1 (675) | evanhelp.cpp:136 |

Drei Dinge, die man an der Galaxy-Map-Liste sehen muss. Erstens ist
die **Kartenfläche nicht darin** — ein Rechtsklick auf die Sterne
bedeutet dem Original nichts, weshalb OrionLayer dort frei mit der
rechten Taste schwenken kann. Zweitens hängt
`Set_Main_Screen_Help_List_` (evanhelp.cpp:229) je nach `_game_type`
und geöffneter Flottenbox weitere Einträge an; die 15 statischen sind
das, was immer gilt.

Drittens — und das ist eine Zahl, keine Beobachtung: die fünf
Sidebar-Anzeigen **kacheln ihre Spalte**. Zwischen zwei
aufeinanderfolgenden Rechtecken liegen exakt 2 native Pixel
(119→121, 193→195, 268→270, 342→344), viermal hintereinander, bei
einem Zeilenabstand von 74–76. Ein Rechtsklick trifft also praktisch
überall in der Spalte einen Eintrag. Wer die Liste nachbaut und die
Rechtecke stattdessen um den *Inhalt* legt, bekommt tote Streifen
zwischen den Anzeigen, die auf keinem Screenshot zu sehen sind.

Die einzige Ausnahme in der Tabelle ist die Stardate (284): 24–41,
also 17 Pixel in einer Zeile von 21, mit 4 Pixeln Abstand zur
Treasury. Sie ist der einzige Eintrag, der seine Zeile nicht füllt.

Mehrere Listen enden mit einem bildschirmfüllenden Eintrag
(`{545, 0, 0, 639, 479}` bei New Game). Das funktioniert nur, weil
der Lauf beim ersten Treffer stoppt — dieselbe Reihenfolge muss jeder
Nachbau einhalten.

### Der Text — `HELP.LBX`

`TEXTBOX::Draw_Help_Entry_` (textbox.cpp:307) lädt aus einer LBX,
deren Name aus `MOX::_settings.language` folgt
(`Get_Help_Lbx_Name_`, textbox.cpp:17):

```
0/Default HELP.LBX      1 GER_HELP.LBX   2 FRE_HELP.LBX
3 SPA_HELP.LBX          4 ITA_HELP.LBX
```

Eintrag 0 ist ein Record-Array im Format aus
`farload.cpp:90` (`Farload_Library_Data_`): `uint16 total_count`,
`uint16 element_size`, dann `count × element_size`. `element_size`
ist 1403 — `s_help_record` (orion2.h:1004), bestätigt durch
`ORION2RE_STATIC_SIZE_ASSERT(s_help_record, 0x57b)` in sizes.h:73:

```
char   title[80]
char   anim_lbx[14]
uint32 anim_info        untere 16 Bit = LBX-Record-Index
uint8  unknown_0x62
uint32 next_help_idx    0xFFFFFFFF = nächster Record folgt, 0 = Ende
char   body[1300]
```

Die Kette wird bis zu **neun** Records weit verfolgt. Titel und Text
werden in zwei Font-Stilen gesetzt (`Font_Colors2_(4, ...)` bzw.
`(2, ...)`), aber in **derselben Farbe** — an einem nativen
Screenshot gemessen RGB (72, 144, 56).

### Formatcodes im Hilfetext

Der Text ist **kein reiner String**. Er trägt die Steuercodes, die
`FMTPARA` beim Umbrechen auswertet (`fmtpara.cpp`):

| Code | Wirkung | Stelle |
|---|---|---|
| `\a` | Funktionssequenz, Buchstaben aus `"FRTXYSHVPIMOC^="`, Argumente durch `,` getrennt, Ende bei `.` oder dem nächsten `\a` | Process_Function_:384 |
| `\t` | zum nächsten Tabstopp | Paragraph_HT_:239 |
| `\r` `\v` | Zeilenvorschub | Process_Command_:324 |
| `\n` `\f` | Absatzvorschub | Process_Command_:321/334 |
| `\b` | Trennstellen-Hinweis | Record_Break_Position_ |
| 0x17–0x1F | Variablen-/Item-Maschinerie | Process_Command_:345 |

Argumentzeichen sind `_legal_fn_arg_chars = "1234567890+- "`; ein
führendes `+`/`-` bedeutet „relativ zur aktuellen Position" statt
„relativ zum Absatzrand".

Die für Tabellen entscheidende Funktion ist **X**
(`FN_Set_X_Pos_`): `new_x = val + x1`, also eine Spaltenposition im
Pixelraum des Absatzes — und der ist bei Hilfetexten 339 px breit
(`Draw_Help_Entry_` ruft `Get_Formatted_Paragraph_Max_Height_(0x153,
...)`). Der Command-Points-Eintrag steht roh so in der LBX:

```
\aX3.Frigate\aX97.-1 \aX150.Star Base\aX270.+1
```

Die Tabelle besteht also nicht aus Leerzeichen, sondern aus vier
absoluten Spalten. Wer den String ungefiltert zeichnet, bekommt
`X97.` als sichtbaren Text und keine Tabelle.

**Der Text steht nirgends im Quellcode und geht nicht über die
Ext-API.** Ein Client muss die LBX selbst lesen; OrionLayer tut das
mit `tools/help_extract.py`, nach demselben Muster wie
`nebula_extract.py` bei STARBG.LBX.

---

## Galaxy-Map Buttons (mainscr.cpp:1394)

Die Reihenfolge, aus der die Field-IDs 10..15 entstehen:

```cpp
_colonies_button = Add_Irregular_Button_Field_( 17,434, 79,471, ..., "C", 0x28);
_planets_button  = Add_Irregular_Button_Field_( 91,434,154,471, ..., "P", 0x28);
_fleets_button   = Add_Irregular_Button_Field_(167,434,230,471, ..., "F", 0x28);
_leaders_button  = Add_Irregular_Button_Field_(312,435,379,471, ..., "L", 0x28);
_races_button    = Add_Irregular_Button_Field_(386,435,453,471, ..., "R", 0x28);
_info_button     = Add_Irregular_Button_Field_(462,435,526,471, ..., "I", 0x28);
```

**Wichtig:** Feld 14 (Hotkey R) ist `_races_button`, nicht Research.
In der unteren Leiste gibt es überhaupt keinen Research-Button — die
Forschung wird über die Sidebar geöffnet. Der Field-Dump in der
Ext-API-Doku hatte hier zwei Wochen lang ein falsches Label.

---

## Race Selection und die drei Dialoge (racesel.cpp)

Der Ablauf, den OrionLayers Empire-Identity-Screen ersetzt.

```
Race_Selection_Screen_()                    racesel.cpp:180
  Zeile 203: 14 Radios per Add_Radio_Button_Field_
             Position (i/7)*126+351, (i%7)*48+90
  Zeile 212: [EXT-Patch] _current_screen = SCREEN_RACE

  Klick auf Stock-Rasse, _custom_flag == 0  (Zeile 245 ff.)
    → Clear_Fields_, Traits kopieren, race setzen
    → Zeile 253  Naming_Popup_()      Ruler-Name
    → Zeile 262  Flag_Screen_()       Bannerfarbe
       (do/while: ESC im Banner geht zurück zum Namen)
    → screen_state == 2 → done_flag = 1

  Klick auf Custom, _custom_flag == 1
    → Zeile 305  Racial_Option_Screen_()
       Zeile 454 [EXT-Patch] _current_screen = 50
       Zeile 634 [EXT-Patch] Restore bei Cancel
       Accept  → Zeile 662  Naming_Popup_()
                 Zeile 675  Flag_Screen_()
                 Zeile 692  _current_screen = _return_screen
```

Beide Pfade rufen **dieselben zwei Funktionen** auf. Ein externer
Client kann die Abläufe also nicht an der Screen-ID unterscheiden,
sondern nur an der Form der Feldliste.

| Funktion | Zeile | Felder |
|---|---|---|
| `Naming_Popup_` | 766 | delegiert an `namestar::Input_Box_Popup_Animated_`; ein String-Feld (Typ 11) — dieselbe Routine wie die Heimatstern-Benennung |
| `Flag_Screen_` | 844 | 8 Kacheln per `Add_Hidden_Field_` (Typ 7, nicht Radio!), vergleicht `Get_Input_()` gegen die Feld-IDs → ACTIVATE_FIELD ist exakt richtig |

Namenslängen: `Naming_Popup_` arbeitet mit einem 20-Byte-Puffer
(`s_player.name[20]` → 19 Zeichen); Sternnamen
`s_star_data.name[15]` → 14 Zeichen.

**Multiplayer-Vorbehalt:** `Flag_Screen_` legt nur für Farben mit
`_color_flag[i] == 0` ein Feld an. Bei vergebenen Farben gibt es
weniger als 8 Kacheln — eine Erkennung „>= 8 Felder" schlägt dann
fehl.

---

## Screen-Enum (SCREEN)

| ID | Name | OrionLayer-Screen |
|---|---|---|
| 0 | SCREEN_MAIN | galaxy_map |
| 1 | SCREEN_COLONY | colony |
| 3 | SCREEN_DESIGN | ship_design |
| 4 | SCREEN_FLEET | fleet |
| 6 | SCREEN_RACE | select_race |
| 9 | SCREEN_INFO | info |
| 10 | SCREEN_MAIN_MENU | main_menu |
| 13 | SCREEN_NEW_GAME | new_game |
| 18 | SCREEN_PLANET_DATA | planet_data |
| 20 | SCREEN_COLONY_SUMMARY | colony_summary |
| 25 | SCREEN_QUEUE_POPUP | (Build-Queue-Popup) |
| 29 | SCREEN_OFFICERS | leaders |
| 30 | SCREEN_COLONIZATION_IN_MAIN | (Overlay) |
| 32 | SCREEN_PLANET_SUMMARY | planets |
| 36 | SCREEN_TECH_CHANGE | research |
| 39 | SCREEN_REPORTS | reports |
| 40 | SCREEN_TURN_SUMMARY | turn_summary |
| **50** | (kein Enum-Wert) | custom_race — synthetisch per Ext-Patch |

---

## Wichtige Funktionen (Schnellreferenz)

### Galaxy-Map Zeichnen

```
MAINSCR::Draw_Stars_()              mainscr.cpp:145
  → überspringt Black Holes, prüft Star_On_Screen_
  → Draw_A_Star_()                  mainscr.cpp:469
     → Map_Scale_Star_Size_To_Zoom_Level_()  harold.cpp:1066
     → Get_Star_Picture_Seg_()      mainscr.cpp:368
     → Draw_Scaled_Star_Picture_()  mainscr.cpp:20

MAINSCR::Draw_Black_Holes_()        mainscr.cpp:705
MAINSCR::Print_Star_Names_()        mainscr.cpp:504
MAINSCR::Get_Star_Draw_Coords_()    mainscr.cpp:389
MAINSCR::Draw_Influence_Overlay_()  mainscr.cpp:155
HAROLD::Get_Scaled_Value_()         harold.cpp:169
```

### Schiff-Positionierung

```
SHIPS::Build_Ship_Icons_()          ships.cpp:632
SHIPS::Get_Ship_Icon_Coords_()      ships.cpp:202
SHIPS::Get_XYs_For_Orbiting_Ships_() ships.cpp:289
SHIPS::Set_Ship_Icon_XYs_()         ships.cpp:39
MAINSCR::Draw_Ship_Icons_()         mainscr.cpp:965
```

Slot-Geometrie, `Get_XYs_For_Orbiting_Ships_` (ships.cpp:289):

```
slot 0     x = star_x - star_size/2 + star_size - width/2 + (1 - zoom)
           y = star_y - star_size/2 + (1 - zoom) - 1     rechts vom Stern
slot 1     x = star_x - star_size/2 - width/2 - (1 - zoom) + 2
           y = star_y - star_size/2 + (1 - zoom) - 2     links vom Stern
slot 2..4  x = slot1_x - 1
           y = slot1_y + n * (11 - zoom)                 Stapel darunter
slot 5     x/y = Get_Scaled_Value_(ship.x/y)             im Flug
```

Der Stapelabstand `11 - zoom` ist die harte Grenze für die
Icon-Höhe. `Draw_Ship_Icons_` zeichnet **rückwärts**
(`for i = count-1; i >= 0; --i`), damit Slot 0 — der lokale Spieler —
oben liegt.

`_ship_icon[].x/y` sind fertige 640x480-Bildschirmkoordinaten mit der
**oberen linken Ecke** als Anker. Ein externer Client muss die
Slot-Geometrie also nicht nachbauen; sie steht hier nur, um Größen
und Abstände zu erklären.

### Field-System

```
fields::Get_Input_()              Haupt-Einstieg, innere Schleife
  → Interpret_Mouse_Input_()      Radio-Toggle passiert HIER
    → Scan_Field_()
  → Interpret_Keyboard_Input_()
fields::Add_Button_Field_()
fields::Add_Radio_Button_Field_()   Typ 1 — nur per INJECT_CLICK
fields::Add_Hidden_Field_()         Typ 7 — ACTIVATE_FIELD geht
fields::Add_Irregular_Button_Field_()
fields::Add_Hot_Key_()
```

### Screen-Hauptschleifen

```
MAINMENU::Main_Menu_Screen_()       mainmenu.cpp
NEWGAME::Newgame_Screen_()          newgame.cpp
MAINSCR::Main_Screen_()             mainscr.cpp
COLONY::Colony_Screen_()            colony.cpp
RACESEL::Race_Selection_Screen_()   racesel.cpp:180
RACESEL::Racial_Option_Screen_()    racesel.cpp:442
SCIENCE::Science_Screen_()          science.cpp
DIP_SCRN::Diplomacy_Screen_Main_()  dip_scrn_main.cpp
COMBAT::Tactical_Combat_()          combat.cpp
```

---

## Globale Variablen (`mox.h`)

```cpp
MOX::_stardate            // int32, Stardate x 10
MOX::_PLAYER_NUM          // int16
MOX::_NUM_STARS/_SHIPS/_COLONIES/_PLAYERS/_NUM_NEBULAS
MOX::_player[8]           // s_player
MOX::_star[] _ship[] _colony[] _planet[] _nebula[] _leaders[67]
MOX::_ship_icon[]         // Galaxy-Map Position
MOX::_cur_map_scale       // Zoomstufe (10/15/20/30)
MOX::_cur_map_x/_cur_map_y
MOX::_MAP_MAX_X/_MAP_MAX_Y
MOX::_max_map_scale       // NICHT serialisiert — aus MAP_MAX_X
MOX::_max_zoom_count      // NICHT serialisiert — aus MAP_MAX_X
MOX::_star_fields_dim[6]  // Sprite-Pixelgrößen
MOX::_star_seg[]          // geladene Stern-Sprites
MOX::_star_colors_seg[11] // gstar.lbx, für Kolonie-/Summary-Screens
```

---

## Legacy-Format Differenzen (v0 vs orion2re v1)

| Struct | Feld | Legacy | orion2re v1 |
|---|---|---|---|
| `s_player` | settlers[25] | uint32 | uint64 |
| `s_player` | offensive_stagepoint | int8 | int16 |
| `s_star_data` | wormhole_star_id | int8 | int16 |
| `s_star_data` | next_wfi_in_list | uint8 | int16 |
| `s_star_data` | black_hole_blocks | 9 Bytes | BITMAP(MAX_STARS) |
| `s_planet_data` | star_index | int8 | int16 |

---

## Dokumentation im Repo

| Datei | Inhalt |
|---|---|
| `docs/fields.md` | Field-System (UI/Input), sehr detailliert |
| `docs/150vars.md` | CP 1.50 Variablen-Inventar |
| `docs/config.md` | Konfigurations-/Mod-System |
| `docs/deterministic-net.md` | Multiplayer-Synchronisation |
| `docs/modding.md` | Mod-Autor-Guide |
| `docs/testing.md` | Test-Strategie |

---

## Arbeitsweise

Zwei Regeln, die sich in jeder Sitzung bestätigt haben:

1. **Erst den Quellcode lesen, dann Theorien bilden.** Symptome
   führen zuverlässig in die Irre; eine Funktion im Baum klärt die
   Frage meist in Minuten.
2. **Zwei unabhängige Quellen vor jedem Produktivwert.** Header plus
   Live-Probe, oder Header plus static_assert. Was nur aus einer
   Quelle stammt, wandert nach `unverified.py`.

Ein Field-Dump ist keine Quelle: Die Ext-API liefert Geometrie, Typ
und Hotkey — jedes Label darin ist Interpretation, bis der Quellcode
sie bestätigt.
