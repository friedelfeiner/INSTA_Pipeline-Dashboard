# Konzeptpapier: Pipeline Ops-Dashboard

Dieses Dokument dient als Grundlage für die Planung eines technischen Dashboards für die INSTA Pipeline. Das Ziel ist die Überwachung von Kosten, Pipeline-Gesundheit und Datendurchsatz, ohne den privaten Code der Pipeline zu veröffentlichen.

---

## 1. Zielsetzung

- **Transparenz**: Wie viel kostet jeder Durchlauf, welcher Agent ist der teuerste?
- **Health-Check**: Sind alle Agents (Analyst, Narrator, ImageGen etc.) erfolgreich durchgelaufen?
- **Zeitreihe**: Trends über die letzten 28 Tage — Kosten, Fehlerrate, Laufzeiten.
- **Statistik**: Wie viele Ressourcen (API-Calls, Bilder, Videos) werden verbraucht?

---

## 2. Architektur: Zwei-Schichten-Modell

Die Pipeline schreibt am Ende jedes Durchlaufs eine Zeile in **Supabase**. Das Dashboard liest direkt von dort — kein Zwischenschritt, kein Git-Push, kein Exporter-Skript.

```
Lokale Pipeline (privat)
       │
       │  INSERT (eine Zeile pro Durchlauf)
       ▼
 Supabase: Tabelle `pipeline_runs`  ◄──── liest ────  GitHub Pages (öffentlich)
                                                         HTML + JS, kein privater Code
```

**Warum Supabase statt Git-Push:**
- Jeder Durchlauf = eine Zeile → Verlauf der letzten 28 Tage ist gratis dabei
- Supabase hat public read-only Endpoints → Dashboard braucht keinen geheimen API-Key
- Trends, Aggregationen, Zeitreihen funktionieren ohne extra Logik
- Kein lokaler Dateipfad, kein privater Code landet auf GitHub

**Warum GitHub Pages als Display:**
- Kostenlos, keine Server, keine Wartung
- Nur eine HTML-Datei mit JavaScript — kein Framework nötig
- Pipeline-Code bleibt zu 100% privat

---

## 3. Datenmodell: Tabelle `pipeline_runs`

Jede Zeile entspricht einem abgeschlossenen Pipeline-Durchlauf (eine Etappe).

| Spalte | Typ | Beispiel |
|---|---|---|
| `id` | uuid | auto |
| `run_at` | timestamp | 2026-04-23 18:42:00 |
| `etappe_nr` | int | 12 |
| `etappe_name` | text | "Pontremoli → Aulla" |
| `status` | text | "success" / "error" / "partial" |
| `duration_total_s` | int | 847 |
| `photos_input` | int | 34 |
| `photos_selected` | int | 8 |
| `videos_output` | int | 1 |
| `cost_total_eur` | float | 0.43 |
| `cost_llm_eur` | float | 0.18 |
| `cost_imagegen_eur` | float | 0.12 |
| `cost_video_eur` | float | 0.09 |
| `cost_tts_eur` | float | 0.04 |
| `core_theme` | text | "Nebel und Stille" |
| `model_stack` | jsonb | {"claude": "sonnet-4-6", "fal": "..."} |
| `agent_timings_s` | jsonb | {"analyst": 12, "narrator": 8, "imagegen": 277} |
| `retries` | jsonb | {"imagegen": 2, "tts": 0} |
| `errors` | jsonb | [{"agent": "imagegen", "msg": "timeout", "resolved": true}] |

---

## 4. Datenpunkte (Was wollen wir messen?)

### A. Kosten-Monitoring & ROI
- **Kosten pro Agent**: Aufschlüsselung LLM / ImageGen / Video / TTS
- **Kumulierte Kosten**: Gesamtausgaben der gesamten Reise
- **Trendlinie**: Kostenentwicklung über die letzten 28 Tage
- **ROI-Vergleich**: "Mensch vs. Maschine" — Was hätte ein Editor für dieses Reel gekostet?

### B. Zeitliche Performance (neu)
- **Laufzeit pro Agent**: Wall-Clock-Zeit für jeden Step (Analyst: 12s, ImageGen: 4m37s)
- **Flaschenhals-Erkennung**: Welcher Agent braucht am meisten Zeit, Trend über mehrere Etappen
- **28-Tage-Heatmap**: Ähnlich GitHub Contributions — welche Tage hatte die Pipeline einen Durchlauf?

### C. Input-Qualität & Selektion (neu)
- **Foto-Trichter**: Input-Fotos → vom Analyst selektiert → im Video verwendet
- **Selektionsrate**: Wie viel Prozent der Fotos schafft es? (Indikator für Material-Qualität)
- **Core Theme**: Das von der KI identifizierte Tagesthema — kurzer Plausibilitäts-Check

### D. Reliability & Retry-History (neu)
- **Retry-Rate pro Agent**: Wie oft musste ein Agent wiederholen? Trend über Zeit
- **Error-Log (Plain Text)**: Verständliche Fehlermeldungen ("ImageGen: Timeout, Retry #2 erfolgreich")
- **Drift-Erkennung**: Steigt die Retry-Rate bei einem bestimmten Service? Frühwarnung vor Ausfällen

### E. Technisches Health-Panel
- **API-Latenz**: Performance-Check der angebundenen Dienste (Claude, ElevenLabs, FAL.ai)
- **Model-Stack**: Anzeige der aktuell aktiven Modell-Versionen (wichtig nach Updates)
- **Status-Badges**: ✅ Erfolgreich | ⚠️ Partial | ❌ Error

### F. Asset-Gallery (Technische Vorschau)
- Gegenüberstellung: Original-Foto vs. KI-Interpretation (Hero-Image)
- Streak-Anzeige: "Etappe 12 von X — Tag 23 der Reise"

---

## 5. Betreiber-Dashboard vs. Kunden-Dashboard

Diese beiden Ansichten sind grundlegend verschieden:

| | Betreiber (du) | Kunde |
|---|---|---|
| **Fokus** | Operative Kontrolle | Ergebnis & Wert |
| **Metriken** | Latenz, Retries, Kosten/Agent, Fallback-Logs | Gesamtkosten, Output-Qualität, ROI |
| **Granularität** | Jeder Agent-Step | Zusammenfassung pro Etappe |
| **Ton** | Technisch, direkt | Storytelling, visuell |

Das Dokument fokussiert aktuell auf das **Betreiber-Dashboard**. Ein Kunden-Dashboard wird separat konzipiert.

---

## 6. Offene Fragen & Nächste Entscheidungen

- **Kosten-Quellen**: Schätzen wir die Kosten selbst (Einheitspreis-Modell) oder lesen wir echte Abrechnungsdaten aus den APIs?
- **Supabase Public Key**: Welche Tabellen/Spalten sind über den anonymen Key lesbar — was muss Row-Level-Security schützen?
- **Update-Zeitpunkt**: Schreibt die Pipeline nach jedem Agent-Step in Supabase, oder einmal am Ende von `main.py`? (Empfehlung: einmal am Ende, atomar)
- **Dashboard-Intervall**: Lädt das Dashboard live nach, oder reicht ein manueller Refresh?

---

*Stand: 2026-04-23. Nächster Schritt: Supabase-Tabelle anlegen und INSERT-Logik in main.py einbauen.*
