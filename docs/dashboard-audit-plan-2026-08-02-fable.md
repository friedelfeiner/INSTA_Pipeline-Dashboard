# Dashboard-Audit — Befunde & Abarbeitungsplan (Fable-Check-up)

Stand 02.08.2026 · Zweitprüfung des Plans `dashboard-audit-plan-2026-08-02.md` durch Fable.
Jede Behauptung wurde gegen `index.html`, das Pipeline-Repo und **live gegen Supabase**
nachgeprüft: alle Messwerte des Originals sind reproduzierbar (91/76 Zeilen, 34 ohne
Telemetrie, 0 Snapshots mit Horizont `24h`, Narrator 26 Zeilen, Assembler 4×running/4×error,
Advisor-Stand inkl. publish_queue ohne Policy). Auch die Zeilennummern stimmen durchgehend.

**Modelle in diesem Plan:** Haiku (mechanisch, exakt spezifiziert) · Sonnet (Standard-Implementierung)
· Opus (Urteil statt Ausführung)

---

## Was der Check-up gegenüber dem Original ändert

1. **A war in sich widersprüchlich.** A1 stellt `fetchEtappen()` aufs View um, A3 lässt den
   Kosten-Tab „auf `etappen`" — aber beide Ansichten hängen an *derselben* `data.etappenList`
   aus dem *einen* `fetchEtappen()`-Call. Es gibt keinen zweiten Fetch, den A3 belassen könnte.
   → A umgebaut: ein `fetchAll` auf `etappen` (nur 91 Zeilen), Dedupe client-seitig, zwei Listen.
2. **Fünfter Lese-Pfad fehlte.** `fetchMonologListe()` (Zeile 211) liest ebenfalls
   `etappen` mit `order=datum.desc&limit=30` — und Redos tragen `tages_monolog` in die neue
   Run-Zeile weiter (`main.py:676-684`, `_carry`). Das Monolog-Archiv zeigt Redo-Tage doppelt.
   → neu in A2.
3. **C2 ist mit den heutigen Spalten nicht exakt implementierbar.** Für die Plattform-Zuordnung
   (wan27→WaveSpeed, hero→Atlas) fehlen die Stückzahlen: `etappen` hat nur `t2i_count` und
   `video_count` (Summe flash+wan27), kein `wan27_count`/`hero_count`. → C2 präzisiert, neue
   Option „counts-Dict persistieren" (C2a).
4. **D3 hätte einen neuen Bug eingebaut.** „error gewinnt gegen späteres running" heißt: ein
   legitimer Retry (error → running → done) bliebe für immer als Fehler stehen. Die richtige
   Regel läuft über die Varianten-Kennung aus D1, nicht über eine pauschale Status-Hierarchie.
   → D3 umformuliert.
5. **`EtappeDetailModal` hat dieselbe kaputte Gruppierung** (Zeile 1197-1200, im Code sogar als
   „same logic as TabProgress" markiert). E1 will genau dieses Schritte-Panel in den
   Reliability-Tab holen — dann wandert der Verschluck-Bug mit. → neu D9.
6. **E2g rennt in eine bekannte Wand.** `insights_poller.py` dokumentiert (live verifiziert
   22.07.): `profile_visits`, `follows`, `impressions`, `plays` sind für
   `media_product_type=REELS` **nicht** verfügbar — „nicht wieder aufnehmen". `profile_activity`
   ist derselbe Metrik-Familie. → E2g auf einen Kurz-Check mit Erwartung „nein" abgeschwächt;
   die Conversion-Frage gehört zu `account_insights` (I1) und den Story-Insights (I4).
7. **B braucht drei Ergänzungen:** (a) `trend28`, `retryHistory`, `durationHistory`,
   `tripTotal` werden in `transformData()` routen-gemischt gebildet — wenn die Liste gefiltert
   wird, müssen die Reihen aus der gefilterten Liste kommen, sonst zeigt die Übersicht weiter
   gemischte Routen. (b) `selectedIdx` ist ein Listen-Index — bei Filter-/Sortierwechsel muss
   die Auswahl per Etappen-`id` stabil bleiben, sonst springt die gewählte Etappe. (c) Das
   Routen-Dropdown rendert nur bei `curEtappe.kuerzel` (3761) — nach dem Umbau muss es immer da
   sein. → B8–B10.
8. **H kann schärfer.** Kein einziger Nutzer der drei SECURITY-DEFINER-Views in beiden Repos
   (grep leer, nur alte Audit-Docs erwähnen sie). → Erste Option ist jetzt **droppen**, nicht
   reparieren. Advisor-Detail live: die „3 WARN" sind 1× `search_path` (H4) + 2×
   „RLS Policy Always True" auf `etappen`/`stile` — letztere gehören inhaltlich zu K, nicht H.
9. **G5 braucht eine Schreibseiten-Regel.** `Hitl1Panel.freigeben()` schreibt
   `JSON.stringify(...)` (String in jsonb) — das *ist* die kanonische Form, alle 25 DB-Zeilen
   sind Strings, die Pipeline-Leser (`_varianten_laden`, `golden_assemble`) können beide Formen.
   Beim defensiven Lesen die Schreibform **beibehalten**, nicht „reparieren" — sonst entstehen
   gemischte Formen in der DB.

Alles andere aus dem Original hält der Prüfung stand und steht unten unverändert bzw. gestrafft.

---

## Was gemessen wurde (Original, von Fable live reproduziert)

| Messung | Ergebnis |
|---|---|
| Die 60 Zeilen, die `fetchEtappen()` lädt | **15 veraltete Run-Dubletten**, nur **45 echte Tage** |
| `etappen` gesamt / `etappen_aktuell` | 91 / **76** Zeilen — View ist für `anon` lesbar ✓ |
| Etappen ohne Telemetrie | **34 von 91** — das Dashboard zeigt sie als „€0.00" ✓ |
| `narrator`-Zeilen im letzten Lauf | **26** (10 running / 9 done / 7 skipped), ohne Stil-Kennung ✓ |
| `assembler` im letzten Lauf | 4× running, **4× error** ✓ |
| `t2i_bild` in `PREISE_USD` | **$0.067** — Dashboard rechnet mit **$0.030** ✓ |
| `reel_metrics` mit Horizont `24h` | **0** — das engste Fenster wurde nie getroffen ✓ |
| `reel_varianten` in der DB | alle 25 Zeilen jsonb-**String** ✓ |
| Supabase-Advisor `security` | 3× ERROR (Definer-Views) · 1× WARN search_path · 2× WARN USING(true) · publish_queue RLS ohne Policy ✓ |
| LaunchAgent `com.insta.insights` | in `launchctl list` **nicht geladen** ✓ — Rückkanal läuft von Hand |

---

## Block A — Datenquelle geradeziehen 🔴
Modell: Sonnet · Effort: high · Thinking: standard
Begründung: Der größte aktive Fehler. Gegenüber dem Original umgebaut (siehe Check-up Nr. 1):
`fetchEtappen()` bleibt auf `etappen`, holt aber **alles** und dedupliziert client-seitig —
weil der Kosten-Tab die Runs einzeln braucht und beide Ansichten an einem Fetch hängen. Die
eigenständigen Lese-Pfade (HITL, Historie, Monolog-Liste) wechseln aufs View.

**Befund D-1 (bestätigt):** `fetchEtappen()` (129), `fetchEtappenFuerHitl1()` (2388),
`fetchEtappenHistorie()` (2399), `fetchEtappenFuerHitl2()` (2703) **und
`fetchMonologListe()` (211)** lesen `etappen` mit `order=datum.desc&limit=N` — Redo-Dubletten
fressen das Limit, Style-Bewertungen können auf toten Run-1-Zeilen landen, das Monolog-Archiv
zeigt Redo-Tage doppelt (Redos tragen `tages_monolog` weiter, `main.py` `_carry`).

- [x] **A1** `fetchEtappen()` auf `fetchAll('etappen?select=…')` umstellen (91 Zeilen, kein
  Limit-Problem mehr), `run` mitselektieren. `transformData()` baut daraus **zwei Listen**:
  `etappenList` = pro (`route_id`, `datum`) nur der höchste `run` (gleiche Logik wie das View),
  `etappenListAlleRuns` = ungefiltert für den Kosten-Tab
- [x] **A2** `fetchEtappenFuerHitl1()`, `fetchEtappenHistorie()`, `fetchEtappenFuerHitl2()`
  **und `fetchMonologListe()`** auf `etappen_aktuell` umstellen (PATCHes bleiben auf `etappen`
  — das View ist nicht updatebar; die `id` aus der View-Zeile ist dieselbe)
- [x] **A3** Kosten-Tab auf `etappenListAlleRuns` umstellen und Run-Badge in der Zeile zeigen,
  wie `TabReels` es bei `e.run > 1` schon macht (3046-3049)
- [x] **A4** Gegenprobe: Zeilenzahl `etappen_aktuell` (Content-Range) gegen `etappenList.length`
  rechnen; ein Redo-Tag darf in Etappen-Liste, Pfeil-Navigation und Monolog-Archiv nur noch
  einmal stehen, im Kosten-Tab bewusst zweimal (mit Badge)

---

## Block B — Etappen-Navigation: Sortierung, die man vorhersagen kann 🔴
Depends on: Block A
Modell: Opus · Effort: high · Thinking: standard
Begründung: unverändert — die Reihenfolge-Frage ist wichtiger als der Code. Neu sind B8–B10:
die Nebenrechnungen und die Auswahl-Stabilität, ohne die der Umbau an anderer Stelle
Folgefehler erzeugt.

**Befund (bestätigt):** `transformData()` (282) baut `[...valid].reverse()` — rein nach
Wandertag über alle Routen, Routen-Datumsbereiche überlappen sich (Route `51e83f21` spannt
Mai 2025–Apr 2026, mittendrin die zehn nie gelaufenen `1ec25174`-Tage). Das Routen-Dropdown
(3778) springt nur zu `firstIdx`, die Pfeile (3590-3606) laufen über die volle Liste.
Kopfzeile zeigt Wandertag, KPI „letzter Run" hängt an `run_at` — zwei Reihenfolgen in einer
Ansicht.

**Entschieden (Flo, 02.08.):** Nach Route gruppieren **und** Route als echten Filter schaltbar
machen; Wahlschalter Wandertag ↔ Rechendatum; Voreinstellung Wandertag.

- [x] **B1** Routen-Auswahl von „springt zu Index" auf „filtert die Liste" umbauen;
  „Alle Routen" bleibt als Option
- [x] **B2** Sortierung auf „Route, dann Wandertag" umstellen; ohne Routenfilter Routenwechsel
  sichtbar machen (Trennzeile oder Kürzel-Badge je Zeile)
- [x] **B3** Schalter „Wandertag / Rechendatum" in die Kopfzeile; Zustand gilt für Liste,
  Pfeile und Tabellen gemeinsam
- [x] **B4** Pfeil-Navigation und Tastatur-Handler (3590-3606) gegen die gefilterte Liste
  laufen lassen
- [x] **B5** Etappen ohne `run_at` im Rechendatum-Modus ans Ende, Kennzeichnung „nie gelaufen"
  statt stumm €0.00. **Korrektur zur Annahme:** es sind nicht zehn, sondern **31 von 76**
  Etappen ohne `run_at` (live gemessen 02.08.) — der Fall ist deutlich häufiger als gedacht
- [x] **B6** Kopfzeile ergänzt neben „Tag N · Datum" auch das Rechendatum
- [x] **B7** Mobil: Routenfilter und Sortierschalter als Chip-Leiste unter den Titel, nicht
  daneben
- [x] **B8** *(neu)* Nebenreihen aus der **gefilterten** Liste bilden: `trend28`,
  `retryHistory`, `durationHistory`, `tripTotal`/`tripKuerzel`/`tripEtappenCount` — heute
  rechnen sie in `transformData()` routen-gemischt über `valid`
- [x] **B9** *(neu)* Auswahl per Etappen-`id` statt `selectedIdx` führen (oder bei jedem
  Filter-/Sortierwechsel den Index über die `id` neu auflösen) — sonst zeigt der Wechsel des
  Schalters plötzlich eine andere Etappe
- [x] **B10** *(neu)* Routen-Dropdown auch rendern, wenn die aktuelle Etappe kein `kuerzel`
  hat (heute Gate auf `curEtappe.kuerzel`, 3761) — nach B1 ist es der Filter-Einstieg und muss
  immer erreichbar sein

---

## Block C — Kosten: Label und Wert wieder deckungsgleich 🔴
Depends on: Block A
Modell: Sonnet · Effort: high · Thinking: standard
Begründung: Grundsatz entschieden (Schätzwert bleibt, Ist-Kosten-Tab ist die Wahrheit).
Gegenüber dem Original präzisiert: die Plattform-Zuordnung braucht Stückzahlen, die es noch
nicht gibt (Check-up Nr. 3) — deshalb der kleine Telemetrie-Eingriff C2a.

**Befund D-2 (bestätigt):** `platformCosts()` (88-97) rechnet `t2i` mit $0.030 statt $0.067
(Balken ~2,2× zu niedrig), bucht `cost_video_eur` komplett auf Atlas obwohl der Roboter-Hero
(`wan27_clip` $1.50) über WaveSpeed läuft, nutzt hartes 0.88 statt `meta.kurs_usd_eur`
(0.8765), Kommentar nennt noch Seedream. `Math.max(0, …)` (95) kappt negative Atlas-Werte —
die Balken summieren sich nicht mehr auf den Gesamtbetrag.

**Befund D-3 (bestätigt):** „Anthropic" = `cost_llm_eur` = Claude **+ Gemini** (Analyst läuft
default auf Gemini Flash). „FAL.ai" = `cost_tts_eur` = ElevenLabs **+ MiniMax + Suno**
(`pipeline_telemetry.py` sagt es selbst: kein eigenes `cost_musik_eur`-Feld).

- [x] **C1** Einheitspreise als eine Quelle: `tools/costs_report.py --json` schreibt
  `PREISE_USD` (plus Anbieter-Zuordnung je Posten) als eigenen Block mit nach
  `costs_data.json`; `platformCosts()` liest von dort. (`--json` schreibt schon heute direkt
  ins Dashboard-Repo — es kommt nur der Preisblock dazu.)
- [x] **C2** Preise nachziehen, Kurs aus `meta.kurs_usd_eur` statt hartem 0.88, Kommentar
  Seedream→Nano Banana 2. **Achtung Genauigkeit:** exakte Plattform-Zuordnung braucht C2a;
  bis dahin Heuristik (Hero = 1 `wan27_clip`/Run) nur mit sichtbarem „≈"
- [x] **C2a** *(neu, Pipeline-Repo)* `RunTelemetry.counts` (t2i_bild, flash_clip, wan27_clip,
  hero_bild, tts, tts_minimax, suno_song) als jsonb-Spalte `unit_counts` in `etappen`
  persistieren — Migration + eine Zeile in `to_db_dict()`. Damit rechnet das Dashboard die
  Plattform-Split exakt statt heuristisch; C1 greift ohnehin ins Pipeline-Repo
- [x] **C3** Die Schätzung als Schätzung beschriften — „hochgerechnet aus Einheitspreisen ·
  Belege im Ist-Kosten-Tab"
- [x] **C4** `Math.max(0, …)` entfernen oder Rest als „sonstiges" ausweisen, damit die Balken
  aufgehen (Z-1)
- [x] **C5** Balken „Anthropic" → „LLM (Claude + Gemini)", „FAL.ai" → „TTS + Musik"
- [x] **C6** (Z-3) Kosten-Trend-Achse (858): hartes `T1 T7 T14 T21 T28` durch echte
  Tag-Nummern ersetzen (entfällt teilweise mit Block B)
- [x] **C7** `cost_total_eur = null` nicht mehr als €0.00 rendern: „–" plus „ohne Telemetrie"
  in Tabelle, KPIs und Summen; Ø nur über Etappen mit Telemetrie. Betroffene Stellen über
  Zeile 296 hinaus: `trend28` (315) mappt null→0 in die Kurve, `reliabilityStats.ran` (393)
  nutzt `cost > 0` als „ist gelaufen"-Proxy
- [x] **C8** (Z-4) `successRate` (395) an `statusMap` koppeln und `resolved` aus `errors[]`
  auswerten — heute gilt ein Run mit `pipeline_status='fehler'` ohne Errors-Eintrag als Erfolg

---

## Block D — Live Run: die Anzeige passt nicht mehr zur Pipeline 🔴
Modell: Opus · Effort: xhigh · Thinking: standard
Begründung: unverändert ein Neubau der Ansicht, kein Label-Fix. Gegenüber dem Original: D3
umformuliert (hätte sonst erfolgreiche Retries dauerhaft als Fehler gezeigt, Check-up Nr. 4)
und D9 neu (dieselbe Gruppierungslogik steckt auch im `EtappeDetailModal`).

**Bestätigt gegen main.py/variant_runner/DB:** Die zehn real geschriebenen Step-Namen sind
exakt `analyst, map, narrator, selektor, imagegen, animator, audio, assembler,
carousel_publisher, blog_publisher`. `publisher` und `carousel` (im Dashboard vorhanden)
werden nie geschrieben. `log_pipeline_step()` kennt keine Varianten-Kennung; `TabProgress`
(1463-1470) nimmt die letzte Zeile pro Name — deshalb verschwinden die vier Assembler-Fehler
des letzten Laufs hinter einem „läuft…", der Fortschritt zählt Namen statt Soll-Schritte.

**Erledigt 02.08.** Zwei Nachträge zum Befund: (a) `publisher` ist durch D7 kein toter Name
mehr, die Soll-Liste hat elf Einträge. (b) Der Verschluck-Bug ist genauer ein *Live*-Bug —
im Lauf vom 23.07. war die zeitlich letzte Assembler-Zeile zufällig ein `error`, sichtbar
wurde der Fehler erst nach dem Lauf. Während des Laufs verdeckt jedes `running` einer
anderen Variante den Fehler der vorigen; genau das behebt D3.

- [x] **D1** Pipeline: `log_pipeline_step()` um `variante` erweitern (Migration
  `pipeline_steps.variante` + Aufrufer in `variant_runner.py`), damit parallele Stile
  unterscheidbar werden. **Umgesetzt:** Migration `20260802130000` (+ Index auf
  `(etappe_id, ts)`), alle Aufrufer in `variant_runner.py` tragen die Kennung. Der
  Sammel-Log des parallelen Audio-Dispatch wurde auf **pro Variante** umgebaut — die
  Inserts laufen bewusst im Main-Thread (vor dem Thread-Start bzw. nach dem Join), die
  Audio-Threads bleiben schreibfrei (dokumentierter Grund: gleichzeitige Supabase-Calls
  aus diesen Threads haben die Leitung gekippt). `original_images` loggt jetzt ebenfalls
  Audio + Assembler, sonst fehlte die fünfte Variante in der Zählung
- [x] **D2** Dashboard: feste Soll-Reihenfolge der Schritte statt „Reihenfolge des ersten
  Auftretens"; noch nicht begonnene Schritte grau vorzeigen (Skips bleiben möglich —
  personal_hook-Läufe überspringen z. B. map/selektor)
- [x] **D3** *(präzisiert)* Statusregel pro **(step, variante)**: innerhalb einer Variante
  gewinnt die letzte Zeile (ein done nach error ist ein gelungener Retry und darf das error
  ablösen); auf Step-Ebene wird über die Varianten **aggregiert** — ein Step zeigt Fehler,
  solange irgendeine Variante zuletzt auf `error` steht. Nur so verschwinden Fehler nicht und
  erfolgreiche Retries bleiben trotzdem grün. **Grenze:** Läufe von vor D1 haben überall
  `variante = NULL` und fallen auf eine Gruppe pro Schritt zusammen — rückwirkend nicht
  auflösbar, die Kennung wurde damals nicht geschrieben
- [x] **D4** Schritte mit mehreren Varianten als Gruppe zeigen („audio · 3/5 fertig,
  1 Fehler") statt als eine Zeile. Auch eine **einzelne benannte** Variante wird
  aufgeschlüsselt, sonst steht bei „Assembler · läuft…" nicht, welcher Stil rendert
- [x] **D5** Fortschritt aus der Soll-Liste rechnen, nicht aus der Zahl gesehener Namen
  (übersprungene Schritte zählen als erledigt)
- [x] **D6** `STEP_LABELS`/`STEP_DESCRIPTIONS`/`PROGRESS_UNIT` auf die echten Namen
  bringen; `carousel` gestrichen. **Abweichung:** `publisher` bleibt — durch D7 wird er
  jetzt tatsächlich geschrieben. Die Soll-Liste hat damit **elf** Namen, nicht zehn
- [x] **D7** ~~Entscheiden~~ **Entschieden (Flo, 02.08.): die Edge Function schreibt mit.**
  Slot 1 (Prio-Post) loggt die Pipeline in `variant_runner.py`, Slots 2–5 loggt
  `ig-publish-queue` beim Container-Bau und beim Posten — `publish_queue.etappe_id` +
  `variante_stil` liefern die Zuordnung. Der Log ist rein additiv und best-effort
  (`try/catch`), ein fehlgeschlagener Insert kann das Posten nicht beeinflussen. Function
  als **v5** deployt (`verify_jwt: false` unverändert), Queue war dabei leer
- [x] **D8** Hänger erkennen: Step > 30 Min auf `running` → „abgebrochen?" statt „läuft…"
  (pro Variante, in der Bilanz getrennt von echten Fehlern ausgewiesen)
- [x] **D9** *(neu)* Dieselbe Gruppierung im `EtappeDetailModal` (1197-1200) mitziehen — E1
  holt genau dieses Schritte-Panel in den Reliability-Tab, der Verschluck-Bug darf nicht
  mitwandern. Beide Ansichten teilen sich `gruppiereSteps()`; das Modal blendet nie
  begonnene Schritte aus (`zeigeOffene: false`) — es ist Protokoll, keine Vorschau

---

## Block E — Tabs, die die gewählte Etappe ignorieren 🟠
Depends on: Block A
Modell: Sonnet · Effort: high · Thinking: standard
Begründung: unverändert. E3 konkretisiert (die Übersicht deckt die entfallenden Zahlen heute
**nicht** ab), E2g abgeschwächt (Check-up Nr. 6).

**Bestätigt:** `TabReels()` (2908) nimmt keine Props — `data` und `selectedEtappe` werden
ignoriert. `TabReliability` (1060) mischt Bezugsgrößen: „Retries (gewählter Run)" ist die
einzige etappenbezogene Zahl, `slice(-12)` (379) sind die letzten 12 **nach Wandertag**, die
Retry-Karten behaupten pauschal „alle resolved" (1160), das `resolved`-Flag aus der Telemetrie
(sie schreibt es, `add_error(resolved=…)`) wird nie gelesen.

**Entschieden (Flo, 02.08.):** Reliability bleibt ein Etappen-Tab und zeigt nur noch die
gewählte Etappe; die Reise-Aggregate wohnen in der Übersicht.

- [x] **E1** `TabReliability` auf die gewählte Etappe eindampfen: Retries nach Agent,
  Fehlerliste, Pipeline-Schritte dieses Runs (nutzt das D9-bereinigte Panel)
- [x] **E2** Reels-Tab umbauen — Details unten
- [x] **E3** *(konkretisiert)* Die Übersicht zeigt heute nur Retry-Verlauf + Top-3-Events —
  **Erfolgsrate und Retries Reise Σ fehlen dort** und müssen ins Übersicht-Reliability-Panel
  einziehen, bevor E1 sie aus dem Tab entfernt
- [x] **E4** `resolved`-Flag aus `errors[]` auswerten statt pauschal „alle resolved"
- [x] **E5** „letzte 12 Runs" nach Rechendatum bilden (nutzt Block B/B8)

### E2 im Detail — welche Zahlen es gibt (bestätigt am 02.08.)

Instagram: 79 Snapshots · 31 Etappen · 5 Stile, alle neun Metriken gefüllt. YouTube: 10
Snapshots · 2 Etappen, nur views/likes/comments — Watch-Time liefert `videos.list` nicht.
Facebook: nichts (Token ohne `read_insights`). Größenordnungen: Ø ~100 Views ≈ Reach,
Retention 5–8 %, Likes Ø ~1.

Daraus (unverändert gültig): Likes/Kommentare zeigen, nicht ranken · Views ≈ Reach heißt
„Explore-Zuteilung, nicht Qualität" · Retention bleibt Leitgröße ·
Plattformen getrennt ausweisen, nie mitteln (IG ~100 Views vs. YT Ø 6 — ein Mittel wäre
IG-dominiert) · `watch_time_total_sec` ist die ungenutzte zweite Leitgröße · der
Horizont-Verlauf (24h→…→90d) liegt vollständig vor und wird nirgends gezeigt.

⚠️ Erwartungsdämpfer bleibt: Acquapendente → Bolsena hat **eine** Variante mit Snapshot,
nicht fünf; nur fünf der letzten zwölf Etappen haben alle fünf Stile erfasst. Die Ansicht
muss „n von 5 Varianten erfasst" hinschreiben.

- [x] **E2a** `TabReels` auf `selectedEtappe` filtern; dünnen Zustand ehrlich beschriften
- [x] **E2b** Pro Variante eine Zeile mit allen Zahlen (Views, Reach, Watch-Time, Retention,
  Likes, Kommentare, Saves, Shares) — Likes/Kommentare als Anzeige, nicht als Sortierung
- [x] **E2c** Instagram und YouTube getrennt; fehlende YT-Metriken als „liefert die API
  nicht" kennzeichnen, nicht als 0
- [x] **E2d** `watch_time_total_sec` als zweite Leitgröße neben Retention
- [x] **E2e** Horizont-Verlauf je Reel (24h → 72h → 7d → 30d → 90d)
- [x] **E2f** Globalen Stil-Schnitt auf eine Einordnungszeile eindampfen
- [ ] **E2g** *(abgeschwächt, offen — braucht Live-Zugriff auf die Graph API, den ich aus
  dem Dashboard-Code heraus nicht habe)* Kurz gegen die Graph API prüfen, ob
  `profile_activity` für REELS überhaupt existiert — **Erwartung: nein.**
  `insights_poller.py` dokumentiert bereits live-verifiziert, dass `profile_visits`/`follows`
  für Reels nicht verfügbar sind („nicht wieder aufnehmen"). Fällt der Check wie erwartet
  aus: Conversion-Frage läuft über `account_insights` (I1) und Story-Insights (I4), kein
  weiterer Aufwand hier
- [ ] **E2h** Später, eigener Aufwand: YouTube Analytics API (`yt-analytics.readonly`) für
  Watch-Time; Facebook `read_insights`

---

## Block F — Mobil brauchbar machen 🟠
Modell: Sonnet · Effort: medium · Thinking: standard
Begründung: unverändert — `TabStilKatalog` hat null Mobile-Behandlung (kein `useMobile()`,
`.sk-row` = 250 px Info + Bilder + 160 px Bewertung + 36 px Gaps + 28 px Außenabstand;
auf 390 px bleibt für die Bilder nichts). L-5 bestätigt: Zeile 3668 setzt weiter `100vh`.

- [x] **F1** `.sk-row` mobil auf Spaltenlayout: Name + Kategorie oben, Bilder als swipebare
  Strecke volle Breite, Bewertungsknöpfe als 4er-Raster darunter
- [x] **F2** Bildhöhe mobil relativ statt fix 200 px; Außenabstand 28 → ~12 px
- [x] **F3** Filter-Chips (Status + Kategorie) mobil zusammenklappen
- [x] **F4** Zeilen 3668, 2682 (`calc(100vh - 260px)`), 3623, 3628 auf `100dvh`.
  Hinweis: Inline-Styles können kein Doppel-`height` als Fallback — `'100dvh'` allein reicht
  (moderne Browser), optional `minHeight: '100vh'` als Netz für alte

---

## Block G — Render- und Logik-Kleinkram 🟡
Modell: Haiku · Effort: — · Thinking: off
Begründung: unabhängige Ein- bis Fünfzeiler, exakte Zeilennummern. G5 mit
Schreibseiten-Regel (Check-up Nr. 9), G6 neu (klein, gleiche Kragenweite).

- [x] **G1** Stil-Katalog: Status-Chip-Zähler aus derselben kategorie-gefilterten
  Menge rechnen wie `visible`. **Umgesetzt:** `counts` filtert jetzt zuerst auf `activeCat`,
  genau wie `visible`
- [x] **G2** `TabKostenGesamt`: leeres `months` → `lastMonth` ist `undefined`, `.monat`
  stürzt ab — früh aussteigen wie im `fehler`-Zweig. **Umgesetzt:** neuer Early-Return
  „Noch keine Kostendaten" bei `months.length === 0`, vor der `lastMonth`-Berechnung
- [x] **G3** `TabReels`: toter Ternary in `maxStil`; `gruppe.sort()` mutiert das gerenderte
  Array. **Befund beim Abarbeiten:** beides existiert nicht mehr im aktuellen Code — der
  globale Stil-Schnitt wurde im Zuge von E2f bereits auf eine reine Einordnungszeile ohne
  `maxStil`-Balken umgebaut, alle verbliebenen `.sort()`-Aufrufe in `TabReels` laufen auf
  frischen `.filter()`-Kopien, nicht auf geteilten Arrays. Kein Codeeingriff nötig
- [x] **G4** Hartes `850` als Laufzeit-Maximum durch das Maximum der geladenen Etappen
  ersetzen. **Umgesetzt:** `maxDur = Math.max(...withDur.map(e => e.dur), 1)` aus der
  ohnehin vorhandenen `withDur`-Liste, Balkenbreite und Warn-Schwelle (`> maxDur * 0.94`)
  nutzen jetzt `maxDur` statt der festen 850/800
- [x] **G5** `reel_varianten` defensiv parsen: heute sind alle 25 Zeilen jsonb-Strings,
  kommt einmal eine echte Liste, liefert `JSON.parse` still `[]`. **Umgesetzt:** neue
  Helper-Funktion `parseReelVarianten()` (behandelt Array-Fall zuerst, sonst `JSON.parse`
  mit try/catch), an allen drei Lesestellen (`Hitl1Panel`, `Hitl1HistorieViewer`,
  Hitl2-Countdown-Komponente) eingesetzt. **Schreibseite unverändert:**
  `Hitl1Panel.freigeben()` schreibt weiter `JSON.stringify(...)` (kanonische Form)
- [x] **G6** `TabReliability` „Retries pro Agent": Balkenbreite auf 100 clampen.
  **Befund beim Abarbeiten:** die bestehende Formel `retries / maxAgentRetries` (Maximum
  aus derselben `agentRows`-Menge) kann rechnerisch nie über 100 laufen — es gibt kein
  `retries / total`(Summen-)Verhältnis in `TabReliability`. Clamp trotzdem als Absicherung
  ergänzt: `Math.min(pct, 100) || 2` statt `pct || 2` bei der Balkenbreite

---

## Block H — Sicherheit: die drei Views 🟡
Depends on: Block A
Modell: Opus · Effort: medium · Thinking: standard
Begründung: gegenüber dem Original **einfacher geworden**: die Suche nach Nutzern ist schon
gelaufen — `v_etappen_uebersicht`, `v_offene_fotos`, `etappen_uebersicht` haben in beiden
Repos **keinen einzigen Aufrufer** (nur alte Audit-Docs erwähnen sie). `v_offene_fotos` gibt
lokale Pfade (`quelldatei`) an `anon` heraus. `etappen_aktuell` macht seit 29.07. vor, wie es
richtig geht.

**Erledigt 02.08.** Migration `20260802140000_security_views_droppen.sql` (Pipeline-Repo,
Commit `2e5b5cf`), live angewandt. Advisor `security` danach: die drei ERROR-Einträge und der
`search_path`-WARN sind weg; es bleiben die zwei `USING(true)`-WARNs (K) und `publish_queue`
ohne Policy — letzteres jetzt nur noch **INFO** statt WARN, weil die toten Grants entzogen sind.

- [x] **H1** Bestätigt: Volltextsuche in beiden Repos findet **keinen einzigen Aufrufer** der
  drei Views (nur alte Audit-Dokumente). Gegenprobe von der Leseseite her: das Dashboard liest
  ausschließlich `etappen`, `etappen_aktuell`, `fotos`, `routen`, `stile`, `pipeline_steps`.
  → alle drei **gedroppt**; die Definitionen stehen als Kommentar in der Migration, falls je
  eine davon zurückkommt (dann mit `security_invoker = on`)
- [x] **H2** Migration im Pipeline-Repo, `get_advisors(security)` gegengeprüft — die drei
  ERROR-Einträge sind weg, `etappen_aktuell` ist die einzige verbliebene View
- [x] **H3** `publish_queue`: `REVOKE ALL` für `anon` und `authenticated`; übrig bleiben nur
  `postgres` und `service_role`. **Vor dem Entzug geprüft:** nicht nur die Edge Function
  schreibt hier — auch `agents/publisher.py` (Insert) und `tools/insights_poller.py` (Select)
  greifen zu. Beide laufen über `adapters/supabase_client.py`, und `.env` trägt einen
  `SUPABASE_SERVICE_KEY` (`sb_secret_…`, also `service_role`) — der Entzug trifft sie nicht
- [x] **H4** `ALTER FUNCTION … SET search_path = ''` auf `update_modified_column`.
  Verifiziert, dass die zwei Trigger (`etappen`, `fotos`) damit weiter feuern — `now()` liegt
  in `pg_catalog` und bleibt auch bei leerem Pfad auflösbar (Test-Update in einer
  zurückgerollten Transaktion, `updated_at` wurde gesetzt).
  Hinweis: die zwei übrigen WARNs („RLS Policy Always True" auf `etappen`/`stile`) sind
  **K-Material** — das sind genau die `USING(true)`-Policies, die K absichern will

---

## Block I — Was die Pipeline schon kann und das Dashboard nicht zeigt 🟡
Depends on: Block A
Modell: Sonnet · Effort: high · Thinking: standard
Begründung: unverändert. Migrationen bestätigt (`account_insights` 30.07.,
`dauer_min`/`hoehenmeter_*` + Blog-Spalten 01.08., View-Refresh nimmt sie mit).

- [x] **I1** Account-Basislinie in den Reels-Tab: Follower/Reach/Views pro Tag aus
  `account_insights` als Kontextzeile. **Umgesetzt:** neue `fetchAccountInsights()`,
  eigener State in `TabReels`, Zeile zeigt den jüngsten Tages-Snapshot; live geprüft
  (Chromium-Rendering, Screenshot) — zeigt echte Werte „26 Follower · 0 Reach · 6 Views"
- [x] **I2** Kennzahlen-Bande (Dauer, Höhenmeter auf/ab) im Etappen-Header bzw.
  `EtappeDetailModal` — NULL heißt „Zelle weglassen" (so steht es im Migrations-Kommentar).
  **Umgesetzt:** `dauer_min`/`hoehenmeter_auf`/`hoehenmeter_ab` in `fetchEtappen()`-Cols und
  `mapEtappe()` ergänzt, neue Zeile im Modal — rendert nur, wenn mindestens ein Wert gesetzt
  ist. **Live geprüft:** DB hat aktuell für keine Etappe Dauer/Höhenmeter (nur `blog_url`
  bei Tag 17) — Feature ist bereit, sobald die Pipeline die Spalten befüllt
- [x] **I3** `blog_url` als Link in der Etappen-Kopfzeile, wenn gesetzt. **Umgesetzt:**
  Link sowohl in der Etappen-Kopfzeile (neben dem Status-Pill) als auch im
  `EtappeDetailModal`, `target="_blank" rel="noopener noreferrer"`. `mapEtappe()` trägt
  `blogUrl` jetzt mit

### Vorgemerkt — Story-Zahlen vom Quell-Account (Friedelfeiner)

Unverändert aus dem Original, Randbedingungen bestätigt: `.env` trägt die drei `FF_*`-Keys,
`adapters/instagram_stories_client.py` ruft `/{ig-user-id}/stories` bereits ab. Story-Insights
leben nur 24 h; bei N Läufen/Tag liegt die letzte Messung zwischen `24h − Intervall` und
`24h` → **4× täglich** ergibt ein 18–24-h-Fenster plus einen zweiten Horizont `früh` (3–9 h).
Lauf gehört auf `pg_cron` + Edge Function, nicht auf den (ausgeschalteten) Mac-LaunchAgent.

- [ ] **I4** *(vorgemerkt)* Gegen die Graph API prüfen, welche Story-Metriken der FF-Token
  hergibt (`views`, `reach`, `replies`, `navigation`, `profile_visits`, `follows`) und ob die
  24-h-Grenze so hart ist wie angenommen. Story-Metriken sind ein **anderes** Set als
  Reel-Metriken — die REELS-Sperrliste aus `insights_poller.py` gilt hier nicht automatisch
- [ ] **I5** *(vorgemerkt)* Wenn ja: Tabelle `story_metrics` mit zwei Horizonten, Messung 4×
  täglich, eigene Ansicht (Stories nicht mit Reels in einen Vergleich)

### Rückkanal serverseitig — betrifft Reels schon heute 🟠

Bestätigt: `com.insta.insights` ist in `launchctl list` **nicht geladen**, der Rückkanal
läuft von Hand — und das `24h`-Fenster (20–48 h) wurde noch **nie** getroffen (0 Snapshots).
Die Infrastruktur (pg_cron + Edge Function, Muster `ig-publish-queue`) steht; Preis ist die
Portierung des Meta-Calls nach Deno/TS.

Zur Frequenz (Flo, 02.08., bleibt gültig): Häufiger messen beantwortet die Anlaufkurve eines
Reels, nicht die Uhrzeit-Frage — die braucht variierte Slot-Belegung, keine engere Taktung.

- [ ] **I6** `insights_poller` serverseitig als `pg_cron`-Job (Edge Function analog
  `ig-publish-queue`), 4×/Tag — deckt alle Fenster inkl. `24h` sicher ab
- [ ] 👤 **I7** Entscheiden, ob `PUBLISH_BELEGUNG` (tools/styles.py) variieren soll — ohne
  das bleibt jeder Uhrzeit-Vergleich mit dem Stil verwechselbar (Pipeline-Entscheidung)

---

## Block J — Repo-Hygiene ⚪
Modell: Haiku · Effort: — · Thinking: off
Begründung: mechanisch, alles entschieden. Bestätigt: `Presentation Work/` = 97 MB,
untracked; `.DS_Store` ist getrackt (steht als `M` im Status); `style-overview.html` +
`upload_style_reviews.py` + `index.html` + `costs_data.json` uncommitted; `query_db.py`
fragt neben `stile`/`fotos` auch die nicht existente Tabelle `styles` ab.

- [x] **J1** `.gitignore` angelegt (`.DS_Store`, `Presentation Work/`), `.DS_Store` per
  `git rm --cached` aus dem Index entfernt
- [x] **J2** `Presentation Work/` bleibt untracked (jetzt zusätzlich gitignored) — nichts zu
  verschieben, solange es nie committet wurde
- [x] **J3** `style-overview.html`, `upload_style_reviews.py`, `index.html`, `costs_data.json`
  gestaged; dazu `icons/` + `manifest.webmanifest` (von `index.html` referenziert, sonst
  bricht die Seite) sowie `docs/` und `done/` (Audit-Dokumente, kein App-Code)
- [x] **J4** `query_db.py`: toter `fetch_table('styles')`-Aufruf entfernt (Tabelle existiert
  nicht, nur `stile`)
- [ ] **J5** React von Development-Builds auf `production.min.js` (47-49) — vorher prüfen, ob
  die `ErrorBoundary` dann noch brauchbare Meldungen liefert (Prod-React kürzt Fehlertexte;
  Babel-Standalone bleibt unverändert)

---

## Block K — Auth fürs Dashboard ⚪ — eigenes Vorhaben
Modell: Opus · Effort: xhigh · Thinking: standard
Begründung: unverändert kein Quick-Fix. Live bestätigt: die `USING(true)`-Policies auf
`etappen` und `stile` stehen jetzt sogar als eigene Advisor-WARNs da; die Spalten-Grants sind
die einzige Schutzschicht. Wer den Quelltext liest, kann `veto`/`freigabe` setzen und
`reel_varianten` (die publizierten Texte) überschreiben; lesbar sind alle `etappen`-Spalten
inkl. `monolog_final` und GPS aus `fotos`.

- [ ] **K1** Plan erstellen (Agent `Plan`): Supabase Auth mit Magic-Link-User, Policies von
  `TO anon` auf `TO authenticated`, Login-Gate, spaltenbeschränkte View statt `SELECT *`
- [ ] 👤 **K2** Entscheiden — für ein privates Pilger-Dashboard kann der Status quo vertretbar
  sein, aber als bewusste Entscheidung

---

## Reihenfolge

```
A  Datenquelle           🔴  ✅ erledigt
B  Navigation/Sortierung 🔴  ✅ erledigt (inkl. B8–B10)
C  Kosten                🔴  ✅ erledigt (C1, C2a im Pipeline-Repo)
D  Live Run              🔴  ✅ erledigt (D1 + D7 im Pipeline-Repo, Edge Function v5)
E  Etappenbezug          🟠  ✅ erledigt (E2g offen — Live-Check gegen die Graph API nötig)
F  Mobil                 🟠  ✅ erledigt
G  Kleinkram             🟡  ✅ erledigt
H  Views                 🟡  ✅ erledigt (gedroppt, Migration im Pipeline-Repo)
I  Neue Daten            🟡  ✅ erledigt
J  Hygiene               ⚪
K  Auth                  ⚪  eigenes Vorhaben
```

**Fünf Tasks fassen ins Pipeline-Repo** (`C1` Einheitspreise → costs_data.json, `C2a`
unit_counts-Spalte, `D1` Varianten-Kennung in pipeline_steps, `D7` publisher-Step inkl.
Edge Function, `H` Views-Drop + Grants + search_path) — eigene Commits dort, der Rest bleibt
im Dashboard-Repo.
