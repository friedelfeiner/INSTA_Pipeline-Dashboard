# Abarbeiten — von oben nach unten

Ableitung aus `AUDIT_2026-07-27.md`. Ein Schritt pro Abschnitt, in genau dieser Reihenfolge.
Jeder Schritt: Modell, fertiger Prompt zum Kopieren, Abnahme.

**Modell umstellen:** `/model haiku` · `/model sonnet` · `/model opus`
**Effort** = Denktiefe. Claude Code läuft per Default auf `xhigh`; wo unten `low`/`medium` steht,
kannst du es getrost lassen — es kostet nur mehr, es geht nichts kaputt. Haiku hat keinen
Effort-Parameter.

**Zwei Entscheidungen brauche ich von dir, bevor du bei Schritt 5 bzw. 8 ankommst** —
stehen dort jeweils als „⚠️ Vorher entscheiden". Kannst du bis dahin liegen lassen.

**Stand 27.07.2026:** Schritt 1 + 2 + 3 + 4 + 5 + 6 erledigt. Als Nächstes Schritt 7 (⚠️ vorher entscheiden bei Schritt 8).

---

## Block A — kaputt, jetzt reparieren (ein halber Nachmittag)

### ✅ 1 · Grants nachziehen 🔴 `Sonnet` — erledigt 27.07.2026

Behebt **B-1 + B-2 zusammen** — beide haben dieselbe Ursache: die Migration
`20260723150000_anon_grants_verschaerfen.sql` hat beim Verschärfen zwei Aufrufer übersehen.
Solange das offen ist, wirft jede Style-Bewertung ihre Daten weg.

> Neue Migration in `INSTA_Pipeline/supabase/migrations/`:
> `grant update (stil_bewertung, stil_notiz) on public.etappen to anon;`
> `grant update (favorit) on public.stile to anon;`
> Lies vorher `20260723150000_anon_grants_verschaerfen.sql` und ergänze deren Kommentarblock,
> sodass alle vier Dashboard-Aufrufer gelistet sind (Hitl1Panel.freigeben, Hitl2Veto.setzeVeto,
> Hitl2Veto.setzeFreigabe, TabStyleReview.handleRate, skToggleFav).

**Abnahme:** `PATCH …/etappen?id=eq.00000000-0000-0000-0000-000000000000 -d '{"stil_bewertung":2}'`
→ `204` statt `401`.
**Danach von Hand:** alles, was du seit 23.07. im Style-Tab bewertet hast, ist weg und nicht
wiederherstellbar → einmal neu bewerten. ← **steht noch aus**

**Ergebnis:** Migration `20260727120000_anon_grants_stil_nachtragen.sql` (Pipeline-Repo),
angewendet auf `rgwbmqlcxxrynufcmwqx`. Abnahme bestanden: `stil_bewertung`, `stil_notiz`,
`favorit` → `204`; Gegenprobe `pipeline_status`, `tages_monolog`, `datum`, `kategorie` →
weiterhin `401`, die Verschärfung hält also.

**Zusatzfund, nicht im Audit:** `TabMonolog.freigeben` patcht `monolog_final` — seit dem 23.07.
ebenfalls `401`. Nicht aufgefallen, weil dieser Pfad `patch.ok` schon prüfte (sichtbarer Fehler
statt stiller). Grant nach Rückfrage mitgezogen. Nebenwirkung war: derselbe PATCH setzt
`hitl1_entschieden_um`, also schlug auch das Überspringen von HITL #1 fehl.

**Offen:** Die Migrationsdatei ist im Pipeline-Repo **noch nicht committet** — das Repo steht auf
Branch `reforge-a-decore`, nicht auf `main`. In der DB ist sie angewendet.

---

### ✅ 2 · `res.ok`-Checks nachrüsten 🔴 `Sonnet` — erledigt 27.07.2026

B-6 + B-7. **Muss direkt nach Schritt 1 kommen** — sonst fällt der nächste Grant-Fehler wieder
still aus, und du merkst es erst wieder in vier Tagen.

> Vier Schreibpfade in `index.html` prüfen den HTTP-Status nicht: `handleRate` (1656-1677),
> `Hitl1Panel.freigeben` (2415-2432), `Hitl2Veto.setzeVeto` (2683-2689), `setzeFreigabe`
> (2691-2697). Muster wie bei 2250-2251 übernehmen. Bei `handleRate` zusätzlich das optimistische
> `setRating` bei Fehler zurückrollen. Bei `sendMonolog` (162-169) `r.json()` ohne Status-Check →
> `try/finally` bei den drei Aufrufern, damit `setSaving(false)` immer läuft.

**Abnahme:** Netzwerk-Tab auf offline, jeden der vier Buttons drücken — jeder zeigt einen Fehler
und wird wieder klickbar.

**Ergebnis:** Commit `7ae2c8e`. Statt der Offline-Abnahme von Hand wurden die Funktionen aus
`index.html` extrahiert und gegen simulierte Antworten geprüft (204 / 401 / Netzwerkfehler /
500 ohne JSON / leerer Body / kaputtes JSON) — in keinem Pfad bleibt `saving` hängen.
`handleRate` rollt `setRating` bei Fehler zurück. JSX transpiliert sauber durch Babel 7.29
(dieselbe Version wie im `<script>`-Tag).

**Über den Auftrag hinaus:** `onVeto`/`onFreigegeben` laufen jetzt nur noch im Erfolgsfall — sonst
hätte der ausgelöste Reload die frische Fehlermeldung sofort wieder weggespült. Bei `sendMonolog`
liegt der Fix in der Funktion selbst (gibt immer `{ok, error}` zurück, wirft nie); das
`try/finally` bei den drei Aufrufern ist der zweite Riegel.

---

### ✅ 3 · `\u`-Escapes + `running`-Pill 🟠 `Haiku` — erledigt 27.07.2026

B-3. Fünf Minuten, exakt spezifiziert.

> In `index.html` Zeilen 3617, 3622, 3623: Backslash-Escapes durch echte Zeichen ersetzen
> (`läuft`, `→`). Babel löst die in JSX-Text/Attributen nicht auf. Zusätzlich in der Pills-Map
> (458-464) den Eintrag `running` ergänzen, sonst zeigt „läuft" ein grünes ✓.

**Abnahme:** Pipeline-Tab öffnen, Titelzeile lesen.

**Ergebnis:** Die vier `\u`-Escapes lagen tatsächlich bei Zeile 3663/3665/3670/3671 (nicht
3617-3623 — das war eine ältere Zeilenzählung), alle vier ersetzt: `·` (zweimal), `läuft`,
`→` (dreimal). Die eigentliche Pills-Map ist nicht 458-464 (das ist die Plattform-Badge-Leiste),
sondern die `Pill`-Komponente selbst (Zeile 473-479) — dort fehlte `running` und fiel auf den
`ok`-Default (grünes ✓) zurück. Ergänzt mit `IActivity`-Icon + Akzentfarbe (`T.accentSoft`/
`T.accentInk`), damit „läuft" sich optisch von „fertig" abhebt statt es zu imitieren.
Zwei weitere `●`-Escapes (Zeile 3573, 3692, LIVE-Punkt) liegen außerhalb des spezifizierten
Scopes und wurden nicht angefasst. Transpile-Check gegen Babel 7.29 (wie in Schritt 2) bestanden.

---

### ✅ 4 · `fetchAll`-Backport + `file://` raus 🟠 `Sonnet` · Effort `high` — erledigt 27.07.2026

B-4 + B-5. Holt 645 fehlende Bilder zurück. Der Fix liegt bei dir schon fertig herum.

> `fetchAll()` mit Range-Header aus `style-overview.html:359-370` nach `index.html` übernehmen und
> die drei `limit=`-Queries umstellen: Fotos (1832-1833, `limit=3000`, echte Zeilenzahl 1645),
> `fetchReelMetrics` (`limit=2000`), `fetchTelemetrieKosten` (`limit=1000`). PostgREST kappt hart
> bei 1000. Danach `skFileUrl`, `localRows` und den `file://`-Zweig in `ImageCardInline`
> (1520, 1809-1811) entfernen — über HTTPS lädt das nie, zählt aber in „+N mehr" mit.

**Abnahme:** Stil-Katalog laden, Bildzahl gegen `Content-Range: …/1645` gegenrechnen.
**Gleich mitnehmen (H-4):** `style-overview.html` und `upload_style_reviews.py` committen.

**Ergebnis:** `fetchAll(path, pageSize=1000)` als generischer Helper direkt nach den
Supabase-Konstanten in `index.html` ergänzt (baut Headers selbst, damit alle drei Aufrufer nur
noch den REST-Pfad übergeben). Umgestellt: `fetchReelMetrics`, `fetchTelemetrieKosten` (dabei
zusätzlich `order=run_at.asc` ergänzt — fehlte komplett, Range-Pagination ohne `order` ist bei
PostgREST nicht deterministisch) und die Fotos-Query in `TabStilKatalog`. Live gegen die DB
geprüft: `fetchAll` auf die Fotos-Query liefert **1645 von 1645** Zeilen (vorher hart bei 1000
gekappt, `limit=3000` im Query-String wirkungslos) — deckt sich mit dem Audit-Wert. Zweite
Fotos-Query (`bildgen_datei`, kein `bildgen_url`) komplett gestrichen statt umgestellt, dazu
`skFileUrl` und der `file://`-Zweig in `ImageCardInline` entfernt: `imgSrc` ist jetzt einfach
`foto.bildgen_url || null`. Eine dritte `bildgen_datei`-Stelle bei `fetchFotosForEtappe` (2405,
HITL-Panel) bleibt unangetastet — anderer Kontext, dort nur Metadaten-Spalte, kein `file://`-Bau,
nicht im Audit erwähnt. Babel-7.29-Transpile bestanden. `style-overview.html` /
`upload_style_reviews.py` **nicht committet** — das ist ein separater Commit-Schritt, keine
Code-Änderung; steht noch aus.

---

## Block B — funktioniert, aber falsch

### ✅ 5 · HITL-Logik 🟡 `Sonnet` · Effort `high` — erledigt 27.07.2026

L-1, L-2, L-3.

**Entscheidung:** In der DB nachgesehen — aktuell 0 offene Reels, aber 80 historische Fälle mit
Veto/Freigabe bei leerem `post_geplant_um`. Also der Normalfall, kein Ausreißer → Fix im Dashboard,
nicht in `main.py`. „Freigeben"-Button bleibt (spart die Wartezeit bewusst), nur die
Blockade-Logik war falsch.

> `index.html:2719` — `offen` verlangte `post_geplant_um` in der Zukunft; ist es `null`, stand
> „Fenster geschlossen", obwohl die Etappe auf `reel_freigabe` steht: kein Veto, keine Freigabe
> möglich. Außerdem nahm der Code `varianten[0]` statt der Variante mit `hitl_prio_stil` — das Feld
> wurde in der Query nicht mal selektiert. Und „Tag" zeigte `etappen_nr` statt `tag_nr`
> (Fallback-Muster wie in `MonologListeItem`).

**Ergebnis:** `offen` ist jetzt `(!ziel || ziel > now) && !veto && !freigabe` — kein Zieldatum
blockiert nicht mehr, sondern hält das Fenster offen. Die Restzeit-Anzeige zeigt bei fehlendem
Zieldatum stattdessen „Kein Zieldatum gesetzt — wartet auf Freigabe oder Veto" (kein Absturz auf
`ziel.toLocaleTimeString`). `hitl_prio_stil` zur Query in `fetchEtappenFuerHitl2` ergänzt,
`prioVariante` wählt jetzt darüber statt blind `varianten[0]`. „Tag"-Anzeige an den drei Stellen
(`Hitl1Panel`, `Hitl1HistorieViewer`, `Hitl2Veto`) auf `etappe.tag_nr || etappe.etappen_nr`
umgestellt. Babel-7.29-Transpile bestanden (wie in Schritt 2/3).

---

### ✅ 6 · Kleinkram-Fixes 🟡 `Sonnet` — erledigt 27.07.2026

L-4 bis L-7. Vier unabhängige Ein- bis Fünfzeiler, ein Commit.

> `index.html`: (1) Pfeiltasten-Handler 3382-3396 startet bei `max`, die Ansicht bei `defaultIdx`
> → auf `curIdx` umstellen. (2) `100vh` in 3458 überschreibt `100dvh` aus Zeile 14 → auf `100dvh`.
> (3) Monolog-Default-Datum 2151 ist UTC, zwischen 00:00 und 02:00 Wiener Zeit also gestern → lokal
> berechnen. (4) `_skCache` (1791) wird nie invalidiert → beim Bewerten leeren.

**Ergebnis:** Zeilen hatten sich wieder verschoben (Stand nach Schritt 5). (1) Handler bei 3442-3456
berechnete `defaultIdx` nicht, sondern nahm den globalen `max` als Fallback, sobald `selectedIdx`
noch `null` war — erste Pfeiltaste sprang dann vom letzten Listeneintrag statt vom aktuell
angezeigten (`latestRunIdx`). Handler berechnet `defaultIdx` jetzt genauso wie der Render-Pfad.
(2) `calc(100vh - 180px)` bei 2374 (Monolog-Listen-Sidebar) auf `100dvh` umgestellt. (3) Default-Datum
in `MonologPanel` (2176) von `new Date().toISOString().slice(0,10)` (UTC) auf
`Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Vienna' }).format(new Date())` umgestellt.
(4) `skRate` und `skToggleFav` (1888-1912) setzen `_skCache = null` statt nur `_skCache.stile`
mitzupatchen — robuster als zwei Stellen synchron zu halten, erzwingt bei nächstem Mount von
`TabStilKatalog` einen echten Refetch statt sich auf die in-place-Mutation zu verlassen.
Babel-7.29-Transpile bestanden.

---

### 7 · Views auf `security_invoker` 🟡 `Opus` · Effort `high`

S-2, drei Supabase-Advisor-ERRORs.

> `v_etappen_uebersicht`, `v_offene_fotos`, `etappen_uebersicht` sind `SECURITY DEFINER` und
> umgehen damit RLS; `v_offene_fotos` gibt u.a. lokale Pfade (`quelldatei`) an `anon` heraus.
> Fix: `alter view … set (security_invoker = on);`. **Vorher** `INSTA_Pipeline/` danach durchsuchen,
> wer die Views liest — läuft das über den Service-Key, ist es unkritisch; läuft es über `anon`,
> brichst du die Pipeline.

**Warum Opus:** kann Leser brechen, der Agent muss das Urteil fällen, nicht nur das SQL schreiben.
**Abnahme:** `get_advisors(type: security)` — die drei ERROR-Einträge sind weg.

---

### 8 · Kosten-Zahlen vereinheitlichen 🟡 `Opus` · Effort `xhigh`

Z-1 bis Z-4.

> **⚠️ Vorher entscheiden:** Soll der Übersicht-Tab weiter schätzen (`$0.030/Bild × 0.88`,
> hartkodiert) — oder auf dieselbe Quelle wie der Ist-Kosten-Tab (echte Abrechnungen, Kurs
> `0.8765`)? Aktuell zeigen zwei Tabs zwei verschiedene Anthropic/WaveSpeed-Zahlen.
> **Lass dir das erst empfehlen, bevor der Agent etwas ändert.**

> Halte `costs_data.json`, `platformCosts()` (index.html 88-97) und `tools/costs_report.py`
> gegeneinander und empfiehl mir eine Quelle der Wahrheit. Danach: `Math.max(0,…)` in Zeile 95
> kappt negative Atlas-Werte, die vier Balken summieren sich dann nicht mehr auf. Balken „FAL.ai"
> (703) zeigt `cost_tts_eur`, obwohl fal auch Bildgen und Video macht — Label ≠ Wert.
> Trend-Achse (828) hart `T1…T28` trotz `${trend28.length} Runs`. `successRate` (366) zählt nur
> Runs mit nicht-leerem `errors[]` als Fehler, `pipeline_status='fehler'` ohne Errors gilt als
> Erfolg — an `statusMap` koppeln.

---

## Block C — Aufräumen, kann warten

### 9 · Repo-Hygiene ⚪ `Haiku`

H-1 bis H-3.

> **⚠️ Vorher entscheiden:** Soll `Presentation Work/` (97 MB, 43 PNG + 6 MP4) überhaupt versioniert
> werden? Wenn ja → eigenes Repo, **nicht** ins Pages-Repo; Git löscht Blobs nicht mehr raus.
> Default unten: ignorieren.

> `.gitignore` im Dashboard-Repo anlegen (`.DS_Store`, `Presentation Work/`), `.DS_Store` aus dem
> Index nehmen (`git rm --cached`). Danach React von den Development-Builds auf
> `production.min.js` umstellen (47-49) — aber vorher prüfen, ob die `ErrorBoundary` dann noch
> brauchbare Meldungen liefert; Prod-React kürzt Fehlertexte.

---

### 10 · Grant-Aufräumen ⚪ `Sonnet` · optional

S-Anhang. Ändert am Verhalten nichts, verkleinert nur die Angriffsfläche.
**Erst nach Schritt 1**, sonst kollidieren die Migrationen.

> `revoke insert, delete, truncate … from anon` auf allen Tabellen; `publish_queue`-Grants
> komplett entziehen (RLS an, keine Policy → totes Recht). Zusätzlich `search_path` auf
> `update_modified_column` setzen (Advisor-WARN).

---

### 11 · Auth fürs Dashboard ⚪ `Opus` — eigenes Vorhaben

S-1 + S-3. **Kein Quick-Fix, erst planen lassen.**

Solange das offen ist, sind die Spalten-Grants die *einzige* Schutzschicht (die Policies sind
`USING(true)`). Jeder, der den Quelltext liest, kann `veto`/`freigabe` setzen und
`reel_varianten` — die publizierten Narrator-Texte — überschreiben. Lesbar sind ohnehin alle 93
Spalten von `etappen` inkl. `monolog_final` und die GPS-Koordinaten aus `fotos`.

> Erst mit Agent `Plan`: Supabase Auth mit einem Magic-Link-User, alle Policies von `TO anon` auf
> `TO authenticated`, Login-Gate im Dashboard, spaltenbeschränkte View statt `SELECT *` auf
> `etappen`. Plan lesen, dann entscheiden.

Das kann für ein privates Pilger-Dashboard vertretbar sein — aber als bewusste Entscheidung,
nicht als Nebenwirkung.
