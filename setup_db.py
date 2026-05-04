import os
import sys

env_path = '../INSTA_Pipeline/.env'
if not os.path.exists(env_path):
    print("No .env found at", env_path)
    sys.exit(1)

with open(env_path, 'r') as f:
    for line in f:
        if line.startswith('SUPABASE_') or line.startswith('DATABASE_'):
            key = line.split('=')[0]
            print("Found:", key)

