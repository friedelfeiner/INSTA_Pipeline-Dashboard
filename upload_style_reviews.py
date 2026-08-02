#!/usr/bin/env python3
"""Lädt fehlende Bildgen-Fotos klein gerechnet in den style-reviews-Bucket
und trägt die öffentliche URL in fotos.bildgen_url nach.

Betroffen sind Zeilen mit bildgen_datei (lokaler Pfad) aber ohne bildgen_url —
genau die, die im Style-Katalog online leer bleiben, weil file://-URLs
auf GitHub Pages nicht laden.

  python3 upload_style_reviews.py            # Dry-Run, schreibt nichts
  python3 upload_style_reviews.py --apply    # tatsächlich hochladen
"""
import io
import os
import sys

from PIL import Image
from dotenv import load_dotenv
from supabase import create_client

BUCKET = "style-reviews"
MAX_EDGE = 720       # längere Kante
TARGET_KB = 70       # Qualität wird gesenkt bis das Bild darunter liegt (~65 KB Schnitt)

# Das Projekt ist von Dropbox nach 30_PROJEKTE umgezogen; 116 fotos-Zeilen
# tragen noch den alten Pfad. Die Dateien liegen unter dem neuen Root.
PATH_FIXES = [
    ("/Users/flo/Library/CloudStorage/Dropbox/",
     "/Users/flo/Documents/30_PROJEKTE/INSTA PIPELINE/"),
]


def resolve(path):
    """Alten Dropbox-Pfad auf den aktuellen Speicherort mappen."""
    if os.path.exists(path):
        return path
    for old, new in PATH_FIXES:
        if path.startswith(old):
            cand = path.replace(old, new, 1)
            if os.path.exists(cand):
                return cand
    return None

load_dotenv("/Users/flo/Documents/ANTIGRAVITY/INSTA_Pipeline/.env")
url = os.environ["SUPABASE_URL"]
key = os.environ["SUPABASE_SERVICE_KEY"]
sb = create_client(url, key)

apply = "--apply" in sys.argv


def shrink(path):
    """Auf MAX_EDGE herunterrechnen und die Qualität so weit senken,
    bis das Ergebnis unter TARGET_KB liegt (quadratische Bilder brauchen
    bei gleicher Kantenlänge mehr Bytes als hochformatige)."""
    im = Image.open(path)
    if im.mode != "RGB":
        im = im.convert("RGB")
    im.thumbnail((MAX_EDGE, MAX_EDGE), Image.LANCZOS)
    for q in (80, 72, 65, 58, 50):
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=q, optimize=True, progressive=True)
        data = buf.getvalue()
        if len(data) <= TARGET_KB * 1024:
            break
    return data


# Alle Kandidaten holen (paginiert, PostgREST deckelt bei 1000)
rows, start = [], 0
while True:
    page = (sb.table("fotos")
            .select("id,foto_nr,bildgen_datei,tagesstil")
            .is_("bildgen_url", "null")
            .not_.is_("bildgen_datei", "null")
            .order("foto_nr")
            .range(start, start + 999).execute().data)
    rows += page
    if len(page) < 1000:
        break
    start += 1000

for r in rows:
    r["src"] = resolve(r["bildgen_datei"])
missing = [r for r in rows if not r["src"]]
todo = [r for r in rows if r["src"]]
remapped = sum(1 for r in todo if r["src"] != r["bildgen_datei"])

print(f"Kandidaten (bildgen_datei ohne bildgen_url): {len(rows)}")
print(f"  Datei lokal vorhanden : {len(todo)}  (davon {remapped} via Pfad-Remap)")
print(f"  Datei fehlt auf Platte: {len(missing)}")
for r in missing[:10]:
    print(f"    ! {r['foto_nr']}  {r['bildgen_datei']}")
if len(missing) > 10:
    print(f"    ... und {len(missing) - 10} weitere")

if not apply:
    if todo:
        step = max(1, len(todo) // 8)
        print(f"\nProben (max {MAX_EDGE}px, Ziel <{TARGET_KB} KB):")
        for r in todo[::step][:8]:
            print(f"  {r['foto_nr']}: {round(len(shrink(r['src']))/1024)} KB")
    print("\nDry-Run — nichts geschrieben. Mit --apply ausführen.")
    sys.exit(0)

ok = fail = 0
for i, r in enumerate(todo, 1):
    dest = f"{r['id']}/{r['foto_nr']}.jpg"
    try:
        data = shrink(r["src"])
        sb.storage.from_(BUCKET).upload(
            dest, data,
            {"content-type": "image/jpeg", "upsert": "true"},
        )
        public = sb.storage.from_(BUCKET).get_public_url(dest).rstrip("?")
        sb.table("fotos").update({"bildgen_url": public}).eq("id", r["id"]).execute()
        ok += 1
    except Exception as e:
        fail += 1
        print(f"  FEHLER {r['foto_nr']}: {e}")
    if i % 50 == 0 or i == len(todo):
        print(f"  {i}/{len(todo)}  ok={ok} fehler={fail}")

print(f"\nFertig: {ok} hochgeladen, {fail} Fehler, {len(missing)} ohne lokale Datei.")
