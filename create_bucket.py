import os
import sys
from dotenv import load_dotenv
from supabase import create_client

load_dotenv('../INSTA_Pipeline/.env')

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY")
supabase = create_client(url, key)

try:
    print("Buckets before:", supabase.storage.list_buckets())
    res = supabase.storage.create_bucket("style-reviews", {"public": True})
    print("Created bucket:", res)
except Exception as e:
    print("Error:", e)
