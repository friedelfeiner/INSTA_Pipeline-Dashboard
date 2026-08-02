# Dashboard-Audit — Nachtrag: was aus dem 02.08.-Plan offen blieb

Stand 02.08.2026. Grundlage: `dashboard-audit-plan-2026-08-02-fable.md` (Blöcke A–K).
A–I sind laut dortiger Checkliste erledigt (✅), bis auf zwei einzelne Punkte. Dieser
Nachtrag bündelt **nur das Offene** plus, was mir beim Gegenlesen des aktuellen Repo-Stands
zusätzlich aufgefallen ist. Kein neuer Vollaudit — `index.html` wurde nicht noch einmal
komplett gegen die DB durchgemessen.

**Modelle:** Haiku (mechanisch) · Sonnet (Standard) · Opus (Urteil)

---

## Was aus dem alten Plan noch offen ist

| ID | Block | Was |
|---|---|---|
| E2g | E | Kurz-Check gegen die Graph API: `profile_activity` für REELS verfügbar? |
| E2h | E | Später-Vorhaben: YouTube Analytics API, Facebook `read_insights` |
| I4/I5 | I | Story-Insights vom Friedelfeiner-Account (Graph-API-Check + `story_metrics`) |
| I6 | I | `insights_poller` serverseitig als `pg_cron`-Job |
| I7 👤 | I | Slot-Belegung (`PUBLISH_BELEGUNG`) variieren — Pipeline-Entscheidung |
| J5 | J | React auf `production.min.js` umstellen |
| K1/K2 | K | Auth fürs Dashboard — eigenes Vorhaben, noch nicht geplant |

Diese Punkte sind im alten Plan bereits vollständig beschrieben (Kontext, Befund, Abnahme) —
hier nur neu sortiert nach dem, was jetzt tatsächlich als Nächstes sinnvoll ist.

---

## Block L — Uncommitted Stand aufräumen 🔴
Modell: — (kein Agent, eine Entscheidung von dir)
Begründung: `git status` zeigt den kompletten A–I-Umbau aus dem Fable-Plan als **staged, aber
nicht committet** — inklusive `.gitignore`, Icons, Manifest, `costs_data.json`, `index.html`
selbst. Ein Absturz oder `git checkout` würde Wochen Arbeit riskieren, die nirgends sonst liegt.

- [ ] 👤 **L1** Diesen Stand committen (oder in mehrere thematische Commits aufteilen: Icons/PWA,
  Kosten-Umbau, Security-Doku, Hygiene). Bis das passiert, ist alles andere hier zweitrangig.

---

## Block M — Frisch aufgefallen beim Gegenlesen 🟠
Modell: Sonnet · Effort: medium · Thinking: standard

- [ ] **M1** `query_db.py` fragt weiterhin `stile` und `fotos` mit hartem `SUPABASE_KEY` im
  Klartext ab (Zeile 5) — kein Secret-Leak nach außen (das ist der `anon`/`publishable`-Key),
  aber die Datei liegt jetzt committet im Repo. Wenn sie nur Ad-hoc-Debugging war: in `.gitignore`
  aufnehmen oder als `tools/`-Skript mit Kommentar versehen, warum sie bleibt
- [ ] **M2** `costs_data.json` trägt jetzt `meta.nicht_projekt.anthropic` (private Claude-Code-
  Kosten). Kurz prüfen, ob diese Zahl auf GitHub Pages öffentlich landet (das Repo ist laut
  `9c7a2c5` „aus Suchmaschinen raus", aber nicht privat) — falls unerwünscht, gehört sie nicht in
  die öffentlich ausgelieferte JSON, sondern in eine lokale, ignorierte Datei
- [ ] **M3** `docs/dashboard-audit-plan-2026-08-02-fable.md` ist als *modified* markiert
  (Checkboxen wurden beim Abarbeiten live nachgezogen) — beim Commit aus L1 mitnehmen, sonst
  zeigt der nächste Claude-Lauf wieder den alten Stand

---

## Reihenfolge

```
L  Commit nachholen     🔴  zuerst — sonst ist alles andere Kosmetik auf Treibsand
M  Kleine Neufunde      🟠  parallel möglich
E2g/E2h, I4-I7  🟡        Graph-API-Recherche, kein Code-Blocker
J5              ⚪        React prod-Build
K               ⚪        Auth, eigenes Vorhaben — mit Plan-Agent angehen, wenn gewünscht
```

Kein Block hier ist zeitkritisch außer L — die Uncommitted-Änderungen sind der einzige Punkt,
der bei einem Zwischenfall echten Schaden anrichten könnte.
