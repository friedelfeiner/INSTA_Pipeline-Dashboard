# Dashboard MVP — Was wir zuerst bauen

Fokus: Kosten, Performance, Reliability. Alles andere kommt später.

---

## Basis-Kontext (Pflicht für alles andere)

Jeder Durchlauf schreibt diese Felder — ohne sie lässt sich keine Zeitreihe lesen:

| Feld | Beispiel |
|---|---|
| Datum & Uhrzeit | 2026-04-23 18:42 |
| Etappe-Nummer | 12 |
| Etappe-Name | "Pontremoli → Aulla" |
| Status | success / error / partial |

---

## 1. Kostenmonitoring

Was hat dieser Durchlauf gekostet — und wo geht das Geld hin?

| Feld | Beispiel |
|---|---|
| Gesamtkosten (€) | 0.43 |
| davon LLM | 0.18 |
| davon ImageGen | 0.12 |
| davon Video | 0.09 |
| davon TTS | 0.04 |

**Im Dashboard sichtbar:**
- Kosten des heutigen Laufs
- Kumulierte Kosten der gesamten Reise
- Trendlinie über die letzten 28 Tage

---

## 2. Zeitliche Performance

Wie lange hat der Lauf gebraucht — und wer war langsam?

| Feld | Beispiel |
|---|---|
| Gesamtdauer (Sekunden) | 847 |
| Dauer pro Agent | `{"analyst": 12, "narrator": 8, "imagegen": 277}` |

**Im Dashboard sichtbar:**
- Laufzeit gesamt
- Balkendiagramm: Welcher Agent braucht wie lange
- Trend: Wird ein Agent langsamer über mehrere Etappen?

---

## 3. Reliability & Retries

Hat alles funktioniert — oder musste die Pipeline kämpfen?

| Feld | Beispiel |
|---|---|
| Retries pro Agent | `{"imagegen": 2, "tts": 0}` |
| Fehler (falls vorhanden) | `[{"agent": "imagegen", "msg": "timeout", "resolved": true}]` |

**Im Dashboard sichtbar:**
- Retry-Rate pro Agent, Trend über Zeit
- Fehlermeldungen im Klartext ("ImageGen: Timeout, Retry #2 erfolgreich")
- Frühwarnung wenn ein Service häufiger als üblich retried

---

## 4. Offene Entscheidung: Update-Zeitpunkt

**Option A — Einmal am Ende (empfohlen):**
`main.py` schreibt einen einzigen INSERT wenn alles durch ist. Einfach, atomar, kein Halbzustand im Dashboard.

**Option B — Nach jedem Agent-Step:**
Dashboard zeigt Live-Fortschritt ("gerade läuft ImageGen…"). Mehr Aufwand, mehr Komplexität.

Für v1 empfehle ich Option A.

---

## Was kommt später (nicht jetzt)

- Asset-Gallery (Foto-Vergleich)
- Core Theme / Analyst-Selektion
- Model-Stack-Anzeige
- Kunden-Dashboard (separates Konzept)

---

*MVP-Scope. Stand: 2026-04-23.*
