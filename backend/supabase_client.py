import os
from functools import lru_cache
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

@lru_cache
def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)