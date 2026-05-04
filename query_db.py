import urllib.request
import json

SUPABASE_URL = 'https://rgwbmqlcxxrynufcmwqx.supabase.co'
SUPABASE_KEY = 'sb_publishable_F-ZIctvp3JyhpVGNXbMttw_9vc7tdtH'

def fetch_table(name):
    try:
        req = urllib.request.Request(f"{SUPABASE_URL}/rest/v1/{name}?select=*&limit=1", headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"})
        res = urllib.request.urlopen(req)
        print(f"Table {name}:", res.read().decode('utf-8'))
    except Exception as e:
        print(f"Error {name}:", e)

fetch_table('stile')
fetch_table('styles')
fetch_table('fotos')
