# Dashboard-Audit — Befunde & Abarbeitungsplan

Stand 02.08.2026 · geprüft: `index.html` (3895 Zeilen, uncommitted), `costs_data.json`,
`style-overview.html` gegen `INSTA_Pipeline/` (main.py, tools/pipeline_telemetry.py,
agents/variant_runner.py, supabase/migrations/) und live gegen Supabase `rgwbmqlcxxrynufcmwqx`.

Vorgänger: `done/AUDIT_2026-07-27.md` — T-1 bis T-6 dort sind erledigt und werden hier nicht
wiederholt. Was aus diesem Audit noch offen ist, steht unten mit alter ID in Klammern.

**Modelle in diesem Plan:** Haiku (mechanisch, exakt spezifiziert) · Sonnet (Standard-Implementierung)
· Opus (Urteil statt Ausführung: welche Zahl stimmt, was bricht die Pipeline, wie soll eine Ansicht
überhaupt gebaut sein)

---

## Was ich gemessen habe

| Messung | Ergebnis |
|---|---|
| Die 60 Zeilen, die `fetchEtappen()` lädt | **15 veraltete Run-Dubletten**, nur **45 echte Tage** |
| `etappen` gesamt / `etappen_aktuell` | 91 / **76** Zeilen — View ist für `anon` lesbar (HTTP 200) |
| Wandertag- vs. Rechendatum-Reihenfolge | **alle 60** Zeilen stehen woanders, größter Versatz **30 Plätze** |
| Etappen ohne Telemetrie | **34 von 91** — das Dashboard zeigt sie als „€0.00" |
| `narrator`-Zeilen im letzten Lauf | **26** (10 running / 9 done / 7 skipped), alle unter demselben Namen |
| `assembler` im letzten Lauf | 4× running, **4× error** — letzte Zeile ist `running` |
| `t2i_bild` in `PREISE_USD` | **$0.067** — Dashboard rechnet mit **$0.030** |
| Supabase-Advisor `security` | 3× ERROR (SECURITY DEFINER Views), 3× WARN — **unverändert seit 27.07.** |

---

## Block A — Datenquelle geradeziehen 🔴
Modell: Sonnet · Effort: high · Thinking: standard
Begründung: Der größte aktive Fehler und zugleich ein kleiner Eingriff — vier Read-Pfade tauschen
die Tabelle gegen das View. Riskant ist nur die Unterscheidung, *welcher* Pfad das View will:
Kosten sind pro Run echtes Geld, HITL/Style wollen den aktuellen Stand. Diese Trennung muss der
Agent treffen, deshalb `high` und nicht `low`. Muss vor Block B liegen — die Navigation soll nicht
auf Dubletten aufsetzen.

**Befund D-1:** `fetchEtappen()` (129), `fetchEtappenFuerHitl1()` (2388), `fetchEtappenHistorie()`
(2399) und `fetchEtappenFuerHitl2()` (2703) lesen alle `etappen` mit `order=datum.desc&limit=N`.
Genau dafür wurde `etappen_aktuell` gebaut (Migration `20260729120000`, Kommentar dort:
*„Queries, die 'die letzten N Etappen' über `order by datum desc limit N` holen, ziehen dadurch
veraltete Run-1-Stände und denselben Tag mehrfach — das Limit wird von Dubletten aufgefressen"*).

Konkrete Folgen heute:
- Ein Redo-Tag steht **zweimal** in Etappen-Liste, Pfeil-Navigation und Kosten-Tabelle.
- Der Style-Tab schreibt `stil_bewertung` auf `curE.id` — steht die Auswahl auf der Run-1-Zeile,
  landet die Bewertung auf einer Zeile, die niemand mehr liest.
- `limit=60` liefert nur 45 Tage, `limit=10` in HITL entsprechend weniger.

- [ ] **A1** `fetchEtappen()` auf `etappen_aktuell` umstellen; `run` mitselektieren
- [ ] **A2** `fetchEtappenFuerHitl1()`, `fetchEtappenHistorie()`, `fetchEtappenFuerHitl2()` auf `etappen_aktuell` umstellen (PATCHes gehen weiter auf `etappen` — das View ist nicht updatebar)
- [ ] **A3** Kosten-Tab bewusst auf `etappen` belassen (beide Runs sind bezahlt) und Run-Badge in der Zeile zeigen, wie es `TabReels` bei `e.run > 1` schon macht
- [ ] **A4** Gegenprobe: `Content-Range` auf `etappen_aktuell` gegen die angezeigte Etappenzahl rechnen; ein Redo-Tag darf nur noch einmal in der Liste stehen

---

## Block B — Etappen-Navigation: Sortierung, die man vorhersagen kann 🔴
Depends on: Block A
Modell: Opus · Effort: high · Thinking: standard
Begründung: Hier ist die Frage „welche Reihenfolge ist die richtige" wichtiger als der Code —
der Umbau selbst ist eine Sortierfunktion plus ein Schalter. Der Agent muss entscheiden, was mit
Etappen ohne `run_at` passiert und wie der Schalter mit dem Routen-Dropdown zusammenspielt.

**Der Befund, warum du nie weißt, wo du landest:** `transformData()` (282) baut die Liste als
`[...valid].reverse()` — eine **rein nach Wandertag sortierte Liste über alle Routen hinweg**.
Route wird beim Sortieren nicht berücksichtigt. Die Datumsbereiche überlappen sich aber:

| Route | Wandertage | gerechnet | Zeilen |
|---|---|---|---|
| e98e7b46 | Jun 2024 | Mai 2026 | 22 |
| de798eae | Feb–Mär 2025 | Apr–Mai 2026 | 22 |
| 1ec25174 | Mai 2025 | *nie gelaufen* (`run_at` NULL) | 10 |
| 51e83f21 | **Mai 2025 – Apr 2026** | Apr 2026 | 4 |
| 4252a2f0 (VFRA26) | Mai–Jul 2026 | Mai–Jul 2026 | 33 |

Route `51e83f21` spannt fast ein Jahr und wird von der Datumssortierung quer durch die ganze Liste
verteilt — mitten hinein fallen die zehn `1ec25174`-Tage vom Mai 2025. Beim Durchpfeilen wechselst
du deshalb ohne Vorwarnung die Reise. Dazu kommt: **alle 60 Zeilen mit `run_at` stehen bei
Datums-Sortierung an einer anderen Position als bei Rechendatum-Sortierung, der größte Versatz sind
30 Plätze.** Die Kopfzeile („Tag N · Datum") zeigt außerdem den Wandertag, während das
KPI-„letzter Run" nach `run_at` bestimmt wird — zwei Reihenfolgen in einer Ansicht.

**Entschieden (Flo, 02.08.):** Nach Route gruppieren **und** die Route als echten Filter schaltbar
machen — „nur die Via de la Plata durchklicken" muss gehen. Dazu der Wahlschalter für die
Sortierung, wie bei den anderen Chip-Leisten im Dashboard.

Das heißt konkret drei Dinge, die heute alle fehlen:

1. **Route als Filter, nicht als Sprungmarke.** Das Routen-Dropdown (3778) springt heute nur zu
   `firstIdx` — die Liste bleibt alle Routen lang, und die nächste Pfeiltaste trägt dich wieder
   raus. Ist eine Route gewählt, muss `etappenList` auf diese Route eingedampft werden; dann
   laufen Pfeile, Tabellen und Tab-Inhalte automatisch nur noch innerhalb der Reise.
2. **Sortierung innerhalb der Auswahl per Schalter: Wandertag ↔ Rechendatum.** Wandertag ist der
   Erzählblick (Übersicht/Style/Reels), Rechendatum der Betriebsblick (Kosten/Live-Run).
   Voreinstellung: Wandertag.
3. **Ohne Routenfilter nach Route gruppiert**, nicht quer nach Datum gemischt — sonst bleibt das
   Durcheinander für alle, die den Filter nicht anfassen.

Etappen **ohne `run_at`** (die zehn aus `1ec25174`) im Rechendatum-Modus ans Ende und als
„nie gelaufen" kennzeichnen, statt sie stumm mit €0.00 einzureihen.

- [ ] **B1** Routen-Auswahl von „springt zu Index" auf „filtert die Liste" umbauen; „Alle Routen" bleibt als Option
- [ ] **B2** Sortierung in `transformData()` auf „Route, dann Wandertag" umstellen; ohne Routenfilter Routenwechsel in der Liste sichtbar machen (Trennzeile oder Kürzel-Badge je Zeile)
- [ ] **B3** Schalter „Wandertag / Rechendatum" in die Kopfzeile, Zustand gilt für Liste, Pfeile und Tabellen gemeinsam
- [ ] **B4** Pfeil-Navigation und Tastatur-Handler (3590-3606) gegen die gefilterte Liste laufen lassen — heute rechnen sie gegen `data.etappenList` in voller Länge
- [ ] **B5** Etappen ohne `run_at` gesondert behandeln (ans Ende, Kennzeichnung „nie gelaufen")
- [ ] **B6** Kopfzeile ergänzen: neben „Tag N · Datum" auch das Rechendatum zeigen, damit die beiden Reihenfolgen nicht mehr verwechselbar sind
- [ ] **B7** Mobil: Routenfilter und Sortierschalter dürfen die Kopfzeile nicht sprengen — als Chip-Leiste unter den Titel, nicht daneben

---

## Block C — Kosten: Label und Wert wieder deckungsgleich 🔴
Depends on: Block A
Modell: Sonnet · Effort: high · Thinking: standard
Begründung: Die Grundsatzfrage ist entschieden (siehe unten), es bleibt saubere Implementierung mit
einem Abgleich gegen `PREISE_USD`. Der Umbau der Einheitspreis-Quelle (C1) reicht über zwei Repos —
deshalb `high`, aber kein Opus mehr nötig.

**Entschieden (Flo, 02.08.):** Die Etappen-Kosten **bleiben ein Schätzwert** — hochgerechnet aus
Einheitspreisen mal Stückzahl, was bei bekannten Preisen ziemlich genau ist. Der Ist-Kosten-Tab
bleibt die exakte Wahrheit aus den Anbieter-Belegen. Zwei Zahlen, zwei Zwecke, das ist in Ordnung —
sie müssen nur als das beschriftet sein, was sie sind, und die Einheitspreise dürfen nicht wieder
auseinanderlaufen.

Genau das ist hier passiert: `PREISE_USD` wurde in der Pipeline gepflegt, die Kopie im Dashboard
nicht. Deshalb C1 — **eine Quelle statt zweier Listen**: `tools/costs_report.py --json` schreibt
die Einheitspreise als eigenen Block mit nach `costs_data.json`, das Dashboard liest sie von dort.
Dann zieht das nächste Preis-Update das Dashboard automatisch mit.

**Zu deiner Frage nach den €0.00 — nein, das ist noch offen (C6).** Repariert wurde bisher nur der
Ist-Kosten-Tab: der zählt Etappen ohne Telemetrie korrekt als „nicht zugerechnet" und schreibt es
sogar hin. Der Kosten-Tab unter *Etappen* macht in Zeile 296 aus `null` ein `0` und zeigt „€0.00" —
für **34 von 91 Etappen**. `pipeline_telemetry.py:283` schreibt bewusst NULL statt 0.00 und
begründet das dort: *„NULL heisst unbekannt, 0.00 luegt."* Das Dashboard dreht diese Entscheidung
wieder zurück.

**Befund D-2 — `platformCosts()` (88-97) rechnet mit falschen Preisen:**

| im Dashboard | in `tools/pipeline_telemetry.py` |
|---|---|
| `WAVESPEED_EUR_PER_T2I = 0.030 × 0.88` | `t2i_bild = 0.067` (WaveSpeed Nano Banana 2) → Balken **~2,2× zu niedrig** |
| `cost_video_eur` = 100 % Atlas | `wan27_clip = 1.50` (Roboter-Hero) läuft über **WaveSpeed**, nicht Atlas |
| Kurs `0.88` | Ist-Kosten-Tab rechnet mit `0.8765` aus `costs_data.json` |
| Kommentar „Seedream" | Seedream ist nur noch Rückfall, aktiv ist Nano Banana 2 |

Dazu unverändert aus 27.07: `Math.max(0, …)` in Zeile 95 kappt negative Atlas-Werte → die vier
Balken summieren sich dann nicht mehr auf den Gesamtbetrag (Z-1).

**Befund D-3 — zwei Balken tragen einen Anbieternamen, der nicht drinsteckt:**
- „Anthropic" = `cost_llm_eur` = Claude **+ Gemini**. Der Analyst läuft per Default auf Gemini Flash.
- „FAL.ai" = `cost_tts_eur` = fal-ElevenLabs **+ MiniMax + Suno**. `pipeline_telemetry.py:256`
  sagt das selbst: *„Kein eigenes cost_musik_eur-Feld … Suno-Song schlägt darum auf cost_tts_eur
  drauf, obwohl es kein ElevenLabs-TTS ist."*

- [ ] **C1** Einheitspreise als eine Quelle: `tools/costs_report.py --json` schreibt `PREISE_USD` (plus Anbieter-Zuordnung je Posten) nach `costs_data.json`; `platformCosts()` liest sie von dort statt aus hartkodierten Konstanten
- [ ] **C2** Preise nachziehen und Zuordnung korrigieren: `t2i_bild` $0.067 statt $0.030, `wan27_clip` zu WaveSpeed statt Atlas, Kurs aus `meta.kurs_usd_eur` statt hartem `0.88`
- [ ] **C3** Die Schätzung als Schätzung beschriften — im Kosten-Tab eine Zeile „hochgerechnet aus Einheitspreisen · Belege im Ist-Kosten-Tab", damit die beiden Zahlen nicht als Widerspruch gelesen werden
- [ ] **C4** `Math.max(0, …)` entfernen oder den Rest als „sonstiges" ausweisen, damit die Balken auf den Gesamtbetrag aufgehen
- [ ] **C5** Balken „Anthropic" → „LLM (Claude + Gemini)", „FAL.ai" → „TTS + Musik"
- [ ] **C6** (Z-3) Kosten-Trend-Achse Zeile 858: hartes `T1 T7 T14 T21 T28` durch echte Tag-Nummern ersetzen — die Reihe ist zudem routenübergreifend gemischt (entfällt teilweise mit Block B)
- [ ] **C7** `cost_total_eur = null` **nicht** mehr als €0.00 rendern: „–" plus Hinweis „ohne Telemetrie" in Tabelle, KPIs und Summen; Ø-Werte nur über Etappen mit Telemetrie bilden
- [ ] **C8** (Z-4) `successRate` (395) an `statusMap` koppeln und das `resolved`-Flag aus `errors[]` auswerten — heute gilt ein Run mit `pipeline_status='fehler'` ohne Errors-Eintrag als Erfolg

---

## Block D — Live Run: die Anzeige passt nicht mehr zur Pipeline 🔴
Modell: Opus · Effort: xhigh · Thinking: standard
Begründung: Du hast recht, das stimmt hinten und vorne nicht — und es ist kein Label-Fix, sondern
ein Neubau der Ansicht. Die Pipeline ist seit dem Bild-Zweig-Umbau und den parallelen Varianten
mehrfädig, das Dashboard rechnet noch mit einer Kette. Der Agent muss die Schrittstruktur neu
entwerfen; ohne Verständnis von `_stage_varianten` und dem Bild-Thread wird das nichts.

**Was die Pipeline heute wirklich tut** (main.py 811-838, variant_runner):

```
analyst → map → narrator(Grundgerüst) → selektor
   ├─ Bild-Thread PARALLEL:  imagegen → hero → animator
   └─ Haupt-Thread: HITL #1 → pro Stil: narrator → audio → assembler
                              (Audio in mehreren Threads gleichzeitig, gestaffelt)
→ telemetrie → finalize → carousel_publisher → blog_publisher
```

**Was daraus im letzten echten Lauf in `pipeline_steps` landete:**

| Step | Zeilen | Problem |
|---|---|---|
| `analyst` | 26 running + 1 done | funktioniert — Foto-Fortschritt über `detail` |
| `narrator` | **10 running, 9 done, 7 skipped** über 32 Min | eine Zeile pro Stil, **ohne Stil-Kennung** |
| `assembler` | 4× running, **4× error** | letzte Zeile ist `running` |
| `carousel_publisher`, `blog_publisher` | je 1 | dem Dashboard **unbekannt** |
| `publisher` | — | wird **nie** geschrieben, steht aber im Dashboard |

`TabProgress` (1463-1470) gruppiert nach Step-Namen und nimmt **die letzte Zeile pro Name**. Daraus
folgt direkt:

1. **Fehler verschwinden.** Im obigen Lauf sind alle vier Varianten am Assembler gescheitert
   („Keine Fotos mit animation_datei gefunden") — weil die letzte Zeile zufällig `running` war,
   zeigt das Dashboard „Assembler · läuft…". Ein komplett gescheiterter Lauf sieht aus wie ein
   laufender.
2. **Der Narrator-Status ist Zufall.** Bei 26 Zeilen von 5 Stilen sagt die letzte nichts über die
   anderen vier.
3. **Die Reihenfolge stimmt nicht.** Die Liste folgt dem *ersten* Auftreten eines Namens; weil der
   Bild-Zweig parallel läuft, steht `map skipped` hinter `narrator running`.
4. **Der Prozentwert ist bedeutungslos.** `doneCount / total` zählt Step-*Namen*, und der Nenner
   wächst während des Laufs — der Fortschritt kann fallen.
5. **Publish fehlt ganz**, `carousel_publisher`/`blog_publisher` erscheinen als roher Key.

Der saubere Weg führt über die Pipeline: `log_pipeline_step` braucht eine **Variante/Stil-Kennung**
(zusätzliche Spalte oder im `detail`), sonst kann das Dashboard parallele Stile prinzipiell nicht
auseinanderhalten. Das ist ein kleiner Eingriff im Pipeline-Repo mit großer Wirkung hier.

- [ ] **D1** Pipeline: `log_pipeline_step()` um `variante` erweitern (Migration `pipeline_steps.variante` + alle Aufrufer in `variant_runner.py`), damit parallele Stile unterscheidbar werden
- [ ] **D2** Dashboard: feste Soll-Reihenfolge der Schritte definieren statt „Reihenfolge des ersten Auftretens"; noch nicht begonnene Schritte grau vorzeigen
- [ ] **D3** Statusregel umdrehen: ein `error` in einem Step gewinnt gegen ein späteres `running` desselben Namens — Fehler dürfen nicht mehr überschrieben werden
- [ ] **D4** Schritte mit mehreren Varianten als Gruppe zeigen („audio · 3/5 fertig, 1 Fehler") statt als eine Zeile
- [ ] **D5** Fortschritt aus der Soll-Liste rechnen, nicht aus der Zahl gesehener Namen
- [ ] **D6** `STEP_LABELS`/`STEP_DESCRIPTIONS`/`PROGRESS_UNIT` auf die zehn echten Namen bringen: `analyst, map, narrator, selektor, imagegen, animator, audio, assembler, carousel_publisher, blog_publisher` — `carousel` und `publisher` streichen
- [ ] **D7** Entscheiden, ob der Publish-Schritt einen eigenen `pipeline_step` bekommt (heute schreibt `publisher.py` keinen) — sonst endet die Live-Ansicht vor dem interessantesten Moment
- [ ] **D8** Hänger erkennen: bleibt ein Step > 30 Min auf `running`, als „abgebrochen?" markieren statt weiter „läuft…" zu zeigen

---

## Block E — Tabs, die die gewählte Etappe ignorieren 🟠
Depends on: Block A
Modell: Sonnet · Effort: high · Thinking: standard
Begründung: Zwei Tabs, die im Etappen-Modus stehen, aber global rechnen. Der Agent muss pro Tab
entscheiden: auf die Etappe filtern oder ehrlich als Gesamtansicht beschriften. Beides ist
vertretbar — was nicht geht, ist der jetzige Zwischenzustand.

**Reels-Tab (2908):** `function TabReels()` nimmt **gar keine Props**. Die App übergibt
`data` und `selectedEtappe`, beides wird ignoriert — deshalb ändert sich beim Durchpfeilen nichts.
Der Tab lädt alle `reel_metrics` und zeigt zwei globale Sichten. Der Umbau ist unten in **Block E2**
im Detail aufgeschrieben — dort steht auch, welche Zahlen überhaupt da sind.

**Reliability-Tab (1060) — was er soll und warum er nicht trägt:** Er beantwortet „läuft die
Pipeline zuverlässig?" aus zwei Quellen: `retries` (wie oft ein Agent es nochmal versuchen musste)
und `errors` (was gescheitert ist). Das Problem ist die Mischung der Bezugsgrößen:

- „Retries (gewählter Run)" ist die einzige Zahl, die zur gewählten Etappe gehört — und sie steht
  schon als KPI auf der Übersicht.
- „Retries Reise Σ" und „Erfolgsrate" rechnen über **alle** geladenen Etappen.
- „Retries pro Agent" nimmt `list.slice(-12)` — das sind die letzten 12 **nach Wandertag**, nicht
  nach Rechendatum, obwohl die Beschriftung „letzte 12 Runs" sagt (hängt an Block B).
- Die Ereignisliste zeigt Fehler **aller** Etappen, jede Retry-Karte behauptet pauschal
  „alle resolved" — das `resolved`-Flag aus der Telemetrie wird nie gelesen.

**Entschieden (Flo, 02.08.):** Reliability **bleibt ein Etappen-Tab** und zeigt nur noch, was zur
gewählten Etappe gehört. Kein eigener Modus — der mobile Umschalter hat vier Einträge und passt
genau in eine Zeile; ein fünfter würde sie sprengen, und das Layout ist dort gerade gut.

Die Reise-Aggregate müssen deshalb nicht verschoben, sondern nur **nicht doppelt** gezeigt werden:
Erfolgsrate, Retries Σ, Retry-Verlauf über die letzten Runs und die imagegen-Frühwarnung stehen
bereits im Reliability-Panel der **Übersicht** — das ist die Gesamtansicht, dort gehören sie hin.
Der Tab behält dann: Retries dieser Etappe nach Agent, Fehler dieser Etappe im Klartext, und die
Pipeline-Schritte dieses Runs (die das `EtappeDetailModal` schon lädt). Damit beantwortet er eine
einzige Frage — „was ist bei *diesem* Run schiefgegangen" — statt zwei halbe.

- [ ] **E1** `TabReliability` auf die gewählte Etappe eindampfen: Retries nach Agent, Fehlerliste, Pipeline-Schritte dieses Runs — Reise-Aggregate raus (stehen in der Übersicht)
- [ ] **E2** Reels-Tab umbauen — Details im Abschnitt unten
- [ ] **E3** Prüfen, dass das Reliability-Panel der Übersicht die entfallenen Reise-Zahlen wirklich vollständig abdeckt, sonst dort ergänzen
- [ ] **E4** `resolved`-Flag aus `errors[]` auswerten statt pauschal „alle resolved" zu behaupten
- [ ] **E5** „letzte 12 Runs" in der Übersicht tatsächlich nach Rechendatum bilden (nutzt Block B)

### E2 im Detail — welche Zahlen es gibt und was man daraus machen kann

**Was ankommt, gemessen am 02.08.:**

| Plattform | Snapshots | Metriken | Quelle |
|---|---|---|---|
| **Instagram** | 79 · 31 Etappen · 5 Stile | views, reach, likes, comments, saves, shares, total_interactions, watch_time_avg, watch_time_total — **alle gefüllt** | `{media_id}/insights` |
| **YouTube** | 10 · **2 Etappen** | nur views, likes, comments. Reach, Saves, Shares, **Watch-Time = NULL** | `videos.list(part=statistics)` |
| **Facebook** | — | gar nichts: der Token trägt kein `read_insights` (Docstring `insights_poller.py:33`) |
| **Account** | 1 Snapshot | `follower_count` meist NULL — Meta liefert erst ab 100 Followern, der Account hat 24 |

Abgeleitet: `dauer_s` (ffprobe auf die Reel-Datei), `retention_pct` (generierte Spalte,
`watch_time_avg / dauer_s`), `slot` (aus `publish_queue`).

**Die Größenordnungen sind der wichtigste Befund** (Ø je Instagram-Snapshot):

```
Views 101–109 · Reach 94–104 · Watch-Time 3,8–8,0 s · Retention 4,8–7,7 %
Likes 0,9–1,8 · Kommentare 0,0–0,8 · Saves 0,0–0,1 · Shares 0,0–0,2
```

Daraus folgt dreierlei:
1. **Likes und Kommentare zeigen, aber nicht ranken.** Bei Ø 1 Like entscheidet ein einziges Like
   über Platz 1 oder Platz 5. Als Zahl in der Zeile: ja. Als Sortierkriterium: nein, das wäre eine
   Rangliste des Zufalls.
2. **Views ≈ Reach** (101 vs. 94) — es gibt praktisch keine Wiederholungs-Views. „Views" misst hier
   fast nur, wie weit Instagram ausgespielt hat, nicht wie gut das Reel war.
3. **Retention ist die einzige pro Zuschauer normierte Zahl** und damit die einzige, die über Stile
   *und* über Reel-Längen hinweg vergleichbar ist. Bleibt Leitgröße.

**Zu deiner Watch-Time-Frage: plattformübergreifend geht heute nicht — und wäre auch nicht gut.**
YouTube liefert über `videos.list` grundsätzlich keine Watch-Time; dafür bräuchte es die
**YouTube Analytics API** (`estimatedMinutesWatched`, `averageViewDuration`,
`averageViewPercentage`) mit eigenem OAuth-Scope `yt-analytics.readonly` — Pipeline-Ausbau, kein
Dashboard-Task. Selbst wenn: ein gemeinsamer Mittelwert aus Instagram (~100 Views) und YouTube
(Ø **6** Views) wäre vollständig von Instagram dominiert und würde YouTube unsichtbar machen.
**Plattformen getrennt ausweisen**, nebeneinander statt verrechnet.

**Wo wirklich mehr drinsteckt.** Im `raw`-JSON liegt nichts Ungenutztes — es enthält genau die
neun Felder, die schon Spalten sind. Mehr rausholen heißt also besser rechnen:

- **`watch_time_total_sec` wird nirgends angezeigt.** Das ist gebundene Lebenszeit gesamt und fasst
  Reichweite und Aufmerksamkeit in einer Zahl zusammen — bei kleinen Stichproben deutlich stabiler
  als Likes. Starker Kandidat für die zweite Leitgröße neben Retention.
- **Der Verlauf über die Horizonte fehlt.** Der Tab zeigt nur den jüngsten Snapshot; die Reihe
  24h → 72h → 7d → 30d → 90d liegt vollständig vor. Sie beantwortet die interessanteste Frage bei
  Explore-Zuteilung: läuft ein Reel nach oder ist es nach zwei Tagen tot?
- **Engagement-Rate** als `total_interactions / reach` statt roher Likes — normiert, auch wenn die
  Basis dünn bleibt.
- **Profil-Aktivität** (`profile_activity`: Profilaufrufe und Follows aus dem Post heraus) ist die
  eigentliche Conversion-Frage und steht noch nicht in `IG_METRIKEN` — gegen die API prüfen.

**Zur Frage „im Etappen-Tab lassen oder nach oben": beides, aber nach Frage getrennt.**
Der Vergleich der Varianten *einer* Etappe ist der A/B-Test und gehört in den Etappen-Modus. Der
Stil-Vergleich über alle Etappen beantwortet etwas anderes („welcher Stil trägt?") und hat im
Etappen-Modus nichts verloren. Solange die Stichprobe aber so dünn ist, dass n=5 pro Stil kaum
erreicht wird, lohnt der Menü-Umbau nicht — **jetzt etappenbezogen bauen**, den globalen Teil auf
eine kompakte Einordnungszeile eindampfen, den eigenen Reiter vertagen, bis mehr Daten da sind.

⚠️ **Erwartungsdämpfer:** Deine Beispiel-Etappe Acquapendente → Bolsena (Tag 15) hat **genau eine**
Variante mit Snapshot, nicht fünf. Von den letzten zwölf Etappen haben nur fünf wirklich alle
fünf Stile erfasst. Die Ansicht muss das hinschreiben („1 von 5 Varianten erfasst"), sonst sieht
sie aus wie ein A/B-Vergleich, der keiner ist.

- [ ] **E2a** `TabReels` auf `selectedEtappe` filtern; leerer/dünner Zustand ehrlich beschriften („n von 5 Varianten erfasst")
- [ ] **E2b** Pro Variante eine Zeile mit allen Zahlen statt nur einem Balken: Views, Reach, Watch-Time, Retention, Likes, Kommentare, Saves, Shares — Likes/Kommentare als Anzeige, nicht als Sortierung
- [ ] **E2c** Instagram und YouTube getrennt ausweisen, nicht in einen Mittelwert werfen; bei YouTube die fehlenden Metriken als „liefert die API nicht" kennzeichnen statt als 0
- [ ] **E2d** `watch_time_total_sec` als zweite Leitgröße neben Retention aufnehmen
- [ ] **E2e** Horizont-Verlauf je Reel zeigen (24h → 72h → 7d → 30d → 90d) — beantwortet, ob ein Reel nachläuft
- [ ] **E2f** Globalen Stil-Schnitt auf eine Einordnungszeile eindampfen („dieser Stil liegt über/unter seinem Schnitt aus n Reels")
- [ ] **E2g** Pipeline prüfen: `profile_activity` in `IG_METRIKEN` aufnehmbar? Wenn ja, Migration + Poller + Anzeige — das ist die Conversion-Frage
- [ ] **E2h** Später, eigener Aufwand: YouTube Analytics API für Watch-Time (`yt-analytics.readonly`), Facebook `read_insights` freischalten

---

## Block F — Mobil brauchbar machen 🟠
Modell: Sonnet · Effort: medium · Thinking: standard
Begründung: Ein Layout-Umbau ohne Datenlogik — überschaubar, aber `TabStilKatalog` hat heute
**null** Mobile-Behandlung, das wird kein Einzeiler. Betrifft nur diese Ansicht.

**Stil-Katalog auf dem Handy:** `TabStilKatalog` ruft `useMobile()` gar nicht auf. Die `.sk-row`
ist eine feste Flex-Zeile aus **250 px Infospalte + Bilderstrecke + 160 px Bewertungsspalte**, dazu
36 px Gaps und 28 px Außenabstand links/rechts. Auf einem 390-px-Display bleiben für die Bilder
rechnerisch nichts übrig — und genau die sind der Zweck der Ansicht. Die Bilder sind zudem auf
`height: 200px` fixiert.

**Zusätzlich (L-5, entgegen `done/ABARBEITEN.md` noch offen):** am 27.07. wurde die
Monolog-Sidebar gefixt, gemeint war aber der App-Root. **Zeile 3668** setzt weiterhin
`height: '100vh'` und überschreibt das `100dvh` aus Zeile 14 — auf iOS sitzt der untere Rand hinter
der Adressleiste.

- [ ] **F1** `.sk-row` auf dem Handy auf Spaltenlayout umstellen: Name + Kategorie oben, Bilder als swipebare Strecke über die volle Breite, Bewertungsknöpfe darunter als 4er-Raster
- [ ] **F2** Bildhöhe mobil relativ statt fix 200 px; Außenabstand von 28 px auf ~12 px
- [ ] **F3** Filter-Chips (Status + Kategorie) mobil zusammenklappen — heute belegen sie drei Zeilen über der Liste
- [ ] **F4** Zeile 3668 auf `100dvh`; ebenso 2682 (`calc(100vh - 260px)`), 3623, 3628

---

## Block G — Render- und Logik-Kleinkram 🟡
Modell: Haiku · Effort: — · Thinking: off
Begründung: Vier unabhängige Ein- bis Fünfzeiler mit exakten Zeilennummern im Auftrag. Nichts
davon ändert Semantik, ein Commit reicht.

- [ ] **G1** Stil-Katalog: Status-Chip-Zähler (1929-1933) berücksichtigen den Kategorie-Filter nicht — `counts` aus derselben gefilterten Menge rechnen wie `visible`
- [ ] **G2** `TabKostenGesamt`: bei leerem `months` läuft `lastMonth.monat` in einen Absturz (3192-3193) — früh aussteigen wie im `fehler`-Zweig
- [ ] **G3** `TabReels`: toter Ternary in `maxStil` (2955); `gruppe.sort()` (3060) mutiert das gerenderte Array — auf Kopie sortieren
- [ ] **G4** Zeile 1047: hartes `850` als Laufzeit-Maximum durch das Maximum der geladenen Etappen ersetzen
- [ ] **G5** `reel_varianten` defensiv parsen (2422, 2562, 2724): heute liegen alle 25 Zeilen als jsonb-*String*, `golden_assemble.py:91` dokumentiert aber beide Formen. Kommt einmal eine echte Liste, liefert `JSON.parse` still `[]` und HITL #1/#2 zeigen „keine Texte"

---

## Block H — Sicherheit: die drei Views 🟡
Depends on: Block A
Modell: Opus · Effort: high · Thinking: standard
Begründung: Kann Pipeline-Leser brechen. Der Agent muss `INSTA_Pipeline/` nach Nutzern durchsuchen
und beurteilen, ob der Zugriff über den Service-Key läuft (dann unkritisch) oder über `anon`
(dann bricht es). Das SQL selbst ist ein Einzeiler pro View — das Urteil ist die Arbeit.

Advisor-Stand von heute, unverändert gegenüber 27.07.: `v_etappen_uebersicht`, `v_offene_fotos`
und `etappen_uebersicht` sind `SECURITY DEFINER` (Level **ERROR**). `v_offene_fotos` gibt u. a.
`quelldatei` — lokale Pfade — an `anon` heraus. `etappen_aktuell` macht es seit dem 29.07. richtig
vor: `alter view … set (security_invoker = on)`.

- [ ] **H1** Nutzer der drei Views in `INSTA_Pipeline/` suchen und einordnen (Service-Key vs. anon)
- [ ] **H2** `security_invoker = on` als Migration im Pipeline-Repo, danach `get_advisors(type: security)` — die drei ERROR-Einträge müssen weg sein
- [ ] **H3** `publish_queue`: RLS an, keine Policy → die `anon`-Grants (`SELECT, INSERT, UPDATE, DELETE, TRUNCATE`) sind totes Recht, entziehen
- [ ] **H4** `search_path` auf `update_modified_column` setzen (Advisor-WARN)

---

## Block I — Was die Pipeline schon kann und das Dashboard nicht zeigt 🟡
Depends on: Block A
Modell: Sonnet · Effort: high · Thinking: standard
Begründung: Neue Anzeigeflächen statt Reparatur — der Agent muss entscheiden, wo die Zahlen
hingehören, nicht nur wie sie geholt werden. Betrifft nur neue Panels, bestehende Tabs bleiben
unangetastet.

Drei Migrationen aus der letzten Woche haben im Dashboard noch keinen Verbraucher:

- `account_insights` (30.07., anon-lesbar, aktuell 1 Snapshot) — als Basislinie für den Reels-Tab
  gebaut: *„ohne den ist jeder Wochen-Vergleich der Reels mit dem Wachstum des Accounts selbst
  verwechselbar"*. Genau diese Einordnung fehlt dem Reels-Tab heute.
- `etappen.dauer_min`, `hoehenmeter_auf`, `hoehenmeter_ab` (01.08.)
- `etappen.blog_url`, `blog_bild_url` (01.08.)

- [ ] **I1** Account-Basislinie in den Reels-Tab: Follower/Reach/Views pro Tag aus `account_insights` als Kontextzeile über dem Stil-Vergleich
- [ ] **I2** Kennzahlen-Bande (Dauer, Höhenmeter auf/ab) im Etappen-Header bzw. `EtappeDetailModal` — NULL heißt „Zelle weglassen", nicht „—" (so steht es im Migrations-Kommentar)
- [ ] **I3** `blog_url` als Link in der Etappen-Kopfzeile, wenn gesetzt

### Vorgemerkt, jetzt noch nicht bauen — Story-Zahlen vom Quell-Account

Entschieden (Flo, 02.08.): Facebook bleibt außen vor. Der zweite Instagram-Account
(**Friedelfeiner**) ist dagegen interessant, weil dort fast nur Stories laufen — und Stories sind
im Rückkanal bisher ein blinder Fleck.

**Die Zugangsdaten und der halbe Adapter existieren schon:** `.env` trägt `FF_META_ACCESS_TOKEN`,
`FF_INSTAGRAM_USER_ID`, `FF_FACEBOOK_PAGE_ID`, und `adapters/instagram_stories_client.py`
ruft mit ihnen bereits `/{ig-user-id}/stories` ab (der Watcher zieht darüber die Story-Bilder in
die Pipeline). Story-Insights wären eine Erweiterung dieses Adapters, keine neue Anbindung.

**Die harte Randbedingung:** Story-Insights gibt es nur, solange die Story lebt — nach 24 Stunden
ist sie weg und die Zahlen sind nicht mehr abrufbar. Kein Backfill, keine zweite Chance.

**Wie oft messen? Einmal täglich reicht nicht.** Bei *einem* festen Lauf am Tag hängt das
Messalter davon ab, wann die Story gepostet wurde — und eine Story, die kurz vor dem Lauf
rausgeht, ist beim nächsten Lauf schon abgelaufen:

| Story gepostet | Messung beim 07:00-Lauf | Ergebnis |
|---|---|---|
| 06:55 | 5 Minuten alt · am Folgetag bereits abgelaufen | praktisch verloren |
| 07:05 | am Folgetag 23 h 55 min alt | brauchbar |
| 19:00 | am Folgetag 12 h alt | brauchbar, aber halbes Alter |

Die Regel dahinter: **bei N Läufen pro Tag liegt die letzte erfolgreiche Messung einer Story
zwischen `24 h − Intervall` und `24 h`.** Die Streuung ist also genau das Polling-Intervall:

| Läufe/Tag | Intervall | Messalter-Spanne |
|---|---|---|
| 1 | 24 h | 0–24 h — unbrauchbar, plus Verlustrisiko |
| 2 | 12 h | 12–24 h |
| 4 | 6 h | **18–24 h** |
| 6 | 4 h | 20–24 h |

**Empfehlung: 4× täglich.** Damit liegt jede Story am Ende in einem 18–24-h-Fenster und ist mit
jeder anderen vergleichbar — dieselbe Logik, die `reel_metrics` über die Horizonte schon fährt.
Sechs Läufe verengen das Fenster nur noch um zwei Stunden und lohnen den Aufwand nicht.

Der eigentliche Gewinn der vier Läufe ist aber ein zweiter: sie erlauben **zwei Horizonte pro
Story** statt einem — `früh` (3–9 h) und `final` (18–24 h). Die Differenz zeigt, ob eine Story
nachläuft oder sofort tot ist. Genau die Frage, die dem Reels-Tab heute fehlt (E2e).

Zwei Dinge, die vorher geklärt gehören: Story-Views laufen erfahrungsgemäß stark vorn zusammen —
falls die ersten Wochen zeigen, dass zwischen 12 h und 23 h kaum noch etwas passiert, reichen auch
zwei Läufe. Und der Lauf gehört **nicht** an den Mac-LaunchAgent (der ist aus und braucht ein
waches Gerät), sondern auf `pg_cron` + Edge Function — beides ist für die Publish-Queue bereits
eingerichtet. Das bedeutet allerdings, den einen Graph-API-Call aus dem Python-Adapter nach
Deno/TS zu portieren; das ist die Abwägung.

- [ ] **I4** *(vorgemerkt)* Gegen die Graph API prüfen, welche Story-Metriken der FF-Token wirklich hergibt (`views`, `reach`, `replies`, `navigation`, `profile_visits`, `follows` sind die Kandidaten — ob „Herzen"/Story-Likes dabei sind, muss die API beantworten, nicht ich) **und** ob die 24-h-Grenze für Insights wirklich so hart ist wie angenommen
- [ ] **I5** *(vorgemerkt)* Wenn ja: Tabelle `story_metrics` mit zwei Horizonten (`früh`, `final`), Messung 4× täglich; danach eigene Ansicht — Stories sind ein anderes Format als Reels und gehören nicht in denselben Vergleich

### Rückkanal serverseitig — betrifft Reels schon heute 🟠

Der Insights-Poller ist ein LaunchAgent (`docs/deploy/com.insta.insights.plist`, täglich 09:30),
der `python3 -m tools.insights_poller` lokal aufruft. **Der Agent ist nicht geladen** —
`launchctl list` kennt keinen `com.insta.*`-Job. Der Rückkanal läuft also faktisch von Hand.

**Das kostet bereits Daten.** Die Snapshot-Fenster in `insights_poller.py` sind vergänglich: das
`24h`-Fenster fasst nur Reels im Alter 20–48 h, danach ist der Stand für immer weg. In
`reel_metrics` stehen 79 Instagram-Snapshots — verteilt auf `72h`, `7d`, `30d`, `90d` und `final`,
aber **null mit Horizont `24h`**. Das engste Fenster wurde noch nie getroffen.

Die Infrastruktur dafür steht: `ig-publish-queue` läuft seit Ende Juni über `pg_cron` + Edge
Function, alle 5 Minuten, unabhängig vom Mac. Ein zweiter Cron-Job für den Rückkanal ist dasselbe
Muster. Preis: der Poller ist Python, eine Edge Function ist Deno/TS — der Meta-Call müsste
portiert werden (der FF-Token käme als Supabase-Secret dazu, wie `META_ACCESS_TOKEN` es schon ist).

**Zur Frequenz — was sie beantwortet und was nicht** (Flo, 02.08.): Häufigeres Messen liefert die
*Anlaufkurve eines einzelnen Reels* („wie schnell kamen die Views rein"). Es beantwortet **nicht**
die Frage „läuft zwischen 14 und 15 Uhr mehr als zwischen 7 und 8". Dafür braucht es keinen
engeren Takt, sondern den Vergleich von Reels, die zu verschiedenen Uhrzeiten gepostet wurden, auf
**gleichem Messalter** — und genau das liegt mit `posted_at`, `slot` und den Horizonten schon vor.
Der Engpass ist nicht die Messfrequenz, sondern dass `PUBLISH_BELEGUNG` Stil und Uhrzeit fest
koppelt (siehe Hinweistext im Reels-Tab): solange `original_images` immer auf Slot 5 liegt, ist
jede Uhrzeit-Aussage zugleich eine Stil-Aussage. Wer Uhrzeiten sauber vergleichen will, muss die
Slot-Belegung variieren — das ist eine Pipeline-Entscheidung, keine Dashboard-Frage.

- [ ] **I6** `tools/insights_poller.py` als `pg_cron`-Job serverseitig fahren (Edge Function analog `ig-publish-queue`), damit die Snapshot-Fenster nicht länger von Hand getroffen werden müssen — 4×/Tag deckt alle Fenster inkl. `24h` sicher ab
- [ ] **I7** Entscheiden, ob die Slot-Belegung (`PUBLISH_BELEGUNG` in `tools/styles.py`) variieren soll — ohne das bleibt jeder Uhrzeit-Vergleich mit dem Stil verwechselbar

---

## Block J — Repo-Hygiene ⚪
Modell: Haiku · Effort: — · Thinking: off
Begründung: Mechanisch, alles entschieden.

**`Presentation Work/` — geklärt (02.08.):** Das ist das Präsentations-Deck vom Mai
(`Insta Pipeline.html`, `deck-stage.js`, `tweaks-panel.jsx`, 43 Agent-Portraits + 6 MP4, zusammen
97 MB). Mit dem Dashboard hat es nichts zu tun, es liegt hier nur herum. Es ist **untracked**, also
noch nicht im Git-Verlauf — solange das so bleibt, ist nichts passiert. Kommt es einmal rein,
bleibt es dauerhaft im Pages-Repo, weil Git Blobs nicht mehr entfernt. Also: rausschieben und per
`.gitignore` absichern.

- [ ] **J1** `.gitignore` anlegen (`.DS_Store`, `Presentation Work/`), `.DS_Store` aus dem Index nehmen (`git rm --cached`)
- [ ] **J2** `Presentation Work/` aus dem Dashboard-Repo herausnehmen — nach `30_PROJEKTE/` oder in die Dropbox, wo die anderen Deck-Sachen liegen
- [ ] **J3** `style-overview.html` + `upload_style_reviews.py` committen — der `fetchAll`-Fix liegt seit 27.07. nur uncommitted dort; `index.html` und `costs_data.json` sind seit heute ebenfalls uncommitted
- [ ] **J4** `query_db.py` fragt eine Tabelle `styles` ab, die es nicht gibt — löschen oder auf `stile` korrigieren
- [ ] **J5** React von den Development-Builds auf `production.min.js` (47-49) — vorher prüfen, ob die `ErrorBoundary` dann noch brauchbare Meldungen liefert; Prod-React kürzt Fehlertexte

---

## Block K — Auth fürs Dashboard ⚪ — eigenes Vorhaben
Modell: Opus · Effort: xhigh · Thinking: standard
Begründung: Kein Quick-Fix. Erst mit Agent `Plan` planen lassen, Plan lesen, dann entscheiden.

Unverändert offen aus 27.07. (S-1/S-3): Die Policies sind `USING(true)` / `WITH CHECK(true)` —
die Spalten-Grants sind die **einzige** Schutzschicht. Wer den Quelltext liest, kann `veto` und
`freigabe` auf jeder Etappe setzen und `reel_varianten`, also die publizierten Narrator-Texte,
überschreiben. Lesbar sind ohnehin alle Spalten von `etappen` inkl. `monolog_final` und die
GPS-Koordinaten aus `fotos`.

- [ ] **K1** Plan erstellen: Supabase Auth mit einem Magic-Link-User, Policies von `TO anon` auf `TO authenticated`, Login-Gate, spaltenbeschränkte View statt `SELECT *` auf `etappen`
- [ ] **K2** Entscheiden — das kann für ein privates Pilger-Dashboard vertretbar sein, aber als bewusste Entscheidung, nicht als Nebenwirkung

---

## Reihenfolge

```
A  Datenquelle           🔴  ← hier anfangen, alles Weitere setzt darauf auf
B  Navigation/Sortierung 🔴
C  Kosten                🔴  greift einmal ins Pipeline-Repo (C1)
D  Live Run              🔴  greift einmal ins Pipeline-Repo (D1)
E  Etappenbezug          🟠
F  Mobil                 🟠
G  Kleinkram             🟡
H  Views                 🟡
I  Neue Daten            🟡
J  Hygiene               ⚪
K  Auth                  ⚪  eigenes Vorhaben
```

Alle offenen Entscheidungen sind getroffen (02.08.) — der Plan ist von oben nach unten abarbeitbar.
A bis D sind der Kern: danach zeigt das Dashboard die richtigen Zeilen, in vorhersagbarer
Reihenfolge, mit Zahlen und einem Live-Run, die zur Pipeline passen.

**Zwei Tasks fassen ins Pipeline-Repo** (`C1` Einheitspreise nach `costs_data.json`, `D1`
Varianten-Kennung in `pipeline_steps`) — die brauchen dort einen eigenen Commit, der Rest bleibt im
Dashboard-Repo.
